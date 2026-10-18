"""Test map for the neutrals: an open 36x36 grass map where red starts in a fully built
Konohagakure with a strong garrison, next to every neutral creature and tailed beast (one
stack each, spaced so every tile around them can be clicked), every neutral lair and every
artifact (two rows along a free road at y = 16, so a hero can walk along and pick them up).
Blue, an AI in the far corner, keeps the game going. Written to the VCMI Maps folder as
naruto-test-neutrals.vmap ("Naruto test: neutrals and bosses").
python3 tools/make-neutral-testmap.py"""
import json, os, random, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vjson import load, strip
import townkit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORE = '/Applications/VCMI.app/Contents/Resources/Data/config/factions/'
SIZE = 36
OUT = os.path.expanduser('~/Library/Application Support/vcmi/Maps/naruto-test-neutrals.vmap')

base = zipfile.ZipFile(os.path.join(HERE, 'testmaps/base-72x72-4p.vmap'))
header = json.loads(strip(base.read('header.json').decode('utf-8')))
spells = next(o for o in json.loads(strip(base.read('objects.json').decode('utf-8'))) if o.get('type') == 'town')['options']['possibleSpells']
ours = lambda f: json.load(open(os.path.join(ROOT, 'Content/config', f), encoding='utf-8'))
konoha = ours('konohagakure/faction.json')['konohagakure']
neutral = ours('neutral/creatures.json')
lairs = ours('neutral/dwellings.json')['core:creatureGeneratorCommon']['types']
artifacts = ours('artifacts/artifacts.json')

def town_template(conf):
    return townkit.town_map_template(conf['town']['mapObject'])

objects = [
    {'instanceName': 'town_red', 'type': 'town', 'subtype': 'konohagakure', 'x': 6, 'y': 6, 'l': 0,
     'options': {'owner': 'red', 'possibleSpells': spells, 'events': [],
                 'buildings': {'allOf': ['naruto-heroes:' + b for b in konoha['town']['buildings']]},
                 'army': [{'amount': 120, 'type': 'naruto-heroes:genin'}, {'amount': 40, 'type': 'naruto-heroes:hyugaMainBranch'},
                          {'amount': 20, 'type': 'naruto-heroes:sharinganMaster'}, {'amount': 12, 'type': 'naruto-heroes:anbuCaptain'},
                          {'amount': 6, 'type': 'naruto-heroes:gamabunta'}]},
     'template': town_template(konoha)},
    {'instanceName': 'town_blue', 'type': 'town', 'subtype': 'stronghold', 'x': SIZE - 2, 'y': SIZE - 2, 'l': 0,
     'options': {'owner': 'blue', 'possibleSpells': spells, 'events': [], 'buildings': {'allOf': ['core:fort']}},
     'template': town_template(load(CORE + 'stronghold.json')['stronghold'])},
]
# monsters on a grid with 4 tiles between them (guard zones never touch), lairs below
amount = lambda c: 1 if c['level'] >= 10 else {1: 30, 2: 15, 3: 10, 4: 7, 5: 5, 6: 3, 7: 2}[c['level']]
for n, (cid, c) in enumerate(neutral.items()):
    x, y = 10 + 4 * (n % 6), 4 + 4 * (n // 6)
    objects.append({'instanceName': 'monster_%s' % cid, 'type': 'monster', 'subtype': cid, 'x': x, 'y': y, 'l': 0,
                    'options': {'amount': amount(c), 'character': 'savage', 'noGrowing': True, 'neverFlees': True},
                    'template': {'animation': os.path.splitext(c['graphics']['map'])[0], 'editorAnimation': '',
                                 'mask': ['VV', 'VA'], 'visitableFrom': ['+++', '+-+', '+++']}})
for n, (oid, d) in enumerate(lairs.items()):
    x, y = 4 + 5 * (n % 6), 20 + 5 * (n // 6)
    tpl = dict(d['templates']['default'], editorAnimation='')
    objects.append({'instanceName': 'lair_%s' % oid, 'type': 'creatureGeneratorCommon', 'subtype': oid,
                    'x': x, 'y': y, 'l': 0, 'template': tpl})
for n, aid in enumerate(artifacts):
    x, y = 2 + n % 22, 15 + 2 * (n // 22)
    objects.append({'instanceName': 'artifact_%s' % aid, 'type': 'artifact', 'subtype': aid, 'x': x, 'y': y, 'l': 0,
                    'options': {}, 'template': {'animation': artifacts[aid]['graphics']['map'], 'editorAnimation': '',
                                                'mask': ['VA'], 'visitableFrom': ['+++', '+-+', '+++']}})

random.seed(36)
terrain = [['gr%d_' % random.randint(49, 72) for _ in range(SIZE)] for _ in range(SIZE)]
header['mapLevels'] = {'surface': {'height': SIZE, 'index': 0, 'layer': 'core:surface', 'width': SIZE}}
header['name'] = {'exactStrings': ['Naruto test: neutrals and bosses'], 'localStrings': None, 'message': [0],
                  'numbers': None, 'stringsTextID': None}
header['description'] = {'exactStrings': ['Every neutral creature and tailed beast next to a fully built Konoha with a strong garrison, plus every neutral lair and every artifact (the two rows at the middle of the map; the Kage set parts combine). Take the garrison before you fight.'],
                         'localStrings': None, 'message': [0], 'numbers': None, 'stringsTextID': None}
header['players'] = {
    'red': {'allowedFactions': {'anyOf': ['naruto-heroes:konohagakure']}, 'canPlay': 'PlayerOrAI',
            'mainTown': {'generateHero': True, 'l': 0, 'x': 6, 'y': 6}},
    'blue': {'allowedFactions': {'anyOf': ['core:stronghold']}, 'canPlay': 'AIOnly',
             'mainTown': {'generateHero': True, 'l': 0, 'x': SIZE - 2, 'y': SIZE - 2}},
}
header['teams'] = [['red'], ['blue']]
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('header.json', json.dumps(header, indent='\t', ensure_ascii=False).encode('utf-8'))
    z.writestr('objects.json', json.dumps(objects, indent='\t', ensure_ascii=False).encode('utf-8'))
    z.writestr('surface_terrain.json', json.dumps(terrain).encode('utf-8'))
print(OUT, '-', len(neutral), 'monsters,', len(lairs), 'lairs,', len(artifacts), 'artifacts')
