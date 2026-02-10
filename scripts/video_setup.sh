#!/bin/bash

# ============================================
# RUNPOD VIDEO SETUP - WAN 2.1 I2V
# ============================================

set -e

COMFY_DIR="/workspace/ComfyUI"
echo "🚀 Iniciando instalación de Wan 2.1 Video (I2V)..."

# 1. Custom Nodes
echo "📦 Instalando Custom Nodes..."
cd $COMFY_DIR/custom_nodes

# WanWrapper (Kijai)
if [ ! -d "ComfyUI-WanVideoWrapper" ]; then
    git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git
    cd ComfyUI-WanVideoWrapper
    pip install -r requirements.txt
    cd ..
    echo "  ✓ WanVideoWrapper instalado"
else
    echo "  ✓ WanVideoWrapper ya existe"
fi

# VideoHelperSuite (Load/Save Video)
if [ ! -d "ComfyUI-VideoHelperSuite" ]; then
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
    cd ComfyUI-VideoHelperSuite
    pip install -r requirements.txt
    cd ..
    echo "  ✓ VideoHelperSuite instalado"
else
    echo "  ✓ VideoHelperSuite ya existe"
fi

# 2. Modelos Wan 2.1
echo ""
echo "⬇️ Descargando Modelos Wan 2.1..."

# Checkpoints Directory for Diffusion Models
DIFF_DIR="$COMFY_DIR/models/diffusion_models"
mkdir -p $DIFF_DIR

# Wan 2.1 I2V 480P (Optimizado para empezar)
# Usamos HuggingFace mirror kigen/Wan2.1-SafeTensor
if [ ! -f "$DIFF_DIR/Wan2_1-I2V-14B-480P_fp8_e5m2.safetensors" ]; then
    echo "  → Descargando Modelo I2V 14B 480P (~12GB)..."
    wget -O "$DIFF_DIR/Wan2_1-I2V-14B-480P_fp8_e5m2.safetensors" \
        "https://huggingface.co/Kijai/WanVideo-2.1-SafeTensor/resolve/main/Wan2_1-I2V-14B-480P_fp8_e5m2.safetensors" \
        --progress=bar:force:noscroll
else
    echo "  ✓ Modelo I2V ya existe"
fi

# Text Encoder (T5)
ENC_DIR="$COMFY_DIR/models/text_encoders"
mkdir -p $ENC_DIR

if [ ! -f "$ENC_DIR/umt5_xxl_fp8_e4m3fn.safetensors" ]; then
    echo "  → Descargando T5 Encoder (~4GB)..."
    wget -O "$ENC_DIR/umt5_xxl_fp8_e4m3fn.safetensors" \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn.safetensors" \
        --progress=bar:force:noscroll
else
    echo "  ✓ T5 Encoder ya existe"
fi

# VAE
VAE_DIR="$COMFY_DIR/models/vae"
mkdir -p $VAE_DIR

if [ ! -f "$VAE_DIR/Wan2_1_VAE.safetensors" ]; then
    echo "  → Descargando VAE..."
    wget -O "$VAE_DIR/Wan2_1_VAE.safetensors" \
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/Wan2_1_VAE.safetensors" \
        --progress=bar:force:noscroll
else
    echo "  ✓ VAE ya existe"
fi

echo ""
echo "✅ Instalación Completa. Reinicia ComfyUI."
