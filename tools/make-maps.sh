#!/bin/sh
# Rebuild every test map in the VCMI Maps folder (after changing content or pictures).
set -e
cd "$(dirname "$0")/.."
for f in konohagakure sunagakure kirigakure; do
	python3 tools/make-testmap.py $f
done
python3 tools/make-testmap.py konohagakure --out naruto-test-konoha-town-full --name "Naruto test: Konoha town (full)" --buildings all
python3 tools/make-testmap.py konohagakure --out naruto-test-konoha-town-base --name "Naruto test: Konoha town (base)" --buildings base
python3 tools/make-testmap.py sunagakure --out naruto-test-sunagakure-town-full --name "Naruto test: sunagakure town (full)" --buildings all
python3 tools/make-testmap.py kirigakure --out naruto-test-kirigakure-town-full --name "Naruto test: kirigakure town (full)" --buildings all
python3 tools/make-testmap.py konohagakure --out naruto-test-kurama --name "Naruto test: Kurama" \
	--monster kurama:1:48:61 --garrison genin:80,hyugaMainBranch:25,anbuCaptain:12,gamabunta:4
python3 tools/make-showcase-map.py
python3 tools/make-neutral-testmap.py
python3 tools/make-naruto-vs-sasuke.py
