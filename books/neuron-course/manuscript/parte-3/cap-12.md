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

$message = MyChatBot::make()
    ->chat(new UserMessage('I want to know more about Inspector AI Bug Fix.'))
    ->getMessage();

echo $message->getContent();
```

`chat()` — the same method as an ordinary agent. Retrieval happens inside, automatically. From the calling side, a RAG agent and a plain agent are indistinguishable.

### RAG *is* an Agent

This is Section 2.3 arriving for the third time, and it has practical consequences:

> The NeuronAI `RAG` class extends the basic `Agent` class. Your RAG is always an agent, so you can attach tools and define system instructions.

Which means a RAG agent inherits, for free:

- `instructions()` and `SystemPrompt`
- `tools()` and toolkits
- `chatHistory()`
- `structured()`
- `stream()`
- `observe()` for tracing
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

The documentation shows `FileVectorStore` three different ways across three pages:

- `new FileVectorStore(directory: __DIR__, name: 'demo')`
- `new FileVectorStore(directory: storage_path(), topK: 4)`
- `new FileVectoreStore(directory: __DIR__, key: 'demo')` — note the misspelled class name

Also `OpenAIEmbeddingsProvider` vs `OpenAIEmbeddingProvider` (with and without the `s`) and the namespace `RAG\Embeddings\` vs `RAG\EmbeddingProvider\`. This is the highest-traffic code in Part III and four of Appendix A's items live in it — 22 to 25. Settle them against your installed version now rather than after you have written an ingestion script.
:::

### Key takeaways

- Three methods: `provider()`, `embeddings()`, `vectorStore()`.
- The chat model and the embeddings model are independent choices.
- `chat()` is unchanged; retrieval is internal.
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

```php
new DelimiterTextSplitter(
    maxLength: 1000,
    separator: '.',
    wordOverlap: 0
)
```

The three parameters from Section 11.3, in code:

- **`maxLength`** — chunks no longer than this
- **`separator`** — where cuts are allowed; the period by default
- **`wordOverlap`** — words carried between chunks; zero by default

The documentation is explicit that each of these affects performance and accuracy. They are not defaults to accept; they are decisions to make.

### SentenceTextSplitter

```php
new SentenceTextSplitter(
    maxWords: 200,
    overlapWords: 0
)
```

Splits into sentences, groups them into word-based chunks, optionally overlaps by words.

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

        return \array_map(
            fn (string $text): Document => new Document($text),
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
[Verify the Document API]{.callout-title}

Confirm the `Document` constructor signature and content accessor in your installed version — the docs show `Document` in interface signatures but never show it being constructed. Adjust `new Document($text)` and `getContent()` accordingly. Appendix A, item 29.
:::

### Why this matters so much

Every chunk this produces is a complete, self-contained section with its own heading. A retrieval hit brings back a coherent unit rather than an arbitrary 1,000-character window that starts mid-sentence.

**The heading also becomes part of the embedded text**, which means a question phrased like the heading matches strongly. That is a free relevance boost, purely from respecting the document's own structure.

The general principle: **the best chunking strategy is the one your document already has.** Markdown has headings. Code has functions. Transcripts have speakers. Use them.

### Key takeaways

- `withSplitter()` on any data loader.
- `DelimiterTextSplitter` for structural delimiters; `SentenceTextSplitter` for prose.
- `SplitterInterface` is two methods — a custom splitter is an afternoon's work.
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

Different models produce different vector lengths — 768, 1024, 1536 and others. Your vector store must be configured to match. `TypesenseVectorStore` takes `vectorDimension: 1024`; the MariaDB schema declares `VECTOR(1536)`.

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

interface VectorStoreInterface
{
    public function addDocument(Document $document): void;

    /**
     * @param  Document[]  $documents
     */
    public function addDocuments(array $documents): void;

    public function deleteBySource(string $sourceName, string $sourceType): void;

    /**
     * Return docs most similar to the embedding.
     *
     * @param  float[]  $embedding
     * @return Document[]
     */
    public function similaritySearch(array $embedding, int $k = 4): iterable;
}
```

Four methods. Note `deleteBySource` — it exists to support reindexing (Section 12.6), which tells you the framework treats staleness as a first-class problem rather than an afterthought.

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

The documentation makes a point worth repeating: it uses **PHP generators** to read documents, so it never holds more than `topK` items in memory while iterating quickly. You can store thousands of documents and the only constraint is how long a similarity search may take.

There is also a distribution use for it: ship an agent with knowledge already baked into a file. That is a genuinely nice pattern for a packaged tool or a demo.

**PHPVector** — pure PHP, no external service:

```bash
composer require neuron-core/php-vector
```

```php
use NeuronAI\PHPVector\PHPVector;

return new PHPVector(
    path: '/var/data/mydb',
    topK: 5,
);
```

Built on `ezimuel/phpvector`. It implements **HNSW** for approximate nearest-neighbour search and **BM25** for full-text retrieval, and the two can combine into a **hybrid search** pipeline.

**This is the most interesting entry in the list for a PHP audience.** It gives you production-grade retrieval — including hybrid search, which is a genuine quality improvement — with no service to deploy. For a self-hosted application, a small SaaS, or a client who cannot add infrastructure, it is a serious option rather than a toy.

**MariaDB** — native vectors from 11.7:

```sql
CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID NOT NULL PRIMARY KEY,
    content TEXT,
    sourceType VARCHAR(255),
    sourceName VARCHAR(255),
    metadata JSON,
    embedding VECTOR(1536) NOT NULL,
    VECTOR INDEX (embedding)
)
```

```php
return new MariaDBVectorStore(
    new \PDO(...), // Or get the PDO instance from the ORM
);
```

For a PHP shop already running MariaDB, this is the lowest-friction production answer: one table, no new service, backups and monitoring you already have. Note the schema — `sourceType` and `sourceName` are there for reindexing, and `metadata JSON` for filtering.

**Managed and dedicated:** Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch. Each takes its own connection configuration; several need their official client installed via Composer.

::: {.callout .callout-warning}
[There is no pgvector store]{.callout-title}

The list above is complete. A great deal of third-party material assumes NeuronAI ships a pgvector integration, because pgvector is ubiquitous in the Python ecosystem. It does not. If you are on Postgres and want first-party support, your options are PHPVector (which does not care what database you run) or one of the dedicated stores.
:::

### The decision table

| Situation | Store |
|---|---|
| Unit tests | Memory |
| Labs, prototypes, small corpora | File |
| Self-hosted, no new infrastructure, want hybrid search | **PHPVector** |
| Already running MariaDB 11.7+ | **MariaDB** |
| Already running Elasticsearch or OpenSearch | That one |
| Want managed, billions of vectors | Pinecone |
| Want open-source dedicated | Qdrant, Weaviate, Chroma |

**The general rule: use what you already run.** A new database is a new backup story, a new monitoring story and a new failure mode. PHPVector and MariaDB exist precisely so that most PHP teams do not need any of that.

### Hybrid search with filters

Several stores support filtering by metadata alongside vector similarity. The pattern the documentation gives:

```php
class MyChatBot extends RAG
{
    protected array $vectorStoreFilters = [];

    protected function vectorStore(): VectorStoreInterface
    {
        $store = new PineconeVectorStore(
            key: 'PINECONE_API_KEY',
            indexUrl: 'PINECONE_INDEX_URL'
        );

        return $store->withFilters($this->vectorStoreFilters);
    }

    public function addVectorStoreFilters(array $filters): self
    {
        $this->vectorStoreFilters = $filters;
        return $this;
    }
}
```

```php
$response = MyRAG::make()
    ->addVectorStoreFilters([
        // Add filters
    ])
    ->chat(new UserMessage(...))
    ->getMessage();
```

**This is the mechanism for multi-tenant RAG**, and it is important enough to flag loudly. Filtering by `tenant_id` at query time means user A's search cannot return user B's documents. Without it, a shared vector store leaks across tenants — which is a data breach, not a bug.

Chapter 20 builds this properly in Laravel.

::: {.callout .callout-warning}
[Singular or plural?]{.callout-title}

The Pinecone example calls `withFilters()` and the Elasticsearch example calls `withFilter()`. Check both against your store. Appendix A, item 26.
:::

### Custom stores

Implement the interface. Two details the documentation calls out:

**Return scores, not distances.** Convert with `VectorSimilarity::similarityFromDistance()`.

**`addDocument()` can delegate to `addDocuments()`** if your database has no separate single-item API. The two methods exist because many databases do.

The maintainers explicitly invite pull requests for new stores. If you want a well-scoped, genuinely useful piece of open-source contribution, this is one.

### Key takeaways

- Four-method interface; `deleteBySource` exists for reindexing.
- `FileVectorStore` uses generators and scales further than expected.
- **PHPVector** gives HNSW + BM25 hybrid search with zero infrastructure.
- **MariaDB 11.7+** is the lowest-friction production option for most PHP shops.
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

Custom fields saved alongside the document's default fields in the store.

### What to attach

Think of metadata as the columns you will want to filter on later. Once the index is built, adding a field means re-indexing — so decide now:

```php
foreach ($documents as $document) {
    $document->addMetadata('tenant_id',   $tenant->id);
    $document->addMetadata('visibility',  'internal');
    $document->addMetadata('language',    'en');
    $document->addMetadata('updated_at',  $article->updated_at->toDateString());
    $document->addMetadata('category',    $article->category);
}
```

Four things worth attaching almost always:

**Tenant or owner.** The security boundary for multi-tenant retrieval. Non-negotiable if you serve more than one customer from one index.

**Visibility or permission level.** So a public-facing agent cannot retrieve internal documents.

**Language.** Cross-language retrieval mostly works and occasionally produces confusing results.

**Freshness.** A date lets you prefer or filter recent content — useful when old and new versions of a policy both live in the index.

### Hybrid search

Once the fields are in the store, supported databases can narrow a semantic search to records matching criteria on other fields, rather than comparing only the vector embeddings.

The security framing is the one to lead with: **the permission filter must be applied at retrieval, not after.** Retrieving a document the user may not see and then filtering it out of the answer means it was in the model's context — and models paraphrase. The document leaked even though it was never shown.

Filter at the store. Every time.

### Reindexing

The documentation is candid that this is a hot topic in RAG design: chunking makes it hard to update individual pieces of information when the source changes.

NeuronAI's answer is metadata that identifies provenance. The `Document` class carries `sourceType` and `sourceName`, and:

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

If `sourceType` and `sourceName` already exist in the store, **those documents are deleted and replaced** with the new version's chunks. Anything else is stored normally.

That is the operation that solves failure mode 6 from Section 11.5, and it is why `deleteBySource()` is in the store interface.

### The constraint that will catch someone

> The new version of the file **must have the same path and name** as the original, otherwise the documents are added as new ones.

Rename the file, re-index, and you now have both versions in the store — the old chunks orphaned and un-deletable by source, the new ones alongside them. The agent will retrieve from both and answer from whichever matched better.

**In practice:** use a stable identifier, not a filename that reflects content. `policies/refund-policy.md` survives an edit. `policies/refund-policy-v3-final-2026.md` does not.

For `StringDataLoader` ingestion from a database, the same logic applies: set `sourceName` to the record's primary key, not to its title.

### An ingestion strategy worth adopting

```php
// Re-index a single article after it changes
$documents = StringDataLoader::for($article->body)->getDocuments();

foreach ($documents as $document) {
    $document->addMetadata('tenant_id', $article->tenant_id);
    // sourceName should identify the article stably — the ID, not the title
}

$rag->reindexBySource($documents);
```

Hook this to your model's `saved` event and dispatch it to a queue. The index stays current with no cron job and no drift. Chapter 20 builds exactly this.

### Key takeaways

- `addMetadata()` before `addDocuments()`; the fields are your future filters.
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
    ├─ PreProcessQueryNode        ← rewrite / expand the query
    ├─ RetrieveDocumentsNode      ← execute the retrieval strategy
    ├─ PostProcessDocumentsNode   ← rerank / filter the results
    ├─ EnrichInstructionsNode     ← inject documents into the system prompt
    ├─ ChatNode                   ← run inference
    └─ ToolNode                   ← execute tools, if any
    │
AssistantMessage
```

**This is the payoff of Section 2.3.** A RAG agent is a workflow, its nodes are named, and knowing the names lets you hook the system with middleware. Everything in Part IV applies here.

It also maps precisely onto Section 11.5's failure modes:

| Failure | Node that fixes it |
|---|---|
| Question does not look like the answer | `PreProcessQueryNode` |
| Similar but not relevant | `PostProcessDocumentsNode` |
| Hallucination | `EnrichInstructionsNode` + instructions |
| Answer spans chunks | Retrieval strategy + reranking |

### Pre-processors: fixing the query

`PreProcessQueryNode` runs the pre-processor pipeline. The built-in example is `QueryTransformationPreProcessor`, which reinforces the input prompt before it is embedded.

Why this helps: users ask questions in the language of *problems*; documents are written in the language of *solutions*. "Why is my thing broken?" and "Error code 4021 indicates insufficient disk allocation" are semantically far apart. A transformation step rewrites the question into something closer to how the answer is phrased — or expands it into several variants — before the embedding happens.

The cost is one extra model call per query, which is real. Measure whether it earns its place on your corpus; on technical documentation it usually does, on FAQ-style content it often does not.

### Post-processors: fixing the results

`PostProcessDocumentsNode` runs the post-processor pipeline, and reranking is the reason it exists.

```php
use NeuronAI\RAG\PostProcessor\JinaRerankerPostProcessor;
```

**Why reranking works, and why it is the highest-return addition to a working RAG system:**

Vector search compares two embeddings that were computed *independently*. The query was compressed into a vector without knowing about the documents; each document was compressed without knowing about the query. Information is lost in both compressions.

A reranker reads the query and a document **together** and scores their relationship directly. It is far slower per pair, which is why you cannot use it to search millions of documents — but on 50 candidates it is fast, and it catches relevance signals the vector comparison could not represent.

The standard pipeline shape:

```
Vector search → top 50 candidates → rerank → top 5 → send to the model
```

You get the recall of a broad search and the precision of a careful one, and you send fewer, better chunks to the model — which also reduces tokens.

### Retrieval strategy

`RetrieveDocumentsNode` executes the retrieval strategy, and NeuronAI allows that strategy to be customised — including retrieval from external data sources rather than only the vector store.

That is the extension point for anything unusual: a hybrid search combining BM25 and vectors, multi-query retrieval for cross-chunk questions, or pulling from a search API alongside your own index.

### EnrichInstructionsNode: where hallucination is fought

This node adds the retrieved documents to the agent's system prompt.

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

Those instructions plus a `FaithfulnessJudge` in your eval suite are the two halves of the anti-hallucination story: one reduces it, the other tells you whether it worked.

### Middleware on RAG nodes

Because these are workflow nodes, middleware targets them by name — the same API as `Neuron::middleware(ToolNode::class, ...)` from Section 2.3.

Useful applications:

- Log every retrieval: query, documents returned, scores. This is your RAG debugging tool.
- Enforce a minimum similarity score, dropping weak matches before they reach the model.
- Cache retrieval results for repeated queries.
- Redact sensitive content from documents before they enter the prompt.

Chapter 15 covers middleware properly.

### Key takeaways

- Six nodes: pre-process, retrieve, post-process, enrich, chat, tools.
- Pre-processors fix query/answer mismatch at the cost of one model call.
- **Reranking is the highest-return improvement to a working RAG system**: retrieve 50, rerank, send 5.
- `EnrichInstructionsNode` plus strict instructions is the anti-hallucination mechanism.
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
    ->getContent() . PHP_EOL;
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

## Lab 9 — Production Store with Hybrid Search

**Covers:** PHPVector, metadata, filters, evaluation.

### Goal

Move Lab 8 to a store with real retrieval capabilities, add metadata filtering, and measure whether it actually improved anything.

### Install

```bash
composer require neuron-core/php-vector
```

### Swap the store

```php
use NeuronAI\PHPVector\PHPVector;

protected function vectorStore(): VectorStoreInterface
{
    return new PHPVector(
        path: \dirname(__DIR__, 2) . '/storage/phpvector',
        topK: 5,
    );
}
```

One method changed. Everything else — the agent, the loader, the splitter, the scripts — is untouched. That is the interface-driven architecture from Section 2.2 paying off on the data layer, and it is more convincing when you watch it happen than when you read about it.

PHPVector implements HNSW for approximate nearest-neighbour search and BM25 for full-text retrieval, and can combine both into hybrid search.

### Add metadata during ingestion

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();

foreach ($documents as $document) {
    $document->addMetadata('section',  $this->detectSection($document));
    $document->addMetadata('language', 'en');
}

DocsAgent::make()->addDocuments($documents);
```

### Measure it

Build an evaluator (Chapter 10) with fifteen real questions about your documentation:

```php
namespace App\Neuron\Evaluators;

use NeuronAI\Evaluation\Assertions\Judges\FaithfulnessJudge;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;

class DocsRagEvaluator extends BaseEvaluator
{
    protected AgentInterface $judge;

    public function setUp(): void
    {
        $this->judge = /* a cheap judge agent */;
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
            ->getContent();
    }

    public function evaluate(mixed $output, array $item): void
    {
        $this->assert(new StringContainsAny($item['expected_keywords']), $output);

        $this->assert(new FaithfulnessJudge(
            judge: $this->judge,
            context: $item['source_excerpt'],
            threshold: 0.7,
        ), $output);
    }
}
```

Run it against both stores and both splitters. Four configurations, one number each.

**That table is the deliverable of this lab.** Not the code — the measurement. It is the difference between "we improved the RAG" and "faithfulness went from 0.62 to 0.81 when we switched splitters, and switching stores changed nothing".

The second finding is as valuable as the first, and it is the kind of result you will never get by guessing.

### Acceptance criteria

- Only `vectorStore()` differs between the Lab 8 and Lab 9 agents.
- You have a four-row table of faithfulness scores.
- A query filtered by metadata provably cannot return documents outside that filter — test it with two tenants' documents in one index.

## Chapter Exercises

1. **Compare splitters.** Index a real documentation corpus with the default splitter and a custom one. Compare on fifteen questions, using the evaluator rather than your impression.
2. **Prove isolation.** Add tenant metadata and verify a filtered query cannot return another tenant's documents. This is a security test; write it as one.
3. **Re-index.** Change one source file and re-index with `reindexBySource()`. Confirm the old chunks are gone — query for a phrase you deleted.
4. **Report.** Record the faithfulness score for each configuration and write the one-paragraph summary you would send to a client. If the honest summary is "the expensive change did nothing", that is the most valuable sentence in the report.
