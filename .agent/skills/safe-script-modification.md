---
description: How to safely modify the Stable Diffusion generation scripts without breaking deployment
---

# Skill: Safe Script Modification for Lady Nuggets Enterprise

## Overview
This project has two master scripts that are **interdependent and fragile**. This skill teaches you how to modify them safely.

## Critical Files

| File | Language | Role |
|------|----------|------|
| `scripts/runpod_ultra.sh` | Bash | Environment setup, downloads, server management |
| `scripts/factory.py` | Python | Prompt engineering, LLM calls, SD API generation |

## Rule #1: `set -e` Protection (Bash)

`runpod_ultra.sh` uses `set -e` (line 14) which means **ANY command that returns non-zero will kill the entire script**.

### ❌ WRONG (will crash)
```bash
git clone https://example.com/repo.git /path/to/dir 2>/dev/null
curl -L -o file.zip "https://example.com/file.zip" 2>/dev/null
pip install somepackage 2>/dev/null
```

### ✅ CORRECT (safe)
```bash
git clone https://example.com/repo.git /path/to/dir 2>/dev/null || true
curl -L -o file.zip "https://example.com/file.zip" 2>/dev/null || true
pip install somepackage 2>/dev/null || true
```

**ALWAYS append `|| true`** to:
- `git clone` commands
- `curl` downloads that might fail
- `pip install` for optional packages
- Any `rm`, `mv`, `cp` that targets files that might not exist

## Rule #2: Download Verification

Every file downloaded via curl MUST be verified by size:

```bash
# Download
curl -L -o "$FILE_PATH" "$URL" 2>/dev/null || true

# Verify (minimum 1GB for models, 1MB for LoRAs)
FILE_SIZE=$(stat -c%s "$FILE_PATH" 2>/dev/null || stat -f%z "$FILE_PATH" 2>/dev/null || echo "0")
if [ "$FILE_SIZE" -gt 1000000000 ]; then
    echo "✅ Downloaded successfully"
else
    echo "⚠️ Download failed (${FILE_SIZE} bytes)"
    rm -f "$FILE_PATH" 2>/dev/null || true
fi
```

**Why:** CivitAI often returns tiny HTML error pages (26 bytes, 513 bytes) instead of the actual model file. Without size verification, the script would proceed with a corrupted/empty file.

## Rule #3: CLI Flag Sync

If you add a new CLI flag, it MUST be added in **THREE places**:

1. **`runpod_ultra.sh` argument parser** (inside `case $1 in ...`)
2. **`runpod_ultra.sh` help text** (inside `--help|-h)`)
3. **`factory.py` argparse** (inside `parser.add_argument(...)`)

Plus pass-through in bash:
```bash
# In the argument parser
--my-new-flag)
    FACTORY_EXTRA_ARGS="$FACTORY_EXTRA_ARGS --my-new-flag"
    shift
    ;;

# The factory.py call already uses $FACTORY_EXTRA_ARGS:
eval python3 scripts/factory.py --count "$IMAGE_COUNT" --output "$BATCH_DIR" $FACTORY_EXTRA_ARGS
```

## Rule #4: Prompt Structure (Python)

The prompt uses **BREAK sections** for semantic separation. Never flatten into a single line.

### Current Structure:
```
Section 1: artist_mix + QUALITY_PREFIX
BREAK
Section 2: character_tags + scene_prompt
BREAK  
Section 3: QUALITY_SUFFIX + lora_block
```

### When modifying prompts:
- Quality tags go in `QUALITY_PREFIX` or `QUALITY_SUFFIX`
- Artist names go in `ARTIST_MIXES`
- Character features go in `OC_CHARACTER` or `RANDOM_CHARACTERS`
- Scene descriptions come from the LLM via `get_ai_prompt()`
- **NEVER mix these categories**

## Rule #5: Model-Specific Parameters

Different models need different settings. The code auto-detects:

```python
is_wai = 'wai' in model_name.lower()      # WAI-Illustrious
is_oneobs = 'obsession' in model_name.lower()  # OneObsession

hr_denoise = 0.45 if is_wai else 0.7  # WAI = conservative, OO = aggressive
```

If adding a new model, add its detection and appropriate denoise value.

## Rule #6: Port Detection

The SD API detection validates actual JSON responses, not just HTTP 200:

```bash
# This catches nginx proxies returning HTML on port 8080
RESPONSE=$(curl -s --connect-timeout 2 "http://127.0.0.1:$port/sdapi/v1/sd-models")
if echo "$RESPONSE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    # Real SD API
fi
```

**NEVER simplify** port detection to just check HTTP status codes.

## Verification Checklist

Before committing ANY change to these scripts, run:

```bash
# 1. Bash syntax check
bash -n scripts/runpod_ultra.sh && echo "✅ Bash OK"

# 2. Python syntax check  
python3 -c "import py_compile; py_compile.compile('scripts/factory.py', doraise=True)" && echo "✅ Python OK"

# 3. Quick test on RunPod (1 image, no upscale)
./scripts/runpod_ultra.sh --count 1 --no-hires
```

## Common Mistakes to Avoid

| Mistake | Why it breaks | Fix |
|---------|---------------|-----|
| Missing `\|\| true` on git/curl | `set -e` kills script | Always append `\|\| true` |
| Wrong CivitAI URL | Returns HTML not model | Use version ID, verify size |
| Flattening prompt BREAK sections | Kills semantic separation | Keep 3-section structure |
| Adding CLI flag in one file only | Flag ignored or errors | Add in bash + python + help |
| Hardcoding port number | Doesn't work on Forge | Use dynamic port detection |
| Removing `2>/dev/null` | Messy output during install | Keep stderr suppressed |
