# Appendix A — Where the Documentation Drifts from the Code {.unnumbered}

Forty-four places where the official NeuronAI documentation disagrees with itself, contains a typo, or shows an API from an earlier major version. Every one of them produces an error for someone who copies the page.

This is not a complaint about the project. Documentation drift is what happens when a library moves quickly and its docs carry examples written against three major versions. It is, however, a real cost to you — and an afternoon spent settling these against your installed version is the highest-value preparation you can do before writing production code.

## How to resolve them quickly

Rather than checking forty-four items one at a time, run one probe per area. Each settles a whole cluster.

### Setup

```bash
mkdir neuron-verify && cd neuron-verify
composer require neuron-core/neuron-ai
composer show neuron-core/neuron-ai
vendor/bin/neuron list
```

Record the exact version. Everything below is relative to it.

### Probe 1 — namespaces and class names

```bash
grep -rn "class Agent\b"        vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class SystemPrompt\b" vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class FileVectorStore" vendor/neuron-core/neuron-ai/src/
grep -rln "EmbeddingsProvider\|EmbeddingProvider" vendor/neuron-core/neuron-ai/src/RAG/ | head
grep -rn "class .*Observer\|class AgentMonitoring" vendor/ | head
```

Settles items **1–9, 16, 22–25, 39**.

### Probe 2 — method signatures

```bash
grep -rn "function instructions"     vendor/neuron-core/neuron-ai/src/
grep -rn "function setMaxRuns\|function setMaxTries" vendor/neuron-core/neuron-ai/src/
grep -rn "function withFilter"       vendor/neuron-core/neuron-ai/src/RAG/
grep -rn "function init\|function start\|function run\|function getResult" \
     vendor/neuron-core/neuron-ai/src/Workflow/Workflow.php
grep -rn "class ToolRunsExceeded\|class ToolMaxTries" vendor/neuron-core/neuron-ai/src/
```

Settles items **1, 2, 26, 30, 31, 37, 43**.

### Probe 3 — one minimal script per capability

Write and run five short scripts. Each takes minutes and settles a cluster definitively:

| Script | Settles |
|---|---|
| Agent + `chat()` + `getMessage()` | 8, 9 |
| Tool class + toolkit with `only()` | 1–3 |
| `structured()` with a validated DTO | 12–15 |
| `stream()` → `events()` → chunk objects | 38 |
| Minimal 3-node workflow | 30, 31, 32 |

**This is faster and more reliable than reading source**, because it also catches behaviour the signatures do not reveal.

## The items

### Tools — Chapter 5

| # | Issue |
|---|---|
| 1 | `ToolRunsExceededException` in prose vs `ToolMaxTriesException` in the catch example |
| 2 | `setMaxRuns()` vs `setMaxTries()` — different sections use different names |
| 3 | `ExponentiateTool` in the `provide()` source vs `ExponentialTool` in the tools table |
| 4 | `Toolkits\CalendarToolkit\CalendarToolkit` vs `Toolkits\Calendar\...` |
| 5 | `NeuronAI\Tools\Calculator\CalculatorToolkit` vs `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit` |
| 6 | `ProviderTool:make()` — single colon, a typo for `::` |
| 7 | `new SesCleint(...)` — misspelling of `SesClient` |
| 8 | `instructions()` shown as both `public` and `protected` |
| 9 | `use NeuronAI\Agent;` (v2) vs `use NeuronAI\Agent\Agent;` (v3) in toolkit examples |

### Messages and multimodality — Chapters 4 and 8

| # | Issue |
|---|---|
| 10 | `AudioContent` imported but `FileContent` instantiated |
| 11 | `TextBlock` / `FileBlock` vs `TextContent` / `FileContent` |

### Structured output — Chapter 6

| # | Issue |
|---|---|
| 12 | `NeuronAI\StructuredOutput\Property` should be `SchemaProperty` |
| 13 | Symfony validator imports instead of `NeuronAI\StructuredOutput\Validation\Rules\` |
| 14 | `#[OutOfRange]` example imports `InRange` |
| 15 | Custom rule: `respectFormat()` arity mismatch; `$this->pattern` vs `$this->format` |

### Observability and evals — Chapter 10

| # | Issue |
|---|---|
| 16 | Three observer names: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` |
| 17 | `make:evaluator` vs `make:evaluators` between the Unix and Windows tabs |
| 18 | `evaluations --path=X` vs `evaluation X --concurrency=N` — **run `vendor/bin/neuron list`** |
| 19 | `ConsoleDriver` vs `ConsoleOutputDriver` |
| 20 | `autoload-dev` maps `App\Evaluators\` but the generator uses `App\Neuron\Evaluators\` |
| 21 | `new Antrhopic(...)` typo; confirm `setAiProvider()` / `setInstructions()` exist |

### RAG — Chapters 11 and 12

| # | Issue |
|---|---|
| 22 | `FileVectorStore` shown three ways: `(directory, name)`, `(directory, topK)`, `(directory, key)` |
| 23 | `FileVectoreStore` — misspelled class name (extra `e`) |
| 24 | `OpenAIEmbeddingsProvider` vs `OpenAIEmbeddingProvider` |
| 25 | Namespace `RAG\Embeddings\` vs `RAG\EmbeddingProvider\` |
| 26 | `withFilters()` (Pinecone) vs `withFilter()` (Elasticsearch) |
| 27 | Recheck `CalculatorToolkit` naming alongside item 3 |
| 28 | Stray semicolon: `FileDataLoader::for(...);` followed by `->addReader(...)` |
| 29 | Confirm the `Document` constructor and content accessor before shipping a custom splitter |

### Workflows — Chapters 13 to 16

| # | Issue |
|---|---|
| 30 | **`init()`/`run()` vs `start()`/`getResult()`** — two execution APIs on adjacent doc pages |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')` — v2 constructor, still in blog posts |
| 32 | `Edge` class and `addEdges()` — removed in v2, still in v1 material |
| 33 | `BrancheA1Event` — misspelling in the branching example |
| 34 | Missing commas after `message:` in several `ApprovalRequest` examples |
| 35 | Missing semicolon after `parent::__construct($message)` in `ContentReviewInterrupt` |
| 36 | `ContentReviewInterrupt` called with a positional second argument after a named first |
| 37 | Confirm the `CustomState` injection signature on the workflow |
| 38 | Confirm the handler's streaming accessor method name |

### Laravel SDK — Chapters 17 to 23

| # | Issue |
|---|---|
| 39 | `use NeuronAI\Agent;` / `use NeuronAI\SystemPrompt;` — v2 namespaces in the README |
| 40 | `new SystemPrompt(...config('neuron.system_prompt');` — missing closing parenthesis |
| 41 | `$workflow = WorkflowAgent(persistence: ...)` — missing `new` |
| 42 | `ElquentChatHistory` misspelled in prose; doc anchor `#eloquentchathisotry` |
| 43 | Confirm `withFilters()` vs `withFilter()` on the store from `VectorStore::driver()` |
| 44 | Confirm which vector store drivers `config/neuron.php` exposes |

## Priority order

If you have limited time, these six matter most because they appear in the highest-traffic code:

1. **#30** — the workflow execution API. Affects all of Part IV.
2. **#22–25** — `FileVectorStore` and embeddings provider naming. Affects all of Part III.
3. **#18** — the eval command. Your first eval run fails if this is wrong.
4. **#1–2** — the run-limit exception and method names. A wrong `catch` class fails silently, which is the worst kind of wrong.
5. **#16** — the observer class name. Blocks Chapter 10 entirely.
6. **#8** — `instructions()` visibility. Appears in every agent class in this book.

## Three corrections already applied in this book

Beyond the forty-four, three defects in earlier material about this framework have been corrected in the text you have just read, rather than merely flagged:

**The v2 streaming API.** `foreach ($agent->stream($msg) as $chunk) { echo $chunk; }` does not work in v3. `stream()` returns a handler; `events()` yields chunk *objects*; the text is `$chunk->content`. Section 7.2 uses the correct form throughout, and shows the broken one so you recognise it in the wild.

**There is no pgvector store.** A great deal of third-party material assumes one exists, because pgvector is ubiquitous in the Python ecosystem. The complete first-party list is in Section 12.5: Memory, File, PHPVector, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch. Lab 9 is built on PHPVector, and Chapter 20 recommends MariaDB 11.7+.

**No verifiable v4.** Section 26.1 covers this in full. The short version: run `composer show neuron-core/neuron-ai --all` and believe that rather than any document, including this one.
