# Capitolo 15 — Human in the loop

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

La versione eseguibile di ogni listato che segue si trova in [`chapters/Ch15`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch15), nel repository di accompagnamento. Clonalo, esegui `composer install` e gli esempi funzionano su un Ollama locale senza alcuna API key.
:::

## 15.1 L'interruzione: una funzionalità, non un fallimento

### Che cosa fa

Il pattern di interruzione di NeuronAI permette a un workflow di **fermare l'esecuzione e aspettare un input esterno prima di riprendere.**

Non "fermati e ricomincia". Fermati — a metà di un nodo — preservando tutto ciò che la run ha fatto fino a quel momento, e continua da quel nodo con la risposta dell'essere umano iniettata.

### Le quattro fasi

1. **Richiesta** — un nodo individua qualcosa che richiede input umano e chiama `$this->interrupt()` con un `InterruptRequest` che lo descrive.
2. **Pausa** — l'executor persiste la run e `run()` restituisce uno stato marcato come interrotto. Al tuo codice non viene sollevato nulla.
3. **Decisione** — la tua applicazione presenta la richiesta a un essere umano, che approva, rifiuta o modifica.
4. **Ripresa** — restituisci la decisione come semplice array con `resume($payload)->run()`. I nodi completati vengono riproposti dallo store, il nodo in pausa gira di nuovo, e questa volta `interrupt()` restituisce la decisione.

> Un workflow può fermarsi in sicurezza in qualunque punto, persistere il proprio stato e riprendere da dove si era fermato, **anche fra sessioni diverse.**

### Perché "anche fra sessioni diverse" è tutta la storia

Prendilo alla lettera. Il processo PHP termina. La richiesta web si conclude. Il server viene ridistribuito. Passano tre giorni.

Poi il manager clicca "approva" in un'email, e il workflow continua dal nodo in cui si era fermato, con tutto il suo contesto intatto.

Per un pubblico PHP è davvero notevole, perché il modello di esecuzione di PHP è notoriamente legato alla richiesta. La risposta del framework sono gli step durevoli della Sezione 13.5 più un layer di persistenza, e trasforma "l'AI fa tutto" in "l'AI fa il lavoro, un essere umano prende le decisioni" — che è l'unica forma che la maggior parte delle aziende metterà davvero in produzione per qualcosa di consequenziale.

### Una pausa è un risultato, non un'eccezione

Una run sospesa è un esito ordinario di `run()`. Lo verifichi sullo stato restituito:

```php
$state = $workflow->run();

if ($state->isInterrupted()) {
    $request = $state->getInterruptRequest();
    // show it to a human
}
```

Dentro il motore, `interrupt()` continua a srotolare il nodo: solleva un segnale interno che l'executor intercetta al confine dello step. Per questo qualunque codice in un nodo può interrompere, per quanto in profondità si trovi dentro un helper, senza che ogni livello intermedio debba far passare indietro un valore di ritorno. Ma il segnale non arriva mai fino a te. L'executor lo converte in una sospensione persistita e ritorna normalmente.

La conseguenza pratica: non c'è nulla da intercettare, e nulla che venga loggato per sbaglio come un crash. Quello che invece non devi dimenticare è *guardare*. Un chiamante che ignora `isInterrupted()` tratterà una run in pausa come una run conclusa e leggerà uno stato che non è ancora stato scritto. La Sezione 15.4 tratta la gestione.

### Dove questo cambia ciò che puoi costruire

I quattro livelli di difesa della Sezione 5.10 includevano "offerto, filtrato a runtime". Questo è quel livello, e sblocca un'intera categoria di applicazioni:

- Rimborsi sopra una soglia
- Email inviate ai clienti a nome dell'azienda
- Qualunque cancellazione
- Pubblicazione di contenuti
- Qualunque cosa con un requisito di approvazione normativa

Senza interruzione, queste cose sono o completamente automatizzate (inaccettabile) o non automatizzate (nessun valore). Con l'interruzione, l'AI fa la preparazione e un essere umano decide — il che è sia sicuro sia utile.

### Punti chiave

- Fermati a metà nodo, persisti la run, riprendi con l'input umano.
- Quattro fasi: richiesta, pausa, decisione, ripresa.
- Sopravvive alla morte del processo e a lunghe attese: è la funzionalità distintiva.
- Una pausa viene restituita, non sollevata: controlla `isInterrupted()` su ogni stato che ricevi.

## 15.2 interrupt() e ApprovalRequest

### La richiesta integrata

```php
namespace App\Neuron;

use NeuronAI\Agent\Interrupt\ApprovalRequest;
use NeuronAI\Workflow\Interrupt\Action;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;

class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): InputEvent|OutputEvent
    {
        // Interrupt the workflow and wait for the feedback.
        $payload = $this->interrupt(
            new ApprovalRequest(
                message: 'Should I continue?',
                actions: [
                    new Action('delete_file', 'Delete File', 'Delete /var/log/old.txt'),
                ],
            )
        );

        $decision = $payload['delete_file'] ?? 'reject';

        if ($decision === 'approve') {
            $state->set('is_sufficient', true);

            return new OutputEvent();
        }

        $state->set('is_sufficient', false);
        $state->set('user_feedback', \is_array($decision) ? $decision[1] : null);

        return new InputEvent();
    }
}
```

### Leggerlo

**`$this->interrupt($request)`** — la pausa. Al primo passaggio l'esecuzione si ferma qui. Alla ripresa il nodo gira di nuovo e `interrupt()` restituisce l'array che il chiamante ha passato a `resume()`.

**`ApprovalRequest`** — la richiesta integrata per il caso più comune: approvare azioni. Si trova in `NeuronAI\Agent\Interrupt`, perché l'approvazione dei tool dell'agent (Sezione 15.5) è costruita sopra di essa, mentre `Action` resta in `NeuronAI\Workflow\Interrupt`. Nulla impedisce a un nodo di un workflow qualunque di usarla.

**`Action`** — un singolo elemento su cui decidere: un identificativo, un'etichetta e una descrizione. Più azioni in una richiesta significa che l'essere umano decide più cose in un'unica interazione, che è la differenza fra una schermata di approvazione e cinque.

**Il payload** — un semplice array, con le chiavi che decidi tu. Questo libro usa la stessa convenzione dell'approvazione dei tool dell'agent, con chiave l'ID dell'azione: `'approve'`, `'reject'` oppure `['reject', 'reason']`. È un contratto fra il nodo e chi riprende la run, quindi scegli una forma e mantienila.

**La motivazione di un rifiuto** — più utile di quanto sembri. Un rifiuto con una motivazione può entrare direttamente nella chiamata successiva all'agent come guida, trasformando un "no" in un "no, perché X" e permettendo al ciclo di migliorare davvero.

**Restituire `InputEvent` in caso di rifiuto** — questo nodo torna indietro nel ciclo. Il rifiuto non è un fallimento: è un'altra iterazione. Quella combinazione di interruzione più ciclo è il pattern di raffinamento human-in-the-loop, ed è ciò che costruisce il Laboratorio 10.

`ApprovalRequest` e `Action` sono **solo in uscita**. `Action` è un value object di sola lettura: le sue proprietà sono `readonly` e non ha metodi `approve()`, `reject()` o `feedback()`. La richiesta descrive che cosa viene chiesto; la risposta torna indietro separatamente, come payload. Non modifichi mai la richiesta per registrare una decisione.

::: {.callout .callout-warning}
[Gli esempi della documentazione non corrispondono al codice]{.callout-title}

La documentazione importa `ApprovalRequest` da `NeuronAI\Workflow\Interrupt`, che non esiste; la classe è `NeuronAI\Agent\Interrupt\ApprovalRequest`. Il suo esempio di richiesta personalizzata sovrascrive `jsonSerialize()`, che su `InterruptRequest` è `final`, e il suo esempio di ripresa usa un argomento `runId:` nel costruttore che `Workflow` non ha. Tutti e tre falliscono alla prima esecuzione. Appendice A, punti da 34 a 36.
:::

### Indicazioni di progetto per le richieste di approvazione

**Scrivi il messaggio per chi decide, non per lo sviluppatore.** Lo vedranno in un'email o in una schermata di amministrazione, senza contesto. `'Should I continue?'` è un messaggio scarso. `'Approva un rimborso di 240 € per l'ordine #4471 — il cliente segnala che l'articolo è arrivato danneggiato'` permette di decidere senza aprire un altro sistema.

**Includi nella descrizione abbastanza da poter decidere.** Il terzo argomento di `Action` è dove va la sostanza.

**Raggruppa le decisioni correlate in una sola richiesta.** Cinque azioni in una richiesta battono cinque interruzioni sequenziali, ciascuna delle quali è una separata sveglia, notifica e attesa. Gli ID delle azioni devono essere unici all'interno di una richiesta; un duplicato viene rifiutato già alla costruzione della richiesta, perché la sua decisione non potrebbe mai essere consegnata.

### Punti chiave

- `$this->interrupt($request)` mette in pausa e, alla ripresa, restituisce l'array del payload.
- `ApprovalRequest` (in `NeuronAI\Agent\Interrupt`) più `Action` copre approva/rifiuta.
- La richiesta è solo in uscita; la decisione torna come semplice array la cui forma definisci tu.
- Scrivi i messaggi per la persona che decide; raggruppa le decisioni correlate.

## 15.3 Richieste di interruzione personalizzate

### Perché approva/rifiuta non basta sempre

`ApprovalRequest` copre "devo compiere questa azione?". Non copre "ecco una bozza — modificala prima che la salvi", né "scegli una di queste tre opzioni", né "compila il campo mancante".

L'architettura è deliberatamente aperta. Esistono due tipi di pausa — l'attesa di un evento e l'attesa di un orario — e `ApprovalRequest` è semplicemente una `WaitForEventRequest` in ascolto di un evento chiamato `approval`. Crei le tue estendendo `WaitForEventRequest` nello stesso modo.

### L'implementazione

```php
use NeuronAI\Workflow\Interrupt\WaitForEventRequest;

class ContentReviewInterrupt extends WaitForEventRequest
{
    public function __construct(
        protected string $message,
        protected string $content,
    ) {
        parent::__construct('content.reviewed');
    }

    public function getMessage(): string
    {
        return $this->message;
    }

    public function getContent(): string
    {
        return $this->content;
    }

    protected function metadata(): array
    {
        return [
            'message' => $this->message,
            'content' => $this->content,
        ];
    }
}
```

Tre responsabilità:

**Dare un nome all'evento** che attende — qui `content.reviewed`. È quel nome che `signal()` confronta alla ripresa (più sotto).

**Portare i dati** di cui l'essere umano ha bisogno per decidere, più qualunque cosa modificherà.

**`metadata()`** — i campi che servono al tuo frontend. `jsonSerialize()` è `final`: il framework emette sempre l'ID dell'interruzione, il tipo e il nome dell'evento, e ci aggiunge dopo i tuoi metadati. Nota l'implicazione: la tua interruzione attraversa un confine JSON. Tienila serializzabile e piatta.

Quello che torna indietro non è un oggetto richiesta ricostruito. Il motore persiste la richiesta stessa, quindi non c'è nessun `fromArray()` da scrivere. La risposta dell'essere umano arriva come array di payload, e il nodo ne legge ciò che gli serve.

Quel giro completo — oggetto PHP → JSON → interfaccia → campi modificati → array di payload — è tutto il ciclo di vita, e conoscerlo è sapere dove si inserisce il tuo frontend.

### Usarla

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): SaveEvent
    {
        // Generate an article, once. See Section 15.5 for why this is memoized.
        $draft = $this->memoize('draft', fn (): string => ContentCreatorAgent::make()
            ->chat(new UserMessage($event->prompt))
            ->getMessage()
            ?->getContent() ?? '');

        // Interrupt the workflow and wait for the edited version.
        $payload = $this->interrupt(
            new ContentReviewInterrupt(
                message: 'This is the new article. Review the content before saving it to the database.',
                content: $draft
            )
        );

        // Save the content the human sent back
        $state->set('content', $payload['content'] ?? $draft);

        return new SaveEvent();
    }
}
```

E la ripresa, da qualunque cosa riceva la modifica:

```php
$state = ArticleWorkflow::make(workflowId: $workflowId)
    ->setPersistence($persistence)
    ->signal('content.reviewed', ['content' => $editedText])
    ->run();
```

`signal()` è `resume()` con una protezione: consegna il payload solo se l'interruzione corrente sta aspettando quel nome di evento, e altrimenti solleva un'eccezione. Usalo quando il chiamante sa a che cosa sta rispondendo: un handler di webhook per `payment.received` non deve poter rispondere per sbaglio a un'approvazione.

### Il pattern che vale la pena nominare

L'agent ha generato il contenuto. L'essere umano l'ha **modificato**. Il workflow ha salvato la versione **modificata**.

Non è approvazione: è collaborazione. L'AI produce una bozza, l'essere umano la corregge, il sistema usa la versione corretta. Per la generazione di contenuti, la redazione di documenti, i suggerimenti di codice e l'estrazione di dati, è un prodotto migliore di approva/rifiuta, perché il caso comune è "quasi giusto" e non "sì o no".

Come principio di progetto: **quando la risposta umana probabile è "quasi, ma cambia questo", costruisci un'interruzione modificabile invece di un'approvazione.**

::: {.callout .callout-warning}
[Questo esempio genera contenuto prima di interrompere]{.callout-title}

Che è esattamente la situazione di cui parla la Sezione 15.5. Senza il `memoize()` attorno, riprendere questo nodo riesegue `ContentCreatorAgent` e la modifica dell'essere umano viene applicata a una bozza *diversa*. Leggi la Sezione 15.5 prima di mettere in produzione qualcosa di questa forma.
:::

### Attendere eventi e orari

Due helper coprono le pause che non sono affatto una decisione umana:

```php
// Suspend until an external event arrives, or the deadline passes.
$payment = $this->awaitEvent('payment.received', expiresAt: new \DateTimeImmutable('+2 days'));

if ($payment === null) {
    return new OrderExpired();       // the deadline passed, nothing arrived
}

// Suspend until a clock time.
$this->sleepUntil(new \DateTimeImmutable('tomorrow 09:00'));
```

`awaitEvent()` è `interrupt()` con una `WaitForEventRequest`; `sleepUntil()` è `interrupt()` con una `SleepUntilRequest`. Il motore registra la scadenza ma non fa girare alcun timer: nel core nulla si risveglia da solo. È il tuo scheduler (cron, un job in coda ritardato) a chiamare `resume()->run()` senza payload quando arriva il momento, e il workflow controlla l'orario da sé: prima della scadenza la run resta sospesa, dopo `awaitEvent()` restituisce `null` e `sleepUntil()` ritorna. Il nodo non confronta mai orari.

`ApprovalRequest` accetta la stessa scadenza opzionale come terzo argomento, `expiresAt:`.

### Progettare una richiesta di interruzione

- Includi tutto il necessario per decidere. L'essere umano non deve dover aprire un altro sistema.
- Tienila piatta e serializzabile: diventa JSON, e viene persistita con la run.
- Includi un riferimento stabile a ciò su cui si decide (un ID), così una richiesta obsoleta può essere rilevata.
- Imposta una scadenza. Una richiesta di approvazione che riemerge tre settimane dopo può rispondere a una domanda che non vale più, e `expiresAt` trasforma il timeout in un ramo del tuo nodo invece che in un job di pulizia.

### Punti chiave

- Estendi `WaitForEventRequest` per qualunque cosa oltre approva/rifiuta; dai un nome all'evento che attende.
- Sovrascrivi `metadata()`, non `jsonSerialize()`; non c'è nessun `fromArray()`: la risposta torna come array di payload.
- `signal($name, $payload)` riprende solo se la richiesta corrente attende quell'evento.
- `awaitEvent()` e `sleepUntil()` mettono in pausa su eventi e orari; il tuo scheduler chiama `resume()->run()`.
- Quando la risposta è di solito "quasi", rendila modificabile.

## 15.4 Persistere, rilevare e riprendere

### La persistenza è obbligatoria

```php
$workflow = PublishWorkflow::make()
    ->setPersistence(new FilePersistence($storage));
```

Per impostazione predefinita un workflow usa `InMemoryPersistence`, che vive e muore con il processo PHP. Con essa una run può fermarsi e continuare all'interno di un unico script, ma nel momento in cui il processo termina la run in pausa è perduta.

Niente persistenza durevole, niente ripresa fra processi. È la prima cosa da fare bene. Puoi impostarla nel punto di chiamata come sopra, oppure restituirla dall'hook `persistence()` del workflow, così che ogni istanza della classe la riceva.

### Rilevare la pausa

```php
$state = $workflow->run();

if (!$state->isInterrupted()) {
    echo 'Completed without interruption: ' . \var_export($state->get('outcome'), true) . "\n";
    exit(0);
}

$request = $state->getInterruptRequest();
$workflowId = $state->getWorkflowId();

\file_put_contents(
    $storage . "/pending-{$workflowId}.json",
    \json_encode($request, \JSON_PRETTY_PRINT | \JSON_THROW_ON_ERROR),
);
```

Dallo stato escono due cose:

- **`getInterruptRequest()`** — che cosa mostrare all'essere umano. È `JsonSerializable`.
- **`getWorkflowId()`** — l'handle di continuazione. Senza, non puoi riprendere.

Il framework ha già persistito la run: i suoi step completati, il suo stato e la richiesta stessa. Quello che conservi *tu* è il workflow ID e ciò che serve alla tua interfaccia, così che la tua applicazione possa trovare la decisione in sospeso, presentarla e ricollegare la risposta. Lo `start.php` del repository di accompagnamento scrive la richiesta in un file JSON, che per una CLI è esattamente sufficiente:

```
Suspended, awaiting a human decision.
  Workflow ID : workflow_7509539539310313472
  Request     : {"interruptId":1,"type":"wait_for_event","eventName":"approval",...}
```

### Riprendere

```php
$payload = [
    'delete_file' => $decision === 'approve'
        ? 'approve'
        : ['reject', 'Keep it until the audit closes.'],
];

$state = PublishWorkflow::make(workflowId: $workflowId)
    ->setPersistence(new FilePersistence($storage))
    ->resume($payload)
    ->run();
```

Tre requisiti:

1. **La stessa classe di workflow** — il processo che riprende deve ricostruire un grafo identico, e una classe è il modo per garantirlo.
2. **Lo stesso layer di persistenza** e **lo stesso workflow ID.**
3. **Il payload**, che porta la decisione dell'essere umano, passato a `resume()`.

`resume()` si limita a predisporre la risposta; è `run()` a eseguirla. I due vanno sempre in coppia. Sostituisci `run()` con `events()` e la continuazione va in streaming, esattamente come una run nuova (Sezione 14.4).

Esegui `start.php` e `resume.php` del repository di accompagnamento come due comandi separati. La proposta generata prima dell'interruzione viene stampata una volta, nel primo processo, e mai nel secondo. Esegui `resume.php` una seconda volta con lo stesso ID e fallisce con "No run in flight": una run completata fa pulizia dietro di sé.

### Workflow ID e run ID

Una run porta due identificativi, e solo uno dei due è l'handle.

**Il workflow ID** dà il nome alla partizione dello store in cui vivono i record della run. È l'handle di continuazione: ciò che salvi, e ciò che passi a `make(workflowId: ...)`. Un workflow semplice ne riceve uno generato (`workflow_…`) alla sua prima `run()`; prima di allora, `getWorkflowId()` è `null`.

**Il run ID** (`getRunId()`) è un contrassegno di generazione all'interno di quella partizione. Cambia ogni volta che una run nuova parte con lo stesso workflow ID, e serve per il fencing e l'osservabilità: mai per continuare.

Un workflow può anche dichiarare il proprio workflow ID come chiave di business sovrascrivendo `workflowId()`:

```php
class RefundWorkflow extends Workflow
{
    public function __construct(protected string $orderId)
    {
        parent::__construct();
    }

    public function workflowId(): ?string
    {
        return 'refund:' . $this->orderId;
    }
}

// Later, in a process that knows only the order:
RefundWorkflow::make(orderId: $orderId)
    ->setPersistence($persistence)
    ->resume(['refund' => 'approve'])
    ->run();
```

Ora non c'è nulla da conservare a parte: l'ID dell'ordine *è* la strada per tornare alla run. Impone anche una regola che altrimenti dovresti costruire tu: **una sola run attiva per workflow ID**. Chiamare `run()` mentre una run per quella chiave è sospesa solleva `RunInFlightException`, il cui messaggio indica che cosa la risolve e la cui proprietà `interrupt` contiene la richiesta in sospeso. L'Agent usa esattamente questo meccanismo, con il suo thread ID come workflow ID (Sezione 15.5).

### Backend di persistenza

```php
use NeuronAI\Workflow\Persistence\DatabasePersistence;

$persistence = new DatabasePersistence(new \PDO($dsn, $user, $password));   // table: workflow_store
```

**MySQL / MariaDB:**

```sql
CREATE TABLE workflow_store (
    `partition` VARCHAR(255) NOT NULL,
    `key`       VARCHAR(255) NOT NULL,
    `value`     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`partition`, `key`)
);
```

**PostgreSQL:**

```sql
CREATE TABLE workflow_store (
    "partition" VARCHAR(255) NOT NULL,
    "key"       VARCHAR(255) NOT NULL,
    "value"     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("partition", "key")
);
```

Leggi lo schema con attenzione, perché ti dice che cosa sta succedendo. Una sola tabella, con chiave partizione e chiave: ogni record di una run — il suo evento di avvio, il suo record di controllo, ogni step completato, ogni valore memoizzato, lo stato sospeso — è una riga nella partizione che porta il nome del suo workflow ID. I valori sono stringhe serializzate opache; la tabella non sa nulla dei workflow. `partition` e `key` sono parole riservate in MySQL, da qui i backtick. E `updated_at` esiste perché tu possa trovare le run obsolete; aggiungi un indice se intendi interrogarlo.

Gli altri backend conservano gli stessi record:

- **`EloquentPersistence(WorkflowStore::class)`** — un model Laravel con colonne `partition`, `key` e `value` (Capitolo 18).
- **`RedisPersistence($redis, prefix: 'neuron:workflow:')`** — un hash per run, richiede `ext-redis`. Non imposta alcun TTL: la pulizia è compito del workflow, quindi configura l'eviction in modo che non scarti le run attive.

Usa `FilePersistence` per CLI e sviluppo: sopravvive ai riavvii ma è pensata per un singolo processo. Usa i backend database, Eloquent o Redis per qualunque cosa multi-worker o di produzione; ciascuna delle loro scritture è un'operazione condizionale e atomica, ed è su questo che si basa la sezione successiva.

### Le quattro domande operative

Nessun tutorial le copre e ogni sistema di produzione ne ha bisogno.

**1. Chi viene notificato?** L'interruzione non manda email. Lo fa il tuo codice. Collega la notifica nel punto in cui rilevi `isInterrupted()`.

**2. E se nessuno risponde?** Dai alla richiesta un `expiresAt` e pianifica per quell'orario un job che chiami `resume()->run()` senza payload. Il workflow controlla da sé la scadenza e il nodo prende il suo ramo di timeout: escalation, scadenza o rifiuto automatico sono una decisione nel tuo nodo, non uno script di pulizia. Per le run che vuoi semplicemente eliminare, `abandonRun()` scarta una run in pausa e libera il suo workflow ID.

**3. Come previeni una doppia ripresa?** Due manager aprono lo stesso link di approvazione ed entrambi cliccano. La corsa la gestisce il motore: ogni modifica è una scrittura condizionale sul record di controllo della run, quindi vince una sola continuazione, una risposta accettata non può essere sostituita da una in conflitto, e la ripresa di una run completata fallisce con "No run in flight". Quello che il motore non può sapere è a *quale* richiesta fosse destinata una consegna in ritardo. Un job in coda che può essere ritentato deve portare con sé il run ID e il tentativo di esecuzione che ha osservato, e passarli come fence:

```php
$state = $workflow->resume(
    $payload,
    expectedRunId: $runId,
    expectedExecutionAttempt: $attempt,
)->run();
```

Se la run è andata avanti — una nuova generazione, oppure un altro worker l'ha già continuata — la chiamata solleva `StaleWorkflowRunException` prima di toccare qualunque cosa. La tua interfaccia dovrebbe comunque marcare la richiesta come risolta, così che il secondo manager veda "già deciso" invece di un errore.

**4. E un deploy nel frattempo?** Lo stato persistito è PHP serializzato, e contiene le tue classi: l'oggetto di stato, gli eventi, la richiesta di interruzione. Un deploy che rinomina una classe o cambia una proprietà romperà la deserializzazione delle run in volo. O svuota prima di distribuire, o versiona le tue richieste di interruzione. Lo stesso vale per l'aggiornamento di NeuronAI stesso: le run sospese con una versione precedente del formato dello store non possono essere riprese da una più recente.

Quest'ultima è lo spigolo tagliente, e vale la pena soffermarcisi. Gli oggetti PHP serializzati di lunga durata attraverso i deploy sono un problema difficile noto, e l'interruzione ti ci mette in pieno. La mitigazione — tieni le richieste di interruzione e lo stato piccoli, piatti e cambiali di rado — è una regola di progetto, non qualcosa da scoprire durante un incidente.

### Punti chiave

- La persistenza durevole è obbligatoria per la ripresa fra processi; `FilePersistence` per la CLI, un backend database, Eloquent o Redis per la produzione.
- `run()` ritorna; controlla `isInterrupted()`, conserva `getWorkflowId()` e mostra `getInterruptRequest()`.
- Riprendi con la stessa classe, la stessa persistenza e lo stesso workflow ID: `resume($payload)->run()`.
- Il workflow ID è l'handle; il run ID è un contrassegno di generazione. Dichiara `workflowId()` per riprendere tramite una chiave di business.
- Quattro domande operative: notifica, timeout (`expiresAt`), doppia ripresa (scritture condizionali e fence), compatibilità con i deploy.

## 15.5 Memoizzazione, interruzioni condizionali e middleware

### Il problema della riesecuzione

Questa sezione contiene l'avvertimento di correttezza più importante del libro.

Quando un workflow riprende, i nodi completati non vengono rieseguiti: i loro risultati vengono riproposti dallo store. Ma **il nodo che era stato interrotto viene rieseguito dall'inizio, incluso il codice precedente all'interruzione.** È così che `interrupt()` riesce a restituire il payload: l'esecuzione deve raggiungerlo di nuovo.

Leggilo con attenzione, perché ha un costo reale. Se il tuo nodo chiama un LLM, poi interrompe, poi riprende — **la chiamata all'LLM viene rieseguita.** Paghi due volte, aspetti due volte, e per via della Sezione 1.5 la seconda volta potresti ottenere una *risposta diversa*.

Il che significa che l'essere umano ha approvato una cosa e il workflow procede con un'altra.

Non è spreco. È un bug di correttezza, e in un contesto regolamentato è un problema di audit. Ha una correzione di una riga.

### memoize()

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): InputEvent|OutputEvent
    {
        // The result of this closure is persisted and returned when the node re-runs.
        $sentiment = $this->memoize('agent-1', fn (): SentimentResult => MyAgent::make()->structured(
            new UserMessage($event->review),
            SentimentResult::class
        ));

        if ($sentiment->isNegative()) {
            // Interrupt the workflow and wait for the feedback.
            $payload = $this->interrupt(
                new ApprovalRequest(
                    message: 'Negative review detected. Should I answer it?',
                    actions: [
                        new Action('review_id', 'Answer review', $sentiment->content),
                    ],
                )
            );

            if (($payload['review_id'] ?? null) === 'approve') {
                $state->set('is_sufficient', true);

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

Prima esecuzione: la closure viene eseguita e il suo risultato viene scritto nello store come parte dello step corrente. Alla riesecuzione — dopo un'interruzione o dopo un crash — il risultato conservato viene restituito senza rieseguire la closure. Il nodo raggiunge il punto di interruzione con gli stessi valori dell'esecuzione precedente.

L'`ApprovalNode` del repository di accompagnamento lo rende visibile: la sua closure memoizzata stampa una riga, e fra `start.php` e `resume.php` quella riga compare esattamente una volta.

**La regola: qualunque chiamata a un LLM, qualunque chiamata a un'API a pagamento e qualunque cosa non deterministica che preceda un `interrupt()` nello stesso nodo va dentro un `memoize()`.** Non ci sono eccezioni che valga la pena imparare. La closure stessa deve essere una funzione pura dell'evento e dello stato del nodo: `time()`, la casualità e l'I/O vanno *dentro* di essa, mai attorno.

Un limite da tenere a mente. `memoize()` salva un risultato una volta che la closure è ritornata. Se il processo muore dopo un effetto collaterale esterno ma prima che il risultato sia salvato — l'email è partita, la memo non ha fatto commit — la closure viene eseguita di nuovo. Dove conta, passa una chiave di idempotenza al sistema esterno.

Nel materiale meno recente troverai `checkpoint()`. Esiste ancora, deprecato, e si limita a chiamare `memoize()`.

### isResuming() e getResumePayload()

A volte vuoi ramificare in *cima* a un nodo in base al fatto che tu stia riprendendo:

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): InputEvent|OutputEvent
    {
        if ($this->isResuming()) {
            $payload = $this->getResumePayload();

            if (($payload['review_id'] ?? null) === 'approve') {
                $state->set('is_sufficient', true);

                return new OutputEvent();
            }
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

`isResuming()` è vero quando il nodo si sta risvegliando con una risposta; `getResumePayload()` restituisce quella risposta. In caso di rifiuto il codice prosegue fino a `interrupt()`, che — essendo ancora in ripresa — restituisce il payload invece di mettere di nuovo in pausa, e il nodo torna indietro nel ciclo. Ti permette di gestire il caso di ripresa esplicitamente in cima invece di ripercorrere tutto il corpo del nodo — una forma più pulita quando il nodo fa lavoro sostanziale prima dell'interruzione.

### interruptIf()

```php
// Conditional interruption
$payload = $this->interruptIf(
    $state->get('is_sufficient') == true,
    new ApprovalRequest(
        message: 'Should I continue?',
        actions: [
            new Action('review_id', 'Answer review', $state->get('review')),
        ],
    )
);

// Or use a callback to evaluate the condition
$payload = $this->interruptIf(
    fn (): bool => $state->get('is_sufficient', false),
    new ApprovalRequest(
        message: 'Should I continue?',
        actions: [
            new Action('review_id', 'Answer review', $state->get('review')),
        ],
    )
);
```

Quando la condizione è falsa, `interruptIf()` restituisce `null` e l'esecuzione prosegue dritta; `null` significa "non è stato chiesto a nessun essere umano". La forma con callback rimanda la valutazione al momento del controllo. Alla ripresa la condizione non viene proprio rivalutata: il nodo si era già fermato lì, quindi viene restituito il payload.

**L'argomento di prodotto a favore dell'interruzione condizionale:** se ogni azione richiede approvazione, gli esseri umani smettono di leggere e iniziano a cliccare. Interrompi solo sui casi che lo meritano — sopra una soglia, sotto un punteggio di confidenza, fuori dai parametri normali — e le approvazioni restano significative.

### Approvazione dei tool negli agent

La stessa idea applicata alle chiamate a tool, senza scrivere un nodo. Un agent è un workflow, e il suo `ToolNode` controlla ogni tool prima di eseguirlo: se il tool richiede approvazione, il nodo si interrompe con un `ApprovalRequest` che porta una `Action` per ogni chiamata soggetta ad approvazione.

Se un tool richieda approvazione si dichiara sul tool: il Capitolo 5 tratta l'API di dichiarazione. Un tool può dichiarare la propria policy, condizionata ai suoi argomenti; restituire una stringa vale come "sì" ed è la motivazione mostrata a chi approva:

```php
class BuyTicketTool extends Tool
{
    // ...

    protected function approvalPolicy(): bool|string
    {
        return ($this->inputs['amount'] ?? 0) > 100
            ? 'Purchases above €100 need a human sign-off'
            : false;
    }
}
```

Oppure l'agent la sovrascrive nel punto in cui collega il tool: `->requireApproval()`, `->suppressApproval()` o `->withApprovalPolicy(fn (ToolInterface $tool) => ...)`.

Gli acquisti sotto i 100 € procedono; quelli più grandi aspettano un essere umano. È il quarto livello della Sezione 5.10, ora concreto — ed è un prodotto molto migliore sia di "consenti sempre" sia di "blocca sempre".

Il giro completo, su due richieste:

```php
// Request 1: the model asks to buy a €240 ticket.
$agent = TicketAgent::make(threadId: $threadId)
    ->setChatHistory(new SQLChatHistory($pdo))
    ->setPersistence(new DatabasePersistence($pdo));

$state = $agent->chat(new UserMessage('Buy the concert ticket'));

if ($state->isInterrupted()) {
    $pending = $agent->pendingApprovals();   // Action[]: id is the tool call ID
}

// Request 2: the human approved $callId. Same thread, same persistence.
$state = TicketAgent::make(threadId: $threadId)
    ->setChatHistory(new SQLChatHistory($pdo))
    ->setPersistence(new DatabasePersistence($pdo))
    ->submitApprovalDecisions([$callId => 'approve'])
    ->run();
```

Il **thread ID è il workflow ID dell'agent**, quindi all'endpoint di approvazione non serve altro che il thread per trovare la run in pausa. Le decisioni hanno come chiave l'ID della chiamata a tool e assumono le stesse tre forme di prima: `'approve'`, `'reject'`, `['reject', 'reason']`. Un tool viene eseguito solo se approvato esplicitamente; un insieme parziale di decisioni sospende di nuovo la run finché non arrivano le altre. Una nuova `chat()` sul thread mentre una decisione è in sospeso viene rifiutata con `RunInFlightException`: blocca l'input nella tua interfaccia finché le decisioni non sono arrivate. Qui una cronologia della conversazione durevole conta quanto una persistenza durevole: la chiamata a tool in sospeso vive nel thread.

Il Capitolo 22 lo trasforma in una vera schermata di approvazione Laravel.

### ToolSearchMiddleware

```php
$agent->addMiddleware(InferenceNode::class, new ToolSearchMiddleware($toolPool));
```

Per agent con cataloghi ampi di tool. Invece di mandare ogni schema a ogni richiesta — il costo che si accumula della Sezione 1.3 — dà al modello un tool `tool_search` e carica su richiesta i tool corrispondenti dal pool, al massimo cinque per impostazione predefinita.

È la risposta a "e se avessi 200 tool?", che è la domanda naturale dopo il Capitolo 5.

Nota la forma: `addMiddleware(InferenceNode::class, ...)`. La Sezione 2.3 diceva che i nomi dei nodi sono API pubblica. Ecco perché. `InferenceNode` è la base sia del nodo di chat sia di quello di structured output, quindi una sola registrazione copre tutte le modalità.

### Punti chiave

- **Un nodo ripreso si riesegue dall'inizio**, chiamate all'LLM incluse, con risultati potenzialmente diversi.
- `memoize('name', fn)` persiste e ripropone; avvolgi tutto ciò che è costoso o non deterministico prima di un'interruzione.
- `isResuming()` e `getResumePayload()` ramificano in base al fatto che tu ti stia risvegliando.
- `interruptIf()` mantiene significative le approvazioni e restituisce `null` quando non è stato chiesto a nessuno.
- L'approvazione dei tool negli agent si dichiara sul tool e si risponde con `submitApprovalDecisions()->run()`; il thread è l'handle. `ToolSearchMiddleware` gestisce i cataloghi ampi.
