# Chapter 2 — The Architecture of NeuronAI

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## 2.1 The Four Pillars

The whole framework fits in your head as four concepts. Getting them in place now means every later chapter has somewhere to attach.

### Installation, for orientation

```bash
composer require neuron-core/neuron-ai:^4.0.3
```

Requirements: the `curl` extension, and very little else — the framework talks HTTP through its own curl-based client. The package itself runs on PHP 8.1 or later; this book's code needs PHP 8.5 (Chapter 3 says why). The Laravel SDK is covered in Part V, where the book uses Laravel 13 on PHP 8.5.

### Pillar 1 — Agent

The tool-calling loop from Section 1.2, implemented and guarded. You extend a base class, declare which provider to use, what the instructions are, and which tools are available. NeuronAI runs the loop, manages the message array, handles the tool dispatch and enforces the run limits.

This is rung 4 from Section 1.1, out of the box.

### Pillar 2 — Workflow

An event-driven graph. You define nodes; each node receives an event and returns an event; the returned event type determines which node runs next. On top of that: shared state, branching, loops, and **durable execution** — with a persistence store configured, every completed step is recorded, so a run can pause for human input or an external event and resume days later in a different process, and a run whose process crashed picks up after its last completed step instead of starting over.

This is rung 3 done properly, and it is also the substrate for multi-agent systems.

### Pillar 3 — RAG

The retrieval pipeline: data loaders to ingest, an embeddings provider to vectorise, a vector store to hold and search, pre- and post-processors to improve queries and rerank results, and a `RAG` class that ties them together into an agent that answers from your documents.

### Pillar 4 — Observability

Every agent and workflow emits a stream of events as it runs — a node started, an inference began and ended, a tool was called and returned, a run was interrupted — as standard PSR-14 events. You subscribe to them: Inspector, built by the same team, turns them into traces; your own logger or your framework's event system can take them too. Given Section 1.5, this is not a monitoring nicety. Without a trace you cannot answer "why did it do that", and "why did it do that" is the only question you will ever ask.

### The mental picture

```
                   ┌─────────────────────────┐
                   │       WORKFLOW          │
                   │  (nodes, events, state, │
                   │   loops, interruption)  │
                   │                         │
                   │   ┌───────┐  ┌───────┐  │
                   │   │ AGENT │  │  RAG  │  │
                   │   └───────┘  └───────┘  │
                   └─────────────────────────┘
                                │
       ┌────────────┬───────────┼───────────┬────────────┐
   Providers      Tools      Memory    VectorStores   Embeddings
                                │
                          OBSERVABILITY
```

Workflow is the outer container. Agent and RAG are pre-built configurations that live inside it. Underneath, a set of swappable components. Cross-cutting, tracing.

### Key takeaways

- Four pillars: Agent, Workflow, RAG, Observability.
- Workflow is the general case; Agent and RAG are specialisations.
- Observability is a pillar, not an add-on, because of non-determinism.

## 2.2 Everything Is an Interface

One design decision explains most of NeuronAI's shape, and it gives you more practical leverage than any single feature.

### The five interfaces that matter

NeuronAI's architecture is a small set of contracts that every concrete implementation honours:

| Interface | Responsibility | Example implementations |
|---|---|---|
| `AIProviderInterface` | Talk to an LLM | Anthropic, OpenAI, Gemini, Mistral, Ollama, DeepSeek, Bedrock, Azure |
| `ToolInterface` | Give the agent a capability | Your classes, built-in toolkits, MCP-provided tools |
| `MessageStoreInterface` | Store conversation messages | InMemory, File, SQL, Eloquent |
| `EmbeddingsProviderInterface` | Turn text into vectors | OpenAI, Voyage, Ollama |
| `VectorStoreInterface` | Store, filter and search vectors | Memory, File, MariaDB, MongoDB Atlas, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch |

Your application code depends on the interface. Never on the implementation.

::: {.callout .callout-warning}
[Version note]{.callout-title}

That vector store list is the complete set of first-party implementations, and it is worth reading carefully because **NeuronAI does not ship a pgvector store**. A good deal of third-party material — including tutorials and course outlines derived from the Python ecosystem, where pgvector is ubiquitous — assumes it does. If you want Postgres-shaped ergonomics, the closest first-party answer is **MariaDB 11.7+**, which gives you vector search in a database you are probably already running; Chapter 12 builds on it. **PHPVector**, a pure-PHP store with no infrastructure at all, lives in a separate package with its own release cycle, and it had no release for NeuronAI v4 when this book went to press — Chapter 12 explains how to check.
:::

### What this looks like in practice

```php
protected function provider(): AIProviderInterface
{
    return new Anthropic(
        key: 'ANTHROPIC_API_KEY',
        model: 'ANTHROPIC_MODEL',
    );
}
```

Switch to a locally hosted model:

```php
protected function provider(): AIProviderInterface
{
    return new Ollama(
        url: 'OLLAMA_URL',
        model: 'OLLAMA_MODEL',
    );
}
```

Nothing else changes. Not the instructions, not the tools, not the history, not the calling code. In Section 3.6 we push this further and drive the choice entirely from an environment variable.

### Why this is a strategic capability, not a convenience

Four consequences worth naming explicitly, because they are how you justify the framework to a decision-maker:

**Cost tiering.** Route classification and extraction to a cheap fast model; route final synthesis to an expensive one. This is the third lever from Section 1.4, and the interface is what makes it a one-line change instead of a refactor.

**Provider risk.** Outages happen, prices change, terms change. A hard dependency on one vendor's SDK is a business risk. An interface is an exit.

**Local development.** Run Ollama on your laptop and develop everything in this book for free. Deploy against a cloud provider. Same code.

**Data residency.** A client who cannot send data outside the EU, or outside their own building, is a configuration change rather than a rewrite.

### The trade-off, stated honestly

An abstraction over multiple providers converges on their common subset. Provider-specific features — extended thinking modes, native web search tools, particular safety settings — are either exposed through escape hatches or not available. NeuronAI's answer is `ProviderTool`, which lets you use a provider's built-in tools (the OpenAI Responses API, Gemini, Anthropic and ZAI support these), but the framework's own documentation is candid that provider tools introduce constraints and that the portable Tools and Toolkits system stays the more flexible route.

Know what you are trading. Portability costs access to the newest vendor-specific feature for a while.

### Key takeaways

- Five interfaces: provider, tool, message store, embeddings, vector store.
- Depend on the interface; the implementation is configuration.
- The payoff is cost tiering, vendor risk, free local development and data residency.
- The cost is delayed access to provider-specific features.

## 2.3 The Key Insight: Agent and RAG *Are* Workflows

This is the most important section in the chapter. It is the framework's central unifying idea, the official documentation reveals it late, and it explains a great deal that would otherwise look arbitrary.

### The statement

`Agent` and `RAG` are not separate systems that sit next to `Workflow`. **They are workflows.** They are pre-assembled graphs of nodes that implement the two most common agentic patterns.

NeuronAI's own documentation puts it directly: the Agent and RAG classes are workflows themselves, representing ready-to-use implementations of the most common patterns for tool calls, retrieval and structured output.

### What that means concretely

`Agent` extends `Workflow`, literally: open `vendor/neuron-core/neuron-ai/src/Agent/Agent.php` and the class declaration says so. When you call `->chat()` on an agent, you are running a workflow whose nodes are:

- `AgentStartNode` — assembles the request: instructions, messages, run options
- `ChatNode` — calls the LLM; `->stream()` goes through the same node, which simply streams the response
- `StructuredOutputNode` — calls the LLM when you request a typed result
- `ToolNode` — executes the tools the model asked for, pausing first for a human decision when a tool requires approval, then loops back to inference
- `AgentEndNode` — ends the run once the model gives a final answer

`ChatNode` and `StructuredOutputNode` share a base class, `InferenceNode`: "wherever the model is called".

Those node names are not internal trivia. They are part of the public surface. You attach middleware to an agent by naming the node class it should wrap. Here a summarisation middleware runs before every model call, chat or structured, and, once the conversation passes a token budget, replaces the oldest turns with a summary:

```php
$agent = SupportAgent::make(workflowId: $threadId)
    ->addMiddleware(InferenceNode::class, new Summarization(
        provider: $cheapProvider,
        maxTokens: 20_000,
    ));

$state = $agent->chat(new UserMessage('Summarise my last three tickets'));
```

You cannot use that API without knowing that `chat()` is backed by nodes. This is precisely why it belongs in Chapter 2 rather than Chapter 15.

The return value tells the same story. `chat()` does not return a message; it runs the workflow to completion and returns its final state, an `AgentState`, which extends the `WorkflowState` every workflow returns. The assistant's reply is one thing you read off it (Section 3.4).

### The three consequences

**1. Everything you learn about workflows applies to agents.**
Middleware, state, streaming, interruption, persistence — these are workflow features, and agents inherit all of them. When you reach Chapter 15 and learn human-in-the-loop, you are not learning a separate agent feature: a tool that needs approval makes `ToolNode` interrupt the run, exactly as any workflow node can, and approving it resumes the run. Even the conversation's identity is a workflow concept. The thread ID you give an agent (the `workflowId:` argument above; Chapter 4) *is* the run's workflow ID. The framework never invents one — an agent without an ID refuses to run — and in exchange an endpoint holding nothing but the thread ID can find a paused run and resume it.

**2. There is no second framework when the project grows.**
The usual trajectory with other stacks is: prototype with the simple abstraction, hit its ceiling, rewrite against the graph abstraction. Here, `Agent` *is* the graph abstraction with a default configuration. Growing means adding nodes, not migrating.

**3. You can use an Agent as a node inside a larger Workflow.**
This is the multi-agent story, and it needs no special multi-agent API. A research agent is a node. A writer agent is a node. An arbiter is a node. Compose them with events. Chapter 16 does exactly this.

### The decision rule

**Extend `Agent`** when your problem is "one entity, a goal, some tools, loop until done". That is most single-purpose assistants.

**Build a `Workflow`** when you need: control over the order of steps, multiple specialised agents, branching or looping that you author, checkpoints, or a pause for human input.

**Extend `RAG`** when the core job is answering from a document corpus.

And when you are unsure: start with `Agent`. Migrating to a workflow later is additive, because it was a workflow all along.

::: {.callout .callout-tip}
[In practice]{.callout-title}

If you take one sentence from Part I into Part IV, take this one. Readers who miss it experience workflows as an unrelated new topic halfway through the book; readers who have it experience workflows as *"oh — so that is what was under the agent all along"*.
:::

### Key takeaways

- `Agent` and `RAG` are configured workflows, not parallel systems; `chat()` returns the final workflow state.
- Node classes (`ChatNode`, `StructuredOutputNode`, their base `InferenceNode`, `ToolNode`) are public API — middleware targets them.
- Workflow features — interruption, durable persistence, identity — are inherited by agents; a conversation's thread ID is its workflow ID.
- Multi-agent needs no special API: an agent is just a node.

## 2.4 Extend or Compose: Choosing Your Structure

Three structural patterns, one decision rule, and — importantly — a migration path between them that does not involve a rewrite.

### Pattern A — Extend the Agent class

The default, and correct for the large majority of cases.

```php
namespace App\Neuron;

use NeuronAI\Agent\Agent;
use NeuronAI\Agent\SystemPrompt;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\Providers\Anthropic\Anthropic;

class SupportAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return new Anthropic(key: '...', model: '...');
    }

    protected function instructions(): string
    {
        return (string) new SystemPrompt(
            background: ['You are a customer support assistant.'],
        );
    }

    protected function tools(): array
    {
        return [ /* ... */ ];
    }
}
```

Three template methods — `provider()`, `instructions()`, `tools()` — plus the optional `messageStore()` and `contextWindow()`, and each has a setter twin (`setAiProvider()`, `setInstructions()`, `setTools()`, `setMessageStore()`, `setContextWindow()`) that wins over the method when you call it. Everything else is inherited. The class is a declaration of *what this agent is*, and it reads like configuration because it is.

**Why this pattern is worth defending.** The class becomes a named, testable, injectable unit. `SupportAgent` can be bound in a service container, mocked in tests, and reasoned about by a colleague who has never seen the framework. That is a real architectural benefit over scattering fluent configuration across controllers.

### Pattern B — Fluent configuration at the call site

For one-off runs and experiments:

```php
$state = SupportAgent::make(workflowId: $threadId)
    ->toolMaxRuns(5)
    ->addTool(SomeExtraTool::make())
    ->chat(new UserMessage('...'));
```

Use it for per-request variation on top of a declared class: a tool that only appears for admins, a lower run limit for a cheap endpoint. Do not use it as a substitute for having a class — configuration assembled inline in a controller is configuration nobody can find in six months.

### Pattern C — Compose a Workflow from components

When you want authored control flow, you use NeuronAI's components as standalone parts. The documentation is explicit that providers, embeddings, data loaders, chat history and vector stores can all be used as standalone components to build fully custom agentic entities.

```php
$state = Workflow::make(workflowId: $runId)
    ->addNodes([
        new ClassifyNode(),
        new RetrieveNode(),
        new AnswerNode(),
    ])
    ->run();
```

Here *you* wrote the sequence. The model fills in the steps. Like an agent, a workflow runs under an ID you supply: `workflowId:` is the run's address, and the framework never makes one up. `run()` executes the graph and returns the final `WorkflowState` — the same verb and the same kind of result an agent gives you, because an agent is this. This is rung 3 from Section 1.1, with durable persistence and interruption available when needed.

### The migration path

The reason this decision is low-risk: Pattern A → Pattern C is additive. Because `SupportAgent` is already a workflow, promoting it means wrapping it as a node in a larger graph, not rewriting it.

```php
class SupportNode extends Node
{
    public function __invoke(QuestionEvent $event, WorkflowState $state): ResolvedEvent
    {
        $answer = SupportAgent::make(workflowId: $event->threadId)
            ->chat(new UserMessage($event->question))
            ->getMessage();

        return new ResolvedEvent($answer?->getContent());
    }
}
```

`QuestionEvent` and `ResolvedEvent` are your own event classes; the first carries the question and the thread ID of the conversation it belongs to. The node's parameter and return types are what wire it into the graph. Your agent is unchanged. It is now a component of something larger.

### Key takeaways

- Extend `Agent` by default; the class is a named, injectable, testable unit.
- Fluent config for per-request variation, not as a replacement for a class.
- Compose a `Workflow` when you author the control flow.
- Promotion from A to C is additive — wrap, do not rewrite.

## 2.5 The Ecosystem Around the Framework

A short orientation, so that you do not rebuild things that already ship and you know which pieces this book actually uses.

### Inspector

Built by the same team, and the reason observability is a pillar. It is not bundled: the framework itself depends on nothing but the PSR-14 interfaces, so you require Inspector's package (`inspector-apm/inspector-php`, 3.19 or later), set its key,

```dotenv
INSPECTOR_INGESTION_KEY=your-key-here
```

and subscribe its listener, `InspectorSubscriber`, to the agents and workflows you want traced. From then on every execution appears as a timeline: which node ran, which tool was called with which arguments, what came back, how many tokens, how long. Nothing is attached implicitly — an agent you did not subscribe is an agent you cannot see, which is worth a line in your code review checklist.

We wire it up in Chapter 10 and use it again in Chapter 23. Given Section 1.5, plan for a trace viewer of some kind from the start.

### Neuron Cloud

The hosted observability platform the NeuronAI team runs for the framework, and the one the library's own guidance now points to for production tracing. It consumes the same event stream: you require `neuron-core/cloud-sdk` (or its `neuron-core/neuron-cloud-laravel` and `neuron-core/neuron-cloud-symfony` wrappers), give it an API key and a signing key, and subscribe its listener exactly as you would Inspector's. Every run then arrives as one trace — nodes, inferences, tool calls, retrieval, structured output — stitched across the pauses of a durable run. Choosing between the two changes one `subscribe()` call and nothing in your agents. Section 10.2 says what to check before you plan on it.

### The Laravel SDK

```bash
composer require neuron-core/neuron-laravel:^2.0 neuron-core/neuron-ai:^4.0.3
```

The whole of Part V. It provides a config file, artisan generators (`neuron:agent`, `neuron:rag`, `neuron:tool`, `neuron:workflow`, `neuron:node`, `neuron:middleware`), and facades for providers and vector stores. The two tables a production agent needs — the chat messages, and the workflow store that durable runs persist to — come from one migration of your own: the ones SDK 2.0.0 ships do not fit neuron-ai 4.0.3 (Section 17.1).

Worth stressing: this package adds convenience, not capability. Everything it does you could do by hand — which is exactly why we build it by hand first in Parts II to IV.

### MCP — Model Context Protocol

An open protocol for exposing tools to AI systems. NeuronAI ships an MCP connector, so tools published by any MCP server can be attached to a NeuronAI agent like native ones. Chapter 9 covers it. The security implications get their own discussion there: an MCP server is third-party code entering your agent's loop.

### Maestro

An open-source CLI agent framework built on NeuronAI, with tool calling and human-in-the-loop approvals. Useful as a reference implementation of a complete production application, and a good source of code-reading exercises. We return to it in Chapter 27.

### Neuron Hub

A registry of community extensions and toolkits. Check it before writing an integration — and publish yours there.

### Neuron Studio

A community package (`digitalelvis/neuronai-studio`) offering a visual agent builder for Laravel that exports real PHP classes. Useful for prototyping and for demonstrating architecture to non-developers. It generates code; it does not replace understanding it.

### Version landscape

This book targets **NeuronAI 4.0.3**, and for Part V the **Laravel SDK 2.x**, the release line built for NeuronAI v4.

Much of the sample code you will find online was written for older versions. Some of it has the same imports as this book and fails later, on a method that does not exist or returns something else; some of it uses older namespaces (`NeuronAI\Agent` rather than `NeuronAI\Agent\Agent`) and fails on its first `use` statement. If a blog post or a documentation page does not match this book, check which version it targets before you debug anything else.

::: {.callout .callout-warning}
[The upgrade guides ship with the package]{.callout-title}

NeuronAI puts its migration notes where your code can reach them: `vendor/neuron-core/neuron-ai/upgrade/` holds one numbered guide per breaking change, each with before-and-after code and the `grep` patterns that find affected call sites. When a snippet from an older tutorial refuses to run, the answer is usually in one of those files, and they are more current than the documentation site, which lags the code.

Chapter 27 turns this into a **version strategy**: how to determine what you actually have installed, how to read a changelog and an upgrade guide for breaking changes, and how to pin so that a library release is a decision rather than an outage. Before you rely on any version claim — including this one — run `composer show neuron-core/neuron-ai --all`.
:::

### Exercise

Reproduce the four-pillar diagram from memory. Then, for each of Capstone A ("Repo Auditor CLI", Chapter 24) and Capstone B ("Agentic Support Desk", Chapter 25), list which pillars and which ecosystem pieces you expect to need. Keep the answer and compare it against what you actually build; the gap is the most useful feedback this book can give you.

### Key takeaways

- Observability is a stream of PSR-14 events; Inspector and Neuron Cloud are listeners you subscribe explicitly, not something that attaches itself.
- The Laravel SDK for convenience, not capability.
- MCP brings external tools in — and external code with them.
- This book targets NeuronAI 4.0.3 on PHP 8.5. Code written for older versions still fills search results; check the version before debugging.
