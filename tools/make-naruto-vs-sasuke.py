"""Two-player map "Naruto vs Sasuke: Valley of the End" (36x36, hot seat or vs AI).
python3 tools/make-naruto-vs-sasuke.py [--seed N]  -> Maps/naruto-vs-sasuke.vmap

Mirror-symmetric left/right, so both sides are equal:
  Naruto (red)  top left, Konohagakure     | Sasuke (blue) top right, Konohagakure
  neutral Sunagakure below Naruto          | neutral Kirigakure below Sasuke
  the Valley of the End in the middle: Kurama and Gyuki guard the best artifacts.
Walls of obstacles separate the five areas; each passage is guarded. Everything else (mines,
neutral lairs, the villages' map dwellings, artifacts, chests) is spread over the areas, the
Kage set parts in the matching places (Hokage: one part per home and one in the valley).
Built with tools/handmap.py (object entries and terrain codes from VCMI's own random maps); the
script checks that every object can be reached and that the walls only open at the guarded passages."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handmap import HandMap, BASE_HEADER, MAPS, road_line, text

N = 36
OUT = os.path.join(MAPS, 'naruto-vs-sasuke.vmap')
ap = argparse.ArgumentParser()
ap.add_argument('--seed', type=int, default=7)
args = ap.parse_args()
m = HandMap(N, args.seed)
wall, reserved = m.wall, m.reserved
town, hero, monster, artifact, dwelling, thing = m.town, m.hero, m.monster, m.artifact, m.dwelling, m.thing

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

for line in ([(6, 7), (6, 9), (17, 9)],                 # Naruto's gate -> the top passage to Sasuke
             [(6, 9), (10, 9), (10, 31), (6, 31)],       # Naruto -> Sunagakure's gate
             [(10, 16), (14, 16)],                       # -> the valley (west opening)
             [(6, 31), (6, 33), (17, 33)],               # Sunagakure -> the bottom passage to Kirigakure
             [(10, 25), (15, 25), (15, 21)]):            # Sunagakure -> the valley (south opening)
    m.set_road([t for p in road_line(line) for t in (p, MIRROR(p))])
PASSAGES = {'top': (17, 9), 'left': (10, 17), 'valleyWest': (13, 16), 'valleySouth': (15, 22), 'bottom': (17, 33)}

# ------------------------------------------------------------------ towns and heroes

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

m.reserve_paths()

# ------------------------------------------------------------------ obstacles: close the walls, then dress the land

m.dress()

# ------------------------------------------------------------------ checks

red_hero, blue_hero = (6, 8), MIRROR((6, 8))
unreachable = m.unreachable([red_hero, blue_hero])
assert not unreachable, 'cannot be reached: %s' % unreachable
home = m.reach(red_hero, False)
leaks = [name for name, t in (('Sasuke', blue_hero), ('Suna gate', (6, 31)), ('Kiri gate', MIRROR((6, 31))), ('valley', (17, 15))) if t in home]
assert not leaks, "Naruto's home is open to %s without a fight" % leaks

terrain = m.terrain()

# ------------------------------------------------------------------ write

header = json.loads(json.dumps(BASE_HEADER))
header['name'] = text('Naruto vs Sasuke')   # the scenario header shows about 27 characters
header['description'] = text(
    'Naruto and Sasuke start in two villages of the Leaf. Below them the neutral Sunagakure and Kirigakure wait to be '
    'taken, each with its Kage set and its tailed beast; between them lies the Valley of the End, where Kurama and Gyuki '
    'guard the Rinnegan, Kusanagi and the First Hokage\'s Necklace. Defeat the other to win.\n\n'
    'Наруто и Саске начинают в двух деревнях Листа. Под ними ждут нейтральные Суна и Кири, у каждой свой сет Каге и свой '
    'хвостатый зверь; между ними Долина Завершения, где Курама и Гьюки охраняют Риннеган, Кусанаги и Ожерелье Первого '
    'Хокаге. Победите соперника.')
header['players'] = {
    'red': {'allowedFactions': {'anyOf': ['naruto-heroes:konohagakure']}, 'canPlay': 'PlayerOrAI',
            'mainTown': {'generateHero': False, 'l': 0, 'x': m.objects[0]['x'], 'y': m.objects[0]['y']}},
    'blue': {'allowedFactions': {'anyOf': ['naruto-heroes:konohagakure']}, 'canPlay': 'PlayerOrAI',
             'mainTown': {'generateHero': False, 'l': 0, 'x': m.objects[1]['x'], 'y': m.objects[1]['y']}},
}
header['teams'] = [['red'], ['blue']]
header['mapVersion'] = text('1.0')
header['author'] = text('Naruto Heroes')
m.write(OUT, header, terrain)
