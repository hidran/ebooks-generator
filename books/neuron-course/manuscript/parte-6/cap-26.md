# Chapter 26 — Version Strategy, the Ecosystem, and AI-Assisted Development

Three things nobody puts in the documentation, and all three will affect you within a month of shipping.

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## 26.1 Version Strategy

### The landscape

- **v3 is current stable.** The Laravel SDK 1.3.0 requires `neuron-ai: ^3.15`.
- **v1 and v2 are archived** but their documentation remains online at versioned paths, and their code is all over blogs, forums and answer sites.

::: {.callout .callout-warning}
[On the "v4" you may have heard about]{.callout-title}

Course outlines and forum posts circulate referring to a NeuronAI v4 beta. That release could not be verified at the time of writing: the published upgrade material covers v2 → v3 only, the documentation site keeps archived trees at `/v1/` and `/neuron-v3/` paths that are easy to mistake for a newer branch, and the current Laravel SDK pins to `^3.15`.

Before you rely on any version claim — including this one — run:

```bash
composer show neuron-core/neuron-ai --all
```

and check the project's releases page. That command is the authority. This book is not.
:::

### What changed between v2 and v3, and why it matters to you

Three breaks appear constantly in older material, and every one of them is a fatal error for someone copying a tutorial:

**1. Namespaces moved.**

| v1 / v2 | v3 |
|---|---|
| `NeuronAI\Agent` | `NeuronAI\Agent\Agent` |
| `NeuronAI\SystemPrompt` | `NeuronAI\Agent\SystemPrompt` |

**2. `chat()` returns a response, not a message.**

```php
// v2
$message = MyAgent::make()->chat(new UserMessage("Hi, who are you?"));

// v3
$message = MyAgent::make()->chat(new UserMessage("Hi, who are you?"))->getMessage();
```

**3. Attachments became content blocks.**

```php
// v2
$message->addAttachment(new Image($url, AttachmentContentType::URL));

// v3
$message = new UserMessage([
    new TextBlock('Analyze this'),
    new ImageBlock($url, SourceType::URL)
]);
```

And the architectural change underneath all of it: Agent, RAG and the message system were **rebuilt on top of the Workflow component**, which now powers the entire framework. That is why Section 2.3 could say "Agent and RAG *are* workflows" — it became literally true in v3.

### The four-check diagnostic

When you find sample code that does not work:

1. **Check the `use` statements.** `NeuronAI\Agent;` without a second segment means v2 or earlier.
2. **Check for `->getMessage()`.** Its absence means v2.
3. **Check for `Edge` or `addEdges()`.** That is v1.
4. **Check for `->start()->getResult()`.** That is the v2 workflow API.

Four checks, and they identify the version of almost any snippet in seconds. It is worth keeping them somewhere you can find them.

### Surviving a fast-moving dependency

Six practices, all of which apply to any library moving faster than your release cycle:

**Pin and commit `composer.lock`.** Not just in applications — in any repository someone else will clone and expect to work. The lock file is what makes "it worked last year" reproducible.

**Record the version where the code lives.** A line in your README, a constant, a comment at the top of the agent namespace. When someone debugging in eighteen months asks "what were we written against?", they should not have to guess.

**Keep an errata file.** When you find a discrepancy between the documentation and the shipped code — and Appendix A shows there are at least forty-four — write it down where your team will see it. The next person to hit it will otherwise spend the same afternoon you did.

**Separate durable knowledge from perishable knowledge.** Your notes about tool description design, chunking strategy and the agent loop stay true across major versions. Your notes about method signatures do not. Keeping them in different documents means a major upgrade invalidates one file rather than all of them.

**Do not chase a new major immediately.** Let the ecosystem catch up, then upgrade deliberately. A library release should be a decision you make, not an outage you discover.

**Read the upgrade guide before the changelog.** The changelog tells you what changed; the upgrade guide tells you what to do about it. For v2 → v3, the guide is short and the changes are mechanical — which is the best case, and not one to count on.

### Key takeaways

- v3 is current; v1/v2 code is everywhere and does not compile against it.
- Four checks identify a snippet's version in seconds.
- `composer show --all` is the authority on what you actually have.
- Pin the lock file, record the version, keep an errata file.
- Separate durable concepts from perishable API so an upgrade invalidates one document, not all of them.

## 26.2 The Ecosystem

### Maestro — a complete application to read

**Maestro is the first CLI agent built entirely in PHP with NeuronAI.** It is a coding assistant in the shape of the terminal assistants you may already use, and it is open source.

```bash
composer global require neuron-core/maestro
```

On Windows, install and run it under WSL.

It supports every NeuronAI provider — Anthropic, OpenAI, Gemini, Cohere, Mistral, Ollama, Grok, DeepSeek — routed through a provider factory, and integrates Inspector via an `inspector_key` in `.maestro/settings.json`.

**Why it belongs at the end of this book.** The author's own assessment is the point:

> The framework doing the heavy lifting here is Neuron AI, specifically the workflow architecture introduced in v3. Without the ability to interrupt execution mid-agent-loop and resume it based on user input, the tool approval system would require significantly more scaffolding to build and maintain. This pattern — interrupt, present, resume — would have been painful to implement without a workflow-oriented framework underneath.

That is Chapter 15, validated by a real application. Having finished Part IV, you can read Maestro's source and recognise every pattern in it.

**Two features worth studying specifically:**

**The tool approval system** — interactive confirmation before sensitive operations. Section 15.5's `ToolApproval`, in production.

**The extension system** — PHP classes implementing `ExtensionInterface`, registered through an `ExtensionApi` injected at boot. An `ExtensionLoader` builds registries for tools, commands, renderers, events, memories and UI. This is a well-designed plugin architecture and worth reading on its own merits, independent of AI.

**A good exercise:** write a Maestro extension that adds one tool from Capstone A. It is the shortest path from "I built a CLI agent" to "I extended someone else's".

### Neuron Hub

A registry of community extensions and toolkits. Two uses:

**Check before you build.** Someone may have written your integration.

**Publish yours.** A well-built toolkit — a class extending `AbstractToolkit` with a real `guidelines()` method (Section 5.7) — is a small, achievable open-source contribution with a clear audience.

If you are building a portfolio, this is a better first contribution than a documentation typo: scoped, useful, and demonstrably yours.

### Neuron Studio

`digitalelvis/neuronai-studio` — a community package offering a visual agent builder for Laravel that **exports real PHP classes**.

Useful for prototyping and for showing architecture to non-developers. The caveat, plainly: it generates code, it does not replace understanding it. Reaching for Studio before finishing Part II produces classes you cannot debug.

### Beyond Laravel

The framework is deliberately framework-agnostic, and the core package needs only PHP 8.1.

**Symfony.** Everything from Parts II to IV applies directly. Register agents as services; `SQLChatHistory` takes a plain PDO, which you get from a Doctrine connection with `getNativeConnection()`. Inspector ships `inspector-symfony`.

**Spryker, WordPress, legacy in-house.** Same story. The core package has no framework dependencies. The Laravel SDK is, in the maintainers' own words, something you can use *as inspiration to design your own custom integration pattern.*

The framework's positioning argument is worth quoting:

> Rather than fragmenting innovation across framework-specific solutions, Neuron enables collaboration between Laravel developers, Symfony contributors, WordPress plugin authors, and custom framework teams.

If you are not on Laravel, Part V of this book is a case study rather than a prerequisite. The integration points it describes — a service container, a queue, a database, an HTTP layer — exist in every framework worth using.

### Key takeaways

- Maestro is a complete open-source application built on the patterns in this book — read it.
- Neuron Hub is a realistic first open-source contribution.
- Studio generates code; it does not replace understanding it.
- The core package is framework-agnostic; Part V transfers to Symfony, Spryker and anything else.

## 26.3 AI-Assisted Development

### The problem, specific to this library

The public corpus is full of v1 and v2 NeuronAI code. A coding assistant will confidently produce `use NeuronAI\Agent;`, `new Edge(NodeA::class, NodeB::class)` and `chat()` without `getMessage()` — because that is what most of the internet says.

Worse: the assistant will be *fluent* about it. Wrong code with a confident explanation is harder to catch than wrong code that looks uncertain.

### Three fixes, in order of effectiveness

**1. Laravel Boost guidelines.** The Laravel SDK ships current guidelines for coding assistants (Section 17.7). Nothing to configure — install the package and they are there.

**2. Documentation over MCP.** The framework offers an MCP server for its documentation. Connect it to your assistant and it reads current docs rather than recalling stale training data.

This is a satisfying loop: **Chapter 9 taught MCP as a way to give your agents capabilities. Here you use it to give your assistant knowledge about the framework you are building agents with.**

**3. A project rules file.** Whatever your assistant reads — `CLAUDE.md`, `.cursorrules`, or equivalent:

```markdown
# NeuronAI conventions for this project

Target version: neuron-core/neuron-ai ^3.15

## Namespaces (v3 — do not use v1/v2 forms)
- `NeuronAI\Agent\Agent`     NOT `NeuronAI\Agent`
- `NeuronAI\Agent\SystemPrompt`  NOT `NeuronAI\SystemPrompt`

## API
- `chat()` returns a response — always call `->getMessage()`
- `stream()` returns a handler — call `->events()`, chunks are objects (`$chunk->content`)
- Workflows use `init()` / `run()`, NOT `start()` / `getResult()`
- The `Edge` class does not exist — nodes wire via `__invoke` type hints

## Project rules
- Tools are classes, never inline closures
- Toolkits filtered with `only()`, never `exclude()`
- Write tools: `setMaxRuns(1)` + idempotency guard + transaction
- Every pre-interrupt LLM call wrapped in `checkpoint()`
- Tenant scope is a constructor dependency, never read from ambient context
```

Thirty lines, and they encode most of this book's practical rules. Write your own version and put it in the repository — it is the cheapest way to stop a well-meaning assistant from undoing decisions you made deliberately.

### The honest caution

Appendix A is the evidence. **The official documentation itself has drifted from the code in forty-four places** — wrong namespaces, misspelled class names, three different constructor signatures for one class, two different execution APIs on adjacent pages.

An assistant reading that documentation inherits every one of those errors.

The discipline, which is the same one this book has applied throughout:

**Use assistants for shape.** Scaffolding, boilerplate, test fixtures, repetitive DTOs. They are genuinely good at this.

**Verify anything touching the API surface** against your installed version — your IDE's go-to-definition, or `vendor/` directly.

**Never trust a version claim.** If an assistant says "in NeuronAI v3 you do X", check. It has no reliable way to know.

That habit transfers well beyond this framework, and it is the right note to end on: **the tools are useful and they are not authoritative, and knowing the difference is what makes you the engineer in the loop.**

### Key takeaways

- The public corpus is full of v1/v2 code; assistants reproduce it fluently.
- Three fixes: Boost guidelines, documentation over MCP, a project rules file.
- The documentation itself has drifted — assistants inherit its errors.
- Use assistants for shape, verify the API surface, never trust a version claim.

## Afterword

Twenty-six chapters ago, Chapter 1 drew a four-rung ladder and asked one question: *who decides what happens next?*

Everything since has been the machinery required to let a model answer it safely. Tools to give it hands. Structure to make its output usable. Retrieval to give it knowledge. Workflows to give it shape. Interruption to keep a human in the decision. Observability to find out what it actually did.

None of that is specific to NeuronAI, and very little of it is specific to PHP. The framework will change — that is what Section 26.1 is about. The arithmetic in Section 1.4, the four-part tool description in Section 5.4, the difference between filtering at retrieval and filtering after, the fact that a resumed node re-executes from the top: those survive the framework, and they are what you actually learned.

There is one question left, and it is the one to ask about every agent you deploy from here:

> **What is the worst thing it can do, and what stops it?**

If you can answer that, you are ready.
