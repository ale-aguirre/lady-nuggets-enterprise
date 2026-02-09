import os
import random
import requests
import json
import base64
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# OPTIONAL: Google GenAI (Fails on some RunPod envs due to httplib2/pyparsing conflicts)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini SDK not available (Dependency conflict). Gemini will be disabled.")
except Exception:
    genai = None
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini SDK error. Gemini will be disabled.")

# LOAD ENV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

# CONFIG
REFORGE_API = os.getenv("REFORGE_API", "http://127.0.0.1:7861")
GEMINI_KEY = os.getenv("GEMINI_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")
OUTPUT_DIR = os.path.join(BASE_DIR, "content", "raw")
THEMES_FILE = os.path.join(BASE_DIR, "config", "themes.txt")

# === LADY NUGGETS OC PROMPT (V9: High Quality) ===
OC_PROMPT = "(masterpiece:1.3), (best quality:1.3), (EyesHD:1.2), (4k,8k,Ultra HD), ultra-detailed, sharp focus, ray tracing, best lighting, cinematic lighting, 1girl, solo, full body, centered composition, looking at viewer, (very long black hair:1.4), large purple eyes, soft black eyeliner, makeup shadows, glossy lips, subtle blush, mole on chin, bright pupils, narrow waist, wide hips, cute, sexually suggestive, naughty face, wavy hair, (thick black cat tail, long tail, black cat ears), dynamic pose"

# === NEGATIVE PROMPT ===
NEGATIVE_PROMPT = "anatomical nonsense, interlocked fingers, extra fingers, watermark, simple background, transparent, low quality, logo, text, signature, (worst quality, bad quality:1.2), jpeg artifacts, username, censored, extra digit, ugly, bad_hands, bad_feet, bad_anatomy, deformed anatomy, lowres, bad_quality, robotic ears, robotic tail, furry"

# === LO-RA ACTIVATION ===
# Valid LoRAs: LadyNuggets (Available)
LORA_BLOCK = "<lora:LadyNuggets:0.6>"

# ... (Prompt Instructions) ...

def call_reforge_api(prompt):
    # SETTINGS
    HIRES_FIX = True
    ADETAILER = True
    
    print(f"🎨 Generating Image... [Hires: {'ON' if HIRES_FIX else 'OFF'}] [Adetailer: {'ON' if ADETAILER else 'OFF'}] [HD: 4x Anime6B@1.5]")

    # === DYNAMIC MODEL SELECTION ===
    model_payload = {"sd_model_checkpoint": "oneObsession_v19Atypical.safetensors"} # Default
    try:
        models_resp = requests.get(f"{REFORGE_API}/sdapi/v1/sd-models")
        if models_resp.status_code == 200:
            all_models = models_resp.json()
            # Look for OneObsession
            target_model = next((m['title'] for m in all_models if "oneobsession" in m['title'].lower()), None)
            # Fallback to any anime model if not found
            if not target_model:
                    target_model = next((m['title'] for m in all_models if "anime" in m['title'].lower()), None)
            
            if target_model:
                print(f"🎯 Switching Model to: {target_model}")
                model_payload = {"sd_model_checkpoint": target_model}
    except:
        pass

    # === PAYLOAD DEFINITION ===
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 28,
        "cfg_scale": 6.0,
        "width": 512,  # CORRECT FOR SD1.5
        "height": 768, # CORRECT FOR SD1.5
        "sampler_name": "Euler a",
        "batch_size": 1,
        
        # === SETTINGS OVERRIDE ===
        "override_settings": {
            **model_payload,
            "CLIP_stop_at_last_layers": 2
        },

        # === HIRES FIX (Enabled for V9) ===
        "enable_hr": HIRES_FIX,
        "hr_scale": 2.0, # Upscale to 1024x1536
        "hr_upscaler": "R-ESRGAN 4x+ Anime6B",
        "denoising_strength": 0.35,
        "hr_second_pass_steps": 15,
        
        "alwayson_scripts": {
            "ADetailer": {
                "args": [{
                    "ad_model": "face_yolov8n.pt",
                    "ad_confidence": 0.3, 
                    "ad_denoising_strength": 0.35
                }]
            } if ADETAILER else {}
        }
    }
    
    print("\n📜 [DEBUG] Final Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(f"{REFORGE_API}/sdapi/v1/txt2img", json=payload)
        if response.status_code == 200:
            print("✅ Generation Successful!")
            return response.json()
        else:
            print(f"❌ Generation Failed: {response.status_code}")
            try:
                print(f"   Response Body: {response.text}") # Show me user why!
            except: 
                pass
            return None
    except Exception as e:
        print(f"❌ API Connection Error: {e}")
        return None

def save_image(data, prompt):
    if not data or 'images' not in data:
        return
        
    for i, img_str in enumerate(data['images']):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_{timestamp}_{i}.png"
        path = os.path.join(OUTPUT_DIR, filename)
        
        with open(path, "wb") as f:
            f.write(base64.b64decode(img_str))
            
        meta = {"prompt": prompt, "timestamp": timestamp}
        with open(path.replace(".png", ".json"), "w") as f:
            json.dump(meta, f, indent=2)
            
        print(f"💾 Saved to Disk: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Lady Nuggets Factory V9")
    parser.add_argument("--count", type=int, default=1, help="Number of images to generate")
    parser.add_argument("--output", type=str, default=None, help="Custom output directory")
    args = parser.parse_args()

    # Determine Output Directory
    global OUTPUT_DIR
    if args.output:
        OUTPUT_DIR = os.path.join(BASE_DIR, args.output)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # LOG SERVER STATE
    log_server_state()

    themes = load_themes()
    print(f"✨ Factory V9: Lady Nuggets Ultimate (Target: {args.count} images)")
    print(f"📂 Output Directory: {OUTPUT_DIR}")
    
    if not themes:
        print("Please add themes to themes.txt")
        return

    for i in range(args.count):
        theme = random.choice(themes)
        print(f"\n[{i+1}/{args.count}] Theme: '{theme}'...")
        
        full_prompt = get_ai_prompt(theme)
        print(f"🏷️  Full Prompt: {full_prompt[:80]}...") 
        
        data = call_reforge_api(full_prompt)
        save_image(data, full_prompt)
        time.sleep(1)

if __name__ == "__main__":
    main()
