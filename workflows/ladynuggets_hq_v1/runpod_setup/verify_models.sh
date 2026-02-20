#!/usr/bin/env bash
set -euo pipefail
COMFY_ROOT="/workspace/ComfyUI"

echo "== checkpoints =="
ls -lh "$COMFY_ROOT/models/checkpoints" || true
echo "== vae =="
ls -lh "$COMFY_ROOT/models/vae" || true
echo "== upscalers =="
ls -lh "$COMFY_ROOT/models/upscale_models" || true
echo "== embeddings =="
ls -lh "$COMFY_ROOT/models/embeddings" || true
echo "== loras =="
ls -lh "$COMFY_ROOT/models/loras" || true

echo "OK verify"
