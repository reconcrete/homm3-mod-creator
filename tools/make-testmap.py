"""Make a test map: a copy of a small random map where one player's starting town is a
Naruto Heroes faction, written to the VCMI Maps folder.

python3 tools/make-testmap.py konohagakure
    -> Maps/naruto-test-konohagakure.vmap, "Naruto test: konohagakure" in the scenario list
python3 tools/make-testmap.py konohagakure --out naruto-test-kurama --name "Naruto test: Kurama" \
        --monster kurama:1:55:60 --garrison genin:80,hyugaMainBranch:25
    -> the same map plus a monster stack at tile (55, 60) and an army in the town garrison

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

files['header.json'] = json.dumps(header, indent='\t', ensure_ascii=False).encode('utf-8')
files['objects.json'] = json.dumps(objects, indent='\t', ensure_ascii=False).encode('utf-8')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for n, data in files.items():
        z.writestr(n, data)
print(out)
