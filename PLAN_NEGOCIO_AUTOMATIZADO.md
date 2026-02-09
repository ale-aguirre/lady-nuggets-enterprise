# Master Plan: "Lady Nuggets Enterprise" (Day 1 Scalable)

**Filosofía**: "Zero-Touch Operation". Tú eres el dueño, Neko es el CEO operativo.
**Restricción Técnica**: 100% Scripts (Python/JS). 0% n8n/Make.

## 1. El "Curador" (The AI Art Director)
**Problema**: Generar es fácil, filtrar basura es difícil.
**Solución**: Script `curator.py`.
*   **Funcionamiento**:
    1.  ReForge genera lote de 10 imágenes.
    2.  `curator.py` envía cada imagen a GPT-4o-Vision / Gemini Pro Vision.
    3.  **Prompt de Juez**: *"Evalúa esta imagen del 1 al 10 en base a: Anatomía correcta (manos/ojos), Estética Maison Noire, Iluminación. Si es < 7, descártala. Si es > 9, márcala 'Premium'."*
    4.  Solo las > 7 pasan a la etapa de publicación.

## 2. La Fábrica (Content Pipeline)
**Herramienta**: Stable Diffusion ReForge (API mode).
*   **Script**: `factory_manager.py`.
    *   Lee "Ideas" de un archivo de texto (`themes.txt`).
    *   Genera prompts aleatorios basados en tu lógica de Kage ("Gothic Maid", "Future Cyberpunk", etc.).
    *   Envía a ReForge API.
    *   Pasa al **Curador**.
    *   Guarda en: `/Output/Ready_To_Post` o `/Output/Rejected`.

## 3. El Distribuidor (Social Media Manager)
**Herramienta**: Neko / OpenClaw (Scripts personalizados).
*   **Script**: `social_poster.py`.
    *   **Twitter/X**: Usa API v2. Sube imagen premium + texto generado por LLM ("Miren esta belleza...").
    *   **DeviantArt**: Usa API oficial. Sube imagen + tags + link a Patreon.
    *   **Patreon**: (Si la API es compleja, usamos Selenium/Puppeteer scripts). Sube el pack "High Res" para suscriptores.
*   **Interacción**:
    *   Script `reply_bot.py`: Lee comentarios cada hora. Usa LLM para generar respuestas cortas y amables ("Gracias! ❤️", "Pronto más en Patreon!").

## 4. El Community Manager (Discord)
**Herramienta**: Bot de Discord personalizado (alojado en tu PC/VPS).
*   **Funciones**:
    *   **Bienvenida**: Mensaje DM automático con guía de inicio.
    *   **Moderar**: Auto-borrado de spam/links.
    *   **Engagement**: "Daily Waifu". El bot postea una imagen del "Curador" en `#general` preguntando "¿Opiniones?".
    *   **Soporte**: Responde preguntas básicas ("¿Precios?", "¿Comisiones?") usando una base de conocimientos.

## 5. El Negocio (Money Flow)
*   **Producto**:
    *   **Gratis**: Imágenes curadas (baja res/watermark) en Twitter/DA.
    *   **$5/mes**: Acceso a la carpeta "High Res" (autopublicada en Patreon).
    *   **$15/mes**: Acceso al Bot Generador en Discord (Tú pones el prompt, tu ReForge genera).
*   **Web**: Reemplazar Carrd con una landing simple en GitHub Pages (generada por nosotros), limpia y profesional.

## 6. Preguntas Clave para Ti (El Dueño)
Para configurar el "Curador" y el "Manager":
1.  **Criterio de Calidad**: ¿Qué detalles hacen que borres una imagen inmediatamente? (Ej: ¿Manos con 6 dedos? ¿Ojos bizcos? ¿Colores lavados?).
2.  **Personalidad**: ¿Cómo habla Lady Nuggets? ¿Es una IA fría y eficiente? ¿Una chica anime entusiasta? ¿Una "Dominatrix" elegante? Esto define los scripts de respuesta.
3.  **Infraestructura**: ¿Tienes una PC que pueda estar encendida 24/7 generando y sirviendo el bot, o necesitas que configuremos esto para un VPS (servidor alquilado)?

---

**Siguiente Paso**: Si apruebas esta arquitectura "Script-Only", empezaré creando el `curator.py` para probar tu API de ReForge.
