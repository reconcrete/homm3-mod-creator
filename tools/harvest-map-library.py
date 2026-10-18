"""Harvest a library of map pieces from random maps made by VCMI's generator, so hand-built
maps use object entries and terrain codes the game itself wrote:
  objects     one entry per (type, subtype) (template + options), preferring ones on grass
  obstacles   obstacle entries whose tiles all stood on grass, with their blocked tiles
  roads       road piece (view, flip) seen for each pattern of road neighbours
  grass       grass views seen with grass on all 8 sides (plain interior tiles)
python3 tools/harvest-map-library.py [random maps...]  -> tools/testmaps/map-library.json
(default: every .vmap in the VCMI Maps/RandomMaps folder)"""
import collections, glob, json, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vjson import strip

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'testmaps/map-library.json')
OBSTACLES = {'mountain', 'oakTrees', 'pineTrees', 'trees', 'treesDUPLICATE', 'rock', 'grassHills', 'flowers', 'shrub',
             'mushrooms', 'lake', 'lakeDUPLICATE', 'crater', 'stump', 'log', 'mound', 'outcropping', 'deadVegetation',
             'roughHills', 'dirtHills', 'moss', 'mandrake', 'skull'}
TILE = re.compile(r'^([a-z]{2})(\d+)([_\-|+])(?:([a-z]{2})(\d+)([_\-|+]))?(?:([a-z]{2})(\d+)([_\-|+]))?$')
DIRS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]   # N NE E SE S SW W NW

def parse(cell):
    m = TILE.match(cell)
    if not m:
        return None
    t = {'terrain': m.group(1), 'view': int(m.group(2)), 'flip': m.group(3)}
    for i in (4, 7):
        if m.group(i):
            kind = 'road' if m.group(i).startswith('p') else 'river'
            t[kind] = (m.group(i), int(m.group(i + 1)), m.group(i + 2))
    return t

def tiles(o):
    """(dx, dy, char) of an object's mask relative to its anchor (bottom-right)."""
    mask = o['template']['mask']
    h, w = len(mask), max(len(r) for r in mask)
    return [(c - (w - 1), r - (h - 1), ch) for r, row in enumerate(mask) for c, ch in enumerate(row.rjust(w, '0'))]

files = sys.argv[1:] or sorted(glob.glob(os.path.expanduser('~/Library/Application Support/vcmi/Maps/RandomMaps/*.vmap')))
objects, obstacles, roads, grass = {}, {}, collections.defaultdict(collections.Counter), collections.Counter()
for f in files:
    z = zipfile.ZipFile(f)
    levels = {0: json.loads(strip(z.read('surface_terrain.json').decode()))}
    if 'underground_terrain.json' in z.namelist():
        levels[1] = json.loads(strip(z.read('underground_terrain.json').decode()))
    grid = {l: [[parse(c) for c in row] for row in t] for l, t in levels.items()}
    H, W = len(grid[0]), len(grid[0][0])
    at = lambda l, x, y: grid[l][y][x] if 0 <= x < W and 0 <= y < H else None
    for y in range(H):
        for x in range(W):
            t = at(0, x, y)
            if not t:
                continue
            ns = [at(0, x + dx, y + dy) for dx, dy in DIRS]
            if t['terrain'] == 'gr' and t['flip'] == '_' and all(n and n['terrain'] == 'gr' for n in ns):
                grass[t['view']] += 1
            if 'road' in t:
                key = ''.join('1' if n and 'road' in n else '0' for n in ns)
                roads[key][(t['road'][1], t['road'][2])] += 1
    objs = json.loads(strip(z.read('objects.json').decode()))
    for o in (objs.values() if isinstance(objs, dict) else objs):
        if 'template' not in o:      # e.g. the grail: no picture
            continue
        l = o.get('l', 0)
        cells = [(o['x'] + dx, o['y'] + dy, ch) for dx, dy, ch in tiles(o)]
        on_grass = all(at(l, x, y) and at(l, x, y)['terrain'] == 'gr' for x, y, ch in cells if ch != '0')
        clean = {k: v for k, v in o.items() if k not in ('x', 'y', 'l', 'instanceName')}
        if o['type'] in OBSTACLES:
            if on_grass:
                key = o['template']['animation'].lower()
                obstacles[key] = dict(clean, blocked=[[dx, dy] for dx, dy, ch in tiles(o) if ch in 'BA'])
            continue
        key = '%s/%s' % (o['type'], o.get('subtype'))
        if key not in objects or (on_grass and not objects[key][1]):
            objects[key] = (clean, on_grass)

lib = {'objects': {k: v[0] for k, v in sorted(objects.items())},
       'obstacles': [obstacles[k] for k in sorted(obstacles)],
       'roads': {k: [list(vf) for vf, _ in c.most_common()] for k, c in sorted(roads.items())},
       'grass': sorted(grass)}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(lib, open(OUT, 'w'), indent='\t', ensure_ascii=False)
print('%s: %d object types, %d grass obstacles, %d road patterns, %d plain grass views, from %d maps' % (
    os.path.relpath(OUT), len(lib['objects']), len(lib['obstacles']), len(lib['roads']), len(lib['grass']), len(files)))
