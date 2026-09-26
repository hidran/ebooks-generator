# Capítulo 21 — Transmisión hacia el frontend

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

Los listados de Laravel de abajo viven dentro de una aplicación, pero las partes que no la necesitan son ejecutables en [`chapters/Ch21`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch21) del repositorio complementario: `sse-frames.php` imprime las tramas exactas que envía el punto de conexión de la Sección 21.1, `channel.php` imprime los sobres que publica un canal push en la Sección 21.5 y `disconnect.php` reproduce el comportamiento ante la desconexión de la Sección 21.6. Ninguno necesita un modelo.
:::

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
use Generator;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\ProtocolEvent;
use NeuronAI\Workflow\Streaming\SSEEncoder;
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
            $stream = $this->agent->stream(new UserMessage($validated['message']));

            // No adapter or channel attached: stream() returns a Generator of native chunks.
            \assert($stream instanceof Generator);

            foreach ($stream as $chunk) {
                if (! $chunk instanceof TextChunk) {
                    continue;   // tool calls and results stay on the server (Section 7.4)
                }

                echo SSEEncoder::frame(new ProtocolEvent('text', ['content' => $chunk->content]));

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

### Qué hace el bucle

`stream()` es en sí mismo el generador: itéralo directamente. Sin adaptador de transmisión ni canal enganchados, produce los objetos de fragmento nativos de NeuronAI, y `TextChunk` es el único tipo que este punto de conexión deja pasar. Todo lo demás (las llamadas a herramienta con sus argumentos, los resultados de las herramientas) se descarta en el servidor, que es la regla de la Sección 7.4 aplicada en la frontera HTTP.

`SSEEncoder::frame()` es el formato de tramas SSE del framework, y el único lugar donde se producen bytes. Un `ProtocolEvent` es un tipo más una carga serializable en JSON; el codificador lo escribe como una sola línea `data:`, y sustituye el UTF-8 no válido en lugar de hacer fallar la transmisión. La Sección 21.4 deja que un adaptador construya los eventos por ti; aquí, construir uno a mano mantiene explícita la lista de permitidos.

El evento `done` después del bucle no es decoración. Cuando una respuesta SSE termina, `EventSource` lo trata como una conexión caída y programa una reconexión, que, para este punto de conexión, volvería a hacer la pregunta. El evento explícito permite a la página distinguir una respuesta terminada de un fallo y cerrar antes de que eso ocurra.

### Las cuatro cabeceras, cada una con su trabajo

**`Content-Type: text/event-stream`** — le dice al navegador que esto es SSE.

**`Cache-Control: no-cache, no-transform`** — `no-transform` importa: algunos proxies comprimen o reescriben respuestas, lo que rompe las fronteras de las tramas.

**`X-Accel-Buffering: no`** — específica de nginx, y la que te ahorra un día. Sin ella, nginx bufferiza la respuesta y la entrega de golpe, momento en el que tienes toda la complejidad de la transmisión y ninguno de sus beneficios.

**`Connection: keep-alive`** — mantén abierta la conexión.

### El formato de las tramas SSE

```
data: {"type":"text","content":"Hello"}\n\n
```

Dos saltos de línea terminan una trama. Falla uno y el navegador espera eternamente una trama que nunca se completa: un fallo que parece «la transmisión no funciona» y es un carácter.

### El frontend

```javascript
const source = new EventSource('/chat/stream?message=' + encodeURIComponent(text));

source.onmessage = (e) => {
    const chunk = JSON.parse(e.data);

    if (chunk.type === 'text') {
        output.textContent += chunk.content;
    }
};

source.addEventListener('done', () => source.close());

source.onerror = () => source.close();
```

**`EventSource` solo hace GET.** Para un cuerpo POST o usas `fetch()` con un lector de `ReadableStream`, o aceptas el mensaje como parámetro de consulta, lo que limita la longitud del mensaje y mete contenido de usuario en los registros de acceso. Para cualquier cosa real, usa `fetch`.

### Puntos clave

- SSE encaja con la salida de un agente: unidireccional, HTTP puro, reconexión automática.
- Itera `stream()` directamente; reenvía solo el contenido de los `TextChunk`, en tramas construidas con `SSEEncoder::frame()`.
- Envía un evento `done` explícito, o `EventSource` se reconecta y vuelve a preguntar.
- Cuatro cabeceras; `X-Accel-Buffering: no` es la que te ahorra un día.
- Las tramas terminan con dos saltos de línea.
- `EventSource` es solo GET: usa `fetch` con un lector de transmisión para POST.

## 21.2 El problema del almacenamiento en búfer

### El síntoma

Implementaste la transmisión correctamente. Funciona desde la CLI (Sección 7.3). En el navegador no aparece nada durante doce segundos y luego llega la respuesta entera de golpe.

Algo entre tu `echo` y el navegador está reteniendo los bytes.

### Las cuatro capas

**Capa 1 — Almacenamiento en búfer de salida de PHP.**

```ini
; php.ini
output_buffering = Off
implicit_flush = On
```

O dentro de la callback de la transmisión:

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
    fastcgi_pass   unix:/var/run/php/php8.5-fpm.sock;
    fastcgi_buffering off;
    fastcgi_read_timeout 300s;
    # ...
}
```

`fastcgi_buffering off` para toda la location, o la cabecera `X-Accel-Buffering: no` por respuesta. La cabecera es mejor: acota el cambio a los puntos de conexión que lo necesitan, y el resto de tu sitio conserva el beneficio de rendimiento del almacenamiento en búfer.

`fastcgi_read_timeout` también importa: los 60 segundos por defecto cortarán a mitad de transmisión una ejecución larga.

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

Cloudflare, Fastly y similares pueden bufferizar. Cloudflare respeta `text/event-stream` en la mayoría de las configuraciones, pero verifícalo en lugar de suponerlo. Algunas reglas de WAF inspeccionan el cuerpo completo antes de reenviar, que es almacenamiento en búfer con otro nombre.

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

`curl -N` desactiva el almacenamiento en búfer del propio curl. El primer paso que no consiga transmitir es tu culpable, y habrás reducido cuatro capas a una sin tocar un archivo de configuración.

### La propia advertencia del framework

La propia guía de transmisión del framework lo dice directamente: envía las cabeceras del adaptador, construye la trama de cada evento con `SSEEncoder` y haz flush después de cada línea, o la transmisión puede quedarse atascada en los búferes de salida de PHP o en los proxies. Los adaptadores de interfaz integrados incluso ponen `X-Accel-Buffering: no` en su `getHeaders()`.

Avisan de ello porque le pasa a todo el mundo.

### Puntos clave

- Cuatro capas de almacenamiento en búfer: PHP, FPM/servidor web, proxy, CDN.
- Prefiere la cabecera `X-Accel-Buffering` a un `fastcgi_buffering off` global.
- Sube los tiempos de espera de lectura: los 60 s por defecto cortan las ejecuciones largas.
- Biseca con `curl -N` de dentro hacia fuera.

## 21.3 Transmisión con Livewire

### El componente

```php
<?php

declare(strict_types=1);

namespace App\Livewire;

use App\Neuron\Agents\SupportAgent;
use Generator;
use Livewire\Component;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
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

        $stream = $agent->stream(new UserMessage($question));
        \assert($stream instanceof Generator);

        foreach ($stream as $chunk) {
            if ($chunk instanceof ToolCallChunk) {
                $this->activity = $this->label($chunk->tool->getName());
                $this->stream(to: 'activity', content: $this->activity, replace: true);
                continue;
            }

            if (! $chunk instanceof TextChunk) {
                continue;   // tool results, reasoning: never rendered
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

Sin `EventSource`, sin lector de `fetch`, sin parseo manual de tramas. Para un equipo que no quiere mantener un frontend en JavaScript, esto son aproximadamente treinta líneas de PHP para un chat completo con transmisión.

**Fíjate en `replace: true` para la línea de actividad** y en su ausencia para la respuesta. La actividad es un estado que sobrescribe; la respuesta se acumula. Invertirlos es el error de transmisión más común en Livewire.

### La lista de permitidos de etiquetas, otra vez

`$this->label()` mapea nombres de herramienta a texto de cara al usuario, con `?? 'Working on it'` como respaldo. Y el bucle renderiza exactamente dos tipos de fragmento: un `ToolCallChunk` se convierte en una etiqueta, un `TextChunk` se convierte en texto de la respuesta, y todo lo demás (resultados de herramientas, razonamiento) lo descarta la comprobación `instanceof TextChunk` en lugar de una lista de cosas que excluir.

La regla de la Sección 7.4: nunca muestres nombres ni resultados crudos de herramientas. Una herramienta nueva añadida el mes que viene degrada al mensaje genérico en lugar de filtrarle `internal_pricing_lookup` a un cliente. Las listas de permitidos fallan de forma segura, el mismo argumento que `only()` frente a `exclude()` en la Sección 5.8.

### La limitación que conviene conocer

El agente se ejecuta dentro de una petición de Livewire, así que se aplican el `max_execution_time` de PHP-FPM y los tiempos de espera del servidor web. Bien para una respuesta de chat de 15 segundos. Mal para un flujo de trabajo multiagente de dos minutos: eso pertenece a una cola con otro transporte, que es la Sección 21.5.

### Puntos clave

- `$this->stream(to:, content:)` más `wire:stream`: Livewire gestiona el transporte.
- `replace: true` para el estado, omitido para el texto que se acumula.
- Mapea los nombres de herramienta mediante una lista de permitidos con un respaldo seguro.
- Acotado por los tiempos de espera de las peticiones web; las ejecuciones largas necesitan una cola.

## 21.4 Frontends SPA y adaptadores de protocolo

### El punto de conexión

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Neuron\SupportAgentFactory;
use Generator;
use Illuminate\Http\Request;
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Agent\AgentState;
use NeuronAI\Agent\Frontend\AGUIInputTranslator;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\ProtocolEvent;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;

class AgentUiController extends Controller
{
    public function __invoke(Request $request, SupportAgentFactory $agents): StreamedResponse
    {
        $input = $request->validate([
            'threadId'           => ['required', 'string'],
            'runId'              => ['nullable', 'string'],
            'messages'           => ['required', 'array', 'min:1'],
            'messages.*.id'      => ['required', 'string'],
            'messages.*.role'    => ['required', 'string'],
            'messages.*.content' => ['nullable', 'string'],
            'state'              => ['nullable', 'array'],
            'resume'             => ['nullable', 'array'],
        ]);

        // The client names the thread; the server decides whether this user may use it.
        $conversation = $request->user()->conversations()
            ->where('thread_id', $input['threadId'])
            ->firstOrFail();

        $last = \array_last($input['messages']);

        $adapter = new AGUIAdapter(
            threadId: $conversation->thread_id,
            runId: $input['runId'] ?? null,
            messages: $input['messages'],
            state: $input['state'] ?? [],
        );

        $agent = $agents->forThread($conversation->thread_id)->setStreamAdapter($adapter);

        // Answers to a paused run (approvals, browser tool results) continue it;
        // a trailing user message starts a new turn. Nothing else is accepted.
        $continuation = ($input['resume'] ?? []) !== [] || $last['role'] === 'tool';
        abort_unless($continuation || $last['role'] === 'user', 422, 'Nothing to answer and no new message.');

        /** @var Generator<int, ProtocolEvent, mixed, AgentState> $stream */
        $stream = $continuation
            ? $agent->submitInputs($request->all(), new AGUIInputTranslator())->events()
            : $agent->stream(new UserMessage((string) $last['content']));

        return response()->stream(function () use ($stream) {
            foreach (SSEEncoder::encode($stream) as $line) {
                echo $line;
                \flush();
            }
        }, 200, $adapter->getHeaders());
    }
}
```

### Seis cosas que señalar

**El adaptador da la forma, el codificador hace las tramas.** `setStreamAdapter()` hace que `stream()` produzca objetos `ProtocolEvent` (`RUN_STARTED`, `TEXT_MESSAGE_CONTENT` y el resto) en lugar de fragmentos nativos. `SSEEncoder::encode()` convierte cada uno en una línea `data:` y reenvía el valor de retorno del generador, así que el `AgentState` final sigue ahí si lo quieres. El adaptador no sabe nada de bytes, y eso es lo que permite que el mismo adaptador alimente un canal de difusión en la Sección 21.5.

**`getHeaders()` aporta las cabeceras del protocolo, incluida `X-Accel-Buffering: no`.** Los adaptadores integrados ya llevan consigo la solución de nginx de la Sección 21.2, así que no hay nada que fusionar.

**Al agente solo le llega el último mensaje del usuario.** Un cliente AG-UI envía la conversación entera en cada turno. El agente ya tiene esa conversación en su historial de conversación duradero, indexado por hilo: pasarle la copia del cliente hace que cada mensaje anterior se guarde dos veces. Los `messages` del cliente van en cambio al adaptador, que los usa para mantener completa la instantánea de mensajes del protocolo.

**El hilo es la identidad del agente: autorízalo.** El `threadId` de AG-UI se convierte en el hilo del agente, y el hilo *es* el ID del flujo de trabajo del agente: la clave bajo la que se archivan su historial y cualquier ejecución suspendida. Eso lo convierte exactamente en el valor que la Sección 18.2 decía que nunca se tomara de la entrada del usuario. La búsqueda a través de `$request->user()->conversations()` es lo que convierte una cadena proporcionada por el cliente en un hilo que pertenece a este usuario. Devuelve también `runId`: es el identificador por petición del cliente, y sin él el cliente no puede correlacionar la transmisión con la ejecución que pidió.

**La forma de la petición decide entre turno nuevo y continuación.** Un mensaje de usuario al final es un turno nuevo, y va a `stream()`. Un array `resume` (el cliente respondiendo a interrupciones) o un mensaje de herramienta al final es la continuación de una ejecución en pausa, y va a `submitInputs()` con el traductor del protocolo, que la valida contra la petición persistida antes de ejecutar nada y lanza `InputTranslationException` ante cualquier cosa que no coincida. Fíjate en que la continuación llama a `events()`, no a `stream()`: `stream()` siempre empieza un turno nuevo. Una continuación no válida debe ser una respuesta de error, nunca un repliegue a un turno nuevo.

**Cambia el adaptador, conserva todo lo demás.** `VercelAIAdapter` en lugar de `AGUIAdapter` y el mismo agente sirve otro protocolo de frontend, con `VercelAIInputTranslator` para sus continuaciones. El argumento de las interfaces de la Sección 2.2, aplicado al lado de la salida.

### Cuando la ejecución se pausa

Si una herramienta del turno necesita aprobación (Capítulo 22), la transmisión no termina como una completada. El terminal `interrupt()` del adaptador sustituye a `end()`: en AG-UI, `RUN_FINISHED` lleva `outcome: {type: "interrupt", interrupts: [...]}`, una interrupción `confirmation` por cada llamada a herramienta pendiente, con el ID de la llamada a herramienta como su `id`; en Vercel, una parte `tool-approval-request` por llamada.

Un frontend que trate cada `RUN_FINISHED` como «la respuesta está completa» mostrará una ejecución en pausa como si hubiera terminado. Comprueba `outcome.type` antes de cerrar el turno. El cliente responde con un array `resume` en su siguiente petición, que el punto de conexión de arriba dirige a `submitInputs()`. La Sección 22.5 cubre el lado de la aprobación para clientes que no hablan AG-UI.

### Qué cubre el adaptador y qué no

De la Sección 7.5, porque un equipo que elige un frontend necesita saberlo antes de comprometerse:

**Instantáneas en la pausa, no deltas.** El adaptador emite `STATE_SNAPSHOT` y `MESSAGES_SNAPSHOT` antes de terminar una ejecución interrumpida, inicializadas a partir del `state` y los `messages` que pasaste a su constructor. No emite `STATE_DELTA`. Si tu diseño depende de una sincronización fina del estado compartido mientras el agente se ejecuta, el adaptador no te la va a dar.

**Las herramientas definidas por el frontend necesitan un paso más.** Los clientes AG-UI pueden declarar herramientas en `RunAgentInput.tools` para que las ejecute el navegador. NeuronAI las admite como herramientas diferidas: la ejecución se suspende cuando el modelo llama a una, el adaptador publica la llamada y el cliente devuelve el resultado como un mensaje de herramienta al final, que es la rama de continuación de arriba. Lo que el punto de conexión todavía no hace es enganchar esas herramientas al agente. `AGUIInputTranslator::tools($payload)` las construye a partir de la petición; añádelas en la factoría, después de rechazar cualquier nombre que tape una de tus herramientas del lado del servidor, y aplícales tu política de aprobación como a cualquier otra herramienta.

Si estás evaluando CopilotKit o un frontend AG-UI similar, contrasta estos dos puntos con tu diseño ahora y no después de haber construido el frontend.

### Eventos de progreso desde tus propios nodos

Los fragmentos no son lo único que puede llevar una transmisión. Un nodo (en tu propio flujo de trabajo, o en un nodo personalizado de un agente) puede hacer `yield` de un evento de progreso portable, y cada adaptador lo traduce al vocabulario de su protocolo:

```php
use NeuronAI\Agent\Adapters\Events\ActivityStreamEvent;
use NeuronAI\Agent\Adapters\Events\StepStartedStreamEvent;

yield new StepStartedStreamEvent('checking-stock');

yield new ActivityStreamEvent(
    id: "stock-{$orderId}",
    type: 'stock-check',
    data: ['checked' => 3, 'total' => 5],
);
```

En AG-UI se convierten en `STEP_STARTED` y `ACTIVITY_SNAPSHOT`: una actividad con el mismo `id` sustituye a la anterior, que es exactamente la semántica de barra de progreso que quieres. `CustomStreamEvent($name, $value)` se convierte en el evento `CUSTOM` de AG-UI. En Vercel los tres viajan como partes `data-*` transitorias, que llegan a la interfaz sin entrar en el historial de mensajes.

Si tus nodos ya producen objetos de dominio, mapéalos en lugar de reescribir los nodos:

```php
$adapter->mapEvent(
    StockChecked::class,
    static fn (StockChecked $event): ?ActivityStreamEvent => new ActivityStreamEvent(
        id: "stock-{$event->orderId}",
        type: 'stock-check',
        data: ['checked' => $event->checked, 'total' => $event->total],
    ),
);
```

La coincidencia es por clase exacta, y devolver `null` suprime el evento, lo que convierte a `mapEvent()` en el lugar donde mantener un evento interno fuera del cable. El adaptador sigue siendo el único dueño del vocabulario del protocolo; tus nodos nunca importan un tipo de AG-UI.

Una regla para todo ello: **los eventos transmitidos son en vivo y efímeros.** No se persisten, y una ejecución reanudada no los vuelve a reproducir. Nunca hagas que la corrección dependa de que el navegador haya recibido uno.

### Autenticación

Una SPA envía un token; Sanctum o Passport lo gestionan como siempre. La parte importante es que el *agente* se construya para el usuario autenticado y el hilo autorizado. Como el hilo forma parte de la identidad del agente (va al constructor, no a un setter), una factoría se lee mejor que un binding del contenedor:

```php
class SupportAgentFactory
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly AuthManager $auth,
    ) {}

    public function forThread(string $threadId): SupportAgent
    {
        return new SupportAgent(
            orders: $this->orders,
            user: $this->auth->user(),
            threadId: $threadId,
        );
    }
}
```

```php
class SupportAgent extends Agent
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly User $user,
        string $threadId,
    ) {
        parent::__construct(threadId: $threadId);
    }

    // provider(), tools(), chatHistory() as in Chapter 18
}
```

La visibilidad de las herramientas, el historial de conversación y los filtros de RAG se derivan todos de esas dos entradas. El argumento de la Sección 18.1, y la razón de que el controlador se quede tan corto.

### Puntos clave

- `setStreamAdapter()` hace que `stream()` produzca `ProtocolEvent`; `SSEEncoder::encode()` los convierte en tramas; `getHeaders()` ya incluye `X-Accel-Buffering`.
- Envía al agente solo el último mensaje del usuario; el historial del cliente inicializa el adaptador.
- Un array `resume` o un mensaje de herramienta al final es una continuación: `submitInputs()` con el traductor del protocolo y luego `events()`.
- El `threadId` de AG-UI se convierte en el ID del flujo de trabajo del agente: resuélvelo a través del usuario, nunca te fíes del valor en bruto.
- Una ejecución en pausa termina con un resultado de interrupción, no con un final normal; compruébalo antes de cerrar el turno.
- Los nodos producen eventos de progreso portables; `mapEvent()` traduce o suprime los tuyos.

## 21.5 Transmisión desde una cola

Esta es la sección donde se encuentran las Partes IV y V.

### El problema

La Sección 16.4 estableció que las ejecuciones largas pertenecen a una cola. Pero un proceso de cola no tiene conexión HTTP con el usuario, así que ¿cómo llega el progreso al navegador?

La respuesta es un **canal de transmisión**. Todo lo visto hasta ahora es transmisión *pull*: el código que itera el generador es el código que sostiene la respuesta. Un canal es la mitad *push*. Engancha uno a un flujo de trabajo o a un agente, junto con un adaptador de transmisión, y la ejecución entrega al canal cada evento de protocolo a medida que se produce (a Pusher, a Redis, a un websocket) mientras el proceso se limita a llamar a `run()`.

### La arquitectura

```
Navegador → POST /workflows             → crea el registro de la ejecución, devuelve { workflowId }
Navegador → se suscribe a private-workflows.{workflowId}, espera la suscripción
Navegador → POST /workflows/{id}/start  → despacha el trabajo
Proceso   → ejecuta el flujo de trabajo; el canal empuja cada evento, en secuencia
Navegador → reordena por secuencia, renderiza el progreso, reconcilia ante un hueco
```

El orden de las tres primeras líneas importa. Pusher y Redis Pub/Sub no reproducen nada: un evento publicado antes de que el navegador se suscribiera se ha perdido. Así que el navegador se suscribe primero y solo entonces pide al servidor que empiece.

### El trabajo

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\WorkflowRun;
use App\Neuron\Workflows\ContentWorkflow;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Agent\Adapters\AgentChunkAdapter;
use NeuronAI\Laravel\Models\WorkflowStore;
use NeuronAI\Workflow\Persistence\EloquentPersistence;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;
use NeuronAI\Workflow\WorkflowState;
use Pusher\Pusher;

class RunContentWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $timeout = 600;
    public int $tries = 1;   // agent runs are expensive — do not blind-retry

    public function __construct(
        public readonly WorkflowRun $run,
    ) {}

    public function handle(Pusher $pusher): void
    {
        $state = ContentWorkflow::make(
            workflowId: $this->run->workflow_id,
            state: new WorkflowState(['topic' => $this->run->topic]),
        )
            ->setPersistence(new EloquentPersistence(WorkflowStore::class))
            ->setStreamAdapter(new AgentChunkAdapter())
            ->setChannel(new PusherChannel(
                client: $pusher,
                channel: "private-workflows.{$this->run->workflow_id}",
            ))
            ->run();

        if ($state->isInterrupted()) {
            $this->run->update(['status' => 'awaiting_approval']);

            return;   // Chapter 22 records and routes the approval
        }

        $this->run->update([
            'status' => 'completed',
            'result' => $state->get('final'),
        ]);
    }
}
```

### Cuatro cosas que este trabajo hace de forma distinta a una petición web

**`run()`, no un bucle.** Con un adaptador y un canal enganchados, el flujo de trabajo consume su propia transmisión y entrega cada evento a través del canal en el momento en que ocurre. `run()` devuelve el estado final cuando el segmento se completa o se pausa. No hay generador que iterar ni nada que imprimir.

**El adaptador sigue decidiendo la forma.** Un canal lleva eventos de protocolo, nunca objetos nativos, así que necesita un adaptador. `AgentChunkAdapter` es el vocabulario propio de NeuronAI para un consumidor que no habla ningún protocolo de interfaz: cada fragmento o evento de progreso se convierte en un evento con el nombre de su tipo (`text`, `tool-call`, `activity`, `step-started`) y con los propios campos del fragmento como carga. Si el navegador ejecuta un cliente AG-UI o Vercel, engancha ese adaptador en su lugar; al canal le da igual.

**El canal informa del ciclo de vida.** Tras las tramas terminales del adaptador, el canal envía `stream.completed`, `stream.interrupted` o `stream.failed`, llevando solo el ID del flujo de trabajo: ni estado, ni detalles de la excepción. No necesitas tus propios eventos de difusión `WorkflowCompleted` o `WorkflowPaused`: el navegador conoce el resultado por la transmisión y recupera el resultado de tu aplicación, que es el registro autorizado.

**La pausa es un valor de retorno.** Una ejecución interrumpida vuelve con normalidad con `isInterrupted()` a true: no hay nada que capturar. El Capítulo 22 sigue a partir de ahí.

`AgentChunkAdapter` reenvía todo lo que recibe, incluidos los argumentos de las llamadas a herramienta y los resultados de las herramientas. Para una pantalla de progreso que ve la persona que inició la ejecución eso suele estar bien; para cualquier cosa de cara al cliente, suprime lo que no debe viajar con `mapEvent(ToolResultChunk::class, fn () => null)`, o engancha el adaptador AG-UI y deja que decida el frontend. La regla de la Sección 7.4 no deja de aplicarse porque haya cambiado el transporte.

### El cliente de Pusher

`PusherChannel` recibe un cliente configurado por la aplicación, del SDK oficial `pusher/pusher-php-server` (que es también lo que habla Laravel Reverb), de modo que el cifrado, la firma, los puntos de conexión y los tiempos de espera se configuran una sola vez, donde corresponde:

```php
// AppServiceProvider::register()
$this->app->singleton(Pusher::class, fn () => new Pusher(
    config('broadcasting.connections.reverb.key'),
    config('broadcasting.connections.reverb.secret'),
    config('broadcasting.connections.reverb.app_id'),
    config('broadcasting.connections.reverb.options', []) + ['timeout' => 5],
));
```

Fija explícitamente el `timeout` del SDK y usa la versión 7.2.4 o posterior; las versiones anteriores no lo pasan a la petición HTTP.

¿Prefieres Redis? `new RedisChannel($redis, "workflows:{$id}")` publica los mismos sobres en Redis Pub/Sub para un proceso que mantenga la conexión del navegador. ¿Prefieres la difusión propia de Laravel? `CallbackChannel` envuelve un closure por cada método del ciclo de vida, así que `onSend` puede llamar a `Broadcast::private(...)->as($event->type)->with($event->data)->sendNow()`. **`sendNow()`, nunca una difusión encolada.** Una difusión encolada pone tus actualizaciones de progreso en cola detrás del trabajo que las produce (con un solo proceso, un interbloqueo a cámara lenta) y con varios procesos las entrega desordenadas.

### El sobre, y por qué el navegador necesita una biblioteca

`PusherChannel` y `RedisChannel` no envían eventos de protocolo desnudos. Cada mensaje es un sobre:

```json
{"streamId":"81d4f00e881563538f272ca26aa7a8d4","sequence":3,"type":"text","data":{"messageId":"msg_1","content":"The first"}}
```

Detrás de esos campos se esconden tres problemas, y los tres ocurrirán en producción:

**Orden.** Pusher garantiza el orden dentro de un lote, no entre lotes. `sequence` numera cada evento lógico de un segmento, para que el navegador pueda volver a ordenarlos, incluido un `stream.completed` que llegue antes que el texto al que sigue.

**Tamaño.** Pusher limita un evento a 10 KB. Un resultado de herramienta largo o una carga de actividad grande se divide en sobres `stream.fragment` que comparten un mismo número de secuencia, y hay que reensamblarlos antes de poder interpretarlos.

**Huecos.** Una conexión caída pierde eventos para siempre. El navegador debe detectar un número de secuencia que falta y recargar desde la aplicación en lugar de renderizar una transmisión con un agujero.

No quieres escribir eso a mano, y no tienes por qué. `@neuron-core/streaming` es la mitad del navegador del mismo contrato:

```javascript
import { subscribeToPusher } from '@neuron-core/streaming';

const channel = Echo.connector.pusher.subscribe(`private-workflows.${workflowId}`);

channel.bind('pusher:subscription_succeeded', () => {
    fetch(`/workflows/${workflowId}/start`, { method: 'POST', headers: csrfHeaders });
});

const subscription = subscribeToPusher(channel, {
    onEvent: ({ type, data }) => {
        if (type === 'activity') {
            renderProgress(data.id, data.data);
        } else if (type === 'stream.interrupted') {
            showMessage('Waiting for approval.');
        } else if (type === 'stream.completed') {
            loadResult(workflowId);
        }
    },
    onGap: () => loadResult(workflowId),   // reconcile from the server; never guess
});
```

Ordena, reensambla, descarta duplicados e informa de los huecos; tu callback solo ve eventos completos y en secuencia. La referencia al canal viene del cliente de Pusher que Echo ya configuró, así que la autenticación pasa por tus rutas de difusión habituales.

### La autorización del canal

```php
// routes/channels.php
Broadcast::channel('workflows.{workflowId}', function ($user, string $workflowId) {
    return WorkflowRun::where('workflow_id', $workflowId)
        ->where('tenant_id', $user->tenant_id)
        ->exists();
});
```

Sin esto, cualquiera que adivine un ID de flujo de trabajo ve trabajar al agente de otra persona. Los cuatro puntos de fuga de la Sección 18.3 tienen un quinto pariente: el canal de difusión. Para contenido que deba seguir siendo confidencial incluso frente al proveedor de difusión, usa un canal `private-encrypted-*` con la clave maestra de cifrado del SDK; el navegador necesita `pusher-js/with-encryption`, y el consumidor del paquete no cambia.

### Qué compone esto

Este único trabajo es gran parte del libro convergiendo:

- Transmisión de flujos de trabajo con `yield` y eventos de progreso portables (14.4, 21.4)
- Interrupción y persistencia (15.4)
- Persistencia con Eloquent (18.4)
- Ejecución asíncrona (16.4)
- Adaptadores empujando hacia un transporte externo (7.5)
- `pcntl` disponible, así que las herramientas en paralelo funcionan (5.13)
- Inspector suscrito en el flujo de trabajo (23.3)

Esa última es la mala configuración con más probabilidad de morderte: no se monitoriza nada a menos que suscribas el oyente, y un proceso de cola es exactamente donde nadie nota que falta.

### Puntos clave

- Push, no pull: adaptador más canal, y el proceso simplemente llama a `run()`.
- Suscríbete primero y luego inicia la ejecución: Pusher y Redis no reproducen nada.
- `PusherChannel` envía sobres numerados en secuencia y fragmentables; `@neuron-core/streaming` reordena, reensambla e informa de los huecos.
- El canal informa de finalización, pausa y fallo; recupera los resultados de la aplicación.
- Autoriza el canal por inquilino; `$tries = 1` en los trabajos de agentes; los reintentos a ciegas vuelven a gastar dinero.

## 21.6 Desconexión y coste huérfano

### El problema que nadie menciona

Un usuario inicia una ejecución de 30 segundos. En el segundo cuatro cierra la pestaña.

El navegador ya no está. **El agente sigue ejecutándose.** Cada llamada al modelo que quede se factura. En un flujo de trabajo multiagente eso es una cantidad sustancial de dinero gastado en una salida que nadie leerá jamás.

Con poco volumen es invisible. A escala es una partida de gasto.

### Detectarlo en una respuesta en transmisión

```php
return response()->stream(function () use ($agent, $message) {
    $stream = $agent->stream(new UserMessage($message));
    \assert($stream instanceof Generator);

    foreach ($stream as $chunk) {
        if (\connection_aborted()) {
            \Log::info('Client disconnected — stopping agent run');

            try {
                $stream->throw(new ClientDisconnected());
            } catch (ClientDisconnected) {
                // the run is now settled as failed
            }
            break;
        }

        if ($chunk instanceof TextChunk) {
            echo SSEEncoder::frame(new ProtocolEvent('text', ['content' => $chunk->content]));
            \flush();
        }
    }
}, 200, $headers);
```

`connection_aborted()` requiere que hayas escrito en la conexión: PHP solo detecta la tubería rota al intentar escribir. Como estás transmitiendo, estás escribiendo, así que funciona. No funcionaría en un punto de conexión sin transmisión.

### Por qué `break` solo no basta

`ClientDisconnected` es una clase de excepción corriente, tuya. Lo que importa es lanzarla *dentro* del generador.

Una ejecución de un agente es una ejecución de flujo de trabajo duradera. Mientras se ejecuta mantiene una concesión sobre su hilo (diez minutos por defecto para un agente) para que un segundo proceso no pueda iniciar una ejecución concurrente sobre la misma conversación. Un final limpio, una pausa o un fallo capturado liberan la concesión. Abandonar sin más el generador no hace nada de eso: la ejecución sigue marcada como en curso hasta que la concesión caduca.

Con la persistencia en memoria por defecto nunca lo notas, porque el registro muere con la petición. Dale al agente persistencia duradera (lo que hace el Capítulo 22, porque las aprobaciones la necesitan) y un `break` a secas significa que el *siguiente* mensaje del usuario en esa conversación se rechaza con `RunInFlightException` durante hasta diez minutos. `$stream->throw()` entrega la excepción en el punto en el que la ejecución está suspendida; el flujo de trabajo da la ejecución por fallida y relanza, y el siguiente mensaje sustituye con normalidad a la ejecución fallida.

El `disconnect.php` del repositorio complementario ejecuta las dos versiones una al lado de la otra: con `break` solo, el segundo mensaje se rechaza; con el `throw()`, se responde.

**Una advertencia honesta:** detener el bucle detiene *tu* iteración. Una llamada al modelo ya en vuelo se completa y se factura. Estás limitando el daño, no eliminándolo.

### Para los flujos de trabajo en cola

Un navegador desconectado no detiene a un proceso, y no debería: el usuario puede volver, y el resultado vale la pena tenerlo. Pero hay casos en los que la cancelación es lo correcto. Un proceso que se ejecuta con un canal no tiene ningún bucle del que salir, así que la comprobación va dentro del flujo de trabajo: en las primeras líneas de cualquier nodo que inicie un paso costoso:

```php
class ReviewNode extends Node
{
    public function __invoke(DraftReady $event, WorkflowState $state): DraftReviewed|StopEvent
    {
        if (Cache::has("workflow:{$state->getWorkflowId()}:cancelled")) {
            $state->set('cancelled', true);

            return new StopEvent();
        }

        // ... the review itself, as in Chapter 14
    }
}
```

```php
// A cancel endpoint
Cache::put("workflow:{$id}:cancelled", true, now()->addHour());
```

Cancelación explícita, no deducida de la desconexión, y termina la ejecución limpiamente, así que el ID del flujo de trabajo vuelve a quedar libre y el canal informa de `stream.completed` como en cualquier otro final.

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

Registra el uso real a partir de los recuentos de tokens de cada inferencia: la Sección 23.1 suscribe un oyente que hace exactamente eso. La Sección 1.3 decía que capturaras el uso desde el primer prototipo; para esto es para lo que se captura.

### Puntos clave

- Una pestaña cerrada no detiene a un agente: sigues pagando.
- `connection_aborted()` dentro del bucle de la transmisión limita el daño.
- Lanza la excepción dentro del generador antes del `break`, o una ejecución duradera mantiene su hilo bloqueado hasta que caduca la concesión.
- El trabajo en cola debe cancelarse explícitamente, entre pasos, no por deducción.
- Los presupuestos diarios por usuario ponen techo a la exposición; necesitan los recuentos de tokens que llevas registrando.

## Laboratorio 15 — La interfaz de chat con transmisión

**Cubre:** SSE o Livewire, visualización de la actividad de las herramientas, almacenamiento en búfer, desconexión.

### Objetivo

Una interfaz de chat que renderice la respuesta token a token y muestre qué está haciendo el agente mientras lo hace, con los nombres de las herramientas traducidos a un lenguaje que un cliente pueda leer.

### Requisitos

1. **Renderizado token a token.** Elige Livewire (Sección 21.3) o SSE con `fetch` (Sección 21.1). Livewire tiene menos piezas móviles; SSE te enseña más sobre el transporte.
2. **Una línea de actividad de herramientas** que sustituye en lugar de acumular, impulsada por una lista de permitidos de etiquetas con un respaldo seguro.
3. **Los resultados de las herramientas nunca llegan al navegador.** Solo las etiquetas.
4. **La cadena de almacenamiento en búfer verificada** con `curl -N` en los tres puntos de la Sección 21.2: PHP solo, a través del servidor web, a través de toda la pila pública. Anota qué capa, si alguna, necesitó configurarse.
5. **Gestión de la desconexión** con `connection_aborted()`, lanzando la excepción dentro de la transmisión antes de salir del bucle.

### Criterios de aceptación

- El primer token visible llega muy por debajo del segundo con un modelo local. Mídelo; no lo supongas.
- Hacer una pregunta que dispare una herramienta muestra la etiqueta amigable y luego la respuesta.
- Añadir una herramienta nueva sin añadir su etiqueta muestra «Working on it», no el nombre interno de la herramienta. Pruébalo deliberadamente.
- Cerrar la pestaña a mitad de respuesta produce una línea de registro y detiene el bucle, y un mensaje nuevo en la misma conversación, enviado justo después, recibe respuesta en lugar de ser rechazado.
- `curl -N` transmite a través de todo la pila, no solo en local.

### La parte que la gente se salta

El requisito cuatro. Es tentador cantar victoria cuando funciona en `artisan serve`, donde no hay nginx ni proxy. El primer despliegue es donde la transmisión se rompe, y la bisección de la Sección 21.2 es la diferencia entre cinco minutos y una tarde.

Ejecuta los tres comandos `curl -N` contra tu entorno de staging real antes de dar este laboratorio por terminado.

### Ir más allá

Añade un botón de «parar» que aborte la petición desde el lado del navegador y confirma que `connection_aborted()` se dispara. Después mide lo que ahorró: ejecuta el mismo prompt hasta el final, anota el recuento de tokens y compáralo con una ejecución abortada. Ese número es el argumento para construir el botón.
