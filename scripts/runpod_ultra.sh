#!/bin/bash
# ==============================================================================
# 🚀 LADY NUGGETS ENTERPRISE - RUNPOD ULTRA SCRIPT
# ==============================================================================
# Ultra-robust master script for RunPod deployment.
# Auto-detects environment, handles errors gracefully, provides detailed logs.
#
# Usage: 
#   ./scripts/runpod_ultra.sh                  # Generate 2 images (default)
#   ./scripts/runpod_ultra.sh --count 10       # Generate 10 images
#   ./scripts/runpod_ultra.sh --help           # Show help
# ==============================================================================

set -e  # Exit on error
trap 'echo "❌ Script failed at line $LINENO"; exit 1' ERR

# === COLORS ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# === DEFAULTS ===
DEFAULT_COUNT=2
IMAGE_COUNT=$DEFAULT_COUNT
SKIP_MODEL_DOWNLOAD=false
VERBOSE=false

# === PARSE ARGUMENTS ===
while [[ $# -gt 0 ]]; do
    case $1 in
        --count|-c)
            IMAGE_COUNT="$2"
            shift 2
            ;;
        --no-model)
            SKIP_MODEL_DOWNLOAD=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --count, -c NUMBER    Number of images to generate (default: 2)"
            echo "  --no-model            Skip model download check"
            echo "  --verbose, -v         Show detailed output"
            echo "  --help, -h            Show this help message"
            exit 0
            ;;
        *)
            # Legacy support: first argument without flag = count
            if [[ $1 =~ ^[0-9]+$ ]]; then
                IMAGE_COUNT="$1"
            fi
            shift
            ;;
    esac
done

# === BANNER ===
clear
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       🏭 LADY NUGGETS ENTERPRISE - RUNPOD ULTRA SCRIPT v2.0         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ==============================================================================
# STEP 0: ENVIRONMENT DETECTION
# ==============================================================================
echo -e "${BLUE}🔍 [0/7] Detecting Environment...${NC}"

# Detect if we're on RunPod
if [ -d "/workspace" ]; then
    echo -e "   ${GREEN}✅ RunPod Environment Detected${NC}"
    IS_RUNPOD=true
    WORK_DIR="/workspace/lady-nuggets-enterprise"
    SD_DIR="/workspace/stable-diffusion-webui"
else
    echo -e "   ${YELLOW}⚠️  Local Environment Detected${NC}"
    IS_RUNPOD=false
    WORK_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
    SD_DIR="$HOME/stable-diffusion-webui"
fi

echo "   📁 Working Directory: $WORK_DIR"
echo "   📁 SD Directory: $SD_DIR"

# ==============================================================================
# STEP 1: FIND ACTIVE SERVER (PORT DETECTION)
# ==============================================================================
echo ""
echo -e "${BLUE}🔌 [1/7] Detecting SD API Server...${NC}"

REFORGE_API=""
PORTS_TO_CHECK=(7860 7861 7862 8080 3000)

for port in "${PORTS_TO_CHECK[@]}"; do
    if curl -s --connect-timeout 2 "http://127.0.0.1:$port/docs" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Server found on port $port${NC}"
        REFORGE_API="http://127.0.0.1:$port"
        break
    fi
done

if [ -z "$REFORGE_API" ]; then
    echo -e "   ${YELLOW}⚠️  No active server found. Will attempt to start one.${NC}"
    NEED_SERVER_START=true
    REFORGE_API="http://127.0.0.1:7860"
else
    echo -e "   ${GREEN}✅ Using: $REFORGE_API${NC}"
    NEED_SERVER_START=false
fi

export REFORGE_API

# ==============================================================================
# STEP 2: API KEYS
# ==============================================================================
echo ""
echo -e "${BLUE}🔑 [2/7] Checking API Keys...${NC}"

ENV_FILE="$WORK_DIR/config/.env"
KEYS_OK=true

# Create .env if missing
if [ ! -f "$ENV_FILE" ]; then
    echo -e "   ${YELLOW}⚠️  Creating .env template...${NC}"
    mkdir -p "$WORK_DIR/config"
    cat > "$ENV_FILE" << 'EOF'
# === LADY NUGGETS ENTERPRISE ===
# AI Prompt Generation (At least one required)
GROQ_KEY=
OPENROUTER_KEY=

# Stable Diffusion API
REFORGE_API=http://127.0.0.1:7860
EOF
    KEYS_OK=false
fi

# Load .env
set -a
source "$ENV_FILE" 2>/dev/null || true
set +a

# Override REFORGE_API with detected port
export REFORGE_API

# Check for at least one AI key
if [ -z "$GROQ_KEY" ] && [ -z "$OPENROUTER_KEY" ]; then
    echo -e "   ${RED}❌ No AI API key found!${NC}"
    echo "      You need at least one of: GROQ_KEY or OPENROUTER_KEY"
    echo ""
    echo -e "   ${CYAN}📌 TO FIX: Edit $ENV_FILE${NC}"
    echo "      💡 Get free keys at:"
    echo "         - Groq: https://console.groq.com/keys"
    echo "         - OpenRouter: https://openrouter.ai/keys"
    KEYS_OK=false
else
    [ -n "$GROQ_KEY" ] && echo -e "   ${GREEN}✅ GROQ_KEY: ${GROQ_KEY:0:15}...${NC}"
    [ -n "$OPENROUTER_KEY" ] && echo -e "   ${GREEN}✅ OPENROUTER_KEY: ${OPENROUTER_KEY:0:15}...${NC}"
fi

if [ "$KEYS_OK" = false ]; then
    echo ""
    echo -e "${RED}⛔ Setup incomplete. Fix the issues above and run again.${NC}"
    exit 1
fi

# ==============================================================================
# STEP 3: DEPENDENCIES
# ==============================================================================
echo ""
echo -e "${BLUE}📦 [3/7] Installing Dependencies...${NC}"

pip install -q python-dotenv requests 2>/dev/null || pip install python-dotenv requests
if command -v apt-get &> /dev/null; then
    apt-get update -qq && apt-get install -y -qq zip 2>/dev/null || true
fi
echo -e "   ${GREEN}✅ Dependencies installed${NC}"

# ==============================================================================
# STEP 4: MODEL CHECK
# ==============================================================================
echo ""
echo -e "${BLUE}🎨 [4/7] Checking Model Checkpoint...${NC}"

if [ "$SKIP_MODEL_DOWNLOAD" = true ]; then
    echo -e "   ${YELLOW}⏭️  Skipping model download (--no-model flag)${NC}"
else
    MODEL_DIR="$SD_DIR/models/Stable-diffusion"
    MODEL_NAME="oneObsession_v19Atypical.safetensors"
    MODEL_URL="https://civitai.com/api/download/models/2443982?type=Model&format=SafeTensor&size=pruned&fp=fp16"
    MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

    mkdir -p "$MODEL_DIR" 2>/dev/null || true

    if [ -f "$MODEL_PATH" ]; then
        FILE_SIZE=$(stat -c%s "$MODEL_PATH" 2>/dev/null || stat -f%z "$MODEL_PATH" 2>/dev/null || echo "0")
        if [ "$FILE_SIZE" -lt 1000000 ]; then
            echo -e "   ${YELLOW}⚠️  Model file corrupted. Removing...${NC}"
            rm -f "$MODEL_PATH"
        fi
    fi

    if [ ! -f "$MODEL_PATH" ]; then
        echo -e "   ${CYAN}⬇️  Downloading OneObsession v19 (~2GB)...${NC}"
        wget -q --show-progress "$MODEL_URL" -O "$MODEL_PATH" || {
            echo -e "   ${YELLOW}⚠️  Download failed. Will use available model.${NC}"
        }
    else
        echo -e "   ${GREEN}✅ Model exists: $MODEL_NAME${NC}"
    fi
fi

# ==============================================================================
# STEP 5: LORA CHECK
# ==============================================================================
echo ""
echo -e "${BLUE}🧩 [5/7] Checking LoRA Files...${NC}"

LORA_DIR="$SD_DIR/models/Lora"
mkdir -p "$LORA_DIR" 2>/dev/null || true

# Check if LadyNuggets LoRA exists
if ls "$LORA_DIR"/LadyNuggets* 2>/dev/null | head -1 > /dev/null; then
    echo -e "   ${GREEN}✅ LadyNuggets LoRA found${NC}"
else
    echo -e "   ${YELLOW}⚠️  LadyNuggets LoRA not found${NC}"
    echo "      Factory will work without it (using base prompt only)"
fi

# ==============================================================================
# STEP 6: SERVER STARTUP (IF NEEDED)
# ==============================================================================
echo ""
echo -e "${BLUE}🚀 [6/7] Server Management...${NC}"

wait_for_server() {
    local max_wait=180
    local waited=0
    echo -n "   ⏳ Waiting for server"
    while [ $waited -lt $max_wait ]; do
        if curl -s --connect-timeout 2 "$REFORGE_API/docs" > /dev/null 2>&1; then
            echo ""
            echo -e "   ${GREEN}✅ Server is UP!${NC}"
            return 0
        fi
        echo -n "."
        sleep 3
        ((waited+=3))
    done
    echo ""
    return 1
}

if [ "$NEED_SERVER_START" = true ]; then
    if [ "$IS_RUNPOD" = true ]; then
        echo -e "   ${CYAN}🔄 Starting Stable Diffusion server...${NC}"
        
        # Kill any zombie processes
        pkill -f "launch.py" 2>/dev/null || true
        sleep 2
        
        cd "$SD_DIR"
        
        # Fix root permission if needed
        sed -i 's/can_run_as_root=0/can_run_as_root=1/g' webui.sh 2>/dev/null || true
        
        # Start server
        nohup python3 launch.py --nowebui --api --listen --port 7860 --xformers > /workspace/reforge.log 2>&1 &
        
        if ! wait_for_server; then
            echo -e "   ${RED}❌ Server failed to start!${NC}"
            echo "   📜 Last 20 lines of log:"
            tail -n 20 /workspace/reforge.log
            exit 1
        fi
    else
        echo -e "   ${RED}❌ No server running and cannot auto-start locally.${NC}"
        echo "      Please start your local SD server first, then run this script again."
        exit 1
    fi
else
    echo -e "   ${GREEN}✅ Server already running${NC}"
fi

# Verify server responds to API
echo -n "   🔍 Verifying API... "
if curl -s "$REFORGE_API/sdapi/v1/options" > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}Warning: API may not be fully ready${NC}"
fi

# ==============================================================================
# STEP 7: GENERATE IMAGES
# ==============================================================================
echo ""
echo -e "${BLUE}🎨 [7/7] Starting Image Generation...${NC}"
echo ""

cd "$WORK_DIR"

# Create batch folder
BATCH_ID=$(date +"%Y%m%d_%H%M%S")
BATCH_DIR="content/batch_${BATCH_ID}"
mkdir -p "$BATCH_DIR"

echo -e "   ${CYAN}📋 Configuration:${NC}"
echo "      - Images to generate: $IMAGE_COUNT"
echo "      - Output directory: $BATCH_DIR"
echo "      - API endpoint: $REFORGE_API"
echo ""

# Run factory
python3 scripts/factory.py --count "$IMAGE_COUNT" --output "$BATCH_DIR"
GEN_EXIT_CODE=$?

if [ $GEN_EXIT_CODE -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Generation failed with exit code $GEN_EXIT_CODE${NC}"
    echo "   Check the output above for errors."
    exit 1
fi

# ==============================================================================
# PACKAGING
# ==============================================================================
echo ""
echo -e "${BLUE}📦 Compressing Results...${NC}"

ZIP_NAME="lady_nuggets_${BATCH_ID}.zip"
zip -q -r "$ZIP_NAME" "$BATCH_DIR"

# Count images
IMG_COUNT=$(find "$BATCH_DIR" -name "*.png" 2>/dev/null | wc -l | tr -d ' ')

# ==============================================================================
# SUMMARY
# ==============================================================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                         ✅ COMPLETE!                                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "   📁 Output folder: ${CYAN}$BATCH_DIR${NC}"
echo -e "   📦 ZIP file: ${CYAN}$ZIP_NAME${NC}"
echo -e "   🖼️  Images generated: ${GREEN}$IMG_COUNT${NC}"
echo ""
echo -e "   ${YELLOW}💡 To generate more:${NC}"
echo "      ./scripts/runpod_ultra.sh --count 10"
echo ""
if [ "$IS_RUNPOD" = true ]; then
    echo -e "   ${RED}🛑 Don't forget to STOP your RunPod when done!${NC}"
fi
echo ""
