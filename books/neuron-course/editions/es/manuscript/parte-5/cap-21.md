# Capítulo 21 — Transmisión hacia el frontend

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

Los listados de Laravel de abajo viven dentro de una aplicación, pero las partes que no la necesitan son ejecutables en [`chapters/Ch21`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch21) del repositorio complementario: `sse-frames.php` imprime las tramas exactas que envía el punto de conexión de la Sección 21.1, `channel.php` imprime los sobres que publica un canal push en la Sección 21.5 y `disconnect.php` reproduce el comportamiento ante la desconexión de la Sección 21.6. Ninguno necesita un modelo.
:::

## 21.1 Server-Sent Events en Laravel

### Por qué SSE en lugar de WebSockets

Para las respuestas de un agente el tráfico es unidireccional: el servidor envía, el navegador recibe. SSE te da eso sobre HTTP corriente, con un cliente integrado en el navegador y sin infraestructura extra.

Los WebSockets son la elección correcta cuando el navegador también necesita empujar, cosa que en una interfaz de chat no ocurre, porque el mensaje siguiente es una petición nueva.

### El controlador

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Conversation;
use App\Neuron\Agents\SupportAgent;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Gate;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\ProtocolEvent;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;

class ChatStreamController extends Controller
{
    public function __invoke(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ): StreamedResponse {
        Gate::authorize('participate', $conversation);

        $validated = $request->validate([
            'message' => ['required', 'string', 'max:4000'],
        ]);

        $agent = $agent->for($conversation->threadId());
        $agent->recoverFailedTurn();

        $stream = $agent->stream(new UserMessage($validated['message']));

        // Lazy until pulled: admit the run now, while a refusal can still be an HTTP status.
        $stream->valid();

        return response()->stream(function () use ($stream) {
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

Antes de que haya un bucle hay un agente, y llega de la manera en que lo construyó la Sección 18.1. La ruta nombra la conversación (`Route::get('/chat/stream/{conversation}', ChatStreamController::class)`), la acción recibe el agente por inyección en el método, y `for()` lo vincula al hilo de la conversación una vez que la policy ha autorizado al usuario. Un agente sin un hilo vinculado no transmite en absoluto. `recoverFailedTurn()` es la respuesta a la quinta pregunta de la Sección 18.4, dada antes del turno y nunca después; la Sección 21.6 muestra por qué un punto de conexión de transmisión es donde más se justifica.

`stream()` es en sí mismo el generador: itéralo directamente. También es perezoso: no se ejecuta nada hasta que se extrae el primer elemento, y `$stream->valid()` lo extrae en el controlador, antes de que exista la respuesta. Un hilo que no puede aceptar el turno (otra pestaña sigue transmitiendo sobre él) se rechaza entonces con un estado HTTP, el 409 al que lo asigna la Sección 21.4, en lugar de con un `200` que termina sin una palabra. Sin adaptador de transmisión enganchado, el generador produce los objetos de fragmento nativos de NeuronAI, y `TextChunk` es el único tipo que este punto de conexión deja pasar. Todo lo demás (las llamadas a herramienta con sus argumentos, los resultados de las herramientas) se descarta en el servidor, que es la regla de la Sección 7.4 aplicada en la frontera HTTP.

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
const source = new EventSource(`/chat/stream/${conversationId}?message=` + encodeURIComponent(text));

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

- SSE encaja con la salida de un agente: unidireccional, HTTP puro, un cliente integrado en el navegador.
- Autoriza, vincula con `for()`, recupera y haz avanzar el generador antes de devolver la respuesta: tras el primer byte, un fallo ya no puede ser un estado.
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

use App\Models\Conversation;
use App\Neuron\Agents\SupportAgent;
use Livewire\Component;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Chat\Messages\UserMessage;

class Chat extends Component
{
    public Conversation $conversation;

    public string $input = '';
    public string $answer = '';
    public ?string $activity = null;
    public array $history = [];

    public function send(SupportAgent $agent): void
    {
        $this->authorize('participate', $this->conversation);

        $question = \trim($this->input);

        if ($question === '') {
            return;
        }

        $this->history[] = ['role' => 'user', 'content' => $question];
        $this->input     = '';
        $this->answer    = '';

        $agent = $agent->for($this->conversation->threadId());
        $agent->recoverFailedTurn();

        $stream = $agent->stream(new UserMessage($question));

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

El agente llega como en un controlador. La página monta el componente con su conversación (`<livewire:chat :conversation="$conversation" />`), Livewire resuelve `SupportAgent` desde el contenedor para la acción, y `send()` hace lo que hace cada punto de conexión de este capítulo antes de un turno: autoriza, vincula con `for()`, recupera. Livewire protege el ID del modelo frente a manipulaciones entre peticiones, pero la policy se ejecuta igualmente en cada `send()`: quién puede usar una conversación puede cambiar mientras la página sigue abierta.

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

use App\Models\Conversation;
use App\Neuron\Agents\SupportAgent;
use App\Neuron\ThreadScope;
use Generator;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Gate;
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Agent\Frontend\AGUIInputTranslator;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\SSEEncoder;
use Symfony\Component\HttpFoundation\StreamedResponse;
use Throwable;

class AgentUiController extends Controller
{
    public function __invoke(Request $request, SupportAgent $agent): StreamedResponse
    {
        $request->validate([
            'threadId'           => ['required', 'string', 'regex:/^t\d+:u\d+:c\d+$/'],
            'runId'              => ['nullable', 'string'],
            'messages'           => ['required', 'array', 'min:1'],
            'messages.*.id'      => ['required', 'string'],
            'messages.*.role'    => ['required', 'string'],
            'messages.*.content' => ['nullable', 'string'],
            'state'              => ['nullable', 'array'],
            'resume'             => ['nullable', 'array'],
        ]);

        // The client names the thread; the server decides whether this user may use it.
        $threadId = $request->input('threadId');
        $conversation = Conversation::findOrFail(ThreadScope::of($threadId)->conversationId);

        Gate::authorize('participate', $conversation);
        abort_unless($conversation->threadId() === $threadId, 403);

        // The messages as posted: validate() returns only the keys its rules name.
        $messages = $request->input('messages');
        $last = \array_last($messages);

        // Answers to a paused run (approvals, browser tool results) continue it;
        // a trailing user message starts a new turn. Nothing else is accepted.
        $continuation = $request->array('resume') !== [] || $last['role'] === 'tool';
        abort_unless($continuation || $last['role'] === 'user', 422, 'Nothing to answer and no new message.');

        // On a copy of its own: the recovered turn must not stream into this response.
        $agent->for($threadId)->recoverFailedTurn();

        $adapter = new AGUIAdapter(
            threadId: $threadId,
            runId: $request->input('runId'),
            messages: $messages,
            state: $request->array('state'),
        );

        $agent = $agent->for($threadId)->setStreamAdapter(fn (): AGUIAdapter => $adapter);

        $events = $continuation
            ? $agent->submitInputs($request->all(), new AGUIInputTranslator())->events()
            : $agent->stream(new UserMessage((string) $last['content']));

        // Admission is lazy: start it now, so a refusal is an HTTP status, not a RUN_ERROR frame.
        $events->valid();

        return response()->stream(function () use ($events, $adapter): Generator {
            try {
                yield from SSEEncoder::encode($events);
            } catch (Throwable $e) {
                report($e);

                foreach ($adapter->error($e) as $event) {
                    yield SSEEncoder::frame($event);
                }
            }
        }, 200, $adapter->getHeaders());
    }
}
```

### Siete cosas que señalar

**El adaptador da la forma, el codificador hace las tramas.** `setStreamAdapter()` hace que `stream()` produzca objetos `ProtocolEvent` (`RUN_STARTED`, `TEXT_MESSAGE_CONTENT` y el resto) en lugar de fragmentos nativos. Acepta una factoría, llamada una vez por segmento de ejecución (Sección 7.5); esta petición ejecuta un solo segmento, así que la closure devuelve la instancia de la que la respuesta toma sus cabeceras. `SSEEncoder::encode()` convierte cada evento en una línea `data:` y reenvía el valor de retorno del generador, así que el `AgentState` final sigue ahí (es lo que evalúa `yield from`) si lo quieres. La callback es en sí misma un generador: Laravel imprime y vacía cada trama que produce con `yield`. El adaptador no sabe nada de bytes, y eso es lo que permite que el mismo adaptador alimente un canal de difusión en la Sección 21.5.

**`getHeaders()` aporta las cabeceras del protocolo, incluida `X-Accel-Buffering: no`.** Los adaptadores integrados llevan consigo la solución de nginx de la Sección 21.2, así que no hay nada que fusionar.

**Al agente solo le llega el último mensaje del usuario.** Un cliente AG-UI envía la conversación entera en cada turno. El agente ya tiene esa conversación en su historial de conversación duradero, indexado por hilo: pasarle la copia del cliente hace que cada mensaje anterior se guarde dos veces. Los `messages` del cliente van en cambio al adaptador, que los usa para mantener completa la instantánea de mensajes del protocolo. Van enteros, desde `$request->input('messages')`. `validate()` devuelve solo las claves que nombran sus reglas, y un adaptador inicializado con ese subconjunto ha perdido cada `toolCallId` y `toolCalls`: lanza `InputTranslationException` ante cualquier conversación que contenga un mensaje de herramienta, y una continuación que entrega un resultado de herramienta nunca puede funcionar.

**El hilo es la identidad del agente: autorízalo.** El `threadId` de AG-UI se convierte en el hilo del agente, y el hilo *es* el ID del flujo de trabajo del agente: la clave bajo la que se archivan su historial y cualquier ejecución suspendida. Eso lo convierte exactamente en el valor que la Sección 18.2 decía que nunca se tomara de la entrada del usuario. Tres pasos convierten una cadena proporcionada por el cliente en un hilo que este usuario puede usar: `ThreadScope` (Sección 18.3) lee la conversación a partir del nombre, la policy decide si este usuario puede usar esa conversación, y el nombre que el servidor deriva del registro debe ser el que envió el cliente. Solo entonces se lee o se escribe algo bajo él. Devuelve también `runId`: es el identificador por petición del cliente, y sin él el cliente no puede correlacionar la transmisión con la ejecución que pidió.

**La forma de la petición decide entre turno nuevo y continuación.** Un mensaje de usuario al final es un turno nuevo, y va a `stream()`. Un array `resume` (el cliente respondiendo a interrupciones) o un mensaje de herramienta al final es la continuación de una ejecución en pausa, y va a `submitInputs()` con el traductor del protocolo, que la valida contra la petición persistida antes de ejecutar nada y lanza `InputTranslationException` ante cualquier cosa que no coincida. La prueba de continuación va primero, como en la Sección 7.5: tras una pausa de aprobación la lista del cliente sigue terminando con la pregunta del usuario. Fíjate en que la continuación llama a `events()`, no a `stream()`: `stream()` siempre empieza un turno nuevo. Una continuación no válida debe ser una respuesta de error, nunca un repliegue a un turno nuevo.

**Hasta la primera trama, un fallo es un código de estado.** Antes de devolver la respuesta ocurren dos cosas. `recoverFailedTurn()` termina un turno fallido (Sección 18.4) sobre una copia propia (vinculada al hilo, sin adaptador), de modo que la respuesta recuperada cae en el historial y no en esta transmisión. Y `$events->valid()` extrae el primer evento. `stream()` y `events()` son perezosos: la ejecución se admite solo cuando el generador se extrae por primera vez y, dejada a la callback, eso ocurre después de que el `200` ya ha salido, de modo que un hilo que no puede aceptar el turno (una aprobación aún pendiente, otra pestaña transmitiendo) llega al navegador como una trama `RUN_ERROR` bajo un estado de éxito. Extraído en el controlador, el rechazo sigue siendo una excepción que Laravel puede convertir en un estado. El adaptador se construye ahí por la misma razón: su constructor valida los mensajes con los que se inicializa. A partir de ese punto `SSEEncoder::encode()` es lo único que itera el generador, y un fallo cuando las tramas ya fluyen ya está en la red como `RUN_ERROR` cuando llega al `catch`: `$adapter->error()` entonces no produce nada, y cierra el protocolo solo si no se había enviado ninguna trama. Los estados se asignan una sola vez para toda la aplicación, en `bootstrap/app.php`:

```php
// bootstrap/app.php
return Application::configure(basePath: dirname(__DIR__))
    // ->withRouting(...) and ->withMiddleware(...) as the skeleton has them
    ->withExceptions(function (Exceptions $exceptions): void {
        // The first callback whose type matches wins: the most specific class goes first.
        $exceptions->render(fn (InputTranslationException $e) => response()->json(
            ['message' => $e->getMessage()], 400,
        ));
        $exceptions->render(fn (PersistenceException $e) => response()->json(
            ['message' => 'Conversations are unavailable. Retry later.'], 503,
        ));
        $exceptions->render(fn (RunInFlightException $e) => response()->json(
            ['message' => 'The conversation is busy.', 'status' => $e->status->value], 409,
        ));
        $exceptions->render(fn (WorkflowException $e) => response()->json(
            ['message' => 'The conversation changed. Reload it.'], 409,
        ));
    })->create();
```

Los cuatro viven en `NeuronAI\Exceptions`. `PersistenceException` y `RunInFlightException` extienden ambas `WorkflowException`, y por eso importa el orden. El mensaje de una `InputTranslationException` está escrito para los clientes; el de una `WorkflowException` lleva detalles internos, y se queda en el registro.

**Cambia el adaptador, conserva todo lo demás.** `VercelAIAdapter` en lugar de `AGUIAdapter` y el mismo agente sirve otro protocolo de frontend, con `VercelAIInputTranslator` para sus continuaciones. El argumento de las interfaces de la Sección 2.2, aplicado al lado de la salida.

### Cuando la ejecución se pausa

Si una herramienta del turno necesita aprobación (Capítulo 22), la transmisión no termina como una completada. El terminal `interrupt()` del adaptador sustituye a `end()`: en AG-UI, `RUN_FINISHED` lleva `outcome: {type: "interrupt", interrupts: [...]}`, una interrupción `confirmation` por cada llamada a herramienta pendiente, con el ID de la llamada a herramienta como su `id`; en Vercel, una parte `tool-approval-request` por llamada.

Un frontend que trate cada `RUN_FINISHED` como «la respuesta está completa» mostrará una ejecución en pausa como si hubiera terminado. Comprueba `outcome.type` antes de cerrar el turno. El cliente responde con un array `resume` en su siguiente petición, que el punto de conexión de arriba dirige a `submitInputs()`. La Sección 22.5 cubre el lado de la aprobación para clientes que no hablan AG-UI.

### Qué cubre el adaptador y qué no

De la Sección 7.5, porque un equipo que elige un frontend necesita saberlo antes de comprometerse:

**Instantáneas en la pausa, no deltas.** El adaptador emite `STATE_SNAPSHOT` y `MESSAGES_SNAPSHOT` antes de terminar una ejecución interrumpida, inicializadas a partir del `state` y los `messages` que pasaste a su constructor. No emite `STATE_DELTA`. Si tu diseño depende de una sincronización fina del estado compartido mientras el agente se ejecuta, el adaptador no te la va a dar.

**Las herramientas definidas por el frontend necesitan un paso más.** Los clientes AG-UI pueden declarar herramientas en `RunAgentInput.tools` para que las ejecute el navegador. NeuronAI las admite como herramientas diferidas: la ejecución se suspende cuando el modelo llama a una, el adaptador publica la llamada y el cliente devuelve el resultado como un mensaje de herramienta al final, que es la rama de continuación de arriba. Lo que el punto de conexión todavía no hace es enganchar esas herramientas al agente. `(new AGUIInputTranslator())->tools($request->all())` las construye a partir de la petición; añádelas a la copia vinculada con `addTool()`, después de rechazar cualquier nombre que tape una de tus herramientas del lado del servidor, y aplícales tu política de aprobación como a cualquier otra herramienta. Exime también la ruta de los middleware `TrimStrings` y `ConvertEmptyStringsToNull` de Laravel: con ellos, un resultado de herramienta que es una cadena vacía llega al traductor como `null` y se rechaza.

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

Una SPA envía un token; Sanctum o Passport lo gestionan como siempre. La parte importante es lo que se le dice al *agente* sobre el usuario que acaba de autenticarse: nada. El contenedor construye el mismo `SupportAgent` sin contexto para cada petición (Sección 18.1), el punto de conexión autoriza el hilo, y `for()` vincula una copia a él. Lo que el agente hace por este usuario se deduce entonces del hilo y de nada más:

```php
class SupportAgent extends Agent
{
    // constructor, provider(), messageStore(), persistence() as in Chapter 18

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());

        return [
            new SearchOrdersTool($scope->tenantId),
            new GetOrderStatusTool($scope->tenantId),
        ];
    }
}
```

La visibilidad de las herramientas, el historial de conversación y los filtros de RAG se derivan todos de esa única entrada. Ninguna factoría, y ningún `auth()` dentro del agente: la misma clase se ejecuta sin cambios en el proceso de cola de la Sección 21.5, donde no hay ningún usuario al que preguntar. El argumento de la Sección 18.3, y la razón de que el controlador se quede tan corto.

### Puntos clave

- `setStreamAdapter()` acepta una factoría y hace que `stream()` produzca `ProtocolEvent`; `SSEEncoder::encode()` los convierte en tramas; `getHeaders()` ya incluye `X-Accel-Buffering`.
- Envía al agente solo el último mensaje del usuario; el historial del cliente inicializa el adaptador, entero, desde `input()`, no desde `validate()`.
- Un array `resume` o un mensaje de herramienta al final es una continuación: `submitInputs()` con el traductor del protocolo y luego `events()`.
- El `threadId` de AG-UI se convierte en el ID del flujo de trabajo del agente: autorízalo contra la conversación que nombra, nunca te fíes del valor en bruto.
- Recupera un turno fallido y haz avanzar el generador antes de devolver la respuesta: hasta la primera trama, un rechazo todavía puede ser un 400 o un 409.
- Una ejecución en pausa por una aprobación termina con un resultado de interrupción, no con un final normal; compruébalo antes de cerrar el turno.
- Los nodos producen eventos de progreso portables; `mapEvent()` traduce o suprime los tuyos.

## 21.5 Transmisión desde una cola

Esta es la sección donde se encuentran las Partes IV y V.

### El problema

La Sección 16.4 estableció que las ejecuciones largas pertenecen a una cola. Pero un proceso de cola no tiene conexión HTTP con el usuario, así que ¿cómo llega el progreso al navegador?

La respuesta es un **canal de transmisión**. Todo lo visto hasta ahora es transmisión *pull*: el código que itera el generador es el código que sostiene la respuesta. Un canal es la mitad *push*. Engancha uno a un flujo de trabajo o a un agente, junto con un adaptador de transmisión, y la ejecución entrega al canal cada evento de protocolo a medida que se produce (a Pusher, a Redis, a un websocket) mientras el proceso se limita a llamar a `run()`.

### La arquitectura

```
Navegador → POST /workflows             → crea el registro de la ejecución y su ID de ejecución, devuelve { workflowId }
Navegador → se suscribe a private-workflows.{workflowId}, espera la suscripción
Navegador → POST /workflows/{id}/start  → despacha el trabajo
Proceso   → ejecuta el flujo de trabajo; el canal empuja cada evento, en secuencia
Navegador → reordena por secuencia, renderiza el progreso, reconcilia ante un hueco
```

El orden de las tres primeras líneas importa. Pusher y Redis Pub/Sub no reproducen nada: un evento publicado antes de que el navegador se suscribiera se ha perdido. Así que el navegador se suscribe primero y solo entonces pide al servidor que empiece. La primera petición hace una cosa más: acuña el ID de ejecución (un UUID en una columna `run_id` del registro) antes de que exista ningún trabajo. El trabajo de abajo depende de él.

### El trabajo

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\WorkflowRun;
use App\Neuron\Workflows\ContentState;
use App\Neuron\Workflows\ContentWorkflow;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use NeuronAI\Agent\Adapters\AgentChunkAdapter;
use NeuronAI\Exceptions\RunInFlightException;
use NeuronAI\Workflow\Executor\ExecutionRequest;
use NeuronAI\Workflow\Persistence\PersistenceInterface;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;
use NeuronAI\Workflow\WorkflowStatus;
use Pusher\Pusher;

class RunContentWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** Longer than the longest run, shorter than the queue connection's retry_after (360). */
    public int $timeout = 300;

    public function __construct(
        public readonly WorkflowRun $run,
    ) {}

    public function handle(PersistenceInterface $runs, Pusher $pusher): void
    {
        $workflowId = $this->run->workflow_id;

        $workflow = ContentWorkflow::make(
            workflowId: $workflowId,
            state: new ContentState(['topic' => $this->run->topic]),
        )
            ->setPersistence($runs)
            ->setLeaseTimeout(600)
            ->setStreamAdapter(fn (): AgentChunkAdapter => new AgentChunkAdapter())
            ->setChannel(fn (): PusherChannel => new PusherChannel(
                client: $pusher,
                channel: "private-workflows.{$workflowId}",
                batchSize: 1,
            ));

        try {
            // The run ID was minted with the record: every delivery of this job names the same run.
            $state = $workflow->run(ExecutionRequest::start(
                runId: $this->run->run_id,
                recoverFailed: true,
            ));
        } catch (RunInFlightException $e) {
            if ($e->status !== WorkflowStatus::Running) {
                throw $e;   // paused, not dead: there is nothing to recover
            }

            // A delivery that was killed still holds the lease: come back when it has expired.
            $this->release(\max(1, $e->leaseExpiresAt - \time()));

            return;
        }

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

### Cinco cosas que este trabajo hace de forma distinta a una petición web

**`run()`, no un bucle.** Con un adaptador y un canal enganchados, el flujo de trabajo consume su propia transmisión y entrega cada evento a través del canal en el momento en que ocurre. `run()` devuelve el estado final cuando el segmento se completa o se pausa. No hay generador que iterar ni nada que imprimir. Ambos setters aceptan una factoría, porque un adaptador y un canal guardan el estado de la transmisión de un segmento: el segmento que se pausa para una aprobación y el que continúa después construyen cada uno el suyo. Un agente en un proceso necesita una cosa más: su turno tiene que ser en transmisión (`chat($message, stream: true)`, la forma anticipada de la Sección 7.5), porque un `chat()` simple hace una llamada al modelo con búfer, y ningún texto llega nunca al canal.

**El adaptador sigue decidiendo la forma.** Un canal lleva eventos de protocolo, nunca objetos nativos, así que necesita un adaptador. `AgentChunkAdapter` es el vocabulario propio de NeuronAI para un consumidor que no habla ningún protocolo de interfaz: cada fragmento o evento de progreso se convierte en un evento con el nombre de su tipo (`text`, `tool-call`, `activity`, `step-started`) y con los propios campos del fragmento como carga. Si el navegador ejecuta un cliente AG-UI o Vercel, engancha ese adaptador en su lugar; al canal le da igual.

**El canal informa del ciclo de vida.** Tras las tramas terminales del adaptador, el canal envía `stream.completed`, `stream.interrupted` o `stream.failed`, llevando solo el ID del flujo de trabajo: ni estado, ni detalles de la excepción. No necesitas tus propios eventos de difusión `WorkflowCompleted` o `WorkflowPaused`: el navegador conoce el resultado por la transmisión y recupera el resultado de tu aplicación, que es el registro autorizado.

**La pausa es un valor de retorno.** Una ejecución interrumpida vuelve con normalidad con `isInterrupted()` a true: no hay nada que capturar. El Capítulo 22 sigue a partir de ahí.

**Una reentrega termina la misma ejecución.** Reintentar un trabajo tan caro suena a pagar dos veces. No lo es, gracias a la Sección 13.5: cada nodo completado es un paso confirmado. El ID de ejecución se acuñó junto con el registro, así que cada entrega de este trabajo nombra la misma ejecución, y `recoverFailed: true` le dice a un inicio que encuentra esa ejecución fallida (o todavía marcada como en curso por un proceso al que mataron, una vez caducada su concesión) que la continúe en lugar de empezar de nuevo. Los pasos confirmados se reproducen desde el almacén, no se ejecutan: la investigación y el borrador que pagó la primera entrega no se compran dos veces, y solo vuelve a ejecutarse el nodo que estaba en marcha cuando murió. Un `run()` simple también recupera una ejecución fallida, pero sustituye a aquella cuyo proceso fue matado, y empieza desde el primer nodo. Mientras la concesión de la entrega muerta siga vigente, el inicio se rechaza con `RunInFlightException`, y el trabajo se libera a sí mismo hasta que la concesión haya caducado.

Tres relojes lo hacen seguro. La concesión (`setLeaseTimeout(600)`: un flujo de trabajo simple no tiene ninguna concesión hasta que le fijas una, un agente trae por defecto los mismos diez minutos) debe durar más que el nodo individual más largo, para que una ejecución lenta nunca se tome por muerta. El `$timeout` del trabajo debe durar más que la ejecución más larga. Y el `retry_after` de la conexión de cola debe superar a `$timeout`: `DB_QUEUE_RETRY_AFTER=360` para un `$timeout` de 300, `REDIS_QUEUE_RETRY_AFTER` en una cola Redis. Laravel trae 90, lo que entrega a un segundo proceso un trabajo que sigue ejecutándose. Lo que el almacén no puede hacer es recordar una ejecución que se completó (sus registros se eliminan), así que un trabajo entregado de nuevo tras haber tenido éxito inicia una ejecución nueva; son los relojes los que evitan que ocurra.

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

Dos valores por defecto de `PusherChannel` conviene conocerlos antes de la primera ejecución. Envía los eventos en lotes de diez, y un lote parcial espera hasta llenarse o hasta que termine el segmento, de modo que un puñado de eventos de progreso llegaría todo al final: `batchSize: 1` en el trabajo es lo que hace que cada uno salga en cuanto se produce. Y un nombre de canal admite solo letras, dígitos y `-_=@,.;`. Un ID de flujo de trabajo que pasa a formar parte de uno no puede contener dos puntos, así que el estilo `t1:refund:42` de la Sección 18.3 necesita aquí otro separador: `t1.content.42`.

¿Prefieres Redis? Una factoría que devuelve `new RedisChannel($redis, "workflows:{$id}")` publica los mismos sobres en Redis Pub/Sub para un proceso que mantenga la conexión del navegador. ¿Prefieres la difusión propia de Laravel? `CallbackChannel` envuelve un closure por cada método del ciclo de vida, así que `onSend` puede llamar a `Broadcast::private(...)->as($event->type)->with($event->data)->sendNow()`. **`sendNow()`, nunca una difusión encolada.** Una difusión encolada pone tus actualizaciones de progreso en cola detrás del trabajo que las produce (con un solo proceso, un interbloqueo a cámara lenta) y con varios procesos las entrega desordenadas.

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

channel.bind('pusher:subscription_succeeded', function once() {
    channel.unbind('pusher:subscription_succeeded', once);   // it fires again on every reconnect
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
- Pasos duraderos, reproducidos cuando un trabajo se entrega de nuevo (13.5)
- Interrupción y persistencia (15.4)
- Persistencia en base de datos (18.4)
- Ejecución asíncrona (16.4)
- Adaptadores empujando hacia un transporte externo (7.5)
- `pcntl` y `posix` disponibles, así que las herramientas en paralelo funcionan (5.13)
- Inspector suscrito en el flujo de trabajo (23.3)

Esa última es la mala configuración con más probabilidad de morderte: no se monitoriza nada a menos que suscribas el oyente, y un proceso de cola es exactamente donde nadie nota que falta.

### Puntos clave

- Push, no pull: una factoría de adaptador más una factoría de canal, y el proceso simplemente llama a `run()`.
- Suscríbete primero y luego inicia la ejecución: Pusher y Redis no reproducen nada.
- `PusherChannel` envía sobres numerados en secuencia y fragmentables, en lotes de diez salvo que pases `batchSize: 1`; `@neuron-core/streaming` reordena, reensambla e informa de los huecos.
- El canal informa de finalización, pausa y fallo; recupera los resultados de la aplicación.
- Autoriza el canal por inquilino. Reserva el ID de ejecución y deja que el trabajo reintente: una reentrega termina la misma ejecución desde su último paso confirmado, siempre que `retry_after` supere a `$timeout`.

## 21.6 Desconexión y coste huérfano

### El problema que nadie menciona

Un usuario inicia una ejecución de 30 segundos. En el segundo cuatro cierra la pestaña.

Lo que ocurre después depende de dónde viva la ejecución. En un proceso de cola no ocurre nada en absoluto: el navegador ya no está y **el agente sigue ejecutándose.** Cada llamada al modelo que quede se factura. En un flujo de trabajo multiagente eso es una cantidad sustancial de dinero gastado en una salida que nadie leerá jamás. En una respuesta en transmisión ocurre lo contrario: la ejecución se corta a mitad de turno, y lo que ya había escrito decide si el mensaje siguiente del usuario recibirá respuesta.

Con poco volumen ambos son invisibles. A escala el primero es una partida de gasto y el segundo es un ticket de soporte.

### Qué le hace una desconexión a una respuesta en transmisión

Con el `ignore_user_abort=0` por defecto de PHP, tu bucle nunca se entera de que el cliente se ha ido. Se entera PHP, en la primera escritura tras la desconexión, y termina el script allí mismo. Ninguna línea posterior a ese `echo` se ejecuta: una comprobación de `connection_aborted()` al principio del bucle nunca se alcanza, el evento `done` nunca se envía, el código posterior al `foreach` nunca se ejecuta.

El motor sí se da cuenta. Una ejecución cuyo consumidor deja de extraer antes de que se haya asentado se registra como **fallida**, de inmediato, cuando la petición se cierra y el generador se destruye. No se queda marcada como en curso hasta que caduque la concesión de diez minutos del agente, así que el hilo no queda bloqueado para el mensaje siguiente.

Lo que se pierde es la respuesta. Si vale la pena tenerla con independencia de que alguien esté mirando, dilo en el controlador de la Sección 21.1, antes de devolver la respuesta:

```php
// The run now completes into the history even if the tab closes.
\ignore_user_abort(true);

return response()->stream(function () use ($stream) {
    foreach ($stream as $chunk) {
        if (! $chunk instanceof TextChunk || \connection_aborted()) {
            continue;   // nobody is reading: keep pulling, stop writing
        }

        // ... frame, echo and flush as in Section 21.1
    }

    // ... the done event
}, 200, [/* ... the same four headers */]);
```

Solo ahora `connection_aborted()` significa algo: el script sobrevive a la escritura fallida, y la función lo informa a partir de la iteración siguiente. El bucle sigue extrayendo, así que el turno termina y el usuario encuentra la respuesta completa cuando vuelve. Sustituye `continue` por `break` y estás de vuelta en el comportamiento por defecto, por elección: el motor da la ejecución por fallida cuando termina la petición y el generador se libera.

La otra manera de conservar la respuesta es no atar en absoluto la ejecución a la petición: la ejecución en cola de la Sección 21.5, que ningún navegador puede interrumpir.

**Una advertencia honesta:** elijas lo que elijas, los tokens generados antes de la desconexión se facturan. Terminar la ejecución limita el daño; no lo deshace.

### Por qué el mensaje siguiente puede fallar

La ejecución fallida en sí es inofensiva: el turno siguiente sobre el hilo la sustituye. Lo que importa es lo que el turno fallido ya había guardado.

Si el cliente se fue antes de que empezara la primera respuesta, no se guardó nada, y el mensaje siguiente simplemente se responde. Si se fue después de un paso de herramienta, la pregunta del usuario ya está en el historial. Un segundo mensaje de usuario justo después no es una conversación válida, así que el siguiente `chat()` o `stream()` lanza `ChatHistoryException: Invalid message sequence`, y para entonces ya ha sustituido a la ejecución fallida, lo único que se habría podido recuperar.

Así que termina primero el turno fallido. Eso es `recoverFailedTurn()`, de la Sección 18.4: haz `inspect()` de la ejecución del hilo, y si su estado es `Failed`, continúala con `run(ExecutionRequest::resume(expectedRunId: ..., expectedExecutionAttempt: ...))`. La ejecución se completa desde sus pasos confirmados (una herramienta que ya se ejecutó no se vuelve a ejecutar), su respuesta cae en el historial, y la pregunta nueva sigue entonces una conversación válida. Por eso todos los puntos de conexión de este capítulo lo llaman antes de iniciar un turno. No es gratis: termina todos los turnos fallidos, incluido el que no había guardado nada, así que cada pregunta abandonada cuesta una llamada al modelo por una respuesta que el usuario no esperó. Ese es el precio de un hilo que sigue siendo utilizable.

El `disconnect.php` del repositorio complementario ejecuta los tres casos uno al lado del otro: un cliente que se va antes de que se guarde nada, y el mensaje siguiente se responde; uno que se va después de un paso de herramienta, y el mensaje siguiente se rechaza con la `ChatHistoryException`; y lo mismo otra vez con el turno fallido terminado primero: el mensaje siguiente se responde, y la herramienta se ha ejecutado una sola vez en total.

Un caso que `recoverFailedTurn()` no puede ver: un proceso matado de golpe (sin memoria, el `request_terminate_timeout` de FPM) no ejecuta ningún destructor y no registra nada. Su ejecución sigue en `running`, y los turnos nuevos sobre el hilo se rechazan con `RunInFlightException` hasta que caduca la concesión. Si la pregunta se había guardado, el turno siguiente falla como arriba, y el `resetConversation()` de la Sección 18.4 es lo que queda.

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

- Una pestaña cerrada no detiene una ejecución en cola (sigues pagando) y corta a mitad de turno una en transmisión.
- Con el `ignore_user_abort=0` por defecto, PHP termina el script en la escritura siguiente; el motor da la ejecución por fallida de inmediato, y el hilo no queda bloqueado.
- `ignore_user_abort(true)`, o una ejecución en cola, conserva la respuesta.
- Un turno fallido que había guardado su pregunta bloquea el siguiente: `recoverFailedTurn()` antes de cada turno.
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
5. **Gestión de la desconexión.** `recoverFailedTurn()` antes de cada turno, y una elección que puedas defender entre dejar que una pestaña cerrada termine la ejecución y conservarla con `ignore_user_abort(true)`.

### Criterios de aceptación

- El primer token visible llega muy por debajo del segundo con un modelo local. Mídelo; no lo supongas.
- Hacer una pregunta que dispare una herramienta muestra la etiqueta amigable y luego la respuesta.
- Añadir una herramienta nueva sin añadir su etiqueta muestra «Working on it», no el nombre interno de la herramienta. Pruébalo deliberadamente.
- Cerrar la pestaña a mitad de respuesta deja una ejecución fallida, no un hilo bloqueado, y un mensaje nuevo en la misma conversación, enviado justo después, recibe respuesta en lugar de ser rechazado. Pruébalo una vez más con una pregunta que dispare una herramienta, cerrando la pestaña después de que la herramienta se haya ejecutado.
- `curl -N` transmite a través de todo la pila, no solo en local.

### La parte que la gente se salta

El requisito cuatro. Es tentador cantar victoria cuando funciona en `artisan serve`, donde no hay nginx ni proxy. El primer despliegue es donde la transmisión se rompe, y la bisección de la Sección 21.2 es la diferencia entre cinco minutos y una tarde.

Ejecuta los tres comandos `curl -N` contra tu entorno de staging real antes de dar este laboratorio por terminado.

### Ir más allá

Añade un botón de «parar». Abortar la petición desde el lado del navegador es la versión fácil, y la Sección 21.6 dice lo que cuesta: la ejecución falla y la respuesta parcial se pierde. La mejor mantiene abierta la conexión: envuelve el cliente HTTP del proveedor en `NeuronAI\HttpClient\StoppableHttpClient` con una closure que lea un indicador de la caché, levanta el indicador desde un punto de conexión de parada, y la respuesta en transmisión termina en su evento siguiente, con el texto escrito hasta entonces conservado en el historial. Después mide lo que ahorró: ejecuta el mismo prompt hasta el final, anota el recuento de tokens y compáralo con una ejecución detenida. Ese número es el argumento para construir el botón.
