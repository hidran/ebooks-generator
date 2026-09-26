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
$response = MyAgent::make()->chat(new UserMessage('...'))->getMessage();

// Convenience: all text blocks joined
echo $response?->getContent();
```

Pero con un modelo de razonamiento, la respuesta lleva más que texto:

```php
use NeuronAI\Chat\Messages\ContentBlocks\ReasoningContent;
use NeuronAI\Chat\Messages\ContentBlocks\TextContent;

foreach ($response->getContentBlocks() as $block) {
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
[Cambio en la v3]{.callout-title}

Las versiones anteriores usaban `addAttachment(new Image($url, ...))`. La v3 lo sustituyó por el sistema de bloques de contenido. Los tutoriales antiguos muestran la llamada vieja. Relacionado: la documentación es inconsistente con los nombres de las clases de bloque —`TextBlock`/`FileBlock` aparecen en algunos sitios donde las clases publicadas son `TextContent`/`FileContent`—, y un ejemplo importa `AudioContent` mientras instancia `FileContent`. Ver los puntos 10 y 11 del Apéndice A.
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
    ->chat(new UserMessage("What's my name?"))
    ->getMessage();

echo $message?->getContent();
// I'm sorry, I don't know your name.
```

Ahora conserva la misma instancia:

```php
$agent = AssistantAgent::make();

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

El componente de NeuronAI que guarda la transcripción y la reenvía es `ChatHistory`. Eso es todo lo que significa «memoria» en esta capa.

### Cuatro consecuencias que conviene enunciar

**1. La memoria cuesta dinero en cada turno.**
El turno veinte reenvía diecinueve intercambios anteriores. Este es el mecanismo detrás de la tabla de costes de la Sección 1.4, y es por lo que las conversaciones largas se encarecen aunque los mensajes individuales sean cortos.

**2. La memoria está acotada por la ventana de contexto.**
No es una base de datos que crece. Es un búfer con un techo rígido. Algo tendrá que descartarse tarde o temprano, y la única pregunta es qué y cómo: Sección 4.4.

**3. La memoria está enteramente bajo tu control.**
Lo cual es liberador en cuanto lo aceptas. Puedes editar el historial, inyectar un resumen, descartar turnos irrelevantes o mantener un hecho fijado permanentemente a nivel de sistema. Nada es sagrado; es tu array.

**4. La ausencia de estado es lo que hace fácil el escalado horizontal.**
Cualquier servidor web puede atender cualquier petición, siempre que pueda cargar la transcripción. No hay afinidad de sesión con un proveedor. Carga un `ChatHistory` desde almacenamiento compartido y cualquier nodo puede continuar cualquier conversación. Es una ventaja arquitectónica genuina, y es inusual que una funcionalidad con apariencia de estado escale con tanta limpieza.

### El modelo mental que conviene conservar

El modelo es una **función pura**: entra la transcripción, sale el siguiente mensaje. Todo lo que parece memoria, persistencia de personalidad o aprendizaje es tu código eligiendo qué entra en la transcripción.

Todas las técnicas del resto de este libro —recorte del historial, resumen, RAG, almacenes de memoria a largo plazo— son respuestas distintas a una sola pregunta: **¿qué ponemos en la transcripción?**

### Puntos clave

- No hay sesión del lado del servidor; la transcripción se reenvía en cada turno.
- La memoria cuesta tokens en cada turno y está limitada por la ventana de contexto.
- El historial es tu array: editable, inyectable, reemplazable.
- El modelo es una función pura de la transcripción.

## 4.3 Implementaciones de ChatHistory

### La interfaz

```php
NeuronAI\Chat\History\ChatHistoryInterface
```

Registra una implementando `chatHistory()` en tu agente, o pasando una instancia a `setChatHistory()`. Si no haces ninguna de las dos cosas, el valor por defecto es en memoria.

El historial es un servicio que usan los nodos del agente, no parte del estado de la ejecución: `ChatNode` lee de él la transcripción y le añade mensajes, y la transcripción nunca se copia en el `AgentState` que devuelve `chat()`. Esa separación importa cuando las ejecuciones se vuelven duraderas (Capítulo 15). El estado guardado de una ejecución en pausa sigue siendo pequeño por mucho que crezca la conversación, y la conversación vive en un único lugar: el almacenamiento del historial.

### ¿Qué conversación? El ID de hilo

Un historial pertenece siempre a una conversación —un **hilo**— y algo tiene que decir cuál. En NeuronAI ese algo es el agente, no el historial:

```php
$agent = SupportAgent::make(threadId: $threadId);
```

Dentro de la clase del agente, el método `chatHistory()` construye el historial *sin* ID de hilo. Antes de que el historial se lea o escriba por primera vez, el agente le vincula su propio ID de hilo. La identidad entra por un único sitio, el punto de llamada que sabe realmente de qué conversación trata esta petición, y nunca dentro de la clase que solo sabe dónde se guardan las conversaciones.

Es el mismo ID del que hablaba la Sección 2.3: el ID de hilo es también el ID del flujo de trabajo de la ejecución del agente. Cuando en el Capítulo 15 una ejecución se pause a la espera de una aprobación humana, el punto de conexión que la reanude no necesitará más que el ID de hilo para encontrarla.

De ahí se siguen dos reglas, y ambas se hacen cumplir:

- **Un historial se vincula una sola vez.** Puedes, en cambio, pasar un ID de hilo directamente al constructor de un historial; el agente lo adopta. Pero si contradice el `threadId:` dado al agente, obtienes una excepción en lugar de una conversación escrita en silencio en el hilo equivocado.
- **Un historial duradero sin hilo se niega a funcionar.** Usa un historial de archivo o SQL que nunca se vinculó y lanzará una excepción en lugar de leer tranquilamente una conversación vacía.

::: {.callout .callout-warning}
[El ID de hilo es entrada del usuario]{.callout-title}

Lo que pases como `threadId:` selecciona qué conversación se carga, se amplía y se reanuda. Si llega en una petición —un segmento de URL, un campo de formulario—, comprueba que el usuario actual es el dueño de ese hilo antes de construir el agente con él. El framework no hace ningún control de acceso; basta con que falte una comprobación de propiedad para que cualquier usuario pueda leer la conversación de cualquier otro.
:::

### InMemoryChatHistory

```php
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\InMemoryChatHistory;

protected function chatHistory(): ChatHistoryInterface
{
    return new InMemoryChatHistory(threadId: $this->threadId, contextWindow: 150_000);
}
```

Un array. Vive solo durante el proceso PHP actual. A diferencia de los demás backends, nunca queda sin hilo: si no recibe un ID de hilo, se genera una clave aleatoria. Eso importa en cuanto el agente tiene identidad propia. Construye el agente con `make(threadId: ...)` —como hace el punto de conexión AG-UI de la Sección 7.5— y el agente encuentra el historial ya ligado a otro hilo y lanza *"Conflicting thread identity"*. Así que pasa el hilo del agente, como hace el listado: `$this->threadId` es `null` cuando no lo hay, y el historial se genera la clave exactamente igual que antes. Correcto para: scripts de una sola ejecución, puntos de conexión de API sin estado donde el historial lo llevas tú, y pruebas.

Recuerda que en una petición web normal PHP muere al terminar la respuesta. Historial en memoria en un contexto web significa **ninguna memoria entre peticiones**, lo cual es una sorpresa genuinamente frecuente para desarrolladores acostumbrados a entornos de ejecución de larga vida.

### FileChatHistory

```php
use NeuronAI\Chat\History\FileChatHistory;

protected function chatHistory(): ChatHistoryInterface
{
    return new FileChatHistory(
        directory: '/home/app/storage/neuron',
        contextWindow: 150_000,
    );
}
```

`directory` es una ruta absoluta, que se crea si no existe. La conversación es el ID de hilo que el agente vincula: `neuron_<thread>.chat` en ese directorio. Usa un ID de usuario como hilo para una conversación por usuario, o un ID de hilo generado para varias.

Correcto para: herramientas de CLI, aplicaciones de un solo servidor, prototipos. No correcto para: despliegues multiservidor sin almacenamiento compartido, ni para alta concurrencia; dos escrituras simultáneas sobre la misma clave no acabarán bien.

### SQLChatHistory

Crea primero la tabla. Una fila por mensaje, indexada por hilo (se muestra MySQL; las versiones de PostgreSQL y SQLite solo difieren en los tipos de columna):

```sql
CREATE TABLE IF NOT EXISTS chat_messages (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  thread_id VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL,
  content LONGTEXT NULL,
  meta LONGTEXT NULL,
  archived_at DATETIME NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_thread_id (thread_id)
);
```

```php
use NeuronAI\Chat\History\SQLChatHistory;

protected function chatHistory(): ChatHistoryInterface
{
    return new SQLChatHistory(
        pdo: new \PDO('mysql:host=localhost;dbname=DB;charset=utf8mb4', 'user', 'pass'),
        table: 'chat_messages',
        contextWindow: 150_000,
    );
}
```

Recibe un `PDO` normal, así que funciona en cualquier aplicación PHP con independencia del framework. En Laravel le pasarías `\DB::connection()->getPdo()`; en Symfony, `$connection->getNativeConnection()` de una conexión de Doctrine.

Como cada mensaje es su propia fila —`role`, los bloques de contenido como JSON en `content`, todo lo demás (uso, llamadas a herramientas, metadatos) como JSON en `meta`—, la tabla es útil para el resto de tu aplicación, no solo para el agente: informes por mensaje, tareas de retención, un panel de soporte que liste conversaciones. Puedes añadir columnas —una clave externa a tu tabla de usuarios, por ejemplo— siempre que se mantenga la estructura base. `archived_at` se explica en la Sección 4.4.

### EloquentChatHistory

Cubierta por completo en el Capítulo 18, se lista aquí para que el mapa esté completo:

```php
new EloquentChatHistory(
    modelClass: ChatMessage::class,
    contextWindow: 150_000,
);
```

La misma forma de tabla que el backend SQL, la misma vinculación al hilo: la clase del modelo es lo único que necesita saber.

### Elegir

| Backend | Úsalo cuando | Evítalo cuando |
|---|---|---|
| InMemory | Scripts, puntos de conexión sin estado, pruebas | Necesitas persistencia |
| File | Herramientas de CLI, un solo servidor, prototipos | Multiservidor, alta concurrencia |
| SQL | Cualquier framework, producción, multiservidor | No tienes base de datos |
| Eloquent | Laravel con relaciones y scopes | No estás en Laravel |

El Laboratorio 2, al final de este capítulo, construye un chat de CLI persistente sobre `FileChatHistory`.

### Puntos clave

- Cuatro backends: InMemory, File, SQL, Eloquent.
- Construye el historial sin hilo; dale al agente `make(threadId: ...)`, y él vinculará el hilo al historial. El ID de hilo es también el ID del flujo de trabajo de la ejecución.
- Autoriza el ID de hilo antes de usarlo: selecciona de quién es la conversación que se carga.
- En una petición web, en memoria significa ninguna memoria entre peticiones.
- `SQLChatHistory` recibe un PDO normal, guarda una fila por mensaje y funciona en cualquier framework.

## 4.4 Ventana de contexto y recorte

### El error que esto previene

El fallo de producción más común en la IA conversacional:

> «Funciona bien, y luego, a partir de unos treinta mensajes, empieza a lanzar errores.»

La transcripción creció por encima del límite de contexto del modelo. El proveedor rechaza la petición: no la trunca por ti, devuelve un error.

El `ChatHistory` de NeuronAI lo previene recortando automáticamente. Sigue el uso de tokens a partir de las respuestas del proveedor y, cuando la transcripción se acerca al límite configurado, quita mensajes del principio de lo que envía al modelo.

«Quita de lo que envía» es una formulación deliberada. Los backends duraderos —File, SQL, Eloquent— no borran los mensajes recortados: los marcan como archivados (la columna `archived_at` de la Sección 4.3, o una clave en el archivo) y dejan de cargarlos. El modelo ve el hilo recortado; tu aplicación sigue teniendo la transcripción completa para auditoría, analítica o una política de retención. Solo `InMemoryChatHistory` descarta sin más lo que recorta, y `flushAll()` es la única operación que borra de verdad un hilo, mensajes archivados incluidos.

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

El recortador no corta sin más en el byte donde se alcanza el límite. Busca un punto de corte que minimice la pérdida de contexto; la documentación lo describe como identificar un corte algo menos agresivo que el calculado en primera instancia.

Eso significa que necesita espacio de maniobra. Configura exactamente en el límite del modelo y el recortador no tendrá adónde mover su punto de corte, y podrás desbordarte igualmente. El margen es lo que le permite elegir una frontera sensata en lugar de una mecánica.

### Dónde va

```php
protected function chatHistory(): ChatHistoryInterface
{
    return new InMemoryChatHistory(threadId: $this->threadId, contextWindow: 185_000);
}
```

Todas las implementaciones reciben el mismo argumento. Los guiones bajos en los literales numéricos son una funcionalidad de PHP 7.4+ y hacen estos valores mucho más fáciles de leer de un vistazo: úsalos.

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
protected function chatHistory(): ChatHistoryInterface
{
    return new InMemoryChatHistory(
        threadId: $this->threadId,
        contextWindow: ProviderFactory::contextWindow()
    );
}
```

### Qué te cuesta el recorte

El recorte saca los mensajes más antiguos de la vista del modelo. El usuario estableció una restricción en el mensaje tres —«responde siempre en español», «mi número de cuenta es X»— y en el mensaje cuarenta ha desaparecido. El agente parece desarrollar amnesia a mitad de conversación, lo que los usuarios leen como un error aunque funcione según lo diseñado.

Tres mitigaciones, en orden creciente de sofisticación:

**Reformula las constantes en el prompt de sistema.** El prompt de sistema se reenvía en cada turno y no está sujeto a recorte. Todo lo que deba sobrevivir pertenece ahí, no a la transcripción.

**Resume en lugar de descartar.** NeuronAI incluye un middleware de resumen, `Summarization`, que enganchas a los nodos de inferencia del agente (Sección 2.3): en vez de dejar que los turnos más antiguos salgan de la vista, los comprime en un mensaje de resumen breve que permanece en el contexto. Mayor fidelidad, a costa de una llamada extra al LLM. Se cubre junto con los demás middleware en el Capítulo 15.

**Saca los hechos duraderos de la transcripción por completo.** Memoria a largo plazo: Sección 4.5.

### Puntos clave

- Configura entre un 5 y un 10 % por debajo del límite real del modelo; el recortador necesita margen.
- Deduce el valor del proveedor, nunca lo escribas a fuego para todo el proyecto.
- El recorte oculta al modelo los mensajes más antiguos: las restricciones duraderas pertenecen al prompt de sistema.
- Los backends duraderos archivan los mensajes recortados en lugar de borrarlos; la transcripción completa se queda en tu almacenamiento.
- El resumen conserva más contexto a costa de una llamada extra.

## 4.5 Memoria de sesión frente a memoria a largo plazo

Tres cosas distintas se llaman «memoria». Elegir la equivocada produce una arquitectura que no se arregla afinando parámetros.

### Tres mecanismos

**1. Memoria de sesión — `ChatHistory`.**
La conversación actual. Acotada por la ventana de contexto, recortada automáticamente, delimitada a un hilo. Responde: «¿qué acabamos de decir?».

**2. Memoria a largo plazo — un almacén externo de hechos.**
Hechos duraderos sobre un usuario o entidad que persisten entre conversaciones. No está acotada por la ventana de contexto porque no está en la transcripción: el agente la consulta bajo demanda, a través de una herramienta. Responde: «¿qué sé de esta persona?».

**3. Conocimiento — RAG.**
Tus documentos, indexados y recuperados por similitud semántica. No va sobre el usuario en absoluto; va sobre tu dominio. Responde: «¿qué dice nuestra documentación?».

Los tres se confunden constantemente en las conversaciones de producto, y la confusión produce mala arquitectura. «El bot debería recordar las preferencias del cliente» es el mecanismo 2. «El bot debería responder a partir de nuestro manual» es el mecanismo 3. Construir el primero con el tercero —indexar conversaciones en un almacén vectorial— es un error de diseño que produce un recuerdo vago y poco fiable.

### Memoria a largo plazo en NeuronAI

NeuronAI incluye un juego de herramientas para Zep, un servicio de grafo de conocimiento diseñado exactamente para esto:

```php
use NeuronAI\Tools\Toolkits\Zep\ZepLongTermMemoryToolkit;

protected function tools(): array
{
    return [
        ZepLongTermMemoryToolkit::make(
            key: 'ZEP_API_KEY',
            user_id: 'ID',
        ),
    ];
}
```

Fíjate bien en que esto es un **juego de herramientas**, no un componente de historial. Esa es la afirmación arquitectónica: la memoria a largo plazo es algo que el agente *elige consultar*, mediante una llamada a una herramienta, no algo inyectado automáticamente en cada petición. El modelo decide cuándo un hecho merece consultarse o guardarse.

El argumento `user_id` particiona el almacén. Úsalo como clave de aislamiento para la entidad que estés siguiendo: un usuario, una empresa, un proyecto.

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

Memoria a largo plazo significa almacenar hechos personales, derivados por un modelo de lenguaje, en un servicio de terceros. Eso es una conversación de RGPD antes que una conversación de ingeniería:

- ¿Cuál es tu base jurídica para almacenarlo?
- ¿Puede el usuario ver qué se ha guardado sobre él?
- ¿Puede solicitar su borrado, y el borrado se propaga?
- ¿Dónde reside físicamente el almacén?

Nada de esto es una razón para evitar el patrón. Es una razón para diseñarlo deliberadamente en vez de descubrirlo en una auditoría. El Capítulo 23 vuelve a ello.

### Ejercicio

Para una aplicación en la que trabajes de verdad, enumera cinco cosas que necesitaría «recordar». Clasifica cada una en una de las cinco filas de la tabla de decisión anterior y justifica las que no resultaran obvias. Las filas que costó clasificar son las que te darán problemas en producción.

### Puntos clave

- Tres mecanismos distintos: memoria de sesión, memoria a largo plazo, recuperación de conocimiento.
- La memoria a largo plazo es un **juego de herramientas**: se consulta deliberadamente, no se inyecta de forma automática.
- Los hechos contables vienen de la base de datos, nunca de un almacén vectorial.
- Almacenar hechos personales derivados es una decisión de privacidad, no solo técnica.

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
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\FileChatHistory;
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

    protected function chatHistory(): ChatHistoryInterface
    {
        return new FileChatHistory(
            directory: \dirname(__DIR__, 2) . '/storage/chat',
            contextWindow: ProviderFactory::contextWindow(),
        );
    }
}
```

Fíjate en lo que la clase *no* contiene: un ID de hilo. No hay constructor, ni propiedad `$threadId`, ni clave pasada a `FileChatHistory`. La clase describe dónde se guardan las conversaciones; a qué conversación pertenece esta ejecución lo decide quien construye el agente, mediante `make(threadId: ...)`, exactamente como se describió en la Sección 4.3. La misma clase sirve a todos los hilos.

### El bucle

**`examples/04-chat-loop.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\PersistentAgent;
use NeuronAI\Chat\Messages\UserMessage;

$threadId = $argv[1] ?? 'default';
$agent = PersistentAgent::make(threadId: $threadId);

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

`/reset` no toca el sistema de archivos. `resetConversation()` le pide al agente que olvide: abandona cualquier ejecución inacabada en el hilo y llama a `flushAll()` sobre el historial, que en `FileChatHistory` borra el archivo de ese hilo —mensajes archivados incluidos— y nada más. Borrar archivos a mano con un glob acopla tu código a un formato de nombre de archivo que es asunto de la biblioteca, y un patrón que empareje más de lo que pretendías es un mal hábito que arrastrar a código que borra cosas. Mira en `storage/chat/` antes y después de un reinicio para comprobarlo tú mismo.
:::

### Criterios de aceptación

- Dos IDs de hilo distintos mantienen dos conversaciones independientes.
- La conversación sobrevive a un reinicio completo del proceso.
- `/reset` limpia un hilo y deja el otro intacto.
- Un error del proveedor se imprime en `STDERR` y te devuelve al prompt en lugar de matar el bucle.

### Ir más allá

Añade un comando `/history` que imprima la transcripción actual con los roles —`$agent->getChatHistory()->getMessages()` te da los objetos `Message`, y `getRole()` en cada uno— y observa qué saca de la vista el recorte a medida que la conversación supera tu `contextWindow` configurada. Ponla deliberadamente baja —2.000 tokens— para verlo ocurrir en unos pocos turnos y no en unos cientos. Luego abre el archivo del hilo en `storage/chat/`: los mensajes recortados siguen ahí, marcados con `archived_at`.
