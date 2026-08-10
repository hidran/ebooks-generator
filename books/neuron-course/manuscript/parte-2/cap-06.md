# Chapter 6 — Structured Output

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch06`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch06), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

## 6.1 Why Structured Output Exists

Getting typed objects out of a language model is the feature that turns an AI demo into a piece of software.

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

Every one of those is a production incident, and Section 1.5 already told you why you cannot test your way out: the same input produces different output.

### What NeuronAI does instead

Two layers, and the separation between them is the design insight:

**Layer 1 — Schema.** You define a PHP class with strict type hints and `#[SchemaProperty]` attributes. NeuronAI generates the corresponding JSON schema from your class and sends it to the model as part of the request. The model is *told* the shape it must produce.

**Layer 2 — Validation.** You attach validation attributes to the properties. NeuronAI parses the response, validates it against those rules, and — critically — **if validation fails it retries, telling the model exactly which properties were wrong.**

You get back an instance of your class. Typed. Validated. Ready to persist.

> Layer 1 tells the model what you want. Layer 2 checks whether you got it, and asks again if you did not.

Most JSON-mode implementations in other ecosystems give you layer 1 only. The retry-with-violations loop in layer 2 is what makes the difference between "usually works" and "works".

### Where this changes your architecture

Structured output is what makes an agent a **component** rather than a chat feature. Once the output is a typed object you can:

- Persist it directly
- Pass it into existing domain services that know nothing about AI
- Assert on its shape in tests — the contract testing from Section 1.5, finally possible
- Put an agent in the middle of a business process with deterministic code on both sides

That last one is the big architectural unlock. Non-deterministic component, deterministic boundary.

### Key takeaways

- Prompt-and-parse fails in a dozen small ways that are untestable in aggregate.
- Two layers: schema generation from PHP classes, then validation with retry.
- A validated typed object is what lets an agent sit inside a normal business process.

## 6.2 Defining the Output Class

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

`description` is what the model reads to decide what goes in the field. `'The user name.'` is adequate. `'The full name of the person placing the order, as written in the source text. Do not infer or complete partial names.'` is better, and eliminates a class of hallucination.

Section 5.4's four-part formula applies, minus the "when to use" part: say what the field is, what format you expect, and what not to do.

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

**These are different from validation rules, and the distinction matters.** Schema constraints go *to the model* — they are instructions in the request. Validation rules (Section 6.5) run *on the response* — they are checks after the fact.

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

## 6.3 Requesting Structured Output

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

That difference in return type is worth pausing on, because you have just spent three chapters typing `->getMessage()->getContent()` and will reach for it here out of habit.

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

| Method | Returns | Use for |
|---|---|---|
| `chat()` | Response → `getMessage()` → text | Conversation |
| `structured()` | An instance of your class | Data extraction |
| `stream()` | Handler → `events()` → chunks | Real-time UI |

Same agent, same tools, same history. Three entry points, each backed by a different node — `ChatNode`, `StructuredOutputNode`, `StreamingNode`. Section 2.3 said node classes are public API; this is the first place you feel it.

### Key takeaways

- `structured($message, MyClass::class)` returns the instance directly.
- `getOutputClass()` sets a default shape but you must still call `structured()`.
- Prefer the per-agent contract.
- Three entry points, three nodes, one agent.

## 6.4 Nested Objects and Typed Arrays

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

::: {.callout .callout-warning}
[Documentation warning]{.callout-title}

The nested-class example on the official page imports `NeuronAI\StructuredOutput\Property` (should be `SchemaProperty`) and `Symfony\Component\Validator\Constraints\NotBlank` / `Valid` — leftovers from before the framework shipped its own validation component. The correct namespace is `NeuronAI\StructuredOutput\Validation\Rules\NotBlank`, as used above. Copying that block verbatim will not compile. Appendix A, items 12 and 13.
:::

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

NeuronAI puts all three specifications into the schema, and the model chooses per element.

This is more powerful than it first looks. It lets you model **documents made of heterogeneous blocks** — the shape behind every modern CMS, page builder and rich-text editor. Asking a model to convert an unstructured document into an ordered list of typed blocks is one of the genuinely strong use cases for this feature.

### Design guidance

**Depth costs accuracy.** Each nesting level is another chance for a malformed shape. Two levels is comfortable, three is pushing it, four means you should extract in stages.

**Extract in stages when the document is large.** One agent produces the top-level structure with identifiers; a second agent fills in the detail per item. Two focused calls beat one call with a schema the model half-satisfies. This is also cheaper, because the second call carries a much smaller schema.

**Model what you need, not what exists.** The source invoice has forty fields. Your process uses six. Extract six. Every field in the schema costs tokens on the request and is another opportunity for a violation.

### Key takeaways

- Type a property as another DTO for nesting; it comes back as an instance.
- `anyOf: [Tag::class]` for arrays of objects; PHP's type system cannot express it alone.
- `anyOf` with several classes models heterogeneous block documents.
- Keep depth shallow; extract in stages; model only the fields you use.

## 6.5 Validation and Retry

This is the most valuable section in the chapter. It is what makes structured output reliable rather than merely likely.

### The mechanism

Validation attributes go on the output class properties. When the model responds, NeuronAI parses the data and checks it. **If one or more properties fail, NeuronAI resends the request to the model with a detailed report of what was wrong**, and repeats until it succeeds or hits the retry limit.

That is the part to emphasise. It is not "validate and throw". It is "validate and tell the model what it got wrong so it can fix it".

You are giving the model a compiler error and asking it to try again — which is, in fact, exactly what it is good at.

### The default

By default NeuronAI retries **once** on validation failure. One extra attempt, with the violations included.

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

The documentation's guidance is sensible: with a less capable model, balance the probability of a valid answer against token consumption. Each retry is a full request — schema, prompt and the violation report — so retries are not cheap. This is Section 1.4's arithmetic appearing in a new place.

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

::: {.callout .callout-warning}
[Corrected example]{.callout-title}

The official example for a custom rule has three small bugs: `respectFormat` is declared with one parameter but called with two, `$this->pattern` is referenced where `$this->format` was defined, and there is no early return after the type violation. The version above is corrected. Appendix A, item 15.
:::

**The message you write is sent to the model on retry.** So write it as an instruction, not a complaint. `'{name} must match the format apps/{id}/show'` gives the model something to act on. `'{name} is invalid'` does not.

That principle is worth stating on its own: **violation messages are prompts.** Every one you write is text a language model will read and try to satisfy.

### Business rules in the validation layer

Validation rules do not have to be format checks:

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

Compare this to putting "refunds must not exceed 500 euros" in the system prompt. One is a request. The other is a constraint. Everything in Section 5.10 about hiding versus instructing applies here in a different form.

### Key takeaways

- Validation failure triggers a retry that tells the model exactly what was wrong.
- Default is one retry; tune with `maxRetries`; `0` disables it.
- Schema constraints instruct; validation rules enforce.
- Violation messages are prompts — write them as instructions.
- Business rules encoded as validation are constraints, not requests.

## 6.6 Structured Output vs Tool Calling

### The confusion

Both involve a JSON schema. Both produce structured data. Both use `#[SchemaProperty]` in the NeuronAI implementation — Section 5.6 used the same attribute for structured tool *input*.

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

Worth naming for symmetry: the same DTO class can serve both directions. Section 5.6's `ObjectProperty(class: Color::class)` and this chapter's `structured($msg, Color::class)` use the same annotated class.

One `Address` class can define what a tool accepts *and* what an agent returns. That is a real benefit of the attribute-based design — one contract, two directions, defined once.

### Key takeaways

- Tool calling is a call; structured output is a return.
- Ask whether the model needs the result to keep reasoning.
- They compose: tools in the middle, structure at the end.
- Never use a tool to deliver the final answer.

## Lab 5 — Extracting Orders from Free Text

**Covers:** output classes, nesting, typed arrays, validation with retry.

### Goal

Order emails arrive as unstructured prose. Turn them into an `Order` object with line items, totals and a delivery address, validated well enough that the next line of code can be `$repository->save($order)`.

### The input

Work with real-shaped messiness. A few examples to test against:

```
Hi, I'd like to order 3 of the blue widgets (SKU BW-1120) at 12.50 each
and one of the large frames, WF-0080, 45 euros. Ship to 14 St James
Street, Leeds, LS1 4DA. Thanks — Jo Turner
```

```
order: 2x BW-1120, 1x WF-0080. total 70. same address as last time.
```

The second one is the interesting case: an ambiguous total, a missing address, and a reference to information the model does not have. Decide what your schema should do about it before you write it.

### The shape

Three classes. The sketch, for you to complete:

```php
class Order
{
    #[SchemaProperty(description: '...', required: true)]
    #[NotBlank]
    public string $customerName;

    #[SchemaProperty(description: '...', required: true, anyOf: [OrderLine::class])]
    #[Count(min: 1)]
    public array $lines;

    #[SchemaProperty(description: '...', required: true)]
    #[GreaterThan(reference: 0)]
    public float $total;

    #[SchemaProperty(description: '...', required: false)]
    public ?Address $deliveryAddress = null;
}
```

`OrderLine` carries an SKU, a quantity and a unit price. `Address` you already have from Section 6.4.

### Requirements

1. **The SKU is a format, not a string.** Use `#[Regex]` so `BW-1120` validates and `blue widget` does not.
2. **Quantities are positive integers.** A model that reads "a few" and writes `0` should be told to try again.
3. **The total must be consistent** with the line items. This one is not expressible as a property rule — decide whether to check it in your own code after the object comes back, or to instruct the model in the description. Try both and see which fails less.
4. **A missing address must not be a fatal error.** Optional, nullable, defaulted.
5. **Descriptions must forbid invention.** "Do not infer prices that are not stated in the text" belongs in a `description`, and its absence is the single most common cause of a plausible, wrong extraction.

### Acceptance criteria

- The clean example produces a fully populated `Order` with two lines.
- The messy example produces an `Order` with a null address and does not throw.
- An input with a malformed SKU triggers a retry, and the retry succeeds. Log the violation to prove the retry actually happened rather than the first attempt being lucky.
- With `maxRetries: 0`, that same input fails. If it does not, your validation is not doing anything.

### Going further

Run the whole lab against a small local model on Ollama, then against a frontier model, with `maxRetries: 3` on both. Count the retries each needs. That number is the most honest model-selection benchmark in this book, because it measures the thing you actually care about: how often the output is usable without a second pass.
