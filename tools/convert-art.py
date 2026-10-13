"""Turn Anton's generated images in art/inbox/ into in-game assets.

Heroes: art/inbox/hero-<name>.png ->
  Content/sprites/naruto/heroes/<heroId>/portraitLarge.png  58x64 (hero screen, tavern)
  Content/sprites/naruto/heroes/<heroId>/portraitSmall.png  48x32 (hero lists, face crop)
  The large crop is the same centered full-height crop as the art review sheet.

Creatures: art/inbox/creature-<name>.png (transparent, full body, facing right) ->
  Content/sprites/naruto/creatures/<creatureId>/portraitLarge.png  58x64, opaque: the upper
      part of the figure over the creature background of the original town it borrows
  Content/sprites/naruto/creatures/<creatureId>/portraitSmall.png  32x32, transparent
  Content/sprites/naruto/creatures/<creatureId>/battle.json + battle/*.png
      static battle sprite, only for creatures listed in BATTLE below (see there)

<heroId> / <creatureId> is the camelCase of <name> (creature-ninja-hound.png -> ninjaHound),
the id used in the mod's JSON. Originals are copied to art/masters/ (git-ignored).

Safe to rerun after images are regenerated: outputs are rebuilt when the inbox file (or
this script) is newer. Then rerun the town generators (tools/towns/*.py), which point the
JSON at whatever exists here and fall back to borrowed originals otherwise.
python3 tools/convert-art.py [--force]"""
import json, math, os, re, shutil, sys
from PIL import Image, ImageEnhance, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(ROOT, 'art/inbox')
MASTERS = os.path.join(ROOT, 'art/masters')
SPRITES = os.path.join(ROOT, 'Content/sprites/naruto')
SELF_MTIME = os.path.getmtime(os.path.abspath(__file__))

def camel(slug):
    first, *rest = slug.split('-')
    return first + ''.join(w.capitalize() for w in rest)

def stale(src, out, force):
    return force or not os.path.exists(out) or os.path.getmtime(out) < max(os.path.getmtime(src), SELF_MTIME)

# ---------------------------------------------------------------- heroes

LARGE, SMALL = (58, 64), (48, 32)

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

def convert_heroes(force):
    done = skipped = 0
    for f in sorted(os.listdir(INBOX)):
        if not (f.startswith('hero-') and f.endswith('.png')):
            continue
        slug = f[len('hero-'):-len('.png')]
        src = os.path.join(INBOX, f)
        out = os.path.join(SPRITES, 'heroes', camel(slug))
        large, small = os.path.join(out, 'portraitLarge.png'), os.path.join(out, 'portraitSmall.png')
        if not stale(src, large, force):
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

# ---------------------------------------------------------------- creatures: the figure

def figure(im):
    """The creature cut out cleanly: (image cropped to the figure, with haze removed).
    Generated images carry faint haze, soft ground shadows and stray specks far from the
    body; the figure is where the solid pixels are (alpha > 128, specks eroded away)."""
    im = im.convert('RGBA')
    alpha = im.split()[-1]
    solid = alpha.point(lambda v: 255 if v > 128 else 0)
    x0, y0, x1, y1 = solid.filter(ImageFilter.MinFilter(9)).getbbox()
    pad = 8
    box = (max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad))
    fig = im.crop(box)
    a = fig.split()[-1].point(lambda v: 0 if v < 48 else v)   # drop haze, keep soft edges
    fig.putalpha(a)
    return fig

# ---------------------------------------------------------------- creatures: portraits

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

# Hand-set portrait crops where the head is not the top of the figure (quadrupeds):
# (center x, top, height) as fractions of the FIGURE (see figure()), large and small.
CROPS = {
    'ninja-hound': {'large': (0.71, -0.05, 0.81), 'small': (0.82, -0.03, 0.43)},
    'ninken-pack-leader': {'large': (0.73, -0.02, 0.72), 'small': (0.83, -0.01, 0.42)},
}

def head_crop(fig, height_share, aspect, spec=None):
    """Crop from the top of the figure down height_share of its height, centered on the
    head (the mass of the top quarter), or at a hand-set place. May run past the edges."""
    W, H = fig.size
    if spec:
        cx, top, h = spec[0] * W, spec[1] * H, spec[2] * H
    else:
        alpha = fig.split()[-1]
        band = alpha.crop((0, 0, W, max(1, H // 4)))
        cols = [sum(band.crop((i, 0, i + 1, band.height)).tobytes()) for i in range(W)]
        cx = sum(i * c for i, c in enumerate(cols)) / (sum(cols) or 1)
        top, h = -0.03 * H, height_share * H
    w = h * aspect
    left = int(round(cx - w / 2))
    return fig.crop((left, int(round(top)), left + int(round(w)), int(round(top + h))))

def creature_portraits(fig, town, slug, large, small):
    spec = CROPS.get(slug, {})
    big = head_crop(fig, 0.72, CR_LARGE[0] / CR_LARGE[1], spec.get('large')).resize(CR_LARGE, Image.LANCZOS)
    out = background(town).copy(); out.alpha_composite(big)
    out.convert('RGB').save(large)
    head_crop(fig, 0.45, 1.0, spec.get('small')).resize(CR_SMALL, Image.LANCZOS).save(small)

# ---------------------------------------------------------------- creatures: battle sprites

# Static battle sprites (first half of M8): the one still image stands in for every
# animation group. VCMI times an action by its frame count, so each action gets a few
# frames derived from the still: a small hop while moving, a lunge for melee, a recoil for
# shots, a flinch when hit, a topple for death. Real animation replaces this later.
#
# Layout copied from the original creature DEFs: a 450x400 canvas, feet on y = 267, the
# figure centered on x = 196 (one hex) or x = 218 (two hexes wide). VCMI mirrors the
# canvas for units facing left and generates the shadow and the selection outline.
#
# slug -> (body height in pixels, two hexes wide). Originals for scale: Halfling 65,
# Monk 78, Pikeman 95, Behemoth 98 tall. Only creatures listed here get battle sprites.
BATTLE = {
    'academy-student': (78, False), 'genin': (82, False),
    'ninja-hound': (68, True), 'ninken-pack-leader': (74, True),
    'hyuga-guard': (84, False), 'hyuga-main-branch': (86, False),
    'medical-ninja': (82, False), 'senior-medic': (84, False),
    'uchiha-police': (84, False), 'sharingan-master': (88, False),
    'anbu-operative': (86, False), 'anbu-captain': (90, False),
    'toad-warrior': (96, True), 'gamabunta': (110, True),
}
CANVAS, BASELINE, CENTER_1, CENTER_2 = (450, 400), 267, 196, 218
SHOOT_CLIMAX = 2      # frame of the shoot groups at which the projectile leaves

# animation group -> list of (dx, dy) offsets of the still, one per frame
LUNGE = [3, 9, 15, 15, 8, 2]
GROUPS = {
    0: [(0, 0), (0, -2), (0, -3), (0, -1)],                 # moving: small hop
    1: [(0, 0)],                                            # mouse over
    2: [(0, 0)],                                            # idle
    3: [(-3, 0), (-6, 0), (-4, 0), (-1, 0)],                # hit: knocked back
    4: [(-1, 0), (-3, 0), (-3, 0), (-1, 0)],                # defend
    7: [(0, 0)], 8: [(0, 0)],                               # turning
    11: [(x, -x // 2) for x in LUNGE],                      # melee attack up
    12: [(x, 0) for x in LUNGE],                            # melee attack front
    13: [(x, x // 2) for x in LUNGE],                       # melee attack down
    14: [(0, 0), (-2, 0), (-4, 0), (-3, 0), (-1, 0), (0, 0)],   # shoot up / front / down: recoil
    15: [(0, 0), (-2, 0), (-4, 0), (-3, 0), (-1, 0), (0, 0)],
    16: [(0, 0), (-2, 0), (-4, 0), (-3, 0), (-1, 0), (0, 0)],
    17: [(0, 0), (0, -1), (0, -2), (0, -2), (0, -1), (0, 0)],   # special / cast: rise
    18: [(0, 0), (0, -1), (0, -2), (0, -2), (0, -1), (0, 0)],
    19: [(0, 0), (0, -1), (0, -2), (0, -2), (0, -1), (0, 0)],
}
DEATH_ANGLES = [15, 35, 55, 75, 90, 90]                    # group 5: topple backwards
DEATH_ANGLES_WIDE = [25, 60, 100, 140, 180, 180]           # four-legged and squat creatures roll onto their backs

def scale_figure(fig, height):
    """Resize to the battle height without dark fringes (premultiplied alpha), then sharpen."""
    w = max(1, round(fig.width * height / fig.height))
    small = fig.convert('RGBa').resize((w, height), Image.LANCZOS).convert('RGBA')
    rgb = small.convert('RGB').filter(ImageFilter.UnsharpMask(radius=0.8, percent=70, threshold=2))
    rgb.putalpha(small.split()[-1])
    return rgb

def feet_x(sprite):
    """Horizontal center of the feet (alpha mass of the bottom fifth)."""
    a = sprite.split()[-1]
    band = a.crop((0, int(sprite.height * 0.8), sprite.width, sprite.height))
    cols = [sum(band.crop((i, 0, i + 1, band.height)).tobytes()) for i in range(band.width)]
    return sum(i * c for i, c in enumerate(cols)) / (sum(cols) or 1)

def battle_sprite(fig, slug, out_dir):
    height, wide = BATTLE[slug]
    sprite = scale_figure(fig, height)
    anchor = sprite.width / 2 if wide else feet_x(sprite)      # the point that sits on the hex center
    cx = CENTER_2 if wide else CENTER_1
    frames_dir = os.path.join(out_dir, 'battle')
    if os.path.isdir(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir)

    def place(img, left, top, name):
        canvas = Image.new('RGBA', CANVAS, (0, 0, 0, 0))
        canvas.alpha_composite(img, (int(round(left)), int(round(top))))
        canvas.save(os.path.join(frames_dir, name), optimize=True)
        return name

    made = {}
    def still(dx, dy):
        if (dx, dy) not in made:
            made[(dx, dy)] = place(sprite, cx - anchor + dx, BASELINE - sprite.height + dy, 's_%d_%d.png' % (dx, dy))
        return made[(dx, dy)]

    sequences = []
    for group, offsets in sorted(GROUPS.items()):
        sequences.append({'group': group, 'frames': [still(dx, dy) for dx, dy in offsets]})
    # death: rotate backwards around the feet, sink to the ground, darken at the end
    death = []
    angles = DEATH_ANGLES_WIDE if wide else DEATH_ANGLES
    for i, angle in enumerate(angles):
        rot = sprite.rotate(angle, resample=Image.BICUBIC, expand=True)
        box = rot.split()[-1].point(lambda v: 255 if v > 128 else 0).getbbox()
        rot = rot.crop(box)
        if i == len(angles) - 1:
            rgb = ImageEnhance.Brightness(rot.convert('RGB')).enhance(0.78); rgb.putalpha(rot.split()[-1]); rot = rgb
        back = 0 if wide else math.sin(math.radians(angle)) * sprite.height * 0.45   # a toppled body lies behind its feet
        death.append(place(rot, cx - back - rot.width / 2, BASELINE - rot.height, 'd_%d.png' % i))
    sequences.append({'group': 5, 'frames': death})
    sequences.sort(key=lambda s: s['group'])
    for s in sequences:
        s['generateShadow'] = 1
        s['generateOverlay'] = 1
    rel = 'naruto/creatures/%s/battle/' % camel(slug)
    with open(os.path.join(out_dir, 'battle.json'), 'w') as f:
        json.dump({'basepath': rel, 'sequences': sequences}, f, indent='\t')
        f.write('\n')

def convert_creatures(force):
    towns = creature_sections()
    done = skipped = sprites = 0
    for f in sorted(os.listdir(INBOX)):
        if not (f.startswith('creature-') and f.endswith('.png')):
            continue
        slug = f[len('creature-'):-len('.png')]
        src = os.path.join(INBOX, f)
        out = os.path.join(SPRITES, 'creatures', camel(slug))
        large, small = os.path.join(out, 'portraitLarge.png'), os.path.join(out, 'portraitSmall.png')
        battle = os.path.join(out, 'battle.json')
        need_battle = slug in BATTLE and stale(src, battle, force)
        if not stale(src, large, force) and not need_battle:
            skipped += 1
            continue
        os.makedirs(out, exist_ok=True)
        os.makedirs(os.path.join(MASTERS, 'creatures'), exist_ok=True)
        shutil.copy2(src, os.path.join(MASTERS, 'creatures', f))
        fig = figure(Image.open(src))
        creature_portraits(fig, towns.get(slug), slug, large, small)
        if slug in BATTLE:
            battle_sprite(fig, slug, out)
            sprites += 1
        done += 1
    print('creatures: %d converted (%d with battle sprites), %d up to date' % (done, sprites, skipped))

def prune():
    """Remove converted assets whose inbox image is gone (withdrawn for a redraw), so the
    town generators fall back to borrowed art instead of showing a rejected version."""
    for kind in ('hero', 'creature'):
        have = {camel(f[len(kind) + 1:-4]) for f in os.listdir(INBOX) if f.startswith(kind + '-') and f.endswith('.png')}
        folder = os.path.join(SPRITES, kind + 's')
        for d in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            if d not in have and os.path.isdir(os.path.join(folder, d)):
                shutil.rmtree(os.path.join(folder, d))
                print('removed %s/%s (no image in the inbox)' % (kind + 's', d))

if __name__ == '__main__':
    force = '--force' in sys.argv
    convert_heroes(force)
    convert_creatures(force)
    prune()
