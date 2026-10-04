# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Modules 6 and 7

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^4.0 (verified on 4.0.3), PHP 8.5.

---

> ## ⚠ CORRECTION TO LAB 01
>
> The streaming snippet in the earlier `lab-01-php-puro.md` file used the v2 API:
>
> ```php
> // WRONG for v4 (v2 form: plain strings)
> foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
>     echo $chunk;
> }
> ```
>
> In v4, `stream()` returns the generator itself, and it yields **chunk objects**, not strings. Only some of them carry text, so filter with `instanceof TextChunk`. (The v3 form, `stream()->events()`, no longer exists either: there is no handler.) Correct form:
>
> ```php
> use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
>
> $stream = AssistantAgent::make()
>     ->setThreadId('lab-01')
>     ->stream(new UserMessage($prompt));
>
> foreach ($stream as $chunk) {
>     if ($chunk instanceof TextChunk) {
>         echo $chunk->content;
>     }
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
$response = $agent->setThreadId('demo')->chat(new UserMessage(
    'Extract the order details as JSON with keys name, items, total.'
))->getMessage()?->getContent();

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
        description: 'The age of the user, in years.',
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

$person = MyAgent::make()->setThreadId('demo')->structured(
    new UserMessage("I'm John and I like pizza!"),
    Person::class
);

echo $person->name . ' like ' . $person->preference;
// John like pizza
```

Like `chat()`, `structured()` needs a thread ID bound before it runs: an agent with no ID bound refuses to run. `setThreadId('demo')` is the one-shot form.

`structured()` instead of `chat()`. Second argument is the class. What comes back is **an instance of that class** — not an `AgentState`, not a message. You do not call `getMessage()`.

That difference in return type is worth pausing on in the video, because students have just spent three modules typing `->getMessage()?->getContent()` and will reach for it here out of habit.

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
    ->setThreadId('demo')
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
| `chat()` | `AgentState` → `getMessage()` → text | Conversation |
| `structured()` | An instance of your class | Data extraction |
| `stream()` | A generator of chunks; `getReturn()` → `AgentState` | Real-time UI |

Same agent, same tools, same history. Three entry points, but only two inference nodes. `chat()` and `stream()` both run through `ChatNode`: streaming is the same inference with a different transport, selected by a flag the agent records when the run starts. `structured()` routes to `StructuredOutputNode`, which owns the schema, the parsing and the retry loop. Lesson 2.3 said node classes are public API; here is the first place students feel it — a middleware aimed at `ChatNode` covers chat and streaming alike, and never touches a structured call.

### Key takeaways

- `structured($message, MyClass::class)` returns the instance directly.
- `getOutputClass()` sets a default shape but you must still call `structured()`.
- Prefer the per-agent contract.
- Three entry points, two inference nodes (`ChatNode` for chat and stream, `StructuredOutputNode`), one agent.

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

Use `anyOf` for the schema and `#[ArrayOf]` for the validation:

```php
use NeuronAI\StructuredOutput\Validation\Rules\ArrayOf;

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
    #[ArrayOf(Tag::class)]
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

PHP cannot express `Tag[]` in a type hint, so `anyOf` carries the information the type system cannot. It only shapes the schema, though. The rules on `Tag` (here the `#[NotBlank]` on `$name`) run on each item only when `#[ArrayOf(Tag::class)]` is on the property too; without it a blank tag is accepted on the first attempt, with no violation and no retry. Use both.

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
    #[ArrayOf([TextBlock::class, TableBlock::class, ImageBlock::class])]
    public array $content;
}
```

Neuron puts all three specifications into the schema, and the model chooses per element. To tell the blocks apart on the way back, each specification carries a mandatory `__classname__` discriminator that the model must fill; an element without it cannot be deserialized, and the attempt fails.

This is more powerful than it first looks. It lets you model **documents made of heterogeneous blocks** — the shape behind every modern CMS, page builder and rich-text editor. Asking a model to convert an unstructured document into an ordered list of typed blocks is a genuinely strong use case, and it is one of the better demos you can record for this module.

### Design guidance

**Depth costs accuracy.** Each nesting level is another chance for a malformed shape. Two levels is comfortable, three is pushing it, four means you should extract in stages.

**Extract in stages when the document is large.** One agent produces the top-level structure with identifiers; a second agent fills in the detail per item. Two focused calls beat one call with a schema the model half-satisfies. This is also cheaper, because the second call carries a much smaller schema.

**Model what you need, not what exists.** The source invoice has forty fields. Your process uses six. Extract six. Every field in the schema costs tokens on the request and is another opportunity for a violation.

### Key takeaways

- Type a property as another DTO for nesting; it comes back as an instance.
- `anyOf: [Tag::class]` plus `#[ArrayOf(Tag::class)]` for arrays of objects: the first shapes the schema, the second runs the item rules.
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
$person = MyAgent::make()->setThreadId('demo')->structured(
    messages: new UserMessage("I'm John and I like pizza!"),
    class: Person::class,
    maxRetries: 3
);
```

Zero disables retry — a single attempt:

```php
$person = MyAgent::make()->setThreadId('demo')->structured(
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
| `#[OutOfRange]` | Number must lie within `min`–`max`; `strict` excludes the bounds |
| `#[IsTrue]` / `#[IsFalse]` | Exact boolean |
| `#[IsNull]` / `#[IsNotNull]` | Nullability |
| `#[Json]` | Valid JSON string |
| `#[Url]` | Valid URL; `http` and `https` only unless you pass `schemes:` |
| `#[Email]` | Valid email |
| `#[IPAddress]` | Valid IP (note the capitals — the autoloader is case-sensitive on Linux) |
| `#[ArrayOf]` | Array of a given class or scalar type; what makes item rules run |
| `#[Enum]` | One of `values`, or of a backed enum's cases via `class`; `nullable` flag |
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
$invoice = InvoiceAgent::make()->setThreadId('demo')->structured(
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

Consume a streamed response correctly with the v4 API.

### The API

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()
    ->setThreadId('demo')
    ->stream(new UserMessage('How are you?'));

foreach ($stream as $chunk) {
    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}

// I'm fine, thank you! How can I assist you today?
```

Three steps, and each is a place people go wrong:

**1. `stream()` instead of `chat()`, but the same node.** Both verbs run the same `ChatNode`. `stream()` records a flag on the run that tells the node to call the provider's streaming endpoint instead of the buffered one, and to yield every piece as it arrives. Streaming is a transport choice, not a different execution path — which is why a middleware attached to `ChatNode` covers both, and why everything Module 5 said about tools still holds mid-stream.

**2. `stream()` returns the generator.** There is no second call: you iterate what comes back. Its return type is `Generator`, always, and the generator is lazy: the call itself contacts no provider, and the run starts when your loop asks for the first item. A stream nobody iterates is a run that never happened. Attaching a stream adapter or a channel (Lesson 7.5) changes what the generator yields and where else the output goes, never what `stream()` returns; when there is no loop to write, the eager form is `chat($message, stream: true)`, and Lesson 7.5 comes back to it.

**3. It yields objects, not strings — and not only text.** Filter with `instanceof`. Echoing `$chunk->content` for every item works right up to the first item that is not a text chunk: a tool call, a fragment of tool arguments, or the `InterruptEvent` that marks a paused run. None of those has a `content` property.

> **Older streaming code.** Two earlier shapes of this API survive in tutorials and sample repositories. Neither runs on v4:
>
> ```php
> // v2 form: plain strings
> foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
>     echo $chunk;
> }
>
> // v3 form: a handler, then events()
> foreach (AssistantAgent::make()->stream(new UserMessage($prompt))->events() as $chunk) {
>     echo $chunk->content;
> }
> ```
>
> The first form is the more treacherous of the two, because its outer shape matches the v4 one — you do iterate `stream()` directly — so the broken line looks almost correct. What is wrong is the inside of the loop: every item is an object, and only some of them carry text. Every older tutorial you find will show one of these two forms.

### The chunk types

All under `NeuronAI\Chat\Messages\Stream\Chunks`, all extending `StreamChunk`, all with a `toArray()`:

| Chunk | Contains |
|---|---|
| `TextChunk` | A piece of the response text, in `content` |
| `ReasoningChunk` | Part of the model's reasoning summary — reasoning models only |
| `ToolArgumentChunk` | A fragment of the arguments of a tool call the model is still writing |
| `ToolCallChunk` | A tool call the model decided to make |
| `ToolResultChunk` | The result of that call, once executed |
| `ImageChunk`, `AudioChunk` | Generated media, from models that produce it |

**What you receive depends on your agent and your provider.** No tools attached means no tool chunks — you can iterate expecting only text and reasoning. `ToolArgumentChunk` appears only with providers that stream arguments incrementally; Gemini and Ollama deliver them in one piece and never emit it. That is worth knowing before you write branching logic you do not need.

Besides chunks, the generator can carry two other kinds of object: the `InterruptEvent` that marks a run paused for approval (Module 15), and the progress events a workflow node chooses to yield (Module 14). A loop that handles the chunk types it cares about and ignores everything else is correct by construction, and stays correct when you add tools next month.

### Getting the final message

When the loop ends, the generator's return value is the finished run:

```php
$stream = MyAgent::make()
    ->setThreadId('demo')
    ->stream(new UserMessage('How are you?'));

foreach ($stream as $chunk) {
    // stream to the user
}

$state = $stream->getReturn();
echo $state->getMessage()?->getContent();
```

`getReturn()` is plain PHP — every generator has one, available once it has finished — and here it returns the same `AgentState` that `chat()` would have returned. `getMessage()` is nullable because a run that paused before any inference completed has no assistant message yet; after an ordinary stream it is the complete reply.

This matters more than it looks. You stream to the user *and* get the complete `AssistantMessage` to persist, log, or run through a moderation check. You do not have to reassemble it from chunks yourself, which is exactly the tedious, error-prone thing everyone does on their first streaming implementation.

### Why chunk objects rather than strings

The framework's upgrade notes explain the reasoning, and it is a good design lesson for students.

Streaming raw message instances coupled the application to Neuron's internal message system. Dedicated chunk classes create a boundary: your UI code depends on a small, stable set of chunk types rather than on internal message plumbing. That separation is what made the stream adapter system possible (Lesson 7.5), and it means the internals can evolve without breaking your frontend.

It is a textbook case of introducing a DTO at a layer boundary — worth pointing out to an audience that writes PHP for a living.

### Key takeaways

- `stream()` returns a lazy generator of chunk objects; iterate it, or nothing runs.
- Filter with `instanceof TextChunk` before touching `content`.
- Which chunks you get depends on whether the agent has tools and how the provider streams.
- `getReturn()` gives you the final `AgentState`, with the complete assembled message.

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
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the Repository pattern and when using it is a mistake.';

$start = \microtime(true);
$first = null;

$stream = AssistantAgent::make()
    ->setThreadId('demo')
    ->stream(new UserMessage($prompt));

// No adapter attached, so the generator yields the provider's native chunks.
foreach ($stream as $chunk) {
    if (!$chunk instanceof TextChunk) {
        continue;
    }

    $first ??= \microtime(true);

    echo $chunk->content;
    \flush();
}

$end = \microtime(true);

\printf(
    "\n\n[first token: %.2fs | total: %.2fs]\n",
    ($first ?? $end) - $start,
    $end - $start,
);
```

```bash
php examples/06-streaming.php
```

### The demo to record

Run the same prompt twice — once with `chat()`, once with `stream()` — and put both timings on screen.

Total time: roughly identical. Time to first visible output: 4.1 seconds versus 0.7. Then say the sentence: *the work took the same time; the wait did not.*

Measuring time-to-first-token in the script is worth the four extra lines. It turns an assertion into a number, and students can reproduce it.

Note where the clock stops: at the first `TextChunk`, not at the first item. A reasoning model may spend seconds yielding reasoning chunks before a word of the answer appears, and it is the answer the user is waiting for.

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
use App\Neuron\Tools\ServerConfigurationTool;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolResultChunk;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()
    ->setThreadId('demo')
    ->addTool(new ServerConfigurationTool())
    ->stream(
        new UserMessage("What's the IP address of the server?")
    );

foreach ($stream as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        echo "\n- Calling tool: " . $chunk->tool->getName();
        echo "\n- Input: " . json_encode($chunk->tool->getInputs()) . "\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        echo "- Tool " . $chunk->tool->getName() . " completed";
        echo "\n- Result: " . $chunk->tool->getResult() . "\n";
        continue;
    }

    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}
```

`ServerConfigurationTool` is an ordinary `Tool` subclass in the Module 5 shape: a `$name` of `get_server_configuration`, a description, and an `__invoke()` that returns the configuration. A fixed return value keeps the example free of network access.

Output:

```
- Calling tool: get_server_configuration
- Input: []
- Tool get_server_configuration completed
- Result: {"hostname":"app-01","ip":"192.168.0.10","gateway":"192.168.0.1"}
The IP address of the server is 192.168.0.10.
```

### What the chunks carry

Both tool chunks hold a `ToolCall` in `$chunk->tool` — the record of one invocation, not the executable tool you registered. It is plain data:

- `$chunk->tool->getName()`
- `$chunk->tool->getInputs()` — the arguments the model chose
- `$chunk->tool->getCallId()` — the identifier that pairs a call with its result
- `$chunk->tool->getResult()` — on the result chunk

Having the arguments available is what makes a genuinely informative progress display possible. Not "working…" but "Searching orders for customer 4471". The call ID is what lets a UI turn the "calling" line into a "done" line in place, rather than printing two unrelated rows — and when the model calls the same tool twice in one turn, it is the only thing that tells the two apart.

If your provider streams tool arguments, `ToolArgumentChunk`s arrive before the `ToolCallChunk`, each carrying a `delta` of raw, partial JSON. They exist for a live "the agent is typing a query" preview. Never parse them; wait for the `ToolCallChunk`, which carries the complete inputs.

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

foreach ($stream as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        $name = $chunk->tool->getName();
        echo "\n" . ($labels[$name] ?? 'Working on it') . "...\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        continue; // never shown to the user
    }

    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}
```

The allowlist matters: `$labels[$name] ?? 'Working on it'` means a newly added tool degrades to a generic message rather than leaking its internal name. Same reasoning as `only()` over `exclude()` in Lesson 5.8 — allowlists fail safe. So does the last branch: anything the loop does not recognise is dropped, not printed.

### The UX principle

A progress line for a tool that takes 200 ms is visual noise. A progress line for one that takes four seconds is essential.

Consider showing tool activity only after a short delay, so fast calls stay invisible and slow ones explain themselves. That is the behaviour of every well-designed loading state, and it applies here directly.

### Key takeaways

- Tools stream automatically; you get `ToolCallChunk` and `ToolResultChunk`, and possibly `ToolArgumentChunk` deltas first.
- The chunks carry a `ToolCall` record: name, arguments, call ID and result.
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

An adapter translates NeuronAI's native stream objects into a frontend protocol. You attach it to the agent with `setStreamAdapter()`, and from then on the same `stream()` call yields **protocol events** instead of chunks:

```php
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()
    ->setThreadId('thread_123')
    ->setStreamAdapter(fn (): AGUIAdapter => new AGUIAdapter(threadId: 'thread_123'))
    ->stream(new UserMessage('What is the square root of 144?'));

foreach ($stream as $event) {
    echo json_encode($event) . "\n";
}

// {"type":"RUN_STARTED","runId":"run_...","threadId":"thread_123"}
// {"type":"TEXT_MESSAGE_START","messageId":"msg_...","role":"assistant"}
// {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg_...","delta":"The square root"}
// ...
```

Same for Vercel:

```php
use NeuronAI\Agent\Adapters\VercelAIAdapter;

$agent->setStreamAdapter(fn (): VercelAIAdapter => new VercelAIAdapter());
```

Each item is a `NeuronAI\Workflow\Streaming\ProtocolEvent`: a `type` and a JSON-serialisable `data` array, one object per event on the wire. The built-in adapters live under `NeuronAI\Agent\Adapters`, because they encode agent concepts — tool calls, approvals — while the contract they implement belongs to the workflow layer, where any workflow can use it.

**Your agent code does not change.** The adapter sits at the boundary. This is the same interface-driven design as the provider swap in Lesson 3.6, applied to the output side — the architecture is consistent rather than incidental.

`setStreamAdapter()` takes a factory rather than an instance because an adapter holds the state of one stream: it tracks open messages and tool calls. The agent calls the factory once per execution segment — a run that pauses and is later continued is two segments — so each gets an adapter of its own. Never share one between concurrent streams.

### Protocol events, and where the bytes happen

Notice what the adapter does *not* do: it does not produce `data: ...` lines. The protocol decides the shape of each event; the transport decides how that event becomes bytes. For Server-Sent Events, the HTTP edge frames the stream with `SSEEncoder`:

```php
use NeuronAI\Workflow\Streaming\SSEEncoder;

$lines = SSEEncoder::encode($stream);

foreach ($lines as $line) {
    echo $line; // data: {"type":"TEXT_MESSAGE_CONTENT",...}\n\n
    flush();
}

$state = $lines->getReturn(); // the final AgentState, still reachable
```

`encode()` wraps the generator and forwards its return value, so the final state survives the framing. `SSEEncoder::frame($event)` frames a single event when you need that instead.

The split exists because SSE is only one destination. A websocket, a Redis stream or a broadcast channel wants the *event*, not a framed line, and keeping the two concerns apart is what lets the same adapter feed all of them — the channels at the end of this section depend on it.

### A complete AG-UI endpoint

```php
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Exceptions\InputTranslationException;
use NeuronAI\Exceptions\WorkflowException;
use NeuronAI\Workflow\Streaming\SSEEncoder;

$input = json_decode(file_get_contents('php://input'), true);

$messages = $input['messages'];

// PHP 8.5: array_last() returns null for an empty list - no key juggling.
$last = array_last($messages);

// A resume array or a trailing tool message continues a paused run. Test for
// it first: this endpoint only starts new turns.
if (($input['resume'] ?? []) !== [] || ($last['role'] ?? null) === 'tool') {
    http_response_code(400);
    exit('This endpoint starts new turns; it cannot continue a paused run.');
}

if (($last['role'] ?? null) !== 'user') {
    http_response_code(400);
    exit('A new turn must end with a user message.');
}

// $input['threadId'] came from the browser. Check here that the signed-in
// user owns that thread, before anything is read or written under it.

try {
    $adapter = new AGUIAdapter(
        threadId: $input['threadId'],
        runId: $input['runId'] ?? null,
        messages: $messages,
        state: $input['state'] ?? [],
    );

    $stream = MyAgent::make(workflowId: $input['threadId'])
        ->setStreamAdapter(fn (): AGUIAdapter => $adapter)
        ->stream(new UserMessage((string) $last['content']));

    // The generator is lazy. Pull the first event now, while a refusal can
    // still be an HTTP status.
    $stream->valid();
} catch (InputTranslationException $e) {
    http_response_code(400);
    exit($e->getMessage());
} catch (WorkflowException) {
    http_response_code(409);
    exit('This thread already has a run in flight.');
}

foreach ($adapter->getHeaders() as $name => $value) {
    header("{$name}: {$value}");
}

try {
    foreach (SSEEncoder::encode($stream) as $line) {
        echo $line;
        flush();
    }
} catch (Throwable $e) {
    // RUN_ERROR is already on the wire. The details stay on the server.
    error_log((string) $e);
}
```

Six things to notice:

**AG-UI clients POST a `RunAgentInput` payload.** They do not simply open a connection. It carries `threadId`, `runId`, the message history, the tools the client can run, and shared state.

**The thread is the conversation, on both sides — and the browser chose it.** The adapter requires `threadId` and echoes it in `RUN_STARTED` and `RUN_FINISHED`; the agent is bound to the same value through `make(workflowId:)`, because for an agent the workflow ID *is* the conversation thread: the key its history is stored under, and the one a later continuation uses to find a paused run. That makes `threadId` untrusted input used as a storage key. NeuronAI performs no access control, so authorise the signed-in user for the thread before binding the agent to it; skip that, and anyone who can guess or copy an ID reads and continues someone else's conversation. `runId` is the client's per-request identifier, unrelated to the run ID NeuronAI gives the run itself: pass it and the adapter echoes it back; omit it and the adapter invents one, which is fine for testing and wrong for a real client that expects to correlate the stream with the run it asked for.

**Only the last user message goes to the agent.** The client's copy of the history seeds the adapter's `messages` snapshot; it is not replayed into the model. The agent's own chat history for the thread is the record — which means this endpoint needs a durable message store (Module 4) to remember anything between requests. With the default in-memory store, every request is a fresh conversation. Picking that message out uses `array_last()`, new in PHP 8.5 alongside `array_first()`: it returns the last element of an array whatever its keys, or `null` for an empty one, so a single check rejects both an empty list and one that does not end with a user turn.

**A `resume` array or a trailing tool message is not a new turn.** It is the client *continuing* a paused run — answering an approval, or delivering the results of frontend tools. Test for it first, and on its own: after an approval pause the client's message list still ends with the user's question, so a check on the last role alone would wave a `resume` request through as a fresh one. A continuation goes through `submitInputs()` with the protocol's input translator, not through `stream()`, and it only works if the paused run outlived the request that started it: durable workflow persistence (`setPersistence()`, Module 13) next to the durable message store. Modules 21 and 22 build that side in Laravel. Here, the first 400 makes sure a continuation is never silently misread as a fresh question.

**Until the first frame a failure is an HTTP status; after it, a protocol event.** The adapter's constructor validates the messages it is seeded with — each needs a string `id` — and throws `InputTranslationException`, whose message is written for clients: a 400. The run itself is admitted only when the generator is first pulled, and that is what `$stream->valid()` is for. It advances to `RUN_STARTED` and no further, so a thread that cannot take a new turn — typically one still paused for an approval, which throws `RunInFlightException`, a `WorkflowException` — becomes a 409 instead of a 200 with an empty event stream. From there on, `SSEEncoder::encode()` must be the only thing that iterates the generator. A failure once frames are flowing has already been sent as `RUN_ERROR` by the time the exception reaches your `catch`: log it and stop.

**`getHeaders()` gives you the SSE headers, and `flush()` goes after each line.** Lesson 7.3's warning, and the docs repeat it here for good reason. The headers are also why the adapter is built outside the factory: this request runs a single segment, so the closure hands back the instance the headers came from.

In real code, remember that `json_decode()` returns `null` on a malformed body; validate the payload before trusting any of its keys.

### The event mapping

| NeuronAI output | AG-UI events |
|---|---|
| Run lifecycle | `RUN_STARTED`, `RUN_FINISHED` |
| `TextChunk` | `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END` |
| `ReasoningChunk` | `REASONING_START`, `REASONING_MESSAGE_START`, `REASONING_MESSAGE_CONTENT`, `REASONING_MESSAGE_END`, `REASONING_END` |
| `ToolCallChunk` + `ToolResultChunk` | `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END`, `TOOL_CALL_RESULT` |
| Workflow progress events | `STEP_STARTED`, `STEP_FINISHED`, `ACTIVITY_SNAPSHOT`, `CUSTOM` |
| Run paused for approval | `STATE_SNAPSHOT`, `MESSAGES_SNAPSHOT`, then `RUN_FINISHED` with an `interrupt` outcome |
| Run failed | `RUN_ERROR` |

One consequence of the tool row is easy to miss: the adapter buffers a server-side call and publishes all four `TOOL_CALL_*` events together, once the result exists. An AG-UI client learns about a tool when it has finished, not when it starts — so for a slow tool, the "Checking the refund policy…" line from Lesson 7.4 has to come from somewhere else, such as a progress event.

The other one is the paused run. A stream suspended for approval does not end like a completed one: `RUN_FINISHED` carries `outcome: {type: "interrupt"}` with one `confirmation` interrupt per tool awaiting approval, keyed by the tool call ID. A client that treats every `RUN_FINISHED` as "the answer is complete" will get this wrong. Nor is the outcome the only sign of a pause: a run that stopped to hand a tool to the frontend publishes the call and ends with a plain `RUN_FINISHED`, and it is the call without a result that tells the client there is more to do. Module 15 covers approval itself; Modules 21 and 22 answer these interrupts over HTTP.

Errors reach the wire without their message. `RUN_ERROR` (and the Vercel `error` part) carry a neutral text, never `$exception->getMessage()`, so a stack detail cannot leak to a browser. Override the adapter's protected `errorMessage()` if your clients should know more.

### What the adapter covers, and the gap that remains

**Frontend-defined tools are supported.** The tools a client lists in `RunAgentInput` — executed in the browser, not on your server — can be attached to the agent as deferred tools. When the model calls one, the run suspends, the adapter publishes the call, the client executes it and sends the result back in its next request, and the run continues. That request is a continuation, not a new turn — the trailing tool message the endpoint above turns away — and Module 21 picks it up in Laravel.

**Shared state is echoed, not synchronised.** The adapter carries the `state` and `messages` the client sent and returns them as `STATE_SNAPSHOT` and `MESSAGES_SNAPSHOT` when a run pauses, so the client's picture stays complete. It never emits `STATE_DELTA`, and nothing in the agent writes into AG-UI state. If your frontend design depends on the agent mutating shared state live, that is the gap.

If you are evaluating CopilotKit or a similar AG-UI frontend, know that boundary before you commit to a design that depends on it.

### Custom adapters

```php
namespace NeuronAI\Workflow\Streaming\Adapter;

interface StreamAdapterInterface
{
    public function start(): iterable;
    public function transform(object $chunk): iterable;
    public function end(): iterable;
    public function interrupt(InterruptRequest $request): iterable;
    public function error(Throwable $error): iterable;
}
```

Every iterable yields `ProtocolEvent` objects. `transform()` does the work, one native object in, zero or more events out. `start()` opens the protocol. Exactly one terminal closes each segment, and the agent picks it from the outcome, never your code: `end()` on completion, `interrupt()` when the run pauses — so the client learns what it is waiting for — and `error()` on failure. Nothing resets an adapter between segments, because nothing needs to: the factory builds a new one for each, so an instance only ever holds the state of a single stream, and a paused run and its continuation never share one. Return an empty iterable from any method your protocol has nothing to say in.

A small one, for a homegrown frontend that wants text and tool progress and nothing else:

```php
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Workflow\Interrupt\InterruptRequest;
use NeuronAI\Workflow\Streaming\Adapter\StreamAdapterInterface;
use NeuronAI\Workflow\Streaming\ProtocolEvent;

final class ProgressAdapter implements StreamAdapterInterface
{
    public function start(): iterable
    {
        return [];
    }

    public function transform(object $chunk): iterable
    {
        if ($chunk instanceof TextChunk) {
            yield new ProtocolEvent('delta', ['text' => $chunk->content]);
        }

        if ($chunk instanceof ToolCallChunk) {
            yield new ProtocolEvent('progress', ['tool' => $chunk->tool->getName()]);
        }
    }

    public function end(): iterable
    {
        yield new ProtocolEvent('done');
    }

    public function interrupt(InterruptRequest $request): iterable
    {
        yield new ProtocolEvent('paused', ['request' => $request->jsonSerialize()]);
    }

    public function error(Throwable $error): iterable
    {
        yield new ProtocolEvent('error', ['message' => 'Something went wrong.']);
    }
}
```

The same allowlist instinct as Lesson 7.4, enforced at the protocol boundary: tool results never leave the server because the adapter has no branch for them. Attach it the way you attach the built-in ones: `->setStreamAdapter(fn (): ProgressAdapter => new ProgressAdapter())`. HTTP headers are not part of the interface; if your protocol needs some, declare a `getHeaders()` on the adapter yourself, as `AGUIAdapter` and `VercelAIAdapter` do.

Before writing your own, check whether `AgentChunkAdapter` already fits. It is NeuronAI's native vocabulary: one event per chunk, named after its kind (`text`, `reasoning`, `tool-call`, `tool-result`, …), with the chunk's `toArray()` as payload. When the consumer is your own frontend and speaks no standard protocol, it is usually all you need.

### The use case worth highlighting

Everything so far assumes the code iterating the generator is also the code talking to the browser — a controller holding the HTTP connection open. Often it is not.

A long agent run belongs on a queue worker (Lesson 1.4's latency arithmetic, Lesson 5.13's `pcntl` constraint), and a queue worker has no HTTP connection to the user. Its output would simply be thrown away. **Channels** solve exactly that. The adapter decides the shape of the output; a channel decides where it goes:

```php
use NeuronAI\Agent\Adapters\VercelAIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;

// Inside a queued job: the HTTP request returned long ago.
$state = MyAgent::make(workflowId: $threadId)
    ->setStreamAdapter(fn (): VercelAIAdapter => new VercelAIAdapter())
    ->setChannel(fn (): PusherChannel => new PusherChannel(
        client: $pusher,
        channel: "private-chat.{$threadId}",
    ))
    ->chat(new UserMessage($message), stream: true);
```

`setChannel()` takes a factory for the same reason `setStreamAdapter()` does: a channel serves one segment. And the verb is `chat()`, not `stream()`. With `stream: true` it is the eager form Lesson 7.2 promised: the provider streams, each protocol event goes out through the channel as it is produced, and the call returns the final `AgentState`. No loop in your code at all. Both halves matter. `stream()` would hand the job a generator that delivers nothing until something iterates it; `chat()` without the flag makes a buffered model call, and the channel sees the protocol's opening and closing frames at most, never the text.

The framework ships three channels under `NeuronAI\Workflow\Streaming\Channel`: `PusherChannel` (it takes a configured client from the optional `pusher/pusher-php-server` package, works with Pusher-compatible servers such as Reverb and Soketi, and sends events in batches of ten unless you pass `batchSize: 1`), `RedisChannel` for Redis Pub/Sub, and `CallbackChannel`, which wraps a closure for anything else — a Laravel broadcast, a log, a test. A channel needs an adapter to have anything to send; attach `AgentChunkAdapter` when the browser speaks no UI protocol.

Two properties to design around. A channel failure never fails the run: the agent carries on and reports the transport error as an event. And streamed output is ephemeral — nothing yielded is stored or replayed, so a browser that reconnects mid-run has missed what it missed. The chat history is the record the UI reconciles from (after a reload, `AGUIAdapter::hydrate()` rebuilds what an AG-UI client held from the stored messages and the persisted run); never make correctness depend on a client receiving a streamed item.

Module 21 builds this in Laravel.

### Module 7 assessment

1. Convert one Module 5 agent from `chat()` to `stream()`. Measure time-to-first-token both ways.
2. Add tool progress display with a label allowlist and a safe fallback.
3. Sketch which adapter you would use for your own frontend stack, and decide whether the AG-UI shared-state gap would affect you. Then decide who holds the stream: the HTTP request, or a queue worker with a channel.

---

**END OF MODULES 6–7**

*Next: Module 8 — Attachments and multimodality. Then Module 9 (MCP) and Module 10 (observability and testing), closing Part II.*
