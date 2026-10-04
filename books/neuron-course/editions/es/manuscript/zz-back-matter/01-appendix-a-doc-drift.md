# Apéndice A — Dónde la documentación se desvía del código {.unnumbered}

Ciento tres lugares donde el material oficial de NeuronAI —el sitio de documentación, los README, las guías de actualización y las skills para agentes— contradice al código, se contradice a sí mismo, contiene una errata o muestra una API de una versión anterior, o donde el código hace algo que su propio material no te cuenta. Sesenta y seis siguen abiertos en neuron-ai 4.0.2 y neuron-laravel 2.0.0, las versiones sobre las que se verificó este libro. Diez de ellos no son en absoluto problemas de documentación, sino defectos del código, cuatro en la biblioteca y seis en el SDK de Laravel, encontrados al verificar este libro. Cada punto abierto produce un error, o un resultado incorrecto, para quien copia la página.

Esto no es una queja sobre el proyecto. La deriva de la documentación es lo que ocurre cuando una biblioteca se mueve deprisa y el material que la rodea arrastra ejemplos escritos contra cuatro versiones mayores. Sí es, en cambio, un coste real para ti, y una tarde dedicada a resolverlos contra tu versión instalada es la preparación de mayor valor que puedes hacer antes de escribir código de producción.

## Cómo leer la tabla

Cada punto lleva su estado frente a neuron-ai 4.0.2 y neuron-laravel 2.0.0. Los números son fijos, porque los capítulos los citan: un punto que ya no se aplica conserva su número y dice qué fue de él.

- **Abierto**: sigue mal en el material que encontrarás, o sigue en el código.
- **Resuelto**: el código responde la pregunta; el punto dice cuál es la respuesta.
- **Corregido**: estaba mal, y la versión publicada lo corrigió; solo lo encontrarás en una instalación más antigua.
- **Obsoleto**: lo que describía no existe en la 4.0.2; solo lo encontrarás en material antiguo.

Los puntos del 1 al 44 se refieren a material anterior a la v4 que sigue en línea y se sigue copiando. Los puntos del 45 al 76 se refieren al propio material de la v4, y a los defectos que afloraron con él. Los puntos del 77 en adelante se refieren a la versión estable: lo que la 4.0.2 y el SDK 2.0.0 hacen y su propio material cuenta mal o calla. Cada grupo está ordenado por los capítulos a los que afecta.

Un límite. Un estado que describe una página del sitio de documentación es el que esa página tenía cuando se leyó, y el sitio cambia más deprisa que un libro. Trata esos puntos como cosas que comprobar con los sondeos de abajo, no como cosas que seguro siguen ahí.

## Algunos de estos ya están resueltos

El repositorio complementario fija cada API que usa este libro contra una versión conocida, y ejecutar su conjunto de pruebas te dice cuáles de los puntos de abajo siguen abiertos en *tu* instalación:

```bash
git clone https://github.com/hidran/neuronai-php-book.git
cd neuronai-php-book && composer install && composer check
```

Este libro se verificó contra **neuron-ai 4.0.2** y **neuron-laravel 2.0.0**, sobre PHP 8.5 y Laravel 13; el colofón recoge la tabla completa. Cada estado de abajo se estableció contra esos dos paquetes, leyendo su código fuente o ejecutando un sondeo contra ellos.

## Cómo resolverlos rápido

En lugar de comprobar ciento tres puntos de uno en uno, ejecuta un sondeo por área. Cada uno resuelve un grupo entero.

### Preparación

```bash
mkdir neuron-verify && cd neuron-verify
composer require neuron-core/neuron-ai
composer show neuron-core/neuron-ai
vendor/bin/neuron --help
```

Anota la versión exacta. Todo lo que sigue es relativo a ella. Los puntos sobre el SDK de Laravel necesitan una aplicación que tenga instalado también `neuron-core/neuron-laravel`.

### Sondeo 1 — Namespaces y nombres de clase

```bash
grep -rn "class Agent\b"        vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class SystemPrompt\b" vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class ApprovalRequest" vendor/neuron-core/neuron-ai/src/
grep -rln "EmbeddingsProvider\|EmbeddingProvider" vendor/neuron-core/neuron-ai/src/RAG/ | head
grep -rn "class .*Adapter\b" vendor/neuron-core/neuron-ai/src/Agent/Adapters/ | head
grep -rn "class ToolRunsExceeded\|class ToolMaxTries" vendor/neuron-core/neuron-ai/src/
grep -rn "class .*Toolkit\b" vendor/neuron-core/neuron-ai/src/Tools/Toolkits/
ls vendor/neuron-core/neuron-ai/src/Chat/History/
ls -d vendor/neuron-core/neuron-ai/src/*/Observability/
```

Resuelve los puntos **1, 4–5, 9, 24–25, 34, 39, 54, 76, 84**.

### Sondeo 2 — Firmas de métodos

```bash
grep -rn "function instructions"      vendor/neuron-core/neuron-ai/src/Agent/
grep -rn "function approvalPolicy"    vendor/neuron-core/neuron-ai/src/Tools/Tool.php
grep -rn -B3 "function toolErrorHandler" vendor/neuron-core/neuron-ai/src/Agent/
grep -n -A3 "function __construct"    vendor/neuron-core/neuron-ai/src/Workflow/Workflow.php
grep -n "function run\|function events\|function submitInputs\|function inspect\|function acknowledge\|function abandon" \
     vendor/neuron-core/neuron-ai/src/Workflow/Workflow.php
grep -n -A5 "public static function" \
     vendor/neuron-core/neuron-ai/src/Workflow/Executor/ExecutionRequest.php
grep -n "must have"                   vendor/neuron-core/neuron-ai/src/Workflow/NodeSignature.php
grep -rn "function delete\|function search" \
     vendor/neuron-core/neuron-ai/src/RAG/VectorStore/VectorStoreInterface.php
grep -n -A6 "function __construct"    vendor/neuron-core/neuron-ai/src/RAG/VectorStore/FileVectorStore.php
```

Resuelve los puntos **8, 22–23, 30–31, 36–37, 45–46, 58, 63, 67, 77**.

### Sondeo 3 — Lee las guías incluidas en el paquete

```bash
ls vendor/neuron-core/neuron-ai/upgrade/
find vendor/neuron-core/neuron-ai/src -name AGENTS.md
ls vendor/neuron-core/neuron-ai/skills/
grep -rnE "make\(threadId:|setChatHistory\(|->resume\(|approvalPolicy\(array" \
     vendor/neuron-core/neuron-ai/skills \
     vendor/neuron-core/neuron-laravel/resources/boost/skills 2>/dev/null
```

Las guías de actualización, los archivos `AGENTS.md` de cada módulo y las skills se distribuyen con el código, así que describen la versión que instalaste. Son la prosa más fiable que publica el proyecto, y ni siquiera ellas son perfectas (puntos 54, 66, 93, 102 y 103). El último comando busca cuatro grafías de la API que la 4.0.2 eliminó. Contra la 4.0.2, las skills del paquete principal responden con dos líneas, una de ellas un método que define la propia aplicación. Contra neuron-laravel 2.0.0, las copias para Boost responden con veinticinco (punto 100).

### Sondeo 4 — Un script mínimo por capacidad

Escribe y ejecuta seis scripts breves. Cada uno lleva minutos y resuelve un grupo de forma definitiva:

| Script | Resuelve |
|---|---|
| Agente + `chat()` + `getMessage()`, una vez con un hilo vinculado y otra sin él | 8, 9, 77–78 |
| Clase de herramienta + juego de herramientas con `only()`, y una herramienta sujeta a aprobación | 1–3, 45–46 |
| `structured()` con un DTO validado, al que se envía a propósito un valor incorrecto y después una clave ausente | 12–15, 49–50, 82 |
| Recorre `stream()`, imprime los `TextChunk` y luego `getReturn()` | 38, 53 |
| Flujo de trabajo mínimo de 3 nodos, después una interrupción, `submitInputs($answer)->run()` en un segundo proceso, y un `run()` más cuando ya ha terminado | 30–32, 34–37, 67, 90–91 |
| RAG con un `DocumentSchema` y una búsqueda filtrada | 26, 43, 58–60 |

**Esto es más rápido y más fiable que leer el código fuente**, porque también detecta comportamientos que las firmas no revelan.

## Los puntos

### Herramientas — Capítulo 5

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 1 | `ToolRunsExceededException` en la prosa frente a `ToolMaxTriesException` en el ejemplo de catch | **Resuelto.** Solo existe `NeuronAI\Exceptions\ToolRunsExceededException` |
| 2 | `setMaxRuns()` frente a `setMaxTries()`: secciones distintas usan nombres distintos | **Abierto.** `setMaxRuns()` (herramienta) y `toolMaxRuns()` (agente) son los correctos; el ejemplo de `with()` sigue llamando a `setMaxTries(1)`, sobre un `MySQLToolkit` al que no se le pasa ningún PDO |
| 3 | `ExponentiateTool` en el código de `provide()` frente a `ExponentialTool` en la tabla de herramientas | **Obsoleto.** La calculadora se reescribió en torno a `EvaluateTool`; no existe ninguna de las dos clases |
| 4 | `Toolkits\CalendarToolkit\CalendarToolkit` frente a `Toolkits\Calendar\...` | **Resuelto.** `NeuronAI\Tools\Toolkits\Calendar\` |
| 5 | `NeuronAI\Tools\Calculator\CalculatorToolkit` frente a `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit` | **Resuelto.** El segundo |
| 6 | `ProviderTool:make()`: dos puntos simples, errata por `::` | **Resuelto.** Corregido en la documentación de la v4 |
| 7 | `new SesCleint(...)`: errata por `SesClient` | **Abierto.** La herramienta que documenta esa página, `SESTool`, está obsoleta en la 4.0.2 y desaparecerá en la próxima versión mayor |
| 8 | `instructions()` mostrado tanto `public` como `protected` | **Resuelto.** `protected`, con retorno `SystemMessage\|string`; un retorno `string` simple sigue siendo válido |
| 9 | `use NeuronAI\Agent;` (v2) frente a `use NeuronAI\Agent\Agent;` en los ejemplos de juegos de herramientas | **Abierto.** Dos de las skills que se distribuyen con la 4.0.2 también imprimen la forma de la v2 (punto 102) |

### Mensajes y multimodalidad — Capítulos 4 y 8

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 10 | Se importa `AudioContent` pero se instancia `FileContent` | **Abierto.** |
| 11 | `TextBlock` / `FileBlock` frente a `TextContent` / `FileContent` | **Abierto.** Las clases son `TextContent` / `FileContent` |

### Salida estructurada — Capítulo 6

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 12 | `NeuronAI\StructuredOutput\Property` debería ser `SchemaProperty` | **Abierto.** |
| 13 | Imports del validador de Symfony en lugar de `NeuronAI\StructuredOutput\Validation\Rules\` | **Abierto.** |
| 14 | El ejemplo de `#[OutOfRange]` importa `InRange` | **Abierto.** No existe ninguna regla `InRange` |
| 15 | Regla propia: aridad incoherente de `respectFormat()`; `$this->pattern` frente a `$this->format` | **Abierto.** |

### Observabilidad y evaluaciones — Capítulo 10

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 16 | Tres nombres de observer: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` | **Resuelto, con un cuarto nombre.** La v4 emite eventos PSR-14; el oyente es `Inspector\Neuron\V4\InspectorSubscriber`, en `inspector-apm/inspector-php` `^3.19`, y hay que suscribirlo explícitamente. Las versiones de la 3.18.1 a la 3.18.3 traen un subscriber escrito para un namespace previo a la versión estable, que no registra nada; la guía de actualización 46 imprime una comprobación de una línea para el archivo instalado |
| 17 | `make:evaluator` frente a `make:evaluators` entre las pestañas de Unix y Windows | **Resuelto.** `make:evaluators`; el singular da "Unknown command" |
| 18 | `evaluations --path=X` frente a `evaluation X --concurrency=N` | **Resuelto.** `neuron evaluation`, en singular; funcionan tanto `--path=<dir>` como un `<dir>` posicional; `--concurrency=N` necesita `pcntl` y `spatie/fork` |
| 19 | `ConsoleDriver` frente a `ConsoleOutputDriver` | **Resuelto.** Ninguno de los dos: `ConsoleOutput` y `JsonOutput`, en `NeuronAI\Evaluation\Output` |
| 20 | `autoload-dev` mapea `App\Evaluators\` pero el generador usa `App\Neuron\Evaluators\` | **Abierto, y peor.** El generador lee solo `autoload`, nunca `autoload-dev`, así que los evaluadores generados siempre acaban en rutas de producción |
| 21 | Errata `new Antrhopic(...)`; confirma que existan `setAiProvider()` / `setInstructions()` | **Resuelto.** Ambos métodos existen en `AgentInterface`; la errata sigue ahí |

### RAG — Capítulos 11 y 12

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 22 | `FileVectorStore` mostrado de tres formas: `(directory, name)`, `(directory, topK)`, `(directory, key)` | **Resuelto.** `(directory, topK = 4, name = 'neuron', ext = '.store', schema = null)` |
| 23 | `FileVectoreStore`: nombre de clase con errata (una `e` de más) | **Abierto.** |
| 24 | `OpenAIEmbeddingsProvider` frente a `OpenAIEmbeddingProvider` | **Resuelto.** `OpenAIEmbeddingsProvider`, con la `s`; `model:` es obligatorio |
| 25 | Namespace `RAG\Embeddings\` frente a `RAG\EmbeddingProvider\` | **Resuelto.** `NeuronAI\RAG\Embeddings\` |
| 26 | `withFilters()` (Pinecone) frente a `withFilter()` (Elasticsearch) | **Obsoleto.** Han desaparecido los dos; los filtros se declaran en un `DocumentSchema` y se aplican mediante `retrievalScope()` |
| 27 | Revisa de nuevo la denominación de `CalculatorToolkit` junto al punto 3 | **Obsoleto.** Véase el punto 3 |
| 28 | Punto y coma sobrante: `FileDataLoader::for(...);` seguido de `->addReader(...)` | **Abierto.** |
| 29 | Confirma el constructor de `Document` y el accesor de contenido antes de publicar un divisor propio | **Resuelto.** `Document` es `final`; un divisor propio debe copiar `sourceType`, `sourceName` y los metadatos en cada fragmento, o la reindexación no podrá encontrarlo |

### Flujos de trabajo — Capítulos 13 a 16

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 30 | **`init()`/`run()` frente a `start()`/`getResult()`**: dos API de ejecución en páginas contiguas | **Resuelto, con una tercera API.** La v2 usaba `start()`/`getResult()`, la v3 `init()`/`run()`; la v4 no tiene ningún gestor: `$workflow->run()`, o `events()` para transmitir, cada uno con un `ExecutionRequest` opcional |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')`: constructor de la v2, todavía en entradas de blog | **Resuelto.** En la v4 es `Workflow::make(workflowId: ..., state: ...)`; la persistencia pasa por `setPersistence()` |
| 32 | Clase `Edge` y `addEdges()`: eliminados en la v2, todavía en material de la v1 | **Abierto.** Solo en material antiguo |
| 33 | `BrancheA1Event`: errata en el ejemplo de ramificación | **Abierto.** |
| 34 | `ApprovalRequest` importado desde `NeuronAI\Workflow\Interrupt` | **Abierto.** La clase es `NeuronAI\Agent\Interrupt\ApprovalRequest` |
| 35 | El ejemplo de petición propia sobrescribe `jsonSerialize()`, usa un `$this->note` no definido y omite `use DateTimeImmutable` | **Abierto.** `jsonSerialize()` es `final` en `InterruptRequest`; sobrescribe `metadata()` en su lugar |
| 36 | `Workflow::make(runId: ...)` y `getRunId()` usados como identificador para reanudar | **Abierto.** El constructor no tiene ningún argumento `runId` y el flujo de trabajo no tiene `getRunId()`. El identificador es el ID del flujo de trabajo. El ID de ejecución es una barrera: léelo del estado o de `inspect()` y devuélvelo junto con el intento de ejecución. `ExecutionRequest::start(runId: ...)` reserva uno |
| 37 | Confirma la firma de inyección de `CustomState` en el flujo de trabajo | **Resuelto.** `Workflow::make(state: new CustomState())`, o un hook `state()` más `@extends Workflow<CustomState>` |
| 38 | Confirma el nombre del método accesor de transmisión del gestor | **Resuelto.** No hay gestor: `events()` devuelve un generador, y `getReturn()` sobre él da el estado final |

### SDK de Laravel — Capítulos 17 a 23

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 39 | `use NeuronAI\Agent;` / `use NeuronAI\SystemPrompt;`: namespaces de la v2 en el README | **Abierto.** |
| 40 | `new SystemPrompt(...config('neuron.system_prompt');`: falta el paréntesis de cierre | **Abierto.** |
| 41 | `$workflow = WorkflowAgent(persistence: ...)`: falta `new` | **Obsoleto.** El ejemplo ya no está en el README de la 2.0.0 |
| 42 | `ElquentChatHistory` con errata en la prosa; ancla del documento `#eloquentchathisotry` | **Abierto.** Los dos siguen en el README de la 2.0.0, en una sección sobre una clase que la 4.0.2 eliminó (puntos 68 y 79) |
| 43 | Confirma `withFilters()` frente a `withFilter()` en el almacén que devuelve `VectorStore::driver()` | **Obsoleto.** Véase el punto 26 |
| 44 | Confirma qué drivers de almacén vectorial expone `config/neuron.php` | **Resuelto.** `file`, `pinecone`, `qdrant`, `meilisearch`, `chroma` |

### Material de la v4 — herramientas (Capítulo 5)

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 45 | `approvalPolicy(array $inputs)` en la documentación y en las skills de Laravel Boost. El método no recibe parámetros: las entradas ya están vinculadas; lee `$this->inputs` o `$this->getInput('amount')`. Copiar la firma documentada produce una sobrescritura incompatible, es decir, un error fatal | **Abierto.** Las skills que se distribuyen con neuron-ai 4.0.2 imprimen la firma correcta; las tres copias para Boost de neuron-laravel 2.0.0 no (punto 100) |
| 46 | La función de `toolErrorHandler()` tipada como `fn (Throwable $e, ToolInterface $tool)`. El segundo argumento es un `ToolCall`; el tipo documentado provoca un `TypeError` la primera vez que una herramienta lanza una excepción | **Abierto.** Las skills y los archivos `AGENTS.md` incluidos en el paquete imprimen `ToolCall` |
| 47 | La tabla de juegos de herramientas presenta `FileSystemToolkit` como lectura, búsqueda y análisis. También incluye herramientas de escritura, edición, borrado y bash, lo que importa para lo que le pasas a `only()` | **Abierto.** Ocho herramientas en la 4.0.2. `FileSystemToolkit::make($scope)` confina a un directorio las herramientas de archivos, no el shell |
| 48 | La lista de herramientas de proveedor omite ZAI, y el respaldo de las llamadas a herramientas en paralelo se describe como exclusivo de Windows. También se recurre a él sin `spatie/fork`, y para una sola llamada | **Abierto.** |

### Material de la v4 — salida estructurada (Capítulo 6)

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 49 | Las reglas de comparación —`GreaterThan`, `GreaterThanEqual`, `LowerThan`, `LowerThanEqual`, `EqualTo`, `NotEqualTo` y `OutOfRange`— construían su mensaje de infracción sin el nombre del campo y con el *tipo* de la referencia en lugar de su valor; `LowerThan` y `LowerThanEqual` además decían "greater than". Ese mensaje es lo que el reintento envía al modelo: un reembolso de 900 € volvía como *"must be greater than int"*. Un defecto del código | **Corregido.** La 4.0.2 nombra el campo y el valor: *"amount must be less than or equal to 500"* |
| 50 | `#[IpAddress]` en la documentación; la clase es `IPAddress`. Funciona en un sistema de archivos que no distingue mayúsculas de minúsculas y falla en producción en Linux | **Abierto.** |

### Material de la v4 — mensajes y transmisión (Capítulos 7 y 8)

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 51 | Los ejemplos multimodales pasan el contenido como `source:`. El parámetro es `content:` en todos los bloques de contenido | **Abierto.** |
| 52 | Se importa `NeuronAI\Chat\MediaType`; el enum es `NeuronAI\Chat\Enums\MediaType`. `SourceType` nunca se importa, y un ejemplo dice `UserMssage` | **Abierto.** |
| 53 | La página de transmisión sigue describiendo `StreamingNode`, `events()` sobre un gestor, el antiguo namespace `Chat\Messages\Stream\Adapters\` y el eliminado `SSEAdapter`, y hace echo de `$chunk->content` sin filtrar por `TextChunk`. Además nombra `NeuronAI\Agent\Adapter\AgentChunkAdapter` y `NeuronAI\Workflow\Channel\CallbackChannel`, ninguno de los cuales existe en esa ruta | **Abierto.** Las clases son `NeuronAI\Agent\Adapters\AgentChunkAdapter` y `NeuronAI\Workflow\Streaming\Channel\CallbackChannel` |
| 54 | La skill `neuron-streaming` enumera un `NativeAdapter`. La clase es `AgentChunkAdapter` | **Abierto.** Sigue en la skill que se distribuye con la 4.0.2 |

### Material de la v4 — observabilidad y evaluaciones (Capítulo 10)

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 55 | La skill `neuron-monitoring` dice que `neuron-core/cloud-sdk`, `neuron-cloud-laravel` y `neuron-cloud-symfony` están disponibles en Packagist. En el momento de escribir esto, los tres devuelven 404 | **Abierto.** La skill que se distribuye con la 4.0.2 lo sigue diciendo |
| 56 | La plantilla del generador de evaluadores llamaba a `->getMessage()->getContent()` sin el operador null-safe, así que los evaluadores generados no pasaban PHPStan tal como salían | **Abierto, con otra forma.** La plantilla de la 4.0.2 deja comentados los cuerpos de los métodos: `getDataset()` y `run()` no devuelven nada, así que la clase generada sigue sin pasar PHPStan, y `neuron evaluation` se detiene en un `TypeError` hasta que los rellenas |
| 57 | El descubrimiento de evaluadores buscaba coincidencias con `^class`, así que un evaluador `final`, `readonly` o `abstract` se omitía en silencio: *"No evaluator classes found"* | **Corregido.** El descubrimiento lee cada archivo con el tokenizador de PHP; un evaluador `final class` se encuentra y se ejecuta |

### Material de la v4 — RAG (Capítulos 12 y 20)

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 58 | La página de almacenes vectoriales muestra `delete(FilterGroup $filters)`. La firma es `delete(FilterExpression $filters)` | **Abierto.** |
| 59 | La misma página encadena `Filter::gt(...)->lt(...)->eq(...)`. La cadena se ejecuta, porque `lt()` y `eq()` son factorías estáticas y PHP te deja llamarlas sobre una instancia, y conserva solo la última condición: las dos primeras se descartan sin una palabra. El encadenamiento empieza en `Filter::where()`, que devuelve `Criteria` | **Abierto.** |
| 60 | La documentación incluye PHPVector entre los almacenes de la v4. `neuron-core/php-vector` no tenía ninguna versión compatible con la v4 en el momento de escribir esto | **Abierto.** |
| 61 | La skill `neuron-rag` llama a `$this->resolveProvider()`, que no existe. El método es `getProvider()` | **Corregido** en la skill que se distribuye con neuron-ai 4.0.2. La copia para Boost de neuron-laravel 2.0.0 lo sigue teniendo (punto 100) |
| 62 | `setRetrievalScope()` *reemplaza* el hook `retrievalScope()` en lugar de sumarse a él, y descarta en silencio un filtro de inquilino (Sección 20.1) | **Resuelto.** Sigue reemplazando el hook, y ahora el paquete lo dice: "un setter explícito prevalece sobre su hook" (`src/RAG/AGENTS.md`, guía de actualización 19) |

### Material de la v4 — flujos de trabajo (Capítulos 13 a 16, 22)

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 63 | La página "Loops & Branches" da a cada nodo un tercer parámetro `WorkflowResources $resources`. Antes de la versión estable la clase no existía, y el `__invoke()` de un nodo debía recibir exactamente dos | **Corregido.** La 4.0.2 incluye `WorkflowResources`, y `__invoke()` recibe dos parámetros o tres |
| 64 | Las guías de actualización se contradecían entre sí: la guía 9 convertía el ID de ejecución en el identificador para continuar; la guía 14 volvía a convertir en identificador el ID del flujo de trabajo y relegaba el ID de ejecución a una marca por intento | **Obsoleto.** Las guías se reescribieron y renumeraron para la versión estable, y coinciden con el código: el ID del flujo de trabajo es el identificador, el ID de ejecución y el intento de ejecución son barreras |
| 65 | `AsyncBranchRunner`, que antes de la versión estable se llamaba `AsyncExecutor`, necesita `amphp/amp`, que el paquete incluye solo como dependencia de desarrollo y no en `suggest`. Sin ella, una bifurcación en paralelo falla con *"Call to undefined function Amp\async()"* | **Abierto.** |
| 66 | La skill `neuron-workflow` llama a `->setProvider()`. El método es `setAiProvider()` | **Abierto.** Sigue en la skill que se distribuye con la 4.0.2 |
| 67 | La página de humano en el circuito llama a `$workflow->resume([...])` y se detiene ahí. Antes de la versión estable `resume()` solo dejaba preparada la respuesta, y no pasaba nada hasta `->run()` o `->events()` | **Obsoleto.** `Workflow::resume()` no existe en la 4.0.2. Continúa con `submitInputs($answer)->run()` o con `run(ExecutionRequest::resume($answer))` |

### Material de la v4 — SDK de Laravel y guías de actualización (Capítulos 17 a 23)

| # | Problema | Estado en la 4.0.2 |
|---|---|---|
| 68 | El README de la 2.x sigue mostrando patrones de la v3: un middleware `ToolApproval`, `StreamingNode`, `->events()` sobre una transmisión, e Inspector activado solo con la variable de entorno | **Abierto, y más amplio.** El README de la 2.0.0 documenta además `EloquentChatHistory` y un hook `chatHistory()`, ambos eliminados en la 4.0.2 (punto 79) |
| 69 | El docblock de la facade `Neuron` no tiene ninguna entrada `middleware()`, así que tu IDE y PHPStan rechazan una llamada que la clase acepta | **Abierto.** Irrelevante mientras la facade lance una excepción (punto 94) |
| 70 | El `MonitoredAgent` de la guía de actualización 7 sobrescribía el constructor sin llamar a `parent::__construct()`, con lo que perdía el ID de hilo | **Obsoleto.** El ejemplo no está en las guías que se distribuyen con la 4.0.2 |
| 71 | El ejemplo de "los puntos de conexión de reanudación no cambian" de la guía 11 usaba el orden antiguo del constructor y un argumento `chat(payload:)` que no existe; la guía 13 seguía incluyendo un adaptador SSE | **Obsoleto.** Ninguno de los dos está en las guías que se distribuyen con la 4.0.2 |

## Defectos del código encontrados al verificar este libro

Estos no son problemas de documentación. Son comportamientos del código, cada uno reproducido por un script. Tres de los cinco están corregidos en la 4.0.2 y uno está obsoleto; siguen aquí para quien lea desde una instalación más antigua. Las pruebas de contrato del repositorio complementario fijan el que sigue abierto, de modo que el día que cambie lo dirá la build. Los defectos encontrados en la versión estable están en la sección siguiente.

| # | Defecto | Dónde muerde | Estado en la 4.0.2 |
|---|---|---|---|
| 72 | `RAG::reindexBySource()` agrupaba los documentos en un array indexado por nombre de fuente, así que PHP convertía un nombre puramente numérico como `"42"` en un entero y el filtro de borrado fallaba después la validación del esquema | Sección 20.2 | **Corregido.** La 4.0.2 vuelve a leer el nombre del documento; `"42"` funciona |
| 73 | `make:node` generaba PHP no válido (una barra invertida duplicada en `Workflow\\Events`), y `make:agent` importaba `NeuronAI\Providers\Anthropic`, que es un namespace, como si fuera la clase | Sección 3.3 | **Corregido** en la CLI del paquete principal. El `neuron:node` del SDK tiene un fallo propio (punto 95) |
| 74 | La comprobación de intento obsoleto lanza una simple `WorkflowException` (*"Stale continuation…"*), mientras que la de ejecución obsoleta lanza `StaleWorkflowRunException`, así que un `catch` escrito para la segunda nunca ve la primera | Sección 22.3 | **Abierto.** La Sección 22.3 se apoya en esa diferencia; `abandon()` presenta la misma división (punto 92) |
| 75 | `StdioTransport::connect()` escapaba los argumentos pero no el comando, así que una ruta de intérprete que contiene un espacio —la predeterminada con Laravel Herd en macOS— la partía el shell y el servidor MCP moría al instante | Sección 9.2 | **Corregido.** La 4.0.2 arranca el servidor sin shell, así que la ruta se pasa tal cual; la antigua solución con `escapeshellarg()` ahora falla con *"Failed to start the MCP server"* |
| 76 | Un `InMemoryChatHistory` construido sin ID de hilo se ligaba a una clave aleatoria `mem_…`, así que un hook `chatHistory()` que omitía el hilo hacía que `make(threadId: ...)` lanzara *"Conflicting thread identity"* | Secciones 4.3 y 7.5 | **Obsoleto.** Las clases de historial, el hook y el argumento `threadId:` han desaparecido (puntos 77 y 79) |

También conviene conocer dos huecos de tipado, porque hacen que código correcto falle en el análisis estático en lugar de en tiempo de ejecución: `subscribe()` tipa su oyente como `callable(object): void`, así que ningún oyente tipado a una clase de evento concreta pasa PHPStan en el nivel 8; y el generador transmitido está tipado como `Generator<int, object>`, que no satisface `SSEEncoder::encode()`. El repositorio complementario marca cada solución provisional con un comentario. Un tercer hueco está cerrado: `Agent::stream()` se declara `Generator`, así que un simple `foreach` sobre él no necesita ningún `assert`.

## Encontrados en la 4.0.2 y en el SDK 2.0.0

Cada punto de abajo está abierto en neuron-ai 4.0.2 y neuron-laravel 2.0.0. Cuando uno es un defecto del código y no una deriva del material, el punto lo dice. Los puntos que implican una base de datos se ejecutaron sobre SQLite.

### Identidad y memoria — Capítulos 3, 4 y 18

| # | Problema |
|---|---|
| 77 | Los listados más antiguos, el material previo a la versión estable y las skills para Boost del SDK pasan la conversación como `make(threadId: ...)`. El constructor es `(?string $workflowId, ?WorkflowState $state)`, así que la llamada falla con *"Unknown named parameter $threadId"*. Usa `make(workflowId: ...)`, `setThreadId()` o `for()` (Sección 4.3) |
| 78 | Un agente, un RAG o un flujo de trabajo sin un ID vinculado se niega a ejecutarse: *"This agent has no thread ID: bind one with setThreadId() first."*, o *"This workflow has no workflow ID: bind one with setWorkflowId() first."* El framework nunca inventa uno, así que todo `Agent::make()->chat(...)` de una línea del material antiguo falla. En un agente la excepción es una `AgentException`, que un `catch` escrito para los fallos del modelo se traga (Sección 26.14) |
| 79 | Un hook `chatHistory()` que se quedó en el código nunca se llama, y nada lo avisa: las clases eliminadas que nombra nunca se cargan, el agente responde, y la conversación queda en el almacén en memoria predeterminado con su ventana de 50.000 tokens. Los hooks son `messageStore()` y `contextWindow()`. `setChatHistory()`, en cambio, falla de forma evidente (Secciones 4.3 y 18.2) |
| 80 | Un almacén de mensajes se salta un mensaje cuyo ID ya tiene: `append()` es idempotente por contrato. Una prueba que encola dos veces la misma instancia de `AssistantMessage` en `FakeAIProvider` pierde por eso la segunda respuesta en silencio, y el turno siguiente lanza `ChatHistoryException: Invalid message sequence`. Construye un mensaje por cada respuesta preparada |
| 81 | Las skills `neuron-agent` y `neuron-tool-approval` dicen que el siguiente `chat()` sustituye a un turno fallido. Solo es así cuando el turno falló antes de que se guardara su pregunta. Tras un paso de herramienta, el siguiente `chat()` lanza `ChatHistoryException: Invalid message sequence`, hasta que un simple `run()` termina el turno fallido. La skill `neuron-laravel-integration` lo cuenta bien (Sección 18.4) |

### Salida estructurada — Capítulo 6

| # | Problema |
|---|---|
| 82 | Cuando los reintentos se agotan por una clave obligatoria ausente, o por un valor del tipo equivocado, `structured()` lanza `DeserializerException`, que extiende `NeuronException` y no es una `AgentException`. Un `catch (AgentException)` solo ve las infracciones de las reglas. Captura las dos (Secciones 6.4 y 26.14) |
| 83 | `#[ArrayOf(X::class)]` valida cada elemento con las reglas del propio elemento y después descarta lo que encontró: la infracción dice *"lines must be an array of OrderLine"* sea cual sea el elemento que incumplió la regla que fuera, y esa frase es todo lo que el reintento le dice al modelo. Sin `#[ArrayOf]`, las reglas de los elementos ni siquiera se ejecutan. Un defecto del código; la Sección 6.5 dice dónde poner la restricción en su lugar |

### Transmisión, MCP y observabilidad — Capítulos 7, 9 y 10

| # | Problema |
|---|---|
| 84 | Los eventos de observabilidad viven en `NeuronAI\Agent\Observability\`, `NeuronAI\Workflow\Observability\` y `NeuronAI\RAG\Observability\`. El material previo a la versión estable, incluida la skill `neuron-monitoring` para Boost del SDK, usa `NeuronAI\Observability\Events\`. `subscribe()` acepta cualquier cadena, así que un oyente sobre el nombre antiguo nunca se dispara y no hay ningún error (Sección 10.2) |
| 85 | El punto de conexión simple de la skill `neuron-frontend-integration` envía sus encabezados y después itera dentro de `try { ... } catch (Throwable) {}`. El generador es perezoso, así que un turno que el motor rechaza con `RunInFlightException` se lanza dentro de ese `try`: el navegador recibe un 200 y una transmisión vacía. Extrae el primer evento con `$events->valid()` antes del primer encabezado, como hacen las skills de Laravel y de Symfony (Secciones 7.5 y 21.4). La misma skill indica dos versiones del cliente AG-UI con el que se probó, la 1.0.x y la 0.0.59 |
| 86 | `McpConnector::tools()` lanza `ToolException` cuando el esquema de una herramienta del servidor usa `anyOf`, `oneOf`, `$ref` o una lista de tipos, y basta una herramienta así para que falle el descubrimiento de todo el servidor. Es la forma que los servidores Python construidos sobre FastMCP y Pydantic dan a un parámetro opcional. La 3.x simplificaba esas propiedades en silencio, así que el material antiguo se conecta sin comentarios. `only()` filtra antes de la conversión (Sección 9.1 y guía de actualización 50) |

### RAG — Capítulos 12 y 20

| # | Problema |
|---|---|
| 87 | `PdfReader` ejecuta `pdftotext` mediante `symfony/process`, y `HtmlReader` necesita `html2text/html2text`. El paquete no incluye ninguno de los dos ni en `require` ni en `suggest`, así que Composer no los instala con él. El docblock de `HtmlReader` promete además Markdown; devuelve texto plano (Sección 12.2) |
| 88 | `OpenAIEmbeddingsProvider` pide 1024 dimensiones si no le dices otra cosa, y el `config/neuron.php` del SDK fija el mismo número; `MariaDBVectorStore::setupTable()` crea `VECTOR(1536)` si no le dices otra cosa. Los dos valores predeterminados no coinciden: pasa el número a ambos lados (Sección 12.4) |

### Flujos de trabajo — Capítulos 13 a 16, 22 y 26

| # | Problema |
|---|---|
| 89 | `expiresAt` no rechaza una respuesta tardía. Una carga entregada después del plazo llega al nodo como cualquier otra; solo un `run(ExecutionRequest::resume())` sin entrada convierte una espera vencida en `null`. Un nodo que deba rechazar una respuesta tardía comprueba el reloj por su cuenta, dentro de `memoize()` (Sección 26.10) |
| 90 | Un ID del flujo de trabajo cuya ejecución terminó vuelve a estar libre: sus registros se eliminan, y el siguiente `run()`, simple o con el mismo ID de ejecución reservado, ejecuta el flujo de trabajo desde el principio. Un trabajo de inicio reentregado repite el trabajo. `retainCompletionUntilAcknowledged()` conserva el resultado y rechaza la reentrega con `RunInFlightException`, hasta que llamas a `acknowledge()` (Secciones 22.4 y 26.13) |
| 91 | Cuando no hay nada esperando, las tres formas de continuar fallan de tres maneras distintas. `submitInputs()` lanza `InputTranslationException`, que no es una `WorkflowException`. `run(ExecutionRequest::resume($payload))` lanza una simple `WorkflowException`, *"No run in flight"*. La misma llamada con `expectedRunId:` lanza `StaleWorkflowRunException`. Un gestor de excepciones tiene que mapear las tres (Sección 21.4) |
| 92 | `abandon()` repite la división del punto 74: un ID de ejecución obsoleto lanza `StaleWorkflowRunException`, un intento obsoleto una simple `WorkflowException`, *"Cannot abandon a different execution attempt."* Un defecto del código. Llamado con un ID de ejecución cuando nada ocupa el ID del flujo de trabajo, lanza también `StaleWorkflowRunException` donde un bucle de limpieza espera `false` (Sección 22.4) |
| 93 | Las guías incluidas en el paquete dicen que un nodo que alcanza sus esperas en un orden distinto "falla con `WorkflowException` en lugar de perder la respuesta". Es cierto para un `interruptIf()` cuya condición cambió. Con un simple `if` alrededor de `interrupt()` no se lanza nada: una espera se identifica por su posición, así que la respuesta va a la espera que ahora llega primero, y el nodo vuelve a detenerse en la pregunta que ya estaba respondida. Un defecto del código (Sección 15.5) |

### SDK de Laravel 2.0.0 — Capítulos 17 a 23

| # | Problema |
|---|---|
| 94 | La facade `Neuron` lanza una excepción en cada llamada. Construye `Agent::make()` y nunca vincula un hilo, así que `Neuron::chat()`, `Neuron::stream()` y `Neuron::structured()` acaban todos en *"This agent has no thread ID"*. Genera una clase de agente y vincúlala con `->for($threadId)`. Un defecto del SDK (Sección 17.4) |
| 95 | `php artisan neuron:node` genera `use NeuronAI\Workflow\StartEvent;` y `use NeuronAI\Workflow\StopEvent;`. Las clases viven en `NeuronAI\Workflow\Events\`. El archivo pasa `php -l`, y el flujo de trabajo que contiene el nodo falla la validación en su primera ejecución. Un defecto del SDK (Sección 17.3) |
| 96 | La migración `chat_messages` que se distribuye no tiene columna `message_id` y el modelo `ChatMessage` que se distribuye no la declara fillable, mientras que `EloquentMessageStore` identifica cada fila por ella. El mismo mensaje se guarda dos veces y vuelve con un ID distinto. Escribe tú la migración y el modelo. Un defecto del SDK (Sección 18.2) |
| 97 | `EloquentPersistence` sobre la tabla `workflow_store` que se distribuye falla. La tabla tiene una clave primaria compuesta y ningún `id`, así que las actualizaciones y los borrados del modelo van a `where "id" is null`: un flujo de trabajo muere en su primer paso con *"Stale execution attempt 1 cannot write…"*, y el turno terminado de un agente nunca se limpia, así que su siguiente `chat()` lanza `RunInFlightException`. Usa `DatabasePersistence` sobre esa tabla. Un defecto del SDK (Sección 18.4) |
| 98 | `AIProvider::driver()` y `EmbeddingProvider::driver()`, llamados sin argumento, lanzan un `TypeError` cuando `NEURON_AI_PROVIDER` o `NEURON_EMBEDDING_PROVIDER` no está definida: *"getDefaultDriver(): Return value must be of type string, null returned"*. La configuración no tiene valor de respaldo para ninguna de las dos, y el README nunca menciona la segunda. Un defecto del SDK (Sección 17.2) |
| 99 | `VectorStoreManager` no está registrado como singleton, a diferencia de los otros dos managers. Un driver añadido con `VectorStore::extend()` vive en una instancia que solo conserva la caché de la facade: resuelve el manager desde el contenedor, o vacía las instancias resueltas de la facade, y el driver resulta *"not supported"*. Registra el singleton en tu propio proveedor de servicios. Un defecto del SDK (Secciones 17.6 y 20.1) |
| 100 | Las skills para Boost incluidas en el SDK son copias hechas antes de la versión estable, y enseñan la API que esta eliminó: `make(threadId:)`, `setChatHistory()` y las clases `…ChatHistory`, `$workflow->resume()`, `abandonRun()`, `acknowledgeCompletion()`, `AsyncExecutor`, `NeuronAI\Observability\Events\`, `approvalPolicy(array $inputs)`, `resolveProvider()`, y una instancia de adaptador pasada a `setStreamAdapter()`, que ahora recibe una factoría. Instala en su lugar las skills que se distribuyen con neuron-ai (Secciones 17.7 y 27.3) |
| 101 | El SDK distribuye generadores y ningún comando de evaluación. `vendor/bin/neuron evaluation` se ejecuta fuera de la aplicación arrancada, así que un evaluador que toca una facade falla con *"A facade root has not been set."* La skill `neuron-laravel-integration` te hace escribir tú mismo `php artisan neuron:evaluate` (Sección 23.4) |

### Las skills incluidas en el paquete y el README — Capítulo 27

| # | Problema |
|---|---|
| 102 | Las skills que se distribuyen con la 4.0.2 están al día, no impecables. `neuron-workflow` imprime `use NeuronAI\Agent;` y `->setProvider()` (punto 66), habla de "el `StreamingNode` integrado", que no existe, y te dice que extiendas "la clase base abstracta `Event`", que es una interfaz. `neuron-evaluation` imprime `use NeuronAI\Agent;`. `neuron-test` sigue llamando a `$workflow->resume([...])->run()`. `neuron-streaming` enumera `NativeAdapter` (punto 54). Y `src/Tools/AGENTS.md` construye un `new DeferredTool(...)`; la clase es `FrontendTool` |
| 103 | El README dice que las skills instaladas son enlaces simbólicos, "así que se mantienen al día cada vez que Neuron se actualiza mediante Composer". La guía de actualización 0 dice que nada apunta dentro de `vendor/` y que Composer no refresca las copias instaladas. No se ha resuelto aquí; volver a ejecutar `npx skills add ./vendor/neuron-core/neuron-ai/skills -y` después de cada actualización es lo correcto en ambos casos (Sección 17.7) |

## Orden de prioridad

Si tienes tiempo limitado, estos siete son los que más importan porque aparecen en el código de mayor tráfico:

1. **#77 y #78** — la identidad. Nada se ejecuta sin un ID, y el argumento que el material antiguo usa para pasar uno ya no existe. Afectan a todos los capítulos.
2. **#30, #36 y #67** — la API de ejecución de flujos de trabajo y la forma de continuar una ejecución en pausa, ahora que `resume()` ya no existe. Afectan a toda la Parte IV.
3. **#79** — el hook `chatHistory()` muerto. El agente responde, no conserva nada duradero, y nada te avisa.
4. **del #94 al #97** — el SDK de Laravel. La facade lanza una excepción, y las tablas que se distribuyen no encajan con los almacenes.
5. **#45 y #46** — las firmas de la política de aprobación y del gestor de errores. La primera es un error fatal al cargar la clase; la segunda falla justo cuando una herramienta lanza una excepción, que es el único momento en que importa.
6. **#26 y #58–59** — los filtros. El método antiguo ha desaparecido, y la cadena documentada conserva en silencio solo su última condición.
7. **#16 y #84** — la observabilidad. No se traza nada hasta que suscribes el oyente, un oyente sobre un nombre de clase antiguo nunca se dispara, y nada te avisa de ninguna de las dos cosas.

## Correcciones ya aplicadas en este libro

Más allá de los puntos anteriores, cuatro cosas que el material anterior sobre este framework tiene mal se han corregido en el texto que acabas de leer, en lugar de simplemente señalarse:

**La API de transmisión, por partida doble.** `foreach ($agent->stream($msg) as $chunk) { echo $chunk; }` era la forma de la v2 e imprimía objetos; la v3 devolvía un gestor con `events()`. En la v4, `stream()` *vuelve a ser* el generador, pero produce *objetos* fragmento, y solo algunos de ellos son texto. La Sección 7.2 filtra por `TextChunk`, lee `getReturn()` para obtener el estado final y muestra las dos formas anteriores para que las reconozcas cuando las encuentres.

**Las pausas son resultados, no excepciones.** Los tutoriales sobre humano en el circuito escritos antes de la v4 capturan `WorkflowInterrupt`. No se lanza nada: `run()` retorna, y `$state->isInterrupted()` dice por qué. El Capítulo 15 está escrito en torno a esto desde la primera página.

**No existe un almacén pgvector.** Gran cantidad de material de terceros supone que existe, porque pgvector es omnipresente en el ecosistema Python. La lista completa de primera parte está en la Sección 12.5: Memory, File, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch y MongoDB Atlas, con PHPVector como paquete aparte a la espera de una versión para la v4. El Laboratorio 9 está construido sobre MariaDB, y el Capítulo 20 recomienda MariaDB 11.7+.

**`required: true` comprueba la presencia, no el contenido.** Una clave obligatoria omitida provoca una `DeserializerException` y dispara un reintento; una cadena vacía está presente, así que pasa. La Sección 6.4 empareja cada escalar obligatorio con `#[NotBlank]`, que es lo que detecta el valor vacío, y el punto 82 dice qué excepción te llega cuando los reintentos se agotan.
