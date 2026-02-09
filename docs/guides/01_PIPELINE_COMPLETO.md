# 🔄 Guía 01: Pipeline Completo de Producción

> **Objetivo:** Generar lotes de 50 imágenes, evaluar calidad automáticamente, quedarse solo con las mejores, empaquetar y reportar.
> **Prioridad:** #1 - Impacto directo en producción de contenido

---

## Problema Actual

Hoy el flujo es manual:
1. `factory.py` genera imágenes
2. Alexis revisa una por una
3. Descarta las malas manualmente

**Queremos:** Un comando que genere 50, descarte las malas, y empaquete las top 10 listas para publicar.

---

## Arquitectura del Pipeline

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ factory  │────▶│ curator  │────▶│  packer  │────▶│  report  │
│ genera   │     │ evalúa   │     │ organiza │     │ resumen  │
│ 50 imgs  │     │ score>7  │     │ HiRes/Lo │     │ stats    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

---

## Implementación Paso a Paso

### Paso 1: Refactorizar `curator.py`

**Archivo:** `scripts/curator.py`

El curator actual es básico. Necesita:

```python
# curator.py - v2 SPEC

# INPUT: Directorio con imágenes generadas
# OUTPUT: Directorio con imágenes aprobadas (score >= 7)

# Flujo:
# 1. Leer todas las imágenes .png del directorio input
# 2. Para cada imagen:
#    a. Convertir a base64
#    b. Enviar a Groq Vision (llama-3.3-70b con vision) o OpenRouter (gemini-2.0-flash)
#    c. Prompt de evaluación (ver abajo)
#    d. Parsear score numérico de la respuesta
#    e. Si score >= 7: mover a /approved/
#    f. Si score >= 9: mover a /approved/ y marcar como "premium"
#    g. Si score < 7: mover a /rejected/
# 3. Generar reporte JSON con stats

# PROMPT DE EVALUACIÓN:
JUDGE_PROMPT = """
Evalúa esta imagen anime del 1 al 10. Responde SOLO con un JSON:
{"score": N, "reason": "breve explicación"}

Criterios:
- Anatomía: ¿Manos correctas (5 dedos)? ¿Ojos simétricos? ¿Proporciones naturales?
- Composición: ¿Centrada? ¿Buen encuadre? ¿Pose dinámica?
- Calidad: ¿Detalles nítidos? ¿Sin artefactos? ¿Colores vibrantes?
- Estética: ¿Atractiva? ¿Profesional? ¿Publicable en Patreon?

Score < 5: Defectos graves (manos deformes, anatomía rota)
Score 5-6: Aceptable pero no destacable
Score 7-8: Buena calidad, publicable
Score 9-10: Premium, destacable, portada
"""

# API para Vision:
# - Groq: NO soporta vision (solo texto). No usar.
# - OpenRouter: Usar google/gemini-2.0-flash-exp:free (tiene vision)
# - Alternativa: OpenAI compatible con GPT-4o-mini (si tienen key)

# IMPORTANTE: Groq NO sirve para curación (no tiene vision).
# Usar OpenRouter con modelo que soporte imágenes.
```

**Modelos con Vision gratuitos (OpenRouter):**
- `google/gemini-2.0-flash-exp:free` ← Recomendado
- `meta-llama/llama-3.2-11b-vision-instruct:free`

### Paso 2: Crear `pipeline.py` (Orquestador)

**Archivo nuevo:** `scripts/pipeline.py`

```python
# pipeline.py SPEC

# Este script orquesta todo el pipeline:
# 1. Crea directorios temporales: /batch_TIMESTAMP/{raw, approved, rejected, premium}
# 2. Llama a factory.py para generar N imágenes en /raw/
# 3. Llama a curator.py para evaluar cada imagen
# 4. Mueve aprobadas a /approved/, rechazadas a /rejected/
# 5. Crea versiones con watermark en /watermarked/ (para gratis)
# 6. Empaqueta /approved/ en ZIP
# 7. Genera reporte final

# CLI:
# python pipeline.py --generate 50 --min-score 7 --output content/batches/

# Estructura de salida:
# content/batches/batch_20260209/
# ├── approved/          (imágenes buenas, sin watermark)
# ├── premium/           (score >= 9)
# ├── rejected/          (descartadas, para review manual)
# ├── watermarked/       (versiones con watermark para redes)
# ├── report.json        (stats del batch)
# └── batch_approved.zip (listo para subir a Patreon)
```

### Paso 3: Watermark Automático

```python
# En pipeline.py o como módulo separado

# Usar Pillow para agregar watermark:
# - Texto semi-transparente "Lady Nuggets" en esquina inferior
# - O logo PNG overlay
# - Las watermarked van a redes sociales (gratis)
# - Las originales van a Patreon (pago)

from PIL import Image, ImageDraw, ImageFont

def add_watermark(image_path, output_path, text="@LadyNuggets"):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    # Texto semi-transparente en esquina inferior derecha
    # Font size relativo al tamaño de imagen
    font_size = img.width // 20
    # Posición: esquina inferior derecha con padding
    # Color: blanco semi-transparente
    # ...implementar...
    img.save(output_path)
```

### Paso 4: Reporte de Batch

```json
// report.json ejemplo
{
  "batch_id": "batch_20260209_143000",
  "timestamp": "2026-02-09T14:30:00",
  "total_generated": 50,
  "approved": 12,
  "rejected": 38,
  "premium": 3,
  "approval_rate": "24%",
  "avg_score": 6.2,
  "top_themes": ["Cyberpunk", "Gothic Lolita", "Beach"],
  "generation_time_minutes": 25,
  "gpu": "RTX A6000",
  "model": "oneObsession_v19"
}
```

---

## Integración con `runpod_ultra.sh`

Modificar el script para que llame a `pipeline.py` en vez de `factory.py` directamente:

```bash
# En runpod_ultra.sh, cambiar la sección [7/7]:
# De:
python3 "$WORK_DIR/scripts/factory.py" --count "$IMAGE_COUNT" --output "$BATCH_DIR"
# A:
python3 "$WORK_DIR/scripts/pipeline.py" --generate "$IMAGE_COUNT" --min-score 7 --output "$BATCH_DIR"
```

---

## Dependencias Adicionales

```
# requirements.txt - agregar:
Pillow>=10.0.0   # Para watermarks
```

---

## Verificación

1. Generar 10 imágenes de prueba
2. Verificar que curator evalúa cada una con score
3. Verificar que las score >= 7 están en /approved/
4. Verificar que las watermarked tienen marca
5. Verificar que el ZIP se genera correctamente
6. Verificar que report.json tiene stats correctas

---

## Notas para el Agente

- **NO usar Groq para curación** - no soporta vision
- **Usar OpenRouter con Gemini Flash** - es gratis y soporta imágenes
- El watermark debe ser sutil pero visible - no arruinar la imagen
- El pipeline debe ser resiliente a fallos (si una imagen falla la evaluación, continuar con las demás)
- Guardar las rechazadas también (el owner puede querer revisarlas)
