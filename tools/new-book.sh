#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SLUG="${1:?usage: new-book.sh <slug> [--title T] [--author A]}"; shift || true
TITLE="$SLUG"; AUTHOR="Author"
while [[ $# -gt 0 ]]; do case "$1" in
  --title) TITLE="$2"; shift 2;; --author) AUTHOR="$2"; shift 2;;
  *) echo "unknown arg: $1" >&2; exit 2;; esac; done

DEST="$ROOT/books/$SLUG"
[[ -e "$DEST" ]] && { echo "ERROR: $DEST exists" >&2; exit 1; }
mkdir -p "$DEST/sources/images" "$DEST/manuscript/00-front-matter" \
         "$DEST/manuscript/parte-1" "$DEST/editions" "$DEST/figures"

# Escape sed replacement metacharacters (\, /, &) so titles/authors with
# slashes or ampersands substitute literally.
sed_escape() { printf '%s' "$1" | sed -e 's/[\/&]/\\&/g'; }
SLUG_E=$(sed_escape "$SLUG"); TITLE_E=$(sed_escape "$TITLE"); AUTHOR_E=$(sed_escape "$AUTHOR")

sed -e "s/__SLUG__/$SLUG_E/g" -e "s/__TITLE__/$TITLE_E/g" -e "s/__AUTHOR__/$AUTHOR_E/g" \
    "$ROOT/tools/templates/book.yaml" > "$DEST/book.yaml"
sed -e "s/__SLUG__/$SLUG_E/g" "$ROOT/tools/templates/glossary.md" > "$DEST/glossary.md"
echo "✓ created $DEST"
echo "  next: drop material into books/$SLUG/sources/ then ask Claude to 'produce a book from books/$SLUG'"
