#!/bin/bash
# scripts/factory_only.sh
# Run this if the server is already running!

# 1. Setup Env (Assumes you already exported these in the terminal)
# export GROQ_KEY="YOUR_KEY"
# export OPENROUTER_KEY="YOUR_KEY"
export REFORGE_API="http://127.0.0.1:7860"

# 2. Prepare Batch Folder
BATCH_ID=$(date +"%Y%m%d_%H%M%S")
BATCH_DIR="content/batch_${BATCH_ID}"
mkdir -p "$BATCH_DIR"

# 3. Generate
echo "🏭 Generating 10 Images (Batch: $BATCH_ID)..."
cd /workspace/lady-nuggets-enterprise || exit
python3 scripts/factory.py --count 10 --output "$BATCH_DIR"

# 4. Zip
echo "📦 Compressing..."
ZIP_NAME="lady_nuggets_${BATCH_ID}.zip"
zip -r "$ZIP_NAME" "$BATCH_DIR"

echo "✅ DONE! Download: $ZIP_NAME"
