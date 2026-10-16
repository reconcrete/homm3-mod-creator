"""Make a test map: a copy of a small random map where one player's starting town is a
Naruto Heroes faction, written to the VCMI Maps folder.

python3 tools/make-testmap.py konohagakure
    -> Maps/naruto-test-konohagakure.vmap, "Naruto test: konohagakure" in the scenario list
python3 tools/make-testmap.py konohagakure --out naruto-test-kurama --name "Naruto test: Kurama" \
        --monster kurama:1:48:61 --garrison genin:80,hyugaMainBranch:25
    -> the same map plus a monster stack at tile (48, 61) and an army in the town garrison
python3 tools/make-testmap.py konohagakure --out naruto-test-konoha-town-full --buildings all
    -> the town starts with every building built (or --buildings base: no upgrades), to
       review the town screen without playing for weeks

Map files reference mod content by plain id (the map scope sees every active mod).
The base map is 72x72; the red town's gate is at (52, 59) and row 60 below it is open."""
import argparse, glob, json, os, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
from vjson import strip

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser()
ap.add_argument('faction')
ap.add_argument('--player', default='red')
ap.add_argument('--base', default=os.path.join(HERE, 'testmaps/base-72x72-4p.vmap'))
ap.add_argument('--out', help='map file name without extension (default naruto-test-<faction>)')
ap.add_argument('--name', help='map title in the scenario list')
ap.add_argument('--monster', action='append', default=[], metavar='ID:AMOUNT:X:Y',
                help='place a hostile stack of one of our creatures; repeatable')
ap.add_argument('--find', action='store_true', help='list free tiles near the gate where a monster can be clicked all over')
ap.add_argument('--buildings', choices=['base', 'all'],
                help="pre-build the player's town: every base building, or everything incl. upgrades and grail")
ap.add_argument('--garrison', metavar='ID:AMOUNT,...', help="army in the player's town garrison (up to 7 stacks)")
args = ap.parse_args()

out = os.path.expanduser('~/Library/Application Support/vcmi/Maps/%s.vmap' % (args.out or 'naruto-test-' + args.faction))
zin = zipfile.ZipFile(args.base)
files = {n: zin.read(n) for n in zin.namelist()}
header = json.loads(strip(files['header.json'].decode('utf-8')))
objects = json.loads(strip(files['objects.json'].decode('utf-8')))

our_creatures = {}
for f in glob.glob(os.path.join(ROOT, 'Content/config/*/creatures.json')):
    our_creatures.update(json.load(open(f, encoding='utf-8')))

header['players'][args.player]['allowedFactions'] = {'anyOf': ['naruto-heroes:' + args.faction]}
header['name'] = {'exactStrings': [args.name or 'Naruto test: ' + args.faction], 'localStrings': None,
                  'message': [0], 'numbers': None, 'stringsTextID': None}  # message code 0 = exactStrings[0]
for o in objects:
    if o.get('type') == 'town' and o['options'].get('owner') == args.player:
        o['subtype'] = args.faction
        o['template']['animation'] = 'AVCcasx0'
        if args.buildings:
            built = list(json.load(open(os.path.join(ROOT, 'Content/config', args.faction, 'faction.json'),
                                        encoding='utf-8'))[args.faction]['town']['buildings'])
            if args.buildings == 'base':
                upgrades = {'townHall', 'cityHall', 'capitol', 'citadel', 'castle', 'grail',
                            'mageGuild2', 'mageGuild3', 'mageGuild4', 'mageGuild5'}
                built = [b for b in built if b not in upgrades and not b.startswith('dwellingUp')]
            # canonical "<mod>:<building>" ids, as VCMI writes them ("core:fort" for original towns)
            o['options']['buildings'] = {'allOf': ['naruto-heroes:' + b for b in built]}
        if args.garrison:
            army = []
            for part in args.garrison.split(','):
                cid, amount = part.split(':')
                assert cid in our_creatures, 'unknown creature ' + cid
                army.append({'amount': int(amount), 'type': 'naruto-heroes:' + cid})
            assert len(army) <= 7
            o['options']['army'] = army

blocked = set()
for o in objects:
    if 'template' not in o:
        continue
    for r, row in enumerate(reversed(o['template']['mask'])):
        for c, ch in enumerate(reversed(row)):
            if ch in 'BAHT':
                blocked.add((o['x'] - c, o['y'] - r))
for n, spec in enumerate(args.monster):
    cid, amount, x, y = spec.split(':')
    x, y = int(x), int(y)
    assert cid in our_creatures, 'unknown creature ' + cid
    assert (x, y) not in blocked, 'tile (%d, %d) is occupied' % (x, y)
    sprite = os.path.splitext(our_creatures[cid]['graphics']['map'])[0]
    objects.append({
        'instanceName': 'monster_naruto_test_%d' % n, 'type': 'monster', 'subtype': cid,
        'x': x, 'y': y, 'l': 0,
        'options': {'amount': int(amount), 'character': 'savage', 'noGrowing': True, 'neverFlees': True},
        'template': {'animation': sprite, 'editorAnimation': '', 'mask': ['VV', 'VA'],
                     'visitableFrom': ['+++', '+-+', '+++']},
    })

# Clickability check. On the adventure map a monster is attacked by clicking its own tile or a
# tile next to it (its guard zone) that the hero can walk onto. Guarded tiles can only be
# entered directly from an unguarded tile, so a monster squeezed against a town or rocks has
# tiles under its sprite that can't be clicked. Report any such tile.
def reach(monsters):
    """Tiles the hero can walk to from the town gate without crossing a guard zone, and a
    test for whether a tile can be clicked (entered, or attacked from such a tile)."""
    terrain = json.loads(strip(files['surface_terrain.json'].decode('utf-8')))
    H, W = len(terrain), len(terrain[0])
    water = {(x, y) for y in range(H) for x in range(W) if terrain[y][x][:2] in ('wt', 'rc')}
    guarded = {(mx + dx, my + dy) for mx, my in monsters for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    town = next(o for o in objects if o.get('type') == 'town' and o['options'].get('owner') == args.player)
    gate = next((town['x'] - c, town['y'] - r) for r, row in enumerate(reversed(town['template']['mask']))
                for c, ch in enumerate(reversed(row)) if ch == 'A')
    free = lambda t: 0 <= t[0] < W and 0 <= t[1] < H and t not in blocked and t not in water
    seen, todo = {gate}, [gate]
    while todo:
        x, y = todo.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                t = (x + dx, y + dy)
                if t not in seen and free(t) and t not in guarded:
                    seen.add(t); todo.append(t)
    near = lambda t: any((t[0] + dx, t[1] + dy) in seen for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    return gate, free, seen, near

def clickable_problems(x, y, others):
    """Tiles under a 2x2 monster sprite at (x, y) that can't be clicked."""
    gate, free, seen, near = reach(others + [(x, y)])
    attackable = lambda t: free(t) and (t in seen or near(t))
    bad = [t for t in [(x - 1, y - 1), (x, y - 1), (x - 1, y)] if not attackable(t)]
    if not any(attackable((x + dx, y + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)):
        bad.append((x, y))
    return bad

def check_monsters():
    existing = [(o['x'], o['y']) for o in objects if o.get('type') == 'monster']
    ours = [tuple(int(v) for v in spec.split(':')[2:]) for spec in args.monster]
    for spec, (x, y) in zip(args.monster, ours):
        others = [m for m in existing if m != (x, y)]
        bad = clickable_problems(x, y, others)
        print('%s at (%d, %d): %s' % (spec.split(':')[0], x, y,
              'every tile under the sprite can be clicked' if not bad else 'NOT clickable: %s' % bad))
    if args.find:
        gate, free, seen, near = reach(existing)
        spots = sorted((abs(x - gate[0]) + abs(y - gate[1]), x, y) for x, y in seen
                       if (x, y) not in blocked and abs(x - gate[0]) + abs(y - gate[1]) >= 3
                       and not clickable_problems(x, y, existing))
        print('good spots near the gate %s (distance, x, y):' % (gate,), spots[:12])
check_monsters()

files['header.json'] = json.dumps(header, indent='\t', ensure_ascii=False).encode('utf-8')
files['objects.json'] = json.dumps(objects, indent='\t', ensure_ascii=False).encode('utf-8')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for n, data in files.items():
        z.writestr(n, data)
print(out)
