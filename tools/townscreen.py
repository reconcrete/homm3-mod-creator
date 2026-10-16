"""Build a town screen from Anton's town art (batch 4).

Inputs (art/inbox/): town-<faction>-background.png (landscape, no buildings) and one
picture per building, town-<faction>-<slug>.png (transparent, building on its own ground
patch, 3/4 view from above).

Outputs (Content/sprites/naruto/<faction>/town/):
  background.png            800x374 town screen background
  <buildingId>.png/.json    the building scaled for the screen, as a one-frame animation
  <buildingId>-area.png     click/hover mask (the building's opaque pixels)
  <buildingId>-border.png   gold outline shown when the building is hovered
  hall/<buildingId>.png     150x70 town-hall icon (the building over its part of the town)
  icons/*.png               town-list icons, 58x64 and 48x32, normal and "built today"
  structures.json           positions for the town generator (tools/towns/<faction>.py),
                            which uses it instead of the borrowed Castle screen
  ../hallIcons.json         hall icon animation: our icons, borrowed ones where art is missing

Layout: each building spot is (center x, ground y, width) on the 800x374 screen. The
picture is trimmed to its opaque pixels, scaled to that width, and its bottom edge is put
on the ground line. Upgrades share their base's spot (VCMI shows only the highest built).
Draw order (z) follows the ground line: things lower on the screen are in front.
python3 tools/townscreen.py konohagakure [--preview DIR]"""
import json, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lod, h3def

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(ROOT, 'art/inbox')
H3 = os.path.expanduser('~/Library/Application Support/vcmi/Data')
SCREEN = (800, 374)
BORDER = (255, 231, 74, 255)      # gold, like the original town-screen outlines

# Upgrade chains share one spot; listed bottom-up.
CHAINS = {
    'hall': ['villageHall', 'townHall', 'cityHall', 'capitol'],
    'fort': ['fort', 'citadel', 'castle'],
    'guild': ['mageGuild1', 'mageGuild2', 'mageGuild3', 'mageGuild4', 'mageGuild5'],
}
for n in range(1, 8):
    CHAINS['d%d' % n] = ['dwellingLvl%d' % n, 'dwellingUpLvl%d' % n]

TOWNS = {
    'konohagakure': {
        # crop of the 1536x1024 background (keeps the Hokage faces and the open ground)
        'crop': (0, 120, 1536, 838),
        # Castle's borrowed hall icons, for buildings without art
        'hallFallback': 'HALLCSTL.DEF',
        # buildingId -> (picture slug, center x, ground y, width in pixels)
        'buildings': {
            'villageHall': ('hokage-office', 395, 300, 150),
            'townHall': ('hokage-chambers', 395, 300, 158),
            'cityHall': ('hokage-tower', 395, 300, 132),
            'capitol': ('hokage-residence', 395, 300, 170),
            'fort': ('village-gate', 262, 202, 176),
            'citadel': ('fortified-gate', 262, 202, 138),
            'castle': ('great-wall-of-konoha', 262, 202, 290),
            'mageGuild1': ('jutsu-library-level-1', 662, 224, 96),
            'mageGuild2': ('jutsu-library-level-2', 662, 224, 104),
            'mageGuild3': ('jutsu-library-level-3', 662, 224, 112),
            'mageGuild4': ('jutsu-library-level-4', 662, 224, 120),
            'mageGuild5': ('jutsu-library-level-5', 662, 224, 128),
            'tavern': ('ichiraku-ramen', 84, 370, 118),
            'blacksmith': ('tentens-weapon-shop', 562, 364, 94),
            'marketplace': ('konoha-market', 286, 360, 112),
            'resourceSilo': ('market-storehouse', 372, 373, 86),
            'special1': ('konoha-hospital', 742, 300, 102),
            'special2': ('training-ground-3', 656, 362, 110),
            'grail': ('hokage-rock', 760, 202, 106),
            'dwellingLvl1': ('ninja-academy', 746, 373, 108),
            'dwellingUpLvl1': ('ninja-academy-upgraded', 746, 373, 112),
            'dwellingLvl2': ('inuzuka-kennels', 196, 338, 114),
            'dwellingUpLvl2': ('inuzuka-kennels-upgraded', 196, 338, 118),
            'dwellingLvl3': ('hyuga-compound', 62, 302, 118),
            'dwellingUpLvl3': ('hyuga-compound-upgraded', 62, 302, 122),
            'dwellingLvl4': ('medical-corps', 472, 372, 112),
            'dwellingUpLvl4': ('medical-corps-upgraded', 472, 372, 116),
            'dwellingLvl5': ('uchiha-district', 560, 270, 136),
            'dwellingUpLvl5': ('uchiha-district-upgraded', 560, 270, 140),
            'dwellingLvl6': ('anbu-headquarters', 168, 262, 116),
            'dwellingUpLvl6': ('anbu-headquarters-upgraded', 168, 262, 116),
            'dwellingLvl7': ('mount-myoboku-gate', 66, 208, 100),
            'dwellingUpLvl7': ('mount-myoboku-gate-upgraded', 66, 208, 100),
        },
        # town-list icons: building shown for a town without and with a fort
        'icons': {'village': 'villageHall', 'fort': 'cityHall'},
    },
}

def opaque_box(im, threshold=128):
    return im.split()[-1].point(lambda v: 255 if v > threshold else 0).getbbox()

def scaled(im, width):
    im = im.crop(opaque_box(im, 24))
    h = max(1, round(im.height * width / im.width))
    out = im.convert('RGBa').resize((width, h), Image.LANCZOS).convert('RGBA')
    rgb = out.convert('RGB').filter(ImageFilter.UnsharpMask(radius=0.7, percent=50, threshold=2))
    rgb.putalpha(out.split()[-1].point(lambda v: 0 if v < 16 else v))
    return rgb

def area_and_border(sprite):
    solid = sprite.split()[-1].point(lambda v: 255 if v > 96 else 0)
    area = Image.new('RGBA', sprite.size, (0, 0, 0, 0))
    area.putalpha(solid)
    ring = ImageChops.subtract(solid.filter(ImageFilter.MaxFilter(3)), solid.filter(ImageFilter.MinFilter(3)))
    border = Image.new('RGBA', sprite.size, (0, 0, 0, 0))
    border.paste(BORDER, (0, 0), ring)
    return area, border

def write_anim(path, rel_png):
    with open(path, 'w') as f:
        json.dump({'sequences': [{'group': 0, 'frames': [rel_png]}]}, f, indent='\t')
        f.write('\n')

def lod_def(name):
    for a in ('H3sprite.lod', 'H3ab_spr.lod'):
        try:
            return h3def.decode(lod.read(os.path.join(H3, a), name)[1])
        except KeyError:
            pass

def built_mark(def_name, normal, built):
    """The 'built today' mark: pixels that differ between two frames of an original icon DEF."""
    g = lod_def(def_name)[0]
    a, b = g[normal][1], g[built][1]
    diff = ImageChops.difference(a.convert('RGB'), b.convert('RGB')).convert('L').point(lambda v: 255 if v > 24 else 0)
    mark = b.copy(); mark.putalpha(ImageChops.multiply(diff, b.split()[-1]))
    return mark

def build(faction, preview_dir=None):
    spec = TOWNS[faction]
    out = os.path.join(ROOT, 'Content/sprites/naruto', faction, 'town')
    rel = 'naruto/%s/town/' % faction
    os.makedirs(os.path.join(out, 'hall'), exist_ok=True)
    os.makedirs(os.path.join(out, 'icons'), exist_ok=True)

    bg = Image.open(os.path.join(INBOX, 'town-%s-background.png' % faction)).convert('RGB')
    bg = bg.crop(spec['crop']).resize(SCREEN, Image.LANCZOS)
    bg.save(os.path.join(out, 'background.png'))

    structures, sprites, missing = {}, {}, []
    for bid, (slug, cx, ground, width) in spec['buildings'].items():
        src = os.path.join(INBOX, 'town-%s-%s.png' % (faction, slug))
        if not os.path.exists(src):
            missing.append(slug)
            continue
        sprite = scaled(Image.open(src).convert('RGBA'), width)
        x, y = round(cx - sprite.width / 2), ground - sprite.height
        sprites[bid] = (sprite, x, y)
        area, border = area_and_border(sprite)
        sprite.save(os.path.join(out, bid + '.png'))
        area.save(os.path.join(out, bid + '-area.png'))
        border.save(os.path.join(out, bid + '-border.png'))
        write_anim(os.path.join(out, bid + '.json'), rel + bid + '.png')
        structures[bid] = {'animation': rel + bid, 'x': x, 'y': y, 'z': ground - 300,
                           'area': rel + bid + '-area.png', 'border': rel + bid + '-border.png'}

    # hall icons 150x70: the building filling the icon (the bottom of its ground patch may be
    # cut off) over the part of the town behind it, at the same zoom, kept inside the screen
    for bid, (sprite, x, y) in sprites.items():
        icon_w, icon_h = 150, 70
        k = min((icon_w - 4) / sprite.width, (icon_h + 8) / sprite.height)
        small = sprite.resize((max(1, round(sprite.width * k)), max(1, round(sprite.height * k))), Image.LANCZOS)
        w, h = icon_w / k, icon_h / k
        cx, cy = x + sprite.width / 2, y + sprite.height - (small.height - 8 - icon_h / 2) / k
        left = min(max(0, cx - w / 2), SCREEN[0] - w); top = min(max(0, cy - h / 2), SCREEN[1] - h)
        back = bg.crop((int(left), int(top), int(left + w), int(top + h))).resize((icon_w, icon_h), Image.LANCZOS).convert('RGBA')
        back.alpha_composite(small, ((icon_w - small.width) // 2, icon_h + 8 - small.height))
        back.convert('RGB').save(os.path.join(out, 'hall', bid + '.png'))

    # hall icon animation: frame = building id (ids from the buildings library)
    library = json.load(open(os.path.join(os.path.dirname(__file__), 'building-ids.json')))
    fallback_frames = len(lod_def(spec['hallFallback'])[0])
    images = []
    for bid, num in sorted(library.items(), key=lambda kv: kv[1]):
        if bid in sprites:
            images.append({'frame': num, 'file': rel + 'hall/' + bid + '.png'})
        elif num < fallback_frames:      # borrowed icon for a building without art
            images.append({'frame': num, 'defFile': spec['hallFallback'], 'defFrame': num})
    with open(os.path.join(out, '..', 'hallIcons.json'), 'w') as f:
        json.dump({'images': images}, f, indent='\t'); f.write('\n')

    # town-list icons: the chosen building over the background, 58x64 and 48x32, plus the
    # "built today" variants with the mark copied from the original icons
    icons = {}
    for kind, bid in spec['icons'].items():
        sprite, x, y = sprites[bid]
        for size, def_name, (normal, built) in (((58, 64), 'ITPT.DEF', (0, 1)), ((48, 32), 'ITPA.DEF', (2, 3))):
            w, h = size
            cx, cy = x + sprite.width / 2, y + sprite.height / 2
            span = max(sprite.width / w, sprite.height / h) * 1.05
            box = (int(cx - w * span / 2), int(cy - h * span / 2), int(cx + w * span / 2), int(cy + h * span / 2))
            canvas = Image.new('RGBA', SCREEN, (0, 0, 0, 0))
            canvas.paste(bg.convert('RGBA'), (0, 0))
            canvas.alpha_composite(sprite, (x, y))
            icon = canvas.crop(box).resize(size, Image.LANCZOS)
            name = '%s%s' % (kind, 'Large' if w == 58 else 'Small')
            icon.convert('RGB').save(os.path.join(out, 'icons', name + '.png'))
            done = icon.copy(); done.alpha_composite(built_mark(def_name, normal, built))
            done.convert('RGB').save(os.path.join(out, 'icons', name + 'Built.png'))
            icons.setdefault(kind, {}).setdefault('normal', {})['large' if w == 58 else 'small'] = rel + 'icons/' + name + '.png'
            icons[kind].setdefault('built', {})['large' if w == 58 else 'small'] = rel + 'icons/' + name + 'Built.png'

    with open(os.path.join(out, 'structures.json'), 'w') as f:
        json.dump({'background': rel + 'background.png', 'structures': structures, 'icons': icons}, f, indent='\t')
        f.write('\n')
    print('%s: %d buildings placed%s' % (faction, len(structures), ', missing art: ' + ', '.join(missing) if missing else ''))

    if preview_dir:
        def scene(chosen, name):
            canvas = bg.convert('RGBA')
            for bid in sorted(chosen, key=lambda b: structures[b]['z']):
                sprite, x, y = sprites[bid]
                canvas.alpha_composite(sprite, (x, y))
            canvas.save(os.path.join(preview_dir, '%s-%s.png' % (faction, name)))
        top = [c[-1] for c in CHAINS.values()] + [b for b in sprites if not any(b in c for c in CHAINS.values())]
        base = [c[0] for c in CHAINS.values()] + [b for b in sprites if not any(b in c for c in CHAINS.values()) and b != 'grail']
        scene([b for b in top if b in sprites], 'all-upgraded')
        scene([b for b in base if b in sprites], 'all-base')
        sheet = Image.new('RGB', (5 * 160, ((len(sprites) + 4) // 5) * 80), (40, 40, 40))
        for i, bid in enumerate(sorted(sprites)):
            sheet.paste(Image.open(os.path.join(out, 'hall', bid + '.png')), ((i % 5) * 160, (i // 5) * 80))
        sheet.save(os.path.join(preview_dir, '%s-hall-icons.png' % faction))

if __name__ == '__main__':
    preview = sys.argv[sys.argv.index('--preview') + 1] if '--preview' in sys.argv else None
    build(sys.argv[1], preview)
