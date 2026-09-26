# Chapter 12 — The NeuronAI RAG Pipeline

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch12`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch12), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

## 12.1 The RAG Class

### Generate it

```bash
# Unix
vendor/bin/neuron make:rag App\\Neuron\\MyChatBot

# Windows
.\vendor\bin\neuron make:rag App\Neuron\MyChatBot
```

### The class

```php
namespace App\Neuron;

use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Embeddings\OpenAIEmbeddingsProvider;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\FileVectorStore;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class MyChatBot extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(
            key: 'ANTHROPIC_API_KEY',
            model: 'ANTHROPIC_MODEL',
        );
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return new OpenAIEmbeddingsProvider(
            key: 'OPENAI_API_KEY',
            model: 'OPENAI_MODEL'
        );
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return new FileVectorStore(
            directory: __DIR__,
            name: 'demo'
        );
    }
}
```

Three methods instead of the Agent's one. Same shape, two extra components:

- `provider()` — the chat model, as before
- `embeddings()` — turns text into vectors
- `vectorStore()` — stores and searches them

**Note that these are two different models.** Your provider might be Claude; your embeddings provider might be OpenAI or a local Ollama model. They are independent choices, and mixing them is normal rather than a mistake.

### Using it

```php
use App\Neuron\MyChatBot;
use NeuronAI\Chat\Messages\UserMessage;

$state = MyChatBot::make()
    ->chat(new UserMessage('I want to know more about Inspector AI Bug Fix.'));

echo $state->getMessage()?->getContent();
```

`chat()` — the same method as an ordinary agent, returning the same final `AgentState`. Retrieval happens inside, automatically. From the calling side, a RAG agent and a plain agent are indistinguishable. (`getMessage()` is nullable because a run that paused before any inference — a tool awaiting approval, say — has no answer yet; hence the `?->`.)

### RAG *is* an Agent

This is Section 2.3 arriving for the third time, and it has practical consequences:

> The NeuronAI `RAG` class extends the basic `Agent` class. Your RAG is always an agent, so you can attach tools and define system instructions.

Which means a RAG agent inherits, for free:

- `instructions()` and `SystemPrompt`
- `tools()` and toolkits
- `chatHistory()`
- `structured()`
- `stream()`
- `subscribe()` for tracing events
- thread identity, persistence and resume
- Everything from Chapters 3 through 10

### The combined pattern

The documentation's example is a good one — workout tips from a knowledge base, plus a tool for the user's current status:

```php
class WorkoutTipsAgent extends RAG
{
    protected function provider(): AIProviderInterface { /* ... */ }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are an AI Agent specialized in providing workout tips.'],
        );
    }

    protected function embeddings(): EmbeddingsProviderInterface { /* ... */ }

    protected function vectorStore(): VectorStoreInterface { /* ... */ }

    protected function tools(): array
    {
        return [
            CalculatorToolkit::make(),
        ];
    }
}
```

Knowledge from retrieval, facts from tools, arithmetic from the toolkit. That is Section 11.4's "they compose", in one class.

::: {.callout .callout-warning}
[The vector store signature — check this before you write anything]{.callout-title}

The documentation has shown `FileVectorStore` several ways across several pages — `name:` on one, `topK:` on another, and at one point a `key:` argument under a misspelled class name, `FileVectoreStore`. Likewise `OpenAIEmbeddingsProvider` vs `OpenAIEmbeddingProvider`, and `RAG\Embeddings\` vs `RAG\EmbeddingProvider\`. Appendix A, items 22 to 25.

The source settles it. The constructor is `FileVectorStore(string $directory, int $topK = 4, string $name = 'neuron', string $ext = '.store', ?DocumentSchema $schema = null)` — there is no `key:` — and the embeddings classes live in `NeuronAI\RAG\Embeddings\`, with the `s`. This is the highest-traffic code in Part III: open the class in your editor and check it before you write an ingestion script, not after.
:::

### Key takeaways

- Three methods: `provider()`, `embeddings()`, `vectorStore()`.
- The chat model and the embeddings model are independent choices.
- `chat()` returns the same `AgentState` as any agent; retrieval is internal.
- RAG inherits every Agent feature, including tools.

## 12.2 Data Loaders and Readers

### The one-liner

```php
use App\Neuron\MyRAG;
use NeuronAI\RAG\DataLoader\FileDataLoader;

MyRAG::make()->addDocuments(
    FileDataLoader::for(__DIR__.'/my-article.md')->getDocuments()
);
```

Load, split, embed, store — four operations, one statement.

### FileDataLoader

Point it at a file or a directory:

```php
// A single file
$documents = FileDataLoader::for(__DIR__.'/my-article.md')->getDocuments();

// Every file in a directory
$documents = FileDataLoader::for(__DIR__)->getDocuments();
```

By default it reads file contents as plain text. Not every format is plain text, which is what readers are for.

### Readers

**Each reader is bound to a file extension.** The loader picks the right one automatically based on what it finds.

**PDF:**

```php
$documents = FileDataLoader::for(__DIR__)
    ->addReader('pdf', new \NeuronAI\RAG\DataLoader\PdfReader())
    ->getDocuments();
```

Requires the **poppler** utility (`pdftotext`) on the system. A system dependency, not a Composer one — which is why "it works on my machine" here usually means "poppler is installed on my machine".

```bash
sudo apt install poppler-utils    # Debian/Ubuntu
brew install poppler              # macOS
```

**HTML:**

```php
$documents = FileDataLoader::for(__DIR__)
    ->addReader(['html', 'xhtml'], new \NeuronAI\RAG\DataLoader\HtmlReader())
    ->getDocuments();
```

Requires `mtibben/html2text`:

```bash
composer require mtibben/html2text
```

Note it converts HTML **to Markdown** rather than stripping tags. That matters: headings survive as `##`, which means a heading-aware splitter (Section 12.3) can use them. Stripping to plain text would throw that structure away.

An extension can map to several readers, or several extensions to one reader — `['html', 'xhtml']` above.

### StringDataLoader

For text you already have — from a database, an API, an editor:

```php
use NeuronAI\RAG\DataLoader\StringDataLoader;

$contents = [
    // list of strings (text you want to embed)
];

foreach ($contents as $text) {
    $documents = StringDataLoader::for($text)->getDocuments();

    MyRAG::make()->addDocuments($documents);
}
```

**This is the loader you will use most in a real application.** Your knowledge base is probably rows in a table — articles, product descriptions, policy records — not files on disk. The file loader gets the documentation space; the string loader gets the production use.

One efficiency note on that example: it constructs the RAG agent inside the loop. Hoist it:

```php
$rag = MyRAG::make();

foreach ($contents as $text) {
    $rag->addDocuments(StringDataLoader::for($text)->getDocuments());
}
```

### Standalone components

You do not need a RAG agent to ingest. The embeddings provider and vector store work independently:

```php
$embedder = new OpenAIEmbeddingsProvider(
    key: 'OPENAI_API_KEY',
    model: 'OPENAI_MODEL'
);

$store = new FileVectorStore(
    directory: __DIR__,
    name: 'demo'
);

$documents = FileDataLoader::for(__DIR__.'/documents')
    ->addReader('pdf', new \NeuronAI\RAG\DataLoader\PdfReader())
    ->getDocuments();

$store->addDocuments(
    $embedder->embedDocuments($documents)
);
```

**The store must be the same one your RAG agent uses.** Same directory, same index, same collection. This is the single most common ingestion bug: you index into one store and query another, and the agent reports it knows nothing.

**Why use standalone components?** Because ingestion and querying are different jobs with different lifecycles. Ingestion is a batch process, a cron job, a queue worker. It does not need a chat provider configured, an API key for the LLM, or the agent's instructions. Separating them keeps your ingestion script lean and makes it deployable independently.

This is also the pattern Chapter 20 uses in Laravel, where ingestion runs as a queued job.

### Key takeaways

- `FileDataLoader::for($path)->getDocuments()` for files and directories.
- Readers map to extensions; PDF needs poppler, HTML needs `mtibben/html2text`.
- HTML converts to Markdown, preserving structure for the splitter.
- `StringDataLoader` is what you will actually use — most knowledge bases are database rows.
- Ingest with standalone components; the store must be identical to the agent's.

## 12.3 Splitters

### Attaching a splitter

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new DelimiterTextSplitter())
    ->getDocuments();
```

### DelimiterTextSplitter — the default

This is what every data loader uses when you do not call `withSplitter()`:

```php
new DelimiterTextSplitter(
    maxLength: 1000,
    separator: '.',
    wordOverlap: 0
)
```

The three parameters from Section 11.3, in code:

- **`maxLength`** — chunks no longer than this
- **`separator`** — where cuts are allowed; the loaders pass the period
- **`wordOverlap`** — words carried between chunks; zero by default

Construct the class yourself and the separator defaults to a space, not a period — one more reason to pass all three explicitly. A fourth, optional `minLength` merges a fragment shorter than that into the chunk before it, so a stray closing sentence does not become a chunk of its own.

The documentation is explicit that each of these affects performance and accuracy. They are not defaults to accept; they are decisions to make.

### SentenceTextSplitter

```php
new SentenceTextSplitter(
    maxWords: 200,
    overlapWords: 0
)
```

Splits into sentences, groups them into word-based chunks, optionally overlaps by words. Its `minWords` plays the same role as `minLength`.

**Which to use.** `SentenceTextSplitter` is generally better for prose because word counts track token counts more closely than character counts do, and grouping whole sentences avoids mid-sentence cuts. `DelimiterTextSplitter` is better when your content has a structural delimiter worth cutting on — which brings us to the important part.

### Custom splitters: the highest-leverage code in your RAG

```php
namespace NeuronAI\RAG\Splitter;

use NeuronAI\RAG\Document;

interface SplitterInterface
{
    /**
     * @return Document[]
     */
    public function splitDocument(Document $document): array;

    /**
     * @param  Document[]  $documents
     * @return Document[]
     */
    public function splitDocuments(array $documents): array;
}
```

Two methods. Here is a Markdown heading splitter — perhaps forty lines, and it will outperform any generic splitter on documentation:

```php
<?php

declare(strict_types=1);

namespace App\Rag;

use NeuronAI\RAG\Document;
use NeuronAI\RAG\Splitter\SplitterInterface;

class MarkdownSectionSplitter implements SplitterInterface
{
    public function __construct(
        private readonly int $maxChars = 2000,
    ) {}

    public function splitDocument(Document $document): array
    {
        // Split on level-2 headings, keeping the heading with its section
        $parts = \preg_split(
            '/^(?=##\s)/m',
            $document->getContent(),
            -1,
            PREG_SPLIT_NO_EMPTY
        ) ?: [];

        $chunks = [];

        foreach ($parts as $part) {
            $part = \trim($part);

            if ($part === '') {
                continue;
            }

            // Fall back to paragraph splitting for oversized sections
            if (\mb_strlen($part) > $this->maxChars) {
                foreach ($this->splitLongSection($part) as $piece) {
                    $chunks[] = $piece;
                }
                continue;
            }

            $chunks[] = $part;
        }

        // Each chunk keeps its parent's provenance and metadata
        return \array_map(
            fn (string $text): Document => (new Document($text))
                ->setSourceType($document->getSourceType())
                ->setSourceName($document->getSourceName())
                ->setMetadata($document->getMetadata()),
            $chunks
        );
    }

    public function splitDocuments(array $documents): array
    {
        $result = [];

        foreach ($documents as $document) {
            foreach ($this->splitDocument($document) as $chunk) {
                $result[] = $chunk;
            }
        }

        return $result;
    }

    /**
     * @return string[]
     */
    private function splitLongSection(string $section): array
    {
        $paragraphs = \preg_split('/\n{2,}/', $section) ?: [];

        $chunks  = [];
        $current = '';

        foreach ($paragraphs as $paragraph) {
            if (\mb_strlen($current . "\n\n" . $paragraph) > $this->maxChars && $current !== '') {
                $chunks[] = \trim($current);
                $current  = $paragraph;
                continue;
            }

            $current = $current === '' ? $paragraph : $current . "\n\n" . $paragraph;
        }

        if (\trim($current) !== '') {
            $chunks[] = \trim($current);
        }

        return $chunks;
    }
}
```

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();
```

::: {.callout .callout-warning}
[A chunk must inherit its parent's provenance]{.callout-title}

The docs show `Document` in interface signatures but never show it being constructed (Appendix A, item 29). The class settles it: `new Document(string $content)`, then fluent setters — `setSourceType()`, `setSourceName()`, `setMetadata()` — and getters for each. There are no public properties to poke at, and the class is `final`.

The three setters in `splitDocument()` are not decoration. A bare `new Document($text)` is filed under source type and name `manual`, so every chunk would lose the file it came from, `reindexBySource()` (Section 12.6) could never find it again, and any tenant metadata you attached before splitting would vanish. The built-in splitters copy all three; a custom one must do the same.
:::

### Why this matters so much

Every chunk this produces is a complete, self-contained section with its own heading. A retrieval hit brings back a coherent unit rather than an arbitrary 1,000-character window that starts mid-sentence.

**The heading also becomes part of the embedded text**, which means a question phrased like the heading matches strongly. That is a free relevance boost, purely from respecting the document's own structure.

The general principle: **the best chunking strategy is the one your document already has.** Markdown has headings. Code has functions. Transcripts have speakers. Use them.

### Key takeaways

- `withSplitter()` on any data loader.
- `DelimiterTextSplitter` for structural delimiters; `SentenceTextSplitter` for prose.
- `SplitterInterface` is two methods — a custom splitter is an afternoon's work. Copy source and metadata onto every chunk.
- Respect the document's own structure; it is the biggest quality lever in RAG.

## 12.4 Embeddings Providers

### The interface

```php
protected function embeddings(): EmbeddingsProviderInterface
{
    return new OpenAIEmbeddingsProvider(
        key: 'OPENAI_API_KEY',
        model: 'OPENAI_MODEL'
    );
}
```

Same shape as every other component. Swappable — with one very large caveat.

### Local embeddings with Ollama

```php
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Embeddings\OllamaEmbeddingsProvider;

class MyRAG extends RAG
{
    protected function embeddings(): EmbeddingsProviderInterface
    {
        return new OllamaEmbeddingsProvider(
            model: 'OLLAMA_EMBEDDINGS_MODEL'
        );
    }
}
```

No API key, no cost, no data leaving the machine.

```bash
ollama pull nomic-embed-text
```

**Use this for every lab in Part III.** Combined with a local chat model from Section 3.6, the entire RAG part costs nothing to work through.

It is also a legitimate production choice. Embedding models are small and fast; running one locally is very different from running a frontier chat model locally.

### Hosted options

`OpenAIEmbeddingsProvider`, `VoyageEmbeddingsProvider` and others. Voyage in particular is worth knowing about — it specialises in retrieval embeddings and often outperforms general-purpose models on RAG benchmarks.

### Custom providers

Extend `AbstractEmbeddingsProvider`. Same extension story as everywhere else in the framework.

### The caveat that is not like the others

Section 3.6 taught that swapping providers is a one-line change. **Embeddings are the exception.**

Change the embeddings model and every vector in your store becomes meaningless. They are coordinates in a different space. Retrieval will return results — it will not fail loudly — and they will be wrong.

**Changing the embeddings model means re-embedding the entire corpus.**

Three practical consequences:

- Record which model produced your index. In the store's name, in a metadata field, in a deployment note — somewhere.
- Budget re-embedding time before you switch. Millions of chunks is hours and real money.
- Never make the embeddings model an environment variable that differs between environments. Development on `nomic-embed-text` and production on `text-embedding-3-large` means your dev index and prod index are incompatible, and the bug will be baffling.

That last one is a genuinely nasty trap, and it is the natural mistake for someone who has just learned the `ProviderFactory` pattern from Section 3.6.

### Dimensions

Different models produce different vector lengths — 768, 1024, 1536 and others. Your vector store must be configured to match. `TypesenseVectorStore` takes `vectorDimension: 1024`; `MariaDBVectorStore::setupTable(dimensions: 768)` creates a `VECTOR(768)` column, and defaults to 1536 if you do not say.

Mismatch means either a hard error or silent nonsense, depending on the store. Check it when you set up.

### Key takeaways

- `OllamaEmbeddingsProvider` runs locally, free — use it for all labs.
- Hosted options include OpenAI and Voyage; Voyage is retrieval-specialised.
- **Changing the embeddings model invalidates your entire index.**
- Never vary the embeddings model across environments.
- Vector dimensions must match your store's configuration.

## 12.5 Vector Stores

### The interface

```php
namespace NeuronAI\RAG\VectorStore;

use NeuronAI\RAG\Document;
use NeuronAI\RAG\Schema\DocumentSchema;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;

interface VectorStoreInterface
{
    public function getSchema(): DocumentSchema;

    public function addDocument(Document $document): VectorStoreInterface;

    /**
     * @param  Document[]  $documents
     */
    public function addDocuments(array $documents): VectorStoreInterface;

    /**
     * Delete every document matching the filters.
     */
    public function delete(FilterExpression $filters): VectorStoreInterface;

    /**
     * Return the documents most similar to the request's embedding.
     *
     * @return iterable<Document>
     */
    public function search(SearchRequest $request): iterable;
}
```

Five methods. Three of them say something about the framework's priorities.

`search()` takes a `SearchRequest` — embedding, optional filters, optional `topK` — built fresh for every call. A store holds no search state, so a filter you set for one query cannot quietly constrain, or fail to constrain, the next.

`delete()` takes a filter rather than a hard-coded pair of fields. It exists to support reindexing (Section 12.6), which tells you the framework treats staleness as a first-class problem rather than an afterthought.

`getSchema()` returns the store's `DocumentSchema`: the declaration of which metadata fields exist, what type they are, and which ones you may filter on. It is optional to configure and central to filtering; both are covered below.

### The catalogue

**Memory** — volatile, current session only. For tests and throwaway interactions.

```php
return new MemoryVectorStore();
```

**File** — filesystem storage, and better engineered than it sounds:

```php
return new FileVectorStore(
    directory: storage_path(),
    topK: 4
);
```

The documentation makes a point worth repeating: it uses **PHP generators** to read documents, so it never holds more than `topK` items in memory while iterating quickly. You can store thousands of documents and the only constraint is how long a similarity search may take. It creates the directory and an empty store file on construction, so a brand-new store is safe to search, delete from or reindex straight away.

There is also a distribution use for it: ship an agent with knowledge already baked into a file. That is a genuinely nice pattern for a packaged tool or a demo.

**PHPVector** — pure PHP, no external service. Built on `ezimuel/phpvector`, it implements **HNSW** for approximate nearest-neighbour search and **BM25** for full-text retrieval, and combines the two into a genuine **hybrid search** pipeline — vector and lexical ranking together. That makes it the most interesting entry in the list for a PHP audience: production-grade retrieval with no service to deploy.

::: {.callout .callout-warning}
[PHPVector has no release for this version of NeuronAI yet]{.callout-title}

`neuron-core/php-vector` ships separately from the framework, and at the time of writing its latest release (1.1.0) still requires the previous major version of `neuron-ai` (3.x). Composer will refuse to install it next to this book's version, and that release implements an older store interface anyway. Watch the package for a release that supports the `search()`/`delete()`/`getSchema()` interface above; until then, the labs in this chapter use `FileVectorStore` and `MariaDBVectorStore`, and the companion repository does not depend on it.
:::

**MariaDB** — native vectors from 11.7:

```php
$store = new MariaDBVectorStore(
    pdo: new \PDO($dsn, $user, $password), // Or get the PDO instance from the ORM
    tableName: 'rag_documents',
);

$store->setupTable(dimensions: 768); // once, at install time
```

`setupTable()` creates the table the store expects:

```sql
CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID NOT NULL PRIMARY KEY,
    content TEXT,
    sourceType VARCHAR(255),
    sourceName VARCHAR(255),
    metadata JSON,
    embedding VECTOR(768) NOT NULL,
    VECTOR INDEX (embedding)
)
```

For a PHP shop already running MariaDB, this is the lowest-friction production answer: one table, no new service, backups and monitoring you already have. Note the schema — `sourceType` and `sourceName` are there for reindexing, and `metadata JSON` for filtering.

**Managed and dedicated:** Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch, and MongoDB Atlas Vector Search. Each takes its own connection configuration; several need their official client installed via Composer.

::: {.callout .callout-warning}
[There is no pgvector store]{.callout-title}

The list above is complete. A great deal of third-party material assumes NeuronAI ships a pgvector integration, because pgvector is ubiquitous in the Python ecosystem. It does not. If you are on Postgres and want first-party support, your options are one of the dedicated stores — or, once it ships a compatible release, PHPVector, which does not care what database you run. A custom store (below) is the third route.
:::

### The decision table

| Situation | Store |
|---|---|
| Unit tests | Memory |
| Labs, prototypes, small corpora | File |
| Already running MariaDB 11.7+ | **MariaDB** |
| Self-hosted, no new infrastructure, want hybrid search | PHPVector, once it supports this version |
| Already running Elasticsearch, OpenSearch or MongoDB Atlas | That one |
| Want managed, billions of vectors | Pinecone |
| Want open-source dedicated | Qdrant, Weaviate, Chroma |

**The general rule: use what you already run.** A new database is a new backup story, a new monitoring story and a new failure mode. MariaDB — and PHPVector, when it catches up — exist precisely so that most PHP teams do not need any of that.

### Filtered search

Every built-in store can narrow a similarity search to documents whose metadata matches a condition. You write the condition once, in a portable vocabulary, and each store compiles it to its own native syntax — the same filter runs on the file store in development and on Pinecone or MariaDB in production.

Two pieces make it work. The store is told which metadata fields exist and which are filterable, through a `DocumentSchema`. The agent declares the mandatory constraint for its searches in `retrievalScope()`:

```php
use NeuronAI\RAG\Schema\DocumentField;
use NeuronAI\RAG\Schema\DocumentSchema;
use NeuronAI\RAG\VectorStore\Filter\Filter;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;

class MyChatBot extends RAG
{
    protected ?string $tenantId = null;

    public function forTenant(string $tenantId): static
    {
        $this->tenantId = $tenantId;
        return $this;
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return new PineconeVectorStore(
            key: 'PINECONE_API_KEY',
            indexUrl: 'PINECONE_INDEX_URL',
            schema: DocumentSchema::of(
                DocumentField::string('tenant_id')->required()->filterable(),
                DocumentField::string('visibility')->required()->filterable(),
            ),
        );
    }

    protected function retrievalScope(): ?FilterExpression
    {
        if ($this->tenantId === null) {
            // Fail closed: an unscoped search would cross tenants
            throw new \LogicException('Call forTenant() before chatting.');
        }

        return Filter::where('tenant_id', $this->tenantId)
            ->where('visibility', 'public');
    }
}
```

```php
$response = MyChatBot::make()
    ->forTenant($tenant->uuid)
    ->chat(new UserMessage($question))
    ->getMessage();
```

**This is the mechanism for multi-tenant RAG**, and it is important enough to flag loudly. Filtering by `tenant_id` at query time means user A's search cannot return user B's documents. Without it, a shared vector store leaks across tenants — which is a data breach, not a bug.

Note the guard. Returning `null` from `retrievalScope()` means "no constraint", so a missing tenant must be an error, never a quiet fallback to searching everyone's documents.

The scope is not a suggestion the pipeline may override. Anything else that adds a filter during a run — a middleware, a custom retrieval strategy — is combined with it by AND, so a later filter can narrow the search but never widen it. When the value is only known at runtime, `setRetrievalScope()` sets the same thing from outside the class.

The vocabulary covers what applications actually need — `where()`, `whereNot()`, `whereIn()`, the numeric ranges (`whereGreaterThan()`, `whereLessThanOrEqual()` and friends), `whereContainsAny()`/`whereContainsAll()` for string-list fields — plus `FilterGroup::anyOf()` and `allOf()` for nested OR/AND logic. For the rare backend feature outside it, `Filter::raw(PineconeVectorStore::class, $nativeFragment)` passes native syntax through to that store and makes every other store throw, so swapping stores fails loudly instead of silently mis-filtering.

Chapter 20 builds this properly in Laravel.

::: {.callout .callout-warning}
[An undeclared field is a hard error, not an empty result]{.callout-title}

Filter on a metadata field the store's schema does not declare filterable — a typo, or a field you forgot to declare — and the store throws a `DocumentSchemaException` before it touches the database. Only `sourceType`, `sourceName` and declared filterable fields are valid filter targets. Two more rules to know before you design the schema: filter values are scalars (`null` throws, because "missing" and "null" mean different things on different databases), and `whereNot()` is only allowed on a `required()` field, for the same reason.

That strictness is the point. A filter that silently matched nothing — or everything — on one backend and not another would be the worst kind of multi-tenant bug.
:::

### Custom stores

Implement the interface. Four details matter:

**Return scores, not distances.** Convert with `VectorSimilarity::similarityFromDistance()`.

**Honour the schema.** Validate documents and filters against `getSchema()` before any database I/O; the `HasDocumentSchema` trait the built-in stores use gives you the plumbing.

**Compile or evaluate the filters.** Translate the `FilterExpression` into your backend's syntax — or, for a store that scans in PHP, evaluate it with `FilterEvaluator`, as the file and memory stores do.

**`addDocument()` can delegate to `addDocuments()`** if your database has no separate single-item API. The two methods exist because many databases do.

The maintainers explicitly invite pull requests for new stores. If you want a well-scoped, genuinely useful piece of open-source contribution, this is one.

### Key takeaways

- Five-method interface; `search()` takes a fresh `SearchRequest` every call, and `delete()` takes a filter.
- `FileVectorStore` uses generators and scales further than expected.
- **MariaDB 11.7+** is the lowest-friction production option for most PHP shops.
- PHPVector's HNSW + BM25 hybrid search awaits a release for this version of the framework.
- Declare filterable fields in a `DocumentSchema`; put mandatory constraints in `retrievalScope()`.
- Metadata filters are how you do multi-tenant RAG safely.
- Use what you already run.

## 12.6 Metadata and Reindexing

### Metadata

```php
$documents = FileDataLoader::for($directory)->getDocuments();

foreach ($documents as $document) {
    $document->addMetadata('user_id', 1234);
}

MyRAG::make()->addDocuments($documents);
```

Custom fields saved alongside the document's default fields in the store. Any JSON-safe value is accepted and round-trips — stored, then returned on the retrieved document's `getMetadata()`. A handful of names (`id`, `content`, `embedding`, `score`, `sourceType`, `sourceName`, `metadata` and a few backend-internal ones) are reserved, and `addMetadata()` throws if you use one.

### What to attach

Think of metadata as the columns you will want to filter on later. Once the index is built, adding a field means re-indexing — so decide now:

```php
foreach ($documents as $document) {
    $document->addMetadata('tenant_id',   $tenant->uuid);
    $document->addMetadata('visibility',  'internal');
    $document->addMetadata('language',    'en');
    $document->addMetadata('updated_at',  $article->updated_at->getTimestamp());
    $document->addMetadata('category',    $article->category);
}
```

Then tell the store about the ones you will filter on:

```php
$schema = DocumentSchema::of(
    DocumentField::string('tenant_id')->required()->filterable(),
    DocumentField::string('visibility')->required()->filterable(),
    DocumentField::string('language')->filterable(),
    DocumentField::integer('updated_at')->filterable(),
);
```

`category` is not declared: it is stored and returned, but not filterable. That is a deliberate choice, not a loophole — declare a field when the database needs to know its type, because it must be present on every document (`required()`) or because you filter on it (`filterable()`). Note `updated_at` is an integer timestamp, not a date string: range filters are numeric, and a `DateTimeInterface` passed to a range filter is converted to a timestamp for you.

`RAG::addDocuments()` validates every document against the schema *before* calling the embeddings model, so a chunk missing its `tenant_id` fails fast instead of costing you an embedding call and a half-written batch.

Four things worth attaching almost always:

**Tenant or owner.** The security boundary for multi-tenant retrieval. Non-negotiable if you serve more than one customer from one index.

**Visibility or permission level.** So a public-facing agent cannot retrieve internal documents.

**Language.** Cross-language retrieval mostly works and occasionally produces confusing results.

**Freshness.** A date lets you prefer or filter recent content — useful when old and new versions of a policy both live in the index.

### Filtering at retrieval

Once the fields are in the store and declared in its schema, every built-in store can narrow a semantic search to records matching criteria on other fields, rather than comparing only the vector embeddings. The documentation sometimes calls this hybrid search, but the framework's own vocabulary reserves that term for combining vector and keyword ranking. This is filtered search.

The security framing is the one to lead with: **the permission filter must be applied at retrieval, not after.** Retrieving a document the user may not see and then filtering it out of the answer means it was in the model's context — and models paraphrase. The document leaked even though it was never shown.

Filter at the store. Every time.

### Reindexing

The documentation is candid that this is a hot topic in RAG design: chunking makes it hard to update individual pieces of information when the source changes.

NeuronAI's answer is metadata that identifies provenance. Every `Document` carries a `sourceType` and a `sourceName` — `FileDataLoader` sets them to `files` and the file's name — and:

```php
$documents = FileDataLoader::for("/path/to/directory")
    ->withSplitter(
        new SentenceTextSplitter(
            maxWords: 200,
            overlapWords: 0
        )
    )
    ->getDocuments();

MyRAG::make()->reindexBySource($documents);
```

`reindexBySource()` groups the new chunks by source and, for each `sourceType`/`sourceName` pair, **deletes that source's existing documents and adds the new version's chunks**. A source not yet in the store is simply added.

That is the operation that solves failure mode 6 from Section 11.5, and it is why `delete()` is in the store interface. Under the hood it is an ordinary filter:

```php
$store->delete(
    Filter::where('sourceType', 'files')
        ->where('sourceName', 'refund-policy.md'),
);
```

Plain `addDocuments()` has no such check: run an ingestion script twice with it and every chunk is in the store twice.

### The constraint that will catch someone

> The new version of the file **must have the same path and name** as the original, otherwise the documents are added as new ones.

Rename the file, re-index, and you now have both versions in the store — the old chunks orphaned under a source name nothing will ever reindex, the new ones alongside them. The agent will retrieve from both and answer from whichever matched better.

**In practice:** use a stable identifier, not a filename that reflects content. `policies/refund-policy.md` survives an edit. `policies/refund-policy-v3-final-2026.md` does not.

For `StringDataLoader` ingestion from a database, the same logic applies, with one extra step: the string loader files everything under source type and name `manual`, so you set both yourself — `sourceName` to the record's primary key, not to its title.

### An ingestion strategy worth adopting

```php
// Re-index a single article after it changes
$documents = StringDataLoader::for($article->body)->getDocuments();

foreach ($documents as $document) {
    $document
        ->setSourceType('articles')
        ->setSourceName((string) $article->id) // the ID, never the title
        ->addMetadata('tenant_id', $article->tenant_uuid);
}

$rag->reindexBySource($documents);
```

Hook this to your model's `saved` event and dispatch it to a queue. The index stays current with no cron job and no drift. Chapter 20 builds exactly this.

### Key takeaways

- `addMetadata()` before `addDocuments()`; the fields are your future filters.
- Declare the fields you filter on in the store's `DocumentSchema`; undeclared metadata is stored but not filterable.
- Attach tenant, visibility, language and freshness by default.
- Filter permissions **at retrieval** — post-filtering is a leak.
- `reindexBySource()` replaces a source's chunks; `sourceName` must be stable.
- Use record IDs, not titles, as source names.

## 12.7 The RAG Workflow: Pre- and Post-Processors

### The pipeline

When a `UserMessage` enters a RAG agent, six nodes run in order:

```
UserMessage
    │
    ├─ PreProcessNode        ← rewrite / expand the query
    ├─ RetrievalNode         ← execute the retrieval strategy
    ├─ PostProcessNode       ← rerank / filter the results
    ├─ InstructionsNode      ← inject documents into the system prompt
    ├─ ChatNode              ← run inference
    └─ ToolNode              ← execute tools, if any
    │
AssistantMessage
```

The first four replace the plain agent's start node; from `ChatNode` on, it is the same agent loop as everywhere else in the book.

**This is the payoff of Section 2.3.** A RAG agent is a workflow, its nodes are named, and knowing the names lets you hook the system with middleware. Everything in Part IV applies here.

It also maps precisely onto Section 11.5's failure modes:

| Failure | Node that fixes it |
|---|---|
| Question does not look like the answer | `PreProcessNode` |
| Similar but not relevant | `PostProcessNode` |
| Hallucination | `InstructionsNode` + instructions |
| Answer spans chunks | Retrieval strategy + reranking |

### Pre-processors: fixing the query

`PreProcessNode` runs the pre-processor pipeline. The built-in example is `QueryTransformationPreProcessor`, which asks a model to reshape the question before it is embedded:

```php
use NeuronAI\RAG\PreProcessor\QueryTransformationPreProcessor;
use NeuronAI\RAG\PreProcessor\QueryTransformationType;

protected function preProcessors(): array
{
    return [
        new QueryTransformationPreProcessor(
            provider: $this->getProvider(),
            transformation: QueryTransformationType::REWRITING,
        ),
    ];
}
```

Why this helps: users ask questions in the language of *problems*; documents are written in the language of *solutions*. "Why is my thing broken?" and "Error code 4021 indicates insufficient disk allocation" are semantically far apart. A transformation step rewrites the question into something closer to how the answer is phrased before the embedding happens. `REWRITING` is the default; `DECOMPOSITION` breaks a compound question into simpler ones, and `HYDE` has the model draft a hypothetical answer and embeds that instead — an answer-shaped query matches answer-shaped documents.

The cost is one extra model call per query, which is real. Measure whether it earns its place on your corpus; on technical documentation it usually does, on FAQ-style content it often does not. A cheaper, faster provider than your main chat model is usually enough for the rewrite.

### Post-processors: fixing the results

`PostProcessNode` runs the post-processor pipeline, and reranking is the reason it exists.

```php
use NeuronAI\RAG\PostProcessor\JinaRerankerPostProcessor;

protected function vectorStore(): VectorStoreInterface
{
    return new FileVectorStore(directory: storage_path('vectors'), topK: 50);
}

protected function postProcessors(): array
{
    return [
        new JinaRerankerPostProcessor(key: 'JINA_API_KEY', topN: 5),
    ];
}
```

Cohere (`CohereRerankerPostProcessor`) and a self-hosted LocalAI reranker (`LocalAIRerankerPostProcessor`) are the alternatives. Two cheaper post-processors need no model at all: `FixedThresholdPostProcessor` drops documents under a score threshold, and `AdaptiveThresholdPostProcessor` sets the cut-off from the score distribution of each result set.

**Why reranking works, and why it is the highest-return addition to a working RAG system:**

Vector search compares two embeddings that were computed *independently*. The query was compressed into a vector without knowing about the documents; each document was compressed without knowing about the query. Information is lost in both compressions.

A reranker reads the query and a document **together** and scores their relationship directly. It is far slower per pair, which is why you cannot use it to search millions of documents — but on 50 candidates it is fast, and it catches relevance signals the vector comparison could not represent.

The standard pipeline shape — and exactly what the listing above configures:

```
Vector search → top 50 candidates → rerank → top 5 → send to the model
```

You get the recall of a broad search and the precision of a careful one, and you send fewer, better chunks to the model — which also reduces tokens.

### Retrieval strategy

`RetrievalNode` executes the retrieval strategy, and NeuronAI allows that strategy to be customised — including retrieval from external data sources rather than only the vector store. The default, `SimilarityRetrieval`, embeds the query and runs one `search()`; your own strategy implements `RetrievalInterface` and hands it to `setRetrieval()` or returns it from a `retrieval()` override.

That is the extension point for anything unusual: a hybrid search combining BM25 and vectors, multi-query retrieval for cross-chunk questions, or pulling from a search API alongside your own index.

One obligation comes with it. `retrieve(Message $query, ?FilterExpression $filters = null)` receives the filters in force for this run — including your `retrievalScope()`. A custom strategy must apply them, combined with any of its own through `FilterScope::merge()`, and never drop them; otherwise the strategy is the hole in your tenant isolation.

Two strategies ship alongside the default. `CompositeRetrieval` runs several strategies in order and pools their results, which is how you search two stores at once. `SemanticMemoryRetrieval` searches past conversations that were stored as documents, restricted to the thread IDs you pass it — combine the two and the agent can recall "what we discussed last week" alongside the knowledge base. That is long-term memory, not knowledge retrieval, in the terms of Section 11.1; it is worth knowing the pieces exist, and the framework's conversation-memory guide covers wiring them.

### InstructionsNode: where hallucination is fought

This node adds the retrieved documents to the agent's system prompt, as a separate block wrapped in `<EXTRA-CONTEXT>` tags, each document labelled with its source type and source name. Your own instructions are left untouched ahead of it.

Which means the system prompt is where you constrain the model's use of them. Combine the node's mechanism with your `instructions()`:

```php
protected function instructions(): string
{
    return (string) new SystemPrompt(
        background: [
            'You answer questions using only the documents provided in your context.',
            'You are not a general-purpose assistant. Outside these documents you know nothing.',
        ],
        steps: [
            'Read the provided documents.',
            'If they contain the answer, give it and name the source document.',
            'If they do not, say clearly that the information is not in the knowledge base. '
            . 'Do not answer from general knowledge.',
        ],
        output: [
            'Cite the source of every factual claim.',
            'Never present an inference as something the documents state.',
        ],
    );
}
```

The source labels are what make "name the source document" possible — another reason the `sourceName` you set at ingestion should mean something to a reader.

Those instructions plus a `FaithfulnessJudge` in your eval suite are the two halves of the anti-hallucination story: one reduces it, the other tells you whether it worked.

### Middleware on RAG nodes

Because these are workflow nodes, middleware targets them by class — `$rag->addMiddleware(RetrievalNode::class, new MyMiddleware())`, or a `middleware()` override on the agent, the same mechanism Section 2.3 introduced for `ToolNode`.

Useful applications:

- Log every retrieval: query, documents returned, scores. This is your RAG debugging tool.
- Inject a per-run filter. A middleware's `before()` on `RetrievalNode` receives the `QueryPreProcessedEvent` and can call `addFilters()` on it; the filter is ANDed with the retrieval scope and dies with the run.
- Cache retrieval results for repeated queries.
- Redact sensitive content from documents before they enter the prompt.

Chapter 15 covers middleware properly.

### Key takeaways

- Six nodes: pre-process, retrieve, post-process, enrich instructions, chat, tools.
- Pre-processors fix query/answer mismatch at the cost of one model call.
- **Reranking is the highest-return improvement to a working RAG system**: retrieve 50, rerank, send 5.
- A custom retrieval strategy must honour the filters it is given.
- `InstructionsNode` plus strict instructions is the anti-hallucination mechanism.
- Nodes are named, so middleware can hook every stage.

## Lab 8 — Documentation RAG, Zero Cost

**Covers:** RAG class, file loader, custom splitter, local embeddings, file store.

### Goal

Ask questions of a folder of Markdown documentation, with no API keys and no infrastructure. Everything local, everything free.

### Prerequisites

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### The agent

**`src/Rag/DocsAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Rag;

use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Ollama\Ollama;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Embeddings\OllamaEmbeddingsProvider;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\FileVectorStore;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class DocsAgent extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return new Ollama(
            url: env('OLLAMA_URL', 'http://localhost:11434/api'),
            model: env('OLLAMA_MODEL', 'qwen2.5:7b'),
        );
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return new OllamaEmbeddingsProvider(
            model: env('OLLAMA_EMBEDDINGS_MODEL', 'nomic-embed-text'),
        );
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return new FileVectorStore(
            directory: \dirname(__DIR__, 2) . '/storage/vectors',
            topK: 5,
        );
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You answer questions about a software project using only its documentation.',
                'Outside the provided documents you know nothing about this project.',
            ],
            steps: [
                'Read the documents provided in your context.',
                'If they answer the question, answer and name the source.',
                'If they do not, say the documentation does not cover it.',
            ],
            output: [
                'Be concise. Include a short code example when the documents contain one.',
                'Always end with the source section heading you used.',
            ],
        );
    }
}
```

### The ingestion script

**`examples/08-index-docs.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Rag\DocsAgent;
use App\Rag\MarkdownSectionSplitter;
use NeuronAI\RAG\DataLoader\FileDataLoader;

$directory = $argv[1] ?? __DIR__ . '/fixtures/docs';

if (!\is_dir($directory)) {
    \fwrite(STDERR, "Not a directory: {$directory}\n");
    exit(1);
}

$start = \microtime(true);

$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();

\printf("Split into %d chunks.\n", \count($documents));

DocsAgent::make()->addDocuments($documents);

\printf("Indexed in %.1fs.\n", \microtime(true) - $start);
```

### The query script

**`examples/09-ask-docs.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Rag\DocsAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'How do I configure the vector store?';

echo DocsAgent::make()
    ->chat(new UserMessage($question))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

```bash
php examples/08-index-docs.php ./docs
php examples/09-ask-docs.php "How do I add a custom tool?"
php examples/09-ask-docs.php "What is the airspeed velocity of an unladen swallow?"
```

### The test that matters

That last question is the point of the lab. **The agent should say the documentation does not cover it.**

If it answers anyway, you have just reproduced failure mode 5 from Section 11.5 on your own machine — and you can fix it by strengthening the `steps` and `background` sections. That is a far more useful outcome than a successful query.

### Acceptance criteria

- Indexing reports a chunk count consistent with the number of `##` headings in your corpus, not a round number that suggests character-count splitting.
- A question phrased like a heading returns that section.
- An out-of-scope question is refused, explicitly, without a plausible invented answer.
- Deleting the vector store directory and re-running indexing produces the same answers.

### Extensions

1. Compare `MarkdownSectionSplitter` against the default `DelimiterTextSplitter` on the same questions.
2. Change `topK` from 5 to 2 and to 10. Observe answer quality and latency.
3. Edit a source file, re-run indexing with `reindexBySource()`, and confirm the old chunks are gone.

## Lab 9 — Production Store with Filtered Search

**Covers:** MariaDB, document schema, metadata, filters, evaluation.

### Goal

Move Lab 8 to a production database, add metadata filtering, and measure whether it actually improved anything.

### Install

MariaDB 11.7 or later, with its native vector type. If you do not already run one, a container is enough:

```bash
docker run -d --name rag-mariadb -p 3306:3306 \
    -e MARIADB_ROOT_PASSWORD=secret -e MARIADB_DATABASE=rag \
    mariadb:11.8
```

### Swap the store

```php
use NeuronAI\RAG\Schema\DocumentField;
use NeuronAI\RAG\Schema\DocumentSchema;
use NeuronAI\RAG\VectorStore\MariaDBVectorStore;

protected function vectorStore(): VectorStoreInterface
{
    return new MariaDBVectorStore(
        pdo: new \PDO(
            env('RAG_DSN', 'mysql:host=127.0.0.1;port=3306;dbname=rag'),
            env('RAG_DB_USER', 'root'),
            env('RAG_DB_PASSWORD', 'secret'),
        ),
        topK: 5,
        schema: DocumentSchema::of(
            DocumentField::string('section')->filterable(),
            DocumentField::string('language')->filterable(),
        ),
    );
}
```

Create the table once, sized for `nomic-embed-text`'s 768 dimensions, with the same connection details:

```php
$pdo = new \PDO(
    env('RAG_DSN', 'mysql:host=127.0.0.1;port=3306;dbname=rag'),
    env('RAG_DB_USER', 'root'),
    env('RAG_DB_PASSWORD', 'secret'),
);

(new MariaDBVectorStore(pdo: $pdo))->setupTable(dimensions: 768);
```

One method changed. Everything else — the agent, the loader, the splitter, the scripts — is untouched. That is the interface-driven architecture from Section 2.2 paying off on the data layer, and it is more convincing when you watch it happen than when you read about it.

The schema fields are optional (no `required()`), so Lab 8's documents, which carry no metadata, still index cleanly; they simply will not match a filter on those fields.

### Add metadata during ingestion

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();

foreach ($documents as $document) {
    // The first line of each chunk is its heading
    $document->addMetadata('section',  \strtok($document->getContent(), "\n") ?: 'untitled');
    $document->addMetadata('language', 'en');
}

DocsAgent::make()->reindexBySource($documents);
```

`reindexBySource()` rather than `addDocuments()`, so running the script again replaces each file's chunks instead of duplicating them — which works only because `MarkdownSectionSplitter` passes each file's source name down to its chunks.

### Measure it

Build an evaluator (Chapter 10) with fifteen real questions about your documentation:

```php
namespace App\Neuron\Evaluators;

use App\Rag\DocsAgent;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\AgentInterface;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Evaluation\Assertions\Judges\FaithfulnessJudge;
use NeuronAI\Evaluation\Assertions\StringContainsAny;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;
use NeuronAI\Providers\Anthropic\Anthropic;

class DocsRagEvaluator extends BaseEvaluator
{
    protected AgentInterface $judge;

    public function setUp(): void
    {
        // Any cheap agent with structured output will do (Section 10.5).
        $this->judge = Agent::make()
            ->setAiProvider(new Anthropic(/* ... */))
            ->setInstructions('You check whether an answer is supported by its sources.');
    }

    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(__DIR__ . '/datasets/docs-questions.json');
    }

    public function run(array $item): mixed
    {
        return DocsAgent::make()
            ->chat(new UserMessage($item['question']))
            ->getMessage()
            ?->getContent() ?? '';
    }

    public function evaluate(mixed $output, array $item): void
    {
        $this->assert(new StringContainsAny($item['expected_keywords']), $output);

        $this->assert(new FaithfulnessJudge(
            judge: $this->judge,
            context: $item['source_excerpt'],
            threshold: 0.7,
        ), $output, 'faithfulness');
    }
}
```

The third argument to `assert()` labels the score, so the report shows a `faithfulness` metric rather than the judge's class name — handy when you are about to compare four runs of it.

Run it against both stores and both splitters. Four configurations, one number each.

**That table is the deliverable of this lab.** Not the code — the measurement. It is the difference between "we improved the RAG" and "faithfulness went from 0.62 to 0.81 when we switched splitters, and switching stores changed nothing".

The second finding is as valuable as the first, and it is the kind of result you will never get by guessing. It is also the likely one here: the file store and MariaDB rank by the same cosine similarity, so moving between them buys you durability, concurrency and filtering at scale — not better answers. Better answers come from the splitter, the reranker and the instructions.

### Acceptance criteria

- Only `vectorStore()` differs between the Lab 8 and Lab 9 agents.
- You have a four-row table of faithfulness scores.
- A query filtered by metadata provably cannot return documents outside that filter — test it with two tenants' documents in one index. The companion repository's `chapters/Ch12/run/isolation.php` is a starting point.
- A filter on an undeclared field, such as `Filter::eq('author', 'me')`, throws rather than returning an empty result.

## Chapter Exercises

1. **Compare splitters.** Index a real documentation corpus with the default splitter and a custom one. Compare on fifteen questions, using the evaluator rather than your impression.
2. **Prove isolation.** Add tenant metadata and verify a filtered query cannot return another tenant's documents. This is a security test; write it as one.
3. **Re-index.** Change one source file and re-index with `reindexBySource()`. Confirm the old chunks are gone — query for a phrase you deleted.
4. **Report.** Record the faithfulness score for each configuration and write the one-paragraph summary you would send to a client. If the honest summary is "the expensive change did nothing", that is the most valuable sentence in the report.
