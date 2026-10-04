# Capitolo 17 — L'SDK per Laravel

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 17.1 Installazione e filosofia

### Installa

```bash
composer require neuron-core/neuron-laravel
```

**Requisiti:** questo libro usa Laravel 13 su PHP 8.5, con la versione 2.0.0 dell'SDK. Questa richiede `neuron-core/neuron-ai` `^4.0` e quindi tira dentro il framework: qui, la 4.0.3. Il pacchetto in sé accetta release di Laravel e PHP più vecchie; il codice del libro richiede PHP 8.5.

### Che cosa fornisce

Cinque cose, dalla descrizione del pacchetto stesso:

- Un file di configurazione per le credenziali del provider AI e degli embedding
- Comandi Artisan per generare lo scheletro dei componenti più usati
- Facade che istanziano provider e vector store dalla configurazione
- Migration pronte all'uso per `EloquentChatHistory`
- Linee guida per assistenti di codice AI integrate con Laravel Boost

Leggi l'elenco tenendo presente il framework che il pacchetto installa, perché l'SDK 2.0.0 non ne ha tenuto il passo. Le prime tre voci funzionano su neuron-ai 4.0.3, con l'eccezione di un generatore, e sono ciò che usa il resto della Parte V: il file di configurazione, i generatori e le facade per provider, embedding e vector store. Le ultime due no, e nemmeno la funzionalità con cui il README si apre, la facade `Neuron`.

::: {.callout .callout-warning}
[L'SDK 2.0.0 non è al passo con neuron-ai 4.0.3]{.callout-title}

Quattro parti del pacchetto non funzionano con la versione del framework che esso stesso installa. Per ciascuna c'è un'alternativa funzionante, indicata nel punto in cui se ne parla:

- La facade `Neuron` lancia un'eccezione a ogni chiamata. Usa una classe agent generata e associata a un thread (Sezione 17.4).
- `php artisan neuron:node` scrive una classe i cui import non esistono. Correggi due righe a mano (Sezione 17.3).
- Le migration e i model inclusi non sono adatti al message store della 4.0.3 né alla sua persistenza del workflow. Tieni la migration e il model nella tua applicazione (qui sotto, e Capitolo 18).
- Le skill Boost incluse insegnano API che la 4.0.3 ha rimosso. Installa le skill distribuite con il pacchetto core (Sezione 17.7).

Verificato su neuron-ai 4.0.3 e neuron-laravel 2.0.0. Una release successiva dell'SDK può chiudere uno qualunque di questi punti; controlla prima di aggirarli.
:::

La quarta voce dell'elenco del pacchetto è quella su cui agire per prima. `EloquentChatHistory` non esiste più: sulla 4.0.3 una conversazione vive in un message store, `EloquentMessageStore` in Laravel, che identifica ogni riga con un `message_id` e fa affidamento su un indice univoco `(thread_id, message_id)`. La migration `chat_messages` dell'SDK non crea quella colonna, e il suo model `ChatMessage` non la rende fillable. La sua tabella `workflow_store` ha una chiave primaria composta e nessun `id`, quindi `EloquentPersistence` sopra il model `WorkflowStore` dell'SDK non riesce a cancellare i record di una run conclusa, e il secondo messaggio su un thread viene rifiutato. Non pubblicare il tag `neuron-migrations`. Scrivi una migration tua per le due tabelle, e un model `App\Models\ChatMessage` con `thread_id`, `message_id`, `role`, `content` e `meta` fillable. Il Capitolo 18 costruisce entrambi.

### La filosofia, citata

Il README si apre con un'affermazione che vale la pena leggere per intero:

> Neuron non ha bisogno di astrazioni invasive. Ha già una sintassi molto semplice, codice tipizzato al 100% e interfacce chiare su cui puoi fare affidamento per sviluppare il tuo sistema agentico o creare plugin ed estensioni personalizzati.

E:

> In questo pacchetto ti forniamo un kit di sviluppo progettato specificamente per i punti di integrazione con Laravel **senza limitare l'accesso ai componenti nativi di Neuron.** Puoi anche usare questo pacchetto come ispirazione per progettare il tuo pattern di integrazione personalizzato.

Ne derivano tre cose, ed è il motivo per cui la Parte V viene dopo le Parti da II a IV invece che al loro posto:

**Tutto ciò che hai imparato funziona ancora.** Le tue classi agent, i tool, i workflow e le pipeline RAG restano invariati. L'SDK aggiunge punti d'ingresso; non sostituisce l'API.

**L'SDK è opzionale.** La guida dei manutentori stessi a NeuronAI in Laravel, la skill `neuron-laravel-integration` distribuita dentro il pacchetto core (Sezione 17.7), non lo installa mai: richiede `neuron-core/neuron-ai`, aggiunge all'applicazione un service provider, una migration e un model, e tiene le chiavi dei provider in `config/services.php`. Ciò che l'SDK aggiunge sopra sono provider e store costruiti dalla configurazione, e i generatori. La Parte V prende questi dall'SDK e cabla tutto il resto nell'applicazione.

**È un'implementazione di riferimento.** Il pacchetto ti invita esplicitamente a usarlo come ispirazione per la tua integrazione. Se lavori in Symfony, Spryker o un framework interno legacy, leggi il sorgente di questo pacchetto e costruisci l'equivalente — i punti di integrazione sono gli stessi.

Quest'ultimo punto conta se non sei su Laravel. Questa parte è trasferibile.

### Punti chiave

- `composer require neuron-core/neuron-laravel`; Laravel 13 su PHP 8.5; SDK 2.0.0 con neuron-ai 4.0.3.
- Che cosa funziona: config, generatori e le facade di provider, embedding e vector store.
- Che cosa non funziona sulla 4.0.3: la facade `Neuron`, il generatore dei nodi, le migration e i model inclusi, le skill Boost.
- Aggiunge comodità, mai capacità — tutto ciò che viene dalle Parti da II a IV resta invariato.
- Progettato per essere leggibile come modello per altri framework.

## 17.2 Configurazione

### Pubblica la configurazione

```bash
php artisan vendor:publish --tag=neuron-config
```

Produce `config/neuron.php`.

### Variabili d'ambiente

```dotenv
# Support for: anthropic, gemini, openai, openai-responses, mistral, ollama, huggingface, deepseek
NEURON_AI_PROVIDER=anthropic

# Support for: openai, gemini, ollama, voyage, mistral
NEURON_EMBEDDING_PROVIDER=openai

# Support for: file, pinecone, qdrant, meilisearch, chroma
NEURON_STORE_PROVIDER=file

ANTHROPIC_KEY=
ANTHROPIC_MODEL=

GEMINI_KEY=
GEMINI_MODEL=

OPENAI_KEY=
OPENAI_MODEL=

MISTRAL_KEY=
MISTRAL_MODEL=

OLLAMA_URL=
OLLAMA_MODEL=

# And many others
```

::: {.callout .callout-warning}
[Due di queste non hanno un default]{.callout-title}

`config/neuron.php` legge `NEURON_AI_PROVIDER` e `NEURON_EMBEDDING_PROVIDER` senza alcun fallback. Lascia la prima non impostata e `AIProvider::driver()` fallisce con un `TypeError`, `AIProviderManager::getDefaultDriver(): Return value must be of type string, null returned`, che non nomina la variabile mancante. `EmbeddingProvider::driver()` fallisce allo stesso modo senza la seconda, e l'elenco del README stesso non la menziona mai. Impostale entrambe. `NEURON_STORE_PROVIDER` è opzionale e ha `file` come fallback.
:::

Più, per il tracing:

```dotenv
INSPECTOR_INGESTION_KEY=fwe45gtxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Il README presenta quella chiave come tutto ciò che serve. Non è così. Il framework core non dipende da Inspector e non aggancia alcun observer da solo: il tracing è un listener PSR-14 che sottoscrivi esplicitamente (Capitolo 10). In Laravel significa richiedere `inspector-apm/inspector-laravel` e, per nome, `inspector-apm/inspector-php` alla `^3.19` (le release 3.18 precedenti contengono un subscriber che sulla 4.0.3 non registra nulla), mantenere la chiave qui sopra e sottoscrivere l'`InspectorSubscriber` di Inspector a `ObservabilityEvent` sugli agent che vuoi tracciare — in una classe base condivisa o dovunque il tuo container costruisca gli agent, così che nessuno sfugga. Una chiave senza sottoscrizione non produce tracce, e nessun errore che te lo segnali.

### Questa è la Sezione 3.6, fatta dal framework

Nella Parte II hai costruito `ProviderFactory` a mano — un'istruzione `match` che mappa il nome di un driver su un provider configurato. L'SDK è quello, come servizio Laravel di prima classe.

Stessa idea, stessi benefici: nomi dei vendor in un posto solo, scelta del provider come configurazione, sviluppo locale gratuito con Ollama, stratificazione dei costi come modifica di configurazione.

Avendo costruito tu stesso la factory, sai esattamente che cosa sta facendo l'SDK. È una posizione molto migliore che trattarlo come magia.

### Configurazione specifica per ambiente

Il pattern Laravel naturale, e uno degli argomenti pratici più forti a favore dell'SDK:

```dotenv
# .env.local — free, offline, no rate limits
NEURON_AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434/api
OLLAMA_MODEL=qwen2.5:7b
```

```dotenv
# .env.staging — cheap, real, good enough for QA
NEURON_AI_PROVIDER=openai
OPENAI_MODEL=gpt-4.1-mini
```

```dotenv
# .env.production
NEURON_AI_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-sonnet-4-5
```

Un codebase, tre profili di costo, zero modifiche al codice.

::: {.callout .callout-warning}
[Un'eccezione, riportata dalla Sezione 12.4]{.callout-title}

Il provider e il modello di *embedding* non devono variare per ambiente. Embedding diversi significano indici vettoriali incompatibili. Fissali entrambi in `config/neuron.php` invece di lasciarli a `.env`, o prima o poi ti troverai a debuggare un sistema RAG che restituisce sciocchezze solo in staging.
:::

### System prompt in configurazione

Il README mostra il system prompt che arriva dalla configurazione:

```php
public function instructions(): string
{
    return (string) new SystemPrompt(...config('neuron.system_prompt'));
}
```

Utile per un assistente di default. **Non** è il pattern giusto per un agent reale — un prompt è una specifica (Sezione 3.5), e le specifiche stanno nel codice, sotto controllo di versione, revisionate. Un file di configurazione che un deploy può cambiare senza una code review è la casa sbagliata per il comportamento.

Usalo per il default generato; dichiara le istruzioni nella classe agent per tutto ciò che conta.

::: {.callout .callout-warning}
[Due problemi in quello snippet del README]{.callout-title}

L'esempio pubblicato recita `return (string) new SystemPrompt(...config('neuron.system_prompt');` — manca una parentesi di chiusura. Usa inoltre `use NeuronAI\Agent;` e `use NeuronAI\SystemPrompt;`, che sono namespace di versioni precedenti. Le classi sono `NeuronAI\Agent\Agent` e `NeuronAI\Agent\SystemPrompt`.
:::

Il tipo di ritorno stringa è corretto. La firma del framework è `instructions(): SystemMessage|string` — un `SystemMessage` ti permette di dividere le istruzioni in blocchi e marcare quello statico per il prompt caching — ma una stringa semplice viene accettata e incapsulata per te, e restringere il tipo di ritorno a `string` nella tua classe è legale. Lo è anche allargare il metodo da `protected` a `public`, come fa il README. La classe che genera `neuron:agent` (Sezione 17.3) fa entrambe le cose.

### Punti chiave

- `vendor:publish --tag=neuron-config`, poi le variabili d'ambiente; `NEURON_AI_PROVIDER` e `NEURON_EMBEDDING_PROVIDER` non hanno un default.
- Questa è la `ProviderFactory` della Sezione 3.6, fornita già pronta.
- Varia il provider per ambiente; **mai** il modello di embedding.
- Tieni i system prompt veri nel codice, non in configurazione.

## 17.3 Generatori Artisan

### I comandi

```bash
# Create an agent
php artisan neuron:agent MyAgent

# Create a RAG
php artisan neuron:rag MyRAG

# Create a tool
php artisan neuron:tool MyTool

# Create a workflow
php artisan neuron:workflow MyWorkflow

# Create a node
php artisan neuron:node CustomNode

# Create a middleware
php artisan neuron:middleware CustomMiddleware
```

`php artisan neuron:agent MyAgent` crea `app/Neuron/Agents/MyAgent.php` con i metodi di base già abbozzati. Gli stub di agent, tool, workflow e middleware corrispondono all'API della 4.0.3: il tool generato, per esempio, dichiara la propria identità come proprietà `protected string $name` e `protected ?string $description` senza costruttore, la forma che il Capitolo 19 usa ovunque. Lo stub del RAG lascia i suoi tre hook commentati, da riempire. Lo stub del nodo, così come viene generato, non funziona.

::: {.callout .callout-warning}
[`neuron:node` genera import che non esistono]{.callout-title}

Lo stub del nodo nell'SDK 2.0.0 importa `NeuronAI\Workflow\StartEvent` e `NeuronAI\Workflow\StopEvent`. Entrambe le classi vivono in `NeuronAI\Workflow\Events\`. Il file generato supera il parsing, e il primo workflow che esegue il nodo fallisce con `Failed to validate App\Neuron\Nodes\CustomNode: First parameter of __invoke method must be a type that implements NeuronAI\Workflow\Events\Event`. Correggi le due righe `use` dopo la generazione:

```php
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
```
:::

### Meglio della CLI del core, in un aspetto preciso

Confronta con la Sezione 3.3:

```bash
# Core package — full namespace, doubled backslashes on Unix
./vendor/bin/neuron make:agent App\\Agents\\AssistantAgent

# Laravel SDK — just the name
php artisan neuron:agent MyAgent
```

Niente namespace, niente escape dei backslash, nessuna differenza fra sistemi operativi. L'SDK conosce la struttura della tua applicazione.

È una piccola cosa che elimina un attrito reale — la differenza Unix/Windows sui backslash del Capitolo 3 genera confusione autentica, e qui semplicemente non esiste.

### Una struttura di progetto suggerita

I generatori mettono gli agent in `app/Neuron/Agents`. Estendi la convenzione:

```
app/Neuron/
├── Agents/          SupportAgent, ResearchAgent, ReviewerAgent
├── Tools/           SearchOrdersTool, RequestRefundTool
├── Workflows/       ContentWorkflow
│   ├── Nodes/
│   └── Events/
├── Middleware/
├── Dto/             Verdict, Invoice, RefundRequest
└── Rag/             KnowledgeBaseAgent
```

Un solo namespace che contiene tutto ciò che è agentico. Uno sviluppatore nuovo apre `app/Neuron` e vede l'intera superficie AI dell'applicazione, invece di trovare un agent in `app/Services`, un tool in `app/Support` e un DTO in `app/Http/Resources`.

I generatori non concordano tutti con questo albero così come escono dalla scatola — `neuron:tool` scrive in `app/Neuron/Agents/Tools`, `neuron:node` in `app/Neuron/Nodes` e `neuron:rag` in `app/Neuron/RAG`. Sposta i file una volta, o passa al comando il nome di classe completamente qualificato; in ogni caso, decidi l'albero prima del decimo file, non dopo.

### Punti chiave

- Sei generatori, tutti `php artisan neuron:*`.
- Solo il nome — niente namespace, niente escape, nessuna differenza di sistema operativo.
- Correggi i due import in ogni classe generata da `neuron:node`.
- Tieni tutto ciò che è agentico sotto `app/Neuron`.

## 17.4 La facade Neuron, e che cosa usare al suo posto

### Perché esiste

L'autore del framework descrive il problema onestamente:

> Prima di questa release, usare Neuron AI dentro Laravel significava creare una classe agent dedicata, estendere `Agent`, implementare un metodo `provider()` e cablare a mano il system prompt. Quel pattern è quello giusto una volta che il tuo agent ha una personalità, un insieme di tool e un ruolo nella tua applicazione. Ma è un sacco di cerimonia per uno sviluppatore che vuole solo verificare se Claude, o GPT, o Gemini rispondono bene a un dato prompt.

Una facade è la risposta di Laravel a quella forma di problema, e questo è un uso da manuale. Su neuron-ai 4.0.3 è anche l'unica parte dell'SDK che non puoi chiamare.

::: {.callout .callout-warning}
[La facade `Neuron` lancia un'eccezione su neuron-ai 4.0.3]{.callout-title}

Un agent viene eseguito solo dopo che gli è stato associato un thread ID (Sezione 3.4). La facade dell'SDK 2.0.0 costruisce il suo agent con un semplice `Agent::make()` e non offre alcun modo di associarne uno, quindi `Neuron::chat()`, `Neuron::stream()` e `Neuron::structured()` falliscono tutti con `AgentException: This agent has no thread ID: bind one with setThreadId() first.`, con o senza `tools()` e `middleware()` nella catena. L'alternativa funzionante è quella che la citazione chiama cerimonia, una classe agent dedicata, e il generatore riduce la cerimonia a un solo comando. Il resto di questa sezione la usa.
:::

### Le tre modalità

```bash
php artisan neuron:agent AssistantAgent
```

La classe generata non ha bisogno di modifiche per fare le veci della facade. Il suo `provider()` restituisce `AIProvider::driver()`, il default configurato, e il suo `instructions()` costruisce il system prompt da `config/neuron.php`: le due cose che la facade legge. Risolvila dal container, associala a un thread e chiamala:

```php
use App\Neuron\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

// The container builds the agent; for() returns a copy bound to one thread
$agent = app(AssistantAgent::class)->for($threadId);

// Chat (synchronous) — returns the final AgentState
$response = $agent->chat(new UserMessage('Hello!'))->getMessage();
echo $response?->getContent();

// Stream (real-time chunks) — the call itself is the generator
foreach ($agent->stream(new UserMessage('Hello')) as $chunk) {
    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}

// Structured output
$person = $agent->structured(new UserMessage('I am John and I like pizza!'), Person::class);
```

Gli stessi tre punti d'ingresso della tabella della Sezione 6.3 — `chat()`, `stream()`, `structured()` — con un solo file generato alle spalle: `chat()` va fino in fondo e restituisce l'`AgentState`, `stream()` è un generatore su cui iteri direttamente, `structured()` restituisce l'oggetto. `getMessage()` è nullable, da cui il `?->`. Non portarti dietro sulla classe il ciclo di streaming del README: chiama `->events()` sul risultato e stampa `$event->content`, ma `stream()` restituisce il generatore stesso e produce diversi tipi di chunk, quindi filtra per `TextChunk` come sopra.

`$threadId` è l'argomento che la facade non chiede mai. Dà un nome alla conversazione a cui appartiene la chiamata: una qualunque stringa nuova per una domanda isolata, l'ID della conversazione stessa quando l'utente ci torna. `for()` restituisce una copia dell'agent associata a quel thread ed è l'argomento della Sezione 17.5; da dove arrivano i thread ID, e che cosa viene memorizzato sotto di essi, è materia del Capitolo 18. `AssistantAgent::make()->setThreadId(...)` della Parte II funziona anche in Laravel, ma lascia che sia il container a costruire l'agent: dal Capitolo 18 in poi ha dipendenze nel costruttore. In un controller, ricevi l'agent come parametro del metodo invece di chiamare `app()`.

### Agganciare i tool

```php
$response = app(AssistantAgent::class)->for($threadId)
    ->addTool(new SearchTool())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

$response = app(AssistantAgent::class)->for($threadId)
    ->addTool([new SearchTool(), CalculatorToolkit::make()])
    ->chat(new UserMessage('Hello!'))
    ->getMessage();
```

Istanza singola o array. `addTool()` aggiunge a ciò che restituisce l'hook `tools()` della classe, solo su questa copia associata.

### Agganciare i middleware

```php
use App\Neuron\Middleware\AuditTrail;
use NeuronAI\Agent\Nodes\ChatNode;
use NeuronAI\Agent\Nodes\ToolNode;

// Record every tool execution in the audit log
$response = app(AssistantAgent::class)->for($threadId)
    ->addMiddleware(ToolNode::class, new AuditTrail())
    ->chat(new UserMessage('Summarise yesterday\'s orders'))
    ->getMessage();

// Both arguments accept arrays
$agent = app(AssistantAgent::class)->for($threadId)
    ->addMiddleware([ChatNode::class, ToolNode::class], [new AuditTrail()]);
```

`AuditTrail` è una tua classe — `php artisan neuron:middleware AuditTrail` la genera con gli hook `before()` e `after()` vuoti da riempire.

**Ecco le classi dei nodi, in un namespace reale:** `NeuronAI\Agent\Nodes\ChatNode`, `ToolNode`, `StructuredOutputNode`.

Ogni modalità di interazione è sostenuta da un nodo: `ChatNode` esegue l'inferenza sia per `chat()` sia per `stream()`, `StructuredOutputNode` per `structured()`, e `ToolNode` esegue i tool. Il README elenca ancora un `StreamingNode` separato per `stream()`; una classe del genere non esiste, e un middleware agganciato a esso non verrebbe mai eseguito.

**Questa è la Sezione 2.3 riscossa fino in fondo.** Non puoi usare questa API senza sapere che un agent è un workflow di nodi con un nome. Quell'affermazione, fatta il secondo giorno del libro, è ciò su cui questa API è costruita.

### L'approvazione non è un middleware

L'esempio di middleware del README stesso aggancia un middleware `ToolApproval` a `ToolNode`. Quella classe appartiene alle versioni precedenti e non esiste più. L'approvazione appartiene a `ToolNode` stesso e si configura sul tool — il tool dichiara il proprio rischio, e puoi imporla o revocarla nel punto in cui lo agganci (Sezione 19.3):

```php
$state = app(AssistantAgent::class)->for($threadId)
    ->addTool(DeleteLogFileTool::make()->requireApproval())
    ->chat(new UserMessage('Delete the oldest log file'));

$state->isInterrupted();   // true — the run paused before deleting anything
```

L'agent si mette in pausa correttamente. Ciò che questo non sa fare è *proseguire*: la run in pausa e la sua conversazione sono tenute nella memoria del processo, ed entrambe spariscono quando la richiesta finisce. Riprendere in una richiesta successiva richiede un message store durevole e la persistenza del workflow, e il Capitolo 18 li aggiunge. L'approvazione è l'esempio più chiaro del punto successivo.

### Quando spostarla nella classe

Il README traccia la sua linea fra la facade e una classe:

> Per memoria personalizzata, middleware multipli o comportamenti dell'agent più avanzati, crea una classe agent dedicata usando `php artisan neuron:agent`.

La classe ce l'hai già, quindi la linea passa invece al suo interno: fra ciò che agganci nel punto in cui l'agent viene chiamato, come sopra, e ciò che la classe dichiara nei suoi hook. Vale la pena aggiungere altri quattro inneschi:

- L'agent deve **mettersi in pausa e riprendere** — approvazione dei tool, o qualunque altra interruzione
- L'agent ha bisogno di un **nome** — `SupportAgent`, non `AssistantAgent`: qualcosa che un collega possa trovare e su cui possa ragionare
- L'agent ha bisogno di **test**
- La configurazione dell'agent compare in **più di un posto**

La configurazione nel punto di chiamata è per prototipi, funzionalità interne una tantum e script di amministrazione. Gli hook di una classe con un nome sono per tutto ciò che ha un ruolo nella tua applicazione. Il Pattern A contro il Pattern B della Sezione 2.4, in abito Laravel.

### Punti chiave

- La facade `Neuron` lancia un'eccezione su neuron-ai 4.0.3: il suo agent non riceve mai un thread ID. La sostituisce una classe agent generata e associata con `for()`.
- `chat()`, `stream()`, `structured()` — gli stessi punti d'ingresso e tipi di ritorno di qualunque classe agent.
- `addTool()` e `addMiddleware()` si concatenano alla copia associata.
- Le classi dei nodi vivono in `NeuronAI\Agent\Nodes\`; `ChatNode` serve sia `chat()` sia `stream()`.
- L'approvazione vive sul tool, non in un middleware — e riprendere una run in pausa richiede gli store durevoli del Capitolo 18.
- Sposta la configurazione nella classe quando l'agent deve riprendere, ha bisogno di un nome o di test, o è configurato due volte.

## 17.5 Copiare, non mutare: la storia di concorrenza dell'agent

### Il problema che risolve

Il container ti consegna un agent, e in un runtime a lunga vita — Octane, Swoole, RoadRunner, un queue worker — un oggetto può sopravvivere alla richiesta che lo ha chiesto. Registrato come singleton lo fa sempre; tenuto in una proprietà di un servizio a lunga vita lo fa per sbaglio.

Ora considera che cosa fa a un'istanza del genere un binding per mutazione:

```php
// Request A
$agent->setThreadId($aliceThread)
    ->addTool(new AdminDeleteTool())
    ->chat(...);

// Request B, milliseconds later, different user, same instance
$agent->chat(...);  // ...whose conversation is this, and does it have the admin tool?
```

`setThreadId()` e `addTool()` modificano l'oggetto su cui vengono chiamati, quindi entrambe le risposte sono quella sbagliata: la richiesta B gira sul thread di Alice, con i suoi messaggi nel prompt e il tool di amministrazione a disposizione. È una fuga di dati e di privilegi fra richieste che compare solo sotto Octane, solo qualche volta, ed è estremamente sgradevole da diagnosticare. A una richiesta B che associ prima il proprio thread non va molto meglio: riceve una `WorkflowException`, perché un agent già associato non può essere puntato su un altro thread.

### Il progetto

`for()` è la risposta del framework, e il commento sul metodo ne enuncia il contratto:

> Una copia associata a $workflowId; il ricevente non viene mai modificato.

Per un agent, il workflow ID è il thread ID. Dimostrato:

```php
$response = $agent->for($threadId)
    ->addTool(new SearchTool())
    ->addMiddleware(ToolNode::class, new AuditTrail())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

// $agent is untouched — no thread, no tools, no middleware
$agent->for($otherThreadId)->chat(new UserMessage('Hello!'));
```

La classe della facade dell'SDK è scritta secondo la stessa regola, e il suo README spiega perché:

> La facade risolve un **singleton**, quindi i metodi di configurazione non mutano mai l'istanza condivisa — restituiscono una copia fresca e indipendente che concateni nella chiamata.

La facade ha il progetto giusto e le manca solo il thread. `for()` ha entrambi.

### Perché merita una sezione tutta sua

Due ragioni.

**È una proprietà di sicurezza, non una comodità.** In un deploy PHP-FPM senza stato il bug sarebbe invisibile. Sotto Octane sarebbe una fuga di dati. Il progetto anticipa il modello di deploy che sta diventando normale.

**È un pattern che vale la pena rubare.** Configurazione immutabile per default su un servizio condiviso — `withX()` che restituisce un clone invece di `setX()` che muta — è buona progettazione in generale, e la maggior parte degli sviluppatori PHP ha scritto la versione mutante almeno una volta.

Il principio generale: **un servizio condiviso dovrebbe distribuire copie configurate, non lasciare che i chiamanti lo riconfigurino.**

### La regola pratica

Poiché `for()` restituisce una copia e lascia intatto il ricevente, associare su un'istruzione e chiamare su quella dopo non fa nulla:

```php
// This does NOT work as it appears to
$agent->for($threadId);
$agent->chat(new UserMessage('...'));  // AgentException — $agent still has no thread
```

```php
// Chain it, or hold the copy
$bound = $agent->for($threadId);
$bound->chat(new UserMessage('...'));  // runs on $threadId
```

Semplice una volta detto, e cinque minuti di confusione se non lo è.

L'altra metà della regola riguarda dove vanno i setter. `addTool()` e `addMiddleware()` continuano a modificare l'oggetto su cui vengono chiamati, quindi chiamali sulla copia restituita da `for()`, mai sull'istanza che ti ha dato il container. E, tanto per cominciare, non registrare l'agent come singleton; il Capitolo 18 mostra come il container dovrebbe costruirlo.

### Punti chiave

- `for()` restituisce una copia associata a un thread; l'agent costruito dal container non viene mai modificato.
- Previene fughe fra richieste sotto Octane, Swoole e RoadRunner.
- Concatena la chiamata o tieni la copia restituita — `for()` su una riga a sé non associa nulla.
- `addTool()` e `addMiddleware()` vanno sulla copia, non sull'istanza del container.
- Vale la pena rubarlo come pattern generale per i servizi condivisi.

## 17.6 Facade dei componenti

### Tre facade

```php
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
```

Ciascuna espone `driver()`:

```php
class YouTubeAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver('anthropic');
    }
}
```

Forma familiare — lo stesso pattern `driver()` di `Cache::driver()`, `Queue::connection()` e `Storage::disk()`. È deliberato, ed è il motivo per cui non richiede spiegazioni a un pubblico Laravel. Sotto sono normali manager di Laravel, quindi `extend()` registra un driver tuo — la Sezione 20.1 dice a quali store si addice. Un'avvertenza prima di farlo: l'SDK registra come singleton i manager dei provider e degli embedding ma non `VectorStoreManager`, quindi un driver aggiunto con `VectorStore::extend()` finisce su un'istanza che solo la facade possiede. Sparisce quando la cache della facade viene svuotata, e `app(VectorStoreManager::class)` non lo vede mai. Registra tu il manager, con `$this->app->singleton(VectorStoreManager::class)` in un service provider, prima di estenderlo.

### Un agent RAG, completamente configurato

```php
namespace App\Neuron;

use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class MyChatBot extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver('anthropic');
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return EmbeddingProvider::driver('openai');
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return VectorStore::driver('file');
    }
}
```

Confronta con la versione in PHP puro della Sezione 12.1: tre costruttori con chiavi, modelli, directory e nomi. Qui, tre nomi di driver, tutto il resto in configurazione.

I driver di vector store inclusi sono `file`, `pinecone`, `qdrant`, `meilisearch` e `chroma`. Uno store costruito da `config/neuron.php` non ha uno schema dei documenti, il che significa che memorizza i tuoi metadati ma non può *filtrare* su di essi — il filtraggio richiede che i campi siano dichiarati in anticipo. Conta nel momento in cui arriva un secondo tenant, e il Capitolo 20 costruisce il suo store di conseguenza.

### Con nome contro default

```php
// Explicit driver
AIProvider::driver('anthropic');

// Configured default — NEURON_AI_PROVIDER
AIProvider::driver();
```

**Preferisci il default** per la maggior parte degli agent. Nominare il driver nella classe reintroduce esattamente l'accoppiamento che la Sezione 3.6 aveva rimosso — e rompe silenziosamente la configurazione per ambiente della Sezione 17.2, perché un agent che scrive `'anthropic'` a codice chiamerà Anthropic in sviluppo locale a prescindere da ciò che dice `.env.local`. Il default dipende però dal fatto che `NEURON_AI_PROVIDER` sia impostata: senza, `driver()` è il `TypeError` della Sezione 17.2.

Nomina il driver solo quando questo agent specifico richiede genuinamente quel provider specifico — un modello economico per un nodo classificatore, un modello con capacità visive per l'estrattore di fatture.

### Stratificazione dei costi, in Laravel

La scelta del modello per agent della Sezione 16.1, espressa in modo pulito:

```php
class ClassifierAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver('ollama');   // free, local, good enough
    }
}

class WriterAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();          // the configured default
    }
}
```

Una riga per agent decide dove finiscono i soldi in un sistema multi-agente.

Ciò che il manager non sa fare è dare a due agent lo stesso driver con impostazioni diverse. Tiene una sola configurazione per driver e mette in cache ciò che costruisce, quindi ogni agent che chiede `'anthropic'` riceve lo stesso oggetto provider: un modello, un insieme di parametri, un client HTTP. Quando a un agent serve un provider tutto suo — un secondo modello dello stesso vendor, un client con un timeout proprio — costruiscilo dentro il `provider()` di quell'agent a partire da `config('neuron.provider.anthropic')`. Il framework chiama l'hook da capo a ogni segmento di esecuzione, e la skill Laravel dei manutentori (Sezione 17.7) costruisce così il provider di ogni agent.

### Punti chiave

- `AIProvider`, `EmbeddingProvider`, `VectorStore` — tutte con `driver()`.
- Stesso idioma di `Cache::driver()`; nessuna spiegazione necessaria.
- Preferisci `driver()` senza argomenti così che la configurazione per ambiente continui a funzionare.
- Nomina un driver solo quando quell'agent lo richiede davvero.
- Il manager condivide un solo provider per driver; costruisci il provider nell'hook quando a un agent ne serve uno suo.

## 17.7 Laravel Boost e lo sviluppo assistito dall'AI

### Che cosa viene incluso

Il pacchetto include **linee guida per assistenti di codice AI integrate con Laravel Boost**, per aiutare gli assistenti a scrivere codice NeuronAI migliore. Arrivano come un insieme di skill Boost — una ciascuna per agent, tool, approvazione dei tool, workflow, RAG, streaming, structured output, testing, valutazione, monitoraggio e integrazione frontend.

Perché conta: l'ecosistema contiene una grande quantità di materiale vecchio. Un assistente di codice addestrato su codice pubblico produrrà con sicurezza codice scritto per versioni precedenti: `use NeuronAI\Agent;`, `new Edge(...)`, `Tool::make(...)->setCallable(...)`, un middleware `ToolApproval`, `->events()` su uno stream.

Distribuire linee guida insieme al pacchetto è una correzione diretta: l'assistente legge ciò che è vero adesso invece di ciò che era vero due anni fa. Vale esattamente finché le linee guida tengono il passo del codice, e nell'SDK 2.0.0 non l'hanno tenuto.

::: {.callout .callout-warning}
[Le skill Boost incluse insegnano API rimosse]{.callout-title}

Le skill di neuron-laravel 2.0.0 insegnano ancora `MyAgent::make(threadId: ...)`, `setChatHistory()` con `SQLChatHistory` o `EloquentChatHistory`, `$workflow->resume()` e `abandonRun()`. Niente di tutto questo esiste in neuron-ai 4.0.3, e un assistente che segue quelle skill scrive codice che fallisce alla prima chiamata. Le skill aggiornate sono le tredici del pacchetto core, sotto `vendor/neuron-core/neuron-ai/skills/`: gli stessi undici argomenti, più `neuron-laravel-integration` e `neuron-symfony-integration`. Installa quelle, con il comando indicato dal README del framework:

```bash
npx skills add ./vendor/neuron-core/neuron-ai/skills -y
```
:::

`neuron-laravel-integration` è quella da leggere accanto al resto della Parte V. È il resoconto dei manutentori stessi su come cablare NeuronAI in un'applicazione Laravel 13: il container, le tabelle, l'autorizzazione dei thread, le queue, lo streaming, i test. I capitoli che seguono vi si appoggiano.

### L'idea più ampia

È un pattern da notare più che una semplice funzionalità: **una libreria che distribuisce istruzioni per gli strumenti che scrivono codice contro di essa.**

Se mantieni pacchetti, quell'idea ha valore immediato — quando gli assistenti dei tuoi utenti generano codice sbagliato contro la tua libreria, quello è il tuo carico di supporto.

Se stai costruendo sistemi agentici, chiude un cerchio attorno a cui questo libro gira da un pezzo: puoi collegare la documentazione di NeuronAI a un assistente di codice tramite un server MCP (Capitolo 9), e usare agent per aiutarti a costruire agent.

### L'avvertenza onesta

Mantieni un inquadramento sobrio. Gli assistenti restano sicuri di sé e sbagliati sulle librerie che si muovono in fretta, e perfino la *documentazione ufficiale* si è discostata dal codice in decine di punti. Un assistente che legge quella documentazione eredita la deriva.

Nemmeno le linee guida incluse ne sono immuni, e questo capitolo ne è la prova: le skill dell'SDK sono già rimaste indietro rispetto al framework che descrivono. La skill di approvazione dei tool dell'SDK, per di più, dice all'assistente di dichiarare `approvalPolicy(array $inputs)`; la classe `Tool` dichiara `approvalPolicy()` senza parametri e legge gli input tramite `getInput()`. Un assistente che segue la skill scrive un metodo che PHP rifiuta come override incompatibile. Il README del pacchetto stesso, come questo capitolo ha mostrato, contiene ancora esempi scritti per una versione precedente. Le linee guida abbassano il tasso di errore; non eliminano il bisogno di verificare.

La disciplina: usa gli assistenti per scaffolding e boilerplate; verifica qualunque cosa tocchi la superficie dell'API contro la versione che hai installato. È la stessa abitudine che questo libro applica dall'inizio, e si trasferisce ben oltre NeuronAI. Il Capitolo 27 va oltre.

### Punti chiave

- Il pacchetto distribuisce linee guida per gli assistenti di codice come skill di Laravel Boost.
- Esiste perché il corpus pubblico è pieno di codice scritto per versioni precedenti.
- Anche le linee guida possono andare alla deriva: nell'SDK 2.0.0 insegnano API che la 4.0.3 ha rimosso.
- Usa le skill in `vendor/neuron-core/neuron-ai/skills/`, fra cui `neuron-laravel-integration`.
- Buon pattern per i manutentori di librerie in generale.
- Verifica il codice generato contro la tua versione installata — sempre.

## Laboratorio 11 — Cinque minuti alla prima risposta

**Copre:** la configurazione, il generatore di agent, l'associazione di un thread e il sapere quando la configurazione va nella classe.

### Obiettivo

Un endpoint `POST /api/ask` funzionante, servito da una classe agent generata, da `composer require` alla prima risposta in circa cinque minuti. Poi la metà più interessante: individuare il punto esatto in cui configurare l'agent nel controller smette di essere lo strumento giusto.

### Parte prima — falla funzionare

1. Installa l'SDK e pubblica la configurazione.
2. Imposta `NEURON_AI_PROVIDER=ollama` in `.env`, con `OLLAMA_MODEL` che indica un modello che hai già scaricato, così che non costi nulla.
3. Esegui `php artisan neuron:agent AssistantAgent` e lascia la classe generata così com'è.
4. Scrivi un controller che legge `message` dalla richiesta, associa l'agent a un thread e ne restituisce la risposta, e una route verso di esso in `routes/api.php` (`php artisan install:api` crea quel file se la tua applicazione non ce l'ha).
5. Conferma che funziona con `curl`.

Questa è tutta la prima parte, e dovrebbe richiedere davvero pochi minuti. Il controller è di tre istruzioni:

```php
namespace App\Http\Controllers;

use App\Neuron\Agents\AssistantAgent;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\UniqueIdGenerator;

class AskController extends Controller
{
    public function __invoke(Request $request, AssistantAgent $agent): JsonResponse
    {
        $data = $request->validate(['message' => ['required', 'string']]);

        $state = $agent
            ->for(UniqueIdGenerator::generateId('ask_'))
            ->chat(new UserMessage($data['message']));

        return response()->json(['answer' => $state->getMessage()?->getContent()]);
    }
}
```

```bash
curl -s http://localhost:8000/api/ask \
    -H 'Accept: application/json' \
    -d 'message=How do I implement a PSR-15 middleware without a framework?'
```

Laravel risolve `AssistantAgent` dal container perché il metodo lo chiede. L'endpoint risponde a domande singole, quindi ogni richiesta conia un thread ID nuovo e nulla sopravvive alla risposta. Il giorno in cui un utente dovrà poter fare una domanda successiva, il thread dovrà arrivare da qualche parte e la conversazione dovrà vivere da qualche parte: è il Capitolo 18.

### Parte seconda — rompila deliberatamente

Ora aggiungi i requisiti uno alla volta, e annota dove ciascuno comincia a far male:

1. **L'endpoint ha bisogno di un system prompt specifico per il tuo prodotto.** Configurazione, o codice?
2. **Gli serve un tool.** Ti trovi ancora a tuo agio nel controller?
3. **Gli serve un test.** Come metti un fake provider dietro l'endpoint?
4. **Un secondo endpoint ha bisogno della stessa configurazione.** Dove vive adesso?

Al terzo o quarto requisito dovresti stare spostando le cose fuori dal controller e dentro la classe: il prompt in `instructions()`, il tool in `tools()`. È quella la lezione — non che configurare nel punto di chiamata sia sbagliato, ma che puoi sentire esattamente quando smette di andarti bene.

### Criteri di accettazione

- `POST /api/ask` restituisce una risposta sensata con `NEURON_AI_PROVIDER=ollama` e nessuna chiave API configurata.
- Passare a un provider cloud richiede solo una modifica a `.env`.
- Sai dire, in una frase, quale dei quattro requisiti qui sopra ha spinto la configurazione dentro la classe.

### Una trappola da evitare

Non associare su un'istruzione e chiamare su quella dopo — Sezione 17.5. Se il tuo controller chiama `$agent->for(...)` su una riga e `$agent->chat(...)` su quella dopo, la copia associata viene buttata via e la chiamata fallisce con `AgentException: This agent has no thread ID`. Scrivilo come una catena unica. Quando arrivi al requisito due, il tool entra in quella catena dopo `for()`; conferma che venga davvero offerto.
