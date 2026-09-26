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
    public function ask(Request $request)
    {
        return SupportAgent::make()
            ->chat(new UserMessage($request->input('message')))
            ->getMessage()
            ?->getContent();
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

Recuerda `parent::__construct()` (Sección 4.3) y que un constructor propio significa `new`, no `::make()`. `make()` reenvía sus argumentos al constructor, así que una vez que el constructor es tuyo, `make(threadId: ...)` ya no llega al padre; la Sección 18.3 muestra cómo pasar el hilo tú mismo.

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
            ?->getContent();
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

Las migraciones aterrizan en `database/migrations/neuron`, una subcarpeta, y por eso hace falta el flag `--path`. Ejecuta ambos comandos juntos; el segundo es fácil de olvidar y el fallo es silencioso.

Son tres: la tabla `chat_messages`, una columna `archived_at` añadida a ella y la tabla `workflow_store` que usa la Sección 18.4. Si un proyecto existente publicó las migraciones del paquete con una versión anterior, vuelve a publicarlas: las versiones anteriores solo incluían la primera.

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
            modelClass: ChatMessage::class,
            contextWindow: 100000,
        );
    }
}
```

```php
MyAgent::make(threadId: 'THREAD_ID')->chat(new UserMessage('Hello'));
```

`NeuronAI\Laravel\Models\ChatMessage` viene con el paquete.

Fíjate en lo que el historial *no* recibe: el hilo. El hilo pertenece al agente. Lo declaras una vez, con `make(threadId: ...)`, y el agente lo vincula a cualquier historial que devuelva `chatHistory()` antes de la primera lectura. El historial se construye sin identidad, y el framework nunca se inventa una.

El hilo es más que una clave del historial. Es también el **ID del flujo de trabajo** del agente: el nombre bajo el que una ejecución pausada se persiste y más tarde se vuelve a encontrar (Sección 18.4). Un solo identificador, declarado en un solo sitio, da nombre tanto a la conversación como a la ejecución.

*Todavía puedes* vincular de antemano un historial —`new EloquentChatHistory(ChatMessage::class, 'THREAD_ID')`— y el agente adopta esa clave. Pero una clave que solo aparece cuando se ejecuta el hook llega después de que la ejecución haya empezado, demasiado tarde para que la ejecución pueda encontrarse por su hilo. Declara el hilo en el agente.

::: {.callout .callout-warning}
[Ortografía]{.callout-title}

La documentación escribe `ElquentChatHistory` en la prosa y ancla la sección en `#eloquentchathisotry`. La clase es `EloquentChatHistory`. Apéndice A, punto 42: inofensivo una vez que lo sabes, y veinte minutos perdidos si estás buscando la versión mal escrita.
:::

### Hacer real `thread_id`

`'THREAD_ID'` es un marcador de posición. En la práctica es el límite de aislamiento, y equivocarse es una fuga de datos:

```php
class SupportAgent extends Agent
{
    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(
            modelClass: ChatMessage::class,
            contextWindow: ProviderContext::window(),
        );
    }
}
```

```php
$this->app->bind(SupportAgent::class, function ($app) {
    $conversation = $app->make(ConversationResolver::class)->current();

    return SupportAgent::make(threadId: "conv:{$conversation->id}");
});
```

El agente no necesita constructor propio: `make(threadId:)` es la puerta de entrada del framework para la identidad, y el binding es el único sitio que la decide.

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
contextWindow: config('neuron.context_windows.' . config('neuron.provider.default'), 29_000),
```

Cambia de proveedor por entorno y el recortador lo sigue. Escribe 100.000 a fuego y quien ejecute Ollama en local chocará con errores de contexto que en producción no aparecen nunca.

### Extender el modelo

El `ChatMessage` del paquete es un punto de partida. Una aplicación real normalmente quiere:

- Una clave externa hacia `users`
- Borrado lógico para la política de retención
- Un índice sobre `thread_id` más una marca de tiempo
- Una columna de inquilino

Extiende el modelo y pasa tu clase como `modelClass`. Aquí es también donde vive el RGPD: las conversaciones contienen lo que sea que los usuarios hayan escrito, lo que en un contexto de soporte significa datos personales. El borrado, la exportación y la retención son requisitos de producto, no ocurrencias tardías: la advertencia sobre registros de la Sección 3.7, hecha concreta.

Un comportamiento cambia las cuentas de la retención. Cuando el historial recorta mensajes de la ventana de contexto, no los borra: los marca con `archived_at` y carga solo las filas no archivadas. El modelo ve el hilo recortado; tu tabla conserva la transcripción completa. Eso es bueno para la auditoría y para la exportación, pero significa que «el agente lo olvidó» y «ya no lo guardamos» son ahora afirmaciones distintas. Tu tarea de retención tiene que borrar explícitamente las filas archivadas.

### Puntos clave

- Publica y migra con `--path=/database/migrations/neuron`: tres migraciones.
- Declara el hilo en el agente (`make(threadId:)`); construye el historial sin él.
- El ID de hilo es el límite de aislamiento: derívalo en el servidor, nunca de la entrada.
- Deduce `contextWindow` del proveedor configurado.
- Extiende `ChatMessage` para claves externas, multiinquilino y retención; las filas recortadas se archivan, no se borran.

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
        int $conversationId,
    ) {
        // The thread is the conversation's identity - and the run's workflow ID
        parent::__construct(threadId: "t{$tenant->id}:c{$conversationId}");
    }

    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        // No thread here: the agent binds its own
        return new EloquentChatHistory(
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

Así es como un agente con constructor propio declara su hilo: se lo pasa al constructor del padre, no al historial. La clave compuesta se construye a partir de dos valores del servidor, nunca de nada que venga en la petición.

### El principio

**Delimita en la construcción, no en el momento de la consulta.**

La herramienta recibe un `Tenant` y construye sus consultas a partir de él. No existe un camino de código en el que una herramienta consulte sin ámbito de inquilino, porque no tiene forma de hacerlo.

Compara con la alternativa: una herramienta que lee el inquilino actual de una variable global o de una facade dentro de `__invoke()`. Funciona hasta que algo se ejecuta fuera de una petición: un trabajo en cola, un comando programado, un flujo de trabajo reanudado. Entonces la global está vacía o, peor, contiene el inquilino equivocado.

**Los sistemas agénticos se ejecutan fuera del ciclo de petición mucho más a menudo que el código de aplicación normal.** Procesos de cola (Sección 16.4), flujos de trabajo reanudados (Sección 15.4), ingesta programada (Capítulo 20). El contexto de inquilino ambiental no es fiable en los tres casos. Pásalo explícitamente.

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

Con prefijo de inquilino, para que un flujo de trabajo reanudado no pueda confundirse con el de otro inquilino, y con clave de negocio, para que una petición posterior que solo conoce el inquilino y el pedido reconstruya el flujo de trabajo y encuentre su ejecución pausada con una sola lectura. Un flujo de trabajo que no declara ningún ID recibe uno generado por el motor: se puede continuar, pero solo quien haya guardado la referencia.

### Testear el aislamiento

Merece escribirse como prueba de verdad:

```php
public function test_tenant_a_cannot_see_tenant_b_conversation(): void
{
    $agentA = new TenantSupportAgent($tenantA, $conversationId);
    $agentA->chat(new UserMessage('My secret code is ALPHA'));

    $agentB = new TenantSupportAgent($tenantB, $conversationId);
    $reply = $agentB->chat(new UserMessage('What is my secret code?'))->getMessage();

    $this->assertStringNotContainsString('ALPHA', (string) $reply?->getContent());
}
```

Fíjate en el montaje deliberadamente hostil: el *mismo* ID de conversación para ambos inquilinos. Si falta el prefijo de inquilino, esta prueba falla, que es exactamente lo que quieres que cace.

### Puntos clave

- Cuatro puntos de fuga: historial, almacén vectorial, herramientas, persistencia de flujos de trabajo; para un agente, el hilo cubre el primero y el último.
- Delimita en la construcción; no leas contexto ambiental dentro de las herramientas.
- Declara con `workflowId()` IDs de flujo de trabajo con clave de negocio y prefijo de inquilino.
- El código agéntico se ejecuta a menudo fuera del ciclo de petición: allí las globales no son fiables.
- Escribe una prueba de aislamiento con un identificador que colisione.

## 18.4 Persistencia de flujos de trabajo con Eloquent

### El montaje

```php
use NeuronAI\Laravel\Models\WorkflowStore;
use NeuronAI\Workflow\Persistence\EloquentPersistence;
use NeuronAI\Workflow\Persistence\PersistenceInterface;

class TenantSupportAgent extends Agent
{
    // ...

    protected function persistence(): PersistenceInterface
    {
        return new EloquentPersistence(WorkflowStore::class);
    }
}
```

`persistence()` es un hook como `provider()` y `chatHistory()`; `setPersistence()` es su gemelo setter, para un `Workflow` simple o un caso puntual. El paquete incluye el modelo `WorkflowStore`, y su migración viene con `--tag=neuron-migrations` junto a las tablas del historial de conversación. `EloquentPersistence` no recibe nada más que la clase del modelo: toma prestadas su tabla y su conexión.

Esa tabla, `workflow_store`, es toda la persistencia de NeuronAI: un único espacio clave-valor particionado. Cada registro de una ejecución —su arranque, su registro de control, los resultados de sus pasos— vive en la partición que lleva el nombre del **ID del flujo de trabajo**, que para un agente es el hilo. Eso es lo que permite a un punto de conexión de aprobación reconstruir `TenantSupportAgent` a partir solo del inquilino y la conversación y encontrar la ejecución pausada con una sola lectura. Cuando una ejecución termina limpiamente, su partición se barre; no se acumula nada.

::: {.callout .callout-warning}
[`workflow_store` no es una tabla de la aplicación]{.callout-title}

Los nombres de partición y las claves están codificados en hexadecimal y los valores son registros serializados del motor. No hay ningún `tenant_id` por el que filtrar ni nada pensado para leerse con un `where()`. Trata la tabla como el almacenamiento privado del motor: haz copia de seguridad, nunca la consultes. En MySQL además requiere el modo SQL estricto —el ajuste de conexión `'strict' => true`, el valor por defecto de Laravel—, y `EloquentPersistence` se niega a arrancar sin él antes que arriesgarse a registros truncados.
:::

### Por qué Eloquent en lugar de archivos

La Sección 15.4 ofrecía `FilePersistence` y `DatabasePersistence`. En Laravel, la persistencia con Eloquent te da:

**Seguridad multiservidor.** Cualquier proceso puede reanudar cualquier flujo de trabajo. La persistencia en archivo sobre disco local significa que la reanudación debe caer en la misma máquina, cosa que detrás de un balanceador de carga es un lanzamiento de moneda. El backend de archivos está pensado para un uso controlado de un solo proceso.

**Continuación atómica.** Cada escritura es un compare-and-write condicional dentro de una transacción en la conexión del modelo. Dos procesos que compiten por continuar la misma ejecución no pueden ganar ambos.

**Una sola conexión.** La ejecución vive en la base de datos que ya gestionas, en la conexión que usan tus modelos, sin una segunda credencial que administrar.

**Copias de seguridad.** Los flujos de trabajo en vuelo se respaldan con todo lo demás, en lugar de vivir en un directorio que nadie se acuerda de incluir.

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

La página de detalle le pregunta al propio agente qué está esperando. Reconstrúyelo para la conversación y lee `pendingApprovals()`: una acción por cada llamada a herramienta sujeta a aprobación, con el ID de la llamada, el nombre de la herramienta, los argumentos y el motivo que dio la herramienta para pedirla:

```php
foreach ($agent->pendingApprovals() as $action) {
    // $action->id, $action->name, $action->inputs, $action->reason
}
```

La misma información está también en el último mensaje del hilo en el historial de conversación, que es a partir de lo que renderiza un frontend (Capítulo 22).

Como las conversaciones en espera son filas de *tu* tabla, «la IA está esperando a un humano» se convierte en una página de índice corriente con autorización corriente. Ese es el momento en que el humano en el circuito deja de ser una funcionalidad exótica de IA y se convierte en desarrollo de aplicaciones normal, que es precisamente lo que hace el patrón desplegable.

### Recordatorios operativos de la Sección 15.4

Las cuatro preguntas siguen aplicando, ahora con respuestas de Laravel:

- **Notificación** → envía una `Notification` cuando el estado devuelto responde `isInterrupted()`; no hay ninguna excepción que capturar
- **Tiempo de espera** → un comando programado sobre `awaiting_approval_at` que cierra las ejecuciones estancadas con un rechazo, `submitApprovalDecisions([$callId => ['reject', 'Timed out']])->run()`: rechazar es la vía de cancelación
- **Doble reanudación** → la gestiona el motor: un segundo envío para una ejecución ya cerrada no encuentra ninguna ejecución persistida y lanza una excepción, y un nuevo `chat()` sobre un hilo que sigue esperando lanza `RunInFlightException`; bloquea la entrada en la interfaz hasta que se entregue la decisión
- **Compatibilidad con despliegues** → mantén las peticiones de interrupción pequeñas y planas; la carga serializada contiene tus clases. Las herramientas nunca se serializan, así que una herramienta que guarda un repositorio o un cliente HTTP no plantea problemas a la persistencia

### Puntos clave

- `EloquentPersistence(WorkflowStore::class)`, devuelto desde el hook `persistence()` del agente.
- Una sola tabla `workflow_store`, particionada por ID del flujo de trabajo: el hilo, para un agente. Haz copia de seguridad; nunca la consultes.
- Seguro en multiservidor, atómico, en tu conexión existente, respaldado.
- Registra las aprobaciones pendientes en tu propio modelo cuando `isInterrupted()`; lee los detalles con `pendingApprovals()`.
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
