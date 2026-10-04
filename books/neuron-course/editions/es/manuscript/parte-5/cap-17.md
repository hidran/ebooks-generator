# Capítulo 17 — El SDK para Laravel

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

Este capítulo es conceptual y no tiene código propio, pero el repositorio complementario [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene versiones ejecutables de todo lo que el libro construye.
:::

## 17.1 Instalación y filosofía

### Instalar

```bash
composer require neuron-core/neuron-laravel
```

**Requisitos:** este libro usa Laravel 13 sobre PHP 8.5, con la versión 2.0.0 del SDK. Esta requiere `neuron-core/neuron-ai` `^4.0` y, por tanto, arrastra el framework: aquí, la 4.0.2. El paquete en sí acepta versiones anteriores de Laravel y de PHP; el código del libro necesita PHP 8.5.

### Qué aporta

Cinco cosas, según la descripción del propio paquete:

- Un archivo de configuración para las credenciales del proveedor de IA y de las incrustaciones
- Comandos de Artisan para generar el esqueleto de los componentes más usados
- Facades que instancian proveedores y almacenes vectoriales a partir de la configuración
- Migraciones listas para usar para `EloquentChatHistory`
- Directrices para asistentes de código de IA integradas con Laravel Boost

Lee la lista teniendo delante el framework que el paquete instala, porque el SDK 2.0.0 no le ha seguido el paso. Los tres primeros elementos funcionan en neuron-ai 4.0.2, con la excepción de un generador, y son lo que usa el resto de la Parte V: el archivo de configuración, los generadores y las facades de proveedores, incrustaciones y almacenes vectoriales. Los dos últimos no, y tampoco la funcionalidad con la que abre el README, la facade `Neuron`.

::: {.callout .callout-warning}
[El SDK 2.0.0 no está al día con neuron-ai 4.0.2]{.callout-title}

Cuatro partes del paquete fallan con la versión del framework que él mismo instala. Cada una tiene una alternativa que funciona, indicada allí donde aparece:

- La facade `Neuron` lanza una excepción en cada llamada. Usa una clase agente generada y vinculada a un hilo (Sección 17.4).
- `php artisan neuron:node` escribe una clase cuyos imports no existen. Corrige dos líneas a mano (Sección 17.3).
- Las migraciones y los modelos incluidos no encajan con el almacén de mensajes de la 4.0.2 ni con su persistencia del flujo de trabajo. Ten la migración y el modelo en tu propia aplicación (más abajo, y Capítulo 18).
- Las skills de Boost incluidas enseñan API que la 4.0.2 eliminó. Instala las skills que se distribuyen con el paquete core (Sección 17.7).

Verificado sobre neuron-ai 4.0.2 y neuron-laravel 2.0.0. Una versión posterior del SDK puede cerrar cualquiera de estos puntos; compruébalo antes de rodearlos.
:::

El cuarto elemento de la lista del paquete es el primero sobre el que hay que actuar. `EloquentChatHistory` ya no existe: en la 4.0.2 una conversación vive en un almacén de mensajes, `EloquentMessageStore` en Laravel, que identifica cada fila por un `message_id` y se apoya en un índice único `(thread_id, message_id)`. La migración `chat_messages` del SDK no crea esa columna, y su modelo `ChatMessage` no la declara fillable. Su tabla `workflow_store` tiene una clave primaria compuesta y ningún `id`, así que `EloquentPersistence` sobre el modelo `WorkflowStore` del SDK no puede borrar los registros de una ejecución terminada, y el segundo mensaje de un hilo se rechaza. No publiques la etiqueta `neuron-migrations`. Escribe una migración propia para las dos tablas, y un modelo `App\Models\ChatMessage` con `thread_id`, `message_id`, `role`, `content` y `meta` declarados fillable. El Capítulo 18 construye ambos.

### La filosofía, citada

El README se abre con una afirmación que merece leerse entera:

> Neuron no necesita abstracciones invasivas. Ya tiene una sintaxis muy simple, código tipado al 100 % e interfaces claras en las que puedes apoyarte para desarrollar tu sistema agéntico o crear plugins y extensiones propios.

Y:

> En este paquete te proporcionamos un kit de desarrollo diseñado específicamente para los puntos de integración con Laravel **sin limitar el acceso a los componentes nativos de Neuron.** También puedes usar este paquete como inspiración para diseñar tu propio patrón de integración a medida.

De ahí se siguen tres cosas, y son la razón de que la Parte V venga después de las Partes II a IV y no en su lugar:

**Todo lo que aprendiste sigue funcionando.** Tus clases agente, herramientas, flujos de trabajo y pipelines de RAG no cambian. El SDK añade puntos de entrada; no sustituye la API.

**El SDK es opcional.** La guía de los propios mantenedores para usar NeuronAI en Laravel, la skill `neuron-laravel-integration` que se distribuye dentro del paquete core (Sección 17.7), no lo instala nunca: requiere `neuron-core/neuron-ai`, añade a la aplicación un proveedor de servicios, una migración y un modelo, y guarda las claves de los proveedores en `config/services.php`. Lo que el SDK añade encima son proveedores y almacenes construidos a partir de la configuración, y generadores. La Parte V toma eso de él y cablea todo lo demás en la aplicación.

**Es una implementación de referencia.** El paquete te invita explícitamente a usarlo como inspiración para tu propia integración. Si trabajas en Symfony, Spryker o un framework interno heredado, lee el código de este paquete y construye el equivalente: los puntos de integración son los mismos.

Ese último punto importa si no estás en Laravel. Esta parte es transferible.

### Puntos clave

- `composer require neuron-core/neuron-laravel`; Laravel 13 sobre PHP 8.5; SDK 2.0.0 con neuron-ai 4.0.2.
- Lo que funciona: configuración, generadores y las facades de proveedores, incrustaciones y almacenes vectoriales.
- Lo que no funciona en la 4.0.2: la facade `Neuron`, el generador de nodos, las migraciones y los modelos incluidos, las skills de Boost.
- Añade comodidad, nunca capacidad: todo lo de las Partes II a IV sigue igual.
- Diseñado para leerse como plantilla para otros frameworks.

## 17.2 Configuración

### Publica la configuración

```bash
php artisan vendor:publish --tag=neuron-config
```

Produce `config/neuron.php`.

### Variables de entorno

```dotenv
# Support for: anthropic, gemini, openai, openai-responses, mistral, ollama, huggingface, deepseek
NEURON_AI_PROVIDER=anthropic

# Support for: openai, gemini, ollama, voyage, mistral
NEURON_EMBEDDING_PROVIDER=openai

# Support for: file, pinecone, qdrant, meilisearch, chroma
NEURON_STORE_PROVIDER=file

ANTHROPIC_KEY=
ANTHROPIC_MODEL=

GEMINI_KEY=
GEMINI_MODEL=

OPENAI_KEY=
OPENAI_MODEL=

MISTRAL_KEY=
MISTRAL_MODEL=

OLLAMA_URL=
OLLAMA_MODEL=

# And many others
```

::: {.callout .callout-warning}
[Dos de ellas no tienen valor por defecto]{.callout-title}

`config/neuron.php` lee `NEURON_AI_PROVIDER` y `NEURON_EMBEDDING_PROVIDER` sin ningún valor de respaldo. Deja la primera sin definir y `AIProvider::driver()` falla con un `TypeError`, `AIProviderManager::getDefaultDriver(): Return value must be of type string, null returned`, que no nombra la variable que falta. `EmbeddingProvider::driver()` falla igual sin la segunda, y el propio listado del README no la menciona nunca. Define las dos. `NEURON_STORE_PROVIDER` es opcional y tiene `file` como valor de respaldo.
:::

Más, para el trazado:

```dotenv
INSPECTOR_INGESTION_KEY=fwe45gtxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

El README presenta esa clave como todo lo que necesitas. No lo es. El framework core no depende de Inspector y no engancha ningún observador por su cuenta: el trazado es un oyente PSR-14 que suscribes explícitamente (Capítulo 10). En Laravel eso significa requerir `inspector-apm/inspector-laravel` y, por su nombre, `inspector-apm/inspector-php` en `^3.19` (las versiones 3.18 anteriores traen un suscriptor que en la 4.0.2 no registra nada), mantener la clave de arriba y suscribir el `InspectorSubscriber` de Inspector a `ObservabilityEvent` en los agentes que quieras trazar, en una clase base compartida o dondequiera que tu contenedor construya los agentes, para que no se escape ninguno. Una clave sin suscripción no produce trazas, ni ningún error que te lo avise.

### Esto es la Sección 3.6, hecha por el framework

En la Parte II construiste `ProviderFactory` a mano: una sentencia `match` que mapea un nombre de driver a un proveedor configurado. El SDK es eso, como servicio de Laravel de primera clase.

Misma idea, mismos beneficios: nombres de proveedor en un solo sitio, elección de proveedor como configuración, desarrollo local gratis con Ollama, escalonado de costes como cambio de configuración.

Habiendo construido tú mismo la factoría, sabes exactamente qué está haciendo el SDK. Es una posición mucho mejor que tratarlo como magia.

### Configuración específica de cada entorno

El patrón natural de Laravel, y uno de los argumentos prácticos más fuertes a favor del SDK:

```dotenv
# .env.local — free, offline, no rate limits
NEURON_AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434/api
OLLAMA_MODEL=qwen2.5:7b
```

```dotenv
# .env.staging — cheap, real, good enough for QA
NEURON_AI_PROVIDER=openai
OPENAI_MODEL=gpt-4.1-mini
```

```dotenv
# .env.production
NEURON_AI_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-sonnet-4-5
```

Un código base, tres perfiles de coste, cero cambios de código.

::: {.callout .callout-warning}
[Una excepción, traída de la Sección 12.4]{.callout-title}

El proveedor y el modelo de *incrustaciones* no deben variar según el entorno. Incrustaciones distintas significan índices vectoriales incompatibles. Fija ambos en `config/neuron.php` en lugar de dejarlos a `.env`, o acabarás depurando un sistema RAG que devuelve disparates solo en staging.
:::

### El prompt de sistema en configuración

El README muestra el prompt de sistema viniendo de la configuración:

```php
public function instructions(): string
{
    return (string) new SystemPrompt(...config('neuron.system_prompt'));
}
```

Útil para un asistente por defecto. **No** es el patrón correcto para un agente real: un prompt es una especificación (Sección 3.5), y las especificaciones van en el código, bajo control de versiones, revisadas. Un archivo de configuración que un despliegue puede cambiar sin revisión de código es el hogar equivocado para el comportamiento.

Úsalo para el valor por defecto generado; declara las instrucciones en la clase agente para todo lo que importe.

::: {.callout .callout-warning}
[Dos problemas en ese fragmento del README]{.callout-title}

El ejemplo publicado dice `return (string) new SystemPrompt(...config('neuron.system_prompt');`: falta un paréntesis de cierre. Además usa `use NeuronAI\Agent;` y `use NeuronAI\SystemPrompt;`, que son namespaces de versiones anteriores. Las clases son `NeuronAI\Agent\Agent` y `NeuronAI\Agent\SystemPrompt`. Apéndice A, puntos 39 y 40.
:::

El tipo de retorno string es correcto. La firma del propio framework es `instructions(): SystemMessage|string` —un `SystemMessage` te permite dividir las instrucciones en bloques y marcar el estático para el prompt caching—, pero un string simple se acepta y se envuelve por ti, y restringir el tipo de retorno a `string` en tu clase es legal. También lo es ampliar el método de `protected` a `public`, como hace el README. La clase que genera `neuron:agent` (Sección 17.3) hace ambas cosas.

### Puntos clave

- `vendor:publish --tag=neuron-config` y luego las variables de entorno; `NEURON_AI_PROVIDER` y `NEURON_EMBEDDING_PROVIDER` no tienen valor por defecto.
- Esto es la `ProviderFactory` de la Sección 3.6, servida ya hecha.
- Varía el proveedor por entorno; **nunca** el modelo de incrustaciones.
- Mantén los prompts de sistema de verdad en el código, no en la configuración.

## 17.3 Generadores de Artisan

### Los comandos

```bash
# Create an agent
php artisan neuron:agent MyAgent

# Create a RAG
php artisan neuron:rag MyRAG

# Create a tool
php artisan neuron:tool MyTool

# Create a workflow
php artisan neuron:workflow MyWorkflow

# Create a node
php artisan neuron:node CustomNode

# Create a middleware
php artisan neuron:middleware CustomMiddleware
```

`php artisan neuron:agent MyAgent` crea `app/Neuron/Agents/MyAgent.php` con los métodos básicos esbozados. Los stubs de agente, herramienta, flujo de trabajo y middleware se ajustan a la API de la 4.0.2: la herramienta generada, por ejemplo, declara su identidad como propiedades `protected string $name` y `protected ?string $description` sin constructor, la forma que usa el Capítulo 19 de principio a fin. El stub de RAG deja sus tres hooks comentados para que los rellenes. El stub de nodo no funciona tal como se genera.

::: {.callout .callout-warning}
[`neuron:node` genera imports que no existen]{.callout-title}

El stub de nodo del SDK 2.0.0 importa `NeuronAI\Workflow\StartEvent` y `NeuronAI\Workflow\StopEvent`. Ambas clases viven en `NeuronAI\Workflow\Events\`. El archivo generado pasa el análisis sintáctico, y el primer flujo de trabajo que ejecuta el nodo falla con `Failed to validate App\Neuron\Nodes\CustomNode: First parameter of __invoke method must be a type that implements NeuronAI\Workflow\Events\Event`. Corrige las dos líneas `use` después de generar:

```php
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
```
:::

### Mejor que la CLI del core, en un aspecto concreto

Compara con la Sección 3.3:

```bash
# Core package — full namespace, doubled backslashes on Unix
./vendor/bin/neuron make:agent App\\Agents\\AssistantAgent

# Laravel SDK — just the name
php artisan neuron:agent MyAgent
```

Sin namespace, sin escapar barras invertidas, sin diferencias entre sistemas operativos. El SDK conoce la estructura de tu aplicación.

Es una cosa pequeña que elimina un punto de fricción real: la diferencia Unix/Windows de las barras invertidas del Capítulo 3 causa confusión genuina, y aquí sencillamente no existe.

### Una estructura de proyecto sugerida

Los generadores ponen los agentes en `app/Neuron/Agents`. Extiende la convención:

```
app/Neuron/
├── Agents/          SupportAgent, ResearchAgent, ReviewerAgent
├── Tools/           SearchOrdersTool, RequestRefundTool
├── Workflows/       ContentWorkflow
│   ├── Nodes/
│   └── Events/
├── Middleware/
├── Dto/             Verdict, Invoice, RefundRequest
└── Rag/             KnowledgeBaseAgent
```

Un solo namespace que contiene todo lo agéntico. Un desarrollador nuevo abre `app/Neuron` y ve toda la superficie de IA de la aplicación, en lugar de encontrar un agente en `app/Services`, una herramienta en `app/Support` y un DTO en `app/Http/Resources`.

Los generadores no coinciden todos con este árbol de serie: `neuron:tool` escribe en `app/Neuron/Agents/Tools`, `neuron:node` en `app/Neuron/Nodes` y `neuron:rag` en `app/Neuron/RAG`. Mueve los archivos una vez, o pasa al comando el nombre de clase completamente cualificado; en cualquier caso, decide el árbol antes del décimo archivo, no después.

### Puntos clave

- Seis generadores, todos `php artisan neuron:*`.
- Solo el nombre: sin namespace, sin escapes, sin diferencias de sistema operativo.
- Corrige los dos imports en cada clase que genere `neuron:node`.
- Mantén todo lo agéntico bajo `app/Neuron`.

## 17.4 La facade Neuron, y qué usar en su lugar

### Por qué existe

El autor del framework describe el problema con honestidad:

> Antes de esta versión, usar Neuron AI dentro de Laravel significaba crear una clase agente dedicada, extender `Agent`, implementar un método `provider()` y cablear tú mismo el prompt de sistema. Ese patrón es el correcto una vez que tu agente tiene personalidad, un conjunto de herramientas y un papel en tu aplicación. Pero es mucha ceremonia para un desarrollador que solo quiere comprobar si Claude, o GPT, o Gemini responden bien a un prompt dado.

Una facade es la respuesta de Laravel a esa forma de problema, y este es un uso de manual. En neuron-ai 4.0.2 es además la única parte del SDK a la que no puedes llamar.

::: {.callout .callout-warning}
[La facade `Neuron` lanza una excepción en neuron-ai 4.0.2]{.callout-title}

Un agente solo se ejecuta una vez que tiene un ID de hilo vinculado (Sección 3.4). La facade del SDK 2.0.0 construye su agente con un simple `Agent::make()` y no ofrece forma de vincular uno, así que `Neuron::chat()`, `Neuron::stream()` y `Neuron::structured()` fallan todos con `AgentException: This agent has no thread ID: bind one with setThreadId() first.`, con o sin `tools()` y `middleware()` en la cadena. La alternativa que funciona es la que la cita llama ceremonia, una clase agente dedicada, y el generador reduce la ceremonia a un solo comando. El resto de esta sección la usa.
:::

### Los tres modos

```bash
php artisan neuron:agent AssistantAgent
```

La clase generada no necesita cambios para hacer las veces de la facade. Su `provider()` devuelve `AIProvider::driver()`, el valor por defecto configurado, y su `instructions()` construye el prompt de sistema a partir de `config/neuron.php`: las dos cosas que lee la facade. Resuélvela del contenedor, vincúlala a un hilo y llámala:

```php
use App\Neuron\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

// The container builds the agent; for() returns a copy bound to one thread
$agent = app(AssistantAgent::class)->for($threadId);

// Chat (synchronous) — returns the final AgentState
$response = $agent->chat(new UserMessage('Hello!'))->getMessage();
echo $response?->getContent();

// Stream (real-time chunks) — the call itself is the generator
foreach ($agent->stream(new UserMessage('Hello')) as $chunk) {
    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}

// Structured output
$person = $agent->structured(new UserMessage('I am John and I like pizza!'), Person::class);
```

Los mismos tres puntos de entrada de la tabla de la Sección 6.3 —`chat()`, `stream()`, `structured()`— con un único archivo generado detrás: `chat()` se ejecuta hasta el final y devuelve el `AgentState`, `stream()` es un generador que recorres directamente, `structured()` devuelve el objeto. `getMessage()` es nullable, de ahí el `?->`. No traslades a la clase el bucle de transmisión del README: llama a `->events()` sobre el resultado e imprime `$event->content`, pero `stream()` devuelve el propio generador y produce varios tipos de fragmento, así que filtra por `TextChunk` como arriba.

`$threadId` es el argumento que la facade nunca pide. Da nombre a la conversación a la que pertenece la llamada: cualquier cadena nueva para una pregunta suelta, el ID de la propia conversación cuando el usuario vuelve a ella. `for()` devuelve una copia del agente vinculada a ese hilo y es el tema de la Sección 17.5; de dónde salen los ID de hilo, y qué se guarda bajo ellos, es el Capítulo 18. `AssistantAgent::make()->setThreadId(...)` de la Parte II también funciona en Laravel, pero deja que el contenedor construya el agente: a partir del Capítulo 18 tiene dependencias en el constructor. En un controlador, recibe el agente como parámetro del método en lugar de llamar a `app()`.

### Enganchar herramientas

```php
$response = app(AssistantAgent::class)->for($threadId)
    ->addTool(new SearchTool())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

$response = app(AssistantAgent::class)->for($threadId)
    ->addTool([new SearchTool(), CalculatorToolkit::make()])
    ->chat(new UserMessage('Hello!'))
    ->getMessage();
```

Instancia única o array. `addTool()` añade a lo que devuelva el hook `tools()` de la clase, solo en esta copia vinculada.

### Enganchar middleware

```php
use App\Neuron\Middleware\AuditTrail;
use NeuronAI\Agent\Nodes\ChatNode;
use NeuronAI\Agent\Nodes\ToolNode;

// Record every tool execution in the audit log
$response = app(AssistantAgent::class)->for($threadId)
    ->addMiddleware(ToolNode::class, new AuditTrail())
    ->chat(new UserMessage('Summarise yesterday\'s orders'))
    ->getMessage();

// Both arguments accept arrays
$agent = app(AssistantAgent::class)->for($threadId)
    ->addMiddleware([ChatNode::class, ToolNode::class], [new AuditTrail()]);
```

`AuditTrail` es una clase tuya: `php artisan neuron:middleware AuditTrail` la genera con los hooks `before()` y `after()` vacíos para que los rellenes.

**Aquí están las clases de nodo, en un namespace real:** `NeuronAI\Agent\Nodes\ChatNode`, `ToolNode`, `StructuredOutputNode`.

Cada modo de interacción está respaldado por un nodo: `ChatNode` ejecuta la inferencia tanto para `chat()` como para `stream()`, `StructuredOutputNode` para `structured()`, y `ToolNode` ejecuta las herramientas. El README todavía enumera un `StreamingNode` aparte para `stream()`; esa clase no existe, y un middleware enganchado a ella nunca se ejecutaría.

**Esta es la Sección 2.3 cobrada del todo.** No puedes usar esta API sin saber que un agente es un flujo de trabajo de nodos con nombre. Esa afirmación, hecha el segundo día del libro, es sobre lo que está construida esta API.

### La aprobación no es middleware

El propio ejemplo de middleware del README engancha un middleware `ToolApproval` a `ToolNode`. Esa clase pertenece a versiones anteriores y ya no existe. La aprobación pertenece al propio `ToolNode` y se configura en la herramienta: la herramienta declara su riesgo, y puedes forzarla o eximirla allí donde la enganchas (Sección 19.3):

```php
$state = app(AssistantAgent::class)->for($threadId)
    ->addTool(DeleteLogFileTool::make()->requireApproval())
    ->chat(new UserMessage('Delete the oldest log file'));

$state->isInterrupted();   // true — the run paused before deleting anything
```

El agente se pausa correctamente. Lo que este no puede hacer es *continuar*: la ejecución pausada y su conversación se guardan en la memoria del proceso, y ambas desaparecen cuando termina la petición. Reanudar en una petición posterior necesita un almacén de mensajes duradero y persistencia del flujo de trabajo, y el Capítulo 18 los añade. La aprobación es el ejemplo más claro del siguiente punto.

### Cuándo llevarla a la clase

El README traza su línea entre la facade y una clase:

> Para memoria propia, varios middleware o comportamientos de agente más avanzados, crea una clase agente dedicada usando `php artisan neuron:agent`.

Ya tienes la clase, así que la línea pasa por dentro de ella: entre lo que enganchas allí donde se llama al agente, como arriba, y lo que la clase declara en sus hooks. Merece la pena añadir otros cuatro desencadenantes:

- El agente debe **pausarse y reanudarse**: aprobación de herramientas, o cualquier otra interrupción
- El agente necesita un **nombre** (`SupportAgent`, no `AssistantAgent`), algo que un colega pueda encontrar y sobre lo que razonar
- El agente necesita **pruebas**
- La configuración del agente aparece en **más de un sitio**

La configuración en el punto de llamada es para prototipos, funcionalidades internas puntuales y scripts de administración. Los hooks de una clase con nombre son para todo lo que tenga un papel en tu aplicación. El Patrón A frente al Patrón B de la Sección 2.4, vestido de Laravel.

### Puntos clave

- La facade `Neuron` lanza una excepción en neuron-ai 4.0.2: su agente nunca recibe un ID de hilo. La sustituye una clase agente generada y vinculada con `for()`.
- `chat()`, `stream()`, `structured()`: los mismos puntos de entrada y tipos de retorno que cualquier clase agente.
- `addTool()` y `addMiddleware()` se encadenan a la copia vinculada.
- Las clases de nodo viven en `NeuronAI\Agent\Nodes\`; `ChatNode` sirve tanto `chat()` como `stream()`.
- La aprobación vive en la herramienta, no en un middleware, y reanudar una ejecución pausada necesita los almacenes duraderos del Capítulo 18.
- Lleva la configuración a la clase cuando el agente deba reanudarse, necesite un nombre o pruebas, o esté configurado dos veces.

## 17.5 Copiar, no mutar: la historia de concurrencia del agente

### El problema que resuelve

El contenedor te entrega un agente, y en un entorno de ejecución de larga vida —Octane, Swoole, RoadRunner, un proceso de cola— un objeto puede sobrevivir a la petición que lo pidió. Registrado como singleton lo hace siempre; guardado en una propiedad de un servicio de larga vida lo hace por accidente.

Ahora piensa en qué le hace a una instancia así una vinculación por mutación:

```php
// Request A
$agent->setThreadId($aliceThread)
    ->addTool(new AdminDeleteTool())
    ->chat(...);

// Request B, milliseconds later, different user, same instance
$agent->chat(...);  // ...whose conversation is this, and does it have the admin tool?
```

`setThreadId()` y `addTool()` cambian el objeto sobre el que se llaman, así que las dos respuestas son la mala: la petición B se ejecuta en el hilo de Alice, con sus mensajes en el prompt y la herramienta de administración disponible. Es una fuga de datos y de privilegios entre peticiones que solo aparece bajo Octane, solo a veces, y que sería extremadamente desagradable de diagnosticar. A una petición B que vincule antes su propio hilo no le va mucho mejor: recibe una `WorkflowException`, porque un agente ya vinculado no se puede apuntar a otro hilo.

### El diseño

`for()` es la respuesta del framework, y el comentario del método enuncia el contrato:

> Una copia vinculada a $workflowId; el receptor nunca se modifica.

Para un agente, el ID del flujo de trabajo es el ID de hilo. Demostrado:

```php
$response = $agent->for($threadId)
    ->addTool(new SearchTool())
    ->addMiddleware(ToolNode::class, new AuditTrail())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

// $agent is untouched — no thread, no tools, no middleware
$agent->for($otherThreadId)->chat(new UserMessage('Hello!'));
```

La clase de la facade del SDK está escrita según la misma regla, y su README dice por qué:

> La facade resuelve un **singleton**, así que los métodos de configuración nunca mutan la instancia compartida: devuelven una copia fresca e independiente que encadenas a la llamada.

La facade tiene el diseño y solo le falta el hilo. `for()` tiene ambos.

### Por qué merece sección propia

Dos razones.

**Es una propiedad de seguridad, no una comodidad.** En un despliegue PHP-FPM sin estado el error sería invisible. Bajo Octane sería una fuga de datos. El diseño anticipa el modelo de despliegue que se está volviendo normal.

**Es un patrón que merece la pena robar.** Configuración inmutable por defecto sobre un servicio compartido —`withX()` que devuelve un clon en vez de `setX()` que muta— es buen diseño en general, y la mayoría de los desarrolladores de PHP ha escrito la versión mutante al menos una vez.

El principio general: **un servicio compartido debería repartir copias configuradas, no dejar que quien lo llama lo reconfigure.**

### La regla práctica

Como `for()` devuelve una copia y deja intacto el receptor, vincular en una sentencia y llamar en la siguiente no hace nada:

```php
// This does NOT work as it appears to
$agent->for($threadId);
$agent->chat(new UserMessage('...'));  // AgentException — $agent still has no thread
```

```php
// Chain it, or hold the copy
$bound = $agent->for($threadId);
$bound->chat(new UserMessage('...'));  // runs on $threadId
```

Simple una vez dicho, y cinco minutos de confusión si no se dice.

La otra mitad de la regla es dónde van los setters. `addTool()` y `addMiddleware()` siguen cambiando el objeto sobre el que se llaman, así que llámalos sobre la copia que devolvió `for()`, nunca sobre la instancia que te dio el contenedor. Y, para empezar, no registres el agente como singleton; el Capítulo 18 muestra cómo debería construirlo el contenedor.

### Puntos clave

- `for()` devuelve una copia vinculada a un hilo; el agente que construyó el contenedor nunca se modifica.
- Previene fugas entre peticiones bajo Octane, Swoole y RoadRunner.
- Encadena la llamada o guarda la copia devuelta: `for()` en una línea aparte no vincula nada.
- `addTool()` y `addMiddleware()` van sobre la copia, no sobre la instancia del contenedor.
- Merece robarse como patrón general para servicios compartidos.

## 17.6 Facades de componentes

### Tres facades

```php
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
```

Cada una expone `driver()`:

```php
class YouTubeAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver('anthropic');
    }
}
```

Forma familiar: el mismo patrón `driver()` de `Cache::driver()`, `Queue::connection()` y `Storage::disk()`. Es deliberado, y por eso no necesita explicación para un público de Laravel. Por debajo son managers normales de Laravel, así que `extend()` registra un driver propio: la Sección 20.1 dice a qué almacenes les conviene. Una advertencia antes de hacerlo: el SDK registra como singletons los managers de proveedores y de incrustaciones, pero no `VectorStoreManager`, así que un driver añadido con `VectorStore::extend()` acaba en una instancia que solo tiene la facade. Desaparece cuando se vacía la caché de la facade, y `app(VectorStoreManager::class)` nunca lo ve. Registra tú el manager, con `$this->app->singleton(VectorStoreManager::class)` en un proveedor de servicios, antes de extenderlo.

### Un agente RAG, completamente configurado

```php
namespace App\Neuron;

use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class MyChatBot extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver('anthropic');
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return EmbeddingProvider::driver('openai');
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return VectorStore::driver('file');
    }
}
```

Compara con la versión en PHP puro de la Sección 12.1: tres constructores con claves, modelos, directorios y nombres. Aquí, tres nombres de driver y todo lo demás en la configuración.

Los drivers de almacén vectorial incluidos son `file`, `pinecone`, `qdrant`, `meilisearch` y `chroma`. Un almacén construido a partir de `config/neuron.php` no tiene esquema de documentos, lo que significa que guarda tus metadatos pero no puede *filtrar* por ellos: filtrar exige declarar los campos de antemano. Eso importa en cuanto llega un segundo inquilino, y el Capítulo 20 construye su almacén en consecuencia.

### Con nombre frente a por defecto

```php
// Explicit driver
AIProvider::driver('anthropic');

// Configured default — NEURON_AI_PROVIDER
AIProvider::driver();
```

**Prefiere el valor por defecto** para la mayoría de los agentes. Nombrar el driver en la clase reintroduce exactamente el acoplamiento que la Sección 3.6 eliminó, y rompe silenciosamente la configuración por entorno de la Sección 17.2, porque un agente que escribe `'anthropic'` a fuego llamará a Anthropic en desarrollo local diga lo que diga `.env.local`. El valor por defecto depende, eso sí, de que `NEURON_AI_PROVIDER` esté definida: sin ella, `driver()` es el `TypeError` de la Sección 17.2.

Nombra el driver solo cuando este agente concreto requiera genuinamente ese proveedor concreto: un modelo barato para un nodo clasificador, un modelo con visión para el extractor de facturas.

### Escalonado de costes, en Laravel

La elección de modelo por agente de la Sección 16.1, expresada con limpieza:

```php
class ClassifierAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver('ollama');   // free, local, good enough
    }
}

class WriterAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();          // the configured default
    }
}
```

Una línea por agente decide adónde va el dinero en todo un sistema multiagente.

Lo que el manager no puede hacer es dar a dos agentes el mismo driver con ajustes distintos. Guarda una sola configuración por driver y cachea lo que construye, así que todo agente que pida `'anthropic'` recibe el mismo objeto proveedor: un modelo, un conjunto de parámetros, un cliente HTTP. Cuando un agente necesite un proveedor propio —un segundo modelo del mismo fabricante, un cliente con su propio tiempo de espera—, constrúyelo dentro del `provider()` de ese agente a partir de `config('neuron.provider.anthropic')`. El framework llama al hook de nuevo en cada segmento de ejecución, y la skill de Laravel de los mantenedores (Sección 17.7) construye así el proveedor de cada agente.

### Puntos clave

- `AIProvider`, `EmbeddingProvider`, `VectorStore`: todas con `driver()`.
- El mismo idioma que `Cache::driver()`; no necesita explicación.
- Prefiere `driver()` sin argumento para que la configuración por entorno siga funcionando.
- Nombra un driver solo cuando ese agente lo requiera de verdad.
- El manager comparte un único proveedor por driver; construye el proveedor en el hook cuando un agente necesite el suyo.

## 17.7 Laravel Boost y el desarrollo asistido por IA

### Qué se incluye

El paquete incluye **directrices para asistentes de código de IA integradas con Laravel Boost**, para ayudar a los asistentes a escribir mejor código de NeuronAI. Llegan como un conjunto de skills de Boost: una para cada tema (agentes, herramientas, aprobación de herramientas, flujos de trabajo, RAG, transmisión, salida estructurada, pruebas, evaluación, monitorización e integración con el frontend).

Por qué importa: como documenta ampliamente el Apéndice A, el ecosistema contiene una gran cantidad de material antiguo. Un asistente de código entrenado con código público producirá con seguridad código escrito para versiones anteriores: `use NeuronAI\Agent;`, `new Edge(...)`, `Tool::make(...)->setCallable(...)`, un middleware `ToolApproval`, `->events()` sobre una transmisión.

Distribuir directrices junto al paquete es una solución directa: el asistente lee lo que es cierto ahora en lugar de lo que era cierto hace dos años. Vale exactamente mientras las directrices sigan el paso del código, y en el SDK 2.0.0 no lo han seguido.

::: {.callout .callout-warning}
[Las skills de Boost incluidas enseñan API eliminada]{.callout-title}

Las skills de neuron-laravel 2.0.0 todavía enseñan `MyAgent::make(threadId: ...)`, `setChatHistory()` con `SQLChatHistory` o `EloquentChatHistory`, `$workflow->resume()` y `abandonRun()`. Nada de eso existe en neuron-ai 4.0.2, y un asistente que siga esas skills escribe código que falla en la primera llamada. Las skills actuales son las trece del paquete core, bajo `vendor/neuron-core/neuron-ai/skills/`: los mismos once temas, más `neuron-laravel-integration` y `neuron-symfony-integration`. Instala esas en su lugar, con el comando que da el README del framework:

```bash
npx skills add ./vendor/neuron-core/neuron-ai/skills -y
```
:::

`neuron-laravel-integration` es la que conviene leer junto al resto de la Parte V. Es el relato de los propios mantenedores sobre cómo cablear NeuronAI en una aplicación Laravel 13: el contenedor, las tablas, la autorización de hilos, las colas, la transmisión, las pruebas. Los capítulos siguientes se apoyan en ella.

### La idea más amplia

Es un patrón que conviene notar más que una simple funcionalidad: **una biblioteca que distribuye instrucciones para las herramientas que escriben código contra ella.**

Si mantienes paquetes, esa idea tiene valor inmediato: cuando los asistentes de tus usuarios generan código incorrecto contra tu biblioteca, esa es tu carga de soporte.

Si estás construyendo sistemas agénticos, cierra un círculo alrededor del que este libro lleva un rato rondando: puedes conectar la documentación de NeuronAI a un asistente de código mediante un servidor MCP (Capítulo 9) y usar agentes para ayudar a construir agentes.

### La advertencia honesta

Mantén un encuadre sobrio. Los asistentes siguen equivocándose con seguridad sobre las bibliotecas que se mueven rápido, y el Apéndice A es la prueba directa: la *documentación oficial* se ha desviado del código en decenas de lugares. Un asistente que lea esa documentación hereda la desviación.

Las directrices incluidas tampoco son inmunes, y este capítulo es la prueba: las skills del SDK ya se han quedado atrás respecto al framework que describen. La skill de aprobación de herramientas del SDK, además, le dice al asistente que declare `approvalPolicy(array $inputs)`; la clase `Tool` declara `approvalPolicy()` sin parámetros y lee las entradas mediante `getInput()`. Un asistente que siga la skill escribe un método que PHP rechaza como sobrescritura incompatible. El propio README del paquete, como ha mostrado este capítulo, todavía contiene ejemplos escritos para una versión anterior. Las directrices reducen la tasa de error; no eliminan la necesidad de comprobar.

La disciplina: usa asistentes para el andamiaje y el boilerplate; verifica cualquier cosa que toque la superficie de la API contra tu versión instalada. Es el mismo hábito que este libro ha aplicado desde el principio, y se transfiere mucho más allá de NeuronAI. El Capítulo 27 va más lejos.

### Puntos clave

- El paquete distribuye directrices para asistentes de código como skills de Laravel Boost.
- Existe porque el corpus público está lleno de código escrito para versiones anteriores.
- Las directrices también pueden desviarse: en el SDK 2.0.0 enseñan API que la 4.0.2 eliminó.
- Usa las skills de `vendor/neuron-core/neuron-ai/skills/`, entre ellas `neuron-laravel-integration`.
- Buen patrón para los mantenedores de bibliotecas en general.
- Verifica el código generado contra tu versión instalada, siempre.

## Laboratorio 11 — Cinco minutos hasta la primera respuesta

**Cubre:** la configuración, el generador de agentes, la vinculación de un hilo y saber cuándo la configuración va en la clase.

### Objetivo

Un punto de conexión `POST /api/ask` funcionando, respondido por una clase agente generada, desde `composer require` hasta la primera respuesta en unos cinco minutos. Luego la mitad más interesante: identificar el punto exacto en el que configurar el agente en el controlador deja de ser la herramienta adecuada.

### Parte uno: hazlo funcionar

1. Instala el SDK y publica la configuración.
2. Pon `NEURON_AI_PROVIDER=ollama` en `.env`, con `OLLAMA_MODEL` apuntando a un modelo que ya hayas descargado, para que esto no cueste nada.
3. Ejecuta `php artisan neuron:agent AssistantAgent` y deja la clase generada tal cual.
4. Escribe un controlador que lea `message` de la petición, vincule el agente a un hilo y devuelva su respuesta, y una ruta hacia él en `routes/api.php` (`php artisan install:api` crea ese archivo si tu aplicación no lo tiene).
5. Confírmalo con `curl`.

Esa es toda la primera parte, y debería llevar genuinamente unos minutos. El controlador son tres sentencias:

```php
namespace App\Http\Controllers;

use App\Neuron\Agents\AssistantAgent;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\UniqueIdGenerator;

class AskController extends Controller
{
    public function __invoke(Request $request, AssistantAgent $agent): JsonResponse
    {
        $data = $request->validate(['message' => ['required', 'string']]);

        $state = $agent
            ->for(UniqueIdGenerator::generateId('ask_'))
            ->chat(new UserMessage($data['message']));

        return response()->json(['answer' => $state->getMessage()?->getContent()]);
    }
}
```

```bash
curl -s http://localhost:8000/api/ask \
    -H 'Accept: application/json' \
    -d 'message=How do I implement a PSR-15 middleware without a framework?'
```

Laravel resuelve `AssistantAgent` del contenedor porque el método lo pide. El punto de conexión responde preguntas sueltas, así que cada petición acuña un ID de hilo nuevo y nada sobrevive a la respuesta. El día en que un usuario deba poder hacer una pregunta de seguimiento, el hilo tendrá que salir de algún sitio y la conversación tendrá que vivir en algún sitio: eso es el Capítulo 18.

### Parte dos: rómpelo deliberadamente

Ahora añade requisitos de uno en uno y anota dónde empieza a doler cada uno:

1. **El punto de conexión necesita un prompt de sistema específico de tu producto.** ¿Configuración o código?
2. **Necesita una herramienta.** ¿Sigues cómodo en el controlador?
3. **Necesita una prueba.** ¿Cómo pones un proveedor falso detrás del punto de conexión?
4. **Un segundo punto de conexión necesita la misma configuración.** ¿Dónde vive ahora?

Para el requisito tres o cuatro deberías estar sacando cosas del controlador y llevándolas a la clase: el prompt a `instructions()`, la herramienta a `tools()`. Esa es la lección: no que configurar en el punto de llamada sea malo, sino que puedes sentir exactamente cuándo deja de encajar.

### Criterios de aceptación

- `POST /api/ask` devuelve una respuesta sensata con `NEURON_AI_PROVIDER=ollama` y sin ninguna clave de API configurada.
- Cambiar a un proveedor en la nube requiere solo un cambio en `.env`.
- Puedes decir, en una frase, cuál de los cuatro requisitos anteriores empujó la configuración a la clase.

### Una trampa que evitar

No vincules en una sentencia y llames en la siguiente: Sección 17.5. Si tu controlador llama a `$agent->for(...)` en una línea y a `$agent->chat(...)` en la siguiente, la copia vinculada se desecha y la llamada falla con `AgentException: This agent has no thread ID`. Escríbelo como una única cadena. Cuando llegues al requisito dos, la herramienta entra en esa cadena después de `for()`; confirma que se está ofreciendo de verdad.
