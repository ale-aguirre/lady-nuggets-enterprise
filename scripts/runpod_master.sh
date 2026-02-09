#!/bin/bash
# ==============================================================================
# LADY NUGGETS ENTERPRISE - RUNPOD MASTER SCRIPT
# ==============================================================================
# One-click deployment for RunPod. Run this ONCE when you start a new pod.
# Usage: bash scripts/runpod_master.sh
# ==============================================================================

set -e  # Exit on error

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║       🏭 LADY NUGGETS ENTERPRISE - RUNPOD MASTER SCRIPT          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# ==============================================================================
# STEP 1: ENVIRONMENT VARIABLES
# ==============================================================================
echo "📋 [1/6] Checking Environment Variables..."

ENV_FILE="/workspace/lady-nuggets-enterprise/config/.env"
ENV_OK=true

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "   ⚠️  .env file not found. Creating template..."
    mkdir -p /workspace/lady-nuggets-enterprise/config
    cat > "$ENV_FILE" << 'EOF'
# === LADY NUGGETS ENTERPRISE CONFIG ===
# Fill in your API keys below

# AI Prompt Generation (At least one required)
GROQ_KEY=
OPENROUTER_KEY=

# Stable Diffusion API
REFORGE_API=http://127.0.0.1:7860

# Optional
PATREON_LINK=https://patreon.com/ladynuggets
EOF
    echo "   📝 Created template at: $ENV_FILE"
    ENV_OK=false
fi

# Load current .env
source "$ENV_FILE" 2>/dev/null || true

# Validate required keys
if [ -z "$GROQ_KEY" ] && [ -z "$OPENROUTER_KEY" ]; then
    echo "   ❌ ERROR: No AI API key found!"
    echo "      You need at least one of: GROQ_KEY or OPENROUTER_KEY"
    echo ""
    echo "   📌 TO FIX: Edit $ENV_FILE and add your keys:"
    echo "      nano $ENV_FILE"
    echo ""
    echo "   💡 Get free keys at:"
    echo "      - Groq: https://console.groq.com/keys"
    echo "      - OpenRouter: https://openrouter.ai/keys"
    ENV_OK=false
else
    if [ -n "$GROQ_KEY" ]; then
        echo "   ✅ GROQ_KEY: Found (${GROQ_KEY:0:10}...)"
    fi
    if [ -n "$OPENROUTER_KEY" ]; then
        echo "   ✅ OPENROUTER_KEY: Found (${OPENROUTER_KEY:0:15}...)"
    fi
fi

# Set REFORGE_API if not set
export REFORGE_API="${REFORGE_API:-http://127.0.0.1:7860}"
echo "   ✅ REFORGE_API: $REFORGE_API"

if [ "$ENV_OK" = false ]; then
    echo ""
    echo "   ⛔ Setup incomplete. Please fix the issues above and run again."
    exit 1
fi

# ==============================================================================
# STEP 2: DEPENDENCIES
# ==============================================================================
echo ""
echo "📦 [2/6] Installing Dependencies..."

pip install -q python-dotenv requests > /dev/null 2>&1
apt-get update -qq && apt-get install -y -qq zip > /dev/null 2>&1
echo "   ✅ Dependencies installed"

# ==============================================================================
# STEP 3: MODEL CHECKPOINT
# ==============================================================================
echo ""
echo "🎨 [3/6] Checking Model Checkpoint..."

MODEL_DIR="/workspace/stable-diffusion-webui/models/Stable-diffusion"
MODEL_NAME="oneObsession_v19Atypical.safetensors"
MODEL_URL="https://civitai.com/api/download/models/2443982?type=Model&format=SafeTensor&size=pruned&fp=fp16"
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

mkdir -p "$MODEL_DIR"

if [ -f "$MODEL_PATH" ]; then
    # Check if file is valid (> 1GB = probably real, < 1MB = probably error page)
    FILE_SIZE=$(stat -c%s "$MODEL_PATH" 2>/dev/null || stat -f%z "$MODEL_PATH" 2>/dev/null || echo "0")
    if [ "$FILE_SIZE" -lt 1000000 ]; then
        echo "   ⚠️  Model file exists but is too small (corrupted download)"
        echo "   🗑️  Removing corrupted file..."
        rm -f "$MODEL_PATH"
    fi
fi

if [ ! -f "$MODEL_PATH" ]; then
    echo "   ⬇️  Downloading OneObsession v19 (~2GB)..."
    echo "   📡 URL: $MODEL_URL"
    wget -q --show-progress "$MODEL_URL" -O "$MODEL_PATH"
    echo "   ✅ Model downloaded!"
    NEED_RESTART=true
else
    echo "   ✅ Model exists: $MODEL_NAME"
    NEED_RESTART=false
fi

# ==============================================================================
# STEP 4: ADETAILER EXTENSION
# ==============================================================================
echo ""
echo "💄 [4/6] Checking Adetailer Extension..."

ADETAILER_PATH="/workspace/stable-diffusion-webui/extensions/adetailer"
if [ ! -d "$ADETAILER_PATH" ]; then
    echo "   ⬇️  Installing Adetailer..."
    git clone -q https://github.com/Bing-su/adetailer.git "$ADETAILER_PATH"
    echo "   ✅ Adetailer installed!"
    NEED_RESTART=true
else
    echo "   ✅ Adetailer already installed"
fi

# ==============================================================================
# STEP 5: SERVER CHECK & RESTART
# ==============================================================================
echo ""
echo "🚀 [5/6] Checking ReForge Server..."

# Function to check if server is up
check_server() {
    curl -s "$REFORGE_API/docs" > /dev/null 2>&1
    return $?
}

# If we downloaded something new, restart server
if [ "$NEED_RESTART" = true ]; then
    echo "   🔄 New files detected. Restarting server..."
    
    # Kill existing server (safely)
    pkill -f "launch.py" 2>/dev/null || true
    sleep 3
    
    # Start server
    cd /workspace/stable-diffusion-webui
    sed -i 's/can_run_as_root=0/can_run_as_root=1/g' webui.sh 2>/dev/null || true
    
    nohup python3 launch.py --nowebui --api --listen --port 7860 --xformers > /workspace/reforge.log 2>&1 &
    
    echo "   ⏳ Waiting for server to start (this may take 2-3 minutes)..."
    for i in {1..120}; do
        if check_server; then
            echo "   ✅ Server is UP!"
            break
        fi
        if [ $i -eq 120 ]; then
            echo "   ❌ Server timeout. Check /workspace/reforge.log for errors."
            exit 1
        fi
        sleep 2
        echo -n "."
    done
    echo ""
else
    if check_server; then
        echo "   ✅ Server is already running"
    else
        echo "   ⚠️  Server not running. Starting..."
        cd /workspace/stable-diffusion-webui
        sed -i 's/can_run_as_root=0/can_run_as_root=1/g' webui.sh 2>/dev/null || true
        
        nohup python3 launch.py --nowebui --api --listen --port 7860 --xformers > /workspace/reforge.log 2>&1 &
        
        echo "   ⏳ Waiting for server..."
        for i in {1..120}; do
            if check_server; then
                echo "   ✅ Server is UP!"
                break
            fi
            sleep 2
            echo -n "."
        done
        echo ""
    fi
fi

# ==============================================================================
# STEP 6: GENERATE IMAGES
# ==============================================================================
echo ""
echo "🎨 [6/6] Starting Image Generation..."
echo ""

cd /workspace/lady-nuggets-enterprise

# Create batch folder
BATCH_ID=$(date +"%Y%m%d_%H%M%S")
BATCH_DIR="content/batch_${BATCH_ID}"
mkdir -p "$BATCH_DIR"

# Run factory
python3 scripts/factory.py --count 2 --output "$BATCH_DIR"

# Zip results
echo ""
echo "📦 Compressing results..."
ZIP_NAME="lady_nuggets_${BATCH_ID}.zip"
zip -q -r "$ZIP_NAME" "$BATCH_DIR"

# Summary
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                        ✅ COMPLETE!                              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "   📁 Output folder: $BATCH_DIR"
echo "   📦 ZIP file: $ZIP_NAME"
echo "   📊 Images generated: $(ls -1 $BATCH_DIR/*.png 2>/dev/null | wc -l)"
echo ""
echo "   💡 To generate more images:"
echo "      python3 scripts/factory.py --count 10"
echo ""
echo "   🛑 Don't forget to STOP your RunPod when done!"
echo ""
