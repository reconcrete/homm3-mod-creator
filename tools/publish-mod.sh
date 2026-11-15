#!/bin/sh
# Copy the mod as players install it into the standalone mod repository (github.com/reconcrete/naruto-heroes):
#   mod.json, Content/ (with the three playable maps in Content/maps), mods/ (sub-mods), screenshots/, README.md, LICENSE
# from publish/ here. Then review, commit and push in that repository (branches main and vcmi-1.7; VCMI's mod
# list points at vcmi-1.7). Never copies art/ (Anton's sources stay private).
# Usage: tools/publish-mod.sh [repo-dir]   (default: ../naruto-heroes-mod)
set -e
cd "$(dirname "$0")/.."
DEST=${1:-../naruto-heroes-mod}
[ -d "$DEST/.git" ] || { echo "$DEST is not a git checkout of the mod repository"; exit 1; }
rsync -a --delete Content/ "$DEST/Content/"
rsync -a --delete mods/ "$DEST/mods/"
rsync -a --delete publish/screenshots/ "$DEST/screenshots/"
cp mod.json publish/README.md publish/LICENSE "$DEST/"
echo "copied mod $(python3 -c "import json; print(json.load(open('mod.json'))['version'])") to $DEST:"
(cd "$DEST" && git status --short | head -20)
