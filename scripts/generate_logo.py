import requests
import json
import base64
import os
import time
from datetime import datetime

# === CONFIG ===
API_URL = "http://127.0.0.1:7860" # Reforge API
OUTPUT_DIR = "content/logo_concepts"

# === LOGO PARAMS ===
PROMPT = "minimalist vector logo, silhouette of anime girl with cat ears and tail, elegant pose, simple lines, monochrome, circular frame, professional brand identity, clean design, purple accent, suitable for social media profile picture, <lora:aesthetic_quality_masterpiece:0.8>"
NEGATIVE = "detailed, realistic, complex, photo, 3d, messy, text, watermark, signature, gradient, shading, (worst quality, low quality:1.4)"
STEPS = 40
CFG = 7
WIDTH = 512
HEIGHT = 512
SAMPLER = "Euler a"
MODEL = "waiIllustriousSDXL_v160.safetensors" # Or whatever makes sense, but user asked for Illustrious

def generate_logo():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    payload = {
        "prompt": PROMPT,
        "negative_prompt": NEGATIVE,
        "steps": STEPS,
        "cfg_scale": CFG,
        "width": WIDTH,
        "height": HEIGHT,
        "sampler_name": SAMPLER,
        "batch_size": 4, # Generate 4 variations
        "override_settings": {
            "sd_model_checkpoint": MODEL
        }
    }

    print(f"🎨 Generating Logo Concepts with {MODEL}...")
    try:
        resp = requests.post(f"{API_URL}/sdapi/v1/txt2img", json=payload, timeout=300)
        if resp.status_code == 200:
            data = resp.json()
            for idx, img in enumerate(data['images']):
                path = f"{OUTPUT_DIR}/logo_concept_{idx+1}.png"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(img))
                print(f"   ✅ Saved: {path}")
            
            # Upscale instructions
            print("\n🚀 NEXT STEPS (Post-Process):")
            print("1. Pick the best logo.")
            print("2. Use the 'Extras' tab in A1111/Reforge UI to Upscale (R-ESRGAN 4x+ Anime6B) to 2048x.")
            print("3. Use remove.bg (or Photoshop) to remove background.")
        else:
            print(f"❌ Error: {resp.text}")
    except Exception as e:
        print(f"❌ API Error: {e}")
        print("   (Make sure RunPod is running!)")

if __name__ == "__main__":
    generate_logo()
