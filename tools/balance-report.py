"""Balance report: our creatures next to the original towns' creatures of the same tier.
python3 tools/balance-report.py [--all]
Per tier (base / upgraded) it prints the originals' range and each of ours, with a combat
index sqrt(HP x average damage) scaled by attack and defense (H3's 5% per point), per gold
and per week (index x growth), and flags values outside the originals' range by more than 15%.
--all prints every row, not only flagged ones."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vjson import load
import townkit, lod

def crtraits():
    """Original creature stats from CRTRAITS.TXT, by core creature index, in our config's shape."""
    lines = lod.read(townkit.H3DATA + '/H3bitmap.lod', 'CRTRAITS.TXT')[1].decode('cp1252').replace('\r', '').split('\n')[2:]
    rows = [l.split('\t') for l in lines if len(l.split('\t')) >= 21 and l.split('\t')[8].isdigit()]
    res = ('wood', 'mercury', 'ore', 'sulfur', 'crystal', 'gems', 'gold')
    return [{'name': r[0], 'cost': {k: int(v) for k, v in zip(res, r[2:9]) if int(v)}, 'fightValue': int(r[9]),
             'aiValue': int(r[10]), 'growth': int(r[11]), 'hitPoints': int(r[13]), 'speed': int(r[14]),
             'attack': int(r[15]), 'defense': int(r[16]), 'damage': {'min': int(r[17]), 'max': int(r[18])},
             'shots': int(r[19])} for r in rows]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_TOWNS = ['castle', 'rampart', 'tower', 'inferno', 'necropolis', 'dungeon', 'stronghold', 'fortress', 'conflux']
OURS = ['konohagakure', 'sunagakure', 'kirigakure', 'neutral']   # neutrals compare with base creatures; bosses (level 10) are left out

def index(c):
    dmg = (c['damage']['min'] + c['damage']['max']) / 2
    return math.sqrt(c['hitPoints'] * dmg) * (1.05 ** ((c['attack'] + c['defense']) / 2 - 5))

def row(cid, c):
    return {'id': cid, 'hp': c['hitPoints'], 'att': c['attack'], 'def': c['defense'],
            'dmg': (c['damage']['min'] + c['damage']['max']) / 2, 'spd': c['speed'], 'growth': c['growth'],
            'gold': c['cost'].get('gold', 0), 'ai': c['aiValue'], 'fight': c['fightValue'], 'idx': index(c),
            }

core = townkit.core_creatures()
TRAITS = crtraits()
for c in core.values():
    if c.get('index', 999) < len(TRAITS):
        c.update(TRAITS[c['index']])
groups = {}   # (level, upgraded) -> {'core': [rows], 'ours': [rows]}
for cid, c in core.items():
    if c.get('faction') in CORE_TOWNS and not c.get('special') and 1 <= c.get('level', 0) <= 7 and 'hitPoints' in c:
        up = any(cid in (o.get('upgrades') or []) for o in core.values())
        groups.setdefault((c['level'], up), {'core': [], 'ours': []})['core'].append(row(cid, c))
for f in OURS:
    mine = json.load(open(os.path.join(ROOT, 'Content/config', f, 'creatures.json')))
    for cid, c in mine.items():
        if c['level'] > 7:
            continue
        up = any(cid in (o.get('upgrades') or []) for o in mine.values())
        groups.setdefault((c['level'], up), {'core': [], 'ours': []})['ours'].append(dict(row(cid, c), town=f[:4]))

KEYS = ['hp', 'att', 'def', 'dmg', 'spd', 'growth', 'gold', 'ai', 'fight', 'idx']
flags = 0
for key in sorted(groups):
    g = groups[key]
    if not g['ours']:
        continue
    lo = {k: min(r[k] for r in g['core']) for k in KEYS}
    hi = {k: max(r[k] for r in g['core']) for k in KEYS}
    avg = {k: sum(r[k] for r in g['core']) / len(g['core']) for k in KEYS}
    lo['perGold'] = min(r['idx'] / r['gold'] for r in g['core']); hi['perGold'] = max(r['idx'] / r['gold'] for r in g['core'])
    lo['week'] = min(r['idx'] * r['growth'] for r in g['core']); hi['week'] = max(r['idx'] * r['growth'] for r in g['core'])
    print('\nTier %d%s  originals: hp %d-%d  att %d-%d  def %d-%d  dmg %.1f-%.1f  spd %d-%d  gold %d-%d  ai %d-%d  index %.1f-%.1f (avg %.1f)' % (
        key[0], '+' if key[1] else '', lo['hp'], hi['hp'], lo['att'], hi['att'], lo['def'], hi['def'], lo['dmg'], hi['dmg'],
        lo['spd'], hi['spd'], lo['gold'], hi['gold'], lo['ai'], hi['ai'], lo['idx'], hi['idx'], avg['idx']))
    for r in g['ours']:
        r['perGold'] = r['idx'] / r['gold']; r['week'] = r['idx'] * r['growth']
        out = [k for k in KEYS + ['perGold', 'week'] if k not in ('growth',) and (r[k] > hi[k] * 1.15 or r[k] < lo[k] / 1.15)]
        flags += bool(out)
        if out or '--all' in sys.argv:
            print('  %-4s %-20s hp %4d att %2d def %2d dmg %5.1f spd %2d gr %2d gold %4d ai %5d fight %5d index %5.1f /gold %.3f (orig %.3f-%.3f) %s' % (
                r['town'], r['id'], r['hp'], r['att'], r['def'], r['dmg'], r['spd'], r['growth'], r['gold'], r['ai'], r['fight'], r['idx'],
                r['perGold'], lo['perGold'], hi['perGold'], ('OUTSIDE: ' + ', '.join(out)) if out else ''))
print('\n%d of our creatures have values outside the originals\' range (+-15%%)' % flags)
