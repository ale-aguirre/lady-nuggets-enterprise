# ☁️ Guía de Migración a RunPod (Lady Nuggets Enterprise)

Esta guía te explica cómo mover tu operación a la nube para liberar tu Mac y generar a máxima velocidad.

## 1. Configuración Inicial
1.  Ve a [RunPod.io](https://runpod.io) y crea una cuenta.
2.  Carga saldo (Mínimo $10 o $25 USD).
3.  Ve a **Community Cloud** (es más barato).

## 2. Eligiendo la Máquina (Pod)
1.  Haz clic en **Deploy**.
2.  Selecciona GPU: **NVIDIA RTX 3090** (Mejor calidad/precio, ~$0.24/hora).
3.  **Template (Plantilla)**: Esto es clave.
    *   Busca: `runpod/stable-diffusion:webui` (Trae Automatic1111 pre-instalado).
    *   O mejor aún: `runpod/stable-diffusion:comfyui` si prefieres ComfyUI (pero nuestro script usa A1111/ReForge).
    *   *Recomendación:* Usa **RunPod Stable Diffusion WebUI**.

## 3. Configuración del Pod
*   **Container Disk**: 20GB (Mínimo para el sistema).
*   **Volume Disk**: 40GB (Aquí guardas tus modelos y salidas. Esto persiste aunque apagues el Pod).
*   Haz clic en **Deploy**.

## 4. Conectando "Lady Nuggets"
Una vez que el Pod esté "Running":
1.  Haz clic en **Connect** > **Jupyter Lab** (Te abre una terminal web).
2.  Abre la terminal en Jupyter y clona tu repo (o sube los scripts):
    ```bash
    git clone https://github.com/tusuario/lady-nuggets-enterprise.git
    cd lady-nuggets-enterprise
    pip install -r requirements.txt
    ```
3.  **Modelos**:
    *   Tendrás que descargar tu checkpoint (`HassakuXL...`) en la carpeta `models/Stable-diffusion` del Pod.
    *   Puedes usar `wget` para descargarlo directo de Civitai (mucho más rápido que subirlo).

## 5. Ejecución Remota
1.  Edita `config/.env` en el Pod con tus claves.
2.  Corre el script igual que en tu Mac:
    ```bash
    python3 scripts/factory.py
    ```

## 6. ¡IMPORTANTE! Ahorro de Costos 💸
*   **Stop (Detener)**: El Pod se apaga (no cobra GPU) pero te siguen cobrando el disco (~$0.01/hora). Úsalo si vas a volver mañana.
*   **Terminate (Destruir)**: Borra TODO. Deja de cobrarte 100%. Úsalo si ya terminaste todo y respaldaste tus imágenes.

**Tip Pro:** Usa `scp` para bajar las imágenes a tu Mac:
```bash
scp -r root@ip-del-pod:/workspace/lady-nuggets/content/raw ./Descargas/Nuggets
```
