# Writes <slug>.js: the Studio setup for one creature (autopilot + export hook + its animation plan).
# Serve the folder with RECEIVER_SCRIPTS=<dir> receiver.py and run it in the tab with fetch + eval.
# Usage: python3 make-setup.py SLUG   (PLAN below lists each creature's presets and saved AI motions)
import json, os, sys
T = os.path.expanduser('~/Projects/naruto-heroes/tools/3d/studio/')
auto = open(T + 'autopilot.js').read()
hook = open(T + 'export-hook.js').read()
BLOCK = {'ai': 'Ninja Blocking'}
JUTSU = {'ai': 'Ninja Jutsu Casting'}
PLAN = {
 'medical-ninja': ['idle', 'walk', 'box_01', 'hit_to_body_01', 'fall', BLOCK],
 'hyuga-guard': ['idle', 'walk', 'box_02', 'hit_to_body_02', 'fall', BLOCK],
 'hunter-nin': ['idle', 'walk', 'slash', 'hit_to_body_01', 'fall', 'pitch_baseball', BLOCK],
 'hozuki-brawler': ['idle', 'walk', 'box_03', 'hit_to_head', 'fall', BLOCK],
 'human-puppet': ['idle', 'walk', 'slash', 'hit_to_side', 'fall', BLOCK],
 'kamaitachi': ['idle', 'walk', 'slash', 'hit_to_body_01', 'fall', BLOCK],
 'mist-genin': ['idle', 'walk', 'slash', 'hit_to_body_01', 'fall', BLOCK],
 'suna-genin': ['idle', 'walk', 'slash', 'hit_to_stomach', 'fall', BLOCK],
 'uchiha-police': ['idle', 'walk', 'slash', 'hit_to_body_01', 'fall', 'cast_a_spell', BLOCK],
 'wind-kunoichi': ['idle', 'walk', 'front_kick_02', 'hit_to_body_02', 'fall', 'cast_a_spell', BLOCK],
 'yuki-clan-adept': ['idle', 'walk', 'front_kick_01', 'hit_to_side', 'fall', 'cast_a_spell', BLOCK],
 'wooden-puppet': ['idle', 'walk', 'chop', 'hit_to_body_01', 'fall', BLOCK],
 'summoned-shark': ['idle', 'walk', 'box_03', 'hit_to_head', 'fall', BLOCK],
 'sand-colossus': ['idle', 'walk', 'chop', 'hit_to_body_02', 'fall', BLOCK],
 'toad-warrior': ['idle', 'jump', 'slash', 'hit_to_body_01', 'fall', BLOCK],
 # batch 3 (2026-10-21)
 'academy-student': ['idle', 'walk', 'box_02', 'hit_to_body_01', 'fall', BLOCK],
 'hyuga-main-branch': ['idle', 'walk', 'box_01', 'hit_to_body_02', 'fall', BLOCK],
 'sharingan-master': ['idle', 'walk', 'slash', 'hit_to_body_01', 'fall', JUTSU, BLOCK],
 'suna-chunin': ['idle', 'walk', 'slash', 'hit_to_stomach', 'fall', BLOCK],
 'battle-puppet': ['idle', 'walk', 'chop', 'hit_to_body_01', 'fall', BLOCK],
 'bloody-mist-graduate': ['idle', 'walk', 'slash', 'hit_to_side', 'fall', BLOCK],
 'tracker-hunter-nin': ['idle', 'walk', 'slash', 'hit_to_body_02', 'fall', 'pitch_baseball', BLOCK],
 # batch 4 (2026-10-25)
 'senior-medic': ['idle', 'walk', 'box_03', 'hit_to_body_01', 'fall', BLOCK],
 'anbu-captain': ['idle', 'walk', 'slash', 'hit_to_side', 'fall', BLOCK],
 'fan-master': ['idle', 'walk', 'front_kick_02', 'hit_to_body_02', 'fall', JUTSU, BLOCK],
 'kazekage-puppet': ['idle', 'walk', 'chop', 'hit_to_body_01', 'fall', 'pitch_baseball', BLOCK],
 'ice-mirror-master': ['idle', 'walk', 'front_kick_01', 'hit_to_side', 'fall', JUTSU, BLOCK],
 'swordsman-of-the-seven': ['idle', 'walk', 'slash', 'hit_to_body_01', 'fall', BLOCK],
 'great-shark': ['idle', 'walk', 'box_02', 'hit_to_head', 'fall', BLOCK],
}
slug = sys.argv[1]
js = ("const a = document.querySelector('a[href^=\"/workspace/animate\"]'); if (a && !/\\/animate\\//.test(location.pathname)) { a.click(); await new Promise(r => setTimeout(r, 4000)); }\n"
      + auto.strip().rstrip(';') + ";\n" + hook + f"\nwindow.__expName = '{slug}-export.glb';\n"
      + f"window.__ap.start({json.dumps(PLAN[slug])});\n'started {slug} ' + location.pathname")
open(f'{slug}.js', 'w').write(js)
print(len(js))
