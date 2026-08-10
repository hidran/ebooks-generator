# Chapter 15 — Human in the Loop

## 15.1 Interruption: The Feature, Not the Failure

### What it does

NeuronAI's interruption pattern lets a workflow **pause execution and wait for external input before resuming.**

Not "stop and start over". Pause — in the middle of a node — preserving everything, and resume from that exact point with the human's answer injected.

### The four phases

The documentation describes a request-response pattern:

1. **Request** — a node identifies something requiring human input and creates an `InterruptRequest`.
2. **Pause** — the workflow throws a `WorkflowInterrupt` exception, preserving the entire execution context.
3. **Decision** — your application presents the request to a human, who approves, rejects or edits.
4. **Resume** — the workflow continues from the same node, with the decision available.

> This design ensures a workflow can safely pause at any point, persist its state, and resume exactly where it left off, **even across different sessions.**

### Why "even across different sessions" is the whole story

Read that literally. The PHP process ends. The web request completes. The server is redeployed. Three days pass.

Then the manager clicks "approve" in an email, and the workflow continues from the middle of the node where it stopped, with all its context intact.

For a PHP audience this is genuinely notable, because PHP's execution model is famously request-scoped. The framework's answer is serialisation plus a persistence layer, and it turns "AI does the whole thing" into "AI does the work, a human makes the decisions" — which is the only shape most businesses will actually deploy for anything consequential.

### Interruption is an exception, deliberately

`WorkflowInterrupt` is thrown, not returned. That looks odd at first and the reasoning is worth stating.

It means interruption unwinds the stack from wherever it happens — arbitrarily deep inside a node, inside a helper, inside a middleware — without every intermediate layer needing to know about it or thread a return value back. Any node or middleware can interrupt, from anywhere.

The cost is that you must catch it. A `WorkflowInterrupt` escaping to your error handler looks like a crash and will be logged as one. Section 15.4 covers the handling.

### Where this changes what you can build

Section 5.10's four defence layers included "offered, gated at runtime". This is that layer, and it unlocks a category of application:

- Refunds above a threshold
- Emails sent to customers on the company's behalf
- Any deletion
- Publishing content
- Anything with a regulatory sign-off requirement

Without interruption, these are either fully automated (unacceptable) or not automated (no value). With it, the AI does the preparation and a human makes the call — which is both safe and useful.

### Key takeaways

- Pause mid-node, preserve everything, resume with human input.
- Four phases: request, pause, decision, resume.
- Survives process death and long delays — this is the distinguishing feature.
- Thrown as an exception so any depth can interrupt; you must catch it.

## 15.2 interrupt() and ApprovalRequest

### The built-in request

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

### Reading it

**`$this->interrupt($request)`** — the pause. Execution stops here on the first pass and continues here on resume, with the human's response as the return value.

**`ApprovalRequest`** — the built-in implementation, covering the most common case: approving actions such as tool calls.

**`Action`** — a single decidable item: an identifier, a label, and a description. Several actions in one request means the human decides several things in one interaction, which is the difference between one approval screen and five.

**`$humanResponse->getAction('delete_file')`** — retrieve the decision by identifier.

**`isApproved()` and `->feedback`** — approved or not, plus free-text the human added. That feedback field is more useful than it looks: a rejection with a reason can go straight into the next agent call as guidance, turning "no" into "no, because X" and letting the loop actually improve.

**Returning `InputEvent` on rejection** — this node loops back. Rejection is not failure; it is another iteration. That combination of interruption plus loop is the human-in-the-loop refinement pattern, and it is what Lab 10 builds.

::: {.callout .callout-warning}
[Syntax errors in the published examples]{.callout-title}

Several `ApprovalRequest` examples in the documentation are missing the comma after `message:`, and the `ContentReviewInterrupt` example in Section 15.3 is missing a semicolon after `parent::__construct($message)` and passes a positional argument after a named one. All three are copy-paste failures rather than API differences. Appendix A, items 34 to 36.
:::

### Design guidance for approval requests

**Write the message for the decider, not the developer.** They are seeing this in an email or an admin screen, with no context. `'Should I continue?'` is a poor message. `'Approve a €240 refund for order #4471 — customer reports item arrived damaged'` lets someone decide without opening another system.

**Include enough in the description to decide.** The third `Action` argument is where the substance goes.

**Group related decisions into one request.** Five actions in one request beats five sequential interruptions, each of which is a separate wake-up, notification and wait.

### Key takeaways

- `$this->interrupt($request)` pauses and later returns the human's response.
- `ApprovalRequest` plus `Action` covers approve/reject with feedback.
- `isApproved()` and `->feedback`; feedback can steer the next iteration.
- Write messages for the person deciding; group related decisions.

## 15.3 Custom Interrupt Requests

### Why approve/reject is not always enough

`ApprovalRequest` covers "should I do this action?". It does not cover "here is a draft — edit it before I save it", or "pick one of these three options", or "fill in the missing field".

The architecture is deliberately open: extend the abstract `InterruptRequest` to create custom interruption experiences.

### The implementation

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

Three responsibilities:

**Carry the data** the human needs to decide, plus whatever they will edit.

**`jsonSerialize()`** — so it can be stored and sent to a frontend. Note the implication: your interruption crosses a JSON boundary. Keep it serialisable and flat.

**`fromArray()`** — reconstruct it from the edited data on the way back.

That round trip — PHP object → JSON → UI → edited JSON → PHP object — is the whole lifecycle, and knowing it is where your frontend fits.

### Using it

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

### The pattern worth naming

The agent generated content. The human **edited** it. The workflow saved the **edited** version.

That is not approval — it is collaboration. The AI produces a draft, the human corrects it, the system uses the corrected version. For content generation, document drafting, code suggestions and data extraction, this is a better product than approve/reject, because the common case is "nearly right" rather than "yes or no".

As a design principle: **when the likely human response is "almost, but change this", build an editable interrupt rather than an approval.**

::: {.callout .callout-warning}
[This example generates content before interrupting]{.callout-title}

Which is exactly the situation Section 15.5 is about. As written, resuming this node re-runs `ContentCreatorAgent` and the human's edit is applied to a *different* draft. Read Section 15.5 before you ship anything shaped like this.
:::

### Interrupt request design

- Include everything needed to decide. The human should not have to open another system.
- Keep it flat and serialisable — it becomes JSON.
- Include a stable reference to what is being decided (an ID), so a stale request can be detected.
- Consider expiry. An approval request that surfaces three weeks later may be answering a question that no longer applies.

### Key takeaways

- Extend `InterruptRequest` for anything beyond approve/reject.
- `jsonSerialize()` out, `fromArray()` back — the request crosses a JSON boundary.
- The edited request is what the node receives, enabling collaboration rather than gating.
- When the answer is usually "almost", make it editable.

## 15.4 Catching, Persisting and Resuming

### Persistence is required

```php
$workflow = new WorkflowAgent(new FilePersistence(__DIR__));
```

> To be able to interrupt and resume a Workflow (also Agent and RAG) you need to provide the persistence layer when creating the Workflow instance.

No persistence, no resumption. This is the first thing to get right.

### Catching the interrupt

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

Two things come out of the exception:

- **`getRequest()`** — what to show the human.
- **`getWorkflowId()`** — the resume token. Without it you cannot resume.

The framework has already persisted the execution state. What *you* store is the request and the token, so your application can find the pending decision, present it, and reconnect the answer.

### Resuming

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

Three requirements:

1. **The same persistence layer.**
2. **The same workflow ID.**
3. **The reconstructed request**, carrying the human's decision, passed to `init()`.

### Database persistence

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

Read the schema carefully, because it tells you what is happening: `LONGBLOB` / `BYTEA` — the entire serialised execution state, as binary. And `idx_updated_at` exists so you can find stale interrupts, which is your cleanup story.

Use `FilePersistence` for CLI and development. Use `DatabasePersistence` for anything multi-server or production.

### The four operational questions

Nobody's tutorial covers these and every production system needs them.

**1. Who is notified?** The interrupt does not send an email. Your code does. Wire the notification in the catch block.

**2. What if nobody responds?** Interrupts accumulate. You need a timeout policy: escalate, expire, or auto-reject. `idx_updated_at` is there for this query.

**3. How do you prevent double-resume?** Two managers open the same approval link and both click. Mark the request resolved atomically before resuming.

**4. What about a deployment in between?** The serialised state contains your classes. A deployment that renames a class or changes a property will break deserialisation of in-flight interrupts. Either drain before deploying, or version your interrupt requests.

That last one is the sharp edge, and it is worth dwelling on. Long-lived serialised PHP objects across deployments is a known hard problem, and interruption puts you squarely in it. The mitigation — keep interrupt requests small, flat, and change them rarely — is a design rule, not something to discover during an incident.

### Key takeaways

- Persistence is mandatory for interruption; `FilePersistence` for CLI, `DatabasePersistence` for production.
- Catch `WorkflowInterrupt`; store `getRequest()` and `getWorkflowId()`.
- Resume with the same persistence, the same ID, and the reconstructed request.
- Four operational questions: notification, timeout, double-resume, deployment compatibility.

## 15.5 Checkpoints, Conditional Interrupts and Middleware

### The re-execution problem

This section contains the most important correctness warning in the book.

> When the Workflow is resumed it restarts execution **from the node where it was interrupted. The node will be re-executed entirely, including the code before the interruption.**

Read that carefully, because it has real cost. If your node calls an LLM, then interrupts, then resumes — **the LLM call runs again.** You pay twice, you wait twice, and because of Section 1.5 you may get a *different answer* the second time.

Which means the human approved one thing and the workflow proceeds with another.

That is not waste. That is a correctness bug, and in a regulated context it is an audit failure. It has a one-line fix.

### Checkpoints

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

Two arguments:

- A **name**, unique within the node
- A **closure** wrapping the work whose result should be saved

First run: the closure executes and its result is stored. After resume: the stored result is returned without re-executing.

The documentation's phrasing is precise — the node reaches the interruption point *with the exact same state as the previous run*.

**The rule: any LLM call, any paid API call, and anything non-deterministic that precedes an `interrupt()` in the same node belongs inside a `checkpoint()`.** There are no exceptions worth learning.

### consumeResumeRequest()

Sometimes you want to branch at the *top* of a node based on whether you are resuming:

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

Returns the feedback, or `null` if the node is running normally rather than waking. It lets you handle the resume case explicitly at the top instead of re-walking the whole node body — a cleaner shape when the node does substantial work before the interrupt.

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

The callback form matters: it defers evaluation, and it avoids constructing the request when the condition is false.

**The product argument for conditional interruption:** if every action needs approval, humans stop reading and start clicking. Interrupt only on the cases that warrant it — over a threshold, below a confidence score, outside normal parameters — and approvals stay meaningful.

### ToolApproval middleware

The same idea applied to tool calls, without writing a node:

```php
Neuron::middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Delete the oldest log file'));
```

Conditional on the arguments:

```php
new ToolApproval(
    tools: [
        BuyTicketTool::class => function (array $args): bool {
            return $args['amount'] > 100;
        }
    ]
)
```

Purchases under €100 proceed; larger ones wait for a human. This is Section 5.10's fourth layer, now concrete — and it is a far better product than either always-allow or always-block.

Note the shape: `middleware(ToolNode::class, ...)`. Section 2.3 said node names are public API. This is why.

### ToolSearchMiddleware

```php
new ToolSearchMiddleware([...])
```

For agents with large tool catalogues. Rather than sending every schema on every request — Section 1.3's compounding cost — it selects relevant tools dynamically.

This is the answer to "what if I have 200 tools?", which is the natural question after Chapter 5.

### Key takeaways

- **A resumed node re-executes from the top** — including LLM calls, with possibly different results.
- `checkpoint('name', fn)` saves and replays; wrap everything expensive or non-deterministic before an interrupt.
- `consumeResumeRequest()` branches on whether you are waking.
- `interruptIf()` keeps approvals meaningful; the callback form defers evaluation.
- `ToolApproval` gates tool calls conditionally on arguments; `ToolSearchMiddleware` handles large catalogues.
