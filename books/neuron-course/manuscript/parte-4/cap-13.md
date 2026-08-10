# Chapter 13 — The Event-Driven Model

::: {.callout .callout-warning}
[Before you write any workflow code]{.callout-title}

The workflow documentation contains **two different execution APIs** across its own pages:

```php
// v3 style — Multi Step Workflow page
$handler = Workflow::make()->addNodes([...])->init();
$handler->run();

// v2 style — Loops & Branches page, and most blog posts
$state = Workflow::make()->addNodes([...])->start()->getResult();
```

The v2 style also shows `Workflow::make(new WorkflowState(), $persistence, 'id')` and an `Edge` class that **no longer exists in v3** — the event-driven model replaced it entirely.

Run one minimal workflow against your installed version and settle two things: `init()`/`run()` versus `start()`/`getResult()`, and the `Workflow` constructor signature. This part uses the v3 `init()`/`run()` form throughout. Almost every blog post you find will use the other one. Appendix A, items 30 to 32.
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

This is why Chapter 2 insisted on it. Part IV is not a new topic — it is the layer that was underneath Parts II and III all along.

### What makes NeuronAI's workflow distinctive

The documentation names two capabilities:

**Streaming** — a multi-agent system can push updates to clients as it runs.

**Interruption** — the workflow can pause mid-process, ask for human input, wait, and continue exactly where it left off — even hours or days later.

The second one is unusual. Most workflow engines can pause; few can pause *inside* a node, serialise the whole execution context, survive a process restart, and resume with human feedback injected at the exact point it stopped. That is Chapter 15, and it is the strongest single argument for the framework.

### Key takeaways

- Nodes triggered by events, returning events that trigger further nodes.
- A node is anything from one line to a whole agent.
- Agent and RAG *are* workflows; this is the substrate, not an add-on.
- Streaming and interruption are the distinguishing capabilities.

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

### The idea that makes it click

**The method signature is the graph.**

```php
public function __invoke(StartEvent $event, WorkflowState $state): FirstEvent
```

Read it as a wiring statement: *this node runs when a `StartEvent` appears, and when it finishes it emits a `FirstEvent`.*

There is no separate edge definition, no configuration file, no `addEdge()` call. **The type hints are the wiring.**

Let that sit, because everything else in Part IV follows from it:

- Want a loop? Return the event that triggers an earlier node.
- Want a branch? Declare a union return type.
- Want to know the graph? Read the signatures.

::: {.callout .callout-warning}
[Historical note]{.callout-title}

Version 1 had an explicit `Edge` class and `addEdges()`. v2 removed it in favour of the event model. If you find a tutorial using `new Edge(NodeA::class, NodeB::class)`, it predates the current architecture by two major versions. Appendix A, item 32.
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

`set()` and `get()`. Available to every node.

### Events vs state: when to use which

A distinction people consistently get wrong, so here it is explicitly:

**Events carry the message.** What this specific step produced, passed to the next specific step. Ephemeral, directional, typed.

**State carries the context.** Things many nodes need: the user, the tenant, accumulated results, configuration. Persistent across the whole run.

The heuristic: **if only the next node needs it, put it in the event. If several nodes need it, or you need it after the run, put it in state.**

Overusing state produces a workflow where every node reads and writes a global bag — which is a workflow in name only, because the data flow is invisible again. Overusing events produces enormous event classes that pass everything along. Both extremes are worse than the balance.

### Key takeaways

- Event = plain class implementing `Event`; `StartEvent` and `StopEvent` are built in.
- Node = class with `__invoke(Event, WorkflowState): Event`.
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

Point 2 deserves emphasis. Coming from procedural pipelines, the natural assumption is that the array order matters. It does not, and understanding why is understanding the model.

### Is this useful?

By itself, no. But it is the right place to start because it isolates the mechanics from the complexity, and because the next section only adds one idea to it.

### Key takeaways

- `Workflow::make()->addNodes([...])->init()` then `run()`.
- `addNodes()` is a registry, not a sequence — events determine order.
- Execution runs from `StartEvent` to `StopEvent`.

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

Strip away everything except the three signatures:

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

Keep events small. An event should carry what the *next* node needs, not everything accumulated so far. Large shared context belongs in state (Section 14.3). An event that grows to fifteen properties is telling you its data belongs in state.

### Key takeaways

- Three nodes, three signatures, one graph.
- The type declarations are the wiring — readable and IDE-navigable.
- Name events as past-tense domain facts, not `FirstEvent`.
- Keep events small; put shared context in state.

## 13.5 Why Not Just Write a Script?

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

**Several loops with intermediate checkpoints.** Doable with `while`, until you need to know which iteration you were on after a crash.

**Streaming real-time updates.** A script can echo. It cannot easily emit structured progress events from arbitrary depth without threading a callback through every function.

**Pause, wait, resume.** This is the one that is not a matter of effort. Serialising the entire execution state mid-function, persisting it, resuming in a different process hours later — you cannot write that in a script without building a workflow engine. And if you build one, you have built this.

### The four development benefits

From the documentation:

**Model and maintain complex scenarios.** From a few steps up to iterative loops with checkpoints, using the same building blocks.

**Human in the loop.** Deploy AI in sensitive areas because a human is always in the loop for critical decisions.

**Streaming.** Real-time updates to the client during execution.

**Debugging with Inspector.** Instead of wondering why the workflow made a decision, see exactly what happened at any node.

That last one connects to Chapter 10. Nodes are named units, so a trace shows named steps. A script shows a stack trace.

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
