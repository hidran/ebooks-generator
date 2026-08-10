# Capítulo 8 — Adjuntos y multimodalidad

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch08`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch08), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 8.1 Los medios como bloques de contenido

### Nada nuevo que aprender

La Sección 4.1 estableció que un mensaje contiene una lista ordenada de bloques de contenido, no una cadena. La multimodalidad es ese hecho, usado.

Una imagen es un bloque. Un PDF es un bloque. El audio es un bloque. Los añades igual que añades texto.

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

Esa es toda la API. La elegancia merece notarse: no hay un «agente de visión» aparte, ni un método distinto, ni una clase de proveedor alternativa. El mismo agente, el mismo `chat()`, un bloque más.

### Los tipos de bloque

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

Bloques disponibles: `TextContent`, `ReasoningContent`, `ImageContent`, `FileContent`, `AudioContent`, `VideoContent`.

NeuronAI proyecta cada uno automáticamente al formato correcto de cada proveedor, que es toda la razón por la que el cambio de proveedor de la Sección 3.6 sobrevive a la multimodalidad.

::: {.callout .callout-warning}
[Nota sobre la documentación]{.callout-title}

El ejemplo de audio de la página oficial importa `AudioContent` pero luego instancia `FileContent`. Comprueba cuál espera tu versión. Apéndice A, punto 10.
:::

### Mezclar bloques

Un mensaje puede contener varios bloques de varios tipos:

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

Dos documentos, una pregunta, una llamada.

### Verifica el modelo, no solo el framework

La documentación pone aquí un recuadro de aviso, y merece repetirse:

**Antes de usar un bloque de contenido, verifica que el modelo pueda interpretarlo.**

El framework adjuntará tan tranquilo un bloque de vídeo a una petición dirigida a un modelo de solo texto. Lo que vuelve es un error del proveedor o, peor, una respuesta segura de sí misma sobre contenido que el modelo nunca vio.

Las capacidades del modelo no son asunto del framework y cambian cada mes. Consulta la matriz de capacidades actual del proveedor y falla pronto en tu propio código:

```php
if (!$this->providerSupportsVision()) {
    throw new \RuntimeException('Configured model cannot process images.');
}
```

Esto importa específicamente por la Sección 3.6. Si la elección de proveedor es una variable de entorno, alguien acabará poniendo `NEURON_PROVIDER=ollama` con un modelo local de solo texto y apuntando tu extractor de facturas hacia él.

### Puntos clave

- Los medios son bloques de contenido, añadidos con `addContent()`. Sin agente especial, sin método especial.
- Seis tipos de bloque; NeuronAI los proyecta según el proveedor.
- Un mensaje puede mezclar varios bloques de varios tipos.
- Verifica tú la capacidad del modelo: el framework no lo hará.

## 8.2 Tipos de origen y la optimización del ID de archivo

### Los tres tipos de origen

```php
SourceType::URL     // The provider fetches it
SourceType::BASE64  // You embed the bytes in the request
SourceType::ID      // Reference a file already uploaded to the provider
```

**`URL`** — el más simple. El proveedor descarga el recurso. Requiere que el archivo sea accesible públicamente, lo que para documentos de negocio privados normalmente lo descarta, o te obliga a URLs firmadas con caducidad corta.

**`BASE64`** — lees el archivo y lo incrustas. Funciona con cualquier cosa de tu disco y mantiene el archivo privado dentro de la petición. Cuesta ancho de banda y tamaño de petición en cada llamada.

**`ID`** — sube el archivo a la plataforma del proveedor una vez y luego referéncialo por identificador.

### Por qué `ID` importa más de lo que parece

```php
$message = new UserMessage([
    new TextBlock('Analyze this'),
    new FileBlock("file_id_xxxx", SourceType::ID)
]);
```

Recuerda la Sección 1.2: **cada iteración del bucle del agente reenvía la conversación entera.**

Con `BASE64`, un PDF de 4 MB está en el array de mensajes. La iteración dos lo reenvía. La tres lo reenvía. Una ejecución de agente de cinco pasos ha subido 20 MB.

Con `ID`, el archivo se sube una vez y cada mensaje posterior lleva una cadena corta.

La documentación enuncia el beneficio con claridad: grandes ahorros en consumo de tokens y mejora del tiempo de respuesta. Para cualquier agente de procesamiento de documentos que dé más de un paso, esto no es una microoptimización; es la diferencia entre viable y no viable.

::: {.callout .callout-warning}
[Inconsistencia de nombres]{.callout-title}

El ejemplo de `SourceType::ID` usa `TextBlock` y `FileBlock`, mientras que todos los demás ejemplos usan `TextContent` y `FileContent`. Un par de los dos está mal. Apéndice A, punto 11: comprueba tu versión instalada.
:::

### La tabla de decisión

| Situación | Tipo de origen |
|---|---|
| Imagen pública, una sola llamada | `URL` |
| Archivo privado, una sola llamada | `BASE64` |
| Archivo privado, agente de varios pasos | `ID` |
| El mismo documento en muchas conversaciones | `ID` |
| Archivo grande (> 1 MB), cualquier agente con herramientas | `ID` |

La regla práctica: **si el agente tiene herramientas, da por hecho que habrá varias iteraciones y prefiere `ID`.**

### Notas prácticas

**La subida de archivos es específica de cada proveedor.** NeuronAI abstrae la *referencia*, no la subida. Llamarás directamente a la API de archivos del proveedor, o usarás su SDK, para obtener un ID. Consulta la documentación de tu proveedor.

**Los IDs caducan.** Los proveedores aplican políticas de retención. No persistas un ID de archivo como si fuera permanente; guarda tu propia referencia y vuelve a subir cuando haga falta.

**Los IDs están acotados al proveedor.** Un ID de archivo de OpenAI no significa nada para Anthropic. Este es uno de los pocos sitios donde la portabilidad de la Sección 3.6 se resquebraja de verdad, y conviene nombrarlo con honestidad en lugar de pasarlo por alto.

### Puntos clave

- Tres tipos de origen: `URL`, `BASE64`, `ID`.
- `ID` evita volver a subir la carga en cada iteración del bucle; el ahorro se acumula con la longitud del bucle.
- La subida es específica del proveedor; los IDs caducan y no son portables.

## 8.3 Coste y diseño multimodal

### Las imágenes son caras en tokens

Una imagen se convierte en tokens antes de que el modelo la vea. El recuento depende de las dimensiones y de la estrategia de teselado del proveedor, pero un modelo mental útil:

- Una imagen pequeña (512×512): aproximadamente 250–800 tokens
- Una captura de pantalla típica (1920×1080): aproximadamente 1.000–1.700 tokens
- Una foto de alta resolución: varios miles

**Una sola captura de pantalla puede costar más tokens de entrada que toda la conversación de texto que la rodea.**

Ahora combina eso con la propiedad de retransmisión de la Sección 1.2 y la solución de la 8.2, y la arquitectura se vuelve obvia: redimensiona antes de enviar y usa IDs de archivo para cualquier cosa de varios pasos.

### Redimensiona antes de enviar

La optimización con más palanca del trabajo multimodal, y son tres líneas:

```php
$image = new \Imagick($path);
$image->thumbnailImage(1024, 1024, true);  // bestfit
$image->setImageCompressionQuality(80);
$blob = $image->getImageBlob();
```

La mayoría de las tareas de visión —leer una factura, identificar un objeto, describir una escena— no necesitan 4000 píxeles de ancho. Reducir a 1024 px suele recortar el coste en tokens a la mitad o más sin pérdida medible de precisión.

Pruébalo en tu propia tarea en lugar de suponerlo. Ejecuta la misma extracción a tres resoluciones y compara tanto la calidad de la salida como el recuento de tokens.

### PDF: ¿enviar el documento o extraer el texto?

Una decisión de diseño real, y la respuesta no es siempre «envía el PDF».

**Envía el PDF cuando** la maquetación importa: tablas, formularios, facturas donde la posición carga significado, documentos escaneados sin capa de texto.

**Extrae el texto primero cuando** el documento sea prosa densa sin maquetación significativa. Un informe de 40 páginas cuesta muchísimos menos tokens como texto extraído que como imágenes de página, y para la prosa la maquetación no aporta nada.

```php
// Cheap path for text-heavy documents
$text = (new \Smalot\PdfParser\Parser())->parseFile($path)->getText();

$message = new UserMessage("Summarise this report:\n\n{$text}");
```

Elegir por tipo de documento, en lugar de aplicar una única estrategia a todo, es lo que separa un pipeline meditado de una demo.

### Audio y vídeo

Ambos son caros y ambos tienen una descomposición más barata:

**Audio** — transcribe con un servicio dedicado de voz a texto y luego trabaja con texto. Más barato, más rápido, y la transcripción es reutilizable, buscable y almacenable. Manda audio crudo a un modelo multimodal solo cuando el tono, la identidad del hablante o un sonido no verbal importen de verdad.

**Vídeo** — el mismo argumento, con más fuerza. Extrae fotogramas clave más una transcripción. Enviar vídeo completo a un modelo es la operación más cara de todo este libro, y rara vez es la mejor respuesta.

El principio general: **convierte a texto en el punto más barato del pipeline, salvo que la información no textual sea justamente el objetivo.**

### Puntos clave

- Las imágenes pueden costar más que la conversación que las rodea; redimensiona antes de enviar.
- Extrae texto de los PDF de prosa; envía el documento cuando la maquetación cargue significado.
- Transcribe el audio y descompón el vídeo en lugar de enviar medios crudos.
- Convierte a texto pronto salvo que la señal no textual sea lo que necesitas.

## Laboratorio 6 — El extractor de facturas

**Cubre:** salida estructurada (Capítulo 6) más adjuntos (este capítulo).

### Objetivo

Leer un documento de factura y devolver un objeto `Invoice` tipado y validado. Es lo más comercialmente útil de toda la Parte II.

### Las clases de salida

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

Lee lo que están haciendo las descripciones. `'Do not reformat it'` en el número de factura. `'Convert from whatever format appears'` en la fecha. `'Use 0 if the invoice has no VAT'`: esa última previene un nulo donde declaraste un float, que es un fallo real con el que chocarías en tu primera factura exenta de IVA.

### El agente

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

### El ejecutor

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

### El paso de verificación que nadie enseña

Añade esto después de la extracción:

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

**Los atributos de validación comprueban la forma. Solo tu código puede comprobar la aritmética.**

Un modelo puede producir un `Invoice` perfectamente bien formado en el que los números no cuadran: leyó mal un dígito. Ninguna restricción de esquema caza eso. Una comprobación de coherencia entre campos en PHP corriente sí, y cuesta cuatro líneas.

Esta es la cara práctica de la Sección 1.5: un componente no determinista con una frontera determinista alrededor. El DTO es la frontera de forma; esta comprobación es la semántica. Todo pipeline de extracción en producción necesita ambas.

### Criterios de aceptación

- Tres facturas de maquetaciones genuinamente distintas se extraen sin excepción.
- Una factura exenta de IVA produce `vat_amount = 0.0`, no un nulo ni un error fatal.
- La comprobación aritmética salta con al menos una entrada corrompida deliberadamente.
- Ejecutar la misma factura a resolución completa y reducida a 1024 px produce los mismos valores, y tienes anotados ambos recuentos de tokens.

### Ir más allá

1. Registra la tasa de fallo en tus tres facturas, mejora la descripción del campo con peor rendimiento y vuelve a ejecutar. Anota qué cambió.
2. Añade una segunda comprobación entre campos: `subtotal + vat_amount ≈ total`.
3. Cambia de `BASE64` a un ID de archivo del proveedor y mide la diferencia de tokens en una ejecución de varios pasos. La Sección 8.2 predice un gran ahorro; confírmalo con tu propio documento.
