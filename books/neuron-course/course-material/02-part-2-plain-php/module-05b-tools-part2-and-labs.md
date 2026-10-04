# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Module 5, Lessons 5.8 to 5.13 + Labs

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^4.0.3, PHP 8.5.
> Continues from Lessons 5.1–5.7.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.8 — Toolkit Filters: exclude, only, with

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Attach a toolkit and then narrow it, so the agent gets the capabilities it needs and nothing more.

### Why filtering is not a nicety

A toolkit is a coherent set, but "coherent" is not the same as "appropriate for this agent". Three concrete costs of attaching more than you need:

**Tokens.** Every tool's name, description and parameter schema is transmitted on **every** iteration of the loop. The Calendar toolkit alone is eighteen tools. At five loop iterations you have paid for that schema five times.

**Wrong-tool errors.** Selection accuracy degrades as the catalogue grows. Fourteen maths tools where two would do means twelve extra chances to pick the wrong one.

**Blast radius.** Every attached tool is reachable by any user who can talk to the agent. That is Lesson 5.1's security model, applied to convenience imports.

### exclude()

Attach the toolkit, remove specific tools:

```php
class DocsAgent extends Agent
{
    protected function tools(): array
    {
        return [
            FileSystemToolkit::make('/srv/docs')->exclude([
                WriteFileTool::class,
                EditFileTool::class,
                DeleteFileTool::class,
                BashTool::class,
            ]),
        ];
    }
}
```

Exclusion works on fully qualified class names. Use it when you want most of a toolkit and are removing a few known problems.

### only()

Attach the toolkit, keep a subset:

```php
protected function tools(): array
{
    return [
        CalculatorToolkit::make()->only([
            StandardDeviationTool::class,
            MedianTool::class,
        ]),
    ];
}
```

Use it when you want a small, specific slice of a large toolkit.

### exclude or only? A rule that ages well

**Prefer `only()`.**

`exclude()` is a denylist, and denylists rot. When the framework adds tools to a toolkit in a new release, your `exclude()` list does not know about them — and your agent silently gains capabilities you never reviewed.

That is not a hypothetical. The FileSystem toolkit once offered only reading, searching and parsing; it now also ships write, edit, delete and bash tools. An agent written as `FileSystemToolkit::make()->exclude([ParseFileTool::class])` against the older toolkit, and upgraded without a review, gained a shell.

`only()` is an allowlist. New tools appear in the toolkit and your agent does not get them until you say so. That is the correct default for anything touching data or side effects. The `DocsAgent` above is better written as:

```php
FileSystemToolkit::make('/srv/docs')->only([
    ReadFileTool::class,
    GrepFileContentTool::class,
    GlobPathTool::class,
]),
```

Use `exclude()` when you genuinely want breadth and are pruning known problems. Use `only()` everywhere else, and especially in Part V when tools reach your database.

### with()

Retrieve a specific tool from the toolkit and reconfigure it:

```php
protected function tools(): array
{
    return [
        MySQLToolkit::make($this->pdo)
            ->with(
                MySQLSchemaTool::class,
                fn (ToolInterface $tool): ToolInterface => $tool->setMaxRuns(1)
            ),
    ];
}
```

Pass the class name and a callback. The tool instance is injected, you change its settings, you return it.

The schema tool is the natural example: an agent only needs to inspect the schema once. Limiting it to a single run stops a confused model from re-reading the entire structure five times, which is both slow and expensive given that schema output is verbose.

`with()` is also where per-tool approval goes when the tool comes from a toolkit — `fn (Tool $tool): ToolInterface => $tool->requireApproval()` on `MySQLWriteTool`, for instance. The parameter is typed `Tool` there because the approval methods are declared on the base class, not on `ToolInterface`. Lesson 5.10 covers approval.

> **The method is `setMaxRuns()`.** The `with()` example in the documentation calls `setMaxTries(1)` (the v3 name), and passes the toolkit no PDO connection. Neither works: there is no `setMaxTries()` — the tool-level setter is `setMaxRuns()` and the agent-level one is `toolMaxRuns()` — and `MySQLToolkit` requires its PDO.

### Combining filters

The methods chain:

```php
CalculatorToolkit::make()
    ->only([EvaluateTool::class, MeanTool::class])
    ->with(EvaluateTool::class, fn (ToolInterface $tool): ToolInterface => $tool->setMaxRuns(3));
```

Two tools, one of them capped. Read it top to bottom: select, then configure.

### Key takeaways

- Filtering reduces tokens, wrong-tool errors and blast radius.
- Prefer `only()` — allowlists survive framework updates; denylists do not.
- `with()` reconfigures a single tool inside a toolkit.
- Filters chain.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.9 — Max Runs: Guarding the Loop

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Configure the framework's safety limit correctly, and understand what an exceeded limit is actually telling you.

### The unbounded loop, revisited

Lesson 1.2 established that the agent loop is a `while` with no guaranteed exit. The model keeps requesting tools until it decides it is finished. If it never decides, the loop never ends.

This is not hypothetical. Three ways it happens in practice:

- The tool returns something the model misreads as failure, so it retries. Forever.
- The task is genuinely impossible with the tools available, and the model keeps trying alternatives.
- Two tools feed each other in a cycle — search returns a reference, fetch returns something needing another search.

Each iteration costs a model call and grows the context. Unbounded, this is a runaway bill.

### The guard

Neuron counts how many times each tool is invoked during an agent run — one `chat()` turn, including any pause for human approval in between. Exceed the limit and the tool node throws `ToolRunsExceededException`. **The default is 10 calls, counted per tool individually.**

That "per tool individually" detail matters. Five tools at the default limit means up to fifty tool executions in one `chat()` call before anything stops.

### Setting it

```php
use NeuronAI\Exceptions\ToolRunsExceededException;

try {
    $message = YouTubeAgent::make()
        ->setThreadId('demo')
        ->toolMaxRuns(5) // Max number of calls for each tool
        ->addTool(
            // Tool level config takes precedence over the global setting
            CustomTool::make()->setMaxRuns(2)
        )
        ->chat(new UserMessage($input))
        ->getMessage();

} catch (ToolRunsExceededException $exception) {
    // do something
}
```

Two levels:

- **`toolMaxRuns(n)`** on the agent — the default for every tool.
- **`setMaxRuns(n)`** on a tool — overrides the agent setting for that tool.

**Tool-level wins.** That precedence is what you want: a permissive global default with tight limits on the tools that are slow, expensive or dangerous.

> **Catch the right exception class.** The documentation has named the exception two ways: `ToolRunsExceededException` in its prose, `ToolMaxTriesException` (the v3 name) in an example catch block. Only the first exists — `NeuronAI\Exceptions\ToolRunsExceededException`. PHP does not complain about a `catch` naming a class that does not exist, it simply never matches. A wrong class name produces silent non-handling rather than an obvious error, which is the worst kind of bug to inherit.

### What counts as "the same tool"

The counter is keyed by the tool's *run key*, which is its name by default: every `get_current_weather` call consumes the same budget, whatever the coordinates. That is right for most tools, but it cannot tell a model that is legitimately checking five cities from one that is asking for the same city five times.

When the arguments matter, add the `TrackByInputs` trait to the tool class:

```php
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\TrackByInputs;

class WeatherTool extends Tool
{
    use TrackByInputs;

    // ...
}
```

The run key becomes the tool name plus a hash of the inputs, so `setMaxRuns(1)` now means "at most once *per set of arguments*": five different cities go through, the same city twice does not. For anything subtler — only some parameters matter — override `getRunKey()` yourself.

Two further details of the accounting. A call a human *rejected* consumes no slot. And the count survives interruptions: an approval pause in the middle of a run does not reset it.

### Choosing values

| Tool character | Suggested limit | Reasoning |
|---|---|---|
| Schema introspection | 1 | Read once; the answer does not change mid-run |
| Expensive external API | 2–3 | Each call costs money or quota |
| Cheap local computation | 5–10 | Genuinely needs repetition for multi-step maths |
| Write operations | 1 | Two identical writes is almost always a bug |

That last row is the important one, and it pays to be exact about what it buys. The limit holds inside one run: a model that calls the write tool a second time in the same turn gets `ToolRunsExceededException` instead of a second charge. It does not hold across turns. The counter starts again with the next `chat()`, so a user who replies "try again" gets a second write. What makes a write safe to repeat is an idempotency key: derive one from the operation itself — the order number, the payment intent — and have the code that performs the write refuse a duplicate. Set the limit deliberately, and build the guard as well; Lesson 19.2 does.

### What an exceeded limit is telling you

This is the point students miss. An exceeded run limit is not usually a limit that is set too low. It is a **diagnostic**, and it almost always means one of three things:

1. **Your tool description is unclear**, so the model keeps trying variations. Go back to Lesson 5.4.
2. **Your tool returns something ambiguous** — an empty string, an unhelpful error — so the model cannot tell success from failure.
3. **The task is impossible with the tools provided**, and the model is flailing. Give it a tool that can say "not available" as a legitimate answer.

Raising the limit "to make it work" treats the symptom. When you hit this exception, read the trace and find out what the model was trying to accomplish on attempt eight.

### Handling it gracefully

An exception reaching the user as a 500 is bad. Catch it and degrade:

```php
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Exceptions\ToolRunsExceededException;

try {
    $answer = $agent->chat(new UserMessage($input))->getMessage()?->getContent();
} catch (ToolRunsExceededException $e) {
    // Log the full trace for diagnosis
    $logger->warning('Agent exceeded tool run limit', [
        'input'     => $input,
        'exception' => $e::class,
        'message'   => $e->getMessage(),
    ]);

    $answer = "I couldn't complete that request. Could you rephrase it, "
            . "or would you like me to pass it to a human?";
}
```

Lesson 5.11 covers a more sophisticated option: handing the error back to the model so it can recover on its own.

### Key takeaways

- Default is 10 runs, per tool, per agent run; exceeding it throws `ToolRunsExceededException`.
- `toolMaxRuns()` sets the agent default; `setMaxRuns()` on a tool overrides it.
- Runs are counted by run key — the tool name by default; `TrackByInputs` counts per set of arguments.
- Write tools should be capped at 1 — per run. Across turns, only an idempotency guard prevents a duplicate write.
- An exceeded limit is a diagnostic about tool design, not a limit to raise.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.10 — Visibility: Conditional Tool Availability

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Make tool availability depend on who is asking, and understand why hiding beats refusing.

### The API

```php
class YouTubeAgent extends Agent
{
    protected function tools(): array
    {
        return [
            GetTranscriptionTool::make('API_KEY')->visible(
                auth()->user()->can('read-transcripts')
            ),
        ];
    }
}
```

`visible(false)` and the tool is not available during agent execution. It is not in the schema sent to the model. As far as the model is concerned, it does not exist.

### Why hiding beats instructing

The tempting alternative is to put the rule in the system prompt:

> "Only use the refund tool if the user is an administrator."

Do not do this. Three reasons, in ascending order of seriousness:

**It leaks.** The model knows the tool exists and will mention it. "I could process a refund, but you don't have permission" tells a user exactly which capability to go after.

**It is unreliable.** Instructions are followed probabilistically. Lesson 1.5 said assume non-determinism, and an access-control rule that works ninety-eight per cent of the time is not access control.

**It is attackable.** Instructions in the system prompt compete with instructions in the user's message. Prompt injection is a live technique; a schema that never included the tool is not vulnerable to it.

`visible(false)` removes the capability rather than forbidding its use. The model cannot request a tool it was never told about.

### Where visibility fits among the layers

Four independent mechanisms, and understanding what each one does is the point of this lesson:

| Layer | Mechanism | Enforced by |
|---|---|---|
| Not offered | `visible(false)` | Schema construction |
| Offered, gated at runtime | `approvalPolicy()`, `requireApproval()` | Human decision |
| Offered, checked on execution | Policy check inside `__invoke()` | Your PHP |
| Offered, restricted at source | Database grants, API scopes | Infrastructure |

Use several. `visible()` is your first line, not your only one — a bug in the visibility expression should not be the only thing between a user and a refund.

### Visibility vs. approval

The documentation draws this distinction well and it is worth reproducing precisely:

- **Visibility** is a *build-time* decision. The tool is included in the schema, or it is not. Decided before the model ever sees anything.
- **Approval** is a *runtime gatekeeper*. The tool is offered, the model requests it, and the framework intercepts the call and pauses for a human decision.

Approval is expressed on the tool itself, and it can be conditional on the arguments:

```php
BuyTicketTool::make()->withApprovalPolicy(
    fn (ToolInterface $tool): bool|string => $tool->getInput('amount') > 100
        ? 'Purchases above 100 need a human sign-off'
        : false
)
```

Small purchases go through; large ones wait for a human. That is a much better product than either always-allow or always-block. We build the full human-in-the-loop flow in Module 15 and wire it to a real UI in Module 22; the rest of this lesson covers what belongs to the tool and the agent, so the distinction lands while visibility is fresh.

> **v3 form, for recognition only.** Older material gates tools with a `ToolApproval` middleware: `new ToolApproval(tools: [BuyTicketTool::class => fn (array $args): bool => ...])`. That middleware no longer exists in v4; approval lives on the tool, as below.

### Approval lives on the tool

Before every tool call, the agent's tool node asks the tool one question: *does this call require approval?* The tool answers with the call's arguments already bound — and cast, as Lesson 5.5 described. There is no middleware to register and no agent-level switch; a tool that never asks for approval is never gated.

The answer comes from two places.

**The tool author declares the tool's intrinsic risk** by overriding `approvalPolicy()`. The default returns `false`. Return `true` to gate the tool — or return a string, which counts as `true` and doubles as the reason shown to the approver:

```php
class TransferMoneyTool extends Tool
{
    protected string $name = 'transfer_money';

    protected ?string $description = 'Transfers money between two accounts of the current customer.';

    protected function approvalPolicy(): bool|string
    {
        return ($this->inputs['amount'] ?? 0) > 100
            ? 'Transfers above $100 require a human sign-off'
            : false;
    }

    // properties(), __invoke() ...
}
```

This is the right home for risk that is a property of the tool: a transfer is dangerous in every agent that ever attaches it, so the tool says so once.

> **`approvalPolicy()` takes no arguments.** The documentation shows `approvalPolicy(array $inputs)`. The method takes no parameters: the inputs are already bound on the tool, so read them from `$this->inputs` or `$this->getInput('amount')`. Copying the documented signature is a fatal error — PHP rejects an override whose signature is incompatible with the parent's.

**The agent developer overrides it at attach time**, in either direction:

```php
protected function tools(): array
{
    return [
        DeleteFileTool::make()->requireApproval(),
        TransferMoneyTool::make()->suppressApproval(),
        BuyTicketTool::make()->withApprovalPolicy(
            fn (ToolInterface $tool): bool|string => $tool->getInput('amount') > 100
                ? 'Purchases above 100 need a human sign-off'
                : false
        ),
    ];
}
```

`requireApproval()` gates every call. `suppressApproval()` waives a policy the tool declared — for an internal batch agent, say, where no human is available and the risk is managed elsewhere. `withApprovalPolicy()` replaces the declared policy with your own callback, which receives the tool with the call's inputs bound. If you configure more than one, the last override wins. Tools that come from a toolkit get the same treatment through `with()`, from Lesson 5.8.

### What the caller sees

When a gated call comes up, `chat()` does not throw and does not wait. It returns a state that is *interrupted*:

```php
$agent = ShopAgent::make(workflowId: $threadId);

$state = $agent->chat(new UserMessage('Buy two tickets for Saturday'));

if ($state->isInterrupted()) {
    foreach ($agent->pendingApprovals() as $action) {
        // $action->id      the tool call ID to decide on
        // $action->name    the tool name
        // $action->reason  why the tool asked, from its policy
        // $action->inputs  the typed arguments
    }
}
```

`isInterrupted()` is the test to use. A paused state still has a message — `getMessage()` returns the model's tool-call message, not an answer — so a null check would tell you nothing. `pendingApprovals()` returns one `Action` per call still waiting for a decision — enough to render an approval screen. A decision comes back keyed by call ID, and `run()` continues the same run:

```php
$state = ShopAgent::make(workflowId: $threadId)
    ->submitApprovalDecisions([
        'call_123' => 'approve',
        'call_456' => ['reject', 'Too expensive, ask the user for a cheaper option'],
    ])
    ->run();
```

Three rules make this safe. **A tool runs only if it is explicitly approved** — silence is never consent, and a payload that leaves a call undecided suspends the run again. **A rejection is not an error**: the model receives a tool result saying the action was not executed, together with your reason, and carries on with that knowledge. And **calls that needed no approval still run** — in the example, a cheap purchase requested in the same turn executes once the batch is decided.

While the decision is outstanding the thread belongs to the paused run: a new `chat()` on it throws `RunInFlightException` instead of starting a second run beside the first. Across two HTTP requests — the chat endpoint, then the approve endpoint — the thread ID is all the second request has to carry: the paused run is found by it. For that to work the agent needs a workflow persistence backend and a durable message store (Lesson 4.3), so the second process can load what the first one saved. Module 15 sets that up.

### The pattern to teach

Compute visibility from the actor, not from a global:

```php
class OrderAgent extends Agent
{
    public function __construct(
        private User $user,
        private OrderRepository $orders,
        private RefundService $refunds,
    ) {
        parent::__construct();
    }

    protected function tools(): array
    {
        return [
            SearchOrdersTool::make($this->orders),

            GetOrderStatusTool::make($this->orders),

            RequestRefundTool::make($this->refunds)
                ->visible($this->user->can('refund.create')),

            DeleteOrderTool::make($this->orders)
                ->visible($this->user->hasRole('admin')),
        ];
    }
}
```

The agent takes the user as a constructor dependency and derives its own capability surface. Two users talking to "the same agent" are talking to agents with different tool lists.

A constructor of your own changes one thing about building the agent: the thread ID is no longer its first argument, so bind the conversation afterwards. `::make()` still forwards whatever the constructor takes — `OrderAgent::make($user, $orders, $refunds)->setThreadId($threadId)`. When a container builds the agent instead, `->for($threadId)` returns a copy bound to the thread; Part V uses that form.

### Exercise

Add a `delete_cache` tool to your demo agent, visible only when `APP_ROLE=admin`. Run the agent as a non-admin and ask it directly: "delete the cache". Then ask: "what tools do you have?" Verify the tool is absent from both the behaviour and the answer.

### Key takeaways

- `visible(false)` removes the tool from the schema entirely.
- Hiding beats instructing: prompt-based restrictions leak, are probabilistic, and are attackable.
- Visibility is build-time; approval is runtime. Both exist, for different jobs.
- Approval lives on the tool: `approvalPolicy()` declares it, `requireApproval()` / `suppressApproval()` / `withApprovalPolicy()` override it at attach time.
- A gated call returns an interrupted state; `pendingApprovals()` lists what to decide, `submitApprovalDecisions([...])->run()` continues. Only explicit approval runs a tool.
- Derive visibility from the actor, injected into the agent's constructor.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.11 — Tool Error Handling

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Decide what happens when a tool throws, and use the model's own recovery ability instead of crashing.

### The default

A tool can end in two ways: it returns, or it throws. Neuron treats the two differently, on purpose, and the split falls on the natural boundary of the language.

**A return value is a conversational outcome.** Whatever `__invoke()` returns becomes the tool result the model sees, and the loop continues.

**An escaped exception is a bug.** It propagates up through `chat()` into your application and aborts the run. The conversation history stays consistent — the half-finished tool call is never committed — but the turn is over.

That is a reasonable default — silent failure would be worse — but it means the decision is yours, tool by tool: which failures are part of the conversation, and which are defects?

### The alternative: tell the model

This is the idea worth the whole lesson. A failure the model can do something about should not crash the run; it should be handed back to the model as the tool's result.

The model then decides what to do: retry with different arguments, try a different tool, or tell the user the data is unavailable. You get graceful degradation without writing recovery logic, because the recovery logic is the model.

The primary way to do that is to **return** the failure, with `ToolOutput::error()`:

```php
use NeuronAI\Tools\ToolOutput;

public function __invoke(string $order_id): string|ToolOutput
{
    $order = $this->orders->find($order_id);

    if ($order === null) {
        return ToolOutput::error(
            "No order matches \"{$order_id}\". Check the number with the user before trying again."
        );
    }

    return \json_encode([
        'id'     => $order->id,
        'status' => $order->status,
        'eta'    => $order->eta,
    ], \JSON_THROW_ON_ERROR);
}
```

The error text becomes the result the model reads, flagged as a failure. Providers with a native error flag on tool results — Anthropic, Bedrock — receive it as such; the others receive the text. Catch your own exceptions at the tool boundary and convert the recoverable ones like this, visibly, in the code that knows what went wrong. Neuron's built-in tools follow the same convention: a division by zero in the calculator's `evaluate` returns `Division by zero at position 2` as an error result, not an exception. And as Lesson 5.5 showed, the framework already does this for you when the model sends an argument of the wrong type, leaves out a required one, or picks a value outside an `enum:`.

What remains are exceptions you did not anticipate — from a library, a driver, a network client deep in the call. For those there is an agent-level override: a **tool error handler**. It receives every exception that escapes a tool. **If the handler returns a value, that value is returned to the model as the result of the tool**, and the loop continues. If it returns `null`, it declines, and the exception propagates as before.

### Fluent definition

```php
use NeuronAI\Tools\ToolCall;
use NeuronAI\Tools\ToolOutput;

$agent = Agent::make()
    ->toolErrorHandler(
        fn (Throwable $e, ToolCall $call): ToolOutput => ToolOutput::error("Error: {$e->getMessage()}")
    );
```

### Inside the agent class

```php
class MyAgent extends Agent
{
    protected function resolveToolErrorHandler(): ?callable
    {
        return fn (Throwable $e, ToolCall $call): ToolOutput => ToolOutput::error("Error: {$e->getMessage()}");
    }
}
```

The callback receives the exception and the failing call — the `ToolCall` from Lesson 5.1, with the tool's name and the arguments the model sent. Both matter — the call lets you branch on which tool failed. It may return a string, a `ToolOutput`, or `null`.

Type the second parameter as `ToolCall`. The documentation (and every v3 example) types it `ToolInterface`, and a handler written that way fails with a `TypeError` at exactly the wrong moment — the first time a tool throws.

### Writing a good handler

The naive version leaks internals into the conversation. A 500-character stack trace becomes context the model must reason about, and possibly text a user sees.

Write handlers that tell the model something *actionable*:

```php
use NeuronAI\Exceptions\HttpException;

protected function resolveToolErrorHandler(): ?callable
{
    return function (\Throwable $e, ToolCall $call): ?ToolOutput {
        $this->logger->error('Tool failure', [
            'tool'      => $call->getName(),
            'inputs'    => $call->getInputs(),
            'exception' => $e::class,
            'message'   => $e->getMessage(),
        ]);

        return match (true) {
            $e instanceof HttpException => ToolOutput::error(
                "The {$call->getName()} service is temporarily unreachable. "
                . "Do not retry more than once. If it fails again, tell the user "
                . "the data is unavailable right now."
            ),

            $e instanceof AuthorizationException => null,

            default => ToolOutput::error(
                "The {$call->getName()} tool failed. Tell the user you could not "
                . "complete this step, and do not retry."
            ),
        };
    };
}
```

(`AuthorizationException` stands for your application's own permission exception; it is not part of Neuron.) Four principles visible in that code:

**Log fully, tell the model briefly.** Your logs get the exception and the arguments. The model gets one sentence.

**Include the instruction, not just the fact.** "Do not retry more than once" is doing real work. Without it, a transient failure can burn through the max-runs limit from Lesson 5.9 in seconds.

**Never leak internals into the conversation.** Connection strings, file paths, internal hostnames, credentials in exception messages — all of these end up in the transcript, which may be stored, logged and shown to the user.

**Decline what must not be handled.** The `null` arm hands the permission failure back to your application untouched. More on that below.

### The interaction with max runs

The error handler catches the run-limit exception too. That gives you a graceful exit at the limit rather than an exception at the boundary:

```php
$e instanceof ToolRunsExceededException => ToolOutput::error(
    "You have used this tool too many times. Stop calling it and answer with "
    . "what you already know, or tell the user you cannot complete the task."
),
```

The model receives a clear stop signal and writes a sensible final message. Far better than a 500. (The class is `NeuronAI\Exceptions\ToolRunsExceededException`; the v3 name `ToolMaxTriesException` does not exist.)

### When to let it crash

Not everything should be handled. Throw from the tool — and return `null` from the handler for that exception — when:

- The failure indicates a bug you need to see in your error tracker
- The failure is a permission violation — do not let the model reason about that, fail hard and audit it
- The failure would leave data in an inconsistent state

"Return the error to the model" is a resilience pattern for expected, recoverable failures. It is not a substitute for correctness.

### Key takeaways

- A returned value is a conversational outcome; an escaped exception is a bug that aborts the run.
- Return recoverable failures from the tool with `ToolOutput::error()`.
- The agent's error handler, `fn (Throwable $e, ToolCall $call)`, converts escaped exceptions: a returned value becomes the tool result, `null` lets the exception propagate.
- Log fully, tell the model briefly, and include an instruction about retrying.
- Never leak internals into the transcript.
- Let permission violations and bugs crash.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.12 — Provider Tools

**Duration:** 10 minutes
**Type:** Theory with code

### Learning objectives

Use a provider's built-in capabilities where they fit, and know the constraints you accept in exchange.

### What they are

Some providers ship server-side tools — web search, file search and others — that execute inside their infrastructure rather than in your PHP process. You enable them; the provider runs them.

### The API

```php
use NeuronAI\Providers\OpenAI\Responses\OpenAIResponses;
use NeuronAI\Tools\ProviderTool;

class MyAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new OpenAIResponses(
            key: 'OPENAI_API_KEY',
            model: 'OPENAI_MODEL',
        );
    }

    protected function tools(): array
    {
        return [
            ProviderTool::make(
                type: 'web_search'
            )->setOptions([/* ... */]),
        ];
    }
}
```

They sit in the same `tools()` array as everything else, which is a nice piece of API design — the abstraction holds.

**Support is limited to `OpenAIResponses`, `Gemini`, `Anthropic` and `ZAI`.** Every other provider — Ollama, the OpenAI chat-completions API, Mistral, Bedrock — throws a `ProviderException` when it finds a provider tool in the list.

> Older versions of the documentation show `ProviderTool:make()` with a single colon. It is a typo for `::`.

### The trade-off, stated as the docs state it

The official documentation is refreshingly blunt: provider tools introduce a lot of constraints, and the most flexible and reliable way to add capabilities to your agents remains the Tools and Toolkits system.

That is the framework authors telling you their own feature is the second choice. Take them at their word, and explain why to students:

**You lose portability.** This is the big one. Lesson 3.6 sold provider swapping as the framework's central benefit. A provider tool anchors you: switch from OpenAI to Ollama and the agent stops working, because the Ollama provider rejects the tool with an exception on the very first request. At least the failure is loud. But the whole cost-tiering and vendor-risk argument evaporates for any agent that depends on one.

**You lose control.** You cannot see the query, filter the sources, cache the result, rate-limit it, or log what was retrieved. For a regulated environment, "we don't know what it searched" is not an acceptable answer.

**You lose testability.** No fake, no stub, no offline CI. Lesson 5.3 made testability the argument for tool classes; provider tools give it back.

**You inherit their constraints.** Rate limits, regional availability, pricing and behaviour are all outside your control and can change without a deployment on your side.

### When they are the right call

Not never. Provider tools are genuinely good when:

- You are prototyping and want web search working in thirty seconds
- The provider's implementation is materially better than what you would build (their search index, their document handling)
- You are already committed to that provider for other reasons
- The capability is peripheral — nice to have, not load-bearing

### The recommended default

Use `TavilyToolkit` or `JinaToolkit` for web search. Both are portable, both work with any provider, both are testable, both let you see and cache what came back. Choose one per agent, though: each provides a tool named `web_search` and another named `url_reader`, and tool names must be unique, so an agent given both toolkits throws a `ToolException` the first time it runs.

Reach for a provider tool when you have a specific reason, and write the reason down.

### Key takeaways

- Provider tools run server-side; supported on OpenAIResponses, Gemini, Anthropic and ZAI only — other providers throw.
- They cost you portability, control, testability and independence.
- The framework's own documentation recommends the portable Tools/Toolkits system.
- Good for prototypes and peripheral capabilities; bad for anything load-bearing.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.13 — Parallel Tool Calls

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Cut wall-clock time when the model requests several tools at once, and know exactly where this optimisation does not apply.

### The problem

When the model requests three tools in one turn, the default behaviour is sequential:

```
1. Call tool A → wait for result
2. Call tool B → wait for result
3. Call tool C → wait for result

Total time: Time(A) + Time(B) + Time(C)
```

Three API calls at 800 ms each is 2.4 seconds of the user staring at nothing — and that is one iteration of the loop.

With parallel execution:

```
1. Call tool A, B, and C all at once
2. Wait for all to complete

Total time: Max(Time(A), Time(B), Time(C))
```

800 ms. A third of the time, for one boolean.

### Enabling it

```bash
composer require spatie/fork
```

```php
class DemoAgent extends Agent
{
    public function __construct()
    {
        parent::__construct();
        $this->parallelToolCalls(true);
    }

    protected function provider(): AIProviderInterface
    {
        // ...
    }

    protected function tools(): array
    {
        return [
            CalculatorToolkit::make(),
        ];
    }
}
```

Under the hood, the framework injects a `ParallelToolNode` in place of the standard `ToolNode`. This is Lesson 2.3 becoming concrete: an agent is a workflow, and "enable parallel tools" means *swap one node for another*. Worth pointing at explicitly — it is the first time in the course that the workflow substrate is visibly doing something.

### The constraint that decides everything

**It requires the `pcntl` and `posix` extensions (`posix` since 4.0.3) and the `spatie/fork` package, and `pcntl` only works in CLI processes, not in a web context.**

Read that twice before designing around this feature. It means:

| Context | Parallel tools |
|---|---|
| CLI script | ✅ Yes |
| Artisan command | ✅ Yes |
| Queue worker (CLI) | ✅ Yes |
| HTTP request via PHP-FPM | ❌ No |
| Web request in any SAPI | ❌ No |

For a web application, the practical route is: push agent execution to a queue worker, which is a CLI process. That is where parallel tools apply — and it happens to be where you wanted long-running agent work anyway, for the latency reasons from Lesson 1.4. Module 22 builds this properly.

### Graceful degradation

The design here is thoughtful and worth praising in the video: if `pcntl` or `posix` is not present — a Windows development machine, for instance — or `spatie/fork` is not installed, the implementation **automatically falls back to sequential execution**. It does the same when the model requested only one tool, which is not worth a fork. No configuration, no environment detection in your code, no crash.

You develop locally without `pcntl`/`posix` and deploy to production where it is enabled, without changing a line. The agent adapts to whatever environment it finds itself in.

That is a good example of a framework absorbing environmental variation instead of pushing it onto the developer, and it is the kind of detail worth teaching as a design pattern rather than just a feature.

### When it actually helps

Parallel execution only helps when the model requests **multiple tools in a single turn**. It does nothing for:

- Sequential dependencies — B needs A's output, so they cannot overlap
- Single-tool turns
- Fast local tools, where fork overhead exceeds the work

It helps most with several independent I/O-bound calls: three weather lookups, four API queries, five file reads. If your agent is not tool-hungry in this specific way, enabling it changes nothing.

### Cautions

**Forked processes do not share state.** Each fork is a separate process. Tools that mutate shared in-memory state, hold an open transaction, or assume a singleton will behave differently. Keep tools stateless and self-contained — which Lesson 5.1 recommended anyway, for other reasons.

**Debugging is harder.** Errors in a forked process are less pleasant to trace. Develop with it off, enable it when the tool set is stable.

**Database connections need care.** A PDO connection inherited across a fork is a classic source of strange, intermittent failures. If your tools hit the database, open the connection inside the tool rather than sharing one across forks — or use the two hooks `parallelToolCalls()` accepts, which run inside every child process before and after its tool:

```php
$this->parallelToolCalls(
    true,
    beforeChild: fn () => DB::purge(),
    afterChild: fn () => DB::purge(),
);
```

That is the Laravel form: drop the inherited connection so the child opens its own. Only each tool's *result* travels back from the child, serialized; the tool object and its dependencies never cross the process boundary.

### Key takeaways

- `parallelToolCalls(true)` swaps `ToolNode` for `ParallelToolNode`.
- Requires `spatie/fork`, `pcntl` and `posix`; **CLI only**, never in a web request.
- Falls back to sequential automatically when unavailable, and for single-call turns.
- `beforeChild` / `afterChild` hooks reset per-process resources such as database connections.
- Helps only with multiple independent I/O-bound calls in one turn.
- Keep tools stateless; be careful with database connections across forks.

---
═══════════════════════════════════════════════════════════════
# MODULE 5 LABS
═══════════════════════════════════════════════════════════════
---

## LAB 3 — Weather + Calculator Agent

**Duration:** 25 minutes
**Covers:** custom tool class, toolkit, filters, max runs, error handling

### Goal

An agent that answers *"What's the average current temperature between Turin and Milan?"* by calling a weather tool twice and a calculator tool once. Three round trips to the model. It is the clearest demonstration of the agent loop in the whole course.

### The tool

**`src/Tools/WeatherTool.php`**

```php
<?php

declare(strict_types=1);

namespace App\Tools;

use NeuronAI\Exceptions\HttpException;
use NeuronAI\HttpClient\Curl\CurlHttpClient;
use NeuronAI\HttpClient\HttpClientInterface;
use NeuronAI\HttpClient\HttpRequest;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolOutput;
use NeuronAI\Tools\ToolProperty;

class WeatherTool extends Tool
{
    private const BASE_URL = 'https://api.open-meteo.com/v1/';

    protected string $name = 'get_current_weather';

    protected ?string $description = 'Returns current weather conditions for a geographic location: temperature '
        . 'in Celsius, wind speed in km/h, and a numeric weather code. Use this '
        . 'whenever the user asks about current weather, temperature, or conditions '
        . 'anywhere in the world. You must derive latitude and longitude yourself '
        . 'from the place name. Never invent weather data — always call this tool.';

    protected HttpClientInterface $client;

    public function __construct(?HttpClientInterface $client = null)
    {
        $this->client = $client ?? (new CurlHttpClient(timeout: 10.0))->withBaseUri(self::BASE_URL);
    }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'latitude',
                type: PropertyType::NUMBER,
                description: 'Latitude in decimal degrees. Example: 45.0703 for Turin, Italy. '
                           . 'Negative values for the southern hemisphere.',
                required: true,
            ),
            new ToolProperty(
                name: 'longitude',
                type: PropertyType::NUMBER,
                description: 'Longitude in decimal degrees. Example: 7.6869 for Turin, Italy. '
                           . 'Negative values for the western hemisphere.',
                required: true,
            ),
        ];
    }

    public function __invoke(float $latitude, float $longitude): string|ToolOutput
    {
        $query = \http_build_query([
            'latitude'  => $latitude,
            'longitude' => $longitude,
            'current'   => 'temperature_2m,wind_speed_10m,weather_code',
        ]);

        try {
            $data = $this->client->request(HttpRequest::get("forecast?{$query}"))->json();
        } catch (HttpException) {
            return ToolOutput::error(
                'The weather service is unreachable right now. Do not retry; '
                . 'tell the user the data is unavailable.'
            );
        }

        if (!isset($data['current'])) {
            return ToolOutput::error('The weather service returned no current conditions for these coordinates.');
        }

        return \json_encode($data['current'], \JSON_THROW_ON_ERROR);
    }
}
```

Open-Meteo needs no API key, so the whole lab runs free — combined with Ollama, students complete it with no account anywhere.

Three things in this class are worth a second look. The `float` parameters need no defensive widening, because binding casts the model's `"45.07"` to `45.07` before the call (Lesson 5.5). An unreachable service is *returned* as `ToolOutput::error()` rather than thrown, with an instruction attached (Lesson 5.11). And the HTTP client is the framework's own `CurlHttpClient`, so the lab adds no dependency — while the optional constructor argument is the seam from Lesson 5.3: a test passes a stub and never reaches Open-Meteo.

### The agent

**`src/Agents/WeatherAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use App\Tools\WeatherTool;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\ToolCall;
use NeuronAI\Tools\ToolOutput;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\Calculator\EvaluateTool;
use NeuronAI\Tools\Toolkits\Calculator\MeanTool;
use Throwable;

class WeatherAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a weather assistant. You only report real data obtained from your tools.',
            ],
            steps: [
                'Derive the geographic coordinates of every location mentioned by the user.',
                'Call the weather tool once for each location.',
                'If a comparison or an average is requested, use the calculator tools.',
            ],
            output: [
                'Answer in English, in two sentences at most.',
                'Always state temperatures in degrees Celsius.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            WeatherTool::make()->setMaxRuns(4),

            CalculatorToolkit::make()->only([
                EvaluateTool::class,
                MeanTool::class,
            ]),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return function (Throwable $e, ToolCall $call): ToolOutput {
            \error_log(\sprintf('[tool:%s] %s: %s', $call->getName(), $e::class, $e->getMessage()));

            return ToolOutput::error(
                "The {$call->getName()} tool failed. Do not retry more than once. "
                . 'If it fails again, tell the user the data is unavailable.'
            );
        };
    }
}
```

Note what this class demonstrates from the module: a class-based tool (5.3), a four-part description (5.4), examples in property descriptions (5.4), `only()` as an allowlist (5.8), a per-tool run cap (5.9), and a real error handler (5.11). Of the calculator's fourteen tools the agent keeps two: `evaluate` for any formula and `mean` for averages.

### The runner

**`examples/03-weather-agent.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\WeatherAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? "What's the average current temperature between Turin and Milan?";

$start = \microtime(true);

try {
    echo WeatherAgent::make()
        ->setThreadId('demo')
        ->toolMaxRuns(6)
        ->chat(new UserMessage($prompt))
        ->getMessage()
        ?->getContent() . PHP_EOL;

    \printf("\n[%.2fs]\n", \microtime(true) - $start);
} catch (\Throwable $e) {
    \fwrite(STDERR, "Failed: {$e->getMessage()}\n");
    exit(1);
}
```

```bash
php examples/03-weather-agent.php
php examples/03-weather-agent.php "Compare Turin, Milan, Rome and Palermo. Which is warmest?"
```

### What to point out on camera

Run it with Inspector wired in, as Module 10 shows (in v4 tracing is a PSR-14 subscriber that you subscribe explicitly; the key alone records nothing), and open the trace. Students see the actual sequence: two weather calls, one calculator call (`mean`, or `evaluate` with the whole formula), one final text response. That picture is what Lesson 1.2's table described in the abstract, and seeing it makes the cost arithmetic of Lesson 1.4 concrete.

Then break it deliberately: change the tool description to `'Gets the weather.'` and re-run. Frequently the model answers from general knowledge without calling the tool at all. Change it back. One string, completely different behaviour — Lesson 5.4's claim, demonstrated.

---

## LAB 4 — Database Analyst Agent

**Duration:** 25 minutes
**Covers:** MySQL toolkit, schema scoping, least privilege, read-only design

### Goal

An agent that answers real questions about a real database without hallucinating numbers.

### Set up a scoped database user

Before any PHP, this:

```sql
CREATE USER 'agent_ro'@'localhost' IDENTIFIED BY 'a-strong-password';

GRANT SELECT ON shop.orders     TO 'agent_ro'@'localhost';
GRANT SELECT ON shop.customers  TO 'agent_ro'@'localhost';
GRANT SELECT ON shop.products   TO 'agent_ro'@'localhost';

FLUSH PRIVILEGES;
```

**Do this first, and say why on camera.** Everything else in this lab is application-layer control that a sufficiently clever prompt might get around. This grant is enforced by MySQL. It is the only layer that cannot be talked out of its position.

### The agent

**`src/Agents/DataAnalystAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Exceptions\ToolRunsExceededException;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\Calculator\EvaluateTool;
use NeuronAI\Tools\Toolkits\Calculator\MeanTool;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSchemaTool;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSelectTool;
use NeuronAI\Tools\ToolCall;
use NeuronAI\Tools\ToolOutput;

class DataAnalystAgent extends Agent
{
    private \PDO $pdo;

    public function __construct()
    {
        parent::__construct();

        $this->pdo = new \PDO(
            \sprintf(
                'mysql:host=%s;dbname=%s;charset=utf8mb4',
                env('DB_HOST', '127.0.0.1'),
                env('DB_NAME', 'shop'),
            ),
            env('DB_USER', 'agent_ro'),
            env('DB_PASS', ''),
            [\PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION],
        );
    }

    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a data analyst working with a read-only e-commerce database.',
                'You never estimate or guess numbers. Every figure you report comes from a query.',
            ],
            steps: [
                'Inspect the database schema first, once, to understand the available tables.',
                'Write a SELECT query that answers the question.',
                'Use the calculator tools for any derived statistics.',
            ],
            output: [
                'State the number, then the query you ran, in a fenced sql block.',
                'If a question cannot be answered with the available tables, say so plainly.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            MySQLSchemaTool::make(
                $this->pdo,
                ['orders', 'customers', 'products'],
            )->setMaxRuns(1),

            MySQLSelectTool::make($this->pdo)->setMaxRuns(5),

            CalculatorToolkit::make()->only([
                EvaluateTool::class,
                MeanTool::class,
            ]),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return function (\Throwable $e, ToolCall $call): ToolOutput {
            if ($e instanceof ToolRunsExceededException) {
                return ToolOutput::error(
                    "You have used {$call->getName()} as often as allowed. "
                    . 'Answer from the results you already have.'
                );
            }

            \error_log(\sprintf('[tool:%s] %s: %s', $call->getName(), $e::class, $e->getMessage()));

            return ToolOutput::error(
                "The {$call->getName()} tool failed. Do not retry; tell the user "
                . 'the data is unavailable right now.'
            );
        };
    }
}
```

The handler has less to do than you might expect. A query the database rejects — an unknown column, a table the user may not read — never reaches it: `MySQLSelectTool` returns the database's own message to the model as an error result, which is what lets the model correct its SQL. What does reach the handler is the rest. A run limit gets a sentence telling the model to work with what it has. The genuinely unexpected — a lost connection, a failure in the schema tool — gets a log line for you and one fixed sentence for the model, never the exception's text (Lesson 5.11).

### The runner

**`examples/05-data-analyst.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\DataAnalystAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'How many orders did we receive today?';

echo DataAnalystAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage($question))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

```bash
php examples/05-data-analyst.php "How many orders did we receive today?"
php examples/05-data-analyst.php "What's the average order value this month, by country?"
php examples/05-data-analyst.php "Which three products have the highest revenue?"
```

### Four defence layers, and the demonstration

Count them out on screen:

1. **`MySQLWriteTool` is not attached.** The agent has no tool that writes, and the one that reads cannot be talked into it: `MySQLSelectTool` accepts a single statement that begins with `SELECT`, `WITH`, `SHOW`, `DESCRIBE` or `EXPLAIN`, and runs it in a `READ ONLY` transaction that it always rolls back.
2. **The schema tool describes three tables.** The model is never told that `payments` or `users` exist. This layer is advisory: it narrows what the model is shown, not what the connection can read, and a model that guesses a table name is stopped by layer 4, not by this one.
3. **`MySQLSchemaTool` is capped at one run.** No repeated expensive introspection.
4. **The database user only holds SELECT on three tables.** Enforced by MySQL.

Then run the demonstration that makes the point:

```bash
php examples/05-data-analyst.php "Delete all orders from last year."
```

The agent explains it cannot. Not because the prompt told it not to — because **there is no tool that writes.** That distinction is the entire security lesson of Module 5, and it lands far better as a live demo than as a slide.

---

## MODULE 5 ASSESSMENT

1. **Design.** Take a feature from your own application and design three tools for it. Write the descriptions before the implementations. For each, answer the four questions from Lesson 5.4.

2. **Convert.** Take one inline tool and convert it to a class. Write a PHPUnit test that invokes it directly with no agent involved.

3. **Constrain.** Attach a toolkit with `only()`, set a per-tool run cap, and add an error handler that returns an instruction rather than a stack trace.

4. **Break it.** Deliberately write a vague tool description and observe the failure. Fix it with one string change. Record what changed in the model's behaviour.

5. **Secure.** For an agent with database access, list your defence layers and identify which one an attacker could not defeat with a prompt.

---

**END OF MODULE 5**

*Next: Module 6 — Structured Output. Getting typed PHP objects out of a language model.*
