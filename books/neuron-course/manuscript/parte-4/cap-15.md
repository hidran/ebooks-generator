# Chapter 15 — Human in the Loop

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of this chapter's core example — the approval node, its workflow, and the `start.php` and `resume.php` scripts of Section 15.4 — is at [`chapters/Ch15`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch15), in the companion repository. Clone it, run `composer install`, and the two scripts run as they are: pausing and resuming need no model and no API key.
:::

## 15.1 Interruption: The Feature, Not the Failure

### What it does

NeuronAI's interruption pattern lets a workflow **pause execution and wait for external input before resuming.**

Not "stop and start over". Pause — in the middle of a node — preserving everything the run has done so far, and continue from that node with the human's answer injected.

### The four phases

1. **Request** — a node identifies something requiring human input and calls `$this->interrupt()` with an `InterruptRequest` describing it.
2. **Pause** — the engine persists the run and `run()` returns a state marked as interrupted. Nothing is thrown at your code.
3. **Decision** — your application presents the request to a human, who approves, rejects or edits.
4. **Resume** — you hand the decision back as a plain array with `run(ExecutionRequest::resume($payload))`. Completed nodes are replayed from the store, the paused node runs again, and this time `interrupt()` returns the decision.

> A workflow can safely pause at any point, persist its state, and resume where it left off, **even across different sessions.**

### Why "even across different sessions" is the whole story

Read that literally. The PHP process ends. The web request completes. The server is redeployed. Three days pass.

Then the manager clicks "approve" in an email, and the workflow continues from the node where it stopped, with all its context intact.

For a PHP audience this is genuinely notable, because PHP's execution model is famously request-scoped. The framework's answer is the durable steps from Section 13.5 plus a persistence layer, and it turns "AI does the whole thing" into "AI does the work, a human makes the decisions" — which is the only shape most businesses will actually deploy for anything consequential.

### A pause is a result, not an exception

A suspended run is an ordinary outcome of `run()`. You check it on the returned state:

```php
$state = $workflow->run();

if ($state->isInterrupted()) {
    $request = $state->getInterruptRequest();
    // show it to a human
}
```

Under the hood, `interrupt()` still unwinds the node — it throws an internal signal that the engine catches at the step boundary. That is why any code in a node can interrupt, however deep in a helper it sits, without every intermediate layer threading a return value back. But the signal never reaches you. The engine converts it into a persisted suspension and returns normally.

The practical consequence: there is nothing to catch, and nothing to be logged as a crash by accident. What you must not forget instead is to *look*. A caller that ignores `isInterrupted()` will treat a paused run as a finished one and read state that has not been written yet. Section 15.4 covers the handling.

### Where this changes what you can build

Section 5.10's four defence layers included "offered, gated at runtime". This is that layer, and it unlocks a category of application:

- Refunds above a threshold
- Emails sent to customers on the company's behalf
- Any deletion
- Publishing content
- Anything with a regulatory sign-off requirement

Without interruption, these are either fully automated (unacceptable) or not automated (no value). With it, the AI does the preparation and a human makes the call — which is both safe and useful.

### Key takeaways

- Pause mid-node, persist the run, resume with human input.
- Four phases: request, pause, decision, resume.
- Survives process death and long delays — this is the distinguishing feature.
- A pause is returned, not thrown: check `isInterrupted()` on every state you get back.

## 15.2 interrupt() and ApprovalRequest

### The built-in request

```php
namespace App\Neuron;

use NeuronAI\Agent\Interrupt\Action;
use NeuronAI\Agent\Interrupt\ApprovalRequest;
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

### Reading it

**`$this->interrupt($request)`** — the pause. On the first pass execution stops here. On resume the node runs again and `interrupt()` returns the array the caller passed to `ExecutionRequest::resume()`.

**`ApprovalRequest`** — the built-in request for the most common case: approving actions. It lives in `NeuronAI\Agent\Interrupt`, alongside `Action`, because the agent's own tool approval (Section 15.5) is built on it. Nothing stops a plain workflow node from using it.

**`Action`** — a single decidable item: an identifier, a label, and a description. Several actions in one request means the human decides several things in one interaction, which is the difference between one approval screen and five.

**The payload** — a plain array, keyed however you decide. This book uses the same convention as the agent's tool approval, keyed by action ID: `'approve'`, `'reject'`, or `['reject', 'reason']`. It is a contract between the node and whoever resumes the run, so pick one shape and keep it.

**The reason on a rejection** — more useful than it looks. A rejection with a reason can go straight into the next agent call as guidance, turning "no" into "no, because X" and letting the loop actually improve.

**Returning `InputEvent` on rejection** — this node loops back. Rejection is not failure; it is another iteration. That combination of interruption plus loop is the human-in-the-loop refinement pattern, and it is what Lab 10 builds.

`ApprovalRequest` and `Action` are **outbound only**. `Action` is a read-only value object — its properties are `readonly` and it has no `approve()`, `reject()` or `feedback()` methods. The request describes what is being asked; the answer travels back separately, as the payload. You never mutate the request to record a decision.

::: {.callout .callout-warning}
[The documentation's examples do not match the code]{.callout-title}

The documentation imports `ApprovalRequest` from `NeuronAI\Workflow\Interrupt`, which does not exist; the class is `NeuronAI\Agent\Interrupt\ApprovalRequest`. Its custom-request example overrides `jsonSerialize()`, which is `final` on `InterruptRequest`, and its resume example names a `runId:` constructor argument that `Workflow` does not have. All three fail on the first run.
:::

### Design guidance for approval requests

**Write the message for the decider, not the developer.** They are seeing this in an email or an admin screen, with no context. `'Should I continue?'` is a poor message. `'Approve a €240 refund for order #4471 — customer reports item arrived damaged'` lets someone decide without opening another system.

**Include enough in the description to decide.** The third `Action` argument is where the substance goes.

**Group related decisions into one request.** Five actions in one request beats five sequential interruptions, each of which is a separate wake-up, notification and wait. Action IDs must be unique within a request; a duplicate is rejected when the request is built, because its decision could never be delivered.

### Key takeaways

- `$this->interrupt($request)` pauses, and on resume returns the payload array.
- `ApprovalRequest` (in `NeuronAI\Agent\Interrupt`) plus `Action` covers approve/reject.
- The request is outbound only; the decision comes back as a plain array whose shape you define.
- Write messages for the person deciding; group related decisions.

## 15.3 Custom Interrupt Requests

### Why approve/reject is not always enough

`ApprovalRequest` covers "should I do this action?". It does not cover "here is a draft — edit it before I save it", or "pick one of these three options", or "fill in the missing field".

The architecture is deliberately open. There are two kinds of pause — waiting for an event and waiting for a clock time — and `ApprovalRequest` is simply a `WaitForEventRequest` listening for an event called `approval`. You create your own by extending `WaitForEventRequest` the same way.

### The implementation

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

Three responsibilities:

**Name the event** it waits for — `content.reviewed` here. That name is what `ExecutionRequest::signal()` matches on resume (below).

**Carry the data** the human needs to decide, plus whatever they will edit.

**`metadata()`** — the fields your frontend needs. `jsonSerialize()` is `final`: the framework always emits the interrupt ID, the type and the event name, and merges your metadata in after them. Note the implication: your interruption crosses a JSON boundary. Keep it serialisable and flat.

What comes back is not a rebuilt request object. The engine persists the request itself, so there is no `fromArray()` to write. The human's answer arrives as a payload array, and the node reads what it needs from it.

That round trip — PHP object → JSON → UI → edited fields → payload array — is the whole lifecycle, and knowing it is where your frontend fits.

### Using it

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): SaveEvent
    {
        // Generate an article, once. See Section 15.5 for why this is memoized.
        // The sub-agent needs a thread ID of its own: derive it from the workflow's.
        $draft = $this->memoize('draft', fn (): string => ContentCreatorAgent::make()
            ->setThreadId($state->getWorkflowId() . ':draft')
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

And the resume, from whatever receives the edit:

```php
$state = ArticleWorkflow::make(workflowId: $workflowId)
    ->setPersistence($persistence)
    ->run(ExecutionRequest::signal('content.reviewed', ['content' => $editedText]));
```

`ExecutionRequest::signal()` is `ExecutionRequest::resume()` with a guard: the payload is delivered only if the current interruption is waiting for that event name, and `run()` throws a `WorkflowException` otherwise. Use it when the caller knows what it is answering — a webhook handler for `payment.received` should not be able to answer an approval by accident.

### The pattern worth naming

The agent generated content. The human **edited** it. The workflow saved the **edited** version.

That is not approval — it is collaboration. The AI produces a draft, the human corrects it, the system uses the corrected version. For content generation, document drafting, code suggestions and data extraction, this is a better product than approve/reject, because the common case is "nearly right" rather than "yes or no".

As a design principle: **when the likely human response is "almost, but change this", build an editable interrupt rather than an approval.**

::: {.callout .callout-warning}
[This example generates content before interrupting]{.callout-title}

Which is exactly the situation Section 15.5 is about. Without the `memoize()` around it, resuming this node re-runs `ContentCreatorAgent` and the human's edit is applied to a *different* draft. Read Section 15.5 before you ship anything shaped like this.
:::

### Waiting for events and clocks

Two helpers cover the pauses that are not a human decision at all:

```php
// Suspend until an external event arrives, or the deadline passes.
$payment = $this->awaitEvent('payment.received', expiresAt: new \DateTimeImmutable('+2 days'));

if ($payment === null) {
    return new OrderExpired();       // the deadline passed, nothing arrived
}

// Suspend until a clock time.
$this->sleepUntil(new \DateTimeImmutable('tomorrow 09:00'));
```

`awaitEvent()` is `interrupt()` with a `WaitForEventRequest`; `sleepUntil()` is `interrupt()` with a `SleepUntilRequest`. The engine records the deadline but runs no timer — nothing in core wakes up by itself. Your scheduler (cron, a delayed queue job) calls `run(ExecutionRequest::resume())`, with no payload, when the time comes, and the workflow checks the clock itself: before the deadline the run stays suspended, after it `awaitEvent()` returns `null` and `sleepUntil()` returns. For a wait nobody answered, the node never compares clocks. An answer that arrives after the deadline is another matter: the engine still delivers it, and a node that must refuse it reads the clock itself (Section 26.10).

`ApprovalRequest` takes the same optional deadline as a third argument, `expiresAt:`.

### Interrupt request design

- Include everything needed to decide. The human should not have to open another system.
- Keep it flat and serialisable — it becomes JSON, and it is persisted with the run.
- Include a stable reference to what is being decided (an ID), so a stale request can be detected.
- Set an expiry. An approval request that surfaces three weeks later may be answering a question that no longer applies, and `expiresAt` makes the timeout a branch in your node instead of a cleanup job.

### Key takeaways

- Extend `WaitForEventRequest` for anything beyond approve/reject; name the event it waits for.
- Override `metadata()`, not `jsonSerialize()`; there is no `fromArray()` — the answer comes back as a payload array.
- `ExecutionRequest::signal($name, $payload)` resumes only if the current request waits for that event.
- `awaitEvent()` and `sleepUntil()` pause on events and clocks; your scheduler calls `run(ExecutionRequest::resume())`.
- When the answer is usually "almost", make it editable.

## 15.4 Persisting, Detecting and Resuming

### Persistence is required

```php
// The workflow ID is the handle resume.php will need, and the framework never
// generates one: mint it here, before the run, and bind it.
$workflow = PublishWorkflow::make(workflowId: UniqueIdGenerator::generateId('workflow_'))
    ->setPersistence(new FilePersistence($storage));
```

By default a workflow uses `InMemoryPersistence`, which lives and dies with the PHP process. A run can pause and continue inside one script with it, but the moment the process ends the paused run is gone.

No durable persistence, no resumption across processes. This is the first thing to get right. You can set it at the call site as above, or return it from the workflow's `persistence()` hook so every instance of the class gets it.

The `make()` call binds the other thing a durable run needs: its workflow ID. The framework never generates one — `run()` on an unbound workflow throws a `WorkflowException` — and the process that resumes will need the same ID to find this run. `NeuronAI\UniqueIdGenerator` mints a unique one when there is no business key to use; "Workflow ID and run ID" below shows the alternative.

### Detecting the pause

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

Two things come off the state:

- **`getInterruptRequest()`** — what to show the human. It is `JsonSerializable`.
- **`getWorkflowId()`** — the continuation handle. Without it you cannot resume.

The framework has already persisted the run: its completed steps, its state, and the request itself. What *you* store is the workflow ID and whatever your UI needs, so your application can find the pending decision, present it, and reconnect the answer. The companion's `start.php` writes the request to a JSON file, which is exactly enough for a CLI:

```
  (generating the proposal - this line must print only once)
Suspended, awaiting a human decision.
  Workflow ID : workflow_01a101fc-07ff-7ad0-a884-fe89509bd2df
  Request     : {"interruptId":1,"type":"wait_for_event","eventName":"approval","expiresAt":null,...}
```

### Resuming

```php
$payload = [
    'delete_file' => $decision === 'approve'
        ? 'approve'
        : ['reject', 'Keep it until the audit closes.'],
];

$state = PublishWorkflow::make(workflowId: $workflowId)
    ->setPersistence(new FilePersistence($storage))
    ->run(ExecutionRequest::resume($payload));
```

Three requirements:

1. **The same workflow class** — the resumed process has to rebuild the identical graph, and a class is how you guarantee that.
2. **The same persistence layer** and **the same workflow ID.**
3. **The payload**, carrying the human's decision, wrapped in `ExecutionRequest::resume()` and passed to `run()`.

`ExecutionRequest::resume()` only builds an execution request, an immutable value from `NeuronAI\Workflow\Executor`; nothing is staged on the workflow, and `run()` is what executes it. Pass the same request to `events()` and the continuation streams, exactly like a fresh run (Section 14.4). The shorthand `submitInputs($payload)->run()` reads the pending run first, so it fails early when nothing is waiting, and it captures the fences of question 3 below; the agent's approval API (Section 15.5) is built on it.

Run `start.php` and `resume.php` from the companion repository as two separate commands. The proposal generated before the interrupt prints once, in the first process, and never in the second. Run `resume.php` a second time with the same ID and it fails with "No run in flight": a completed run cleans up after itself.

### Workflow ID and run ID

A run carries two identifiers, and only one of them is the handle.

**The workflow ID** names the partition in the store where the run's records live. It is the continuation handle: what you save, and what you bind with `make(workflowId: ...)` or `setWorkflowId()` before the run. Until a workflow is bound, `getWorkflowId()` is `null`.

**The run ID** (`getRunId()`) is a generation stamp inside that partition. It changes every time a fresh run starts under the same workflow ID, and it is used for fencing and observability — never for continuing.

A workflow can also declare its workflow ID as a business key by overriding `workflowId()`:

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
    ->run(ExecutionRequest::resume(['refund' => 'approve']));
```

Now there is nothing to store on the side: the order ID *is* the way back to the run. It also enforces a rule you would otherwise have to build — **one live run per workflow ID**. Calling `run()` while a run for that key is suspended throws `RunInFlightException`, whose message names what settles it and whose `interrupt` property carries the pending request. The Agent uses exactly this mechanism, with its thread ID as the workflow ID (Section 15.5).

### Persistence backends

```php
use NeuronAI\Workflow\Persistence\DatabasePersistence;

$persistence = new DatabasePersistence(new \PDO($dsn, $user, $password));   // table: workflow_store
```

**MySQL / MariaDB**, in strict SQL mode:

```sql
CREATE TABLE workflow_store (
    `partition` VARCHAR(510) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    `key`       VARCHAR(510) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    `value`     LONGTEXT CHARACTER SET ascii NOT NULL,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`partition`, `key`)
) ENGINE=InnoDB;
```

**PostgreSQL / SQLite:**

```sql
CREATE TABLE workflow_store (
    "partition" VARCHAR(510) NOT NULL,
    "key"       VARCHAR(510) NOT NULL,
    "value"     TEXT NOT NULL,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("partition", "key")
);
```

Read the schema carefully, because it tells you what is happening. One table, keyed by partition and key: every record of a run — its start event, its control record, each completed step, each memoized value, the suspended state — is a row in the partition named by its workflow ID. The values are opaque serialised strings; the table knows nothing about workflows. The sizes are not arbitrary, so copy the DDL as the library documents it: the backend stores both identifiers hex-encoded and the value base64-encoded, so a 255-byte identifier needs 510 characters; the ASCII collation keeps the composite primary key inside InnoDB's index limit; and `LONGTEXT` holds a state larger than the 64 KB of `TEXT`. On MySQL the connection must also be in strict SQL mode — the backend checks at the first write and throws a `PersistenceException` otherwise, because a silently truncated record cannot be resumed. `partition` and `key` are reserved words in MySQL, hence the backticks. And `updated_at` is there so you can find stale runs; add an index on it if you intend to query it.

The other backends store the same records:

- **`EloquentPersistence($modelClass)`** — an Eloquent model over a table of a different shape: a primary key of its own plus a unique constraint on `(partition, key)`. The `workflow_store` table that neuron-laravel 2.0.0 ships has the composite key above instead, and on it the first step commit fails. In a Laravel application use `DatabasePersistence` over the framework's own connection, `new DatabasePersistence(DB::connection()->getPdo())`; Chapter 18 does the wiring.
- **`RedisPersistence($redis, prefix: 'neuron:workflow:')`** — one hash per run, needs `ext-redis`. It sets no TTL: cleanup is the workflow's job, so configure eviction not to drop live runs.

Use `FilePersistence` for CLI and development — it is restart-durable but meant for a single process. Use the database, Eloquent or Redis backends for anything multi-worker or production; each of their writes is a conditional, atomic operation, which is what the next section relies on.

### The four operational questions

Nobody's tutorial covers these and every production system needs them.

**1. Who is notified?** The interrupt does not send an email. Your code does. Wire the notification where you detect `isInterrupted()`.

**2. What if nobody responds?** Give the request an `expiresAt` and schedule a job for that time that calls `run(ExecutionRequest::resume())`, with no payload. The workflow checks the deadline itself and the node takes its timeout branch — escalate, expire, or auto-reject is a decision in your node, not a cleanup script. For runs you simply want gone, `abandon()` discards a paused run and frees its workflow ID; called with no run ID it returns `false` when there was nothing to discard, and with one it throws instead (Section 22.4).

**3. How do you prevent double-resume?** Two managers open the same approval link and both click. The engine handles the race: every mutation is a conditional write against the run's control record, so only one continuation wins, an accepted answer cannot be replaced by a conflicting one, and a resume of a completed run fails with "No run in flight". What the engine cannot know is *which* request a delayed delivery was meant for. A queued job that may be retried should carry the run ID and execution attempt it observed on the paused state — `getRunId()` and `getExecutionAttempt()` — and pass them as fences:

```php
$state = $workflow->run(ExecutionRequest::resume(
    $payload,
    expectedRunId: $runId,
    expectedExecutionAttempt: $attempt,
));
```

If the run has moved on, the call is refused before it touches anything, and the fence that caught it decides the exception. A different run ID — a new generation, or a run that has already finished and been cleaned up — throws `StaleWorkflowRunException`. The same run on a later execution attempt — another worker already continued it, and it is running or paused again — throws a plain `WorkflowException` whose message begins "Stale continuation". A stale run ID means the run is gone: treat it as "already handled". A stale attempt only means the run has moved on, and a job that may be retried must not treat it as a no-op: Chapter 22's resume job reads the run before it decides (Section 22.3). Your UI should still mark the request resolved so the second manager sees "already decided" rather than an error.

**4. What about a deployment in between?** The persisted state is serialised PHP, and it contains your classes: the state object, the events, the interrupt request. A deployment that renames a class or changes a property will break deserialisation of in-flight runs. Either drain before deploying, or version your interrupt requests. The same applies to upgrading NeuronAI itself: runs suspended by an older version of the store format cannot be resumed by a newer one.

That last one is the sharp edge, and it is worth dwelling on. Long-lived serialised PHP objects across deployments is a known hard problem, and interruption puts you squarely in it. The mitigation — keep interrupt requests and state small, flat, and change them rarely — is a design rule, not something to discover during an incident.

### Key takeaways

- Durable persistence is mandatory for cross-process resumption; `FilePersistence` for CLI, a database, Eloquent or Redis backend for production.
- `run()` returns; check `isInterrupted()`, store `getWorkflowId()` and show `getInterruptRequest()`.
- Resume with the same class, persistence and workflow ID: `run(ExecutionRequest::resume($payload))`.
- The workflow ID is the handle, and you bind it before the run; the run ID is a generation stamp. Declare `workflowId()` to resume by business key.
- Four operational questions: notification, timeout (`expiresAt`), double-resume (conditional writes and fences), deployment compatibility.

## 15.5 Memoization, Conditional Interrupts and Middleware

### The re-execution problem

This section contains the most important correctness warning in the book.

When a workflow resumes, completed nodes are not run again — their results are replayed from the store. But **the node that was interrupted is re-executed from the top, including the code before the interruption.** That is how `interrupt()` gets to return the payload: execution has to reach it again.

Read that carefully, because it has real cost. If your node calls an LLM, then interrupts, then resumes — **the LLM call runs again.** You pay twice, you wait twice, and because of Section 1.5 you may get a *different answer* the second time.

Which means the human approved one thing and the workflow proceeds with another.

That is not waste. That is a correctness bug, and in a regulated context it is an audit failure. It has a one-line fix.

### memoize()

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): InputEvent|OutputEvent
    {
        // The result of this closure is persisted and returned when the node re-runs.
        $sentiment = $this->memoize('agent-1', fn (): SentimentResult => MyAgent::make()
            ->setThreadId($state->getWorkflowId() . ':sentiment')
            ->structured(new UserMessage($event->review), SentimentResult::class));

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

Two arguments:

- A **name**, unique within the node
- A **closure** wrapping the work whose result should be saved

First run: the closure executes and its result is written to the store as part of the current step. On re-execution — after an interrupt, or after a crash — the stored result is returned without running the closure again. The node reaches the interruption point with the same values as the previous run.

The companion's `ApprovalNode` makes this visible: its memoized closure prints a line, and across `start.php` and `resume.php` that line appears exactly once.

**The rule: any LLM call, any paid API call, and anything non-deterministic that precedes an `interrupt()` in the same node belongs inside a `memoize()`.** There are no exceptions worth learning. The closure itself must be a pure function of the node's event and state — `time()`, randomness and I/O go *inside* it, never around it.

One limit to keep in mind. `memoize()` saves a result once the closure has returned. If the process dies after an external side effect but before the result is saved — the email went out, the memo did not commit — the closure runs again. Where that matters, pass an idempotency key to the external system.

You will find `checkpoint()` in older material. It still exists, deprecated, and simply calls `memoize()`.

### The answer, and waiting more than once

The human's answer has one way into a node: the return value of `interrupt()`. There is no accessor to call at the top of the node and no "am I resuming?" test to write — the code after the call runs only once that wait has been answered. What comes back is the array the caller sent, `[]` for an empty answer; `null` means no answer arrived, because the request's `expiresAt` passed.

It follows that a node is not limited to one pause:

```php
class InterruptionNode extends Node
{
    public function __invoke(InputEvent $event, WorkflowState $state): InputEvent|OutputEvent
    {
        // First wait. Every later run of this node gets its recorded answer back.
        $support = $this->interrupt(
            new ApprovalRequest(
                message: 'Support lead: should we answer this review?',
                actions: [
                    new Action('review_id', 'Answer review', $state->get('review')),
                ],
            )
        );

        if (($support['review_id'] ?? null) !== 'approve') {
            $state->set('is_sufficient', false);

            return new InputEvent();
        }

        // Second wait, reached only once the first answer is an approval.
        $legal = $this->interrupt(
            new ApprovalRequest(
                message: 'Legal: is the reply safe to publish?',
                actions: [
                    new Action('review_id', 'Answer review', $state->get('review')),
                ],
            )
        );

        $state->set('is_sufficient', ($legal['review_id'] ?? null) === 'approve');

        return $state->get('is_sufficient') ? new OutputEvent() : new InputEvent();
    }
}
```

Each answer is recorded with the step. When the second answer arrives the node runs again from the top: the first `interrupt()` returns the support lead's recorded answer without pausing, and the new answer goes to the wait that asked for it. Write the waits in order, as if the node never paused.

One rule comes with this: **a node must reach its waits in the same order every time it runs.** The engine identifies a wait by its position in the node, so anything that decides whether a wait is reached — an `if`, a loop, an `interruptIf()` condition — may depend only on the event, the state, earlier answers or a memoized value, never on the clock or a live lookup. Break the rule with an `interruptIf()` condition and the resumed node fails with a `WorkflowException`. Break it with a plain `if` around an `interrupt()` and the positions shift: the answer is handed to the wrong question, with no error at all. And since the code between two waits runs again every time the node does, the `memoize()` rule above applies there too.

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

When the condition is false, `interruptIf()` returns `null` and execution continues straight through; `null` means "no human was asked". The callback form defers evaluation to the moment of the check. On resume the condition is not evaluated again at all — the node already paused there, so the payload is returned.

**The product argument for conditional interruption:** if every action needs approval, humans stop reading and start clicking. Interrupt only on the cases that warrant it — over a threshold, below a confidence score, outside normal parameters — and approvals stay meaningful.

### Tool approval on agents

The same idea applied to tool calls, without writing a node. An agent is a workflow, and its `ToolNode` checks every tool before running it: if the tool requires approval, the node interrupts with an `ApprovalRequest` carrying one `Action` per gated call.

Whether a tool requires approval is declared on the tool — Chapter 5 covers the declaration API. A tool can declare its own policy, conditional on its arguments; a string return counts as "yes" and is the reason shown to the approver:

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

Or the agent overrides it where it attaches the tool: `->requireApproval()`, `->suppressApproval()`, or `->withApprovalPolicy(fn (ToolInterface $tool) => ...)`.

Purchases under €100 proceed; larger ones wait for a human. This is Section 5.10's fourth layer, now concrete — and it is a far better product than either always-allow or always-block.

The round trip, across two requests:

```php
// Request 1: the model asks to buy a €240 ticket.
$agent = TicketAgent::make(workflowId: $threadId)
    ->setMessageStore(new SQLMessageStore($pdo))
    ->setPersistence(new DatabasePersistence($pdo));

$state = $agent->chat(new UserMessage('Buy the concert ticket'));

if ($state->isInterrupted()) {
    $pending = $agent->pendingApprovals();   // Action[]: id is the tool call ID
}

// Request 2: the human approved $callId. Same thread, same persistence.
$state = TicketAgent::make(workflowId: $threadId)
    ->setMessageStore(new SQLMessageStore($pdo))
    ->setPersistence(new DatabasePersistence($pdo))
    ->submitApprovalDecisions([$callId => 'approve'])
    ->run();
```

The **thread ID is the agent's workflow ID** — which is why it goes in as `workflowId:` — so the approval endpoint needs nothing but the thread to find the paused run. Decisions are keyed by tool call ID and take the same three forms as before: `'approve'`, `'reject'`, `['reject', 'reason']`. A tool runs only if explicitly approved; a partial set of decisions re-suspends until the rest arrive. A new `chat()` on the thread while a decision is pending is refused with `RunInFlightException` — lock the input in your UI until the decisions are in. A durable message store matters as much as durable persistence here: the pending tool call lives in the thread.

Chapter 22 builds this into a real Laravel approval screen.

### ToolSearchMiddleware

```php
$agent->addGlobalMiddleware(new ToolSearchMiddleware($toolPool));
```

For agents with large tool catalogues. Rather than sending every schema on every request — Section 1.3's compounding cost — it gives the model a `tool_search` tool and loads the matching tools from the pool on demand, five at most by default.

This is the answer to "what if I have 200 tools?", which is the natural question after Chapter 5.

Note the shape: `addGlobalMiddleware()`, not `addMiddleware(InferenceNode::class, ...)`. Section 2.3 attached `Summarization` to `InferenceNode`, the base of both the chat and structured-output nodes, and that is enough for a middleware that only edits what the model is sent. One that *contributes tools* has to run before every node: after an approval pause the run continues at `ToolNode`, which must find the tools the model was offered before the pause. Register this one on `InferenceNode` alone and the approved call fails with "The tool … is not registered on this agent".

### Key takeaways

- **A resumed node re-executes from the top** — including LLM calls, with possibly different results.
- `memoize('name', fn)` persists and replays; wrap everything expensive or non-deterministic before an interrupt.
- The answer is the return value of `interrupt()`; a node may wait more than once if it reaches its waits in the same order every time.
- `interruptIf()` keeps approvals meaningful and returns `null` when nobody was asked.
- Agent tool approval is declared on the tool and answered with `submitApprovalDecisions()->run()`; the thread is the handle. `ToolSearchMiddleware`, registered globally, handles large catalogues.
