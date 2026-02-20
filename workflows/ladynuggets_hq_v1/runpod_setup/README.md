# Runpod Pod Setup (Comfy Anime HQ)

## 1) En Runpod UI (Pods)
- GPU: **RTX 4090 (24GB)** (si no hay, usar L40S)
- Template (ID recomendado): **`runpod-comfy`** (`Runpod ComfyUI`)
- Alternativa: `cw3nka7d08` (`ComfyUI`)
- Network Volume: **120-200 GB**
- Container disk: **30+ GB**
- Auto-stop idle: **30 min**
- Exponer puertos: `8188` (Comfy API/UI), `22` (SSH opcional)

### Spot vs On-Demand (importante)
- **Primera vez (setup + descarga de modelos):** usa **On-Demand**.
- Cuando ya tenes modelos en volumen persistente: cambia a **Spot** para bajar costo.
- Si Spot corta la instancia, el volumen persiste y no perdés checkpoints.

## 2) En el terminal del Pod
```bash
cd /workspace
bash runpod_setup/bootstrap_comfy_pod.sh
cp runpod_setup/models.env.example runpod_setup/models.env
# Solo completa CIVITAI_TOKEN (las URLs base ya vienen preconfiguradas)
bash runpod_setup/download_models.sh runpod_setup/models.env
bash runpod_setup/verify_models.sh
```

## 3) Conectar Nuggets al Comfy Pod
En Nuggets `.env`:
- `COMFY_BASE_URL=https://<tu-pod>-8188.proxy.runpod.net`
- `COMFY_API_MODE=pod`

Luego reinicia Nuggets.

## Notas
- El script soporta Civitai con token (`CIVITAI_TOKEN`) y URLs directas.
- Si un modelo no descarga, revisa URL y permisos del token.
