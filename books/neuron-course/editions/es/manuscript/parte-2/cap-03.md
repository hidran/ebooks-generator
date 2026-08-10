# Capítulo 3 — Configuración y tu primer agente

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch03`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch03), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 3.1 El esqueleto del proyecto

Vamos a construir un proyecto limpio en PHP puro que soportará todos los ejemplos de las Partes II, III y IV. Sin framework, sin magia.

### Por qué PHP puro primero

Vas a pasar la Parte V dentro de Laravel, donde una facade te entrega un agente configurado y un comando de artisan genera tus clases. Esa comodidad vale la pena, pero solo después de haber visto qué está ocultando. Todo lo que hace el SDK de Laravel ya lo habrás hecho a mano.

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
        "php": "^8.1"
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
composer require neuron-core/neuron-ai vlucas/phpdotenv guzzlehttp/guzzle
```

**`neuron-core/neuron-ai`** — el framework. Requiere PHP 8.1 o posterior.

**`vlucas/phpdotenv`** — lee un archivo `.env` y lo carga en el entorno. Laravel lo incluye; PHP puro no. Sin él tendrías que escribir las claves de API a fuego, cosa que no vamos a hacer.

**`guzzlehttp/guzzle`** — un cliente HTTP. NeuronAI incorpora internamente lo que necesita; lo requerimos explícitamente porque nuestras propias herramientas llamarán a APIs externas en el Capítulo 5, y una dependencia explícita es una dependencia honesta.

### Fija la versión

```json
"require": {
    "php": "^8.1",
    "neuron-core/neuron-ai": "^3.0",
    "vlucas/phpdotenv": "^5.6",
    "guzzlehttp/guzzle": "^7.9"
}
```

**Versiona `composer.lock` en un repositorio didáctico.** No es el consejo habitual para bibliotecas: es deliberado. Quien siga este libro dentro de un año debe obtener la misma API contra la que se escribió. Sin el archivo de bloqueo obtendrá lo que `^3.0` resuelva ese día y, si una publicación menor cambió una firma, obtendrá un error con el que nadie podrá ayudarle.

### Verifica

```bash
php -r "require 'vendor/autoload.php'; echo class_exists(NeuronAI\Agent\Agent::class) ? 'OK' : 'FAIL';"
```

Si eso imprime `FAIL`, casi con seguridad estás en una versión mayor antigua donde la clase era `NeuronAI\Agent`. Compruébalo con:

```bash
composer show neuron-core/neuron-ai | head -5
```

### Unas palabras sobre los namespaces y la documentación

Entre la v2 y la v3 los namespaces se movieron:

| v1 / v2 | v3 |
|---|---|
| `NeuronAI\Agent` | `NeuronAI\Agent\Agent` |
| `NeuronAI\SystemPrompt` | `NeuronAI\Agent\SystemPrompt` |

Partes de la documentación oficial, varias entradas de blog y la mayoría de los artículos de terceros siguen mostrando los imports de la v2. Cuando encuentres código de ejemplo cuyas instrucciones `use` no coincidan con este libro, comprueba a qué versión apunta antes de dar por hecho que algo está roto. Es la fuente de confusión más común para quien llega desde tutoriales.

### Puntos clave

- `composer require neuron-core/neuron-ai`, PHP 8.1+.
- Fija la versión y versiona `composer.lock` en los repositorios didácticos.
- La v2 → v3 movió los namespaces; los tutoriales antiguos no compilan contra la v3.

## 3.3 La CLI del framework

Los generadores crean componentes del framework con la estructura correcta. Conviene saber qué producen, porque también querrás escribir estas clases a mano.

### El binario

Instalar el paquete te da un ejecutable en `vendor/bin/neuron`.

```bash
./vendor/bin/neuron
```

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
| `make:agent` | Clase que extiende `Agent` con los esbozos de `provider()` e `instructions()` | Capítulo 3 |
| `make:tool` | Clase que extiende `Tool` con los esbozos de `properties()` e `__invoke()` | Capítulo 5 |
| `make:node` | Nodo de flujo de trabajo con un esbozo de `__invoke(Event, WorkflowState)` | Capítulo 13 |
| `make:event` | Clase de evento que implementa `Event` | Capítulo 13 |

Los generadores escriben el archivo en la ruta implicada por tu mapeo PSR-4. `App\Agents\AssistantAgent` aterriza en `src/Agents/AssistantAgent.php` gracias al mapeo que fijamos en la Sección 3.1. Si aterriza en un sitio inesperado, tu bloque de autoload está mal.

### La postura honesta sobre los generadores

Ahorran teclear e imponen una convención de nombres. Ese es todo el beneficio. Cada clase que producen es PHP corriente que podrías teclear tú en noventa segundos, y en este libro las escribimos a mano con frecuencia, porque quien solo ha generado un agente no sabe realmente qué es un agente.

Úsalos cuando te hagan productivo. No los uses como sustituto de entender la forma de la clase.

### Puntos clave

- Cuatro generadores: `make:agent`, `make:tool`, `make:node`, `make:event`.
- Unix necesita barras invertidas dobles; PowerShell no.
- La ruta de salida sigue tu mapeo PSR-4.

## 3.4 Tu primer agente

Este es el primer código ejecutable del libro.

### Los tres métodos plantilla

Una clase de agente responde a tres preguntas:

- `provider()` — ¿con qué LLM hablo?
- `instructions()` — ¿quién soy y cómo me comporto?
- `tools()` — ¿qué puedo hacer realmente? *(opcional; Capítulo 5)*

Todo lo demás —el array de mensajes, el bucle, el historial, el despacho de herramientas— se hereda.

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

    public function instructions(): string
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
[Nota sobre la visibilidad]{.callout-title}

La documentación oficial muestra `instructions()` como `public` en algunos ejemplos y como `protected` en otros. Ambas aparecen en los documentos actuales. Usa la que coincida con la clase base de la versión que instales —compruébalo con tu IDE o con `composer show`— y mantén la coherencia en todo tu proyecto. Es el punto 8 del Apéndice A.
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

$response = AssistantAgent::make()
    ->chat(new UserMessage($prompt))
    ->getMessage();

echo $response->getContent() . PHP_EOL;
```

```bash
php examples/01-first-agent.php "How do I implement a PSR-15 middleware without a framework?"
```

### Leer la cadena, pieza a pieza

```php
AssistantAgent::make()
```

Factoría estática en la clase base. Equivale a `new AssistantAgent()` para un constructor sin argumentos, y se lee mejor en una cadena fluida. Cuando tu agente reciba argumentos de constructor —como hará `PersistentAgent` en la Sección 4.3— usa `new` en su lugar.

```php
->chat(new UserMessage($prompt))
```

Ejecuta el bucle de la Sección 1.2. Aquí una sola iteración, porque no hay herramientas. Fíjate en que `chat()` devuelve un **objeto respuesta**, no el mensaje.

```php
->getMessage()
```

Extrae el mensaje del asistente de la respuesta.

::: {.callout .callout-warning}
[Cambio v2 → v3]{.callout-title}

En versiones anteriores `chat()` devolvía el mensaje directamente. En la v3 debes llamar a `getMessage()`. Es el segundo error más común al adaptar código de ejemplo antiguo, justo detrás de los namespaces.
:::

```php
$response->getContent()
```

Devuelve todo el contenido textual del mensaje concatenado en una sola cadena. La Sección 4.1 explica por qué «concatenado» es la palabra adecuada: un mensaje puede contener varios bloques de contenido.

### Dos cosas que van a fallar

**Undefined array key "ANTHROPIC_KEY"** — falta el archivo `.env` o no se cargó. La Sección 3.7 construye `bootstrap.php` como es debido; por ahora, confirma que el archivo existe y tiene la clave.

**Error 401 / de autenticación** — la clave es incorrecta, o tienes la facturación deshabilitada en el proveedor. Revisa la consola del proveedor antes de depurar el código.

### Puntos clave

- Tres métodos plantilla; el bucle se hereda.
- `chat()` devuelve una respuesta; `getMessage()` devuelve el mensaje; `getContent()` devuelve el texto.
- `::make()` para agentes sencillos, `new` cuando el constructor recibe argumentos.

## 3.5 SystemPrompt: estructurar las instrucciones

Las instrucciones que los modelos siguen de verdad tienen una estructura. NeuronAI te da una de tres partes, y vale la pena entender por qué existe antes de usarla.

### El problema del prompt como párrafo

La mayoría escribe el prompt de sistema como un bloque de prosa:

```php
public function instructions(): string
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
    background: [...],  // who you are, what domain, what you are not
    steps:      [...],  // the procedure to follow
    output:     [...],  // the contract for the response
);
```

Conviértelo a cadena con `(string)` y devuélvelo desde `instructions()`.

### Un ejemplo real

```php
public function instructions(): string
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

### Puntos clave

- Tres secciones: `background` (identidad), `steps` (procedimiento), `output` (contrato).
- Una instrucción por elemento del array.
- «Consúltalo antes de responder» pertenece a `steps` y es tu mejor herramienta antialucinación.
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
                url: env('OLLAMA_URL', 'http://localhost:11434/api'),
                model: env('OLLAMA_MODEL', 'qwen2.5:7b'),
            ),
            default => throw new \InvalidArgumentException("Unknown provider: {$driver}"),
        };
    }

    private static function require(string $key): string
    {
        return env($key) ?? throw new \RuntimeException("Missing environment variable: {$key}");
    }
}
```

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

El mismo código. Cuatro motores. Cronometra cada uno: la diferencia de latencia entre lo local y la nube es el detalle que dará forma a tus decisiones de diseño más adelante.

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

# Optional: tracing via inspector.dev
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
2. **Instala** los tres paquetes de la Sección 3.2. Verifica con la línea de `class_exists`; si imprime `FAIL`, para y arregla la versión antes de continuar.
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
use NeuronAI\Chat\History\ChatHistoryInterface;
use NeuronAI\Chat\History\InMemoryChatHistory;
use NeuronAI\Providers\AIProviderInterface;

class AssistantAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    public function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a technical assistant specialised in PHP development.',
                'You are talking to experienced developers: no unrequested basics.',
            ],
            steps: [
                'Analyse the question and identify the real problem, not only the stated one.',
                'If the question is ambiguous, ask the single most useful clarifying question.',
                'Answer with code when code is the answer.',
            ],
            output: [
                'Answer in English.',
                'Use fenced code blocks with the language declared.',
                'No preambles such as "Certainly!" or "Great question".',
            ],
        );
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        // Roughly 90 % of the model's context window: the trimmer needs headroom.
        return new InMemoryChatHistory(contextWindow: 120_000);
    }
}
```

6. **Ejecútalo** con `examples/01-first-agent.php` de la Sección 3.4.
7. **Cambia de proveedor** usando la variable de entorno, como mínimo entre Ollama y un proveedor en la nube.

### El benchmark

Amplía `01-first-agent.php` para que recorra todos los proveedores con credenciales configuradas, ejecute el mismo prompt contra cada uno e imprima una tabla con proveedor, tiempo transcurrido y longitud de la respuesta. Guarda este script: en el Capítulo 10 le añadirás los recuentos de tokens de `$response->getUsage()` y se convertirá en una herramienta genuinamente útil para elegir modelo.

### Criterios de aceptación

- `composer dump-autoload` no produce avisos, y `App\Agents\AssistantAgent` se resuelve.
- El mismo prompt devuelve una respuesta sensata con al menos dos valores distintos de `NEURON_PROVIDER`, sin cambiar ningún archivo PHP.
- `.env` no está versionado. Verifícalo con `git status --ignored` en lugar de suponerlo.
- Una clave de API ausente produce tu `RuntimeException` con un mensaje útil, no un fallo por puntero nulo en las profundidades del proveedor.

### Si no funciona

Los tres fallos que explican casi todos los problemas de la primera ejecución: un mapeo PSR-4 incorrecto (clase no encontrada), un namespace de la v2 en una instrucción `use` (clase no encontrada, pero una clase *del framework*) y un `.env` que nunca se copió desde `.env.example` (falta la clave). Compruébalos en ese orden.
