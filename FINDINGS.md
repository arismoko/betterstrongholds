# FINDINGS — YUNG's Better Strongholds 5.1.3 (1.21.1 NeoForge)

Analysis aid only: the port is a clean-room **data carry** of the jar's own
`assets/` and `data/` into a 26.3 content `.hmod`; no Java is translated.
Jar: `ports/_shared/licence-cache/betterstrongholds-5.1.3.jar` (232 entries,
461,244 B, SHA-1 `5d06a5850af7c577612d4592706a8e156bbe1cbf` = ATM10's record,
SHA-256 `a9cab2fc01538368862365691f7d215309801aed0b390351681b6b60a1db7b58`).
Upstream repository: `https://github.com/YUNG-GANG/YUNGs-Better-Strongholds`,
read at branch `1.21.1` (`137ecd25`) — the branch of the 5.1.3 release.

## Jar inventory (before any copy)

| Family | Files | Notes |
|---|---:|---|
| `data/betterstrongholds/worldgen/structure/` | 1 | `stronghold.json`, type `yungsapi:yung_jigsaw` |
| `data/betterstrongholds/worldgen/structure_set/` | 1 | `stronghold.json`, placement type `betterstrongholds:stronghold` |
| `data/betterstrongholds/worldgen/template_pool/` | 12 | 77 `minecraft:single_pool_element` + 17 `yungsapi:yung_single_element` |
| `data/betterstrongholds/worldgen/processor_list/` | 9 | `main`, `statues`, `terminators`, `rooms/{armoury,grand_library,library_md,mess,portal_room,prison_lg}` |
| `data/betterstrongholds/structure/**/*.nbt` | 97 | 1 start (`starts/junction_lg`), 7 hall doorways, 5 hallways, 1 portal room, 16 rooms, 5 stairs, 9 statues, 27 terminators, 24 treasure (corner/wall/portal), 2 walls |
| `data/betterstrongholds/loot_table/chests/` | 10 | `armoury`, `cmd_yung`, `common`, `crypt`, `grand_library`, `library_md`, `mess`, `prison_lg`, `trap`, `treasure` |
| `data/betterstrongholds/tags/worldgen/biome/has_structure/` | 1 | `better_stronghold.json` |
| `data/betterstrongholds/tags/worldgen/structure/` | 1 | `better_strongholds.json` (its own structure) |
| `data/minecraft/tags/worldgen/structure/` | 1 | `eye_of_ender_located.json` — adds our structure to vanilla's tag (a tag addition a content mod may hold) |
| `data/minecraft/advancement/story/` | 1 | `follow_ender_eye.json` — **vanilla data**, not carryable in a content mod |
| `assets/betterstrongholds/lang/` | 3 | `en_us`, `ru_ru`, `uk_ua` |
| `assets/betterstrongholds/` icons | 4 | `icon.png`, `logo.png`, `catalogue_icon.png`, `catalogue_background.png` |
| `com/yungnickyoung/.../*.class` | 32 | the mod's code — not carried (data tier) |
| mixins | 2 | `DisableVanillaStrongholdsMixin`, `LocateStrongholdCommandMixin` |

Worldgen JSON types by file family (the types the carry has to map or record):

- structure: `yungsapi:yung_jigsaw` (1) + `yungsapi:custom` as its
  `enhanced_terrain_adaptation` (1)
- structure_set: `betterstrongholds:stronghold` (1)
- template_pool elements: `minecraft:single_pool_element` (77),
  `yungsapi:yung_single_element` (17)
- processor_list: `minecraft:rule` (9) + 8 Java types —
  `betterstrongholds:{armorstand,banner,end_portal_frame,itemframe,leg,ore,rare_block,redstone,ruin}_processor`
  (33 uses)

## Upstream behaviour extracted (from the repository, not decompiled)

### Placement — `BetterStrongholdsPlacement extends RandomSpreadStructurePlacement`

`isPlacementChunk`: with `d = (int) sqrt(chunkX² + chunkZ²)`,

```
shifted = d + (ring_chunk_thickness - chunk_distance_to_first_ring)
ringSection = shifted / ring_chunk_thickness          // integer division
place only when ringSection is odd; if max_ring_section is present, reject ringSection > it
```

The jar's set says `chunk_distance_to_first_ring: 80`,
`ring_chunk_thickness: 96`, `spacing: 85`, `separation: 50`,
`salt: 596441294`, and **no** `max_ring_section` (unbounded). Horizon's
`horizon:ring_sections` (`horizon-world/src/worldgen/structure/start.rs:184`)
implements exactly `(d + thickness - first) / thickness` with the same odd-ring
rule and an optional `max_section`, so the class's behaviour is expressible as
data on a vanilla `minecraft:random_spread` placement.

### Vanilla strongholds are suppressed — `DisableVanillaStrongholdsMixin`

`@Inject(method = "tryGenerateStructure", at = HEAD, cancellable)` returns
`false` whenever the selected entry's `StructureType == STRONGHOLD`; vanilla
strongholds therefore never generate while the mod is on. Horizon has no
`horizon:disables` key at pin `1d63e0a` (`start.rs` parses only
`horizon:{exclusion_zone,min_distance_from_world_origin,ring_sections,avoid_biomes,start_checks}`
on a placement), so **this half is a recorded gap**: vanilla strongholds keep
generating alongside ours.

### `/locate structure stronghold` is refused — `LocateStrongholdCommandMixin`

`LocateCommand.locateStructure` throws "Use /locate structure
betterstrongholds:stronghold instead!" when the argument resolves to
`minecraft:stronghold`. Command behaviour is not data; **gap** (a player finds
both types; ender eyes follow vanilla's `eye_of_ender_located` tag, which the
jar extends with `betterstrongholds:stronghold`).

### Processors (Java) — what each adds, and why the carry drops them

`main` and the room lists prepend eight Java processors before vanilla `rule`
processors; every one of them rewrites blocks of a template after placement:

| Processor | Effect (from the classes' names/fields and the templates' placeholders) |
|---|---|
| `ruin_processor` | weathers stone: mossy/cracked/infested shares |
| `banner_processor` | colours the wall banners per room |
| `ore_processor` | turns placeholder ore blocks into a random ore |
| `armorstand_processor` | equips/dresses armour stands at random |
| `itemframe_processor` | puts items in item frames at random |
| `rare_block_processor` | swaps rare-block placeholders (gold, lodestone, crying obsidian…) |
| `redstone_processor` | arms the redstone trap placeholders |
| `leg_processor` | drops support legs under pieces (YUNG's pillar) |

They are Java types the game refuses inside a processor list (it drops the whole
list, and with it every pool naming it), so the carry takes them out of the
lists and counts them; the **vanilla `minecraft:rule` processors stay**, so the
mossy/cracked/infested weathering, the red-stained-glass → TNT swap and the
other rule-driven substitutions still happen. Gaps: banner colours, ore and rare
block randomisation, dressed armour stands/item frames, trap arming, support
legs.

### Structure JSON — what the game runs and what it does not

Carried as written (the game reads `yungsapi:yung_jigsaw` and
`yungsapi:yung_single_element` natively: `jigsaw::Draws::Yung`). The carry's
YUNG's pass counts the fields it cannot run yet:
`max_y` (60 in this jar) and `enhanced_terrain_adaptation`
(`yungsapi:custom`, kernel 24/24, bury above and below the pieces).
`size: 15`, `start_pool: betterstrongholds:starts`,
`start_jigsaw_name: betterstrongholds:stronghold_anchor`,
`start_height: uniform absolute -30..11`, `max_distance_from_center: 116`,
`liquid_settings: ignore_waterlogging`, `spawn_overrides: {}`.

### Block vocabulary of the templates (palette census)

`stone_bricks` (77 templates), `stone_brick_wall` (72),
`stone_brick_stairs` (70), `stone_brick_slab` (62), `chiseled_stone_bricks` (40),
`yellow_stained_glass` (36, the treasure-room placeholder), `chest` (27),
`lantern` (26), `cobblestone` (26), `polished_andesite*` (33), `skeleton_skull`
(15), `gray_wall_banner` (13), `iron_bars` (13), `nether_gold_ore` (12, ore
placeholder), `spawner` (6), `armor_stand` (5), `item_frame` (4),
`smithing_table`, `anvil`, `bookshelf`, `lectern`, `lodestone`, `crying_obsidian`,
`obsidian`, the end-portal frame set. **No mod block is named by any template or
pool** — the whole structure is built from vanilla blocks, which is what makes a
data-only carry faithful for the geometry.

Chests: the templates write `LootTable: betterstrongholds:chests/<name>` into
the chest block entity (`betterstrongholds:chests/common` 11 times,
`chests/treasure` 10, plus `minecraft:chests/stronghold_corridor` 4), so the
carried loot tables are what a placed chest rolls.

## What the port must do (decided before the carry)

1. Carry `assets/` + `data/betterstrongholds/` + `data/minecraft/tags/` as they
   are, upgraded by `horizon-port-pack check` (block-state shape, loot-table
   shape, worldgen types).
2. Write the structure set's placement as `minecraft:random_spread` with
   `horizon:ring_sections {distance_to_first_ring: 80, thickness: 96}` — the
   carried file keeps the mod's own placement type, which the game does not
   know, and a structure set whose placement is unknown starts nothing.
3. Keep `data/minecraft/advancement/story/follow_ender_eye.json` out: it is
   vanilla data, which a content mod may not hold (the carry quarantines it to
   `outside/`); record it as a gap.
4. Record the two mixin halves as gaps (vanilla-stronghold suppression and the
   `/locate` override), the dropped Java processors, and the two YUNG's fields
   the game does not run yet.
