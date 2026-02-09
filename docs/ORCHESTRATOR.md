# 🎯 ORCHESTRATOR - Lady Nuggets Enterprise

> **Este documento es la fuente de verdad para cualquier agente IA que trabaje en este proyecto.**
> Léelo COMPLETO antes de hacer cualquier cambio.

---

## 🧠 Contexto del Proyecto

**Owner:** Alexis Aguirre (@ladynuggets en DeviantArt - 6K followers)  
**Objetivo:** Pipeline automatizado de contenido NSFW anime para monetizar via Patreon/Fanvue  
**Modelo:** Zero-Touch Operation - generación, curación, y distribución automática  

### El Negocio
- **Gratis:** Imágenes curadas (baja res / watermark) en Twitter/DeviantArt
- **$5/mes:** Acceso galería High Res (Patreon)
- **$15/mes:** Acceso al bot generador en Discord
- **$50/mes:** Comisión simple mensual incluida

---

## 🏗️ Arquitectura Actual

```
┌─────────────────────────────────────────────────────────┐
│                  LADY NUGGETS ENTERPRISE                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │ factory  │───▶│ curator  │───▶│  distributor     │   │
│  │   .py    │    │   .py    │    │   .py            │   │
│  │ (genera) │    │ (filtra) │    │ (publica)        │   │
│  └──────────┘    └──────────┘    └──────────────────┘   │
│       │                                │                 │
│       ▼                                ▼                 │
│  ┌──────────┐                   ┌──────────────────┐    │
│  │ Stable   │                   │ Twitter/DA/      │    │
│  │Diffusion │                   │ Patreon           │    │
│  │ API      │                   └──────────────────┘    │
│  └──────────┘                                           │
│                                                          │
│  ┌──────────┐    ┌──────────┐                           │
│  │ discord  │    │ reply    │                            │
│  │  _bot.py │    │  _bot.py │                            │
│  └──────────┘    └──────────┘                           │
└─────────────────────────────────────────────────────────┘
```

### Estado de Componentes

| Script | Estado | Descripción |
|--------|--------|-------------|
| `factory.py` | ✅ V10 Funcional | Genera imágenes con SD + LLM prompting |
| `curator.py` | ⚠️ Básico | Evalúa calidad con Vision AI (necesita mejora) |
| `distributor.py` | ⚠️ Borrador | Publica en Twitter/DA/Patreon |
| `discord_bot.py` | ⚠️ Borrador | Bot de Discord con engagement |
| `reply_bot.py` | ⚠️ Borrador | Auto-responde comentarios |
| `runpod_ultra.sh` | ✅ V2 Funcional | Deploy automático en RunPod |

---

## ⚙️ Stack Técnico

### Generación de Imágenes
- **Motor:** Stable Diffusion WebUI (A1111)
- **Modelo:** OneObsession v19 Atypical (Illustrious/NoobAI merge)
  - CivitAI ID: `2443982`
  - Tipo: SD 1.5 → Illustrious fine-tune
  - **Parámetros óptimos del autor:**
    - Steps: 25-35
    - CFG: 3-6 (NO más alto)
    - Sampler: Euler a
    - Resolución: 832×1216 o 768×1344
  - **Descarga:** `curl -L -o model.safetensors "URL?token=CIVITAI_TOKEN"` (token como query param, NO header)
- **LoRA:** LadyNuggets (personaje principal)
- **Deploy:** RunPod (A6000 48GB recomendado)
  - Template: `RunPod Stable Diffusion` (`runpod/stable-diffusion:web-ui-10.2.1`)

### LLM para Prompting
- **Primario:** Groq (gratis, rápido) → `llama-3.3-70b-versatile`
- **Fallback:** OpenRouter (gratis) → `meta-llama/llama-3.3-70b-instruct:free`

### API Keys Requeridas
| Key | Variable | Propósito |
|-----|----------|-----------|
| Groq | `GROQ_KEY` | LLM prompting |
| OpenRouter | `OPENROUTER_KEY` | LLM fallback |
| CivitAI | `CIVITAI_TOKEN` | Descarga modelos |

---

## 🎨 Personaje: Lady Nuggets

**Rasgos fijos:**
- Pelo negro muy largo y ondulado
- Ojos grandes púrpura
- Eyeliner negro, labios brillantes, rubor sutil, lunar en mentón
- Cintura estrecha, caderas anchas
- Cola de gato negra gruesa, orejas de gato negras

**Prompt base:**
```
masterpiece, best quality, amazing quality, very aesthetic, absurdres, newest, depth of field, highres,
1girl, solo, full body, centered composition, looking at viewer,
(very long black hair:1.4), large purple eyes, soft black eyeliner, makeup shadows, glossy lips, subtle blush, mole on chin, bright pupils,
narrow waist, wide hips, cute, sexually suggestive, naughty face, wavy hair,
(thick black cat tail, long tail, black cat ears), dynamic pose
```

---

## 🚀 Roadmap - Próximas Features

### Fase 1 - Pipeline Básico (ACTUAL)
- [x] Factory V10 (generación con LLM prompting)
- [x] RunPod deployment automático
- [x] CivitAI download fix
- [ ] Auto-detección de VRAM y ajuste de resolución
- [ ] Prompt engineering avanzado (estilos artísticos, composición)

### Fase 2 - Calidad y Volumen
- [ ] Curator V2 (evaluación automática con Vision AI)
- [ ] Pipeline completo: genera → evalúa → descarta → regenera
- [ ] Multi-character system (más allá de Lady Nuggets)
- [ ] Batch inteligente con reportes de calidad

### Fase 3 - Dashboard Web
- [ ] Dashboard Next.js para visualizar imágenes generadas
- [ ] Filtros, favoritos, ajuste de parámetros desde browser
- [ ] Galería con watermark automático para versiones públicas

### Fase 4 - Distribución Automática
- [ ] Distributor: auto-post a Twitter/DA/Patreon
- [ ] Discord bot con "Daily Waifu"
- [ ] Reply bot para engagement automático

---

## 📋 Quick Start para Agentes

### Generar imágenes en RunPod:
```bash
git clone https://github.com/ale-aguirre/lady-nuggets-enterprise.git
cd lady-nuggets-enterprise
export CIVITAI_TOKEN=<key>
chmod +x scripts/runpod_ultra.sh
./scripts/runpod_ultra.sh --count 10
```

### Desarrollo local:
```bash
cd lady-nuggets-enterprise
source venv/bin/activate
python scripts/factory.py --count 2 --debug
```

### Archivos clave a revisar:
1. `PERFIL.md` - Contexto del negocio y del owner
2. `PLAN_NEGOCIO_AUTOMATIZADO.md` - Arquitectura del pipeline
3. `docs/RUNPOD_SETUP.md` - Guía de deployment
4. `.agent/workflows/civitai-download.md` - Cómo descargar modelos
5. `config/.env` - API keys y configuración
6. `config/themes.txt` - Temas para generación

---

## ⚠️ Lecciones Aprendidas (Bugs Resueltos)

1. **CivitAI downloads**: SIEMPRE usar `&token=KEY` como query parameter, NO `Authorization: Bearer` header
2. **VRAM OOM en 3090**: 832×1216 + Hires 2x = 1664×2432 excede 24GB. Usar A6000 (48GB) o reducir hires scale
3. **Puerto SD API**: Puede ser 7860, 7861, o 7862. El script auto-detecta
4. **OneObsession v19**: CFG alto (>6) genera imágenes sobresaturadas. Mantener en 3-6
