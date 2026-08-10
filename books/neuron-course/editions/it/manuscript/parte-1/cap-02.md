# Capitolo 2 — L'architettura di NeuronAI

## 2.1 I quattro pilastri

L'intero framework sta in testa come quattro concetti. Sistemarli adesso significa che ogni capitolo successivo avrà dove attaccarsi.

### Installazione, per orientamento

```bash
composer require neuron-core/neuron-ai
```

Requisiti: PHP 8.1 o superiore per il pacchetto core. L'SDK Laravel, trattato nella Parte V, richiede PHP 8.2 e Laravel 10 o superiore.

### Pilastro 1 — Agent

Il ciclo di tool calling della Sezione 1.2, implementato e protetto. Estendi una classe base, dichiari quale provider usare, quali sono le istruzioni e quali tool sono disponibili. NeuronAI esegue il ciclo, gestisce l'array dei messaggi, si occupa del dispatch dei tool e applica i limiti di esecuzione.

È il piolo 4 della Sezione 1.1, pronto all'uso.

### Pilastro 2 — Workflow

Un grafo event-driven. Definisci dei nodi; ogni nodo riceve un evento e restituisce un evento; il tipo dell'evento restituito determina quale nodo viene eseguito dopo. In più: stato condiviso, diramazioni, cicli, checkpoint su storage, interruzione per l'input umano e ripresa — potenzialmente giorni dopo.

È il piolo 3 fatto per bene, ed è anche il substrato dei sistemi multi-agente.

### Pilastro 3 — RAG

La pipeline di retrieval: data loader per l'ingestion, un provider di embedding per vettorizzare, un vector store per conservare e cercare, pre- e post-processor per migliorare le query e riordinare i risultati, e una classe `RAG` che li lega insieme in un agent che risponde a partire dai tuoi documenti.

### Pilastro 4 — Observability

Tracciamento di ogni chiamata all'LLM, invocazione di tool e retrieval, consegnato tramite Inspector. Vista la Sezione 1.5, non è un vezzo di monitoraggio. Senza un trace non puoi rispondere a "perché ha fatto così", e "perché ha fatto così" è l'unica domanda che ti porrai mai.

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
| `ChatHistoryInterface` | Conservare lo stato della conversazione | InMemory, File, SQL, Eloquent |
| `EmbeddingsProviderInterface` | Trasformare testo in vettori | OpenAI, Voyage, Ollama |
| `VectorStoreInterface` | Conservare e cercare vettori | Memory, File, PHPVector, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch |

Il codice della tua applicazione dipende dall'interfaccia. Mai dall'implementazione.

::: {.callout .callout-warning}
[Nota di versione]{.callout-title}

Quell'elenco di vector store è l'insieme completo delle implementazioni di prima parte, e va letto con attenzione perché **NeuronAI non include uno store pgvector**. Molto materiale di terze parti — inclusi tutorial e programmi di corso derivati dall'ecosistema Python, dove pgvector è onnipresente — presume di sì. Se vuoi ergonomia in stile Postgres, le risposte di prima parte più vicine sono **PHPVector** (PHP puro, nessuna infrastruttura) e **MariaDB 11.7+**, che ti dà ricerca vettoriale in un database che probabilmente stai già facendo girare. Il Capitolo 12 usa entrambi.
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

Un'astrazione su più provider converge sul loro sottoinsieme comune. Le funzionalità specifiche di un provider — modalità di ragionamento estese, caching dei prompt, tool nativi di ricerca web, particolari impostazioni di sicurezza — o vengono esposte tramite vie di fuga o non sono disponibili. La risposta di NeuronAI è `ProviderTool`, che ti permette di usare i tool integrati di un provider (OpenAI Responses, Gemini e Anthropic li supportano), ma la documentazione del framework ammette candidamente che i provider tool introducono vincoli e che il sistema portabile di Tool e Toolkit resta la strada più flessibile.

Sappi che cosa stai scambiando. La portabilità costa l'accesso, per un po', alla funzionalità proprietaria più recente.

### Punti chiave

- Cinque interfacce: provider, tool, chat history, embedding, vector store.
- Dipendi dall'interfaccia; l'implementazione è configurazione.
- Il ritorno è stratificazione dei costi, rischio fornitore, sviluppo locale gratuito e residenza dei dati.
- Il costo è l'accesso ritardato alle funzionalità specifiche di un provider.

## 2.3 L'intuizione chiave: Agent e RAG *sono* Workflow

È la sezione più importante del capitolo. È l'idea unificante centrale del framework, la documentazione ufficiale la rivela tardi, e spiega moltissimo di ciò che altrimenti sembrerebbe arbitrario.

### L'affermazione

`Agent` e `RAG` non sono sistemi separati che stanno accanto a `Workflow`. **Sono workflow.** Sono grafi di nodi pre-assemblati che implementano i due pattern agentici più comuni.

La documentazione di NeuronAI lo dice direttamente: le classi Agent e RAG sono esse stesse workflow, e rappresentano implementazioni pronte all'uso dei pattern più comuni per chiamate a tool, retrieval e structured output.

### Che cosa significa in concreto

Quando chiami `->chat()` su un agent, stai eseguendo un workflow i cui nodi sono grosso modo:

- `ChatNode` — chiama l'LLM
- `ToolNode` — esegue gli eventuali tool richiesti e torna indietro nel ciclo
- `StructuredOutputNode` — usato quando richiedi un risultato tipizzato
- `StreamingNode` — usato quando chiami `->stream()`

Quei nomi di nodo non sono dettagli interni. Fanno parte della superficie pubblica. Nell'SDK Laravel colleghi un middleware nominando il nodo su cui deve girare:

```php
Neuron::middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Delete the oldest log file'));
```

Non puoi usare quell'API senza sapere che dietro `chat()` ci sono dei nodi. È esattamente per questo che l'argomento sta nel Capitolo 2 e non nel 15.

### Le tre conseguenze

**1. Tutto quello che impari sui workflow vale per gli agent.**
Middleware, stato, streaming, interruzione, persistenza: sono funzionalità dei workflow, e gli agent le ereditano tutte. Quando arriverai al Capitolo 15 e imparerai l'human-in-the-loop, non starai imparando una funzionalità separata degli agent. Starai imparando una funzionalità dei workflow che gli agent ottengono gratis.

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

- `Agent` e `RAG` sono workflow configurati, non sistemi paralleli.
- Le classi dei nodi (`ChatNode`, `ToolNode`, `StreamingNode`, `StructuredOutputNode`) sono API pubblica: i middleware le prendono di mira.
- Le funzionalità dei workflow vengono ereditate dagli agent.
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

    public function instructions(): string
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

Tre metodi template — `provider()`, `instructions()`, `tools()` — più l'opzionale `chatHistory()`. Tutto il resto è ereditato. La classe è una dichiarazione di *che cosa è questo agent*, e si legge come configurazione perché lo è.

**Perché vale la pena difendere questo pattern.** La classe diventa un'unità con un nome, testabile e iniettabile. `SupportAgent` può essere registrata in un service container, mockata nei test e ragionata da un collega che non ha mai visto il framework. È un vantaggio architetturale reale rispetto a spargere configurazione fluente per i controller.

### Pattern B — Configurazione fluente sul punto di chiamata

Per esecuzioni una tantum ed esperimenti:

```php
$response = SupportAgent::make()
    ->toolMaxRuns(5)
    ->addTool(SomeExtraTool::make())
    ->chat(new UserMessage('...'));
```

Usalo per variazioni per-richiesta sopra una classe dichiarata: un tool che compare solo per gli amministratori, un limite di esecuzioni più basso per un endpoint economico. Non usarlo come sostituto della classe: la configurazione assemblata inline in un controller è configurazione che fra sei mesi nessuno troverà.

### Pattern C — Comporre un Workflow dai componenti

Quando vuoi un flusso di controllo scritto da te, usi i componenti di NeuronAI come pezzi indipendenti. La documentazione è esplicita: provider, embedding, data loader, chat history e vector store possono essere usati tutti come componenti autonomi per costruire entità agentiche completamente personalizzate.

```php
$handler = Workflow::make()
    ->addNodes([
        new ClassifyNode(),
        new RetrieveNode(),
        new AnswerNode(),
    ])
    ->init();

$handler->run();
```

Qui la sequenza l'hai scritta *tu*. Il modello riempie i passi. È il piolo 3 della Sezione 1.1, con checkpoint e interruzione disponibili quando servono.

### Il percorso di migrazione

Il motivo per cui questa decisione è a basso rischio: Pattern A → Pattern C è additivo. Poiché `SupportAgent` è già un workflow, promuoverlo significa avvolgerlo come nodo in un grafo più grande, non riscriverlo.

```php
class SupportNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): ResolvedEvent
    {
        $answer = SupportAgent::make()->chat($event->message)->getMessage();
        return new ResolvedEvent($answer->getContent());
    }
}
```

Il tuo agent è invariato. Ora è un componente di qualcosa di più grande.

### Punti chiave

- Estendi `Agent` per default; la classe è un'unità con nome, iniettabile e testabile.
- Configurazione fluente per la variazione per-richiesta, non come sostituto di una classe.
- Componi un `Workflow` quando il flusso di controllo lo scrivi tu.
- La promozione da A a C è additiva: avvolgi, non riscrivere.

## 2.5 L'ecosistema intorno al framework

Un breve orientamento, così da non ricostruire cose che esistono già e sapere quali pezzi questo libro usa davvero.

### Inspector

Costruito dallo stesso team, ed è il motivo per cui l'observability è un pilastro. Imposta una variabile d'ambiente:

```dotenv
INSPECTOR_INGESTION_KEY=your-key-here
```

e ogni esecuzione dell'agent compare come una linea temporale: quale nodo ha girato, quale tool è stato chiamato con quali argomenti, cosa è tornato indietro, quanti token, quanto tempo.

Lo usiamo nel Capitolo 10 e di nuovo nel 23. Vista la Sezione 1.5, metti in conto un visualizzatore di trace di qualche tipo fin dall'inizio: questo è semplicemente la strada di minor resistenza.

### L'SDK Laravel

```bash
composer require neuron-core/neuron-laravel
```

Tutta la Parte V. Fornisce un file di configurazione, generatori artisan (`neuron:agent`, `neuron:rag`, `neuron:tool`, `neuron:workflow`, `neuron:node`, `neuron:middleware`), facade per provider e vector store, migration pronte per la chat history su Eloquent e un layer di persistenza Eloquent per le interruzioni dei workflow.

Vale la pena insistere: questo pacchetto aggiunge comodità, non capacità. Tutto quello che fa potresti farlo a mano — che è esattamente il motivo per cui nelle Parti da II a IV lo facciamo a mano prima.

### MCP — Model Context Protocol

Un protocollo aperto per esporre tool ai sistemi AI. NeuronAI include un connettore MCP, così i tool pubblicati da qualunque server MCP possono essere collegati a un agent NeuronAI come se fossero nativi. Lo copre il Capitolo 9. Le implicazioni di sicurezza hanno lì la loro discussione: un server MCP è codice di terze parti che entra nel ciclo del tuo agent.

### Maestro

Un framework open source per agent CLI costruito su NeuronAI, con tool calling e approvazioni human-in-the-loop. Utile come implementazione di riferimento di un'applicazione di produzione completa, e ottima fonte di esercizi di lettura del codice. Ci torniamo nel Capitolo 26.

### Neuron Hub

Un registro di estensioni e toolkit della comunità. Controllalo prima di scrivere un'integrazione — e pubblica lì la tua.

### Neuron Studio

Un pacchetto della comunità (`digitalelvis/neuronai-studio`) che offre un costruttore visuale di agent per Laravel ed esporta vere classi PHP. Utile per prototipare e per mostrare l'architettura a chi non sviluppa. Genera codice; non sostituisce il capirlo.

### Panorama delle versioni

- **v3.x — stabile corrente.** Questo libro la prende di mira. L'SDK Laravel 1.3.0 richiede `neuron-ai: ^3.15`, un limite inferiore utile da ricordare quando leggerai la Parte V.
- **v1 e v2 — legacy, e ancora ovunque su internet.** I namespace sono diversi: `NeuronAI\Agent` è diventato `NeuronAI\Agent\Agent` e `NeuronAI\SystemPrompt` è diventato `NeuronAI\Agent\SystemPrompt`. Se trovi un articolo di blog o una pagina di documentazione i cui import non corrispondono a questo libro, controlla a quale versione punta prima di debuggare qualunque altra cosa. Parti della documentazione ufficiale portano ancora import dell'era v2.

::: {.callout .callout-warning}
[Sulla "v4" di cui potresti aver sentito parlare]{.callout-title}

Circolano programmi di corso e post di forum che parlano di una beta di NeuronAI v4, di solito promettendo tool approval di primo livello e valutazioni estese. Al momento della scrittura quel rilascio non è stato verificabile: il materiale di upgrade pubblicato copre solo v2 → v3, e l'SDK Laravel corrente si aggancia a `^3.15`.

Invece di tirare a indovinare, questo libro ti dà qualcosa di più duraturo: il Capitolo 26 è un capitolo di **strategia di versione** su come determinare che cosa hai davvero installato, come leggere un changelog cercando spostamenti di namespace che rompono, e come fissare le versioni perché un rilascio della libreria sia una decisione e non un disservizio. Prima di fidarti di qualunque affermazione sulla versione — inclusa questa — esegui `composer show neuron-core/neuron-ai --all`.
:::

### Esercizio

Riproduci a memoria il diagramma dei quattro pilastri. Poi, per ciascuno dei due progetti finali — A ("Repo Auditor CLI", Capitolo 24) e B ("Help desk agentico", Capitolo 25) — elenca quali pilastri e quali pezzi dell'ecosistema ti aspetti di dover usare. Conserva la risposta e confrontala con ciò che costruirai davvero: lo scarto è il feedback più utile che questo libro possa darti.

### Punti chiave

- Inspector per i trace; l'SDK Laravel per la comodità, non per le capacità.
- MCP porta dentro tool esterni — e con loro codice esterno.
- Questo libro punta alla v3.x; i namespace v1/v2 sono diversi e compaiono ancora nei risultati di ricerca.
