# 🏭 Lady Nuggets Enterprise — Agent Instructions

> **Read this FIRST before touching any code in this project.**

## Project Overview
Automated anime image generation pipeline using **Stable Diffusion** on **RunPod** cloud GPUs.

### Architecture
```
runpod_ultra.sh  →  factory.py  →  SD WebUI API (Forge/Reforge)
    (bash)           (python)        (localhost:3000 or :7860)
```

- `runpod_ultra.sh` = **Master orchestrator** (environment detection, downloads, server management)
- `factory.py` = **Generation engine** (prompt building, LLM integration, API calls)
- These two files are the **core of the project**. Treat them with extreme care.

## ⚠️ CRITICAL RULES — DO NOT BREAK

### 1. Bash Script (`runpod_ultra.sh`)
- **`set -e` is active on line 14** — ANY command returning non-zero will kill the entire script
- **ALWAYS append `|| true`** to commands that may fail (git clone, curl, pip install)
- **NEVER** remove `|| true` from existing commands
- **Test syntax** after edits: `bash -n scripts/runpod_ultra.sh`
- Port detection validates JSON (not just HTTP response) — do not simplify this

### 2. Python Script (`factory.py`)
- **Prompt structure uses BREAK sections** — do not flatten into single line
- **Model-specific params** (denoise varies by model) — check `is_wai` / `is_oneobs` flags
- **LoRA logic splits aesthetic/character** — aesthetic always apply, character only with `--lora`
- **Test syntax** after edits: `python3 -c "import py_compile; py_compile.compile('scripts/factory.py', doraise=True)"`

### 3. General
- `.env` is **gitignored** — never commit API keys
- All external downloads must have **size verification** (check bytes > threshold)
- Every new CLI flag must be added to **BOTH** `runpod_ultra.sh` and `factory.py`

## Environment Details

### RunPod Setup
| Setting | Value |
|---------|-------|
| Template | `Stable Diffusion WebUI Forge` (runpod/forge:3.3.0) |
| GPU | RTX 4090 × 1 |
| Container Disk | 50 GB minimum |
| Launch flags | `--nowebui --api --listen --xformers --medvram-sdxl` |

### Models (auto-downloaded)
| Model | Role | Denoise |
|-------|------|---------|
| WAI-Illustrious v16 | Primary (anime) | 0.45 |
| OneObsession v19 | Secondary (2.5D) | 0.7 |

### Generation Parameters
```
Steps: 20          | CFG: 5           | Sampler: Euler a
Scheduler: Karras  | CLIP Skip: 2     | Size: 832×1216
Hires: 1.5x        | Upscaler: R-ESRGAN 4x+ Anime6B
```

### API Keys Required
```bash
GROQ_KEY=...           # Free at console.groq.com/keys
OPENROUTER_KEY=...     # Free at openrouter.ai/keys  
CIVITAI_TOKEN=...      # From civitai.com/user/account
```

## CLI Flags
```bash
./scripts/runpod_ultra.sh \
  --count 10        \ # Number of images
  --random-char     \ # Random anime characters (vs Lady Nuggets OC)
  --lora            \ # Enable character LoRA
  --theme "Beach"   \ # Specific theme
  --no-hires        \ # Skip upscaling (faster)
  --no-model        \ # Skip model download
  --help            \ # Show help
```

## Before Modifying Code

1. **Read the relevant skill** in `.agent/skills/` first
2. Run syntax checks after every edit:
   ```bash
   bash -n scripts/runpod_ultra.sh
   python3 -c "import py_compile; py_compile.compile('scripts/factory.py', doraise=True)"
   ```
3. Test on RunPod with `--count 1 --no-hires` before committing large changes
4. **Never restructure prompt assembly** without understanding BREAK sections
5. **Never change `set -e` behavior** — add `|| true` to failing commands instead
