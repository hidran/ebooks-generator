# Chapter 17 — The Laravel SDK

## 17.1 Installation and Philosophy

### Install

```bash
composer require neuron-core/neuron-laravel
```

**Requirements:** PHP >= 8.2, Laravel >= 10. It pulls in `neuron-core/neuron-ai` ^3.15.

Note the version floor is higher than the core package's PHP 8.1. If you are on 8.1, you use the core package directly — which, after Parts II to IV, you already know how to do.

### What it provides

Five things, from the package's own description:

- A configuration file for AI provider and embeddings credentials
- Artisan commands to scaffold the most-used components
- Facades that instantiate providers and vector stores from configuration
- Ready-to-run migrations for `EloquentChatHistory`
- AI coding-assistant guidelines integrated with Laravel Boost

### The philosophy, quoted

The README opens with a statement worth reading in full:

> Neuron doesn't need invasive abstractions. It already has a very simple syntax, 100% typed code, and clear interfaces you can rely on to develop your agentic system or create custom plugins and extensions.

And:

> In this package we provide you with a development kit specifically designed for Laravel integration points **without limiting access to the Neuron native components.** You can also use this package as an inspiration to design your own custom integration pattern.

Three things follow, and they are the reason Part V comes after Parts II to IV rather than instead of them:

**Everything you learned still works.** Your agent classes, tools, workflows and RAG pipelines are unchanged. The SDK adds entry points; it does not replace the API.

**The SDK is optional.** You can `composer require neuron-core/neuron-ai` in a Laravel app and wire the container yourself. The SDK saves you an afternoon.

**It is a reference implementation.** The package explicitly invites you to use it as inspiration for your own integration. If you work in Symfony, Spryker or a legacy in-house framework, read this package's source and build the equivalent — the integration points are the same.

That last point matters if you are not on Laravel. This part is transferable.

### Key takeaways

- `composer require neuron-core/neuron-laravel`; PHP 8.2+, Laravel 10+.
- Config, generators, facades, migrations, Boost guidelines.
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

Plus, for tracing:

```dotenv
INSPECTOR_INGESTION_KEY=fwe45gtxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

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

The *embeddings* model must not vary by environment. Different embeddings mean incompatible vector indexes. Pin it in `config/neuron.php` rather than leaving it to `.env`, or you will eventually debug a RAG system that returns nonsense only in staging.
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

Use it for the facade's default; declare instructions in the agent class for anything that matters.

::: {.callout .callout-warning}
[Two problems in that README snippet]{.callout-title}

The published example reads `return (string) new SystemPrompt(...config('neuron.system_prompt');` — a missing closing parenthesis. It also uses `use NeuronAI\Agent;` and `use NeuronAI\SystemPrompt;`, which are **v2 namespaces**. In v3 these are `NeuronAI\Agent\Agent` and `NeuronAI\Agent\SystemPrompt`. Appendix A, items 39 and 40.
:::

### Key takeaways

- `vendor:publish --tag=neuron-config`, then env variables.
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

`php artisan neuron:agent MyAgent` creates `app/Neuron/Agents/MyAgent.php` with the basic methods stubbed.

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

### Key takeaways

- Six generators, all `php artisan neuron:*`.
- Name only — no namespace, no escaping, no OS difference.
- Keep everything agentic under `app/Neuron`.

## 17.4 The Neuron Facade

### Why it exists

The framework author describes the problem honestly:

> Before this release, using Neuron AI inside Laravel meant creating a dedicated agent class, extending `Agent`, implementing a `provider()` method, and wiring the system prompt yourself. That pattern is the right one once your agent has a personality, a set of tools, and a role in your application. But it is a lot of ceremony for a developer who just wants to check whether Claude, or GPT, or Gemini responds well to a given prompt.

A facade is Laravel's answer to that shape of problem, and this is a textbook use of one.

### The three modes

```php
use NeuronAI\Laravel\Facades\Neuron;
use NeuronAI\Chat\Messages\UserMessage;

// Chat (synchronous)
$response = Neuron::chat(new UserMessage('Hello!'))->getMessage();
echo $response->getContent();

// Stream (real-time chunks)
foreach (Neuron::stream(new UserMessage('Hello'))->events() as $event) {
    echo $event->content;
}

// Structured output
$person = Neuron::structured(new UserMessage('I am John and I like pizza!'), Person::class);
```

The same three entry points from Section 6.3's table — `chat()`, `stream()`, `structured()` — with no class to write. It reads the default provider and system prompt from configuration.

### Attaching tools

```php
$response = Neuron::tools(new SearchTool())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

$response = Neuron::tools([new SearchTool(), CalculatorToolkit::make()])
    ->chat(new UserMessage('Hello!'))
    ->getMessage();
```

Single instance or array.

### Attaching middleware

```php
use NeuronAI\Agent\Middleware\ToolApproval;
use NeuronAI\Agent\Nodes\ChatNode;
use NeuronAI\Agent\Nodes\ToolNode;

// Require human approval before the agent executes any tool
$response = Neuron::middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Delete the oldest log file'))
    ->getMessage();

// Both arguments accept arrays
$neuron = Neuron::middleware([ChatNode::class, ToolNode::class], [new ToolApproval()]);
```

**Here are the node classes, in a real namespace:** `NeuronAI\Agent\Nodes\ChatNode`, `ToolNode`, `StreamingNode`, `StructuredOutputNode`.

The README states the mapping directly — each interaction mode is backed by its own node: `ChatNode` for `chat()`, `StreamingNode` for `stream()`, `StructuredOutputNode` for `structured()`, and `ToolNode` for tool execution.

**This is Section 2.3 fully cashed in.** You cannot use this API without knowing that an agent is a workflow of named nodes. That claim, made on the second day of the book, is what this API is built on.

### When to stop using the facade

The README says it plainly:

> For custom memory, multiple middleware, or more advanced agent behaviour, create a dedicated agent class using `php artisan neuron:agent`.

Three more triggers worth adding:

- The agent needs a **name** — something a colleague can find and reason about
- The agent needs **tests**
- The agent's configuration appears in **more than one place**

The facade is for prototypes, one-off internal features, and admin scripts. The class is for anything with a role in your application. Section 2.4's Pattern A versus Pattern B, in Laravel clothing.

### Key takeaways

- `Neuron::chat()`, `::stream()`, `::structured()` — no class required.
- `::tools()` and `::middleware()` chain onto the call.
- Node classes live in `NeuronAI\Agent\Nodes\`; each interaction mode maps to one.
- Graduate to a class when the agent needs a name, tests, or appears twice.

## 17.5 Copy, Not Mutate: The Facade's Concurrency Story

### The problem this solves

A facade resolves a singleton. In a long-running runtime — Octane, Swoole, RoadRunner — that instance persists across requests.

Now consider what a naive implementation would do:

```php
// Request A
Neuron::tools(new AdminDeleteTool())->chat(...);

// Request B, milliseconds later, different user
Neuron::chat(...);  // ...does request B have the admin tool?
```

If `tools()` mutated the shared instance, the answer would be yes — and you would have a cross-request privilege leak that only appears under Octane, only sometimes, and would be extremely unpleasant to diagnose.

### The design

The README addresses it directly:

> The facade resolves a **singleton**, so configuration methods never mutate the shared instance — they return a fresh, independent copy you chain into the call. This means every `Neuron::chat(...)` starts from the clean, configured default unless you explicitly attach tools or middleware.

Demonstrated:

```php
$response = Neuron::tools(new SearchTool())
    ->middleware(ToolNode::class, new ToolApproval())
    ->chat(new UserMessage('Hello!'))
    ->getMessage();

// The singleton is untouched — this call has no tools or middleware
Neuron::chat(new UserMessage('Hello!'));
```

### Why this deserves its own section

Two reasons.

**It is a safety property, not a convenience.** In a stateless PHP-FPM deployment the bug would be invisible. Under Octane it would be a data leak. The design anticipates the deployment model that is becoming normal.

**It is a pattern worth stealing.** Immutable-by-default configuration on a shared service — `withX()` returning a clone rather than `setX()` mutating — is good design generally, and most PHP developers have written the mutating version at least once.

The general principle: **a shared service should hand out configured copies, not let callers reconfigure it.**

### The practical rule

Because each chain is independent, you cannot build up configuration across statements:

```php
// This does NOT work as it appears to
Neuron::tools(new SearchTool());
Neuron::chat(new UserMessage('...'));  // no tools — different copy
```

```php
// Chain it, or hold the copy
$agent = Neuron::tools(new SearchTool());
$agent->chat(new UserMessage('...'));  // has tools
```

Simple once stated, and a confusing five minutes if it is not.

### Key takeaways

- The facade is a singleton; `tools()` and `middleware()` return independent copies.
- Prevents cross-request leakage under Octane, Swoole and RoadRunner.
- Chain the call or hold the returned instance — configuration does not accumulate across statements.
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

Familiar shape — the same `driver()` pattern as `Cache::driver()`, `Queue::connection()` and `Storage::disk()`. That is deliberate, and it is why it needs no explanation to a Laravel audience.

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

### Named versus default

```php
// Explicit driver
AIProvider::driver('anthropic');

// Configured default — NEURON_AI_PROVIDER
AIProvider::driver();
```

**Prefer the default** for most agents. Naming the driver in the class re-introduces exactly the coupling that Section 3.6 removed — and it silently breaks the environment-based configuration from Section 17.2, because an agent that hardcodes `'anthropic'` will call Anthropic in local development regardless of what `.env.local` says.

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

### Key takeaways

- `AIProvider`, `EmbeddingProvider`, `VectorStore` — all with `driver()`.
- Same idiom as `Cache::driver()`; no explanation needed.
- Prefer `driver()` with no argument so environment configuration keeps working.
- Name a driver only when that agent genuinely requires it.

## 17.7 Laravel Boost and AI-Assisted Development

### What ships

The package includes **AI coding-assistant guidelines integrated with Laravel Boost**, to help assistants write better NeuronAI code.

Why this matters: as Appendix A documents at length, the ecosystem contains a great deal of v1 and v2 material. A coding assistant trained on public code will confidently produce `use NeuronAI\Agent;` and `new Edge(...)` — APIs that were removed two major versions ago.

Shipping current guidelines with the package is a direct fix. The assistant reads what is true now rather than what was true two years ago.

### The wider idea

This is a pattern worth noticing rather than just a feature: **a library shipping instructions for the tools that write code against it.**

If you maintain packages, that idea has immediate value — when your users' assistants generate wrong code against your library, that is your support burden.

If you are building agentic systems, it closes a loop this book has been circling: you can connect the NeuronAI documentation to a coding assistant via an MCP server (Chapter 9), and use agents to help build agents.

### The honest caveat

Keep the framing sober. Assistants remain confidently wrong about fast-moving libraries, and Appendix A is direct evidence — the *official documentation* has drifted from the code in forty-four places. An assistant reading that documentation inherits the drift.

The discipline: use assistants for scaffolding and boilerplate; verify anything touching the API surface against your installed version. That is the same habit this book has applied throughout, and it transfers well beyond NeuronAI. Chapter 26 goes further.

### Key takeaways

- The package ships current guidelines for coding assistants via Laravel Boost.
- It exists because the public corpus is full of v1/v2 code.
- Good pattern for library maintainers generally.
- Verify generated code against your installed version — always.

## Lab 11 — Five Minutes to First Response

**Covers:** the facade, configuration, and knowing when to graduate away from both.

### Goal

A working `POST /api/ask` endpoint, answered through the facade, from `composer require` to first response in about five minutes. Then the more interesting half: identify the exact point at which the facade stops being the right tool.

### Part one — make it work

1. Install the SDK and publish the config.
2. Set `NEURON_AI_PROVIDER=ollama` in `.env` so this costs nothing.
3. Write a route and a controller that reads `message` from the request and returns the facade's answer.
4. Confirm it works with `curl`.

That is the whole first part, and it should genuinely take minutes. The controller is four lines.

### Part two — break it deliberately

Now add requirements one at a time, and note where each one starts to hurt:

1. **The endpoint needs a system prompt specific to your product.** Config, or code?
2. **It needs one tool.** Still comfortable in the controller?
3. **It needs a test.** How do you fake the facade?
4. **A second endpoint needs the same configuration.** Where does it live now?

By requirement three or four you should be reaching for `php artisan neuron:agent`. That is the lesson — not that the facade is bad, but that you can feel exactly when it stops fitting.

### Acceptance criteria

- `POST /api/ask` returns a sensible answer with `NEURON_AI_PROVIDER=ollama` and no API keys configured.
- Switching to a cloud provider requires only an `.env` change.
- You can state, in one sentence, which of the four requirements above pushed you to a class.

### A trap to avoid

Do not accumulate facade configuration across statements — Section 17.5. If your controller calls `Neuron::tools(...)` on one line and `Neuron::chat(...)` on the next, the tools are silently absent. Write it as one chain and confirm the tool is actually being offered.
