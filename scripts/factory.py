import os
import random
import requests
import json
import base64
import time
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# LOAD ENV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

# CONFIG
REFORGE_API = os.getenv("REFORGE_API", "http://127.0.0.1:7861")
GEMINI_KEY = os.getenv("GEMINI_KEY")
OUTPUT_DIR = os.path.join(BASE_DIR, "content", "raw")
THEMES_FILE = os.path.join(BASE_DIR, "config", "themes.txt")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# === LADY NUGGETS OC PROMPT (V9: High Quality) ===
OC_PROMPT = """(masterpiece:1.3), (best quality:1.3), (EyesHD:1.2), (4k,8k,Ultra HD), ultra-detailed, sharp focus, ray tracing, best lighting, cinematic lighting, 
1girl, solo, full body, centered composition, looking at viewer,
(very long black hair:1.4), large purple eyes, soft black eyeliner, makeup shadows, glossy lips, subtle blush, mole on chin, bright pupils, narrow waist, wide hips, cute, sexually suggestive, naughty face, wavy hair,
(thick black cat tail, long tail, black cat ears), dynamic pose,
(style_by_ araneesama: 0.4),(style_by_ Blue-Senpai:1) (style_by_ Kurowa:0.8)"""

# === NEGATIVE PROMPT ===
NEGATIVE_PROMPT = "anatomical nonsense, interlocked fingers, extra fingers, watermark, simple background, transparent, low quality, logo, text, signature, (worst quality, bad quality:1.2), jpeg artifacts, username, censored, extra digit, ugly, bad_hands, bad_feet, bad_anatomy, deformed anatomy, bad proportions, lowres, bad_quality, robotic ears, robotic tail, furry"

# === GEMINI INSTRUCTION ===
PROMPT_ENGINEER_INSTRUCTION = """
Act as a Danbooru Scene Generator for an anime character (Lady Nuggets).
I will give you a Theme. You must output visual tags describing the OUTFIT, ACTION, and BACKGROUND.
DO NOT describe the character's base features (hair/eyes/ears) as they are already fixed.

RULES:
1. OUTPUT: "tag1, tag2, tag3..."
2. FOCUS: Outfit, Action, Background, Lighting.
3. NSFW: Allowed if implied by theme.

Theme: {theme}
"""

def load_themes():
    with open(THEMES_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_ai_prompt(theme):
    try:
        response = model.generate_content(PROMPT_ENGINEER_INSTRUCTION.format(theme=theme))
        scene_tags = response.text.strip()
        return f"{OC_PROMPT}, {scene_tags}"
    except Exception as e:
        print(f"⚠️ Gemini Error: {e}")
        return f"{OC_PROMPT}, {theme}"

def call_reforge_api(prompt):
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 28,
        "cfg_scale": 6.0,
        "width": 832,
        "height": 1216,
        "sampler_name": "Euler a",
        "batch_size": 1,
        
        # === SETTINGS OVERRIDE ===
        "override_settings": {
            "sd_model_checkpoint": "oneObsession_v19Atypical.safetensors",
            "CLIP_stop_at_last_layers": 2
        },

        # === HIRES FIX (Enabled for V9) ===
        "enable_hr": True,
        "hr_scale": 1.5,
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
            }
        }
    }
    
    try:
        response = requests.post(f"{REFORGE_API}/sdapi/v1/txt2img", json=payload)
        return response.json()
    except Exception as e:
        print(f"❌ API Error: {e}")
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
            
        print(f"✅ Saved (V9 HighRes): {filename}")

import argparse

def main():
    parser = argparse.ArgumentParser(description="Lady Nuggets Factory V9")
    parser.add_argument("--count", type=int, default=1, help="Number of images to generate")
    args = parser.parse_args()

    themes = load_themes()
    print(f"✨ Factory V9: Lady Nuggets Ultimate (Target: {args.count} images)")
    
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
