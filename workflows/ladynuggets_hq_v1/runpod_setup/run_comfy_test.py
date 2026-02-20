#!/usr/bin/env python3
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
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

    wf = json.loads(workflow_file.read_text())
    wf["1"]["inputs"]["ckpt_name"] = "hassakuXLIllustrious_v34.safetensors"
    wf["10"]["inputs"]["model_name"] = "RealESRGAN_x4plus_anime_6B.pth"
    wf["2"]["inputs"]["batch_size"] = 1
    wf["3"]["inputs"]["text"] = prompt_text
    wf["5"]["inputs"]["seed"] = seed
    wf["8"]["inputs"]["seed"] = seed + 1

    print(f"[test] comfy={comfy}")
    print(f"[test] seed={seed}")

    created = http_json("POST", f"{comfy}/prompt", {"prompt": wf})
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
