#!/usr/bin/env bash
# Build a book's editions from book.yaml. Local-only.
set -euo pipefail

PANDOC="/opt/homebrew/bin/pandoc"
SOFFICE="/opt/homebrew/bin/soffice"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/tools"

BOOK="" ; EDITIONS_SEL="" ; FORMATS_SEL="" ; VALIDATE=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --book) BOOK="$2"; shift 2;;
    --edition) EDITIONS_SEL="$EDITIONS_SEL $2"; shift 2;;
    --formats) FORMATS_SEL="${2//,/ }"; shift 2;;
    --no-validate) VALIDATE=0; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
[[ -z "$BOOK" ]] && { echo "ERROR: --book required" >&2; exit 2; }

# Resolve book dir: accept a path or a slug under books/
if [[ -d "$BOOK" ]]; then BOOKDIR="$(cd "$BOOK" && pwd)"; else BOOKDIR="$ROOT/books/$BOOK"; fi
CFG="$BOOKDIR/book.yaml"
[[ -f "$CFG" ]] || { echo "ERROR: $CFG not found" >&2; exit 1; }

eval "$(python3 "$TOOLS/lib/bookcfg.py" "$CFG" shellvars)"
[[ -n "$EDITIONS_SEL" ]] && EDITIONS="$EDITIONS_SEL"
[[ -n "$FORMATS_SEL"  ]] && FORMATS="$FORMATS_SEL"
mkdir -p "$BOOKDIR/build"

manuscript_dir() {  # $1 = lang
  if [[ "$1" == "$PRIMARY_LANG" ]]; then echo "$BOOKDIR/manuscript"
  else echo "$BOOKDIR/editions/$1/manuscript"; fi
}
out_name() {  # $1 = lang -> base name
  if [[ "$1" == "$PRIMARY_LANG" ]]; then echo "$SLUG"; else echo "$SLUG-$1"; fi
}

for lang in $EDITIONS; do
  MS="$(manuscript_dir "$lang")"
  [[ -d "$MS" ]] || { echo "skip $lang: no manuscript at $MS" >&2; continue; }
  BASE="$(out_name "$lang")"
  MD_FILES=$(find "$MS" -name '*.md' | sort)
  META="$BOOKDIR/build/.metadata-$lang.yaml"
  python3 "$TOOLS/lib/make-metadata.py" "$CFG" "$lang" > "$META"

  for fmt in $FORMATS; do
    case "$fmt" in
      epub)
        echo "→ EPUB ($lang)"
        "$PANDOC" --metadata-file="$META" --css="$TOOLS/lib/kindle.css" \
          --toc --toc-depth=2 --split-level=1 \
          --resource-path=".:$BOOKDIR:$MS:$BOOKDIR/figures" \
          -o "$BOOKDIR/build/$BASE.epub" $MD_FILES
        echo "  ✓ build/$BASE.epub"
        ;;
      paperback)
        echo "→ Paperback ($lang)"
        "$PANDOC" --metadata-file="$META" --toc --toc-depth=2 \
          --resource-path=".:$BOOKDIR:$MS:$BOOKDIR/figures" \
          --reference-doc="$TOOLS/lib/paperback.docx" \
          -o "$BOOKDIR/build/$BASE.docx" $MD_FILES
        "$SOFFICE" --headless --convert-to pdf --outdir "$BOOKDIR/build" \
          "$BOOKDIR/build/$BASE.docx" >/dev/null 2>&1
        python3 "$TOOLS/fix-pdf-trim.py" "$BOOKDIR/build/$BASE.pdf"
        echo "  ✓ build/$BASE.docx + build/$BASE.pdf"
        ;;
    esac
  done

  if [[ "$VALIDATE" -eq 1 ]]; then
    if [[ -f "$BOOKDIR/build/$BASE.epub" ]]; then
      echo "→ epubcheck ($lang)"
      epubcheck "$BOOKDIR/build/$BASE.epub" >/dev/null 2>"$BOOKDIR/build/.epubcheck-$lang.log" \
        && echo "  ✓ epub valid" \
        || { echo "  ✗ epub invalid — see build/.epubcheck-$lang.log"; exit 1; }
    fi
    if [[ -f "$BOOKDIR/build/$BASE.pdf" ]]; then
      SZ=$(pdfinfo "$BOOKDIR/build/$BASE.pdf" | awk '/Page size/{print $3"x"$5}')
      [[ "$SZ" == "432x648" ]] && echo "  ✓ pdf trim $SZ" \
        || { echo "  ✗ pdf trim $SZ != 432x648"; exit 1; }
    fi
  fi
done
echo "✓ build-book done"
