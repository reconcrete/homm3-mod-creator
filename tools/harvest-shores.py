"""Harvest coastline terrain pieces from random maps made by VCMI's generator, for hand-built maps
with sea (tools/handmap.py, HandMap.water). A coast has transition pictures on both sides:
  water   water tiles next to land: shore views 0-19, keyed by which of the 8 neighbours are land
  grass   grass tiles next to water: the sand-edge views 20-37, keyed by which neighbours are water
          (only tiles whose other neighbours are all grass, so the edge is a pure grass-water one)
Each key (N NE E SE S SW W NW, '1' = the other side) lists the (view, flip) pairs the generator used,
most frequent first; `inner` lists plain water views (water on all 8 sides).
.venv/bin/python tools/harvest-shores.py [random maps...]  -> tools/testmaps/shore-library.json
(default: every .vmap in the VCMI Maps/RandomMaps folder)"""
import collections, glob, json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'testmaps/shore-library.json')
DIRS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]   # N NE E SE S SW W NW
CELL = re.compile(r'^([a-z]{2})(\d+)([_\-|+])')

files = sys.argv[1:] or glob.glob(os.path.expanduser('~/Library/Application Support/vcmi/Maps/RandomMaps/*.vmap'))
water, grass, inner = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter), collections.Counter()
for f in files:
    z = zipfile.ZipFile(f)
    for name in z.namelist():
        if not name.endswith('_terrain.json'):
            continue
        t = [[CELL.match(c).groups() for c in row] for row in json.loads(z.read(name))]
        h, w = len(t), len(t[0])
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                ter, view, flip = t[y][x]
                around = [t[y + dy][x + dx][0] for dx, dy in DIRS]
                if ter == 'wt':
                    key = ''.join('0' if a == 'wt' else '1' for a in around)
                    (inner if key == '00000000' else water[key])[(int(view), flip)] += 1
                elif ter == 'gr' and 'wt' in around and all(a in ('gr', 'wt') for a in around):
                    grass[''.join('1' if a == 'wt' else '0' for a in around)][(int(view), flip)] += 1
lib = {'water': {k: [list(p) for p, _ in c.most_common()] for k, c in sorted(water.items())},
       'grass': {k: [list(p) for p, _ in c.most_common()] for k, c in sorted(grass.items())},
       'inner': [list(p) for p, _ in inner.most_common()]}
json.dump(lib, open(OUT, 'w'), indent=1)
print(OUT, '%d water keys, %d grass keys, %d plain water views' % (len(lib['water']), len(lib['grass']), len(lib['inner'])))
