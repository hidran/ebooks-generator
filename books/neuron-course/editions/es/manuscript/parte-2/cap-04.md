# Capítulo 4 — Mensajes y memoria

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

El chat de CLI persistente del Laboratorio 2 está en [`chapters/Ch04`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch04), en el repositorio complementario: `PersistentAgent.php` y `run/chat-loop.php`. Como todos los ejemplos de ahí, se ejecuta contra un Ollama local sin clave de API.
:::

## 4.1 El modelo de mensajes

NeuronAI tiene una capa de mensajes unificada —roles, bloques de contenido, metadatos— y es la pieza que hace que el cambio de proveedor funcione de verdad en lugar de solo aparentarlo.

### Por qué existe una capa de mensajes unificada

Cada proveedor tiene su propia forma de petición y de respuesta. OpenAI, Anthropic, Gemini y Ollama difieren en cómo representan los roles, cómo adjuntan imágenes, cómo devuelven las llamadas a herramientas y cómo exponen los rastros de razonamiento.

La respuesta de NeuronAI es una única abstracción de mensaje que se proyecta sobre todos ellos. Esto es lo que hace que la Sección 3.6 sea algo más que un truco de fiesta: el cambio funciona porque la capa de mensajes absorbe las diferencias. Sin ella, «cambia una línea para cambiar de proveedor» sería falso en el momento en que adjuntaras una imagen o leyeras una llamada a una herramienta.

### Qué es un mensaje

Tres partes:

- **Rol** — quién habla: user, assistant o system. Las instrucciones del agente viajan como un `SystemMessage`; una llamada a herramienta es un mensaje assistant especializado (`ToolCallMessage`) y su resultado un mensaje user especializado (`ToolResultMessage`)
- **Bloques de contenido** — la carga útil real
- **Metadatos** — información adicional de la respuesta del proveedor, como el uso de tokens

### Bloques de contenido

Esta es la parte que a la mayoría se le escapa. Un mensaje no contiene una cadena. Contiene una **lista ordenada de bloques de contenido**, cada uno implementando `ContentBlockInterface`. NeuronAI ofrece tipos de bloque para texto, razonamiento, imagen, archivo, audio y vídeo —más el bloque de sistema del que están hechas las instrucciones (Sección 3.5)— y proyecta cada uno automáticamente al formato correcto de cada proveedor.

Pasar una cadena al constructor simplemente crea el primer bloque de texto:

```php
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;

// A string constructor argument becomes the first TextContent block
$message = new UserMessage('Hi');

$message->addContent(new TextContent('My name is John.'));
$message->addContent(new TextContent('Answer as a professional concierge.'));

echo $message->getContent();
// Hi My name is John. Answer as a professional concierge.

$blocks = $message->getTextBlocks();
```

Ahora `getContent()` cobra sentido: une todos los bloques de texto en una sola cadena, separados por espacios, y devuelve `null` cuando el mensaje no tiene texto alguno. Es una comodidad, no la estructura subyacente.

### Leer una respuesta como es debido

```php
$response = MyAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage('...'))
    ->getMessage();

// Convenience: all text blocks joined
echo $response?->getContent();
```

Pero con un modelo de razonamiento, la respuesta lleva más que texto:

```php
use NeuronAI\Chat\Messages\ContentBlocks\ReasoningContent;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;

foreach ($response?->getContentBlocks() ?? [] as $block) {
    echo match ($block::class) {
        ReasoningContent::class => "Reasoning: {$block->content}\n\n",
        TextContent::class      => $block->content,
        default                 => '',
    };
}
```

NeuronAI captura automáticamente los pasos de razonamiento del modelo como un bloque distinto, y `getContent()` lo deja fuera deliberadamente. Si solo llamas a `getContent()`, nunca los ves; `$response->getReasoning()` es el atajo cuando quieres solo ese bloque. Para depurar un agente que tomó una decisión extraña, el bloque de razonamiento suele ser la respuesta.

### Construir una conversación a mano

A veces ya tienes una conversación —de tu propia base de datos o de una importación— y necesitas sembrar el agente con ella. Pasa un array a `chat()`:

```php
use NeuronAI\Chat\Enums\MessageRole;
use NeuronAI\Chat\Messages\Message;

$message = MyAgent::make()
    ->setThreadId('demo')
    ->chat([
        new Message(MessageRole::USER, 'Hi, my company is called Inspector.dev'),
        new Message(MessageRole::ASSISTANT, 'Great, how can I assist you today?'),
        new Message(MessageRole::USER, 'What is the name of the company I work for?'),
    ])
    ->getMessage();

echo $message?->getContent();
// You work for Inspector.dev
```

El último mensaje del array se trata como el más reciente. Esta es la vía de escape para cualquier situación en la que el propio componente de historial de NeuronAI no sea donde vive tu conversación: un esquema heredado, la exportación de otro sistema, una sesión reconstruida.

### Anticipo de multimodalidad

Adjuntar un documento usa el mismo mecanismo: otro bloque de contenido.

```php
use NeuronAI\Chat\Messages\ContentBlocks\FileContent;
use NeuronAI\Chat\Enums\SourceType;

$message = new UserMessage('Summarize this document');

$message->addContent(
    new FileContent(
        content: base64_encode(file_get_contents(__DIR__ . '/invoice.pdf')),
        sourceType: SourceType::BASE64,
        mediaType: 'application/pdf',
    )
);
```

`SourceType` admite `BASE64`, `URL` e `ID`. Ese tercero importa para el coste: muchos proveedores te permiten subir un archivo una vez a su plataforma y luego referenciarlo por ID, lo que evita volver a subir la carga en cada iteración del bucle del agente. Dada la aritmética de tokens de la Sección 1.4, eso supone un ahorro sustancial en cualquier ejecución de varios pasos que implique un documento. El Capítulo 8 lo cubre como es debido.

::: {.callout .callout-warning}
[Adjuntos en tutoriales antiguos]{.callout-title}

Los tutoriales escritos para versiones anteriores adjuntan contenido multimedia con `addAttachment(new Image($url, ...))`. Esa llamada aquí no existe; el contenido multimedia es un bloque de contenido, como arriba. Relacionado: la documentación es inconsistente con los nombres de las clases de bloque —`TextBlock`/`FileBlock` aparecen en algunos sitios donde las clases publicadas son `TextContent`/`FileContent`—, y un ejemplo importa `AudioContent` mientras instancia `FileContent`.
:::

### Puntos clave

- Un mensaje es rol + bloques de contenido + metadatos; no una cadena.
- `getContent()` une los bloques de texto; `getContentBlocks()` te da todo, incluido el razonamiento.
- Pasa un array de objetos `Message` para sembrar una conversación existente.
- La capa de mensajes unificada es la razón por la que el cambio de proveedor sobrevive al contacto con imágenes, archivos y llamadas a herramientas.

## 4.2 El modelo no tiene memoria

La ausencia de estado es una restricción de diseño, no una limitación que haya que sortear. Esta sección va de interiorizarla, porque casi toda la confusión sobre la «memoria» se disuelve en cuanto lo haces.

### La demostración

Toma el `AssistantAgent` del Laboratorio 1 y pregúntale algo que no puede saber:

```php
use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$message = AssistantAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage("What's my name?"))
    ->getMessage();

echo $message?->getContent();
// I'm sorry, I don't know your name.
```

Ahora conserva la misma instancia:

```php
$agent = AssistantAgent::make()->setThreadId('demo');

$agent->chat(new UserMessage('Hi, my name is Valerio!'));

$message = $agent->chat(new UserMessage('Do you remember my name?'))->getMessage();
echo $message?->getContent();
// Sure, your name is Valerio!
```

La lectura obvia —«el agente aprendió mi nombre»— es errónea, y corregirla es el objetivo de esta sección.

### Qué ocurrió realmente

La segunda llamada envió esto al proveedor:

```
system:    <instructions>
user:      Hi, my name is Valerio!
assistant: Hi Valerio, nice to meet you...
user:      Do you remember my name?
```

El modelo no recordó nada. **Tu proceso reenvió la transcripción.** No hay sesión del lado del proveedor, ni registro de usuario, ni nada persistido entre peticiones. El modelo lee la conversación entera de nuevo, cada vez, y responde como si recordara.

El componente de NeuronAI que reenvía la transcripción es `ChatHistory`, y la lee de un *almacén de mensajes*: aquí el predeterminado, que vive en la memoria de ese único objeto agente. Eso es todo lo que significa «memoria» en esta capa.

### Cuatro consecuencias que conviene enunciar

**1. La memoria cuesta dinero en cada turno.**
El turno veinte reenvía diecinueve intercambios anteriores. Este es el mecanismo detrás de la tabla de costes de la Sección 1.4, y es por lo que las conversaciones largas se encarecen aunque los mensajes individuales sean cortos.

**2. La memoria está acotada por la ventana de contexto.**
No es una base de datos que crece. Es un búfer con un techo rígido. Algo tendrá que descartarse tarde o temprano, y la única pregunta es qué y cómo: Sección 4.4.

**3. La memoria está enteramente bajo tu control.**
Lo cual es liberador en cuanto lo aceptas. Puedes editar el historial, inyectar un resumen, descartar turnos irrelevantes o mantener un hecho fijado permanentemente a nivel de sistema. Nada es sagrado; es tu array.

**4. La ausencia de estado es lo que hace fácil el escalado horizontal.**
Cualquier servidor web puede atender cualquier petición, siempre que pueda cargar la transcripción. No hay afinidad de sesión con un proveedor. Guarda los mensajes en almacenamiento compartido y cualquier nodo puede continuar cualquier conversación. Es una ventaja arquitectónica genuina, y es inusual que una funcionalidad con apariencia de estado escale con tanta limpieza.

### El modelo mental que conviene conservar

El modelo es una **función pura**: entra la transcripción, sale el siguiente mensaje. Todo lo que parece memoria, persistencia de personalidad o aprendizaje es tu código eligiendo qué entra en la transcripción.

Todas las técnicas del resto de este libro —recorte del historial, resumen, RAG, almacenes de memoria a largo plazo— son respuestas distintas a una sola pregunta: **¿qué ponemos en la transcripción?**

### Puntos clave

- No hay sesión del lado del servidor; la transcripción se reenvía en cada turno.
- La memoria cuesta tokens en cada turno y está limitada por la ventana de contexto.
- El historial es tu array: editable, inyectable, reemplazable.
- El modelo es una función pura de la transcripción.

## 4.3 ChatHistory y almacenes de mensajes

### La interfaz

```php
NeuronAI\Chat\History\MessageStoreInterface
```

La memoria de sesión son dos clases con dos tareas. `ChatHistory` es concreto, y nunca lo construyes tú: cada vez que una ejecución arranca o se reanuda, el agente abre uno para su hilo, y ese objeto carga la conversación, la mantiene dentro de la ventana de contexto y escribe los mensajes nuevos. El lugar donde se guardan los mensajes es un **almacén de mensajes** —cualquier cosa que implemente la interfaz de arriba—, y esa es la parte que eliges tú.

Lo eliges implementando `messageStore()` en tu agente, o pasando una instancia a `setMessageStore()`; el tamaño de la ventana lo fijas con `contextWindow()` o `setContextWindow()` (Sección 4.4). Un setter, una vez llamado, prevalece sobre el método. Si no haces nada de esto, el valor por defecto es un almacén en memoria y una ventana de 50.000 tokens.

El historial es un servicio que usan los nodos del agente, no parte del estado de la ejecución: `ChatNode` lee de él la transcripción y le añade mensajes, y la transcripción nunca se copia en el `AgentState` que devuelve `chat()`. Esa separación importa cuando las ejecuciones se vuelven duraderas (Capítulo 15). El estado guardado de una ejecución en pausa sigue siendo pequeño por mucho que crezca la conversación, y la conversación vive en un único lugar: el almacén.

::: {.callout .callout-warning}
[Código de historial en tutoriales antiguos]{.callout-title}

Los tutoriales escritos para versiones anteriores construyen el propio historial —un `FileChatHistory`, un `SQLChatHistory`— en un método `chatHistory()` del agente. Esas clases ya no existen, y el fallo es silencioso: nada llama a un método llamado `chatHistory()`, así que el agente se carga, responde y guarda la conversación en el almacén en memoria por defecto. Si una conversación no sobrevive a un reinicio, busca primero ese método.
:::

### ¿Qué conversación? El ID de hilo

Un historial pertenece siempre a una conversación —un **hilo**— y algo tiene que decir cuál. En NeuronAI ese algo es el agente, no el almacén:

```php
$agent = SupportAgent::make(workflowId: $threadId);
```

Un almacén no tiene hilo propio. Cada método de la interfaz recibe el ID de hilo como argumento, de modo que un solo almacén sirve a todas las conversaciones, y es el agente quien aporta el ID: abre su historial sobre el almacén *para su propio hilo*. La identidad entra por un único sitio, el punto de llamada que sabe realmente de qué conversación trata esta petición, y nunca dentro de la clase que solo sabe dónde se guardan las conversaciones.

Es el mismo ID del que hablaba la Sección 2.3: el ID de hilo es también el ID del flujo de trabajo de la ejecución del agente, y por eso el argumento del constructor se llama `workflowId:`. `setThreadId()`, de la Sección 3.4, fija el mismo valor después de la construcción. Cuando en el Capítulo 15 una ejecución se pause a la espera de una aprobación humana, el punto de conexión que la reanude no necesitará más que el ID de hilo para encontrarla.

De ahí se siguen dos reglas, y ambas se hacen cumplir:

- **Un agente sin hilo se niega a funcionar.** El framework nunca genera un ID. Llama a `chat()`, `getChatHistory()` o `resetConversation()` en un agente sin vincular y obtienes una `AgentException` —*"This agent has no thread ID: bind one with setThreadId() first."*— en lugar de una conversación guardada en silencio bajo una clave que nadie eligió.
- **Un agente se vincula una sola vez.** Fijar de nuevo el mismo ID es inofensivo; fijar uno distinto lanza una excepción, en lugar de escribir en silencio el resto de la conversación en otro hilo. Para atender otra conversación, construye otro agente, o llama a `$agent->for($otherThreadId)`, que devuelve una copia vinculada a ese hilo.

Una clase de agente con constructor propio debe seguir llamando a `parent::__construct()`: pásale el ID de hilo, o vincula el hilo después con `setThreadId()` o `for()`.

::: {.callout .callout-warning}
[El ID de hilo es entrada del usuario]{.callout-title}

Lo que pases como `workflowId:` selecciona qué conversación se carga, se amplía y se reanuda. Si llega en una petición —un segmento de URL, un campo de formulario—, comprueba que el usuario actual es el dueño de ese hilo antes de construir el agente con él. El framework no hace ningún control de acceso; basta con que falte una comprobación de propiedad para que cualquier usuario pueda leer la conversación de cualquier otro.
:::

### InMemoryMessageStore

```php
use NeuronAI\Chat\History\InMemoryMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;

protected function messageStore(): MessageStoreInterface
{
    return new InMemoryMessageStore();
}
```

Un array por hilo, en la memoria del proceso. Es el valor por defecto, así que el método de arriba solo escribe de forma explícita lo que ya hace un agente sin `messageStore()`: el `AssistantAgent` del Laboratorio 1, por ejemplo. El almacén pertenece al objeto agente que lo creó: conserva el objeto y la conversación continúa, como en la Sección 4.2; construye un segundo agente con el mismo ID de hilo y empieza vacío, porque tiene un almacén propio. Correcto para: scripts de una sola ejecución, puntos de conexión de API sin estado donde el historial lo llevas tú, y pruebas.

Recuerda que en una petición web normal PHP muere al terminar la respuesta. Un almacén en memoria en un contexto web significa **ninguna memoria entre peticiones**, lo cual es una sorpresa genuinamente frecuente para desarrolladores acostumbrados a entornos de ejecución de larga vida.

### FileMessageStore

```php
use NeuronAI\Chat\History\FileMessageStore;

protected function messageStore(): MessageStoreInterface
{
    return new FileMessageStore(directory: '/home/app/storage/neuron');
}
```

`directory` es una ruta absoluta, que se crea en la primera escritura si no existe. Cada hilo es un archivo JSON dentro de ella, `neuron_<thread>.chat`, que toma su nombre del ID de hilo que le pasa el agente, codificado como en una URL, de modo que un ID nunca puede nombrar una ruta fuera del directorio. Usa un ID de usuario como hilo para una conversación por usuario, o un ID de hilo generado para varias.

Correcto para: herramientas de CLI, aplicaciones de un solo servidor, prototipos. No correcto para: despliegues multiservidor sin almacenamiento compartido, ni para procesos concurrentes; cada escritura reemplaza el archivo entero, y dos procesos que escriban en el mismo hilo perderán mensajes. Hay además una trampa más cercana: el nombre del archivo conserva las mayúsculas y minúsculas del ID de hilo, así que en un sistema de archivos que no distingue mayúsculas de minúsculas —el valor por defecto en macOS y Windows— `user-Alice` y `user-alice` son un solo archivo y una sola conversación.

### SQLMessageStore

Crea primero la tabla. Una fila por mensaje: `id` ordena el hilo, y `message_id` es la identidad propia del mensaje, única dentro de su hilo. Esta es la tabla para MySQL y MariaDB:

```sql
CREATE TABLE chat_messages (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  thread_id VARBINARY(255) NOT NULL,
  message_id VARBINARY(64) NOT NULL,
  role VARCHAR(32) NOT NULL,
  content LONGTEXT NULL,
  meta LONGTEXT NULL,
  archived_at DATETIME NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  UNIQUE INDEX idx_thread_message (thread_id, message_id)
);
```

`VARBINARY` en las dos columnas de ID es deliberado. Los IDs de hilo y de mensaje deben compararse byte a byte, y las intercalaciones por defecto de MySQL y MariaDB ignoran mayúsculas y acentos: declara esas columnas como `VARCHAR` y `user-Alice` y `user-alice` leerán, y borrarán, los mensajes el uno del otro. PostgreSQL y SQLite comparan el texto de forma exacta, así que allí ambas son simples `VARCHAR`, y al resto de la tabla le bastan los ajustes habituales de dialecto: `BIGSERIAL` o `INTEGER PRIMARY KEY AUTOINCREMENT` para `id`, tipos `TEXT` y `TIMESTAMP`, ninguna cláusula `ON UPDATE` y un simple `UNIQUE (thread_id, message_id)`.

```php
use NeuronAI\Chat\History\SQLMessageStore;

protected function messageStore(): MessageStoreInterface
{
    return new SQLMessageStore(
        pdo: new \PDO('mysql:host=localhost;dbname=DB;charset=utf8mb4', 'user', 'pass'),
        table: 'chat_messages',
    );
}
```

Recibe un `PDO` normal, así que funciona en cualquier aplicación PHP con independencia del framework. En Laravel le pasarías `\DB::connection()->getPdo()`; en Symfony, `$connection->getNativeConnection()` de una conexión de Doctrine.

Como cada mensaje es su propia fila —`role`, los bloques de contenido como JSON en `content`, todo lo demás (uso, llamadas a herramientas, metadatos) como JSON en `meta`—, la tabla es útil para el resto de tu aplicación, no solo para el agente: informes por mensaje, tareas de retención, un panel de soporte que liste conversaciones. Puedes añadir columnas —una clave externa a tu tabla de usuarios, por ejemplo— siempre que admitan nulos y se mantenga la estructura base. `archived_at` se explica en la Sección 4.4.

### EloquentMessageStore

Cubierto por completo en el Capítulo 18, se lista aquí para que el mapa esté completo:

```php
new EloquentMessageStore(modelClass: ChatMessage::class);
```

La misma forma de tabla que el almacén SQL, la misma indiferencia hacia los hilos: la clase del modelo es lo único que necesita saber.

### Elegir

| Almacén | Úsalo cuando | Evítalo cuando |
|---|---|---|
| InMemory | Scripts, puntos de conexión sin estado, pruebas | Necesitas persistencia |
| File | Herramientas de CLI, un solo servidor, prototipos | Multiservidor, procesos concurrentes |
| SQL | Cualquier framework, producción, multiservidor | No tienes base de datos |
| Eloquent | Laravel con relaciones y scopes | No estás en Laravel |

El Laboratorio 2, al final de este capítulo, construye un chat de CLI persistente sobre `FileMessageStore`.

### Puntos clave

- Un único `ChatHistory` concreto, cuatro almacenes de mensajes: InMemory, File, SQL, Eloquent.
- Un almacén no lleva ningún hilo. Dale al agente `make(workflowId: ...)` o `setThreadId()`, y él abrirá el historial para ese hilo; sin uno, se niega a ejecutarse. El ID de hilo es también el ID del flujo de trabajo de la ejecución.
- Autoriza el ID de hilo antes de usarlo: selecciona de quién es la conversación que se carga.
- En una petición web, en memoria significa ninguna memoria entre peticiones.
- `SQLMessageStore` recibe un PDO normal, guarda una fila por mensaje y funciona en cualquier framework.

## 4.4 Ventana de contexto y recorte

### El error que esto previene

El fallo de producción más común en la IA conversacional:

> «Funciona bien, y luego, a partir de unos treinta mensajes, empieza a lanzar errores.»

La transcripción creció por encima del límite de contexto del modelo. Un proveedor en la nube rechaza la petición: no la trunca por ti, devuelve un error. Ollama falla al revés: trunca el prompt a su `num_ctx` y responde con lo que queda, sin ningún error.

El `ChatHistory` de NeuronAI previene ambos recortando automáticamente. Sigue el uso de tokens a partir de las respuestas del proveedor y, cuando la conversación ya no cabe en la ventana configurada, quita mensajes del principio de lo que envía al modelo.

«Quita de lo que envía» es una formulación deliberada. El recorte nunca borra. El historial le pide a su almacén que archive lo que ha quitado, y todos los almacenes lo hacen: una marca de tiempo `archived_at` en la fila (Sección 4.3) o en la entrada del archivo, un contador en memoria. El modelo ve el hilo recortado; `loadAll()` en el almacén sigue devolviendo la transcripción completa, para auditoría, analítica, una política de retención o una pantalla que recorra la conversación hacia atrás. `flushAll()` es la única operación que borra de verdad un hilo, mensajes archivados incluidos.

### La regla del 5–10 %

De la documentación, y vale la pena memorizarla porque es precisa y fácil de equivocar:

**Configura la ventana de contexto entre un 5 y un 10 % por debajo del límite real del modelo.**

| Límite del modelo | Configura |
|---|---|
| 32K | 29.000 |
| 128K | 118.000 |
| 200K | 185.000 |
| 1M | 920.000 |

### Por qué el margen no es superstición

El recortador no corta sin más en el mensaje donde se alcanza el límite. Un historial debe empezar con un mensaje del usuario, así que un corte solo puede caer al inicio de un turno. Cuando el corte más pequeño que basta cae dentro de un turno, el recortador conserva ese turno entero mientras el resultado no pase de un 5 % por encima de la ventana, y solo más allá corta en el turno siguiente. El último turno se conserva por grande que sea.

La ventana es, pues, un objetivo que el recortador puede rebasar un poco, con tal de no tirar un largo intercambio con herramientas para ahorrar unos pocos tokens. Configura exactamente en el límite del modelo y esa tolerancia no tendrá adónde ir, y podrás desbordarte igualmente. El margen es lo que le permite elegir una frontera sensata en lugar de una mecánica.

### Dónde va

```php
protected function contextWindow(): int
{
    return 185_000;
}
```

La ventana pertenece al agente, no al almacén: sea cual sea el almacén que hayas elegido, se fija aquí, o con `setContextWindow()` desde fuera. Si la omites obtienes 50.000 tokens: más de lo que admite un modelo local de 32K. Los guiones bajos en los literales numéricos son una funcionalidad de PHP 7.4+ y hacen estos valores mucho más fáciles de leer de un vistazo: úsalos.

### Configúralo por modelo, no por proyecto

Este es el error contra el que conviene advertir explícitamente. Si tu proveedor es configurable (Sección 3.6), tu límite de contexto también lo es. Un valor escrito a fuego para un modelo de 200K se vuelve incorrecto en el momento en que alguien pone `NEURON_PROVIDER=ollama` y obtiene un modelo local de 32K.

Dedúcelo:

```php
// src/ProviderFactory.php
public static function contextWindow(?string $driver = null): int
{
    $driver ??= env('NEURON_PROVIDER', 'ollama');

    return (int) match ($driver) {
        'anthropic' => 185_000,
        'openai'    => 118_000,
        'gemini'    => 920_000,
        'mistral'   => 118_000,
        'ollama'    => 29_000,
        default     => 29_000,
    };
}
```

```php
protected function contextWindow(): int
{
    return ProviderFactory::contextWindow();
}
```

La cifra de Ollama es la única que depende de tu propia configuración. 29.000 presupone una ventana de 32K, y un modelo local solo la tiene si la pides: `parameters: ['options' => ['num_ctx' => 32_768]]` en el proveedor Ollama, como hace la factoría de la Sección 3.6. Sin ello, Ollama trunca en su propio valor por defecto, normalmente mucho menor, mucho antes de que el recortador vea motivo para actuar. Cambia uno de los dos números y tendrás que cambiar el otro.

### Qué te cuesta el recorte

El recorte saca los mensajes más antiguos de la vista del modelo. El usuario estableció una restricción en el mensaje tres —«responde siempre en español», «mi número de cuenta es X»— y en el mensaje cuarenta ha desaparecido. El agente parece desarrollar amnesia a mitad de conversación, lo que los usuarios leen como un error aunque funcione según lo diseñado.

Tres mitigaciones, en orden creciente de sofisticación:

**Reformula las constantes en el prompt de sistema.** El prompt de sistema se reenvía en cada turno y no está sujeto a recorte. Todo lo que deba sobrevivir pertenece ahí, no a la transcripción.

**Resume en lugar de descartar.** NeuronAI incluye un middleware de resumen, `Summarization`, que enganchas a los nodos de inferencia del agente (Sección 2.3): cuando la conversación supera un presupuesto de tokens, sustituye todo salvo los últimos mensajes por un mensaje de resumen breve que permanece en el contexto. El modelo conserva más del hilo, a costa de una llamada extra al LLM, y de la transcripción. El middleware reescribe el hilo mediante `flushAll()`, de modo que los mensajes originales, archivados incluidos, desaparecen del almacén; si necesitas ese registro, guarda una copia propia. Los middleware se cubren en el Capítulo 15.

**Saca los hechos duraderos de la transcripción por completo.** Memoria a largo plazo: Sección 4.5.

### Puntos clave

- Configura entre un 5 y un 10 % por debajo del límite real del modelo; el recortador necesita margen.
- Deduce el valor del proveedor, nunca lo escribas a fuego para todo el proyecto. Con Ollama, fija `num_ctx` en consonancia: trunca en silencio en lugar de fallar.
- El recorte oculta al modelo los mensajes más antiguos: las restricciones duraderas pertenecen al prompt de sistema.
- Todos los almacenes archivan los mensajes recortados en lugar de borrarlos; la transcripción completa se queda en tu almacenamiento.
- El resumen conserva más contexto a costa de una llamada extra, y de la transcripción guardada, a la que sustituye.

## 4.5 Memoria de sesión frente a memoria a largo plazo

Tres cosas distintas se llaman «memoria». Elegir la equivocada produce una arquitectura que no se arregla afinando parámetros.

### Tres mecanismos

**1. Memoria de sesión — `ChatHistory`.**
La conversación actual. Acotada por la ventana de contexto, recortada automáticamente, delimitada a un hilo. Responde: «¿qué acabamos de decir?».

**2. Memoria a largo plazo — un almacén fuera de la transcripción.**
Lo que conversaciones anteriores establecieron sobre un usuario o entidad, conservado más allá de un hilo concreto. No está acotada por la ventana de contexto porque no está en la transcripción: solo vuelve a entrar lo que es relevante para la pregunta actual. Responde: «¿qué sé de esta persona?».

**3. Conocimiento — RAG.**
Tus documentos, indexados y recuperados por similitud semántica. No va sobre el usuario en absoluto; va sobre tu dominio. Responde: «¿qué dice nuestra documentación?».

Los tres se confunden constantemente en las conversaciones de producto, y la confusión produce mala arquitectura. «El bot debería recordar las preferencias del cliente» es el mecanismo 2. «El bot debería responder a partir de nuestro manual» es el mecanismo 3. Los dos pueden compartir maquinaria —NeuronAI construye el segundo con los componentes del tercero—, pero nunca un almacén: indexa conversaciones en el mismo almacén vectorial que el manual y las palabras de un cliente vuelven como respuesta a la pregunta de otro.

### Memoria a largo plazo en NeuronAI

La memoria de conversaciones de NeuronAI tiene dos mitades, ambas construidas con componentes de RAG (Capítulo 12) y cada una opcional por separado. La mitad que escribe es un nodo. Devuelve un `ConversationIngestionNode` desde el método `exitNodes()` del agente, en lugar del final por defecto, y cada turno completado —el texto del usuario y la respuesta final del modelo, nunca las llamadas a herramientas— se guarda como un documento en un almacén vectorial, etiquetado con su ID de hilo. El nodo necesita ese almacén y un proveedor de incrustaciones, inyectados aquí a través del constructor:

```php
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\Nodes\ConversationIngestionNode;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

public function __construct(
    protected VectorStoreInterface $conversationStore,
    protected EmbeddingsProviderInterface $embeddings,
) {
    parent::__construct();
}

protected function exitNodes(): array
{
    return [new ConversationIngestionNode(
        vectorStore: $this->conversationStore,
        embeddingProvider: $this->embeddings,
    )];
}
```

La mitad que lee es una estrategia de recuperación, `SemanticMemoryRetrieval`. Dados el mismo almacén y una lista de IDs de hilo, un agente RAG (Sección 12.7) encuentra los intercambios pasados más cercanos en significado a la pregunta actual y los añade al prompt como contexto adicional.

Fíjate bien en que esto es **recuperación**, no un componente de historial. Esa es la afirmación arquitectónica: la memoria a largo plazo no es una transcripción más larga reenviada en cada turno. Es una búsqueda, y al modelo solo le llega lo que la búsqueda devuelve.

La lista de IDs de hilo particiona el almacén. Es una lista de permitidos, y nada se le añade por ti, ni siquiera el hilo actual: pasa exactamente los hilos que este usuario tiene derecho a recordar. Guarda además las conversaciones en un almacén vectorial propio. Solo esta estrategia aplica la lista; cualquier otra recuperación sobre el mismo almacén devuelve las conversaciones de todos.

El material más antiguo usa para esta tarea un juego de herramientas, `ZepLongTermMemoryToolkit`. Sigue incluido, pero está obsoleto y se eliminará en la próxima versión mayor.

### La tabla de decisión

| Requisito | Mecanismo |
|---|---|
| «Continúa con lo que acabo de decir» | Memoria de sesión |
| «Recuerda que soy vegetariano, para siempre» | Memoria a largo plazo |
| «Responde según nuestra política de devoluciones» | RAG |
| «No reveles nunca los precios internos» | Prompt de sistema |
| «¿Cuántos pedidos ha hecho este cliente?» | Herramienta de base de datos |

Esa última fila merece énfasis, porque es el error que la gente comete más a menudo. El número de pedidos es un **hecho de tu base de datos**. No es memoria y no es RAG. Pregúntalo con SQL, a través de una herramienta. Recurrir a un almacén vectorial para responder una pregunta contable es un olor de diseño, y produce respuestas aproximadamente correctas, que para un recuento es lo mismo que incorrectas.

### La dimensión de privacidad

Memoria a largo plazo significa almacenar lo que la gente le dijo a tu aplicación, y lo que un modelo de lenguaje respondió, más allá de la conversación en la que se dijo, a menudo en un servicio de terceros. Eso es una conversación de RGPD antes que una conversación de ingeniería:

- ¿Cuál es tu base jurídica para almacenarlo?
- ¿Puede el usuario ver qué se ha guardado sobre él?
- ¿Puede solicitar su borrado, y el borrado se propaga?
- ¿Dónde reside físicamente el almacén?

Sobre la tercera pregunta: `resetConversation()` limpia el historial de conversación y nada más. Los documentos del almacén de conversaciones tienen un ciclo de vida propio y se borran aparte, a través del almacén vectorial, hilo por hilo.

Nada de esto es una razón para evitar el patrón. Es una razón para diseñarlo deliberadamente en vez de descubrirlo en una auditoría. El Capítulo 23 vuelve a ello.

### Ejercicio

Para una aplicación en la que trabajes de verdad, enumera cinco cosas que necesitaría «recordar». Clasifica cada una en una de las cinco filas de la tabla de decisión anterior y justifica las que no resultaran obvias. Las filas que costó clasificar son las que te darán problemas en producción.

### Puntos clave

- Tres mecanismos distintos: memoria de sesión, memoria a largo plazo, recuperación de conocimiento.
- La memoria a largo plazo es **recuperación** sobre un almacén de conversaciones propio, acotado por una lista explícita de IDs de hilo: se consulta en cada pregunta, no se reenvía en cada turno.
- Los hechos contables vienen de la base de datos, nunca de un almacén vectorial.
- Almacenar lo que los usuarios dijeron más allá de la conversación es una decisión de privacidad, no solo técnica.

## Laboratorio 2 — Un chat de CLI persistente

La demostración más convincente de todo lo de este capítulo: cierra el terminal, vuelve a abrirlo y la conversación sigue ahí.

### El agente

**`src/Agents/PersistentAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Chat\History\FileMessageStore;
use NeuronAI\Chat\History\MessageStoreInterface;
use NeuronAI\Providers\AIProviderInterface;

class PersistentAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a technical assistant that remembers conversation context.'],
            output: ['Answer concisely.'],
        );
    }

    protected function messageStore(): MessageStoreInterface
    {
        return new FileMessageStore(
            directory: \dirname(__DIR__, 2) . '/storage/chat',
        );
    }

    protected function contextWindow(): int
    {
        return ProviderFactory::contextWindow();
    }
}
```

Fíjate en lo que la clase *no* contiene: un ID de hilo. No hay constructor, ni propiedad `$threadId`, ni clave pasada a `FileMessageStore`. La clase describe dónde se guardan las conversaciones; a qué conversación pertenece esta ejecución lo decide quien construye el agente, mediante `make(workflowId: ...)`, exactamente como se describió en la Sección 4.3. La misma clase sirve a todos los hilos.

### El bucle

**`examples/04-chat-loop.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\PersistentAgent;
use NeuronAI\Chat\Messages\UserMessage;

$threadId = $argv[1] ?? 'default';
$agent = PersistentAgent::make(workflowId: $threadId);

echo "Thread: {$threadId} — /exit to quit, /reset to clear memory.\n\n";

while (true) {
    $input = \readline('> ');

    if ($input === false) {
        break;
    }

    $input = \trim($input);

    if ($input === '') {
        continue;
    }

    \readline_add_history($input);

    if ($input === '/exit') {
        break;
    }

    if ($input === '/reset') {
        $agent->resetConversation();
        echo "Memory cleared.\n\n";
        continue;
    }

    try {
        $reply = $agent->chat(new UserMessage($input))->getMessage();
        echo "\n" . $reply?->getContent() . "\n\n";
    } catch (\Throwable $e) {
        \fwrite(STDERR, "Error: {$e->getMessage()}\n\n");
    }
}
```

```bash
php examples/04-chat-loop.php project-alpha
```

Dile algo. Sal. Vuelve a abrir el terminal. Ejecuta el mismo comando otra vez y pregúntale qué dijiste. **Esa** es la demostración: la transcripción salió del disco y se reenvió, exactamente como describía la Sección 4.2. No se recordó nada; se reprodujo algo.

::: {.callout .callout-tip}
[En la práctica]{.callout-title}

`/reset` no toca el sistema de archivos. `resetConversation()` le pide al agente que olvide: abandona cualquier ejecución inacabada en el hilo y llama a `flushAll()` sobre el historial, que vacía el hilo en el almacén: en `FileMessageStore`, borrando el archivo de ese hilo —mensajes archivados incluidos— y nada más. Borrar archivos a mano con un glob acopla tu código a un formato de nombre de archivo que es asunto de la biblioteca, y un patrón que empareje más de lo que pretendías es un mal hábito que arrastrar a código que borra cosas. Mira en `storage/chat/` antes y después de un reinicio para comprobarlo tú mismo.
:::

### Criterios de aceptación

- Dos IDs de hilo distintos mantienen dos conversaciones independientes.
- La conversación sobrevive a un reinicio completo del proceso.
- `/reset` limpia un hilo y deja el otro intacto.
- Un error del proveedor se imprime en `STDERR` y te devuelve al prompt en lugar de matar el bucle.

### Ir más allá

Añade un comando `/history` que imprima la transcripción actual con los roles —`$agent->getChatHistory()->getMessages()` te da los objetos `Message`, y `getRole()` en cada uno— y observa qué saca de la vista el recorte a medida que la conversación supera la ventana de contexto. Ponla deliberadamente baja —`->setContextWindow(2_000)` en el agente que construye el bucle— para verlo ocurrir en unos pocos turnos y no en unos cientos. Luego abre el archivo del hilo en `storage/chat/`: los mensajes recortados siguen ahí, marcados con `archived_at`.
