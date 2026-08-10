# Capitolo 13 — Il modello event-driven

::: {.callout .callout-warning}
[Prima di scrivere qualunque codice di workflow]{.callout-title}

La documentazione sui workflow contiene **due API di esecuzione diverse** fra le sue stesse pagine:

```php
// v3 style — Multi Step Workflow page
$handler = Workflow::make()->addNodes([...])->init();
$handler->run();

// v2 style — Loops & Branches page, and most blog posts
$state = Workflow::make()->addNodes([...])->start()->getResult();
```

Lo stile v2 mostra anche `Workflow::make(new WorkflowState(), $persistence, 'id')` e una classe `Edge` che **non esiste più in v3**: il modello event-driven l'ha sostituita del tutto.

Esegui un workflow minimo sulla tua versione installata e risolvi due cose: `init()`/`run()` contro `start()`/`getResult()`, e la firma del costruttore di `Workflow`. Questa parte usa la forma v3 `init()`/`run()` ovunque. Quasi ogni articolo di blog che troverai userà l'altra. Appendice A, punti da 30 a 32.
:::

## 13.1 Che cos'è un workflow

### La definizione

Un workflow è un modo event-driven, basato su nodi, di controllare il flusso di esecuzione di un'applicazione.

La tua applicazione è divisa in **nodi**, che vengono innescati da **eventi** e che a loro volta restituiscono eventi che innescano altri nodi. Combinali e puoi esprimere flussi arbitrariamente complessi.

La documentazione offre un paragone che vale la pena prendere in prestito: **"È come n8n a livello di codice."** Se hai visto uno strumento di automazione visuale, la cosa arriva subito — riquadri collegati da frecce, solo che i riquadri sono classi PHP e le frecce sono tipi.

### Un nodo può essere qualunque cosa

Da una singola riga di codice a un agent completo. Input e output arbitrari, passati in giro dagli eventi.

Quella flessibilità è il punto. Un nodo potrebbe:

- Chiamare un LLM
- Interrogare il tuo database
- Eseguire un retrieval RAG
- Mandare un'email
- Aspettare un essere umano
- Essere un intero `Agent` che fa il proprio ciclo di tool calling

### L'affermazione della Sezione 2.3, alla fonte

> Le classi Agent e RAG sono esse stesse dei workflow. Rappresentano implementazioni pronte all'uso dei pattern più comuni per chiamate a tool, retrieval e structured output. Il Workflow ti permette di programmare il tuo sistema agentico completamente da zero. Agent e RAG possono essere usati dentro un Workflow per svolgere compiti come qualunque altro componente.

È il motivo per cui il Capitolo 2 ci insisteva. La Parte IV non è un argomento nuovo: è il livello che stava sotto le Parti II e III fin dall'inizio.

### Che cosa rende distintivo il workflow di NeuronAI

La documentazione nomina due capacità:

**Streaming** — un sistema multi-agente può spingere aggiornamenti ai client mentre gira.

**Interruzione** — il workflow può fermarsi a metà processo, chiedere input umano, aspettare e continuare esattamente da dove si era fermato — anche ore o giorni dopo.

La seconda è insolita. La maggior parte dei motori di workflow sa mettersi in pausa; pochi sanno fermarsi *dentro* un nodo, serializzare l'intero contesto di esecuzione, sopravvivere al riavvio di un processo e riprendere con il feedback umano iniettato esattamente nel punto in cui si erano fermati. È il Capitolo 15, ed è l'argomento più forte in assoluto a favore del framework.

### Punti chiave

- Nodi innescati da eventi, che restituiscono eventi che innescano altri nodi.
- Un nodo è qualunque cosa, da una riga a un agent intero.
- Agent e RAG *sono* workflow; questo è il substrato, non un'aggiunta.
- Streaming e interruzione sono le capacità distintive.

## 13.2 Nodo, evento, stato

### Evento

Una semplice classe PHP che implementa `Event`. Può avere qualunque nome e qualunque proprietà.

```php
namespace App\Neuron;

class FirstEvent implements Event
{
    public function __construct(protected string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(protected string $secondMsg){}
}
```

Generali:

```bash
vendor/bin/neuron make:event App\\Neuron\\FirstEvent
```

Due eventi speciali arrivano con il framework:

- **`StartEvent`** — quello con cui il workflow inizia
- **`StopEvent`** — quello che lo termina

### Nodo

Una classe che estende `Node` con un solo metodo:

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\WorkflowState;

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
    {
        echo "\n- Handling StartEvent";

        return new FirstEvent("InitialNode complete");
    }
}
```

```bash
vendor/bin/neuron make:node App\\Neuron\\InitialNode
```

### L'idea che fa scattare tutto

**La firma del metodo è il grafo.**

```php
public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
```

Leggila come una dichiarazione di cablaggio: *questo nodo gira quando compare uno `StartEvent`, e quando finisce emette un `FirstEvent`.*

Non c'è una definizione di arco separata, nessun file di configurazione, nessuna chiamata `addEdge()`. **I type hint sono il cablaggio.**

Lascialo sedimentare, perché tutto il resto della Parte IV ne discende:

- Vuoi un ciclo? Restituisci l'evento che innesca un nodo precedente.
- Vuoi una diramazione? Dichiara un tipo di ritorno unione.
- Vuoi conoscere il grafo? Leggi le firme.

::: {.callout .callout-warning}
[Nota storica]{.callout-title}

La versione 1 aveva una classe `Edge` esplicita e `addEdges()`. La v2 l'ha rimossa in favore del modello a eventi. Se trovi un tutorial che usa `new Edge(NodeA::class, NodeB::class)`, precede l'architettura attuale di due versioni major. Appendice A, punto 32.
:::

### Stato

`WorkflowState` è il contenitore condiviso che viaggia attraverso l'esecuzione:

```php
class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): StopEvent
    {
        $state->set('message', 'Hello World!');

        return new StopEvent();
    }
}
```

`set()` e `get()`. Disponibili a ogni nodo.

### Eventi e stato: quando usare l'uno o l'altro

Una distinzione che si sbaglia sistematicamente, quindi eccola esplicita:

**Gli eventi portano il messaggio.** Ciò che questo passo specifico ha prodotto, passato al passo specifico successivo. Effimeri, direzionali, tipizzati.

**Lo stato porta il contesto.** Cose di cui molti nodi hanno bisogno: l'utente, il tenant, i risultati accumulati, la configurazione. Persistenti per tutta l'esecuzione.

L'euristica: **se serve solo al nodo successivo, mettilo nell'evento. Se serve a più nodi, o ti serve dopo l'esecuzione, mettilo nello stato.**

Abusare dello stato produce un workflow in cui ogni nodo legge e scrive un contenitore globale — che è un workflow solo di nome, perché il flusso dei dati è di nuovo invisibile. Abusare degli eventi produce classi evento enormi che si passano tutto. Entrambi gli estremi sono peggio dell'equilibrio.

### Punti chiave

- Evento = semplice classe che implementa `Event`; `StartEvent` e `StopEvent` sono integrati.
- Nodo = classe con `__invoke(Event, WorkflowState): Event`.
- **La firma del metodo è il grafo**: nessun arco da dichiarare.
- Eventi per il messaggio fra due passi; stato per il contesto condiviso.

## 13.3 Un workflow a un solo passo

### Tutto quanto

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\StopEvent;
use NeuronAI\Workflow\WorkflowState;

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): StopEvent
    {
        $state->set('answer', 'Hello World!');

        return new StopEvent();
    }
}
```

```php
use NeuronAI\Workflow\Workflow;

$handler = Workflow::make()
    ->addNodes([
        new InitialNode(),
    ])
    ->init();

$handler->run();
```

`StartEvent` in ingresso, `StopEvent` in uscita. Un nodo.

### Il ciclo di vita

1. `Workflow::make()` costruisce il workflow.
2. `addNodes()` registra i nodi. **L'ordine nell'array non è l'ordine di esecuzione**: lo decidono gli eventi. L'array è un registro, non una sequenza.
3. `init()` prepara l'esecuzione e restituisce un handler.
4. `run()` esegue: emetti `StartEvent`, trova il nodo la cui firma lo accetta, eseguilo, prendi l'evento restituito, trova il nodo che accetta *quello*, ripeti fino a `StopEvent`.

Il punto 2 merita enfasi. Venendo da pipeline procedurali, l'assunzione naturale è che l'ordine dell'array conti. Non conta, e capire perché significa capire il modello.

### È utile?

Di per sé, no. Ma è il punto giusto da cui partire perché isola la meccanica dalla complessità, e perché la sezione successiva vi aggiunge una sola idea.

### Punti chiave

- `Workflow::make()->addNodes([...])->init()` e poi `run()`.
- `addNodes()` è un registro, non una sequenza: sono gli eventi a determinare l'ordine.
- L'esecuzione va da `StartEvent` a `StopEvent`.

## 13.4 Multi-passo: gli eventi come cablaggio

### Gli eventi

```php
namespace App\Neuron;

class FirstEvent implements Event
{
    public function __construct(protected string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(protected string $secondMsg){}
}
```

### I nodi

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use App\Neuron\FirstEvent;

class InitialNode extends Node
{
    /**
     * Gets the "StartEvent" and returns "FirstEvent"
     */
    public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
    {
        echo "\n- Handling StartEvent";

        return new FirstEvent("InitialNode complete");
    }
}
```

```php
class NodeOne extends Node
{
    /**
     * Takes "FirstEvent" as input and returns "SecondEvent"
     */
    public function __invoke(FirstEvent $event, WorkflowState $state): SecondEvent
    {
        echo "\n- ".$event->firstMsg;

        return new SecondEvent("NodeOne complete");
    }
}
```

```php
class NodeTwo extends Node
{
    /**
     * Takes "SecondEvent" as input and returns "StopEvent"
     */
    public function __invoke(SecondEvent $event, WorkflowState $state): StopEvent
    {
        echo "\n- ".$event->secondMsg;
        echo "\n- NodeTwo complete";

        return new StopEvent();
    }
}
```

### Eseguirlo

```php
use NeuronAI\Workflow\Workflow;

$handler = Workflow::make()
    ->addNodes([
        new InitialNode(),
        new NodeOne(),
        new NodeTwo(),
    ])
    ->init();

$handler->run();
```

```
- Handling StartEvent
- InitialNode complete
- NodeOne complete
- NodeTwo complete
```

### Leggere il grafo dalle firme

Togli tutto tranne le tre firme:

```php
__invoke(StartEvent  $e, ...): FirstEvent
__invoke(FirstEvent  $e, ...): SecondEvent
__invoke(SecondEvent $e, ...): StopEvent
```

```
StartEvent → InitialNode → FirstEvent → NodeOne → SecondEvent → NodeTwo → StopEvent
```

Il grafo è lì, nelle dichiarazioni di tipo. Nessuna configurazione che possa andare fuori sincrono con il codice, e il tuo IDE lo naviga: clicca sul tipo dell'evento per trovare il nodo che lo consuma.

### I nomi, che contano più di quanto sembri

`FirstEvent` e `SecondEvent` vanno bene per un tutorial e sono terribili per un progetto reale. In produzione, dai agli eventi il nome di **ciò che è accaduto**:

```php
ArticleDrafted
ResearchCompleted
ReviewRejected
RefundApproved
PaymentFailed
```

Fatti al passato, non posizioni in una sequenza. Allora la firma si legge come una frase: *questo nodo gira quando un articolo è stato redatto e produce una richiesta di revisione*. Chi legge il codice sei mesi dopo capisce il flusso senza un diagramma.

È l'ordinaria denominazione degli eventi di dominio della progettazione event-driven, e si applica qui senza modifiche.

### Un campo per evento, o tutto il contesto?

Tieni piccoli gli eventi. Un evento dovrebbe portare ciò che serve al nodo *successivo*, non tutto ciò che si è accumulato finora. Il contesto condiviso ampio appartiene allo stato (Sezione 14.3). Un evento che arriva a quindici proprietà ti sta dicendo che i suoi dati appartengono allo stato.

### Punti chiave

- Tre nodi, tre firme, un grafo.
- Le dichiarazioni di tipo sono il cablaggio: leggibili e navigabili dall'IDE.
- Dai agli eventi nomi di fatti di dominio al passato, non `FirstEvent`.
- Tieni piccoli gli eventi; metti il contesto condiviso nello stato.

## 13.5 Perché non scrivere semplicemente uno script?

### L'obiezione

La documentazione la solleva da sé, il che è un buon segno:

> "Sembra ottimo, ma perché non posso scrivere un normale script PHP con qualche if e qualche funzione?"

E ammette: *"È una domanda legittima, e me la sono sentita fare spesso mentre costruivo Neuron."*

### La risposta onesta per i casi semplici

**Per un processo lineare in tre passi, uno script è meglio.** Meno file, meno indirezione, più facile da leggere. La risposta del framework stesso lo concede: il potenziale non è visibile quando il caso d'uso è semplice, ed è normale.

Non vendertelo troppo bene. Adottare i workflow per tutto produce una base di codice in cui una chiamata di funzione è diventata quattro classi, e te ne pentirai.

### Dove lo script si rompe

La risposta documentata elenca le condizioni, e ciascuna corrisponde a un costo reale:

**Più diramazioni eseguite in concorrenza.** Farlo in uno script significa `pcntl_fork` e raccolta manuale dei risultati. La Sezione 14.2 lo mostra come tipo di ritorno.

**Diversi cicli con checkpoint intermedi.** Fattibile con un `while`, finché non ti serve sapere a quale iterazione eri dopo un crash.

**Streaming di aggiornamenti in tempo reale.** Uno script può fare echo. Non può facilmente emettere eventi di avanzamento strutturati da profondità arbitraria senza far passare una callback attraverso ogni funzione.

**Fermarsi, aspettare, riprendere.** Questa non è una questione di sforzo. Serializzare l'intero stato di esecuzione a metà funzione, persisterlo, riprendere in un processo diverso ore dopo: non puoi scriverlo in uno script senza costruire un motore di workflow. E se ne costruisci uno, hai costruito questo.

### I quattro benefici di sviluppo

Dalla documentazione:

**Modellare e mantenere scenari complessi.** Da pochi passi fino a cicli iterativi con checkpoint, usando gli stessi mattoni.

**Human in the loop.** Metti l'AI in aree sensibili perché un essere umano è sempre nel ciclo per le decisioni critiche.

**Streaming.** Aggiornamenti in tempo reale al client durante l'esecuzione.

**Debugging con Inspector.** Invece di chiederti perché il workflow ha preso una decisione, vedi esattamente che cosa è successo in ogni nodo.

Quest'ultimo si collega al Capitolo 10. I nodi sono unità con un nome, quindi un trace mostra passi con un nome. Uno script mostra uno stack trace.

### La regola decisionale

Scrivi uno script quando: lineare, nessuna diramazione, nessun input umano, nessun bisogno di riprendere, nessuno streaming.

Scrivi un workflow quando **anche solo una** di queste è vera: più agent, approvazione umana, ripresa, lunga durata, streaming dell'avanzamento, o diramazioni e cicli non banali.

E l'argomento che chiude la questione, dai documenti:

> Se le cose si mettono male, Neuron ha già l'architettura adatta ad aiutarti a scalare a qualunque livello.

Non cambi framework quando arriva il requisito. Aggiungi un nodo.

### Punti chiave

- Per processi lineari semplici uno script è genuinamente migliore. Dillo.
- Concorrenza, checkpoint, streaming e ripresa sono dove gli script si rompono.
- Fermarsi e riprendere non è questione di sforzo: richiede un motore.
- Un solo elemento scatenante basta a giustificare un workflow; non ti servono tutti.
