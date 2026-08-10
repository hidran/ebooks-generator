# Capitolo 8 — Allegati e multimodalità

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch08`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch08), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 8.1 I media come blocchi di contenuto

### Niente di nuovo da imparare

La Sezione 4.1 ha stabilito che un messaggio contiene un elenco ordinato di blocchi di contenuto, non una stringa. La multimodalità è quel fatto, usato.

Un'immagine è un blocco. Un PDF è un blocco. L'audio è un blocco. Li aggiungi nello stesso modo in cui aggiungi il testo.

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

Questa è tutta l'API. Vale la pena notare l'eleganza: non c'è un "agent visione" separato, nessun metodo diverso, nessuna classe provider alternativa. Stesso agent, stesso `chat()`, un blocco in più.

### I tipi di blocco

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

Blocchi disponibili: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

NeuronAI mappa automaticamente ciascuno nel formato corretto del provider — che è l'intera ragione per cui lo scambio di provider della Sezione 3.6 sopravvive alla multimodalità.

::: {.callout .callout-warning}
[Nota sulla documentazione]{.callout-title}

L'esempio audio sulla pagina ufficiale importa `AudioContent` ma poi istanzia `FileContent`. Controlla quale si aspetta la tua versione. Appendice A, punto 10.
:::

### Mescolare i blocchi

Un messaggio può contenere più blocchi di più tipi:

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

Due documenti, una domanda, una chiamata.

### Verifica il modello, non solo il framework

La documentazione mette qui un riquadro di suggerimento, e merita di essere ripetuto:

**Prima di usare un blocco di contenuto, verifica che il modello sappia interpretarlo.**

Il framework allegherà volentieri un blocco video a una richiesta destinata a un modello solo testuale. Quello che torna indietro è un errore dal provider oppure, peggio, una risposta sicura di sé su contenuti che il modello non ha mai visto.

Le capacità dei modelli non sono un affare del framework e cambiano ogni mese. Controlla la matrice di capacità attuale del provider, e fallisci in fretta nel tuo codice:

```php
if (!$this->providerSupportsVision()) {
    throw new \RuntimeException('Configured model cannot process images.');
}
```

Questo conta in modo specifico per via della Sezione 3.6. Se la scelta del provider è una variabile d'ambiente, prima o poi qualcuno imposterà `NEURON_PROVIDER=ollama` con un modello locale solo testuale e ci punterà contro il tuo estrattore di fatture.

### Punti chiave

- I media sono blocchi di contenuto, aggiunti con `addContent()`. Nessun agent speciale, nessun metodo speciale.
- Sei tipi di blocco; NeuronAI li mappa per provider.
- Un messaggio può mescolare più blocchi di più tipi.
- Verifica tu la capacità del modello: il framework non lo farà.

## 8.2 Tipi di sorgente e l'ottimizzazione con file ID

### I tre tipi di sorgente

```php
SourceType::URL     // The provider fetches it
SourceType::BASE64  // You embed the bytes in the request
SourceType::ID      // Reference a file already uploaded to the provider
```

**`URL`** — il più semplice. Il provider scarica la risorsa. Richiede che il file sia raggiungibile pubblicamente, cosa che per i documenti aziendali riservati di solito lo esclude, o ti costringe a URL firmati con scadenza breve.

**`BASE64`** — leggi il file e lo incorpori. Funziona per qualunque cosa sul tuo disco, mantiene il file privato alla richiesta. Costa banda e dimensione della richiesta a ogni chiamata.

**`ID`** — carichi il file sulla piattaforma del provider una volta, poi lo referenzi tramite identificativo.

### Perché `ID` conta più di quanto sembri

```php
$message = new UserMessage([
    new TextBlock('Analyze this'),
    new FileBlock("file_id_xxxx", SourceType::ID)
]);
```

Ricorda la Sezione 1.2: **ogni iterazione del ciclo dell'agent rimanda l'intera conversazione.**

Con `BASE64`, un PDF da 4 MB è nell'array dei messaggi. La seconda iterazione lo rimanda. La terza lo rimanda. Un'esecuzione di agent in cinque passi ha caricato 20 MB.

Con `ID`, il file viene caricato una volta e ogni messaggio successivo porta una stringa breve.

La documentazione dichiara il beneficio in modo netto: grandi risparmi nel consumo di token e tempi di risposta migliori. Per qualunque agent di elaborazione documenti che faccia più di un passo, non è una micro-ottimizzazione: è la differenza fra sostenibile e no.

::: {.callout .callout-warning}
[Incoerenza nei nomi]{.callout-title}

L'esempio di `SourceType::ID` usa `TextBlock` e `FileBlock`, mentre ogni altro esempio usa `TextContent` e `FileContent`. Una delle due coppie è sbagliata. Appendice A, punto 11 — controlla la tua versione installata.
:::

### La tabella decisionale

| Situazione | Tipo di sorgente |
|---|---|
| Immagine pubblica, chiamata singola | `URL` |
| File riservato, chiamata singola | `BASE64` |
| File riservato, agent multi-passo | `ID` |
| Stesso documento in molte conversazioni | `ID` |
| File grande (> 1 MB), qualunque agent con tool | `ID` |

La regola pratica: **se l'agent ha dei tool, presumi più iterazioni e preferisci `ID`.**

### Note pratiche

**Il caricamento del file è specifico del provider.** NeuronAI astrae il *riferimento*, non il caricamento. Chiamerai direttamente l'API file del provider, o userai il suo SDK, per ottenere un ID. Controlla la documentazione del tuo provider.

**Gli ID scadono.** I provider applicano politiche di conservazione. Non persistere un file ID come se fosse permanente; conserva un tuo riferimento e ricarica quando serve.

**Gli ID sono legati al provider.** Un file ID di OpenAI non significa nulla per Anthropic. È uno dei pochi punti in cui la portabilità della Sezione 3.6 trapela davvero — meglio dirlo onestamente che sorvolarci sopra.

### Punti chiave

- Tre tipi di sorgente: `URL`, `BASE64`, `ID`.
- `ID` evita di ricaricare il payload a ogni iterazione del ciclo: il risparmio si accumula con la lunghezza del ciclo.
- Il caricamento è specifico del provider; gli ID scadono e non sono portabili.

## 8.3 Costo e progettazione multimodale

### Le immagini costano care in token

Un'immagine viene convertita in token prima che il modello la veda. Il conteggio dipende dalle dimensioni e dalla strategia di suddivisione del provider, ma un modello mentale utile:

- Un'immagine piccola (512×512): all'incirca 250–800 token
- Uno screenshot tipico (1920×1080): all'incirca 1.000–1.700 token
- Una foto ad alta risoluzione: diverse migliaia

**Un solo screenshot può costare più token in ingresso dell'intera conversazione testuale attorno.**

Ora combinalo con la proprietà di ritrasmissione della Sezione 1.2 e con la soluzione della Sezione 8.2, e l'architettura diventa ovvia: ridimensiona prima di inviare, e usa i file ID per qualunque cosa multi-passo.

### Ridimensiona prima di inviare

L'ottimizzazione con più leva nel lavoro multimodale, e sono tre righe:

```php
$image = new \Imagick($path);
$image->thumbnailImage(1024, 1024, true);  // bestfit
$image->setImageCompressionQuality(80);
$blob = $image->getImageBlob();
```

La maggior parte dei compiti di visione — leggere una fattura, identificare un oggetto, descrivere una scena — non ha bisogno di 4000 pixel di larghezza. Scendere a 1024 px spesso dimezza o più il costo in token senza perdita misurabile di accuratezza.

Provalo sul tuo compito invece di indovinare. Esegui la stessa estrazione a tre risoluzioni e confronta sia la qualità dell'output sia il conteggio dei token.

### PDF: mandare il documento o estrarre il testo?

Una vera decisione di progetto, e la risposta non è sempre "manda il PDF".

**Manda il PDF quando** il layout conta: tabelle, moduli, fatture in cui la posizione porta significato, documenti scansionati senza livello di testo.

**Estrai prima il testo quando** il documento è prosa densa senza layout significativo. Un report di 40 pagine costa molti meno token come testo estratto che come immagini di pagina, e per la prosa il layout non aggiunge nulla.

```php
// Cheap path for text-heavy documents
$text = (new \Smalot\PdfParser\Parser())->parseFile($path)->getText();

$message = new UserMessage("Summarise this report:\n\n{$text}");
```

Scegliere per tipo di documento, invece di applicare un'unica strategia a tutto, è ciò che separa una pipeline ragionata da una demo.

### Audio e video

Entrambi sono costosi ed entrambi hanno una scomposizione più economica:

**Audio** — trascrivi con un servizio dedicato di riconoscimento vocale, poi lavora con il testo. Più economico, più veloce, e la trascrizione è riusabile, ricercabile e archiviabile. Manda audio grezzo a un modello multimodale solo quando tono, identità del parlante o suoni non verbali contano davvero.

**Video** — lo stesso argomento, ancora di più. Estrai fotogrammi chiave più una trascrizione. Mandare un video completo a un modello è l'operazione più costosa di tutto questo libro, ed è raramente la risposta migliore.

Il principio generale: **converti in testo nel punto più economico della pipeline, a meno che l'informazione non testuale non sia proprio il punto.**

### Punti chiave

- Le immagini possono costare più della conversazione circostante; ridimensiona prima di inviare.
- Estrai il testo dai PDF di prosa; manda il documento quando il layout porta significato.
- Trascrivi l'audio e scomponi il video invece di mandare media grezzi.
- Converti in testo presto, a meno che il segnale non testuale sia ciò che ti serve.

## Laboratorio 6 — L'estrattore di fatture

**Copre:** structured output (Capitolo 6) più allegati (questo capitolo).

### Obiettivo

Leggere un documento di fattura e restituire un oggetto `Invoice` tipizzato e validato. È la cosa commercialmente più utile di tutta la Parte II.

### Le classi di output

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

Leggi che cosa stanno facendo le descrizioni. `'Do not reformat it'` sul numero di fattura. `'Convert from whatever format appears'` sulla data. `'Use 0 if the invoice has no VAT'` — quest'ultima previene un null dove hai dichiarato un float, che è un fallimento reale in cui incapperesti alla prima fattura esente IVA.

### L'agent

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

### L'esecutore

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

### Il passo di verifica che nessuno insegna

Aggiungi questo dopo l'estrazione:

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

**Gli attributi di validazione controllano la forma. Solo il tuo codice può controllare l'aritmetica.**

Un modello può produrre una `Invoice` perfettamente ben formata in cui i numeri non tornano: ha letto male una cifra. Nessun vincolo di schema lo intercetta. Un controllo di coerenza fra campi in normale PHP sì, e costa quattro righe.

È il volto pratico della Sezione 1.5: un componente non deterministico con un confine deterministico attorno. Il DTO è il confine di forma; questo controllo è quello semantico. Ogni pipeline di estrazione in produzione ha bisogno di entrambi.

### Criteri di accettazione

- Tre fatture di layout genuinamente diversi si estraggono senza eccezioni.
- Una fattura esente IVA produce `vat_amount = 0.0`, non un null né un errore fatale.
- Il controllo aritmetico scatta su almeno un input volutamente corrotto.
- Eseguire la stessa fattura a piena risoluzione e ridimensionata a 1024 px produce gli stessi valori — e hai annotato entrambi i conteggi di token.

### Andare oltre

1. Registra il tasso di fallimento sulle tue tre fatture, migliora la descrizione del campo che va peggio e riesegui. Annota che cosa è cambiato.
2. Aggiungi un secondo controllo fra campi: `subtotal + vat_amount ≈ total`.
3. Passa da `BASE64` a un file ID del provider e misura la differenza di token su un'esecuzione multi-passo. La Sezione 8.2 prevede un grande risparmio; confermalo sul tuo documento.
