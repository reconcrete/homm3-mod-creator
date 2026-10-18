"""Sunagakure: generates the town's JSON from the spec in the vault note
~/O/Projects/HoMM3-Naruto/Plans/Naruto-Mod-Sunagakure.md ("Details").
Run: python3 tools/towns/sunagakure.py   (then tools/check.sh)"""
import copy, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from townkit import *

F = 'sunagakure'
t = Texts()
castle = load(VCMI_CONFIG + '/factions/castle.json')['castle']
stronghold = load(VCMI_CONFIG + '/factions/stronghold.json')['stronghold']
tower = load(VCMI_CONFIG + '/factions/tower.json')['tower']

def stats(cost, hp, speed, att, dfn, dmg, growth, fight, ai, amount):
    return dict(cost=cost, hp=hp, speed=speed, attack=att, defense=dfn, dmg=dmg,
                growth=growth, fight=fight, ai=ai, amount=amount)

# ------------------------------------------------------------------ creatures

construct = {'construct': {'type': 'NON_LIVING'}, 'mindImmunity': {'type': 'MIND_IMMUNITY'}}
sand_shield = lambda v: {'sandShield': {'type': 'GENERAL_DAMAGE_REDUCTION', 'subtype': 'damageTypeRanged', 'val': v}}
poison = lambda chance: {'poison': {'type': 'SPELL_AFTER_ATTACK', 'subtype': 'spell.poison', 'val': chance}}
spell_armor = lambda v: {'spellArmor': {'type': 'SPELL_DAMAGE_REDUCTION', 'subtype': 'spellSchool.any', 'val': v}}
sand_armor = lambda v: {'sandArmor': {'type': 'GENERAL_DAMAGE_REDUCTION', 'subtype': 'damageTypeAll', 'val': v}}
wind_blade = {'windBlade': {'type': 'TWO_HEX_ATTACK_BREATH'}, 'flies': {'type': 'FLYING'}}

creatures = dict([
    creature(t, F, 'sunaGenin', 1, ('Suna Genin', 'Suna Genin'), ('Генин Суны', 'Генины Суны'),
             'pikeman', 'Pikeman', stats({'gold': 55}, 9, 5, 4, 5, (1, 3), 14, 90, 85, (20, 50)),
             upgrades=['sunaChunin'], abilities=sand_shield(25)),
    creature(t, F, 'sunaChunin', 1, ('Suna Chunin', 'Suna Chunin'), ('Чунин Суны', 'Чунины Суны'),
             'halberdier', 'Halberdier', stats({'gold': 80}, 10, 6, 5, 7, (2, 3), 14, 115, 120, (20, 50)),
             abilities=sand_shield(40)),
    creature(t, F, 'woodenPuppet', 2, ('Wooden Puppet', 'Wooden Puppets'), ('Деревянная марионетка', 'Деревянные марионетки'),
             'stoneGargoyle', 'Stone Gargoyle', stats({'gold': 110}, 18, 5, 6, 6, (2, 4), 9, 150, 150, (16, 30)),
             upgrades=['battlePuppet'], abilities=dict(construct), double_wide=False),
    creature(t, F, 'battlePuppet', 2, ('Battle Puppet', 'Battle Puppets'), ('Боевая марионетка', 'Боевые марионетки'),
             'obsidianGargoyle', 'Obsidian Gargoyle', stats({'gold': 150}, 20, 6, 7, 7, (2, 4), 9, 190, 210, (16, 30)),
             abilities=dict(construct, blackAnt={'type': 'SPELL_AFTER_ATTACK', 'subtype': 'spell.bind', 'val': 100}),
             double_wide=False),
    creature(t, F, 'windKunoichi', 3, ('Wind Kunoichi', 'Wind Kunoichi'), ('Куноичи ветра', 'Куноичи ветра'),
             'orc', 'Orc', stats({'gold': 220}, 16, 6, 9, 5, (3, 5), 7, 230, 270, (12, 25)),
             upgrades=['fanMaster'], shots=12, projectile='wind-scythe', abilities={'shooter': {'type': 'SHOOTER'}}),
    creature(t, F, 'fanMaster', 3, ('Fan Master', 'Fan Masters'), ('Мастер веера', 'Мастера веера'),
             'orcChieftain', 'Orc Chieftain', stats({'gold': 280}, 18, 7, 10, 6, (3, 5), 7, 290, 380, (12, 25)),
             shots=16, projectile='wind-scythe', abilities={'shooter': {'type': 'SHOOTER'}, 'windScythe': {'type': 'SHOOTS_ALL_ADJACENT'}}),
    creature(t, F, 'desertScorpion', 4, ('Desert Scorpion', 'Desert Scorpions'), ('Пустынный скорпион', 'Пустынные скорпионы'),
             'manticore', 'Manticore', stats({'gold': 300}, 38, 6, 10, 11, (4, 7), 4, 400, 430, (10, 20)),
             upgrades=['poisonScorpion'], abilities=poison(20), double_wide=True),
    creature(t, F, 'poisonScorpion', 4, ('Poison Scorpion', 'Poison Scorpions'), ('Ядовитый скорпион', 'Ядовитые скорпионы'),
             'scorpicore', 'Scorpicore', stats({'gold': 380}, 42, 7, 11, 12, (5, 8), 4, 480, 560, (10, 20)),
             abilities=poison(40), double_wide=True),
    creature(t, F, 'humanPuppet', 5, ('Human Puppet', 'Human Puppets'), ('Человеческая марионетка', 'Человеческие марионетки'),
             'ironGolem', 'Iron Golem', stats({'gold': 550}, 50, 5, 13, 15, (10, 15), 3, 620, 680, (8, 16)),
             upgrades=['kazekagePuppet'], abilities=dict(construct, **spell_armor(30))),
    creature(t, F, 'kazekagePuppet', 5, ('Kazekage Puppet', 'Kazekage Puppets'), ('Марионетка Казекаге', 'Марионетки Казекаге'),
             'stoneGolem', 'Arch Mage', stats({'gold': 650}, 55, 6, 15, 16, (12, 16), 3, 760, 900, (8, 16)),
             shots=8, projectile='senbon',   # iron sand needles
             abilities=dict(construct, shooter={'type': 'SHOOTER'}, **spell_armor(50))),
    creature(t, F, 'kamaitachi', 6, ('Kamaitachi', 'Kamaitachi'), ('Камаитачи', 'Камаитачи'),
             'roc', 'Roc', stats({'gold': 1050}, 85, 10, 17, 13, (15, 22), 2, 1400, 1600, (4, 10)),
             upgrades=['greatKamaitachi'], abilities=dict(wind_blade), double_wide=True),
    creature(t, F, 'greatKamaitachi', 6, ('Great Kamaitachi', 'Great Kamaitachi'), ('Великий Камаитачи', 'Великие Камаитачи'),
             'thunderbird', 'Thunderbird', stats({'gold': 1300}, 95, 13, 19, 15, (18, 26), 2, 1750, 2100, (4, 10)),
             abilities=dict(wind_blade), double_wide=True),
    creature(t, F, 'sandColossus', 7, ('Sand Colossus', 'Sand Colossi'), ('Песчаный колосс', 'Песчаные колоссы'),
             'giant', 'Lesser Titan', stats({'gold': 2400, 'crystal': 1}, 230, 6, 19, 22, (30, 45), 1, 3500, 4300, (1, 4)),
             upgrades=['gaarasSandTsunami'], abilities=dict(construct, **sand_armor(20)), double_wide=True),
    creature(t, F, 'gaarasSandTsunami', 7, ("Gaara's Sand Tsunami", "Gaara's Sand Tsunamis"),
             ('Песчаное цунами Гаары', 'Песчаные цунами Гаары'),
             'titan', 'Greater Titan', stats({'gold': 4500, 'crystal': 2}, 330, 8, 24, 28, (40, 55), 1, 6200, 8200, (1, 4)),
             abilities=dict(construct, wave={'type': 'ATTACKS_ALL_ADJACENT'}, **sand_armor(25)), double_wide=True),
])
for c in creatures.values():      # Titan and Orc graphics come with ranged parts we don't use
    if 'shots' not in c:
        c['graphics'].pop('missile', None)

# ------------------------------------------------------------------ buildings

B = {}
B.update(hall_chain(['Kazekage Office', 'Kazekage Chambers', 'Kazekage Tower', 'Kazekage Residence'],
                    ['Кабинет Казекаге', 'Палаты Казекаге', 'Башня Казекаге', 'Резиденция Казекаге'],
                    'your village', 'деревне'))
B.update(fort_chain(['Sand Wall', 'Fortified Sand Wall', 'Absolute Sand Defense'],
                    ['Песчаная стена', 'Укреплённая стена', 'Абсолютная защита']))
B.update(guild_chain('Wind Scroll Tower', 'Башня свитков ветра'))
B['tavern'] = building('Desert Oasis Inn', 'Оазис', 'Travellers rest at the oasis: hire heroes, hear rumors and visit the Thieves\' Guild. Defenders fight with +1 morale.',
                       'Путники отдыхают у оазиса: наём героев, слухи и гильдия воров. Защитники города получают +1 к боевому духу.',
                       {'gold': 500, 'wood': 5})
B['blacksmith'] = building('Iron Sand Forge', 'Кузница железного песка', 'The Iron Sand Forge sells Ammo Carts to your armies.',
                           'Кузница железного песка продаёт вашим армиям тележки с боеприпасами.', {'gold': 1000, 'wood': 5},
                           warMachine='ammoCart')
B['marketplace'] = building('Caravan Bazaar', 'Караванный базар', 'Trade resources here; the more markets you own, the better the rates.',
                            'Здесь можно обменивать ресурсы; чем больше у вас рынков, тем выгоднее курс.', {'gold': 500, 'wood': 5})
B['resourceSilo'] = building('Desert Storehouse', 'Пустынный склад', 'The Desert Storehouse adds 1 crystal to your stock every day.',
                             'Пустынный склад ежедневно приносит 1 кристалл.', {'gold': 5000, 'ore': 5}, produce={'crystal': 1})
B['special1'] = building('Sand Barrier', 'Песчаный барьер',
                         'In a siege the walls take one more hit and defenders take 20% less damage from shooters.',
                         'При осаде стены выдерживают на один удар больше, а защитники получают на 20% меньше урона от стрелков.',
                         {'gold': 2000, 'ore': 10}, requires=['fort'],
                         fortifications={'wallsHealth': 1, 'citadelHealth': 1, 'upperTowerHealth': 1, 'lowerTowerHealth': 1},
                         bonuses=[{'type': 'GENERAL_DAMAGE_REDUCTION', 'subtype': 'damageTypeRanged', 'val': 20}])
B['special2'] = building("Chiyo's Poison Lab", 'Лаборатория Чиё',
                         'Antidotes make Suna creatures immune to poison; venom research gives scorpions +2 Attack.',
                         'Противоядия защищают существ Суны от яда; опыты с ядом дают скорпионам +2 к атаке.',
                         {'gold': 1500, 'mercury': 5}, requires=['dwellingLvl4'],
                         bonuses=[{'type': 'SPELL_IMMUNITY', 'subtype': 'spell.poison', 'propagator': 'PLAYER',
                                   'limiters': [{'type': 'FACTION_LIMITER', 'faction': F}]},
                                  {'type': 'PRIMARY_SKILL', 'subtype': 'primarySkill.attack', 'val': 2, 'propagator': 'PLAYER',
                                   'limiters': [{'type': 'CREATURE_TYPE_LIMITER', 'creature': 'desertScorpion', 'includeUpgrades': True}]}])
B['grail'] = building("Shukaku's Tea Kettle", 'Чайник Шукаку',
                      'The relic Shukaku was once sealed in: +5000 gold per day, +50% creature growth and +2 Defense for all your heroes.',
                      'Реликвия, в которой когда-то был запечатан Шукаку: +5000 золота в день, +50% к приросту существ и +2 к защите всех ваших героев.',
                      bonuses=[{'type': 'PRIMARY_SKILL', 'subtype': 'primarySkill.defence', 'val': 2, 'propagator': 'PLAYER'}])
R = {'mercury': 2, 'sulfur': 2, 'crystal': 2, 'gems': 2}
R10 = {'mercury': 10, 'sulfur': 10, 'crystal': 10, 'gems': 10}
B.update(dwelling_pair(1, 'Desert Barracks', 'Пустынные казармы', 'Suna Genin', 'генины Суны', 'Suna Chunin', 'чунины Суны',
                       {'gold': 500, 'ore': 10}, {'gold': 1000, 'ore': 5}, ['fort']))
B.update(dwelling_pair(2, 'Puppet Workshop', 'Мастерская марионеток', 'Wooden Puppets', 'деревянные марионетки',
                       'Battle Puppets', 'боевые марионетки', {'gold': 1000, 'wood': 5, 'ore': 5},
                       {'gold': 1000, 'wood': 5, 'ore': 5}, ['dwellingLvl1']))
B.update(dwelling_pair(3, 'Wind Training Cliffs', 'Скалы ветра', 'Wind Kunoichi', 'куноичи ветра', 'Fan Masters', 'мастера веера',
                       {'gold': 1000, 'ore': 5}, {'gold': 1000, 'ore': 5}, ['dwellingLvl1']))
B.update(dwelling_pair(4, 'Scorpion Dunes', 'Дюны скорпионов', 'Desert Scorpions', 'пустынные скорпионы',
                       'Poison Scorpions', 'ядовитые скорпионы', {'gold': 2000, 'wood': 5, 'ore': 5},
                       {'gold': 2000, 'ore': 5, 'crystal': 5}, ['allOf', ['dwellingLvl1'], ['blacksmith']]))
B.update(dwelling_pair(5, 'Red Secret Puppet Hall', 'Зал алых марионеток', 'Human Puppets', 'человеческие марионетки',
                       'Kazekage Puppets', 'марионетки Казекаге', dict({'gold': 3000, 'wood': 5, 'ore': 5}, **R),
                       dict({'gold': 1000}, **R), ['allOf', ['dwellingLvl2'], ['mageGuild1']]))
B.update(dwelling_pair(6, 'Kamaitachi Canyon', 'Каньон Камаитачи', 'Kamaitachi', 'камаитачи', 'Great Kamaitachi',
                       'великие камаитачи', {'gold': 5000, 'wood': 10, 'ore': 10}, {'gold': 3000, 'ore': 10},
                       ['allOf', ['dwellingLvl3'], ['dwellingLvl5']]))
B.update(dwelling_pair(7, 'Sealed Sand Altar', 'Алтарь запечатанного песка', 'Sand Colossi', 'песчаные колоссы',
                       "Gaara's Sand Tsunamis", 'песчаные цунами Гаары', dict({'gold': 20000}, **R10), dict({'gold': 20000}, **R10),
                       ['allOf', ['dwellingLvl6'], ['mageGuild2']]))
BUILDING_RU = {k: (v[1], v[2]) for k, v in B.items()}
buildings = {k: v[0] for k, v in B.items()}

screen = town_screen(F)
assert screen, 'run tools/townscreen.py sunagakure first'

siege = copy.deepcopy(stronghold['town']['siege'])
siege['shooter'] = 'windKunoichi'
siege['towerIconLarge'] = creatures['windKunoichi']['graphics']['iconLarge']
siege['towerIconSmall'] = creatures['windKunoichi']['graphics']['iconSmall']

guild_spells = {
    'magicArrow': 30, 'shield': 12, 'protectFire': 4, 'protectWater': 3, 'dispel': 12, 'cure': 6, 'bless': 5,
    'stoneSkin': 12, 'haste': 14, 'slow': 8, 'bloodlust': 2, 'summonBoat': 2, 'viewEarth': 3, 'viewAir': 3,
    'iceBolt': 10, 'lightningBolt': 25, 'fireWall': 3, 'quicksand': 10, 'scuttleBoat': 2, 'visions': 3,
    'disguise': 4, 'protectAir': 3, 'precision': 10, 'weakness': 4, 'disruptingRay': 12, 'fortune': 8,
    'blind': 4, 'removeObstacle': 4,
    'fireball': 5, 'frostRing': 6, 'landMine': 4, 'forceField': 10, 'earthquake': 10, 'destroyUndead': 4,
    'airShield': 14, 'protectEarth': 5, 'antiMagic': 12, 'mirth': 4, 'misfortune': 4, 'hypnotize': 6,
    'forgetfulness': 6, 'teleport': 8,
    'chainLightning': 14, 'inferno': 3, 'meteorShower': 10, 'fireShield': 3, 'resurrection': 6, 'prayer': 5,
    'sorrow': 5, 'slayer': 5, 'frenzy': 4, 'counterstrike': 10, 'berserk': 4, 'clone': 6, 'waterWalk': 8,
    'townPortal': 10,
    'fly': 14, 'dimensionDoor': 12, 'implosion': 14, 'magicMirror': 12, 'fireElemental': 4,
    'earthElemental': 14, 'waterElemental': 6, 'airElemental': 16,
}

TOWN_NAMES = [('Sunagakure', 'Сунагакуре'), ('Hidden Sand', 'Скрытый Песок'), ('Wind Country Gate', 'Врата Страны Ветра'),
              ('Desert Oasis', 'Оазис'), ('Great Dunes', 'Великие дюны'), ('Red Canyon', 'Красный каньон'),
              ('Sand Fortress', 'Песчаная крепость'), ('Kazekage Pass', 'Перевал Казекаге'), ('Dry Wells', 'Сухие колодцы'),
              ('Puppet Valley', 'Долина марионеток')]

faction = {F: {
    'name': 'Sunagakure',
    'description': '{Sunagakure}\n\nThe Village Hidden in the Sand, in the Land of Wind. Puppeteers and Wind Sages field puppets that fear nothing, poison scorpions, wind shooters and giants of living sand behind walls of sand.',
    'alignment': 'neutral',
    'nativeTerrain': 'sand',
    'boat': stronghold['boat'],
    'creatureBackground': stronghold['creatureBackground'],
    'puzzleMap': stronghold['puzzleMap'],
    'town': {
        'mapObject': town_map_object('sunagakure', stronghold['town']['mapObject']),
        'icons': screen['icons'],
        'musicTheme': stronghold['town']['musicTheme'],
        'defaultTavern': 5,
        'tavernVideo': stronghold['town']['tavernVideo'],
        'guildBackground': tower['town']['guildBackground'],
        'townBackground': screen['background'],
        'guildWindow': tower['town']['guildWindow'],
        'guildWindowPosition': tower['town']['guildWindowPosition'],
        'guildSpellPositions': tower['town']['guildSpellPositions'],
        'buildingsIcons': 'naruto/%s/hallIcons' % F,
        # Castle's hall background: rows keep its counts 4 / 3 / 2 / 4 / 3
        'hallBackground': castle['town']['hallBackground'],
        'hallSlots': [
            [['villageHall', 'townHall', 'cityHall', 'capitol'], ['fort', 'citadel', 'castle'], ['tavern'], ['blacksmith']],
            [['marketplace'], ['mageGuild1', 'mageGuild2', 'mageGuild3', 'mageGuild4', 'mageGuild5'], ['special1']],
            [['special2'], ['resourceSilo']],
            [['dwellingLvl1', 'dwellingUpLvl1'], ['dwellingLvl2', 'dwellingUpLvl2'], ['dwellingLvl3', 'dwellingUpLvl3'], ['dwellingLvl4', 'dwellingUpLvl4']],
            [['dwellingLvl5', 'dwellingUpLvl5'], ['dwellingLvl6', 'dwellingUpLvl6'], ['dwellingLvl7', 'dwellingUpLvl7']],
        ],
        'creatures': [['sunaGenin', 'sunaChunin'], ['woodenPuppet', 'battlePuppet'], ['windKunoichi', 'fanMaster'],
                      ['desertScorpion', 'poisonScorpion'], ['humanPuppet', 'kazekagePuppet'], ['kamaitachi', 'greatKamaitachi'],
                      ['sandColossus', 'gaarasSandTsunami']],
        'horde': [],
        'mageGuild': 5,
        'guildSpells': guild_spells,
        'primaryResource': 'crystal',
        'moatAbility': stronghold['town']['moatAbility'],
        'names': [en for en, _ in TOWN_NAMES],
        'structures': screen['structures'],
        'buildings': buildings,
        'siege': siege,
    },
}}

# ------------------------------------------------------------------ hero classes

classes = dict([
    hero_class(t, F, 'puppeteer', 'Puppeteer', 'Кукольник', 'might', 4, (1, 3, 1, 1), (30, 45, 12, 13), (25, 35, 20, 20),
               {'pathfinding': 5, 'archery': 5, 'logistics': 5, 'scouting': 4, 'diplomacy': 3, 'navigation': 1,
                'leadership': 2, 'wisdom': 3, 'mysticism': 2, 'luck': 3, 'ballistics': 6, 'eagleEye': 2,
                'necromancy': 0, 'estates': 3, 'fireMagic': 1, 'airMagic': 4, 'waterMagic': 1, 'earthMagic': 3,
                'scholar': 2, 'tactics': 7, 'artillery': 7, 'learning': 3, 'offence': 5, 'armorer': 9,
                'intelligence': 2, 'sorcery': 1, 'resistance': 5, 'firstAid': 4},
               {F: 6}),
    hero_class(t, F, 'windSage', 'Wind Sage', 'Мудрец ветра', 'magic', 5, (0, 1, 2, 3), (15, 15, 35, 35), (20, 20, 30, 30),
               {'pathfinding': 3, 'archery': 1, 'logistics': 3, 'scouting': 3, 'diplomacy': 3, 'navigation': 1,
                'leadership': 1, 'wisdom': 8, 'mysticism': 4, 'luck': 3, 'ballistics': 1, 'eagleEye': 4,
                'necromancy': 0, 'estates': 3, 'fireMagic': 3, 'airMagic': 9, 'waterMagic': 3, 'earthMagic': 5,
                'scholar': 4, 'tactics': 2, 'artillery': 1, 'learning': 3, 'offence': 2, 'armorer': 2,
                'intelligence': 5, 'sorcery': 6, 'resistance': 2, 'firstAid': 3},
               {F: 6}),
])

# ------------------------------------------------------------------ heroes

S, W, K = 'sunaGenin', 'woodenPuppet', 'windKunoichi'
STD = [(S, 10, 20), (W, 4, 7), (K, 2, 3)]
B_, A_ = 'basic', 'advanced'
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

H_ = []
# Specialty icons: the original hero specialty icon closest in meaning (UN44/UN32 frame).
ICON = {'kankuro': 32, 'sasori': 34, 'chiyo': 25, 'baki': 102, 'matsuri': 5, 'yashamaru': 8, 'gaara': 77,
        'temari': 99, 'rasa': 15, 'pakura': 145, 'thirdKazekage': 129, 'ebizo': 56}

def add(hid, cls, female, name, ru_name, bio, ru_bio, spec, specialty, skills, army, spells=None):
    H_.append(hero(t, hid, cls, female, name, ru_name, bio, ru_bio, spec[0], spec[1], specialty, skills, army,
                   0, ICON[hid], spells))   # portraits are Anton's; the borrowed fallback is never used

add('kankuro', 'puppeteer', False, 'Kankuro', 'Канкуро',
    'Gaara\'s elder brother, a master puppeteer who fights from behind Karasu, Kuroari and Sanshouo.',
    'Старший брат Гаары, мастер-кукольник, сражающийся из-за спин Карасу, Куроари и Саншоуо.',
    creature_spec('Puppets', 'Марионетки', 'Wooden or Battle Puppets', 'деревянные и боевые марионетки'),
    {'creature': W}, [('artillery', B_), ('armorer', B_)], [(S, 10, 20), (W, 4, 7), (W, 4, 7)])
add('sasori', 'puppeteer', False, 'Sasori', 'Сасори',
    'Sasori of the Red Sand, who turned himself into a puppet and keeps a hundred more for battle.',
    'Сасори Красного Песка, превративший себя в марионетку и держащий для боя ещё сотню.',
    creature_spec('Human Puppets', 'Человеческие марионетки', 'Human or Kazekage Puppets', 'человеческие марионетки и марионетки Казекаге'),
    {'creature': 'humanPuppet'}, [('armorer', B_), ('tactics', B_)], STD)
add('chiyo', 'puppeteer', True, 'Chiyo', 'Чиё',
    'Lady Chiyo, the elder of Suna, inventor of puppet combat and of the jutsu that gives one\'s life to another.',
    'Старейшина Суны Чиё, основательница боя марионетками и создательница техники, отдающей свою жизнь другому.',
    (('Life Transfer', 'Spell bonus: Cure', 'Her Cure heals 5% more for every level.'),
     ('Передача жизни', 'Бонус заклинанию: Лечение', 'Её Лечение восстанавливает на 5% больше здоровья за каждый уровень.')),
    {'bonuses': {'lifeTransfer': {'type': 'SPECIFIC_SPELL_DAMAGE', 'subtype': 'spell.cure', 'val': 5, 'updater': 'TIMES_HERO_LEVEL'}}},
    [('firstAid', B_), ('tactics', B_)], STD, ['cure'])
add('baki', 'puppeteer', False, 'Baki', 'Баки',
    'The stern jonin who leads Suna\'s teams, with a wind blade that cuts before it is seen.',
    'Суровый джонин, ведущий команды Суны; его клинок ветра режет раньше, чем его заметят.',
    skill_spec('Offense', 'Нападение', 'Offense', 'Нападение'), {'secondary': 'offence'},
    [('offence', B_), ('tactics', B_)], STD)
add('matsuri', 'puppeteer', True, 'Matsuri', 'Мацури',
    'Gaara\'s devoted student, who trains the village\'s young genin with a rope dart.',
    'Преданная ученица Гаары, обучающая юных генинов деревни бою с джохьё.',
    creature_spec('Suna Genin', 'Генины Суны', 'Suna Genin or Suna Chunin', 'генины и чунины Суны'),
    {'creature': S}, [('archery', B_), ('offence', B_)], [(S, 10, 20), (S, 10, 20), (W, 4, 7)])
add('yashamaru', 'puppeteer', False, 'Yashamaru', 'Яшамару',
    'A gentle medical ninja who raised the young Gaara, and knows every wound sand can make.',
    'Мягкий ниндзя-медик, воспитавший маленького Гаару; ему знакома любая рана, какую может нанести песок.',
    skill_spec('First Aid', 'Первая помощь', 'First Aid', 'Первая помощь'), {'secondary': 'firstAid'},
    [('firstAid', B_), ('armorer', B_)], [(S, 10, 20), ('firstAidTent', 1, 1), (W, 4, 7)])
add('gaara', 'windSage', False, 'Gaara', 'Гаара',
    'The Fifth Kazekage, whose sand moves on its own to shield him and those he protects.',
    'Пятый Казекаге, чей песок сам защищает его и тех, кого он оберегает.',
    (('Sand Shield', 'Spell bonus: Stone Skin', 'His Stone Skin gives extra Defense by creature tier: +3 for tiers 1–2, +2 for tiers 3–4, +1 for tiers 5–6.'),
     ('Песчаный щит', 'Бонус заклинанию: Каменная кожа', 'Его Каменная кожа даёт дополнительную защиту по уровню существа: +3 для 1–2, +2 для 3–4, +1 для 5–6.')),
    {'bonuses': {'sandShield': {'type': 'SPECIAL_PECULIAR_ENCHANT', 'subtype': 'spell.stoneSkin', 'addInfo': 0}}},
    [('earthMagic', B_), ('wisdom', B_)], STD, ['stoneSkin'])
add('temari', 'windSage', True, 'Temari', 'Темари',
    'The eldest of the Sand siblings, whose giant fan raises gales and calls the Kamaitachi.',
    'Старшая из детей Казекаге; её огромный веер поднимает бури и призывает Камаитачи.',
    creature_spec('Kamaitachi', 'Камаитачи', 'Kamaitachi or Great Kamaitachi', 'камаитачи и великие камаитачи'),
    {'creature': 'kamaitachi'}, [('airMagic', B_), ('wisdom', B_)], STD, ['disruptingRay'])
add('rasa', 'windSage', False, 'Rasa', 'Раса',
    'The Fourth Kazekage, whose Gold Dust filled the village\'s coffers.',
    'Четвёртый Казекаге, чья Золотая пыль наполняла казну деревни.',
    (('Gold Dust', '+350 gold per day', 'Adds 350 gold to your treasury every day.'),
     ('Золотая пыль', '+350 золота в день', 'Ежедневно приносит в казну 350 золота.')),
    {'bonuses': {'gold': {'type': 'GENERATE_RESOURCE', 'subtype': 'resource.gold', 'val': 350}}},
    [('wisdom', B_), ('estates', B_)], STD, ['shield'])
add('pakura', 'windSage', True, 'Pakura', 'Пакура',
    'The Hero of the Sand, whose Scorch Release dries an enemy to dust in a heartbeat.',
    'Героиня Песка, чья стихия Испепеления иссушает врага в одно мгновение.',
    *school_spec('Scorch Release', 'Стихия Испепеления', 'Fire', 'Огня', 'fire'),
    [('fireMagic', B_), ('wisdom', B_)], STD, ['magicArrow'])
add('thirdKazekage', 'windSage', False, 'Third Kazekage', 'Третий Казекаге',
    'The strongest Kazekage in Suna\'s history, master of iron sand.',
    'Сильнейший Казекаге в истории Суны, повелитель железного песка.',
    *school_spec('Iron Sand', 'Железный песок', 'Earth', 'Земли', 'earth'),
    [('earthMagic', B_), ('wisdom', B_)], STD, ['slow'])
add('ebizo', 'windSage', False, 'Ebizo', 'Эбизо',
    'Chiyo\'s younger brother, an elder of the council who has seen every trick the desert knows.',
    'Младший брат Чиё, старейшина совета, повидавший все хитрости пустыни.',
    (('Elder\'s Knowledge', 'Knowledge bonus', '+1 Knowledge, and 1 more for every 4 levels (rounded up).'),
     ('Знания старейшины', 'Бонус к знаниям', '+1 к знаниям и ещё по 1 за каждые 4 уровня (с округлением вверх).')),
    {'bonuses': {'knowledge': {'type': 'PRIMARY_SKILL', 'subtype': 'primarySkill.knowledge', 'updater': grows(5)}}},
    [('wisdom', A_)], STD, ['dispel'])
heroes = dict(H_)

# ------------------------------------------------------------------ adventure-map dwellings

dwellings = {'core:creatureGeneratorCommon': {'types': dict([
    dwelling_object_like(t, 'desertBarracks', 'Desert Barracks', 'Пустынные казармы', S, 'pikeman'),
    dwelling_object_like(t, 'puppetWorkshop', 'Puppet Workshop', 'Мастерская марионеток', W, 'stoneGargoyle'),
    dwelling_object_like(t, 'windTrainingCliffs', 'Wind Training Cliffs', 'Скалы ветра', K, 'orc'),
    dwelling_object_like(t, 'scorpionDunes', 'Scorpion Dunes', 'Дюны скорпионов', 'desertScorpion', 'manticore'),
    dwelling_object_like(t, 'redSecretPuppetHall', 'Red Secret Puppet Hall', 'Зал алых марионеток', 'humanPuppet', 'mage'),
    dwelling_object_like(t, 'kamaitachiCanyon', 'Kamaitachi Canyon', 'Каньон Камаитачи', 'kamaitachi', 'roc'),
    dwelling_object_like(t, 'sealedSandAltar', 'Sealed Sand Altar', 'Алтарь запечатанного песка', 'sandColossus', 'giant'),
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
faction_texts(t, F, 'Суна',
              '{Суна}\n\nДеревня Скрытого Песка в Стране Ветра. Кукольники и Мудрецы ветра ведут в бой бесстрашных марионеток, ядовитых скорпионов, стрелков ветра и великанов из живого песка под защитой песчаных стен.',
              [ru for _, ru in TOWN_NAMES], BUILDING_RU)
ru_file = write_json('Content/config/translations/russian-%s.json' % F, dict(sorted(t.ru.items())))
register(files, ru_file)
print('%s: %d creatures, %d classes, %d heroes, %d buildings, %d Russian strings' %
      (F, len(creatures), len(classes), len(heroes), len(buildings), len(t.ru)))
