# Capítulo 20 — RAG sobre los datos de la aplicación

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

Este capítulo es conceptual y no tiene código propio, pero el repositorio complementario [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene versiones ejecutables de todo lo que el libro construye.
:::

## 20.1 Un agente RAG en Laravel

### El almacén

Una base de conocimiento compartida por muchos inquilinos tiene que filtrar cada búsqueda por inquilino, y un almacén solo puede filtrar por los campos de los que se le ha informado. Así que el almacén va primero, con un `DocumentSchema` que declara los metadatos por los que la aplicación va a filtrar:

```php
namespace App\Neuron\Rag;

use NeuronAI\RAG\Schema\DocumentField;
use NeuronAI\RAG\Schema\DocumentSchema;

final class KnowledgeBase
{
    public static function schema(): DocumentSchema
    {
        return DocumentSchema::of(
            DocumentField::integer('tenant_id')->required()->filterable(),
            DocumentField::integer('article_id')->required()->filterable(),
            DocumentField::string('visibility')->required()->filterable(),
            DocumentField::integer('updated_at')->filterable(),
        );
    }
}
```

`required()` hace que el almacén rechace un documento que llegue sin el campo: el error de ingesta en el que alguien olvida marcar el inquilino falla ruidosamente en el momento de indexar, en lugar de producir un fragmento que no se puede filtrar.

La misma clase construye el almacén, de modo que el nombre de la tabla, el top-K y el esquema tienen una única definición:

```php
// In KnowledgeBase, which now also imports
// Illuminate\Support\Facades\DB and NeuronAI\RAG\VectorStore\MariaDBVectorStore
public static function store(): MariaDBVectorStore
{
    return new MariaDBVectorStore(
        pdo: DB::connection()->getPdo(),
        tableName: 'knowledge_base',
        topK: 5,
        schema: self::schema(),
    );
}
```

¿Por qué no añadir simplemente una clave `schema` a `config/neuron.php`? Porque `php artisan config:cache` serializa la configuración con `var_export()`, y un objeto `DocumentSchema` no sobrevive al viaje: el comando falla con «Your configuration files are not serializable». Los objetos van en el código.

¿Y por qué construir un almacén nuevo en cada llamada en lugar de registrar uno como driver con `VectorStore::extend()` y dejar que lo conserve el manager? Porque `MariaDBVectorStore` guarda el PDO que se le entrega, y un manager conserva lo que construyó durante toda la vida del proceso. Un worker de cola vive días; cuando Laravel se reconecta tras una conexión caída, el worker seguiría usando el PDO viejo, ya muerto. Un almacén es un objeto barato —una conexión, un nombre de tabla, un esquema—, así que el agente y cada trabajo llaman a `KnowledgeBase::store()` y cada uno recibe la conexión que Laravel tiene en ese momento.

::: {.callout .callout-warning}
[`VectorStore::extend()` solo funciona si registras el manager como singleton]{.callout-title}

Para un almacén que no guarda ninguna conexión —un `FileVectorStore`, o Qdrant y Pinecone, que son clientes HTTP—, `VectorStore::extend('name', fn () => ...)` en un proveedor de servicios es la manera Laravel de registrarlo. En neuron-laravel 2.0.0 no hace nada útil, y lo hace en silencio: el SDK registra `AIProviderManager` y `EmbeddingProviderManager` como singletons, pero no `VectorStoreManager`. La facade `VectorStore` resuelve el manager una vez y lo guarda en caché, así que `extend()` en `boot()` funciona hasta que algo vacía las instancias resueltas de las facades —una prueba, un servidor de larga vida entre peticiones—, y entonces la siguiente resolución construye un manager nuevo que nunca ha oído hablar de tu driver («Driver [name] not supported»). Registra el manager en tu propio proveedor, el del Capítulo 18, antes de que nada llame a `extend()`:

```php
// NeuronServiceProvider::register()
$this->app->singleton(VectorStoreManager::class);
```
:::

### La tabla

El almacén no crea su tabla. Lo hace `MariaDBVectorStore::setupTable()`, y su sitio es una migración:

```php
use App\Neuron\Rag\KnowledgeBase;
use Illuminate\Database\Migrations\Migration;

return new class extends Migration
{
    public function up(): void
    {
        KnowledgeBase::store()->setupTable((int) config('neuron.embedding.openai.dimensions'));
    }

    public function down(): void
    {
        KnowledgeBase::store()->dropTable();
    }
};
```

Necesita MariaDB 11.7 o posterior, y necesita que tú le des la dimensión de la incrustación. Los dos lados de ese número vienen con valores por defecto distintos: el `config/neuron.php` del SDK configura el embedder de OpenAI para 1024 dimensiones, mientras que `setupTable()` crea una columna `VECTOR(1536)`. Una columna y un modelo que no se ponen de acuerdo sobre la longitud de un vector no pueden trabajar juntos, así que fija el número una sola vez, en `config/neuron.php`, bajo `embedding.openai` —`'dimensions' => 1536`— y deja que la migración lo lea de ahí. Elige un valor que tu modelo de incrustaciones sepa producir y trátalo como parte del esquema: cambiarlo más tarde significa eliminar la tabla y volver a calcular las incrustaciones de cada artículo.

El embedder necesita una línea más en `.env`. `NEURON_EMBEDDING_PROVIDER` no tiene valor por defecto (el SDK lo lee sin alternativa), y `EmbeddingProvider::driver()` lanza un `TypeError` cuando no está definido: ponlo en `openai` (o `gemini`, `ollama`, `voyage`, `mistral`) junto con la clave de ese proveedor.

Un almacén no guarda estado por búsqueda, y cada búsqueda lleva sus propios filtros en una petición inmutable, así que incluso un almacén compartido entre peticiones no puede filtrar el filtro de un inquilino hacia otro. (Los tutoriales antiguos configuran los filtros en el propio almacén con `withFilters()`, lo que convertía una instancia compartida en una fuga entre inquilinos; el método ya no existe.)

### La clase

```php
namespace App\Neuron\Rag;

use App\Neuron\ThreadScope;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\Filter\Filter;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class KnowledgeBaseAgent extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return EmbeddingProvider::driver();
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return KnowledgeBase::store();
    }

    protected function retrievalScope(): ?FilterExpression
    {
        return Filter::eq('tenant_id', ThreadScope::of($this->getThreadId())->tenantId);
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You answer questions using only the knowledge base articles in your context.',
                'You do not have general knowledge about this company beyond those articles.',
            ],
            steps: [
                'Read the provided articles.',
                'If they answer the question, answer and cite the article title.',
                'If they do not, say the knowledge base does not cover it and offer to '
                . 'escalate to a human.',
            ],
            output: [
                'Cite the source article for every factual claim.',
                'Keep answers under 150 words unless the user asks for detail.',
            ],
        );
    }
}
```

El agente se construye como el Capítulo 18 construye un agente: no sabe nada de quien lo llama. No hay ningún `Tenant` en el constructor; el inquilino es el que nombra el hilo al que el agente está vinculado —`$agent->for($conversation->threadId())`—, y `ThreadScope` (Sección 18.3) lo vuelve a leer. Un agente que nunca se vincula no se ejecuta en absoluto, porque el framework no genera ningún ID de hilo, así que no hay manera de buscar en este almacén sin un inquilino. La clase no declara `messageStore()`: una pregunta a la base de conocimiento se responde con los artículos, y la conversación queda en memoria durante la ejecución. La Sección 20.4 le da al agente un historial persistente.

### El filtro de inquilino no es opcional

`retrievalScope()` devuelve el filtro de inquilino incondicionalmente, calculado a partir del hilo, y el nodo de recuperación lo aplica a cada búsqueda que hace este agente. No hay camino de código que consulte el almacén sin él. Cualquier otra cosa que añada un filtro durante una ejecución —un middleware en el nodo de recuperación, una estrategia de recuperación a medida— se combina con el ámbito mediante AND, así que puede estrechar la búsqueda pero nunca ampliarla.

La regla de la Sección 12.6: **filtra en la recuperación, nunca después.** Un documento recuperado y luego excluido de la respuesta estuvo igualmente en el contexto del modelo, y los modelos parafrasean. El filtro de inquilino es el equivalente RAG de un `where tenant_id = ?` en cada consulta, y pertenece al mismo sitio: al componente que construye la consulta.

::: {.callout .callout-warning}
[`setRetrievalScope()` reemplaza el ámbito; no se suma a él]{.callout-title}

`RAG` también tiene un setter `setRetrievalScope()`, y es tentador usarlo desde un controlador para un filtro extra puntual. No lo hagas, en este agente. El setter *reemplaza* lo que devuelve `retrievalScope()`: pásale `Filter::eq('visibility', 'public')` y el filtro de inquilino desaparece, y la búsqueda recorre los artículos públicos de todos los inquilinos. Mantén cada restricción obligatoria dentro del hook, calculada a partir del hilo al que está vinculado el agente.
:::

### Elegir un almacén en Laravel

De la Sección 12.5, con la lente de Laravel:

**MariaDB 11.7+** — una tabla en la base de datos que ya ejecutas. Copias de seguridad, monitorización, transacciones y conmutación por error ya resueltas. Para la mayoría de las aplicaciones Laravel es la respuesta correcta, y es el almacén construido arriba.

**Elasticsearch o Meilisearch** — si ya ejecutas uno para la búsqueda del sitio, úsalo y evita un segundo sistema.

**Pinecone o Qdrant** — cuando la escala exija de verdad una base de datos dedicada.

**PHPVector** — `neuron-core/php-vector`, PHP puro, HNSW más búsqueda híbrida BM25, ningún servicio. Atractivo para despliegues autoalojados y clientes que no pueden añadir infraestructura, pero en el momento de escribir esto no tiene ninguna versión para NeuronAI v4 (Sección 12.5). Compruébalo antes de contar con él.

La regla general se sostiene: **usa lo que ya ejecutas.** Elijas el que elijas, acepta el mismo argumento `schema:`, y los mismos filtros portables funcionan en todos.

### Puntos clave

- Declara los metadatos filtrables en un `DocumentSchema`; construye el almacén en el código (`KnowledgeBase::store()`), no en la configuración en caché, y una vez por resolución cuando guarda un PDO.
- Crea la tabla en una migración con la dimensión de la incrustación fijada en ambos lados; define `NEURON_EMBEDDING_PROVIDER`.
- Pon el filtro de inquilino en `retrievalScope()`, leído del hilo, para que ningún camino lo sortee, y nunca lo reemplaces con `setRetrievalScope()`.
- Un almacén no guarda estado por búsqueda: los filtros viajan con cada búsqueda. Si usas `VectorStore::extend()`, registra antes `VectorStoreManager` como singleton.
- MariaDB para la mayoría de las aplicaciones Laravel.

## 20.2 Ingesta en cola

### El trabajo

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\Article;
use App\Neuron\Rag\KnowledgeBase;
use App\Neuron\Rag\MarkdownSectionSplitter;
use DateTimeInterface;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Contracts\Queue\ShouldQueueAfterCommit;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\RAG\DataLoader\StringDataLoader;

class IndexArticle implements ShouldQueue, ShouldQueueAfterCommit
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $maxExceptions = 3;
    public int $backoff = 30;

    public function retryUntil(): DateTimeInterface
    {
        return now()->addHours(6);
    }

    public function __construct(
        public readonly Article $article,
    ) {}

    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)
            ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
            ->getDocuments();

        foreach ($documents as $document) {
            $document->setSourceType('article');
            $document->setSourceName("article-{$this->article->id}");
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->getTimestamp());
        }

        $store    = KnowledgeBase::store();
        $embedder = EmbeddingProvider::driver();

        // Fail on a bad document before paying for its embedding
        foreach ($documents as $document) {
            $store->getSchema()->validate($document);
        }

        $store->addDocuments($embedder->embedDocuments($documents));
    }
}
```

Componentes autónomos (Sección 12.2) en lugar de un agente RAG: la ingesta no necesita proveedor de chat, ni instrucciones, ni herramientas. Mantener el trabajo ligero significa que arranca más rápido y tiene menos razones para fallar. `MarkdownSectionSplitter` es el divisor de la Sección 12.3, trasladado de `App\Rag` a `App\Neuron\Rag`, junto a `KnowledgeBase`.

`ShouldQueueAfterCommit` retiene el envío hasta que la transacción de base de datos que lo rodea se confirma, y lo descarta si la transacción se revierte. Sin él, un trabajo en una cola rápida puede arrancar antes del commit, leer el cuerpo antiguo del artículo e indexarlo, y nada dispara una segunda ejecución. Los ajustes de reintento se explican abajo, en «Configuración de la cola».

Los metadatos tienen que coincidir con el esquema de la Sección 20.1, y el esquema es estricto con los tipos: `integer` significa un `int` de PHP, así que dale a `Article` casts enteros para sus columnas de ID en lugar de fiarte del driver. `updated_at` se guarda como marca de tiempo Unix porque los filtros de rango son numéricos; la Sección 20.3 filtra por él. El almacén vuelve a validar cada documento en `addDocuments()`, pero para entonces las incrustaciones ya están pagadas; el bucle de arriba falla antes y gratis. (`RAG::addDocuments()` hace la misma comprobación en el mismo orden, que es una de las razones por las que el siguiente trabajo usa el agente.)

### Dispararlo

```php
class Article extends Model
{
    protected static function booted(): void
    {
        static::saved(function (Article $article) {
            if ($article->wasChanged('body') || $article->wasRecentlyCreated) {
                ReindexArticle::dispatch($article);
            }
        });

        static::deleted(function (Article $article) {
            RemoveArticleFromIndex::dispatch($article->id, $article->tenant_id);
        });
    }
}
```

La guarda `wasChanged('body')` importa. Sin ella, cada guardado —un incremento del contador de visitas, un toque a una marca de tiempo— vuelve a embeber el artículo entero. Eso es dinero real gastado en nada, repetidamente.

Eliminar es una sola llamada, porque un almacén borra por cualquier filtro que el esquema permita:

```php
public function handle(): void
{
    KnowledgeBase::store()->delete(
        Filter::where('tenant_id', $this->tenantId)->where('article_id', $this->articleId),
    );
}
```

Delimitar el borrado por inquilino además de por artículo no cuesta nada y significa que un error en el llamante no puede eliminar los fragmentos de otro inquilino.

### Reindexar en lugar de añadir

```php
class ReindexArticle implements ShouldQueue, ShouldQueueAfterCommit
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    // $maxExceptions, $backoff, retryUntil() and the constructor, as in IndexArticle

    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)
            ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
            ->getDocuments();

        foreach ($documents as $document) {
            $document->setSourceType('article');
            $document->setSourceName("article-{$this->article->id}");   // stable — the ID, never the title
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->getTimestamp());
        }

        KnowledgeBaseAgent::make()->reindexBySource($documents);
    }
}
```

`reindexBySource()` valida el lote entero, calcula las incrustaciones de los fragmentos de cada fuente y solo después borra todo lo guardado bajo el `sourceType` y el `sourceName` de esa fuente y añade los fragmentos nuevos. Una validación fallida o una llamada de incrustación fallida dejan la versión antigua del índice intacta. El esquema es la razón de que aquí se repita cada línea de metadatos: quita la línea de `tenant_id` y el trabajo falla antes de calcular ninguna incrustación, en lugar de escribir fragmentos que ningún inquilino puede recuperar.

La restricción de la Sección 12.6, repetida porque es fácil equivocarse: **`sourceName` debe ser estable.** Usa el ID del artículo. Derívalo del título y un cambio de nombre editorial dejará huérfanos los fragmentos viejos: se quedan en el índice, no se pueden borrar por fuente, y el agente responde a partir de ambas versiones.

Dale un prefijo: `article-42` en lugar de `42`. Un número a secas funciona, pero el prefijo dice qué clase de cosa es la fuente cuando lees el índice.

### Configuración de la cola

**Una cola dedicada.** La incrustación es lento; no dejes que retrase los correos de restablecimiento de contraseña.

```php
ReindexArticle::dispatch($article)->onQueue('indexing');
```

**Límites de tasa.** Los proveedores de incrustaciones los tienen. Una reindexación masiva de 10.000 artículos chocará con uno.

```php
public function middleware(): array
{
    return [new RateLimited('embeddings')];
}
```

(`RateLimited` es `Illuminate\Queue\Middleware\RateLimited`, y el limitador `embeddings` se define con `RateLimiter::for()` en un proveedor de servicios.)

**Rellenos por bloques.** Para el índice inicial, usa `chunkById()` y envía por lotes en lugar de cargarlo todo en memoria.

**Reintentos.** Los fallos transitorios de los proveedores son normales, así que los trabajos fijan `$backoff = 30` y `$maxExceptions = 3`: tres fallos reales terminan el trabajo. No cuentes los intentos con `$tries = 3` en un trabajo que usa `RateLimited`: cada vez que el limitador libera el trabajo consume un intento, así que un relleno de 10.000 artículos vería fallar sus trabajos tras tres liberaciones sin un solo error. `retryUntil()` acota el trabajo por tiempo, y `$maxExceptions` cuenta solo excepciones.

### El modo de fallo para el que planificar

Un trabajo de indexación falla en silencio y el artículo nunca entra en el índice. El agente responde entonces «la base de conocimiento no lo cubre» para contenido que existe, lo que parece un problema de calidad del RAG y en realidad es un problema operativo.

Sigue la pista:

```php
// last lines of handle(), in both jobs
$this->article->timestamps = false;
$this->article->forceFill(['indexed_at' => $this->article->updated_at])->saveQuietly();
```

```php
Article::whereNull('indexed_at')
       ->orWhereColumn('indexed_at', '<', 'updated_at')
       ->count();
```

`indexed_at` registra qué versión del artículo llegó al índice: copia el `updated_at` que el trabajo leyó al empezar. Un simple `update(['indexed_at' => now()])` movería también `updated_at`, y la consulta de la alerta podría señalar un artículo sano —o esconder una edición hecha mientras el trabajo corría—; además, `saveQuietly()` evita que el guardado vuelva a disparar los eventos del modelo. Un número, con alerta posible. Constrúyelo ya: es la diferencia entre una demo y un sistema, y nadie piensa en ello hasta el primer ticket de soporte.

### Puntos clave

- Haz la ingesta con componentes autónomos dentro de un trabajo en cola, enviado tras el commit.
- Pon una guarda con `wasChanged()`: no vuelvas a embeber en cada guardado.
- Respeta el esquema: campos obligatorios presentes, enteros como `int`, fechas como marcas de tiempo.
- `reindexBySource()` con un ID estable y con prefijo como `sourceName`; borra por filtro.
- Cola dedicada, límite de tasa, rellenos por bloques, reintentos acotados por `retryUntil()` y `$maxExceptions`, no por `$tries`.
- Sigue `indexed_at` y pon una alerta sobre la diferencia.

## 20.3 Recuperación consciente de los permisos

### El problema

Tu base de conocimiento tiene artículos públicos, artículos solo para clientes y runbooks internos. Todos en un mismo índice.

Un cliente hace una pregunta. Si la recuperación casa con un runbook interno y este entra en el contexto, el modelo puede parafrasearlo dentro de la respuesta. El usuario nunca vio el documento, pero obtuvo su contenido.

**Eso es una violación de datos, y en tus registros no lo parece.** No se renderizó ningún documento, no se llamó a ningún punto de conexión: la fuga ocurrió dentro de una paráfrasis.

### La solución

El hilo ya nombra al usuario que hace la petición junto al inquilino, así que el ámbito crece en una condición y el agente sigue sin recibir nada en su constructor:

```php
protected function retrievalScope(): ?FilterExpression
{
    $scope = ThreadScope::of($this->getThreadId());

    return Filter::where('tenant_id', $scope->tenantId)
        ->whereIn('visibility', $this->allowedVisibilities($scope));
}

private function allowedVisibilities(ThreadScope $scope): array
{
    $user = User::where('tenant_id', $scope->tenantId)->findOrFail($scope->userId);

    return match (true) {
        $user->hasRole('staff')    => ['public', 'customer', 'internal'],
        $user->hasRole('customer') => ['public', 'customer'],
        default                    => ['public'],
    };
}
```

El rol se lee de la base de datos, por ID, para el usuario que nombra el hilo, y el usuario debe pertenecer al inquilino que nombra el hilo. De lo que se fía la petición es del propio hilo: el controlador autorizó la conversación (Sección 18.2) antes de vincularle el agente.

La recuperación nunca devuelve lo que el usuario no puede ver. El filtro se calcula a partir del actor y se aplica en el almacén. `Filter::where()` inicia una cadena AND; `whereIn()` coincide con cualquiera de los valores listados. Ambos campos están declarados como filtrables en el esquema de la Sección 20.1: filtra por un campo que no declara y el almacén lanza una `DocumentSchemaException` antes de tocar la base de datos, que es justo el fallo que quieres.

### La regla, una vez más

**Filtra en la recuperación, nunca después.**

El postfiltrado —recuperarlo todo y luego descartar lo que el usuario no puede ver antes de mostrarlo— falla porque el modelo ya lo leyó. El único punto seguro es antes de que la búsqueda vectorial devuelva.

Es la regla de seguridad de RAG con más consecuencias, y no es obvia.

### Testearla

```php
public function test_customer_cannot_retrieve_internal_articles(): void
{
    $this->indexArticle('Internal escalation runbook', visibility: 'internal',
        body: 'The emergency override code is OMEGA-7.');

    $answer = app(KnowledgeBaseAgent::class)
        ->for($customerConversation->threadId())
        ->chat(new UserMessage('What is the emergency override code?'))
        ->getMessage()
        ?->getContent();

    $this->assertStringNotContainsString('OMEGA-7', (string) $answer);
}
```

(`$customerConversation` es una conversación de un cliente del inquilino, `$staffConversation` una de un miembro del personal.) Un token distintivo en un documento restringido, y un aserto de que nunca aflora. Este es las pruebas por contrato de la Sección 1.5 aplicado a la seguridad: no puedes hacer asertos sobre la redacción de la respuesta, pero sí sobre lo que nunca debe aparecer en ella.

Ejecútalo en CI. Es una de las pocas pruebas de IA a la vez lo bastante determinista como para fiarse y lo bastante importante como para condicionar un despliegue.

Puedes hacerlo totalmente determinista afirmando un paso antes: sobre lo que llegó al modelo, no sobre lo que dijo el modelo. Los documentos recuperados se inyectan en las instrucciones, así que dale al agente dobles de prueba para todo lo que saldría del proceso —el `FakeAIProvider` del framework para el modelo, `FakeEmbeddingsProvider` para el embedder y un almacén en memoria— y comprueba el prompt de sistema que registró el proveedor:

```php
$embeddings = new FakeEmbeddingsProvider();
$store      = new MemoryVectorStore(schema: KnowledgeBase::schema());

$runbook = new Document('The emergency override code is OMEGA-7.');
$runbook->addMetadata('tenant_id',  $tenant->id);
$runbook->addMetadata('article_id', 1);
$runbook->addMetadata('visibility', 'internal');
$store->addDocuments($embeddings->embedDocuments([$runbook]));

$ask = function (Conversation $conversation) use ($embeddings, $store): FakeAIProvider {
    $provider = new FakeAIProvider(new AssistantMessage('I cannot help with that.'));

    app(KnowledgeBaseAgent::class)
        ->setAiProvider($provider)
        ->setEmbeddingsProvider($embeddings)
        ->setVectorStore($store)
        ->for($conversation->threadId())
        ->chat(new UserMessage('What is the emergency override code?'));

    return $provider;
};

$ask($customerConversation)->assertSent(
    fn (RequestRecord $request): bool => !$request->systemPrompt?->contains('OMEGA-7')
);

// The control: the same store and question for staff does retrieve it
$ask($staffConversation)->assertSent(
    fn (RequestRecord $request): bool => $request->systemPrompt?->contains('OMEGA-7') === true
);
```

Sin modelo, sin red, sin base de datos para la búsqueda, sin inestabilidad: si se recuperó el fragmento restringido para el cliente, la prueba falla siempre. El control con el personal importa tanto como el aserto que protege. Una prueba que simula solo el proveedor de chat seguiría llamando al embedder real y al almacén real; y una prueba que nunca demuestra que el documento *se puede* recuperar pasa con la misma tranquilidad cuando el almacén está vacío.

### Filtros de frescura

El mismo mecanismo gestiona el contenido superado:

```php
return Filter::where('tenant_id', ThreadScope::of($this->getThreadId())->tenantId)
    ->whereGreaterThanOrEqual('updated_at', now()->subYear());
```

La sintaxis es portable: la misma expresión se compila para MariaDB, Meilisearch, Pinecone o cualquier otro almacén incluido. Los filtros de rango son numéricos, y una fecha que se les pase se normaliza a una marca de tiempo Unix, que es por lo que la Sección 20.2 guardó `updated_at` con `getTimestamp()`. Una fecha guardada como `'2026-01-31'` no podría filtrarse por rango en absoluto.

Útil cuando las versiones vieja y nueva de una política viven ambas en el índice y quieres que el modelo prefiera la actual.

### Puntos clave

- Un índice, varios niveles de visibilidad: o filtras o hay fuga.
- Una fuga por paráfrasis es invisible en tus registros.
- Calcula las visibilidades permitidas a partir del actor; aplícalas en `retrievalScope()`.
- Testea con un token distintivo en un documento restringido; ejecútalo en CI: con el proveedor falso es totalmente determinista.
- Filtros portables: rangos numéricos, fechas como marcas de tiempo, cada campo declarado en el esquema.

## 20.4 Combinar RAG y herramientas

### Las dos preguntas

- *«¿Cuál es vuestra política de reembolsos?»* → prosa en un documento → **RAG**
- *«¿Se ha reembolsado mi pedido n.º 4471?»* → una fila de una tabla → **herramienta**

La Sección 11.4 hizo la distinción. Aquí se convierte en una sola clase, porque `RAG` extiende `Agent` (Sección 12.1).

### El agente

```php
class SupportAgent extends RAG
{
    public function __construct(
        protected MessageStoreInterface $conversations,
        protected PersistenceInterface $runs,
    ) {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return EmbeddingProvider::driver();
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return KnowledgeBase::store();
    }

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;
    }

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;
    }

    protected function contextWindow(): int
    {
        return config('neuron.context_windows.' . config('neuron.provider.default'), 29_000);
    }

    protected function retrievalScope(): ?FilterExpression
    {
        $scope = ThreadScope::of($this->getThreadId());

        return Filter::where('tenant_id', $scope->tenantId)
            ->whereIn('visibility', $this->allowedVisibilities($scope));
    }

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());
        $user  = User::where('tenant_id', $scope->tenantId)->findOrFail($scope->userId);

        return [
            new SearchOrdersTool($scope->tenantId),
            new GetOrderStatusTool($scope->tenantId),

            (new RequestRefundTool($scope->tenantId, $scope->userId))
                ->visible(Gate::forUser($user)->allows('create', Refund::class))
                ->setMaxRuns(1),
        ];
    }

    // allowedVisibilities() as in Section 20.3

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a customer support assistant.',
                'Policy questions are answered from the knowledge base articles in your context.',
                'Questions about specific orders are answered by calling your tools.',
            ],
            steps: [
                'Decide whether the question is about policy or about specific order data.',
                'For policy: answer from the provided articles and cite the article title.',
                'For order data: call the appropriate tool. Never state order details you '
                . 'have not retrieved with a tool.',
                'If neither source answers the question, offer to escalate to a human.',
            ],
            output: [
                'Answer in the user\'s language.',
                'Under 150 words unless detail is requested.',
                'Never state a monetary amount you did not retrieve from a tool.',
            ],
        );
    }
}
```

Este es el `SupportAgent` del Capítulo 18 con su clase base cambiada de `Agent` a `RAG` y los tres hooks de RAG añadidos: los mismos dos almacenes inyectados, el mismo `ThreadScope`, el mismo `for($conversation->threadId())` en el controlador. El agente no conoce su contexto; el inquilino y el usuario salen del hilo, y las herramientas reciben IDs escalares.

### La instrucción que más trabaja

> *"Never state order details you have not retrieved with a herramienta."*

Y su hermana más fuerte:

> *"Never state a monetary amount you did not retrieve from a herramienta."*

Sin estas, el modelo producirá con seguridad el estado de un pedido o el importe de un reembolso de la nada, porque ha visto miles de conversaciones de soporte durante el entrenamiento y sabe qué aspecto tienen.

**Las instrucciones antialucinación deben ser específicas sobre la clase de hecho.** «Sé preciso» no hace nada. «Nunca declares un importe monetario que no hayas recuperado» es accionable, comprobable y —con el `FaithfulnessJudge` de la Sección 10.5— medible.

### Una clase, casi todo el libro

Cuenta lo que hay dentro: abstracción de proveedor (3.6), estructura del prompt de sistema (3.5), un hilo que sirve de clave tanto al historial de conversación como a cualquier aprobación de reembolso en pausa y lleva el inquilino y el usuario (4.3, 18.2, 18.3), herramientas con dependencias (5.3), visibilidad de herramientas (5.10), límites de ejecución (5.9), recuperación RAG (12.1), filtros de permisos (20.3) y un contrato antialucinación (11.5).

Siete capítulos en una sola clase. Merece detenerse: el libro compone en lugar de acumular, y esta clase es la prueba.

### Puntos clave

- RAG extiende Agent, así que la recuperación y las herramientas viven en una sola clase.
- Dile al modelo qué fuente responde a qué tipo de pregunta.
- Las instrucciones antialucinación deben nombrar la clase de hecho.
- Todo lo de las Partes II a IV se compone en un único agente.

## Laboratorio 14 — La base de conocimiento corporativa

**Cubre:** RAG sobre datos de la aplicación, ingesta en cola, filtros de permisos, citas.

### Objetivo

Los artículos de la base de conocimiento viven en Eloquent. Se indexan automáticamente cuando cambian, se responden con citas y nunca son recuperables por quien no debería verlos.

### Requisitos

1. **Una tabla `articles`** con `body`, `title`, `tenant_id`, `visibility` (`public` / `customer` / `internal`) e `indexed_at`.
2. **Indexación automática** al guardar, protegida por `wasChanged('body')`, enviada a una cola `indexing` dedicada con reintentos y límite de tasa.
3. **`reindexBySource()`** usando el ID del artículo con prefijo (`article-42`) como nombre estable de fuente, sobre un almacén cuyo `DocumentSchema` declara cada campo por el que filtras y cuya tabla crea una migración con la dimensión de la incrustación fijada. Editar un artículo debe reemplazar sus fragmentos, no añadirse a ellos.
4. **El borrado** elimina los fragmentos del artículo del índice.
5. **Recuperación consciente de los permisos** como en la Sección 20.3, calculada a partir del rol del usuario que pregunta.
6. **Citas.** Cada afirmación factual de una respuesta nombra su artículo de origen. Si la base de conocimiento no cubre la pregunta, el agente lo dice y ofrece escalar.

### Criterios de aceptación

- Editar un artículo y preguntar por el pasaje cambiado devuelve el contenido nuevo, y una frase que borraste ya no es recuperable.
- Un cliente no puede obtener el contenido de un artículo `internal`, probado con un token distintivo como en la Sección 20.3.
- `Article::whereNull('indexed_at')->orWhereColumn('indexed_at', '<', 'updated_at')->count()` devuelve cero después de que la cola se vacíe, y tienes una alerta para cuando no lo haga.
- Tocar un artículo sin cambiar su cuerpo no envía ningún trabajo de indexación. Haz el aserto sobre la cola, no sobre los registros.
- Una pregunta fuera de ámbito produce la oferta de escalado, no una respuesta inventada.

### La medición

Construye un conjunto de evaluación de quince preguntas sobre tus artículos reales, con un aserto `FaithfulnessJudge` (Sección 10.5). Registra la puntuación antes y después de cambiar a un divisor consciente de los encabezados.

Ese número es lo que le enseñas a un responsable. «El agente de la base de conocimiento responde con fidelidad el 0,87 de las veces, medido sobre quince preguntas representativas, y aquí está la tendencia desde que cambiamos el chunking» es una conversación fundamentalmente distinta de «parece que va bastante bien».

### Ir más allá

Añade el camino de escalado de verdad: cuando el agente ofrezca escalar y el usuario acepte, crea un ticket de soporte que contenga la pregunta, los artículos recuperados y la respuesta del agente. Acabas de construir la primera mitad del Proyecto final B.
