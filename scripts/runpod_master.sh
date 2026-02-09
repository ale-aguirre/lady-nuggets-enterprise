#!/bin/bash
# scripts/runpod_master.sh
# ONE-CLICK INSTALL & GENERATE SCRIPT

echo "🚀 STARTER: Lady Nuggets Enterprise Protocol"
echo "============================================="

# 1. Environment Setup
echo "📦 [1/5] Installing Dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# 2. Adetailer (Face Fixer)
echo "💄 [2/5] Checking Adetailer..."
ADETAILER_PATH="/workspace/stable-diffusion-webui/extensions/adetailer"
if [ ! -d "$ADETAILER_PATH" ]; then
    git clone https://github.com/Bing-su/adetailer.git "$ADETAILER_PATH"
    echo "   -> Installed."
else
    echo "   -> Already exists."
fi

# 3. Model Download (OneObsession)
echo "⬇️  [3/5] Checking Model..."
MODEL_DIR="/workspace/stable-diffusion-webui/models/Stable-diffusion"
cd "$MODEL_DIR" || exit
if [ ! -f "oneObsession_v19Atypical.safetensors" ]; then
    echo "   -> Downloading OneObsession (2GB+)... This may take a minute."
    wget -q --show-progress https://civitai.com/api/download/models/302970 --content-disposition
else
    echo "   -> Model ready."
fi

# 4. Generate Images
cd /workspace/lady-nuggets-enterprise || exit
COUNT=${1:-6} # Default to 6 images if not specified
echo "🏭 [4/5] Generating $COUNT Images..."
python3 scripts/factory.py --count "$COUNT"

# 5. Pack Results
echo "📦 [5/5] Compressing Results..."
chmod +x scripts/pack_images.sh
./scripts/pack_images.sh

echo "============================================="
echo "✅ MISSION COMPLETE!"
echo "👉 1. Right-Click the 'lady_nuggets_batch_....zip' file -> Download."
echo "👉 2. Go to RunPod Dashboard -> TERMINATE POD (Trash Icon)."
echo "============================================="
