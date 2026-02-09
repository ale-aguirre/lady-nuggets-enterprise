#!/bin/bash
# scripts/factory_only.sh
# Run this if the server is already running!

# 1. Setup Env (Assumes you already exported these in the terminal)
# export GROQ_KEY="YOUR_KEY"
# export OPENROUTER_KEY="YOUR_KEY"
export REFORGE_API="http://127.0.0.1:7860"

# 2. Check & Download Model (User reported missing model)
MODEL_DIR="/workspace/stable-diffusion-webui/models/Stable-diffusion"
MODEL_NAME="oneObsession_v19Atypical.safetensors"
MODEL_URL="https://civitai.com/api/download/models/302970"

if [ ! -f "$MODEL_DIR/$MODEL_NAME" ]; then
    echo "⬇️ Model Check: MISSING! Downloading OneObsession now..."
    mkdir -p "$MODEL_DIR"
    wget -q --show-progress "$MODEL_URL" -O "$MODEL_DIR/$MODEL_NAME"
else
    echo "✅ Model Check: OneObsession Found."
fi

# 2b. Prepare Batch Folder
BATCH_ID=$(date +"%Y%m%d_%H%M%S")
BATCH_DIR="content/batch_${BATCH_ID}"
mkdir -p "$BATCH_DIR"

# FIX: Google Gemini / httplib2 dependency conflict
echo "🔧 Fixing dependencies (Just in case)..."
pip install "pyparsing==2.4.7" > /dev/null 2>&1

# 3. Generate
echo "🏭 Generating 2 Images (Batch: $BATCH_ID)..."
cd /workspace/lady-nuggets-enterprise || exit
python3 scripts/factory.py --count 2 --output "$BATCH_DIR"

# 4. Zip
echo "📦 Compressing..."
ZIP_NAME="lady_nuggets_${BATCH_ID}.zip"
zip -r "$ZIP_NAME" "$BATCH_DIR"

echo "✅ DONE! Download: $ZIP_NAME"
