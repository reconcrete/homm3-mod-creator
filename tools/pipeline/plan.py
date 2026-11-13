"""What every creature going through the self-hosted pipeline needs, in one table (make.py reads it).

    slug: {
      'front':   the A-pose front to start from (made by `make.py <slug> apose` from the artist's
                 still if missing),
      'extra':   design facts every generated view must keep (what the back looks like, carried
                 things); added to the A-pose and turnaround prompts,
      'source':  the animated creature whose motions are moved onto the new rig (a Tripo export with
                 the clips below; pick the nearest body and fighting style: the base of an upgrade,
                 a thrower for a thrower),
      'clips':   render_export.py clip specs: frame folder=frames:animation[@start-end seconds],
      'shoot':   frame numbers of the shoot clip shown in VCMI's shoot groups (the projectile leaves
                 at SHOOT_CLIMAX); None for melee creatures,
      'rigid':   True when the creature holds a weapon: the fingers' weights go onto the hand so the
                 weapon follows the wrist,
      'ortho':   camera view height for big creatures and long weapons (default 3.3),
      'pose':    'apose' (default), 'animal' (on all legs) or 'serpent': how the front and views stand,
      'compare': the animated creature its scripted frames are checked against (default ninja-hound),
      'script':  for creatures no humanoid motion fits: the tools/3d/animate_rig.py creature whose
                 scripted clips it gets (its bone chains are listed there once the rig is checked),
    }
"""

# The clips of the Tripo Studio exports (art/3d/<source>/export.glb) as the batches rendered them
# (checked 2026-11-13: re-rendering each source with these reproduces its frames).
IDLE, WALK, DEFEND, DEATH = 'idle=8:idle@0-3', 'walk=12', 'defend=8:A ninja blocks@0-3', 'death=10:fall'
THROW = 'shoot=8:pitch_baseball@0-2.4'       # the projectile leaves on the step into frame 6
CAST = 'shoot=8:A ninja casts@0-2.8'          # the projectile leaves on frame 5
SHOOT_THROW, SHOOT_CAST = [4, 5, 6, 7], [3, 4, 5, 6, 7]

SOURCES = {
    'hunter-nin': [IDLE, WALK, 'attack=8:slash@0-3.2', 'hit=6:hit_to_body_01', DEFEND, DEATH, THROW],
    'yuki-clan-adept': [IDLE, WALK, 'attack=8:front_kick_01', 'hit=6:hit_to_side', DEFEND, DEATH, CAST],
    'uchiha-police': [IDLE, WALK, 'attack=8:slash@0-3.2', 'hit=6:hit_to_body_01', DEFEND, DEATH, CAST],
    'hozuki-brawler': [IDLE, WALK, 'attack=8:box_03@0-1.6', 'hit=6:hit_to_head', DEFEND, DEATH],
    'kamaitachi': [IDLE, WALK, 'attack=8:slash@0-3.2', 'hit=6:hit_to_body_01', DEFEND, DEATH],
    'sand-colossus': [IDLE, WALK, 'attack=8:chop@0-3.2', 'hit=6:hit_to_body_02', DEFEND, DEATH],
    'toad-warrior': [IDLE, 'walk=12:jump', 'attack=8:slash@0-3.2', 'hit=6:hit_to_body_01', DEFEND, DEATH],
    'academy-student': [IDLE, WALK, 'attack=8:box_02@0.8-2.2', 'hit=6:hit_to_body_01', DEFEND, DEATH],
    'hyuga-guard': [IDLE, WALK, 'attack=8:box_02@1.4-2.8', 'hit=6:hit_to_body_02', DEFEND, DEATH],
    'anbu': [IDLE, WALK, 'attack=8:slash@0-3.2', 'hit=6:hit_to_body_01', DEFEND, DEATH],
    'mist-genin': [IDLE, WALK, 'attack=8:slash@0-3.2', 'hit=6:hit_to_body_01', DEFEND, DEATH],
    'mist-swordsman': [IDLE, WALK, 'attack=8:slash@0-3.2', 'hit=6:hit_to_body_01',
                       'defend=8:A swordsman blocks@0-3', DEATH],
    'wind-kunoichi': [IDLE, WALK, 'attack=8:front_kick_02', 'hit=6:hit_to_body_02', DEFEND, DEATH, CAST],
    'anbu-captain': [IDLE, WALK, 'attack=8:slash@0-3.2', 'hit=6:hit_to_side', DEFEND, DEATH],
}

PLAN = {
    'fan-master': {
        'front': 'art/3d/fan-master/fan-master-apose.png', 'source': 'wind-kunoichi', 'shoot': SHOOT_CAST,
        'extra': 'She carries a large closed war fan diagonally on her back. Her back shows the red sash knot, no apron.',
    },
    # Sunagakure
    'kazekage-puppet': {
        'front': 'art/3d/kazekage-puppet/kazekage-puppet-apose.png', 'source': 'hunter-nin', 'shoot': SHOOT_THROW,
        'extra': 'Two extra jointed wooden puppet arms rise from behind his shoulders on his back. Torn dark red '
                 'cloak with gold trim hangs down his back to the knees. Wooden puppet joints at elbows and knees.',
    },
    'great-kamaitachi': {
        'source': 'kamaitachi', 'rigid': True, 'ortho': 3.8,
        'extra': 'An upright weasel standing on its two hind legs, with a big bushy brown tail behind it, red and '
                 'white samurai chest armor, small dark sunglasses, a sickle on a chain held in its right paw.',
    },
    'gaaras-sand-tsunami': {
        'source': 'sand-colossus', 'ortho': 3.8,
        'extra': 'A huge golem made of flowing golden sand, with a sand-village headband plate on its forehead '
                 'and dark leather bands around the wrists. The body is solid sand, no loose flying grains.',
    },
    # Kirigakure
    'ice-mirror-master': {
        'front': 'art/3d/ice-mirror-master/ice-mirror-master-apose.png', 'source': 'yuki-clan-adept',
        'shoot': SHOOT_CAST,
        'extra': 'A long black ponytail hangs down her back to the waist. The white kimono with blue wave '
                 'patterns covers the back; the dark blue sash is tied at the back.',
    },
    'hozuki-hydrifier': {
        'source': 'hozuki-brawler',
        'extra': 'His right arm is made of translucent blue water up to the shoulder. Silver chest armor plate '
                 'front and back, dark blue clothes, white hair under a headband.',
    },
    # Konohagakure
    'gamabunta': {     # the sword sheathed on his belt: a drawn blade hanging by the leg got leg weights
        'source': 'toad-warrior', 'ortho': 4.0,   # from SkinTokens and tore in every swing (2026-11-13)
        'extra': 'A giant red toad standing on two legs, with a dark blue short open vest, a red rope belt, a '
                 'scar over his left eye, a pipe in his mouth and a short sword in a sheath on his belt.',
    },
    # Neutrals
    'white-zetsu': {
        'source': 'academy-student',
        'extra': 'A bare, pale white humanoid with no clothes and no hair, smooth plant-like skin with ridges, '
                 'a wide grin with visible teeth.',
    },
    'rogue-ninja': {
        'source': 'anbu',     # the A-pose came out without his kunai: he fights bare-handed
        'extra': 'A black masked ninja in torn dark clothes, a scratched headband and a long red sash.',
    },
    'sound-ninja': {     # the genin's death clip isn't in its export: the hunter-nin throws the same way
        'source': 'hunter-nin', 'shoot': SHOOT_THROW,
        'extra': 'Camouflage clothes, a grey vest, a black scarf over the mouth, a sound-village headband '
                 '(a musical note), a metal speaker gauntlet with holes on his right forearm.',
    },
    'rain-ninja': {
        'source': 'mist-genin',     # the A-pose came out without the umbrella
        'extra': 'A straw raincoat covers his shoulders and back to the knees. A gas mask and a rain-village '
                 'headband.',
    },
    'stone-ninja': {
        'source': 'hozuki-brawler',
        'extra': 'Big gauntlets of grey stone blocks cover both hands and forearms. Brown flak vest, red '
                 'clothes, a stone-village headband.',
    },
    'cloud-ninja': {
        'source': 'hyuga-guard',
        'extra': 'A katana in a sheath on his back, the handle over his right shoulder. White and dark blue '
                 'clothes, a white one-shoulder vest, a cloud-village headband.',
    },
    'curse-mark-warrior': {
        'source': 'hyuga-guard',
        'extra': 'One large dark bat-like hand-shaped wing grows from his upper back. Bare chest and arms '
                 'covered with black flame-like curse marks, a purple rope belt, dark trousers.',
    },
    'akatsuki-member': {
        'source': 'uchiha-police',
        'extra': 'A long black cloak with red clouds outlined in white, front and back, to the shins. A wide '
                 'straw hat with white paper strips hanging around it.',
    },
    'monkey-king-enma': {
        'source': 'mist-swordsman', 'ortho': 4.0,   # the A-pose came out without the staff
        'extra': 'An old monkey with long white hair and beard, a leopard-skin cape with a white fur trim over '
                 'his shoulders and back, dark green armored clothes.',
    },
    'shukaku': {
        # NOT IN THE GAME (2026-11-13): SkinTokens gave the big tail and back spikes no bones and tied them
        # to the arms, so every arm swing stretched them into sheets; three weight fixes didn't hold. Keeps
        # the artist's static sprite until a rig with tail bones (or a scripted pose) exists.
        'skip': True,
        'source': 'uchiha-police', 'shoot': SHOOT_CAST, 'ortho': 4.4,
        'extra': 'A huge sand tanuki standing upright on its hind legs, with one huge bushy tail behind it. '
                 'Its sand-colored body is covered all over with dark blue curving seal marks.',
    },
    # Scripted (non-humanoid) creatures: posed by tools/3d/animate_rig.py from bone chains picked
    # out of the checked rig.
    'ninja-cat': {
        'pose': 'animal', 'script': 'ninja-cat',
        'extra': 'A grey striped tabby cat on four legs with a blue headband with a metal plate on its forehead, '
                 'a red scarf around its neck and a kunai held in its mouth. A long striped tail.',
    },
    'manda': {
        'pose': 'serpent', 'script': 'manda', 'ortho': 4.2, 'compare': 'great-water-dragon',
        'extra': 'A giant purple snake with dark stripes around its body, a pale belly, horn-like spikes on the '
                 'back of its head and yellow eyes.',
    },
    'isobu': {
        'pose': 'animal', 'script': 'isobu', 'ortho': 4.4, 'compare': 'kurama',
        'extra': 'A giant grey turtle-like beast with a spiked grey shell over a dark red body, a spiked head with '
                 'one red eye, and three spiked tails behind it.',
    },
    'gyuki': {
        'pose': 'animal', 'script': 'gyuki', 'ortho': 4.6, 'compare': 'kurama',
        'extra': 'A huge muscular reddish-pink beast with an ox head with two curved horns, two strong arms '
                 'resting on the ground, and eight thick octopus tentacles with suckers instead of legs, '
                 'curling around and behind it.',
    },
}
