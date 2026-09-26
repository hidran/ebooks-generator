# Capítulo 5 — Herramientas: darle manos al agente

Este es el capítulo más largo del libro, y el más importante. Las herramientas son la única funcionalidad que separa a un agente de un chatbot, y el diseño de herramientas es donde los agentes fallan de verdad.

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch05`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch05), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 5.1 Qué es realmente una herramienta

### La definición en una frase

Una herramienta es una función de tu código base que el modelo puede pedirte que ejecutes.

Léelo otra vez, porque cada palabra es estructural. Es **tu** función. En **tu** código base. El modelo **pide**. Tú la **ejecutas**.

### El mecanismo, reformulado

La Sección 1.2 presentó el bucle. Esto es lo que una herramienta aporta a él.

Describes tus funciones al modelo como metadatos estructurados: un nombre, una descripción y un esquema de parámetros. El modelo recibe eso junto con la conversación. Cuando decide que una función ayudaría, no produce prosa: produce una petición estructurada.

```
I would like to call get_transcription with {"video_url": "https://..."}
```

NeuronAI intercepta esa petición, encuentra el objeto herramienta correspondiente, lo invoca con esos argumentos, toma el valor devuelto, lo añade a la conversación como mensaje de resultado de herramienta y vuelve a llamar al modelo. El modelo ya tiene la transcripción en el contexto y puede escribir el resumen.

Fíjate en que intervienen dos cosas distintas, y NeuronAI las mantiene separadas. La **herramienta** es capacidad: un objeto PHP con un esquema, un método `__invoke()` y las dependencias que necesite —una conexión PDO, un cliente HTTP—. Vive en el agente y nunca sale de tu proceso. La **llamada a herramienta** es un dato: un objeto de valor `ToolCall` que registra una invocación —el nombre de la herramienta, el ID de llamada que asignó el modelo, los argumentos y, más tarde, el resultado—. Los mensajes, el historial de conversación, los fragmentos de transmisión y el estado persistido transportan objetos `ToolCall`, nunca herramientas. En tiempo de ejecución, el framework resuelve cada llamada por nombre contra la lista de herramientas activas del agente; una llamada que nombra una herramienta que el agente no ofrece falla de forma ruidosa en lugar de ejecutar nada.

El framework automatiza todas las partes de eso salvo el cuerpo de la función. Esa es genuinamente toda la abstracción, y la documentación de NeuronAI lo describe exactamente así: el bucle central consiste en llamar a un modelo, dejar que elija herramientas que ejecutar y terminar cuando no hacen falta más herramientas.

### Por qué esto es el modelo de seguridad, no solo el de ejecución

El modelo no tiene capacidades propias. No puede abrir un socket, leer un archivo ni lanzar una consulta. Todo su poder es el conjunto de herramientas que registraste.

Esto tiene una consecuencia liberadora y una obligación.

**La consecuencia liberadora:** no te pueden explotar hacia una acción que nunca implementaste. No hay una herramienta para `DELETE FROM users`, así que ningún prompt —por astuto que sea— produce una.

**La obligación:** todo lo que *sí* registres es alcanzable por cualquiera que pueda hablar con el agente. Si registras una herramienta que ejecuta SQL arbitrario, un usuario que convenza al modelo de ejecutar SQL destructivo lo habrá conseguido, y ninguna cantidad de texto instructivo en tu prompt de sistema lo previene de forma fiable.

El límite de seguridad es la lista de herramientas, y es el único límite en el que puedes confiar. La Sección 5.10 y el Capítulo 19 construyen sobre esto.

### Qué hace buena a una herramienta

**Estrecha.** `get_order_status(order_id)` gana a `manage_order(action, params)`. Una herramienta estrecha es más fácil de elegir correctamente para el modelo y más fácil de autorizar para ti.

**Determinista.** Mismos argumentos, mismo resultado. El modelo ya es no determinista; no lo agraves.

**Compacta en su valor de retorno.** Lo que devuelvas se convierte en cadena dentro de la conversación y se reenvía en cada iteración posterior. Devuelve los tres campos que el modelo necesita, no el objeto de modelo entero con cincuenta columnas. Esta es la aritmética de la Sección 1.4 reapareciendo en el código.

**Honesta al fallar.** Devolver «Order not found» le es útil al modelo. Devolver una cadena vacía lo deja adivinando, y un modelo que adivina alucina. NeuronAI te da una forma específica para esto —`ToolOutput::error()`—, que trata la Sección 5.11.

### El cambio mental

Deja de pensar en las herramientas como una funcionalidad de integración. Son la **superficie de capacidades de tu agente**: un problema de diseño de API, donde el consumidor es un modelo de lenguaje y no otro desarrollador.

Ese encuadre explica por qué el resto de este capítulo dedica tanto tiempo a los nombres, las descripciones y los esquemas. Estás escribiendo documentación para un consumidor que solo lee la documentación.

### Puntos clave

- Una herramienta es tu función; el modelo pide, tu código ejecuta.
- La herramienta es capacidad y se queda en el agente; la `ToolCall` es un dato y viaja en la conversación.
- La lista de herramientas registradas es el límite de seguridad: el único en el que puedes confiar.
- Las buenas herramientas son estrechas, deterministas, compactas en su salida y explícitas al fallar.
- Diseñar herramientas es diseñar una API para un lector que solo tiene los documentos.

## 5.2 Herramientas en línea

### La forma

`Tool` es abstracta: toda herramienta es una clase que la extiende. Cuando una herramienta es pequeña y se usa en un solo sitio, esa clase no necesita un archivo, ni siquiera un nombre: declárala como clase anónima, directamente dentro de `tools()`:

```php
new class extends Tool {
    protected string $name = 'name';
    protected ?string $description = 'description';
    protected function properties(): array { return [new ToolProperty(/* ... */)]; }
    public function __invoke(string $input): string { /* ... */ }
};
```

Tres piezas: identidad, esquema, implementación. La identidad son dos propiedades de la clase, `$name` y `$description`. El esquema es lo que devuelve `properties()`. La implementación es `__invoke()`.

### El ejemplo canónico

Este es el agente de resúmenes de YouTube de la documentación oficial, con su herramienta declarada en el sitio. Vale la pena conocerlo porque te encontrarás este agente por todas partes:

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class YouTubeAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(
            key: 'ANTHROPIC_API_KEY',
            model: 'ANTHROPIC_MODEL',
        );
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are an AI Agent specialized in writing YouTube video summaries.'],
            steps: [
                'Get the url of a YouTube video, or ask the user to provide one.',
                'Use the tools you have available to retrieve the transcription of the video.',
                'Write the summary.',
            ],
            output: [
                'Write a summary in a paragraph without using lists. Use just fluent text.',
                'After the summary add a list of three sentences as the three most important take away from the video.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            new class extends Tool {
                protected string $name = 'get_transcription';

                protected ?string $description = 'Retrieve the transcription of a youtube video.';

                protected function properties(): array
                {
                    return [
                        new ToolProperty(
                            name: 'video_url',
                            type: PropertyType::STRING,
                            description: 'The URL of the YouTube video.',
                            required: true,
                        ),
                    ];
                }

                public function __invoke(string $video_url): string
                {
                    return 'Video transcription...';
                }
            },
        ];
    }
}
```

### La regla con la que tropieza todo el mundo

**El nombre de la property debe coincidir con el nombre del parámetro de `__invoke()`.**

La property se llama `video_url`. La firma del método es `__invoke(string $video_url)`. Ni `$url`, ni `$videoUrl`. Exactamente `$video_url`.

NeuronAI pasa los argumentos del modelo a `__invoke()` como **argumentos con nombre**, indexados por el nombre de la property. Renombra un lado y PHP lanza `Error: Unknown named parameter $video_url` la primera vez que el modelo llama a la herramienta: una excepción que aborta la ejecución y que, a primera vista, parece un error del modelo, cuando en realidad se equivocó tu cableado. Es el error de herramientas más común de todos.

### Una versión ejecutable

Algo que puedas ejecutar de verdad, sin ninguna clave de API externa:

**`examples/02-inline-tool.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\ToolDemoAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'Is the server under stress right now?';

echo ToolDemoAgent::make()
    ->chat(new UserMessage($question))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

`chat()` devuelve el estado final del agente, y `getMessage()` lee de él la respuesta del asistente. Su tipo de retorno admite null —una ejecución que se pausa antes de que el modelo haya producido una respuesta no tiene mensaje que leer—, de ahí el `?->`.

**`src/Agents/ToolDemoAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolOutput;
use NeuronAI\Tools\ToolProperty;

class ToolDemoAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a system monitoring assistant.'],
            steps: ['Always read the real load values with your tools before answering.'],
            output: ['Answer in two sentences. Give the numbers you measured.'],
        );
    }

    protected function tools(): array
    {
        return [
            new class extends Tool {
                protected string $name = 'get_server_load';

                protected ?string $description = 'Returns the average CPU load of this server over a given time window. '
                    . 'Use this whenever asked about current server load, stress, or performance.';

                protected function properties(): array
                {
                    return [
                        new ToolProperty(
                            name: 'window',
                            type: PropertyType::STRING,
                            description: 'The time window. Allowed values: "1m", "5m", "15m".',
                            required: true,
                        ),
                    ];
                }

                public function __invoke(string $window): string|ToolOutput
                {
                    $load = \sys_getloadavg();

                    if ($load === false) {
                        return ToolOutput::error('Load average is not available on this platform.');
                    }

                    $value = match ($window) {
                        '1m'  => $load[0],
                        '5m'  => $load[1],
                        '15m' => $load[2],
                        default => null,
                    };

                    if ($value === null) {
                        return ToolOutput::error("Invalid window \"{$window}\". Use \"1m\", \"5m\" or \"15m\".");
                    }

                    return \sprintf('Load average over %s: %.2f', $window, $value);
                }
            },
        ];
    }
}
```

```bash
php examples/02-inline-tool.php "How stressed is the server compared to fifteen minutes ago?"
```

Esa pregunta fuerza dos llamadas a la misma herramienta con argumentos distintos: un primer experimento mejor que una pregunta de una sola llamada, porque ves iterar el bucle.

Fíjate en los dos `return ToolOutput::error()`. Una ventana no válida no es un error de tu código; es una equivocación del modelo que este puede corregir. Devolverla como resultado de error le entrega al modelo una frase sobre la que puede actuar, y el bucle continúa. Lanzar una excepción, en cambio, abortaría toda la ejecución. La Sección 5.11 convierte esa distinción en una regla.

### Cuándo es correcto usar herramientas en línea

**Úsalas para:** prototipos, scripts puntuales, herramientas que genuinamente no se reutilizan, demostraciones didácticas.

**No las uses para:** nada que necesite una dependencia, nada que vayas a testear, nada que aparezca en más de un agente, nada de más de unas diez líneas.

Una clase anónima no captura variables del ámbito que la rodea: una dependencia tiene que entrar por un constructor que escribas para ello, y en ese momento la clase ya se ha ganado un nombre. No se puede simular ni testear de forma aislada, porque no hay un nombre de clase que instanciar, y no se puede reutilizar. La Sección 5.3 arregla las cuatro cosas.

### Puntos clave

- `Tool` es abstracta; la herramienta más ligera es una clase anónima que la extiende dentro de `tools()`.
- La identidad son las propiedades `$name` y `$description`; el esquema es `properties()`; la lógica es `__invoke()`.
- Los nombres de las properties deben coincidir exactamente con los de los parámetros de `__invoke()`: los argumentos se pasan por nombre.
- Las herramientas en línea son para prototipos; no se pueden inyectar, testear ni reutilizar.

## 5.3 Herramientas como clases

Esta es la forma que realmente vas a publicar.

### Genera el esqueleto

```bash
# Unix
vendor/bin/neuron make:tool App\\Neuron\\Tools\\GetTranscriptionTool

# Windows PowerShell
.\vendor\bin\neuron make:tool App\Neuron\Tools\GetTranscriptionTool
```

La clase generada ya tiene las cuatro partes que siguen, con valores de relleno que sustituir.

### Las cuatro partes de una clase herramienta

```php
<?php

namespace App\Neuron\Tools;

use NeuronAI\HttpClient\Curl\CurlHttpClient;
use NeuronAI\HttpClient\HttpClientInterface;
use NeuronAI\HttpClient\HttpRequest;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

class GetTranscriptionTool extends Tool
{
    protected string $name = 'get_transcription';

    protected ?string $description = 'Retrieve the transcription of a youtube video.';

    protected HttpClientInterface $client;

    public function __construct(protected string $key)
    {
    }

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'video_url',
                type: PropertyType::STRING,
                description: 'The URL of the YouTube video.',
                required: true,
            ),
        ];
    }

    public function __invoke(string $video_url): string
    {
        $response = $this->getClient()
            ->request(HttpRequest::get('transcript?url=' . \urlencode($video_url) . '&text=true'))
            ->json();

        return (string) ($response['content'] ?? '');
    }

    protected function getClient(): HttpClientInterface
    {
        return $this->client ??= (new CurlHttpClient(customHeaders: ['x-api-key' => $this->key]))
            ->withBaseUri('https://api.supadata.ai/v1/youtube/');
    }
}
```

**1. Identidad** — las propiedades `$name` y `$description`. Son valores por defecto de propiedades de la clase, no argumentos del constructor, así que la identidad la fija la clase y no hay constructor padre al que llamar.

**2. El constructor** — pertenece por completo a tus dependencias. Aquí es una clave de API; en una aplicación real podría ser un repositorio, una conexión PDO, un servicio de correo.

**3. `properties()`** — el esquema, los mismos objetos que en la versión en línea.

**4. `__invoke()`** — la implementación. El método mágico de invocación de PHP, de modo que el objeto herramienta es invocable. Los nombres de los parámetros deben coincidir con los de las properties, exactamente como en la Sección 5.2.

Cualquier otra cosa que la clase necesite —ayudantes como `getClient()`— se mantiene privada a la herramienta. El cliente perezoso con `??=` de aquí es un hábito pequeño pero bueno: no se construye ningún cliente HTTP salvo que el modelo llame realmente a la herramienta. Y el cliente es el propio `CurlHttpClient` de NeuronAI, el mismo que usa el juego de herramientas de Supadata integrado en el framework, así que la herramienta no necesita nada más allá de `ext-curl`: ni Guzzle ni ningún paquete de Composer adicional.

### Engancharla

```php
protected function tools(): array
{
    return [
        GetTranscriptionTool::make('API_KEY'),
    ];
}
```

`::make()` reenvía sus argumentos al constructor. Así, una herramienta con dependencias sigue leyéndose limpiamente en la lista de herramientas del agente.

### Por qué este patrón se gana su ceremonia extra

**Acepta dependencias.** Una clase recibe una conexión PDO, un repositorio, un servicio de correo, mediante su constructor, desde tu contenedor de inyección de dependencias. Y puede conservarlas sin ceremonia: como en los mensajes y en el estado persistido solo viajan datos `ToolCall`, un objeto herramienta nunca se serializa, así que una conexión viva o un cliente HTTP dentro de él funciona con cualquier backend de persistencia.

**Es testeable unitariamente sin un LLM.** Este es el argumento que más importa:

```php
public function test_it_returns_the_transcript(): void
{
    $tool = new GetTranscriptionTool('fake-key');

    $result = $tool('https://youtube.com/watch?v=xyz');

    $this->assertStringContainsString('expected phrase', $result);
}
```

La herramienta es un objeto invocable. La invocas directamente, sin agente, sin proveedor, sin ninguna llamada de red a un modelo. Dado el problema del no determinismo de la Sección 1.5, que una gran parte de tu sistema agéntico sea PHP corriente y testeable es una victoria significativa, y la frontera entre «testeable» y «no testeable» pasa exactamente por esta clase.

**Es reutilizable y publicable.** Las herramientas implementan `ToolInterface`. Una herramienta bien construida puede publicarse como paquete de Composer o contribuirse al framework.

**Tiene un nombre real.** `GetTranscriptionTool` aparece en las trazas de pila, en tu contenedor de dependencias, en la navegación de tu IDE. Una clase anónima aparece como `NeuronAI\Tools\Tool@anonymous`.

::: {.callout .callout-tip}
[En la práctica]{.callout-title}

Coge la herramienta en línea `get_server_load` de la Sección 5.2, conviértela en clase y escríbele una prueba de PHPUnit. Lleva cinco minutos, y expone el argumento de la testabilidad mucho mejor que leerlo.
:::

### Puntos clave

- Propiedades `$name` / `$description` para la identidad, el constructor solo para las dependencias, `properties()` para el esquema, `__invoke()` para la lógica.
- `::make()` reenvía los argumentos del constructor.
- Las herramientas basadas en clases son inyectables, testeables sin LLM, reutilizables y publicables.
- La clase herramienta es la frontera entre el PHP determinista y la IA no determinista: pon todo el código posible del lado determinista.

## 5.4 Las descripciones de herramientas son ingeniería de prompts

### La afirmación

Cuando un agente se comporta mal, la causa normalmente no es el modelo, ni el framework, ni el prompt de sistema. Es que la descripción de una herramienta no le dijo al modelo con suficiente claridad cuándo usarla.

La documentación oficial es inusualmente directa al respecto: el nombre y la descripción de la herramienta y de sus properties se pasan al LLM en lenguaje natural, y cuanto más explícito y claro seas, más probable es que el LLM entienda cuándo, si acaso, y por qué usar la herramienta.

### Qué ve el modelo

No tu código. No tus tipos. No el nombre de tu clase. Esto, más o menos:

```json
{
  "name": "get_transcription",
  "description": "Retrieve the transcription of a youtube video.",
  "parameters": {
    "video_url": {
      "type": "string",
      "description": "The URL of the YouTube video.",
      "required": true
    }
  }
}
```

Esa es la interfaz completa. Toda decisión de selección que tome el modelo se basa en esas cadenas.

### La fórmula de descripción en cuatro partes

**1. Qué hace.** Una oración. Verbo concreto.

**2. Cuándo usarla.** La parte más valiosa y la más frecuentemente omitida. Da las condiciones de activación en el lenguaje del usuario, no en el tuyo.

**3. Qué devuelve.** Fija expectativas para que el modelo pueda planificar una secuencia de varios pasos.

**4. Qué no hacer.** La salvaguarda. Especialmente «no inventes estos datos».

**Mala:**

```php
protected string $name = 'get_weather';

protected ?string $description = 'Gets the weather.';
```

**Buena:**

```php
protected string $name = 'get_current_weather';

protected ?string $description = 'Returns current weather conditions for a location: temperature in Celsius, '
    . 'wind speed, and a condition code. Use this whenever the user asks about '
    . 'current weather, temperature, or conditions anywhere. Requires latitude '
    . 'and longitude — derive them yourself from the place name. Never invent '
    . 'weather data; always call this tool.';
```

Más larga, y vale cada token. Responde a las cuatro preguntas.

### Las descripciones de las properties importan igual

La descripción del parámetro es donde previenes las llamadas malformadas:

```php
new ToolProperty(
    name: 'latitude',
    type: PropertyType::NUMBER,
    description: 'Latitude in decimal degrees. Example: 45.0703 for Turin, Italy. '
               . 'Negative for southern hemisphere.',
    required: true,
)
```

El ejemplo trabajado está haciendo trabajo real. Los modelos reconocen patrones a partir de ejemplos de forma mucho más fiable que a partir de descripciones abstractas de tipos, y un ejemplo en la descripción de una property elimina toda una clase de errores de formato.

### Convenciones de nombres

- `snake_case`, verbo primero: `get_order_status`, `send_notification`, `search_documents`
- Específico antes que general: `search_orders_by_customer` gana a `search`
- Prefijos consistentes en todo tu catálogo: `get_`, `list_`, `create_`, `send_`
- Nunca uses jerga interna. `fetch_sku_metadata_v2` no significa nada para el modelo, y los sufijos de versión internos lo confunden activamente.

### El experimento que cambia cómo escribes herramientas

Construye el mismo agente del tiempo dos veces. Versión A: `'get_weather'` / `'Gets the weather.'`. Versión B: la descripción en cuatro partes anterior.

Pregunta a ambas: *«¿Debería llevarme una chaqueta a Turín esta tarde?»*

La versión A responde con frecuencia desde el conocimiento general del modelo sin llamar a la herramienta en absoluto, porque nada en la descripción conectaba «¿debería llevarme una chaqueta?» con «consulta el tiempo». La versión B llama a la herramienta, porque la descripción enumeraba explícitamente las condiciones de activación.

Mismo código, mismo modelo, una cadena cambiada, comportamiento correcto. **La descripción es el programa.**

### Consejos prácticos

- Escribe la descripción antes que la implementación. Si no puedes describir cuándo debe usarse, el alcance de la herramienta está mal.
- Trata las descripciones como código versionado y revísalas.
- Cuando un agente elija la herramienta equivocada, lee las dos descripciones una al lado de la otra. La ambigüedad casi siempre es visible.
- Mantén explícita la frontera entre dos herramientas parecidas. Si tienes `search_orders` y `search_products`, di en cada descripción para qué sirve la *otra*.

### Puntos clave

- El nombre, la descripción y las descripciones de las properties son toda la interfaz del modelo.
- Cuatro partes: qué, cuándo, qué devuelve, qué no hacer.
- Los ejemplos dentro de las descripciones de properties previenen errores de formato.
- Herramienta equivocada elegida → lee las descripciones, no el código.

## 5.5 Tipos de property: escalares, arrays y objetos

### ToolProperty — escalares

```php
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolProperty;

protected function properties(): array
{
    return [
        new ToolProperty(
            name: 'arg',
            type: PropertyType::STRING,
            description: 'Describe the value you expect',
            required: true,
        ),
    ];
}
```

`PropertyType` es un enum con seis casos: `STRING`, `INTEGER`, `NUMBER`, `BOOLEAN`, `ARRAY` y `OBJECT`. Los cuatro primeros son los que usas con `ToolProperty`; los arrays y los objetos tienen sus propias clases de property, más abajo. `ToolProperty` también acepta un array `enum:` cuando una cadena solo puede tomar unos pocos valores.

Dos argumentos que conviene distinguir:

- **`required`** — ¿debe el modelo suministrar esta property en absoluto?
- **`nullable`** — ¿puede el valor suministrado ser nulo?

No son lo mismo, y confundirlos produce esquemas que permiten entradas que no pretendías. Una property obligatoria pero anulable debe estar presente y puede ser nula; una property opcional puede faltar por completo.

### Qué llega a `__invoke()`: vincular es convertir

El tipo que declaras no es solo esquema. Antes de que se ejecute `__invoke()`, NeuronAI pasa cada argumento que envió el modelo por el `cast()` de su property, y tu método recibe el valor convertido.

Esto importa porque los modelos son descuidados con los tipos JSON. Pide un `NUMBER` y recibirás con regularidad `"45.07"`: una cadena. Pide un `BOOLEAN` y puede que recibas `"true"`. La conversión convierte lo que convertiría el propio modo coercitivo de PHP: `"45.07"` pasa a ser `45.07`, `"5"` pasa a ser `5` para un `INTEGER`, `"true"` pasa a ser `true`, y los elementos de un array pasan por la property `items` del array. Así que un simple `float $latitude` en tu firma es seguro; no necesitas ampliarlo a `float|int|string` y convertir a mano.

Lo que no se puede convertir nunca llega a tu código. Si el modelo envía `"north"` para un `NUMBER`, `__invoke()` ni siquiera se llama: el resultado de la herramienta pasa a ser un error que el modelo puede leer —`Parameter "latitude" must be of type number, string given.`— y el bucle continúa, de modo que el modelo puede corregir su propia llamada. Un tipo incorrecto es una equivocación del modelo que él debe corregir, no un error de tu aplicación. Un argumento obligatorio que *falta* es otra cosa, y sigue lanzando una excepción.

Los mismos valores tipados alimentan todo lo demás que juzga la llamada —las políticas de aprobación de la Sección 5.10 y el recuento de ejecuciones de la Sección 5.9—, así que una política que compara `amount > 100` no puede eludirse porque el modelo escriba el número como cadena.

### ArrayProperty — listas

Usa `items` para declarar el tipo de los elementos:

```php
use NeuronAI\Tools\ArrayProperty;

new ArrayProperty(
    name: 'prop_array',
    description: 'Describe the value you expect',
    required: true,
    items: new ToolProperty(
        name: 'prop',
        type: PropertyType::STRING,
        description: 'Describe the value you expect',
        required: true,
    ),
)
```

Y limita el tamaño con `minItems` / `maxItems`:

```php
$property = new ArrayProperty(
    name: 'tags',
    description: 'List of tags associated with the item',
    required: true,
    items: new ToolProperty(
        name: 'tag',
        type: PropertyType::STRING,
        description: 'A single tag',
        required: true,
    ),
    minItems: 1,
    maxItems: 10,
);
```

**Por qué los límites importan en la práctica.** Sin `maxItems`, a un modelo al que le pidan «etiqueta este artículo a fondo» puede devolver sesenta etiquetas. Cada una de ellas son tokens en la conversación y, si tu herramienta hace luego una llamada a la API por etiqueta, sesenta llamadas. `maxItems: 10` es un control de costes y una protección frente a límites de tasa, no meramente una regla de validación.

Eso sí, ten claro dónde se aplica. `minItems` y `maxItems` van al JSON Schema que recibe el modelo, y los modelos y proveedores suelen respetarlos, pero la vinculación de NeuronAI convierte los elementos sin contarlos. Si once elementos causarían un daño real, comprueba `count()` en `__invoke()` y devuelve un error sobre el que el modelo pueda actuar.

### ObjectProperty — estructuras anidadas

```php
use NeuronAI\Tools\ObjectProperty;

new ObjectProperty(
    name: 'colors',
    description: 'RGB color',
    required: true,
    properties: [
        new ToolProperty(
            name: 'r',
            type: PropertyType::NUMBER,
            description: 'The red part of the RGB',
            required: true,
        ),
        new ToolProperty(
            name: 'g',
            type: PropertyType::NUMBER,
            description: 'The green part of the RGB',
            required: true,
        ),
        new ToolProperty(
            name: 'b',
            type: PropertyType::NUMBER,
            description: 'The blue part of the RGB',
            required: true,
        ),
    ],
)
```

Las properties se anidan de forma arbitraria: un array de objetos, un objeto que contiene arrays, y así sucesivamente.

### La guía de diseño que importa más que la sintaxis

*Puedes* expresar estructuras profundamente anidadas. En su mayoría *no deberías*.

Cada nivel de anidamiento es otra oportunidad para que el modelo produzca una forma que no valide, y los esquemas complejos consumen tokens en absolutamente cada petición del bucle: recuerda de la Sección 1.3 que el esquema completo de herramientas se retransmite en cada iteración.

Tres reglas:

**Prefiere lo plano.** Dos properties escalares ganan a un objeto con dos campos, salvo que el objeto se reutilice genuinamente entre herramientas.

**Prefiere varias herramientas estrechas a una herramienta ancha con una unión discriminada.** Una herramienta que recibe `{action: "create"|"update"|"delete", payload: {...}}` es más difícil de llamar correctamente para el modelo que tres herramientas separadas. Además es imposible de autorizar con granularidad: no puedes dejar que un usuario borre pero no cree si ambas cosas viven detrás de una sola herramienta.

**Deja que el modelo haga el trabajo de conversión.** En lugar de aceptar una fecha en texto libre y parsearla tú, declara la property como una cadena ISO 8601 con un ejemplo en la descripción. Los modelos son buenos convirtiendo formatos, y obtienes una forma validada en la frontera en lugar de un problema de parseo dentro de tu herramienta.

### Ejercicio

Escribe una herramienta `compare_cities` que reciba un `ArrayProperty` de nombres de ciudad con `minItems: 2, maxItems: 5` y devuelva una comparación. Después pídele al agente que compare ocho ciudades. Observa si el modelo respeta la restricción y cómo reacciona al verse restringido. Después añade en `__invoke()` una comprobación con `count()` que devuelva `ToolOutput::error()`, y mira qué hace el modelo con esa información.

### Puntos clave

- Tres clases: `ToolProperty`, `ArrayProperty`, `ObjectProperty`.
- `required` y `nullable` son preguntas distintas.
- Vincular es convertir: `__invoke()` recibe valores tipados, y un argumento que no se puede convertir vuelve al modelo como error en lugar de llegar a tu código.
- `minItems` / `maxItems` son controles de coste y de límite de tasa, no solo validación.
- Prefiere esquemas planos y varias herramientas estrechas a una herramienta ancha.

## 5.6 Entrada estructurada en herramientas

### El problema

El ejemplo RGB de la Sección 5.5 necesitaba tres objetos `ToolProperty` anidados para tres campos. Un objeto realista —una dirección, una línea de pedido, un filtro de búsqueda— tiene ocho o doce. Escribir ese esquema a mano es verboso y, peor aún, el esquema y aquello que describe se separan con el tiempo.

### La solución

Pasa una clase PHP a `ObjectProperty` mediante el argumento `class`. NeuronAI genera el esquema a partir de la clase y le entrega a tu herramienta una **instancia** de ella.

**El DTO:**

```php
<?php

namespace App\Neuron\Dto;

use NeuronAI\StructuredOutput\SchemaProperty;

class Color
{
    #[SchemaProperty(description: "The RED part of the RGB", required: true)]
    public float $r;

    #[SchemaProperty(description: "The GREEN part of the RGB", required: true)]
    public float $g;

    #[SchemaProperty(description: "The BLUE part of the RGB", required: true)]
    public float $b;
}
```

**La herramienta:**

```php
<?php

namespace App\Neuron\Tools;

use App\Neuron\Dto\Color;
use NeuronAI\Tools\ObjectProperty;
use NeuronAI\Tools\Tool;

class MyTool extends Tool
{
    protected string $name = 'my_tool';

    protected ?string $description = 'Describe what the tool does and when to use it.';

    protected function properties(): array
    {
        return [
            new ObjectProperty(
                name: 'color',
                description: 'Combination of colors',
                required: true,
                class: Color::class,
            ),
        ];
    }

    public function __invoke(Color $color) { /* ... */ }
}
```

Fíjate en la firma: `__invoke(Color $color)`. No un array. Un objeto tipado, con autocompletado del IDE, análisis estático y soporte de refactorización. Es la regla de «vincular es convertir» de la Sección 5.5 aplicada a objetos: el `ObjectProperty` deserializa el JSON del modelo en tu clase antes de la llamada.

### Por qué este es el valor por defecto que conviene adoptar

**El esquema y el tipo no pueden separarse.** Añade un campo al DTO y el esquema se actualiza. No hay un segundo sitio que recordar editar, que es el modo de fallo de los esquemas escritos a mano en un código base con más de un colaborador.

**El análisis estático vuelve a funcionar.** PHPStan o Psalm pueden ver `$color->r`. Con entrada en forma de array ven `mixed`, y los cuerpos de tus herramientas se convierten en un punto ciego del análisis.

**El DTO es reutilizable.** La misma clase anotada sirve para el structured *output* (Capítulo 6). Una sola clase `Order` puede definir qué debe producir el modelo y qué acepta una herramienta: el mismo contrato en ambas direcciones.

**`#[SchemaProperty]` admite restricciones de validación.** Además de `title`, `description` y `required`, el atributo acepta `min` y `max`, `minLength` y `maxLength`, y `anyOf`. Empuja la validación al esquema para que el modelo reciba las reglas en lugar de que tu herramienta descubra las violaciones en tiempo de ejecución.

::: {.callout .callout-warning}
[Nota sobre el namespace]{.callout-title}

`SchemaProperty` vive bajo `NeuronAI\StructuredOutput\`, no bajo `NeuronAI\Tools\`. Eso no es un accidente: es el mismo mecanismo que usa el sistema de salida estructurada, que es exactamente por lo que el DTO es reutilizable en ambos. La documentación a veces lo escribe como `NeuronAI\StructuredOutput\Property`, que no existe; ver el punto 12 del Apéndice A.
:::

### Ejercicio

Reescribe la `WeatherTool` del Laboratorio 3 para que reciba un DTO `Coordinates` con `latitude` y `longitude` anotados con `#[SchemaProperty]`. Pon las dos versiones una al lado de la otra y decide cuál preferirías mantener con cuatro colaboradores.

### Puntos clave

- `ObjectProperty(class: MyDto::class)` genera el esquema a partir de una clase PHP anotada.
- `__invoke()` recibe una instancia tipada, no un array.
- El esquema y el tipo no pueden separarse; el análisis estático sigue funcionando.
- El mismo DTO sirve para entrada estructurada y para salida estructurada.

## 5.7 Juegos de herramientas

### El problema que resuelven los juegos de herramientas

Un agente que necesita matemáticas necesita más de una herramienta: algo que evalúe una fórmula, aritmética entera exacta para factoriales, combinaciones y números primos, y estadística —media, mediana, moda, varianza, desviación típica—. Declarar catorce herramientas individualmente en cada agente es ruido.

### Enganchar uno

```php
<?php

namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            CalculatorToolkit::make(),
        ];
    }
}
```

Una línea, catorce herramientas.

### De qué está hecho un juego de herramientas

```php
namespace NeuronAI\Tools\Toolkits\Calculator;

use NeuronAI\Tools\Toolkits\AbstractToolkit;

class CalculatorToolkit extends AbstractToolkit
{
    public function guidelines(): ?string
    {
        return <<<TEXT
            This toolkit performs mathematical calculations with precision and determinism.
            For arithmetic, algebra, trigonometry, logarithms or any formula, write the whole expression
            and pass it to the evaluate tool in a single call instead of computing intermediate steps
            yourself; it works in double precision, about 15 significant digits. Use the integer tools
            (factorial, combinations, permutations, gcd, lcm, mod_pow, is_prime, prime_factors) when an
            exact result with large integers is required, and the statistics tools for datasets.
            TEXT;
    }

    public function provide(): array
    {
        return [
            EvaluateTool::make(),
            FactorialTool::make(),
            CombinationsTool::make(),
            PermutationsTool::make(),
            GcdTool::make(),
            LcmTool::make(),
            ModPowTool::make(),
            IsPrimeTool::make(),
            PrimeFactorsTool::make(),
            MeanTool::make(),
            MedianTool::make(),
            ModeTool::make(),
            VarianceTool::make(),
            StandardDeviationTool::make(),
        ];
    }
}
```

Dos métodos en `AbstractToolkit`.

**`provide()`** devuelve las herramientas. Una vez enganchadas, se comportan exactamente como si se hubieran declarado individualmente.

**`guidelines()` es el interesante.** Le da al modelo información contextual sobre cómo funcionan las herramientas *en conjunto*, algo que ninguna descripción de herramienta individual puede transmitir. NeuronAI añade al prompt de sistema las guidelines de cada juego de herramientas enganchado, seguidas de los nombres de sus herramientas.

Mira lo que dicen en realidad las guidelines de la calculadora: escribe la expresión completa y pásala a `evaluate` en una sola llamada, en lugar de calcular tú los pasos intermedios. Esa única frase cambia el comportamiento. Los modelos de lenguaje son poco fiables con la aritmética, y lo son igualmente al copiar un resultado intermedio largo de una llamada a herramienta a la siguiente. Sin la guideline, un modelo ante un cálculo de varias partes o intenta hacerlo mentalmente o encadena una docena de llamadas pequeñas, transcribiendo números de coma flotante entre ellas. Con ella, el modelo escribe `(19.3 + 18.6) / 2` una sola vez y un analizador determinista lo calcula.

**Ese es el punto que conviene destacar:** la descripción de una herramienta individual dice *qué hace esta herramienta*. Las guidelines dicen *cómo combinar estas herramientas en una estrategia*. Si construyes tu propio juego de herramientas, las guidelines son donde va la estrategia, y saltárselas desperdicia la mayor parte del mecanismo.

::: {.callout .callout-warning}
[La calculadora necesita bcmath]{.callout-title}

Las herramientas de aritmética entera exacta calculan con la extensión `bcmath` y se niegan a construirse sin ella. Como `provide()` instancia todas las herramientas, `CalculatorToolkit::make()` falla al arrancar el agente en una compilación de PHP sin `ext-bcmath`, aunque solo quisieras `evaluate`. Habilita la extensión en todos los sitios donde se ejecute el agente, o engancha individualmente `EvaluateTool::make()` y las herramientas de estadística.
:::

### El catálogo integrado

| Juego de herramientas | Capacidad | Necesita |
|---|---|---|
| **Calculator** | 14 herramientas: evaluación de expresiones, matemáticas enteras exactas (factorial, combinaciones, MCD, números primos…), media, mediana, moda, varianza, desviación típica | `ext-bcmath` |
| **Calendar** | 18 herramientas: hora actual, formateo, diferencias, conversión de zona horaria, día de la semana, año bisiesto, periodos | — |
| **MySQL / PGSQL** | Introspección de esquema, SELECT, operaciones de escritura | PDO |
| **FileSystem** | leer, grep, glob, parsear — y escribir, editar, borrar, y una shell bash | directorio de ámbito opcional |
| **Tavily** | búsqueda web, extracción de páginas, rastreo de sitios | clave de API |
| **Jina** | búsqueda web, lector de URL | clave de API |
| **Supadata YouTube** | transcripción de vídeo, metadatos de vídeo, canal, lista de reproducción | clave de API |
| **Zep** | almacenar y recuperar memoria a largo plazo | clave de API |
| **AWS SES** | enviar correo | `aws/aws-sdk-php` |

Lee dos veces la fila de FileSystem. El juego de herramientas no es de solo lectura: enganchado entero, le da al modelo la capacidad de sobrescribir, borrar y ejecutar comandos de shell. Su directorio de ámbito opcional (`FileSystemToolkit::make('/path/to/docs')`) confina las herramientas de archivos a un único árbol, pero la shell solo se arranca ahí, no queda confinada por él. La Sección 5.8 muestra cómo quedarte solo con las herramientas que de verdad quieres ofrecer.

### Los juegos de herramientas de base de datos merecen atención especial

`MySQLToolkit` le da a un agente acceso genuino a tus datos. Pregunta «¿cuántos pedidos recibimos hoy?» y hace introspección del esquema, escribe una consulta y devuelve el número real, sin alucinaciones.

```php
use NeuronAI\Tools\Toolkits\MySQL\MySQLToolkit;

protected function tools(): array
{
    return [
        MySQLToolkit::make(
            new \PDO("mysql:host=localhost;dbname=DB_NAME;charset=utf8mb4", "DB_USER", "DB_PASS"),
        ),
    ];
}
```

El juego de herramientas se divide en herramientas separadas por capacidad, y **la división es el control de seguridad**:

- `MySQLSchemaTool` — lee la estructura
- `MySQLSelectTool` — lee datos
- `MySQLWriteTool` — INSERT, UPDATE, DELETE

El propio consejo de la documentación merece citarse: si no confías en el comportamiento de tu agente, simplemente puedes no proporcionarle la herramienta de escritura. Enganchar solo las herramientas de lectura es una mitigación completa y eficaz, no un compromiso.

Segundo control: `MySQLSchemaTool` recibe una lista opcional de tablas.

```php
MySQLSchemaTool::make(
    new \PDO($dsn, $user, $password),
    ['users', 'categories', 'articles', 'tags']
)
```

Esto limita lo que el agente puede ver, lo que limita lo que puede consultar. Un agente de contenidos ve artículos, categorías y etiquetas. Un agente de administración de usuarios ve usuarios, roles y permisos. Ninguno de los dos ve pagos.

Tercer control, y el que conviene enfatizar más: **la instancia de PDO es una conexión, así que dale al agente sus propias credenciales de base de datos.** Un usuario de MySQL de solo lectura cuesta una sentencia `GRANT` y aplica en la capa de base de datos lo que tu selección de herramientas aplica en la capa de aplicación. Defensa en profundidad, y la única capa con la que un prompt no puede discutir.

### Puntos clave

- Un juego de herramientas engancha en una línea un conjunto coherente de capacidades.
- `guidelines()` transmite la estrategia entre herramientas: la parte que cambia el comportamiento.
- Los juegos de herramientas de base de datos separan lectura de escritura a propósito; omitir la herramienta de escritura es un diseño válido.
- Limita el alcance del esquema por tabla y dale al agente sus propias credenciales de solo lectura.

## 5.8 Filtros de juego de herramientas: exclude, only, with

### Por qué filtrar no es un detalle

Un juego de herramientas es un conjunto coherente, pero «coherente» no es lo mismo que «apropiado para este agente». Tres costes concretos de enganchar más de lo que necesitas:

**Tokens.** El nombre, la descripción y el esquema de parámetros de cada herramienta se transmiten en **cada** iteración del bucle. Solo el juego de herramientas Calendar son dieciocho herramientas. Con cinco iteraciones del bucle, has pagado ese esquema cinco veces.

**Errores de herramienta equivocada.** La precisión de la selección se degrada a medida que crece el catálogo. Catorce herramientas matemáticas donde bastarían dos significa doce oportunidades extra de elegir mal.

**Radio de impacto.** Toda herramienta enganchada es alcanzable por cualquier usuario que pueda hablar con el agente. Ese es el modelo de seguridad de la Sección 5.1, aplicado a los imports por comodidad.

### exclude()

Engancha el juego de herramientas y elimina herramientas concretas:

```php
class DocsAgent extends Agent
{
    protected function tools(): array
    {
        return [
            FileSystemToolkit::make('/srv/docs')->exclude([
                WriteFileTool::class,
                EditFileTool::class,
                DeleteFileTool::class,
                BashTool::class,
            ]),
        ];
    }
}
```

La exclusión funciona con nombres de clase totalmente cualificados. Úsala cuando quieras la mayor parte de un juego de herramientas y estés eliminando unos pocos problemas conocidos.

### only()

Engancha el juego de herramientas y conserva un subconjunto:

```php
protected function tools(): array
{
    return [
        CalculatorToolkit::make()->only([
            StandardDeviationTool::class,
            MedianTool::class,
        ]),
    ];
}
```

Úsalo cuando quieras una porción pequeña y concreta de un juego de herramientas grande.

### ¿exclude u only? Una regla que envejece bien

**Prefiere `only()`.**

`exclude()` es una lista de denegación, y las listas de denegación se pudren. Cuando el framework añada herramientas a un juego de herramientas en una versión nueva, tu lista de `exclude()` no sabrá nada de ellas, y tu agente ganará silenciosamente capacidades que nunca revisaste.

No es una hipótesis. El juego de herramientas FileSystem ofrecía antes solo lectura, búsqueda y análisis; ahora incluye además herramientas para escribir, editar, borrar y ejecutar bash. Un agente escrito como `FileSystemToolkit::make()->exclude([ParseFileTool::class])` contra el juego de herramientas antiguo, y actualizado sin revisión, ganó una shell.

`only()` es una lista de permitidos. Aparecen herramientas nuevas en el juego de herramientas y tu agente no las obtiene hasta que tú lo digas. Ese es el valor por defecto correcto para cualquier cosa que toque datos o produzca efectos colaterales. El `DocsAgent` de arriba queda mejor escrito así:

```php
FileSystemToolkit::make('/srv/docs')->only([
    ReadFileTool::class,
    GrepFileContentTool::class,
    GlobPathTool::class,
]),
```

Usa `exclude()` cuando quieras amplitud genuinamente y estés podando problemas conocidos. Usa `only()` en todo lo demás, y especialmente en la Parte V, cuando las herramientas lleguen a tu base de datos.

### with()

Recupera una herramienta concreta del juego de herramientas y reconfigúrala:

```php
protected function tools(): array
{
    return [
        MySQLToolkit::make($this->pdo)
            ->with(
                MySQLSchemaTool::class,
                fn (ToolInterface $tool): ToolInterface => $tool->setMaxRuns(1)
            ),
    ];
}
```

Pasa el nombre de la clase y un callback. Se inyecta la instancia de la herramienta, cambias sus ajustes y la devuelves.

La herramienta de esquema es el ejemplo natural: un agente solo necesita inspeccionar el esquema una vez. Limitarla a una sola ejecución evita que un modelo confundido relea la estructura entera cinco veces, algo lento y caro dado lo verbosa que es la salida del esquema.

`with()` es también donde va la aprobación por herramienta cuando la herramienta viene de un juego de herramientas: `fn (ToolInterface $tool): ToolInterface => $tool->requireApproval()` sobre `MySQLWriteTool`, por ejemplo. La Sección 5.10 trata la aprobación.

::: {.callout .callout-warning}
[El método es setMaxRuns()]{.callout-title}

El ejemplo de `with()` en la documentación llama a `setMaxTries(1)` y no le pasa al juego de herramientas ninguna conexión PDO. Ninguna de las dos cosas funciona: no existe `setMaxTries()` —el setter a nivel de herramienta es `setMaxRuns()` y el de nivel de agente es `toolMaxRuns()`— y `MySQLToolkit` requiere su PDO. Ese es el punto 2 del Apéndice A.
:::

### Combinar filtros

Los métodos se encadenan:

```php
CalculatorToolkit::make()
    ->only([EvaluateTool::class, MeanTool::class])
    ->with(EvaluateTool::class, fn (ToolInterface $tool): ToolInterface => $tool->setMaxRuns(3));
```

Dos herramientas, una de ellas con tope. Léelo de arriba abajo: selecciona y luego configura.

### Puntos clave

- Filtrar reduce tokens, errores de herramienta equivocada y radio de impacto.
- Prefiere `only()`: las listas de permitidos sobreviven a las actualizaciones del framework; las de denegación no.
- `with()` reconfigura una sola herramienta dentro de un juego de herramientas.
- Los filtros se encadenan.

## 5.9 Max Runs: proteger el bucle

### El bucle ilimitado, revisitado

La Sección 1.2 estableció que el bucle del agente es un `while` sin salida garantizada. El modelo sigue pidiendo herramientas hasta que decide que ha terminado. Si nunca lo decide, el bucle nunca termina.

Esto no es hipotético. Tres formas en que ocurre en la práctica:

- La herramienta devuelve algo que el modelo interpreta mal como un fallo, así que reintenta. Eternamente.
- La tarea es genuinamente imposible con las herramientas disponibles, y el modelo sigue probando alternativas.
- Dos herramientas se alimentan mutuamente en un ciclo: la búsqueda devuelve una referencia y la descarga devuelve algo que requiere otra búsqueda.

Cada iteración cuesta una llamada al modelo y hace crecer el contexto. Sin límite, esto es una factura desbocada.

### La protección

NeuronAI cuenta cuántas veces se invoca cada herramienta durante una ejecución del agente: un turno de `chat()`, incluida cualquier pausa intermedia para la aprobación humana. Supera el límite y el nodo de herramientas lanza `ToolRunsExceededException`. **El valor por defecto son 10 llamadas, contadas por herramienta individualmente.**

Ese detalle de «por herramienta individualmente» importa. Cinco herramientas con el límite por defecto significa hasta cincuenta ejecuciones de herramientas en una sola llamada a `chat()` antes de que nada se detenga.

### Configurarlo

```php
use NeuronAI\Exceptions\ToolRunsExceededException;

try {
    $message = YouTubeAgent::make()
        ->toolMaxRuns(5) // Max number of calls for each tool
        ->addTool(
            // Tool level config takes precedence over the global setting
            CustomTool::make()->setMaxRuns(2)
        )
        ->chat(...)
        ->getMessage();

} catch (ToolRunsExceededException $exception) {
    // do something
}
```

Dos niveles:

- **`toolMaxRuns(n)`** en el agente: el valor por defecto para todas las herramientas.
- **`setMaxRuns(n)`** en una herramienta: anula el ajuste del agente para esa herramienta.

**Gana el nivel de herramienta.** Esa precedencia es la que quieres: un valor global permisivo con límites estrictos en las herramientas lentas, caras o peligrosas.

::: {.callout .callout-warning}
[Captura la clase de excepción correcta]{.callout-title}

La documentación ha nombrado la excepción de dos maneras: `ToolRunsExceededException` en su prosa, `ToolMaxTriesException` en el bloque catch de un ejemplo. Solo existe la primera: `NeuronAI\Exceptions\ToolRunsExceededException`. Ese es el punto 1 del Apéndice A, y merece atención: PHP no protesta por un `catch` que nombra una clase inexistente; simplemente nunca coincide. Un nombre de clase incorrecto produce una no-gestión silenciosa en vez de un error evidente, que es la peor clase de error que heredar.
:::

### Qué cuenta como «la misma herramienta»

El contador se indexa por la *clave de ejecución* de la herramienta, que por defecto es su nombre: cada llamada a `get_current_weather` consume el mismo presupuesto, sean cuales sean las coordenadas. Eso es lo correcto para la mayoría de las herramientas, pero no permite distinguir un modelo que consulta legítimamente cinco ciudades de uno que pregunta cinco veces por la misma ciudad.

Cuando los argumentos importan, añade el trait `TrackByInputs` a la clase de la herramienta:

```php
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\TrackByInputs;

class WeatherTool extends Tool
{
    use TrackByInputs;

    // ...
}
```

La clave de ejecución pasa a ser el nombre de la herramienta más un hash de las entradas, así que `setMaxRuns(1)` significa ahora «como mucho una vez *por conjunto de argumentos*»: cinco ciudades distintas pasan, la misma ciudad dos veces no. Para algo más sutil —solo importan algunos parámetros—, sobrescribe tú mismo `getRunKey()`.

Dos detalles más del recuento. Una llamada que un humano *rechazó* no consume ningún hueco. Y el recuento sobrevive a las interrupciones: una pausa de aprobación en mitad de una ejecución no lo reinicia.

### Elegir valores

| Carácter de la herramienta | Límite sugerido | Razonamiento |
|---|---|---|
| Introspección de esquema | 1 | Se lee una vez; la respuesta no cambia a mitad de ejecución |
| API externa cara | 2–3 | Cada llamada cuesta dinero o cuota |
| Cálculo local barato | 5–10 | Necesita repetición genuinamente para matemáticas de varios pasos |
| Operaciones de escritura | 1 | Dos escrituras idénticas es casi siempre un error |

Esa última fila es la importante. Una herramienta de escritura con límite 1 significa que un modelo que reintenta no puede cobrarle dos veces a un cliente. Configúralo deliberadamente.

### Qué te está diciendo un límite superado

Esta es la parte que a la gente se le escapa. Un límite de ejecuciones superado no suele ser un límite puesto demasiado bajo. Es un **diagnóstico**, y casi siempre significa una de tres cosas:

1. **Tu descripción de herramienta no está clara**, así que el modelo sigue probando variantes. Vuelve a la Sección 5.4.
2. **Tu herramienta devuelve algo ambiguo** —una cadena vacía, un error poco útil—, así que el modelo no puede distinguir el éxito del fallo.
3. **La tarea es imposible con las herramientas proporcionadas**, y el modelo está dando palos de ciego. Dale una herramienta que pueda decir «no disponible» como respuesta legítima.

Subir el límite «para que funcione» trata el síntoma. Cuando te encuentres con esta excepción, lee la traza y averigua qué intentaba lograr el modelo en el intento número ocho.

### Gestionarlo con elegancia

Que una excepción llegue al usuario como un 500 es malo. Captúrala y degrada:

```php
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Exceptions\ToolRunsExceededException;

try {
    $answer = $agent->chat(new UserMessage($input))->getMessage()?->getContent();
} catch (ToolRunsExceededException $e) {
    // Log the full trace for diagnosis
    $logger->warning('Agent exceeded tool run limit', [
        'input'     => $input,
        'exception' => $e::class,
        'message'   => $e->getMessage(),
    ]);

    $answer = "I couldn't complete that request. Could you rephrase it, "
            . "or would you like me to pass it to a human?";
}
```

La Sección 5.11 cubre una opción más sofisticada: devolverle el error al modelo para que pueda recuperarse por sí mismo.

### Puntos clave

- El valor por defecto son 10 ejecuciones, por herramienta, por ejecución del agente; superarlo lanza `ToolRunsExceededException`.
- `toolMaxRuns()` fija el valor por defecto del agente; `setMaxRuns()` en una herramienta lo anula.
- Las ejecuciones se cuentan por clave de ejecución: el nombre de la herramienta por defecto; `TrackByInputs` cuenta por conjunto de argumentos.
- Las herramientas de escritura deberían tener tope 1.
- Un límite superado es un diagnóstico sobre el diseño de herramientas, no un límite que subir.

## 5.10 Visibilidad: disponibilidad condicional de herramientas

### La API

```php
class YouTubeAgent extends Agent
{
    protected function tools(): array
    {
        return [
            GetTranscriptionTool::make('API_KEY')->visible(
                auth()->user()->can(...)
            ),
        ];
    }
}
```

`visible(false)` y la herramienta no está disponible durante la ejecución del agente. No está en el esquema enviado al modelo. En lo que respecta al modelo, no existe.

### Por qué ocultar gana a instruir

La alternativa tentadora es poner la regla en el prompt de sistema:

> «Usa la herramienta de reembolso solo si el usuario es administrador.»

No hagas esto. Tres razones, en orden creciente de gravedad:

**Se filtra.** El modelo sabe que la herramienta existe y la mencionará. «Podría tramitar un reembolso, pero no tienes permiso» le dice al usuario exactamente qué capacidad perseguir.

**No es fiable.** Las instrucciones se siguen de forma probabilística. La Sección 1.5 dijo que dieras por hecho el no determinismo, y una regla de control de acceso que funciona el noventa y ocho por ciento de las veces no es control de acceso.

**Es atacable.** Las instrucciones del prompt de sistema compiten con las instrucciones del mensaje del usuario. La inyección de prompts es una técnica viva; un esquema que nunca incluyó la herramienta no es vulnerable a ella.

`visible(false)` elimina la capacidad en lugar de prohibir su uso. El modelo no puede pedir una herramienta de la que nunca se le habló.

### Dónde encaja la visibilidad entre las capas

Cuatro mecanismos independientes, y entender qué hace cada uno es el objetivo de esta sección:

| Capa | Mecanismo | La aplica |
|---|---|---|
| No ofrecida | `visible(false)` | La construcción del esquema |
| Ofrecida, con puerta en ejecución | `approvalPolicy()`, `requireApproval()` | Una decisión humana |
| Ofrecida, comprobada al ejecutar | Comprobación de policy dentro de `__invoke()` | Tu PHP |
| Ofrecida, restringida en el origen | Permisos de base de datos, ámbitos de API | La infraestructura |

Usa varias. `visible()` es tu primera línea, no la única: un error en la expresión de visibilidad no debería ser lo único entre un usuario y un reembolso.

### Visibilidad frente a aprobación

La documentación traza bien esta distinción y vale la pena reproducirla con precisión:

- La **visibilidad** es una decisión *en tiempo de construcción*. La herramienta se incluye en el esquema o no. Se decide antes de que el modelo vea nada.
- La **aprobación** es un *guardián en tiempo de ejecución*. La herramienta se ofrece, el modelo la pide y el framework intercepta la llamada y se detiene a esperar una decisión humana.

La aprobación se expresa en la propia herramienta, y puede condicionarse a los argumentos:

```php
BuyTicketTool::make()->withApprovalPolicy(
    fn (ToolInterface $tool): bool|string => $tool->getInput('amount') > 100
        ? 'Purchases above 100 need a human sign-off'
        : false
)
```

Las compras pequeñas pasan; las grandes esperan a un humano. Eso es mucho mejor producto que permitir siempre o bloquear siempre. Construimos el flujo completo con intervención humana en el Capítulo 15 y lo conectamos a una interfaz real en el Capítulo 22; el resto de esta sección cubre lo que corresponde a la herramienta y al agente, para que la distinción cale mientras la visibilidad está fresca.

### La aprobación vive en la herramienta

Antes de cada llamada a herramienta, el nodo de herramientas del agente le hace a la herramienta una sola pregunta: *¿requiere aprobación esta llamada?* La herramienta responde con los argumentos de la llamada ya vinculados —y convertidos, como describió la Sección 5.5—. No hay middleware que registrar ni interruptor a nivel de agente; una herramienta que nunca pide aprobación nunca queda retenida.

La respuesta viene de dos sitios.

**Quien escribe la herramienta declara su riesgo intrínseco** sobrescribiendo `approvalPolicy()`. El valor por defecto devuelve `false`. Devuelve `true` para someter la herramienta a aprobación, o devuelve una cadena, que cuenta como `true` y sirve además como el motivo que se muestra a quien aprueba:

```php
class TransferMoneyTool extends Tool
{
    protected string $name = 'transfer_money';

    protected ?string $description = 'Transfers money between two accounts of the current customer.';

    protected function approvalPolicy(): bool|string
    {
        return ($this->inputs['amount'] ?? 0) > 100
            ? 'Transfers above $100 require a human sign-off'
            : false;
    }

    // properties(), __invoke() ...
}
```

Este es el sitio adecuado para un riesgo que es propiedad de la herramienta: una transferencia es peligrosa en cualquier agente que llegue a engancharla, así que la herramienta lo dice una sola vez.

::: {.callout .callout-warning}
[approvalPolicy() no recibe argumentos]{.callout-title}

La documentación muestra `approvalPolicy(array $inputs)`. El método no recibe parámetros: las entradas ya están vinculadas a la herramienta, así que léelas de `$this->inputs` o con `$this->getInput('amount')`. Copiar la firma documentada es un error fatal: PHP rechaza una sobrescritura cuya firma es incompatible con la del padre. Apéndice A, punto 45.
:::

**Quien desarrolla el agente la sobrescribe al engancharla**, en cualquiera de los dos sentidos:

```php
protected function tools(): array
{
    return [
        DeleteFileTool::make()->requireApproval(),
        TransferMoneyTool::make()->suppressApproval(),
        BuyTicketTool::make()->withApprovalPolicy(
            fn (ToolInterface $tool): bool|string => $tool->getInput('amount') > 100
                ? 'Purchases above 100 need a human sign-off'
                : false
        ),
    ];
}
```

`requireApproval()` somete a aprobación todas las llamadas. `suppressApproval()` anula una política que declaró la herramienta: para un agente interno por lotes, por ejemplo, donde no hay ningún humano disponible y el riesgo se gestiona en otra parte. `withApprovalPolicy()` sustituye la política declarada por tu propio callback, que recibe la herramienta con las entradas de la llamada ya vinculadas. Si configuras más de una, gana la última sobrescritura. Las herramientas que vienen de un juego de herramientas reciben el mismo trato mediante `with()`, de la Sección 5.8.

### Qué ve quien llama

Cuando llega una llamada retenida, `chat()` no lanza ninguna excepción ni se queda esperando. Devuelve un estado *interrumpido*:

```php
$agent = ShopAgent::make(threadId: $threadId);

$state = $agent->chat(new UserMessage('Buy two tickets for Saturday'));

if ($state->isInterrupted()) {
    foreach ($agent->pendingApprovals() as $action) {
        // $action->id      the tool call ID to decide on
        // $action->name    the tool name
        // $action->reason  why the tool asked, from its policy
        // $action->inputs  the typed arguments
    }
}
```

`pendingApprovals()` devuelve un `Action` por cada llamada que sigue esperando una decisión: lo suficiente para mostrar una pantalla de aprobación. Una decisión vuelve indexada por ID de llamada, y `run()` continúa la misma ejecución:

```php
$state = ShopAgent::make(threadId: $threadId)
    ->submitApprovalDecisions([
        'call_123' => 'approve',
        'call_456' => ['reject', 'Too expensive, ask the user for a cheaper option'],
    ])
    ->run();
```

Tres reglas hacen que esto sea seguro. **Una herramienta solo se ejecuta si se aprueba explícitamente**: el silencio nunca es consentimiento, y una carga que deja una llamada sin decidir vuelve a suspender la ejecución. **Un rechazo no es un error**: el modelo recibe un resultado de herramienta que dice que la acción no se ejecutó, junto con tu motivo, y continúa con ese conocimiento. Y **las llamadas que no necesitaban aprobación se ejecutan igualmente**: en el ejemplo, una compra barata pedida en el mismo turno se ejecuta una vez decidido el lote.

A lo largo de dos peticiones HTTP —el punto de conexión de chat y luego el de aprobación—, el agente necesita el mismo ID de hilo, un backend de persistencia del flujo de trabajo y un historial de conversación duradero, para que el segundo proceso pueda encontrar la ejecución pausada. El Capítulo 15 prepara todo eso.

### El patrón que conviene adoptar

Calcula la visibilidad a partir del actor, no de una variable global:

```php
class OrderAgent extends Agent
{
    public function __construct(private User $user)
    {
        parent::__construct();
    }

    protected function tools(): array
    {
        return [
            SearchOrdersTool::make($this->orders),

            GetOrderStatusTool::make($this->orders),

            RequestRefundTool::make($this->refunds)
                ->visible($this->user->can('refund.create')),

            DeleteOrderTool::make($this->orders)
                ->visible($this->user->hasRole('admin')),
        ];
    }
}
```

El agente recibe al usuario como dependencia del constructor y deduce su propia superficie de capacidades. Dos usuarios que hablan con «el mismo agente» están hablando con agentes que tienen listas de herramientas distintas.

Fíjate en que esto requiere `new OrderAgent($user)` en lugar de `::make()`, como se estableció en la Sección 4.3.

### Ejercicio

Añade una herramienta `delete_cache` a tu agente de demostración, visible solo cuando `APP_ROLE=admin`. Ejecuta el agente como no administrador y pídeselo directamente: «borra la caché». Después pregunta: «¿qué herramientas tienes?». Verifica que la herramienta esté ausente tanto del comportamiento como de la respuesta.

### Puntos clave

- `visible(false)` elimina la herramienta del esquema por completo.
- Ocultar gana a instruir: las restricciones basadas en prompts se filtran, son probabilísticas y son atacables.
- La visibilidad es en tiempo de construcción; la aprobación es en tiempo de ejecución. Ambas existen, para trabajos distintos.
- La aprobación vive en la herramienta: `approvalPolicy()` la declara; `requireApproval()` / `suppressApproval()` / `withApprovalPolicy()` la sobrescriben al engancharla.
- Una llamada retenida devuelve un estado interrumpido; `pendingApprovals()` enumera lo que hay que decidir y `submitApprovalDecisions([...])->run()` continúa. Solo la aprobación explícita ejecuta una herramienta.
- Deduce la visibilidad del actor, inyectado en el constructor del agente.

## 5.11 Gestión de errores en herramientas

### El comportamiento por defecto

Una herramienta puede terminar de dos maneras: devuelve un valor o lanza una excepción. NeuronAI trata ambos casos de forma distinta, a propósito, y la división cae en la frontera natural del lenguaje.

**Un valor devuelto es un resultado de la conversación.** Lo que devuelva `__invoke()` se convierte en el resultado de herramienta que ve el modelo, y el bucle continúa.

**Una excepción que se escapa es un error de programación.** Se propaga hacia arriba a través de `chat()` hasta tu aplicación y aborta la ejecución. El historial de conversación se mantiene coherente —la llamada a herramienta a medio terminar nunca se confirma—, pero el turno ha acabado.

Es un valor por defecto razonable —un fallo silencioso sería peor—, pero significa que la decisión es tuya, herramienta por herramienta: ¿qué fallos forman parte de la conversación y cuáles son defectos?

### La alternativa: cuéntaselo al modelo

Esta es la idea que justifica la sección entera. Un fallo con el que el modelo puede hacer algo no debería tumbar la ejecución; debería devolvérsele al modelo como resultado de la herramienta.

El modelo decide entonces qué hacer: reintentar con otros argumentos, probar otra herramienta o decirle al usuario que los datos no están disponibles. Obtienes una degradación elegante sin escribir lógica de recuperación, porque la lógica de recuperación es el modelo.

La forma principal de hacerlo es **devolver** el fallo, con `ToolOutput::error()`:

```php
use NeuronAI\Tools\ToolOutput;

public function __invoke(string $order_id): string|ToolOutput
{
    $order = $this->orders->find($order_id);

    if ($order === null) {
        return ToolOutput::error(
            "No order matches \"{$order_id}\". Check the number with the user before trying again."
        );
    }

    return \json_encode([
        'id'     => $order->id,
        'status' => $order->status,
        'eta'    => $order->eta,
    ], \JSON_THROW_ON_ERROR);
}
```

El texto del error se convierte en el resultado que lee el modelo, marcado como fallo. Los proveedores con un indicador de error nativo en los resultados de herramientas —Anthropic, Bedrock— lo reciben como tal; los demás reciben el texto. Captura tus propias excepciones en la frontera de la herramienta y convierte así las recuperables, de forma visible, en el código que sabe qué salió mal. Las herramientas integradas de NeuronAI siguen la misma convención: una división por cero en el `evaluate` de la calculadora devuelve `Division by zero at position 2` como resultado de error, no como excepción. Y, como mostró la Sección 5.5, el framework ya lo hace por ti cuando el modelo envía un argumento del tipo incorrecto.

Quedan las excepciones que no previste: de una biblioteca, un controlador, un cliente de red en lo profundo de la llamada. Para esas hay una sobrescritura a nivel de agente: un **gestor de errores de herramientas**. Recibe toda excepción que se escapa de una herramienta. **Si el gestor devuelve un valor, ese valor se le devuelve al modelo como el resultado de la herramienta**, y el bucle continúa. Si devuelve `null`, declina, y la excepción se propaga como antes.

### Definición fluida

```php
$agent = Agent::make()
    ->toolErrorHandler(
        fn (Throwable $e, ToolCall $call): ToolOutput => ToolOutput::error("Error: {$e->getMessage()}")
    );
```

### Dentro de la clase agente

```php
class MyAgent extends Agent
{
    protected function resolveToolErrorHandler(): ?callable
    {
        return fn (Throwable $e, ToolCall $call): ToolOutput => ToolOutput::error("Error: {$e->getMessage()}");
    }
}
```

El callback recibe la excepción y la llamada que falló: la `ToolCall` de la Sección 5.1, con el nombre de la herramienta y los argumentos que envió el modelo. Ambas importan: la llamada te permite ramificar según qué herramienta falló. Puede devolver una cadena, un `ToolOutput` o `null`.

Tipa el segundo parámetro como `ToolCall`. La documentación todavía lo tipa como `ToolInterface`, y un gestor escrito así falla con un `TypeError` justo en el peor momento: la primera vez que una herramienta lanza una excepción. Apéndice A, punto 46.

### Escribir un buen gestor

La versión ingenua filtra las tripas del sistema a la conversación. Una traza de pila de 500 caracteres se convierte en contexto sobre el que el modelo debe razonar, y posiblemente en texto que ve un usuario.

Escribe gestores que le digan al modelo algo *accionable*:

```php
protected function resolveToolErrorHandler(): ?callable
{
    return function (\Throwable $e, ToolCall $call): ?ToolOutput {
        $this->logger->error('Tool failure', [
            'tool'      => $call->getName(),
            'inputs'    => $call->getInputs(),
            'exception' => $e::class,
            'message'   => $e->getMessage(),
        ]);

        return match (true) {
            $e instanceof HttpException => ToolOutput::error(
                "The {$call->getName()} service is temporarily unreachable. "
                . "Do not retry more than once. If it fails again, tell the user "
                . "the data is unavailable right now."
            ),

            $e instanceof AuthorizationException => null,

            default => ToolOutput::error(
                "The {$call->getName()} tool failed. Tell the user you could not "
                . "complete this step, and do not retry."
            ),
        };
    };
}
```

Cuatro principios visibles en ese código:

**Registra completo, cuéntale al modelo lo justo.** Tus registros se llevan la excepción y los argumentos. El modelo se lleva una frase.

**Incluye la instrucción, no solo el hecho.** «Do not retry more than once» está haciendo trabajo real. Sin ella, un fallo transitorio puede consumir el límite de max runs de la Sección 5.9 en segundos.

**Nunca filtres las tripas del sistema a la conversación.** Cadenas de conexión, rutas de archivo, nombres de host internos, credenciales en los mensajes de excepción: todo eso acaba en la transcripción, que puede almacenarse, registrarse y mostrarse al usuario.

**Declina lo que no debe gestionarse.** La rama `null` le devuelve el fallo de permisos a tu aplicación intacto. Más sobre eso a continuación.

### La interacción con max runs

El gestor de errores también captura la excepción del límite de ejecuciones. Eso te da una salida elegante en el límite en lugar de una excepción en la frontera:

```php
$e instanceof ToolRunsExceededException => ToolOutput::error(
    "You have used this tool too many times. Stop calling it and answer with "
    . "what you already know, or tell the user you cannot complete the task."
),
```

El modelo recibe una señal clara de parada y escribe un mensaje final sensato. Mucho mejor que un 500.

### Cuándo dejar que reviente

No todo debe gestionarse. Lanza la excepción desde la herramienta —y devuelve `null` desde el gestor para esa excepción— cuando:

- El fallo indica un error que necesitas ver en tu sistema de seguimiento de errores
- El fallo es una violación de permisos: no dejes que el modelo razone sobre eso, falla en seco y audítalo
- El fallo dejaría los datos en un estado inconsistente

«Devuelve el error al modelo» es un patrón de resiliencia para fallos esperados y recuperables. No es un sustituto de la corrección.

### Puntos clave

- Un valor devuelto es un resultado de la conversación; una excepción que se escapa es un error que aborta la ejecución.
- Devuelve desde la herramienta los fallos recuperables con `ToolOutput::error()`.
- El gestor de errores del agente, `fn (Throwable $e, ToolCall $call)`, convierte las excepciones que se escapan: un valor devuelto se convierte en el resultado de la herramienta; `null` deja que la excepción se propague.
- Registra completo, cuéntale al modelo lo justo e incluye una instrucción sobre reintentar.
- Nunca filtres las tripas del sistema a la transcripción.
- Deja que revienten las violaciones de permisos y los errores de programación.

## 5.12 Herramientas de proveedor

### Qué son

Algunos proveedores incluyen herramientas del lado del servidor —búsqueda web, búsqueda de archivos y otras— que se ejecutan dentro de su infraestructura en lugar de en tu proceso PHP. Tú las habilitas; el proveedor las ejecuta.

### La API

```php
use NeuronAI\Providers\OpenAI\Responses\OpenAIResponses;
use NeuronAI\Tools\ProviderTool;

class MyAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new OpenAIResponses(
            key: 'OPENAI_API_KEY',
            model: 'OPENAI_MODEL',
        );
    }

    protected function tools(): array
    {
        return [
            ProviderTool::make(
                type: 'web_search'
            )->setOptions([/* ... */]),
        ];
    }
}
```

Van en el mismo array `tools()` que todo lo demás, lo cual es una buena pieza de diseño de API: la abstracción aguanta.

**El soporte se limita a `OpenAIResponses`, `Gemini`, `Anthropic` y `ZAI`.** Cualquier otro proveedor —Ollama, la API de chat completions de OpenAI, Mistral, Bedrock— lanza una `ProviderException` cuando encuentra una herramienta de proveedor en la lista.

::: {.callout .callout-warning}
[Errata de la documentación]{.callout-title}

Versiones anteriores de la documentación muestran `ProviderTool:make()` con dos puntos simples. Es una errata por `::`. Punto 6 del Apéndice A.
:::

### El compromiso, tal como lo enuncian los documentos

La documentación oficial es refrescantemente franca: las herramientas de proveedor introducen muchas restricciones, y la forma más flexible y fiable de añadir capacidades a tus agentes sigue siendo el sistema de Herramientas y Juegos de herramientas.

Eso son los autores del framework diciéndote que su propia funcionalidad es la segunda opción. Tómales la palabra, y entiende por qué:

**Pierdes portabilidad.** Esta es la grande. La Sección 3.6 vendió el cambio de proveedor como el beneficio central del framework. Una herramienta de proveedor te ancla: cambia de OpenAI a Ollama y el agente deja de funcionar, porque el proveedor de Ollama rechaza la herramienta con una excepción en la primerísima petición. Al menos el fallo es ruidoso. Pero todo el argumento del escalonado de costes y del riesgo de proveedor se evapora para cualquier agente que dependa de una.

**Pierdes control.** No puedes ver la consulta, filtrar las fuentes, cachear el resultado, limitar su tasa ni registrar qué se recuperó. Para un entorno regulado, «no sabemos qué buscó» no es una respuesta aceptable.

**Pierdes testabilidad.** Sin falso, sin stub, sin CI sin conexión. La Sección 5.3 hizo de la testabilidad el argumento a favor de las clases herramienta; las herramientas de proveedor te la devuelven.

**Heredas sus restricciones.** Los límites de tasa, la disponibilidad regional, los precios y el comportamiento están todos fuera de tu control y pueden cambiar sin un despliegue por tu parte.

### Cuándo son la decisión correcta

No es que nunca lo sean. Las herramientas de proveedor son genuinamente buenas cuando:

- Estás prototipando y quieres búsqueda web funcionando en treinta segundos
- La implementación del proveedor es materialmente mejor que la que construirías (su índice de búsqueda, su tratamiento de documentos)
- Ya estás comprometido con ese proveedor por otros motivos
- La capacidad es periférica: un extra agradable, no algo estructural

### El valor por defecto recomendado

Usa `TavilyToolkit` o `JinaToolkit` para búsqueda web. Ambos son portables, ambos funcionan con cualquier proveedor, ambos son testeables y ambos te dejan ver y cachear lo que volvió.

Recurre a una herramienta de proveedor cuando tengas una razón concreta, y escribe esa razón.

### Puntos clave

- Las herramientas de proveedor se ejecutan del lado del servidor; soportadas solo en OpenAIResponses, Gemini, Anthropic y ZAI; los demás proveedores lanzan una excepción.
- Te cuestan portabilidad, control, testabilidad e independencia.
- La propia documentación del framework recomienda el sistema portable de Herramientas/Juegos de herramientas.
- Buenas para prototipos y capacidades periféricas; malas para cualquier cosa estructural.

## 5.13 Llamadas a herramientas en paralelo

### El problema

Cuando el modelo pide tres herramientas en un mismo turno, el comportamiento por defecto es secuencial:

```
1. Llamar a la herramienta A → esperar el resultado
2. Llamar a la herramienta B → esperar el resultado
3. Llamar a la herramienta C → esperar el resultado

Tiempo total: Tiempo(A) + Tiempo(B) + Tiempo(C)
```

Tres llamadas a la API de 800 ms cada una son 2,4 segundos con el usuario mirando la nada, y eso es una iteración del bucle.

Con ejecución en paralelo:

```
1. Llamar a las herramientas A, B y C a la vez
2. Esperar a que terminen todas

Tiempo total: Máx(Tiempo(A), Tiempo(B), Tiempo(C))
```

800 ms. Un tercio del tiempo, por un booleano.

### Habilitarlo

```bash
composer require spatie/fork
```

```php
class DemoAgent extends Agent
{
    public function __construct()
    {
        parent::__construct();
        $this->parallelToolCalls(true);
    }

    protected function provider(): AIProviderInterface
    {
        // ...
    }

    protected function tools(): array
    {
        return [
            CalculatorToolkit::make(),
        ];
    }
}
```

Por debajo, el framework inyecta un `ParallelToolNode` en lugar del `ToolNode` estándar. Esto es la Sección 2.3 volviéndose concreta: un agente es un flujo de trabajo, y «habilitar herramientas en paralelo» significa *cambiar un nodo por otro*. Es la primera vez en este libro que el sustrato de flujo de trabajo hace algo visible.

### La restricción que lo decide todo

**Requiere la extensión `pcntl`, y `pcntl` solo funciona en procesos de CLI, no en un contexto web.**

Léelo dos veces antes de diseñar alrededor de esta funcionalidad. Significa:

| Contexto | Herramientas en paralelo |
|---|---|
| Script de CLI | ✅ Sí |
| Comando de artisan | ✅ Sí |
| Proceso de cola (CLI) | ✅ Sí |
| Petición HTTP vía PHP-FPM | ❌ No |
| Petición web en cualquier SAPI | ❌ No |

Para una aplicación web, la vía práctica es: empuja la ejecución del agente a un proceso de cola, que es un proceso de CLI. Ahí es donde aplican las herramientas en paralelo, y resulta que es donde querías el trabajo agéntico de larga duración de todos modos, por las razones de latencia de la Sección 1.4. El Capítulo 22 lo construye como es debido.

### Degradación elegante

El diseño aquí es cuidadoso: si `pcntl` no está presente —una máquina de desarrollo con Windows, por ejemplo— o `spatie/fork` no está instalado, la implementación **recae automáticamente en ejecución secuencial**. Hace lo mismo cuando el modelo pidió una sola herramienta, que no justifica un fork. Sin configuración, sin detección de entorno en tu código, sin reventar.

Desarrollas en local sin `pcntl` y despliegas a producción, donde está habilitado, sin cambiar una línea. El agente se adapta al entorno en el que se encuentre.

Ese es un buen ejemplo de un framework absorbiendo la variación del entorno en lugar de empujarla al desarrollador, y vale la pena robarlo como patrón de diseño más que meramente usarlo como funcionalidad.

### Cuándo ayuda de verdad

La ejecución en paralelo solo ayuda cuando el modelo pide **varias herramientas en un solo turno**. No hace nada para:

- Dependencias secuenciales: B necesita la salida de A, así que no pueden solaparse
- Turnos de una sola herramienta
- Herramientas locales rápidas, donde el coste del fork supera al trabajo

Ayuda sobre todo con varias llamadas independientes limitadas por E/S: tres consultas del tiempo, cuatro consultas a APIs, cinco lecturas de archivo. Si tu agente no es «hambriento de herramientas» de esta forma concreta, habilitarlo no cambia nada.

### Precauciones

**Los procesos bifurcados no comparten estado.** Cada fork es un proceso aparte. Las herramientas que mutan estado compartido en memoria, mantienen una transacción abierta o asumen un singleton se comportarán de forma distinta. Mantén las herramientas sin estado y autocontenidas, que es lo que la Sección 5.1 recomendaba de todos modos, por otras razones.

**Depurar es más difícil.** Los errores en un proceso bifurcado son menos agradables de rastrear. Desarrolla con esto desactivado y actívalo cuando el conjunto de herramientas esté estable.

**Las conexiones a base de datos requieren cuidado.** Una conexión PDO heredada a través de un fork es una fuente clásica de fallos extraños e intermitentes. Si tus herramientas acceden a la base de datos, abre la conexión dentro de la herramienta en lugar de compartir una entre forks, o usa los dos hooks que acepta `parallelToolCalls()`, que se ejecutan dentro de cada proceso hijo antes y después de su herramienta:

```php
$this->parallelToolCalls(
    true,
    beforeChild: fn () => DB::purge(),
    afterChild: fn () => DB::purge(),
);
```

Esa es la forma de Laravel: descartar la conexión heredada para que el hijo abra la suya. Del hijo solo vuelve el *resultado* de cada herramienta, serializado; el objeto herramienta y sus dependencias nunca cruzan la frontera del proceso.

### Puntos clave

- `parallelToolCalls(true)` cambia `ToolNode` por `ParallelToolNode`.
- Requiere `spatie/fork` y `pcntl`; **solo CLI**, nunca en una petición web.
- Recae automáticamente en secuencial cuando no está disponible, y en los turnos de una sola llamada.
- Los hooks `beforeChild` / `afterChild` reinician los recursos de cada proceso, como las conexiones a base de datos.
- Ayuda solo con varias llamadas independientes limitadas por E/S en un mismo turno.
- Mantén las herramientas sin estado; ten cuidado con las conexiones a base de datos entre forks.

## Laboratorio 3 — Agente del tiempo y calculadora

**Cubre:** clase herramienta propia, juego de herramientas, filtros, max runs, gestión de errores.

### Objetivo

Un agente que responda *«¿Cuál es la temperatura media actual entre Turín y Milán?»* llamando dos veces a una herramienta del tiempo y una vez a una herramienta de calculadora. Tres idas y vueltas al modelo: la demostración más clara del bucle del agente de todo el libro.

### La herramienta

**`src/Tools/WeatherTool.php`**

```php
<?php

declare(strict_types=1);

namespace App\Tools;

use NeuronAI\Exceptions\HttpException;
use NeuronAI\HttpClient\Curl\CurlHttpClient;
use NeuronAI\HttpClient\HttpClientInterface;
use NeuronAI\HttpClient\HttpRequest;
use NeuronAI\Tools\PropertyType;
use NeuronAI\Tools\Tool;
use NeuronAI\Tools\ToolOutput;
use NeuronAI\Tools\ToolProperty;
use Uri\WhatWg\Url;

class WeatherTool extends Tool
{
    private const BASE_URL = 'https://api.open-meteo.com/v1/';

    protected string $name = 'get_current_weather';

    protected ?string $description = 'Returns current weather conditions for a geographic location: temperature '
        . 'in Celsius, wind speed in km/h, and a numeric weather code. Use this '
        . 'whenever the user asks about current weather, temperature, or conditions '
        . 'anywhere in the world. You must derive latitude and longitude yourself '
        . 'from the place name. Never invent weather data — always call this tool.';

    protected HttpClientInterface $client;

    protected function properties(): array
    {
        return [
            new ToolProperty(
                name: 'latitude',
                type: PropertyType::NUMBER,
                description: 'Latitude in decimal degrees. Example: 45.0703 for Turin, Italy. '
                           . 'Negative values for the southern hemisphere.',
                required: true,
            ),
            new ToolProperty(
                name: 'longitude',
                type: PropertyType::NUMBER,
                description: 'Longitude in decimal degrees. Example: 7.6869 for Turin, Italy. '
                           . 'Negative values for the western hemisphere.',
                required: true,
            ),
        ];
    }

    public function __invoke(float $latitude, float $longitude): string|ToolOutput
    {
        // PHP 8.5: the pipe operator reads top to bottom - the parameters
        // become a query string, and the query string becomes the request.
        $request = [
            'latitude'  => $latitude,
            'longitude' => $longitude,
            'current'   => 'temperature_2m,wind_speed_10m,weather_code',
        ]
            |> \http_build_query(...)
            |> (static fn (string $query): HttpRequest => HttpRequest::get("forecast?{$query}"));

        try {
            $data = $this->getClient()->request($request)->json();
        } catch (HttpException) {
            return ToolOutput::error(
                'The weather service is unreachable right now. Do not retry; '
                . 'tell the user the data is unavailable.'
            );
        }

        if (!isset($data['current'])) {
            return ToolOutput::error('The weather service returned no current conditions for these coordinates.');
        }

        return \json_encode($data['current'], \JSON_THROW_ON_ERROR);
    }

    protected function getClient(): HttpClientInterface
    {
        // PHP 8.5: Uri\WhatWg\Url parses the endpoint the way a browser would,
        // so a malformed base URL fails here rather than on the first request.
        return $this->client ??= (new CurlHttpClient(timeout: 10.0))
            ->withBaseUri(new Url(self::BASE_URL)->toAsciiString());
    }
}
```

Open-Meteo no necesita clave de API, así que todo el laboratorio se ejecuta gratis; combinado con Ollama, lo completas sin cuenta en ningún sitio.

Aquí aparecen dos novedades de PHP 8.5. El operador pipe `|>` pasa el valor de su izquierda como único argumento al callable de su derecha, así que construir la petición se lee en el orden en que ocurre —array, cadena de consulta, petición— en lugar de de dentro hacia fuera. Y `Uri\WhatWg\Url`, la mitad de la extensión URI que sigue el estándar de los navegadores (Sección 3.6), valida la URL base cuando se construye el cliente y no en la primera petición.

Hay tres cosas en esta clase que merecen una segunda mirada. Los parámetros `float` no necesitan ninguna ampliación defensiva, porque la vinculación convierte el `"45.07"` del modelo en `45.07` antes de la llamada (Sección 5.5). Un servicio inalcanzable se *devuelve* como `ToolOutput::error()` en lugar de lanzarse, con una instrucción adjunta (Sección 5.11). Y el cliente HTTP es el propio `CurlHttpClient` del framework, así que el laboratorio no añade ninguna dependencia.

### El agente

**`src/Agents/WeatherAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use App\Tools\WeatherTool;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\ToolCall;
use NeuronAI\Tools\ToolOutput;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\Calculator\EvaluateTool;
use NeuronAI\Tools\Toolkits\Calculator\MeanTool;
use Throwable;

class WeatherAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a weather assistant. You only report real data obtained from your tools.',
            ],
            steps: [
                'Derive the geographic coordinates of every location mentioned by the user.',
                'Call the weather tool once for each location.',
                'If a comparison or an average is requested, use the calculator tools.',
            ],
            output: [
                'Answer in English, in two sentences at most.',
                'Always state temperatures in degrees Celsius.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            WeatherTool::make()->setMaxRuns(4),

            CalculatorToolkit::make()->only([
                EvaluateTool::class,
                MeanTool::class,
            ]),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return function (Throwable $e, ToolCall $call): ToolOutput {
            \error_log(\sprintf('[tool:%s] %s: %s', $call->getName(), $e::class, $e->getMessage()));

            return ToolOutput::error(
                "The {$call->getName()} tool failed. Do not retry more than once. "
                . 'If it fails again, tell the user the data is unavailable.'
            );
        };
    }
}
```

Fíjate en lo que esta única clase demuestra del capítulo: una herramienta basada en clase (5.3), una descripción en cuatro partes (5.4), ejemplos en las descripciones de properties (5.4), `only()` como lista de permitidos (5.8), un tope de ejecuciones por herramienta (5.9) y un gestor de errores real (5.11). De las catorce herramientas de la calculadora, el agente se queda con dos: `evaluate` para cualquier fórmula y `mean` para las medias.

### El ejecutor

**`examples/03-weather-agent.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\WeatherAgent;
use NeuronAI\Chat\Messages\UserMessage;

$prompt = $argv[1] ?? "What's the average current temperature between Turin and Milan?";

$start = \microtime(true);

try {
    echo WeatherAgent::make()
        ->toolMaxRuns(6)
        ->chat(new UserMessage($prompt))
        ->getMessage()
        ?->getContent() . PHP_EOL;

    \printf("\n[%.2fs]\n", \microtime(true) - $start);
} catch (\Throwable $e) {
    \fwrite(STDERR, "Failed: {$e->getMessage()}\n");
    exit(1);
}
```

```bash
php examples/03-weather-agent.php
php examples/03-weather-agent.php "Compare Turin, Milan, Rome and Palermo. Which is warmest?"
```

### Dos cosas que observar

Ejecútalo con Inspector conectado, como muestra el Capítulo 10, y abre la traza. Verás la secuencia real: dos llamadas al tiempo, una llamada a la calculadora —`mean`, o `evaluate` con la fórmula completa— y una respuesta textual final. Esa imagen es lo que la tabla de la Sección 1.2 describía en abstracto, y verla hace concreta la aritmética de costes de la Sección 1.4.

Después rómpelo deliberadamente: cambia la descripción de la herramienta a `'Gets the weather.'` y vuelve a ejecutar. Con frecuencia el modelo responderá desde su conocimiento general sin llamar a la herramienta en absoluto. Devuélvela a su estado. Una cadena, comportamiento completamente distinto: la afirmación de la Sección 5.4, demostrada en tu propia máquina.

## Laboratorio 4 — Agente analista de base de datos

**Cubre:** juego de herramientas de MySQL, delimitación del esquema, privilegio mínimo, diseño de solo lectura.

### Objetivo

Un agente que responda preguntas reales sobre una base de datos real sin alucinar números.

### Configura un usuario de base de datos acotado

Antes de nada de PHP, esto:

```sql
CREATE USER 'agent_ro'@'localhost' IDENTIFIED BY 'a-strong-password';

GRANT SELECT ON shop.orders     TO 'agent_ro'@'localhost';
GRANT SELECT ON shop.customers  TO 'agent_ro'@'localhost';
GRANT SELECT ON shop.products   TO 'agent_ro'@'localhost';

FLUSH PRIVILEGES;
```

**Haz esto primero.** Todo lo demás en este laboratorio es control en la capa de aplicación que un prompt suficientemente astuto podría sortear. Este `GRANT` lo aplica MySQL. Es la única capa a la que no se puede convencer de cambiar de posición.

### El agente

**`src/Agents/DataAnalystAgent.php`**

```php
<?php

declare(strict_types=1);

namespace App\Agents;

use App\ProviderFactory;
use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSchemaTool;
use NeuronAI\Tools\Toolkits\MySQL\MySQLSelectTool;
use NeuronAI\Tools\ToolCall;
use NeuronAI\Tools\ToolOutput;

class DataAnalystAgent extends Agent
{
    private \PDO $pdo;

    public function __construct()
    {
        parent::__construct();

        $this->pdo = new \PDO(
            \sprintf(
                'mysql:host=%s;dbname=%s;charset=utf8mb4',
                env('DB_HOST', '127.0.0.1'),
                env('DB_NAME', 'shop'),
            ),
            env('DB_USER', 'agent_ro'),
            env('DB_PASS', ''),
            [\PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION],
        );
    }

    protected function provider(): AIProviderInterface
    {
        return ProviderFactory::make();
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: [
                'You are a data analyst working with a read-only e-commerce database.',
                'You never estimate or guess numbers. Every figure you report comes from a query.',
            ],
            steps: [
                'Inspect the database schema first, once, to understand the available tables.',
                'Write a SELECT query that answers the question.',
                'Use the calculator tools for any derived statistics.',
            ],
            output: [
                'State the number, then the query you ran, in a fenced sql block.',
                'If a question cannot be answered with the available tables, say so plainly.',
            ],
        );
    }

    protected function tools(): array
    {
        return [
            MySQLSchemaTool::make(
                $this->pdo,
                ['orders', 'customers', 'products'],
            )->setMaxRuns(1),

            MySQLSelectTool::make($this->pdo)->setMaxRuns(5),

            CalculatorToolkit::make(),
        ];
    }

    protected function resolveToolErrorHandler(): ?callable
    {
        return fn (\Throwable $e, ToolCall $call): ToolOutput => ToolOutput::error(
            "Query failed: {$e->getMessage()}. Check the schema and correct the SQL. "
            . "Do not retry more than twice."
        );
    }
}
```

### El ejecutor

**`examples/05-data-analyst.php`**

```php
<?php

declare(strict_types=1);

require __DIR__ . '/../bootstrap.php';

use App\Agents\DataAnalystAgent;
use NeuronAI\Chat\Messages\UserMessage;

$question = $argv[1] ?? 'How many orders did we receive today?';

echo (new DataAnalystAgent())
    ->chat(new UserMessage($question))
    ->getMessage()
    ?->getContent() . PHP_EOL;
```

```bash
php examples/05-data-analyst.php "How many orders did we receive today?"
php examples/05-data-analyst.php "What's the average order value this month, by country?"
php examples/05-data-analyst.php "Which three products have the highest revenue?"
```

### Cuatro capas de defensa

1. **`MySQLWriteTool` no está enganchada.** El agente no tiene forma de escribir.
2. **El esquema está acotado a tres tablas.** El agente no puede ver `payments` ni `users`.
3. **`MySQLSchemaTool` tiene tope de una ejecución.** Sin introspección cara repetida.
4. **El usuario de base de datos solo tiene SELECT sobre tres tablas.** Lo aplica MySQL.

Después ejecuta la demostración que remata la idea:

```bash
php examples/05-data-analyst.php "Delete all orders from last year."
```

El agente explica que no puede. No porque el prompt se lo prohibiera, sino porque **no hay ninguna herramienta que escriba.** Esa distinción es toda la lección de seguridad de este capítulo, y cala mucho mejor como algo que ejecutas que como algo que lees.

## Ejercicios del capítulo

1. **Diseña.** Toma una funcionalidad de tu propia aplicación y diseña tres herramientas para ella. Escribe las descripciones antes que las implementaciones. Para cada una, responde a las cuatro preguntas de la Sección 5.4.

2. **Convierte.** Toma una herramienta en línea y conviértela en clase. Escribe una prueba de PHPUnit que la invoque directamente sin ningún agente involucrado.

3. **Restringe.** Engancha un juego de herramientas con `only()`, fija un tope de ejecuciones por herramienta y añade un gestor de errores que devuelva una instrucción en lugar de una traza de pila.

4. **Rómpelo.** Escribe deliberadamente una descripción de herramienta vaga y observa el fallo. Arréglalo cambiando una cadena. Anota qué cambió en el comportamiento del modelo.

5. **Asegura.** Para un agente con acceso a la base de datos, enumera tus capas de defensa e identifica cuál no podría derrotar un atacante con un prompt.

::: {.callout .callout-warning}
[Antes de publicar nada de este capítulo]{.callout-title}

La documentación de Herramientas es la página más densa del proyecto NeuronAI, y se ha contradicho a sí misma y al código en nombres de excepción, nombres de método, nombres de clase, namespaces, rutas de import y firmas de método. Casi cada uno de ellos produce un error fatal para quien copia la página. Están listados en el Apéndice A, a partir del punto 1, con scripts de sondeo que los resuelven todos contra tu versión instalada en unos minutos.
:::
