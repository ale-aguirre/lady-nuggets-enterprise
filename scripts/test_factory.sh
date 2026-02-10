#!/bin/bash

# ==============================================================================
# 🧪 LADY NUGGETS - SAFE TEST RUNNER
# ==============================================================================
# This script creates a temporary .env to test new settings WITHOUT breaking
# your main configuration.
#
# Usage: ./scripts/test_factory.sh
# ==============================================================================

echo "🧪 TEST MODE - Generating 2 images with EXPERIMENTAL settings..."
echo "   (This will NOT overwrite your main config)"

# 1. Backup current .env (Safety First)
cp config/.env config/.env.backup

# 2. Create Temporary Test Config
# EDIT THIS BLOCK TO TEST NEW SETTINGS
cat > config/.env.test << EOF
# === TEST CONFIGURATION ===
FORCE_OC=true
USE_PERFECT_HANDS=true
USE_PERFECT_EYES=true
CHARACTER_LORA_WEIGHT=0.9
REFORGE_API=http://127.0.0.1:7860
# (Copy your API keys from .env manually if needed, or source them)
EOF

# Source keys from backup so we don't lose them
grep "GROQ_KEY" config/.env.backup >> config/.env.test
grep "OPENROUTER_KEY" config/.env.backup >> config/.env.test

# 3. Run Generation with Test Config
export ENV_FILE=config/.env.test
echo ""
echo "🚀 Launching Factory with TEST config..."
python3 scripts/factory.py --count 2 --output content/test_run

# 4. Restore Original Config
mv config/.env.backup config/.env

echo ""
echo "✅ Test Complete!"
echo "   📁 Results: content/test_run/"
echo "   🛡️  Original config restored."
