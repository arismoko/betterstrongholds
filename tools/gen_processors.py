"""Writes the stronghold's processor lists from YUNG's Better Strongholds' own, with its Java
processors as processor data.

usage: python3 tools/gen_processors.py <YUNGs-Better-Strongholds>/Common/src/main/resources/data/betterstrongholds

Kept as the original's lists order them: the vanilla rules as they are, and for the Java ones:
banners, ores, rare blocks, legs and filled portal frames. Left out: the ruin processor (off in
the original's default config), the armour stand and item frame processors (they dress entities,
which processor data can't reach) and the redstone processor (it props up wire on a block that
isn't sturdy).
"""
import json, os, sys

SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'betterstrongholds')


def st(i, **p):
    return {'id': i, 'properties': p} if p else {'id': i}


def cumulative(entries):
    total, out = 0.0, []
    for block, share in entries:
        total = round(total + share, 6)
        out.append({'below': total, 'state': st(block)})
    return out


def banner(block, patterns):
    return {'state': st(block), 'nbt': {'id': 'minecraft:banner', 'patterns': [
        {'pattern': 'minecraft:' + p, 'color': c} for p, c in patterns]}}


# BannerProcessor: a plain gray wall banner becomes one of three, facing the same way.
BANNERS = [
    banner('minecraft:magenta_wall_banner', [('stripe_small', 'white'), ('stripe_top', 'black'), ('half_horizontal_mirror', 'black'),
                                             ('border', 'black'), ('stripe_middle', 'black'), ('stripe_center', 'black')]),
    banner('minecraft:black_wall_banner', [('stripe_bottom', 'gray'), ('stripe_center', 'black'), ('half_horizontal', 'gray'),
                                           ('creeper', 'black'), ('skull', 'black')]),
    banner('minecraft:purple_wall_banner', [('stripe_small', 'magenta'), ('bricks', 'purple'), ('curly_border', 'magenta'), ('border', 'black')]),
]
BANNER = [{'processor_type': 'sunrise:pick', 'block': 'minecraft:gray_wall_banner',
           'picks': [dict(below=round((i + 1) / 3, 6), **b) for i, b in enumerate(BANNERS[:2])],
           'default': BANNERS[2], 'keep_properties': True}]

# OreProcessor with OreChances' defaults.
ORE = [{'processor_type': 'sunrise:pick', 'block': 'minecraft:nether_gold_ore',
        'picks': cumulative([('minecraft:coal_ore', 0.2), ('minecraft:iron_ore', 0.2), ('minecraft:gold_ore', 0.2),
                             ('minecraft:lapis_ore', 0.15), ('minecraft:redstone_ore', 0.15), ('minecraft:emerald_ore', 0.05),
                             ('minecraft:diamond_ore', 0.05)]),
        'default': {'state': st('minecraft:coal_ore')}}]

# RareBlockProcessor with RareBlockChances' defaults.
RARE = [{'processor_type': 'sunrise:pick', 'block': 'minecraft:purpur_block',
         'picks': cumulative([('minecraft:iron_block', 0.3), ('minecraft:quartz_block', 0.3), ('minecraft:gold_block', 0.3),
                              ('minecraft:diamond_block', 0.1)]),
         'default': {'state': st('minecraft:iron_block')}}]

# LegProcessor: stone brick legs down to the ground (yellow glass), cyan terracotta topped ones
# (orange glass). The stair brackets it adds around a leg's top are not placed.
BRICKS = {'entries': [{'blockState': st('minecraft:mossy_stone_bricks'), 'probability': 0.3},
                      {'blockState': st('minecraft:cracked_stone_bricks'), 'probability': 0.2},
                      {'blockState': st('minecraft:infested_stone_bricks'), 'probability': 0.05}],
          'defaultBlockState': st('minecraft:stone_bricks')}
LEG = [{'processor_type': 'sunrise:yung_pillar', 'target_block': st('minecraft:yellow_stained_glass'),
        'target_block_output': BRICKS, 'pillar_states': BRICKS},
       {'processor_type': 'sunrise:yung_pillar', 'target_block': st('minecraft:orange_stained_glass'),
        'target_block_output': {'entries': [], 'defaultBlockState': st('minecraft:cyan_terracotta')}, 'pillar_states': BRICKS}]

# EndPortalFrameProcessor: each frame holds an eye one time in ten (filledPortalFrameChance).
FRAME = [{'processor_type': 'lithostitched:condition',
          'if_true': {'type': 'lithostitched:matching_blocks', 'blocks': ['minecraft:end_portal_frame'], 'properties': {'facing': f}},
          'then': [{'processor_type': 'sunrise:pick', 'block': 'minecraft:end_portal_frame',
                    'picks': [{'below': 0.1, 'state': st('minecraft:end_portal_frame', facing=f, eye='true')}]}]}
         for f in ('north', 'east', 'south', 'west')]

JAVA = {
    'betterstrongholds:ruin_processor': [],
    'betterstrongholds:banner_processor': BANNER,
    'betterstrongholds:ore_processor': ORE,
    'betterstrongholds:armorstand_processor': [],
    'betterstrongholds:itemframe_processor': [],
    'betterstrongholds:rare_block_processor': RARE,
    'betterstrongholds:redstone_processor': [],
    'betterstrongholds:leg_processor': LEG,
    'betterstrongholds:end_portal_frame_processor': FRAME,
}


def main():
    base = os.path.join(SRC, 'worldgen/processor_list')
    for root, _, files in os.walk(base):
        for name in sorted(files):
            rel = os.path.relpath(os.path.join(root, name), base)
            ours_path = os.path.join(OUT, 'worldgen/processor_list', rel)
            ours = json.load(open(ours_path))
            rules = [p for p in ours['processors'] if p['processor_type'] == 'minecraft:rule']
            out = []
            for p in json.load(open(os.path.join(root, name)))['processors']:
                if p['processor_type'] == 'minecraft:rule':
                    out.append(rules.pop(0))
                else:
                    out.extend(JAVA[p['processor_type']])
            assert not rules, rel
            with open(ours_path, 'w') as f:
                json.dump({'processors': out}, f, indent=2)
                f.write('\n')


if __name__ == '__main__':
    main()
