# Chapter 20 — RAG on Application Data

## 20.1 A RAG Agent in Laravel

### The class

```php
namespace App\Neuron\Rag;

use App\Models\Tenant;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class KnowledgeBaseAgent extends RAG
{
    protected array $vectorStoreFilters = [];

    public function __construct(
        private readonly Tenant $tenant,
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
        $store = VectorStore::driver();

        return $store->withFilters(\array_merge(
            ['tenant_id' => $this->tenant->id],
            $this->vectorStoreFilters,
        ));
    }

    public function addVectorStoreFilters(array $filters): self
    {
        $this->vectorStoreFilters = $filters;

        return $this;
    }

    public function instructions(): string
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

### The tenant filter is not optional

`withFilters(['tenant_id' => $this->tenant->id])` is applied unconditionally in `vectorStore()`, merged with any runtime filters. There is no code path that queries the store without it.

Section 12.6's rule: **filter at retrieval, never after.** A document retrieved and then excluded from the answer was still in the model's context, and models paraphrase. The tenant filter is the RAG equivalent of a `where tenant_id = ?` on every query — and it belongs in the same place, at the component that builds the query.

::: {.callout .callout-warning}
[Check the method name and the driver list]{.callout-title}

`withFilters()` versus `withFilter()` is unresolved across the documentation (Appendix A, item 26 and item 43), and the set of vector store drivers `VectorStore::driver()` actually exposes depends on your published `config/neuron.php` (item 44). Confirm both before you build ingestion on top of them.
:::

### Choosing a store in Laravel

From Section 12.5, with the Laravel lens:

**MariaDB 11.7+** — one table in the database you already run. Backups, monitoring, transactions and failover already solved. For most Laravel applications this is the right answer.

**PHPVector** — `neuron-core/php-vector`, pure PHP, HNSW plus BM25 hybrid search, no service. Good for self-hosted deployments and clients who cannot add infrastructure.

**Elasticsearch or Meilisearch** — if you already run one for site search, use it and avoid a second system.

**Pinecone or Qdrant** — when scale genuinely demands a dedicated database.

The general rule stands: **use what you already run.**

### Key takeaways

- Three facades, three driver calls, everything else in config.
- Apply the tenant filter inside `vectorStore()` so no path bypasses it.
- MariaDB or PHPVector for most Laravel applications.

## 20.2 Queued Ingestion

### The job

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\Article;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
use NeuronAI\RAG\DataLoader\StringDataLoader;

class IndexArticle implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;
    public int $backoff = 30;

    public function __construct(
        public readonly Article $article,
    ) {}

    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)
            ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
            ->getDocuments();

        foreach ($documents as $document) {
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->toDateString());
        }

        $store    = VectorStore::driver();
        $embedder = EmbeddingProvider::driver();

        $store->addDocuments($embedder->embedDocuments($documents));
    }
}
```

Standalone components (Section 12.2) rather than a RAG agent — ingestion needs no chat provider, no instructions, no tools. Keeping the job lean means it starts faster and has fewer reasons to fail.

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

### Reindexing rather than adding

```php
class ReindexArticle implements ShouldQueue
{
    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)->getDocuments();

        foreach ($documents as $document) {
            $document->addMetadata('tenant_id', $this->article->tenant_id);
            // sourceName must be stable — the ID, never the title
        }

        (new KnowledgeBaseAgent($this->article->tenant))
            ->reindexBySource($documents);
    }
}
```

Section 12.6's constraint, restated because it is easy to get wrong: **`sourceName` must be stable.** Use the article ID. Derive it from the title and an editorial rename orphans the old chunks — they stay in the index, un-deletable by source, and the agent answers from both versions.

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

**Chunked backfills.** For an initial index, `chunkById()` and dispatch in batches rather than loading everything into memory.

**Retries with backoff.** `$tries = 3`, `$backoff = 30`. Transient provider failures are normal.

### The failure mode to plan for

An indexing job fails silently and the article never enters the index. The agent then answers "the knowledge base does not cover it" for content that exists — which looks like a RAG quality problem and is actually an ops problem.

Track it:

```php
$article->update(['indexed_at' => now()]);
```

```php
Article::whereNull('indexed_at')
       ->orWhereColumn('indexed_at', '<', 'updated_at')
       ->count();
```

One number, alertable. Build it now — it is the difference between a demo and a system, and nobody thinks of it until the first support ticket.

### Key takeaways

- Ingest with standalone components in a queued job.
- Guard on `wasChanged()` — do not re-embed on every save.
- `reindexBySource()` with a stable ID as `sourceName`.
- Dedicated queue, rate limiting, chunked backfills, retries.
- Track `indexed_at` and alert on the gap.

## 20.3 Permission-Aware Retrieval

### The problem

Your knowledge base has public articles, customer-only articles and internal runbooks. All in one index.

A customer asks a question. If retrieval matches an internal runbook and it enters the context, the model may paraphrase it into the answer. The user never saw the document, but they got its contents.

**That is a data breach, and it does not look like one in your logs.** No document was rendered, no endpoint was called — the leak happened inside a paraphrase.

### The fix

```php
protected function vectorStore(): VectorStoreInterface
{
    return VectorStore::driver()->withFilters([
        'tenant_id'  => $this->tenant->id,
        'visibility' => $this->allowedVisibilities(),
    ]);
}

private function allowedVisibilities(): array
{
    return match (true) {
        $this->user->hasRole('staff')    => ['public', 'customer', 'internal'],
        $this->user->hasRole('customer') => ['public', 'customer'],
        default                          => ['public'],
    };
}
```

Retrieval never returns what the user may not see. The filter is computed from the actor, applied at the store.

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

    $answer = (new KnowledgeBaseAgent($tenant, $customerUser))
        ->chat(new UserMessage('What is the emergency override code?'))
        ->getMessage()
        ->getContent();

    $this->assertStringNotContainsString('OMEGA-7', $answer);
}
```

A distinctive token in a restricted document, and an assertion that it never surfaces. This is the contract testing from Section 1.5 applied to security: you cannot assert the answer's wording, but you can assert what must never appear in it.

Run it in CI. It is one of the few AI tests that is both deterministic enough to trust and important enough to gate a deploy.

### Freshness filters

The same mechanism handles superseded content:

```php
->withFilters([
    'tenant_id'  => $this->tenant->id,
    'updated_at' => ['$gte' => now()->subYear()->toDateString()],
])
```

Filter syntax is store-specific — check your store's documentation.

Useful when old and new versions of a policy both live in the index and you want the model to prefer the current one.

### Key takeaways

- One index, several visibility levels — filter or leak.
- A paraphrased leak is invisible in your logs.
- Compute allowed visibilities from the actor; apply at the store.
- Test with a distinctive token in a restricted document; run it in CI.

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
        private readonly Tenant $tenant,
        private readonly User $user,
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
        return VectorStore::driver()->withFilters([
            'tenant_id'  => $this->tenant->id,
            'visibility' => $this->allowedVisibilities(),
        ]);
    }

    protected function tools(): array
    {
        return [
            new SearchOrdersTool($this->tenant),
            new GetOrderStatusTool($this->tenant),

            (new RequestRefundTool($this->refunds, $this->user))
                ->visible($this->user->can('create', Refund::class))
                ->setMaxRuns(1),
        ];
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            thread_id: "t{$this->tenant->id}:u{$this->user->id}",
            modelClass: ChatMessage::class,
            contextWindow: config('neuron.context_window'),
        );
    }

    public function instructions(): string
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

### The instruction doing the most work

> *"Never state order details you have not retrieved with a tool."*

And its stronger sibling:

> *"Never state a monetary amount you did not retrieve from a tool."*

Without these the model will confidently produce an order status or a refund amount from nothing, because it has seen thousands of support conversations in training and knows what one looks like.

**Anti-hallucination instructions should be specific about the class of fact.** "Be accurate" does nothing. "Never state a monetary amount you did not retrieve" is actionable, checkable, and — with `FaithfulnessJudge` from Section 10.5 — measurable.

### One class, most of the book

Count what is in it: provider abstraction (3.6), system prompt structure (3.5), chat history with tenant isolation (4.3, 18.3), tools with dependencies (5.3), tool visibility (5.10), run limits (5.9), RAG retrieval (12.1), permission filters (20.3), and a hallucination contract (11.5).

Nine chapters in forty lines. That is worth pausing on: the book composes rather than accumulates, and this class is the proof.

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
3. **`reindexBySource()`** using the article ID as the stable source name. Editing an article must replace its chunks, not add to them.
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
