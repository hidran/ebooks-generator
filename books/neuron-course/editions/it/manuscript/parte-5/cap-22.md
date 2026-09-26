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
    $table->unsignedInteger('execution_attempt');
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

    $table->unique(['workflow_id', 'run_id']);
    $table->index(['tenant_id', 'status']);
    $table->index('expires_at');
});
```

**Perché due tabelle.** La tabella del framework è un insieme di record serializzati opachi indicizzati per partizione — non puoi interrogarla, filtrarla né autorizzare su di essa, e non dovresti provarci: le sue righe cambiano sotto scritture condizionali che non controlli. La tua è un normale record che puoi indicizzare, delimitare e renderizzare. Separarle significa che il framework possiede le sue viscere e tu possiedi il tuo prodotto.

**Ciò che copi è una proiezione, non la richiesta.** La persistenza del workflow resta la fonte autorevole per la richiesta pendente. La tua tabella conserva ciò che le serve per instradare la risposta — il workflow ID, il run ID e il tentativo di esecuzione che ha osservato — più una resa JSON della richiesta per la schermata. Run ID e tentativo sono i fence di consegna della Sezione 22.3; senza di essi una risposta tardiva o duplicata non si distingue da una attuale.

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
- Copia una proiezione — workflow ID, run ID, tentativo — e non trattare mai la tua copia come fonte di verità.
- Relazione polimorfica verso il soggetto, così chi approva vede su che cosa sta decidendo.
- Ogni esito, scadenza compresa, riprende il workflow.

## 22.2 Rilevare la pausa e notificare

### Il job che avvia la run

```php
public function handle(): void
{
    try {
        $state = RefundWorkflow::make(orderId: $this->orderId, requestedAmount: $this->amount)
            ->setPersistence(new EloquentPersistence(WorkflowStore::class))
            ->run();
    } catch (RunInFlightException $e) {
        // One live run per workflow ID: this order already has a refund in progress.
        $this->recordDuplicateRequest($e->status);

        return;
    }

    if (! $state->isInterrupted()) {
        $this->recordCompletion($state);

        return;
    }

    $request = $state->getInterruptRequest();

    $approval = PendingApproval::create([
        'workflow_id'       => $state->getWorkflowId(),
        'run_id'            => $state->getRunId(),
        'execution_attempt' => $state->getExecutionAttempt(),
        'tenant_id'         => $this->tenantId,
        'type'              => 'refund',
        'subject_type'      => Order::class,
        'subject_id'        => $this->orderId,
        'request'           => \json_encode($request),
        'status'            => 'pending',
        'expires_at'        => $request instanceof RefundApprovalRequest ? $request->getExpiresAt() : null,
    ]);

    Notification::send(
        $this->approversFor($approval),
        new ApprovalRequired($approval)
    );
}
```

Per la pausa non si cattura nulla. `run()` ritorna normalmente, e lo stato dice se la run è finita o è in attesa. La pausa è un risultato, non un'eccezione (Sezione 15.1) — ed è per questo che il record di business e la notifica stanno sotto un normale `if`.

L'unica eccezione che vale la pena catturare è `RunInFlightException`. `RefundWorkflow` dichiara `refund:{orderId}` come suo workflow ID (Sezione 15.4), quindi una seconda richiesta di rimborso per un ordine il cui primo rimborso è ancora in attesa di approvazione viene rifiutata prima che giri qualunque cosa. È una regola di business che ottieni gratis; trasformala in un messaggio invece che in un job fallito.

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
- Cattura `RunInFlightException` — una sola run attiva per workflow ID è una regola di business.
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
        $this->authorize('resolve', $approval);

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
    $this->authorize('resolve', $approval);

    $validated = $request->validate([
        'decision' => ['required', 'in:approve,reject'],
        'feedback' => ['nullable', 'string', 'max:2000'],
        'amount'   => ['nullable', 'numeric', 'min:0'],   // the approver may adjust it
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

    public int $tries = 1;

    public function __construct(
        public readonly PendingApproval $approval,
        public readonly ?array $decision,   // null: deliver nothing, let the workflow check its deadline
    ) {}

    public function handle(): void
    {
        try {
            $state = RefundWorkflow::make(orderId: $this->approval->subject_id)
                ->setPersistence(new EloquentPersistence(WorkflowStore::class))
                ->resume(
                    $this->decision,
                    expectedRunId: $this->approval->run_id,
                    expectedExecutionAttempt: $this->approval->execution_attempt,
                )
                ->run();
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
}
```

I requisiti della Sezione 15.4, ora in un job in coda: **la stessa classe di workflow**, ricostruita a partire dal solo ID dell'ordine perché la classe dichiara `refund:{orderId}` come suo workflow ID; **la stessa persistenza**; e **il payload** — un semplice array, che il nodo legge direttamente. Non c'è alcun oggetto richiesta da ricostruire.

Ciò che il job aggiunge è la coppia di **fence**. `expectedRunId` ed `expectedExecutionAttempt` sono i valori che la run ha riportato quando è andata in pausa, e `resume()` si rifiuta di consegnare la risposta se nel frattempo la run è andata avanti — una nuova generazione sotto lo stesso workflow ID, o un altro worker che l'ha già fatta proseguire. Le code riconsegnano, gli utenti fanno doppio clic, i deploy riavviano i worker a metà job: i fence trasformano ciascuno di questi casi in un no-op loggato invece che in una risposta applicata alla richiesta sbagliata.

::: {.callout .callout-warning}
[Due fence, due tipi di eccezione]{.callout-title}

Nella build 4.x su cui è stato verificato questo libro, solo il fence sul run ID lancia `StaleWorkflowRunException`. Un *tentativo* obsoleto — la stessa run, già fatta proseguire da un altro worker — lancia un semplice `WorkflowException` il cui messaggio inizia con *"Stale continuation"*, quindi il `catch` qui sopra lo lascia passare e il job fallisce invece di loggare un no-op. Finché la cosa non viene allineata a monte (Appendice A, voce 74), aggiungi un secondo `catch` per `WorkflowException` che tratti quel messaggio come obsoleto e rilanci tutto il resto. Controlla l'executor nella tua versione installata prima di fare affidamento sull'uno o sull'altro comportamento.
:::

Usa qui `resume()` invece del `signal()` della Sezione 15.3. `signal()` controlla il nome dell'evento, ma non accetta fence, e a un job che può essere consegnato due volte servono più i fence che il controllo del nome.

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
- Ricostruisci a partire dalla chiave di business, riprendi con il payload, e proteggi con il run ID e il tentativo che hai salvato.
- Tratta un fence obsoleto come un no-op: la risposta era per una run che è andata avanti. Verifica quale eccezione lancia la tua versione per ciascun fence.
- Per i contenuti abbozzati, una textarea batte due pulsanti.

## 22.4 Timeout, zombie e deploy

### Far scadere le approvazioni ferme

La scadenza appartiene al workflow. `RefundApprovalRequest` porta `expiresAt`, e quando dopo di essa arriva un `resume()` senza input, il workflow rientra nel nodo in attesa senza risposta; `interruptIf()` restituisce `null` e il nodo prende il suo ramo di timeout. Il nodo non confronta mai orologi, e nel core non gira alcun timer — il tuo scheduler deve solo bussare:

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

Non cancellare a mano le loro righe. Le scritture dello store sono protette dal suo record di controllo, e un `DELETE` grezzo può fare a gara con un worker che sta recuperando la stessa run. Chiedilo invece al workflow:

```php
PendingApproval::query()
    ->where('status', 'failed')
    ->where('updated_at', '<', now()->subDays(30))
    ->each(function (PendingApproval $approval) {
        RefundWorkflow::make(orderId: $approval->subject_id)
            ->setPersistence(new EloquentPersistence(WorkflowStore::class))
            ->abandonRun($approval->run_id);
    });
```

`abandonRun()` scarta una run in pausa, fallita o morta e libera il suo workflow ID, con il fence del run ID che passi. Rifiuta una run viva sotto un lease, e un completamento trattenuto. Trenta giorni di grazia, poi si rimuove.

### Worker crashati e lease

Un worker ucciso a metà run — l'OOM killer, il `SIGKILL` di un deploy, un timeout del job — non ha modo di registrare nulla. La sua run resta marcata `running`, e il motore non può distinguerla da un worker semplicemente lento.

Un **lease** risolve la questione. Con `setLeaseTimeout(900)` la run detiene una scadenza che ogni step committato rinnova; una volta decorsa, la run conta come morta, e la successiva `run()` la sostituisce (oppure `resume()->run()` la recupera, riusando gli step committati). Senza lease solo un `resume()->run()` esplicito può prendere in carico la run. Un agent detiene per default un lease di dieci minuti; un workflow semplice non ne detiene nessuno.

Scegli un timeout superiore al tratto silenzioso più lungo fra uno step e l'altro, e superiore al `$timeout` del job stesso. Un lease più corto di una chiamata lenta al provider riporta in vita una run che non era morta — e a quel punto due worker la stanno eseguendo.

### Completamenti persi

Resta una lacuna. La `run()` del job di ripresa completa il rimborso, e il worker muore prima che `recordOutcome()` scriva la riga di audit. Il workflow è concluso e i suoi record sono spariti; la tua tabella dice ancora `approved`, senza alcun rimborso registrato.

Per i workflow in cui questo conta, conserva l'esito finché non l'hai registrato:

```php
$workflow = RefundWorkflow::make(orderId: $approval->subject_id)
    ->setPersistence(new EloquentPersistence(WorkflowStore::class))
    ->retainCompletionUntilAcknowledged();

$state = $workflow->resume(/* ...as above */)->run();

$this->recordOutcome($state);

$workflow->acknowledgeCompletion($approval->run_id);
```

Con la ritenzione attiva, il completamento scrive lo stato terminale nello store invece di cancellare tutto. Se il worker muore prima di confermare, un job di riconciliazione chiama `resume(expectedRunId: $approval->run_id)->run()` senza payload: il workflow riproduce l'esito trattenuto senza eseguire alcun nodo, tu lo registri, e poi confermi. Fino ad allora il workflow ID resta occupato — una nuova `run()` per quell'ordine lancia `RunInFlightException` citando `acknowledgeCompletion()` — che è esattamente il promemoria che vuoi.

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
        protected string $message,
        protected int $orderId,
        protected float $amount,
        ?DateTimeImmutable $expiresAt = null,
    ) {
        parent::__construct(self::EVENT, $expiresAt);
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
- Le run completate si cancellano da sole; ripulisci il resto con `abandonRun()`, mai con un `DELETE` grezzo.
- Imposta un lease superiore allo step silenzioso più lungo; trattieni i completamenti che non puoi permetterti di perdere.
- Lo stato serializzato contiene le tue classi — tieni le richieste piatte, dai un default alle nuove proprietà, svuota prima dei deploy rischiosi e fallisci rumorosamente.

## 22.5 Approvazione dei tool di un agent in Laravel

Il workflow dei rimborsi possiede la propria pausa: è un nodo a decidere di interrompere. La pausa di un agent viene invece da un tool. La Sezione 15.5 ha mostrato il meccanismo — il tool dichiara un'approval policy, il `ToolNode` dell'agent interrompe con un'azione per ogni chiamata soggetta ad approvazione, e `submitApprovalDecisions()` fa proseguire la run. Ecco che cosa serve in un'applicazione Laravel.

### L'agent

```php
class SupportAgent extends Agent
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly User $user,
        string $threadId,
    ) {
        parent::__construct(threadId: $threadId);
    }

    protected function persistence(): PersistenceInterface
    {
        return new EloquentPersistence(WorkflowStore::class);
    }

    protected function chatHistory(): ChatHistoryInterface
    {
        return new EloquentChatHistory(ChatMessage::class);   // unbound: the agent binds its thread
    }

    protected function tools(): array
    {
        return [
            new SearchOrdersTool($this->orders),
            (new IssueRefundTool($this->orders))->requireApproval(),
        ];
    }
}
```

Due collaboratori durevoli, ed entrambi sono necessari. La **persistenza del workflow** contiene la run in pausa; lo store in memoria predefinito la dimenticherebbe alla fine della richiesta. Una **cronologia della conversazione durevole** contiene la conversazione, compresa la tool call pendente dell'assistente; senza, il thread non può proseguire in un'altra richiesta.

Nessuno dei due riceve il thread ID. L'agent l'ha ricevuto nel costruttore, e lega da sé la cronologia. Non solo: **il thread ID è il workflow ID dell'agent.** La run in pausa è archiviata in `workflow_store` sotto il thread, quindi tutto ciò che deve ritrovarla — l'endpoint di approvazione, la pagina che si ricarica — ha bisogno del thread e di nient'altro. Non c'è alcun run ID da salvare, ed è per questo che questa sezione non ha bisogno di una tabella `pending_approvals`.

### Un endpoint per il turno, uno per le decisioni

```php
class ThreadController extends Controller
{
    public function __construct(
        private readonly SupportAgentFactory $agents,
    ) {}

    public function chat(Request $request, Conversation $conversation): JsonResponse
    {
        $this->authorize('participate', $conversation);

        $validated = $request->validate(['message' => ['required', 'string', 'max:4000']]);
        $agent = $this->agents->forThread($conversation->thread_id);

        try {
            $state = $agent->chat(new UserMessage($validated['message']));
        } catch (RunInFlightException $e) {
            return response()->json([
                'status'  => 'awaiting_approval',
                'pending' => $agent->pendingApprovals(),
            ], 409);
        }

        return $this->respond($agent, $state);
    }

    public function pending(Conversation $conversation): JsonResponse
    {
        $this->authorize('participate', $conversation);

        return response()->json(
            $this->agents->forThread($conversation->thread_id)->pendingApprovals()
        );
    }

    public function decide(Request $request, Conversation $conversation): JsonResponse
    {
        $this->authorize('approveTools', $conversation);

        $validated = $request->validate(['decisions' => ['required', 'array']]);
        $agent = $this->agents->forThread($conversation->thread_id);

        try {
            $state = $agent->submitApprovalDecisions($validated['decisions'])->run();
        } catch (InputTranslationException $e) {
            return response()->json(['error' => $e->getMessage()], 422);
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

**`RunInFlightException` è il lock che hai dimenticato di costruire.** Un nuovo messaggio su un thread la cui run è in attesa di una decisione viene rifiutato dal motore prima che qualunque cosa raggiunga il modello o lo store. Mappalo su HTTP 409 e rimanda indietro le azioni pendenti, così il client può renderizzarle di nuovo. La tua UI dovrebbe bloccare l'input finché ci sono approvazioni aperte; questo è ciò che succede quando non lo fa.

**`pendingApprovals()` sopravvive a un refresh della pagina.** Legge l'interruzione persistita in un processo a freddo e restituisce gli oggetti `Action` ancora in attesa di una decisione — ciascuno con l'ID della tool call come `id`, il nome del tool, il motivo che il tool ha dato per chiedere, e i suoi `inputs`. È ciò che la pagina chiama al mount. Riflette anche i progressi parziali: un'azione già decisa non viene più restituita.

**Le decisioni sono indicizzate per ID della tool call** e hanno tre forme: `'approve'`, `'reject'`, oppure `['reject', 'reason']`. Gli invii sono incrementali — una richiesta può portare solo le azioni decise di recente, e la run si risospende finché non ci sono tutte. Un tool gira solo se approvato esplicitamente; il silenzio non è mai consenso. Una decisione per un ID di chiamata che la run non sta aspettando viene respinta con `InputTranslationException` prima che venga eseguito qualunque cosa — un 422, non un 500.

**Chi approva non deve per forza essere la persona che chatta.** `decide()` autorizza un'abilità diversa da `chat()`. La richiesta di rimborso di un cliente può restare in attesa nella sua conversazione mentre un manager, su un'altra schermata, chiama `pendingApprovals()` per quel thread e invia la decisione. Il thread ID è l'unico riferimento di cui entrambi hanno bisogno — ed è per questo che deve venire da un record per cui l'utente è autorizzato, mai direttamente dalla richiesta (Sezione 18.2).

### La scadenza per le approvazioni degli agent

Un'approvazione di un tool non porta con sé alcuna scadenza: una run di un agent sospesa non detiene alcun lease e aspetta indefinitamente. Se il tuo prodotto ne ha bisogno, tienila nella tua applicazione e annulla rifiutando:

```php
$agent = $this->agents->forThread($conversation->thread_id);

$agent->submitApprovalDecisions(
    collect($agent->pendingApprovals())
        ->mapWithKeys(fn (Action $action) => [$action->id => ['reject', 'No decision within 48 hours.']])
        ->all()
)->run();
```

Il modello riceve il rifiuto come risultato del tool e risponde al cliente di conseguenza, e il thread torna libero. Non ricorrere qui ad `abandonRun()`: si rifiuta finché c'è un'approvazione pendente, perché lascerebbe nella conversazione una tool call senza risposta.

### Punti chiave

- Un agent con approvazione ha bisogno di persistenza del workflow durevole e di una cronologia della conversazione durevole.
- Il thread ID è il workflow ID: un unico riferimento per il turno, le decisioni e il ricaricamento.
- `RunInFlightException` significa "decisioni pendenti" — restituisci 409 con `pendingApprovals()`.
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
3. **Un record `pending_approvals`** con relazione polimorfica verso l'`Order`, che salvi il run ID e il tentativo di esecuzione, così che la schermata mostri su che cosa si sta decidendo e la ripresa possa essere protetta dal fence.
4. **`lockForUpdate()`** alla risoluzione, con lo stato controllato dentro il lock.
5. **Ripresa inviata, non in linea**, con `expectedRunId` ed `expectedExecutionAttempt`.
6. **`expiresAt` a 48 ore** sulla richiesta, escalation a 24, entrambi guidati dallo scheduler.
7. **Una riga di audit** per il rimborso, che nomina chi ha approvato.

### Criteri di accettazione

- Un rimborso da 40 € si completa senza alcun coinvolgimento umano.
- Un rimborso da 400 € crea un'approvazione, notifica, e nulla gira finché non viene risolta.
- Una seconda richiesta di rimborso per lo stesso ordine mentre la prima è pendente viene rifiutata con un messaggio chiaro, non con un job fallito.
- Due schede del browser che cliccano entrambe approva producono **un** rimborso e un messaggio "già risolta" nella seconda.
- Riavviare il queue worker e il server applicativo fra interruzione e ripresa non cambia nulla.
- L'importo nella riga di audit coincide con l'importo che chi approva ha visto. Dimostralo loggando dentro la closure memoizzata e confermando che sia stata eseguita una sola volta.
- Un'approvazione lasciata lì per 48 ore scade, riprende senza risposta, prende il ramo di timeout del nodo e notifica il cliente — invece di restare pendente per sempre.

### I due modi di fallire da riprodurre deliberatamente

**Doppia ripresa.** Togli il lock, clicca approva in due schede, e guarda che cosa succede. Il motore paga comunque una volta sola — il secondo job di ripresa logga una continuazione obsoleta e non fa nulla — ma ora la tua tabella registra due approvatori per un solo rimborso. Rimetti il lock. Poi togli i fence dal job, invialo due volte a mano, e leggi il fallimento del secondo job: è l'errore che sarebbe stato mostrato ai tuoi utenti.

**Rigenerazione non memoizzata.** Sposta la preparazione del caso dentro il nodo di approvazione stesso, senza `memoize()`, e conferma che la run ripresa produca un caso diverso da quello approvato. Un nodo ripreso viene rieseguito dall'inizio. In un workflow di rimborso non è un'inefficienza — è approvare un importo e pagarne un altro. Poi rimettila nel suo nodo, o avvolgila in `memoize()`, e guarda la riga di log comparire esattamente una volta.

Sono entrambi esperimenti da cinque minuti, ed entrambi sono più convincenti di qualunque quantità di prosa sul perché quelle salvaguardie esistano.

### Andare oltre

Aggiungi una simulazione di deploy: interrompi un workflow, aggiungi una proprietà tipizzata *senza default* alla tua classe di richiesta di interruzione, fai il deploy e prova la ripresa. Guardala fallire alla prima lettura di quella proprietà. Poi dichiara la proprietà con un default, come nella Sezione 22.4, e guarda la stessa run sospesa riprendere. È l'esercizio che trasforma "tieni piatte le richieste di interruzione" da consiglio a regola che seguirai davvero.
