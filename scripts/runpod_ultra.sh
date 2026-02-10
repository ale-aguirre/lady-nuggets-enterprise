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
        --preset)
            PRESET="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --count, -c NUMBER    Number of images to generate (default: 2)"
            echo "  --preset NAME         Load config/presets/NAME.env (e.g. 'oc-forced')"
            echo "  --random-char         Use random anime characters (not just Lady Nuggets)"
            echo "  --lora                Enable character LoRA"
            echo "  --theme TEXT          Use a specific theme"
            echo "  --no-hires            Disable Hires Fix (faster, lower quality)"
            echo "  --no-model            Skip model check"
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
    
    # Handle Presets
    if [ -n "$PRESET" ]; then
        PRESET_FILE="$WORK_DIR/config/presets/${PRESET}.env"
        if [ -f "$PRESET_FILE" ]; then
            echo -e "   ${CYAN}📋 Loading preset: ${PRESET}${NC}"
            # Backup current .env
            cp "$WORK_DIR/config/.env" "$WORK_DIR/config/.env.backup" 2>/dev/null || true
            # Apply preset
            cp "$PRESET_FILE" "$WORK_DIR/config/.env"
        else
            echo -e "   ${RED}❌ Preset not found: $PRESET_FILE${NC}"
            exit 1
        fi
    fi
    
    # Auto-detect SD installation (Forge, Reforge, or vanilla A1111)
    SD_DIR=""
    for candidate_dir in \
        "/workspace/stable-diffusion-webui-forge" \
        "/workspace/stable-diffusion-webui-reforge" \
        "/workspace/stable-diffusion-webui" \
        "/workspace/sd-webui"; do
        if [ -d "$candidate_dir" ]; then
            SD_DIR="$candidate_dir"
            break
        fi
    done
    
    if [ -z "$SD_DIR" ]; then
        echo -e "   ${YELLOW}⚠️  No SD installation found in /workspace${NC}"
        SD_DIR="/workspace/stable-diffusion-webui"  # fallback
    fi
else
    echo -e "   ${YELLOW}⚠️  Local Environment Detected${NC}"
    IS_RUNPOD=false
    WORK_DIR="$(dirname "$(dirname "$(realpath "$0")")")"
    SD_DIR="$HOME/stable-diffusion-webui"
fi

echo "   📁 Working Directory: $WORK_DIR"
echo "   📁 SD Directory: $SD_DIR"

# ==============================================================================
# STEP 1: FIND ACTIVE SD API
# ==============================================================================
echo ""
echo -e "${BLUE}🔌 [1/7] Detecting SD API Server...${NC}"

REFORGE_API=""
NEED_SERVER_START=false
SERVER_FOUND=false

# Function: check if a port has a working SD API (returns JSON)
check_sd_api() {
    local port=$1
    local response
    response=$(curl -s --connect-timeout 3 "http://127.0.0.1:$port/sdapi/v1/sd-models" 2>/dev/null || echo "")
    if [ -n "$response" ] && echo "$response" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
        return 0
    fi
    return 1
}

# Step 1a: Quick check all common ports
PORTS_TO_CHECK=(7860 7861 3000 3001 8080 8188)
for port in "${PORTS_TO_CHECK[@]}"; do
    if check_sd_api $port; then
        echo -e "   ${GREEN}✅ SD API found on port $port${NC}"
        REFORGE_API="http://127.0.0.1:$port"
        SERVER_FOUND=true
        break
    fi
done

# Step 1b: If not found and on RunPod, check Forge log for port and wait
if [ "$SERVER_FOUND" = false ] && [ "$IS_RUNPOD" = true ]; then
    FORGE_LOG="/workspace/logs/forge.log"
    
    # Try to find the actual port from Forge log
    FORGE_PORT=""
    if [ -f "$FORGE_LOG" ]; then
        # Forge logs "Running on local URL: http://0.0.0.0:XXXX"
        FORGE_PORT=$(grep -oP 'Running on local URL.*?:(\d+)' "$FORGE_LOG" 2>/dev/null | grep -oP '\d+$' | tail -1 || echo "")
        if [ -n "$FORGE_PORT" ]; then
            echo -e "   ${CYAN}ℹ️  Forge log shows port $FORGE_PORT${NC}"
            # Add this port to the front of our check list
            PORTS_TO_CHECK=($FORGE_PORT "${PORTS_TO_CHECK[@]}")
        fi
    fi
    
    # Wait for Forge to finish loading models (SDXL takes 3-5 min)
    echo -e "   ${CYAN}⏳ Waiting for Forge API to become ready (SDXL models take 3-5 min)...${NC}"
    MAX_WAIT=300  # 5 minutes
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        for port in "${PORTS_TO_CHECK[@]}"; do
            if check_sd_api $port; then
                echo ""
                echo -e "   ${GREEN}✅ SD API ready on port $port (waited ${WAITED}s)${NC}"
                REFORGE_API="http://127.0.0.1:$port"
                SERVER_FOUND=true
                break 2
            fi
        done
        
        # Show progress every 15 seconds
        if [ $((WAITED % 15)) -eq 0 ] && [ $WAITED -gt 0 ]; then
            echo -n "   ⏳ ${WAITED}s..."
            # Also check Forge log for progress
            if [ -f "$FORGE_LOG" ]; then
                LAST_LINE=$(tail -1 "$FORGE_LOG" 2>/dev/null || echo "")
                if echo "$LAST_LINE" | grep -qi "error\|exception\|failed" 2>/dev/null; then
                    echo " (Forge might have errors)"
                else
                    echo ""
                fi
            else
                echo ""
            fi
        fi
        
        sleep 5
        ((WAITED+=5))
    done
fi

if [ "$SERVER_FOUND" = true ]; then
    echo -e "   ${GREEN}✅ Using: $REFORGE_API${NC}"
else
    echo -e "   ${YELLOW}⚠️  No SD API found after waiting. Will try to start server.${NC}"
    NEED_SERVER_START=true
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
        # Install dependencies — but DON'T break numpy/scikit-image!
        # ultralytics pulls numpy 2.x which breaks skimage (and crashes Forge)
        pip install ultralytics 2>/dev/null || true
        # Fix scikit-image to work with numpy 2.x
        pip install -U scikit-image 2>/dev/null || true
        echo -e "   ${GREEN}✅ ADetailer installed!${NC}"
        echo -e "   ${YELLOW}   ℹ️  ADetailer will be active on next pod restart${NC}"
        # NOTE: We do NOT set NEED_SERVER_START here!
        # The running Forge server doesn't need to be restarted just for extensions.
        # Extensions load on server startup, so they'll be active next time.
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

# --- Lazy Embeddings (Quality Boost for Illustrious) ---
EMBEDDING_DIR="$SD_DIR/embeddings"
mkdir -p "$EMBEDDING_DIR" 2>/dev/null || true
echo -e "   ${CYAN}⬇️  Downloading Lazy Embeddings...${NC}"
# lazypos v2
if [ ! -f "$EMBEDDING_DIR/lazypos.safetensors" ] && [ -n "$CIVITAI_TOKEN" ]; then
    curl -L -o "$EMBEDDING_DIR/lazypos.safetensors" \
        "https://civitai.com/api/download/models/1268948?type=Model&format=SafeTensor&token=${CIVITAI_TOKEN}" 2>/dev/null && \
    echo -e "   ${GREEN}✅ lazypos downloaded${NC}"
else
    echo -e "   ${GREEN}✅ lazypos found${NC}"
fi
# lazyneg v2
if [ ! -f "$EMBEDDING_DIR/lazyneg.safetensors" ] && [ -n "$CIVITAI_TOKEN" ]; then
    curl -L -o "$EMBEDDING_DIR/lazyneg.safetensors" \
        "https://civitai.com/api/download/models/1268949?type=Model&format=SafeTensor&token=${CIVITAI_TOKEN}" 2>/dev/null && \
    echo -e "   ${GREEN}✅ lazyneg downloaded${NC}"
else
    echo -e "   ${GREEN}✅ lazyneg found${NC}"
fi


# Perfect Eyes LoRA (User Request)
PERFECT_EYES="$LORA_DIR/perfect_eyes.safetensors"
if [ ! -f "$PERFECT_EYES" ]; then
    echo -e "   ${CYAN}⬇️  Downloading Perfect Eyes LoRA...${NC}"
    curl -L -o "$PERFECT_EYES" \
        "https://civitai.com/api/download/models/2066663?type=Model&format=SafeTensor&token=${CIVITAI_TOKEN}" 2>/dev/null && \
    echo -e "   ${GREEN}✅ Perfect Eyes downloaded${NC}"
else
    echo -e "   ${GREEN}✅ Perfect Eyes LoRA found${NC}"
fi

# Perfect Hands LoRA (EnvyBetterHands - Quality Fix)
PERFECT_HANDS="$LORA_DIR/better_hands.safetensors"
if [ ! -f "$PERFECT_HANDS" ]; then
    echo -e "   ${CYAN}⬇️  Downloading Perfect Hands LoRA...${NC}"
    curl -L -o "$PERFECT_HANDS" \
        "https://civitai.com/api/download/models/2062094?type=Model&format=SafeTensor&token=${CIVITAI_TOKEN}" 2>/dev/null && \
    echo -e "   ${GREEN}✅ Perfect Hands downloaded${NC}"
else
    echo -e "   ${GREEN}✅ Perfect Hands LoRA found${NC}"
fi

# ==============================================================================
# STEP 6: SERVER STARTUP (IF NEEDED)
# ==============================================================================
echo ""
echo -e "${BLUE}🚀 [6/7] Server Management...${NC}"

if [ "$SERVER_FOUND" = true ]; then
    # Server was found in Step 1 — use it as-is
    echo -e "   ${GREEN}✅ Server running at $REFORGE_API${NC}"
    
elif [ "$SERVER_FOUND" = false ] && [ "$IS_RUNPOD" = true ]; then
    echo -e "   ${YELLOW}⚠️  No SD API detected. Attempting to start server...${NC}"
    
    # Diagnostic: show what's listening
    echo -e "   ${CYAN}📋 Diagnostic — active ports:${NC}"
    ss -tlnp 2>/dev/null | grep -E ':(7860|7861|3000|3001|8080|8188) ' | head -5 || echo "      (none found on SD ports)"
    
    # Diagnostic: show Forge process
    echo -e "   ${CYAN}📋 Diagnostic — Forge processes:${NC}"
    ps aux 2>/dev/null | grep -i "forge\|webui\|launch\|gradio" | grep -v grep | head -3 || echo "      (none found)"
    
    # Diagnostic: show Forge log tail
    FORGE_LOG="/workspace/logs/forge.log"
    if [ -f "$FORGE_LOG" ]; then
        echo -e "   ${CYAN}📋 Diagnostic — last 5 lines of forge.log:${NC}"
        tail -5 "$FORGE_LOG" 2>/dev/null | sed 's/^/      /'
    fi
    
    # Try to find launch file in the detected SD_DIR
    LAUNCH_FILE=""
    for candidate in "$SD_DIR/launch.py" "$SD_DIR/webui.py" "$SD_DIR/main.py"; do
        if [ -f "$candidate" ]; then
            LAUNCH_FILE="$candidate"
            echo -e "   ${CYAN}ℹ️  Found launch file: $LAUNCH_FILE${NC}"
            break
        fi
    done
    
    if [ -n "$LAUNCH_FILE" ]; then
        echo -e "   ${CYAN}🔄 Starting SD server on port 7860...${NC}"
        
        # Don't kill existing Forge if it's running on another port
        # Just start a new instance on 7860 with API enabled
        cd "$SD_DIR"
        sed -i 's/can_run_as_root=0/can_run_as_root=1/g' webui.sh 2>/dev/null || true
        
        nohup python3 "$LAUNCH_FILE" --api --listen --port 7860 --xformers --medvram-sdxl > /workspace/reforge_manual.log 2>&1 &
        SERVER_PID=$!
        echo -e "   ${CYAN}ℹ️  Server PID: $SERVER_PID${NC}"
        
        # Wait for server to become ready (up to 5 minutes)
        echo -e "   ${CYAN}⏳ Waiting for server to load model (up to 5 min)...${NC}"
        MAX_WAIT=300
        WAITED=0
        while [ $WAITED -lt $MAX_WAIT ]; do
            if check_sd_api 7860; then
                echo ""
                echo -e "   ${GREEN}✅ Server is UP on port 7860! (waited ${WAITED}s)${NC}"
                REFORGE_API="http://127.0.0.1:7860"
                SERVER_FOUND=true
                break
            fi
            
            # Check if process died
            if ! kill -0 $SERVER_PID 2>/dev/null; then
                echo ""
                echo -e "   ${RED}❌ Server process died!${NC}"
                echo -e "   ${YELLOW}📜 Last 20 lines of log:${NC}"
                tail -20 /workspace/reforge_manual.log 2>/dev/null | sed 's/^/      /'
                break
            fi
            
            # Show progress
            if [ $((WAITED % 30)) -eq 0 ] && [ $WAITED -gt 0 ]; then
                echo -e "   ⏳ ${WAITED}s... (still loading)"
                tail -1 /workspace/reforge_manual.log 2>/dev/null | sed 's/^/      /' || true
            fi
            
            sleep 5
            ((WAITED+=5))
        done
    else
        echo -e "   ${RED}❌ No launch file found in $SD_DIR${NC}"
        echo -e "   ${YELLOW}   Contents of SD_DIR:${NC}"
        ls -la "$SD_DIR"/*.py 2>/dev/null | head -5 | sed 's/^/      /' || echo "      (no python files found)"
    fi
    
elif [ "$SERVER_FOUND" = false ]; then
    echo -e "   ${RED}❌ No server running and cannot auto-start locally.${NC}"
    echo "      Please start your local SD server first, then run this script again."
    exit 1
fi

# Final API verification
echo ""
if [ "$SERVER_FOUND" = true ]; then
    echo -n "   🔍 Final API check... "
    if check_sd_api $(echo "$REFORGE_API" | grep -oP ':\K\d+'); then
        echo -e "${GREEN}✅ API confirmed working${NC}"
    else
        echo -e "${YELLOW}⚠️  API might not be fully ready${NC}"
    fi
    export REFORGE_API
else
    echo -e "   ${RED}❌ FATAL: No working SD API found.${NC}"
    echo -e "   ${YELLOW}   Possible causes:${NC}"
    echo -e "   ${YELLOW}   1. Forge is still loading (restart pod and wait 5 min before running script)${NC}"
    echo -e "   ${YELLOW}   2. Forge crashed (check /workspace/logs/forge.log)${NC}"
    echo -e "   ${YELLOW}   3. Wrong template (use 'Stable Diffusion WebUI Forge' template)${NC}"
    echo ""
    echo -e "   ${CYAN}💡 Try this: wait 3-5 minutes after pod starts, then run the script again${NC}"
    exit 1
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
# RESTORE BACKUP (IF PRESET USED)
# ==============================================================================
if [ -n "$PRESET" ] && [ -f "$WORK_DIR/config/.env.backup" ]; then
    echo ""
    echo -e "${BLUE}🔄 Restoring original .env configuration...${NC}"
    mv "$WORK_DIR/config/.env.backup" "$WORK_DIR/config/.env"
    echo -e "   ${GREEN}✅ Configuration restored${NC}"
fi

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


