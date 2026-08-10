# How to Use This Book {.unnumbered}

## The three-beat structure

Almost every subject in this book is presented three times, at increasing levels of comfort.

**First the theory.** What is actually happening underneath — the agent loop, tokens and cost, embeddings, the event-driven model. No code. These sections exist so that when a framework does something for you, you know precisely what it is doing.

**Then plain PHP.** The same idea implemented with Composer and a CLI script, no framework, no magic, no service container. You see every object being constructed and every call being made.

**Then Laravel.** The same idea again, integrated into a real application: dependency injection, Eloquent, queues, HTTP, an interface a user can look at.

This "naked first, dressed second" order is deliberate. PHP developers tend to distrust magic, correctly, and the fastest way to make a framework feel trustworthy is to show what it replaced. If you already know Laravel well you can move quickly through the plain-PHP implementations, but do not skip them: Parts II through IV are where the concepts are actually taught, and Part V assumes all of them.

## The six parts

**Part I — Foundations** (Chapters 1–2). No code at all. The autonomy ladder, the agent loop, the anatomy of a model call, what a context window costs, why prompting is not programming, where NeuronAI sits among the Python frameworks, and how NeuronAI is put together. Two chapters, and they are the ones that change how you design.

**Part II — Plain PHP and Composer** (Chapters 3–10). Setup and your first agent, messages and memory, tools in depth, structured output with validation, streaming, multimodality, MCP, and observability with evaluation in CI. This is the longest part of the book and the core of it.

**Part III — Retrieval** (Chapters 11–12). Why retrieval exists and what it does not solve, then the NeuronAI pipeline end to end: loaders, splitters, embeddings, vector stores, metadata filtering, reindexing, and pre- and post-processors.

**Part IV — Workflows** (Chapters 13–16). The event-driven model, loops and branches, typed state, streaming from inside a workflow, human-in-the-loop with checkpointing and resumption, and multi-agent orchestration.

**Part V — Laravel** (Chapters 17–23). The SDK, facades and dependency injection, chat history in Eloquent, multi-tenancy, tools over your real models, retrieval over application data, SSE and Livewire streaming, approval workflows in production, cost control, resilience, security, and a deployment checklist.

**Part VI — Capstones** (Chapters 24–26). Two full projects, then version strategy, the surrounding ecosystem, and AI-assisted development.

## Running the code

### The companion repository

The examples are written to be typed, but they also exist as a repository organised as a monorepo:

```
neuron-course/
├── 01-plain-php/          # Composer, CLI, zero framework
│   ├── composer.json
│   ├── .env.example
│   ├── src/
│   └── examples/          # one script per chapter section
├── 02-laravel-app/        # Laravel 12 + neuron-laravel
└── 99-capstone/           # the final projects
```

Each section has a Git tag, so `git checkout chapter-05-tools` puts you at the exact starting state for that section. The repository ships a committed `composer.lock`, which means the API you get is the API this book was written against, even years from now. If a snippet in the book disagrees with the library you installed today, the lock file is the tiebreaker for what the text meant.

### Providers, and how not to spend money

API cost is the single biggest reason people abandon a project like this halfway through. The labs are structured so that it is not a factor.

**Install Ollama and pull two models.** Everything in Parts II through IV is designed to run locally, free, and offline:

```bash
ollama pull qwen2.5:7b        # chat, tool calling, structured output
ollama pull nomic-embed-text  # embeddings for Part III
```

`qwen2.5:7b` is the recommended local model because it does tool calling and structured output competently, which many small models do not. If your machine struggles, a smaller quantisation will still complete every lab, just less reliably — and watching a weaker model fail at tool selection is genuinely instructive.

**Use a paid provider only where quality is the point.** Anthropic, OpenAI and Gemini appear in the exercises that depend on frontier-model tool-calling or structured-output quality, and in Part V where production behaviour is the subject. Each of those exercises says so at the top.

Chapter 3 dedicates a whole section to swapping providers, because a one-line provider change is NeuronAI's most immediately valuable feature and the one that keeps you from getting locked in while you are still learning.

## Conventions

**Code.** PHP 8.2+, `declare(strict_types=1)` in application files, explicit types where they help, and secrets in the environment rather than the source. Code blocks are complete enough to run unless the text says otherwise; where a snippet is a fragment, the surrounding class or function is shown in the block immediately before it.

**Names.** Every class name, namespace, method, package, command, file path and environment variable is written exactly as you must type it. Where the official documentation shows a different name from the one that works, the book uses the one that works and Appendix A records the discrepancy.

**Version notes.** Where an API changed between major versions, or where published material is still showing the old form, the text says so at the point of use. These are not asides; they are the difference between code that runs and code that does not.

**In practice.** Short asides marked *In practice* carry technique that does not fit the main line of argument — the thing you would be told by a colleague looking over your shoulder.

**Key takeaways.** Each section closes with the three or four claims worth remembering. If you are reviewing rather than reading, they are a usable index of the book's argument.

## Labs and capstones

Sixteen labs are distributed through the book, each at the end of the chapter whose material it exercises:

| Lab | Chapter | What you build |
|---|---|---|
| 1 | 3 | The plain-PHP project skeleton and your first working agent, switchable across three providers |
| 2 | 4 | An interactive multi-turn chat CLI with history on disk and a `/reset` command |
| 3 | 5 | A weather and calculator agent — a custom tool over a public API plus `CalculatorToolkit` |
| 4 | 5 | A database analyst agent over a real schema, read-only, with the schema narrowed to relevant tables |
| 5 | 6 | Typed, validated extraction: free-text order emails into an `Order` DTO with line items and totals |
| 6 | 8 | An agent that reads a screenshot of an invoice and returns a structured DTO |
| 7 | 10 | A PHPUnit suite over an agent with a fake provider and fake tools — no network, fully deterministic |
| 8 | 12 | Documentation retrieval at zero cost: Markdown ingestion, `FileVectorStore`, Ollama embeddings |
| 9 | 12 | The same retrieval on a production store with hybrid search |
| 10 | 16 | The content factory — researcher, writer, reviewer with a correction loop, human approval, publisher |
| 11 | 17 | `POST /api/ask` answered through the facade: five minutes from `composer require` to first response |
| 12 | 18 | Persistent per-user chat with multiple threads and history in the database |
| 13 | 19 | An e-commerce agent with `search_orders`, `get_order_status` and `request_refund` — refunds need approval |
| 14 | 20 | A company knowledge base: Eloquent articles, queue-indexed, answered with source citations |
| 15 | 21 | A chat interface streaming token by token, with a "using tool X" indicator |
| 16 | 22 | Refund approval end to end: the agent prepares the case, stops, a manager approves, the workflow resumes |

Some labs are walked through end to end, code and all. Others are specified rather than solved — requirements, acceptance criteria and the hints you need, with the implementation left to you. The proportion shifts deliberately as the book goes on: by Part V you have seen every pattern the lab needs, and being handed the answer would waste the exercise.

The labs are the book. Reading a chapter about tools teaches you what a tool is; writing one teaches you why tool descriptions are prompt engineering. Budget real time for them.

The two capstones in Part VI are deliberately larger and deliberately under-specified — they state requirements, not steps, because by that point deciding the steps is the skill being tested.

## The appendices

**Appendix A — Where the documentation drifts from the code.** Forty-four verified discrepancies between the official NeuronAI documentation and the shipped library, grouped by chapter, with probe scripts that settle them in bulk against your installed version. Read it before you write production code.

**Appendix B — Glossary.** The vocabulary, defined once.

## If you are in a hurry

If you need something working this week rather than understanding the field, read Chapter 1 (it will change what you decide to build), Chapter 3 (setup and first agent), Chapter 5 (tools), and Chapter 6 (structured output). That is enough to ship a useful rung-3 feature.

Then come back for Chapter 10, because the difference between a demo and a product is knowing what your agent actually did.
