# Capitolo 13 — Il modello event-driven

::: {.callout .callout-warning}
[Prima di scrivere qualunque codice di workflow]{.callout-title}

Un workflow si esegue chiamando `run()` sul workflow stesso, e restituisce lo stato finale:

```php
$state = Workflow::make(workflowId: 'demo')->addNodes($nodes)->run();
```

I tutorial scritti per versioni precedenti chiamano `start()` o `init()` e passano per un oggetto handler; nessuno dei due esiste nella versione di questo libro. Il costruttore è `(?string $workflowId, ?WorkflowState $state)`, quindi il materiale che gli passa un oggetto di persistenza o un argomento `resumeToken:` fallisce. E l'`__invoke()` di un nodo prende l'evento e lo stato, più un terzo parametro facoltativo `WorkflowResources $resources` che porta i servizi che il nodo può usare; il Capitolo 14 tratta le resources dove parla dello stato.
:::

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch13`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch13), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
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

È il motivo per cui il Capitolo 2 ci insisteva. La Parte IV non è un argomento nuovo: è il livello che stava sotto le Parti II e III fin dall'inizio. È letterale, non una figura retorica: `Agent` è dichiarato come `class Agent extends Workflow`, e il ciclo di tool calling che hai usato nella Parte II è un insieme di nodi instradati dallo stesso motore che stai per programmare direttamente.

### Che cosa rende distintivo il workflow di NeuronAI

La documentazione nomina due capacità, e una terza sta sotto entrambe:

**Streaming** — un sistema multi-agente può spingere aggiornamenti ai client mentre gira.

**Interruzione** — il workflow può fermarsi a metà processo, chiedere input umano, aspettare e continuare dal nodo che si è messo in pausa — anche ore o giorni dopo, in un processo diverso.

**Durabilità** — ogni nodo che si completa viene registrato in uno store come *step*. Una run che va in crash, fallisce o si mette in pausa non riparte dall'inizio: gli step completati vengono riprodotti dallo store, e gira solo il lavoro non finito.

La terza è ciò che rende possibile la seconda. La maggior parte dei motori di workflow sa mettersi in pausa; pochi sanno fermarsi *dentro* un nodo, sopravvivere al riavvio di un processo e proseguire con il feedback umano iniettato nel punto in cui si erano fermati, senza rifare il lavoro costoso venuto prima. La Sezione 13.5 mostra gli step durevoli con un crash che puoi eseguire; il Capitolo 15 costruisce l'interruzione sopra di essi, ed è l'argomento più forte in assoluto a favore del framework.

### Punti chiave

- Nodi innescati da eventi, che restituiscono eventi che innescano altri nodi.
- Un nodo è qualunque cosa, da una riga a un agent intero.
- Agent e RAG *sono* workflow; questo è il substrato, non un'aggiunta.
- Streaming, interruzione e step durevoli sono le capacità distintive.

## 13.2 Nodo, evento, stato

### Evento

Una semplice classe PHP che implementa `Event`. Può avere qualunque nome e qualunque proprietà.

```php
namespace App\Neuron;

use NeuronAI\Workflow\Events\Event;

class FirstEvent implements Event
{
    public function __construct(public readonly string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(public readonly string $secondMsg){}
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
use NeuronAI\Workflow\Events\StartEvent;
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

La firma è rigida: prima un evento, poi un `WorkflowState` (o una sua sottoclasse), facoltativamente un `WorkflowResources` come terzo, e un tipo di ritorno fatto di eventi. Il workflow valida ogni nodo tramite reflection quando costruisce il grafo all'inizio di un'esecuzione, quindi una firma malformata fa fallire la run con il nome del nodo nel messaggio; `addNodes()` di per sé non la controlla.

### L'idea che fa scattare tutto

**La firma del metodo è il grafo.**

```text
public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
```

Leggila come una dichiarazione di cablaggio: *questo nodo gira quando compare uno `StartEvent`, e quando finisce emette un `FirstEvent`.*

Non c'è una definizione di arco separata, nessun file di configurazione, nessuna chiamata `addEdge()`. **I type hint sono il cablaggio.**

Lascialo sedimentare, perché tutto il resto della Parte IV ne discende:

- Vuoi un ciclo? Restituisci l'evento che innesca un nodo precedente.
- Vuoi una diramazione? Dichiara un tipo di ritorno unione.
- Vuoi conoscere il grafo? Leggi le firme.

::: {.callout .callout-warning}
[Nessuna classe `Edge`]{.callout-title}

Non esistono una classe `Edge` né `addEdges()`: gli archi sono i tipi di evento. Se trovi un tutorial che usa `new Edge(NodeA::class, NodeB::class)`, è stato scritto per una versione del framework molto più vecchia.
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

`set()` e `get()`, più `has()`, `delete()`, `only()` e `all()`. Disponibili a ogni nodo — e, poiché lo stato viene salvato a ogni step completato (Sezione 13.5), deve essere serializzabile. La Sezione 14.3 spiega che cosa questo esclude.

### Eventi e stato: quando usare l'uno o l'altro

Una distinzione che si sbaglia sistematicamente, quindi eccola esplicita:

**Gli eventi portano il messaggio.** Ciò che questo passo specifico ha prodotto, passato al passo specifico successivo. Effimeri, direzionali, tipizzati.

**Lo stato porta il contesto.** Cose di cui molti nodi hanno bisogno: l'utente, il tenant, i risultati accumulati, la configurazione. Persistenti per tutta l'esecuzione.

L'euristica: **se serve solo al nodo successivo, mettilo nell'evento. Se serve a più nodi, o ti serve dopo l'esecuzione, mettilo nello stato.**

Abusare dello stato produce un workflow in cui ogni nodo legge e scrive un contenitore globale — che è un workflow solo di nome, perché il flusso dei dati è di nuovo invisibile. Abusare degli eventi produce classi evento enormi che si passano tutto. Entrambi gli estremi sono peggio dell'equilibrio.

### Punti chiave

- Evento = semplice classe che implementa `Event`; `StartEvent` e `StopEvent` sono integrati.
- Nodo = classe con `__invoke(Event, WorkflowState): Event` — più un terzo parametro facoltativo `WorkflowResources`.
- **La firma del metodo è il grafo**: nessun arco da dichiarare.
- Eventi per il messaggio fra due passi; stato per il contesto condiviso.

## 13.3 Un workflow a un solo passo

### Tutto quanto

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
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

$state = Workflow::make(workflowId: 'demo')
    ->addNodes([
        new InitialNode(),
    ])
    ->run();

echo $state->get('answer'); // Hello World!
```

`StartEvent` in ingresso, `StopEvent` in uscita. Un nodo. `run()` restituisce il `WorkflowState` finale.

### Il ciclo di vita

1. `Workflow::make(workflowId: 'demo')` costruisce il workflow. Il suo costruttore accetta due argomenti opzionali, un workflow ID e uno stato iniziale. L'ID deve essere associato prima della run: il framework non ne genera mai uno, e `run()` su un workflow senza ID lancia una `WorkflowException`. Per ora va bene una stringa qualsiasi (la Sezione 13.5 spiega a cosa serve l'ID); lo stato iniziale per ora non ti serve.
2. `addNodes()` registra i nodi. **L'ordine nell'array non è l'ordine di esecuzione**: lo decidono gli eventi. L'array è un registro, non una sequenza.
3. `run()` esegue: genera un run ID, emette `StartEvent`, trova il nodo la cui firma lo accetta, lo esegue, registra il risultato come step, prende l'evento restituito, trova il nodo che accetta *quello*, e ripete fino a `StopEvent`. Restituisce lo stato finale.

Fra la costruzione di un workflow e la sua esecuzione non c'è nulla: lo eseguono `run()` e il suo fratello per lo streaming `events()` (Sezione 14.4), ed entrambi si chiamano sul workflow stesso. L'unica eccezione è la ripresa di una run in pausa, dove `submitInputs()` restituisce un `PendingExecution` su cui chiami poi `run()` o `events()` (Capitolo 15).

Il punto 2 merita enfasi. Venendo da pipeline procedurali, l'assunzione naturale è che l'ordine dell'array conti. Non conta, e capire perché significa capire il modello.

### La forma a classe

`addNodes()` è comodo per uno script. In un'applicazione un workflow è di solito una classe, e i suoi nodi arrivano dall'hook `nodes()`:

```php
use NeuronAI\Workflow\Workflow;

class GreetingWorkflow extends Workflow
{
    protected function nodes(): array
    {
        return [
            new InitialNode(),
        ];
    }
}

$state = GreetingWorkflow::make(workflowId: 'demo')->run();
```

Il motore chiama `nodes()` da capo all'inizio di ogni segmento di esecuzione, quindi il grafo è sempre costruito dalla configurazione corrente del workflow — il che conta quando una run può mettersi in pausa in un processo e proseguire in un altro.

### È utile?

Di per sé, no. Ma è il punto giusto da cui partire perché isola la meccanica dalla complessità, e perché la sezione successiva vi aggiunge una sola idea.

### Punti chiave

- `Workflow::make(workflowId: ...)->addNodes([...])->run()` restituisce lo stato finale; non c'è alcun handler.
- `addNodes()` è un registro, non una sequenza: sono gli eventi a determinare l'ordine.
- L'esecuzione va da `StartEvent` a `StopEvent`.
- In una sottoclasse, l'hook `nodes()` fornisce il grafo.

## 13.4 Multi-passo: gli eventi come cablaggio

### Gli eventi

```php
namespace App\Neuron;

use NeuronAI\Workflow\Events\Event;

class FirstEvent implements Event
{
    public function __construct(public readonly string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(public readonly string $secondMsg){}
}
```

### I nodi

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
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

$state = Workflow::make(workflowId: 'demo')
    ->addNodes([
        new InitialNode(),
        new NodeOne(),
        new NodeTwo(),
    ])
    ->run();
```

```
- Handling StartEvent
- InitialNode complete
- NodeOne complete
- NodeTwo complete
```

### Leggere il grafo dalle firme

Togli tutto tranne le tre firme:

```text
__invoke(StartEvent  $e, ...): FirstEvent
__invoke(FirstEvent  $e, ...): SecondEvent
__invoke(SecondEvent $e, ...): StopEvent
```

```
StartEvent → InitialNode → FirstEvent → NodeOne → SecondEvent → NodeTwo → StopEvent
```

Il grafo è lì, nelle dichiarazioni di tipo. Nessuna configurazione che possa andare fuori sincrono con il codice, e il tuo IDE lo naviga: clicca sul tipo dell'evento per trovare il nodo che lo consuma.

Anche il framework sa leggerlo. `$workflow->export()` percorre le stesse firme e stampa il grafo — come albero in console per default, o come diagramma Mermaid con `setExporter(new MermaidExporter())` — ed è un modo economico per verificare che il grafo che intendevi sia il grafo che hai scritto.

### I nomi, che contano più di quanto sembri

`FirstEvent` e `SecondEvent` vanno bene per un tutorial e sono terribili per un progetto reale. In produzione, dai agli eventi il nome di **ciò che è accaduto**:

```text
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

## 13.5 Step durevoli

### Ogni nodo è uno step

Finora un workflow sembra un modo ordinato di chiamare funzioni in un ordine deciso dai tipi. Sotto, è un piccolo motore di esecuzione durevole, e la differenza si vede la prima volta che qualcosa fallisce.

Quando un nodo restituisce, il motore non si limita a passare l'evento al nodo successivo. **Registra uno step** (commit): l'evento restituito e lo stato così com'è, scritti nella persistenza del workflow sotto l'identità della run. Solo allora instrada l'evento oltre. Nella configurazione di default quello store è in memoria e sparisce con il processo, ed è per questo che non te ne sei accorto. Dai al workflow un backend di persistenza che sopravviva al processo, e ogni nodo completato diventa un fatto che il motore non rifarà.

La conseguenza: una run che fallisce nel suo quinto nodo, e viene avviata di nuovo, **riproduce** (replay) i nodi da uno a quattro dallo store — i loro eventi e il loro stato vengono riletti, il loro `__invoke()` non viene chiamato — ed esegue solo il quinto.

### Il workflow ID

Per ritrovare una run, il motore ha bisogno di un nome per essa. Quel nome è il **workflow ID**, ed è la partizione dello store in cui vive ogni record della run. Puoi passarne uno esplicitamente — `Workflow::make(workflowId: 'report:42')` — ma l'abitudine migliore è lasciare che il workflow dichiari la propria chiave di business:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Workflow;

class ReportWorkflow extends Workflow
{
    public function __construct(private readonly int $reportId)
    {
        parent::__construct();
    }

    public function workflowId(): ?string
    {
        return 'report:' . $this->reportId;
    }

    protected function nodes(): array
    {
        return [
            new ResearchNode(),
            new PublishNode(),
        ];
    }
}
```

Qualunque processo in grado di costruire `ReportWorkflow::make(reportId: 42)` e di raggiungere lo stesso store può trovare questa run. Non c'è alcuna tabella che mappi i tuoi record su ID generati dal motore, perché la chiave di business *è* la posizione nello store. Un workflow che non dichiara nulla deve ricevere un ID da chi lo costruisce, con `make(workflowId: ...)`, `setWorkflowId()` o `for()`: il framework non se ne inventa mai uno, e `run()` su un workflow senza ID lancia un'eccezione. In ogni caso l'ID è leggibile da `$state->getWorkflowId()` dopo l'avvio della run.

Non confonderlo con il **run ID**. Ogni volta che una run parte sotto un workflow ID, il motore le assegna un run ID nuovo (`$state->getRunId()`), un marcatore di generazione usato per il tracing e per tagliare fuori gli scrittori obsoleti. Il workflow ID è l'handle con cui prosegui una run; il run ID ti dice quale tentativo stai guardando. La regola che ne discende: **una sola run attiva per workflow ID**. Avviarne una seconda mentre la prima è ancora in pausa o in esecuzione lancia una `RunInFlightException`.

### Memoizzare dentro uno step

Gli step hanno la dimensione di un nodo. Un nodo che fa una chiamata costosa e *poi* fallisce riparte dalla sua prima riga, e paga di nuovo la chiamata. `memoize()` chiude quel buco:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;
use RuntimeException;

class PublishNode extends Node
{
    /**
     * Stands in for a flaky HTTP endpoint: the first call fails.
     *
     * PHP 8.5: asymmetric visibility on a static property - anyone may read
     * the counter, only this node may change it.
     */
    public private(set) static int $publishCalls = 0;

    public function __invoke(ResearchDone $event, WorkflowState $state): StopEvent
    {
        $draft = $this->memoize('draft', function () use ($event): string {
            echo "- PublishNode: drafting from '{$event->notes}'\n";

            return 'Report based on: ' . $event->notes;
        });

        if (++self::$publishCalls === 1) {
            echo "- PublishNode: publishing... failed\n";
            throw new RuntimeException('Publisher unavailable');
        }

        echo "- PublishNode: publishing... done\n";
        $state->set('published', $draft);

        return new StopEvent();
    }
}
```

Il contatore è dichiarato `public private(set) static`: PHP 8.5 estende la visibilità asimmetrica alle proprietà statiche, così qualunque codice può leggere il contatore mentre solo il nodo stesso può modificarlo — una garanzia che un semplice `public static` non potrebbe dare.

La closure gira una volta sola. Il suo risultato viene registrato sotto il nome `draft` nel momento in cui restituisce, e quando il nodo gira di nuovo il valore torna dallo store senza che la closure venga chiamata. In un workflow reale la closure è la chiamata all'LLM, la richiesta HTTP, l'esecuzione del tool — qualunque cosa costosa o non deterministica.

Due regole la rendono sicura. **La closure deve dipendere solo dall'evento e dallo stato del nodo**, così il valore registrato è ancora la risposta giusta al replay. E **una memo non è una transazione**: un crash dopo la chiamata esterna ma prima che il suo risultato sia registrato ripete la chiamata. Dove una ripetizione avrebbe conseguenze — un pagamento, un'email — dai al sistema esterno una chiave di idempotenza.

::: {.callout .callout-warning}
[`checkpoint()` è il vecchio nome]{.callout-title}

I tutorial più vecchi usano `checkpoint()`. Esiste ancora, deprecato, e si limita a chiamare `memoize()`. Scrivi `memoize()`.
:::

### Vederlo all'opera

`ResearchNode`, il primo step, è l'ovvio nodo da due righe: consuma `StartEvent`, stampa `- ResearchNode: calling the slow research service` e restituisce un evento `ResearchDone` che porta le sue note.

Il repository di accompagnamento esegue il workflow due volte su una directory `FilePersistence`. Il primo tentativo fallisce in `PublishNode`; il secondo è un oggetto `ReportWorkflow` nuovo di zecca che non condivide nulla con il primo tranne la directory e il workflow ID che dichiara. Potrebbe benissimo essere un processo diverso, un giorno diverso:

```php
$storage = \sys_get_temp_dir() . '/neuron-book-ch13';
$persistence = new FilePersistence($storage);

echo "Attempt 1\n";
try {
    ReportWorkflow::make(reportId: 42)->setPersistence($persistence)->run();
} catch (RuntimeException $e) {
    echo "  caught: {$e->getMessage()}\n";
}

echo "\nAttempt 2\n";
$state = ReportWorkflow::make(reportId: 42)->setPersistence($persistence)->run();
```

```
Attempt 1
- ResearchNode: calling the slow research service
- PublishNode: drafting from 'Three sources, one counter-argument'
- PublishNode: publishing... failed
  caught: Publisher unavailable

Attempt 2
- PublishNode: publishing... done

Workflow ID: report:42
Published: 'Report based on: Three sources, one counter-argument'
Status: Completed
```

Il secondo `run()` ha trovato una run *fallita* sotto `report:42` e l'ha recuperata invece di ricominciare da capo. `ResearchNode` non ha stampato nulla, perché il suo step è stato riprodotto. La bozza non è stata riscritta, perché era memoizzata. Solo la chiamata di pubblicazione è stata rieseguita. Niente nel codice chiamante diceva "recupera": un semplice `run()` recupera automaticamente una run fallita, e ne avrebbe avviata una nuova se non ci fosse stato nulla da recuperare.

Il recupero automatico ha due spigoli. Primo: la run recuperata conserva il suo input *vecchio*. Se arriva una nuova richiesta sotto la stessa chiave di business mentre nello store c'è ancora una run fallita, un semplice `run()` porta a termine la vecchia run con il vecchio input, e la nuova richiesta viene assorbita in silenzio. Metti l'input della run nello start event (`setStartEvent()`), che viene salvato insieme alla run, così ciò che viene recuperato è ciò che era stato chiesto; e quando vuoi una generazione nuova, dillo esplicitamente con `run(ExecutionRequest::start())` (`NeuronAI\Workflow\Executor\ExecutionRequest`). Secondo: lo stato che inizializzi dal costruttore non è durevole finché uno step non viene registrato: una run che va in pausa o fallisce nel primo nodo e viene proseguita da un'istanza inizializzata diversamente vede il nuovo seed, non l'originale. Lo start event, a differenza del seed, viene salvato insieme alla run.

Quando la run si completa, il motore cancella i suoi record. Lo store contiene lavoro in corso, non storia, quindi non cresce, e il workflow ID è libero per la run successiva.

### Dove vivono i record

`setPersistence()` accetta qualunque backend che implementi `PersistenceInterface`. Quelli inclusi:

| Backend | Usalo per |
|---|---|
| `InMemoryPersistence` | Il default. Replay solo all'interno di un processo. |
| `FilePersistence` | Sviluppo, e deploy a processo singolo. |
| `DatabasePersistence` | Produzione con più worker (PDO, una tabella `workflow_store`). |
| `EloquentPersistence` | Lo stesso, tramite un modello Laravel. |
| `RedisPersistence` | Produzione con più worker, su Redis. |

Qualunque tu scelga, un workflow ID è una partizione, e ogni scrittura è una scrittura condizionale sul record di controllo della run, quindi due worker non possono far avanzare entrambi la stessa run. Il Capitolo 15 si basa su tutto questo per mettere in pausa una run in attesa di un essere umano; il Capitolo 22 lo porta su un database reale.

### Punti chiave

- Ogni nodo completato viene registrato come step durevole; una run recuperata riproduce gli step completati invece di rieseguirli.
- Il workflow ID dà il nome alla run nello store; dichiaralo con `workflowId()` come chiave di business. Il run ID è un timbro per singolo tentativo.
- Una sola run attiva per workflow ID; un semplice `run()` recupera automaticamente una run fallita, con il suo input originale; `run(ExecutionRequest::start())` ne avvia una nuova.
- `memoize('name', fn () => ...)` rende il lavoro costoso dentro un nodo sicuro al replay. Non è exactly-once: usa chiavi di idempotenza per gli effetti collaterali.
- Per default, il completamento cancella i record della run.

## 13.6 Perché non scrivere semplicemente uno script?

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

**Diversi cicli con checkpoint intermedi.** Fattibile con un `while`, finché non ti serve sapere a quale iterazione eri dopo un crash. In un workflow ogni iterazione è il proprio step durevole, quindi il motore lo sa già.

**Streaming di aggiornamenti in tempo reale.** Uno script può fare echo. Non può facilmente emettere eventi di avanzamento strutturati da profondità arbitraria senza far passare una callback attraverso ogni funzione.

**Fermarsi, aspettare, riprendere.** Questa non è una questione di sforzo. Persistere ogni step completato, fermarsi a metà nodo, proseguire in un processo diverso ore dopo senza ripetere il lavoro già fatto, e garantire che due worker non facciano mai avanzare la stessa run: non puoi scriverlo in uno script senza costruire un motore di workflow. E se ne costruisci uno, hai costruito la Sezione 13.5.

### I quattro benefici di sviluppo

Dalla documentazione:

**Modellare e mantenere scenari complessi.** Da pochi passi fino a cicli iterativi con checkpoint, usando gli stessi mattoni.

**Human in the loop.** Metti l'AI in aree sensibili perché un essere umano è sempre nel ciclo per le decisioni critiche.

**Streaming.** Aggiornamenti in tempo reale al client durante l'esecuzione.

**Debugging con Inspector.** Invece di chiederti perché il workflow ha preso una decisione, vedi esattamente che cosa è successo in ogni nodo.

Quest'ultimo si collega al Capitolo 10. Il motore emette un evento all'inizio e alla fine di ogni nodo, e qualunque observer — Inspector compreso — li trasforma in un trace di passi con un nome. Uno script mostra uno stack trace.

### La regola decisionale

Scrivi uno script quando: lineare, nessuna diramazione, nessun input umano, nessun bisogno di riprendere, nessuno streaming.

Scrivi un workflow quando **anche solo una** di queste è vera: più agent, approvazione umana, ripresa, lunga durata, streaming dell'avanzamento, o diramazioni e cicli non banali.

E l'argomento che chiude la questione, dai documenti:

> Se le cose si mettono male, Neuron ha già l'architettura adatta ad aiutarti a scalare a qualunque livello.

Non cambi framework quando arriva il requisito. Aggiungi un nodo.

### Punti chiave

- Per processi lineari semplici uno script è genuinamente migliore. Dillo.
- Concorrenza, checkpoint, streaming e ripresa sono dove gli script si rompono.
- Fermarsi e riprendere non è questione di sforzo: richiede step durevoli, cioè un motore.
- Un solo elemento scatenante basta a giustificare un workflow; non ti servono tutti.
