# LadyNuggets HQ v1 (isolated package)

This package is fully isolated and does NOT modify the current active pipeline/workflow.

## Files
- comfy_hq_v1_api.json: ComfyUI API workflow (3-stage: base -> detail -> upscale)
- pipeline_hq_v1.json: New pipeline config template
- prompt_system_hq_v1.md: Prompt/copy/classification standard

## Where to use
1. Keep current pipeline untouched.
2. Duplicate current runtime config to a NEW runtime file if needed.
3. Wire this package in a separate integration step only after validation.

## Runtime env needed
- RUNPOD_API_KEY
- RUNPOD_ENDPOINT_ID
- DA credentials already present in enterprise config path.

## Notes
- Model names/checkpoints are placeholders and must match files installed in your Comfy runtime.
- Upscaler model `4x-UltraSharp.pth` must exist in Comfy upscaler models folder.
