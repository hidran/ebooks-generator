# Appendice A — Dove la documentazione si discosta dal codice {.unnumbered}

Centotré punti in cui il materiale ufficiale di NeuronAI — il sito della documentazione, i README, le guide all'aggiornamento e le skill per agent — contraddice il codice, contraddice sé stesso, contiene un refuso o mostra un'API di una versione precedente, oppure in cui il codice fa qualcosa che il suo stesso materiale non ti dice. Sessantasei sono aperti su neuron-ai 4.0.2 e neuron-laravel 2.0.0, le versioni su cui questo libro è stato verificato. Dieci di questi non sono affatto problemi di documentazione, ma difetti del codice, quattro nella libreria e sei nell'SDK per Laravel, trovati durante la verifica di questo libro. Ogni punto aperto produce un errore, o un risultato sbagliato, per chi copia la pagina.

Non è una lamentela sul progetto. La deriva della documentazione è ciò che succede quando una libreria si muove in fretta e il materiale che la circonda porta esempi scritti contro quattro major diverse. È però un costo reale per te — e un pomeriggio passato a risolverli contro la tua versione installata è la preparazione di maggior valore che puoi fare prima di scrivere codice di produzione.

## Come leggere la tabella

Ogni punto riporta il suo stato rispetto a neuron-ai 4.0.2 e neuron-laravel 2.0.0. I numeri sono fissi, perché i capitoli li citano: un punto che non vale più conserva il suo numero e dice che fine ha fatto.

- **Aperto** — ancora sbagliato nel materiale che troverai, o ancora nel codice.
- **Risolto** — il codice risponde alla domanda; il punto dice qual è la risposta.
- **Corretto** — era sbagliato, e la release lo ha corretto; lo incontrerai solo su un'installazione più vecchia.
- **Obsoleto** — ciò che descriveva non esiste nella 4.0.2; lo incontrerai solo nel materiale più vecchio.

I punti dall'1 al 44 riguardano materiale precedente alla v4 ma ancora online e ancora copiato. I punti dal 45 al 76 riguardano il materiale della v4 stessa, e i difetti emersi insieme a esso. I punti dal 77 in poi riguardano la release stabile: ciò che la 4.0.2 e l'SDK 2.0.0 fanno e che il loro stesso materiale sbaglia o tace. Ogni gruppo è ordinato per i capitoli su cui incide.

Un limite. Uno stato che descrive una pagina del sito della documentazione è quello che la pagina aveva quando è stata letta, e il sito cambia più in fretta di un libro. Tratta quei punti come cose da controllare con le sonde qui sotto, non come cose che ci sono ancora di sicuro.

## Alcuni di questi sono già risolti

Il repository di accompagnamento fissa ogni API usata da questo libro contro una versione nota, e l'esecuzione della sua suite di test ti dice quali dei punti qui sotto sono ancora aperti sulla *tua* installazione:

```bash
git clone https://github.com/hidran/neuronai-php-book.git
cd neuronai-php-book && composer install && composer check
```

Questo libro è stato verificato contro **neuron-ai 4.0.2** e **neuron-laravel 2.0.0**, su PHP 8.5 e Laravel 13; il colophon riporta la tabella completa. Ogni stato qui sotto è stato stabilito contro questi due pacchetti, leggendone il sorgente o eseguendo una sonda contro di essi.

## Come risolverli in fretta

Invece di controllare centotré punti uno alla volta, esegui una sonda per area. Ciascuna risolve un intero gruppo.

### Preparazione

```bash
mkdir neuron-verify && cd neuron-verify
composer require neuron-core/neuron-ai
composer show neuron-core/neuron-ai
vendor/bin/neuron --help
```

Registra la versione esatta. Tutto ciò che segue è relativo a essa. I punti sull'SDK per Laravel richiedono un'applicazione in cui sia installato anche `neuron-core/neuron-laravel`.

### Sonda 1 — namespace e nomi di classi

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

Risolve i punti **1, 4–5, 9, 24–25, 34, 39, 54, 76, 84**.

### Sonda 2 — firme dei metodi

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

Risolve i punti **8, 22–23, 30–31, 36–37, 45–46, 58, 63, 67, 77**.

### Sonda 3 — leggi le guide incluse nel pacchetto

```bash
ls vendor/neuron-core/neuron-ai/upgrade/
find vendor/neuron-core/neuron-ai/src -name AGENTS.md
ls vendor/neuron-core/neuron-ai/skills/
grep -rnE "make\(threadId:|setChatHistory\(|->resume\(|approvalPolicy\(array" \
     vendor/neuron-core/neuron-ai/skills \
     vendor/neuron-core/neuron-laravel/resources/boost/skills 2>/dev/null
```

Le guide all'aggiornamento, i file `AGENTS.md` di ciascun modulo e le skill sono distribuiti con il codice, quindi descrivono la versione che hai installato. Sono la prosa più affidabile che il progetto pubblichi — e nemmeno loro sono perfette (punti 54, 66, 93, 102 e 103). L'ultimo comando cerca quattro grafie dell'API che la 4.0.2 ha rimosso. Contro la 4.0.2 le skill del pacchetto core rispondono con due righe, una delle quali è un metodo definito dall'applicazione stessa. Contro neuron-laravel 2.0.0 le copie per Boost rispondono con venticinque (punto 100).

### Sonda 4 — uno script minimo per capacità

Scrivi ed esegui sei brevi script. Ciascuno richiede pochi minuti e risolve un gruppo in modo definitivo:

| Script | Risolve |
|---|---|
| Agent + `chat()` + `getMessage()`, una volta con un thread associato e una volta senza | 8, 9, 77–78 |
| Classe tool + toolkit con `only()`, e un tool soggetto ad approvazione | 1–3, 45–46 |
| `structured()` con un DTO validato, a cui si manda di proposito un valore errato e poi una chiave mancante | 12–15, 49–50, 82 |
| Itera `stream()`, stampa i `TextChunk`, poi `getReturn()` | 38, 53 |
| Workflow minimo a 3 nodi, poi un'interruzione, `submitInputs($answer)->run()` in un secondo processo, e un altro `run()` una volta terminato | 30–32, 34–37, 67, 90–91 |
| RAG con un `DocumentSchema` e una ricerca filtrata | 26, 43, 58–60 |

**È più veloce e più affidabile che leggere il sorgente**, perché coglie anche comportamenti che le firme non rivelano.

## I punti

### Tool — Capitolo 5

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 1 | `ToolRunsExceededException` nella prosa contro `ToolMaxTriesException` nell'esempio di catch | **Risolto.** Esiste solo `NeuronAI\Exceptions\ToolRunsExceededException` |
| 2 | `setMaxRuns()` contro `setMaxTries()` — sezioni diverse usano nomi diversi | **Aperto.** `setMaxRuns()` (tool) e `toolMaxRuns()` (agent) sono corretti; l'esempio di `with()` chiama ancora `setMaxTries(1)`, su un `MySQLToolkit` a cui non viene passato alcun PDO |
| 3 | `ExponentiateTool` nel sorgente di `provide()` contro `ExponentialTool` nella tabella dei tool | **Obsoleto.** La calcolatrice è stata riscritta attorno a `EvaluateTool`; nessuna delle due classi esiste |
| 4 | `Toolkits\CalendarToolkit\CalendarToolkit` contro `Toolkits\Calendar\...` | **Risolto.** `NeuronAI\Tools\Toolkits\Calendar\` |
| 5 | `NeuronAI\Tools\Calculator\CalculatorToolkit` contro `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit` | **Risolto.** Il secondo |
| 6 | `ProviderTool:make()` — due punti singoli, refuso per `::` | **Risolto.** Corretto nella documentazione v4 |
| 7 | `new SesCleint(...)` — refuso per `SesClient` | **Aperto.** Il tool che quella pagina documenta, `SESTool`, è deprecato nella 4.0.2 e sparirà con la prossima major |
| 8 | `instructions()` mostrato sia `public` sia `protected` | **Risolto.** `protected`, con ritorno `SystemMessage\|string`; un ritorno `string` semplice è ancora lecito |
| 9 | `use NeuronAI\Agent;` (v2) contro `use NeuronAI\Agent\Agent;` negli esempi dei toolkit | **Aperto.** Anche due delle skill distribuite con la 4.0.2 stampano la forma v2 (punto 102) |

### Messaggi e multimodalità — Capitoli 4 e 8

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 10 | `AudioContent` importato ma viene istanziato `FileContent` | **Aperto.** |
| 11 | `TextBlock` / `FileBlock` contro `TextContent` / `FileContent` | **Aperto.** Le classi sono `TextContent` / `FileContent` |

### Structured output — Capitolo 6

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 12 | `NeuronAI\StructuredOutput\Property` dovrebbe essere `SchemaProperty` | **Aperto.** |
| 13 | Import del validatore di Symfony invece di `NeuronAI\StructuredOutput\Validation\Rules\` | **Aperto.** |
| 14 | L'esempio di `#[OutOfRange]` importa `InRange` | **Aperto.** Non esiste alcuna regola `InRange` |
| 15 | Regola personalizzata: arità di `respectFormat()` non coerente; `$this->pattern` contro `$this->format` | **Aperto.** |

### Osservabilità ed eval — Capitolo 10

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 16 | Tre nomi di observer: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` | **Risolto, con un quarto nome.** La v4 emette eventi PSR-14; il listener è `Inspector\Neuron\V4\InspectorSubscriber`, in `inspector-apm/inspector-php` `^3.19`, e va sottoscritto esplicitamente. Le release dalla 3.18.1 alla 3.18.3 contengono un subscriber scritto per un namespace di pre-release, che non registra nulla; la guida all'aggiornamento 46 stampa un controllo di una riga per il file installato |
| 17 | `make:evaluator` contro `make:evaluators` fra la scheda Unix e quella Windows | **Risolto.** `make:evaluators`; il singolare dà "Unknown command" |
| 18 | `evaluations --path=X` contro `evaluation X --concurrency=N` | **Risolto.** `neuron evaluation`, al singolare; funzionano sia `--path=<dir>` sia un `<dir>` posizionale; `--concurrency=N` richiede `pcntl` e `spatie/fork` |
| 19 | `ConsoleDriver` contro `ConsoleOutputDriver` | **Risolto.** Nessuno dei due: `ConsoleOutput` e `JsonOutput`, in `NeuronAI\Evaluation\Output` |
| 20 | `autoload-dev` mappa `App\Evaluators\` ma il generatore usa `App\Neuron\Evaluators\` | **Aperto, e peggiorato.** Il generatore legge solo `autoload`, mai `autoload-dev`, quindi gli evaluator generati finiscono sempre nei percorsi di produzione |
| 21 | Refuso `new Antrhopic(...)`; conferma che `setAiProvider()` / `setInstructions()` esistano | **Risolto.** Entrambi i metodi esistono su `AgentInterface`; il refuso resta |

### RAG — Capitoli 11 e 12

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 22 | `FileVectorStore` mostrato in tre modi: `(directory, name)`, `(directory, topK)`, `(directory, key)` | **Risolto.** `(directory, topK = 4, name = 'neuron', ext = '.store', schema = null)` |
| 23 | `FileVectoreStore` — nome di classe con refuso (una `e` in più) | **Aperto.** |
| 24 | `OpenAIEmbeddingsProvider` contro `OpenAIEmbeddingProvider` | **Risolto.** `OpenAIEmbeddingsProvider`, con la `s`; `model:` è obbligatorio |
| 25 | Namespace `RAG\Embeddings\` contro `RAG\EmbeddingProvider\` | **Risolto.** `NeuronAI\RAG\Embeddings\` |
| 26 | `withFilters()` (Pinecone) contro `withFilter()` (Elasticsearch) | **Obsoleto.** Sono spariti entrambi; i filtri si dichiarano in un `DocumentSchema` e si applicano tramite `retrievalScope()` |
| 27 | Ricontrolla la denominazione di `CalculatorToolkit` insieme al punto 3 | **Obsoleto.** Vedi il punto 3 |
| 28 | Punto e virgola di troppo: `FileDataLoader::for(...);` seguito da `->addReader(...)` | **Aperto.** |
| 29 | Conferma il costruttore di `Document` e l'accessore al contenuto prima di rilasciare uno splitter personalizzato | **Risolto.** `Document` è `final`; uno splitter personalizzato deve copiare `sourceType`, `sourceName` e i metadati su ogni chunk, altrimenti la reindicizzazione non riesce a trovarlo |

### Workflow — Capitoli da 13 a 16

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 30 | **`init()`/`run()` contro `start()`/`getResult()`** — due API di esecuzione su pagine adiacenti della documentazione | **Risolto, con una terza API.** La v2 usava `start()`/`getResult()`, la v3 `init()`/`run()`; la v4 non ha alcun handler: `$workflow->run()`, oppure `events()` per lo streaming, ciascuno con un `ExecutionRequest` opzionale |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')` — costruttore v2, ancora presente nei post dei blog | **Risolto.** In v4 è `Workflow::make(workflowId: ..., state: ...)`; la persistenza passa per `setPersistence()` |
| 32 | Classe `Edge` e `addEdges()` — rimossi in v2, ancora nel materiale v1 | **Aperto.** Solo nel materiale vecchio |
| 33 | `BrancheA1Event` — refuso nell'esempio di diramazione | **Aperto.** |
| 34 | `ApprovalRequest` importato da `NeuronAI\Workflow\Interrupt` | **Aperto.** La classe è `NeuronAI\Agent\Interrupt\ApprovalRequest` |
| 35 | L'esempio di richiesta personalizzata sovrascrive `jsonSerialize()`, usa un `$this->note` non definito e omette `use DateTimeImmutable` | **Aperto.** `jsonSerialize()` è `final` su `InterruptRequest`; sovrascrivi invece `metadata()` |
| 36 | `Workflow::make(runId: ...)` e `getRunId()` usati come handle per la ripresa | **Aperto.** Il costruttore non ha un argomento `runId` e il workflow non ha `getRunId()`. L'handle è il workflow ID. Il run ID è un fence: leggilo dallo stato o da `inspect()` e ripassalo insieme al tentativo di esecuzione. `ExecutionRequest::start(runId: ...)` ne riserva uno |
| 37 | Conferma la firma di iniezione di `CustomState` sul workflow | **Risolto.** `Workflow::make(state: new CustomState())`, oppure un hook `state()` più `@extends Workflow<CustomState>` |
| 38 | Conferma il nome del metodo accessore di streaming sull'handler | **Risolto.** Non c'è alcun handler: `events()` restituisce un generatore, e `getReturn()` su di esso fornisce lo stato finale |

### SDK per Laravel — Capitoli da 17 a 23

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 39 | `use NeuronAI\Agent;` / `use NeuronAI\SystemPrompt;` — namespace v2 nel README | **Aperto.** |
| 40 | `new SystemPrompt(...config('neuron.system_prompt');` — parentesi di chiusura mancante | **Aperto.** |
| 41 | `$workflow = WorkflowAgent(persistence: ...)` — manca `new` | **Obsoleto.** L'esempio non c'è più nel README della 2.0.0 |
| 42 | `ElquentChatHistory` con refuso nella prosa; ancora del documento `#eloquentchathisotry` | **Aperto.** Sono entrambi ancora nel README della 2.0.0, in una sezione su una classe che la 4.0.2 ha rimosso (punti 68 e 79) |
| 43 | Conferma `withFilters()` contro `withFilter()` sullo store restituito da `VectorStore::driver()` | **Obsoleto.** Vedi il punto 26 |
| 44 | Conferma quali driver di vector store espone `config/neuron.php` | **Risolto.** `file`, `pinecone`, `qdrant`, `meilisearch`, `chroma` |

### Materiale della v4 — tool (Capitolo 5)

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 45 | `approvalPolicy(array $inputs)` nella documentazione e nelle skill di Laravel Boost. Il metodo non accetta parametri — gli input sono già stati sottoposti a binding; leggi `$this->inputs` o `$this->getInput('amount')`. Copiare la firma documentata produce un override incompatibile, cioè un errore fatale | **Aperto.** Le skill distribuite con neuron-ai 4.0.2 stampano la firma corretta; le tre copie per Boost in neuron-laravel 2.0.0 no (punto 100) |
| 46 | La callback di `toolErrorHandler()` tipizzata come `fn (Throwable $e, ToolInterface $tool)`. Il secondo argomento è un `ToolCall`; il tipo documentato provoca un `TypeError` la prima volta che un tool lancia un'eccezione | **Aperto.** Le skill e i file `AGENTS.md` inclusi nel pacchetto stampano `ToolCall` |
| 47 | La tabella dei toolkit elenca `FileSystemToolkit` come lettura, ricerca e parsing. Distribuisce anche tool di scrittura, modifica, cancellazione e bash — il che conta per ciò che passi a `only()` | **Aperto.** Otto tool nella 4.0.2. `FileSystemToolkit::make($scope)` confina in una directory i tool sui file, non la shell |
| 48 | L'elenco dei tool dei provider omette ZAI, e il fallback delle chiamate ai tool in parallelo è descritto come solo per Windows. Il fallback scatta anche senza `spatie/fork`, e per una singola chiamata | **Aperto.** |

### Materiale della v4 — structured output (Capitolo 6)

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 49 | Le regole di confronto — `GreaterThan`, `GreaterThanEqual`, `LowerThan`, `LowerThanEqual`, `EqualTo`, `NotEqualTo` e `OutOfRange` — costruivano il messaggio di violazione senza il nome del campo e con il *tipo* del riferimento invece del suo valore; `LowerThan` e `LowerThanEqual` dicevano inoltre "greater than". Quel messaggio è ciò che il ritentativo invia al modello: un rimborso da 900 € tornava indietro come *"must be greater than int"*. Un difetto del codice | **Corretto.** La 4.0.2 nomina il campo e il valore: *"amount must be less than or equal to 500"* |
| 50 | `#[IpAddress]` nella documentazione; la classe è `IPAddress`. Funziona su un filesystem che non distingue maiuscole e minuscole, fallisce in produzione su Linux | **Aperto.** |

### Materiale della v4 — messaggi e streaming (Capitoli 7 e 8)

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 51 | Gli esempi multimodali passano il payload come `source:`. Il parametro è `content:` su ogni blocco di contenuto | **Aperto.** |
| 52 | Viene importato `NeuronAI\Chat\MediaType`; l'enum è `NeuronAI\Chat\Enums\MediaType`. `SourceType` non viene mai importato, e un esempio riporta `UserMssage` | **Aperto.** |
| 53 | La pagina sullo streaming descrive ancora `StreamingNode`, `events()` su un handler, il vecchio namespace `Chat\Messages\Stream\Adapters\` e il rimosso `SSEAdapter`, e stampa `$chunk->content` senza filtrare per `TextChunk`. Nomina inoltre `NeuronAI\Agent\Adapter\AgentChunkAdapter` e `NeuronAI\Workflow\Channel\CallbackChannel`, nessuno dei quali esiste a quel percorso | **Aperto.** Le classi sono `NeuronAI\Agent\Adapters\AgentChunkAdapter` e `NeuronAI\Workflow\Streaming\Channel\CallbackChannel` |
| 54 | La skill `neuron-streaming` elenca un `NativeAdapter`. La classe è `AgentChunkAdapter` | **Aperto.** È ancora nella skill distribuita con la 4.0.2 |

### Materiale della v4 — osservabilità ed eval (Capitolo 10)

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 55 | La skill `neuron-monitoring` dice che `neuron-core/cloud-sdk`, `neuron-cloud-laravel` e `neuron-cloud-symfony` sono disponibili su Packagist. Al momento della scrittura, tutti e tre restituiscono 404 | **Aperto.** La skill distribuita con la 4.0.2 lo dice ancora |
| 56 | Lo stub del generatore di evaluator chiamava `->getMessage()->getContent()` senza l'operatore null-safe, quindi gli evaluator generati non superavano PHPStan così come erano | **Aperto, in una forma nuova.** Lo stub della 4.0.2 mette sotto commento i corpi dei metodi: `getDataset()` e `run()` non restituiscono nulla, quindi la classe generata continua a non superare PHPStan, e `neuron evaluation` si ferma su un `TypeError` finché non li riempi |
| 57 | La ricerca degli evaluator faceva match su `^class`, quindi un evaluator `final`, `readonly` o `abstract` veniva saltato in silenzio — *"No evaluator classes found"* | **Corretto.** La ricerca legge ogni file con il tokenizer di PHP; un evaluator `final class` viene trovato ed eseguito |

### Materiale della v4 — RAG (Capitoli 12 e 20)

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 58 | La pagina sui vector store mostra `delete(FilterGroup $filters)`. La firma è `delete(FilterExpression $filters)` | **Aperto.** |
| 59 | La stessa pagina concatena `Filter::gt(...)->lt(...)->eq(...)`. La catena viene eseguita, perché `lt()` ed `eq()` sono factory statiche e PHP ti lascia chiamarle su un'istanza, e conserva solo l'ultima condizione: le prime due vengono scartate senza una parola. La concatenazione parte da `Filter::where()`, che restituisce `Criteria` | **Aperto.** |
| 60 | La documentazione elenca PHPVector fra gli store della v4. `neuron-core/php-vector` non aveva una release compatibile con la v4 al momento della scrittura | **Aperto.** |
| 61 | La skill `neuron-rag` chiama `$this->resolveProvider()`, che non esiste. Il metodo è `getProvider()` | **Corretto** nella skill distribuita con neuron-ai 4.0.2. La copia per Boost in neuron-laravel 2.0.0 ce l'ha ancora (punto 100) |
| 62 | `setRetrievalScope()` *sostituisce* l'hook `retrievalScope()` invece di aggiungersi a esso, e fa cadere in silenzio un filtro sul tenant — Sezione 20.1 | **Risolto.** Sostituisce ancora l'hook, e ora il pacchetto lo dice: "un setter esplicito prevale sul suo hook" (`src/RAG/AGENTS.md`, guida all'aggiornamento 19) |

### Materiale della v4 — workflow (Capitoli da 13 a 16, 22)

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 63 | La pagina "Loops & Branches" dà a ogni nodo un terzo parametro `WorkflowResources $resources`. Prima della release la classe non esisteva, e l'`__invoke()` di un nodo doveva accettarne esattamente due | **Corretto.** La 4.0.2 distribuisce `WorkflowResources`, e `__invoke()` accetta due parametri o tre |
| 64 | Le guide all'aggiornamento si contraddicevano a vicenda: la guida 9 faceva del run ID l'handle di continuazione; la guida 14 tornava a farne il workflow ID e declassava il run ID a contrassegno per singolo tentativo | **Obsoleto.** Le guide sono state riscritte e rinumerate per la release, e concordano con il codice: il workflow ID è l'handle, il run ID e il tentativo di esecuzione sono fence |
| 65 | `AsyncBranchRunner`, che prima della release si chiamava `AsyncExecutor`, richiede `amphp/amp`, che il pacchetto elenca solo come dipendenza di sviluppo e non sotto `suggest`. Senza di esso una diramazione parallela fallisce con *"Call to undefined function Amp\async()"* | **Aperto.** |
| 66 | La skill `neuron-workflow` chiama `->setProvider()`. Il metodo è `setAiProvider()` | **Aperto.** È ancora nella skill distribuita con la 4.0.2 |
| 67 | La pagina sull'human-in-the-loop chiama `$workflow->resume([...])` e si ferma lì. Prima della release `resume()` si limitava a predisporre la risposta, e non succedeva nulla fino a `->run()` o `->events()` | **Obsoleto.** `Workflow::resume()` non esiste nella 4.0.2. Continua con `submitInputs($answer)->run()` oppure `run(ExecutionRequest::resume($answer))` |

### Materiale della v4 — SDK per Laravel e guide all'aggiornamento (Capitoli da 17 a 23)

| # | Problema | Stato sulla 4.0.2 |
|---|---|---|
| 68 | Il README della 2.x mostra ancora pattern della v3: un middleware `ToolApproval`, `StreamingNode`, `->events()` su uno stream, e Inspector abilitato dalla sola variabile d'ambiente | **Aperto, e più esteso.** Il README della 2.0.0 documenta anche `EloquentChatHistory` e un hook `chatHistory()`, entrambi rimossi nella 4.0.2 (punto 79) |
| 69 | Il docblock della facade `Neuron` non ha una voce `middleware()`, quindi il tuo IDE e PHPStan rifiutano una chiamata che la classe accetta | **Aperto.** Irrilevante finché la facade lancia un'eccezione (punto 94) |
| 70 | Il `MonitoredAgent` della guida all'aggiornamento 7 sovrascriveva il costruttore senza chiamare `parent::__construct()`, perdendo il thread ID | **Obsoleto.** L'esempio non c'è nelle guide distribuite con la 4.0.2 |
| 71 | L'esempio "gli endpoint di ripresa sono invariati" della guida 11 usava il vecchio ordine del costruttore e un argomento `chat(payload:)` che non esiste; la guida 13 elencava ancora un adapter SSE | **Obsoleto.** Nessuno dei due c'è nelle guide distribuite con la 4.0.2 |

## Difetti del codice trovati verificando questo libro

Questi non sono problemi di documentazione. Sono comportamenti del codice, ciascuno riprodotto da uno script. Tre dei cinque sono corretti nella 4.0.2 e uno è obsoleto; restano qui per chi legge da un'installazione più vecchia. I test di contratto del repository di accompagnamento fissano quello aperto, così il giorno in cui cambia è la build a dirlo. I difetti trovati sulla release stabile sono nella sezione successiva.

| # | Difetto | Dove morde | Stato sulla 4.0.2 |
|---|---|---|---|
| 72 | `RAG::reindexBySource()` raggruppava i documenti in un array indicizzato per nome della sorgente, quindi PHP trasformava un nome puramente numerico come `"42"` in un intero e il filtro di cancellazione falliva poi la validazione dello schema | Sezione 20.2 | **Corretto.** La 4.0.2 rilegge il nome dal documento; `"42"` funziona |
| 73 | `make:node` generava PHP non valido (un backslash raddoppiato in `Workflow\\Events`), e `make:agent` importava `NeuronAI\Providers\Anthropic`, che è un namespace, come se fosse la classe | Sezione 3.3 | **Corretto** nella CLI del core. Il `neuron:node` dell'SDK ha un difetto tutto suo (punto 95) |
| 74 | Il controllo sul tentativo obsoleto lancia una semplice `WorkflowException` (*"Stale continuation…"*), mentre quello sulla run obsoleta lancia `StaleWorkflowRunException` — quindi un `catch` scritto per la seconda non vede mai la prima | Sezione 22.3 | **Aperto.** La Sezione 22.3 fa leva su questa differenza; `abandon()` presenta la stessa divisione (punto 92) |
| 75 | `StdioTransport::connect()` faceva l'escape degli argomenti ma non del comando, quindi il percorso di un interprete che contiene uno spazio — il default con Laravel Herd su macOS — veniva spezzato dalla shell e il server MCP moriva all'istante | Sezione 9.2 | **Corretto.** La 4.0.2 avvia il server senza shell, quindi il percorso viene passato così com'è; la vecchia soluzione con `escapeshellarg()` ora fallisce con *"Failed to start the MCP server"* |
| 76 | Un `InMemoryChatHistory` costruito senza thread ID si legava a una chiave casuale `mem_…`, quindi un hook `chatHistory()` che ometteva il thread faceva lanciare a `make(threadId: ...)` l'errore *"Conflicting thread identity"* | Sezioni 4.3 e 7.5 | **Obsoleto.** Le classi della cronologia, l'hook e l'argomento `threadId:` sono spariti tutti (punti 77 e 79) |

Vale la pena conoscere anche due lacune di tipizzazione, perché fanno fallire all'analisi statica del codice corretto invece che a runtime: `subscribe()` tipizza il suo listener come `callable(object): void`, quindi nessun listener tipizzato su una specifica classe di evento supera PHPStan al livello 8; e il generatore in streaming è tipizzato `Generator<int, object>`, che non soddisfa `SSEEncoder::encode()`. Il repository di accompagnamento segnala ogni soluzione alternativa con un commento. Una terza lacuna è chiusa: `Agent::stream()` è dichiarato `Generator`, quindi un semplice `foreach` su di esso non richiede alcun `assert`.

## Trovati sulla 4.0.2 e sull'SDK 2.0.0

Ogni punto qui sotto è aperto su neuron-ai 4.0.2 e neuron-laravel 2.0.0. Dove un punto è un difetto del codice e non una deriva del materiale, lo dice. I punti che coinvolgono un database sono stati eseguiti su SQLite.

### Identità e memoria — Capitoli 3, 4 e 18

| # | Problema |
|---|---|
| 77 | I listati più vecchi, il materiale di pre-release e le skill per Boost dell'SDK passano la conversazione come `make(threadId: ...)`. Il costruttore è `(?string $workflowId, ?WorkflowState $state)`, quindi la chiamata fallisce con *"Unknown named parameter $threadId"*. Usa `make(workflowId: ...)`, `setThreadId()` o `for()` — Sezione 4.3 |
| 78 | Un agent, un RAG o un workflow senza un ID associato si rifiuta di partire: *"This agent has no thread ID: bind one with setThreadId() first."*, oppure *"This workflow has no workflow ID: bind one with setWorkflowId() first."* Il framework non ne inventa mai uno, quindi ogni `Agent::make()->chat(...)` su una riga del materiale più vecchio fallisce. Su un agent l'eccezione è una `AgentException`, che un `catch` scritto per i fallimenti del modello inghiotte — Sezione 26.14 |
| 79 | Un hook `chatHistory()` rimasto nel codice non viene mai chiamato, e nulla lo segnala: le classi rimosse che nomina non vengono mai caricate, l'agent risponde, e la conversazione resta nello store in memoria predefinito con la sua finestra da 50.000 token. Gli hook sono `messageStore()` e `contextWindow()`. `setChatHistory()`, al contrario, fallisce in modo evidente — Sezioni 4.3 e 18.2 |
| 80 | Un message store salta un messaggio di cui possiede già l'ID: `append()` è idempotente per contratto. Un test che accoda due volte la stessa istanza di `AssistantMessage` in `FakeAIProvider` perde quindi in silenzio la seconda risposta, e il turno successivo lancia `ChatHistoryException: Invalid message sequence`. Costruisci un messaggio per ogni risposta preparata |
| 81 | Le skill `neuron-agent` e `neuron-tool-approval` dicono che il `chat()` successivo sostituisce un turno fallito. Vale solo quando il turno è fallito prima che la sua domanda venisse salvata. Dopo uno step di tool il `chat()` successivo lancia `ChatHistoryException: Invalid message sequence`, finché un semplice `run()` non porta a termine il turno fallito. La skill `neuron-laravel-integration` lo dice nel modo giusto — Sezione 18.4 |

### Structured output — Capitolo 6

| # | Problema |
|---|---|
| 82 | Quando i ritentativi si esauriscono su una chiave obbligatoria mancante, o su un valore del tipo sbagliato, `structured()` lancia `DeserializerException`, che estende `NeuronException` e non è una `AgentException`. Un `catch (AgentException)` vede solo le violazioni delle regole. Cattura entrambe — Sezioni 6.4 e 26.14 |
| 83 | `#[ArrayOf(X::class)]` valida ogni elemento con le regole dell'elemento stesso e poi scarta ciò che ha trovato: la violazione recita *"lines must be an array of OrderLine"* qualunque elemento abbia infranto qualunque regola, e quella frase è tutto ciò che il ritentativo dice al modello. Senza `#[ArrayOf]` le regole degli elementi non vengono eseguite affatto. Un difetto del codice; la Sezione 6.5 dice dove mettere invece il vincolo |

### Streaming, MCP e osservabilità — Capitoli 7, 9 e 10

| # | Problema |
|---|---|
| 84 | Gli eventi di osservabilità stanno in `NeuronAI\Agent\Observability\`, `NeuronAI\Workflow\Observability\` e `NeuronAI\RAG\Observability\`. Il materiale di pre-release, compresa la skill `neuron-monitoring` per Boost dell'SDK, usa `NeuronAI\Observability\Events\`. `subscribe()` accetta qualunque stringa, quindi un listener sul vecchio nome non scatta mai e non c'è alcun errore — Sezione 10.2 |
| 85 | L'endpoint semplice della skill `neuron-frontend-integration` invia gli header e poi itera dentro `try { ... } catch (Throwable) {}`. Il generatore è lazy, quindi un turno che il motore rifiuta con `RunInFlightException` viene lanciato dentro quel `try`: il browser riceve un 200 e uno stream vuoto. Estrai il primo evento con `$events->valid()` prima del primo header, come fanno le skill per Laravel e per Symfony — Sezioni 7.5 e 21.4. La stessa skill indica due versioni del client AG-UI con cui è stata provata, la 1.0.x e la 0.0.59 |
| 86 | `McpConnector::tools()` lancia `ToolException` quando lo schema di un tool del server usa `anyOf`, `oneOf`, `$ref` o un elenco di tipi, e basta un tool così per far fallire la scoperta dell'intero server. È la forma che i server Python costruiti su FastMCP e Pydantic danno a un parametro opzionale. La 3.x semplificava quelle proprietà in silenzio, quindi il materiale più vecchio si collega senza commenti. `only()` filtra prima della conversione — Sezione 9.1 e guida all'aggiornamento 50 |

### RAG — Capitoli 12 e 20

| # | Problema |
|---|---|
| 87 | `PdfReader` esegue `pdftotext` tramite `symfony/process`, e `HtmlReader` richiede `html2text/html2text`. Il pacchetto non elenca nessuno dei due né sotto `require` né sotto `suggest`, quindi Composer non li installa insieme a esso. Il docblock di `HtmlReader` promette inoltre Markdown; restituisce testo semplice — Sezione 12.2 |
| 88 | `OpenAIEmbeddingsProvider` chiede 1024 dimensioni se non gli dici altro, e il `config/neuron.php` dell'SDK imposta lo stesso numero; `MariaDBVectorStore::setupTable()` crea `VECTOR(1536)` se non gli dici altro. I due default non coincidono: passa il numero a entrambi i lati — Sezione 12.4 |

### Workflow — Capitoli da 13 a 16, 22 e 26

| # | Problema |
|---|---|
| 89 | `expiresAt` non rifiuta una risposta in ritardo. Un payload consegnato dopo la scadenza raggiunge il nodo come qualunque altro; solo un `run(ExecutionRequest::resume())` senza input trasforma un'attesa scaduta in `null`. Un nodo che deve rifiutare una risposta in ritardo controlla l'orologio da sé, dentro `memoize()` — Sezione 26.10 |
| 90 | Un workflow ID la cui run è terminata è di nuovo libero: i suoi record vengono eliminati, e il `run()` successivo, semplice o con lo stesso run ID riservato, esegue il workflow dall'inizio. Un job di avvio riconsegnato ripete il lavoro. `retainCompletionUntilAcknowledged()` conserva l'esito e rifiuta la riconsegna con `RunInFlightException`, finché non chiami `acknowledge()` — Sezioni 22.4 e 26.13 |
| 91 | Quando non c'è nulla in attesa, i tre modi di continuare falliscono in tre modi diversi. `submitInputs()` lancia `InputTranslationException`, che non è una `WorkflowException`. `run(ExecutionRequest::resume($payload))` lancia una semplice `WorkflowException`, *"No run in flight"*. La stessa chiamata con `expectedRunId:` lancia `StaleWorkflowRunException`. Un gestore delle eccezioni deve mapparle tutte e tre — Sezione 21.4 |
| 92 | `abandon()` ripete la divisione del punto 74: un run ID obsoleto lancia `StaleWorkflowRunException`, un tentativo obsoleto una semplice `WorkflowException`, *"Cannot abandon a different execution attempt."* Un difetto del codice. Chiamato con un run ID quando nulla occupa il workflow ID, lancia inoltre `StaleWorkflowRunException` là dove un ciclo di pulizia si aspetta `false` — Sezione 22.4 |
| 93 | Le guide incluse nel pacchetto dicono che un nodo che raggiunge le sue attese in un ordine diverso "fallisce con `WorkflowException` invece di perdere la risposta". È vero per un `interruptIf()` la cui condizione è cambiata. Con un semplice `if` attorno a `interrupt()` non viene lanciato nulla: un'attesa è identificata dalla sua posizione, quindi la risposta va all'attesa che ora viene per prima, e il nodo si ferma di nuovo sulla domanda che aveva già ricevuto risposta. Un difetto del codice — Sezione 15.5 |

### SDK per Laravel 2.0.0 — Capitoli da 17 a 23

| # | Problema |
|---|---|
| 94 | La facade `Neuron` lancia un'eccezione a ogni chiamata. Costruisce `Agent::make()` e non associa mai un thread, quindi `Neuron::chat()`, `Neuron::stream()` e `Neuron::structured()` finiscono tutti in *"This agent has no thread ID"*. Genera una classe agent e associala con `->for($threadId)`. Un difetto dell'SDK — Sezione 17.4 |
| 95 | `php artisan neuron:node` genera `use NeuronAI\Workflow\StartEvent;` e `use NeuronAI\Workflow\StopEvent;`. Le classi stanno in `NeuronAI\Workflow\Events\`. Il file supera `php -l`, e il workflow che contiene il nodo fallisce la validazione alla prima esecuzione. Un difetto dell'SDK — Sezione 17.3 |
| 96 | La migration `chat_messages` distribuita non ha una colonna `message_id` e il model `ChatMessage` distribuito non la rende fillable, mentre `EloquentMessageStore` identifica ogni riga in base a essa. Lo stesso messaggio viene salvato due volte e torna indietro con un ID diverso. Scrivi da te la migration e il model. Un difetto dell'SDK — Sezione 18.2 |
| 97 | `EloquentPersistence` sulla tabella `workflow_store` distribuita fallisce. La tabella ha una chiave primaria composta e nessun `id`, quindi gli update e le delete del model vanno su `where "id" is null`: un workflow muore al primo step con *"Stale execution attempt 1 cannot write…"*, e il turno concluso di un agent non viene mai ripulito, quindi il suo `chat()` successivo lancia `RunInFlightException`. Usa `DatabasePersistence` su quella tabella. Un difetto dell'SDK — Sezione 18.4 |
| 98 | `AIProvider::driver()` ed `EmbeddingProvider::driver()`, chiamati senza argomento, lanciano un `TypeError` quando `NEURON_AI_PROVIDER` o `NEURON_EMBEDDING_PROVIDER` non è impostata: *"getDefaultDriver(): Return value must be of type string, null returned"*. La configurazione non ha un valore di ripiego per nessuna delle due, e il README non nomina mai la seconda. Un difetto dell'SDK — Sezione 17.2 |
| 99 | `VectorStoreManager` non è registrato come singleton, a differenza degli altri due manager. Un driver aggiunto con `VectorStore::extend()` vive su un'istanza che solo la cache della facade possiede: risolvi il manager dal container, oppure svuota le istanze risolte della facade, e il driver risulta *"not supported"*. Registra il singleton nel tuo service provider. Un difetto dell'SDK — Sezioni 17.6 e 20.1 |
| 100 | Le skill per Boost incluse nell'SDK sono copie fatte prima della release, e insegnano l'API che questa ha rimosso: `make(threadId:)`, `setChatHistory()` e le classi `…ChatHistory`, `$workflow->resume()`, `abandonRun()`, `acknowledgeCompletion()`, `AsyncExecutor`, `NeuronAI\Observability\Events\`, `approvalPolicy(array $inputs)`, `resolveProvider()`, e un'istanza di adapter passata a `setStreamAdapter()`, che ora accetta una factory. Installa invece le skill distribuite con neuron-ai — Sezioni 17.7 e 27.3 |
| 101 | L'SDK distribuisce generatori e nessun comando per le eval. `vendor/bin/neuron evaluation` gira fuori dall'applicazione avviata, quindi un evaluator che tocca una facade fallisce con *"A facade root has not been set."* La skill `neuron-laravel-integration` ti fa scrivere da te `php artisan neuron:evaluate` — Sezione 23.4 |

### Le skill incluse nel pacchetto e il README — Capitolo 27

| # | Problema |
|---|---|
| 102 | Le skill distribuite con la 4.0.2 sono aggiornate, non impeccabili. `neuron-workflow` stampa `use NeuronAI\Agent;` e `->setProvider()` (punto 66), parla del "`StreamingNode` integrato", che non esiste, e ti dice di estendere "la classe base astratta `Event`", che è un'interfaccia. `neuron-evaluation` stampa `use NeuronAI\Agent;`. `neuron-test` chiama ancora `$workflow->resume([...])->run()`. `neuron-streaming` elenca `NativeAdapter` (punto 54). E `src/Tools/AGENTS.md` costruisce un `new DeferredTool(...)`; la classe è `FrontendTool` |
| 103 | Il README dice che le skill installate sono collegate con symlink, "quindi restano aggiornate ogni volta che Neuron viene aggiornato tramite Composer". La guida all'aggiornamento 0 dice che nulla punta dentro `vendor/` e che Composer non aggiorna le copie installate. Non è stato stabilito qui; eseguire di nuovo `npx skills add ./vendor/neuron-core/neuron-ai/skills -y` dopo ogni aggiornamento è giusto in entrambi i casi — Sezione 17.7 |

## Ordine di priorità

Se hai poco tempo, questi sette contano di più perché compaiono nel codice a più alto traffico:

1. **#77 e #78** — l'identità. Nulla parte senza un ID, e l'argomento che il materiale più vecchio usa per passarne uno non esiste più. Riguardano ogni capitolo.
2. **#30, #36 e #67** — l'API di esecuzione dei workflow e il modo in cui si fa proseguire una run in pausa, ora che `resume()` non c'è più. Riguardano tutta la Parte IV.
3. **#79** — l'hook `chatHistory()` morto. L'agent risponde, non conserva nulla di durevole, e nulla ti avverte.
4. **dal #94 al #97** — l'SDK per Laravel. La facade lancia un'eccezione, e le tabelle distribuite non si adattano agli store.
5. **#45 e #46** — le firme dell'approval policy e del gestore degli errori. La prima è un errore fatale al caricamento della classe; la seconda fallisce esattamente quando un tool lancia un'eccezione, che è l'unico momento in cui conta.
6. **#26 e #58–59** — i filtri. Il vecchio metodo non c'è più, e la catena documentata conserva in silenzio solo la sua ultima condizione.
7. **#16 e #84** — l'osservabilità. Non viene tracciato nulla finché non sottoscrivi il listener, un listener su un vecchio nome di classe non scatta mai, e nulla ti avverte né dell'una né dell'altra cosa.

## Correzioni già applicate in questo libro

Oltre ai punti qui sopra, quattro cose che il materiale precedente su questo framework sbaglia sono state corrette nel testo che hai appena letto, invece che semplicemente segnalate:

**L'API di streaming, per due volte.** `foreach ($agent->stream($msg) as $chunk) { echo $chunk; }` era la forma della v2 e stampava oggetti; la v3 restituiva un handler con `events()`. In v4, `stream()` *è* di nuovo il generatore — ma produce *oggetti* chunk, e solo alcuni di essi sono testo. La Sezione 7.2 filtra per `TextChunk`, legge `getReturn()` per ottenere lo stato finale, e mostra entrambe le forme precedenti così che tu le riconosca quando le incontri.

**Le pause sono risultati, non eccezioni.** I tutorial sull'human-in-the-loop scritti prima della v4 catturano `WorkflowInterrupt`. Non viene lanciato nulla: `run()` ritorna, e `$state->isInterrupted()` dice perché. Il Capitolo 15 è scritto attorno a questo fin dalla prima pagina.

**Non esiste uno store pgvector.** Una gran quantità di materiale di terze parti presume che esista, perché pgvector è onnipresente nell'ecosistema Python. L'elenco completo di prima parte è nella Sezione 12.5: Memory, File, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch e MongoDB Atlas, con PHPVector come pacchetto separato in attesa di una release per la v4. Il Laboratorio 9 è costruito su MariaDB, e il Capitolo 20 raccomanda MariaDB 11.7+.

**`required: true` controlla la presenza, non il contenuto.** Una chiave obbligatoria omessa provoca una `DeserializerException` e innesca un ritentativo; una stringa vuota è presente, quindi passa. La Sezione 6.4 abbina a ogni scalare obbligatorio un `#[NotBlank]`, che è ciò che intercetta il valore vuoto, e il punto 82 dice quale eccezione ti arriva quando i ritentativi si esauriscono.
