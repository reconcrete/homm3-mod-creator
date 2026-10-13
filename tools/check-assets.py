"""Static check of every borrowed graphic the mod references.
For each image / animation name in Content/config (and our sprite JSON files) verify the
file exists in the original game archives or in Content/, and that "FILE.DEF:group:frame"
references point to an existing frame. Prints problems; exit code 1 if any.
python3 tools/check-assets.py [--sheet OUT.png]   (optionally render creature/hero previews)"""
import glob, json, os, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
import lod
from vjson import load

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H3 = os.path.expanduser('~/Library/Application Support/vcmi/Data')
ARCHIVES = ['H3sprite.lod', 'H3ab_spr.lod', 'H3bitmap.lod', 'H3ab_bmp.lod']
IMAGE_KEYS = {'animation', 'map', 'iconLarge', 'iconSmall', 'mapAttackFromLeft', 'mapAttackFromRight',
              'projectile', 'large', 'small', 'specialtyLarge', 'specialtySmall', 'towerIconLarge',
              'towerIconSmall', 'townBackground', 'hallBackground', 'buildingsIcons', 'guildWindow',
              'guildBackground', 'border', 'area', 'campaignBonus', '120px', '130px', 'editorAnimation',
              'defFile', 'battle', 'male', 'female'}

index = {}
for a in ARCHIVES:
    for name, *_ in lod.entries(os.path.join(H3, a)):
        base, ext = os.path.splitext(name.lower())
        index.setdefault(base, []).append((a, name))

def def_frames(archive, name):
    data = lod.read(os.path.join(H3, archive), name)[1]
    n_blocks = struct.unpack_from('<I', data, 12)[0]; pos = 16 + 768; groups = {}
    for _ in range(n_blocks):
        gid, n = struct.unpack_from('<II', data, pos); pos += 16 + 17 * n
        groups[gid] = n
    return groups

problems, checked = [], 0
def check(ref, where):
    global checked
    checked += 1
    parts = ref.split(':')
    name = parts[0]
    base = os.path.splitext(name.lower())[0].split('/')[-1]
    if '/' in name or name.startswith('naruto'):
        # our own file under Content/sprites or Content/data
        hits = glob.glob(os.path.join(ROOT, 'Content', '*', name + '*'), recursive=False) + \
               glob.glob(os.path.join(ROOT, 'Content', '*', name))
        if not hits:
            problems.append('%s: own file %s not found' % (where, name))
        return
    if base not in index:
        problems.append('%s: %s not in the game archives' % (where, name)); return
    if len(parts) == 3:
        archive, real = next(((a, n) for a, n in index[base] if n.lower().endswith('.def')), (None, None))
        if not archive:
            problems.append('%s: %s is not a DEF' % (where, name)); return
        g, f = int(parts[1]), int(parts[2])
        groups = def_frames(archive, real)
        if g not in groups or f >= groups[g]:
            problems.append('%s: %s has no frame %d:%d' % (where, name, g, f))

def walk(node, where):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == 'prefix' and isinstance(v, str):      # puzzle map pieces PREFIX00..PREFIXnn
                check(v + '00', where + '/' + k)
            elif k in IMAGE_KEYS and isinstance(v, str) and v not in ('default',):
                check(v, where + '/' + k)
            elif k in IMAGE_KEYS and isinstance(v, list) and all(isinstance(x, str) for x in v):
                for x in v: check(x, where + '/' + k)
            else:
                walk(v, where + '/' + k)
    elif isinstance(node, list):
        for i, v in enumerate(node): walk(v, '%s[%d]' % (where, i))

for f in sorted(glob.glob(os.path.join(ROOT, 'Content/config/**/*.json'), recursive=True)):
    if '/translations/' in f: continue
    walk(load(f), os.path.relpath(f, ROOT))
for f in sorted(glob.glob(os.path.join(ROOT, 'Content/sprites/**/*.json'), recursive=True)):
    anim = load(f)
    for img in anim.get('images', []):
        if 'defFile' in img:
            check('%s:%d:%d' % (img['defFile'], img.get('defGroup', 0), img.get('defFrame', 0)), os.path.relpath(f, ROOT))
    # our own PNG animations (e.g. creature battle sprites): every listed frame must exist
    groups = set()
    for seq in anim.get('sequences', []):
        groups.add(seq['group'])
        for frame in seq['frames']:
            checked += 1
            if not os.path.exists(os.path.join(ROOT, 'Content/sprites', anim.get('basepath', ''), frame)):
                problems.append('%s: frame %s missing' % (os.path.relpath(f, ROOT), frame))
    if '/creatures/' in f and anim.get('sequences') and not {0, 2, 5} <= groups:
        problems.append('%s: a creature animation needs groups 0 (move), 2 (idle) and 5 (death)' % os.path.relpath(f, ROOT))

for p in problems: print('PROBLEM', p)
print('%d references checked, %d problems' % (checked, len(problems)))
sys.exit(1 if problems else 0)
