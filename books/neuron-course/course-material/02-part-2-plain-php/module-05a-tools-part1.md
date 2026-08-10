# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Module 5, Lessons 5.1 to 5.7

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^3.0, PHP 8.3.
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

```php
Tool::make('name', 'description')
    ->addProperty(new ToolProperty(...))
    ->setCallable(fn (...) => ...);
```

Three pieces: identity, schema, implementation.

### The canonical example

This is the shape from the official documentation, and it is worth using verbatim in the course because students will meet it everywhere:

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
            Tool::make(
                'get_transcription',
                'Retrieve the transcription of a youtube video.',
            )->addProperty(
                new ToolProperty(
                    name: 'video_url',
                    type: PropertyType::STRING,
                    description: 'The URL of the YouTube video.',
                    required: true,
                )
            )->setCallable(function (string $video_url) {
                return 'Video transcription...';
            }),
        ];
    }
}
```

### The rule students trip over

**The property name must match the callable's parameter name.**

The property is named `video_url`. The closure signature is `function (string $video_url)`. Not `$url`, not `$videoUrl`. Exactly `$video_url`.

Neuron maps the model's JSON arguments onto the callable by name. Rename one side and you get a confusing failure that looks like the model got it wrong when in fact your wiring did.

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
    ->chat(new UserMessage($question))
    ->getMessage()
    ->getContent() . PHP_EOL;
```

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
            Tool::make(
                'get_server_load',
                'Returns the average CPU load of this server over a given time window. '
                . 'Use this whenever asked about current server load, stress, or performance.'
            )->addProperty(
                new ToolProperty(
                    name: 'window',
                    type: PropertyType::STRING,
                    description: 'The time window. Allowed values: "1m", "5m", "15m".',
                    required: true,
                )
            )->setCallable(function (string $window): string {
                $load = \sys_getloadavg();

                $value = match ($window) {
                    '1m'  => $load[0],
                    '5m'  => $load[1],
                    '15m' => $load[2],
                    default => throw new \InvalidArgumentException("Invalid window: {$window}"),
                };

                return \sprintf('Load average over %s: %.2f', $window, $value);
            }),
        ];
    }
}
```

```bash
php examples/02-inline-tool.php "How stressed is the server compared to fifteen minutes ago?"
```

That question forces two calls to the same tool with different arguments. It is a better demo than a single-call question, because students see the loop iterate.

### When inline is the right choice

**Use it for:** prototypes, one-off scripts, tools that genuinely have no reuse, teaching demos.

**Do not use it for:** anything that needs a dependency, anything you will test, anything that appears in more than one agent, anything longer than about ten lines.

The closure cannot be injected, cannot be mocked, cannot be unit tested in isolation, and cannot be reused. Lesson 5.3 fixes all four.

### Key takeaways

- `Tool::make()->addProperty()->setCallable()`.
- Property name must exactly match the callable parameter name.
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

use GuzzleHttp\Client;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class GetTranscriptionTool extends Tool
{
    protected Client $client;

    public function __construct(protected string $key)
    {
        parent::__construct(
            'get_transcription',
            'Retrieve the transcription of a youtube video.',
        );
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
            ->get('transcript?url=' . $video_url . '&text=true')
            ->getBody()
            ->getContents();

        $response = json_decode($response, true);

        return $response['content'];
    }

    protected function getClient(): Client
    {
        return $this->client ??= new Client([
            'base_uri' => 'https://api.supadata.ai/v1/youtube/',
            'headers'  => ['x-api-key' => $this->key],
        ]);
    }
}
```

**1. The constructor** — declares identity by calling `parent::__construct(name, description)`, and takes whatever dependencies the tool needs. Here it is an API key; in a real application it might be a repository, a PDO connection, a mailer.

**2. `properties()`** — the schema, same objects as the inline version.

**3. `__invoke()`** — the implementation. PHP's magic invoke method, so the tool object is callable. Parameter names must match the property names, exactly as in Lesson 5.2.

**4. Helpers** — anything else the class needs, kept private to the tool. The lazy `??=` client here is a small but good habit: no HTTP client is constructed unless the model actually calls the tool.

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

**It takes dependencies.** The inline closure could only capture variables from scope. A class receives a PDO connection, a repository, a mailer — through its constructor, from your DI container.

**It is unit testable without an LLM.** This is the argument that matters most:

```php
public function test_it_returns_the_transcript(): void
{
    $tool = new GetTranscriptionTool('fake-key');

    $result = $tool('https://youtube.com/watch?v=xyz');

    $this->assertStringContainsString('expected phrase', $result);
}
```

The tool is a callable object. You invoke it directly, with no agent, no provider, no network call to a model. Given the non-determinism problem from Lesson 1.5, having a large part of your agentic system be ordinary testable PHP is a significant win — and the boundary between "testable" and "not testable" runs exactly along this class.

**It is reusable and shippable.** Tools implement `ToolInterface`. A well-built tool can be published as a Composer package or contributed upstream to the framework. This is how the ecosystem grows, and it is a realistic path to visibility for a developer who wants one.

**It has a real name.** `GetTranscriptionTool` appears in stack traces, in your DI container, in your IDE's navigation. A closure appears as `{closure}`.

### The refactoring exercise to record

Take the `get_server_load` inline tool from Lesson 5.2 and convert it to a class. Then write a PHPUnit test for it. Five minutes of video, and it makes the testability argument far better than a slide can.

### Key takeaways

- Constructor for identity and dependencies, `properties()` for schema, `__invoke()` for logic.
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
            nullable: false,
        ),
    ];
}
```

`PropertyType` covers the scalar types — string, number, boolean and so on. Check the enum in your installed version for the exact cases.

Two arguments worth distinguishing:

- **`required`** — must the model supply this property at all?
- **`nullable`** — may the supplied value be null?

They are not the same thing, and conflating them produces schemas that permit inputs you did not intend. A required-but-nullable property must be present and may be null; an optional property may be absent entirely.

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

Write a `compare_cities` tool that takes an `ArrayProperty` of city names with `minItems: 2, maxItems: 5`, and returns a comparison. Then run it and ask the agent to compare eight cities. Observe how the constraint is enforced and how the model reacts.

### Key takeaways

- Three classes: `ToolProperty`, `ArrayProperty`, `ObjectProperty`.
- `required` and `nullable` are different questions.
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
    public function __construct() { /* ... */ }

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

Note the signature: `__invoke(Color $color)`. Not an array. A typed object, with IDE completion, static analysis and refactoring support.

### Why this is the pattern to teach as the default

**The schema and the type cannot drift.** Add a field to the DTO and the schema updates. There is no second place to remember to edit — which is the failure mode of hand-written schemas in a codebase with more than one contributor.

**Static analysis works again.** PHPStan or Psalm can see `$color->r`. With array-shaped input they see `mixed`, and your tool bodies become an analysis blind spot.

**The DTO is reusable.** The same annotated class works for structured *output* (Module 6). One `Order` class can define what the model must produce and what a tool accepts — the same contract in both directions.

**`#[SchemaProperty]` supports validation constraints.** Beyond `description` and `required`, the attribute accepts constraints such as `minLength` and `maxLength`. Push validation into the schema so the model receives the rules rather than your tool discovering violations at runtime. Check the attribute's signature in your installed version for the full set.

### Note on the namespace

`SchemaProperty` lives under `NeuronAI\StructuredOutput\`, not under `NeuronAI\Tools\`. That is not an accident — it is the same mechanism the structured-output system uses, which is exactly why the DTO is reusable across both. Worth mentioning, because the import location surprises people.

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

An agent that needs arithmetic needs sum, subtract, multiply, divide, exponentiate, square root, mean, median, mode, standard deviation and variance. Declaring eleven tools individually in every agent is noise.

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

One line, twelve tools.

### What a toolkit is made of

```php
namespace NeuronAI\Tools\Toolkits\Calculator;

use NeuronAI\Tools\Toolkits\AbstractToolkit;

class CalculatorToolkit extends AbstractToolkit
{
    public function guidelines(): ?string
    {
        return "This toolkit allows you to perform mathematical operations. You can also use this functions to solve
        mathematical expressions executing smaller operations step by step to calculate the final result.";
    }

    public function provide(): array
    {
        return [
            SumTool::make(),
            SubtractTool::make(),
            MultiplyTool::make(),
            DivideTool::make(),
            ExponentiateTool::make(),
        ];
    }
}
```

Two methods on `AbstractToolkit`.

**`provide()`** returns the tools. Once attached, they behave exactly as if declared individually.

**`guidelines()` is the interesting one.** It gives the model contextual information about how the tools work *together*, which no individual tool description can convey.

Look at what the calculator's guidelines actually say: complex expressions can be solved by executing smaller operations step by step. That single sentence changes behaviour. Without it, a model faced with a multi-part calculation may attempt it in its head — and language models are unreliable at arithmetic. With it, the model decomposes the problem into tool calls and gets the right answer.

**That is the lesson to draw out:** an individual tool description says *what this tool does*. Guidelines say *how to combine these tools into a strategy*. If you build your own toolkit, the guidelines are where the strategy goes, and skipping them wastes most of the mechanism.

### The built-in catalogue

| Toolkit | Capability | Needs |
|---|---|---|
| **Calculator** | 12 tools: arithmetic, roots, mean, median, mode, standard deviation, variance | — |
| **Calendar** | 18 tools: current time, formatting, differences, timezone conversion, weekday, leap year, periods | — |
| **MySQL / PGSQL** | Schema introspection, SELECT, write operations | PDO |
| **FileSystem** | describe directory, read, grep, glob, preview, parse | — |
| **Tavily** | web search, page extraction, site crawl | API key |
| **Jina** | web search, URL reader | API key |
| **Supadata YouTube** | video transcript, video metadata, channel, playlist | API key |
| **Zep** | long-term memory store and retrieve | API key |
| **AWS SES** | send email | `aws/aws-sdk-php` |

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

The documentation's own advice, worth quoting in the video: if you are not confident about your agent's behaviour, you may simply not provide the writing tool. Attaching read tools only is a complete, effective mitigation — not a compromise.

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

---
═══════════════════════════════════════════════════════════════

## PRE-RECORDING VERIFICATION LIST — MODULE 5

The Tools documentation is the densest page in the project and contains several internal inconsistencies. Check each against your installed version before recording, so you teach the real API rather than the documented one.

| # | Issue | Where it appears |
|---|---|---|
| 1 | **`ToolRunsExceededException` vs `ToolMaxTriesException`** — the prose names the first, the example `catch` block names the second | Max Runs section |
| 2 | **`setMaxRuns()` vs `setMaxTries()`** — the Max Runs section uses the first, the `with()` filter example uses the second | Max Runs / Filters |
| 3 | **`ExponentiateTool` vs `ExponentialTool`** — the `provide()` source shows the first, the tools table shows the second | Calculator toolkit |
| 4 | **`Toolkits\CalendarToolkit\CalendarToolkit` vs `Toolkits\Calendar\...`** — the import and the tools table disagree | Calendar toolkit |
| 5 | **`NeuronAI\Tools\Calculator\CalculatorToolkit` vs `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit`** | Toolkits intro vs Calculator section |
| 6 | **`ProviderTool:make()`** — single colon, a typo for `::` | Provider Tools |
| 7 | **`new SesCleint(...)`** — misspelling of `SesClient` | AWS SES |
| 8 | **`instructions()` visibility** — `public` in some examples, `protected` in others | Throughout |
| 9 | **`use NeuronAI\Agent;` vs `use NeuronAI\Agent\Agent;`** — v2 imports survive in several toolkit examples | Toolkit sections |

None of these are framework bugs; they are documentation drift across versions. But every one of them will produce a fatal error for a student who copies the page, so resolving them in your material is a real value-add over the official docs — and worth mentioning on camera as a reason to trust the course.

---

**END OF LESSONS 5.1–5.7**

*Next: Lessons 5.8–5.13 — toolkit filters, max runs, visibility, error handling, provider tools, parallel execution. Then the Module 5 labs.*
