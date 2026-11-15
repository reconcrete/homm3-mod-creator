#!/bin/sh
# Package the mod for another computer (network play needs identical mods on both):
#   <out>/naruto-heroes.zip      the mod: naruto-heroes/mod.json + Content/ + mods/ (sub-mods), exactly as this
#                                computer loads it (VCMI compares mod checksums); the playable maps
#                                travel inside it (Content/maps)
# Import it on the other computer with the VCMI launcher's "Import files" button.
# Usage: tools/package-mod.sh [out-dir]   (default: ~/Desktop/naruto-heroes-share)
set -e
cd "$(dirname "$0")/.."
OUT=${1:-$HOME/Desktop/naruto-heroes-share}
VERSION=$(python3 -c "import json; print(json.load(open('mod.json'))['version'])")
STAGE=$(mktemp -d)
mkdir "$STAGE/naruto-heroes"
cp mod.json "$STAGE/naruto-heroes/"
cp -R Content mods "$STAGE/naruto-heroes/"
mkdir -p "$OUT"
rm -f "$OUT/naruto-heroes.zip" "$OUT"/*.vmap
(cd "$STAGE" && zip -q -r -X "$OUT/naruto-heroes.zip" naruto-heroes)
rm -rf "$STAGE"
echo "$OUT: naruto-heroes.zip (mod version $VERSION, $(du -h "$OUT/naruto-heroes.zip" | cut -f1), maps inside)"
