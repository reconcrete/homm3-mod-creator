"""Make a test map: a copy of a small random map where one player's starting town is a
Naruto Heroes faction. Written to the VCMI Maps folder as naruto-test-<faction>.vmap.
python3 tools/make-testmap.py konohagakure [player=red] [base=tools/testmaps/base-72x72-4p.vmap]"""
import json, os, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
from vjson import strip

faction = sys.argv[1]
player = sys.argv[2] if len(sys.argv) > 2 else 'red'
base = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(__file__), 'testmaps/base-72x72-4p.vmap')
out = os.path.expanduser('~/Library/Application Support/vcmi/Maps/naruto-test-%s.vmap' % faction)

zin = zipfile.ZipFile(base)
files = {n: zin.read(n) for n in zin.namelist()}
header = json.loads(strip(files['header.json'].decode('utf-8')))
objects = json.loads(strip(files['objects.json'].decode('utf-8')))

header['players'][player]['allowedFactions'] = {'anyOf': ['naruto-heroes:' + faction]}
header['name'] = {'exactStrings': ['Naruto test: ' + faction], 'localStrings': None, 'message': [0],
                  'numbers': None, 'stringsTextID': None}  # message code 0 = exactStrings[0]
for o in objects:
    if o.get('type') == 'town' and o['options'].get('owner') == player:
        o['subtype'] = faction
        o['template']['animation'] = 'AVCcasx0'
files['header.json'] = json.dumps(header, indent='\t', ensure_ascii=False).encode('utf-8')
files['objects.json'] = json.dumps(objects, indent='\t', ensure_ascii=False).encode('utf-8')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for n, data in files.items():
        z.writestr(n, data)
print(out)
