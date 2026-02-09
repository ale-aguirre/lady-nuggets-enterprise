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

## 2. Instalación y Ejecución (Todo en Uno)
Cuando el Pod diga "Running", dale a **"Connect"** -> **"Jupyter Lab"**, abre la **Terminal** y pega esto:

```bash
# 1. Traer el código
git clone https://github.com/ale-aguirre/lady-nuggets-enterprise.git
cd lady-nuggets-enterprise

# 2. EJECUTAR EL ULTRA SCRIPT (Auto-detecta todo)
chmod +x scripts/runpod_ultra.sh
./scripts/runpod_ultra.sh --count 6
```

*El `--count 6` al final es la cantidad de imágenes. Cámbialo si quieres más.*

> **💡 Opciones adicionales:**
> - `./scripts/runpod_ultra.sh --help` → Ver todas las opciones
> - `./scripts/runpod_ultra.sh --no-model` → Saltar descarga de modelo
> - `./scripts/runpod_ultra.sh --verbose` → Más detalles

## 3. Finalizar
1.  Cuando el script termine, verás un archivo `.zip` en la lista de la izquierda.
2.  Click derecho -> **Download**.
3.  Ve al Dashboard de RunPod y **TERMINA** el Pod (Icono de Basura).
