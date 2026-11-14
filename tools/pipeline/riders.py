"""Hero adventure-map sprites: a rider on a mount per hero class (the original game has a knight on
a horse for every class). The concept comes from ComfyUI's homm3/rider-from-refs (a picture of the
rider + a picture of the mount), then the creature pipeline makes the 3D model (views.py with
--pose animal, model.py) and tools/3d/render_rider.py renders the map frames.

    .venv/bin/python tools/pipeline/riders.py concept CLASS [--seeds 1,2,3,4]
    .venv/bin/python tools/pipeline/riders.py pick CLASS SEED      -> art/pipeline/rider-CLASS/front.png
    make.py rider-CLASS viewcands/pickview/model (as for a creature; the plan entry has pose 'animal')
    blender -b -P tools/3d/render_rider.py -- art/pipeline/rider-CLASS/model/model-30k.glb art/pipeline/rider-CLASS/map
    .venv/bin/python tools/pipeline/riders.py sprites CLASS        -> Content/sprites/naruto/map/heroes/CLASS(.json)
    then rerun the faction's town generator (townkit.hero_class picks the sprite up) and check in the game.

The flag: VCMI draws only the cloth (AF00-AF07, in the player's colour) over the hero picture; the
pole with its gold tip belongs to the hero picture. sprites draws the pole from the original knight's
pole tip (the same pixel in every frame, so the cloth hangs on it) straight down to the rider's
chest, and moves the rider up to 3 px towards it.

Files in art/pipeline/rider-<class>/ (the slug for views.py and model.py is rider-<class>).
"""
import argparse, pathlib, shutil, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import comfy
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[2]
INBOX = ROOT / 'art' / 'inbox'

# class -> rider picture, mount picture, rider, mount, how the rider sits (what the prompt says about each)
ASTRIDE = ("The rider sits upright on the mount's back with both hands resting on the saddle, legs on both sides "
           "of the mount.")
RIDERS = {
    'shinobi': ('hero-naruto-uzumaki.png', 'creature-gamabunta.png',
                'Naruto Uzumaki, a young ninja with spiky blond hair, whisker marks, a Leaf headband, an orange '
                'and black jumpsuit and black sandals',
                'a big red-orange warty toad crouching on all four legs, cream belly, a dark blue short vest with '
                'white trim and a red rope belt like the toad in image 2, a small leather saddle on its back', ASTRIDE),
    'sage': ('hero-jiraiya.png', 'creature-toad-warrior.png',
             'Jiraiya, a tall man with long spiky white hair, a horned forehead protector, a red short haori over a '
             'green kimono, a big scroll on his back',
             'a big olive-green warty toad crouching on all four legs, pale yellow belly, a red short vest with a '
             'black rope belt, a small leather saddle on its back', ASTRIDE),
    'puppeteer': ('hero-kankuro.png', 'creature-desert-scorpion.png',
                  'Kankuro, a young puppet master in a black hooded suit with two cat-ear points on the hood, purple '
                  'face paint, a bandaged puppet bundle on his back',
                  'a giant sand-colored desert scorpion standing on its eight legs, big pincers held low in front, its '
                  'segmented tail curled up high over its back behind the rider, a small saddle on its back', ASTRIDE),
    'windSage': ('hero-gaara.png', 'creature-gaaras-sand-tsunami.png',
                 'Gaara, a young man with short red hair, a dark red long coat, a big sand gourd on his back, arms '
                 'crossed',
                 'a flat, shapeless floating cloud of swirling golden sand, wider than it is tall, its underside a '
                 'little above the ground; not an animal: no head, no face, no legs',
                 "The rider stands upright on top of the sand cloud, feet together, arms crossed."),
    'swordsman': ('hero-zabuza-momochi.png', 'creature-great-shark.png',
                  'Zabuza Momochi, a tall ninja with bandages over his mouth, a Mist headband worn sideways, bare '
                  'arms, grey striped trousers, a huge cleaver sword strapped across his back',
                  'a great grey-blue shark gliding just above the ground on its belly, its wide head and open toothed '
                  'jaws in front, fins out to the sides, a small saddle on its back, a little water spraying around '
                  'it', ASTRIDE),
    'mistSage': ('hero-mei-terumi.png', 'creature-isobu.png',
                 'Mei Terumi, a woman with very long auburn hair, a blue high-collared dress, a Mist headband',
                 'a giant sea turtle standing on its four flipper legs, a high domed dark green shell with coral and '
                 'barnacles, a pale beaked head, a small saddle on top of the shell', ASTRIDE),
}

PROMPT = ('Image 1 shows the rider, image 2 shows the colors and painting style of the mount. Paint one picture: '
          '{rider}, riding {mount}. {seat} Front view: the mount faces the viewer straight on, symmetrical, '
          'low enough that the whole rider is visible above it. The whole figure from the top of the rider\'s head to '
          'the bottom of the mount, centered, filling two thirds of the picture. Plain light grey background, even '
          'studio lighting, no cast shadow, nothing else in the picture. Painted fantasy game art with the colors '
          'and shading of image 2.')


def folder(cls):
    return ROOT / 'art' / 'pipeline' / f'rider-{cls}'


def concept(cls, seeds):
    rider, mount, who, what, seat = RIDERS[cls]
    out = folder(cls) / 'concept'
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for seed in seeds:
        saved = comfy.run('rider-from-refs', {
            ('rider', 'image'): str(INBOX / rider), ('mount', 'image'): str(INBOX / mount),
            ('prompt', 'prompt'): PROMPT.format(rider=who, mount=what, seat=seat), ('seed', 'noise_seed'): seed,
            ('save', 'filename_prefix'): f'homm3/riders/{cls}',
        }, out / 'raw')
        f = [p for paths in saved.values() for p in paths][0]
        dst = out / f'{seed}.png'
        Image.open(f).convert('RGB').save(dst)
        made.append((seed, dst))
        print(cls, seed, '->', dst)
    sheet = Image.new('RGB', (400 * len(made), 430), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, (seed, p) in enumerate(made):
        sheet.paste(Image.open(p).resize((400, 400), Image.LANCZOS), (400 * i, 30))
        d.text((400 * i + 6, 8), str(seed), fill=(255, 220, 0))
    sheet.save(out / 'sheet.png')
    print(out / 'sheet.png')


def sprites(cls):
    import json, os
    sys.path.insert(0, str(ROOT / 'tools'))
    import lod, h3def
    import numpy as np
    src = folder(cls) / 'map'
    meta = json.load(open(src / 'meta.json'))
    knight = h3def.decode(lod.read(os.path.expanduser('~/Library/Application Support/vcmi/Data/H3sprite.lod'),
                                   'AH00_.DEF')[1])
    dst = ROOT / 'Content' / 'sprites' / 'naruto' / 'map' / 'heroes' / cls
    dst.mkdir(parents=True, exist_ok=True)
    seqs, sheet = [], Image.new('RGBA', (96 * 8 * 2, 64 * 10 * 2), (60, 110, 60, 255))
    def load(g, f):
        return Image.open(src / f'g{g}' / f'{f}.png').convert('RGBA').resize((96, 64), Image.LANCZOS).filter(
            ImageFilter.UnsharpMask(1.2, 80, 2))
    # each direction moved down so its standing picture's lowest pixel is on row 63, like the knight's
    drop = {d: 63 - int(np.nonzero(np.array(load(d, 0))[..., 3] > 40)[0].max()) for d in range(5)}
    for g in range(10):
        names = []
        for f in range(8):
            im = load(g, f)
            dy = drop[g % 5]
            k = np.array(knight[g][f % len(knight[g])][1])
            ys, xs = np.nonzero(k[..., 3] > 0)
            tx, ty = int(xs[ys.argmin()]), int(ys.min())                   # the pole tip
            cx, cy = meta['chest'][f'{g}:{f}']
            cy += dy
            dx = int(round(max(-3, min(3, tx - cx))))
            frame = Image.new('RGBA', (96, 64), (0, 0, 0, 0))
            frame.alpha_composite(im.crop((0, 0, 96, 64 - dy)), (dx, dy))
            px = frame.load()
            for y in range(ty, int(round(cy)) + 1):                        # the knight's pole colours
                c = k[y, tx] if k[y, tx, 3] and y < ty + 3 else (40, 26, 14, 255)
                px[tx, y] = tuple(int(v) for v in c[:3]) + (255,)
            frame.save(dst / f'{g}-{f}.png')
            names.append(f'{g}-{f}.png')
            sheet.alpha_composite(frame.resize((192, 128), Image.NEAREST), (192 * f, 128 * g))
        seqs.append({'group': g, 'frames': names, 'generateShadow': 2})
    (dst.parent / f'{cls}.json').write_text(json.dumps({'basepath': f'naruto/map/heroes/{cls}/', 'sequences': seqs},
                                                       indent='\t') + '\n')
    sheet.save(folder(cls) / 'map-sheet.png')
    print(dst.parent / f'{cls}.json', folder(cls) / 'map-sheet.png')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('concept', 'pick', 'sprites'))
    ap.add_argument('cls', choices=RIDERS)
    ap.add_argument('seed', nargs='?', type=int)
    ap.add_argument('--seeds', default='1,2,3,4')
    a = ap.parse_args()
    if a.action == 'concept':
        concept(a.cls, [int(s) for s in a.seeds.split(',')])
    elif a.action == 'sprites':
        sprites(a.cls)
    else:
        shutil.copy(folder(a.cls) / 'concept' / f'{a.seed}.png', folder(a.cls) / 'front.png')
        print(folder(a.cls) / 'front.png')
