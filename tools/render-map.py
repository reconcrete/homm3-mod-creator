"""Draw a .vmap the way the adventure map shows it: terrain, roads, every object with its shadow,
in VCMI's drawing order, so a map (or a new map picture) can be checked by eye before Anton plays.
.venv/bin/python tools/render-map.py MAP.vmap OUT.png [--zoom 2] [--crop x0,y0,x1,y1] [--marks]

--crop  tiles x0..x1, y0..y1 (inclusive) only, e.g. around one town or passage
--marks tile grid; blocked tiles red, visit tiles yellow, the 8 tiles a monster guards blue,
        walkable tiles under an object's picture (it looks like a wall but isn't) magenta dots

Engine details copied from VCMI 1.7 (client/mapView, lib/mapping/CMap.cpp): an object is drawn per
tile it covers, ordered by CMap::compareObjectBlitOrder (zIndex first, then whichever blocks the
tile right below the other's blocked tile, then the anchor row, heroes last); a picture's
bottom-right corner sits on the bottom-right corner of the anchor tile; generated shadows are the
silhouette sheared left (x + 0.5 * height), squashed to half height, black at alpha 128, blurred.
H3 sprites carry their own shadow in palette indices 1 (faint) and 4."""
import argparse, functools, json, os, re, sys, zipfile
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lod, h3def, townkit
from vjson import strip

ROOT = os.path.dirname(HERE)
SPRITES = os.path.join(ROOT, 'Content', 'sprites')
T = 32
TERRAIN = {'gr': 'GRASTL', 'dt': 'DIRTTL', 'sa': 'sandtl', 'sn': 'Snowtl', 'sw': 'Swmptl', 'rg': 'ROUGTL',
           'sb': 'Subbtl', 'lv': 'Lavatl', 'wt': 'Watrtl', 'rc': 'rocktl'}
ROADS = {'pd': 'dirtrd', 'pg': 'gravrd', 'pc': 'cobbrd'}
_names = None
_cache = {}


def archive_of(name):
    global _names
    if _names is None:
        _names = {}
        for arc in ('H3sprite.lod', 'H3ab_spr.lod'):
            p = os.path.join(townkit.H3DATA, arc)
            if os.path.exists(p):
                for n, *_ in lod.entries(p):
                    _names.setdefault(n.lower(), (p, n))
    return _names.get(name.lower())


def h3_frames(name, shadows=True):
    """Group 0 frames of an original DEF; shadow indices become translucent black."""
    key = ('def', name.lower(), shadows)
    if key not in _cache:
        found = archive_of(name if name.lower().endswith('.def') else name + '.def')
        if not found:
            _cache[key] = None
            return None
        data = lod.read(found[0], found[1])[1]
        _cache[key] = h3def.decode(data, shadows=shadows)
    return _cache[key]


def generated_shadow(im):
    a = im.split()[-1]
    box = a.getbbox()
    if not box:
        return None
    low = box[3] - 1
    # VCMI maps source (x, y) to (x - 0.5 * (low - y), (y + low) / 2); PIL wants the inverse
    sh = a.transform(im.size, Image.AFFINE, (1, -1.0, low, 0, 2, -low), resample=Image.BILINEAR)
    sh = sh.point(lambda v: 128 if v > 0 else 0).filter(ImageFilter.BoxBlur(1))
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.putalpha(sh)
    return out


def sprite(animation):
    """(picture, shadow or None) of a map object's first frame."""
    key = ('anim', animation)
    if key in _cache:
        return _cache[key]
    base = os.path.splitext(animation)[0]
    js = os.path.join(SPRITES, base + '.json')
    res = None
    if os.path.exists(js):
        d = json.load(open(js))
        seq = next(s for s in d['sequences'] if s.get('group', 0) == 0)
        im = Image.open(os.path.join(SPRITES, d['basepath'], seq['frames'][0])).convert('RGBA')
        ov = os.path.join(SPRITES, d['basepath'], os.path.splitext(seq['frames'][0])[0] + '-overlay.png')
        if os.path.exists(ov):                       # owner flags: shown red
            o = Image.open(ov).convert('RGBA')
            red = Image.new('RGBA', o.size, (220, 30, 30, 255))
            red.putalpha(o.split()[-1])
            im.alpha_composite(red)
        res = (im, generated_shadow(im) if seq.get('generateShadow') else None)
    else:
        groups = h3_frames(base)
        if groups:
            g = groups.get(0) or next(iter(groups.values()))
            res = (g[0][1], None)
    _cache[key] = res
    return res


def mask_cells(mask):
    h, w = len(mask), max(len(r) for r in mask)
    return {(c - (w - 1), r - (h - 1)): ch for r, row in enumerate(mask) for c, ch in enumerate(row.rjust(w, '0'))}


class Obj:
    def __init__(self, i, o):
        self.id, self.o = i, o
        self.x, self.y = o['x'], o['y']
        self.cells = mask_cells(o['template']['mask'])
        self.z = int(o['template'].get('zIndex', 0))
        self.hero = o['type'] == 'hero'

    def blocked(self):
        return [(self.x + dx, self.y + dy) for (dx, dy), ch in self.cells.items() if ch in 'BA']

    def blocking_at(self, t):
        return self.cells.get((t[0] - self.x, t[1] - self.y), '0') in 'BA'

    def covers(self, t):
        return self.cells.get((t[0] - self.x, t[1] - self.y), '0') != '0'


def blit_order(a, b):
    if a.z or b.z:
        if a.z != b.z:
            return -1 if a.z > b.z else 1
        return -1 if a.id < b.id else 1
    a_blocks_b = sum(a.blocking_at((x, y + 1)) for x, y in b.blocked())
    b_blocks_a = sum(b.blocking_at((x, y + 1)) for x, y in a.blocked())
    if a_blocks_b != b_blocks_a:
        return -1 if a_blocks_b < b_blocks_a else 1
    if a.y != b.y:
        return -1 if a.y < b.y else 1
    if b.hero != a.hero:
        return -1 if b.hero else 1
    return -1 if a.id < b.id else 1


def layers(cell):
    """[(code, view, flip)] of a cell code like 'gr12_' or 'gr12_pc3-' (terrain, then road)."""
    return [(c, int(v), f) for c, v, f in re.findall(r'([a-z]{2})(\d+)(.)', cell)]


def tile_image(code, view, flip):
    g = h3_frames(TERRAIN.get(code) or ROADS.get(code), shadows=False)
    im = g[0][view][1]
    if flip in '|+':
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if flip in '-+':
        im = im.transpose(Image.FLIP_TOP_BOTTOM)
    return im


def render(path, zoom=1, crop=None, marks=False):
    z = zipfile.ZipFile(path)
    return draw(json.loads(strip(z.read('objects.json').decode('utf-8'))), json.loads(z.read('surface_terrain.json')),
                zoom, crop, marks)


def draw(objects, terrain, zoom=1, crop=None, marks=False):
    """objects: map objects as in objects.json (type, x, y, template with animation and mask);
    terrain: rows of cell codes as in surface_terrain.json."""
    n_y, n_x = len(terrain), len(terrain[0])
    canvas = Image.new('RGBA', (n_x * T, n_y * T), (0, 0, 0, 255))
    for y in range(n_y):
        for x in range(n_x):
            for code, view, flip in layers(terrain[y][x]):
                if code in TERRAIN:
                    canvas.alpha_composite(tile_image(code, view, flip), (x * T, y * T))
                elif code in ROADS:        # VCMI draws a road half a tile down: its lower half on the next row
                    im = tile_image(code, view, flip)
                    canvas.alpha_composite(im.crop((0, 0, T, T // 2)), (x * T, y * T + T // 2))
                    if y + 1 < n_y:
                        canvas.alpha_composite(im.crop((0, T // 2, T, T)), (x * T, (y + 1) * T))
    objs = [Obj(i, o) for i, o in enumerate(objects) if o.get('l', 0) == 0]
    per_tile = {}
    for ob in objs:
        for (dx, dy), ch in ob.cells.items():
            if ch != '0':
                per_tile.setdefault((ob.x + dx, ob.y + dy), []).append(ob)
    layer = canvas.copy()
    for (tx, ty), lst in per_tile.items():
        if not (0 <= tx < n_x and 0 <= ty < n_y):
            continue
        lst.sort(key=functools.cmp_to_key(blit_order))
        box = (tx * T, ty * T, tx * T + T, ty * T + T)
        tile = layer.crop(box)
        for ob in lst:
            sp = sprite(ob.o['template']['animation'])
            if not sp:
                continue
            im, shadow = sp
            left, top = (ob.x + 1) * T - im.width, (ob.y + 1) * T - im.height
            for part in (shadow, im):
                if part is not None:
                    piece = part.crop((box[0] - left, box[1] - top, box[2] - left, box[3] - top))
                    tile.alpha_composite(piece)
        canvas.paste(tile, box[:2])
    if marks:
        over = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        blocked, visit, guard, under = set(), set(), set(), set()
        for ob in objs:
            blocked |= set(ob.blocked())
            visit |= {(ob.x + dx, ob.y + dy) for (dx, dy), ch in ob.cells.items() if ch == 'A'}
            if ob.o['type'] == 'monster':
                guard |= {(ob.x + dx, ob.y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        for ob in objs:
            if ob.o['type'] in ('monster', 'hero') or ob.z:
                continue
            sp = sprite(ob.o['template']['animation'])
            if not sp:
                continue
            a = sp[0].split()[-1]
            left, top = (ob.x + 1) * T - sp[0].width, (ob.y + 1) * T - sp[0].height
            for ty in range(top // T, (top + sp[0].height) // T + 1):
                for tx in range(left // T, (left + sp[0].width) // T + 1):
                    if (tx, ty) in blocked or not (0 <= tx < n_x and 0 <= ty < n_y):
                        continue
                    # a free tile counts as "under the picture" when the picture covers most of its lower half
                    sub = a.crop((tx * T - left, ty * T - top + T // 2, tx * T - left + T, ty * T - top + T))
                    hist = sub.histogram()
                    if sum(hist[200:]) > 0.5 * T * T // 2:
                        under.add((tx, ty))
        for x in range(n_x):
            for y in range(n_y):
                r = (x * T, y * T, x * T + T - 1, y * T + T - 1)
                d.rectangle(r, outline=(255, 255, 255, 40))
                if (x, y) in visit:
                    d.rectangle(r, fill=(255, 220, 0, 90))
                elif (x, y) in blocked:
                    d.rectangle(r, fill=(255, 0, 0, 45))
                if (x, y) in guard:
                    d.rectangle(r, outline=(60, 140, 255, 200), width=2)
                if (x, y) in under:
                    d.ellipse((x * T + 12, y * T + 12, x * T + 20, y * T + 20), fill=(255, 0, 255, 230))
        canvas.alpha_composite(over)
    if crop:
        x0, y0, x1, y1 = crop
        canvas = canvas.crop((x0 * T, y0 * T, (x1 + 1) * T, (y1 + 1) * T))
    if zoom != 1:
        canvas = canvas.resize((canvas.width * zoom, canvas.height * zoom), Image.NEAREST)
    return canvas


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('map')
    ap.add_argument('out')
    ap.add_argument('--zoom', type=int, default=1)
    ap.add_argument('--crop')
    ap.add_argument('--marks', action='store_true')
    a = ap.parse_args()
    im = render(a.map, a.zoom, tuple(int(v) for v in a.crop.split(',')) if a.crop else None, a.marks)
    im.convert('RGB').save(a.out)
    print(a.out, im.size)
