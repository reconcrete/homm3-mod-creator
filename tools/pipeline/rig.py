"""Rig a model with SkinTokens / TokenRig (skeleton + skin weights) on the GPU server.

    .venv/bin/python tools/pipeline/rig.py <slug> [--model model-30k.glb]

Reads art/pipeline/<slug>/model/<model>, writes art/pipeline/<slug>/rig/rigged.glb. ComfyUI's
models are unloaded first: SkinTokens and ComfyUI share the 12 GB card. Server address:
SKINTOKENS_URL or "skintokens_url" in tools/pipeline/local.json. Check the rig by eye
(rigcheck.py) before animating it.
"""
import argparse, os, pathlib, shutil, sys, time

import requests
from gradio_client import Client, handle_file

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comfy

ROOT = pathlib.Path(__file__).resolve().parents[2]
URL = (os.environ.get('SKINTOKENS_URL') or comfy.config().get('skintokens_url') or 'http://127.0.0.1:7860').rstrip('/')

def rig(src, dest):
    requests.post(comfy.URL + '/free', json={'unload_models': True, 'free_memory': True}, timeout=60)
    client = Client(URL + '/', verbose=False)
    t0 = time.time()
    status, glb = client.predict(
        [handle_file(str(src))],
        5, 0.95, 1.0, 2.0, 3,          # top_k, top_p, temperature, repetition_penalty, num_beams (the app's defaults)
        False,                          # use an existing skeleton
        True,                           # transfer: keep the texture
        False,                          # voxel skin post-process
        'experiments/articulation_xl_quantization_256_token_4/grpo_1400.ckpt', 'None',
        api_name='/run_gradio')
    print(f'  rigged in {time.time() - t0:.0f} s: {status}')
    path = glb[0] if isinstance(glb, (list, tuple)) else glb
    path = path.get('path', path) if isinstance(path, dict) else path
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, dest)
    return dest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--model', default='model-30k.glb')
    a = ap.parse_args()
    base = ROOT / 'art' / 'pipeline' / a.slug
    print('rig ->', rig(base / 'model' / a.model, base / 'rig' / 'rigged.glb'))

if __name__ == '__main__':
    main()
