# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Modules 8, 9 and 10

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^4.0 (verified on 4.0.3), PHP 8.5.
> **This batch closes Part II.**

---
═══════════════════════════════════════════════════════════════
# MODULE 8 — ATTACHMENTS AND MULTIMODALITY
═══════════════════════════════════════════════════════════════
---

## LESSON 8.1 — Media as Content Blocks

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Attach images, documents, audio and video to a message using the same mechanism you already know.

### Nothing new to learn

Lesson 4.1 established that a message holds an ordered list of content blocks, not a string. Multimodality is that fact, used.

An image is a block. A PDF is a block. Audio is a block. You add them the same way you add text.

```php
use NeuronAI\Chat\Enums\MediaType;
use NeuronAI\Chat\Enums\SourceType;
use NeuronAI\Chat\Messages\ContentBlocks\ImageContent;
use NeuronAI\Chat\Messages\UserMessage;

$message = new UserMessage('Describe this image');

$message->addContent(
    new ImageContent(
        content: 'https://placehold.co/600x400/EEE/31343C',
        sourceType: SourceType::URL,
        mediaType: MediaType::PNG
    )
);

$state = MyAgent::make()->setThreadId('demo')->chat($message);
echo $state->getMessage()?->getContent();
```

That is the entire API. The elegance is worth pointing out: there is no separate "vision agent", no different method, no alternate provider class. Same agent, same `chat()`, one more block. (`chat()` returns an `AgentState`, so the reply is `getMessage()?->getContent()`, and like every run it needs a thread ID bound first.)

### The block types

```php
use NeuronAI\Chat\Enums\MediaType;
use NeuronAI\Chat\Enums\SourceType;
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;

$message = new UserMessage('Summarize this document');

$message->addContent(
    new FileContent(
        content: base64_encode(file_get_contents(__DIR__ . '/invoice.pdf')),
        sourceType: SourceType::BASE64,
        mediaType: MediaType::PDF,
    )
);
```

```php
use NeuronAI\Chat\Enums\MediaType;
use NeuronAI\Chat\Enums\SourceType;
use NeuronAI\Chat\Messages\ContentBlocks\VideoContent;

$message = new UserMessage('Summarize the content of this lesson.');

$message->addContent(
    new VideoContent(
        content: base64_encode(file_get_contents(__DIR__ . '/lesson_1.mp4')),
        sourceType: SourceType::BASE64,
        mediaType: MediaType::MP4
    )
);
```

The blocks you attach to a user message: `TextContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`. Two more exist and you will meet them without creating them: `ReasoningContent`, which the framework fills from a reasoning model's response, and `SystemContent`, the block type the agent's instructions are made of.

Every media block takes the same three arguments — the content (`content:`, not `source:`), a `SourceType`, and a media type — and `FileContent` adds an optional `filename`. OpenAI, Mistral and Bedrock send it along with the document, so pass it; it costs you nothing. The media type accepts either a `MediaType` case (`NeuronAI\Chat\Enums\MediaType`) or a plain MIME string: the enum covers the common image, document, audio and video formats, and a string handles anything it does not.

Neuron maps each into the correct provider-specific format automatically — which is the whole reason the provider swap from Lesson 3.6 survives multimodality.

> **Documentation note.** The multimodal examples on the official page do not run as printed. They pass the payload as `source:`, but the constructor parameter is `content:` — with named arguments that is a fatal *unknown named parameter* error. They import `NeuronAI\Chat\MediaType`, which lives in `NeuronAI\Chat\Enums`, and never import `SourceType`. And the audio example imports `AudioContent`, then instantiates `FileContent`: use `AudioContent`, with the same arguments as the image block. The listings in this lesson are checked against the source.

### Mixing blocks

A message can hold several blocks of several types:

```php
$message = new UserMessage('Compare these two invoices and list the differences.');

$message->addContent(new FileContent(
    content: base64_encode(file_get_contents('/uploads/inv-a.pdf')),
    sourceType: SourceType::BASE64,
    mediaType: MediaType::PDF,
));

$message->addContent(new FileContent(
    content: base64_encode(file_get_contents('/uploads/inv-b.pdf')),
    sourceType: SourceType::BASE64,
    mediaType: MediaType::PDF,
));
```

Two documents, one question, one call.

### Verify the model, not just the framework

The documentation puts a hint box here, and it earns repeating on camera:

**Before using a content block, verify the model can interpret it.**

The framework will happily attach a video block to a request bound for a text-only model. What comes back is an error from the provider, or worse, a confident answer about content the model never saw.

Model capabilities are not a framework concern and they change monthly. Check the provider's current capability matrix, and fail fast in your own code:

```php
if (!$this->providerSupportsVision()) {
    throw new \RuntimeException('Configured model cannot process images.');
}
```

This matters specifically because of Lesson 3.6. If provider choice is an environment variable, someone will eventually set `NEURON_PROVIDER=ollama` with a text-only local model and point your invoice extractor at it.

### Key takeaways

- Media are content blocks, added with `addContent()`. No special agent, no special method.
- Five block types to attach, one constructor shape (`content:`, `SourceType`, media type); Neuron maps them per provider.
- A message can mix several blocks of several types.
- Verify model capability yourself — the framework will not.

---
═══════════════════════════════════════════════════════════════

## LESSON 8.2 — Source Types and the File ID Optimisation

**Duration:** 11 minutes
**Type:** Hands-on with cost analysis

### Learning objectives

Choose the right source type, and understand why the third one exists.

### The three source types

```php
SourceType::URL     // The provider fetches it
SourceType::BASE64  // You embed the bytes in the request
SourceType::ID      // Reference a file already uploaded to the provider
```

**`URL`** — simplest. The provider fetches the resource. Requires the file to be publicly reachable, which for private business documents usually rules it out, or forces you into signed URLs with short expiry.

**`BASE64`** — you read the file and embed it. Works for anything on your disk, keeps the file private to the request. Costs bandwidth and request size on every call.

**`ID`** — upload the file to the provider's platform once, then reference it by identifier.

### Why `ID` matters more than it looks

```php
use NeuronAI\Chat\Enums\SourceType;
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;
use NeuronAI\Chat\Messages\UserMessage;

$message = new UserMessage([
    new TextContent('Analyze this'),
    new FileContent('file_id_xxxx', SourceType::ID),
]);
```

The constructor also takes an array of blocks, which reads better than a chain of `addContent()` calls when the message is built in one place.

Recall Lesson 1.2: **every iteration of the agent loop re-sends the entire conversation.**

With `BASE64`, a 4 MB PDF is in the message array. Iteration two re-sends it. Iteration three re-sends it. A five-step agent run has uploaded 20 MB.

With `ID`, the file is uploaded once and every subsequent message carries a short string.

What the ID saves is upload bytes and the latency of sending them on every call. It does not save tokens: the provider still reads the file into the model's context on each request, and bills those tokens each time. To pay less for tokens that repeat, use prompt caching (Lesson 3.5). For any document-processing agent that takes more than one step, the smaller request is still not a micro-optimisation; it is the difference between viable and not.

> **Naming inconsistency.** The official `SourceType::ID` example uses `TextBlock` and `FileBlock`, while every other example uses `TextContent` and `FileContent`. There are no `TextBlock` or `FileBlock` classes: the listing above uses the real ones.

### The decision table

| Situation | Source type |
|---|---|
| Public image, single call | `URL` |
| Private file, single call | `BASE64` |
| Private file, multi-step agent | `ID` |
| Same document across many conversations | `ID` |
| Large file (> 1 MB), any agent with tools | `ID` |

The rule of thumb: **if the agent has tools, assume multiple iterations, and prefer `ID`.**

### Practical notes

**File upload is provider-specific.** Neuron abstracts the *reference*, not the upload. You will call the provider's file API directly, or use their SDK, to get an ID. Check your provider's documentation.

**IDs expire.** Providers apply retention policies. Do not persist a file ID as though it were permanent; store your own reference and re-upload when needed.

**IDs are provider-scoped.** A file ID from OpenAI means nothing to Anthropic. This is one of the few places where the portability from Lesson 3.6 genuinely leaks — worth naming honestly rather than glossing over.

**Not every provider accepts every source type for every block — and a combination it cannot express is usually left out of the request, not rejected.** In the v4 source, the OpenAI chat-completions mapper carries text, images and files but has no URL form for `FileContent` and no mapping for audio or video; Mistral's has no base64 form for files; Cohere's ignores `FileContent` altogether; and Ollama's carries text and base64 images only — a URL image throws, a PDF quietly disappears; Anthropic's mapper drops `VideoContent` the same way. Where the block is dropped, the call succeeds; the model simply never sees the document, and answers anyway. That is Lesson 8.1's warning in its sharpest form, and the reason to test every provider you configure with a document whose content the model could not guess.

### Key takeaways

- Three source types: `URL`, `BASE64`, `ID`.
- `ID` avoids re-uploading the payload on every loop iteration — the saving in bytes and latency compounds with loop length. It does not reduce tokens; prompt caching does.
- Upload is provider-specific; IDs expire and are not portable.
- A block the provider cannot map is usually dropped silently — test each provider with a document the model cannot guess.

---
═══════════════════════════════════════════════════════════════

## LESSON 8.3 — Multimodal Cost and Design

**Duration:** 10 minutes
**Type:** Theory

### Learning objectives

Estimate the cost of multimodal work and design around it rather than discovering it on the invoice.

### Images are expensive in tokens

An image is converted into tokens before the model sees it. The count depends on dimensions and the provider's tiling strategy, but a useful mental model:

- A small image (512×512): roughly 250–800 tokens
- A typical screenshot (1920×1080): roughly 1,000–1,700 tokens
- A high-resolution photo: several thousand

**One screenshot can cost more input tokens than the entire text conversation around it.**

Now combine that with Lesson 1.2's re-transmission property and Lesson 8.2's fix, and the architecture becomes obvious: resize before sending to cut the tokens, and use file IDs for anything multi-step to stop re-uploading the bytes.

### Resize before you send

The single highest-leverage optimisation in multimodal work, and it is three lines:

```php
$image = new \Imagick($path);
$image->thumbnailImage(1024, 1024, true);  // bestfit
$image->setImageCompressionQuality(80);
$blob = $image->getImageBlob();
```

Most vision tasks — reading an invoice, identifying an object, describing a scene — do not need 4000 pixels wide. Downscaling to 1024 px often cuts token cost by half or more with no measurable loss in accuracy.

Test it on your own task rather than guessing. Run the same extraction at three resolutions and compare both the output quality and the token count. That comparison makes an excellent five-minute segment.

### PDFs: send the document or extract the text?

A real design decision, and the answer is not always "send the PDF".

**Send the PDF when** layout matters — tables, forms, invoices where position carries meaning, scanned documents with no text layer.

**Extract text first when** the document is text-heavy prose with no meaningful layout. A 40-page report costs far fewer tokens as extracted text than as page images, and for prose the layout adds nothing.

```php
// Cheap path for text-heavy documents
$text = (new \Smalot\PdfParser\Parser())->parseFile($path)->getText();

$message = new UserMessage("Summarise this report:\n\n{$text}");
```

Choosing per document type, rather than applying one strategy to everything, is what separates a considered pipeline from a demo.

### Audio and video

Both are expensive and both have a cheaper decomposition:

**Audio** — transcribe with a dedicated speech-to-text service, then work with text. Cheaper, faster, and the transcript is reusable, searchable and storable. Send raw audio to a multimodal model only when tone, speaker identity or non-speech sound genuinely matters.

**Video** — the same argument, more so. Extract keyframes plus a transcript. Sending full video to a model is the most expensive operation in this entire course, and it is rarely the best answer.

The general principle: **convert to text at the cheapest point in the pipeline, unless the non-text information is the point.**

### Key takeaways

- Images can cost more than the surrounding conversation; resize before sending.
- Extract text from prose PDFs; send the document when layout carries meaning.
- Transcribe audio and decompose video rather than sending raw media.
- Convert to text early unless the non-text signal is what you need.

---
═══════════════════════════════════════════════════════════════

## LESSON 8.4 — Lab: Invoice Extractor

**Duration:** 20 minutes
**Type:** Lab — combines Modules 6 and 8

### Goal

Read an invoice PDF and return a validated, typed `Invoice` object. This is the single most commercially useful thing in Part II, and it is a good capstone for the multimodal module because it combines structured output with an attachment.

### The output classes

**`src/Dto/InvoiceLine.php`**

```php
<?php

declare(strict_types=1);

namespace App\Dto;

use NeuronAI\StructuredOutput\SchemaProperty;
use NeuronAI\StructuredOutput\Validation\Rules\GreaterThan;
use NeuronAI\StructuredOutput\Validation\Rules\NotBlank;

class InvoiceLine
{
    #[SchemaProperty(
        description: 'The description of the line item exactly as written on the invoice.',
        required: true
    )]
    #[NotBlank]
    public string $description;

    #[SchemaProperty(description: 'Quantity of units.', required: true)]
    #[GreaterThan(reference: 0)]
    public float $quantity;

    #[SchemaProperty(description: 'Unit price excluding VAT, in the invoice currency.', required: true)]
    public float $unit_price;

    #[SchemaProperty(description: 'Line total excluding VAT.', required: true)]
    public float $line_total;
}
```

**`src/Dto/Invoice.php`**

```php
<?php

declare(strict_types=1);

namespace App\Dto;

use NeuronAI\StructuredOutput\SchemaProperty;
use NeuronAI\StructuredOutput\Validation\Rules\ArrayOf;
use NeuronAI\StructuredOutput\Validation\Rules\NotBlank;
use NeuronAI\StructuredOutput\Validation\Rules\Regex;

class Invoice
{
    #[SchemaProperty(
        description: 'The invoice number exactly as printed. Do not reformat it.',
        required: true
    )]
    #[NotBlank]
    public string $number;

    #[SchemaProperty(
        description: 'Issue date in ISO 8601 format, YYYY-MM-DD. Convert from whatever '
                   . 'format appears on the document.',
        required: true
    )]
    #[Regex('/^\d{4}-\d{2}-\d{2}$/')]
    public string $issue_date;

    #[SchemaProperty(description: 'The legal name of the supplier issuing the invoice.', required: true)]
    #[NotBlank]
    public string $supplier_name;

    #[SchemaProperty(
        description: 'Three-letter ISO currency code, e.g. EUR, USD, GBP.',
        required: true
    )]
    #[Regex('/^[A-Z]{3}$/')]
    public string $currency;

    #[SchemaProperty(description: 'Total excluding VAT.', required: true)]
    public float $subtotal;

    #[SchemaProperty(description: 'Total VAT amount. Use 0 if the invoice has no VAT.', required: true)]
    public float $vat_amount;

    #[SchemaProperty(description: 'Grand total including VAT.', required: true)]
    public float $total;

    #[SchemaProperty(
        description: 'Every line item on the invoice, in the order they appear.',
        required: true,
        anyOf: [InvoiceLine::class]
    )]
    #[ArrayOf(InvoiceLine::class)]
    public array $lines;
}
```

Point out on camera what the descriptions are doing. `'Do not reformat it'` on the invoice number. `'Convert from whatever format appears'` on the date. `'Use 0 if the invoice has no VAT'` — that last one prevents a null where you declared a float, which is a real failure you would otherwise hit on your first VAT-exempt invoice. And `#[ArrayOf(InvoiceLine::class)]` is what makes the `NotBlank` and `GreaterThan` rules on each line actually run: `anyOf` only shapes the schema (Lesson 6.4).

### The agent

**`src/Agents/InvoiceAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\Dto\Invoice;
use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;

class InvoiceAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function getOutputClass(): string
    {
        return Invoice::class;
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You extract structured data from invoice documents.',
                'You are not an accountant. You transcribe what is on the document; you do not judge it.',
            ],
            steps: [
                'Read every line item, including any that continue onto a second page.',
                'Transcribe values exactly. Do not correct apparent errors on the document.',
                'If a value is genuinely absent, use the documented fallback rather than guessing.',
            ],
            output: [
                'Every monetary value is a number, never a string, and never includes a currency symbol.',
                'Dates are ISO 8601.',
            ],
        );
    }
}
```

### The runner

This lab sends a base64 PDF, so it needs a provider whose mapper carries documents: Anthropic, OpenAI or Gemini. The Ollama mapper sends text and base64 images only; it drops the `FileContent` block without an error and the model invents an invoice from the text prompt alone (Lesson 8.2). Set `NEURON_PROVIDER` accordingly before you run it.

**`examples/07-invoice.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\InvoiceAgent;
use NeuronAI\Chat\Enums\MediaType;
use NeuronAI\Chat\Enums\SourceType;
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;
use NeuronAI\Chat\Messages\UserMessage;

$path = $argv[1] ?? __DIR__ . '/fixtures/invoice.pdf';

if (!\is_file($path)) {
    \fwrite(STDERR, "File not found: {$path}\n");
    exit(1);
}

$message = new UserMessage('Extract the structured data from this invoice.');

$message->addContent(
    new FileContent(
        content: \base64_encode(\file_get_contents($path)),
        sourceType: SourceType::BASE64,
        mediaType: MediaType::PDF,
        filename: \basename($path),
    )
);

$invoice = InvoiceAgent::make()->setThreadId('demo')->structured(
    messages: $message,
    maxRetries: 2,
);

\printf(
    "Invoice %s from %s (%s)\n  Subtotal: %.2f\n  VAT:      %.2f\n  Total:    %.2f\n  Lines:    %d\n",
    $invoice->number,
    $invoice->supplier_name,
    $invoice->issue_date,
    $invoice->subtotal,
    $invoice->vat_amount,
    $invoice->total,
    \count($invoice->lines),
);

foreach ($invoice->lines as $line) {
    \printf("    - %-40s %6.2f × %8.2f = %9.2f\n",
        \substr($line->description, 0, 40),
        $line->quantity,
        $line->unit_price,
        $line->line_total,
    );
}
```

### The verification step nobody teaches

Add this after the extraction, and make a point of it:

```php
$computed = \array_sum(\array_map(fn ($l) => $l->line_total, $invoice->lines));

if (\abs($computed - $invoice->subtotal) > 0.01) {
    \fwrite(STDERR, sprintf(
        "⚠ Line totals sum to %.2f but subtotal reads %.2f — flag for human review\n",
        $computed,
        $invoice->subtotal,
    ));
}
```

**Validation attributes check shape. Only your code can check arithmetic.**

A model can produce a perfectly well-formed `Invoice` in which the numbers do not add up — it misread one digit. No schema constraint catches that. A cross-field consistency check in ordinary PHP does, and it costs four lines.

This is the practical face of Lesson 1.5: a non-deterministic component with a deterministic boundary around it. The DTO is the shape boundary; this check is the semantic one. Every production extraction pipeline needs both.

### Exercise

1. Run the extractor against three real invoices of different layouts. Record the failure rate.
2. Improve the worst-performing field's description. Re-run. Record the change.
3. Add a second cross-field check: `subtotal + vat_amount ≈ total`.

---
═══════════════════════════════════════════════════════════════
# MODULE 9 — MCP: THE MODEL CONTEXT PROTOCOL
═══════════════════════════════════════════════════════════════
---

## LESSON 9.1 — What MCP Is and Why It Matters

**Duration:** 11 minutes
**Type:** Theory

### Learning objectives

Understand the protocol, and be able to explain to a client why it changes the economics of integration.

### The definition

MCP is an open standard, designed by Anthropic, for connecting agents to external service providers — your application database, external APIs, third-party platforms.

Practically: it lets a server expose a set of tools over a defined protocol, and any MCP-capable client can consume them.

### The problem it solves

Before MCP, every integration was bespoke. Want your agent to use Slack? Read the Slack API docs, write the tool classes, handle the auth, maintain it. Then do the same for Jira. Then GitHub. Then your CRM. And every other framework in every other language does the same work again.

MCP inverts this. The **provider** publishes one server. Every client — Neuron, LangChain, a desktop assistant, an IDE — consumes it.

For you as an integrator, the change is: *"two days of work per integration"* becomes *"one line of configuration, if a server exists."*

### In Neuron

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'command' => 'php',
                'args' => ['/home/code/mcp_server.php'],
            ])->tools(),
        ];
    }
}
```

Three details worth pausing on:

**The spread operator.** `...McpConnector::make(...)->tools()` — `tools()` returns an array, and the spread merges it into your list. Forget the `...` and you nest an array inside the tools array, which fails in a way that is not obvious from the error.

**One connector per server.** Create a separate `McpConnector` instance for each server you connect to.

**Discovery is automatic.** Neuron discovers the tools the server exposes. You do not enumerate them. When the agent decides to run one, Neuron generates the appropriate request, calls it on the server, and returns the result to the model.

> **Strict schema conversion.** Discovery converts each tool's input schema into Neuron's tool property types, and it is strict about it. A schema that uses `anyOf`, `oneOf`, `$ref` or a list of types makes `tools()` throw a `ToolException` (`JSON Schema keyword 'anyOf' cannot be represented by the tool property types.`), and a single such tool fails discovery for the whole server. This is not exotic: Python servers built with FastMCP describe every optional parameter as `anyOf: [integer, null]`. `only()` filters before conversion, so an allowlist (Lesson 9.4) also keeps the tools you cannot use out of the way.

The framework's own summary is the line to quote: *it feels exactly like your own defined tools, but you can access a huge archive of predefined actions with one line of code.*

### Where to find servers

- MCP official GitHub: `github.com/modelcontextprotocol/servers`
- MCP-GET registry: `mcp-get.com`

### The honest assessment

**What MCP genuinely gives you:** an enormous catalogue of integrations you did not write, an ecosystem that grows without your involvement, and a standard that is being adopted broadly rather than by one vendor.

**What it costs you:** every one of Lesson 5.1's guarantees. You did not write those tools. You did not review them. You do not control their descriptions, their behaviour, their error handling, or what they do with the arguments the model sends. Lesson 9.4 takes this seriously.

For a course audience, the balanced position is: MCP is excellent for connecting to services you already trust, and requires real diligence for anything else.

### Key takeaways

- An open standard: servers expose tools, any client consumes them.
- One line of configuration replaces a bespoke integration.
- Spread the result; one connector per server; discovery is automatic.
- You inherit code you did not write — which is the whole point and the whole risk.

---
═══════════════════════════════════════════════════════════════

## LESSON 9.2 — Local Servers

**Duration:** 10 minutes
**Type:** Hands-on

### Learning objectives

Connect to a server running on your own machine, and understand the process model.

### Command-style configuration

For a server installed locally on your machine or VM:

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'command' => 'php',
                'args' => ['/home/code/mcp_server.php'],
            ])->tools(),
        ];
    }
}
```

Neuron starts the process and communicates with it over standard input and output.

> **The command is one program path.** `StdioTransport` starts the server directly, with `proc_open([$command, ...$args])`, and no shell in between. So `command` is exactly one program path, taken literally, and everything after it goes in `args`, one element per argument. A path with a space in it, the default on macOS with Laravel Herd, whose PHP lives under `~/Library/Application Support/…`, works as it is: `'command' => PHP_BINARY`. Do not quote it and do not wrap it in `escapeshellarg()`: the quotes become part of the file name and the server never starts (`McpException: Failed to start the MCP server`). The same goes for `~`, `$VAR`, `VAR=value` prefixes and `cd … && …`: a shell would interpret them, this transport does not. Put variables in `env` (below), and on Windows use `npx.cmd` for npm-installed servers, not `npx`.

### The Node ecosystem

Most published servers are Node packages, run with `npx`:

```php
...McpConnector::make([
    'command' => 'npx',
    'args' => ['-y', '@modelcontextprotocol/server-everything'],
])->tools(),
```

`server-everything` is the reference implementation and the right thing to demo with — it exposes examples of every MCP feature and is the fastest way to see discovery working. `-y` runs whatever version is current; outside a demo, pin one after the package name (`package@x.y.z`).

**Note for your PHP audience:** this requires Node on the machine running the agent. Say it plainly, because a PHP developer with no Node installed will hit a confusing failure and assume the framework is broken. Add it to the prerequisites for this module.

### The process model, and its consequences

The server is a **child process** of your PHP process. Three things follow, and they are all worth stating:

**Startup cost per turn.** Each turn builds the connector, which spawns the process, waits for discovery, then works. In a CLI script that is fine. In a web request it is latency on every request.

**It runs with your privileges, but not with your environment.** File system access and network are yours: treat it exactly as you would treat any dependency you `exec()`. The environment is not. The server receives only `HOME`, `LOGNAME`, `PATH`, `SHELL`, `TERM` and `USER` from your process (plus a few Windows variables), so your API keys do not reach it. Whatever it needs goes through the `env` key:

```php
...McpConnector::make([
    'command' => 'php',
    'args' => [__DIR__ . '/crm_mcp_server.php'],
    'env' => ['CRM_API_KEY' => (string) env('CRM_API_KEY')],
])->tools(),
```

`env` wins on a name clash. Proxy settings, `LANG` and `TMPDIR` are in the same position as secrets: pass them if the server needs them.

**It is not for a typical web deployment.** Spawning `npx` per HTTP request is not a production pattern. For web applications, use remote servers (Lesson 9.3), or run agent work on a queue worker where process startup is amortised over a longer job.

### The genuinely interesting case: your own server

You can write an MCP server in PHP:

```php
...McpConnector::make([
    'command' => 'php',
    'args' => ['/home/code/mcp_server.php'],
])->tools(),
```

Why would you? Because it turns your application's capabilities into something **any** agent can consume — your Neuron agent, a colleague's Python agent, an IDE assistant, a desktop client.

Instead of building tools for one agent, you publish a capability surface once. For a company with a valuable internal system, that is a strategic move rather than an implementation detail. Worth flagging as an idea students can take back to their teams.

### Key takeaways

- `command` + `args` for local servers; communication over stdio.
- Most servers are Node packages — Node is a prerequisite.
- The server is a child process: startup cost, your privileges but a reduced environment, unsuitable for per-request web use.
- Writing your own server exposes your system to every agent ecosystem at once.

---
═══════════════════════════════════════════════════════════════

## LESSON 9.3 — Remote Servers

**Duration:** 11 minutes
**Type:** Hands-on

### Learning objectives

Connect to hosted MCP servers over HTTP, with authentication, and choose between the two transports.

### Streamable HTTP

The normal case for hosted servers:

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
                'token' => 'BEARER_TOKEN',
                'timeout' => 30,
                'headers' => [
                    //'x-custom-header' => 'value'
                ]
            ])->tools(),
        ];
    }
}
```

Four keys:

- **`url`** — the server endpoint
- **`token`** — used as the authorization bearer token
- **`timeout`** — seconds; set it deliberately (see below)
- **`headers`** — anything else the server requires

You do not configure the protocol version. The client asks for revision `2025-11-25` in its `initialize` request, takes whatever version the server settles on, and the streamable HTTP transport sends it back as an `MCP-Protocol-Version` header on every later request, which is what current servers expect.

### SSE transport

Set `async => true`:

```php
...McpConnector::make([
    'url' => 'https://mcp.example.com',
    'token' => 'BEARER_TOKEN',
    'timeout' => 30,
    'async' => true
])->tools(),
```

Server-Sent Events keeps a single long-lived HTTP connection over which the server pushes updates.

**Which to use:** whichever the server documents. This is not your choice — it is a property of the server you are connecting to. Read their docs. SSE is the legacy HTTP+SSE transport: it does not recover an expired session and follows no redirects, so where a server offers both, take streamable HTTP.

### Set the timeout deliberately

The default is 30 seconds per request, which is generous. Recall Lesson 1.4's latency arithmetic: a multi-step agent making several MCP calls compounds every timeout.

The key applies to every transport, stdio included, where it bounds each wait for a response from a local server.

If a server routinely takes 25 seconds, either it is unsuitable for interactive use, or your agent belongs on a queue. Do not discover this in production. Measure it during integration and decide.

### Handle the token like a credential

`'token' => 'BEARER_TOKEN'` in the documentation is a placeholder. In real code:

```php
...McpConnector::make([
    'url'     => env('CRM_MCP_URL'),
    'token'   => env('CRM_MCP_TOKEN'),
    'timeout' => 15,
])->tools(),
```

Everything from Lesson 3.7 applies. This is a credential to a system that can probably read or modify business data.

### Discovery happens when the agent runs

An operational detail that surprises people: **`tools()` connects to the server.** Neuron calls your agent's `tools()` hook once per execution segment, not when you call `make()`: every `chat()` turn builds the connector and lists the server's tools again.

That means:

- Building the agent connects to nothing; the first `chat()` does
- A slow server slows every turn, before the model call
- A server that is down makes `chat()` throw instead of answering

If your `tools()` method connects to three remote MCP servers, you have three points of failure between a user's request and the first token of the response. Plan for it: catch failures inside `tools()`, degrade to a reduced tool set, and monitor server availability as part of your own uptime rather than someone else's. A failed connection raises `McpException`, a schema the converter rejects raises `ToolException`:

```php
use NeuronAI\Exceptions\ToolException;
use NeuronAI\MCP\McpConnector;
use NeuronAI\MCP\McpException;

protected function tools(): array
{
    try {
        return [
            ...McpConnector::make([
                'url'     => env('CRM_MCP_URL'),
                'token'   => env('CRM_MCP_TOKEN'),
                'timeout' => 10,
            ])->only(['search_contacts'])->tools(),
        ];
    } catch (McpException|ToolException $e) {
        // Degrade to a reduced tool set: the agent still answers, without the CRM.
        \error_log('CRM MCP server unavailable: ' . $e->getMessage());

        return [];
    }
}
```

### Key takeaways

- `url` + `token` + `timeout` + `headers` for streamable HTTP; add `async => true` for SSE.
- Transport is the server's choice, not yours.
- Discovery happens at every turn, when `tools()` runs — remote servers are availability dependencies.
- Treat tokens as credentials; set timeouts explicitly.

---
═══════════════════════════════════════════════════════════════

## LESSON 9.4 — Filtering and Security

**Duration:** 13 minutes
**Type:** Hands-on with a security discussion

### Learning objectives

Restrict what an MCP server can offer your agent, and reason honestly about the trust you are extending.

### Filtering by tool name

```php
class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            // EXCLUDE: discard certain tools
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
            ])->exclude([
                'tool_name_1',
                'tool_name_2',
            ])->tools(),

            // ONLY: select the tools you want to include
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
            ])->only([
                'tool_name_1',
                'tool_name_2',
            ])->tools(),
        ];
    }
}
```

**Important difference from Lesson 5.8.** Toolkit filters take fully qualified **class names**. MCP filters take **tool name strings**, because the tools are defined remotely and have no PHP classes on your side.

This has a consequence worth stating: there is no static analysis, no IDE completion, and no compile-time error if a name changes. A typo in an `only()` list silently yields fewer tools than you expected. Log the resulting tool count during development.

### Use `only()`. Always.

Lesson 5.8 argued that allowlists beat denylists because toolkits gain tools in framework releases. With MCP the argument is far stronger:

**The server can add tools at any time, without your knowledge, without a deployment on your side.**

You wrote `exclude(['delete_everything'])`. Next month the maintainer adds `purge_all`. Your agent now has it. You did not update a dependency, you did not deploy, you did not review a changelog. The capability arrived over the network.

`only()` is the only defensible option for any MCP server you do not control. Say this firmly in the video — it is one of the few places in this course where there is a genuinely right answer.

### The trust question, stated properly

Every argument from Lesson 5.1 about the tool list being your security boundary assumed you wrote the tools. With MCP you did not.

What you are extending trust to:

- **Tool descriptions you did not write.** And descriptions are instructions the model reads. A malicious or careless description is a prompt injection vector with a legitimate-looking delivery mechanism.
- **Behaviour you cannot inspect.** The tool says it reads a calendar. You cannot verify that is all it does.
- **A dependency that changes without a version bump.** Composer gives you a lock file. An MCP server gives you whatever it is running today.
- **Wherever your arguments go.** If the model passes customer data to a remote tool, that data has left your infrastructure. That is a GDPR question, not a technical preference.
- **Descriptions that change under an allowed name.** `only()` pins names, not descriptions or schemas. The tool you approved on Monday can describe itself differently on Friday.
- **Tool results.** What a tool returns goes into the conversation as text the model reads. A result can carry instructions as easily as a description can: it is a prompt injection channel too.
- **Name collisions.** Two servers, or a server and one of your own tools, exposing the same tool name make the run fail with a `ToolException` before the first provider request. Filter one of them out with `only()` or `exclude()`.

### A workable policy

**Tier 1 — Servers you run.** Your own MCP server, on your infrastructure. Same trust as your own code. Use freely.

**Tier 2 — Servers from vendors you already trust.** Your CRM's official server, where you already have a contract, a DPA and a support channel. Use with `only()`.

**Tier 3 — Everything else.** Community servers, random registry entries, anything unmaintained. Treat as untrusted code. For production: read the source, pin a version, run it yourself rather than connecting to a hosted instance, and combine `only()` with tool approval for anything with side effects.

Prototyping is different — Tier 3 is fine for a spike. The distinction is between "trying it" and "shipping it", and being explicit about that keeps the lesson from sounding like fear-mongering.

### Layer the defences

MCP tools are still tools, so everything from Module 5 applies — including the approval gate. Every discovered tool is an `McpTool`, an ordinary subclass of `Tool`, and `with()` lets you configure one of them by its server-side name before the connector hands it to the agent:

```php
use NeuronAI\MCP\McpConnector;
use NeuronAI\MCP\McpTool;

protected function tools(): array
{
    return [
        ...McpConnector::make([
            'url'   => env('CRM_MCP_URL'),
            'token' => env('CRM_MCP_TOKEN'),
        ])->only([
            'search_contacts',
            'get_contact',
            'update_contact',
        ])->with(
            'update_contact',
            fn (McpTool $tool) => $tool->requireApproval(),
        )->tools(),
    ];
}
```

The allowlist decides which tools exist. `requireApproval()` decides which of them may run without a human: the agent pauses before `update_contact` executes and waits for a decision. Put every tool that writes behind it; Module 15 covers what the agent needs in order to pause and resume. The callback may also return a different tool to use in place of the discovered one, which is the natural place for the last layer: for a truly sensitive integration, proxy the call through your own PHP tool that validates arguments before forwarding, so you have a place to enforce your own rules.

### Module 9 assessment

1. Connect to `server-everything` and log which tools are discovered.
2. Restrict it with `only()` to two tools; verify the agent cannot use a third.
3. For an integration you would actually build, classify the server into a trust tier and write down what you would require before shipping it.

---
═══════════════════════════════════════════════════════════════
# MODULE 10 — OBSERVABILITY, EVALS AND TESTING
═══════════════════════════════════════════════════════════════
---

## LESSON 10.1 — Why You Cannot Debug an Agent

**Duration:** 10 minutes
**Type:** Theory

### Learning objectives

Understand why your existing debugging toolkit fails here, and what replaces each piece of it.

### The problem, in the framework authors' own words

Inspector's documentation for Neuron opens with a passage worth reading aloud, because it is unusually honest for vendor documentation:

Integrating AI agents means you are not only working with functions and deterministic code — you are programming by influencing probability distributions. Same input ≠ output. Reproducibility, versioning and debugging become real problems. Prompting is not programming in the common sense: no static types, small changes break output, long prompts cost latency, and no two models behave the same with the same prompt.

That is Lesson 1.5, restated by the people who built the tool.

### What breaks

**Breakpoints.** You can step through your PHP. You cannot step through the model's decision. The interesting moment — *why did it choose that tool?* — happens on someone else's GPU.

**Reproduction.** "Steps to reproduce" assumes determinism. Re-running the failing input may work fine.

**Logs as you write them.** A log line saying "agent responded" tells you nothing. You need the prompt, the tools offered, the tool selected, the arguments, the result, the tokens and the timing — for every iteration.

**Your mental model of a stack trace.** An agent run is not a call stack. It is a sequence of decisions, and the failure is usually in the reasoning, not in the code.

### What replaces it

| Classical practice | Agentic equivalent |
|---|---|
| Breakpoints | Execution traces |
| Reproduction steps | A dataset of representative inputs |
| Unit tests | Evals with property-based assertions |
| Error rate | Quality score tracked over time |
| Stack traces | Timeline of nodes, tools and tokens |

Three of those five are covered in this module. The other two — datasets and quality tracking — are the same tool viewed over time.

### The one-sentence version

> You cannot debug an agent. You can only observe it and measure it.

Which is why observability was a pillar in Lesson 2.1 rather than an appendix.

### Key takeaways

- Breakpoints, reproduction and equality assertions all assume determinism.
- Traces replace debugging; evals replace unit tests; quality scores replace error rates.
- This is why observability is architectural, not operational.

---
═══════════════════════════════════════════════════════════════

## LESSON 10.2 — Setting Up Observability

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Get full execution traces working: first with a local logger, then with a tracing backend, including the setup that background workers need.

### Events, and who listens to them

Every agent, RAG and workflow dispatches events as it runs: the start and end of each node, every inference, every tool call, every retrieval. They are PSR-14 events — plain objects, one class per kind, all extending `NeuronAI\Observability\ObservabilityEvent` — and each instance owns its own dispatcher. There is no global registry. Observability is whatever you subscribe to that dispatcher.

`subscribe()` works on **Agent, RAG and Workflow** — which is Lesson 2.3 again: they are all workflows, so they all dispatch the same events.

### Start local: a logger

```php
use NeuronAI\Agent\Observability\ToolCalled;
use NeuronAI\Observability\LogListener;
use NeuronAI\Observability\ObservabilityEvent;

$agent = WeatherAgent::make()
    ->subscribe(ObservabilityEvent::class, new LogListener($logger))
    ->subscribe(ToolCalled::class, function (ToolCalled $event): void {
        echo $event->tool->getName() . ' ' . json_encode($event->tool->getInputs()) . PHP_EOL;
    });
```

Matching is by class, with `instanceof` semantics. Subscribing to `ObservabilityEvent::class` receives everything, which is what `LogListener` wants: it writes every event's name and data to any PSR-3 logger. Subscribing to `ToolCalled::class` receives only finished tool calls. Listeners belong to the instance, so they see every run of it, resumed runs included.

Events live in the `Observability` namespace of the module that emits them: `NeuronAI\Agent\Observability` for inference, tool, message and structured-output events, `NeuronAI\Workflow\Observability` for the workflow lifecycle, `NeuronAI\RAG\Observability` for retrieval. Check the `use` line. `subscribe()` takes the class name as a string, so a listener registered against a name that does not exist — `NeuronAI\Observability\Events\ToolCalled`, as older articles print it — raises no error. It simply never fires. When a listener stays silent, the import is the first suspect.

Run it and the loop appears in order: `workflow-start`; then, each node bracketed by a `workflow-node-start` and a `workflow-node-end`, `inference-start`, `inference-stop`, `message-saving`, `message-saved`, `tool-calling`, `tool-called`, a second inference; and finally `workflow-end`. That is already more than "agent responded", and it costs nothing. For timings, token counts and a timeline you can search across thousands of runs, you want a tracing backend.

Two more things belong here. If your application already has a PSR-14 dispatcher, `setEventDispatcher()` forwards every event to it after the agent's own listeners have run. And the older API you will find in articles — `observe()` with an `ObserverInterface` or a `LogObserver` — still works through an adapter, but it is deprecated. Write new code against `subscribe()`.

### Inspector

Inspector is the tracing backend Neuron was built alongside. The maintainers' current monitoring guide documents a second option, Neuron Cloud, a hosted platform that ships as `neuron-core/cloud-sdk` for plain PHP, `neuron-core/neuron-cloud-laravel` and `neuron-core/neuron-cloud-symfony`. When this course was verified none of the three was on Packagist, so check before you plan on it. Both are the same mechanism — a PSR-14 listener subscribed to `ObservabilityEvent::class` — so everything below about subscribing applies to either; this lesson shows Inspector. Neither is required: the framework depends on neither and attaches nothing by itself. You install one, and you subscribe it.

```bash
composer require "inspector-apm/inspector-php:^3.19"
```

You need version 3.19 or later for the `Inspector\Neuron\V4` namespace. The 3.18.x releases contain a subscriber written for a pre-release namespace: it loads, subscribes without complaint and records nothing. `inspector-laravel`, `inspector-symfony` and the other framework packages pull the package in for you; require it in your own `composer.json` anyway, and check that the version that resolves is 3.19 or later.

### The environment variable

```dotenv
INSPECTOR_INGESTION_KEY=nwse877auxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Create a key by registering an app at `app.inspector.dev`.

### Subscribe the listener

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Observability\ObservabilityEvent;

$agent = MyAgent::make()
    ->subscribe(ObservabilityEvent::class, InspectorSubscriber::instance());
```

`InspectorSubscriber::instance()` reads `INSPECTOR_INGESTION_KEY` from the environment. When you have no environment to read, pass the key as its first argument:

```php
InspectorSubscriber::instance('your-ingestion-key')
```

When your framework already owns an `Inspector` instance, as Laravel and Symfony do, construct the listener around it instead — `new InspectorSubscriber($inspector)` — so the agent's segments land inside the transaction the framework opened for the request or the job.

### The setting you do not need, and the mistake to look for

This is the most operationally important section in the chapter.

**An agent you did not subscribe is not traced.** Setting `INSPECTOR_INGESTION_KEY` is not enough: the key configures a subscriber, it does not attach one. A missing subscription produces no traces and no error, so the natural conclusion — "Inspector is broken" — is wrong.

To cover every agent, subscribe where agents are built — a shared base class, a factory, the container — rather than at each call site:

```php
use Inspector\Neuron\V4\InspectorSubscriber;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\AgentState;
use NeuronAI\Observability\ObservabilityEvent;

abstract class MonitoredAgent extends Agent
{
    public function __construct(?string $workflowId = null, ?AgentState $state = null)
    {
        parent::__construct($workflowId, $state);

        $this->subscribe(ObservabilityEvent::class, InspectorSubscriber::instance());
    }
}
```

Keep the parent's two-parameter signature and forward it. `make()` passes its arguments straight to the constructor, and an agent's workflow ID is its conversation thread ID, so `MyAgent::make(workflowId: $threadId)` keeps working.

What you do not configure is flushing. Older material tells you to enable `autoFlush` for long-running processes — queue workers, Swoole, RoadRunner — where events would pile up in memory waiting for an end of request that never comes. There is no such option. When the subscriber opened the transaction itself, it sends the trace as soon as the workflow ends, run by run. When the host application opened it, the subscriber leaves flushing to the host.

Given that Lesson 1.4 pushes long agent work onto queues, and Lesson 5.13 requires CLI for parallel tools, **most serious Neuron deployments run in workers — and in a worker the failure to look for is an agent that was never subscribed.**

### Framework-specific packages

If you are integrating into Laravel or Symfony, add the framework package (`inspector-laravel`, `inspector-symfony`) for better data collection. Not required, but recommended — it correlates the agent trace with the HTTP request, the queries and the queue job around it, which is what you actually want when diagnosing a production incident. Hand its `Inspector` instance to the subscriber, as shown above, so the two end up in the same trace.

Module 23 covers this in the Laravel context.

::: {.callout .callout-warning}
[Namespace drift]{.callout-title}

Four names for this component appear across the ecosystem, and only the first works with the Neuron this course uses:

- `Inspector\Neuron\V4\InspectorSubscriber` — the PSR-14 listener this lesson subscribes
- `Inspector\Neuron\InspectorObserver` — same package, but written for the observer API of older Neuron versions
- `NeuronAI\Observability\InspectorObserver` — from older versions of the framework; it no longer exists
- `NeuronAI\Observability\AgentMonitoring` — older articles, and still in some structured-output examples

The second is the dangerous one: it resolves, and wiring it through the deprecated `observe()` looks as if it works. This is the single most likely place to copy a `use` statement from the wrong version.
:::

### Key takeaways

- Every agent, RAG and workflow dispatches PSR-14 events; `subscribe()` a listener to see them.
- `LogListener` for local visibility, costs nothing.
- Inspector (or Neuron Cloud) is optional: `composer require "inspector-apm/inspector-php:^3.19"`, set the key, subscribe `InspectorSubscriber`.
- A listener subscribed to a class that does not exist never fires and nothing errors; events live in `NeuronAI\Agent\Observability`, `NeuronAI\Workflow\Observability` and `NeuronAI\RAG\Observability`.
- Nothing is attached automatically. Subscribe in a base class or factory so no agent is missed.
- No `autoFlush` to set: the subscriber sends each run's trace when the workflow ends.
- Use `Inspector\Neuron\V4\InspectorSubscriber`; the other three names belong to older versions.

---
═══════════════════════════════════════════════════════════════

## LESSON 10.3 — Reading a Trace

**Duration:** 13 minutes
**Type:** Hands-on — screen recording

### Learning objectives

Turn a trace into a diagnosis. This lesson is mostly screen capture; the value is in the narration.

### What a trace shows

Every inference step, every tool call, every retrieval — with arguments, results, token counts and timings.

Run the Lab 3 weather agent with Inspector subscribed and walk through the timeline:

```
▸ WeatherAgent                                        4.82s   3,641 tokens
  ├─ ChatNode                          1.31s     892 in / 84 out
  ├─ ToolNode: get_current_weather     0.42s
  │    input:  {"latitude": 45.0703, "longitude": 7.6869}
  │    output: {"temperature_2m": 14.2, ...}
  ├─ ToolNode: get_current_weather     0.38s
  │    input:  {"latitude": 45.4642, "longitude": 9.19}
  ├─ ChatNode                          1.44s   1,203 in / 61 out
  ├─ ToolNode: mean                    0.01s
  └─ ChatNode                          1.26s   1,310 in / 91 out
```

### The four questions to answer from a trace

Teach it as a procedure, not as "look around":

**1. How many model calls?**
Three here. Lesson 1.4's cost model, made visible. If you expected one, you have a design problem.

**2. Which tools, with which arguments?**
This is where wrong-tool and wrong-argument bugs are visible. The model called `get_current_weather` with Turin's coordinates — so it derived them correctly. If it had passed a city name as a string, your property description (Lesson 5.4) needs the worked example.

**3. Where did the time go?**
Model calls: 4.01s. Tools: 0.81s. The model is the bottleneck, so optimisation means fewer iterations, not faster tools. If the ratio were reversed, you would cache the tool.

**4. Where did the tokens go?**
892 → 1,203 → 1,310 input tokens. Growing, because the conversation grows. Exactly the compounding from Lesson 1.4, now measured rather than estimated.

### Diagnosing from traces: three patterns

**The same tool called five times with near-identical arguments.**
The model does not believe it got an answer. Your tool's return value is ambiguous, or its description does not match what it does. Fix the tool, not the run limit.

**A long gap before the first tool call.**
The model spent time deciding. Usually too many tools, or overlapping descriptions. Filter (Lesson 5.8) or add `ToolSearchMiddleware`.

**Input tokens far higher than expected on the first call.**
Your tool schemas are large. Count your attached tools. Each one's full schema is in every request.

### The exercise that teaches this best

Do not just show a healthy trace. **Break something and read the trace together.**

Change `get_current_weather`'s description to `'Gets the weather.'` and re-run. The trace shows the model answering with no tool call at all. Then narrate: *the code is identical; the only change is a string; the trace shows the model never even considered the tool.*

That is the moment Lesson 5.4 becomes real, and it is worth ten minutes of recording.

### Key takeaways

- Four questions: how many calls, which tools with which arguments, where the time went, where the tokens went.
- Repeated identical calls mean an ambiguous tool, not a low limit.
- Read a broken trace on camera; it teaches more than a healthy one.

---
═══════════════════════════════════════════════════════════════

## LESSON 10.4 — Evals: PHPUnit for Non-Deterministic Systems

**Duration:** 15 minutes
**Type:** Hands-on

### Learning objectives

Build an evaluator and understand the mental shift from assertion to measurement.

### The framing that makes it click

Think of an eval as **PHPUnit for a service that is not deterministic.**

A unit test knows the expected output because the function is deterministic. An agent asked the same question twice may give two answers that are both correct and differently worded. You cannot assert equality.

What you can do: define a dataset of realistic inputs, run the agent against each, and assert that the output meets criteria — contains keywords, stays within a length range, matches a pattern, or passes judgement from another agent acting as reviewer.

### Configure the project

Keep evaluators out of production code:

```json
"autoload-dev": {
    "psr-4": {
        "App\\Evaluators\\": "evaluators/"
    }
},
```

```bash
mkdir -p evaluators/datasets
composer dump-autoload
```

`autoload-dev` is the right choice — evaluation code is for development and QA, and should not ship.

### Generate an evaluator

```bash
# Unix
vendor/bin/neuron make:evaluators App\\Evaluators\\AgentEvaluator

# Windows
.\vendor\bin\neuron make:evaluators App\Evaluators\AgentEvaluator
```

The command is `make:evaluators`, plural, on every platform. The official docs show `make:evaluator` on the Unix tab; that command does not exist.

> **The generator and `autoload-dev`.** `make:evaluators` resolves the target directory from the PSR-4 prefixes in `composer.json`. On neuron-ai 4.0.2 it read the `autoload` section only, so in a project whose `autoload` maps `App\` to `app/` — every Laravel application — `App\Evaluators\AgentEvaluator` matched that production prefix and the file landed in `app/Evaluators/`, not in `evaluators/`. Since 4.0.3 it reads `autoload-dev` as well, merged after the production prefixes, and the most specific prefix wins: with `App\` in `autoload` and `App\Evaluators\` in `autoload-dev`, as above, the file lands in `evaluators/`. Pass the fully qualified name, and check where the file landed before you build on it; if no prefix matches, the command warns and writes under the current directory. The docs' own example, `App\Neuron\Evaluators\AgentEvaluator`, adds a namespace that matches neither prefix. If the file lands in the wrong place, move it into `evaluators/`, or write evaluators by hand — the structure below is all there is to them.

### The three-method structure

```php
namespace App\Evaluators;

use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;
use NeuronAI\UniqueIdGenerator;

class AgentEvaluator extends BaseEvaluator
{
    /**
     * 1. Get the dataset to evaluate against
     */
    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(__DIR__ . '/datasets/dataset.json');
    }

    /**
     * 2. Run the agent logic being tested
     */
    public function run(array $datasetItem): mixed
    {
        $state = MyAgent::make()
            ->setThreadId(UniqueIdGenerator::generateId('eval_'))
            ->chat(new UserMessage($datasetItem['input']));

        return $state->getMessage()?->getContent() ?? '';
    }

    /**
     * 3. Evaluate the output against expected results
     */
    public function evaluate(mixed $output, array $datasetItem): void
    {
        $this->assert(
            new StringContains($datasetItem['reference']),
            $output,
        );
    }
}
```

Load a dataset, run each item, assert on the output. That is the whole model, and its simplicity is a feature — the shape is familiar to anyone who has written a data provider in PHPUnit.

Two details in `run()`. `chat()` returns the final `AgentState`, and its `getMessage()` is nullable, so the evaluator hands the assertion an empty string rather than a null — a string assertion given anything but a string reports the item as an error, not as a failure. And whatever `run()` returns is what `evaluate()` receives as `$output`: a string here, a conversation trajectory in Lesson 10.5.

Bind a thread ID in `run()`, as above. An agent has no thread ID until you give it one, and `chat()` throws without it; a fresh ID per item also means no item sees another item's conversation.

### Datasets

**`ArrayDataset`** — inline, good for a handful of cases:

```php
public function getDataset(): DatasetInterface
{
    return new ArrayDataset([
        [
            'input' => 'Hi',
            'reference' => 'help'
        ]
    ]);
}
```

**`JsonDataset`** — a file, which is what you want in practice:

```php
return new JsonDataset(__DIR__ . '/datasets/dataset.json');
```

**There is no prescribed format.** The evaluator loads a list of test cases; the keys are yours. `input` and `reference` are conventions in the examples, not requirements. You can implement `DatasetInterface` to load from anywhere — a database, a CSV, production logs.

That last option is the one worth highlighting: **build your dataset from real failures.** Every time a user reports a bad answer, add the input to the dataset. Your eval suite becomes a regression suite for exactly the things that actually broke.

### Key takeaways

- Evals are PHPUnit for non-deterministic services.
- Three methods: `getDataset()`, `run()`, `evaluate()`.
- `ArrayDataset` for a few cases, `JsonDataset` for real suites, `DatasetInterface` for anything else.
- Grow the dataset from real reported failures.

---
═══════════════════════════════════════════════════════════════

## LESSON 10.5 — Assertions and AI as a Judge

**Duration:** 16 minutes
**Type:** Hands-on

### Learning objectives

Choose assertions that measure what you care about, including the case where only another model can judge.

### The built-in assertions

```php
$this->assert(new StringContains('positive'), $output);
$this->assert(new StringContainsAll(['hello', 'world']), $output);
$this->assert(new StringContainsAny(['success', 'completed']), $output);
$this->assert(new StringStartsWith('Hello'), $output);
$this->assert(new StringEndsWith('!'), $output);
$this->assert(new StringLengthBetween(10, 100), $output);
$this->assert(new MatchesRegex('/^\d{3}-\d{2}-\d{4}$/'), $output);
$this->assert(new IsValidJson(), $output);
```

Two more interesting ones:

**`StringDistance`** — Levenshtein similarity:

```php
$this->assert(new StringDistance(
    reference: 'expected text',
    threshold: 0.5,   // minimum similarity score
    maxDistance: 50   // maximum allowed edits
), $output);
```

**`StringSimilarity`** — semantic similarity via embeddings:

```php
use NeuronAI\Evaluation\Assertions\StringSimilarity;
use NeuronAI\RAG\Embeddings\OpenAIEmbeddingsProvider;

$this->assert(new StringSimilarity(
    reference: 'The quick brown fox',
    embeddingsProvider: new OpenAIEmbeddingsProvider(key: 'YOUR_KEY', model: 'text-embedding-3-small'),
    threshold: 0.6
), $output);
```

The distinction is worth drawing out. `StringDistance` measures *character* similarity — "colour" and "color" are close. `StringSimilarity` measures *meaning* — "the cat sat on the mat" and "a feline was resting on the rug" are close despite sharing almost no characters.

For evaluating natural-language output, semantic similarity is almost always the one you want. It costs an embedding call per assertion, which is cheap.

This is also the first appearance of the embeddings component, which is the whole of Module 12. Flag the connection.

### AI as a judge

Some qualities cannot be measured with string operations. Is the answer polite? Helpful? Grounded in the source, or hallucinated?

For these, use another agent as the evaluator:

```php
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\AgentInterface;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Evaluation\Assertions\AgentJudge;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\UniqueIdGenerator;

class AgentJudgeEvaluator extends BaseEvaluator
{
    protected AgentInterface $judge;

    public function setUp(): void
    {
        $this->judge = Agent::make()
            ->setAiProvider(new Anthropic(/* ... */))
            ->setInstructions('You are an expert evaluator for customer support responses.');
    }

    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(/* ... */);
    }

    public function run(array $datasetItem): mixed
    {
        return MyAgent::make()
            ->setThreadId(UniqueIdGenerator::generateId('eval_'))
            ->chat(new UserMessage($datasetItem['input']))
            ->getMessage()
            ?->getContent() ?? '';
    }

    public function evaluate(mixed $output, array $datasetItem): void
    {
        $this->assert(new AgentJudge(
            judge: $this->judge,
            criteria: 'Response should be helpful, polite, and address the customer\'s question directly',
            threshold: $datasetItem['threshold']
        ), $output);
    }
}
```

The judge is an ordinary agent configured fluently: `setAiProvider()` and `setInstructions()` are part of `AgentInterface`, so this works on any agent, not just a bare `Agent::make()`. The assertion asks the judge for a structured score between 0 and 1 with its reasoning, so the judge's model must support structured output.

> **A typo to avoid.** The official example for this block misspells `Anthropic` as `Antrhopic`. Copy it and the class does not resolve.

### The specialised judges

Neuron ships judges for the recurring evaluation questions, in `NeuronAI\Evaluation\Assertions\Judges`:

**`FaithfulnessJudge`** — is the output grounded in the provided context, or did it hallucinate?

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedContext,
    threshold: 0.7
), $output);
```

`context` is a string: join the retrieved documents' content before you pass it.

**This is the single most important assertion for RAG systems**, and it is the reason to introduce evals before Module 11 rather than after. A RAG system that answers fluently from information it invented is worse than one that says "I don't know". Faithfulness is how you measure that, and you cannot measure it with string matching.

**`CorrectnessJudge`** — does it match the expected answer?

```php
$this->assert(new CorrectnessJudge(
    judge: $this->judge,
    expected: $datasetItem['expected_answer'],
    threshold: 0.7
), $output);
```

**`RelevanceJudge`** — does it actually address the question? It takes the original `question` alongside the judge.

**`HelpfulnessJudge`** — is it useful and actionable?

**`TaskCompletionJudge`** — did the agent accomplish a stated `goal` over a whole conversation? This one reads a trajectory rather than a single answer; the next section shows where trajectories come from.

### Name the metric

Every `assert()` records a score, and by default the score is filed under the assertion's class name. Pass a third argument to name the metric yourself:

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedContext,
), $output, 'faithfulness');
```

The label is what the report aggregates by: the console summary and the JSON output show average, minimum, maximum and count per label. It matters as soon as you have two assertions of the same class measuring different things — two `AgentJudge`s, one for tone and one for accuracy, are indistinguishable without it — and it gives you metric names that survive refactoring the assertion that produces them.

### Evaluating what the agent did, not only what it said

A string assertion sees the final answer. For an agent with tools that is often the least interesting part: the question is whether it called the right tool, with the right arguments, and did not call the one it should have left alone.

For that, `run()` drives the agent through a `Conversation` and returns its `Trajectory` — a read-only view over the messages the run produced:

```php
use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\Assertions\Trajectory\ToolWasCalled;
use NeuronAI\Evaluation\Assertions\Trajectory\ToolWasNotCalled;
use NeuronAI\Evaluation\Conversation\Conversation;

public function run(array $datasetItem): mixed
{
    return Conversation::make(WeatherAgent::make())
        ->withTurns([$datasetItem['input']])
        ->run();
}

public function evaluate(mixed $trajectory, array $datasetItem): void
{
    $this->assert(new ToolWasCalled('get_current_weather', ['latitude' => 45.07]), $trajectory);
    $this->assert(new ToolWasNotCalled('delete_forecast'), $trajectory);
    $this->assert(new StringContains('Turin'), $trajectory->finalAnswer());
}
```

`ToolWasCalled` takes an optional argument constraint — a subset of the inputs, as here, or a closure. `TrajectoryMatches` asserts on the sequence of tool names, strictly or loosely. `ToolWasApproved` and `ToolWasRejected` check what happened at the approval gate, and `withApprovals()` on the conversation plays the human when the agent pauses (Module 15). String assertions apply to `finalAnswer()`; every judge accepts the trajectory itself and reads its transcript.

This is where evals for agents stop being evals for chatbots. An agent that gives the right answer after calling a tool it should never have touched has passed a string assertion and failed you.

### Two cautions about judges

**The judge is also non-deterministic.** You are measuring a probabilistic system with a probabilistic instrument. Thresholds absorb this, but do not treat a judge score as ground truth. Track it over time and look for movement, not absolute values.

**Judges cost money.** Every judged assertion is an extra LLM call. A 200-item dataset with three judged assertions is 600 extra calls per run. Do not economise by giving the judge a weaker model than the agent: a weaker judge scores more noisily, and you end up tuning against the noise. Control the cost instead with `--cache` (Lesson 10.6), with a sample of the dataset on pull requests, and with string or trajectory assertions wherever they are enough. Whatever judge you use, check its scores against a handful of answers you have graded by hand.

### Custom assertions

```php
use NeuronAI\Evaluation\Assertions\AbstractAssertion;
use NeuronAI\Evaluation\AssertionResult;

class GreaterThanAssertion extends AbstractAssertion
{
    public function __construct(
        private readonly float $threshold
    ) {}

    public function evaluate(mixed $actual): AssertionResult
    {
        if (!is_numeric($actual)) {
            return AssertionResult::fail(
                0.0,
                'Expected numeric value, got ' . gettype($actual),
            );
        }

        if ($actual > $this->threshold) {
            return AssertionResult::pass(1.0);
        }

        return AssertionResult::fail(
            0.0,
            "Expected {$actual} to be greater than {$this->threshold}",
        );
    }
}
```

Note `AssertionResult::pass(1.0)` and `fail(0.0)` — assertions return a **score**, not a boolean. That is what allows partial credit and threshold-based judging, and it is the design detail that makes the whole module a measurement system rather than a pass/fail gate.

### Key takeaways

- Ten built-in string assertions; `StringSimilarity` for meaning, `StringDistance` for characters.
- Five judges: faithfulness, correctness, relevance, helpfulness, task completion.
- Name the metric with `assert()`'s third argument; the report aggregates by label.
- Trajectory assertions check which tools ran, with which arguments — the part a final answer hides.
- `FaithfulnessJudge` is the essential one for RAG — introduce it before Module 11.
- Judges are non-deterministic and cost money; control the cost with `--cache`, sampling and cheaper assertions, not with a weaker judge.
- Assertions return scores, not booleans.

---
═══════════════════════════════════════════════════════════════

## LESSON 10.6 — Running Evals: Output, Parallelism and CI

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Run the suite, route results where you need them, and make evals fast enough to actually use.

### Running

```bash
# Unix
vendor/bin/neuron evaluation --path=evaluators

# Windows
.\vendor\bin\neuron evaluation --path=evaluators
```

The command is `evaluation`, singular, and it accepts the directory either as `--path=evaluators` or as a plain positional argument — both forms in the official docs work. If your evaluators autoload through anything other than Composer's autoloader, add `--autoload-file=bootstrap.php`. `vendor/bin/neuron --help` lists every command your installed version has.

The command exits with a non-zero status if any item fails. Keep that in mind for CI, below.

### Output drivers

Create `evaluation.php` in the project root:

```php
<?php

use NeuronAI\Evaluation\Output\ConsoleOutput;
use NeuronAI\Evaluation\Output\JsonOutput;

return [
    'output' => [
        ConsoleOutput::class,
        new JsonOutput(__DIR__ . '/evaluation-results.json'),
    ],
];
```

Note the shape: `output` is a **list**, not a map of class to options. `EvaluationOutputResolver` accepts either a class-string or an already-constructed instance. There is no reflection-based option mapping: a driver that needs an option, like `JsonOutput`'s file path, is handed over ready-made. A class-string is built by the optional `resolver` entry of this file — a `callable(class-string): object`, typically the application's container — or with a plain `new` when there is none, in which case a driver whose constructor needs arguments is refused.

Multiple drivers run simultaneously — console for the developer, JSON for CI to consume.

Without a config file, the system defaults to `[ConsoleOutput::class]`. (Older material shows `ConsoleDriver`, `JsonDriver` and an options-map config such as `ConsoleDriver::class => ['verbose' => true]`: those names and that shape do not exist in 4.x.)

### Custom output: the pattern that makes evals a business tool

```php
namespace App\Neuron\Evaluations;

use NeuronAI\Evaluation\Contracts\EvaluationOutputInterface;
use NeuronAI\Evaluation\Runner\EvaluationReport;

class DatabaseOutput implements EvaluationOutputInterface
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly string $table = 'evaluations'
    ) {}

    public function output(EvaluationReport $report): void
    {
        $results = $report->getResults();

        $stmt = $this->pdo->prepare(
            "INSERT INTO {$this->table} (passed, failed, success_rate, total_time, created_at, updated_at)
             VALUES (?, ?, ?, ?, NOW(), NOW())"
        );

        $stmt->execute([
            $results->getPassedCount(),
            $results->getFailedCount(),
            $results->getSuccessRate(),
            $report->getDuration(),
        ]);
    }
}
```

A driver receives the `EvaluationReport` for the whole run: one report per evaluator, the start and finish instants, and `getResults()`, which flattens every evaluator's items into one set of counts. For per-metric history, `getResults()->getScoreStatisticsByLabel()` returns the average, minimum, maximum and count for each label from Lesson 10.5 — one row per metric per run is the table you will want to chart.

Register it by class and let a resolver build it:

```php
return [
    'resolver' => fn (string $class): object => match ($class) {
        DatabaseOutput::class => new DatabaseOutput(new \PDO(/* ... */), 'evaluations'),
        default => new $class(),
    },
    'output' => [
        ConsoleOutput::class,
        DatabaseOutput::class,
    ],
];
```

Do not write `new DatabaseOutput(new \PDO(...))` in the list. `evaluation.php` is loaded before the first item runs, so a driver built there holds a live connection when `--concurrency` forks, and every child inherits it. The runner builds the output drivers only after all runs have finished, so a driver listed as a class-string, with the resolver supplying its connection, never has a connection at fork time. Connecting inside `output()` works as well.

**Why this matters beyond engineering.** Persisting the success rate on every run gives you a quality metric over time. You can chart it. You can show it to a stakeholder. You can answer "did last week's prompt change make things better or worse?" with a number instead of an opinion.

That is the transition from evals as a developer convenience to evals as evidence. For anyone selling AI work to a business, it is the difference between "trust me" and a graph.

### Parallel execution

Most eval time is spent waiting on the provider. Run items concurrently:

```bash
vendor/bin/neuron evaluation path/to/evaluators --concurrency=3
```

The documented example: one 2-second LLM call per item over a 100-item dataset drops from roughly 200 seconds to roughly 66.

**Requirements** — the same set as Lesson 5.13:

```bash
composer require --dev spatie/fork
```

plus the `pcntl` and `posix` extensions (Linux and macOS; not Windows; `posix` is required since 4.0.3). If any of them is missing, the command prints a notice and falls back to sequential, so the same command works everywhere.

**Choosing a level.** Every item in flight is an active provider request. Start at 3–5 and increase while you avoid rate limits. Rate-limit errors show up as test failures, so if failures appear when you raise concurrency, lower it before you go hunting for a bug in your agent.

### Four things to know about parallel runs

**Results are unaffected.** Items are independent, order is preserved, the report is identical.

**State is not shared.** Each item sees the state as of `setUp()`. Side effects from one item are invisible to others. If your evaluator accumulates state across items, run it sequentially.

**Outputs must be serializable.** The return value of `run()` crosses a process boundary via `serialize()`. A closure or an open connection cannot cross; assertion results survive but the reported output becomes a placeholder.

**Timing reads oddly.** Total time is wall clock; average per test is real per-item duration. Under parallelism the average can exceed total ÷ count. Expect it rather than filing a bug.

### Caching runs, not verdicts

Much of an eval's cost is `run()`, and much of your iteration is on `evaluate()`: tightening a threshold, rewording a judge's criteria, adding an assertion. `--cache` separates the two:

```bash
vendor/bin/neuron evaluation evaluators --cache
```

The first run stores each item's `run()` output under `.neuron/cache/evaluation/`. Later runs serve unchanged items from the cache and **always re-run the assertions**, so you can iterate on `evaluate()` against frozen outputs for free. `--fresh` re-runs everything and overwrites the cache.

The cache key covers the evaluator's `run()` method, the dataset item and the framework version. It does not see your agent's class or your prompt files unless you declare them:

```php
public function cacheDependencies(): array
{
    return [MyAgent::class, __DIR__ . '/../prompts/support.md'];
}
```

Change a declared dependency and the affected items run again. Forget to declare one and you are measuring yesterday's agent. And a cache hit says nothing about provider drift — the model behind the API can change while your cache does not — so pair `--cache` with a periodic `--fresh` run.

### In CI

```yaml
- name: Run evaluations
  run: |
    vendor/bin/neuron evaluation --path=evaluators || true
    php -r '$r = json_decode(file_get_contents("evaluation-results.json"), true, 512, JSON_THROW_ON_ERROR); exit($r["success_rate"] >= 0.95 ? 0 : 1);'
  env:
    ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Three pieces of practical advice:

**Do not gate every PR on the full suite.** It costs money and it is slow. Run a small smoke set on PRs and the full suite nightly.

**Do not fail the build on a single item.** Set a success-rate threshold. A 95% pass rate on a probabilistic system is a healthy build, not a broken one — and treating one flaky item as a failure teaches your team to ignore the signal. The runner itself exits non-zero on any failed item, so the bare command is an all-or-nothing gate and the threshold is yours to implement. The step above ignores the exit code and reads `success_rate`, a fraction between 0 and 1, from the JSON report that `evaluation.php` writes. If the run crashes before it writes the report, the second command fails and so does the build.

**Keep the API keys out of forks.** Eval runs cost real money; a public repository with eval-on-PR is a way to donate your budget to strangers.

### Module 10 assessment

1. Subscribe Inspector — or a `LogListener` — to a Module 5 agent. Break a tool description and read the trace.
2. Build an evaluator with five real inputs and at least one `StringSimilarity` assertion.
3. Add a `FaithfulnessJudge` assertion (it will matter in Module 11).
4. Write a custom output driver that appends to a CSV, and run the suite three times to produce a trend.
5. Time the suite sequentially and at `--concurrency=5`.

---

## PART II — PRE-RECORDING VERIFICATION LIST (ADDITIONS)

Carrying forward from Module 5's list:

| # | Issue | Where |
|---|---|---|
| 10 | `AudioContent` imported but `FileContent` instantiated | Messages / audio |
| 11 | `TextBlock` / `FileBlock` vs `TextContent` / `FileContent` | Messages / file ID |
| 12 | `NeuronAI\StructuredOutput\Property` should be `SchemaProperty` (v4 class: `NeuronAI\StructuredOutput\SchemaProperty`) | Structured output / nested |
| 13 | Symfony validator imports instead of `NeuronAI\StructuredOutput\Validation\Rules\` | Structured output / nested |
| 14 | `#[OutOfRange]` example imports `InRange` | Structured output / rules |
| 15 | Custom rule: `respectFormat()` arity, `$this->pattern` vs `$this->format` | Structured output / custom |
| 16 | Names for the observer in older material: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring`. On v4 use `Inspector\Neuron\V4\InspectorSubscriber` with `subscribe(ObservabilityEvent::class, …)` | Observability |
| 17 | `make:evaluator` vs `make:evaluators` between OS tabs (`make:evaluators`, plural, is the real one) | Evals |
| 18 | `evaluations --path=X` vs `evaluation X --concurrency=N` (the command is `evaluation`; `--path=X` and a positional X both work) | Evals |
| 19 | `ConsoleDriver` / `ConsoleOutputDriver` in the docs; the 4.x classes are `NeuronAI\Evaluation\Output\ConsoleOutput` and `JsonOutput` | Evals / output |
| 20 | `autoload-dev` maps `App\Evaluators\` but the docs' generator example uses `App\Neuron\Evaluators\` (the generator reads `autoload-dev` since 4.0.3) | Evals / setup |
| 21 | `new Antrhopic(...)` typo (`setAiProvider()` / `setInstructions()` exist on `AgentInterface`) | Evals / judge |

Resolve all 21 before recording. A short "how this course differs from the docs" segment listing a few of these is a strong trust signal in the free preview lessons.

---

**END OF PART II**

*Next: Part III — RAG. Module 11 (retrieval theory) and Module 12 (the Neuron pipeline).*
