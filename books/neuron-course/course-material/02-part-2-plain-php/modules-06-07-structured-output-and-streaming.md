# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Modules 6 and 7

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^3.0, PHP 8.3.

---

> ## ⚠ CORRECTION TO LAB 01
>
> The streaming snippet in the earlier `lab-01-php-puro.md` file used the v2 API:
>
> ```php
> // WRONG for v3
> foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
>     echo $chunk;
> }
> ```
>
> In v3, `stream()` returns a **handler**, and you call `events()` on it to get the generator.
> The generator yields **chunk objects**, not strings. Correct form:
>
> ```php
> $handler = AssistantAgent::make()->stream(new UserMessage($prompt));
>
> foreach ($handler->events() as $chunk) {
>     echo $chunk->content;
> }
> ```
>
> Fix this in the lab file before publishing. Lesson 7.2 covers it fully.

---
═══════════════════════════════════════════════════════════════
# MODULE 6 — STRUCTURED OUTPUT
═══════════════════════════════════════════════════════════════
---

## LESSON 6.1 — Why Structured Output Exists

**Duration:** 11 minutes
**Type:** Theory

### Learning objectives

Understand why getting typed objects out of a language model is the feature that turns an AI demo into a piece of software.

### The problem

Everything so far has produced prose. Prose is fine when a human reads it. It is useless when the next step is `$order->save()`.

The naive approach is to ask for JSON in the prompt and parse it:

```php
$response = $agent->chat(new UserMessage(
    'Extract the order details as JSON with keys name, items, total.'
))->getMessage()->getContent();

$data = json_decode($response, true); // 🤞
```

This fails in ways that are individually small and collectively fatal:

- The model wraps the JSON in a markdown code fence
- It adds a friendly sentence before the JSON
- It uses `total_amount` instead of `total` on one run in twenty
- It returns a string where you expected a number
- It omits a field entirely when the source text did not mention it
- It hallucinates an extra field you never asked for

Every one of those is a production incident, and Lesson 1.5 already told you why you cannot test your way out: the same input produces different output.

### What Neuron does instead

Two layers, and the separation between them is the design insight worth teaching:

**Layer 1 — Schema.** You define a PHP class with strict type hints and `#[SchemaProperty]` attributes. Neuron generates the corresponding JSON schema from your class and sends it to the model as part of the request. The model is *told* the shape it must produce.

**Layer 2 — Validation.** You attach validation attributes to the properties. Neuron parses the response, validates it against those rules, and — critically — **if validation fails it retries, telling the model exactly which properties were wrong.**

You get back an instance of your class. Typed. Validated. Ready to persist.

### The line worth putting on a slide

> Layer 1 tells the model what you want. Layer 2 checks whether you got it, and asks again if you did not.

Most JSON-mode implementations in other ecosystems give you layer 1 only. The retry-with-violations loop in layer 2 is what makes the difference between "usually works" and "works".

### Where this changes your architecture

Structured output is what makes an agent a **component** rather than a chat feature. Once the output is a typed object you can:

- Persist it directly
- Pass it into existing domain services that know nothing about AI
- Assert on its shape in tests — the contract testing from Lesson 1.5, finally possible
- Put an agent in the middle of a business process with deterministic code on both sides

That last one is the big architectural unlock. Non-deterministic component, deterministic boundary.

### Key takeaways

- Prompt-and-parse fails in a dozen small ways that are untestable in aggregate.
- Two layers: schema generation from PHP classes, then validation with retry.
- A validated typed object is what lets an agent sit inside a normal business process.

---
═══════════════════════════════════════════════════════════════

## LESSON 6.2 — Defining the Output Class

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Write an output DTO whose PHP types and attributes generate the schema the model receives.

### The basic form

```php
<?php

namespace App\Neuron\Output;

use NeuronAI\StructuredOutput\SchemaProperty;

class Person
{
    #[SchemaProperty(
        description: 'The user name.',
        required: true
    )]
    public string $name;

    #[SchemaProperty(
        description: 'What the user love to eat.',
        required: false
    )]
    public string $preference;
}
```

Two things generate the schema:

**The PHP type hint.** `public string $name` becomes a string in the JSON schema. This is why strict typing is not a style preference here — it is the schema. An untyped or `mixed` property gives the model nothing to work with.

**The attribute.** `#[SchemaProperty]` adds the metadata the type cannot express.

### The description is doing the same job as a tool description

This is the connection to make explicitly, because it saves explaining the same principle twice.

`description` is what the model reads to decide what goes in the field. `'The user name.'` is adequate. `'The full name of the person placing the order, as written in the source text. Do not infer or complete partial names.'` is better, and eliminates a class of hallucination.

Lesson 5.4's four-part formula applies, minus the "when to use" part: say what the field is, what format you expect, and what not to do.

The documentation's own recommendation is to always define at least `description` and `required`. Treat that as a minimum, not a target.

### Schema constraints

`#[SchemaProperty]` accepts constraints that go into the JSON schema itself:

```php
class Person
{
    #[SchemaProperty(
        description: 'The user name.',
        required: true,
        minLength: 3,
        maxLength: 255,
    )]
    public string $name;

    #[SchemaProperty(
        description: 'What the user love to eat.',
        required: false,
        min: 18,
        max: 64,
    )]
    public ?int $age = null;
}
```

`minLength` / `maxLength` for strings, `min` / `max` for numbers.

**These are different from validation rules, and the distinction matters.** Schema constraints go *to the model* — they are instructions in the request. Validation rules (Lesson 6.5) run *on the response* — they are checks after the fact.

Use both. The schema constraint reduces the chance of a violation; the validation rule catches it when it happens anyway.

### Optional properties

Note the pattern for optional fields:

```php
#[SchemaProperty(description: '...', required: false)]
public ?int $age = null;
```

Nullable type, default value. Without the default, an uninitialised typed property throws when accessed — which turns "the model omitted an optional field" into a fatal error at exactly the moment you were trying to be lenient.

### Where to put these classes

`App\Neuron\Output` in the documentation's examples. Any convention works; pick one and hold it, because these classes multiply quickly and they are easy to confuse with your domain models.

**Do not use your Eloquent models or domain entities as output classes.** They have relations, casts, lifecycle hooks and dozens of properties the model has no business populating. Write a dedicated DTO and map it in your own code. The DTO is a contract with the model; your entity is a contract with your database. Keeping them separate is the same instinct that keeps request objects out of your persistence layer.

### Key takeaways

- The PHP type hint *is* the schema — strict typing is mandatory here.
- `description` deserves the same care as a tool description.
- Schema constraints instruct the model; validation rules check the response. Use both.
- Optional properties need a nullable type *and* a default.
- Never use a domain entity as the output class.

---
═══════════════════════════════════════════════════════════════

## LESSON 6.3 — Requesting Structured Output

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Call the agent for a typed result, and choose between per-call and per-agent output contracts.

### Per call

```php
use NeuronAI\Chat\Messages\UserMessage;

$person = MyAgent::make()->structured(
    new UserMessage("I'm John and I like pizza!"),
    Person::class
);

echo $person->name . ' like ' . $person->preference;
// John like pizza
```

`structured()` instead of `chat()`. Second argument is the class. What comes back is **an instance of that class** — not a response wrapper, not a message. You do not call `getMessage()`.

That difference in return type is worth pausing on in the video, because students have just spent three modules typing `->getMessage()->getContent()` and will reach for it here out of habit.

### Per agent

When an agent always produces the same shape, put the contract in the class:

```php
class MyAgent extends Agent
{
    protected function getOutputClass(): string
    {
        return Person::class;
    }
}
```

```php
$person = MyAgent::make()
    ->structured(new UserMessage("I'm John and I like pizza"));

echo $person->name . ' like ' . $person->preference;
```

**The detail that catches everyone:** you still have to call `structured()`. `getOutputClass()` sets the default shape; it does not change what `chat()` does. Calling `chat()` on an agent with an output class still returns prose.

The documentation states this explicitly — *you always need to call the `structured()` method to require strict output* — precisely because it is unintuitive.

### Which one to use

**Per-agent (`getOutputClass()`)** when the agent has one job. `InvoiceExtractorAgent` always produces an `Invoice`. The contract belongs in the class, where a reader finds it, and every call site cannot get it wrong.

**Per-call** when the same agent serves several extraction shapes, or when the shape is chosen at runtime.

Default to per-agent. An agent with a declared output class is self-documenting, and it composes better when you later wrap it as a workflow node.

### The three ways to run an agent

Worth putting on one slide, because Module 7 adds the third:

| Method | Returns | Use for |
|---|---|---|
| `chat()` | Response → `getMessage()` → text | Conversation |
| `structured()` | An instance of your class | Data extraction |
| `stream()` | Handler → `events()` → chunks | Real-time UI |

Same agent, same tools, same history. Three entry points, each backed by a different node — `ChatNode`, `StructuredOutputNode`, `StreamingNode`. Lesson 2.3 said node classes are public API; here is the first place students feel it.

### Key takeaways

- `structured($message, MyClass::class)` returns the instance directly.
- `getOutputClass()` sets a default shape but you must still call `structured()`.
- Prefer the per-agent contract.
- Three entry points, three nodes, one agent.

---
═══════════════════════════════════════════════════════════════

## LESSON 6.4 — Nested Objects and Typed Arrays

**Duration:** 15 minutes
**Type:** Hands-on

### Learning objectives

Express realistic data shapes — objects inside objects, lists of objects, lists of mixed types.

### Nested classes

Type a property as another structured class:

```php
<?php

namespace App\Neuron\Output;

use NeuronAI\StructuredOutput\SchemaProperty;
use NeuronAI\StructuredOutput\Validation\Rules\NotBlank;

class Person
{
    #[SchemaProperty(description: 'The user name.', required: true)]
    #[NotBlank]
    public string $name;

    #[SchemaProperty(description: 'What user love to eat.', required: true)]
    public string $preference;

    #[SchemaProperty(description: 'The address to complete the delivery.', required: true)]
    public Address $address;
}
```

```php
<?php

namespace App\Neuron\Output;

use NeuronAI\StructuredOutput\SchemaProperty;
use NeuronAI\StructuredOutput\Validation\Rules\NotBlank;

class Address
{
    #[SchemaProperty(description: 'The name of the street.', required: true)]
    #[NotBlank]
    public string $street;

    #[SchemaProperty(description: 'The name of the city.', required: false)]
    public string $city;

    #[SchemaProperty(description: 'The zip code of the address.', required: true)]
    #[NotBlank]
    public string $zip;
}
```

```php
$person = MyAgent::make()->structured(
    new UserMessage("I'm John and I want a pizza at st. James Street 00560!"),
    Person::class
);

echo $person->address->street;
// st.James Street
```

`$person->address` is an `Address` instance. Full IDE completion, full static analysis, all the way down.

> **Documentation warning.** The nested-class example on the official page imports `NeuronAI\StructuredOutput\Property` (should be `SchemaProperty`) and `Symfony\Component\Validator\Constraints\NotBlank` / `Valid` — leftovers from before the framework shipped its own validation component. The correct namespace is `NeuronAI\StructuredOutput\Validation\Rules\NotBlank`. Add this to your verification list; copying that block verbatim will not compile.

### Arrays of strings

A plain `array` property defaults to a list of strings:

```php
#[SchemaProperty(description: 'A list of keywords.', required: true)]
public array $keywords;
```

### Arrays of objects

Use `anyOf`:

```php
class Person
{
    #[SchemaProperty(description: 'The user name.', required: true)]
    #[NotBlank]
    public string $name;

    #[SchemaProperty(
        description: 'The list of tag for the user profile.',
        required: true,
        anyOf: [Tag::class]
    )]
    public array $tags;
}
```

```php
class Tag
{
    #[SchemaProperty(description: 'The name of the tag', required: true)]
    #[NotBlank]
    public string $name;
}
```

PHP cannot express `Tag[]` in a type hint, so `anyOf` carries the information the type system cannot.

### Arrays of mixed types

`anyOf` takes a list, and that list can hold several classes:

```php
class Report
{
    #[SchemaProperty(
        description: 'The content of the report',
        required: true,
        anyOf: [TextBlock::class, TableBlock::class, ImageBlock::class]
    )]
    public array $content;
}
```

Neuron puts all three specifications into the schema, and the model chooses per element.

This is more powerful than it first looks. It lets you model **documents made of heterogeneous blocks** — the shape behind every modern CMS, page builder and rich-text editor. Asking a model to convert an unstructured document into an ordered list of typed blocks is a genuinely strong use case, and it is one of the better demos you can record for this module.

### Design guidance

**Depth costs accuracy.** Each nesting level is another chance for a malformed shape. Two levels is comfortable, three is pushing it, four means you should extract in stages.

**Extract in stages when the document is large.** One agent produces the top-level structure with identifiers; a second agent fills in the detail per item. Two focused calls beat one call with a schema the model half-satisfies. This is also cheaper, because the second call carries a much smaller schema.

**Model what you need, not what exists.** The source invoice has forty fields. Your process uses six. Extract six. Every field in the schema costs tokens on the request and is another opportunity for a violation.

### Key takeaways

- Type a property as another DTO for nesting; it comes back as an instance.
- `anyOf: [Tag::class]` for arrays of objects; PHP's type system cannot express it alone.
- `anyOf` with several classes models heterogeneous block documents.
- Keep depth shallow; extract in stages; model only the fields you use.

---
═══════════════════════════════════════════════════════════════

## LESSON 6.5 — Validation and Retry

**Duration:** 17 minutes
**Type:** Hands-on — the most valuable lesson in Module 6

### Learning objectives

Use the validation layer and understand the retry loop that makes structured output reliable rather than merely likely.

### The mechanism

Validation attributes go on the output class properties. When the model responds, Neuron parses the data and checks it. **If one or more properties fail, Neuron resends the request to the model with a detailed report of what was wrong**, and repeats until it succeeds or hits the retry limit.

That is the part to emphasise. It is not "validate and throw". It is "validate and tell the model what it got wrong so it can fix it".

You are giving the model a compiler error and asking it to try again — which is, in fact, exactly what it is good at.

### The default

By default Neuron retries **once** on validation failure. One extra attempt, with the violations included.

### Configuring it

```php
$person = MyAgent::make()->structured(
    messages: new UserMessage("I'm John and I like pizza!"),
    class: Person::class,
    maxRetries: 3
);
```

Zero disables retry — a single attempt:

```php
$person = MyAgent::make()->structured(
    messages: new UserMessage("I'm John and I like pizza!"),
    class: Person::class,
    maxRetries: 0
);
```

The documentation's guidance is sensible: with a less capable model, balance the probability of a valid answer against token consumption. Each retry is a full request — schema, prompt and the violation report — so retries are not cheap. This is Lesson 1.4's arithmetic appearing in a new place.

**Practical values:** frontier model with a simple schema → 1 (the default). Small local model, or a complex nested schema → 2 or 3. Batch processing where a failure can be requeued → 0, and handle it in your pipeline instead of paying for retries inline.

### The rule catalogue

| Rule | Checks |
|---|---|
| `#[NotBlank]` | Not empty. Takes `allowNull` |
| `#[Length]` | String length: `min`, `max`, `exactly` |
| `#[WordsCount]` | Word count: `min`, `max`, `exactly` |
| `#[Count]` | Array size: `min`, `max`, `exactly` |
| `#[EqualTo]` / `#[NotEqualTo]` | Strict comparison against `reference` |
| `#[GreaterThan]` / `#[GreaterThanEqual]` | Numeric lower bound |
| `#[LowerThan]` / `#[LowerThanEqual]` | Numeric upper bound |
| `#[OutOfRange]` | Number outside `min`–`max`; `strict` flag |
| `#[IsTrue]` / `#[IsFalse]` | Exact boolean |
| `#[IsNull]` / `#[IsNotNull]` | Nullability |
| `#[Json]` | Valid JSON string |
| `#[Url]` | Valid URL |
| `#[Email]` | Valid email |
| `#[IpAddress]` | Valid IP |
| `#[ArrayOf]` | Array of a given class |
| `#[Regex]` | Matches a pattern |

All under `NeuronAI\StructuredOutput\Validation\Rules\`.

### The two rules that earn their keep

**`#[WordsCount]`** is unusual and genuinely useful. Length limits in a prompt ("keep it under 50 words") are followed loosely. A `#[WordsCount(min: 1, max: 50)]` attribute is enforced, and a violation triggers a retry with the specific complaint. If you generate summaries, titles or meta descriptions with hard limits, this turns a soft request into a contract.

```php
class Article
{
    #[SchemaProperty(description: 'SEO page title.', required: true)]
    #[WordsCount(max: 10)]
    public string $title;

    #[SchemaProperty(description: 'Meta description.', required: true)]
    #[WordsCount(min: 20, max: 30)]
    public string $description;
}
```

**`#[Regex]`** enforces formats a schema constraint cannot express — SKUs, order references, postcodes, coupon codes:

```php
class Coupon
{
    #[Regex('/^[A-Z]{2}\d{4}$/')]
    public string $code;
}
```

### Custom rules

Rules are PHP attributes extending `AbstractValidationRule`:

```php
namespace App\Neuron\Output;

use Attribute;
use NeuronAI\StructuredOutput\Validation\Rules\AbstractValidationRule;

#[Attribute(Attribute::TARGET_PROPERTY)]
class MyFormatRule extends AbstractValidationRule
{
    public function __construct(protected string $format)
    {
    }

    public function validate(string $name, mixed $value, array &$violations): void
    {
        if (!is_string($value)) {
            $violations[] = $this->buildMessage($name, '{name} must be a string.');
            return;
        }

        if (!$this->respectFormat($value)) {
            $violations[] = $this->buildMessage(
                $name,
                '{name} must match the format {format}',
                ['format' => $this->format]
            );
        }
    }

    protected function respectFormat(string $value): bool
    {
        // your check
    }
}
```

```php
class Route
{
    #[MyFormatRule('apps/{id}/show')]
    public string $path;
}
```

> The official example for this has three small bugs — `respectFormat` declared with one parameter but called with two, `$this->pattern` referenced where `$this->format` was defined, and no early return after the type violation. The version above is corrected. Another item for the verification list.

**The message you write is sent to the model on retry.** So write it as an instruction, not a complaint. `'{name} must match the format apps/{id}/show'` gives the model something to act on. `'{name} is invalid'` does not.

That principle deserves a slide of its own: **violation messages are prompts.** Every one you write is text a language model will read and try to satisfy.

### Business rules in the validation layer

A pattern worth showing. Validation rules do not have to be format checks:

```php
class RefundRequest
{
    #[SchemaProperty(description: 'Refund amount in euros.', required: true)]
    #[GreaterThan(reference: 0)]
    #[LowerThanEqual(reference: 500)]
    public float $amount;

    #[SchemaProperty(description: 'Reason code.', required: true)]
    #[Regex('/^(DAMAGED|WRONG_ITEM|LATE|OTHER)$/')]
    public string $reason;
}
```

The model cannot produce a refund over €500 or an unrecognised reason code — not because you asked it politely, but because the object will not validate and it will be told to try again.

Compare this to putting "refunds must not exceed 500 euros" in the system prompt. One is a request. The other is a constraint. Everything in Lesson 5.10 about hiding versus instructing applies here in a different form.

### Key takeaways

- Validation failure triggers a retry that tells the model exactly what was wrong.
- Default is one retry; tune with `maxRetries`; `0` disables it.
- Schema constraints instruct; validation rules enforce.
- Violation messages are prompts — write them as instructions.
- Business rules encoded as validation are constraints, not requests.

---
═══════════════════════════════════════════════════════════════

## LESSON 6.6 — Structured Output vs Tool Calling

**Duration:** 10 minutes
**Type:** Theory

### Learning objectives

Choose correctly between two mechanisms that look similar and solve different problems.

### The confusion

Both involve a JSON schema. Both produce structured data. Both use `#[SchemaProperty]` in the Neuron implementation — Lesson 5.6 used the same attribute for structured tool *input*.

Yet they sit at opposite ends of the interaction.

### The distinction

**Tool calling is input.** The model produces a structured request so that *your code can run*. The data flows in, your function executes, and the result goes back to the model. It is a call.

**Structured output is the terminal result.** The model produces the final answer in a shape *your code consumes*. Nothing goes back to the model. It is a return.

| | Tool calling | Structured output |
|---|---|---|
| Purpose | Ask your code to act | Deliver the final answer |
| Direction | Model → your function → model | Model → your application |
| Position in the loop | Middle, repeatable | End, once |
| Method | `chat()` | `structured()` |
| Node | `ToolNode` | `StructuredOutputNode` |
| Can loop? | Yes | No |

### The decision rule

**Does the model need the result to continue reasoning?**

Yes → tool. No → structured output.

*"Look up this customer's orders and tell me if they're a repeat buyer."* The model needs the order data before it can judge. Tool.

*"Extract the name, email and order total from this text."* Nothing further to reason about. Structured output.

### They compose

An agent frequently uses both in one execution, and this is the shape most real extraction agents take:

```php
$invoice = InvoiceAgent::make()->structured(
    new UserMessage('Process the invoice at /uploads/inv-2291.pdf'),
    Invoice::class
);
```

Internally: the agent calls a `read_file` tool (tool calling), maybe calls a `lookup_vendor` tool to resolve a supplier code (tool calling), then produces an `Invoice` object (structured output). Tools in the middle, structure at the end.

### The anti-pattern

Do not use a tool as a way to receive the final result — a `save_result` tool that the model calls with the extracted data.

It appears to work, and it is worse in every respect: no validation, no retry-with-violations, no typed return value, and you have made a terminal answer into a side effect. When the model calls it twice, you now have a duplicate-handling problem you invented for yourself.

If the data is the answer, use `structured()`.

### The mirror image

Worth naming for symmetry: the same DTO class can serve both directions. Lesson 5.6's `ObjectProperty(class: Color::class)` and this module's `structured($msg, Color::class)` use the same annotated class.

One `Address` class can define what a tool accepts *and* what an agent returns. That is a real benefit of the attribute-based design — one contract, two directions, defined once.

### Module 6 assessment

1. Build an output class for a domain object you actually work with. Include one nested class and one array of objects.
2. Add validation encoding a real business rule, not just a format check.
3. Run it against a deliberately incomplete input and observe the retry. Then set `maxRetries: 0` and observe the failure.
4. Take one agent from Module 5 that returns prose and give it a `getOutputClass()`.

---
═══════════════════════════════════════════════════════════════
# MODULE 7 — STREAMING
═══════════════════════════════════════════════════════════════
---

## LESSON 7.1 — Why Streaming Matters

**Duration:** 9 minutes
**Type:** Theory

### Learning objectives

Understand what streaming does and does not fix, so you apply it where it helps.

### The number from Lesson 1.4

A model call takes 1–4 seconds. A five-iteration agent run with tool execution reaches 10–20 seconds of wall clock. Nobody waits 20 seconds at a blank screen.

### What streaming actually changes

**It does not make anything faster.** The total time is identical. Every token, every tool call, every round trip takes exactly as long.

**It changes when the user sees the first token.** Instead of 12 seconds of nothing followed by a complete answer, they see text appearing after 800 milliseconds and continuing.

Perceived wait is dominated by time-to-first-token, not time-to-completion. A response that streams for 15 seconds feels faster than one that blocks for 8. This is well-established in interface design generally, and it is unusually pronounced with text because the user can start reading while the rest arrives.

### The second benefit, which is underrated

Streaming lets you show **what the agent is doing**, not just what it eventually said.

Neuron's chunk types include tool calls and tool results. So you can render:

```
Let me check that for you.
  → Looking up order #4471...
  → Found it. Checking refund eligibility...
The order is eligible for a full refund.
```

That is a completely different product from a spinner. The user sees progress, understands why it is taking time, and — importantly — can tell that the system is working on the right problem before it finishes. Lesson 7.4 builds this.

### When not to stream

- **Batch and background jobs.** Nobody is watching.
- **Structured output.** You need the complete validated object; a half-parsed one is useless.
- **Very short responses.** Streaming a two-word answer adds complexity for nothing.
- **When you need to post-process the whole answer** before displaying it — filtering, redaction, formatting.

### Key takeaways

- Streaming changes perceived latency, not actual latency.
- Time-to-first-token is what users feel.
- Streaming tool activity is a product feature, not just a progress indicator.
- Not for batch work, structured output, or answers you must post-process.

---
═══════════════════════════════════════════════════════════════

## LESSON 7.2 — stream() and events()

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Consume a streamed response correctly with the v3 API.

### The API

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\UserMessage;

$handler = MyAgent::make()->stream(new UserMessage('How are you?'));

foreach ($handler->events() as $chunk) {
    echo $chunk->content;
}

// I'm fine, thank you! How can I assist you today?
```

Three steps, and each is a place people go wrong:

**1. `stream()` instead of `chat()`.** This prepares the agent's workflow to use `StreamingNode` rather than `ChatNode` — the third node swap in the course, after `ToolNode`/`ParallelToolNode` in Lesson 5.13 and `StructuredOutputNode` in Lesson 6.3.

**2. `stream()` returns a handler, not a generator.** You cannot iterate it directly.

**3. `events()` returns the generator.** And it yields **objects**, not strings. `$chunk->content`, not `$chunk`.

> **v2 → v3 change.** Earlier versions streamed plain strings for text and message instances for tool operations. v3 introduced dedicated chunk classes. Every older tutorial you find will show the string form. This is the third significant v2→v3 break in the course, after the namespaces and `getMessage()`.

### The chunk types

Four classes:

| Chunk | Contains |
|---|---|
| `TextChunk` | A piece of the response text |
| `ReasoningChunk` | Part of the model's reasoning summary — reasoning models only |
| `ToolCallChunk` | The model requesting a tool execution |
| `ToolResultChunk` | The result of a tool execution |

**What you receive depends on your agent.** No tools attached means no `ToolCallChunk` or `ToolResultChunk` — you can iterate expecting only text and reasoning. That is worth knowing before you write branching logic you do not need.

### Getting the final message

After the stream completes, the handler still holds the assembled result:

```php
$handler = MyAgent::make()->stream(...);

foreach ($handler->events() as $chunk) {
    // stream to the user
}

$message = $handler->getMessage();
echo $message->getContent();
```

This matters more than it looks. You stream to the user *and* get the complete `AssistantMessage` to persist, log, or run through a moderation check. You do not have to reassemble it from chunks yourself, which is exactly the tedious, error-prone thing everyone does on their first streaming implementation.

### Why chunk objects rather than strings

The framework's upgrade notes explain the reasoning, and it is a good design lesson for students.

Streaming raw message instances coupled the application to Neuron's internal message system. Dedicated chunk classes create a boundary: your UI code depends on a small, stable set of chunk types rather than on internal message plumbing. That separation is what made the stream adapter system possible (Lesson 7.5), and it means the internals can evolve without breaking your frontend.

It is a textbook case of introducing a DTO at a layer boundary — worth pointing out to an audience that writes PHP for a living.

### Key takeaways

- `stream()` → handler → `events()` → generator of chunk objects.
- `$chunk->content`, not `$chunk`.
- Four chunk types; which you get depends on whether the agent has tools.
- `getMessage()` on the handler gives you the complete assembled message afterwards.

---
═══════════════════════════════════════════════════════════════

## LESSON 7.3 — Streaming from the CLI

**Duration:** 11 minutes
**Type:** Hands-on

### Learning objectives

Get real-time output in a terminal, and understand the buffering problem before it appears in a web context.

### The example

**`examples/06-streaming.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the Repository pattern and when using it is a mistake.';

$start   = \microtime(true);
$first   = null;

$handler = AssistantAgent::make()->stream(new UserMessage($prompt));

foreach ($handler->events() as $chunk) {
    $first ??= \microtime(true);

    echo $chunk->content;
    \flush();
}

$end = \microtime(true);

\printf(
    "\n\n[first token: %.2fs | total: %.2fs]\n",
    $first - $start,
    $end - $start
);
```

```bash
php examples/06-streaming.php
```

### The demo to record

Run the same prompt twice — once with `chat()`, once with `stream()` — and put both timings on screen.

Total time: roughly identical. Time to first visible output: 4.1 seconds versus 0.7. Then say the sentence: *the work took the same time; the wait did not.*

Measuring time-to-first-token in the script is worth the four extra lines. It turns an assertion into a number, and students can reproduce it.

### The buffering problem

`flush()` is in there for a reason, and the reason gets much larger in Module 21.

PHP buffers output. So does the web server. So does the reverse proxy. Any one of them can hold your carefully streamed tokens and release them in a single block at the end — at which point you have all the complexity of streaming and none of the benefit.

From the CLI, `flush()` is usually enough. In a web context you also need to deal with:

- PHP's `output_buffering` setting
- `ob_end_flush()` if a buffer is already open
- nginx's `proxy_buffering` and `fastcgi_buffering`
- Any CDN or proxy in front of the application

The framework's own AG-UI documentation includes the warning: send the protocol headers and flush after each line, or the stream can get stuck in PHP output buffers or proxies.

Mention it here, solve it properly in Module 21. Students who meet it for the first time in production lose a day to it.

### Note on parallel tool calls

Lesson 5.13 established that `pcntl` is CLI-only. Streaming is one of the few contexts where you have both available at once — a CLI agent can stream *and* run tools in parallel. Worth a sentence, because it makes the CLI agent (Capstone A) a genuinely capable target rather than a toy.

### Key takeaways

- `flush()` after each chunk.
- Measure time-to-first-token; it is the number that justifies the feature.
- Buffering exists at four layers in a web stack — Module 21.

---
═══════════════════════════════════════════════════════════════

## LESSON 7.4 — Streaming with Tools

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Show the user what the agent is doing while it does it.

### Tools work inside the stream

Nothing special is required. The agent handles tool calls in the middle of the stream and continues to the final response. You just receive extra chunk types.

### The full pattern

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Tools\Tool;

$handler = MyAgent::make()
    ->addTool(
        Tool::make(
            'get_server_configuration',
            'retrieve the server network configuration'
        )->addProperty(/* ... */)->setCallable(/* ... */)
    )
    ->stream(
        new UserMessage("What's the IP address of the server?")
    );

foreach ($handler->events() as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        echo "\n- Calling tool: " . $chunk->tool->getName();
        echo "\n- Input: " . json_encode($chunk->tool->getInputs());
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        echo "\n- Tool " . $chunk->tool->getName() . " completed";
        echo "\n- Result: " . $chunk->tool->getResult();
        continue;
    }

    echo $chunk->content;
}
```

Output:

```
Let me retrieve the server configuration.
- Calling tool: get_server_configuration
- Tool get_server_configuration completed
The IP address of the server is: 192.168.0.10
```

### What the chunks carry

Both tool chunks hold the **tool instance**, which is more than a name:

- `$chunk->tool->getName()`
- `$chunk->tool->getInputs()` — the arguments the model chose
- `$chunk->tool->getResult()` — on the result chunk

Having the arguments available is what makes a genuinely informative progress display possible. Not "working…" but "Searching orders for customer 4471".

### The security point, stated firmly

**Do not pipe raw tool inputs and results to end users.**

The CLI example above is a debugging view, and it is perfect for that. In a user-facing product it leaks:

- Internal identifiers and database keys
- SQL queries, revealing your schema
- API endpoints and parameter names
- Anything in an error message

Map to human-readable labels instead:

```php
$labels = [
    'get_order_status'  => 'Looking up your order',
    'search_orders'     => 'Searching your order history',
    'get_refund_policy' => 'Checking the refund policy',
];

foreach ($handler->events() as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        $name = $chunk->tool->getName();
        echo "\n" . ($labels[$name] ?? 'Working on it') . "...\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        continue; // never shown to the user
    }

    echo $chunk->content;
}
```

The allowlist matters: `$labels[$name] ?? 'Working on it'` means a newly added tool degrades to a generic message rather than leaking its internal name. Same reasoning as `only()` over `exclude()` in Lesson 5.8 — allowlists fail safe.

### The UX principle

A progress line for a tool that takes 200 ms is visual noise. A progress line for one that takes four seconds is essential.

Consider showing tool activity only after a short delay, so fast calls stay invisible and slow ones explain themselves. That is the behaviour of every well-designed loading state, and it applies here directly.

### Key takeaways

- Tools stream automatically; you get `ToolCallChunk` and `ToolResultChunk`.
- Chunks carry the tool instance, including the arguments the model chose.
- Never show raw tool inputs or results to end users — map to labels with a safe fallback.
- Show progress for slow tools only.

---
═══════════════════════════════════════════════════════════════

## LESSON 7.5 — Stream Adapters and UI Protocols

**Duration:** 13 minutes
**Type:** Theory with code

### Learning objectives

Connect a Neuron agent to a modern frontend without writing protocol plumbing.

### The problem adapters solve

Your agent produces Neuron chunks. Your frontend speaks a protocol — Vercel AI SDK's data stream format, or AG-UI. Without adapters you hand-write the translation, including message lifecycle events, event formatting and ID tracking, and you rewrite it whenever the protocol moves.

### The design

Adapters are translators between Neuron's internal streaming events and a specific frontend protocol. Pass one to `events()`:

```php
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;

$handler = MyAgent::make()->stream(new UserMessage('What is the square root of 144?'));

$stream = $handler->events(new AGUIAdapter());

foreach ($stream as $line) {
    echo $line;
}
```

Same for Vercel:

```php
use NeuronAI\Chat\Messages\Stream\Adapters\VercelAIAdapter;

$stream = $handler->events(new VercelAIAdapter());
```

**Your agent code does not change.** The adapter sits at the boundary. This is the same interface-driven design as the provider swap in Lesson 3.6, applied to the output side — and it is worth drawing that parallel explicitly, because it shows the architecture is consistent rather than incidental.

### A complete AG-UI endpoint

```php
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;

$input = json_decode(file_get_contents('php://input'), true);

$messages = [];
foreach ($input['messages'] as $message) {
    if ($message['role'] === 'user') {
        $messages[] = new UserMessage($message['content']);
    }
}

$adapter = new AGUIAdapter(
    threadId: $input['threadId'],
    runId: $input['runId'],
);

foreach ($adapter->getHeaders() as $name => $value) {
    header("{$name}: {$value}");
}

$stream = MyAgent::make()->stream($messages)->events($adapter);

foreach ($stream as $line) {
    echo $line;
    flush();
}
```

Four things to point out:

**AG-UI clients POST a `RunAgentInput` payload.** They do not simply open a connection. It carries `threadId`, `runId`, the message history, and more.

**Echo the identifiers back.** Pass `threadId` and `runId` to the constructor so the adapter returns them in `RUN_STARTED` and `RUN_FINISHED`. Omit them and the adapter invents its own — fine for testing, wrong for a real client that expects to correlate the stream with the run it asked for.

**`getHeaders()` gives you the SSE headers.** Send them.

**`flush()` after each line.** Lesson 7.3's warning, and the docs repeat it here for good reason.

### The event mapping

| Neuron chunk | AG-UI events |
|---|---|
| Run lifecycle | `RUN_STARTED`, `RUN_FINISHED` |
| `TextChunk` | `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END` |
| `ReasoningChunk` | `REASONING_START`, `REASONING_MESSAGE_START`, `REASONING_MESSAGE_CONTENT`, `REASONING_MESSAGE_END`, `REASONING_END` |
| `ToolCallChunk` | `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END` |
| `ToolResultChunk` | `TOOL_CALL_RESULT` |

### Two limitations to state honestly

**Server-side tools only.** Tools attached to your agent run on your server, and the client is informed through the `TOOL_CALL_*` events. AG-UI's *frontend-defined* tools — listed in the `tools` field of `RunAgentInput` and executed by the client — are not handled by the adapter.

**No shared state events.** The adapter does not emit `STATE_SNAPSHOT`, `STATE_DELTA` or `MESSAGES_SNAPSHOT`, so AG-UI clients' state-synchronisation features are unavailable through it.

If you are evaluating CopilotKit or a similar AG-UI frontend, know these two gaps before you commit to a design that depends on them.

### Custom adapters

```php
interface StreamAdapterInterface
{
    public function transform(object $chunk): iterable;
    public function getHeaders(): array;
    public function start(): iterable;
    public function end(): iterable;
}
```

Four methods. `transform()` does the work; `start()` and `end()` handle protocol lifecycle; `getHeaders()` supplies transport headers.

You can also extend `SSEAdapter` when you only need to change the transformation.

### The use case worth highlighting

Adapters can push to an external transport such as Pusher. That means an agent running **in a background job** can stream its progress to a browser it has no direct connection to.

This is the answer to a problem that would otherwise seem intractable: long agent runs belong on a queue worker (Lesson 1.4's latency arithmetic, Lesson 5.13's `pcntl` constraint), but a queue worker has no HTTP connection to the user. An adapter pushing to a websocket transport bridges exactly that gap.

Module 21 builds this in Laravel.

### Module 7 assessment

1. Convert one Module 5 agent from `chat()` to `stream()`. Measure time-to-first-token both ways.
2. Add tool progress display with a label allowlist and a safe fallback.
3. Sketch which adapter you would use for your own frontend stack, and identify whether either AG-UI limitation would affect you.

---

**END OF MODULES 6–7**

*Next: Module 8 — Attachments and multimodality. Then Module 9 (MCP) and Module 10 (observability and testing), closing Part II.*
