# Design — NeuronAI course slide system

**Date:** 2026-08-12
**Book:** `books/neuron-course` (*Agentic AI in PHP with NeuronAI*)
**Status:** approved, pilot in progress

## Problem

The course has 126 lesson scripts in `books/neuron-course/course-material/`, of which
**47 are theory lessons** (~9.5 hours of video). Recording them against text-only
material wastes the strongest teaching asset in the scripts: they are full of
structures that are inherently visual — the autonomy ladder, the agent loop, the
cost curve, the RAG pipeline, the workflow graph.

The author needs slide decks carrying **diagrams, charts and bullet structure** for
the theory lessons, in English first and then Italian and Spanish.

## Decisions

| Question | Decision |
|---|---|
| Granularity | One `.pptx` per module (~20 files), lessons as sections within |
| First build | Module 1 pilot (7 lessons), style locked before scaling |
| Languages | English first; Italian and Spanish after the pilot is approved |
| Look | Dark technical — reads well in screen-recorded video |
| Format | Real `.pptx` via python-pptx, native editable shapes |

## Architecture — content/render split

Three languages × ~20 modules makes hand-authored decks untenable: a translation
would mean re-drawing every diagram. The split:

- **YAML spec holds text only.** Slide type plus its content strings.
- **Python engine holds all visual logic.** Geometry, palette, connectors, charts.

Translating a deck is translating a YAML file. Diagram geometry, code blocks,
numbers and identifiers never move — the same discipline as the book's translation
rules (CLAUDE.md §8), applied to slides.

```
tools/slides/                     ← engine (shared, versioned)
  deckgen/
    theme.py      palette, type scale, geometry tokens
    deck.py       Deck wrapper: 16:9, background, footer, progress strip
    layouts.py    divider, objectives, bullets, cards, quote,
                  big-number, table, code, takeaways
    diagrams.py   flow_chain, cycle, stack, ladder, split_compare,
                  matrix, quadrant, flowchart, mapping
    charts.py     native pptx bar / stacked-column / line
  build-deck.py   CLI: build-deck.py <spec.yaml> -o <out.pptx>

books/neuron-course/slides/       ← content (versioned)
  en/module-01.yaml
  it/module-01.yaml
  es/module-01.yaml

books/neuron-course/build/slides/<lang>/*.pptx   ← output (gitignored by books/*/build/)
```

A slide declares a layout and its fields:

```yaml
- layout: ladder
  title: The autonomy ladder
  axis: {left: "Your code decides", right: "The model decides"}
  rungs:
    - {n: 1, label: "Bare LLM call", note: "one in, one out"}
    - {n: 4, label: "Agent", note: "model authors the control flow", accent: true}
```

## Native objects, not images

Every box is an autoshape, every arrow a connector, every chart a real pptx chart
with embedded data. Consequences that matter:

- The author can nudge a box or fix a typo mid-recording without regenerating.
- Vector output stays crisp at 4K recording resolution.
- No external toolchain — no mermaid CLI, no SVG rasteriser (neither is installed).

## Visual language

| Token | Value | Use |
|---|---|---|
| `bg` | `#16181D` | slide ground |
| `surface` | `#1F232B` | cards, diagram nodes |
| `surface_2` | `#272C36` | raised nodes, table header |
| `text` | `#ECEFF4` | headings, body |
| `muted` | `#8B93A3` | captions, inactive nodes |
| `accent` | `#7C6BF0` | the single emphasis colour |
| `warn` | `#E8A33D` | cost, ceilings, irreversible actions |
| `danger` | `#E4664F` | what breaks |
| `ok` | `#4FBF8B` | what survives |
| `line` | `#343A45` | rules, connectors |

One accent used sparingly is what makes 9 hours of video feel like one system.
Type: **Inter** for prose, **Menlo** for code and identifiers — both verified
present on the author's machine. Slide size 13.333 × 7.5 in (16:9).

## Per-lesson rhythm

Each lesson is a self-contained run that can be recorded straight through:

**Section divider** (number, title, duration) → **Objectives** → **content slides**
→ **Key takeaways**

A persistent footer carries `1.4 · Context Windows, Cost and Latency` plus a
segmented progress strip showing which lesson of the module is on screen, so a
viewer landing mid-course always knows where they are.

## Module 1 inventory (~62 slides)

| Lesson | Signature visual |
|---|---|
| 1.1 Autonomy Ladder | 4-rung ladder with a "who decides next" axis; rung-1 and rung-4 flow chains |
| 1.2 Agent Loop | cyclic loop diagram with decision diamond and exit branch; model-cannot-execute barrier; 6-step worked-example sequence table |
| 1.3 Anatomy of a Call | request-envelope stack; role chips; system-prompt quadrant |
| 1.4 Cost & Latency | stacked-column chart of input vs output tokens over 5 iterations with cumulative line; token-scale bar chart; context-ceiling diagram with 5–10% headroom band; `$60/day → $700/day` contrast |
| 1.5 Non-Determinism | divergence diagram (one prompt → three outputs); what-breaks → what-replaces-it mapping |
| 1.6 The Landscape | Python-microservice-beside-PHP vs Neuron-inside-the-app; LangGraph↔Neuron concept map |
| 1.7 Decision Framework | Q1→Q4 decision flowchart branching to rungs; 4-case × 4-question matrix; escalation ladder |

Every primitive Module 1 needs is reused across the remaining 40 theory lessons.
That is why Module 1 is the correct pilot: it exercises the whole engine.

## Verification

- `tests/test_deckgen.py` — theme tokens, spec→slide-count, every layout renders
  without text overflow.
- Generated decks are rendered to images and inspected visually before hand-off.
  No "looks right" claim without looking.

## Out of scope

- Hands-on and lab lessons (65 of them) — those are screen recordings, not slides.
- Video editing, narration, or export to formats other than `.pptx`.
