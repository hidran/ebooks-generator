# Colophon {.unnumbered}

## Versions

The code in this book was written against:

| Component | Version |
|---|---|
| `neuron-core/neuron-ai` | ^3.x — v3 is current stable |
| `neuron-core/neuron-laravel` | ^1.3 — 1.3.0 requires `neuron-ai: ^3.15` |
| PHP | 8.1+ for the core package, 8.2+ for the Laravel SDK |
| Laravel | 10 to 13 |
| Ollama models | `qwen2.5:7b` (chat), `nomic-embed-text` (embeddings) |

Model identifiers appearing in examples — `claude-sonnet-4-5`, `gpt-4.1-mini`, `gemini-2.0-flash`, `mistral-large-latest` — were current when written and will not stay that way. Check your provider's model list rather than trusting any book, including this one.

Before relying on a version claim anywhere in these pages:

```bash
composer show neuron-core/neuron-ai --all
```

## Production

Written in Markdown. Built with pandoc into EPUB3 and a 6×9 inch DOCX, converted to PDF with LibreOffice. The EPUB is validated with epubcheck; the PDF page size is checked to be exactly 432 × 648 points.

The build tooling is a small set of shell scripts and Python helpers: `bookcfg.py` parses the book configuration, `make-metadata.py` produces the per-edition pandoc metadata, and `fix-pdf-trim.py` snaps the PDF to the exact trim size. Nothing in the pipeline calls an external service.

Diagrams are ASCII inside fenced code blocks — deliberately, so they survive reflow at any font size on any reader, which no raster image does.

## Editions

Published in English, Italian and Spanish. The Italian and Spanish editions are translations of the English text, governed by a shared glossary that pins product, package, class and command names as invariant and keeps entrenched industry vocabulary — prompt, token, tool, agent, workflow, embedding, streaming — in English.

Code is identical across all three editions. Comments, string literals and identifiers are never translated.

## Corrections

Software moves. If you find something in this book that no longer matches the library, Appendix A explains how to determine what is actually true on your installation — which is the answer this book would give you anyway.

## About the author

Hidran Arias builds and teaches PHP systems. This book grew out of a twenty-three-module course on the same material, and out of the conviction that the agentic-AI conversation has been conducted almost entirely in Python for reasons that have nothing to do with where the work actually is.

---

*Agentic AI in PHP with NeuronAI*
First edition, 2026
