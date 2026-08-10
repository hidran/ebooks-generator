# Chapter 8 — Attachments and Multimodality

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch08`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch08), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

## 8.1 Media as Content Blocks

### Nothing new to learn

Section 4.1 established that a message holds an ordered list of content blocks, not a string. Multimodality is that fact, used.

An image is a block. A PDF is a block. Audio is a block. You add them the same way you add text.

```php
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Chat\Messages\ContentBlocks\ImageContent;
use NeuronAI\Chat\Enums\SourceType;

$message = new UserMessage('Describe this image');

$message->addContent(
    new ImageContent(
        content: 'https://placehold.co/600x400/EEE/31343C',
        sourceType: SourceType::URL,
        mediaType: 'image/png'
    )
);

$response = MyAgent::make()->chat($message)->getMessage();
echo $response->getContent();
```

That is the entire API. The elegance is worth noticing: there is no separate "vision agent", no different method, no alternate provider class. Same agent, same `chat()`, one more block.

### The block types

```php
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;
use NeuronAI\Chat\Enums\SourceType;

$message = new UserMessage('Summarize this document');

$message->addContent(
    new FileContent(
        content: base64_encode(file_get_contents(__DIR__ . '/invoice.pdf')),
        sourceType: SourceType::BASE64,
        mediaType: 'application/pdf'
    )
);
```

```php
use NeuronAI\Chat\Messages\ContentBlocks\VideoContent;
use NeuronAI\Chat\Enums\SourceType;

$message = new UserMessage('Summarize the content of this lesson.');

$message->addContent(
    new VideoContent(
        content: base64_encode(file_get_contents(__DIR__ . '/lesson_1.mp4')),
        sourceType: SourceType::BASE64,
        mediaType: 'video/mp4'
    )
);
```

Available blocks: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

NeuronAI maps each into the correct provider-specific format automatically — which is the whole reason the provider swap from Section 3.6 survives multimodality.

::: {.callout .callout-warning}
[Documentation note]{.callout-title}

The audio example on the official page imports `AudioContent` but then instantiates `FileContent`. Check which one your version expects. Appendix A, item 10.
:::

### Mixing blocks

A message can hold several blocks of several types:

```php
$message = new UserMessage('Compare these two invoices and list the differences.');

$message->addContent(new FileContent(
    content: base64_encode(file_get_contents('/uploads/inv-a.pdf')),
    sourceType: SourceType::BASE64,
    mediaType: 'application/pdf',
));

$message->addContent(new FileContent(
    content: base64_encode(file_get_contents('/uploads/inv-b.pdf')),
    sourceType: SourceType::BASE64,
    mediaType: 'application/pdf',
));
```

Two documents, one question, one call.

### Verify the model, not just the framework

The documentation puts a hint box here, and it earns repeating:

**Before using a content block, verify the model can interpret it.**

The framework will happily attach a video block to a request bound for a text-only model. What comes back is an error from the provider, or worse, a confident answer about content the model never saw.

Model capabilities are not a framework concern and they change monthly. Check the provider's current capability matrix, and fail fast in your own code:

```php
if (!$this->providerSupportsVision()) {
    throw new \RuntimeException('Configured model cannot process images.');
}
```

This matters specifically because of Section 3.6. If provider choice is an environment variable, someone will eventually set `NEURON_PROVIDER=ollama` with a text-only local model and point your invoice extractor at it.

### Key takeaways

- Media are content blocks, added with `addContent()`. No special agent, no special method.
- Six block types; NeuronAI maps them per provider.
- A message can mix several blocks of several types.
- Verify model capability yourself — the framework will not.

## 8.2 Source Types and the File ID Optimisation

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

Recall Section 1.2: **every iteration of the agent loop re-sends the entire conversation.**

With `BASE64`, a 4 MB PDF is in the message array. Iteration two re-sends it. Iteration three re-sends it. A five-step agent run has uploaded 20 MB.

With `ID`, the file is uploaded once and every subsequent message carries a short string.

The documentation states the benefit plainly — big savings in token consumption and improved response time. For any document-processing agent that takes more than one step, this is not a micro-optimisation; it is the difference between viable and not.

::: {.callout .callout-warning}
[Naming inconsistency]{.callout-title}

The `SourceType::ID` example uses `TextBlock` and `FileBlock`, while every other example uses `TextContent` and `FileContent`. One pair is wrong. Appendix A, item 11 — check your installed version.
:::

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

**File upload is provider-specific.** NeuronAI abstracts the *reference*, not the upload. You will call the provider's file API directly, or use their SDK, to get an ID. Check your provider's documentation.

**IDs expire.** Providers apply retention policies. Do not persist a file ID as though it were permanent; store your own reference and re-upload when needed.

**IDs are provider-scoped.** A file ID from OpenAI means nothing to Anthropic. This is one of the few places where the portability from Section 3.6 genuinely leaks — worth naming honestly rather than glossing over.

### Key takeaways

- Three source types: `URL`, `BASE64`, `ID`.
- `ID` avoids re-uploading the payload on every loop iteration — the saving compounds with loop length.
- Upload is provider-specific; IDs expire and are not portable.

## 8.3 Multimodal Cost and Design

### Images are expensive in tokens

An image is converted into tokens before the model sees it. The count depends on dimensions and the provider's tiling strategy, but a useful mental model:

- A small image (512×512): roughly 250–800 tokens
- A typical screenshot (1920×1080): roughly 1,000–1,700 tokens
- A high-resolution photo: several thousand

**One screenshot can cost more input tokens than the entire text conversation around it.**

Now combine that with Section 1.2's re-transmission property and Section 8.2's fix, and the architecture becomes obvious: resize before sending, and use file IDs for anything multi-step.

### Resize before you send

The single highest-leverage optimisation in multimodal work, and it is three lines:

```php
$image = new \Imagick($path);
$image->thumbnailImage(1024, 1024, true);  // bestfit
$image->setImageCompressionQuality(80);
$blob = $image->getImageBlob();
```

Most vision tasks — reading an invoice, identifying an object, describing a scene — do not need 4000 pixels wide. Downscaling to 1024 px often cuts token cost by half or more with no measurable loss in accuracy.

Test it on your own task rather than guessing. Run the same extraction at three resolutions and compare both the output quality and the token count.

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

**Video** — the same argument, more so. Extract keyframes plus a transcript. Sending full video to a model is the most expensive operation in this entire book, and it is rarely the best answer.

The general principle: **convert to text at the cheapest point in the pipeline, unless the non-text information is the point.**

### Key takeaways

- Images can cost more than the surrounding conversation; resize before sending.
- Extract text from prose PDFs; send the document when layout carries meaning.
- Transcribe audio and decompose video rather than sending raw media.
- Convert to text early unless the non-text signal is what you need.

## Lab 6 — The Invoice Extractor

**Covers:** structured output (Chapter 6) plus attachments (this chapter).

### Goal

Read an invoice document and return a validated, typed `Invoice` object. This is the single most commercially useful thing in Part II.

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

Read what the descriptions are doing. `'Do not reformat it'` on the invoice number. `'Convert from whatever format appears'` on the date. `'Use 0 if the invoice has no VAT'` — that last one prevents a null where you declared a float, which is a real failure you would otherwise hit on your first VAT-exempt invoice.

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
use NeuronAI\Chat\Enums\SourceType;

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

Add this after the extraction:

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

This is the practical face of Section 1.5: a non-deterministic component with a deterministic boundary around it. The DTO is the shape boundary; this check is the semantic one. Every production extraction pipeline needs both.

### Acceptance criteria

- Three invoices of genuinely different layouts extract without an exception.
- A VAT-exempt invoice produces `vat_amount = 0.0`, not a null or a fatal error.
- The arithmetic check fires on at least one deliberately corrupted input.
- Running the same invoice at full resolution and downscaled to 1024 px produces the same values — and you have both token counts written down.

### Going further

1. Record the failure rate across your three invoices, improve the description of the worst-performing field, and re-run. Write down what changed.
2. Add a second cross-field check: `subtotal + vat_amount ≈ total`.
3. Switch from `BASE64` to a provider file ID and measure the token difference on a multi-step run. Section 8.2 predicts a large saving; confirm it on your own document.
