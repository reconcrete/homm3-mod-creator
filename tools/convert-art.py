"""Turn Anton's generated images in art/inbox/ into in-game assets.

Heroes: art/inbox/hero-<name>.png ->
  Content/sprites/naruto/heroes/<heroId>/portraitLarge.png  58x64 (hero screen, tavern)
  Content/sprites/naruto/heroes/<heroId>/portraitSmall.png  48x32 (hero lists, face crop)
<heroId> is the camelCase of <name> (hero-naruto-uzumaki.png -> narutoUzumaki), the id
used in the mod's hero JSON. The large crop is the same centered full-height crop as the
art review sheet (tools/review-sheet.py), so the game shows what Anton approved.
The original is copied to art/masters/heroes/ (git-ignored; full size kept for re-exports).

Safe to rerun after images are regenerated: outputs are rebuilt when the inbox file is
newer. Then rerun the town generators (tools/towns/*.py) so the JSON points at them.
python3 tools/convert-art.py [--force]"""
import os, shutil, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(ROOT, 'art/inbox')
MASTERS = os.path.join(ROOT, 'art/masters')
SPRITES = os.path.join(ROOT, 'Content/sprites/naruto')
LARGE, SMALL = (58, 64), (48, 32)

def camel(slug):
    first, *rest = slug.split('-')
    return first + ''.join(w.capitalize() for w in rest)

def hero_large(im):
    w, h = im.size
    cw = int(h * LARGE[0] / LARGE[1])
    left = (w - cw) // 2
    return im.crop((left, 0, left + cw, h)).resize(LARGE, Image.LANCZOS)

def hero_small(im):
    # face crop: 80% of the width, centered; the band from the forehead to the chin
    w, h = im.size
    cw = int(w * 0.80); ch = int(cw * SMALL[1] / SMALL[0])
    left = (w - cw) // 2; top = int(h * 0.17)
    return im.crop((left, top, left + cw, top + ch)).resize(SMALL, Image.LANCZOS)

def main(force):
    done = skipped = 0
    for f in sorted(os.listdir(INBOX)):
        if not (f.startswith('hero-') and f.endswith('.png')):
            continue
        slug = f[len('hero-'):-len('.png')]
        src = os.path.join(INBOX, f)
        out = os.path.join(SPRITES, 'heroes', camel(slug))
        large, small = os.path.join(out, 'portraitLarge.png'), os.path.join(out, 'portraitSmall.png')
        if not force and os.path.exists(large) and os.path.getmtime(large) >= os.path.getmtime(src):
            skipped += 1
            continue
        os.makedirs(out, exist_ok=True)
        os.makedirs(os.path.join(MASTERS, 'heroes'), exist_ok=True)
        shutil.copy2(src, os.path.join(MASTERS, 'heroes', f))
        im = Image.open(src).convert('RGB')
        hero_large(im).save(large)
        hero_small(im).save(small)
        done += 1
    print('heroes: %d converted, %d up to date' % (done, skipped))

if __name__ == '__main__':
    main('--force' in sys.argv)
