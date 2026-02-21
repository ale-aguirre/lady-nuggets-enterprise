#!/usr/bin/env bash
set -euo pipefail

SRC_ROOT="/workspace/ComfyUI/models"
SRC_CKPT="${SRC_ROOT}/checkpoints/hassakuXLIllustrious_v34.safetensors"
SRC_VAE="${SRC_ROOT}/vae/sdxl_vaeFix.safetensors"
SRC_UPS="${SRC_ROOT}/upscale_models/RealESRGAN_x4plus_anime_6B.pth"

[[ -f "$SRC_CKPT" ]] || { echo "Falta checkpoint fuente: $SRC_CKPT"; exit 1; }
[[ -f "$SRC_VAE"  ]] || { echo "Falta VAE fuente: $SRC_VAE"; exit 1; }
[[ -f "$SRC_UPS"  ]] || { echo "Falta upscaler fuente: $SRC_UPS"; exit 1; }

mapfile -t CKPT_DIRS < <(
  {
    find /workspace -type d -path '*/models/checkpoints' 2>/dev/null || true
    # fallback por si el template usa esta ruta y todavia no existe
    echo "/workspace/ComfyUI/models/checkpoints"
  } | awk 'NF' | sort -u
)

if [[ "${#CKPT_DIRS[@]}" -eq 0 ]]; then
  echo "No encontré dirs de checkpoints."
  exit 1
fi

for CKPT_DIR in "${CKPT_DIRS[@]}"; do
  MODELS_ROOT="$(cd "${CKPT_DIR}/.." 2>/dev/null || true; pwd)"
  [[ -n "${MODELS_ROOT:-}" ]] || continue
  VAE_DIR="${MODELS_ROOT}/vae"
  UPS_DIR="${MODELS_ROOT}/upscale_models"
  mkdir -p "$CKPT_DIR" "$VAE_DIR" "$UPS_DIR"

  cp -f "$SRC_CKPT" "${CKPT_DIR}/hassakuXLIllustrious_v34.safetensors"
  cp -f "$SRC_VAE"  "${VAE_DIR}/sdxl_vaeFix.safetensors"
  cp -f "$SRC_UPS"  "${UPS_DIR}/RealESRGAN_x4plus_anime_6B.pth"

  echo "SYNC target:"
  echo "  CKPT -> ${CKPT_DIR}"
  echo "  VAE  -> ${VAE_DIR}"
  echo "  UPS  -> ${UPS_DIR}"
done

echo "OK sync (${#CKPT_DIRS[@]} targets)"
