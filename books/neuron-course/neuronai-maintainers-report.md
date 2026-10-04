# NeuronAI — documentation and code issues found while writing a course on v4

**For:** the NeuronAI maintainers · **From:** Hidran Arias, author of *Agentic AI in PHP with NeuronAI*

While writing a book and course on NeuronAI v4, every claim and code example was checked against the installed code. This file lists what was found: places where the official material (documentation site, READMEs, upgrade guides, in-package skills, Laravel Boost skills) disagrees with the code, with itself, or shows an API from an earlier version, plus defects in the code. It is meant to be actionable, so items are numbered and each carries its current status.

## Versions checked

| Package | Version | Notes |
|---|---|---|
| `neuron-core/neuron-ai` | **4.0.3** (released 2026-10-03) | Originally verified on 4.0.2; re-checked on 4.0.3 by diffing the two releases and re-running the checks below |
| `neuron-core/neuron-laravel` | **2.0.0** | Latest release; unchanged since the first pass |
| `inspector-apm/inspector-php` | 3.19.1 | |
| PHP | 8.3 for the re-check (8.5 for the original pass) | |

A status that describes a page of the documentation site is the one that page had when it was read; the site changes faster than this list.

## Summary

- 103 items in total, 66 open on the versions above, of which **ten are defects in the code** (four in the library: items 74, 83, 92 and 93; six in the Laravel SDK: items 94 to 99).
- **What 4.0.3 changed** (the complete `src/` diff against 4.0.2 is eight files): `spatie/fork`-based parallelism (`--concurrency`, `parallelToolCalls()`) now also requires `ext-posix`, with the docs updated to say so; `make:evaluators` now reads `autoload-dev` (item 20 fixed); the `make:agent` stub reads `$_ENV['ANTHROPIC_API_KEY']` and `$_ENV['ANTHROPIC_MODEL']` instead of placeholder strings; `bin/neuron` honours Composer's `_composer_autoload_path`; AG-UI input translation ignores an empty `resume` array; `ConsoleOutput` no longer calls `printHeader()`; and the workflow guides now state that a completed run is deleted unless `retainCompletionUntilAcknowledged()` is used (item 90 behaviour unchanged).
- **No other source file changed**, so every other status below holds for 4.0.3 as it did for 4.0.2.
- The Boost skills bundled in neuron-laravel 2.0.0 are still the largest single source of stale API (item 100): 27 matches for the removed spellings across the core and Boost skills, 25 of them in Boost.

## Status key

- **Open** — still wrong in the material, or still in the code.
- **Settled** — the code answers the question; the entry says what the answer is.
- **Fixed** — corrected by a release.
- **Obsolete** — the thing it described no longer exists.

Items 1 to 44 concern material that predates v4 but is still online and copied. Items 45 to 76 concern the v4 material itself and defects that surfaced with it. Items 77 onwards concern the stable release.

## Quick way to reproduce

```bash
mkdir neuron-verify && cd neuron-verify
composer require neuron-core/neuron-ai:4.0.3 neuron-core/neuron-laravel
vendor/bin/neuron --help
ls vendor/neuron-core/neuron-ai/upgrade/ vendor/neuron-core/neuron-ai/skills/
grep -rnE "make\(threadId:|setChatHistory\(|->resume\(|approvalPolicy\(array" \
     vendor/neuron-core/neuron-ai/skills vendor/neuron-core/neuron-laravel/resources/boost/skills
```

The last command finds four spellings of the API that v4 removed. Against 4.0.3 it matches two lines in the core skills (one of them a method an application defines) and twenty-five in the Boost copies.

## The items

### Tools

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 1 | `ToolRunsExceededException` in prose vs `ToolMaxTriesException` in the catch example | **Settled.** Only `NeuronAI\Exceptions\ToolRunsExceededException` exists |
| 2 | `setMaxRuns()` vs `setMaxTries()` — different sections use different names | **Open.** `setMaxRuns()` (tool) and `toolMaxRuns()` (agent) are right; the `with()` example still calls `setMaxTries(1)`, on a `MySQLToolkit` given no PDO |
| 3 | `ExponentiateTool` in the `provide()` source vs `ExponentialTool` in the tools table | **Obsolete.** The calculator was rewritten around `EvaluateTool`; neither class exists |
| 4 | `Toolkits\CalendarToolkit\CalendarToolkit` vs `Toolkits\Calendar\...` | **Settled.** `NeuronAI\Tools\Toolkits\Calendar\` |
| 5 | `NeuronAI\Tools\Calculator\CalculatorToolkit` vs `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit` | **Settled.** The second |
| 6 | `ProviderTool:make()` — single colon, a typo for `::` | **Settled.** Fixed in the v4 docs |
| 7 | `new SesCleint(...)` — misspelling of `SesClient` | **Open.** The tool that page documents, `SESTool`, is deprecated in 4.0.3 and goes in the next major |
| 8 | `instructions()` shown as both `public` and `protected` | **Settled.** `protected`, returning `SystemMessage\|string`; a plain `string` return is still legal |
| 9 | `use NeuronAI\Agent;` (v2) vs `use NeuronAI\Agent\Agent;` in toolkit examples | **Open.** Two of the skills that ship with 4.0.3 print the v2 form too (item 102) |

### Messages and multimodality

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 10 | `AudioContent` imported but `FileContent` instantiated | **Open.** |
| 11 | `TextBlock` / `FileBlock` vs `TextContent` / `FileContent` | **Open.** The classes are `TextContent` / `FileContent` |

### Structured output

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 12 | `NeuronAI\StructuredOutput\Property` should be `SchemaProperty` | **Open.** |
| 13 | Symfony validator imports instead of `NeuronAI\StructuredOutput\Validation\Rules\` | **Open.** |
| 14 | `#[OutOfRange]` example imports `InRange` | **Open.** There is no `InRange` rule |
| 15 | Custom rule: `respectFormat()` arity mismatch; `$this->pattern` vs `$this->format` | **Open.** |

### Observability and evals

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 16 | Three observer names: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` | **Settled, with a fourth name.** v4 dispatches PSR-14 events; the listener is `Inspector\Neuron\V4\InspectorSubscriber`, in `inspector-apm/inspector-php` `^3.19`, and it must be subscribed explicitly. Releases 3.18.1 to 3.18.3 carry a subscriber written for a pre-release namespace, which records nothing; upgrade guide 46 prints a one-line check for the installed file |
| 17 | `make:evaluator` vs `make:evaluators` between the Unix and Windows tabs | **Settled.** `make:evaluators`; the singular is "Unknown command" |
| 18 | `evaluations --path=X` vs `evaluation X --concurrency=N` | **Settled.** `neuron evaluation`, singular; both `--path=<dir>` and a positional `<dir>` work; `--concurrency=N` needs `pcntl`, `posix` and `spatie/fork` (4.0.3 added `posix`; without it the runner prints a notice and runs sequentially) |
| 19 | `ConsoleDriver` vs `ConsoleOutputDriver` | **Settled.** Neither: `ConsoleOutput` and `JsonOutput`, in `NeuronAI\Evaluation\Output` |
| 20 | `autoload-dev` maps `App\Evaluators\` but the generator uses `App\Neuron\Evaluators\` | **Fixed in 4.0.3.** `make:evaluators` now merges `autoload-dev` into the prefixes it considers, production prefixes first. On 4.0.2 the generator read only `autoload`, so generated evaluators always landed in production paths. Checked: with `App\` in `autoload` and `App\Evaluators\` in `autoload-dev`, `make:evaluators 'App\Evaluators\AgentEvaluator'` writes to `evaluators/`, the most specific prefix|
| 21 | `new Antrhopic(...)` typo; confirm `setAiProvider()` / `setInstructions()` exist | **Settled.** Both methods exist on `AgentInterface`; the typo remains |

### RAG

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 22 | `FileVectorStore` shown three ways: `(directory, name)`, `(directory, topK)`, `(directory, key)` | **Settled.** `(directory, topK = 4, name = 'neuron', ext = '.store', schema = null)` |
| 23 | `FileVectoreStore` — misspelled class name (extra `e`) | **Open.** |
| 24 | `OpenAIEmbeddingsProvider` vs `OpenAIEmbeddingProvider` | **Settled.** `OpenAIEmbeddingsProvider`, with the `s`; `model:` is required |
| 25 | Namespace `RAG\Embeddings\` vs `RAG\EmbeddingProvider\` | **Settled.** `NeuronAI\RAG\Embeddings\` |
| 26 | `withFilters()` (Pinecone) vs `withFilter()` (Elasticsearch) | **Obsolete.** Both are gone; filters are declared in a `DocumentSchema` and applied through `retrievalScope()` |
| 27 | Recheck `CalculatorToolkit` naming alongside item 3 | **Obsolete.** See item 3 |
| 28 | Stray semicolon: `FileDataLoader::for(...);` followed by `->addReader(...)` | **Open.** |
| 29 | Confirm the `Document` constructor and content accessor before shipping a custom splitter | **Settled.** `Document` is `final`; a custom splitter must copy `sourceType`, `sourceName` and metadata onto each chunk, or reindexing cannot find it |

### Workflows

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 30 | **`init()`/`run()` vs `start()`/`getResult()`** — two execution APIs on adjacent doc pages | **Settled, with a third API.** v2 used `start()`/`getResult()`, v3 `init()`/`run()`; v4 has no handler at all: `$workflow->run()`, or `events()` to stream, each taking an optional `ExecutionRequest` |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')` — v2 constructor, still in blog posts | **Settled.** v4 is `Workflow::make(workflowId: ..., state: ...)`; persistence goes through `setPersistence()` |
| 32 | `Edge` class and `addEdges()` — removed in v2, still in v1 material | **Open.** In old material only |
| 33 | `BrancheA1Event` — misspelling in the branching example | **Open.** |
| 34 | `ApprovalRequest` imported from `NeuronAI\Workflow\Interrupt` | **Open.** The class is `NeuronAI\Agent\Interrupt\ApprovalRequest` |
| 35 | The custom-request example overrides `jsonSerialize()`, uses an undefined `$this->note` and omits `use DateTimeImmutable` | **Open.** `jsonSerialize()` is `final` on `InterruptRequest`; override `metadata()` instead |
| 36 | `Workflow::make(runId: ...)` and `getRunId()` used as the resume handle | **Open.** The constructor has no `runId` argument and the workflow has no `getRunId()`. The handle is the workflow ID. The run ID is a fence: read it from the state or from `inspect()` and pass it back with the execution attempt. `ExecutionRequest::start(runId: ...)` reserves one |
| 37 | Confirm the `CustomState` injection signature on the workflow | **Settled.** `Workflow::make(state: new CustomState())`, or a `state()` hook plus `@extends Workflow<CustomState>` |
| 38 | Confirm the handler's streaming accessor method name | **Settled.** There is no handler: `events()` returns a generator, and `getReturn()` on it gives the final state |

### Laravel SDK

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 39 | `use NeuronAI\Agent;` / `use NeuronAI\SystemPrompt;` — v2 namespaces in the README | **Open.** |
| 40 | `new SystemPrompt(...config('neuron.system_prompt');` — missing closing parenthesis | **Open.** |
| 41 | `$workflow = WorkflowAgent(persistence: ...)` — missing `new` | **Obsolete.** The example is gone from the 2.0.0 README |
| 42 | `ElquentChatHistory` misspelled in prose; doc anchor `#eloquentchathisotry` | **Open.** Both are still in the 2.0.0 README, in a section about a class that 4.0.3 removed (items 68 and 79) |
| 43 | Confirm `withFilters()` vs `withFilter()` on the store from `VectorStore::driver()` | **Obsolete.** See item 26 |
| 44 | Confirm which vector store drivers `config/neuron.php` exposes | **Settled.** `file`, `pinecone`, `qdrant`, `meilisearch`, `chroma` |

### v4 material — tools

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 45 | `approvalPolicy(array $inputs)` in the docs and the Laravel Boost skills. The method takes no parameters — the inputs are already bound; read `$this->inputs` or `$this->getInput('amount')`. Copying the documented signature is a fatal incompatible override | **Open.** The skills that ship with neuron-ai 4.0.3 print the right signature; the three Boost copies in neuron-laravel 2.0.0 do not (item 100) |
| 46 | `toolErrorHandler()`'s callback typed `fn (Throwable $e, ToolInterface $tool)`. The second argument is a `ToolCall`; the documented type is a `TypeError` the first time a tool throws | **Open.** The in-package skills and `AGENTS.md` files print `ToolCall` |
| 47 | The toolkit table lists `FileSystemToolkit` as read, search and parse. It also ships write, edit, delete and bash tools — which matters for what you pass to `only()` | **Open.** Eight tools in 4.0.3. `FileSystemToolkit::make($scope)` confines the file tools to a directory, not the shell |
| 48 | The provider-tool list omits ZAI, and the parallel-tool-call fallback is described as Windows-only. It also falls back without `spatie/fork`, and since 4.0.3 without the `posix` extension (`posix_kill`), and for a single call | **Open.** |

### v4 material — structured output

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 49 | The comparison rules — `GreaterThan`, `GreaterThanEqual`, `LowerThan`, `LowerThanEqual`, `EqualTo`, `NotEqualTo`, and `OutOfRange` — built their violation message without the field name and with the reference's *type* instead of its value; `LowerThan` and `LowerThanEqual` also said "greater than". That message is what the retry sends the model: a €900 refund came back as *"must be greater than int"*. A code defect | **Fixed in 4.0.2.** names the field and the value: *"amount must be less than or equal to 500"* |
| 50 | `#[IpAddress]` in the docs; the class is `IPAddress`. Works on a case-insensitive filesystem, fails in production on Linux | **Open.** |

### v4 material — messages and streaming

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 51 | Multimodal examples pass the payload as `source:`. The parameter is `content:` on every content block | **Open.** |
| 52 | `NeuronAI\Chat\MediaType` imported; the enum is `NeuronAI\Chat\Enums\MediaType`. `SourceType` is never imported, and one example reads `UserMssage` | **Open.** |
| 53 | The streaming page still describes `StreamingNode`, `events()` on a handler, the old `Chat\Messages\Stream\Adapters\` namespace and the removed `SSEAdapter`, and echoes `$chunk->content` without filtering for `TextChunk`. It also names `NeuronAI\Agent\Adapter\AgentChunkAdapter` and `NeuronAI\Workflow\Channel\CallbackChannel`, neither of which exists at that path | **Open.** The classes are `NeuronAI\Agent\Adapters\AgentChunkAdapter` and `NeuronAI\Workflow\Streaming\Channel\CallbackChannel` |
| 54 | The `neuron-streaming` skill lists a `NativeAdapter`. The class is `AgentChunkAdapter` | **Open.** Still in the skill that ships with 4.0.3 |

### v4 material — observability and evals

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 55 | The `neuron-monitoring` skill says `neuron-core/cloud-sdk`, `neuron-cloud-laravel` and `neuron-cloud-symfony` are available on Packagist. Re-checked against Packagist on 2026-10-04: all three return 404 | **Open.** The skill (`neuron-monitoring`) and `neuron-evaluation` that ship with 4.0.3 still say so |
| 56 | The evaluator generator's stub called `->getMessage()->getContent()` without the null-safe operator, so generated evaluators failed PHPStan out of the box | **Open, in a new form.** The 4.0.3 stub comments its bodies out: `getDataset()` and `run()` return nothing, so the generated class still fails PHPStan, and `neuron evaluation` stops on a `TypeError` until you fill them in | Unchanged in 4.0.3
| 57 | Evaluator discovery matched `^class`, so a `final`, `readonly` or `abstract` evaluator was silently skipped — *"No evaluator classes found"* | **Fixed.** Discovery reads each file with PHP's tokenizer; a `final class` evaluator is found and run |

### v4 material — RAG

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 58 | The vector-store page shows `delete(FilterGroup $filters)`. The signature is `delete(FilterExpression $filters)` | **Open.** |
| 59 | The same page chains `Filter::gt(...)->lt(...)->eq(...)`. The chain runs, because `lt()` and `eq()` are static factories and PHP lets you call them on an instance, and it keeps only the last condition: the first two are dropped without a word. Chaining starts from `Filter::where()`, which returns `Criteria` | **Open.** |
| 60 | The docs list PHPVector among the v4 stores. `neuron-core/php-vector` still has no v4-compatible release: 1.1.0 requires `neuron-ai ^3.0` | **Open.** |
| 61 | The `neuron-rag` skill calls `$this->resolveProvider()`, which does not exist. The method is `getProvider()` | **Fixed** in the skill that ships with neuron-ai 4.0.2 and later. The Boost copy in neuron-laravel 2.0.0 still has it (item 100) |
| 62 | `setRetrievalScope()` *replaces* the `retrievalScope()` hook rather than adding to it, and silently drops a tenant filter | **Settled.** It still replaces the hook, and the package now says so: "an explicit setter wins over its hook" (`src/RAG/AGENTS.md`, upgrade guide 19) |

### v4 material — workflows

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 63 | The "Loops & Branches" page gives every node a third `WorkflowResources $resources` parameter. Before the release the class did not exist, and a node's `__invoke()` had to take exactly two | **Fixed in 4.0.2.** ships `WorkflowResources`, and `__invoke()` takes two parameters or three |
| 64 | The upgrade guides disagreed with each other: guide 9 made the run ID the continuation handle; guide 14 made it the workflow ID again and demoted the run ID to a per-attempt stamp | **Obsolete.** The guides were rewritten and renumbered for the release, and they agree with the code: the workflow ID is the handle, the run ID and the execution attempt are fences |
| 65 | `AsyncBranchRunner`, called `AsyncExecutor` before the release, needs `amphp/amp`, which the package lists only as a development dependency and not under `suggest`. Without it a fork fails with *"Call to undefined function Amp\async()"* | **Open.** Unchanged in 4.0.3 |
| 66 | The `neuron-workflow` skill calls `->setProvider()`. The method is `setAiProvider()` | **Open.** Still in the skill that ships with 4.0.3 |
| 67 | The human-in-the-loop page calls `$workflow->resume([...])` and stops. Before the release `resume()` only staged the answer, and nothing happened until `->run()` or `->events()` | **Obsolete.** `Workflow::resume()` does not exist in 4.0.3. Continue with `submitInputs($answer)->run()` or `run(ExecutionRequest::resume($answer))` |

### v4 material — Laravel SDK and upgrade guides

| # | Issue | Status on 4.0.3 |
|---|---|---|
| 68 | The 2.x README still shows v3 patterns: a `ToolApproval` middleware, `StreamingNode`, `->events()` on a stream, and Inspector enabled by the environment variable alone | **Open, and wider.** The 2.0.0 README also documents `EloquentChatHistory` and a `chatHistory()` hook, both removed in 4.0.3 (item 79) |
| 69 | The `Neuron` facade's docblock has no `middleware()` entry, so your IDE and PHPStan reject a call the class accepts | **Open.** Moot while the facade throws (item 94) |
| 70 | Upgrade guide 7's `MonitoredAgent` overrode the constructor without calling `parent::__construct()`, dropping the thread ID | **Obsolete.** The example is not in the guides that ship with 4.0.3 |
| 71 | Upgrade guide 11's "resume endpoints are unchanged" example used the old constructor order and a `chat(payload:)` argument that does not exist; guide 13 still listed an SSE adapter | **Obsolete.** Neither is in the guides that ship with 4.0.3 |

## Code defects found earlier

These are not documentation problems. They are behaviour in the code, each reproduced by a script. Three of the five are fixed and one is obsolete; they stay here so the numbering is stable. The defects found on the stable release are in the next section.

| # | Defect | Status on 4.0.3 |
|---|---|---|
| 72 | `RAG::reindexBySource()` grouped documents in an array keyed by source name, so PHP turned a purely numeric name such as `"42"` into an integer and the delete filter then failed schema validation | **Fixed in 4.0.2.** reads the name back from the document; `"42"` works |
| 73 | `make:node` generated invalid PHP (a doubled backslash in `Workflow\\Events`), and `make:agent` imported `NeuronAI\Providers\Anthropic`, a namespace, as if it were the class | **Fixed** in the core CLI. The SDK's `neuron:node` has a fault of its own (item 95) |
| 74 | The stale-attempt check throws a plain `WorkflowException` (*"Stale continuation…"*), while the stale-run check throws `StaleWorkflowRunException` — so a `catch` written for the second never sees the first | **Open.** `abandon()` has the same split (item 92) |
| 75 | `StdioTransport::connect()` escaped the arguments but not the command, so an interpreter path containing a space — the default with Laravel Herd on macOS — was split by the shell and the MCP server died at once | **Fixed in 4.0.2.** starts the server without a shell, so the path is passed as it is; the old `escapeshellarg()` workaround now fails with *"Failed to start the MCP server"* |
| 76 | `InMemoryChatHistory` built with no thread ID bound itself to a random `mem_…` key, so a `chatHistory()` hook that omitted the thread made `make(threadId: ...)` throw *"Conflicting thread identity"* | **Obsolete.** The history classes, the hook and the `threadId:` argument are all gone (items 77 and 79) |

Two typing gaps are worth knowing about too, because they make correct code fail static analysis rather than at runtime: `subscribe()` types its listener as `callable(object): void`, so no listener typed to a specific event class passes PHPStan level 8; and the streamed generator is typed `Generator<int, object>`, which does not satisfy `SSEEncoder::encode()`. The companion repository marks each workaround with a comment. A third gap is closed: `Agent::stream()` is declared `Generator`, so a plain `foreach` over it needs no `assert`.

## Found on 4.0.3 and the SDK 2.0.0

Every item below is open on neuron-ai 4.0.3 and neuron-laravel 2.0.0. Where one is a defect in the code and not drift in the material, the entry says so. The items that involve a database were run on SQLite.

### Identity and memory

| # | Issue |
|---|---|
| 77 | Older listings, pre-release material and the SDK's Boost skills pass the conversation as `make(threadId: ...)`. The constructor is `(?string $workflowId, ?WorkflowState $state)`, so the call fails with *"Unknown named parameter $threadId"*. Use `make(workflowId: ...)`, `setThreadId()` or `for()` |
| 78 | An agent, a RAG or a workflow with no ID bound refuses to run: *"This agent has no thread ID: bind one with setThreadId() first."*, or *"This workflow has no workflow ID: bind one with setWorkflowId() first."* The framework never invents one, so every one-line `Agent::make()->chat(...)` in older material fails. On an agent the exception is an `AgentException`, which a `catch` written for model failures swallows |
| 79 | A leftover `chatHistory()` hook is never called, and nothing says so: the removed classes it names are never loaded, the agent answers, and the conversation sits in the default in-memory store with its 50,000-token window. The hooks are `messageStore()` and `contextWindow()`. `setChatHistory()`, by contrast, fails loudly |
| 80 | A message store skips a message whose ID it already holds: `append()` is idempotent by contract. A test that queues the same `AssistantMessage` instance twice in `FakeAIProvider` therefore loses the second answer in silence, and the turn after it throws `ChatHistoryException: Invalid message sequence`. Build one message per scripted reply |
| 81 | The `neuron-agent` and `neuron-tool-approval` skills say the next `chat()` supersedes a failed turn. That holds only when the turn failed before its question was stored. After a tool step the next `chat()` throws `ChatHistoryException: Invalid message sequence`, until a plain `run()` finishes the failed turn. The `neuron-laravel-integration` skill has it right |

### Structured output

| # | Issue |
|---|---|
| 82 | When the retries run out on a missing required key, or on a value of the wrong type, `structured()` throws `DeserializerException`, which extends `NeuronException` and is not an `AgentException`. A `catch (AgentException)` sees only the rule violations. Catch both |
| 83 | `#[ArrayOf(X::class)]` validates each item with the item's own rules and then discards what it found: the violation reads *"lines must be an array of OrderLine"* whichever item broke whichever rule, and that sentence is all the retry tells the model. Without `#[ArrayOf]` the item rules do not run at all. A code defect. Put the constraint on the item class instead of relying on `#[ArrayOf]` |

### Streaming, MCP and observability

| # | Issue |
|---|---|
| 84 | Observability events live in `NeuronAI\Agent\Observability\`, `NeuronAI\Workflow\Observability\` and `NeuronAI\RAG\Observability\`. Pre-release material, the SDK's Boost `neuron-monitoring` skill included, uses `NeuronAI\Observability\Events\`. `subscribe()` takes any string, so a listener on the old name never fires and nothing errors |
| 85 | The plain endpoint in the `neuron-frontend-integration` skill sends its headers and then iterates inside `try { ... } catch (Throwable) {}`. The generator is lazy, so a turn the engine refuses with `RunInFlightException` is thrown inside that `try`: the browser gets a 200 and an empty stream. Prime the generator with `$events->valid()` before the first header, as the Laravel and Symfony skills do The same skill names two versions of the AG-UI client it was tested with, 1.0.x and 0.0.59 |
| 86 | `McpConnector::tools()` throws `ToolException` when a server tool's schema uses `anyOf`, `oneOf`, `$ref` or a list of types, and one such tool fails discovery for the whole server. It is the shape Python servers built on FastMCP and Pydantic give an optional parameter. 3.x simplified those properties silently, so older material connects without comment. `only()` filters before the conversion |

### RAG

| # | Issue |
|---|---|
| 87 | `PdfReader` runs `pdftotext` through `symfony/process`, and `HtmlReader` needs `html2text/html2text`. The package lists neither under `require` or `suggest`, so Composer installs neither with it. `HtmlReader`'s docblock also promises Markdown; it returns plain text |
| 88 | `OpenAIEmbeddingsProvider` asks for 1024 dimensions unless told otherwise, and the SDK's `config/neuron.php` sets the same number; `MariaDBVectorStore::setupTable()` creates `VECTOR(1536)` unless told otherwise. The two defaults do not match: give both sides the number |

### Workflows

| # | Issue |
|---|---|
| 89 | `expiresAt` does not refuse a late answer. A payload delivered after the deadline reaches the node like any other; only an inputless `run(ExecutionRequest::resume())` turns an expired wait into `null`. A node that must refuse a late answer checks the clock itself, inside `memoize()` |
| 90 | A workflow ID whose run completed is free again: its records are swept, and the next `run()`, plain or with the same reserved run ID, executes the workflow from the top. A redelivered start job repeats the work. `retainCompletionUntilAcknowledged()` keeps the outcome and refuses the redelivery with `RunInFlightException`, until you `acknowledge()` it | **4.0.3 documents this behaviour** in `src/Workflow/AGENTS.md` and the `neuron-workflow` skill ("A clean completion deletes the run by default"); the behaviour itself is unchanged and a redelivered start job still re-executes
| 91 | With nothing waiting, the three ways to continue fail three different ways. `submitInputs()` throws `InputTranslationException`, which is not a `WorkflowException`. `run(ExecutionRequest::resume($payload))` throws a plain `WorkflowException`, *"No run in flight"*. The same call with `expectedRunId:` throws `StaleWorkflowRunException`. An exception handler has to map all three |
| 92 | `abandon()` repeats the split of item 74: a stale run ID throws `StaleWorkflowRunException`, a stale attempt a plain `WorkflowException`, *"Cannot abandon a different execution attempt."* A code defect. Called with a run ID when nothing holds the workflow ID, it also throws `StaleWorkflowRunException` where a clean-up loop expects `false` |
| 93 | The in-package guides say a node that reaches its waits in a different order "fails with `WorkflowException` instead of losing the answer". That is true of an `interruptIf()` whose condition changed. With a plain `if` around `interrupt()` nothing is thrown: a wait is identified by its position, so the answer goes to whichever wait now comes first, and the node pauses again on the question that was already answered. A code defect |

### Laravel SDK 2.0.0

| # | Issue |
|---|---|
| 94 | The `Neuron` facade throws on every call. It builds `Agent::make()` and never binds a thread, so `Neuron::chat()`, `Neuron::stream()` and `Neuron::structured()` all end in *"This agent has no thread ID"*. Generate an agent class and bind it with `->for($threadId)`. An SDK defect |
| 95 | `php artisan neuron:node` generates `use NeuronAI\Workflow\StartEvent;` and `use NeuronAI\Workflow\StopEvent;`. The classes live in `NeuronAI\Workflow\Events\`. The file passes `php -l`, and the workflow that contains the node fails validation on its first run. An SDK defect |
| 96 | The shipped `chat_messages` migration has no `message_id` column and the shipped `ChatMessage` model does not make it fillable, while `EloquentMessageStore` keys every row on it. The same message is stored twice and comes back with a different ID. Write the migration and the model yourself. An SDK defect |
| 97 | `EloquentPersistence` over the shipped `workflow_store` table fails. The table has a composite primary key and no `id`, so the model's updates and deletes go to `where "id" is null`: a workflow dies on its first step with *"Stale execution attempt 1 cannot write…"*, and an agent's finished turn is never cleared, so its next `chat()` throws `RunInFlightException`. Use `DatabasePersistence` on that table. An SDK defect |
| 98 | `AIProvider::driver()` and `EmbeddingProvider::driver()`, called with no argument, throw a `TypeError` when `NEURON_AI_PROVIDER` or `NEURON_EMBEDDING_PROVIDER` is unset: *"getDefaultDriver(): Return value must be of type string, null returned"*. The config has no fallback for either, and the README never mentions the second. An SDK defect |
| 99 | `VectorStoreManager` is not registered as a singleton, unlike the other two managers. A driver added with `VectorStore::extend()` lives on an instance that only the facade's cache holds: resolve the manager from the container, or clear the facade's resolved instances, and the driver is *"not supported"*. Register the singleton in your own provider. An SDK defect |
| 100 | The Boost skills bundled with the SDK are copies made before the release, and they teach the API it removed: `make(threadId:)`, `setChatHistory()` and the `…ChatHistory` classes, `$workflow->resume()`, `abandonRun()`, `acknowledgeCompletion()`, `AsyncExecutor`, `NeuronAI\Observability\Events\`, `approvalPolicy(array $inputs)`, `resolveProvider()`, and an adapter instance passed to `setStreamAdapter()`, which now takes a factory. Install the skills that ship with neuron-ai instead |
| 101 | The SDK ships generators and no evaluation command. `vendor/bin/neuron evaluation` runs outside the booted application, so an evaluator that touches a facade fails with *"A facade root has not been set."* The `neuron-laravel-integration` skill has you write `php artisan neuron:evaluate` yourself |

### The in-package skills and README

| # | Issue |
|---|---|
| 102 | The skills that ship with 4.0.3 are current, not flawless. `neuron-workflow` prints `use NeuronAI\Agent;` and `->setProvider()` (item 66), speaks of "the built-in `StreamingNode`", which does not exist, and tells you to extend "the abstract `Event` base class", which is an interface. `neuron-evaluation` prints `use NeuronAI\Agent;`. `neuron-test` still calls `$workflow->resume([...])->run()`. `neuron-streaming` lists `NativeAdapter` (item 54). And `src/Tools/AGENTS.md` builds a `new DeferredTool(...)`; the class is `FrontendTool` | All of it is unchanged in 4.0.3, which only touched the `neuron-agent`, `neuron-evaluation`, `neuron-workflow` and Laravel/Symfony integration skills for the `posix`, `make:evaluators` and completion-retention changes
| 103 | The README says the installed skills are symlinked, "so they stay current whenever Neuron is updated through Composer". Upgrade guide 0 says nothing points into `vendor/` and that Composer does not refresh the installed copies. Not settled here; running `npx skills add ./vendor/neuron-core/neuron-ai/skills -y` again after every update is right either way |

## Priority order

If you have limited time, these seven matter most because they appear in the highest-traffic code:

1. **#77 and #78** — identity. Nothing runs without an ID, and the argument older material uses to pass one no longer exists. Affects every chapter.
2. **#30, #36 and #67** — the workflow execution API and how a paused run is continued, now that `resume()` is gone. Affects all of Part IV.
3. **#79** — the dead `chatHistory()` hook. The agent answers, keeps nothing durable, and nothing warns you.
4. **#94 to #97** — the Laravel SDK. The facade throws, and the shipped tables do not fit the stores.
5. **#45 and #46** — the approval-policy and error-handler signatures. The first is a fatal error when the class loads; the second fails exactly when a tool throws, which is the only time it matters.
6. **#26 and #58–59** — filters. The old method is gone, and the documented chain silently keeps only its last condition.
7. **#16 and #84** — observability. Nothing is traced until you subscribe the listener, a listener on an old class name never fires, and nothing warns you of either.
