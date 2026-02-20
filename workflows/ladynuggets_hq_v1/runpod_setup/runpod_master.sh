#!/usr/bin/env bash
set -euo pipefail

# Single entrypoint for pod setup.
# Usage:
#   bash runpod_master.sh init
#   CIVITAI_TOKEN=xxx bash runpod_master.sh models
#   CIVITAI_TOKEN=xxx bash runpod_master.sh all
#   bash runpod_master.sh verify

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_EXAMPLE="${ROOT_DIR}/models.env.example"
ENV_FILE="${ROOT_DIR}/models.env"

usage() {
  cat <<'EOF'
runpod_master.sh

Commands:
  init      Install deps + create Comfy model folders
  models    Create models.env (if missing), inject CIVITAI_TOKEN if provided, download models
  verify    Verify downloaded model files
  cleanup   Remove duplicate model files (*.1, *.2...) keeping canonical names
  all       init + models + verify

Optional env:
  CIVITAI_TOKEN=<token>   Inject token into models.env before download
EOF
}

ensure_env_file() {
  if [[ ! -f "${ENV_FILE}" ]]; then
    cp "${ENV_EXAMPLE}" "${ENV_FILE}"
  fi
}

sanitize_env_file() {
  # Fix legacy values from older setup iterations.
  sed -i 's|^UPSCALER_NAME=.*|UPSCALER_NAME=RealESRGAN_x4plus_anime_6B.pth|' "${ENV_FILE}" || true
  sed -i 's|^UPSCALER_URL=https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus_anime_6B.pth|UPSCALER_URL=https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth|' "${ENV_FILE}" || true
}

inject_token_if_present() {
  if [[ -n "${CIVITAI_TOKEN:-}" ]]; then
    python3 - <<'PY' "${ENV_FILE}" "${CIVITAI_TOKEN}"
from pathlib import Path
import sys
p = Path(sys.argv[1])
token = sys.argv[2]
lines = p.read_text().splitlines()
out = []
done = False
for ln in lines:
    if ln.startswith("CIVITAI_TOKEN="):
        out.append(f"CIVITAI_TOKEN={token}")
        done = True
    else:
        out.append(ln)
if not done:
    out.insert(0, f"CIVITAI_TOKEN={token}")
p.write_text("\n".join(out) + "\n")
PY
    chmod 600 "${ENV_FILE}" || true
  fi
}

cmd_init() {
  bash "${ROOT_DIR}/bootstrap_comfy_pod.sh"
}

cmd_models() {
  ensure_env_file
  sanitize_env_file
  inject_token_if_present
  bash "${ROOT_DIR}/download_models.sh" "${ENV_FILE}"
}

cmd_verify() {
  bash "${ROOT_DIR}/verify_models.sh"
}

cmd_cleanup() {
  local comfy_root="/workspace/ComfyUI/models"
  local dir
  for dir in checkpoints vae upscale_models embeddings loras; do
    local base="${comfy_root}/${dir}"
    [[ -d "${base}" ]] || continue
    shopt -s nullglob
    for dup in "${base}"/*.[0-9]*.safetensors "${base}"/*.[0-9]*.pth; do
      [[ -f "${dup}" ]] || continue
      local original
      original="$(echo "${dup}" | sed -E 's/\.([0-9]+)(\.[^.]+)$/\2/')"
      if [[ -f "${original}" ]]; then
        echo "REMOVE dup -> ${dup}"
        rm -f "${dup}"
      else
        echo "KEEP as canonical missing original -> ${dup}"
      fi
    done
    shopt -u nullglob
  done
  echo "OK cleanup"
}

main() {
  # Avoid concurrent runs that create duplicate files.
  exec 9>/tmp/runpod_master.lock
  flock -n 9 || {
    echo "Another runpod_master.sh process is running. Wait and retry."
    exit 1
  }

  local cmd="${1:-}"
  case "${cmd}" in
    init)
      cmd_init
      ;;
    models)
      cmd_models
      ;;
    verify)
      cmd_verify
      ;;
    cleanup)
      cmd_cleanup
      ;;
    all)
      cmd_init
      cmd_models
      cmd_verify
      ;;
    ""|-h|--help|help)
      usage
      ;;
    *)
      echo "Unknown command: ${cmd}"
      usage
      exit 1
      ;;
  esac
}

main "$@"
