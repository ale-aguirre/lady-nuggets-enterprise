# 🎨 Guía 02: Prompt Engineering Avanzado

> **Objetivo:** Sistema de prompts más sofisticado con estilos artísticos, variación inteligente, y composiciones profesionales.
> **Prioridad:** #2 - Más variedad = más engagement = más subs

---

## Problema Actual

El sistema actual genera prompts con un solo LLM call genérico. Resultado:
- Poca variación entre imágenes
- Composiciones repetitivas
- Sin control de estilos artísticos

---

## Sistema Propuesto: Prompt Composer

```
┌─────────────┐   ┌──────────────┐   ┌─────────────┐
│   THEME     │ + │    STYLE     │ + │    MOOD     │ = FINAL PROMPT
│ "Beach Day" │   │ "Manhwa"     │   │ "Romantic"  │
└─────────────┘   └──────────────┘   └─────────────┘
```

---

## Paso 1: Crear Banco de Estilos Artísticos

**Archivo nuevo:** `config/styles.json`

```json
{
  "styles": {
    "manhwa": {
      "tags": "(manhwa style), (korean webtoon), clean linework, sharp eyes, detailed shading",
      "negative_extra": "chibi, super deformed, western cartoon",
      "description": "Estilo Solo Leveling / Lookism"
    },
    "anime_classic": {
      "tags": "(anime screenshot), (anime coloring), cel shading, vibrant colors",
      "negative_extra": "realistic, photorealistic, 3d",
      "description": "Estilo anime TV clásico"
    },
    "semi_realistic": {
      "tags": "((realistic, photorealistic, realistic shading)), detailed skin texture",
      "negative_extra": "flat color, cel shading, anime screenshot",
      "description": "Estilo 2.5D semi-realista"
    },
    "flat_2d": {
      "tags": "((flat color:1.8)), (abstract:0.5), bold outlines, minimalist shading",
      "negative_extra": "realistic, 3d, photorealistic",
      "description": "Estilo ilustración plana"
    },
    "cinematic": {
      "tags": "(chiaroscuro, high contrast:0.5), (sunbeam), volumetric lighting, dramatic shadows, film grain",
      "negative_extra": "flat lighting, overexposed",
      "description": "Iluminación dramática tipo película"
    },
    "dark_mood": {
      "tags": "(dark, chiaroscuro, high-contrast:1.7), moody atmosphere, dim lighting",
      "negative_extra": "bright, colorful, cheerful",
      "description": "Ambiente oscuro y misterioso"
    },
    "pastel": {
      "tags": "pastel colors, soft lighting, dreamy atmosphere, soft focus background",
      "negative_extra": "harsh shadows, dark, high contrast",
      "description": "Colores pastel suaves"
    }
  }
}
```

> **NOTA:** Los tags de estilo vienen directamente de las recomendaciones del autor de OneObsession v19.

### Paso 2: Crear Banco de Composiciones

**Archivo nuevo:** `config/compositions.json`

```json
{
  "compositions": {
    "portrait_close": {
      "framing": "close-up portrait, face focus, upper body",
      "pose": "looking at viewer, slight head tilt, soft expression"
    },
    "full_body_dynamic": {
      "framing": "full body, wide shot, centered",
      "pose": "dynamic pose, action pose, weight shift"
    },
    "three_quarter": {
      "framing": "three-quarter view, cowboy shot, from side",
      "pose": "hand on hip, confident stance, looking over shoulder"
    },
    "sitting": {
      "framing": "sitting, from above slightly, medium shot",
      "pose": "sitting cross-legged, leaning forward, relaxed"
    },
    "back_view": {
      "framing": "from behind, back view, looking back",
      "pose": "looking over shoulder, wind in hair, walking away"
    },
    "low_angle": {
      "framing": "from below, low angle, dramatic perspective",
      "pose": "standing tall, hands on hips, looking down at viewer"
    }
  }
}
```

### Paso 3: Mejorar el LLM System Prompt

**En `factory.py`, reemplazar `PROMPT_SYSTEM`:**

```python
PROMPT_SYSTEM = """You are an expert Anime Art Director specialized in Danbooru-style prompts.

RULES:
1. OUTPUT ONLY comma-separated tags. NO explanations, NO quotes.
2. Include: outfit details (materials, colors, accessories), location details, lighting, expression
3. Use precise Danbooru tags (e.g., "serafuku" not "school uniform")
4. Outfit MUST match location logically
5. Add 2-3 atmospheric details (particles, reflections, etc.)
6. Keep under 80 words
7. NEVER repeat the character description (hair, eyes, etc.) - that's already handled

QUALITY GUIDELINES:
- Describe the SCENE, not the character
- Be specific about fabrics: "silk", "leather", "lace", "velvet"
- Include environment interaction: "wind blowing hair", "wet floor reflections"
- Add micro-details: "earrings", "ribbon", "choker", "bracelet"

EXAMPLES:
Theme: "Witch Academy" + Style: "cinematic"
→ wearing pointed witch hat, black lace corset, flowing cape, thigh-high boots, holding crystal staff, ancient library background, floating books, candlelight, dust particles, volumetric light through window, mysterious smile

Theme: "Street Fashion" + Style: "manhwa"  
→ wearing oversized hoodie, pleated miniskirt, platform sneakers, crossbody bag, leaning against graffiti wall, neon signs, wet pavement reflections, nighttime, convenience store glow, earbuds dangling, confident smirk
"""
```

### Paso 4: Prompt Builder Modular

**Modificar `factory.py` - función `build_prompt()`:**

```python
import json
import random

def load_config(filename):
    config_dir = os.path.join(BASE_DIR, "config")
    with open(os.path.join(config_dir, filename)) as f:
        return json.load(f)

def build_prompt(theme, style_name=None, composition_name=None):
    """
    Construye prompt completo combinando:
    - OC_BASE (personaje fijo)
    - Style (estilo artístico)
    - Composition (encuadre/pose)
    - Scene (generada por LLM)
    - LoRA block
    """
    styles = load_config("styles.json")["styles"]
    compositions = load_config("compositions.json")["compositions"]
    
    # Selección aleatoria si no se especifica
    style = styles.get(style_name, random.choice(list(styles.values())))
    comp = compositions.get(composition_name, random.choice(list(compositions.values())))
    
    # Pedir al LLM solo la escena (no el personaje ni composición)
    scene_prompt = get_ai_prompt(f"{theme} + Style: {style.get('description', '')}")
    
    # Construir prompt final
    parts = [
        OC_BASE,
        comp["framing"],
        comp["pose"],
        style["tags"],
        scene_prompt
    ]
    
    # Agregar LoRA
    lora_block = build_lora_block()
    if lora_block:
        parts.append(lora_block)
    
    full_prompt = ", ".join(parts)
    
    # Construir negative también
    full_negative = NEGATIVE_PROMPT
    if style.get("negative_extra"):
        full_negative += ", " + style["negative_extra"]
    
    return full_prompt, full_negative
```

### Paso 5: Temas Mejorados

**Actualizar `config/themes.txt`:**

```text
# === LOCATIONS ===
Rooftop Sunset
Cherry Blossom Garden
Neon Tokyo Alley
Medieval Castle Library
Underwater Palace
Space Station
Victorian Ballroom
Hot Springs Mountain
Cyberpunk Nightclub
Enchanted Forest
Beach Boardwalk
Gothic Cathedral
Cozy Coffee Shop
Rainy City Street
Desert Oasis

# === OUTFITS ===
Gothic Lolita
Shrine Maiden
Military Commander
Bunny Girl Casino
Mermaid Princess
Witch Academy
Idol Stage
Kimono Festival
Maid Cafe
Racing Queen

# === MOODS ===
Romantic Moonlight
Battle Ready
Sleepy Morning
Playful Summer
Mysterious Night
Elegant Gala
Rebellious Street
Dreamy Fantasy
Confident Boss
Shy Date
```

---

## Verificación

1. Generar 10 imágenes con estilos diferentes
2. Verificar que cada imagen tiene estilo artístico distinto
3. Verificar que las composiciones varían (no siempre full body frontal)
4. Verificar que los outfits son coherentes con la ubicación
5. Comparar variedad visual con el sistema anterior

---

## Notas para el Agente

- Los tags de estilo del autor de OneObsession son CRÍTICOS - no inventar tags genéricos
- El LLM solo debe generar la ESCENA, no repetir el personaje
- Mantener el CFG en 3-6 (recomendación del autor del modelo)
- Si un estilo tiene `negative_extra`, CONCATENAR al negative prompt base, no reemplazar
- Testear cada estilo individualmente antes de mezclar
