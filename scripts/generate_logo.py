import requests
import json
import base64
import os
import time
from datetime import datetime

# === CONFIG ===
# === CONFIG ===
def detect_sd_api():
    """Dynamically detect SD API port (7860, 7861, 7862, 3000)."""
    env_api = os.getenv("REFORGE_API", "")
    ports = [7860, 7861, 7862, 3000, 3001, 8080, 8188]
    for port in ports:
        try:
            url = f"http://127.0.0.1:{port}"
            resp = requests.get(f"{url}/sdapi/v1/sd-models", timeout=2)
            if resp.status_code == 200:
                print(f"✅ Found SD API at: {url}")
                return url
        except:
            pass
    
    if env_api: return env_api
    return "http://127.0.0.1:7860"

API_URL = detect_sd_api()
OUTPUT_DIR = "content/logo_concepts"

# === LOGO PARAMS ===
PROMPT = "minimalist vector logo, silhouette of anime girl with cat ears and tail, elegant pose, simple lines, monochrome, circular frame, professional brand identity, clean design, purple accent, suitable for social media profile picture, <lora:aesthetic_quality_masterpiece:0.8>"
NEGATIVE = "detailed, realistic, complex, photo, 3d, messy, text, watermark, signature, gradient, shading, (worst quality, low quality:1.4)"
STEPS = 40
CFG = 7
WIDTH = 512
HEIGHT = 512
SAMPLER = "Euler a"
MODEL = "waiIllustriousSDXL_v160.safetensors"

def generate_logo():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"🎨 Generating Logo Concepts with {MODEL}...")
    print(f"   Target API: {API_URL}")
    
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

    try:
        resp = requests.post(f"{API_URL}/sdapi/v1/txt2img", json=payload, timeout=300)
        if resp.status_code == 200:
            data = resp.json()
            if 'images' not in data:
                print("❌ Error: No images returned from API.")
                return

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
            print(f"❌ Error: {resp.status_code} - {resp.text}")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION REFUSED to {API_URL}")
        print("   👉 CAUSE: The Stable Diffusion WebUI is NOT running.")
        print("   👉 FIX: Run './scripts/runpod_ultra.sh --count 1' first to start the server.")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    generate_logo()
