#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Apt packages"
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y aria2 jq curl git

echo "[2/4] Comfy paths"
COMFY_ROOT="/workspace/ComfyUI"
mkdir -p "$COMFY_ROOT/models/checkpoints"
mkdir -p "$COMFY_ROOT/models/vae"
mkdir -p "$COMFY_ROOT/models/upscale_models"
mkdir -p "$COMFY_ROOT/models/embeddings"
mkdir -p "$COMFY_ROOT/models/loras"

echo "[3/4] Setup folder"
mkdir -p /workspace/runpod_setup
cp -f /workspace/lady-nuggets-enterprise/workflows/ladynuggets_hq_v1/runpod_setup/* /workspace/runpod_setup/ 2>/dev/null || true

echo "[4/4] Done"
echo "OK bootstrap"
