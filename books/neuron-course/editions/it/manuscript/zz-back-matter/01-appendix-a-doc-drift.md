# Appendice A — Dove la documentazione si discosta dal codice {.unnumbered}

Settantasei punti in cui il materiale ufficiale di NeuronAI — il sito della documentazione, i README, le guide all'aggiornamento e le skill per agent — contraddice il codice, contraddice sé stesso, contiene un refuso o mostra un'API di una major precedente. Sei di essi — il punto 49 e i punti dal 72 al 76 — non sono affatto problemi di documentazione, ma difetti del codice, trovati durante la verifica di questo libro. Ciascuno di essi produce un errore, o un risultato sbagliato, per chi copia la pagina.

Non è una lamentela sul progetto. La deriva della documentazione è ciò che succede quando una libreria si muove in fretta e i suoi documenti portano esempi scritti contro quattro major diverse; la riscrittura del motore dei workflow nella v4 l'ha resa inevitabile. È però un costo reale per te — e un pomeriggio passato a risolverli contro la tua versione installata è la preparazione di maggior valore che puoi fare prima di scrivere codice di produzione.

## Come leggere la tabella

Le voci dalla 1 alla 44 sono state catalogate contro la v3. I loro numeri sono invariati, perché i capitoli li citano, e ciascuna riporta ora il suo **stato in v4**:

- **Aperto** — ancora sbagliato nel materiale che troverai.
- **Risolto** — il codice risponde alla domanda; la voce dice qual è la risposta.
- **Obsoleto** — ciò che descriveva non esiste più in v4.

Le voci dalla 45 in poi sono nuove in v4.

## Alcuni di questi sono già risolti

Il repository di accompagnamento fissa ogni API usata da questo libro contro una versione nota, e l'esecuzione della sua suite di test ti dice quali dei punti qui sotto sono ancora aperti sulla *tua* installazione:

```bash
git clone https://github.com/hidran/neuronai-php-book.git
cd neuronai-php-book && composer install && composer check
```

Questo libro è stato verificato contro il ramo **neuron-ai 4.x** poco prima del tag 4.0.0, e contro **neuron-laravel 2.x**; il colophon registra i commit. Dove uno stato qui sotto dice *Risolto*, è contro queste versioni che è stato risolto.

## Come risolverli in fretta

Invece di controllare settantasei voci una alla volta, esegui una sonda per area. Ciascuna risolve un intero gruppo.

### Preparazione

```bash
mkdir neuron-verify && cd neuron-verify
composer require neuron-core/neuron-ai
composer show neuron-core/neuron-ai
vendor/bin/neuron --help
```

Registra la versione esatta. Tutto ciò che segue è relativo a essa.

### Sonda 1 — namespace e nomi di classi

```bash
grep -rn "class Agent\b"        vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class SystemPrompt\b" vendor/neuron-core/neuron-ai/src/ | head
grep -rn "class ApprovalRequest" vendor/neuron-core/neuron-ai/src/
grep -rln "EmbeddingsProvider\|EmbeddingProvider" vendor/neuron-core/neuron-ai/src/RAG/ | head
grep -rn "class .*Adapter\b" vendor/neuron-core/neuron-ai/src/Agent/Adapters/ | head
grep -rn "class ToolRunsExceeded\|class ToolMaxTries" vendor/neuron-core/neuron-ai/src/
```

Risolve le voci **1, 4–5, 9, 22–25, 34, 39, 54**.

### Sonda 2 — firme dei metodi

```bash
grep -rn "function instructions"      vendor/neuron-core/neuron-ai/src/Agent/
grep -rn "function approvalPolicy"    vendor/neuron-core/neuron-ai/src/Tools/Tool.php
grep -rn "function toolErrorHandler"  vendor/neuron-core/neuron-ai/src/Agent/
grep -rn "function run\|function events\|function resume\|function __construct" \
     vendor/neuron-core/neuron-ai/src/Workflow/Workflow.php
grep -rn "function delete\|function search" \
     vendor/neuron-core/neuron-ai/src/RAG/VectorStore/VectorStoreInterface.php
```

Risolve le voci **8, 30–31, 36–37, 45–46, 58, 63**.

### Sonda 3 — leggi le guide incluse nel pacchetto

```bash
ls vendor/neuron-core/neuron-ai/upgrade/
find vendor/neuron-core/neuron-ai/src -name AGENTS.md
```

Le guide all'aggiornamento e i file `AGENTS.md` di ciascun modulo sono distribuiti con il codice, quindi descrivono la versione che hai installato. Sono la prosa più affidabile che il progetto pubblichi — e nemmeno loro sono perfette (voci 64, 70, 71).

### Sonda 4 — uno script minimo per capacità

Scrivi ed esegui sei brevi script. Ciascuno richiede pochi minuti e risolve un gruppo in modo definitivo:

| Script | Risolve |
|---|---|
| Agent + `chat()` + `getMessage()` | 8, 9 |
| Classe tool + toolkit con `only()`, e un tool soggetto ad approvazione | 1–3, 45–46 |
| `structured()` con un DTO validato, a cui si manda di proposito un valore errato | 12–15, 49–50 |
| Itera `stream()`, stampa i `TextChunk`, poi `getReturn()` | 38, 53 |
| Workflow minimo a 3 nodi, poi un'interruzione e una ripresa in un secondo processo | 30–32, 34–37, 67 |
| RAG con un `DocumentSchema` e una ricerca filtrata | 26, 43, 58–60 |

**È più veloce e più affidabile che leggere il sorgente**, perché coglie anche comportamenti che le firme non rivelano.

## Le voci

### Tool — Capitolo 5

| # | Problema | Stato in v4 |
|---|---|---|
| 1 | `ToolRunsExceededException` nella prosa contro `ToolMaxTriesException` nell'esempio di catch | **Risolto.** Esiste solo `NeuronAI\Exceptions\ToolRunsExceededException` |
| 2 | `setMaxRuns()` contro `setMaxTries()` — sezioni diverse usano nomi diversi | **Aperto.** `setMaxRuns()` (tool) e `toolMaxRuns()` (agent) sono corretti; l'esempio di `with()` chiama ancora `setMaxTries(1)`, su un `MySQLToolkit` a cui non viene passato alcun PDO |
| 3 | `ExponentiateTool` nel sorgente di `provide()` contro `ExponentialTool` nella tabella dei tool | **Obsoleto.** La calcolatrice è stata riscritta attorno a `EvaluateTool`; nessuna delle due classi esiste |
| 4 | `Toolkits\CalendarToolkit\CalendarToolkit` contro `Toolkits\Calendar\...` | **Risolto.** `NeuronAI\Tools\Toolkits\Calendar\` |
| 5 | `NeuronAI\Tools\Calculator\CalculatorToolkit` contro `NeuronAI\Tools\Toolkits\Calculator\CalculatorToolkit` | **Risolto.** Il secondo |
| 6 | `ProviderTool:make()` — due punti singoli, refuso per `::` | **Risolto.** Corretto nella documentazione v4 |
| 7 | `new SesCleint(...)` — refuso per `SesClient` | Aperto |
| 8 | `instructions()` mostrato sia `public` sia `protected` | **Risolto.** `protected`, con ritorno `SystemMessage\|string`; un ritorno `string` semplice è ancora lecito |
| 9 | `use NeuronAI\Agent;` (v2) contro `use NeuronAI\Agent\Agent;` negli esempi dei toolkit | Aperto |

### Messaggi e multimodalità — Capitoli 4 e 8

| # | Problema | Stato in v4 |
|---|---|---|
| 10 | `AudioContent` importato ma viene istanziato `FileContent` | Aperto |
| 11 | `TextBlock` / `FileBlock` contro `TextContent` / `FileContent` | Aperto. Le classi sono `TextContent` / `FileContent` |

### Structured output — Capitolo 6

| # | Problema | Stato in v4 |
|---|---|---|
| 12 | `NeuronAI\StructuredOutput\Property` dovrebbe essere `SchemaProperty` | Aperto |
| 13 | Import del validatore di Symfony invece di `NeuronAI\StructuredOutput\Validation\Rules\` | Aperto |
| 14 | L'esempio di `#[OutOfRange]` importa `InRange` | Aperto |
| 15 | Regola personalizzata: arità di `respectFormat()` non coerente; `$this->pattern` contro `$this->format` | Aperto |

### Osservabilità ed eval — Capitolo 10

| # | Problema | Stato in v4 |
|---|---|---|
| 16 | Tre nomi di observer: `Inspector\Neuron\InspectorObserver`, `NeuronAI\Observability\InspectorObserver`, `NeuronAI\Observability\AgentMonitoring` | **Risolto, con un quarto nome.** La v4 usa eventi PSR-14; il listener è `Inspector\Neuron\V4\InspectorSubscriber`, in `inspector-apm/inspector-php` 3.18.1 o successivo, e va sottoscritto esplicitamente |
| 17 | `make:evaluator` contro `make:evaluators` fra la scheda Unix e quella Windows | **Risolto.** `make:evaluators`; il singolare dà "Unknown command" |
| 18 | `evaluations --path=X` contro `evaluation X --concurrency=N` | **Risolto.** `neuron evaluation`, al singolare; funzionano sia `--path=<dir>` sia un `<dir>` posizionale; `--concurrency=N` richiede `pcntl` e `spatie/fork` |
| 19 | `ConsoleDriver` contro `ConsoleOutputDriver` | **Risolto.** Nessuno dei due: `ConsoleOutput` e `JsonOutput`, in `NeuronAI\Evaluation\Output` |
| 20 | `autoload-dev` mappa `App\Evaluators\` ma il generatore usa `App\Neuron\Evaluators\` | **Aperto, e peggiorato.** Il generatore legge solo `autoload`, mai `autoload-dev`, quindi gli evaluator generati finiscono sempre nei percorsi di produzione |
| 21 | Refuso `new Antrhopic(...)`; conferma che `setAiProvider()` / `setInstructions()` esistano | **Risolto.** Entrambi i metodi esistono su `AgentInterface`; il refuso resta |

### RAG — Capitoli 11 e 12

| # | Problema | Stato in v4 |
|---|---|---|
| 22 | `FileVectorStore` mostrato in tre modi: `(directory, name)`, `(directory, topK)`, `(directory, key)` | **Risolto.** `(directory, topK = 4, name = 'neuron', ext = '.store', schema = null)` |
| 23 | `FileVectoreStore` — nome di classe con refuso (una `e` in più) | Aperto |
| 24 | `OpenAIEmbeddingsProvider` contro `OpenAIEmbeddingProvider` | **Risolto.** `OpenAIEmbeddingsProvider`, con la `s`; `model:` è obbligatorio |
| 25 | Namespace `RAG\Embeddings\` contro `RAG\EmbeddingProvider\` | **Risolto.** `NeuronAI\RAG\Embeddings\` |
| 26 | `withFilters()` (Pinecone) contro `withFilter()` (Elasticsearch) | **Obsoleto.** Sono spariti entrambi; i filtri si dichiarano in un `DocumentSchema` e si applicano tramite `retrievalScope()` |
| 27 | Ricontrolla la denominazione di `CalculatorToolkit` insieme alla voce 3 | **Obsoleto.** Vedi la voce 3 |
| 28 | Punto e virgola di troppo: `FileDataLoader::for(...);` seguito da `->addReader(...)` | Aperto |
| 29 | Conferma il costruttore di `Document` e l'accessore al contenuto prima di rilasciare uno splitter personalizzato | **Risolto.** `Document` è `final`; uno splitter personalizzato deve copiare `sourceType`, `sourceName` e i metadati su ogni chunk, altrimenti la reindicizzazione non riesce a trovarlo |

### Workflow — Capitoli da 13 a 16

| # | Problema | Stato in v4 |
|---|---|---|
| 30 | **`init()`/`run()` contro `start()`/`getResult()`** — due API di esecuzione su pagine adiacenti della documentazione | **Risolto, con una terza API.** La v2 usava `start()`/`getResult()`, la v3 `init()`/`run()`; la v4 non ha alcun handler: `$workflow->run()`, oppure `events()` per lo streaming |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')` — costruttore v2, ancora presente nei post dei blog | **Risolto.** In v4 è `Workflow::make(workflowId: ..., state: ...)`; la persistenza passa per `setPersistence()` |
| 32 | Classe `Edge` e `addEdges()` — rimossi in v2, ancora nel materiale v1 | Aperto (nel materiale vecchio) |
| 33 | `BrancheA1Event` — refuso nell'esempio di diramazione | Aperto |
| 34 | `ApprovalRequest` importato da `NeuronAI\Workflow\Interrupt` | **Aperto.** La classe è `NeuronAI\Agent\Interrupt\ApprovalRequest` |
| 35 | L'esempio di richiesta personalizzata sovrascrive `jsonSerialize()`, usa un `$this->note` non definito e omette `use DateTimeImmutable` | **Aperto.** `jsonSerialize()` è `final` su `InterruptRequest`; sovrascrivi invece `metadata()` |
| 36 | `Workflow::make(runId: ...)` e `getRunId()` usati come handle per la ripresa | **Aperto.** Non esiste un argomento `runId` nel costruttore; l'handle è il workflow ID, e il run ID è un fence per singolo tentativo (vedi la voce 64) |
| 37 | Conferma la firma di iniezione di `CustomState` sul workflow | **Risolto.** `Workflow::make(state: new CustomState())`, oppure un hook `state()` più `@extends Workflow<CustomState>` |
| 38 | Conferma il nome del metodo accessore di streaming sull'handler | **Risolto.** Non c'è alcun handler: `events()` restituisce un generatore, e `getReturn()` su di esso fornisce lo stato finale |

### SDK per Laravel — Capitoli da 17 a 23

| # | Problema | Stato in v4 |
|---|---|---|
| 39 | `use NeuronAI\Agent;` / `use NeuronAI\SystemPrompt;` — namespace v2 nel README | Aperto |
| 40 | `new SystemPrompt(...config('neuron.system_prompt');` — parentesi di chiusura mancante | Aperto |
| 41 | `$workflow = WorkflowAgent(persistence: ...)` — manca `new` | **Obsoleto.** L'esempio non c'è più nel README della 2.x |
| 42 | `ElquentChatHistory` con refuso nella prosa; ancora del documento `#eloquentchathisotry` | Aperto |
| 43 | Conferma `withFilters()` contro `withFilter()` sullo store restituito da `VectorStore::driver()` | **Obsoleto.** Vedi la voce 26 |
| 44 | Conferma quali driver di vector store espone `config/neuron.php` | **Risolto.** `file`, `pinecone`, `qdrant`, `meilisearch`, `chroma` |

### Novità della v4 — tool e messaggi (Capitoli 5, 7, 8)

| # | Problema |
|---|---|
| 45 | `approvalPolicy(array $inputs)` nella documentazione e nelle skill di Laravel Boost. Il metodo non accetta parametri — gli input sono già stati sottoposti a binding; leggi `$this->inputs`. Copiare la firma documentata produce un override incompatibile, cioè un errore fatale |
| 46 | La callback di `toolErrorHandler()` tipizzata come `fn (Throwable $e, ToolInterface $tool)`. Il secondo argomento è un `ToolCall`; il tipo documentato provoca un `TypeError` la prima volta che un tool lancia un'eccezione |
| 47 | La tabella dei toolkit elenca `FileSystemToolkit` come lettura, ricerca e parsing. Distribuisce anche tool di scrittura, modifica, cancellazione e bash — il che conta per ciò che passi a `only()` |
| 48 | L'elenco dei tool dei provider omette ZAI, e il fallback delle chiamate ai tool in parallelo è descritto come solo per Windows. Il fallback scatta anche senza `spatie/fork`, e per una singola chiamata |
| 51 | Gli esempi multimodali passano il payload come `source:`. Il parametro è `content:` su ogni blocco di contenuto |
| 52 | Viene importato `NeuronAI\Chat\MediaType`; l'enum è `NeuronAI\Chat\Enums\MediaType`. `SourceType` non viene mai importato, e un esempio riporta `UserMssage` |
| 53 | La pagina sullo streaming descrive ancora `StreamingNode`, `events()` su un handler, il vecchio namespace `Chat\Messages\Stream\Adapters\` e il rimosso `SSEAdapter`, e stampa `$chunk->content` senza filtrare per `TextChunk`. Nomina inoltre `NeuronAI\Agent\Adapter\AgentChunkAdapter` e `NeuronAI\Workflow\Channel\CallbackChannel`, nessuno dei quali esiste a quel percorso |
| 54 | La skill `neuron-streaming` elenca un `NativeAdapter`. La classe è `AgentChunkAdapter` |

### Novità della v4 — structured output (Capitolo 6)

| # | Problema |
|---|---|
| 49 | Le regole di confronto — `GreaterThan`, `GreaterThanEqual`, `LowerThan`, `LowerThanEqual`, `EqualTo`, `NotEqualTo` e `OutOfRange` — costruiscono il messaggio di violazione senza il nome del campo e con il *tipo* del riferimento invece del suo valore; `LowerThan` e `LowerThanEqual` dicono inoltre "greater than". Quel messaggio è ciò che il ritentativo invia al modello: un rimborso da 900 € torna indietro come *"must be greater than int"*. È un difetto del codice; la Sezione 6.5 mostra come aggirarlo |
| 50 | `#[IpAddress]` nella documentazione; la classe è `IPAddress`. Funziona su un filesystem che non distingue maiuscole e minuscole, fallisce in produzione su Linux |

### Novità della v4 — osservabilità ed eval (Capitolo 10)

| # | Problema |
|---|---|
| 55 | La skill `neuron-monitoring` dice che `neuron-core/cloud-sdk`, `neuron-cloud-laravel` e `neuron-cloud-symfony` sono disponibili su Packagist. Al momento della scrittura, tutti e tre restituiscono 404 |
| 56 | Lo stub del generatore di evaluator chiama ancora `->getMessage()->getContent()` senza l'operatore null-safe, quindi gli evaluator generati non superano PHPStan così come sono |
| 57 | La ricerca degli evaluator fa match su `^class`, quindi un evaluator `final`, `readonly` o `abstract` viene saltato in silenzio — *"No evaluator classes found"* |

### Novità della v4 — RAG (Capitoli 12 e 20)

| # | Problema |
|---|---|
| 58 | La pagina sui vector store mostra `delete(FilterGroup $filters)`. La firma è `delete(FilterExpression $filters)` |
| 59 | La stessa pagina concatena `Filter::gt(...)->lt(...)->eq(...)`. `Filter::gt()` restituisce un `Filter`, che non ha `lt()`; la concatenazione parte da `Filter::where()`, che restituisce `Criteria` |
| 60 | La documentazione elenca PHPVector fra gli store della v4. `neuron-core/php-vector` non aveva una release compatibile con la v4 al momento della scrittura |
| 61 | La skill `neuron-rag` chiama `$this->resolveProvider()`, che non esiste. Il metodo è `getProvider()` |
| 62 | `setRetrievalScope()` *sostituisce* l'hook `retrievalScope()` invece di aggiungersi a esso. Non è documentato da nessuna parte, e fa cadere in silenzio un filtro sul tenant — Sezione 20.1 |

### Novità della v4 — workflow (Capitoli da 13 a 16, 22)

| # | Problema |
|---|---|
| 63 | La pagina "Loops & Branches" dà a ogni nodo un terzo parametro `WorkflowResources $resources`. La classe non esiste, e l'`__invoke()` di un nodo deve accettarne esattamente due |
| 64 | Le guide all'aggiornamento si contraddicono a vicenda: la guida 9 fa del run ID l'handle di continuazione; la guida 14 torna a farne il workflow ID e declassa il run ID a contrassegno per singolo tentativo. Il codice segue la guida 14 |
| 65 | `AsyncExecutor` richiede `amphp/amp`, che il pacchetto elenca solo come dipendenza di sviluppo e non sotto `suggest`. Senza di esso l'executor fallisce con *"Call to undefined function Amp\async()"* |
| 66 | La skill `neuron-workflow` chiama `->setProvider()`. Il metodo è `setAiProvider()` |
| 67 | La pagina sull'human-in-the-loop chiama `$workflow->resume([...])` e si ferma lì. `resume()` si limita a predisporre la risposta; non succede nulla finché non chiami `->run()` o `->events()` |

### Novità della v4 — SDK per Laravel e guide all'aggiornamento (Capitoli da 17 a 23)

| # | Problema |
|---|---|
| 68 | Il README della 2.x mostra ancora pattern della v3: un middleware `ToolApproval`, `StreamingNode`, `->events()` su uno stream, e Inspector abilitato dalla sola variabile d'ambiente |
| 69 | Il docblock della facade `Neuron` non ha una voce `middleware()`, quindi la chiamata funziona ma il tuo IDE e PHPStan dicono di no |
| 70 | Il `MonitoredAgent` della guida all'aggiornamento 7 sovrascrive il costruttore senza chiamare `parent::__construct()`, perdendo il thread ID |
| 71 | L'esempio "gli endpoint di ripresa sono invariati" della guida 11 usa il vecchio ordine del costruttore e un argomento `chat(payload:)` che non esiste; la guida 13 elenca ancora un adapter SSE |

## Difetti del codice trovati verificando questo libro

Questi non sono problemi di documentazione. Sono comportamenti del codice 4.x contro cui questo libro è stato verificato, ciascuno riprodotto da uno script nel repository di accompagnamento. Controllali contro la tua versione; alcuni potrebbero essere stati corretti quando leggerai queste pagine.

| # | Difetto | Dove morde |
|---|---|---|
| 72 | `RAG::reindexBySource()` raggruppa i documenti in un array indicizzato per nome della sorgente, quindi PHP trasforma un nome puramente numerico come `"42"` in un intero e il filtro di cancellazione fallisce poi la validazione dello schema. Usa `article-42`, non `42` | Sezione 20.2 |
| 73 | `make:node` genera PHP non valido (un backslash raddoppiato in `Workflow\\Events`), e `make:agent` importa `NeuronAI\Providers\Anthropic`, che è un namespace, come se fosse la classe | Sezione 3.3 |
| 74 | Il controllo sul tentativo non più valido lancia una semplice `WorkflowException`, mentre quello sulla run non più valida lancia `StaleWorkflowRunException` — quindi un job che cattura solo quest'ultima si perde metà delle riconsegne per cui è stato scritto | Sezione 22.3 |
| 75 | `StdioTransport::connect()` fa l'escape degli argomenti ma non del comando, quindi il percorso di un interprete che contiene uno spazio — il default con Laravel Herd su macOS — viene spezzato dalla shell e il server MCP muore all'istante. Invariato rispetto alla 3.x | Sezione 9.2 |
| 76 | Un `InMemoryChatHistory` costruito senza thread ID si lega a una chiave casuale `mem_…` — di proposito, secondo il sorgente, ma a differenza di ogni altro backend della cronologia, che resta senza thread. Un hook `chatHistory()` che omette il thread fa quindi lanciare a `make(threadId: ...)` l'errore *"Conflicting thread identity"*. Passa `threadId: $this->threadId` | Sezioni 4.3 e 7.5 |

Vale la pena conoscere anche tre lacune di tipizzazione, perché fanno fallire all'analisi statica del codice corretto invece che a runtime: `subscribe()` tipizza il suo listener come `callable(object): void`, quindi nessun listener tipizzato su una specifica classe di evento supera PHPStan al livello 8; `Agent::stream()` è tipizzato `Generator|AgentState`, quindi un semplice `foreach` su di esso richiede un `assert`; e il generatore in streaming è tipizzato `Generator<int, object>`, che non soddisfa `SSEEncoder::encode()`. Il repository di accompagnamento segnala ogni soluzione alternativa con un commento.

## Ordine di priorità

Se hai poco tempo, queste sette contano di più perché compaiono nel codice a più alto traffico:

1. **#30 e #36** — l'API di esecuzione dei workflow e l'handle per la ripresa. Riguardano tutta la Parte IV.
2. **#45** — la firma dell'approval policy. Copiarla è un errore fatale al primo tool soggetto ad approvazione.
3. **#46** — la firma del gestore degli errori. Fallisce esattamente quando un tool lancia un'eccezione, che è l'unico momento in cui conta.
4. **#26 e #58–59** — i filtri. Il vecchio metodo non c'è più e i nuovi esempi non compilano.
5. **#16** — il listener dell'osservabilità. Non viene tracciato nulla finché non lo registri, e nulla ti avverte.
6. **#49** — i messaggi di validazione. Un ritentativo che non dice al modello nulla di utile è un ritentativo che paghi due volte.
7. **#18** — il comando delle eval. La tua prima esecuzione di eval fallisce se questo è sbagliato.

## Correzioni già applicate in questo libro

Oltre alle voci qui sopra, quattro cose che il materiale precedente su questo framework sbaglia sono state corrette nel testo che hai appena letto, invece che semplicemente segnalate:

**L'API di streaming, per due volte.** `foreach ($agent->stream($msg) as $chunk) { echo $chunk; }` era la forma della v2 e stampava oggetti; la v3 restituiva un handler con `events()`. In v4, `stream()` *è* di nuovo il generatore — ma produce *oggetti* chunk, e solo alcuni di essi sono testo. La Sezione 7.2 filtra per `TextChunk`, legge `getReturn()` per ottenere lo stato finale, e mostra entrambe le forme precedenti così che tu le riconosca quando le incontri.

**Le pause sono risultati, non eccezioni.** Ogni tutorial della v3 sull'human-in-the-loop cattura `WorkflowInterrupt`. In v4 non viene lanciato nulla: `run()` ritorna, e `$state->isInterrupted()` dice perché. Il Capitolo 15 è scritto attorno a questo fin dalla prima pagina.

**Non esiste uno store pgvector.** Una gran quantità di materiale di terze parti presume che esista, perché pgvector è onnipresente nell'ecosistema Python. L'elenco completo di prima parte è nella Sezione 12.5: Memory, File, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch e MongoDB Atlas, con PHPVector come pacchetto separato in attesa di una release per la v4. Il Laboratorio 9 è costruito su MariaDB, e il Capitolo 20 raccomanda MariaDB 11.7+.

**`required: true` non valida.** Dà forma allo schema inviato al modello e non viene controllato al ritorno. La Sezione 6.4 abbina a ogni scalare obbligatorio una regola, ed è questo che fa sì che una chiave omessa inneschi un ritentativo invece di un errore fatale.
