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
from PIL import Image, ImageChops, ImageEnhance, ImageFilter
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
BACKGROUND = {'Konohagakure': 'TPCASCAS.PCX', 'Sunagakure': 'TPCASSTR.PCX',
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
    'kurama': {'large': (0.78, 0.30, 0.62), 'small': (0.83, 0.32, 0.43)},   # head at the right, tails on top
    'desert-scorpion': {'large': (0.62, 0.32, 0.66), 'small': (0.70, 0.48, 0.44)},   # tail on top, head low right
    'poison-scorpion': {'large': (0.62, 0.32, 0.66), 'small': (0.70, 0.48, 0.44)},
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
    # Sunagakure
    'suna-genin': (82, False), 'suna-chunin': (84, False),
    'wooden-puppet': (82, False), 'battle-puppet': (86, False),
    'wind-kunoichi': (86, False), 'fan-master': (88, False),
    'desert-scorpion': (70, True), 'poison-scorpion': (78, True),
    'human-puppet': (90, False), 'kazekage-puppet': (92, False),
    'kamaitachi': (96, True), 'great-kamaitachi': (100, True),
    'sand-colossus': (112, True), 'gaaras-sand-tsunami': (124, True),
    # Kirigakure
    'mist-genin': (82, False), 'bloody-mist-graduate': (84, False),
    'hunter-nin': (84, False), 'tracker-hunter-nin': (86, False),
    'hozuki-brawler': (86, False), 'hozuki-hydrifier': (88, False),
    'summoned-shark': (96, True), 'great-shark': (100, True),
    'yuki-clan-adept': (86, False), 'ice-mirror-master': (88, False),
    'mist-swordsman': (86, False), 'swordsman-of-the-seven': (90, False),
    'water-dragon': (116, True), 'great-water-dragon': (128, True),
    # neutrals and tailed beasts (Kurama has rendered animation, see RENDERED)
    'white-zetsu': (80, False), 'ninja-cat': (56, False), 'rogue-ninja': (84, False),
    'sound-ninja': (84, False), 'rain-ninja': (84, False), 'stone-ninja': (86, False),
    'cloud-ninja': (86, False), 'curse-mark-warrior': (90, False), 'monkey-king-enma': (110, True),
    'manda': (104, True), 'akatsuki-member': (90, False),
    'shukaku': (140, True), 'isobu': (124, True), 'gyuki': (140, True),
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

# adventure-map sprite from the still: one frame on the 64x64 canvas of the original map
# creatures, feet on the bottom edge. The originals keep a similar height whatever the
# creature (a Halfling is 41 px, a Pikeman 57, a Dragon 47-53) and big ones get wider, so the
# height follows the battle height loosely and the width is capped.
def map_sprite(fig, slug, out_dir):
    height, wide = BATTLE[slug]
    h = max(34, min(54, round(height * 0.55)))
    k = min(h / fig.height, 60 / fig.width)
    small = premultiplied_resize(fig, (max(1, round(fig.width * k)), max(1, round(fig.height * k))))
    cx = 40 if wide else 46
    canvas = Image.new('RGBA', MAP_CANVAS, (0, 0, 0, 0))
    canvas.alpha_composite(small, (min(max(0, round(cx - small.width / 2)), MAP_CANVAS[0] - small.width), MAP_CANVAS[1] - 1 - small.height))
    os.makedirs(os.path.join(out_dir, 'map'), exist_ok=True)
    canvas.save(os.path.join(out_dir, 'map', '0.png'), optimize=True)
    with open(os.path.join(out_dir, 'map.json'), 'w') as f:
        json.dump({'basepath': 'naruto/creatures/%s/map/' % camel(slug),
                   'sequences': [{'group': 0, 'frames': ['0.png'], 'generateShadow': 2}]}, f, indent='\t')
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
        need_battle = slug in BATTLE and slug not in RENDERED and (stale(src, battle, force) or
                                                                   stale(src, os.path.join(out, 'map.json'), force))
        if not stale(src, large, force) and not need_battle:
            skipped += 1
            continue
        os.makedirs(out, exist_ok=True)
        os.makedirs(os.path.join(MASTERS, 'creatures'), exist_ok=True)
        shutil.copy2(src, os.path.join(MASTERS, 'creatures', f))
        fig = figure(Image.open(src))
        creature_portraits(fig, towns.get(slug), slug, large, small)
        if slug in BATTLE and slug not in RENDERED:
            battle_sprite(fig, slug, out)
            map_sprite(fig, slug, out)
            sprites += 1
        done += 1
    print('creatures: %d converted (%d with battle and map sprites), %d up to date' % (done, sprites, skipped))

# ---------------------------------------------------------------- creatures: rendered animation

# Creatures with real animation frames (rendered from a 3D model by the art session).
# Every frame of a creature gets the same scale and offset, so the animation doesn't
# jitter: the source ground point lands on the hex center line of the battle layout.
#   frames: folder with <action>/NN.png (transparent RGBA, creature facing right)
#   ground: pixel under the body center in the source frames
#   scale:  source pixels -> battle pixels (Azure Dragon is 87x111 standing)
#   lift:   pixels to raise the ground point above the feet line; a 3/4 view puts the near
#           paws of a big creature below the point under its body center
#   groups: VCMI animation group -> (action, frame numbers or None for all)
RENDERED = {
    'kurama': {
        'frames': 'art/3d/kurama/work/frames', 'ground': (450, 562), 'scale': 0.32, 'lift': 10, 'wide': True,
        'groups': {
            0: ('walk', None), 1: ('idle', None), 2: ('idle', None),
            3: ('hit', None), 4: ('hit', None), 5: ('death', None),
            7: ('idle', [0]), 8: ('idle', [0]),
            11: ('attack', None), 12: ('attack', None), 13: ('attack', None),
        },
        'map': ('idle', 0),      # frame used for the adventure-map sprite
    },
}
# Tripo-rigged creatures (art session, 2026-10-20). Their frames come from tools/3d/:
# render_export.py (humanoids, Tripo Studio mocap and AI clips) or animate_rig.py (scripted
# hound and scorpion). They keep the artist's adventure-map sprite ('map': None).
MELEE_GROUPS = {
    0: ('walk', None), 1: ('idle', None), 2: ('idle', None),
    3: ('hit', None), 4: ('defend', None), 5: ('death', None),
    7: ('idle', [0]), 8: ('idle', [0]),
    11: ('attack', None), 12: ('attack', None), 13: ('attack', None),
}
RENDERED.update({
    'genin': {
        'frames': 'art/3d/genin/work/frames', 'ground': (444, 601), 'scale': 0.1885, 'wide': False, 'map': None,
        # frame 5 is the wind-up peak; the shuriken leaves on the step into frame 6, which must sit at index SHOOT_CLIMAX
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'anbu-operative': {
        'frames': 'art/3d/anbu/work/frames', 'ground': (442, 600), 'scale': 0.2014, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'mist-swordsman': {     # rendered with a wider camera (ortho 4.0) so the raised cleaver fits
        'frames': 'art/3d/mist-swordsman/work/frames', 'ground': (460, 567), 'scale': 0.2337, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'ninja-hound': {
        # no lift (battle check 2026-10-21): the ground y is already the lowest paw, so lift 6 stood it 6 px above the
        # row line, higher than the griffin and the humanoids beside it
        'frames': 'art/3d/ninja-hound/work/frames', 'ground': (461, 622), 'scale': 0.1481, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'desert-scorpion': {
        # no lift (battle check 2026-10-21): the ground y is already the lowest leg tip; lift 6 made it float
        'frames': 'art/3d/desert-scorpion/work/frames', 'ground': (456, 631), 'scale': 0.148, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'hyuga-guard': {
        'frames': 'art/3d/hyuga-guard/work/frames', 'ground': (442, 603), 'scale': 0.1935, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'medical-ninja': {
        'frames': 'art/3d/medical-ninja/work/frames', 'ground': (443, 599), 'scale': 0.1894, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'hunter-nin': {
        'frames': 'art/3d/hunter-nin/work/frames', 'ground': (450, 601), 'scale': 0.1949, 'wide': False, 'map': None,
        # same throw clip as genin: the senbon leaves on the step into frame 6 (index SHOOT_CLIMAX)
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'hozuki-brawler': {
        'frames': 'art/3d/hozuki-brawler/work/frames', 'ground': (444, 603), 'scale': 0.1977, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'human-puppet': {
        'frames': 'art/3d/human-puppet/work/frames', 'ground': (447, 601), 'scale': 0.2093, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'kamaitachi': {     # upright weasel, wider camera (ortho 3.8); two-hex in creatures.json, no lift: stands on two feet
        'frames': 'art/3d/kamaitachi/work/frames', 'ground': (494, 570), 'scale': 0.2481, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'water-dragon': {   # coiled serpent. Battle check 2026-10-21: the coil's underside is the frame bottom, so no
        # lift (with 6 it floated above its row); ground x between the coil's mass (405) and the bbox centre (452), and
        # scale 0.23 instead of 0.2495, so the tail no longer reaches 27 px into the hex in front (now ~16 px)
        'frames': 'art/3d/water-dragon/work/frames', 'ground': (440, 608), 'scale': 0.23, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'mist-genin': {
        'frames': 'art/3d/mist-genin/work/frames', 'ground': (444, 598), 'scale': 0.1911, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'summoned-shark': {     # upright on two feet: two-hex in creatures.json but no lift
        'frames': 'art/3d/summoned-shark/work/frames', 'ground': (472, 618), 'scale': 0.2096, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'toad-warrior': {   # upright, no lift; ortho 3.8. Ground and height from the feet (y 577): the katana tip hangs lower
        'frames': 'art/3d/toad-warrior/work/frames', 'ground': (463, 577), 'scale': 0.2437, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,   # 'walk' is a hop
    },
    'suna-genin': {     # wide cloak flares to the left; ground x checked on the chest and legs (447-451)
        'frames': 'art/3d/suna-genin/work/frames', 'ground': (447, 605), 'scale': 0.1894, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'wooden-puppet': {
        'frames': 'art/3d/wooden-puppet/work/frames', 'ground': (436, 594), 'scale': 0.192, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'uchiha-police': {
        'frames': 'art/3d/uchiha-police/work/frames', 'ground': (443, 599), 'scale': 0.1949, 'wide': False, 'map': None,
        # hand seals, then both palms thrust forward: the fireball leaves on frame 5 (index SHOOT_CLIMAX)
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [3, 4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'sand-colossus': {  # upright golem on two legs: two-hex in creatures.json but no lift; ortho 3.6
        'frames': 'art/3d/sand-colossus/work/frames', 'ground': (447, 594), 'scale': 0.2835, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'wind-kunoichi': {  # ponytail and sash flare; ground x from torso and legs (451-453), not the chest band
        'frames': 'art/3d/wind-kunoichi/work/frames', 'ground': (451, 598), 'scale': 0.1972, 'wide': False, 'map': None,
        # same jutsu cast as uchiha-police: the wind scythe leaves on frame 5 (index SHOOT_CLIMAX)
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [3, 4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'yuki-clan-adept': {    # wide kimono sleeves pull the torso band back; ground x between torso (441) and legs (452)
        'frames': 'art/3d/yuki-clan-adept/work/frames', 'ground': (446, 598), 'scale': 0.1977, 'wide': False, 'map': None,
        # same jutsu cast as uchiha-police: the water bullet leaves on frame 5 (index SHOOT_CLIMAX)
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [3, 4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
})
# Batch 3 (art session, 2026-10-21): ground x is the idle figure's centroid (humanoids), the
# bounding-box centre (four-legged) or the centroid (serpent); scale = BATTLE height / idle height.
RENDERED.update({
    'suna-chunin': {    # cloak and gourd: centroid 451, between the feet (468) and the box centre (441)
        'frames': 'art/3d/suna-chunin/work/frames', 'ground': (451, 607), 'scale': 0.1922, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'bloody-mist-graduate': {
        'frames': 'art/3d/bloody-mist-graduate/work/frames', 'ground': (442, 603), 'scale': 0.1927, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'tracker-hunter-nin': {
        'frames': 'art/3d/tracker-hunter-nin/work/frames', 'ground': (444, 602), 'scale': 0.1963, 'wide': False, 'map': None,
        # same throw clip and window as hunter-nin: the senbon leaves on the step into frame 6 (index SHOOT_CLIMAX)
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'ninken-pack-leader': {     # scripted quadruped like ninja-hound; no lift (the battle check found lift 6 floats animals)
        'frames': 'art/3d/ninken-pack-leader/work/frames', 'ground': (453, 625), 'scale': 0.1605, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'great-water-dragon': {     # scripted serpent, rendered with ortho 4.2 so the death roll stays in frame. Sized like
        # the battle-checked water-dragon: 118 tall (its 107 + upgrade), no lift, ground x set so the head reaches
        # about as far into the front hex (58 px right of the ground point)
        'frames': 'art/3d/great-water-dragon/work/frames', 'ground': (483, 579), 'scale': 0.3224, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'academy-student': {    # box_02 sampled from 0.8 s: the clip opens with a long crouching wind-up
        'frames': 'art/3d/academy-student/work/frames', 'ground': (443, 600), 'scale': 0.1797, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'hyuga-main-branch': {
        'frames': 'art/3d/hyuga-main-branch/work/frames', 'ground': (446, 605), 'scale': 0.1977, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'sharingan-master': {
        'frames': 'art/3d/sharingan-master/work/frames', 'ground': (447, 599), 'scale': 0.2051, 'wide': False, 'map': None,
        # same jutsu cast as uchiha-police: the fireball leaves on frame 5 (index SHOOT_CLIMAX)
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [3, 4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'battle-puppet': {
        'frames': 'art/3d/battle-puppet/work/frames', 'ground': (450, 598), 'scale': 0.1995, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'poison-scorpion': {    # scripted scorpion like desert-scorpion (second Studio rig); no lift
        'frames': 'art/3d/poison-scorpion/work/frames', 'ground': (458, 643), 'scale': 0.1592, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
})
# Batch 4 (art session, 2026-10-25, Tripo Studio; integrated 2026-11-12), same method as batch 3.
# Every frame checked on contact sheets before going in: feet on one line in all actions, nothing
# touches the frame edge, no broken limbs or weapons.
RENDERED.update({
    'senior-medic': {
        'frames': 'art/3d/senior-medic/work/frames', 'ground': (446, 597), 'scale': 0.1953, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'anbu-captain': {   # framed smaller than the operative (idle 373 px tall, feet at 560); the sword hangs to the
        # right, but the head, torso and feet all sit near the centroid (465)
        'frames': 'art/3d/anbu-captain/work/frames', 'ground': (465, 560), 'scale': 0.2413, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'swordsman-of-the-seven': {     # the cleaver stays in frame at the top of the overhead swing (attack 04)
        'frames': 'art/3d/swordsman-of-the-seven/work/frames', 'ground': (458, 584), 'scale': 0.2362, 'wide': False,
        'map': None, 'groups': MELEE_GROUPS,
    },
    'great-shark': {    # upright on two feet like summoned-shark: two-hex in creatures.json but no lift
        'frames': 'art/3d/great-shark/work/frames', 'ground': (448, 609), 'scale': 0.2252, 'wide': True,
        'map': None, 'groups': MELEE_GROUPS,
    },
})
# Self-hosted pipeline (tools/pipeline/, 2026-11-12/13): Qwen A-pose and views -> Pixal3D model ->
# SkinTokens rig -> motions moved over from a Tripo export (retarget.py), or scripted for animals
# and beasts (tools/3d/animate_rig.py) -> battle frames. Plan per creature: tools/pipeline/plan.py;
# generated by `make.py <slug> anim`. Frames in art/pipeline/<slug>/anim/frames. Every model, rig and
# action checked by eye, with full-size close-ups next to the source creature. Shukaku isn't here:
# its boneless tail stretched with the arms (see plan.py), so it keeps the static sprite.
RENDERED.update({
    'fan-master': {     # wind-kunoichi's motions
        'frames': 'art/pipeline/fan-master/anim/frames', 'ground': (450, 592), 'scale': 0.2085, 'wide': False, 'map': None,
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [3, 4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'kazekage-puppet': {     # hunter-nin's motions
        'frames': 'art/pipeline/kazekage-puppet/anim/frames', 'ground': (453, 596), 'scale': 0.2206, 'wide': False, 'map': None,
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'great-kamaitachi': {     # kamaitachi's motions
        'frames': 'art/pipeline/great-kamaitachi/anim/frames', 'ground': (458, 586), 'scale': 0.2625, 'wide': True, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'gaaras-sand-tsunami': {     # sand-colossus's motions
        'frames': 'art/pipeline/gaaras-sand-tsunami/anim/frames', 'ground': (449, 587), 'scale': 0.3333, 'wide': True, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'ice-mirror-master': {     # yuki-clan-adept's motions
        'frames': 'art/pipeline/ice-mirror-master/anim/frames', 'ground': (442, 595), 'scale': 0.2061, 'wide': False, 'map': None,
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [3, 4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'hozuki-hydrifier': {     # hozuki-brawler's motions
        'frames': 'art/pipeline/hozuki-hydrifier/anim/frames', 'ground': (450, 600), 'scale': 0.2061, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'gamabunta': {     # toad-warrior's motions
        'frames': 'art/pipeline/gamabunta/anim/frames', 'ground': (447, 575), 'scale': 0.3030, 'wide': True, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'white-zetsu': {     # academy-student's motions
        'frames': 'art/pipeline/white-zetsu/anim/frames', 'ground': (446, 594), 'scale': 0.1905, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'rogue-ninja': {     # anbu's motions
        'frames': 'art/pipeline/rogue-ninja/anim/frames', 'ground': (447, 601), 'scale': 0.1947, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'sound-ninja': {     # hunter-nin's motions
        'frames': 'art/pipeline/sound-ninja/anim/frames', 'ground': (444, 595), 'scale': 0.1972, 'wide': False, 'map': None,
        'groups': {**MELEE_GROUPS, **{g: ('shoot', [4, 5, 6, 7]) for g in (14, 15, 16)}},
    },
    'rain-ninja': {     # mist-genin's motions
        'frames': 'art/pipeline/rain-ninja/anim/frames', 'ground': (452, 603), 'scale': 0.1956, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'stone-ninja': {     # hozuki-brawler's motions
        'frames': 'art/pipeline/stone-ninja/anim/frames', 'ground': (445, 604), 'scale': 0.1998, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'cloud-ninja': {     # hyuga-guard's motions
        'frames': 'art/pipeline/cloud-ninja/anim/frames', 'ground': (451, 600), 'scale': 0.2021, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'curse-mark-warrior': {     # hyuga-guard's motions
        'frames': 'art/pipeline/curse-mark-warrior/anim/frames', 'ground': (457, 601), 'scale': 0.2228, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'akatsuki-member': {     # uchiha-police's motions
        'frames': 'art/pipeline/akatsuki-member/anim/frames', 'ground': (444, 595), 'scale': 0.2128, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'monkey-king-enma': {     # mist-swordsman's motions
        'frames': 'art/pipeline/monkey-king-enma/anim/frames', 'ground': (457, 565), 'scale': 0.3143, 'wide': True, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'ninja-cat': {     # scripted, tools/3d/animate_rig.py
        'frames': 'art/pipeline/ninja-cat/anim/frames', 'ground': (453, 604), 'scale': 0.1238, 'wide': False, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'manda': {     # scripted, tools/3d/animate_rig.py
        'frames': 'art/pipeline/manda/anim/frames', 'ground': (451, 589), 'scale': 0.2905, 'wide': True, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'isobu': {     # scripted, tools/3d/animate_rig.py
        'frames': 'art/pipeline/isobu/anim/frames', 'ground': (455, 579), 'scale': 0.3498, 'wide': True, 'map': None,
        'groups': MELEE_GROUPS,
    },
    'gyuki': {     # scripted, tools/3d/animate_rig.py
        'frames': 'art/pipeline/gyuki/anim/frames', 'ground': (442, 578), 'scale': 0.4118, 'wide': True, 'map': None,
        'groups': MELEE_GROUPS,
    },
})
MAP_CANVAS, MAP_BOX = (64, 64), (60, 54)   # original map creatures: 64x64, standing on the bottom edge, about 25-47 wide and 41-57 tall

def premultiplied_resize(im, size):
    out = im.convert('RGBa').resize(size, Image.LANCZOS).convert('RGBA')
    rgb = out.convert('RGB').filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=2))
    rgb.putalpha(out.split()[-1].point(lambda v: 0 if v < 24 else v))
    return rgb

def rendered_creature(slug, spec, force):
    src_root = os.path.join(ROOT, spec['frames'])
    out = os.path.join(SPRITES, 'creatures', camel(slug))
    target = os.path.join(out, 'battle.json')
    sources = [os.path.join(dp, f) for dp, _, fs in os.walk(src_root) for f in fs if f.endswith('.png')]
    if not sources:
        print('rendered %s: no frames in %s' % (slug, spec['frames'])); return
    newest = max(os.path.getmtime(f) for f in sources)
    if not force and os.path.exists(target) and os.path.getmtime(target) >= max(newest, SELF_MTIME):
        print('rendered %s: up to date' % slug); return
    frames_dir = os.path.join(out, 'battle')
    if os.path.isdir(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir)
    k = spec['scale']; gx, gy = spec['ground']
    cx = CENTER_2 if spec['wide'] else CENTER_1
    made, clipped = {}, 0
    def frame(action, n):
        nonlocal clipped
        if (action, n) not in made:
            im = Image.open(os.path.join(src_root, action, '%02d.png' % n)).convert('RGBA')
            small = premultiplied_resize(im, (round(im.width * k), round(im.height * k)))
            left, top = round(cx - gx * k), round(BASELINE - spec.get('lift', 0) - gy * k)
            canvas = Image.new('RGBA', CANVAS, (0, 0, 0, 0))
            canvas.alpha_composite(small, (left, top)) if left >= 0 and top >= 0 else canvas.paste(small, (left, top), small)
            box = small.split()[-1].getbbox()
            if box and (left + box[0] < 0 or top + box[1] < 0 or left + box[2] > CANVAS[0] or top + box[3] > CANVAS[1]):
                clipped += 1
            name = '%s_%02d.png' % (action, n)
            canvas.save(os.path.join(frames_dir, name), optimize=True)
            made[(action, n)] = name
        return made[(action, n)]
    sequences = []
    for group, (action, numbers) in sorted(spec['groups'].items()):
        if numbers is None:
            numbers = sorted(int(f[:-4]) for f in os.listdir(os.path.join(src_root, action)) if f.endswith('.png'))
        sequences.append({'group': group, 'frames': [frame(action, n) for n in numbers],
                          'generateShadow': 1, 'generateOverlay': 1})
    with open(target, 'w') as f:
        json.dump({'basepath': 'naruto/creatures/%s/battle/' % camel(slug), 'sequences': sequences}, f, indent='\t')
        f.write('\n')
    if spec['map'] is None:     # keeps the map sprite made from the artist's picture
        print('rendered %s: %d battle frames in %d groups%s' %
              (slug, len(made), len(sequences), ', %d CLIPPED by the 450x400 canvas' % clipped if clipped else ''))
        return
    # adventure-map sprite: one frame, fitted into the box original map creatures occupy
    action, n = spec['map']
    im = Image.open(os.path.join(src_root, action, '%02d.png' % n)).convert('RGBA')
    im = im.crop(im.split()[-1].point(lambda v: 255 if v > 128 else 0).getbbox())
    r = min(MAP_BOX[0] / im.width, MAP_BOX[1] / im.height)
    small = premultiplied_resize(im, (max(1, round(im.width * r)), max(1, round(im.height * r))))
    canvas = Image.new('RGBA', MAP_CANVAS, (0, 0, 0, 0))
    canvas.alpha_composite(small, (min(max(0, 40 - small.width // 2), MAP_CANVAS[0] - small.width), 63 - small.height))
    os.makedirs(os.path.join(out, 'map'), exist_ok=True)
    canvas.save(os.path.join(out, 'map', '0.png'), optimize=True)
    with open(os.path.join(out, 'map.json'), 'w') as f:
        json.dump({'basepath': 'naruto/creatures/%s/map/' % camel(slug),
                   'sequences': [{'group': 0, 'frames': ['0.png'], 'generateShadow': 2}]}, f, indent='\t')
        f.write('\n')
    print('rendered %s: %d battle frames in %d groups%s, map sprite' %
          (slug, len(made), len(sequences), ', %d CLIPPED by the 450x400 canvas' % clipped if clipped else ''))

# ---------------------------------------------------------------- adventure-map objects

# map-dwelling-<slug>.png -> Content/sprites/naruto/map/dwellings/<slug>.json + <slug>/0.png:
# a one-frame map object on a 96x96 canvas (3x3 tiles), the picture standing on the bottom
# edge and centered over the two right columns, which the dwelling blocks (mask VVV/VBB/VBA,
# entered from below; fits VCMI's 2x2 rule for random dwellings). VCMI adds the shadow.
DWELLING_CANVAS, DWELLING_BOX, DWELLING_CENTER = (96, 96), (94, 92), 58

def flag_poles(base, overlay, poles):
    """Flagpoles drawn into the picture, their pennants into the overlay: VCMI tints the white
    pixels of '<frame>-overlay.png' with the owner's color (how the HD mod flags its towns).
    poles: (x, bottom y, height, +1 pennant to the right / -1 to the left)."""
    px, ov = base.load(), overlay.load()
    for x, bottom, height, side in poles:
        for y in range(bottom - height, bottom + 1):
            px[x, y] = (58, 42, 28, 255)
            px[x + 1, y] = (112, 88, 60, 255)
        top = bottom - height
        for row, length in enumerate((7, 6, 5, 3)):         # a pennant fluttering away from the pole
            for i in range(length):
                ov[x + 1 + side * (1 + i) if side > 0 else x - 1 - i, top + 1 + row] = (255, 255, 255, 255)

def map_object(src, folder, slug, canvas, box, center_x, poles=()):
    im = Image.open(src).convert('RGBA')
    im = im.crop(im.split()[-1].point(lambda v: 255 if v > 128 else 0).getbbox())
    k = min(box[0] / im.width, box[1] / im.height)
    small = im.convert('RGBa').resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS).convert('RGBA')
    rgb = small.convert('RGB').filter(ImageFilter.UnsharpMask(radius=0.6, percent=50, threshold=2))
    rgb.putalpha(small.split()[-1].point(lambda v: 0 if v < 24 else v))
    out = Image.new('RGBA', canvas, (0, 0, 0, 0))
    out.alpha_composite(rgb, (min(max(0, round(center_x - rgb.width / 2)), canvas[0] - rgb.width), canvas[1] - 1 - rgb.height))
    overlay = Image.new('RGBA', canvas, (0, 0, 0, 0))
    flag_poles(out, overlay, poles)
    d = os.path.join(SPRITES, 'map', folder, slug)
    os.makedirs(d, exist_ok=True)
    out.save(os.path.join(d, '0.png'), optimize=True)
    if poles:
        overlay.save(os.path.join(d, '0-overlay.png'), optimize=True)
    with open(os.path.join(SPRITES, 'map', folder, slug + '.json'), 'w') as f:
        json.dump({'basepath': 'naruto/map/%s/%s/' % (folder, slug),
                   'sequences': [{'group': 0, 'frames': ['0.png'], 'generateShadow': 2}]}, f, indent='\t')
        f.write('\n')

# map-town-<faction>-<village|fort|castle>.png -> naruto/map/towns/<faction>-<level>: 192x192 like
# the original town sprites (6x6 tiles; the gate on the entrance tile, column 4 of the bottom
# row, x 96-127), sized like the originals (about 158x150 for a castle), two flags at the gate.
TOWN_CANVAS, TOWN_CENTER = (192, 192), 112
TOWN_BOX = {'village': (132, 122), 'fort': (146, 136), 'castle': (158, 150)}
TOWN_POLES = [(91, 190, 14, -1), (131, 190, 14, 1)]
DWELLING_POLES = [(91, 94, 14, -1)]       # one flag on the right edge, next to the entrance tile

# artifact-<slug>.png -> Content/sprites/naruto/artifacts/<artifactId>/: icon.png 44x44 (hero
# screen, transparent), bonus.png 58x64 (campaign bonus picture) and map.json + map/0.png
# (adventure map, 64x32, the artifact in the right tile like the originals).
def fit(im, box):
    im = im.crop(im.split()[-1].point(lambda v: 255 if v > 128 else 0).getbbox())
    k = min(box[0] / im.width, box[1] / im.height)
    small = im.convert('RGBa').resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS).convert('RGBA')
    rgb = small.convert('RGB').filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=2))
    rgb.putalpha(small.split()[-1].point(lambda v: 0 if v < 24 else v))
    return rgb

def convert_artifacts(force):
    done = 0
    for f in sorted(os.listdir(INBOX)):
        if not (f.startswith('artifact-') and f.endswith('.png')):
            continue
        aid = camel(f[len('artifact-'):-4])
        src = os.path.join(INBOX, f)
        out = os.path.join(SPRITES, 'artifacts', aid)
        if not stale(src, os.path.join(out, 'map.json'), force):
            continue
        os.makedirs(os.path.join(out, 'map'), exist_ok=True)
        im = Image.open(src).convert('RGBA')
        for name, canvas, box, anchor in (('icon.png', (44, 44), (42, 42), 'center'), ('bonus.png', (58, 64), (54, 58), 'center'),
                                          ('map/0.png', (64, 32), (31, 31), 'right')):
            pic = fit(im, box)
            c = Image.new('RGBA', canvas, (0, 0, 0, 0))
            pos = ((canvas[0] - pic.width) // 2, (canvas[1] - pic.height) // 2) if anchor == 'center' else \
                (48 - pic.width // 2, canvas[1] - 1 - pic.height)
            c.alpha_composite(pic, pos)
            c.save(os.path.join(out, name), optimize=True)
        with open(os.path.join(out, 'map.json'), 'w') as fh:
            json.dump({'basepath': 'naruto/artifacts/%s/map/' % aid,
                       'sequences': [{'group': 0, 'frames': ['0.png'], 'generateShadow': 2}]}, fh, indent='\t')
            fh.write('\n')
        done += 1
    print('artifacts: %d converted' % done)

def convert_map_objects(force):
    done = 0
    for f in sorted(os.listdir(INBOX)):
        if f.startswith('map-dwelling-') and f.endswith('.png'):
            slug = f[len('map-dwelling-'):-4]
            target = os.path.join(SPRITES, 'map', 'dwellings', slug + '.json')
            if stale(os.path.join(INBOX, f), target, force):
                map_object(os.path.join(INBOX, f), 'dwellings', slug, DWELLING_CANVAS, DWELLING_BOX, DWELLING_CENTER, DWELLING_POLES)
                done += 1
        elif f.startswith('map-town-') and f.endswith('.png'):
            slug = f[len('map-town-'):-4]
            level = slug.rsplit('-', 1)[1]
            target = os.path.join(SPRITES, 'map', 'towns', slug + '.json')
            if level in TOWN_BOX and stale(os.path.join(INBOX, f), target, force):
                map_object(os.path.join(INBOX, f), 'towns', slug, TOWN_CANVAS, TOWN_BOX[level], TOWN_CENTER, TOWN_POLES)
                done += 1
    print('map objects: %d converted' % done)

# projectile-<name>.png (pointing right) -> naruto/projectiles/<name>.json + <name>/NN.png: one
# frame per angle in PROJECTILE_ANGLES (+90 = shooting straight up), like the original
# projectile DEFs; VCMI picks the frame closest to the shot's angle and mirrors group 0 for
# shots to the left. Lengths at 0 degrees follow the originals (arrow 30 px, Gog's fireball 36).
PROJECTILE_ANGLES = [90, 72, 45, 27, 0, -27, -45, -72, -90]   # also in townkit.py
PROJECTILES = {'shuriken': 16, 'kunai': 30, 'fireball': 36, 'wind-scythe': 40, 'senbon': 30,
               'ice-senbon': 32, 'water-bullet': 36}

def convert_projectiles(force):
    done = 0
    for name, length in PROJECTILES.items():
        src = os.path.join(INBOX, 'projectile-%s.png' % name)
        target = os.path.join(SPRITES, 'projectiles', name + '.json')
        if not os.path.exists(src) or not stale(src, target, force):
            continue
        im = Image.open(src).convert('RGBA')
        im = im.crop(im.split()[-1].point(lambda v: 255 if v > 24 else 0).getbbox())
        small = premultiplied_resize(im, (length, max(1, round(im.height * length / im.width))))
        d = os.path.join(SPRITES, 'projectiles', name)
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        frames = []
        for i, angle in enumerate(PROJECTILE_ANGLES):
            rot = small.convert('RGBa').rotate(angle, resample=Image.BICUBIC, expand=True).convert('RGBA')
            box = rot.split()[-1].point(lambda v: 255 if v > 8 else 0).getbbox()
            # keep the crop centered on the image center, which VCMI puts on the flight path
            cx, cy = rot.width / 2, rot.height / 2
            hw, hh = max(cx - box[0], box[2] - cx), max(cy - box[1], box[3] - cy)
            rot = rot.crop((int(cx - hw), int(cy - hh), int(round(cx + hw)), int(round(cy + hh))))
            rot.save(os.path.join(d, '%02d.png' % i), optimize=True)
            frames.append('%02d.png' % i)
        with open(target, 'w') as f:
            json.dump({'basepath': 'naruto/projectiles/%s/' % name, 'sequences': [{'group': 0, 'frames': frames}]}, f, indent='\t')
            f.write('\n')
        done += 1
    print('projectiles: %d converted' % done)

# hero specialty icons: specialty-<slug>.png -> heroes/<heroId>/specialtyLarge.png (44x44) and
# specialtySmall.png (32x32), opaque like UN44.DEF / UN32.DEF; the artist's bevelled frame is kept
SPECIALTY = {'shadow-clone-jutsu': 'narutoUzumaki', 'copy-ninja': 'kakashiHatake', 'eight-gates': 'mightGuy',
             'insect-swarm': 'shinoAburame', 'wind-blades': 'asumaSarutobi', 'sand-shield': 'gaara', 'gold-dust': 'rasa',
             'mirage': 'gengetsuHozuki', 'bubbles': 'utakata', 'explosive-sword': 'jinpachiMunashi',
             'silent-killing': 'zabuzaMomochi', 'puppets': 'kankuro'}

def icon(im, size):
    im = im.convert('RGB')
    plain = Image.new('RGB', im.size, im.getpixel((0, 0)))   # some tiles sit on a plain margin: cut it off
    im = im.crop(ImageChops.difference(im, plain).convert('L').point(lambda v: 255 if v > 30 else 0).getbbox())
    m = round(im.width * 0.006)              # a few light pixels at the very edge of some pictures
    im = im.crop((m, m, im.width - m, im.height - m)).resize((size, size), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=2))

def convert_specialties(force):
    done = 0
    for slug, hid in SPECIALTY.items():
        src = os.path.join(INBOX, 'specialty-%s.png' % slug)
        out = os.path.join(SPRITES, 'heroes', hid)
        if not os.path.exists(src) or not stale(src, os.path.join(out, 'specialtyLarge.png'), force):
            continue
        os.makedirs(out, exist_ok=True)
        im = Image.open(src)
        icon(im, 44).save(os.path.join(out, 'specialtyLarge.png'))
        icon(im, 32).save(os.path.join(out, 'specialtySmall.png'))
        done += 1
    # the mod icon: VCMI 1.7.5's launcher has no place for one, so it waits at the repo root
    src = os.path.join(INBOX, 'mod-icon.png')
    if os.path.exists(src) and stale(src, os.path.join(ROOT, 'mod-icon.png'), force):
        icon(Image.open(src), 256).save(os.path.join(ROOT, 'mod-icon.png'))
        done += 1
    print('specialty icons and mod icon: %d converted' % done)

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
    for slug, spec in RENDERED.items():
        rendered_creature(slug, spec, force)
    convert_map_objects(force)
    convert_artifacts(force)
    convert_specialties(force)
    convert_projectiles(force)
    prune()
