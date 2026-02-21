#!/usr/bin/env bash
set -euo pipefail

SRC_ROOT="/workspace/ComfyUI/models"

find_active_ckpt_dir() {
  local p=""
  for name in sd_xl_base_1.0.safetensors flux1-schnell-fp8.safetensors v1-5-pruned-emaonly.safetensors; do
    p="$(find /workspace -type f -name "$name" 2>/dev/null | head -n1 || true)"
    if [[ -n "$p" ]]; then
      dirname "$p"
      return 0
    fi
  done
  return 1
}

ACTIVE_CKPT_DIR="$(find_active_ckpt_dir || true)"
if [[ -z "${ACTIVE_CKPT_DIR:-}" ]]; then
  echo "No pude detectar directorio activo de checkpoints."
  exit 1
fi

ACTIVE_MODELS_ROOT="$(cd "${ACTIVE_CKPT_DIR}/.." && pwd)"
ACTIVE_VAE_DIR="${ACTIVE_MODELS_ROOT}/vae"
ACTIVE_UPS_DIR="${ACTIVE_MODELS_ROOT}/upscale_models"

mkdir -p "$ACTIVE_CKPT_DIR" "$ACTIVE_VAE_DIR" "$ACTIVE_UPS_DIR"

copy_if_exists() {
  local src="$1"
  local dst="$2"
  if [[ -f "$src" ]]; then
    cp -f "$src" "$dst"
    echo "SYNC $(basename "$src") -> $dst"
  fi
}

copy_if_exists "${SRC_ROOT}/checkpoints/hassakuXLIllustrious_v34.safetensors" "${ACTIVE_CKPT_DIR}/hassakuXLIllustrious_v34.safetensors"
copy_if_exists "${SRC_ROOT}/vae/sdxl_vaeFix.safetensors" "${ACTIVE_VAE_DIR}/sdxl_vaeFix.safetensors"
copy_if_exists "${SRC_ROOT}/upscale_models/RealESRGAN_x4plus_anime_6B.pth" "${ACTIVE_UPS_DIR}/RealESRGAN_x4plus_anime_6B.pth"

echo "ACTIVE_CKPT_DIR=${ACTIVE_CKPT_DIR}"
echo "ACTIVE_VAE_DIR=${ACTIVE_VAE_DIR}"
echo "ACTIVE_UPS_DIR=${ACTIVE_UPS_DIR}"
echo "OK sync"

