# Capítulo 12 — El pipeline de RAG de NeuronAI

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch12`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch12), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 12.1 La clase RAG

### Genérala

```bash
# Unix
vendor/bin/neuron make:rag App\\Neuron\\MyChatBot

# Windows
.\vendor\bin\neuron make:rag App\Neuron\MyChatBot
```

### La clase

```php
namespace App\Neuron;

use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Embeddings\OpenAIEmbeddingsProvider;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\FileVectorStore;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class MyChatBot extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(
            key: 'ANTHROPIC_API_KEY',
            model: 'ANTHROPIC_MODEL',
        );
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return new OpenAIEmbeddingsProvider(
            key: 'OPENAI_API_KEY',
            model: 'OPENAI_MODEL'
        );
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return new FileVectorStore(
            directory: __DIR__,
            name: 'demo'
        );
    }
}
```

Tres métodos en lugar del único del Agent. La misma forma, dos componentes extra:

- `provider()` — el modelo de chat, como antes
- `embeddings()` — convierte texto en vectores
- `vectorStore()` — los guarda y los busca

**Fíjate en que son dos modelos distintos.** Tu proveedor podría ser Claude; tu proveedor de incrustaciones podría ser OpenAI o un modelo local de Ollama. Son elecciones independientes, y mezclarlas es normal y no un error.

### Usarla

```php
use App\Neuron\MyChatBot;
use NeuronAI\Chat\Messages\UserMessage;

$message = MyChatBot::make()
    ->chat(new UserMessage('I want to know more about Inspector AI Bug Fix.'))
    ->getMessage();

echo $message->getContent();
```

`chat()`: el mismo método que en un agente corriente. La recuperación ocurre dentro, automáticamente. Desde el lado que llama, un agente RAG y un agente normal son indistinguibles.

### RAG *es* un Agent

Esta es la Sección 2.3 llegando por tercera vez, y tiene consecuencias prácticas:

> La clase `RAG` de NeuronAI extiende la clase básica `Agent`. Tu RAG siempre es un agente, así que puedes engancharle herramientas y definir instrucciones de sistema.

Lo que significa que un agente RAG hereda, gratis:

- `instructions()` y `SystemPrompt`
- `tools()` y juegos de herramientas
- `chatHistory()`
- `structured()`
- `stream()`
- `observe()` para trazado
- Todo lo de los Capítulos 3 al 10

### El patrón combinado

El ejemplo de la documentación está bien elegido: consejos de entrenamiento a partir de una base de conocimiento, más una herramienta para el estado actual del usuario:

```php
class WorkoutTipsAgent extends RAG
{
    protected function provider(): AIProviderInterface { /* ... */ }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are an AI Agent specialized in providing workout tips.'],
        );
    }

    protected function embeddings(): EmbeddingsProviderInterface { /* ... */ }

    protected function vectorStore(): VectorStoreInterface { /* ... */ }

    protected function tools(): array
    {
        return [
            CalculatorToolkit::make(),
        ];
    }
}
```

Conocimiento de la recuperación, hechos de las herramientas, aritmética del juego de herramientas. Eso es el «se componen» de la Sección 11.4, en una sola clase.

::: {.callout .callout-warning}
[La firma del almacén vectorial: comprueba esto antes de escribir nada]{.callout-title}

La documentación muestra `FileVectorStore` de tres formas distintas en tres páginas:

- `new FileVectorStore(directory: __DIR__, name: 'demo')`
- `new FileVectorStore(directory: storage_path(), topK: 4)`
- `new FileVectoreStore(directory: __DIR__, key: 'demo')` — fíjate en el nombre de clase con errata

También `OpenAIEmbeddingsProvider` frente a `OpenAIEmbeddingProvider` (con y sin la `s`) y el namespace `RAG\Embeddings\` frente a `RAG\EmbeddingProvider\`. Este es el código de mayor tráfico de la Parte III y cuatro de los puntos del Apéndice A viven en él: del 22 al 25. Resuélvelos contra tu versión instalada ahora, no después de haber escrito un script de ingesta.
:::

### Puntos clave

- Tres métodos: `provider()`, `embeddings()`, `vectorStore()`.
- El modelo de chat y el de incrustaciones son elecciones independientes.
- `chat()` no cambia; la recuperación es interna.
- El RAG hereda todas las funcionalidades del Agent, incluidas las herramientas.

## 12.2 Cargadores de datos y lectores

### La línea única

```php
use App\Neuron\MyRAG;
use NeuronAI\RAG\DataLoader\FileDataLoader;

MyRAG::make()->addDocuments(
    FileDataLoader::for(__DIR__.'/my-article.md')->getDocuments()
);
```

Cargar, dividir, embeber, guardar: cuatro operaciones, una instrucción.

### FileDataLoader

Apúntalo a un archivo o a un directorio:

```php
// A single file
$documents = FileDataLoader::for(__DIR__.'/my-article.md')->getDocuments();

// Every file in a directory
$documents = FileDataLoader::for(__DIR__)->getDocuments();
```

Por defecto lee el contenido de los archivos como texto plano. No todos los formatos son texto plano, y para eso están los lectores.

### Lectores

**Cada lector está ligado a una extensión de archivo.** El cargador elige el correcto automáticamente según lo que encuentre.

**PDF:**

```php
$documents = FileDataLoader::for(__DIR__)
    ->addReader('pdf', new \NeuronAI\RAG\DataLoader\PdfReader())
    ->getDocuments();
```

Requiere la utilidad **poppler** (`pdftotext`) en el sistema. Una dependencia del sistema, no de Composer, que es por lo que aquí «funciona en mi máquina» normalmente significa «poppler está instalado en mi máquina».

```bash
sudo apt install poppler-utils    # Debian/Ubuntu
brew install poppler              # macOS
```

**HTML:**

```php
$documents = FileDataLoader::for(__DIR__)
    ->addReader(['html', 'xhtml'], new \NeuronAI\RAG\DataLoader\HtmlReader())
    ->getDocuments();
```

Requiere `mtibben/html2text`:

```bash
composer require mtibben/html2text
```

Fíjate en que convierte el HTML **a Markdown** en lugar de quitar las etiquetas. Eso importa: los encabezados sobreviven como `##`, lo que significa que un divisor consciente de los encabezados (Sección 12.3) puede usarlos. Reducir a texto plano tiraría esa estructura a la basura.

Una extensión puede mapear a varios lectores, o varias extensiones a un solo lector: `['html', 'xhtml']` arriba.

### StringDataLoader

Para texto que ya tienes: de una base de datos, de una API, de un editor.

```php
use NeuronAI\RAG\DataLoader\StringDataLoader;

$contents = [
    // list of strings (text you want to embed)
];

foreach ($contents as $text) {
    $documents = StringDataLoader::for($text)->getDocuments();

    MyRAG::make()->addDocuments($documents);
}
```

**Este es el cargador que más usarás en una aplicación real.** Tu base de conocimiento probablemente son filas de una tabla —artículos, descripciones de producto, registros de políticas— y no archivos en disco. El cargador de archivos se lleva el espacio en la documentación; el de cadenas se lleva el uso en producción.

Una nota de eficiencia sobre ese ejemplo: construye el agente RAG dentro del bucle. Sácalo fuera:

```php
$rag = MyRAG::make();

foreach ($contents as $text) {
    $rag->addDocuments(StringDataLoader::for($text)->getDocuments());
}
```

### Componentes autónomos

No necesitas un agente RAG para hacer la ingesta. El proveedor de incrustaciones y el almacén vectorial funcionan de forma independiente:

```php
$embedder = new OpenAIEmbeddingsProvider(
    key: 'OPENAI_API_KEY',
    model: 'OPENAI_MODEL'
);

$store = new FileVectorStore(
    directory: __DIR__,
    name: 'demo'
);

$documents = FileDataLoader::for(__DIR__.'/documents')
    ->addReader('pdf', new \NeuronAI\RAG\DataLoader\PdfReader())
    ->getDocuments();

$store->addDocuments(
    $embedder->embedDocuments($documents)
);
```

**El almacén debe ser el mismo que usa tu agente RAG.** Mismo directorio, mismo índice, misma colección. Este es el error de ingesta más común: indexas en un almacén y consultas otro, y el agente dice que no sabe nada.

**¿Por qué usar componentes autónomos?** Porque la ingesta y la consulta son trabajos distintos con ciclos de vida distintos. La ingesta es un proceso por lotes, un cron, un proceso de cola. No necesita un proveedor de chat configurado, ni una clave de API para el LLM, ni las instrucciones del agente. Separarlos mantiene tu script de ingesta ligero y lo hace desplegable de forma independiente.

Este es además el patrón que usa el Capítulo 20 en Laravel, donde la ingesta se ejecuta como un trabajo en cola.

### Puntos clave

- `FileDataLoader::for($path)->getDocuments()` para archivos y directorios.
- Los lectores se mapean a extensiones; PDF necesita poppler, HTML necesita `mtibben/html2text`.
- El HTML se convierte a Markdown, preservando la estructura para el divisor.
- `StringDataLoader` es lo que usarás de verdad: la mayoría de las bases de conocimiento son filas de base de datos.
- Haz la ingesta con componentes autónomos; el almacén debe ser idéntico al del agente.

## 12.3 Divisores

### Enganchar un divisor

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new DelimiterTextSplitter())
    ->getDocuments();
```

### DelimiterTextSplitter — el valor por defecto

```php
new DelimiterTextSplitter(
    maxLength: 1000,
    separator: '.',
    wordOverlap: 0
)
```

Los tres parámetros de la Sección 11.3, en código:

- **`maxLength`** — fragmentos no más largos que esto
- **`separator`** — dónde se permite cortar; el punto por defecto
- **`wordOverlap`** — palabras arrastradas entre fragmentos; cero por defecto

La documentación es explícita en que cada uno de ellos afecta al rendimiento y a la precisión. No son valores por defecto que aceptar; son decisiones que tomar.

### SentenceTextSplitter

```php
new SentenceTextSplitter(
    maxWords: 200,
    overlapWords: 0
)
```

Divide en frases, las agrupa en fragmentos basados en número de palabras y opcionalmente solapa por palabras.

**Cuál usar.** `SentenceTextSplitter` es generalmente mejor para prosa porque el recuento de palabras sigue al de tokens más de cerca que el de caracteres, y agrupar frases enteras evita cortes a mitad de frase. `DelimiterTextSplitter` es mejor cuando tu contenido tiene un delimitador estructural por el que merezca la pena cortar, lo que nos lleva a la parte importante.

### Divisores propios: el código con más palanca de tu RAG

```php
namespace NeuronAI\RAG\Splitter;

use NeuronAI\RAG\Document;

interface SplitterInterface
{
    /**
     * @return Document[]
     */
    public function splitDocument(Document $document): array;

    /**
     * @param  Document[]  $documents
     * @return Document[]
     */
    public function splitDocuments(array $documents): array;
}
```

Dos métodos. Aquí va un divisor por encabezados de Markdown —quizá cuarenta líneas— que superará a cualquier divisor genérico sobre documentación:

```php
<?php

declare(strict_types=1);

namespace App\Rag;

use NeuronAI\RAG\Document;
use NeuronAI\RAG\Splitter\SplitterInterface;

class MarkdownSectionSplitter implements SplitterInterface
{
    public function __construct(
        private readonly int $maxChars = 2000,
    ) {}

    public function splitDocument(Document $document): array
    {
        // Split on level-2 headings, keeping the heading with its section
        $parts = \preg_split(
            '/^(?=##\s)/m',
            $document->getContent(),
            -1,
            PREG_SPLIT_NO_EMPTY
        ) ?: [];

        $chunks = [];

        foreach ($parts as $part) {
            $part = \trim($part);

            if ($part === '') {
                continue;
            }

            // Fall back to paragraph splitting for oversized sections
            if (\mb_strlen($part) > $this->maxChars) {
                foreach ($this->splitLongSection($part) as $piece) {
                    $chunks[] = $piece;
                }
                continue;
            }

            $chunks[] = $part;
        }

        return \array_map(
            fn (string $text): Document => new Document($text),
            $chunks
        );
    }

    public function splitDocuments(array $documents): array
    {
        $result = [];

        foreach ($documents as $document) {
            foreach ($this->splitDocument($document) as $chunk) {
                $result[] = $chunk;
            }
        }

        return $result;
    }

    /**
     * @return string[]
     */
    private function splitLongSection(string $section): array
    {
        $paragraphs = \preg_split('/\n{2,}/', $section) ?: [];

        $chunks  = [];
        $current = '';

        foreach ($paragraphs as $paragraph) {
            if (\mb_strlen($current . "\n\n" . $paragraph) > $this->maxChars && $current !== '') {
                $chunks[] = \trim($current);
                $current  = $paragraph;
                continue;
            }

            $current = $current === '' ? $paragraph : $current . "\n\n" . $paragraph;
        }

        if (\trim($current) !== '') {
            $chunks[] = \trim($current);
        }

        return $chunks;
    }
}
```

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();
```

::: {.callout .callout-warning}
[Verifica la API de Document]{.callout-title}

Confirma la firma del constructor de `Document` y el accesor de contenido en tu versión instalada: los documentos muestran `Document` en las firmas de interfaz pero nunca lo muestran construyéndose. Ajusta `new Document($text)` y `getContent()` en consecuencia. Apéndice A, punto 29.
:::

### Por qué esto importa tanto

Cada fragmento que esto produce es una sección completa y autocontenida con su propio encabezado. Un acierto de recuperación trae de vuelta una unidad coherente en lugar de una ventana arbitraria de 1.000 caracteres que empieza a mitad de frase.

**El encabezado también forma parte del texto embebido**, lo que significa que una pregunta formulada como el encabezado casa con fuerza. Es un aumento de relevancia gratuito, puramente por respetar la estructura propia del documento.

El principio general: **la mejor estrategia de chunking es la que tu documento ya tiene.** El Markdown tiene encabezados. El código tiene funciones. Las transcripciones tienen hablantes. Úsalos.

### Puntos clave

- `withSplitter()` en cualquier cargador de datos.
- `DelimiterTextSplitter` para delimitadores estructurales; `SentenceTextSplitter` para prosa.
- `SplitterInterface` son dos métodos: un divisor propio es trabajo de una tarde.
- Respeta la estructura propia del documento; es la mayor palanca de calidad en RAG.

## 12.4 Proveedores de incrustaciones

### La interfaz

```php
protected function embeddings(): EmbeddingsProviderInterface
{
    return new OpenAIEmbeddingsProvider(
        key: 'OPENAI_API_KEY',
        model: 'OPENAI_MODEL'
    );
}
```

La misma forma que cualquier otro componente. Intercambiable, con una salvedad muy grande.

### Incrustaciones locales con Ollama

```php
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Embeddings\OllamaEmbeddingsProvider;

class MyRAG extends RAG
{
    protected function embeddings(): EmbeddingsProviderInterface
    {
        return new OllamaEmbeddingsProvider(
            model: 'OLLAMA_EMBEDDINGS_MODEL'
        );
    }
}
```

Sin clave de API, sin coste, sin que los datos salgan de la máquina.

```bash
ollama pull nomic-embed-text
```

**Usa esto en todos los laboratorios de la Parte III.** Combinado con un modelo de chat local de la Sección 3.6, toda la parte de RAG no cuesta nada de recorrer.

Es además una elección legítima de producción. Los modelos de incrustación son pequeños y rápidos; ejecutar uno en local es muy distinto de ejecutar en local un modelo de chat de frontera.

### Opciones alojadas

`OpenAIEmbeddingsProvider`, `VoyageEmbeddingsProvider` y otros. Voyage en particular merece conocerse: se especializa en incrustaciones para recuperación y a menudo supera a los modelos de propósito general en benchmarks de RAG.

### Proveedores propios

Extiende `AbstractEmbeddingsProvider`. La misma historia de extensión que en cualquier otro punto del framework.

### La salvedad que no es como las demás

La Sección 3.6 enseñó que cambiar de proveedor es un cambio de una línea. **Las incrustaciones son la excepción.**

Cambia el modelo de incrustaciones y todos los vectores de tu almacén se vuelven carentes de sentido. Son coordenadas en otro espacio. La recuperación devolverá resultados —no fallará ruidosamente— y estarán mal.

**Cambiar el modelo de incrustaciones significa reembeber todo el corpus.**

Tres consecuencias prácticas:

- Registra qué modelo produjo tu índice. En el nombre del almacén, en un campo de metadatos, en una nota de despliegue: en algún sitio.
- Presupuesta el tiempo de reembebido antes de cambiar. Millones de fragmentos son horas y dinero real.
- Nunca hagas del modelo de incrustaciones una variable de entorno que difiera entre entornos. Desarrollo con `nomic-embed-text` y producción con `text-embedding-3-large` significa que tu índice de desarrollo y el de producción son incompatibles, y el error será desconcertante.

Esa última es una trampa genuinamente desagradable, y es el error natural de alguien que acaba de aprender el patrón `ProviderFactory` de la Sección 3.6.

### Dimensiones

Distintos modelos producen vectores de distinta longitud: 768, 1024, 1536 y otras. Tu almacén vectorial debe estar configurado para coincidir. `TypesenseVectorStore` recibe `vectorDimension: 1024`; el esquema de MariaDB declara `VECTOR(1536)`.

Un desajuste significa o un error duro o disparates silenciosos, según el almacén. Compruébalo al configurarlo.

### Puntos clave

- `OllamaEmbeddingsProvider` se ejecuta en local, gratis: úsalo en todos los laboratorios.
- Las opciones alojadas incluyen OpenAI y Voyage; Voyage está especializado en recuperación.
- **Cambiar el modelo de incrustaciones invalida todo tu índice.**
- Nunca varíes el modelo de incrustaciones entre entornos.
- Las dimensiones de los vectores deben coincidir con la configuración de tu almacén.

## 12.5 Almacenes vectoriales

### La interfaz

```php
namespace NeuronAI\RAG\VectorStore;

use NeuronAI\RAG\Document;

interface VectorStoreInterface
{
    public function addDocument(Document $document): void;

    /**
     * @param  Document[]  $documents
     */
    public function addDocuments(array $documents): void;

    public function deleteBySource(string $sourceName, string $sourceType): void;

    /**
     * Return docs most similar to the embedding.
     *
     * @param  float[]  $embedding
     * @return Document[]
     */
    public function similaritySearch(array $embedding, int $k = 4): iterable;
}
```

Cuatro métodos. Fíjate en `deleteBySource`: existe para dar soporte a la reindexación (Sección 12.6), lo que te dice que el framework trata la obsolescencia como un problema de primera clase y no como un añadido.

### El catálogo

**Memory** — volátil, solo la sesión actual. Para pruebas e interacciones desechables.

```php
return new MemoryVectorStore();
```

**File** — almacenamiento en el sistema de archivos, y mejor construido de lo que suena:

```php
return new FileVectorStore(
    directory: storage_path(),
    topK: 4
);
```

La documentación hace una observación que merece repetirse: usa **generadores de PHP** para leer documentos, así que nunca mantiene en memoria más de `topK` elementos mientras itera rápidamente. Puedes almacenar miles de documentos y la única restricción es cuánto puede tardar una búsqueda por similitud.

También tiene un uso de distribución: publicar un agente con el conocimiento ya horneado en un archivo. Es un patrón genuinamente bonito para una herramienta empaquetada o una demo.

**PHPVector** — PHP puro, sin servicio externo:

```bash
composer require neuron-core/php-vector
```

```php
use NeuronAI\PHPVector\PHPVector;

return new PHPVector(
    path: '/var/data/mydb',
    topK: 5,
);
```

Construido sobre `ezimuel/phpvector`. Implementa **HNSW** para búsqueda aproximada de vecinos más próximos y **BM25** para recuperación de texto completo, y ambos pueden combinarse en un pipeline de **búsqueda híbrida**.

**Esta es la entrada más interesante de la lista para un público de PHP.** Te da recuperación de nivel producción —incluida la búsqueda híbrida, que es una mejora de calidad genuina— sin ningún servicio que desplegar. Para una aplicación autoalojada, un SaaS pequeño o un cliente que no puede añadir infraestructura, es una opción seria y no un juguete.

**MariaDB** — vectores nativos desde la 11.7:

```sql
CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID NOT NULL PRIMARY KEY,
    content TEXT,
    sourceType VARCHAR(255),
    sourceName VARCHAR(255),
    metadata JSON,
    embedding VECTOR(1536) NOT NULL,
    VECTOR INDEX (embedding)
)
```

```php
return new MariaDBVectorStore(
    new \PDO(...), // Or get the PDO instance from the ORM
);
```

Para una empresa de PHP que ya ejecuta MariaDB, esta es la respuesta de producción con menos fricción: una tabla, ningún servicio nuevo, copias de seguridad y monitorización que ya tienes. Fíjate en el esquema: `sourceType` y `sourceName` están ahí para la reindexación, y `metadata JSON` para el filtrado.

**Gestionados y dedicados:** Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch. Cada uno recibe su propia configuración de conexión; varios necesitan su cliente oficial instalado vía Composer.

::: {.callout .callout-warning}
[No hay almacén pgvector]{.callout-title}

La lista de arriba está completa. Gran cantidad de material de terceros asume que NeuronAI incluye una integración con pgvector, porque pgvector es omnipresente en el ecosistema Python. No la incluye. Si estás en Postgres y quieres soporte de primera parte, tus opciones son PHPVector (al que le da igual qué base de datos ejecutes) o uno de los almacenes dedicados.
:::

### La tabla de decisión

| Situación | Almacén |
|---|---|
| Pruebas unitarias | Memory |
| Laboratorios, prototipos, corpus pequeños | File |
| Autoalojado, sin infraestructura nueva, quieres búsqueda híbrida | **PHPVector** |
| Ya ejecutas MariaDB 11.7+ | **MariaDB** |
| Ya ejecutas Elasticsearch u OpenSearch | Ese mismo |
| Quieres gestionado, miles de millones de vectores | Pinecone |
| Quieres dedicado y de código abierto | Qdrant, Weaviate, Chroma |

**La regla general: usa lo que ya ejecutas.** Una base de datos nueva es una nueva historia de copias de seguridad, una nueva historia de monitorización y un nuevo modo de fallo. PHPVector y MariaDB existen precisamente para que la mayoría de los equipos de PHP no necesiten nada de eso.

### Búsqueda híbrida con filtros

Varios almacenes admiten filtrar por metadatos junto a la similitud vectorial. El patrón que da la documentación:

```php
class MyChatBot extends RAG
{
    protected array $vectorStoreFilters = [];

    protected function vectorStore(): VectorStoreInterface
    {
        $store = new PineconeVectorStore(
            key: 'PINECONE_API_KEY',
            indexUrl: 'PINECONE_INDEX_URL'
        );

        return $store->withFilters($this->vectorStoreFilters);
    }

    public function addVectorStoreFilters(array $filters): self
    {
        $this->vectorStoreFilters = $filters;
        return $this;
    }
}
```

```php
$response = MyRAG::make()
    ->addVectorStoreFilters([
        // Add filters
    ])
    ->chat(new UserMessage(...))
    ->getMessage();
```

**Este es el mecanismo del RAG multi-tenant**, y es lo bastante importante como para señalarlo bien alto. Filtrar por `tenant_id` en tiempo de consulta significa que la búsqueda del usuario A no puede devolver documentos del usuario B. Sin ello, un almacén vectorial compartido se filtra entre inquilinos, lo que es una violación de datos y no un error menor.

El Capítulo 20 lo construye como es debido en Laravel.

::: {.callout .callout-warning}
[¿Singular o plural?]{.callout-title}

El ejemplo de Pinecone llama a `withFilters()` y el de Elasticsearch a `withFilter()`. Comprueba ambos contra tu almacén. Apéndice A, punto 26.
:::

### Almacenes propios

Implementa la interfaz. Dos detalles que la documentación señala:

**Devuelve puntuaciones, no distancias.** Convierte con `VectorSimilarity::similarityFromDistance()`.

**`addDocument()` puede delegar en `addDocuments()`** si tu base de datos no tiene una API separada para elementos individuales. Los dos métodos existen porque muchas bases de datos sí la tienen.

Los mantenedores invitan explícitamente a enviar pull requests con nuevos almacenes. Si quieres una contribución de código abierto bien acotada y genuinamente útil, esta es una.

### Puntos clave

- Interfaz de cuatro métodos; `deleteBySource` existe para la reindexación.
- `FileVectorStore` usa generadores y escala más de lo que se espera.
- **PHPVector** da búsqueda híbrida HNSW + BM25 con cero infraestructura.
- **MariaDB 11.7+** es la opción de producción con menos fricción para la mayoría de las empresas de PHP.
- Los filtros por metadatos son cómo se hace RAG multi-tenant con seguridad.
- Usa lo que ya ejecutas.

## 12.6 Metadatos y reindexación

### Metadatos

```php
$documents = FileDataLoader::for($directory)->getDocuments();

foreach ($documents as $document) {
    $document->addMetadata('user_id', 1234);
}

MyRAG::make()->addDocuments($documents);
```

Campos propios guardados junto a los campos por defecto del documento en el almacén.

### Qué adjuntar

Piensa en los metadatos como las columnas por las que querrás filtrar más adelante. Una vez construido el índice, añadir un campo significa reindexar, así que decide ahora:

```php
foreach ($documents as $document) {
    $document->addMetadata('tenant_id',   $tenant->id);
    $document->addMetadata('visibility',  'internal');
    $document->addMetadata('language',    'en');
    $document->addMetadata('updated_at',  $article->updated_at->toDateString());
    $document->addMetadata('category',    $article->category);
}
```

Cuatro cosas que casi siempre merece la pena adjuntar:

**Inquilino o propietario.** El límite de seguridad para la recuperación multi-tenant. No negociable si sirves a más de un cliente desde un índice.

**Visibilidad o nivel de permiso.** Para que un agente de cara al público no pueda recuperar documentos internos.

**Idioma.** La recuperación entre idiomas mayormente funciona y ocasionalmente produce resultados confusos.

**Frescura.** Una fecha te permite preferir o filtrar contenido reciente, útil cuando las versiones vieja y nueva de una política viven ambas en el índice.

### Búsqueda híbrida

Una vez los campos están en el almacén, las bases de datos compatibles pueden restringir una búsqueda semántica a los registros que cumplen criterios sobre otros campos, en lugar de comparar solo las incrustaciones vectoriales.

El encuadre de seguridad es con el que hay que empezar: **el filtro de permisos debe aplicarse en la recuperación, no después.** Recuperar un documento que el usuario no puede ver y luego filtrarlo fuera de la respuesta significa que estuvo en el contexto del modelo, y los modelos parafrasean. El documento se filtró aunque nunca se mostrara.

Filtra en el almacén. Siempre.

### Reindexación

La documentación es franca al decir que este es un tema candente en el diseño de RAG: el chunking hace difícil actualizar piezas individuales de información cuando la fuente cambia.

La respuesta de NeuronAI son metadatos que identifican la procedencia. La clase `Document` lleva `sourceType` y `sourceName`, y:

```php
$documents = FileDataLoader::for("/path/to/directory")
    ->withSplitter(
        new SentenceTextSplitter(
            maxWords: 200,
            overlapWords: 0
        )
    )
    ->getDocuments();

MyRAG::make()->reindexBySource($documents);
```

Si `sourceType` y `sourceName` ya existen en el almacén, **esos documentos se borran y se sustituyen** por los fragmentos de la nueva versión. Todo lo demás se guarda normalmente.

Esa es la operación que resuelve el modo de fallo 6 de la Sección 11.5, y es por lo que `deleteBySource()` está en la interfaz del almacén.

### La restricción que pillará a alguien

> La nueva versión del archivo **debe tener la misma ruta y el mismo nombre** que la original; de lo contrario, los documentos se añaden como nuevos.

Renombra el archivo, reindexa y tendrás ambas versiones en el almacén: los fragmentos viejos huérfanos y no borrables por fuente, y los nuevos junto a ellos. El agente recuperará de ambos y responderá desde el que haya casado mejor.

**En la práctica:** usa un identificador estable, no un nombre de archivo que refleje el contenido. `policies/refund-policy.md` sobrevive a una edición. `policies/refund-policy-v3-final-2026.md` no.

Para la ingesta con `StringDataLoader` desde una base de datos, aplica la misma lógica: pon `sourceName` a la clave primaria del registro, no a su título.

### Una estrategia de ingesta que conviene adoptar

```php
// Re-index a single article after it changes
$documents = StringDataLoader::for($article->body)->getDocuments();

foreach ($documents as $document) {
    $document->addMetadata('tenant_id', $article->tenant_id);
    // sourceName should identify the article stably — the ID, not the title
}

$rag->reindexBySource($documents);
```

Engancha esto al evento `saved` de tu modelo y envíalo a una cola. El índice se mantiene al día sin ningún cron y sin deriva. El Capítulo 20 construye exactamente esto.

### Puntos clave

- `addMetadata()` antes de `addDocuments()`; los campos son tus futuros filtros.
- Adjunta inquilino, visibilidad, idioma y frescura por defecto.
- Filtra los permisos **en la recuperación**: el postfiltrado es una fuga.
- `reindexBySource()` sustituye los fragmentos de una fuente; `sourceName` debe ser estable.
- Usa IDs de registro, no títulos, como nombres de fuente.

## 12.7 El flujo de trabajo de RAG: procesadores previos y posteriores

### El pipeline

Cuando un `UserMessage` entra en un agente RAG, se ejecutan seis nodos en orden:

```
UserMessage
    │
    ├─ PreProcessQueryNode        ← reescribe / expande la consulta
    ├─ RetrieveDocumentsNode      ← ejecuta la estrategia de recuperación
    ├─ PostProcessDocumentsNode   ← reordena / filtra los resultados
    ├─ EnrichInstructionsNode     ← inyecta los documentos en el prompt de sistema
    ├─ ChatNode                   ← ejecuta la inferencia
    └─ ToolNode                   ← ejecuta las herramientas, si las hay
    │
AssistantMessage
```

**Esta es la recompensa de la Sección 2.3.** Un agente RAG es un flujo de trabajo, sus nodos tienen nombre, y conocer los nombres te permite enganchar el sistema con middleware. Todo lo de la Parte IV aplica aquí.

También se proyecta con precisión sobre los modos de fallo de la Sección 11.5:

| Fallo | Nodo que lo arregla |
|---|---|
| La pregunta no se parece a la respuesta | `PreProcessQueryNode` |
| Similar pero no relevante | `PostProcessDocumentsNode` |
| Alucinación | `EnrichInstructionsNode` + instrucciones |
| La respuesta abarca varios fragmentos | Estrategia de recuperación + reordenación |

### Procesadores previos: arreglar la consulta

`PreProcessQueryNode` ejecuta el pipeline de procesadores previos. El ejemplo integrado es `QueryTransformationPreProcessor`, que refuerza el prompt de entrada antes de embeberlo.

Por qué ayuda: los usuarios formulan preguntas en el lenguaje de los *problemas*; los documentos están escritos en el lenguaje de las *soluciones*. «¿Por qué está roto mi trasto?» y «El código de error 4021 indica asignación de disco insuficiente» están semánticamente lejos. Un paso de transformación reescribe la pregunta en algo más cercano a cómo está formulada la respuesta —o la expande en varias variantes— antes de que ocurra la incrustación.

El coste es una llamada extra al modelo por consulta, que es real. Mide si se gana su sitio en tu corpus; en documentación técnica normalmente sí, en contenido tipo preguntas frecuentes a menudo no.

### Procesadores posteriores: arreglar los resultados

`PostProcessDocumentsNode` ejecuta el pipeline de procesadores posteriores, y la reordenación es la razón de que exista.

```php
use NeuronAI\RAG\PostProcessor\JinaRerankerPostProcessor;
```

**Por qué funciona la reordenación, y por qué es la incorporación con mayor retorno a un sistema RAG que ya funciona:**

La búsqueda vectorial compara dos incrustaciones calculadas *de forma independiente*. La consulta se comprimió en un vector sin saber nada de los documentos; cada documento se comprimió sin saber nada de la consulta. Se pierde información en ambas compresiones.

Un reranker lee la consulta y un documento **juntos** y puntúa su relación directamente. Es muchísimo más lento por par, y por eso no puedes usarlo para buscar entre millones de documentos, pero sobre 50 candidatos es rápido y captura señales de relevancia que la comparación vectorial no podía representar.

La forma estándar del pipeline:

```
Búsqueda vectorial → 50 candidatos → reordenación → 5 mejores → enviar al modelo
```

Obtienes la cobertura de una búsqueda amplia y la precisión de una cuidadosa, y le envías al modelo menos fragmentos y mejores, lo que además reduce tokens.

### Estrategia de recuperación

`RetrieveDocumentsNode` ejecuta la estrategia de recuperación, y NeuronAI permite personalizar esa estrategia, incluida la recuperación desde fuentes de datos externas y no solo desde el almacén vectorial.

Ese es el punto de extensión para cualquier cosa inusual: una búsqueda híbrida que combine BM25 y vectores, recuperación multiconsulta para preguntas que abarcan varios fragmentos, o tirar de una API de búsqueda junto a tu propio índice.

### EnrichInstructionsNode: donde se combate la alucinación

Este nodo añade los documentos recuperados al prompt de sistema del agente.

Lo que significa que el prompt de sistema es donde restringes el uso que el modelo hace de ellos. Combina el mecanismo del nodo con tus `instructions()`:

```php
protected function instructions(): string
{
    return (string) new SystemPrompt(
        background: [
            'You answer questions using only the documents provided in your context.',
            'You are not a general-purpose assistant. Outside these documents you know nothing.',
        ],
        steps: [
            'Read the provided documents.',
            'If they contain the answer, give it and name the source document.',
            'If they do not, say clearly that the information is not in the knowledge base. '
            . 'Do not answer from general knowledge.',
        ],
        output: [
            'Cite the source of every factual claim.',
            'Never present an inference as something the documents state.',
        ],
    );
}
```

Esas instrucciones más un `FaithfulnessJudge` en tu suite de evaluación son las dos mitades de la historia antialucinación: una la reduce, la otra te dice si funcionó.

### Middleware en los nodos de RAG

Como estos son nodos de flujo de trabajo, el middleware los apunta por nombre: la misma API que `Neuron::middleware(ToolNode::class, ...)` de la Sección 2.3.

Aplicaciones útiles:

- Registrar cada recuperación: consulta, documentos devueltos, puntuaciones. Esta es tu herramienta de depuración de RAG.
- Imponer una puntuación mínima de similitud, descartando coincidencias débiles antes de que lleguen al modelo.
- Cachear resultados de recuperación para consultas repetidas.
- Censurar contenido sensible de los documentos antes de que entren en el prompt.

El Capítulo 15 cubre el middleware como es debido.

### Puntos clave

- Seis nodos: preprocesar, recuperar, posprocesar, enriquecer, chatear, herramientas.
- Los procesadores previos arreglan el desajuste consulta/respuesta a cambio de una llamada al modelo.
- **La reordenación es la mejora con mayor retorno para un sistema RAG que ya funciona**: recupera 50, reordena, envía 5.
- `EnrichInstructionsNode` más instrucciones estrictas es el mecanismo antialucinación.
- Los nodos tienen nombre, así que el middleware puede engancharse a cada etapa.

## Laboratorio 8 — RAG sobre documentación, a coste cero

**Cubre:** clase RAG, cargador de archivos, divisor propio, incrustaciones locales, almacén en archivo.

### Objetivo

Hacer preguntas a una carpeta de documentación en Markdown, sin claves de API y sin infraestructura. Todo local, todo gratis.

### Requisitos previos

```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### El agente

**`src/Rag/DocsAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Rag;

use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Ollama\Ollama;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Embeddings\OllamaEmbeddingsProvider;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\FileVectorStore;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class DocsAgent extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return new Ollama(
            url: env('OLLAMA_URL', 'http://localhost:11434/api'),
            model: env('OLLAMA_MODEL', 'qwen2.5:7b'),
        );
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return new OllamaEmbeddingsProvider(
            model: env('OLLAMA_EMBEDDINGS_MODEL', 'nomic-embed-text'),
        );
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return new FileVectorStore(
            directory: \dirname(__DIR__, 2) . '/storage/vectors',
            topK: 5,
        );
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You answer questions about a software project using only its documentation.',
                'Outside the provided documents you know nothing about this project.',
            ],
            steps: [
                'Read the documents provided in your context.',
                'If they answer the question, answer and name the source.',
                'If they do not, say the documentation does not cover it.',
            ],
            output: [
                'Be concise. Include a short code example when the documents contain one.',
                'Always end with the source section heading you used.',
            ],
        );
    }
}
```

### El script de ingesta

**`examples/08-index-docs.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Rag\DocsAgent;
use App\Rag\MarkdownSectionSplitter;
use NeuronAI\RAG\DataLoader\FileDataLoader;

$directory = $argv[1] ?? __DIR__ . '/fixtures/docs';

if (!\is_dir($directory)) {
    \fwrite(STDERR, "Not a directory: {$directory}\n");
    exit(1);
}

$start = \microtime(true);

$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();

\printf("Split into %d chunks.\n", \count($documents));

DocsAgent::make()->addDocuments($documents);

\printf("Indexed in %.1fs.\n", \microtime(true) - $start);
```

### El script de consulta

**`examples/09-ask-docs.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Rag\DocsAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'How do I configure the vector store?';

echo DocsAgent::make()
    ->chat(new UserMessage($question))
    ->getMessage()
    ->getContent() . PHP_EOL;
```

```bash
php examples/08-index-docs.php ./docs
php examples/09-ask-docs.php "How do I add a custom tool?"
php examples/09-ask-docs.php "What is the airspeed velocity of an unladen swallow?"
```

### La prueba que importa

Esa última pregunta es el objetivo del laboratorio. **El agente debería decir que la documentación no lo cubre.**

Si responde igualmente, acabas de reproducir el modo de fallo 5 de la Sección 11.5 en tu propia máquina, y puedes arreglarlo reforzando las secciones `steps` y `background`. Ese es un resultado mucho más útil que una consulta exitosa.

### Criterios de aceptación

- La indexación reporta un número de fragmentos coherente con el número de encabezados `##` de tu corpus, no un número redondo que sugiera división por recuento de caracteres.
- Una pregunta formulada como un encabezado devuelve esa sección.
- Una pregunta fuera de ámbito se rechaza explícitamente, sin una respuesta inventada plausible.
- Borrar el directorio del almacén vectorial y volver a ejecutar la indexación produce las mismas respuestas.

### Extensiones

1. Compara `MarkdownSectionSplitter` con el `DelimiterTextSplitter` por defecto sobre las mismas preguntas.
2. Cambia `topK` de 5 a 2 y a 10. Observa la calidad de las respuestas y la latencia.
3. Edita un archivo fuente, vuelve a ejecutar la indexación con `reindexBySource()` y confirma que los fragmentos viejos han desaparecido.

## Laboratorio 9 — Almacén de producción con búsqueda híbrida

**Cubre:** PHPVector, metadatos, filtros, evaluación.

### Objetivo

Mover el Laboratorio 8 a un almacén con capacidades de recuperación reales, añadir filtrado por metadatos y medir si realmente mejoró algo.

### Instalar

```bash
composer require neuron-core/php-vector
```

### Cambiar el almacén

```php
use NeuronAI\PHPVector\PHPVector;

protected function vectorStore(): VectorStoreInterface
{
    return new PHPVector(
        path: \dirname(__DIR__, 2) . '/storage/phpvector',
        topK: 5,
    );
}
```

Un método cambiado. Todo lo demás —el agente, el cargador, el divisor, los scripts— queda intacto. Esa es la arquitectura guiada por interfaces de la Sección 2.2 dando frutos en la capa de datos, y resulta más convincente verlo ocurrir que leerlo.

PHPVector implementa HNSW para búsqueda aproximada de vecinos más próximos y BM25 para recuperación de texto completo, y puede combinar ambos en búsqueda híbrida.

### Añadir metadatos durante la ingesta

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();

foreach ($documents as $document) {
    $document->addMetadata('section',  $this->detectSection($document));
    $document->addMetadata('language', 'en');
}

DocsAgent::make()->addDocuments($documents);
```

### Mídelo

Construye un evaluador (Capítulo 10) con quince preguntas reales sobre tu documentación:

```php
namespace App\Neuron\Evaluators;

use NeuronAI\Evaluation\Assertions\Judges\FaithfulnessJudge;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;

class DocsRagEvaluator extends BaseEvaluator
{
    protected AgentInterface $judge;

    public function setUp(): void
    {
        $this->judge = /* a cheap judge agent */;
    }

    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(__DIR__ . '/datasets/docs-questions.json');
    }

    public function run(array $item): mixed
    {
        return DocsAgent::make()
            ->chat(new UserMessage($item['question']))
            ->getMessage()
            ->getContent();
    }

    public function evaluate(mixed $output, array $item): void
    {
        $this->assert(new StringContainsAny($item['expected_keywords']), $output);

        $this->assert(new FaithfulnessJudge(
            judge: $this->judge,
            context: $item['source_excerpt'],
            threshold: 0.7,
        ), $output);
    }
}
```

Ejecútalo contra ambos almacenes y ambos divisores. Cuatro configuraciones, un número cada una.

**Esa tabla es el entregable de este laboratorio.** No el código: la medición. Es la diferencia entre «mejoramos el RAG» y «la fidelidad pasó de 0,62 a 0,81 al cambiar de divisor, y cambiar de almacén no cambió nada».

El segundo hallazgo es tan valioso como el primero, y es el tipo de resultado que nunca obtendrás suponiendo.

### Criterios de aceptación

- Solo `vectorStore()` difiere entre los agentes del Laboratorio 8 y del 9.
- Tienes una tabla de cuatro filas con puntuaciones de fidelidad.
- Una consulta filtrada por metadatos demostrablemente no puede devolver documentos fuera de ese filtro; pruébalo con documentos de dos inquilinos en un mismo índice.

## Ejercicios del capítulo

1. **Compara divisores.** Indexa un corpus de documentación real con el divisor por defecto y con uno propio. Compara sobre quince preguntas, usando el evaluador en lugar de tu impresión.
2. **Demuestra el aislamiento.** Añade metadatos de inquilino y verifica que una consulta filtrada no puede devolver documentos de otro inquilino. Es una prueba de seguridad; escríbelo como tal.
3. **Reindexa.** Cambia un archivo fuente y reindexa con `reindexBySource()`. Confirma que los fragmentos viejos han desaparecido consultando una frase que borraste.
4. **Informa.** Registra la puntuación de fidelidad de cada configuración y escribe el resumen de un párrafo que le enviarías a un cliente. Si el resumen honesto es «el cambio caro no hizo nada», esa es la frase más valiosa del informe.
