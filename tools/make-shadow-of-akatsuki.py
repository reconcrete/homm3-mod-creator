"""Single-player story map "Naruto: Shadow of the Akatsuki" (36x36, one level, red vs two AIs).
python3 tools/make-shadow-of-akatsuki.py [--seed N] [--ascii]  -> Maps/naruto-shadow-of-akatsuki.vmap

The Akatsuki stole Shukaku; Naruto (red, Leaf Outpost) frees Kakashi, takes quests from Iruka,
Jiraiya and Chiyo, and breaks into the Akatsuki hideout to defeat Shukaku within eight weeks.
Sasori (tan, Suna town) and Kisame (blue, Kiri town) are allied AIs.

  +------------------------+--+-----------------------+
  | A Leaf Outpost (red)   |  | B Forest of Death      |   A-B, A-C, C1-C2, B-D, C2-D: passages
  |   Iruka, Zetsu spies,  |AB|   Kakashi's cell,      |   through the walls, each guarded by a
  |   cat pocket           |  |   Jiraiya, Manda       |   monster standing in it.
  +----------AC------------+  +---------BD------------+   D-E: a quest guard that opens only for
  | C1 valley  |  C2       |CD| D Shark Bay (blue)     |   Naruto at level 8 (the Akatsuki barrier).
  |  entrance  |  Chiyo    |  |   Kisame, the necklace +---------DE---------+
  +---inner----+  Sasori,  |  | E Akatsuki hideout: Deidara, then Shukaku |
  | C2 Puppet Valley (tan) |  |                                           |
  +------------------------+--+-------------------------------------------+

The AIs can't take the story away from red: every quest object and the story events stand behind
red-only gates or ask red-only quests (allOf sub-limiter "colors": ["red"]), and the quests ask for
artifacts that the targets carry, so red can win an item back from an AI hero who took it first.
Sasori starts at the far end of Puppet Valley, two guards away from the Leaf Outpost.

Story texts are English and Russian (VCMI 1.7 maps carry english.json / russian.json, picked by
the game language). Built with tools/handmap.py; the script checks that every object can be
reached, that each area opens only through its guard or quest gate, that no object sits on a
blocked tile and that every tile under a monster's sprite can be clicked.

Can't be set from a map: VCMI 1.7.5's JSON map format has no game-setting overrides (only H3M/HotA
maps and random-map templates call CMap::overrideGameSettings), so monthly wandering monsters stay
on unless "settings": {"creatures": {"allowRandomSpecialWeeks": false}} goes into mod.json, which
would switch special weeks off in every game with the mod."""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handmap import HandMap, Texts, BASE_HEADER, MAPS, MOD, EMPTY_TEXT, HEROES, lib, h3, road_line, mask_cells

N = 36
NAME = 'naruto-shadow-of-akatsuki'
OUT = os.path.join(MAPS, NAME + '.vmap')
ap = argparse.ArgumentParser()
ap.add_argument('--seed', type=int, default=11)
ap.add_argument('--ascii', action='store_true', help='print a text picture of the map')
args = ap.parse_args()
m = HandMap(N, args.seed)
m.clear_sprites = True
T = Texts()
wall = m.wall
j = lambda o: json.loads(json.dumps(o))
mod = lambda i: MOD + ':' + i

# ------------------------------------------------------------------ walls, passages, roads

for y in range(N):                                   # A|B and C|D
    wall |= {(17, y), (18, y)}
for x in range(0, 17):                               # A / C
    wall |= {(x, 16), (x, 17)}
for x in range(19, N):                               # B / D, D / E, and the inner wall of E
    wall |= {(x, 13), (x, 14), (x, 26), (x, 27), (x, 31)}
# C: the valley entrance (C1, x 0-9, y 18-23) is walled off from the rest of the valley (C2)
wall |= {(x, 24) for x in range(0, 11)} | {(10, y) for y in range(18, 25)}
# Kakashi's cell in B's north-east corner: a guarded gap at x 30, then a Leaf seal (red-only quest
# guard) at (31, 3), then a one-tile corridor (32, 3) where the ambush waits, then the prison
wall |= {(30, y) for y in range(0, 6)} | {(x, 5) for x in range(30, N)} | {(31, y) for y in range(0, 5)}
wall |= {(32, 0), (32, 1), (32, 2), (32, 4)}
# the cats' den in A's south-east corner
wall |= {(12, y) for y in range(11, 16)} | {(x, 11) for x in range(12, 17)}

# A passage is a gap in a wall with its guard on the gap tile nearest the side a hero comes from
# first, so the guard zone covers the whole gap and the monster's sprite (which spreads up and left
# of its tile) lies on open ground on that side. The gaps between areas are two tiles wide, so no
# single tile is the only way through. Pockets use 2-tile gaps the same way.
PASSAGES = {   # name: (gap tiles, guard tile)
    'AB': ([(17, 6), (18, 6), (17, 7), (18, 7)], (17, 7)),
    'AC': ([(7, 16), (8, 16), (7, 17), (8, 17)], (8, 16)),
    'inner': ([(7, 24), (8, 24)], (8, 24)),               # C1 / C2: Sasori's checkpoint
    'BD': ([(26, 13), (27, 13), (26, 14), (27, 14)], (27, 13)),
    'CD': ([(17, 22), (18, 22), (17, 23), (18, 23)], (17, 23)),
    'cave': ([(22, 31), (23, 31)], (23, 31)),            # E: the way down to Shukaku
    'prison': ([(30, 2), (30, 3)], (30, 3)),             # B: the guards outside Kakashi's cell
    'cats': ([(14, 11), (15, 11)], (15, 11)),            # A: the cats' den
}
GATES = {'barrier': (30, 26), 'seal': (31, 3)}           # quest guards in one-tile gaps
for gap, _ in PASSAGES.values():
    wall -= set(gap)
wall -= {(30, 26), (30, 27), (31, 3), (32, 3)}

for line in ([(5, 6), (5, 9), (12, 9), (12, 7), (26, 7), (26, 21), (30, 21), (30, 29), (23, 29), (23, 33), (28, 33)],
             [(5, 9), (5, 12), (8, 12), (8, 33), (5, 33)],            # A -> C1 -> C2 and Sasori's gate
             [(8, 26), (16, 26), (16, 23), (26, 23), (26, 21)],      # C2 -> D
             [(26, 5), (26, 3), (29, 3)]):                           # B: the path to Kakashi's cell
    m.set_road(road_line(line))

# ------------------------------------------------------------------ object builders

LIMITER = dict(j(lib('seerHut/0')[1]['quest']['limiter']), artifacts=[])   # the library's hut asked for a pendant
REWARD = dict(j(lib('seerHut/0')[1]['rewardable']['info'][0]['reward']), creatures=[])     # ... and gave archers

def limiter(**kw):
    return dict(j(LIMITER), **kw)

RED_ONLY = [limiter(colors=['red'])]   # as an allOf sub-limiter: the quest keeps its own name and texts

def reward(exp=0, artifacts=(), creatures=(), primary=(0, 0, 0, 0), resources=None):
    r = dict(j(REWARD), heroExperience=exp, primary=list(primary),
             creatures=[{'amount': n, 'type': mod(c)} for c, n in creatures])
    if artifacts:
        r['artifacts'] = [mod(a) for a in artifacts]
    if resources:
        r['resources'] = resources
    return r

def rewardable(key, message, rew):
    """The 'rewardable' block VCMI writes for Pandora's boxes and events, with one reward."""
    opt = j(lib('pandoraBox/object')[1])
    info = opt['rewardable']['info'][0]
    info['message'] = T.say(key, *message) if message else j(EMPTY_TEXT)
    info['reward'] = rew
    return opt

def quest(key, first, nxt, done, mission):
    q = j(lib('seerHut/0')[1]['quest'])
    q['firstVisitText'] = T.say(key + '.first', *first)
    q['nextVisitText'] = T.say(key + '.next', *nxt)
    q['completedText'] = T.say(key + '.completed', *done)
    q['limiter'] = limiter(**mission)
    return q

def seer(key, at, rew, *texts, artifact, sub=0):
    """A seer hut that wants an artifact, for red only."""
    tpl, opt = lib('seerHut/%d' % sub)
    opt['quest'] = quest(key, *texts, mission={'artifacts': [mod(artifact)], 'allOf': j(RED_ONLY)})
    opt['rewardable']['info'][0]['reward'] = rew
    return m.add('seerHut', str(sub), tpl, at, opt, near=1)

def gate(key, at, *texts, mission):
    """A quest guard: blocks its tile until the quest is done, then disappears."""
    o = m.add('questGuard', 'object', h3('avxbor80'), at, {'quest': quest(key, *texts, mission=mission)}, near=0, entrance=False)
    m.gates.add(at)
    m.open.add(at)        # paths to what lies behind it go through it
    return o

def event(key, at, message, rew=None, army=(), before=None):
    """A story event (invisible, for the human red player only, gone after the first visit)."""
    opt = rewardable(key, message, rew or j(REWARD))
    opt['guardMessage'] = T.say(key + '.ambush', *before) if before else j(EMPTY_TEXT)
    opt.update({'aIActivable': False, 'humanActivable': True, 'removeAfterVisit': True, 'availableFor': ['red']})
    if army:
        opt['army'] = [{'amount': n, 'type': mod(c)} for c, n in army]
    return m.add('event', 'object', dict(h3('AVZevnt0'), mask=['A']), at, opt, near=0, entrance=False)   # VCMI makes events 1x1

def guard(cid, amount, at, key=None, text=None, carries=None, near=0):
    """A monster that never flees or joins; `text` is shown before the fight, `carries` is an
    artifact the winner takes."""
    extra = {'character': 'savage', 'neverFlees': True, 'noGrowing': True}
    if text:
        extra['rewardMessage'] = T.say(key, *text)
    if carries:
        extra['rewardArtifact'] = mod(carries)
    return m.monster(cid, amount, at, near=near, **extra)

def pandora(key, at, message, rew):
    tpl, _ = lib('pandoraBox/object')
    return m.add('pandoraBox', 'object', tpl, at, rewardable(key, message, rew))

# ------------------------------------------------------------------ towns and heroes

HOME = ['villageHall', 'tavern', 'fort', 'dwellingLvl1', 'dwellingLvl2']
leaf = m.town('konohagakure', (5, 5), 'red', HOME, [('academyStudent', 20), ('genin', 8)],
              name=T.id('town.leafOutpost.name', 'Leaf Outpost', 'Застава Листа'))
puppets = m.town('sunagakure', (5, 32), 'tan', ['villageHall', 'tavern', 'fort', 'mageGuild1', 'dwellingLvl1', 'dwellingLvl2'],
                 [('sunaGenin', 16), ('woodenPuppet', 6)],
                 name=T.id('town.puppetValley.name', 'Puppet Valley', 'Долина марионеток'))
bay = m.town('kirigakure', (30, 20), 'blue', ['villageHall', 'townHall', 'tavern', 'fort', 'mageGuild1',
                                              'dwellingLvl1', 'dwellingLvl2', 'dwellingLvl3', 'dwellingLvl4'],
             [('mistGenin', 24), ('hunterNin', 10), ('hozukiBrawler', 6), ('summonedShark', 3)],
             name=T.id('town.sharkBay.name', 'Shark Bay', 'Акулья бухта'))
m.reserve([(5, 6), (5, 33), (30, 21)])
naruto = m.hero('narutoUzumaki', 'red', (5, 7), [('academyStudent', 30), ('genin', 12), ('ninjaHound', 8)])
m.hero('sasori', 'tan', (5, 34), [('sunaGenin', 12), ('woodenPuppet', 6), ('windKunoichi', 3)], experience=1000)
m.hero('kisameHoshigaki', 'blue', (31, 22), [('mistGenin', 20), ('hunterNin', 10), ('hozukiBrawler', 5), ('summonedShark', 3)], experience=4000)

# ------------------------------------------------------------------ passage guards

guard('rogueNinja', 15, PASSAGES['AB'][1])
guard('soundNinja', 14, PASSAGES['AC'][1])
guard('stoneNinja', 10, PASSAGES['inner'][1], 'monster.checkpoint.message',
      ('Stone ninja hired by Sasori hold the road between the valley entrance and his town.',
       'Ниндзя Камня, нанятые Сасори, перекрыли дорогу между входом в долину и его городом.'))
guard('mistSwordsman', 4, PASSAGES['BD'][1])
guard('greatShark', 6, PASSAGES['CD'][1])

# ------------------------------------------------------------------ A: the Leaf Outpost (easy)

guard('whiteZetsu', 30, (5, 14), 'monster.zetsu.message',
      ('The White Zetsu spies try to melt into the trees, clutching their loot.',
       'Шпионы Белые Зецу пытаются раствориться среди деревьев, прижимая к себе добычу.'), carries='ichirakuRamenCoupon')
seer('seer.iruka', (9, 11), reward(1500, ['leafForeheadProtector']),
     ('Iruka: "Naruto! White Zetsu spies are watching the outpost from the woods to the south, and they stole my '
      'Ichiraku Ramen Coupon. Get it back, and I\'ll give you something you\'ve earned."',
      'Ирука: «Наруто! Из леса к югу за заставой следят шпионы Белые Зецу, и они украли мой купон на рамен Ичираку. '
      'Верни его, и я дам тебе то, что ты заслужил.»'),
     ('Iruka: "The Zetsu spies still have my coupon. They hide in the woods south of the outpost."',
      'Ирука: «Мой купон всё ещё у шпионов Зецу. Они прячутся в лесу к югу от заставы.»'),
     ('Iruka: "You got it back! Ramen is on me next time. And take my forehead protector: you\'re a real shinobi now."',
      'Ирука: «Ты его вернул! В следующий раз рамен за мой счёт. И возьми мой протектор: теперь ты настоящий шиноби.»'),
     artifact='ichirakuRamenCoupon')
guard('ninjaCat', 12, PASSAGES['cats'][1])
m.open.add(PASSAGES['cats'][1])
m.artifact('kunai', (14, 14), near=0)
m.artifact('chakraPills', (16, 13), near=0)
m.thing('treasureChest/treasureChest', (13, 13), near=0)
m.thing('mine/sawmill', (2, 11))
m.thing('mine/orePit', (13, 3))
m.dwelling('ninjaAcademy', (9, 5))
m.dwelling('inuzukaKennels', (2, 15))
m.dwelling('zetsuTree', (10, 15))
m.thing('learningStone/learningStone', (15, 1))
guard('rogueNinja', 8, (16, 3))
m.thing('campfire/campfire', (8, 8))
m.thing('treasureChest/treasureChest', (1, 8))
for res, at in (('wood', (3, 9)), ('ore', (15, 5)), ('gold', (7, 14)), ('wood', (11, 13)), ('ore', (1, 3))):
    m.thing('resource/' + res, at)
m.artifact('gamaChanWallet', (9, 1))

# ------------------------------------------------------------------ B: the Forest of Death (middle)

guard('curseMarkWarrior', 6, PASSAGES['prison'][1], 'monster.captors.message',
      ('Orochimaru\'s Curse Mark warriors guard the cell where Kakashi is chained.',
       'Воины проклятой печати Орочимару охраняют темницу, где прикован Какаши.'))
m.open.add(PASSAGES['prison'][1])
gate('gate.seal', GATES['seal'],
     ('A Leaf sealing tag locks Kakashi\'s cell from outside: he sealed himself in to keep the Sound ninja from '
      'taking him away. Only Leaf chakra can release it.',
      'Печать Листа запирает темницу Какаши снаружи: он запечатал себя сам, чтобы ниндзя Звука не увели его. '
      'Снять её может только чакра Листа.'),
     ('The Leaf seal holds. Only a Leaf ninja can release it.', 'Печать Листа держится. Снять её может только ниндзя Листа.'),
     ('The seal knows your chakra and fades. Inside, something moves in the dark...',
      'Печать узнаёт вашу чакру и гаснет. Внутри, в темноте, что-то шевелится...'),
     mission={'colors': ['red']})
event('event.ambush', (32, 3),
      ('The ambush is beaten. The Sound ninja\'s packs hold gold and a map of the forest paths. Kakashi is just ahead.',
       'Засада отбита. В сумках ниндзя Звука нашлось золото и карта лесных троп. Какаши совсем рядом.'),
      reward(2000, resources={'gold': 1000}), army=[('soundNinja', 5), ('soundNinja', 5), ('rainNinja', 5)],
      before=('Sound ninja were waiting inside the cell: an ambush!', 'Внутри темницы поджидали ниндзя Звука: засада!'))
tpl, opt = lib('prison/prison')
opt.update({'experience': 5000, 'type': mod('kakashiHatake'), 'army': [{'amount': 10, 'type': mod('genin')}, {'amount': 8, 'type': mod('ninjaHound')}]})
m.add('prison', 'prison', tpl, (35, 3), opt, near=0)
m.thing('treasureChest/treasureChest', (33, 0), near=0)
guard('manda', 1, (32, 10), 'monster.manda.message',
      ('Manda rises, hissing, coiled around Orochimaru\'s snake contract. The great snake does not like visitors.',
       'Манда поднимается с шипением, обвившись вокруг контракта змей Орочимару. Большой змей не любит гостей.'),
      carries='summoningContractSnakes')
seer('seer.jiraiya', (22, 2), reward(2500, ['hokageCloak'], [('toadWarrior', 2)]),
     ('Jiraiya: "Off to fight the Akatsuki, are you? Then show me what you\'ve got. Orochimaru\'s great snake Manda '
      'nests in the south-east of this forest and guards his snake contract. Bring me that contract, and you get the '
      'Fourth Hokage\'s cloak and two of my toads."',
      'Джирайя: «Собрался драться с Акацуки? Тогда покажи, на что способен. На юго-востоке этого леса гнездится Манда, '
      'большой змей Орочимару, и стережёт его контракт змей. Принеси мне этот контракт — и получишь плащ Четвёртого '
      'Хокаге и двух моих жаб.»'),
     ('Jiraiya: "No contract yet? Manda keeps it in the south-east of the forest."',
      'Джирайя: «Контракта всё нет? Манда держит его на юго-востоке леса.»'),
     ('Jiraiya: "Ha! Not bad at all. That contract won\'t serve Orochimaru again. This was Minato\'s cloak. Wear it '
      'well, and take my toads with you."',
      'Джирайя: «Ха! Совсем неплохо. Этот контракт больше не послужит Орочимару. А это плащ Минато. Носи его с честью '
      'и возьми с собой моих жаб.»'),
     artifact='summoningContractSnakes', sub=1)
guard('soundNinja', 10, (21, 11), 'monster.hat.message',
      ('These Sound ninja raided a Leaf supply camp. One of them wears a Hokage Hat.',
       'Эти ниндзя Звука разграбили лагерь снабжения Листа. На одном из них Шляпа Хокаге.'), carries='hokageHat')
m.dwelling('hyugaCompound', (29, 9))
m.dwelling('soundVillageOutpost', (23, 4))
m.thing('mine/goldMine', (34, 7))
m.thing('mine/crystalCavern', (23, 10))
m.artifact('chuninVest', (35, 12))
m.artifact('explosiveTags', (19, 0))
for res, at in (('gold', (28, 11)), ('crystal', (20, 4)), ('wood', (31, 7)), ('gems', (24, 0))):
    m.thing('resource/' + res, at)

# ------------------------------------------------------------------ C: Puppet Valley, Sasori (middle)

# C1, the valley entrance
m.dwelling('catHideout', (2, 20))
m.thing('mine/sulfurDune', (2, 22))
m.thing('resource/sulfur', (6, 20))
m.thing('treasureChest/treasureChest', (5, 22))
# C2, the rest of the valley
guard('humanPuppet', 5, (13, 32), 'monster.hiruko.message',
      ('Sasori\'s human puppets drag Hiruko, his old shell, behind them.',
       'Человеческие марионетки Сасори тащат за собой Хируко, его старую оболочку.'), carries='hiruko')
seer('seer.chiyo', (13, 20), reward(3000, primary=(2, 2, 0, 0)),
     ('Chiyo: "Sasori is my grandson, and he has become a monster. His human puppets carry Hiruko, his old shell, in '
      'the south-east of the valley. Bring it to me, and I will teach you how to fight his puppets."',
      'Чиё: «Сасори — мой внук, и он стал чудовищем. Его человеческие марионетки таскают Хируко, его старую оболочку, на '
      'юго-востоке долины. Принеси её мне, и я научу тебя сражаться с его марионетками.»'),
     ('Chiyo: "Hiruko is still with Sasori\'s puppets in the south-east of the valley. If Sasori took it, take it from him."',
      'Чиё: «Хируко всё ещё у марионеток Сасори на юго-востоке долины. Если его забрал Сасори — отбери у него.»'),
     ('Chiyo: "So this is what is left of his first puppet... Listen well: this is how Sasori fights."',
      'Чиё: «Вот всё, что осталось от его первой марионетки... Слушай внимательно: вот как сражается Сасори.»'),
     artifact='hiruko', sub=2)
guard('windKunoichi', 8, (15, 29), carries='temarisGiantFan')
m.dwelling('uchihaDistrict', (12, 28))
m.dwelling('rogueNinjaHideout', (10, 34))
m.thing('mine/gemPond', (14, 34))
m.thing('treasureChest/treasureChest', (16, 19))
m.thing('campfire/campfire', (11, 31))
m.artifact('soldierPills', (1, 35))
m.artifact('sandForeheadProtector', (11, 19))
for res, at in (('gems', (14, 24)), ('gold', (7, 35)), ('wood', (16, 31)), ('mercury', (1, 29)), ('ore', (3, 26))):
    m.thing('resource/' + res, at)

# ------------------------------------------------------------------ D: Shark Bay, Kisame (hard)

guard('swordsmanOfTheSeven', 3, (34, 17), 'monster.necklace.message',
      ('Kisame\'s Swordsmen of the Seven guard the First Hokage\'s Necklace, taken from a Leaf ninja.',
       'Мечники Семи из отряда Кисаме охраняют Ожерелье Первого Хокаге, отнятое у ниндзя Листа.'), carries='firstHokagesNecklace')
gate('gate.barrier', GATES['barrier'],
     ('An Akatsuki barrier seals the way to the hideout. It gives way only to the Nine-Tails\' chakra: Naruto himself '
      'must touch it, and he must be at least level 8.',
      'Барьер Акацуки закрывает путь к убежищу. Он уступит только чакре Девятихвостого: коснуться его должен сам Наруто, '
      'и не ниже 8-го уровня.'),
     ('The barrier holds. Only Naruto, at level 8 or higher, can break it.',
      'Барьер держится. Сломать его может только Наруто не ниже 8-го уровня.'),
     ('Naruto\'s chakra flares up, and the barrier cracks open! Beyond it lies the Akatsuki hideout.',
      'Чакра Наруто вспыхивает, и барьер раскалывается! За ним — убежище Акацуки.'),
     mission={'heroLevel': 8, 'heroes': [mod('narutoUzumaki')]})     # Naruto is red's alone; no AI can pass
m.dwelling('medicalCorps', (21, 17))
m.dwelling('enmasCave', (22, 21))
m.dwelling('cloudVillageLighthouse', (34, 24))
guard('hozukiBrawler', 12, (23, 17))
m.thing('mine/alchemistLab', (21, 24))
m.thing('mine/goldMine', (25, 17))
m.artifact('hunterNinMask', (19, 15))
m.artifact('kubikiribocho', (35, 15))
for res, at in (('mercury', (24, 25)), ('gold', (33, 21)), ('ore', (28, 24)), ('crystal', (19, 20))):
    m.thing('resource/' + res, at)

# ------------------------------------------------------------------ E: the Akatsuki hideout (the end)

event('event.hideout', (30, 27),
      ('The Akatsuki hideout. In the cave below, the ritual has driven Shukaku mad. Deidara of the Akatsuki guards the way down.',
       'Убежище Акацуки. В пещере внизу ритуал свёл Шукаку с ума. Путь вниз охраняет Дейдара из Акацуки.'))
pandora('pandora.gamabunta', (34, 29),
        ('A summoning scroll left by Jiraiya. Gamabunta, chief of the toads, answers your call!',
         'Свиток призыва, оставленный Джирайей. На зов отвечает Гамабунта, глава жаб!'),
        reward(creatures=[('gamabunta', 1)]))
m.thing('magicWell/magicWell', (20, 29))
guard('akatsukiMember', 4, PASSAGES['cave'][1], 'monster.deidara.message',     # 4: one was weaker than the passage guards
      ('Deidara and his clay clones block the way: "You want the One-Tail? Then let me show you true art. Art is an explosion!"',
       'Дейдара и его глиняные клоны преграждают путь: «Тебе нужен Однохвостый? Тогда я покажу тебе настоящее искусство. Искусство — это взрыв!»'))
shukaku = guard('shukaku', 1, (28, 34), 'monster.shukaku.message',
                ('Shukaku, the One-Tail, tears free of the Akatsuki seals!', 'Шукаку, Однохвостый, вырывается из печатей Акацуки!'))

# ------------------------------------------------------------------ obstacles and checks

def picture():
    marks = {at: {'monster': 'M', 'town': 'T', 'hero': 'H', 'event': 'e', 'questGuard': 'Q', 'seerHut': 'S', 'artifact': 'a',
                  'prison': 'P', 'pandoraBox': 'p'}.get(o['type'], 'o') for at, o, tpl in m.visits}
    return m.ascii(marks)

try:
    m.keep_monsters_clickable()
    m.reserve_paths()
    m.dress()
except AssertionError:
    print(picture())
    raise

start = m.at[naruto['instanceName']]
# no object on a blocked tile: each visit tile is blocked by its own object only (events by nothing)
blockers = {}
for o in m.objects:
    for dx, dy, ch in mask_cells(o['template']):
        if ch in 'BA' and o['type'] != 'event':
            blockers.setdefault((o['x'] + dx, o['y'] + dy), []).append(o['instanceName'])
on_blocked = [(o['instanceName'], at, blockers.get(at)) for at, o, tpl in m.visits
              if blockers.get(at, []) != ([] if o['type'] == 'event' else [o['instanceName']])]
assert not on_blocked, 'objects on a blocked tile: %s' % on_blocked
unreachable = m.unreachable([start])
assert not unreachable, 'cannot be reached: %s' % unreachable
# every area opens only through its own guards or gate: with those standing and every other guard
# beaten, a hero from the Leaf Outpost can't get in (B, C and D each have two ways in)
AREAS = {'B': (26, 4), 'C1': (8, 20), 'C2': (8, 28), 'D': (26, 18), 'E': (30, 29), "Kakashi's cell": (32, 3),
         "the prison": (34, 4), "cats' den": (13, 14), "Shukaku's cave": (25, 33)}   # road or reserved tiles (never under an obstacle)
everywhere = m.reach(start, True)
assert all(t in everywhere for t in AREAS.values()), 'an area sample tile is blocked: %s' % [a for a, t in AREAS.items() if t not in everywhere]
home = m.reach(start, False)
leaks =[a for a, t in AREAS.items() if t in home]
assert not leaks, 'the Leaf Outpost is open to %s without a fight' % leaks
for area, guards in (('B', ['AB', 'BD']), ('C1', ['AC', 'inner']), ('C2', ['inner', 'CD']), ('D', ['BD', 'CD']),
                     ("Kakashi's cell", ['prison']), ("cats' den", ['cats']), ("Shukaku's cave", ['cave'])):
    seen = m.reach(start, False, ignore=m.monsters - {PASSAGES[g][1] for g in guards}, gates_open=True)
    assert AREAS[area] not in seen, '%s is open without beating the %s guard' % (area, ' or '.join(guards))
seen = m.reach(start, False, ignore=m.monsters, gates_open=False)
closed = [a for a in ('E', "Kakashi's cell", 'the prison') if AREAS[a] in seen]
assert not closed, '%s open without their quest guard' % closed
# Sasori's way to the outpost: two guards (the checkpoint and the valley entrance) stand in it
sasori_free = m.reach(m.at['hero_2'], False, ignore=m.monsters - {PASSAGES['inner'][1], PASSAGES['AC'][1]})
assert start not in sasori_free, 'Sasori reaches the Leaf Outpost past fewer than two guards'
bad = m.unclickable(start)
if bad:
    print(picture())
assert not bad, 'monster sprite tiles that cannot be clicked (monster, tile): %s' % bad

# ------------------------------------------------------------------ header: story, timed events, victory and loss

say = T.say
header = j(BASE_HEADER)
for k in ('allowedAbilities', 'allowedArtifacts', 'allowedSpells'):   # the base map lists only original content
    del header[k]
# taverns offer our heroes only (the base map's original ones stay out), minus the story characters,
# the Akatsuki members and the heroes placed on the map
STORY = ('narutoUzumaki', 'kakashiHatake', 'jiraiya', 'tsunade', 'minatoNamikaze', 'orochimaru', 'itachiUchiha',
         'chiyo', 'sasori', 'kisameHoshigaki', 'gaara')
assert all(h in HEROES for h in STORY)
header['allowedHeroes'] = {'anyOf': [mod(h) for h in HEROES if h not in STORY]}
header['name'] = say('header.name', "Naruto: Akatsuki's Shadow", 'Наруто: Тень Акацуки')   # the scenario header shows about 27 characters
header['description'] = say('header.description',
    'The Akatsuki have stolen Shukaku, the One-Tail, from Sunagakure. Sasori holds Puppet Valley in the south, Kisame '
    'holds Shark Bay in the east, and in their hideout behind Shark Bay the extraction ritual has begun: in eight weeks '
    'it will be over. Tsunade sends Naruto from the Leaf Outpost. Kakashi went ahead to scout and has not come back. '
    'Free him, grow strong (the barrier gives way only to Naruto at level 8) and stop the ritual.\n\n'
    'Win: defeat Shukaku. Lose: Naruto falls, or day 57 comes.',
    'Акацуки похитили Шукаку, Однохвостого, из Сунагакуре. Сасори держит Долину марионеток на юге, Кисаме — Акулью '
    'бухту на востоке, а в их убежище за бухтой начался ритуал извлечения: через восемь недель он завершится. Цунаде '
    'посылает Наруто с Заставы Листа. Какаши ушёл на разведку и не вернулся. Освободите его, наберитесь сил (барьер '
    'уступит только Наруто 8-го уровня) и сорвите ритуал.\n\n'
    'Победа: одолеть Шукаку. Поражение: Наруто погибнет или наступит 57-й день.')
header['author'] = say('header.author', 'Naruto Heroes', 'Naruto Heroes')
header['mapVersion'] = say('header.mapVersion', '1.0', '1.0')
header['difficulty'] = 'NORMAL'
main_town = lambda t: {'generateHero': False, 'l': 0, 'x': t['x'], 'y': t['y']}
header['players'] = {
    'red': {'allowedFactions': {'anyOf': [mod('konohagakure')]}, 'canPlay': 'PlayerOrAI', 'mainTown': main_town(leaf)},
    'blue': {'allowedFactions': {'anyOf': [mod('kirigakure')]}, 'canPlay': 'AIOnly', 'mainTown': main_town(bay)},
    'tan': {'allowedFactions': {'anyOf': [mod('sunagakure')]}, 'canPlay': 'AIOnly', 'mainTown': main_town(puppets)},
}
header['teams'] = [['red'], ['blue', 'tan']]           # the two Akatsuki members are allies

def timed(name, day, text, players=('red',), human=True, resources=None):
    """A message (and resources) on the given day (VCMI counts firstOccurrence from 0 = day 1)."""
    e = {'name': name, 'message': say('event.%s.message' % name, *text), 'players': list(players),
         'humanAffected': int(human), 'computerAffected': int(not human), 'firstOccurrence': day - 1,
         'nextOccurrence': 0, 'deletedObjectsInstances': []}
    if resources:
        e['resources'] = resources
    return e

header['events'] = [
    timed('tsunade', 1, ('A letter from Tsunade: "Naruto, the Akatsuki have stolen Shukaku, the One-Tail. Sasori holds '
        'Puppet Valley to the south, Kisame holds Shark Bay to the east, and their hideout lies behind Shark Bay, sealed by '
        'a barrier. Only your chakra can break it, and only once you are strong enough: level 8. The ritual will be over '
        'in eight weeks. Kakashi went ahead to scout and has gone silent. Beware Sasori: his valley lies just south of '
        'the outpost, behind the Sound ninja on the southern road. Keep a garrison in the outpost, and don\'t take Naruto '
        'south before his army is ready."',
        'Письмо от Цунаде: «Наруто, Акацуки похитили Шукаку, Однохвостого. Сасори держит Долину марионеток на юге, '
        'Кисаме — Акулью бухту на востоке, а за бухтой их убежище, закрытое барьером. Сломать его может только твоя '
        'чакра, и только когда ты станешь достаточно сильным: 8-й уровень. Через восемь недель ритуал завершится. Какаши '
        'ушёл на разведку и молчит. Берегись Сасори: его долина сразу к югу от заставы, за ниндзя Звука на южной дороге. '
        'Оставь в заставе гарнизон и не веди Наруто на юг, пока его армия не готова.»')),
    timed('pakkun', 3, ('Pakkun, Kakashi\'s ninja dog, limps into the outpost: "Kakashi was ambushed by Orochimaru\'s '
        'Sound ninja. They keep him in the Forest of Death, east of here, in its north-east corner. Jiraiya is somewhere '
        'in that forest too."',
        'На заставу, прихрамывая, приходит Паккун, пёс-ниндзя Какаши: «Какаши попал в засаду ниндзя Звука Орочимару. '
        'Его держат в Лесу Смерти, к востоку отсюда, в его северо-восточном углу. Где-то в том лесу и Джирайя.»')),
    timed('chiyo', 5, ('A message from old Chiyo, the elder of Sunagakure: she hides from her grandson Sasori in a hut in '
        'the north-east of Puppet Valley and knows his weaknesses. Look for her once you are past the valley entrance.',
        'Весточка от старой Чиё, старейшины Сунагакуре: она прячется от своего внука Сасори в хижине на северо-востоке '
        'Долины марионеток и знает его слабые места. Найдите её, когда пройдёте вход в долину.')),
    timed('supplies', 8, ('Shizune sends supplies from Konoha: "Lady Tsunade says: spend them wisely."',
        'Шизуне присылает припасы из Конохи: «Госпожа Цунаде велела потратить их с умом.»'),
        resources={'gold': 2000, 'wood': 5, 'ore': 5}),
    timed('scouts', 15, ('Scouts report: Sasori and Kisame have received reinforcements from the Akatsuki. Expect '
        'attacks on the outpost.', 'Разведчики докладывают: Сасори и Кисаме получили подкрепления от Акацуки. Ждите '
        'нападения на заставу.')),
    timed('reinforcements', 15, ('Akatsuki reinforcements arrive.', 'Прибывают подкрепления Акацуки.'),
        players=('blue', 'tan'), human=False, resources={'gold': 4000, 'wood': 8, 'ore': 8}),
    timed('materials', 22, ('Tsunade sends rare materials from the Konoha storehouses.',
        'Цунаде присылает редкие материалы со складов Конохи.'),
        resources={'gold': 1500, 'mercury': 3, 'sulfur': 3, 'crystal': 3, 'gems': 3}),
    timed('halfway', 29, ('Four weeks are gone. The ritual is half done: Shukaku has four weeks left.',
        'Прошло четыре недели. Ритуал наполовину завершён: у Шукаку осталось четыре недели.')),
    timed('lastWeek', 50, ('Only one week left! After day 56 the Akatsuki will finish the ritual, and Shukaku will be lost.',
        'Осталась всего неделя! После 56-го дня Акацуки завершат ритуал, и Шукаку будет потерян.')),
]
header['rumors'] = [{'name': 'rumor%d' % i, 'text': say('header.rumor.%d.text' % i, en, ru)} for i, (en, ru) in enumerate([
    ('They say Jiraiya, the Toad Sage, is peeping at the hot springs in the Forest of Death again.',
     'Говорят, Джирайя, Жабий Отшельник, снова подглядывает за горячими источниками в Лесу Смерти.'),
    ('Old Chiyo of Sunagakure has sworn to stop her grandson Sasori.',
     'Старая Чиё из Сунагакуре поклялась остановить своего внука Сасори.'),
    ('Kisame\'s Swordsmen of the Seven took a necklace from a Leaf ninja: the First Hokage\'s, they say.',
     'Мечники Семи из отряда Кисаме отняли у ниндзя Листа ожерелье — говорят, самого Первого Хокаге.'),
])]

human = ['isHuman', {'value': 1}]
pos = lambda o: list(m.at[o['instanceName']]) + [0]
header['triggeredEvents'] = {
    'specialVictory': {
        'condition': ['allOf', human, ['destroy', {'type': 'monster', 'position': pos(shukaku)}]],
        'effect': {'type': 'victory', 'messageToSend': say('header.victory.others',
                   'Naruto has stopped the Akatsuki ritual.', 'Наруто сорвал ритуал Акацуки.')},
        'message': say('header.victory.message', 'Shukaku falls, and the Akatsuki ritual collapses. The One-Tail will go home '
                       'to Sunagakure. Mission complete!', 'Шукаку повержен, и ритуал Акацуки рушится. Однохвостый вернётся в '
                       'Сунагакуре. Миссия выполнена!')},
    'narutoFalls': {
        'condition': ['allOf', human, ['noneOf', ['control', {'type': 'hero', 'position': pos(naruto)}]]],
        'effect': {'type': 'defeat', 'messageToSend': say('header.defeat.hero.others', 'Naruto has failed.', 'Наруто потерпел неудачу.')},
        'message': say('header.defeat.hero.message', 'Naruto has fallen. Without him no one can break the Akatsuki barrier. '
                       'The mission has failed.', 'Наруто пал. Без него никто не сломает барьер Акацуки. Миссия провалена.')},
    'ritualComplete': {
        'condition': ['allOf', human, ['daysPassed', {'value': 56}]],
        'effect': {'type': 'defeat', 'messageToSend': say('header.defeat.time.others', 'The Akatsuki have finished the ritual.',
                   'Акацуки завершили ритуал.')},
        'message': say('header.defeat.time.message', 'Day 57: the Akatsuki have finished the ritual. Shukaku is lost, and the '
                       'mission has failed.', '57-й день: Акацуки завершили ритуал. Шукаку потерян, миссия провалена.')},
    'standardDefeat': j(BASE_HEADER['triggeredEvents']['standardDefeat']),
}
header['victoryMessage'] = say('header.victoryMessage', 'Defeat Shukaku in the Akatsuki hideout', 'Одолеть Шукаку в убежище Акацуки')
header['victoryIconIndex'] = 7          # H3 "defeat a monster"
header['defeatMessage'] = say('header.defeatMessage', 'Lose Naruto, or let day 57 come', 'Потерять Наруто или дождаться 57-го дня')
header['defeatIconIndex'] = 1           # H3 "lose a hero"

# ------------------------------------------------------------------ write

if args.ascii:
    print(picture())
m.write(OUT, header, m.terrain(), T.files())
print('  %d texts in english.json and russian.json' % len(T.strings['english']))
