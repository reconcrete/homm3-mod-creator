#!/bin/bash
# Validate the mod: strict JSON parse of every file, then a VCMI dummy server run
# (loads all game content with the validation level from settings.json) and a log scan.
# Usage: tools/check.sh            exit code 0 = clean
cd "$(dirname "$0")/.."
LOG="$HOME/Library/Logs/vcmi/VCMI_Server_log.txt"
fail=0
while IFS= read -r f; do
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null || { echo "BAD JSON: $f"; python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>&1 | tail -1; fail=1; }
done < <(find mod.json Content -name '*.json')
[ $fail = 1 ] && exit 1
/Applications/VCMI.app/Contents/MacOS/vcmiserver --dummy-run > /dev/null 2>&1
rc=$?
# Lines from our mod, plus any ERROR anywhere (engine errors often don't name the mod)
# Skip the harmless directory-overlap notices ("both mods add file 'sprites/'") and
# file overlaps between other mods; keep everything else.
hits=$(grep -E "ERROR|WARN" "$LOG" | grep -vE "Potential confict detected .*add file '[^']*/'$" \
  | grep -vE "Potential confict detected between '(hd-remastered|russian-translation|vcmi-extras[^']*)' and '(hd-remastered|russian-translation|vcmi-extras[^']*)'")
naruto=$(grep -iE "naruto" "$LOG" | grep -E "\] (ERROR|WARN) | is invalid|[Ff]ailed |[Uu]nknown " )
if [ -n "$hits$naruto" ] || [ $rc != 0 ]; then
  echo "vcmiserver exit code: $rc"; echo "$hits"; echo "$naruto"; exit 1
fi
grep -q "Loading mod: OK (naruto-heroes)" "$LOG" || { echo "naruto-heroes not loaded"; exit 1; }
echo "OK: naruto-heroes loads with no errors or warnings"
