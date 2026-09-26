# Chapter 5 — Tools: Giving the Agent Hands

This is the longest chapter in the book, and the most important. Tools are the single feature that separates an agent from a chatbot, and tool design is where agents actually fail.

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch05`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch05), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

## 5.1 What a Tool Actually Is

### The one-sentence definition

A tool is a function in your codebase that the model can ask you to run.

Read that again, because every word is load-bearing. It is **your** function. In **your** codebase. The model **asks**. You **run** it.

### The mechanism, restated

Section 1.2 introduced the loop. Here is what a tool contributes to it.

You describe your functions to the model as structured metadata: a name, a description, and a parameter schema. The model receives that alongside the conversation. When it decides a function would help, it does not produce prose — it produces a structured request:

```
I would like to call get_transcription with {"video_url": "https://..."}
```

NeuronAI intercepts that request, finds the matching tool object, invokes it with those arguments, takes the return value, appends it to the conversation as a tool-result message, and calls the model again. The model now has the transcript in context and can write the summary.

Notice that two different things are involved, and NeuronAI keeps them apart. The **tool** is capability: a PHP object with a schema, an `__invoke()` method and whatever dependencies it needs — a PDO connection, an HTTP client. It lives on the agent and never leaves your process. The **tool call** is data: a `ToolCall` value object recording one invocation — the tool's name, the call ID the model assigned, the arguments, and later the result. Messages, chat history, streaming chunks and persisted state carry `ToolCall` objects, never tools. At execution time the framework resolves each call by name against the agent's live tool list; a call naming a tool the agent does not offer fails loudly instead of running anything.

The framework automates every part of that except the function body. That is genuinely the whole abstraction, and NeuronAI's documentation describes it exactly this way: the core loop is calling a model, letting it choose tools to execute, and finishing when no more tools are needed.

### Why this is the security model, not just the execution model

The model has no capabilities of its own. It cannot open a socket, read a file, or issue a query. Its entire power is the set of tools you registered.

This has a liberating consequence and an obligation.

**The liberating consequence:** you cannot be exploited into an action you never implemented. There is no tool for `DELETE FROM users`, so no prompt — however cleverly constructed — produces one.

**The obligation:** everything you *do* register is reachable by anyone who can talk to the agent. If you register a tool that runs arbitrary SQL, a user who convinces the model to run destructive SQL has succeeded, and no amount of instruction text in your system prompt reliably prevents it.

The security boundary is the tool list, and it is the only boundary you can trust. Section 5.10 and Chapter 19 build on this.

### What makes a good tool

**Narrow.** `get_order_status(order_id)` beats `manage_order(action, params)`. A narrow tool is easier for the model to choose correctly and easier for you to authorise.

**Deterministic.** Same arguments, same result. The model is already non-deterministic; do not compound it.

**Compact in its return value.** Whatever you return is stringified into the conversation and re-sent on every subsequent iteration. Return the three fields the model needs, not the entire model object with fifty columns. This is Section 1.4's arithmetic reappearing in code.

**Honest in failure.** Returning "Order not found" is useful to the model. Returning an empty string leaves it guessing, and a guessing model hallucinates. NeuronAI gives you a dedicated shape for this — `ToolOutput::error()` — which Section 5.11 covers.

### The mental shift

Stop thinking of tools as an integration feature. They are the **capability surface of your agent** — an API design problem, where the consumer is a language model rather than another developer.

That framing explains why the rest of this chapter spends so much time on naming, descriptions and schemas. You are writing documentation for a consumer that reads only the documentation.

### Key takeaways

- A tool is your function; the model requests, your code executes.
- The tool is capability and stays on the agent; the `ToolCall` is data and travels in the conversation.
- The registered tool list is the security boundary — the only one you can rely on.
- Good tools are narrow, deterministic, compact in output, and explicit about failure.
- Designing tools is API design for a reader who has only the docs.

## 5.2 Inline Tools

### The shape

`Tool` is abstract: every tool is a class that extends it. When a tool is small and used in exactly one place, that class does not need a file or even a name — declare it as an anonymous class, right inside `tools()`:

```php
new class extends Tool {
    protected string $name = 'name';
    protected ?string $description = 'description';
    protected function properties(): array { return [new ToolProperty(...)]; }
    public function __invoke(...) { ... }
};
```

Three pieces: identity, schema, implementation. Identity is two class properties, `$name` and `$description`. The schema is what `properties()` returns. The implementation is `__invoke()`.

### The canonical example

This is the YouTube-summary agent from the official documentation, with its tool declared in place. It is worth knowing because you will meet this agent everywhere:

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

### The rule everyone trips over

**The property name must match the `__invoke()` parameter name.**

The property is named `video_url`. The method signature is `__invoke(string $video_url)`. Not `$url`, not `$videoUrl`. Exactly `$video_url`.

NeuronAI passes the model's arguments to `__invoke()` as **named arguments**, keyed by property name. Rename one side and PHP throws `Error: Unknown named parameter $video_url` the first time the model calls the tool — an exception that aborts the run and looks, at first glance, like the model got something wrong, when in fact your wiring did. It is the single most common tool bug.

### A runnable version

Something you can actually execute, with no external API key:

**`examples/02-inline-tool.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\ToolDemoAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'Is the server under stress right now?';

echo ToolDemoAgent::make()
    ->chat(new UserMessage($question))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

`chat()` returns the agent's final state, and `getMessage()` reads the assistant's reply from it. Its return type is nullable — a run that pauses before the model has produced any response has no message to read — hence the `?->`.

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
                            description: 'The time window. Allowed values: "1m", "5m", "15m".',
                            required: true,
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
                        default => null,
                    };

                    if ($value === null) {
                        return ToolOutput::error("Invalid window \"{$window}\". Use \"1m\", \"5m\" or \"15m\".");
                    }

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

That question forces two calls to the same tool with different arguments — a better first experiment than a single-call question, because you watch the loop iterate.

Note the two `ToolOutput::error()` returns. An invalid window is not a bug in your code; it is a mistake the model made and can correct. Returning it as an error result hands the model a sentence it can act on, and the loop continues. Throwing an exception instead would abort the whole run. Section 5.11 turns that distinction into a rule.

### When inline is the right choice

**Use it for:** prototypes, one-off scripts, tools that genuinely have no reuse, teaching demos.

**Do not use it for:** anything that needs a dependency, anything you will test, anything that appears in more than one agent, anything longer than about ten lines.

An anonymous class does not capture variables from the surrounding scope: a dependency has to be passed in through a constructor you write for it, at which point the class has earned a name. It cannot be mocked or unit tested in isolation, because there is no class name to instantiate, and it cannot be reused. Section 5.3 fixes all four.

### Key takeaways

- `Tool` is abstract; the lightest tool is an anonymous class extending it inside `tools()`.
- Identity is the `$name` and `$description` properties; the schema is `properties()`; the logic is `__invoke()`.
- Property names must exactly match the `__invoke()` parameter names — the arguments are passed by name.
- Inline tools are for prototypes; they cannot be injected, tested or reused.

## 5.3 Tools as Classes

This is the form you will actually ship.

### Generate the scaffolding

```bash
# Unix
vendor/bin/neuron make:tool App\\Neuron\\Tools\\GetTranscriptionTool

# Windows PowerShell
.\vendor\bin\neuron make:tool App\Neuron\Tools\GetTranscriptionTool
```

The generated class already has the four parts below, with placeholder values to replace.

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
    protected string $name = 'get_transcription';

    protected ?string $description = 'Retrieve the transcription of a youtube video.';

    protected HttpClientInterface $client;

    public function __construct(protected string $key)
    {
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
        $response = $this->getClient()
            ->request(HttpRequest::get('transcript?url=' . \urlencode($video_url) . '&text=true'))
            ->json();

        return (string) ($response['content'] ?? '');
    }

    protected function getClient(): HttpClientInterface
    {
        return $this->client ??= (new CurlHttpClient(customHeaders: ['x-api-key' => $this->key]))
            ->withBaseUri('https://api.supadata.ai/v1/youtube/');
    }
}
```

**1. Identity** — the `$name` and `$description` properties. They are class property defaults, not constructor arguments, so identity is fixed by the class and there is no parent constructor to call.

**2. The constructor** — belongs entirely to your dependencies. Here it is an API key; in a real application it might be a repository, a PDO connection, a mailer.

**3. `properties()`** — the schema, same objects as the inline version.

**4. `__invoke()`** — the implementation. PHP's magic invoke method, so the tool object is callable. Parameter names must match the property names, exactly as in Section 5.2.

Anything else the class needs — helpers like `getClient()` — stays private to the tool. The lazy `??=` client here is a small but good habit: no HTTP client is constructed unless the model actually calls the tool. And the client is NeuronAI's own `CurlHttpClient`, the same one the framework's built-in Supadata toolkit uses, so the tool needs nothing beyond `ext-curl` — no Guzzle, no extra Composer package.

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

**It takes dependencies.** A class receives a PDO connection, a repository, a mailer — through its constructor, from your DI container. And it can hold them without ceremony: because only `ToolCall` data ever travels in messages and persisted state, a tool object is never serialized, so a live connection or an HTTP client inside it works with every persistence backend.

**It is unit testable without an LLM.** This is the argument that matters most:

```php
public function test_it_returns_the_transcript(): void
{
    $tool = new GetTranscriptionTool('fake-key');

    $result = $tool('https://youtube.com/watch?v=xyz');

    $this->assertStringContainsString('expected phrase', $result);
}
```

The tool is a callable object. You invoke it directly, with no agent, no provider, no network call to a model. Given the non-determinism problem from Section 1.5, having a large part of your agentic system be ordinary testable PHP is a significant win — and the boundary between "testable" and "not testable" runs exactly along this class.

**It is reusable and shippable.** Tools implement `ToolInterface`. A well-built tool can be published as a Composer package or contributed upstream to the framework.

**It has a real name.** `GetTranscriptionTool` appears in stack traces, in your DI container, in your IDE's navigation. An anonymous class appears as `NeuronAI\Tools\Tool@anonymous`.

::: {.callout .callout-tip}
[In practice]{.callout-title}

Take the `get_server_load` inline tool from Section 5.2 and convert it to a class, then write a PHPUnit test for it. It takes five minutes, and it makes the testability argument far better than reading about it does.
:::

### Key takeaways

- `$name` / `$description` properties for identity, the constructor for dependencies only, `properties()` for schema, `__invoke()` for logic.
- `::make()` forwards constructor arguments.
- Class-based tools are injectable, testable without an LLM, reusable and shippable.
- The tool class is the boundary between deterministic PHP and non-deterministic AI — put as much logic as possible on the deterministic side.

## 5.4 Tool Descriptions Are Prompt Engineering

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
protected string $name = 'get_weather';

protected ?string $description = 'Gets the weather.';
```

**Good:**

```php
protected string $name = 'get_current_weather';

protected ?string $description = 'Returns current weather conditions for a location: temperature in Celsius, '
    . 'wind speed, and a condition code. Use this whenever the user asks about '
    . 'current weather, temperature, or conditions anywhere. Requires latitude '
    . 'and longitude — derive them yourself from the place name. Never invent '
    . 'weather data; always call this tool.';
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

### The experiment that changes how you write tools

Build the same weather agent twice. Version A: `'get_weather'` / `'Gets the weather.'`. Version B: the four-part description above.

Ask both: *"Should I bring a jacket to Turin this afternoon?"*

Version A frequently answers from the model's general knowledge without calling the tool at all, because nothing in the description connected "should I bring a jacket" to "get the weather". Version B calls the tool, because the description explicitly listed the trigger conditions.

Same code, same model, one string changed, correct behaviour. **The description is the program.**

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

## 5.5 Property Types: Scalars, Arrays and Objects

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

`PropertyType` is an enum with six cases: `STRING`, `INTEGER`, `NUMBER`, `BOOLEAN`, `ARRAY` and `OBJECT`. The first four are what you use with `ToolProperty`; arrays and objects have their own property classes, below. `ToolProperty` also takes an `enum:` array when a string may only be one of a few values.

Two arguments worth distinguishing:

- **`required`** — must the model supply this property at all?
- **`nullable`** — may the supplied value be null?

They are not the same thing, and conflating them produces schemas that permit inputs you did not intend. A required-but-nullable property must be present and may be null; an optional property may be absent entirely.

### What reaches `__invoke()`: binding is casting

The type you declare is not only schema. Before `__invoke()` runs, NeuronAI passes every argument the model sent through its property's `cast()`, and your method receives the converted value.

This matters because models are loose with JSON types. Ask for a `NUMBER` and you will regularly receive `"45.07"` — a string. Ask for a `BOOLEAN` and you may get `"true"`. The cast converts what PHP's own coercive mode would convert: `"45.07"` becomes `45.07`, `"5"` becomes `5` for an `INTEGER`, `"true"` becomes `true`, and array elements go through the array's `items` property. So a plain `float $latitude` in your signature is safe; you do not need to widen it to `float|int|string` and cast by hand.

What cannot be converted never reaches your code. If the model sends `"north"` for a `NUMBER`, `__invoke()` is not called at all: the tool's result becomes an error the model can read — `Parameter "latitude" must be of type number, string given.` — and the loop continues, so the model can correct its own call. A wrong type is the model's mistake to fix, not a bug in your application. A *missing* required argument is different, and still throws.

The same typed values feed everything else that judges the call — the approval policies of Section 5.10 and the run counting of Section 5.9 — so a policy that compares `amount > 100` cannot be sidestepped by the model spelling the number as a string.

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

Know where it is enforced, though. `minItems` and `maxItems` go into the JSON Schema the model receives, and models and providers generally respect them — but NeuronAI's binding casts the elements without counting them. If eleven items would do real damage, check `count()` in `__invoke()` and return an error the model can act on.

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

Every level of nesting is another chance for the model to produce a shape that does not validate, and complex schemas consume tokens on every single request in the loop — remember from Section 1.3 that the full tool schema is re-transmitted every iteration.

Three rules:

**Prefer flat.** Two scalar properties beat one object with two fields, unless the object is genuinely reused across tools.

**Prefer several narrow tools over one wide tool with a discriminated union.** A tool taking `{action: "create"|"update"|"delete", payload: {...}}` is harder for the model to call correctly than three separate tools. It is also impossible to authorise granularly — you cannot let a user delete but not create if both live behind one tool.

**Let the model do the conversion work.** Rather than accepting a free-text date and parsing it yourself, declare the property as an ISO 8601 string with an example in the description. Models are good at format conversion, and you get a validated shape at the boundary instead of a parsing problem inside your tool.

### Exercise

Write a `compare_cities` tool that takes an `ArrayProperty` of city names with `minItems: 2, maxItems: 5`, and returns a comparison. Then ask the agent to compare eight cities. Observe whether the model respects the constraint and how it reacts to being constrained. Then add a `count()` check in `__invoke()` that returns `ToolOutput::error()`, and see what the model does with the feedback.

### Key takeaways

- Three classes: `ToolProperty`, `ArrayProperty`, `ObjectProperty`.
- `required` and `nullable` are different questions.
- Binding is casting: `__invoke()` receives typed values, and an argument that cannot be converted comes back to the model as an error instead of reaching your code.
- `minItems` / `maxItems` are cost and rate-limit controls, not just validation.
- Prefer flat schemas and several narrow tools over one wide tool.

## 5.6 Structured Tool Input

### The problem

The RGB example from Section 5.5 needed three nested `ToolProperty` objects for three fields. A realistic object — an address, an order line, a search filter — has eight or twelve. Hand-writing that schema is verbose, and worse, the schema and the thing it describes drift apart over time.

### The solution

Pass a PHP class to `ObjectProperty` via the `class` argument. NeuronAI generates the schema from the class and hands your tool an **instance** of it.

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

Note the signature: `__invoke(Color $color)`. Not an array. A typed object, with IDE completion, static analysis and refactoring support. This is the binding-is-casting rule from Section 5.5 applied to objects: the `ObjectProperty` deserializes the model's JSON into your class before the call.

### Why this is the default worth adopting

**The schema and the type cannot drift.** Add a field to the DTO and the schema updates. There is no second place to remember to edit — which is the failure mode of hand-written schemas in a codebase with more than one contributor.

**Static analysis works again.** PHPStan or Psalm can see `$color->r`. With array-shaped input they see `mixed`, and your tool bodies become an analysis blind spot.

**The DTO is reusable.** The same annotated class works for structured *output* (Chapter 6). One `Order` class can define what the model must produce and what a tool accepts — the same contract in both directions.

**`#[SchemaProperty]` supports validation constraints.** Beyond `title`, `description` and `required`, the attribute accepts `min` and `max`, `minLength` and `maxLength`, and `anyOf`. Push validation into the schema so the model receives the rules rather than your tool discovering violations at runtime.

::: {.callout .callout-warning}
[Note on the namespace]{.callout-title}

`SchemaProperty` lives under `NeuronAI\StructuredOutput\`, not under `NeuronAI\Tools\`. That is not an accident — it is the same mechanism the structured-output system uses, which is exactly why the DTO is reusable across both. The documentation sometimes writes it as `NeuronAI\StructuredOutput\Property`, which does not exist; see item 12 in Appendix A.
:::

### Exercise

Rewrite the `WeatherTool` from Lab 3 to take a `Coordinates` DTO with `latitude` and `longitude` annotated with `#[SchemaProperty]`. Put the two versions side by side and decide which you would rather maintain with four contributors.

### Key takeaways

- `ObjectProperty(class: MyDto::class)` generates the schema from an annotated PHP class.
- `__invoke()` receives a typed instance, not an array.
- Schema and type cannot drift; static analysis keeps working.
- The same DTO serves structured input and structured output.

## 5.7 Toolkits

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

**`guidelines()` is the interesting one.** It gives the model contextual information about how the tools work *together*, which no individual tool description can convey. NeuronAI appends each attached toolkit's guidelines to the system prompt, followed by the names of its tools.

Look at what the calculator's guidelines actually say: write the whole expression and pass it to `evaluate` in a single call, instead of computing intermediate steps yourself. That single sentence changes behaviour. Language models are unreliable at arithmetic, and they are just as unreliable at copying a long intermediate result from one tool call into the next. Without the guideline, a model faced with a multi-part calculation either attempts it in its head or chains a dozen small calls, transcribing floats between them. With it, the model writes `(19.3 + 18.6) / 2` once and a deterministic parser computes it.

**That is the point worth drawing out:** an individual tool description says *what this tool does*. Guidelines say *how to combine these tools into a strategy*. If you build your own toolkit, the guidelines are where the strategy goes, and skipping them wastes most of the mechanism.

::: {.callout .callout-warning}
[The calculator needs bcmath]{.callout-title}

The exact integer tools compute with the `bcmath` extension and refuse to be constructed without it. Because `provide()` instantiates every tool, `CalculatorToolkit::make()` fails at agent boot on a PHP build without `ext-bcmath` — even if you only wanted `evaluate`. Enable the extension everywhere the agent runs, or attach `EvaluateTool::make()` and the statistics tools individually.
:::

### The built-in catalogue

| Toolkit | Capability | Needs |
|---|---|---|
| **Calculator** | 14 tools: expression evaluation, exact integer maths (factorial, combinations, gcd, primes…), mean, median, mode, variance, standard deviation | `ext-bcmath` |
| **Calendar** | 18 tools: current time, formatting, differences, timezone conversion, weekday, leap year, periods | — |
| **MySQL / PGSQL** | Schema introspection, SELECT, write operations | PDO |
| **FileSystem** | read, grep, glob, parse — and write, edit, delete, and a bash shell | optional scope directory |
| **Tavily** | web search, page extraction, site crawl | API key |
| **Jina** | web search, URL reader | API key |
| **Supadata YouTube** | video transcript, video metadata, channel, playlist | API key |
| **Zep** | long-term memory store and retrieve | API key |
| **AWS SES** | send email | `aws/aws-sdk-php` |

Read the FileSystem row twice. The toolkit is not read-only: attached whole, it hands the model the ability to overwrite, delete and run shell commands. Its optional scope directory (`FileSystemToolkit::make('/path/to/docs')`) confines the file tools to one tree, but the shell is only started there, not confined by it. Section 5.8 shows how to keep only the tools you mean to offer.

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
- `MySQLSelectTool` — reads data
- `MySQLWriteTool` — INSERT, UPDATE, DELETE

The documentation's own advice is worth quoting: if you are not confident about your agent's behaviour, you may simply not provide the writing tool. Attaching read tools only is a complete, effective mitigation — not a compromise.

Second control: `MySQLSchemaTool` takes an optional list of tables.

```php
MySQLSchemaTool::make(
    new \PDO(...),
    ['users', 'categories', 'articles', 'tags']
)
```

This limits what the agent can see, which limits what it can query. A content agent sees articles, categories and tags. A user-administration agent sees users, roles and permissions. Neither sees payments.

Third control, and the one to emphasise most: **the PDO instance is a connection, so give the agent its own database credentials.** A read-only MySQL user costs one `GRANT` statement and enforces at the database layer what your tool selection enforces at the application layer. Defence in depth, and the only layer a prompt cannot argue with.

### Key takeaways

- A toolkit attaches a coherent capability set in one line.
- `guidelines()` conveys cross-tool strategy — the part that changes behaviour.
- Database toolkits split read from write on purpose; omitting the write tool is a valid design.
- Limit schema scope by table, and give the agent its own read-only credentials.

## 5.8 Toolkit Filters: exclude, only, with

### Why filtering is not a nicety

A toolkit is a coherent set, but "coherent" is not the same as "appropriate for this agent". Three concrete costs of attaching more than you need:

**Tokens.** Every tool's name, description and parameter schema is transmitted on **every** iteration of the loop. The Calendar toolkit alone is eighteen tools. At five loop iterations you have paid for that schema five times.

**Wrong-tool errors.** Selection accuracy degrades as the catalogue grows. Fourteen maths tools where two would do means twelve extra chances to pick the wrong one.

**Blast radius.** Every attached tool is reachable by any user who can talk to the agent. That is Section 5.1's security model, applied to convenience imports.

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

`with()` is also where per-tool approval goes when the tool comes from a toolkit — `fn (ToolInterface $tool): ToolInterface => $tool->requireApproval()` on `MySQLWriteTool`, for instance. Section 5.10 covers approval.

::: {.callout .callout-warning}
[The method is setMaxRuns()]{.callout-title}

The `with()` example in the documentation calls `setMaxTries(1)`, and passes the toolkit no PDO connection. Neither works: there is no `setMaxTries()` — the tool-level setter is `setMaxRuns()` and the agent-level one is `toolMaxRuns()` — and `MySQLToolkit` requires its PDO. That is item 2 in Appendix A.
:::

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

## 5.9 Max Runs: Guarding the Loop

### The unbounded loop, revisited

Section 1.2 established that the agent loop is a `while` with no guaranteed exit. The model keeps requesting tools until it decides it is finished. If it never decides, the loop never ends.

This is not hypothetical. Three ways it happens in practice:

- The tool returns something the model misreads as failure, so it retries. Forever.
- The task is genuinely impossible with the tools available, and the model keeps trying alternatives.
- Two tools feed each other in a cycle — search returns a reference, fetch returns something needing another search.

Each iteration costs a model call and grows the context. Unbounded, this is a runaway bill.

### The guard

NeuronAI counts how many times each tool is invoked during an agent run — one `chat()` turn, including any pause for human approval in between. Exceed the limit and the tool node throws `ToolRunsExceededException`. **The default is 10 calls, counted per tool individually.**

That "per tool individually" detail matters. Five tools at the default limit means up to fifty tool executions in one `chat()` call before anything stops.

### Setting it

```php
use NeuronAI\Exceptions\ToolRunsExceededException;

try {
    $message = YouTubeAgent::make()
        ->toolMaxRuns(5) // Max number of calls for each tool
        ->addTool(
            // Tool level config takes precedence over the global setting
            CustomTool::make()->setMaxRuns(2)
        )
        ->chat(...)
        ->getMessage();

} catch (ToolRunsExceededException $exception) {
    // do something
}
```

Two levels:

- **`toolMaxRuns(n)`** on the agent — the default for every tool.
- **`setMaxRuns(n)`** on a tool — overrides the agent setting for that tool.

**Tool-level wins.** That precedence is what you want: a permissive global default with tight limits on the tools that are slow, expensive or dangerous.

::: {.callout .callout-warning}
[Catch the right exception class]{.callout-title}

The documentation has named the exception two ways: `ToolRunsExceededException` in its prose, `ToolMaxTriesException` in an example catch block. Only the first exists — `NeuronAI\Exceptions\ToolRunsExceededException`. That is item 1 in Appendix A, and it deserves the attention: PHP does not complain about a `catch` naming a class that does not exist, it simply never matches. A wrong class name produces silent non-handling rather than an obvious error, which is the worst kind of bug to inherit.
:::

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

That last row is the important one. A write tool with a limit of 1 means a retrying model cannot double-charge a customer. Set it deliberately.

### What an exceeded limit is telling you

This is the part people miss. An exceeded run limit is not usually a limit set too low. It is a **diagnostic**, and it almost always means one of three things:

1. **Your tool description is unclear**, so the model keeps trying variations. Go back to Section 5.4.
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

Section 5.11 covers a more sophisticated option: handing the error back to the model so it can recover on its own.

### Key takeaways

- Default is 10 runs, per tool, per agent run; exceeding it throws `ToolRunsExceededException`.
- `toolMaxRuns()` sets the agent default; `setMaxRuns()` on a tool overrides it.
- Runs are counted by run key — the tool name by default; `TrackByInputs` counts per set of arguments.
- Write tools should be capped at 1.
- An exceeded limit is a diagnostic about tool design, not a limit to raise.

## 5.10 Visibility: Conditional Tool Availability

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

**It is unreliable.** Instructions are followed probabilistically. Section 1.5 said assume non-determinism, and an access-control rule that works ninety-eight per cent of the time is not access control.

**It is attackable.** Instructions in the system prompt compete with instructions in the user's message. Prompt injection is a live technique; a schema that never included the tool is not vulnerable to it.

`visible(false)` removes the capability rather than forbidding its use. The model cannot request a tool it was never told about.

### Where visibility fits among the layers

Four independent mechanisms, and understanding what each one does is the point of this section:

| Layer | Mechanism | Enforced by |
|---|---|---|
| Not offered | `visible(false)` | Schema construction |
| Offered, gated at runtime | `approvalPolicy()`, `requireApproval()` | Human decision |
| Offered, checked on execution | Policy check inside `__invoke()` | Your PHP |
| Offered, restricted at source | Database grants, API scopes | Infrastructure |

Use several. `visible()` is your first line, not your only one — a bug in the visibility expression should not be the only thing between a user and a refund.

### Visibility vs approval

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

Small purchases go through; large ones wait for a human. That is a much better product than either always-allow or always-block. We build the full human-in-the-loop flow in Chapter 15 and wire it to a real UI in Chapter 22; the rest of this section covers what belongs to the tool and the agent, so the distinction lands while visibility is fresh.

### Approval lives on the tool

Before every tool call, the agent's tool node asks the tool one question: *does this call require approval?* The tool answers with the call's arguments already bound — and cast, as Section 5.5 described. There is no middleware to register and no agent-level switch; a tool that never asks for approval is never gated.

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

::: {.callout .callout-warning}
[approvalPolicy() takes no arguments]{.callout-title}

The documentation shows `approvalPolicy(array $inputs)`. The method takes no parameters: the inputs are already bound on the tool, so read them from `$this->inputs` or `$this->getInput('amount')`. Copying the documented signature is a fatal error — PHP rejects an override whose signature is incompatible with the parent's. Appendix A, item 45.
:::

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

`requireApproval()` gates every call. `suppressApproval()` waives a policy the tool declared — for an internal batch agent, say, where no human is available and the risk is managed elsewhere. `withApprovalPolicy()` replaces the declared policy with your own callback, which receives the tool with the call's inputs bound. If you configure more than one, the last override wins. Tools that come from a toolkit get the same treatment through `with()`, from Section 5.8.

### What the caller sees

When a gated call comes up, `chat()` does not throw and does not wait. It returns a state that is *interrupted*:

```php
$agent = ShopAgent::make(threadId: $threadId);

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

`pendingApprovals()` returns one `Action` per call still waiting for a decision — enough to render an approval screen. A decision comes back keyed by call ID, and `run()` continues the same run:

```php
$state = ShopAgent::make(threadId: $threadId)
    ->submitApprovalDecisions([
        'call_123' => 'approve',
        'call_456' => ['reject', 'Too expensive, ask the user for a cheaper option'],
    ])
    ->run();
```

Three rules make this safe. **A tool runs only if it is explicitly approved** — silence is never consent, and a payload that leaves a call undecided suspends the run again. **A rejection is not an error**: the model receives a tool result saying the action was not executed, together with your reason, and carries on with that knowledge. And **calls that needed no approval still run** — in the example, a cheap purchase requested in the same turn executes once the batch is decided.

Across two HTTP requests — the chat endpoint, then the approve endpoint — the agent needs the same thread ID, a workflow persistence backend and a durable chat history, so the second process can find the paused run. Chapter 15 sets that up.

### The pattern to adopt

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

Note that this requires `new OrderAgent($user)` rather than `::make()`, as established in Section 4.3.

### Exercise

Add a `delete_cache` tool to your demo agent, visible only when `APP_ROLE=admin`. Run the agent as a non-admin and ask it directly: "delete the cache". Then ask: "what tools do you have?" Verify the tool is absent from both the behaviour and the answer.

### Key takeaways

- `visible(false)` removes the tool from the schema entirely.
- Hiding beats instructing: prompt-based restrictions leak, are probabilistic, and are attackable.
- Visibility is build-time; approval is runtime. Both exist, for different jobs.
- Approval lives on the tool: `approvalPolicy()` declares it, `requireApproval()` / `suppressApproval()` / `withApprovalPolicy()` override it at attach time.
- A gated call returns an interrupted state; `pendingApprovals()` lists what to decide, `submitApprovalDecisions([...])->run()` continues. Only explicit approval runs a tool.
- Derive visibility from the actor, injected into the agent's constructor.

## 5.11 Tool Error Handling

### The default

A tool can end in two ways: it returns, or it throws. NeuronAI treats the two differently, on purpose, and the split falls on the natural boundary of the language.

**A return value is a conversational outcome.** Whatever `__invoke()` returns becomes the tool result the model sees, and the loop continues.

**An escaped exception is a bug.** It propagates up through `chat()` into your application and aborts the run. The conversation history stays consistent — the half-finished tool call is never committed — but the turn is over.

That is a reasonable default — silent failure would be worse — but it means the decision is yours, tool by tool: which failures are part of the conversation, and which are defects?

### The alternative: tell the model

This is the idea worth the whole section. A failure the model can do something about should not crash the run; it should be handed back to the model as the tool's result.

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

The error text becomes the result the model reads, flagged as a failure. Providers with a native error flag on tool results — Anthropic, Bedrock — receive it as such; the others receive the text. Catch your own exceptions at the tool boundary and convert the recoverable ones like this, visibly, in the code that knows what went wrong. NeuronAI's built-in tools follow the same convention: a division by zero in the calculator's `evaluate` returns `Division by zero at position 2` as an error result, not an exception. And as Section 5.5 showed, the framework already does this for you when the model sends an argument of the wrong type.

What remains are exceptions you did not anticipate — from a library, a driver, a network client deep in the call. For those there is an agent-level override: a **tool error handler**. It receives every exception that escapes a tool. **If the handler returns a value, that value is returned to the model as the result of the tool**, and the loop continues. If it returns `null`, it declines, and the exception propagates as before.

### Fluent definition

```php
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

The callback receives the exception and the failing call — the `ToolCall` from Section 5.1, with the tool's name and the arguments the model sent. Both matter — the call lets you branch on which tool failed. It may return a string, a `ToolOutput`, or `null`.

Type the second parameter as `ToolCall`. The documentation still types it `ToolInterface`, and a handler written that way fails with a `TypeError` at exactly the wrong moment — the first time a tool throws. Appendix A, item 46.

### Writing a good handler

The naive version leaks internals into the conversation. A 500-character stack trace becomes context the model must reason about, and possibly text a user sees.

Write handlers that tell the model something *actionable*:

```php
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

Four principles visible in that code:

**Log fully, tell the model briefly.** Your logs get the exception and the arguments. The model gets one sentence.

**Include the instruction, not just the fact.** "Do not retry more than once" is doing real work. Without it, a transient failure can burn through the max-runs limit from Section 5.9 in seconds.

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

The model receives a clear stop signal and writes a sensible final message. Far better than a 500.

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

## 5.12 Provider Tools

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

::: {.callout .callout-warning}
[Documentation typo]{.callout-title}

Older versions of the documentation show `ProviderTool:make()` with a single colon. It is a typo for `::`. Appendix A item 6.
:::

### The trade-off, stated as the docs state it

The official documentation is refreshingly blunt: provider tools introduce a lot of constraints, and the most flexible and reliable way to add capabilities to your agents remains the Tools and Toolkits system.

That is the framework authors telling you their own feature is the second choice. Take them at their word, and understand why:

**You lose portability.** This is the big one. Section 3.6 sold provider swapping as the framework's central benefit. A provider tool anchors you: switch from OpenAI to Ollama and the agent stops working, because the Ollama provider rejects the tool with an exception on the very first request. At least the failure is loud. But the whole cost-tiering and vendor-risk argument evaporates for any agent that depends on one.

**You lose control.** You cannot see the query, filter the sources, cache the result, rate-limit it, or log what was retrieved. For a regulated environment, "we don't know what it searched" is not an acceptable answer.

**You lose testability.** No fake, no stub, no offline CI. Section 5.3 made testability the argument for tool classes; provider tools give it back.

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

- Provider tools run server-side; supported on OpenAIResponses, Gemini, Anthropic and ZAI only — other providers throw.
- They cost you portability, control, testability and independence.
- The framework's own documentation recommends the portable Tools/Toolkits system.
- Good for prototypes and peripheral capabilities; bad for anything load-bearing.

## 5.13 Parallel Tool Calls

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

Under the hood, the framework injects a `ParallelToolNode` in place of the standard `ToolNode`. This is Section 2.3 becoming concrete: an agent is a workflow, and "enable parallel tools" means *swap one node for another*. It is the first time in this book that the workflow substrate is visibly doing something.

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

For a web application, the practical route is: push agent execution to a queue worker, which is a CLI process. That is where parallel tools apply — and it happens to be where you wanted long-running agent work anyway, for the latency reasons from Section 1.4. Chapter 22 builds this properly.

### Graceful degradation

The design here is thoughtful: if `pcntl` is not present — a Windows development machine, for instance — or `spatie/fork` is not installed, the implementation **automatically falls back to sequential execution**. It does the same when the model requested only one tool, which is not worth a fork. No configuration, no environment detection in your code, no crash.

You develop locally without `pcntl` and deploy to production where it is enabled, without changing a line. The agent adapts to whatever environment it finds itself in.

That is a good example of a framework absorbing environmental variation instead of pushing it onto the developer, and it is worth stealing as a design pattern rather than merely using as a feature.

### When it actually helps

Parallel execution only helps when the model requests **multiple tools in a single turn**. It does nothing for:

- Sequential dependencies — B needs A's output, so they cannot overlap
- Single-tool turns
- Fast local tools, where fork overhead exceeds the work

It helps most with several independent I/O-bound calls: three weather lookups, four API queries, five file reads. If your agent is not tool-hungry in this specific way, enabling it changes nothing.

### Cautions

**Forked processes do not share state.** Each fork is a separate process. Tools that mutate shared in-memory state, hold an open transaction, or assume a singleton will behave differently. Keep tools stateless and self-contained — which Section 5.1 recommended anyway, for other reasons.

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
- Requires `spatie/fork` and `pcntl`; **CLI only**, never in a web request.
- Falls back to sequential automatically when unavailable, and for single-call turns.
- `beforeChild` / `afterChild` hooks reset per-process resources such as database connections.
- Helps only with multiple independent I/O-bound calls in one turn.
- Keep tools stateless; be careful with database connections across forks.

## Lab 3 — Weather and Calculator Agent

**Covers:** custom tool class, toolkit, filters, max runs, error handling.

### Goal

An agent that answers *"What's the average current temperature between Turin and Milan?"* by calling a weather tool twice and a calculator tool once. Three round trips to the model — the clearest demonstration of the agent loop in the book.

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
    protected string $name = 'get_current_weather';

    protected ?string $description = 'Returns current weather conditions for a geographic location: temperature '
        . 'in Celsius, wind speed in km/h, and a numeric weather code. Use this '
        . 'whenever the user asks about current weather, temperature, or conditions '
        . 'anywhere in the world. You must derive latitude and longitude yourself '
        . 'from the place name. Never invent weather data — always call this tool.';

    protected HttpClientInterface $client;

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
        try {
            $data = $this->getClient()->request(HttpRequest::get('forecast?' . \http_build_query([
                'latitude'  => $latitude,
                'longitude' => $longitude,
                'current'   => 'temperature_2m,wind_speed_10m,weather_code',
            ])))->json();
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

    protected function getClient(): HttpClientInterface
    {
        return $this->client ??= (new CurlHttpClient(timeout: 10.0))
            ->withBaseUri('https://api.open-meteo.com/v1/');
    }
}
```

Open-Meteo needs no API key, so the whole lab runs free — combined with Ollama, you complete it without an account anywhere.

Three things in this class are worth a second look. The `float` parameters need no defensive widening, because binding casts the model's `"45.07"` to `45.07` before the call (Section 5.5). An unreachable service is *returned* as `ToolOutput::error()` rather than thrown, with an instruction attached (Section 5.11). And the HTTP client is the framework's own `CurlHttpClient`, so the lab adds no dependency.

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

Note what this one class demonstrates from the chapter: a class-based tool (5.3), a four-part description (5.4), examples in property descriptions (5.4), `only()` as an allowlist (5.8), a per-tool run cap (5.9), and a real error handler (5.11). Of the calculator's fourteen tools the agent keeps two: `evaluate` for any formula and `mean` for averages.

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

### Two things to observe

Run it with Inspector wired in, as Chapter 10 shows, and open the trace. You see the actual sequence: two weather calls, one calculator call — `mean`, or `evaluate` with the whole formula — and one final text response. That picture is what Section 1.2's table described in the abstract, and seeing it makes the cost arithmetic of Section 1.4 concrete.

Then break it deliberately: change the tool description to `'Gets the weather.'` and re-run. Frequently the model answers from general knowledge without calling the tool at all. Change it back. One string, completely different behaviour — Section 5.4's claim, demonstrated on your own machine.

## Lab 4 — Database Analyst Agent

**Covers:** MySQL toolkit, schema scoping, least privilege, read-only design.

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

**Do this first.** Everything else in this lab is application-layer control that a sufficiently clever prompt might get around. This grant is enforced by MySQL. It is the only layer that cannot be talked out of its position.

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

            CalculatorToolkit::make(),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return fn (\Throwable $e, ToolCall $call): ToolOutput => ToolOutput::error(
            "Query failed: {$e->getMessage()}. Check the schema and correct the SQL. "
            . "Do not retry more than twice."
        );
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
    ?->getContent() . PHP_EOL;
```

```bash
php examples/05-data-analyst.php "How many orders did we receive today?"
php examples/05-data-analyst.php "What's the average order value this month, by country?"
php examples/05-data-analyst.php "Which three products have the highest revenue?"
```

### Four defence layers

1. **`MySQLWriteTool` is not attached.** The agent has no way to write.
2. **Schema is scoped to three tables.** The agent cannot see `payments` or `users`.
3. **`MySQLSchemaTool` is capped at one run.** No repeated expensive introspection.
4. **The database user only holds SELECT on three tables.** Enforced by MySQL.

Then run the demonstration that makes the point:

```bash
php examples/05-data-analyst.php "Delete all orders from last year."
```

The agent explains it cannot. Not because the prompt told it not to — because **there is no tool that writes.** That distinction is the entire security lesson of this chapter, and it lands far better as something you run than as something you read.

## Chapter Exercises

1. **Design.** Take a feature from your own application and design three tools for it. Write the descriptions before the implementations. For each, answer the four questions from Section 5.4.

2. **Convert.** Take one inline tool and convert it to a class. Write a PHPUnit test that invokes it directly with no agent involved.

3. **Constrain.** Attach a toolkit with `only()`, set a per-tool run cap, and add an error handler that returns an instruction rather than a stack trace.

4. **Break it.** Deliberately write a vague tool description and observe the failure. Fix it with one string change. Record what changed in the model's behaviour.

5. **Secure.** For an agent with database access, list your defence layers and identify which one an attacker could not defeat with a prompt.

::: {.callout .callout-warning}
[Before you ship anything from this chapter]{.callout-title}

The Tools documentation is the densest page in the NeuronAI project, and it has disagreed with itself and with the code in exception names, method names, class names, namespaces, import paths and method signatures. Almost every one of them produces a fatal error for someone who copies the page. They are listed in Appendix A, starting at item 1, with probe scripts that settle all of them against your installed version in a few minutes.
:::
