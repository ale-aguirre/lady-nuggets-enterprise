# ☁️ Guía de Configuración en RunPod (Bajo Costo) v2

## 1. Conceptos Clave (Antes de Empezar)
*   **Community Cloud (Nube Comunitaria):** Son computadoras de usuarios particulares o empresas pequeñas. Son **mucho más baratas**. Úsalas siempre.
*   **Secure Cloud (Nube Segura):** Son centros de datos profesionales TIER 3/4. Son más caros y fiables. **NO** lo necesitas para este proyecto.
*   **¿Qué es "Spot"? (¡IMPORTANTE!):**
    *   Es como comprar un pasaje de avión en "lista de espera".
    *   Usas capacidad sobrante por un precio ridículo (ej. $0.19 en vez de $0.40).
    *   *Riesgo:* Alguien podría "quitarte" la máquina si paga el precio completo. (Pasa muy poco, y para generar imágenes no importa si se corta).

## 2. Eligiendo la GPU (La Batalla de Precios)

### ❌ NO RECOMENDADO:
*   **RTX 5090 ($0.79/hr):** Es un Ferrari para ir a comprar pan. Es para *entrenar* IA, no para *usarla*. No amortizarás el costo extra con velocidad.
*   **RTX 4070 Ti (12GB VRAM):** Muy poca memoria. SDXL + Hires Fix podría fallar.

### ✅ RECOMENDADO (Ranking Actualizado):
Busca en "Community Cloud" usando el filtro y activa el switch **"Spot"**:
1.  **RTX A4500 / A5000:** *(Si están disponibles, son las más baratas).*
2.  **RTX 3090 (24GB VRAM):** ~$0.30 - $0.34/hr. **Tu mejor opción ahora.** Es el estándar de la industria. Rápida y con memoria de sobra.
3.  **RTX 4090:** ~$0.45 - $0.60/hr. Solo úsala si no hay 3090 y tienes urgencia. Es muy rápida pero pagas el lujo.

## 3. Guía Visual: Cómo Desplegar
1.  Ve a **"Pods"** -> **"Deploy"**.
2.  En el filtro de arriba, selecciona **"Community Cloud"**.
    *   *Ignora la advertencia amarilla que dice "Choose Secure Cloud...". Es publicidad.*
3.  Busca la tarjeta **RTX A4500** (o la que elijas).
4.  Dale al botón que dice **"Deploy"** sobre esa tarjeta.
5.  **PERSONALIZAR (Customize Deployment):**
    *   **Template (Elige con cuidado):**
        *   En la barra de búsqueda escribe: **stable diffusion**
        *   Busca la tarjeta que se llama exactamente: **RunPod Stable Diffusion**
        *   Debajo del nombre dirá algo como: `runpod/stable-diffusion-webui:10.2.1`
        *   Tiene el cubo violeta de RunPod como logo. ¡Esa es la buena!
    *   **Container Disk:** Ponle al menos **20GB**-30GB (para que quepan tus modelos).
    *   **Volume Disk:** 20GB está bien.
6.  Dale a **"Continue"** -> **"Deploy"**.

## 4. Instalación (Solo la primera vez)
Cuando el Pod diga "Running" (corriendo), dale al botón **"Connect"** y luego a **"Jupyter Lab"**.
Se abrirá una ventana tipo carpeta de archivos. Abre la **Terminal** (icono negro abajo) y pega esto:

```bash
# 1. Clonar tu Proyecto
git clone https://github.com/ale-aguirre/lady-nuggets-enterprise.git

# 2. Entrar y Preparar
cd lady-nuggets-enterprise

# 3. Instalar librerías y ADETAILER (¡Importante!)
pip install -r requirements.txt

# Instalar Adetailer (Para que factory.py funcione perfecto)
cd /workspace/stable-diffusion-webui/extensions
git clone https://github.com/Bing-su/adetailer.git

# 4. Descargar el Modelo OneObsession (Directo de Civitai para no gastar tu internet)
cd /workspace/stable-diffusion-webui/models/Stable-diffusion
wget https://civitai.com/api/download/models/302970 --content-disposition
# (Nota: Verifica que ese sea el ID correcto del modelo OneObsession en Civitai, si no, cámbialo)
```

## 5. ¡A Generar!
```bash
# Volver a tu carpeta
cd /workspace/lady-nuggets-enterprise

# Generar 50 imágenes
python3 scripts/factory.py --count 50

# Empaquetar
./scripts/pack_images.sh
```
*(Luego descarga el ZIP y BORRA el Pod).*
