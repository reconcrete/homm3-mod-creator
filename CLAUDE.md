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
- `art/inbox/` — Anton drops generated images here (git-ignored); `art/masters/` —
  processed full-size originals (committed); `tools/` — scripts.
- The installed mod is a symlink: `~/Library/Application Support/vcmi/Mods/naruto-heroes`
  → this folder (VCMI follows it). Edits are live; no install step.

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
  `CPKMAN.DEF`). Replace them in M7–M9 without changing ids.
- Balance yardstick: the original game's numbers (H3 CRTRAITS / HCTRAITS values).

## Verify (every change)

- `tools/check.sh` — strict JSON parse + `vcmiserver --dummy-run` (loads all content
  with validation level from settings.json, currently `full`) + scan of
  `~/Library/Logs/vcmi/VCMI_Server_log.txt`. Must print `OK`.
- `tools/client-check.sh` — starts the real client, waits for the main menu, quits,
  scans `VCMI_Client_log.txt`. Run before each commit.

## Rules

- Don't touch other mods. Back up VCMI config files before editing
  (backups in `~/Library/Application Support/vcmi/config-backups/`).
- Vault (`~/O`): notes only, no code or images, dash-separated file names, never git there.
- Commit in this repo at the end of each milestone.
