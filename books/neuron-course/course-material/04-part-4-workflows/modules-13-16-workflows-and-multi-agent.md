# Agentic AI in PHP with Neuron
## PART IV — WORKFLOWS AND MULTI-AGENT SYSTEMS
### Full lesson scripts — Modules 13, 14, 15 and 16

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^3.0, PHP 8.3.

---

> ## ⚠ API DRIFT WARNING FOR THIS PART
>
> The workflow documentation contains **two different execution APIs** across its own pages:
>
> ```php
> // v3 style — Multi Step Workflow page
> $handler = Workflow::make()->addNodes([...])->init();
> $handler->run();
>
> // v2 style — Loops & Branches page, and most blog posts
> $state = Workflow::make()->addNodes([...])->start()->getResult();
> ```
>
> The v2 style also shows `Workflow::make(new WorkflowState(), $persistence, 'id')` and an
> `Edge` class that **no longer exists in v3** — the event-driven model replaced it entirely.
>
> **Before recording Part IV**, run one minimal workflow against your installed version and
> settle: `init()`/`run()` vs `start()`/`getResult()`, and the `Workflow` constructor signature.
> The lessons below use the v3 `init()`/`run()` form. Every blog post you find will use the other one.

---
═══════════════════════════════════════════════════════════════
# MODULE 13 — THE EVENT-DRIVEN MODEL
═══════════════════════════════════════════════════════════════
---

## LESSON 13.1 — What a Workflow Is

**Duration:** 11 minutes
**Type:** Theory

### Learning objectives

Understand the workflow abstraction and why it is the framework's foundation rather than an advanced extra.

### The definition

A workflow is an event-driven, node-based way to control the execution flow of an application.

Your application is divided into **Nodes**, which are triggered by **Events**, and which themselves return Events that trigger further nodes. Combine them and you can express arbitrarily complex flows.

The documentation offers a comparison worth using: **"It's like n8n at code level."** For an audience that has seen a visual automation tool, that lands immediately — boxes connected by arrows, except the boxes are PHP classes and the arrows are types.

### A node can be anything

From a single line of code to a complete agent. Arbitrary inputs and outputs, passed around by events.

That flexibility is the point. A node might:

- Call an LLM
- Query your database
- Run a RAG retrieval
- Send an email
- Wait for a human
- Be an entire `Agent` doing its own tool-calling loop

### The statement from Lesson 2.3, in the source

> Agent and RAG classes are workflows themselves. They represent ready-to-use implementations of the most common patterns for tool calls, retrieval and structured output. Workflow allows you to program your agentic system completely from scratch. Agent and RAG can be used inside a Workflow to complete tasks as any other component.

This is why Module 2 insisted on it. Part IV is not a new topic — it is the layer that was underneath Parts II and III all along.

### What makes Neuron's workflow distinctive

The documentation names two capabilities:

**Streaming** — a multi-agent system can push updates to clients as it runs.

**Interruption** — the workflow can pause mid-process, ask for human input, wait, and continue exactly where it left off — even hours or days later.

The second one is unusual. Most workflow engines can pause; few can pause *inside* a node, serialise the whole execution context, survive a process restart, and resume with human feedback injected at the exact point it stopped. That is Module 15, and it is the strongest single argument for the framework.

### Key takeaways

- Nodes triggered by events, returning events that trigger further nodes.
- A node is anything from one line to a whole agent.
- Agent and RAG *are* workflows; this is the substrate, not an add-on.
- Streaming and interruption are the distinguishing capabilities.

---
═══════════════════════════════════════════════════════════════

## LESSON 13.2 — Node, Event, State

**Duration:** 12 minutes
**Type:** Theory with code

### Learning objectives

Know the three primitives and the one idea that makes the model click.

### Event

A plain PHP class implementing `Event`. It can have any name and any properties.

```php
namespace App\Neuron;

class FirstEvent implements Event
{
    public function __construct(protected string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(protected string $secondMsg){}
}
```

Generate them:

```bash
vendor/bin/neuron make:event App\\Neuron\\FirstEvent
```

Two special events ship with the framework:

- **`StartEvent`** — what the workflow begins with
- **`StopEvent`** — what ends it

### Node

A class extending `Node` with one method:

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\WorkflowState;

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
    {
        echo "\n- Handling StartEvent";

        return new FirstEvent("InitialNode complete");
    }
}
```

```bash
vendor/bin/neuron make:node App\\Neuron\\InitialNode
```

### The idea that makes it click

**The method signature is the graph.**

```php
public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
```

Read it as a wiring statement: *this node runs when a `StartEvent` appears, and when it finishes it emits a `FirstEvent`.*

There is no separate edge definition, no configuration file, no `addEdge()` call. **The type hints are the wiring.**

Say this on camera and let it sit. Everything else in Part IV follows from it:

- Want a loop? Return the event that triggers an earlier node.
- Want a branch? Declare a union return type.
- Want to know the graph? Read the signatures.

> **Historical note worth mentioning.** Version 1 had an explicit `Edge` class and `addEdges()`. V2 removed it in favour of the event model. If you find a tutorial using `new Edge(NodeA::class, NodeB::class)`, it predates the current architecture by two major versions.

### State

`WorkflowState` is the shared bag that travels through the run:

```php
class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): StopEvent
    {
        $state->set('message', 'Hello World!');

        return new StopEvent();
    }
}
```

`set()` and `get()`. Available to every node.

### Events vs state: when to use which

A distinction students consistently get wrong, so make it explicit:

**Events carry the message.** What this specific step produced, passed to the next specific step. Ephemeral, directional, typed.

**State carries the context.** Things many nodes need: the user, the tenant, accumulated results, configuration. Persistent across the whole run.

The heuristic: **if only the next node needs it, put it in the event. If several nodes need it, or you need it after the run, put it in state.**

Overusing state produces a workflow where every node reads and writes a global bag — which is a workflow in name only, because the data flow is invisible again. Overusing events produces enormous event classes that pass everything along. Both extremes are worse than the balance.

### Key takeaways

- Event = plain class implementing `Event`; `StartEvent` and `StopEvent` are built in.
- Node = class with `__invoke(Event, WorkflowState): Event`.
- **The method signature is the graph** — no edges to declare.
- Events for the message between two steps; state for shared context.

---
═══════════════════════════════════════════════════════════════

## LESSON 13.3 — A Single-Step Workflow

**Duration:** 9 minutes
**Type:** Hands-on

### Learning objectives

Run the smallest possible workflow and understand its lifecycle.

### The whole thing

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\StopEvent;
use NeuronAI\Workflow\WorkflowState;

class InitialNode extends Node
{
    public function __invoke(StartEvent $event, WorkflowState $state): StopEvent
    {
        $state->set('answer', 'Hello World!');

        return new StopEvent();
    }
}
```

```php
use NeuronAI\Workflow\Workflow;

$handler = Workflow::make()
    ->addNodes([
        new InitialNode(),
    ])
    ->init();

$handler->run();
```

`StartEvent` in, `StopEvent` out. One node.

### The lifecycle

1. `Workflow::make()` builds the workflow.
2. `addNodes()` registers the nodes. **Order in the array is not execution order** — the events decide that. The array is a registry, not a sequence.
3. `init()` prepares the run and returns a handler.
4. `run()` executes: emit `StartEvent`, find the node whose signature accepts it, run it, take the returned event, find the node that accepts *that*, repeat until `StopEvent`.

Point 2 deserves emphasis. Students coming from procedural pipelines assume the array order matters. It does not, and understanding why is understanding the model.

### Is this useful?

By itself, no. But it is the right place to start because it isolates the mechanics from the complexity, and because the next lesson only adds one idea to it.

### Key takeaways

- `Workflow::make()->addNodes([...])->init()` then `run()`.
- `addNodes()` is a registry, not a sequence — events determine order.
- Execution runs from `StartEvent` to `StopEvent`.

---
═══════════════════════════════════════════════════════════════

## LESSON 13.4 — Multi-Step: Events as Wiring

**Duration:** 13 minutes
**Type:** Hands-on

### Learning objectives

Build a three-node workflow and see the type system express the graph.

### The events

```php
namespace App\Neuron;

class FirstEvent implements Event
{
    public function __construct(protected string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(protected string $secondMsg){}
}
```

### The nodes

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use App\Neuron\FirstEvent;

class InitialNode extends Node
{
    /**
     * Gets the "StartEvent" and returns "FirstEvent"
     */
    public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
    {
        echo "\n- Handling StartEvent";

        return new FirstEvent("InitialNode complete");
    }
}
```

```php
class NodeOne extends Node
{
    /**
     * Takes "FirstEvent" as input and returns "SecondEvent"
     */
    public function __invoke(FirstEvent $event, WorkflowState $state): SecondEvent
    {
        echo "\n- ".$event->firstMsg;

        return new SecondEvent("NodeOne complete");
    }
}
```

```php
class NodeTwo extends Node
{
    /**
     * Takes "SecondEvent" as input and returns "StopEvent"
     */
    public function __invoke(SecondEvent $event, WorkflowState $state): StopEvent
    {
        echo "\n- ".$event->secondMsg;
        echo "\n- NodeTwo complete";

        return new StopEvent();
    }
}
```

### Running it

```php
use NeuronAI\Workflow\Workflow;

$handler = Workflow::make()
    ->addNodes([
        new InitialNode(),
        new NodeOne(),
        new NodeTwo(),
    ])
    ->init();

$handler->run();
```

```
- Handling StartEvent
- InitialNode complete
- NodeOne complete
- NodeTwo complete
```

### Reading the graph from the signatures

Put the three signatures on one slide with everything else stripped away:

```php
__invoke(StartEvent  $e, ...): FirstEvent
__invoke(FirstEvent  $e, ...): SecondEvent
__invoke(SecondEvent $e, ...): StopEvent
```

```
StartEvent → InitialNode → FirstEvent → NodeOne → SecondEvent → NodeTwo → StopEvent
```

The graph is right there in the type declarations. No configuration to fall out of sync with the code, and your IDE navigates it: click through the event type to find the node that consumes it.

### Naming, which matters more than it looks

`FirstEvent` and `SecondEvent` are fine for a tutorial and terrible for a real project. In production, name events for **what happened**:

```php
ArticleDrafted
ResearchCompleted
ReviewRejected
RefundApproved
PaymentFailed
```

Past-tense facts, not sequence positions. Then the signature reads like a sentence: *this node runs when an article has been drafted and produces a review request*. Someone reading the code six months later understands the flow without a diagram.

This is ordinary domain-event naming from event-driven design, and it applies unchanged here.

### One field per event, or the whole context?

Keep events small. An event should carry what the *next* node needs, not everything accumulated so far. Large shared context belongs in state (Lesson 14.3). An event that grows to fifteen properties is telling you its data belongs in state.

### Key takeaways

- Three nodes, three signatures, one graph.
- The type declarations are the wiring — readable and IDE-navigable.
- Name events as past-tense domain facts, not `FirstEvent`.
- Keep events small; put shared context in state.

---
═══════════════════════════════════════════════════════════════

## LESSON 13.5 — Why Not Just Write a Script?

**Duration:** 11 minutes
**Type:** Theory — the objection lesson

### Learning objectives

Answer the honest objection, and know when the answer is "you're right, write the script".

### The objection

The documentation raises it itself, which is a good sign:

> "This sounds great, but why can't I just write a regular PHP script with some if-statements and functions?"

And it admits: *"It's a fair question, and one I heard a lot while building Neuron."*

Say this to your students before they think it. Pre-empting the objection buys credibility; dismissing it loses it.

### The honest answer for simple cases

**For a three-step linear process, a script is better.** Fewer files, less indirection, easier to read. The framework's own answer concedes this — the potential is not visible when the use case is simple, and that is normal.

Do not oversell. Students who adopt workflows for everything will produce a codebase where a function call became four classes, and they will resent it.

### Where the script breaks

The documented answer lists the conditions, and each maps to a real cost:

**Multiple branches run concurrently.** Doing this in a script means `pcntl_fork` and manual result collection. Lesson 14.2 shows it as a return type.

**Several loops with intermediate checkpoints.** Doable with `while`, until you need to know which iteration you were on after a crash.

**Streaming real-time updates.** A script can echo. It cannot easily emit structured progress events from arbitrary depth without threading a callback through every function.

**Pause, wait, resume.** This is the one that is not a matter of effort. Serialising the entire execution state mid-function, persisting it, resuming in a different process hours later — you cannot write that in a script without building a workflow engine. And if you build one, you have built this.

### The four development benefits

From the documentation:

**Model and maintain complex scenarios.** From a few steps up to iterative loops with checkpoints, using the same building blocks.

**Human in the loop.** Deploy AI in sensitive areas because a human is always in the loop for critical decisions.

**Streaming.** Real-time updates to the client during execution.

**Debugging with Inspector.** Instead of wondering why the workflow made a decision, see exactly what happened at any node.

That last one connects to Module 10. Nodes are named units, so a trace shows named steps. A script shows a stack trace.

### The decision rule

Write a script when: linear, no branching, no human input, no need to resume, no streaming.

Write a workflow when **any one of** these is true: multiple agents, human approval, resumable, long-running, streaming progress, or non-trivial branching and looping.

And the argument that closes it, from the docs:

> If things hit the fan, Neuron already has the appropriate architecture to help you scale at any level.

You do not migrate frameworks when the requirement arrives. You add a node.

### Key takeaways

- For simple linear processes, a script is genuinely better. Say so.
- Concurrency, checkpoints, streaming and resumption are where scripts break.
- Pause-and-resume is not a matter of effort — it requires an engine.
- One trigger is enough to justify a workflow; you do not need all of them.

---
═══════════════════════════════════════════════════════════════
# MODULE 14 — LOOPS, BRANCHES AND STATE
═══════════════════════════════════════════════════════════════
---

## LESSON 14.1 — Loops

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Build iteration into a workflow using nothing but return types.

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

This is the number one workflow bug. It fails at runtime with a confusing message, and the cause is a union type someone forgot to widen after adding a branch. Put it on a slide.

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

**Every loop iteration costs LLM calls.** This is Lesson 1.4 again. An unbounded review loop is an unbounded bill.

**Have a plan for hitting the limit.** Escalating to a human beats silently shipping the third draft. That is the natural bridge into Module 15.

### Loops are where agentic systems earn their keep

A loop with an LLM in it is *iterative refinement*: draft, critique, revise, repeat until good enough. That pattern — writer plus critic — is one of the highest-value multi-agent shapes, and it is a three-node workflow with one union return type.

### Key takeaways

- A loop is a node returning an event that re-triggers an earlier node.
- **Declare every possible return type in the union** — the most common workflow bug.
- Returning `StartEvent` restarts the whole workflow.
- The framework does not bound loops; count in state and plan for the limit.

---
═══════════════════════════════════════════════════════════════

## LESSON 14.2 — Branches, Sequential and Parallel

**Duration:** 15 minutes
**Type:** Hands-on

### Learning objectives

Split execution down alternative paths, and run independent paths concurrently.

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

**A convergence trick worth teaching:** to rejoin two branches, have the last node of each return the *same* event type. Whichever branch ran, the same downstream node picks it up. That is how you build diamond shapes without any join syntax.

*(The documentation's example class names are `BrancheA1Event` — a French-flavoured misspelling. Do not copy it into your course.)*

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

The practical consequence, and it is the thing students will trip over: **a branch writing to `$state` is writing to a copy that will be discarded.** If you want data out of a branch, it goes in the `StopEvent` result. Full stop.

Show this failure deliberately on camera — set state in a branch, read it in the merge node, watch it be absent. Then fix it with the result. Five minutes, and the rule sticks.

### When parallel branches pay off

Same shape as Lesson 5.13: **independent, I/O-bound work**. Three agents analysing the same document from different angles. Two API calls that do not depend on each other. Text and image processing of one upload.

Not useful for: sequential dependencies, or trivially fast work where coordination costs more than it saves.

### Key takeaways

- Conditional branching is a union return type; converge by returning a shared event type.
- `ParallelEvent(['name' => $event, ...])` runs branches concurrently.
- Branches end with `StopEvent(result: ...)`; the merge node reads `getResult('name')`.
- **Branch state is an isolated copy** — mutations are discarded; return data via the result.

---
═══════════════════════════════════════════════════════════════

## LESSON 14.3 — Managing State

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Use the default state container, and replace it with a typed one when the project deserves it.

### The default

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\StopEvent;
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

Then inject it when constructing the workflow. *(Confirm the injection signature in your version — this is one of the places where the v2/v3 constructor drift shows.)*

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

Now the loop guard from Lesson 14.1 reads as `$state->hasReachedLimit()` in every node that needs it, defined once.

### The serialisation constraint

Critical for Module 15, and worth flagging here so it is not a surprise:

**State is serialised when a workflow is interrupted.** Which means:

- **Resources cannot be serialised.** Database connections, file handles, open sockets. Store an identifier and re-establish the connection when the node resumes.
- Same for closures and anything holding a resource indirectly.

The framework's own guidance is explicit on this. A `CustomState` holding a `PDO` will fail at the interruption boundary — and it will fail there, not where you wrote it, which makes it an unpleasant bug.

**Store IDs, not objects with connections.** `protected int $userId` rather than a hydrated Eloquent model carrying a live connection.

### Key takeaways

- `WorkflowState` is a string-keyed bag: fine small, weak at scale.
- `CustomState` gives typed accessors, discoverability and a home for derived logic.
- **State is serialised on interruption** — no resources, no connections, no closures.
- Store IDs and re-hydrate inside the node.

---
═══════════════════════════════════════════════════════════════

## LESSON 14.4 — Streaming a Workflow

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Emit progress from inside a multi-node workflow so the client sees what is happening.

### One keyword

Add `\Generator` to the return type and `yield`:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\StartEvent;
use NeuronAI\Workflow\StopEvent;

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

**`yield` emits progress. `return` emits the routing event.** Two channels from one method — that is the whole design, and it is elegant enough to point out. PHP generators, used exactly as intended.

### Why this is a genuinely strong feature

Compare the two user experiences for a workflow that takes 45 seconds:

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

For multi-agent systems this matters even more, because the runs are longer. Lesson 1.4 said latency compounds; this is how you make compounded latency tolerable.

### Design guidance

**Name progress events for the user, not the developer.** `"Searching the knowledge base"` beats `"RetrieveDocumentsNode invoked"`. Same principle as the tool-label allowlist in Lesson 7.4 — and the same security concern: do not leak internals.

**Do not yield every detail.** A progress line per document retrieved is noise. One per meaningful phase.

**Yield before slow work, not after.** `yield new ProgressEvent("Researching...")` then do the research. Yielding afterwards tells the user what already finished, which is the wrong half of the information.

### Connecting to the frontend

The stream adapters from Lesson 7.5 apply here. A workflow's progress events go through `AGUIAdapter` or `VercelAIAdapter` to a browser, and — as noted there — an adapter pushing to a transport like Pusher lets a **queued** workflow stream to a client it has no direct connection to.

That is the combination Module 21 builds: long workflow on a worker, live progress in the browser.

### Key takeaways

- Add `\Generator` to the return type; `yield` progress, `return` the routing event.
- Two channels from one method.
- Name progress events for users; one per phase; yield before the work.
- Adapters carry workflow progress to the frontend, including from queued jobs.

---
═══════════════════════════════════════════════════════════════
# MODULE 15 — HUMAN IN THE LOOP
═══════════════════════════════════════════════════════════════
---

## LESSON 15.1 — Interruption: The Feature, Not the Failure

**Duration:** 12 minutes
**Type:** Theory

### Learning objectives

Understand the interruption model and why it is the framework's most distinctive capability.

### What it does

Neuron's interruption pattern lets a workflow **pause execution and wait for external input before resuming.**

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

`WorkflowInterrupt` is thrown, not returned. That is a design decision worth a sentence of explanation, because it looks odd at first.

It means interruption unwinds the stack from wherever it happens — arbitrarily deep inside a node, inside a helper, inside a middleware — without every intermediate layer needing to know about it or thread a return value back. Any node or middleware can interrupt, from anywhere.

The cost is that you must catch it. A `WorkflowInterrupt` escaping to your error handler looks like a crash and will be logged as one. Lesson 15.4 covers the handling.

### Where this changes what you can build

Lesson 5.10's four defence layers included "offered, gated at runtime". This is that layer, and it unlocks a category of application:

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

---
═══════════════════════════════════════════════════════════════

## LESSON 15.2 — interrupt() and ApprovalRequest

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Pause a node and act on the human's decision.

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

### Design guidance for approval requests

**Write the message for the decider, not the developer.** They are seeing this in an email or an admin screen, with no context. `'Should I continue?'` is a poor message. `'Approve a €240 refund for order #4471 — customer reports item arrived damaged'` lets someone decide without opening another system.

**Include enough in the description to decide.** The third `Action` argument is where the substance goes.

**Group related decisions into one request.** Five actions in one request beats five sequential interruptions, each of which is a separate wake-up, notification and wait.

### Key takeaways

- `$this->interrupt($request)` pauses and later returns the human's response.
- `ApprovalRequest` plus `Action` covers approve/reject with feedback.
- `isApproved()` and `->feedback`; feedback can steer the next iteration.
- Write messages for the person deciding; group related decisions.

---
═══════════════════════════════════════════════════════════════

## LESSON 15.3 — Custom Interrupt Requests

**Duration:** 12 minutes
**Type:** Hands-on

### Learning objectives

Build an interruption carrying whatever your interface needs, not just yes or no.

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

That round trip — PHP object → JSON → UI → edited JSON → PHP object — is the whole lifecycle, and naming it explicitly helps students see where their frontend fits.

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

Worth stating as a design principle: **when the likely human response is "almost, but change this", build an editable interrupt rather than an approval.**

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

---
═══════════════════════════════════════════════════════════════

## LESSON 15.4 — Catching, Persisting and Resuming

**Duration:** 15 minutes
**Type:** Hands-on — the operational heart of Module 15

### Learning objectives

Wire the full pause-and-resume cycle, including the storage that makes it survive a process restart.

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

**Read the schema out loud**, because it tells you what is happening: `LONGBLOB` / `BYTEA` — the entire serialised execution state, as binary. And `idx_updated_at` exists so you can find stale interrupts, which is your cleanup story.

Use `FilePersistence` for CLI and development. Use `DatabasePersistence` for anything multi-server or production.

### The four operational questions

Nobody's tutorial covers these and every production system needs them. Put them on a slide:

**1. Who is notified?** The interrupt does not send an email. Your code does. Wire the notification in the catch block.

**2. What if nobody responds?** Interrupts accumulate. You need a timeout policy: escalate, expire, or auto-reject. `idx_updated_at` is there for this query.

**3. How do you prevent double-resume?** Two managers open the same approval link and both click. Mark the request resolved atomically before resuming.

**4. What about a deployment in between?** The serialised state contains your classes. A deployment that renames a class or changes a property will break deserialisation of in-flight interrupts. Either drain before deploying, or version your interrupt requests.

That last one is the sharp edge, and it is worth dwelling on. Long-lived serialised PHP objects across deployments is a known hard problem, and interruption puts you squarely in it. The mitigation — keep interrupt requests small, flat, and change them rarely — is worth stating as a design rule rather than discovered as an incident.

### Key takeaways

- Persistence is mandatory for interruption; `FilePersistence` for CLI, `DatabasePersistence` for production.
- Catch `WorkflowInterrupt`; store `getRequest()` and `getWorkflowId()`.
- Resume with the same persistence, the same ID, and the reconstructed request.
- Four operational questions: notification, timeout, double-resume, deployment compatibility.

---
═══════════════════════════════════════════════════════════════

## LESSON 15.5 — Checkpoints, Conditional Interrupts and Middleware

**Duration:** 16 minutes
**Type:** Hands-on

### Learning objectives

Avoid re-running expensive work on resume, interrupt conditionally, and gate tool calls with middleware.

### The re-execution problem

> When the Workflow is resumed it restarts execution **from the node where it was interrupted. The node will be re-executed entirely, including the code before the interruption.**

Read that carefully, because it has real cost. If your node calls an LLM, then interrupts, then resumes — **the LLM call runs again.** You pay twice, you wait twice, and because of Lesson 1.5 you may get a *different answer* the second time, which means the human approved something other than what gets used.

That last consequence is the serious one. It is not just waste; it is a correctness bug.

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

**The rule to teach: any LLM call, any paid API call, and anything non-deterministic that precedes an `interrupt()` in the same node belongs inside a `checkpoint()`.** No exceptions worth teaching.

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

Purchases under €100 proceed; larger ones wait for a human. This is Lesson 5.10's fourth layer, now concrete — and it is a far better product than either always-allow or always-block.

Note the shape: `middleware(ToolNode::class, ...)`. Lesson 2.3 said node names are public API. This is why.

### ToolSearchMiddleware

```php
new ToolSearchMiddleware([...])
```

For agents with large tool catalogues. Rather than sending every schema on every request — Lesson 1.3's compounding cost — it selects relevant tools dynamically.

Worth mentioning as the answer to "what if I have 200 tools?", which someone always asks after Module 5.

### Key takeaways

- **A resumed node re-executes from the top** — including LLM calls, with possibly different results.
- `checkpoint('name', fn)` saves and replays; wrap everything expensive or non-deterministic before an interrupt.
- `consumeResumeRequest()` branches on whether you are waking.
- `interruptIf()` keeps approvals meaningful; the callback form defers evaluation.
- `ToolApproval` gates tool calls conditionally on arguments; `ToolSearchMiddleware` handles large catalogues.

---
═══════════════════════════════════════════════════════════════
# MODULE 16 — MULTI-AGENT SYSTEMS
═══════════════════════════════════════════════════════════════
---

## LESSON 16.1 — Orchestration Patterns

**Duration:** 12 minutes
**Type:** Theory

### Learning objectives

Recognise the standard multi-agent shapes and choose one deliberately.

### First, the sceptical question

Multi-agent systems demo beautifully and are frequently the wrong answer. Before adopting one, ask: **would one agent with more tools do this?**

Often yes. Every additional agent is another set of model calls, another system prompt to maintain, another place for context to be lost in translation. Lesson 1.4's arithmetic applies per agent.

Multi-agent earns its place when: the sub-tasks need genuinely different instructions, the agents need different tool sets or permissions, or you want independent review of one agent's output.

That third one is the strongest case, and it is not really about capability — it is about **independence**. An agent reviewing its own work is a poor critic. A separate agent with a critic's system prompt is a better one.

### The patterns

**Sequential.** Researcher → Writer → Editor. Each stage's output feeds the next. Simple, predictable, easy to debug. The default, and often sufficient.

**Supervisor.** One coordinator decides which specialist to invoke, receives the result, decides what is next. Flexible, and the most expensive — the supervisor makes a model call per decision.

**Parallel.** Several agents work simultaneously on independent sub-tasks; a merge node combines. Fast for genuinely independent work. Lesson 14.2 gives you the mechanism.

**Debate / critic loop.** A generator produces, a critic evaluates, the generator revises. Repeat until the critic is satisfied or the limit is reached. This is Lesson 14.1's loop with two agents in it, and it is the highest-quality-per-complexity pattern in the list.

### Mapping patterns to Neuron

Each is a workflow shape you already know:

| Pattern | Mechanism |
|---|---|
| Sequential | Chain of nodes, one event each |
| Supervisor | A node returning a union of specialist events |
| Parallel | `ParallelEvent` with named branches |
| Critic loop | Union return type looping back |

**No special multi-agent API.** That is the point of Lesson 2.3 arriving for the final time: an agent is a node, and composing nodes is what workflows do.

### Cost discipline

A four-agent sequential pipeline is at minimum four model calls, usually more if any of them use tools. A critic loop running three rounds is six-plus.

Two mitigations worth teaching:

**Different models per agent.** The researcher and the critic may need a strong model; the formatter does not. Lesson 3.6's provider swap is per-node here, and it is one of the framework's better arguments in a multi-agent context.

**Bound every loop.** Lesson 14.1's counter, non-negotiable.

### Key takeaways

- Ask whether one agent with more tools would do; often it would.
- Independent review is the strongest case for multi-agent.
- Four patterns: sequential, supervisor, parallel, critic loop.
- No special API — agents are nodes.
- Vary the model per agent; bound every loop.

---
═══════════════════════════════════════════════════════════════

## LESSON 16.2 — An Agent as a Node

**Duration:** 11 minutes
**Type:** Hands-on

### Learning objectives

Wrap an agent as a workflow node, and keep it independently testable.

### The wrapper

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Nodes;

use App\Agents\ResearchAgent;
use App\Workflow\Events\ResearchCompleted;
use App\Workflow\Events\TopicRequested;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;

class ResearchNode extends Node
{
    public function __invoke(TopicRequested $event, WorkflowState $state): \Generator|ResearchCompleted
    {
        yield new ProgressEvent("Researching {$event->topic}...");

        $findings = ResearchAgent::make()
            ->chat(new UserMessage("Research this topic thoroughly: {$event->topic}"))
            ->getMessage()
            ->getContent();

        $state->set('sources_used', $this->countSources($findings));

        return new ResearchCompleted($event->topic, $findings);
    }
}
```

The node is a thin adapter. All the intelligence — provider, instructions, tools — lives in `ResearchAgent`, which is unchanged and still works standalone.

**Say that explicitly on camera:** `ResearchAgent` does not know it is in a workflow. You can still unit-test it, still call it directly, still reuse it in a different pipeline. The node is glue.

### Structured output between agents

Passing prose between agents loses information and invites misinterpretation. Pass typed objects instead:

```php
class ReviewNode extends Node
{
    public function __invoke(DraftCompleted $event, WorkflowState $state): DraftCompleted|ArticleApproved
    {
        $verdict = ReviewerAgent::make()->structured(
            new UserMessage($event->draft),
            Verdict::class
        );

        if ($verdict->approved) {
            return new ArticleApproved($event->draft);
        }

        $state->set('last_feedback', $verdict->feedback);

        return new DraftCompleted($event->draft, $verdict->feedback);
    }
}
```

```php
class Verdict
{
    #[SchemaProperty(description: 'Whether the draft meets the quality bar.', required: true)]
    public bool $approved;

    #[SchemaProperty(
        description: 'If not approved, the specific changes required. One instruction per sentence.',
        required: true
    )]
    public string $feedback;

    #[SchemaProperty(description: 'Quality score from 0 to 10.', required: true)]
    #[GreaterThanEqual(reference: 0)]
    #[LowerThanEqual(reference: 10)]
    public int $score;
}
```

**This is Module 6 doing structural work.** `$verdict->approved` is a boolean your PHP branches on. Parsing "the draft looks good to me!" for a yes/no would be a coin flip.

The rule: **structured output at every agent-to-agent boundary.** Prose is for humans.

### Different providers per node

```php
class DraftNode extends Node
{
    public function __invoke(ResearchCompleted $event, WorkflowState $state): DraftCompleted
    {
        // Strong model — this is the creative work
        $draft = WriterAgent::make()->chat(/* ... */);

        return new DraftCompleted($draft);
    }
}

class FormatNode extends Node
{
    public function __invoke(ArticleApproved $event, WorkflowState $state): StopEvent
    {
        // Cheap model — mechanical transformation
        $formatted = FormatterAgent::make()->chat(/* ... */);

        return new StopEvent(result: $formatted);
    }
}
```

Each agent declares its own provider. Cost tiering across a multi-agent system is a property of how you wrote the agents, not something you configure separately.

### Key takeaways

- The node is a thin adapter; the agent stays independent and testable.
- Use `structured()` at every agent-to-agent boundary — prose loses information.
- Yield progress from agent nodes; runs are long enough to need it.
- Provider choice is per agent, so cost tiering is free.

---
═══════════════════════════════════════════════════════════════

## LESSON 16.3 — Context Without Token Explosion

**Duration:** 12 minutes
**Type:** Theory with code

### Learning objectives

Pass information between agents without each one re-sending everything that came before.

### The failure mode

The naive multi-agent pipeline accumulates. Agent 1 produces 800 words. Agent 2 receives them plus the original prompt, produces 1,200. Agent 3 receives everything, produces 1,500. Agent 4 receives all of it.

By the fourth agent you are sending 4,000 words of context to produce 300 words of output — and Lesson 1.4 already showed what accumulation does to cost.

### Four techniques

**1. Pass the artefact, not the transcript.**

The writer needs the research *findings*. It does not need the researcher's reasoning, its tool calls, or its intermediate drafts.

```php
// Bad: the whole conversation
return new ResearchCompleted($agent->getChatHistory()->getMessages());

// Good: just the output
return new ResearchCompleted($event->topic, $findings);
```

**2. Summarise at the boundary.**

When one agent's output is genuinely large, add a compression step. One cheap model call to reduce 3,000 words to 400 saves far more than it costs on any pipeline with two or more downstream agents.

**3. Use state for shared context, events for the handoff.**

Lesson 13.2's distinction, applied. The tenant, the user, the brief — state. The specific artefact this node produced for the next one — event.

**4. Give each agent only what it needs.**

```php
class FactCheckNode extends Node
{
    public function __invoke(DraftCompleted $event, WorkflowState $state): FactCheckCompleted
    {
        // The fact-checker gets claims and sources. Not the draft's prose,
        // not the brief, not the research narrative.
        $result = FactCheckAgent::make()->structured(
            new UserMessage(json_encode([
                'claims'  => $event->extractedClaims,
                'sources' => $state->get('sources'),
            ])),
            FactCheckResult::class
        );

        return new FactCheckCompleted($result);
    }
}
```

This is ordinary interface design — minimal, explicit inputs — applied to agents. Worth naming that way for a senior audience: **each agent has an interface, and a wide interface is as bad here as anywhere else.**

### Measuring it

Enable Inspector (Module 10) and read input tokens per node across the run. If they grow linearly through the pipeline, you are accumulating. That number is your optimisation target, and it is visible rather than guessed.

### Key takeaways

- Pass artefacts, not transcripts.
- Summarise at boundaries when output is large.
- State for shared context, events for handoffs.
- Treat each agent's input as an interface — keep it minimal.
- Read input tokens per node in the trace to find accumulation.

---
═══════════════════════════════════════════════════════════════

## LESSON 16.4 — Asynchronous Execution

**Duration:** 11 minutes
**Type:** Theory

### Learning objectives

Get long multi-agent runs off the request cycle, and understand what changes when you do.

### Why this is not optional

Add up what Part IV has established:

- A multi-agent run is many model calls (Lesson 16.1)
- Each is 1–4 seconds (Lesson 1.4)
- Parallel tool calls need CLI (Lesson 5.13)
- Human-in-the-loop means waiting hours or days (Lesson 15.1)

A 60-second workflow cannot live in an HTTP request. Anything with an interruption *definitely* cannot.

**Long workflows belong on a queue.**

### The architecture

```
HTTP request  → dispatch a job → return a workflow ID immediately
Queue worker  → run the workflow → stream progress via an adapter
                                  → persist any interruption
Human         → responds via UI/email
Queue worker  → resume the workflow → complete
Client        → receives progress and the result over the transport
```

Four pieces you already have:

- **Persistence** (Lesson 15.4) for interruption state
- **Stream adapters** (Lesson 7.5) to push progress to a transport
- **Workflow ID** as the correlation key
- **Queue** as the execution context

### What changes on a worker

**`pcntl` becomes available**, so parallel tool calls (Lesson 5.13) and parallel evals (Lesson 10.6) work.

**Inspector needs `autoFlush: true`** (Lesson 10.2). A worker has no end-of-request, so without it traces never ship. This is the single most likely misconfiguration in an async deployment.

**No HTTP connection to the user.** Which is why adapters pushing to a websocket transport matter — the worker streams to Pusher, the browser listens.

**Timeouts are yours to manage.** Queue workers have time limits. A workflow that runs for ten minutes needs a worker configured for it, or needs to interrupt and resume across jobs.

### The pattern that ties Part IV together

For a long, human-gated workflow, each segment between interruptions is its own job:

```
Job 1: run until the approval interrupt → persist → notify the manager → end
       (worker is free)
Job 2: triggered by the approval → resume → run to completion or the next interrupt
```

The worker is not blocked waiting. Between segments there is no process at all — only a row in `workflow_interrupts`.

That is what "resume even across different sessions" means operationally, and it is worth drawing on a slide. It is also, for a PHP audience used to request-scoped execution, a genuinely satisfying resolution: PHP's statelessness stops being a limitation and becomes the deployment model.

### Module 15–16 assessment

1. Build a three-agent sequential workflow with structured output at each boundary.
2. Add a critic loop with a bounded counter and a plan for hitting the limit.
3. Add an interruption before the final action; persist it; resume from a separate script.
4. Wrap every pre-interrupt LLM call in a `checkpoint()` and verify it is not re-executed.
5. Measure input tokens per node and reduce the accumulation.

---
═══════════════════════════════════════════════════════════════

## LAB 10 — The Content Factory

**Duration:** 40 minutes
**Covers:** everything in Part IV

### Goal

Research → draft → review loop → human approval → publish. It is the canonical multi-agent workflow and it exercises loops, state, streaming, interruption, checkpointing and persistence in one artefact.

### The shape

```
StartEvent
   ↓
ResearchNode        (Tavily toolkit)
   ↓ ResearchCompleted
DraftNode           (writer agent)
   ↓ DraftCompleted
ReviewNode          (critic agent, structured Verdict)
   ↓ DraftCompleted (loop back, max 3)  |  ArticleApproved
                                        ↓
ApprovalNode        (interrupt — human reviews and edits)
   ↓ ArticleEdited
PublishNode
   ↓ StopEvent
```

### The events

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Events;

use NeuronAI\Workflow\Events\Event;

final class ResearchCompleted implements Event
{
    public function __construct(
        public readonly string $topic,
        public readonly string $findings,
    ) {}
}

final class DraftCompleted implements Event
{
    public function __construct(
        public readonly string $draft,
        public readonly ?string $feedback = null,
    ) {}
}

final class ArticleApproved implements Event
{
    public function __construct(
        public readonly string $draft,
    ) {}
}

final class ArticleEdited implements Event
{
    public function __construct(
        public readonly string $content,
    ) {}
}
```

Note the naming — past-tense facts, per Lesson 13.4. Note also `readonly`: events are messages, not mutable containers.

### The state

```php
<?php

declare(strict_types=1);

namespace App\Workflow;

use NeuronAI\Workflow\WorkflowState;

class ContentState extends WorkflowState
{
    protected int $revisions = 0;
    protected array $feedbackLog = [];

    public function recordRevision(string $feedback): self
    {
        $this->revisions++;
        $this->feedbackLog[] = $feedback;
        return $this;
    }

    public function revisionCount(): int
    {
        return $this->revisions;
    }

    public function hasReachedLimit(int $max = 3): bool
    {
        return $this->revisions >= $max;
    }

    public function feedbackHistory(): array
    {
        return $this->feedbackLog;
    }
}
```

Scalars and arrays only — no connections, no resources. Lesson 14.3's serialisation constraint, respected by design.

### The review node — where the module comes together

```php
<?php

declare(strict_types=1);

namespace App\Workflow\Nodes;

use App\Agents\ReviewerAgent;
use App\Dto\Verdict;
use App\Workflow\ContentState;
use App\Workflow\Events\ArticleApproved;
use App\Workflow\Events\DraftCompleted;
use App\Workflow\Events\ProgressEvent;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\Workflow\Node;

class ReviewNode extends Node
{
    public function __invoke(
        DraftCompleted $event,
        ContentState $state
    ): \Generator|DraftCompleted|ArticleApproved {
        yield new ProgressEvent('Reviewing the draft...');

        $verdict = ReviewerAgent::make()->structured(
            new UserMessage($event->draft),
            Verdict::class
        );

        if ($verdict->approved) {
            yield new ProgressEvent("Approved with a score of {$verdict->score}/10.");

            return new ArticleApproved($event->draft);
        }

        if ($state->hasReachedLimit()) {
            yield new ProgressEvent('Revision limit reached — sending to human review as is.');

            return new ArticleApproved($event->draft);
        }

        $state->recordRevision($verdict->feedback);

        yield new ProgressEvent("Revision {$state->revisionCount()}: {$verdict->feedback}");

        return new DraftCompleted($event->draft, $verdict->feedback);
    }
}
```

Every Part IV concept in one class: a union return type (14.1), a bounded loop with a plan for the limit (14.1), custom state (14.3), streaming progress (14.4), and structured output at an agent boundary (16.2).

### The approval node

```php
class ApprovalNode extends Node
{
    public function __invoke(ArticleApproved $event, ContentState $state): ArticleEdited
    {
        $reviewed = $this->interrupt(
            new ContentReviewInterrupt(
                message: \sprintf(
                    'Article ready after %d revision(s). Review and edit before publishing.',
                    $state->revisionCount()
                ),
                content: $event->draft
            )
        );

        return new ArticleEdited($reviewed->getContent());
    }
}
```

The human edits rather than approves — Lesson 15.3's collaboration pattern.

### The checkpoint demonstration

Show the bug before the fix. Write `ApprovalNode` so the draft is *generated* inside it, un-checkpointed:

```php
// DELIBERATELY WRONG — for the demo
$draft = WriterAgent::make()->chat(...)->getMessage()->getContent();

$reviewed = $this->interrupt(new ContentReviewInterrupt(/* ... */, $draft));
```

Run it, interrupt, resume. The draft regenerates and **the resumed version differs from the one the human approved.** That is a correctness bug, live on camera.

Then wrap it:

```php
$draft = $this->checkpoint('draft', fn () => WriterAgent::make()->chat(...)->getMessage()->getContent());
```

Re-run. Same draft. Same content the human saw.

**This is the best five minutes in Part IV.** It is not an abstract efficiency argument — it is a demonstrable correctness failure with a one-line fix.

### Running it

```php
$workflow = new ContentWorkflow(
    new FilePersistence(__DIR__ . '/../storage/workflows')
);

try {
    $handler = $workflow->init();

    foreach ($handler->streamEvents() as $progress) {
        echo "  {$progress->message}\n";
    }

    echo "\nPublished.\n";
} catch (WorkflowInterrupt $interrupt) {
    $id      = $interrupt->getWorkflowId();
    $request = $interrupt->getRequest();

    \file_put_contents(
        __DIR__ . "/../storage/pending/{$id}.json",
        \json_encode($request, JSON_PRETTY_PRINT)
    );

    echo "\nAwaiting review. Workflow ID: {$id}\n";
    echo "Edit storage/pending/{$id}.json and run: php examples/11-resume.php {$id}\n";
}
```

*(Confirm the streaming accessor on the handler in your installed version — this is one of the v2/v3 drift points from the warning at the top.)*

Editing a JSON file on disk as the "approval UI" is exactly right for a CLI lab. It makes the mechanism visible, and Module 22 replaces it with a real Filament screen.

### Extensions

1. Add a parallel branch: fact-check and SEO analysis run concurrently after approval, merged before publishing.
2. Add `interruptIf()` so only articles scoring below 8 require human review.
3. Move execution to a queue worker and stream progress over a websocket.

---

## PART IV — VERIFICATION LIST (ADDITIONS)

| # | Issue | Where |
|---|---|---|
| 30 | `init()`/`run()` vs `start()`/`getResult()` — two execution APIs across doc pages | Workflow, throughout |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')` — v2 constructor still in blog posts | Interruption, blogs |
| 32 | `Edge` class and `addEdges()` — removed in v2, still in v1 material | Older tutorials |
| 33 | `BrancheA1Event` — misspelling in the branching example | Loops & branches |
| 34 | Missing commas after `message:` in several `ApprovalRequest` examples | Human in the loop |
| 35 | Missing semicolon after `parent::__construct($message)` in `ContentReviewInterrupt` | Human in the loop |
| 36 | `ContentReviewInterrupt` invoked with a positional second argument after a named first | Human in the loop |
| 37 | Confirm the `CustomState` injection signature on the workflow | Managing the state |
| 38 | Confirm the handler's streaming accessor method name | Workflow streaming |

Running total: **38 items.**

---

**END OF PART IV**

*Next: Part V — Laravel. Module 17 (SDK setup), Module 18 (agents as first-class citizens), Module 19 (tools that touch your application), Module 20 (RAG on application data).*
