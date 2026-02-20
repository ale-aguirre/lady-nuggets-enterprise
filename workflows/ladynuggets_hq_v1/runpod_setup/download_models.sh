#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-runpod_setup/models.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ENV no encontrado: $ENV_FILE"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

COMFY_ROOT="/workspace/ComfyUI"

fetch() {
  local url="$1"
  local out="$2"
  if [[ -z "${url:-}" ]]; then
    echo "SKIP vacío -> $out"
    return 0
  fi

  mkdir -p "$(dirname "$out")"

  if [[ -f "$out" ]]; then
    echo "SKIP ya existe -> $out"
    return 0
  fi

  # Self-heal known broken URL from previous config.
  if [[ "$url" == "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus_anime_6B.pth" ]]; then
    echo "Fix URL rota de Anime6B -> usando v0.2.2.4"
    url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
  fi

  if [[ -n "${CIVITAI_TOKEN:-}" && "$url" == *"civitai.com"* ]]; then
    echo "Descargando (Civitai token query) -> $out"
    local final_url="$url"
    if [[ "$url" != *"token="* ]]; then
      if [[ "$url" == *"?"* ]]; then
        final_url="${url}&token=${CIVITAI_TOKEN}"
      else
        final_url="${url}?token=${CIVITAI_TOKEN}"
      fi
    fi
    aria2c --allow-overwrite=true -x 8 -s 8 -k 1M -o "$(basename "$out")" -d "$(dirname "$out")" "$final_url"
  else
    echo "Descargando -> $out"
    aria2c --allow-overwrite=true -x 8 -s 8 -k 1M -o "$(basename "$out")" -d "$(dirname "$out")" "$url"
  fi
}

fetch "${CKPT_URL:-}" "$COMFY_ROOT/models/checkpoints/${CKPT_NAME:-hassakuV3_4.safetensors}"
fetch "${VAE_URL:-}" "$COMFY_ROOT/models/vae/${VAE_NAME:-sdxl_vaeFix.safetensors}"
fetch "${UPSCALER_URL:-}" "$COMFY_ROOT/models/upscale_models/${UPSCALER_NAME:-R-ESRGAN 4x+ Anime6B.pth}"

fetch "${NEG_EMBED_URL_1:-}" "$COMFY_ROOT/models/embeddings/${NEG_EMBED_NAME_1:-negativeXL_D.safetensors}"
fetch "${LORA_URL_1:-}" "$COMFY_ROOT/models/loras/${LORA_NAME_1:-lora1.safetensors}"
fetch "${LORA_URL_2:-}" "$COMFY_ROOT/models/loras/${LORA_NAME_2:-lora2.safetensors}"

echo "OK downloads"
