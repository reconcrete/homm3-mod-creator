"""Our adventure-map pictures (towns, dwellings, lairs) standing on real terrain next to the original
objects they replace, drawn by tools/render-map.py, for a look before anything goes into a map.
.venv/bin/python tools/preview-map-objects.py OUT_DIR [--only SLUG,...] [--terrain gr,sa,sn,dt]

Writes OUT_DIR/dwellings-<terrain>.png and towns-<terrain>.png (zoom 2): each object in its own
cell with a road leading to its visit tile; a second copy with --marks style tile marks (blocked red,
visit tile yellow, walkable tiles under the picture magenta) shows whether the drawn door is where a
hero enters and whether the picture spills over tiles a hero can walk on."""
import argparse, glob, importlib.util, json, os, random, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
spec = importlib.util.spec_from_file_location('render_map', os.path.join(HERE, 'render-map.py'))
rm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rm)
import townkit

ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(ROOT, 'Content', 'config')
VIEWS = {'gr': range(49, 73), 'sn': range(49, 73), 'dt': range(21, 45), 'sa': range(0, 24), 'rg': range(49, 73)}
ORIGINAL_DWELLINGS = [('guardhouse', 'AVGpike0', ['VVV', 'VBV', 'VBA']), ('archersTower', 'AVGcros0', ['VVV', 'VVV', 'VAB']),
                      ('goblinBarracks', 'AVGgobl0', ['VVV', 'VVV', 'VBA'])]
ORIGINAL_TOWNS = [('castle', 'AVCcasx0'), ('stronghold', 'AVCstrx0'), ('fortress', 'Avcftrx0')]


def ours_dwellings():
    out = []
    for f in sorted(glob.glob(os.path.join(CONFIG, '*', 'dwellings.json'))):
        for oid, d in json.load(open(f))['core:creatureGeneratorCommon']['types'].items():
            t = d['templates']['default']
            if t['animation'].startswith('naruto/'):
                out.append((oid, t['animation'], t['mask']))
    return out


def ours_towns():
    out = []
    for fac in ('konohagakure', 'sunagakure', 'kirigakure'):
        tpls = json.load(open(os.path.join(CONFIG, fac, 'faction.json')))[fac]['town']['mapObject']['templates']
        for level in ('village', 'fort', 'castle'):
            out.append(('%s-%s' % (fac, level), tpls[level]['animation'], tpls[level].get('mask', townkit.TOWN_MASK)))
    return out


def sheet(items, cell_w, cell_h, cols, terrain_code, marks, label_rows=True):
    rng = random.Random(1)
    rows = (len(items) + cols - 1) // cols
    W, H = cols * cell_w, rows * cell_h
    terrain = [['%s%d_' % (terrain_code, rng.choice(VIEWS[terrain_code])) for _ in range(W)] for _ in range(H)]
    objects = []
    for i, (name, anim, mask) in enumerate(items):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h
        ax, ay = cx + cell_w - 2, cy + cell_h - 2          # anchor: bottom-right mask tile
        objects.append({'type': 'creatureGeneratorCommon', 'x': ax, 'y': ay, 'template': {'animation': anim, 'mask': mask}})
    im = rm.draw(objects, terrain, zoom=2, marks=marks).convert('RGB')
    d = ImageDraw.Draw(im)
    for i, (name, *_ ) in enumerate(items):
        cx, cy = (i % cols) * cell_w * 64, (i // cols) * cell_h * 64
        d.text((cx + 4, cy + 3), name, fill=(255, 255, 0))
    return im


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--only')
    ap.add_argument('--terrain', default='gr,sa,sn')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    only = set(a.only.split(',')) if a.only else None
    pick = lambda items: [it for it in items if not only or any(o in it[0] or o in it[1] for o in only)]
    dw = [(n, an, m) for n, an, m in ORIGINAL_DWELLINGS] + pick(ours_dwellings())
    tw = [(n, an, townkit.TOWN_MASK) for n, an in ORIGINAL_TOWNS] + pick(ours_towns())
    for t in a.terrain.split(','):
        for kind, items, cw, ch, cols in (('dwellings', dw, 5, 5, 7), ('towns', tw, 8, 7, 4)):
            for marks in (False, True):
                p = os.path.join(a.out, '%s-%s%s.png' % (kind, t, '-marks' if marks else ''))
                sheet(items, cw, ch, cols, t, marks).save(p)
                print(p)
