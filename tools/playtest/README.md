# Play tests on a Linux test machine

The real VCMI client runs on a virtual screen (Xvfb) on a Linux machine, so Claude can play the mod
like a player: it clicks and types with xdotool and takes lossless screenshots with ffmpeg. None of
this touches the screen or keyboard of the Mac where Anton works. A view-only browser page
(noVNC) shows the game live.

## Commands (from the repo root on the Mac)

```
tools/playtest/play game start [WxH]     virtual screen (default 1920x1080) + viewer + game
tools/playtest/play game stop|restart|status|log [N]
tools/playtest/play shot [NAME]           screenshot -> art/playtest/NAME.png (git-ignored), prints the path
tools/playtest/play input click X Y       then waits PLAYTEST_WAIT seconds (0.8) and takes a shot
      input rclick X Y | dclick X Y | move X Y | drag X1 Y1 X2 Y2 | key Return | type TEXT
      input rhold X Y MS                  right button held (VCMI's info popup), shot taken while held
tools/playtest/play cheat CODE...         typed into the chat; console commands start with a slash
tools/playtest/play hover "X Y"...        status-bar text under each point, stacked in one image
tools/playtest/play burst N [SEC] [ACTION ARGS]   optional input, then N shots as one contact sheet
tools/playtest/play errors                ERROR/WARN lines of the client log, counted
tools/playtest/play rec start [NAME] | rec stop   H.264 video (about 1 MB/s) + a contact sheet
tools/playtest/play sync                  copy the mod (mod.json + Content), the Maps folder and these scripts
```

Coordinates are pixels of the virtual screen (1920x1080 by default). After `sync`, restart the game
(`play game restart`), because VCMI loads mods only at start.

The host comes from `playtest_ssh` in the git-ignored `tools/pipeline/local.json`, and the viewer
address from `playtest_view` there.

## On the test machine (`~/Projects/vcmi/`)

- `src/`: VCMI source at the same tag as the client on the Mac (1.7.5). `build/` and `install/` hold
  the build: `cmake -S src -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DENABLE_LAUNCHER=OFF
  -DENABLE_EDITOR=OFF -DENABLE_LOBBY=OFF -DENABLE_TEST=OFF -DFORCE_BUNDLED_FL=ON
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_INSTALL_PREFIX=$PWD/install`, then `ninja -C build
  install`.
- `home/`: everything the game reads or writes. `bin/env.sh` points the XDG folders there:
  - `share/vcmi/`: Data, Mp3, Maps, Mods, Saves (the Heroes 3 files are Anton's copy; never share them)
  - `config/vcmi/`: settings.json, modSettings.json (copied from the Mac: same active mods)
  - `cache/vcmi/`: logs
- `bin/`: the scripts in `server/` (`play sync` copies them).
- `shots/`: screenshots and videos.
- systemd --user units (from `server/units/`, not enabled at boot): `vcmi-display`, `vcmi-view` and
  `vcmi-client`.
- `server/settings.json`: the start settings: 1920x1080, interface at 150%, no intro, sound off,
  player name Claude. It is copied only when no settings file exists yet.

## Playing well

- **Moving:** click a tile once to show the path and a second time to walk.
- **Info popups:** VCMI shows them while the right button is held, so use `input rhold`.
- **Taking shots:** wait before shooting after anything that animates (battles, map scrolling), with
  `PLAYTEST_WAIT=2`.
- **Cheat codes** (`play cheat CODE`; the full list is in VCMI's `docs/players/Cheat_Codes.md`). Use them to reach the scene you are testing:
  - `vcmieagles`: reveal the map
  - `vcminahar`: unlimited movement
  - `vcmiteleport X Y`: move the hero to a tile
  - `vcmilevel N`: gain N levels
  - `vcmiformenos`: resources
  - `vcmibuild`: build everything in the selected town
  - `vcmiarmy <creatureId> N`: give creatures
  - `/set showVisitable on`, `/set showBlocked on`: tile overlays (blocked tiles red, visitable
    tiles outlined yellow). Console commands need the slash, or the text just goes to the chat.
  - F6 toggles the tile grid.
- **Screenshots for posts:** close the extra panels, hide the cursor (the shots never include it),
  start the game at a larger size (`play game start 2560x1440` or `3840x2160`) and raise `scaling`
  in settings.json to match.
- **Mouse:** park it over the right panel (about 1780, 720) before a shot. At the screen edge it
  scrolls the map.
- **Battle settings:** the test machine has the battle hover highlight, movement shadow and cursor
  shadow switched off (`battle` in `home/config/vcmi/settings.json`) for clean screenshots. Switch
  them on to judge how a battle plays.

## A play-test brief (for a subagent)

Give it a time box (about 45 minutes) as well as a screenshot budget (about 120): the first long run
went on for 1.5 hours after the story was done. Ask for:
- findings, most important first, each with a screenshot path and a suggested fix
- what worked
- social-media shots, named `social-*`
- notes on the tools

Have it check each suspected engine-level problem with a quick experiment before reporting it. For
example, a marker picture on the test machine only: the monster offset of 2026-11-14 turned out to
be our `mapMask`, not the art.
