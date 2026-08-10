# Chapter 22 — Workflows and Human Approval in Production

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## 22.1 The Approval Lifecycle

### The insight from Section 18.4, expanded

Because interrupts are Eloquent rows, "the AI is waiting for a human" is a record in your database. Which means it gets everything database records get: a status, an owner, a deadline, an index page, a policy, an audit trail.

**Human-in-the-loop stops being an AI feature and becomes a workflow feature of your application.** That reframing is the point of this chapter.

### The supporting table

The package's `WorkflowInterrupt` holds the serialised execution state. You want a companion table holding the *business* view:

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

**Why two tables.** The framework's table is a serialised blob — you cannot query it, filter it, or authorise against it. Yours is a normal record you can index, scope and render. Separating them means the framework owns its internals and you own your product.

Also worth noting: `subject_type` / `subject_id` is a morph, so an approval links to the order, article or invoice it concerns. Without it, your approval screen shows an opaque JSON payload and the approver has to go and find the record themselves.

### The states

```
pending ──approve──→ approved ──→ (workflow resumed) ──→ completed
   │
   ├────reject───→ rejected ──→ (workflow resumed with rejection)
   │
   └────timeout──→ expired ──→ (escalated or abandoned)
```

**Rejection resumes the workflow too.** That is the point of Section 15.2's loop-back: rejection with feedback is another iteration, not a dead end.

### The four questions, answered

Section 15.4 posed them. Here are the Laravel answers, which the rest of this chapter builds:

| Question | Answer |
|---|---|
| Who is notified? | A `Notification` dispatched in the catch block (22.2) |
| What if nobody responds? | `expires_at` plus a scheduled command (22.4) |
| How to prevent double-resume? | `lockForUpdate()` on the status column (22.3) |
| What about deployments? | Small, flat, rarely-changed interrupt requests (22.4) |

### Key takeaways

- Interrupts are rows, so approvals are ordinary application state.
- Two tables: the framework's serialised blob and your queryable business record.
- Morph to the subject so approvers see what they are deciding about.
- Rejection resumes the workflow; it is not a terminal state.

## 22.2 Catching and Notifying

### The catch block

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

### Two design points

**Include enough in the email to decide — but decide in the app.**

The subject line and body should tell the approver what this is about, so they can triage without clicking. The decision itself happens on an authenticated page, because that is where you can authorise it, lock it and audit it.

Resist one-click approve/reject links in email. They are convenient, and they are a signed-URL security surface you now have to get right.

**State the expiry.** An approver who knows the request expires in 48 hours behaves differently from one who does not. It also makes Section 22.4's timeout policy visible rather than surprising.

### Key takeaways

- Create the business record and notify in the catch block.
- Route approvers by role, tenant and threshold.
- Email for awareness; decide in the authenticated application.
- Tell the approver when it expires.

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
        $this->authorize('resolve', $approval);

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

### The three things this gets right

**`lockForUpdate()` inside a transaction.** Two managers open the same email and both click approve. Without the lock, both dispatch a resume job and the workflow runs twice — which for a refund means paying twice.

**Status checked *after* acquiring the lock.** Checking before is a race; the check must happen while holding the lock.

**Resume is dispatched, not executed inline.** The controller records a decision and returns. Resuming may take a minute; the approver should not wait for it, and an HTTP timeout should not orphan the workflow.

That third point is easy to skip and it is the difference between a screen that feels instant and one that hangs.

### The resume job

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

Section 15.4's three requirements: same persistence, same workflow ID, reconstructed request.

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

The human edits the content; the edited version goes back into the workflow. Section 15.3's collaboration pattern, in a form. This is far more useful than approve/reject for anything the AI drafted — because the common response is "almost".

### Key takeaways

- `lockForUpdate()` in a transaction; check status while holding the lock.
- Record the decision, dispatch the resume — never resume inline.
- Same persistence, same ID, reconstructed request.
- For drafted content, a textarea beats two buttons.

## 22.4 Timeouts, Zombies and Deployments

### Expiring stale approvals

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

**Resume with a rejection rather than abandoning.** An abandoned workflow leaves its serialised state in the database forever and never tells anyone what happened. A rejected one completes, notifies, and cleans up.

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

### Orphaned interrupt rows

The framework's `workflow_interrupts` table grows. Clean up rows whose business record is resolved:

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

Thirty days of grace, then remove. Without this, a busy system accumulates serialised blobs indefinitely.

### The deployment problem, and how to live with it

Section 15.4 flagged it; here is the practical handling.

The serialised state contains **your classes**. Rename a node, add a typed property to a state class, change an interrupt request's constructor — and deserialisation of in-flight workflows breaks.

Four mitigations, in order of usefulness:

**1. Keep interrupt requests small and flat.** Strings, numbers, arrays. No models, no connections, no closures. The smaller the surface, the less there is to break.

**2. Version them.**

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

**3. Drain before risky deploys.** For a release that changes workflow classes, stop dispatching new workflows, let pending ones resolve, then deploy.

**4. Fail loudly.** Wrap the resume in a try/catch, log the deserialisation failure with the workflow ID, and mark the approval as `failed` rather than leaving it pending forever. A visible failure is recoverable; a silent one is not.

### Monitoring

Four numbers worth a dashboard:

- Pending approvals, by age
- Approvals expired in the last 7 days — a rising number means your process is broken, not your code
- Failed resumes
- Orphaned interrupt rows

### Key takeaways

- Expire by resuming with a rejection, never by abandoning.
- Escalate before expiring.
- Clean orphaned interrupt rows after a grace period.
- Serialised state contains your classes — keep requests flat, version them, drain before risky deploys.
- Fail loudly on deserialisation errors.

## Lab 16 — Refund Approval, End to End

**Covers:** the whole of Parts IV and V. This is the lab that proves the pattern is deployable.

### Goal

An agent prepares a refund. The workflow stops. A manager approves from an authenticated screen. The workflow resumes on a worker and executes the refund — surviving a process restart and a deploy in between.

### The flow

```
Customer asks for a refund
   ↓
Agent gathers the order, checks eligibility, prepares the case   (checkpointed)
   ↓
Refund over €100?  → interrupt
   ↓
PendingApproval row + notification to approvers
   ↓                                      (hours pass; nothing is running)
Manager opens the approval screen, sees the order and the case
   ↓
Approve (with an optional adjusted amount) or reject with feedback
   ↓
ResumeWorkflow job → refund executed → audit row → customer notified
```

### Requirements

1. **Checkpoint everything before the interrupt.** Section 15.5. The case the manager reads must be the case the workflow acts on.
2. **`interruptIf()`** so refunds under €100 never interrupt.
3. **A `pending_approvals` record** morphing to the `Order`, so the screen shows what is being decided.
4. **`lockForUpdate()`** on resolution, with the status checked inside the lock.
5. **Resume dispatched, not inline.**
6. **`expires_at` at 48 hours**, escalation at 24, both scheduled.
7. **An audit row** for the refund, naming the approver.

### Acceptance criteria

- A €40 refund completes with no human involvement.
- A €400 refund creates an approval, notifies, and nothing runs until it is resolved.
- Two browser tabs both clicking approve produce **one** refund and a "already resolved" message in the second.
- Restarting the queue worker and the application server between interrupt and resume changes nothing.
- The amount in the audit row matches the amount the approver saw. Prove this by logging inside the checkpoint closure and confirming it executed once.
- An approval left for 48 hours expires, resumes with a rejection, and notifies the customer — rather than sitting pending forever.

### The two failure modes to reproduce deliberately

**Double-resume.** Remove the lock, click approve in two tabs, and watch two refunds appear. Put it back.

**Un-checkpointed regeneration.** Remove the `checkpoint()` around the case preparation and confirm the resumed run produces a different case from the one approved. In a refund workflow that is not an inefficiency — it is approving one amount and paying another.

Both are five-minute experiments, and both are more convincing than any amount of prose about why the safeguards exist.

### Going further

Add a deployment simulation: interrupt a workflow, add a typed property to your interrupt request class, deploy, and attempt the resume. Watch it fail. Then apply the versioning from Section 22.4 and watch it succeed. That is the exercise that turns "keep interrupt requests flat" from advice into a rule you will actually follow.
