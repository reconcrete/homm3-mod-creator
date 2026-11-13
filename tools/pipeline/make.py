"""Take one creature of plan.py through the self-hosted pipeline, one checked step at a time.

    .venv/bin/python tools/pipeline/make.py <slug> <step> [options]

Steps (each ends with a sheet to look at; never go on before the sheet passes the eye check):
    apose [--seeds 1,2,3]   A-pose front candidates from the artist's still (Qwen) -> apose/sheet.png
    pick N                  use candidate N as the front (front.png)
    views [--seed N] [--only left,back]   turnaround views (views.py) -> views-sheet.png
    viewcands --only back --seeds 2,3,4 [--hint TEXT]   more candidates for failed views
    pickview --view back:3[:m]  use a candidate (m: mirrored)
    model                   Pixal3D model, 30k-face copy and turntables -> model/turntable*.png
    rig                     SkinTokens rig and rig check -> rig/check-{skeleton,weights,poses}.png
    anim                    motions from the plan's source, battle frames, sheets next to the source
                            (anim/compare.png, anim/closeups.png at full size) and the RENDERED entry
Files go to art/pipeline/<slug>/.
"""
import argparse, os, pathlib, shutil, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comfy
import plan

ROOT = pathlib.Path(__file__).resolve().parents[2]
BLENDER = '/Applications/Blender.app/Contents/MacOS/Blender'
PY = sys.executable
GREY = (224, 224, 224)

APOSE = ('Redraw this exact character as a clean full-body front view for a 3D character turnaround. '
         'The character stands straight and faces the viewer directly, in a neutral A-pose: the arms '
         'straight and held out about 30 degrees from the body, the hands relaxed, the legs straight, the '
         'feet slightly apart and flat on the ground. Keep the same character exactly: the same face, '
         'outfit, colors, materials, hair, accessories and body proportions. No action, no effects, no '
         'motion lines. Full body from the top of the head to the feet, centered, filling most of the '
         'height. Plain light grey background, even studio lighting, no cast shadow, nothing else in the '
         'picture.')

FRONT_POSE = {
    'apose': APOSE,
    'animal': ('Redraw this exact creature as a clean full-body front view for a 3D character turnaround: it '
               'faces the viewer directly and stands in a neutral, calm pose on all its legs, the head level, the '
               'tail relaxed. Keep the same creature exactly: the same face, colors, markings, materials, '
               'accessories and body proportions. No action, no effects. Full body, centered, filling most of the '
               'picture. Plain light grey background, even studio lighting, no cast shadow, nothing else in the '
               'picture.'),
    'serpent': ('Redraw this exact creature as a clean full-body front view for a 3D character turnaround: it '
                'faces the viewer directly, its body coiled on the ground and its head raised calmly, mouth '
                'closed. Keep the same creature exactly: the same head, colors, stripes, scales and proportions. '
                'No action, no effects. Full body, centered, filling most of the picture. Plain light grey '
                'background, even studio lighting, no cast shadow, nothing else in the picture.'),
}

def run(*cmd, keep=('SHEET', 'WROTE', 'MESH', 'DECIMATED', 'HIP', 'RENDERED', 'MAP', 'HANDS', 'SEPARATED',
                    'Error', 'Traceback', 'differ', 'rig ->', 'model ->', ' -> ', 'rigged')):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, cwd=ROOT)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if any(k in l for k in keep)]
    print('\n'.join(l[:160] for l in lines))
    if r.returncode != 0 or any('Traceback' in l or 'Error' in l and 'MISSING' not in l for l in lines):
        print((r.stdout + r.stderr)[-3000:])
        sys.exit(f'step failed: {cmd[:4]}')
    return r.stdout

def blender(script, *args):
    return run(BLENDER, '-b', '-P', ROOT / script, '--', *args)

def label_sheet(items, path, tile=384):
    """items: [(image path, label)] in one row"""
    sheet = Image.new('RGB', (tile * len(items), tile + 22), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for i, (p, text) in enumerate(items):
        im = Image.open(p).convert('RGBA')
        bg = Image.new('RGBA', im.size, GREY + (255,)); bg.alpha_composite(im)
        im = bg.convert('RGB'); im.thumbnail((tile, tile))
        sheet.paste(im, (i * tile + (tile - im.width) // 2, 22 + (tile - im.height) // 2))
        d.text((i * tile + 6, 5), text, fill=(255, 255, 0))
    sheet.save(path)
    print('SHEET', path)

def front_of(slug, base):
    p = plan.PLAN[slug].get('front')
    if p and (ROOT / p).exists():
        return ROOT / p
    if (base / 'front.png').exists():
        return base / 'front.png'
    sys.exit(f'{slug}: no A-pose front yet: run the apose step and pick one')

def step_apose(slug, base, a):
    src = ROOT / 'art' / 'inbox' / f'creature-{slug}.png'
    im = Image.open(src).convert('RGBA')
    bb = im.getbbox()
    im = im.crop(bb)
    side = int(max(im.size) * 1.12)
    canvas = Image.new('RGBA', (side, side), GREY + (255,))
    canvas.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    out = base / 'apose'
    out.mkdir(parents=True, exist_ok=True)
    still = out / 'still.png'
    canvas.convert('RGB').save(still)
    extra = plan.PLAN[slug].get('extra', '')
    items = [(still, 'artist still')]
    for seed in [int(s) for s in a.seeds.split(',')]:
        saved = comfy.run('unit-views', {
            ('reference', 'image'): str(still),
            ('prompt', 'prompt'): FRONT_POSE[plan.PLAN[slug].get('pose', 'apose')] + (' ' + extra if extra else ''),
            ('seed', 'noise_seed'): seed,
            ('save', 'filename_prefix'): f'homm3/{slug}/apose',
        }, out / 'raw')
        files = [p for paths in saved.values() for p in paths]
        shutil.copy(files[0], out / f'seed-{seed}.png')
        items.append((out / f'seed-{seed}.png', f'seed {seed}'))
    label_sheet(items, out / 'sheet.png', tile=512)

def step_pick(slug, base, a):
    shutil.copy(base / 'apose' / f'seed-{a.n}.png', base / 'front.png')
    print('front ->', base / 'front.png')

def step_views(slug, base, a):
    args = [PY, ROOT / 'tools/pipeline/views.py', slug, front_of(slug, base), '--seed', a.seed, '--only', a.only]
    args += ['--pose', plan.PLAN[slug].get('pose', 'apose')]
    if plan.PLAN[slug].get('extra'):
        args += ['--extra', plan.PLAN[slug]['extra']]
    run(*args)
    v = base / 'views'
    label_sheet([(v / f'{n}.png', n) for n in ('front', 'left', 'back', 'right')], base / 'views-sheet.png')

def step_viewcands(slug, base, a):
    """Several seeds of the views that failed the check -> views/cand/<view>-<seed>.png and a sheet."""
    import views as V
    p = plan.PLAN[slug]
    front = front_of(slug, base)
    out = base / 'views' / 'cand'
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for view in a.only.split(','):
        items = [(front, 'front')]
        for seed in [int(x) for x in a.seeds.split(',')]:
            prompt = V.SIDES[view] + V.KEEP.format(pose=V.POSES[p.get('pose', 'apose')]) + \
                (' ' + a.hint if a.hint else '') + (' ' + p['extra'] if p.get('extra') else '')
            saved = comfy.run('unit-views', {
                ('reference', 'image'): str(front), ('prompt', 'prompt'): prompt,
                ('seed', 'noise_seed'): seed, ('save', 'filename_prefix'): f'homm3/{slug}/{view}',
            }, out / 'raw')
            f = [q for paths in saved.values() for q in paths][0]
            shutil.copy(f, out / f'{view}-{seed}.png')
            items.append((out / f'{view}-{seed}.png', f'{view} seed {seed}'))
        label_sheet(items, out / f'{view}-sheet.png', tile=320)

def step_pickview(slug, base, a):
    view, seed, *flags = a.view.split(':')   # view:seed[:m]; m mirrors it (a back view that copied
    im = Image.open(base / 'views' / 'cand' / f'{view}-{seed}.png')   # a held prop onto the front's side)
    if 'm' in flags:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im.save(base / 'views' / f'{view}.png')
    v = base / 'views'
    label_sheet([(v / f'{n}.png', n) for n in ('front', 'left', 'back', 'right')], base / 'views-sheet.png')

def step_model(slug, base, a):
    run(PY, ROOT / 'tools/pipeline/model.py', slug)
    m = base / 'model'
    blender('tools/pipeline/decimate.py', m / 'model.glb', m / 'model-30k.glb')
    blender('tools/pipeline/turntable.py', m / 'model-30k.glb', m / 'turntable-30k.png', 'turn=0')

def step_rig(slug, base, a):
    run(PY, ROOT / 'tools/pipeline/rig.py', slug)
    blender('tools/pipeline/rigcheck.py', base / 'rig' / 'rigged.glb', base / 'rig' / 'check', 'front=-y')

def frames_of(root, action):
    d = pathlib.Path(root) / action
    return sorted(d.glob('*.png')) if d.is_dir() else []

def compare_sheet(new_root, src_root, path, cols=12, cw=225, ch=200):
    acts = ['idle', 'walk', 'attack', 'hit', 'defend', 'death', 'shoot']
    acts = [x for x in acts if frames_of(new_root, x)]
    sheet = Image.new('RGB', (cw * cols + 40, ch * len(acts) * 2), (60, 90, 60))
    d = ImageDraw.Draw(sheet)
    for r, act in enumerate(acts):
        for k, (root, tag) in enumerate(((new_root, 'NEW'), (src_root, 'SRC'))):
            y = (r * 2 + k) * ch
            for c, f in enumerate(frames_of(root, act)[:cols]):
                im = Image.open(f).convert('RGBA').resize((cw, ch))
                sheet.paste(im, (40 + c * cw, y), im)
            d.text((2, y + 4), f'{tag}\n{act}', fill=(255, 255, 0))
    sheet.save(path)
    print('SHEET', path)

def closeups(new_root, src_root, path):
    """The extreme frames at full render size, new above source, plus the feet at 2x: the defects
    contact-sheet tiles hide (feet, hands, faces) show here."""
    picks = [('idle', 0), ('walk', 2), ('walk', 8), ('attack', 3), ('attack', 5), ('hit', 2), ('defend', 3),
             ('death', 4), ('shoot', 5)]
    rows = []
    for root in (new_root, src_root):
        tiles, feet = [], []
        for act, i in picks:
            fs = frames_of(root, act)
            if len(fs) <= i:
                continue
            im = Image.open(fs[i]).convert('RGBA')
            bb = im.getbbox()
            cx = (bb[0] + bb[2]) // 2
            c = im.crop((cx - 170, 60, cx + 170, 700))
            bg = Image.new('RGBA', c.size, (60, 90, 60, 255)); bg.alpha_composite(c)
            ImageDraw.Draw(bg).text((4, 4), f'{act} {i:02d}', fill=(255, 255, 0))
            tiles.append(bg.convert('RGB'))
            f = im.crop((cx - 85, bb[3] - 110, cx + 85, bb[3] + 10)).resize((340, 240), Image.LANCZOS)
            fb = Image.new('RGBA', f.size, (60, 90, 60, 255)); fb.alpha_composite(f)
            feet.append(fb.convert('RGB'))
        rows.append((tiles, feet))
    W = 340 * max(len(r[0]) for r in rows)
    sheet = Image.new('RGB', (W, (640 + 240) * 2), (30, 30, 30))
    for k, (tiles, feet) in enumerate(rows):
        y = k * 880
        for i, t in enumerate(tiles):
            sheet.paste(t, (i * 340, y))
        for i, t in enumerate(feet):
            sheet.paste(t, (i * 340, y + 640))
    sheet.save(path)
    print('SHEET', path, '(top: new, bottom: source; feet at 2x under each)')

def measure(slug, frames):
    """Ground point and scale for convert-art.py's RENDERED, like the batches: x = the idle figure's
    centroid, y = its lowest pixel, scale = the BATTLE height / the idle height."""
    ys_top, ys_bot, xs = [], [], []
    for f in frames_of(frames, 'idle'):
        a = np.array(Image.open(f))[:, :, 3] > 40
        y, x = np.nonzero(a)
        ys_top.append(y.min()); ys_bot.append(y.max()); xs.append(x.mean())
    height = float(np.median(np.array(ys_bot) - np.array(ys_top)))
    return (round(float(np.mean(xs))), int(max(ys_bot))), height

def step_anim(slug, base, a):
    p = plan.PLAN[slug]
    if p.get('script'):
        return step_scripted(slug, base, p)
    src = p['source']
    clips = plan.SOURCES[src] if 'shoot' in p and p['shoot'] else [c for c in plan.SOURCES[src] if not c.startswith('shoot=')]
    anim = base / 'anim'
    if anim.exists():
        shutil.rmtree(anim)
    anim.mkdir(parents=True)
    out = blender('tools/pipeline/retarget.py', ROOT / 'art/3d' / src / 'export.glb', base / 'rig' / 'rigged.glb',
                  anim / 'animated.glb')
    hands = next((l.split()[1:] for l in out.splitlines() if l.startswith('HANDS')), [])
    extra = [f'ortho={p["ortho"]}'] if p.get('ortho') else []
    if p.get('rigid') and hands:
        extra += [f'rigid={h}' for h in hands]
    blender('tools/3d/render_export.py', anim / 'animated.glb', anim / 'frames', 'turn=30', *extra, *clips)
    src_frames = ROOT / 'art/3d' / src / 'work/frames'
    compare_sheet(anim / 'frames', src_frames, anim / 'compare.png')
    closeups(anim / 'frames', src_frames, anim / 'closeups.png')
    (gx, gy), h = measure(slug, anim / 'frames')
    entry(slug, p, anim / 'frames', h, (gx, gy), f"{src}'s motions")

def step_scripted(slug, base, p):
    """Clips posed by tools/3d/animate_rig.py from the rig's bone chains (listed there under p['script'])."""
    anim = base / 'anim'
    if anim.exists():
        shutil.rmtree(anim)
    anim.mkdir(parents=True)
    blender('tools/3d/animate_rig.py', base / 'rig' / 'rigged.glb', anim / 'frames', p['script'])
    ref = ROOT / 'art/3d' / p.get('compare', 'ninja-hound') / 'work/frames'
    compare_sheet(anim / 'frames', ref, anim / 'compare.png')
    closeups(anim / 'frames', ref, anim / 'closeups.png')
    (gx, gy), h = measure(slug, anim / 'frames')
    entry(slug, p, anim / 'frames', h, (gx, gy), 'scripted, tools/3d/animate_rig.py')

def entry(slug, p, frames, h, ground, note):
    gx, gy = ground
    battle = _battle_heights()[slug]
    groups = 'MELEE_GROUPS' if not p.get('shoot') else \
        "{**MELEE_GROUPS, **{g: ('shoot', %s) for g in (14, 15, 16)}}" % p['shoot']
    print(f"RENDERED entry:\n    '{slug}': {{     # {note}\n"
          f"        'frames': 'art/pipeline/{slug}/anim/frames', 'ground': ({gx}, {gy}), "
          f"'scale': {battle[0] / h:.4f}, 'wide': {battle[1]}, 'map': None,\n        'groups': {groups},\n    }},")

def _battle_heights():
    src = (ROOT / 'tools/convert-art.py').read_text()
    start = src.index('BATTLE = {')
    end = src.index('\n}\n', start) + 2
    ns = {}
    exec(src[start:end], ns)
    return ns['BATTLE']

STEPS = {'apose': step_apose, 'pick': step_pick, 'views': step_views, 'viewcands': step_viewcands,
         'pickview': step_pickview, 'model': step_model, 'rig': step_rig,
         'anim': step_anim}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug', choices=sorted(plan.PLAN))
    ap.add_argument('step', choices=STEPS)
    ap.add_argument('n', nargs='?', type=int)
    ap.add_argument('--seeds', default='1,2,3')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--only', default='left,back,right')
    ap.add_argument('--hint', default='', help='extra direction for viewcands, e.g. what the back shows')
    ap.add_argument('--view', help='pickview: view:seed')
    a = ap.parse_args()
    base = ROOT / 'art' / 'pipeline' / a.slug
    base.mkdir(parents=True, exist_ok=True)
    STEPS[a.step](a.slug, base, a)

if __name__ == '__main__':
    main()
