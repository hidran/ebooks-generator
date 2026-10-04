# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Module 5, Lessons 5.1 to 5.7

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^4.0.3, PHP 8.5.
> **Module 5 is the longest and most important module in the course.** Lessons 5.8–5.13 follow in the next batch.

---
═══════════════════════════════════════════════════════════════
# MODULE 5 — TOOLS: GIVING THE AGENT HANDS
═══════════════════════════════════════════════════════════════
---

## LESSON 5.1 — What a Tool Actually Is

**Duration:** 13 minutes
**Type:** Theory

### Learning objectives

Understand precisely what happens when an agent "uses a tool", and why this is the single feature that separates an agent from a chatbot.

### The one-sentence definition

A tool is a function in your codebase that the model can ask you to run.

Read that again, because every word is load-bearing. It is **your** function. In **your** codebase. The model **asks**. You **run** it.

### The mechanism, restated

Lesson 1.2 introduced the loop. Here is what a tool contributes to it.

You describe your functions to the model as structured metadata: a name, a description, and a parameter schema. The model receives that alongside the conversation. When it decides a function would help, it does not produce prose — it produces a structured request:

```
I would like to call get_transcription with {"video_url": "https://..."}
```

Neuron intercepts that request, finds the matching tool object, invokes it with those arguments, takes the return value, appends it to the conversation as a tool-result message, and calls the model again. The model now has the transcript in context and can write the summary.

The framework automates every part of that except the function body. That is genuinely the whole abstraction, and Neuron's documentation describes it exactly this way: the core loop is calling a model, letting it choose tools to execute, and finishing when no more tools are needed.

### Why this is the security model, not just the execution model

The model has no capabilities of its own. It cannot open a socket, read a file, or issue a query. Its entire power is the set of tools you registered.

This has a liberating consequence and an obligation.

**The liberating consequence:** you cannot be exploited into an action you never implemented. There is no tool for `DELETE FROM users`, so no prompt — however cleverly constructed — produces one.

**The obligation:** everything you *do* register is reachable by anyone who can talk to the agent. If you register a tool that runs arbitrary SQL, a user who convinces the model to run destructive SQL has succeeded, and no amount of instruction text in your system prompt reliably prevents it.

The security boundary is the tool list, and it is the only boundary you can trust. Lesson 5.10 and Module 19 build on this.

### What makes a good tool

**Narrow.** `get_order_status(order_id)` beats `manage_order(action, params)`. A narrow tool is easier for the model to choose correctly and easier for you to authorise.

**Deterministic.** Same arguments, same result. The model is already non-deterministic; do not compound it.

**Compact in its return value.** Whatever you return is stringified into the conversation and re-sent on every subsequent iteration. Return the three fields the model needs, not the entire Eloquent model with fifty columns. This is Lesson 1.4's arithmetic reappearing in code.

**Honest in failure.** Returning "Order not found" is useful to the model. Returning an empty string leaves it guessing, and a guessing model hallucinates.

### The mental shift

Stop thinking of tools as an integration feature. They are the **capability surface of your agent** — an API design problem, where the consumer is a language model rather than another developer.

That framing explains why the rest of this module spends so much time on naming, descriptions and schemas. You are writing documentation for a consumer that reads only the documentation.

### Key takeaways

- A tool is your function; the model requests, your code executes.
- The registered tool list is the security boundary — the only one you can rely on.
- Good tools are narrow, deterministic, compact in output, and explicit about failure.
- Designing tools is API design for a reader who has only the docs.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.2 — Inline Tools

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Build a working tool with the fluent API and see the loop execute for the first time.

### The shape

`Tool` is an abstract class, so the lightest tool is an anonymous class that extends it, written in place inside `tools()`:

```php
new class extends Tool {
    protected string $name = 'name';
    protected ?string $description = 'description';

    protected function properties(): array { return [new ToolProperty(...)]; }

    public function __invoke(...): string { ... }
}
```

Three pieces: identity (the `$name` and `$description` properties), schema (`properties()`), implementation (`__invoke()`).

> **v3 form, for recognition only.** Older material builds the same tool with `Tool::make('name', 'description')->addProperty(new ToolProperty(...))->setCallable(fn (...) => ...)`. In v4 `Tool` is abstract and has no constructor, so `Tool::make()` fails with "Cannot instantiate abstract class", and `setCallable()` does not exist. Nothing below uses that form.

### The canonical example

This is the YouTube-summary agent from the official documentation, with its tool declared in place. It is worth knowing because students will meet this agent everywhere:

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class YouTubeAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(
            key: 'ANTHROPIC_API_KEY',
            model: 'ANTHROPIC_MODEL',
        );
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are an AI Agent specialized in writing YouTube video summaries.'],
            steps: [
                'Get the url of a YouTube video, or ask the user to provide one.',
                'Use the tools you have available to retrieve the transcription of the video.',
                'Write the summary.',
            ],
            output: [
                'Write a summary in a paragraph without using lists. Use just fluent text.',
                'After the summary add a list of three sentences as the three most important take away from the video.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            new class extends Tool {
                protected string $name = 'get_transcription';

                protected ?string $description = 'Retrieve the transcription of a youtube video.';

                protected function properties(): array
                {
                    return [
                        new ToolProperty(
                            name: 'video_url',
                            type: PropertyType::STRING,
                            description: 'The URL of the YouTube video.',
                            required: true,
                        ),
                    ];
                }

                public function __invoke(string $video_url): string
                {
                    return 'Video transcription...';
                }
            },
        ];
    }
}
```

### The rule students trip over

**The property name must match the `__invoke()` parameter name.**

The property is named `video_url`. The method signature is `__invoke(string $video_url)`. Not `$url`, not `$videoUrl`. Exactly `$video_url`.

Neuron passes the model's arguments to `__invoke()` as **named arguments**, keyed by property name. Rename one side and PHP throws `Error: Unknown named parameter $video_url` the first time the model calls the tool — an exception that aborts the run and looks, at first glance, like the model got something wrong, when in fact your wiring did.

Say this out loud in the video and put it on a slide. It is the single most common tool bug.

### A runnable version

Something students can actually execute, with no external API key:

**`examples/02-inline-tool.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\ToolDemoAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'Is the server under stress right now?';

echo ToolDemoAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage($question))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

This is the chain from Lesson 3.4: `setThreadId()` names the conversation the run belongs to, `chat()` returns the agent's final state, and `getMessage()` reads the model's latest message from it. Its return type is nullable, hence the `?->`.

**`src/Agents/ToolDemoAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolOutput;
use NeuronAI\Tools\ToolProperty;

class ToolDemoAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a system monitoring assistant.'],
            steps: ['Always read the real load values with your tools before answering.'],
            output: ['Answer in two sentences. Give the numbers you measured.'],
        );
    }

    protected function tools(): array
    {
        return [
            new class extends Tool {
                protected string $name = 'get_server_load';

                protected ?string $description = 'Returns the average CPU load of this server over a given time window. '
                    . 'Use this whenever asked about current server load, stress, or performance.';

                protected function properties(): array
                {
                    return [
                        new ToolProperty(
                            name: 'window',
                            type: PropertyType::STRING,
                            description: 'The time window to average over.',
                            required: true,
                            enum: ['1m', '5m', '15m'],
                        ),
                    ];
                }

                public function __invoke(string $window): string|ToolOutput
                {
                    $load = \sys_getloadavg();

                    if ($load === false) {
                        return ToolOutput::error('Load average is not available on this platform.');
                    }

                    $value = match ($window) {
                        '1m'  => $load[0],
                        '5m'  => $load[1],
                        '15m' => $load[2],
                        default => throw new \LogicException("Unexpected window \"{$window}\"."),
                    };

                    return \sprintf('Load average over %s: %.2f', $window, $value);
                }
            },
        ];
    }
}
```

```bash
php examples/02-inline-tool.php "How stressed is the server compared to fifteen minutes ago?"
```

That question forces two calls to the same tool with different arguments. It is a better demo than a single-call question, because students see the loop iterate.

Two failures are possible here, and they are handled in two different places. A window the model gets wrong never reaches `__invoke()`: the `enum:` goes into the schema the model reads, and Neuron enforces it when it binds the arguments. Ask for `"30m"` and the tool's result is `Parameter "window" must be one of "1m", "5m", "15m"; "30m" given.` — a sentence the model can act on, so the loop continues. That is why the `default` arm throws: no call that comes through the agent can reach it, so reaching it is a bug in your code, not a mistake the model made. The failure the tool can meet on its own — a platform with no load average — it *returns*, with `ToolOutput::error()`, and the model reads that too. Lesson 5.11 turns the distinction between returning and throwing into a rule.

### When inline is the right choice

**Use it for:** prototypes, one-off scripts, tools that genuinely have no reuse, teaching demos.

**Do not use it for:** anything that needs a dependency, anything you will test, anything that appears in more than one agent, anything longer than about ten lines.

An anonymous class does not capture variables from the surrounding scope: a dependency has to be passed in through a constructor you write for it, at which point the class has earned a name. It cannot be mocked or unit tested in isolation, because there is no class name to instantiate, and it cannot be reused. Lesson 5.3 fixes all four.

### Key takeaways

- `Tool` is abstract; the lightest tool is an anonymous class extending it inside `tools()`.
- Identity is the `$name` and `$description` properties; the schema is `properties()`; the logic is `__invoke()`.
- Property names must exactly match the `__invoke()` parameter names — the arguments are passed by name.
- Inline tools are for prototypes; they cannot be injected, tested or reused.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.3 — Tools as Classes

**Duration:** 17 minutes
**Type:** Hands-on — the production pattern

### Learning objectives

Write the form of tool you will actually ship, with dependencies, testability and reuse.

### Generate the scaffolding

```bash
# Unix
vendor/bin/neuron make:tool App\\Neuron\\Tools\\GetTranscriptionTool

# Windows PowerShell
.\vendor\bin\neuron make:tool App\Neuron\Tools\GetTranscriptionTool
```

### The four parts of a tool class

```php
<?php

namespace App\Neuron\Tools;

use NeuronAI\HttpClient\Curl\CurlHttpClient;
use NeuronAI\HttpClient\HttpClientInterface;
use NeuronAI\HttpClient\HttpRequest;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class GetTranscriptionTool extends Tool
{
    private const ENDPOINT = 'https://api.supadata.ai/v1/youtube/transcript';

    protected string $name = 'get_transcription';

    protected ?string $description = 'Retrieve the transcription of a youtube video.';

    protected HttpClientInterface $client;

    public function __construct(protected string $key, ?HttpClientInterface $client = null)
    {
        $this->client = $client ?? new CurlHttpClient(timeout: 10.0);
    }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'video_url',
                type: PropertyType::STRING,
                description: 'The URL of the YouTube video.',
                required: true,
            ),
        ];
    }

    public function __invoke(string $video_url): string
    {
        $response = $this->client
            ->request(HttpRequest::get(
                self::ENDPOINT . '?url=' . \urlencode($video_url) . '&text=true',
                ['x-api-key' => $this->key],
            ))
            ->json();

        return (string) ($response['content'] ?? '');
    }
}
```

**1. Identity** — the `$name` and `$description` properties. They are class property defaults, not constructor arguments, so identity is fixed by the class and there is no parent constructor to call. (In v3 a tool declared its identity with `parent::__construct(name, description)`; in v4 `Tool` has no constructor and that call is an error.)

**2. The constructor** — belongs entirely to your dependencies. Here they are an API key and an HTTP client; in a real application they might be a repository, a PDO connection, a mailer.

**3. `properties()`** — the schema, same objects as the inline version.

**4. `__invoke()`** — the implementation. PHP's magic invoke method, so the tool object is callable. Parameter names must match the property names, exactly as in Lesson 5.2.

The second constructor argument is optional, and it is the seam that makes the class testable. Leave it out and the tool builds Neuron's own `CurlHttpClient` — the client every provider and toolkit in the framework defaults to, so the tool needs nothing beyond `ext-curl`: no Guzzle, no extra Composer package. Pass one and the tool uses yours, untouched: the request carries its full URL and its own header, so any `HttpClientInterface` will do. The explicit `timeout:` is deliberate as well — the client's default is five minutes, far longer than anyone should wait on one tool call.

### Attaching it

```php
protected function tools(): array
{
    return [
        GetTranscriptionTool::make('API_KEY'),
    ];
}
```

`::make()` forwards its arguments to the constructor. So a tool with dependencies still reads cleanly in the agent's tool list.

### Why this pattern earns its extra ceremony

**It takes dependencies.** A class receives a PDO connection, a repository, a mailer — through its constructor, from your DI container. And it can hold them without ceremony: because only `ToolCall` data ever travels in messages and persisted state, a tool object is never serialized, so a live connection or an HTTP client inside it works with every persistence backend. One thing to know about its lifetime: the instance you attach is a prototype, and the framework runs a fresh clone of it for every call. The clones share the services you injected; anything a call writes to the tool's own properties is gone with its clone.

**It is unit testable without an LLM.** This is the argument that matters most:

```php
public function test_it_returns_the_transcript(): void
{
    $client = $this->createStub(HttpClientInterface::class);
    $client->method('request')->willReturn(
        new HttpResponse(200, '{"content": "Welcome back to the channel."}')
    );

    $tool = new GetTranscriptionTool('fake-key', $client);

    $result = $tool('https://youtube.com/watch?v=xyz');

    $this->assertStringContainsString('Welcome back', $result);
}
```

(`HttpClientInterface` and `HttpResponse` live in `NeuronAI\HttpClient`.) The tool is a callable object. You invoke it directly, with no agent, no provider, no call to a model — and, because the test hands it a stubbed client, no call to the transcript service either. Given the non-determinism problem from Lesson 1.5, having a large part of your agentic system be ordinary testable PHP is a significant win — and the boundary between "testable" and "not testable" runs exactly along this class.

A direct call skips the binding step that Lesson 5.5 describes. To test that as well — the casts, the required arguments — drive the tool the way the framework does: `$tool->setInputs([...])->execute()`, then read `$tool->getResult()`.

**It is reusable and shippable.** Tools implement `ToolInterface`. A well-built tool can be published as a Composer package or contributed upstream to the framework. This is how the ecosystem grows, and it is a realistic path to visibility for a developer who wants one.

**It has a real name.** `GetTranscriptionTool` appears in stack traces, in your DI container, in your IDE's navigation. An anonymous class appears as `NeuronAI\Tools\Tool@anonymous`.

### The refactoring exercise to record

Take the `get_server_load` inline tool from Lesson 5.2 and convert it to a class. Then write a PHPUnit test for it. Five minutes of video, and it makes the testability argument far better than a slide can.

### Key takeaways

- `$name` / `$description` properties for identity, the constructor for dependencies only, `properties()` for schema, `__invoke()` for logic.
- `::make()` forwards constructor arguments.
- Class-based tools are injectable, testable without an LLM, reusable and shippable.
- The tool class is the boundary between deterministic PHP and non-deterministic AI — put as much logic as possible on the deterministic side.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.4 — Tool Descriptions Are Prompt Engineering

**Duration:** 16 minutes
**Type:** Theory with A/B demonstration

### Learning objectives

Write names and descriptions that produce correct tool selection, and recognise description quality as the primary cause of agent failure.

### The claim

When an agent misbehaves, the cause is usually not the model, the framework, or the system prompt. It is that a tool's description did not tell the model clearly enough when to use it.

The official documentation is unusually direct about this: the name and description of the tool and its properties are passed to the LLM in natural language, and the more explicit and clear you are, the more likely the LLM understands when, if, and why to use the tool.

### What the model sees

Not your code. Not your types. Not your class name. This, roughly:

```json
{
  "name": "get_transcription",
  "description": "Retrieve the transcription of a youtube video.",
  "parameters": {
    "video_url": {
      "type": "string",
      "description": "The URL of the YouTube video.",
      "required": true
    }
  }
}
```

That is the complete interface. Every selection decision the model makes is based on those strings.

### The four-part description formula

**1. What it does.** One clause. Concrete verb.

**2. When to use it.** The most valuable and most frequently omitted part. Give the trigger conditions in the user's language, not yours.

**3. What it returns.** Sets expectations so the model can plan a multi-step sequence.

**4. What not to do.** The guardrail. Especially "do not invent this data".

**Poor:**
```php
'get_weather',
'Gets the weather.'
```

**Good:**
```php
'get_current_weather',
'Returns current weather conditions for a location: temperature in Celsius, '
. 'wind speed, and a condition code. Use this whenever the user asks about '
. 'current weather, temperature, or conditions anywhere. Requires latitude '
. 'and longitude — derive them yourself from the place name. Never invent '
. 'weather data; always call this tool.'
```

Longer, and worth every token. It answers all four questions.

### Property descriptions matter as much

The parameter description is where you prevent malformed calls:

```php
new ToolProperty(
    name: 'latitude',
    type: PropertyType::NUMBER,
    description: 'Latitude in decimal degrees. Example: 45.0703 for Turin, Italy. '
               . 'Negative for southern hemisphere.',
    required: true,
)
```

The worked example is doing real work. Models pattern-match on examples far more reliably than on abstract type descriptions, and one example in a property description eliminates an entire class of format errors.

### Naming conventions

- `snake_case`, verb-first: `get_order_status`, `send_notification`, `search_documents`
- Specific over general: `search_orders_by_customer` beats `search`
- Consistent prefixes across your catalogue: `get_`, `list_`, `create_`, `send_`
- Never use internal jargon. `fetch_sku_metadata_v2` means nothing to the model — and internal version suffixes actively confuse it.

### The A/B demonstration to record

This is five minutes of video that changes how students write tools for the rest of their careers.

Build the same weather agent twice. Version A: `'get_weather'` / `'Gets the weather.'`. Version B: the four-part description above.

Ask both: *"Should I bring a jacket to Turin this afternoon?"*

Version A frequently answers from the model's general knowledge without calling the tool at all, because nothing in the description connected "should I bring a jacket" to "get the weather". Version B calls the tool, because the description explicitly listed the trigger conditions.

Then show the fix landing: same code, same model, one string changed, correct behaviour. **The description is the program.**

### Practical advice

- Write the description before the implementation. If you cannot describe when it should be used, the tool's scope is wrong.
- Treat descriptions as versioned code and review them.
- When an agent picks the wrong tool, read the two descriptions side by side. The ambiguity is almost always visible.
- Keep the boundary between two similar tools explicit. If you have `search_orders` and `search_products`, say in each description what the *other* one is for.

### Key takeaways

- Name, description and property descriptions are the model's entire interface.
- Four parts: what, when, returns, what-not-to-do.
- Examples inside property descriptions prevent format errors.
- Wrong tool selected → read the descriptions, not the code.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.5 — Property Types: Scalars, Arrays and Objects

**Duration:** 16 minutes
**Type:** Hands-on

### Learning objectives

Express any input shape your tool needs, using the three property classes and their constraints.

### ToolProperty — scalars

```php
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

protected function properties(): array
{
    return [
        new ToolProperty(
            name: 'arg',
            type: PropertyType::STRING,
            description: 'Describe the value you expect',
            required: true,
        ),
    ];
}
```

`PropertyType` is an enum with six cases: `STRING`, `INTEGER`, `NUMBER`, `BOOLEAN`, `ARRAY` and `OBJECT`. The first four are what you use with `ToolProperty`; arrays and objects have their own property classes, below. `ToolProperty` also takes an `enum:` array when a value may only be one of a few, as `get_server_load` did in Lesson 5.2: the list goes into the schema, and binding enforces it.

Two arguments worth distinguishing:

- **`required`** — must the model supply this property at all?
- **`nullable`** — may the supplied value be null?

They are not the same thing, and conflating them produces schemas that permit inputs you did not intend. A required-but-nullable property must be present and may be null; an optional property may be absent entirely.

### What reaches `__invoke()`: binding is casting

The type you declare is not only schema. Before `__invoke()` runs, Neuron passes every argument the model sent through its property's `cast()`, and your method receives the converted value.

This matters because models are loose with JSON types. Ask for a `NUMBER` and you will regularly receive `"45.07"` — a string. Ask for a `BOOLEAN` and you may get `"true"`. The cast converts what PHP's own coercive mode would convert: `"45.07"` becomes `45.07`, `"5"` becomes `5` for an `INTEGER`, `"true"` becomes `true`, and array elements go through the array's `items` property. So a plain `float $latitude` in your signature is safe; you do not need to widen it to `float|int|string` and cast by hand.

What cannot be converted never reaches your code. If the model sends `"north"` for a `NUMBER`, `__invoke()` is not called at all: the tool's result becomes an error the model can read — `Parameter "latitude" must be of type number, string given.` — and the loop continues, so the model can correct its own call. A required argument the model leaves out is settled the same way — `Parameter "latitude" is required.` — and so is a value outside a property's `enum:`. All three are the model's mistakes to fix, not bugs in your application: nothing is thrown, and the error handler of Lesson 5.11 is never involved. (In v3 these arrived unchecked and surfaced as a `TypeError` or `MissingCallbackParameter`.)

### ArrayProperty — lists

Use `items` to declare the element type:

```php
use NeuronAI\Tools\ArrayProperty;

new ArrayProperty(
    name: 'prop_array',
    description: 'Describe the value you expect',
    required: true,
    items: new ToolProperty(
        name: 'prop',
        type: PropertyType::STRING,
        description: 'Describe the value you expect',
        required: true,
    ),
)
```

And constrain the size with `minItems` / `maxItems`:

```php
$property = new ArrayProperty(
    name: 'tags',
    description: 'List of tags associated with the item',
    required: true,
    items: new ToolProperty(
        name: 'tag',
        type: PropertyType::STRING,
        description: 'A single tag',
        required: true,
    ),
    minItems: 1,
    maxItems: 10,
);
```

**Why the limits matter operationally.** Without `maxItems` a model asked to "tag this article thoroughly" may return sixty tags. Every one of them is tokens in the conversation, and if your tool then makes one API call per tag, sixty calls. `maxItems: 10` is a cost control and a rate-limit guard, not merely a validation rule.

Know where it is enforced, though. `minItems` and `maxItems` go into the JSON Schema the model receives, and models and providers generally respect them — but Neuron's binding casts the elements without counting them. If eleven items would do real damage, check `count()` in `__invoke()` and return `ToolOutput::error()` with a message the model can act on.

### ObjectProperty — nested structures

```php
use NeuronAI\Tools\ObjectProperty;

new ObjectProperty(
    name: 'colors',
    description: 'RGB color',
    required: true,
    properties: [
        new ToolProperty(
            name: 'r',
            type: PropertyType::NUMBER,
            description: 'The red part of the RGB',
            required: true,
        ),
        new ToolProperty(
            name: 'g',
            type: PropertyType::NUMBER,
            description: 'The green part of the RGB',
            required: true,
        ),
        new ToolProperty(
            name: 'b',
            type: PropertyType::NUMBER,
            description: 'The blue part of the RGB',
            required: true,
        ),
    ],
)
```

Properties nest arbitrarily: an array of objects, an object containing arrays, and so on.

### The design guidance that matters more than the syntax

You *can* express deeply nested structures. You mostly *should not*.

Every level of nesting is another chance for the model to produce a shape that does not validate, and complex schemas consume tokens on every single request in the loop — remember from Lesson 1.3 that the full tool schema is re-transmitted every iteration.

Three rules:

**Prefer flat.** Two scalar properties beat one object with two fields, unless the object is genuinely reused across tools.

**Prefer several narrow tools over one wide tool with a discriminated union.** A tool taking `{action: "create"|"update"|"delete", payload: {...}}` is harder for the model to call correctly than three separate tools. It is also impossible to authorise granularly — you cannot let a user delete but not create if both live behind one tool.

**Let the model do the conversion work.** Rather than accepting a free-text date and parsing it yourself, declare the property as an ISO 8601 string with an example in the description. Models are good at format conversion, and you get a validated shape at the boundary instead of a parsing problem inside your tool.

### Exercise

Write a `compare_cities` tool that takes an `ArrayProperty` of city names with `minItems: 2, maxItems: 5`, and returns a comparison. Then ask the agent to compare eight cities. Observe whether the model respects the constraint and how it reacts to being constrained. Then add a `count()` check in `__invoke()` that returns `ToolOutput::error()`, and see what the model does with the feedback.

### Key takeaways

- Three classes: `ToolProperty`, `ArrayProperty`, `ObjectProperty`.
- `required` and `nullable` are different questions.
- Binding is casting: `__invoke()` receives typed values, and an argument that is missing, outside its `enum:` or impossible to convert comes back to the model as an error instead of reaching your code.
- `minItems` / `maxItems` are cost and rate-limit controls, not just validation.
- Prefer flat schemas and several narrow tools over one wide tool.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.6 — Structured Tool Input

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Replace hand-written object schemas with annotated PHP classes, and receive typed objects in your tool.

### The problem

The RGB example from Lesson 5.5 needed three nested `ToolProperty` objects for three fields. A realistic object — an address, an order line, a search filter — has eight or twelve. Hand-writing that schema is verbose, and worse, the schema and the thing it describes drift apart over time.

### The solution

Pass a PHP class to `ObjectProperty` via the `class` argument. Neuron generates the schema from the class and hands your tool an **instance** of it.

**The DTO:**

```php
<?php

namespace App\Neuron\Dto;

use NeuronAI\StructuredOutput\SchemaProperty;

class Color
{
    #[SchemaProperty(description: "The RED part of the RGB", required: true)]
    public float $r;

    #[SchemaProperty(description: "The GREEN part of the RGB", required: true)]
    public float $g;

    #[SchemaProperty(description: "The BLUE part of the RGB", required: true)]
    public float $b;
}
```

**The tool:**

```php
<?php

namespace App\Neuron\Tools;

use App\Neuron\Dto\Color;
use NeuronAI\Tools\ObjectProperty;
use NeuronAI\Tools\Tool;

class MyTool extends Tool
{
    protected string $name = 'my_tool';

    protected ?string $description = 'Describe what the tool does and when to use it.';

    protected function properties(): array
    {
        return [
            new ObjectProperty(
                name: 'color',
                description: 'Combination of colors',
                required: true,
                class: Color::class,
            ),
        ];
    }

    public function __invoke(Color $color) { /* ... */ }
}
```

Note the signature: `__invoke(Color $color)`. Not an array. A typed object, with IDE completion, static analysis and refactoring support. This is the binding-is-casting rule from Lesson 5.5 applied to objects: the `ObjectProperty` deserializes the model's JSON into your class before the call.

### Why this is the pattern to teach as the default

**The schema and the type cannot drift.** Add a field to the DTO and the schema updates. There is no second place to remember to edit — which is the failure mode of hand-written schemas in a codebase with more than one contributor.

**Static analysis works again.** PHPStan or Psalm can see `$color->r`. With array-shaped input they see `mixed`, and your tool bodies become an analysis blind spot.

**The DTO is reusable.** The same annotated class works for structured *output* (Module 6). One `Order` class can define what the model must produce and what a tool accepts — the same contract in both directions.

**`#[SchemaProperty]` supports validation constraints.** Beyond `title`, `description` and `required`, the attribute accepts `min` and `max`, `minLength` and `maxLength`, and `anyOf`. Push validation into the schema so the model receives the rules rather than your tool discovering violations at runtime.

### Note on the namespace

`SchemaProperty` lives under `NeuronAI\StructuredOutput\`, not under `NeuronAI\Tools\`. That is not an accident — it is the same mechanism the structured-output system uses, which is exactly why the DTO is reusable across both. Worth mentioning, because the import location surprises people. The documentation sometimes writes it as `NeuronAI\StructuredOutput\Property`, which does not exist.

### Exercise

Rewrite the `WeatherTool` from the Module 5 lab to take a `Coordinates` DTO with `latitude` and `longitude` annotated with `#[SchemaProperty]`. Compare the two versions side by side on screen.

### Key takeaways

- `ObjectProperty(class: MyDto::class)` generates the schema from an annotated PHP class.
- `__invoke()` receives a typed instance, not an array.
- Schema and type cannot drift; static analysis keeps working.
- The same DTO serves structured input and structured output.

---
═══════════════════════════════════════════════════════════════

## LESSON 5.7 — Toolkits

**Duration:** 15 minutes
**Type:** Hands-on

### Learning objectives

Attach whole capability sets in one line, and understand the `guidelines()` mechanism that makes a toolkit more than a list.

### The problem toolkits solve

An agent that needs maths needs more than one tool: something to evaluate a formula, exact integer arithmetic for factorials, combinations and primes, and statistics — mean, median, mode, variance, standard deviation. Declaring fourteen tools individually in every agent is noise.

### Attaching one

```php
<?php

namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            CalculatorToolkit::make(),
        ];
    }
}
```

One line, fourteen tools.

### What a toolkit is made of

```php
namespace NeuronAI\Tools\Toolkits\Calculator;

use NeuronAI\Tools\Toolkits\AbstractToolkit;

class CalculatorToolkit extends AbstractToolkit
{
    public function guidelines(): ?string
    {
        return <<<TEXT
            This toolkit performs mathematical calculations with precision and determinism.
            For arithmetic, algebra, trigonometry, logarithms or any formula, write the whole expression
            and pass it to the evaluate tool in a single call instead of computing intermediate steps
            yourself; it works in double precision, about 15 significant digits. Use the integer tools
            (factorial, combinations, permutations, gcd, lcm, mod_pow, is_prime, prime_factors) when an
            exact result with large integers is required, and the statistics tools for datasets.
            TEXT;
    }

    public function provide(): array
    {
        return [
            EvaluateTool::make(),
            FactorialTool::make(),
            CombinationsTool::make(),
            PermutationsTool::make(),
            GcdTool::make(),
            LcmTool::make(),
            ModPowTool::make(),
            IsPrimeTool::make(),
            PrimeFactorsTool::make(),
            MeanTool::make(),
            MedianTool::make(),
            ModeTool::make(),
            VarianceTool::make(),
            StandardDeviationTool::make(),
        ];
    }
}
```

Two methods on `AbstractToolkit`.

**`provide()`** returns the tools. Once attached, they behave exactly as if declared individually.

**`guidelines()` is the interesting one.** It gives the model contextual information about how the tools work *together*, which no individual tool description can convey. Neuron appends each attached toolkit's guidelines to the system prompt, inside a `<TOOLS-GUIDELINES>` block, under a heading that lists the names of that toolkit's tools.

Look at what the calculator's guidelines actually say: write the whole expression and pass it to `evaluate` in a single call, instead of computing intermediate steps yourself. That single sentence changes behaviour. Language models are unreliable at arithmetic, and they are just as unreliable at copying a long intermediate result from one tool call into the next. Without the guideline, a model faced with a multi-part calculation either attempts it in its head or chains a dozen small calls, transcribing floats between them. With it, the model writes `(19.3 + 18.6) / 2` once and a deterministic parser computes it.

**That is the lesson to draw out:** an individual tool description says *what this tool does*. Guidelines say *how to combine these tools into a strategy*. If you build your own toolkit, the guidelines are where the strategy goes, and skipping them wastes most of the mechanism.

> **The calculator needs bcmath.** The exact integer tools compute with the `bcmath` extension and refuse to be constructed without it. Because `provide()` instantiates every tool, `CalculatorToolkit::make()` fails at agent boot on a PHP build without `ext-bcmath` — even if you only wanted `evaluate`. Enable the extension everywhere the agent runs, or attach `EvaluateTool::make()` and the statistics tools individually.

### The built-in catalogue

| Toolkit | Capability | Needs |
|---|---|---|
| **Calculator** | 14 tools: expression evaluation, exact integer maths (factorial, combinations, gcd, primes…), mean, median, mode, variance, standard deviation | `ext-bcmath` |
| **Calendar** | 18 tools: current time, formatting, differences, timezone conversion, weekday, leap year, periods | — |
| **MySQL / PGSQL** | Schema introspection, SELECT, write operations | PDO |
| **FileSystem** | read, grep, glob, parse — and write, edit, delete, and a bash shell | optional scope directory |
| **Tavily** | web search, page extraction, site crawl | API key |
| **Jina** | web search, URL reader | API key |
| **TodoPlanning** | one tool, `write_todos`: a task list the model keeps and updates while it works through a multi-step job | — |

Three more ship with 4.0.3 marked `@deprecated`, to be removed in the next major version: the Supadata YouTube toolkit, the Zep long-term memory toolkit, and `SESTool`, a single tool for sending email through AWS SES. Do not build on them.

Read the FileSystem row twice. The toolkit is not read-only: attached whole, it hands the model the ability to overwrite, delete and run shell commands. Its optional scope directory (`FileSystemToolkit::make('/path/to/docs')`) confines the file tools to one tree, but the shell is only started there, not confined by it. Lesson 5.8 shows how to keep only the tools you mean to offer.

### The database toolkits deserve special attention

`MySQLToolkit` gives an agent genuine access to your data. Ask "how many orders did we receive today?" and it introspects the schema, writes a query and returns the real number — no hallucination.

```php
use NeuronAI\Tools\Toolkits\MySQL\MySQLToolkit;

protected function tools(): array
{
    return [
        MySQLToolkit::make(
            new \PDO("mysql:host=localhost;dbname=DB_NAME;charset=utf8mb4", "DB_USER", "DB_PASS"),
        ),
    ];
}
```

The toolkit splits into separate tools by capability, and **the split is the security control**:

- `MySQLSchemaTool` — reads structure
- `MySQLSelectTool` — reads data: one statement per call, run inside a `READ ONLY` transaction that the tool always rolls back
- `MySQLWriteTool` — INSERT, UPDATE, DELETE

The documentation's own advice is worth quoting in the video: if you are not confident about your agent's behaviour, you may simply not provide the writing tool. Attaching read tools only is a complete, effective mitigation — not a compromise.

Second control: `MySQLSchemaTool` takes an optional list of tables.

```php
MySQLSchemaTool::make(
    new \PDO($dsn, $user, $password),
    ['users', 'categories', 'articles', 'tags']
)
```

This limits what the model is shown, not what the connection can read. A content agent is told about articles, categories and tags; a user-administration agent about users, roles and permissions; neither is told that a payments table exists. But a table the model was never shown is still a table it can name in a query, so treat the list as a way to keep the agent focused and its schema output short, not as access control.

Third control, and the one to emphasise most: **the PDO instance is a connection, so give the agent its own, with its own database credentials.** A read-only MySQL user costs one `GRANT` statement and enforces at the database layer what your tool selection enforces at the application layer. Defence in depth, and the only layer a prompt cannot argue with. A connection of its own matters too: the select tool refuses to run on one that is already inside a transaction, because its rollback would discard your application's work.

### Key takeaways

- A toolkit attaches a coherent capability set in one line.
- `guidelines()` conveys cross-tool strategy — the part that changes behaviour.
- Database toolkits split read from write on purpose; omitting the write tool is a valid design.
- A table list on the schema tool narrows what the model is shown, not what it can read; the agent's own read-only credentials are the access control.

---
═══════════════════════════════════════════════════════════════

## PRE-RECORDING VERIFICATION LIST — MODULE 5

The Tools documentation is the densest page in the project and contains several internal inconsistencies. Each one below has been checked against neuron-ai 4.0.3 and resolved in this script, so you teach the real API rather than the documented one. Re-check any signature you are unsure of against `vendor/neuron-core/neuron-ai` before recording.

| # | Issue | Resolution on 4.0.3 |
|---|---|---|
| 1 | **`ToolRunsExceededException` vs `ToolMaxTriesException`** — the prose names the first, the example `catch` block names the second | Only `NeuronAI\Exceptions\ToolRunsExceededException` exists |
| 2 | **`setMaxRuns()` vs `setMaxTries()`** — the Max Runs section uses the first, the `with()` filter example uses the second | `setMaxRuns()` on a tool, `toolMaxRuns()` on the agent; `setMaxTries()` is gone |
| 3 | **`ExponentiateTool` vs `ExponentialTool`** | Neither exists: the calculator was rewritten around `EvaluateTool` |
| 4 | **`Toolkits\CalendarToolkit\CalendarToolkit` vs `Toolkits\Calendar\...`** | `NeuronAI\Tools\Toolkits\Calendar\CalendarToolkit` |
| 5 | **`NeuronAI\Tools\Calculator\CalculatorToolkit` vs `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit`** | The second |
| 6 | **`ProviderTool:make()`** — single colon, a typo for `::` | `::` |
| 7 | **`new SesCleint(...)`** — misspelling of `SesClient` | The tool that page documents, `SESTool`, is deprecated and goes in the next major version: do not build on it |
| 8 | **`instructions()` visibility** — `public` in some examples, `protected` in others | `protected`, returning `SystemMessage\|string`; a plain `string` return is legal |
| 9 | **`use NeuronAI\Agent;` vs `use NeuronAI\Agent\Agent;`** — v2 imports survive in several toolkit examples | `NeuronAI\Agent\Agent` |
| 10 | **`setCallable()` / `Tool::make($name, $description)`** — still in v3 material | Removed: `Tool` is abstract; identity is `$name`/`$description`, logic is `__invoke()` |
| 11 | **`approvalPolicy(array $inputs)`** and **`toolErrorHandler` typed `ToolInterface $tool`** (Lessons 5.10, 5.11) | `approvalPolicy()` takes no parameters; the handler's second argument is a `ToolCall` |

None of these are framework bugs; they are documentation drift across versions. But every one of them will produce a fatal error for a student who copies the page, so resolving them in your material is a real value-add over the official docs — and worth mentioning on camera as a reason to trust the course.

---

**END OF LESSONS 5.1–5.7**

*Next: Lessons 5.8–5.13 — toolkit filters, max runs, visibility, error handling, provider tools, parallel execution. Then the Module 5 labs.*
