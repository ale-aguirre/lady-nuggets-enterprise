# 🤖 Instrucciones para LLMs - Lady Nuggets Enterprise

> **¿Sos un agente IA trabajando en este proyecto?**
> Seguí estas instrucciones en orden. No improvises.

---

## Paso 0: Contexto Obligatorio

**ANTES de hacer cualquier cosa, leé estos archivos:**

1. `docs/ORCHESTRATOR.md` — Arquitectura, stack, estado de cada componente
2. `PERFIL.md` — Quién es el dueño y qué busca con este proyecto
3. `docs/RUNPOD_SETUP.md` — Cómo deployar en RunPod

---

## ¿Qué tenés que hacer?

El dueño (Alexis) te va a pedir una de estas cosas. Seguí la guía correspondiente:

### Opción A: "Generá imágenes" / "Correlo en RunPod"
→ Seguí `docs/RUNPOD_SETUP.md`
→ Si hay errores, leé `docs/ORCHESTRATOR.md` sección "Lecciones Aprendidas"

### Opción B: "Mejorá el pipeline"
→ Leé e implementá `docs/guides/01_PIPELINE_COMPLETO.md`
→ **Orden:** curator.py → pipeline.py → watermark → reportes

### Opción C: "Mejorá los prompts"
→ Leé e implementá `docs/guides/02_PROMPT_ENGINEERING.md`
→ **Orden:** styles.json → compositions.json → modificar factory.py

### Opción D: "Hacé el dashboard"
→ Leé e implementá `docs/guides/03_DASHBOARD.md`
→ **Orden:** setup Next.js → API routes → galería → filtros

### Opción E: "Agregá personajes"
→ Leé e implementá `docs/guides/04_MULTI_CHARACTER.md`
→ **Orden:** characters.json → modificar factory.py → testear

---

## 🔴 Reglas OBLIGATORIAS

1. **NUNCA subas API keys a Git.** El `.env` está en `.gitignore` por una razón.
2. **SIEMPRE hacé `git push`** después de cada cambio funcional.
3. **SIEMPRE probá con `python3 -c "import py_compile; py_compile.compile('scripts/factory.py')"`** antes de pushear.
4. **NUNCA uses CFG mayor a 6** en los parámetros de generación (causa oversaturation en Illustrious).
5. **Usá dark mode** en cualquier UI que crees (preferencia del dueño).
6. **Stack del dueño:** Next.js + Tailwind CSS + Lucide Icons. No uses otros frameworks.

---

## 🔧 Cómo arreglar problemas comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `405 Not Allowed` | nginx proxy de RunPod | Matar server y reiniciar: `pkill -f launch.py; cd /workspace/stable-diffusion-webui; nohup python3 launch.py --api --listen --port 7860 --xformers > /workspace/reforge.log 2>&1 &` |
| `401 Unauthorized` en LLM | API keys vacías/incorrectas | Verificar `config/.env` tiene keys reales |
| `ADetailer not found` | Extensión no instalada | `factory.py` ya lo maneja automáticamente |
| `CUDA out of memory` | Resolución muy alta | Reducir `hr_scale` de 1.5 a 1.0 o desactivar hires |
| Puerto incorrecto | Server en otro puerto | `factory.py` auto-detecta (7860, 7861, 7862) |
| `.env` vacío en pod nuevo | `.gitignore` lo excluye | Crear manualmente con las keys |

---

## 📋 Orden de Prioridad de Features

Si el dueño no especifica qué hacer, seguí este orden:

```
1. Pipeline Completo  (01_PIPELINE_COMPLETO.md)   → Más producción
2. Prompt Engineering  (02_PROMPT_ENGINEERING.md)  → Más variedad
3. Dashboard          (03_DASHBOARD.md)            → Control visual
4. Multi-Character    (04_MULTI_CHARACTER.md)      → Más audiencia
```

Cada guía tiene su sección de **Verificación** al final. No la saltees.

---

## ⚙️ Parámetros de Generación Correctos

**Estos son los parámetros investigados y validados para Illustrious/OneObsession v19:**

| Parámetro | Valor | Por qué |
|-----------|-------|---------|
| Steps | 25 | Sweet spot para Illustrious (más no mejora) |
| CFG Scale | 4.5 | Rango seguro 3-5. Arriba de 6 = sobresaturación |
| Sampler | Euler a | Consenso comunidad para Illustrious |
| Resolución | 832×1216 | Ratio 2:3, tamaño recomendado |
| Hires Scale | 1.5x | 2x puede causar artefactos |
| Hires Denoise | 0.45 | 0.4-0.5 da mejor detalle |
| Hires Steps | 20 | Más pasos = upscale más limpio |
| Hires Upscaler | Latent | Eficiente en VRAM |
| CLIP Skip | 2 | Estándar para Illustrious |

**Resultado final:** 1248×1824 pixels (alta calidad para Patreon)

---

## 📁 Estructura del Proyecto

```
lady-nuggets-enterprise/
├── config/
│   ├── .env              # API keys (NO se sube a Git)
│   └── themes.txt        # Temas para generación
├── scripts/
│   ├── factory.py        # ⭐ Core: genera imágenes con SD + LLM
│   ├── curator.py        # Evalúa calidad (necesita mejorar)
│   ├── distributor.py    # Publica en redes (borrador)
│   ├── discord_bot.py    # Bot Discord (borrador)
│   ├── runpod_ultra.sh   # ⭐ Deploy automático en RunPod
│   └── rescue.sh         # Reiniciar server SD
├── docs/
│   ├── ORCHESTRATOR.md   # ⭐ Contexto maestro del proyecto
│   ├── RUNPOD_SETUP.md   # Guía de deployment
│   ├── INSTRUCCIONES_LLM.md  # ESTE ARCHIVO
│   └── guides/           # Guías de implementación por feature
├── content/              # Imágenes generadas
└── web/                  # Dashboard (vacío, por implementar)
```
