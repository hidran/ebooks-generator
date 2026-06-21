#!/usr/bin/env bash
# Transcribe audio/video locally with mlx_whisper. No network.
set -euo pipefail
MLX="$(command -v mlx_whisper || echo /opt/anaconda3/bin/mlx_whisper)"
[[ -x "$MLX" ]] || { echo "ERROR: mlx_whisper not found" >&2; exit 1; }

MEDIA="${1:?usage: transcribe-video.sh <media> <outdir> [--model M] [--language L]}"
OUTDIR="${2:?missing outdir}"; shift 2
MODEL="large-v3"; LANG="auto"
while [[ $# -gt 0 ]]; do case "$1" in
  --model) MODEL="$2"; shift 2;; --language) LANG="$2"; shift 2;;
  *) echo "unknown arg: $1" >&2; exit 2;; esac; done
mkdir -p "$OUTDIR"

ARGS=(--model "mlx-community/whisper-$MODEL" --output-dir "$OUTDIR"
      --output-format all)
[[ "$LANG" != "auto" ]] && ARGS+=(--language "$LANG")
echo "→ transcribing $(basename "$MEDIA") (model=$MODEL lang=$LANG)"
"$MLX" "$MEDIA" "${ARGS[@]}"
echo "✓ transcript → $OUTDIR"
