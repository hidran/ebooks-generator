# Agentic AI in PHP with Neuron
## PART IV — WORKFLOWS AND MULTI-AGENT SYSTEMS
### Full lesson scripts — Modules 13, 14, 15 and 16

> Copy each lesson block (between the `═══` separators) into its own Google Doc.
> Target version: `neuron-core/neuron-ai` ^4.0 (verified on 4.0.3), PHP 8.5.

---

> ## ⚠ API DRIFT WARNING FOR THIS PART
>
> Older tutorials, blog posts and parts of the documentation show execution APIs that do not exist in v4:
>
> ```php
> // v3 style: a handler object (does not run on v4)
> $handler = Workflow::make()->addNodes([...])->init();
> $handler->run();
>
> // v2 style (does not run on v4)
> $state = Workflow::make()->addNodes([...])->start()->getResult();
> ```
>
> The v2 style also shows `Workflow::make(new WorkflowState(), $persistence, 'id')` and an
> `Edge` class that no longer exists — the event-driven model replaced it entirely.
>
> **In v4 a workflow runs by calling `run()` on the workflow itself, and it returns the final state:**
>
> ```php
> $state = Workflow::make(workflowId: 'demo')->addNodes($nodes)->run();
> ```
>
> There is no handler, and neither `init()` nor `start()` exists. The constructor is
> `(?string $workflowId, ?WorkflowState $state)`, so material that passes a persistence object or a
> `resumeToken:` argument to it fails. A node's `__invoke()` takes the event and the state, plus an
> optional third `WorkflowResources $resources` parameter (Lesson 14.3). The lessons below use the v4 form.

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

This is why Module 2 insisted on it. Part IV is not a new topic — it is the layer that was underneath Parts II and III all along. That is literal, not a figure of speech: `Agent` is declared as `class Agent extends Workflow`, and the tool-calling loop you used in Part II is a set of nodes routed by the same engine you are about to program directly.

### What makes Neuron's workflow distinctive

The documentation names two capabilities, and a third sits underneath both:

**Streaming** — a multi-agent system can push updates to clients as it runs.

**Interruption** — the workflow can pause mid-process, ask for human input, wait, and continue from the node that paused — even hours or days later, in a different process.

**Durability** — every node that completes is committed to a store as a *step*. A run that crashes, fails or pauses does not start again from the top: the completed steps are replayed from the store, and only the unfinished work runs.

The third is what makes the second possible. Most workflow engines can pause; few can pause *inside* a node, survive a process restart, and continue with human feedback injected at the point it stopped, without redoing the expensive work that came before. Lesson 13.6 shows the durable steps with a crash you can run; Module 15 builds interruption on top of them, and it is the strongest single argument for the framework.

### Key takeaways

- Nodes triggered by events, returning events that trigger further nodes.
- A node is anything from one line to a whole agent.
- Agent and RAG *are* workflows; this is the substrate, not an add-on.
- Streaming, interruption and durable steps are the distinguishing capabilities.

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

use NeuronAI\Workflow\Events\Event;

class FirstEvent implements Event
{
    public function __construct(public readonly string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(public readonly string $secondMsg){}
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
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Node;
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

The signature is strict: an event first, a `WorkflowState` (or a subclass of it) second, optionally a `WorkflowResources` third, and a return type made of events. The workflow validates every node by reflection when it builds the graph at the start of an execution, so a malformed signature fails the run with the node's name in the message; `addNodes()` itself does not check it.

### The idea that makes it click

**The method signature is the graph.**

```text
public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
```

Read it as a wiring statement: *this node runs when a `StartEvent` appears, and when it finishes it emits a `FirstEvent`.*

There is no separate edge definition, no configuration file, no `addEdge()` call. **The type hints are the wiring.**

Say this on camera and let it sit. Everything else in Part IV follows from it:

- Want a loop? Return the event that triggers an earlier node.
- Want a branch? Declare a union return type.
- Want to know the graph? Read the signatures.

> **Historical note worth mentioning.** There is no `Edge` class and no `addEdges()`: the event types are the edges. Version 1 had them; later versions removed them in favour of the event model. If you find a tutorial using `new Edge(NodeA::class, NodeB::class)`, it was written for a much older version of the framework.

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

`set()` and `get()`, plus `has()`, `delete()`, `only()` and `all()`. Available to every node — and, because state is saved with every completed step (Lesson 13.6), it has to be serialisable. Lesson 14.3 spells out what that rules out.

### Events vs state: when to use which

A distinction students consistently get wrong, so make it explicit:

**Events carry the message.** What this specific step produced, passed to the next specific step. Ephemeral, directional, typed.

**State carries the context.** Things many nodes need: the user, the tenant, accumulated results, configuration. Persistent across the whole run.

The heuristic: **if only the next node needs it, put it in the event. If several nodes need it, or you need it after the run, put it in state.**

Overusing state produces a workflow where every node reads and writes a global bag — which is a workflow in name only, because the data flow is invisible again. Overusing events produces enormous event classes that pass everything along. Both extremes are worse than the balance.

### Key takeaways

- Event = plain class implementing `Event`; `StartEvent` and `StopEvent` are built in.
- Node = class with `__invoke(Event, WorkflowState): Event` — plus an optional `WorkflowResources` third parameter.
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

use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\Node;
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

$state = Workflow::make(workflowId: 'demo')
    ->addNodes([
        new InitialNode(),
    ])
    ->run();

echo $state->get('answer'); // Hello World!
```

`StartEvent` in, `StopEvent` out. One node. `run()` returns the final `WorkflowState`.

### The lifecycle

1. `Workflow::make(workflowId: 'demo')` builds the workflow. Its constructor takes two optional arguments, a workflow ID and an initial state. The ID must be bound before the run: the framework never generates one, and `run()` on an unbound workflow throws a `WorkflowException`. Any string will do for now (Lesson 13.6 says what the ID is for); the initial state you do not need yet.
2. `addNodes()` registers the nodes. **Order in the array is not execution order** — the events decide that. The array is a registry, not a sequence.
3. `run()` executes: it generates a run ID, emits `StartEvent`, finds the node whose signature accepts it, runs it, commits the result as a step, takes the returned event, finds the node that accepts *that*, and repeats until `StopEvent`. It returns the final state.

Nothing sits between building a workflow and running it: `run()` and its streaming sibling `events()` (Lesson 14.4) execute it, and both are called on the workflow itself. The one exception is continuing a paused run, where `submitInputs()` returns a `PendingExecution` that you then `run()` or `events()` (Module 15).

Point 2 deserves emphasis. Students coming from procedural pipelines assume the array order matters. It does not, and understanding why is understanding the model.

### The class form

`addNodes()` is convenient for a script. In an application, a workflow is usually a class, and its nodes come from the `nodes()` hook:

```php
use NeuronAI\Workflow\Workflow;

class GreetingWorkflow extends Workflow
{
    protected function nodes(): array
    {
        return [
            new InitialNode(),
        ];
    }
}

$state = GreetingWorkflow::make(workflowId: 'demo')->run();
```

The engine calls `nodes()` fresh at the start of every execution segment, so the graph is always built from the workflow's current configuration — which matters once a run can pause in one process and continue in another.

### Is this useful?

By itself, no. But it is the right place to start because it isolates the mechanics from the complexity, and because the next lesson only adds one idea to it.

### Key takeaways

- `Workflow::make(workflowId: ...)->addNodes([...])->run()` returns the final state; there is no handler.
- `addNodes()` is a registry, not a sequence — events determine order.
- Execution runs from `StartEvent` to `StopEvent`.
- In a subclass, the `nodes()` hook supplies the graph.

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

use NeuronAI\Workflow\Events\Event;

class FirstEvent implements Event
{
    public function __construct(public readonly string $firstMsg){}
}

class SecondEvent implements Event
{
    public function __construct(public readonly string $secondMsg){}
}
```

### The nodes

```php
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
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

$state = Workflow::make(workflowId: 'demo')
    ->addNodes([
        new InitialNode(),
        new NodeOne(),
        new NodeTwo(),
    ])
    ->run();
```

```
- Handling StartEvent
- InitialNode complete
- NodeOne complete
- NodeTwo complete
```

### Reading the graph from the signatures

Put the three signatures on one slide with everything else stripped away:

```text
__invoke(StartEvent  $e, ...): FirstEvent
__invoke(FirstEvent  $e, ...): SecondEvent
__invoke(SecondEvent $e, ...): StopEvent
```

```
StartEvent → InitialNode → FirstEvent → NodeOne → SecondEvent → NodeTwo → StopEvent
```

The graph is right there in the type declarations. No configuration to fall out of sync with the code, and your IDE navigates it: click through the event type to find the node that consumes it.

The framework can read it too. `$workflow->export()` walks the same signatures and prints the graph — as a console tree by default, or as a Mermaid diagram with `setExporter(new MermaidExporter())` — which is a cheap way to check that the graph you meant is the graph you wrote.

### Naming, which matters more than it looks

`FirstEvent` and `SecondEvent` are fine for a tutorial and terrible for a real project. In production, name events for **what happened**:

```text
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

**Several loops with intermediate checkpoints.** Doable with `while`, until you need to know which iteration you were on after a crash. In a workflow every iteration is its own durable step, so the engine already knows.

**Streaming real-time updates.** A script can echo. It cannot easily emit structured progress events from arbitrary depth without threading a callback through every function.

**Pause, wait, resume.** This is the one that is not a matter of effort. Persisting every completed step, stopping mid-node, continuing in a different process hours later without repeating the work already done, and guaranteeing that two workers never advance the same run — you cannot write that in a script without building a workflow engine. And if you build one, you have built Lesson 13.6.

### The four development benefits

From the documentation:

**Model and maintain complex scenarios.** From a few steps up to iterative loops with checkpoints, using the same building blocks.

**Human in the loop.** Deploy AI in sensitive areas because a human is always in the loop for critical decisions.

**Streaming.** Real-time updates to the client during execution.

**Debugging with Inspector.** Instead of wondering why the workflow made a decision, see exactly what happened at any node.

That last one connects to Module 10. The engine dispatches an event as each node starts and ends, and any observer — Inspector included — turns those into a trace of named steps. A script shows a stack trace.

### The decision rule

Write a script when: linear, no branching, no human input, no need to resume, no streaming.

Write a workflow when **any one of** these is true: multiple agents, human approval, resumable, long-running, streaming progress, or non-trivial branching and looping.

And the argument that closes it, from the docs:

> If things hit the fan, Neuron already has the appropriate architecture to help you scale at any level.

You do not migrate frameworks when the requirement arrives. You add a node.

### Key takeaways

- For simple linear processes, a script is genuinely better. Say so.
- Concurrency, checkpoints, streaming and resumption are where scripts break.
- Pause-and-resume is not a matter of effort — it requires durable steps, which is an engine.
- One trigger is enough to justify a workflow; you do not need all of them.

---
═══════════════════════════════════════════════════════════════

## LESSON 13.6 — Durable Steps

**Duration:** 14 minutes
**Type:** Hands-on

### Learning objectives

Understand what `run()` does underneath: every node is a committed step, a failed run recovers instead of restarting, and the workflow ID is how a run is found again.

### Every node is a step

So far a workflow looks like a tidy way to call functions in an order decided by types. Underneath, it is a small durable-execution engine, and the difference shows the first time something fails.

When a node returns, the engine does not just hand the event to the next node. It **commits a step**: the returned event and the state as they stand, written to the workflow's persistence under the run's identity. Only then does it route the event onward. On the default configuration that store is in memory and disappears with the process, which is why you have not noticed it. Give the workflow a persistence backend that outlives the process, and every completed node becomes a fact the engine will not redo.

The consequence: a run that fails in its fifth node, and is started again, **replays** nodes one to four from the store — their events and state are read back, their `__invoke()` is not called — and executes only the fifth.

### The workflow ID

To find a run again, the engine needs a name for it. That name is the **workflow ID**, and it is the partition in the store where every record of the run lives. You can pass one explicitly — `Workflow::make(workflowId: 'report:42')` — but the better habit is to let the workflow declare its own business key:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Workflow;

class ReportWorkflow extends Workflow
{
    public function __construct(private readonly int $reportId)
    {
        parent::__construct();
    }

    public function workflowId(): ?string
    {
        return 'report:' . $this->reportId;
    }

    protected function nodes(): array
    {
        return [
            new ResearchNode(),
            new PublishNode(),
        ];
    }
}
```

Any process that can build `ReportWorkflow::make(reportId: 42)` and reach the same store can find this run. There is no table mapping your records to engine-generated IDs, because the business key *is* the storage location. A workflow that declares nothing must be given an ID by whoever builds it, with `make(workflowId: ...)`, `setWorkflowId()` or `for()`: the framework never makes one up, and `run()` on an unbound workflow throws. Either way the ID is readable from `$state->getWorkflowId()` once the run starts.

Do not confuse it with the **run ID**. Each time a run starts under a workflow ID, the engine stamps it with a fresh run ID (`$state->getRunId()`), a generation marker used for tracing and for fencing stale writers. The workflow ID is the handle you continue a run by; the run ID tells you which attempt you are looking at. The rule that follows from this: **one live run per workflow ID**. Starting a second while the first is still paused or running throws a `RunInFlightException`.

### Memoizing inside a step

Steps are node-sized. A node that makes an expensive call and *then* fails runs again from its first line, and pays for the call again. `memoize()` closes that gap:

```php
namespace App\Neuron;

use NeuronAI\Workflow\Events\StopEvent;
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\WorkflowState;
use RuntimeException;

class PublishNode extends Node
{
    /**
     * Stands in for a flaky HTTP endpoint: the first call fails.
     *
     * PHP 8.5: asymmetric visibility on a static property - anyone may read
     * the counter, only this node may change it.
     */
    public private(set) static int $publishCalls = 0;

    public function __invoke(ResearchDone $event, WorkflowState $state): StopEvent
    {
        $draft = $this->memoize('draft', function () use ($event): string {
            echo "- PublishNode: drafting from '{$event->notes}'\n";

            return 'Report based on: ' . $event->notes;
        });

        if (++self::$publishCalls === 1) {
            echo "- PublishNode: publishing... failed\n";
            throw new RuntimeException('Publisher unavailable');
        }

        echo "- PublishNode: publishing... done\n";
        $state->set('published', $draft);

        return new StopEvent();
    }
}
```

The counter is declared `public private(set) static`: PHP 8.5 extends asymmetric visibility to static properties, so any code can read the counter while only the node itself can change it — a guarantee a plain `public static` could not give.

The closure runs once. Its result is committed under the name `draft` the moment it returns, and when the node runs again the value comes back from the store without the closure being called. In a real workflow the closure is the LLM call, the HTTP request, the tool execution — anything expensive or non-deterministic.

Two rules make it safe. **The closure must depend only on the node's event and state**, so the recorded value is still the right answer on replay. And **a memo is not a transaction**: a crash after the external call but before its result is committed repeats the call. Where a repeat would matter — a payment, an email — give the external system an idempotency key.

> **`checkpoint()` is the old name.** Older tutorials use `checkpoint()`. It still exists, deprecated, and simply calls `memoize()`. Write `memoize()`.

### Watching it work

`ResearchNode`, the first step, is the obvious two-liner: it consumes `StartEvent`, prints `- ResearchNode: calling the slow research service`, and returns a `ResearchDone` event carrying its notes.

Run the workflow twice against a `FilePersistence` directory. The first attempt fails in `PublishNode`; the second is a brand-new `ReportWorkflow` object that shares nothing with the first except the directory and the workflow ID it declares. It could just as well be a different process on a different day:

```php
$storage = \sys_get_temp_dir() . '/neuron-course-13';
$persistence = new FilePersistence($storage);

echo "Attempt 1\n";
try {
    ReportWorkflow::make(reportId: 42)->setPersistence($persistence)->run();
} catch (RuntimeException $e) {
    echo "  caught: {$e->getMessage()}\n";
}

echo "\nAttempt 2\n";
$state = ReportWorkflow::make(reportId: 42)->setPersistence($persistence)->run();
```

```
Attempt 1
- ResearchNode: calling the slow research service
- PublishNode: drafting from 'Three sources, one counter-argument'
- PublishNode: publishing... failed
  caught: Publisher unavailable

Attempt 2
- PublishNode: publishing... done

Workflow ID: report:42
Published: 'Report based on: Three sources, one counter-argument'
Status: Completed
```

The second `run()` found a *failed* run under `report:42` and recovered it rather than starting over. `ResearchNode` did not print anything, because its step was replayed. The draft was not rewritten, because it was memoized. Only the publish call ran again. Nothing in the calling code said "recover": a plain `run()` recovers a failed run automatically, and would have started a fresh one if there had been nothing to recover.

Automatic recovery has two edges. First, the recovered run keeps its *old* input: if a new request arrives under the same business key while a failed run is still in the store, a plain `run()` finishes the old run with the old input, and the new request is silently absorbed. Put the run's input in the start event (`setStartEvent()`), which is stored with the run, so that what recovers is what was asked; and when a fresh generation is what you want, say so with `run(ExecutionRequest::start())` (`NeuronAI\Workflow\Executor\ExecutionRequest`). Second, state you seed through the constructor is not durable until a step commits: a run that pauses or fails in its first node and is continued by an instance seeded differently sees the new seed, not the original. The start event, unlike the seed, is persisted with the run.

When the run completes, the engine deletes its records. The store holds work in progress, not history, so it does not grow, and the workflow ID is free for the next run.

### Where the records live

`setPersistence()` takes any backend implementing `PersistenceInterface`. The ones that ship:

| Backend | Use it for |
|---|---|
| `InMemoryPersistence` | The default. Replay within one process only. |
| `FilePersistence` | Development, and single-process deployments. |
| `DatabasePersistence` | Production with several workers (PDO, one `workflow_store` table). |
| `EloquentPersistence` | The same, through a Laravel model. |
| `RedisPersistence` | Production with several workers, on Redis. |

Whichever you choose, one workflow ID is one partition, and every write is a conditional write against the run's control record, so two workers cannot both advance the same run. Module 15 relies on all of this to pause a run for a human; Module 22 puts it on a real database.

### Key takeaways

- Every completed node is committed as a durable step; a recovered run replays completed steps instead of re-executing them.
- The workflow ID names the run in the store; declare it with `workflowId()` as a business key. The run ID is a per-attempt stamp.
- One live run per workflow ID; a plain `run()` recovers a failed run automatically, with its original input; `run(ExecutionRequest::start())` begins a fresh one.
- `memoize('name', fn () => ...)` makes expensive work inside a node replay-safe. It is not exactly-once: use idempotency keys for side effects.
- Completion deletes the run's records by default.

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

`FirstEvent|SecondEvent`. The union is not decoration. PHP enforces it: return an event that is not in the signature and the node dies with a `TypeError` — `Return value must be of type FirstEvent, SecondEvent returned` — on the one path that returns it, which is usually the rare branch nobody exercised in testing.

The tempting fix is to widen the return type to plain `Event`. It runs, and it costs you the thing Module 13 was about: the signature no longer says where the flow can go, so neither can a reader, nor `export()`, which draws the graph from those same return types.

This is the number one workflow bug, and the cause is always the same: a union type someone forgot to widen after adding a branch. Put it on a slide.

### Loop to anywhere

> You can create a loop from any node to any other node by defining the appropriate input and return events. A node can even return a `StartEvent` to jump right to the first node of the workflow.

Returning `StartEvent` restarts the flow from the top — within the same run, so state keeps everything written so far.

### The guard you must write yourself

Until you set a step budget (see below), the framework will not stop an infinite loop. If your condition never becomes false, the workflow runs forever.

Use state as a counter:

```php
class ReviewNode extends Node
{
    private const MAX_ATTEMPTS = 3;

    public function __invoke(DraftReady $event, WorkflowState $state): DraftReady|ArticleApproved
    {
        $attempts = (int) $state->get('review_attempts', 0);

        $verdict = $this->memoize('verdict', fn (): Verdict => ReviewerAgent::make()
            ->setThreadId($state->getWorkflowId() . ':review')
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

The reviewer is an agent, and an agent needs an ID of its own: the node derives it from the workflow's ID, so the reviewer's conversation stays separate and every run gets its own review thread.

The counter is your business limit: it knows what "too many revisions" means and escalates. As a backstop for the loops you did not foresee, the framework has an opt-in step budget: `setMaxSteps(50)` on the workflow (or a `maxSteps()` override in a workflow class) fails the run with a `WorkflowException` — `Workflow ID 'demo' exceeded its budget of 50 steps` — once one path goes past that many node steps. Replayed steps count, so pausing and resuming does not reset it. There is no default budget: until you set one, a plain workflow is unbounded.

Three things this demonstrates beyond the counter:

**Each iteration is its own durable step.** The engine numbers steps as it traverses, so the third pass through `ReviewNode` is a different step from the first, with the counter in state committed alongside it. A run that crashes on the third review and is recovered replays the first two from the store and resumes on the third — and the `memoize()` around the reviewer call (Lesson 13.6) is scoped to that iteration, so the verdict already paid for on a given pass is never requested twice.

**Every loop iteration costs LLM calls.** This is Lesson 1.4 again. An unbounded review loop is an unbounded bill.

**Have a plan for hitting the limit.** Escalating to a human beats silently shipping the third draft. That is the natural bridge into Module 15.

### Loops are where agentic systems earn their keep

A loop with an LLM in it is *iterative refinement*: draft, critique, revise, repeat until good enough. That pattern — writer plus critic — is one of the highest-value multi-agent shapes, and it is a three-node workflow with one union return type.

### Key takeaways

- A loop is a node returning an event that re-triggers an earlier node.
- **Declare every possible return type in the union** — the most common workflow bug.
- Returning `StartEvent` restarts the whole workflow.
- The framework bounds loops only if you opt in with `setMaxSteps()`; count in state for the business limit, use the budget as a backstop, and plan for the limit.
- Every iteration is a separate durable step; memoize the LLM call inside it.

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

*(The documentation's branching example names the class `BrancheA1Event` — a stray `e`. Do not copy it into your course.)*

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

The practical consequence, and it is the thing students will trip over: **a branch writing to `$state` is writing to a copy that will be discarded.** If you want data out of a branch, it goes in the `StopEvent` result. Full stop.

Show this failure deliberately on camera — set state in a branch, read it in the merge node, watch it be absent. Then fix it with the result. Five minutes, and the rule sticks.

### Parallel is not concurrent until you say so

The default branch runner executes the branches **one after another**. The isolation, the named results and the merge all work, but the elapsed time is the sum of the branches. For real concurrency, swap the branch runner with `setBranchRunner()`, or override the `branchRunner()` hook in a workflow class:

```php
use NeuronAI\Workflow\Executor\AsyncBranchRunner;

$state = MyWorkflow::make(workflowId: $documentId)
    ->setBranchRunner(new AsyncBranchRunner())
    ->run();
```

`AsyncBranchRunner` runs each branch in an Amp fiber and needs `amphp/amp` installed — Neuron does not require it, and without it the fork fails with `Call to undefined function Amp\async()`. The fibers only overlap while one of them is waiting on I/O, so for branches that call a model, the provider also needs the non-blocking `AmpHttpClient` (from `amphp/http-client`) set with `setHttpClient()`. With both, two model calls complete in the time of the slower one. With only the branch runner, they still queue behind each other.

Concurrent branches share the workflow's node instances, so two branches must not reach the same node: give each branch its own events and nodes.

Branch steps are durable like any other: each node inside each branch is committed as its own step, so a recovered run does not redo the branches that already finished. What happens when a branch pauses for a human is Module 15's business; the short version is that branches pause one at a time.

### When parallel branches pay off

Same shape as Lesson 5.13: **independent, I/O-bound work**, running on `AsyncBranchRunner`. Three agents analysing the same document from different angles. Two API calls that do not depend on each other. Text and image processing of one upload.

Not useful for: sequential dependencies, or trivially fast work where coordination costs more than it saves.

### Key takeaways

- Conditional branching is a union return type; converge by returning a shared event type.
- A `ParallelEvent` subclass with named branches forks; the node accepting that subclass joins.
- Branches end with `StopEvent(result: ...)`; the merge node reads `getResult('name')`.
- Branches run sequentially by default; `AsyncBranchRunner` (set with `setBranchRunner()`) plus `amphp/amp` (and `AmpHttpClient` for providers) makes them concurrent.
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

A string-keyed bag with `set()` and `get()`. Fine for small workflows and prototypes. You can seed it before the run, too: `Workflow::make(workflowId: $id, state: new WorkflowState(['topic' => $topic]))`.

### Its weaknesses, stated plainly

- **Typos are silent.** `$state->get('user_id')` versus `$state->set('userId', ...)` returns null with no complaint.
- **No types.** Everything is `mixed`; static analysis sees nothing.
- **No discoverability.** Nothing tells a new developer what keys exist. You grep.

For a three-node workflow, acceptable. For a system a team maintains, not.

### CustomState

```php
use NeuronAI\Workflow\WorkflowState;

class CustomState extends WorkflowState
{
    protected int $userId = 0;

    public function setUserId(int $userId): CustomState
    {
        $this->userId = $userId;
        return $this;
    }

    public function getUserId(): int
    {
        return $this->userId;
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
        $userId = $state->getUserId();
        //...

        return new StopEvent();
    }
}
```

The second parameter of `__invoke()` may be any subclass of `WorkflowState`; the workflow checks it when it validates the node.

Then inject it. A workflow needs an ID before it runs, and the `Workflow` constructor is `(?string $workflowId, ?WorkflowState $state)`, so for a one-off workflow pass both by name:

```php
$state = Workflow::make(workflowId: 'demo', state: (new CustomState())->setUserId($userId))
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

$state = ExampleWorkflow::make(workflowId: 'demo')->run(); // PHPStan infers CustomState
```

The `@extends` annotation is what makes `run()`'s return type `CustomState` rather than `WorkflowState` for PHPStan and your IDE — the same mechanism `Agent` uses to return an `AgentState`. Tutorials written for older versions inject state as a third constructor argument, after persistence and a resume token; that call fails.

### Why this is the right default for real work

**Typed accessors.** `getUserId(): int` — IDE completion, PHPStan coverage, refactoring support.

**Self-documenting.** The class *is* the list of what this workflow carries. Onboarding becomes "read `OrderWorkflowState`".

**A place for logic.** Derived values belong on the state object, not repeated in four nodes:

```php
class ContentWorkflowState extends WorkflowState
{
    /** @var list<array{draft: string, feedback: string}> */
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

    // PHP 8.5: #[\NoDiscard] turns a bare `$state->hasReachedLimit();` -
    // a check whose answer nobody reads - into a warning.
    #[\NoDiscard]
    public function hasReachedLimit(int $max = 3): bool
    {
        return $this->revisionCount() >= $max;
    }

    public function lastFeedback(): ?string
    {
        // PHP 8.5: array_last() is null on an empty list and, unlike end(),
        // leaves the array's internal pointer alone.
        return \array_last($this->revisions)['feedback'] ?? null;
    }
}
```

Now the loop guard from Lesson 14.1 reads as `$state->hasReachedLimit()` in every node that needs it, defined once.

Two PHP 8.5 additions keep the class honest. `#[\NoDiscard]` makes PHP warn when a caller ignores a method's return value, which for a check like `hasReachedLimit()` is always a bug. `array_last()` returns the last element of an array, or `null` when it is empty, without moving the internal pointer the way `end()` does.

### The serialisation constraint

Critical for everything durable, and worth knowing now so it is not a surprise:

**State is serialised every time a step commits.** Not only when a workflow pauses — after every node, on every run, including a plain in-memory one, because that is what a durable step is (Lesson 13.6). Which means:

- **Resources cannot be serialised.** Database connections, file handles, open sockets. Store an identifier and re-establish the connection inside the node that needs it.
- Same for closures and anything holding a resource or a closure indirectly.

Put a `PDO` in state and the run fails the moment the node that stored it returns: `Serialization of 'PDO' is not allowed`. That is the good news — it fails early, next to the line that caused it, instead of hours later at a pause boundary.

**Store IDs, not objects with connections.** `protected int $userId` rather than a hydrated model carrying a live connection. Services a node needs, such as a database connection or an HTTP client, do not go in state at all. The workflow builds them as a `WorkflowResources` object, once per execution segment, from a `setResources()` factory or a `resources()` hook; they are never persisted, and a continuation builds them again. A node reads them through an optional third `__invoke()` parameter:

```php
use NeuronAI\Workflow\WorkflowResources;

class AppResources extends WorkflowResources
{
    public function __construct(public readonly \PDO $pdo)
    {
        parent::__construct();
    }
}

class LoadUserNode extends Node
{
    public function __invoke(StartEvent $event, CustomState $state, AppResources $resources): StopEvent
    {
        $statement = $resources->pdo->prepare('SELECT name FROM users WHERE id = ?');
        $statement->execute([$state->getUserId()]);
        $state->set('name', $statement->fetchColumn());

        return new StopEvent();
    }
}

$state = Workflow::make(workflowId: 'demo', state: (new CustomState())->setUserId($userId))
    ->setResources(fn (): AppResources => new AppResources($pdo))
    ->addNodes([new LoadUserNode()])
    ->run();
```

The state carries the `int`; the node, running with a live connection, loads the user it needs. A workflow class returns the same object from its `resources()` hook.

**Parallel branches clone the state.** The `data` bag behind `get()`/`set()` is deep-copied for each branch. A subclass holding mutable *objects* in its own properties must define `__clone()` so the copies really are independent; plain scalars and arrays, like `ContentWorkflowState`'s revisions, need nothing.

### Key takeaways

- `WorkflowState` is a string-keyed bag: fine small, weak at scale.
- `CustomState` gives typed accessors, discoverability and a home for derived logic.
- Inject with `Workflow::make(state: ...)`, or the `state()` hook plus `@extends Workflow<CustomState>`.
- **State is serialised at every step commit** — no resources, no connections, no closures.
- Store IDs and re-hydrate inside the node; services come from `resources()` or `setResources()`, never from state.

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

**`yield` emits progress. `return` emits the routing event.** Two channels from one method — that is the whole design, and it is elegant enough to point out. PHP generators, used exactly as intended.

Note that `ProgressEvent` does not implement `Event`. It never routes anything; a node may yield any object at all. Only the returned value has to be an `Event`.

The union `\Generator|FirstEvent` is the framework's documented form, and it earns its place: PHP accepts it, and `export()` reads the `FirstEvent` half to draw the edge. PHPStan does not accept it — a function that yields may only declare generator types, so it reports `generator.returnType` on every `yield`. If your codebase runs PHPStan, declare `\Generator` alone and move the routing into the docblock, `@return \Generator<int, ProgressEvent, mixed, FirstEvent>`. The workflow runs identically; the price is that `export()` no longer sees where the node leads and shows the next node as orphaned.

To receive the stream, call `events()` instead of `run()`. It returns a generator of everything the nodes yield, and the final state is the generator's return value:

```php
$stream = Workflow::make(workflowId: 'demo')
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

Like `run()`, `events()` needs a workflow ID; without one it throws at the call, before you iterate.

### Progress is not durable

Yielded output is live and ephemeral. It is not written to the store, and when a recovered run replays completed steps (Lesson 13.6), those steps' progress events are **not** emitted again — only the returned event is durable. A client that reconnects halfway through has missed what it missed.

So never make correctness depend on a progress event arriving. Anything the application must know goes in state or in the result; progress is for the human watching.

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

**Name progress events for the user, not the developer.** `"Searching the knowledge base"` beats `"RetrievalNode invoked"`. Same principle as the tool-label allowlist in Lesson 7.4 — and the same security concern: do not leak internals.

**Do not yield every detail.** A progress line per document retrieved is noise. One per meaningful phase.

**Yield before slow work, not after.** `yield new ProgressEvent("Researching...")` then do the research. Yielding afterwards tells the user what already finished, which is the wrong half of the information.

### Connecting to the frontend

The stream adapters from Lesson 7.5 apply here. `setStreamAdapter()` takes a factory returning an `AGUIAdapter` or a `VercelAIAdapter`; the adapter turns a workflow's output into protocol events for a browser, and because the workflow calls the factory once per execution segment, each segment gets a fresh adapter. An adapter only encodes what it understands: yield Neuron's portable stream events (`StepStartedStreamEvent`, `ActivityStreamEvent` and friends, in `NeuronAI\Agent\Adapters\Events`) directly, or keep your own `ProgressEvent` and register a translation with the adapter's `mapEvent()`. Add a channel with `setChannel()`, which takes a factory too and returns, for example, a `PusherChannel` or a `RedisChannel`, and a **queued** workflow streams to a client it has no direct connection to.

That is the combination Module 21 builds: long workflow on a worker, live progress in the browser.

### Key takeaways

- Add `\Generator` to the return type; `yield` progress, `return` the routing event.
- Two channels from one method; consume them with `events()` and `getReturn()`.
- Progress is ephemeral: never stored, never replayed.
- Name progress events for users; one per phase; yield before the work.
- Adapters and channels carry workflow progress to the frontend, including from queued jobs.

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

For a PHP audience this is genuinely notable, because PHP's execution model is famously request-scoped. The framework's answer is the durable steps from Lesson 13.5 plus a persistence layer, and it turns "AI does the whole thing" into "AI does the work, a human makes the decisions" — which is the only shape most businesses will actually deploy for anything consequential.

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

The practical consequence: there is nothing to catch, and nothing to be logged as a crash by accident. What you must not forget instead is to *look*. A caller that ignores `isInterrupted()` will treat a paused run as a finished one and read state that has not been written yet. Lesson 15.4 covers the handling.

### Where this changes what you can build

Lesson 5.10's four defence layers included "offered, gated at runtime". This is that layer, and it unlocks a category of application:

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

**`ApprovalRequest`** — the built-in request for the most common case: approving actions. It lives in `NeuronAI\Agent\Interrupt`, alongside `Action`, because the agent's own tool approval (Lesson 15.5) is built on it. Nothing stops a plain workflow node from using it.

**`Action`** — a single decidable item: an identifier, a label, and a description. Several actions in one request means the human decides several things in one interaction, which is the difference between one approval screen and five.

**The payload** — a plain array, keyed however you decide. This course uses the same convention as the agent's tool approval, keyed by action ID: `'approve'`, `'reject'`, or `['reject', 'reason']`. It is a contract between the node and whoever resumes the run, so pick one shape and keep it.

**The reason on a rejection** — more useful than it looks. A rejection with a reason can go straight into the next agent call as guidance, turning "no" into "no, because X" and letting the loop actually improve.

**Returning `InputEvent` on rejection** — this node loops back. Rejection is not failure; it is another iteration. That combination of interruption plus loop is the human-in-the-loop refinement pattern, and it is what Lab 10 builds.

`ApprovalRequest` and `Action` are **outbound only**. `Action` is a read-only value object — its properties are `readonly` and it has no `approve()`, `reject()` or `feedback()` methods. The request describes what is being asked; the answer travels back separately, as the payload. You never mutate the request to record a decision.

> **The documentation's examples do not match the code.** The documentation imports `ApprovalRequest` from `NeuronAI\Workflow\Interrupt`, which does not exist; the class is `NeuronAI\Agent\Interrupt\ApprovalRequest`. Its custom-request example overrides `jsonSerialize()`, which is `final` on `InterruptRequest`, and its resume example names a `runId:` constructor argument that `Workflow` does not have. All three fail on the first run.

### Design guidance for approval requests

**Write the message for the decider, not the developer.** They are seeing this in an email or an admin screen, with no context. `'Should I continue?'` is a poor message. `'Approve a €240 refund for order #4471 — customer reports item arrived damaged'` lets someone decide without opening another system.

**Include enough in the description to decide.** The third `Action` argument is where the substance goes.

**Group related decisions into one request.** Five actions in one request beats five sequential interruptions, each of which is a separate wake-up, notification and wait. Action IDs must be unique within a request; a duplicate is rejected when the request is built, because its decision could never be delivered.

### Key takeaways

- `$this->interrupt($request)` pauses, and on resume returns the payload array.
- `ApprovalRequest` (in `NeuronAI\Agent\Interrupt`) plus `Action` covers approve/reject.
- The request is outbound only; the decision comes back as a plain array whose shape you define.
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
        // Generate an article, once. See Lesson 15.5 for why this is memoized.
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

> **This example generates content before interrupting.** Which is exactly the situation Lesson 15.5 is about. Without the `memoize()` around it, resuming this node re-runs `ContentCreatorAgent` and the human's edit is applied to a *different* draft. Read Lesson 15.5 before you ship anything shaped like this.

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

`awaitEvent()` is `interrupt()` with a `WaitForEventRequest`; `sleepUntil()` is `interrupt()` with a `SleepUntilRequest`. The engine records the deadline but runs no timer — nothing in core wakes up by itself. Your scheduler (cron, a delayed queue job) calls `run(ExecutionRequest::resume())`, with no payload, when the time comes, and the workflow checks the clock itself: before the deadline the run stays suspended, after it `awaitEvent()` returns `null` and `sleepUntil()` returns. For a wait nobody answered, the node never compares clocks. An answer that arrives after the deadline is another matter: the engine still delivers it, and a node that must refuse it reads the clock itself (Lesson 26.10).

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

---
═══════════════════════════════════════════════════════════════

## LESSON 15.4 — Persisting, Detecting and Resuming

**Duration:** 15 minutes
**Type:** Hands-on — the operational heart of Module 15

### Learning objectives

Wire the full pause-and-resume cycle, including the storage that makes it survive a process restart.

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

The framework has already persisted the run: its completed steps, its state, and the request itself. What *you* store is the workflow ID and whatever your UI needs, so your application can find the pending decision, present it, and reconnect the answer. A `start.php` script can write the request to a JSON file, which is exactly enough for a CLI:

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

`ExecutionRequest::resume()` only builds an execution request, an immutable value from `NeuronAI\Workflow\Executor`; nothing is staged on the workflow, and `run()` is what executes it. Pass the same request to `events()` and the continuation streams, exactly like a fresh run (Lesson 14.4). The shorthand `submitInputs($payload)->run()` reads the pending run first, so it fails early when nothing is waiting, and it captures the fences of question 3 below; the agent's approval API (Lesson 15.5) is built on it.

Run a `start.php` and a `resume.php` built from these snippets as two separate commands. The proposal generated before the interrupt prints once, in the first process, and never in the second. Run `resume.php` a second time with the same ID and it fails with "No run in flight": a completed run cleans up after itself.

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

Now there is nothing to store on the side: the order ID *is* the way back to the run. It also enforces a rule you would otherwise have to build — **one live run per workflow ID**. Calling `run()` while a run for that key is suspended throws `RunInFlightException`, whose message names what settles it and whose `interrupt` property carries the pending request. The Agent uses exactly this mechanism, with its thread ID as the workflow ID (Lesson 15.5).

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

- **`EloquentPersistence($modelClass)`** — an Eloquent model over a table of a different shape: a primary key of its own plus a unique constraint on `(partition, key)`. The `workflow_store` table that neuron-laravel 2.0.0 ships has the composite key above instead, and on it the first step commit fails. In a Laravel application use `DatabasePersistence` over the framework's own connection, `new DatabasePersistence(DB::connection()->getPdo())`; Module 18 does the wiring.
- **`RedisPersistence($redis, prefix: 'neuron:workflow:')`** — one hash per run, needs `ext-redis`. It sets no TTL: cleanup is the workflow's job, so configure eviction not to drop live runs.

Use `FilePersistence` for CLI and development — it is restart-durable but meant for a single process. Use the database, Eloquent or Redis backends for anything multi-worker or production; each of their writes is a conditional, atomic operation, which is what the next section relies on.

### The four operational questions

Nobody's tutorial covers these and every production system needs them.

**1. Who is notified?** The interrupt does not send an email. Your code does. Wire the notification where you detect `isInterrupted()`.

**2. What if nobody responds?** Give the request an `expiresAt` and schedule a job for that time that calls `run(ExecutionRequest::resume())`, with no payload. The workflow checks the deadline itself and the node takes its timeout branch — escalate, expire, or auto-reject is a decision in your node, not a cleanup script. For runs you simply want gone, `abandon()` discards a paused run and frees its workflow ID; called with no run ID it returns `false` when there was nothing to discard, and with one it throws instead (Lesson 22.4).

**3. How do you prevent double-resume?** Two managers open the same approval link and both click. The engine handles the race: every mutation is a conditional write against the run's control record, so only one continuation wins, an accepted answer cannot be replaced by a conflicting one, and a resume of a completed run fails with "No run in flight". What the engine cannot know is *which* request a delayed delivery was meant for. A queued job that may be retried should carry the run ID and execution attempt it observed on the paused state — `getRunId()` and `getExecutionAttempt()` — and pass them as fences:

```php
$state = $workflow->run(ExecutionRequest::resume(
    $payload,
    expectedRunId: $runId,
    expectedExecutionAttempt: $attempt,
));
```

If the run has moved on, the call is refused before it touches anything, and the fence that caught it decides the exception. A different run ID — a new generation, or a run that has already finished and been cleaned up — throws `StaleWorkflowRunException`. The same run on a later execution attempt — another worker already continued it, and it is running or paused again — throws a plain `WorkflowException` whose message begins "Stale continuation". A stale run ID means the run is gone: treat it as "already handled". A stale attempt only means the run has moved on, and a job that may be retried must not treat it as a no-op: Module 22's resume job reads the run before it decides (Lesson 22.3). Your UI should still mark the request resolved so the second manager sees "already decided" rather than an error.

**4. What about a deployment in between?** The persisted state is serialised PHP, and it contains your classes: the state object, the events, the interrupt request. A deployment that renames a class or changes a property will break deserialisation of in-flight runs. Either drain before deploying, or version your interrupt requests. The same applies to upgrading Neuron itself: runs suspended by an older version of the store format cannot be resumed by a newer one.

That last one is the sharp edge, and it is worth dwelling on. Long-lived serialised PHP objects across deployments is a known hard problem, and interruption puts you squarely in it. The mitigation — keep interrupt requests and state small, flat, and change them rarely — is a design rule, not something to discover during an incident.

### Key takeaways

- Durable persistence is mandatory for cross-process resumption; `FilePersistence` for CLI, a database, Eloquent or Redis backend for production.
- `run()` returns; check `isInterrupted()`, store `getWorkflowId()` and show `getInterruptRequest()`.
- Resume with the same class, persistence and workflow ID: `run(ExecutionRequest::resume($payload))`.
- The workflow ID is the handle, and you bind it before the run; the run ID is a generation stamp. Declare `workflowId()` to resume by business key.
- Four operational questions: notification, timeout (`expiresAt`), double-resume (conditional writes and fences), deployment compatibility.

---
═══════════════════════════════════════════════════════════════

## LESSON 15.5 — Memoization, Conditional Interrupts and Middleware

**Duration:** 16 minutes
**Type:** Hands-on

### Learning objectives

Avoid re-running expensive work on resume, interrupt conditionally, and gate tool calls with middleware.

### The re-execution problem

This section contains the most important correctness warning in the course.

When a workflow resumes, completed nodes are not run again — their results are replayed from the store. But **the node that was interrupted is re-executed from the top, including the code before the interruption.** That is how `interrupt()` gets to return the payload: execution has to reach it again.

Read that carefully, because it has real cost. If your node calls an LLM, then interrupts, then resumes — **the LLM call runs again.** You pay twice, you wait twice, and because of Lesson 1.5 you may get a *different answer* the second time.

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

Make this visible: have the memoized closure print a line, and across `start.php` and `resume.php` that line appears exactly once.

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

Whether a tool requires approval is declared on the tool — Module 5 covers the declaration API. A tool can declare its own policy, conditional on its arguments; a string return counts as "yes" and is the reason shown to the approver:

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

Purchases under €100 proceed; larger ones wait for a human. This is Lesson 5.10's fourth layer, now concrete — and it is a far better product than either always-allow or always-block.

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

Module 22 builds this into a real Laravel approval screen.

### ToolSearchMiddleware

```php
$agent->addGlobalMiddleware(new ToolSearchMiddleware($toolPool));
```

For agents with large tool catalogues. Rather than sending every schema on every request — Lesson 1.3's compounding cost — it gives the model a `tool_search` tool and loads the matching tools from the pool on demand, five at most by default.

This is the answer to "what if I have 200 tools?", which is the natural question after Module 5.

Note the shape: `addGlobalMiddleware()`, not `addMiddleware(InferenceNode::class, ...)`. Lesson 2.3 attached `Summarization` to `InferenceNode`, the base of both the chat and structured-output nodes, and that is enough for a middleware that only edits what the model is sent. One that *contributes tools* has to run before every node: after an approval pause the run continues at `ToolNode`, which must find the tools the model was offered before the pause. Register this one on `InferenceNode` alone and the approved call fails with "The tool … is not registered on this agent".

### Key takeaways

- **A resumed node re-executes from the top** — including LLM calls, with possibly different results.
- `memoize('name', fn)` persists and replays; wrap everything expensive or non-deterministic before an interrupt.
- The answer is the return value of `interrupt()`; a node may wait more than once if it reaches its waits in the same order every time.
- `interruptIf()` keeps approvals meaningful and returns `null` when nobody was asked.
- Agent tool approval is declared on the tool and answered with `submitApprovalDecisions()->run()`; the thread is the handle. `ToolSearchMiddleware`, registered globally, handles large catalogues.

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

**No special multi-agent API.** That is the point of Lesson 2.3 arriving for the final time: an agent runs inside a node, and composing nodes is what workflows do.

### Cost discipline

A four-agent sequential pipeline is at minimum four model calls, usually more if any of them use tools. A critic loop running three rounds is six-plus.

Two mitigations worth teaching:

**Different models per agent.** The researcher and the critic may need a strong model; the formatter does not. Lesson 3.6's provider swap is per-node here, and it is one of the framework's better arguments in a multi-agent context.

**Bound every loop.** Lesson 14.1's counter, non-negotiable.

### Key takeaways

- Ask whether one agent with more tools would do; often it would.
- Independent review is the strongest case for multi-agent.
- Four patterns: sequential, supervisor, parallel, critic loop.
- No special API — agents run inside nodes.
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
use App\Workflow\Events\ProgressEvent;
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
            ->setThreadId($state->getWorkflowId() . ':research')
            ->chat(new UserMessage("Research this topic thoroughly: {$event->topic}"))
            ->getMessage()
            ?->getContent() ?? '';

        $state->set('sources_used', $this->countSources($findings));

        return new ResearchCompleted($event->topic, $findings);
    }
}
```

The node is a thin adapter. All the intelligence — provider, instructions, tools — lives in `ResearchAgent`, which is unchanged and still works standalone.

**Say that explicitly on camera:** `ResearchAgent` does not know it is in a workflow. You can still unit-test it, still call it directly, still reuse it in a different pipeline. The node is glue.

`getMessage()` is nullable — it is `null` when the run paused before any inference, or ended with no message at all — hence the `?->` and the fallback.

### An agent is a workflow inside a node

`Agent` extends `Workflow`: `chat()` runs the agent's own graph of nodes to completion and returns its `AgentState`. So a multi-agent workflow is, literally, workflows running inside the nodes of a workflow. Three consequences follow.

**The agent is called, not added.** An agent is not a node — you cannot pass it to `addNodes()`. The node is where you decide what goes into the agent and what comes out.

**The inner run is separate.** A sub-agent has its own identity: an agent's workflow ID is its conversation thread ID, and the framework never makes one up, so a sub-agent with no thread ID throws before it runs. Bind a thread derived from the outer workflow's ID — `->setThreadId($state->getWorkflowId() . ':research')` — and give each sub-agent its own suffix. With no persistence and no message store configured, the sub-agent runs on in-memory persistence and an in-memory history: it shares nothing with the outer workflow's state or store. That is usually what you want for a pipeline stage. Be careful with the one case where the thread is fixed *and* the store is durable: a reviewer inside a loop that always uses the same thread ID and a `messageStore()` backed by a file or a database accumulates every earlier iteration's conversation. A looped sub-agent should keep the default in-memory store, use a thread per iteration (`':review:' . $state->revisionCount()`), or reset its conversation. The outer workflow's durability still covers it at the step level — once `ResearchNode` completes, its result is committed, and a resume or recovery replays it instead of calling the agent again. What is *not* covered is the node that is running when the pause or crash happens; wrap its agent calls in `memoize()` (Lesson 15.5), as Lab 10 does.

**A sub-agent's pause does not propagate.** If you give a sub-agent an approval-gated tool (Lesson 15.5), its `chat()` returns an interrupted `AgentState`, and the node reading `getMessage()` would receive the pending tool call rather than an answer. Keep approval-gated tools out of pipeline agents, or check `isInterrupted()` in the node and raise the question to the outer workflow with its own `interrupt()`.

### Structured output between agents

Passing prose between agents loses information and invites misinterpretation. Pass typed objects instead:

```php
class ReviewNode extends Node
{
    public function __invoke(DraftCompleted $event, WorkflowState $state): DraftCompleted|ArticleApproved
    {
        $verdict = ReviewerAgent::make()
            ->setThreadId($state->getWorkflowId() . ':review')
            ->structured(new UserMessage($event->draft), Verdict::class);

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
        $draft = WriterAgent::make()
            ->setThreadId($state->getWorkflowId() . ':draft')
            ->chat(/* ... */)
            ->getMessage()
            ?->getContent() ?? '';

        return new DraftCompleted($draft);
    }
}

class FormatNode extends Node
{
    public function __invoke(ArticleApproved $event, WorkflowState $state): StopEvent
    {
        // Cheap model — mechanical transformation
        $formatted = FormatterAgent::make()
            ->setThreadId($state->getWorkflowId() . ':format')
            ->chat(/* ... */)
            ->getMessage()
            ?->getContent() ?? '';

        return new StopEvent(result: $formatted);
    }
}
```

Each agent declares its own provider. Cost tiering across a multi-agent system is a property of how you wrote the agents, not something you configure separately.

### Key takeaways

- The node is a thin adapter; the agent stays independent and testable.
- An agent is a workflow: call it from a node, memoize the call if the node can pause, and keep approval-gated tools out of sub-agents.
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
        $result = FactCheckAgent::make()
            ->setThreadId($state->getWorkflowId() . ':fact-check')
            ->structured(
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

Subscribe Inspector to the workflow and its agents (Module 10) and read input tokens per node across the run. If they grow linearly through the pipeline, you are accumulating. That number is your optimisation target, and it is visible rather than guessed.

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
Queue worker  → run the workflow → stream progress over a channel
                                  → persist any interruption
Human         → responds via UI/email
Queue worker  → resume the workflow → complete
Client        → receives progress and the result over the transport
```

Four pieces you already have:

- **Persistence** (Lesson 15.4) for interruption state
- **Stream adapters and channels** (Lesson 7.5): the adapter shapes the events, the channel (`setChannel()`) pushes them to a transport
- **Workflow ID** as the correlation key
- **Queue** as the execution context

### What changes on a worker

**`pcntl` and `posix` become available**, so parallel tool calls (Lesson 5.13) and parallel evals (Lesson 10.6) work.

**Monitoring must be wired where the worker builds its agents.** Inspector is a listener you subscribe on each agent and workflow (Lesson 10.2); nothing is attached globally. A worker has no end-of-request, so the subscriber sends each trace when the workflow it started ends. The single most likely misconfiguration in an async deployment is a worker whose agents were never subscribed, which produces no traces at all and no error.

**No HTTP connection to the user.** Which is why streaming channels matter — attach a `PusherChannel` or `RedisChannel` with `setChannel()`, the worker publishes through it, the browser listens.

**Timeouts are yours to manage.** Queue workers have time limits. A workflow that runs for ten minutes needs a worker configured for it, or needs to interrupt and resume across jobs. And a worker killed mid-run — timeout, memory limit — leaves the run marked as running. An agent holds a ten-minute lease by default, after which the next run supersedes the dead one; a plain workflow opts in with `setLeaseTimeout($seconds)`. Pick a lease longer than your slowest node.

### The pattern that ties Part IV together

For a long, human-gated workflow, each segment between interruptions is its own job:

```
Job 1: run until the approval interrupt → persist → notify the manager → end
       (worker is free)
Job 2: triggered by the approval → resume → run to completion or the next interrupt
```

The worker is not blocked waiting. Between segments there is no process at all — only rows in `workflow_store`, under the run's workflow ID.

Job 2 should carry the run ID and execution attempt it saw when the interrupt was recorded, and pass them in `ExecutionRequest::resume($payload, expectedRunId: ..., expectedExecutionAttempt: ...)` to `run()` (Lesson 15.4). A retried job then fails cleanly instead of delivering a stale answer to a run that has moved on.

That is what "resume even across different sessions" means operationally, and it is worth drawing on a slide. It is also, for a PHP audience used to request-scoped execution, a genuinely satisfying resolution: PHP's statelessness stops being a limitation and becomes the deployment model.

### Module 15–16 assessment

1. Build a three-agent sequential workflow with structured output at each boundary.
2. Add a critic loop with a bounded counter and a plan for hitting the limit.
3. Add an interruption before the final action; persist it; resume from a separate script.
4. Wrap every pre-interrupt LLM call in a `memoize()` and verify it is not re-executed.
5. Measure input tokens per node and reduce the accumulation.

---
═══════════════════════════════════════════════════════════════

## LAB 10 — The Content Factory

**Duration:** 40 minutes
**Covers:** everything in Part IV

### Goal

Research → draft → review loop → human approval → publish. It is the canonical multi-agent workflow and it exercises loops, state, streaming, interruption, memoization and persistence in one artefact.

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

        $verdict = $this->memoize('verdict', fn (): Verdict => ReviewerAgent::make()
            ->setThreadId($state->getWorkflowId() . ':review:' . $state->revisionCount())
            ->structured(new UserMessage($event->draft), Verdict::class));

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

Every Part IV concept in one class: a union return type (14.1), a bounded loop with a plan for the limit (14.1), custom state (14.3), streaming progress (14.4), a memoized agent call (13.5), and structured output at an agent boundary (16.2). The reviewer gets a thread per iteration, so each pass starts a fresh conversation.

### The approval node

```php
class ApprovalNode extends Node
{
    public function __invoke(ArticleApproved $event, ContentState $state): ArticleEdited
    {
        $payload = $this->interrupt(
            new ContentReviewInterrupt(
                message: \sprintf(
                    'Article ready after %d revision(s). Review and edit before publishing.',
                    $state->revisionCount()
                ),
                content: $event->draft
            )
        );

        return new ArticleEdited($payload['content'] ?? $event->draft);
    }
}
```

The human edits rather than approves — Lesson 15.3's collaboration pattern. The edited text comes back in the payload; if the reviewer sends nothing for `content`, the draft goes through unchanged.

### The workflow

```php
/** @extends Workflow<ContentState> */
class ContentWorkflow extends Workflow
{
    protected function state(): ContentState
    {
        return new ContentState();
    }

    protected function nodes(): array
    {
        return [
            new ResearchNode(),
            new DraftNode(),
            new ReviewNode(),
            new ApprovalNode(),
            new PublishNode(),
        ];
    }
}
```

The nodes are typed to `ContentState`, so the workflow must be seeded with that class: the `state()` hook makes every run start with a `ContentState` (seeding it with a plain `WorkflowState` would fail the nodes' type declaration), and the `@extends` annotation tells static analysis that `run()` returns one — so `$state->revisionCount()` type-checks at the call site without a cast.

### The memoization demonstration

Do this deliberately. It is the most valuable twenty minutes in Part IV, because it turns an abstract warning into a bug you have personally caused.

Write `ApprovalNode` so the draft is *generated* inside it, un-memoized:

```php
// DELIBERATELY WRONG — reproduce the bug before fixing it
$draft = WriterAgent::make()
    ->setThreadId($state->getWorkflowId() . ':draft')
    ->chat(new UserMessage($brief))
    ->getMessage()
    ?->getContent() ?? '';

$payload = $this->interrupt(new ContentReviewInterrupt('Review before publishing.', $draft));
```

Run it, interrupt, resume. The draft regenerates and **the resumed version differs from the one the human approved.**

Then wrap it:

```php
$draft = $this->memoize('draft', fn (): string => WriterAgent::make()
    ->setThreadId($state->getWorkflowId() . ':draft')
    ->chat(new UserMessage($brief))
    ->getMessage()
    ?->getContent() ?? '');
```

Re-run. Same draft. Same content the human saw.

That is not an efficiency argument. It is a demonstrable correctness failure with a one-line fix, and it is the reason Lesson 15.5 exists.

### Running it

```php
// The workflow ID is yours to bind; the framework never generates one.
$workflow = ContentWorkflow::make(workflowId: UniqueIdGenerator::generateId('workflow_'))
    ->setPersistence(new FilePersistence(__DIR__ . '/../storage/workflows'));

$stream = $workflow->events();

foreach ($stream as $event) {
    if ($event instanceof ProgressEvent) {
        echo "  {$event->message}\n";
    }
}

$state = $stream->getReturn();

if (!$state->isInterrupted()) {
    echo "\nPublished.\n";
    exit(0);
}

$id = $state->getWorkflowId();

// The fences travel with the request: the run ID and the execution attempt.
\file_put_contents(
    __DIR__ . "/../storage/pending/{$id}.json",
    \json_encode([
        'run_id' => $state->getRunId(),
        'execution_attempt' => $state->getExecutionAttempt(),
        'request' => $state->getInterruptRequest(),
    ], JSON_PRETTY_PRINT)
);

echo "\nAwaiting review. Workflow ID: {$id}\n";
echo "Edit request.content in storage/pending/{$id}.json and run: php resume.php {$id}\n";
```

`events()` is the streaming terminal from Lesson 14.4: a generator (it is always a `Generator`) that yields whatever the nodes yield, as they yield it, and returns the final state from `getReturn()`. It yields framework objects too — among them the event that marks the pause — which is why the loop filters on `ProgressEvent`. As with `run()`, the pause is not thrown; you read it off the returned state.

And the resume script, in a separate process:

```php
$pending = \json_decode((string) \file_get_contents(__DIR__ . "/../storage/pending/{$id}.json"), true);

$state = ContentWorkflow::make(workflowId: $id)
    ->setPersistence(new FilePersistence(__DIR__ . '/../storage/workflows'))
    ->run(ExecutionRequest::signal(
        'content.reviewed',
        ['content' => $pending['request']['content']],
        expectedRunId: $pending['run_id'],
        expectedExecutionAttempt: $pending['execution_attempt'],
    ));

echo $state->get('published');
```

The signal carries the run ID and execution attempt recorded at the interrupt, so a duplicated or retried delivery fails instead of answering a run that has moved on. The completed research, draft and review steps are not run again. Only `ApprovalNode` re-executes, receives the edited content, and hands it to `PublishNode`.

Editing a JSON file on disk as the "approval UI" is exactly right for a CLI lab. It makes the mechanism visible, and Module 22 replaces it with a real admin screen.

### Acceptance criteria

- The review loop runs at most three times, and hitting the limit escalates rather than failing.
- Killing the PHP process after the interrupt and resuming from a fresh process produces the published article.
- With `memoize()` in place, the published content is byte-identical to what the interrupt request showed the human. Without it, it is not — prove both.
- Progress lines appear as the workflow runs, not all at the end.

### Extensions

1. Add a parallel branch: fact-check and SEO analysis run concurrently after approval, merged before publishing.
2. Add `interruptIf()` so only articles scoring below 8 require human review.
3. Move execution to a queue worker and stream progress over a websocket.

---

## PART IV — VERIFICATION LIST (ADDITIONS)

| # | Issue | Where |
|---|---|---|
| 30 | `init()`/`run()` vs `start()`/`getResult()` — older execution APIs across doc pages and blogs. On v4, neither exists: `run()` on the workflow returns the final state, `events()` streams | Workflow, throughout |
| 31 | `Workflow::make(new WorkflowState(), $persistence, 'id')` — the old constructor, still in blog posts. On v4 it is `make(workflowId:, state:)` plus `setPersistence()` | Interruption, blogs |
| 32 | `Edge` class and `addEdges()` — removed in v2, still in v1 material | Older tutorials |
| 33 | `BrancheA1Event` — misspelling in the branching example | Loops & branches |
| 34 | Missing commas after `message:` in several `ApprovalRequest` examples | Human in the loop |
| 35 | Missing semicolon after `parent::__construct($message)` in `ContentReviewInterrupt`; on v4 the class extends `WaitForEventRequest` and overrides `metadata()` (`jsonSerialize()` is final) | Human in the loop |
| 36 | `ContentReviewInterrupt` invoked with a positional second argument after a named first | Human in the loop |
| 37 | `CustomState` injection: `Workflow::make(workflowId:, state:)` or the `state()` hook | Managing the state |
| 38 | Workflow streaming: `events()` on the workflow, `getReturn()` for the final state (no handler, no `streamEvents()`) | Workflow streaming |
| 39 | `ApprovalRequest` imported from `NeuronAI\Workflow\Interrupt`; it lives in `NeuronAI\Agent\Interrupt`. `StartEvent`/`StopEvent`/`Event` live in `NeuronAI\Workflow\Events` | Human in the loop |
| 40 | `WorkflowInterrupt` caught from `run()`, `getRequest()`, `init($request)` — gone: a pause is a returned state (`isInterrupted()`), resume is `run(ExecutionRequest::resume($payload))`; `checkpoint()` is the deprecated name of `memoize()` | Human in the loop |

Running total: **40 items.**

---

**END OF PART IV**

*Next: Part V — Laravel. Module 17 (SDK setup), Module 18 (agents as first-class citizens), Module 19 (tools that touch your application), Module 20 (RAG on application data).*
