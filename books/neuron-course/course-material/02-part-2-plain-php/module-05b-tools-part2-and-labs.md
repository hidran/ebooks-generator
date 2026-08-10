# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Module 5, Lessons 5.8 to 5.13 + Labs

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^3.0, PHP 8.3.
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

**Wrong-tool errors.** Selection accuracy degrades as the catalogue grows. Twelve arithmetic tools where three would do means nine extra chances to pick the wrong one.

**Blast radius.** Every attached tool is reachable by any user who can talk to the agent. That is Lesson 5.1's security model, applied to convenience imports.

### exclude()

Attach the toolkit, remove specific tools:

```php
class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            CalculatorToolkit::make()->exclude([
                DivideTool::class,
                ExponentiateTool::class,
                MultiplyTool::class,
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

`exclude()` is a denylist, and denylists rot. When the framework adds three tools to a toolkit in a minor release, your `exclude()` list does not know about them — and your agent silently gains capabilities you never reviewed.

`only()` is an allowlist. New tools appear in the toolkit and your agent does not get them until you say so. That is the correct default for anything touching data or side effects.

Use `exclude()` when you genuinely want breadth and are pruning known problems. Use `only()` everywhere else, and especially in Part V when tools reach your database.

### with()

Retrieve a specific tool from the toolkit and reconfigure it:

```php
protected function tools(): array
{
    return [
        MySQLToolkit::make()
            ->with(
                MySQLSchemaTool::class,
                fn (ToolInterface $tool) => $tool->setMaxTries(1)
            ),
    ];
}
```

Pass the class name and a callback. The tool instance is injected, you change its settings, you return it.

The schema tool is the natural example: an agent only needs to inspect the schema once. Limiting it to a single run stops a confused model from re-reading the entire structure five times, which is both slow and expensive given that schema output is verbose.

> **Verify the method name.** The `with()` example in the documentation calls `setMaxTries(1)`, while the Max Runs section uses `setMaxRuns()`. Item 2 on your verification list — check which exists in your installed version.

### Combining filters

The methods chain:

```php
CalculatorToolkit::make()
    ->only([SumTool::class, MeanTool::class, DivideTool::class])
    ->with(DivideTool::class, fn (ToolInterface $tool) => $tool->setMaxRuns(3));
```

Three tools, one of them capped. Read it top to bottom: select, then configure.

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

Neuron tracks how many times each tool is invoked during an execution session. Exceed the limit and execution is interrupted with an exception. **The default is 10 calls, counted per tool individually.**

That "per tool individually" detail matters. Five tools at the default limit means up to fifty tool executions in one `chat()` call before anything stops.

### Setting it

```php
try {
    $response = YouTubeAgent::make()
        ->toolMaxRuns(5) // Max number of calls for each tool
        ->addTool(
            // Tool level config takes precedence over the global setting
            CustomTool::make()->setMaxRuns(2)
        )
        ->chat(...)
        ->getMessage();

} catch (ToolMaxTriesException $exception) {
    // do something
}
```

Two levels:

- **`toolMaxRuns(n)`** on the agent — the default for every tool.
- **`setMaxRuns(n)`** on a tool — overrides the agent setting for that tool.

**Tool-level wins.** That precedence is what you want: a permissive global default with tight limits on the tools that are slow, expensive or dangerous.

> **Verify the exception class.** The prose in the documentation names `ToolRunsExceededException`; the example catch block names `ToolMaxTriesException`. Item 1 on your verification list. Check what your version actually throws before writing a catch block — and before recording, since a wrong class name in a `catch` produces silent non-handling rather than an obvious error.

### Choosing values

| Tool character | Suggested limit | Reasoning |
|---|---|---|
| Schema introspection | 1 | Read once; the answer does not change mid-run |
| Expensive external API | 2–3 | Each call costs money or quota |
| Cheap local computation | 5–10 | Genuinely needs repetition for multi-step maths |
| Write operations | 1 | Two identical writes is almost always a bug |

That last row is the important one. A write tool with a limit of 1 means a retrying model cannot double-charge a customer. Set it deliberately.

### What an exceeded limit is telling you

This is the point students miss. `ToolRunsExceededException` is not usually a limit that is set too low. It is a **diagnostic**, and it almost always means one of three things:

1. **Your tool description is unclear**, so the model keeps trying variations. Go back to Lesson 5.4.
2. **Your tool returns something ambiguous** — an empty string, an unhelpful error — so the model cannot tell success from failure.
3. **The task is impossible with the tools provided**, and the model is flailing. Give it a tool that can say "not available" as a legitimate answer.

Raising the limit "to make it work" treats the symptom. When you hit this exception, read the trace and find out what the model was trying to accomplish on attempt eight.

### Handling it gracefully

An exception reaching the user as a 500 is bad. Catch it and degrade:

```php
use NeuronAI\Chat\Messages\UserMessage;

try {
    $answer = $agent->chat(new UserMessage($input))->getMessage()->getContent();
} catch (\Throwable $e) {
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

- Default is 10 runs, per tool, per execution session.
- `toolMaxRuns()` sets the agent default; `setMaxRuns()` on a tool overrides it.
- Write tools should be capped at 1.
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
                auth()->user()->can(...)
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
| Offered, gated at runtime | `ToolApproval` middleware | Human decision |
| Offered, checked on execution | Policy check inside `__invoke()` | Your PHP |
| Offered, restricted at source | Database grants, API scopes | Infrastructure |

Use several. `visible()` is your first line, not your only one — a bug in the visibility expression should not be the only thing between a user and a refund.

### Visibility vs. approval

The documentation draws this distinction well and it is worth reproducing precisely:

- **Visibility** is a *build-time* decision. The tool is included in the schema, or it is not. Decided before the model ever sees anything.
- **Approval** is a *runtime gatekeeper*. The tool is offered, the model requests it, and the framework intercepts the call and pauses for a human decision.

Approval is expressed with the `ToolApproval` middleware, and it can be conditional on the arguments:

```php
new ToolApproval(
    tools: [
        BuyTicketTool::class => function (array $args): bool {
            return $args['amount'] > 100;
        }
    ]
)
```

Small purchases go through; large ones wait for a human. That is a much better product than either always-allow or always-block. We build it properly in Module 15 and wire it to a real UI in Module 22 — mentioned here so the distinction lands while visibility is fresh.

### The pattern to teach

Compute visibility from the actor, not from a global:

```php
class OrderAgent extends Agent
{
    public function __construct(private User $user)
    {
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

Note that this requires `new OrderAgent($user)` rather than `::make()`, as established in Lesson 4.3.

### Exercise

Add a `delete_cache` tool to your demo agent, visible only when `APP_ROLE=admin`. Run the agent as a non-admin and ask it directly: "delete the cache". Then ask: "what tools do you have?" Verify the tool is absent from both the behaviour and the answer.

### Key takeaways

- `visible(false)` removes the tool from the schema entirely.
- Hiding beats instructing: prompt-based restrictions leak, are probabilistic, and are attackable.
- Visibility is build-time; approval is runtime. Both exist, for different jobs.
- Derive visibility from the actor, injected into the agent's constructor.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.11 — Tool Error Handling

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Decide what happens when a tool throws, and use the model's own recovery ability instead of crashing.

### The default

`ToolNode` accepts an `$errorHandler` argument. **By default it re-raises execution errors.** Your tool throws, and the exception propagates up through `chat()` into your application.

That is a reasonable default — silent failure would be worse — but it is rarely what you want in production. One transient timeout on one tool call, and a conversation that was going fine dies.

### The alternative: tell the model

This is the idea worth the whole lesson. Instead of crashing, hand the error back to the model as the tool's result.

**If the handler returns a value, that value is returned to the model as the result of the tool.**

The model then decides what to do: retry with different arguments, try a different tool, or tell the user the data is unavailable. You get graceful degradation without writing recovery logic, because the recovery logic is the model.

### Fluent definition

```php
$agent = Agent::make()
    ->toolErrorHandler(
        fn (Throwable $e, ToolInterface $tool): string => "Error: {$e->getMessage()}"
    );
```

### Inside the agent class

```php
class MyAgent extends Agent
{
    protected function resolveToolErrorHandler(): ?callable
    {
        return fn (Throwable $e, ToolInterface $tool): string => "Error: {$e->getMessage()}";
    }
}
```

The callback receives the exception and the failing tool instance. Both matter — the tool instance lets you branch on which tool failed.

### Writing a good handler

The naive version leaks internals into the conversation. A 500-character stack trace becomes context the model must reason about, and possibly text a user sees.

Write handlers that tell the model something *actionable*:

```php
protected function resolveToolErrorHandler(): ?callable
{
    return function (\Throwable $e, ToolInterface $tool): string {
        $this->logger->error('Tool failure', [
            'tool'      => $tool->getName(),
            'exception' => $e::class,
            'message'   => $e->getMessage(),
        ]);

        return match (true) {
            $e instanceof ConnectException =>
                "The {$tool->getName()} service is temporarily unreachable. "
                . "Do not retry more than once. If it fails again, tell the user "
                . "the data is unavailable right now.",

            $e instanceof NotFoundException =>
                "No record matched those arguments. Check the values with the user "
                . "before trying again.",

            $e instanceof \InvalidArgumentException =>
                "Invalid arguments: {$e->getMessage()}. Correct them and retry once.",

            default =>
                "The {$tool->getName()} tool failed. Tell the user you could not "
                . "complete this step, and do not retry.",
        };
    };
}
```

Three principles visible in that code:

**Log fully, tell the model briefly.** Your logs get the stack trace. The model gets one sentence.

**Include the instruction, not just the fact.** "Do not retry more than once" is doing real work. Without it, a transient failure can burn through the max-runs limit from Lesson 5.9 in seconds.

**Never leak internals into the conversation.** Connection strings, file paths, internal hostnames, credentials in exception messages — all of these end up in the transcript, which may be stored, logged and shown to the user.

### The interaction with max runs

The error handler catches `ToolRunsExceededException` too. That gives you a graceful exit at the limit rather than an exception at the boundary:

```php
$e instanceof ToolRunsExceededException =>
    "You have used this tool too many times. Stop calling it and answer with "
    . "what you already know, or tell the user you cannot complete the task.",
```

The model receives a clear stop signal and writes a sensible final message. Far better than a 500.

*Verification list item 1 applies here too — confirm the exception class name before writing this branch.*

### When to let it crash

Not everything should be handled. Let it propagate when:

- The failure indicates a bug you need to see in your error tracker
- The failure is a permission violation — do not let the model reason about that, fail hard and audit it
- The failure would leave data in an inconsistent state

"Return the error to the model" is a resilience pattern for expected, recoverable failures. It is not a substitute for correctness.

### Key takeaways

- Default behaviour is to re-raise; configure a handler for production.
- A returned value becomes the tool result the model sees.
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

**Support is limited to `OpenAIResponses`, `Gemini` and `Anthropic`.**

> Verification item 6: the documentation shows `ProviderTool:make()` with a single colon. It is a typo for `::`.

### The trade-off, stated as the docs state it

The official documentation is refreshingly blunt: provider tools introduce a lot of constraints, and the most flexible and reliable way to add capabilities to your agents remains the Tools and Toolkits system.

That is the framework authors telling you their own feature is the second choice. Take them at their word, and explain why to students:

**You lose portability.** This is the big one. Lesson 3.6 sold provider swapping as the framework's central benefit. A provider tool anchors you: switch from OpenAI to Ollama and that capability silently vanishes. The whole cost-tiering and vendor-risk argument evaporates for any agent that depends on one.

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

Use `TavilyToolkit` or `JinaToolkit` for web search. Both are portable, both work with any provider, both are testable, both let you see and cache what came back.

Reach for a provider tool when you have a specific reason, and write the reason down.

### Key takeaways

- Provider tools run server-side; supported on OpenAIResponses, Gemini and Anthropic only.
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

**It requires the `pcntl` extension, and `pcntl` only works in CLI processes, not in a web context.**

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

The design here is thoughtful and worth praising in the video: if `pcntl` is not present — a Windows development machine, for instance — the implementation **automatically falls back to sequential execution**. No configuration, no environment detection in your code, no crash.

You develop locally without `pcntl` and deploy to production where it is enabled, without changing a line. The agent adapts to whatever environment it finds itself in.

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

**Database connections need care.** A PDO connection inherited across a fork is a classic source of strange, intermittent failures. If your tools hit the database, open the connection inside the tool rather than sharing one across forks.

### Key takeaways

- `parallelToolCalls(true)` swaps `ToolNode` for `ParallelToolNode`.
- Requires `spatie/fork` and `pcntl`; **CLI only**, never in a web request.
- Falls back to sequential automatically when unavailable.
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

use GuzzleHttp\Client;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class WeatherTool extends Tool
{
    protected Client $client;

    public function __construct()
    {
        parent::__construct(
            'get_current_weather',
            'Returns current weather conditions for a geographic location: temperature '
            . 'in Celsius, wind speed in km/h, and a numeric weather code. Use this '
            . 'whenever the user asks about current weather, temperature, or conditions '
            . 'anywhere in the world. You must derive latitude and longitude yourself '
            . 'from the place name. Never invent weather data — always call this tool.'
        );
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

    public function __invoke(float $latitude, float $longitude): string
    {
        $body = $this->getClient()->get('forecast', [
            'query' => [
                'latitude'  => $latitude,
                'longitude' => $longitude,
                'current'   => 'temperature_2m,wind_speed_10m,weather_code',
            ],
        ])->getBody()->getContents();

        $data = \json_decode($body, true, 512, JSON_THROW_ON_ERROR);

        if (!isset($data['current'])) {
            throw new \RuntimeException('No current weather data in the API response.');
        }

        return \json_encode($data['current'], JSON_THROW_ON_ERROR);
    }

    protected function getClient(): Client
    {
        return $this->client ??= new Client([
            'base_uri' => 'https://api.open-meteo.com/v1/',
            'timeout'  => 10,
        ]);
    }
}
```

Open-Meteo needs no API key, so the whole lab runs free — combined with Ollama, students complete it with no account anywhere.

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
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\Calculator\DivideTool;
use NeuronAI\Tools\Toolkits\Calculator\MeanTool;
use NeuronAI\Tools\Toolkits\Calculator\SumTool;
use NeuronAI\Tools\ToolInterface;

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
                SumTool::class,
                DivideTool::class,
                MeanTool::class,
            ]),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return function (\Throwable $e, ToolInterface $tool): string {
            \error_log("[tool:{$tool->getName()}] {$e::class}: {$e->getMessage()}");

            return "The {$tool->getName()} tool failed: {$e->getMessage()}. "
                 . "Do not retry more than once. If it fails again, tell the user "
                 . "the data is unavailable.";
        };
    }
}
```

Note what this class demonstrates from the module: a class-based tool (5.3), a four-part description (5.4), examples in property descriptions (5.4), `only()` as an allowlist (5.8), a per-tool run cap (5.9), and a real error handler (5.11).

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
        ->toolMaxRuns(6)
        ->chat(new UserMessage($prompt))
        ->getMessage()
        ->getContent() . PHP_EOL;

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

Run it with `INSPECTOR_INGESTION_KEY` set and open the trace. Students see the actual sequence: two weather calls, one mean call, one final text response. That picture is what Lesson 1.2's table described in the abstract, and seeing it makes the cost arithmetic of Lesson 1.4 concrete.

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
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSchemaTool;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSelectTool;
use NeuronAI\Tools\ToolInterface;

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

            CalculatorToolkit::make(),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return fn (\Throwable $e, ToolInterface $tool): string =>
            "Query failed: {$e->getMessage()}. Check the schema and correct the SQL. "
            . "Do not retry more than twice.";
    }
}
```

### The runner

**`examples/05-data-analyst.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\DataAnalystAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'How many orders did we receive today?';

echo (new DataAnalystAgent())
    ->chat(new UserMessage($question))
    ->getMessage()
    ->getContent() . PHP_EOL;
```

```bash
php examples/05-data-analyst.php "How many orders did we receive today?"
php examples/05-data-analyst.php "What's the average order value this month, by country?"
php examples/05-data-analyst.php "Which three products have the highest revenue?"
```

### Four defence layers, and the demonstration

Count them out on screen:

1. **`MySQLWriteTool` is not attached.** The agent has no way to write.
2. **Schema is scoped to three tables.** The agent cannot see `payments` or `users`.
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
