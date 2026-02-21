#!/usr/bin/env python3
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from pathlib import Path


def http_json(method: str, url: str, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))


def http_download(url: str, out_path: Path):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=300) as r:
        out_path.write_bytes(r.read())


def main():
    root = Path(__file__).resolve().parent
    workflow_file = root.parent / "comfy_hq_v1_api.json"
    out_dir = root.parent / "test_output"
    out_dir.mkdir(parents=True, exist_ok=True)

    comfy_env = os.environ.get("COMFY_BASE_URL", "").strip()
    comfy_candidates = [comfy_env] if comfy_env else ["http://127.0.0.1:8188", "http://127.0.0.1:3000"]
    comfy = None
    for c in comfy_candidates:
      if not c:
          continue
      c = c.rstrip("/")
      try:
          _ = http_json("GET", f"{c}/object_info")
          comfy = c
          break
      except Exception:
          continue
    if comfy is None:
      print("[test] no reachable Comfy API. Set COMFY_BASE_URL explicitly.")
      sys.exit(4)
    prompt_text = os.environ.get(
        "TEST_PROMPT",
        "masterpiece, best quality, ultra detailed anime style, adult woman inspired by sailor moon, "
        "blonde twin tails, sailor uniform redesign, beach sunset, dynamic pose, cinematic lighting, "
        "sharp eyes, high contrast, clean lineart, no child, mature proportions",
    )
    seed = int(os.environ.get("TEST_SEED", str(random.randint(1, 2_147_483_647))))

    object_info = http_json("GET", f"{comfy}/object_info")
    ckpt_list = (
        object_info.get("CheckpointLoaderSimple", {})
        .get("input", {})
        .get("required", {})
        .get("ckpt_name", [[]])[0]
        or []
    )
    upscaler_list = (
        object_info.get("UpscaleModelLoader", {})
        .get("input", {})
        .get("required", {})
        .get("model_name", [[]])[0]
        or []
    )

    target_ckpt = "hassakuXLIllustrious_v34.safetensors"
    if target_ckpt not in ckpt_list:
        if "sd_xl_base_1.0.safetensors" in ckpt_list:
            target_ckpt = "sd_xl_base_1.0.safetensors"
        elif ckpt_list:
            target_ckpt = ckpt_list[0]
    target_upscaler = "RealESRGAN_x4plus_anime_6B.pth"
    can_hq = target_upscaler in upscaler_list and target_ckpt in ckpt_list

    print(f"[test] available_ckpt={ckpt_list}")
    print(f"[test] available_upscalers={upscaler_list}")
    print(f"[test] target_ckpt={target_ckpt}")
    print(f"[test] target_upscaler={target_upscaler} can_hq={can_hq}")

    wf = json.loads(workflow_file.read_text())
    wf["1"]["inputs"]["ckpt_name"] = target_ckpt
    wf["10"]["inputs"]["model_name"] = target_upscaler
    wf["2"]["inputs"]["batch_size"] = 1
    wf["3"]["inputs"]["text"] = prompt_text
    wf["5"]["inputs"]["seed"] = seed
    wf["8"]["inputs"]["seed"] = seed + 1

    print(f"[test] comfy={comfy}")
    print(f"[test] seed={seed}")

    def try_submit(prompt_wf, label: str):
        try:
            created_local = http_json("POST", f"{comfy}/prompt", {"prompt": prompt_wf})
            print(f"[test] submit ok ({label})")
            return created_local
        except HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            print(f"[test] submit failed ({label}) -> HTTP {e.code}")
            if body:
                print(f"[test] error body: {body[:1200]}")
            return None

    created = try_submit(wf, "hq_workflow") if can_hq else None
    if not can_hq:
        print("[test] hq skipped (checkpoint/upscaler not available in API list)")
    if created is None:
        print("[test] fallback -> basic workflow")
        basic_neg = (
            "worst quality, low quality, blurry, bad anatomy, bad hands, extra fingers, "
            "watermark, text, logo, child, loli"
        )
        wf = {
            "1": {"inputs": {"ckpt_name": target_ckpt}, "class_type": "CheckpointLoaderSimple"},
            "2": {"inputs": {"width": 832, "height": 1216, "batch_size": 1}, "class_type": "EmptyLatentImage"},
            "3": {"inputs": {"text": prompt_text, "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
            "4": {"inputs": {"text": basic_neg, "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
            "5": {
                "inputs": {
                    "seed": seed,
                    "steps": 28,
                    "cfg": 6.0,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["3", 0],
                    "negative": ["4", 0],
                    "latent_image": ["2", 0],
                },
                "class_type": "KSampler",
            },
            "6": {"inputs": {"samples": ["5", 0], "vae": ["1", 2]}, "class_type": "VAEDecode"},
            "7": {"inputs": {"filename_prefix": "LadyNuggets_HQ_v1_test", "images": ["6", 0]}, "class_type": "SaveImage"},
        }
        created = try_submit(wf, "basic_workflow")
        if created is None:
            print("[test] both workflows failed")
            sys.exit(5)

    prompt_id = created["prompt_id"]
    print(f"[test] prompt_id={prompt_id}")

    deadline = time.time() + 600
    result = None
    while time.time() < deadline:
        hist = http_json("GET", f"{comfy}/history/{prompt_id}")
        item = hist.get(prompt_id)
        if item and item.get("outputs"):
            result = item
            break
        time.sleep(2)

    if result is None:
        print("[test] timeout waiting for comfy history")
        sys.exit(2)

    images = []
    for node in result.get("outputs", {}).values():
        for img in node.get("images", []):
            images.append(img)

    if not images:
        print("[test] no output images found")
        sys.exit(3)

    first = images[0]
    qs = urllib.parse.urlencode(
        {
            "filename": first["filename"],
            "subfolder": first.get("subfolder", ""),
            "type": first.get("type", "output"),
        }
    )
    view_url = f"{comfy}/view?{qs}"
    ts = int(time.time())
    out_file = out_dir / f"hq_test_{ts}.png"
    http_download(view_url, out_file)

    print(f"[test] ok -> {out_file}")


if __name__ == "__main__":
    main()
