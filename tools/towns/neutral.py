"""Neutral creatures and tailed-beast bosses: generates Content/config/neutral/*.json from
the spec in ~/O/Projects/HoMM3-Naruto/Plans/Naruto-Mod-Neutral-Creatures.md ("Details").
Run: python3 tools/towns/neutral.py   (then tools/check.sh)"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from townkit import *

AREA = 'neutral'
t = Texts()

def stats(cost, hp, speed, att, dfn, dmg, growth, fight, ai, amount):
    return dict(cost=cost, hp=hp, speed=speed, attack=att, defense=dfn, dmg=dmg,
                growth=growth, fight=fight, ai=ai, amount=amount)

boss = {'excludeFromRandomization': True}
on_terrain = lambda terrain: [
    {'type': 'PRIMARY_SKILL', 'subtype': 'primarySkill.attack', 'val': 3, 'limiters': [{'type': 'TERRAIN_LIMITER', 'terrain': terrain}]},
    {'type': 'PRIMARY_SKILL', 'subtype': 'primarySkill.defence', 'val': 3, 'limiters': [{'type': 'TERRAIN_LIMITER', 'terrain': terrain}]}]

creatures = dict([
    creature(t, 'neutral', 'whiteZetsu', 1, ('White Zetsu', 'White Zetsu'), ('Белый Зецу', 'Белые Зецу'),
             'peasant', 'Peasant', stats({'gold': 35}, 5, 4, 3, 3, (1, 2), 20, 45, 40, (40, 90)),
             abilities={'noWill': {'type': 'MIND_IMMUNITY'}}),
    creature(t, 'neutral', 'ninjaCat', 2, ('Ninja Cat', 'Ninja Cats'), ('Кошка-ниндзя', 'Кошки-ниндзя'),
             'harpy', 'Harpy', stats({'gold': 90}, 10, 9, 6, 4, (2, 3), 9, 120, 140, (16, 30)),
             abilities={'thief': {'type': 'RETURN_AFTER_STRIKE'}}, double_wide=False),
    creature(t, 'neutral', 'rogueNinja', 2, ('Rogue Ninja', 'Rogue Ninja'), ('Нукенин', 'Нукенины'),
             'rogue', 'Rogue', stats({'gold': 100}, 12, 6, 7, 4, (2, 4), 8, 130, 130, (16, 30))),
    creature(t, 'neutral', 'soundNinja', 3, ('Sound Ninja', 'Sound Ninja'), ('Ниндзя Звука', 'Ниндзя Звука'),
             'sharpshooter', 'Sharpshooter', stats({'gold': 220}, 20, 6, 8, 6, (3, 5), 6, 260, 300, (12, 25)),
             shots=12, projectile='kunai', abilities={'shooter': {'type': 'SHOOTER'},
                                  'soundWave': {'type': 'ENEMY_DEFENCE_REDUCTION', 'val': 30}}),
    creature(t, 'neutral', 'rainNinja', 3, ('Rain Ninja', 'Rain Ninja'), ('Ниндзя Дождя', 'Ниндзя Дождя'),
             'nomad', 'Nomad', stats({'gold': 200}, 22, 6, 8, 7, (3, 5), 6, 250, 260, (12, 25)),
             abilities={'rainSwampAttack': on_terrain('swamp')[0], 'rainSwampDefense': on_terrain('swamp')[1],
                        'rainWaterAttack': on_terrain('water')[0], 'rainWaterDefense': on_terrain('water')[1]},
             double_wide=False),
    creature(t, 'neutral', 'stoneNinja', 4, ('Stone Ninja', 'Stone Ninja'), ('Ниндзя Камня', 'Ниндзя Камня'),
             'battleDwarf', 'Battle Dwarf', stats({'gold': 350}, 40, 5, 10, 14, (5, 8), 4, 430, 440, (10, 20)),
             abilities={'earthStyle': {'type': 'DEFENSIVE_STANCE', 'val': 5}}),
    creature(t, 'neutral', 'cloudNinja', 5, ('Cloud Ninja', 'Cloud Ninja'), ('Ниндзя Облака', 'Ниндзя Облака'),
             'stormElemental', 'Storm Elemental', stats({'gold': 500}, 35, 9, 13, 10, (9, 14), 3, 580, 680, (8, 16)),
             abilities={'lightning': {'type': 'SPELL_AFTER_ATTACK', 'subtype': 'spell.thunderbolt', 'val': 20},
                        'lightningStrength': {'type': 'SPECIFIC_SPELL_POWER', 'subtype': 'spell.thunderbolt', 'val': 10}}),
    creature(t, 'neutral', 'curseMarkWarrior', 5, ('Curse Mark Warrior', 'Curse Mark Warriors'),
             ('Воин проклятой печати', 'Воины проклятой печати'),
             'troll', 'Troll', stats({'gold': 550}, 45, 7, 15, 9, (12, 16), 3, 640, 720, (8, 16)),
             abilities={'berserkPower': {'type': 'REVENGE'}, 'mindless': {'type': 'MIND_IMMUNITY'}}),
    creature(t, 'neutral', 'monkeyKingEnma', 6, ('Monkey King Enma', 'Monkey King Enma'), ('Царь обезьян Энма', 'Цари обезьян Энма'),
             'ogre', 'Ogre', stats({'gold': 1100}, 100, 8, 17, 17, (18, 26), 2, 1500, 1700, (4, 10)),
             abilities={'adamantineStaff': {'type': 'UNLIMITED_RETALIATIONS'}}, double_wide=True),
    creature(t, 'neutral', 'manda', 7, ('Manda', 'Manda'), ('Манда', 'Манда'),
             'hydra', 'Hydra', stats({'gold': 3000}, 250, 9, 22, 20, (35, 50), 1, 4000, 4800, (1, 4)),
             abilities={'poisonBite': {'type': 'SPELL_AFTER_ATTACK', 'subtype': 'spell.poison', 'val': 50}}, double_wide=True),
    creature(t, 'neutral', 'akatsukiMember', 7, ('Akatsuki Member', 'Akatsuki Members'), ('Член Акацуки', 'Члены Акацуки'),
             'enchanter', 'Enchanter', stats({'gold': 3500}, 180, 11, 24, 20, (40, 55), 1, 4600, 5600, (1, 4)),
             abilities={'deadly': {'type': 'DOUBLE_DAMAGE_CHANCE', 'val': 20},
                        'spellImmunity': {'type': 'LEVEL_SPELL_IMMUNITY', 'val': 2}}),
    # Tailed-beast bosses: level 10 like the Azure Dragon, never random monsters.
    creature(t, 'neutral', 'shukaku', 10, ('Shukaku', 'Shukaku'), ('Шукаку', 'Шукаку'),
             'ancientBehemoth', 'Greater Titan',
             stats({'gold': 20000, 'crystal': 10}, 800, 10, 40, 45, (50, 60), 1, 36000, 46000, (1, 1)),
             shots=8, projectile='wind-scythe',
             abilities={'sandArmor': {'type': 'GENERAL_DAMAGE_REDUCTION', 'subtype': 'damageTypeAll', 'val': 30},
                        'shooter': {'type': 'SHOOTER'}, 'windSandBlast': {'type': 'SHOOTS_ALL_ADJACENT'}},
             double_wide=True, extra=boss),
    creature(t, 'neutral', 'isobu', 10, ('Isobu', 'Isobu'), ('Исобу', 'Исобу'),
             'rustDragon', 'Rust Dragon',
             stats({'gold': 22000, 'mercury': 10}, 1100, 8, 38, 55, (45, 60), 1, 40000, 52000, (1, 1)),
             abilities={'coralArmor': {'type': 'GENERAL_DAMAGE_REDUCTION', 'subtype': 'damageTypeAll', 'val': 40},
                        'coralSpellArmor': {'type': 'SPELL_DAMAGE_REDUCTION', 'subtype': 'spellSchool.any', 'val': 50}},
             double_wide=True, extra=boss),
    creature(t, 'neutral', 'gyuki', 10, ('Gyuki', 'Gyuki'), ('Гьюки', 'Гьюки'),
             'chaosHydra', 'Chaos Hydra',
             stats({'gold': 26000, 'sulfur': 15}, 950, 14, 45, 40, (50, 70), 1, 50000, 66000, (1, 1)),
             abilities={'tentacles': {'type': 'ADDITIONAL_ATTACK', 'val': 2},
                        'tentacleGuard': {'type': 'UNLIMITED_RETALIATIONS'}},
             double_wide=True, extra=boss),
    creature(t, 'neutral', 'kurama', 10, ('Kurama', 'Kurama'), ('Курама', 'Курама'),
             'azureDragon', 'Azure Dragon',
             stats({'gold': 30000, 'sulfur': 20}, 1000, 16, 50, 45, (70, 90), 1, 58000, 80000, (1, 1)),
             abilities={'fireBreath': {'type': 'ATTACKS_ALL_ADJACENT'},
                        'fireImmunity': {'type': 'SPELL_SCHOOL_IMMUNITY', 'subtype': 'spellSchool.fire'},
                        'spellImmunity': {'type': 'LEVEL_SPELL_IMMUNITY', 'val': 3}},
             double_wide=True, idle=7, extra=boss),
])
for c in creatures.values():      # some borrowed graphics come with ranged parts we don't use
    if 'shots' not in c:
        c['graphics'].pop('missile', None)

# ------------------------------------------------------------------ lairs (map dwellings)

LAIRS = [  # (object id, English, Russian, creature, picture slug, ambient sound)
    ('rogueNinjaHideout', 'Rogue Ninja Hideout', 'Убежище нукенинов', 'rogueNinja', 'rogue-ninja', 'LOOPCAMP'),
    ('soundVillageOutpost', 'Sound Village Outpost', 'Застава Деревни Звука', 'soundNinja', 'sound-ninja', 'LOOPCAVE'),
    ('rainVillageTower', 'Rain Village Tower', 'Башня Деревни Дождя', 'rainNinja', 'rain-ninja', 'LOOPFOUN'),
    ('stoneVillageCliff', 'Stone Village Cliff', 'Утёс Деревни Камня', 'stoneNinja', 'stone-ninja', 'LOOPCAVE'),
    ('cloudVillageLighthouse', 'Cloud Village Lighthouse', 'Маяк Деревни Облака', 'cloudNinja', 'cloud-ninja', 'LOOPAIR'),
    ('curseMarkLair', 'Curse Mark Lair', 'Логово проклятой печати', 'curseMarkWarrior', 'curse-mark-warrior', 'LOOPCAVE'),
    ('zetsuTree', 'Zetsu Tree', 'Дерево Зецу', 'whiteZetsu', 'white-zetsu', 'LOOPELF'),
    ('catHideout', 'Cat Hideout', 'Убежище кошек', 'ninjaCat', 'ninja-cat', 'LOOPCAMP'),
    ('enmasCave', "Enma's Cave", 'Пещера Энмы', 'monkeyKingEnma', 'monkey-king-enma', 'LOOPCAVE'),
    ('mandasLair', "Manda's Lair", 'Логово Манды', 'manda', 'manda', 'LOOPMONS'),
    ('akatsukiHideout', 'Akatsuki Hideout', 'Убежище Акацуки', 'akatsukiMember', 'akatsuki-member', 'LOOPCAVE'),
]
dwellings = {'core:creatureGeneratorCommon': {'types': dict(
    own_dwelling_object(t, oid, en, ru, cid, slug, ambient) for oid, en, ru, cid, slug, ambient in LAIRS
    if has_map_sprite('dwellings', slug))}}

# ------------------------------------------------------------------ output

D = 'Content/config/%s/' % AREA
files = {'creatures': [write_json(D + 'creatures.json', creatures)],
         'objects': [write_json(D + 'dwellings.json', dwellings)]}
ru_file = write_json('Content/config/translations/russian-%s.json' % AREA, dict(sorted(t.ru.items())))
register(files, ru_file)
print('neutral: %d creatures, %d lairs, %d Russian strings' % (len(creatures), len(dwellings['core:creatureGeneratorCommon']['types']), len(t.ru)))
