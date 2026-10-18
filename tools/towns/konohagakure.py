"""Konohagakure: generates the town's JSON from the spec in the vault note
~/O/Projects/HoMM3-Naruto/Plans/Naruto-Mod-Konohagakure.md ("Details").
Run: python3 tools/towns/konohagakure.py   (then tools/check.sh)"""
import copy, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from townkit import *

F = 'konohagakure'
t = Texts()
castle = load(VCMI_CONFIG + '/factions/castle.json')['castle']
rampart = load(VCMI_CONFIG + '/factions/rampart.json')['rampart']

def stats(cost, hp, speed, att, dfn, dmg, growth, fight, ai, amount):
    return dict(cost=cost, hp=hp, speed=speed, attack=att, defense=dfn, dmg=dmg,
                growth=growth, fight=fight, ai=ai, amount=amount)

# ------------------------------------------------------------------ creatures

FIREBALL = 'fireball'   # the Uchiha fire style
blind = lambda chance: {'type': 'SPELL_AFTER_ATTACK', 'subtype': 'spell.blind', 'val': chance, 'addInfo': [1, 0]}
gentle_fist = {'type': 'SPELL_AFTER_ATTACK', 'subtype': 'spell.dispelHelpful', 'val': 100}

creatures = dict([
    creature(t, F, 'academyStudent', 1, ('Academy Student', 'Academy Students'),
             ('Ученик Академии', 'Ученики Академии'), 'rogue', 'Rogue',
             stats({'gold': 50}, 8, 5, 4, 4, (1, 3), 14, 80, 75, (20, 50)),
             upgrades=['genin']),
    creature(t, F, 'genin', 1, ('Genin', 'Genin'), ('Генин', 'Генины'), 'halfling', 'Halfling',
             stats({'gold': 75}, 8, 6, 5, 4, (1, 3), 14, 100, 115, (20, 50)),
             abilities={'shooter': {'type': 'SHOOTER'}}, shots=8, projectile='shuriken'),
    creature(t, F, 'ninjaHound', 2, ('Ninja Hound', 'Ninja Hounds'), ('Пёс-ниндзя', 'Псы-ниндзя'),
             'hellHound', 'Hell Hound',
             stats({'gold': 100}, 10, 7, 6, 4, (2, 4), 9, 130, 140, (16, 30)),
             upgrades=['ninkenPackLeader']),
    creature(t, F, 'ninkenPackLeader', 2, ('Ninken Pack Leader', 'Ninken Pack Leaders'),
             ('Вожак нинкенов', 'Вожаки нинкенов'), 'cerberus', 'Cerberus',
             stats({'gold': 140}, 10, 9, 7, 5, (2, 4), 9, 180, 200, (16, 30)),
             abilities={'bitesTwice': {'type': 'ADDITIONAL_ATTACK', 'val': 1}}),
    creature(t, F, 'hyugaGuard', 3, ('Hyuga Guard', 'Hyuga Guards'), ('Страж Хьюга', 'Стражи Хьюга'),
             'monk', 'Monk',
             stats({'gold': 200}, 25, 5, 8, 8, (3, 5), 7, 300, 320, (12, 25)),
             upgrades=['hyugaMainBranch'], abilities={'gentleFist': gentle_fist}, double_wide=False),
    creature(t, F, 'hyugaMainBranch', 3, ('Hyuga Main Branch', 'Hyuga Main Branch'),
             ('Хьюга главной ветви', 'Хьюга главной ветви'), 'zealot', 'Zealot',
             stats({'gold': 250}, 28, 7, 10, 9, (3, 6), 7, 370, 420, (12, 25)),
             abilities={'gentleFist': gentle_fist,
                        'chakraPoints': {'type': 'ENEMY_DEFENCE_REDUCTION', 'val': 30}}, double_wide=False),
    creature(t, F, 'medicalNinja', 4, ('Medical Ninja', 'Medical Ninja'), ('Ниндзя-медик', 'Ниндзя-медики'),
             'woodElf', 'Wood Elf',
             stats({'gold': 300}, 30, 5, 7, 9, (4, 6), 4, 380, 420, (10, 20)),
             upgrades=['seniorMedic'],
             abilities={'heals': {'type': 'SPELLCASTER', 'subtype': 'spell.cure', 'val': 1},
                        'casts': {'type': 'CASTS', 'val': 2},
                        'healPower': {'type': 'SPECIFIC_SPELL_POWER', 'subtype': 'spell.cure', 'val': 8}}),
    creature(t, F, 'seniorMedic', 4, ('Senior Medic', 'Senior Medics'), ('Старший медик', 'Старшие медики'),
             'grandElf', 'Grand Elf',
             stats({'gold': 400}, 35, 6, 8, 10, (5, 7), 4, 480, 560, (10, 20)),
             abilities={'heals': {'type': 'SPELLCASTER', 'subtype': 'spell.cure', 'val': 2},
                        'casts': {'type': 'CASTS', 'val': 3},
                        'healPower': {'type': 'SPECIFIC_SPELL_POWER', 'subtype': 'spell.cure', 'val': 12}}),
    creature(t, F, 'uchihaPolice', 5, ('Uchiha Police', 'Uchiha Police'), ('Полицейский Учиха', 'Полиция Учиха'),
             'mage', 'Mage',
             stats({'gold': 400}, 30, 6, 11, 8, (8, 12), 3, 450, 520, (8, 16)),
             upgrades=['sharinganMaster'], shots=12, projectile=FIREBALL,
             abilities={'shooter': {'type': 'SHOOTER'}, 'sharingan': blind(10)}),
    creature(t, F, 'sharinganMaster', 5, ('Sharingan Master', 'Sharingan Masters'),
             ('Мастер Шарингана', 'Мастера Шарингана'), 'archMage', 'Arch Mage',
             stats({'gold': 475}, 30, 7, 12, 10, (9, 12), 3, 520, 700, (8, 16)),
             shots=16, projectile=FIREBALL,
             abilities={'shooter': {'type': 'SHOOTER'}, 'noMeleePenalty': {'type': 'NO_MELEE_PENALTY'},
                        'greatFireball': {'type': 'SPELL_LIKE_ATTACK', 'subtype': 'spell.fireballAbility'},
                        'sharingan': blind(20)}),
    creature(t, F, 'anbuOperative', 6, ('ANBU Operative', 'ANBU Operatives'),
             ('Оперативник АНБУ', 'Оперативники АНБУ'), 'vampire', 'Vampire',
             stats({'gold': 1000}, 80, 8, 16, 12, (15, 20), 2, 1300, 1500, (4, 10)),
             upgrades=['anbuCaptain'], abilities={'fromTheShadows': {'type': 'BLOCKS_RETALIATION'}}),
    creature(t, F, 'anbuCaptain', 6, ('ANBU Captain', 'ANBU Captains'), ('Капитан АНБУ', 'Капитаны АНБУ'),
             'vampireLord', 'Nosferatu',
             stats({'gold': 1250}, 90, 10, 18, 14, (18, 24), 2, 1650, 2000, (4, 10)),
             abilities={'fromTheShadows': {'type': 'BLOCKS_RETALIATION'},
                        'vanish': {'type': 'RETURN_AFTER_STRIKE'}}),
    creature(t, F, 'toadWarrior', 7, ('Toad Warrior', 'Toad Warriors'), ('Жаба-воин', 'Жабы-воины'),
             'behemoth', 'Young Behemoth',
             stats({'gold': 2800, 'gems': 1}, 180, 8, 19, 17, (30, 45), 1, 3300, 4200, (1, 4)),
             upgrades=['gamabunta'], abilities={'leaps': {'type': 'FLYING'}}),
    creature(t, F, 'gamabunta', 7, ('Gamabunta', 'Gamabunta'), ('Гамабунта', 'Гамабунта'),
             'ancientBehemoth', 'Ancient Behemoth',
             stats({'gold': 4500, 'gems': 2}, 300, 11, 25, 24, (40, 50), 1, 6000, 8000, (1, 4)),
             abilities={'leaps': {'type': 'FLYING'}, 'swordSweep': {'type': 'ATTACKS_ALL_ADJACENT'}}),
])

# ------------------------------------------------------------------ buildings

def b(name, ru_name, desc, ru_desc, cost=None, **extra):
    d = {'name': name, 'description': desc}
    if cost is not None:
        d['cost'] = cost
    d.update(extra)
    return d, ru_name, ru_desc

HALL_DESC = ('The {0} allows you to purchase town structures and earns your village {1} gold per day.',
             '{0} позволяет возводить постройки и приносит деревне {1} золота в день.')
# Hall labels hold about 22 characters (the original Russian "Гильдия Магов 1 Уровня" is 22).
guild = lambda lvl: b('Jutsu Library Level %d' % lvl, 'Библиотека техник %d' % lvl,
                      'Scrolls of level %d jutsu. A visiting hero learns the spells kept here.' % lvl,
                      'Свитки техник %d уровня. Герой может изучить хранящиеся здесь заклинания.' % lvl,
                      {'gold': 2000, 'wood': 5, 'ore': 5} if lvl == 1 else
                      {'gold': 1000, 'wood': 5, 'ore': 5, 'mercury': 2 + 2 * lvl, 'sulfur': 2 + 2 * lvl,
                       'crystal': 2 + 2 * lvl, 'gems': 2 + 2 * lvl})
def dwelling(name, ru_name, cname, ru_cname, cost, requires=None, up=False):
    what, ru_what = (('upgraded ' if up else '') + name, ('улучшенное здание «%s»' % ru_name) if up else ru_name)
    return b(('Upg. ' if up else '') + name, ('Ул. ' if up else '') + ru_name,   # "Ул." as in the original Russian
             'The %s allows you to recruit %s.' % (what, cname),
             '%s позволяет нанимать существ: %s.' % (ru_what[0].upper() + ru_what[1:], ru_cname),
             cost, **({'requires': requires} if requires else {}),
             **({'upgrades': 'dwellingLvl%d' % up} if up else {}))

TRAIN = [('attack', '+1 Attack', '+1 к атаке'), ('defence', '+1 Defense', '+1 к защите'),
         ('spellpower', '+1 Spell Power', '+1 к силе магии'), ('knowledge', '+1 Knowledge', '+1 к знаниям')]

buildings = {
    'villageHall': b('Hokage Office', 'Кабинет Хокаге', HALL_DESC[0].format('Hokage Office', 500),
                     HALL_DESC[1].format('Кабинет Хокаге', 500)),
    'townHall': b('Hokage Chambers', 'Палаты Хокаге', HALL_DESC[0].format('Hokage Chambers', 1000),
                  HALL_DESC[1].format('Палаты Хокаге', 1000), {'gold': 2500}),
    'cityHall': b('Hokage Tower', 'Башня Хокаге', HALL_DESC[0].format('Hokage Tower', 2000),
                  HALL_DESC[1].format('Башня Хокаге', 2000), {'gold': 5000}),
    'capitol': b('Hokage Residence', 'Резиденция Хокаге',
                 'The Hokage Residence earns your village 4000 gold per day.',
                 'Резиденция Хокаге приносит деревне 4000 золота в день.', {'gold': 10000}),
    'fort': b('Village Gate', 'Врата деревни', 'The Village Gate surrounds Konoha with defensive walls.',
              'Врата деревни окружают Коноху защитными стенами.', {'gold': 5000, 'wood': 20, 'ore': 20}),
    'citadel': b('Fortified Gate', 'Укреплённые врата',
                 'Adds a keep and a moat to the defenses and increases base creature growth by 50%.',
                 'Добавляет к обороне башню и ров и увеличивает прирост существ на 50%.',
                 {'gold': 2500, 'ore': 5}),
    'castle': b('Great Wall of Konoha', 'Великая стена Конохи',
                'Adds two arrow towers, strengthens the walls and doubles base creature growth.',
                'Добавляет две стрелковые башни, укрепляет стены и удваивает прирост существ.',
                {'gold': 5000, 'wood': 10, 'ore': 10}),
    'tavern': b('Ichiraku Ramen', 'Рамен Ичираку',
                'Heroes gather over a bowl of ramen here: hire heroes, hear rumors and visit the Thieves\' Guild. Defenders fight with +1 morale.',
                'Здесь за миской рамена собираются герои: наём героев, слухи и гильдия воров. Защитники города получают +1 к боевому духу.',
                {'gold': 500, 'wood': 5}),
    'blacksmith': b('Tenten\'s Weapon Shop', 'Оружейная лавка Тентен',
                    'Tenten\'s Weapon Shop sells Ballistas to your armies.',
                    'Оружейная лавка Тентен продаёт вашим армиям баллисты.',
                    {'gold': 1000, 'wood': 5}, warMachine='ballista'),
    'marketplace': b('Konoha Market', 'Рынок Конохи',
                     'Trade resources here; the more markets you own, the better the rates.',
                     'Здесь можно обменивать ресурсы; чем больше у вас рынков, тем выгоднее курс.',
                     {'gold': 500, 'wood': 5}),
    'resourceSilo': b('Market Storehouse', 'Склад рынка',
                      'The Market Storehouse adds 1 wood and 1 ore to your stock every day.',
                      'Склад рынка ежедневно пополняет запасы на 1 древесину и 1 руду.',
                      {'gold': 5000, 'ore': 5}, produce={'wood': 1, 'ore': 1}),
    'mageGuild1': guild(1), 'mageGuild2': guild(2), 'mageGuild3': guild(3),
    'mageGuild4': guild(4), 'mageGuild5': guild(5),
    'special1': b('Konoha Hospital', 'Госпиталь Конохи',
                  'The hospital sells First Aid Tents. During a siege, defending troops get +2 Defense and regenerate 20 health each round.',
                  'Госпиталь продаёт палатки первой помощи. При осаде защитники получают +2 к защите и восстанавливают 20 здоровья каждый раунд.',
                  {'gold': 2500, 'wood': 5, 'ore': 5}, requires=['dwellingLvl4'], warMachine='firstAidTent',
                  bonuses=[{'type': 'PRIMARY_SKILL', 'subtype': 'primarySkill.defence', 'val': 2},
                           {'type': 'HP_REGENERATION', 'val': 20}]),
    'special2': b('Training Ground 3', 'Полигон №3',
                  'Click it with a hero in town: each hero may train here once and choose +1 Attack, Defense, Spell Power or Knowledge.',
                  'Щёлкните по нему, когда герой в городе: каждый герой может один раз потренироваться здесь и выбрать +1 к атаке, защите, силе магии или знаниям.',
                  {'gold': 1500, 'ore': 5}, requires=['dwellingLvl1'],
                  # Visited on click only. An automatic visit asks its question when a hero enters
                  # town, and at game start (hero generated in a town that has it) the question is
                  # lost before the screen is ready: the server then waits forever and refuses
                  # every move ("has to answer queries").
                  manualHeroVisit=True,
                  configuration={
                      'visitMode': 'hero', 'selectMode': 'selectPlayer',
                      'onSelectMessage': 'Kakashi holds up two bells. What will you train?',
                      'onVisitedMessage': 'You have already trained at Training Ground 3.',
                      'rewards': [{'message': 'Training pays off: %s.' % en,
                                   'primary': {skill: 1}} for skill, en, _ in TRAIN]}),
    'grail': b('Hokage Rock', 'Скала Хокаге',
               'The faces of the Hokage watch over the village: +5000 gold per day, +50% creature growth and +2 morale for all your heroes.',
               'Лики Хокаге хранят деревню: +5000 золота в день, +50% к приросту существ и +2 к боевому духу всех ваших героев.',
               bonuses=[{'type': 'MORALE', 'val': 2, 'propagator': 'PLAYER'}]),
    'dwellingLvl1': dwelling('Ninja Academy', 'Академия ниндзя', 'Academy Students', 'ученики Академии',
                             {'gold': 500, 'ore': 10}, ['fort']),
    'dwellingLvl2': dwelling('Inuzuka Kennels', 'Псарни Инузука', 'Ninja Hounds', 'псы-ниндзя',
                             {'gold': 1000, 'wood': 5, 'ore': 5}, ['dwellingLvl1']),
    'dwellingLvl3': dwelling('Hyuga Compound', 'Поместье Хьюга', 'Hyuga Guards', 'стражи Хьюга',
                             {'gold': 1000, 'ore': 5}, ['dwellingLvl1']),
    'dwellingLvl4': dwelling('Medical Corps', 'Медицинский корпус', 'Medical Ninja', 'ниндзя-медики',
                             {'gold': 2000, 'wood': 5, 'ore': 5}, ['allOf', ['dwellingLvl1'], ['mageGuild1']]),
    'dwellingLvl5': dwelling('Uchiha District', 'Квартал Учиха', 'Uchiha Police', 'полиция Учиха',
                             {'gold': 3000, 'wood': 5, 'ore': 5, 'mercury': 2, 'sulfur': 2, 'crystal': 2, 'gems': 2},
                             ['allOf', ['dwellingLvl3'], ['mageGuild1']]),
    'dwellingLvl6': dwelling('ANBU Headquarters', 'Штаб АНБУ', 'ANBU Operatives', 'оперативники АНБУ',
                             {'gold': 5000, 'wood': 10, 'ore': 10}, ['dwellingLvl5']),
    'dwellingLvl7': dwelling('Mount Myoboku Gate', 'Врата горы Мёбоку', 'Toad Warriors', 'жабы-воины',
                             {'gold': 20000, 'mercury': 10, 'sulfur': 10, 'crystal': 10, 'gems': 10},
                             ['allOf', ['dwellingLvl6'], ['mageGuild2']]),
    'dwellingUpLvl1': dwelling('Ninja Academy', 'Академия ниндзя', 'Genin', 'генины', {'gold': 1000, 'ore': 5}, up=1),
    'dwellingUpLvl2': dwelling('Inuzuka Kennels', 'Псарни Инузука', 'Ninken Pack Leaders', 'вожаки нинкенов',
                               {'gold': 1000, 'wood': 5, 'ore': 5}, up=2),
    'dwellingUpLvl3': dwelling('Hyuga Compound', 'Поместье Хьюга', 'Hyuga Main Branch fighters', 'бойцы главной ветви Хьюга',
                               {'gold': 1000, 'ore': 5}, up=3),
    'dwellingUpLvl4': dwelling('Medical Corps', 'Медицинский корпус', 'Senior Medics', 'старшие медики',
                               {'gold': 2000, 'ore': 5, 'mercury': 5}, up=4),
    'dwellingUpLvl5': dwelling('Uchiha District', 'Квартал Учиха', 'Sharingan Masters', 'мастера Шарингана',
                               {'gold': 1000, 'mercury': 2, 'sulfur': 2, 'crystal': 2, 'gems': 2}, up=5),
    'dwellingUpLvl6': dwelling('ANBU Headquarters', 'Штаб АНБУ', 'ANBU Captains', 'капитаны АНБУ',
                               {'gold': 3000, 'wood': 10}, up=6),
    'dwellingUpLvl7': dwelling('Mount Myoboku Gate', 'Врата горы Мёбоку', 'Gamabunta', 'Гамабунта',
                               {'gold': 20000, 'mercury': 10, 'sulfur': 10, 'crystal': 10, 'gems': 10}, up=7),
}
BUILDING_RU = {k: (v[1], v[2]) for k, v in buildings.items()}
buildings = {k: v[0] for k, v in buildings.items()}
TRAIN_RU = {'onSelectMessage': 'Какаши показывает два колокольчика. Что будете тренировать?',
            'onVisitedMessage': 'Вы уже тренировались на полигоне №3.',
            'rewards': [(ru, 'Тренировка окупилась: %s.' % ru) for _, _, ru in TRAIN]}

# Town screen: Anton's town art when tools/townscreen.py has built it (background, building
# pictures and positions, hall icons, town icons); otherwise Castle's borrowed screen, minus
# the dock, hordes and Brotherhood (Hospital on the Lighthouse picture, Training Ground on
# the Stables picture, Jutsu Library 5 repeating level 4) with Castle's hall icons.
SCREEN = os.path.join(ROOT, 'Content/sprites/naruto/konohagakure/town/structures.json')
screen = json.load(open(SCREEN)) if os.path.exists(SCREEN) else None
if screen:
    structures = screen['structures']
    town_background, town_icons = screen['background'], screen['icons']
else:
    structures = copy.deepcopy(castle['town']['structures'])
    for k in ('shipyard', 'ship', 'horde1', 'horde1Upgr', 'special3'):
        del structures[k]
    structures['mageGuild5'] = dict(structures['mageGuild4'])
    town_background = castle['town']['townBackground']
    town_icons = {
        'village': {'normal': {'large': 'ITPT.DEF:0:18', 'small': 'ITPA.DEF:0:20'},
                    'built': {'large': 'ITPT.DEF:0:19', 'small': 'ITPA.DEF:0:21'}},
        'fort': {'normal': {'large': 'ITPT.DEF:0:0', 'small': 'ITPA.DEF:0:2'},
                 'built': {'large': 'ITPT.DEF:0:1', 'small': 'ITPA.DEF:0:3'}},
    }
    hall_icons = write_json('Content/sprites/naruto/konohagakure/hallIcons.json', {'images': [
        {'frame': i, 'defFile': 'HALLCSTL.DEF', 'defFrame': i} for i in
        list(range(0, 4)) + [5] + list(range(7, 18)) + [21, 26] + list(range(30, 44))
    ] + [{'frame': 4, 'defFile': 'HALLRAMP.DEF', 'defFrame': 4}]})

siege = copy.deepcopy(castle['town']['siege'])
siege['shooter'] = 'genin'
# battle-queue icon of the arrow towers: the Genin's borrowed portrait
siege['towerIconLarge'] = creatures['genin']['graphics']['iconLarge']
siege['towerIconSmall'] = creatures['genin']['graphics']['iconSmall']

guild_spells = {
    # level 1
    'magicArrow': 30, 'shield': 8, 'protectFire': 3, 'protectWater': 3, 'dispel': 12, 'cure': 12,
    'bless': 8, 'stoneSkin': 5, 'haste': 10, 'slow': 10, 'bloodlust': 3, 'summonBoat': 2,
    'viewEarth': 3, 'viewAir': 3,
    # level 2
    'iceBolt': 20, 'lightningBolt': 25, 'fireWall': 10, 'quicksand': 4, 'scuttleBoat': 2, 'visions': 2,
    'disguise': 4, 'protectAir': 2, 'precision': 6, 'weakness': 4, 'disruptingRay': 5, 'fortune': 4,
    'blind': 12, 'removeObstacle': 4,
    # level 3
    'fireball': 16, 'frostRing': 8, 'landMine': 6, 'forceField': 4, 'earthquake': 6, 'destroyUndead': 4,
    'airShield': 6, 'protectEarth': 4, 'antiMagic': 8, 'mirth': 4, 'misfortune': 4, 'hypnotize': 10,
    'forgetfulness': 10, 'teleport': 8,
    # level 4
    'chainLightning': 10, 'inferno': 8, 'meteorShower': 10, 'fireShield': 5, 'resurrection': 8,
    'prayer': 10, 'sorrow': 5, 'slayer': 5, 'frenzy': 5, 'counterstrike': 5, 'berserk': 5, 'clone': 14,
    'waterWalk': 10, 'townPortal': 10,
    # level 5
    'fly': 10, 'dimensionDoor': 18, 'implosion': 12, 'magicMirror': 12, 'fireElemental': 10,
    'earthElemental': 12, 'waterElemental': 12, 'airElemental': 10,
}

TOWN_NAMES = [('Konohagakure', 'Конохагакуре'), ('Hidden Leaf', 'Скрытый Лист'), ('Tanzaku Town', 'Танзаку'),
              ('Fire Temple', 'Храм Огня'), ('Otafuku Town', 'Отафуку'), ('Valley of the End', 'Долина Завершения'),
              ('Naka River', 'Река Нака'), ('Forest of Death', 'Лес Смерти'), ('Shukuba Town', 'Шукуба'),
              ('Nakano Shrine', 'Храм Накано')]

faction = {F: {
    'name': 'Konohagakure',
    'description': '{Konohagakure}\n\nThe Village Hidden in the Leaves, in the Land of Fire. Shinobi and Sages fight side by side with ninja hounds, clan warriors, medics and the giant toads of Mount Myoboku. Balanced troops: every tier knows a clan technique.',
    'alignment': 'good',
    'nativeTerrain': 'grass',
    'boat': 'boatCastle',
    'creatureBackground': castle['creatureBackground'],
    'puzzleMap': castle['puzzleMap'],
    'town': {
        'mapObject': castle['town']['mapObject'],
        'icons': town_icons,
        'musicTheme': castle['town']['musicTheme'],
        'defaultTavern': 5,
        'tavernVideo': castle['town']['tavernVideo'],
        'guildBackground': castle['town']['guildBackground'],
        'townBackground': town_background,
        'guildWindow': rampart['town']['guildWindow'],
        'guildWindowPosition': rampart['town']['guildWindowPosition'],
        'guildSpellPositions': rampart['town']['guildSpellPositions'],
        'buildingsIcons': 'naruto/konohagakure/hallIcons',
        'hallBackground': castle['town']['hallBackground'],
        'hallSlots': [
            [['villageHall', 'townHall', 'cityHall', 'capitol'], ['fort', 'citadel', 'castle'], ['tavern'], ['blacksmith']],
            # The hall background (Castle's, borrowed) has empty frames painted in for Castle's
            # slots: rows must keep Castle's counts 4 / 3 / 2 / 4 / 3, or frames show as black
            # boxes. Row 3 is Training Ground 3 + Market Storehouse (Castle: Stables + horde).
            [['marketplace'], ['mageGuild1', 'mageGuild2', 'mageGuild3', 'mageGuild4', 'mageGuild5'], ['special1']],
            [['special2'], ['resourceSilo']],
            [['dwellingLvl1', 'dwellingUpLvl1'], ['dwellingLvl2', 'dwellingUpLvl2'], ['dwellingLvl3', 'dwellingUpLvl3'], ['dwellingLvl4', 'dwellingUpLvl4']],
            [['dwellingLvl5', 'dwellingUpLvl5'], ['dwellingLvl6', 'dwellingUpLvl6'], ['dwellingLvl7', 'dwellingUpLvl7']],
        ],
        'creatures': [['academyStudent', 'genin'], ['ninjaHound', 'ninkenPackLeader'], ['hyugaGuard', 'hyugaMainBranch'],
                      ['medicalNinja', 'seniorMedic'], ['uchihaPolice', 'sharinganMaster'], ['anbuOperative', 'anbuCaptain'],
                      ['toadWarrior', 'gamabunta']],
        'horde': [],
        'mageGuild': 5,
        'guildSpells': guild_spells,
        'moatAbility': castle['town']['moatAbility'],
        'names': [en for en, _ in TOWN_NAMES],
        'structures': structures,
        'buildings': buildings,
        'siege': siege,
    },
}}
FACTION_RU = {'name': 'Коноха',
              'description': '{Коноха}\n\nДеревня Скрытого Листа в Стране Огня. Шиноби и Мудрецы сражаются бок о бок с псами-ниндзя, воинами кланов, медиками и гигантскими жабами горы Мёбоку. Сбалансированные войска: каждый уровень владеет клановой техникой.'}

# ------------------------------------------------------------------ hero classes

classes = dict([
    hero_class(t, F, 'shinobi', 'Shinobi', 'Шиноби', 'might', 0, (2, 2, 1, 1), (40, 35, 12, 13), (30, 30, 20, 20),
               {'pathfinding': 5, 'archery': 6, 'logistics': 7, 'scouting': 6, 'diplomacy': 3, 'navigation': 2,
                'leadership': 7, 'wisdom': 3, 'mysticism': 2, 'luck': 4, 'ballistics': 5, 'eagleEye': 2,
                'necromancy': 0, 'estates': 3, 'fireMagic': 2, 'airMagic': 3, 'waterMagic': 2, 'earthMagic': 2,
                'scholar': 1, 'tactics': 8, 'artillery': 4, 'learning': 3, 'offence': 8, 'armorer': 6,
                'intelligence': 1, 'sorcery': 1, 'resistance': 4, 'firstAid': 3},
               {F: 6, 'inferno': 3, 'necropolis': 3}, 'zealot'),
    hero_class(t, F, 'sage', 'Sage', 'Мудрец', 'magic', 1, (1, 0, 2, 2), (20, 15, 30, 35), (20, 20, 30, 30),
               {'pathfinding': 2, 'archery': 1, 'logistics': 3, 'scouting': 3, 'diplomacy': 4, 'navigation': 2,
                'leadership': 3, 'wisdom': 8, 'mysticism': 5, 'luck': 3, 'ballistics': 1, 'eagleEye': 5,
                'necromancy': 0, 'estates': 3, 'fireMagic': 4, 'airMagic': 4, 'waterMagic': 5, 'earthMagic': 5,
                'scholar': 5, 'tactics': 2, 'artillery': 1, 'learning': 4, 'offence': 2, 'armorer': 2,
                'intelligence': 6, 'sorcery': 4, 'resistance': 2, 'firstAid': 5},
               {F: 6, 'inferno': 3, 'necropolis': 3}, 'zealot'),
])

# ------------------------------------------------------------------ heroes

S, H, M, U, T7 = 'academyStudent', 'ninjaHound', 'hyugaGuard', 'medicalNinja', 'toadWarrior'
STD = [(S, 10, 20), (H, 4, 7), (M, 2, 3)]
B, A, E = 'basic', 'advanced', 'expert'
creature_spec = lambda en, ru, what_en, what_ru: (
    (en, 'Creature bonus: ' + en,
     'Increases the speed of any %s by 1 and their Attack and Defense by 5%% for every level of the hero divided by the creature tier.' % what_en),
    (ru, 'Бонус существам: ' + ru,
     'Скорость существ (%s) +1, атака и защита +5%% за каждый уровень героя, делённый на уровень существа.' % what_ru))
grows = lambda per20: {'type': 'GROWS_WITH_LEVEL', 'valPer20': per20, 'stepSize': 1}

H_ = []
def add(hid, cls, female, name, ru_name, bio, ru_bio, spec, specialty, skills, army, portrait, icon, spells=None):
    H_.append(hero(t, hid, cls, female, name, ru_name, bio, ru_bio, spec[0], spec[1], specialty, skills, army,
                   portrait, icon, spells))

# --- Shinobi
add('narutoUzumaki', 'shinobi', False, 'Naruto Uzumaki', 'Наруто Узумаки',
    'A loud, stubborn ninja of Konoha who never goes back on his word. His Shadow Clones fill the battlefield, and he believes every genin can become Hokage.',
    'Шумный и упрямый ниндзя Конохи, который никогда не отступает от своих слов. Его теневые клоны заполняют поле боя, а сам он верит, что любой генин может стать Хокаге.',
    creature_spec('Genin', 'Генины', 'Academy Students or Genin', 'ученики Академии и генины'),
    {'creature': S}, [('offence', B), ('leadership', B)], [(S, 10, 20), (S, 10, 20), (H, 4, 7)], 4, 1, ['clone'])
add('sasukeUchiha', 'shinobi', False, 'Sasuke Uchiha', 'Саске Учиха',
    'The last heir of the Uchiha clan, cold and brilliant. His Sharingan reads every move before it is made.',
    'Последний наследник клана Учиха, холодный и блестящий. Его Шаринган читает каждое движение противника заранее.',
    creature_spec('Uchiha', 'Учиха', 'Uchiha Police or Sharingan Masters', 'полиция Учиха и мастера Шарингана'),
    {'creature': 'uchihaPolice'}, [('offence', B), ('tactics', B)], STD, 14, 44)
add('kakashiHatake', 'shinobi', False, 'Kakashi Hatake', 'Какаши Хатаке',
    'The Copy Ninja, said to know a thousand jutsu. Behind the mask and the orange book is one of Konoha\'s sharpest minds.',
    'Копирующий ниндзя, знающий, по слухам, тысячу техник. За маской и оранжевой книжкой скрывается один из самых острых умов Конохи.',
    (('Copy Ninja', 'Eagle Eye and copying', 'Increases the chance to learn spells cast in battle by 5% for every level, and allows copying spells one level higher than Eagle Eye allows.'),
     ('Копирующий ниндзя', 'Орлиный глаз и копирование', 'Шанс выучить заклинание, применённое в бою, +5% за каждый уровень; можно копировать заклинания на один уровень выше, чем позволяет Орлиный глаз.')),
    {'secondary': 'eagleEye', 'bonuses': {'copyNinja': {'type': 'LEARN_BATTLE_SPELL_LEVEL_LIMIT', 'val': 1}}},
    [('eagleEye', B), ('offence', B)], STD, 44, 13)
add('rockLee', 'shinobi', False, 'Rock Lee', 'Рок Ли',
    'A ninja who cannot use ninjutsu or genjutsu, and trains taijutsu until his fists speak for him.',
    'Ниндзя, не способный к ниндзюцу и гендзюцу, который тренирует тайдзюцу, пока за него не начинают говорить кулаки.',
    (('Offense', 'Secondary skill bonus: Offense', 'Increases the bonus of the Offense skill by 5% for every level.'),
     ('Нападение', 'Бонус навыку: Нападение', 'Эффект навыка «Нападение» +5% за каждый уровень героя.')),
    {'secondary': 'offence'}, [('offence', B), ('armorer', B)], STD, 86, 102)
add('mightGuy', 'shinobi', False, 'Might Guy', 'Майто Гай',
    'The Sublime Green Beast of Konoha. When he opens the Eight Gates, his whole army moves in a blur.',
    'Великолепный зелёный зверь Конохи. Когда он открывает Восемь врат, вся его армия движется как вихрь.',
    (('Eight Gates', 'Speed bonus', 'All creatures in his army get +1 speed, +2 from level 11 and +3 from level 21.'),
     ('Восемь врат', 'Бонус скорости', 'Все существа в его армии получают +1 к скорости, +2 с 11-го уровня и +3 с 21-го.')),
    {'bonuses': {'eightGates': {'type': 'STACKS_SPEED', 'updater': grows(2)}}},
    [('offence', B), ('logistics', B)], STD, 38, 144)
add('nejiHyuga', 'shinobi', False, 'Neji Hyuga', 'Неджи Хьюга',
    'A branch-family prodigy of the Hyuga clan whose Byakugan sees every chakra point on the field.',
    'Гений побочной ветви клана Хьюга, чей Бьякуган видит каждую точку чакры на поле боя.',
    creature_spec('Hyuga', 'Хьюга', 'Hyuga Guards or Hyuga Main Branch', 'стражи Хьюга и Хьюга главной ветви'),
    {'creature': M}, [('tactics', B), ('offence', B)], [(S, 10, 20), (M, 2, 3), (M, 2, 3)], 16, 12)
add('tenten', 'shinobi', True, 'Tenten', 'Тентен',
    'A weapons specialist who never misses. Her scrolls hold more blades than an armory.',
    'Мастер оружия, которая никогда не промахивается. В её свитках больше клинков, чем в оружейной.',
    (('Ballista', 'Ballista bonus', 'The Ballista gains +1 speed and +5% Attack and Defense for every 5 levels of the hero.'),
     ('Баллиста', 'Бонус баллисте', 'Баллиста получает +1 к скорости и +5% к атаке и защите за каждые 5 уровней героя.')),
    {'creature': 'ballista', 'creatureLevel': 5}, [('artillery', B), ('archery', B)],
    [(S, 10, 20), ('ballista', 1, 1), (M, 2, 3)], 42, 6)
add('kibaInuzuka', 'shinobi', False, 'Kiba Inuzuka', 'Киба Инузука',
    'A wild Inuzuka tracker who fights back to back with Akamaru and a pack of ninken.',
    'Неистовый следопыт клана Инузука, сражающийся спина к спине с Акамару и стаей нинкенов.',
    creature_spec('Ninja Hounds', 'Псы-ниндзя', 'Ninja Hounds or Ninken Pack Leaders', 'псы-ниндзя и вожаки нинкенов'),
    {'creature': H}, [('scouting', B), ('offence', B)], [(S, 10, 20), (H, 4, 7), (H, 4, 7)], 112, 48)
add('hinataHyuga', 'shinobi', True, 'Hinata Hyuga', 'Хината Хьюга',
    'The gentle heiress of the Hyuga, far stronger than she believes. Her Protective Eight Trigrams guard everyone behind her.',
    'Мягкая наследница клана Хьюга, куда сильнее, чем сама думает. Её Защитные восемь триграмм прикрывают всех за её спиной.',
    (('Protective Palms', 'Hyuga defense bonus', 'Hyuga Guards and Hyuga Main Branch get +1 speed and one extra retaliation, and their Defense grows by 1 for every 3–4 levels of the hero (+6 at level 20).'),
     ('Защитные ладони', 'Бонус защите Хьюга', 'Стражи Хьюга и Хьюга главной ветви получают +1 к скорости и дополнительный ответный удар, а их защита растёт на 1 каждые 3–4 уровня героя (+6 на 20-м уровне).')),
    {'base': {'limiters': [{'type': 'CREATURE_TYPE_LIMITER', 'creature': M, 'includeUpgrades': True}]},
     'bonuses': {'retaliation': {'type': 'ADDITIONAL_RETALIATION', 'val': 1},
                 'speed': {'type': 'STACKS_SPEED', 'val': 1},
                 'defence': {'type': 'PRIMARY_SKILL', 'subtype': 'primarySkill.defence', 'updater': grows(6)}}},
    [('armorer', B), ('leadership', B)], [(S, 10, 20), (M, 2, 3), (M, 2, 3)], 80, 16)
add('chojiAkimichi', 'shinobi', False, 'Choji Akimichi', 'Чоджи Акимичи',
    'A big-hearted Akimichi who fights best on a full stomach. Wherever he goes, food and gold follow.',
    'Добродушный Акимичи, который лучше всего сражается на сытый желудок. Где он, там еда и золото.',
    (('Gold', '+350 gold per day', 'Adds 350 gold to your treasury every day.'),
     ('Золото', '+350 золота в день', 'Ежедневно приносит в казну 350 золота.')),
    {'bonuses': {'gold': {'type': 'GENERATE_RESOURCE', 'subtype': 'resource.gold', 'val': 350}}},
    [('armorer', B), ('estates', B)], STD, 22, 15)
add('shinoAburame', 'shinobi', False, 'Shino Aburame', 'Шино Абураме',
    'A quiet Aburame whose body is a hive of chakra-eating insects. By the time the enemy notices the swarm, it is too late.',
    'Молчаливый Абураме, чьё тело — улей насекомых, пожирающих чакру. Когда враг замечает рой, уже слишком поздно.',
    (('Insect Swarm', 'Opening Weakness', 'Each battle opens with expert Weakness on all enemies. It lasts 1 round, 2 from level 6, 3 from level 11 and 4 from level 16.'),
     ('Рой насекомых', 'Слабость в начале боя', 'Каждый бой начинается с Ослабления (эксперт) на всех врагов. Длится 1 раунд, 2 с 6-го уровня, 3 с 11-го и 4 с 16-го.')),
    {'bonuses': {'insects': {'type': 'OPENING_BATTLE_SPELL', 'subtype': 'spell.weakness', 'addInfo': 3, 'updater': grows(4)}}},
    [('scouting', B), ('resistance', B)], STD, 12, 10)
add('asumaSarutobi', 'shinobi', False, 'Asuma Sarutobi', 'Асума Сарутоби',
    'The Third Hokage\'s son, a guardian of the Fire Temple, who channels wind chakra through his trench knives.',
    'Сын Третьего Хокаге, бывший страж Храма Огня, пропускающий чакру ветра через свои кастеты-клинки.',
    (('Wind Blades', 'Armor-piercing attacks', 'His troops ignore 1.25% of the enemy\'s Defense for every level (25% at level 20).'),
     ('Клинки ветра', 'Пробивающие атаки', 'Его войска игнорируют 1,25% защиты врага за каждый уровень (25% на 20-м уровне).')),
    {'bonuses': {'windBlades': {'type': 'ENEMY_DEFENCE_REDUCTION', 'updater': grows(25)}}},
    [('offence', B), ('leadership', B)], STD, 17, 141)

# --- Sages
add('jiraiya', 'sage', False, 'Jiraiya', 'Джирайя',
    'One of the Legendary Sannin, toad sage of Mount Myoboku and a famously bad influence. The toads answer his summons.',
    'Один из Легендарных Саннинов, жабий отшельник горы Мёбоку и известный дурной пример. Жабы откликаются на его призыв.',
    creature_spec('Toads', 'Жабы', 'Toad Warriors or Gamabunta', 'жабы-воины и Гамабунта'),
    {'creature': T7}, [('wisdom', B), ('leadership', B)], STD, 25, 149, ['haste'])
add('tsunade', 'sage', True, 'Tsunade', 'Цунаде',
    'Legendary Sannin and the greatest medical ninja alive. Her strength can split the earth; her hands can mend almost anything.',
    'Легендарный Саннин и величайший ниндзя-медик. Её сила раскалывает землю, а руки способны залечить почти что угодно.',
    creature_spec('Medics', 'Медики', 'Medical Ninja or Senior Medics', 'ниндзя-медики и старшие медики'),
    {'creature': U}, [('firstAid', B), ('wisdom', B)], STD, 29, 21, ['cure'])
add('sakuraHaruno', 'sage', True, 'Sakura Haruno', 'Сакура Харуно',
    'Tsunade\'s apprentice, with precise chakra control and a punch to match. No wounded ally is left behind.',
    'Ученица Цунаде с точнейшим контролем чакры и не менее точным ударом. Ни один раненый союзник не остаётся без помощи.',
    (('First Aid', 'Secondary skill bonus: First Aid', 'Increases the healing of the First Aid skill by 5% for every level.'),
     ('Первая помощь', 'Бонус навыку: Первая помощь', 'Лечение навыка «Первая помощь» +5% за каждый уровень героя.')),
    {'secondary': 'firstAid'}, [('firstAid', B), ('offence', B)], [(S, 10, 20), ('firstAidTent', 1, 1), (M, 2, 3)],
    110, 8, ['cure'])
add('hiruzenSarutobi', 'sage', False, 'Hiruzen Sarutobi', 'Хирузен Сарутоби',
    'The Third Hokage, called the Professor, who is said to know every jutsu of the Leaf.',
    'Третий Хокаге, прозванный Профессором. Говорят, он знает все техники Листа.',
    (('The Professor', 'Knows every level 1 spell', 'Can cast every level 1 spell, as if it were in his spellbook.'),
     ('Профессор', 'Знает все заклинания 1 уровня', 'Может применять любое заклинание 1-го уровня, как если бы оно было в его книге.')),
    {'bonuses': {'professor': {'type': 'SPELLS_OF_LEVEL', 'subtype': 'spellLevel1'}}},
    [('wisdom', A)], STD, 40, 26, ['magicArrow'])
add('minatoNamikaze', 'sage', False, 'Minato Namikaze', 'Минато Намиказе',
    'The Fourth Hokage, the Yellow Flash of the Leaf. With his Flying Thunder God, whole armies move before the enemy can blink.',
    'Четвёртый Хокаге, Жёлтая Молния Конохи. С его Летящим Богом Грома целые армии перемещаются быстрее, чем враг успеет моргнуть.',
    (('Haste', 'Spell bonus: Haste', 'His Haste gives extra speed by creature tier: +3 for tiers 1–2, +2 for tiers 3–4, +1 for tiers 5–6.'),
     ('Ускорение', 'Бонус заклинанию: Ускорение', 'Его Ускорение даёт дополнительную скорость по уровню существа: +3 для 1–2, +2 для 3–4, +1 для 5–6.')),
    {'bonuses': {'haste': {'type': 'SPECIAL_PECULIAR_ENCHANT', 'subtype': 'spell.haste', 'addInfo': 0}}},
    [('logistics', B), ('airMagic', B)], STD, 118, 46, ['haste'])
add('itachiUchiha', 'sage', False, 'Itachi Uchiha', 'Итачи Учиха',
    'A genius of the Uchiha who carries a terrible secret. One look into his Mangekyo Sharingan and the enemy is lost in Tsukuyomi.',
    'Гений клана Учиха, хранящий страшную тайну. Один взгляд в его Мангекё Шаринган — и враг теряется в Цукуёми.',
    (('Tsukuyomi', 'Spell bonus: Blind', 'His Blind lasts 1 round longer for every 5 levels (rounded up).'),
     ('Цукуёми', 'Бонус заклинанию: Слепота', 'Его Слепота длится на 1 раунд дольше за каждые 5 уровней (с округлением вверх).')),
    {'bonuses': {'tsukuyomi': {'type': 'SPELL_DURATION', 'subtype': 'spell.blind', 'updater': grows(4)}}},
    [('wisdom', B), ('fireMagic', B)], STD, 72, 57, ['blind'])
add('shikamaruNara', 'sage', False, 'Shikamaru Nara', 'Шикамару Нара',
    'A lazy genius of the Nara clan who plans twenty moves ahead. His shadow holds the enemy in place.',
    'Ленивый гений клана Нара, просчитывающий ход на двадцать шагов вперёд. Его тень удерживает врага на месте.',
    (('Shadow Possession', 'Spell bonus: Slow', 'His Slow reduces the target\'s speed by an extra 15%.'),
     ('Техника захвата тенью', 'Бонус заклинанию: Замедление', 'Его Замедление дополнительно снижает скорость цели на 15%.')),
    {'bonuses': {'shadow': {'type': 'SPECIAL_ADD_VALUE_ENCHANT', 'subtype': 'spell.slow', 'addInfo': -15}}},
    [('tactics', B), ('wisdom', B)], STD, 21, 72, ['slow'])
add('kurenaiYuhi', 'sage', True, 'Kurenai Yuhi', 'Куренай Юхи',
    'Konoha\'s mistress of genjutsu. Her illusions make enemy archers forget which end of the bow to hold.',
    'Мастер гендзюцу Конохи. От её иллюзий вражеские стрелки забывают, с какой стороны держать лук.',
    (('Genjutsu', 'Spell bonus: Forgetfulness', 'Her Forgetfulness lasts 1 round longer for every 5 levels (rounded up).'),
     ('Гендзюцу', 'Бонус заклинанию: Забывчивость', 'Её Забывчивость длится на 1 раунд дольше за каждые 5 уровней (с округлением вверх).')),
    {'bonuses': {'genjutsu': {'type': 'SPELL_DURATION', 'subtype': 'spell.forgetfulness', 'updater': grows(4)}}},
    [('wisdom', B), ('intelligence', B)], STD, 94, 121, ['forgetfulness'])
add('inoYamanaka', 'sage', True, 'Ino Yamanaka', 'Ино Яманака',
    'The Yamanaka heiress, who can slip her mind into an enemy\'s body and turn it against its own side.',
    'Наследница клана Яманака, способная переселить своё сознание в тело врага и обратить его против своих.',
    (('Mind Transfer', 'Spell bonus: Hypnotize', 'Her Hypnotize lasts 1 round longer for every 5 levels (rounded up).'),
     ('Техника переноса разума', 'Бонус заклинанию: Гипноз', 'Её Гипноз длится на 1 раунд дольше за каждые 5 уровней (с округлением вверх).')),
    {'bonuses': {'mindTransfer': {'type': 'SPELL_DURATION', 'subtype': 'spell.hypnotize', 'updater': grows(4)}}},
    [('wisdom', B), ('scholar', B)], STD, 34, 40, ['hypnotize'])
add('yamato', 'sage', False, 'Yamato', 'Ямато',
    'A former ANBU captain and the only living user of Wood Release besides the First Hokage. He raises walls and houses from nothing.',
    'Бывший капитан АНБУ и единственный, кроме Первого Хокаге, владелец стихии Дерева. Он возводит стены и дома из ничего.',
    (('Wood Release', 'Earth magic bonus', 'Earth spells cast by him are 2% more effective for every level.'),
     ('Стихия Дерева', 'Бонус магии Земли', 'Заклинания магии Земли эффективнее на 2% за каждый уровень героя.')),
    {'bonuses': {'woodRelease': {'type': 'SPELL_DAMAGE', 'subtype': 'spellSchool.earth', 'val': 2, 'updater': 'TIMES_HERO_LEVEL'}}},
    [('earthMagic', B), ('wisdom', B)], STD, 63, 19, ['stoneSkin'])
add('hashiramaSenju', 'sage', False, 'Hashirama Senju', 'Хаширама Сенджу',
    'The First Hokage and founder of Konoha, the God of Shinobi. Forests rise where he walks, and his cells heal any wound.',
    'Первый Хокаге и основатель Конохи, Бог шиноби. Там, где он проходит, вырастают леса, а его клетки залечивают любые раны.',
    (('Wood Release Cells', 'Regeneration', 'All creatures in his army regenerate 2 health per hero level at the start of each round.'),
     ('Клетки Хаширамы', 'Регенерация', 'Все существа в его армии в начале каждого раунда восстанавливают по 2 здоровья за каждый уровень героя.')),
    {'bonuses': {'regeneration': {'type': 'HP_REGENERATION', 'val': 2, 'updater': 'TIMES_HERO_LEVEL'}}},
    [('earthMagic', B), ('leadership', B)], STD, 104, 25, ['stoneSkin'])
add('tobiramaSenju', 'sage', False, 'Tobirama Senju', 'Тобирама Сенджу',
    'The Second Hokage, a stern master of Water Release who founded the Academy and the ANBU.',
    'Второй Хокаге, суровый мастер стихии Воды, основавший Академию и АНБУ.',
    (('Water Release', 'Water magic bonus', 'Water spells cast by him are 2% more effective for every level.'),
     ('Стихия Воды', 'Бонус магии Воды', 'Заклинания магии Воды эффективнее на 2% за каждый уровень героя.')),
    {'bonuses': {'waterRelease': {'type': 'SPELL_DAMAGE', 'subtype': 'spellSchool.water', 'val': 2, 'updater': 'TIMES_HERO_LEVEL'}}},
    [('waterMagic', B), ('wisdom', B)], STD, 10, 131, ['dispel'])
add('orochimaru', 'sage', False, 'Orochimaru', 'Орочимару',
    'A Legendary Sannin who chose forbidden jutsu and immortality over his village. Even the dead answer to him.',
    'Легендарный Саннин, выбравший запретные техники и бессмертие вместо своей деревни. Даже мёртвые подчиняются ему.',
    (('Impure World Reincarnation', 'Spell bonus: Resurrection', 'His Resurrection restores 3% more health for every level.'),
     ('Техника воскрешения', 'Бонус заклинанию: Воскрешение', 'Его Воскрешение восстанавливает на 3% больше здоровья за каждый уровень.')),
    {'bonuses': {'edoTensei': {'type': 'SPECIFIC_SPELL_DAMAGE', 'subtype': 'spell.resurrection', 'val': 3, 'updater': 'TIMES_HERO_LEVEL'}}},
    [('wisdom', B), ('mysticism', B)], STD, 73, 88, ['curse'])
heroes = dict(H_)

# ------------------------------------------------------------------ adventure-map dwellings

# Borrowed pictures: the original dwelling of each borrowed creature sprite.
dwellings = {'core:creatureGeneratorCommon': {'types': dict([
    dwelling_object(t, 'ninjaAcademy', 'Ninja Academy', 'Академия ниндзя', S, 'AVGpike0.def', 'LOOPPIKE'),
    dwelling_object(t, 'inuzukaKennels', 'Inuzuka Kennels', 'Псарни Инузука', H, 'AVGhell0.def', 'LOOPDOG'),
    dwelling_object(t, 'hyugaCompound', 'Hyuga Compound', 'Поместье Хьюга', M, 'AVGmonk0.def', 'LOOPMONK'),
    dwelling_object(t, 'medicalCorps', 'Medical Corps', 'Медицинский корпус', U, 'AVGelf0.def', 'LOOPELF'),
    dwelling_object(t, 'uchihaDistrict', 'Uchiha District', 'Квартал Учиха', 'uchihaPolice', 'AVGmage0.def', 'LOOPMAGI'),
    dwelling_object(t, 'anbuHeadquarters', 'ANBU Headquarters', 'Штаб АНБУ', 'anbuOperative', 'AVGvamp0.def', 'LOOPDEAD'),
    dwelling_object(t, 'mountMyobokuGate', 'Mount Myoboku Gate', 'Врата горы Мёбоку', T7, 'AVGbhmt0.def', 'LOOPBEHE'),
])}}

# ------------------------------------------------------------------ output

D = 'Content/config/%s/' % F
files = {
    'factions': [write_json(D + 'faction.json', faction)],
    'creatures': [write_json(D + 'creatures.json', creatures)],
    'heroClasses': [write_json(D + 'heroClasses.json', classes)],
    'heroes': [write_json(D + 'heroes.json', heroes)],
    'objects': [write_json(D + 'dwellings.json', dwellings)],
}
fk = 'faction.%s.%s.' % (MOD, F)
t.add(fk + 'name', FACTION_RU['name'])
t.add(fk + 'description', FACTION_RU['description'])
for i, (_, ru) in enumerate(TOWN_NAMES):
    t.add(fk + 'randomName.%d' % i, ru)   # key formats verified with --translate-mod
for bid, (ru_name, ru_desc) in BUILDING_RU.items():
    bk = 'building.%s.%s.%s.' % (MOD, F, bid)
    t.add(bk + 'name', ru_name)
    t.add(bk + 'description', ru_desc)
tk = 'building.%s.%s.special2.' % (MOD, F)
t.add(tk + 'onSelect', TRAIN_RU['onSelectMessage'])
t.add(tk + 'onVisited', TRAIN_RU['onVisitedMessage'])
for i, (_, msg) in enumerate(TRAIN_RU['rewards']):
    t.add(tk + 'rewards.%d' % i, msg)
ru_file = write_json('Content/config/translations/russian-%s.json' % F, dict(sorted(t.ru.items())))

# register the files in mod.json
import json
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
print('konohagakure: %d creatures, %d classes, %d heroes, %d buildings, %d Russian strings' %
      (len(creatures), len(classes), len(heroes), len(buildings), len(t.ru)))
