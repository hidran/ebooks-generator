# Capitolo 14 — Cicli, diramazioni e stato

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch14`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch14), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 14.1 Cicli

### Un ciclo è un tipo di ritorno

```php
class NodeOne extends Node
{
    public function __invoke(FirstEvent $event, WorkflowState $state): FirstEvent|SecondEvent
    {
        echo "\n- ".$event->firstMsg;

        if (rand(0, 1) === 1) {
            // Returning FirstEvent triggers another execution of NodeOne
            return new FirstEvent("Running a loop on NodeOne");
        }

        return new SecondEvent("NodeOne complete, move forward");
    }
}
```

Il nodo consuma `FirstEvent` e può anche *restituire* `FirstEvent`. Restituirlo lo innesca di nuovo.

Output:

```
- Handling StartEvent
- InitialNode complete
- Running a loop on NodeOne
- Running a loop on NodeOne
- NodeOne complete, move forward
- NodeTwo complete
```

### La regola da non dimenticare

> Devi dichiarare **tutti i possibili eventi di ritorno** nella firma del metodo, perché il Workflow possa costruire la catena di esecuzione.

`FirstEvent|SecondEvent`. L'unione non è decorazione. PHP la fa rispettare: restituisci un evento che non è nella firma e il nodo muore con un `TypeError` — `Return value must be of type FirstEvent, SecondEvent returned` — sull'unico percorso che lo restituisce, che di solito è la diramazione rara che nessuno ha esercitato nei test.

La correzione allettante è allargare il tipo di ritorno a un semplice `Event`. Funziona, e ti costa proprio ciò di cui parlava il Capitolo 13: la firma non dice più dove può andare il flusso, quindi non lo sa più un lettore, né `export()`, che disegna il grafo proprio da quei tipi di ritorno.

È il bug numero uno dei workflow, e la causa è sempre la stessa: un tipo unione che qualcuno ha dimenticato di allargare dopo aver aggiunto una diramazione.

### Cicli verso qualunque punto

> Puoi creare un ciclo da qualunque nodo verso qualunque altro nodo definendo gli eventi di ingresso e di ritorno appropriati. Un nodo può perfino restituire uno `StartEvent` per saltare direttamente al primo nodo del workflow.

Restituire `StartEvent` riavvia il flusso dall'inizio — all'interno della stessa run, quindi lo stato conserva tutto ciò che è stato scritto finora. Il `run/loop.php` del repository di accompagnamento è costruito esattamente su questo: il revisore restituisce `StartEvent` a un rifiuto, e il nodo scrittore che lo consuma legge dallo stato il feedback del revisore e produce la bozza successiva.

### La protezione che devi scrivere tu

Il framework non fermerà un ciclo infinito. Se la tua condizione non diventa mai falsa, il workflow gira per sempre.

Usa lo stato come contatore:

```php
class ReviewNode extends Node
{
    private const MAX_ATTEMPTS = 3;

    public function __invoke(DraftReady $event, WorkflowState $state): DraftReady|ArticleApproved
    {
        $attempts = (int) $state->get('review_attempts', 0);

        $verdict = $this->memoize('verdict', fn (): Verdict => ReviewerAgent::make()
            ->structured(new UserMessage($event->draft), Verdict::class));

        if ($verdict->approved) {
            return new ArticleApproved($event->draft);
        }

        if ($attempts + 1 >= self::MAX_ATTEMPTS) {
            $state->set('escalate_reason', 'review_limit_reached');

            return new ArticleApproved($event->draft); // or an EscalationEvent
        }

        $state->set('review_attempts', $attempts + 1);
        $state->set('last_feedback', $verdict->feedback);

        return new DraftReady($event->draft);
    }
}
```

Tre cose che questo dimostra oltre al contatore:

**Ogni iterazione è il proprio step durevole.** Il motore numera gli step mentre attraversa il grafo, quindi il terzo passaggio in `ReviewNode` è uno step diverso dal primo, con il contatore nello stato registrato insieme a esso. Una run che va in crash alla terza revisione e viene recuperata riproduce le prime due dallo store e riprende dalla terza — e il `memoize()` attorno alla chiamata al revisore (Sezione 13.5) è limitato a quell'iterazione, quindi il verdetto già pagato in un dato passaggio non viene mai richiesto due volte.

**Ogni iterazione del ciclo costa chiamate all'LLM.** È di nuovo la Sezione 1.4. Un ciclo di revisione illimitato è una fattura illimitata.

**Abbi un piano per quando si raggiunge il limite.** Passare la palla a un essere umano batte il pubblicare in silenzio la terza bozza. È il ponte naturale verso il Capitolo 15.

### I cicli sono dove i sistemi agentici si guadagnano il posto

Un ciclo con dentro un LLM è *raffinamento iterativo*: redigi, critica, rivedi, ripeti finché non è abbastanza buono. Quel pattern — scrittore più critico — è una delle forme multi-agente di maggior valore, ed è un workflow a tre nodi con un solo tipo di ritorno unione.

### Punti chiave

- Un ciclo è un nodo che restituisce un evento che innesca di nuovo un nodo precedente.
- **Dichiara ogni possibile tipo di ritorno nell'unione**: il bug di workflow più comune.
- Restituire `StartEvent` riavvia l'intero workflow.
- Il framework non limita i cicli; conta nello stato e pianifica per il limite.
- Ogni iterazione è uno step durevole separato; memoizza la chiamata all'LLM al suo interno.

## 14.2 Diramazioni, sequenziali e parallele

### Diramazione condizionale

Stesso meccanismo di un ciclo — un tipo di ritorno unione, ma le alternative portano a nodi diversi:

```php
class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): BranchA1Event|BranchB1Event
    {
        if ($this->shouldTakeA($state)) {
            return new BranchA1Event('Going down branch A');
        }

        return new BranchB1Event('Going down branch B');
    }
}
```

Ogni diramazione prosegue poi attraverso i propri nodi e alla fine raggiunge `StopEvent`, oppure riconverge su un tipo di evento condiviso.

**Un trucco di convergenza che vale la pena conoscere:** per riunire due diramazioni, fai in modo che l'ultimo nodo di ciascuna restituisca lo *stesso* tipo di evento. Qualunque diramazione sia stata eseguita, lo stesso nodo a valle la raccoglie. È così che costruisci forme a diamante senza alcuna sintassi di giunzione.

::: {.callout .callout-warning}
[Non copiare il nome della classe dai documenti]{.callout-title}

L'esempio di diramazione della documentazione chiama la classe `BrancheA1Event` — con una `e` di troppo. Appendice A, punto 33.
:::

### Diramazioni parallele

La diramazione condizionale sceglie un percorso. Quella parallela si biforca in diversi, ciascuno eseguito fino alla propria fine, e ne riunisce i risultati.

La biforcazione restituisce un `ParallelEvent`. Dagli una sottoclasse propria, perché il nodo di riunione viene instradato proprio in base a quella classe — la stessa regola un-evento-un-nodo di ovunque — e una sottoclasse con un nome permette a un workflow di contenere più di una biforcazione:

```php
use NeuronAI\Workflow\Events\ParallelEvent;

class DocumentProcessingStarted extends ParallelEvent
{
}

class DocumentProcessing extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): DocumentProcessingStarted
    {
        return new DocumentProcessingStarted([
            'text'  => new TextProcessEvent(),
            'image' => new ImageProcessEvent(),
        ]);
    }
}
```

Ogni diramazione è una **chiave con nome** che mappa sul primo evento di quella diramazione. I nomi sono obbligatori: una semplice lista viene rifiutata, perché il nome diventa l'identità della diramazione. I nodi che gestiscono quegli eventi, e tutto ciò che sta a valle in ciascuna diramazione, si registrano normalmente nel workflow:

```php
class MyWorkflow extends Workflow
{
    protected function nodes(): array
    {
        return [
            new DocumentProcessing(),

            // "text" branch
            new DescriptionGenerationNode(),
            new TextRefactorNode(),

            // "image" branch
            new ImageProcessNode(),
            new AddWatermarkNode(),

            new MergeNode(),
        ];
    }
}
```

### Restituire risultati da una diramazione

Ogni diramazione termina quando il suo ultimo nodo restituisce uno `StopEvent`, e **lo `StopEvent` porta il risultato**:

```php
class TextRefactorNode extends Node
{
    public function __invoke(TextProcessEvent $event, WorkflowState $state): StopEvent
    {
        // do the work
        return new StopEvent(result: $refinedText);
    }
}
```

Una volta completate tutte le diramazioni, la stessa istanza di `DocumentProcessingStarted`, che ora contiene il risultato di ogni diramazione, viene instradata al nodo che la accetta. Quel nodo è il punto di fusione, e legge ciascun risultato per nome:

```php
class MergeNode extends Node
{
    public function __invoke(DocumentProcessingStarted $event, WorkflowState $state): StopEvent
    {
        $textResult  = $event->getResult('text');
        $imageResult = $event->getResult('image');

        // Combine, persist, return a final event...
        return new StopEvent();
    }
}
```

### La regola di isolamento — la parte importante

> Ogni diramazione riceve una **copia isolata** dello stato del workflow. Le diramazioni partono dallo stesso snapshot, ma le mutazioni all'interno di una diramazione non si propagano alle diramazioni sorelle né al workflow principale. **L'unico modo di far tornare indietro dei dati è il risultato dello `StopEvent`.**

È intenzionale, e il ragionamento regge: con stato mutabile condiviso fra diramazioni concorrenti ottieni una corsa critica, e poi una sessione di debug del tipo "chi ha scritto questo valore?" che non piace a nessuno.

La conseguenza pratica, ed è la cosa su cui inciampano tutti: **una diramazione che scrive su `$state` sta scrivendo su una copia che verrà buttata.** Se vuoi far uscire dei dati da una diramazione, vanno nel risultato dello `StopEvent`. Punto.

### Parallelo non significa concorrente finché non lo dici tu

L'executor di default esegue le diramazioni **una dopo l'altra**. L'isolamento, i risultati con nome e la fusione funzionano tutti, ma il tempo trascorso è la somma delle diramazioni. Per una concorrenza reale, sostituisci l'executor:

```php
use NeuronAI\Workflow\Executor\AsyncExecutor;

$state = MyWorkflow::make()
    ->setExecutor(new AsyncExecutor())
    ->run();
```

`AsyncExecutor` esegue ogni diramazione in una fiber di Amp e richiede che `amphp/amp` sia installato — NeuronAI non lo richiede, e senza di esso la biforcazione fallisce con `Call to undefined function Amp\async()`. Le fiber si sovrappongono solo mentre una di esse è in attesa di I/O, quindi per le diramazioni che chiamano un modello anche il provider ha bisogno dell'`AmpHttpClient` non bloccante (da `amphp/http-client`), impostato con `setHttpClient()`. Con entrambi, due chiamate al modello si completano nel tempo della più lenta. Con il solo executor, restano comunque in coda l'una dietro l'altra.

Gli step delle diramazioni sono durevoli come tutti gli altri: ogni nodo dentro ogni diramazione viene registrato come step a sé, quindi una run recuperata non rifà le diramazioni già terminate. Che cosa succede quando una diramazione si mette in pausa in attesa di un essere umano è affare del Capitolo 15; in breve, le diramazioni si mettono in pausa una alla volta.

::: {.callout .callout-tip}
[In pratica]{.callout-title}

Riproducilo deliberatamente una volta — imposta lo stato in una diramazione, leggilo nel nodo di fusione, guarda che non c'è — poi correggi con il risultato. Cinque minuti, e la regola si fissa in un modo che la lettura non ottiene.
:::

### Quando le diramazioni parallele si ripagano

Stessa forma della Sezione 5.13: **lavoro indipendente e legato all'I/O**, eseguito con `AsyncExecutor`. Tre agent che analizzano lo stesso documento da angolazioni diverse. Due chiamate API che non dipendono l'una dall'altra. Elaborazione di testo e immagine di un unico caricamento.

Non utili per: dipendenze sequenziali, o lavoro banalmente veloce dove il coordinamento costa più di quanto risparmi.

### Punti chiave

- La diramazione condizionale è un tipo di ritorno unione; converge restituendo un tipo di evento condiviso.
- Una sottoclasse di `ParallelEvent` con diramazioni con nome biforca; il nodo che accetta quella sottoclasse riunisce.
- Le diramazioni terminano con `StopEvent(result: ...)`; il nodo di fusione legge `getResult('name')`.
- Per default le diramazioni girano in sequenza; `AsyncExecutor` più `amphp/amp` (e `AmpHttpClient` per i provider) le rende concorrenti.
- **Lo stato di una diramazione è una copia isolata**: le mutazioni vengono scartate; restituisci i dati tramite il risultato.

## 14.3 Gestire lo stato

### Il default

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\WorkflowState;

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): StopEvent
    {
        $state->set('message', 'Hello World!');

        return new StopEvent();
    }
}
```

Un contenitore a chiavi stringa con `set()` e `get()`. Va bene per workflow piccoli e prototipi. Puoi anche popolarlo prima della run: `Workflow::make(state: new WorkflowState(['topic' => $topic]))`.

### Le sue debolezze, dette chiaramente

- **I refusi sono silenziosi.** `$state->get('user_id')` contro `$state->set('userId', ...)` restituisce null senza lamentarsi.
- **Niente tipi.** Tutto è `mixed`; l'analisi statica non vede nulla.
- **Nessuna scopribilità.** Nulla dice a un nuovo sviluppatore quali chiavi esistono. Fai grep.

Per un workflow a tre nodi è accettabile. Per un sistema mantenuto da un team, no.

### CustomState

```php
use App\Models\User;
use NeuronAI\Workflow\WorkflowState;

class CustomState extends WorkflowState
{
    protected User $user;

    public function setUser(User $user): CustomState
    {
        $this->user = $user;
        return $this;
    }

    public function getUser(): User
    {
        return $this->user;
    }
}
```

I nodi lo accettano al posto di `WorkflowState`:

```php
class ExampleNode extends Node
{
    public function __invoke(StartEvent $event, CustomState $state): StopEvent
    {
        // Use state properties in your nodes
        if ($state->getUser()->isAdmin()) {
            //...
        }

        return new StopEvent();
    }
}
```

Il secondo parametro di `__invoke()` può essere qualunque sottoclasse di `WorkflowState`; il workflow lo verifica quando valida il nodo.

Poi iniettalo. Il costruttore di `Workflow` è `(?string $workflowId, ?WorkflowState $state)`, quindi per un workflow usa e getta passalo per nome:

```php
$state = Workflow::make(state: (new CustomState())->setUser($user))
    ->addNodes([
        new ExampleNode(),
    ])
    ->run();
```

Per una classe workflow, restituiscilo invece dall'hook `state()`, e di' all'analisi statica quale stato porta il workflow:

```php
/** @extends Workflow<CustomState> */
class ExampleWorkflow extends Workflow
{
    protected function state(): CustomState
    {
        return new CustomState();
    }

    protected function nodes(): array
    {
        return [
            new ExampleNode(),
        ];
    }
}

$state = ExampleWorkflow::make()->run(); // PHPStan infers CustomState
```

L'annotazione `@extends` è ciò che fa sì che il tipo di ritorno di `run()` sia `CustomState` invece di `WorkflowState` per PHPStan e per il tuo IDE — lo stesso meccanismo che `Agent` usa per restituire un `AgentState`. Il materiale scritto per le versioni precedenti inietta lo stato come terzo argomento del costruttore, dopo la persistenza e un resume token; in v4 quella chiamata fallisce. Appendice A, punto 37.

### Perché è il default giusto per il lavoro vero

**Accessori tipizzati.** `getUser(): User` — completamento nell'IDE, copertura di PHPStan, supporto al refactoring.

**Autodocumentante.** La classe *è* l'elenco di ciò che questo workflow porta con sé. L'onboarding diventa "leggi `OrderWorkflowState`".

**Un posto per la logica.** I valori derivati appartengono all'oggetto stato, non ripetuti in quattro nodi:

```php
class ContentWorkflowState extends WorkflowState
{
    protected array $revisions = [];

    public function addRevision(string $draft, string $feedback): self
    {
        $this->revisions[] = ['draft' => $draft, 'feedback' => $feedback];
        return $this;
    }

    public function revisionCount(): int
    {
        return \count($this->revisions);
    }

    public function hasReachedLimit(int $max = 3): bool
    {
        return $this->revisionCount() >= $max;
    }

    public function lastFeedback(): ?string
    {
        $last = \end($this->revisions);
        return $last === false ? null : $last['feedback'];
    }
}
```

Ora la protezione del ciclo della Sezione 14.1 si legge come `$state->hasReachedLimit()` in ogni nodo che ne ha bisogno, definita una volta sola.

### Il vincolo di serializzazione

Cruciale per tutto ciò che è durevole, e vale la pena saperlo ora così non è una sorpresa:

**Lo stato viene serializzato ogni volta che uno step viene registrato.** Non solo quando un workflow si mette in pausa — dopo ogni nodo, in ogni run, anche una semplice run in memoria, perché è questo che è uno step durevole (Sezione 13.5). Il che significa:

- **Le risorse non possono essere serializzate.** Connessioni al database, handle di file, socket aperti. Conserva un identificativo e ristabilisci la connessione dentro il nodo che ne ha bisogno.
- Lo stesso vale per le closure e per qualunque cosa contenga indirettamente una risorsa o una closure.

Metti un `PDO` nello stato e la run fallisce nel momento in cui il nodo che l'ha salvato restituisce: `Serialization of 'PDO' is not allowed`. È la buona notizia — fallisce presto, accanto alla riga che l'ha causato, invece che ore dopo al confine di una pausa.

**Conserva ID, non oggetti con connessioni.** `protected int $userId` invece di un modello idratato che porta con sé una connessione viva. Se un oggetto di stato ha davvero bisogno di una dipendenza viva, l'hook `restoreState()` del workflow è il punto in cui la ricolleghi allo stato riletto dallo store.

**Le diramazioni parallele clonano lo stato.** Il contenitore `data` dietro `get()`/`set()` viene copiato in profondità per ogni diramazione. Una sottoclasse che tiene *oggetti* mutabili nelle proprie proprietà deve definire `__clone()` perché le copie siano davvero indipendenti; semplici scalari e array, come le revisioni di `ContentWorkflowState`, non richiedono nulla.

### Punti chiave

- `WorkflowState` è un contenitore a chiavi stringa: bene in piccolo, debole su scala.
- `CustomState` dà accessori tipizzati, scopribilità e una casa per la logica derivata.
- Inietta con `Workflow::make(state: ...)`, oppure con l'hook `state()` più `@extends Workflow<CustomState>`.
- **Lo stato viene serializzato a ogni registrazione di uno step**: niente risorse, niente connessioni, niente closure.
- Conserva gli ID e reidrata dentro il nodo.

## 14.4 Streaming di un workflow

### Una sola parola chiave

Aggiungi `\Generator` al tipo di ritorno e usa `yield`:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\WorkflowState;

class ProgressEvent
{
    public function __construct(public readonly string $message){}
}

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): \Generator|FirstEvent
    {
        yield new ProgressEvent("Handling StartEvent");

        return new FirstEvent("InitialNode complete");
    }
}

class NodeOne extends Node
{
    public function __invoke(FirstEvent $event, WorkflowState $state): \Generator|SecondEvent
    {
        yield new ProgressEvent($event->firstMsg);

        return new SecondEvent("NodeOne complete");
    }
}

class NodeTwo extends Node
{
    public function __invoke(SecondEvent $event, WorkflowState $state): \Generator|StopEvent
    {
        yield new ProgressEvent($event->secondMsg);
        yield new ProgressEvent("NodeTwo complete");

        $state->set('message', 'Streaming end');

        return new StopEvent();
    }
}
```

> Per fare streaming di eventi da un nodo devi aggiungere `\Generator` come tipo di ritorno aggiuntivo su `__invoke`.

**`yield` emette avanzamento. `return` emette l'evento di instradamento.** Due canali da un solo metodo — è tutto il progetto, e sono i generatori PHP usati esattamente come previsto.

Nota che `ProgressEvent` non implementa `Event`. Non instrada mai nulla; un nodo può fare yield di qualunque oggetto. Solo il valore restituito dev'essere un `Event`.

L'unione `\Generator|FirstEvent` è la forma documentata dal framework, e si guadagna il posto: PHP la accetta, ed `export()` legge la metà `FirstEvent` per disegnare l'arco. PHPStan non la accetta — una funzione che fa yield può dichiarare solo tipi generatore, quindi segnala `generator.returnType` su ogni `yield`. Se la tua base di codice usa PHPStan, dichiara solo `\Generator` e sposta l'instradamento nel docblock, `@return \Generator<int, ProgressEvent, mixed, FirstEvent>`. Il workflow gira in modo identico; il prezzo è che `export()` non vede più dove porta il nodo e mostra il nodo successivo come orfano.

Per ricevere lo stream, chiama `events()` invece di `run()`. Restituisce un generatore di tutto ciò di cui i nodi fanno yield, e lo stato finale è il valore di ritorno del generatore:

```php
$stream = Workflow::make()
    ->addNodes([
        new InitialNode(),
        new NodeOne(),
        new NodeTwo(),
    ])
    ->events();

foreach ($stream as $item) {
    if ($item instanceof ProgressEvent) {
        echo $item->message . "\n";
    }
}

$state = $stream->getReturn();
```

### L'avanzamento non è durevole

L'output emesso con yield è vivo ed effimero. Non viene scritto nello store, e quando una run recuperata riproduce gli step completati (Sezione 13.5), gli eventi di avanzamento di quegli step **non** vengono emessi di nuovo — solo l'evento restituito è durevole. Un client che si riconnette a metà strada ha perso ciò che ha perso.

Quindi non far mai dipendere la correttezza dall'arrivo di un evento di avanzamento. Tutto ciò che l'applicazione deve sapere va nello stato o nel risultato; l'avanzamento è per l'essere umano che guarda.

### Perché è una funzionalità genuinamente forte

Confronta le due esperienze utente per un workflow che impiega 45 secondi.

**Senza streaming:**

```
[spinner] ......................................... fatto
```

**Con streaming:**

```
Ricerca sull'argomento...
  Trovate 12 fonti
Redazione dell'articolo...
  Bozza completata: 1.240 parole
Revisione...
  Richiesta revisione: aggiungere una contro-argomentazione
Revisione in corso...
Fatto.
```

Il secondo non è uno spinner più carino. È un prodotto diverso. L'utente sa che il sistema sta lavorando sul problema giusto, capisce perché è lento e può abbandonare prima se è andato storto.

Per i sistemi multi-agente conta ancora di più, perché le esecuzioni sono più lunghe. La Sezione 1.4 diceva che la latenza si accumula; questo è il modo di renderla tollerabile.

### Indicazioni di progetto

**Dai nome agli eventi di avanzamento per l'utente, non per lo sviluppatore.** `"Searching the knowledge base"` batte `"RetrievalNode invoked"`. Stesso principio della lista di permessi delle etichette dei tool nella Sezione 7.4 — e stessa preoccupazione di sicurezza: non far trapelare dettagli interni.

**Non fare yield di ogni dettaglio.** Una riga di avanzamento per ogni documento recuperato è rumore. Una per fase significativa.

**Fai yield prima del lavoro lento, non dopo.** `yield new ProgressEvent("Researching...")` e poi fai la ricerca. Fare yield dopo dice all'utente che cosa è già finito, che è la metà sbagliata dell'informazione.

### Collegarsi al frontend

Gli stream adapter della Sezione 7.5 si applicano qui. `setStreamAdapter()` con `AGUIAdapter` o `VercelAIAdapter` trasforma l'output di un workflow in eventi di protocollo per un browser. Un adapter codifica solo ciò che capisce: fai yield direttamente degli eventi di stream portabili di NeuronAI (`StepStartedStreamEvent`, `ActivityStreamEvent` e compagnia, in `NeuronAI\Agent\Adapters\Events`), oppure tieni il tuo `ProgressEvent` e registra una traduzione con il `mapEvent()` dell'adapter. Aggiungi un canale con `setChannel()` — `PusherChannel`, `RedisChannel` — e un workflow **in coda** fa streaming verso un client con cui non ha alcuna connessione diretta.

È la combinazione che costruisce il Capitolo 21: workflow lungo su un worker, avanzamento dal vivo nel browser.

### Punti chiave

- Aggiungi `\Generator` al tipo di ritorno; `yield` per l'avanzamento, `return` per l'evento di instradamento.
- Due canali da un solo metodo; consumali con `events()` e `getReturn()`.
- L'avanzamento è effimero: mai salvato, mai riprodotto.
- Dai nomi agli eventi di avanzamento pensando agli utenti; uno per fase; fai yield prima del lavoro.
- Adapter e canali portano l'avanzamento del workflow al frontend, anche dai job in coda.
