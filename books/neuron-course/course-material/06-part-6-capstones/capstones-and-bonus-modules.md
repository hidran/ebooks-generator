# Agentic AI in PHP with Neuron
## PART VI — CAPSTONES + BONUS MODULES
### Project briefs and closing material

> Copy each section into its own Google Doc.
> Target versions: `neuron-core/neuron-ai` 4.0.3, `neuron-core/neuron-laravel` 2.0.0, PHP 8.5.

---

> ## NOTE — NEURON v4 IS RELEASED
>
> Earlier drafts of this course targeted v3 and spoke of a v4 "in beta" (and, in one draft, doubted that
> a v4 existed). v4 is out: `neuron-core/neuron-ai` 4.0.3 (released 2026-10-03) and `neuron-core/neuron-laravel`
> 2.0.0, which requires `neuron-ai ^4.0`. Everything in this file targets those two releases, and no
> working example uses v3 code.
>
> **Before recording:** run `composer show neuron-core/neuron-ai` and check the GitHub releases page: a later 4.x
> release may have changed something. Bonus module B1 is a **version strategy** lesson, including what
> changed between v3 and v4.

---
═══════════════════════════════════════════════════════════════
# CAPSTONE A — REPO AUDITOR CLI
═══════════════════════════════════════════════════════════════
---

## Project Brief

**Duration:** 3–4 hours of guided build, split across 6 videos
**Stack:** Plain PHP 8.5 + Composer. No framework. Needs `symfony/process` (`composer require symfony/process`) for the git tool.
**Covers:** Modules 3–10 (Part II)

### What the student builds

A command-line agent that audits a PHP repository and produces a structured report:

```bash
php auditor.php /path/to/repo --format=json
```

```
Auditing /home/hidran/projects/shop ...

  Reading composer.json
  Scanning source tree (412 files)
  Checking dependency advisories
  Reading recent commit history
  Analysing test coverage configuration

━━━ Repo Audit: shop ━━━

Health score       62 / 100
PHP constraint     ^8.1  (consider ^8.3)
Dependencies       47 direct, 3 with known advisories
Test setup         PHPUnit present, no coverage threshold configured
Commit cadence     14 commits in the last 30 days, 2 contributors

Findings (7)
  [high]   Package X has advisory CVE-... — upgrade to 2.4.1
  [medium] No CI configuration found
  [medium] 23 files exceed 400 lines
  ...

Written to audit-shop-2026-08-10.json
```

### Why this project

Three reasons worth stating to students:

**It has no external dependencies.** No API keys beyond the LLM, no database, no services. A student can complete it on a laptop, offline, with Ollama.

**The tools are genuinely useful.** Reading files, running `git log`, parsing `composer.json` — these are the shapes of tool that most real agents need.

**It exercises the full Part II surface** without any Laravel knowledge, which means it works as a standalone portfolio piece for a Symfony, WordPress or legacy-stack developer.

### Build order

**Video 1 — Scaffolding and the first agent (30 min)**

- Project setup from Lesson 3.1
- `ProviderFactory` from Lesson 3.6
- `AuditorAgent` with a `SystemPrompt` that establishes it as a code auditor, not a code fixer
- A CLI entry point taking a path argument

**Video 2 — The file system tools (45 min)**

Attach `FileSystemToolkit` confined to the repository and cut down with `only()`, and write two custom tools:

```php
use NeuronAI\Tools\Toolkits\FileSystem\FileSystemToolkit;
use NeuronAI\Tools\Toolkits\FileSystem\GlobPathTool;
use NeuronAI\Tools\Toolkits\FileSystem\GrepFileContentTool;
use NeuronAI\Tools\Toolkits\FileSystem\ReadFileTool;

$fileTools = FileSystemToolkit::make($repoPath)->only([
    ReadFileTool::class,
    GrepFileContentTool::class,
    GlobPathTool::class,
]);
```

```php
use NeuronAI\Tools\Tool;

class ComposerManifestTool extends Tool
{
    protected string $name = 'read_composer_manifest';

    protected ?string $description = 'Returns the composer.json of the repository being audited: the PHP version '
        . 'constraint, the direct dependencies with their version constraints, the '
        . 'autoload configuration, and the declared scripts. Use this first, before any '
        . 'other analysis, to understand what kind of project this is. Never guess a '
        . 'dependency version — read it here.';

    public function __construct(private readonly string $repoPath)
    {
    }

    protected function properties(): array
    {
        return [];   // no arguments — the path is a constructor dependency
    }

    public function __invoke(): string
    {
        $path = $this->repoPath . '/composer.json';

        if (! \is_file($path)) {
            return 'No composer.json found. This may not be a PHP project.';
        }

        $raw      = \file_get_contents($path);
        $manifest = $raw === false ? null : \json_decode($raw, true);

        if (! \is_array($manifest)) {
            return 'composer.json could not be read or is not valid JSON.';
        }

        return \json_encode([
            'name'        => $manifest['name']      ?? null,
            'php'         => $manifest['require']['php'] ?? null,
            'require'     => $manifest['require']     ?? [],
            'require-dev' => $manifest['require-dev'] ?? [],
            'scripts'     => \array_keys($manifest['scripts'] ?? []),
        ], JSON_THROW_ON_ERROR);
    }
}
```

**Two teaching points to draw out.**

The tool takes **no properties** — the repository path is a constructor dependency, not something the model chooses. The name and description are class properties (`Tool` has no constructor arguments for them in v4), so the constructor holds nothing but that dependency. That is deliberate: a path the model supplies is a path traversal waiting to happen. Lesson 5.1's principle, applied concretely. The toolkit's own tools do take a path, which is why the scope argument matters: `FileSystemToolkit::make($repoPath)` refuses anything outside `$repoPath`, and `only()` leaves out the write, edit, delete and shell tools (the toolkit has eight, not just read and search).

The return value is a **reduced** manifest, not the whole file. Lesson 19.1's argument about token cost, in a plain-PHP setting.

**Video 3 — The git tool and safe subprocess execution (30 min)**

`Process` is `Symfony\Component\Process\Process`, from the `symfony/process` package.

```php
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;
use Symfony\Component\Process\Process;

class GitHistoryTool extends Tool
{
    protected string $name = 'read_git_history';

    protected ?string $description = '...';   // the four-part formula from Lesson 5.4

    public function __construct(private readonly string $repoPath)
    {
    }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'days',
                type: PropertyType::INTEGER,
                description: 'How many days of history to summarise. Example: 30. Maximum 365.',
                required: true,
            ),
        ];
    }

    public function __invoke(int $days): string
    {
        $days = \max(1, \min(365, $days));   // clamp, never trust the model

        $process = new Process(
            ['git', 'log', "--since={$days} days ago", '--pretty=format:%h|%an|%ad|%s', '--date=short'],
            $this->repoPath,
        );

        $process->setTimeout(15);
        $process->run();

        if (! $process->isSuccessful()) {
            return 'Could not read git history. This may not be a git repository.';
        }

        $lines = \array_slice(\explode("\n", \trim($process->getOutput())), 0, 100);

        return $lines === [''] ? 'No commits in this period.' : \implode("\n", $lines);
    }
}
```

**Three things to emphasise on camera:**

**Argument arrays, never string interpolation.** `['git', 'log', "--since={$days} days ago"]` with Symfony Process passes arguments without a shell. Interpolating a model-supplied value into a shell string is remote code execution with extra steps.

**Clamp the numeric input.** `max(1, min(365, $days))`. The model may send 99999. Binding casts the *type* for you (`"30"` arrives as `30`, and `"thirty"` goes back to the model as an error before `__invoke()` runs), but it knows nothing about your *range*. Validation attributes are for structured output; tool argument ranges you enforce yourself. Note the property is `INTEGER`, not `NUMBER`: a `NUMBER` may legitimately bind as `30.5`, which an `int` parameter will not accept.

**Bound the output.** `array_slice(..., 0, 100)`. A repository with 40,000 commits would otherwise put 40,000 lines into the conversation.

And remember that what comes back is untrusted: commit subjects, author names and file contents belong to whoever wrote the audited repository, and a commit message can say "ignore your instructions". That is why the auditor is read-only.

**Video 4 — Structured output (35 min)**

The `AuditReport` DTO, using everything from Module 6:

```php
use NeuronAI\StructuredOutput\SchemaProperty;
use NeuronAI\StructuredOutput\Validation\Rules\NotBlank;
use NeuronAI\StructuredOutput\Validation\Rules\Regex;
use NeuronAI\StructuredOutput\Validation\Rules\WordsCount;

class Finding
{
    #[SchemaProperty(description: 'Severity: one of high, medium, low.', required: true)]
    #[Regex('/^(high|medium|low)$/')]
    public string $severity;

    #[SchemaProperty(description: 'Category, e.g. dependencies, testing, structure, security.', required: true)]
    #[NotBlank]
    public string $category;

    #[SchemaProperty(description: 'What the issue is, in one sentence. State the fact you observed.', required: true)]
    #[WordsCount(max: 30)]
    public string $description;

    #[SchemaProperty(description: 'The concrete action to take. Start with a verb.', required: true)]
    #[WordsCount(max: 25)]
    public string $recommendation;

    #[SchemaProperty(description: 'The file or package this concerns, if applicable.', required: false)]
    public ?string $subject = null;
}
```

```php
use NeuronAI\StructuredOutput\SchemaProperty;
use NeuronAI\StructuredOutput\Validation\Rules\GreaterThanEqual;
use NeuronAI\StructuredOutput\Validation\Rules\LowerThanEqual;
use NeuronAI\StructuredOutput\Validation\Rules\WordsCount;

class AuditReport
{
    #[SchemaProperty(description: 'Overall health score from 0 to 100.', required: true)]
    #[GreaterThanEqual(reference: 0)]
    #[LowerThanEqual(reference: 100)]
    public int $score;

    #[SchemaProperty(description: 'Two-sentence summary of the repository state.', required: true)]
    #[WordsCount(min: 15, max: 60)]
    public string $summary;

    #[SchemaProperty(
        description: 'Every issue found, most severe first.',
        required: true,
        anyOf: [Finding::class]
    )]
    public array $findings;
}
```

The attributes live in `NeuronAI\StructuredOutput\Validation\Rules\` (not in Symfony's validator, as older material has it). `#[WordsCount]` is doing real work here — without it the model writes paragraphs where you wanted a line, and your terminal output becomes unreadable.

**Video 5 — Streaming, error handling and run limits (30 min)**

- `stream()` with tool-activity labels (Lesson 7.4): the stream yields chunk objects, so filter with `instanceof TextChunk` for the text and read the tool-call chunks for the labels
- `toolErrorHandler()` returning instructions (Lesson 5.11): the callback is `fn (Throwable $e, ToolCall $call)`
- `toolMaxRuns()` for the agent-wide default (15, for the file tools), `setMaxRuns()` on your own tools: manifest 1, git 3
- `connection_aborted()` is irrelevant here; instead handle SIGINT gracefully — a user pressing Ctrl-C still deserves a clean exit

**Video 6 — Traces, evals and packaging (35 min)**

- Subscribe Inspector as Lesson 10.2 shows (it needs `inspector-apm/inspector-php ^3.19`, and nothing is traced until you subscribe the listener), read a real trace, tune the tool descriptions based on what you see
- A small eval suite: five repositories with known issues, asserting the findings mention them
- Package as a Composer `bin` so it installs globally

### Assessment rubric

| Criterion | Evidence |
|---|---|
| Tool design | Descriptions follow the four-part formula; property descriptions contain examples |
| Safety | Model-supplied paths confined to the repository; process arguments as arrays; numeric inputs clamped; read-only tools, with every tool result treated as untrusted text |
| Token discipline | Every tool bounds and reduces its output |
| Structure | Report is a validated DTO, not parsed prose |
| Resilience | Error handler returns instructions; run limits set per tool |
| Measurement | An eval suite exists and produces a score |

### Extensions for ambitious students

1. Add `parallelToolCalls(true)` — this is a CLI tool, so `pcntl` and `posix` are available if your PHP build includes them, and `spatie/fork` must be installed (Lesson 5.13)
2. Add an MCP connector to a GitHub server for issue and PR context (Module 9)
3. Compare the report across three providers and publish the differences

---
═══════════════════════════════════════════════════════════════
# CAPSTONE B — AGENTIC SUPPORT DESK
═══════════════════════════════════════════════════════════════
---

## Project Brief

**Duration:** 8–10 hours of guided build, split across 12 videos
**Stack:** Laravel 13 on PHP 8.5 + `neuron-core/neuron-laravel` 2.0.0 (on `neuron-ai` 4.0.3)
**Covers:** everything

### What the student builds

A multi-tenant customer support application where an agent handles enquiries end to end:

- Answers policy questions from a knowledge base (RAG)
- Looks up orders and shipment status (tools)
- Prepares refunds, which pause for human approval above a threshold (workflow + interruption)
- Streams its work to the customer live
- Escalates to a human when it cannot help
- Records everything for audit

This is Case C from Lesson 1.7 — the one where the four questions all pointed to rung 4. It earns every piece of machinery in the course, which is exactly why it is the capstone.

### The architecture

```
Customer (Livewire chat)
   │
   ├─ POST message
   │
SupportAgent (RAG + tools + EloquentMessageStore)
   │
   ├─ policy question → retrieval, tenant + visibility filtered
   ├─ order question  → SearchOrdersTool / GetOrderStatusTool
   └─ refund request  → RefundWorkflow
                          │
                          ├─ EligibilityNode   (structured output)
                          ├─ AmountNode        (tool: compute refund)
                          ├─ ApprovalNode      (interrupt if > threshold)
                          │      │
                          │      └─ workflow_store (paused run) + PendingApproval row
                          │                                    │
                          │                              Manager approves
                          │                                    │
                          │                          ResumeRefundWorkflow job
                          │
                          └─ ExecuteRefundNode (idempotent, audited)
```

### Build order

**Video 1 — Laravel setup (30 min)**
`composer require`, publish the config, one application migration for `chat_messages` and `workflow_store` (the ones SDK 2.0.0 ships do not fit neuron-ai 4.0.3), a smoke test through a container-resolved agent bound with `->for('smoke')` — the `Neuron` facade throws on neuron-ai 4.0.3, because it builds an agent with no thread ID — and the `app/Neuron` structure.

**Video 2 — Domain scaffolding (40 min)**
Tenants, users, orders, refunds, knowledge base articles. Factories and seeders. No AI yet — deliberately, so students see how little of the application is agentic.

**Video 3 — The first agent (35 min)**
`SupportAgent` with DI, `EloquentMessageStore` injected into the agent, with tenant and user carried in the thread ID, a controller, a plain Blade page.

**Video 4 — Knowledge base ingestion (50 min)**
`IndexArticle` job, custom Markdown splitter, metadata for tenant and visibility, the `indexed_at` gap alert.

**Video 5 — RAG with permission filters (40 min)**
A `DocumentSchema` declaring tenant and visibility as filterable, `retrievalScope()` applying both, the anti-hallucination system prompt, and the CI test asserting a restricted article never surfaces.

**Video 6 — Order tools (45 min)**
`SearchOrdersTool` and `GetOrderStatusTool` with tenant constructor dependency, column selection, bounded results, empty-case strings.

**Video 7 — Streaming chat with Livewire (45 min)**
`wire:stream`, tool-activity labels through an allowlist, the buffering checklist.

**Video 8 — The refund workflow (60 min)**
Events, nodes, `RefundEligibility` structured output, the bounded loop, `WorkflowState` subclass.

**Video 9 — Human in the loop (60 min)**
`interrupt()` with a custom `RefundApprovalRequest`, `memoize()` around the eligibility call, `DatabasePersistence` on the `workflow_store` table, the `PendingApproval` table for the manager's screen.

**Video 10 — The approval screen (50 min)**
Index and detail pages, a policy, `lockForUpdate()` resolution, the `ResumeRefundWorkflow` job, which delivers the decision with `ExecutionRequest::signal(RefundApprovalRequest::EVENT, $payload, expectedRunId: $runId, expectedExecutionAttempt: $attempt)`, notifications with expiry.

**Video 11 — Observability and evals (45 min)**
Inspector with the Laravel package (it needs `inspector-apm/inspector-php ^3.19`), subscribed explicitly (Lesson 10.2), usage logging, an eval suite with `FaithfulnessJudge`, the tenant-isolation and permission tests in CI.

**Video 12 — Production hardening (50 min)**
Budgets, rate limits, provider fallback, the audit table, and the deployment checklist from Lesson 23.6 worked through live.

### The three hardest parts, and how to teach them

**1. The memoization bug (Video 9).**

Build it wrong first. Compute refund eligibility inside `ApprovalNode` without `memoize()`, interrupt, resume — and show that the recomputed eligibility differs from what the manager approved.

Then wrap it:

```php
$eligibility = $this->memoize('eligibility', fn () => EligibilityAgent::make()
    ->setThreadId($state->getWorkflowId() . ':eligibility')
    ->structured(
        new UserMessage($this->describeOrder($order)),
        RefundEligibility::class
    ));
```

Same content on resume. The interrupted node still re-executes from the top — durable steps skip *completed* nodes, not the one that paused — so the closure's stored result is the only thing standing between the manager's decision and a freshly generated one. (`checkpoint()` was the older name for this; it still exists, deprecated, and delegates to `memoize()`.) The inner agent needs its own thread ID, because every agent run needs one. **This is the single most valuable five minutes in the capstone** — a demonstrable correctness failure, fixed in one line, that no tutorial covers.

**2. Idempotent refund execution (Video 12).**

```php
use Illuminate\Support\Facades\DB;
use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;

class ExecuteRefundNode extends Node
{
    public function __invoke(RefundApproved $event, RefundState $state): StopEvent
    {
        $refund = DB::transaction(function () use ($event, $state) {
            $order = Order::where('tenant_id', $state->tenantId())
                ->whereKey($state->orderId())
                ->lockForUpdate()
                ->firstOrFail();

            $existing = $order->refunds()
                ->where('workflow_id', $state->getWorkflowId())
                ->first();

            if ($existing !== null) {
                return $existing;   // this workflow already refunded — return the same record
            }

            $refund = $order->refunds()->create([
                'amount'      => $event->amount,
                'reason'      => $event->reason,
                'workflow_id' => $state->getWorkflowId(),
                'approved_by' => $event->approvedBy,
            ]);

            // same transaction, same workflow ID: a re-run returns above and writes no second audit row
            AgentAction::record($state, 'execute_refund', ['refund_id' => $refund->id]);

            return $refund;
        });

        return new StopEvent(result: $refund->id);
    }
}
```

The `workflow_id` on the refund record is the idempotency key. The workflow engine fences most duplicates before they reach this node — a resume carrying a stale run or attempt is refused (a stale run ID throws `StaleWorkflowRunException`, a stale attempt a plain `WorkflowException`), and a completed step is never re-run — but the fence protects the workflow's own bookkeeping, not your payment provider. A job that times out after the refund row commits and before the step does will run this node again, and the key is what makes that second run return the first refund instead of creating another. The order lookup carries the tenant: `RefundState` holds the tenant ID next to the order ID.

Point out that this is not an AI concern. It is ordinary distributed-systems hygiene, and it matters here because agentic systems retry and resume far more than typical request handlers.

**3. The escalation path (Video 6 or 12).**

Every agent needs a way to give up:

```php
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class EscalateTool extends Tool
{
    protected string $name = 'escalate_to_human';

    protected ?string $description = 'Hand this conversation to a human support agent. Use this when you cannot answer '
        . 'from the knowledge base, when the customer explicitly asks for a human, when the '
        . 'customer is upset, or when the request is outside what your tools can do. '
        . 'Using this tool is always an acceptable outcome — prefer it over guessing.';

    public function __construct(
        private readonly int $conversationId,
    ) {
    }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'reason',
                type: PropertyType::STRING,
                description: 'One sentence for the human agent: why you are escalating.',
                required: true,
            ),
        ];
    }

    public function __invoke(string $reason): string
    {
        Conversation::findOrFail($this->conversationId)->escalate($reason);

        return 'This conversation has been passed to a human agent. '
             . 'Tell the customer someone will reply shortly.';
    }
}
```

**"Using this tool is always an acceptable outcome — prefer it over guessing."**

That sentence in the description is worth its own slide. Without an explicit escape hatch, a model faced with an impossible request will invent something, because producing an answer is what it does. Giving it a legitimate way to fail is the most effective anti-hallucination measure in the entire application, and it costs one tool.

### Assessment rubric

| Area | Criterion |
|---|---|
| **Isolation** | Tenant test passes with colliding conversation IDs |
| **Retrieval** | Restricted-article test passes; filters declared in the `DocumentSchema` and applied inside `retrievalScope()` |
| **Tools** | Constructor-scoped; bounded; visible() from policies; write tools capped at 1 |
| **Workflow** | Every pre-interrupt LLM call memoized; loops bounded |
| **Approval** | `lockForUpdate()` resolution; expiry scheduled; resume dispatched not inline, carrying the run and attempt fences |
| **Idempotency** | Refund carries a workflow-scoped key; double resume creates one record |
| **Observability** | Inspector subscribed explicitly, on web and queue workers alike; usage logged |
| **Quality** | Eval suite with `FaithfulnessJudge`; a recorded baseline score |
| **Audit** | Every consequential tool writes an `agent_actions` row |
| **Escalation** | The agent has, and uses, a way to give up |

### The final exercise

Have students answer the five questions from Lesson 23.6 about their own capstone, on camera or in writing:

1. What does this agent cost per request, and at what volume does that become a problem?
2. What is the worst thing it can do, and what stops it?
3. How would I find out what it did, three weeks from now?
4. What happens when the provider is down?
5. What data leaves my infrastructure, and where does it go?

A student who can answer all five about code they wrote has completed the course in the way that matters.

---
═══════════════════════════════════════════════════════════════
# BONUS B1 — VERSION STRATEGY
═══════════════════════════════════════════════════════════════
---

**Duration:** 15 minutes
**Type:** Theory — and the lesson that keeps your course alive

### Learning objectives

Handle a fast-moving dependency, both as a developer and as a course author.

### The landscape, as of recording

- **v4 is current.** The course is verified on the released tags: `neuron-core/neuron-ai` 4.0.3 and `neuron-core/neuron-laravel` 2.0.0, on Laravel 13 and PHP 8.5.
- **Pre-release 4.x is still in circulation.** The 4.x branch was public before the 4.0.0 tag, and its API changed on the way to the release: how a run is resumed, how a thread ID is bound, where chat history lives, where observability events are. Tutorials, sample repositories and any assistant trained in that window show this dialect. It is not v3, it is not 4.0.3, and no upgrade guide covers it; the sixth check below recognises it.
- **v3 is the previous major.** Stable, widely deployed, and the version most tutorials written in 2025 and 2026 assume.
- **v1 and v2 are archived** but their documentation remains online at versioned paths, and their code is all over Medium, DEV and Stack Overflow.

> **Which version do you actually have?** Before you rely on any version claim, including this course's, run `composer show neuron-core/neuron-ai` and check the project's releases page. That command is the authority. If a 4.x minor has shipped since recording, read its changelog against the lessons you depend on.

### What changed between v3 and v4, and why it matters to you

Most Neuron code you will find online predates v4, whose workflow engine is built around **durable execution**, and several APIs have a different shape because of it. This table is the one place in the course where v3 code is shown: it is labelled, and it is never the only runnable version of anything.

| Older code (v3) | This course (v4) |
|---|---|
| `Tool::make($name, $description)->setCallable(...)` | `Tool` is abstract; name and description are class properties, the logic is `__invoke()` |
| `chat()` returns a response | `chat()` returns an `AgentState`; `getMessage()` can be `null` |
| `stream()` returns a handler with `events()` | `stream()` *is* the generator, of chunk objects; `getReturn()` gives the state |
| `$workflow->init()->run()` | `$workflow->run()` |
| An interrupt throws `WorkflowInterrupt` | A pause is a result: `$state->isInterrupted()` |
| `resume` with a request object | `submitInputs($payload)->run()` or `run(ExecutionRequest::resume($payload))`, addressed by workflow ID |
| `MyAgent::make()->chat(...)`, no ID needed | An ID is bound first: `make(workflowId: $threadId)` or `setThreadId()` |
| `chatHistory()` returning `FileChatHistory`, `SQLChatHistory` or `EloquentChatHistory` | `messageStore()` returning `FileMessageStore`, `SQLMessageStore` or `EloquentMessageStore` |
| `checkpoint()` | `memoize()` (`checkpoint()` survives, deprecated) |
| `ToolApproval` middleware | `approvalPolicy()` on the tool; `submitApprovalDecisions()` on the agent |
| `withFilters()` on the store | A `DocumentSchema` plus `retrievalScope()` |
| `observe(new InspectorObserver(...))` | PSR-14 events: `subscribe()` a listener |

Compare with what changed earlier, between v2 and v3, which you will also meet in older material:

```php
// v2 — does not run on v3 or v4
use NeuronAI\Agent;
$message = MyAgent::make()->chat(new UserMessage("Hi, who are you?"));
$message->addAttachment(new Image($url, AttachmentContentType::URL));
```

| v1 / v2 | v3 and later |
|---|---|
| `NeuronAI\Agent` | `NeuronAI\Agent\Agent` |
| `NeuronAI\SystemPrompt` | `NeuronAI\Agent\SystemPrompt` |
| attachments added with `addAttachment()` | content blocks on the message (in v4: `new UserMessage([new TextContent('Analyze this'), new ImageContent($url, SourceType::URL)])`) |

Underneath, every completed node is a **durable step**, committed to the workflow store and replayed rather than re-run after a crash or a pause. Agent and RAG are workflows (Lesson 2.3), so they inherit that durability, which is why a chat can be refused with `RunInFlightException` while an approval is pending on the same thread. The node that *paused* still re-executes from the top on resume (Module 15).

### The diagnostic to teach

When a student finds sample code that does not work, or that looks right and might not be:

1. **Check the `use` statements.** `NeuronAI\Agent;` without a second segment means v2 or earlier.
2. **Check for `->getMessage()`.** Its absence after `chat()` means v2.
3. **Check for `Edge` or `addEdges()`.** That is v1.
4. **Check for `->start()->getResult()`.** That is the v2 workflow API.
5. **Check for `->init()`, `catch (WorkflowInterrupt`, `ToolApproval` or `setCallable()`.** Any of them means v3.
6. **Check for the pre-release 4.x dialect:** `->resume(`, `make(threadId:`, `setChatHistory(`, any `*ChatHistory` class, `abandonRun(`, `acknowledgeCompletion(`, or `NeuronAI\Observability\Events\`. Any of them means a pre-release of v4. It looks current, and it fails on 4.0.3, not always loudly: an agent that still overrides `chatHistory()` runs, and quietly keeps the conversation in memory.

Six checks, and they identify the version of almost any snippet in seconds. Put them on a card students can keep.

### For the course itself

Practices that keep a course from rotting:

**Pin the exact version and commit `composer.lock`** in the teaching repository (`"neuron-core/neuron-ai": "4.0.3"`, not `^4.0`: a caret range accepts every later 4.x). A student following along in a year gets the API you recorded against.

**State the version on screen** in the first lesson of every part. A card in the corner costs nothing.

**Tag every lesson in Git.** `git checkout lesson-05-tools` gets the exact starting state.

**Keep a living errata document** linked from every lesson description. Updating a paragraph is minutes; re-recording a video is hours.

**Record the concepts long and the API short.** Lessons about tool descriptions, chunking strategy and the agent loop stay true across majors. Lessons that are mostly method signatures do not, so keep those tight and expect to re-record them.

**Do not chase a new major immediately.** Let the ecosystem catch up. Add an upgrade module rather than re-recording the course. The same goes for pre-releases: an API can still move between a pre-release and its tag.

**Read the upgrade guide before the changelog.** NeuronAI's guide to v4 ships *inside the package*, in `vendor/neuron-core/neuron-ai/upgrade/`: one numbered guide per breaking change, each with search patterns and before/after code, so the version you read is the version you installed. An upgrade goes in this order: on a branch, bump the version, run static analysis first (removed classes and methods show up as errors), run your contract tests, work through the in-package guides in order starting with guide 0 (it reinstalls the agent skills), and run your evals last.

That last pair is the real advice, and it applies to any framework course. **Structure the course so the durable material is separable from the perishable material**, and you re-record 15% instead of 100%.

### Key takeaways

- v4 is current; v3 code is the most common thing you will find, and v1/v2 code is still everywhere. None of it runs against 4.0.3 unchanged.
- Six checks identify a snippet's version, the pre-release 4.x dialect included.
- The upgrade guide ships in `vendor/`; read that one, not the website's.
- Pin the exact version and the lock file, tag every lesson, keep an errata document.
- Separate durable concepts from perishable API so you re-record 15%, not 100%.

---
═══════════════════════════════════════════════════════════════
# BONUS B2 — THE ECOSYSTEM
═══════════════════════════════════════════════════════════════
---

**Duration:** 25 minutes
**Type:** Orientation

### Maestro — a complete application to read

**Maestro is the first CLI agent built entirely in PHP with Neuron.** It is a coding assistant in the shape of Claude Code or Aider, and it is open source.

```bash
composer global require neuron-core/maestro
```

*(On Windows, install and run it under WSL.)*

It supports every Neuron provider — Anthropic, OpenAI, Gemini, Cohere, Mistral, Ollama, Grok, DeepSeek — routed through a provider factory, and integrates Inspector via an `inspector_key` in `.maestro/settings.json`.

**Why it belongs in this course.** The author's own assessment is the point:

> The framework doing the heavy lifting here is Neuron AI, specifically the workflow architecture introduced in v3. Without the ability to interrupt execution mid-agent-loop and resume it based on user input, the tool approval system would require significantly more scaffolding to build and maintain. This pattern — interrupt, present, resume — would have been painful to implement without a workflow-oriented framework underneath.

That is Module 15, validated by a real application. Students who finished Part IV can read Maestro's source and recognise every pattern. Check its `composer.json` first: the quote describes the v3 architecture, and an application of Maestro's size moves to a new major on its own schedule. If it still targets v3, reading it is also a good exercise in the six-check diagnostic from B1.

**Two features worth studying specifically:**

**The tool approval system** — interactive confirmation before sensitive operations. Lesson 15.5's tool approval, in production (in 4.0.3 that is `approvalPolicy()` on the tool, not a `ToolApproval` middleware).

**The extension system** — PHP classes implementing `ExtensionInterface`, registered through an `ExtensionApi` injected at boot. An `ExtensionLoader` builds registries for tools, commands, renderers, events, memories and UI. This is a well-designed plugin architecture and worth reading on its own merits, independent of AI.

**Suggested exercise:** write a Maestro extension that adds one tool from Capstone A. It is the shortest path from "I built a CLI agent" to "I extended someone else's".

### Neuron Hub

A registry of community extensions and toolkits. Two uses:

**Check before you build.** Someone may have written your integration.

**Publish yours.** A well-built toolkit — a class extending `AbstractToolkit` with a real `guidelines()` method (Lesson 5.7) — is a small, achievable open-source contribution with a clear audience.

For a student building a portfolio, this is a better first contribution than a documentation typo: scoped, useful, and demonstrably yours.

### Neuron Studio

`digitalelvis/neuronai-studio` — a community package offering a visual agent builder for Laravel that **exports real PHP classes**.

Useful for prototyping and for showing architecture to non-developers. The caveat to state plainly: it generates code, it does not replace understanding it. A student who reaches for Studio before finishing Part II will produce classes they cannot debug.

### Beyond Laravel

The framework is deliberately framework-agnostic, and the core package needs only PHP 8.1.

**Symfony.** Everything from Parts II–IV applies directly. Register agents as services; `SQLMessageStore` takes a plain PDO, which you get from a Doctrine connection with `getNativeConnection()`. Inspector ships `inspector-symfony`.

**Spryker, WordPress, legacy in-house.** Same story. The core package has no framework dependencies. The Laravel SDK is, in the maintainers' own words, something you can use *as inspiration to design your own custom integration pattern.*

The framework's positioning argument is worth quoting for a mixed audience:

> Rather than fragmenting innovation across framework-specific solutions, Neuron enables collaboration between Laravel developers, Symfony contributors, WordPress plugin authors, and custom framework teams.

**Say this explicitly to non-Laravel students in Part I**, so they know Part V is a case study rather than a prerequisite. It affects whether they buy the course.

### Key takeaways

- Maestro is a complete open-source application built on the patterns in this course — read it.
- Neuron Hub is a realistic first open-source contribution.
- Studio generates code; it does not replace understanding it.
- The core package is framework-agnostic; Part V transfers to Symfony, Spryker and anything else.

---
═══════════════════════════════════════════════════════════════
# BONUS B3 — AI-ASSISTED DEVELOPMENT
═══════════════════════════════════════════════════════════════
---

**Duration:** 20 minutes
**Type:** Practical, with a caution

### Learning objectives

Use coding assistants effectively on a fast-moving library, and understand why this is harder than it looks.

### The problem, specific to this course

The public corpus is full of v1, v2 and v3 Neuron code, and of pre-release 4.x code. A coding assistant will confidently produce `use NeuronAI\Agent;`, `new Edge(NodeA::class, NodeB::class)`, `->init()->run()` and a `ToolApproval` middleware — because that is what most of the internet says. One trained on the pre-release will write `Agent::make(threadId: $id)` or `->resume($payload)->run()` instead: they look right, and they fail on 4.0.3.

Worse: the assistant will be *fluent* about it. Wrong code with a confident explanation is harder to catch than wrong code that looks uncertain.

### Three fixes, in order of effectiveness

**1. The framework's own agent material.** NeuronAI ships guidance for coding assistants inside the package: an `AGENTS.md` beside each module in `vendor/neuron-core/neuron-ai/src/`, a set of agent skills in `vendor/neuron-core/neuron-ai/skills/`, and the upgrade guides in `upgrade/`, which are written to be executed step by step by an assistant. On a project upgraded from an older version, reinstall the skills first: the old ones describe the old API. On Laravel, take care (Lesson 17.7): the Boost skills bundled with neuron-laravel 2.0.0 are copies made before the release and still teach removed forms — `make(threadId:)`, `setChatHistory()`, `resume()`, an `approvalPolicy(array $inputs)` signature. Point your assistant at the skills in `vendor/neuron-core/neuron-ai/skills/` instead; they include `neuron-laravel-integration`. Treat all of it as better than training data and worse than the code.

**2. Documentation over MCP.** The framework offers an MCP server for its documentation. Connect it to Claude Code, Cursor or any MCP-capable assistant and the assistant reads current docs rather than recalling stale training data.

This is a nice loop to point out: **Module 9 taught MCP as a way to give your agents capabilities. Here you use it to give your assistant knowledge about the framework you are building agents with.**

**3. A project rules file.** Whatever your assistant reads — `CLAUDE.md`, `.cursorrules`, or equivalent:

```markdown
# NeuronAI conventions for this project

Verified version: neuron-core/neuron-ai 4.0.3 (Laravel SDK: neuron-core/neuron-laravel 2.0.0)
Require it exactly (`"neuron-core/neuron-ai": "4.0.3"`), never `^4.0`: a caret range accepts every later 4.x
Code from v1-v3 or from a pre-release 4.x is wrong here, even when it looks current

## Namespaces (do not use v1/v2 forms)
- `NeuronAI\Agent\Agent`     NOT `NeuronAI\Agent`
- `NeuronAI\Agent\SystemPrompt`  NOT `NeuronAI\SystemPrompt`
- Observability events: `NeuronAI\Agent\Observability\`, `NeuronAI\Workflow\Observability\`, `NeuronAI\RAG\Observability\`

## API (4.0.3 — do not use v3 or pre-release forms)
- `chat()` returns `AgentState` — `->getMessage()?->getContent()`
- `stream()` is the generator — iterate it; chunks are objects; `->getReturn()` for the state
- Workflows: `->run()` / `->events()`, NOT `init()`; no `Edge` class
- A pause is a result: check `$state->isInterrupted()`, never catch `WorkflowInterrupt`
- Resume with `->run(ExecutionRequest::resume($payload))` or `->submitInputs($payload)->run()`; there is no `resume()` method
- Bind an ID before any run: `make(workflowId: $id)` or `setThreadId($id)`; `make(threadId: ...)` does not exist
- Memory is `messageStore()` returning a `MessageStoreInterface` (`SQLMessageStore`, `EloquentMessageStore`); no `*ChatHistory` classes, no `setChatHistory()`
- Tools extend `Tool`; `$name` / `$description` are properties, not constructor args
- Approval lives on the tool (`approvalPolicy()`), NOT in a `ToolApproval` middleware

## Project rules
- Tools are classes, never anonymous
- Toolkits filtered with `only()`, never `exclude()`
- Write tools: `setMaxRuns(1)` + idempotency guard + transaction
- Every pre-interrupt LLM call wrapped in `memoize()`
- Tenant scope is a constructor dependency, never read from ambient context
- When a snippet, a skill or your memory disagrees with `vendor/neuron-core/neuron-ai/`, the source wins
```

That file is worth building live on camera. It is a distillation of the whole course into thirty-odd lines, and it makes an excellent free preview lesson — it shows prospective students what the course covers without giving away how any of it works.

### The honest caution

The verification list kept for this course (44 items at first, 103 in the report now sent to the maintainers) is the evidence. **The official documentation itself has drifted from the code in dozens of places** — wrong namespaces, misspelled class names, three different constructor signatures for one class, two different execution APIs on adjacent pages.

An assistant reading that documentation inherits every one of those errors.

The discipline to teach, which is the same discipline this course applied throughout:

**Use assistants for shape.** Scaffolding, boilerplate, test fixtures, repetitive DTOs. They are genuinely good at this.

**Verify anything touching the API surface** against your installed version — your IDE's go-to-definition, or `vendor/` directly.

**Never trust a version claim.** If the assistant says "in Neuron v4 you do X", check. It has no reliable way to know.

That habit transfers well beyond this framework, and it is a good note to end the course on: **the tools are useful and they are not authoritative, and knowing the difference is what makes you the engineer in the loop.**

### Key takeaways

- The public corpus is full of v1–v3 and pre-release 4.x code; assistants reproduce it fluently.
- Three fixes: the framework's in-package agent material (on Laravel, the neuron-ai skills rather than the bundled Boost ones), documentation over MCP, a project rules file.
- The documentation itself has drifted — assistants inherit its errors.
- Use assistants for shape, verify the API surface, never trust a version claim.

---
═══════════════════════════════════════════════════════════════
# COURSE COMPLETE
═══════════════════════════════════════════════════════════════

## What has been produced

| Part | Modules | Lessons |
|---|---|---|
| I — Foundations | 1–2 | 12 |
| II — Plain PHP | 3–10 | 51 |
| III — RAG | 11–12 | 12 |
| IV — Workflows | 13–16 | 18 |
| V — Laravel | 17–23 | 39 |
| VI — Capstones + bonus | — | 2 projects, 3 bonus modules |
| **Total** | **23** | **~132 lessons** |

Plus: 10 labs, 2 capstone projects, and a pre-recording verification list (103 items in the maintainers' report).

## Still to produce before recording

**Re-run the verification items** (103 in the maintainers' report, most of them settled by the source on 4.0.3). Run one script per part against your installed version and settle every ambiguity. Budget half a day. This is the single highest-value preparation task, and a short segment in the free preview explaining that you did it is a strong trust signal.

**Re-verify against the latest 4.x.** `composer show neuron-core/neuron-ai --all` plus the GitHub releases page: everything here was checked on 4.0.3 and neuron-laravel 2.0.0.

**Decide the Module 5.13 placement.** Parallel tool calls need `pcntl`, which is CLI-only. It may read better in Part V alongside queue workers, where students already have the infrastructure.

**Build the teaching repository** with per-lesson Git tags and a committed `composer.lock`.

## The through-line, for your course description

Twenty-three modules answering one question from Lesson 1.1 — *who decides what happens next* — and then building everything required to let a model answer it safely: tools to give it hands, structure to make its output usable, retrieval to give it knowledge, workflows to give it shape, interruption to keep a human in the decision, and observability to find out what it actually did.

The closing question from Lesson 23.6 is the one to put in the sales page:

> **What is the worst thing your agent can do, and what stops it?**

A developer who can answer that about their own system has understood this course. Nobody else in the PHP space is teaching that, and it is the difference between a course about a framework and a course about building things that are allowed to run in production.
