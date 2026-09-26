# Appendix A — Where the Documentation Drifts from the Code {.unnumbered}

Seventy-six places where the official NeuronAI material — the documentation site, the READMEs, the upgrade guides and the agent skills — disagrees with the code, disagrees with itself, contains a typo, or shows an API from an earlier major version. Six of them — item 49 and items 72 to 76 — are not documentation problems at all but defects in the code, found while verifying this book. Every one of them produces an error, or a wrong result, for someone who copies the page.

This is not a complaint about the project. Documentation drift is what happens when a library moves quickly and the material around it carries examples written against four major versions. It is, however, a real cost to you — and an afternoon spent settling these against your installed version is the highest-value preparation you can do before writing production code.

## How to read the table

Items 1 to 44 concern material that predates v4 but is still online and still copied. Their numbers are fixed, because the chapters cite them, and each carries its status against the v4 code this book uses:

- **Open** — still wrong in the material you will find.
- **Settled** — the code answers the question; the entry says what the answer is.
- **Obsolete** — the thing it described does not exist in v4; you will meet it only in older material.

Items 45 onwards concern the v4 material itself, grouped by the chapters they affect.

## Some of these are already settled

The companion repository pins every API this book uses against a known version, and running its test suite tells you which of the items below are still open on *your* installation:

```bash
git clone https://github.com/hidran/neuronai-php-book.git
cd neuronai-php-book && composer install && composer check
```

This book was verified against the **neuron-ai 4.x** branch shortly before the 4.0.0 tag, and **neuron-laravel 2.x**; the colophon records the commits. Where a status below says *Settled*, that is what it was settled against.

## How to resolve them quickly

Rather than checking seventy-six items one at a time, run one probe per area. Each settles a whole cluster.

### Setup

```bash
mkdir neuron-verify && cd neuron-verify
composer require neuron-core/neuron-ai
composer show neuron-core/neuron-ai
vendor/bin/neuron --help
```

Record the exact version. Everything below is relative to it.

### Probe 1 — namespaces and class names

```bash
grep -rn "class Agent\b"        vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class SystemPrompt\b" vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class ApprovalRequest" vendor/neuron-core/neuron-ai/src/
grep -rln "EmbeddingsProvider\|EmbeddingProvider" vendor/neuron-core/neuron-ai/src/RAG/ | head
grep -rn "class .*Adapter\b" vendor/neuron-core/neuron-ai/src/Agent/Adapters/ | head
grep -rn "class ToolRunsExceeded\|class ToolMaxTries" vendor/neuron-core/neuron-ai/src/
```

Settles items **1, 4–5, 9, 22–25, 34, 39, 54**.

### Probe 2 — method signatures

```bash
grep -rn "function instructions"      vendor/neuron-core/neuron-ai/src/Agent/
grep -rn "function approvalPolicy"    vendor/neuron-core/neuron-ai/src/Tools/Tool.php
grep -rn "function toolErrorHandler"  vendor/neuron-core/neuron-ai/src/Agent/
grep -rn "function run\|function events\|function resume\|function __construct" \
     vendor/neuron-core/neuron-ai/src/Workflow/Workflow.php
grep -rn "function delete\|function search" \
     vendor/neuron-core/neuron-ai/src/RAG/VectorStore/VectorStoreInterface.php
```

Settles items **8, 30–31, 36–37, 45–46, 58, 63**.

### Probe 3 — read the in-package guides

```bash
ls vendor/neuron-core/neuron-ai/upgrade/
find vendor/neuron-core/neuron-ai/src -name AGENTS.md
```

The upgrade guides and the per-module `AGENTS.md` files ship with the code, so they describe the version you installed. They are the most reliable prose the project publishes — and even they are not perfect (items 64, 70, 71).

### Probe 4 — one minimal script per capability

Write and run six short scripts. Each takes minutes and settles a cluster definitively:

| Script | Settles |
|---|---|
| Agent + `chat()` + `getMessage()` | 8, 9 |
| Tool class + toolkit with `only()`, and one approval-gated tool | 1–3, 45–46 |
| `structured()` with a validated DTO, sent a bad value on purpose | 12–15, 49–50 |
| Iterate `stream()`, print `TextChunk`s, then `getReturn()` | 38, 53 |
| Minimal 3-node workflow, then an interrupt and a resume in a second process | 30–32, 34–37, 67 |
| RAG with a `DocumentSchema` and one filtered search | 26, 43, 58–60 |

**This is faster and more reliable than reading source**, because it also catches behaviour the signatures do not reveal.

## The items

### Tools — Chapter 5

| # | Issue | v4 status |
|---|---|---|
| 1 | `ToolRunsExceededException` in prose vs `ToolMaxTriesException` in the catch example | **Settled.** Only `NeuronAI\Exceptions\ToolRunsExceededException` exists |
| 2 | `setMaxRuns()` vs `setMaxTries()` — different sections use different names | **Open.** `setMaxRuns()` (tool) and `toolMaxRuns()` (agent) are right; the `with()` example still calls `setMaxTries(1)`, on a `MySQLToolkit` given no PDO |
| 3 | `ExponentiateTool` in the `provide()` source vs `ExponentialTool` in the tools table | **Obsolete.** The calculator was rewritten around `EvaluateTool`; neither class exists |
| 4 | `Toolkits\CalendarToolkit\CalendarToolkit` vs `Toolkits\Calendar\...` | **Settled.** `NeuronAI\Tools\Toolkits\Calendar\` |
| 5 | `NeuronAI\Tools\Calculator\CalculatorToolkit` vs `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit` | **Settled.** The second |
| 6 | `ProviderTool:make()` — single colon, a typo for `::` | **Settled.** Fixed in the v4 docs |
| 7 | `new SesCleint(...)` — misspelling of `SesClient` | Open |
| 8 | `instructions()` shown as both `public` and `protected` | **Settled.** `protected`, returning `SystemMessage\|string`; a plain `string` return is still legal |
| 9 | `use NeuronAI\Agent;` (v2) vs `use NeuronAI\Agent\Agent;` in toolkit examples | Open |

### Messages and multimodality — Chapters 4 and 8

| # | Issue | v4 status |
|---|---|---|
| 10 | `AudioContent` imported but `FileContent` instantiated | Open |
| 11 | `TextBlock` / `FileBlock` vs `TextContent` / `FileContent` | Open. The classes are `TextContent` / `FileContent` |

### Structured output — Chapter 6

| # | Issue | v4 status |
|---|---|---|
| 12 | `NeuronAI\StructuredOutput\Property` should be `SchemaProperty` | Open |
| 13 | Symfony validator imports instead of `NeuronAI\StructuredOutput\Validation\Rules\` | Open |
| 14 | `#[OutOfRange]` example imports `InRange` | Open |
| 15 | Custom rule: `respectFormat()` arity mismatch; `$this->pattern` vs `$this->format` | Open |

### Observability and evals — Chapter 10

| # | Issue | v4 status |
|---|---|---|
| 16 | Three observer names: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` | **Settled, with a fourth name.** v4 uses PSR-14 events; the listener is `Inspector\Neuron\V4\InspectorSubscriber`, in `inspector-apm/inspector-php` 3.18.1 or later, and it must be subscribed explicitly |
| 17 | `make:evaluator` vs `make:evaluators` between the Unix and Windows tabs | **Settled.** `make:evaluators`; the singular is "Unknown command" |
| 18 | `evaluations --path=X` vs `evaluation X --concurrency=N` | **Settled.** `neuron evaluation`, singular; both `--path=<dir>` and a positional `<dir>` work; `--concurrency=N` needs `pcntl` and `spatie/fork` |
| 19 | `ConsoleDriver` vs `ConsoleOutputDriver` | **Settled.** Neither: `ConsoleOutput` and `JsonOutput`, in `NeuronAI\Evaluation\Output` |
| 20 | `autoload-dev` maps `App\Evaluators\` but the generator uses `App\Neuron\Evaluators\` | **Open, and worse.** The generator reads only `autoload`, never `autoload-dev`, so generated evaluators always land in production paths |
| 21 | `new Antrhopic(...)` typo; confirm `setAiProvider()` / `setInstructions()` exist | **Settled.** Both methods exist on `AgentInterface`; the typo remains |

### RAG — Chapters 11 and 12

| # | Issue | v4 status |
|---|---|---|
| 22 | `FileVectorStore` shown three ways: `(directory, name)`, `(directory, topK)`, `(directory, key)` | **Settled.** `(directory, topK = 4, name = 'neuron', ext = '.store', schema = null)` |
| 23 | `FileVectoreStore` — misspelled class name (extra `e`) | Open |
| 24 | `OpenAIEmbeddingsProvider` vs `OpenAIEmbeddingProvider` | **Settled.** `OpenAIEmbeddingsProvider`, with the `s`; `model:` is required |
| 25 | Namespace `RAG\Embeddings\` vs `RAG\EmbeddingProvider\` | **Settled.** `NeuronAI\RAG\Embeddings\` |
| 26 | `withFilters()` (Pinecone) vs `withFilter()` (Elasticsearch) | **Obsolete.** Both are gone; filters are declared in a `DocumentSchema` and applied through `retrievalScope()` |
| 27 | Recheck `CalculatorToolkit` naming alongside item 3 | **Obsolete.** See item 3 |
| 28 | Stray semicolon: `FileDataLoader::for(...);` followed by `->addReader(...)` | Open |
| 29 | Confirm the `Document` constructor and content accessor before shipping a custom splitter | **Settled.** `Document` is `final`; a custom splitter must copy `sourceType`, `sourceName` and metadata onto each chunk, or reindexing cannot find it |

### Workflows — Chapters 13 to 16

| # | Issue | v4 status |
|---|---|---|
| 30 | **`init()`/`run()` vs `start()`/`getResult()`** — two execution APIs on adjacent doc pages | **Settled, with a third API.** v2 used `start()`/`getResult()`, v3 `init()`/`run()`; v4 has no handler at all: `$workflow->run()`, or `events()` to stream |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')` — v2 constructor, still in blog posts | **Settled.** v4 is `Workflow::make(workflowId: ..., state: ...)`; persistence goes through `setPersistence()` |
| 32 | `Edge` class and `addEdges()` — removed in v2, still in v1 material | Open (in old material) |
| 33 | `BrancheA1Event` — misspelling in the branching example | Open |
| 34 | `ApprovalRequest` imported from `NeuronAI\Workflow\Interrupt` | **Open.** The class is `NeuronAI\Agent\Interrupt\ApprovalRequest` |
| 35 | The custom-request example overrides `jsonSerialize()`, uses an undefined `$this->note` and omits `use DateTimeImmutable` | **Open.** `jsonSerialize()` is `final` on `InterruptRequest`; override `metadata()` instead |
| 36 | `Workflow::make(runId: ...)` and `getRunId()` used as the resume handle | **Open.** There is no `runId` constructor argument; the handle is the workflow ID, and the run ID is a per-attempt fence (see item 64) |
| 37 | Confirm the `CustomState` injection signature on the workflow | **Settled.** `Workflow::make(state: new CustomState())`, or a `state()` hook plus `@extends Workflow<CustomState>` |
| 38 | Confirm the handler's streaming accessor method name | **Settled.** There is no handler: `events()` returns a generator, and `getReturn()` on it gives the final state |

### Laravel SDK — Chapters 17 to 23

| # | Issue | v4 status |
|---|---|---|
| 39 | `use NeuronAI\Agent;` / `use NeuronAI\SystemPrompt;` — v2 namespaces in the README | Open |
| 40 | `new SystemPrompt(...config('neuron.system_prompt');` — missing closing parenthesis | Open |
| 41 | `$workflow = WorkflowAgent(persistence: ...)` — missing `new` | **Obsolete.** The example is gone from the 2.x README |
| 42 | `ElquentChatHistory` misspelled in prose; doc anchor `#eloquentchathisotry` | Open |
| 43 | Confirm `withFilters()` vs `withFilter()` on the store from `VectorStore::driver()` | **Obsolete.** See item 26 |
| 44 | Confirm which vector store drivers `config/neuron.php` exposes | **Settled.** `file`, `pinecone`, `qdrant`, `meilisearch`, `chroma` |

### v4 material — tools and messages (Chapters 5, 7, 8)

| # | Issue |
|---|---|
| 45 | `approvalPolicy(array $inputs)` in the docs and the Laravel Boost skills. The method takes no parameters — the inputs are already bound; read `$this->inputs`. Copying the documented signature is a fatal incompatible override |
| 46 | `toolErrorHandler()`'s callback typed `fn (Throwable $e, ToolInterface $tool)`. The second argument is a `ToolCall`; the documented type is a `TypeError` the first time a tool throws |
| 47 | The toolkit table lists `FileSystemToolkit` as read, search and parse. It also ships write, edit, delete and bash tools — which matters for what you pass to `only()` |
| 48 | The provider-tool list omits ZAI, and the parallel-tool-call fallback is described as Windows-only. It also falls back without `spatie/fork`, and for a single call |
| 51 | Multimodal examples pass the payload as `source:`. The parameter is `content:` on every content block |
| 52 | `NeuronAI\Chat\MediaType` imported; the enum is `NeuronAI\Chat\Enums\MediaType`. `SourceType` is never imported, and one example reads `UserMssage` |
| 53 | The streaming page still describes `StreamingNode`, `events()` on a handler, the old `Chat\Messages\Stream\Adapters\` namespace and the removed `SSEAdapter`, and echoes `$chunk->content` without filtering for `TextChunk`. It also names `NeuronAI\Agent\Adapter\AgentChunkAdapter` and `NeuronAI\Workflow\Channel\CallbackChannel`, neither of which exists at that path |
| 54 | The `neuron-streaming` skill lists a `NativeAdapter`. The class is `AgentChunkAdapter` |

### v4 material — structured output (Chapter 6)

| # | Issue |
|---|---|
| 49 | The comparison rules — `GreaterThan`, `GreaterThanEqual`, `LowerThan`, `LowerThanEqual`, `EqualTo`, `NotEqualTo`, and `OutOfRange` — build their violation message without the field name and with the reference's *type* instead of its value; `LowerThan` and `LowerThanEqual` also say "greater than". That message is what the retry sends the model: a €900 refund comes back as *"must be greater than int"*. A code defect; Section 6.5 shows the workaround |
| 50 | `#[IpAddress]` in the docs; the class is `IPAddress`. Works on a case-insensitive filesystem, fails in production on Linux |

### v4 material — observability and evals (Chapter 10)

| # | Issue |
|---|---|
| 55 | The `neuron-monitoring` skill says `neuron-core/cloud-sdk`, `neuron-cloud-laravel` and `neuron-cloud-symfony` are available on Packagist. At the time of writing, all three return 404 |
| 56 | The evaluator generator's stub still calls `->getMessage()->getContent()` without the null-safe operator, so generated evaluators fail PHPStan out of the box |
| 57 | Evaluator discovery matches `^class`, so a `final`, `readonly` or `abstract` evaluator is silently skipped — *"No evaluator classes found"* |

### v4 material — RAG (Chapters 12 and 20)

| # | Issue |
|---|---|
| 58 | The vector-store page shows `delete(FilterGroup $filters)`. The signature is `delete(FilterExpression $filters)` |
| 59 | The same page chains `Filter::gt(...)->lt(...)->eq(...)`. `Filter::gt()` returns a `Filter`, which has no `lt()`; chaining starts from `Filter::where()`, which returns `Criteria` |
| 60 | The docs list PHPVector among the v4 stores. `neuron-core/php-vector` had no v4-compatible release at the time of writing |
| 61 | The `neuron-rag` skill calls `$this->resolveProvider()`, which does not exist. The method is `getProvider()` |
| 62 | `setRetrievalScope()` *replaces* the `retrievalScope()` hook rather than adding to it. Documented nowhere, and it silently drops a tenant filter — Section 20.1 |

### v4 material — workflows (Chapters 13 to 16, 22)

| # | Issue |
|---|---|
| 63 | The "Loops & Branches" page gives every node a third `WorkflowResources $resources` parameter. The class does not exist, and a node's `__invoke()` must take exactly two |
| 64 | The upgrade guides disagree with each other: guide 9 makes the run ID the continuation handle; guide 14 makes it the workflow ID again and demotes the run ID to a per-attempt stamp. The code follows guide 14 |
| 65 | `AsyncExecutor` needs `amphp/amp`, which the package lists only as a development dependency and not under `suggest`. Without it the executor fails with *"Call to undefined function Amp\async()"* |
| 66 | The `neuron-workflow` skill calls `->setProvider()`. The method is `setAiProvider()` |
| 67 | The human-in-the-loop page calls `$workflow->resume([...])` and stops. `resume()` only stages the answer; nothing happens until `->run()` or `->events()` |

### v4 material — Laravel SDK and upgrade guides (Chapters 17 to 23)

| # | Issue |
|---|---|
| 68 | The 2.x README still shows v3 patterns: a `ToolApproval` middleware, `StreamingNode`, `->events()` on a stream, and Inspector enabled by the environment variable alone |
| 69 | The `Neuron` facade's docblock has no `middleware()` entry, so the call works but your IDE and PHPStan say it does not |
| 70 | Upgrade guide 7's `MonitoredAgent` overrides the constructor without calling `parent::__construct()`, dropping the thread ID |
| 71 | Upgrade guide 11's "resume endpoints are unchanged" example uses the old constructor order and a `chat(payload:)` argument that does not exist; guide 13 still lists an SSE adapter |

## Code defects found while verifying this book

These are not documentation problems. They are behaviour in the 4.x code this book was verified against, each reproduced by a script in the companion repository. Check them against your version; some may be fixed by the time you read this.

| # | Defect | Where it bites |
|---|---|---|
| 72 | `RAG::reindexBySource()` groups documents in an array keyed by source name, so PHP turns a purely numeric name such as `"42"` into an integer and the delete filter then fails schema validation. Use `article-42`, not `42` | Section 20.2 |
| 73 | `make:node` generates invalid PHP (a doubled backslash in `Workflow\\Events`), and `make:agent` imports `NeuronAI\Providers\Anthropic`, a namespace, as if it were the class | Section 3.3 |
| 74 | The stale-attempt check throws a plain `WorkflowException`, while the stale-run check throws `StaleWorkflowRunException` — so a job that catches only the latter misses half the redeliveries it was written for | Section 22.3 |
| 75 | `StdioTransport::connect()` escapes the arguments but not the command, so an interpreter path containing a space — the default with Laravel Herd on macOS — is split by the shell and the MCP server dies at once. Unchanged from 3.x | Section 9.2 |
| 76 | `InMemoryChatHistory` built with no thread ID binds itself to a random `mem_…` key — deliberately, says the source, but unlike every other history backend, which stays unbound. A `chatHistory()` hook that omits the thread therefore makes `make(threadId: ...)` throw *"Conflicting thread identity"*. Pass `threadId: $this->threadId` | Sections 4.3 and 7.5 |

Three typing gaps are worth knowing about too, because they make correct code fail static analysis rather than at runtime: `subscribe()` types its listener as `callable(object): void`, so no listener typed to a specific event class passes PHPStan level 8; `Agent::stream()` is typed `Generator|AgentState`, so a plain `foreach` over it needs an `assert`; and the streamed generator is typed `Generator<int, object>`, which does not satisfy `SSEEncoder::encode()`. The companion repository marks each workaround with a comment.

## Priority order

If you have limited time, these seven matter most because they appear in the highest-traffic code:

1. **#30 and #36** — the workflow execution API and the resume handle. Affects all of Part IV.
2. **#45** — the approval-policy signature. Copying it is a fatal error on the first approval-gated tool.
3. **#46** — the error-handler signature. It fails exactly when a tool throws, which is the only time it matters.
4. **#26 and #58–59** — filters. The old method is gone and the new examples do not compile.
5. **#16** — the observability listener. Nothing is traced until you subscribe it, and nothing warns you.
6. **#49** — the validation messages. A retry that tells the model nothing useful is a retry you pay for twice.
7. **#18** — the eval command. Your first eval run fails if this is wrong.

## Corrections already applied in this book

Beyond the items above, four things that earlier material about this framework gets wrong have been corrected in the text you have just read, rather than merely flagged:

**The streaming API, twice over.** `foreach ($agent->stream($msg) as $chunk) { echo $chunk; }` was the v2 form and printed objects; v3 returned a handler with `events()`. In v4, `stream()` *is* the generator again — but it yields chunk *objects*, only some of which are text. Section 7.2 filters for `TextChunk`, reads `getReturn()` for the final state, and shows both older forms so you recognise them in the wild.

**Pauses are results, not exceptions.** Tutorials on human-in-the-loop written before v4 catch `WorkflowInterrupt`. Nothing is thrown: `run()` returns, and `$state->isInterrupted()` says why. Chapter 15 is written around that from the first page.

**There is no pgvector store.** A great deal of third-party material assumes one exists, because pgvector is ubiquitous in the Python ecosystem. The complete first-party list is in Section 12.5: Memory, File, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch and MongoDB Atlas, with PHPVector as a separate package awaiting a v4 release. Lab 9 is built on MariaDB, and Chapter 20 recommends MariaDB 11.7+.

**`required: true` does not validate.** It shapes the schema sent to the model and is not checked on the way back. Section 6.4 pairs every required scalar with a rule, which is what makes an omitted key trigger a retry instead of a fatal error.
