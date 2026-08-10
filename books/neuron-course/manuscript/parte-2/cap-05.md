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

**Honest in failure.** Returning "Order not found" is useful to the model. Returning an empty string leaves it guessing, and a guessing model hallucinates.

### The mental shift

Stop thinking of tools as an integration feature. They are the **capability surface of your agent** — an API design problem, where the consumer is a language model rather than another developer.

That framing explains why the rest of this chapter spends so much time on naming, descriptions and schemas. You are writing documentation for a consumer that reads only the documentation.

### Key takeaways

- A tool is your function; the model requests, your code executes.
- The registered tool list is the security boundary — the only one you can rely on.
- Good tools are narrow, deterministic, compact in output, and explicit about failure.
- Designing tools is API design for a reader who has only the docs.

## 5.2 Inline Tools

### The shape

```php
Tool::make('name', 'description')
    ->addProperty(new ToolProperty(...))
    ->setCallable(fn (...) => ...);
```

Three pieces: identity, schema, implementation.

### The canonical example

This is the shape from the official documentation, and it is worth knowing verbatim because you will meet it everywhere:

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

### The rule everyone trips over

**The property name must match the callable's parameter name.**

The property is named `video_url`. The closure signature is `function (string $video_url)`. Not `$url`, not `$videoUrl`. Exactly `$video_url`.

NeuronAI maps the model's JSON arguments onto the callable by name. Rename one side and you get a confusing failure that looks like the model got it wrong when in fact your wiring did. It is the single most common tool bug.

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

That question forces two calls to the same tool with different arguments — a better first experiment than a single-call question, because you watch the loop iterate.

### When inline is the right choice

**Use it for:** prototypes, one-off scripts, tools that genuinely have no reuse, teaching demos.

**Do not use it for:** anything that needs a dependency, anything you will test, anything that appears in more than one agent, anything longer than about ten lines.

The closure cannot be injected, cannot be mocked, cannot be unit tested in isolation, and cannot be reused. Section 5.3 fixes all four.

### Key takeaways

- `Tool::make()->addProperty()->setCallable()`.
- Property name must exactly match the callable parameter name.
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

**3. `__invoke()`** — the implementation. PHP's magic invoke method, so the tool object is callable. Parameter names must match the property names, exactly as in Section 5.2.

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

The tool is a callable object. You invoke it directly, with no agent, no provider, no network call to a model. Given the non-determinism problem from Section 1.5, having a large part of your agentic system be ordinary testable PHP is a significant win — and the boundary between "testable" and "not testable" runs exactly along this class.

**It is reusable and shippable.** Tools implement `ToolInterface`. A well-built tool can be published as a Composer package or contributed upstream to the framework.

**It has a real name.** `GetTranscriptionTool` appears in stack traces, in your DI container, in your IDE's navigation. A closure appears as `{closure}`.

::: {.callout .callout-tip}
[In practice]{.callout-title}

Take the `get_server_load` inline tool from Section 5.2 and convert it to a class, then write a PHPUnit test for it. It takes five minutes, and it makes the testability argument far better than reading about it does.
:::

### Key takeaways

- Constructor for identity and dependencies, `properties()` for schema, `__invoke()` for logic.
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

Every level of nesting is another chance for the model to produce a shape that does not validate, and complex schemas consume tokens on every single request in the loop — remember from Section 1.3 that the full tool schema is re-transmitted every iteration.

Three rules:

**Prefer flat.** Two scalar properties beat one object with two fields, unless the object is genuinely reused across tools.

**Prefer several narrow tools over one wide tool with a discriminated union.** A tool taking `{action: "create"|"update"|"delete", payload: {...}}` is harder for the model to call correctly than three separate tools. It is also impossible to authorise granularly — you cannot let a user delete but not create if both live behind one tool.

**Let the model do the conversion work.** Rather than accepting a free-text date and parsing it yourself, declare the property as an ISO 8601 string with an example in the description. Models are good at format conversion, and you get a validated shape at the boundary instead of a parsing problem inside your tool.

### Exercise

Write a `compare_cities` tool that takes an `ArrayProperty` of city names with `minItems: 2, maxItems: 5`, and returns a comparison. Then ask the agent to compare eight cities. Observe how the constraint is enforced and how the model reacts to being constrained.

### Key takeaways

- Three classes: `ToolProperty`, `ArrayProperty`, `ObjectProperty`.
- `required` and `nullable` are different questions.
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

### Why this is the default worth adopting

**The schema and the type cannot drift.** Add a field to the DTO and the schema updates. There is no second place to remember to edit — which is the failure mode of hand-written schemas in a codebase with more than one contributor.

**Static analysis works again.** PHPStan or Psalm can see `$color->r`. With array-shaped input they see `mixed`, and your tool bodies become an analysis blind spot.

**The DTO is reusable.** The same annotated class works for structured *output* (Chapter 6). One `Order` class can define what the model must produce and what a tool accepts — the same contract in both directions.

**`#[SchemaProperty]` supports validation constraints.** Beyond `description` and `required`, the attribute accepts constraints such as `minLength` and `maxLength`. Push validation into the schema so the model receives the rules rather than your tool discovering violations at runtime. Check the attribute's signature in your installed version for the full set.

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

**That is the point worth drawing out:** an individual tool description says *what this tool does*. Guidelines say *how to combine these tools into a strategy*. If you build your own toolkit, the guidelines are where the strategy goes, and skipping them wastes most of the mechanism.

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

**Wrong-tool errors.** Selection accuracy degrades as the catalogue grows. Twelve arithmetic tools where three would do means nine extra chances to pick the wrong one.

**Blast radius.** Every attached tool is reachable by any user who can talk to the agent. That is Section 5.1's security model, applied to convenience imports.

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

::: {.callout .callout-warning}
[Verify the method name]{.callout-title}

The `with()` example in the documentation calls `setMaxTries(1)`, while the Max Runs section uses `setMaxRuns()`. That is item 2 in Appendix A — check which one exists in your installed version before you write either.
:::

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

## 5.9 Max Runs: Guarding the Loop

### The unbounded loop, revisited

Section 1.2 established that the agent loop is a `while` with no guaranteed exit. The model keeps requesting tools until it decides it is finished. If it never decides, the loop never ends.

This is not hypothetical. Three ways it happens in practice:

- The tool returns something the model misreads as failure, so it retries. Forever.
- The task is genuinely impossible with the tools available, and the model keeps trying alternatives.
- Two tools feed each other in a cycle — search returns a reference, fetch returns something needing another search.

Each iteration costs a model call and grows the context. Unbounded, this is a runaway bill.

### The guard

NeuronAI tracks how many times each tool is invoked during an execution session. Exceed the limit and execution is interrupted with an exception. **The default is 10 calls, counted per tool individually.**

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

::: {.callout .callout-warning}
[Verify the exception class]{.callout-title}

The prose in the documentation names `ToolRunsExceededException`; the example catch block names `ToolMaxTriesException`. That is item 1 in Appendix A. Check what your version actually throws before writing a catch block — a wrong class name in a `catch` produces silent non-handling rather than an obvious error, which is the worst kind of bug to inherit.
:::

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

Section 5.11 covers a more sophisticated option: handing the error back to the model so it can recover on its own.

### Key takeaways

- Default is 10 runs, per tool, per execution session.
- `toolMaxRuns()` sets the agent default; `setMaxRuns()` on a tool overrides it.
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
| Offered, gated at runtime | `ToolApproval` middleware | Human decision |
| Offered, checked on execution | Policy check inside `__invoke()` | Your PHP |
| Offered, restricted at source | Database grants, API scopes | Infrastructure |

Use several. `visible()` is your first line, not your only one — a bug in the visibility expression should not be the only thing between a user and a refund.

### Visibility vs approval

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

Small purchases go through; large ones wait for a human. That is a much better product than either always-allow or always-block. We build it properly in Chapter 15 and wire it to a real UI in Chapter 22 — mentioned here so the distinction lands while visibility is fresh.

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
- Derive visibility from the actor, injected into the agent's constructor.

## 5.11 Tool Error Handling

### The default

`ToolNode` accepts an `$errorHandler` argument. **By default it re-raises execution errors.** Your tool throws, and the exception propagates up through `chat()` into your application.

That is a reasonable default — silent failure would be worse — but it is rarely what you want in production. One transient timeout on one tool call, and a conversation that was going fine dies.

### The alternative: tell the model

This is the idea worth the whole section. Instead of crashing, hand the error back to the model as the tool's result.

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

**Include the instruction, not just the fact.** "Do not retry more than once" is doing real work. Without it, a transient failure can burn through the max-runs limit from Section 5.9 in seconds.

**Never leak internals into the conversation.** Connection strings, file paths, internal hostnames, credentials in exception messages — all of these end up in the transcript, which may be stored, logged and shown to the user.

### The interaction with max runs

The error handler catches the run-limit exception too. That gives you a graceful exit at the limit rather than an exception at the boundary:

```php
$e instanceof ToolRunsExceededException =>
    "You have used this tool too many times. Stop calling it and answer with "
    . "what you already know, or tell the user you cannot complete the task.",
```

The model receives a clear stop signal and writes a sensible final message. Far better than a 500. Appendix A item 1 applies here too — confirm the exception class name before writing this branch.

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

## 5.12 Provider Tools

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

::: {.callout .callout-warning}
[Documentation typo]{.callout-title}

The documentation shows `ProviderTool:make()` with a single colon. It is a typo for `::`. Appendix A item 6.
:::

### The trade-off, stated as the docs state it

The official documentation is refreshingly blunt: provider tools introduce a lot of constraints, and the most flexible and reliable way to add capabilities to your agents remains the Tools and Toolkits system.

That is the framework authors telling you their own feature is the second choice. Take them at their word, and understand why:

**You lose portability.** This is the big one. Section 3.6 sold provider swapping as the framework's central benefit. A provider tool anchors you: switch from OpenAI to Ollama and that capability silently vanishes. The whole cost-tiering and vendor-risk argument evaporates for any agent that depends on one.

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

- Provider tools run server-side; supported on OpenAIResponses, Gemini and Anthropic only.
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

The design here is thoughtful: if `pcntl` is not present — a Windows development machine, for instance — the implementation **automatically falls back to sequential execution**. No configuration, no environment detection in your code, no crash.

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

**Database connections need care.** A PDO connection inherited across a fork is a classic source of strange, intermittent failures. If your tools hit the database, open the connection inside the tool rather than sharing one across forks.

### Key takeaways

- `parallelToolCalls(true)` swaps `ToolNode` for `ParallelToolNode`.
- Requires `spatie/fork` and `pcntl`; **CLI only**, never in a web request.
- Falls back to sequential automatically when unavailable.
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

Open-Meteo needs no API key, so the whole lab runs free — combined with Ollama, you complete it without an account anywhere.

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
            $class = $e::class;

            \error_log("[tool:{$tool->getName()}] {$class}: {$e->getMessage()}");

            return "The {$tool->getName()} tool failed: {$e->getMessage()}. "
                 . "Do not retry more than once. If it fails again, tell the user "
                 . "the data is unavailable.";
        };
    }
}
```

Note what this one class demonstrates from the chapter: a class-based tool (5.3), a four-part description (5.4), examples in property descriptions (5.4), `only()` as an allowlist (5.8), a per-tool run cap (5.9), and a real error handler (5.11).

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

### Two things to observe

Run it with `INSPECTOR_INGESTION_KEY` set and open the trace. You see the actual sequence: two weather calls, one mean call, one final text response. That picture is what Section 1.2's table described in the abstract, and seeing it makes the cost arithmetic of Section 1.4 concrete.

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

The Tools documentation is the densest page in the NeuronAI project and it disagrees with itself in nine places — exception names, method names, class names, namespaces and import paths. Every one of them produces a fatal error for someone who copies the page. They are items 1 to 9 in Appendix A, with probe scripts that settle all of them against your installed version in a few minutes.
:::
