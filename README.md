# homm3-mod-creator

Tools for building Heroes of Might and Magic III mods for [VCMI](https://vcmi.eu) with the
help of an LLM coding agent (Claude Code), and the first mod made with them: **Naruto Heroes**.

## Naruto Heroes (the mod in this repo)

A VCMI 1.7.5 mod that adds three Naruto villages as playable towns: Konohagakure,
Sunagakure and Kirigakure (14 creatures, 2 hero classes and their heroes each), 11 neutral
creatures with map lairs, the tailed beasts Shukaku, Isobu, Gyuki and Kurama as bosses, and
43 artifacts including the three Kage sets. English and Russian.

- `mod.json`, `Content/`: the mod as VCMI loads it.
- `tools/make-naruto-vs-sasuke.py` builds the two-player map "Naruto vs Sasuke: Valley of
  the End" into VCMI's Maps folder.
- `tools/package-mod.sh` writes an installable zip of the mod and that map.

Install: copy (or symlink) this folder into VCMI's `Mods/` folder as `naruto-heroes`, then
enable it in the launcher. It needs the original Heroes III data that VCMI uses; the mod
borrows some original graphics and sounds from it and ships none of them.

A fan-made, non-commercial project, not affiliated with the owners of Naruto or Heroes of
Might and Magic.

## The tools

All content is generated from Python data scripts; the JSON in `Content/config/` is never
edited by hand.

- `tools/towns/<area>.py` + `tools/townkit.py`: towns, creatures, heroes, neutrals and
  artifacts from one data script per area, English and Russian side by side.
- `tools/convert-art.py`, `tools/townscreen.py`: turn generated images into game assets
  (portraits, battle and map sprites, projectiles, town screens, map objects).
- `tools/3d/`: Blender scripts that rig, animate and render 3D models into battle animation.
- `tools/make-*.py`: test maps and play maps.
- `tools/check.sh`, `tools/client-check.sh`, `tools/check-assets.py`,
  `tools/check-translations.sh`: validation against a real VCMI install.
- `tools/lod.py`, `tools/h3def.py`, `tools/h3pcx.py`: read the original game's archives.

`CLAUDE.md` is the working guide the agent follows in this repo.

## Plans

The goal is a framework you can clone, point at a theme and build a mod with an LLM agent:
generic pipeline (image generation, image to 3D, rigging, animation, conversion to VCMI,
checks) separated from the mod-specific data, with self-hosted ComfyUI workflows for the art.
For now this repo is the working copy of the first mod.
