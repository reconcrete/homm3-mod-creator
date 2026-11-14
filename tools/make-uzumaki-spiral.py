"""Co-op story map "Naruto: The Uzumaki Spiral" (36x36, one level): two humans, red Naruto (Konoha)
and blue Gaara (Suna), on one team against teal, an AI Yagura (Kiri).
python3 tools/make-uzumaki-spiral.py [--seed N] [--ascii]  -> Maps/naruto-uzumaki-spiral.vmap

The ruins of Uzushiogakure, the whirlpool village of the Uzumaki clan, stand on a round island
laid out as the clan's double spiral. Red lands on the north-west coast, blue on the south-east;
each walks a spiral road of about 70 tiles into the central temple, where Yagura (teal) holds the
ruins and the masked man is binding Isobu, the Three-Tails.

Each road has two seals, and the key to each lies in the partner's arm (co-op):
  gate 1  a border guard; its keymaster tent stands in the partner's first stretch (A). A two-way
          portal joins the two A stretches. Once a key holder walks through, it is gone for both.
  gate 2  a quest guard that wants a treasure lying in the partner's second stretch (B), guarded.
          A second two-way portal joins the B stretches; allied heroes meet and trade.
  shrine  Isobu's shrine opens with two seals: the first only for Gaara, the second only for Naruto.
Teal's heroes reach the middle of either arm through a one-way portal in the temple, so Kiri raids
the B stretches (and the towns, once gate 1 is open). Win: defeat Isobu. Lose: Naruto or Gaara
falls, or day 36 comes (Isobu is bound).

Texts in English and Russian (the map's own files plus the mod's translations, see
Texts.register_in_mod). Built with tools/handmap.py and its checks."""
import argparse, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handmap import HandMap, Texts, BASE_HEADER, MAPS, ROOT, MOD, EMPTY_TEXT, HEROES, lib, h3, road_line, mask_cells

N = 36
NAME = 'naruto-uzumaki-spiral'
OUT = os.path.join(ROOT, 'Content', 'maps', NAME + '.vmap')   # shipped with the mod (Content/maps)
ap = argparse.ArgumentParser()
ap.add_argument('--seed', type=int, default=3)
ap.add_argument('--ascii', action='store_true', help='print a text picture of the map')
args = ap.parse_args()
m = HandMap(N, args.seed)
m.clear_sprites = True
T = Texts()
j = lambda o: json.loads(json.dumps(o))
mod = lambda i: MOD + ':' + i

# ------------------------------------------------------------------ geometry: island, spiral arms, temple

CX = CY = 18.0                    # island centre (between tiles 17 and 18)
ISLAND = 17.2                     # radius of the land
PLAZA = 5.3                       # radius of the temple plaza
PITCH = 1.6                       # radius gained per radian along an arm
WIDTH = 3.7                       # corridor width
TMAX = (ISLAND - 1.2 - PLAZA) / PITCH    # arm parameter at the coast (about 6.7, a little over one turn)
ARMS = {'red': math.pi, 'blue': 0.0}     # angle where each arm leaves the plaza; red ends north-west, blue south-east


def polar(x, y):
    dx, dy = x + 0.5 - CX, y + 0.5 - CY
    return math.hypot(dx, dy), math.atan2(dy, dx)


def arm_at(x, y):
    """(arm, t) of a corridor tile, None otherwise; t = 0 at the plaza, TMAX at the coast."""
    r, th = polar(x, y)
    best = None
    for arm, phi in ARMS.items():
        a = (th - phi) % (2 * math.pi)
        for n in range(3):
            t = a + 2 * math.pi * n
            if t > TMAX + 0.4:
                break
            d = abs(r - (PLAZA + PITCH * t))
            if d < WIDTH / 2 and (best is None or d < best[2]):
                best = (arm, t, d)
    return best[:2] if best else None


def point(arm, t, side=0.0):
    """The corridor tile at parameter t; side moves across the corridor (+ outwards, in tiles)."""
    r = PLAZA + PITCH * t + side
    th = ARMS[arm] + t
    return int(math.floor(CX + r * math.cos(th))), int(math.floor(CY + r * math.sin(th)))


ARM, PLAZA_TILES = {}, set()
for y in range(N):
    for x in range(N):
        r, _ = polar(x, y)
        if r > ISLAND:
            continue
        if r < PLAZA:
            PLAZA_TILES.add((x, y))
            continue
        a = arm_at(x, y)
        if a:
            ARM[(x, y)] = a
# a landing at each arm's coastal end, wide enough for the home town: land pushed a little into the
# sea, at least one wall tile away from the other arm
LANDING = 7.4
for arm in ARMS:
    qx, qy = point(arm, TMAX + 0.45)
    other = {p for p, (a, _) in ARM.items() if a != arm}
    for y in range(N):
        for x in range(N):
            if math.hypot(x - qx, y - qy) <= LANDING and (x, y) not in PLAZA_TILES and \
                    not any((x + dx, y + dy) in other for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                ARM[(x, y)] = (arm, TMAX + 0.3)
# where the two arms come within a diagonal step of each other, both edge tiles become wall: a one-tile
# wall that touches only at a corner lets heroes slip through (found when random trees stopped plugging it)
touching = [p for p, (a, _) in ARM.items()
            if any(ARM.get((p[0] + dx, p[1] + dy), (a,))[0] != a for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
for p in touching:
    del ARM[p]
m.set_water([(x, y) for y in range(N) for x in range(N) if polar(x, y)[0] > ISLAND and (x, y) not in ARM])
m.wall |= {(x, y) for y in range(N) for x in range(N)
           if (x, y) not in m.water and (x, y) not in ARM and (x, y) not in PLAZA_TILES}


def section(arm, t, half=0.22):
    """Corridor tiles across the arm around parameter t."""
    return sorted(p for p, (a, tt) in ARM.items() if a == arm and abs(tt - t) * (PLAZA + PITCH * t) <= half * 4)


def choke(arm, t, gap, keep=(), half=0.22):
    """Wall the corridor across at t except the tile `gap` (a gate stands there) and `keep` (a guard's
    zone: walking through it means a fight, so the guard alone closes the way). Road tiles in the wall
    leave the road (it goes through the gap)."""
    for p in section(arm, t, half):
        if p != gap and p not in keep:
            m.wall.add(p)
            if p in m.road:
                m.road.discard(p)
                m.reserved[p[1]][p[0]] = False


def road_tile(arm, t):
    """The road tile across the arm at t (seals stand on the road)."""
    sec = section(arm, t)
    on_road = [p for p in sec if p in m.road]
    c = point(arm, t)
    return min(on_road or sec, key=lambda p: (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2)


# the roads: each arm's centre line, from the coast to the plaza
for arm in ARMS:
    pts = []
    steps = int(TMAX * 30)
    for i in range(steps + 1):
        p = point(arm, TMAX - TMAX * i / steps)
        if not pts or p != pts[-1]:
            pts.append(p)
    m.set_road([p for p in pts if p in ARM or p in PLAZA_TILES])


def picture():
    marks = {}
    for at, o, tpl in m.visits:
        marks[at] = {'monster': 'M', 'town': 'T', 'hero': 'H', 'event': 'e', 'questGuard': 'Q', 'seerHut': 'S',
                     'artifact': 'a', 'borderGuard': 'G', 'keymasterTent': 'K', 'monolithTwoWay': 'P',
                     'monolithOneWayEntrance': 'I', 'monolithOneWayExit': 'O'}.get(o['type'], 'o')
    pic = m.ascii(marks).split('\n')
    return '\n'.join(row.replace('#', '#') for row in pic)


GEOMETRY_ONLY = os.environ.get('GEOMETRY_ONLY')
if GEOMETRY_ONLY:
    marks = {}
    for arm in ARMS:
        for k in range(int(TMAX * 2) + 1):
            marks[point(arm, k / 2)] = 'abcdefghijklmnop'[k] if arm == 'red' else 'ABCDEFGHIJKLMNOP'[k]
    for p in m.water:
        marks[p] = '~'
    print(m.ascii(marks))
    print('TMAX %.2f; marks every t=0.5 from the plaza: red a.., blue A..' % TMAX)
    sys.exit()

# ------------------------------------------------------------------ the shrine in the middle of the spiral
# Isobu's shrine: a 3x3 room at the very centre, entered from the north through two seals in a row
# (18, 16) -> seal 1 (18, 17), Gaara only -> seal 2 (18, 18), Naruto only -> the room (17-19, 19-21)
SHRINE = {(x, y) for x in (17, 18, 19) for y in (19, 20, 21)}
SEAL1, SEAL2 = (18, 17), (18, 18)
for x in range(16, 21):
    for y in range(17, 23):
        if (x, y) not in SHRINE and (x, y) not in (SEAL1, SEAL2):
            m.wall.add((x, y))
m.wall -= {(16, 17), (20, 17)}             # the seals' corridor needs only its two neighbours closed
m.wall |= {(17, 17), (19, 17)}
m.set_road(road_line([(13, 16), (23, 16)]))

# ------------------------------------------------------------------ object builders (as in make-shadow-of-akatsuki.py)

LIMITER = dict(j(lib('seerHut/0')[1]['quest']['limiter']), artifacts=[])
REWARD = dict(j(lib('seerHut/0')[1]['rewardable']['info'][0]['reward']), creatures=[])


def limiter(**kw):
    return dict(j(LIMITER), **kw)


def reward(exp=0, artifacts=(), creatures=(), primary=(0, 0, 0, 0), resources=None, spells=()):
    r = dict(j(REWARD), heroExperience=exp, primary=list(primary),
             creatures=[{'amount': n, 'type': mod(c)} for c, n in creatures])
    if artifacts:
        r['artifacts'] = [mod(a) for a in artifacts]
    if resources:
        r['resources'] = resources
    if spells:
        r['spells'] = ['core:' + s for s in spells]
    return r


def rewardable(key, message, rew):
    opt = j(lib('pandoraBox/object')[1])
    info = opt['rewardable']['info'][0]
    info['message'] = T.say(key, *message) if message else j(EMPTY_TEXT)
    info['reward'] = rew
    return opt


def quest(key, first, nxt, done, mission):
    q = j(lib('seerHut/0')[1]['quest'])
    q['firstVisitText'] = T.say(key + '.first', *first)
    q['nextVisitText'] = T.say(key + '.next', *nxt)
    q['completedText'] = T.say(key + '.completed', *done)
    q['limiter'] = limiter(**mission)
    return q


def gate(key, at, texts, mission):
    """A quest guard: blocks its tile until the quest is done, then disappears (for everyone)."""
    o = m.add('questGuard', 'object', h3('avxbor80'), at, {'quest': quest(key, *texts, mission=mission)}, near=0, entrance=False)
    m.gates.add(at)
    m.open.add(at)
    return o


COLORS = {'lblue': 0, 'green': 1, 'red': 2, 'dblue': 3, 'brown': 4, 'purple': 5, 'white': 6, 'black': 7}


def border_guard(color, at):
    """Disappears for everyone once a hero who visited the keymaster tent of its colour walks through."""
    o = m.add('borderGuard', color, h3('AVXbor%d0' % COLORS[color]), at, {}, near=0, entrance=False)
    m.gates.add(at)
    m.open.add(at)
    return o


def keymaster(color, at, near=3):
    return place('keymasterTent', color, h3('AVXkey%d0' % COLORS[color]), {}, at, near)


def guard(cid, amount, at, key=None, text=None, carries=None, near=0):
    extra = {'character': 'savage', 'neverFlees': True, 'noGrowing': True}
    if text:
        extra['rewardMessage'] = T.say(key, *text)
    if carries:
        extra['rewardArtifact'] = mod(carries)
    return m.monster(cid, amount, at, near=near, **extra)


def checkpoint(arm, t, cid, amount, key=None, text=None, carries=None):
    """A guard standing across the road at about t. Walls go on the fewest corridor tiles around its
    zone that close every way past it, while each tile under its picture stays clickable from a tile
    outside the zone (VCMI attacks a clicked guard only then)."""
    import itertools
    from handmap import sprite_tiles
    open_ = lambda p: m.inside(*p) and p not in m.wall and not m.blocked[p[1]][p[0]]
    here = {p for p, (a, _) in ARM.items() if a == arm}
    for need_all in (True, False):           # all picture tiles clickable if possible, else at least one
      for dt in (0, 0.06, -0.06, 0.12, -0.12, 0.18, -0.18, 0.24, -0.24, 0.3, -0.3, 0.36, -0.36):
          for side in (0, 0.8, -0.8, 1.4, -1.4):
              at = on_arm(arm, t + dt, side)
              if at not in here or not open_(at):
                  continue
              zone = {(at[0] + dx, at[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
              sprite = sprite_tiles(at)
              if not all(open_(p) for p in sprite):
                  continue
              before, after = on_arm(arm, t + dt - 0.5), on_arm(arm, t + dt + 0.5)
              band = sorted(p for p in section(arm, t + dt, half=0.4) if p not in zone and open_(p) and not m.reserved[p[1]][p[0]]
                            and p not in (before, after))
              for n in range(len(band) + 1):
                  for walls in itertools.combinations(band, n):
                      walls = set(walls)
                      def flood(src):
                          seen, todo = {src}, [src]
                          while todo:
                              x, y = todo.pop()
                              for dx in (-1, 0, 1):
                                  for dy in (-1, 0, 1):
                                      q = (x + dx, y + dy)
                                      if q in seen or q in zone or q in walls or not open_(q) or (q not in here and q not in PLAZA_TILES):
                                          continue
                                      seen.add(q)
                                      todo.append(q)
                          return seen
                      side_a = flood(before)
                      if after in side_a:          # a way past that avoids the zone
                          continue
                      sides = flood(after)         # players arrive from the coast side (higher t)
                      hits = [any((sx + dx, sy + dy) in sides for dx in (-1, 0, 1) for dy in (-1, 0, 1)) for sx, sy in sprite]
                      clickable = all(hits) if need_all else any(hits)
                      if not clickable:
                          continue
                      g = guard(cid, amount, at, key, text, carries)
                      m.wall |= walls
                      return g
    raise SystemExit('no checkpoint spot for %s on the %s road at t=%.2f' % (cid, arm, t))


def pandora(key, at, message, rew, near=3):
    tpl, _ = lib('pandoraBox/object')
    return place('pandoraBox', 'object', tpl, rewardable(key, message, rew), at, near)


def portal(kind, sub, at, near=2):
    """Monoliths: two-way pairs from the library; one-way entrance/exit from the original pictures."""
    if kind == 'monolithTwoWay':
        tpl, opt = lib('monolithTwoWay/' + sub)
        return place(kind, sub, tpl, opt, at, near + 1)
    tpl = h3('AVXmn1b0' if kind == 'monolithOneWayEntrance' else 'AVXmx1b0')
    return place(kind, sub, tpl, {}, at, near + 1)


mir = lambda p: (N - 1 - p[0], N - 1 - p[1])


def dwelling(oid, at, radius=5):
    from handmap import DWELLINGS
    tpl = DWELLINGS[oid]['templates']['default']
    return place('creatureGeneratorCommon', oid, dict(tpl, visitableFrom=tpl.get('visitableFrom', ['---', '+-+', '+++'])), None, at, radius)


def artifact(aid, at, radius=3):
    from handmap import ARTIFACTS
    tpl = {'animation': ARTIFACTS[aid]['graphics']['map'], 'mask': ['VA'], 'visitableFrom': ['+++', '+-+', '+++']}
    return place('artifact', aid, tpl, None, at, radius)


def place(kind, sub, tpl, opt, mid, radius=4):
    """Place an object on the free spot nearest `mid` from which a path reaches a road, and reserve that
    path at once so later objects can't wall it in (corridors are narrow and the landings full)."""
    from handmap import entry_tiles, visit_offset
    spots = sorted(((mid[0] + dx, mid[1] + dy) for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1)),
                   key=lambda p: (abs(p[0] - mid[0]) + abs(p[1] - mid[1]), p))
    ox, oy = visit_offset(tpl)
    for at in spots:
        if not m.inside(*at) or not m.fits(tpl, at[0] - ox, at[1] - oy):
            continue
        cells = [(at[0] - ox + dx, at[1] - oy + dy) for dx, dy, ch in mask_cells(tpl) if ch in 'BA']
        if any(c in m.wall or c in m.water or not m.inside(*c) for c in cells):
            continue
        for x, y in cells:                       # pretend it stands there, then look for its way out
            m.blocked[y][x] = True
        entries = [e for e in entry_tiles(tpl, *at) if m.inside(*e) and not m.blocked[e[1]][e[0]] and e not in m.wall]
        ok = any(m.reserve_path(e) for e in entries)
        for x, y in cells:
            m.blocked[y][x] = False
        if ok:
            return m.add(kind, sub, tpl, at, opt, near=0)
    raise SystemExit('no spot for %s %s near %s' % (kind, sub, mid))


def home_thing(key, mid, radius=6):
    tpl, opt = lib(key)
    return place(key.split('/')[0], key.split('/')[1], tpl, opt, mid, radius)


def thing(key, mid, radius=3):
    return home_thing(key, mid, radius)        # blue's half is red's turned half a circle


def on_arm(arm, t, side=0.0):
    return point(arm, t, side)


def along(make, arm, t, side, *args):
    """make(at, *args) at about t on the arm, sliding along the road until it fits."""
    for dt in (0, 0.08, -0.08, 0.16, -0.16, 0.24, -0.24):
        for sd in (side, -side):
            try:
                return make(on_arm(arm, t + dt, sd), *args)
            except SystemExit:
                continue
    raise SystemExit('nothing fits near t=%.2f on the %s road for %s' % (t, arm, make.__name__))


# ------------------------------------------------------------------ towns and heroes

HOME = ['villageHall', 'townHall', 'tavern', 'fort', 'marketplace', 'mageGuild1', 'dwellingLvl1', 'dwellingLvl2', 'dwellingLvl3']
# the landings differ in shape (a town faces down on both), so each is laid out by hand: town, then
# the road from its gate to the spiral, then the mines on the nearest free spots around the middle
LANDINGS = {'red': dict(town=(5, 6), road=[(5, 7), (5, 8), (4, 8), (4, 10), (3, 10)], hero=(6, 8), middle=(7, 2)),
            'blue': dict(town=(31, 33), road=[(31, 34), (28, 34), (28, 28), (31, 28), (31, 25), (32, 25)], hero=(27, 32),
                         middle=(31, 29))}
for arm, l in LANDINGS.items():
    m.set_road(road_line(l['road']))
leaf = m.town('konohagakure', LANDINGS['red']['town'], 'red', HOME, [('academyStudent', 20), ('genin', 10)],
              name=T.id('town.leafLanding.name', 'Leaf Landing', 'Причал Листа'))
sand = m.town('sunagakure', LANDINGS['blue']['town'], 'blue', HOME, [('sunaGenin', 20), ('sunaChunin', 10)],
              name=T.id('town.sandLanding.name', 'Sand Landing', 'Причал Песка'))
temple = m.town('kirigakure', (17, 15), 'teal', ['villageHall', 'townHall', 'tavern', 'fort', 'citadel', 'mageGuild1', 'mageGuild2',
                                                'dwellingLvl1', 'dwellingLvl2', 'dwellingLvl3', 'dwellingLvl4', 'dwellingLvl5',
                                                'dwellingUpLvl1', 'dwellingUpLvl2'],
                [('bloodyMistGraduate', 30), ('trackerHunterNin', 16), ('hozukiHydrifier', 10), ('greatShark', 6)],
                name=T.id('town.uzushioTemple.name', 'Uzushio Temple', 'Храм Узусио'))
naruto = m.hero('narutoUzumaki', 'red', LANDINGS['red']['hero'], [('genin', 24), ('ninjaHound', 10), ('hyugaGuard', 5)])
gaara = m.hero('gaara', 'blue', LANDINGS['blue']['hero'], [('sunaGenin', 26), ('woodenPuppet', 10), ('windKunoichi', 5)])
yagura = m.hero('yagura', 'teal', (21, 15), [('mistGenin', 18), ('hunterNin', 9), ('hozukiBrawler', 6), ('summonedShark', 3),
                                             ('yukiClanAdept', 2)], experience=2500)

# ------------------------------------------------------------------ the arms (blue mirrors red, so both are equal)

TREASURE_TEXT = {
    'hiramekarei': ('Kiri swordsmen guard a blade they looted from Uzushio long ago: Hiramekarei, the twin sword of the '
                    'Seven. Gaara\'s road is sealed by Kiri chakra, and only a Kiri blade can cut it.',
                    'Мечники Кири охраняют клинок, давным-давно вывезенный из Узусио: Хирамекарей, парный меч Семи. '
                    'Дорогу Гаары запечатала чакра Кири, и разрезать её может только клинок Кири.'),
    'scrollOfSeals': ('Kiri swordsmen guard the Scroll of Seals of the Uzumaki clan, taken when Uzushio fell. The seal on '
                      'Naruto\'s road is an Uzumaki seal, and only this scroll can undo it.',
                      'Мечники Кири охраняют Свиток печатей клана Узумаки, захваченный при падении Узусио. На дороге '
                      'Наруто стоит печать Узумаки, и снять её может только этот свиток.'),
}
ARMCFG = {
    'red': dict(partner='blue', guard_color='green', tent_color='purple', mine='crystalCavern',
                treasure='hiramekarei', needs='scrollOfSeals', prize='flyingThunderGodKunai', lair='catHideout'),
    'blue': dict(partner='red', guard_color='purple', tent_color='green', mine='sulfurDune',
                 treasure='scrollOfSeals', needs='hiramekarei', prize='temarisGiantFan', lair='zetsuTree'),
}
G1, G2 = 4.85, 2.4                         # the two seal gates on each road
gates1, gates2 = {}, {}

# the seals first: their walls go down before any object reserves a path across them
for arm, c in ARMCFG.items():
    g1 = road_tile(arm, G1)
    gates1[arm] = border_guard(c['guard_color'], g1)
    choke(arm, G1, g1, half=0.12)
    g2 = road_tile(arm, G2)
    gates2[arm] = (g2, c['needs'])
    choke(arm, G2, g2, half=0.12)

for arm, c in ARMCFG.items():
    # home: the economy, on the free spots nearest the landing's middle
    mid = LANDINGS[arm]['middle']
    for key in ('mine/sawmill', 'mine/orePit', 'mine/goldMine', 'mine/' + c['mine'], 'resource/wood', 'resource/ore',
                'treasureChest/treasureChest'):
        home_thing(key, mid)
    # A: the outer road
    thing('treasureChest/treasureChest', on_arm(arm, 6.35, 1.2))
    thing('resource/gold', on_arm(arm, 6.15, -1.2))
    keymaster(c['tent_color'], on_arm(arm, 5.95, 1.2))            # the partner's key
    checkpoint(arm, 5.7, 'trackerHunterNin', 18)
    portal('monolithTwoWay', 'monolith1', on_arm(arm, 5.4, 1.2))   # window A: the two outer roads
    thing('learningStone/learningStone', on_arm(arm, 5.2, -1.2))
    along(lambda at: dwelling(c['lair'], at), arm, 5.05, 1.0)
    thing('campfire/campfire', on_arm(arm, 4.95, -1.2))
    # B: the middle road (Kiri raids it through the temple's one-way monolith)
    portal('monolithOneWayExit', 'monolith1', on_arm(arm, 4.62, 1.2))
    checkpoint(arm, 4.35, 'stoneNinja', 21)
    thing('treasureChest/treasureChest', on_arm(arm, 4.12, -1.2))
    along(lambda at: dwelling('soundVillageOutpost', at), arm, 3.98, 1.0)
    portal('monolithTwoWay', 'monolith2', on_arm(arm, 3.78, 1.2))   # window B: the two middle roads
    thing('magicWell/magicWell', on_arm(arm, 3.64, -1.2))
    checkpoint(arm, 3.45, 'cloudNinja', 14)
    for res, t, side in (('mercury', 3.28, 1.2), ('sulfur', 3.2, -1.2), ('crystal', 3.12, 1.2), ('gems', 3.05, -1.2)):
        thing('resource/' + res, on_arm(arm, t, side))
    checkpoint(arm, 2.92, 'mistSwordsman', 9, 'monster.treasure.%s.message' % arm, TREASURE_TEXT[c['treasure']],
               carries=c['treasure'])
    thing('treasureChest/treasureChest', on_arm(arm, 2.66, 1.2))
    # C: the inner road, Kiri's ground
    checkpoint(arm, 1.98, 'waterDragon', 4)
    artifact(c['prize'], on_arm(arm, 1.85, 1.0))
    pandora('pandora.%s' % arm, on_arm(arm, 1.5, -1.0), ('The Uzumaki sealing masks still hold the chakra of the clan. It flows into you.',
            'Маски печатей Узумаки всё ещё хранят чакру клана. Она вливается в вас.'), reward(exp=3000))
    thing('shrineOfMagicLevel2/shrineOfMagicLevel2', on_arm(arm, 1.1, 1.0))

# the second seals: each wants the treasure from the partner's road
gate('gate.uzumaki', gates2['red'][0],
     (('An Uzumaki seal bars the road: a wall of red script that burns at a touch. It was written with the Scroll of Seals, '
       'and only that scroll can undo it. The scroll lies on Gaara\'s road.',
       'Дорогу перекрывает печать Узумаки: стена красных письмен, обжигающая при прикосновении. Её написали Свитком печатей, '
       'и снять её может только этот свиток. Свиток лежит на дороге Гаары.'),
      ('The Uzumaki seal still burns. Bring the Scroll of Seals from Gaara\'s road: your heroes can meet through the stone '
       'circles and trade.',
       'Печать Узумаки всё ещё горит. Принесите Свиток печатей с дороги Гаары: ваши герои могут встретиться через каменные '
       'круги и обменяться.'),
      ('Naruto unrolls the Scroll of Seals. The red script reads itself backwards and fades. The scroll crumbles to dust.',
       'Наруто разворачивает Свиток печатей. Красные письмена читаются задом наперёд и гаснут. Свиток рассыпается в пыль.')),
     mission={'artifacts': [mod('scrollOfSeals')]})
gate('gate.mist', gates2['blue'][0],
     (('A seal of Kiri water chakra bars the road, a wall of mist that closes again behind every blow. Only a Kiri blade '
       'can cut it: Hiramekarei, which lies on Naruto\'s road.',
       'Дорогу перекрывает печать водной чакры Кири, стена тумана, которая смыкается после каждого удара. Разрезать её '
       'может только клинок Кири: Хирамекарей, что лежит на дороге Наруто.'),
      ('The mist seal still holds. Bring Hiramekarei from Naruto\'s road: your heroes can meet through the stone circles '
       'and trade.',
       'Туманная печать всё ещё держится. Принесите Хирамекарей с дороги Наруто: ваши герои могут встретиться через '
       'каменные круги и обменяться.'),
      ('Hiramekarei splits into its twin blades and cuts the mist in two. The seal is gone, and so is the sword, back into the '
       'mist it came from.',
       'Хирамекарей распадается на два клинка и рассекает туман надвое. Печати больше нет, а меч уходит обратно в туман, '
       'из которого пришёл.')),
     mission={'artifacts': [mod('hiramekarei')]})

# ------------------------------------------------------------------ the temple plaza and Isobu's shrine

# Kiri's raids: the one-way portal to the middle of either road stands in a niche east of the shrine; the
# masked man's seal in its doorway holds until the day-10 event removes it (the AI raided from day 2 in the
# first play test, before the warning)
RAID_PORTAL, RAID_DOOR = (21, 19), (21, 18)
m.wall |= {(22, 18), (22, 19), (22, 20), (21, 20)}
raid_portal = portal('monolithOneWayEntrance', 'monolith1', RAID_PORTAL, near=0)
raid_seal = gate('gate.raids', RAID_DOOR,
     (('The masked man\'s stone circle. It is sealed and still gathering chakra; it will wake on day 10.',
       'Каменный круг человека в маске. Он запечатан и ещё набирает чакру; он проснётся на 10-й день.'),
      ('The stone circle is still sealed. It will wake on day 10.', 'Каменный круг всё ещё запечатан. Он проснётся на 10-й день.'),
      ('The stone circle wakes.', 'Каменный круг просыпается.')),                  # never shown: the day-10 event removes it
     mission={'heroes': [mod('narutoUzumaki')], 'colors': ['teal']})      # no one can: Naruto is never teal
gate('gate.sand', SEAL1,
     (('The shrine of the Uzumaki: the masked man\'s seal covers its door. Two locks glow on it, one of sand and one of '
       'Uzumaki script. The sand lock answers only to the chakra of a jinchuriki of the sand: Gaara.',
       'Святилище Узумаки: его дверь покрывает печать человека в маске. На ней светятся два замка, песчаный и из письмен '
       'Узумаки. Песчаный замок отзывается только на чакру джинчурики песка: Гаару.'),
      ('The sand lock waits for Gaara.', 'Песчаный замок ждёт Гаару.'),
      ('Gaara lays his hand on the lock. The sand in it remembers Shukaku and crumbles away.',
       'Гаара кладёт руку на замок. Песок в нём помнит Шукаку и осыпается.')),
     mission={'heroes': [mod('gaara')]})
gate('gate.spiral', SEAL2,
     (('The second lock is Uzumaki script, the clan\'s own seal turned against it. It answers only to Uzumaki blood: Naruto.',
       'Второй замок — письмена Узумаки, собственная печать клана, обращённая против него. Он отзывается только на кровь '
       'Узумаки: Наруто.'),
      ('The Uzumaki lock waits for Naruto.', 'Замок Узумаки ждёт Наруто.'),
      ('The script knows Naruto\'s chakra. The spiral on the door turns once and opens. Below, the Three-Tails roars.',
       'Письмена узнают чакру Наруто. Спираль на двери делает оборот и раскрывается. Внизу ревёт Трёххвостый.')),
     mission={'heroes': [mod('narutoUzumaki')]})
isobu = guard('isobu', 1, (19, 21), 'monster.isobu.message',
              ('Isobu, the Three-Tails, rises in the masked man\'s chains, maddened by the seal, and attacks!',
               'Исобу, Трёххвостый, поднимается в цепях человека в маске, обезумевший от печати, и нападает!'), near=0)
m.artifact('willOfFire', (17, 21), near=0)

# ------------------------------------------------------------------ obstacles and checks

# before any decoration: walls and seals alone must keep the stretches apart (random trees once hid a leak)
def walls_reach(start):
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q in seen or not m.inside(*q) or q in m.wall or q in m.water or q in m.gates:
                    continue
                seen.add(q)
                todo.append(q)
    return seen
for arm, home in (('red', LANDINGS['red']['hero']), ('blue', LANDINGS['blue']['hero'])):
    seen = walls_reach(home)
    other = 'blue' if arm == 'red' else 'red'
    leaks = [p for p, (a, t) in ARM.items() if p in seen and (a == other or t < G1 - 0.15)]
    assert not leaks, '%s landing reaches past its first seal or into the %s road by walls alone: %s' % (arm, other, leaks[:5])

try:
    m.keep_monsters_clickable()
    m.reserve_paths()
    m.dress(density=0.10)
except AssertionError:
    print(picture())
    raise

starts = {'red': m.at[naruto['instanceName']], 'blue': m.at[gaara['instanceName']]}
blockers = {}
for o in m.objects:
    for dx, dy, ch in mask_cells(o['template']):
        if ch in 'BA' and o['type'] != 'event':
            blockers.setdefault((o['x'] + dx, o['y'] + dy), []).append(o['instanceName'])
on_blocked = [(o['instanceName'], at, blockers.get(at)) for at, o, tpl in m.visits
              if blockers.get(at, []) != ([] if o['type'] == 'event' else [o['instanceName']])]
assert not on_blocked, 'objects on a blocked tile: %s' % on_blocked
unreachable = m.unreachable(list(starts.values()))
assert not unreachable, 'cannot be reached: %s' % unreachable
# each stretch opens only through its own guards and gates
for arm, home in starts.items():
    beaten = m.reach(home, False, ignore=m.monsters, gates_open=False)
    for other_arm in ARMS:
        for t, label in ((4.0, 'B'), (1.5, 'C')):
            p = on_arm(other_arm, t)
            assert p not in beaten, '%s reaches %s %s past every monster without opening a seal' % (arm, other_arm, label)
    assert (18, 15) not in beaten and SEAL1 not in beaten
    assert starts['blue' if arm == 'red' else 'red'] not in beaten, 'the two landings are joined by land'
everything = m.reach(starts['red'], False, ignore=m.monsters, gates_open=True)
assert all(p in everything for p in SHRINE - {(19, 21), (17, 21)}), 'the shrine cannot be reached with every seal open'
# Kiri's heroes walk the temple and both inner roads, but no further without the one-way portal
kiri = m.reach(m.at[yagura['instanceName']], False, ignore=m.monsters, gates_open=False)
assert not any(on_arm(a, 3.5) in kiri or starts[a] in kiri for a in ARMS), 'Kiri walks out of the temple past the seals'
for arm, home in starts.items():      # each road's guards, from its own landing (the way its player meets them)
    # a guard on a stretch walked northwards has the top of its picture beyond it: one clickable picture
    # tile (and its own) is enough there; none at all is a fault
    bad = []
    for mo in sorted(m.monsters):
        if ARM.get(mo, ('plaza',))[0] not in (arm, 'plaza'):
            continue
        seen = m.reach(home, False, ignore=m.monsters - {mo}, gates_open=True)
        zone = {(mo[0] + dx, mo[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - {mo}
        # attackable: a click on its own tile walks into its zone from outside (VCMI starts the fight there)
        if not any((z[0] + dx, z[1] + dy) in seen for z in zone if m.inside(*z) and not m.blocked[z[1]][z[0]]
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            bad.append(mo)
    assert not bad, 'guards that cannot be attacked from %s: %s' % (arm, bad)

# ------------------------------------------------------------------ header: story, timed events, victory and loss

say = T.say
header = j(BASE_HEADER)
for k in ('allowedAbilities', 'allowedArtifacts', 'allowedSpells'):
    del header[k]
STORY = ('narutoUzumaki', 'gaara', 'yagura', 'kakashiHatake', 'jiraiya', 'tsunade', 'temari', 'kankuro', 'meiTerumi')
assert all(h in HEROES for h in STORY)
header['allowedHeroes'] = {'anyOf': [mod(h) for h in HEROES if h not in STORY]}
header['name'] = say('header.name', 'Naruto: The Uzumaki Spiral', 'Наруто: Спираль Узумаки')
header['description'] = say('header.description',
    'Co-op for two players (red and blue are allies). The ruins of Uzushiogakure, the whirlpool village of the Uzumaki '
    'clan, lie on an island built as the clan\'s double spiral. Yagura, the Fourth Mizukage, puppet of a masked man, '
    'holds the temple at its heart and is binding Isobu, the Three-Tails, with the clan\'s own seals. Naruto lands on the '
    'north-west shore, Gaara on the south-east. Each spiral road is shut by seals whose keys lie on the other road: work '
    'together. Stone circles join the two roads.\n\n'
    'Win: defeat Isobu in the shrine at the centre. Lose: Naruto or Gaara falls, or day 36 comes.',
    'Кооператив для двух игроков (красный и синий — союзники). Руины Узусиогакуре, Деревни Водоворота клана Узумаки, '
    'лежат на острове, выстроенном двойной спиралью клана. Ягура, Четвёртый Мизукаге, марионетка человека в маске, '
    'держит храм в её сердце и сковывает Исобу, Трёххвостого, собственными печатями клана. Наруто высаживается на '
    'северо-западном берегу, Гаара — на юго-восточном. Каждую спиральную дорогу закрывают печати, ключи от которых '
    'лежат на другой дороге: действуйте вместе. Каменные круги соединяют две дороги.\n\n'
    'Победа: одолеть Исобу в святилище в центре. Поражение: погибнет Наруто или Гаара, или наступит 36-й день.')
header['author'] = say('header.author', 'Naruto Heroes', 'Naruto Heroes')
header['mapVersion'] = say('header.mapVersion', '1.0', '1.0')
header['difficulty'] = 'HARD'
main_town = lambda t: {'generateHero': False, 'l': 0, 'x': t['x'], 'y': t['y']}
header['players'] = {
    'red': {'allowedFactions': {'anyOf': [mod('konohagakure')]}, 'canPlay': 'PlayerOrAI', 'mainTown': main_town(leaf)},
    'blue': {'allowedFactions': {'anyOf': [mod('sunagakure')]}, 'canPlay': 'PlayerOrAI', 'mainTown': main_town(sand)},
    'teal': {'allowedFactions': {'anyOf': [mod('kirigakure')]}, 'canPlay': 'AIOnly', 'mainTown': main_town(temple)},
}
header['teams'] = [['red', 'blue'], ['teal']]


def timed(name, day, text, players=('red', 'blue'), human=True, resources=None):
    """A message (and resources) on the given day (VCMI counts firstOccurrence from 0 = day 1)."""
    e = {'name': name, 'message': say('event.%s.message' % name, *text), 'players': list(players),
         'humanAffected': int(human), 'computerAffected': int(not human), 'firstOccurrence': day - 1,
         'nextOccurrence': 0, 'deletedObjectsInstances': []}
    if resources:
        e['resources'] = resources
    return e


KIRI = ('Kiri\'s hunter-nin gather in the temple.', 'Охотники Кири собираются в храме.')
header['events'] = [
    timed('landing', 1, ('Uzushiogakure. Naruto and Gaara land on opposite shores of the spiral island. Tsunade\'s orders: '
        '"Yagura holds the temple at the centre, and the masked man is chaining the Three-Tails with the Uzumaki seals. In five '
        'weeks Isobu will be his weapon. Each of your roads is sealed, and the keys lie on the other road: help each other. '
        'The stone circles on your roads lead to each other\'s."',
        'Узусиогакуре. Наруто и Гаара высаживаются на противоположных берегах спирального острова. Приказ Цунаде: «Ягура '
        'держит храм в центре, а человек в маске сковывает Трёххвостого печатями Узумаки. Через пять недель Исобу станет его '
        'оружием. Каждую вашу дорогу закрывает печать, а ключи лежат на другой дороге: помогайте друг другу. Каменные круги '
        'на ваших дорогах ведут на дорогу друга.»')),
    timed('keys', 2, ('An old Uzumaki inscription on the shore: "The guardian of each road lets through whoever has visited '
        'the tent of its colour, and once it has let one through, it is gone for all." Naruto\'s road is guarded in green, '
        'and the green tent stands on Gaara\'s road. Gaara\'s road is guarded in purple, and the purple tent stands on '
        'Naruto\'s.',
        'Старая надпись Узумаки на берегу: «Страж каждой дороги пропускает того, кто побывал в шатре его цвета, а пропустив '
        'одного, исчезает для всех.» Дорогу Наруто сторожит зелёный страж, и зелёный шатёр стоит на дороге Гаары. Дорогу '
        'Гаары сторожит фиолетовый, и фиолетовый шатёр стоит на дороге Наруто.')),
    timed('supplies', 8, ('Supply boats arrive from Konoha and Suna.', 'Прибывают лодки с припасами из Конохи и Суны.'),
        resources={'gold': 2000, 'wood': 5, 'ore': 5}),
    dict(timed('raids', 10, ('Scouts report: the masked man\'s stone circle in the temple has woken. From now on Kiri\'s '
        'hunter-nin step into it and come out on your roads, past the first seals. Guard your mines, and your towns once the '
        'green and purple guardians are gone. Keep Naruto and Gaara with strong armies: if either falls, the mission fails.',
        'Разведчики докладывают: каменный круг человека в маске в храме проснулся. Теперь охотники Кири входят в него и '
        'выходят на ваших дорогах, за первыми печатями. Берегите шахты, а когда исчезнут зелёный и фиолетовый стражи, и '
        'города. Держите при Наруто и Гааре сильные армии: если кто-то из них падёт, миссия провалена.')),
        deletedObjectsInstances=[m.objects.index(raid_seal)]),     # the seal on Kiri's portal goes (ids = list order)
    timed('materials', 22, ('Tsunade and the Kazekage\'s council send rare materials.',
        'Цунаде и совет Казекаге присылают редкие материалы.'), resources={'gold': 2500, 'mercury': 4, 'sulfur': 4,
                                                                            'crystal': 4, 'gems': 4}),
    timed('halfway', 22, ('Three weeks are gone. The chains on Isobu tighten: two weeks left.',
        'Прошло три недели. Цепи на Исобу затягиваются: осталось две недели.')),
    timed('lastWeek', 29, ('One week left! On day 36 the binding will be complete.',
        'Осталась одна неделя! На 36-й день сковывание завершится.')),
] + [timed('kiri%d' % d, d, KIRI, players=('teal',), human=False,
           resources={'gold': 3000 + 500 * (d // 7), 'wood': 6, 'ore': 6, 'mercury': 3, 'sulfur': 3, 'crystal': 3, 'gems': 3})
     for d in (8, 15, 22, 29, 36)]
header['rumors'] = [{'name': 'rumor%d' % i, 'text': say('header.rumor.%d.text' % i, en, ru)} for i, (en, ru) in enumerate([
    ('They say Kiri destroyed Uzushiogakure because it feared the Uzumaki seals.',
     'Говорят, Кири уничтожила Узусиогакуре, потому что боялась печатей Узумаки.'),
    ('The Fourth Mizukage has strange eyes these days, the fishermen say: red, with a pattern in them.',
     'Рыбаки говорят, что у Четвёртого Мизукаге теперь странные глаза: красные, с узором.'),
    ('Monkey King Enma once trained in the caves of Uzushio, the old tales say.',
     'Старые сказания говорят, что Царь обезьян Энма когда-то тренировался в пещерах Узусио.'),
])]

human = ['isHuman', {'value': 1}]
pos = lambda o: list(m.at[o['instanceName']]) + [0]
header['triggeredEvents'] = {
    'specialVictory': {
        'condition': ['allOf', human, ['destroy', {'type': 'monster', 'position': pos(isobu)}]],
        'effect': {'type': 'victory', 'messageToSend': say('header.victory.others',
                   'Isobu is free of the masked man\'s chains.', 'Исобу свободен от цепей человека в маске.')},
        'message': say('header.victory.message', 'Isobu falls, and the masked man\'s chains break with him. The Three-Tails '
                       'sinks back into the sea, free. Yagura wakes from his long dream. Uzushiogakure is silent again: '
                       'mission complete!', 'Исобу повержен, и цепи человека в маске рвутся вместе с ним. Трёххвостый, '
                       'свободный, уходит обратно в море. Ягура пробуждается от долгого сна. Узусиогакуре снова молчит: '
                       'миссия выполнена!')},
    'narutoFalls': {
        'condition': ['allOf', human, ['noneOf', ['control', {'type': 'hero', 'position': pos(naruto)}]]],
        'effect': {'type': 'defeat', 'messageToSend': say('header.defeat.naruto.others', 'Naruto has fallen.', 'Наруто пал.')},
        'message': say('header.defeat.naruto.message', 'Naruto has fallen. Without Uzumaki blood the shrine will never open. '
                       'The mission has failed.', 'Наруто пал. Без крови Узумаки святилище никогда не откроется. Миссия '
                       'провалена.')},
    'gaaraFalls': {
        'condition': ['allOf', human, ['noneOf', ['control', {'type': 'hero', 'position': pos(gaara)}]]],
        'effect': {'type': 'defeat', 'messageToSend': say('header.defeat.gaara.others', 'Gaara has fallen.', 'Гаара пал.')},
        'message': say('header.defeat.gaara.message', 'Gaara has fallen. Without him the sand lock will never open. The '
                       'mission has failed.', 'Гаара пал. Без него песчаный замок никогда не откроется. Миссия провалена.')},
    'isobuBound': {
        'condition': ['allOf', human, ['daysPassed', {'value': 35}]],
        'effect': {'type': 'defeat', 'messageToSend': say('header.defeat.time.others', 'Isobu is bound.', 'Исобу скован.')},
        'message': say('header.defeat.time.message', 'Day 36: the binding is complete. Isobu rises from the sea as the masked '
                       'man\'s weapon. The mission has failed.', '36-й день: сковывание завершено. Исобу поднимается из моря '
                       'оружием человека в маске. Миссия провалена.')},
    'standardDefeat': j(BASE_HEADER['triggeredEvents']['standardDefeat']),
}
header['victoryMessage'] = say('header.victoryMessage', 'Defeat Isobu in the shrine', 'Одолеть Исобу в святилище')
header['victoryIconIndex'] = 7
header['defeatMessage'] = say('header.defeatMessage', 'Lose Naruto or Gaara, or let day 36 come',
                              'Гибель Наруто или Гаары, или 36-й день')
header['defeatIconIndex'] = 1

# ------------------------------------------------------------------ write

if args.ascii:
    print(picture())
os.makedirs(os.path.dirname(OUT), exist_ok=True)
m.write(OUT, header, m.terrain(), T.files())
T.register_in_mod(OUT)
print('  %d texts in english.json and russian.json' % len(T.strings['english']))
