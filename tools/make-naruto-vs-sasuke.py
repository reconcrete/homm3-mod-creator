"""Two-player map "Naruto vs Sasuke: Valley of the End" (36x36, hot seat or vs AI).
python3 tools/make-naruto-vs-sasuke.py [--seed N]  -> Maps/naruto-vs-sasuke.vmap

Mirror-symmetric left/right, so both sides are equal:
  Naruto (red)  top left, Konohagakure     | Sasuke (blue) top right, Konohagakure
  neutral Sunagakure below Naruto          | neutral Kirigakure below Sasuke
  the Valley of the End in the middle: Kurama and Gyuki guard the best artifacts.
Walls of obstacles separate the five areas; each passage is guarded. Everything else (mines,
neutral lairs, the villages' map dwellings, artifacts, chests) is spread over the areas, the
Kage set parts in the matching places (Hokage: one part per home and one in the valley).
Object entries and terrain codes come from tools/testmaps/map-library.json (harvested from
VCMI's own random maps); the script checks that every object can be reached and that the
walls only open at the guarded passages."""
import argparse, collections, json, os, random, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vjson import strip
import townkit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
N = 36
OUT = os.path.expanduser('~/Library/Application Support/vcmi/Maps/naruto-vs-sasuke.vmap')
ap = argparse.ArgumentParser()
ap.add_argument('--seed', type=int, default=7)
args = ap.parse_args()
rng = random.Random(args.seed)

LIB = json.load(open(os.path.join(HERE, 'testmaps/map-library.json')))
ours = lambda f: json.load(open(os.path.join(ROOT, 'Content/config', f), encoding='utf-8'))
FACTIONS = {f: ours(f + '/faction.json')[f] for f in ('konohagakure', 'sunagakure', 'kirigakure')}
CREATURES = {}
for f in ('konohagakure', 'sunagakure', 'kirigakure', 'neutral'):
    CREATURES.update(ours(f + '/creatures.json'))
ARTIFACTS = ours('artifacts/artifacts.json')
DWELLINGS = {}
for f in ('konohagakure', 'sunagakure', 'kirigakure', 'neutral'):
    DWELLINGS.update(ours(f + '/dwellings.json')['core:creatureGeneratorCommon']['types'])
HEROES = ours('konohagakure/heroes.json')
CLASSES = ours('konohagakure/heroClasses.json')
base = zipfile.ZipFile(os.path.join(HERE, 'testmaps/base-72x72-4p.vmap'))
header = json.loads(strip(base.read('header.json').decode('utf-8')))
SPELLS = next(o for o in json.loads(strip(base.read('objects.json').decode('utf-8'))) if o.get('type') == 'town')['options']['possibleSpells']

# ------------------------------------------------------------------ grid bookkeeping

blocked = [[False] * N for _ in range(N)]     # obstacles and the blocked part of objects
reserved = [[False] * N for _ in range(N)]    # roads, passages, entrances: never put obstacles here
wall = set()                                  # tiles that must end up blocked
objects, visits = [], []                      # map objects; (tile, object) to check reachability
counter = collections.Counter()
inside = lambda x, y: 0 <= x < N and 0 <= y < N

def mask_cells(tpl):
    mask = tpl['mask']
    h, w = len(mask), max(len(r) for r in mask)
    return [(c - (w - 1), r - (h - 1), ch) for r, row in enumerate(mask) for c, ch in enumerate(row.rjust(w, '0'))]

def visit_offset(tpl):
    return next(((dx, dy) for dx, dy, ch in mask_cells(tpl) if ch == 'A'), (0, 0))

def entry_tiles(tpl, ax, ay):
    """Tiles a hero can enter the object from (visitableFrom, centered on the visit tile)."""
    vf = tpl.get('visitableFrom', ['+++', '+-+', '+++'])
    return [(ax + c - 1, ay + r - 1) for r in range(3) for c in range(3) if vf[r][c] == '+']

def fits(tpl, x, y, allow_reserved_visit=False):
    ox, oy = visit_offset(tpl)
    for dx, dy, ch in mask_cells(tpl):
        tx, ty = x + dx, y + dy
        if ch == '0':
            continue
        if not inside(tx, ty):
            return False
        if ch in 'BA' and (blocked[ty][tx] or (reserved[ty][tx] and not (allow_reserved_visit and (dx, dy) == (ox, oy)))):
            return False
    ax, ay = x + ox, y + oy
    return any(inside(ex, ey) and not blocked[ey][ex] and (ex, ey) not in wall for ex, ey in entry_tiles(tpl, ax, ay))

def add(kind, subtype, tpl, at, options=None, near=3, entrance=True):
    """Place an object so that its visitable tile is at `at` (or the nearest free spot)."""
    ox, oy = visit_offset(tpl)
    ax0, ay0 = at
    spots = sorted(((ax0 + dx, ay0 + dy) for dx in range(-near, near + 1) for dy in range(-near, near + 1)),
                   key=lambda p: (abs(p[0] - ax0) + abs(p[1] - ay0), p))
    for ax, ay in spots:
        x, y = ax - ox, ay - oy
        if fits(tpl, x, y, allow_reserved_visit=(kind in ('monster', 'hero'))):
            break
    else:
        raise SystemExit('no room for %s %s near %s' % (kind, subtype, at))
    for dx, dy, ch in mask_cells(tpl):
        if ch in 'BA':
            blocked[y + dy][x + dx] = True
    if entrance:   # keep one tile in front free: below if possible, never on a wall line
        entries = entry_tiles(tpl, ax, ay)
        for ex, ey in [(ax, ay + 1)] + entries:
            if (ex, ey) in entries and inside(ex, ey) and not blocked[ey][ex] and (ex, ey) not in wall:
                reserved[ey][ex] = True
                break
    counter[kind] += 1
    o = {'instanceName': '%s_%d' % (kind, counter[kind]), 'type': kind, 'subtype': subtype, 'x': x, 'y': y, 'l': 0,
         'template': dict(tpl, editorAnimation=tpl.get('editorAnimation', ''))}
    if options is not None:
        o['options'] = options
    objects.append(o)
    visits.append(((ax, ay), o, tpl))
    return ax, ay

def lib(key):
    e = LIB['objects'][key]
    return e['template'], json.loads(json.dumps(e.get('options'))) if 'options' in e else None

MIRROR = lambda p: (N - 1 - p[0], p[1])

# ------------------------------------------------------------------ the five areas

# walls: top (Naruto | Sasuke), bottom (Suna | Kiri), left (Naruto / Suna), right (Sasuke / Kiri),
# and the ring around the valley (x 13-22, y 13-22)
for y in range(0, 13):
    wall |= {(17, y), (18, y)}
for y in range(23, N):
    wall |= {(17, y), (18, y)}
for x in range(0, 13):
    wall |= {(x, 17), (x, 18), (N - 1 - x, 17), (N - 1 - x, 18)}
for i in range(13, 23):
    wall |= {(i, 13), (i, 22), (13, i), (22, i)}

def road_line(points):
    tiles = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 == x1:
            tiles += [(x0, y) for y in range(min(y0, y1), max(y0, y1) + 1)]
        else:
            tiles += [(x, y0) for x in range(min(x0, x1), max(x0, x1) + 1)]
    return tiles

road = set()
for line in ([(6, 7), (6, 9), (17, 9)],                 # Naruto's gate -> the top passage to Sasuke
             [(6, 9), (10, 9), (10, 31), (6, 31)],       # Naruto -> Sunagakure's gate
             [(10, 16), (14, 16)],                       # -> the valley (west opening)
             [(6, 31), (6, 33), (17, 33)],               # Sunagakure -> the bottom passage to Kirigakure
             [(10, 25), (15, 25), (15, 21)]):            # Sunagakure -> the valley (south opening)
    for t in road_line(line):
        road |= {t, MIRROR(t)}
for x, y in road:
    reserved[y][x] = True
    wall.discard((x, y))
PASSAGES = {'top': (17, 9), 'left': (10, 17), 'valleyWest': (13, 16), 'valleySouth': (15, 22), 'bottom': (17, 33)}

# ------------------------------------------------------------------ towns and heroes

def town(faction, at, owner=None, buildings=(), army=()):
    conf = FACTIONS[faction]
    level = 'fort' if 'fort' in buildings else 'village'
    tpl = dict(conf['town']['mapObject']['templates'][level])
    tpl = {'animation': tpl['animation'], 'mask': tpl.get('mask', townkit.TOWN_MASK), 'visitableFrom': ['---', '+-+', '+++']}
    options = {'possibleSpells': SPELLS, 'events': [], 'buildings': {'allOf': ['naruto-heroes:' + b for b in buildings]}}
    if owner:
        options['owner'] = owner
    if army:
        options['army'] = [{'amount': n, 'type': 'naruto-heroes:' + c} for c, n in army]
    return add('town', faction, tpl, at, options, near=0, entrance=False)

def hero(hid, owner, at):
    cls = HEROES[hid]['class']
    t = CLASSES[cls]['mapObject']['templates']['default']
    tpl = {'animation': t['animation'].split('.')[0], 'editorAnimation': t.get('editorAnimation', '').split('.')[0],
           'mask': ['VVV', 'VAV'], 'visitableFrom': ['+++', '+-+', '+++']}
    return add('hero', cls, tpl, at, {'owner': owner, 'type': 'naruto-heroes:' + hid}, near=0, entrance=False)

HOME = ['villageHall', 'tavern', 'fort', 'dwellingLvl1', 'dwellingLvl2']
town('konohagakure', (6, 6), 'red', HOME)
town('konohagakure', MIRROR((6, 6)), 'blue', HOME)
NEUTRAL = ['villageHall', 'fort', 'dwellingLvl1', 'dwellingLvl2', 'dwellingLvl3']
town('sunagakure', (6, 30), None, NEUTRAL, [('sunaGenin', 30), ('woodenPuppet', 12), ('windKunoichi', 8), ('desertScorpion', 3)])
town('kirigakure', MIRROR((6, 30)), None, NEUTRAL, [('mistGenin', 30), ('hunterNin', 12), ('hozukiBrawler', 8), ('summonedShark', 3)])
for x, y in [(6, 7), MIRROR((6, 7)), (6, 31), MIRROR((6, 31))]:
    reserved[y][x] = True
hero('narutoUzumaki', 'red', (6, 8))
hero('sasukeUchiha', 'blue', MIRROR((6, 8)))

# ------------------------------------------------------------------ everything else

def monster(cid, amount, at, near=2):
    c = CREATURES[cid]
    tpl = {'animation': os.path.splitext(c['graphics']['map'])[0], 'mask': ['VV', 'VA'], 'visitableFrom': ['+++', '+-+', '+++']}
    return add('monster', cid, tpl, at, {'amount': amount, 'character': 'hostile'}, near=near, entrance=False)

def artifact(aid, at):
    tpl = {'animation': ARTIFACTS[aid]['graphics']['map'], 'mask': ['VA'], 'visitableFrom': ['+++', '+-+', '+++']}
    return add('artifact', aid, tpl, at, {})

def dwelling(oid, at):
    return add('creatureGeneratorCommon', oid, DWELLINGS[oid]['templates']['default'], at)

def thing(key, at, **opt):
    tpl, options = lib(key)
    if opt:
        options = dict(options or {}, **opt)
    return add(key.split('/')[0], key.split('/')[1], tpl, at, options)

# passage guards (Naruto's side; mirrored for Sasuke, except the shared top and bottom ones)
monster('akatsukiMember', 3, PASSAGES['top'], near=0)
monster('manda', 2, PASSAGES['bottom'], near=0)
for side in (lambda p: p, MIRROR):
    monster('soundNinja' if side((0, 0)) == (0, 0) else 'rainNinja', 14, side(PASSAGES['left']), near=0)
    monster('curseMarkWarrior', 9, side(PASSAGES['valleyWest']), near=0)
    monster('cloudNinja', 9, side(PASSAGES['valleySouth']), near=0)

# each home (left: Naruto, right: Sasuke), then each neutral village's area (left: Suna, right: Kiri)
SWAP = {'hokageHat': 'hokageCloak', 'ichirakuRamenCoupon': 'kunai', 'gamaChanWallet': 'chakraPills',
        'desertBarracks': 'mistAcademy', 'puppetWorkshop': 'hunterNinDivision', 'soundVillageOutpost': 'rainVillageTower',
        'curseMarkLair': 'cloudVillageLighthouse', 'kazekageHat': 'mizukageHat', 'kazekageRobe': 'mizukageRobe',
        'gourdOfSand': 'hozukiWaterFlask', 'temarisGiantFan': 'kubikiribocho', 'hiruko': 'hiramekarei',
        'shukaku': 'isobu', 'soundNinja': 'rainNinja', 'sandForeheadProtector': 'mistForeheadProtector'}
for side, swap in ((lambda p: p, lambda k: k), (MIRROR, lambda k: SWAP.get(k, k))):
    # home
    thing('mine/sawmill', side((2, 11)))
    thing('mine/orePit', side((13, 3)))
    thing('mine/crystalCavern', side((3, 15)))
    dwelling('ninjaAcademy', side((14, 7)))
    dwelling('inuzukaKennels', side((10, 4)))
    dwelling('zetsuTree', side((5, 12)))
    dwelling('catHideout', side((15, 11)))
    dwelling('stoneVillageCliff', side((8, 15)))
    thing('learningStone/learningStone', side((12, 1)))
    thing('campfire/campfire', side((8, 11)))
    thing('treasureChest/treasureChest', side((12, 11)))
    thing('treasureChest/treasureChest', side((1, 8)))
    for res, at in (('wood', (4, 9)), ('wood', (11, 14)), ('ore', (9, 2)), ('ore', (15, 4)), ('gold', (7, 13)), ('crystal', (12, 15))):
        thing('resource/' + res, side(at))
    artifact(swap('ichirakuRamenCoupon'), side((8, 8)))
    artifact(swap('gamaChanWallet'), side((1, 14)))
    artifact(swap('hokageHat'), side((15, 1)))
    monster('ninjaCat', 12, side((14, 2)))
    monster('whiteZetsu', 30, side((4, 14)))
    monster('rogueNinja', 10, side((12, 4)))
    # neutral village's area
    thing('mine/goldMine', side((2, 21)))
    thing('mine/gemPond', side((14, 32)))
    thing('mine/alchemistLab', side((12, 29)))
    thing('mine/sulfurDune', side((7, 23)))
    dwelling(swap('desertBarracks'), side((3, 24)))
    dwelling(swap('puppetWorkshop'), side((15, 29)))
    dwelling('rogueNinjaHideout', side((9, 20)))
    dwelling(swap('soundVillageOutpost'), side((2, 32)))
    dwelling(swap('curseMarkLair'), side((15, 26)))
    thing('campfire/campfire', side((9, 27)))
    thing('treasureChest/treasureChest', side((1, 27)))
    thing('treasureChest/treasureChest', side((12, 23)))
    for res, at in (('gold', (8, 24)), ('gold', (11, 34)), ('mercury', (13, 27)), ('sulfur', (4, 32)), ('gems', (4, 35)), ('wood', (11, 20)), ('ore', (9, 34))):
        thing('resource/' + res, side(at))
    artifact(swap('kazekageHat'), side((1, 25)))
    artifact(swap('kazekageRobe'), side((14, 24)))
    artifact(swap('temarisGiantFan'), side((7, 35)))
    artifact(swap('hiruko'), side((12, 26)))
    artifact(swap('sandForeheadProtector'), side((5, 20)))
    monster('rogueNinja', 14, side((13, 24)))
    monster(swap('soundNinja'), 10, side((3, 20)))
    monster('stoneNinja', 8, side((8, 35)))
    monster('curseMarkWarrior', 4, side((11, 27)))
    # the tailed beast of the village guards the third Kage set part in a corner
    artifact(swap('gourdOfSand'), side((1, 35)))
    monster(swap('shukaku'), 1, side((2, 34)), near=1)

# the Valley of the End
artifact('rinnegan', (16, 16))
artifact('kusanagi', (18, 16))
monster('kurama', 1, (17, 17), near=0)
artifact('firstHokagesNecklace', (17, 21))
artifact('summoningContractToads', (19, 21))
monster('gyuki', 1, (18, 20), near=0)
dwelling('enmasCave', (15, 19))
dwelling('mandasLair', (21, 19))
dwelling('akatsukiHideout', (20, 15))
artifact('akatsukiCloak', (15, 14))
monster('akatsukiMember', 2, (16, 14), near=1)

# keep a walkable path from every object to the roads before any obstacle goes down
def reserve_path(start):
    prev, todo = {start: None}, collections.deque([start])
    while todo:
        t = todo.popleft()
        if t in road:
            while t is not None:
                reserved[t[1]][t[0]] = True
                t = prev[t]
            return True
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (t[0] + dx, t[1] + dy)
                if n not in prev and inside(*n) and n not in wall and (not blocked[n[1]][n[0]] or n in road):
                    prev[n] = t
                    todo.append(n)
    return False

for at, o, tpl in visits:
    if o['type'] in ('monster', 'hero'):
        continue
    entries = [e for e in entry_tiles(tpl, *at) if inside(*e) and not blocked[e[1]][e[0]] and e not in wall]
    assert any(reserve_path(e) for e in entries), 'no way to %s %s at %s' % (o['type'], o['subtype'], at)

# ------------------------------------------------------------------ obstacles: close the walls, then dress the land

OBST = sorted(LIB['obstacles'], key=lambda o: -len(o['blocked']))
SMALL = [o for o in OBST if len(o['blocked']) == 1]

def try_obstacle(o, x, y, allowed):
    for dx, dy, ch in mask_cells(o['template']):
        tx, ty = x + dx, y + dy
        if ch != '0' and not inside(tx, ty):
            return False
        if ch in 'BA' and (blocked[ty][tx] or reserved[ty][tx] or (tx, ty) not in allowed):
            return False
    for dx, dy, ch in mask_cells(o['template']):
        if ch in 'BA':
            blocked[y + dy][x + dx] = True
    counter['obstacle'] += 1
    objects.append({'instanceName': '%s_%d' % (o['type'], counter['obstacle']), 'type': o['type'], 'subtype': o['subtype'],
                    'x': x, 'y': y, 'l': 0, 'template': dict(o['template'], editorAnimation='')})
    return True

near_wall = {(x + dx, y + dy) for x, y in wall for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
for x, y in sorted(wall, key=lambda t: rng.random()):          # big pieces first, spilling one tile off the wall
    if blocked[y][x]:
        continue
    for o in OBST[:len(OBST) - len(SMALL)] if rng.random() < 0.8 else []:
        bx, by = rng.choice(o['blocked'])
        if try_obstacle(o, x - bx, y - by, near_wall):
            break
for x, y in sorted(wall):                                        # close every gap left with one-tile pieces
    if not blocked[y][x]:
        for o in sorted(SMALL, key=lambda o: rng.random()):
            if try_obstacle(o, x, y, {(x, y)}):
                break
open_wall = [t for t in wall if not blocked[t[1]][t[0]]]
assert not open_wall, 'wall tiles left open: %s' % open_wall

free = {(x, y) for x in range(N) for y in range(N) if not blocked[y][x] and not reserved[y][x]}
for _ in range(int(len(free) * 0.12)):                           # scattered trees, rocks and flowers
    x, y = rng.choice(sorted(free))
    o = rng.choice(OBST)
    bx, by = rng.choice(o['blocked'])
    try_obstacle(o, x - bx, y - by, free)

# ------------------------------------------------------------------ checks

monsters = {(o['x'], o['y']) for o in objects if o['type'] == 'monster'}
guarded = {(x + dx, y + dy) for x, y in monsters for dx in (-1, 0, 1) for dy in (-1, 0, 1)}

def reach(start, through_guards):
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                t = (x + dx, y + dy)
                if t in seen or not inside(*t) or (blocked[t[1]][t[0]] and not (through_guards and t in monsters)):
                    continue
                if not through_guards and t in guarded:
                    continue
                seen.add(t)
                todo.append(t)
    return seen

red_hero, blue_hero = (6, 8), MIRROR((6, 8))
everywhere = reach(red_hero, True) | reach(blue_hero, True)
unreachable = [(o['type'], o['subtype'], at) for at, o, tpl in visits if o['type'] not in ('hero',)
               and not any(e in everywhere or e in monsters for e in entry_tiles(tpl, *at))]
assert not unreachable, 'cannot be reached: %s' % unreachable
home = reach(red_hero, False)
leaks = [name for name, t in (('Sasuke', blue_hero), ('Suna gate', (6, 31)), ('Kiri gate', MIRROR((6, 31))), ('valley', (17, 15))) if t in home]
assert not leaks, "Naruto's home is open to %s without a fight" % leaks

# ------------------------------------------------------------------ terrain with roads

def road_piece(x, y):
    dirs = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
    key = ''.join('1' if (x + dx, y + dy) in road else '0' for dx, dy in dirs)
    if key in LIB['roads']:
        return LIB['roads'][key][0]
    cross = lambda k: k[0] + k[2] + k[4] + k[6]
    match = [v for k, v in LIB['roads'].items() if cross(k) == cross(key)]
    return max(match, key=len)[0] if match else LIB['roads']['00100010'][0]

terrain = []
for y in range(N):
    row = []
    for x in range(N):
        cell = 'gr%d_' % rng.choice(LIB['grass'])
        if (x, y) in road:
            view, flip = road_piece(x, y)
            cell += 'pc%d%s' % (view, flip)
        row.append(cell)
    terrain.append(row)

# ------------------------------------------------------------------ write

def text(s):
    return {'exactStrings': [s], 'localStrings': None, 'message': [0], 'numbers': None, 'stringsTextID': None}

header['mapLevels'] = {'surface': {'height': N, 'index': 0, 'layer': 'core:surface', 'width': N}}
header['name'] = text('Naruto vs Sasuke: Valley of the End / Наруто против Саске')
header['description'] = text(
    'Naruto and Sasuke start in two villages of the Leaf. Below them the neutral Sunagakure and Kirigakure wait to be '
    'taken, each with its Kage set and its tailed beast; between them lies the Valley of the End, where Kurama and Gyuki '
    'guard the Rinnegan, Kusanagi and the First Hokage\'s Necklace. Defeat the other to win.\n\n'
    'Наруто и Саске начинают в двух деревнях Листа. Под ними ждут нейтральные Суна и Кири, у каждой свой сет Каге и свой '
    'хвостатый зверь; между ними Долина Завершения, где Курама и Гьюки охраняют Риннеган, Кусанаги и Ожерелье Первого '
    'Хокаге. Победите соперника.')
header['players'] = {
    'red': {'allowedFactions': {'anyOf': ['naruto-heroes:konohagakure']}, 'canPlay': 'PlayerOrAI',
            'mainTown': {'generateHero': False, 'l': 0, 'x': objects[0]['x'], 'y': objects[0]['y']}},
    'blue': {'allowedFactions': {'anyOf': ['naruto-heroes:konohagakure']}, 'canPlay': 'PlayerOrAI',
             'mainTown': {'generateHero': False, 'l': 0, 'x': objects[1]['x'], 'y': objects[1]['y']}},
}
header['teams'] = [['red'], ['blue']]
header['mapVersion'] = text('1.0')
header['author'] = text('Naruto Heroes')
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('header.json', json.dumps(header, indent='\t', ensure_ascii=False).encode('utf-8'))
    z.writestr('objects.json', json.dumps(objects, indent='\t', ensure_ascii=False).encode('utf-8'))
    z.writestr('surface_terrain.json', json.dumps(terrain).encode('utf-8'))
kinds = collections.Counter(o['type'] for o in objects)
print(OUT)
print('  %d objects: %s' % (len(objects), ', '.join('%d %s' % (n, k) for k, n in kinds.most_common())))
