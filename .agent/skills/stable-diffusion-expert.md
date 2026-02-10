---
description: Expert guide for Stable Diffusion with Forge/Reforge on RunPod - model selection, parameters, and quality optimization
---

# Skill: Stable Diffusion Expert (Forge + RunPod)

## RunPod Configuration

### Recommended Pod Setup
| Setting | Value | Why |
|---------|-------|-----|
| Template | `runpod/forge:3.3.0` | Forge is 30-45% faster than A1111 |
| GPU | RTX 4090 × 1 | Best quality/price, 24GB VRAM |
| Container Disk | **50 GB** | Models = 6-7GB each + extensions |
| Volume Disk | 50-75 GB | Persistence between restarts |
| GPU Count | **1** | SD does NOT benefit from multi-GPU |

### Launch Flags
```bash
python3 launch.py --nowebui --api --listen --port 7860 --xformers --medvram-sdxl
```

| Flag | Purpose |
|------|---------|
| `--nowebui` | API-only mode (no browser UI) |
| `--api` | Enable REST API |
| `--xformers` | Memory-efficient attention |
| `--medvram-sdxl` | **CRITICAL** for 24GB GPUs — prevents OOM |
| `--listen` | Accept external connections |

### Without `--medvram-sdxl`, 24GB GPUs will OOM during Hires Fix:
```
832×1216 base = ~12GB VRAM
+ Hires 1.5x (1248×1824) = ~18GB VRAM peak
+ ADetailer inpainting = ~20GB VRAM peak
Total: needs --medvram-sdxl to fit in 24GB
```

## Model Selection Guide

### Current Best Models (2025-2026)

| Model | Style | Quality | Prompt Difficulty | Hires Denoise |
|-------|-------|---------|-------------------|---------------|
| **WAI-Illustrious v16** | Pure anime | ⭐⭐⭐⭐⭐ | Easy (works out of box) | **0.35-0.50** |
| OneObsession v19 | 2.5D / color | ⭐⭐⭐⭐ | Medium | **0.65-0.70** |
| NoobAI-XL | Precise anime | ⭐⭐⭐⭐ | Hard (needs specific tags) | 0.40-0.50 |

### Model-Specific Differences
- **WAI**: Built-in VAE, lower denoise needed, simpler prompts work
- **OneObsession**: More artistic color palette, higher denoise for detail
- **NoobAI**: Strict Danbooru tag adherence, needs more LoRAs

## Optimal Generation Parameters

### Core Settings (proven for all Illustrious-family models)
```
Steps: 20               # More steps ≠ better quality above 20
CFG Scale: 5             # Sweet spot. Never go above 7 (overcooking)
Sampler: Euler a         # Best for Illustrious family
Scheduler: Karras        # Smoother noise distribution
CLIP Skip: 2             # Standard for anime checkpoints
Base Resolution: 832×1216  # Portrait. Use 1216×832 for landscape
```

### Hires Fix Settings
```
Upscaler: R-ESRGAN 4x+ Anime6B    # Best for anime
Scale: 1.5x                        # Final: 1248×1824
Hires Steps: 15-20                 
Hires CFG: 5                       # Match base CFG
Denoise: 0.35-0.50 (WAI) / 0.65-0.70 (OneObsession)
```

### Why Denoise Differs by Model
- **Low denoise (0.35-0.50)**: Preserves anatomy from 1st pass, adds texture/detail
- **High denoise (0.65-0.70)**: Redraws more aggressively, better for fixing issues but can introduce new ones
- WAI already has clean anatomy → low denoise = safe
- OneObsession benefits from aggressive redraw → high denoise = more artistic

## Prompt Engineering

### Structure (BREAK sections for SDXL)
```
Section 1: Artists + Quality tags
BREAK
Section 2: Character description + Scene
BREAK
Section 3: Quality suffix + LoRA tags
```

### Quality Tags (from official WAI recommendations)
```
# Positive (keep minimal — too many hurts quality!)
masterpiece, best quality, amazing quality

# Negative (keep focused)
bad quality, worst quality, worst detail, sketch, censor
```

### Artist Mixing (enhances style variety)
```
(yoneyama mai:1.16), (ciloranko:1.05), (rella:1.1)
(mika pikazo:0.8), (wlop:0.5), (fuzichoco:0.86)
```
- Use 2-4 artists per image
- Weight range: 0.5-1.2
- Mix diverse styles for unique results

### DO NOT
- Add excessive quality tags (actually reduces quality on WAI)
- Use CFG > 7 ("overcooks" the image)
- Use very long negative prompts (counterproductive on Illustrious models)
- Set denoise > 0.5 on WAI (destroys anatomy)

## CivitAI Download API

### URL Format
```
https://civitai.com/api/download/models/{modelId}?type=Model&format=SafeTensor&size=pruned&fp=fp16&token={TOKEN}
```

### Known Model IDs
| Model | CivitAI Model ID |
|-------|-----------------|
| WAI-Illustrious-SDXL | 827184 |
| OneObsession v19 | Download version ID: 2443982 |

### Common Download Issues
- 26 bytes response = invalid/expired token
- 513 bytes response = redirect page (need `-L` flag in curl)
- Always verify file size > 1GB for checkpoints, > 1MB for LoRAs

## Extensions

### ADetailer (After Detailer)
- Fixes hands, faces, and eyes automatically
- Install: git clone into `$SD_DIR/extensions/adetailer/`
- Requires: `pip install ultralytics`
- **Server must restart after installation**

### Forge-Specific Features
- Built-in VRAM optimization (no separate --opt-split-attention needed)
- Style Selector extension (when using WebUI mode)
- Better model switching without OOM
