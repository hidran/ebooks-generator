# Capitolo 15 — Human in the loop

## 15.1 L'interruzione: una funzionalità, non un fallimento

### Che cosa fa

Il pattern di interruzione di NeuronAI permette a un workflow di **fermare l'esecuzione e aspettare un input esterno prima di riprendere.**

Non "fermati e ricomincia". Fermati — a metà di un nodo — preservando tutto, e riprendi da quel punto esatto con la risposta dell'essere umano iniettata.

### Le quattro fasi

La documentazione descrive un pattern richiesta-risposta:

1. **Richiesta** — un nodo individua qualcosa che richiede input umano e crea un `InterruptRequest`.
2. **Pausa** — il workflow solleva un'eccezione `WorkflowInterrupt`, preservando l'intero contesto di esecuzione.
3. **Decisione** — la tua applicazione presenta la richiesta a un essere umano, che approva, rifiuta o modifica.
4. **Ripresa** — il workflow continua dallo stesso nodo, con la decisione disponibile.

> Questo progetto garantisce che un workflow possa fermarsi in sicurezza in qualunque punto, persistere il proprio stato e riprendere esattamente da dove si era fermato, **anche fra sessioni diverse.**

### Perché "anche fra sessioni diverse" è tutta la storia

Prendilo alla lettera. Il processo PHP termina. La richiesta web si conclude. Il server viene ridistribuito. Passano tre giorni.

Poi il manager clicca "approva" in un'email, e il workflow continua dal centro del nodo in cui si era fermato, con tutto il suo contesto intatto.

Per un pubblico PHP è davvero notevole, perché il modello di esecuzione di PHP è notoriamente legato alla richiesta. La risposta del framework è serializzazione più un layer di persistenza, e trasforma "l'AI fa tutto" in "l'AI fa il lavoro, un essere umano prende le decisioni" — che è l'unica forma che la maggior parte delle aziende metterà davvero in produzione per qualcosa di consequenziale.

### L'interruzione è un'eccezione, di proposito

`WorkflowInterrupt` viene sollevata, non restituita. All'inizio sembra strano e vale la pena spiegare il ragionamento.

Significa che l'interruzione srotola lo stack da dovunque avvenga — arbitrariamente in profondità dentro un nodo, dentro un helper, dentro un middleware — senza che ogni livello intermedio debba saperne o far passare indietro un valore di ritorno. Qualunque nodo o middleware può interrompere, da qualunque punto.

Il costo è che devi intercettarla. Una `WorkflowInterrupt` che sfugge al tuo error handler sembra un crash e verrà loggata come tale. La Sezione 15.4 tratta la gestione.

### Dove questo cambia ciò che puoi costruire

I quattro livelli di difesa della Sezione 5.10 includevano "offerto, filtrato a runtime". Questo è quel livello, e sblocca un'intera categoria di applicazioni:

- Rimborsi sopra una soglia
- Email inviate ai clienti a nome dell'azienda
- Qualunque cancellazione
- Pubblicazione di contenuti
- Qualunque cosa con un requisito di approvazione normativa

Senza interruzione, queste cose sono o completamente automatizzate (inaccettabile) o non automatizzate (nessun valore). Con l'interruzione, l'AI fa la preparazione e un essere umano decide — il che è sia sicuro sia utile.

### Punti chiave

- Fermati a metà nodo, preserva tutto, riprendi con l'input umano.
- Quattro fasi: richiesta, pausa, decisione, ripresa.
- Sopravvive alla morte del processo e a lunghe attese: è la funzionalità distintiva.
- Sollevata come eccezione perché qualunque profondità possa interrompere; devi intercettarla.

## 15.2 interrupt() e ApprovalRequest

### La richiesta integrata

```php
namespace App\Neuron;

use NeuronAI\Workflow\Events\Event;
use NeuronAI\Workflow\Interrupt\Action;
use NeuronAI\Workflow\Interrupt\ApprovalRequest;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;

class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): OutputEvent
    {
        // Interrupt the workflow and wait for the feedback.
        $humanResponse = $this->interrupt(
            new ApprovalRequest(
                message: 'Should I continue?',
                actions: [
                    new Action('delete_file', 'Delete File', 'Delete /var/log/old.txt'),
                ],
            )
        );

        $action = $humanResponse->getAction('delete_file');

        if ($action->isApproved()) {
            $state->set('is_sufficient', true);
            $state->set('user_feedback', $action->feedback);

            return new OutputEvent();
        }

        $state->set('is_sufficient', false);

        return new InputEvent();
    }
}
```

### Leggerlo

**`$this->interrupt($request)`** — la pausa. L'esecuzione si ferma qui al primo passaggio e riprende qui alla ripresa, con la risposta dell'essere umano come valore di ritorno.

**`ApprovalRequest`** — l'implementazione integrata, che copre il caso più comune: approvare azioni come le chiamate a tool.

**`Action`** — un singolo elemento su cui decidere: un identificativo, un'etichetta e una descrizione. Più azioni in una richiesta significa che l'essere umano decide più cose in un'unica interazione, che è la differenza fra una schermata di approvazione e cinque.

**`$humanResponse->getAction('delete_file')`** — recupera la decisione per identificativo.

**`isApproved()` e `->feedback`** — approvato o no, più il testo libero che l'essere umano ha aggiunto. Quel campo di feedback è più utile di quanto sembri: un rifiuto con una motivazione può entrare direttamente nella chiamata successiva all'agent come guida, trasformando un "no" in un "no, perché X" e permettendo al ciclo di migliorare davvero.

**Restituire `InputEvent` in caso di rifiuto** — questo nodo torna indietro nel ciclo. Il rifiuto non è un fallimento: è un'altra iterazione. Quella combinazione di interruzione più ciclo è il pattern di raffinamento human-in-the-loop, ed è ciò che costruisce il Laboratorio 10.

::: {.callout .callout-warning}
[Errori di sintassi negli esempi pubblicati]{.callout-title}

A diversi esempi di `ApprovalRequest` nella documentazione manca la virgola dopo `message:`, e all'esempio di `ContentReviewInterrupt` della Sezione 15.3 manca il punto e virgola dopo `parent::__construct($message)` e viene passato un argomento posizionale dopo uno nominato. Tutti e tre sono errori di copia-incolla, non differenze di API. Appendice A, punti da 34 a 36.
:::

### Indicazioni di progetto per le richieste di approvazione

**Scrivi il messaggio per chi decide, non per lo sviluppatore.** Lo vedranno in un'email o in una schermata di amministrazione, senza contesto. `'Should I continue?'` è un messaggio scarso. `'Approva un rimborso di 240 € per l'ordine #4471 — il cliente segnala che l'articolo è arrivato danneggiato'` permette di decidere senza aprire un altro sistema.

**Includi nella descrizione abbastanza da poter decidere.** Il terzo argomento di `Action` è dove va la sostanza.

**Raggruppa le decisioni correlate in una sola richiesta.** Cinque azioni in una richiesta battono cinque interruzioni sequenziali, ciascuna delle quali è una separata sveglia, notifica e attesa.

### Punti chiave

- `$this->interrupt($request)` mette in pausa e più tardi restituisce la risposta dell'essere umano.
- `ApprovalRequest` più `Action` copre approva/rifiuta con feedback.
- `isApproved()` e `->feedback`; il feedback può guidare l'iterazione successiva.
- Scrivi i messaggi per la persona che decide; raggruppa le decisioni correlate.

## 15.3 Richieste di interruzione personalizzate

### Perché approva/rifiuta non basta sempre

`ApprovalRequest` copre "devo compiere questa azione?". Non copre "ecco una bozza — modificala prima che la salvi", né "scegli una di queste tre opzioni", né "compila il campo mancante".

L'architettura è deliberatamente aperta: estendi l'astratta `InterruptRequest` per creare esperienze di interruzione personalizzate.

### L'implementazione

```php
class ContentReviewInterrupt extends InterruptRequest
{
    public function __construct(
        protected string $message,
        protected string $content
    ) {
        parent::__construct($message);
    }

    public function getContent(): string
    {
        return $this->content;
    }

    public function jsonSerialize(): array
    {
        return [
            'message' => $this->message,
            'content' => $this->content,
        ];
    }

    public static function fromArray(array $data)
    {
        return new static($data['message'], $data['content']);
    }
}
```

Tre responsabilità:

**Portare i dati** di cui l'essere umano ha bisogno per decidere, più qualunque cosa modificherà.

**`jsonSerialize()`** — così può essere conservata e mandata a un frontend. Nota l'implicazione: la tua interruzione attraversa un confine JSON. Tienila serializzabile e piatta.

**`fromArray()`** — ricostruirla dai dati modificati al ritorno.

Quel giro completo — oggetto PHP → JSON → interfaccia → JSON modificato → oggetto PHP — è tutto il ciclo di vita, e conoscerlo è sapere dove si inserisce il tuo frontend.

### Usarla

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): OutputEvent
    {
        // Generate an article
        $response = ContentCreatorAgent::make()
            ->chat(new UserMessage($event->prompt))
            ->getMessage();

        // Interrupt the workflow and wait for the feedback.
        $reviewRequest = $this->interrupt(
            new ContentReviewInterrupt(
                message: 'This is the new article. Review the content before saving it to the database.',
                content: $response->getContent()
            )
        );

        // Save the content of the updated interrupt request
        $state->set('content', $reviewRequest->getContent());

        return new InputEvent();
    }
}
```

### Il pattern che vale la pena nominare

L'agent ha generato il contenuto. L'essere umano l'ha **modificato**. Il workflow ha salvato la versione **modificata**.

Non è approvazione: è collaborazione. L'AI produce una bozza, l'essere umano la corregge, il sistema usa la versione corretta. Per la generazione di contenuti, la redazione di documenti, i suggerimenti di codice e l'estrazione di dati, è un prodotto migliore di approva/rifiuta, perché il caso comune è "quasi giusto" e non "sì o no".

Come principio di progetto: **quando la risposta umana probabile è "quasi, ma cambia questo", costruisci un'interruzione modificabile invece di un'approvazione.**

::: {.callout .callout-warning}
[Questo esempio genera contenuto prima di interrompere]{.callout-title}

Che è esattamente la situazione di cui parla la Sezione 15.5. Così com'è scritto, riprendere questo nodo riesegue `ContentCreatorAgent` e la modifica dell'essere umano viene applicata a una bozza *diversa*. Leggi la Sezione 15.5 prima di mettere in produzione qualcosa di questa forma.
:::

### Progettare una richiesta di interruzione

- Includi tutto il necessario per decidere. L'essere umano non deve dover aprire un altro sistema.
- Tienila piatta e serializzabile: diventa JSON.
- Includi un riferimento stabile a ciò su cui si decide (un ID), così una richiesta obsoleta può essere rilevata.
- Valuta una scadenza. Una richiesta di approvazione che riemerge tre settimane dopo può rispondere a una domanda che non vale più.

### Punti chiave

- Estendi `InterruptRequest` per qualunque cosa oltre approva/rifiuta.
- `jsonSerialize()` all'andata, `fromArray()` al ritorno: la richiesta attraversa un confine JSON.
- La richiesta modificata è ciò che il nodo riceve, il che abilita la collaborazione invece del semplice filtro.
- Quando la risposta è di solito "quasi", rendila modificabile.

## 15.4 Intercettare, persistere e riprendere

### La persistenza è obbligatoria

```php
$workflow = new WorkflowAgent(new FilePersistence(__DIR__));
```

> Per poter interrompere e riprendere un Workflow (e anche Agent e RAG) devi fornire il layer di persistenza quando crei l'istanza del Workflow.

Niente persistenza, niente ripresa. È la prima cosa da fare bene.

### Intercettare l'interruzione

```php
$workflow = new WorkflowAgent(
    new FilePersistence(__DIR__),
);

try {
    return $workflow->init()->run();
} catch (WorkflowInterrupt $interrupt) {
    $request    = $interrupt->getRequest();
    $workflowId = $interrupt->getWorkflowId();

    /*
    * You can store the request as a json object
    * along with the resume token, and ask the user for a feedback.
    */
    $pdo->prepare("INSERT INTO interruption_requests (resume_token, request) VALUES (?, ?)");
    $pdo->execute([
        $workflowId,
        json_encode($request),
    ]);
}
```

Dall'eccezione escono due cose:

- **`getRequest()`** — che cosa mostrare all'essere umano.
- **`getWorkflowId()`** — il token di ripresa. Senza, non puoi riprendere.

Il framework ha già persistito lo stato di esecuzione. Quello che conservi *tu* è la richiesta e il token, così che la tua applicazione possa trovare la decisione in sospeso, presentarla e ricollegare la risposta.

### Riprendere

```php
$workflow = new WorkflowAgent(
    new FilePersistence(__DIR__),
    $workflowId // <- Use the same ID you got during interruption
);

$request = ContentReviewInterrupt::fromArray($data);

// Resume the Workflow passing the processed request as the feedback
$result = $workflow->init($request)->run();

// Get the final answer
echo $result->get('content');
```

Tre requisiti:

1. **Lo stesso layer di persistenza.**
2. **Lo stesso ID di workflow.**
3. **La richiesta ricostruita**, che porta la decisione dell'essere umano, passata a `init()`.

### Persistenza su database

```php
use NeuronAI\Workflow\Persistence\DatabasePersistence;

$workflow = new WorkflowAgent(
    new DatabasePersistence(
        pdo: new \PDO(...),
        table: 'workflow_interrupts'
    ),
    'CUSTOM_ID'
);
```

**MySQL / MariaDB:**

```sql
CREATE TABLE IF NOT EXISTS workflow_interrupts (
    workflow_id VARCHAR(255) PRIMARY KEY,
    data LONGBLOB NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_workflow_id (workflow_id),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**PostgreSQL:**

```sql
CREATE TABLE workflow_interrupts (
    workflow_id VARCHAR(255) PRIMARY KEY,
    data BYTEA NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_workflow_id ON workflow_interrupts(workflow_id);
CREATE INDEX idx_updated_at ON workflow_interrupts(updated_at);
```

Leggi lo schema con attenzione, perché ti dice che cosa sta succedendo: `LONGBLOB` / `BYTEA` — l'intero stato di esecuzione serializzato, in binario. E `idx_updated_at` esiste perché tu possa trovare le interruzioni obsolete: è la tua storia di pulizia.

Usa `FilePersistence` per CLI e sviluppo. Usa `DatabasePersistence` per qualunque cosa multi-server o di produzione.

### Le quattro domande operative

Nessun tutorial le copre e ogni sistema di produzione ne ha bisogno.

**1. Chi viene notificato?** L'interruzione non manda email. Lo fa il tuo codice. Collega la notifica nel blocco catch.

**2. E se nessuno risponde?** Le interruzioni si accumulano. Ti serve una politica di timeout: escalation, scadenza o rifiuto automatico. `idx_updated_at` è lì per questa query.

**3. Come previeni una doppia ripresa?** Due manager aprono lo stesso link di approvazione ed entrambi cliccano. Marca la richiesta come risolta in modo atomico prima di riprendere.

**4. E un deploy nel frattempo?** Lo stato serializzato contiene le tue classi. Un deploy che rinomina una classe o cambia una proprietà romperà la deserializzazione delle interruzioni in volo. O svuota prima di distribuire, o versiona le tue richieste di interruzione.

Quest'ultima è lo spigolo tagliente, e vale la pena soffermarcisi. Gli oggetti PHP serializzati di lunga durata attraverso i deploy sono un problema difficile noto, e l'interruzione ti ci mette in pieno. La mitigazione — tieni le richieste di interruzione piccole, piatte e cambiale di rado — è una regola di progetto, non qualcosa da scoprire durante un incidente.

### Punti chiave

- La persistenza è obbligatoria per l'interruzione; `FilePersistence` per la CLI, `DatabasePersistence` per la produzione.
- Intercetta `WorkflowInterrupt`; conserva `getRequest()` e `getWorkflowId()`.
- Riprendi con la stessa persistenza, lo stesso ID e la richiesta ricostruita.
- Quattro domande operative: notifica, timeout, doppia ripresa, compatibilità con i deploy.

## 15.5 Checkpoint, interruzioni condizionali e middleware

### Il problema della riesecuzione

Questa sezione contiene l'avvertimento di correttezza più importante del libro.

> Quando il Workflow viene ripreso, riparte l'esecuzione **dal nodo in cui era stato interrotto. Il nodo verrà rieseguito interamente, incluso il codice precedente all'interruzione.**

Leggilo con attenzione, perché ha un costo reale. Se il tuo nodo chiama un LLM, poi interrompe, poi riprende — **la chiamata all'LLM viene rieseguita.** Paghi due volte, aspetti due volte, e per via della Sezione 1.5 la seconda volta potresti ottenere una *risposta diversa*.

Il che significa che l'essere umano ha approvato una cosa e il workflow procede con un'altra.

Non è spreco. È un bug di correttezza, e in un contesto regolamentato è un problema di audit. Ha una correzione di una riga.

### Checkpoint

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): OutputEvent
    {
        // The result of this code block is saved and returned when the workflow is resumed.
        $sentiment = $this->checkpoint('agent-1', function () {
            return MyAgent::make()->structured(
                new UserMessage(...),
                SentimentResult::class
            );
        });

        // Interrupt the workflow and wait for the feedback.
        if ($sentiment->isNegative()) {
            $feedback = $this->interrupt(
                new ApprovalRequest(
                    message: 'Should I continue?',
                    actions: [
                        new Action('review_id', 'Answer review', $sentiment->content),
                    ],
                )
            );

            if ($feedback->getAction('review_id')->isApproved()) {
                $state->set('is_sufficient', true);
                $state->set('user_feedback', $feedback->getAction('review_id')->feedback);

                return new OutputEvent();
            }
        }

        $state->set('is_sufficient', false);

        return new InputEvent();
    }
}
```

Due argomenti:

- Un **nome**, unico all'interno del nodo
- Una **closure** che avvolge il lavoro il cui risultato va salvato

Prima esecuzione: la closure viene eseguita e il suo risultato viene conservato. Dopo la ripresa: il risultato conservato viene restituito senza rieseguire.

La formulazione della documentazione è precisa: il nodo raggiunge il punto di interruzione *con esattamente lo stesso stato dell'esecuzione precedente*.

**La regola: qualunque chiamata a un LLM, qualunque chiamata a un'API a pagamento e qualunque cosa non deterministica che preceda un `interrupt()` nello stesso nodo va dentro un `checkpoint()`.** Non ci sono eccezioni che valga la pena imparare.

### consumeResumeRequest()

A volte vuoi ramificare in *cima* a un nodo in base al fatto che tu stia riprendendo:

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): OutputEvent
    {
        // Ask for the final resume request
        $feedback = $this->consumeResumeRequest();

        // If the request is not there yet, jump to the interruption
        if ($feedback !== null && $feedback->getAction('review_id')->isApproved()) {
            $state->set('is_sufficient', true);
            $state->set('user_feedback', $feedback->getAction('review_id')->feedback);

            return new OutputEvent();
        }

        $this->interrupt(
            new ApprovalRequest(
                message: 'Should I continue?',
                actions: [
                    new Action('review_id', 'Answer review', $state->get('review')),
                ],
            )
        );

        $state->set('is_sufficient', false);

        return new InputEvent();
    }
}
```

Restituisce il feedback, oppure `null` se il nodo sta girando normalmente invece di risvegliarsi. Ti permette di gestire il caso di ripresa esplicitamente in cima invece di ripercorrere tutto il corpo del nodo — una forma più pulita quando il nodo fa lavoro sostanziale prima dell'interruzione.

### interruptIf()

```php
// Conditional interruption
$this->interruptIf(
    $state->get('is_sufficient') == true,
    new ApprovalRequest(
        message: 'Should I continue?',
        actions: [
            new Action('review_id', 'Answer review', $state->get('review')),
        ],
    )
);

// Or use a callback to evaluate the condition
$this->interruptIf(
    fn() => $state->get('is_sufficient', false),
    new ApprovalRequest(
        message: 'Should I continue?',
        actions: [
            new Action('review_id', 'Answer review', $state->get('review')),
        ],
    )
);
```

La forma con callback conta: rimanda la valutazione ed evita di costruire la richiesta quando la condizione è falsa.

**L'argomento di prodotto a favore dell'interruzione condizionale:** se ogni azione richiede approvazione, gli esseri umani smettono di leggere e iniziano a cliccare. Interrompi solo sui casi che lo meritano — sopra una soglia, sotto un punteggio di confidenza, fuori dai parametri normali — e le approvazioni restano significative.

### Middleware ToolApproval

La stessa idea applicata alle chiamate a tool, senza scrivere un nodo:

```php
Neuron::middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Delete the oldest log file'));
```

Condizionale rispetto agli argomenti:

```php
new ToolApproval(
    tools: [
        BuyTicketTool::class => function (array $args): bool {
            return $args['amount'] > 100;
        }
    ]
)
```

Gli acquisti sotto i 100 € procedono; quelli più grandi aspettano un essere umano. È il quarto livello della Sezione 5.10, ora concreto — ed è un prodotto molto migliore sia di "consenti sempre" sia di "blocca sempre".

Nota la forma: `middleware(ToolNode::class, ...)`. La Sezione 2.3 diceva che i nomi dei nodi sono API pubblica. Ecco perché.

### ToolSearchMiddleware

```php
new ToolSearchMiddleware([...])
```

Per agent con cataloghi ampi di tool. Invece di mandare ogni schema a ogni richiesta — il costo che si accumula della Sezione 1.3 — seleziona dinamicamente i tool rilevanti.

È la risposta a "e se avessi 200 tool?", che è la domanda naturale dopo il Capitolo 5.

### Punti chiave

- **Un nodo ripreso si riesegue dall'inizio**, chiamate all'LLM incluse, con risultati potenzialmente diversi.
- `checkpoint('name', fn)` salva e ripropone; avvolgi tutto ciò che è costoso o non deterministico prima di un'interruzione.
- `consumeResumeRequest()` ramifica in base al fatto che tu ti stia risvegliando.
- `interruptIf()` mantiene significative le approvazioni; la forma con callback rimanda la valutazione.
- `ToolApproval` filtra le chiamate a tool in base agli argomenti; `ToolSearchMiddleware` gestisce i cataloghi ampi.
