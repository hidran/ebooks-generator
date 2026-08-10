# Appendice A — Dove la documentazione si discosta dal codice {.unnumbered}

Quarantaquattro punti in cui la documentazione ufficiale di NeuronAI contraddice sé stessa, contiene un refuso o mostra un'API di una major precedente. Ciascuno di essi produce un errore per chi copia la pagina.

Non è una lamentela sul progetto. La deriva della documentazione è ciò che succede quando una libreria si muove in fretta e i suoi documenti portano esempi scritti contro tre major diverse. È però un costo reale per te — e un pomeriggio passato a risolverli contro la tua versione installata è la preparazione di maggior valore che puoi fare prima di scrivere codice di produzione.

## Come risolverli in fretta

Invece di controllare quarantaquattro voci una alla volta, esegui una sonda per area. Ciascuna risolve un intero gruppo.

### Preparazione

```bash
mkdir neuron-verify && cd neuron-verify
composer require neuron-core/neuron-ai
composer show neuron-core/neuron-ai
vendor/bin/neuron list
```

Registra la versione esatta. Tutto ciò che segue è relativo a essa.

### Sonda 1 — namespace e nomi di classi

```bash
grep -rn "class Agent\b"        vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class SystemPrompt\b" vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class FileVectorStore" vendor/neuron-core/neuron-ai/src/
grep -rln "EmbeddingsProvider\|EmbeddingProvider" vendor/neuron-core/neuron-ai/src/RAG/ | head
grep -rn "class .*Observer\|class AgentMonitoring" vendor/ | head
```

Risolve le voci **1–9, 16, 22–25, 39**.

### Sonda 2 — firme dei metodi

```bash
grep -rn "function instructions"     vendor/neuron-core/neuron-ai/src/
grep -rn "function setMaxRuns\|function setMaxTries" vendor/neuron-core/neuron-ai/src/
grep -rn "function withFilter"       vendor/neuron-core/neuron-ai/src/RAG/
grep -rn "function init\|function start\|function run\|function getResult" \
     vendor/neuron-core/neuron-ai/src/Workflow/Workflow.php
grep -rn "class ToolRunsExceeded\|class ToolMaxTries" vendor/neuron-core/neuron-ai/src/
```

Risolve le voci **1, 2, 26, 30, 31, 37, 43**.

### Sonda 3 — uno script minimo per capacità

Scrivi ed esegui cinque brevi script. Ciascuno richiede pochi minuti e risolve un gruppo in modo definitivo:

| Script | Risolve |
|---|---|
| Agent + `chat()` + `getMessage()` | 8, 9 |
| Classe tool + toolkit con `only()` | 1–3 |
| `structured()` con un DTO validato | 12–15 |
| `stream()` → `events()` → oggetti chunk | 38 |
| Workflow minimo a 3 nodi | 30, 31, 32 |

**È più veloce e più affidabile che leggere il sorgente**, perché coglie anche comportamenti che le firme non rivelano.

## Le voci

### Tool — Capitolo 5

| # | Problema |
|---|---|
| 1 | `ToolRunsExceededException` nella prosa contro `ToolMaxTriesException` nell'esempio di catch |
| 2 | `setMaxRuns()` contro `setMaxTries()` — sezioni diverse usano nomi diversi |
| 3 | `ExponentiateTool` nel sorgente di `provide()` contro `ExponentialTool` nella tabella dei tool |
| 4 | `Toolkits\CalendarToolkit\CalendarToolkit` contro `Toolkits\Calendar\...` |
| 5 | `NeuronAI\Tools\Calculator\CalculatorToolkit` contro `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit` |
| 6 | `ProviderTool:make()` — due punti singoli, refuso per `::` |
| 7 | `new SesCleint(...)` — refuso per `SesClient` |
| 8 | `instructions()` mostrato sia `public` sia `protected` |
| 9 | `use NeuronAI\Agent;` (v2) contro `use NeuronAI\Agent\Agent;` (v3) negli esempi dei toolkit |

### Messaggi e multimodalità — Capitoli 4 e 8

| # | Problema |
|---|---|
| 10 | `AudioContent` importato ma viene istanziato `FileContent` |
| 11 | `TextBlock` / `FileBlock` contro `TextContent` / `FileContent` |

### Structured output — Capitolo 6

| # | Problema |
|---|---|
| 12 | `NeuronAI\StructuredOutput\Property` dovrebbe essere `SchemaProperty` |
| 13 | Import del validatore di Symfony invece di `NeuronAI\StructuredOutput\Validation\Rules\` |
| 14 | L'esempio di `#[OutOfRange]` importa `InRange` |
| 15 | Regola personalizzata: arità di `respectFormat()` non coerente; `$this->pattern` contro `$this->format` |

### Osservabilità ed eval — Capitolo 10

| # | Problema |
|---|---|
| 16 | Tre nomi di observer: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` |
| 17 | `make:evaluator` contro `make:evaluators` fra la scheda Unix e quella Windows |
| 18 | `evaluations --path=X` contro `evaluation X --concurrency=N` — **esegui `vendor/bin/neuron list`** |
| 19 | `ConsoleDriver` contro `ConsoleOutputDriver` |
| 20 | `autoload-dev` mappa `App\Evaluators\` ma il generatore usa `App\Neuron\Evaluators\` |
| 21 | Refuso `new Antrhopic(...)`; conferma che `setAiProvider()` / `setInstructions()` esistano |

### RAG — Capitoli 11 e 12

| # | Problema |
|---|---|
| 22 | `FileVectorStore` mostrato in tre modi: `(directory, name)`, `(directory, topK)`, `(directory, key)` |
| 23 | `FileVectoreStore` — nome di classe con refuso (una `e` in più) |
| 24 | `OpenAIEmbeddingsProvider` contro `OpenAIEmbeddingProvider` |
| 25 | Namespace `RAG\Embeddings\` contro `RAG\EmbeddingProvider\` |
| 26 | `withFilters()` (Pinecone) contro `withFilter()` (Elasticsearch) |
| 27 | Ricontrolla la denominazione di `CalculatorToolkit` insieme alla voce 3 |
| 28 | Punto e virgola di troppo: `FileDataLoader::for(...);` seguito da `->addReader(...)` |
| 29 | Conferma il costruttore di `Document` e l'accessore al contenuto prima di rilasciare uno splitter personalizzato |

### Workflow — Capitoli da 13 a 16

| # | Problema |
|---|---|
| 30 | **`init()`/`run()` contro `start()`/`getResult()`** — due API di esecuzione su pagine adiacenti della documentazione |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')` — costruttore v2, ancora presente nei post dei blog |
| 32 | Classe `Edge` e `addEdges()` — rimossi in v2, ancora nel materiale v1 |
| 33 | `BrancheA1Event` — refuso nell'esempio di diramazione |
| 34 | Virgole mancanti dopo `message:` in diversi esempi di `ApprovalRequest` |
| 35 | Punto e virgola mancante dopo `parent::__construct($message)` in `ContentReviewInterrupt` |
| 36 | `ContentReviewInterrupt` chiamato con un secondo argomento posizionale dopo un primo con nome |
| 37 | Conferma la firma di iniezione di `CustomState` sul workflow |
| 38 | Conferma il nome del metodo accessore di streaming sull'handler |

### SDK per Laravel — Capitoli da 17 a 23

| # | Problema |
|---|---|
| 39 | `use NeuronAI\Agent;` / `use NeuronAI\SystemPrompt;` — namespace v2 nel README |
| 40 | `new SystemPrompt(...config('neuron.system_prompt');` — parentesi di chiusura mancante |
| 41 | `$workflow = WorkflowAgent(persistence: ...)` — manca `new` |
| 42 | `ElquentChatHistory` con refuso nella prosa; ancora del documento `#eloquentchathisotry` |
| 43 | Conferma `withFilters()` contro `withFilter()` sullo store restituito da `VectorStore::driver()` |
| 44 | Conferma quali driver di vector store espone `config/neuron.php` |

## Ordine di priorità

Se hai poco tempo, queste sei contano di più perché compaiono nel codice a più alto traffico:

1. **#30** — l'API di esecuzione dei workflow. Riguarda tutta la Parte IV.
2. **#22–25** — la denominazione di `FileVectorStore` e del provider di embedding. Riguarda tutta la Parte III.
3. **#18** — il comando delle eval. La tua prima esecuzione di eval fallisce se questo è sbagliato.
4. **#1–2** — l'eccezione e i nomi dei metodi per i limiti di esecuzione. Una classe sbagliata nel `catch` fallisce silenziosamente, che è il peggior tipo di sbagliato.
5. **#16** — il nome della classe observer. Blocca interamente il Capitolo 10.
6. **#8** — la visibilità di `instructions()`. Compare in ogni classe agent di questo libro.

## Tre correzioni già applicate in questo libro

Oltre alle quarantaquattro, tre difetti presenti nel materiale precedente su questo framework sono stati corretti nel testo che hai appena letto, invece che semplicemente segnalati:

**L'API di streaming della v2.** `foreach ($agent->stream($msg) as $chunk) { echo $chunk; }` non funziona in v3. `stream()` restituisce un handler; `events()` produce *oggetti* chunk; il testo è `$chunk->content`. La Sezione 7.2 usa la forma corretta ovunque, e mostra quella rotta così che tu la riconosca quando la incontri.

**Non esiste uno store pgvector.** Una gran quantità di materiale di terze parti presume che esista, perché pgvector è onnipresente nell'ecosistema Python. L'elenco completo di prima parte è nella Sezione 12.5: Memory, File, PHPVector, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch. Il Laboratorio 9 è costruito su PHPVector, e il Capitolo 20 raccomanda MariaDB 11.7+.

**Nessuna v4 verificabile.** La Sezione 26.1 lo copre per intero. La versione breve: esegui `composer show neuron-core/neuron-ai --all` e credi a quello invece che a qualunque documento, incluso questo.
