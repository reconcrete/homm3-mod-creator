#!/bin/bash
# Compare our Russian translation keys with the strings VCMI exports for the mod.
# The export is made with our Russian files switched off, so it lists exactly the keys
# VCMI knows (with their English text). MISSING = not translated, UNKNOWN = wrong key.
cd "$(dirname "$0")/.."
OUT="$HOME/Library/Application Support/vcmi/extracted/translationFull/naruto-heroes"
rm -rf "$OUT"
cp mod.json /tmp/naruto-heroes-mod.json.$$
python3 -c "
import json; m=json.load(open('mod.json')); m['russian'].pop('translations', None)
json.dump(m, open('mod.json','w'), indent='\t', ensure_ascii=False)"
/Applications/VCMI.app/Contents/MacOS/vcmiserver --translate-mod naruto-heroes > /dev/null 2>&1
cp /tmp/naruto-heroes-mod.json.$$ mod.json && rm /tmp/naruto-heroes-mod.json.$$
python3 - "$OUT" <<'PY'
import json, glob, sys
sys.path.insert(0, 'tools'); from vjson import load
exp = {}
for f in glob.glob(sys.argv[1] + '/**/*.json', recursive=True): exp.update(load(f))
ours = {}
for f in glob.glob('Content/config/translations/russian-*.json'): ours.update(json.load(open(f)))
missing = sorted(k for k in exp if k not in ours)
unknown = sorted(k for k in ours if k not in exp)
print('%d strings, %d translated' % (len(exp), len(exp) - len(missing)))
for k in missing: print('MISSING', k, '=', exp[k])
for k in unknown: print('UNKNOWN', k)
sys.exit(1 if missing or unknown else 0)
PY
