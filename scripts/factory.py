import os
import random
import requests
import json
import base64
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# LOAD ENV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

# CONFIG
REFORGE_API = os.getenv("REFORGE_API", "http://127.0.0.1:7860")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")
OUTPUT_DIR = os.path.join(BASE_DIR, "content", "raw")
THEMES_FILE = os.path.join(BASE_DIR, "config", "themes.txt")

# === LADY NUGGETS OC PROMPT (V9: High Quality) ===
OC_PROMPT = "(masterpiece:1.3), (best quality:1.3), (EyesHD:1.2), (4k,8k,Ultra HD), ultra-detailed, sharp focus, ray tracing, best lighting, cinematic lighting, 1girl, solo, full body, centered composition, looking at viewer, (very long black hair:1.4), large purple eyes, soft black eyeliner, makeup shadows, glossy lips, subtle blush, mole on chin, bright pupils, narrow waist, wide hips, cute, sexually suggestive, naughty face, wavy hair, (thick black cat tail, long tail, black cat ears), dynamic pose"

# === NEGATIVE PROMPT ===
NEGATIVE_PROMPT = "anatomical nonsense, interlocked fingers, extra fingers, watermark, simple background, transparent, low quality, logo, text, signature, (worst quality, bad quality:1.2), jpeg artifacts, username, censored, extra digit, ugly, bad_hands, bad_feet, bad_anatomy, deformed anatomy, lowres, bad_quality, robotic ears, robotic tail, furry"

# === LO-RA ACTIVATION (Only Available) ===
LORA_BLOCK = "<lora:LadyNuggets:0.8>"

# === PROMPT INSTRUCTION ===
PROMPT_ENGINEER_INSTRUCTION = """
Act as a Senior Anime Art Director. Create a visually stunning prompt for an anime illustration.
Character: Lady Nuggets (Already defined).
Theme: {theme}

INSTRUCTIONS:
1. Analyze the Theme: Determine the best Outfit, Location, and Action.
2. COHERENCE: The Outfit must match the Location. The Pose must match the Action.
3. QUALITY: Use precise Danbooru tags.
4. OUTPUT FORMAT: Return a single string of comma-separated tags.

FINAL OUTPUT EXAMPLE:
"wearing gothic lolita dress, lace trim, frills, standing in rose garden, moonlight, blue roses, petals in wind, slight smile, elegant pose, soft cinematic lighting"
"""

# GROQ MODELS (Fastest)
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768"
]

# FREE MODELS (OpenRouter)
FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3-8b-instruct:free",
    "openrouter/auto"
]

def get_groq_prompt(theme):
    if not GROQ_KEY:
        return None
        
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    
    for model_name in GROQ_MODELS:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": PROMPT_ENGINEER_INSTRUCTION.format(theme=theme)}
            ],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        try:
            print(f"⚡ Groq: Trying {model_name}...")
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                if content:
                    return f"{OC_PROMPT}, {content.strip()}, {LORA_BLOCK}"
            else:
                print(f"   -> Failed ({response.status_code})")
                
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
            
    return None

def load_themes():
    with open(THEMES_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def get_ai_prompt(theme):
    # 1. Try Groq (FASTEST)
    if GROQ_KEY:
        print("⚡ AI: Attempting Groq...")
        prompt = get_groq_prompt(theme)
        if prompt:
            return prompt

    # 2. Try OpenRouter
    if OPENROUTER_KEY:
        print("🔄 AI: Attempting OpenRouter...")
        prompt = get_openrouter_prompt(theme)
        if prompt:
            return prompt
    
    # 3. Fallback
    print("❌ AI Failed. Using Fallback Prompt.")
    return f"{OC_PROMPT}, {theme}, {LORA_BLOCK}"

def log_server_state():
    print("\n🔍 [DEBUG] Server Inventory:")
    try:
        requests.post(f"{REFORGE_API}/sdapi/v1/refresh-checkpoints")
        
        m_resp = requests.get(f"{REFORGE_API}/sdapi/v1/sd-models")
        if m_resp.status_code == 200:
            models = [m['title'] for m in m_resp.json()]
            print(f"   📂 Checkpoints ({len(models)}):")
            for m in models:
                print(f"      - {m}")
        
        l_resp = requests.get(f"{REFORGE_API}/sdapi/v1/loras")
        if l_resp.status_code == 200:
            loras = [l['name'] for l in l_resp.json()]
            print(f"   🧩 LoRAs ({len(loras)}):")
            for l in loras:
                print(f"      - {l}")
    except Exception as e:
        print(f"   ⚠️ Failed to query server: {e}")

def call_reforge_api(prompt):
    # SETTINGS
    HIRES_FIX = True
    ADETAILER = True
    
    print(f"🎨 Generating... [Hires: {'ON' if HIRES_FIX else 'OFF'}] [Adetailer: {'ON' if ADETAILER else 'OFF'}]")

    # === DYNAMIC MODEL SELECTION ===
    model_payload = {"sd_model_checkpoint": "oneObsession_v19Atypical.safetensors"}
    try:
        models_resp = requests.get(f"{REFORGE_API}/sdapi/v1/sd-models")
        if models_resp.status_code == 200:
            all_models = models_resp.json()
            target_model = next((m['title'] for m in all_models if "oneobsession" in m['title'].lower()), None)
            if not target_model:
                target_model = next((m['title'] for m in all_models if "anime" in m['title'].lower()), None)
            
            if target_model:
                print(f"🎯 Using Model: {target_model}")
                model_payload = {"sd_model_checkpoint": target_model}
    except:
        pass

    # === PAYLOAD ===
    payload = {
        "prompt": prompt,
        "negative_prompt": NEGATIVE_PROMPT,
        "steps": 28,
        "cfg_scale": 6.0,
        "width": 512,   # SD1.5 Native
        "height": 768,  # SD1.5 Native
        "sampler_name": "Euler a",
        "batch_size": 1,
        
        "override_settings": {
            **model_payload,
            "CLIP_stop_at_last_layers": 2
        },

        # HIRES FIX
        "enable_hr": HIRES_FIX,
        "hr_scale": 2.0,
        "hr_upscaler": "Latent",  # ALWAYS AVAILABLE
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
    
    print("\n📜 [DEBUG] Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(f"{REFORGE_API}/sdapi/v1/txt2img", json=payload)
        if response.status_code == 200:
            print("✅ Generation Successful!")
            return response.json()
        else:
            print(f"❌ Generation Failed: {response.status_code}")
            print(f"   Body: {response.text[:500]}")
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
            
        print(f"💾 Saved: {filename}")

def main():
    parser = argparse.ArgumentParser(description="Lady Nuggets Factory V9")
    parser.add_argument("--count", type=int, default=1, help="Number of images")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    global OUTPUT_DIR
    if args.output:
        OUTPUT_DIR = os.path.join(BASE_DIR, args.output)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    log_server_state()

    themes = load_themes()
    print(f"✨ Factory V9: Target: {args.count} images")
    print(f"📂 Output: {OUTPUT_DIR}")
    
    if not themes:
        print("Please add themes to themes.txt")
        return

    for i in range(args.count):
        theme = random.choice(themes)
        print(f"\n[{i+1}/{args.count}] Theme: '{theme}'...")
        
        full_prompt = get_ai_prompt(theme)
        print(f"🏷️  Prompt: {full_prompt[:80]}...") 
        
        data = call_reforge_api(full_prompt)
        save_image(data, full_prompt)
        time.sleep(1)

if __name__ == "__main__":
    main()
