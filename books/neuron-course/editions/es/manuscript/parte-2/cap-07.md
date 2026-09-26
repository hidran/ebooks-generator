# Capítulo 7 — Transmisión

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch07`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch07), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 7.1 Por qué importa la transmisión

### El número de la Sección 1.4

Una llamada al modelo tarda de 1 a 4 segundos. Una ejecución de agente de cinco iteraciones con ejecución de herramientas alcanza los 10–20 segundos de reloj. Nadie espera 20 segundos ante una pantalla en blanco.

### Qué cambia realmente la transmisión

**No hace nada más rápido.** El tiempo total es idéntico. Cada token, cada llamada a herramienta, cada ida y vuelta tarda exactamente lo mismo.

**Cambia cuándo ve el usuario el primer token.** En lugar de 12 segundos de nada seguidos de una respuesta completa, ve texto apareciendo a los 800 milisegundos y continuando.

La espera percibida está dominada por el tiempo hasta el primer token, no por el tiempo hasta la finalización. Una respuesta que fluye durante 15 segundos se siente más rápida que una que bloquea durante 8. Esto está bien establecido en el diseño de interfaces en general, y es inusualmente pronunciado con texto porque el usuario puede empezar a leer mientras llega el resto.

### El segundo beneficio, que está infravalorado

La transmisión te permite mostrar **qué está haciendo el agente**, no solo lo que acabó diciendo.

Los tipos de fragmento de NeuronAI incluyen llamadas a herramientas y resultados de herramientas. Así que puedes renderizar:

```
Let me check that for you.
  → Looking up order #4471...
  → Found it. Checking refund eligibility...
The order is eligible for a full refund.
```

Ese es un producto completamente distinto de un spinner. El usuario ve el progreso, entiende por qué tarda y —algo importante— puede darse cuenta de que el sistema está trabajando en el problema correcto antes de que termine. La Sección 7.4 lo construye.

### Cuándo no transmitir

- **Trabajos por lotes y en segundo plano.** Nadie está mirando.
- **Salida estructurada.** Necesitas el objeto completo y validado; uno parseado a medias es inútil.
- **Respuestas muy cortas.** Transmitir de una respuesta de dos palabras añade complejidad para nada.
- **Cuando necesitas postprocesar la respuesta entera** antes de mostrarla: filtrado, redacción, formateo.

### Puntos clave

- La transmisión cambia la latencia percibida, no la real.
- El tiempo hasta el primer token es lo que sienten los usuarios.
- Transmitir de la actividad de las herramientas es una funcionalidad de producto, no solo un indicador de progreso.
- No para trabajo por lotes, salida estructurada ni respuestas que debas postprocesar.

## 7.2 stream() y sus fragmentos

### La API

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()->stream(new UserMessage('How are you?'));

foreach ($stream as $chunk) {
    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}

// I'm fine, thank you! How can I assist you today?
```

Tres cosas que notar, y cada una es un sitio donde la gente se equivoca:

**1. `stream()` en lugar de `chat()`, pero el mismo nodo.** Ambos verbos ejecutan el mismo `ChatNode`. `stream()` registra en la ejecución un indicador que le dice al nodo que llame al punto de conexión de transmisión del proveedor en lugar del que usa búfer, y que entregue cada pieza en cuanto llega. La transmisión es una elección de transporte, no un camino de ejecución distinto: por eso un middleware enganchado a `ChatNode` cubre ambos, y por eso todo lo que el Capítulo 5 dijo sobre herramientas sigue valiendo en mitad de la transmisión.

**2. `stream()` devuelve el generador.** No hay una segunda llamada: iteras lo que vuelve. Su tipo de retorno declarado es `Generator|AgentState`, y la rama `AgentState` solo se da cuando enganchas *a la vez* un adaptador de transmisión y un canal (Sección 7.5); en ese caso el agente transmite de forma anticipada al canal y te entrega el estado final. En el caso simple siempre es un generador. El análisis estático ve la unión, así que los scripts complementarios la acotan una vez con `\assert($stream instanceof Generator)`.

**3. Produce objetos, no cadenas, y no solo texto.** Filtra con `instanceof`. Hacer `echo` de `$chunk->content` para cada elemento funciona justo hasta el primer elemento que no es un fragmento de texto: una llamada a herramienta, un trozo de los argumentos de una herramienta o el `InterruptEvent` que marca una ejecución en pausa. Ninguno de ellos tiene una propiedad `content`.

::: {.callout .callout-warning}
[Código de transmisión antiguo]{.callout-title}

Dos formas anteriores de esta API sobreviven en tutoriales y repositorios de ejemplo:

```php
// Older form 1: plain strings
foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
    echo $chunk;
}

// Older form 2: a handler, then events()
foreach (AssistantAgent::make()->stream(new UserMessage($prompt))->events() as $chunk) {
    echo $chunk->content;
}
```

La primera forma es la más traicionera de las dos, porque su forma exterior coincide con la de este libro —sí iteras `stream()` directamente—, así que la línea rota parece casi correcta. Lo que está mal es el interior del bucle: cada elemento es un objeto, y solo algunos llevan texto.
:::

### Los tipos de fragmento

Todos bajo `NeuronAI\Chat\Messages\Stream\Chunks`, todos extienden `StreamChunk`, todos con un `toArray()`:

| Fragmento | Contiene |
|---|---|
| `TextChunk` | Un fragmento del texto de la respuesta, en `content` |
| `ReasoningChunk` | Parte del resumen de razonamiento del modelo, solo en modelos de razonamiento |
| `ToolArgumentChunk` | Un trozo de los argumentos de una llamada a herramienta que el modelo aún está escribiendo |
| `ToolCallChunk` | Una llamada a herramienta que el modelo decidió hacer |
| `ToolResultChunk` | El resultado de esa llamada, una vez ejecutada |
| `ImageChunk`, `AudioChunk` | Contenido multimedia generado, en los modelos que lo producen |

**Lo que recibes depende de tu agente y de tu proveedor.** Sin herramientas enganchadas no hay fragmentos de herramienta: puedes iterar esperando solo texto y razonamiento. `ToolArgumentChunk` solo aparece con proveedores que transmiten los argumentos de forma incremental; Gemini y Ollama los entregan de una pieza y nunca lo emiten. Vale la pena saberlo antes de escribir lógica de ramificación que no necesitas.

Además de fragmentos, el generador puede llevar otros dos tipos de objeto: el `InterruptEvent` que marca una ejecución en pausa a la espera de aprobación (Capítulo 15), y los eventos de progreso que un nodo de flujo de trabajo decide emitir (Capítulo 14). Un bucle que gestiona los tipos de fragmento que le interesan e ignora todo lo demás es correcto por construcción, y sigue siéndolo cuando el mes que viene añadas herramientas.

### Obtener el mensaje final

Cuando el bucle termina, el valor de retorno del generador es la ejecución terminada:

```php
$stream = MyAgent::make()->stream(...);

foreach ($stream as $chunk) {
    // stream to the user
}

$state = $stream->getReturn();
echo $state->getMessage()?->getContent();
```

`getReturn()` es PHP puro —todo generador tiene uno, disponible cuando ha terminado— y aquí devuelve el mismo `AgentState` que habría devuelto `chat()`. `getMessage()` admite `null` porque una ejecución que se pausó antes de completar alguna inferencia aún no tiene mensaje del asistente; tras una transmisión normal es la respuesta completa.

Esto importa más de lo que parece. Haces transmisión al usuario *y* obtienes el `AssistantMessage` completo para persistirlo, registrarlo o pasarlo por una comprobación de moderación. No tienes que reensamblarlo tú desde los fragmentos, que es exactamente lo tedioso y propenso a errores que todo el mundo hace en su primera implementación de transmisión.

### Por qué objetos de fragmento en lugar de cadenas

Las notas de actualización del framework explican el razonamiento, y es una buena lección de diseño.

Transmitir de instancias de mensaje crudas acoplaba la aplicación al sistema interno de mensajes de NeuronAI. Las clases de fragmento dedicadas crean una frontera: el código de tu interfaz depende de un conjunto pequeño y estable de tipos de fragmento en lugar de las tripas internas de los mensajes. Esa separación es lo que hizo posible el sistema de adaptadores de transmisión (Sección 7.5), y significa que las tripas pueden evolucionar sin romper tu frontend.

Es un caso de manual de introducir un DTO en la frontera de una capa.

### Puntos clave

- `stream()` devuelve el generador directamente; itéralo.
- Produce objetos de varios tipos: filtra con `instanceof TextChunk` antes de tocar `content`.
- Qué fragmentos recibes depende de si el agente tiene herramientas y de cómo transmite el proveedor.
- `getReturn()` te da el `AgentState` final, con el mensaje completo ensamblado.

## 7.3 Transmisión desde la CLI

### El ejemplo

**`examples/06-streaming.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the Repository pattern and when using it is a mistake.';

$start = \microtime(true);
$first = null;

$stream = AssistantAgent::make()->stream(new UserMessage($prompt));

// No adapter and no channel attached, so stream() returned a Generator.
\assert($stream instanceof Generator);

foreach ($stream as $chunk) {
    if (!$chunk instanceof TextChunk) {
        continue;
    }

    $first ??= \microtime(true);

    echo $chunk->content;
    \flush();
}

$end = \microtime(true);

\printf(
    "\n\n[first token: %.2fs | total: %.2fs]\n",
    ($first ?? $end) - $start,
    $end - $start,
);
```

```bash
php examples/06-streaming.php
```

Fíjate en dónde se para el reloj: en el primer `TextChunk`, no en el primer elemento. Un modelo de razonamiento puede pasar segundos emitiendo fragmentos de razonamiento antes de que aparezca una sola palabra de la respuesta, y es la respuesta lo que el usuario está esperando.

### La comparación que vale la pena medir

Ejecuta el mismo prompt dos veces —una con `chat()`, otra con `stream()`— y compara los tiempos.

Tiempo total: aproximadamente idéntico. Tiempo hasta la primera salida visible: 4,1 segundos frente a 0,7. *El trabajo tardó lo mismo; la espera no.*

Medir el tiempo hasta el primer token en el script vale las cuatro líneas extra. Convierte una afirmación en un número en tu propio hardware, con tu propio proveedor.

### El problema del almacenamiento en búfer

`flush()` está ahí por una razón, y la razón se hace mucho mayor en el Capítulo 21.

PHP bufferiza la salida. El servidor web también. El proxy inverso también. Cualquiera de ellos puede retener tus tokens cuidadosamente transmitidos y soltarlos en un solo bloque al final, momento en el que tienes toda la complejidad de la transmisión y ninguno de sus beneficios.

Desde la CLI, `flush()` suele bastar. En un contexto web también tienes que lidiar con:

- El ajuste `output_buffering` de PHP
- `ob_end_flush()` si ya hay un búfer abierto
- El `proxy_buffering` y el `fastcgi_buffering` de nginx
- Cualquier CDN o proxy delante de la aplicación

La propia documentación de AG-UI del framework incluye la advertencia: manda las cabeceras del protocolo y haz flush después de cada línea, o la transmisión puede quedarse atascada en los búferes de salida de PHP o en los proxies.

Se menciona aquí y se resuelve como es debido en el Capítulo 21. Quien se lo encuentra por primera vez en producción pierde un día con ello.

### Nota sobre las llamadas a herramientas en paralelo

La Sección 5.13 estableció que `pcntl` es solo de CLI. La transmisión es uno de los pocos contextos donde tienes ambas cosas disponibles a la vez: un agente de CLI puede transmitir *y* ejecutar herramientas en paralelo. Vale la pena saberlo, porque convierte al agente de CLI del Proyecto final A en un objetivo genuinamente capaz y no en un juguete.

### Puntos clave

- `flush()` después de cada fragmento.
- Mide el tiempo hasta el primer token; es el número que justifica la funcionalidad.
- El almacenamiento en búfer existe en cuatro capas de una pila web: Capítulo 21.

## 7.4 Transmisión con herramientas

### Las herramientas funcionan dentro de la transmisión

No hace falta nada especial. El agente gestiona las llamadas a herramientas en mitad de la transmisión y continúa hasta la respuesta final. Simplemente recibes tipos de fragmento adicionales.

### El patrón completo

```php
use App\Neuron\MyAgent;
use App\Neuron\Tools\ServerConfigurationTool;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolResultChunk;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()
    ->addTool(new ServerConfigurationTool())
    ->stream(
        new UserMessage("What's the IP address of the server?")
    );

foreach ($stream as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        echo "\n- Calling tool: " . $chunk->tool->getName();
        echo "\n- Input: " . json_encode($chunk->tool->getInputs()) . "\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        echo "- Tool " . $chunk->tool->getName() . " completed";
        echo "\n- Result: " . $chunk->tool->getResult() . "\n";
        continue;
    }

    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}
```

`ServerConfigurationTool` es una subclase corriente de `Tool` con la forma del Capítulo 5: un `$name` igual a `get_server_configuration`, una descripción y un `__invoke()` que devuelve la configuración. La versión complementaria responde con un valor fijo, así que el ejemplo no necesita red.

Salida:

```
- Calling tool: get_server_configuration
- Input: []
- Tool get_server_configuration completed
- Result: {"hostname":"app-01","ip":"192.168.0.10","gateway":"192.168.0.1"}
The IP address of the server is 192.168.0.10.
```

### Qué llevan los fragmentos

Ambos fragmentos de herramienta contienen un `ToolCall` en `$chunk->tool`: el registro de una invocación, no la herramienta ejecutable que registraste. Son datos simples:

- `$chunk->tool->getName()`
- `$chunk->tool->getInputs()` — los argumentos que eligió el modelo
- `$chunk->tool->getCallId()` — el identificador que empareja una llamada con su resultado
- `$chunk->tool->getResult()` — en el fragmento de resultado

Tener disponibles los argumentos es lo que hace posible una visualización de progreso genuinamente informativa. No «trabajando…», sino «Buscando pedidos del cliente 4471». El ID de llamada es lo que permite a una interfaz convertir in situ la línea «llamando» en una línea «hecho», en lugar de imprimir dos filas sin relación; y cuando el modelo llama a la misma herramienta dos veces en un turno, es lo único que distingue una llamada de la otra.

Si tu proveedor transmite los argumentos de las herramientas, los `ToolArgumentChunk` llegan antes del `ToolCallChunk`, cada uno con un `delta` de JSON crudo y parcial. Existen para una vista previa en vivo del tipo «el agente está escribiendo una consulta». Nunca los analices; espera al `ToolCallChunk`, que lleva las entradas completas.

### El punto de seguridad, dicho con firmeza

**No canalices las entradas y resultados crudos de las herramientas hacia los usuarios finales.**

El ejemplo de CLI anterior es una vista de depuración, y para eso es perfecto. En un producto de cara al usuario filtra:

- Identificadores internos y claves de base de datos
- Consultas SQL, revelando tu esquema
- Puntos de conexión de API y nombres de parámetros
- Cualquier cosa que haya en un mensaje de error

Mapea a etiquetas legibles por humanos:

```php
$labels = [
    'get_order_status'  => 'Looking up your order',
    'search_orders'     => 'Searching your order history',
    'get_refund_policy' => 'Checking the refund policy',
];

foreach ($stream as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        $name = $chunk->tool->getName();
        echo "\n" . ($labels[$name] ?? 'Working on it') . "...\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        continue; // never shown to the user
    }

    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}
```

La lista de permitidos importa: `$labels[$name] ?? 'Working on it'` significa que una herramienta recién añadida degrada a un mensaje genérico en lugar de filtrar su nombre interno. El mismo razonamiento que `only()` frente a `exclude()` en la Sección 5.8: las listas de permitidos fallan de forma segura. Lo mismo hace la última rama: todo lo que el bucle no reconoce se descarta, no se imprime.

### El principio de experiencia de usuario

Una línea de progreso para una herramienta que tarda 200 ms es ruido visual. Una línea de progreso para una que tarda cuatro segundos es esencial.

Plantéate mostrar la actividad de las herramientas solo tras un breve retardo, para que las llamadas rápidas queden invisibles y las lentas se expliquen solas. Ese es el comportamiento de todo estado de carga bien diseñado, y aquí aplica directamente.

### Puntos clave

- Las herramientas transmiten automáticamente; recibes `ToolCallChunk` y `ToolResultChunk`, y posiblemente antes deltas `ToolArgumentChunk`.
- Los fragmentos llevan un registro `ToolCall`: nombre, argumentos, ID de llamada y resultado.
- Nunca muestres entradas ni resultados crudos de herramientas a los usuarios finales: mapea a etiquetas con un respaldo seguro.
- Muestra progreso solo para las herramientas lentas.

## 7.5 Adaptadores de transmisión y protocolos de interfaz

### El problema que resuelven los adaptadores

Tu agente produce fragmentos de NeuronAI. Tu frontend habla un protocolo: el formato de flujo de datos del SDK de IA de Vercel, o AG-UI. Sin adaptadores escribes la traducción a mano, incluidos los eventos de ciclo de vida de mensajes, el formateo de eventos y el seguimiento de IDs, y la reescribes cada vez que el protocolo se mueve.

### El diseño

Un adaptador traduce los objetos de transmisión nativos de NeuronAI a un protocolo de frontend. Lo enganchas al agente con `setStreamAdapter()`, y a partir de ahí la misma llamada `stream()` produce **eventos de protocolo** en lugar de fragmentos:

```php
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;

$stream = MyAgent::make()
    ->setStreamAdapter(new AGUIAdapter(threadId: 'thread_123'))
    ->stream(new UserMessage('What is the square root of 144?'));

foreach ($stream as $event) {
    echo json_encode($event) . "\n";
}

// {"type":"RUN_STARTED","runId":"run_...","threadId":"thread_123"}
// {"type":"TEXT_MESSAGE_START","messageId":"msg_...","role":"assistant"}
// {"type":"TEXT_MESSAGE_CONTENT","messageId":"msg_...","delta":"The square root"}
// ...
```

Lo mismo para Vercel:

```php
use NeuronAI\Agent\Adapters\VercelAIAdapter;

$agent->setStreamAdapter(new VercelAIAdapter());
```

Cada elemento es un `NeuronAI\Workflow\Streaming\ProtocolEvent`: un `type` y un array `data` serializable a JSON, un objeto por evento en el cable. Los adaptadores incluidos viven bajo `NeuronAI\Agent\Adapters`, porque codifican conceptos del agente —llamadas a herramientas, aprobaciones—, mientras que el contrato que implementan pertenece a la capa de flujos de trabajo, donde cualquier flujo de trabajo puede usarlo.

**El código de tu agente no cambia.** El adaptador se sitúa en la frontera. Este es el mismo diseño guiado por interfaces del cambio de proveedor de la Sección 3.6, aplicado al lado de la salida: la arquitectura es consistente, no accidental.

Un adaptador tiene estado durante una transmisión: lleva la cuenta de los mensajes y las llamadas a herramientas abiertos. Crea una instancia nueva por petición y nunca compartas una entre transmisiones concurrentes.

### Eventos de protocolo, y dónde nacen los bytes

Fíjate en lo que el adaptador *no* hace: no produce líneas `data: ...`. El protocolo decide la forma de cada evento; el transporte decide cómo se convierte ese evento en bytes. Para Server-Sent Events, el borde HTTP enmarca la transmisión con `SSEEncoder`:

```php
use NeuronAI\Workflow\Streaming\SSEEncoder;

$lines = SSEEncoder::encode($stream);

foreach ($lines as $line) {
    echo $line; // data: {"type":"TEXT_MESSAGE_CONTENT",...}\n\n
    flush();
}

$state = $lines->getReturn(); // the final AgentState, still reachable
```

`encode()` envuelve el generador y reenvía su valor de retorno, así que el estado final sobrevive al enmarcado. `SSEEncoder::frame($event)` enmarca un único evento cuando necesitas eso.

La separación existe porque SSE es solo un destino. Un websocket, un stream de Redis o un canal de difusión quieren el *evento*, no una línea enmarcada, y mantener separadas las dos responsabilidades es lo que permite que el mismo adaptador los alimente a todos: los canales del final de esta sección dependen de ello.

### Un punto de conexión AG-UI completo

```php
use NeuronAI\Agent\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\SSEEncoder;

$input = json_decode(file_get_contents('php://input'), true);

$messages = $input['messages'];

// PHP 8.5: array_last() returns null for an empty list - no key juggling.
$last = array_last($messages);

if (($last['role'] ?? null) !== 'user') {
    http_response_code(400);
    exit('A new turn must end with a user message.');
}

$adapter = new AGUIAdapter(
    threadId: $input['threadId'],
    runId: $input['runId'] ?? null,
    messages: $messages,
    state: $input['state'] ?? [],
);

foreach ($adapter->getHeaders() as $name => $value) {
    header("{$name}: {$value}");
}

$stream = MyAgent::make(threadId: $input['threadId'])
    ->setStreamAdapter($adapter)
    ->stream(new UserMessage((string) $last['content']));

foreach (SSEEncoder::encode($stream) as $line) {
    echo $line;
    flush();
}
```

Cinco cosas que notar:

**Los clientes AG-UI hacen POST de una carga `RunAgentInput`.** No se limitan a abrir una conexión. Lleva `threadId`, `runId`, el historial de mensajes, las herramientas que el cliente puede ejecutar y el estado compartido.

**El hilo es la conversación, en ambos lados.** El adaptador exige `threadId` y lo devuelve en `RUN_STARTED` y `RUN_FINISHED`; el agente recibe el mismo valor mediante `make(threadId:)`, y ese hilo *es* la identidad de la ejecución del agente: la clave con la que una continuación posterior encuentra una ejecución en pausa. `runId` es el identificador por petición del cliente: pásalo y el adaptador lo devuelve; omítelo y el adaptador se inventa uno, lo cual es aceptable para pruebas e incorrecto para un cliente real que espera correlacionar la transmisión con la ejecución que pidió.

**Al agente solo le llega el último mensaje del usuario.** La copia del historial que tiene el cliente alimenta la instantánea `messages` del adaptador; no se vuelve a pasar al modelo. El historial de conversación del propio agente para ese hilo es el registro de referencia, lo que significa que este punto de conexión necesita un historial persistente (Capítulo 4) para recordar algo entre peticiones. Con el historial en memoria por defecto, cada petición es una conversación nueva. Para extraer ese mensaje se usa `array_last()`, nueva en PHP 8.5 junto a `array_first()`: devuelve el último elemento de un array sean cuales sean sus claves, o `null` si está vacío, así que una sola comprobación rechaza tanto una lista vacía como una que no termina con un turno del usuario.

**Una petición que no termina con un mensaje del usuario no es un turno nuevo.** Un mensaje de herramienta al final o un array `resume` es el cliente *continuando* una ejecución en pausa: entrega resultados de herramientas del frontend o una decisión de aprobación. Eso pasa por `submitInputs()` con el traductor de entradas del protocolo, no por `stream()`; el Capítulo 21 expone las formas de las peticiones y el Capítulo 22 construye el punto de conexión que responde a las aprobaciones. El 400 de arriba está ahí para que una continuación nunca se interprete en silencio como una pregunta nueva.

**`getHeaders()` te da las cabeceras SSE, y `flush()` va después de cada línea.** La advertencia de la Sección 7.3, y los documentos la repiten aquí con razón.

En código real, recuerda que `json_decode()` devuelve `null` ante un cuerpo mal formado; valida la carga antes de fiarte de cualquiera de sus claves.

### El mapeo de eventos

| Salida de NeuronAI | Eventos AG-UI |
|---|---|
| Ciclo de vida de la ejecución | `RUN_STARTED`, `RUN_FINISHED` |
| `TextChunk` | `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END` |
| `ReasoningChunk` | `REASONING_START`, `REASONING_MESSAGE_START`, `REASONING_MESSAGE_CONTENT`, `REASONING_MESSAGE_END`, `REASONING_END` |
| `ToolCallChunk` + `ToolResultChunk` | `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END`, `TOOL_CALL_RESULT` |
| Eventos de progreso del flujo de trabajo | `STEP_STARTED`, `STEP_FINISHED`, `ACTIVITY_SNAPSHOT`, `CUSTOM` |
| Ejecución en pausa a la espera de aprobación | `STATE_SNAPSHOT`, `MESSAGES_SNAPSHOT` y luego `RUN_FINISHED` con un resultado `interrupt` |
| Ejecución fallida | `RUN_ERROR` |

Una consecuencia de la fila de herramientas es fácil de pasar por alto: el adaptador guarda en búfer una llamada del lado del servidor y publica los cuatro eventos `TOOL_CALL_*` juntos, una vez que existe el resultado. Un cliente AG-UI se entera de una herramienta cuando ha terminado, no cuando empieza; así que, para una herramienta lenta, la línea «Checking the refund policy…» de la Sección 7.4 tiene que venir de otro sitio, como un evento de progreso.

La otra es la ejecución en pausa. Una transmisión suspendida no termina como una completada: `RUN_FINISHED` lleva `outcome: {type: "interrupt"}` con una interrupción `confirmation` por cada herramienta pendiente de aprobación, indexada por el ID de la llamada a herramienta. Un cliente que trate cada `RUN_FINISHED` como «la respuesta está completa» se equivocará. El Capítulo 15 trata la aprobación en sí; el Capítulo 22 responde a estas interrupciones por HTTP.

Los errores llegan al cable sin su mensaje. `RUN_ERROR` (y la parte `error` de Vercel) llevan un texto neutro, nunca `$exception->getMessage()`, para que un detalle de la pila no pueda filtrarse a un navegador. Sobrescribe el método protegido `errorMessage()` del adaptador si tus clientes deben saber más.

### Lo que cubre el adaptador, y la laguna que queda

**Las herramientas definidas por el frontend están soportadas.** Las herramientas que un cliente lista en `RunAgentInput` —ejecutadas en el navegador, no en tu servidor— pueden engancharse al agente como herramientas diferidas. Cuando el modelo llama a una, la ejecución se suspende, el adaptador publica la llamada, el cliente la ejecuta y devuelve el resultado en su siguiente petición, y la ejecución continúa. Esa petición es una continuación, no un turno nuevo, y el Capítulo 21 muestra cómo distinguir una cosa de la otra.

**El estado compartido se devuelve tal cual, no se sincroniza.** El adaptador lleva el `state` y los `messages` que envió el cliente y los devuelve como `STATE_SNAPSHOT` y `MESSAGES_SNAPSHOT` cuando una ejecución se pausa, para que la imagen del cliente siga completa. Nunca emite `STATE_DELTA`, y nada en el agente escribe en el estado de AG-UI. Si el diseño de tu frontend depende de que el agente modifique el estado compartido en vivo, esa es la laguna.

Si estás evaluando CopilotKit o un frontend AG-UI similar, conoce ese límite antes de comprometerte con un diseño que dependa de él.

### Adaptadores propios

```php
namespace NeuronAI\Workflow\Streaming\Adapter;

interface StreamAdapterInterface
{
    public function reset(): void;
    public function start(): iterable;
    public function transform(object $chunk): iterable;
    public function end(): iterable;
    public function interrupt(InterruptRequest $request): iterable;
    public function error(Throwable $error): iterable;
}
```

Cada iterable produce objetos `ProtocolEvent`. `transform()` hace el trabajo: un objeto nativo entra, cero o más eventos salen. `start()` abre el protocolo. Exactamente un terminal cierra cada segmento, y lo elige el agente según el resultado, nunca tu código: `end()` al completarse, `interrupt()` cuando la ejecución se pausa —para que el cliente sepa qué está esperando— y `error()` ante un fallo. `reset()` se llama antes de cada segmento, así que una sola instancia puede servir a una ejecución en pausa y a su continuación en el mismo proceso. Devuelve un iterable vacío desde cualquier método en el que tu protocolo no tenga nada que decir.

Uno pequeño, para un frontend casero que quiere texto y progreso de herramientas y nada más:

```php
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\Stream\Chunks\ToolCallChunk;
use NeuronAI\Workflow\Interrupt\InterruptRequest;
use NeuronAI\Workflow\Streaming\Adapter\StreamAdapterInterface;
use NeuronAI\Workflow\Streaming\ProtocolEvent;

final class ProgressAdapter implements StreamAdapterInterface
{
    public function reset(): void
    {
    }

    public function start(): iterable
    {
        return [];
    }

    public function transform(object $chunk): iterable
    {
        if ($chunk instanceof TextChunk) {
            yield new ProtocolEvent('delta', ['text' => $chunk->content]);
        }

        if ($chunk instanceof ToolCallChunk) {
            yield new ProtocolEvent('progress', ['tool' => $chunk->tool->getName()]);
        }
    }

    public function end(): iterable
    {
        yield new ProtocolEvent('done');
    }

    public function interrupt(InterruptRequest $request): iterable
    {
        yield new ProtocolEvent('paused', ['request' => $request->jsonSerialize()]);
    }

    public function error(Throwable $error): iterable
    {
        yield new ProtocolEvent('error', ['message' => 'Something went wrong.']);
    }
}
```

El mismo instinto de lista de permitidos de la Sección 7.4, impuesto en la frontera del protocolo: los resultados de las herramientas nunca salen del servidor porque el adaptador no tiene una rama para ellos. Las cabeceras HTTP no forman parte de la interfaz; si tu protocolo necesita alguna, declara tú mismo un `getHeaders()` en el adaptador, como hacen los incluidos.

Antes de escribir el tuyo, comprueba si `AgentChunkAdapter` ya te sirve. Es el vocabulario nativo de NeuronAI: un evento por fragmento, con el nombre de su tipo (`text`, `reasoning`, `tool-call`, `tool-result`, …) y el `toArray()` del fragmento como carga. Cuando el consumidor es tu propio frontend y no habla ningún protocolo estándar, suele ser todo lo que necesitas.

### El caso de uso que conviene destacar

Todo lo anterior supone que el código que itera el generador es también el que habla con el navegador: un controlador que mantiene abierta la conexión HTTP. A menudo no es así.

Una ejecución larga de un agente pertenece a un proceso de cola (la aritmética de latencia de la Sección 1.4, la restricción de `pcntl` de la 5.13), y un proceso de cola no tiene conexión HTTP con el usuario. Su salida simplemente se tiraría. Los **canales** resuelven exactamente eso. El adaptador decide la forma de la salida; un canal decide adónde va:

```php
use NeuronAI\Agent\Adapters\VercelAIAdapter;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Streaming\Channel\PusherChannel;

// Inside a queued job: the HTTP request returned long ago.
$state = MyAgent::make(threadId: $threadId)
    ->setStreamAdapter(new VercelAIAdapter())
    ->setChannel(new PusherChannel(
        client: $pusher,
        channel: "private-chat.{$threadId}",
    ))
    ->stream(new UserMessage($message));
```

Con un adaptador *y* un canal enganchados, `stream()` consume él mismo el pipeline, entrega cada evento de protocolo a través del canal en el momento en que ocurre y devuelve el `AgentState` final: la segunda rama del tipo de retorno de la Sección 7.2. Ningún bucle en tu código.

El framework incluye tres canales bajo `NeuronAI\Workflow\Streaming\Channel`: `PusherChannel` (recibe un cliente configurado del paquete opcional `pusher/pusher-php-server`, y funciona con servidores compatibles con Pusher como Reverb y Soketi), `RedisChannel` para Redis Pub/Sub, y `CallbackChannel`, que envuelve un closure para cualquier otra cosa: un broadcast de Laravel, un log, una prueba. Un canal necesita un adaptador para tener algo que enviar; engancha `AgentChunkAdapter` cuando el navegador no habla ningún protocolo de interfaz.

Dos propiedades en torno a las que diseñar. Un fallo del canal nunca hace fallar la ejecución: el agente sigue adelante e informa del error de transporte como un evento. Y la salida transmitida es efímera: nada de lo emitido se almacena ni se reproduce, así que un navegador que se reconecta a mitad de la ejecución se ha perdido lo que se ha perdido. El historial de conversación es el registro con el que la interfaz se reconcilia; nunca hagas que la corrección dependa de que un cliente reciba un elemento transmitido.

El Capítulo 21 lo construye en Laravel.

### Puntos clave

- `setStreamAdapter()` convierte la transmisión en objetos `ProtocolEvent` para AG-UI, el SDK de IA de Vercel o el vocabulario propio de NeuronAI; el código de tu agente no cambia.
- Los adaptadores deciden la forma, no los bytes: `SSEEncoder` enmarca los eventos en el borde HTTP y mantiene accesible el estado final.
- Los clientes AG-UI hacen POST de una carga: el hilo es la identidad del agente, devuelve `runId` y envía solo el nuevo mensaje del usuario.
- Una ejecución en pausa termina con un resultado `interrupt`, no con un final normal; las herramientas del frontend y las aprobaciones vuelven como continuaciones.
- Un canal entrega los mismos eventos cuando nadie sostiene la transmisión: así es como un proceso de cola transmite a un navegador.

## Ejercicios del capítulo

1. **Mídelo.** Convierte un agente del Capítulo 5 de `chat()` a `stream()`. Mide el tiempo hasta el primer token de ambas formas y anota los dos números. Si la diferencia es pequeña, pregúntate por qué: un modelo local rápido con una respuesta corta genuinamente no necesita transmisión, y saberlo es tan útil como la funcionalidad.

2. **Muestra el trabajo.** Añade visualización del progreso de herramientas con una lista de permitidos de etiquetas y un respaldo seguro. Después añade una herramienta nueva sin añadir su etiqueta y confirma que degrada al mensaje genérico en lugar de filtrar su nombre interno.

3. **Elige un adaptador.** Esboza qué adaptador usarías para tu propia pila de frontend y decide si la laguna de estado compartido de AG-UI te afectaría. Después decide quién sostiene la transmisión: la petición HTTP o un proceso de cola con un canal. Si no estás seguro, esa es la respuesta que hay que averiguar antes de construir, no después.
