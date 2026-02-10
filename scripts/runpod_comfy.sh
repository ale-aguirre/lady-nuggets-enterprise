#!/bin/bash

# ============================================
# RUNPOD COMFYUI SETUP - FANVUE PRODUCTION
# Script de instalación automática
# ============================================

set -e  # Exit on error

echo "🚀 Iniciando setup de ComfyUI para producción Fanvue..."
echo "=================================================="

# Directorio base
COMFYUI_DIR="/workspace/ComfyUI"
cd $COMFYUI_DIR

# ============================================
# 1. CUSTOM NODES
# ============================================
echo ""
echo "📦 Instalando Custom Nodes..."

cd custom_nodes

# InstantID (para consistencia facial)
if [ ! -d "ComfyUI_InstantID" ]; then
    echo "  → Instalando InstantID..."
    git clone https://github.com/cubiq/ComfyUI_InstantID.git
    cd ComfyUI_InstantID
    pip install -r requirements.txt -q
    cd ..
else
    echo "  ✓ InstantID ya instalado"
fi

# Impact Pack (para FaceDetailer)
if [ ! -d "ComfyUI-Impact-Pack" ]; then
    echo "  → Instalando Impact Pack..."
    git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
    cd ComfyUI-Impact-Pack
    pip install -r requirements.txt -q
    cd ..
else
    echo "  ✓ Impact Pack ya instalado"
fi

# Reactor (face swap rápido - backup)
if [ ! -d "comfyui-reactor-node" ]; then
    echo "  → Instalando Reactor Node..."
    git clone https://github.com/Gourieff/comfyui-reactor-node.git
    cd comfyui-reactor-node
    pip install -r requirements.txt -q
    cd ..
else
    echo "  ✓ Reactor Node ya instalado"
fi

cd $COMFYUI_DIR

# ============================================
# 2. CHECKPOINT PRINCIPAL
# ============================================
echo ""
echo "🎨 Descargando epiCRealism XL checkpoint..."

CHECKPOINT_DIR="$COMFYUI_DIR/models/checkpoints"
mkdir -p $CHECKPOINT_DIR

# epiCRealism XL - LastFAME
if [ ! -f "$CHECKPOINT_DIR/epicrealismXL_v16LastFAME.safetensors" ]; then
    echo "  → Descargando epiCRealism XL (~6.5GB)..."
    wget -O "$CHECKPOINT_DIR/epicrealismXL_v16LastFAME.safetensors" \
        "https://civitai.com/api/download/models/1221069?type=Model&format=SafeTensor&size=pruned&fp=fp16" \
        --progress=bar:force:noscroll
    echo "  ✓ epiCRealism XL descargado"
else
    echo "  ✓ epiCRealism XL ya existe"
fi

# ============================================
# 3. INSTANTID MODELS
# ============================================
echo ""
echo "👤 Descargando modelos InstantID..."

# IP-Adapter
INSTANTID_DIR="$COMFYUI_DIR/models/instantid"
mkdir -p $INSTANTID_DIR

if [ ! -f "$INSTANTID_DIR/ip-adapter.bin" ]; then
    echo "  → Descargando ip-adapter.bin..."
    wget -O "$INSTANTID_DIR/ip-adapter.bin" \
        "https://huggingface.co/InstantX/InstantID/resolve/main/ip-adapter.bin" \
        --progress=bar:force:noscroll
    echo "  ✓ ip-adapter.bin descargado"
else
    echo "  ✓ ip-adapter.bin ya existe"
fi

# ControlNet
CONTROLNET_DIR="$COMFYUI_DIR/models/controlnet"
mkdir -p $CONTROLNET_DIR

if [ ! -f "$CONTROLNET_DIR/diffusion_pytorch_model.safetensors" ]; then
    echo "  → Descargando ControlNet InstantID..."
    wget -O "$CONTROLNET_DIR/diffusion_pytorch_model.safetensors" \
        "https://huggingface.co/InstantX/InstantID/resolve/main/ControlNetModel/diffusion_pytorch_model.safetensors" \
        --progress=bar:force:noscroll
    echo "  ✓ ControlNet descargado"
else
    echo "  ✓ ControlNet ya existe"
fi

# InsightFace (Antelopev2)
INSIGHTFACE_DIR="$COMFYUI_DIR/models/insightface/models/antelopev2"
mkdir -p $INSIGHTFACE_DIR

if [ ! -f "$INSIGHTFACE_DIR/1k3d68.onnx" ]; then
    echo "  → Descargando InsightFace Antelopev2..."
    cd /tmp
    wget "https://huggingface.co/MonsterMMORPG/tools/resolve/main/antelopev2.zip" \
        --progress=bar:force:noscroll
    unzip -q antelopev2.zip -d antelopev2
    mv antelopev2/* $INSIGHTFACE_DIR/
    rm -rf antelopev2 antelopev2.zip
    echo "  ✓ InsightFace descargado"
else
    echo "  ✓ InsightFace ya existe"
fi

# ============================================
# 4. UPSCALER
# ============================================
echo ""
echo "⬆️  Descargando Upscaler..."

UPSCALE_DIR="$COMFYUI_DIR/models/upscale_models"
mkdir -p $UPSCALE_DIR

if [ ! -f "$UPSCALE_DIR/4x_foolhardy_Remacri.pth" ]; then
    echo "  → Descargando 4x_foolhardy_Remacri..."
    wget -O "$UPSCALE_DIR/4x_foolhardy_Remacri.pth" \
        "https://huggingface.co/FacehugmanIII/4x_foolhardy_Remacri/resolve/main/4x_foolhardy_Remacri.pth" \
        --progress=bar:force:noscroll
    echo "  ✓ Upscaler descargado"
else
    echo "  ✓ Upscaler ya existe"
fi

# ============================================
# 5. VAE (opcional pero recomendado)
# ============================================
echo ""
echo "🎭 Descargando VAE..."

VAE_DIR="$COMFYUI_DIR/models/vae"
mkdir -p $VAE_DIR

if [ ! -f "$VAE_DIR/sdxl_vae.safetensors" ]; then
    echo "  → Descargando SDXL VAE..."
    wget -O "$VAE_DIR/sdxl_vae.safetensors" \
        "https://huggingface.co/stabilityai/sdxl-vae/resolve/main/sdxl_vae.safetensors" \
        --progress=bar:force:noscroll
    echo "  ✓ VAE descargado"
else
    echo "  ✓ VAE ya existe"
fi

# ============================================
# 6. WORKFLOW JSON
# ============================================
echo ""
echo "📄 Descargando workflow optimizado..."

WORKFLOW_DIR="$COMFYUI_DIR/user/default/workflows"
mkdir -p $WORKFLOW_DIR

if [ ! -f "$WORKFLOW_DIR/fanvue_production.json" ]; then
    echo "  → Descargando workflow Fanvue..."
    wget -O "$WORKFLOW_DIR/fanvue_production.json" \
        "https://civitai.com/api/download/models/848926?type=Workflow" \
        --progress=bar:force:noscroll 2>/dev/null || echo "  ⚠️  Descarga manual del workflow desde CivitAI"
else
    echo "  ✓ Workflow ya existe"
fi

# ============================================
# RESUMEN FINAL
# ============================================
echo ""
echo "=================================================="
echo "✅ SETUP COMPLETADO"
echo "=================================================="
echo ""
echo "📊 Modelos instalados:"
echo "  • epiCRealism XL checkpoint"
echo "  • InstantID (ip-adapter + controlnet)"
echo "  • InsightFace Antelopev2"
echo "  • 4x Upscaler"
echo "  • SDXL VAE"
echo ""
echo "🔧 Custom Nodes:"
echo "  • ComfyUI_InstantID"
echo "  • Impact Pack (FaceDetailer)"
echo "  • Reactor Node"
echo ""
echo "🎯 SIGUIENTE PASO:"
echo "  1. Reinicia ComfyUI (Ctrl+C en terminal y vuelve a iniciar)"
echo "  2. Abre ComfyUI en el navegador"
echo "  3. Load Workflow → fanvue_production.json"
echo "  4. ¡Empieza a generar!"
echo ""
echo "💾 Espacio usado aproximado: ~12GB"
echo "=================================================="
echo ""
echo "🚀 ¡Listo para producción!"
