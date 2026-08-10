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

## 7.2 stream() y events()

### La API

```php
use App\Neuron\MyAgent;
use NeuronAI\Chat\Messages\UserMessage;

$handler = MyAgent::make()->stream(new UserMessage('How are you?'));

foreach ($handler->events() as $chunk) {
    echo $chunk->content;
}

// I'm fine, thank you! How can I assist you today?
```

Tres pasos, y cada uno es un sitio donde la gente se equivoca:

**1. `stream()` en lugar de `chat()`.** Esto prepara el flujo de trabajo del agente para usar `StreamingNode` en vez de `ChatNode`: el tercer cambio de nodo de este libro, tras `ToolNode`/`ParallelToolNode` en la Sección 5.13 y `StructuredOutputNode` en la 6.3.

**2. `stream()` devuelve un gestor, no un generador.** No puedes iterarlo directamente.

**3. `events()` devuelve el generador.** Y produce **objetos**, no cadenas. `$chunk->content`, no `$chunk`.

::: {.callout .callout-warning}
[Cambio v2 → v3]{.callout-title}

Las versiones anteriores hacían transmisión de cadenas simples para el texto e instancias de mensaje para las operaciones de herramientas. La v3 introdujo clases de fragmento dedicadas. Todos los tutoriales antiguos que encuentres mostrarán la forma con cadenas:

```php
// WRONG for v3
foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
    echo $chunk;
}
```

Esta es la tercera ruptura significativa de v2 → v3 del libro, tras los namespaces y `getMessage()`. Es también la que con más frecuencia sobrevive en el código de ejemplo publicado, porque la forma rota sigue *pareciendo* correcta.
:::

### Los tipos de fragmento

Cuatro clases:

| Fragmento | Contiene |
|---|---|
| `TextChunk` | Un fragmento del texto de la respuesta |
| `ReasoningChunk` | Parte del resumen de razonamiento del modelo, solo en modelos de razonamiento |
| `ToolCallChunk` | El modelo solicitando la ejecución de una herramienta |
| `ToolResultChunk` | El resultado de la ejecución de una herramienta |

**Lo que recibes depende de tu agente.** Sin herramientas enganchadas no hay `ToolCallChunk` ni `ToolResultChunk`: puedes iterar esperando solo texto y razonamiento. Vale la pena saberlo antes de escribir lógica de ramificación que no necesitas.

### Obtener el mensaje final

Una vez completada la transmisión, el gestor sigue conservando el resultado ensamblado:

```php
$handler = MyAgent::make()->stream(...);

foreach ($handler->events() as $chunk) {
    // stream to the user
}

$message = $handler->getMessage();
echo $message->getContent();
```

Esto importa más de lo que parece. Haces transmisión al usuario *y* obtienes el `AssistantMessage` completo para persistirlo, registrarlo o pasarlo por una comprobación de moderación. No tienes que reensamblarlo tú desde los fragmentos, que es exactamente lo tedioso y propenso a errores que todo el mundo hace en su primera implementación de transmisión.

### Por qué objetos de fragmento en lugar de cadenas

Las notas de actualización del framework explican el razonamiento, y es una buena lección de diseño.

Transmitir de instancias de mensaje crudas acoplaba la aplicación al sistema interno de mensajes de NeuronAI. Las clases de fragmento dedicadas crean una frontera: el código de tu interfaz depende de un conjunto pequeño y estable de tipos de fragmento en lugar de las tripas internas de los mensajes. Esa separación es lo que hizo posible el sistema de adaptadores de transmisión (Sección 7.5), y significa que las tripas pueden evolucionar sin romper tu frontend.

Es un caso de manual de introducir un DTO en la frontera de una capa.

### Puntos clave

- `stream()` → gestor → `events()` → generador de objetos de fragmento.
- `$chunk->content`, no `$chunk`.
- Cuatro tipos de fragmento; cuáles recibes depende de si el agente tiene herramientas.
- `getMessage()` en el gestor te da después el mensaje completo ensamblado.

## 7.3 Transmisión desde la CLI

### El ejemplo

**`examples/06-streaming.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the Repository pattern and when using it is a mistake.';

$start   = \microtime(true);
$first   = null;

$handler = AssistantAgent::make()->stream(new UserMessage($prompt));

foreach ($handler->events() as $chunk) {
    $first ??= \microtime(true);

    echo $chunk->content;
    \flush();
}

$end = \microtime(true);

\printf(
    "\n\n[first token: %.2fs | total: %.2fs]\n",
    $first - $start,
    $end - $start
);
```

```bash
php examples/06-streaming.php
```

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
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Tools\Tool;

$handler = MyAgent::make()
    ->addTool(
        Tool::make(
            'get_server_configuration',
            'retrieve the server network configuration'
        )->addProperty(/* ... */)->setCallable(/* ... */)
    )
    ->stream(
        new UserMessage("What's the IP address of the server?")
    );

foreach ($handler->events() as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        echo "\n- Calling tool: " . $chunk->tool->getName();
        echo "\n- Input: " . json_encode($chunk->tool->getInputs());
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        echo "\n- Tool " . $chunk->tool->getName() . " completed";
        echo "\n- Result: " . $chunk->tool->getResult();
        continue;
    }

    echo $chunk->content;
}
```

Salida:

```
Let me retrieve the server configuration.
- Calling tool: get_server_configuration
- Tool get_server_configuration completed
The IP address of the server is: 192.168.0.10
```

### Qué llevan los fragmentos

Ambos fragmentos de herramienta contienen la **instancia de la herramienta**, que es más que un nombre:

- `$chunk->tool->getName()`
- `$chunk->tool->getInputs()` — los argumentos que eligió el modelo
- `$chunk->tool->getResult()` — en el fragmento de resultado

Tener disponibles los argumentos es lo que hace posible una visualización de progreso genuinamente informativa. No «trabajando…», sino «Buscando pedidos del cliente 4471».

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

foreach ($handler->events() as $chunk) {
    if ($chunk instanceof ToolCallChunk) {
        $name = $chunk->tool->getName();
        echo "\n" . ($labels[$name] ?? 'Working on it') . "...\n";
        continue;
    }

    if ($chunk instanceof ToolResultChunk) {
        continue; // never shown to the user
    }

    echo $chunk->content;
}
```

La lista de permitidos importa: `$labels[$name] ?? 'Working on it'` significa que una herramienta recién añadida degrada a un mensaje genérico en lugar de filtrar su nombre interno. El mismo razonamiento que `only()` frente a `exclude()` en la Sección 5.8: las listas de permitidos fallan de forma segura.

### El principio de experiencia de usuario

Una línea de progreso para una herramienta que tarda 200 ms es ruido visual. Una línea de progreso para una que tarda cuatro segundos es esencial.

Plantéate mostrar la actividad de las herramientas solo tras un breve retardo, para que las llamadas rápidas queden invisibles y las lentas se expliquen solas. Ese es el comportamiento de todo estado de carga bien diseñado, y aquí aplica directamente.

### Puntos clave

- Las herramientas transmiten automáticamente; recibes `ToolCallChunk` y `ToolResultChunk`.
- Los fragmentos llevan la instancia de la herramienta, incluidos los argumentos que eligió el modelo.
- Nunca muestres entradas ni resultados crudos de herramientas a los usuarios finales: mapea a etiquetas con un respaldo seguro.
- Muestra progreso solo para las herramientas lentas.

## 7.5 Adaptadores de transmisión y protocolos de interfaz

### El problema que resuelven los adaptadores

Tu agente produce fragmentos de NeuronAI. Tu frontend habla un protocolo: el formato de flujo de datos del SDK de IA de Vercel, o AG-UI. Sin adaptadores escribes la traducción a mano, incluidos los eventos de ciclo de vida de mensajes, el formateo de eventos y el seguimiento de IDs, y la reescribes cada vez que el protocolo se mueve.

### El diseño

Los adaptadores son traductores entre los eventos de transmisión internos de NeuronAI y un protocolo de frontend concreto. Pasa uno a `events()`:

```php
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;

$handler = MyAgent::make()->stream(new UserMessage('What is the square root of 144?'));

$stream = $handler->events(new AGUIAdapter());

foreach ($stream as $line) {
    echo $line;
}
```

Lo mismo para Vercel:

```php
use NeuronAI\Chat\Messages\Stream\Adapters\VercelAIAdapter;

$stream = $handler->events(new VercelAIAdapter());
```

**El código de tu agente no cambia.** El adaptador se sitúa en la frontera. Este es el mismo diseño guiado por interfaces del cambio de proveedor de la Sección 3.6, aplicado al lado de la salida: la arquitectura es consistente, no accidental.

### Un punto de conexión AG-UI completo

```php
use NeuronAI\Chat\Messages\Stream\Adapters\AGUIAdapter;
use NeuronAI\Chat\Messages\UserMessage;

$input = json_decode(file_get_contents('php://input'), true);

$messages = [];
foreach ($input['messages'] as $message) {
    if ($message['role'] === 'user') {
        $messages[] = new UserMessage($message['content']);
    }
}

$adapter = new AGUIAdapter(
    threadId: $input['threadId'],
    runId: $input['runId'],
);

foreach ($adapter->getHeaders() as $name => $value) {
    header("{$name}: {$value}");
}

$stream = MyAgent::make()->stream($messages)->events($adapter);

foreach ($stream as $line) {
    echo $line;
    flush();
}
```

Cuatro cosas que notar:

**Los clientes AG-UI hacen POST de una carga `RunAgentInput`.** No se limitan a abrir una conexión. Lleva `threadId`, `runId`, el historial de mensajes y más.

**Devuelve los identificadores.** Pasa `threadId` y `runId` al constructor para que el adaptador los devuelva en `RUN_STARTED` y `RUN_FINISHED`. Si los omites, el adaptador se inventa los suyos: aceptable para pruebas, incorrecto para un cliente real que espera correlacionar la transmisión con la ejecución que pidió.

**`getHeaders()` te da las cabeceras SSE.** Envíalas.

**`flush()` después de cada línea.** La advertencia de la Sección 7.3, y los documentos la repiten aquí con razón.

### El mapeo de eventos

| Fragmento de NeuronAI | Eventos AG-UI |
|---|---|
| Ciclo de vida de la ejecución | `RUN_STARTED`, `RUN_FINISHED` |
| `TextChunk` | `TEXT_MESSAGE_START`, `TEXT_MESSAGE_CONTENT`, `TEXT_MESSAGE_END` |
| `ReasoningChunk` | `REASONING_START`, `REASONING_MESSAGE_START`, `REASONING_MESSAGE_CONTENT`, `REASONING_MESSAGE_END`, `REASONING_END` |
| `ToolCallChunk` | `TOOL_CALL_START`, `TOOL_CALL_ARGS`, `TOOL_CALL_END` |
| `ToolResultChunk` | `TOOL_CALL_RESULT` |

### Dos limitaciones que enunciar con honestidad

**Solo herramientas del lado del servidor.** Las herramientas enganchadas a tu agente se ejecutan en tu servidor, y al cliente se le informa mediante los eventos `TOOL_CALL_*`. Las herramientas *definidas por el frontend* de AG-UI —listadas en el campo `tools` de `RunAgentInput` y ejecutadas por el cliente— no las gestiona el adaptador.

**Sin eventos de estado compartido.** El adaptador no emite `STATE_SNAPSHOT`, `STATE_DELTA` ni `MESSAGES_SNAPSHOT`, así que las funcionalidades de sincronización de estado de los clientes AG-UI no están disponibles a través de él.

Si estás evaluando CopilotKit o un frontend AG-UI similar, conoce estas dos lagunas antes de comprometerte con un diseño que dependa de ellas.

### Adaptadores propios

```php
interface StreamAdapterInterface
{
    public function transform(object $chunk): iterable;
    public function getHeaders(): array;
    public function start(): iterable;
    public function end(): iterable;
}
```

Cuatro métodos. `transform()` hace el trabajo; `start()` y `end()` gestionan el ciclo de vida del protocolo; `getHeaders()` suministra las cabeceras del transporte.

También puedes extender `SSEAdapter` cuando solo necesites cambiar la transformación.

### El caso de uso que conviene destacar

Los adaptadores pueden empujar hacia un transporte externo como Pusher. Eso significa que un agente ejecutándose **en un trabajo en segundo plano** puede transmitir su progreso a un navegador con el que no tiene conexión directa.

Esta es la respuesta a un problema que de otro modo parecería intratable: las ejecuciones largas de agentes pertenecen a un proceso de cola (la aritmética de latencia de la Sección 1.4, la restricción de `pcntl` de la 5.13), pero un proceso de cola no tiene conexión HTTP con el usuario. Un adaptador que empuja hacia un transporte websocket salva exactamente esa brecha.

El Capítulo 21 lo construye en Laravel.

### Puntos clave

- Los adaptadores traducen los fragmentos de NeuronAI a un protocolo de frontend; el código de tu agente no cambia.
- Los clientes AG-UI hacen POST de una carga: devuelve `threadId` y `runId`.
- Dos lagunas: sin herramientas definidas por el frontend, sin eventos de estado compartido.
- Un adaptador sobre un transporte websocket permite que un proceso de cola transmita a un navegador.

## Ejercicios del capítulo

1. **Mídelo.** Convierte un agente del Capítulo 5 de `chat()` a `stream()`. Mide el tiempo hasta el primer token de ambas formas y anota los dos números. Si la diferencia es pequeña, pregúntate por qué: un modelo local rápido con una respuesta corta genuinamente no necesita transmisión, y saberlo es tan útil como la funcionalidad.

2. **Muestra el trabajo.** Añade visualización del progreso de herramientas con una lista de permitidos de etiquetas y un respaldo seguro. Después añade una herramienta nueva sin añadir su etiqueta y confirma que degrada al mensaje genérico en lugar de filtrar su nombre interno.

3. **Elige un adaptador.** Esboza qué adaptador usarías para tu propia pila de frontend y decide si alguna de las dos limitaciones de AG-UI te afectaría. Si no estás seguro, esa es la respuesta que hay que averiguar antes de construir, no después.
