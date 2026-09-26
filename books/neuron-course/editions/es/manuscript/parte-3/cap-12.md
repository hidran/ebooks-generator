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

$state = MyChatBot::make()
    ->chat(new UserMessage('I want to know more about Inspector AI Bug Fix.'));

echo $state->getMessage()?->getContent();
```

`chat()`: el mismo método que en un agente corriente, que devuelve el mismo `AgentState` final. La recuperación ocurre dentro, automáticamente. Desde el lado que llama, un agente RAG y un agente normal son indistinguibles. (`getMessage()` admite null porque una ejecución que se pausó antes de cualquier inferencia —una herramienta a la espera de aprobación, por ejemplo— todavía no tiene respuesta; de ahí el `?->`).

### RAG *es* un Agent

Esta es la Sección 2.3 llegando por tercera vez, y tiene consecuencias prácticas:

> La clase `RAG` de NeuronAI extiende la clase básica `Agent`. Tu RAG siempre es un agente, así que puedes engancharle herramientas y definir instrucciones de sistema.

Lo que significa que un agente RAG hereda, gratis:

- `instructions()` y `SystemPrompt`
- `tools()` y juegos de herramientas
- `chatHistory()`
- `structured()`
- `stream()`
- `subscribe()` para los eventos de trazado
- identidad del hilo, persistencia y reanudación
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

La documentación ha mostrado `FileVectorStore` de varias formas en varias páginas: `name:` en una, `topK:` en otra y, en algún momento, un argumento `key:` bajo un nombre de clase con errata, `FileVectoreStore`. Lo mismo ocurre con `OpenAIEmbeddingsProvider` frente a `OpenAIEmbeddingProvider`, y con `RAG\Embeddings\` frente a `RAG\EmbeddingProvider\`. Apéndice A, puntos del 22 al 25.

El código fuente zanja la cuestión. El constructor es `FileVectorStore(string $directory, int $topK = 4, string $name = 'neuron', string $ext = '.store', ?DocumentSchema $schema = null)` —no existe `key:`— y las clases de incrustaciones viven en `NeuronAI\RAG\Embeddings\`, con la `s`. Este es el código de mayor tráfico de la Parte III: abre la clase en tu editor y compruébala antes de escribir un script de ingesta, no después.
:::

### Puntos clave

- Tres métodos: `provider()`, `embeddings()`, `vectorStore()`.
- El modelo de chat y el de incrustaciones son elecciones independientes.
- `chat()` devuelve el mismo `AgentState` que cualquier agente; la recuperación es interna.
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

Es lo que usa cualquier cargador de datos cuando no llamas a `withSplitter()`:

```php
new DelimiterTextSplitter(
    maxLength: 1000,
    separator: '.',
    wordOverlap: 0
)
```

Los tres parámetros de la Sección 11.3, en código:

- **`maxLength`** — fragmentos no más largos que esto
- **`separator`** — dónde se permite cortar; los cargadores pasan el punto
- **`wordOverlap`** — palabras arrastradas entre fragmentos; cero por defecto

Si construyes la clase tú mismo, el separador por defecto es un espacio, no un punto: un motivo más para pasar los tres explícitamente. Un cuarto parámetro opcional, `minLength`, une al fragmento anterior cualquier trozo más corto que ese umbral, para que una frase de cierre suelta no se convierta en un fragmento propio.

La documentación es explícita en que cada uno de ellos afecta al rendimiento y a la precisión. No son valores por defecto que aceptar; son decisiones que tomar.

### SentenceTextSplitter

```php
new SentenceTextSplitter(
    maxWords: 200,
    overlapWords: 0
)
```

Divide en frases, las agrupa en fragmentos basados en número de palabras y opcionalmente solapa por palabras. Su `minWords` cumple la misma función que `minLength`.

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

        // Each chunk keeps its parent's provenance and metadata
        return \array_map(
            fn (string $text): Document => (new Document($text))
                ->setSourceType($document->getSourceType())
                ->setSourceName($document->getSourceName())
                ->setMetadata($document->getMetadata()),
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
[Un fragmento debe heredar la procedencia de su padre]{.callout-title}

La documentación muestra `Document` en las firmas de interfaz pero nunca lo muestra construyéndose (Apéndice A, punto 29). La clase zanja la cuestión: `new Document(string $content)` y después setters fluidos —`setSourceType()`, `setSourceName()`, `setMetadata()`— con un getter para cada uno. No hay propiedades públicas que tocar, y la clase es `final`.

Los tres setters de `splitDocument()` no son decoración. Un `new Document($text)` a secas se archiva con tipo y nombre de origen `manual`, así que cada fragmento perdería el archivo del que procede, `reindexBySource()` (Sección 12.6) nunca podría volver a encontrarlo y cualquier metadato de inquilino que hubieras adjuntado antes de dividir desaparecería. Los divisores integrados copian los tres; uno propio debe hacer lo mismo.
:::

### Por qué esto importa tanto

Cada fragmento que esto produce es una sección completa y autocontenida con su propio encabezado. Un acierto de recuperación trae de vuelta una unidad coherente en lugar de una ventana arbitraria de 1.000 caracteres que empieza a mitad de frase.

**El encabezado también forma parte del texto embebido**, lo que significa que una pregunta formulada como el encabezado casa con fuerza. Es un aumento de relevancia gratuito, puramente por respetar la estructura propia del documento.

El principio general: **la mejor estrategia de chunking es la que tu documento ya tiene.** El Markdown tiene encabezados. El código tiene funciones. Las transcripciones tienen hablantes. Úsalos.

### Puntos clave

- `withSplitter()` en cualquier cargador de datos.
- `DelimiterTextSplitter` para delimitadores estructurales; `SentenceTextSplitter` para prosa.
- `SplitterInterface` son dos métodos: un divisor propio es trabajo de una tarde. Copia el origen y los metadatos en cada fragmento.
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

Distintos modelos producen vectores de distinta longitud: 768, 1024, 1536 y otras. Tu almacén vectorial debe estar configurado para coincidir. `TypesenseVectorStore` recibe `vectorDimension: 1024`; `MariaDBVectorStore::setupTable(dimensions: 768)` crea una columna `VECTOR(768)`, y usa 1536 por defecto si no indicas nada.

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
use NeuronAI\RAG\Schema\DocumentSchema;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;

interface VectorStoreInterface
{
    public function getSchema(): DocumentSchema;

    public function addDocument(Document $document): VectorStoreInterface;

    /**
     * @param  Document[]  $documents
     */
    public function addDocuments(array $documents): VectorStoreInterface;

    /**
     * Delete every document matching the filters.
     */
    public function delete(FilterExpression $filters): VectorStoreInterface;

    /**
     * Return the documents most similar to the request's embedding.
     *
     * @return iterable<Document>
     */
    public function search(SearchRequest $request): iterable;
}
```

Cinco métodos. Tres de ellos dicen algo sobre las prioridades del framework.

`search()` recibe una `SearchRequest` —incrustación, filtros opcionales, `topK` opcional— construida de nuevo en cada llamada. Un almacén no guarda ningún estado de búsqueda, así que un filtro que fijes para una consulta no puede restringir, o dejar de restringir, en silencio la siguiente.

`delete()` recibe un filtro en lugar de un par de campos fijado en el código. Existe para dar soporte a la reindexación (Sección 12.6), lo que te dice que el framework trata la obsolescencia como un problema de primera clase y no como un añadido.

`getSchema()` devuelve el `DocumentSchema` del almacén: la declaración de qué campos de metadatos existen, de qué tipo son y por cuáles puedes filtrar. Configurarlo es opcional, y es central para el filtrado; ambas cosas se tratan más abajo.

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

La documentación hace una observación que merece repetirse: usa **generadores de PHP** para leer documentos, así que nunca mantiene en memoria más de `topK` elementos mientras itera rápidamente. Puedes almacenar miles de documentos y la única restricción es cuánto puede tardar una búsqueda por similitud. Crea el directorio y un archivo de almacén vacío al construirse, así que un almacén recién creado admite búsquedas, borrados o reindexaciones de inmediato.

También tiene un uso de distribución: publicar un agente con el conocimiento ya horneado en un archivo. Es un patrón genuinamente bonito para una herramienta empaquetada o una demo.

**PHPVector** — PHP puro, sin servicio externo. Construido sobre `ezimuel/phpvector`, implementa **HNSW** para búsqueda aproximada de vecinos más próximos y **BM25** para recuperación de texto completo, y combina ambos en un verdadero pipeline de **búsqueda híbrida**: clasificación vectorial y léxica a la vez. Eso lo convierte en la entrada más interesante de la lista para un público de PHP: recuperación de nivel producción sin ningún servicio que desplegar.

::: {.callout .callout-warning}
[PHPVector todavía no tiene versión para esta versión de NeuronAI]{.callout-title}

`neuron-core/php-vector` se publica aparte del framework y, en el momento de escribir esto, su última versión (1.1.0) todavía requiere `neuron-ai` 3.x. Composer se negará a instalarlo junto a la versión de este libro y, de todos modos, la versión 3.x implementa la antigua interfaz de almacén. Vigila el paquete hasta que salga una versión compatible con la interfaz `search()`/`delete()`/`getSchema()` de arriba; mientras tanto, los laboratorios de este capítulo usan `FileVectorStore` y `MariaDBVectorStore`, y el repositorio complementario no depende de él.
:::

**MariaDB** — vectores nativos desde la 11.7:

```php
$store = new MariaDBVectorStore(
    pdo: new \PDO(...), // Or get the PDO instance from the ORM
    tableName: 'rag_documents',
);

$store->setupTable(dimensions: 768); // once, at install time
```

`setupTable()` crea la tabla que el almacén espera:

```sql
CREATE TABLE IF NOT EXISTS rag_documents (
    id UUID NOT NULL PRIMARY KEY,
    content TEXT,
    sourceType VARCHAR(255),
    sourceName VARCHAR(255),
    metadata JSON,
    embedding VECTOR(768) NOT NULL,
    VECTOR INDEX (embedding)
)
```

Para una empresa de PHP que ya ejecuta MariaDB, esta es la respuesta de producción con menos fricción: una tabla, ningún servicio nuevo, copias de seguridad y monitorización que ya tienes. Fíjate en el esquema: `sourceType` y `sourceName` están ahí para la reindexación, y `metadata JSON` para el filtrado.

**Gestionados y dedicados:** Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch y MongoDB Atlas Vector Search. Cada uno recibe su propia configuración de conexión; varios necesitan su cliente oficial instalado vía Composer.

::: {.callout .callout-warning}
[No hay almacén pgvector]{.callout-title}

La lista de arriba está completa. Gran cantidad de material de terceros asume que NeuronAI incluye una integración con pgvector, porque pgvector es omnipresente en el ecosistema Python. No la incluye. Si estás en Postgres y quieres soporte de primera parte, tus opciones son uno de los almacenes dedicados o, cuando publique una versión compatible, PHPVector, al que le da igual qué base de datos ejecutes. Un almacén propio (más abajo) es la tercera vía.
:::

### La tabla de decisión

| Situación | Almacén |
|---|---|
| Pruebas unitarias | Memory |
| Laboratorios, prototipos, corpus pequeños | File |
| Ya ejecutas MariaDB 11.7+ | **MariaDB** |
| Autoalojado, sin infraestructura nueva, quieres búsqueda híbrida | PHPVector, cuando admita esta versión |
| Ya ejecutas Elasticsearch, OpenSearch o MongoDB Atlas | Ese mismo |
| Quieres gestionado, miles de millones de vectores | Pinecone |
| Quieres dedicado y de código abierto | Qdrant, Weaviate, Chroma |

**La regla general: usa lo que ya ejecutas.** Una base de datos nueva es una nueva historia de copias de seguridad, una nueva historia de monitorización y un nuevo modo de fallo. MariaDB —y PHPVector, cuando se ponga al día— existen precisamente para que la mayoría de los equipos de PHP no necesiten nada de eso.

### Búsqueda filtrada

Todos los almacenes integrados pueden restringir una búsqueda por similitud a los documentos cuyos metadatos cumplen una condición. Escribes la condición una sola vez, en un vocabulario portable, y cada almacén la compila a su propia sintaxis nativa: el mismo filtro se ejecuta en el almacén de archivos en desarrollo y en Pinecone o MariaDB en producción.

Dos piezas lo hacen funcionar. Al almacén se le dice qué campos de metadatos existen y cuáles son filtrables, mediante un `DocumentSchema`. El agente declara la restricción obligatoria de sus búsquedas en `retrievalScope()`:

```php
use NeuronAI\RAG\Schema\DocumentField;
use NeuronAI\RAG\Schema\DocumentSchema;
use NeuronAI\RAG\VectorStore\Filter\Filter;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;

class MyChatBot extends RAG
{
    protected ?string $tenantId = null;

    public function forTenant(string $tenantId): static
    {
        $this->tenantId = $tenantId;
        return $this;
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return new PineconeVectorStore(
            key: 'PINECONE_API_KEY',
            indexUrl: 'PINECONE_INDEX_URL',
            schema: DocumentSchema::of(
                DocumentField::string('tenant_id')->required()->filterable(),
                DocumentField::string('visibility')->required()->filterable(),
            ),
        );
    }

    protected function retrievalScope(): ?FilterExpression
    {
        if ($this->tenantId === null) {
            // Fail closed: an unscoped search would cross tenants
            throw new \LogicException('Call forTenant() before chatting.');
        }

        return Filter::where('tenant_id', $this->tenantId)
            ->where('visibility', 'public');
    }
}
```

```php
$response = MyChatBot::make()
    ->forTenant($tenant->uuid)
    ->chat(new UserMessage(...))
    ->getMessage();
```

**Este es el mecanismo del RAG multi-tenant**, y es lo bastante importante como para señalarlo bien alto. Filtrar por `tenant_id` en tiempo de consulta significa que la búsqueda del usuario A no puede devolver documentos del usuario B. Sin ello, un almacén vectorial compartido se filtra entre inquilinos, lo que es una violación de datos y no un error menor.

Fíjate en la guarda. Devolver `null` desde `retrievalScope()` significa «sin restricción», así que un inquilino ausente debe ser un error, nunca un respaldo silencioso que busque entre los documentos de todos.

El ámbito no es una sugerencia que el pipeline pueda ignorar. Cualquier otra cosa que añada un filtro durante una ejecución —un middleware, una estrategia de recuperación propia— se combina con él mediante AND, así que un filtro posterior puede estrechar la búsqueda pero nunca ampliarla. Cuando el valor solo se conoce en tiempo de ejecución, `setRetrievalScope()` fija lo mismo desde fuera de la clase.

El vocabulario cubre lo que las aplicaciones necesitan de verdad —`where()`, `whereNot()`, `whereIn()`, los rangos numéricos (`whereGreaterThan()`, `whereLessThanOrEqual()` y compañía), `whereContainsAny()`/`whereContainsAll()` para campos de listas de cadenas— más `FilterGroup::anyOf()` y `allOf()` para lógica OR/AND anidada. Para la rara funcionalidad del backend que quede fuera, `Filter::raw(PineconeVectorStore::class, $nativeFragment)` pasa la sintaxis nativa a ese almacén y hace que todos los demás lancen una excepción, de modo que cambiar de almacén falla de forma visible en lugar de filtrar mal en silencio.

El Capítulo 20 lo construye como es debido en Laravel.

::: {.callout .callout-warning}
[Un campo no declarado es un error duro, no un resultado vacío]{.callout-title}

Filtra por un campo de metadatos que el esquema del almacén no declara filtrable —una errata, o un campo que olvidaste declarar— y el almacén lanza una `DocumentSchemaException` antes de tocar la base de datos. Solo `sourceType`, `sourceName` y los campos declarados filtrables son destinos válidos de un filtro. Otras dos reglas que conviene conocer antes de diseñar el esquema: los valores de los filtros son escalares (`null` lanza una excepción, porque «ausente» y «null» significan cosas distintas en bases de datos distintas), y `whereNot()` solo se permite en un campo `required()`, por la misma razón.

Esa rigidez es la clave. Un filtro que en silencio no encontrara nada —o lo encontrara todo— en un backend y no en otro sería el peor tipo de error multi-tenant.
:::

### Almacenes propios

Implementa la interfaz. Importan cuatro detalles:

**Devuelve puntuaciones, no distancias.** Convierte con `VectorSimilarity::similarityFromDistance()`.

**Respeta el esquema.** Valida documentos y filtros contra `getSchema()` antes de cualquier E/S con la base de datos; el trait `HasDocumentSchema` que usan los almacenes integrados te da la fontanería.

**Compila o evalúa los filtros.** Traduce la `FilterExpression` a la sintaxis de tu backend o, en un almacén que recorre los datos en PHP, evalúala con `FilterEvaluator`, como hacen los almacenes de archivos y de memoria.

**`addDocument()` puede delegar en `addDocuments()`** si tu base de datos no tiene una API separada para elementos individuales. Los dos métodos existen porque muchas bases de datos sí la tienen.

Los mantenedores invitan explícitamente a enviar pull requests con nuevos almacenes. Si quieres una contribución de código abierto bien acotada y genuinamente útil, esta es una.

### Puntos clave

- Interfaz de cinco métodos; `search()` recibe una `SearchRequest` nueva en cada llamada, y `delete()` recibe un filtro.
- `FileVectorStore` usa generadores y escala más de lo que se espera.
- **MariaDB 11.7+** es la opción de producción con menos fricción para la mayoría de las empresas de PHP.
- La búsqueda híbrida HNSW + BM25 de PHPVector espera una versión para esta versión del framework.
- Declara los campos filtrables en un `DocumentSchema`; pon las restricciones obligatorias en `retrievalScope()`.
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

Campos propios guardados junto a los campos por defecto del documento en el almacén. Se acepta cualquier valor apto para JSON, y hace el viaje de ida y vuelta: se guarda y luego se devuelve en `getMetadata()` del documento recuperado. Un puñado de nombres (`id`, `content`, `embedding`, `score`, `sourceType`, `sourceName`, `metadata` y algunos internos de los backends) están reservados, y `addMetadata()` lanza una excepción si usas uno.

### Qué adjuntar

Piensa en los metadatos como las columnas por las que querrás filtrar más adelante. Una vez construido el índice, añadir un campo significa reindexar, así que decide ahora:

```php
foreach ($documents as $document) {
    $document->addMetadata('tenant_id',   $tenant->uuid);
    $document->addMetadata('visibility',  'internal');
    $document->addMetadata('language',    'en');
    $document->addMetadata('updated_at',  $article->updated_at->getTimestamp());
    $document->addMetadata('category',    $article->category);
}
```

Después informa al almacén de aquellos por los que vas a filtrar:

```php
$schema = DocumentSchema::of(
    DocumentField::string('tenant_id')->required()->filterable(),
    DocumentField::string('visibility')->required()->filterable(),
    DocumentField::string('language')->filterable(),
    DocumentField::integer('updated_at')->filterable(),
);
```

`category` no está declarado: se guarda y se devuelve, pero no es filtrable. Es una elección deliberada, no un resquicio: declara un campo cuando la base de datos necesita conocer su tipo, porque debe estar presente en todos los documentos (`required()`) o porque filtras por él (`filterable()`). Fíjate en que `updated_at` es una marca de tiempo entera, no una cadena de fecha: los filtros de rango son numéricos, y un `DateTimeInterface` pasado a un filtro de rango se convierte en marca de tiempo por ti.

`RAG::addDocuments()` valida cada documento contra el esquema *antes* de llamar al modelo de incrustaciones, así que un fragmento al que le falta su `tenant_id` falla enseguida en lugar de costarte una llamada de incrustación y un lote escrito a medias.

Cuatro cosas que casi siempre merece la pena adjuntar:

**Inquilino o propietario.** El límite de seguridad para la recuperación multi-tenant. No negociable si sirves a más de un cliente desde un índice.

**Visibilidad o nivel de permiso.** Para que un agente de cara al público no pueda recuperar documentos internos.

**Idioma.** La recuperación entre idiomas mayormente funciona y ocasionalmente produce resultados confusos.

**Frescura.** Una fecha te permite preferir o filtrar contenido reciente, útil cuando las versiones vieja y nueva de una política viven ambas en el índice.

### Filtrar en la recuperación

Una vez que los campos están en el almacén y declarados en su esquema, todos los almacenes integrados pueden restringir una búsqueda semántica a los registros que cumplen criterios sobre otros campos, en lugar de comparar solo las incrustaciones vectoriales. La documentación a veces lo llama búsqueda híbrida, pero el vocabulario del propio framework reserva ese término para combinar la clasificación vectorial y por palabras clave. Esto es búsqueda filtrada.

El encuadre de seguridad es con el que hay que empezar: **el filtro de permisos debe aplicarse en la recuperación, no después.** Recuperar un documento que el usuario no puede ver y luego filtrarlo fuera de la respuesta significa que estuvo en el contexto del modelo, y los modelos parafrasean. El documento se filtró aunque nunca se mostrara.

Filtra en el almacén. Siempre.

### Reindexación

La documentación es franca al decir que este es un tema candente en el diseño de RAG: el chunking hace difícil actualizar piezas individuales de información cuando la fuente cambia.

La respuesta de NeuronAI son metadatos que identifican la procedencia. Todo `Document` lleva un `sourceType` y un `sourceName` —`FileDataLoader` los fija en `files` y el nombre del archivo— y:

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

`reindexBySource()` agrupa los fragmentos nuevos por origen y, para cada par `sourceType`/`sourceName`, **borra los documentos existentes de ese origen y añade los fragmentos de la nueva versión**. Un origen que aún no está en el almacén simplemente se añade.

Esa es la operación que resuelve el modo de fallo 6 de la Sección 11.5, y es por lo que `delete()` está en la interfaz del almacén. Por debajo es un filtro corriente:

```php
$store->delete(
    Filter::where('sourceType', 'files')
        ->where('sourceName', 'refund-policy.md'),
);
```

El `addDocuments()` a secas no hace esa comprobación: ejecuta dos veces un script de ingesta con él y cada fragmento estará dos veces en el almacén.

### La restricción que pillará a alguien

> La nueva versión del archivo **debe tener la misma ruta y el mismo nombre** que la original; de lo contrario, los documentos se añaden como nuevos.

Renombra el archivo, reindexa y tendrás ambas versiones en el almacén: los fragmentos viejos huérfanos bajo un nombre de fuente que nada volverá a reindexar, y los nuevos junto a ellos. El agente recuperará de ambos y responderá desde el que haya casado mejor.

**En la práctica:** usa un identificador estable, no un nombre de archivo que refleje el contenido. `policies/refund-policy.md` sobrevive a una edición. `policies/refund-policy-v3-final-2026.md` no.

Para la ingesta con `StringDataLoader` desde una base de datos, aplica la misma lógica, con un paso extra: el cargador de cadenas archiva todo con tipo y nombre de origen `manual`, así que fijas los dos tú mismo: `sourceName` a la clave primaria del registro, no a su título.

### Una estrategia de ingesta que conviene adoptar

```php
// Re-index a single article after it changes
$documents = StringDataLoader::for($article->body)->getDocuments();

foreach ($documents as $document) {
    $document
        ->setSourceType('articles')
        ->setSourceName((string) $article->id) // the ID, never the title
        ->addMetadata('tenant_id', $article->tenant_uuid);
}

$rag->reindexBySource($documents);
```

Engancha esto al evento `saved` de tu modelo y envíalo a una cola. El índice se mantiene al día sin ningún cron y sin deriva. El Capítulo 20 construye exactamente esto.

### Puntos clave

- `addMetadata()` antes de `addDocuments()`; los campos son tus futuros filtros.
- Declara en el `DocumentSchema` del almacén los campos por los que filtras; los metadatos no declarados se guardan pero no son filtrables.
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
    ├─ PreProcessNode        ← reescribe / expande la consulta
    ├─ RetrievalNode         ← ejecuta la estrategia de recuperación
    ├─ PostProcessNode       ← reordena / filtra los resultados
    ├─ InstructionsNode      ← inyecta los documentos en el prompt de sistema
    ├─ ChatNode              ← ejecuta la inferencia
    └─ ToolNode              ← ejecuta las herramientas, si las hay
    │
AssistantMessage
```

Los cuatro primeros sustituyen al nodo inicial del agente simple; a partir de `ChatNode`, es el mismo bucle del agente que en el resto del libro.

**Esta es la recompensa de la Sección 2.3.** Un agente RAG es un flujo de trabajo, sus nodos tienen nombre, y conocer los nombres te permite enganchar el sistema con middleware. Todo lo de la Parte IV aplica aquí.

También se proyecta con precisión sobre los modos de fallo de la Sección 11.5:

| Fallo | Nodo que lo arregla |
|---|---|
| La pregunta no se parece a la respuesta | `PreProcessNode` |
| Similar pero no relevante | `PostProcessNode` |
| Alucinación | `InstructionsNode` + instrucciones |
| La respuesta abarca varios fragmentos | Estrategia de recuperación + reordenación |

### Procesadores previos: arreglar la consulta

`PreProcessNode` ejecuta el pipeline de procesadores previos. El ejemplo integrado es `QueryTransformationPreProcessor`, que pide a un modelo que reformule la pregunta antes de calcular su incrustación:

```php
use NeuronAI\RAG\PreProcessor\QueryTransformationPreProcessor;
use NeuronAI\RAG\PreProcessor\QueryTransformationType;

protected function preProcessors(): array
{
    return [
        new QueryTransformationPreProcessor(
            provider: $this->getProvider(),
            transformation: QueryTransformationType::REWRITING,
        ),
    ];
}
```

Por qué ayuda: los usuarios formulan preguntas en el lenguaje de los *problemas*; los documentos están escritos en el lenguaje de las *soluciones*. «¿Por qué está roto mi trasto?» y «El código de error 4021 indica asignación de disco insuficiente» están semánticamente lejos. Un paso de transformación reescribe la pregunta en algo más cercano a cómo está formulada la respuesta antes de que ocurra la incrustación. `REWRITING` es el valor por defecto; `DECOMPOSITION` descompone una pregunta compuesta en otras más simples, y `HYDE` hace que el modelo redacte una respuesta hipotética y calcula la incrustación de esta: una consulta con forma de respuesta casa con documentos con forma de respuesta.

El coste es una llamada extra al modelo por consulta, que es real. Mide si se gana su sitio en tu corpus; en documentación técnica normalmente sí, en contenido tipo preguntas frecuentes a menudo no. Para la reescritura suele bastar un proveedor más barato y rápido que tu modelo de chat principal.

### Procesadores posteriores: arreglar los resultados

`PostProcessNode` ejecuta el pipeline de procesadores posteriores, y la reordenación es la razón de que exista.

```php
use NeuronAI\RAG\PostProcessor\JinaRerankerPostProcessor;

protected function vectorStore(): VectorStoreInterface
{
    return new FileVectorStore(directory: storage_path('vectors'), topK: 50);
}

protected function postProcessors(): array
{
    return [
        new JinaRerankerPostProcessor(key: 'JINA_API_KEY', topN: 5),
    ];
}
```

Las alternativas son Cohere (`CohereRerankerPostProcessor`) y un reranker autoalojado de LocalAI (`LocalAIRerankerPostProcessor`). Dos procesadores posteriores más baratos no necesitan ningún modelo: `FixedThresholdPostProcessor` descarta los documentos por debajo de un umbral de puntuación, y `AdaptiveThresholdPostProcessor` fija el corte a partir de la distribución de puntuaciones de cada conjunto de resultados.

**Por qué funciona la reordenación, y por qué es la incorporación con mayor retorno a un sistema RAG que ya funciona:**

La búsqueda vectorial compara dos incrustaciones calculadas *de forma independiente*. La consulta se comprimió en un vector sin saber nada de los documentos; cada documento se comprimió sin saber nada de la consulta. Se pierde información en ambas compresiones.

Un reranker lee la consulta y un documento **juntos** y puntúa su relación directamente. Es muchísimo más lento por par, y por eso no puedes usarlo para buscar entre millones de documentos, pero sobre 50 candidatos es rápido y captura señales de relevancia que la comparación vectorial no podía representar.

La forma estándar del pipeline, y exactamente lo que configura el listado de arriba:

```
Búsqueda vectorial → 50 candidatos → reordenación → 5 mejores → enviar al modelo
```

Obtienes la cobertura de una búsqueda amplia y la precisión de una cuidadosa, y le envías al modelo menos fragmentos y mejores, lo que además reduce tokens.

### Estrategia de recuperación

`RetrievalNode` ejecuta la estrategia de recuperación, y NeuronAI permite personalizar esa estrategia, incluida la recuperación desde fuentes de datos externas y no solo desde el almacén vectorial. La predeterminada, `SimilarityRetrieval`, calcula la incrustación de la consulta y ejecuta un único `search()`; tu propia estrategia implementa `RetrievalInterface` y se la pasas a `setRetrieval()` o la devuelves desde una sobrescritura de `retrieval()`.

Ese es el punto de extensión para cualquier cosa inusual: una búsqueda híbrida que combine BM25 y vectores, recuperación multiconsulta para preguntas que abarcan varios fragmentos, o tirar de una API de búsqueda junto a tu propio índice.

Con ella viene una obligación. `retrieve(Message $query, ?FilterExpression $filters = null)` recibe los filtros vigentes en esta ejecución, incluido tu `retrievalScope()`. Una estrategia propia debe aplicarlos, combinados con los suyos mediante `FilterScope::merge()`, y no descartarlos nunca; de lo contrario, la estrategia es el agujero en tu aislamiento entre inquilinos.

Junto a la predeterminada se incluyen dos estrategias. `CompositeRetrieval` ejecuta varias estrategias en orden y junta sus resultados, que es como se busca en dos almacenes a la vez. `SemanticMemoryRetrieval` busca en conversaciones pasadas guardadas como documentos, restringida a los ID de hilo que le pases: combina ambas y el agente puede recordar «lo que hablamos la semana pasada» junto a la base de conocimiento. En los términos de la Sección 11.1 eso es memoria a largo plazo, no recuperación de conocimiento; merece la pena saber que las piezas existen, y la guía de memoria conversacional del framework explica cómo conectarlas.

### InstructionsNode: donde se combate la alucinación

Este nodo añade los documentos recuperados al prompt de sistema del agente, como un bloque aparte envuelto en etiquetas `<EXTRA-CONTEXT>`, con cada documento etiquetado con su tipo y su nombre de origen. Tus propias instrucciones quedan intactas, delante de él.

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

Las etiquetas de origen son lo que hace posible «nombra el documento de origen»: otra razón para que el `sourceName` que fijas en la ingesta signifique algo para un lector.

Esas instrucciones más un `FaithfulnessJudge` en tu suite de evaluación son las dos mitades de la historia antialucinación: una la reduce, la otra te dice si funcionó.

### Middleware en los nodos de RAG

Como estos son nodos de flujo de trabajo, el middleware los apunta por clase: `$rag->addMiddleware(RetrievalNode::class, new MyMiddleware())`, o una sobrescritura de `middleware()` en el agente, el mismo mecanismo que la Sección 2.3 presentó para `ToolNode`.

Aplicaciones útiles:

- Registrar cada recuperación: consulta, documentos devueltos, puntuaciones. Esta es tu herramienta de depuración de RAG.
- Inyectar un filtro por ejecución. El `before()` de un middleware sobre `RetrievalNode` recibe el `QueryPreProcessedEvent` y puede llamar a `addFilters()` sobre él; el filtro se combina con AND con el ámbito de recuperación y muere con la ejecución.
- Cachear resultados de recuperación para consultas repetidas.
- Censurar contenido sensible de los documentos antes de que entren en el prompt.

El Capítulo 15 cubre el middleware como es debido.

### Puntos clave

- Seis nodos: preprocesar, recuperar, posprocesar, enriquecer las instrucciones, chatear, herramientas.
- Los procesadores previos arreglan el desajuste consulta/respuesta a cambio de una llamada al modelo.
- **La reordenación es la mejora con mayor retorno para un sistema RAG que ya funciona**: recupera 50, reordena, envía 5.
- Una estrategia de recuperación propia debe respetar los filtros que recibe.
- `InstructionsNode` más instrucciones estrictas es el mecanismo antialucinación.
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
    ?->getContent() . PHP_EOL;
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

## Laboratorio 9 — Almacén de producción con búsqueda filtrada

**Cubre:** MariaDB, esquema de documentos, metadatos, filtros, evaluación.

### Objetivo

Mover el Laboratorio 8 a una base de datos de producción, añadir filtrado por metadatos y medir si realmente mejoró algo.

### Instalar

MariaDB 11.7 o posterior, con su tipo vectorial nativo. Si todavía no ejecutas ninguno, basta un contenedor:

```bash
docker run -d --name rag-mariadb -p 3306:3306 \
    -e MARIADB_ROOT_PASSWORD=secret -e MARIADB_DATABASE=rag \
    mariadb:11.8
```

### Cambiar el almacén

```php
use NeuronAI\RAG\Schema\DocumentField;
use NeuronAI\RAG\Schema\DocumentSchema;
use NeuronAI\RAG\VectorStore\MariaDBVectorStore;

protected function vectorStore(): VectorStoreInterface
{
    return new MariaDBVectorStore(
        pdo: new \PDO(
            env('RAG_DSN', 'mysql:host=127.0.0.1;port=3306;dbname=rag'),
            env('RAG_DB_USER', 'root'),
            env('RAG_DB_PASSWORD', 'secret'),
        ),
        topK: 5,
        schema: DocumentSchema::of(
            DocumentField::string('section')->filterable(),
            DocumentField::string('language')->filterable(),
        ),
    );
}
```

Crea la tabla una vez, dimensionada para las 768 dimensiones de `nomic-embed-text`, con los mismos datos de conexión:

```php
$pdo = new \PDO(
    env('RAG_DSN', 'mysql:host=127.0.0.1;port=3306;dbname=rag'),
    env('RAG_DB_USER', 'root'),
    env('RAG_DB_PASSWORD', 'secret'),
);

(new MariaDBVectorStore(pdo: $pdo))->setupTable(dimensions: 768);
```

Un método cambiado. Todo lo demás —el agente, el cargador, el divisor, los scripts— queda intacto. Esa es la arquitectura guiada por interfaces de la Sección 2.2 dando frutos en la capa de datos, y resulta más convincente verlo ocurrir que leerlo.

Los campos del esquema son opcionales (sin `required()`), así que los documentos del Laboratorio 8, que no llevan metadatos, se siguen indexando sin problemas; simplemente no casarán con un filtro sobre esos campos.

### Añadir metadatos durante la ingesta

```php
$documents = FileDataLoader::for($directory)
    ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
    ->getDocuments();

foreach ($documents as $document) {
    // The first line of each chunk is its heading
    $document->addMetadata('section',  \strtok($document->getContent(), "\n") ?: 'untitled');
    $document->addMetadata('language', 'en');
}

DocsAgent::make()->reindexBySource($documents);
```

`reindexBySource()` en lugar de `addDocuments()`, para que volver a ejecutar el script sustituya los fragmentos de cada archivo en vez de duplicarlos, lo cual solo funciona porque `MarkdownSectionSplitter` transmite el nombre de origen de cada archivo a sus fragmentos.

### Mídelo

Construye un evaluador (Capítulo 10) con quince preguntas reales sobre tu documentación:

```php
namespace App\Neuron\Evaluators;

use App\Rag\DocsAgent;
use NeuronAI\Agent\AgentInterface;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Evaluation\Assertions\Judges\FaithfulnessJudge;
use NeuronAI\Evaluation\Assertions\StringContainsAny;
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
            ?->getContent() ?? '';
    }

    public function evaluate(mixed $output, array $item): void
    {
        $this->assert(new StringContainsAny($item['expected_keywords']), $output);

        $this->assert(new FaithfulnessJudge(
            judge: $this->judge,
            context: $item['source_excerpt'],
            threshold: 0.7,
        ), $output, 'faithfulness');
    }
}
```

El tercer argumento de `assert()` etiqueta la puntuación, así que el informe muestra una métrica `faithfulness` en lugar del nombre de clase del juez: práctico cuando estás a punto de comparar cuatro ejecuciones.

Ejecútalo contra ambos almacenes y ambos divisores. Cuatro configuraciones, un número cada una.

**Esa tabla es el entregable de este laboratorio.** No el código: la medición. Es la diferencia entre «mejoramos el RAG» y «la fidelidad pasó de 0,62 a 0,81 al cambiar de divisor, y cambiar de almacén no cambió nada».

El segundo hallazgo es tan valioso como el primero, y es el tipo de resultado que nunca obtendrás suponiendo. Aquí es también el probable: el almacén de archivos y MariaDB clasifican con la misma similitud de coseno, así que pasar de uno a otro te da durabilidad, concurrencia y filtrado a escala, no mejores respuestas. Las mejores respuestas vienen del divisor, del reranker y de las instrucciones.

### Criterios de aceptación

- Solo `vectorStore()` difiere entre los agentes del Laboratorio 8 y del 9.
- Tienes una tabla de cuatro filas con puntuaciones de fidelidad.
- Una consulta filtrada por metadatos demostrablemente no puede devolver documentos fuera de ese filtro; pruébalo con documentos de dos inquilinos en un mismo índice. El `chapters/Ch12/run/isolation.php` del repositorio complementario es un punto de partida.
- Un filtro sobre un campo no declarado, como `Filter::eq('author', 'me')`, lanza una excepción en lugar de devolver un resultado vacío.

## Ejercicios del capítulo

1. **Compara divisores.** Indexa un corpus de documentación real con el divisor por defecto y con uno propio. Compara sobre quince preguntas, usando el evaluador en lugar de tu impresión.
2. **Demuestra el aislamiento.** Añade metadatos de inquilino y verifica que una consulta filtrada no puede devolver documentos de otro inquilino. Es una prueba de seguridad; escríbelo como tal.
3. **Reindexa.** Cambia un archivo fuente y reindexa con `reindexBySource()`. Confirma que los fragmentos viejos han desaparecido consultando una frase que borraste.
4. **Informa.** Registra la puntuación de fidelidad de cada configuración y escribe el resumen de un párrafo que le enviarías a un cliente. Si el resumen honesto es «el cambio caro no hizo nada», esa es la frase más valiosa del informe.
