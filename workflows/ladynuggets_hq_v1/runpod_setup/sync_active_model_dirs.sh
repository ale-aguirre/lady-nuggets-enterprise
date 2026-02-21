#!/usr/bin/env bash
set -euo pipefail

SRC_ROOT="/workspace/ComfyUI/models"
SRC_CKPT="${SRC_ROOT}/checkpoints/hassakuXLIllustrious_v34.safetensors"
SRC_VAE="${SRC_ROOT}/vae/sdxl_vaeFix.safetensors"
SRC_UPS="${SRC_ROOT}/upscale_models/RealESRGAN_x4plus_anime_6B.pth"

[[ -f "$SRC_CKPT" ]] || { echo "Falta checkpoint fuente: $SRC_CKPT"; exit 1; }
[[ -f "$SRC_VAE"  ]] || { echo "Falta VAE fuente: $SRC_VAE"; exit 1; }
[[ -f "$SRC_UPS"  ]] || { echo "Falta upscaler fuente: $SRC_UPS"; exit 1; }

copy_safe() {
  local src="$1"
  local dst="$2"
  local src_real dst_real
  src_real="$(realpath "$src")"
  if [[ -e "$dst" ]]; then
    dst_real="$(realpath "$dst")"
    if [[ "$src_real" == "$dst_real" ]]; then
      echo "SKIP same file -> $dst"
      return 0
    fi
  fi
  cp -f "$src" "$dst"
}

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

  copy_safe "$SRC_CKPT" "${CKPT_DIR}/hassakuXLIllustrious_v34.safetensors"
  copy_safe "$SRC_VAE"  "${VAE_DIR}/sdxl_vaeFix.safetensors"
  copy_safe "$SRC_UPS"  "${UPS_DIR}/RealESRGAN_x4plus_anime_6B.pth"

  # Some Comfy templates expose a fixed checkpoint list (e.g. sd_xl_base_1.0.*).
  # Force allowed filename to point to Hassaku so API can load anime model without changing allow-list.
  if [[ -f "${CKPT_DIR}/hassakuXLIllustrious_v34.safetensors" ]]; then
    if [[ -e "${CKPT_DIR}/sd_xl_base_1.0.safetensors" && ! -L "${CKPT_DIR}/sd_xl_base_1.0.safetensors" ]]; then
      if [[ ! -e "${CKPT_DIR}/sd_xl_base_1.0.safetensors.orig_hqv1" ]]; then
        mv "${CKPT_DIR}/sd_xl_base_1.0.safetensors" "${CKPT_DIR}/sd_xl_base_1.0.safetensors.orig_hqv1"
      else
        rm -f "${CKPT_DIR}/sd_xl_base_1.0.safetensors"
      fi
    fi
    ln -sfn "hassakuXLIllustrious_v34.safetensors" "${CKPT_DIR}/sd_xl_base_1.0.safetensors"
    echo "ALIAS sd_xl_base_1.0.safetensors -> hassakuXLIllustrious_v34.safetensors"
  fi

  echo "SYNC target:"
  echo "  CKPT -> ${CKPT_DIR}"
  echo "  VAE  -> ${VAE_DIR}"
  echo "  UPS  -> ${UPS_DIR}"
done

echo "OK sync (${#CKPT_DIRS[@]} targets)"
