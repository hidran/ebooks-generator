#!/usr/bin/env bash
# Normalize sources/* into .work/ (text/markdown) + figures. Local-only.
set -euo pipefail
PANDOC="/opt/homebrew/bin/pandoc"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/tools"

BOOK=""
while [[ $# -gt 0 ]]; do case "$1" in
  --book) BOOK="$2"; shift 2;; *) echo "unknown arg: $1" >&2; exit 2;; esac; done
[[ -z "$BOOK" ]] && { echo "ERROR: --book required" >&2; exit 2; }
if [[ -d "$BOOK" ]]; then BOOKDIR="$(cd "$BOOK" && pwd)"; else BOOKDIR="$ROOT/books/$BOOK"; fi
CFG="$BOOKDIR/book.yaml"
if [[ -f "$CFG" ]]; then eval "$(python3 "$TOOLS/lib/bookcfg.py" "$CFG" shellvars)"; fi
SRC="$BOOKDIR/sources"
NORM="$BOOKDIR/.work/normalized"
TRANS="$BOOKDIR/.work/transcripts"
mkdir -p "$NORM" "$TRANS" "$BOOKDIR/figures"
[[ -d "$SRC" ]] || { echo "no sources/ in $BOOKDIR (nothing to import)"; exit 0; }

shopt -s nullglob nocaseglob
for f in "$SRC"/*; do
  [[ -d "$f" ]] && continue
  name="$(basename "${f%.*}")"; ext="${f##*.}"; ext="$(echo "$ext" | tr 'A-Z' 'a-z')"
  case "$ext" in
    pdf)            pdftotext -layout "$f" "$NORM/$name.txt"; echo "pdf → $name.txt";;
    docx|html|htm|epub|odt) "$PANDOC" "$f" -t gfm -o "$NORM/$name.md"; echo "$ext → $name.md";;
    md|markdown)    cp "$f" "$NORM/$name.md"; echo "md → $name.md";;
    txt|vtt|srt)    cp "$f" "$NORM/$name.$ext"; echo "$ext → passthrough";;
    mp4|mov|mkv|m4v|mp3|wav|m4a|aac)
        "$TOOLS/transcribe-video.sh" "$f" "$TRANS" --model "${TRANS_MODEL:-large-v3}" --language "${TRANS_LANG:-auto}"
        ;;
    *)              echo "skip (unknown): $(basename "$f")";;
  esac
done
# images
if [[ -d "$SRC/images" ]]; then cp -R "$SRC/images/." "$BOOKDIR/figures/"; echo "images → figures/"; fi
echo "✓ import done → $NORM"
