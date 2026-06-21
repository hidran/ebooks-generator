#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIX="$ROOT/tests/fixtures/sample-book"
rm -rf "$FIX/build"
"$ROOT/tools/build-book.sh" --book "$FIX" --formats epub
test -f "$FIX/build/sample-book.epub"     || { echo "FAIL: no en epub"; exit 1; }
test -f "$FIX/build/sample-book-es.epub"  && echo "note: es epub built (no es manuscript yet — expected skip)" || true
echo "✓ selftest EPUB OK"
"$ROOT/tools/build-book.sh" --book "$FIX" --formats paperback
SIZE=$(pdfinfo "$FIX/build/sample-book.pdf" | awk '/Page size/{print $3"x"$5}')
test "$SIZE" = "432x648" || { echo "FAIL: trim $SIZE != 432x648"; exit 1; }
echo "✓ selftest paperback trim OK ($SIZE)"
mkdir -p "$FIX/sources"
printf 'Imported body text.' | "/opt/homebrew/bin/pandoc" -f markdown -o "$FIX/sources/note.docx" -
"$ROOT/tools/import-sources.sh" --book "$FIX"
test -f "$FIX/.work/normalized/note.md" || { echo "FAIL: docx not imported"; exit 1; }
echo "✓ selftest import OK"
