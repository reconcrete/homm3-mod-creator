"""Game screens (main menu, loading screen, scenario-selection backgrounds) redrawn for a mod's
theme with ComfyUI's homm3/screen-from-reference: the original screen gives the composition,
a picture of the mod's own art gives the style.

    .venv/bin/python tools/pipeline/screens.py THEME.json generate SCREEN [--seeds 1,2,3,4]
    .venv/bin/python tools/pipeline/screens.py THEME.json install SCREEN SEED
    .venv/bin/python tools/pipeline/screens.py THEME.json buttons

THEME.json (the mod's data, e.g. tools/menu-screens.json):
    {"style": "art/inbox/<a picture in the mod's style>",
     "title": "the logo text", "labels": "hide" (optional),
     "screens": {"gamselbk": "what the picture shows", ...}}

generate writes art/menu/<screen>/<seed>.png (1600x1200) and a contact sheet with the original
and the candidates side by side (sheet.png). Look at it: the composition of the original, the
button column or loading bar left clear, the logo spelled right, no stray text. install writes
Content/data/<NAME>.png (800x600) and Content/data2x/<NAME>.png (1600x1200, used at interface
scaling of 200% and with HD textures). VCMI finds both by name, nothing to register. buttons
rewrites every main-menu button (and the sub-menu labels) with the old background's glow turned
into plain shadow: on a new picture the original buttons show a pink halo. Then check in the
real game (tools/playtest). A mod that ships the same file name loads after ours
alphabetically and wins, with a "Potential conflict" warning in the log: russian-translation ships
all of these files, so with it switched on its Russian menu shows instead.
"""
import argparse, json, os, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import comfy, lod, h3pcx
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parents[2]
H3 = pathlib.Path(os.path.expanduser('~/Library/Application Support/vcmi/Data/H3bitmap.lod'))
OUT = ROOT / 'art' / 'menu'
SIZE = (1600, 1200)
# name in the archive, and what the layout must keep (the parts the game draws on top)
SCREENS = {
    'gamselbk': ('GamSelBk.pcx', 'The main menu: the title logo at the top left, the main figures in the left half, '
                 'the right third of the picture a calm, empty background with no figures and no text, because the '
                 'menu buttons are drawn there.'),
    'loadbar': ('loadbar.pcx', 'The loading screen: the title logo at the top center, a group of heroes in the '
                'middle, the bottom tenth of the picture plain ground with no figures, because the loading bar is '
                'drawn there.'),
    'gamselb0': ('gamselb0.pcx', 'A scenario-selection background: the title logo at the top left, the figures in '
                 'the left half, the right half a calm, empty sky.'),
    'gamselb1': ('gamselb1.pcx', 'A scenario-selection background: the title logo at the top left, one huge creature '
                 'in the left half, the right half a calm, empty sky.'),
}
RULES = ('Image 1 is a blurred layout sketch: keep only its composition, where the light, dark and busy areas sit. '
         'Paint a completely new picture: none of the figures, objects or letters of image 1 remain. '
         'Image 2 is the art style: '
         'painted fantasy game art with rich light. {layout} The logo text reads exactly "{title}" in big '
         'bevelled golden letters. No other text, no copyright line, no publisher logo, no frame or border. '
         'The picture shows: {subject}')


def original(screen):
    p = OUT / 'originals' / f'{screen}.png'
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        im =h3pcx.decode(lod.read(str(H3), SCREENS[screen][0])[1])
        (im if isinstance(im, Image.Image) else im[0]).convert('RGB').save(p)
    return p


def blurred(screen):
    # the original only as composition: sharp, the model copies its figures and logo (a knight survived)
    p = OUT / 'originals' / f'{screen}-layout.png'
    if not p.exists():
        from PIL import ImageFilter
        Image.open(original(screen)).filter(ImageFilter.GaussianBlur(18)).save(p)
    return p


def generate(theme, screen, seeds):
    layout = blurred(screen)
    style = ROOT / theme.get('style', '') if theme.get('style') else layout
    prompt = RULES.format(layout=SCREENS[screen][1], title=theme['title'], subject=theme['screens'][screen])
    out = OUT / screen
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for seed in seeds:
        saved = comfy.run('screen-from-reference', {
            ('layout', 'image'): str(layout), ('style', 'image'): str(style),
            ('prompt', 'prompt'): prompt, ('seed', 'noise_seed'): seed,
            ('size', 'width'): SIZE[0], ('size', 'height'): SIZE[1],
            ('save', 'filename_prefix'): f'homm3/screens/{screen}',
        }, out / 'raw')
        f = [p for paths in saved.values() for p in paths][0]
        dst = out / f'{seed}.png'
        Image.open(f).convert('RGB').resize(SIZE, Image.LANCZOS).save(dst)
        made.append((seed, dst))
        print(screen, seed, '->', dst)
    tiles = [('original', original(screen))] + made
    sheet = Image.new('RGB', (400 * len(tiles), 330), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, (label, p) in enumerate(tiles):
        sheet.paste(Image.open(p).convert('RGB').resize((400, 300), Image.LANCZOS), (400 * i, 30))
        d.text((400 * i + 6, 8), str(label), fill=(255, 220, 0))
    sheet.save(out / 'sheet.png')
    print(out / 'sheet.png')


def install(screen, seed):
    src = Image.open(OUT / screen / f'{seed}.png').convert('RGB')
    for folder, size in (('data', (800, 600)), ('data2x', SIZE)):
        d = ROOT / 'Content' / folder
        d.mkdir(parents=True, exist_ok=True)
        src.resize(size, Image.LANCZOS).save(d / f'{screen}.png', optimize=True)
        print('wrote', d / f'{screen}.png')


MAINMENU = pathlib.Path('/Applications/VCMI.app/Contents/Resources/Data/config/mainmenu.json')
SPRITES = H3.with_name('H3sprite.lod')


def unmix(img, bg, tol=22):
    """The original buttons and labels have their glow and shadow painted over the original
    background (a pink halo on the red main menu). Each pixel that is the background darkened by
    one factor (p = bg * (1 - a)) becomes black at alpha a, so it shades any new picture."""
    import numpy as np
    p = np.asarray(img.convert('RGBA'), dtype=np.float32)
    b = np.asarray(bg.convert('RGB'), dtype=np.float32)
    rgb, alpha = p[..., :3], p[..., 3]
    k = np.clip((rgb * b).sum(-1) / np.maximum((b * b).sum(-1), 1), 0, 1.2)    # best single factor
    fit = np.abs(rgb - b * k[..., None]).max(-1) <= tol
    halo = fit & (alpha > 0) & (k <= 1.02)
    out = p.copy()
    out[halo, :3] = 0
    out[halo, 3] = np.clip((1 - k[halo]) * 255, 0, 255)
    out[halo & (out[..., 3] < 12), 3] = 0
    # the glow was dithered: stray pixels that didn't fit stay pink specks. An opaque pixel with
    # few opaque neighbours is one of them: shadow too, at the alpha of the shadow around it
    from scipy.ndimage import uniform_filter
    solid = (out[..., 3] == 255).astype(np.float32)
    stray = (solid > 0) & (uniform_filter(solid, 5) < 0.3)
    shade = uniform_filter(np.where(halo, out[..., 3], 0), 5) / np.maximum(uniform_filter(halo.astype(np.float32), 5), 1e-3)
    out[stray, :3] = 0
    out[stray, 3] = shade[stray]
    return Image.fromarray(out.astype('uint8'), 'RGBA'), halo.mean()


def placed(img, bg, x, y, center):
    """The background under a button: its config position, refined by a small search (the
    halo matches the background exactly where the button was drawn)."""
    import numpy as np
    w, h = img.size
    x0, y0 = (x - w // 2, y - h // 2) if center else (x, y)
    best = None
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            crop = bg.crop((x0 + dx, y0 + dy, x0 + dx + w, y0 + dy + h))
            _, share = unmix(img, crop)
            if best is None or share > best[0]:
                best = (share, crop, dx, dy)
    return best


def buttons(theme):
    """Every main-menu button and label without the original background's glow:
    Content/sprites/<NAME>.json + naruto/menu/<NAME>/N.png, Content/data/<label>.png.
    They lie on the main menu picture (gamselbk) in all of mainmenu.json's menus. The labels
    ("New Game", "Load Game" in the sub-menus) sit at a fixed spot left of the buttons, where a new
    picture may have its hero's face: "labels": "hide" in THEME.json ships them empty."""
    sys.path.insert(0, str(ROOT / 'tools'))
    import h3def, vjson
    bg = Image.open(original('gamselbk')).convert('RGB')
    menus = vjson.load(str(MAINMENU))['window']['items']
    done = set()
    for m in menus:
        for b in m.get('buttons', []):
            name = b['name'].upper()
            if name in done:
                continue
            done.add(name)
            groups = h3def.decode(lod.read(str(SPRITES), name + '.DEF')[1], shadows=True)
            frames = [f for _, f in groups[0]]
            share, crop, dx, dy = placed(frames[0], bg, b['x'], b['y'], b.get('center'))
            d = ROOT / 'Content' / 'sprites' / 'naruto' / 'menu' / name
            d.mkdir(parents=True, exist_ok=True)
            for i, f in enumerate(frames):
                unmix(f, crop)[0].save(d / f'{i}.png', optimize=True)
            (ROOT / 'Content' / 'sprites' / f'{name}.json').write_text(json.dumps(
                {'basepath': f'naruto/menu/{name}/', 'sequences': [{'group': 0, 'frames': [f'{i}.png' for i in range(len(frames))]}]},
                indent='\t') + '\n')
            print(f'{name}: {len(frames)} frames, halo {share:.0%}, offset {dx},{dy}')
        for im in m.get('images', []):
            name = im['name'].lower()
            if name in done:
                continue
            done.add(name)
            label = h3pcx.decode(lod.read(str(H3), im['name'].upper() + '.PCX')[1])
            label = label if isinstance(label, Image.Image) else label[0]
            share, crop, dx, dy = placed(label.convert('RGBA'), bg, im['x'], im['y'], False)
            if theme.get('labels') == 'hide':
                Image.new('RGBA', label.size, (0, 0, 0, 0)).save(ROOT / 'Content' / 'data' / f'{name}.png')
            else:
                unmix(label, crop)[0].save(ROOT / 'Content' / 'data' / f'{name}.png', optimize=True)
            print(f'{name}: label, halo {share:.0%}, offset {dx},{dy}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('theme')
    ap.add_argument('action', choices=('generate', 'install', 'buttons'))
    ap.add_argument('screen', nargs='?', choices=SCREENS)
    ap.add_argument('seed', nargs='?', type=int)
    ap.add_argument('--seeds', default='1,2,3,4')
    a = ap.parse_args()
    theme = json.load(open(a.theme))
    if a.action == 'buttons':
        buttons(theme)
    elif a.action == 'generate':
        generate(theme, a.screen, [int(s) for s in a.seeds.split(',')])
    else:
        install(a.screen, a.seed)
