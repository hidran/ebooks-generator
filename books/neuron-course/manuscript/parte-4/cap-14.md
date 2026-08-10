# Chapter 14 — Loops, Branches and State

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch14`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch14), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

## 14.1 Loops

### A loop is a return type

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

The node consumes `FirstEvent` and can also *return* `FirstEvent`. Returning it triggers itself again.

Output:

```
- Handling StartEvent
- InitialNode complete
- Running a loop on NodeOne
- Running a loop on NodeOne
- NodeOne complete, move forward
- NodeTwo complete
```

### The rule you must not forget

> You have to declare **all possible return events** on the method signature to let the Workflow build the execution chain.

`FirstEvent|SecondEvent`. If you return an event type that is not in the signature, the workflow cannot resolve the next node.

This is the number one workflow bug. It fails at runtime with a confusing message, and the cause is a union type someone forgot to widen after adding a branch.

### Loop to anywhere

> You can create a loop from any node to any other node by defining the appropriate input and return events. A node can even return a `StartEvent` to jump right to the first node of the workflow.

Returning `StartEvent` restarts the whole flow — full retry from the top.

### The guard you must write yourself

The framework will not stop an infinite loop. If your condition never becomes false, the workflow runs forever.

Use state as a counter:

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

Two things this demonstrates beyond the counter:

**Every loop iteration costs LLM calls.** This is Section 1.4 again. An unbounded review loop is an unbounded bill.

**Have a plan for hitting the limit.** Escalating to a human beats silently shipping the third draft. That is the natural bridge into Chapter 15.

### Loops are where agentic systems earn their keep

A loop with an LLM in it is *iterative refinement*: draft, critique, revise, repeat until good enough. That pattern — writer plus critic — is one of the highest-value multi-agent shapes, and it is a three-node workflow with one union return type.

### Key takeaways

- A loop is a node returning an event that re-triggers an earlier node.
- **Declare every possible return type in the union** — the most common workflow bug.
- Returning `StartEvent` restarts the whole workflow.
- The framework does not bound loops; count in state and plan for the limit.

## 14.2 Branches, Sequential and Parallel

### Conditional branching

Same mechanism as a loop — a union return type, but the alternatives lead to different nodes:

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

Each branch then proceeds through its own nodes and eventually reaches `StopEvent`, or converges back onto a shared event type.

**A convergence trick worth knowing:** to rejoin two branches, have the last node of each return the *same* event type. Whichever branch ran, the same downstream node picks it up. That is how you build diamond shapes without any join syntax.

::: {.callout .callout-warning}
[Do not copy the class name from the docs]{.callout-title}

The documentation's branching example names the class `BrancheA1Event` — a stray `e`. Appendix A, item 33.
:::

### Parallel branches

Sequential branching picks one path. Parallel branching runs several **concurrently**.

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

Each branch is a **named key** mapping to the first event of that branch. The nodes that handle those events, and everything downstream in each branch, register in the workflow normally:

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

### Returning results from a branch

Each branch ends when its last node returns a `StopEvent`, and **the `StopEvent` carries the result**:

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

Once all branches complete, the `ParallelEvent` is forwarded to the merge point, which reads each result by name:

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

### The isolation rule — the important part

> Each branch gets an **isolated copy** of the workflow state. Branches start from the same snapshot, but mutations inside a branch do not propagate to sibling branches or to the main workflow. **The only way to pass data back is through the `StopEvent` result.**

This is intentional, and the reasoning is sound: with shared mutable state across concurrent branches you get a race, and then a "who wrote this value?" debugging session that nobody enjoys.

The practical consequence, and it is the thing everyone trips over: **a branch writing to `$state` is writing to a copy that will be discarded.** If you want data out of a branch, it goes in the `StopEvent` result. Full stop.

::: {.callout .callout-tip}
[In practice]{.callout-title}

Reproduce this deliberately once — set state in a branch, read it in the merge node, watch it be absent — then fix it with the result. Five minutes, and the rule sticks in a way that reading it does not.
:::

### When parallel branches pay off

Same shape as Section 5.13: **independent, I/O-bound work**. Three agents analysing the same document from different angles. Two API calls that do not depend on each other. Text and image processing of one upload.

Not useful for: sequential dependencies, or trivially fast work where coordination costs more than it saves.

### Key takeaways

- Conditional branching is a union return type; converge by returning a shared event type.
- `ParallelEvent(['name' => $event, ...])` runs branches concurrently.
- Branches end with `StopEvent(result: ...)`; the merge node reads `getResult('name')`.
- **Branch state is an isolated copy** — mutations are discarded; return data via the result.

## 14.3 Managing State

### The default

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
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

A string-keyed bag with `set()` and `get()`. Fine for small workflows and prototypes.

### Its weaknesses, stated plainly

- **Typos are silent.** `$state->get('user_id')` versus `$state->set('userId', ...)` returns null with no complaint.
- **No types.** Everything is `mixed`; static analysis sees nothing.
- **No discoverability.** Nothing tells a new developer what keys exist. You grep.

For a three-node workflow, acceptable. For a system a team maintains, not.

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

Nodes accept it in place of `WorkflowState`:

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

Then inject it when constructing the workflow. Confirm the injection signature in your version — this is one of the places where the v2/v3 constructor drift shows. Appendix A, item 37.

### Why this is the right default for real work

**Typed accessors.** `getUser(): User` — IDE completion, PHPStan coverage, refactoring support.

**Self-documenting.** The class *is* the list of what this workflow carries. Onboarding becomes "read `OrderWorkflowState`".

**A place for logic.** Derived values belong on the state object, not repeated in four nodes:

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

Now the loop guard from Section 14.1 reads as `$state->hasReachedLimit()` in every node that needs it, defined once.

### The serialisation constraint

Critical for Chapter 15, and worth knowing now so it is not a surprise:

**State is serialised when a workflow is interrupted.** Which means:

- **Resources cannot be serialised.** Database connections, file handles, open sockets. Store an identifier and re-establish the connection when the node resumes.
- Same for closures and anything holding a resource indirectly.

The framework's own guidance is explicit on this. A `CustomState` holding a `PDO` will fail at the interruption boundary — and it will fail there, not where you wrote it, which makes it an unpleasant bug to trace.

**Store IDs, not objects with connections.** `protected int $userId` rather than a hydrated model carrying a live connection.

### Key takeaways

- `WorkflowState` is a string-keyed bag: fine small, weak at scale.
- `CustomState` gives typed accessors, discoverability and a home for derived logic.
- **State is serialised on interruption** — no resources, no connections, no closures.
- Store IDs and re-hydrate inside the node.

## 14.4 Streaming a Workflow

### One keyword

Add `\Generator` to the return type and `yield`:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;

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

> To stream events from a node you need to add `\Generator` as an additional return type on `__invoke`.

**`yield` emits progress. `return` emits the routing event.** Two channels from one method — that is the whole design, and it is PHP generators used exactly as intended.

### Why this is a genuinely strong feature

Compare the two user experiences for a workflow that takes 45 seconds.

**Without streaming:**

```
[spinner] ......................................... done
```

**With streaming:**

```
Researching the topic...
  Found 12 sources
Drafting the article...
  Draft complete: 1,240 words
Reviewing...
  Revision requested: add a counter-argument
Revising...
Done.
```

The second is not a nicer spinner. It is a different product. The user knows the system is working on the right problem, understands why it is slow, and can abandon early if it has gone wrong.

For multi-agent systems this matters even more, because the runs are longer. Section 1.4 said latency compounds; this is how you make compounded latency tolerable.

### Design guidance

**Name progress events for the user, not the developer.** `"Searching the knowledge base"` beats `"RetrieveDocumentsNode invoked"`. Same principle as the tool-label allowlist in Section 7.4 — and the same security concern: do not leak internals.

**Do not yield every detail.** A progress line per document retrieved is noise. One per meaningful phase.

**Yield before slow work, not after.** `yield new ProgressEvent("Researching...")` then do the research. Yielding afterwards tells the user what already finished, which is the wrong half of the information.

### Connecting to the frontend

The stream adapters from Section 7.5 apply here. A workflow's progress events go through `AGUIAdapter` or `VercelAIAdapter` to a browser, and — as noted there — an adapter pushing to a transport like Pusher lets a **queued** workflow stream to a client it has no direct connection to.

That is the combination Chapter 21 builds: long workflow on a worker, live progress in the browser.

### Key takeaways

- Add `\Generator` to the return type; `yield` progress, `return` the routing event.
- Two channels from one method.
- Name progress events for users; one per phase; yield before the work.
- Adapters carry workflow progress to the frontend, including from queued jobs.
