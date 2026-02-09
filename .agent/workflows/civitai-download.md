---
description: How to download models from CivitAI via terminal (RunPod/Linux)
---

# Downloading from CivitAI via Terminal

CivitAI requires authentication for downloads. The API key must be passed as a **query parameter**, NOT as an Authorization header.

## Get Your API Key
1. Go to https://civitai.com/user/account
2. Scroll to "API Keys" section
3. Generate a new key

## Download Command (CORRECT)

```bash
# ✅ CORRECT - Token as query parameter
curl -L -o model.safetensors "https://civitai.com/api/download/models/MODEL_VERSION_ID?token=YOUR_API_KEY"
```

## Example: Download OneObsession v19

```bash
cd /workspace/stable-diffusion-webui/models/Stable-diffusion

curl -L -o oneObsession_v19Atypical.safetensors \
  "https://civitai.com/api/download/models/2443982?type=Model&format=SafeTensor&size=pruned&fp=fp16&token=YOUR_CIVITAI_API_KEY"
```

## Common Mistakes

```bash
# ❌ WRONG - Authorization header gets stripped on redirect
curl -L -H "Authorization: Bearer API_KEY" -o model.safetensors "URL"

# ❌ WRONG - wget doesn't follow redirects properly with headers  
wget --header="Authorization: Bearer API_KEY" -O model.safetensors "URL"
```

## Download LoRAs

```bash
cd /workspace/stable-diffusion-webui/models/Lora

# Example: Download a LoRA
curl -L -o MyLora.safetensors \
  "https://civitai.com/api/download/models/LORA_VERSION_ID?token=YOUR_API_KEY"
```

## Verify Download

```bash
# Should be several GB for checkpoints, MB for LoRAs
ls -lh model.safetensors

# If file is tiny (< 1KB), it contains an error message
cat model.safetensors
```
