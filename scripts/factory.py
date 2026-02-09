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
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OUTPUT_DIR = os.path.join(BASE_DIR, "content", "raw")
THEMES_FILE = os.path.join(BASE_DIR, "config", "themes.txt")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

# FREE MODELS (OpenRouter)
FREE_MODELS = [
    "meta-llama/llama-3-8b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "openchat/openchat-7b:free",
    "huggingfaceh4/zephyr-7b-beta:free"
]

def get_openrouter_prompt(theme):
    if not OPENROUTER_KEY:
        return None
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ladynuggets.com", # Required by OpenRouter
        "X-Title": "Lady Nuggets Factory"
    }
    
    # Try different free models until one works
    for model_name in FREE_MODELS:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": PROMPT_ENGINEER_INSTRUCTION.format(theme=theme)}
            ]
        }
        try:
            print(f"🤖 OpenRouter: Trying {model_name}...")
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                if content:
                    return f"{OC_PROMPT}, {content.strip()}"
            else:
                print(f"   -> Failed ({response.status_code})")
                
        except Exception as e:
            print(f"   -> Error: {e}")
            
    print("⚠️ OpenRouter: All free models failed.")
    return None

def load_themes():
    with open(THEMES_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_ai_prompt(theme):
    # 1. Try OpenRouter (Priority if Key exists)
    if OPENROUTER_KEY:
        prompt = get_openrouter_prompt(theme)
        if prompt:
            return prompt

    # 2. Try Gemini Direct (Legacy/Backup)
    if GEMINI_KEY:
        for attempt in range(3):
            try:
                response = model.generate_content(PROMPT_ENGINEER_INSTRUCTION.format(theme=theme))
                scene_tags = response.text.strip()
                return f"{OC_PROMPT}, {scene_tags}"
            except Exception as e:
                if "429" in str(e):
                    print(f"⚠️ Quota hit. Waiting 10s... (Attempt {attempt+1}/3)")
                    time.sleep(10)
                else:
                    print(f"⚠️ Gemini Error: {e}")
                    break
    
    # 3. Fallback
    print("⚠️ Using Fallback Prompt (No AI Expansion)")
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
