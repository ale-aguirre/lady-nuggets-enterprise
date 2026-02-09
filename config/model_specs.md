# OneObsession / Illustrious Recommended Settings (Analyzed/Extracted)

## 🎨 Quality Boosters (Positive Prompt)
(EyesHD:1.2), (4k,8k,Ultra HD), ultra-detailed, sharp focus, ray tracing, best lighting, detailed illustration, detailed background, cinematic, beautiful face, beautiful eyes, ambient occlusion, soft lighting, absolutely eye-catching, intricate cinematic background, masterpiece, best quality, amazing quality, depth of field, high contrast, colorful depth, chiaroscuro

## 🚫 Negative Prompt (Universal)
anatomical nonsense, interlocked fingers, extra fingers, watermark, simple background, transparent, low quality, logo, text, signature, (worst quality, bad quality:1.2), jpeg artifacts, username, censored, extra digit, ugly, bad_hands, bad_feet, bad_anatomy, deformed anatomy, bad proportions, lowres, bad_quality

## ⚙️ Generation Parameters
- **Steps**: 20 - 30 (Use 28 for balance)
- **CFG Scale**: 5.0 - 6.0
- **Sampler**: Euler a (Crucial for this model)
- **Resolution**: 832x1216 (Portrait) | 1024x1536 (High Res)
- **Hires Fix**:
    - Upscaler: R-ESRGAN 4x+ Anime6B
    - Denoising: 0.35 - 0.4
    - Steps: 15
- **Adetailer**:
    - Model: face_yolov8n.pt
    - Confidence: 0.3
    - Denoising: 0.35 - 0.4
