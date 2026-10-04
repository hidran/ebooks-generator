# Chapter 17 — The Laravel SDK

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## 17.1 Installation and Philosophy

### Install

```bash
composer require neuron-core/neuron-laravel
```

**Requirements:** this book uses Laravel 13 on PHP 8.5, with version 2.0.0 of the SDK. It requires `neuron-core/neuron-ai` `^4.0` and so pulls the framework in: 4.0.2 here. The package itself accepts older Laravel and PHP releases; the book's code needs PHP 8.5.

### What it provides

Five things, from the package's own description:

- A configuration file for AI provider and embeddings credentials
- Artisan commands to scaffold the most-used components
- Facades that instantiate providers and vector stores from configuration
- Ready-to-run migrations for `EloquentChatHistory`
- AI coding-assistant guidelines integrated with Laravel Boost

Read the list against the framework the package installs, because SDK 2.0.0 has not kept pace with it. The first three items work on neuron-ai 4.0.2, one generator excepted, and are what the rest of Part V uses: the configuration file, the generators, and the facades for providers, embeddings and vector stores. The last two do not, and neither does the feature the README leads with, the `Neuron` facade.

::: {.callout .callout-warning}
[SDK 2.0.0 is out of step with neuron-ai 4.0.2]{.callout-title}

Four parts of the package fail on the framework version it installs. Each has a working alternative, given where it comes up:

- The `Neuron` facade throws on every call. Use a generated agent class bound to a thread (Section 17.4).
- `php artisan neuron:node` writes a class whose imports do not exist. Correct two lines by hand (Section 17.3).
- The shipped migrations and models do not fit the 4.0.2 message store or its workflow persistence. Own the migration and the model in your application (below, and Chapter 18).
- The bundled Boost skills teach API that 4.0.2 removed. Install the skills that ship with the core package (Section 17.7).

Confirmed against neuron-ai 4.0.2 and neuron-laravel 2.0.0. A later SDK release may close any of these; check before you work around them.
:::

The fourth item on the package's list is the one to act on first. `EloquentChatHistory` no longer exists: on 4.0.2 a conversation lives in a message store, `EloquentMessageStore` in Laravel, which identifies every row by a `message_id` and relies on a unique `(thread_id, message_id)` index. The SDK's `chat_messages` migration creates no such column, and its `ChatMessage` model does not make it fillable. Its `workflow_store` table has a composite primary key and no `id`, so `EloquentPersistence` over the SDK's `WorkflowStore` model cannot delete the records of a finished run, and the second message on a thread is refused. Do not publish the `neuron-migrations` tag. Write one migration of your own for the two tables, and an `App\Models\ChatMessage` model with `thread_id`, `message_id`, `role`, `content` and `meta` fillable. Chapter 18 builds both.

### The philosophy, quoted

The README opens with a statement worth reading in full:

> Neuron doesn't need invasive abstractions, it already has a very simple syntax, 100% typed code, and clear interfaces you can rely on to develop your agentic system or create custom plugins and extensions.

And:

> In this package we provide you with a development kit specifically designed for Laravel integration points **without limiting the access to the Neuron native components.** You can also use this package as an inspiration to design your own custom integration pattern.

Three things follow, and they are the reason Part V comes after Parts II to IV rather than instead of them:

**Everything you learned still works.** Your agent classes, tools, workflows and RAG pipelines are unchanged. The SDK adds entry points; it does not replace the API.

**The SDK is optional.** The maintainers' own guide to NeuronAI in Laravel, the `neuron-laravel-integration` skill that ships inside the core package (Section 17.7), never installs it: it requires `neuron-core/neuron-ai`, adds one service provider, one migration and one model to the application, and keeps the provider keys in `config/services.php`. What the SDK adds on top is providers and stores built from configuration, and generators. Part V takes those from it and wires everything else in the application.

**It is a reference implementation.** The package explicitly invites you to use it as inspiration for your own integration. If you work in Symfony, Spryker or a legacy in-house framework, read this package's source and build the equivalent — the integration points are the same.

That last point matters if you are not on Laravel. This part is transferable.

### Key takeaways

- `composer require neuron-core/neuron-laravel`; Laravel 13 on PHP 8.5; SDK 2.0.0 with neuron-ai 4.0.2.
- What works: config, generators, and the provider, embeddings and vector store facades.
- What does not on 4.0.2: the `Neuron` facade, the node generator, the shipped migrations and models, the Boost skills.
- It adds convenience, never capability — everything from Parts II to IV is unchanged.
- Designed to be readable as a template for other frameworks.

## 17.2 Configuration

### Publish the config

```bash
php artisan vendor:publish --tag=neuron-config
```

Produces `config/neuron.php`.

### Environment variables

```dotenv
# Support for: anthropic, gemini, openai, openai-responses, mistral, ollama, huggingface, deepseek
NEURON_AI_PROVIDER=anthropic

# Support for: openai, gemini, ollama, voyage, mistral
NEURON_EMBEDDING_PROVIDER=openai

# Support for: file, pinecone, qdrant, meilisearch, chroma
NEURON_STORE_PROVIDER=file

ANTHROPIC_KEY=
ANTHROPIC_MODEL=

GEMINI_KEY=
GEMINI_MODEL=

OPENAI_KEY=
OPENAI_MODEL=

MISTRAL_KEY=
MISTRAL_MODEL=

OLLAMA_URL=
OLLAMA_MODEL=

# And many others
```

::: {.callout .callout-warning}
[Two of these have no default]{.callout-title}

`config/neuron.php` reads `NEURON_AI_PROVIDER` and `NEURON_EMBEDDING_PROVIDER` with no fallback. Leave the first unset and `AIProvider::driver()` fails with a `TypeError`, `AIProviderManager::getDefaultDriver(): Return value must be of type string, null returned`, which does not name the variable that is missing. `EmbeddingProvider::driver()` fails the same way without the second, and the README's own listing never mentions it. Set both. `NEURON_STORE_PROVIDER` is optional and falls back to `file`.
:::

Plus, for tracing:

```dotenv
INSPECTOR_INGESTION_KEY=fwe45gtxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The README presents that key as all you need. It is not. The core framework does not depend on Inspector and attaches no observer on its own: tracing is a PSR-14 listener that you subscribe explicitly (Chapter 10). In Laravel that means requiring `inspector-apm/inspector-laravel` and, by name, `inspector-apm/inspector-php` at `^3.19` (earlier 3.18 releases carry a subscriber that records nothing on 4.0.2), keeping the key above, and subscribing Inspector's `InspectorSubscriber` to `ObservabilityEvent` on the agents you want traced — in a shared base class or wherever your container builds agents, so none are missed. A key with no subscription produces no traces, and no error to tell you so.

### This is Section 3.6, done by the framework

In Part II you built `ProviderFactory` by hand — a `match` statement mapping a driver name to a configured provider. The SDK is that, as a first-class Laravel service.

Same idea, same benefits: vendor names in one place, provider choice as configuration, free local development with Ollama, cost tiering as a config change.

Having built the factory yourself, you know exactly what the SDK is doing. That is a much better position than treating it as magic.

### Environment-specific configuration

The natural Laravel pattern, and one of the strongest practical arguments for the SDK:

```dotenv
# .env.local — free, offline, no rate limits
NEURON_AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434/api
OLLAMA_MODEL=qwen2.5:7b
```

```dotenv
# .env.staging — cheap, real, good enough for QA
NEURON_AI_PROVIDER=openai
OPENAI_MODEL=gpt-4.1-mini
```

```dotenv
# .env.production
NEURON_AI_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-sonnet-4-5
```

One codebase, three cost profiles, zero code changes.

::: {.callout .callout-warning}
[One exception, carried forward from Section 12.4]{.callout-title}

The *embeddings* provider and model must not vary by environment. Different embeddings mean incompatible vector indexes. Pin both in `config/neuron.php` rather than leaving them to `.env`, or you will eventually debug a RAG system that returns nonsense only in staging.
:::

### System prompt in config

The README shows the system prompt coming from configuration:

```php
public function instructions(): string
{
    return (string) new SystemPrompt(...config('neuron.system_prompt'));
}
```

Useful for a default assistant. **Not** the right pattern for a real agent — a prompt is a specification (Section 3.5), and specifications belong in code, in version control, reviewed. A config file that a deploy can change without a code review is the wrong home for behaviour.

Use it for the generated default; declare instructions in the agent class for anything that matters.

::: {.callout .callout-warning}
[Two problems in that README snippet]{.callout-title}

The published example reads `return (string) new SystemPrompt(...config('neuron.system_prompt');` — a missing closing parenthesis. It also uses `use NeuronAI\Agent;` and `use NeuronAI\SystemPrompt;`, which are namespaces from older versions. The classes are `NeuronAI\Agent\Agent` and `NeuronAI\Agent\SystemPrompt`. Appendix A, items 39 and 40.
:::

The string return type is correct. The framework's own signature is `instructions(): SystemMessage|string` — a `SystemMessage` lets you split instructions into blocks and mark the static one for prompt caching — but a plain string is accepted and wrapped for you, and narrowing the return type to `string` in your class is legal. So is widening the method from `protected` to `public`, as the README does. The class `neuron:agent` generates (Section 17.3) does both.

### Key takeaways

- `vendor:publish --tag=neuron-config`, then env variables; `NEURON_AI_PROVIDER` and `NEURON_EMBEDDING_PROVIDER` have no default.
- This is `ProviderFactory` from Section 3.6, supplied for you.
- Vary the provider by environment; **never** vary the embeddings model.
- Keep real system prompts in code, not config.

## 17.3 Artisan Generators

### The commands

```bash
# Create an agent
php artisan neuron:agent MyAgent

# Create a RAG
php artisan neuron:rag MyRAG

# Create a tool
php artisan neuron:tool MyTool

# Create a workflow
php artisan neuron:workflow MyWorkflow

# Create a node
php artisan neuron:node CustomNode

# Create a middleware
php artisan neuron:middleware CustomMiddleware
```

`php artisan neuron:agent MyAgent` creates `app/Neuron/Agents/MyAgent.php` with the basic methods stubbed. The agent, tool, workflow and middleware stubs match the 4.0.2 API: the generated tool, for instance, declares its identity as `protected string $name` and `protected ?string $description` properties with no constructor, the shape Chapter 19 uses throughout. The RAG stub leaves its three hooks commented out for you to fill in. The node stub does not run as generated.

::: {.callout .callout-warning}
[`neuron:node` generates imports that do not exist]{.callout-title}

The node stub in SDK 2.0.0 imports `NeuronAI\Workflow\StartEvent` and `NeuronAI\Workflow\StopEvent`. Both classes live in `NeuronAI\Workflow\Events\`. The generated file parses, and the first workflow that runs the node fails with `Failed to validate App\Neuron\Nodes\CustomNode: First parameter of __invoke method must be a type that implements NeuronAI\Workflow\Events\Event`. Correct the two `use` lines after generating:

```php
use NeuronAI\Workflow\Events\StartEvent;
use NeuronAI\Workflow\Events\StopEvent;
```
:::

### Better than the core CLI, in one specific way

Compare with Section 3.3:

```bash
# Core package — full namespace, doubled backslashes on Unix
./vendor/bin/neuron make:agent App\\Agents\\AssistantAgent

# Laravel SDK — just the name
php artisan neuron:agent MyAgent
```

No namespace, no backslash escaping, no OS difference. The SDK knows your application structure.

That is a small thing that removes a real friction point — the Unix/Windows backslash difference from Chapter 3 causes genuine confusion, and here it simply does not exist.

### A suggested project structure

The generators put agents in `app/Neuron/Agents`. Extend the convention:

```
app/Neuron/
├── Agents/          SupportAgent, ResearchAgent, ReviewerAgent
├── Tools/           SearchOrdersTool, RequestRefundTool
├── Workflows/       ContentWorkflow
│   ├── Nodes/
│   └── Events/
├── Middleware/
├── Dto/             Verdict, Invoice, RefundRequest
└── Rag/             KnowledgeBaseAgent
```

One namespace containing everything agentic. A new developer opens `app/Neuron` and sees the whole AI surface of the application, rather than finding an agent in `app/Services`, a tool in `app/Support` and a DTO in `app/Http/Resources`.

The generators do not all agree with this tree out of the box — `neuron:tool` writes to `app/Neuron/Agents/Tools`, `neuron:node` to `app/Neuron/Nodes` and `neuron:rag` to `app/Neuron/RAG`. Move the files once, or pass the fully qualified class name to the command; either way, decide on the tree before the tenth file, not after it.

### Key takeaways

- Six generators, all `php artisan neuron:*`.
- Name only — no namespace, no escaping, no OS difference.
- Correct the two imports in every class `neuron:node` generates.
- Keep everything agentic under `app/Neuron`.

## 17.4 The Neuron Facade, and What to Use Instead

### Why it exists

The framework author describes the problem honestly:

> Before this release, using Neuron AI inside Laravel meant creating a dedicated agent class, extending `Agent`, implementing a `provider()` method, and wiring the system prompt yourself. That pattern is the right one once your agent has a personality, a set of tools, and a role in your application. But it is a lot of ceremony for a developer who just wants to check whether Claude, or GPT, or Gemini responds well to a given prompt.

A facade is Laravel's answer to that shape of problem, and this is a textbook use of one. On neuron-ai 4.0.2 it is also the one part of the SDK you cannot call.

::: {.callout .callout-warning}
[The `Neuron` facade throws on neuron-ai 4.0.2]{.callout-title}

An agent runs only once a thread ID is bound to it (Section 3.4). The facade in SDK 2.0.0 builds its agent with a bare `Agent::make()` and offers no way to bind one, so `Neuron::chat()`, `Neuron::stream()` and `Neuron::structured()` all fail with `AgentException: This agent has no thread ID: bind one with setThreadId() first.`, with or without `tools()` and `middleware()` in the chain. The working alternative is the one the quote calls ceremony, a dedicated agent class, and the generator reduces the ceremony to one command. The rest of this section uses it.
:::

### The three modes

```bash
php artisan neuron:agent AssistantAgent
```

The generated class needs no editing to stand in for the facade. Its `provider()` returns `AIProvider::driver()`, the configured default, and its `instructions()` builds the system prompt from `config/neuron.php`: the two things the facade reads. Resolve it from the container, bind it to a thread, and call it:

```php
use App\Neuron\Agents\AssistantAgent;
use NeuronAI\Chat\Messages\Stream\Chunks\TextChunk;
use NeuronAI\Chat\Messages\UserMessage;

// The container builds the agent; for() returns a copy bound to one thread
$agent = app(AssistantAgent::class)->for($threadId);

// Chat (synchronous) — returns the final AgentState
$response = $agent->chat(new UserMessage('Hello!'))->getMessage();
echo $response?->getContent();

// Stream (real-time chunks) — the call itself is the generator
foreach ($agent->stream(new UserMessage('Hello')) as $chunk) {
    if ($chunk instanceof TextChunk) {
        echo $chunk->content;
    }
}

// Structured output
$person = $agent->structured(new UserMessage('I am John and I like pizza!'), Person::class);
```

The same three entry points from Section 6.3's table — `chat()`, `stream()`, `structured()` — with one generated file behind them: `chat()` runs to completion and returns the `AgentState`, `stream()` is a generator you iterate directly, `structured()` returns the object. `getMessage()` is nullable, hence the `?->`. Do not carry the README's streaming loop over to the class: it calls `->events()` on the result and echoes `$event->content`, but `stream()` returns the generator itself and yields several kinds of chunk, so filter for `TextChunk` as above.

`$threadId` is the argument the facade never asks for. It names the conversation the call belongs to: any fresh string for a one-off question, the conversation's own ID when the user comes back to it. `for()` returns a copy of the agent bound to that thread and is the subject of Section 17.5; where thread IDs come from, and what is stored under them, is Chapter 18. `AssistantAgent::make()->setThreadId(...)` from Part II works in Laravel too, but let the container build the agent: from Chapter 18 on it has constructor dependencies. In a controller, take the agent as a method parameter instead of calling `app()`.

### Attaching tools

```php
$response = app(AssistantAgent::class)->for($threadId)
    ->addTool(new SearchTool())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

$response = app(AssistantAgent::class)->for($threadId)
    ->addTool([new SearchTool(), CalculatorToolkit::make()])
    ->chat(new UserMessage('Hello!'))
    ->getMessage();
```

Single instance or array. `addTool()` adds to whatever the class's `tools()` hook returns, on this bound copy only.

### Attaching middleware

```php
use App\Neuron\Middleware\AuditTrail;
use NeuronAI\Agent\Nodes\ChatNode;
use NeuronAI\Agent\Nodes\ToolNode;

// Record every tool execution in the audit log
$response = app(AssistantAgent::class)->for($threadId)
    ->addMiddleware(ToolNode::class, new AuditTrail())
    ->chat(new UserMessage('Summarise yesterday\'s orders'))
    ->getMessage();

// Both arguments accept arrays
$agent = app(AssistantAgent::class)->for($threadId)
    ->addMiddleware([ChatNode::class, ToolNode::class], [new AuditTrail()]);
```

`AuditTrail` is your own class — `php artisan neuron:middleware AuditTrail` generates it with empty `before()` and `after()` hooks to fill in.

**Here are the node classes, in a real namespace:** `NeuronAI\Agent\Nodes\ChatNode`, `ToolNode`, `StructuredOutputNode`.

Each interaction mode is backed by a node: `ChatNode` runs inference for both `chat()` and `stream()`, `StructuredOutputNode` for `structured()`, and `ToolNode` executes tools. The README still lists a separate `StreamingNode` for `stream()`; there is no such class, and middleware attached to it would never run.

**This is Section 2.3 fully cashed in.** You cannot use this API without knowing that an agent is a workflow of named nodes. That claim, made on the second day of the book, is what this API is built on.

### Approval is not middleware

The README's own middleware example attaches a `ToolApproval` middleware to `ToolNode`. That class belongs to older versions and does not exist any more. Approval is owned by `ToolNode` itself and configured on the tool — the tool declares its risk, and you can force or waive it where you attach it (Section 19.3):

```php
$state = app(AssistantAgent::class)->for($threadId)
    ->addTool(DeleteLogFileTool::make()->requireApproval())
    ->chat(new UserMessage('Delete the oldest log file'));

$state->isInterrupted();   // true — the run paused before deleting anything
```

The agent pauses correctly. What this one cannot do is *continue*: the paused run and its conversation are held in process memory, and both are gone when the request ends. Resuming in a later request needs a durable message store and workflow persistence, and Chapter 18 adds them. Approval is the clearest example of the next point.

### When to move it into the class

The README draws its line between the facade and a class:

> For custom memory, multiple middleware, or more advanced agent behaviour, create a dedicated agent class using `php artisan neuron:agent`.

You already have the class, so the line runs through it instead: between what you attach where the agent is called, as above, and what the class declares in its hooks. Four more triggers worth adding:

- The agent must **pause and resume** — tool approval, or any other interruption
- The agent needs a **name** — `SupportAgent`, not `AssistantAgent`: something a colleague can find and reason about
- The agent needs **tests**
- The agent's configuration appears in **more than one place**

Configuration at the call site is for prototypes, one-off internal features, and admin scripts. The hooks of a named class are for anything with a role in your application. Section 2.4's Pattern A versus Pattern B, in Laravel clothing.

### Key takeaways

- The `Neuron` facade throws on neuron-ai 4.0.2: its agent never gets a thread ID. A generated agent class bound with `for()` replaces it.
- `chat()`, `stream()`, `structured()` — the same entry points and return types as any agent class.
- `addTool()` and `addMiddleware()` chain onto the bound copy.
- Node classes live in `NeuronAI\Agent\Nodes\`; `ChatNode` serves both `chat()` and `stream()`.
- Approval lives on the tool, not in middleware — and resuming a paused run needs the durable stores of Chapter 18.
- Move configuration into the class when the agent must resume, needs a name or tests, or is configured twice.

## 17.5 Copy, Not Mutate: The Agent's Concurrency Story

### The problem this solves

The container hands you an agent, and in a long-running runtime — Octane, Swoole, RoadRunner, a queue worker — an object can outlive the request that asked for it. Registered as a singleton it always does; held in a property of a long-lived service it does so by accident.

Now consider what binding by mutation does to such an instance:

```php
// Request A
$agent->setThreadId($aliceThread)
    ->addTool(new AdminDeleteTool())
    ->chat(...);

// Request B, milliseconds later, different user, same instance
$agent->chat(...);  // ...whose conversation is this, and does it have the admin tool?
```

`setThreadId()` and `addTool()` change the object they are called on, so both answers are the bad one: request B runs on Alice's thread, with her messages in the prompt and the admin tool on offer. That is a cross-request leak of data and privilege that only appears under Octane, only sometimes, and would be extremely unpleasant to diagnose. A request B that binds its own thread first fares little better: it gets a `WorkflowException`, because a bound agent cannot be re-pointed.

### The design

`for()` is the framework's answer, and the comment on the method states the contract:

> A copy bound to $workflowId; the receiver is never modified.

For an agent, the workflow ID is the thread ID. Demonstrated:

```php
$response = $agent->for($threadId)
    ->addTool(new SearchTool())
    ->addMiddleware(ToolNode::class, new AuditTrail())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

// $agent is untouched — no thread, no tools, no middleware
$agent->for($otherThreadId)->chat(new UserMessage('Hello!'));
```

The SDK's facade class is written to the same rule, and its README says why:

> The facade resolves a **singleton**, so configuration methods never mutate the shared instance — they return a fresh, independent copy you chain into the call.

The facade has the design and lacks only the thread. `for()` has both.

### Why this deserves its own section

Two reasons.

**It is a safety property, not a convenience.** In a stateless PHP-FPM deployment the bug would be invisible. Under Octane it would be a data leak. The design anticipates the deployment model that is becoming normal.

**It is a pattern worth stealing.** Immutable-by-default configuration on a shared service — `withX()` returning a clone rather than `setX()` mutating — is good design generally, and most PHP developers have written the mutating version at least once.

The general principle: **a shared service should hand out configured copies, not let callers reconfigure it.**

### The practical rule

Because `for()` returns a copy and leaves the receiver alone, binding on one statement and calling on the next does nothing:

```php
// This does NOT work as it appears to
$agent->for($threadId);
$agent->chat(new UserMessage('...'));  // AgentException — $agent still has no thread
```

```php
// Chain it, or hold the copy
$bound = $agent->for($threadId);
$bound->chat(new UserMessage('...'));  // runs on $threadId
```

Simple once stated, and a confusing five minutes if it is not.

The other half of the rule is where the setters go. `addTool()` and `addMiddleware()` still change the object they are called on, so call them on the copy `for()` returned, never on the instance the container gave you. And do not register the agent as a singleton to begin with; Chapter 18 shows how the container should build it.

### Key takeaways

- `for()` returns a copy bound to one thread; the agent the container built is never modified.
- Prevents cross-request leakage under Octane, Swoole and RoadRunner.
- Chain the call or hold the returned copy — `for()` on a line of its own binds nothing.
- `addTool()` and `addMiddleware()` go on the copy, not on the container's instance.
- Worth stealing as a general pattern for shared services.

## 17.6 Component Facades

### Three facades

```php
use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
```

Each exposes `driver()`:

```php
class YouTubeAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver('anthropic');
    }
}
```

Familiar shape — the same `driver()` pattern as `Cache::driver()`, `Queue::connection()` and `Storage::disk()`. That is deliberate, and it is why it needs no explanation to a Laravel audience. They are ordinary Laravel managers underneath, so `extend()` registers a driver of your own — Section 20.1 says which stores it suits. One caveat before you do: the SDK registers the provider and embeddings managers as singletons but not `VectorStoreManager`, so a driver added with `VectorStore::extend()` lands on an instance only the facade holds. It is gone when the facade's cache is cleared, and `app(VectorStoreManager::class)` never sees it. Register the manager yourself, with `$this->app->singleton(VectorStoreManager::class)` in a service provider, before you extend it.

### A RAG agent, fully configured

```php
namespace App\Neuron;

use NeuronAI\Laravel\Facades\AIProvider;
use NeuronAI\Laravel\Facades\EmbeddingProvider;
use NeuronAI\Laravel\Facades\VectorStore;
use NeuronAI\Providers\AIProviderInterface;
use NeuronAI\RAG\Embeddings\EmbeddingsProviderInterface;
use NeuronAI\RAG\RAG;
use NeuronAI\RAG\VectorStore\VectorStoreInterface;

class MyChatBot extends RAG
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver('anthropic');
    }

    protected function embeddings(): EmbeddingsProviderInterface
    {
        return EmbeddingProvider::driver('openai');
    }

    protected function vectorStore(): VectorStoreInterface
    {
        return VectorStore::driver('file');
    }
}
```

Compare with the plain-PHP version from Section 12.1: three constructors with keys, models, directories and names. Here, three driver names, everything else in config.

The shipped vector store drivers are `file`, `pinecone`, `qdrant`, `meilisearch` and `chroma`. A store built from `config/neuron.php` has no document schema, which means it stores your metadata but cannot *filter* on it — filtering needs the fields declared up front. That matters the moment a second tenant arrives, and Chapter 20 builds its store accordingly.

### Named versus default

```php
// Explicit driver
AIProvider::driver('anthropic');

// Configured default — NEURON_AI_PROVIDER
AIProvider::driver();
```

**Prefer the default** for most agents. Naming the driver in the class re-introduces exactly the coupling that Section 3.6 removed — and it silently breaks the environment-based configuration from Section 17.2, because an agent that hardcodes `'anthropic'` will call Anthropic in local development regardless of what `.env.local` says. The default does depend on `NEURON_AI_PROVIDER` being set: without it, `driver()` is the `TypeError` from Section 17.2.

Name the driver only when this specific agent genuinely requires that specific provider — a cheap model for a classifier node, a vision-capable model for the invoice extractor.

### Cost tiering, in Laravel

Section 16.1's per-agent model choice, expressed cleanly:

```php
class ClassifierAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver('ollama');   // free, local, good enough
    }
}

class WriterAgent extends Agent
{
    protected function provider(): AIProviderInterface
    {
        return AIProvider::driver();          // the configured default
    }
}
```

One line per agent decides where the money goes across a multi-agent system.

What the manager cannot do is give two agents the same driver with different settings. It keeps one configuration per driver and caches what it builds, so every agent that asks for `'anthropic'` receives the same provider object: one model, one set of parameters, one HTTP client. When an agent needs a provider of its own — a second model from the same vendor, a client with its own timeout — construct it inside that agent's `provider()` from `config('neuron.provider.anthropic')`. The framework calls the hook afresh for every execution segment, and the maintainers' Laravel skill (Section 17.7) builds every agent's provider that way.

### Key takeaways

- `AIProvider`, `EmbeddingProvider`, `VectorStore` — all with `driver()`.
- Same idiom as `Cache::driver()`; no explanation needed.
- Prefer `driver()` with no argument so environment configuration keeps working.
- Name a driver only when that agent genuinely requires it.
- The manager shares one provider per driver; build the provider in the hook when an agent needs its own.

## 17.7 Laravel Boost and AI-Assisted Development

### What ships

The package includes **AI coding-assistant guidelines integrated with Laravel Boost**, to help assistants write better NeuronAI code. They ship as a set of Boost skills — one each for agents, tools, tool approval, workflows, RAG, streaming, structured output, testing, evaluation, monitoring and frontend integration.

Why this matters: as Appendix A documents at length, the ecosystem contains a great deal of old material. A coding assistant trained on public code will confidently produce code written for older versions: `use NeuronAI\Agent;`, `new Edge(...)`, `Tool::make(...)->setCallable(...)`, a `ToolApproval` middleware, `->events()` on a stream.

Shipping guidelines with the package is a direct fix: the assistant reads what is true now rather than what was true two years ago. It holds for exactly as long as the guidelines keep up with the code, and in SDK 2.0.0 they have not.

::: {.callout .callout-warning}
[The bundled Boost skills teach removed API]{.callout-title}

The skills in neuron-laravel 2.0.0 still teach `MyAgent::make(threadId: ...)`, `setChatHistory()` with `SQLChatHistory` or `EloquentChatHistory`, `$workflow->resume()` and `abandonRun()`. None of them exists in neuron-ai 4.0.2, and an assistant that follows those skills writes code that fails on its first call. The current skills are the thirteen in the core package, under `vendor/neuron-core/neuron-ai/skills/`: the same eleven topics, plus `neuron-laravel-integration` and `neuron-symfony-integration`. Install those instead, with the command the framework's README gives:

```bash
npx skills add ./vendor/neuron-core/neuron-ai/skills -y
```
:::

`neuron-laravel-integration` is the one to read beside the rest of Part V. It is the maintainers' own account of wiring NeuronAI into a Laravel 13 application: the container, the tables, thread authorisation, queues, streaming, tests. The chapters that follow lean on it.

### The wider idea

This is a pattern worth noticing rather than just a feature: **a library shipping instructions for the tools that write code against it.**

If you maintain packages, that idea has immediate value — when your users' assistants generate wrong code against your library, that is your support burden.

If you are building agentic systems, it closes a loop this book has been circling: you can connect the NeuronAI documentation to a coding assistant via an MCP server (Chapter 9), and use agents to help build agents.

### The honest caveat

Keep the framing sober. Assistants remain confidently wrong about fast-moving libraries, and Appendix A is direct evidence — the *official documentation* has drifted from the code in dozens of places. An assistant reading that documentation inherits the drift.

Shipped guidelines are not immune either, and this chapter is the evidence: the SDK's skills have already fallen behind the framework they describe. The SDK's tool-approval skill, besides, tells the assistant to declare `approvalPolicy(array $inputs)`; the `Tool` class declares `approvalPolicy()` with no parameters and reads inputs through `getInput()`. An assistant that follows the skill writes a method PHP rejects as an incompatible override. The package's own README, as this chapter has shown, still carries examples written for an older version. Guidelines lower the error rate; they do not remove the need to check.

The discipline: use assistants for scaffolding and boilerplate; verify anything touching the API surface against your installed version. That is the same habit this book has applied throughout, and it transfers well beyond NeuronAI. Chapter 27 goes further.

### Key takeaways

- The package ships guidelines for coding assistants as Laravel Boost skills.
- It exists because the public corpus is full of code written for older versions.
- The guidelines can drift too: in SDK 2.0.0 they teach API that 4.0.2 removed.
- Use the skills in `vendor/neuron-core/neuron-ai/skills/`, `neuron-laravel-integration` among them.
- Good pattern for library maintainers generally.
- Verify generated code against your installed version — always.

## Lab 11 — Five Minutes to First Response

**Covers:** configuration, the agent generator, binding a thread, and knowing when configuration belongs in the class.

### Goal

A working `POST /api/ask` endpoint, answered by a generated agent class, from `composer require` to first response in about five minutes. Then the more interesting half: identify the exact point at which configuring the agent in the controller stops being the right tool.

### Part one — make it work

1. Install the SDK and publish the config.
2. Set `NEURON_AI_PROVIDER=ollama` in `.env`, with `OLLAMA_MODEL` naming a model you have pulled, so this costs nothing.
3. Run `php artisan neuron:agent AssistantAgent` and leave the generated class as it is.
4. Write a controller that reads `message` from the request, binds the agent to a thread and returns its answer, and a route to it in `routes/api.php` (`php artisan install:api` creates that file if your application has none).
5. Confirm it works with `curl`.

That is the whole first part, and it should genuinely take minutes. The controller is three statements:

```php
namespace App\Http\Controllers;

use App\Neuron\Agents\AssistantAgent;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use NeuronAI\Chat\Messages\UserMessage;
use NeuronAI\UniqueIdGenerator;

class AskController extends Controller
{
    public function __invoke(Request $request, AssistantAgent $agent): JsonResponse
    {
        $data = $request->validate(['message' => ['required', 'string']]);

        $state = $agent
            ->for(UniqueIdGenerator::generateId('ask_'))
            ->chat(new UserMessage($data['message']));

        return response()->json(['answer' => $state->getMessage()?->getContent()]);
    }
}
```

```bash
curl -s http://localhost:8000/api/ask \
    -H 'Accept: application/json' \
    -d 'message=How do I implement a PSR-15 middleware without a framework?'
```

Laravel resolves `AssistantAgent` from the container because the method asks for it. The endpoint answers single questions, so every request mints a fresh thread ID and nothing outlives the response. The day a user should be able to ask a follow-up, the thread has to come from somewhere and the conversation has to live somewhere: that is Chapter 18.

### Part two — break it deliberately

Now add requirements one at a time, and note where each one starts to hurt:

1. **The endpoint needs a system prompt specific to your product.** Config, or code?
2. **It needs one tool.** Still comfortable in the controller?
3. **It needs a test.** How do you put a fake provider behind the endpoint?
4. **A second endpoint needs the same configuration.** Where does it live now?

By requirement three or four you should be moving things out of the controller and into the class: the prompt into `instructions()`, the tool into `tools()`. That is the lesson — not that configuring at the call site is bad, but that you can feel exactly when it stops fitting.

### Acceptance criteria

- `POST /api/ask` returns a sensible answer with `NEURON_AI_PROVIDER=ollama` and no API keys configured.
- Switching to a cloud provider requires only an `.env` change.
- You can state, in one sentence, which of the four requirements above pushed the configuration into the class.

### A trap to avoid

Do not bind on one statement and call on the next — Section 17.5. If your controller calls `$agent->for(...)` on one line and `$agent->chat(...)` on the next, the bound copy is thrown away and the call fails with `AgentException: This agent has no thread ID`. Write it as one chain. When you reach requirement two, the tool goes into that chain after `for()`; confirm it is actually being offered.
