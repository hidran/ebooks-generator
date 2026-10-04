# Chapter 27 — Version Strategy, the Ecosystem, and AI-Assisted Development

Three things nobody puts in the documentation, and all three will affect you within a month of shipping.

::: {.callout .callout-tip}
[Code for this chapter]{.callout-title}

This chapter is conceptual and has no standalone code, but the companion repository at [https://github.com/hidran/neuronai-php-book](https://github.com/hidran/neuronai-php-book) holds runnable versions of everything the book builds.
:::

## 27.1 Version Strategy

### The landscape

- **v4 is current.** This book is verified on the released tags: neuron-ai 4.0.2 and neuron-laravel 2.0.0, on Laravel 13 and PHP 8.5. The colophon records the same versions.
- **Pre-release 4.x is still in circulation.** The 4.x branch was public before the 4.0.0 tag, and its API changed on the way to the release: how a run is resumed, how a thread ID is bound, where chat history lives, where observability events are. Tutorials, sample repositories and any assistant trained in that window show this dialect. It is not v3, it is not 4.0.2, and no upgrade guide covers it; the sixth check below recognises it.
- **v3 is the previous major.** It is stable, widely deployed, and the version most tutorials written in 2025 and 2026 assume.
- **v1 and v2 are archived** but their documentation remains online at versioned paths, and their code is all over blogs, forums and answer sites.

::: {.callout .callout-warning}
[Which version do you actually have?]{.callout-title}

Before you rely on any version claim — including this book's — run:

```bash
composer show neuron-core/neuron-ai
```

and check the project's releases page. That command is the authority. This book is not. If a 4.x minor has shipped since publication, read its changelog against the chapters you depend on: the companion repository's contract tests exist precisely to catch the drift.
:::

### What changed between v3 and v4, and why it matters to you

Most NeuronAI code you will find online predates v4, whose workflow engine is built around **durable execution** — and several APIs have a different shape because of it. The older forms you will meet first, and what this book uses instead:

| Older code (v3) | This book (v4) | Where in this book |
|---|---|---|
| `Tool::make($name, $description)->setCallable(...)` | `Tool` is abstract; name and description are class properties | 5.2, 5.3 |
| `chat()` returns a response | `chat()` returns an `AgentState`; `getMessage()` can be `null` | 3.4 |
| `stream()` returns a handler with `events()` | `stream()` *is* the generator; `getReturn()` gives the state | 7.2 |
| `$workflow->init()->run()` | `$workflow->run()` | 13.3 |
| An interrupt throws `WorkflowInterrupt` | A pause is a result: `$state->isInterrupted()` | 15.1 |
| `resume` with a request object | `submitInputs($payload)->run()` or `run(ExecutionRequest::resume($payload))`, addressed by workflow ID | 15.4 |
| `MyAgent::make()->chat(...)`, no ID needed | An ID is bound first: `make(workflowId: $threadId)` or `setThreadId()` | 3.4 |
| `chatHistory()` returning `FileChatHistory`, `SQLChatHistory` or `EloquentChatHistory` | `messageStore()` returning `FileMessageStore`, `SQLMessageStore` or `EloquentMessageStore` | 4.3 |
| `checkpoint()` | `memoize()` — `checkpoint()` survives, deprecated | 15.5 |
| `ToolApproval` middleware | `approvalPolicy()` on the tool; `submitApprovalDecisions()` on the agent | 5.10, 15.5 |
| `withFilters()` on the store | A `DocumentSchema` plus `retrievalScope()` | 12.5, 20.1 |
| `observe(new InspectorObserver(...))` | PSR-14 events: `subscribe()` a listener | 10.2 |

Underneath, every completed node is a **durable step**, committed to the workflow store and replayed rather than re-run after a crash or a pause. Agent and RAG are workflows (Section 2.3), so they inherit that durability, which is why a chat can be refused with `RunInFlightException` while an approval is pending on the same thread. The node that *paused* still re-executes from the top on resume (Chapter 15).

### The six-check diagnostic

When you find sample code that does not work — or that looks right and you are not sure:

1. **Check the `use` statements.** `NeuronAI\Agent;` without a second segment means v2 or earlier.
2. **Check for `->getMessage()`.** Its absence after `chat()` means v2.
3. **Check for `Edge` or `addEdges()`.** That is v1.
4. **Check for `->start()->getResult()`.** That is the v2 workflow API.
5. **Check for `->init()`, `catch (WorkflowInterrupt`, `ToolApproval` or `setCallable()`.** Any of them means v3.
6. **Check for the pre-release 4.x dialect:** `->resume(`, `make(threadId:`, `setChatHistory(`, any `*ChatHistory` class, `abandonRun(`, `acknowledgeCompletion(`, or `NeuronAI\Observability\Events\`. Any of them means a pre-release of v4. It looks current, and it fails on 4.0.2 — not always loudly: an agent that still overrides `chatHistory()` runs, and quietly keeps the conversation in memory.

Six checks, and they identify the version of almost any snippet in seconds. It is worth keeping them somewhere you can find them.

### Surviving a fast-moving dependency

Six practices, all of which apply to any library moving faster than your release cycle:

**Pin the version and commit `composer.lock`.** Not just in applications — in any repository someone else will clone and expect to work. The lock file is what makes "it worked last year" reproducible, and `composer.json` should require the exact version you verified (`"neuron-core/neuron-ai": "4.0.2"`), not `^4.0`: a caret range means `>=4.0.0 <5.0.0`, so the next `composer update` can move you to any later 4.x release without anyone having decided to.

**Record the version where the code lives.** A line in your README, a constant, a comment at the top of the agent namespace. When someone debugging in eighteen months asks "what were we written against?", they should not have to guess.

**Keep an errata file.** When you find a discrepancy between the documentation and the shipped code — and Appendix A shows there are dozens — write it down where your team will see it. The next person to hit it will otherwise spend the same afternoon you did.

**Separate durable knowledge from perishable knowledge.** Your notes about tool description design, chunking strategy and the agent loop stay true across major versions. Your notes about method signatures do not. Keeping them in different documents means a major upgrade invalidates one file rather than all of them.

**Do not chase a new major immediately.** Let the ecosystem catch up, then upgrade deliberately. A library release should be a decision you make, not an outage you discover. The same goes for pre-releases: an API can still move between a pre-release and its tag, so code verified on one is not verified on the other. This book's own listings were written on the 4.x branch and had to be re-verified against 4.0.2.

**Read the upgrade guide before the changelog.** The changelog tells you what changed; the upgrade guide tells you what to do about it. NeuronAI's guide to v4 is fifty-seven numbered guides plus a guide 0, each with search patterns and before/after code — and it ships *inside the package*, in `vendor/neuron-core/neuron-ai/upgrade/`, so the version you read is the version you installed. The website can lag the code; the in-package guide cannot. They migrate from 3.x, so a pre-release needs the sixth check first.

An upgrade, then, goes in this order. Do it on a branch. Bump the version. Run static analysis before anything else: removed classes and methods show up there as errors, before a single test runs. Run your contract tests. Work through the in-package guides in order, starting with guide 0 (it reinstalls the agent skills), applying only what their search patterns match in your code. Run your evals last, because they are what notices a change in behaviour that still type-checks.

### Key takeaways

- v4 is current; v3 code is the most common thing you will find, and v1/v2 code is still everywhere. None of it compiles against v4 unchanged.
- Older code differs in concept, not just syntax: v4 has durable steps, pauses as results, approval on the tool.
- Six checks identify a snippet's version in seconds, the pre-release 4.x dialect included.
- The upgrade guide ships in `vendor/`; read that one, not the website's.
- `composer show neuron-core/neuron-ai` is the authority on what you actually have.
- Pin the exact version and the lock file, record the version, keep an errata file.
- Upgrade on a branch: static analysis, contract tests, the in-package guides from guide 0, then evals.
- Separate durable concepts from perishable API so an upgrade invalidates one document, not all of them.

## 27.2 The Ecosystem

### Maestro — a complete application to read

**Maestro is the first CLI agent built entirely in PHP with NeuronAI.** It is a coding assistant in the shape of the terminal assistants you may already use, and it is open source.

```bash
composer global require neuron-core/maestro
```

On Windows, install and run it under WSL.

It supports eight of the providers NeuronAI ships — Anthropic, OpenAI, Gemini, Cohere, Mistral, Ollama, Grok, DeepSeek — routed through a provider factory, and integrates Inspector via an `inspector_key` in `.maestro/settings.json`.

**Why it belongs at the end of this book.** The author's own assessment is the point:

> The framework doing the heavy lifting here is Neuron AI, specifically the workflow architecture introduced in v3. Without the ability to interrupt execution mid-agent-loop and resume it based on user input, the tool approval system would require significantly more scaffolding to build and maintain. This pattern — interrupt, present, resume — would have been painful to implement without a workflow-oriented framework underneath.

That is Chapter 15, validated by a real application. Having finished Part IV, you can read Maestro's source and recognise every pattern in it. Check its `composer.json` first: the quote describes the v3 architecture, and an application of Maestro's size moves to a new major on its own schedule. If it still targets v3, reading it is also a good exercise in the six-check diagnostic above.

**Two features worth studying specifically:**

**The tool approval system** — interactive confirmation before sensitive operations. Section 15.5's tool approval, in production.

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

The framework is deliberately framework-agnostic. The core package itself declares PHP 8.1 with `ext-curl`; this book's code, like the companion repository, needs PHP 8.5.

**Symfony.** Everything from Parts II to IV applies directly. Register agents as services; `SQLMessageStore` takes a plain PDO, which you get from a Doctrine connection with `getNativeConnection()`. Inspector ships `inspector-symfony`.

**Spryker, WordPress, legacy in-house.** Same story. The core package has no framework dependencies. The Laravel SDK is, in the maintainers' own words, something you can use *as inspiration to design your own custom integration pattern.*

The framework's positioning argument is worth quoting:

> Rather than fragmenting innovation across framework-specific solutions, Neuron enables collaboration between Laravel developers, Symfony contributors, WordPress plugin authors, and custom framework teams.

If you are not on Laravel, Part V of this book is a case study rather than a prerequisite. The integration points it describes — a service container, a queue, a database, an HTTP layer — exist in every framework worth using.

### Key takeaways

- Maestro is a complete open-source application built on the patterns in this book — read it.
- Neuron Hub is a realistic first open-source contribution.
- Studio generates code; it does not replace understanding it.
- The core package is framework-agnostic; Part V transfers to Symfony, Spryker and anything else.

## 27.3 AI-Assisted Development

### The problem, specific to this library

The public corpus is full of v1, v2 and v3 NeuronAI code, and of pre-release 4.x code. A coding assistant will confidently produce `use NeuronAI\Agent;`, `new Edge(NodeA::class, NodeB::class)`, `->init()->run()` and a `ToolApproval` middleware — because that is what most of the internet says. One trained on the pre-release will write `Agent::make(threadId: $id)` or `->resume($payload)->run()` instead: they look right, and they fail on 4.0.2.

Worse: the assistant will be *fluent* about it. Wrong code with a confident explanation is harder to catch than wrong code that looks uncertain.

### Three fixes, in order of effectiveness

**1. The framework's own agent material.** NeuronAI ships guidance for coding assistants inside the package: an `AGENTS.md` beside each module in `vendor/neuron-core/neuron-ai/src/`, a set of agent skills, and the upgrade guide in `upgrade/`, which is written to be executed step by step by an assistant. On a project upgraded from an older version, reinstall the skills first — the old ones describe the old API. On Laravel, take care (Section 17.7): the Boost skills bundled with neuron-laravel 2.0.0 lag the core package and still teach removed forms — `make(threadId:)`, `setChatHistory()`, `resume()`, an `approvalPolicy(array $inputs)` signature. Point your assistant at the current skills in `vendor/neuron-core/neuron-ai/skills/` instead; they include `neuron-laravel-integration`, which the Laravel package lacks. Treat all of it as better than training data and worse than the code.

**2. Documentation over MCP.** The framework offers an MCP server for its documentation. Connect it to your assistant and it reads current docs rather than recalling stale training data.

This is a satisfying loop: **Chapter 9 taught MCP as a way to give your agents capabilities. Here you use it to give your assistant knowledge about the framework you are building agents with.**

**3. A project rules file.** Whatever your assistant reads — `CLAUDE.md`, `.cursorrules`, or equivalent:

```markdown
# NeuronAI conventions for this project

Verified version: neuron-core/neuron-ai 4.0.2 (Laravel SDK: neuron-core/neuron-laravel 2.0.0)
Require it exactly (`"neuron-core/neuron-ai": "4.0.2"`), never `^4.0`: a caret range accepts every later 4.x
Code from v1-v3 or from a pre-release 4.x is wrong here, even when it looks current

## Namespaces (do not use v1/v2 forms)
- `NeuronAI\Agent\Agent`     NOT `NeuronAI\Agent`
- `NeuronAI\Agent\SystemPrompt`  NOT `NeuronAI\SystemPrompt`
- Observability events: `NeuronAI\Agent\Observability\`, `NeuronAI\Workflow\Observability\`, `NeuronAI\RAG\Observability\`

## API (4.0.2 — do not use v3 or pre-release forms)
- `chat()` returns `AgentState` — `->getMessage()?->getContent()`
- `stream()` is the generator — iterate it; chunks are objects; `->getReturn()` for the state
- Workflows: `->run()` / `->events()`, NOT `init()`; no `Edge` class
- A pause is a result: check `$state->isInterrupted()`, never catch `WorkflowInterrupt`
- Resume with `->run(ExecutionRequest::resume($payload))` or `->submitInputs($payload)->run()`; there is no `resume()` method
- Bind an ID before any run: `make(workflowId: $id)` or `setThreadId($id)`; `make(threadId: ...)` does not exist
- Memory is `messageStore()` returning a `MessageStoreInterface` (`SQLMessageStore`, `EloquentMessageStore`); no `*ChatHistory` classes, no `setChatHistory()`
- Tools extend `Tool`; `$name` / `$description` are properties, not constructor args
- Approval lives on the tool (`approvalPolicy()`), NOT in a `ToolApproval` middleware

## Project rules
- Tools are classes, never anonymous
- Toolkits filtered with `only()`, never `exclude()`
- Write tools: `setMaxRuns(1)` + idempotency guard + transaction
- Every pre-interrupt LLM call wrapped in `memoize()`
- Tenant scope is a constructor dependency, never read from ambient context
- When a snippet, a skill or your memory disagrees with `vendor/neuron-core/neuron-ai/`, the source wins
```

Twenty-nine lines, and they encode most of this book's practical rules. Write your own version and put it in the repository — it is the cheapest way to stop a well-meaning assistant from undoing decisions you made deliberately.

### The honest caution

Appendix A is the evidence. **The official documentation itself has drifted from the code in dozens of places** — wrong namespaces, misspelled class names, signatures the code dropped a release ago.

An assistant reading that documentation inherits every one of those errors.

The discipline, which is the same one this book has applied throughout:

**Use assistants for shape.** Scaffolding, boilerplate, test fixtures, repetitive DTOs. They are genuinely good at this.

**Verify anything touching the API surface** against your installed version — your IDE's go-to-definition, or `vendor/` directly.

**Never trust a version claim.** If an assistant says "in NeuronAI v4 you do X", check. It has no reliable way to know.

That habit transfers well beyond this framework, and it is the right note to end on: **the tools are useful and they are not authoritative, and knowing the difference is what makes you the engineer in the loop.**

### Key takeaways

- The public corpus is full of v1–v3 and pre-release 4.x code; assistants reproduce it fluently.
- Three fixes: the framework's in-package agent material (on Laravel, the neuron-ai skills rather than the bundled Boost ones), documentation over MCP, a project rules file.
- The documentation itself has drifted — assistants inherit its errors.
- Use assistants for shape, verify the API surface, never trust a version claim.

## Afterword

Twenty-six chapters ago, Chapter 1 drew a four-rung ladder and asked one question: *who decides what happens next?*

Everything since has been the machinery required to let a model answer it safely. Tools to give it hands. Structure to make its output usable. Retrieval to give it knowledge. Workflows to give it shape. Interruption to keep a human in the decision. Observability to find out what it actually did.

None of that is specific to NeuronAI, and very little of it is specific to PHP. The framework will change — that is what Section 27.1 is about. The arithmetic in Section 1.4, the four-part tool description in Section 5.4, the difference between filtering at retrieval and filtering after, the fact that a resumed node re-executes from the top: those survive the framework, and they are what you actually learned.

There is one question left, and it is the one to ask about every agent you deploy from here:

> **What is the worst thing it can do, and what stops it?**

If you can answer that, you are ready.
