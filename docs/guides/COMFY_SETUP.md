# 🎱 Guía de Setup: ComfyUI & High-End Workflows

## 1. Instalación en RunPod
Cuando alquiles un Pod (GPU), elige una plantilla que ya tenga **ComfyUI**.
*   **Recomendado**: `RunPod SDXL + ComfyUI` o `ComfyUI (Community)`.
*   **Vital**: Asegúrate de que tenga **ComfyUI Manager** instalado (suele venir por defecto, si no, es un `git clone` fácil).

## 2. El "Prompt Maestro" para Claude Sonnet 4.5
Copia y pega esto en Claude para que te genere los workflows JSON exactos que necesitamos.

```text
Actúa como un Ingeniero Senior en Generación de Imágenes con ComfyUI.
Necesito que construyas un workflow en formato JSON (API format) para Anime High-End.

**Requisitos del Workflow:**
1. **Model Loader**: Debe cargar un checkpoint SDXL o Pony Diffusion (ej. "waiIllustrious").
2. **Prompting**: Dos nodos CLIP Text Encode (Positivo y Negativo).
3. **Sampling**: Nodo KSampler (Euler a / DPM++ 2M Karras, 25-30 steps).
4. **Resolution**: Empty Latent Image a 1216x832 (Portrait).
5. **Face Refiner (Vital)**: Usa el nodo "FaceDetailer" (de Impact Pack) para detectar y mejorar caras automáticamente.
6. **Upscale**: Un paso final de "Image Scale to Total Pixels" (x1.5 o x2.0) para alta resolución.
7. **Output**: Save Image.

**IMPORTANTE:**
- Usa IDs de nodos estándar.
- Devuélveme SOLO el JSON válido, listo para guardar como "workflow_api.json".
- No expliques cada nodo, solo dame el JSON.
```

## 3. Instalación de Nodos en ComfyUI
Una vez tengas el JSON de Claude:
1.  Abre tu ComfyUI en el navegador.
2.  Arrastra el archivo JSON a la ventana.
3.  Si salen nodos rojos (faltantes), abre "Manager" -> "Install Missing Custom Nodes".
4.  Reinicia ComfyUI.
