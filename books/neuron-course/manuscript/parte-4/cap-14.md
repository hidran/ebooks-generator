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

`FirstEvent|SecondEvent`. The union is not decoration. PHP enforces it: return an event that is not in the signature and the node dies with a `TypeError` — `Return value must be of type FirstEvent, SecondEvent returned` — on the one path that returns it, which is usually the rare branch nobody exercised in testing.

The tempting fix is to widen the return type to plain `Event`. It runs, and it costs you the thing Chapter 13 was about: the signature no longer says where the flow can go, so neither can a reader, nor `export()`, which draws the graph from those same return types.

This is the number one workflow bug, and the cause is always the same: a union type someone forgot to widen after adding a branch.

### Loop to anywhere

> You can create a loop from any node to any other node by defining the appropriate input and return events. A node can even return a `StartEvent` to jump right to the first node of the workflow.

Returning `StartEvent` restarts the flow from the top — within the same run, so state keeps everything written so far. The companion's `run/loop.php` is built on exactly this: the reviewer returns `StartEvent` on a rejection, and the writer node that consumes it reads the reviewer's feedback from state and produces the next draft.

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

        $verdict = $this->memoize('verdict', fn (): Verdict => ReviewerAgent::make()
            ->structured(new UserMessage($event->draft), Verdict::class));

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

Three things this demonstrates beyond the counter:

**Each iteration is its own durable step.** The engine numbers steps as it traverses, so the third pass through `ReviewNode` is a different step from the first, with the counter in state committed alongside it. A run that crashes on the third review and is recovered replays the first two from the store and resumes on the third — and the `memoize()` around the reviewer call (Section 13.5) is scoped to that iteration, so the verdict already paid for on a given pass is never requested twice.

**Every loop iteration costs LLM calls.** This is Section 1.4 again. An unbounded review loop is an unbounded bill.

**Have a plan for hitting the limit.** Escalating to a human beats silently shipping the third draft. That is the natural bridge into Chapter 15.

### Loops are where agentic systems earn their keep

A loop with an LLM in it is *iterative refinement*: draft, critique, revise, repeat until good enough. That pattern — writer plus critic — is one of the highest-value multi-agent shapes, and it is a three-node workflow with one union return type.

### Key takeaways

- A loop is a node returning an event that re-triggers an earlier node.
- **Declare every possible return type in the union** — the most common workflow bug.
- Returning `StartEvent` restarts the whole workflow.
- The framework does not bound loops; count in state and plan for the limit.
- Every iteration is a separate durable step; memoize the LLM call inside it.

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

Conditional branching picks one path. Parallel branching forks into several, each running to its own end, and joins the results.

The fork returns a `ParallelEvent`. Give it a subclass of its own, because the join node is routed by that class — the same one-event-one-node rule as everywhere else — and a named subclass lets one workflow contain more than one fork:

```php
use NeuronAI\Workflow\Events\ParallelEvent;

class DocumentProcessingStarted extends ParallelEvent
{
}

class DocumentProcessing extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): DocumentProcessingStarted
    {
        return new DocumentProcessingStarted([
            'text'  => new TextProcessEvent(),
            'image' => new ImageProcessEvent(),
        ]);
    }
}
```

Each branch is a **named key** mapping to the first event of that branch. The names are required: a plain list is rejected, because the name becomes the branch's identity. The nodes that handle those events, and everything downstream in each branch, register in the workflow normally:

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

Once all branches complete, the same `DocumentProcessingStarted` instance, now holding every branch's result, is routed to the node that accepts it. That node is the merge point, and it reads each result by name:

```php
class MergeNode extends Node
{
    public function __invoke(DocumentProcessingStarted $event, WorkflowState $state): StopEvent
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

### Parallel is not concurrent until you say so

The default executor runs the branches **one after another**. The isolation, the named results and the merge all work, but the elapsed time is the sum of the branches. For real concurrency, swap the executor:

```php
use NeuronAI\Workflow\Executor\AsyncExecutor;

$state = MyWorkflow::make()
    ->setExecutor(new AsyncExecutor())
    ->run();
```

`AsyncExecutor` runs each branch in an Amp fiber and needs `amphp/amp` installed — NeuronAI does not require it, and without it the fork fails with `Call to undefined function Amp\async()`. The fibers only overlap while one of them is waiting on I/O, so for branches that call a model, the provider also needs the non-blocking `AmpHttpClient` (from `amphp/http-client`) set with `setHttpClient()`. With both, two model calls complete in the time of the slower one. With only the executor, they still queue behind each other.

Branch steps are durable like any other: each node inside each branch is committed as its own step, so a recovered run does not redo the branches that already finished. What happens when a branch pauses for a human is Chapter 15's business; the short version is that branches pause one at a time.

::: {.callout .callout-tip}
[In practice]{.callout-title}

Reproduce this deliberately once — set state in a branch, read it in the merge node, watch it be absent — then fix it with the result. Five minutes, and the rule sticks in a way that reading it does not.
:::

### When parallel branches pay off

Same shape as Section 5.13: **independent, I/O-bound work**, running on `AsyncExecutor`. Three agents analysing the same document from different angles. Two API calls that do not depend on each other. Text and image processing of one upload.

Not useful for: sequential dependencies, or trivially fast work where coordination costs more than it saves.

### Key takeaways

- Conditional branching is a union return type; converge by returning a shared event type.
- A `ParallelEvent` subclass with named branches forks; the node accepting that subclass joins.
- Branches end with `StopEvent(result: ...)`; the merge node reads `getResult('name')`.
- Branches run sequentially by default; `AsyncExecutor` plus `amphp/amp` (and `AmpHttpClient` for providers) makes them concurrent.
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

A string-keyed bag with `set()` and `get()`. Fine for small workflows and prototypes. You can seed it before the run, too: `Workflow::make(state: new WorkflowState(['topic' => $topic]))`.

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

The second parameter of `__invoke()` may be any subclass of `WorkflowState`; the workflow checks it when it validates the node.

Then inject it. The `Workflow` constructor is `(?string $workflowId, ?WorkflowState $state)`, so for a one-off workflow pass it by name:

```php
$state = Workflow::make(state: (new CustomState())->setUser($user))
    ->addNodes([
        new ExampleNode(),
    ])
    ->run();
```

For a workflow class, return it from the `state()` hook instead, and tell static analysis which state the workflow carries:

```php
/** @extends Workflow<CustomState> */
class ExampleWorkflow extends Workflow
{
    protected function state(): CustomState
    {
        return new CustomState();
    }

    protected function nodes(): array
    {
        return [
            new ExampleNode(),
        ];
    }
}

$state = ExampleWorkflow::make()->run(); // PHPStan infers CustomState
```

The `@extends` annotation is what makes `run()`'s return type `CustomState` rather than `WorkflowState` for PHPStan and your IDE — the same mechanism `Agent` uses to return an `AgentState`. Material written for earlier versions injects state as a third constructor argument, after persistence and a resume token; in v4 that call fails. Appendix A, item 37.

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

Critical for everything durable, and worth knowing now so it is not a surprise:

**State is serialised every time a step commits.** Not only when a workflow pauses — after every node, on every run, including a plain in-memory one, because that is what a durable step is (Section 13.5). Which means:

- **Resources cannot be serialised.** Database connections, file handles, open sockets. Store an identifier and re-establish the connection inside the node that needs it.
- Same for closures and anything holding a resource or a closure indirectly.

Put a `PDO` in state and the run fails the moment the node that stored it returns: `Serialization of 'PDO' is not allowed`. That is the good news — it fails early, next to the line that caused it, instead of hours later at a pause boundary.

**Store IDs, not objects with connections.** `protected int $userId` rather than a hydrated model carrying a live connection. If a state object genuinely needs a live dependency, the workflow's `restoreState()` hook is where you reattach it to state read back from the store.

**Parallel branches clone the state.** The `data` bag behind `get()`/`set()` is deep-copied for each branch. A subclass holding mutable *objects* in its own properties must define `__clone()` so the copies really are independent; plain scalars and arrays, like `ContentWorkflowState`'s revisions, need nothing.

### Key takeaways

- `WorkflowState` is a string-keyed bag: fine small, weak at scale.
- `CustomState` gives typed accessors, discoverability and a home for derived logic.
- Inject with `Workflow::make(state: ...)`, or the `state()` hook plus `@extends Workflow<CustomState>`.
- **State is serialised at every step commit** — no resources, no connections, no closures.
- Store IDs and re-hydrate inside the node.

## 14.4 Streaming a Workflow

### One keyword

Add `\Generator` to the return type and `yield`:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\WorkflowState;

class ProgressEvent
{
    public function __construct(public readonly string $message){}
}

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

Note that `ProgressEvent` does not implement `Event`. It never routes anything; a node may yield any object at all. Only the returned value has to be an `Event`.

The union `\Generator|FirstEvent` is the framework's documented form, and it earns its place: PHP accepts it, and `export()` reads the `FirstEvent` half to draw the edge. PHPStan does not accept it — a function that yields may only declare generator types, so it reports `generator.returnType` on every `yield`. If your codebase runs PHPStan, declare `\Generator` alone and move the routing into the docblock, `@return \Generator<int, ProgressEvent, mixed, FirstEvent>`. The workflow runs identically; the price is that `export()` no longer sees where the node leads and shows the next node as orphaned.

To receive the stream, call `events()` instead of `run()`. It returns a generator of everything the nodes yield, and the final state is the generator's return value:

```php
$stream = Workflow::make()
    ->addNodes([
        new InitialNode(),
        new NodeOne(),
        new NodeTwo(),
    ])
    ->events();

foreach ($stream as $item) {
    if ($item instanceof ProgressEvent) {
        echo $item->message . "\n";
    }
}

$state = $stream->getReturn();
```

### Progress is not durable

Yielded output is live and ephemeral. It is not written to the store, and when a recovered run replays completed steps (Section 13.5), those steps' progress events are **not** emitted again — only the returned event is durable. A client that reconnects halfway through has missed what it missed.

So never make correctness depend on a progress event arriving. Anything the application must know goes in state or in the result; progress is for the human watching.

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

**Name progress events for the user, not the developer.** `"Searching the knowledge base"` beats `"RetrievalNode invoked"`. Same principle as the tool-label allowlist in Section 7.4 — and the same security concern: do not leak internals.

**Do not yield every detail.** A progress line per document retrieved is noise. One per meaningful phase.

**Yield before slow work, not after.** `yield new ProgressEvent("Researching...")` then do the research. Yielding afterwards tells the user what already finished, which is the wrong half of the information.

### Connecting to the frontend

The stream adapters from Section 7.5 apply here. `setStreamAdapter()` with `AGUIAdapter` or `VercelAIAdapter` turns a workflow's output into protocol events for a browser. An adapter only encodes what it understands: yield NeuronAI's portable stream events (`StepStartedStreamEvent`, `ActivityStreamEvent` and friends, in `NeuronAI\Agent\Adapters\Events`) directly, or keep your own `ProgressEvent` and register a translation with the adapter's `mapEvent()`. Add a channel with `setChannel()` — `PusherChannel`, `RedisChannel` — and a **queued** workflow streams to a client it has no direct connection to.

That is the combination Chapter 21 builds: long workflow on a worker, live progress in the browser.

### Key takeaways

- Add `\Generator` to the return type; `yield` progress, `return` the routing event.
- Two channels from one method; consume them with `events()` and `getReturn()`.
- Progress is ephemeral: never stored, never replayed.
- Name progress events for users; one per phase; yield before the work.
- Adapters and channels carry workflow progress to the frontend, including from queued jobs.
