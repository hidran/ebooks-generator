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

**Requisiti:** PHP >= 8.2, Laravel >= 10. Tira dentro `neuron-core/neuron-ai` ^3.15.

Nota che la soglia minima di versione è più alta del PHP 8.1 del pacchetto core. Se sei su 8.1, usi direttamente il pacchetto core — cosa che, dopo le Parti da II a IV, sai già fare.

### Che cosa fornisce

Cinque cose, dalla descrizione del pacchetto stesso:

- Un file di configurazione per le credenziali del provider AI e degli embedding
- Comandi Artisan per generare lo scheletro dei componenti più usati
- Facade che istanziano provider e vector store dalla configurazione
- Migration pronte all'uso per `EloquentChatHistory`
- Linee guida per assistenti di codice AI integrate con Laravel Boost

### La filosofia, citata

Il README si apre con un'affermazione che vale la pena leggere per intero:

> Neuron non ha bisogno di astrazioni invasive. Ha già una sintassi molto semplice, codice tipizzato al 100% e interfacce chiare su cui puoi fare affidamento per sviluppare il tuo sistema agentico o creare plugin ed estensioni personalizzati.

E:

> In questo pacchetto ti forniamo un kit di sviluppo progettato specificamente per i punti di integrazione con Laravel **senza limitare l'accesso ai componenti nativi di Neuron.** Puoi anche usare questo pacchetto come ispirazione per progettare il tuo pattern di integrazione personalizzato.

Ne derivano tre cose, ed è il motivo per cui la Parte V viene dopo le Parti da II a IV invece che al loro posto:

**Tutto ciò che hai imparato funziona ancora.** Le tue classi agent, i tool, i workflow e le pipeline RAG restano invariati. L'SDK aggiunge punti d'ingresso; non sostituisce l'API.

**L'SDK è opzionale.** Puoi fare `composer require neuron-core/neuron-ai` in un'app Laravel e cablare il container da solo. L'SDK ti risparmia un pomeriggio.

**È un'implementazione di riferimento.** Il pacchetto ti invita esplicitamente a usarlo come ispirazione per la tua integrazione. Se lavori in Symfony, Spryker o un framework interno legacy, leggi il sorgente di questo pacchetto e costruisci l'equivalente — i punti di integrazione sono gli stessi.

Quest'ultimo punto conta se non sei su Laravel. Questa parte è trasferibile.

### Punti chiave

- `composer require neuron-core/neuron-laravel`; PHP 8.2+, Laravel 10+.
- Config, generatori, facade, migration, linee guida Boost.
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

Più, per il tracing:

```dotenv
INSPECTOR_INGESTION_KEY=fwe45gtxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

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

Il modello di *embedding* non deve variare per ambiente. Embedding diversi significano indici vettoriali incompatibili. Fissalo in `config/neuron.php` invece di lasciarlo a `.env`, o prima o poi ti troverai a debuggare un sistema RAG che restituisce sciocchezze solo in staging.
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

Usalo per il default della facade; dichiara le istruzioni nella classe agent per tutto ciò che conta.

::: {.callout .callout-warning}
[Due problemi in quello snippet del README]{.callout-title}

L'esempio pubblicato recita `return (string) new SystemPrompt(...config('neuron.system_prompt');` — manca una parentesi di chiusura. Usa inoltre `use NeuronAI\Agent;` e `use NeuronAI\SystemPrompt;`, che sono **namespace v2**. In v3 sono `NeuronAI\Agent\Agent` e `NeuronAI\Agent\SystemPrompt`. Appendice A, punti 39 e 40.
:::

### Punti chiave

- `vendor:publish --tag=neuron-config`, poi le variabili d'ambiente.
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

`php artisan neuron:agent MyAgent` crea `app/Neuron/Agents/MyAgent.php` con i metodi di base già abbozzati.

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

### Punti chiave

- Sei generatori, tutti `php artisan neuron:*`.
- Solo il nome — niente namespace, niente escape, nessuna differenza di sistema operativo.
- Tieni tutto ciò che è agentico sotto `app/Neuron`.

## 17.4 La facade Neuron

### Perché esiste

L'autore del framework descrive il problema onestamente:

> Prima di questa release, usare Neuron AI dentro Laravel significava creare una classe agent dedicata, estendere `Agent`, implementare un metodo `provider()` e cablare a mano il system prompt. Quel pattern è quello giusto una volta che il tuo agent ha una personalità, un insieme di tool e un ruolo nella tua applicazione. Ma è un sacco di cerimonia per uno sviluppatore che vuole solo verificare se Claude, o GPT, o Gemini rispondono bene a un dato prompt.

Una facade è la risposta di Laravel a quella forma di problema, e questo è un uso da manuale.

### Le tre modalità

```php
use NeuronAI\Laravel\Facades\Neuron;
use NeuronAI\Chat\Messages\UserMessage;

// Chat (synchronous)
$response = Neuron::chat(new UserMessage('Hello!'))->getMessage();
echo $response->getContent();

// Stream (real-time chunks)
foreach (Neuron::stream(new UserMessage('Hello'))->events() as $event) {
    echo $event->content;
}

// Structured output
$person = Neuron::structured(new UserMessage('I am John and I like pizza!'), Person::class);
```

Gli stessi tre punti d'ingresso della tabella della Sezione 6.3 — `chat()`, `stream()`, `structured()` — senza alcuna classe da scrivere. Legge il provider di default e il system prompt dalla configurazione.

### Agganciare i tool

```php
$response = Neuron::tools(new SearchTool())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

$response = Neuron::tools([new SearchTool(), CalculatorToolkit::make()])
    ->chat(new UserMessage('Hello!'))
    ->getMessage();
```

Istanza singola o array.

### Agganciare i middleware

```php
use NeuronAI\Agent\Middleware\ToolApproval;
use NeuronAI\Agent\Nodes\ChatNode;
use NeuronAI\Agent\Nodes\ToolNode;

// Require human approval before the agent executes any tool
$response = Neuron::middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Delete the oldest log file'))
    ->getMessage();

// Both arguments accept arrays
$neuron = Neuron::middleware([ChatNode::class, ToolNode::class], [new ToolApproval()]);
```

**Ecco le classi dei nodi, in un namespace reale:** `NeuronAI\Agent\Nodes\ChatNode`, `ToolNode`, `StreamingNode`, `StructuredOutputNode`.

Il README enuncia la mappatura direttamente — ogni modalità di interazione è sostenuta dal proprio nodo: `ChatNode` per `chat()`, `StreamingNode` per `stream()`, `StructuredOutputNode` per `structured()` e `ToolNode` per l'esecuzione dei tool.

**Questa è la Sezione 2.3 riscossa fino in fondo.** Non puoi usare questa API senza sapere che un agent è un workflow di nodi con un nome. Quell'affermazione, fatta il secondo giorno del libro, è ciò su cui questa API è costruita.

### Quando smettere di usare la facade

Il README lo dice chiaramente:

> Per memoria personalizzata, middleware multipli o comportamenti dell'agent più avanzati, crea una classe agent dedicata usando `php artisan neuron:agent`.

Vale la pena aggiungere altri tre inneschi:

- L'agent ha bisogno di un **nome** — qualcosa che un collega possa trovare e su cui possa ragionare
- L'agent ha bisogno di **test**
- La configurazione dell'agent compare in **più di un posto**

La facade è per prototipi, funzionalità interne una tantum e script di amministrazione. La classe è per tutto ciò che ha un ruolo nella tua applicazione. Il Pattern A contro il Pattern B della Sezione 2.4, in abito Laravel.

### Punti chiave

- `Neuron::chat()`, `::stream()`, `::structured()` — nessuna classe richiesta.
- `::tools()` e `::middleware()` si concatenano alla chiamata.
- Le classi dei nodi vivono in `NeuronAI\Agent\Nodes\`; ogni modalità di interazione ne mappa una.
- Passa a una classe quando l'agent ha bisogno di un nome, di test, o compare due volte.

## 17.5 Copiare, non mutare: la storia di concorrenza della facade

### Il problema che risolve

Una facade risolve un singleton. In un runtime a lunga vita — Octane, Swoole, RoadRunner — quell'istanza persiste fra le richieste.

Ora considera che cosa farebbe un'implementazione ingenua:

```php
// Request A
Neuron::tools(new AdminDeleteTool())->chat(...);

// Request B, milliseconds later, different user
Neuron::chat(...);  // ...does request B have the admin tool?
```

Se `tools()` mutasse l'istanza condivisa, la risposta sarebbe sì — e avresti una fuga di privilegi fra richieste che compare solo sotto Octane, solo qualche volta, ed estremamente sgradevole da diagnosticare.

### Il progetto

Il README lo affronta direttamente:

> La facade risolve un **singleton**, quindi i metodi di configurazione non mutano mai l'istanza condivisa — restituiscono una copia fresca e indipendente che concateni nella chiamata. Questo significa che ogni `Neuron::chat(...)` parte dal default pulito e configurato, a meno che tu non agganci esplicitamente tool o middleware.

Dimostrato:

```php
$response = Neuron::tools(new SearchTool())
    ->middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

// The singleton is untouched — this call has no tools or middleware
Neuron::chat(new UserMessage('Hello!'));
```

### Perché merita una sezione tutta sua

Due ragioni.

**È una proprietà di sicurezza, non una comodità.** In un deploy PHP-FPM senza stato il bug sarebbe invisibile. Sotto Octane sarebbe una fuga di dati. Il progetto anticipa il modello di deploy che sta diventando normale.

**È un pattern che vale la pena rubare.** Configurazione immutabile per default su un servizio condiviso — `withX()` che restituisce un clone invece di `setX()` che muta — è buona progettazione in generale, e la maggior parte degli sviluppatori PHP ha scritto la versione mutante almeno una volta.

Il principio generale: **un servizio condiviso dovrebbe distribuire copie configurate, non lasciare che i chiamanti lo riconfigurino.**

### La regola pratica

Poiché ogni catena è indipendente, non puoi accumulare configurazione fra istruzioni diverse:

```php
// This does NOT work as it appears to
Neuron::tools(new SearchTool());
Neuron::chat(new UserMessage('...'));  // no tools — different copy
```

```php
// Chain it, or hold the copy
$agent = Neuron::tools(new SearchTool());
$agent->chat(new UserMessage('...'));  // has tools
```

Semplice una volta detto, e cinque minuti di confusione se non lo è.

### Punti chiave

- La facade è un singleton; `tools()` e `middleware()` restituiscono copie indipendenti.
- Previene fughe fra richieste sotto Octane, Swoole e RoadRunner.
- Concatena la chiamata o tieni l'istanza restituita — la configurazione non si accumula fra istruzioni.
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

Forma familiare — lo stesso pattern `driver()` di `Cache::driver()`, `Queue::connection()` e `Storage::disk()`. È deliberato, ed è il motivo per cui non richiede spiegazioni a un pubblico Laravel.

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

### Con nome contro default

```php
// Explicit driver
AIProvider::driver('anthropic');

// Configured default — NEURON_AI_PROVIDER
AIProvider::driver();
```

**Preferisci il default** per la maggior parte degli agent. Nominare il driver nella classe reintroduce esattamente l'accoppiamento che la Sezione 3.6 aveva rimosso — e rompe silenziosamente la configurazione per ambiente della Sezione 17.2, perché un agent che scrive `'anthropic'` a codice chiamerà Anthropic in sviluppo locale a prescindere da ciò che dice `.env.local`.

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

### Punti chiave

- `AIProvider`, `EmbeddingProvider`, `VectorStore` — tutte con `driver()`.
- Stesso idioma di `Cache::driver()`; nessuna spiegazione necessaria.
- Preferisci `driver()` senza argomenti così che la configurazione per ambiente continui a funzionare.
- Nomina un driver solo quando quell'agent lo richiede davvero.

## 17.7 Laravel Boost e lo sviluppo assistito dall'AI

### Che cosa viene incluso

Il pacchetto include **linee guida per assistenti di codice AI integrate con Laravel Boost**, per aiutare gli assistenti a scrivere codice NeuronAI migliore.

Perché conta: come l'Appendice A documenta a lungo, l'ecosistema contiene una grande quantità di materiale v1 e v2. Un assistente di codice addestrato su codice pubblico produrrà con sicurezza `use NeuronAI\Agent;` e `new Edge(...)` — API rimosse due major fa.

Distribuire linee guida aggiornate insieme al pacchetto è una correzione diretta. L'assistente legge ciò che è vero adesso invece di ciò che era vero due anni fa.

### L'idea più ampia

È un pattern da notare più che una semplice funzionalità: **una libreria che distribuisce istruzioni per gli strumenti che scrivono codice contro di essa.**

Se mantieni pacchetti, quell'idea ha valore immediato — quando gli assistenti dei tuoi utenti generano codice sbagliato contro la tua libreria, quello è il tuo carico di supporto.

Se stai costruendo sistemi agentici, chiude un cerchio attorno a cui questo libro gira da un pezzo: puoi collegare la documentazione di NeuronAI a un assistente di codice tramite un server MCP (Capitolo 9), e usare agent per aiutarti a costruire agent.

### L'avvertenza onesta

Mantieni un inquadramento sobrio. Gli assistenti restano sicuri di sé e sbagliati sulle librerie che si muovono in fretta, e l'Appendice A è la prova diretta — la *documentazione ufficiale* si è discostata dal codice in quarantaquattro punti. Un assistente che legge quella documentazione eredita la deriva.

La disciplina: usa gli assistenti per scaffolding e boilerplate; verifica qualunque cosa tocchi la superficie dell'API contro la versione che hai installato. È la stessa abitudine che questo libro applica dall'inizio, e si trasferisce ben oltre NeuronAI. Il Capitolo 26 va oltre.

### Punti chiave

- Il pacchetto distribuisce linee guida aggiornate per gli assistenti di codice tramite Laravel Boost.
- Esiste perché il corpus pubblico è pieno di codice v1/v2.
- Buon pattern per i manutentori di librerie in generale.
- Verifica il codice generato contro la tua versione installata — sempre.

## Laboratorio 11 — Cinque minuti alla prima risposta

**Copre:** la facade, la configurazione e il sapere quando abbandonarle entrambe.

### Obiettivo

Un endpoint `POST /api/ask` funzionante, servito tramite la facade, da `composer require` alla prima risposta in circa cinque minuti. Poi la metà più interessante: individuare il punto esatto in cui la facade smette di essere lo strumento giusto.

### Parte prima — falla funzionare

1. Installa l'SDK e pubblica la configurazione.
2. Imposta `NEURON_AI_PROVIDER=ollama` in `.env` così che non costi nulla.
3. Scrivi una route e un controller che legge `message` dalla richiesta e restituisce la risposta della facade.
4. Conferma che funziona con `curl`.

Questa è tutta la prima parte, e dovrebbe richiedere davvero pochi minuti. Il controller è di quattro righe.

### Parte seconda — rompila deliberatamente

Ora aggiungi i requisiti uno alla volta, e annota dove ciascuno comincia a far male:

1. **L'endpoint ha bisogno di un system prompt specifico per il tuo prodotto.** Configurazione, o codice?
2. **Gli serve un tool.** Ti trovi ancora a tuo agio nel controller?
3. **Gli serve un test.** Come fai il fake della facade?
4. **Un secondo endpoint ha bisogno della stessa configurazione.** Dove vive adesso?

Al terzo o quarto requisito dovresti stare allungando la mano verso `php artisan neuron:agent`. È quella la lezione — non che la facade sia cattiva, ma che puoi sentire esattamente quando smette di andarti bene.

### Criteri di accettazione

- `POST /api/ask` restituisce una risposta sensata con `NEURON_AI_PROVIDER=ollama` e nessuna chiave API configurata.
- Passare a un provider cloud richiede solo una modifica a `.env`.
- Sai dire, in una frase, quale dei quattro requisiti qui sopra ti ha spinto verso una classe.

### Una trappola da evitare

Non accumulare configurazione della facade fra istruzioni diverse — Sezione 17.5. Se il tuo controller chiama `Neuron::tools(...)` su una riga e `Neuron::chat(...)` su quella dopo, i tool sono silenziosamente assenti. Scrivilo come una catena unica e conferma che il tool venga davvero offerto.
