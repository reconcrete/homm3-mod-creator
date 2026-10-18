# Naruto Heroes — VCMI mod

A VCMI 1.7.5 mod (id `naruto-heroes`) adding three Naruto villages as towns. Built across
many Claude Code sessions; progress and next steps live in the vault build log:
`~/O/Projects/HoMM3-Naruto/Work-In-Progress/Naruto-Heroes-Build-Log.md`. The design
(source of truth) is `~/O/Projects/HoMM3-Naruto/Plans/`. High level is Anton's and locked;
numbers and mechanics are ours, specified first in each area note's "Details" section.

## Layout

- `mod.json` — mod metadata, lists every content file.
- `Content/` — the mod's virtual filesystem root (VCMI mounts `Content/` of a mod).
  - `config/<area>/` — one folder per area (`konohagakure`, `sunagakure`, `kirigakure`,
    `neutral`, `artifacts`), one file per content type: `faction.json`, `creatures.json`,
    `heroClasses.json`, `heroes.json`, `objects.json`, ...
  - `config/translations/russian-<area>.json` — Russian texts (English lives in the
    content JSON itself).
  - `sprites/`, `data/` — our converted images (M7+).
- `art/inbox/` — Anton's generated images (git-ignored); `art/masters/` — full-size
  copies of converted images (git-ignored, too big for git); `tools/` — scripts.
- `python3 tools/convert-art.py` turns inbox images into game assets under
  `Content/sprites/naruto/`: hero portraits `heroes/<heroId>/portraitLarge.png` (58x64)
  and `portraitSmall.png` (48x32); creature portraits `creatures/<creatureId>/...` (58x64
  over the borrowed town's creature background, 32x32 transparent; crops centered on the
  head, hand-set in `CROPS` where that fails). Rerun it after images are regenerated,
  then rerun the town generators: `townkit.hero()` / `creature()` use Anton's portrait
  when it exists, the borrowed original otherwise. Full validation checks every image
  file exists.
- Static battle sprites (first half of M8): for creatures listed in `BATTLE` in
  `convert-art.py` (body height in px, two-hex flag; all built towns listed) it also writes
  `creatures/<creatureId>/battle.json` + `battle/*.png`: 450x400 canvases, feet on y=267,
  centered on x=196 (one hex) or 218 (two hexes), like the original DEFs. Each action
  gets a few frames derived from the one still (hop, lunge, recoil, flinch, topple),
  because VCMI times actions by frame count. `townkit.creature()` uses it when it exists
  and sets `attackClimaxFrame` to 3 (1-based). Add a town's creatures to `BATTLE` when
  the town is built. Adventure-map sprites are still borrowed.
- The converter removes converted assets whose inbox image is gone (withdrawn for a
  redraw), so generators fall back to borrowed art.
- Rendered animation (creatures listed in `RENDERED` in `convert-art.py`, first: Kurama,
  frames from the art session in `art/3d/<name>/work/frames/<action>/NN.png`): one scale
  and one offset for all frames, ground point onto the hex line, written to the same
  `battle.json` layout plus a one-frame adventure-map sprite (`map.json`).
- Neutral creatures and bosses: `tools/towns/neutral.py` -> `Content/config/neutral/` (11
  neutrals, 4 tailed beasts at level 10 excluded from random monsters, 11 lairs with the
  artist's map pictures via `own_dwelling_object`). Test map: `tools/make-neutral-testmap.py`
  ("Naruto test: neutrals and bosses"). Map pictures: `convert-art.py` turns
  `map-dwelling-*.png` into `naruto/map/dwellings/<slug>` (96x96, mask VVV/VBB/VBA).
- Test maps: `tools/make-testmap.py` (see its docstring). `naruto-test-konohagakure` is
  the plain Konoha map; `naruto-test-kurama` adds Kurama at (48, 61), four tiles west and
  two south of the red town gate, and a strong town garrison. The script checks that every
  tile under a placed monster's sprite can be clicked (`--find` lists good spots). Maps
  can't be validated from the command line; Anton's playtest is the check.
- Town screen from Anton's art (M9): `python3 tools/townscreen.py <faction> [--preview DIR]`
  reads `art/inbox/town-<faction>-background.png` + one picture per building, and writes
  `Content/sprites/naruto/<faction>/town/` (800x374 background, each building scaled with
  an `-area` click mask and a gold `-border` outline, 150x70 hall icons, town-list icons,
  `structures.json`) plus `../hallIcons.json`. The layout (spot = center x, ground y,
  width; upgrades share their base's spot; z from the ground line) is the `TOWNS` table in
  that script; tune it with the preview images. The town generator uses `structures.json`
  when it exists, Castle's borrowed screen otherwise. Without `area` a building gets no
  hover text or outline in VCMI. Review maps: `naruto-test-konoha-town-base` / `-full`
  (`make-testmap.py --buildings base|all`).
- Showcase map: `python3 tools/make-showcase-map.py` -> "Naruto Heroes: all towns", red owns
  one fully built town of every faction (ours + the 9 originals) on a fresh 36x36 grass map,
  blue AI in a corner so the game doesn't end on day 1. Add new factions to `OURS`.
- Town hall (`hallSlots`): rows must keep the borrowed background's counts (Castle: 4 / 3 /
  2 / 4 / 3), or the frames painted into the background show as black boxes. Hall labels
  hold about 22 characters; keep Russian names within that ("Ул." for upgrades).
- Copy `~/Library/Logs/vcmi/VCMI_Client_log.txt` before running any check after Anton has
  played: the next client start overwrites it.
- The installed mod is a symlink: `~/Library/Application Support/vcmi/Mods/naruto-heroes`
  → this folder (VCMI follows it). Edits are live; no install step.

## Generated content (don't hand-edit the JSON)

Towns: `konohagakure`, `sunagakure`, `kirigakure` (all built; Suna and Kiri use the shared
helpers in `townkit.py`: `hall_chain`, `fort_chain`, `guild_chain`, `dwelling_pair`,
`faction_texts`, `register`, `town_screen`, `dwelling_object_like`; Konoha keeps its own
inline copies). Borrowed looks: Konoha = Castle; Suna = Stronghold (map, siege, music,
creature backgrounds) + Tower's mage-guild window + Castle's hall layout; Kiri = Fortress +
Dungeon's mage-guild window. A borrowed original dwelling must fit a 2x2 random-dwelling
footprint (the Water Conflux doesn't).

Each town's JSON is generated from a data script: `tools/towns/<faction>.py` (numbers from
the vault Details spec, English and Russian side by side) using helpers in
`tools/townkit.py`. Edit the script, run `python3 tools/towns/<faction>.py`, then verify.
The script writes `Content/config/<faction>/*.json`, `Content/config/translations/
russian-<faction>.json` and registers the files in `mod.json`. Borrowed graphics are
looked up from the installed game (core VCMI config, CRANIM.TXT and Objects.txt inside
the H3 .lod archives), so a creature only names the original creature it borrows.

Helpers: `tools/lod.py` (read .lod archives), `tools/h3def.py` / `tools/h3pcx.py` (decode
original sprites and pictures, e.g. contact sheets to pick borrowed art), `tools/vjson.py`
(load VCMI's lenient JSON), `tools/make-testmap.py` (copy of a small random map with a
player on one of our factions, written to the VCMI Maps folder).

## Conventions

- Ids are camelCase, English: faction `konohagakure`, creatures `academyStudent`,
  heroes `narutoUzumaki`, classes `shinobi`/`sage`. Never rename an id once committed
  (saves and maps reference them).
- Strict JSON only (no comments, no trailing commas) so python can validate it.
  Tabs for indentation.
- Every visible string: English in the content file, Russian in the translation file.
  Russian names follow the glossary (`~/O/Projects/HoMM3-Naruto/Knowledge/Common/
  Naruto-Heroes-Glossary.md`): the ru.naruto.fandom spelling (Какаши, Саске, Шикамару,
  Джирайя, Хьюга, Учиха).
- Translation keys: get the full list with
  `vcmiserver --translate-mod naruto-heroes` (see tools/export-translation-keys.sh).
- Borrowed graphics until Anton's art exists: reference original DEF names (e.g.
  `CPKMAN.DEF`); single frames as `FILE.DEF:group:frame` (VCMI supports this for any
  image field; creature portraits are `TWCRPORT.DEF` / `CPRSMALL.DEF` frame = core
  index + 2, hero specialty icons `UN44.DEF` / `UN32.DEF` frame = original hero index).
  Replace them in M7–M9 without changing ids.
- Adventure-map dwellings are required for every town creature line (random dwellings
  on maps fail with "failed to find dwelling for <town> of level N" otherwise).
- Balance yardstick: the original game's numbers (H3 CRTRAITS / HCTRAITS values).

## Verify (every change)

- `tools/check.sh` — strict JSON parse + `vcmiserver --dummy-run` (loads all content
  with validation level from settings.json, currently `full`) + scan of
  `~/Library/Logs/vcmi/VCMI_Server_log.txt`. Must print `OK`.
- `tools/client-check.sh` — starts the real client, waits for the main menu, quits,
  scans `VCMI_Client_log.txt`. Run before each commit.
- `python3 tools/check-assets.py` — every borrowed image/animation reference exists in the
  game archives, including DEF frames. Must print `0 problems`.
- `tools/check-translations.sh` — our Russian keys vs the keys VCMI exports for the mod
  (export made with our translations switched off). Must show no MISSING/UNKNOWN.
- In-game checks need Anton: `vcmiclient --testmap` crashes in VCMI 1.7.5 (it builds a
  human interface for player "invalid"), and `--headless` crashes on connect.
- **Never drive the GUI** (keystrokes via osascript, screenshots): Anton works on this
  Mac at the same time, keystrokes can land in his terminal, screenshots capture his
  screen. Ask him for a playtest instead.

## Rules

- Don't touch other mods. Back up VCMI config files before editing
  (backups in `~/Library/Application Support/vcmi/config-backups/`).
- Vault (`~/O`): notes only, no code or images, dash-separated file names, never git there.
- Commit in this repo at the end of each milestone. Other sessions (e.g. the art session
  with `tools/generate-art.py`, `art/reference/`, `art/logs*`) may work in this repo at
  the same time: commit only your own paths, never `git add -A`. Re-read the vault build
  log right before editing it.
