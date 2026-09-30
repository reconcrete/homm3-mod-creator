"""Shared helpers for the town generators in tools/towns/.

A town script holds the design data (numbers from the vault "Details" spec, English and
Russian texts side by side) and calls these helpers to write the mod's JSON files:
  Content/config/<faction>/{faction,creatures,heroClasses,heroes}.json
  Content/config/translations/russian-<faction>.json
Borrowed original graphics are looked up from the installed game (core VCMI config and
the H3 .lod archives), so a creature only names the original creature it borrows from.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(__file__))
import lod
from vjson import load

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD = 'naruto-heroes'
VCMI_CONFIG = '/Applications/VCMI.app/Contents/Resources/Data/config'
H3DATA = os.path.expanduser('~/Library/Application Support/vcmi/Data')

# ---------------------------------------------------------------- original game data

_core = None
def core_creatures():
    global _core
    if _core is None:
        _core = {}
        for f in os.listdir(VCMI_CONFIG + '/creatures'):
            _core.update(load(VCMI_CONFIG + '/creatures/' + f))
    return _core

_cranim = None
def cranim(name):
    """Row of CRANIM.TXT (animation timings, missile offsets) for an original creature,
    by its English name as written in the file (e.g. 'Arch Mage')."""
    global _cranim
    if _cranim is None:
        text = lod.read(H3DATA + '/H3bitmap.lod', 'CRANIM.TXT')[1].decode('cp1252')
        _cranim = {}
        for line in text.replace('\r', '').split('\n')[2:]:
            cols = line.split('\t')
            if len(cols) > 24 and cols[-1].strip():
                _cranim[cols[-1].strip()] = cols
    c = _cranim[name]
    num = lambda i: float(c[i]) if c[i].strip() else 0.0
    return {
        'fidget': num(0), 'walk': num(1), 'attack': num(2),
        'offset': {'upperX': int(num(4)), 'upperY': int(num(5)), 'middleX': int(num(6)),
                   'middleY': int(num(7)), 'lowerX': int(num(8)), 'lowerY': int(num(9))},
        'angles': [num(10 + i) for i in range(9)],
        'climax': int(num(23)),
    }

# Adventure-map DEF of each original creature (from H3 Objects.txt, object type 54).
MAP_DEF = {
    'rogue': 'AVWrog.def', 'halfling': 'AVWhalf.def', 'hellHound': 'AVWhoun0.def',
    'cerberus': 'AVWhoux0.def', 'monk': 'AvWMonk.def', 'zealot': 'AVWmonx0.def',
    'woodElf': 'AVWelfw0.def', 'grandElf': 'AVWelfx0.def', 'mage': 'AVWmage0.def',
    'archMage': 'AVWmagx0.def', 'vampire': 'AVWvamp0.def', 'vampireLord': 'AVWvamx0.def',
    'behemoth': 'AVWbhmt0.def', 'ancientBehemoth': 'AVWbhmx0.def',
}

def portrait(index):
    """Large and small portrait resource names of original hero #index."""
    names = [n for n, *_ in lod.entries(H3DATA + '/H3bitmap.lod')]
    def pick(prefix):
        cands = sorted(n for n in names if n.upper().startswith(prefix) and n[3:6] == '%03d' % index)
        main = [n for n in cands if n[6:8].upper() not in ('EL', 'PL', 'SH')] or cands
        return os.path.splitext(main[0])[0]
    return pick('HPL'), pick('HPS')

# ---------------------------------------------------------------- translations

class Texts:
    """Collects Russian strings under their VCMI translation keys."""
    def __init__(self):
        self.ru = {}
    def add(self, key, ru):
        self.ru[key] = ru

def write_json(rel, data):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent='\t', ensure_ascii=False)
        f.write('\n')
    return rel

# ---------------------------------------------------------------- creatures

def creature(t, faction, cid, level, name, ru_name, borrow, cranim_name, stats, upgrades=None,
             abilities=None, shots=None, projectile=None, ray=None, double_wide=None):
    """name / ru_name: (singular, plural). borrow: original creature id whose graphics and
    sounds are reused. stats: dict with cost, hp, speed, attack, defense, dmg (min, max),
    growth, fight, ai, amount (min, max)."""
    core = core_creatures()[borrow]
    anim = cranim(cranim_name)
    icon = core['index'] + 2   # TWCRPORT / CPRSMALL frame of the original creature
    g = {
        'animation': core['graphics']['animation'],
        'map': MAP_DEF[borrow],
        'mapMask': ['VVV', 'VAV'],
        'mapAttackFromLeft': core['graphics']['mapAttackFromLeft'],
        'mapAttackFromRight': core['graphics']['mapAttackFromRight'],
        'iconLarge': 'TWCRPORT.DEF:0:%d' % icon,
        'iconSmall': 'CPRSMALL.DEF:0:%d' % icon,
        'animationTime': {'attack': anim['attack'], 'walk': anim['walk'], 'idle': 10},
        'timeBetweenFidgets': anim['fidget'],
    }
    own = 'naruto/creatures/%s/' % cid       # Anton's portrait, made by tools/convert-art.py
    if os.path.exists(os.path.join(ROOT, 'Content/sprites', own, 'portraitLarge.png')):
        g['iconLarge'], g['iconSmall'] = own + 'portraitLarge.png', own + 'portraitSmall.png'
    if shots:
        m = {'attackClimaxFrame': anim['climax'], 'frameAngles': anim['angles'], 'offset': anim['offset']}
        if ray:
            m['ray'] = ray
        else:
            m['projectile'] = projectile or core['graphics']['missile']['projectile']
        g['missile'] = m
    c = {
        'name': {'singular': name[0], 'plural': name[1]},
        'faction': faction,
        'level': level,
        'cost': stats['cost'],
        'hitPoints': stats['hp'],
        'speed': stats['speed'],
        'attack': stats['attack'],
        'defense': stats['defense'],
        'damage': {'min': stats['dmg'][0], 'max': stats['dmg'][1]},
        'growth': stats['growth'],
        'horde': 0,
        'fightValue': stats['fight'],
        'aiValue': stats['ai'],
        'advMapAmount': {'min': stats['amount'][0], 'max': stats['amount'][1]},
        'abilities': abilities or {},
        'graphics': g,
        'sound': core['sound'],
    }
    if upgrades:
        c['upgrades'] = upgrades
    if shots:
        c['shots'] = shots
    if double_wide if double_wide is not None else core.get('doubleWide'):
        c['doubleWide'] = True
    t.add('creatures.%s.%s.name.singular' % (MOD, cid), ru_name[0])
    t.add('creatures.%s.%s.name.plural' % (MOD, cid), ru_name[1])
    return cid, c

# ---------------------------------------------------------------- hero classes and heroes

def hero_class(t, faction, cid, name, ru_name, affinity, borrow_index, primary, low, high, skills,
               tavern, commander):
    """borrow_index: original class index whose look is reused (0 knight, 1 cleric, ...)."""
    core = load(VCMI_CONFIG + '/heroClasses.json')
    orig = next(v for v in core.values() if v['index'] == borrow_index)
    c = {
        'name': name, 'faction': faction, 'affinity': affinity, 'commander': commander,
        'defaultTavern': 5, 'tavern': tavern,
        'mapObject': orig['mapObject'], 'animation': orig['animation'],
        'primarySkills': dict(zip(('attack', 'defence', 'spellpower', 'knowledge'), primary)),
        'lowLevelChance': dict(zip(('attack', 'defence', 'spellpower', 'knowledge'), low)),
        'highLevelChance': dict(zip(('attack', 'defence', 'spellpower', 'knowledge'), high)),
        'secondarySkills': skills,
    }
    t.add('heroClass.%s.%s.name' % (MOD, cid), ru_name)
    return cid, c

def hero(t, hid, cls, female, name, ru_name, bio, ru_bio, spec, ru_spec, specialty, skills, army,
         portrait_index, spec_icon, spells=None):
    """spec / ru_spec: (name, tooltip, description). specialty: VCMI specialty object.
    skills: [(skill, level)]. army: [(creature, min, max)]. portrait_index / spec_icon:
    original hero whose portrait / specialty icon (UN44, UN32 frame) is borrowed."""
    large, small = portrait(portrait_index)
    own = 'naruto/heroes/%s/' % hid           # Anton's portrait, made by tools/convert-art.py
    if os.path.exists(os.path.join(ROOT, 'Content/sprites', own, 'portraitLarge.png')):
        large, small = own + 'portraitLarge.png', own + 'portraitSmall.png'
    h = {
        'class': cls, 'female': female,
        'images': {'large': large, 'small': small,
                   'specialtyLarge': 'UN44.DEF:0:%d' % spec_icon,
                   'specialtySmall': 'UN32.DEF:0:%d' % spec_icon},
        'army': [{'creature': c, 'min': a, 'max': b} for c, a, b in army],
        'skills': [{'skill': s, 'level': l} for s, l in skills],
        'specialty': specialty,
        'texts': {'name': name, 'biography': bio,
                  'specialty': {'name': spec[0], 'tooltip': spec[1], 'description': spec[2]}},
    }
    if spells:
        h['spellbook'] = spells
    base = 'hero.%s.%s.' % (MOD, hid)
    t.add(base + 'name', ru_name)
    t.add(base + 'biography', ru_bio)
    t.add(base + 'specialty.name', ru_spec[0])
    t.add(base + 'specialty.tooltip', ru_spec[1])
    t.add(base + 'specialty.description', ru_spec[2])
    return hid, h

# ---------------------------------------------------------------- adventure-map dwellings

_objtxt = None
def h3_template(def_name):
    """Template of an original map object from Objects.txt: animation, VCMI mask, terrains."""
    global _objtxt
    if _objtxt is None:
        text = lod.read(H3DATA + '/H3bitmap.lod', 'Objects.txt')[1].decode('cp1252')
        _objtxt = {}
        for line in text.replace('\r', '').split('\n')[1:]:
            c = line.split()
            if len(c) >= 9:
                _objtxt.setdefault(c[0].lower(), c)
    c = _objtxt[def_name.lower()]
    # Objects.txt stores the 6x8 masks starting from the bottom-right tile; reverse them so
    # rows run top to bottom, left to right, anchored at the bottom-right like VCMI masks.
    block, visit = c[1][::-1], c[2][::-1]
    import struct
    for archive in ('H3sprite.lod', 'H3ab_spr.lod'):
        try:
            data = lod.read(H3DATA + '/' + archive, c[0])[1]; break
        except KeyError:
            continue
    w, h = struct.unpack_from('<II', data, 4)
    cols, rows_n = min(8, -(-w // 32)), min(6, -(-h // 32))
    rows = []
    for i in range(6 - rows_n, 6):
        row = ''
        for j in range(8 - cols, 8):
            b, v = block[i * 8 + j] == '0', visit[i * 8 + j] == '1'
            row += 'A' if b and v else 'B' if b else 'V'
        rows.append(row)
    return {'animation': os.path.splitext(c[0])[0], 'mask': rows}

def dwelling_object(t, oid, name, ru_name, creature_id, borrow_def, ambient):
    """A creatureGeneratorCommon map object (external dwelling) for one creature."""
    o = {'name': name, 'creatures': [[creature_id]], 'sounds': {'ambient': [ambient]},
         'templates': {'default': h3_template(borrow_def)}}
    t.add('mapObject.%s.creatureGeneratorCommon.%s.name' % (MOD, oid), ru_name)
    return oid, o
