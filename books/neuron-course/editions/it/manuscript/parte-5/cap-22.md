# Capitolo 22 — Workflow e approvazione umana in produzione

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

I listati Laravel qui sotto vivono dentro un'applicazione, ma il workflow che guidano è eseguibile da solo in [`chapters/Ch22`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch22) nel repository di accompagnamento. `refund.php` percorre l'intero ciclo di vita — il rimborso approvato automaticamente, la pausa, la ripresa protetta dal fence, la riconsegna rifiutata, la scadenza superata e il completamento trattenuto — senza modello e senza Laravel. `agent-approval.php` riproduce allo stesso modo il giro completo di approvazione di un agent della Sezione 22.5, con un agent nuovo per ogni richiesta, ricostruito a partire dal solo thread ID.
:::

## 22.1 Il ciclo di vita di un'approvazione

### L'intuizione della Sezione 18.4, ampliata

Poiché una run sospesa vive nel tuo database, "l'AI sta aspettando un essere umano" è un fatto che la tua applicazione può tenere come record. Il che significa che riceve tutto ciò che i record di un database ricevono: uno stato, un proprietario, una scadenza, una pagina indice, una policy, una traccia di audit.

**L'human-in-the-loop smette di essere una funzionalità AI e diventa una funzionalità di workflow della tua applicazione.** Quel cambio di inquadramento è il punto di questo capitolo.

### La tabella di supporto

La tabella `workflow_store` del framework contiene la run stessa: il suo record di controllo, i suoi step completati, il suo stato sospeso, la richiesta pendente. Tu vuoi una tabella compagna che contenga la vista *di business*:

```php
Schema::create('pending_approvals', function (Blueprint $table) {
    $table->id();
    $table->string('workflow_id');          // the continuation handle, e.g. refund:1042
    $table->string('run_id');               // the generation that asked
    $table->unsignedInteger('interrupt_id');        // which of that run's pauses
    $table->unsignedInteger('execution_attempt');   // the attempt that paused
    $table->foreignId('tenant_id')->constrained();
    $table->foreignId('requested_by')->nullable()->constrained('users');
    $table->foreignId('resolved_by')->nullable()->constrained('users');

    $table->string('type');                 // refund, publish, escalation
    $table->string('subject_type')->nullable();
    $table->unsignedBigInteger('subject_id')->nullable();

    $table->json('request');                // the InterruptRequest, as JSON, for rendering
    $table->json('response')->nullable();   // what the human decided

    $table->string('status')->default('pending');   // pending|approved|rejected|expired|failed
    $table->timestamp('expires_at')->nullable();
    $table->timestamp('resolved_at')->nullable();

    $table->timestamps();

    $table->unique(['workflow_id', 'run_id', 'interrupt_id']);
    $table->index(['tenant_id', 'status']);
    $table->index('expires_at');
});
```

**Perché due tabelle.** La tabella del framework è un insieme di record serializzati opachi indicizzati per partizione — non puoi interrogarla, filtrarla né autorizzare su di essa, e non dovresti provarci: le sue righe cambiano sotto scritture condizionali che non controlli. La tua è un normale record che puoi indicizzare, delimitare e renderizzare. Separarle significa che il framework possiede le sue viscere e tu possiedi il tuo prodotto.

**Ciò che copi è una proiezione, non la richiesta.** La persistenza del workflow resta la fonte autorevole per la richiesta pendente. La tua tabella conserva ciò che le serve per instradare la risposta — il workflow ID, il run ID, l'interrupt ID e il tentativo di esecuzione che ha osservato — più una resa JSON della richiesta per la schermata. Run ID e tentativo sono i fence di consegna della Sezione 22.3; senza di essi una risposta tardiva o duplicata non si distingue da una attuale. L'interrupt ID c'è perché una stessa run può andare in pausa più di una volta — un rifiuto che rimanda indietro, un nodo che attende due volte — e ogni pausa ha una riga tutta sua; una chiave unica senza di esso rifiuterebbe la seconda.

Vale la pena notare anche: `subject_type` / `subject_id` è una relazione polimorfica, quindi un'approvazione si collega all'ordine, all'articolo o alla fattura che riguarda. Senza, la tua schermata di approvazione mostra un payload JSON opaco e chi approva deve andarsi a cercare il record da solo.

### Gli stati

```
pending ──approva──→ approved ──→ (workflow ripreso) ──→ completed
   │
   ├────respingi───→ rejected ──→ (workflow ripreso con il rifiuto)
   │
   └────scadenza───→ expired ──→ (workflow ripreso senza risposta; il nodo prende il ramo di timeout)
```

**Ogni percorso riprende il workflow.** L'approvazione lo fa proseguire, il rifiuto è un'altra iterazione (il ritorno indietro della Sezione 15.2), e una scadenza è il workflow che si accorge della propria scadenza. Nessuno di essi è un vicolo cieco che si lascia dietro una run sospesa.

### Le quattro domande, con risposta

La Sezione 15.4 le poneva. Ecco le risposte Laravel, che il resto di questo capitolo costruisce:

| Domanda | Risposta |
|---|---|
| Chi viene notificato? | Una `Notification` inviata quando la run ritorna interrotta (22.2) |
| E se nessuno risponde? | `expiresAt` sulla richiesta, più una ripresa senza input schedulata (22.4) |
| Come prevenire la doppia ripresa? | Le scritture condizionali e i fence di consegna del motore, più `lockForUpdate()` sul tuo record (22.3) |
| E i deploy? | Richieste di interruzione piccole, piatte, cambiate di rado e con proprietà dotate di default (22.4) |

### Punti chiave

- Una run sospesa è un fatto del database, quindi le approvazioni sono ordinario stato applicativo.
- Due tabelle: lo store opaco del framework e il tuo record di business interrogabile.
- Copia una proiezione — workflow ID, run ID, interrupt ID, tentativo — e non trattare mai la tua copia come fonte di verità.
- Relazione polimorfica verso il soggetto, così chi approva vede su che cosa sta decidendo.
- Ogni esito, scadenza compresa, riprende il workflow.

## 22.2 Rilevare la pausa e notificare

### Il job che avvia la run

```php
public function handle(PersistenceInterface $runs): void
{
    try {
        $state = RefundWorkflow::make(orderId: $this->orderId, requestedAmount: $this->amount)
            ->setPersistence($runs)
            ->setLeaseTimeout(600)
            // Minted with the request: every delivery of this job names the same run.
            ->run(ExecutionRequest::start(runId: $this->runId, recoverFailed: true));
    } catch (RunInFlightException $e) {
        if ($e->reservedRunId !== $e->runId) {
            // One live run per workflow ID: another request's refund holds this order.
            $this->recordDuplicateRequest($e->status);
        } elseif ($e->status === WorkflowStatus::Suspended) {
            // An earlier delivery paused this run and died before it recorded the pause.
            $this->recordPause($e->workflowId, $e->runId, $e->executionAttempt, $e->interrupt);
        } else {
            // A killed delivery still holds the lease: come back when it has expired.
            $this->release(\max(1, $e->leaseExpiresAt - \time()));
        }

        return;
    }

    if (! $state->isInterrupted()) {
        $this->recordCompletion($state);

        return;
    }

    $this->recordPause(
        $state->getWorkflowId(),
        $state->getRunId(),
        $state->getExecutionAttempt(),
        $state->getInterruptRequest(),
    );
}

private function recordPause(
    string $workflowId,
    string $runId,
    int $attempt,
    InterruptRequest $request,
): void {
    // Repeatable: a redelivery finds the row, and nobody is notified twice.
    $approval = PendingApproval::firstOrCreate([
        'workflow_id'  => $workflowId,
        'run_id'       => $runId,
        'interrupt_id' => $request->getId(),
    ], [
        'execution_attempt' => $attempt,
        'tenant_id'         => $this->tenantId,
        'type'              => 'refund',
        'subject_type'      => Order::class,
        'subject_id'        => $this->orderId,
        'request'           => \json_encode($request),
        'status'            => 'pending',
        'expires_at'        => $request instanceof RefundApprovalRequest ? $request->getExpiresAt() : null,
    ]);

    if ($approval->wasRecentlyCreated) {
        Notification::send(
            $this->approversFor($approval),
            new ApprovalRequired($approval)
        );
    }
}
```

Per la pausa non si cattura nulla. `run()` ritorna normalmente, e lo stato dice se la run è finita o è in attesa. La pausa è un risultato, non un'eccezione (Sezione 15.1) — ed è per questo che il record di business e la notifica stanno sotto un normale `if`.

**Il run ID è riservato, non generato.** Lo conia il controller che accetta la richiesta di rimborso — `(string) Str::uuid()` — e lo passa al job insieme all'ordine e all'importo, così che ogni consegna di quel job nomini la stessa run. `ExecutionRequest::start(runId: ..., recoverFailed: true)` dice allora ogni volta la stessa cosa: avvia questa run oppure, se una consegna precedente l'ha lasciata fallita o il suo worker è stato ucciso, portala a termine dall'ultimo step registrato. Un semplice `run()` non può dirlo. Recupera qualunque run fallita trovi sotto il workflow ID, quindi una seconda richiesta per un ordine il cui primo rimborso è fallito a metà porterebbe a termine in silenzio la *prima* richiesta — il suo importo, il suo caso — e la riporterebbe come la seconda.

L'unica eccezione che vale la pena catturare è `RunInFlightException`. `RefundWorkflow` dichiara `refund:{orderId}` come suo workflow ID (Sezione 15.4), e un avvio riservato non sostituisce mai una run che non ha avviato lui, quindi una seconda richiesta di rimborso per un ordine il cui primo rimborso è ancora in attesa di approvazione — o è fallito, e attende di essere recuperato — viene rifiutata prima che giri qualunque cosa. È una regola di business che ottieni gratis; trasformala in un messaggio invece che in un job fallito. `reservedRunId` distingue questo caso dagli altri due, in cui la run di intralcio è del job stesso. Trovata sospesa, è stata messa in pausa da una consegna precedente morta prima di registrare la pausa: l'eccezione porta il run ID, il tentativo e la richiesta, che è tutto ciò che serve al record. Trovata ancora in esecuzione, il job torna in coda finché il lease non è scaduto.

`recordPause()` è scritto per essere ripetuto: `firstOrCreate()` sulla chiave unica della tabella significa che una riconsegna trova la riga scritta da una consegna precedente, e solo la consegna che l'ha creata notifica. La persistenza è il binding del Capitolo 18 — `DatabasePersistence` sulla connessione di Laravel stessa — iniettato in `handle()`. Il lease, e `$tries = 3` e `$timeout = 300` che questo job dichiara come il prossimo, sono spiegati nelle Sezioni 22.3 e 22.4.

La scadenza viene dalla richiesta. `RefundApprovalRequest` è una sottoclasse di `WaitForEventRequest` (Sezione 15.3), e il nodo che la solleva imposta `expiresAt` — così le 48 ore vivono in un solo posto, il workflow, e la tua tabella si limita a rispecchiarle per l'indicizzazione.

### Chi notificare

```php
private function approversFor(PendingApproval $approval): Collection
{
    return User::query()
        ->where('tenant_id', $approval->tenant_id)
        ->whereHas('roles', fn ($q) => $q->where('name', 'approver'))
        ->get();
}
```

Basato sui ruoli, vincolato al tenant. Estendilo con delle soglie — un rimborso da 50 € va a un supervisore, uno da 5.000 € va a un manager — usando l'importo già presente nel payload della richiesta.

### La notifica

```php
class ApprovalRequired extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(
        private readonly PendingApproval $approval,
    ) {}

    public function via(object $notifiable): array
    {
        return ['mail', 'database'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $request = \json_decode($this->approval->request, true);

        return (new MailMessage())
            ->subject("Approval needed: {$request['message']}")
            ->line($request['message'])
            ->action('Review', route('approvals.show', $this->approval))
            ->line('This request expires ' . $this->approval->expires_at->diffForHumans() . '.');
    }
}
```

`$request['message']` è lì perché ce lo mette `RefundApprovalRequest::metadata()`. La forma JSON di una richiesta è composta dai campi del framework — `interruptId`, `type`, `eventName`, `expiresAt` — seguiti da ciò che aggiunge la tua sottoclasse; progetta `metadata()` per la schermata e per l'email, visto che sono i suoi unici lettori.

### Due punti di progetto

**Metti nell'email abbastanza per decidere — ma decidi nell'applicazione.**

L'oggetto e il corpo dovrebbero dire a chi approva di che cosa si tratta, così da poter fare triage senza cliccare. La decisione vera e propria avviene su una pagina autenticata, perché è lì che puoi autorizzarla, bloccarla e tracciarla in audit.

Resisti ai link approva/respingi a un clic nelle email. Sono comodi, e sono una superficie di sicurezza a URL firmati che adesso ti tocca implementare correttamente.

**Dichiara la scadenza.** Chi approva sapendo che la richiesta scade fra 48 ore si comporta diversamente da chi non lo sa. Rende anche visibile invece che sorprendente la politica di timeout della Sezione 22.4.

### Punti chiave

- `run()` ritorna; su `isInterrupted()`, registra la proiezione e notifica.
- Parti da un run ID riservato dalla richiesta e da `recoverFailed: true`, mai da un semplice `run()`.
- Cattura `RunInFlightException` — una sola run attiva per workflow ID è una regola di business, e `reservedRunId` distingue una seconda richiesta da una riconsegna.
- La scadenza vive sulla richiesta; la tua tabella la rispecchia.
- Instrada chi approva per ruolo, tenant e soglia.
- L'email per la consapevolezza; la decisione nell'applicazione autenticata.

## 22.3 La schermata di approvazione e la ripresa sicura

### L'indice

```php
class ApprovalsController extends Controller
{
    public function index(Request $request)
    {
        $approvals = PendingApproval::query()
            ->where('tenant_id', $request->user()->tenant_id)
            ->where('status', 'pending')
            ->with('subject')
            ->latest()
            ->paginate(20);

        return view('approvals.index', compact('approvals'));
    }

    public function show(PendingApproval $approval)
    {
        Gate::authorize('resolve', $approval);

        return view('approvals.show', [
            'approval' => $approval,
            'request'  => \json_decode($approval->request, true),
        ]);
    }
}
```

Una pagina indice con una policy. Niente di esotico — ed è proprio il punto.

### L'azione di risoluzione, con il lock

```php
public function resolve(Request $request, PendingApproval $approval)
{
    Gate::authorize('resolve', $approval);

    $requested = \json_decode($approval->request, true)['amount'];

    $validated = $request->validate([
        'decision' => ['required', 'in:approve,reject'],
        'feedback' => ['nullable', 'string', 'max:2000'],
        // The approver may lower the amount, never raise it.
        'amount'   => ['nullable', 'numeric', 'min:0', "max:{$requested}"],
    ]);

    $locked = DB::transaction(function () use ($approval, $validated, $request) {
        $fresh = PendingApproval::whereKey($approval->id)
            ->lockForUpdate()
            ->first();

        if ($fresh->status !== 'pending') {
            return null;   // someone else already decided
        }

        $fresh->update([
            'status'      => $validated['decision'] === 'approve' ? 'approved' : 'rejected',
            'response'    => \json_encode($validated),
            'resolved_by' => $request->user()->id,
            'resolved_at' => now(),
        ]);

        return $fresh;
    });

    if ($locked === null) {
        return back()->with('warning', 'This request was already resolved by someone else.');
    }

    ResumeRefundWorkflow::dispatch($locked, $validated);

    return redirect()
        ->route('approvals.index')
        ->with('status', 'Decision recorded. The workflow is continuing.');
}
```

### Due livelli, due compiti

Due manager aprono la stessa email ed entrambi cliccano approva. Due cose non devono succedere: il rimborso non deve essere pagato due volte, e i tuoi record non devono dire che l'hanno approvato due persone.

**Della prima si occupa il motore.** Ogni modifica di una run è una scrittura condizionale sul suo record di controllo, quindi può essere accettata una sola continuazione. Una seconda ripresa di una run conclusa non trova nulla in corso; una che fa a gara con la prima perde la scrittura. Per un rimborso è la differenza fra pagare una volta e pagare due volte, e regge anche se il tuo codice sbaglia il lock.

**Della seconda si occupa il tuo lock.** `lockForUpdate()` dentro una transazione, con lo stato controllato *dopo* aver acquisito il lock — controllarlo prima è una race condition. Senza, il motore paga comunque una volta sola, ma entrambi i manager vedono "decisione registrata", entrambi vengono salvati come chi ha approvato, e la traccia di audit mente. Il lock è ciò che trasforma il secondo clic in "già risolta da qualcun altro".

**La ripresa viene inviata, non eseguita in linea.** Il controller registra una decisione e ritorna. Riprendere può richiedere un minuto; chi approva non dovrebbe aspettarlo, e un timeout HTTP non dovrebbe lasciare orfano il workflow.

Quel terzo punto è facile da saltare ed è la differenza fra una schermata che sembra istantanea e una che si pianta.

### Il job di ripresa

```php
class ResumeRefundWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;

    /** Longer than the longest continuation, shorter than the queue's retry_after (360). */
    public int $timeout = 300;

    public function __construct(
        public readonly PendingApproval $approval,
        public readonly ?array $decision,   // null: deliver nothing, let the workflow check its deadline
    ) {}

    public function handle(PersistenceInterface $runs): void
    {
        $workflow = RefundWorkflow::make(orderId: $this->approval->subject_id)
            ->setPersistence($runs)
            ->setLeaseTimeout(600);

        try {
            $state = $workflow->run($this->request($workflow->inspect()));
        } catch (StaleWorkflowRunException $e) {
            // The run this answer was meant for is gone or replaced. Nothing was touched.
            Log::info('Stale refund resume ignored', ['approval' => $this->approval->id]);

            return;
        }

        if ($state->isInterrupted()) {
            return;   // still waiting: the deadline is not due yet
        }

        $this->recordOutcome($state);   // audit row, customer notification
    }

    private function request(?WorkflowRunSnapshot $run): ExecutionRequest
    {
        $runId = $this->approval->run_id;

        // A redelivery: the answer is already in and a later step failed. Finish that run.
        if ($run?->runId === $runId && $run->status === WorkflowStatus::Failed) {
            return ExecutionRequest::resume(
                expectedRunId: $runId,
                expectedExecutionAttempt: $run->executionAttempt,   // the attempt it is on now
            );
        }

        $fences = [
            'expectedRunId'            => $runId,
            'expectedExecutionAttempt' => $this->approval->execution_attempt,
        ];

        if ($this->decision === null) {
            // Nothing to deliver: the workflow checks its own deadline.
            return ExecutionRequest::resume(...$fences);
        }

        return ExecutionRequest::signal(
            RefundApprovalRequest::EVENT,
            $this->decision,
            ...$fences,
        );
    }
}
```

I requisiti della Sezione 15.4, ora in un job in coda: **la stessa classe di workflow**, ricostruita a partire dal solo ID dell'ordine perché la classe dichiara `refund:{orderId}` come suo workflow ID; **la stessa persistenza**; e **il payload** — un semplice array, che il nodo legge direttamente. Non c'è alcuna richiesta di interruzione da ricostruire.

Ciò che il job aggiunge è la coppia di **fence**. `expectedRunId` ed `expectedExecutionAttempt` sono i valori che la run ha riportato quando è andata in pausa, e il motore si rifiuta di consegnare la risposta se nel frattempo la run è andata avanti — una nuova generazione sotto lo stesso workflow ID, o un altro worker che l'ha già fatta proseguire. Le code riconsegnano, gli utenti fanno doppio clic, i deploy riavviano i worker a metà job: i fence trasformano ciascuno di questi casi in un rifiuto invece che in una risposta applicata alla richiesta sbagliata.

**Il primo ramo di `request()` è quello che fa pagare i rimborsi.** Il job viene ritentato — `$tries = 3` — perché una continuazione si può rieseguire senza rischi: gli step completati vengono riprodotti dallo store, non eseguiti (Sezione 13.5). Ma un ritentativo non può limitarsi a ripetersi. Una volta che il motore ha accettato la risposta, la run è a un tentativo di esecuzione successivo, e se poi uno step seguente lancia — l'API di pagamento è giù — la run è `failed` e il tentativo nella tua tabella è obsoleto per sempre: consegnare di nuovo la risposta può solo essere rifiutato. Perciò ogni consegna legge prima la run. Una run che è ancora questa e `Failed` contiene già la sua risposta; ciò che le serve è una ripresa senza input con il fence sul tentativo in cui si trova *adesso*, che riusa gli step registrati e riesegue quello fallito. Senza quel ramo un rimborso approvato il cui step di pagamento è fallito una volta non viene mai pagato. Con esso, quello step può girare due volte, quindi la chiamata di pagamento al suo interno deve portare una chiave di idempotenza costruita a partire dal workflow ID e dal run ID — mai dal tentativo, che cambia a ogni ritentativo.

I ritentativi richiedono che tre orologi siano d'accordo, gli stessi tre di qualunque run in coda (Capitolo 21). Il lease — `setLeaseTimeout(600)` — deve durare più del singolo step più lungo della run. Il `$timeout` del job deve durare più della continuazione più lunga. E il `retry_after` della connessione di coda deve superare `$timeout`: `DB_QUEUE_RETRY_AFTER=360` per un `$timeout` di 300, dove Laravel fornisce 90 e consegna a un secondo worker un job ancora in esecuzione. Il job di avvio della Sezione 22.2 dichiara gli stessi `$tries` e `$timeout`.

::: {.callout .callout-warning}
[Due fence, due tipi di eccezione]{.callout-title}

Su neuron-ai 4.0.2 solo il fence sul run ID lancia `StaleWorkflowRunException`. Un *tentativo* obsoleto — la stessa run, già fatta proseguire da un altro worker — lancia un semplice `WorkflowException` il cui messaggio inizia con *"Stale continuation"* (Appendice A, punto 74), quindi il `catch` qui sopra lo lascia passare e il job fallisce. Lascia che sia così. Un run ID obsoleto dimostra che la run è sparita o è stata sostituita; un tentativo obsoleto dice soltanto che è andata avanti, e può essere andata avanti in un worker che nel frattempo è morto. Il ritentativo rilegge la run: sparita, e il `catch` logga un no-op; fallita, e `request()` la porta a termine; ancora detenuta, e dopo la terza consegna l'hook `failed()` del job (Sezione 22.4) mette l'approvazione davanti a una persona. Se catturi quell'eccezione come no-op, un rimborso approvato che nessuno sta pagando viene loggato come innocuo. Controlla il motore nella tua versione installata prima di fare affidamento sull'uno o sull'altro comportamento.
:::

Consegna la risposta con `ExecutionRequest::signal()` invece che con `ExecutionRequest::resume()`. Entrambi accettano i due fence; il `signal()` della Sezione 15.3 controlla anche il nome dell'evento, così una decisione può raggiungere solo una run che sta aspettando `refund.decided`. Tieni il `resume()` senza input per i due casi in cui non c'è nulla da consegnare: una scadenza da controllare, e una run fallita da portare a termine.

### Il caso modificabile

Per un `ContentReviewInterrupt` (Sezione 15.3), la schermata è una textarea:

```blade
<form method="POST" action="{{ route('approvals.resolve', $approval) }}">
    @csrf

    <p class="mb-3">{{ $request['message'] }}</p>

    <textarea name="content" rows="20" class="w-full border rounded p-3">{{ $request['content'] }}</textarea>

    <div class="mt-4 flex gap-2">
        <button name="decision" value="approve" class="px-4 py-2 bg-black text-white rounded">
            Approve and publish
        </button>
        <button name="decision" value="reject" class="px-4 py-2 border rounded">
            Send back with feedback
        </button>
    </div>
</form>
```

L'essere umano modifica il contenuto; la versione modificata torna dentro il workflow come chiave `content` del payload. Aggiungi `'content' => ['nullable', 'string']` alle regole di validazione e viaggia invariata attraverso lo stesso job. Il pattern di collaborazione della Sezione 15.3, in un form. È molto più utile di approva/respingi per qualunque cosa l'AI abbia abbozzato — perché la risposta comune è "quasi".

### Punti chiave

- Il motore impedisce la doppia ripresa; `lockForUpdate()` mantiene onesti i tuoi record.
- Controlla lo stato mentre tieni il lock; registra la decisione, invia la ripresa — mai riprendere in linea.
- Ricostruisci a partire dalla chiave di business, consegna la risposta con `ExecutionRequest::signal()`, e proteggi con il run ID e il tentativo che hai salvato.
- Ritenta il job, e leggi la run a ogni consegna: una run fallita dopo che la risposta è entrata si porta a termine con una ripresa senza input sul suo tentativo corrente.
- Un run ID obsoleto è un no-op: la run è sparita. Un tentativo obsoleto non prova nulla — lascia che il job fallisca e riprovi.
- Per i contenuti abbozzati, una textarea batte due pulsanti.

## 22.4 Timeout, zombie e deploy

### Far scadere le approvazioni ferme

La scadenza appartiene al workflow. `RefundApprovalRequest` porta `expiresAt`, e quando dopo di essa arriva un `run(ExecutionRequest::resume())` senza input, il workflow rientra nel nodo in attesa senza risposta; `interruptIf()` restituisce `null` e il nodo prende il suo ramo di timeout. Il nodo non confronta mai orologi, e nel core non gira alcun timer — il tuo scheduler deve solo bussare:

```php
class ExpireStaleApprovals extends Command
{
    protected $signature = 'approvals:expire';

    public function handle(): int
    {
        PendingApproval::query()
            ->where('status', 'pending')
            ->where('expires_at', '<', now())
            ->chunkById(100, function ($approvals) {
                foreach ($approvals as $approval) {
                    ResumeRefundWorkflow::dispatch($approval, null);
                }
            });

        return self::SUCCESS;
    }
}
```

**Non consegnare nulla; non fabbricare un rifiuto.** Una decisione `null` è una ripresa senza input. Prima della scadenza — disallineamento degli orologi fra server, una richiesta la cui scadenza è stata spostata — il workflow resta semplicemente sospeso e il job ritorna. Dopo, il nodo registra una scadenza e la run si completa, notifica e fa pulizia. Il `recordOutcome()` del job marca l'approvazione come `expired` a partire dallo stato restituito dal workflow, così il record segue il workflow e non il contrario.

Schedulalo:

```php
Schedule::command('approvals:expire')->hourly();
```

### Escalation prima della scadenza

Comportamento di prodotto migliore di un timeout silenzioso:

```php
Schedule::call(function () {
    PendingApproval::where('status', 'pending')
        ->where('created_at', '<', now()->subHours(24))
        ->whereNull('escalated_at')
        ->each(function ($approval) {
            Notification::send($approval->escalationTargets(), new ApprovalOverdue($approval));
            $approval->update(['escalated_at' => now()]);
        });
})->hourly();
```

Sollecita a 24 ore, fai scadere a 48.

### Che cosa resta nello store

Una run che si completa fa pulizia da sé: una conclusione pulita cancella in modo condizionale l'intera partizione della run in `workflow_store`, quindi i rimborsi completati non lasciano nulla dietro di sé. Ciò che si accumula sono le run che non finiscono mai — richieste sospese a cui nessuno risponderà mai, run il cui worker è fallito e nessuno ha ritentato.

Non cancellare a mano le loro righe. Le scritture dello store sono protette dal suo record di controllo, e un `DELETE` grezzo può fare a gara con un worker che sta recuperando la stessa run. Chiedilo invece al motore:

```php
$engine = app(WorkflowEngine::class);

PendingApproval::query()
    ->where('status', 'failed')
    ->where('updated_at', '<', now()->subDays(30))
    ->each(function (PendingApproval $approval) use ($engine) {
        try {
            $engine->abandon($approval->workflow_id, $approval->run_id);
        } catch (StaleWorkflowRunException) {
            // Nothing of that run is left: it is gone, or a newer run holds the order.
        } catch (WorkflowException $e) {
            // Live under a lease, or a retained completion: not this sweep's to remove.
            report($e);
        }
    });
```

`WorkflowEngine` gestisce le run per workflow ID senza costruire il workflow — tutto ciò che serve a una scansione — e Laravel lo risolve automaticamente sul binding di persistenza del Capitolo 18. Il suo `abandon()` scarta una run in pausa, fallita o morta e libera il workflow ID, con il fence del run ID che passi. Lascia fuori il tentativo: quello nella tua tabella è il tentativo che ha messo in pausa, e una run fallita dopo di esso è andata oltre. Quando `abandon()` non può fare ciò che gli hai chiesto, lancia, e un'eccezione che sfugge a `each()` termina la scansione — da qui i due catch. `StaleWorkflowRunException` significa che quella run non detiene più l'ID: è già sparita, oppure l'ordine ha una run più recente. Un semplice `WorkflowException` è un rifiuto: una run viva sotto un lease, o un completamento trattenuto. Trenta giorni di grazia, poi si rimuove.

### Worker crashati e lease

Un worker ucciso a metà run — l'OOM killer, il `SIGKILL` di un deploy, un timeout del job — non ha modo di registrare nulla. La sua run resta marcata `running`, e il motore non può distinguerla da un worker semplicemente lento.

Un **lease** risolve la questione. Con `setLeaseTimeout(600)` la run detiene una scadenza che ogni step registrato rinnova; una volta decorsa, la run conta come morta. Una riconsegna del job che l'ha avviata la recupera allora, riusando gli step registrati — è a questo che serve `recoverFailed: true` sull'avvio riservato — e lo stesso fa un `run(ExecutionRequest::resume())` senza input; un semplice `run()` la sostituirebbe e ricomincerebbe da capo. Senza lease solo un `run(ExecutionRequest::resume())` esplicito può prendere in carico la run. Un agent detiene per default un lease di dieci minuti; un workflow semplice non ne detiene nessuno, ed è per questo che entrambi i job ne impostano uno.

Scegli il lease superiore al tratto silenzioso più lungo fra due step — una chiamata lenta al provider, una richiesta di pagamento — e non in base al `$timeout` del job: ciascuno dei tre orologi della Sezione 22.3 è misurato rispetto a qualcosa di diverso. Un lease più corto di una chiamata lenta al provider riporta in vita una run che non era morta — e a quel punto due worker la stanno eseguendo.

### Completamenti persi

Resta una lacuna. La `run()` del job di ripresa completa il rimborso, e il worker muore prima che `recordOutcome()` scriva la riga di audit. Il workflow è concluso e i suoi record sono spariti; la tua tabella dice ancora `approved`, senza alcun rimborso registrato.

Per i workflow in cui questo conta, conserva l'esito finché non l'hai registrato:

```php
$workflow = RefundWorkflow::make(orderId: $this->approval->subject_id)
    ->setPersistence($runs)
    ->setLeaseTimeout(600)
    ->retainCompletionUntilAcknowledged();

$state = $workflow->run($this->request($workflow->inspect()));

// ...the stale and still-waiting returns, as above

$this->recordOutcome($state);

$workflow->acknowledge($this->approval->run_id);
```

Con la ritenzione attiva, il completamento scrive lo stato terminale nello store invece di cancellare tutto. Se il worker muore prima di confermare, la riconsegna trova la run `Completed`, e la risposta che porta è obsoleta. Ciò che deve chiedere è l'esito: `run(ExecutionRequest::resume(expectedRunId: $runId))`, senza payload, riproduce l'esito trattenuto senza eseguire alcun nodo; tu lo registri, e poi confermi. In `request()` è uno stato in più nel primo ramo — `Completed` accanto a `Failed`. Fino ad allora il workflow ID resta occupato — un nuovo avvio per quell'ordine lancia `RunInFlightException`, il cui messaggio cita `acknowledge()` e il run ID — che è esattamente il promemoria che vuoi.

### Il problema dei deploy, e come conviverci

La Sezione 15.4 lo segnalava; ecco la gestione pratica.

La run persistita contiene **le tue classi**, serializzate: lo stato, gli eventi, la richiesta di interruzione pendente. Rinomina un nodo, cambia una classe di stato, aggiungi una proprietà tipizzata a una richiesta di interruzione — e la deserializzazione delle run in volo si rompe.

Quattro mitigazioni, in ordine di utilità:

**1. Tieni le richieste di interruzione piccole e piatte.** Stringhe, numeri, array. Niente model, niente connessioni, niente closure. Più piccola è la superficie, meno c'è da rompere.

**2. Aggiungi proprietà con valori di default, e versiona la forma trasmessa.**

```php
class RefundApprovalRequest extends WaitForEventRequest
{
    public const EVENT = 'refund.decided';

    public const VERSION = 2;

    // Added in version 2. Declared with a default, so requests suspended
    // by version 1 unserialise with 'EUR' instead of an uninitialised property.
    protected string $currency = 'EUR';

    public function __construct(
        final protected string $message,
        final protected int $orderId,
        final protected float $amount,
        ?DateTimeImmutable $expiresAt = null,
    ) {
        parent::__construct(self::EVENT, $expiresAt);
    }

    /**
     * The version-2 field is set with a wither, in the style of the
     * framework's own withId(): the constructor - and every call site written
     * for version 1 - stays as it was.
     *
     * PHP 8.5: clone() takes the properties to change, and #[\NoDiscard]
     * warns if the caller drops the copy and keeps the unchanged original.
     */
    #[\NoDiscard('withCurrency() returns a copy; the original request is unchanged.')]
    public function withCurrency(string $currency): static
    {
        return clone($this, ['currency' => $currency]);
    }

    public function getMessage(): string
    {
        return $this->message;
    }

    /**
     * @return array<string, mixed>
     */
    protected function metadata(): array
    {
        return [
            'version'  => self::VERSION,
            'message'  => $this->message,
            'orderId'  => $this->orderId,
            'amount'   => $this->amount,
            'currency' => $this->currency,
        ];
    }
}
```

Le due metà risolvono problemi diversi. La deserializzazione non esegue il tuo costruttore, quindi una proprietà che la versione 1 non ha mai scritto semplicemente manca: se è dichiarata con un default, la vecchia richiesta torna con quel default; se è promossa, o tipizzata senza default, la prima lettura è un errore fatale. La `version` in `metadata()` è per gli altri lettori — la schermata di approvazione e chiunque costruisca il payload di ripresa — così un form renderizzato da una richiesta della versione 1 può ancora ricevere risposta nella forma che il nodo si aspetta.

Due funzionalità di PHP 8.5 mantengono la classe onesta. Le proprietà promosse sono `final`, così una sottoclasse non può ridichiarare i campi che `metadata()` mette in trasmissione; e `clone($this, ['currency' => $currency])` copia l'oggetto e imposta le proprietà elencate in un'unica espressione, ed è così che `withCurrency()` aggiunge il campo della versione 2 senza toccare il costruttore né alcun punto di chiamata scritto per la versione 1.

**3. Svuota prima dei deploy rischiosi.** Per una release che cambia le classi dei workflow, smetti di inviare nuovi workflow, lascia che quelli pendenti si risolvano, poi fai il deploy. Aggiornare NeuronAI stesso rientra in questa categoria: le run sospese con un formato di store più vecchio non possono essere riprese da uno più nuovo.

**4. Fallisci rumorosamente.** Un job di ripresa che non riesce a deserializzare la run lancia un'eccezione. Lascialo fare: marca l'approvazione come `failed` dall'hook `failed()` del job, logga il workflow ID e il run ID, e lascia la run a un essere umano perché la recuperi o la abbandoni. Un fallimento visibile è recuperabile; uno silenzioso no.

### Monitoraggio

Quattro numeri che meritano una dashboard:

- Approvazioni pendenti, per età
- Approvazioni scadute negli ultimi 7 giorni — un numero in crescita significa che è rotto il tuo processo, non il tuo codice
- Riprese fallite, e riprese obsolete ignorate — un filo costante delle seconde è normale, un picco significa che qualcosa sta riconsegnando
- Approvazioni ferme su `approved` senza esito registrato — i completamenti persi della sezione precedente

### Punti chiave

- Fai scadere con una ripresa senza input; il workflow controlla la propria scadenza e prende il suo ramo di timeout.
- Fai escalation prima di far scadere.
- Le run completate si cancellano da sole; ripulisci il resto con `abandon()`, mai con un `DELETE` grezzo, e aspettati che lanci quando non c'è nulla da abbandonare.
- Imposta un lease superiore allo step silenzioso più lungo, `$timeout` superiore al job più lungo e `retry_after` superiore a `$timeout`; trattieni i completamenti che non puoi permetterti di perdere.
- Lo stato serializzato contiene le tue classi — tieni le richieste piatte, dai un default alle nuove proprietà, svuota prima dei deploy rischiosi e fallisci rumorosamente.

## 22.5 Approvazione dei tool di un agent in Laravel

Il workflow dei rimborsi possiede la propria pausa: è un nodo a decidere di interrompere. La pausa di un agent viene invece da un tool. La Sezione 15.5 ha mostrato il meccanismo — il tool dichiara un'approval policy, il `ToolNode` dell'agent interrompe con un'azione per ogni chiamata soggetta ad approvazione, e `submitApprovalDecisions()` fa proseguire la run. Ecco che cosa serve in un'applicazione Laravel.

### L'agent

```php
class SupportAgent extends Agent
{
    public function __construct(
        protected MessageStoreInterface $conversations,
        protected PersistenceInterface $runs,
    ) {
        parent::__construct();
    }

    protected function messageStore(): MessageStoreInterface
    {
        return $this->conversations;   // durable: it holds the pending tool call
    }

    protected function persistence(): PersistenceInterface
    {
        return $this->runs;            // durable: it holds the paused run
    }

    protected function tools(): array
    {
        $scope = ThreadScope::of($this->getThreadId());

        return [
            new SearchOrdersTool($scope->tenantId),
            (new IssueRefundTool($scope->tenantId))->requireApproval(),
        ];
    }

    // provider(), contextWindow() and recoverFailedTurn() as in Chapter 18
}
```

Due collaboratori durevoli, ed entrambi sono necessari. La **persistenza del workflow** contiene la run in pausa; lo store in memoria predefinito la dimenticherebbe alla fine della richiesta. Un **message store durevole** contiene la conversazione, compresa la tool call pendente dell'assistente; senza, il thread non può proseguire in un'altra richiesta. Sono i due binding del Capitolo 18, iniettati dal container e restituiti dai due hook — e devono essere proprio questi hook. Un agent che sovrascrive ancora `chatHistory()` carica e va in pausa senza errori mentre la sua conversazione resta in memoria (Sezione 18.2). La card di approvazione si renderizza comunque, perché la run in pausa è durevole; approvarla fallisce con `ChatHistoryException`, perché la tool call a cui risponde non è più in nessuna cronologia.

Nessuno dei due riceve il thread ID. Gli store sono servizi condivisi; il thread viene legato a ogni richiesta, con `for()`. Non solo: **il thread ID è il workflow ID dell'agent.** La run in pausa è archiviata in `workflow_store` sotto il thread, quindi tutto ciò che deve ritrovarla — l'endpoint di approvazione, la pagina che si ricarica — ha bisogno del thread e di nient'altro. Non c'è alcun run ID da salvare, ed è per questo che qui instradare una decisione non ha bisogno di una tabella `pending_approvals`. Il registro di chi ha approvato che cosa resta comunque da tenere a te: scrivilo in `decide()`.

### Un endpoint per il turno, uno per le decisioni

```php
class ThreadController extends Controller
{
    public function chat(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ): JsonResponse {
        Gate::authorize('participate', $conversation);

        $validated = $request->validate(['message' => ['required', 'string', 'max:4000']]);

        $agent = $agent->for($conversation->threadId());
        $agent->recoverFailedTurn();

        try {
            $state = $agent->chat(new UserMessage($validated['message']));
        } catch (RunInFlightException $e) {
            // suspended: decisions are pending; running: another request holds the turn
            return response()->json([
                'status'  => $e->status->value,
                'pending' => $agent->pendingApprovals(),
            ], 409);
        }

        return $this->respond($agent, $state);
    }

    public function pending(Conversation $conversation, SupportAgent $agent): JsonResponse
    {
        Gate::authorize('participate', $conversation);

        return response()->json(
            $agent->for($conversation->threadId())->pendingApprovals()
        );
    }

    public function decide(
        Request $request,
        Conversation $conversation,
        SupportAgent $agent,
    ): JsonResponse {
        Gate::authorize('approveTools', $conversation);

        $validated = $request->validate(['decisions' => ['required', 'array']]);

        $agent = $agent->for($conversation->threadId());

        try {
            $state = $agent->submitApprovalDecisions($validated['decisions'])->run();
        } catch (InputTranslationException $e) {
            return response()->json(['error' => $e->getMessage()], 400);
        } catch (WorkflowException $e) {
            // Two approvers at once, and the other one won: send back what is still open.
            return response()->json([
                'status'  => 'conflict',
                'pending' => $agent->pendingApprovals(),
            ], 409);
        }

        return $this->respond($agent, $state);
    }

    private function respond(SupportAgent $agent, AgentState $state): JsonResponse
    {
        return response()->json($state->isInterrupted()
            ? ['status' => 'awaiting_approval', 'pending' => $agent->pendingApprovals()]
            : ['status' => 'completed', 'answer' => $state->getMessage()?->getContent()]);
    }
}
```

### Che cosa fa ciascun pezzo

**`RunInFlightException` è il lock che hai dimenticato di costruire.** Un nuovo messaggio su un thread la cui run è in attesa di una decisione viene rifiutato dal motore prima che qualunque cosa raggiunga il modello o lo store. Mappalo su HTTP 409 e rimanda indietro le azioni pendenti, così il client può renderizzarle di nuovo. La tua UI dovrebbe bloccare l'input finché ci sono approvazioni aperte; questo è ciò che succede quando non lo fa. La stessa eccezione con lo stato `running` è una seconda richiesta che arriva mentre un turno è ancora in esecuzione: lo stesso 409, senza nulla di pendente.

**`recoverFailedTurn()` viene prima di `chat()`.** La quinta domanda della Sezione 18.4 morde più forte qui. Chi approva dice sì, il rimborso viene emesso, e il provider fallisce alla chiamata subito dopo: la run è `failed` con la sua domanda già memorizzata, e ogni messaggio successivo su quel thread viene rifiutato con `ChatHistoryException`. Portare prima a termine il turno fallito riusa gli step registrati — il rimborso non viene emesso una seconda volta — e costa una lettura quando non c'è nulla da portare a termine.

**`pendingApprovals()` sopravvive a un refresh della pagina.** Legge l'interruzione persistita in un processo a freddo e restituisce gli oggetti `Action` ancora in attesa di una decisione — ciascuno con l'ID della tool call come `id`, il nome del tool, il motivo che il tool ha dato per chiedere, e i suoi `inputs`. È ciò che la pagina chiama al mount. Riflette anche i progressi parziali: un'azione già decisa non viene più restituita.

**Le decisioni sono indicizzate per ID della tool call** e hanno tre forme: `'approve'`, `'reject'`, oppure `['reject', 'reason']`. Gli invii sono incrementali — una richiesta può portare solo le azioni decise di recente, e la run si risospende finché non ci sono tutte. Un tool gira solo se approvato esplicitamente; il silenzio non è mai consenso. Una decisione per un ID di chiamata che la run non sta aspettando viene respinta con `InputTranslationException` prima che venga eseguito qualunque cosa — un 400, non un 500.

**Due approvatori possono comunque scontrarsi.** Entrambi aprono la stessa card ed entrambi inviano. `submitApprovalDecisions()` cattura la run e il tentativo che ha letto, quindi viene accettata una sola continuazione; il `run()` dell'altro lancia un `WorkflowException` — `StaleWorkflowRunException` quando il vincitore ha già portato a termine la run, uno semplice finché il vincitore è ancora in esecuzione. È un 409 con ciò che è ancora pendente, e una pagina che si ricarica, non un 500. Gli stati sono quelli della mappatura a livello di applicazione in `bootstrap/app.php` (Capitolo 21); i catch locali ci sono per inviare insieme le azioni pendenti.

**Chi approva non deve per forza essere la persona che chatta.** `decide()` autorizza un'abilità diversa da `chat()`. La richiesta di rimborso di un cliente può restare in attesa nella sua conversazione mentre un manager, su un'altra schermata, chiama `pendingApprovals()` per quel thread e invia la decisione. Il thread ID è l'unico riferimento di cui entrambi hanno bisogno — ed è per questo che deve venire da un record per cui l'utente è autorizzato, mai direttamente dalla richiesta (Sezione 18.2).

### La scadenza per le approvazioni degli agent

Un'approvazione di un tool non porta con sé alcuna scadenza: una run di un agent sospesa non detiene alcun lease e aspetta indefinitamente. Se il tuo prodotto ne ha bisogno, tienila nella tua applicazione e annulla rifiutando:

```php
$agent = app(SupportAgent::class)->for($conversation->threadId());

$agent->submitApprovalDecisions(
    collect($agent->pendingApprovals())
        ->mapWithKeys(fn (Action $action) => [$action->id => ['reject', 'No decision within 48 hours']])
        ->all()
)->run();
```

Il modello riceve il rifiuto come risultato del tool e risponde al cliente di conseguenza, e il thread torna libero. Non ricorrere qui ad `abandon()`: su un agent lancia un `AgentException` finché c'è un'approvazione pendente, perché lascerebbe nella conversazione una tool call senza risposta. `resetConversation()` libera davvero il thread, al prezzo di cancellarne la cronologia.

### Punti chiave

- Un agent con approvazione ha bisogno di persistenza del workflow durevole e di un message store durevole, restituiti da `persistence()` e `messageStore()`.
- Il thread ID è il workflow ID: un unico riferimento per il turno, le decisioni e il ricaricamento.
- `RunInFlightException` significa "decisioni pendenti" — restituisci 409 con `pendingApprovals()`; anche una gara persa fra due approvatori è un 409.
- Recupera un turno fallito prima di ogni `chat()`.
- `pendingApprovals()` ricostruisce la UI di approvazione dopo un refresh; le decisioni sono incrementali e indicizzate per ID della tool call.
- Le approvazioni degli agent non hanno scadenza; falle scadere inviando dei rifiuti.

## Laboratorio 16 — Approvazione di un rimborso, dall'inizio alla fine

**Copre:** l'intera Parte IV e l'intera Parte V. È il laboratorio che dimostra che il pattern è distribuibile.

### Obiettivo

Un agent prepara un rimborso. Il workflow si ferma. Un manager approva da una schermata autenticata. Il workflow riprende su un worker ed esegue il rimborso — sopravvivendo nel frattempo a un riavvio di processo e a un deploy.

### Il flusso

```
Il cliente chiede un rimborso
   ↓
L'agent raccoglie l'ordine, verifica l'idoneità, prepara il caso   (memoizzato)
   ↓
Rimborso sopra i 100 €?  → interruzione, con un expiresAt a 48 ore
   ↓
Riga PendingApproval (workflow ID, run ID, tentativo) + notifica a chi approva
   ↓                                      (passano le ore; nulla è in esecuzione)
Il manager apre la schermata di approvazione, vede l'ordine e il caso
   ↓
Approva (con un importo rettificato opzionale) o respinge con feedback
   ↓
Job ResumeRefundWorkflow, con fence → rimborso eseguito → riga di audit → cliente notificato
```

### Requisiti

1. **Memoizza tutto prima dell'interruzione.** Sezione 15.5. Il caso che il manager legge deve essere il caso su cui il workflow agisce.
2. **`interruptIf()`** così che i rimborsi sotto i 100 € non interrompano mai.
3. **Un record `pending_approvals`** con relazione polimorfica verso l'`Order`, che salvi il run ID, l'interrupt ID e il tentativo di esecuzione, così che la schermata mostri su che cosa si sta decidendo e la ripresa possa essere protetta dal fence.
4. **`lockForUpdate()`** alla risoluzione, con lo stato controllato dentro il lock.
5. **Ripresa inviata, non in linea**, con `expectedRunId` ed `expectedExecutionAttempt`, in un job che può essere ritentato.
6. **`expiresAt` a 48 ore** sulla richiesta, escalation a 24, entrambi guidati dallo scheduler.
7. **Una riga di audit** per il rimborso, che nomina chi ha approvato.

### Criteri di accettazione

- Un rimborso da 40 € si completa senza alcun coinvolgimento umano.
- Un rimborso da 400 € crea un'approvazione, notifica, e nulla gira finché non viene risolta.
- Una seconda richiesta di rimborso per lo stesso ordine mentre la prima è pendente viene rifiutata con un messaggio chiaro, non con un job fallito.
- Due schede del browser che cliccano entrambe approva producono **un** rimborso e un messaggio "già risolta" nella seconda.
- Riavviare il queue worker e il server applicativo fra interruzione e ripresa non cambia nulla.
- Un rimborso approvato il cui step di pagamento lancia una volta viene pagato dal ritentativo del job — una volta sola, con il caso preparato una volta sola — invece di restare approvato e non pagato.
- L'importo nella riga di audit coincide con l'importo che chi approva ha visto. Dimostralo loggando dentro la closure memoizzata e confermando che sia stata eseguita una sola volta.
- Un'approvazione lasciata lì per 48 ore scade, riprende senza risposta, prende il ramo di timeout del nodo e notifica il cliente — invece di restare pendente per sempre.

### I due modi di fallire da riprodurre deliberatamente

**Doppia ripresa.** Togli il lock, clicca approva in due schede, e guarda che cosa succede. Il motore paga comunque una volta sola — il secondo job di ripresa viene rifiutato come obsoleto e non paga nulla — ma ora la tua tabella registra due approvatori per un solo rimborso. Rimetti il lock. Poi togli i fence dal job, invialo due volte a mano, e leggi il fallimento del secondo job: è l'errore che sarebbe stato mostrato ai tuoi utenti.

**Rigenerazione non memoizzata.** Sposta la preparazione del caso dentro il nodo di approvazione stesso, senza `memoize()`, e conferma che la run ripresa produca un caso diverso da quello approvato. Un nodo ripreso viene rieseguito dall'inizio. In un workflow di rimborso non è un'inefficienza — è approvare un importo e pagarne un altro. Poi rimettila nel suo nodo, o avvolgila in `memoize()`, e guarda la riga di log comparire esattamente una volta.

Sono entrambi esperimenti da cinque minuti, ed entrambi sono più convincenti di qualunque quantità di prosa sul perché quelle salvaguardie esistano.

### Andare oltre

Aggiungi una simulazione di deploy: interrompi un workflow, aggiungi una proprietà tipizzata *senza default* alla tua classe di richiesta di interruzione, fai il deploy e prova la ripresa. Guardala fallire alla prima lettura di quella proprietà. Poi dichiara la proprietà con un default, come nella Sezione 22.4, e guarda la stessa run sospesa riprendere. È l'esercizio che trasforma "tieni piatte le richieste di interruzione" da consiglio a regola che seguirai davvero.
