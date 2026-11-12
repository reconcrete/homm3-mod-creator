"""3D model of a creature from its four checked views (homm3/model-from-views, Pixal3D multi-view).

    .venv/bin/python tools/pipeline/model.py <slug> [--seed N]

Reads art/pipeline/<slug>/views/{front,left,back,right}.png, writes art/pipeline/<slug>/model/
model.glb and a turntable check sheet (model/turntable.png, textured and clay). Check the sheet
by eye before rigging: no holes, blobs or fused limbs, nothing missing that the views show.
"""
import argparse, pathlib, shutil, subprocess, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comfy

ROOT = pathlib.Path(__file__).resolve().parents[2]
BLENDER = '/Applications/Blender.app/Contents/MacOS/Blender'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--seed', type=int, default=None, help='seed of the shape sampler (template default 56)')
    a = ap.parse_args()
    base = ROOT / 'art' / 'pipeline' / a.slug
    out = base / 'model'
    inputs = {(v, 'image'): str(base / 'views' / f'{v}.png') for v in ('front', 'left', 'back', 'right')}
    inputs[('save model', 'filename_prefix')] = f'homm3/{a.slug}/model'
    saved = comfy.run('model-from-views', inputs, out / 'raw', timeout=3 * 3600)
    glbs = [p for paths in saved.values() for p in paths if p.suffix == '.glb']
    shutil.copy(glbs[0], out / 'model.glb')
    print('model ->', out / 'model.glb')
    r = subprocess.run([BLENDER, '-b', '-P', str(ROOT / 'tools/pipeline/turntable.py'), '--',
                        str(out / 'model.glb'), str(out / 'turntable.png'), 'turn=180'], capture_output=True, text=True)
    print('\n'.join(l for l in r.stdout.splitlines() if l.startswith(('MESH', 'SHEET'))) or r.stdout[-2000:] + r.stderr[-2000:])

if __name__ == '__main__':
    main()
