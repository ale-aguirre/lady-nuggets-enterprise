#!/usr/bin/env python3
"""
🏭 LADY NUGGETS FACTORY V10 - PRODUCTION READY
================================================
Generates AI-enhanced images using Stable Diffusion with intelligent prompting.

Features:
- Multi-LLM support (Groq → OpenRouter fallback)
- Detailed logging with colors
- Robust error handling with retries
- LoRA auto-detection
"""

import os
import random
import requests
import json
import base64
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# === LOAD ENV ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

# === COLORS FOR TERMINAL ===
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(level, msg):
    """Colored logging"""
    icons = {
        'info': f"{Colors.BLUE}ℹ️ ",
        'success': f"{Colors.GREEN}✅",
        'warning': f"{Colors.YELLOW}⚠️ ",
        'error': f"{Colors.RED}❌",
        'debug': f"{Colors.CYAN}🔍",
        'ai': f"{Colors.CYAN}🤖",
        'gen': f"{Colors.GREEN}🎨",
    }
    icon = icons.get(level, "")
    print(f"{icon} {msg}{Colors.END}")

# === CONFIG ===
def detect_sd_api():
    """Dynamically detect SD API port (7860, 7861, 7862).
    Validates response is real SD API (JSON), not nginx proxy (HTML 405)."""
    env_api = os.getenv("REFORGE_API", "")
    
    # Try ports in order of priority
    ports = [7860, 7861, 7862]
    for port in ports:
        try:
            url = f"http://127.0.0.1:{port}"
            resp = requests.get(f"{url}/sdapi/v1/sd-models", timeout=3)
            if resp.status_code == 200:
                # Verify it's actual JSON from SD API, not nginx HTML
                try:
                    data = resp.json()
                    if isinstance(data, list):
                        log('success', f"SD API verified on port {port} ({len(data)} models)")
                        return url
                except (ValueError, TypeError):
                    log('warning', f"Port {port} responded but not valid SD API (nginx proxy?)")
                    continue
        except:
            pass
    
    # Fallback to env or default
    if env_api:
        log('warning', f"No active SD API found, using .env: {env_api}")
        return env_api
    log('warning', "No SD API found, defaulting to port 7860")
    return "http://127.0.0.1:7860"

REFORGE_API = detect_sd_api()
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")
OUTPUT_DIR = os.path.join(BASE_DIR, "content", "raw")
THEMES_FILE = os.path.join(BASE_DIR, "config", "themes.txt")

# === LADY NUGGETS CHARACTER DEFINITION ===
# Using author-recommended quality tags for OneObsession
OC_BASE = """masterpiece, best quality, amazing quality, very aesthetic, absurdres, newest, depth of field, highres,
1girl, solo, full body, centered composition, looking at viewer, 
(very long black hair:1.4), large purple eyes, soft black eyeliner, makeup shadows, glossy lips, subtle blush, mole on chin, bright pupils, 
narrow waist, wide hips, cute, sexually suggestive, naughty face, wavy hair, 
(thick black cat tail, long tail, black cat ears), dynamic pose"""

# === NEGATIVE PROMPT (Author Recommended) ===
NEGATIVE_PROMPT = """worst quality, normal quality, anatomical nonsense, bad anatomy, interlocked fingers, extra fingers, 
watermark, simple background, transparent, low quality, logo, text, signature, 
face backlighting, backlighting, extra limbs, missing limbs, bad_hands, bad_feet, ugly, deformed"""

# === LLM MODELS ===
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]

OPENROUTER_FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2-7b-instruct:free",
]

# === PROMPT ENGINEER SYSTEM ===
PROMPT_SYSTEM = """You are an expert Anime Art Director specialized in Danbooru-style prompts for Stable Diffusion.
Your task is to create a scene prompt based on the given theme.

RULES:
1. OUTPUT ONLY comma-separated tags, NO explanations
2. Include: outfit details, location, lighting, pose, expression
3. Use precise Danbooru tags (e.g., "serafuku", not "school uniform")
4. Outfit MUST match location (e.g., swimsuit for beach, not formal dress)
5. Keep under 100 words

EXAMPLES:
Theme: "Witch Academy" → wearing black witch hat, gothic lolita dress, holding magic staff, standing in mystical library, ancient tomes, candlelight, mysterious smile, elegant pose
Theme: "Beach Day" → wearing white bikini, sarong, standing on sandy beach, ocean waves, sunset lighting, playful pose, hair blowing in wind, holding sun hat"""

def detect_loras():
    """Detect available LoRAs from server"""
    try:
        resp = requests.get(f"{REFORGE_API}/sdapi/v1/loras", timeout=5)
        if resp.status_code == 200:
            loras = resp.json()
            log('debug', f"Found {len(loras)} LoRAs: {[l['name'] for l in loras]}")
            return loras
        return []
    except Exception as e:
        log('warning', f"Could not fetch LoRAs: {e}")
        return []

def build_lora_block():
    """Build LoRA activation string based on available LoRAs"""
    loras = detect_loras()
    lora_tags = []
    
    # Priority LoRAs
    priority_loras = {
        'LadyNuggets': 0.8,
        'ladynuggets': 0.8,
        'lady_nuggets': 0.8,
    }
    
    for lora in loras:
        name = lora.get('name', '')
        for key, weight in priority_loras.items():
            if key.lower() in name.lower():
                lora_tags.append(f"<lora:{name}:{weight}>")
                log('success', f"LoRA activated: {name} @ {weight}")
                break
    
    return ", ".join(lora_tags) if lora_tags else ""

def call_groq(theme):
    """Call Groq API for prompt generation"""
    if not GROQ_KEY:
        return None
    
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    
    for model in GROQ_MODELS:
        log('ai', f"[Groq] Trying {model}...")
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": PROMPT_SYSTEM},
                    {"role": "user", "content": f"Create a prompt for theme: {theme}"}
                ],
                "temperature": 0.7,
                "max_tokens": 256
            }
            
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content'].strip()
                # Clean up response (remove quotes, explanations)
                content = content.strip('"\'')
                if '\n' in content:
                    content = content.split('\n')[0]  # Take first line only
                log('success', f"[Groq] {model} responded!")
                return content
            else:
                log('warning', f"[Groq] {model} failed: {resp.status_code}")
                
        except Exception as e:
            log('warning', f"[Groq] {model} error: {str(e)[:50]}")
    
    return None

def call_openrouter(theme):
    """Call OpenRouter API for prompt generation"""
    if not OPENROUTER_KEY:
        return None
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ladynuggets.com",
        "X-Title": "Lady Nuggets Factory"
    }
    
    for model in OPENROUTER_FREE_MODELS:
        log('ai', f"[OpenRouter] Trying {model}...")
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": PROMPT_SYSTEM},
                    {"role": "user", "content": f"Create a prompt for theme: {theme}"}
                ],
                "max_tokens": 256
            }
            
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=20
            )
            
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content'].strip()
                content = content.strip('"\'')
                if '\n' in content:
                    content = content.split('\n')[0]
                log('success', f"[OpenRouter] {model} responded!")
                return content
            else:
                log('warning', f"[OpenRouter] {model} failed: {resp.status_code}")
                
        except Exception as e:
            log('warning', f"[OpenRouter] {model} error: {str(e)[:50]}")
    
    return None

def get_ai_prompt(theme):
    """Get AI-generated prompt with fallback chain"""
    log('ai', f"Generating prompt for theme: '{theme}'")
    
    # Try Groq first (fastest)
    if GROQ_KEY:
        result = call_groq(theme)
        if result:
            return result
    
    # Fallback to OpenRouter
    if OPENROUTER_KEY:
        result = call_openrouter(theme)
        if result:
            return result
    
    # Ultimate fallback
    log('warning', "All AI providers failed. Using basic prompt.")
    return f"{theme}, detailed background, dramatic lighting, dynamic pose"

def get_model_info():
    """Get current model info from server"""
    try:
        resp = requests.get(f"{REFORGE_API}/sdapi/v1/sd-models", timeout=5)
        if resp.status_code == 200:
            models = resp.json()
            # Find our preferred model
            for m in models:
                if 'oneobsession' in m['title'].lower():
                    return m['title']
                if 'obsession' in m['title'].lower():
                    return m['title']
            # Fallback to first anime-ish model
            for m in models:
                if any(x in m['title'].lower() for x in ['anime', 'manga', 'pony']):
                    return m['title']
            # Last resort: first model
            return models[0]['title'] if models else None
    except:
        pass
    return "oneObsession_v19Atypical.safetensors"

def log_server_state():
    """Log current server inventory"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    log('debug', "Server Inventory:")
    
    try:
        # Refresh models
        requests.post(f"{REFORGE_API}/sdapi/v1/refresh-checkpoints", timeout=5)
        
        # List models
        resp = requests.get(f"{REFORGE_API}/sdapi/v1/sd-models", timeout=5)
        if resp.status_code == 200:
            models = [m['title'] for m in resp.json()]
            print(f"   {Colors.WHITE}📂 Checkpoints ({len(models)}):{Colors.END}")
            for m in models:
                print(f"      - {m}")
        
        # List LoRAs
        resp = requests.get(f"{REFORGE_API}/sdapi/v1/loras", timeout=5)
        if resp.status_code == 200:
            loras = [l['name'] for l in resp.json()]
            print(f"   {Colors.WHITE}🧩 LoRAs ({len(loras)}):{Colors.END}")
            for l in loras:
                print(f"      - {l}")
                
    except Exception as e:
        log('error', f"Failed to query server: {e}")
    
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

def generate_image(prompt, negative_prompt, model_name):
    """Call SD API with retry logic"""
    log('gen', f"Starting generation with model: {model_name}")
    
    # === OPTIMIZED FOR OneObsession v19 (Per Author Recommendations) ===
    # Source: https://civitai.com/models/1318945/one-obsession
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        
        # Author recommended settings
        "steps": 30,                    # Author recommends 25-35
        "cfg_scale": 5.0,               # Author recommends 3-6 (NOT higher!)
        "width": 832,                   # Author recommended: 832x1216
        "height": 1216,                 # Optimal for this model
        "sampler_name": "Euler a",      # Author specifically recommends Euler a
        "batch_size": 1,
        
        "override_settings": {
            "sd_model_checkpoint": model_name,
            "CLIP_stop_at_last_layers": 2
        },
        
        # Hires Fix (2x upscale = 1664x2432 final)
        "enable_hr": True,
        "hr_scale": 2.0,
        "hr_upscaler": "Latent",         # Latent works well with this model
        "denoising_strength": 0.35,      # Lower = preserve more detail
        "hr_second_pass_steps": 15,
        
        # ADetailer for face enhancement
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
    
    # Log payload summary
    print(f"\n{Colors.WHITE}📜 Generation Config:{Colors.END}")
    print(f"   Model: {model_name}")
    print(f"   Size: {payload['width']}x{payload['height']} → {int(payload['width']*2)}x{int(payload['height']*2)} (Hires)")
    print(f"   Steps: {payload['steps']} + {payload['hr_second_pass_steps']} (Hires)")
    print(f"   Prompt: {prompt[:80]}...")
    
    # Retry logic
    max_retries = 2
    for attempt in range(max_retries):
        try:
            log('info', f"Attempt {attempt + 1}/{max_retries}...")
            resp = requests.post(
                f"{REFORGE_API}/sdapi/v1/txt2img",
                json=payload,
                timeout=300  # 5 min timeout for generation
            )
            
            if resp.status_code == 200:
                log('success', "Generation complete!")
                return resp.json()
            else:
                error_body = resp.text[:200]
                log('error', f"Generation failed ({resp.status_code}): {error_body}")
                
                # Check for model error
                if 'SafetensorError' in error_body:
                    log('error', "Model file is corrupted! Please re-download.")
                    return None
                    
        except requests.exceptions.Timeout:
            log('warning', "Request timed out, retrying...")
        except Exception as e:
            log('error', f"Request error: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2)
    
    return None

def save_image(data, prompt, output_dir):
    """Save generated image and metadata"""
    if not data or 'images' not in data:
        return 0
    
    saved = 0
    for i, img_str in enumerate(data['images']):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lady_nuggets_{timestamp}_{i}.png"
        path = os.path.join(output_dir, filename)
        
        with open(path, "wb") as f:
            f.write(base64.b64decode(img_str))
        
        # Save metadata
        meta = {
            "prompt": prompt,
            "timestamp": timestamp,
            "model": "oneObsession_v19"
        }
        with open(path.replace(".png", ".json"), "w") as f:
            json.dump(meta, f, indent=2)
        
        log('success', f"Saved: {filename}")
        saved += 1
    
    return saved

def load_themes():
    """Load themes from file"""
    try:
        with open(THEMES_FILE, "r") as f:
            themes = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return themes
    except FileNotFoundError:
        log('warning', f"Themes file not found: {THEMES_FILE}")
        return ["Fantasy Princess", "Cyber Punk", "Beach Day", "Gothic Lolita"]

def main():
    parser = argparse.ArgumentParser(description="Lady Nuggets Factory V10")
    parser.add_argument("--count", type=int, default=1, help="Number of images to generate")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--theme", type=str, default=None, help="Specific theme to use")
    parser.add_argument("--debug", action="store_true", help="Show debug information")
    args = parser.parse_args()
    
    # Setup output directory
    output_dir = args.output if args.output else OUTPUT_DIR
    if not output_dir.startswith('/'):
        output_dir = os.path.join(BASE_DIR, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Banner
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}🏭 LADY NUGGETS FACTORY V10{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"   Target: {args.count} images")
    print(f"   Output: {output_dir}")
    print(f"   API: {REFORGE_API}")
    
    # Check API keys
    print(f"\n{Colors.WHITE}🔑 API Keys:{Colors.END}")
    if GROQ_KEY:
        print(f"   {Colors.GREEN}✓{Colors.END} Groq: {GROQ_KEY[:15]}...")
    else:
        print(f"   {Colors.YELLOW}✗{Colors.END} Groq: Not configured")
    
    if OPENROUTER_KEY:
        print(f"   {Colors.GREEN}✓{Colors.END} OpenRouter: {OPENROUTER_KEY[:15]}...")
    else:
        print(f"   {Colors.YELLOW}✗{Colors.END} OpenRouter: Not configured")
    
    # Log server state
    log_server_state()
    
    # Get model and LoRAs
    model_name = get_model_info()
    lora_block = build_lora_block()
    
    log('info', f"Using model: {model_name}")
    
    # Load themes
    themes = load_themes()
    log('info', f"Loaded {len(themes)} themes")
    
    # Generation loop
    total_saved = 0
    for i in range(args.count):
        print(f"\n{Colors.BOLD}[{i+1}/{args.count}]{Colors.END}")
        
        # Select theme
        theme = args.theme if args.theme else random.choice(themes)
        log('info', f"Theme: {theme}")
        
        # Get AI-generated scene prompt
        scene_prompt = get_ai_prompt(theme)
        
        # Build full prompt
        full_prompt = f"{OC_BASE}, {scene_prompt}"
        if lora_block:
            full_prompt += f", {lora_block}"
        
        # Generate
        result = generate_image(full_prompt, NEGATIVE_PROMPT, model_name)
        
        # Save
        if result:
            saved = save_image(result, full_prompt, output_dir)
            total_saved += saved
        
        # Small delay between generations
        if i < args.count - 1:
            time.sleep(1)
    
    # Summary
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}✅ GENERATION COMPLETE{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"   Images saved: {total_saved}/{args.count}")
    print(f"   Location: {output_dir}")
    print()

if __name__ == "__main__":
    main()
