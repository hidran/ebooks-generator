# Design — *Agentic AI in PHP with NeuronAI* ebook

**Date:** 2026-08-10
**Book directory:** `books/neuron-course/`
**Status:** approved

---

## 1. Goal

Turn the existing 23-module video course under `books/neuron-course/` into a published
ebook in three languages (EN, IT, ES), each as EPUB3 and a 6×9 KDP paperback.

The source is written as **video narration**: lesson blocks separated by `═══` bars,
each carrying a duration, a lesson type, learning objectives, instructor stage
directions, and Google-Doc copy instructions. None of that belongs in a book. The
central work of this project is a faithful script → prose transformation that keeps
every line of code and every technical claim while removing all trace of the video
production it was written for.

**Scale:** ~84,000 words of source. The EN manuscript lands at roughly 85–90k words;
IT and ES roughly double that again, for ~250k words total.

## 2. Book identity

```yaml
slug: agentic-ai-php-neuron
title: "Agentic AI in PHP with NeuronAI"
subtitle: "From your first agent to multi-agent systems in production with Laravel"
author: "Hidran Arias"
date: "2026"
primary_language: en
trim: "6x9"
formats: [epub, paperback]
keywords: [agentic ai, php, neuronai, laravel, ai agents, rag, llm]
editions: en (primary), it (translate_from en), es (translate_from en)
```

The slug differs from the directory name on purpose: the directory `neuron-course/`
records where the material came from, while the slug names the build outputs
(`agentic-ai-php-neuron.epub`, `-it.epub`, `-es.epub`). `build-book.sh` resolves the
book by directory and names outputs from the slug, so both hold.

### Library naming

The library is **NeuronAI**. The course material calls it "Neuron" throughout, which
reads as a different product from the `NeuronAI\` namespace a reader actually types.
The book normalizes to `NeuronAI` in all prose, headings and part titles, with the
preface anchoring it once: *NeuronAI, installed as `neuron-core/neuron-ai`, documented
at neuron-ai.dev.*

Code is never touched. `NeuronAI\Agent\Agent`, `composer require neuron-core/neuron-ai`,
`vendor/bin/neuron`, and every URL stay verbatim. The glossary pins `NeuronAI` as an
invariant term so the IT and ES editions cannot drift to "Neurone" or back to "Neuron".

## 3. Source material handling

The 13 course files move from the book root into `books/neuron-course/course-material/`.

They deliberately do **not** go into `sources/`, which `.gitignore` excludes — the course
scripts are authored work, not raw input like video or PDF, and must stay versioned.
`course-material/` keeps them tracked while leaving the book root clean for
`manuscript/`, `editions/` and `build/`.

The material is read-only input. The manuscript is written fresh from it; the course
files are never edited in place.

`00-curriculum/00-course-curriculum.md` is an Italian production plan for recording the
course, not book content. It is not converted. Its durable parts — the teaching repo
layout, the Ollama-first provider strategy, the theory → plain PHP → Laravel structure —
fold into the front matter chapter *How to use this book*.

## 4. Structure

23 modules become 26 chapters across 6 parts.

```
manuscript/
  00-front-matter/
    01-copyright.md
    02-preface.md
    03-how-to-use-this-book.md
  parte-1/  00-part.md · cap-01 · cap-02
  parte-2/  00-part.md · cap-03 … cap-10
  parte-3/  00-part.md · cap-11 · cap-12
  parte-4/  00-part.md · cap-13 … cap-16
  parte-5/  00-part.md · cap-17 … cap-23
  parte-6/  00-part.md · cap-24 · cap-25 · cap-26
  zz-back-matter/
    01-appendix-a-doc-drift.md
    02-appendix-b-glossary.md
    03-colophon.md
```

| Part | Chapters | Source | Subject |
|---|---|---|---|
| I — Foundations | 1–2 | `modules-01-02-foundations.md` | autonomy ladder, agent loop, cost, NeuronAI architecture |
| II — Plain PHP | 3–10 | 5 files in `02-part-2-plain-php/` | setup, memory, tools, structured output, streaming, multimodal, MCP, observability |
| III — RAG | 11–12 | `modules-11-12-rag.md` | retrieval theory, the NeuronAI RAG pipeline |
| IV — Workflows | 13–16 | `modules-13-16-workflows-and-multi-agent.md` | events, state, HITL, multi-agent |
| V — Laravel | 17–23 | 2 files in `05-part-5-laravel/` | SDK, Eloquent history, tools, RAG, SSE, approvals, production |
| VI — Capstones | 24–26 | `capstones-and-bonus-modules.md` | Repo Auditor CLI, Agentic Support Desk, version strategy + ecosystem + AI-assisted development |

**Part dividers.** Each `00-part.md` holds a single `# Part N — Title {.unnumbered}` plus
a short orienting paragraph. `build-book.sh` runs pandoc with `--split-level=1`, so every
H1 opens a new EPUB page; the divider therefore renders as a real part-title page.
`find | sort` orders `00-part.md` before `cap-01.md`, and `parte-1` … `parte-6` sort
correctly as single digits.

**Chapter file shape.** One `#` H1 per file (the chapter title). Lessons become `##`
sections numbered to match the source (`## 5.3 Tools as Classes`), so a reader who also
owns the course can navigate between them. Sub-sections are `###`.

**Labs stay in their chapters.** Labs are the payoff of the material they follow, and an
appendix would separate them from the concepts they exercise. Each becomes a numbered
exercise section at the end of its own chapter:

| Lab | Chapter |
|---|---|
| Lab 1 — plain PHP setup (from `00-curriculum/01-lab-01-...`) | 3 |
| Labs 3–4 — weather/calculator, database analyst | 5 |
| Labs 8–9 — documentation RAG, hybrid-search store | 11, 12 |
| Lab 10 — the content factory | 16 |

## 5. Script → prose transformation

The transformation is editorial, not generative: no new technical claims, no invented
APIs, no dropped code.

**Removed**

- `═══` separator bars and "copy each lesson block into its own Google Doc"
- `**Duration:** 12 minutes` and `**Type:** Theory, no code` lines
- Stage directions with no reader value — "draw the ladder on screen", "demo this live",
  "put a card in the video"

**Kept verbatim**

- Every code block, shell command, table, and ASCII diagram
- Key takeaways, as the closing beat of the section they belong to

**Rewritten**

- `## LESSON 5.3 — Tools as Classes` → `## 5.3 Tools as Classes`
- Learning objectives dissolve into the section's opening prose rather than standing as a
  bulleted block
- Substantive instructor notes become *In practice* asides; only the ones carrying real
  technique survive
- Course deixis → book deixis: "in this course" → "in this book", "in the next video" →
  "in the next chapter", "students" → "you"

### Corrections applied at the source

The course README records three defects. All are fixed in the manuscript, not merely
noted:

1. **Lab 1 streaming uses the v2 API.** `foreach ($agent->stream(...) as $chunk) echo $chunk;`
   is replaced by the v3 form — `stream()` returns a handler, `events()` yields chunk
   objects, and the content is `$chunk->content`.
2. **There is no pgvector store.** NeuronAI does not ship one. Lab 9 is built on
   **PHPVector** (pure PHP, HNSW + BM25, no infrastructure) and Chapter 20 recommends
   **MariaDB 11.7+**. First-party stores are listed accurately: Memory, File, PHPVector,
   MariaDB, Pinecone, Weaviate, Elasticsearch, OpenSearch, Typesense, Qdrant, ChromaDB,
   Meilisearch.
3. **No verifiable v4.** v3 is current stable; the Laravel SDK 1.3.0 requires
   `neuron-ai: ^3.15`. The planned "upgrading to v4" bonus module becomes a durable
   **version strategy** chapter instead.

## 6. Back matter

**Appendix A — Where the documentation drifts from the code.** The 44-item verification
checklist, reframed from a pre-recording task list into a reader's reference: what to
check against your installed version, the probe scripts that settle each cluster at once,
and the six items that matter most. The "turn this into a selling point" section is
marketing advice for the course author and is dropped.

**Appendix B — Glossary.** Reader-facing terms, sharing its term list with the
translation glossary but written as definitions.

**Colophon.** Toolchain, verified library versions, build date.

## 7. Figures

The source contains no images; all its diagrams are ASCII inside fenced blocks, which
render correctly in both EPUB and DOCX. The book therefore ships with no `figures/`
content, and `--resource-path` needs nothing beyond the defaults. If diagrams are added
later they follow the repo convention: `figures/cap-XX/name.png`, referenced
book-root-relative as `figures/cap-XX/name.png` with no `../`.

## 8. Translation

IT and ES are translated in-session from the finished EN manuscript into
`editions/<lang>/manuscript/`, preserving the file tree exactly.

`glossary.md` is written before translation begins and governs both editions. It pins:

- **Invariant:** NeuronAI, Laravel, Composer, Eloquent, Ollama, and all class, package
  and command names
- **Kept in English:** prompt, token, tool, agent, workflow, embedding, chunk, context
  window, streaming, checkpoint, human-in-the-loop, deploy, endpoint
- **Translated:** ordinary prose, chapter and section titles, key takeaways

Per-edition `title` and `subtitle` overrides live in `book.yaml`;
`tools/lib/make-metadata.py` already honours them.

## 9. Build and verification

```bash
bash tools/build-book.sh --book neuron-course --edition en
```

Each edition must pass, with output recorded:

- `epubcheck` — clean
- `pdfinfo` page size — exactly `432x648` pt
- Every chapter file non-empty and present in the EPUB TOC
- No `═══` bars, `**Duration:**` lines, or Google-Doc references anywhere in the manuscript

## 10. Milestones

Each milestone is independently verifiable and independently useful.

1. **EN edition** — scaffold, manuscript, build, epubcheck + trim verified
2. **IT edition** — translation, build, verified
3. **ES edition** — translation, build, verified

## 11. Out of scope

- Recording, publishing, or distributing the course itself
- Building the companion teaching repository with per-lesson Git tags
- Actually running the 44 verification probes against an installed NeuronAI (the book
  tells the reader how; it does not claim the result)
- Cover art
