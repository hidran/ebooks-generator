# CLAUDE.md — Multi-Book Production Playbook

This file is read by Claude Code at the start of every session. It tells you how this repository works and what to do when asked to "produce a book from `books/<slug>`."

---

## 1. Project Overview

This is a local-only multi-book publishing pipeline. Each book lives under `books/<slug>/` and is fully self-contained: sources, manuscript, figures, translations, and build outputs. Shared tooling lives in `tools/` and `tests/`. Nothing calls an external API — transcription runs on-device via mlx_whisper, translation is done by Claude in-session.

The repository ships with **no books** — only the tooling. To start one: scaffold it with `tools/new-book.sh <slug>`, drop your raw inputs (documents, video, audio, images) into `books/<slug>/sources/`, then run the 8-step workflow in Section 4 to turn them into an EPUB/DOCX/PDF.

---

## 2. Repository Layout

```
ebooks/
├── CLAUDE.md                    # this playbook (read every session)
├── books/
│   └── <slug>/
│       ├── book.yaml            # book metadata and edition config
│       ├── sources/             # gitignored — raw inputs (video, PDF, DOCX, MD, images)
│       │   └── images/          # source images copied into figures/ on import
│       ├── glossary.md          # term consistency table for this book
│       ├── manuscript/          # primary-language chapters (Markdown)
│       │   ├── 00-front-matter/
│       │   ├── parte-1/ … parte-N/
│       │   └── zz-back-matter/
│       ├── editions/
│       │   └── <lang>/
│       │       └── manuscript/  # translated chapters (same structure)
│       ├── figures/             # screenshots and diagrams referenced in chapters
│       ├── .work/               # gitignored intermediates
│       │   ├── normalized/      # text/markdown derived from sources
│       │   └── transcripts/     # mlx_whisper output (.txt, .vtt, .srt, .json)
│       └── build/               # gitignored final outputs (EPUB, DOCX, PDF)
├── tools/
│   ├── new-book.sh              # scaffold a new books/<slug>/ folder (Task 12)
│   ├── import-sources.sh        # normalize sources → .work/; transcribe AV
│   ├── transcribe-video.sh      # standalone mlx_whisper wrapper
│   ├── extract-frames.sh        # pull frames at timestamps or scene changes
│   ├── build-book.sh            # build EPUB + paperback per edition
│   ├── fix-pdf-trim.py          # snap PDF pages to exact 6×9 (432×648 pt)
│   ├── lib/
│   │   ├── bookcfg.py           # parse book.yaml → shell vars
│   │   ├── make-metadata.py     # book.yaml + lang → pandoc metadata
│   │   ├── kindle.css           # EPUB stylesheet
│   │   └── paperback.docx       # 6×9 reference doc (KDP margins)
│   └── templates/               # book.yaml + glossary scaffold templates
├── tests/
│   ├── test_bookcfg.py
│   ├── test_make_metadata.py
│   ├── fixtures/
│   └── selftest.sh
└── docs/
    └── superpowers/             # specs, plans, task briefs
```

---

## 3. book.yaml Schema

Every book has a `book.yaml` at `books/<slug>/book.yaml`. Full schema:

```yaml
slug: my-book
title: "My Book Title"
subtitle: "An optional subtitle"
author: "Author Name"
date: "2026"
rights: "© 2026 Author Name. All rights reserved."
publisher: "Self-published"
keywords: [keyword one, keyword two, keyword three]
primary_language: en        # ISO 639-1
trim: "6x9"                 # only supported trim
formats: [epub, paperback]  # epub → EPUB3; paperback → DOCX+PDF
transcription:
  model: large-v3           # mlx_whisper model tag (strips "mlx-community/whisper-" prefix)
  language: en              # language hint for whisper; "auto" = detect
editions:
  - lang: en                # primary edition (no translate_from)
  - lang: es
    translate_from: en      # source edition lang to translate from
    style: "natural Spanish; keep English tech terms"
```

Key fields:
- `primary_language` — the language of `manuscript/`; must match one edition with no `translate_from`.
- `trim` — only `"6x9"` is supported; build validates exact 432×648 pt page size.
- `editions` — each entry with `translate_from` triggers an in-session translation into `editions/<lang>/manuscript/` during the workflow.
- `style` — freeform style instruction passed to you during translation.

---

## 4. Producing a Book — The 8-Step Workflow

When asked to "produce a book from `books/<slug>`", execute this workflow in order:

### Step 1 — Read book.yaml

Read `books/<slug>/book.yaml` to understand the book's slug, title, language, editions, transcription settings, and style notes. Keep this context active for every subsequent step.

### Step 2 — Import Sources

Run from the repo root:

```bash
bash tools/import-sources.sh --book <slug>
```

This normalizes every file in `sources/`:
- Video/audio (mp4, mov, mkv, mp3, wav, etc.) → mlx_whisper transcript in `.work/transcripts/` (txt + vtt + srt + json)
- PDF → `pdftotext -layout` → `.work/normalized/<name>.txt`
- DOCX, HTML, EPUB, ODT → `pandoc -t gfm` → `.work/normalized/<name>.md`
- MD, TXT, VTT, SRT → passthrough copy into `.work/normalized/` or `.work/transcripts/`
- `sources/images/*` → copied into `figures/`

Outputs land in `.work/` (gitignored). The script is idempotent: re-running it is safe.

### Step 3 — Validate and Clean Transcripts

Open each file in `.work/transcripts/` and `.work/normalized/`. Read them against the source context (course slides, chapter names, known terminology from `glossary.md`). Fix:
- Mis-heard technical terms (e.g., "Claude code" vs "cloud code")
- Garbled proper names, command names, brand names
- Run-on sentences where natural paragraph breaks exist

Do not paraphrase — preserve the speaker's voice. Save cleaned versions back in place (overwrite `.work/transcripts/<name>.txt`).

### Step 4 — Author the Manuscript

Create or extend files in `books/<slug>/manuscript/`:

```
manuscript/
  00-front-matter/
    00-title.md
    01-copyright.md
    02-dedica.md
    03-intro.md
  parte-1/
    cap-01.md
    cap-02.md
  parte-2/
    cap-03.md
    …
  parte-N/
    cap-XX.md
  zz-back-matter/
    appendix.md
    colophon.md
```

Chapter naming: `cap-XX.md` with two-digit zero-padded numbers. The build script discovers all `.md` files in alphabetical order, so naming determines chapter sequence.

Each chapter is plain Markdown. Use ATX headings (`#` for chapter title, `##` for sections, `###` for subsections). Reference figures with a **book-root-relative** path (see Figure Paths below):

```markdown
![Caption](figures/cap-XX/screenshot.png)
```

### Step 5 — Extract Frames

When a chapter needs a screenshot or diagram from a video source:

```bash
bash tools/extract-frames.sh sources/<video> books/<slug>/figures/cap-XX/ [<HH:MM:SS> …]
# or scene detection:
bash tools/extract-frames.sh sources/<video> books/<slug>/figures/cap-XX/ --scene [THRESH]
```

Place resulting `.png` files in `books/<slug>/figures/cap-XX/` and reference them in the chapter Markdown with the path shown in Step 4.

### Step 6 — Translate Each Edition

For every edition in `book.yaml` that has a `translate_from` key, translate the primary manuscript in-session:

- Source: `books/<slug>/manuscript/` (primary language)
- Target: `books/<slug>/editions/<lang>/manuscript/` (same folder structure)
- Glossary: `books/<slug>/glossary.md` — follow every term mapping exactly
- Style: use the `style` field from the edition's `book.yaml` entry

Translation rules (see Section 8 for full detail):
- Accuracy first; meaning and technical content must match exactly
- Preserve all Markdown formatting, code blocks, figure references, and paths
- Apply `glossary.md` term mappings consistently throughout
- Keep entrenched English tech terms (e.g., "prompt", "token", "deploy") in English unless the glossary maps them
- Use the edition's `style` for register/voice decisions
- Skip any source-language-only stylistic issues that have no target-language equivalent

### Step 7 — Build

Run from the repo root:

```bash
bash tools/build-book.sh --book <slug>
```

Optional flags:
- `--edition <lang>` — build only one edition (repeatable)
- `--formats epub,paperback` — restrict output formats
- `--no-validate` — skip epubcheck + trim check

Outputs land in `books/<slug>/build/` (gitignored).

### Step 8 — Report Results

After the build, read and report:
- epubcheck result: pass/warn/fail, with any error messages
- Trim validation: confirm exact 432×648 pt (6×9") page size
- List output files in `books/<slug>/build/`
- Flag any content gaps (empty chapters, missing figures, untranslated segments)

---

## 5. Commands Reference

All commands run from the **repo root** (`/Users/hidranarias/projects/ebooks`).

### `tools/new-book.sh` — Scaffold a new book (Task 12, not yet created)

```bash
bash tools/new-book.sh <slug> [--title "Title"] [--author "Name"]
```

Creates `books/<slug>/` with the standard folder structure and a starter `book.yaml`.

### `tools/import-sources.sh` — Normalize sources

```bash
bash tools/import-sources.sh --book <slug>
```

- `--book` (required) — slug or path to a book directory

### `tools/transcribe-video.sh` — Standalone transcription

```bash
bash tools/transcribe-video.sh <media> <outdir> [--model M] [--language L]
```

- `<media>` — path to video or audio file
- `<outdir>` — directory for transcript output (created if absent)
- `--model` — mlx_whisper model tag, default `large-v3`
- `--language` — language code or `auto`, default `auto`

### `tools/extract-frames.sh` — Video frame extraction

```bash
bash tools/extract-frames.sh <video> <outdir> [<HH:MM:SS> …]
bash tools/extract-frames.sh <video> <outdir> --scene [THRESH]
```

- Explicit timestamps: one frame per timestamp, named `frame_001.png`, `frame_002.png`, …
- `--scene [THRESH]`: scene-change detection, default threshold `0.4`, named `scene_001.png`, …

### `tools/build-book.sh` — Build editions

```bash
bash tools/build-book.sh --book <slug> [--edition <lang>] [--formats epub,paperback] [--no-validate]
```

- `--book` (required) — slug or path
- `--edition` — build a specific language edition; omit to build all editions in `book.yaml`
- `--formats` — comma-separated: `epub`, `paperback`, or both (default: both)
- `--no-validate` — skip epubcheck and trim validation

---

## 6. Conventions

### Chapter Numbering

```
parte-1/cap-01.md     # Part 1, Chapter 1
parte-1/cap-02.md     # Part 1, Chapter 2
parte-2/cap-03.md     # Part 2, Chapter 3
```

Chapters continue their numeric sequence across parts. The build script discovers `.md` files alphabetically, so `parte-1/` sorts before `parte-2/`, and `cap-01.md` before `cap-02.md`.

### Figure Paths

Figures live at `books/<slug>/figures/cap-XX/<name>.png`. Reference them from the chapter Markdown with a **book-root-relative** path (no `../`):

```markdown
![Alt text](figures/cap-03/terminal-output.png)
```

`build-book.sh` runs pandoc from the repo root with `--resource-path` including the book directory, so a bare `figures/cap-XX/<name>.png` resolves to `books/<slug>/figures/cap-XX/<name>.png` regardless of which `parte-N/cap-XX.md` the reference sits in. Do **not** use `../../figures/...` — pandoc cannot resolve it under this invocation and silently drops the image (and validation will not flag the missing figure).

### Trim and Page Size

- Trim: **6×9 inches** (432×648 pt)
- KDP margins: inside 0.875" / outside 0.5" / top 0.75" / bottom 0.75", mirror margins enabled
- The build script validates exact 432×648 pt; `--no-validate` skips this check

### Build Outputs

`books/<slug>/build/` (gitignored). The **primary** edition omits the language suffix; translation editions carry `-<lang>`:
- `<slug>.epub` / `<slug>-<lang>.epub` — EPUB3 for Kindle and ebook stores
- `<slug>.docx` / `<slug>-<lang>.docx` — KDP paperback upload file
- `<slug>.pdf` / `<slug>-<lang>.pdf` — PDF rendered from DOCX via LibreOffice

---

## 7. Toolchain

All tools are local. No network calls during the workflow.

| Tool | Path | Purpose |
|------|------|---------|
| pandoc | `/opt/homebrew/bin/pandoc` | Markdown → EPUB/DOCX; DOCX/HTML/EPUB → GFM |
| LibreOffice (soffice) | `/opt/homebrew/bin/soffice` | DOCX → PDF |
| epubcheck | `epubcheck` (PATH) | EPUB3 validation |
| pdftotext / pdfinfo | PATH (poppler) | PDF → text; PDF metadata |
| ffmpeg | `/opt/homebrew/bin/ffmpeg` | Frame extraction from video |
| mlx_whisper | `/opt/anaconda3/bin/mlx_whisper` | On-device audio/video transcription |
| python3 | PATH | `bookcfg.py`, `fix-pdf-trim.py`, tests |
| pypdf | pip | PDF inspection in `fix-pdf-trim.py` |
| pyyaml | pip | `book.yaml` parsing in `bookcfg.py` |

Python helpers (`tools/lib/bookcfg.py`) are called directly by the shell scripts; no manual invocation needed.

---

## 8. Translation Rules

Translation is performed in-session by Claude. There is no batch API pipeline.

1. **Accuracy first.** The translation must match the source's meaning, technical content, and terminology exactly. Fluency is secondary to accuracy.

2. **Use the book's glossary.** Apply every mapping in `books/<slug>/glossary.md` consistently throughout the entire manuscript. Inconsistent terminology is a hard error.

3. **Preserve code and markup unchanged.** Code blocks (fenced or indented), inline code, shell commands, file paths, URLs, and figure references must be copied verbatim. Never translate code.

4. **Keep entrenched English tech terms.** Terms like "prompt", "token", "pipeline", "deploy", "endpoint", "context window", and similar industry-standard English are kept in English unless `glossary.md` explicitly maps them to a target-language equivalent.

5. **Preserve Markdown formatting.** All ATX headings, bold/italic markers, lists, blockquotes, tables, and horizontal rules must be preserved with identical structure. Do not add or remove heading levels.

6. **Skip source-language-only stylistic issues.** If the source has an awkward construction that only exists in the source language (e.g., a grammatical workaround specific to Italian), adapt naturally to the target language rather than replicating the awkwardness.

7. **Apply the edition's style directive.** The `style` field in `book.yaml` (e.g., `"natural Spanish; keep English tech terms"`) governs register and voice decisions. Follow it throughout.

8. **Match meaning, not words.** Idiomatic expressions, humor, and analogies should be rendered in target-language equivalents that carry the same meaning, not literal word-for-word translations.
