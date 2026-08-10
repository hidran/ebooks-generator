# Capítulo 18 — Agentes como ciudadanos de primera clase

## 18.1 Agentes en el contenedor

### El problema de `::make()` por todas partes

```php
class SupportController extends Controller
{
    public function ask(Request $request)
    {
        return SupportAgent::make()
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ->getContent();
    }
}
```

Funciona. Pero ahora el controlador construye el agente, lo que significa que no puedes sustituirlo en pruebas, no puedes variarlo por inquilino y no puedes configurarlo en un solo sitio.

### Inyección por constructor

```php
class SupportAgent extends Agent
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly User $user,
    ) {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function tools(): array
    {
        return [
            new SearchOrdersTool($this->orders),
            new GetOrderStatusTool($this->orders),
        ];
    }
}
```

Recuerda `parent::__construct()` (Sección 4.3) y que un constructor propio significa `new`, no `::make()`.

### El binding

```php
// AppServiceProvider::register()

$this->app->bind(SupportAgent::class, function ($app) {
    return new SupportAgent(
        orders: $app->make(OrderRepository::class),
        user: $app->make('auth')->user(),
    );
});
```

```php
class SupportController extends Controller
{
    public function __construct(
        private readonly SupportAgent $agent,
    ) {}

    public function ask(Request $request)
    {
        return $this->agent
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ->getContent();
    }
}
```

El controlador pide un agente y recibe uno, correctamente configurado para el usuario actual.

### Por qué merece la ceremonia

**Testabilidad.** Sustituye el binding en una prueba y el controlador habla con un doble. Este es el problema de la Sección 1.5: no puedes hacer asertos sobre la salida del modelo, así que la frontera que *sí* puedes testear es cómo el controlador maneja un agente, y la inyección de dependencias es lo que hace que esa frontera exista.

```php
$this->app->bind(SupportAgent::class, fn () => new FakeSupportAgent());

$this->post('/support/ask', ['message' => 'Where is my order?'])
     ->assertOk();
```

**Configuración por usuario.** El binding resuelve el usuario actual, así que la visibilidad de las herramientas (Sección 5.10) se calcula por petición sin que el controlador lo sepa.

**Un solo sitio que cambiar.** Proveedor, herramientas, historial, instrucciones: todo decidido en el binding.

**Se lee como Laravel.** Lo que importa para la adopción. Un agente que llega por inyección es un servicio como cualquier otro, y un equipo ya sabe razonar sobre servicios.

### Bindings con ámbito

Para entornos de ejecución de larga vida:

```php
$this->app->scoped(SupportAgent::class, function ($app) {
    return new SupportAgent(/* ... */);
});
```

`scoped()` da una instancia por petición y se reinicia entre peticiones bajo Octane.

::: {.callout .callout-warning}
[Nunca uses `singleton()` con un agente que lleve contexto de usuario]{.callout-title}

Bajo Octane esa instancia persiste entre peticiones, y el usuario B hereda las herramientas y el historial del usuario A. Es la misma clase de error que la semántica de copia de la facade previene en la Sección 17.5, salvo que aquí la responsabilidad es tuya y bajo PHP-FPM no se manifestará en absoluto.
:::

### Puntos clave

- Inyección por constructor y luego el binding en un service proveedor.
- Testabilidad, configuración por usuario, punto único de cambio.
- `scoped()` y no `singleton()` para cualquier cosa que lleve contexto de usuario.

## 18.2 EloquentChatHistory

### Publica y migra

```bash
php artisan vendor:publish --tag=neuron-migrations
php artisan migrate --path=/database/migrations/neuron
```

La migración aterriza en `database/migrations/neuron`, una subcarpeta, y por eso hace falta el flag `--path`. Ejecuta ambos comandos juntos; el segundo es fácil de olvidar y el fallo es silencioso.

### Úsala

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\EloquentChatHistory;
use NeuronAI\Laravel\Models\ChatMessage;

class MyAgent extends Agent
{
    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            thread_id: 'THREAD_ID',
            modelClass: ChatMessage::class,
            contextWindow: 100000
        );
    }
}
```

`NeuronAI\Laravel\Models\ChatMessage` viene con el paquete.

::: {.callout .callout-warning}
[Ortografía]{.callout-title}

La documentación escribe `ElquentChatHistory` en la prosa y ancla la sección en `#eloquentchathisotry`. La clase es `EloquentChatHistory`. Apéndice A, punto 42: inofensivo una vez que lo sabes, y veinte minutos perdidos si estás buscando la versión mal escrita.
:::

### Hacer real `thread_id`

`'THREAD_ID'` es un marcador de posición. En la práctica es el límite de aislamiento, y equivocarse es una fuga de datos:

```php
class SupportAgent extends Agent
{
    public function __construct(
        private readonly string $threadId,
    ) {
        parent::__construct();
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            thread_id: $this->threadId,
            modelClass: ChatMessage::class,
            contextWindow: ProviderContext::window(),
        );
    }
}
```

```php
$this->app->bind(SupportAgent::class, function ($app) {
    $conversation = $app->make(ConversationResolver::class)->current();

    return new SupportAgent(threadId: "conv:{$conversation->id}");
});
```

**Nunca derives el ID de hilo de la entrada del usuario.** Un parámetro de petición que se convierte en ID de hilo significa que cualquiera puede leer la conversación de cualquiera cambiando un número. Derívalo en el servidor a partir de un recurso autenticado y autorizado.

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
contextWindow: config('neuron.context_windows.' . config('neuron.default'), 29_000),
```

Cambia de proveedor por entorno y el recortador lo sigue. Escribe 100.000 a fuego y quien ejecute Ollama en local chocará con errores de contexto que en producción no aparecen nunca.

### Extender el modelo

El `ChatMessage` del paquete es un punto de partida. Una aplicación real normalmente quiere:

- Una clave externa hacia `users`
- Borrado lógico para la política de retención
- Un índice sobre `thread_id` más una marca de tiempo
- Una columna de inquilino

Extiende el modelo y pasa tu clase como `modelClass`. Aquí es también donde vive el RGPD: las conversaciones contienen lo que sea que los usuarios hayan escrito, lo que en un contexto de soporte significa datos personales. El borrado, la exportación y la retención son requisitos de producto, no ocurrencias tardías: la advertencia sobre registros de la Sección 3.7, hecha concreta.

### Puntos clave

- Publica y migra con `--path=/database/migrations/neuron`.
- `thread_id` es el límite de aislamiento: derívalo en el servidor, nunca de la entrada.
- Deduce `contextWindow` del proveedor configurado.
- Extiende `ChatMessage` para claves externas, multiinquilino y retención.

## 18.3 Aislamiento multi-tenant

### Los cuatro puntos de fuga

Un sistema agéntico en una aplicación multi-tenant tiene cuatro sitios por donde los datos de los inquilinos pueden cruzarse:

1. **Historial de chat** — `thread_id`
2. **Almacén vectorial** — filtros de metadatos (Sección 12.6)
3. **Herramientas** — los datos que consultan
4. **Persistencia de flujos de trabajo** — el ID de flujo de trabajo

Falla en uno solo y tienes una brecha. Ten la lista en un sitio donde la veas durante la revisión de código.

### Un agente consciente del inquilino

```php
namespace App\Neuron\Agents;

use App\Models\Tenant;
use NeuronAI\Agent\Agent;
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\EloquentChatHistory;
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Models\ChatMessage;
use NeuronAI\Providers\AIProviderInterface;

class TenantSupportAgent extends Agent
{
    public function __construct(
        private readonly Tenant $tenant,
        private readonly int $conversationId,
    ) {
        parent::__construct();
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            thread_id: "t{$this->tenant->id}:c{$this->conversationId}",
            modelClass: ChatMessage::class,
            contextWindow: config('neuron.context_window'),
        );
    }

    protected function tools(): array
    {
        return [
            // The tool receives the tenant — it cannot query outside it
            new SearchOrdersTool($this->tenant),
        ];
    }
}
```

### El principio

**Delimita en la construcción, no en el momento de la consulta.**

La herramienta recibe un `Tenant` y construye sus consultas a partir de él. No existe un camino de código en el que una herramienta consulte sin ámbito de inquilino, porque no tiene forma de hacerlo.

Compara con la alternativa: una herramienta que lee el inquilino actual de una variable global o de una facade dentro de `__invoke()`. Funciona hasta que algo se ejecuta fuera de una petición: un trabajo en cola, un comando programado, un flujo de trabajo reanudado. Entonces la global está vacía o, peor, contiene el inquilino equivocado.

**Los sistemas agénticos se ejecutan fuera del ciclo de petición mucho más a menudo que el código de aplicación normal.** Procesos de cola (Sección 16.4), flujos de trabajo reanudados (Sección 15.4), ingesta programada (Capítulo 20). El contexto de inquilino ambiental no es fiable en los tres casos. Pásalo explícitamente.

Ese argumento se generaliza mucho más allá de NeuronAI.

### IDs de flujo de trabajo

```php
$workflowId = "t{$tenant->id}:refund:{$order->id}";
```

Con prefijo de inquilino, para que un flujo de trabajo reanudado no pueda confundirse con el de otro inquilino y para que puedas consultar las interrupciones pendientes por inquilino.

### Testear el aislamiento

Merece escribirse como prueba de verdad:

```php
public function test_tenant_a_cannot_see_tenant_b_conversation(): void
{
    $agentA = new TenantSupportAgent($tenantA, $conversationId);
    $agentA->chat(new UserMessage('My secret code is ALPHA'));

    $agentB = new TenantSupportAgent($tenantB, $conversationId);
    $reply = $agentB->chat(new UserMessage('What is my secret code?'))->getMessage();

    $this->assertStringNotContainsString('ALPHA', $reply->getContent());
}
```

Fíjate en el montaje deliberadamente hostil: el *mismo* ID de conversación para ambos inquilinos. Si falta el prefijo de inquilino, esta prueba falla, que es exactamente lo que quieres que cace.

### Puntos clave

- Cuatro puntos de fuga: historial, almacén vectorial, herramientas, persistencia de flujos de trabajo.
- Delimita en la construcción; no leas contexto ambiental dentro de las herramientas.
- El código agéntico se ejecuta a menudo fuera del ciclo de petición: allí las globales no son fiables.
- Escribe una prueba de aislamiento con un identificador que colisione.

## 18.4 Persistencia de flujos de trabajo con Eloquent

### El montaje

```php
use NeuronAI\Laravel\Models\WorkflowInterrupt;
use NeuronAI\Workflow\Persistence\EloquentPersistence;

$workflow = new WorkflowAgent(
    persistence: new EloquentPersistence(WorkflowInterrupt::class)
);
```

El paquete incluye el modelo `WorkflowInterrupt`; la migración viene con `--tag=neuron-migrations` junto a la tabla del historial de chat.

::: {.callout .callout-warning}
[Falta `new` en el README]{.callout-title}

El ejemplo publicado dice `$workflow = WorkflowAgent(persistence: ...)`. Una errata, pero de las que producen un confuso error de «función no definida» en lugar de algo que apunte a la causa. Apéndice A, punto 41.
:::

### Por qué Eloquent en lugar de archivos

La Sección 15.4 ofrecía `FilePersistence` y `DatabasePersistence`. En Laravel, la persistencia con Eloquent te da:

**Seguridad multiservidor.** Cualquier proceso puede reanudar cualquier flujo de trabajo. La persistencia en archivo sobre disco local significa que la reanudación debe caer en la misma máquina, cosa que detrás de un balanceador de carga es un lanzamiento de moneda.

**Consultabilidad.** Las aprobaciones pendientes se convierten en una lista que puedes renderizar:

```php
$pending = WorkflowInterrupt::query()
    ->where('updated_at', '<', now()->subHours(24))
    ->get();
```

Informes de aprobaciones estancadas, paneles por inquilino, trabajos de escalado: todo Eloquent corriente.

**Integración transaccional.** La interrupción se escribe en la misma base de datos que tus datos de dominio, así que una reanudación puede ser atómica con el registro de negocio al que afecta.

**Copias de seguridad.** Los flujos de trabajo en vuelo se respaldan con todo lo demás, en lugar de vivir en un directorio que nadie se acuerda de incluir.

### La pantalla de aprobaciones pendientes

El patrón que esto desbloquea, y el que construye el Capítulo 22:

```php
class ApprovalsController extends Controller
{
    public function index(Request $request)
    {
        $pending = WorkflowInterrupt::query()
            ->where('tenant_id', $request->user()->tenant_id)
            ->latest()
            ->paginate();

        return view('approvals.index', compact('pending'));
    }
}
```

Como las interrupciones son filas, «la IA está esperando a un humano» se convierte en una página de índice corriente con autorización corriente. Ese es el momento en que el humano en el circuito deja de ser una funcionalidad exótica de IA y se convierte en desarrollo de aplicaciones normal, que es precisamente lo que hace el patrón desplegable.

### Recordatorios operativos de la Sección 15.4

Las cuatro preguntas siguen aplicando, ahora con respuestas de Laravel:

- **Notificación** → envía una `Notification` en el bloque catch
- **Tiempo de espera** → un comando programado sobre `updated_at`
- **Doble reanudación** → `lockForUpdate()` y una columna de estado
- **Compatibilidad con despliegues** → mantén las peticiones de interrupción pequeñas y planas; la carga serializada contiene tus clases

### Puntos clave

- `EloquentPersistence(WorkflowInterrupt::class)` con el modelo incluido.
- Seguro en multiservidor, consultable, transaccional, respaldado.
- Las aprobaciones pendientes se convierten en una página de índice corriente.
- Las cuatro preguntas operativas reciben respuestas corrientes de Laravel.

## Laboratorio 12 — Chat persistente multihilo

**Cubre:** bindings del contenedor, `EloquentChatHistory`, aislamiento de hilos, ventanas de contexto.

### Objetivo

Un usuario autenticado puede mantener varias conversaciones independientes con el mismo agente, cada una persistida, cada una aislada, cada una reanudable tras un despliegue completo.

### Requisitos

1. **Una tabla `conversations`** propiedad de los usuarios, con un título y marcas de tiempo. Un usuario puede tener muchas.
2. **El agente se resuelve desde el contenedor**, con el binding llevando la conversación actual, nunca construido en un controlador.
3. **El ID de hilo se deriva en el servidor** del usuario autenticado y del registro de conversación, nunca de un parámetro de petición. Demuéstralo: intenta leer la conversación de otro usuario por ID y obtén un 403 de tu policy, no una respuesta del agente.
4. **La ventana de contexto viene de la configuración**, indexada por el proveedor configurado, como en la Sección 18.2.
5. **Extiende `ChatMessage`** con una clave externa a `conversations` y un borrado lógico.

### Criterios de aceptación

- Dos conversaciones de un mismo usuario no ven los mensajes de la otra.
- Dos usuarios con IDs de conversación consecutivos no pueden alcanzar los hilos del otro; verifícalo con una prueba de autorización, no a ojo.
- Reiniciar el servidor de aplicación no pierde nada.
- Cambiar `NEURON_AI_PROVIDER` de `anthropic` a `ollama` cambia la ventana de contexto del recortador sin tocar el código. Registra el valor configurado para demostrarlo.
- Borrar una conversación hace el borrado lógico de sus mensajes, y el agente deja de verlos.

### La parte interesante

Escribe la prueba de aislamiento de la Sección 18.3 con un **ID de conversación que colisione entre dos inquilinos o dos usuarios**. Es la prueba que caza el prefijo ausente, y es el que la gente se salta porque el camino feliz ya funcionaba.

### Ir más allá

Añade un punto de conexión `/conversations/{id}/export` que devuelva la transcripción completa como JSON. Ya has satisfecho el requisito de exportación del RGPD, y descubrirás de inmediato si tu modelo de mensajes lleva suficiente contexto como para ser exportable: la mayoría de los primeros intentos no lo lleva.
