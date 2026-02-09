#!/bin/bash
# scripts/factory_only.sh - FIXED VERSION
# Run this in RunPod terminal

set -e  # Exit on error

echo "🏭 Lady Nuggets Factory - RunPod Edition"
echo "========================================="

# 1. Config
export REFORGE_API="http://127.0.0.1:7860"
MODEL_DIR="/workspace/stable-diffusion-webui/models/Stable-diffusion"
MODEL_NAME="oneObsession_v19Atypical.safetensors"
MODEL_URL="https://civitai.com/api/download/models/2443982?type=Model&format=SafeTensor&size=pruned&fp=fp16"

# 2. Check & Download Model
echo "📦 [1/4] Checking Model..."
if [ ! -f "$MODEL_DIR/$MODEL_NAME" ]; then
    echo "   ⬇️ Downloading OneObsession (2GB)..."
    mkdir -p "$MODEL_DIR"
    wget -q --show-progress "$MODEL_URL" -O "$MODEL_DIR/$MODEL_NAME"
    echo "   ✅ Downloaded!"
    NEED_RESTART=true
else
    echo "   ✅ Model exists"
    NEED_RESTART=false
fi

# 3. Restart Server if needed (to detect new model)
if [ "$NEED_RESTART" = true ]; then
    echo "🔄 [2/4] Restarting ReForge to detect model..."
    pkill -f "launch.py" || true
    sleep 3
    
    cd /workspace/stable-diffusion-webui
    nohup python3 launch.py --nowebui --api --listen --port 7860 --xformers > /workspace/reforge.log 2>&1 &
    
    echo "   ⏳ Waiting for server..."
    for i in {1..120}; do
        if curl -s http://127.0.0.1:7860/docs > /dev/null 2>&1; then
            echo "   ✅ Server ready!"
            break
        fi
        sleep 2
    done
else
    echo "⏭️  [2/4] Server restart not needed"
fi

# 4. Prepare Batch
BATCH_ID=$(date +"%Y%m%d_%H%M%S")
BATCH_DIR="content/batch_${BATCH_ID}"
mkdir -p "$BATCH_DIR"

# 5. Generate
echo "🎨 [3/4] Generating 2 Images (Batch: $BATCH_ID)..."
cd /workspace/lady-nuggets-enterprise || exit

# Use updated factory.py
python3 scripts/factory.py --count 2 --output "$BATCH_DIR"

# 6. Zip
echo "📦 [4/4] Compressing..."
ZIP_NAME="lady_nuggets_${BATCH_ID}.zip"
zip -q -r "$ZIP_NAME" "$BATCH_DIR"

echo ""
echo "========================================="
echo "✅ DONE! Download: $ZIP_NAME"
echo "📊 Generated: $(ls -1 $BATCH_DIR/*.png 2>/dev/null | wc -l) images"
echo "========================================="
