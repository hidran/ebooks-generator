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

Luego regístralo como driver propio, junto a los que define `config/neuron.php`:

```php
// AppServiceProvider::boot()

VectorStore::extend('knowledge_base', fn () => new MariaDBVectorStore(
    pdo: DB::connection()->getPdo(),
    tableName: 'knowledge_base',
    topK: 5,
    schema: KnowledgeBase::schema(),
));
```

¿Por qué no añadir simplemente una clave `schema` a `config/neuron.php`? Porque `php artisan config:cache` serializa la configuración con `var_export()`, y un objeto `DocumentSchema` no sobrevive al viaje: el comando falla con «Your configuration files are not serializable». Los objetos van en el código; `extend()` es la manera Laravel de ponerlos ahí.

El manager construye el almacén una vez y entrega la misma instancia a cada llamante, durante toda la vida del proceso; bajo Octane, a cada petición. Eso es seguro por diseño: un almacén no guarda estado por búsqueda, y cada búsqueda lleva sus propios filtros en una petición inmutable. (Los tutoriales antiguos configuran los filtros en el propio almacén con `withFilters()`, lo que convertía una instancia compartida en una fuga entre inquilinos; el método ya no existe. Apéndice A, puntos 26 y 43.)

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
use NeuronAI\RAG\VectorStore\Filter\Filter;
use NeuronAI\RAG\VectorStore\Filter\FilterExpression;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class KnowledgeBaseAgent extends RAG
{
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
        return VectorStore::driver('knowledge_base');
    }

    protected function retrievalScope(): ?FilterExpression
    {
        return Filter::eq('tenant_id', $this->tenant->id);
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

### El filtro de inquilino no es opcional

`retrievalScope()` devuelve el filtro de inquilino incondicionalmente, y el nodo de recuperación lo aplica a cada búsqueda que hace este agente. No hay camino de código que consulte el almacén sin él. Cualquier otra cosa que añada un filtro durante una ejecución —un middleware en el nodo de recuperación, una estrategia de recuperación a medida— se combina con el ámbito mediante AND, así que puede estrechar la búsqueda pero nunca ampliarla.

La regla de la Sección 12.6: **filtra en la recuperación, nunca después.** Un documento recuperado y luego excluido de la respuesta estuvo igualmente en el contexto del modelo, y los modelos parafrasean. El filtro de inquilino es el equivalente RAG de un `where tenant_id = ?` en cada consulta, y pertenece al mismo sitio: al componente que construye la consulta.

::: {.callout .callout-warning}
[`setRetrievalScope()` reemplaza el ámbito; no se suma a él]{.callout-title}

`RAG` también tiene un setter `setRetrievalScope()`, y es tentador usarlo desde un controlador para un filtro extra puntual. No lo hagas, en este agente. El setter *reemplaza* lo que devuelve `retrievalScope()`: pásale `Filter::eq('visibility', 'public')` y el filtro de inquilino desaparece, y la búsqueda recorre los artículos públicos de todos los inquilinos. Mantén cada restricción obligatoria dentro del hook, calculada a partir de las dependencias del constructor.
:::

### Elegir un almacén en Laravel

De la Sección 12.5, con la lente de Laravel:

**MariaDB 11.7+** — una tabla en la base de datos que ya ejecutas. Copias de seguridad, monitorización, transacciones y conmutación por error ya resueltas. Para la mayoría de las aplicaciones Laravel es la respuesta correcta, y es el almacén registrado arriba.

**Elasticsearch o Meilisearch** — si ya ejecutas uno para la búsqueda del sitio, úsalo y evita un segundo sistema.

**Pinecone o Qdrant** — cuando la escala exija de verdad una base de datos dedicada.

**PHPVector** — `neuron-core/php-vector`, PHP puro, HNSW más búsqueda híbrida BM25, ningún servicio. Atractivo para despliegues autoalojados y clientes que no pueden añadir infraestructura, pero en el momento de escribir esto no tiene ninguna versión para NeuronAI v4 (Sección 12.5). Compruébalo antes de contar con él.

La regla general se sostiene: **usa lo que ya ejecutas.** Elijas el que elijas, acepta el mismo argumento `schema:`, y los mismos filtros portables funcionan en todos.

### Puntos clave

- Declara los metadatos filtrables en un `DocumentSchema`; registra el almacén con `VectorStore::extend()`, no en la configuración en caché.
- Pon el filtro de inquilino en `retrievalScope()` para que ningún camino lo sortee, y nunca lo reemplaces con `setRetrievalScope()`.
- Una instancia de almacén compartida es segura: los filtros viajan con cada búsqueda.
- MariaDB para la mayoría de las aplicaciones Laravel.

## 20.2 Ingesta en cola

### El trabajo

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\Article;
use App\Rag\MarkdownSectionSplitter;
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
            $document->setSourceType('article');
            $document->setSourceName("article-{$this->article->id}");
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->getTimestamp());
        }

        $store    = VectorStore::driver('knowledge_base');
        $embedder = EmbeddingProvider::driver();

        // Fail on a bad document before paying for its embedding
        foreach ($documents as $document) {
            $store->getSchema()->validate($document);
        }

        $store->addDocuments($embedder->embedDocuments($documents));
    }
}
```

Componentes autónomos (Sección 12.2) en lugar de un agente RAG: la ingesta no necesita proveedor de chat, ni instrucciones, ni herramientas. Mantener el trabajo ligero significa que arranca más rápido y tiene menos razones para fallar.

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
    VectorStore::driver('knowledge_base')->delete(
        Filter::where('tenant_id', $this->tenantId)->where('article_id', $this->articleId),
    );
}
```

Delimitar el borrado por inquilino además de por artículo no cuesta nada y significa que un error en el llamante no puede eliminar los fragmentos de otro inquilino.

### Reindexar en lugar de añadir

```php
class ReindexArticle implements ShouldQueue
{
    public function handle(): void
    {
        $documents = StringDataLoader::for($this->article->body)->getDocuments();

        foreach ($documents as $document) {
            $document->setSourceType('article');
            $document->setSourceName("article-{$this->article->id}");   // stable — the ID, never the title
            $document->addMetadata('tenant_id',  $this->article->tenant_id);
            $document->addMetadata('article_id', $this->article->id);
            $document->addMetadata('visibility', $this->article->visibility);
            $document->addMetadata('updated_at', $this->article->updated_at->getTimestamp());
        }

        (new KnowledgeBaseAgent($this->article->tenant))
            ->reindexBySource($documents);
    }
}
```

`reindexBySource()` borra todo lo guardado bajo el `sourceType` y el `sourceName` de cada documento, y luego valida, calcula las incrustaciones y añade los fragmentos nuevos. El esquema es la razón de que aquí se repita cada línea de metadatos: quita la línea de `tenant_id` y el trabajo falla antes de calcular ninguna incrustación, en lugar de escribir fragmentos que ningún inquilino puede recuperar.

La restricción de la Sección 12.6, repetida porque es fácil equivocarse: **`sourceName` debe ser estable.** Usa el ID del artículo. Derívalo del título y un cambio de nombre editorial dejará huérfanos los fragmentos viejos: se quedan en el índice, no se pueden borrar por fuente, y el agente responde a partir de ambas versiones.

Que sea un string que no sea puramente numérico: `article-42`, no `"42"`. En el código 4.x con el que se verificó este libro, `reindexBySource()` agrupa los documentos en un array de PHP indexado por nombre de fuente, PHP convierte la clave `"42"` en el entero `42`, y el filtro de borrado falla entonces la validación del esquema porque `sourceName` es un campo string. Un prefijo lo evita, y de todos modos se lee mejor en el índice.

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
- Respeta el esquema: campos obligatorios presentes, enteros como `int`, fechas como marcas de tiempo.
- `reindexBySource()` con un ID estable y con prefijo como `sourceName`; borra por filtro.
- Cola dedicada, límite de tasa, rellenos por bloques, reintentos.
- Sigue `indexed_at` y pon una alerta sobre la diferencia.

## 20.3 Recuperación consciente de los permisos

### El problema

Tu base de conocimiento tiene artículos públicos, artículos solo para clientes y runbooks internos. Todos en un mismo índice.

Un cliente hace una pregunta. Si la recuperación casa con un runbook interno y este entra en el contexto, el modelo puede parafrasearlo dentro de la respuesta. El usuario nunca vio el documento, pero obtuvo su contenido.

**Eso es una violación de datos, y en tus registros no lo parece.** No se renderizó ningún documento, no se llamó a ningún punto de conexión: la fuga ocurrió dentro de una paráfrasis.

### La solución

El agente recibe ahora el `User` que hace la petición junto al `Tenant`, y el ámbito crece en una condición:

```php
protected function retrievalScope(): ?FilterExpression
{
    return Filter::where('tenant_id', $this->tenant->id)
        ->whereIn('visibility', $this->allowedVisibilities());
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

    $answer = (new KnowledgeBaseAgent($tenant, $customerUser))
        ->chat(new UserMessage('What is the emergency override code?'))
        ->getMessage()
        ?->getContent();

    $this->assertStringNotContainsString('OMEGA-7', (string) $answer);
}
```

Un token distintivo en un documento restringido, y un aserto de que nunca aflora. Este es las pruebas por contrato de la Sección 1.5 aplicado a la seguridad: no puedes hacer asertos sobre la redacción de la respuesta, pero sí sobre lo que nunca debe aparecer en ella.

Ejecútalo en CI. Es una de las pocas pruebas de IA a la vez lo bastante determinista como para fiarse y lo bastante importante como para condicionar un despliegue.

Puedes hacerlo totalmente determinista afirmando un paso antes: sobre lo que llegó al modelo, no sobre lo que dijo el modelo. Los documentos recuperados se inyectan en las instrucciones, así que dale al agente el `FakeAIProvider` del framework y comprueba el prompt de sistema que registró:

```php
$provider = new FakeAIProvider(new AssistantMessage('I cannot help with that.'));

(new KnowledgeBaseAgent($tenant, $customerUser))
    ->setAiProvider($provider)
    ->chat(new UserMessage('What is the emergency override code?'));

$provider->assertSent(
    fn (RequestRecord $request): bool => !$request->systemPrompt?->contains('OMEGA-7')
);
```

Sin modelo, sin red, sin inestabilidad: si se recuperó el fragmento restringido, la prueba falla siempre.

### Filtros de frescura

El mismo mecanismo gestiona el contenido superado:

```php
return Filter::where('tenant_id', $this->tenant->id)
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
        private readonly Tenant $tenant,
        private readonly User $user,
        private readonly RefundService $refunds,
    ) {
        parent::__construct(threadId: "t{$tenant->id}:u{$user->id}");
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
        return VectorStore::driver('knowledge_base');
    }

    protected function retrievalScope(): ?FilterExpression
    {
        return Filter::where('tenant_id', $this->tenant->id)
            ->whereIn('visibility', $this->allowedVisibilities());
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
            modelClass: ChatMessage::class,
            contextWindow: config('neuron.context_window'),
        );
    }

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

### La instrucción que más trabaja

> *"Never state order details you have not retrieved with a herramienta."*

Y su hermana más fuerte:

> *"Never state a monetary amount you did not retrieve from a herramienta."*

Sin estas, el modelo producirá con seguridad el estado de un pedido o el importe de un reembolso de la nada, porque ha visto miles de conversaciones de soporte durante el entrenamiento y sabe qué aspecto tienen.

**Las instrucciones antialucinación deben ser específicas sobre la clase de hecho.** «Sé preciso» no hace nada. «Nunca declares un importe monetario que no hayas recuperado» es accionable, comprobable y —con el `FaithfulnessJudge` de la Sección 10.5— medible.

### Una clase, casi todo el libro

Cuenta lo que hay dentro: abstracción de proveedor (3.6), estructura del prompt de sistema (3.5), un hilo que sirve de clave tanto al historial de conversación como a cualquier aprobación de reembolso en pausa (4.3, 18.2, 18.3), herramientas con dependencias (5.3), visibilidad de herramientas (5.10), límites de ejecución (5.9), recuperación RAG (12.1), filtros de permisos (20.3) y un contrato antialucinación (11.5).

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
3. **`reindexBySource()`** usando el ID del artículo con prefijo (`article-42`) como nombre estable de fuente, sobre un almacén cuyo `DocumentSchema` declara cada campo por el que filtras. Editar un artículo debe reemplazar sus fragmentos, no añadirse a ellos.
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
