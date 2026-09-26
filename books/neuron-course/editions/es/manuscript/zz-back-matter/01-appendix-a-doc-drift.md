# Apéndice A — Dónde la documentación se desvía del código {.unnumbered}

Setenta y seis lugares donde el material oficial de NeuronAI —el sitio de documentación, los README, las guías de actualización y las skills para agentes— contradice al código, se contradice a sí mismo, contiene una errata o muestra una API de una versión mayor anterior. Seis de ellos —el punto 49 y los puntos del 72 al 76— no son en absoluto problemas de documentación, sino defectos del código, encontrados al verificar este libro. Cada uno de ellos produce un error, o un resultado incorrecto, para quien copia la página.

Esto no es una queja sobre el proyecto. La deriva de la documentación es lo que ocurre cuando una biblioteca se mueve deprisa y sus documentos arrastran ejemplos escritos contra cuatro versiones mayores; la reescritura del motor de flujos de trabajo en la v4 la hizo inevitable. Sí es, en cambio, un coste real para ti, y una tarde dedicada a resolverlos contra tu versión instalada es la preparación de mayor valor que puedes hacer antes de escribir código de producción.

## Cómo leer la tabla

Los puntos del 1 al 44 se catalogaron contra la v3. Sus números no cambian, porque los capítulos los citan, y cada uno lleva ahora su **estado en la v4**:

- **Abierto**: sigue mal en el material que encontrarás.
- **Resuelto**: el código responde la pregunta; el punto dice cuál es la respuesta.
- **Obsoleto**: lo que describía ya no existe en la v4.

Los puntos del 45 en adelante son nuevos en la v4.

## Algunos de estos ya están resueltos

El repositorio complementario fija cada API que usa este libro contra una versión conocida, y ejecutar su conjunto de pruebas te dice cuáles de los puntos de abajo siguen abiertos en *tu* instalación:

```bash
git clone https://github.com/hidran/neuronai-php-book.git
cd neuronai-php-book && composer install && composer check
```

Este libro se verificó contra la rama **neuron-ai 4.x** poco antes de la etiqueta 4.0.0, y contra **neuron-laravel 2.x**; el colofón registra los commits. Donde un estado de abajo dice *Resuelto*, es contra esas versiones contra las que se resolvió.

## Cómo resolverlos rápido

En lugar de comprobar setenta y seis puntos de uno en uno, ejecuta un sondeo por área. Cada uno resuelve un grupo entero.

### Preparación

```bash
mkdir neuron-verify && cd neuron-verify
composer require neuron-core/neuron-ai
composer show neuron-core/neuron-ai
vendor/bin/neuron --help
```

Anota la versión exacta. Todo lo que sigue es relativo a ella.

### Sondeo 1 — Namespaces y nombres de clase

```bash
grep -rn "class Agent\b"        vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class SystemPrompt\b" vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class ApprovalRequest" vendor/neuron-core/neuron-ai/src/
grep -rln "EmbeddingsProvider\|EmbeddingProvider" vendor/neuron-core/neuron-ai/src/RAG/ | head
grep -rn "class .*Adapter\b" vendor/neuron-core/neuron-ai/src/Agent/Adapters/ | head
grep -rn "class ToolRunsExceeded\|class ToolMaxTries" vendor/neuron-core/neuron-ai/src/
```

Resuelve los puntos **1, 4–5, 9, 22–25, 34, 39, 54**.

### Sondeo 2 — Firmas de métodos

```bash
grep -rn "function instructions"      vendor/neuron-core/neuron-ai/src/Agent/
grep -rn "function approvalPolicy"    vendor/neuron-core/neuron-ai/src/Tools/Tool.php
grep -rn "function toolErrorHandler"  vendor/neuron-core/neuron-ai/src/Agent/
grep -rn "function run\|function events\|function resume\|function __construct" \
     vendor/neuron-core/neuron-ai/src/Workflow/Workflow.php
grep -rn "function delete\|function search" \
     vendor/neuron-core/neuron-ai/src/RAG/VectorStore/VectorStoreInterface.php
```

Resuelve los puntos **8, 30–31, 36–37, 45–46, 58, 63**.

### Sondeo 3 — Lee las guías incluidas en el paquete

```bash
ls vendor/neuron-core/neuron-ai/upgrade/
find vendor/neuron-core/neuron-ai/src -name AGENTS.md
```

Las guías de actualización y los archivos `AGENTS.md` de cada módulo se distribuyen con el código, así que describen la versión que instalaste. Son la prosa más fiable que publica el proyecto, y ni siquiera ellas son perfectas (puntos 64, 70, 71).

### Sondeo 4 — Un script mínimo por capacidad

Escribe y ejecuta seis scripts breves. Cada uno lleva minutos y resuelve un grupo de forma definitiva:

| Script | Resuelve |
|---|---|
| Agente + `chat()` + `getMessage()` | 8, 9 |
| Clase de herramienta + juego de herramientas con `only()`, y una herramienta sujeta a aprobación | 1–3, 45–46 |
| `structured()` con un DTO validado, al que se envía un valor incorrecto a propósito | 12–15, 49–50 |
| Recorre `stream()`, imprime los `TextChunk` y luego `getReturn()` | 38, 53 |
| Flujo de trabajo mínimo de 3 nodos, y después una interrupción y una reanudación en un segundo proceso | 30–32, 34–37, 67 |
| RAG con un `DocumentSchema` y una búsqueda filtrada | 26, 43, 58–60 |

**Esto es más rápido y más fiable que leer el código fuente**, porque también detecta comportamientos que las firmas no revelan.

## Los puntos

### Herramientas — Capítulo 5

| # | Problema | Estado en la v4 |
|---|---|---|
| 1 | `ToolRunsExceededException` en la prosa frente a `ToolMaxTriesException` en el ejemplo de catch | **Resuelto.** Solo existe `NeuronAI\Exceptions\ToolRunsExceededException` |
| 2 | `setMaxRuns()` frente a `setMaxTries()`: secciones distintas usan nombres distintos | **Abierto.** `setMaxRuns()` (herramienta) y `toolMaxRuns()` (agente) son los correctos; el ejemplo de `with()` sigue llamando a `setMaxTries(1)`, sobre un `MySQLToolkit` al que no se le pasa ningún PDO |
| 3 | `ExponentiateTool` en el código de `provide()` frente a `ExponentialTool` en la tabla de herramientas | **Obsoleto.** La calculadora se reescribió en torno a `EvaluateTool`; no existe ninguna de las dos clases |
| 4 | `Toolkits\CalendarToolkit\CalendarToolkit` frente a `Toolkits\Calendar\...` | **Resuelto.** `NeuronAI\Tools\Toolkits\Calendar\` |
| 5 | `NeuronAI\Tools\Calculator\CalculatorToolkit` frente a `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit` | **Resuelto.** El segundo |
| 6 | `ProviderTool:make()`: dos puntos simples, errata por `::` | **Resuelto.** Corregido en la documentación de la v4 |
| 7 | `new SesCleint(...)`: errata por `SesClient` | Abierto |
| 8 | `instructions()` mostrado tanto `public` como `protected` | **Resuelto.** `protected`, con retorno `SystemMessage\|string`; un retorno `string` simple sigue siendo válido |
| 9 | `use NeuronAI\Agent;` (v2) frente a `use NeuronAI\Agent\Agent;` en los ejemplos de juegos de herramientas | Abierto |

### Mensajes y multimodalidad — Capítulos 4 y 8

| # | Problema | Estado en la v4 |
|---|---|---|
| 10 | Se importa `AudioContent` pero se instancia `FileContent` | Abierto |
| 11 | `TextBlock` / `FileBlock` frente a `TextContent` / `FileContent` | Abierto. Las clases son `TextContent` / `FileContent` |

### Salida estructurada — Capítulo 6

| # | Problema | Estado en la v4 |
|---|---|---|
| 12 | `NeuronAI\StructuredOutput\Property` debería ser `SchemaProperty` | Abierto |
| 13 | Imports del validador de Symfony en lugar de `NeuronAI\StructuredOutput\Validation\Rules\` | Abierto |
| 14 | El ejemplo de `#[OutOfRange]` importa `InRange` | Abierto |
| 15 | Regla propia: aridad incoherente de `respectFormat()`; `$this->pattern` frente a `$this->format` | Abierto |

### Observabilidad y evaluaciones — Capítulo 10

| # | Problema | Estado en la v4 |
|---|---|---|
| 16 | Tres nombres de observer: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` | **Resuelto, con un cuarto nombre.** La v4 usa eventos PSR-14; el oyente es `Inspector\Neuron\V4\InspectorSubscriber`, en `inspector-apm/inspector-php` 3.18.1 o posterior, y hay que suscribirlo explícitamente |
| 17 | `make:evaluator` frente a `make:evaluators` entre las pestañas de Unix y Windows | **Resuelto.** `make:evaluators`; el singular da "Unknown command" |
| 18 | `evaluations --path=X` frente a `evaluation X --concurrency=N` | **Resuelto.** `neuron evaluation`, en singular; funcionan tanto `--path=<dir>` como un `<dir>` posicional; `--concurrency=N` necesita `pcntl` y `spatie/fork` |
| 19 | `ConsoleDriver` frente a `ConsoleOutputDriver` | **Resuelto.** Ninguno de los dos: `ConsoleOutput` y `JsonOutput`, en `NeuronAI\Evaluation\Output` |
| 20 | `autoload-dev` mapea `App\Evaluators\` pero el generador usa `App\Neuron\Evaluators\` | **Abierto, y peor.** El generador lee solo `autoload`, nunca `autoload-dev`, así que los evaluadores generados siempre acaban en rutas de producción |
| 21 | Errata `new Antrhopic(...)`; confirma que existan `setAiProvider()` / `setInstructions()` | **Resuelto.** Ambos métodos existen en `AgentInterface`; la errata sigue ahí |

### RAG — Capítulos 11 y 12

| # | Problema | Estado en la v4 |
|---|---|---|
| 22 | `FileVectorStore` mostrado de tres formas: `(directory, name)`, `(directory, topK)`, `(directory, key)` | **Resuelto.** `(directory, topK = 4, name = 'neuron', ext = '.store', schema = null)` |
| 23 | `FileVectoreStore`: nombre de clase con errata (una `e` de más) | Abierto |
| 24 | `OpenAIEmbeddingsProvider` frente a `OpenAIEmbeddingProvider` | **Resuelto.** `OpenAIEmbeddingsProvider`, con la `s`; `model:` es obligatorio |
| 25 | Namespace `RAG\Embeddings\` frente a `RAG\EmbeddingProvider\` | **Resuelto.** `NeuronAI\RAG\Embeddings\` |
| 26 | `withFilters()` (Pinecone) frente a `withFilter()` (Elasticsearch) | **Obsoleto.** Han desaparecido los dos; los filtros se declaran en un `DocumentSchema` y se aplican mediante `retrievalScope()` |
| 27 | Revisa de nuevo la denominación de `CalculatorToolkit` junto al punto 3 | **Obsoleto.** Véase el punto 3 |
| 28 | Punto y coma sobrante: `FileDataLoader::for(...);` seguido de `->addReader(...)` | Abierto |
| 29 | Confirma el constructor de `Document` y el accesor de contenido antes de publicar un divisor propio | **Resuelto.** `Document` es `final`; un divisor propio debe copiar `sourceType`, `sourceName` y los metadatos en cada fragmento, o la reindexación no podrá encontrarlo |

### Flujos de trabajo — Capítulos 13 a 16

| # | Problema | Estado en la v4 |
|---|---|---|
| 30 | **`init()`/`run()` frente a `start()`/`getResult()`**: dos API de ejecución en páginas contiguas | **Resuelto, con una tercera API.** La v2 usaba `start()`/`getResult()`, la v3 `init()`/`run()`; la v4 no tiene ningún gestor: `$workflow->run()`, o `events()` para transmitir |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')`: constructor de la v2, todavía en entradas de blog | **Resuelto.** En la v4 es `Workflow::make(workflowId: ..., state: ...)`; la persistencia pasa por `setPersistence()` |
| 32 | Clase `Edge` y `addEdges()`: eliminados en la v2, todavía en material de la v1 | Abierto (en material antiguo) |
| 33 | `BrancheA1Event`: errata en el ejemplo de ramificación | Abierto |
| 34 | `ApprovalRequest` importado desde `NeuronAI\Workflow\Interrupt` | **Abierto.** La clase es `NeuronAI\Agent\Interrupt\ApprovalRequest` |
| 35 | El ejemplo de petición propia sobrescribe `jsonSerialize()`, usa un `$this->note` no definido y omite `use DateTimeImmutable` | **Abierto.** `jsonSerialize()` es `final` en `InterruptRequest`; sobrescribe `metadata()` en su lugar |
| 36 | `Workflow::make(runId: ...)` y `getRunId()` usados como identificador para reanudar | **Abierto.** No existe ningún argumento `runId` en el constructor; el identificador es el ID del flujo de trabajo, y el ID de ejecución es una barrera por intento (véase el punto 64) |
| 37 | Confirma la firma de inyección de `CustomState` en el flujo de trabajo | **Resuelto.** `Workflow::make(state: new CustomState())`, o un hook `state()` más `@extends Workflow<CustomState>` |
| 38 | Confirma el nombre del método accesor de transmisión del gestor | **Resuelto.** No hay gestor: `events()` devuelve un generador, y `getReturn()` sobre él da el estado final |

### SDK de Laravel — Capítulos 17 a 23

| # | Problema | Estado en la v4 |
|---|---|---|
| 39 | `use NeuronAI\Agent;` / `use NeuronAI\SystemPrompt;`: namespaces de la v2 en el README | Abierto |
| 40 | `new SystemPrompt(...config('neuron.system_prompt');`: falta el paréntesis de cierre | Abierto |
| 41 | `$workflow = WorkflowAgent(persistence: ...)`: falta `new` | **Obsoleto.** El ejemplo ya no está en el README de la 2.x |
| 42 | `ElquentChatHistory` con errata en la prosa; ancla del documento `#eloquentchathisotry` | Abierto |
| 43 | Confirma `withFilters()` frente a `withFilter()` en el almacén que devuelve `VectorStore::driver()` | **Obsoleto.** Véase el punto 26 |
| 44 | Confirma qué drivers de almacén vectorial expone `config/neuron.php` | **Resuelto.** `file`, `pinecone`, `qdrant`, `meilisearch`, `chroma` |

### Nuevo en la v4 — herramientas y mensajes (Capítulos 5, 7, 8)

| # | Problema |
|---|---|
| 45 | `approvalPolicy(array $inputs)` en la documentación y en las skills de Laravel Boost. El método no recibe parámetros: las entradas ya están vinculadas; lee `$this->inputs`. Copiar la firma documentada produce una sobrescritura incompatible, es decir, un error fatal |
| 46 | La función de `toolErrorHandler()` tipada como `fn (Throwable $e, ToolInterface $tool)`. El segundo argumento es un `ToolCall`; el tipo documentado provoca un `TypeError` la primera vez que una herramienta lanza una excepción |
| 47 | La tabla de juegos de herramientas presenta `FileSystemToolkit` como lectura, búsqueda y análisis. También incluye herramientas de escritura, edición, borrado y bash, lo que importa para lo que le pasas a `only()` |
| 48 | La lista de herramientas de proveedor omite ZAI, y el respaldo de las llamadas a herramientas en paralelo se describe como exclusivo de Windows. También se recurre a él sin `spatie/fork`, y para una sola llamada |
| 51 | Los ejemplos multimodales pasan el contenido como `source:`. El parámetro es `content:` en todos los bloques de contenido |
| 52 | Se importa `NeuronAI\Chat\MediaType`; el enum es `NeuronAI\Chat\Enums\MediaType`. `SourceType` nunca se importa, y un ejemplo dice `UserMssage` |
| 53 | La página de transmisión sigue describiendo `StreamingNode`, `events()` sobre un gestor, el antiguo namespace `Chat\Messages\Stream\Adapters\` y el eliminado `SSEAdapter`, y hace echo de `$chunk->content` sin filtrar por `TextChunk`. Además nombra `NeuronAI\Agent\Adapter\AgentChunkAdapter` y `NeuronAI\Workflow\Channel\CallbackChannel`, ninguno de los cuales existe en esa ruta |
| 54 | La skill `neuron-streaming` enumera un `NativeAdapter`. La clase es `AgentChunkAdapter` |

### Nuevo en la v4 — salida estructurada (Capítulo 6)

| # | Problema |
|---|---|
| 49 | Las reglas de comparación —`GreaterThan`, `GreaterThanEqual`, `LowerThan`, `LowerThanEqual`, `EqualTo`, `NotEqualTo` y `OutOfRange`— construyen su mensaje de infracción sin el nombre del campo y con el *tipo* de la referencia en lugar de su valor; `LowerThan` y `LowerThanEqual` además dicen "greater than". Ese mensaje es lo que el reintento envía al modelo: un reembolso de 900 € vuelve como *"must be greater than int"*. Es un defecto del código; la Sección 6.5 muestra cómo sortearlo |
| 50 | `#[IpAddress]` en la documentación; la clase es `IPAddress`. Funciona en un sistema de archivos que no distingue mayúsculas de minúsculas y falla en producción en Linux |

### Nuevo en la v4 — observabilidad y evaluaciones (Capítulo 10)

| # | Problema |
|---|---|
| 55 | La skill `neuron-monitoring` dice que `neuron-core/cloud-sdk`, `neuron-cloud-laravel` y `neuron-cloud-symfony` están disponibles en Packagist. En el momento de escribir esto, los tres devuelven 404 |
| 56 | La plantilla del generador de evaluadores sigue llamando a `->getMessage()->getContent()` sin el operador null-safe, así que los evaluadores generados no pasan PHPStan tal como salen |
| 57 | El descubrimiento de evaluadores busca coincidencias con `^class`, así que un evaluador `final`, `readonly` o `abstract` se omite en silencio: *"No evaluator classes found"* |

### Nuevo en la v4 — RAG (Capítulos 12 y 20)

| # | Problema |
|---|---|
| 58 | La página de almacenes vectoriales muestra `delete(FilterGroup $filters)`. La firma es `delete(FilterExpression $filters)` |
| 59 | La misma página encadena `Filter::gt(...)->lt(...)->eq(...)`. `Filter::gt()` devuelve un `Filter`, que no tiene `lt()`; el encadenamiento empieza en `Filter::where()`, que devuelve `Criteria` |
| 60 | La documentación incluye PHPVector entre los almacenes de la v4. `neuron-core/php-vector` no tenía ninguna versión compatible con la v4 en el momento de escribir esto |
| 61 | La skill `neuron-rag` llama a `$this->resolveProvider()`, que no existe. El método es `getProvider()` |
| 62 | `setRetrievalScope()` *reemplaza* el hook `retrievalScope()` en lugar de sumarse a él. No está documentado en ninguna parte, y descarta en silencio un filtro de inquilino (Sección 20.1) |

### Nuevo en la v4 — flujos de trabajo (Capítulos 13 a 16, 22)

| # | Problema |
|---|---|
| 63 | La página "Loops & Branches" da a cada nodo un tercer parámetro `WorkflowResources $resources`. La clase no existe, y el `__invoke()` de un nodo debe recibir exactamente dos |
| 64 | Las guías de actualización se contradicen entre sí: la guía 9 convierte el ID de ejecución en el identificador para continuar; la guía 14 vuelve a convertir en identificador el ID del flujo de trabajo y relega el ID de ejecución a una marca por intento. El código sigue la guía 14 |
| 65 | `AsyncExecutor` necesita `amphp/amp`, que el paquete incluye solo como dependencia de desarrollo y no en `suggest`. Sin ella, el ejecutor falla con *"Call to undefined function Amp\async()"* |
| 66 | La skill `neuron-workflow` llama a `->setProvider()`. El método es `setAiProvider()` |
| 67 | La página de humano en el circuito llama a `$workflow->resume([...])` y se detiene ahí. `resume()` solo deja preparada la respuesta; no pasa nada hasta `->run()` o `->events()` |

### Nuevo en la v4 — SDK de Laravel y guías de actualización (Capítulos 17 a 23)

| # | Problema |
|---|---|
| 68 | El README de la 2.x sigue mostrando patrones de la v3: un middleware `ToolApproval`, `StreamingNode`, `->events()` sobre una transmisión, e Inspector activado solo con la variable de entorno |
| 69 | El docblock de la facade `Neuron` no tiene ninguna entrada `middleware()`, así que la llamada funciona pero tu IDE y PHPStan dicen que no |
| 70 | El `MonitoredAgent` de la guía de actualización 7 sobrescribe el constructor sin llamar a `parent::__construct()`, con lo que pierde el ID de hilo |
| 71 | El ejemplo de "los puntos de conexión de reanudación no cambian" de la guía 11 usa el orden antiguo del constructor y un argumento `chat(payload:)` que no existe; la guía 13 sigue incluyendo un adaptador SSE |

## Defectos del código encontrados al verificar este libro

Estos no son problemas de documentación. Son comportamientos del código 4.x contra el que se verificó este libro, cada uno reproducido por un script en el repositorio complementario. Compruébalos contra tu versión; puede que algunos estén corregidos cuando leas esto.

| # | Defecto | Dónde muerde |
|---|---|---|
| 72 | `RAG::reindexBySource()` agrupa los documentos en un array indexado por nombre de fuente, así que PHP convierte un nombre puramente numérico como `"42"` en un entero y el filtro de borrado falla después la validación del esquema. Usa `article-42`, no `42` | Sección 20.2 |
| 73 | `make:node` genera PHP no válido (una barra invertida duplicada en `Workflow\\Events`), y `make:agent` importa `NeuronAI\Providers\Anthropic`, que es un namespace, como si fuera la clase | Sección 3.3 |
| 74 | La comprobación de intento obsoleto lanza una simple `WorkflowException`, mientras que la de ejecución obsoleta lanza `StaleWorkflowRunException`, así que un trabajo que solo captura esta última se pierde la mitad de las reentregas para las que se escribió | Sección 22.3 |
| 75 | `StdioTransport::connect()` escapa los argumentos pero no el comando, así que una ruta de intérprete que contiene un espacio —la predeterminada con Laravel Herd en macOS— la parte el shell y el servidor MCP muere al instante. Sin cambios respecto a la 3.x | Sección 9.2 |
| 76 | Un `InMemoryChatHistory` construido sin ID de hilo se liga a una clave aleatoria `mem_…` —a propósito, según el código fuente, pero a diferencia de todos los demás backends de historial, que quedan sin hilo—. Por eso, un hook `chatHistory()` que omite el hilo hace que `make(threadId: ...)` lance *"Conflicting thread identity"*. Pasa `threadId: $this->threadId` | Secciones 4.3 y 7.5 |

También conviene conocer tres huecos de tipado, porque hacen que código correcto falle en el análisis estático en lugar de en tiempo de ejecución: `subscribe()` tipa su oyente como `callable(object): void`, así que ningún oyente tipado a una clase de evento concreta pasa PHPStan en el nivel 8; `Agent::stream()` está tipado como `Generator|AgentState`, así que un simple `foreach` sobre él necesita un `assert`; y el generador transmitido está tipado como `Generator<int, object>`, que no satisface `SSEEncoder::encode()`. El repositorio complementario marca cada solución provisional con un comentario.

## Orden de prioridad

Si tienes tiempo limitado, estos siete son los que más importan porque aparecen en el código de mayor tráfico:

1. **#30 y #36** — la API de ejecución de flujos de trabajo y el identificador para reanudar. Afectan a toda la Parte IV.
2. **#45** — la firma de la política de aprobación. Copiarla es un error fatal en la primera herramienta sujeta a aprobación.
3. **#46** — la firma del gestor de errores. Falla justo cuando una herramienta lanza una excepción, que es el único momento en que importa.
4. **#26 y #58–59** — los filtros. El método antiguo ha desaparecido y los ejemplos nuevos no compilan.
5. **#16** — el oyente de observabilidad. No se traza nada hasta que lo suscribes, y nada te avisa.
6. **#49** — los mensajes de validación. Un reintento que no le dice al modelo nada útil es un reintento que pagas dos veces.
7. **#18** — el comando de evaluaciones. Tu primera ejecución falla si esto está mal.

## Correcciones ya aplicadas en este libro

Más allá de los puntos anteriores, cuatro cosas que el material anterior sobre este framework tiene mal se han corregido en el texto que acabas de leer, en lugar de simplemente señalarse:

**La API de transmisión, por partida doble.** `foreach ($agent->stream($msg) as $chunk) { echo $chunk; }` era la forma de la v2 e imprimía objetos; la v3 devolvía un gestor con `events()`. En la v4, `stream()` *vuelve a ser* el generador, pero produce *objetos* fragmento, y solo algunos de ellos son texto. La Sección 7.2 filtra por `TextChunk`, lee `getReturn()` para obtener el estado final y muestra las dos formas anteriores para que las reconozcas cuando las encuentres.

**Las pausas son resultados, no excepciones.** Todos los tutoriales de la v3 sobre humano en el circuito capturan `WorkflowInterrupt`. En la v4 no se lanza nada: `run()` retorna, y `$state->isInterrupted()` dice por qué. El Capítulo 15 está escrito en torno a esto desde la primera página.

**No existe un almacén pgvector.** Gran cantidad de material de terceros supone que existe, porque pgvector es omnipresente en el ecosistema Python. La lista completa de primera parte está en la Sección 12.5: Memory, File, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch y MongoDB Atlas, con PHPVector como paquete aparte a la espera de una versión para la v4. El Laboratorio 9 está construido sobre MariaDB, y el Capítulo 20 recomienda MariaDB 11.7+.

**`required: true` no valida.** Da forma al esquema que se envía al modelo y no se comprueba a la vuelta. La Sección 6.4 empareja cada escalar obligatorio con una regla, y eso es lo que hace que una clave omitida dispare un reintento en lugar de un error fatal.
