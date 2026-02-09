# 👥 Guía 04: Sistema Multi-Personaje

> **Objetivo:** Expandir más allá de Lady Nuggets con personajes configurables.
> **Prioridad:** #4 - Más personajes = más variedad = más audiencia
> **Impacto:** Permite crear "series" temáticas y atraer fans de distintos arquetipos

---

## Problema Actual

Solo existe Lady Nuggets (catgirl pelo negro, ojos púrpura). Toda la producción es del mismo personaje.
Para escalar el contenido y atraer más audiencia, necesitamos variedad.

---

## Sistema de Personajes

### Estructura de datos

**Archivo nuevo:** `config/characters.json`

```json
{
  "characters": {
    "lady_nuggets": {
      "name": "Lady Nuggets",
      "description": "La OC principal. Catgirl misteriosa y traviesa.",
      "tags": {
        "physical": "(very long black hair:1.4), large purple eyes, soft black eyeliner, makeup shadows, glossy lips, subtle blush, mole on chin, bright pupils, narrow waist, wide hips, wavy hair",
        "features": "(thick black cat tail, long tail, black cat ears)",
        "personality": "cute, sexually suggestive, naughty face"
      },
      "lora": "LadyNuggets",
      "lora_weight": 0.8,
      "color_palette": ["purple", "black", "silver"],
      "default_style": "anime_classic",
      "active": true
    },
    "sakura": {
      "name": "Sakura Moon",
      "description": "Kitsune (fox girl) elegante y serena. Contraste con Nuggets.",
      "tags": {
        "physical": "(very long white hair:1.4), fox ears, golden eyes, delicate features, pale skin, slender build, elegant posture",
        "features": "(fluffy white fox tail:1.3), (fox ears:1.2)",
        "personality": "serene expression, gentle smile, graceful"
      },
      "lora": null,
      "lora_weight": 0,
      "color_palette": ["white", "gold", "pink"],
      "default_style": "pastel",
      "active": true
    },
    "raven": {
      "name": "Raven Hex",  
      "description": "Demon girl rebelde. Para contenido más dark/gothic.",
      "tags": {
        "physical": "(short messy red hair:1.3), sharp red eyes, dark makeup, smirk, athletic build, tan skin, abs",
        "features": "(small demon horns:1.2), (demon tail:1.1), (small bat wings:0.8)",
        "personality": "confident, rebellious, fierce expression, smirk"
      },
      "lora": null,
      "lora_weight": 0,
      "color_palette": ["red", "black", "dark purple"],
      "default_style": "dark_mood",
      "active": false
    }
  }
}
```

---

## Implementación

### Paso 1: Cargar personajes en `factory.py`

```python
def load_characters():
    """Carga personajes desde config"""
    config_path = os.path.join(BASE_DIR, "config", "characters.json")
    with open(config_path) as f:
        data = json.load(f)
    # Solo retornar personajes activos
    return {k: v for k, v in data["characters"].items() if v.get("active", True)}

def build_character_prompt(character_key=None):
    """Construye prompt base para un personaje"""
    characters = load_characters()
    
    if character_key is None:
        # Selección aleatoria ponderada (Lady Nuggets aparece más)
        weights = {"lady_nuggets": 5}  # 5x más probable
        char_key = random.choices(
            list(characters.keys()),
            weights=[weights.get(k, 1) for k in characters.keys()]
        )[0]
    else:
        char_key = character_key
    
    char = characters[char_key]
    
    # Construir prompt del personaje
    parts = [
        "1girl, solo",
        char["tags"]["physical"],
        char["tags"]["features"],
        char["tags"]["personality"]
    ]
    
    # LoRA si existe
    lora_tag = ""
    if char.get("lora"):
        lora_tag = f"<lora:{char['lora']}:{char['lora_weight']}>"
    
    return ", ".join(parts), lora_tag, char
```

### Paso 2: CLI con selección de personaje

```python
# En main():
parser.add_argument("--character", type=str, default=None,
    help="Character key (lady_nuggets, sakura, raven) or 'random'")
parser.add_argument("--list-characters", action="store_true",
    help="List available characters")
```

### Paso 3: Metadata por personaje

Cada imagen guardada debe incluir qué personaje se usó:

```json
{
  "prompt": "...",
  "character": "lady_nuggets",
  "character_name": "Lady Nuggets",
  "theme": "Cyberpunk",
  "style": "cinematic",
  "timestamp": "20260210_143000",
  "score": null
}
```

---

## Creación de Nuevos Personajes

### Guía para el Owner

Para crear un personaje nuevo:

1. **Definir rasgos físicos** en tags Danbooru precisos
2. **Elegir features especiales** (orejas, cola, cuernos, alas)
3. **Definir personalidad visual** (expresión, actitud)
4. **Asignar paleta de colores** (para coherencia visual)
5. **Opcionalmente entrenar LoRA** (ver guía de LoRA training)

### Cómo entrenar LoRA para personaje nuevo

> **Nota:** Esto es OPCIONAL. Los personajes sin LoRA funcionan pero son menos consistentes.

1. Generar 50+ imágenes del personaje que te gusten
2. Curadorarlas (las mejores 20-30)
3. Usar kohya_ss para entrenar LoRA (guía separada si se necesita)
4. Agregar el LoRA al config del personaje

---

## Interacción entre Personajes

### Escenas con múltiples personajes (Futuro)

```json
{
  "scene_type": "duo",
  "characters": ["lady_nuggets", "sakura"],
  "interaction": "standing together, height difference, contrasting outfits",
  "prompt_modifier": "2girls, "
}
```

> **IMPORTANTE:** Escenas multi-personaje son MUCHO más difíciles para SD.
> Solo intentar después de que cada personaje funcione bien individualmente.
> Requiere más VRAM y más pasos.

---

## Verificación

1. `python factory.py --list-characters` muestra personajes disponibles
2. `python factory.py --character lady_nuggets --count 2` genera solo Lady Nuggets
3. `python factory.py --character sakura --count 2` genera Sakura Moon
4. `python factory.py --character random --count 5` genera mix aleatorio
5. Metadata de cada imagen incluye el personaje usado
6. Los LoRAs se aplican correctamente cuando existen

---

## Notas para el Agente

- **Lady Nuggets siempre es la principal** - debe aparecer más que el resto
- Los personajes sin LoRA serán menos consistentes - es esperado
- NO mezclar features de personajes (cola de gato en fox girl, etc.)
- Cada personaje debe tener paleta de colores coherente
- Testear cada personaje individualmente antes de activarlo
- Los personajes inactivos (`"active": false`) no aparecen en rotación random
