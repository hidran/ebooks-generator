# Capitolo 2 — L'architettura di NeuronAI

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 2.1 I quattro pilastri

L'intero framework sta in testa come quattro concetti. Sistemarli adesso significa che ogni capitolo successivo avrà dove attaccarsi.

### Installazione, per orientamento

```bash
composer require neuron-core/neuron-ai
```

Requisiti: l'estensione `curl`, e ben poco altro: il framework parla HTTP attraverso un proprio client basato su curl. Il pacchetto in sé gira su PHP 8.1 o superiore; il codice di questo libro richiede PHP 8.5 (il Capitolo 3 spiega perché). L'SDK Laravel è trattato nella Parte V, dove il libro usa Laravel 13 su PHP 8.5.

### Pilastro 1 — Agent

Il ciclo di tool calling della Sezione 1.2, implementato e protetto. Estendi una classe base, dichiari quale provider usare, quali sono le istruzioni e quali tool sono disponibili. NeuronAI esegue il ciclo, gestisce l'array dei messaggi, si occupa del dispatch dei tool e applica i limiti di esecuzione.

È il piolo 4 della Sezione 1.1, pronto all'uso.

### Pilastro 2 — Workflow

Un grafo event-driven. Definisci dei nodi; ogni nodo riceve un evento e restituisce un evento; il tipo dell'evento restituito determina quale nodo viene eseguito dopo. In più: stato condiviso, diramazioni, cicli ed **esecuzione durevole** — con uno store di persistenza configurato, ogni step completato viene registrato, così una run può mettersi in pausa per un input umano o un evento esterno e riprendere giorni dopo in un altro processo, e una run il cui processo è andato in crash riparte dopo il suo ultimo step completato invece di ricominciare da capo.

È il piolo 3 fatto per bene, ed è anche il substrato dei sistemi multi-agente.

### Pilastro 3 — RAG

La pipeline di retrieval: data loader per l'ingestion, un provider di embedding per vettorizzare, un vector store per conservare e cercare, pre- e post-processor per migliorare le query e riordinare i risultati, e una classe `RAG` che li lega insieme in un agent che risponde a partire dai tuoi documenti.

### Pilastro 4 — Observability

Ogni agent e ogni workflow emette un flusso di eventi mentre gira — un nodo è partito, un'inferenza è cominciata e finita, un tool è stato chiamato e ha risposto, una run è stata interrotta — sotto forma di eventi PSR-14 standard. Sei tu a sottoscriverli: Inspector, costruito dallo stesso team, li trasforma in trace; anche il tuo logger o il sistema di eventi del tuo framework possono riceverli. Vista la Sezione 1.5, non è un vezzo di monitoraggio. Senza un trace non puoi rispondere a "perché ha fatto così", e "perché ha fatto così" è l'unica domanda che ti porrai mai.

### L'immagine mentale

```
                   ┌─────────────────────────┐
                   │       WORKFLOW          │
                   │  (nodi, eventi, stato,  │
                   │   cicli, interruzione)  │
                   │                         │
                   │   ┌───────┐  ┌───────┐  │
                   │   │ AGENT │  │  RAG  │  │
                   │   └───────┘  └───────┘  │
                   └─────────────────────────┘
                                │
       ┌────────────┬───────────┼───────────┬────────────┐
    Provider      Tools    ChatHistory  VectorStores  Embeddings
                                │
                          OBSERVABILITY
```

Il Workflow è il contenitore esterno. Agent e RAG sono configurazioni preconfezionate che vivono al suo interno. Sotto, un insieme di componenti intercambiabili. Trasversale, il tracing.

### Punti chiave

- Quattro pilastri: Agent, Workflow, RAG, Observability.
- Il Workflow è il caso generale; Agent e RAG sono specializzazioni.
- L'observability è un pilastro, non un'aggiunta, proprio a causa del non determinismo.

## 2.2 Tutto è un'interfaccia

Una sola decisione di progetto spiega gran parte della forma di NeuronAI, e ti dà più leva pratica di qualunque singola funzionalità.

### Le cinque interfacce che contano

L'architettura di NeuronAI è un piccolo insieme di contratti che ogni implementazione concreta rispetta:

| Interfaccia | Responsabilità | Implementazioni di esempio |
|---|---|---|
| `AIProviderInterface` | Parlare con un LLM | Anthropic, OpenAI, Gemini, Mistral, Ollama, DeepSeek, Bedrock, Azure |
| `ToolInterface` | Dare all'agent una capacità | Le tue classi, i toolkit inclusi, i tool forniti via MCP |
| `MessageStoreInterface` | Conservare i messaggi della conversazione | InMemory, File, SQL, Eloquent |
| `EmbeddingsProviderInterface` | Trasformare testo in vettori | OpenAI, Voyage, Ollama |
| `VectorStoreInterface` | Conservare, filtrare e cercare vettori | Memory, File, MariaDB, MongoDB Atlas, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch |

Il codice della tua applicazione dipende dall'interfaccia. Mai dall'implementazione.

::: {.callout .callout-warning}
[Nota di versione]{.callout-title}

Quell'elenco di vector store è l'insieme completo delle implementazioni di prima parte, e va letto con attenzione perché **NeuronAI non include uno store pgvector**. Molto materiale di terze parti — inclusi tutorial e programmi di corso derivati dall'ecosistema Python, dove pgvector è onnipresente — presume di sì. Se vuoi ergonomia in stile Postgres, la risposta di prima parte più vicina è **MariaDB 11.7+**, che ti dà ricerca vettoriale in un database che probabilmente stai già facendo girare; il Capitolo 12 si basa su di essa. **PHPVector**, uno store in PHP puro senza alcuna infrastruttura, vive in un pacchetto separato con un proprio ciclo di rilascio, e al momento della stampa di questo libro non aveva ancora una release per NeuronAI v4: il Capitolo 12 spiega come verificarlo.
:::

### Come si presenta in pratica

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(
        key: 'ANTHROPIC_API_KEY',
        model: 'ANTHROPIC_MODEL',
    );
}
```

Passa a un modello ospitato in locale:

```php
protected function provider(): AIProviderInterface
{
    return new Ollama(
        url: 'OLLAMA_URL',
        model: 'OLLAMA_MODEL',
    );
}
```

Nient'altro cambia. Non le istruzioni, non i tool, non la cronologia, non il codice chiamante. Nella Sezione 3.6 spingiamo oltre e pilotiamo la scelta interamente da una variabile d'ambiente.

### Perché è una capacità strategica, non una comodità

Quattro conseguenze da nominare esplicitamente, perché sono il modo in cui giustifichi il framework a chi decide:

**Stratificazione dei costi.** Instrada classificazione ed estrazione verso un modello economico e veloce; instrada la sintesi finale verso uno costoso. È la terza leva della Sezione 1.4, e l'interfaccia è ciò che la rende un cambiamento di una riga invece di un refactoring.

**Rischio provider.** I disservizi accadono, i prezzi cambiano, i termini cambiano. Una dipendenza rigida dall'SDK di un singolo fornitore è un rischio di business. Un'interfaccia è una via d'uscita.

**Sviluppo locale.** Fai girare Ollama sul portatile e sviluppa gratis tutto quello che c'è in questo libro. Metti in produzione su un provider cloud. Stesso codice.

**Residenza dei dati.** Un cliente che non può mandare dati fuori dall'UE, o fuori dal proprio edificio, diventa un cambio di configurazione anziché una riscrittura.

### Il compromesso, detto onestamente

Un'astrazione su più provider converge sul loro sottoinsieme comune. Le funzionalità specifiche di un provider — modalità di ragionamento estese, tool nativi di ricerca web, particolari impostazioni di sicurezza — o vengono esposte tramite vie di fuga o non sono disponibili. La risposta di NeuronAI è `ProviderTool`, che ti permette di usare i tool integrati di un provider (li supportano l'API OpenAI Responses, Gemini, Anthropic e ZAI), ma la documentazione del framework ammette candidamente che i provider tool introducono vincoli e che il sistema portabile di Tool e Toolkit resta la strada più flessibile.

Sappi che cosa stai scambiando. La portabilità costa l'accesso, per un po', alla funzionalità proprietaria più recente.

### Punti chiave

- Cinque interfacce: provider, tool, message store, embedding, vector store.
- Dipendi dall'interfaccia; l'implementazione è configurazione.
- Il ritorno è stratificazione dei costi, rischio fornitore, sviluppo locale gratuito e residenza dei dati.
- Il costo è l'accesso ritardato alle funzionalità specifiche di un provider.

## 2.3 L'intuizione chiave: Agent e RAG *sono* Workflow

È la sezione più importante del capitolo. È l'idea unificante centrale del framework, la documentazione ufficiale la rivela tardi, e spiega moltissimo di ciò che altrimenti sembrerebbe arbitrario.

### L'affermazione

`Agent` e `RAG` non sono sistemi separati che stanno accanto a `Workflow`. **Sono workflow.** Sono grafi di nodi pre-assemblati che implementano i due pattern agentici più comuni.

La documentazione di NeuronAI lo dice direttamente: le classi Agent e RAG sono esse stesse workflow, e rappresentano implementazioni pronte all'uso dei pattern più comuni per chiamate a tool, retrieval e structured output.

### Che cosa significa in concreto

`Agent` estende `Workflow`, alla lettera: apri `vendor/neuron-core/neuron-ai/src/Agent/Agent.php` e la dichiarazione della classe lo dice. Quando chiami `->chat()` su un agent, stai eseguendo un workflow i cui nodi sono:

- `AgentStartNode` — assembla la richiesta: istruzioni, messaggi, opzioni della run
- `ChatNode` — chiama l'LLM; `->stream()` passa per lo stesso nodo, che semplicemente trasmette la risposta in streaming
- `StructuredOutputNode` — chiama l'LLM quando richiedi un risultato tipizzato
- `ToolNode` — esegue i tool che il modello ha richiesto, fermandosi prima per una decisione umana quando un tool richiede approvazione, poi torna all'inferenza
- `AgentEndNode` — chiude la run quando il modello dà una risposta finale

`ChatNode` e `StructuredOutputNode` condividono una classe base, `InferenceNode`: "ovunque venga chiamato il modello".

Quei nomi di nodo non sono dettagli interni. Fanno parte della superficie pubblica. Colleghi un middleware a un agent nominando la classe del nodo che deve avvolgere. Qui un middleware di riassunto gira prima di ogni chiamata al modello, chat o strutturata, e, quando la conversazione supera un budget di token, sostituisce i turni più vecchi con un riassunto:

```php
$agent = SupportAgent::make(workflowId: $threadId)
    ->addMiddleware(InferenceNode::class, new Summarization(
        provider: $cheapProvider,
        maxTokens: 20_000,
    ));

$state = $agent->chat(new UserMessage('Summarise my last three tickets'));
```

Non puoi usare quell'API senza sapere che dietro `chat()` ci sono dei nodi. È esattamente per questo che l'argomento sta nel Capitolo 2 e non nel 15.

Il valore di ritorno racconta la stessa storia. `chat()` non restituisce un messaggio; esegue il workflow fino alla fine e restituisce il suo stato finale, un `AgentState`, che estende il `WorkflowState` restituito da ogni workflow. La risposta dell'assistente è una delle cose che ci leggi sopra (Sezione 3.4).

### Le tre conseguenze

**1. Tutto quello che impari sui workflow vale per gli agent.**
Middleware, stato, streaming, interruzione, persistenza: sono funzionalità dei workflow, e gli agent le ereditano tutte. Quando arriverai al Capitolo 15 e imparerai l'human-in-the-loop, non starai imparando una funzionalità separata degli agent: un tool che richiede approvazione fa sì che `ToolNode` interrompa la run, esattamente come può fare qualunque nodo di workflow, e approvarlo riprende la run. Perfino l'identità della conversazione è un concetto dei workflow. Il thread ID che dai a un agent (l'argomento `workflowId:` qui sopra; Capitolo 4) *è* il workflow ID della run. Il framework non ne inventa mai uno — un agent senza ID si rifiuta di girare — e in cambio un endpoint che non ha in mano nient'altro che il thread ID può trovare una run in pausa e riprenderla.

**2. Non c'è un secondo framework quando il progetto cresce.**
La traiettoria abituale con altri stack è: prototipo con l'astrazione semplice, arrivi al suo soffitto, riscrivi sull'astrazione a grafo. Qui `Agent` *è* l'astrazione a grafo con una configurazione di default. Crescere significa aggiungere nodi, non migrare.

**3. Puoi usare un Agent come nodo dentro un Workflow più grande.**
È la storia del multi-agente, e non richiede alcuna API speciale. Un agent ricercatore è un nodo. Un agent scrittore è un nodo. Un arbitro è un nodo. Li componi con gli eventi. Il Capitolo 16 fa esattamente questo.

### La regola decisionale

**Estendi `Agent`** quando il tuo problema è "un'entità, un obiettivo, qualche tool, cicla finché non è finito". È la maggior parte degli assistenti monoscopo.

**Costruisci un `Workflow`** quando ti serve: controllo sull'ordine dei passi, più agent specializzati, diramazioni o cicli che scrivi tu, checkpoint o una pausa per l'input umano.

**Estendi `RAG`** quando il lavoro principale è rispondere a partire da un corpus documentale.

E quando sei incerto: parti da `Agent`. Migrare a un workflow più avanti è additivo, perché era un workflow fin dall'inizio.

::: {.callout .callout-tip}
[In pratica]{.callout-title}

Se porti una sola frase dalla Parte I alla Parte IV, porta questa. Chi se la perde vive i workflow come un argomento nuovo e scollegato a metà libro; chi ce l'ha vive i workflow come *"ah — ecco che cosa c'era sotto l'agent per tutto il tempo"*.
:::

### Punti chiave

- `Agent` e `RAG` sono workflow configurati, non sistemi paralleli; `chat()` restituisce lo stato finale del workflow.
- Le classi dei nodi (`ChatNode`, `StructuredOutputNode`, la loro base `InferenceNode`, `ToolNode`) sono API pubblica: i middleware le prendono di mira.
- Le funzionalità dei workflow — interruzione, persistenza durevole, identità — vengono ereditate dagli agent; il thread ID di una conversazione è il suo workflow ID.
- Il multi-agente non richiede API speciali: un agent è semplicemente un nodo.

## 2.4 Estendere o comporre: scegliere la struttura

Tre pattern strutturali, una regola decisionale e — cosa importante — un percorso di migrazione fra loro che non comporta riscritture.

### Pattern A — Estendere la classe Agent

Il default, e corretto nella grande maggioranza dei casi.

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;

class SupportAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(key: '...', model: '...');
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a customer support assistant.'],
        );
    }

    protected function tools(): array
    {
        return [ /* ... */ ];
    }
}
```

Tre metodi template — `provider()`, `instructions()`, `tools()` — più gli opzionali `messageStore()` e `contextWindow()`, e ognuno ha un setter gemello (`setAiProvider()`, `setInstructions()`, `setTools()`, `setMessageStore()`, `setContextWindow()`) che prevale sul metodo quando lo chiami. Tutto il resto è ereditato. La classe è una dichiarazione di *che cosa è questo agent*, e si legge come configurazione perché lo è.

**Perché vale la pena difendere questo pattern.** La classe diventa un'unità con un nome, testabile e iniettabile. `SupportAgent` può essere registrata in un service container, mockata nei test e ragionata da un collega che non ha mai visto il framework. È un vantaggio architetturale reale rispetto a spargere configurazione fluente per i controller.

### Pattern B — Configurazione fluente sul punto di chiamata

Per esecuzioni una tantum ed esperimenti:

```php
$state = SupportAgent::make(workflowId: $threadId)
    ->toolMaxRuns(5)
    ->addTool(SomeExtraTool::make())
    ->chat(new UserMessage('...'));
```

Usalo per variazioni per-richiesta sopra una classe dichiarata: un tool che compare solo per gli amministratori, un limite di esecuzioni più basso per un endpoint economico. Non usarlo come sostituto della classe: la configurazione assemblata inline in un controller è configurazione che fra sei mesi nessuno troverà.

### Pattern C — Comporre un Workflow dai componenti

Quando vuoi un flusso di controllo scritto da te, usi i componenti di NeuronAI come pezzi indipendenti. La documentazione è esplicita: provider, embedding, data loader, chat history e vector store possono essere usati tutti come componenti autonomi per costruire entità agentiche completamente personalizzate.

```php
$state = Workflow::make(workflowId: $runId)
    ->addNodes([
        new ClassifyNode(),
        new RetrieveNode(),
        new AnswerNode(),
    ])
    ->run();
```

Qui la sequenza l'hai scritta *tu*. Il modello riempie i passi. Come un agent, un workflow gira sotto un ID che fornisci tu: `workflowId:` è l'indirizzo della run, e il framework non ne inventa mai uno. `run()` esegue il grafo e restituisce il `WorkflowState` finale — lo stesso verbo e lo stesso tipo di risultato che ti dà un agent, perché un agent è proprio questo. È il piolo 3 della Sezione 1.1, con persistenza durevole e interruzione disponibili quando servono.

### Il percorso di migrazione

Il motivo per cui questa decisione è a basso rischio: Pattern A → Pattern C è additivo. Poiché `SupportAgent` è già un workflow, promuoverlo significa avvolgerlo come nodo in un grafo più grande, non riscriverlo.

```php
class SupportNode extends Node
{
    public function __invoke(QuestionEvent $event, WorkflowState $state): ResolvedEvent
    {
        $answer = SupportAgent::make(workflowId: $event->threadId)
            ->chat(new UserMessage($event->question))
            ->getMessage();

        return new ResolvedEvent($answer?->getContent());
    }
}
```

`QuestionEvent` e `ResolvedEvent` sono classi evento tue; la prima porta la domanda e il thread ID della conversazione a cui appartiene. Sono i tipi del parametro e del valore di ritorno del nodo a collegarlo al grafo. Il tuo agent è invariato. Ora è un componente di qualcosa di più grande.

### Punti chiave

- Estendi `Agent` per default; la classe è un'unità con nome, iniettabile e testabile.
- Configurazione fluente per la variazione per-richiesta, non come sostituto di una classe.
- Componi un `Workflow` quando il flusso di controllo lo scrivi tu.
- La promozione da A a C è additiva: avvolgi, non riscrivere.

## 2.5 L'ecosistema intorno al framework

Un breve orientamento, così da non ricostruire cose che esistono già e sapere quali pezzi questo libro usa davvero.

### Inspector

Costruito dallo stesso team, ed è il motivo per cui l'observability è un pilastro. Non è incluso nel pacchetto: il framework in sé non dipende da nient'altro che dalle interfacce PSR-14, quindi richiedi il pacchetto di Inspector (`inspector-apm/inspector-php`, 3.19 o successivo), imposti la sua chiave

```dotenv
INSPECTOR_INGESTION_KEY=your-key-here
```

e sottoscrivi il suo listener, `InspectorSubscriber`, agli agent e ai workflow che vuoi tracciare. Da lì in poi ogni esecuzione compare come una linea temporale: quale nodo ha girato, quale tool è stato chiamato con quali argomenti, cosa è tornato indietro, quanti token, quanto tempo. Niente viene collegato implicitamente: un agent che non hai sottoscritto è un agent che non puoi vedere, e questo merita una riga nella checklist della tua code review.

Lo colleghiamo nel Capitolo 10 e lo usiamo di nuovo nel 23. Vista la Sezione 1.5, metti in conto un visualizzatore di trace di qualche tipo fin dall'inizio.

### Neuron Cloud

La piattaforma di observability ospitata che il team di NeuronAI gestisce per il framework, ed è quella a cui oggi rimandano le indicazioni della libreria stessa per il tracing in produzione. Consuma lo stesso flusso di eventi: richiedi `neuron-core/cloud-sdk` (o i suoi wrapper `neuron-core/neuron-cloud-laravel` e `neuron-core/neuron-cloud-symfony`), gli dai una chiave API e una chiave di firma, e sottoscrivi il suo listener esattamente come faresti con quello di Inspector. Ogni run arriva allora come un'unica trace — nodi, inferenze, tool call, retrieval, structured output — ricucita attraverso le pause di una run durevole. Scegliere tra i due cambia una chiamata a `subscribe()` e nulla nei tuoi agent. La Sezione 10.2 dice che cosa controllare prima di farci affidamento.

### L'SDK Laravel

```bash
composer require neuron-core/neuron-laravel
```

Tutta la Parte V. Fornisce un file di configurazione, generatori artisan (`neuron:agent`, `neuron:rag`, `neuron:tool`, `neuron:workflow`, `neuron:node`, `neuron:middleware`) e facade per provider e vector store. Le due tabelle di cui un agent di produzione ha bisogno — i messaggi della chat e lo store dei workflow su cui persistono le run durevoli — vengono da una migration tua: quelle distribuite con l'SDK 2.0.0 non si adattano a neuron-ai 4.0.2 (Sezione 17.1).

Vale la pena insistere: questo pacchetto aggiunge comodità, non capacità. Tutto quello che fa potresti farlo a mano — che è esattamente il motivo per cui nelle Parti da II a IV lo facciamo a mano prima.

### MCP — Model Context Protocol

Un protocollo aperto per esporre tool ai sistemi AI. NeuronAI include un connettore MCP, così i tool pubblicati da qualunque server MCP possono essere collegati a un agent NeuronAI come se fossero nativi. Lo copre il Capitolo 9. Le implicazioni di sicurezza hanno lì la loro discussione: un server MCP è codice di terze parti che entra nel ciclo del tuo agent.

### Maestro

Un framework open source per agent CLI costruito su NeuronAI, con tool calling e approvazioni human-in-the-loop. Utile come implementazione di riferimento di un'applicazione di produzione completa, e ottima fonte di esercizi di lettura del codice. Ci torniamo nel Capitolo 27.

### Neuron Hub

Un registro di estensioni e toolkit della comunità. Controllalo prima di scrivere un'integrazione — e pubblica lì la tua.

### Neuron Studio

Un pacchetto della comunità (`digitalelvis/neuronai-studio`) che offre un costruttore visuale di agent per Laravel ed esporta vere classi PHP. Utile per prototipare e per mostrare l'architettura a chi non sviluppa. Genera codice; non sostituisce il capirlo.

### Panorama delle versioni

Questo libro punta a **NeuronAI 4.0.2** e, per la Parte V, all'**SDK Laravel 2.x**, la linea di rilascio costruita per NeuronAI v4.

Buona parte del codice di esempio che troverai online è stata scritta per versioni precedenti. Una parte ha gli stessi import di questo libro e fallisce più tardi, su un metodo che non esiste o che restituisce altro; un'altra parte usa namespace più vecchi (`NeuronAI\Agent` invece di `NeuronAI\Agent\Agent`) e fallisce già sulla prima istruzione `use`. Se un articolo di blog o una pagina di documentazione non corrisponde a questo libro, controlla a quale versione punta prima di debuggare qualunque altra cosa.

::: {.callout .callout-warning}
[Le guide di aggiornamento arrivano con il pacchetto]{.callout-title}

NeuronAI mette le note di migrazione dove il tuo codice può raggiungerle: `vendor/neuron-core/neuron-ai/upgrade/` contiene una guida numerata per ogni breaking change, ciascuna con il codice prima e dopo e i pattern `grep` che trovano i punti di chiamata coinvolti. Quando uno snippet di un tutorial più vecchio si rifiuta di girare, la risposta di solito è in uno di quei file, e sono più aggiornati del sito della documentazione, che resta indietro rispetto al codice.

Il Capitolo 27 trasforma tutto questo in una **strategia di versione**: come determinare che cosa hai davvero installato, come leggere un changelog e una guida di aggiornamento cercando breaking change, e come fissare le versioni perché un rilascio della libreria sia una decisione e non un disservizio. Prima di fidarti di qualunque affermazione sulla versione — inclusa questa — esegui `composer show neuron-core/neuron-ai --all`.
:::

### Esercizio

Riproduci a memoria il diagramma dei quattro pilastri. Poi, per ciascuno dei due progetti finali — A ("Repo Auditor CLI", Capitolo 24) e B ("Help desk agentico", Capitolo 25) — elenca quali pilastri e quali pezzi dell'ecosistema ti aspetti di dover usare. Conserva la risposta e confrontala con ciò che costruirai davvero: lo scarto è il feedback più utile che questo libro possa darti.

### Punti chiave

- L'observability è un flusso di eventi PSR-14; Inspector e Neuron Cloud sono listener che sottoscrivi esplicitamente, non qualcosa che si collega da solo.
- L'SDK Laravel per la comodità, non per le capacità.
- MCP porta dentro tool esterni — e con loro codice esterno.
- Questo libro punta a NeuronAI 4.0.2 su PHP 8.5. Il codice scritto per versioni precedenti riempie ancora i risultati di ricerca; controlla la versione prima di debuggare.
