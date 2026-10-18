"""Make the showcase map: red owns one fully built town of every faction (ours and the 9
originals) on a small all-grass map, to look at all towns side by side. Blue, an AI with
one town in the far corner, keeps the game from ending on day 1 (with no enemy left the
game is won at once). Start it as red; save on day 1 to keep a save.
Written to the VCMI Maps folder as naruto-showcase.vmap ("Naruto Heroes: all towns").
python3 tools/make-showcase-map.py"""
import json, os, random, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vjson import load, strip
import townkit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORE = '/Applications/VCMI.app/Contents/Resources/Data/config/factions/'
OURS = ['konohagakure', 'sunagakure', 'kirigakure']
ORIGINALS = ['castle', 'rampart', 'tower', 'inferno', 'necropolis', 'dungeon', 'stronghold', 'fortress', 'conflux']
SIZE = 36
OUT = os.path.expanduser('~/Library/Application Support/vcmi/Maps/naruto-showcase.vmap')

base = zipfile.ZipFile(os.path.join(HERE, 'testmaps/base-72x72-4p.vmap'))
header = json.loads(strip(base.read('header.json').decode('utf-8')))
base_objects = json.loads(strip(base.read('objects.json').decode('utf-8')))
spells = next(o for o in base_objects if o.get('type') == 'town')['options']['possibleSpells']

def town_buildings(faction):
    """Every building of the town except the shipyard and what needs it (the map is inland)."""
    if faction in OURS:
        blds = json.load(open(os.path.join(ROOT, 'Content/config', faction, 'faction.json'), encoding='utf-8'))[faction]['town']['buildings']
        scope = 'naruto-heroes'
    else:
        blds = load(CORE + faction + '.json')[faction]['town']['buildings']
        scope = 'core'
    keep = [k for k, v in blds.items() if v is not None and k not in ('shipyard', 'ship')
            and 'shipyard' not in json.dumps(v.get('requires', []))]
    return ['%s:%s' % (scope, k) for k in keep]

def template(faction):
    conf = json.load(open(os.path.join(ROOT, 'Content/config', faction, 'faction.json'), encoding='utf-8')) if faction in OURS \
        else load(CORE + faction + '.json')
    anim = conf[faction]['town']['mapObject']['templates']['castle']['animation']
    t = townkit.h3_template(anim)
    return {'animation': t['animation'], 'editorAnimation': '', 'mask': t['mask'],
            'visitableFrom': ['---', '+-+', '+++']}

def town(n, faction, owner, x, y, built=True):
    return {'instanceName': 'town_%d' % n, 'type': 'town', 'subtype': faction, 'x': x, 'y': y, 'l': 0,
            'options': {'owner': owner, 'possibleSpells': spells, 'events': [],
                        'buildings': {'allOf': town_buildings(faction) if built else ['core:fort']}},
            'template': template(faction)}

# 12 towns in three rows of four (a town is 6x6 tiles; its gate is 2 left of its x, on its y)
objects, factions = [], OURS + ORIGINALS
spots = [(6 + 8 * c, 8 + 9 * r) for r in range(3) for c in range(4)]
for n, (faction, (x, y)) in enumerate(zip(factions, spots)):
    objects.append(town(n, faction, 'red', x, y))
gate = (spots[0][0] - 2, spots[0][1])
objects.append(town(len(objects), 'stronghold', 'blue', SIZE - 2, SIZE - 2, built=False))

random.seed(36)
terrain = [['gr%d_' % random.randint(49, 72) for _ in range(SIZE)] for _ in range(SIZE)]

header['mapLevels'] = {'surface': {'height': SIZE, 'index': 0, 'layer': 'core:surface', 'width': SIZE}}
header['name'] = {'exactStrings': ['Naruto Heroes: all towns'], 'localStrings': None, 'message': [0],
                  'numbers': None, 'stringsTextID': None}
header['description'] = {'exactStrings': ['Every town fully built, side by side: Konohagakure, Sunagakure, Kirigakure and the nine original towns. Red owns them all; open them from the town list on the right.'],
                         'localStrings': None, 'message': [0], 'numbers': None, 'stringsTextID': None}
header['players'] = {
    'red': {'allowedFactions': {'anyOf': ['naruto-heroes:konohagakure']}, 'canPlay': 'PlayerOrAI',
            'mainTown': {'generateHero': True, 'l': 0, 'x': spots[0][0], 'y': spots[0][1]}},
    'blue': {'allowedFactions': {'anyOf': ['core:stronghold']}, 'canPlay': 'AIOnly',
             'mainTown': {'generateHero': True, 'l': 0, 'x': SIZE - 2, 'y': SIZE - 2}},
}
header['teams'] = [['red'], ['blue']]     # one team each (an empty list leaves teams unset)

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('header.json', json.dumps(header, indent='\t', ensure_ascii=False).encode('utf-8'))
    z.writestr('objects.json', json.dumps(objects, indent='\t', ensure_ascii=False).encode('utf-8'))
    z.writestr('surface_terrain.json', json.dumps(terrain).encode('utf-8'))
print(OUT)
for o in objects:
    print('  %-12s %-5s at (%2d, %2d), %d buildings' % (o['subtype'], o['options']['owner'], o['x'], o['y'], len(o['options']['buildings']['allOf'])))
