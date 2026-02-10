# 🏭 Lady Nuggets Enterprise

Automatic anime image generation pipeline using Stable Diffusion on RunPod.

## 🚀 Quick Start (RunPod)

### 1. Create Pod
- **Template:** `Stable Diffusion WebUI Forge` (`runpod/forge:3.3.0`)
- **GPU:** RTX 4090 × 1
- **Container Disk:** 50 GB
- **Volume Disk:** 50-75 GB (optional, for persistence)

### 2. First-Time Setup
```bash
cd /workspace
git clone https://github.com/ale-aguirre/lady-nuggets-enterprise.git
cd lady-nuggets-enterprise

# Create config with your API keys
cat > config/.env << 'EOF'
GROQ_KEY=your_groq_key_here
OPENROUTER_KEY=your_openrouter_key_here
CIVITAI_TOKEN=your_civitai_token_here
REFORGE_API=http://127.0.0.1:7860
EOF
```

### 3. Get Free API Keys

| Service | URL | Purpose |
|---------|-----|---------|
| **Groq** | https://console.groq.com/keys | LLM prompt generation (free) |
| **OpenRouter** | https://openrouter.ai/keys | LLM fallback (free tier) |
| **CivitAI** | https://civitai.com/user/account | Model downloads |

### 4. Generate Images
```bash
./scripts/runpod_ultra.sh --count 10
```

## 📋 Usage Options

```bash
# Generate 5 images (default)
./scripts/runpod_ultra.sh --count 5

# Use specific theme
./scripts/runpod_ultra.sh --count 5 --theme "Beach Day"

# Enable character LoRA
./scripts/runpod_ultra.sh --count 5 --lora

# Use random anime characters (not just Lady Nuggets OC)
./scripts/runpod_ultra.sh --count 5 --random-char

# Skip model download (use existing)
./scripts/runpod_ultra.sh --count 5 --no-model

# Disable Hires Fix (faster but lower quality)
./scripts/runpod_ultra.sh --count 5 --no-hires
```

## 🎨 Models

| Model | Style | Auto-Download |
|-------|-------|:---:|
| **WAI-Illustrious v16** (primary) | Anime | ✅ |
| OneObsession v19 (secondary) | 2.5D / Color | ✅ |

## 📁 Project Structure

```
config/
  .env              # API keys (gitignored - create manually)
  themes.txt        # Scene themes for generation
  loras.txt         # LoRA download URLs
scripts/
  factory.py        # Core generation engine
  runpod_ultra.sh   # RunPod automation script
content/            # Generated images output
```

## ⚠️ Important Notes

- `.env` is **gitignored** — you must create it manually on each new pod
- Models auto-download on first run (~7GB each, needs CIVITAI_TOKEN)
- Use `--medvram-sdxl` flag if running on 24GB GPUs (auto-configured)
