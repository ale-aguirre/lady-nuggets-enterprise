#!/bin/bash
# Scripts/pack_images.sh
# Zips the 'content/raw' folder for easy download from RunPod

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ZIP_NAME="lady_nuggets_batch_${TIMESTAMP}.zip"

echo "📦 Packing images into ${ZIP_NAME}..."
zip -r "${ZIP_NAME}" content/raw

echo "✅ Done! You can now right-click and 'Download' this file in JupyterLab."
echo "   File: ${ZIP_NAME}"
