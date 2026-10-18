"""Artifacts: generates Content/config/artifacts/artifacts.json from the spec in
~/O/Projects/HoMM3-Naruto/Plans/Naruto-Mod-Artifacts.md ("Details"). Pictures come from
tools/convert-art.py (Content/sprites/naruto/artifacts/<id>/).
Run: python3 tools/towns/artifacts.py   (then tools/check.sh)"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from townkit import *

AREA = 'artifacts'
t = Texts()

def skill(name, val):
    return {'type': 'PRIMARY_SKILL', 'subtype': 'primarySkill.' + name, 'val': val, 'valueType': 'BASE_NUMBER'}
def b(btype, val=0, subtype=None, **extra):
    d = {'type': btype, 'val': val, 'valueType': 'BASE_NUMBER'}
    if subtype:
        d['subtype'] = subtype
    d.update(extra)
    return d
def of_faction(bonus, faction):
    return dict(bonus, limiters=['CREATURES_ONLY', {'type': 'FACTION_LIMITER', 'faction': faction}])
def growth(level, val, faction=None):   # like the Legion parts: the town the hero visits or guards
    g = {'type': 'CREATURE_GROWTH', 'subtype': 'creatureLevel%d' % level, 'val': val, 'propagator': 'TOWN_AND_VISITOR'}
    if faction:
        g['limiters'] = [{'type': 'FACTION_LIMITER', 'faction': faction}]
    return g

ART = []
def art(aid, slot, cls, value, name, ru_name, desc, ru_desc, bonuses=None, instance=None, components=None):
    a = {'type': ['HERO'], 'slot': slot, 'class': cls, 'value': value,
         'text': {'name': name, 'description': desc, 'event': 'You find %s.' % name},
         'graphics': {'image': 'naruto/artifacts/%s/icon.png' % aid, 'scenarioBonus': 'naruto/artifacts/%s/bonus.png' % aid,
                      'map': 'naruto/artifacts/%s/map' % aid}}
    if bonuses:
        a['bonuses'] = bonuses
    if instance:
        a['instanceBonuses'] = instance
    if components:
        a['components'] = components
    key = 'artifact.%s.%s.' % (MOD, aid)
    t.add(key + 'name', ru_name)
    t.add(key + 'description', ru_desc)
    t.add(key + 'event', 'Вы нашли: %s.' % ru_name)
    ART.append((aid, a))

# ---------------------------------------------------------------- everyday ninja gear
art('kunai', 'RIGHT_HAND', 'TREASURE', 1000, 'Kunai', 'Кунай', '+2 Attack.', '+2 к атаке.', {'attack': skill('attack', 2)})
art('leafForeheadProtector', 'HEAD', 'TREASURE', 1500, 'Leaf Forehead Protector', 'Протектор Листа',
    '+2 Defense; Konoha creatures +1 morale.', '+2 к защите; существа Конохи +1 к боевому духу.',
    {'defence': skill('defence', 2), 'konoha': of_faction(b('MORALE', 1), 'konohagakure')})
art('sandForeheadProtector', 'HEAD', 'TREASURE', 1500, 'Sand Forehead Protector', 'Протектор Песка',
    '+2 Defense; Suna creatures +1 Defense.', '+2 к защите; существа Суны +1 к защите.',
    {'defence': skill('defence', 2), 'suna': of_faction(skill('defence', 1), 'sunagakure')})
art('mistForeheadProtector', 'HEAD', 'TREASURE', 1500, 'Mist Forehead Protector', 'Протектор Тумана',
    '+2 Defense; Kiri creatures +1 Attack.', '+2 к защите; существа Кири +1 к атаке.',
    {'defence': skill('defence', 2), 'kiri': of_faction(skill('attack', 1), 'kirigakure')})
art('chuninVest', 'TORSO', 'MINOR', 2500, 'Chunin Vest', 'Жилет чунина', '+3 Defense.', '+3 к защите.',
    {'defence': skill('defence', 3)})
art('explosiveTags', 'MISC', 'TREASURE', 1500, 'Explosive Tags', 'Взрывные печати',
    '+1 Attack; the Ballista deals 50% more damage.', '+1 к атаке; баллиста наносит на 50% больше урона.',
    {'attack': skill('attack', 1),
     'ballista': dict(b('PERCENTAGE_DAMAGE_BOOST', 50, 'damageTypeRanged'), valueType='ADDITIVE_VALUE',
                      limiters=[{'type': 'CREATURE_TYPE_LIMITER', 'creature': 'ballista'}])})
art('soldierPills', 'MISC', 'MINOR', 2500, 'Soldier Pills', 'Пилюли солдата', '+1 morale, +1 Attack.',
    '+1 к боевому духу, +1 к атаке.', {'morale': b('MORALE', 1), 'attack': skill('attack', 1)})
art('chakraPills', 'MISC', 'TREASURE', 1500, 'Chakra Pills', 'Пилюли чакры', '+3 spell points per day.',
    '+3 очка магии в день.', {'mana': b('MANA_REGENERATION', 3)})
art('gamaChanWallet', 'MISC', 'TREASURE', 1500, 'Gama-chan Wallet', 'Кошелёк Гама-чан', '+250 gold per day.',
    '+250 золота в день.', instance={'gold': dict(b('GENERATE_RESOURCE', 250, 'resource.gold'), stacking='ALWAYS')})
art('ichirakuRamenCoupon', 'MISC', 'TREASURE', 1000, 'Ichiraku Ramen Coupon', 'Купон на рамен Ичираку',
    '+1 morale, +1 luck.', '+1 к боевому духу, +1 к удаче.', {'morale': b('MORALE', 1), 'luck': b('LUCK', 1)})

# ---------------------------------------------------------------- famous items
art('flyingThunderGodKunai', 'MISC', 'MAJOR', 10000, 'Flying Thunder God Kunai', 'Кунай Летящего Бога Грома',
    'The hero can cast Dimension Door (basic).', 'Герой может применять Дверь измерений (базовый уровень).',
    {'teleport': b('SPELL', 1, 'spell.dimensionDoor')})
art('mightGuysLegWeights', 'FEET', 'MAJOR', 6000, "Might Guy's Leg Weights", 'Утяжелители Майто Гая',
    'Troops +2 speed.', 'Скорость войск +2.', {'speed': b('STACKS_SPEED', 2)})
art('hunterNinMask', 'HEAD', 'MINOR', 3000, 'Hunter-nin Mask', 'Маска охотника-ниндзя', '+2 sight on the map, +1 Attack.',
    '+2 к обзору на карте, +1 к атаке.', {'sight': b('SIGHT_RADIUS', 2), 'attack': skill('attack', 1)})
art('temarisGiantFan', 'LEFT_HAND', 'MAJOR', 7000, "Temari's Giant Fan", 'Огромный веер Темари',
    'Troops take 25% less damage from shooters.', 'Войска получают на 25% меньше урона от стрелков.',
    {'wind': b('GENERAL_DAMAGE_REDUCTION', 25, 'damageTypeRanged')})
art('hiruko', 'TORSO', 'MAJOR', 6000, 'Hiruko', 'Хируко', '+5 Defense.', '+5 к защите.', {'defence': skill('defence', 5)})
art('akatsukiCloak', 'SHOULDERS', 'MAJOR', 8000, 'Akatsuki Cloak', 'Плащ Акацуки', '+3 Defense, +3 Spell Power.',
    '+3 к защите, +3 к силе магии.', {'defence': skill('defence', 3), 'spellpower': skill('spellpower', 3)})
art('scrollOfSeals', 'MISC', 'RELIC', 15000, 'Scroll of Seals', 'Свиток печатей', 'The hero can cast every level 4 spell.',
    'Герой может применять любое заклинание 4-го уровня.', {'spells': b('SPELLS_OF_LEVEL', 3, 'spellLevel4')})
art('summoningContractToads', 'MISC', 'MAJOR', 5000, 'Summoning Contract: Toads', 'Контракт призыва: жабы',
    'A Konoha town the hero visits or guards gains 1 more tier 7 creature per week.',
    'Город Конохи, где стоит герой, получает на 1 существо 7-го уровня в неделю больше.',
    instance={'toads': growth(7, 1, 'konohagakure')})
art('summoningContractSlugs', 'MISC', 'MAJOR', 5000, 'Summoning Contract: Slugs', 'Контракт призыва: слизни',
    'A Konoha town the hero visits or guards gains 3 more tier 4 creatures (medics) per week.',
    'Город Конохи, где стоит герой, получает на 3 существа 4-го уровня (медиков) в неделю больше.',
    instance={'slugs': growth(4, 3, 'konohagakure')})
art('summoningContractSnakes', 'MISC', 'MAJOR', 5000, 'Summoning Contract: Snakes', 'Контракт призыва: змеи',
    'Any town the hero visits or guards gains 1 more tier 6 creature per week.',
    'Любой город, где стоит герой, получает на 1 существо 6-го уровня в неделю больше.',
    instance={'snakes': growth(6, 1)})

# ---------------------------------------------------------------- Kekkei Genkai eyes
art('sharingan', 'NECK', 'RELIC', 15000, 'Sharingan', 'Шаринган',
    '+3 Spell Power; troops immune to Blind; +20% chance to learn spells of level 1-3 cast in battle.',
    '+3 к силе магии; войска невосприимчивы к Слепоте; +20% к шансу выучить заклинание 1–3-го уровня, применённое в бою.',
    {'spellpower': skill('spellpower', 3), 'noBlind': b('SPELL_IMMUNITY', 0, 'spell.blind'),
     'copy': dict(b('LEARN_BATTLE_SPELL_CHANCE', 20), valueType='ADDITIVE_VALUE'),
     'copyLevel': dict(b('LEARN_BATTLE_SPELL_LEVEL_LIMIT', 3), valueType='INDEPENDENT_MAX')})
art('byakugan', 'NECK', 'RELIC', 12000, 'Byakugan', 'Бьякуган', '+3 sight; shooters ignore distance and wall penalties.',
    '+3 к обзору; стрелки не получают штрафов за расстояние и стены.',
    {'sight': b('SIGHT_RADIUS', 3), 'noDistance': dict(b('NO_DISTANCE_PENALTY'), limiters=['SHOOTER_ONLY']),
     'noWall': dict(b('NO_WALL_PENALTY'), limiters=['SHOOTER_ONLY'])})
art('rinnegan', 'NECK', 'RELIC', 25000, 'Rinnegan', 'Риннеган', 'Expert mastery of all four schools of magic.',
    'Экспертное владение всеми четырьмя школами магии.', {'schools': b('MAGIC_SCHOOL_SKILL', 3, 'spellSchool.any')})

# ---------------------------------------------------------------- legendary swords
art('kusanagi', 'RIGHT_HAND', 'RELIC', 12000, 'Kusanagi', 'Кусанаги', "+3 Attack; troops ignore 30% of the enemy's Defense.",
    '+3 к атаке; войска игнорируют 30% защиты врага.', {'attack': skill('attack', 3), 'pierce': b('ENEMY_DEFENCE_REDUCTION', 30)})
art('kubikiribocho', 'RIGHT_HAND', 'MAJOR', 7000, 'Kubikiribocho', 'Кубикирибочо', '+5 Attack.', '+5 к атаке.',
    {'attack': skill('attack', 5)})
art('samehada', 'RIGHT_HAND', 'RELIC', 12000, 'Samehada', 'Самехада', '+3 Attack; enemy spells cost 3 more mana.',
    '+3 к атаке; заклинания врага стоят на 3 маны больше.',
    {'attack': skill('attack', 3), 'chakraEater': b('CHANGES_SPELL_COST_FOR_ENEMY', 3)})
art('hiramekarei', 'RIGHT_HAND', 'MAJOR', 7000, 'Hiramekarei', 'Хирамекарей', '+2 Attack, +3 Knowledge.',
    '+2 к атаке, +3 к знаниям.', {'attack': skill('attack', 2), 'knowledge': skill('knowledge', 3)})
art('kiba', 'RIGHT_HAND', 'MAJOR', 7000, 'Kiba Blades', 'Клинки Киба', '+3 Attack; air spells +20%.',
    '+3 к атаке; заклинания Воздуха +20%.', {'attack': skill('attack', 3), 'air': b('SPELL_DAMAGE', 20, 'spellSchool.air')})
art('nuibari', 'RIGHT_HAND', 'MAJOR', 8000, 'Nuibari', 'Нуибари', "+3 Attack; troops' melee hits bind the target 10% of the time.",
    '+3 к атаке; удары войск в ближнем бою в 10% случаев сковывают цель.',
    {'attack': skill('attack', 3), 'thread': dict(b('SPELL_AFTER_ATTACK', 10, 'spell.bind'), addInfo=[1, 2])})
art('shibuki', 'RIGHT_HAND', 'MAJOR', 7000, 'Shibuki', 'Шибуки', '+3 Attack; fire spells +20%.',
    '+3 к атаке; заклинания Огня +20%.', {'attack': skill('attack', 3), 'fire': b('SPELL_DAMAGE', 20, 'spellSchool.fire')})
art('kabutowari', 'RIGHT_HAND', 'MAJOR', 8000, 'Kabutowari', 'Кабутовари', "+3 Attack; troops ignore 15% of the enemy's Defense.",
    '+3 к атаке; войска игнорируют 15% защиты врага.', {'attack': skill('attack', 3), 'split': b('ENEMY_DEFENCE_REDUCTION', 15)})

# ---------------------------------------------------------------- Kage sets
art('hokageHat', 'HEAD', 'MAJOR', 6000, 'Hokage Hat', 'Шляпа Хокаге', '+1 morale, +2 Spell Power, +2 Knowledge.',
    '+1 к боевому духу, +2 к силе магии, +2 к знаниям.',
    {'morale': b('MORALE', 1), 'spellpower': skill('spellpower', 2), 'knowledge': skill('knowledge', 2)})
art('hokageCloak', 'SHOULDERS', 'MAJOR', 6000, 'Hokage Cloak', 'Плащ Хокаге', '+3 Defense; Konoha creatures +1 morale.',
    '+3 к защите; существа Конохи +1 к боевому духу.',
    {'defence': skill('defence', 3), 'konoha': of_faction(b('MORALE', 1), 'konohagakure')})
art('firstHokagesNecklace', 'NECK', 'MAJOR', 7000, "First Hokage's Necklace", 'Ожерелье Первого Хокаге',
    'Troops regenerate 10 health per round.', 'Войска восстанавливают 10 здоровья каждый раунд.', {'regeneration': b('HP_REGENERATION', 10)})
art('willOfFire', 'HEAD', 'SPECIAL', 40000, 'Will of Fire', 'Воля Огня',
    'Hokage Hat, Hokage Cloak and First Hokage\'s Necklace combined: +2 morale; Konoha creatures +2 Attack and +2 Defense.',
    'Шляпа Хокаге, Плащ Хокаге и Ожерелье Первого Хокаге вместе: +2 к боевому духу; существа Конохи +2 к атаке и +2 к защите.',
    {'morale': b('MORALE', 2), 'attack': of_faction(skill('attack', 2), 'konohagakure'),
     'defence': of_faction(skill('defence', 2), 'konohagakure')},
    components=['hokageHat', 'hokageCloak', 'firstHokagesNecklace'])
art('kazekageHat', 'HEAD', 'MAJOR', 6000, 'Kazekage Hat', 'Шляпа Казекаге', '+2 Defense, +2 Spell Power.',
    '+2 к защите, +2 к силе магии.', {'defence': skill('defence', 2), 'spellpower': skill('spellpower', 2)})
art('gourdOfSand', 'SHOULDERS', 'MAJOR', 7000, 'Gourd of Sand', 'Тыква с песком', 'Troops take 10% less damage from attacks.',
    'Войска получают на 10% меньше урона от атак.', {'sand': b('GENERAL_DAMAGE_REDUCTION', 10, 'damageTypeAll')})
art('kazekageRobe', 'TORSO', 'MAJOR', 6000, 'Kazekage Robe', 'Мантия Казекаге', '+4 Defense.', '+4 к защите.',
    {'defence': skill('defence', 4)})
art('sandCoffin', 'HEAD', 'SPECIAL', 40000, 'Sand Coffin', 'Песчаный гроб',
    'Kazekage Hat, Gourd of Sand and Kazekage Robe combined: each battle opens with expert Stone Skin on the army for the whole battle; Suna creatures +2 Defense.',
    'Шляпа Казекаге, Тыква с песком и Мантия Казекаге вместе: каждый бой начинается с Каменной кожи (эксперт) на армии до конца боя; существа Суны +2 к защите.',
    {'stoneSkin': dict(b('OPENING_BATTLE_SPELL', 50, 'spell.stoneSkin'), addInfo=3),
     'defence': of_faction(skill('defence', 2), 'sunagakure')},
    components=['kazekageHat', 'gourdOfSand', 'kazekageRobe'])
art('mizukageHat', 'HEAD', 'MAJOR', 6000, 'Mizukage Hat', 'Шляпа Мизукаге', '+2 Attack, +2 Knowledge.',
    '+2 к атаке, +2 к знаниям.', {'attack': skill('attack', 2), 'knowledge': skill('knowledge', 2)})
art('mizukageRobe', 'TORSO', 'MAJOR', 6000, 'Mizukage Robe', 'Мантия Мизукаге', '+3 Attack, +1 Defense.',
    '+3 к атаке, +1 к защите.', {'attack': skill('attack', 3), 'defence': skill('defence', 1)})
art('hozukiWaterFlask', 'MISC', 'MAJOR', 5000, 'Hozuki Water Flask', 'Фляга Хозуки', 'Troops take 10% less damage in melee.',
    'Войска получают на 10% меньше урона в ближнем бою.', {'water': b('GENERAL_DAMAGE_REDUCTION', 10, 'damageTypeMelee')})
art('bloodyMist', 'HEAD', 'SPECIAL', 40000, 'Bloody Mist', 'Кровавый Туман',
    'Mizukage Hat, Mizukage Robe and Hozuki Water Flask combined: each battle opens with expert Bloodlust on the army for the whole battle; Kiri creatures +2 Attack.',
    'Шляпа Мизукаге, Мантия Мизукаге и Фляга Хозуки вместе: каждый бой начинается с Жажды крови (эксперт) на армии до конца боя; существа Кири +2 к атаке.',
    {'bloodlust': dict(b('OPENING_BATTLE_SPELL', 50, 'spell.bloodlust'), addInfo=3),
     'attack': of_faction(skill('attack', 2), 'kirigakure')},
    components=['mizukageHat', 'mizukageRobe', 'hozukiWaterFlask'])

artifacts = dict(ART)
missing = [a for a in artifacts if not os.path.exists(os.path.join(ROOT, 'Content/sprites/naruto/artifacts', a, 'icon.png'))]
assert not missing, 'run tools/convert-art.py first; missing pictures: %s' % missing

D = 'Content/config/%s/' % AREA
files = {'artifacts': [write_json(D + 'artifacts.json', artifacts)]}
ru_file = write_json('Content/config/translations/russian-%s.json' % AREA, dict(sorted(t.ru.items())))
register(files, ru_file)
print('artifacts: %d (%d combined), %d Russian strings' % (len(artifacts), sum(1 for a in artifacts.values() if 'components' in a), len(t.ru)))
