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
# Quality prefix: User's Golden Formula (from Civitai proven prompts)
import random
QUALITY_PREFIX = """masterpiece,best quality,amazing quality,very aesthetic,absurdres,newest,highres,
ultra-detailed,sharp focus,ray tracing,best lighting,detailed illustration,beautiful face,beautiful eyes"""

# Artist mixes: User's exact golden mixes from their best generations
ARTIST_MIXES = [
    "(yoneyama mai:1.16),(artist ciloranko:1.05),zhibuji loom,(fuzichoco:0.86),(rella:1.1),(konya karasue:1.1),(hagimorijia:1.05),wlop",
    "(yoneyama mai:1.16),(artist ciloranko:1.05),(rella:1.1),liuyin,wlop",
    "(rella:1.1),(mika pikazo:0.8),(yoneyama mai:0.9),wlop,(fuzichoco:0.7)",
    "(rella:1.0),(redum4:0.8),(wlop:0.6),(konya karasue:0.8)",
]

# Quality suffix: User's proven high-impact tags (lazypos, impasto, foreshortening)
QUALITY_SUFFIX = """high detail,subtle,high contrast,colorful depth,
chiaroscuro,impasto,(shallow depth of field:1.4),(foreshortening:1.4),
depth of field,cinematic lighting,ambient occlusion,soft lighting"""

# Character definition (body only, no quality tags)
OC_CHARACTER = """1girl, solo, full body, centered composition, looking at viewer, 
(very long black hair:1.4), large purple eyes, soft black eyeliner, makeup shadows, glossy lips, subtle blush, mole on chin, bright pupils, 
narrow waist, wide hips, cute, sexually suggestive, naughty face, wavy hair, 
(thick black cat tail, long tail, black cat ears)"""



# === CHARACTERS & SCENES (Pinup / Ecchi / Spicy) ===
RANDOM_CHARACTERS = [
    # -- SPICY PINUP SCENARIOS --
    "1girl, lying on bed, white sheets, messy hair, looking at viewer, blush, suggestive, bedroom, morning light, (pulling own clothes:1.4), (groin:1.2), panties",
    "1girl, pink open shirt, collared shirt, black bra, denim shorts, open fly, lace-trimmed panties, breast press, looking at viewer, blush, bedroom",
    "1girl, onsen, steam, wet hair, blushing, looking at viewer, towel, japanese bath, naked, wet skin, droplets",
    "1girl, beach, swimsuit, wet skin, lens flare, ocean background, tying hair, cleavage, navel, shiny skin",
    "1girl, gym wear, sweat, ponytail, drinking water, fitness center, mirror selfie, yoga pants, cameltoe, tight clothes",
    "1girl, selfiestick, holding phone, duck face, cleavage, crop top, navel, mirror, flash",
    "1girl, from behind, ass focus, looking back, panties, skirt lift, suggestive, blush, detailed skin",
    
    # -- POPULAR WAIFUS (Pinup Verify) --
    "furina \(genshin impact\), 1girl, solo, nightgown, bedroom, holding pillow, cute, thighs, bare legs",
    "kafka \(honkai: star rail\), 1girl, solo, office lady, glasses, sitting on desk, crossing legs, teasing smile, black pantyhose, heels",
    "black swan \(honkai: star rail\), 1girl, solo, purple dress, tarot cards, mystical atmosphere, simple background, cleavage",
    "jinx \(league of legends\), 1girl, solo, underwear, messy room, graffiti, eating snacks, relaxed, tattoos, pale skin",
    "ahri \(league of legends\), 1girl, solo, kda all out, backstage, mirror, brushing tail, cleavage, corset",
    "yor briar \(spy x family\), 1girl, solo, sweater, casual clothes, kitchen, cooking, blushing, happy, apron",
    "makima \(chainsaw man\), 1girl, solo, white shirt, tie, smoking, balcony, city lights, melancholic, office lady",
    "2b \(nier:automata\), 1girl, solo, white dress (optional), field of flowers, taking off blindfold, beautiful eyes, thighs",
    "tifa lockhart \(ff7\), 1girl, solo, barmaid uniform, wiping counter, 7th heaven, smiling, warm lighting, cleavage, suspenders",
    "marin kitagawa \(sono bisque doll\), 1girl, solo, bikini, beach, laughing, gyaru, peace sign, cleavage, tongue out",
]

# Flag for random character mode
USE_RANDOM_CHAR = True

# === NEGATIVE PROMPT (User's Proven Formula) ===
NEGATIVE_PROMPT = """anatomical nonsense,interlocked fingers,extra fingers,watermark,transparent,
low quality,logo,text,signature,(worst quality, bad quality:1.2),jpeg artifacts,username,censored,
extra digit,ugly,bad_hands,bad_feet,bad_anatomy,deformed anatomy,bad proportions,lowres,bad_quality,
worst_quality,bad_detail,poorly_detailed,deformed hands,missing finger,muscular woman"""

# === LLM MODELS ===
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]

# STRICTLY FREE models on OpenRouter
# DeepSeek R1 EXCLUSIVE - We only want the best reasoning
OPENROUTER_MODELS = [
    "tngtech/deepseek-r1t2-chimera:free",  # User requested variant
    "arcee-ai/trinity-large-preview:free", # Reliable Backup
    "deepseek/deepseek-r1-distill-llama-70b:free", # Reasoning Backup
]

# === PROMPT ENGINEER SYSTEM ===
# === PROFESSIONAL PROMPT SYSTEM (Storytelling + Cinematic) ===
PROMPT_SYSTEM = """You are a PROFESSIONAL Stable Diffusion prompt engineer specializing in high-end Ecchi/Pinup photography.

Your goal: Create LONG, CINEMATIC, STORY-DRIVEN prompts (40-60 tags) with professional photography terminology.

MANDATORY STRUCTURE:
1. QUALITY BASE: "masterpiece, best quality, ultra-detailed, 8k, absurdres, highly detailed"
2. SUBJECT: "1girl, solo" + specific character details
3. NARRATIVE SCENE: Tell a STORY (e.g., "lazy Sunday morning in bed, just woke up, stretching arms above head, messy bedroom hair")
4. EXPRESSION: Professional terms ("sultry gaze", "seductive smile", "playful smirk", "teasing expression", "bedroom eyes")
5. OUTFIT: Specific fabrics/details ("silk camisole", "lace trim", "sheer fabric", "see-through material")
6. POSE: Dynamic and suggestive ("arched back", "hand on hip", "looking over shoulder", "crossed legs")
7. LIGHTING: CRITICAL ("volumetric lighting", "rim light", "soft window light", "dramatic shadows", "backlit", "golden hour")
8. COMPOSITION: Photography terms ("dutch angle", "shallow depth of field", "bokeh", "cinematic composition", "intimate framing")
9. ATMOSPHERE: Mood setting ("intimate atmosphere", "sensual mood", "cozy ambiance")

EXAMPLES (LONG FORMAT):

Input: "Lazy Morning Bedroom"
Output: masterpiece, best quality, ultra-detailed, 8k, absurdres, 1girl, solo, lazy Sunday morning in bed, just woke up, stretching arms above head, messy bedroom hair, sultry half-asleep expression, white silk camisole, lace trim panties, lying on white sheets, unmade bed, arched back, soft morning sunlight streaming through curtains, volumetric lighting, warm color temperature, rim light on hair, shallow depth of field, bokeh background, intimate atmosphere, cozy bedroom setting, soft shadows, detailed skin texture, bedroom eyes, playful smile, bare shoulders, thighs visible, cinematic composition, dutch angle

Input: "Poolside Afternoon"
Output: masterpiece, best quality, ultra-detailed, 8k, absurdres, 1girl, solo, relaxing by infinity pool, golden hour sunset, wet skin glistening, water droplets on body, black designer bikini, tying bikini string, looking at viewer with seductive smile, sitting on pool edge, legs in water, sultry expression, sunglasses pushed up on head, backlit by sunset, rim lighting on curves, dramatic shadows, tropical background blurred, bokeh, shallow depth of field, warm orange lighting, lens flare, intimate atmosphere, professional fashion photography, detailed skin, hip dip visible, cinematic framing"""  

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
    
    # HARDCODED AESTHETIC LORA (Since we download it in runpod_ultra.sh)
    # This bypasses API detection issues
    lora_tags.append("<lora:aesthetic_quality_masterpiece:0.6>")
    log('success', "Aesthetic LoRA: aesthetic_quality_masterpiece @ 0.6 (Forced)")

    # HARDCODED PERFECT EYES LORA (User Request)
    lora_tags.append("<lora:perfect_eyes:0.5>")
    log('success', "Aesthetic LoRA: perfect_eyes @ 0.5 (Forced)")
    
    for lora in loras:
        name = lora.get('name', '')
        name_lower = name.lower()
        
        # Skip if it's the one we already hardcoded
        if 'aesthetic_quality' in name_lower:
            continue
            
        # Character LoRAs only with --lora flag
        if USE_LORA:
            for key, weight in character_loras.items():
                if key.lower() in name_lower:
                    lora_tags.append(f"<lora:{name}:{weight}>")
                    log('success', f"Character LoRA: {name} @ {weight}")
                    break
    
    return ", ".join(lora_tags)

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
                log('debug', f"   📝 Raw response: {content[:100]}...")  # Debug log
                content = content.strip('"\'')
                # If content starts with thinking process <think>, remove it
                if '<think>' in content:
                    content = content.split('</think>')[-1].strip()
                
                if '\n' in content:
                    lines = [l.strip() for l in content.split('\n') if l.strip()]
                    if lines:
                        # Prefer the last line if it looks like tags, or first line if narrative
                        content = lines[0] 
                
                if not content:
                    log('warning', f"   ⚠️ Empty response from {model}")
                    return None
                    
                log('success', f"[OpenRouter] {model} responded: {content[:50]}...")
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
    log('warning', "All AI providers failed. Using built-in PROFESSIONAL prompt library.")
    theme_prompts = {
        "Bedroom (Lingerie)": "masterpiece, best quality, ultra-detailed, 8k, 1girl, solo, lazy Sunday morning in bed, just woke up, stretching arms above head, messy bedroom hair, sultry half-asleep expression, white silk camisole, lace trim panties, lying on white sheets, unmade bed, arched back, soft morning sunlight streaming through curtains, volumetric lighting, warm color temperature, rim light on hair, shallow depth of field, bokeh background, intimate atmosphere, cozy bedroom setting, soft shadows, detailed skin texture, bedroom eyes, playful smile, bare shoulders, thighs visible",
        
        "Beach (Bikini)": "masterpiece, best quality, ultra-detailed, 8k, 1girl, solo, relaxing on white sand beach, golden hour afternoon, slight ocean breeze, turquoise water background, white designer bikini with side ties, tying bikini string behind back, wet skin glistening with suntan oil, water droplets, looking at viewer with seductive smile, sitting with legs crossed, arched back, long hair flowing in wind, sultry expression, sunglasses on head, backlit by warm sunset, rim lighting on curves, lens flare, bokeh, tropical palm trees blurred in background, intimate atmosphere, fashion photography, detailed skin, hip curves visible",
        
        "Onsen (Steam)": "masterpiece, best quality, ultra-detailed, 8k, 1girl, solo, private outdoor onsen at dusk, rising steam creating mystical atmosphere, traditional wooden bath, wet long hair clinging to shoulders, droplets on bare skin, small white towel barely covering, sultry relaxed expression, eyes half closed, looking at viewer, sitting on stone edge, legs in hot water, soft evening light filtering through steam, volumetric fog, rim lighting through mist, warm color grading, intimate setting, japanese aesthetic, cherry blossom petals floating, wooden bucket nearby, sensual mood, detailed skin with water beads",
        
        "Feet Focus": "masterpiece, best quality, ultra-detailed, 8k, 1girl, solo, sitting on plush velvet chair, legs elegantly extended upward, barefoot soles facing viewer, detailed toes with red pedicure, looking back over shoulder with playful teasing smile, sultry expression, wearing short silk robe partially open, soft studio lighting, rim light on legs, shallow depth of field, feet in sharp focus, bokeh background, intimate atmosphere, professional fashion photography, detailed skin texture, arched feet, sensual pose",
        
        "From Behind (Ass Focus)": "masterpiece, best quality, ultra-detailed, 8k, 1girl, solo, standing in front of floor-length mirror, looking back over shoulder at viewer, seductive smile, bedroom eyes, black lace panties, bare back visible, hand on hip, arched lower back emphasizing curves, messy ponytail, soft bedroom lighting, volumetric light from window, rim light on curve of hips, warm color temperature, intimate atmosphere, morning light, detailed skin texture, tasteful composition, cinematic framing, shallow depth of field",
        
        "Poolside Afternoon": "masterpiece, best quality, ultra-detailed, 8k, 1girl, solo, relaxing by infinity pool, golden hour sunset, wet skin glistening, water droplets on body, black designer bikini, adjusting bikini strap, looking at viewer with seductive smile, sitting on pool edge, legs in water, sultry expression, sunglasses pushed up on head, backlit by sunset, rim lighting on curves, dramatic shadows, tropical background blurred, bokeh, shallow depth of field, warm orange lighting, lens flare, intimate atmosphere, professional fashion photography, detailed skin, hip dip visible",
        
        "Mirror Selfie": "masterpiece, best quality, ultra-detailed, 8k, 1girl, solo, taking mirror selfie in modern bathroom, holding phone up, looking at phone screen with playful duck face expression, wearing crop top and short shorts, leaning forward slightly, cleavage visible, one hand on hip, sultry teasing smile, camera flash creating dramatic lighting, rim light from bathroom lights, shallow depth of field, phone in focus, bokeh mirror reflection, intimate casual atmosphere, messy hair in bun, detailed skin, warm lighting, sensual pose",
    }
    fallback = theme_prompts.get(theme, f"masterpiece, best quality, ultra-detailed, 8k, 1girl, solo, {theme}, sultry expression, seductive smile, volumetric lighting, rim light, shallow depth of field, bokeh, cinematic composition, intimate atmosphere, detailed skin, professional photography")
    return fallback

def get_model_info():
    """Get current model info from server. Prioritizes OneObsession > WAI."""
    try:
        resp = requests.get(f"{REFORGE_API}/sdapi/v1/sd-models", timeout=5)
        if resp.status_code == 200:
            models = resp.json()
            
            # Priority 1: OneObsession (User Request: Pinup/Ecchi)
            for m in models:
                if 'oneobsession' in m['title'].lower() or 'obsession' in m['title'].lower():
                    return m['title']
            
            # Priority 2: WAI-Illustrious (Fallback High Quality)
            for m in models:
                if 'wai' in m['title'].lower() and 'illustrious' in m['title'].lower():
                    return m['title']
                if 'waiillustrious' in m['title'].lower():
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

def generate_image(prompt, negative_prompt, model_name, upscale_factor=2.0, no_hires=False, output_dir=None):
    """Call SD API with retry logic
    Args:
        upscale_factor: 2.0 (default for high qual), 1.5, 1.0 (off)
        output_dir: Directory to save images to (fixes ZIP bug)
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR
    log('gen', f"Starting generation with model: {model_name}")
    
    # Detect model type
    is_wai = 'wai' in model_name.lower()
    is_obs = 'obsession' in model_name.lower()
    
    # OPTIMIZED SETTINGS FOR MODEL TYPE
    # Obsession: Higher denoise, WAI: Lower denoise
    # User requested quality boost: using 2.0x upscale and slightly lower denoise to preserve details
    hr_denoise = 0.45 if is_obs else (0.35 if is_wai else 0.4)
    
    # Obsession/Pinup Specific Settings (Civitai Verified)
    steps = 30 if is_obs else 28
    cfg = 6.0 if is_obs else 5.0
    sampler = "DPM++ 2M Karras" if is_obs else "Euler a"
    
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        
        # High Quality Settings
        "steps": steps,
        "cfg_scale": cfg,
        "width": 832,
        "height": 1216,
        "sampler_name": sampler,
        "scheduler": "Karras",
        "batch_size": 1,
        
        "override_settings": {
            "sd_model_checkpoint": model_name,
            "CLIP_stop_at_last_layers": 2
        },
    }
    
    # Hires Fix (2x Default)
    use_hires = not no_hires and upscale_factor > 1.0
    if use_hires:
        payload.update({
            "enable_hr": True,
            "hr_scale": upscale_factor,
            "hr_upscaler": "R-ESRGAN 4x+ Anime6B",
            "denoising_strength": hr_denoise,
            "hr_second_pass_steps": 15,
            "hr_cfg_scale": cfg,
        })
        final_w = int(832 * upscale_factor)
        final_h = int(1216 * upscale_factor)
        log('info', f"Hires Fix: {upscale_factor}x → {final_w}x{final_h} (denoise {hr_denoise})")
    else:
        payload["enable_hr"] = False
        log('info', "Hires Fix: DISABLED (base 832x1216)")
    
    # ADetailer: HIGH RES FIX (1024x1024)
    # This prevents the blurry face issue by rendering the face at high res before pasting back
    try:
        scripts_resp = requests.get(f"{REFORGE_API}/sdapi/v1/scripts", timeout=5)
        if scripts_resp.status_code == 200:
            scripts_data = scripts_resp.json()
            available_scripts = [s.lower() for s in scripts_data.get("txt2img", [])]
            if "adetailer" in available_scripts:
                payload["alwayson_scripts"] = {
                    "ADetailer": {
                        "args": [
                            {   # Slot 1: Face fix (High Res)
                                "ad_model": "face_yolov8n.pt",
                                "ad_prompt": "detailed face, beautiful eyes, perfect face",
                                "ad_negative_prompt": "ugly face, deformed face, gas mask, mask",
                                "ad_confidence": 0.3,
                                "ad_denoising_strength": 0.4,
                                "ad_inpaint_width": 1024,
                                "ad_inpaint_height": 1024
                            },
                            {   # Slot 2: Hand fix (High Res)
                                "ad_model": "hand_yolov8n.pt",
                                "ad_prompt": "detailed hands, perfect fingers, 5 fingers",
                                "ad_negative_prompt": "extra fingers, fewer fingers, bad hands, 6 fingers",
                                "ad_confidence": 0.3,
                                "ad_denoising_strength": 0.45,
                                "ad_inpaint_width": 1024,
                                "ad_inpaint_height": 1024
                            }
                        ]
                    }
                }
                log('success', "ADetailer: face + hand fix enabled (@ 1024px)")
            else:
                log('warning', "ADetailer not found")
    except Exception:
        pass

    # FreeU Integration (Quality Boost)
    # Using conservative settings for SDXL/Pony/Illustrious
    try:
        available_scripts = [] # Need to fetch again if not cached, but for now assuming it might be there if integrated
        # FreeU is usually an extension or script. In Forge it's often built-in under 'Integrated'.
        # We can try adding it to alwayson_scripts or as a backend option.
        # For Forge, FreeU is often an 'AlwaysOn' script named 'FreeU Integrated' or just 'FreeU'.
        if "alwayson_scripts" not in payload:
            payload["alwayson_scripts"] = {}
            
        payload["alwayson_scripts"]["FreeU Integrated"] = {
            "args": [
                True,  # Enabled
                1.01,  # b1 (Backbone 1 focus) - Conservative for SDXL
                1.02,  # b2 (Backbone 2 focus)
                0.99,  # s1 (Skip 1 suppression)
                0.95   # s2 (Skip 2 suppression)
            ]
        }
        log('info', "FreeU: Enabled (Quality Boost)")
    except:
        pass

    # SAVE JSON METADATA
    try:
        # Create metadata payload
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": payload["steps"],
            "cfg_scale": payload["cfg_scale"],
            "sampler": payload["sampler_name"],
            "model": model_name,
            "hires_upscale": upscale_factor if use_hires else "None",
            "denoising_strength": hr_denoise if use_hires else "N/A"
        }
    except:
        metadata = {}

    log('info', "Sending request to SD Forge...")
    resp = requests.post(f"{REFORGE_API}/sdapi/v1/txt2img", json=payload, timeout=600)
    
    if resp.status_code == 200:
        data = resp.json()
        if 'images' not in data:
            log('error', "No images returned")
            return
            
        for idx, img_b64 in enumerate(data['images']):
            # Save Image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lady_nuggets_{timestamp}_{idx}.png"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(img_b64))
            
            # Save JSON Metadata
            json_filename = f"lady_nuggets_{timestamp}_{idx}.json"
            json_filepath = os.path.join(output_dir, json_filename)
            with open(json_filepath, "w") as f:
                json.dump(metadata, f, indent=2)
                
            log('success', f"Saved: {filename} + .json")
        
        return len(data['images'])
    else:
        log('error', f"Generation failed: {resp.text}")
        return 0

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
    """Load themes. User requested to OMIT complex external themes."""
    # Return Hardcoded Pinup Themes by default
    return ["Bedroom", "Beach", "Onsen", "Gym", "Office", "Simple Background", "Poolside", "Lingerie"]

def main():
    parser = argparse.ArgumentParser(description="Lady Nuggets Factory V10")
    parser.add_argument("--count", type=int, default=1, help="Number of images to generate")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    parser.add_argument("--theme", type=str, default=None, help="Specific theme to use")
    parser.add_argument("--lora", action="store_true", help="Enable character LoRA")
    parser.add_argument("--upscale", type=float, default=2.0, help="Hires upscale factor: 2.0 (default)")
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
        
        # Select Pinup Scenario (formerly Theme)
        # User requested: "ecchi, nsfw, feet focus, chest focus, from behind, dynamic poses"
        pinup_scenarios = [
            "Bedroom (Lingerie)", "Beach (Bikini)", "Onsen (Steam)", 
            "Simple Background (White)", "Simple Background (Black)",
            "Feet Focus", "Chest Focus", "From Behind (Ass Focus)", 
            "Dynamic Pose (Angle)", "Wet Skin (Shower)", 
            "Sweaty (Gym)", "Closeup (Face)", "Mirror Selfie"
        ]
        
        scenario = args.theme if args.theme else random.choice(pinup_scenarios)
        log('info', f"Scenario: {scenario}")
        
        # Get AI-generated prompt for this scenario
        scene_prompt = get_ai_prompt(scenario)
        
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
        
        # INJECT EMBEDDINGS (lazypos/lazyneg)
        # These are Textual Inversion embeddings downloaded by runpod_ultra.sh
        embedding_pos = "lazypos, "
        embedding_neg = "lazyneg, "
        
        # Added "perfect eyes" trigger word here
        section1 = f"{embedding_pos}perfect eyes, {artist_mix},\n{QUALITY_PREFIX}"
        section2 = f"{character}, {scene_prompt}"
        section3 = f"{QUALITY_SUFFIX}"
        if lora_block:
            section3 += f", {lora_block}"
        
        full_prompt = f"{section1},\nBREAK\n{section2},\nBREAK\n{section3}"
        final_negative = f"{embedding_neg}{NEGATIVE_PROMPT}"
        
        log('info', f"Artists: {artist_mix}")
        log('success', "Embeddings injected: lazypos, lazyneg")
        
        # Generate
        result = generate_image(full_prompt, final_negative, model_name, 
                               upscale_factor=args.upscale, no_hires=args.no_hires,
                               output_dir=output_dir)
        
        # Save check
        if result:
            total_saved += result
        
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
