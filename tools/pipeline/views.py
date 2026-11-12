"""Turnaround views of a creature for 3D: front (given), left, back, right (Qwen Image 2.1).

    .venv/bin/python tools/pipeline/views.py <slug> <front image> [--seed N] [--only left,back] [--extra TEXT]

Writes art/pipeline/<slug>/views/{front,left,back,right}.png (left = facing the right edge of
the picture, right = facing the left edge, as homm3/model-from-views expects). The front image
should be a neutral A-pose on a plain background. Check every view by eye before modelling:
same character, outfit and proportions in all four, nothing extra or missing.
"""
import argparse, pathlib, shutil, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comfy

ROOT = pathlib.Path(__file__).resolve().parents[2]

KEEP = ('Keep everything else exactly the same: the same character, the same neutral A-pose with the arms '
        'held out from the body, the same outfit, colors, materials, hair, accessories and proportions. '
        'Full body from the top of the head to the feet, the same height as in the reference, centered, '
        'feet on the same level. Plain light grey background, even studio lighting, no cast shadow, '
        'nothing else in the picture. A clean character turnaround view.')
PROMPTS = {
    'left': 'Rotate the character 90 degrees so we see a full side view, facing the right edge of the image. ' + KEEP,
    'back': 'Rotate the character 180 degrees so we see the full back view: the character faces away from us. ' + KEEP,
    'right': 'Rotate the character 90 degrees so we see a full side view, facing the left edge of the image. ' + KEEP,
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('front')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--only', default='left,back,right')
    ap.add_argument('--extra', default='', help='design facts every view must keep (what the back looks like, carried items)')
    a = ap.parse_args()
    out = ROOT / 'art' / 'pipeline' / a.slug / 'views'
    out.mkdir(parents=True, exist_ok=True)
    shutil.copy(a.front, out / 'front.png')
    work = out / 'raw'
    for view in a.only.split(','):
        saved = comfy.run('unit-views', {
            ('reference', 'image'): a.front,
            ('prompt', 'prompt'): PROMPTS[view] + (' ' + a.extra if a.extra else ''),
            ('seed', 'noise_seed'): a.seed,
            ('save', 'filename_prefix'): f'homm3/{a.slug}/{view}',
        }, work)
        files = [p for paths in saved.values() for p in paths]
        shutil.copy(files[0], out / f'{view}.png')
        print(view, '->', out / f'{view}.png')

if __name__ == '__main__':
    main()
