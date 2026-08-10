# Capítulo 21 — Streaming hacia el frontend

## 21.1 Server-Sent Events en Laravel

### Por qué SSE en lugar de WebSockets

Para las respuestas de un agente el tráfico es unidireccional: el servidor envía, el navegador recibe. SSE te da eso sobre HTTP corriente, con reconexión automática integrada en el navegador y sin infraestructura extra.

Los WebSockets son la elección correcta cuando el navegador también necesita empujar, cosa que en una interfaz de chat no ocurre, porque el mensaje siguiente es una petición nueva.

### El controlador

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Neuron\Agents\SupportAgent;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\UserMessage;
use Symfony\Component\HttpFoundation\StreamedResponse;

class ChatStreamController extends Controller
{
    public function __construct(
        private readonly SupportAgent $agent,
    ) {}

    public function __invoke(Request $request): StreamedResponse
    {
        $validated = $request->validate([
            'message' => ['required', 'string', 'max:4000'],
        ]);

        return response()->stream(function () use ($validated) {
            $handler = $this->agent->stream(new UserMessage($validated['message']));

            foreach ($handler->events() as $chunk) {
                echo 'data: ' . \json_encode([
                    'type'    => \class_basename($chunk),
                    'content' => $chunk->content ?? null,
                ]) . "\n\n";

                if (\ob_get_level() > 0) {
                    \ob_flush();
                }
                \flush();
            }

            echo "event: done\ndata: {}\n\n";
            \flush();
        }, 200, [
            'Content-Type'      => 'text/event-stream',
            'Cache-Control'     => 'no-cache, no-transform',
            'X-Accel-Buffering' => 'no',
            'Connection'        => 'keep-alive',
        ]);
    }
}
```

### Las cuatro cabeceras, cada una con su trabajo

**`Content-Type: text/event-stream`** — le dice al navegador que esto es SSE.

**`Cache-Control: no-cache, no-transform`** — `no-transform` importa: algunos proxies comprimen o reescriben respuestas, lo que rompe las fronteras de los frames.

**`X-Accel-Buffering: no`** — específica de nginx, y la que te ahorra un día. Sin ella, nginx bufferiza la respuesta y la entrega de golpe, momento en el que tienes toda la complejidad del streaming y ninguno de sus beneficios.

**`Connection: keep-alive`** — mantén abierta la conexión.

### El formato de los frames SSE

```
data: {"type":"TextChunk","content":"Hello"}\n\n
```

Dos saltos de línea terminan un frame. Falla uno y el navegador espera eternamente un frame que nunca se completa: un fallo que parece «el streaming no funciona» y es un carácter.

### El frontend

```javascript
const source = new EventSource('/chat/stream?message=' + encodeURIComponent(text));

source.onmessage = (e) => {
    const chunk = JSON.parse(e.data);

    if (chunk.type === 'TextChunk') {
        output.textContent += chunk.content;
    }
};

source.addEventListener('done', () => source.close());

source.onerror = () => source.close();
```

**`EventSource` solo hace GET.** Para un cuerpo POST o usas `fetch()` con un lector de `ReadableStream`, o aceptas el mensaje como parámetro de consulta, lo que limita la longitud del mensaje y mete contenido de usuario en los logs de acceso. Para cualquier cosa real, usa `fetch`.

### Puntos clave

- SSE encaja con la salida de un agente: unidireccional, HTTP puro, reconexión automática.
- Cuatro cabeceras; `X-Accel-Buffering: no` es la que te ahorra un día.
- Los frames terminan con dos saltos de línea.
- `EventSource` es solo GET: usa `fetch` con un lector de stream para POST.

## 21.2 El problema del buffering

### El síntoma

Implementaste el streaming correctamente. Funciona desde la CLI (Sección 7.3). En el navegador no aparece nada durante doce segundos y luego llega la respuesta entera de golpe.

Algo entre tu `echo` y el navegador está reteniendo los bytes.

### Las cuatro capas

**Capa 1 — Buffering de salida de PHP.**

```ini
; php.ini
output_buffering = Off
implicit_flush = On
```

O dentro de la callback del stream:

```php
while (\ob_get_level() > 0) {
    \ob_end_flush();
}
```

Laravel puede abrir búferes en middleware; el bucle cierra lo que haya en lugar de suponer que hay uno.

**Capa 2 — PHP-FPM y el servidor web.**

nginx bufferiza las respuestas FastCGI por defecto:

```nginx
location ~ \.php$ {
    fastcgi_pass   unix:/var/run/php/php8.3-fpm.sock;
    fastcgi_buffering off;
    fastcgi_read_timeout 300s;
    # ...
}
```

`fastcgi_buffering off` para toda la location, o la cabecera `X-Accel-Buffering: no` por respuesta. La cabecera es mejor: acota el cambio a los endpoints que lo necesitan, y el resto de tu sitio conserva el beneficio de rendimiento del buffering.

`fastcgi_read_timeout` también importa: los 60 segundos por defecto cortarán a mitad de stream una ejecución larga.

**Capa 3 — Proxy inverso.**

```nginx
location /chat/stream {
    proxy_pass http://app;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 300s;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
}
```

`proxy_http_version 1.1` más una cabecera `Connection` vacía mantiene viva la conexión hacia arriba.

**Capa 4 — CDN o WAF.**

Cloudflare, Fastly y similares pueden bufferizar. Cloudflare respeta `text/event-stream` en la mayoría de las configuraciones, pero verifícalo en lugar de suponerlo. Algunas reglas de WAF inspeccionan el cuerpo completo antes de reenviar, que es buffering con otro nombre.

### El procedimiento de diagnóstico

Biseca de dentro hacia fuera. Esto convierte una tarde frustrante en cinco minutos:

```bash
# 1. PHP alone. Does it stream?
php -r 'for($i=0;$i<5;$i++){echo "chunk $i\n";flush();sleep(1);}'

# 2. Through PHP-FPM and the web server, bypassing any proxy
curl -N http://127.0.0.1:8080/chat/stream

# 3. Through the full public stack
curl -N https://app.example.com/chat/stream
```

`curl -N` desactiva el buffering del propio curl. El primer paso que no consiga hacer streaming es tu culpable, y habrás reducido cuatro capas a una sin tocar un archivo de configuración.

### La propia advertencia del framework

La documentación de AG-UI lo dice directamente: envía las cabeceras del protocolo y haz flush después de cada línea, o el stream puede quedarse atascado en los búferes de salida de PHP o en los proxies.

Avisan de ello porque le pasa a todo el mundo.

### Puntos clave

- Cuatro capas de buffering: PHP, FPM/servidor web, proxy, CDN.
- Prefiere la cabecera `X-Accel-Buffering` a un `fastcgi_buffering off` global.
- Sube los tiempos de espera de lectura: los 60 s por defecto cortan las ejecuciones largas.
- Biseca con `curl -N` de dentro hacia fuera.

## 21.3 Streaming con Livewire

### El componente

```php
<?php

declare(strict_types=1);

namespace App\Livewire;

use App\Neuron\Agents\SupportAgent;
use Livewire\Component;
use NeuronAI\Chat\Messages\UserMessage;

class Chat extends Component
{
    public string $input = '';
    public string $answer = '';
    public ?string $activity = null;
    public array $history = [];

    public function send(SupportAgent $agent): void
    {
        $question = \trim($this->input);

        if ($question === '') {
            return;
        }

        $this->history[] = ['role' => 'user', 'content' => $question];
        $this->input     = '';
        $this->answer    = '';

        $handler = $agent->stream(new UserMessage($question));

        foreach ($handler->events() as $chunk) {
            if ($chunk instanceof ToolCallChunk) {
                $this->activity = $this->label($chunk->tool->getName());
                $this->stream(to: 'activity', content: $this->activity, replace: true);
                continue;
            }

            if ($chunk instanceof ToolResultChunk) {
                continue;
            }

            $this->answer .= $chunk->content;
            $this->stream(to: 'answer', content: $chunk->content);
        }

        $this->activity  = null;
        $this->history[] = ['role' => 'assistant', 'content' => $this->answer];
    }

    private function label(string $tool): string
    {
        return [
            'search_orders'     => 'Looking through your orders',
            'get_order_status'  => 'Checking that order',
            'request_refund'    => 'Preparing a refund request',
        ][$tool] ?? 'Working on it';
    }

    public function render()
    {
        return view('livewire.chat');
    }
}
```

### La vista

```blade
<div class="space-y-4">
    @foreach ($history as $message)
        <div @class(['text-right' => $message['role'] === 'user'])>
            {{ $message['content'] }}
        </div>
    @endforeach

    <div wire:stream="activity" class="text-sm text-gray-500 italic">
        {{ $activity }}
    </div>

    <div wire:stream="answer" class="whitespace-pre-wrap">
        {{ $answer }}
    </div>

    <form wire:submit="send" class="flex gap-2">
        <input wire:model="input" class="flex-1 border rounded px-3 py-2" autofocus>
        <button type="submit" class="px-4 py-2 bg-black text-white rounded">Send</button>
    </form>
</div>
```

### Por qué para la mayoría de los equipos Laravel este es el punto óptimo

`$this->stream(to: 'answer', content: $chunk->content)` empuja hacia `wire:stream="answer"` en la vista. Livewire gestiona el transporte SSE, la reconexión y las actualizaciones del DOM.

Sin `EventSource`, sin lector de `fetch`, sin parseo manual de frames. Para un equipo que no quiere mantener un frontend en JavaScript, esto son aproximadamente treinta líneas de PHP para un chat con streaming completo.

**Fíjate en `replace: true` para la línea de actividad** y en su ausencia para la respuesta. La actividad es un estado que sobrescribe; la respuesta se acumula. Invertirlos es el error de streaming más común en Livewire.

### La lista de permitidos de etiquetas, otra vez

`$this->label()` mapea nombres de tool a texto de cara al usuario, con `?? 'Working on it'` como respaldo.

La regla de la Sección 7.4: nunca muestres nombres ni resultados crudos de tools. Una tool nueva añadida el mes que viene degrada al mensaje genérico en lugar de filtrarle `internal_pricing_lookup` a un cliente. Las listas de permitidos fallan de forma segura, el mismo argumento que `only()` frente a `exclude()` en la Sección 5.8.

### La limitación que conviene conocer

El agente se ejecuta dentro de una petición de Livewire, así que se aplican el `max_execution_time` de PHP-FPM y los tiempos de espera del servidor web. Bien para una respuesta de chat de 15 segundos. Mal para un workflow multiagente de dos minutos: eso pertenece a una cola con otro transporte, que es la Sección 21.5.

### Puntos clave

- `$this->stream(to:, content:)` más `wire:stream`: Livewire gestiona el transporte.
- `replace: true` para el estado, omitido para el texto que se acumula.
- Mapea los nombres de tool mediante una lista de permitidos con un respaldo seguro.
- Acotado por los tiempos de espera de las peticiones web; las ejecuciones largas necesitan una cola.

## 21.4 Frontends SPA y adaptadores de protocolo

### El endpoint

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Neuron\Agents\SupportAgent;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use Symfony\Component\HttpFoundation\StreamedResponse;

class AgentUiController extends Controller
{
    public function __invoke(Request $request, SupportAgent $agent): StreamedResponse
    {
        $input = $request->validate([
            'threadId'           => ['required', 'string'],
            'runId'              => ['required', 'string'],
            'messages'           => ['required', 'array'],
            'messages.*.role'    => ['required', 'string'],
            'messages.*.content' => ['required', 'string'],
        ]);

        $messages = \collect($input['messages'])
            ->where('role', 'user')
            ->map(fn (array $m) => new UserMessage($m['content']))
            ->all();

        $adapter = new AGUIAdapter(
            threadId: $input['threadId'],
            runId: $input['runId'],
        );

        return response()->stream(function () use ($agent, $messages, $adapter) {
            foreach ($agent->stream($messages)->events($adapter) as $line) {
                echo $line;
                \flush();
            }
        }, 200, \array_merge($adapter->getHeaders(), [
            'X-Accel-Buffering' => 'no',
        ]));
    }
}
```

### Cuatro cosas que señalar

**`getHeaders()` aporta las cabeceras del protocolo.** El `X-Accel-Buffering` fúndelo tú: la solución de nginx de la Sección 21.2 no es asunto del adaptador.

**Devuelve `threadId` y `runId`.** La Sección 7.5 estableció que omitirlos hace que el adaptador se invente los suyos, lo que significa que el cliente no puede correlacionar el stream con la ejecución que pidió.

**Valida la carga.** Llega de un navegador. El array `messages` es entrada de usuario como cualquier otra.

**Cambia el adaptador, conserva todo lo demás.** `VercelAIAdapter` en lugar de `AGUIAdapter` y el mismo agente sirve otro protocolo de frontend. El argumento de las interfaces de la Sección 2.2, aplicado al lado de la salida.

### Las dos limitaciones, repetidas

De la Sección 7.5, porque un equipo que elige un frontend necesita saberlo antes de comprometerse:

**Solo tools del lado del servidor.** Las tools enganchadas a tu agente se ejecutan en tu servidor; al cliente se le informa mediante eventos `TOOL_CALL_*`. Las tools *definidas por el frontend* de AG-UI —declaradas en el campo `tools` de `RunAgentInput` y ejecutadas por el cliente— no se gestionan.

**Sin eventos de estado compartido.** El adaptador no emite `STATE_SNAPSHOT`, `STATE_DELTA` ni `MESSAGES_SNAPSHOT`, así que las funcionalidades de sincronización de estado del lado del cliente no están disponibles a través de él.

Si estás evaluando CopilotKit o un frontend AG-UI similar, comprueba si tu diseño depende de alguna de las dos. Mejor descubrirlo ahora que después de haber construido el frontend.

### Autenticación

Una SPA envía un token; Sanctum o Passport lo gestionan como siempre. La parte importante es que el *agente* se resuelva para el usuario autenticado:

```php
$this->app->bind(SupportAgent::class, function ($app) {
    return new SupportAgent(
        tenant: $app['auth']->user()->tenant,
        user:   $app['auth']->user(),
    );
});
```

La visibilidad de las tools, el historial de chat y los filtros de RAG se derivan todos de ese binding. El argumento de la Sección 18.1, y la razón de que el controlador se quede tan corto.

### Puntos clave

- `->events($adapter)` más `$adapter->getHeaders()`; el `X-Accel-Buffering` añádelo tú.
- Devuelve `threadId` y `runId` para que el cliente pueda correlacionar.
- Dos lagunas de AG-UI: sin tools definidas por el frontend, sin eventos de sincronización de estado.
- Resuelve el agente por usuario autenticado; todo lo demás se deriva de ahí.

## 21.5 Streaming desde una cola

Esta es la sección donde se encuentran las Partes IV y V.

### El problema

La Sección 16.4 estableció que las ejecuciones largas pertenecen a una cola. Pero un worker de cola no tiene conexión HTTP con el usuario, así que ¿cómo llega el progreso al navegador?

### La arquitectura

```
Navegador → POST /workflows   → envía el job → devuelve { workflowId }
Navegador → se suscribe a un canal privado para ese workflowId
Worker    → ejecuta el workflow → emite cada evento de progreso
Navegador → renderiza el progreso en vivo
Worker    → termina → emite la finalización
```

### El trabajo

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Events\WorkflowProgressed;
use App\Neuron\Workflows\ContentWorkflow;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Workflow\Exceptions\WorkflowInterrupt;
use NeuronAI\Workflow\Persistence\EloquentPersistence;
use NeuronAI\Laravel\Models\WorkflowInterrupt as WorkflowInterruptModel;

class RunContentWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $timeout = 600;
    public int $tries = 1;   // agent runs are expensive — do not blind-retry

    public function __construct(
        public readonly string $workflowId,
        public readonly int $tenantId,
        public readonly string $topic,
    ) {}

    public function handle(): void
    {
        $workflow = new ContentWorkflow(
            persistence: new EloquentPersistence(WorkflowInterruptModel::class),
            workflowId: $this->workflowId,
        );

        try {
            $handler = $workflow->init();

            foreach ($handler->events() as $event) {
                WorkflowProgressed::dispatch(
                    $this->workflowId,
                    $event->message ?? '',
                );
            }

            WorkflowCompleted::dispatch($this->workflowId, $handler->getResult());

        } catch (WorkflowInterrupt $interrupt) {
            PendingApproval::create([
                'workflow_id' => $interrupt->getWorkflowId(),
                'tenant_id'   => $this->tenantId,
                'request'     => \json_encode($interrupt->getRequest()),
                'status'      => 'pending',
            ]);

            WorkflowPaused::dispatch($this->workflowId);
        }
    }
}
```

### El evento de difusión

```php
class WorkflowProgressed implements ShouldBroadcastNow
{
    public function __construct(
        public readonly string $workflowId,
        public readonly string $message,
    ) {}

    public function broadcastOn(): PrivateChannel
    {
        return new PrivateChannel("workflows.{$this->workflowId}");
    }
}
```

**`ShouldBroadcastNow`, no `ShouldBroadcast`.** El segundo encola la difusión, lo que significa que tus actualizaciones de progreso hacen cola detrás del trabajo que las está produciendo. Con un solo worker eso es un interbloqueo a cámara lenta.

### La autorización del canal

```php
// routes/channels.php
Broadcast::channel('workflows.{workflowId}', function ($user, string $workflowId) {
    return WorkflowRun::where('id', $workflowId)
        ->where('tenant_id', $user->tenant_id)
        ->exists();
});
```

Sin esto, cualquiera que adivine un ID de workflow ve trabajar al agente de otra persona. Los cuatro puntos de fuga de la Sección 18.3 tienen un quinto pariente: el canal de difusión.

### El frontend

```javascript
Echo.private(`workflows.${workflowId}`)
    .listen('WorkflowProgressed', (e) => {
        progressList.append(`<li>${e.message}</li>`);
    })
    .listen('WorkflowPaused', () => {
        showMessage('Waiting for approval.');
    })
    .listen('WorkflowCompleted', (e) => {
        showResult(e.result);
    });
```

### Qué compone esto

Este único trabajo es gran parte del libro convergiendo:

- Streaming de workflows con `yield` (14.4)
- Interrupción y persistencia (15.4)
- Persistencia con Eloquent (18.4)
- Ejecución asíncrona (16.4)
- Adaptadores empujando hacia un transporte externo (7.5)
- `pcntl` disponible, así que las tools en paralelo funcionan (5.13)
- Inspector necesita aquí `autoFlush: true` (10.2)

Esa última es la mala configuración con más probabilidad de morderte: sin ella el worker acumula eventos de trace y no los envía nunca, porque no hay final de petición.

### Puntos clave

- Envía el trabajo, devuelve un ID, suscríbete a un canal privado, emite el progreso.
- `ShouldBroadcastNow`: las difusiones encoladas se bloquean detrás del trabajo que las produce.
- Autoriza el canal por tenant.
- `$tries = 1` en los trabajos de agentes; los reintentos a ciegas vuelven a gastar dinero.
- `autoFlush: true` para Inspector en los workers.

## 21.6 Desconexión y coste huérfano

### El problema que nadie menciona

Un usuario inicia una ejecución de 30 segundos. En el segundo cuatro cierra la pestaña.

El navegador ya no está. **El agente sigue ejecutándose.** Cada llamada al modelo que quede se factura. En un workflow multiagente eso es una cantidad sustancial de dinero gastado en una salida que nadie leerá jamás.

Con poco volumen es invisible. A escala es una partida de gasto.

### Detectarlo en una respuesta en streaming

```php
return response()->stream(function () use ($agent, $message) {
    $handler = $agent->stream(new UserMessage($message));

    foreach ($handler->events() as $chunk) {
        if (\connection_aborted()) {
            \Log::info('Client disconnected — stopping agent run');
            break;
        }

        echo 'data: ' . \json_encode(['content' => $chunk->content]) . "\n\n";
        \flush();
    }
}, 200, $headers);
```

`connection_aborted()` requiere que hayas escrito en la conexión: PHP solo detecta la tubería rota al intentar escribir. Como estás haciendo streaming, estás escribiendo, así que funciona. No funcionaría en un endpoint sin streaming.

**Una advertencia honesta:** salir del bucle detiene *tu* iteración. Una llamada al modelo ya en vuelo se completa y se factura. Estás limitando el daño, no eliminándolo.

### Para los workflows en cola

Un navegador desconectado no detiene a un worker, y no debería: el usuario puede volver, y el resultado vale la pena tenerlo. Pero hay casos en los que la cancelación es lo correcto:

```php
public function handle(): void
{
    foreach ($handler->events() as $event) {
        if (Cache::has("workflow:{$this->workflowId}:cancelled")) {
            $this->recordCancellation();
            return;
        }

        WorkflowProgressed::dispatch(/* ... */);
    }
}
```

```php
// A cancel endpoint
Cache::put("workflow:{$id}:cancelled", true, now()->addHour());
```

Cancelación explícita, no deducida de la desconexión.

### Guardas de presupuesto

El complemento, y lo que de verdad pone techo a la exposición:

```php
class BudgetMiddleware
{
    public function handle($request, Closure $next)
    {
        $spent = Cache::get("ai_spend:{$request->user()->id}:" . today()->toDateString(), 0);

        if ($spent > config('neuron.daily_user_budget')) {
            abort(429, 'Daily AI usage limit reached.');
        }

        return $next($request);
    }
}
```

Registra el uso real a partir de los recuentos de tokens de la respuesta después de cada ejecución. La Sección 1.3 decía que capturaras el uso desde el primer prototipo; para esto es para lo que se captura.

### Puntos clave

- Una pestaña cerrada no detiene a un agente: sigues pagando.
- `connection_aborted()` dentro del bucle del stream limita el daño.
- El trabajo en cola debe cancelarse explícitamente, no por deducción.
- Los presupuestos diarios por usuario ponen techo a la exposición; necesitan los recuentos de tokens que llevas registrando.

## Laboratorio 15 — La interfaz de chat con streaming

**Cubre:** SSE o Livewire, visualización de la actividad de las tools, buffering, desconexión.

### Objetivo

Una interfaz de chat que renderice la respuesta token a token y muestre qué está haciendo el agente mientras lo hace, con los nombres de las tools traducidos a un lenguaje que un cliente pueda leer.

### Requisitos

1. **Renderizado token a token.** Elige Livewire (Sección 21.3) o SSE con `fetch` (Sección 21.1). Livewire tiene menos piezas móviles; SSE te enseña más sobre el transporte.
2. **Una línea de actividad de tools** que sustituye en lugar de acumular, impulsada por una lista de permitidos de etiquetas con un respaldo seguro.
3. **Los resultados de las tools nunca llegan al navegador.** Solo las etiquetas.
4. **La cadena de buffering verificada** con `curl -N` en los tres puntos de la Sección 21.2: PHP solo, a través del servidor web, a través de todo el stack público. Anota qué capa, si alguna, necesitó configurarse.
5. **Gestión de la desconexión** con `connection_aborted()`.

### Criterios de aceptación

- El primer token visible llega muy por debajo del segundo con un modelo local. Mídelo; no lo supongas.
- Hacer una pregunta que dispare una tool muestra la etiqueta amigable y luego la respuesta.
- Añadir una tool nueva sin añadir su etiqueta muestra «Working on it», no el nombre interno de la tool. Pruébalo deliberadamente.
- Cerrar la pestaña a mitad de respuesta produce una línea de log y detiene el bucle.
- `curl -N` hace streaming a través de todo el stack, no solo en local.

### La parte que la gente se salta

El requisito cuatro. Es tentador cantar victoria cuando funciona en `artisan serve`, donde no hay nginx ni proxy. El primer despliegue es donde el streaming se rompe, y la bisección de la Sección 21.2 es la diferencia entre cinco minutos y una tarde.

Ejecuta los tres comandos `curl -N` contra tu entorno de staging real antes de dar este laboratorio por terminado.

### Ir más allá

Añade un botón de «parar» que aborte la petición desde el lado del navegador y confirma que `connection_aborted()` se dispara. Después mide lo que ahorró: ejecuta el mismo prompt hasta el final, anota el recuento de tokens y compáralo con una ejecución abortada. Ese número es el argumento para construir el botón.
