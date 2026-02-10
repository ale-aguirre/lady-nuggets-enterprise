#!/bin/bash

# ============================================
# RUNPOD VIDEO SETUP - LTX VIDEO v2
# ============================================

set -e

COMFY_DIR="/workspace/ComfyUI"
echo "🚀 Iniciando instalación de LTX Video v2..."

# 1. Custom Nodes
echo "📦 Instalando Custom Nodes..."
cd $COMFY_DIR/custom_nodes

# ComfyUI-LTXVideo (Lightricks)
if [ ! -d "ComfyUI-LTXVideo" ]; then
    echo "  → Instalando ComfyUI-LTXVideo..."
    git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git
    cd ComfyUI-LTXVideo
    pip install -r requirements.txt
    cd ..
    echo "  ✓ ComfyUI-LTXVideo instalado"
else
    echo "  ✓ ComfyUI-LTXVideo ya existe"
fi

# 2. Modelos LTX
echo ""
echo "⬇️ Descargando Modelos LTX..."

# Checkpoints
CKPT_DIR="$COMFY_DIR/models/checkpoints"
mkdir -p $CKPT_DIR

if [ ! -f "$CKPT_DIR/ltx-2-19b-dev-fp8.safetensors" ]; then
    echo "  → Descargando Checkpoint (FP8) ~20GB..."
    wget -O "$CKPT_DIR/ltx-2-19b-dev-fp8.safetensors" \
        "https://huggingface.co/Lightricks/LTX-2/resolve/main/ltx-2-19b-dev-fp8.safetensors" \
        --progress=bar:force:noscroll
else
    echo "  ✓ Checkpoint ya existe"
fi

# Text Encoders
ENC_DIR="$COMFY_DIR/models/text_encoders"
mkdir -p $ENC_DIR

if [ ! -f "$ENC_DIR/gemma_3_12B_it_fp4_mixed.safetensors" ]; then
    echo "  → Descargando Gemma 3 Text Encoder..."
    wget -O "$ENC_DIR/gemma_3_12B_it_fp4_mixed.safetensors" \
        "https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors" \
        --progress=bar:force:noscroll
else
    echo "  ✓ Gemma 3 Encoder ya existe"
fi

# Latent Upscale Models
UPS_DIR="$COMFY_DIR/models/latent_upscale_models"
mkdir -p $UPS_DIR

if [ ! -f "$UPS_DIR/ltx-2-spatial-upscaler-x2-1.0.safetensors" ]; then
    echo "  → Descargando LTX Spatial Upscaler..."
    wget -O "$UPS_DIR/ltx-2-spatial-upscaler-x2-1.0.safetensors" \
        "https://huggingface.co/Lightricks/LTX-2/resolve/main/ltx-2-spatial-upscaler-x2-1.0.safetensors" \
        --progress=bar:force:noscroll
else
    echo "  ✓ LTX Upscaler ya existe"
fi

echo ""
echo "✅ Instalación LTX Completa. Reinicia ComfyUI."
