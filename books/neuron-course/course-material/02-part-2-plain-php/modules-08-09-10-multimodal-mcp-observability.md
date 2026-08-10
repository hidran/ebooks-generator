# Agentic AI in PHP with Neuron
## PART II — PLAIN PHP + COMPOSER
### Full lesson scripts — Modules 8, 9 and 10

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^3.0, PHP 8.3.
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
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Chat\Messages\ContentBlocks\ImageContent;

$message = new UserMessage('Describe this image');

$message->addContent(
    new ImageContent(
        source: 'https://placehold.co/600x400/EEE/31343C',
        sourceType: SourceType::URL,
        mediaType: 'image/png'
    )
);

$response = MyAgent::make()->chat($message)->getMessage();
echo $response->getContent();
```

That is the entire API. The elegance is worth pointing out: there is no separate "vision agent", no different method, no alternate provider class. Same agent, same `chat()`, one more block.

### The block types

```php
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;

$message = new UserMessage('Summarize this document');

$message->addContent(
    new FileContent(
        source: base64_encode(file_get_contents(__DIR__ . '/invoice.pdf')),
        sourceType: SourceType::BASE64,
        mediaType: 'application/pdf'
    )
);
```

```php
use NeuronAI\Chat\Messages\ContentBlocks\VideoContent;

$message = new UserMessage('Summarize the content of this lesson.');

$message->addContent(
    new VideoContent(
        source: base64_encode(file_get_contents(__DIR__ . '/lesson_1.mp4')),
        sourceType: SourceType::BASE64,
        mediaType: 'video/mp4'
    )
);
```

Available blocks: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

Neuron maps each into the correct provider-specific format automatically — which is the whole reason the provider swap from Lesson 3.6 survives multimodality.

> **Documentation note.** The audio example on the official page imports `AudioContent` but then instantiates `FileContent`. Check which one your version expects. Another verification-list item.

### Mixing blocks

A message can hold several blocks of several types:

```php
$message = new UserMessage('Compare these two invoices and list the differences.');

$message->addContent(new FileContent(
    source: base64_encode(file_get_contents('/uploads/inv-a.pdf')),
    sourceType: SourceType::BASE64,
    mediaType: 'application/pdf',
));

$message->addContent(new FileContent(
    source: base64_encode(file_get_contents('/uploads/inv-b.pdf')),
    sourceType: SourceType::BASE64,
    mediaType: 'application/pdf',
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
- Six block types; Neuron maps them per provider.
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
$message = new UserMessage([
    new TextBlock('Analyze this'),
    new FileBlock("file_id_xxxx", SourceType::ID)
]);
```

Recall Lesson 1.2: **every iteration of the agent loop re-sends the entire conversation.**

With `BASE64`, a 4 MB PDF is in the message array. Iteration two re-sends it. Iteration three re-sends it. A five-step agent run has uploaded 20 MB.

With `ID`, the file is uploaded once and every subsequent message carries a short string.

The documentation states the benefit plainly — big savings in token consumption and improved response time. For any document-processing agent that takes more than one step, this is not a micro-optimisation; it is the difference between viable and not.

> **Naming inconsistency.** The `SourceType::ID` example uses `TextBlock` and `FileBlock`, while every other example uses `TextContent` and `FileContent`. One pair is wrong. Verification-list item — check your installed version.

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

### Key takeaways

- Three source types: `URL`, `BASE64`, `ID`.
- `ID` avoids re-uploading the payload on every loop iteration — the saving compounds with loop length.
- Upload is provider-specific; IDs expire and are not portable.

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

Now combine that with Lesson 1.2's re-transmission property and Lesson 8.2's fix, and the architecture becomes obvious: resize before sending, and use file IDs for anything multi-step.

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
    public array $lines;
}
```

Point out on camera what the descriptions are doing. `'Do not reformat it'` on the invoice number. `'Convert from whatever format appears'` on the date. `'Use 0 if the invoice has no VAT'` — that last one prevents a null where you declared a float, which is a real failure you would otherwise hit on your first VAT-exempt invoice.

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

**`examples/07-invoice.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\InvoiceAgent;
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
        source: \base64_encode(\file_get_contents($path)),
        sourceType: SourceType::BASE64,
        mediaType: 'application/pdf',
    )
);

$invoice = InvoiceAgent::make()->structured(
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

### The Node ecosystem

Most published servers are Node packages, run with `npx`:

```php
...McpConnector::make([
    'command' => 'npx',
    'args' => ['-y', '@modelcontextprotocol/server-everything'],
])->tools(),
```

`server-everything` is the reference implementation and the right thing to demo with — it exposes examples of every MCP feature and is the fastest way to see discovery working.

**Note for your PHP audience:** this requires Node on the machine running the agent. Say it plainly, because a PHP developer with no Node installed will hit a confusing failure and assume the framework is broken. Add it to the prerequisites for this module.

### The process model, and its consequences

The server is a **child process** of your PHP process. Three things follow, and they are all worth stating:

**Startup cost per run.** Each execution spawns the process, waits for discovery, then works. In a CLI script that is fine. In a web request it is latency on every request.

**It inherits your environment.** File system access, environment variables, network. A local MCP server runs with your process's privileges. Treat it exactly as you would treat any dependency you `exec()`.

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
- The server is a child process: startup cost, inherited privileges, unsuitable for per-request web use.
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
                    //'x-cutom-header' => 'value'
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

**Which to use:** whichever the server documents. This is not your choice — it is a property of the server you are connecting to. Read their docs.

### Set the timeout deliberately

The default may be generous. Recall Lesson 1.4's latency arithmetic: a multi-step agent making several MCP calls compounds every timeout.

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

### Discovery happens at construction

An operational detail that surprises people: **`tools()` connects to the server.**

That means:

- Building the agent requires the server to be reachable
- A slow server slows agent construction, before any model call
- A server that is down means your agent cannot be constructed at all

If your `tools()` method connects to three remote MCP servers, you have three points of failure between a user's request and the first token of the response. Plan for it: catch failures at construction, degrade to a reduced tool set, and monitor server availability as part of your own uptime rather than someone else's.

### Key takeaways

- `url` + `token` + `timeout` + `headers` for streamable HTTP; add `async => true` for SSE.
- Transport is the server's choice, not yours.
- Discovery happens when you build the agent — remote servers are availability dependencies.
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
    protected function tools()
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

### A workable policy

**Tier 1 — Servers you run.** Your own MCP server, on your infrastructure. Same trust as your own code. Use freely.

**Tier 2 — Servers from vendors you already trust.** Your CRM's official server, where you already have a contract, a DPA and a support channel. Use with `only()`.

**Tier 3 — Everything else.** Community servers, random registry entries, anything unmaintained. Treat as untrusted code. For production: read the source, pin a version, run it yourself rather than connecting to a hosted instance, and combine `only()` with tool approval for anything with side effects.

Prototyping is different — Tier 3 is fine for a spike. The distinction is between "trying it" and "shipping it", and being explicit about that keeps the lesson from sounding like fear-mongering.

### Layer the defences

MCP tools are still tools, so everything from Module 5 applies:

```php
protected function tools(): array
{
    return [
        ...McpConnector::make([
            'url'   => env('CRM_MCP_URL'),
            'token' => env('CRM_MCP_TOKEN'),
        ])->only([
            'search_contacts',
            'get_contact',
        ])->tools(),
    ];
}
```

Read-only tool names in the allowlist. Add `ToolApproval` middleware (Module 15) for anything that writes. And for a truly sensitive integration, consider proxying: wrap the MCP server in your own PHP tool that validates arguments before forwarding, so you have a place to enforce your own rules.

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

## LESSON 10.2 — Setting Up Inspector

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Get full execution traces working, including the configuration that background workers need.

### Install

```bash
composer require inspector-apm/inspector-php
```

Only needed if you are not already using another Inspector library — `inspector-laravel`, `inspector-symfony` and so on already include it.

### The environment variable

```dotenv
INSPECTOR_INGESTION_KEY=nwse877auxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Create a key by registering an app at `app.inspector.dev`.

### Register the observer

```php
use Inspector\Neuron\InspectorObserver;

class MyAgent extends Agent
{
    public function __construct()
    {
        parent::__construct();

        $this->observe(InspectorObserver::instance());
    }

    // ...
}
```

`observe()` works on **Agent, RAG and Workflow** — which is Lesson 2.3 again: they are all workflows, so they all take observers.

### Automatic instrumentation

If your application already reads environment files, Neuron is likely to instrument itself as soon as `INSPECTOR_INGESTION_KEY` is present. Registering the observer explicitly is for when you have no access to environment variables, or want to customise the configuration:

```php
$this->observe(
    InspectorObserver::instance('INSPECTOR_INGESTION_KEY')
);
```

### The setting that will bite you: autoFlush

**This is the most operationally important line in the lesson.**

If your agent runs in a long-running process — a queue worker, Swoole, RoadRunner — you must explicitly enable auto-flush:

```php
$this->observe(
    InspectorObserver::instance(
        key: 'INSPECTOR_INGESTION_KEY',
        autoFlush: true
    )
);
```

Without it, events accumulate in memory and are flushed at the end of the request. A worker process that runs for hours has no "end of request". Your traces never arrive, memory grows, and you conclude the integration is broken when it is merely mis-configured.

Given that Lesson 1.4 pushes long agent work onto queues, and Lesson 5.13 requires CLI for parallel tools, **most serious Neuron deployments are exactly the case that needs `autoFlush`.** Put it on a slide.

### Framework-specific packages

If you are integrating into Laravel or Symfony, add the framework package (`inspector-laravel`, `inspector-symfony`) for better data collection. Not required, but recommended — it correlates the agent trace with the HTTP request, the queries and the queue job around it, which is what you actually want when diagnosing a production incident.

Module 23 covers this in the Laravel context.

> **Verification list — namespace drift.** Three different names for this component appear across the ecosystem:
> - `Inspector\Neuron\InspectorObserver` (current Inspector docs)
> - `NeuronAI\Observability\InspectorObserver` (Neuron-side material)
> - `NeuronAI\Observability\AgentMonitoring` (older articles, and still in some structured-output examples)
>
> Confirm which exists in your installed version before recording. This is the single most likely place for a student to copy a `use` statement that does not resolve.

### Key takeaways

- `composer require inspector-apm/inspector-php`, set the key, call `observe()`.
- Works on Agent, RAG and Workflow.
- `autoFlush: true` for queue workers and long-running runtimes — non-optional.
- Three historical names for the observer class; verify yours.

---
═══════════════════════════════════════════════════════════════

## LESSON 10.3 — Reading a Trace

**Duration:** 13 minutes
**Type:** Hands-on — screen recording

### Learning objectives

Turn a trace into a diagnosis. This lesson is mostly screen capture; the value is in the narration.

### What a trace shows

Every inference step, every tool call, every retrieval — with arguments, results, token counts and timings.

Run the Lab 3 weather agent with Inspector enabled and walk through the timeline:

```
▸ WeatherAgent                                        4.82s   3,412 tokens
  ├─ ChatNode                          1.31s     892 in / 84 out
  ├─ ToolNode: get_current_weather     0.42s
  │    input:  {"latitude": 45.0703, "longitude": 7.6869}
  │    output: {"temperature_2m": 14.2, ...}
  ├─ ToolNode: get_current_weather     0.38s
  │    input:  {"latitude": 45.4642, "longitude": 9.19}
  ├─ ChatNode                          1.44s   1,203 in / 61 out
  ├─ ToolNode: mean                    0.01s
  └─ ChatNode                          1.26s   1,172 in / 91 out
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
892 → 1,203 → 1,172 input tokens. Growing, because the conversation grows. Exactly the compounding from Lesson 1.4, now measured rather than estimated.

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

> **Verification item.** The documentation's `autoload-dev` block maps `App\Evaluators\` to `evaluators/`, but the generator command in the same page creates `App\Neuron\Evaluators\AgentEvaluator`. Those two do not agree. Pick one convention for your course and use it consistently.

### Generate an evaluator

```bash
# Unix
vendor/bin/neuron make:evaluator App\\Neuron\\Evaluators\\AgentEvaluator

# Windows
.\vendor\bin\neuron make:evaluators App\Neuron\Evaluators\AgentEvaluator
```

> Note the singular/plural difference between the two tabs in the official docs — `make:evaluator` vs `make:evaluators`. One is a typo. Verification item.

### The three-method structure

```php
namespace App\Neuron\Evaluators;

use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;

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
        $response = MyAgent::make()->chat(
            new UserMessage($datasetItem['input'])
        )->getMessage();

        return $response->getContent();
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
use NeuronAI\RAG\Embeddings\OpenAI\OpenAIEmbeddings;

$this->assert(new StringSimilarity(
    reference: 'The quick brown fox',
    embeddingsProvider: new OpenAIEmbeddings(key: 'YOUR_KEY'),
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
use NeuronAI\Evaluation\Assertions\AgentJudge;

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
            ->chat(new UserMessage($datasetItem['input']))
            ->getMessage()
            ->getContent();
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

> The official example for this block misspells `Anthropic` as `Antrhopic`. Verification item. Also confirm the `setAiProvider()` / `setInstructions()` fluent methods exist in your version — they appear only here.

### The four specialised judges

Neuron ships judges for the recurring evaluation questions:

**`FaithfulnessJudge`** — is the output grounded in the provided context, or did it hallucinate?

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedDocuments,
    threshold: 0.7
), $output);
```

**This is the single most important assertion for RAG systems**, and it is the reason to introduce evals before Module 11 rather than after. A RAG system that answers fluently from information it invented is worse than one that says "I don't know". Faithfulness is how you measure that, and you cannot measure it with string matching.

**`CorrectnessJudge`** — does it match the expected answer?

```php
$this->assert(new CorrectnessJudge(
    judge: $judge,
    expected: $datasetItem['expected_answer'],
    threshold: 0.7
), $output);
```

**`RelevanceJudge`** — does it actually address the question?

**`HelpfulnessJudge`** — is it useful and actionable?

### Two cautions about judges

**The judge is also non-deterministic.** You are measuring a probabilistic system with a probabilistic instrument. Thresholds absorb this, but do not treat a judge score as ground truth. Track it over time and look for movement, not absolute values.

**Judges cost money.** Every judged assertion is an extra LLM call. A 200-item dataset with three judged assertions is 600 extra calls per run. Use a cheaper model for the judge than for the agent — a good application of the provider-swap argument from Lesson 3.6.

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

- Ten built-in assertions; `StringSimilarity` for meaning, `StringDistance` for characters.
- Four judges: faithfulness, correctness, relevance, helpfulness.
- `FaithfulnessJudge` is the essential one for RAG — introduce it before Module 11.
- Judges are non-deterministic and cost money; use a cheaper model.
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
vendor/bin/neuron evaluations --path=evaluators

# Windows
.\vendor\bin\neuron evaluations --path=evaluators
```

> **Verification item, and an important one.** The parallel-execution section of the same documentation page shows a different invocation: `vendor/bin/neuron evaluation path/to/evaluators --concurrency=3` — singular `evaluation`, and a positional argument rather than `--path=`. Run `vendor/bin/neuron list` on your installed version and use whichever is real. Getting this wrong in a course means every student's first eval command fails.

### Output drivers

Create `evaluation.php` in the project root:

```php
<?php

use NeuronAI\Evaluation\OutputDrivers\ConsoleDriver;
use NeuronAI\Evaluation\OutputDrivers\JsonDriver;

return [
    'output' => [
        ConsoleDriver::class => ['verbose' => true],
        JsonDriver::class    => ['path' => 'evaluation-results.json'],
    ],
];
```

Options are passed to each driver's constructor. Multiple drivers run simultaneously — console for the developer, JSON for CI to consume.

Without a config file, the system defaults to console output.

> *(The docs name the default `ConsoleOutputDriver` in prose but `ConsoleDriver` in the config example. Verification item.)*

### Custom output: the pattern that makes evals a business tool

```php
namespace App\Neuron\Evaluations;

use NeuronAI\Evaluation\Contracts\EvaluationOutputInterface;
use NeuronAI\Evaluation\Runner\EvaluatorSummary;

class DatabaseOutput implements EvaluationOutputInterface
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly string $table = 'evaluations'
    ) {}

    public function output(EvaluatorSummary $summary): void
    {
        $stmt = $this->pdo->prepare(
            "INSERT INTO {$this->table} (passed, failed, success_rate, total_time, created_at, updated_at)
             VALUES (?, ?, ?, ?, NOW(), NOW())"
        );

        $stmt->execute([
            $summary->getPassedCount(),
            $summary->getFailedCount(),
            $summary->getSuccessRate(),
            $summary->getTotalExecutionTime(),
        ]);
    }
}
```

Register it:

```php
return [
    'output' => [
        ConsoleDriver::class => ['verbose' => true],
        DatabaseOutput::class => [
            'pdo'   => new \PDO(/* ... */),
            'table' => 'evaluations',
        ],
    ],
];
```

**Why this matters beyond engineering.** Persisting the success rate on every run gives you a quality metric over time. You can chart it. You can show it to a stakeholder. You can answer "did last week's prompt change make things better or worse?" with a number instead of an opinion.

That is the transition from evals as a developer convenience to evals as evidence. For anyone selling AI work to a business, it is the difference between "trust me" and a graph.

### Parallel execution

Most eval time is spent waiting on the provider. Run items concurrently:

```bash
vendor/bin/neuron evaluation path/to/evaluators --concurrency=3
```

The documented example: one 2-second LLM call per item over a 100-item dataset drops from roughly 200 seconds to roughly 66.

**Requirements** — the same pair as Lesson 5.13:

```bash
composer require --dev spatie/fork
```

plus `pcntl` (Linux and macOS; not Windows). If either is missing, the command prints a notice and falls back to sequential, so the same command works everywhere.

**Choosing a level.** Every item in flight is an active provider request. Start at 3–5 and increase while you avoid rate limits. Rate-limit errors show up as test failures, so if failures appear when you raise concurrency, lower it before you go hunting for a bug in your agent.

### Three things to know about parallel runs

**Results are unaffected.** Items are independent, order is preserved, the report is identical.

**State is not shared.** Each item sees the state as of `setUp()`. Side effects from one item are invisible to others. If your evaluator accumulates state across items, run it sequentially.

**Outputs must be serializable.** The return value of `run()` crosses a process boundary via `serialize()`. A closure or an open connection cannot cross; assertion results survive but the reported output becomes a placeholder.

**Timing reads oddly.** Total time is wall clock; average per test is real per-item duration. Under parallelism the average can exceed total ÷ count. Expect it rather than filing a bug.

### In CI

```yaml
- name: Run evaluations
  run: vendor/bin/neuron evaluations --path=evaluators
  env:
    ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Three pieces of practical advice:

**Do not gate every PR on the full suite.** It costs money and it is slow. Run a small smoke set on PRs and the full suite nightly.

**Do not fail the build on a single item.** Set a success-rate threshold. A 95% pass rate on a probabilistic system is a healthy build, not a broken one — and treating one flaky item as a failure teaches your team to ignore the signal.

**Keep the API keys out of forks.** Eval runs cost real money; a public repository with eval-on-PR is a way to donate your budget to strangers.

### Module 10 assessment

1. Enable Inspector on a Module 5 agent. Break a tool description and read the trace.
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
| 12 | `NeuronAI\StructuredOutput\Property` should be `SchemaProperty` | Structured output / nested |
| 13 | Symfony validator imports instead of `NeuronAI\StructuredOutput\Validation\Rules\` | Structured output / nested |
| 14 | `#[OutOfRange]` example imports `InRange` | Structured output / rules |
| 15 | Custom rule: `respectFormat()` arity, `$this->pattern` vs `$this->format` | Structured output / custom |
| 16 | Three names for the observer: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` | Observability |
| 17 | `make:evaluator` vs `make:evaluators` between OS tabs | Evals |
| 18 | `evaluations --path=X` vs `evaluation X --concurrency=N` | Evals |
| 19 | `ConsoleDriver` vs `ConsoleOutputDriver` | Evals / output |
| 20 | `autoload-dev` maps `App\Evaluators\` but generator uses `App\Neuron\Evaluators\` | Evals / setup |
| 21 | `new Antrhopic(...)` typo; verify `setAiProvider()` / `setInstructions()` exist | Evals / judge |

Resolve all 21 before recording. A short "how this course differs from the docs" segment listing a few of these is a strong trust signal in the free preview lessons.

---

**END OF PART II**

*Next: Part III — RAG. Module 11 (retrieval theory) and Module 12 (the Neuron pipeline).*
