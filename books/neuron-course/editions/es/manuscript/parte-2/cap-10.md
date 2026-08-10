# Capítulo 10 — Observabilidad, evaluaciones y pruebas

::: {.callout .callout-tip}
[El código de este capítulo]{.callout-title}

La versión ejecutable de cada listado que sigue está en [`chapters/Ch10`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch10), en el repositorio complementario. Clónalo, ejecuta `composer install` y los ejemplos funcionan contra un Ollama local sin ninguna clave de API.
:::

## 10.1 Por qué no puedes depurar un agente

### El problema, en palabras de los propios autores del framework

La documentación de Inspector para NeuronAI se abre con un pasaje inusualmente honesto para ser documentación de un proveedor:

Integrar agentes de IA significa que no solo trabajas con funciones y código determinista: estás programando influyendo en distribuciones de probabilidad. Misma entrada ≠ misma salida. La reproducibilidad, el versionado y la depuración se convierten en problemas reales. Escribir prompts no es programar en el sentido habitual: no hay tipos estáticos, cambios pequeños rompen la salida, los prompts largos cuestan latencia y no hay dos modelos que se comporten igual con el mismo prompt.

Eso es la Sección 1.5, reformulada por quienes construyeron la herramienta.

### Qué se rompe

**Los puntos de interrupción.** Puedes recorrer tu PHP paso a paso. No puedes recorrer la decisión del modelo. El momento interesante —*¿por qué eligió esa herramienta?*— ocurre en la GPU de otra persona.

**La reproducción.** «Pasos para reproducir» presupone determinismo. Volver a ejecutar la entrada que falla puede funcionar perfectamente.

**Los registros tal como los escribes.** Una línea de registro que dice «el agente respondió» no te dice nada. Necesitas el prompt, las herramientas ofrecidas, la herramienta elegida, los argumentos, el resultado, los tokens y los tiempos, para cada iteración.

**Tu modelo mental de una traza de pila.** La ejecución de un agente no es una pila de llamadas. Es una secuencia de decisiones, y el fallo suele estar en el razonamiento, no en el código.

### Qué la sustituye

| Práctica clásica | Equivalente agéntico |
|---|---|
| Puntos de interrupción | Trazas de ejecución |
| Pasos de reproducción | Un conjunto de datos de entradas representativas |
| Pruebas unitarias | Evaluaciones con asertos basados en propiedades |
| Tasa de error | Puntuación de calidad seguida en el tiempo |
| Trazas de pila | Línea temporal de nodos, herramientas y tokens |

Tres de esos cinco se cubren en este capítulo. Los otros dos —conjuntos de datos y seguimiento de calidad— son la misma herramienta vista a lo largo del tiempo.

### La versión en una frase

> No puedes depurar un agente. Solo puedes observarlo y medirlo.

Que es por lo que la observabilidad era un pilar en la Sección 2.1 y no un apéndice.

### Puntos clave

- Los puntos de interrupción, la reproducción y los asertos de igualdad presuponen determinismo.
- Las trazas sustituyen a la depuración; las evaluaciones a las pruebas unitarias; las puntuaciones de calidad a las tasas de error.
- Por eso la observabilidad es arquitectónica, no operativa.

## 10.2 Configurar Inspector

### Instalar

```bash
composer require inspector-apm/inspector-php
```

Solo hace falta si no estás usando ya otra biblioteca de Inspector: `inspector-laravel`, `inspector-symfony` y demás ya la incluyen.

### La variable de entorno

```dotenv
INSPECTOR_INGESTION_KEY=nwse877auxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Crea una clave registrando una aplicación en `app.inspector.dev`.

### Registrar el observer

```php
use Inspector\Neuron\InspectorObserver;

class MyAgent extends Agent
{
    public function __construct()
    {
        parent::__construct();

        $this->observe(InspectorObserver::instance());
    }

    // ...
}
```

`observe()` funciona en **Agent, RAG y Workflow**, que es la Sección 2.3 otra vez: todos son flujos de trabajo, así que todos aceptan observers.

### Instrumentación automática

Si tu aplicación ya lee archivos de entorno, es probable que NeuronAI se instrumente a sí mismo en cuanto `INSPECTOR_INGESTION_KEY` esté presente. Registrar el observer explícitamente es para cuando no tienes acceso a variables de entorno, o quieres personalizar la configuración:

```php
$this->observe(
    InspectorObserver::instance('INSPECTOR_INGESTION_KEY')
);
```

### El ajuste que te va a morder: autoFlush

Este es el párrafo operativamente más importante del capítulo.

Si tu agente se ejecuta en un proceso de larga vida —un proceso de cola, Swoole, RoadRunner— debes habilitar explícitamente el vaciado automático:

```php
$this->observe(
    InspectorObserver::instance(
        key: 'INSPECTOR_INGESTION_KEY',
        autoFlush: true
    )
);
```

Sin él, los eventos se acumulan en memoria y se vacían al final de la petición. Un proceso de cola que corre durante horas no tiene «final de la petición». Tus trazas no llegan nunca, la memoria crece y concluyes que la integración está rota cuando meramente está mal configurada.

Dado que la Sección 1.4 empuja el trabajo agéntico largo a las colas, y la 5.13 requiere CLI para las herramientas en paralelo, **la mayoría de los despliegues serios de NeuronAI son exactamente el caso que necesita `autoFlush`.**

### Paquetes específicos de framework

Si vas a integrarlo en Laravel o Symfony, añade el paquete del framework (`inspector-laravel`, `inspector-symfony`) para una mejor recogida de datos. No es obligatorio, pero sí recomendable: correlaciona la traza del agente con la petición HTTP, las consultas y el trabajo en cola que lo rodean, que es lo que realmente quieres al diagnosticar un incidente de producción.

El Capítulo 23 lo cubre en el contexto de Laravel.

::: {.callout .callout-warning}
[Deriva de namespaces]{.callout-title}

En el ecosistema aparecen tres nombres distintos para este componente:

- `Inspector\Neuron\InspectorObserver` (documentación actual de Inspector)
- `NeuronAI\Observability\InspectorObserver` (material del lado de NeuronAI)
- `NeuronAI\Observability\AgentMonitoring` (artículos más antiguos, y todavía en algunos ejemplos de salida estructurada)

Confirma cuál existe en tu versión instalada. Este es el sitio con más probabilidad de que copies una instrucción `use` que no resuelva. Apéndice A, punto 16.
:::

### Puntos clave

- `composer require inspector-apm/inspector-php`, fija la clave, llama a `observe()`.
- Funciona en Agent, RAG y Workflow.
- `autoFlush: true` para procesos de cola y entornos de ejecución de larga vida: no es opcional.
- Tres nombres históricos para la clase observer; verifica el tuyo.

## 10.3 Leer una traza

### Qué muestra una traza

Cada paso de inferencia, cada llamada a herramienta, cada recuperación, con argumentos, resultados, recuentos de tokens y tiempos.

Ejecuta el agente del tiempo del Laboratorio 3 con Inspector habilitado y obtienes una línea temporal:

```
▸ WeatherAgent                                        4.82s   3,412 tokens
  ├─ ChatNode                          1.31s     892 in / 84 out
  ├─ ToolNode: get_current_weather     0.42s
  │    input:  {"latitude": 45.0703, "longitude": 7.6869}
  │    output: {"temperature_2m": 14.2, ...}
  ├─ ToolNode: get_current_weather     0.38s
  │    input:  {"latitude": 45.4642, "longitude": 9.19}
  ├─ ChatNode                          1.44s   1,203 in / 61 out
  ├─ ToolNode: mean                    0.01s
  └─ ChatNode                          1.26s   1,172 in / 91 out
```

### Las cuatro preguntas que responder a partir de una traza

Trátalo como un procedimiento, no como «mirar por ahí»:

**1. ¿Cuántas llamadas al modelo?**
Tres aquí. El modelo de costes de la Sección 1.4, hecho visible. Si esperabas una, tienes un problema de diseño.

**2. ¿Qué herramientas, con qué argumentos?**
Aquí es donde se ven los errores de herramienta equivocada y de argumento equivocado. El modelo llamó a `get_current_weather` con las coordenadas de Turín, así que las dedujo correctamente. Si hubiera pasado un nombre de ciudad como cadena, tu descripción de property (Sección 5.4) necesita el ejemplo trabajado.

**3. ¿Adónde se fue el tiempo?**
Llamadas al modelo: 4,01 s. Herramientas: 0,81 s. El modelo es el cuello de botella, así que optimizar significa menos iteraciones, no herramientas más rápidas. Si la proporción fuera la inversa, cachearías la herramienta.

**4. ¿Adónde se fueron los tokens?**
892 → 1.203 → 1.172 tokens de entrada. Creciendo, porque la conversación crece. Exactamente la acumulación de la Sección 1.4, ahora medida en vez de estimada.

### Diagnosticar a partir de trazas: tres patrones

**La misma herramienta llamada cinco veces con argumentos casi idénticos.**
El modelo no cree haber obtenido una respuesta. El valor de retorno de tu herramienta es ambiguo, o su descripción no coincide con lo que hace. Arregla la herramienta, no el límite de ejecuciones.

**Un hueco largo antes de la primera llamada a una herramienta.**
El modelo pasó tiempo decidiendo. Normalmente demasiadas herramientas, o descripciones solapadas. Filtra (Sección 5.8) o añade `ToolSearchMiddleware`.

**Tokens de entrada mucho más altos de lo esperado en la primera llamada.**
Tus esquemas de herramientas son grandes. Cuenta las herramientas que tienes enganchadas. El esquema completo de cada una va en cada petición.

### El ejercicio que mejor enseña esto

No te limites a mirar una traza sana. **Rompe algo y lee la traza.**

Cambia la descripción de `get_current_weather` a `'Gets the weather.'` y vuelve a ejecutar. La traza muestra al modelo respondiendo sin ninguna llamada a herramienta. El código es idéntico; el único cambio es una cadena; la traza muestra que el modelo ni siquiera consideró la herramienta.

Ese es el momento en el que la Sección 5.4 se vuelve real.

### Puntos clave

- Cuatro preguntas: cuántas llamadas, qué herramientas con qué argumentos, adónde se fue el tiempo, adónde se fueron los tokens.
- Llamadas idénticas repetidas significan una herramienta ambigua, no un límite bajo.
- Lee una traza rota, no solo una sana.

## 10.4 Evaluaciones: PHPUnit para sistemas no deterministas

### El encuadre que lo hace encajar

Piensa en una evaluación como **PHPUnit para un servicio que no es determinista.**

Una prueba unitaria conoce la salida esperada porque la función es determinista. A un agente al que preguntas dos veces lo mismo puede darte dos respuestas correctas con formulaciones distintas. No puedes hacer un aserto de igualdad.

Lo que sí puedes hacer: definir un conjunto de datos de entradas realistas, ejecutar el agente contra cada una y hacer asertos de que la salida cumple criterios: contiene palabras clave, se mantiene en un rango de longitud, coincide con un patrón o supera el juicio de otro agente que actúa de revisor.

### Configurar el proyecto

Mantén los evaluadores fuera del código de producción:

```json
"autoload-dev": {
    "psr-4": {
        "App\\Evaluators\\": "evaluators/"
    }
},
```

```bash
mkdir -p evaluators/datasets
composer dump-autoload
```

`autoload-dev` es la elección correcta: el código de evaluación es para desarrollo y control de calidad, y no debería publicarse.

::: {.callout .callout-warning}
[Desajuste de namespace en los documentos]{.callout-title}

El bloque `autoload-dev` de la documentación mapea `App\Evaluators\` a `evaluators/`, pero el comando generador de la misma página crea `App\Neuron\Evaluators\AgentEvaluator`. Esas dos cosas no concuerdan. Elige una convención y úsala de forma consistente. Apéndice A, punto 20.
:::

### Generar un evaluador

```bash
# Unix
vendor/bin/neuron make:evaluator App\\Neuron\\Evaluators\\AgentEvaluator

# Windows
.\vendor\bin\neuron make:evaluators App\Neuron\Evaluators\AgentEvaluator
```

Fíjate en la diferencia singular/plural entre las dos pestañas de los documentos oficiales: `make:evaluator` frente a `make:evaluators`. Una de las dos es una errata. Apéndice A, punto 17.

### La estructura de tres métodos

```php
namespace App\Neuron\Evaluators;

use NeuronAI\Evaluation\Assertions\StringContains;
use NeuronAI\Evaluation\BaseEvaluator;
use NeuronAI\Evaluation\Contracts\DatasetInterface;
use NeuronAI\Evaluation\Dataset\JsonDataset;

class AgentEvaluator extends BaseEvaluator
{
    /**
     * 1. Get the dataset to evaluate against
     */
    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(__DIR__ . '/datasets/dataset.json');
    }

    /**
     * 2. Run the agent logic being tested
     */
    public function run(array $datasetItem): mixed
    {
        $response = MyAgent::make()->chat(
            new UserMessage($datasetItem['input'])
        )->getMessage();

        return $response->getContent();
    }

    /**
     * 3. Evaluate the output against expected results
     */
    public function evaluate(mixed $output, array $datasetItem): void
    {
        $this->assert(
            new StringContains($datasetItem['reference']),
            $output,
        );
    }
}
```

Carga un conjunto de datos, ejecuta cada elemento, haz asertos sobre la salida. Ese es todo el modelo, y su simplicidad es una virtud: la forma le resulta familiar a cualquiera que haya escrito un proveedor de datos en PHPUnit.

### Conjuntos de datos

**`ArrayDataset`** — en línea, bueno para un puñado de casos:

```php
public function getDataset(): DatasetInterface
{
    return new ArrayDataset([
        [
            'input' => 'Hi',
            'reference' => 'help'
        ]
    ]);
}
```

**`JsonDataset`** — un archivo, que es lo que quieres en la práctica:

```php
return new JsonDataset(__DIR__ . '/datasets/dataset.json');
```

**No hay formato prescrito.** El evaluador carga una lista de casos de prueba; las claves son tuyas. `input` y `reference` son convenciones de los ejemplos, no requisitos. Puedes implementar `DatasetInterface` para cargar desde donde sea: una base de datos, un CSV, registros de producción.

Esa última opción es la que conviene destacar: **construye tu conjunto de datos a partir de fallos reales.** Cada vez que un usuario reporte una respuesta mala, añade la entrada al conjunto de datos. Tu suite de evaluación se convierte en una suite de regresión de exactamente aquello que se rompió de verdad.

### Puntos clave

- Las evaluaciones son PHPUnit para servicios no deterministas.
- Tres métodos: `getDataset()`, `run()`, `evaluate()`.
- `ArrayDataset` para unos pocos casos, `JsonDataset` para suites reales, `DatasetInterface` para todo lo demás.
- Haz crecer el conjunto de datos a partir de fallos reales reportados.

## 10.5 Asertos y la IA como juez

### Los asertos integrados

```php
$this->assert(new StringContains('positive'), $output);
$this->assert(new StringContainsAll(['hello', 'world']), $output);
$this->assert(new StringContainsAny(['success', 'completed']), $output);
$this->assert(new StringStartsWith('Hello'), $output);
$this->assert(new StringEndsWith('!'), $output);
$this->assert(new StringLengthBetween(10, 100), $output);
$this->assert(new MatchesRegex('/^\d{3}-\d{2}-\d{4}$/'), $output);
$this->assert(new IsValidJson(), $output);
```

Dos más interesantes:

**`StringDistance`** — similitud de Levenshtein:

```php
$this->assert(new StringDistance(
    reference: 'expected text',
    threshold: 0.5,   // minimum similarity score
    maxDistance: 50   // maximum allowed edits
), $output);
```

**`StringSimilarity`** — similitud semántica mediante incrustaciones:

```php
use NeuronAI\Evaluation\Assertions\StringSimilarity;
use NeuronAI\RAG\Embeddings\OpenAIEmbeddingsProvider;

$this->assert(new StringSimilarity(
    reference: 'The quick brown fox',
    embeddingsProvider: new OpenAIEmbeddingsProvider(key: 'YOUR_KEY'),
    threshold: 0.6
), $output);
```

La distinción merece destacarse. `StringDistance` mide similitud de *caracteres*: «colour» y «color» están cerca. `StringSimilarity` mide *significado*: «el gato se sentó en la alfombra» y «un felino descansaba sobre el tapete» están cerca pese a no compartir casi ningún carácter.

Para evaluar salida en lenguaje natural, la similitud semántica es casi siempre la que quieres. Cuesta una llamada de incrustación por aserto, que es barato.

Esta es además la primera aparición del componente de incrustaciones, que es todo el Capítulo 12.

### La IA como juez

Algunas cualidades no se pueden medir con operaciones sobre cadenas. ¿Es la respuesta educada? ¿Útil? ¿Anclada en la fuente, o alucinada?

Para eso, usa otro agente como evaluador:

```php
use NeuronAI\Evaluation\Assertions\AgentJudge;

class AgentJudgeEvaluator extends BaseEvaluator
{
    protected AgentInterface $judge;

    public function setUp(): void
    {
        $this->judge = Agent::make()
            ->setAiProvider(new Anthropic(/* ... */))
            ->setInstructions('You are an expert evaluator for customer support responses.');
    }

    public function getDataset(): DatasetInterface
    {
        return new JsonDataset(/* ... */);
    }

    public function run(array $datasetItem): mixed
    {
        return MyAgent::make()
            ->chat(new UserMessage($datasetItem['input']))
            ->getMessage()
            ->getContent();
    }

    public function evaluate(mixed $output, array $datasetItem): void
    {
        $this->assert(new AgentJudge(
            judge: $this->judge,
            criteria: 'Response should be helpful, polite, and address the customer\'s question directly',
            threshold: $datasetItem['threshold']
        ), $output);
    }
}
```

::: {.callout .callout-warning}
[Dos cosas que verificar aquí]{.callout-title}

El ejemplo oficial de este bloque escribe mal `Anthropic` como `Antrhopic`. Y los métodos fluidos `setAiProvider()` / `setInstructions()` aparecen solo en este ejemplo: confirma que existan en tu versión antes de construir sobre ellos. Apéndice A, punto 21.
:::

### Los cuatro jueces especializados

NeuronAI incluye jueces para las preguntas de evaluación recurrentes:

**`FaithfulnessJudge`** — ¿está la salida anclada en el contexto proporcionado, o alucinó?

```php
$this->assert(new FaithfulnessJudge(
    judge: $this->judge,
    context: $retrievedDocuments,
    threshold: 0.7
), $output);
```

**Este es el aserto más importante para los sistemas RAG**, y es la razón por la que las evaluaciones aparecen antes de la Parte III y no después. Un sistema RAG que responde con fluidez a partir de información que se inventó es peor que uno que dice «no lo sé». La fidelidad es cómo mides eso, y no puedes medirlo con coincidencia de cadenas.

**`CorrectnessJudge`** — ¿coincide con la respuesta esperada?

```php
$this->assert(new CorrectnessJudge(
    judge: $judge,
    expected: $datasetItem['expected_answer'],
    threshold: 0.7
), $output);
```

**`RelevanceJudge`** — ¿aborda realmente la pregunta?

**`HelpfulnessJudge`** — ¿es útil y accionable?

### Dos precauciones sobre los jueces

**El juez también es no determinista.** Estás midiendo un sistema probabilístico con un instrumento probabilístico. Los umbrales absorben esto, pero no trates la puntuación de un juez como verdad absoluta. Síguela en el tiempo y busca movimiento, no valores absolutos.

**Los jueces cuestan dinero.** Cada aserto juzgado es una llamada extra al LLM. Un conjunto de datos de 200 elementos con tres asertos juzgados son 600 llamadas extra por ejecución. Usa un modelo más barato para el juez que para el agente: una buena aplicación del argumento del cambio de proveedor de la Sección 3.6.

### Asertos propios

```php
use NeuronAI\Evaluation\Assertions\AbstractAssertion;
use NeuronAI\Evaluation\AssertionResult;

class GreaterThanAssertion extends AbstractAssertion
{
    public function __construct(
        private readonly float $threshold
    ) {}

    public function evaluate(mixed $actual): AssertionResult
    {
        if (!is_numeric($actual)) {
            return AssertionResult::fail(
                0.0,
                'Expected numeric value, got ' . gettype($actual),
            );
        }

        if ($actual > $this->threshold) {
            return AssertionResult::pass(1.0);
        }

        return AssertionResult::fail(
            0.0,
            "Expected {$actual} to be greater than {$this->threshold}",
        );
    }
}
```

Fíjate en `AssertionResult::pass(1.0)` y `fail(0.0)`: los asertos devuelven una **puntuación**, no un booleano. Eso es lo que permite el crédito parcial y el juicio por umbral, y es el detalle de diseño que hace de esto un sistema de medición y no una puerta de pasa/falla.

### Puntos clave

- Diez asertos integrados; `StringSimilarity` para el significado, `StringDistance` para los caracteres.
- Cuatro jueces: fidelidad, corrección, relevancia, utilidad.
- `FaithfulnessJudge` es el esencial para RAG: tenlo listo antes de la Parte III.
- Los jueces son no deterministas y cuestan dinero; usa un modelo más barato.
- Los asertos devuelven puntuaciones, no booleanos.

## 10.6 Ejecutar evaluaciones: salida, paralelismo y CI

### Ejecutar

```bash
# Unix
vendor/bin/neuron evaluation --path=evaluators

# Windows
.\vendor\bin\neuron evaluation --path=evaluators
```

::: {.callout .callout-warning}
[Verifica este comando antes que nada]{.callout-title}

La sección de ejecución en paralelo de la misma página de documentación muestra otra invocación: `vendor/bin/neuron evaluation path/to/evaluators --concurrency=3`, con `evaluation` en singular y un argumento posicional en lugar de `--path=`. Ejecuta `vendor/bin/neuron list` en tu versión instalada y usa el que sea real. Apéndice A, punto 18, y el que con más probabilidad hará fallar tu primera ejecución de evaluaciones.
:::

### Drivers de salida

Crea `evaluation.php` en la raíz del proyecto:

```php
<?php

use NeuronAI\Evaluation\Output\ConsoleOutput;
use NeuronAI\Evaluation\Output\JsonOutput;

return [
    'output' => [
        ConsoleOutput::class,
        new JsonOutput(__DIR__ . '/evaluation-results.json'),
    ],
];
```

Fíjate en la forma: `output` es una **lista**, no un mapa de clase a opciones. `EvaluationOutputResolver` acepta o bien la cadena de clase de un controlador que no necesita argumentos en el constructor, o bien una instancia ya construida. No hay ninguna asignación de opciones por reflexión: un controlador que necesite argumentos se entrega ya montado, como `JsonOutput` aquí arriba.

Varios controladores se ejecutan simultáneamente: consola para el desarrollador, JSON para que lo consuma la CI.

Sin archivo de configuración, el sistema usa por defecto `[ConsoleOutput::class]`.

### Salida propia: el patrón que convierte las evaluaciones en herramienta de negocio

```php
namespace App\Neuron\Evaluations;

use NeuronAI\Evaluation\Contracts\EvaluationOutputInterface;
use NeuronAI\Evaluation\Runner\EvaluatorSummary;

class DatabaseOutput implements EvaluationOutputInterface
{
    public function __construct(
        private readonly \PDO $pdo,
        private readonly string $table = 'evaluations'
    ) {}

    public function output(EvaluatorSummary $summary): void
    {
        $stmt = $this->pdo->prepare(
            "INSERT INTO {$this->table} (passed, failed, success_rate, total_time, created_at, updated_at)
             VALUES (?, ?, ?, ?, NOW(), NOW())"
        );

        $stmt->execute([
            $summary->getPassedCount(),
            $summary->getFailedCount(),
            $summary->getSuccessRate(),
            $summary->getTotalExecutionTime(),
        ]);
    }
}
```

Regístralo:

```php
return [
    'output' => [
        ConsoleOutput::class,
        new DatabaseOutput(new \PDO(/* ... */), 'evaluations'),
    ],
];
```

**Por qué esto importa más allá de la ingeniería.** Persistir la tasa de éxito en cada ejecución te da una métrica de calidad a lo largo del tiempo. Puedes graficarla. Puedes enseñársela a un responsable. Puedes responder a «¿el cambio de prompt de la semana pasada mejoró o empeoró las cosas?» con un número en lugar de una opinión.

Esa es la transición de las evaluaciones como comodidad del desarrollador a las evaluaciones como evidencia. Para cualquiera que venda trabajo de IA a una empresa, es la diferencia entre «confía en mí» y un gráfico.

### Ejecución en paralelo

La mayor parte del tiempo de evaluación se pasa esperando al proveedor. Ejecuta los elementos concurrentemente:

```bash
vendor/bin/neuron evaluation path/to/evaluators --concurrency=3
```

El ejemplo documentado: una llamada al LLM de 2 segundos por elemento en un conjunto de datos de 100 elementos baja de unos 200 segundos a unos 66.

**Requisitos** — el mismo par que en la Sección 5.13:

```bash
composer require --dev spatie/fork
```

más `pcntl` (Linux y macOS; no Windows). Si falta alguno, el comando imprime un aviso y recae en secuencial, así que el mismo comando funciona en todas partes.

**Elegir un nivel.** Cada elemento en vuelo es una petición activa al proveedor. Empieza en 3–5 y sube mientras evites los límites de tasa. Los errores de límite de tasa aparecen como fallos de prueba, así que si aparecen fallos al subir la concurrencia, bájala antes de ponerte a cazar un error en tu agente.

### Cuatro cosas que saber sobre las ejecuciones en paralelo

**Los resultados no se ven afectados.** Los elementos son independientes, el orden se preserva, el informe es idéntico.

**El estado no se comparte.** Cada elemento ve el estado tal como estaba en `setUp()`. Los efectos colaterales de un elemento son invisibles para los demás. Si tu evaluador acumula estado entre elementos, ejecútalo secuencialmente.

**Las salidas deben ser serializables.** El valor de retorno de `run()` cruza una frontera de proceso mediante `serialize()`. Una función anónima o una conexión abierta no pueden cruzar; los resultados de los asertos sobreviven, pero la salida reportada se convierte en un marcador de posición.

**Los tiempos se leen raro.** El tiempo total es tiempo de reloj; la media por prueba es la duración real por elemento. Bajo paralelismo la media puede superar total ÷ número. Espéralo en lugar de abrir un informe de error.

### En CI

```yaml
- name: Run evaluations
  run: vendor/bin/neuron evaluation --path=evaluators
  env:
    ANTHROPIC_KEY: ${{ secrets.ANTHROPIC_KEY }}
```

Tres consejos prácticos:

**No subordines cada PR a la suite completa.** Cuesta dinero y es lenta. Ejecuta un pequeño conjunto de humo en las PR y la suite completa cada noche.

**No hagas fallar la build por un solo elemento.** Fija un umbral de tasa de éxito. Un 95 % de aprobados en un sistema probabilístico es una build sana, no una rota, y tratar un elemento inestable como fallo le enseña a tu equipo a ignorar la señal.

**Mantén las claves de API fuera de los forks.** Las ejecuciones de evaluación cuestan dinero real; un repositorio público con evaluaciones en las PR es una forma de donar tu presupuesto a desconocidos.

### Puntos clave

- Verifica el comando de evaluación contra `vendor/bin/neuron list` antes que nada.
- Varios drivers de salida se ejecutan a la vez; un driver de base de datos convierte las evaluaciones en una tendencia.
- `--concurrency` necesita `spatie/fork` y `pcntl`, y degrada con elegancia sin ellos.
- En CI: conjunto de humo en las PR, suite completa cada noche, umbral en lugar de todo o nada.

## Laboratorio 7 — Una suite de pruebas determinista

**Cubre:** todo lo de este capítulo, más el argumento de testabilidad de la Sección 5.3.

### Objetivo

Una suite de PHPUnit sobre un agente que **no haga ninguna llamada de red**. Se ejecuta en CI, se ejecuta sin conexión, se ejecuta en milisegundos y falla por razones reales en lugar de por inestabilidad.

Este es el complemento de las evaluaciones, no un sustituto. Las evaluaciones miden la calidad contra un modelo en vivo. Esta suite demuestra que tu cableado es correcto sin ninguno.

### Qué testear sin un modelo

Trabaja hacia fuera desde el núcleo determinista:

1. **Clases herramienta, invocadas directamente.** `(new WeatherTool())(45.07, 7.69)`: sin agente, sin proveedor. Simula el cliente HTTP. Aquí vive la mayor parte de tu lógica y toda ella es PHP corriente.
2. **DTOs de salida y reglas de validación.** Pasa un array escrito a mano por tu validación y haz asertos sobre qué violaciones aparecen. Una regla propia de la Sección 6.5 merece su propia prueba.
3. **Comprobaciones entre campos.** La comprobación aritmética de facturas del Laboratorio 6 es PHP puro. Testéala con un `Invoice` deliberadamente incoherente.
4. **Visibilidad de herramientas.** Construye el agente con un usuario administrador y con uno no administrador y haz asertos sobre la lista de herramientas resultante. Es una prueba de control de acceso, y pertenece a tu suite por la misma razón que tus pruebas de middleware de rutas.
5. **Gestores de errores.** Invoca `resolveToolErrorHandler()` con una `ConnectException` y comprueba que la cadena devuelta contiene la instrucción de reintento. La Sección 5.11 argumentaba que la instrucción es estructural; así es como impides que alguien la borre.

### El proveedor falso

NeuronAI incluye componentes falsos precisamente para que la CI pueda ser determinista y gratuita. Usa un proveedor falso para guionizar el lado del modelo en la conversación —una llamada a herramienta preparada seguida de un mensaje final preparado— y comprueba que tus herramientas se invocaron con los argumentos que esperabas.

El objetivo es la inversión: en lugar de preguntar «¿se comportó correctamente el modelo?», preguntas «dado que el modelo se comportó así, ¿hizo *mi* código lo correcto?». La segunda pregunta tiene respuesta correcta.

### Requisitos

- Cero llamadas de red. Imponlo: si tu suite pasa con la máquina sin conexión, lo has conseguido. Si no, encuentra la llamada.
- Todos las pruebas deterministas. Ejecuta la suite cincuenta veces en bucle; un solo fallo significa que se coló algo no determinista.
- Lo bastante rápida como para ejecutarse en cada guardado.

### Criterios de aceptación

- `phpunit` pasa sin `.env`, sin claves de API y sin internet.
- Borrar la instrucción de reintento de tu gestor de errores hace fallar una prueba.
- Quitar una condición `visible()` hace fallar una prueba.
- La suite se ejecuta en menos de dos segundos.

### Después, y por separado

Conecta la suite de evaluaciones de las Secciones 10.4–10.6 a un trabajo **nocturno**, no al mismo. Mantén las dos claramente separadas en tu cabeza y en tu configuración de CI:

| | Suite de pruebas | Suite de evaluaciones |
|---|---|---|
| Pregunta | ¿Es correcto mi código? | ¿Es buena la salida? |
| Necesita un modelo | No | Sí |
| Determinista | Sí | No |
| Coste | Gratis | Dinero real |
| Se ejecuta | En cada commit | Cada noche |
| Falla por | Cualquier fallo | Tasa de éxito por debajo del umbral |

Confundirlas es como los equipos acaban con un pipeline de CI caro, lento e inestable, y luego aprenden a ignorarlo.

## Ejercicios del capítulo

1. **Traza una rotura.** Habilita Inspector en un agente del Capítulo 5, rompe la descripción de una herramienta y lee la traza. Anota cuál de las cuatro preguntas de la Sección 10.3 reveló el problema.
2. **Construye un evaluador** con cinco entradas reales y al menos un aserto `StringSimilarity`.
3. **Añade un aserto `FaithfulnessJudge`.** Importará en el Capítulo 11, y tenerlo listo antes significa que podrás medir tu sistema RAG desde el primer día en lugar de añadir la medición a posteriori.
4. **Escribe un driver de salida propio** que añada líneas a un CSV, y ejecuta la suite tres veces para producir una tendencia.
5. **Cronometra la suite** secuencialmente y con `--concurrency=5`. Si la ganancia es menor de lo que esperabas, comprueba si estás chocando con límites de tasa.

::: {.callout .callout-tip}
[Fin de la Parte II]{.callout-title}

Ya tienes un agente que usa herramientas, recuerda conversaciones, devuelve datos tipados, transmite, lee documentos, se conecta a servidores de herramientas externos y puede trazarse y medirse. Eso es un sistema completo, y todo lo de las Partes III a V está construido sobre él, no al lado.

Veintiuno de los cuarenta y cuatro puntos del Apéndice A están en el material que acabas de recorrer. Si aún no has ejecutado los scripts de sondeo, este es el momento natural: la parte siguiente construye sobre todo ello.
:::
