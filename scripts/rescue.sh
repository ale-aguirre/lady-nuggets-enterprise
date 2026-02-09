#!/bin/bash
# scripts/rescue.sh
# KILLS everything and starts fresh. Use this if "Connection Refused".

echo "💀 KILLING old processes (Safely)..."
# DO NOT kill 'python' generically (kills JupyterLab)
pkill -f "launch.py"
pkill -f "webui.sh"
# Also kill standard SD processes if they have specific names
pkill -f "python3 launch.py"
sleep 2

# 1. Setup Env
export REFORGE_API="http://127.0.0.1:7860"

# FIX: Google Gemini / httplib2 dependency conflict
echo "🔧 Fixing dependencies..."
pip install "pyparsing<3" > /dev/null 2>&1

# 2. Start Server (CLEAN & DIRECT)
echo "🚀 Launching Server (Direct Python Mode)..."
cd /workspace/stable-diffusion-webui || exit

# CLEANUP ENV to prevent port 3000 conflicts
unset COMMANDLINE_ARGS

# LAUNCH DIRECTLY (Bypass webui.sh wrapper)
nohup python3 launch.py --nowebui --api --listen --port 7860 --xformers --enable-insecure-extension-access > /workspace/reforge.log 2>&1 &
SERVER_PID=$!

echo "⏳ Waiting for Server..."
for i in {1..300}; do
    # Check /docs (Swagger) or /sdapi/v1/options to get 200 OK
    if curl -s -f http://127.0.0.1:7860/docs > /dev/null; then
        echo "✅ Server is UP!"
        break
    fi
    if (( i % 5 == 0 )); then
        echo -n "."
    fi
    sleep 2
done

# 3. Generate
BATCH_ID=$(date +"%Y%m%d_%H%M%S")
BATCH_DIR="/workspace/lady-nuggets-enterprise/content/batch_${BATCH_ID}"
mkdir -p "$BATCH_DIR"

echo "🏭 Generating 10 Images..."
cd /workspace/lady-nuggets-enterprise || exit
# Export keys if they were set in terminal, otherwise fallback
python3 scripts/factory.py --count 10 --output "$BATCH_DIR"

# 4. Zip
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "📦 Zipping..."
    ZIP_NAME="lady_nuggets_${BATCH_ID}.zip"
    zip -r "$ZIP_NAME" "$BATCH_DIR"
    echo "✅ DONE: $ZIP_NAME"
else
    echo "❌ Generation Failed!"
    tail -n 20 /workspace/reforge.log
fi
