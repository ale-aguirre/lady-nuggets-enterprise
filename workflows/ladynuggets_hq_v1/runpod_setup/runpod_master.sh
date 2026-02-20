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
  inject_token_if_present
  bash "${ROOT_DIR}/download_models.sh" "${ENV_FILE}"
}

cmd_verify() {
  bash "${ROOT_DIR}/verify_models.sh"
}

main() {
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
