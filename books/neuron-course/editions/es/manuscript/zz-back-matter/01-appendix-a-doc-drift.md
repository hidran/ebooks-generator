# Apéndice A — Dónde la documentación se desvía del código {.unnumbered}

Cuarenta y cuatro lugares donde la documentación oficial de NeuronAI se contradice a sí misma, contiene una errata o muestra una API de una versión mayor anterior. Cada uno de ellos produce un error para quien copia la página.

Esto no es una queja sobre el proyecto. La deriva de la documentación es lo que ocurre cuando una biblioteca se mueve deprisa y sus documentos arrastran ejemplos escritos contra tres versiones mayores. Sí es, en cambio, un coste real para ti, y una tarde dedicada a resolverlos contra tu versión instalada es la preparación de mayor valor que puedes hacer antes de escribir código de producción.

## Algunos de estos ya están resueltos

El repositorio complementario fija cada API que usa este libro contra una versión conocida, y ejecutar su conjunto de pruebas te dice cuáles de los puntos de abajo siguen abiertos en *tu* instalación:

```bash
git clone https://github.com/hidran/neuronai-php-book.git
cd neuronai-php-book && composer install && composer check
```

Verificados contra **neuron-ai 3.16.4**, los siguientes ya no son preguntas abiertas:

- **Punto 18** — el comando es `neuron evaluation`, en singular. No existe `evaluations`. Acepta tanto `--path=<dir>` como un argumento posicional `<dir>`; `--concurrency=N` existe de verdad pero necesita `pcntl` y `spatie/fork`.
- **Punto 19** — ninguno de los dos nombres es correcto. Las clases son `ConsoleOutput` y `JsonOutput`, en `NeuronAI\Evaluation\Output`.
- **Puntos 24 y 25** — es `OpenAIEmbeddingsProvider`, con la `s`, en `NeuronAI\RAG\Embeddings`.

Trata el resto como todavía merecedor de una comprobación.

## Cómo resolverlos rápido

En lugar de comprobar cuarenta y cuatro puntos de uno en uno, ejecuta un sondeo por área. Cada uno resuelve un grupo entero.

### Preparación

```bash
mkdir neuron-verify && cd neuron-verify
composer require neuron-core/neuron-ai
composer show neuron-core/neuron-ai
vendor/bin/neuron --help
```

Anota la versión exacta. Todo lo de abajo es relativo a ella.

### Sondeo 1 — Namespaces y nombres de clase

```bash
grep -rn "class Agent\b"        vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class SystemPrompt\b" vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class FileVectorStore" vendor/neuron-core/neuron-ai/src/
grep -rln "EmbeddingsProvider\|EmbeddingProvider" vendor/neuron-core/neuron-ai/src/RAG/ | head
grep -rn "class .*Observer\|class AgentMonitoring" vendor/ | head
```

Resuelve los puntos **1–9, 16, 22–25, 39**.

### Sondeo 2 — Firmas de métodos

```bash
grep -rn "function instructions"     vendor/neuron-core/neuron-ai/src/
grep -rn "function setMaxRuns\|function setMaxTries" vendor/neuron-core/neuron-ai/src/
grep -rn "function withFilter"       vendor/neuron-core/neuron-ai/src/RAG/
grep -rn "function init\|function start\|function run\|function getResult" \
     vendor/neuron-core/neuron-ai/src/Workflow/Workflow.php
grep -rn "class ToolRunsExceeded\|class ToolMaxTries" vendor/neuron-core/neuron-ai/src/
```

Resuelve los puntos **1, 2, 26, 30, 31, 37, 43**.

### Sondeo 3 — Un script mínimo por capacidad

Escribe y ejecuta cinco scripts breves. Cada uno lleva minutos y resuelve un grupo de forma definitiva:

| Script | Resuelve |
|---|---|
| Agent + `chat()` + `getMessage()` | 8, 9 |
| Clase herramienta + juego de herramientas con `only()` | 1–3 |
| `structured()` con un DTO validado | 12–15 |
| `stream()` → `events()` → objetos de fragmento | 38 |
| Flujo de trabajo mínimo de 3 nodos | 30, 31, 32 |

**Esto es más rápido y más fiable que leer el código fuente**, porque además caza comportamientos que las firmas no revelan.

## Los puntos

### Herramientas — Capítulo 5

| # | Problema |
|---|---|
| 1 | `ToolRunsExceededException` en la prosa frente a `ToolMaxTriesException` en el ejemplo de catch |
| 2 | `setMaxRuns()` frente a `setMaxTries()`: secciones distintas usan nombres distintos |
| 3 | `ExponentiateTool` en el código de `provide()` frente a `ExponentialTool` en la tabla de herramientas |
| 4 | `Toolkits\CalendarToolkit\CalendarToolkit` frente a `Toolkits\Calendar\...` |
| 5 | `NeuronAI\Tools\Calculator\CalculatorToolkit` frente a `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit` |
| 6 | `ProviderTool:make()`: dos puntos simples, errata por `::` |
| 7 | `new SesCleint(...)`: errata de `SesClient` |
| 8 | `instructions()` mostrado como `public` y como `protected` |
| 9 | `use NeuronAI\Agent;` (v2) frente a `use NeuronAI\Agent\Agent;` (v3) en los ejemplos de juegos de herramientas |

### Mensajes y multimodalidad — Capítulos 4 y 8

| # | Problema |
|---|---|
| 10 | Se importa `AudioContent` pero se instancia `FileContent` |
| 11 | `TextBlock` / `FileBlock` frente a `TextContent` / `FileContent` |

### Salida estructurada — Capítulo 6

| # | Problema |
|---|---|
| 12 | `NeuronAI\StructuredOutput\Property` debería ser `SchemaProperty` |
| 13 | Imports del validador de Symfony en lugar de `NeuronAI\StructuredOutput\Validation\Rules\` |
| 14 | El ejemplo de `#[OutOfRange]` importa `InRange` |
| 15 | Regla propia: aridad incoherente de `respectFormat()`; `$this->pattern` frente a `$this->format` |

### Observabilidad y evaluaciones — Capítulo 10

| # | Problema |
|---|---|
| 16 | Tres nombres de observer: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` |
| 17 | `make:evaluator` frente a `make:evaluators` entre las pestañas de Unix y Windows |
| 18 | `evaluations --path=X` frente a `evaluation X --concurrency=N`: **ejecuta `vendor/bin/neuron --help`** |
| 19 | `ConsoleDriver` frente a `ConsoleOutputDriver` |
| 20 | `autoload-dev` mapea `App\Evaluators\` pero el generador usa `App\Neuron\Evaluators\` |
| 21 | Errata `new Antrhopic(...)`; confirma que existan `setAiProvider()` / `setInstructions()` |

### RAG — Capítulos 11 y 12

| # | Problema |
|---|---|
| 22 | `FileVectorStore` mostrado de tres formas: `(directory, name)`, `(directory, topK)`, `(directory, key)` |
| 23 | `FileVectoreStore`: nombre de clase con errata (una `e` de más) |
| 24 | `OpenAIEmbeddingsProvider` frente a `OpenAIEmbeddingProvider` |
| 25 | Namespace `RAG\Embeddings\` frente a `RAG\EmbeddingProvider\` |
| 26 | `withFilters()` (Pinecone) frente a `withFilter()` (Elasticsearch) |
| 27 | Revisa de nuevo la denominación de `CalculatorToolkit` junto al punto 3 |
| 28 | Punto y coma sobrante: `FileDataLoader::for(...);` seguido de `->addReader(...)` |
| 29 | Confirma el constructor de `Document` y el accesor de contenido antes de publicar un divisor propio |

### Flujos de trabajo — Capítulos 13 a 16

| # | Problema |
|---|---|
| 30 | **`init()`/`run()` frente a `start()`/`getResult()`**: dos API de ejecución en páginas contiguas |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')`: constructor de la v2, todavía en entradas de blog |
| 32 | Clase `Edge` y `addEdges()`: eliminados en la v2, todavía en material de la v1 |
| 33 | `BrancheA1Event`: errata en el ejemplo de ramificación |
| 34 | Comas ausentes tras `message:` en varios ejemplos de `ApprovalRequest` |
| 35 | Punto y coma ausente tras `parent::__construct($message)` en `ContentReviewInterrupt` |
| 36 | `ContentReviewInterrupt` llamado con un segundo argumento posicional tras uno con nombre |
| 37 | Confirma la firma de inyección de `CustomState` en el flujo de trabajo |
| 38 | Confirma el nombre del método accesor de transmisión del gestor |

### SDK de Laravel — Capítulos 17 a 23

| # | Problema |
|---|---|
| 39 | `use NeuronAI\Agent;` / `use NeuronAI\SystemPrompt;`: namespaces de la v2 en el README |
| 40 | `new SystemPrompt(...config('neuron.system_prompt');`: falta el paréntesis de cierre |
| 41 | `$workflow = WorkflowAgent(persistence: ...)`: falta `new` |
| 42 | `ElquentChatHistory` con errata en la prosa; ancla del documento `#eloquentchathisotry` |
| 43 | Confirma `withFilters()` frente a `withFilter()` en el almacén que devuelve `VectorStore::driver()` |
| 44 | Confirma qué drivers de almacén vectorial expone `config/neuron.php` |

## Orden de prioridad

Si tienes tiempo limitado, estos seis son los que más importan porque aparecen en el código de mayor tráfico:

1. **#30** — la API de ejecución de flujos de trabajo. Afecta a toda la Parte IV.
2. **#22–25** — la denominación de `FileVectorStore` y del proveedor de incrustaciones. Afecta a toda la Parte III.
3. **#18** — el comando de evaluaciones. Tu primera ejecución falla si esto está mal.
4. **#1–2** — la excepción y los nombres de método de los límites de ejecución. Una clase incorrecta en un `catch` falla en silencio, que es la peor clase de fallo.
5. **#16** — el nombre de la clase observer. Bloquea el Capítulo 10 por completo.
6. **#8** — la visibilidad de `instructions()`. Aparece en todas las clases agente de este libro.

## Tres correcciones ya aplicadas en este libro

Más allá de las cuarenta y cuatro, tres defectos del material anterior sobre este framework se han corregido en el texto que acabas de leer, en lugar de simplemente señalarse:

**La API de transmisión de la v2.** `foreach ($agent->stream($msg) as $chunk) { echo $chunk; }` no funciona en la v3. `stream()` devuelve un gestor; `events()` produce *objetos* fragmento; el texto es `$chunk->content`. La Sección 7.2 usa la forma correcta en todo momento, y muestra la rota para que la reconozcas cuando la encuentres.

**No existe un almacén pgvector.** Gran cantidad de material de terceros supone que existe, porque pgvector es omnipresente en el ecosistema Python. La lista completa de primera parte está en la Sección 12.5: Memory, File, PHPVector, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch. El Laboratorio 9 está construido sobre PHPVector, y el Capítulo 20 recomienda MariaDB 11.7+.

**Ninguna v4 verificable.** La Sección 26.1 lo cubre por completo. La versión breve: ejecuta `composer show neuron-core/neuron-ai --all` y cree a eso en lugar de a cualquier documento, incluido este.
