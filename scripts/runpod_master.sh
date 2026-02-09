#!/bin/bash
# scripts/runpod_master.sh
# ONE-CLICK INSTALL & GENERATE SCRIPT

echo "🚀 STARTER: Lady Nuggets Enterprise Protocol"
echo "============================================="

# 1. Environment Setup
echo "📦 [1/5] Installing Dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
apt-get update && apt-get install -y zip > /dev/null 2>&1

# 1.5. RunPod specific config
export REFORGE_API="http://127.0.0.1:7860"

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
    wget -q --show-progress "https://civitai.com/api/download/models/2443982?type=Model&format=SafeTensor&size=pruned&fp=fp16" -O oneObsession_v19Atypical.safetensors
else
    echo "   -> Model ready."
fi

# 3.5. LoRA Download (Optional)
echo "🧩 [3.5/5] Checking LoRAs..."
LORA_DIR="/workspace/stable-diffusion-webui/models/Lora"
LORA_LIST="/workspace/lady-nuggets-enterprise/config/loras.txt"

if [ -f "$LORA_LIST" ]; then
    while IFS= read -r url || [ -n "$url" ]; do
        # Skip empty lines and comments
        [[ "$url" =~ ^#.*$ ]] || [[ -z "$url" ]] && continue
        
        echo "   -> Downloading LoRA: $url"
        cd "$LORA_DIR" || exit
        wget -q --content-disposition "$url"
    done < "$LORA_LIST"
else
    echo "   -> No loras.txt found. Skipping."
fi

# 3.9. START REFORGE SERVER (Critical)
echo "🚀 [3.9/5] Launching Stable Diffusion (API Mode)..."
cd /workspace/stable-diffusion-webui || exit

# FIX: Allow Root Execution (RunPod runs as root)
sed -i 's/can_run_as_root=0/can_run_as_root=1/g' webui.sh || true
# Alternative patch if variable name differs
sed -i 's/ERROR: This script must not be launched as root/echo "Running as root..."/g' webui.sh || true

# Start in background
nohup ./webui.sh --nowebui --api --listen --port 7860 > /workspace/reforge.log 2>&1 &
SERVER_PID=$!

echo "⏳ Waiting for Server (Port 7860)... This takes up to 10 mins on first run."
for i in {1..300}; do
    if curl -s http://127.0.0.1:7860 > /dev/null; then
        echo "✅ Server is UP!"
        break
    fi
    # Show last log line every 5s to keep user informed
    if (( i % 5 == 0 )); then
        echo ""
        tail -n 1 /workspace/reforge.log
    else
        echo -n "."
    fi
    sleep 2
done

# Check if still down
if ! curl -s http://127.0.0.1:7860 > /dev/null; then
    echo "❌ Server failed to start in time!"
    echo "📜 LOG DUMP:"
    cat /workspace/reforge.log
    exit 1
fi

# 4. Generate Images
cd /workspace/lady-nuggets-enterprise || exit
COUNT=${1:-6} # Default to 6 images if not specified

BATCH_ID=$(date +"%Y%m%d_%H%M%S")
BATCH_DIR="content/batch_${BATCH_ID}"
mkdir -p "$BATCH_DIR"

echo "🏭 [4/5] Generating $COUNT Images (Batch: $BATCH_ID)..."
python3 scripts/factory.py --count "$COUNT" --output "$BATCH_DIR"

# 5. Pack Results (ONLY NEW IMAGES)
echo "📦 [5/5] Compressing Results..."
ZIP_NAME="lady_nuggets_${BATCH_ID}.zip"
zip -r "$ZIP_NAME" "$BATCH_DIR"

echo "============================================="
echo "✅ MISSION COMPLETE!"
echo "👉 1. Right-Click the '$ZIP_NAME' file -> Download."
echo "👉 2. Go to RunPod Dashboard -> TERMINATE POD (Trash Icon)."
echo "============================================="
