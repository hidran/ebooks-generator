# Chapter 20 — RAG on Application Data

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## 20.1 A RAG Agent in Laravel

### The store

A knowledge base shared by many tenants has to filter every search by tenant, and a store can only filter on fields it has been told about. So the store comes first, with a `DocumentSchema` declaring the metadata the application will filter on:

```php
namespace App\Neuron\Rag;

use NeuronAI\RAG\Schema\DocumentField;
use NeuronAI\RAG\Schema\DocumentSchema;

final class KnowledgeBase
{
    public static function schema(): DocumentSchema
    {
        return DocumentSchema::of(
            DocumentField::integer('tenant_id')->required()->filterable(),
            DocumentField::integer('article_id')->required()->filterable(),
            DocumentField::string('visibility')->required()->filterable(),
            DocumentField::integer('updated_at')->filterable(),
        );
    }
}
```

`required()` makes the store reject a document that arrives without the field — the ingestion bug where someone forgets to stamp the tenant fails loudly at indexing time instead of producing an unfilterable chunk.

The same class builds the store, so the table name, the top-K and the schema have one definition:

```php
// In KnowledgeBase, which now also imports
// Illuminate\Support\Facades\DB and NeuronAI\RAG\VectorStore\MariaDBVectorStore
public static function store(): MariaDBVectorStore
{
    return new MariaDBVectorStore(
        pdo: DB::connection()->getPdo(),
        tableName: 'knowledge_base',
        topK: 5,
        schema: self::schema(),
    );
}
```

Why not simply add a `schema` key to `config/neuron.php`? Because `php artisan config:cache` serialises configuration with `var_export()`, and a `DocumentSchema` object does not survive the trip — the command fails with "Your configuration files are not serializable". Objects belong in code.

And why build a new store on every call instead of registering one as a driver with `VectorStore::extend()` and letting the manager hold it? Because `MariaDBVectorStore` keeps the PDO it is given, and a manager keeps what it built for the life of the process. A queue worker lives for days; when Laravel reconnects after a dropped connection the worker would go on using the old, dead PDO. A store is a cheap object — a connection, a table name, a schema — so the agent and every job call `KnowledgeBase::store()` and each gets the connection Laravel holds at that moment.

::: {.callout .callout-warning}
[`VectorStore::extend()` only works if you register the manager as a singleton]{.callout-title}

For a store that holds no connection — a `FileVectorStore`, or Qdrant and Pinecone, which are HTTP clients — `VectorStore::extend('name', fn () => ...)` in a service provider is the Laravel way to register it. In neuron-laravel 2.0.0 it silently does nothing useful: the SDK registers `AIProviderManager` and `EmbeddingProviderManager` as singletons, but not `VectorStoreManager`. The `VectorStore` facade resolves the manager once and caches it, so `extend()` in `boot()` works until something clears the facade's resolved instances — a test, a long-running server between requests — and then the next resolution builds a fresh manager that has never heard of your driver ("Driver [name] not supported"). Register the manager in your own provider, the one from Chapter 18, before anything calls `extend()`:

```php
// NeuronServiceProvider::register()
$this->app->singleton(VectorStoreManager::class);
```
:::

### The table

The store does not create its table. `MariaDBVectorStore::setupTable()` does, and it belongs in a migration:

```php
use App\Neuron\Rag\KnowledgeBase;
use Illuminate\Database\Migrations\Migration;

return new class extends Migration
{
    public function up(): void
    {
        KnowledgeBase::store()->setupTable((int) config('neuron.embedding.openai.dimensions'));
    }

    public function down(): void
    {
        KnowledgeBase::store()->dropTable();
    }
};
```

It needs MariaDB 11.7 or later, and it needs the embedding dimension from you. The two sides of that number ship with different defaults: the SDK's `config/neuron.php` configures the OpenAI embedder for 1024 dimensions, while `setupTable()` creates a `VECTOR(1536)` column. A column and a model that disagree about the length of a vector cannot work together, so pin the number once, in `config/neuron.php`, under `embedding.openai` — `'dimensions' => 1536` — and let the migration read it from there. Choose a value your embedding model can produce, and treat it as part of the schema: changing it later means dropping the table and re-embedding every article.

The embedder needs one more line in `.env`. `NEURON_EMBEDDING_PROVIDER` has no default (the SDK reads it with no fallback), and `EmbeddingProvider::driver()` throws a `TypeError` when it is unset — set it to `openai` (or `gemini`, `ollama`, `voyage`, `mistral`) along with that provider's key.

A store holds no per-search state, and every search carries its own filters in an immutable request, so even a store shared between requests cannot leak one tenant's filter into another's. (Older tutorials configure filters on the store itself with `withFilters()`, which made a shared instance a cross-tenant leak; the method no longer exists. Appendix A, items 26 and 43.)

### The class

```php
namespace App\Neuron\Rag;

use App\Neuron\ThreadScope;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\Filter\Filter;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class KnowledgeBaseAgent extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return EmbeddingProvider::driver();
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return KnowledgeBase::store();
    }

    protected function retrievalScope(): ?FilterExpression
    {
        return Filter::eq('tenant_id', ThreadScope::of($this->getThreadId())->tenantId);
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You answer questions using only the knowledge base articles in your context.',
                'You do not have general knowledge about this company beyond those articles.',
            ],
            steps: [
                'Read the provided articles.',
                'If they answer the question, answer and cite the article title.',
                'If they do not, say the knowledge base does not cover it and offer to '
                . 'escalate to a human.',
            ],
            output: [
                'Cite the source article for every factual claim.',
                'Keep answers under 150 words unless the user asks for detail.',
            ],
        );
    }
}
```

The agent is built the way Chapter 18 builds an agent: it knows nothing about its caller. There is no `Tenant` in the constructor; the tenant is the one named by the thread the agent is bound to — `$agent->for($conversation->threadId())` — and `ThreadScope` (Section 18.3) reads it back. An agent that is never bound does not run at all, because the framework generates no thread ID, so there is no way to search this store without a tenant. The class declares no `messageStore()`: a knowledge-base question is answered from the articles, and the conversation stays in memory for the run. Section 20.4 gives the agent a persistent history.

### The tenant filter is not optional

`retrievalScope()` returns the tenant filter unconditionally, computed from the thread, and the retrieval node applies it to every search this agent makes. There is no code path that queries the store without it. Anything else that adds a filter during a run — a middleware on the retrieval node, a custom retrieval strategy — is combined with the scope by AND, so it can narrow the search but never widen it.

Section 12.6's rule: **filter at retrieval, never after.** A document retrieved and then excluded from the answer was still in the model's context, and models paraphrase. The tenant filter is the RAG equivalent of a `where tenant_id = ?` on every query — and it belongs in the same place, at the component that builds the query.

::: {.callout .callout-warning}
[`setRetrievalScope()` replaces the scope; it does not add to it]{.callout-title}

`RAG` also has a `setRetrievalScope()` setter, and it is tempting to use it from a controller for a one-off extra filter. Don't, on this agent. The setter *replaces* what `retrievalScope()` returns — pass it `Filter::eq('visibility', 'public')` and the tenant filter is gone, and the search runs across every tenant's public articles. Keep every mandatory constraint inside the hook, computed from the thread the agent is bound to.
:::

### Choosing a store in Laravel

From Section 12.5, with the Laravel lens:

**MariaDB 11.7+** — one table in the database you already run. Backups, monitoring, transactions and failover already solved. For most Laravel applications this is the right answer, and it is the store built above.

**Elasticsearch or Meilisearch** — if you already run one for site search, use it and avoid a second system.

**Pinecone or Qdrant** — when scale genuinely demands a dedicated database.

**PHPVector** — `neuron-core/php-vector`, pure PHP, HNSW plus BM25 hybrid search, no service. Attractive for self-hosted deployments and clients who cannot add infrastructure, but at the time of writing it has no release for NeuronAI v4 (Section 12.5). Check before you plan on it.

The general rule stands: **use what you already run.** Whichever you choose, it takes the same `schema:` argument, and the same portable filters run on all of them.

### Key takeaways

- Declare the filterable metadata in a `DocumentSchema`; build the store in code (`KnowledgeBase::store()`), not in cached config, and once per resolution when it holds a PDO.
- Create the table in a migration with the embedding dimension pinned on both sides; set `NEURON_EMBEDDING_PROVIDER`.
- Put the tenant filter in `retrievalScope()`, read from the thread, so no path bypasses it — and never replace it with `setRetrievalScope()`.
- A store holds no per-search state: filters travel with each search. If you use `VectorStore::extend()`, register `VectorStoreManager` as a singleton first.
- MariaDB for most Laravel applications.

## 20.2 Queued Ingestion

### The job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\Article;
use App\Neuron\Rag\KnowledgeBase;
use App\Neuron\Rag\MarkdownSectionSplitter;
use DateTimeInterface;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Contracts\Queue\ShouldQueueAfterCommit;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\RAG\DataLoader\StringDataLoader;

class IndexArticle implements ShouldQueue, ShouldQueueAfterCommit
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $maxExceptions = 3;
    public int $backoff = 30;

    public function retryUntil(): DateTimeInterface
    {
        return now()->addHours(6);
    }

    public function __construct(
        public readonly Article $article,
    ) {}

    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)
            ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
            ->getDocuments();

        foreach ($documents as $document) {
            $document->setSourceType('article');
            $document->setSourceName("article-{$this->article->id}");
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->getTimestamp());
        }

        $store    = KnowledgeBase::store();
        $embedder = EmbeddingProvider::driver();

        // Fail on a bad document before paying for its embedding
        foreach ($documents as $document) {
            $store->getSchema()->validate($document);
        }

        $store->addDocuments($embedder->embedDocuments($documents));
    }
}
```

Standalone components (Section 12.2) rather than a RAG agent — ingestion needs no chat provider, no instructions, no tools. Keeping the job lean means it starts faster and has fewer reasons to fail. `MarkdownSectionSplitter` is the splitter from Section 12.3, moved from `App\Rag` to `App\Neuron\Rag`, next to `KnowledgeBase`.

`ShouldQueueAfterCommit` holds the dispatch until the surrounding database transaction commits, and discards it if the transaction rolls back. Without it, a job on a fast queue can start before the commit, read the old body of the article and index it, and nothing triggers a second run. The retry settings are explained under "Queue configuration" below.

The metadata has to match the schema from Section 20.1, and the schema is strict about types: `integer` means a PHP `int`, so give `Article` integer casts for its ID columns rather than trusting the driver. `updated_at` is stored as a Unix timestamp because range filters are numeric — Section 20.3 filters on it. The store validates every document again in `addDocuments()`, but by then the embeddings are paid for; the loop above fails first and for free. (`RAG::addDocuments()` does the same check in the same order, which is one reason the next job uses the agent.)

### Triggering it

```php
class Article extends Model
{
    protected static function booted(): void
    {
        static::saved(function (Article $article) {
            if ($article->wasChanged('body') || $article->wasRecentlyCreated) {
                ReindexArticle::dispatch($article);
            }
        });

        static::deleted(function (Article $article) {
            RemoveArticleFromIndex::dispatch($article->id, $article->tenant_id);
        });
    }
}
```

The `wasChanged('body')` guard matters. Without it, every save — a view-count increment, a timestamp touch — re-embeds the whole article. That is real money spent on nothing, repeatedly.

Removal is one call, because a store deletes by any filter the schema allows:

```php
public function handle(): void
{
    KnowledgeBase::store()->delete(
        Filter::where('tenant_id', $this->tenantId)->where('article_id', $this->articleId),
    );
}
```

Scoping the delete by tenant as well as article costs nothing and means a bug in the caller cannot remove another tenant's chunks.

### Reindexing rather than adding

```php
class ReindexArticle implements ShouldQueue, ShouldQueueAfterCommit
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    // $maxExceptions, $backoff, retryUntil() and the constructor, as in IndexArticle

    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)
            ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
            ->getDocuments();

        foreach ($documents as $document) {
            $document->setSourceType('article');
            $document->setSourceName("article-{$this->article->id}");   // stable — the ID, never the title
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->getTimestamp());
        }

        KnowledgeBaseAgent::make()->reindexBySource($documents);
    }
}
```

`reindexBySource()` validates the whole batch, embeds each source's chunks, and only then deletes everything stored under that source's `sourceType` and `sourceName` and adds the new chunks. A failed validation or a failed embedding call leaves the old version in the index untouched. The schema is why every metadata line is repeated here: drop the `tenant_id` line and the job fails before embedding anything, instead of writing chunks no tenant can retrieve.

Section 12.6's constraint, restated because it is easy to get wrong: **`sourceName` must be stable.** Use the article ID. Derive it from the title and an editorial rename orphans the old chunks — they stay in the index, un-deletable by source, and the agent answers from both versions.

Give it a prefix — `article-42` rather than `42`. A bare number works, but the prefix says what kind of thing the source is when you read the index.

### Queue configuration

**A dedicated queue.** Embedding is slow; do not let it delay password-reset emails.

```php
ReindexArticle::dispatch($article)->onQueue('indexing');
```

**Rate limits.** Embedding providers have them. A bulk re-index of 10,000 articles will hit one.

```php
public function middleware(): array
{
    return [new RateLimited('embeddings')];
}
```

(`RateLimited` is `Illuminate\Queue\Middleware\RateLimited`, and the `embeddings` limiter is defined with `RateLimiter::for()` in a service provider.)

**Chunked backfills.** For an initial index, `chunkById()` and dispatch in batches rather than loading everything into memory.

**Retries.** Transient provider failures are normal, so the jobs set `$backoff = 30` and `$maxExceptions = 3`: three real failures end the job. Do not count attempts with `$tries = 3` on a job that uses `RateLimited`: every time the limiter releases the job it consumes an attempt, so a 10,000-article backfill would see its jobs fail after three releases without a single error. `retryUntil()` bounds the job by time instead, and `$maxExceptions` counts only exceptions.

### The failure mode to plan for

An indexing job fails silently and the article never enters the index. The agent then answers "the knowledge base does not cover it" for content that exists — which looks like a RAG quality problem and is actually an ops problem.

Track it:

```php
// last lines of handle(), in both jobs
$this->article->timestamps = false;
$this->article->forceFill(['indexed_at' => $this->article->updated_at])->saveQuietly();
```

```php
Article::whereNull('indexed_at')
       ->orWhereColumn('indexed_at', '<', 'updated_at')
       ->count();
```

`indexed_at` records which version of the article reached the index: it copies the `updated_at` the job read at its start. A plain `update(['indexed_at' => now()])` would also move `updated_at`, and the alert query could then flag a healthy article — or hide an edit made while the job was running; `saveQuietly()` also keeps the save from firing the model events again. One number, alertable. Build it now — it is the difference between a demo and a system, and nobody thinks of it until the first support ticket.

### Key takeaways

- Ingest with standalone components in a queued job, dispatched after commit.
- Guard on `wasChanged()` — do not re-embed on every save.
- Match the schema: required fields present, integers as `int`, dates as timestamps.
- `reindexBySource()` with a stable, prefixed ID as `sourceName`; delete by filter.
- Dedicated queue, rate limiting, chunked backfills, retries bounded by `retryUntil()` and `$maxExceptions`, not `$tries`.
- Track `indexed_at` and alert on the gap.

## 20.3 Permission-Aware Retrieval

### The problem

Your knowledge base has public articles, customer-only articles and internal runbooks. All in one index.

A customer asks a question. If retrieval matches an internal runbook and it enters the context, the model may paraphrase it into the answer. The user never saw the document, but they got its contents.

**That is a data breach, and it does not look like one in your logs.** No document was rendered, no endpoint was called — the leak happened inside a paraphrase.

### The fix

The thread already names the requesting user next to the tenant, so the scope grows by one condition and the agent still takes nothing in its constructor:

```php
protected function retrievalScope(): ?FilterExpression
{
    $scope = ThreadScope::of($this->getThreadId());

    return Filter::where('tenant_id', $scope->tenantId)
        ->whereIn('visibility', $this->allowedVisibilities($scope));
}

private function allowedVisibilities(ThreadScope $scope): array
{
    $user = User::where('tenant_id', $scope->tenantId)->findOrFail($scope->userId);

    return match (true) {
        $user->hasRole('staff')    => ['public', 'customer', 'internal'],
        $user->hasRole('customer') => ['public', 'customer'],
        default                    => ['public'],
    };
}
```

The role is read from the database, by ID, for the user the thread names, and the user must belong to the tenant it names. What the request is trusted for is the thread itself: the controller authorised the conversation (Section 18.2) before it bound the agent to it.

Retrieval never returns what the user may not see. The filter is computed from the actor, applied at the store. `Filter::where()` starts an AND chain; `whereIn()` matches any of the listed values. Both fields are declared filterable in the schema from Section 20.1 — filter on a field it does not declare and the store throws a `DocumentSchemaException` before touching the database, which is the failure you want.

### The rule, once more

**Filter at retrieval, never after.**

Post-filtering — retrieve everything, then drop what the user cannot see before displaying — fails because the model already read it. The only safe point is before the vector search returns.

It is the single most consequential RAG security rule, and it is not obvious.

### Testing it

```php
public function test_customer_cannot_retrieve_internal_articles(): void
{
    $this->indexArticle('Internal escalation runbook', visibility: 'internal',
        body: 'The emergency override code is OMEGA-7.');

    $answer = app(KnowledgeBaseAgent::class)
        ->for($customerConversation->threadId())
        ->chat(new UserMessage('What is the emergency override code?'))
        ->getMessage()
        ?->getContent();

    $this->assertStringNotContainsString('OMEGA-7', (string) $answer);
}
```

(`$customerConversation` is a conversation owned by a customer of the tenant, `$staffConversation` one owned by a staff member.) A distinctive token in a restricted document, and an assertion that it never surfaces. This is the contract testing from Section 1.5 applied to security: you cannot assert the answer's wording, but you can assert what must never appear in it.

Run it in CI. It is one of the few AI tests that is both deterministic enough to trust and important enough to gate a deploy.

You can make it fully deterministic by asserting one step earlier — on what reached the model, not on what the model said. Retrieved documents are injected into the instructions, so give the agent fakes for everything that would leave the process — the framework's `FakeAIProvider` for the model, `FakeEmbeddingsProvider` for the embedder and an in-memory store — and check the system prompt the provider recorded:

```php
$embeddings = new FakeEmbeddingsProvider();
$store      = new MemoryVectorStore(schema: KnowledgeBase::schema());

$runbook = new Document('The emergency override code is OMEGA-7.');
$runbook->addMetadata('tenant_id',  $tenant->id);
$runbook->addMetadata('article_id', 1);
$runbook->addMetadata('visibility', 'internal');
$store->addDocuments($embeddings->embedDocuments([$runbook]));

$ask = function (Conversation $conversation) use ($embeddings, $store): FakeAIProvider {
    $provider = new FakeAIProvider(new AssistantMessage('I cannot help with that.'));

    app(KnowledgeBaseAgent::class)
        ->setAiProvider($provider)
        ->setEmbeddingsProvider($embeddings)
        ->setVectorStore($store)
        ->for($conversation->threadId())
        ->chat(new UserMessage('What is the emergency override code?'));

    return $provider;
};

$ask($customerConversation)->assertSent(
    fn (RequestRecord $request): bool => !$request->systemPrompt?->contains('OMEGA-7')
);

// The control: the same store and question for staff does retrieve it
$ask($staffConversation)->assertSent(
    fn (RequestRecord $request): bool => $request->systemPrompt?->contains('OMEGA-7') === true
);
```

No model, no network, no database for the search, no flakiness: if the restricted chunk was retrieved for the customer, the test fails every time. The staff control matters as much as the assertion it guards. A test that fakes only the chat provider would still call the real embedder and the real store; and a test that never proves the document *can* be retrieved passes just as happily when the store is empty.

### Freshness filters

The same mechanism handles superseded content:

```php
return Filter::where('tenant_id', ThreadScope::of($this->getThreadId())->tenantId)
    ->whereGreaterThanOrEqual('updated_at', now()->subYear());
```

The syntax is portable: the same expression compiles to MariaDB, Meilisearch, Pinecone or any other built-in store. Range filters are numeric, and a date passed to one is normalised to a Unix timestamp — which is why Section 20.2 stored `updated_at` with `getTimestamp()`. A date stored as `'2026-01-31'` could not be range-filtered at all.

Useful when old and new versions of a policy both live in the index and you want the model to prefer the current one.

### Key takeaways

- One index, several visibility levels — filter or leak.
- A paraphrased leak is invisible in your logs.
- Compute allowed visibilities from the actor; apply them in `retrievalScope()`.
- Test with a distinctive token in a restricted document; run it in CI — against the fake provider, it is fully deterministic.
- Portable filters: numeric ranges, dates as timestamps, every field declared in the schema.

## 20.4 Combining RAG and Tools

### The two questions

- *"What is your refund policy?"* → prose in a document → **RAG**
- *"Has my order #4471 been refunded?"* → a row in a table → **tool**

Section 11.4 made the distinction. Here it becomes one class, because `RAG` extends `Agent` (Section 12.1).

### The agent

```php
class SupportAgent extends RAG
{
    public function __construct(
        protected MessageStoreInterface $conversations,
        protected PersistenceInterface $runs,
    ) {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return EmbeddingProvider::driver();
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return KnowledgeBase::store();
    }

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;
    }

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;
    }

    protected function contextWindow(): int
    {
        return config('neuron.context_windows.' . config('neuron.provider.default'), 29_000);
    }

    protected function retrievalScope(): ?FilterExpression
    {
        $scope = ThreadScope::of($this->getThreadId());

        return Filter::where('tenant_id', $scope->tenantId)
            ->whereIn('visibility', $this->allowedVisibilities($scope));
    }

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());
        $user  = User::where('tenant_id', $scope->tenantId)->findOrFail($scope->userId);

        return [
            new SearchOrdersTool($scope->tenantId),
            new GetOrderStatusTool($scope->tenantId),

            (new RequestRefundTool($scope->tenantId, $scope->userId))
                ->visible(Gate::forUser($user)->allows('create', Refund::class))
                ->setMaxRuns(1),
        ];
    }

    // allowedVisibilities() as in Section 20.3

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a customer support assistant.',
                'Policy questions are answered from the knowledge base articles in your context.',
                'Questions about specific orders are answered by calling your tools.',
            ],
            steps: [
                'Decide whether the question is about policy or about specific order data.',
                'For policy: answer from the provided articles and cite the article title.',
                'For order data: call the appropriate tool. Never state order details you '
                . 'have not retrieved with a tool.',
                'If neither source answers the question, offer to escalate to a human.',
            ],
            output: [
                'Answer in the user\'s language.',
                'Under 150 words unless detail is requested.',
                'Never state a monetary amount you did not retrieve from a tool.',
            ],
        );
    }
}
```

This is Chapter 18's `SupportAgent` with its base class changed from `Agent` to `RAG` and the three RAG hooks added: the same two injected stores, the same `ThreadScope`, the same `for($conversation->threadId())` in the controller. The agent is context-free; the tenant and the user come out of the thread, and the tools take scalar IDs.

### The instruction doing the most work

> *"Never state order details you have not retrieved with a tool."*

And its stronger sibling:

> *"Never state a monetary amount you did not retrieve from a tool."*

Without these the model will confidently produce an order status or a refund amount from nothing, because it has seen thousands of support conversations in training and knows what one looks like.

**Anti-hallucination instructions should be specific about the class of fact.** "Be accurate" does nothing. "Never state a monetary amount you did not retrieve" is actionable, checkable, and — with `FaithfulnessJudge` from Section 10.5 — measurable.

### One class, most of the book

Count what is in it: provider abstraction (3.6), system prompt structure (3.5), a thread that keys both the chat history and any paused refund approval and carries the tenant and the user (4.3, 18.2, 18.3), tools with dependencies (5.3), tool visibility (5.10), run limits (5.9), RAG retrieval (12.1), permission filters (20.3), and a hallucination contract (11.5).

Seven chapters in one class. That is worth pausing on: the book composes rather than accumulates, and this class is the proof.

### Key takeaways

- RAG extends Agent, so retrieval and tools live in one class.
- Tell the model which source answers which kind of question.
- Anti-hallucination instructions must name the class of fact.
- Everything from Parts II to IV composes into a single agent.

## Lab 14 — The Company Knowledge Base

**Covers:** RAG on application data, queued ingestion, permission filters, citations.

### Goal

Knowledge-base articles live in Eloquent. They are indexed automatically when they change, answered with citations, and never retrievable by someone who should not see them.

### Requirements

1. **An `articles` table** with `body`, `title`, `tenant_id`, `visibility` (`public` / `customer` / `internal`) and `indexed_at`.
2. **Automatic indexing** on save, guarded by `wasChanged('body')`, dispatched to a dedicated `indexing` queue with retries and rate limiting.
3. **`reindexBySource()`** using the prefixed article ID (`article-42`) as the stable source name, against a store whose `DocumentSchema` declares every field you filter on and whose table a migration creates with the embedding dimension pinned. Editing an article must replace its chunks, not add to them.
4. **Deletion** removes the article's chunks from the index.
5. **Permission-aware retrieval** as in Section 20.3, computed from the requesting user's role.
6. **Citations.** Every factual claim in an answer names its source article. If the knowledge base does not cover the question, the agent says so and offers escalation.

### Acceptance criteria

- Editing an article and asking about the changed passage returns the new content, and a phrase you deleted is no longer retrievable.
- A customer cannot obtain the contents of an `internal` article, tested with a distinctive token as in Section 20.3.
- `Article::whereNull('indexed_at')->orWhereColumn('indexed_at', '<', 'updated_at')->count()` returns zero after the queue drains — and you have an alert for when it does not.
- Touching an article without changing its body dispatches no indexing job. Assert on the queue, not on the logs.
- An out-of-scope question produces the escalation offer, not an invented answer.

### The measurement

Build a fifteen-question evaluation set against your real articles, with a `FaithfulnessJudge` assertion (Section 10.5). Record the score before and after you switch to a heading-aware splitter.

That number is what you show a stakeholder. "The knowledge base agent answers faithfully 0.87 of the time, measured over fifteen representative questions, and here is the trend since we changed the chunking" is a fundamentally different conversation from "it seems pretty good".

### Going further

Add the escalation path for real: when the agent offers to escalate and the user accepts, create a support ticket containing the question, the retrieved articles and the agent's answer. You have now built the first half of Capstone B.
