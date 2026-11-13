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
    'behemoth': 'AVWbhmt0.def', 'ancientBehemoth': 'AVWbhmx0.def', 'azureDragon': 'AVWazure.def',
}

_mapdefs = None
def map_def(borrow):
    """Adventure-map DEF of an original creature (Objects.txt, object type 54 = monster)."""
    global _mapdefs
    if borrow in MAP_DEF:
        return MAP_DEF[borrow]
    if _mapdefs is None:
        text = lod.read(H3DATA + '/H3bitmap.lod', 'Objects.txt')[1].decode('cp1252')
        _mapdefs = {}
        for line in text.replace('\r', '').split('\n')[1:]:
            c = line.split()
            if len(c) >= 9 and c[5] == '54':
                _mapdefs.setdefault(int(c[6]), c[0])
    return _mapdefs[core_creatures()[borrow]['index']]

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

# our projectiles (tools/convert-art.py) with the original each falls back to before conversion
PROJECTILES = {'shuriken': 'PHALF.DEF', 'kunai': 'PELFX.DEF', 'fireball': 'CPRGOGX.DEF', 'wind-scythe': 'PORCHX.DEF',
               'senbon': 'PPLIZAX.DEF', 'ice-senbon': 'PMEDUSX.DEF', 'water-bullet': 'PMEDUSX.DEF'}
PROJECTILE_ANGLES = [90, 72, 45, 27, 0, -27, -45, -72, -90]   # one frame each, as in convert-art.py

def missile_offsets(own):
    """Where shots leave our own battle sprite: VCMI starts a projectile at (197, 265) on the
    450x400 canvas (the feet of a one-hex creature) plus these offsets, which the originals
    set at their hands. Ours: near the front edge of the standing frame, at 72 / 60 / 45% of
    the height for shots up / straight / down."""
    from PIL import Image
    anim = json.load(open(os.path.join(ROOT, 'Content/sprites', own, 'battle.json')))
    still = next(s for s in anim['sequences'] if s['group'] == 2)['frames'][0]
    x0, y0, x1, y1 = Image.open(os.path.join(ROOT, 'Content/sprites', anim['basepath'], still)).getchannel('A').getbbox()
    front = lambda share: round(x0 + share * (x1 - x0)) - 197
    up = lambda share: round(y1 - share * (y1 - y0)) - 265
    return {'upperX': front(0.75), 'upperY': up(0.72), 'middleX': front(0.8), 'middleY': up(0.6),
            'lowerX': front(0.75), 'lowerY': up(0.45)}

def creature(t, faction, cid, level, name, ru_name, borrow, cranim_name, stats, upgrades=None,
             abilities=None, shots=None, projectile=None, ray=None, double_wide=None, extra=None,
             idle=10):
    """name / ru_name: (singular, plural). borrow: original creature id whose graphics and
    sounds are reused. stats: dict with cost, hp, speed, attack, defense, dmg (min, max),
    growth, fight, ai, amount (min, max)."""
    core = core_creatures()[borrow]
    anim = cranim(cranim_name)
    icon = core['index'] + 2   # TWCRPORT / CPRSMALL frame of the original creature
    g = {
        'animation': core['graphics']['animation'],
        'map': map_def(borrow),
        'mapMask': ['VVV', 'VAV'],
        'mapAttackFromLeft': core['graphics']['mapAttackFromLeft'],
        'mapAttackFromRight': core['graphics']['mapAttackFromRight'],
        'iconLarge': 'TWCRPORT.DEF:0:%d' % icon,
        'iconSmall': 'CPRSMALL.DEF:0:%d' % icon,
        'animationTime': {'attack': anim['attack'], 'walk': anim['walk'], 'idle': idle},
        'timeBetweenFidgets': anim['fidget'],
    }
    own = 'naruto/creatures/%s/' % cid       # Anton's portrait, made by tools/convert-art.py
    if os.path.exists(os.path.join(ROOT, 'Content/sprites', own, 'portraitLarge.png')):
        g['iconLarge'], g['iconSmall'] = own + 'portraitLarge.png', own + 'portraitSmall.png'
    static = os.path.exists(os.path.join(ROOT, 'Content/sprites', own, 'battle.json'))
    if static:   # battle sprite made by tools/convert-art.py (static from the still, or rendered frames)
        g['animation'] = own + 'battle'
    if os.path.exists(os.path.join(ROOT, 'Content/sprites', own, 'map.json')):
        g['map'] = own + 'map'               # own adventure-map sprite; otherwise the borrowed DEF
    if shots:
        m = {'attackClimaxFrame': anim['climax'], 'frameAngles': anim['angles'], 'offset': anim['offset']}
        if ray:
            m['ray'] = ray
        elif projectile in PROJECTILES and os.path.exists(os.path.join(ROOT, 'Content/sprites/naruto/projectiles', projectile + '.json')):
            m['projectile'] = 'naruto/projectiles/' + projectile    # the artist's, made by tools/convert-art.py
            m['frameAngles'] = PROJECTILE_ANGLES
        else:
            m['projectile'] = PROJECTILES.get(projectile, projectile) or core['graphics']['missile']['projectile']
        if static:
            m['attackClimaxFrame'] = 3     # counted from 1: frame index SHOOT_CLIMAX (2) of convert-art.py's 6-frame shoot groups
            m['offset'] = missile_offsets(own)
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
    if extra:
        c.update(extra)
    t.add('creatures.%s.%s.name.singular' % (MOD, cid), ru_name[0])
    t.add('creatures.%s.%s.name.plural' % (MOD, cid), ru_name[1])
    return cid, c

# ---------------------------------------------------------------- hero classes and heroes

def hero_class(t, faction, cid, name, ru_name, affinity, borrow_index, primary, low, high, skills,
               tavern, commander=None):
    """borrow_index: original class index whose look is reused (0 knight, 1 cleric, ...)."""
    core = load(VCMI_CONFIG + '/heroClasses.json')
    orig = next(v for v in core.values() if v['index'] == borrow_index)
    c = {
        'name': name, 'faction': faction, 'affinity': affinity, 'commander': commander or orig['commander'],
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
    spec_large, spec_small = 'UN44.DEF:0:%d' % spec_icon, 'UN32.DEF:0:%d' % spec_icon
    if os.path.exists(os.path.join(ROOT, 'Content/sprites', own, 'specialtyLarge.png')):   # the artist's icon
        spec_large, spec_small = own + 'specialtyLarge.png', own + 'specialtySmall.png'
    h = {
        'class': cls, 'female': female,
        'images': {'large': large, 'small': small,
                   'specialtyLarge': spec_large, 'specialtySmall': spec_small},
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

def original_dwelling(borrow):
    """(map DEF, ambient sound) of the original adventure-map dwelling of a creature."""
    core = load(VCMI_CONFIG + '/objects/dwellings.json')['creatureGeneratorCommon']['types']
    for typ in core.values():
        if typ['creatures'][0][0] == borrow:
            text = lod.read(H3DATA + '/H3bitmap.lod', 'Objects.txt')[1].decode('cp1252')
            for line in text.replace('\r', '').split('\n')[1:]:
                c = line.split()
                if len(c) >= 9 and c[5] == '17' and int(c[6]) == typ['index']:
                    return c[0], typ.get('sounds', {}).get('ambient', ['LOOPSWOR'])[0]
    raise KeyError('no original dwelling for ' + borrow)

def dwelling_object_like(t, oid, name, ru_name, creature_id, borrow):
    """Map dwelling for one of our creatures, borrowing the original dwelling of `borrow`."""
    def_name, ambient = original_dwelling(borrow)
    return dwelling_object(t, oid, name, ru_name, creature_id, def_name, ambient)

def dwelling_object(t, oid, name, ru_name, creature_id, borrow_def, ambient):
    """A creatureGeneratorCommon map object (external dwelling) for one creature."""
    if has_map_sprite('dwellings', kebab(oid)):     # the artist's picture, named like the object
        return own_dwelling_object(t, oid, name, ru_name, creature_id, kebab(oid), ambient)
    o = {'name': name, 'creatures': [[creature_id]], 'sounds': {'ambient': [ambient]},
         'templates': {'default': h3_template(borrow_def)}}
    t.add('mapObject.%s.creatureGeneratorCommon.%s.name' % (MOD, oid), ru_name)
    return oid, o


# ---------------------------------------------------------------- town buildings and output

def building(name, ru_name, desc, ru_desc, cost=None, **extra):
    """(building config, Russian name, Russian description)."""
    d = {'name': name, 'description': desc}
    if cost is not None:
        d['cost'] = cost
    d.update(extra)
    return d, ru_name, ru_desc

def hall_chain(names, ru_names, place, ru_place):
    """Village hall .. capitol. place / ru_place: 'your village' / 'деревне'."""
    gold = [500, 1000, 2000, 4000]
    cost = [None, {'gold': 2500}, {'gold': 5000}, {'gold': 10000}]
    out = {}
    for i, bid in enumerate(['villageHall', 'townHall', 'cityHall', 'capitol']):
        if bid == 'capitol':
            desc = 'The %s earns %s %d gold per day.' % (names[i], place, gold[i])
            ru = '%s приносит %s %d золота в день.' % (ru_names[i], ru_place, gold[i])
        else:
            desc = 'The %s allows you to purchase town structures and earns %s %d gold per day.' % (names[i], place, gold[i])
            ru = '%s позволяет возводить постройки и приносит %s %d золота в день.' % (ru_names[i], ru_place, gold[i])
        out[bid] = building(names[i], ru_names[i], desc, ru, cost[i])
    return out

def fort_chain(names, ru_names):
    return {
        'fort': building(names[0], ru_names[0], 'The %s surrounds the town with defensive walls.' % names[0],
                         '%s окружает город защитными стенами.' % ru_names[0], {'gold': 5000, 'wood': 20, 'ore': 20}),
        'citadel': building(names[1], ru_names[1],
                            'Adds a keep and a moat to the defenses and increases base creature growth by 50%.',
                            'Добавляет к обороне башню и ров и увеличивает прирост существ на 50%.', {'gold': 2500, 'ore': 5}),
        'castle': building(names[2], ru_names[2],
                           'Adds two arrow towers, strengthens the walls and doubles base creature growth.',
                           'Добавляет две стрелковые башни, укрепляет стены и удваивает прирост существ.',
                           {'gold': 5000, 'wood': 10, 'ore': 10}),
    }

def guild_chain(name, ru_name, levels=5):
    """Mage guild levels; labels stay within the 22 characters a hall label holds."""
    out = {}
    for lvl in range(1, levels + 1):
        cost = {'gold': 2000, 'wood': 5, 'ore': 5} if lvl == 1 else \
            {'gold': 1000, 'wood': 5, 'ore': 5, 'mercury': 2 + 2 * lvl, 'sulfur': 2 + 2 * lvl,
             'crystal': 2 + 2 * lvl, 'gems': 2 + 2 * lvl}
        out['mageGuild%d' % lvl] = building(
            '%s %d' % (name, lvl), '%s %d' % (ru_name, lvl),
            'Scrolls of level %d jutsu. A visiting hero learns the spells kept here.' % lvl,
            'Свитки техник %d уровня. Герой может изучить хранящиеся здесь заклинания.' % lvl, cost)
    return out

def dwelling_pair(level, name, ru_name, cname, ru_cname, up_cname, ru_up_cname, cost, up_cost, requires):
    """Dwelling of a tier and its upgrade ("Ул." prefix as in the original Russian)."""
    base = building(name, ru_name, 'The %s allows you to recruit %s.' % (name, cname),
                    '%s позволяет нанимать существ: %s.' % (ru_name, ru_cname), cost, requires=requires)
    up = building('Upg. ' + name, 'Ул. ' + ru_name, 'The upgraded %s allows you to recruit %s.' % (name, up_cname),
                  'Улучшенное здание «%s» позволяет нанимать существ: %s.' % (ru_name, ru_up_cname), up_cost,
                  upgrades='dwellingLvl%d' % level)
    return {'dwellingLvl%d' % level: base, 'dwellingUpLvl%d' % level: up}

def faction_texts(t, faction, ru_name, ru_description, town_names_ru, building_ru, extra=None):
    """Russian texts of a faction: name, description, town names, building names/descriptions."""
    fk = 'faction.%s.%s.' % (MOD, faction)
    t.add(fk + 'name', ru_name)
    t.add(fk + 'description', ru_description)
    for i, ru in enumerate(town_names_ru):
        t.add(fk + 'randomName.%d' % i, ru)
    for bid, (ru_n, ru_d) in building_ru.items():
        bk = 'building.%s.%s.%s.' % (MOD, faction, bid)
        t.add(bk + 'name', ru_n)
        t.add(bk + 'description', ru_d)
    for k, v in (extra or {}).items():
        t.add('building.%s.%s.%s' % (MOD, faction, k), v)

def register(files, ru_file):
    """Add generated files to mod.json (content lists and the Russian translations)."""
    mj = json.load(open(os.path.join(ROOT, 'mod.json'), encoding='utf-8'))
    for kind, lst in files.items():
        entries = mj.setdefault(kind, [])
        for rel in lst:
            e = rel.replace('Content/', '', 1)
            if e not in entries:
                entries.append(e)
    tr = mj['russian'].setdefault('translations', [])
    e = ru_file.replace('Content/', '', 1)
    if e not in tr:
        tr.append(e)
    write_json('mod.json', mj)

def town_screen(faction):
    """Town screen made by tools/townscreen.py from the artist's art, or None."""
    path = os.path.join(ROOT, 'Content/sprites/naruto', faction, 'town/structures.json')
    return json.load(open(path)) if os.path.exists(path) else None

def own_dwelling_object(t, oid, name, ru_name, creature_id, slug, ambient='LOOPCAVE'):
    """Map dwelling with the artist's picture (tools/convert-art.py: naruto/map/dwellings/<slug>),
    falling back to nothing: call only when the sprite exists."""
    o = {'name': name, 'creatures': [[creature_id]], 'sounds': {'ambient': [ambient]},
         'templates': {'default': {'animation': 'naruto/map/dwellings/' + slug,
                                   'mask': ['VVVV', 'VVBB', 'VVAB'], 'visitableFrom': ['---', '+++', '+++']}}}
    t.add('mapObject.%s.creatureGeneratorCommon.%s.name' % (MOD, oid), ru_name)
    return oid, o

TOWN_MASK = ['VVVVVV', 'VVVVVV', 'VVVVVV', 'VVBBBV', 'VBBBBB', 'VBBABB']   # VCMI's base town mask (moddables.json)

def town_map_object(faction, borrowed):
    """Adventure-map town with the artist's three pictures (tools/convert-art.py:
    naruto/map/towns/<faction>-<level>): village until the fort, the fort picture up to the
    citadel, the castle picture from the castle or the capitol on. Borrowed look otherwise."""
    levels = ('village', 'fort', 'castle')
    if not all(has_map_sprite('towns', '%s-%s' % (faction, l)) for l in levels):
        return borrowed
    return {'filters': {'village': ['noneOf', ['fort']],
                        'fort': ['allOf', ['fort'], ['noneOf', ['castle'], ['capitol']]],
                        'castle': ['anyOf', ['castle'], ['capitol']]},
            'templates': {l: {'animation': 'naruto/map/towns/%s-%s' % (faction, l), 'mask': TOWN_MASK,
                              'visitableFrom': ['---', '+++', '+++']} for l in levels}}

def town_map_template(map_object):
    """Map-file template for a town of this mapObject config (its biggest picture)."""
    t = map_object['templates']['castle']
    if t['animation'].startswith('naruto/'):
        return {'animation': t['animation'], 'editorAnimation': '', 'mask': t['mask'], 'visitableFrom': ['---', '+-+', '+++']}
    h = h3_template(t['animation'])
    return {'animation': h['animation'], 'editorAnimation': '', 'mask': h['mask'], 'visitableFrom': ['---', '+-+', '+++']}

def kebab(oid):
    return re.sub('([A-Z])', lambda m: '-' + m.group(1).lower(), oid)

def has_map_sprite(folder, slug):
    return os.path.exists(os.path.join(ROOT, 'Content/sprites/naruto/map', folder, slug + '.json'))
