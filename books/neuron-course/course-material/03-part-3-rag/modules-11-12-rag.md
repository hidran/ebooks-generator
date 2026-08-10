# Agentic AI in PHP with Neuron
## PART III — RAG
### Full lesson scripts — Modules 11 and 12

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^3.0, PHP 8.3.

---

> ## ⚠ CORRECTION TO THE CURRICULUM
>
> The original curriculum listed **pgvector** as the production vector store for Lab 9 and Module 20.
> **Neuron does not ship a pgvector store.** The first-party list is: Memory, File, PHPVector,
> MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch.
>
> Replace pgvector with one of:
> - **MariaDB** (11.7+, native `VECTOR` column) — closest to "just use your existing database"
> - **PHPVector** (`neuron-core/php-vector`) — pure PHP, HNSW + BM25, no external service
> - **Qdrant** or **Chroma** — if you want to teach a dedicated vector database
>
> My recommendation for the course: **PHPVector for Lab 9**, because it needs no infrastructure and
> demonstrates hybrid search; **MariaDB for Module 20**, because "add a column to the database you
> already run" is the most realistic production story for a PHP audience.

---
═══════════════════════════════════════════════════════════════
# MODULE 11 — RETRIEVAL THEORY
═══════════════════════════════════════════════════════════════
---

## LESSON 11.1 — The Problem RAG Solves

**Duration:** 11 minutes
**Type:** Theory

### Learning objectives

Understand precisely which problem RAG addresses, and — equally important — which problems it does not.

### The gap

A language model knows what was in its training data. It does not know your company's return policy, your internal runbooks, last week's board minutes, or the specification of the product you shipped yesterday.

Ask it anyway and one of two things happens. It says it does not know, which is honest but useless. Or it produces something plausible and wrong, which is worse than useless.

### The definition

RAG is the process of providing references to a knowledge base outside the model's training data before generating a response.

The mechanism, at its simplest:

1. The user asks a question.
2. Your system searches a knowledge base for passages relevant to that question.
3. Those passages are added to the prompt.
4. The model answers using them.

The model has not learned anything. It has been handed the relevant page and asked to read it.

### Why this is cost-effective

The documentation makes the economic argument directly: RAG extends the capabilities of an LLM to a specific domain or an organisation's internal knowledge base **without retraining the model.**

That word — retraining — is the alternative, and it is worth quantifying so students feel the difference:

| | RAG | Fine-tuning |
|---|---|---|
| Cost to set up | Hours | Days to weeks, plus compute |
| Cost to update | Re-index the changed document | Retrain |
| Update latency | Minutes | Days |
| Can cite sources | Yes | No |
| Works with any model | Yes | No — tied to what you tuned |
| Handles frequently changing data | Yes | No |

For "the model should know our documentation", RAG wins on every row. The interesting cases where fine-tuning wins are about *style and format*, not knowledge — and Lesson 11.4 covers that properly.

### The other use, easy to miss

RAG is usually pitched as private-data access. But the same mechanism supplies **recent** information — current research, this quarter's statistics, today's news. The model's training cutoff is a knowledge boundary, and retrieval crosses it in the same way it crosses the boundary of your firewall.

### What RAG is not for

Worth stating now, because the confusion is expensive and Lesson 4.5 already set it up:

**Not for facts your database knows.** "How many orders did this customer place?" is SQL. A vector search over prose will give you an approximately right answer, which for a count is simply wrong.

**Not for user memory.** "Remember I'm vegetarian" is long-term memory, not knowledge retrieval.

**Not for reasoning.** RAG supplies facts. It does not make the model better at logic, arithmetic or planning.

**Not for small corpora.** If your entire knowledge base is 3,000 tokens, put it in the system prompt. No embeddings, no vector store, no pipeline. The infrastructure only earns its place when the corpus exceeds what you can afford to send every time.

That last one is the most commonly ignored, and it is the RAG equivalent of Lesson 1.1's "if you can draw the flowchart, build the flowchart".

### Key takeaways

- RAG hands the model the relevant page; it does not teach it anything.
- Cheaper than fine-tuning on every dimension that matters for knowledge.
- Also crosses the training-cutoff boundary, not just the firewall.
- Not for countable facts, user memory, reasoning, or corpora small enough to inline.

---
═══════════════════════════════════════════════════════════════

## LESSON 11.2 — Embeddings and Similarity Search

**Duration:** 14 minutes
**Type:** Theory

### Learning objectives

Understand what an embedding is well enough to make design decisions, without needing the linear algebra.

### The intuition

An embedding is a list of numbers that represents the *meaning* of a piece of text. A typical model produces 768, 1024 or 1536 numbers per text.

The useful property: **texts with similar meaning produce similar number lists.**

"The cat sat on the mat" and "A feline rested on the rug" share almost no words. Their embeddings are close together. "The cat sat on the mat" and "Quarterly revenue increased by 12%" share the word "the". Their embeddings are far apart.

Keyword search sees the words. Embeddings see the meaning.

### Similarity search

Store the embedding of every chunk of your knowledge base. When a question arrives, embed the question and find the stored vectors closest to it.

That operation is what a **vector store** exists to do. Neuron's interface is exactly this:

```php
public function similaritySearch(array $embedding, int $k = 4): iterable;
```

Give it a vector, get back the `k` nearest documents. `k` — how many chunks to retrieve — is often called top-K, and it is one of the two knobs that most affect quality. The other is chunk size (Lesson 11.3).

### Scores, not distances

A detail Neuron makes explicit and that is worth teaching, because it prevents a real bug:

> `similaritySearch` should return documents with a similarity **score**, not a similarity **distance**.

These run in opposite directions. A distance of 0 means identical; a score of 1 means identical. Mix them up and your "best match" logic silently returns the worst results.

When a database returns distance, convert it:

```php
use NeuronAI\RAG\VectorSimilarity;

$document->setScore(
    VectorSimilarity::similarityFromDistance($distance)
);
```

Anyone implementing a custom store needs this. It is also a nice example of a framework encoding a convention to prevent a category of error.

### Three things that surprise people

**Embeddings are model-specific.** Vectors from OpenAI's model cannot be compared with vectors from Voyage's model. They are different coordinate systems. Change your embeddings provider and **you must re-embed your entire corpus.** Treat the embeddings model as part of your data schema, not as a swappable setting.

This is worth stating firmly because it is one of the few places where the interface-swap freedom of Lesson 3.6 does not apply. The interface swaps; the data does not follow.

**Dimensions must match the store.** If your embeddings model produces 1536 numbers and your vector store column is declared as 1024, nothing works. The MariaDB schema in the docs hardcodes `VECTOR(1536)` for exactly this reason.

**Similarity is not relevance.** Two chunks can be semantically close and only one of them answer the question. This is the gap that reranking exists to close (Lesson 12.7).

### Cost

Embedding is far cheaper than generation — typically a small fraction of the per-token price of a chat model. But you embed the whole corpus once and every query forever, so at scale it is a real line item.

**Ollama runs embedding models locally, free.** For the labs in this course, and for a great many production systems, a local embedding model is entirely adequate. Given that Lesson 3.6 already established Ollama for the labs, RAG can be taught end to end at zero cost.

### Key takeaways

- An embedding is a numeric representation of meaning; similar meanings sit close together.
- `similaritySearch($embedding, $k)` — top-K is one of the two quality knobs.
- Return scores, not distances; convert with `VectorSimilarity`.
- Embeddings are model-specific: changing the model means re-embedding everything.
- Local embedding models make RAG free to learn.

---
═══════════════════════════════════════════════════════════════

## LESSON 11.3 — Chunking: The Decision That Determines Quality

**Duration:** 15 minutes
**Type:** Theory — the most consequential lesson in Module 11

### Learning objectives

Understand why documents must be split, what the trade-offs are, and how to choose parameters deliberately rather than by default.

### Why split at all

Two reasons, and both matter:

**Retrieval precision.** If you embed an entire 40-page manual as one vector, that vector represents the average meaning of the whole manual — which is to say, almost nothing. A question about one paragraph will not match it well.

**Context budget.** You retrieve chunks to put in the prompt. A whole manual will not fit, and even if it did, Lesson 1.4's arithmetic says you would not want to pay for it on every turn.

So: split the document into pieces, embed each piece, retrieve the pieces that match.

### The core trade-off

The framework's documentation states the principle plainly, and it is the sentence to put on a slide:

> The longer your units of text are, the less accurate the embeddings representation will be.

**Small chunks** — precise embeddings, accurate matching, but each retrieved piece may lack the context needed to be useful. You match the exact sentence and it turns out to be meaningless without the paragraph around it.

**Large chunks** — plenty of context, but blurry embeddings and wasted tokens. You retrieve 800 words to answer a question the model could have answered from 40.

There is no universally correct value. There is a correct value *for your content*, and finding it is empirical.

### The three parameters

**Max length.** How big a chunk can get. Neuron's default splitter uses 1,000 characters.

**Separator.** Where it is allowed to cut. The default is the period — sentence boundaries. But if your documents are Markdown with headed sections, cutting on `\n## ` produces chunks that align with the document's own semantic structure, which is almost always better than cutting on sentences.

That is the single most useful practical tip in this lesson: **match the separator to your content's structure**, do not accept the default because it is there.

**Overlap.** Words carried from the previous chunk into the next. The default is zero.

### Why overlap exists

The documentation describes it as increasing the semantic connection between adjacent sections. Concretely, it fixes this failure:

> Chunk 1: "...the refund window is 30 days from delivery."
> Chunk 2: "After this period, only store credit is available."

Chunk 2 alone is unanswerable — *after what period?* With overlap, chunk 2 begins with the tail of chunk 1 and carries its own context.

Cost: duplicated text means more chunks, more embedding calls, more storage. A reasonable starting point is 10–15% of chunk size. Zero is right only when your chunks are genuinely independent — a FAQ where each entry stands alone, a product catalogue.

### Structure-aware chunking

The best chunking respects what the document *is*:

| Content | Split on |
|---|---|
| Markdown documentation | Headings (`##`) |
| FAQ | One chunk per question |
| Code | Function or class boundaries |
| Transcript | Speaker turns or timestamps |
| Legal text | Clause or article |
| Prose | Paragraphs, then sentences |

A custom splitter (Lesson 12.3) is often twenty lines and produces a bigger quality improvement than any amount of prompt tuning. This is the highest-leverage custom code in a RAG system, and it is worth saying so explicitly — students expect the leverage to be in the prompt, and it usually is not.

### How to actually choose

Do not guess. Measure — and you already have the tool from Module 10.

1. Build a dataset of 20 real questions with known correct answers.
2. Index the corpus at three configurations (say 500/1000/2000 characters, 0/10/20% overlap).
3. Run the evaluator against each, using `FaithfulnessJudge` and `CorrectnessJudge`.
4. Compare the scores.

This is why evals came before RAG in the course. Chunking is an empirical parameter, and without a measurement harness you are tuning by vibes.

### Key takeaways

- Split for retrieval precision and for context budget.
- Longer chunks mean blurrier embeddings — that is the core trade-off.
- Match the separator to your content's structure; do not accept the default.
- Overlap fixes chunks that are meaningless alone; start at 10–15%.
- Choose parameters by evaluation, not by intuition.

---
═══════════════════════════════════════════════════════════════

## LESSON 11.4 — RAG, Fine-Tuning, Context Stuffing and Tools

**Duration:** 12 minutes
**Type:** Theory with a decision table

### Learning objectives

Choose the right mechanism for supplying knowledge, from four options that are routinely confused.

### The four options

**1. Context stuffing.** Put everything in the system prompt. Simple, exact, no infrastructure. Limited by the context window and paid for on every single request.

**2. RAG.** Retrieve relevant passages at query time. Scales to any corpus size, supports citation, updates by re-indexing.

**3. Tools.** Let the model query a live system. Exact, current, structured.

**4. Fine-tuning.** Train the model on your data. Expensive, slow to update, but changes the model's default behaviour.

### The decision table

| Situation | Mechanism |
|---|---|
| Under ~2,000 tokens of stable reference | Context stuffing |
| Large unstructured document corpus | RAG |
| Countable or queryable facts | Tools |
| Data that changes minute to minute | Tools |
| Needs to cite a source document | RAG |
| Consistent output style or format | Fine-tuning |
| Domain vocabulary the model misreads | Fine-tuning |
| "The model should know our policies" | RAG |
| "The model should sound like our brand" | Fine-tuning |

### The distinction people get wrong

**Fine-tuning teaches behaviour. RAG supplies facts.**

Fine-tuning a model on your documentation is a common and expensive mistake. The model learns the *shape* of your writing — the vocabulary, the register, the structure — but it does not reliably learn the facts, and when your documentation changes you have to do it all again. Meanwhile you cannot cite anything, because there is nothing to cite.

If someone says "we want the model to know our product", they want RAG. If they say "we want it to write like our support team", that is fine-tuning territory — and even then, a good system prompt with three examples gets most of the way there for a fraction of the cost.

### The other distinction people get wrong

**RAG for prose. Tools for records.**

This is Lesson 4.5's point, and it deserves repeating in a RAG module because this is where the mistake is made.

- *"What is our refund policy?"* → RAG. It is written in a document.
- *"Has order 4471 been refunded?"* → Tool. It is a row in a table.
- *"Which customers had a refund last month?"* → Tool. It is a query.

Indexing your orders table into a vector store to answer the second question is a design error that produces confidently approximate answers. Vector search retrieves things that *look similar*; it does not compute.

### They compose

The best systems use several. Lesson 12.1 shows the framework supports this directly: a `RAG` class **is** an `Agent`, so it can have tools.

The documented example is well chosen — a workout-tips agent with a knowledge base of exercise information (RAG) plus a tool that reads the user's current training status from the database (tool calling). Prose from retrieval, facts from the tool, one answer.

### Key takeaways

- Four mechanisms: stuffing, RAG, tools, fine-tuning.
- Fine-tuning changes behaviour; RAG supplies facts.
- RAG for prose, tools for records — the most common and most expensive confusion.
- Under ~2,000 stable tokens, skip the infrastructure entirely.
- Real systems combine them; Neuron's RAG-is-an-Agent design supports that directly.

---
═══════════════════════════════════════════════════════════════

## LESSON 11.5 — The Limits of Naive RAG

**Duration:** 12 minutes
**Type:** Theory

### Learning objectives

Know how a basic RAG pipeline fails, so you recognise the failures rather than concluding "AI does not work".

### Naive RAG

Embed the question, retrieve top-K, stuff into the prompt, generate. It works surprisingly well, and then it fails in specific, recognisable ways.

### Failure 1 — The question does not look like the answer

The user asks *"Why is my thing broken?"* The document says *"Error code 4021 indicates insufficient disk allocation on the primary volume."*

Semantically distant. The retrieval misses.

**Fix:** query transformation. Rewrite or expand the question before embedding it — Neuron ships `QueryTransformationPreProcessor` for exactly this, and it runs in `PreProcessQueryNode` (Lesson 12.7).

### Failure 2 — Similar is not relevant

You retrieve five chunks, all about refunds. Only one covers the 30-day window the user asked about. The other four are noise, and noise costs tokens and can distract the model into answering from the wrong passage.

**Fix:** reranking. Retrieve broadly, then re-score with a model that reads the query and each document together. Lesson 12.7.

### Failure 3 — The answer spans chunks

*"How do our refund and shipping policies interact for international orders?"* Refunds are in one document, shipping in another, the international exception in a third. Top-K retrieval on one query finds one of them.

**Fix:** multi-query retrieval, or a higher K plus reranking. Genuinely hard — this is where naive RAG shows its edges.

### Failure 4 — Aggregation questions

*"How many articles mention GDPR?"* Vector search retrieves the *most similar* documents, not *all matching* documents. There is no counting operation.

**Fix:** this is not a RAG question. Use a tool, or metadata filtering with a hybrid search. Recognising it is the fix.

### Failure 5 — Confident hallucination

The retrieval returns nothing useful, and the model answers anyway from its general knowledge — fluently, plausibly, wrongly.

**This is the most dangerous failure**, because it looks exactly like success.

**Fix, in three parts:**

1. **Instruct explicitly.** In the `background` section: *"Answer only from the provided documents. If they do not contain the answer, say so."*
2. **Measure it.** `FaithfulnessJudge` from Lesson 10.5 exists for precisely this. It is the reason evals came first.
3. **Cite.** Require the answer to reference the source document. A citation the user can check converts an invisible failure into a visible one.

### Failure 6 — Stale index

Someone updates the policy document. The vector store still holds last quarter's chunks. The agent answers confidently from outdated information.

**Fix:** reindexing, which Neuron addresses with `reindexBySource()` (Lesson 12.6). Also an operational question: what triggers a re-index, and how do you know it ran?

### The honest summary

Naive RAG gets you perhaps 70% of the way. The remaining 30% is query transformation, reranking, metadata filtering, hybrid search and evaluation — which is exactly why Neuron's pipeline has pre-processors and post-processors as first-class stages rather than as an afterthought.

Say this in the video. Students who believe RAG is "embed and retrieve" will ship something that demos beautifully and disappoints in week two. Students who know the six failure modes will recognise what they are looking at.

### Key takeaways

- Six failure modes: query mismatch, irrelevant-but-similar, cross-chunk answers, aggregation, hallucination, staleness.
- Confident hallucination is the most dangerous because it resembles success.
- Instruct, measure with `FaithfulnessJudge`, and cite.
- Naive RAG is ~70%; the pipeline stages are the rest.

---
═══════════════════════════════════════════════════════════════
# MODULE 12 — THE NEURON RAG PIPELINE
═══════════════════════════════════════════════════════════════
---

## LESSON 12.1 — The RAG Class

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Build a working RAG agent and understand what its three methods control.

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

This is Lesson 2.3 arriving for the third time, and it has practical consequences worth listing:

> The Neuron `RAG` class extends the basic `Agent` class. Your RAG is always an agent, so you can attach tools and define system instructions.

Which means a RAG agent inherits, for free:

- `instructions()` and `SystemPrompt`
- `tools()` and toolkits
- `chatHistory()`
- `structured()`
- `stream()`
- `observe()` for tracing
- Everything from Modules 3 through 10

### The combined pattern

The documentation's example is a good one — workout tips from a knowledge base, plus a tool for the user's current status:

```php
class WorkoutTipsAgent extends RAG
{
    protected function provider(): AIProviderInterface { /* ... */ }

    public function instructions(): string
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

Knowledge from retrieval, facts from tools, arithmetic from the toolkit. That is Lesson 11.4's "they compose", in one class.

> **Verification list — the vector store signature.** The documentation shows `FileVectorStore` three different ways across three pages:
> - `new FileVectorStore(directory: __DIR__, name: 'demo')`
> - `new FileVectorStore(directory: storage_path(), topK: 4)`
> - `new FileVectoreStore(directory: __DIR__, key: 'demo')` — note the misspelled class name
>
> Also `OpenAIEmbeddingsProvider` vs `OpenAIEmbeddingProvider` (with and without the `s`) and the namespace `RAG\Embeddings\` vs `RAG\EmbeddingProvider\`. Check your installed version and standardise before recording — this is the highest-traffic code in Part III.

### Key takeaways

- Three methods: `provider()`, `embeddings()`, `vectorStore()`.
- The chat model and the embeddings model are independent choices.
- `chat()` is unchanged; retrieval is internal.
- RAG inherits every Agent feature, including tools.

---
═══════════════════════════════════════════════════════════════

## LESSON 12.2 — Data Loaders and Readers

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Build an ingestion pipeline that turns files and strings into embeddable documents.

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

Requires the **poppler** utility (`pdftotext`) on the system. A system dependency, not a Composer one — say so, because "it works on my machine" here usually means "poppler is installed on my machine".

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

Note it converts HTML **to Markdown** rather than stripping tags. That matters: headings survive as `##`, which means a heading-aware splitter (Lesson 12.3) can use them. Stripping to plain text would throw that structure away.

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

**This is the loader you will use most in a real application.** Your knowledge base is probably rows in a table — articles, product descriptions, policy records — not files on disk. Point this out; the file loader gets the documentation space, but the string loader gets the production use.

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

**The store must be the same one your RAG agent uses.** Same directory, same index, same collection. This is stated in the documentation and it is the single most common ingestion bug: you index into one store and query another, and the agent reports it knows nothing.

**Why use standalone components?** Because ingestion and querying are different jobs with different lifecycles. Ingestion is a batch process, a cron job, a queue worker. It does not need a chat provider configured, an API key for the LLM, or the agent's instructions. Separating them keeps your ingestion script lean and makes it deployable independently.

This is also the pattern Module 20 uses in Laravel, where ingestion runs as a queued job.

### Key takeaways

- `FileDataLoader::for($path)->getDocuments()` for files and directories.
- Readers map to extensions; PDF needs poppler, HTML needs `mtibben/html2text`.
- HTML converts to Markdown, preserving structure for the splitter.
- `StringDataLoader` is what you will actually use — most knowledge bases are database rows.
- Ingest with standalone components; the store must be identical to the agent's.

---
═══════════════════════════════════════════════════════════════

## LESSON 12.3 — Splitters

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Control chunking, and write the custom splitter that will improve your RAG more than anything else.

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

The three parameters from Lesson 11.3, in code:

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

Two methods. Here is a Markdown heading splitter, which is perhaps forty lines and will outperform any generic splitter on documentation:

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

> **Verify the `Document` constructor and content accessor** in your installed version — the docs show `Document` in signatures but not its construction. Adjust `new Document($text)` and `getContent()` accordingly.

### Why this matters so much

Every chunk this produces is a complete, self-contained section with its own heading. A retrieval hit brings back a coherent unit rather than an arbitrary 1,000-character window that starts mid-sentence.

**The heading also becomes part of the embedded text**, which means a question phrased like the heading matches strongly. That is a free relevance boost, purely from respecting the document's own structure.

Say the general principle on camera: **the best chunking strategy is the one your document already has.** Markdown has headings. Code has functions. Transcripts have speakers. Use them.

### Key takeaways

- `withSplitter()` on any data loader.
- `DelimiterTextSplitter` for structural delimiters; `SentenceTextSplitter` for prose.
- `SplitterInterface` is two methods — a custom splitter is an afternoon's work.
- Respect the document's own structure; it is the biggest quality lever in RAG.

---
═══════════════════════════════════════════════════════════════

## LESSON 12.4 — Embeddings Providers

**Duration:** 10 minutes
**Type:** Hands-on

### Learning objectives

Choose an embeddings provider and understand the commitment you are making.

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

**Use this for every lab in Part III.** Combined with a local chat model from Lesson 3.6, the entire RAG module costs nothing to follow. That matters for course completion rates more than any feature.

It is also a legitimate production choice. Embedding models are small and fast; running one locally is very different from running a frontier chat model locally.

### Hosted options

`OpenAIEmbeddingsProvider`, `VoyageEmbeddingsProvider` and others. Voyage in particular is worth mentioning — it specialises in retrieval embeddings and often outperforms general-purpose models on RAG benchmarks.

### Custom providers

Extend `AbstractEmbeddingsProvider`. Same extension story as everywhere else in the framework.

### The caveat that is not like the others

Lesson 3.6 taught that swapping providers is a one-line change. **Embeddings are the exception.**

Change the embeddings model and every vector in your store becomes meaningless. They are coordinates in a different space. Retrieval will return results — it will not fail loudly — and they will be wrong.

**Changing the embeddings model means re-embedding the entire corpus.**

Practical consequences worth putting on a slide:

- Record which model produced your index. In the store's name, in a metadata field, in a deployment note — somewhere.
- Budget re-embedding time before you switch. Millions of chunks is hours and real money.
- Never make the embeddings model an environment variable that differs between environments. Development on `nomic-embed-text` and production on `text-embedding-3-large` means your dev index and prod index are incompatible, and the bug will be baffling.

That last one is a genuinely nasty trap, and it is the natural mistake for someone who has just learned the `ProviderFactory` pattern from Lesson 3.6.

### Dimensions

Different models produce different vector lengths — 768, 1024, 1536 and others. Your vector store must be configured to match. `TypesenseVectorStore` takes `vectorDimension: 1024`; the MariaDB schema declares `VECTOR(1536)`.

Mismatch means either a hard error or silent nonsense, depending on the store. Check it when you set up.

### Key takeaways

- `OllamaEmbeddingsProvider` runs locally, free — use it for all labs.
- Hosted options include OpenAI and Voyage; Voyage is retrieval-specialised.
- **Changing the embeddings model invalidates your entire index.**
- Never vary the embeddings model across environments.
- Vector dimensions must match your store's configuration.

---
═══════════════════════════════════════════════════════════════

## LESSON 12.5 — Vector Stores

**Duration:** 15 minutes
**Type:** Hands-on with a decision table

### Learning objectives

Choose a vector store for a given deployment, and know what the interface requires if you write your own.

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

Four methods. Note `deleteBySource` — it exists to support reindexing (Lesson 12.6), which tells you the framework treats staleness as a first-class problem rather than an afterthought.

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

Module 20 builds this properly in Laravel.

> **Verification item.** The Pinecone example calls `withFilters()` (plural) and the Elasticsearch example calls `withFilter()` (singular). Check both.

### Custom stores

Implement the interface. Two details the documentation calls out:

**Return scores, not distances.** Convert with `VectorSimilarity::similarityFromDistance()`.

**`addDocument()` can delegate to `addDocuments()`** if your database has no separate single-item API. The two methods exist because many databases do.

The maintainers explicitly invite pull requests for new stores. For a student wanting visible open-source contribution, this is a well-scoped, genuinely useful place to start — worth mentioning.

### Key takeaways

- Four-method interface; `deleteBySource` exists for reindexing.
- `FileVectorStore` uses generators and scales further than expected.
- **PHPVector** gives HNSW + BM25 hybrid search with zero infrastructure.
- **MariaDB 11.7+** is the lowest-friction production option for most PHP shops.
- Metadata filters are how you do multi-tenant RAG safely.
- Use what you already run.

---
═══════════════════════════════════════════════════════════════

## LESSON 12.6 — Metadata and Reindexing

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Attach metadata for filtering, and solve the staleness problem from Lesson 11.5.

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

Neuron's answer is metadata that identifies provenance. The `Document` class carries `sourceType` and `sourceName`, and:

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

That is the operation that solves failure mode 6 from Lesson 11.5, and it is why `deleteBySource()` is in the store interface.

### The constraint that will catch someone

> The new version of the file **must have the same path and name** as the original, otherwise the documents are added as new ones.

Rename the file, re-index, and you now have both versions in the store — the old chunks orphaned and un-deletable by source, the new ones alongside them. The agent will retrieve from both and answer from whichever matched better.

**In practice:** use a stable identifier, not a filename that reflects content. `policies/refund-policy.md` survives an edit. `policies/refund-policy-v3-final-2026.md` does not.

For `StringDataLoader` ingestion from a database, the same logic applies: set `sourceName` to the record's primary key, not to its title.

### An ingestion strategy worth teaching

```php
// Re-index a single article after it changes
$documents = StringDataLoader::for($article->body)->getDocuments();

foreach ($documents as $document) {
    $document->addMetadata('tenant_id', $article->tenant_id);
    // sourceName should identify the article stably — the ID, not the title
}

$rag->reindexBySource($documents);
```

Hook this to your model's `saved` event and dispatch it to a queue. The index stays current with no cron job and no drift. Module 20 builds exactly this.

### Key takeaways

- `addMetadata()` before `addDocuments()`; the fields are your future filters.
- Attach tenant, visibility, language and freshness by default.
- Filter permissions **at retrieval** — post-filtering is a leak.
- `reindexBySource()` replaces a source's chunks; `sourceName` must be stable.
- Use record IDs, not titles, as source names.

---
═══════════════════════════════════════════════════════════════

## LESSON 12.7 — The RAG Workflow: Pre- and Post-Processors

**Duration:** 15 minutes
**Type:** Theory with code — closes the loop on Lesson 11.5

### Learning objectives

See the RAG pipeline as the workflow it is, and use its stages to fix naive-RAG failures.

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

**This is the payoff of Lesson 2.3.** A RAG agent is a workflow, its nodes are named, and knowing the names lets you hook the system with middleware. Everything in Part IV applies here.

It also maps precisely onto Lesson 11.5's failure modes:

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

**Why reranking works, and why it is the highest-ROI addition to a working RAG system:**

Vector search compares two embeddings that were computed *independently*. The query was compressed into a vector without knowing about the documents; each document was compressed without knowing about the query. Information is lost in both compressions.

A reranker reads the query and a document **together** and scores their relationship directly. It is far slower per pair, which is why you cannot use it to search millions of documents — but on 50 candidates it is fast, and it catches relevance signals the vector comparison could not represent.

The standard pipeline shape:

```
Vector search → top 50 candidates → rerank → top 5 → send to the model
```

You get the recall of a broad search and the precision of a careful one, and you send fewer, better chunks to the model — which also reduces tokens.

### Retrieval strategy

`RetrieveDocumentsNode` executes the retrieval strategy, and Neuron allows that strategy to be customised — including retrieval from external data sources rather than only the vector store.

That is the extension point for anything unusual: a hybrid search combining BM25 and vectors, multi-query retrieval for cross-chunk questions, or pulling from a search API alongside your own index.

### EnrichInstructionsNode: where hallucination is fought

This node adds the retrieved documents to the agent's system prompt.

Which means the system prompt is where you constrain the model's use of them. Combine the node's mechanism with your `instructions()`:

```php
public function instructions(): string
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

Because these are workflow nodes, middleware targets them by name — the same API as `Neuron::middleware(ToolNode::class, ...)` from Lesson 2.3.

Useful applications:

- Log every retrieval: query, documents returned, scores. This is your RAG debugging tool.
- Enforce a minimum similarity score, dropping weak matches before they reach the model.
- Cache retrieval results for repeated queries.
- Redact sensitive content from documents before they enter the prompt.

Module 15 covers middleware properly. Mention it here so students know the hook exists.

### Key takeaways

- Six nodes: pre-process, retrieve, post-process, enrich, chat, tools.
- Pre-processors fix query/answer mismatch at the cost of one model call.
- **Reranking is the highest-ROI improvement to a working RAG system**: retrieve 50, rerank, send 5.
- `EnrichInstructionsNode` plus strict instructions is the anti-hallucination mechanism.
- Nodes are named, so middleware can hook every stage.

---
═══════════════════════════════════════════════════════════════
# MODULE 12 LABS
═══════════════════════════════════════════════════════════════
---

## LAB 8 — Documentation RAG, Zero Cost

**Duration:** 30 minutes
**Covers:** RAG class, file loader, custom splitter, local embeddings, file store

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

    public function instructions(): string
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

### The demonstration that matters

That last question is the point of the lab. **The agent should say the documentation does not cover it.**

If it answers anyway, you have just reproduced failure mode 5 from Lesson 11.5 live, and you can fix it on camera by strengthening the `steps` and `background` sections. That is a far better lesson than a successful query.

### Extensions

1. Compare `MarkdownSectionSplitter` against the default `DelimiterTextSplitter` on the same questions.
2. Change `topK` from 5 to 2 and to 10. Observe answer quality and latency.
3. Edit a source file, re-run indexing with `reindexBySource()`, and confirm the old chunks are gone.

---

## LAB 9 — Production Store with Hybrid Search

**Duration:** 25 minutes
**Covers:** PHPVector, metadata, filters, evaluation

### Goal

Move Lab 8 to a store with real retrieval capabilities, add metadata filtering, and measure whether it actually improved anything.

*(This replaces the pgvector lab from the original curriculum — see the correction at the top of this document.)*

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

One method changed. Everything else — the agent, the loader, the splitter, the scripts — is untouched. **Say this out loud on camera:** it is the interface-driven architecture from Lesson 2.2 paying off on the data layer, and it is more convincing when students watch it happen than when they read it on a slide.

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

Build an evaluator (Module 10) with fifteen real questions about your documentation:

```php
namespace App\Neuron\Evaluators;

use NeuronAI\Evaluation\Assertions\FaithfulnessJudge;
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

The second finding is as valuable as the first, and it is the kind of result students will never get by guessing.

### Module 12 assessment

1. Index a real documentation corpus with the default splitter and a custom one. Compare on fifteen questions.
2. Add tenant metadata and verify a filtered query cannot return another tenant's documents.
3. Change one source file and re-index with `reindexBySource()`. Confirm the old chunks are gone.
4. Record the faithfulness score for each configuration and present the comparison.

---

## PART III — VERIFICATION LIST (ADDITIONS)

| # | Issue | Where |
|---|---|---|
| 22 | `FileVectorStore` shown with three different signatures: `(directory, name)`, `(directory, topK)`, `(directory, key)` | RAG / vector store / data loader |
| 23 | `FileVectoreStore` — misspelled class name (extra `e`) | Data loader, standalone example |
| 24 | `OpenAIEmbeddingsProvider` vs `OpenAIEmbeddingProvider` | RAG vs data loader |
| 25 | Namespace `RAG\Embeddings\` vs `RAG\EmbeddingProvider\` | RAG vs data loader |
| 26 | `withFilters()` (Pinecone) vs `withFilter()` (Elasticsearch) | Vector store |
| 27 | `ExponentiateTool`-style drift also appears in `CalculatorToolkit` — recheck alongside item 3 | — |
| 28 | Stray semicolon in the standalone ingestion example: `FileDataLoader::for(...);` followed by `->addReader(...)` | Data loader |
| 29 | Confirm the `Document` constructor signature and content accessor before shipping the custom splitter | Splitter |

Running total: **29 items.** Resolve before recording.

---

**END OF PART III**

*Next: Part IV — Workflows and multi-agent systems. Module 13 (the event-driven model), Module 14 (loops, branches, state), Module 15 (human in the loop), Module 16 (multi-agent).*
