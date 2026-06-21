#!/usr/bin/env bash
# Extract frames from a video: explicit timestamps or scene-change detection.
set -euo pipefail
FFMPEG="/opt/homebrew/bin/ffmpeg"
VIDEO="${1:?usage: extract-frames.sh <video> <outdir> [<ts...> | --scene [THRESH]]}"
OUTDIR="${2:?missing outdir}"; shift 2
[[ -f "$VIDEO" ]] || { echo "ERROR: video not found: $VIDEO" >&2; exit 1; }
mkdir -p "$OUTDIR"

if [[ "${1:-}" == "--scene" ]]; then
  THRESH="${2:-0.4}"
  echo "→ scene frames (threshold=$THRESH)"
  "$FFMPEG" -i "$VIDEO" -vf "select='gt(scene,$THRESH)',showinfo" \
    -vsync vfr -q:v 2 "$OUTDIR/scene_%03d.png" 2>/dev/null
  echo "✓ $(ls "$OUTDIR"/scene_*.png 2>/dev/null | wc -l | tr -d ' ') scene frames → $OUTDIR"
else
  idx=1
  for ts in "$@"; do
    out=$(printf "%s/frame_%03d.png" "$OUTDIR" "$idx")
    echo "→ $ts → $out"
    "$FFMPEG" -ss "$ts" -i "$VIDEO" -frames:v 1 -q:v 2 -y "$out" 2>/dev/null
    idx=$((idx + 1))
  done
  echo "✓ frames → $OUTDIR"
fi
