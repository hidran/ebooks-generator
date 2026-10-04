# Capítulo 18 — Agentes como ciudadanos de primera clase

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

Este capítulo es conceptual y no tiene código propio, pero el repositorio complementario [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene versiones ejecutables de todo lo que el libro construye.
:::

## 18.1 Agentes en el contenedor

### El problema de `::make()` por todas partes

```php
class SupportController extends Controller
{
    public function ask(Request $request, Conversation $conversation)
    {
        return SupportAgent::make(workflowId: $conversation->threadId())
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ?->getContent();
    }
}
```

Funciona. Pero ahora el controlador construye el agente, lo que significa que no puedes sustituirlo en pruebas, no puedes entregarle los almacenes que comparte el resto de la aplicación y no puedes configurarlo en un solo sitio. (`threadId()` da nombre al hilo de la conversación; la Sección 18.2 trata de cómo acertar con ese nombre.)

### Inyección por constructor

```php
namespace App\Neuron\Agents;

use NeuronAI\Agent\Agent;
use NeuronAI\Chat\History\MessageStoreInterface;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Workflow\Persistence\PersistenceInterface;

class SupportAgent extends Agent
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

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;
    }

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;
    }

    // contextWindow() arrives in Section 18.2, tools() in Section 18.3
}
```

El constructor pide las dos cosas que un agente conserva entre peticiones —dónde viven las conversaciones (Sección 18.2) y dónde viven las ejecuciones pausadas (Sección 18.4)— y nada sobre quién pregunta. Ni usuario, ni inquilino, ni hilo: la clase describe un agente, no una conversación.

Recuerda `parent::__construct()` (Sección 4.3) y que un constructor propio cambia lo que `make()` acepta. `make()` reenvía sus argumentos al constructor, así que una vez que el constructor es tuyo, `make(workflowId: ...)` es un parámetro con nombre desconocido; el hilo llega por otra vía, más abajo. Y llama a las propiedades promovidas como quieras, salvo `$messageStore` y `$persistence`: `Agent` ya declara ambas, con tipos anulables, y PHP rechaza la redeclaración con un error fatal.

### El binding

```php
namespace App\Providers;

use App\Models\ChatMessage;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\ServiceProvider;
use NeuronAI\Chat\History\EloquentMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;
use NeuronAI\Workflow\Persistence\DatabasePersistence;
use NeuronAI\Workflow\Persistence\PersistenceInterface;

class NeuronServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        // Stateless: it resolves the model's connection on every call
        $this->app->singleton(
            MessageStoreInterface::class,
            fn () => new EloquentMessageStore(ChatMessage::class),
        );

        // It keeps the PDO it was given, so every resolution takes the current one
        $this->app->bind(
            PersistenceInterface::class,
            fn () => new DatabasePersistence(DB::connection()->getPdo()),
        );
    }
}
```

Es un proveedor de servicios tuyo —`php artisan make:provider NeuronServiceProvider` lo crea y lo registra—, no el `NeuronAIServiceProvider` del SDK. Registra los dos almacenes y nada más. El agente no necesita ningún binding: Laravel lee su constructor y lo resuelve por autowiring.

```php
class SupportController extends Controller
{
    public function ask(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ) {
        Gate::authorize('participate', $conversation);

        return $agent
            ->for($conversation->threadId())
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ?->getContent();
    }
}
```

**El contenedor construye el agente; la petición lo vincula.** La acción pide un agente en su firma y recibe uno, conectado a los almacenes de la aplicación. La policy decide si este usuario puede usar esta conversación, y solo entonces `for()` devuelve una copia del agente vinculada al hilo de esa conversación; la instancia que construyó el contenedor no se modifica nunca. Pide el agente en la acción, no en el constructor del controlador: se resuelve cuando se ejecuta la acción, después de que el middleware haya autenticado al usuario, y nada lo retiene más tiempo que la llamada.

### Por qué merece la ceremonia

**Testabilidad.** Entrega al contenedor un agente cuyo proveedor es un doble y el controlador habla con él; la copia que hace `for()` comparte ese proveedor. Este es el problema de la Sección 1.5: no puedes hacer asertos sobre la salida del modelo, así que la frontera que *sí* puedes testear es cómo el controlador maneja un agente, y la inyección de dependencias es lo que hace que esa frontera exista.

```php
$provider = new FakeAIProvider(new AssistantMessage('Your order ships tomorrow.'));

$this->app->instance(
    SupportAgent::class,
    $this->app->make(SupportAgent::class)->setAiProvider($provider),
);

$this->actingAs($user)
    ->post("/conversations/{$conversation->id}/messages", [
        'message' => 'Where is my order?',
    ])
    ->assertOk();

$provider->assertCallCount(1);
```

**Configuración por usuario.** El hilo dice de quién es la conversación, así que lo que el agente construye para una ejecución —sus herramientas y la visibilidad de estas (Sección 5.10)— se deduce del hilo al que fue vinculado, sin que el controlador lo sepa. La Sección 18.3 muestra cómo.

**Un solo sitio que cambiar.** Los almacenes se deciden en el proveedor de servicios; el proveedor, las herramientas y las instrucciones, en la clase. Ningún controlador decide nada de eso.

**Se lee como Laravel.** Lo que importa para la adopción. Un agente que llega por inyección es un servicio como cualquier otro, y un equipo ya sabe razonar sobre servicios.

### Ciclos de vida

Los dos bindings tienen ciclos de vida distintos a propósito, y el agente tiene un tercero:

- El almacén de mensajes es un `singleton()`. `EloquentMessageStore` guarda una clase de modelo y nada más; resuelve la conexión del modelo en cada llamada.
- La persistencia es un simple `bind()`. `DatabasePersistence` conserva el PDO que recibió, así que cada resolución tiene que tomar el actual de Laravel. En un proceso de larga vida una reconexión sustituye ese PDO, y un singleton seguiría sujetando el antiguo.
- El agente no se registra en absoluto. El autowiring construye uno nuevo cada vez que se resuelve —por petición, por trabajo—, y ese es el ciclo de vida que quieres.

::: {.callout .callout-warning}
[Nunca uses `singleton()` con un agente]{.callout-title}

Un agente captura su persistencia —y ese PDO— en el momento en que se construye. Regístralo como singleton y, bajo Octane o en un proceso de cola, una sola instancia atiende todas las peticiones durante toda la vida del proceso: sigue sujetando una conexión mucho después de que una reconexión la haya sustituido, y lo que una petición le haya configurado sigue ahí para la siguiente. La responsabilidad es tuya, y bajo PHP-FPM no se manifestará en absoluto.
:::

### Puntos clave

- Inyección por constructor para los almacenes, con el binding en un proveedor de servicios; el agente mismo se resuelve por autowiring.
- El contenedor construye el agente; la petición autoriza la conversación y vincula su hilo con `for()`.
- Testabilidad, configuración por usuario, punto único de cambio.
- Nunca uses `singleton()` con un agente: resuélvelo por petición o por trabajo.

## 18.2 EloquentMessageStore

### Una sola migración

```bash
php artisan make:migration create_neuron_tables
php artisan make:model ChatMessage
```

Una sola migración tuya crea las dos tablas que NeuronAI necesita: `chat_messages` para las conversaciones y `workflow_store` para las ejecuciones de la Sección 18.4. Sustituye el cuerpo del archivo generado por este y luego ejecuta `php artisan migrate`:

```php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * The conversations (EloquentMessageStore) and the durable runs (DatabasePersistence) of the Neuron agents.
     */
    public function up(): void
    {
        // MySQL and MariaDB collations ignore case and accents: identifiers must compare byte by byte there.
        $mysql = in_array(Schema::getConnection()->getDriverName(), ['mysql', 'mariadb'], true);

        Schema::create('chat_messages', function (Blueprint $table) use ($mysql) {
            $table->id();
            if ($mysql) {
                $table->binary('thread_id', 255);
                $table->binary('message_id', 64);
            } else {
                $table->string('thread_id', 255);
                $table->string('message_id', 64);
            }
            $table->string('role', 32);
            $table->longText('content')->nullable();
            $table->longText('meta')->nullable();
            $table->timestamp('archived_at')->nullable();
            $table->timestamps();
            $table->unique(['thread_id', 'message_id']);
        });

        Schema::create('workflow_store', function (Blueprint $table) use ($mysql) {
            if ($mysql) {
                $table->string('partition', 510)->charset('ascii')->collation('ascii_bin');
                $table->string('key', 510)->charset('ascii')->collation('ascii_bin');
                $table->longText('value')->charset('ascii');
            } else {
                $table->string('partition', 510);
                $table->string('key', 510);
                $table->longText('value');
            }
            $table->timestamp('updated_at')->useCurrent();
            $table->primary(['partition', 'key']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('workflow_store');
        Schema::dropIfExists('chat_messages');
    }
};
```

Es la migración que los mantenedores publican en la skill `neuron-laravel-integration` del framework, que declara haberla ejecutado sin cambios en SQLite, MySQL 8.4, MariaDB 11.7 y PostgreSQL 17. En `chat_messages` hay tres cosas que están ahí para el almacén:

- `message_id` es la identidad de un mensaje. El almacén añade por `(thread_id, message_id)`, así que escribir dos veces el mismo mensaje lo guarda una sola vez, y el índice único sirve para todas las búsquedas por hilo.
- El `id` autoincremental ordena el hilo. Sea cual sea la clave que use tu modelo, debe seguir el orden de inserción: autoincremental, ULID o UUIDv7, nunca UUIDv4.
- `archived_at` marca los mensajes recortados de la ventana de contexto, que se conservan en lugar de borrarse (más abajo).

Las columnas `binary()` son para MySQL y MariaDB, cuyas intercalaciones por defecto no distinguen mayúsculas de minúsculas: con `string()`, dos hilos cuyos nombres solo se diferencian en las mayúsculas compartirían un historial.

::: {.callout .callout-warning}
[No publiques las migraciones del SDK]{.callout-title}

neuron-laravel 2.0.0 sigue ofreciendo `php artisan vendor:publish --tag=neuron-migrations` y un modelo `NeuronAI\Laravel\Models\ChatMessage`, y ninguno de los dos encaja con neuron-ai 4.0.3. El almacén identifica cada mensaje por `message_id`; la tabla del SDK no tiene esa columna y su modelo no la hace fillable. En SQLite, donde este libro lo comprobó, no falla nada: el mismo mensaje se guarda dos veces y vuelve con un ID distinto. Usa la migración de arriba y el modelo de abajo.
:::

### Úsalo

```php
namespace App\Models;

use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Model;

#[Fillable(['thread_id', 'message_id', 'role', 'content', 'meta'])]
class ChatMessage extends Model
{
    protected function casts(): array
    {
        return [
            'content' => 'array',
            'meta' => 'array',
        ];
    }
}
```

Cinco columnas fillable y dos conversiones a array: eso es todo lo que el almacén le pide al modelo. El almacén, por su parte, no recibe nada más que la clase del modelo —`new EloquentMessageStore(ChatMessage::class)`, la línea que `NeuronServiceProvider` ya contiene—, y el agente se lo entrega al framework a través de un hook. Un segundo hook dice cuánta conversación se le puede enviar al modelo:

```php
class SupportAgent extends Agent
{
    // ...

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;
    }

    protected function contextWindow(): int
    {
        return 100_000;
    }
}
```

```php
$agent->for('THREAD_ID')->chat(new UserMessage('Hello'));
```

Fíjate en lo que el almacén *no* recibe: el hilo. El almacén no tiene estado —una sola instancia atiende todas las conversaciones, y por eso puede ser un singleton—, y cada lectura y cada escritura nombra el hilo al que se refiere. El hilo pertenece al agente. Lo vinculas una vez, con `for()`, y el framework nunca se inventa uno: un agente sin hilo se niega a ejecutarse.

El hilo es más que una clave del historial. Es también el **ID del flujo de trabajo** del agente: el nombre bajo el que una ejecución pausada se persiste y más tarde se vuelve a encontrar (Sección 18.4). Un solo identificador, vinculado en un solo sitio, da nombre tanto a la conversación como a la ejecución.

Entre el almacén y el modelo está `ChatHistory`, una clase concreta que el agente se construye a sí mismo cada vez que se ejecuta, a partir exactamente de esas tres cosas: el almacén, el hilo y la ventana. Carga los mensajes activos del hilo y los mantiene dentro del presupuesto. Tú nunca la construyes.

::: {.callout .callout-warning}
[Sobrescribir `chatHistory()` no conserva nada]{.callout-title}

`messageStore()` y `contextWindow()` son los únicos hooks de memoria en neuron-ai 4.0.3. Una clase que sobrescribe `chatHistory()` en su lugar —como siguen mostrando el README de neuron-laravel 2.0.0 y las skills de Boost que incluye— se carga y responde sin ningún error, porque nada llama a ese método. El agente usa en silencio el almacén en memoria con una ventana de 50.000 tokens, y la conversación desaparece cuando termina la petición. Si un agente lo olvida todo entre dos peticiones, busca primero ese método.
:::

### Hacer real `thread_id`

`'THREAD_ID'` es un marcador de posición. En la práctica es el límite de aislamiento, y equivocarse es una fuga de datos. Da nombre al hilo en el servidor, a partir de un registro, y deja que una policy diga quién puede usar ese registro:

```php
class Conversation extends Model
{
    /** Named on the server from three columns of this row, never from a request. */
    public function threadId(): string
    {
        return "t{$this->tenant_id}:u{$this->user_id}:c{$this->id}";
    }
}
```

```php
class ConversationPolicy
{
    public function participate(User $user, Conversation $conversation): bool
    {
        return $conversation->user_id === $user->id
            && $conversation->tenant_id === $user->tenant_id;
    }
}
```

Eso es lo que hacían dos líneas del controlador de la Sección 18.1. La ruta nombra una conversación; `Gate::authorize('participate', $conversation)` decide si este usuario puede usarla; solo entonces `for($conversation->threadId())` vincula el agente. Para nada de esto necesita el agente un argumento de constructor: `for()` es la puerta de entrada de la identidad en un agente construido por el contenedor, y el código que la precede es el único sitio que decide qué hilo puede tocar una petición.

**Nunca derives el ID de hilo de la entrada del usuario.** Un parámetro de petición que se convierte en ID de hilo significa que cualquiera puede leer la conversación de cualquiera cambiando un número. El ID de conversación de la URL también es entrada del usuario; es la policy la que lo convierte en un recurso que este usuario puede usar. Deriva el hilo en el servidor a partir de un recurso autenticado y autorizado.

Es el error de seguridad más probable de este capítulo.

### La ventana de contexto, por proveedor

La Sección 4.4 decía que la dedujeras del modelo y nunca la escribieras a fuego para todo el proyecto. En Laravel:

```php
// config/neuron.php
'context_windows' => [
    'anthropic' => 185_000,
    'openai'    => 118_000,
    'gemini'    => 920_000,
    'ollama'    => 29_000,
],
```

```php
protected function contextWindow(): int
{
    return config('neuron.context_windows.' . config('neuron.provider.default'), 29_000);
}
```

Cambia de proveedor por entorno y el recortador lo sigue. Escribe 100.000 a fuego y quien ejecute Ollama en local chocará con errores de contexto que en producción no aparecen nunca.

### Extender el modelo

`ChatMessage` es un modelo tuyo, así que puede crecer con la aplicación. Una aplicación real normalmente quiere:

- Una clave externa hacia `conversations` o `users`
- Borrado lógico para la política de retención
- Un índice sobre `thread_id` más una marca de tiempo
- Una columna de inquilino

Una regla las gobierna a todas: el almacén escribe sus cinco columnas y no sabe nada de las tuyas. Una columna `NOT NULL` que el almacén no rellena hace fallar cada escritura. Haz anulables las columnas de la aplicación, o rellénalas en un hook `creating` a partir de lo único que toda fila lleva consigo, su hilo:

```php
class ChatMessage extends Model
{
    use SoftDeletes;

    // ...

    protected static function booted(): void
    {
        // The store fills its five columns; the thread says what the others are
        static::creating(function (ChatMessage $message): void {
            $scope = ThreadScope::of($message->thread_id);

            $message->tenant_id = $scope->tenantId;
            $message->conversation_id = $scope->conversationId;
        });
    }
}
```

`ThreadScope` vuelve a leer el nombre que escribió `threadId()`; lo tienes en la Sección 18.3. Aquí es también donde vive el RGPD: las conversaciones contienen lo que sea que los usuarios hayan escrito, lo que en un contexto de soporte significa datos personales. El borrado, la exportación y la retención son requisitos de producto, no ocurrencias tardías: la advertencia sobre registros de la Sección 3.7, hecha concreta.

Un comportamiento cambia las cuentas de la retención. Cuando el historial recorta mensajes de la ventana de contexto, no los borra: los marca con `archived_at` y carga solo las filas no archivadas. El modelo ve el hilo recortado; tu tabla conserva la transcripción completa. Eso es bueno para la auditoría y para la exportación, pero significa que «el agente lo olvidó» y «ya no lo guardamos» son ahora afirmaciones distintas. Tu tarea de retención tiene que borrar explícitamente las filas archivadas.

### Puntos clave

- Una migración y un modelo tuyos; la tabla que publica el SDK no encaja con neuron-ai 4.0.3.
- `messageStore()` devuelve el almacén y `contextWindow()` el presupuesto; el hilo se vincula en el agente con `for()`, nunca se le da al almacén.
- El ID de hilo es el límite de aislamiento: derívalo en el servidor, nunca de la entrada.
- Deduce la ventana de contexto del proveedor configurado.
- Extiende `ChatMessage` para claves externas, multiinquilino y retención, con columnas anulables o rellenadas en `creating`; las filas recortadas se archivan, no se borran.

## 18.3 Aislamiento multi-tenant

### Los cuatro puntos de fuga

Un sistema agéntico en una aplicación multi-tenant tiene cuatro sitios por donde los datos de los inquilinos pueden cruzarse:

1. **Historial de chat** — `thread_id`
2. **Almacén vectorial** — el ámbito de recuperación (Sección 12.6)
3. **Herramientas** — los datos que consultan
4. **Persistencia de flujos de trabajo** — el ID de flujo de trabajo

Falla en uno solo y tienes una brecha. Ten la lista en un sitio donde la veas durante la revisión de código.

Para un agente, el framework fusiona el primero y el último: el ID de hilo *es* el ID del flujo de trabajo. Acierta con el hilo y la ejecución persistida queda delimitada con él; equivócate y se filtran los dos a la vez.

### Un agente consciente del inquilino

```php
namespace App\Neuron;

use LogicException;

/** Who a thread belongs to, read back from the name Conversation::threadId() gave it. */
final readonly class ThreadScope
{
    private function __construct(
        public int $tenantId,
        public int $userId,
        public int $conversationId,
    ) {}

    public static function of(?string $threadId): self
    {
        if (preg_match('/^t(\d+):u(\d+):c(\d+)$/', (string) $threadId, $match) !== 1) {
            throw new LogicException(
                "Thread '{$threadId}' names no tenant, user and conversation."
            );
        }

        return new self((int) $match[1], (int) $match[2], (int) $match[3]);
    }
}
```

```php
class SupportAgent extends Agent
{
    // ...

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());

        return [
            // The tools receive the tenant - they cannot query outside it
            new SearchOrdersTool($scope->tenantId),
            new GetOrderStatusTool($scope->tenantId),
        ];
    }
}
```

Así es como un agente que se construyó sin saber nada de quién lo llama llega a conocer a su inquilino: por el hilo al que fue vinculado, no por `auth()` ni por un argumento de constructor. El nombre se compuso en el servidor a partir de tres columnas de una fila, nunca de nada que venga en la petición, y un hilo que no lleve las tres se rechaza antes de que exista una sola herramienta.

### El principio

**Delimita en la construcción, no en el momento de la consulta.**

La herramienta recibe el ID de un inquilino y construye sus consultas a partir de él. No existe un camino de código en el que una herramienta consulte sin ámbito de inquilino, porque no tiene forma de hacerlo.

Compara con la alternativa: una herramienta que lee el inquilino actual de una variable global o de una facade dentro de `__invoke()`. Funciona hasta que algo se ejecuta fuera de una petición: un trabajo en cola, un comando programado, un flujo de trabajo reanudado. Entonces la global está vacía o, peor, contiene el inquilino equivocado.

**Los sistemas agénticos se ejecutan fuera del ciclo de petición mucho más a menudo que el código de aplicación normal.** Procesos de cola (Sección 16.4), flujos de trabajo reanudados (Sección 15.4), ingesta programada (Capítulo 20). El contexto de inquilino ambiental no es fiable en los tres casos. Pásalo explícitamente, que es lo que hace el hilo: el mismo agente, vinculado al mismo hilo, construye las mismas herramientas en un controlador y en un proceso de cola.

Ese argumento se generaliza mucho más allá de NeuronAI.

### IDs de flujo de trabajo

El ID del flujo de trabajo del agente viene gratis con su hilo. Tus propios flujos de trabajo declaran el suyo sobrescribiendo `workflowId()`:

```php
class RefundWorkflow extends Workflow
{
    public function __construct(
        private readonly Tenant $tenant,
        private readonly Order $order,
    ) {
        parent::__construct();
    }

    public function workflowId(): ?string
    {
        return "t{$this->tenant->id}:refund:{$this->order->id}";
    }

    // nodes() ...
}
```

Con prefijo de inquilino, para que un flujo de trabajo reanudado no pueda confundirse con el de otro inquilino, y con clave de negocio, para que una petición posterior que solo conoce el inquilino y el pedido reconstruya el flujo de trabajo y encuentre su ejecución pausada con una sola lectura. El flujo de trabajo de reembolso del Capítulo 22 conserva el `refund:{orderId}`, más corto, de la Sección 15.4: la clave primaria de un pedido ya es única entre inquilinos, y el prefijo es para las claves de negocio que no lo son. Un flujo de trabajo sin ningún ID —ni declarado ni asignado— no se ejecuta: el motor nunca se inventa uno.

### Testear el aislamiento

Merece escribirse como prueba de verdad:

```php
public function test_tenant_a_history_never_reaches_tenant_b(): void
{
    // The hostile part: both tenants hold user 3 and conversation 7
    $a = (new Conversation())->forceFill(['id' => 7, 'tenant_id' => 1, 'user_id' => 3]);
    $b = (new Conversation())->forceFill(['id' => 7, 'tenant_id' => 2, 'user_id' => 3]);

    $modelA = new FakeAIProvider(new AssistantMessage('Noted.'));
    $modelB = new FakeAIProvider(new AssistantMessage('I do not know.'));

    app(SupportAgent::class)->setAiProvider($modelA)
        ->for($a->threadId())
        ->chat(new UserMessage('My secret code is ALPHA'));

    app(SupportAgent::class)->setAiProvider($modelB)
        ->for($b->threadId())
        ->chat(new UserMessage('What is my secret code?'));

    // Assert on what tenant B's model was sent, not on what a model might answer
    $modelB->assertCallCount(1);
    $modelB->assertSent(fn (RequestRecord $request): bool =>
        ! str_contains(json_encode($request->messages), 'ALPHA'));
}
```

Fíjate en el montaje deliberadamente hostil: los *mismos* números de usuario y de conversación para ambos inquilinos. Si falta el prefijo de inquilino, esta prueba falla, que es exactamente lo que quieres que cace.

Fíjate también en sobre qué hace el aserto. `FakeAIProvider` (Laboratorio 7) registra cada petición, así que la prueba inspecciona los mensajes que llegaron al modelo del inquilino B en lugar de confiar en que un modelo real repita el secreto. No se llama a ningún modelo, el resultado es el mismo en cada ejecución y la prueba puede condicionar un despliegue.

### Puntos clave

- Cuatro puntos de fuga: historial, almacén vectorial, herramientas, persistencia de flujos de trabajo; para un agente, el hilo cubre el primero y el último.
- Delimita en la construcción; no leas contexto ambiental dentro de las herramientas.
- Declara con `workflowId()` IDs de flujo de trabajo con clave de negocio y prefijo de inquilino.
- El código agéntico se ejecuta a menudo fuera del ciclo de petición: allí las globales no son fiables.
- Escribe una prueba de aislamiento con un identificador que colisione, y haz el aserto sobre lo que se envió al modelo.

## 18.4 Persistencia de flujos de trabajo en la base de datos

### El montaje

```php
class SupportAgent extends Agent
{
    // ...

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;
    }
}
```

`persistence()` es un hook como `provider()` y `messageStore()`; `setPersistence()` es su gemelo setter, para un `Workflow` simple o un caso puntual. Lo que devuelve aquí es la `DatabasePersistence` que `NeuronServiceProvider` construye sobre el propio PDO de Laravel, y su tabla llegó con la migración de la Sección 18.2.

Esa tabla, `workflow_store`, es toda la persistencia de NeuronAI: un único espacio clave-valor particionado. Cada registro de una ejecución —su arranque, su registro de control, los resultados de sus pasos— vive en la partición que lleva el nombre del **ID del flujo de trabajo**, que para un agente es el hilo. Eso es lo que permite a un punto de conexión de aprobación vincular `SupportAgent` al hilo de la conversación y encontrar la ejecución pausada con una sola lectura. Cuando una ejecución termina limpiamente, su partición se barre; no se acumula nada.

::: {.callout .callout-warning}
[`workflow_store` no es una tabla de la aplicación]{.callout-title}

Los nombres de partición y las claves están codificados en hexadecimal y los valores son registros del motor codificados en base64. No hay ningún `tenant_id` por el que filtrar ni nada pensado para leerse con un `where()`. Trata la tabla como el almacenamiento privado del motor: haz copia de seguridad, nunca la consultes. En MySQL además requiere el modo SQL estricto —el ajuste de conexión `'strict' => true`, el valor por defecto de Laravel—, y `DatabasePersistence` se niega a escribir sin él antes que arriesgarse a registros truncados.
:::

### Por qué la base de datos en lugar de archivos

La Sección 15.4 enumeraba los backends. En Laravel, `DatabasePersistence` te da:

**Seguridad multiservidor.** Cualquier proceso puede reanudar cualquier flujo de trabajo. La persistencia en archivo sobre disco local significa que la reanudación debe caer en la misma máquina, cosa que detrás de un balanceador de carga es un lanzamiento de moneda. El backend de archivos está pensado para un uso controlado de un solo proceso.

**Continuación atómica.** Cada escritura es un compare-and-write condicional dentro de una transacción en la conexión de Laravel. Dos procesos que compiten por continuar la misma ejecución no pueden ganar ambos.

**Una sola conexión.** La ejecución vive en la base de datos que ya gestionas, en la conexión que usan tus modelos, sin una segunda credencial que administrar.

**Copias de seguridad.** Los flujos de trabajo en vuelo se respaldan con todo lo demás, en lugar de vivir en un directorio que nadie se acuerda de incluir.

`EloquentPersistence` es el otro backend de base de datos. Recibe una clase de modelo y resuelve la conexión del modelo en cada operación, así que puede ser un singleton. No es un sustituto directo para esta tabla: necesita una tabla propia, con una clave primaria `id` corriente y `unique(partition, key)` en lugar de la clave compuesta, y un modelo tuyo —`App\Models\WorkflowRecord`, por ejemplo— con `partition`, `key` y `value` fillable y sin borrado lógico.

::: {.callout .callout-warning}
[No el `WorkflowStore` del SDK]{.callout-title}

neuron-laravel 2.0.0 incluye un modelo `NeuronAI\Laravel\Models\WorkflowStore` sobre una tabla `workflow_store` con clave primaria compuesta y sin `id`. `new EloquentPersistence(WorkflowStore::class)` no funciona con neuron-ai 4.0.3: el backend direcciona las filas por una clave que la tabla no tiene. En SQLite, donde este libro lo comprobó, una ejecución completada no se barre nunca, y el siguiente mensaje en el mismo hilo se rechaza con `RunInFlightException` hasta que vence la concesión de diez minutos. Usa `DatabasePersistence`, o dale a `EloquentPersistence` una tabla y un modelo tuyos.
:::

### La pantalla de aprobaciones pendientes

El patrón que esto desbloquea, y el que construye el Capítulo 22. Como el almacén no es consultable, la lista de conversaciones en espera es algo que tu aplicación registra por su cuenta, en el momento en que se entera de la pausa, y se entera sin ninguna excepción. `chat()` retorna con normalidad, con un estado interrumpido:

```php
$state = $agent->chat(new UserMessage($input));

if ($state->isInterrupted()) {
    $conversation->update(['awaiting_approval_at' => now()]);
}
```

```php
class ApprovalsController extends Controller
{
    public function index(Request $request)
    {
        $pending = Conversation::query()
            ->where('tenant_id', $request->user()->tenant_id)
            ->whereNotNull('awaiting_approval_at')
            ->latest('awaiting_approval_at')
            ->paginate();

        return view('approvals.index', compact('pending'));
    }
}
```

La página de detalle le pregunta al propio agente qué está esperando. Vincúlalo al hilo de la conversación y lee `pendingApprovals()`: una acción por cada llamada a herramienta sujeta a aprobación, con el ID de la llamada, el nombre de la herramienta, los argumentos y el motivo que dio la herramienta para pedirla:

```php
foreach ($agent->pendingApprovals() as $action) {
    // $action->id, $action->name, $action->inputs, $action->reason
}
```

La misma información está también en el último mensaje del hilo en el historial de conversación, que es a partir de lo que renderiza un frontend (Capítulo 22).

Como las conversaciones en espera son filas de *tu* tabla, «la IA está esperando a un humano» se convierte en una página de índice corriente con autorización corriente. Ese es el momento en que el humano en el circuito deja de ser una funcionalidad exótica de IA y se convierte en desarrollo de aplicaciones normal, que es precisamente lo que hace el patrón desplegable.

### Recordatorios operativos de la Sección 15.4

Las cuatro preguntas siguen aplicando, ahora con respuestas de Laravel, y los almacenes duraderos añaden una quinta:

- **Notificación** → envía una `Notification` cuando el estado devuelto responde `isInterrupted()`; no hay ninguna excepción que capturar
- **Tiempo de espera** → un comando programado sobre `awaiting_approval_at` que cierra las ejecuciones estancadas con un rechazo, `submitApprovalDecisions([$callId => ['reject', 'Timed out']])->run()`: rechazar es la vía de cancelación
- **Doble reanudación** → la gestiona el motor: un segundo envío para una ejecución ya cerrada no encuentra ninguna ejecución persistida y lanza `InputTranslationException`, y un nuevo `chat()` sobre un hilo que sigue esperando lanza `RunInFlightException`; responde con un 400 y con un 409, y bloquea la entrada en la interfaz hasta que se entregue la decisión
- **Compatibilidad con despliegues** → mantén las peticiones de interrupción pequeñas y planas; la carga serializada contiene tus clases. Las herramientas nunca se serializan, así que una herramienta que guarda un repositorio o un cliente HTTP no plantea problemas a la persistencia
- **Turnos fallidos** → un turno que muere después de haber guardado su pregunta —el proveedor falla tras un paso de herramienta, una excepción se escapa de una herramienta— deja su ejecución `failed`, y el siguiente `chat()` sobre ese hilo lanza `ChatHistoryException: Invalid message sequence`. Termina el turno fallido antes de empezar el siguiente

```php
class SupportAgent extends Agent
{
    // ...

    /** A failed turn that stored its question blocks the next one: finish it first. */
    public function recoverFailedTurn(): void
    {
        $run = $this->inspect();

        if ($run?->status === WorkflowStatus::Failed) {
            $this->run(ExecutionRequest::resume(
                expectedRunId: $run->runId,
                expectedExecutionAttempt: $run->executionAttempt,
            ));
        }
    }
}
```

```php
$agent = $agent->for($conversation->threadId());
$agent->recoverFailedTurn();

$state = $agent->chat(new UserMessage($request->input('message')));
```

Todo punto de conexión que inicia un turno lo llama primero; si no hay nada que recuperar, no hace nada. Antes, no después: una vez que una pregunta nueva se ha apilado sobre un turno fallido, terminar ese turno falla de la misma manera, y solo `resetConversation()` —que borra el historial del hilo junto con su ejecución— libera el hilo.

### Puntos clave

- `DatabasePersistence` sobre el PDO de Laravel, con el binding en el proveedor de servicios y devuelta desde el hook `persistence()` del agente.
- Una sola tabla `workflow_store`, particionada por ID del flujo de trabajo: el hilo, para un agente. Haz copia de seguridad; nunca la consultes.
- Seguro en multiservidor, atómico, en tu conexión existente, respaldado.
- Registra las aprobaciones pendientes en tu propio modelo cuando `isInterrupted()`; lee los detalles con `pendingApprovals()`.
- Las cuatro preguntas operativas reciben respuestas corrientes de Laravel; la quinta es `recoverFailedTurn()` antes de cada turno.

## Laboratorio 12 — Chat persistente multihilo

**Cubre:** bindings del contenedor, `EloquentMessageStore`, aislamiento de hilos, ventanas de contexto.

### Objetivo

Un usuario autenticado puede mantener varias conversaciones independientes con el mismo agente, cada una persistida, cada una aislada, cada una reanudable tras un despliegue completo.

### Requisitos

1. **Una tabla `conversations`** propiedad de los usuarios, con un inquilino, un título y marcas de tiempo. Un usuario puede tener muchas.
2. **El agente se resuelve desde el contenedor**, por inyección en el método, y se vincula a la conversación actual con `for()`; nunca se construye en un controlador.
3. **El ID de hilo se deriva en el servidor** del registro de conversación, una vez que la policy ha autorizado al usuario autenticado para usarla, nunca de un parámetro de petición. Demuéstralo: intenta leer la conversación de otro usuario por ID y obtén un 403 de tu policy, no una respuesta del agente.
4. **La ventana de contexto viene de la configuración**, indexada por el proveedor configurado, como en la Sección 18.2.
5. **Extiende `ChatMessage`** con una clave externa a `conversations`, rellenada en un hook `creating`, y un borrado lógico.

### Criterios de aceptación

- Dos conversaciones de un mismo usuario no ven los mensajes de la otra.
- Dos usuarios con IDs de conversación consecutivos no pueden alcanzar los hilos del otro; verifícalo con una prueba de autorización, no a ojo.
- Reiniciar el servidor de aplicación no pierde nada.
- Cambiar `NEURON_AI_PROVIDER` de `anthropic` a `ollama` cambia la ventana de contexto del recortador sin tocar el código. Registra el valor configurado para demostrarlo.
- Borrar una conversación hace el borrado lógico de sus mensajes, y el agente deja de verlos.
- Un turno que falla a medias no bloquea la conversación: el siguiente mensaje recibe respuesta.

### La parte interesante

Escribe la prueba de aislamiento de la Sección 18.3 con un **ID de conversación que colisione entre dos inquilinos o dos usuarios**. Es la prueba que caza el prefijo ausente, y es la que la gente se salta porque el camino feliz ya funcionaba.

### Ir más allá

Añade un punto de conexión `/conversations/{id}/export` que devuelva la transcripción completa como JSON. Ya has satisfecho el requisito de exportación del RGPD, y descubrirás de inmediato si tu modelo de mensajes lleva suficiente contexto como para ser exportable: la mayoría de los primeros intentos no lo lleva.
