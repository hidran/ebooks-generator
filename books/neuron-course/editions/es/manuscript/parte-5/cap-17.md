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

**Requisitos:** este libro usa Laravel 13 sobre PHP 8.5, con la versión 2.x del SDK, la línea construida para NeuronAI v4, que arrastra `neuron-core/neuron-ai` 4.x. El paquete en sí acepta versiones anteriores de Laravel y de PHP; el código del libro necesita PHP 8.5.

### Qué aporta

Cinco cosas, según la descripción del propio paquete:

- Un archivo de configuración para las credenciales del proveedor de IA y de las incrustaciones
- Comandos de Artisan para generar el esqueleto de los componentes más usados
- Facades que instancian proveedores y almacenes vectoriales a partir de la configuración
- Migraciones listas para usar para `EloquentChatHistory`
- Directrices para asistentes de código de IA integradas con Laravel Boost

La lista se queda corta con un elemento. Las migraciones cubren más que el historial de conversación: también crean la tabla `workflow_store` en la que persisten los agentes y flujos de trabajo duraderos, que la Sección 18.4 pone a trabajar.

### La filosofía, citada

El README se abre con una afirmación que merece leerse entera:

> Neuron no necesita abstracciones invasivas. Ya tiene una sintaxis muy simple, código tipado al 100 % e interfaces claras en las que puedes apoyarte para desarrollar tu sistema agéntico o crear plugins y extensiones propios.

Y:

> En este paquete te proporcionamos un kit de desarrollo diseñado específicamente para los puntos de integración con Laravel **sin limitar el acceso a los componentes nativos de Neuron.** También puedes usar este paquete como inspiración para diseñar tu propio patrón de integración a medida.

De ahí se siguen tres cosas, y son la razón de que la Parte V venga después de las Partes II a IV y no en su lugar:

**Todo lo que aprendiste sigue funcionando.** Tus clases agente, herramientas, flujos de trabajo y pipelines de RAG no cambian. El SDK añade puntos de entrada; no sustituye la API.

**El SDK es opcional.** Puedes hacer `composer require neuron-core/neuron-ai` en una app Laravel y cablear tú el contenedor. El SDK te ahorra una tarde.

**Es una implementación de referencia.** El paquete te invita explícitamente a usarlo como inspiración para tu propia integración. Si trabajas en Symfony, Spryker o un framework interno heredado, lee el código de este paquete y construye el equivalente: los puntos de integración son los mismos.

Ese último punto importa si no estás en Laravel. Esta parte es transferible.

### Puntos clave

- `composer require neuron-core/neuron-laravel`; Laravel 13 sobre PHP 8.5; SDK 2.x para NeuronAI v4.
- Configuración, generadores, facades, migraciones (historial de conversación y almacén de flujos de trabajo), directrices de Boost.
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

Más, para el trazado:

```dotenv
INSPECTOR_INGESTION_KEY=fwe45gtxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

El README presenta esa clave como todo lo que necesitas. No lo es. El framework core no depende de Inspector y no engancha ningún observador por su cuenta: el trazado es un oyente PSR-14 que suscribes explícitamente (Capítulo 10). En Laravel eso significa requerir `inspector-apm/inspector-laravel`, mantener la clave de arriba y suscribir el `InspectorSubscriber` de Inspector a `ObservabilityEvent` en los agentes que quieras trazar, en una clase base compartida o dondequiera que tu contenedor construya los agentes, para que no se escape ninguno. Una clave sin suscripción no produce trazas, ni ningún error que te lo avise.

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

El modelo de *incrustaciones* no debe variar según el entorno. Incrustaciones distintas significan índices vectoriales incompatibles. Fíjalo en `config/neuron.php` en lugar de dejarlo a `.env`, o acabarás depurando un sistema RAG que devuelve disparates solo en staging.
:::

### El prompt de sistema en configuración

El README muestra el prompt de sistema viniendo de la configuración:

```php
protected function instructions(): string
{
    return (string) new SystemPrompt(...config('neuron.system_prompt'));
}
```

Útil para un asistente por defecto. **No** es el patrón correcto para un agente real: un prompt es una especificación (Sección 3.5), y las especificaciones van en el código, bajo control de versiones, revisadas. Un archivo de configuración que un despliegue puede cambiar sin revisión de código es el hogar equivocado para el comportamiento.

Úsalo para el valor por defecto de la facade; declara las instrucciones en la clase agente para todo lo que importe.

::: {.callout .callout-warning}
[Dos problemas en ese fragmento del README]{.callout-title}

El ejemplo publicado dice `return (string) new SystemPrompt(...config('neuron.system_prompt');`: falta un paréntesis de cierre. Además usa `use NeuronAI\Agent;` y `use NeuronAI\SystemPrompt;`, que son namespaces de versiones anteriores. Las clases son `NeuronAI\Agent\Agent` y `NeuronAI\Agent\SystemPrompt`. Apéndice A, puntos 39 y 40.
:::

El tipo de retorno string es correcto. La firma del propio framework es `instructions(): SystemMessage|string` —un `SystemMessage` te permite dividir las instrucciones en bloques y marcar el estático para el prompt caching—, pero un string simple se acepta y se envuelve por ti, y restringir el tipo de retorno a `string` en tu clase es legal. La clase que genera `neuron:agent` (Sección 17.3) hace exactamente eso.

### Puntos clave

- `vendor:publish --tag=neuron-config` y luego las variables de entorno.
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

`php artisan neuron:agent MyAgent` crea `app/Neuron/Agents/MyAgent.php` con los métodos básicos esbozados. Los stubs se ajustan a la API actual del framework: la herramienta generada, por ejemplo, declara su identidad como propiedades `protected string $name` y `protected ?string $description` sin constructor, la forma que usa el Capítulo 19 de principio a fin.

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

Los generadores no coinciden todos con este árbol de serie: `neuron:tool` escribe en `app/Neuron/Agents/Tools` y `neuron:rag` en `app/Neuron/RAG`. Mueve los archivos una vez, o pasa al comando el nombre de clase completamente cualificado; en cualquier caso, decide el árbol antes del décimo archivo, no después.

### Puntos clave

- Seis generadores, todos `php artisan neuron:*`.
- Solo el nombre: sin namespace, sin escapes, sin diferencias de sistema operativo.
- Mantén todo lo agéntico bajo `app/Neuron`.

## 17.4 La facade Neuron

### Por qué existe

El autor del framework describe el problema con honestidad:

> Antes de esta versión, usar Neuron AI dentro de Laravel significaba crear una clase agente dedicada, extender `Agent`, implementar un método `provider()` y cablear tú mismo el prompt de sistema. Ese patrón es el correcto una vez que tu agente tiene personalidad, un conjunto de herramientas y un papel en tu aplicación. Pero es mucha ceremonia para un desarrollador que solo quiere comprobar si Claude, o GPT, o Gemini responden bien a un prompt dado.

Una facade es la respuesta de Laravel a esa forma de problema, y este es un uso de manual.

### Los tres modos

```php
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Laravel\Facades\Neuron;

// Chat (synchronous) — returns the final AgentState
$response = Neuron::chat(new UserMessage('Hello!'))->getMessage();
echo $response?->getContent();

// Stream (real-time chunks) — the call itself is the generator
foreach (Neuron::stream(new UserMessage('Hello')) as $chunk) {
    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}

// Structured output
$person = Neuron::structured(new UserMessage('I am John and I like pizza!'), Person::class);
```

Los mismos tres puntos de entrada de la tabla de la Sección 6.3 —`chat()`, `stream()`, `structured()`— sin ninguna clase que escribir, y con los mismos tipos de retorno que en una clase agente: `chat()` se ejecuta hasta el final y devuelve el `AgentState`, `stream()` es un generador que recorres directamente, `structured()` devuelve el objeto. Lee el proveedor por defecto y el prompt de sistema de la configuración.

::: {.callout .callout-warning}
[El bucle de transmisión del README está desfasado]{.callout-title}

El README del paquete todavía itera `Neuron::stream(...)->events()` e imprime `$event->content`, la forma que usaban las versiones anteriores. `stream()` devuelve el propio generador —no hay ningún `events()` que llamar sobre él— y produce varios tipos de chunk, así que filtra por `TextChunk` como arriba. `getMessage()` también es nullable, de ahí el `?->`.
:::

### Enganchar herramientas

```php
$response = Neuron::tools(new SearchTool())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

$response = Neuron::tools([new SearchTool(), CalculatorToolkit::make()])
    ->chat(new UserMessage('Hello!'))
    ->getMessage();
```

Instancia única o array.

### Enganchar middleware

```php
use App\Neuron\Middleware\AuditTrail;
use NeuronAI\Agent\Nodes\ChatNode;
use NeuronAI\Agent\Nodes\ToolNode;

// Record every tool execution in the audit log
$response = Neuron::middleware(ToolNode::class, new AuditTrail())
    ->chat(new UserMessage('Summarise yesterday\'s orders'))
    ->getMessage();

// Both arguments accept arrays
$neuron = Neuron::middleware([ChatNode::class, ToolNode::class], [new AuditTrail()]);
```

`AuditTrail` es una clase tuya: `php artisan neuron:middleware AuditTrail` la genera con los hooks `before()` y `after()` vacíos para que los rellenes.

**Aquí están las clases de nodo, en un namespace real:** `NeuronAI\Agent\Nodes\ChatNode`, `ToolNode`, `StructuredOutputNode`.

Cada modo de interacción está respaldado por un nodo: `ChatNode` ejecuta la inferencia tanto para `chat()` como para `stream()`, `StructuredOutputNode` para `structured()`, y `ToolNode` ejecuta las herramientas. El README todavía enumera un `StreamingNode` aparte para `stream()`; esa clase no existe, y un middleware enganchado a ella nunca se ejecutaría.

**Esta es la Sección 2.3 cobrada del todo.** No puedes usar esta API sin saber que un agente es un flujo de trabajo de nodos con nombre. Esa afirmación, hecha el segundo día del libro, es sobre lo que está construida esta API.

### La aprobación no es middleware

El propio ejemplo de middleware del README engancha un middleware `ToolApproval` a `ToolNode`. Esa clase pertenece a versiones anteriores y ya no existe. La aprobación pertenece al propio `ToolNode` y se configura en la herramienta: la herramienta declara su riesgo, y puedes forzarla o eximirla allí donde la enganchas (Sección 19.3):

```php
$state = Neuron::tools(DeleteLogFileTool::make()->requireApproval())
    ->chat(new UserMessage('Delete the oldest log file'));

$state->isInterrupted();   // true — the run paused before deleting anything
```

La facade se pausará correctamente. Lo que no puede hacer es *continuar*: reanudar una ejecución pausada necesita un ID de hilo, un historial de conversación duradero y persistencia del flujo de trabajo (Secciones 18.2 y 18.4), y la facade no configura nada de eso. La aprobación es el ejemplo más claro del siguiente punto.

### Cuándo dejar de usar la facade

El README lo dice sin rodeos:

> Para memoria propia, varios middleware o comportamientos de agente más avanzados, crea una clase agente dedicada usando `php artisan neuron:agent`.

Merece la pena añadir otros cuatro desencadenantes:

- El agente debe **pausarse y reanudarse**: aprobación de herramientas, o cualquier otra interrupción
- El agente necesita un **nombre**, algo que un colega pueda encontrar y sobre lo que razonar
- El agente necesita **pruebas**
- La configuración del agente aparece en **más de un sitio**

La facade es para prototipos, funcionalidades internas puntuales y scripts de administración. La clase es para todo lo que tenga un papel en tu aplicación. El Patrón A frente al Patrón B de la Sección 2.4, vestido de Laravel.

### Puntos clave

- `Neuron::chat()`, `::stream()`, `::structured()`: no se requiere clase; mismos tipos de retorno que una clase agente.
- `::tools()` y `::middleware()` se encadenan a la llamada.
- Las clases de nodo viven en `NeuronAI\Agent\Nodes\`; `ChatNode` sirve tanto `chat()` como `stream()`.
- La aprobación vive en la herramienta, no en un middleware, y la facade no puede reanudar una ejecución pausada.
- Pasa a una clase cuando el agente deba reanudarse, necesite un nombre o pruebas, o aparezca dos veces.

## 17.5 Copiar, no mutar: la historia de concurrencia de la facade

### El problema que resuelve

Una facade resuelve un singleton. En un entorno de ejecución de larga vida —Octane, Swoole, RoadRunner— esa instancia persiste entre peticiones.

Ahora piensa en qué haría una implementación ingenua:

```php
// Request A
Neuron::tools(new AdminDeleteTool())->chat(...);

// Request B, milliseconds later, different user
Neuron::chat(...);  // ...does request B have the admin tool?
```

Si `tools()` mutara la instancia compartida, la respuesta sería que sí, y tendrías una fuga de privilegios entre peticiones que solo aparece bajo Octane, solo a veces, y que sería extremadamente desagradable de diagnosticar.

### El diseño

El README lo aborda directamente:

> La facade resuelve un **singleton**, así que los métodos de configuración nunca mutan la instancia compartida: devuelven una copia fresca e independiente que encadenas a la llamada. Esto significa que cada `Neuron::chat(...)` parte del valor por defecto limpio y configurado, salvo que enganches explícitamente herramientas o middleware.

Demostrado:

```php
$response = Neuron::tools(new SearchTool())
    ->middleware(ToolNode::class, new AuditTrail())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

// The singleton is untouched — this call has no tools or middleware
Neuron::chat(new UserMessage('Hello!'));
```

### Por qué merece sección propia

Dos razones.

**Es una propiedad de seguridad, no una comodidad.** En un despliegue PHP-FPM sin estado el error sería invisible. Bajo Octane sería una fuga de datos. El diseño anticipa el modelo de despliegue que se está volviendo normal.

**Es un patrón que merece la pena robar.** Configuración inmutable por defecto sobre un servicio compartido —`withX()` que devuelve un clon en vez de `setX()` que muta— es buen diseño en general, y la mayoría de los desarrolladores de PHP ha escrito la versión mutante al menos una vez.

El principio general: **un servicio compartido debería repartir copias configuradas, no dejar que quien lo llama lo reconfigure.**

### La regla práctica

Como cada cadena es independiente, no puedes ir acumulando configuración entre sentencias:

```php
// This does NOT work as it appears to
Neuron::tools(new SearchTool());
Neuron::chat(new UserMessage('...'));  // no tools — different copy
```

```php
// Chain it, or hold the copy
$agent = Neuron::tools(new SearchTool());
$agent->chat(new UserMessage('...'));  // has tools
```

Simple una vez dicho, y cinco minutos de confusión si no se dice.

### Puntos clave

- La facade es un singleton; `tools()` y `middleware()` devuelven copias independientes.
- Previene fugas entre peticiones bajo Octane, Swoole y RoadRunner.
- Encadena la llamada o guarda la instancia devuelta: la configuración no se acumula entre sentencias.
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

Forma familiar: el mismo patrón `driver()` de `Cache::driver()`, `Queue::connection()` y `Storage::disk()`. Es deliberado, y por eso no necesita explicación para un público de Laravel. Por debajo son managers normales de Laravel, así que `extend()` registra un driver propio: la Sección 20.1 usa exactamente eso.

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

**Prefiere el valor por defecto** para la mayoría de los agentes. Nombrar el driver en la clase reintroduce exactamente el acoplamiento que la Sección 3.6 eliminó, y rompe silenciosamente la configuración por entorno de la Sección 17.2, porque un agente que escribe `'anthropic'` a fuego llamará a Anthropic en desarrollo local diga lo que diga `.env.local`.

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

### Puntos clave

- `AIProvider`, `EmbeddingProvider`, `VectorStore`: todas con `driver()`.
- El mismo idioma que `Cache::driver()`; no necesita explicación.
- Prefiere `driver()` sin argumento para que la configuración por entorno siga funcionando.
- Nombra un driver solo cuando ese agente lo requiera de verdad.

## 17.7 Laravel Boost y el desarrollo asistido por IA

### Qué se incluye

El paquete incluye **directrices para asistentes de código de IA integradas con Laravel Boost**, para ayudar a los asistentes a escribir mejor código de NeuronAI. Llegan como un conjunto de skills de Boost: una para cada tema (agentes, herramientas, aprobación de herramientas, flujos de trabajo, RAG, transmisión, salida estructurada, pruebas, evaluación, monitorización e integración con el frontend).

Por qué importa: como documenta ampliamente el Apéndice A, el ecosistema contiene una gran cantidad de material antiguo. Un asistente de código entrenado con código público producirá con seguridad código escrito para versiones anteriores: `use NeuronAI\Agent;`, `new Edge(...)`, `Tool::make(...)->setCallable(...)`, un middleware `ToolApproval`, `->events()` sobre una transmisión.

Distribuir directrices actuales junto al paquete es una solución directa. El asistente lee lo que es cierto ahora en lugar de lo que era cierto hace dos años.

### La idea más amplia

Es un patrón que conviene notar más que una simple funcionalidad: **una biblioteca que distribuye instrucciones para las herramientas que escriben código contra ella.**

Si mantienes paquetes, esa idea tiene valor inmediato: cuando los asistentes de tus usuarios generan código incorrecto contra tu biblioteca, esa es tu carga de soporte.

Si estás construyendo sistemas agénticos, cierra un círculo alrededor del que este libro lleva un rato rondando: puedes conectar la documentación de NeuronAI a un asistente de código mediante un servidor MCP (Capítulo 9) y usar agentes para ayudar a construir agentes.

### La advertencia honesta

Mantén un encuadre sobrio. Los asistentes siguen equivocándose con seguridad sobre las bibliotecas que se mueven rápido, y el Apéndice A es la prueba directa: la *documentación oficial* se ha desviado del código en decenas de lugares. Un asistente que lea esa documentación hereda la desviación.

Las directrices incluidas tampoco son inmunes. La skill de aprobación de herramientas del paquete le dice al asistente que declare `approvalPolicy(array $inputs)`; la clase `Tool` declara `approvalPolicy()` sin parámetros y lee las entradas mediante `getInput()`. Un asistente que siga la skill escribe un método que PHP rechaza como sobrescritura incompatible. El propio README del paquete, como ha mostrado este capítulo, todavía contiene ejemplos escritos para una versión anterior. Las directrices reducen la tasa de error; no eliminan la necesidad de comprobar.

La disciplina: usa asistentes para el andamiaje y el boilerplate; verifica cualquier cosa que toque la superficie de la API contra tu versión instalada. Es el mismo hábito que este libro ha aplicado desde el principio, y se transfiere mucho más allá de NeuronAI. El Capítulo 27 va más lejos.

### Puntos clave

- El paquete distribuye directrices actuales para asistentes de código como skills de Laravel Boost.
- Existe porque el corpus público está lleno de código escrito para versiones anteriores.
- Las directrices también pueden desviarse: la skill de aprobación ya lo ha hecho.
- Buen patrón para los mantenedores de bibliotecas en general.
- Verifica el código generado contra tu versión instalada, siempre.

## Laboratorio 11 — Cinco minutos hasta la primera respuesta

**Cubre:** la facade, la configuración y saber cuándo abandonar ambas.

### Objetivo

Un punto de conexión `POST /api/ask` funcionando, respondido a través de la facade, desde `composer require` hasta la primera respuesta en unos cinco minutos. Luego la mitad más interesante: identificar el punto exacto en el que la facade deja de ser la herramienta adecuada.

### Parte uno: hazlo funcionar

1. Instala el SDK y publica la configuración.
2. Pon `NEURON_AI_PROVIDER=ollama` en `.env` para que esto no cueste nada.
3. Escribe una ruta y un controlador que lea `message` de la petición y devuelva la respuesta de la facade.
4. Confírmalo con `curl`.

Esa es toda la primera parte, y debería llevar genuinamente unos minutos. El controlador son cuatro líneas.

### Parte dos: rómpelo deliberadamente

Ahora añade requisitos de uno en uno y anota dónde empieza a doler cada uno:

1. **El punto de conexión necesita un prompt de sistema específico de tu producto.** ¿Configuración o código?
2. **Necesita una herramienta.** ¿Sigues cómodo en el controlador?
3. **Necesita una prueba.** ¿Cómo simulas la facade?
4. **Un segundo punto de conexión necesita la misma configuración.** ¿Dónde vive ahora?

Para el requisito tres o cuatro deberías estar alargando la mano hacia `php artisan neuron:agent`. Esa es la lección: no que la facade sea mala, sino que puedes sentir exactamente cuándo deja de encajar.

### Criterios de aceptación

- `POST /api/ask` devuelve una respuesta sensata con `NEURON_AI_PROVIDER=ollama` y sin ninguna clave de API configurada.
- Cambiar a un proveedor en la nube requiere solo un cambio en `.env`.
- Puedes decir, en una frase, cuál de los cuatro requisitos anteriores te empujó a una clase.

### Una trampa que evitar

No acumules configuración de la facade entre sentencias: Sección 17.5. Si tu controlador llama a `Neuron::tools(...)` en una línea y a `Neuron::chat(...)` en la siguiente, las herramientas están silenciosamente ausentes. Escríbelo como una única cadena y confirma que la herramienta se está ofreciendo de verdad.
