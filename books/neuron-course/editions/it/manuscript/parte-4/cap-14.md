# Capitolo 14 — Cicli, diramazioni e stato

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

`FirstEvent|SecondEvent`. Se restituisci un tipo di evento che non è nella firma, il workflow non può risolvere il nodo successivo.

È il bug numero uno dei workflow. Fallisce a runtime con un messaggio confuso, e la causa è un tipo unione che qualcuno ha dimenticato di allargare dopo aver aggiunto una diramazione.

### Cicli verso qualunque punto

> Puoi creare un ciclo da qualunque nodo verso qualunque altro nodo definendo gli eventi di ingresso e di ritorno appropriati. Un nodo può perfino restituire uno `StartEvent` per saltare direttamente al primo nodo del workflow.

Restituire `StartEvent` riavvia l'intero flusso: un ritentativo completo dall'inizio.

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

        $verdict = ReviewerAgent::make()
            ->structured(new UserMessage($event->draft), Verdict::class);

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

Due cose che questo dimostra oltre al contatore:

**Ogni iterazione del ciclo costa chiamate all'LLM.** È di nuovo la Sezione 1.4. Un ciclo di revisione illimitato è una fattura illimitata.

**Abbi un piano per quando si raggiunge il limite.** Passare la palla a un essere umano batte il pubblicare in silenzio la terza bozza. È il ponte naturale verso il Capitolo 15.

### I cicli sono dove i sistemi agentici si guadagnano il posto

Un ciclo con dentro un LLM è *raffinamento iterativo*: redigi, critica, rivedi, ripeti finché non è abbastanza buono. Quel pattern — scrittore più critico — è una delle forme multi-agente di maggior valore, ed è un workflow a tre nodi con un solo tipo di ritorno unione.

### Punti chiave

- Un ciclo è un nodo che restituisce un evento che innesca di nuovo un nodo precedente.
- **Dichiara ogni possibile tipo di ritorno nell'unione**: il bug di workflow più comune.
- Restituire `StartEvent` riavvia l'intero workflow.
- Il framework non limita i cicli; conta nello stato e pianifica per il limite.

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

La diramazione sequenziale sceglie un percorso. Quella parallela ne esegue diversi **in concorrenza**.

```php
use NeuronAI\Workflow\Events\ParallelEvent;

class DocumentProcessing extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): ParallelEvent
    {
        return new ParallelEvent([
            'text'  => new TextProcessEvent(),
            'image' => new ImageProcessEvent(),
        ]);
    }
}
```

Ogni diramazione è una **chiave con nome** che mappa sul primo evento di quella diramazione. I nodi che gestiscono quegli eventi, e tutto ciò che sta a valle in ciascuna diramazione, si registrano normalmente nel workflow:

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

Una volta completate tutte le diramazioni, il `ParallelEvent` viene inoltrato al punto di fusione, che legge ciascun risultato per nome:

```php
class MergeNode extends Node
{
    public function __invoke(ParallelEvent $event, WorkflowState $state): StopEvent
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

::: {.callout .callout-tip}
[In pratica]{.callout-title}

Riproducilo deliberatamente una volta — imposta lo stato in una diramazione, leggilo nel nodo di fusione, guarda che non c'è — poi correggi con il risultato. Cinque minuti, e la regola si fissa in un modo che la lettura non ottiene.
:::

### Quando le diramazioni parallele si ripagano

Stessa forma della Sezione 5.13: **lavoro indipendente e legato all'I/O**. Tre agent che analizzano lo stesso documento da angolazioni diverse. Due chiamate API che non dipendono l'una dall'altra. Elaborazione di testo e immagine di un unico caricamento.

Non utili per: dipendenze sequenziali, o lavoro banalmente veloce dove il coordinamento costa più di quanto risparmi.

### Punti chiave

- La diramazione condizionale è un tipo di ritorno unione; converge restituendo un tipo di evento condiviso.
- `ParallelEvent(['name' => $event, ...])` esegue le diramazioni in concorrenza.
- Le diramazioni terminano con `StopEvent(result: ...)`; il nodo di fusione legge `getResult('name')`.
- **Lo stato di una diramazione è una copia isolata**: le mutazioni vengono scartate; restituisci i dati tramite il risultato.

## 14.3 Gestire lo stato

### Il default

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\StopEvent;
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

Un contenitore a chiavi stringa con `set()` e `get()`. Va bene per workflow piccoli e prototipi.

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

Poi iniettalo quando costruisci il workflow. Conferma la firma di iniezione nella tua versione: è uno dei punti in cui si vede la deriva del costruttore fra v2 e v3. Appendice A, punto 37.

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

Cruciale per il Capitolo 15, e vale la pena saperlo ora così non è una sorpresa:

**Lo stato viene serializzato quando un workflow viene interrotto.** Il che significa:

- **Le risorse non possono essere serializzate.** Connessioni al database, handle di file, socket aperti. Conserva un identificativo e ristabilisci la connessione quando il nodo riprende.
- Lo stesso vale per le closure e per qualunque cosa contenga indirettamente una risorsa.

Le indicazioni del framework sono esplicite su questo. Un `CustomState` che contiene un `PDO` fallirà al confine dell'interruzione — e fallirà lì, non dove l'hai scritto, il che lo rende un bug sgradevole da tracciare.

**Conserva ID, non oggetti con connessioni.** `protected int $userId` invece di un modello idratato che porta con sé una connessione viva.

### Punti chiave

- `WorkflowState` è un contenitore a chiavi stringa: bene in piccolo, debole su scala.
- `CustomState` dà accessori tipizzati, scopribilità e una casa per la logica derivata.
- **Lo stato viene serializzato all'interruzione**: niente risorse, niente connessioni, niente closure.
- Conserva gli ID e reidrata dentro il nodo.

## 14.4 Streaming di un workflow

### Una sola parola chiave

Aggiungi `\Generator` al tipo di ritorno e usa `yield`:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\StopEvent;

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

**Dai nome agli eventi di avanzamento per l'utente, non per lo sviluppatore.** `"Sto cercando nella base di conoscenza"` batte `"RetrieveDocumentsNode invocato"`. Stesso principio della lista di permessi delle etichette dei tool nella Sezione 7.4 — e stessa preoccupazione di sicurezza: non far trapelare dettagli interni.

**Non fare yield di ogni dettaglio.** Una riga di avanzamento per ogni documento recuperato è rumore. Una per fase significativa.

**Fai yield prima del lavoro lento, non dopo.** `yield new ProgressEvent("Ricerca in corso...")` e poi fai la ricerca. Fare yield dopo dice all'utente che cosa è già finito, che è la metà sbagliata dell'informazione.

### Collegarsi al frontend

Gli adapter dello stream della Sezione 7.5 si applicano qui. Gli eventi di avanzamento di un workflow passano attraverso `AGUIAdapter` o `VercelAIAdapter` fino a un browser e — come notato lì — un adapter che spinge verso un trasporto come Pusher permette a un workflow **in coda** di fare streaming verso un client con cui non ha alcuna connessione diretta.

È la combinazione che costruisce il Capitolo 21: workflow lungo su un worker, avanzamento dal vivo nel browser.

### Punti chiave

- Aggiungi `\Generator` al tipo di ritorno; `yield` per l'avanzamento, `return` per l'evento di instradamento.
- Due canali da un solo metodo.
- Dai nomi agli eventi di avanzamento pensando agli utenti; uno per fase; fai yield prima del lavoro.
- Gli adapter portano l'avanzamento del workflow al frontend, anche dai job in coda.
