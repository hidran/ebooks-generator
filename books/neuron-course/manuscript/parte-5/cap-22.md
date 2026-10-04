# Chapter 22 — Workflows and Human Approval in Production

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The Laravel listings below live inside an application, but the workflow they drive is runnable on its own at [`chapters/Ch22`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch22) in the companion repository. `refund.php` walks the whole lifecycle — the auto-approved refund, the pause, the fenced resume, the refused redelivery, the expired deadline and the retained completion — with no model and no Laravel. `agent-approval.php` plays Section 22.5's agent approval round trip the same way, one fresh agent per request, rebuilt from the thread ID alone.
:::

## 22.1 The Approval Lifecycle

### The insight from Section 18.4, expanded

Because a suspended run lives in your database, "the AI is waiting for a human" is a fact your application can hold as a record. Which means it gets everything database records get: a status, an owner, a deadline, an index page, a policy, an audit trail.

**Human-in-the-loop stops being an AI feature and becomes a workflow feature of your application.** That reframing is the point of this chapter.

### The supporting table

The framework's `workflow_store` table holds the run itself: its control record, its completed steps, its suspended state, the pending request. You want a companion table holding the *business* view:

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

**Why two tables.** The framework's table is a set of opaque serialised records keyed by partition — you cannot query it, filter it, or authorise against it, and you should not try: its rows change under conditional writes you do not control. Yours is a normal record you can index, scope and render. Separating them means the framework owns its internals and you own your product.

**What you copy across is a projection, not the request.** The workflow persistence stays authoritative for the pending request. Your table keeps what it needs to route the answer — the workflow ID, the run ID, the interrupt ID and the execution attempt it observed — plus a JSON rendering of the request for the screen. The run ID and attempt are the delivery fences of Section 22.3; without them a late or duplicated answer cannot be told apart from a current one. The interrupt ID is there because one run can pause more than once — a rejection that loops back, a node that waits twice — and each pause gets a row of its own; a unique key without it would refuse the second.

Also worth noting: `subject_type` / `subject_id` is a morph, so an approval links to the order, article or invoice it concerns. Without it, your approval screen shows an opaque JSON payload and the approver has to go and find the record themselves.

### The states

```
pending ──approve──→ approved ──→ (workflow resumed) ──→ completed
   │
   ├────reject───→ rejected ──→ (workflow resumed with rejection)
   │
   └────deadline─→ expired ──→ (workflow resumed with no answer; the node takes its timeout branch)
```

**Every path resumes the workflow.** Approval continues it, rejection is another iteration (Section 15.2's loop-back), and an expiry is the workflow noticing its own deadline. None of them is a dead end that leaves a suspended run behind.

### The four questions, answered

Section 15.4 posed them. Here are the Laravel answers, which the rest of this chapter builds:

| Question | Answer |
|---|---|
| Who is notified? | A `Notification` dispatched when the run returns interrupted (22.2) |
| What if nobody responds? | `expiresAt` on the request, plus a scheduled inputless resume (22.4) |
| How to prevent double-resume? | The engine's conditional writes and delivery fences, plus `lockForUpdate()` on your record (22.3) |
| What about deployments? | Small, flat, rarely-changed interrupt requests with defaulted properties (22.4) |

### Key takeaways

- A suspended run is a database fact, so approvals are ordinary application state.
- Two tables: the framework's opaque store and your queryable business record.
- Copy a projection — workflow ID, run ID, interrupt ID, attempt — never treat your copy as the source of truth.
- Morph to the subject so approvers see what they are deciding about.
- Every outcome, including expiry, resumes the workflow.

## 22.2 Detecting the Pause and Notifying

### The job that starts the run

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

Nothing is caught for the pause. `run()` returns normally, and the state says whether the run finished or is waiting. The pause is a result, not an exception (Section 15.1) — which is why the business record and the notification sit on an ordinary `if`.

**The run ID is reserved, not generated.** The controller that accepts the refund request mints it — `(string) Str::uuid()` — and passes it to the job with the order and the amount, so every delivery of that job names the same run. `ExecutionRequest::start(runId: ..., recoverFailed: true)` then says the same thing each time: start this run or, if an earlier delivery left it failed or its worker was killed, finish it from its last committed step. A plain `run()` cannot say that. It recovers whatever failed run it finds under the workflow ID, so a second request for an order whose first refund failed halfway would silently finish the *first* request — its amount, its case — and report it as the second.

The one exception worth catching is `RunInFlightException`. `RefundWorkflow` declares `refund:{orderId}` as its workflow ID (Section 15.4), and a reserved start never replaces a run it did not start, so a second refund request for an order whose first one is still awaiting approval — or failed, and is waiting to be recovered — is refused before anything runs. That is a business rule you get for free; turn it into a message rather than a failed job. `reservedRunId` tells that case from the other two, in which the run in the way is this job's own. Found suspended, it was paused by an earlier delivery that died before it recorded the pause: the exception carries the run ID, the attempt and the request, which is all the record needs. Found still running, the job goes back on the queue until the lease has expired.

`recordPause()` is written to be repeated: `firstOrCreate()` on the table's unique key means a redelivery finds the row an earlier delivery wrote, and only the delivery that created it notifies. The persistence is Chapter 18's binding — `DatabasePersistence` over Laravel's own connection — injected into `handle()`. The lease, and the `$tries = 3` and `$timeout = 300` this job declares like the next one, are explained in Sections 22.3 and 22.4.

The deadline comes from the request. `RefundApprovalRequest` is a `WaitForEventRequest` subclass (Section 15.3), and the node that raises it sets `expiresAt` — so the 48 hours live in one place, the workflow, and your table merely mirrors them for indexing.

### Who to notify

```php
private function approversFor(PendingApproval $approval): Collection
{
    return User::query()
        ->where('tenant_id', $approval->tenant_id)
        ->whereHas('roles', fn ($q) => $q->where('name', 'approver'))
        ->get();
}
```

Role-based, tenant-scoped. Extend it with thresholds — a €50 refund goes to a supervisor, a €5,000 refund goes to a manager — using the amount already in the request payload.

### The notification

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

`$request['message']` is there because `RefundApprovalRequest::metadata()` puts it there. The JSON form of a request is the framework's fields — `interruptId`, `type`, `eventName`, `expiresAt` — followed by whatever your subclass adds; design `metadata()` for the screen and the email, since they are its only readers.

### Two design points

**Include enough in the email to decide — but decide in the app.**

The subject line and body should tell the approver what this is about, so they can triage without clicking. The decision itself happens on an authenticated page, because that is where you can authorise it, lock it and audit it.

Resist one-click approve/reject links in email. They are convenient, and they are a signed-URL security surface you now have to get right.

**State the expiry.** An approver who knows the request expires in 48 hours behaves differently from one who does not. It also makes Section 22.4's timeout policy visible rather than surprising.

### Key takeaways

- `run()` returns; on `isInterrupted()`, record the projection and notify.
- Start with a run ID reserved by the request and `recoverFailed: true`, never with a plain `run()`.
- Catch `RunInFlightException` — one live run per workflow ID is a business rule, and `reservedRunId` tells a second request from a redelivery.
- The deadline lives on the request; your table mirrors it.
- Route approvers by role, tenant and threshold.
- Email for awareness; decide in the authenticated application.

## 22.3 The Approval Screen and Safe Resume

### The index

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

An index page with a policy. Nothing exotic — which is the point.

### The resolve action, with the lock

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

### Two layers, two jobs

Two managers open the same email and both click approve. Two things must not happen: the refund must not be paid twice, and your records must not say two people approved it.

**The engine owns the first.** Every mutation of a run is a conditional write against its control record, so only one continuation can be accepted. A second resume of a finished run finds nothing in flight; one racing the first loses the write. For a refund that is the difference between paying once and paying twice, and it holds even if your own code gets the lock wrong.

**Your lock owns the second.** `lockForUpdate()` inside a transaction, with the status checked *after* acquiring the lock — checking before is a race. Without it the engine still pays once, but both managers see "decision recorded", both are stored as the approver, and the audit trail lies. The lock is what turns the second click into "already resolved by someone else".

**Resume is dispatched, not executed inline.** The controller records a decision and returns. Resuming may take a minute; the approver should not wait for it, and an HTTP timeout should not orphan the workflow.

That third point is easy to skip and it is the difference between a screen that feels instant and one that hangs.

### The resume job

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

Section 15.4's requirements, now in a queue job: **the same workflow class**, rebuilt from the order ID alone because the class declares `refund:{orderId}` as its workflow ID; **the same persistence**; and **the payload** — a plain array, which the node reads directly. There is no interrupt request to reconstruct.

What the job adds is the pair of **fences**. `expectedRunId` and `expectedExecutionAttempt` are the values the run reported when it paused, and the engine refuses to deliver the answer if the run has moved on since — a new generation under the same workflow ID, or another worker that already continued it. Queues redeliver, users double-click, deploys restart workers mid-job: the fences turn every one of those into a refusal instead of an answer applied to the wrong request.

**The first branch of `request()` is the one that gets refunds paid.** The job is retried — `$tries = 3` — because a continuation is safe to run again: completed steps are replayed from the store, not executed (Section 13.5). But a retry cannot simply repeat itself. Once the engine has accepted the answer the run is on a later attempt, and if a later step then throws — the payment API is down — the run is `failed` and the attempt in your table is stale for good: delivering the answer again can only be refused. So every delivery reads the run first. A run that is still this one and `Failed` already holds its answer; what it needs is an inputless resume fenced on the attempt it is on *now*, which reuses the committed steps and runs the failed one again. Without that branch an approved refund whose payment step failed once is never paid. With it, that step can run twice, so the payment call inside it must carry an idempotency key built from the workflow ID and the run ID — never from the attempt, which changes with every retry.

Retries need three clocks to agree, the same three as any queued run (Chapter 21). The lease — `setLeaseTimeout(600)` — must outlast the run's longest single step. The job's `$timeout` must outlast the longest continuation. And the queue connection's `retry_after` must exceed `$timeout`: `DB_QUEUE_RETRY_AFTER=360` for a `$timeout` of 300, where Laravel ships 90 and hands a job that is still running to a second worker. The start job of Section 22.2 declares the same `$tries` and `$timeout`.

::: {.callout .callout-warning}
[Two fences, two exception types]{.callout-title}

On neuron-ai 4.0.3 only the run-ID fence throws `StaleWorkflowRunException`. A stale *attempt* — the same run, already continued by another worker — throws a plain `WorkflowException` whose message begins *"Stale continuation"*, so the `catch` above lets it through and the job fails. Leave it that way. A stale run ID proves the run is gone or replaced; a stale attempt only says it has moved on, and it may have moved on into a worker that has since died. The retry reads the run again: gone, and the `catch` logs a no-op; failed, and `request()` finishes it; still held, and after the third try the job's `failed()` hook (Section 22.4) puts the approval in front of a human. Catch that exception as a no-op and an approved refund that nobody is paying is logged as harmless. Check the engine in your installed version before you rely on either behaviour.
:::

Deliver the answer with `ExecutionRequest::signal()` rather than `ExecutionRequest::resume()`. Both take the two fences; Section 15.3's `signal()` also checks the event name, so a decision can only reach a run that is waiting for `refund.decided`. Keep the inputless `resume()` for the two cases with nothing to deliver: a deadline to check, and a failed run to finish.

### The editable case

For a `ContentReviewInterrupt` (Section 15.3), the screen is a textarea:

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

The human edits the content; the edited version goes back into the workflow as the `content` key of the payload. Add `'content' => ['nullable', 'string']` to the validation rules and it travels through the same job unchanged. Section 15.3's collaboration pattern, in a form. This is far more useful than approve/reject for anything the AI drafted — because the common response is "almost".

### Key takeaways

- The engine prevents a double resume; `lockForUpdate()` keeps your records honest.
- Check status while holding the lock; record the decision, dispatch the resume — never resume inline.
- Rebuild from the business key, deliver the answer with `ExecutionRequest::signal()`, and fence with the run ID and attempt you stored.
- Retry the job, and read the run on every delivery: a run that failed after its answer went in is finished with an inputless resume on its current attempt.
- A stale run ID is a no-op: the run is gone. A stale attempt is not proof of anything — let the job fail and try again.
- For drafted content, a textarea beats two buttons.

## 22.4 Timeouts, Zombies and Deployments

### Expiring stale approvals

The deadline belongs to the workflow. `RefundApprovalRequest` carries `expiresAt`, and when an inputless `run(ExecutionRequest::resume())` arrives after it, the workflow re-enters the waiting node with no answer; `interruptIf()` returns `null` and the node takes its timeout branch. The node never compares clocks, and nothing in core runs a timer — your scheduler only has to knock:

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

**Deliver nothing; do not manufacture a rejection.** A `null` decision is an inputless resume. Before the deadline — clock skew between servers, a request whose deadline moved — the workflow simply stays suspended and the job returns. After it, the node records an expiry and the run completes, notifies and cleans up. The job's `recordOutcome()` marks the approval `expired` from the state the workflow returned, so the record follows the workflow rather than the other way round.

Schedule it:

```php
Schedule::command('approvals:expire')->hourly();
```

### Escalation before expiry

Better product behaviour than a silent timeout:

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

Nudge at 24 hours, expire at 48.

### What is left in the store

A run that completes cleans up after itself: a clean finish conditionally deletes the run's whole partition in `workflow_store`, so completed refunds leave nothing behind. What accumulates is runs that never finish — suspended requests nobody will ever answer, runs whose worker failed and nobody retried.

Do not delete their rows by hand. The store's writes are fenced by its control record, and a raw `DELETE` can race a worker that is recovering the same run. Ask the engine instead:

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

`WorkflowEngine` manages runs by workflow ID without building the workflow — all a sweep needs — and Laravel autowires it over Chapter 18's persistence binding. Its `abandon()` discards a paused, failed or dead run and frees the workflow ID, fenced by the run ID you pass. Leave the attempt out: the one in your table is the attempt that paused, and a run that failed afterwards has moved past it. When `abandon()` cannot do what you asked it throws, and an exception that escapes `each()` ends the sweep — hence the two catches. `StaleWorkflowRunException` means that run no longer holds the ID: it is already gone, or the order has a newer run. A plain `WorkflowException` is a refusal: a run that is live under a lease, or a retained completion. Thirty days of grace, then remove.

### Crashed workers and leases

A worker killed mid-run — the OOM killer, a deploy's `SIGKILL`, a job timeout — has no chance to record anything. Its run stays marked `running`, and the engine cannot tell that apart from a worker that is merely slow.

A **lease** resolves it. With `setLeaseTimeout(600)` the run holds a deadline that every committed step renews; once it lapses, the run counts as dead. A redelivery of the job that started it then recovers it, reusing the committed steps — that is what `recoverFailed: true` on the reserved start is for — and so does an inputless `run(ExecutionRequest::resume())`; a plain `run()` would replace it and begin again. Without a lease only an explicit `run(ExecutionRequest::resume())` can take the run over. An agent holds a ten-minute lease by default; a plain workflow holds none, which is why both jobs set one.

Choose the lease above the longest silent stretch between two steps — one slow provider call, one payment request — and not by the job's `$timeout`: each of Section 22.3's three clocks is measured against something different. A lease shorter than a slow provider call revives a run that was not dead — and then two workers are running it.

### Lost completions

One gap remains. The resume job's `run()` completes the refund, and the worker dies before `recordOutcome()` writes the audit row. The workflow is finished and its records are gone; your table still says `approved`, with no refund recorded.

For workflows where that matters, keep the outcome until you have recorded it:

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

With retention on, completion writes the terminal state into the store instead of deleting everything. If the worker dies before acknowledging, the redelivery finds the run `Completed`, and the answer it carries is stale. What it has to ask for is the outcome: `run(ExecutionRequest::resume(expectedRunId: $runId))`, with no payload, replays the retained outcome without executing any node; you record it, and then acknowledge. In `request()` that is one more status in the first branch — `Completed` next to `Failed`. Until then the workflow ID stays taken — a new start for that order throws `RunInFlightException`, whose message names `acknowledge()` and the run ID — which is exactly the reminder you want.

### The deployment problem, and how to live with it

Section 15.4 flagged it; here is the practical handling.

The persisted run contains **your classes**, serialised: the state, the events, the pending interrupt request. Rename a node, change a state class, add a typed property to an interrupt request — and deserialisation of in-flight runs breaks.

Four mitigations, in order of usefulness:

**1. Keep interrupt requests small and flat.** Strings, numbers, arrays. No models, no connections, no closures. The smaller the surface, the less there is to break.

**2. Add properties with defaults, and version the wire shape.**

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

The two halves solve different problems. Unserialising does not run your constructor, so a property that version 1 never wrote is simply missing: if it is declared with a default, the old request comes back with that default; if it is promoted, or typed without a default, the first read of it is a fatal error. The `version` in `metadata()` is for the other readers — the approval screen and whoever builds the resume payload — so a form rendered from a version 1 request can still be answered in the shape the node expects.

Two PHP 8.5 features keep the class honest. The promoted properties are `final`, so a subclass cannot redeclare the fields `metadata()` puts on the wire; and `clone($this, ['currency' => $currency])` copies the object and sets the listed properties in one expression, which is how `withCurrency()` adds the version 2 field without touching the constructor or any call site written for version 1.

**3. Drain before risky deploys.** For a release that changes workflow classes, stop dispatching new workflows, let pending ones resolve, then deploy. Upgrading NeuronAI itself counts as one of these: runs suspended by an older store format cannot be resumed by a newer one.

**4. Fail loudly.** A resume job that cannot deserialise the run throws. Let it: mark the approval as `failed` from the job's `failed()` hook, log the workflow ID and run ID, and leave the run for a human to recover or abandon. A visible failure is recoverable; a silent one is not.

### Monitoring

Four numbers worth a dashboard:

- Pending approvals, by age
- Approvals expired in the last 7 days — a rising number means your process is broken, not your code
- Failed resumes, and stale resumes ignored — a steady trickle of the second is normal, a spike means something is redelivering
- Approvals stuck in `approved` with no recorded outcome — the lost completions of the previous section

### Key takeaways

- Expire with an inputless resume; the workflow checks its own deadline and takes its timeout branch.
- Escalate before expiring.
- Completed runs delete themselves; clean up the rest with `abandon()`, never a raw `DELETE`, and expect it to throw when there is nothing to abandon.
- Set a lease above the longest silent step, `$timeout` above the longest job and `retry_after` above `$timeout`; retain completions you cannot afford to lose.
- Serialised state contains your classes — keep requests flat, give new properties defaults, drain before risky deploys, and fail loudly.

## 22.5 Agent Tool Approval in Laravel

The refund workflow owns its pause: a node decides to interrupt. An agent's pause comes from a tool. Section 15.5 showed the mechanism — the tool declares an approval policy, the agent's `ToolNode` interrupts with one action per gated call, and `submitApprovalDecisions()` continues the run. Here is what it takes in a Laravel application.

### The agent

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

Two durable collaborators, and both are required. **Workflow persistence** holds the paused run; the default in-memory store would forget it when the request ends. **A durable message store** holds the conversation, including the assistant's pending tool call; without it the thread cannot be continued in another request. They are Chapter 18's two bindings, injected by the container and returned from the two hooks — and it has to be these hooks. An agent that still overrides `chatHistory()` loads and pauses without an error while its conversation stays in memory (Section 18.2). The approval card still renders, because the paused run is durable; approving it fails with `ChatHistoryException`, because the tool call it answers is no longer in any history.

Neither is given the thread ID. The stores are shared services; the thread is bound for each request, with `for()`. More than that: **the thread ID is the agent's workflow ID.** The paused run is filed in `workflow_store` under the thread, so everything that needs to find it — the approval endpoint, the page that reloads — needs the thread and nothing else. There is no run ID to store, which is why routing a decision needs no `pending_approvals` table here. The record of who approved what is still yours to keep: write it in `decide()`.

### One endpoint for a turn, one for the decisions

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

### What each piece is doing

**`RunInFlightException` is the lock you forgot to build.** A new message on a thread whose run is waiting for a decision is refused by the engine before anything reaches the model or the store. Map it to HTTP 409 and send the pending actions back, so the client can re-render them. Your UI should lock the input while approvals are open; this is what happens when it does not. The same exception with the status `running` is a second request arriving while a turn is still executing: the same 409, with nothing pending.

**`recoverFailedTurn()` comes before `chat()`.** Section 18.4's fifth question bites hardest here. The approver says yes, the refund is issued, and the provider fails on the very next call: the run is `failed` with its question already stored, and every later message on that thread is refused with `ChatHistoryException`. Finishing the failed turn first reuses the committed steps — the refund is not issued a second time — and costs one read when there is nothing to finish.

**`pendingApprovals()` survives a page refresh.** It reads the persisted interruption in a cold process and returns the `Action` objects still awaiting a decision — each with the tool call ID as `id`, the tool name, the reason the tool gave for asking, and its `inputs`. It is what the page calls on mount. It also reflects partial progress: an action already decided is no longer returned.

**Decisions are keyed by tool call ID** and take three forms: `'approve'`, `'reject'`, or `['reject', 'reason']`. Submissions are incremental — a request may carry only the newly decided actions, and the run re-suspends until all of them are in. A tool runs only if explicitly approved; silence is never consent. A decision for a call ID the run is not waiting for is rejected with `InputTranslationException` before anything executes — a 400, not a 500.

**Two approvers can still collide.** Both open the same card and both submit. `submitApprovalDecisions()` captures the run and the attempt it read, so only one continuation is accepted; the other's `run()` throws a `WorkflowException` — `StaleWorkflowRunException` when the winner has already finished the run, a plain one while the winner is still executing. That is a 409 with whatever is still pending, and a page that reloads, not a 500. The statuses are those of the application-wide mapping in `bootstrap/app.php` (Chapter 21); the local catches are there to send the pending actions with them.

**The approver need not be the person chatting.** `decide()` authorises a different ability from `chat()`. A customer's refund request can wait in their conversation while a manager, on another screen, calls `pendingApprovals()` for that thread and submits the decision. The thread ID is the only handle either of them needs — which is why it must come from a record the user is authorised for, never straight from the request (Section 18.2).

### Expiry for agent approvals

A tool approval carries no deadline of its own: a suspended agent run holds no lease and waits indefinitely. If your product needs one, keep it in your application and cancel by declining:

```php
$agent = app(SupportAgent::class)->for($conversation->threadId());

$agent->submitApprovalDecisions(
    collect($agent->pendingApprovals())
        ->mapWithKeys(fn (Action $action) => [$action->id => ['reject', 'No decision within 48 hours']])
        ->all()
)->run();
```

The model receives the rejection as the tool's result and answers the customer accordingly, and the thread is free again. Do not reach for `abandon()` here: on an agent it throws an `AgentException` while an approval is pending, because it would leave an unanswered tool call in the conversation. `resetConversation()` does free the thread, at the price of wiping its history.

### Key takeaways

- An approving agent needs durable workflow persistence and a durable message store, returned from `persistence()` and `messageStore()`.
- The thread ID is the workflow ID: one handle for the turn, the decisions and the reload.
- `RunInFlightException` means "decisions pending" — return 409 with `pendingApprovals()`; a lost race between two approvers is a 409 too.
- Recover a failed turn before every `chat()`.
- `pendingApprovals()` rebuilds the approval UI after a refresh; decisions are incremental and keyed by tool call ID.
- Agent approvals have no deadline; expire them by submitting rejections.

## Lab 16 — Refund Approval, End to End

**Covers:** the whole of Parts IV and V. This is the lab that proves the pattern is deployable.

### Goal

An agent prepares a refund. The workflow stops. A manager approves from an authenticated screen. The workflow resumes on a worker and executes the refund — surviving a process restart and a deploy in between.

### The flow

```
Customer asks for a refund
   ↓
Agent gathers the order, checks eligibility, prepares the case   (memoized)
   ↓
Refund over €100?  → interrupt, with a 48-hour expiresAt
   ↓
PendingApproval row (workflow ID, run ID, attempt) + notification to approvers
   ↓                                      (hours pass; nothing is running)
Manager opens the approval screen, sees the order and the case
   ↓
Approve (with an optional adjusted amount) or reject with feedback
   ↓
ResumeRefundWorkflow job, fenced → refund executed → audit row → customer notified
```

### Requirements

1. **Memoize everything before the interrupt.** Section 15.5. The case the manager reads must be the case the workflow acts on.
2. **`interruptIf()`** so refunds under €100 never interrupt.
3. **A `pending_approvals` record** morphing to the `Order`, storing the run ID, the interrupt ID and the execution attempt, so the screen shows what is being decided and the resume can be fenced.
4. **`lockForUpdate()`** on resolution, with the status checked inside the lock.
5. **Resume dispatched, not inline**, with `expectedRunId` and `expectedExecutionAttempt`, in a job that may be retried.
6. **`expiresAt` at 48 hours** on the request, escalation at 24, both driven by the scheduler.
7. **An audit row** for the refund, naming the approver.

### Acceptance criteria

- A €40 refund completes with no human involvement.
- A €400 refund creates an approval, notifies, and nothing runs until it is resolved.
- A second refund request for the same order while the first is pending is refused with a clear message, not a failed job.
- Two browser tabs both clicking approve produce **one** refund and an "already resolved" message in the second.
- Restarting the queue worker and the application server between interrupt and resume changes nothing.
- An approved refund whose payment step throws once is paid by the job's retry — once, with the case prepared once — instead of staying approved and unpaid.
- The amount in the audit row matches the amount the approver saw. Prove this by logging inside the memoized closure and confirming it executed once.
- An approval left for 48 hours expires, resumes with no answer, takes the node's timeout branch and notifies the customer — rather than sitting pending forever.

### The two failure modes to reproduce deliberately

**Double-resume.** Remove the lock, click approve in two tabs, and watch what happens. The engine still pays once — the second resume job is refused as stale and pays nothing — but your table now records two approvers for one refund. Put the lock back. Then remove the fences from the job, dispatch it twice by hand, and read the second job's failure: that is the error your users would have been shown.

**Un-memoized regeneration.** Move the case preparation into the approval node itself, without `memoize()`, and confirm the resumed run produces a different case from the one approved. A resumed node re-executes from the top. In a refund workflow that is not an inefficiency — it is approving one amount and paying another. Then put it back in its own node, or wrap it in `memoize()`, and watch the logged line appear exactly once.

Both are five-minute experiments, and both are more convincing than any amount of prose about why the safeguards exist.

### Going further

Add a deployment simulation: interrupt a workflow, add a typed property *without a default* to your interrupt request class, deploy, and attempt the resume. Watch it fail on the first read of that property. Then declare the property with a default, as in Section 22.4, and watch the same suspended run resume. That is the exercise that turns "keep interrupt requests flat" from advice into a rule you will actually follow.
