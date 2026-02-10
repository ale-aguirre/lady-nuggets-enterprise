#!/bin/bash

# Configuration
REFORGE_PATH="/Users/alexisaguirre/Downloads/Lady/stable-diffusion-webui-reforge"

echo "💜 Launching Stable Diffusion ReForge (API Mode)..."
echo "📂 Path: $REFORGE_PATH"

cd "$REFORGE_PATH"

# Check if environment is reachable
if [ -f "webui.sh" ]; then
    # Launch with API enabled
    ./webui.sh --api --listen --nowebui
else
    echo "❌ Error: webui.sh not found in $REFORGE_PATH"
    echo "Please verify the path in the script."
fi
