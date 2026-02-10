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
    
    # Try ports in order of priority (include Forge template ports)
    ports = [7860, 7861, 7862, 3000, 3001, 8080, 8188]
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
# Clean keys to prevent 401 errors from invisible whitespace/quotes
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "").strip().replace('"', '').replace("'", "")
GROQ_KEY = os.getenv("GROQ_KEY", "").strip().replace('"', '').replace("'", "")
OUTPUT_DIR = os.path.join(BASE_DIR, "content", "raw")
THEMES_FILE = os.path.join(BASE_DIR, "config", "themes.txt")

# === LADY NUGGETS CHARACTER DEFINITION ===
# Quality prefix: Illustrious tokens + detail enhancers from proven high-quality prompts
QUALITY_PREFIX = """masterpiece, best quality, amazing quality, very awa, very aesthetic, absurdres, newest, source_anime,
(EyesHD:1.2), ultra-detailed, sharp focus, detailed illustration, detailed background, beautiful face, beautiful eyes"""

# Artist mix (dramatically improves aesthetic quality)
# Rotate different artist combos per generation for variety
import random
ARTIST_MIXES = [
    "(mika pikazo:0.8), (yoneyama mai:0.6), (wlop:0.5)",
    "(rella:1.0), (redum4:0.8), (wlop:0.6)",
    "(artist:quasarcake:0.8), (wlop:0.6), (by kukka:0.5)",
    "(mika pikazo:0.7), (kkia:0.6), (z3zz4:0.5)",
    "(rella:0.8), (mika pikazo:0.6), (yoneyama mai:0.5)",
]

# Quality suffix (goes at end of prompt - proven high-impact tags)
QUALITY_SUFFIX = """depth of field, highres, high detail, subtle, high contrast, colorful depth,
chiaroscuro, impasto, (shallow depth of field:1.4), cinematic lighting"""

# Character definition (body only, no quality tags)
OC_CHARACTER = """1girl, solo, full body, centered composition, looking at viewer, 
(very long black hair:1.4), large purple eyes, soft black eyeliner, makeup shadows, glossy lips, subtle blush, mole on chin, bright pupils, 
narrow waist, wide hips, cute, sexually suggestive, naughty face, wavy hair, 
(thick black cat tail, long tail, black cat ears)"""

# Random anime characters for variety (used by default now)
RANDOM_CHARACTERS = [
    "makima \\(chainsaw man\\), 1girl, solo, red hair, ringed eyes, yellow eyes, braided ponytail, business suit",
    "yor briar \\(spy x family\\), 1girl, solo, black hair, long hair, red eyes, earrings, thorn princess",
    "power \\(chainsaw man\\), 1girl, solo, long hair, blonde hair, red horns, yellow eyes, sharp teeth, fiend",
    "nico robin \\(one piece\\), 1girl, solo, black hair, long hair, blue eyes, mature female, cowboy hat",
    "zero two \\(darling in the franxx\\), 1girl, solo, long hair, pink hair, green eyes, red horns, pilot suit",
    "rem \\(re:zero\\), 1girl, solo, blue hair, short hair, blue eyes, hair ornament, maid",
    "hinata hyuuga \\(naruto\\), 1girl, solo, long hair, dark blue hair, white eyes, byakugan, shy",
    "asuna \\(sao\\), 1girl, solo, long hair, orange hair, brown eyes, knights of blood uniform",
    "marin kitagawa \\(sono bisque doll\\), 1girl, solo, blonde hair, long hair, blue eyes, gyaru, earrings",
    "frieren \\(sousou no frieren\\), 1girl, solo, long hair, white hair, green eyes, elf, pointy ears, staff",
    "esdeath \\(akame ga kill!\\), 1girl, solo, long hair, blue hair, blue eyes, general, military uniform, hat",
    "2b \\(nier:automata\\), 1girl, solo, white hair, short hair, blindfold, black dress, thigh boots",
    "raiden shogun \\(genshin impact\\), 1girl, solo, purple hair, long braided hair, purple eyes, electro archon",
    "sailor moon \\(tsukino usagi\\), 1girl, solo, blonde hair, twintails, blue eyes, sailor uniform, tiara, magical girl",
    "hatsune miku \\(vocaloid\\), 1girl, solo, aqua hair, very long twintails, aqua eyes, headset, futuristic",
    "misato katsuragi \\(evangelion\\), 1girl, solo, purple hair, long hair, red jacket, black dress, cross necklace, beer can",
    "tifa lockhart \\(ff7\\), 1girl, solo, black hair, long hair, red eyes, white tank top, suspenders, black skirt, gloves",
    "aerith gainsborough \\(ff7\\), 1girl, solo, brown hair, long braid, green eyes, pink dress, red jacket, flowers",
    "lucy \\(cyberpunk edgerunners\\), 1girl, solo, white hair, multicolored hair, purple eyes, netrunner suit, futuristic city",
    "rebecca \\(cyberpunk edgerunners\\), 1girl, solo, green hair, twintails, red eyes, tattoo, oversized jacket, gun",
    "ahri \\(league of legends\\), 1girl, solo, fox ears, fox tail, nine tails, blonde hair, yellow eyes, hanbok, korean clothes",
    "d-va \\(overwatch\\), 1girl, solo, brown hair, brown eyes, headset, face paint, pilot suit, mech",
    "nezuko kamado \\(kimetsu no yaiba\\), 1girl, solo, black hair, orange tips, pink eyes, bamboo muzzle, kimono",
]

# Flag for random character mode (Enabled by default for variety)
USE_RANDOM_CHAR = True

# === NEGATIVE PROMPT (from proven working prompts) ===
NEGATIVE_PROMPT = """anatomical nonsense, interlocked fingers, extra fingers, watermark, simple background, transparent,
low quality, logo, text, signature, (worst quality, bad quality:1.2), jpeg artifacts, username, censored,
extra digit, ugly, bad_hands, bad_feet, bad_anatomy, deformed anatomy, bad proportions, lowres, bad_quality,
normal quality, monochrome, grayscale"""

# === LLM MODELS ===
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]

# STRICTLY FREE models on OpenRouter
# Updated Feb 2026 based on availability
OPENROUTER_MODELS = [
    "google/gemini-2.0-pro-exp-02-05:free", # Incredible quality
    "google/gemini-2.0-flash-thinking-exp:free", # Smart reasoning
    "google/gemini-2.0-flash-exp:free", # Fast
    "deepseek/deepseek-r1-distill-llama-70b:free", # Very smart
    "deepseek/deepseek-r1:free", # Often busy
    "meta-llama/llama-3.3-70b-instruct:free", # Great all-rounder
    "nvidia/llama-3.1-nemotron-70b-instruct:free", # Nvidia optimized
    "qwen/qwen-2.5-vl-72b-instruct:free", # Vision capable
    "microsoft/phi-4:free", # Good small model
    "mistralai/mistral-7b-instruct:free", # Fallback
]

# === PROMPT ENGINEER SYSTEM ===
PROMPT_SYSTEM = """You are an expert Anime Art Director for Illustrious XL models.
Create a FOCUSED scene prompt. Quality and visual beauty are critical.

RULES:
1. OUTPUT ONLY comma-separated Danbooru tags, NO explanations
2. Keep it SIMPLE and FOCUSED: 5-8 scene tags MAXIMUM
3. Include: specific outfit (use Danbooru tags), location, ONE lighting style, ONE pose
4. DO NOT add quality tags, artist names, or character descriptions (those are added automatically)
5. Outfit MUST match theme
6. Use precise Danbooru tags (e.g., "serafuku" not "school uniform", "maid_headdress" not "maid hat")

EXAMPLES:
Theme: "Witch Academy" → black witch hat, gothic lolita dress, holding magic staff, mystical library, candlelight, mysterious smile
Theme: "Beach Day" → white bikini, sarong, sandy beach, ocean waves, sunset, playful pose, hair blowing
Theme: "Office" → pencil skirt, white blouse, sitting on desk, office background, warm lighting, crossed legs"""

# LoRA disabled by default - the LadyNuggets LoRA was causing quality issues
# To re-enable, pass --lora flag when running factory.py
USE_LORA = False

def detect_loras():
    """Detect available LoRAs from server"""
    try:
        # Refresh LoRA list first
        requests.post(f"{REFORGE_API}/sdapi/v1/refresh-loras", timeout=5)
        import time; time.sleep(1)
        
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
    """Build LoRA activation string based on available LoRAs.
    Aesthetic LoRAs: ALWAYS applied (quality boost).
    Character LoRAs: only with --lora flag.
    """
    loras = detect_loras()
    if not loras:
        log('info', "No LoRAs available on server")
        return ""
    
    lora_tags = []
    
    # Aesthetic/Quality LoRAs (always use if available)
    aesthetic_loras = {
        'aesthetic_quality': 0.5,
        'masterpiece': 0.5,
        'stabilizer': 0.4,
    }
    
    # Character LoRAs (only if --lora flag)
    character_loras = {
        'LadyNuggets': 0.6,
        'ladynuggets': 0.6,
        'lady_nuggets': 0.6,
    }
    
    for lora in loras:
        name = lora.get('name', '')
        name_lower = name.lower()
        
        # Always apply aesthetic LoRAs
        matched_aesthetic = False
        for key, weight in aesthetic_loras.items():
            if key.lower() in name_lower:
                lora_tags.append(f"<lora:{name}:{weight}>")
                log('success', f"Aesthetic LoRA: {name} @ {weight}")
                matched_aesthetic = True
                break
        
        # Character LoRAs only with --lora flag
        if not matched_aesthetic and USE_LORA:
            for key, weight in character_loras.items():
                if key.lower() in name_lower:
                    lora_tags.append(f"<lora:{name}:{weight}>")
                    log('success', f"Character LoRA: {name} @ {weight}")
                    break
    
    if not USE_LORA:
        log('info', "Character LoRA disabled (use --lora to enable)")
    
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
    
    for model in OPENROUTER_MODELS:
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
                if resp.status_code == 401:
                    try:
                        err_msg = resp.json().get('error', {}).get('message', resp.text)
                        log('warning', f"   ❌ Error details: {err_msg}")
                    except:
                        log('warning', f"   ❌ Response body: {resp.text[:200]}")
                
        except Exception as e:
            log('warning', f"[OpenRouter] {model} error: {str(e)[:50]}")
    
    return None

def get_ai_prompt(theme):
    """Get AI-generated prompt with fallback chain"""
    log('ai', f"Generating prompt for theme: '{theme}'")
    
    # Try OpenRouter first (paid, reliable)
    if OPENROUTER_KEY:
        result = call_openrouter(theme)
        if result:
            return result
    
    # Fallback to Groq (free tier, daily limits)
    if GROQ_KEY:
        result = call_groq(theme)
        if result:
            return result
    
    # Ultimate fallback — rich Danbooru-style prompts per theme
    log('warning', "All AI providers failed. Using built-in prompt library.")
    theme_prompts = {
        "Victorian Ball": "ballgown, white gloves, elbow gloves, chandelier, ballroom, dancing, candlelight, ornate architecture, gold trim, flowing dress, elegant",
        "Cyberpunk Night": "cyberpunk, neon lights, rain, wet streets, holographic, tech wear, crop top, shorts, neon hair, city skyline, night, reflections",
        "Beach Sunset": "beach, sunset, ocean, bikini, sarong, wind, golden hour, waves, palm trees, sand, standing in water, wet skin",
        "Gothic Cathedral": "gothic architecture, stained glass, dark dress, cathedral, candles, dramatic shadows, long dress, cross necklace, solemn expression",
        "Cherry Blossom": "cherry blossoms, petals falling, kimono, japanese garden, bridge, spring, pink flowers, wind, serene, traditional",
        "School Uniform": "serafuku, sailor collar, classroom, window light, school desk, pleated skirt, sitting, looking at viewer, afternoon sun",
        "Maid Cafe": "maid dress, maid headdress, frills, apron, cafe interior, tray, serving, smile, cute pose, heart hands",
        "Fitness Gym": "sports bra, bike shorts, gym, dumbbells, sweat, ponytail, toned body, mirror, determined expression, athletic",
        "Library Study": "glasses, sweater, bookshelf, reading, warm lighting, cozy, sitting, books, concentrated, library interior",
        "Rain Walk": "umbrella, rain, wet hair, puddles, city street, transparent umbrella, coat, boots, reflection, moody lighting",
        "Witch Forest": "witch hat, magic circle, glowing, dark forest, cape, staff, moonlight, mystical, floating particles, spell casting",
        "Space Station": "spacesuit, holographic display, zero gravity, stars, space station interior, futuristic, floating hair, visor",
        "Festival Night": "yukata, festival, paper lanterns, fireworks, night sky, goldfish scooping, crowd, warm lights, summer festival",
        "Royal Throne": "crown, throne room, royal dress, scepter, red carpet, gold decoration, regal pose, cape, jewels, commanding",
        "Underwater": "underwater, bubbles, flowing hair, mermaid tail, coral reef, sunlight rays, fish, ocean blue, serene, floating",
        "Concert Stage": "idol, stage lights, microphone, concert, crowd, spotlight, glowing, singing, energy, colorful lights",
        "Desert Oasis": "desert, oasis, belly dancer outfit, gold jewelry, palm trees, sunset, sand dunes, flowing fabric, exotic",
        "Snow Mountain": "winter coat, fur trim, snow, mountain peak, aurora borealis, breath visible, mittens, scarf, cold, beautiful sky",
        "Steampunk Workshop": "steampunk, goggles, gears, workshop, brass, mechanical, corset, inventor, tools, warm industrial lighting",
        "Garden Tea Party": "tea party, garden, floral dress, hat, teacup, parasol, roses, afternoon, elegant, table setting",
    }
    fallback = theme_prompts.get(theme, f"{theme}, detailed outfit, scenic background, dramatic lighting, dynamic pose, cinematic composition")
    return fallback

def get_model_info():
    """Get current model info from server. Prioritizes WAI > OneObsession > anime."""
    try:
        resp = requests.get(f"{REFORGE_API}/sdapi/v1/sd-models", timeout=5)
        if resp.status_code == 200:
            models = resp.json()
            # Priority 1: WAI-Illustrious (best anime quality)
            for m in models:
                if 'wai' in m['title'].lower() and 'illustrious' in m['title'].lower():
                    return m['title']
                if 'waiillustrious' in m['title'].lower():
                    return m['title']
            # Priority 2: OneObsession (good 2.5D)
            for m in models:
                if 'oneobsession' in m['title'].lower() or 'obsession' in m['title'].lower():
                    return m['title']
            # Priority 3: Any Illustrious-based
            for m in models:
                if 'illustrious' in m['title'].lower():
                    return m['title']
            # Priority 4: Any anime-ish model
            for m in models:
                if any(x in m['title'].lower() for x in ['anime', 'manga', 'noob']):
                    return m['title']
            # Last resort: first model
            return models[0]['title'] if models else None
    except:
        pass
    return "waiIllustriousSDXL_v160.safetensors"

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

def generate_image(prompt, negative_prompt, model_name, upscale_factor=1.5, no_hires=False):
    """Call SD API with retry logic
    Args:
        upscale_factor: 1.0 (off), 1.5 (default), 2.0, 4.0
        no_hires: If True, disable hires fix entirely
    """
    log('gen', f"Starting generation with model: {model_name}")
    
    # Detect model type for optimal params
    is_wai = 'wai' in model_name.lower()
    is_oneobs = 'obsession' in model_name.lower()
    
    # WAI: lower denoise (0.45), OneObsession: higher denoise (0.7)
    hr_denoise = 0.45 if is_wai else 0.7
    
    # === SETTINGS MATCHING PROVEN HIGH-QUALITY PROMPTS ===
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        
        # Generation settings (proven optimal for Illustrious family)
        "steps": 20,
        "cfg_scale": 5,
        "width": 832,
        "height": 1216,
        "sampler_name": "Euler a",
        "scheduler": "Karras",
        "batch_size": 1,
        
        "override_settings": {
            "sd_model_checkpoint": model_name,
            "CLIP_stop_at_last_layers": 2
        },
    }
    
    # Hires Fix
    use_hires = not no_hires and upscale_factor > 1.0
    if use_hires:
        payload.update({
            "enable_hr": True,
            "hr_scale": upscale_factor,
            "hr_upscaler": "R-ESRGAN 4x+ Anime6B",
            "denoising_strength": hr_denoise,
            "hr_second_pass_steps": 15,
            "hr_cfg_scale": 5,
        })
        final_w = int(832 * upscale_factor)
        final_h = int(1216 * upscale_factor)
        log('info', f"Hires Fix: {upscale_factor}x → {final_w}x{final_h} (denoise {hr_denoise})")
    else:
        payload["enable_hr"] = False
        log('info', "Hires Fix: DISABLED (base 832x1216)")
    
    # ADetailer: auto-detect and enable with face + hand fix
    try:
        scripts_resp = requests.get(f"{REFORGE_API}/sdapi/v1/scripts", timeout=5)
        if scripts_resp.status_code == 200:
            scripts_data = scripts_resp.json()
            available_scripts = [s.lower() for s in scripts_data.get("txt2img", [])]
            if "adetailer" in available_scripts:
                payload["alwayson_scripts"] = {
                    "ADetailer": {
                        "args": [
                            {   # Slot 1: Face fix
                                "ad_model": "face_yolov8n.pt",
                                "ad_prompt": "detailed face, beautiful eyes, perfect face",
                                "ad_negative_prompt": "ugly face, deformed face",
                                "ad_confidence": 0.3,
                                "ad_denoising_strength": 0.35
                            },
                            {   # Slot 2: Hand fix (the 6-finger killer)
                                "ad_model": "hand_yolov8n.pt",
                                "ad_prompt": "detailed hands, perfect fingers, 5 fingers",
                                "ad_negative_prompt": "extra fingers, fewer fingers, bad hands, 6 fingers",
                                "ad_confidence": 0.3,
                                "ad_denoising_strength": 0.4
                            }
                        ]
                    }
                }
                log('success', "ADetailer: face + hand fix enabled")
            else:
                log('warning', "ADetailer not installed — run: cd /workspace/stable-diffusion-webui/extensions && git clone https://github.com/Anapnoe/stable-diffusion-webui-adetailer.git adetailer")
    except:
        log('warning', "Could not check scripts endpoint")
    
    # Log payload summary
    print(f"\n{Colors.WHITE}📜 Generation Config:{Colors.END}")
    print(f"   Model: {model_name}")
    hr_info = f" → {int(832*upscale_factor)}x{int(1216*upscale_factor)} (Hires {upscale_factor}x)" if use_hires else ""
    print(f"   Size: {payload['width']}x{payload['height']}{hr_info}")
    has_ad = "alwayson_scripts" in payload and "ADetailer" in payload.get("alwayson_scripts", {})
    print(f"   ADetailer: {'✅ face+hands' if has_ad else '❌ not available'}")
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
    parser.add_argument("--lora", action="store_true", help="Enable LoRA (disabled by default)")
    parser.add_argument("--upscale", type=float, default=1.5, help="Hires upscale factor: 1.0 (off), 1.5 (default), 2.0, 4.0")
    parser.add_argument("--no-hires", action="store_true", help="Disable Hires Fix entirely")
    parser.add_argument("--oc", action="store_true", help="Force use Lady Nuggets OC instead of random characters")
    parser.add_argument("--debug", action="store_true", help="Show debug information")
    args = parser.parse_args()
    
    # Apply flags
    global USE_LORA, USE_RANDOM_CHAR
    USE_LORA = args.lora
    # Random characters are enabled by default (USE_RANDOM_CHAR = True at top)
    # Only disable if user explicitly asks for --oc
    if args.oc:
        USE_RANDOM_CHAR = False
    
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
        
        # Build full prompt with BREAK sections (proven high-quality structure)
        artist_mix = random.choice(ARTIST_MIXES)
        
        # Character selection
        if USE_RANDOM_CHAR:
            character = random.choice(RANDOM_CHARACTERS)
            char_name = character.split(",")[0].strip()
            log('info', f"Character: {char_name}")
        else:
            character = OC_CHARACTER
            log('info', "Character: Lady Nuggets OC")
        
        section1 = f"{artist_mix},\n{QUALITY_PREFIX}"
        section2 = f"{character}, {scene_prompt}"
        section3 = f"{QUALITY_SUFFIX}"
        if lora_block:
            section3 += f", {lora_block}"
        
        full_prompt = f"{section1},\nBREAK\n{section2},\nBREAK\n{section3}"
        
        log('info', f"Artists: {artist_mix}")
        
        # Generate
        result = generate_image(full_prompt, NEGATIVE_PROMPT, model_name, 
                               upscale_factor=args.upscale, no_hires=args.no_hires)
        
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
