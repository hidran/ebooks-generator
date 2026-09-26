# Chapter 13 — The Event-Driven Model

::: {.callout .callout-warning}
[Before you write any workflow code]{.callout-title}

A workflow runs by calling `run()` on the workflow itself, and it returns the final state:

```php
$state = Workflow::make()->addNodes($nodes)->run();
```

Tutorials written for older versions call `start()` or `init()` and go through a handler object; neither exists in this book's version. The constructor is `(?string $workflowId, ?WorkflowState $state)`, so material that passes a persistence object or a `resumeToken:` argument to it fails. And the documentation itself shows nodes with a third `WorkflowResources $resources` parameter that the code rejects: a node's `__invoke()` must take exactly two parameters, the event and the state.

Appendix A, items 30 to 32.
:::

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

The runnable version of every listing below is at [`chapters/Ch13`](https://github.com/hidran/neuronai-php-book/tree/main/chapters/Ch13), in the companion repository. Clone it, run `composer install`, and the examples work against a local Ollama with no API key.
:::

## 13.1 What a Workflow Is

### The definition

A workflow is an event-driven, node-based way to control the execution flow of an application.

Your application is divided into **Nodes**, which are triggered by **Events**, and which themselves return Events that trigger further nodes. Combine them and you can express arbitrarily complex flows.

The documentation offers a comparison worth borrowing: **"It's like n8n at code level."** If you have seen a visual automation tool, that lands immediately — boxes connected by arrows, except the boxes are PHP classes and the arrows are types.

### A node can be anything

From a single line of code to a complete agent. Arbitrary inputs and outputs, passed around by events.

That flexibility is the point. A node might:

- Call an LLM
- Query your database
- Run a RAG retrieval
- Send an email
- Wait for a human
- Be an entire `Agent` doing its own tool-calling loop

### The statement from Section 2.3, in the source

> Agent and RAG classes are workflows themselves. They represent ready-to-use implementations of the most common patterns for tool calls, retrieval and structured output. Workflow allows you to program your agentic system completely from scratch. Agent and RAG can be used inside a Workflow to complete tasks as any other component.

This is why Chapter 2 insisted on it. Part IV is not a new topic — it is the layer that was underneath Parts II and III all along. That is literal, not a figure of speech: `Agent` is declared as `class Agent extends Workflow`, and the tool-calling loop you used in Part II is a set of nodes routed by the same engine you are about to program directly.

### What makes NeuronAI's workflow distinctive

The documentation names two capabilities, and a third sits underneath both:

**Streaming** — a multi-agent system can push updates to clients as it runs.

**Interruption** — the workflow can pause mid-process, ask for human input, wait, and continue from the node that paused — even hours or days later, in a different process.

**Durability** — every node that completes is committed to a store as a *step*. A run that crashes, fails or pauses does not start again from the top: the completed steps are replayed from the store, and only the unfinished work runs.

The third is what makes the second possible. Most workflow engines can pause; few can pause *inside* a node, survive a process restart, and continue with human feedback injected at the point it stopped, without redoing the expensive work that came before. Section 13.5 shows the durable steps with a crash you can run; Chapter 15 builds interruption on top of them, and it is the strongest single argument for the framework.

### Key takeaways

- Nodes triggered by events, returning events that trigger further nodes.
- A node is anything from one line to a whole agent.
- Agent and RAG *are* workflows; this is the substrate, not an add-on.
- Streaming, interruption and durable steps are the distinguishing capabilities.

## 13.2 Node, Event, State

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
use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
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

The signature is strict: exactly two parameters, an event first and a `WorkflowState` (or a subclass of it) second, and a return type made of events. The workflow validates every node by reflection before it runs anything, so a malformed signature fails immediately with the node's name in the message.

### The idea that makes it click

**The method signature is the graph.**

```text
public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
```

Read it as a wiring statement: *this node runs when a `StartEvent` appears, and when it finishes it emits a `FirstEvent`.*

There is no separate edge definition, no configuration file, no `addEdge()` call. **The type hints are the wiring.**

Let that sit, because everything else in Part IV follows from it:

- Want a loop? Return the event that triggers an earlier node.
- Want a branch? Declare a union return type.
- Want to know the graph? Read the signatures.

::: {.callout .callout-warning}
[No `Edge` class]{.callout-title}

There is no `Edge` class and no `addEdges()`: the event types are the edges. If you find a tutorial using `new Edge(NodeA::class, NodeB::class)`, it was written for a much older version of the framework. Appendix A, item 32.
:::

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

`set()` and `get()`, plus `has()`, `delete()`, `only()` and `all()`. Available to every node — and, because state is saved with every completed step (Section 13.5), it has to be serialisable. Section 14.3 spells out what that rules out.

### Events vs state: when to use which

A distinction people consistently get wrong, so here it is explicitly:

**Events carry the message.** What this specific step produced, passed to the next specific step. Ephemeral, directional, typed.

**State carries the context.** Things many nodes need: the user, the tenant, accumulated results, configuration. Persistent across the whole run.

The heuristic: **if only the next node needs it, put it in the event. If several nodes need it, or you need it after the run, put it in state.**

Overusing state produces a workflow where every node reads and writes a global bag — which is a workflow in name only, because the data flow is invisible again. Overusing events produces enormous event classes that pass everything along. Both extremes are worse than the balance.

### Key takeaways

- Event = plain class implementing `Event`; `StartEvent` and `StopEvent` are built in.
- Node = class with `__invoke(Event, WorkflowState): Event` — exactly two parameters.
- **The method signature is the graph** — no edges to declare.
- Events for the message between two steps; state for shared context.

## 13.3 A Single-Step Workflow

### The whole thing

```php
namespace App\Neuron;

use NeuronAI\Workflow\Node;
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
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

$state = Workflow::make()
    ->addNodes([
        new InitialNode(),
    ])
    ->run();

echo $state->get('answer'); // Hello World!
```

`StartEvent` in, `StopEvent` out. One node. `run()` returns the final `WorkflowState`.

### The lifecycle

1. `Workflow::make()` builds the workflow. Its constructor takes two optional arguments, a workflow ID and an initial state; you need neither yet.
2. `addNodes()` registers the nodes. **Order in the array is not execution order** — the events decide that. The array is a registry, not a sequence.
3. `run()` executes: it gives the run an identity, emits `StartEvent`, finds the node whose signature accepts it, runs it, commits the result as a step, takes the returned event, finds the node that accepts *that*, and repeats until `StopEvent`. It returns the final state.

There is no intermediate object between building a workflow and running it. `run()` and its streaming sibling `events()` (Section 14.4) are the only two ways to execute one, and both are called on the workflow itself.

Point 2 deserves emphasis. Coming from procedural pipelines, the natural assumption is that the array order matters. It does not, and understanding why is understanding the model.

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

$state = GreetingWorkflow::make()->run();
```

The engine calls `nodes()` fresh at the start of every execution segment, so the graph is always built from the workflow's current configuration — which matters once a run can pause in one process and continue in another.

### Is this useful?

By itself, no. But it is the right place to start because it isolates the mechanics from the complexity, and because the next section only adds one idea to it.

### Key takeaways

- `Workflow::make()->addNodes([...])->run()` returns the final state; there is no handler.
- `addNodes()` is a registry, not a sequence — events determine order.
- Execution runs from `StartEvent` to `StopEvent`.
- In a subclass, the `nodes()` hook supplies the graph.

## 13.4 Multi-Step: Events as Wiring

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

$state = Workflow::make()
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

Strip away everything except the three signatures:

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

Keep events small. An event should carry what the *next* node needs, not everything accumulated so far. Large shared context belongs in state (Section 14.3). An event that grows to fifteen properties is telling you its data belongs in state.

### Key takeaways

- Three nodes, three signatures, one graph.
- The type declarations are the wiring — readable and IDE-navigable.
- Name events as past-tense domain facts, not `FirstEvent`.
- Keep events small; put shared context in state.

## 13.5 Durable Steps

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

Any process that can build `ReportWorkflow::make(reportId: 42)` and reach the same store can find this run. There is no table mapping your records to engine-generated IDs, because the business key *is* the storage location. A workflow that declares nothing gets a generated ID, readable from `$state->getWorkflowId()` after the run starts.

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

::: {.callout .callout-warning}
[`checkpoint()` is the old name]{.callout-title}

Older tutorials use `checkpoint()`. It still exists, deprecated, and simply calls `memoize()`. Write `memoize()`.
:::

### Watching it work

`ResearchNode`, the first step, is the obvious two-liner: it consumes `StartEvent`, prints `- ResearchNode: calling the slow research service`, and returns a `ResearchDone` event carrying its notes.

The companion repository runs the workflow twice against a `FilePersistence` directory. The first attempt fails in `PublishNode`; the second is a brand-new `ReportWorkflow` object that shares nothing with the first except the directory and the workflow ID it declares. It could just as well be a different process on a different day:

```php
$storage = \sys_get_temp_dir() . '/neuron-book-ch13';
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

Whichever you choose, one workflow ID is one partition, and every write is a conditional write against the run's control record, so two workers cannot both advance the same run. Chapter 15 relies on all of this to pause a run for a human; Chapter 22 puts it on a real database.

### Key takeaways

- Every completed node is committed as a durable step; a recovered run replays completed steps instead of re-executing them.
- The workflow ID names the run in the store; declare it with `workflowId()` as a business key. The run ID is a per-attempt stamp.
- One live run per workflow ID; a plain `run()` recovers a failed run automatically.
- `memoize('name', fn () => ...)` makes expensive work inside a node replay-safe. It is not exactly-once: use idempotency keys for side effects.
- Completion deletes the run's records by default.

## 13.6 Why Not Just Write a Script?

### The objection

The documentation raises it itself, which is a good sign:

> "This sounds great, but why can't I just write a regular PHP script with some if-statements and functions?"

And it admits: *"It's a fair question, and one I heard a lot while building Neuron."*

### The honest answer for simple cases

**For a three-step linear process, a script is better.** Fewer files, less indirection, easier to read. The framework's own answer concedes this — the potential is not visible when the use case is simple, and that is normal.

Do not oversell it to yourself. Adopting workflows for everything produces a codebase where a function call became four classes, and you will resent it.

### Where the script breaks

The documented answer lists the conditions, and each maps to a real cost:

**Multiple branches run concurrently.** Doing this in a script means `pcntl_fork` and manual result collection. Section 14.2 shows it as a return type.

**Several loops with intermediate checkpoints.** Doable with `while`, until you need to know which iteration you were on after a crash. In a workflow every iteration is its own durable step, so the engine already knows.

**Streaming real-time updates.** A script can echo. It cannot easily emit structured progress events from arbitrary depth without threading a callback through every function.

**Pause, wait, resume.** This is the one that is not a matter of effort. Persisting every completed step, stopping mid-node, continuing in a different process hours later without repeating the work already done, and guaranteeing that two workers never advance the same run — you cannot write that in a script without building a workflow engine. And if you build one, you have built Section 13.5.

### The four development benefits

From the documentation:

**Model and maintain complex scenarios.** From a few steps up to iterative loops with checkpoints, using the same building blocks.

**Human in the loop.** Deploy AI in sensitive areas because a human is always in the loop for critical decisions.

**Streaming.** Real-time updates to the client during execution.

**Debugging with Inspector.** Instead of wondering why the workflow made a decision, see exactly what happened at any node.

That last one connects to Chapter 10. The engine dispatches an event as each node starts and ends, and any observer — Inspector included — turns those into a trace of named steps. A script shows a stack trace.

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
