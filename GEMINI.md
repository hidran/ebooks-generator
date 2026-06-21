# GEMINI.md — Multi-Book Production Pipeline

This repository is a local-only, **generic** multi-book publishing pipeline:
drop raw inputs (documents, video, audio, images) into a book folder and the
tooling turns them into EPUB / DOCX / PDF. It ships with **tooling only — no
books**. Nothing calls an external API: transcription runs on-device via
mlx_whisper, and translation is done in-session by the model.

**The canonical playbook is [`CLAUDE.md`](./CLAUDE.md).** It documents the
repository layout, the `book.yaml` schema, the 8-step production workflow, every
`tools/` command, conventions (chapter numbering, figure paths, trim/page size),
the toolchain, and the translation rules. Follow it directly — everything in it
applies here regardless of which model is reading this file.

## Quick orientation
- `tools/` — pipeline scripts: `new-book.sh`, `import-sources.sh`,
  `transcribe-video.sh`, `extract-frames.sh`, `build-book.sh`, plus `lib/` helpers.
- `tests/` — pytest suite + `selftest.sh` for the tooling.
- `books/<slug>/` — created per book by `tools/new-book.sh`; fully self-contained
  (sources, manuscript, figures, editions, build outputs). Gitignored:
  `sources/`, `.work/`, `build/`.

## To start a book
```bash
bash tools/new-book.sh <slug>            # scaffold books/<slug>/
# drop raw inputs into books/<slug>/sources/
# then follow the 8-step workflow in CLAUDE.md (import → clean → author →
# figures → translate → build → report)
```
