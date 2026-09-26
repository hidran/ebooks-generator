# Colophon {.unnumbered}

## Versions

The code in this book was written against, and verified on:

| Component | Version |
|---|---|
| `neuron-core/neuron-ai` | 4.x — verified on commit `df30064`, shortly before the 4.0.0 tag |
| `neuron-core/neuron-laravel` | 2.x — verified on commit `399936c`; requires `neuron-ai` 4.x |
| PHP | 8.5 with `ext-curl` for the book's code — verified on 8.5.4 (the `neuron-ai` package itself declares `^8.1`) |
| Laravel | 13 |
| Ollama models | `llama3.2` (chat), `nomic-embed-text` (embeddings) |

Every PHP listing in the book was compiled with PHP 8.5.4, with all deprecations reported. The companion repositories' code, from which most listings are taken, passes PHPStan at level 8 against those versions. The companion repository's examples were also executed — against a local Ollama model where they need one, and against the framework's own fake provider where they do not; the few that need infrastructure a laptop does not run, such as a MariaDB vector store, were checked statically only. The companion repository's contract tests pin each class, method and named argument the book depends on, so they fail loudly the day a release changes one.

Model identifiers appearing in examples — `claude-sonnet-4-5`, `gpt-4.1-mini`, `gemini-2.0-flash`, `mistral-large-latest` — were current when written and will not stay that way. Check your provider's model list rather than trusting any book, including this one.

Before relying on a version claim anywhere in these pages:

```bash
composer show neuron-core/neuron-ai
```

## Production

Written in Markdown. Built with pandoc into EPUB3 and a 6×9 inch DOCX, converted to PDF with LibreOffice. The EPUB is validated with epubcheck; the PDF page size is checked to be exactly 432 × 648 points.

The build tooling is a small set of shell scripts and Python helpers: `bookcfg.py` parses the book configuration, `make-metadata.py` produces the per-edition pandoc metadata, and `fix-pdf-trim.py` snaps the PDF to the exact trim size. Nothing in the pipeline calls an external service.

Diagrams are ASCII inside fenced code blocks — deliberately, so they survive reflow at any font size on any reader, which no raster image does.

## Editions

Published in English, Italian and Spanish. The Italian and Spanish editions are translations of the English text, governed by a shared glossary that pins product, package, class and command names as invariant.

The two translations diverge deliberately on one point. Italian absorbs English technical vocabulary wholesale — *il tool*, *il workflow*, *l'embedding* — which is how the profession writes in Italy. Spanish translates it: *herramienta*, *flujo de trabajo*, *incrustación*, *transmisión*, *proveedor*, *fragmento*. Only `prompt`, `token` and `middleware` survive in English there, none of them having a settled Spanish equivalent.

Code is identical across all three editions. Comments, string literals and identifiers are never translated.

## Corrections

Software moves. If you find something in this book that no longer matches the library, Appendix A explains how to determine what is actually true on your installation — which is the answer this book would give you anyway.

## About the author

Hidran Arias builds and teaches PHP systems. This book grew out of a twenty-three-module course on the same material, and out of the conviction that the agentic-AI conversation has been conducted almost entirely in Python for reasons that have nothing to do with where the work actually is.

---

*Agentic AI in PHP with NeuronAI*
First edition, 2026
