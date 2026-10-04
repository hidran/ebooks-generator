# Capítulo 3 — Configuración y tu primer agente

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch03`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch03), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 3.1 El esqueleto del proyecto

Vamos a construir un proyecto limpio en PHP puro que soportará todos los ejemplos de las Partes II, III y IV. Sin framework, sin magia.

### Por qué PHP puro primero

Vas a pasar la Parte V dentro de Laravel, donde el contenedor te entrega un agente configurado y un comando de artisan genera tus clases. Esa comodidad vale la pena, pero solo después de haber visto qué está ocultando. Todo lo que hace el SDK de Laravel ya lo habrás hecho a mano.

Esto importa también comercialmente: una parte grande del trabajo en PHP no es Laravel. Symfony, Spryker, WordPress, MVC internos heredados. Un agente construido sobre el paquete puro encaja en cualquiera de ellos.

### Crear el proyecto

```bash
mkdir -p neuron-course/01-plain-php && cd neuron-course/01-plain-php

mkdir -p src/Agents src/Tools src/Dto examples storage/chat
touch bootstrap.php .env .env.example .gitignore
touch storage/chat/.gitkeep
```

```bash
composer init --name="yourname/neuron-lab" --type=project --no-interaction
```

### composer.json

```json
{
    "name": "yourname/neuron-lab",
    "type": "project",
    "require": {
        "php": "^8.5"
    },
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    },
    "config": {
        "sort-packages": true
    },
    "minimum-stability": "stable",
    "prefer-stable": true
}
```

El bloque PSR-4 mapea el namespace `App\` a `src/`. `App\Agents\WeatherAgent` vive en `src/Agents/WeatherAgent.php`. Nada exótico, pero si te equivocas todos los ejemplos posteriores fallarán con un error de clase no encontrada, así que verifícalo ahora:

```bash
composer dump-autoload
```

### .gitignore

```gitignore
/vendor/
/storage/chat/*
!/storage/chat/.gitkeep
.env
.phpunit.result.cache
```

Dos líneas aquí son estructurales. `/vendor/` porque es regenerable. `.env` porque contendrá claves de API, y una clave filtrada en un repositorio público se te factura en cuestión de horas. La Sección 3.7 lo cubre como es debido.

### Estructura final

```
01-plain-php/
├── composer.json
├── bootstrap.php
├── .env                 ← claves reales, nunca versionadas
├── .env.example         ← solo la estructura, versionada
├── src/
│   ├── Agents/
│   ├── Tools/
│   └── Dto/
├── examples/            ← un script ejecutable por sección
└── storage/chat/        ← conversaciones persistidas
```

### Puntos clave

- PHP puro primero; el SDK del framework añade comodidad, no capacidad.
- PSR-4 mapea `App\` → `src/`; verifícalo con `composer dump-autoload` antes de escribir código.
- `.env` está en `.gitignore` desde el minuto uno.

## 3.2 Instalar NeuronAI

### La instalación

```bash
composer require neuron-core/neuron-ai vlucas/phpdotenv
```

**`neuron-core/neuron-ai`** — el framework. Necesita la extensión `curl` y muy poco más: su única dependencia de Composer es la interfaz PSR-14 del despachador de eventos.

**`vlucas/phpdotenv`** — lee un archivo `.env` y lo carga en el entorno. Laravel lo incluye; PHP puro no. Sin él tendrías que escribir las claves de API a fuego, cosa que no vamos a hacer.

**PHP 8.5.** NeuronAI en sí funciona con PHP 8.1 o posterior, pero el código de este libro necesita PHP 8.5, así que comprueba `php -v` antes de seguir. Por el camino te encontrarás con un puñado de novedades de 8.5: el operador pipe `|>`, `clone($object, [...])` para copiar un objeto readonly cambiando algunas propiedades, el atributo `#[\NoDiscard]`, `array_first()` y `array_last()`, y la extensión URI integrada. Se usan donde hacen el código más claro, no en todas partes, y cada una se explica la primera vez que aparece.

Fíjate en lo que falta: un paquete de cliente HTTP. NeuronAI no depende de Guzzle ni de ningún otro: cada proveedor, almacén vectorial y juego de herramientas habla HTTP a través del propio `CurlHttpClient` del framework, y por eso `ext-curl` es un requisito obligatorio. Cuando nuestras propias herramientas llamen a APIs externas en el Capítulo 5, reutilizarán ese mismo cliente, así que el proyecto no necesita nada más.

Comprueba la extensión antes que nada:

```bash
php -m | grep -i curl
```

Si no hay salida, no hay `curl`, y la primera llamada a un proveedor falla. En la mayoría de las distribuciones Linux es un paquete aparte (`php8.5-curl` o similar); en macOS con el PHP de Homebrew viene incluida.

::: {.callout .callout-tip}
[Cuando quieres Guzzle de todos modos]{.callout-title}

Si tu aplicación ya hace pasar el HTTP saliente por un `HandlerStack` de Guzzle —para reintentos, un proxy corporativo, registro de peticiones—, puedes hacer pasar también el tráfico hacia los proveedores por esa misma pila. Instala tú mismo `guzzlehttp/guzzle` y luego entrega el adaptador de NeuronAI, `NeuronAI\HttpClient\Guzzle\GuzzleHttpClient`, a cualquier proveedor con `setHttpClient()`. El comportamiento por defecto no necesita nada de esto; el adaptador está ahí para cuando quieras una única política HTTP para toda la aplicación.
:::

### Fija la versión

```json
"require": {
    "php": "^8.5",
    "neuron-core/neuron-ai": "^4.0.2",
    "vlucas/phpdotenv": "^5.6"
}
```

La restricción dice: 4.0.2, la versión contra la que se escribió y se ejecutó este libro, o una 4.x posterior. **Versiona `composer.lock` en un repositorio didáctico.** No es el consejo habitual para bibliotecas: es deliberado. Quien siga este libro dentro de un año debe obtener la misma API contra la que se escribió. Sin el archivo de bloqueo obtendrá lo que `^4.0.2` resuelva ese día y, si una publicación menor cambió una firma, obtendrá un error con el que nadie podrá ayudarle. La Sección 27.1 va un paso más allá para una aplicación que despliegas: exige la versión exacta, para que una actualización nunca la mueva sin una decisión.

### Verifica

```bash
php -r "require 'vendor/autoload.php'; echo interface_exists(NeuronAI\Chat\History\MessageStoreInterface::class) ? 'OK' : 'FAIL';"
```

La interfaz que comprueba llegó con la versión 4.0, así que `OK` significa que tienes la API para la que está escrito este libro y `FAIL` significa un paquete más antiguo. Compruébalo con:

```bash
composer show neuron-core/neuron-ai | head -5
```

### Unas palabras sobre las versiones y la documentación

El código de ejemplo de internet procede de varias generaciones de NeuronAI, y el escrito para versiones anteriores falla de dos maneras distintas.

El código más antiguo usa namespaces que ya no existen —`NeuronAI\Agent` donde este libro tiene `NeuronAI\Agent\Agent`, `NeuronAI\SystemPrompt` donde tiene `NeuronAI\Agent\SystemPrompt`— y falla en la instrucción `use`. El código más reciente es más sutil: los imports se resuelven y luego un método no existe o devuelve algo distinto. Los primeros sitios donde te toparás con esto son lo que devuelve `chat()` y cómo recibe una ejecución su ID de hilo (Sección 3.4), cómo se guardan las conversaciones (Capítulo 4), cómo declara una herramienta su nombre y su descripción (Capítulo 5) y cómo se arranca un flujo de trabajo (Capítulo 13).

Partes de la documentación oficial, varias entradas de blog y la mayoría de los artículos de terceros siguen mostrando código más antiguo. Cuando encuentres código de ejemplo que no coincida con este libro, comprueba a qué versión apunta antes de dar por hecho que algo está roto. Es la fuente de confusión más común para quien llega desde tutoriales.

### Puntos clave

- `composer require neuron-core/neuron-ai` con `ext-curl`; Guzzle es opcional. El código del libro necesita PHP 8.5.
- Fija la versión y versiona `composer.lock` en los repositorios didácticos.
- El código escrito para versiones anteriores falla en sus namespaces o en tipos de retorno y firmas que cambiaron. Comprueba la versión antes de depurar.

## 3.3 La CLI del framework

Los generadores crean componentes del framework con la estructura correcta. Conviene saber qué producen, porque también querrás escribir estas clases a mano.

### El binario

Instalar el paquete te da un ejecutable en `vendor/bin/neuron`.

```bash
./vendor/bin/neuron
```

Ejecutado sin argumentos, lista sus comandos: una familia de generadores `make:*`, más `evaluation`, que ejecuta las suites de evaluación del Capítulo 10.

### Los generadores

**Unix / macOS** — fíjate en las barras invertidas dobles, que la shell necesita:

```bash
./vendor/bin/neuron make:agent App\\Agents\\AssistantAgent
./vendor/bin/neuron make:tool App\\Tools\\WeatherTool
./vendor/bin/neuron make:node App\\Workflow\\InitialNode
./vendor/bin/neuron make:event App\\Workflow\\FirstEvent
```

**PowerShell de Windows** — barras invertidas simples:

```powershell
.\vendor\bin\neuron make:agent App\Agents\AssistantAgent
.\vendor\bin\neuron make:tool App\Tools\WeatherTool
.\vendor\bin\neuron make:node App\Workflow\InitialNode
.\vendor\bin\neuron make:event App\Workflow\FirstEvent
```

Esa diferencia de barras invertidas cuesta más tiempo perdido del que le corresponde. Si un comando generador parece no hacer nada, cuenta primero tus barras invertidas.

### Qué produce cada uno

| Comando | Produce | Se cubre en |
|---|---|---|
| `make:agent` | Clase que extiende `Agent` con los esbozos de `provider()`, `instructions()`, `tools()` y `middleware()` | Capítulo 3 |
| `make:tool` | Clase que extiende `Tool` con las propiedades `$name`/`$description`, `properties()` e `__invoke()` | Capítulo 5 |
| `make:rag` | Clase que extiende `RAG` | Capítulo 11 |
| `make:workflow` | Clase que extiende `Workflow` con un esbozo de `nodes()` | Capítulo 13 |
| `make:node` | Nodo de flujo de trabajo con un esbozo de `__invoke(StartEvent, WorkflowState)` | Capítulo 13 |
| `make:event` | Clase de evento que implementa `Event` | Capítulo 13 |
| `make:middleware` | Clase que implementa `WorkflowMiddleware` con `before()` y `after()` | Capítulo 15 |
| `make:evaluators` | Clase evaluadora para el ejecutor `evaluation` | Capítulo 10 |

Los generadores escriben el archivo en la ruta implicada por tu mapeo PSR-4. `App\Agents\AssistantAgent` aterriza en `src/Agents/AssistantAgent.php` gracias al mapeo que fijamos en la Sección 3.1. Si aterriza en un sitio inesperado, tu bloque de autoload está mal.

### La postura honesta sobre los generadores

Ahorran teclear e imponen una convención de nombres. Ese es todo el beneficio. Cada clase que producen es PHP corriente que podrías teclear tú en noventa segundos, y en este libro las escribimos a mano con frecuencia, porque quien solo ha generado un agente no sabe realmente qué es un agente.

Lee lo que producen antes de construir encima. Un generador escribe un punto de partida, no una clase terminada: el agente generado, por ejemplo, devuelve un proveedor `Anthropic` con las cadenas de relleno `'ANTHROPIC_KEY'` y `'ANTHROPIC_MODEL'` allí donde tiene que ir tu configuración, y una herramienta generada lleva el nombre de su clase hasta que le das un nombre y una descripción de verdad.

Úsalos cuando te hagan productivo. No los uses como sustituto de entender la forma de la clase.

### Puntos clave

- Los generadores siguen los bloques de construcción del framework: agente, herramienta, RAG, flujo de trabajo, nodo, evento, middleware, evaluador.
- Unix necesita barras invertidas dobles; PowerShell no.
- La ruta de salida sigue tu mapeo PSR-4.

## 3.4 Tu primer agente

Este es el primer código ejecutable del libro.

### Los tres métodos plantilla

Una clase de agente responde a tres preguntas:

- `provider()` — ¿con qué LLM hablo?
- `instructions()` — ¿quién soy y cómo me comporto?
- `tools()` — ¿qué puedo hacer realmente? *(opcional; Capítulo 5)*

Todo lo demás —el array de mensajes, el bucle, el historial, el despacho de herramientas— se hereda. La clase base es en sí misma un flujo de trabajo (Sección 2.3), y estos tres métodos son la forma de configurar los nodos que ya contiene.

### La clase

**`src/Agents/AssistantAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;

class AssistantAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(
            key: $_ENV['ANTHROPIC_KEY'],
            model: $_ENV['ANTHROPIC_MODEL'],
        );
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a technical assistant specialised in PHP development.',
                'You are talking to experienced developers. Do not explain basics unless asked.',
            ],
        );
    }
}
```

Eso es un agente completo. Cuatro líneas de configuración real.

::: {.callout .callout-warning}
[Nota sobre la firma]{.callout-title}

La clase base declara `protected function instructions(): SystemMessage|string`. Devolver un simple `string`, como hace esta clase, es un estrechamiento legítimo de ese tipo de retorno, y es lo que escribe el propio generador del framework; la Sección 3.5 muestra cuándo devolverías en su lugar un `SystemMessage`. Algunos ejemplos de la documentación declaran el método `public`. PHP también lo acepta, ya que una sobrescritura puede ampliar la visibilidad, pero mantenlo `protected` como la clase base y mantén la coherencia en todo tu proyecto. Es el punto 8 del Apéndice A.
:::

### Ejecutarlo

**`examples/01-first-agent.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? 'Explain the difference between readonly and final in PHP 8, in three lines.';

// An agent always runs on a conversation thread, and the framework never
// invents one: without setThreadId() the call below throws an AgentException.
$state = AssistantAgent::make()
    ->setThreadId('demo')
    ->chat(new UserMessage($prompt));

echo $state->getMessage()?->getContent() . PHP_EOL;
```

```bash
php examples/01-first-agent.php "How do I implement a PSR-15 middleware without a framework?"
```

### Leer la cadena, pieza a pieza

```php
AssistantAgent::make()
```

Factoría estática en la clase base. Equivale a `new AssistantAgent()`, y se lee mejor en una cadena fluida. Reenvía sus argumentos al constructor, el primero de los cuales es `workflowId:`: el mismo ID de hilo que fija la línea siguiente, para cuando ya lo conoces al construir. El Laboratorio 2 del Capítulo 4 lo pasa así.

```text
->setThreadId('demo')
```

Dice a qué conversación pertenece esta ejecución. Toda ejecución de un agente necesita un ID de hilo, y NeuronAI nunca inventa uno: quita esta línea y `chat()` lanza una `AgentException` antes de enviar ninguna petición. Una única pregunta no tiene conversación a la que volver, así que aquí sirve cualquier cadena fija; es en el Capítulo 4 donde el hilo empieza a importar.

```text
->chat(new UserMessage($prompt))
```

Ejecuta el bucle de la Sección 1.2. Aquí una sola iteración, porque no hay herramientas. `chat()` ejecuta el flujo de trabajo del agente hasta el final y devuelve su **estado** final, un `AgentState`, no el mensaje. El estado es el resultado completo de la ejecución: la respuesta del proveedor, los mensajes que produjo esta ejecución y, cuando una ejecución se pausa para esperar a un humano (Capítulo 15), el motivo de la pausa.

```php
$state->getMessage()
```

Lee del estado el último mensaje del modelo. Su tipo de retorno admite null —una ejecución que se detiene antes de que ninguna inferencia haya producido una respuesta no tiene mensaje— y por eso está ahí el `?->`. Pero un mensaje no prueba que la ejecución haya terminado: cuando una ejecución se pausa a la espera de la aprobación de una herramienta (Sección 5.10), `getMessage()` devuelve el mensaje de llamada a herramienta del modelo, no una respuesta, y es `$state->isInterrupted()` lo que distingue un caso del otro. El agente de este capítulo nunca se pausa, pero el tipo no lo sabe, y tu analizador estático tampoco.

::: {.callout .callout-warning}
[Adaptar código de ejemplo antiguo]{.callout-title}

`chat()` devuelve el `AgentState`. Los tutoriales escritos para versiones anteriores tratan su resultado como si fuera el propio mensaje, llaman a `->run()` sobre él o declaran el tipo `AgentHandler`; nada de eso funciona aquí. Es el segundo error más común al adaptar código de ejemplo antiguo, justo detrás de los namespaces.
:::

```text
->getContent()
```

Devuelve todo el contenido textual del mensaje unido en una sola cadena. La Sección 4.1 explica por qué «unido» es la palabra adecuada: un mensaje puede contener varios bloques de contenido.

### Dos cosas que van a fallar

**Undefined array key "ANTHROPIC_KEY"** — falta el archivo `.env` o no se cargó. La Sección 3.7 construye `bootstrap.php` como es debido; por ahora, confirma que el archivo existe y tiene la clave.

**Error 401 / de autenticación** — la clave es incorrecta, o tienes la facturación deshabilitada en el proveedor. Revisa la consola del proveedor antes de depurar el código.

### Puntos clave

- Tres métodos plantilla; el bucle se hereda.
- `chat()` devuelve el `AgentState` final de la ejecución; `getMessage()` devuelve el mensaje (o `null` cuando ninguna inferencia produjo uno); `getContent()` devuelve el texto.
- Toda ejecución necesita un ID de hilo —`setThreadId()`, o `workflowId:` pasado a `::make()`— y el framework nunca inventa uno. Una ejecución en pausa se detecta con `isInterrupted()`, no con un mensaje null.

## 3.5 SystemPrompt: estructurar las instrucciones

Las instrucciones que los modelos siguen de verdad tienen una estructura. NeuronAI te da una de tres partes, y vale la pena entender por qué existe antes de usarla.

### El problema del prompt como párrafo

La mayoría escribe el prompt de sistema como un bloque de prosa:

```php
protected function instructions(): string
{
    return 'You are a support assistant for an e-commerce store. Be polite and '
         . 'always answer in Italian and if you do not know something say so and '
         . 'never invent order numbers and keep answers short and use the tools '
         . 'when you need order data and format prices with the euro symbol.';
}
```

Tres problemas, en orden creciente de gravedad:

1. **Las instrucciones se pierden.** Los modelos prestan atención de forma desigual a lo largo de un bloque largo e indiferenciado; la restricción que está en el medio es la que se cae.
2. **Se pudre.** Seis meses y cuatro colaboradores después son 600 palabras con tres contradicciones que nadie encuentra.
3. **No puedes cambiar una sola cosa.** ¿Quieres otro formato de salida? Estás editando una frase encajada entre una afirmación de identidad y una regla de comportamiento.

### La estructura de NeuronAI

`SystemPrompt` recibe tres argumentos con nombre y los renderiza en un prompt estructurado:

```php
use NeuronAI\Agent\SystemPrompt;

new SystemPrompt(
    background: ['You are ...'],   // who you are, what domain, what you are not
    steps:      ['First ...'],     // the procedure to follow
    output:     ['Answer in ...'], // the contract for the response
);
```

Conviértelo a cadena con `(string)` y devuélvelo desde `instructions()`. Cada argumento se renderiza como su propia sección del prompt, con su encabezado. Hay un cuarto, opcional, `toolsUsage:`, para reglas sobre cuándo y cómo llamar a las herramientas: útil en cuanto el agente tenga herramientas que llamar (Capítulo 5).

### Un ejemplo real

```php
protected function instructions(): string
{
    return (string) new SystemPrompt(
        background: [
            'You are an AI Agent specialised in writing YouTube video summaries.',
        ],
        steps: [
            'Get the URL of a YouTube video, or ask the user to provide one.',
            'Use the tools you have available to retrieve the transcription of the video.',
            'Write the summary.',
        ],
        output: [
            'Write a summary in a paragraph without using lists. Use fluent text only.',
            'After the summary add a list of three sentences as the three most '
            . 'important takeaways from the video.',
        ],
    );
}
```

Esa es la forma de la documentación oficial, y vale la pena estudiarla porque es breve. Cada elemento del array es una instrucción. No un párrafo: una instrucción.

### Las tres secciones, y qué pertenece a cada una

**`background` — identidad y dominio.**
Quién es el agente, en qué campo opera, con quién habla y —a menudo la línea más valiosa— qué *no* es. «No eres un asesor legal y no debes interpretar cláusulas contractuales» previene toda una clase de fallos.

**`steps` — procedimiento.**
El orden de las operaciones. Aquí es donde codificas «consúltalo siempre antes de responder», que es la instrucción antialucinación más eficaz de la que dispones. Si tu agente tiene herramientas, la sección de pasos es donde le dices cuándo recurrir a ellas.

**`output` — el contrato de la respuesta.**
Idioma, formato, extensión, tono, formulaciones prohibidas. Mantén esta sección puramente sobre la forma de la respuesta. La disciplina de la separación es lo que hace mantenible el prompt: puedes cambiar tu formato de salida sin tocar la personalidad del agente ni su procedimiento.

### La comparación A/B que vale la pena hacer tú mismo

Mismo agente, misma pregunta, dos prompts.

**Versión A:**

```php
return 'You are a helpful PHP assistant.';
```

**Versión B:**

```php
return (string) new SystemPrompt(
    background: [
        'You are a technical assistant specialised in PHP development.',
        'You are talking to experienced developers.',
    ],
    steps: [
        'Identify the real problem behind the question, not only the stated one.',
        'If the question is ambiguous, ask the single most useful clarifying question.',
    ],
    output: [
        'Answer in English.',
        'Use fenced code blocks with the language declared.',
        'No preambles such as "Certainly!" or "Great question".',
        'Maximum 200 words unless code requires more.',
    ],
);
```

Pregunta a ambas: *«¿Cómo gestiono las subidas de archivos?»*

La versión A devuelve 600 palabras que empiezan por «¡Gran pregunta!». La versión B pregunta qué framework, o responde de forma escueta en PHP puro. La diferencia es inmediata y cala más hondo que cualquier explicación: **el prompt de sistema es la especificación, no el saludo.**

### Orientación práctica

- Una instrucción por elemento del array. Si un elemento contiene una «y», plantéate dividirlo.
- Prefiere instrucciones en positivo. «Responde en español» gana a «no respondas en italiano».
- Las negaciones que importan vale la pena conservarlas, pero enuncia el límite, no una lista de palabras prohibidas.
- Versiona el prompt en Git y trata los cambios de prompt como cambios de código, con revisión. Dada la Sección 1.5, un prompt reformulado es un cambio de comportamiento que no puedes someter a pruebas de regresión convencionales.

### Las cadenas bastan, hasta que quieres caché

Devuelva lo que devuelva `instructions()`, el agente lo guarda como un `SystemMessage`: un mensaje cuyos bloques de contenido son el prompt de sistema. Una cadena se convierte en un bloque. Es todo lo que necesitan los agentes de este libro, y por eso devuelven cadenas. Cuando quieras recuperar las instrucciones efectivas —en una prueba, o para registrar qué versión del prompt se ejecutó—, `$agent->getInstructions()` devuelve ese `SystemMessage`, y `->getContent()` sobre él renderiza el texto. (Los tutoriales escritos para versiones anteriores llaman a `resolveInstructions()` para esto; el método no existe en la v4.)

Devuelve tú mismo un `SystemMessage` cuando quieras más de un bloque, y el motivo habitual es la caché de prompts. Un prompt largo y estable se reenvía en cada turno y en cada iteración de herramientas; los proveedores que admiten caché (Anthropic y la API Responses de OpenAI, entre los proveedores de NeuronAI) facturan un prefijo en caché a una fracción del precio normal de entrada. Marca como cacheado el bloque estable y deja la parte volátil en un bloque propio:

```php
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Chat\Messages\ContentBlocks\SystemContent;
use NeuronAI\Chat\Messages\SystemMessage;

protected function instructions(): SystemMessage
{
    return new SystemMessage([
        (new SystemContent((string) new SystemPrompt(
            background: ['You are a technical assistant specialised in PHP development.'],
        )))->cache(),
        new SystemContent('Today is ' . date('Y-m-d')),
    ]);
}
```

Los proveedores sin caché envían los bloques como texto normal, así que el código sigue siendo portable. La aritmética de la Sección 1.4 dice cuándo compensa: cuanto más largo sea el prompt estático y más llamadas haya por conversación, mayor será el ahorro. Por debajo del tamaño mínimo que un proveedor admite en caché —de unos cientos a unos miles de tokens, según el modelo— el marcador se ignora en silencio, así que el prompt de dos líneas de arriba no guarda nada en caché: el patrón compensa en prompts que se miden en páginas.

### Puntos clave

- Tres secciones: `background` (identidad), `steps` (procedimiento), `output` (contrato).
- Una instrucción por elemento del array.
- «Consúltalo antes de responder» pertenece a `steps` y es tu mejor herramienta antialucinación.
- `instructions()` puede devolver una cadena o un `SystemMessage`; usa lo segundo para dividir el prompt en bloques y poner en caché el estable.
- Los cambios de prompt son cambios de código; revísalos.

## 3.6 Cambiar de proveedor: la interfaz da sus frutos

Esto es lo más persuasivo de la Parte II: un agente, cinco motores, ningún cambio de código.

### La versión ingenua

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(key: '...', model: '...');
}
```

Funciona, pero ahora cada clase de agente conoce el nombre de un proveedor. Con diez agentes, cambiar de proveedor es una modificación en diez archivos más una revisión de código.

### La factoría

**`src/ProviderFactory.php`**

```php
<?php

declare(strict_types=1);

namespace App;

use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\Providers\Gemini\Gemini;
use NeuronAI\Providers\Mistral\Mistral;
use NeuronAI\Providers\Ollama\Ollama;
use NeuronAI\Providers\OpenAI\OpenAI;
use Uri\Rfc3986\Uri;

final class ProviderFactory
{
    public static function make(?string $driver = null): AIProviderInterface
    {
        $driver ??= env('NEURON_PROVIDER', 'ollama');

        return match ($driver) {
            'anthropic' => new Anthropic(
                key: self::require('ANTHROPIC_KEY'),
                model: env('ANTHROPIC_MODEL', 'claude-sonnet-4-5'),
            ),
            'openai' => new OpenAI(
                key: self::require('OPENAI_KEY'),
                model: env('OPENAI_MODEL', 'gpt-4.1-mini'),
            ),
            'gemini' => new Gemini(
                key: self::require('GEMINI_KEY'),
                model: env('GEMINI_MODEL', 'gemini-2.0-flash'),
            ),
            'mistral' => new Mistral(
                key: self::require('MISTRAL_KEY'),
                model: env('MISTRAL_MODEL', 'mistral-large-latest'),
            ),
            'ollama' => new Ollama(
                url: self::ollamaUrl(),
                model: env('OLLAMA_MODEL', 'qwen2.5:7b'),
                // Ollama truncates a prompt to num_ctx instead of rejecting it,
                // and its default is small: ask for the window Section 4.4 budgets.
                parameters: ['options' => ['num_ctx' => 32_768]],
            ),
            default => throw new \InvalidArgumentException("Unknown provider: {$driver}"),
        };
    }

    private static function require(string $key): string
    {
        return env($key) ?? throw new \RuntimeException("Missing environment variable: {$key}");
    }

    private static function ollamaUrl(): string
    {
        $raw = env('OLLAMA_URL', 'http://localhost:11434/api');
        $url = Uri::parse($raw);

        if ($url?->getHost() === null) {
            throw new \InvalidArgumentException("OLLAMA_URL [{$raw}] is not an absolute URL.");
        }

        return $url->toString();
    }
}
```

`ollamaUrl()` usa la extensión URI integrada de PHP 8.5: `Uri\Rfc3986\Uri::parse()` analiza el valor según las reglas de la RFC 3986 y devuelve `null` cuando no puede, así que un `OLLAMA_URL` mal escrito falla aquí, con su nombre en el mensaje, en lugar de aflorar más tarde como un error opaco de cURL.

El argumento `parameters:` de la rama de Ollama es la forma en que cualquier proveedor recibe las opciones de petición que la factoría no modela. Aquí fija `num_ctx`, el tamaño de contexto de Ollama. Si no lo tocas, Ollama no rechaza un prompt demasiado largo: lo trunca, en silencio, a un valor por defecto mucho menor que el que el modelo puede manejar. La Sección 4.4 vuelve sobre ese número.

::: {.callout .callout-warning}
[Verifica el import de Mistral]{.callout-title}

Una página de la documentación oficial muestra `use NeuronAI\Providers\Gemini\Mistral;`, que es un artefacto de copiar y pegar. El namespace correcto sigue el patrón de los demás. Revisa tu directorio `vendor/`: este es exactamente el tipo de detalle con el que chocarás y del que te culparás a ti mismo.
:::

### Usarla

```php
protected function provider(): AIProviderInterface
{
    return ProviderFactory::make();
}
```

Ahora todos los agentes del proyecto dicen lo mismo: «dame el proveedor configurado». Los nombres de proveedor aparecen exactamente en un archivo.

### El experimento

```bash
NEURON_PROVIDER=ollama    php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=anthropic php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=openai    php examples/01-first-agent.php "What is a generator in PHP?"
NEURON_PROVIDER=gemini    php examples/01-first-agent.php "What is a generator in PHP?"
```

El mismo código. Cuatro de los cinco motores. Cronometra cada uno: la diferencia de latencia entre lo local y la nube es el detalle que dará forma a tus decisiones de diseño más adelante.

### Por qué esto merece una sección propia

Tres argumentos, en orden creciente de peso empresarial:

**Desarrollo gratuito.** Ollama en un portátil no cuesta nada. Puedes completar todos los laboratorios de las Partes II, III y IV sin tarjeta de crédito, que es la diferencia entre terminar un libro como este y abandonarlo en el Capítulo 6.

**Escalonado de costes.** La Sección 1.4 te dio tres palancas, y la tercera era «modelo más barato por paso». Un modelo local pequeño para clasificar y enrutar; un modelo de frontera solo para la síntesis final. Aquí eso es un argumento por llamada, no un cambio de arquitectura.

**Riesgo de proveedor y de jurisdicción.** Los precios cambian, las condiciones cambian, los proveedores tienen caídas y algunos clientes no pueden enviar datos fuera de una jurisdicción concreta, o fuera de su propio edificio. Con una dependencia rígida de un SDK, cada una de esas cosas es un proyecto. Aquí cada una es un valor de configuración.

### Puntos clave

- Una factoría; los nombres de proveedor viven exactamente en un archivo.
- Ollama hace que todo lo de este libro se pueda seguir gratis.
- La elección de proveedor se convierte en estrategia de costes, gestión de riesgos y cumplimiento de residencia de datos.

## 3.7 Secretos y entorno

Cargar la configuración de forma segura y evitar el incidente de la clave filtrada que pilla a una cantidad genuinamente grande de desarrolladores en su primer proyecto de IA.

### bootstrap.php

**`bootstrap.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->safeLoad();

function env(string $key, ?string $default = null): ?string
{
    $value = $_ENV[$key] ?? $_SERVER[$key] ?? getenv($key);

    return ($value === false || $value === '') ? $default : (string) $value;
}
```

`safeLoad()` en lugar de `load()`: no lanza excepción cuando falta el archivo, que es lo que quieres en un servidor donde las variables vienen del propio entorno y no de un archivo.

El ayudante `env()` mira `$_ENV`, luego `$_SERVER`, luego `getenv()`, y trata la cadena vacía como ausencia, de modo que una variable presente pero en blanco cae al valor por defecto en lugar de producir un fallo confuso tres capas más abajo.

### .env.example — versionado

```dotenv
# anthropic | openai | gemini | mistral | ollama
NEURON_PROVIDER=ollama

ANTHROPIC_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-5

OPENAI_KEY=
OPENAI_MODEL=gpt-4.1-mini

GEMINI_KEY=
GEMINI_MODEL=gemini-2.0-flash

MISTRAL_KEY=
MISTRAL_MODEL=mistral-large-latest

# Local models: no cost, ideal for the labs
OLLAMA_URL=http://localhost:11434/api
OLLAMA_MODEL=qwen2.5:7b

# Optional: tracing via inspector.dev (wired up in Chapter 10)
INSPECTOR_INGESTION_KEY=
```

```bash
cp .env.example .env
```

`.env.example` documenta la estructura y se versiona. `.env` contiene los valores y no se versiona nunca.

### El problema de la clave filtrada, dicho sin rodeos

Las claves de los proveedores de IA son más peligrosas que la mayoría de las credenciales porque son directamente monetizables. Hay rastreadores automatizados vigilando los commits públicos, y una clave subida a un repositorio público se explota típicamente en cuestión de minutos u horas, facturándotela a tarifas de modelo de frontera hasta que te des cuenta.

Cuatro defensas, todas baratas:

1. **`.env` en `.gitignore` antes de que el archivo exista.** No después.
2. **Un escáner de secretos en CI.** `gitleaks` o `trufflehog`, unas pocas líneas de configuración del flujo.
3. **Límites de gasto en el proveedor.** Todo proveedor importante ofrece un tope mensual rígido. Ponlo. Convierte una catástrofe en una molestia.
4. **Claves separadas por entorno.** Desarrollo, staging, producción, para que revocar una no tumbe las otras.

Si filtras una clave: revócala primero en el proveedor y luego limpia el historial. En ese orden. Reescribir el historial de Git con una clave que sigue activa no logra nada.

### Nunca registres el prompt a ciegas

Un detalle específico de las aplicaciones de IA. Tus prompts contendrán lo que sea que haya escrito el usuario, lo que en una aplicación de soporte significa nombres, direcciones, números de pedido y, en ocasiones, datos de pago. Registrar los prompts completos para depurar es enormemente tentador y crea un problema de cumplimiento en el momento en que lo haces a escala.

Registra recuentos de tokens, el modelo, la latencia, los nombres de las herramientas y un identificador de petición. Registra el *contenido* del prompt solo detrás de una bandera explícita, con retención, y nunca activo por defecto en producción. Volvemos a esto en el Capítulo 23.

### Los nombres de los modelos caducan

Todas las cadenas de modelo de este capítulo acabarán siendo incorrectas. Consulta la lista de modelos actual del proveedor en vez de fiarte de un libro escrito meses antes de que lo leas, incluido este.

### Puntos clave

- `safeLoad()` más un ayudante `env()` defensivo.
- `.env.example` versionado, `.env` nunca.
- Pon hoy mismo un límite de gasto rígido en el proveedor.
- Revoca antes de reescribir el historial.
- No registres prompts completos por defecto.

## Laboratorio 1 — Los cimientos en PHP puro

Todo lo de las Partes II a IV se ejecuta sobre el proyecto que construyes aquí. No te lo saltes; los laboratorios posteriores dan por hecha exactamente esta estructura.

### Qué vas a construir

Un proyecto de Composer con una factoría de proveedores, un agente funcionando y un script de benchmark que ejecuta el mismo prompt en todos los proveedores que tengas configurados.

### Pasos

1. **Monta** la estructura de directorios y el `composer.json` de la Sección 3.1. Ejecuta `composer dump-autoload` y confirma que no reporta errores.
2. **Instala** los dos paquetes de la Sección 3.2, después de comprobar que `ext-curl` está cargada. Verifica con la línea de comprobación de esa sección; si imprime `FAIL`, para y arregla la versión antes de continuar.
3. **Escribe `bootstrap.php`** y el ayudante `env()` de la Sección 3.7. Copia `.env.example` a `.env`.
4. **Escribe `src/ProviderFactory.php`** de la Sección 3.6.
5. **Escribe el agente.** Usa el `SystemPrompt` completo de tres secciones en lugar del mínimo de la Sección 3.4: esta es la versión sobre la que construyen los capítulos posteriores:

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;

class AssistantAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a technical assistant specialised in PHP development.',
                'You are talking to experienced developers: no unrequested basics.',
            ],
            steps: [
                'Analyse the question and identify the real problem, not only the stated one.',
                'If the question is ambiguous, ask the single most useful clarifying question.',
            ],
            output: [
                'Answer in English.',
                'Use fenced code blocks with the language declared.',
                'No preambles such as "Certainly!" or "Great question".',
                'Maximum 200 words unless the code requires more.',
            ],
        );
    }

    protected function contextWindow(): int
    {
        // No store is declared, so the agent keeps the conversation in an
        // InMemoryMessageStore of its own: it lasts as long as this instance.
        // Roughly 90 % of a 32K local model's window: the trimmer needs headroom.
        return 29_000;
    }
}
```

6. **Ejecútalo** con `examples/01-first-agent.php` de la Sección 3.4.
7. **Cambia de proveedor** usando la variable de entorno, como mínimo entre Ollama y un proveedor en la nube.

### El benchmark

Amplía `01-first-agent.php` para que recorra todos los proveedores con credenciales configuradas, ejecute el mismo prompt contra cada uno e imprima una tabla con proveedor, tiempo transcurrido y longitud de la respuesta. Guarda este script: en el Capítulo 10 le añadirás los recuentos de tokens de `$state->getMessage()?->getUsage()` y se convertirá en una herramienta genuinamente útil para elegir modelo.

### Criterios de aceptación

- `composer dump-autoload` no produce avisos, y `App\Agents\AssistantAgent` se resuelve.
- El mismo prompt devuelve una respuesta sensata con al menos dos valores distintos de `NEURON_PROVIDER`, sin cambiar ningún archivo PHP.
- `.env` no está versionado. Verifícalo con `git status --ignored` en lugar de suponerlo.
- Una clave de API ausente produce tu `RuntimeException` con un mensaje útil, no un fallo por puntero nulo en las profundidades del proveedor.

### Si no funciona

Los cuatro fallos que explican casi todos los problemas de la primera ejecución: un mapeo PSR-4 incorrecto (clase no encontrada), un namespace de una versión antigua en una instrucción `use` (clase no encontrada, pero una clase *del framework*), una compilación de PHP sin `ext-curl` (la primera llamada a un proveedor falla) y un `.env` que nunca se copió desde `.env.example` (falta la clave). Compruébalos en ese orden.
