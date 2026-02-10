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
FACTORY_EXTRA_ARGS=""
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
        --random-char)
            FACTORY_EXTRA_ARGS="$FACTORY_EXTRA_ARGS --random-char"
            shift
            ;;
        --lora)
            FACTORY_EXTRA_ARGS="$FACTORY_EXTRA_ARGS --lora"
            shift
            ;;
        --no-hires)
            FACTORY_EXTRA_ARGS="$FACTORY_EXTRA_ARGS --no-hires"
            shift
            ;;
        --theme)
            FACTORY_EXTRA_ARGS="$FACTORY_EXTRA_ARGS --theme \"$2\""
            shift 2
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
            echo "  --random-char         Use random anime characters (not just Lady Nuggets)"
            echo "  --lora                Enable character LoRA"
            echo "  --theme TEXT          Use a specific theme"
            echo "  --no-hires            Disable Hires Fix (faster, lower quality)"
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
# STEP 1: FIND ACTIVE SD API (validates JSON, not nginx)
# ==============================================================================
echo ""
echo -e "${BLUE}🔌 [1/7] Detecting SD API Server...${NC}"

REFORGE_API=""
NEED_SERVER_START=false
PORTS_TO_CHECK=(7860 7861 7862 8080 3000)

for port in "${PORTS_TO_CHECK[@]}"; do
    # Must return valid JSON from SD API, not nginx HTML
    RESPONSE=$(curl -s --connect-timeout 2 "http://127.0.0.1:$port/sdapi/v1/sd-models" 2>/dev/null || echo "")
    if echo "$RESPONSE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
        echo -e "   ${GREEN}✅ SD API verified on port $port${NC}"
        REFORGE_API="http://127.0.0.1:$port"
        break
    elif [ -n "$RESPONSE" ]; then
        echo -e "   ${YELLOW}⚠️  Port $port responds but not SD API (nginx proxy?)${NC}"
    fi
done

if [ -z "$REFORGE_API" ]; then
    echo -e "   ${YELLOW}⚠️  No active SD API found. Will start server on port 7860.${NC}"
    NEED_SERVER_START=true
    REFORGE_API="http://127.0.0.1:7860"
else
    echo -e "   ${GREEN}✅ Using: $REFORGE_API${NC}"
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
# STEP 4: MODEL CHECKPOINTS
# ==============================================================================
echo ""
echo -e "${BLUE}🎨 [4/7] Checking Model Checkpoints...${NC}"

# CivitAI API Key (add to .env for automated downloads)
CIVITAI_TOKEN="${CIVITAI_TOKEN:-}"

if [ "$SKIP_MODEL_DOWNLOAD" = true ]; then
    echo -e "   ${YELLOW}⏭️  Skipping model download (--no-model flag)${NC}"
else
    MODEL_DIR="$SD_DIR/models/Stable-diffusion"
    mkdir -p "$MODEL_DIR" 2>/dev/null || true

    # --- WAI-Illustrious (PRIMARY - best out-of-box anime quality) ---
    WAI_MODEL="waiIllustriousSDXL_v160.safetensors"
    WAI_PATH="$MODEL_DIR/$WAI_MODEL"
    if [ -f "$WAI_PATH" ]; then
        FILE_SIZE_MB=$(($(stat -c%s "$WAI_PATH" 2>/dev/null || stat -f%z "$WAI_PATH" 2>/dev/null || echo "0") / 1024 / 1024))
        echo -e "   ${GREEN}✅ WAI-Illustrious v16: ${FILE_SIZE_MB}MB${NC}"
    else
        if [ -n "$CIVITAI_TOKEN" ]; then
            echo -e "   ${CYAN}⬇️  Downloading WAI-Illustrious v16 (~6.5GB, best anime checkpoint)...${NC}"
            # CivitAI versionId=2514310 = WAI-NSFW-illustrious-SDXL v16.0
            curl -L -o "$WAI_PATH" \
                "https://civitai.com/api/download/models/2514310?token=${CIVITAI_TOKEN}" 2>/dev/null || true
            FILE_SIZE=$(stat -c%s "$WAI_PATH" 2>/dev/null || stat -f%z "$WAI_PATH" 2>/dev/null || echo "0")
            if [ "$FILE_SIZE" -gt 1000000000 ]; then
                echo -e "   ${GREEN}✅ WAI-Illustrious downloaded!${NC}"
            else
                echo -e "   ${YELLOW}⚠️  WAI download may have failed (${FILE_SIZE} bytes)${NC}"
                rm -f "$WAI_PATH" 2>/dev/null
            fi
        else
            echo -e "   ${YELLOW}⚠️  CIVITAI_TOKEN not set. Cannot download WAI-Illustrious.${NC}"
        fi
    fi

    # --- OneObsession v19 (SECONDARY - good for 2.5D / color) ---
    MODEL_NAME="oneObsession_v19Atypical.safetensors"
    MODEL_PATH="$MODEL_DIR/$MODEL_NAME"
    if [ -f "$MODEL_PATH" ]; then
        FILE_SIZE_MB=$(($(stat -c%s "$MODEL_PATH" 2>/dev/null || stat -f%z "$MODEL_PATH" 2>/dev/null || echo "0") / 1024 / 1024))
        echo -e "   ${GREEN}✅ OneObsession v19: ${FILE_SIZE_MB}MB${NC}"
    else
        if [ -n "$CIVITAI_TOKEN" ]; then
            echo -e "   ${CYAN}⬇️  Downloading OneObsession v19 (~6GB)...${NC}"
            curl -L -o "$MODEL_PATH" \
                "https://civitai.com/api/download/models/2443982?type=Model&format=SafeTensor&size=pruned&fp=fp16&token=${CIVITAI_TOKEN}"
            FILE_SIZE=$(stat -c%s "$MODEL_PATH" 2>/dev/null || stat -f%z "$MODEL_PATH" 2>/dev/null || echo "0")
            if [ "$FILE_SIZE" -gt 1000000000 ]; then
                echo -e "   ${GREEN}✅ OneObsession downloaded!${NC}"
            else
                echo -e "   ${YELLOW}⚠️  OneObsession download may have failed${NC}"
                rm -f "$MODEL_PATH" 2>/dev/null
            fi
        else
            echo -e "   ${YELLOW}   Can't download without CIVITAI_TOKEN${NC}"
        fi
    fi
fi

# ==============================================================================
# STEP 5: EXTENSIONS & LORA SETUP
# ==============================================================================
echo ""
echo -e "${BLUE}🧩 [5/7] Setting up Extensions & LoRAs...${NC}"

# --- ADetailer Extension (fixes hands & faces) ---
ADETAILER_DIR="$SD_DIR/extensions/adetailer"
if [ -d "$ADETAILER_DIR" ]; then
    echo -e "   ${GREEN}✅ ADetailer extension installed${NC}"
else
    echo -e "   ${CYAN}⬇️  Installing ADetailer (face + hand fix)...${NC}"
    
    # Method 1: git clone (Anapnoe fork) — || true prevents set -e crash
    GIT_TERMINAL_PROMPT=0 git clone --depth 1 https://github.com/Anapnoe/stable-diffusion-webui-adetailer.git "$ADETAILER_DIR" 2>/dev/null || true
    
    if [ ! -d "$ADETAILER_DIR" ]; then
        # Method 2: Original repo
        GIT_TERMINAL_PROMPT=0 git clone --depth 1 https://github.com/Bing-su/adetailer.git "$ADETAILER_DIR" 2>/dev/null || true
    fi
    
    if [ ! -d "$ADETAILER_DIR" ]; then
        # Method 3: Download as zip (works even when git is blocked)
        echo -e "   ${YELLOW}   Git failed, trying zip download...${NC}"
        TEMP_ZIP="/tmp/adetailer.zip"
        curl -sL -o "$TEMP_ZIP" "https://github.com/Bing-su/adetailer/archive/refs/heads/main.zip" 2>/dev/null
        if [ -f "$TEMP_ZIP" ] && [ "$(stat -c%s "$TEMP_ZIP" 2>/dev/null || stat -f%z "$TEMP_ZIP" 2>/dev/null || echo "0")" -gt 10000 ]; then
            unzip -q "$TEMP_ZIP" -d "/tmp/adetailer_extract" 2>/dev/null
            mv /tmp/adetailer_extract/adetailer-main "$ADETAILER_DIR" 2>/dev/null
            rm -rf "$TEMP_ZIP" /tmp/adetailer_extract 2>/dev/null
        fi
    fi
    
    if [ -d "$ADETAILER_DIR" ]; then
        # Install dependencies
        pip install ultralytics 2>/dev/null || true
        echo -e "   ${GREEN}✅ ADetailer installed! Server will restart to load it.${NC}"
        NEED_SERVER_START=true
    else
        echo -e "   ${YELLOW}⚠️  ADetailer auto-install failed${NC}"
        echo -e "   ${YELLOW}   Try manual: pip install adetailer && cd $SD_DIR/extensions && git clone https://github.com/Bing-su/adetailer.git${NC}"
    fi
fi

# --- LoRA Files ---
LORA_DIR="$SD_DIR/models/Lora"
mkdir -p "$LORA_DIR" 2>/dev/null || true

# Aesthetic Quality LoRA (quality booster - always download)
AESTHETIC_LORA="$LORA_DIR/aesthetic_quality_masterpiece.safetensors"
if [ -f "$AESTHETIC_LORA" ]; then
    echo -e "   ${GREEN}✅ Aesthetic Quality LoRA found${NC}"
else
    if [ -n "$CIVITAI_TOKEN" ]; then
        echo -e "   ${CYAN}⬇️  Downloading Aesthetic Quality LoRA...${NC}"
        curl -L -o "$AESTHETIC_LORA" \
            "https://civitai.com/api/download/models/2241189?type=Model&format=SafeTensor&token=${CIVITAI_TOKEN}" 2>/dev/null
        if [ -f "$AESTHETIC_LORA" ] && [ "$(stat -c%s "$AESTHETIC_LORA" 2>/dev/null || stat -f%z "$AESTHETIC_LORA" 2>/dev/null || echo "0")" -gt 1000000 ]; then
            echo -e "   ${GREEN}✅ Aesthetic LoRA downloaded${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Aesthetic LoRA download may have failed${NC}"
            rm -f "$AESTHETIC_LORA" 2>/dev/null
        fi
    else
        echo -e "   ${YELLOW}⚠️  CIVITAI_TOKEN not set, can't download Aesthetic LoRA${NC}"
    fi
fi

# LadyNuggets Character LoRA (optional)
if ls "$LORA_DIR"/LadyNuggets* 2>/dev/null | head -1 > /dev/null; then
    echo -e "   ${GREEN}✅ LadyNuggets LoRA found (use --lora to activate)${NC}"
else
    echo -e "   ${YELLOW}ℹ️  LadyNuggets LoRA not found (character LoRA optional)${NC}"
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
        # Validate real SD API (JSON), not just HTTP response
        RESPONSE=$(curl -s --connect-timeout 2 "http://127.0.0.1:7860/sdapi/v1/sd-models" 2>/dev/null || echo "")
        if echo "$RESPONSE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
            echo ""
            echo -e "   ${GREEN}✅ Server is UP! (API verified)${NC}"
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
    # Check if server is already running (detected in Step 1)
    if [ -n "$REFORGE_API" ]; then
        # Server already running — DON'T kill it!
        # Forge template runs its own server, we can't restart it with launch.py
        echo -e "   ${YELLOW}⚠️  Extensions were installed but server is already running${NC}"
        echo -e "   ${YELLOW}   ADetailer will be active on NEXT pod restart${NC}"
        echo -e "   ${GREEN}✅ Using existing server at $REFORGE_API${NC}"
    elif [ "$IS_RUNPOD" = true ]; then
        echo -e "   ${CYAN}🔄 Starting Stable Diffusion server...${NC}"
        
        # Try to find the correct launch file
        LAUNCH_FILE=""
        for candidate in "$SD_DIR/launch.py" "$SD_DIR/webui.py" "$SD_DIR/main.py"; do
            if [ -f "$candidate" ]; then
                LAUNCH_FILE="$candidate"
                break
            fi
        done
        
        if [ -z "$LAUNCH_FILE" ]; then
            echo -e "   ${YELLOW}⚠️  Cannot find launch file in $SD_DIR${NC}"
            echo -e "   ${YELLOW}   The server was running before but we can't restart it${NC}"
            echo -e "   ${YELLOW}   Please restart the pod to apply extension changes${NC}"
        else
            # Kill any existing processes
            pkill -f "launch.py" 2>/dev/null || true
            pkill -f "webui.py" 2>/dev/null || true
            sleep 3
            
            cd "$SD_DIR"
            sed -i 's/can_run_as_root=0/can_run_as_root=1/g' webui.sh 2>/dev/null || true
            
            REFORGE_API="http://127.0.0.1:7860"
            export REFORGE_API
            nohup python3 "$LAUNCH_FILE" --nowebui --api --listen --port 7860 --xformers --medvram-sdxl > /workspace/reforge.log 2>&1 &
            
            if ! wait_for_server; then
                echo -e "   ${RED}❌ Server failed to start!${NC}"
                echo "   📜 Last 20 lines of log:"
                tail -n 20 /workspace/reforge.log
                exit 1
            fi
            
            REFORGE_API="http://127.0.0.1:7860"
            export REFORGE_API
        fi
    else
        echo -e "   ${RED}❌ No server running and cannot auto-start locally.${NC}"
        echo "      Please start your local SD server first, then run this script again."
        exit 1
    fi
else
    echo -e "   ${GREEN}✅ Server already running at $REFORGE_API${NC}"
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

# Run factory with all flags
eval python3 scripts/factory.py --count "$IMAGE_COUNT" --output "$BATCH_DIR" $FACTORY_EXTRA_ARGS
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
