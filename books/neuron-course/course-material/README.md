# Agentic AI in PHP with Neuron
### Complete course material — lesson scripts, labs, capstones

**Author:** Hidran Arias
**Framework:** [Neuron](https://www.neuron-ai.dev/) — `neuron-core/neuron-ai` ^3.x
**Language:** English
**Scale:** 23 modules · ~132 lessons · 10 labs · 2 capstone projects

---

## How to use these files

Every lesson is separated by a `═══` bar. **Copy one lesson block per Google Doc.**

Each lesson contains:

- Duration and type (theory / hands-on / lab)
- Learning objectives
- Theory written as narration you can read aloud
- Runnable code examples
- Instructor notes marking the moments worth demonstrating live
- Key takeaways

---

## Index

### `00-curriculum/`

| File | Contents |
|---|---|
| `00-course-curriculum.md` | Full syllabus: 23 modules, structure, repo layout, materials to produce |
| `01-lab-01-plain-php-setup.md` | Standalone starter lab (⚠ see corrections below) |

### `01-part-1-foundations/` — Modules 1–2 · 12 lessons

Conceptual foundation. The autonomy ladder, the agent loop, cost arithmetic, non-determinism, and Neuron's architecture.

**Key lesson:** 1.4 (the cost table showing a five-step agent at ~12× a single call) and 2.3 (Agent and RAG *are* Workflows — stated early, which the official docs reveal late).

### `02-part-2-plain-php/` — Modules 3–10 · 51 lessons

Plain PHP + Composer. No framework. Setup, agents, memory, tools, structured output, streaming, multimodality, MCP, observability and evals.

| File | Modules |
|---|---|
| `modules-03-04-setup-and-memory.md` | Setup, first agent, SystemPrompt, provider swap, messages, chat history |
| `module-05a-tools-part1.md` | Tools: theory, inline, classes, descriptions, property types, toolkits |
| `module-05b-tools-part2-and-labs.md` | Filters, max runs, visibility, error handling, provider tools, parallel + Labs 3–4 |
| `modules-06-07-structured-output-and-streaming.md` | Typed output with validation retry; streaming and chunk types |
| `modules-08-09-10-multimodal-mcp-observability.md` | Attachments, MCP, Inspector, evals, CI |

### `03-part-3-rag/` — Modules 11–12 · 12 lessons + 2 labs

Retrieval theory and the Neuron pipeline: loaders, splitters, embeddings, vector stores, metadata, reindexing, pre/post-processors.

### `04-part-4-workflows/` — Modules 13–16 · 18 lessons + Lab 10

The event-driven model, loops and branches, state, streaming, human-in-the-loop with checkpointing, and multi-agent orchestration.

**Key lesson:** 15.5 — a resumed node re-executes from the top, so an un-checkpointed LLM call can produce *different content from the one the human approved*. A correctness bug with a one-line fix.

### `05-part-5-laravel/` — Modules 17–23 · 39 lessons

| File | Modules |
|---|---|
| `modules-17-20-sdk-agents-tools-rag.md` | SDK setup, facades, DI, Eloquent history, multi-tenancy, tools, RAG on app data |
| `modules-21-23-streaming-hitl-production.md` | SSE and Livewire, approval workflows in production, cost, resilience, security, deployment checklist |

### `06-part-6-capstones/`

Capstone A (Repo Auditor CLI, plain PHP), Capstone B (Agentic Support Desk, Laravel), plus three bonus modules: version strategy, the ecosystem, and AI-assisted development.

---

## ⚠ Corrections to apply

Three issues were found while writing later parts. All are noted inline in the affected files; collected here so nothing is missed.

### 1. Lab 01 streaming snippet uses the v2 API

`00-curriculum/01-lab-01-plain-php-setup.md`, section 6.

```php
// WRONG for v3
foreach (AssistantAgent::make()->stream(new UserMessage($prompt)) as $chunk) {
    echo $chunk;
}
```

```php
// CORRECT for v3 — stream() returns a handler; events() yields chunk OBJECTS
$handler = AssistantAgent::make()->stream(new UserMessage($prompt));

foreach ($handler->events() as $chunk) {
    echo $chunk->content;
}
```

Covered fully in Lesson 7.2.

### 2. There is no pgvector store

The curriculum listed pgvector for Lab 9 and Module 20. **Neuron does not ship one.** First-party stores: Memory, File, PHPVector, MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB, Meilisearch.

Lab 9 has been rewritten around **PHPVector** (pure PHP, HNSW + BM25, no infrastructure). **MariaDB 11.7+** is recommended for Module 20 — one table in the database you already run.

### 3. A "v4" could not be verified

The curriculum referenced a v4 beta and a bonus module about upgrading. Searches return only the v2→v3 upgrade guide. **v3 is current stable** — the Laravel SDK 1.3.0 (2026-06-29) requires `neuron-ai: ^3.15`.

Bonus module B1 is now a **version strategy** lesson, which is more durable regardless. Confirm with `composer show neuron-core/neuron-ai --all` before recording.

---

## Before you record

1. **Work through `VERIFICATION-CHECKLIST.md`.** 44 items where the official documentation disagrees with itself or with the code. Budget half a day. Mentioning that you did this is a strong trust signal in the free preview.

2. **Apply the three corrections above.**

3. **Build the teaching repository** with per-lesson Git tags (`git checkout lesson-05-tools`) and a committed `composer.lock`, so students following along in a year get the API you recorded against.

4. **Decide where Lesson 5.13 goes.** Parallel tool calls need `pcntl`, which is CLI-only. It may read better in Part V alongside queue workers, where students already have the infrastructure.

5. **Set up Ollama** (`qwen2.5:7b` + `nomic-embed-text`). Every lab in Parts II–IV is designed to run free and offline, which matters more for completion rates than any feature.

---

## The through-line

Twenty-three modules answering one question from Lesson 1.1 — *who decides what happens next* — and then building everything required to let a model answer it safely: tools to give it hands, structure to make its output usable, retrieval to give it knowledge, workflows to give it shape, interruption to keep a human in the decision, and observability to find out what it actually did.

The closing question from Lesson 23.6 is the one for the sales page:

> **What is the worst thing your agent can do, and what stops it?**
