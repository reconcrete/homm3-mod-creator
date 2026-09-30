"""Turn Anton's generated images in art/inbox/ into in-game assets.

Creatures: art/inbox/creature-<name>.png (transparent, full body, facing right) ->
  Content/sprites/naruto/creatures/<creatureId>/portraitLarge.png  58x64, opaque: the upper
      part of the figure over the original creature background of the town it borrows
      the look of (Konoha: Castle's)
  Content/sprites/naruto/creatures/<creatureId>/portraitSmall.png  32x32, transparent:
      head and shoulders
  Both crops are centered on the head (the mass of the top of the figure). The town of a
  creature comes from the section it sits in, in the vault note Naruto-Heroes-Creature-Prompts.

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
import os, re, shutil, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

PROMPTS = os.path.expanduser('~/O/Projects/HoMM3-Naruto/Knowledge/Art/Naruto-Heroes-Creature-Prompts.md')
H3BITMAP = os.path.expanduser('~/Library/Application Support/vcmi/Data/H3bitmap.lod')
# creature-window background (100x120) of the original town each village borrows its look from
BACKGROUND = {'Konohagakure': 'TPCASCAS.PCX', 'Sunagakure': 'TPCASTOW.PCX',
              'Kirigakure': 'TPCASFOR.PCX', None: 'tpcasneu.pcx'}
CR_LARGE, CR_SMALL = (58, 64), (32, 32)

def creature_sections():
    """creature slug -> vault section heading (town name, or None for neutrals)."""
    town, out = None, {}
    for line in open(PROMPTS, encoding='utf-8'):
        m = re.match(r'## (.+)', line)
        if m:
            town = m.group(1).strip() if m.group(1).strip() in BACKGROUND else None
        for slug in re.findall(r'`creature-([a-z0-9-]+)\.png`', line):
            out[slug] = town
    return out

_bg = {}
def background(town):
    if town not in _bg:
        import lod, h3pcx
        im = h3pcx.decode(lod.read(H3BITMAP, BACKGROUND[town])[1]).convert('RGBA')
        w, h = im.size   # 100x120 is narrower than 58:64: keep the width, crop the height
        ch = int(w * CR_LARGE[1] / CR_LARGE[0]); top = (h - ch) // 2
        _bg[town] = im.crop((0, top, w, top + ch)).resize(CR_LARGE, Image.LANCZOS)
    return _bg[town]

def head_box(im, height_share):
    """Square-ish crop box on the figure: from its top down height_share of its height,
    centered on the head (alpha mass in the top 25% of the figure)."""
    alpha = im.split()[-1]
    x0, y0, x1, y1 = alpha.getbbox()
    top = alpha.crop((x0, y0, x1, y0 + max(1, (y1 - y0) // 4)))
    cols = [sum(top.crop((i, 0, i + 1, top.height)).tobytes()) for i in range(top.width)]
    total = sum(cols) or 1
    cx = x0 + sum(i * c for i, c in enumerate(cols)) / total
    return cx, y0, (y1 - y0) * height_share

def crop_at(im, cx, top, h, aspect):
    w = h * aspect
    left = int(round(cx - w / 2)); upper = int(round(top - h * 0.04))
    return im.crop((left, upper, left + int(w), upper + int(h)))   # may extend past edges (transparent)

# Hand-set crops where the head is not the top of the figure (quadrupeds, big effects):
# (center x, top, height) as fractions of the image size, for the large and small portrait.
CROPS = {
    'ninja-hound': {'large': (0.70, 0.15, 0.60), 'small': (0.80, 0.17, 0.32)},
    'ninken-pack-leader': {'large': (0.70, 0.13, 0.62), 'small': (0.80, 0.15, 0.33)},
    'sharingan-master': {'large': (0.36, 0.11, 0.62), 'small': (0.33, 0.11, 0.30)},
}

def fixed_crop(im, spec, aspect):
    W, H = im.size
    cx, top, h = spec[0] * W, spec[1] * H, spec[2] * H
    w = h * aspect; left = int(round(cx - w / 2))
    return im.crop((left, int(top), left + int(w), int(top + h)))

def creature_large(im, town, slug=None):
    if slug in CROPS:
        fig = fixed_crop(im, CROPS[slug]['large'], CR_LARGE[0] / CR_LARGE[1]).resize(CR_LARGE, Image.LANCZOS)
    else:
        cx, top, h = head_box(im, 0.72)
        fig = crop_at(im, cx, top, h, CR_LARGE[0] / CR_LARGE[1]).resize(CR_LARGE, Image.LANCZOS)
    out = background(town).copy(); out.alpha_composite(fig)
    return out.convert('RGB')

def creature_small(im, slug=None):
    if slug in CROPS:
        return fixed_crop(im, CROPS[slug]['small'], 1.0).resize(CR_SMALL, Image.LANCZOS)
    cx, top, h = head_box(im, 0.45)
    return crop_at(im, cx, top, h, 1.0).resize(CR_SMALL, Image.LANCZOS)

def convert_creatures(force):
    towns = creature_sections()
    done = skipped = 0
    for f in sorted(os.listdir(INBOX)):
        if not (f.startswith('creature-') and f.endswith('.png')):
            continue
        slug = f[len('creature-'):-len('.png')]
        src = os.path.join(INBOX, f)
        out = os.path.join(SPRITES, 'creatures', camel(slug))
        large, small = os.path.join(out, 'portraitLarge.png'), os.path.join(out, 'portraitSmall.png')
        if not force and os.path.exists(large) and os.path.getmtime(large) >= os.path.getmtime(src):
            skipped += 1
            continue
        os.makedirs(out, exist_ok=True)
        os.makedirs(os.path.join(MASTERS, 'creatures'), exist_ok=True)
        shutil.copy2(src, os.path.join(MASTERS, 'creatures', f))
        im = Image.open(src).convert('RGBA')
        creature_large(im, towns.get(slug), slug).save(large)
        creature_small(im, slug).save(small)
        done += 1
    print('creatures: %d converted, %d up to date' % (done, skipped))

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
    convert_creatures(force)

if __name__ == '__main__':
    main('--force' in sys.argv)
