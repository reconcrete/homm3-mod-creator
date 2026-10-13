"""Neutral creatures and tailed-beast bosses: generates Content/config/neutral/*.json from
the spec in ~/O/Projects/HoMM3-Naruto/Plans/Naruto-Mod-Neutral-Creatures.md ("Details").
So far only Kurama exists (added early, 2026-10-13, to test the first rendered animation);
the rest of the area is M5.
Run: python3 tools/towns/neutral.py   (then tools/check.sh)"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from townkit import *

AREA = 'neutral'
t = Texts()

def stats(cost, hp, speed, att, dfn, dmg, growth, fight, ai, amount):
    return dict(cost=cost, hp=hp, speed=speed, attack=att, defense=dfn, dmg=dmg,
                growth=growth, fight=fight, ai=ai, amount=amount)

creatures = dict([
    # Tailed-beast boss, Azure Dragon class (1000 HP, 50/50, 70-80, speed 19, 30000 + 20 mercury).
    # Sounds and (if no own sprite exists) pictures are borrowed from the Azure Dragon.
    creature(t, 'neutral', 'kurama', 10, ('Kurama', 'Kurama'), ('Курама', 'Курама'),
             'azureDragon', 'Azure Dragon',
             stats({'gold': 30000, 'sulfur': 20}, 1000, 16, 50, 45, (70, 90), 1, 58000, 80000, (1, 1)),
             abilities={
                 'fireBreath': {'type': 'ATTACKS_ALL_ADJACENT'},
                 'fireImmunity': {'type': 'SPELL_SCHOOL_IMMUNITY', 'subtype': 'spellSchool.fire'},
                 'spellImmunity': {'type': 'LEVEL_SPELL_IMMUNITY', 'val': 3},
             },
             double_wide=True, idle=7,
             extra={'excludeFromRandomization': True}),
])

D = 'Content/config/%s/' % AREA
files = {'creatures': [write_json(D + 'creatures.json', creatures)]}
ru_file = write_json('Content/config/translations/russian-%s.json' % AREA, dict(sorted(t.ru.items())))

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
print('neutral: %d creatures, %d Russian strings' % (len(creatures), len(t.ru)))
