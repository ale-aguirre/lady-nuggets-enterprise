import os
import random
import requests
import json
import base64
import time
from datetime import datetime
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
NEGATIVE_PROMPT = "anatomical nonsense, interlocked fingers, extra fingers, watermark, simple background, transparent, low quality, logo, text, signature, (worst quality, bad quality:1.2), jpeg artifacts, username, censored, extra digit, ugly, bad_hands, bad_feet, bad_anatomy, deformed anatomy, bad proportions, lowres, bad_quality, robotic ears, robotic tail, furry"

# === LO-RA ACTIVATION (Indispensable) ===
# NOTE: Filenames must match what is downloaded. SD will ignore if missing.
# We assume standard filenames or user renames them.
LORA_BLOCK = "<lora:stabilizer_ilnaick:0.6> <lora:aesthetic_quality:0.8> <lora:LadyNuggets:0.6>"

# === GEMINI/GROQ INSTRUCTION (Intelligent V2) ===
PROMPT_ENGINEER_INSTRUCTION = """
Act as a Senior Anime Art Director. Your goal is to create a high-coherence, visually stunning prompt for an anime illustration.
Character: Lady Nuggets (Already defined by OC_PROMPT).
Theme: {theme}

INSTRUCTIONS:
1. Analyze the Theme: Determine the best Outfit, Location, and Action to express this theme.
2. COHERENCE: The Outfit must match the Location. The Pose must match the Action.
3. QUALITY: Use precise Danbooru tags.
4. OUTPUT FORMAT: Return a single string of comma-separated tags.

STRUCTURE YOUR "MENTAL" DRAFT (Do not output logic, only tags):
- Outfit: Detailed, textures, fashion-focused.
- Location: Atmospheric, lighting, depth.
- Pose: Dynamic, expressive.

FINAL OUTPUT EXAMPLE:
"wearing gothic lolita dress, lace trim, frills, standing in rose garden, moonlight, blue roses, petals in wind, slight smile, elegant pose, soft cinematic lighting"
"""

if GEMINI_KEY and GEMINI_AVAILABLE:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
    except:
        pass

# FREE MODELS (OpenRouter - Verified Feb 2025)
FREE_MODELS = [
    "google/gemini-2.0-flash-exp:free",      # Experimental but often free/fast
    "meta-llama/llama-3.3-70b-instruct:free", # High quality choice
    "microsoft/phi-3-medium-128k-instruct:free",
    "meta-llama/llama-3-8b-instruct:free",
    "openrouter/auto"                        # OpenRouter's auto-router for free models
]

# GROQ MODELS (Fastest - Verified Feb 2025)
GROQ_MODELS = [
    "llama-3.3-70b-versatile",  # New Flagship
    "llama-3.1-8b-instant",     # Ultra Fast
    "mixtral-8x7b-32768"        # Classic / Stable
]

def get_groq_prompt(theme):
    if not GROQ_KEY:
        return None
        
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    
    # Rotation: Try a high-quality model first, then fallback
    for model_name in GROQ_MODELS:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": PROMPT_ENGINEER_INSTRUCTION.format(theme=theme)}
            ],
            "temperature": 0.7,
            "max_tokens": 1024  # Prevent context window errors
        }
        try:
            print(f"⚡ Groq: Trying {model_name}...")
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                if content:
                    return f"{OC_PROMPT}, {content.strip()}, {LORA_BLOCK}"
            else:
                print(f"   -> Failed ({response.status_code}) Body: {response.text}")
                
        except Exception as e:
            print(f"   -> Error: {e}")
            
    return None

def get_openrouter_prompt(theme):
    if not OPENROUTER_KEY:
        return None
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ladynuggets.com", 
        "X-Title": "Lady Nuggets Factory"
    }
    
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
                    return f"{OC_PROMPT}, {content.strip()}, {LORA_BLOCK}"
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
    # 1. Try Groq (FASTEST & NEW)
    if GROQ_KEY:
        print("⚡ AI: Attempting Groq...")
        prompt = get_groq_prompt(theme)
        if prompt:
            return prompt
        print("⚠️ Groq available but failed. Switching to Backup...")

    # 2. Try OpenRouter
    if OPENROUTER_KEY:
        print("🔄 AI: Attempting OpenRouter Free Models...")
        prompt = get_openrouter_prompt(theme)
        if prompt:
            return prompt
        print("⚠️ OpenRouter failed. Switching to Gemini...")

    # 3. Try Gemini Direct
    if GEMINI_KEY:
        print("✨ AI: Using Gemini Flash (Direct)...")
        for attempt in range(3):
            try:
                response = model.generate_content(PROMPT_ENGINEER_INSTRUCTION.format(theme=theme))
                scene_tags = response.text.strip()
                return f"{OC_PROMPT}, {scene_tags}, {LORA_BLOCK}"
            except Exception as e:
                if "429" in str(e):
                    print(f"   ⚠️ Gemini Quota hit. Waiting 10s... (Attempt {attempt+1}/3)")
                    time.sleep(10)
                else:
                    print(f"   ⚠️ Gemini Error: {e}")
                    break
    
    # 4. Fallback
    print("❌ AI Failed. Using Fallback Prompt (No expansion).")
    return f"{OC_PROMPT}, {theme}"

def call_reforge_api(prompt):
    # SETTINGS
    HIRES_FIX = True
    ADETAILER = True
    
    print(f"🎨 Generating Image... [Hires: {'ON' if HIRES_FIX else 'OFF'}] [Adetailer: {'ON' if ADETAILER else 'OFF'}] [HD: 4x Anime6B]")
    
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
        "enable_hr": HIRES_FIX,
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
            } if ADETAILER else {}
        }
    }
    
    try:
        response = requests.post(f"{REFORGE_API}/sdapi/v1/txt2img", json=payload)
        if response.status_code == 200:
            print("✅ Generation Successful!")
            return response.json()
        else:
            print(f"❌ Generation Failed: {response.status_code}")
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

import argparse

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
