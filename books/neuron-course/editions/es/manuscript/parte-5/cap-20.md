# Capítulo 20 — RAG sobre los datos de la aplicación

## 20.1 Un agente RAG en Laravel

### La clase

```php
namespace App\Neuron\Rag;

use App\Models\Tenant;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class KnowledgeBaseAgent extends RAG
{
    protected array $vectorStoreFilters = [];

    public function __construct(
        private readonly Tenant $tenant,
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
        $store = VectorStore::driver();

        return $store->withFilters(\array_merge(
            ['tenant_id' => $this->tenant->id],
            $this->vectorStoreFilters,
        ));
    }

    public function addVectorStoreFilters(array $filters): self
    {
        $this->vectorStoreFilters = $filters;

        return $this;
    }

    public function instructions(): string
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

### El filtro de inquilino no es opcional

`withFilters(['tenant_id' => $this->tenant->id])` se aplica incondicionalmente en `vectorStore()`, fundido con cualquier filtro de tiempo de ejecución. No hay camino de código que consulte el almacén sin él.

La regla de la Sección 12.6: **filtra en la recuperación, nunca después.** Un documento recuperado y luego excluido de la respuesta estuvo igualmente en el contexto del modelo, y los modelos parafrasean. El filtro de inquilino es el equivalente RAG de un `where tenant_id = ?` en cada consulta, y pertenece al mismo sitio: al componente que construye la consulta.

::: {.callout .callout-warning}
[Comprueba el nombre del método y la lista de drivers]{.callout-title}

`withFilters()` frente a `withFilter()` sigue sin resolverse en la documentación (Apéndice A, puntos 26 y 43), y el conjunto de drivers de almacén vectorial que `VectorStore::driver()` expone realmente depende de tu `config/neuron.php` publicado (punto 44). Confirma ambas cosas antes de construir la ingesta encima.
:::

### Elegir un almacén en Laravel

De la Sección 12.5, con la lente de Laravel:

**MariaDB 11.7+** — una tabla en la base de datos que ya ejecutas. Copias de seguridad, monitorización, transacciones y conmutación por error ya resueltas. Para la mayoría de las aplicaciones Laravel es la respuesta correcta.

**PHPVector** — `neuron-core/php-vector`, PHP puro, HNSW más búsqueda híbrida BM25, ningún servicio. Bueno para despliegues autoalojados y clientes que no pueden añadir infraestructura.

**Elasticsearch o Meilisearch** — si ya ejecutas uno para la búsqueda del sitio, úsalo y evita un segundo sistema.

**Pinecone o Qdrant** — cuando la escala exija de verdad una base de datos dedicada.

La regla general se sostiene: **usa lo que ya ejecutas.**

### Puntos clave

- Tres facades, tres llamadas a `driver()`, todo lo demás en la configuración.
- Aplica el filtro de inquilino dentro de `vectorStore()` para que ningún camino lo sortee.
- MariaDB o PHPVector para la mayoría de las aplicaciones Laravel.

## 20.2 Ingesta en cola

### El trabajo

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\Article;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
use NeuronAI\RAG\DataLoader\StringDataLoader;

class IndexArticle implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;
    public int $backoff = 30;

    public function __construct(
        public readonly Article $article,
    ) {}

    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)
            ->withSplitter(new MarkdownSectionSplitter(maxChars: 2000))
            ->getDocuments();

        foreach ($documents as $document) {
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->toDateString());
        }

        $store    = VectorStore::driver();
        $embedder = EmbeddingProvider::driver();

        $store->addDocuments($embedder->embedDocuments($documents));
    }
}
```

Componentes autónomos (Sección 12.2) en lugar de un agente RAG: la ingesta no necesita proveedor de chat, ni instrucciones, ni herramientas. Mantener el trabajo ligero significa que arranca más rápido y tiene menos razones para fallar.

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

### Reindexar en lugar de añadir

```php
class ReindexArticle implements ShouldQueue
{
    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)->getDocuments();

        foreach ($documents as $document) {
            $document->addMetadata('tenant_id', $this->article->tenant_id);
            // sourceName must be stable — the ID, never the title
        }

        (new KnowledgeBaseAgent($this->article->tenant))
            ->reindexBySource($documents);
    }
}
```

La restricción de la Sección 12.6, repetida porque es fácil equivocarse: **`sourceName` debe ser estable.** Usa el ID del artículo. Derívalo del título y un cambio de nombre editorial dejará huérfanos los fragmentos viejos: se quedan en el índice, no se pueden borrar por fuente, y el agente responde a partir de ambas versiones.

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

**Rellenos por bloques.** Para el índice inicial, usa `chunkById()` y envía por lotes en lugar de cargarlo todo en memoria.

**Reintentos con backoff.** `$tries = 3`, `$backoff = 30`. Los fallos transitorios de los proveedores son normales.

### El modo de fallo para el que planificar

Un trabajo de indexación falla en silencio y el artículo nunca entra en el índice. El agente responde entonces «la base de conocimiento no lo cubre» para contenido que existe, lo que parece un problema de calidad del RAG y en realidad es un problema operativo.

Sigue la pista:

```php
$article->update(['indexed_at' => now()]);
```

```php
Article::whereNull('indexed_at')
       ->orWhereColumn('indexed_at', '<', 'updated_at')
       ->count();
```

Un número, con alerta posible. Constrúyelo ya: es la diferencia entre una demo y un sistema, y nadie piensa en ello hasta el primer ticket de soporte.

### Puntos clave

- Haz la ingesta con componentes autónomos dentro de un trabajo en cola.
- Pon una guarda con `wasChanged()`: no vuelvas a embeber en cada guardado.
- `reindexBySource()` con un ID estable como `sourceName`.
- Cola dedicada, límite de tasa, rellenos por bloques, reintentos.
- Sigue `indexed_at` y pon una alerta sobre la diferencia.

## 20.3 Recuperación consciente de los permisos

### El problema

Tu base de conocimiento tiene artículos públicos, artículos solo para clientes y runbooks internos. Todos en un mismo índice.

Un cliente hace una pregunta. Si la recuperación casa con un runbook interno y este entra en el contexto, el modelo puede parafrasearlo dentro de la respuesta. El usuario nunca vio el documento, pero obtuvo su contenido.

**Eso es una violación de datos, y en tus registros no lo parece.** No se renderizó ningún documento, no se llamó a ningún punto de conexión: la fuga ocurrió dentro de una paráfrasis.

### La solución

```php
protected function vectorStore(): VectorStoreInterface
{
    return VectorStore::driver()->withFilters([
        'tenant_id'  => $this->tenant->id,
        'visibility' => $this->allowedVisibilities(),
    ]);
}

private function allowedVisibilities(): array
{
    return match (true) {
        $this->user->hasRole('staff')    => ['public', 'customer', 'internal'],
        $this->user->hasRole('customer') => ['public', 'customer'],
        default                          => ['public'],
    };
}
```

La recuperación nunca devuelve lo que el usuario no puede ver. El filtro se calcula a partir del actor y se aplica en el almacén.

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

    $answer = (new KnowledgeBaseAgent($tenant, $customerUser))
        ->chat(new UserMessage('What is the emergency override code?'))
        ->getMessage()
        ->getContent();

    $this->assertStringNotContainsString('OMEGA-7', $answer);
}
```

Un token distintivo en un documento restringido, y un aserto de que nunca aflora. Este es las pruebas por contrato de la Sección 1.5 aplicado a la seguridad: no puedes hacer asertos sobre la redacción de la respuesta, pero sí sobre lo que nunca debe aparecer en ella.

Ejecútalo en CI. Es uno de los pocos pruebas de IA a la vez lo bastante determinista como para fiarse y lo bastante importante como para condicionar un despliegue.

### Filtros de frescura

El mismo mecanismo gestiona el contenido superado:

```php
->withFilters([
    'tenant_id'  => $this->tenant->id,
    'updated_at' => ['$gte' => now()->subYear()->toDateString()],
])
```

La sintaxis de filtros es específica de cada almacén: consulta la documentación del tuyo.

Útil cuando las versiones vieja y nueva de una política viven ambas en el índice y quieres que el modelo prefiera la actual.

### Puntos clave

- Un índice, varios niveles de visibilidad: o filtras o hay fuga.
- Una fuga por paráfrasis es invisible en tus registros.
- Calcula las visibilidades permitidas a partir del actor; aplícalas en el almacén.
- Testea con un token distintivo en un documento restringido; ejecútalo en CI.

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
        private readonly Tenant $tenant,
        private readonly User $user,
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
        return VectorStore::driver()->withFilters([
            'tenant_id'  => $this->tenant->id,
            'visibility' => $this->allowedVisibilities(),
        ]);
    }

    protected function tools(): array
    {
        return [
            new SearchOrdersTool($this->tenant),
            new GetOrderStatusTool($this->tenant),

            (new RequestRefundTool($this->refunds, $this->user))
                ->visible($this->user->can('create', Refund::class))
                ->setMaxRuns(1),
        ];
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            thread_id: "t{$this->tenant->id}:u{$this->user->id}",
            modelClass: ChatMessage::class,
            contextWindow: config('neuron.context_window'),
        );
    }

    public function instructions(): string
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

### La instrucción que más trabaja

> *"Never state order details you have not retrieved with a herramienta."*

Y su hermana más fuerte:

> *"Never state a monetary amount you did not retrieve from a herramienta."*

Sin estas, el modelo producirá con seguridad el estado de un pedido o el importe de un reembolso de la nada, porque ha visto miles de conversaciones de soporte durante el entrenamiento y sabe qué aspecto tienen.

**Las instrucciones antialucinación deben ser específicas sobre la clase de hecho.** «Sé preciso» no hace nada. «Nunca declares un importe monetario que no hayas recuperado» es accionable, comprobable y —con el `FaithfulnessJudge` de la Sección 10.5— medible.

### Una clase, casi todo el libro

Cuenta lo que hay dentro: abstracción de proveedor (3.6), estructura del prompt de sistema (3.5), historial de chat con aislamiento por inquilino (4.3, 18.3), herramientas con dependencias (5.3), visibilidad de herramientas (5.10), límites de ejecución (5.9), recuperación RAG (12.1), filtros de permisos (20.3) y un contrato antialucinación (11.5).

Nueve capítulos en cuarenta líneas. Merece detenerse: el libro compone en lugar de acumular, y esta clase es la prueba.

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
3. **`reindexBySource()`** usando el ID del artículo como nombre estable de fuente. Editar un artículo debe reemplazar sus fragmentos, no añadirse a ellos.
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
