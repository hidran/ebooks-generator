# Capitolo 22 — Workflow e approvazione umana in produzione

::: {.callout .callout-tip}
[Il codice di questo capitolo]{.callout-title}

Questo capitolo è concettuale e non ha codice a sé stante, ma il repository di accompagnamento [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) contiene le versioni eseguibili di tutto ciò che il libro costruisce.
:::

## 22.1 Il ciclo di vita di un'approvazione

### L'intuizione della Sezione 18.4, ampliata

Poiché le interruzioni sono righe Eloquent, "l'AI sta aspettando un essere umano" è un record nel tuo database. Il che significa che riceve tutto ciò che i record di un database ricevono: uno stato, un proprietario, una scadenza, una pagina indice, una policy, una traccia di audit.

**L'human-in-the-loop smette di essere una funzionalità AI e diventa una funzionalità di workflow della tua applicazione.** Quel cambio di inquadramento è il punto di questo capitolo.

### La tabella di supporto

Il `WorkflowInterrupt` del pacchetto contiene lo stato di esecuzione serializzato. Tu vuoi una tabella compagna che contenga la vista *di business*:

```php
Schema::create('pending_approvals', function (Blueprint $table) {
    $table->id();
    $table->string('workflow_id')->unique();
    $table->foreignId('tenant_id')->constrained();
    $table->foreignId('requested_by')->nullable()->constrained('users');
    $table->foreignId('resolved_by')->nullable()->constrained('users');

    $table->string('type');                 // refund, publish, escalation
    $table->string('subject_type')->nullable();
    $table->unsignedBigInteger('subject_id')->nullable();

    $table->json('request');                // the serialised InterruptRequest
    $table->json('response')->nullable();   // what the human decided

    $table->string('status')->default('pending');   // pending|approved|rejected|expired
    $table->timestamp('expires_at')->nullable();
    $table->timestamp('resolved_at')->nullable();

    $table->timestamps();

    $table->index(['tenant_id', 'status']);
    $table->index('expires_at');
});
```

**Perché due tabelle.** La tabella del framework è un blob serializzato — non puoi interrogarla, filtrarla né autorizzare su di essa. La tua è un normale record che puoi indicizzare, delimitare e renderizzare. Separarle significa che il framework possiede le sue viscere e tu possiedi il tuo prodotto.

Vale la pena notare anche: `subject_type` / `subject_id` è una relazione polimorfica, quindi un'approvazione si collega all'ordine, all'articolo o alla fattura che riguarda. Senza, la tua schermata di approvazione mostra un payload JSON opaco e chi approva deve andarsi a cercare il record da solo.

### Gli stati

```
pending ──approva──→ approved ──→ (workflow ripreso) ──→ completed
   │
   ├────respingi───→ rejected ──→ (workflow ripreso con il rifiuto)
   │
   └────timeout───→ expired ──→ (escalation o abbandono)
```

**Anche il rifiuto riprende il workflow.** È il punto del ritorno indietro della Sezione 15.2: il rifiuto con feedback è un'altra iterazione, non un vicolo cieco.

### Le quattro domande, con risposta

La Sezione 15.4 le poneva. Ecco le risposte Laravel, che il resto di questo capitolo costruisce:

| Domanda | Risposta |
|---|---|
| Chi viene notificato? | Una `Notification` inviata nel blocco catch (22.2) |
| E se nessuno risponde? | `expires_at` più un comando schedulato (22.4) |
| Come prevenire la doppia ripresa? | `lockForUpdate()` sulla colonna di stato (22.3) |
| E i deploy? | Richieste di interruzione piccole, piatte e cambiate di rado (22.4) |

### Punti chiave

- Le interruzioni sono righe, quindi le approvazioni sono ordinario stato applicativo.
- Due tabelle: il blob serializzato del framework e il tuo record di business interrogabile.
- Relazione polimorfica verso il soggetto, così chi approva vede su che cosa sta decidendo.
- Il rifiuto riprende il workflow; non è uno stato terminale.

## 22.2 Catturare e notificare

### Il blocco catch

```php
public function handle(): void
{
    $workflow = new RefundWorkflow(
        persistence: new EloquentPersistence(WorkflowInterrupt::class),
        workflowId: $this->workflowId,
    );

    try {
        $handler = $workflow->init();
        $handler->run();

        $this->recordCompletion($handler->getResult());

    } catch (WorkflowInterrupt $interrupt) {
        $approval = PendingApproval::create([
            'workflow_id'  => $interrupt->getWorkflowId(),
            'tenant_id'    => $this->tenantId,
            'type'         => 'refund',
            'subject_type' => Order::class,
            'subject_id'   => $this->orderId,
            'request'      => \json_encode($interrupt->getRequest()),
            'status'       => 'pending',
            'expires_at'   => now()->addHours(48),
        ]);

        Notification::send(
            $this->approversFor($approval),
            new ApprovalRequired($approval)
        );
    }
}
```

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

### Due punti di progetto

**Metti nell'email abbastanza per decidere — ma decidi nell'applicazione.**

L'oggetto e il corpo dovrebbero dire a chi approva di che cosa si tratta, così da poter fare triage senza cliccare. La decisione vera e propria avviene su una pagina autenticata, perché è lì che puoi autorizzarla, bloccarla e tracciarla in audit.

Resisti ai link approva/respingi a un clic nelle email. Sono comodi, e sono una superficie di sicurezza a URL firmati che adesso ti tocca implementare correttamente.

**Dichiara la scadenza.** Chi approva sapendo che la richiesta scade fra 48 ore si comporta diversamente da chi non lo sa. Rende anche visibile invece che sorprendente la politica di timeout della Sezione 22.4.

### Punti chiave

- Crea il record di business e notifica nel blocco catch.
- Instrada chi approva per ruolo, tenant e soglia.
- L'email per la consapevolezza; la decisione nell'applicazione autenticata.
- Di' a chi approva quando scade.

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
        'content'  => ['nullable', 'string'],   // for editable interrupts
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

    ResumeWorkflow::dispatch($locked->workflow_id, $validated);

    return redirect()
        ->route('approvals.index')
        ->with('status', 'Decision recorded. The workflow is continuing.');
}
```

### Le tre cose che questo fa bene

**`lockForUpdate()` dentro una transazione.** Due manager aprono la stessa email ed entrambi cliccano approva. Senza il lock, entrambi inviano un job di ripresa e il workflow gira due volte — cosa che per un rimborso significa pagare due volte.

**Lo stato viene controllato *dopo* aver acquisito il lock.** Controllarlo prima è una race condition; il controllo deve avvenire mentre si tiene il lock.

**La ripresa viene inviata, non eseguita in linea.** Il controller registra una decisione e ritorna. Riprendere può richiedere un minuto; chi approva non dovrebbe aspettarlo, e un timeout HTTP non dovrebbe lasciare orfano il workflow.

Quel terzo punto è facile da saltare ed è la differenza fra una schermata che sembra istantanea e una che si pianta.

### Il job di ripresa

```php
class ResumeWorkflow implements ShouldQueue
{
    public int $tries = 1;

    public function __construct(
        public readonly string $workflowId,
        public readonly array $decision,
    ) {}

    public function handle(): void
    {
        $workflow = new RefundWorkflow(
            persistence: new EloquentPersistence(WorkflowInterrupt::class),
            workflowId: $this->workflowId,
        );

        $request = RefundApprovalInterrupt::fromArray($this->decision);

        $result = $workflow->init($request)->run();

        WorkflowCompleted::dispatch($this->workflowId, $result);
    }
}
```

I tre requisiti della Sezione 15.4: stessa persistenza, stesso ID di workflow, richiesta ricostruita.

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

L'essere umano modifica il contenuto; la versione modificata torna dentro il workflow. Il pattern di collaborazione della Sezione 15.3, in un form. È molto più utile di approva/respingi per qualunque cosa l'AI abbia abbozzato — perché la risposta comune è "quasi".

### Punti chiave

- `lockForUpdate()` in una transazione; controlla lo stato mentre tieni il lock.
- Registra la decisione, invia la ripresa — mai riprendere in linea.
- Stessa persistenza, stesso ID, richiesta ricostruita.
- Per i contenuti abbozzati, una textarea batte due pulsanti.

## 22.4 Timeout, zombie e deploy

### Far scadere le approvazioni ferme

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
                    $approval->update([
                        'status'      => 'expired',
                        'resolved_at' => now(),
                    ]);

                    ResumeWorkflow::dispatch($approval->workflow_id, [
                        'decision' => 'reject',
                        'feedback' => 'No response received within the approval window.',
                    ]);
                }
            });

        return self::SUCCESS;
    }
}
```

**Riprendi con un rifiuto invece di abbandonare.** Un workflow abbandonato lascia il suo stato serializzato nel database per sempre e non dice mai a nessuno che cosa sia successo. Uno rifiutato si completa, notifica e fa pulizia.

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

### Righe di interruzione orfane

La tabella `workflow_interrupts` del framework cresce. Ripulisci le righe il cui record di business è risolto:

```php
WorkflowInterrupt::query()
    ->whereNotIn('workflow_id', function ($q) {
        $q->select('workflow_id')
          ->from('pending_approvals')
          ->where('status', 'pending');
    })
    ->where('updated_at', '<', now()->subDays(30))
    ->delete();
```

Trenta giorni di grazia, poi si rimuove. Senza questo, un sistema attivo accumula blob serializzati all'infinito.

### Il problema dei deploy, e come conviverci

La Sezione 15.4 lo segnalava; ecco la gestione pratica.

Lo stato serializzato contiene **le tue classi**. Rinomina un nodo, aggiungi una proprietà tipizzata a una classe di stato, cambia il costruttore di una richiesta di interruzione — e la deserializzazione dei workflow in volo si rompe.

Quattro mitigazioni, in ordine di utilità:

**1. Tieni le richieste di interruzione piccole e piatte.** Stringhe, numeri, array. Niente model, niente connessioni, niente closure. Più piccola è la superficie, meno c'è da rompere.

**2. Versionale.**

```php
class RefundApprovalInterrupt extends InterruptRequest
{
    public const VERSION = 2;

    public function jsonSerialize(): array
    {
        return [
            'version' => self::VERSION,
            'message' => $this->message,
            'amount'  => $this->amount,
        ];
    }

    public static function fromArray(array $data): static
    {
        return match ($data['version'] ?? 1) {
            1       => new static($data['message'], (float) $data['amount']),
            default => new static($data['message'], (float) $data['amount']),
        };
    }
}
```

**3. Svuota prima dei deploy rischiosi.** Per una release che cambia le classi dei workflow, smetti di inviare nuovi workflow, lascia che quelli pendenti si risolvano, poi fai il deploy.

**4. Fallisci rumorosamente.** Avvolgi la ripresa in un try/catch, logga il fallimento di deserializzazione con l'ID di workflow, e marca l'approvazione come `failed` invece di lasciarla pendente per sempre. Un fallimento visibile è recuperabile; uno silenzioso no.

### Monitoraggio

Quattro numeri che meritano una dashboard:

- Approvazioni pendenti, per età
- Approvazioni scadute negli ultimi 7 giorni — un numero in crescita significa che è rotto il tuo processo, non il tuo codice
- Riprese fallite
- Righe di interruzione orfane

### Punti chiave

- Fai scadere riprendendo con un rifiuto, mai abbandonando.
- Fai escalation prima di far scadere.
- Ripulisci le righe di interruzione orfane dopo un periodo di grazia.
- Lo stato serializzato contiene le tue classi — tieni le richieste piatte, versionale, svuota prima dei deploy rischiosi.
- Fallisci rumorosamente sugli errori di deserializzazione.

## Laboratorio 16 — Approvazione di un rimborso, dall'inizio alla fine

**Copre:** l'intera Parte IV e l'intera Parte V. È il laboratorio che dimostra che il pattern è distribuibile.

### Obiettivo

Un agent prepara un rimborso. Il workflow si ferma. Un manager approva da una schermata autenticata. Il workflow riprende su un worker ed esegue il rimborso — sopravvivendo nel frattempo a un riavvio di processo e a un deploy.

### Il flusso

```
Il cliente chiede un rimborso
   ↓
L'agent raccoglie l'ordine, verifica l'idoneità, prepara il caso   (con checkpoint)
   ↓
Rimborso sopra i 100 €?  → interruzione
   ↓
Riga PendingApproval + notifica a chi approva
   ↓                                      (passano le ore; nulla è in esecuzione)
Il manager apre la schermata di approvazione, vede l'ordine e il caso
   ↓
Approva (con un importo rettificato opzionale) o respinge con feedback
   ↓
Job ResumeWorkflow → rimborso eseguito → riga di audit → cliente notificato
```

### Requisiti

1. **Metti checkpoint su tutto prima dell'interruzione.** Sezione 15.5. Il caso che il manager legge deve essere il caso su cui il workflow agisce.
2. **`interruptIf()`** così che i rimborsi sotto i 100 € non interrompano mai.
3. **Un record `pending_approvals`** con relazione polimorfica verso l'`Order`, così che la schermata mostri su che cosa si sta decidendo.
4. **`lockForUpdate()`** alla risoluzione, con lo stato controllato dentro il lock.
5. **Ripresa inviata, non in linea.**
6. **`expires_at` a 48 ore**, escalation a 24, entrambi schedulati.
7. **Una riga di audit** per il rimborso, che nomina chi ha approvato.

### Criteri di accettazione

- Un rimborso da 40 € si completa senza alcun coinvolgimento umano.
- Un rimborso da 400 € crea un'approvazione, notifica, e nulla gira finché non viene risolta.
- Due schede del browser che cliccano entrambe approva producono **un** rimborso e un messaggio "già risolta" nella seconda.
- Riavviare il queue worker e il server applicativo fra interruzione e ripresa non cambia nulla.
- L'importo nella riga di audit coincide con l'importo che chi approva ha visto. Dimostralo loggando dentro la closure del checkpoint e confermando che sia stata eseguita una sola volta.
- Un'approvazione lasciata lì per 48 ore scade, riprende con un rifiuto e notifica il cliente — invece di restare pendente per sempre.

### I due modi di fallire da riprodurre deliberatamente

**Doppia ripresa.** Togli il lock, clicca approva in due schede, e guarda comparire due rimborsi. Rimettilo.

**Rigenerazione senza checkpoint.** Togli il `checkpoint()` attorno alla preparazione del caso e conferma che l'esecuzione ripresa produca un caso diverso da quello approvato. In un workflow di rimborso non è un'inefficienza — è approvare un importo e pagarne un altro.

Sono entrambi esperimenti da cinque minuti, ed entrambi sono più convincenti di qualunque quantità di prosa sul perché quelle salvaguardie esistano.

### Andare oltre

Aggiungi una simulazione di deploy: interrompi un workflow, aggiungi una proprietà tipizzata alla tua classe di richiesta di interruzione, fai il deploy e prova la ripresa. Guardala fallire. Poi applica il versionamento della Sezione 22.4 e guardala riuscire. È l'esercizio che trasforma "tieni piatte le richieste di interruzione" da consiglio a regola che seguirai davvero.
