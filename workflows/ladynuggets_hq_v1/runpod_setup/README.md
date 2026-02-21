# Runpod Pod Setup (Comfy Anime HQ)

## Quick Start (recomendado)
```bash
cd /workspace/lady-nuggets-enterprise/workflows/ladynuggets_hq_v1/runpod_setup
git pull
CIVITAI_TOKEN=TU_TOKEN bash runpod_master.sh all
```

Comandos individuales:
```bash
bash runpod_master.sh init
CIVITAI_TOKEN=TU_TOKEN bash runpod_master.sh models
bash runpod_master.sh sync
bash runpod_master.sh cleanup
bash runpod_master.sh verify
bash runpod_master.sh test
```

Test con prompt custom:
```bash
TEST_PROMPT="adult anime woman inspired by sailor moon, beach sunset, cinematic lighting" bash runpod_master.sh test
```

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

Ahora equivalente con script maestro:
```bash
cd /workspace/lady-nuggets-enterprise/workflows/ladynuggets_hq_v1/runpod_setup
CIVITAI_TOKEN=TU_TOKEN bash runpod_master.sh all
```

## 3) Conectar Nuggets al Comfy Pod
En Nuggets `.env`:
- `COMFY_BASE_URL=https://<tu-pod>-8188.proxy.runpod.net`
- `COMFY_API_MODE=pod`

Luego reinicia Nuggets.

## Notas
- El script soporta Civitai con token (`CIVITAI_TOKEN`) y URLs directas.
- Si un modelo no descarga, revisa URL y permisos del token.
