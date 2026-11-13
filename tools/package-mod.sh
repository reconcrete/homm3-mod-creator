#!/bin/sh
# Package the mod for another computer (network play needs identical mods on both):
#   <out>/naruto-heroes.zip      the mod: naruto-heroes/mod.json + Content/, exactly as this
#                                computer loads it (VCMI compares mod checksums)
#   <out>/naruto-vs-sasuke.vmap  the two-player map
#   <out>/naruto-shadow-of-akatsuki.vmap  the single-player story map
# Import them on the other computer with the VCMI launcher's "Import files" button.
# Usage: tools/package-mod.sh [out-dir]   (default: ~/Desktop/naruto-heroes-share)
set -e
cd "$(dirname "$0")/.."
OUT=${1:-$HOME/Desktop/naruto-heroes-share}
VERSION=$(python3 -c "import json; print(json.load(open('mod.json'))['version'])")
STAGE=$(mktemp -d)
mkdir "$STAGE/naruto-heroes"
cp mod.json "$STAGE/naruto-heroes/"
cp -R Content "$STAGE/naruto-heroes/"
mkdir -p "$OUT"
rm -f "$OUT/naruto-heroes.zip"
(cd "$STAGE" && zip -q -r -X "$OUT/naruto-heroes.zip" naruto-heroes)
rm -rf "$STAGE"
for map in naruto-vs-sasuke naruto-shadow-of-akatsuki; do
	cp "$HOME/Library/Application Support/vcmi/Maps/$map.vmap" "$OUT/"
done
echo "$OUT: naruto-heroes.zip (mod version $VERSION, $(du -h "$OUT/naruto-heroes.zip" | cut -f1)), naruto-vs-sasuke.vmap, naruto-shadow-of-akatsuki.vmap"
