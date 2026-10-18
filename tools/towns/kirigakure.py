"""Kirigakure: generates the town's JSON from the spec in the vault note
~/O/Projects/HoMM3-Naruto/Plans/Naruto-Mod-Kirigakure.md ("Details").
Run: python3 tools/towns/kirigakure.py   (then tools/check.sh)"""
import copy, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from townkit import *

F = 'kirigakure'
t = Texts()
fortress = load(VCMI_CONFIG + '/factions/fortress.json')['fortress']
dungeon = load(VCMI_CONFIG + '/factions/dungeon.json')['dungeon']

def stats(cost, hp, speed, att, dfn, dmg, growth, fight, ai, amount):
    return dict(cost=cost, hp=hp, speed=speed, attack=att, defense=dfn, dmg=dmg,
                growth=growth, fight=fight, ai=ai, amount=amount)

# ------------------------------------------------------------------ creatures

shooter = {'shooter': {'type': 'SHOOTER'}}
ruthless = {'ruthless': {'type': 'DOUBLE_DAMAGE_CHANCE', 'val': 20}}
hydrification = lambda v: {'hydrification': {'type': 'GENERAL_DAMAGE_REDUCTION', 'subtype': 'damageTypeAll', 'val': v}}
frenzy = {'frenzy': {'type': 'FEROCITY', 'val': 1}}
freeze = lambda chance: {'freeze': {'type': 'SPELL_AFTER_ATTACK', 'subtype': 'spell.stoneGaze', 'val': chance, 'addInfo': [1, 0]}}
silent_killing = {'silentKilling': {'type': 'FIRST_STRIKE', 'subtype': 'damageTypeMelee'}}
dragon = {'flies': {'type': 'FLYING'}, 'waterBreath': {'type': 'TWO_HEX_ATTACK_BREATH'}}

creatures = dict([
    creature(t, F, 'mistGenin', 1, ('Mist Genin', 'Mist Genin'), ('Генин Тумана', 'Генины Тумана'),
             'troglodyte', 'Troglodyte', stats({'gold': 50}, 7, 6, 5, 2, (1, 3), 15, 80, 75, (20, 50)),
             upgrades=['bloodyMistGraduate']),
    creature(t, F, 'bloodyMistGraduate', 1, ('Bloody Mist Graduate', 'Bloody Mist Graduates'),
             ('Выпускник Кровавого Тумана', 'Выпускники Кровавого Тумана'),
             'infernalTroglodyte', 'Infernal Troglodyte', stats({'gold': 70}, 8, 7, 6, 3, (2, 3), 15, 105, 110, (20, 50)),
             abilities=dict(ruthless)),
    creature(t, F, 'hunterNin', 2, ('Hunter-nin', 'Hunter-nin'), ('Охотник-ниндзя', 'Охотники-ниндзя'),
             'lizardman', 'Primitive Lizardman', stats({'gold': 110}, 9, 7, 6, 3, (2, 4), 9, 130, 150, (16, 30)),
             upgrades=['trackerHunterNin'], shots=10, projectile='senbon', abilities=dict(shooter)),
    creature(t, F, 'trackerHunterNin', 2, ('Tracker Hunter-nin', 'Tracker Hunter-nin'), ('Охотник-следопыт', 'Охотники-следопыты'),
             'lizardWarrior', 'Advanced Lizardman', stats({'gold': 150}, 10, 9, 7, 4, (2, 4), 9, 170, 220, (16, 30)),
             shots=14, projectile='senbon', abilities=dict(shooter, noDistancePenalty={'type': 'NO_DISTANCE_PENALTY'},
                                      senbon={'type': 'SPELL_AFTER_ATTACK', 'subtype': 'spell.slow', 'val': 20, 'addInfo': [1, 0]})),
    creature(t, F, 'hozukiBrawler', 3, ('Hozuki Brawler', 'Hozuki Brawlers'), ('Боец Хозуки', 'Бойцы Хозуки'),
             'waterElemental', 'Water Elemental', stats({'gold': 190}, 22, 6, 8, 6, (3, 5), 7, 280, 300, (12, 25)),
             upgrades=['hozukiHydrifier'], abilities=hydrification(20), double_wide=False),
    creature(t, F, 'hozukiHydrifier', 3, ('Hozuki Hydrifier', 'Hozuki Hydrifiers'), ('Гидрификатор Хозуки', 'Гидрификаторы Хозуки'),
             'iceElemental', 'Ice Elemental', stats({'gold': 240}, 24, 8, 9, 7, (3, 6), 7, 350, 400, (12, 25)),
             abilities=hydrification(35), double_wide=False),
    creature(t, F, 'summonedShark', 4, ('Summoned Shark', 'Summoned Sharks'), ('Призванная акула', 'Призванные акулы'),
             'basilisk', 'Basilisk', stats({'gold': 320}, 38, 7, 12, 7, (6, 10), 4, 420, 460, (10, 20)),
             upgrades=['greatShark'], abilities=dict(frenzy), double_wide=True),
    creature(t, F, 'greatShark', 4, ('Great Shark', 'Great Sharks'), ('Великая акула', 'Великие акулы'),
             'greaterBasilisk', 'Greater Basilisk', stats({'gold': 420}, 42, 9, 14, 8, (7, 11), 4, 520, 620, (10, 20)),
             abilities=dict(frenzy), double_wide=True),
    creature(t, F, 'yukiClanAdept', 5, ('Yuki Clan Adept', 'Yuki Clan Adepts'), ('Адепт клана Юки', 'Адепты клана Юки'),
             'medusa', 'Medusa', stats({'gold': 480}, 30, 6, 12, 8, (8, 12), 3, 560, 640, (8, 16)),
             upgrades=['iceMirrorMaster'], shots=8, projectile='water-bullet', abilities=dict(shooter, **freeze(15)), double_wide=False),
    creature(t, F, 'iceMirrorMaster', 5, ('Ice Mirror Master', 'Ice Mirror Masters'), ('Мастер ледяных зеркал', 'Мастера ледяных зеркал'),
             'medusaQueen', 'Medusa Queen', stats({'gold': 560}, 32, 8, 13, 9, (9, 13), 3, 640, 800, (8, 16)),
             shots=12, projectile='ice-senbon', abilities=dict(shooter, noMeleePenalty={'type': 'NO_MELEE_PENALTY'}, **freeze(25)), double_wide=False),
    creature(t, F, 'mistSwordsman', 6, ('Mist Swordsman', 'Mist Swordsmen'), ('Мечник Тумана', 'Мечники Тумана'),
             'swordsman', 'Swordsman', stats({'gold': 1050}, 80, 8, 18, 12, (16, 22), 2, 1400, 1600, (4, 10)),
             upgrades=['swordsmanOfTheSeven'], abilities=dict(silent_killing)),
    creature(t, F, 'swordsmanOfTheSeven', 6, ('Swordsman of the Seven', 'Swordsmen of the Seven'), ('Мечник Семи', 'Мечники Семи'),
             'crusader', 'Crusader', stats({'gold': 1300}, 90, 10, 20, 13, (18, 26), 2, 1800, 2150, (4, 10)),
             abilities=dict(silent_killing, deathBlow={'type': 'DOUBLE_DAMAGE_CHANCE', 'val': 20})),
    creature(t, F, 'waterDragon', 7, ('Water Dragon', 'Water Dragons'), ('Водный дракон', 'Водные драконы'),
             'greenDragon', 'Green Dragon', stats({'gold': 2600, 'mercury': 1}, 200, 10, 20, 18, (35, 50), 1, 3600, 4500, (1, 4)),
             upgrades=['greatWaterDragon'], abilities=dict(dragon), double_wide=True),
    creature(t, F, 'greatWaterDragon', 7, ('Great Water Dragon', 'Great Water Dragons'), ('Великий водный дракон', 'Великие водные драконы'),
             'azureDragon', 'Azure Dragon', stats({'gold': 4500, 'mercury': 2}, 300, 14, 26, 24, (45, 55), 1, 6300, 8400, (1, 4)),
             abilities=dict(dragon, waterImmunity={'type': 'SPELL_SCHOOL_IMMUNITY', 'subtype': 'spellSchool.water'}),
             double_wide=True),
])
for c in creatures.values():      # Ice Elemental graphics come with ranged parts we don't use
    if 'shots' not in c:
        c['graphics'].pop('missile', None)

# ------------------------------------------------------------------ buildings

B = {}
B.update(hall_chain(['Mizukage Office', 'Mizukage Chambers', 'Mizukage Tower', 'Mizukage Residence'],
                    ['Кабинет Мизукаге', 'Палаты Мизукаге', 'Башня Мизукаге', 'Резиденция Мизукаге'],
                    'your village', 'деревне'))
B.update(fort_chain(['Mist Wall', 'Fortified Mist Wall', 'Hidden Mist Citadel'],
                    ['Стена Тумана', 'Укреплённая стена', 'Цитадель Тумана']))
B.update(guild_chain('Mist Archive', 'Архив Тумана'))
B['tavern'] = building('Harbor Tavern', 'Портовая таверна', 'Sailors and mercenaries drink by the harbor: hire heroes, hear rumors and visit the Thieves\' Guild. Defenders fight with +1 morale.',
                       'У гавани пьют моряки и наёмники: наём героев, слухи и гильдия воров. Защитники города получают +1 к боевому духу.',
                       {'gold': 500, 'wood': 5})
B['blacksmith'] = building('Swordsmith of the Seven', 'Кузница Семи мечей', 'The swordsmith sells Ballistas to your armies.',
                           'Кузнец продаёт вашим армиям баллисты.', {'gold': 1000, 'wood': 5}, warMachine='ballista')
B['marketplace'] = building('Fish Market', 'Рыбный рынок', 'Trade resources here; the more markets you own, the better the rates.',
                            'Здесь можно обменивать ресурсы; чем больше у вас рынков, тем выгоднее курс.', {'gold': 500, 'wood': 5})
B['resourceSilo'] = building('Harbor Storehouse', 'Портовый склад', 'The Harbor Storehouse adds 1 mercury to your stock every day.',
                             'Портовый склад ежедневно приносит 1 ртуть.', {'gold': 5000, 'ore': 5}, produce={'mercury': 1})
B['shipyard'] = building('Kirigakure Docks', 'Доки Кири', 'The docks build boats for your heroes.',
                         'В доках строят лодки для ваших героев.', {'gold': 2000, 'wood': 20})
B['ship'] = building('Kirigakure Docks', 'Доки Кири', 'The docks build boats for your heroes.',
                     'В доках строят лодки для ваших героев.')
B['special1'] = building('Hidden Mist', 'Скрывающий туман', 'In a siege, defenders take 30% less damage from shooters.',
                         'При осаде защитники получают на 30% меньше урона от стрелков.',
                         {'gold': 2000, 'mercury': 5}, requires=['fort'],
                         bonuses=[{'type': 'GENERAL_DAMAGE_REDUCTION', 'subtype': 'damageTypeRanged', 'val': 30}])
B['special2'] = building('Bloody Mist Arena', 'Арена Кровавого Тумана',
                         'Click it with a hero in town: each hero may fight here once for +1 Attack and +1 Defense.',
                         'Щёлкните по ней, когда герой в городе: каждый герой может один раз сразиться здесь и получить +1 к атаке и +1 к защите.',
                         {'gold': 1000, 'ore': 5}, requires=['dwellingLvl1'],
                         # visited on click only, like Konoha's Training Ground (see the note there)
                         manualHeroVisit=True,
                         configuration={'visitMode': 'hero',
                                        'onVisitedMessage': 'You have already fought in the arena.',
                                        'rewards': [{'message': 'Survivors of the Bloody Mist fight harder: +1 Attack and +1 Defense.',
                                                     'primary': {'attack': 1, 'defence': 1}}]})
B['grail'] = building('Shrine of the Seven Swords', 'Святилище Семи мечей',
                      'The swords of the Seven rest here: +5000 gold per day, +50% creature growth and +2 Attack for all your heroes.',
                      'Здесь покоятся мечи Семерых: +5000 золота в день, +50% к приросту существ и +2 к атаке всех ваших героев.',
                      bonuses=[{'type': 'PRIMARY_SKILL', 'subtype': 'primarySkill.attack', 'val': 2, 'propagator': 'PLAYER'}])
R = {'mercury': 2, 'sulfur': 2, 'crystal': 2, 'gems': 2}
R10 = {'mercury': 10, 'sulfur': 10, 'crystal': 10, 'gems': 10}
B.update(dwelling_pair(1, 'Mist Academy', 'Академия Тумана', 'Mist Genin', 'генины Тумана',
                       'Bloody Mist Graduates', 'выпускники Кровавого Тумана', {'gold': 500, 'ore': 10}, {'gold': 1000, 'ore': 5}, ['fort']))
B.update(dwelling_pair(2, 'Hunter-nin Division', 'Отдел охотников', 'Hunter-nin', 'охотники-ниндзя',
                       'Tracker Hunter-nin', 'охотники-следопыты', {'gold': 1000, 'wood': 5, 'ore': 5},
                       {'gold': 1000, 'wood': 5, 'ore': 5}, ['dwellingLvl1']))
B.update(dwelling_pair(3, 'Hozuki Water Pools', 'Водоёмы Хозуки', 'Hozuki Brawlers', 'бойцы Хозуки',
                       'Hozuki Hydrifiers', 'гидрификаторы Хозуки', {'gold': 1000, 'ore': 5},
                       {'gold': 1000, 'ore': 5, 'mercury': 2}, ['dwellingLvl1']))
B.update(dwelling_pair(4, 'Shark Reef', 'Акулий риф', 'Summoned Sharks', 'призванные акулы', 'Great Sharks', 'великие акулы',
                       {'gold': 2000, 'wood': 5, 'ore': 5}, {'gold': 2000, 'ore': 5, 'mercury': 5}, ['dwellingLvl3']))
B.update(dwelling_pair(5, 'Yuki Clan Ice Hall', 'Ледяной зал Юки', 'Yuki Clan Adepts', 'адепты клана Юки',
                       'Ice Mirror Masters', 'мастера ледяных зеркал', dict({'gold': 3000, 'wood': 5, 'ore': 5}, **R),
                       dict({'gold': 1000}, **R), ['allOf', ['dwellingLvl2'], ['mageGuild1']]))
B.update(dwelling_pair(6, 'Hall of the Seven Swordsmen', 'Зал Семи мечников', 'Mist Swordsmen', 'мечники Тумана',
                       'Swordsmen of the Seven', 'мечники Семи', {'gold': 5000, 'wood': 10, 'ore': 10}, {'gold': 3000, 'ore': 10},
                       ['allOf', ['dwellingLvl4'], ['blacksmith']]))
B.update(dwelling_pair(7, 'Water Dragon Lake', 'Озеро водного дракона', 'Water Dragons', 'водные драконы',
                       'Great Water Dragons', 'великие водные драконы', dict({'gold': 20000}, **R10), dict({'gold': 20000}, **R10),
                       ['allOf', ['dwellingLvl6'], ['mageGuild2']]))
BUILDING_RU = {k: (v[1], v[2]) for k, v in B.items()}
buildings = {k: v[0] for k, v in B.items()}
buildings['ship']['cost'] = None      # the boat itself: no building cost, as in the original towns

screen = town_screen(F)
assert screen, 'run tools/townscreen.py kirigakure first'
structures = copy.deepcopy(screen['structures'])
structures['ship'] = dict(structures['shipyard'], hidden=True)   # no separate boat picture yet

siege = copy.deepcopy(fortress['town']['siege'])
siege['shooter'] = 'hunterNin'
siege['towerIconLarge'] = creatures['hunterNin']['graphics']['iconLarge']
siege['towerIconSmall'] = creatures['hunterNin']['graphics']['iconSmall']

guild_spells = {
    'magicArrow': 30, 'shield': 6, 'protectFire': 6, 'protectWater': 3, 'dispel': 12, 'cure': 12, 'bless': 10,
    'stoneSkin': 4, 'haste': 8, 'slow': 10, 'bloodlust': 2, 'summonBoat': 8, 'viewEarth': 3, 'viewAir': 3,
    'iceBolt': 30, 'lightningBolt': 10, 'fireWall': 2, 'quicksand': 4, 'scuttleBoat': 6, 'visions': 3,
    'disguise': 6, 'protectAir': 2, 'precision': 4, 'weakness': 10, 'disruptingRay': 5, 'fortune': 4,
    'blind': 12, 'removeObstacle': 8,
    'fireball': 3, 'frostRing': 16, 'landMine': 4, 'forceField': 5, 'earthquake': 3, 'destroyUndead': 4,
    'airShield': 5, 'protectEarth': 3, 'antiMagic': 6, 'mirth': 4, 'misfortune': 6, 'hypnotize': 12,
    'forgetfulness': 14, 'teleport': 12,
    'chainLightning': 6, 'inferno': 3, 'meteorShower': 4, 'fireShield': 2, 'resurrection': 6, 'prayer': 10,
    'sorrow': 6, 'slayer': 5, 'frenzy': 6, 'counterstrike': 5, 'berserk': 10, 'clone': 14, 'waterWalk': 12,
    'townPortal': 10,
    'fly': 10, 'dimensionDoor': 16, 'implosion': 8, 'magicMirror': 12, 'fireElemental': 2,
    'earthElemental': 4, 'waterElemental': 18, 'airElemental': 8,
}

TOWN_NAMES = [('Kirigakure', 'Киригакуре'), ('Hidden Mist', 'Скрытый Туман'), ('Bloody Mist', 'Кровавый Туман'),
              ('Water Country Port', 'Порт Страны Воды'), ('Misty Isles', 'Туманные острова'), ('Lake of Mirrors', 'Озеро зеркал'),
              ('Shark Bay', 'Акулья бухта'), ('Seven Swords Harbor', 'Гавань Семи мечей'), ('Mizukage Rock', 'Скала Мизукаге'),
              ('Silent Shore', 'Безмолвный берег')]

faction = {F: {
    'name': 'Kirigakure',
    'description': '{Kirigakure}\n\nThe Village Hidden in the Mist, on the islands of the Land of Water. Swordsmen and Mist Sages lead assassins in the mist: fast, deadly and fragile troops, sharks, ice and water dragons.',
    'alignment': 'evil',
    'nativeTerrain': 'swamp',
    'boat': fortress['boat'],
    'creatureBackground': fortress['creatureBackground'],
    'puzzleMap': fortress['puzzleMap'],
    'town': {
        'mapObject': fortress['town']['mapObject'],
        'icons': screen['icons'],
        'musicTheme': fortress['town']['musicTheme'],
        'defaultTavern': 5,
        'tavernVideo': fortress['town']['tavernVideo'],
        'guildBackground': dungeon['town']['guildBackground'],
        'townBackground': screen['background'],
        'guildWindow': dungeon['town']['guildWindow'],
        'guildWindowPosition': dungeon['town']['guildWindowPosition'],
        'guildSpellPositions': dungeon['town']['guildSpellPositions'],
        'buildingsIcons': 'naruto/%s/hallIcons' % F,
        # Fortress's hall background: rows keep its counts 4 / 3 / 3 / 4 / 3
        'hallBackground': fortress['town']['hallBackground'],
        'hallSlots': [
            [['villageHall', 'townHall', 'cityHall', 'capitol'], ['fort', 'citadel', 'castle'], ['tavern'], ['blacksmith']],
            [['marketplace'], ['mageGuild1', 'mageGuild2', 'mageGuild3', 'mageGuild4', 'mageGuild5'], ['shipyard']],
            [['special1'], ['special2'], ['resourceSilo']],
            [['dwellingLvl1', 'dwellingUpLvl1'], ['dwellingLvl2', 'dwellingUpLvl2'], ['dwellingLvl3', 'dwellingUpLvl3'], ['dwellingLvl4', 'dwellingUpLvl4']],
            [['dwellingLvl5', 'dwellingUpLvl5'], ['dwellingLvl6', 'dwellingUpLvl6'], ['dwellingLvl7', 'dwellingUpLvl7']],
        ],
        'creatures': [['mistGenin', 'bloodyMistGraduate'], ['hunterNin', 'trackerHunterNin'], ['hozukiBrawler', 'hozukiHydrifier'],
                      ['summonedShark', 'greatShark'], ['yukiClanAdept', 'iceMirrorMaster'], ['mistSwordsman', 'swordsmanOfTheSeven'],
                      ['waterDragon', 'greatWaterDragon']],
        'horde': [],
        'mageGuild': 5,
        'guildSpells': guild_spells,
        'primaryResource': 'mercury',
        'moatAbility': fortress['town']['moatAbility'],
        'names': [en for en, _ in TOWN_NAMES],
        'structures': structures,
        'buildings': buildings,
        'siege': siege,
    },
}}

# ------------------------------------------------------------------ hero classes

classes = dict([
    hero_class(t, F, 'swordsman', 'Swordsman', 'Мечник', 'might', 14, (3, 1, 1, 1), (50, 25, 10, 15), (35, 25, 20, 20),
               {'pathfinding': 6, 'archery': 4, 'logistics': 6, 'scouting': 6, 'diplomacy': 2, 'navigation': 5,
                'leadership': 4, 'wisdom': 2, 'mysticism': 2, 'luck': 5, 'ballistics': 4, 'eagleEye': 2,
                'necromancy': 0, 'estates': 2, 'fireMagic': 1, 'airMagic': 3, 'waterMagic': 4, 'earthMagic': 1,
                'scholar': 1, 'tactics': 7, 'artillery': 3, 'learning': 3, 'offence': 9, 'armorer': 4,
                'intelligence': 1, 'sorcery': 1, 'resistance': 3, 'firstAid': 2},
               {F: 6}),
    hero_class(t, F, 'mistSage', 'Mist Sage', 'Мудрец тумана', 'magic', 15, (1, 0, 2, 2), (20, 10, 35, 35), (20, 20, 30, 30),
               {'pathfinding': 3, 'archery': 1, 'logistics': 3, 'scouting': 4, 'diplomacy': 3, 'navigation': 4,
                'leadership': 2, 'wisdom': 8, 'mysticism': 5, 'luck': 3, 'ballistics': 1, 'eagleEye': 5,
                'necromancy': 0, 'estates': 2, 'fireMagic': 2, 'airMagic': 4, 'waterMagic': 9, 'earthMagic': 3,
                'scholar': 4, 'tactics': 2, 'artillery': 1, 'learning': 3, 'offence': 2, 'armorer': 1,
                'intelligence': 5, 'sorcery': 5, 'resistance': 2, 'firstAid': 3},
               {F: 6}),
])

# ------------------------------------------------------------------ heroes

G, N, Z = 'mistGenin', 'hunterNin', 'hozukiBrawler'
STD = [(G, 12, 24), (N, 4, 7), (Z, 2, 3)]
B_ = 'basic'
grows = lambda per20: {'type': 'GROWS_WITH_LEVEL', 'valPer20': per20, 'stepSize': 1}
creature_spec = lambda en, ru, what_en, what_ru: (
    (en, 'Creature bonus: ' + en,
     'Increases the speed of any %s by 1 and their Attack and Defense by 5%% for every level of the hero divided by the creature tier.' % what_en),
    (ru, 'Бонус существам: ' + ru,
     'Скорость существ (%s) +1, атака и защита +5%% за каждый уровень героя, делённый на уровень существа.' % what_ru))
skill_spec = lambda en, ru, what_en, what_ru: (
    (en, 'Secondary skill bonus: ' + en, 'Increases the effect of the %s skill by 5%% for every level.' % what_en),
    (ru, 'Бонус навыку: ' + ru, 'Эффект навыка «%s» +5%% за каждый уровень героя.' % what_ru))
school_spec = lambda en, ru, school_en, school_ru, school: (
    ((en, school_en + ' magic bonus', '%s spells cast by the hero are 2%% more effective for every level.' % school_en),
     (ru, 'Бонус магии ' + school_ru, 'Заклинания магии %s эффективнее на 2%% за каждый уровень героя.' % school_ru)),
    {'bonuses': {'school': {'type': 'SPELL_DAMAGE', 'subtype': 'spellSchool.' + school, 'val': 2, 'updater': 'TIMES_HERO_LEVEL'}}})

# Specialty icons: the original hero specialty icon closest in meaning (UN44/UN32 frame).
ICON = {'zabuzaMomochi': 152, 'kisameHoshigaki': 112, 'chojuro': 109, 'mangetsuHozuki': 131, 'suigetsuHozuki': 135,
        'ameyuriRingo': 45, 'kushimaruKuriarare': 114, 'jinpachiMunashi': 118, 'haku': 30, 'meiTerumi': 57, 'ao': 110,
        'yagura': 151, 'utakata': 122, 'gengetsuHozuki': 40}

H_ = []
def add(hid, cls, female, name, ru_name, bio, ru_bio, spec, specialty, skills, army, spells=None):
    H_.append(hero(t, hid, cls, female, name, ru_name, bio, ru_bio, spec[0], spec[1], specialty, skills, army,
                   0, ICON[hid], spells))   # portraits are Anton's; the borrowed fallback is never used

add('zabuzaMomochi', 'swordsman', False, 'Zabuza Momochi', 'Забуза Момочи',
    'The Demon of the Hidden Mist, master of the Silent Killing, who strikes from fog no one can see through.',
    'Демон Скрытого Тумана, мастер Беззвучного убийства, бьющий из тумана, сквозь который никто не видит.',
    creature_spec('Mist Swordsmen', 'Мечники Тумана', 'Mist Swordsmen or Swordsmen of the Seven', 'мечники Тумана и мечники Семи'),
    {'creature': 'mistSwordsman'}, [('offence', B_), ('tactics', B_)], STD)
add('kisameHoshigaki', 'swordsman', False, 'Kisame Hoshigaki', 'Кисаме Хошигаки',
    'The Monster of the Hidden Mist, wielder of Samehada, who fights with sharks at his side.',
    'Монстр Скрытого Тумана, владелец Самехады, сражающийся бок о бок с акулами.',
    creature_spec('Sharks', 'Акулы', 'Summoned Sharks or Great Sharks', 'призванные и великие акулы'),
    {'creature': 'summonedShark'}, [('offence', B_), ('armorer', B_)], STD)
add('chojuro', 'swordsman', False, 'Chojuro', 'Чоджуро',
    'A shy young swordsman whose twin-hilted Hiramekarei turns his chakra into a blade.',
    'Застенчивый молодой мечник, чей двуручный Хирамекарей превращает его чакру в клинок.',
    skill_spec('Offense', 'Нападение', 'Offense', 'Нападение'), {'secondary': 'offence'},
    [('offence', B_), ('leadership', B_)], STD)
add('mangetsuHozuki', 'swordsman', False, 'Mangetsu Hozuki', 'Мангецу Хозуки',
    'The prodigy of the Hozuki clan, who mastered all seven swords and turns his body to water.',
    'Гений клана Хозуки, освоивший все семь мечей и обращающий своё тело в воду.',
    creature_spec('Hozuki', 'Хозуки', 'Hozuki Brawlers or Hydrifiers', 'бойцы и гидрификаторы Хозуки'),
    {'creature': Z}, [('offence', B_), ('tactics', B_)], [(G, 12, 24), (Z, 2, 3), (Z, 2, 3)])
add('suigetsuHozuki', 'swordsman', False, 'Suigetsu Hozuki', 'Суйгецу Хозуки',
    'Mangetsu\'s younger brother, who slips out of any blow by melting into water.',
    'Младший брат Мангецу, ускользающий от любого удара, растекаясь водой.',
    (('Water Body', 'Hozuki bonus', 'Hozuki Brawlers and Hydrifiers get +1 speed and take 10% less damage from attacks.'),
     ('Водное тело', 'Бонус Хозуки', 'Бойцы и гидрификаторы Хозуки получают +1 к скорости и на 10% меньше урона от атак.')),
    {'base': {'limiters': [{'type': 'CREATURE_TYPE_LIMITER', 'creature': Z, 'includeUpgrades': True}]},
     'bonuses': {'speed': {'type': 'STACKS_SPEED', 'val': 1},
                 'water': {'type': 'GENERAL_DAMAGE_REDUCTION', 'subtype': 'damageTypeAll', 'val': 10}}},
    [('logistics', B_), ('offence', B_)], [(G, 12, 24), (Z, 2, 3), (Z, 2, 3)])
add('ameyuriRingo', 'swordsman', True, 'Ameyuri Ringo', 'Амеюри Ринго',
    'One of the Seven Swordsmen, whose twin blades Kiba call down lightning.',
    'Одна из Семи мечников; её парные клинки Киба призывают молнии.',
    *school_spec('Lightning Blades', 'Клинки молний', 'Air', 'Воздуха', 'air'),
    [('airMagic', B_), ('offence', B_)], STD, ['lightningBolt'])
add('kushimaruKuriarare', 'swordsman', False, 'Kushimaru Kuriarare', 'Кушимару Курияраре',
    'A masked swordsman of the Seven whose needle sword Nuibari stitches his foes together.',
    'Мечник Семи в маске, чей игольчатый меч Нуибари сшивает врагов вместе.',
    creature_spec('Hunter-nin', 'Охотники-ниндзя', 'Hunter-nin or Tracker Hunter-nin', 'охотники-ниндзя и следопыты'),
    {'creature': N}, [('archery', B_), ('offence', B_)], [(G, 12, 24), (N, 4, 7), (N, 4, 7)])
add('jinpachiMunashi', 'swordsman', False, 'Jinpachi Munashi', 'Джинпачи Мунаши',
    'A swordsman of the Seven whose explosive blade Shibuki blows apart whatever it strikes.',
    'Мечник Семи, чей взрывной клинок Шибуки разносит в клочья всё, по чему ударит.',
    (('Ballista', 'Ballista bonus', 'The Ballista gains +1 speed and +5% Attack and Defense for every 5 levels of the hero.'),
     ('Баллиста', 'Бонус баллисте', 'Баллиста получает +1 к скорости и +5% к атаке и защите за каждые 5 уровней героя.')),
    {'creature': 'ballista', 'creatureLevel': 5}, [('artillery', B_), ('offence', B_)],
    [(G, 12, 24), ('ballista', 1, 1), (Z, 2, 3)])
add('haku', 'mistSage', False, 'Haku', 'Хаку',
    'The last of the Yuki clan, whose Demonic Ice Mirrors trap the enemy in a hall of ice.',
    'Последний из клана Юки, чьи Демонические ледяные зеркала запирают врага в ледяном зале.',
    creature_spec('Ice Mirrors', 'Ледяные зеркала', 'Yuki Clan Adepts or Ice Mirror Masters', 'адепты клана Юки и мастера ледяных зеркал'),
    {'creature': 'yukiClanAdept'}, [('waterMagic', B_), ('wisdom', B_)], STD, ['iceBolt'])
add('meiTerumi', 'mistSage', True, 'Mei Terumi', 'Мей Теруми',
    'The Fifth Mizukage, who wields both Lava Release and Boil Release.',
    'Пятая Мизукаге, владеющая стихиями Лавы и Кипения.',
    (('Lava Release', 'Spell bonus: Inferno', 'Her Inferno deals 3% more damage for every level.'),
     ('Стихия Лавы', 'Бонус заклинанию: Инферно', 'Её Инферно наносит на 3% больше урона за каждый уровень.')),
    {'bonuses': {'lava': {'type': 'SPECIFIC_SPELL_DAMAGE', 'subtype': 'spell.inferno', 'val': 3, 'updater': 'TIMES_HERO_LEVEL'}}},
    [('fireMagic', B_), ('wisdom', B_)], STD, ['inferno'])
add('ao', 'mistSage', False, 'Ao', 'Ао',
    'The Mizukage\'s bodyguard, who carries a stolen Byakugan under his eyepatch.',
    'Телохранитель Мизукаге, носящий под повязкой похищенный Бьякуган.',
    (('Byakugan', 'Secondary skill bonus: Scouting', 'Increases the effect of the Scouting skill by 5% for every level.'),
     ('Бьякуган', 'Бонус навыку: Разведка', 'Эффект навыка «Разведка» +5% за каждый уровень героя.')),
    {'secondary': 'scouting'}, [('scouting', B_), ('wisdom', B_)], STD, ['dispel'])
add('yagura', 'mistSage', False, 'Yagura', 'Ягура',
    'The Fourth Mizukage, a child-faced ruler who commanded water dragons in the Bloody Mist years.',
    'Четвёртый Мизукаге, правитель с детским лицом, повелевавший водными драконами в годы Кровавого Тумана.',
    creature_spec('Water Dragons', 'Водные драконы', 'Water Dragons or Great Water Dragons', 'водные и великие водные драконы'),
    {'creature': 'waterDragon'}, [('waterMagic', B_), ('wisdom', B_)], STD, ['cure'])
add('utakata', 'mistSage', False, 'Utakata', 'Утаката',
    'A wandering ninja who blows bubbles through a pipe; some of them burst like acid, some carry him away.',
    'Странствующий ниндзя, выдувающий пузыри из трубки; одни лопаются кислотой, на других он улетает.',
    *school_spec('Bubbles', 'Пузыри', 'Water', 'Воды', 'water'),
    [('waterMagic', B_), ('wisdom', B_)], STD, ['protectFire'])
add('gengetsuHozuki', 'mistSage', False, 'Gengetsu Hozuki', 'Гэнгецу Хозуки',
    'The Second Mizukage, the "Mirage", whose clam-born illusions leave archers shooting at nothing.',
    'Второй Мизукаге, «Мираж», чьи иллюзии из моллюска заставляют лучников стрелять в пустоту.',
    (('Mirages', 'Opening Forgetfulness', 'Each battle opens with expert Forgetfulness on all enemy shooters. It lasts 1 round, 2 from level 6, 3 from level 11 and 4 from level 16.'),
     ('Миражи', 'Забывчивость в начале боя', 'Каждый бой начинается с Забывчивости (эксперт) на всех вражеских стрелков. Длится 1 раунд, 2 с 6-го уровня, 3 с 11-го и 4 с 16-го.')),
    {'bonuses': {'mirage': {'type': 'OPENING_BATTLE_SPELL', 'subtype': 'spell.forgetfulness', 'addInfo': 3, 'updater': grows(4)}}},
    [('wisdom', B_), ('intelligence', B_)], STD, ['forgetfulness'])
heroes = dict(H_)

# ------------------------------------------------------------------ adventure-map dwellings

dwellings = {'core:creatureGeneratorCommon': {'types': dict([
    dwelling_object_like(t, 'mistAcademy', 'Mist Academy', 'Академия Тумана', G, 'troglodyte'),
    dwelling_object_like(t, 'hunterNinDivision', 'Hunter-nin Division', 'Отдел охотников', N, 'lizardman'),
    dwelling_object_like(t, 'hozukiWaterPools', 'Hozuki Water Pools', 'Водоёмы Хозуки', Z, 'gnoll'),   # the Water Conflux is too big for a random dwelling
    dwelling_object_like(t, 'sharkReef', 'Shark Reef', 'Акулий риф', 'summonedShark', 'basilisk'),
    dwelling_object_like(t, 'yukiClanIceHall', 'Yuki Clan Ice Hall', 'Ледяной зал Юки', 'yukiClanAdept', 'medusa'),
    dwelling_object_like(t, 'hallOfTheSevenSwordsmen', 'Hall of the Seven Swordsmen', 'Зал Семи мечников', 'mistSwordsman', 'swordsman'),
    dwelling_object_like(t, 'waterDragonLake', 'Water Dragon Lake', 'Озеро водного дракона', 'waterDragon', 'greenDragon'),
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
faction_texts(t, F, 'Кири',
              '{Кири}\n\nДеревня Скрытого Тумана на островах Страны Воды. Мечники и Мудрецы тумана ведут убийц из тумана: быстрые, смертоносные и хрупкие войска, акулы, лёд и водные драконы.',
              [ru for _, ru in TOWN_NAMES], BUILDING_RU,
              extra={'special2.onVisited': 'Вы уже сражались на арене.',
                     'special2.rewards.0': 'Выжившие в Кровавом Тумане сражаются яростнее: +1 к атаке и +1 к защите.'})
ru_file = write_json('Content/config/translations/russian-%s.json' % F, dict(sorted(t.ru.items())))
register(files, ru_file)
print('%s: %d creatures, %d classes, %d heroes, %d buildings, %d Russian strings' %
      (F, len(creatures), len(classes), len(heroes), len(buildings), len(t.ru)))
