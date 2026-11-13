"""Building blocks for hand-built maps (tools/make-naruto-vs-sasuke.py, tools/make-shadow-of-akatsuki.py).

A HandMap is a one-level grass map built from scratch: walls of obstacles split it into areas,
objects go on given tiles (their entries come from tools/testmaps/map-library.json, harvested from
VCMI's own random maps, or from our content files), roads are drawn as terrain, and checks prove
that every object can be reached and that the walls only open where the script says.

Grid conventions (VCMI's): x to the right, y down; an object's x, y is its bottom-right mask tile;
`at` is always the tile a hero visits (the 'A' of the mask), the object is placed around it.
  blocked   tiles covered by obstacles and the blocked part of objects
  reserved  roads, entrances and paths: no obstacle may go there
  wall      tiles that must end up blocked (closed with obstacles by dress())
  road      road tiles (terrain), also reserved
  open      blocked tiles a hero can get through once their guard is beaten (pockets)
  gates     blocking objects that open (quest guards): passable only "through guards"
Events are not blocking in VCMI (a hero walks onto them), so their tile stays free (reserved)."""
import collections, json, os, random, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vjson import strip
import townkit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAPS = os.path.expanduser('~/Library/Application Support/vcmi/Maps')
MOD = 'naruto-heroes'

LIB = json.load(open(os.path.join(HERE, 'testmaps/map-library.json')))
ours = lambda f: json.load(open(os.path.join(ROOT, 'Content/config', f), encoding='utf-8'))
TOWNS = ('konohagakure', 'sunagakure', 'kirigakure')
FACTIONS = {f: ours(f + '/faction.json')[f] for f in TOWNS}
CREATURES, DWELLINGS, HEROES, CLASSES = {}, {}, {}, {}
for f in TOWNS + ('neutral',):
    CREATURES.update(ours(f + '/creatures.json'))
    DWELLINGS.update(ours(f + '/dwellings.json')['core:creatureGeneratorCommon']['types'])
for f in TOWNS:
    HEROES.update(ours(f + '/heroes.json'))
    CLASSES.update(ours(f + '/heroClasses.json'))
ARTIFACTS = ours('artifacts/artifacts.json')
BASE = zipfile.ZipFile(os.path.join(HERE, 'testmaps/base-72x72-4p.vmap'))
BASE_HEADER = json.loads(strip(BASE.read('header.json').decode('utf-8')))
SPELLS = next(o for o in json.loads(strip(BASE.read('objects.json').decode('utf-8'))) if o.get('type') == 'town')['options']['possibleSpells']
ALL_AROUND = ['+++', '+-+', '+++']

def mask_cells(tpl):
    """(dx, dy, char) of a template's mask relative to its anchor (bottom-right)."""
    mask = tpl['mask']
    h, w = len(mask), max(len(r) for r in mask)
    return [(c - (w - 1), r - (h - 1), ch) for r, row in enumerate(mask) for c, ch in enumerate(row.rjust(w, '0'))]

def visit_offset(tpl):
    return next(((dx, dy) for dx, dy, ch in mask_cells(tpl) if ch == 'A'), (0, 0))

def entry_tiles(tpl, ax, ay):
    """Tiles a hero can enter the object from (visitableFrom, centered on the visit tile)."""
    vf = tpl.get('visitableFrom', ALL_AROUND)
    return [(ax + c - 1, ay + r - 1) for r in range(3) for c in range(3) if vf[r][c] == '+']

def sprite_tiles(m):
    """The tiles a monster's 2x2 sprite covers besides its own tile (it stands bottom-right)."""
    return [(m[0] - 1, m[1] - 1), (m[0], m[1] - 1), (m[0] - 1, m[1])]

def road_line(points):
    tiles = []
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 == x1:
            tiles += [(x0, y) for y in range(min(y0, y1), max(y0, y1) + 1)]
        else:
            tiles += [(x, y0) for x in range(min(x0, x1), max(x0, x1) + 1)]
    return tiles

def text(s):
    """A map text given as an exact string (no translation)."""
    return {'exactStrings': [s], 'localStrings': None, 'message': [0], 'numbers': None, 'stringsTextID': None}

EMPTY_TEXT = {'exactStrings': None, 'localStrings': None, 'message': None, 'numbers': None, 'stringsTextID': None}

class Texts:
    """Translated map texts. VCMI 1.7 reads <language>.json files from the .vmap archive (keys
    without the map name, e.g. "header.name"; the loader prefixes "map.<file name>."), and map
    strings refer to them by text id (MetaString message code 2 = append text id)."""
    def __init__(self):
        self.strings = {'english': {}, 'russian': {}}

    def id(self, key, en, ru):
        assert key not in self.strings['english'], 'text key used twice: ' + key
        self.strings['english'][key], self.strings['russian'][key] = en, ru
        return key

    def say(self, key, en, ru):
        return {'exactStrings': None, 'localStrings': None, 'message': [2], 'numbers': None,
                'stringsTextID': [self.id(key, en, ru)]}

    def files(self):
        return {lang + '.json': s for lang, s in self.strings.items()}

def lib(key):
    e = LIB['objects'][key]
    return e['template'], json.loads(json.dumps(e.get('options'))) if 'options' in e else None

def h3(def_name, visitable_from=ALL_AROUND):
    """Template of an original object straight from Objects.txt (for objects the library lacks)."""
    t = townkit.h3_template(def_name if def_name.lower().endswith('.def') else def_name + '.def')
    return {'animation': t['animation'], 'editorAnimation': '', 'mask': t['mask'], 'visitableFrom': visitable_from}


class HandMap:
    def __init__(self, n, seed):
        self.n = n
        self.rng = random.Random(seed)
        self.blocked = [[False] * n for _ in range(n)]
        self.reserved = [[False] * n for _ in range(n)]
        self.wall, self.road, self.open, self.gates = set(), set(), set(), set()
        self.objects, self.visits = [], []     # map objects; (visit tile, object, template)
        self.at = {}                           # instance name -> visit tile
        self.counter = collections.Counter()
        self.clear_sprites = False             # keep the tiles under monster sprites free (see monster())
        self.clickable = set()

    def inside(self, x, y):
        return 0 <= x < self.n and 0 <= y < self.n

    def reserve(self, tiles):
        for x, y in tiles:
            self.reserved[y][x] = True

    def set_road(self, tiles):
        self.road |= set(tiles)
        for x, y in tiles:
            self.reserved[y][x] = True
            self.wall.discard((x, y))

    # ------------------------------------------------------------------ objects

    def fits(self, tpl, x, y, allow_reserved_visit=False):
        ox, oy = visit_offset(tpl)
        for dx, dy, ch in mask_cells(tpl):
            tx, ty = x + dx, y + dy
            if ch == '0':
                continue
            if not self.inside(tx, ty):
                return False
            if ch in 'BA' and (self.blocked[ty][tx] or (self.reserved[ty][tx] and not (allow_reserved_visit and (dx, dy) == (ox, oy)))):
                return False
        ax, ay = x + ox, y + oy
        return any(self.inside(ex, ey) and not self.blocked[ey][ex] and (ex, ey) not in self.wall for ex, ey in entry_tiles(tpl, ax, ay))

    def add(self, kind, subtype, tpl, at, options=None, near=3, entrance=True):
        """Place an object so that its visitable tile is at `at` (or the nearest free spot)."""
        ox, oy = visit_offset(tpl)
        ax0, ay0 = at
        spots = sorted(((ax0 + dx, ay0 + dy) for dx in range(-near, near + 1) for dy in range(-near, near + 1)),
                       key=lambda p: (abs(p[0] - ax0) + abs(p[1] - ay0), p))
        for ax, ay in spots:
            x, y = ax - ox, ay - oy
            if self.fits(tpl, x, y, allow_reserved_visit=(kind in ('monster', 'hero', 'event', 'questGuard'))):
                break
        else:
            raise SystemExit('no room for %s %s near %s' % (kind, subtype, at))
        for dx, dy, ch in mask_cells(tpl):
            if ch in 'BA':
                if kind == 'event':          # VCMI makes events 1x1, visitable, not blocking
                    self.reserved[y + dy][x + dx] = True
                else:
                    self.blocked[y + dy][x + dx] = True
        if entrance:   # keep one tile in front free: below if possible, never on a wall line
            entries = entry_tiles(tpl, ax, ay)
            for ex, ey in [(ax, ay + 1)] + entries:
                if (ex, ey) in entries and self.inside(ex, ey) and not self.blocked[ey][ex] and (ex, ey) not in self.wall:
                    self.reserved[ey][ex] = True
                    break
        self.counter[kind] += 1
        o = {'instanceName': '%s_%d' % (kind, self.counter[kind]), 'type': kind, 'subtype': subtype, 'x': x, 'y': y, 'l': 0,
             'template': dict(tpl, editorAnimation=tpl.get('editorAnimation', ''))}
        if options is not None:
            o['options'] = options
        self.objects.append(o)
        self.visits.append(((ax, ay), o, tpl))
        self.at[o['instanceName']] = (ax, ay)
        return o

    def town(self, faction, at, owner=None, buildings=(), army=(), name=None):
        conf = FACTIONS[faction]
        level = 'fort' if 'fort' in buildings else 'village'
        tpl = dict(conf['town']['mapObject']['templates'][level])
        tpl = {'animation': tpl['animation'], 'mask': tpl.get('mask', townkit.TOWN_MASK), 'visitableFrom': ['---', '+-+', '+++']}
        options = {'possibleSpells': SPELLS, 'events': [], 'buildings': {'allOf': [MOD + ':' + b for b in buildings]}}
        if owner:
            options['owner'] = owner
        if army:
            options['army'] = [{'amount': n, 'type': MOD + ':' + c} for c, n in army]
        if name:
            options['name'] = name
        return self.add('town', faction, tpl, at, options, near=0, entrance=False)

    def hero(self, hid, owner, at, army=(), experience=None):
        cls = HEROES[hid]['class']
        t = CLASSES[cls]['mapObject']['templates']['default']
        tpl = {'animation': t['animation'].split('.')[0], 'editorAnimation': t.get('editorAnimation', '').split('.')[0],
               'mask': ['VVV', 'VAV'], 'visitableFrom': ALL_AROUND}
        options = {'owner': owner, 'type': MOD + ':' + hid}
        if army:
            options['army'] = [{'amount': n, 'type': MOD + ':' + c} for c, n in army]
        if experience is not None:
            options['experience'] = experience
        return self.add('hero', cls, tpl, at, options, near=0, entrance=False)

    def monster(self, cid, amount, at, near=2, **extra):
        """A hostile stack; extra options (rewardMessage, rewardArtifact, neverFlees, ...) as given.
        With clear_sprites the three tiles under the rest of its 2x2 sprite must be open ground;
        they are reserved, and keep_monsters_clickable() later keeps a way to click each of them."""
        c = CREATURES[cid]
        tpl = {'animation': os.path.splitext(c['graphics']['map'])[0], 'mask': ['VV', 'VA'], 'visitableFrom': ALL_AROUND}
        o = self.add('monster', cid, tpl, at, dict({'amount': amount, 'character': 'hostile'}, **extra), near=near, entrance=False)
        if self.clear_sprites:
            m = self.at[o['instanceName']]
            bad = [t for t in sprite_tiles(m) if not self.inside(*t) or self.blocked[t[1]][t[0]] or t in self.wall]
            assert not bad, '%s at %s: its sprite covers %s (blocked or a wall)' % (cid, m, bad)
            self.reserve(sprite_tiles(m))
            self.clickable.add(m)
        return o

    def artifact(self, aid, at, near=3):
        tpl = {'animation': ARTIFACTS[aid]['graphics']['map'], 'mask': ['VA'], 'visitableFrom': ALL_AROUND}
        return self.add('artifact', aid, tpl, at, {}, near=near)

    def dwelling(self, oid, at, near=3):
        return self.add('creatureGeneratorCommon', oid, DWELLINGS[oid]['templates']['default'], at, near=near)

    def thing(self, key, at, near=3, **opt):
        tpl, options = lib(key)
        if opt:
            options = dict(options or {}, **opt)
        return self.add(key.split('/')[0], key.split('/')[1], tpl, at, options, near=near)

    @property
    def monsters(self):
        return {self.at[o['instanceName']] for o in self.objects if o['type'] == 'monster'}

    # ------------------------------------------------------------------ obstacles

    def reserve_path(self, start, avoid=()):
        """Reserve a walkable path from `start` to the nearest road tile (not through `avoid`)."""
        prev, todo = {start: None}, collections.deque([start])
        while todo:
            t = todo.popleft()
            if t in self.road:
                while t is not None:
                    self.reserved[t[1]][t[0]] = True
                    t = prev[t]
                return True
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (t[0] + dx, t[1] + dy)
                    if n not in prev and n not in avoid and self.inside(*n) and n not in self.wall and \
                            (not self.blocked[n[1]][n[0]] or n in self.road or n in self.open):
                        prev[n] = t
                        todo.append(n)
        return False

    def reserve_paths(self):
        """Keep a walkable path from every object to the roads before any obstacle goes down."""
        for at, o, tpl in self.visits:
            if o['type'] in ('monster', 'hero'):
                continue
            entries = [e for e in entry_tiles(tpl, *at) if self.inside(*e) and not self.blocked[e[1]][e[0]] and e not in self.wall]
            assert any(self.reserve_path(e) for e in entries), 'no way to %s %s at %s' % (o['type'], o['subtype'], at)

    def keep_monsters_clickable(self):
        """For every monster placed with clear_sprites: keep, next to each tile under its sprite, a
        tile outside its guard zone with a path to the road, so a click there attacks it."""
        for m in sorted(self.clickable):
            zone = {(m[0] + dx, m[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
            for s in sprite_tiles(m):
                around = sorted(((s[0] + dx, s[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)),
                                key=lambda t: (t in self.road, self.reserved[t[1]][t[0]] if self.inside(*t) else False), reverse=True)
                ok = [t for t in around if t not in zone and self.inside(*t) and t not in self.wall and not self.blocked[t[1]][t[0]]]
                assert any(self.reserve_path(t, avoid=zone) for t in ok), 'monster at %s: no way to click %s' % (m, s)

    def try_obstacle(self, o, x, y, allowed):
        for dx, dy, ch in mask_cells(o['template']):
            tx, ty = x + dx, y + dy
            if ch != '0' and not self.inside(tx, ty):
                return False
            if ch in 'BA' and (self.blocked[ty][tx] or self.reserved[ty][tx] or (tx, ty) not in allowed):
                return False
        for dx, dy, ch in mask_cells(o['template']):
            if ch in 'BA':
                self.blocked[y + dy][x + dx] = True
        self.counter['obstacle'] += 1
        self.objects.append({'instanceName': '%s_%d' % (o['type'], self.counter['obstacle']), 'type': o['type'], 'subtype': o['subtype'],
                             'x': x, 'y': y, 'l': 0, 'template': dict(o['template'], editorAnimation='')})
        return True

    def dress(self, density=0.12):
        """Close the walls with obstacles (big pieces first, then one-tile pieces), then scatter
        trees, rocks and flowers over a share of the free land."""
        rng = self.rng
        OBST = sorted(LIB['obstacles'], key=lambda o: -len(o['blocked']))
        SMALL = [o for o in OBST if len(o['blocked']) == 1]
        near_wall = {(x + dx, y + dy) for x, y in self.wall for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        for x, y in sorted(self.wall, key=lambda t: rng.random()):      # big pieces, spilling one tile off the wall
            if self.blocked[y][x]:
                continue
            for o in OBST[:len(OBST) - len(SMALL)] if rng.random() < 0.8 else []:
                bx, by = rng.choice(o['blocked'])
                if self.try_obstacle(o, x - bx, y - by, near_wall):
                    break
        for x, y in sorted(self.wall):                                   # close every gap left with one-tile pieces
            if not self.blocked[y][x]:
                for o in sorted(SMALL, key=lambda o: rng.random()):
                    if self.try_obstacle(o, x, y, {(x, y)}):
                        break
        open_wall = [t for t in self.wall if not self.blocked[t[1]][t[0]]]
        assert not open_wall, 'wall tiles left open: %s' % open_wall
        free = {(x, y) for x in range(self.n) for y in range(self.n) if not self.blocked[y][x] and not self.reserved[y][x]}
        for _ in range(int(len(free) * density)):
            x, y = rng.choice(sorted(free))
            o = rng.choice(OBST)
            bx, by = rng.choice(o['blocked'])
            self.try_obstacle(o, x - bx, y - by, free)

    # ------------------------------------------------------------------ checks

    def reach(self, start, through_guards, ignore=(), gates_open=False):
        """Tiles a hero can walk to from `start`. Without through_guards a guard zone (the 8 tiles
        around a monster) and a closed gate stop him; with it every monster and gate counts as
        beaten. Monsters in `ignore` (and the gates, if gates_open) count as beaten in either case."""
        ignore = set(ignore)
        guarded = {(x + dx, y + dy) for x, y in self.monsters - ignore for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        passable = (self.monsters | self.gates) if through_guards else ignore | (self.gates if gates_open else set())
        seen, todo = {start}, [start]
        while todo:
            x, y = todo.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    t = (x + dx, y + dy)
                    if t in seen or not self.inside(*t) or (self.blocked[t[1]][t[0]] and t not in passable):
                        continue
                    if not through_guards and (t in guarded or (t in self.gates and not gates_open)):
                        continue
                    seen.add(t)
                    todo.append(t)
        return seen

    def unreachable(self, starts):
        """Objects no hero can visit from any of `starts`, even after beating every guard."""
        everywhere = set().union(*(self.reach(s, True) for s in starts))
        return [(o['type'], o['subtype'], at) for at, o, tpl in self.visits if o['type'] != 'hero'
                and not any(e in everywhere or e in self.monsters or e in self.gates for e in entry_tiles(tpl, *at))]

    def unclickable(self, start):
        """Tiles under a monster's sprite (2x2, the monster on its bottom-right) that can't be
        clicked: a click on a guarded tile attacks only if the hero can step onto it straight
        from a tile outside every guard zone. Other monsters count as beaten."""
        bad = []
        for m in sorted(self.monsters):
            seen = self.reach(start, False, ignore=self.monsters - {m}, gates_open=True)
            free = lambda t: self.inside(*t) and not self.blocked[t[1]][t[0]]
            near = lambda t: any((t[0] + dx, t[1] + dy) in seen for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            sprite = sprite_tiles(m)
            bad += [(m, t) for t in sprite if not (free(t) and near(t))]
            if not near(m) and not any(free(t) and near(t) for t in sprite):
                bad.append((m, m))
        return bad

    # ------------------------------------------------------------------ terrain and output

    def terrain(self):
        rng = self.rng
        def road_piece(x, y):
            dirs = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
            key = ''.join('1' if (x + dx, y + dy) in self.road else '0' for dx, dy in dirs)
            if key in LIB['roads']:
                return LIB['roads'][key][0]
            cross = lambda k: k[0] + k[2] + k[4] + k[6]
            match = [v for k, v in LIB['roads'].items() if cross(k) == cross(key)]
            return max(match, key=len)[0] if match else LIB['roads']['00100010'][0]
        rows = []
        for y in range(self.n):
            row = []
            for x in range(self.n):
                cell = 'gr%d_' % rng.choice(LIB['grass'])
                if (x, y) in self.road:
                    view, flip = road_piece(x, y)
                    cell += 'pc%d%s' % (view, flip)
                row.append(cell)
            rows.append(row)
        return rows

    def write(self, path, header, terrain, extra=None):
        header['mapLevels'] = {'surface': {'height': self.n, 'index': 0, 'layer': 'core:surface', 'width': self.n}}
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('header.json', json.dumps(header, indent='\t', ensure_ascii=False).encode('utf-8'))
            z.writestr('objects.json', json.dumps(self.objects, indent='\t', ensure_ascii=False).encode('utf-8'))
            z.writestr('surface_terrain.json', json.dumps(terrain).encode('utf-8'))
            for name, data in (extra or {}).items():
                z.writestr(name, json.dumps(data, indent='\t', ensure_ascii=False).encode('utf-8'))
        kinds = collections.Counter(o['type'] for o in self.objects)
        print(path)
        print('  %d objects: %s' % (len(self.objects), ', '.join('%d %s' % (n, k) for k, n in kinds.most_common())))

    def ascii(self, marks=None):
        """Text picture of the map: # blocked, w wall still open, = road, . free, + reserved, letters from `marks`."""
        marks = marks or {}
        out = []
        for y in range(self.n):
            row = ''
            for x in range(self.n):
                c = marks.get((x, y))
                if c is None:
                    c = '#' if self.blocked[y][x] else 'w' if (x, y) in self.wall else '=' if (x, y) in self.road \
                        else '+' if self.reserved[y][x] else '.'
                row += c
            out.append('%2d %s' % (y, row))
        return '\n'.join(['   ' + ''.join(str(x % 10) for x in range(self.n))] + out)
