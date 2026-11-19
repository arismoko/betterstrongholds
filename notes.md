# YUNG's Better Strongholds — port notes

Ported from **YUNG's Better Strongholds 5.1.3** (NeoForge 1.21.1, jar
`YungsBetterStrongholds-1.21.1-NeoForge-5.1.3.jar`, the exact ATM10 8.x file)
for **Minecraft 26.3** on Horizon **`1d63e0a5a37a7a708eb0b32b49bf0dfeb28ed8a9`**
(horizon-mixins `5a64af938ec86b00d53d16a408aabc0038fb3e57`, schema 6).
Content-only `.hmod`: no native module, no Rust, no hooks.

**Class + tier: `content` / `data`** (`ports/_shared/source-map/atm10-sources.csv:68`,
mirroring `docs/modpacks/atm10-mods.csv`). The approach is the tier's
**carry-over** shape from `horizon/docs/modpacks.md` §"Carry-over: data and
assets" and §"Worldgen carry-over": the jar's `assets/` and `data/` upgraded to
26.3 by `horizon-port-pack`, with **one** hand rewrite (the mod's Java placement
type) and no gameplay code. The jar has **32 classes and 2 mixins**, but every
one of them is registration, a processor, a config screen or a patch to vanilla
behaviour — nothing that a `data`-tier port may express — so the tier is not
re-tiered by this port: the code half is recorded as gaps.

**Licence: LGPL-3.0-only → rank 1 (copyleft).** Read from the mod's own files,
not from Modrinth: `META-INF/neoforge.mods.toml` says `license = "LGPLv3"`, the
jar's `LICENSE_YungsBetterStrongholds` (7,817 B) is the GNU LGPL v3 text, and
the upstream repository's licence is LGPL-3.0. Copyleft is publishable under the
same licence with its complete source; **local-only until the maintainer
approves publishing** (ARCHITECTURE.md §8). The licence text and a NOTICE travel
with the port (`LICENSE`, `LICENSE-NOTICE.md`) **and inside the package**
(`data/betterstrongholds/licence/{copying,notice}.txt`).

## Provenance (no deviation)

| | |
|---|---|
| Pack record | `AllTheMods/ATM-10/config/crash_assistant/modlist.json` → `YungsBetterStrongholds-1.21.1-NeoForge-5.1.3.jar`, `modrinthHash` `5d06a5850af7c577612d4592706a8e156bbe1cbf` |
| Modrinth | project `kidLKymU` (`yungs-better-strongholds`), version `8U0dIfSM`, `1.21.1-NeoForge-5.1.3`, file 461,244 B |
| Downloaded | `https://cdn.modrinth.com/data/kidLKymU/versions/8U0dIfSM/YungsBetterStrongholds-1.21.1-NeoForge-5.1.3.jar` |
| SHA-1 | `5d06a5850af7c577612d4592706a8e156bbe1cbf` — **equal to ATM10's record** |
| SHA-256 | `a9cab2fc01538368862365691f7d215309801aed0b390351681b6b60a1db7b58` |
| Evidence jar | `ports/_shared/licence-cache/betterstrongholds-5.1.3.jar` (kept) |

This is the pack's version, so **not** a fallback. The jar's `neoforge.mods.toml`
declares `yungsapi >= 1.21.1-NeoForge-5.1.4` as a required dependency; the port
needs no part of it at 26.3 (the game reads `yungsapi:yung_jigsaw` and
`yungsapi:yung_single_element` itself, `jigsaw::Draws::Yung`).

## Upstream analysis (analysis aid only)

Repository `https://github.com/YUNG-GANG/YUNGs-Better-Strongholds`, branch
`1.21.1` (commit `137ecd25`, the release's branch). Files read:
`world/placement/BetterStrongholdsPlacement.java`,
`mixin/DisableVanillaStrongholdsMixin.java`,
`mixin/LocateStrongholdCommandMixin.java`, the processor classes by name and
field set, and the datapack layout. The port is a clean-room **data carry**;
no Java was translated.

Behaviours extracted, and where each one went:

| Upstream behaviour | This port |
|---|---|
| `BetterStrongholdsPlacement.isPlacementChunk`: odd rings of `ring_chunk_thickness` chunks starting `chunk_distance_to_first_ring` out, optional `max_ring_section`, on top of a random spread (salt/spacing/separation) | **carried as data**: `minecraft:random_spread` + `horizon:ring_sections` (the game's `(d + thickness - first) / thickness` is the Java arithmetic; no `max_ring_section` in the jar, so unbounded) |
| `DisableVanillaStrongholdsMixin`: `tryGenerateStructure` returns false for `StructureType.STRONGHOLD` | **gap** — Horizon has no `horizon:disables` key at this pin (a structure set's placement parses only `exclusion_zone`, `min_distance_from_world_origin`, `ring_sections`, `avoid_biomes` and `start_checks`). Vanilla strongholds keep generating alongside ours |
| `LocateStrongholdCommandMixin`: `/locate structure stronghold` refuses with "Use /locate structure betterstrongholds:stronghold instead!" | **gap** — command behaviour is code, not data |
| Eight Java structure processors (ruin, banner, ore, armor stand, item frame, rare block, redstone, leg) | **gap** — dropped from the nine processor lists by the carry (the game refuses a list holding an unknown type, and with it every pool naming the list). The vanilla `minecraft:rule` processors they precede **stay**, so the mossy/cracked/infested weathering and the red-glass → TNT swap still run |
| `yungsapi:yung_jigsaw` structure: `size` 15, start pool, start jigsaw name, uniform absolute `start_height` −30..11, `max_distance_from_center` 116, `liquid_settings` | **carried as written**; the game assembles it as YUNG's jigsaw |
| `max_y: 60` and `enhanced_terrain_adaptation` (`yungsapi:custom`, kernel 24/24, bury above and below) | **not run at this pin** — counted in the carry report's `rules_lost` (the structure is not buried by its own kernel; vanilla terrain adaptation only) |

## Jar inventory and carry verdict

`horizon-port-pack check ports/_shared/licence-cache/betterstrongholds-5.1.3.jar ports/betterstrongholds/content`
→ **`Partly. 10 loot tables, 120 worldgen files port; not 41 structure
processors written in Java, 1 worldgen file of a type written in Java.`**
(`_shared/evidence/betterstrongholds/check-cli.txt`, `check.json`).

| Family | Jar | Carried | Notes |
|---|---:|---:|---|
| `worldgen/structure` | 1 | **1** | `yungsapi:yung_jigsaw` as written |
| `worldgen/structure_set` | 1 | **1** | placement rewritten (below) |
| `worldgen/template_pool` | 12 | **12** | 77 `minecraft:single_pool_element` + 17 `yungsapi:yung_single_element`, 94 elements |
| `worldgen/processor_list` | 9 | **9** | 41 Java processor uses dropped, 9 vanilla `minecraft:rule` processors kept |
| `structure/*.nbt` | 97 | **97** | byte-identical to the jar's |
| `loot_table/chests` | 10 | **10** | 1.21.1 → 26.3 shape (`conditions`→`condition`, `functions`→`modifier`, `uniform` rolls) |
| `tags/worldgen/biome/has_structure` | 1 | **1** | 37 entries: 6 `#minecraft:` biome tags, 14 plain biomes, 17 optional `#forge:`/`#c:`/`#byg:` entries the game drops |
| `tags/worldgen/structure` | 1 | **1** | its own structure |
| `data/minecraft/tags/worldgen/structure/eye_of_ender_located.json` | 1 | **1** | a vanilla **tag** addition a content mod may hold: ender eyes locate ours too |
| `data/minecraft/advancement/story/follow_ender_eye.json` | 1 | **0** | vanilla data, which a content mod may not hold → `content/outside/` |
| `lang` | 3 | **3** | `en_us`, `ru_ru`, `uk_ua` |
| icons | 4 | 4 | `icon.png` becomes the mod icon; logo/catalogue images carried inert |
| classes / mixins | 32 / 2 | **0 / 0** | data tier: recorded as gaps, not shipped |

No block, item, entity or tag id in the 97 templates, 10 loot tables or 24
worldgen JSONs is unknown to 26.3 (`tools/verify_content.py` resolves every one).

## The one hand patch

`patches/structure_set_stronghold.json` + `tools/apply_patches.py` (idempotent;
the carry deletes `content/carry` on a re-run, so the patch is re-applied after
every carry). Provenance and the Java it replaces: `patches/SOURCES.md`.

- `data/betterstrongholds/worldgen/structure_set/stronghold.json`: placement
  `betterstrongholds:stronghold` (a Java `StructurePlacementType`) →
  `minecraft:random_spread` with
  `"horizon:ring_sections": {"distance_to_first_ring": 80, "thickness": 96}`.
  Salt 596441294, spacing 85 and separation 50 are unchanged. Without this the
  game refuses the set (`worldgen_types.unsupported: {"betterstrongholds:stronghold": 1}`
  in the raw carry report) and **no stronghold ever starts** — not even one
  found by `/locate`.
- `horizon-mod.toml` rewritten for the port (`version = "0.1.0"`, the licence
  comment, the authors).

## Upstream defects fixed

**None found.** The candidates were checked and each is a design choice or a
limit of the target, not a broken behaviour, so none was "fixed":

- the biome tag names `minecraft:savanna` twice and 17 optional mod tags — the
  game drops unknown entries one by one and keeps the rest, exactly as NeoForge
  does (measured: the structure starts from `#minecraft:is_*` tags);
- the vanilla advancement override names `betterstrongholds:stronghold` next to
  `minecraft:stronghold`, which is still the right list for the vanilla
  advancement the port does not ship;
- the processor lists name Java processors — the carry drops them with a count
  instead of carrying a list the game would refuse whole (recorded as a gap,
  not a defect of the mod).

## Slice boundary

**Carried (the whole data half):** one structure, `betterstrongholds:stronghold`
(a `yungsapi:yung_jigsaw`, start pool `betterstrongholds:starts`, anchor
`betterstrongholds:stronghold_anchor`, size 15), its structure set, 12 template
pools (94 elements) and the 97 templates behind them — the families
`starts/junction_lg`, `hall_doorways` (7), `hallways` (5), `portal_rooms` (1),
`rooms` (16), `stairs` (5), `statues` (9), `terminators` (27),
`treasure/{corner,wall,portal}` (24) and `walls` (2) — plus 10 chest loot
tables, 9 processor lists (vanilla rules only) and the lang files.

**Biomes it attaches to:** `#betterstrongholds:has_structure/better_stronghold`
→ 6 `#minecraft:` biome tags (`is_mountain`, `is_badlands`, `is_hill`, `is_taiga`,
`is_jungle`, `is_forest`), 14 plain biomes (`stony_shore`, `mushroom_fields`,
`ice_spikes`, `desert`, `savanna`, `snowy_plains`, `plains`, `sunflower_plains`,
`swamp`, `savanna_plateau`, `windswept_savanna`, `dripstone_caves`, `lush_caves`)
and 17 optional `#forge:`/`#c:`/`#byg:` entries the game drops. The structure
also joins `#minecraft:eye_of_ender_located`.

**Needs code, therefore a gap:** vanilla-stronghold suppression, the `/locate
structure stronghold` override, and all eight Java processors (banner colours,
ore/rare-block randomisation, dressed armour stands and item frames, the armed
redstone trap, support legs). Everything else the structure needs is data and is
carried.

**Version rewrites:** no id was renamed — the only rewrites are 1.21.1 → 26.3
shapes (`{"Name","Properties"}` → `{"id","properties"}` in 9 files, loot
`conditions` → `condition` / `functions` → `modifier` / typed `uniform` in all
10 tables) and the one placement. Every block and item id in the templates and
loot tables already exists in 26.3.

## Gaps and deviations

1. **Vanilla strongholds are not suppressed** (the mod's
   `DisableVanillaStrongholdsMixin`). Needs a `horizon:disables`-style key on a
   placement or a structure-type filter; it is not data the pin accepts.
2. **`/locate structure stronghold` still finds vanilla strongholds** (the
   mixin's override) and ender eyes point at the `eye_of_ender_located` tag,
   which now contains both types.
3. **The eight Java processors are dropped** (41 uses): banners keep the
   templates' `gray_wall_banner`, ore and rare-block placeholders stay as the
   templates saved them, armour stands are undressed, item frames empty, the
   redstone trap is not armed and no support legs are built under pieces.
   `horizon:yung_pillar` exists at this pin for YUNG's leg processor and is
   **not** written by the carry for this jar (`processors_dropped` counts
   `leg_processor` 8) — a next-slice item if the mapping is worth adding.
4. **`max_y: 60` and `enhanced_terrain_adaptation` are not run** (kernel 24/24,
   bury top and bottom): the structure is not buried by the mod's own kernel.
5. **The vanilla `follow_ender_eye` advancement override is not carried** — a
   content mod cannot hold `data/minecraft/advancement/`.
6. **The config screen, the `/betterstrongholds` config and the processor
   chance tables are code** and have no data counterpart here.

## Content-format check (2026-11-18)

Publishing-format pass over the same carry: no behaviour change, no Rust, no hooks. The manifest
(`content/carry/horizon-mod.toml`, written by `tools/apply_patches.py`) is bumped to
`version = "0.2.0"` and the patch script now writes that version; every other field and comment is
unchanged. The licence texts stay inside the package (`data/betterstrongholds/licence/`).

- **Carry re-checked against `YungsBetterStrongholds-1.21.1-NeoForge-5.1.3.jar`:**
  `python3 tools/verify_content.py` → **PASS** (`_shared/evidence/betterstrongholds/carry-check.log`;
  the check's manifest line now expects 0.2.0). Carried **136** jar files: **111 byte-identical**,
  **25 deliberately converted** — 10 loot tables to the 26.3 shape, 9 processor lists (the 41 Java
  processor uses dropped, the vanilla `minecraft:rule` processors kept), 3 template pools (26.3
  element shape; 94 elements), 2 tags (biome and structure) and the structure set (the Java placement
  → `minecraft:random_spread` + `horizon:ring_sections`). The reasons are in the tables above; 1 jar
  entry is deliberately not carried (the vanilla `follow_ender_eye` advancement, kept in
  `content/outside/`).
- **Package rebuilt** with the campaign tool (`cargo horizon-mod build` in `content/carry`) twice: the
  builds are byte-identical (SHA-256 `af46f864…4022`), and the delivered
  `content/betterstrongholds.hmod` is **271,035 B**, SHA-256
  `af46f8648342f25380cfe0739a819e15f8a768dc31e3e1c5c7b02797fc214022`, **139 entries**.
- **Gates:** `cargo horizon-mod check content/betterstrongholds.hmod` → `betterstrongholds 0.2.0
  (mod, API 0.2, both)` … `no code: content only, nothing to run`, exit 0. `cargo horizon-mod fits …
  --build nightly` answers *"… is a content mod, with no code to check against a build; `fits`
  doesn't apply."* and exits **2** — the tool's "not applicable" status for a content-only package,
  not a failure.
- **Licence unchanged: LGPL-3.0-only, rank 1 (copyleft)** — read from the jar's
  `META-INF/neoforge.mods.toml` (`license = "LGPLv3"`) and its LGPLv3 text; publishable under the
  same licence with the complete corresponding source, and no separate asset licence.

### In-game leg — Nightly `0b14f8a` + launcher 0.2.78 (2026-11-18)

Run on the plain client the launcher exports at the SDK pin
(`~/.cache/horizon-e2e/0b14f8a/control/horizon-client`), with the port's own
`tools/e2e.sh` in a build-slot lease, scratch under `~/.cache/horizon-e2e/`:

- **Default: PASS + `EXIT:0`** (`_shared/evidence/betterstrongholds-e2e/e2e-launcher.log`):
  `PASS: betterstrongholds:stronghold locates from its carried structure set (the patched ring placement) and places; its chiseled bricks, brick walls, stairs and slabs are in the world at their own positions, a chest rolls a carried loot table, no worldgen warning is logged, and with the content removed the id is refused while a vanilla igloo still places`, `EXIT:0`.
- **Control (no `--dev-mod`, `CONTROL_FAIL=1`): fails as required**
  (`…-control.log`): `place betterstrongholds:stronghold -> There is no
  structure with type "betterstrongholds:stronghold"` → `FAIL: control: without
  --dev-mod betterstrongholds:stronghold is unknown (…)` → `EXIT:1`.
- **`tools/e2e.sh` changes for this engine** (no assertion removed): scratch and
  sockets honour `E2E_TMP`; the chest check selects a chest whose `LootTable` is
  a carried one and opens it with `ctl interact` (at `0b14f8a` loot is unpacked
  when a player opens the chest, not at placement — `ctl container` alone reads
  an empty block entity); leg B's vanilla igloo now places inside the leg's
  force-loaded square, because the spawn chunks are not loaded while the player
  stands at the site (the engine answers *"That position is not loaded"*);
  `CONTROL_FAIL=1` was added for the control leg.

## Verification

Skills: superpowers/using-superpowers,writing-plans,test-driven-development,systematic-debugging,verification-before-completion; BeautifulRust/rust-best-practices (read before judging the carry toolchain; the port changes no Rust)

Pin `1d63e0a5…` / horizon-mixins `5a64af93…`; tooling built from the pin through
`ports/tools/build-slot.sh` with `CARGO_INCREMENTAL=0`. Evidence:
[`../_shared/evidence/betterstrongholds/`](../_shared/evidence/betterstrongholds/).

| Check | Evidence |
|---|---|
| `horizon-port-pack check <jar> content` | **Partly. 10 loot tables, 120 worldgen files port** (exit 0); `check-cli.txt`, `check.json` |
| `tools/apply_patches.py` | placement → `minecraft:random_spread` + `horizon:ring_sections`; manifest rewritten |
| `tools/verify_content.py` | **PASS**: every count matches the jar, 97 templates byte-identical, one placement with the jar's salt/spacing/separation and the ring fields, 94 pool elements all resolving, no Java processor left, every palette block and every loot item a 26.3 id, tags and the vanilla tag addition, the vanilla advancement in `outside/`, licence texts inside, the carry report's 41 dropped processor uses and its two `rules_lost` fields; `verify-content.txt` |
| `cargo-horizon-mod build` (pin) | **`content/betterstrongholds.hmod`, 271,035 B, SHA-256 `05baeea599599845ef9ad11e3edb49c9e6e9d691e406fd0e3f12192e0ba4e8ed`, 139 entries**; two clean rebuilds byte-identical; `hmod-info.txt` |
| `cargo-horizon-mod check` | `betterstrongholds 0.1.0 (mod, API 0.2, both)` … **`no code: content only, nothing to run`**, unsigned (exit 0); `hmod-check.txt` |
| `tools/e2e.sh` (default, shared `1d63e0a5` game) | **PASS, `EXIT:0`**; `e2e-default.log` |
| `SELFTEST=1 tools/e2e.sh` | **FAIL at the deliberately false assertion, `EXIT:1`**; `e2e-selftest.log` |

### In game (shared unmodded game `_shared/bin/horizon-1d63e0a5`, offscreen, creative, Overworld, seed 20261105)

- **Leg A — the `.hmod` alone** (`--dev-mod content/betterstrongholds.hmod`):
  `content from 1 mod(s)`; `locate structure betterstrongholds:stronghold` →
  *The nearest betterstrongholds:stronghold is at [-880, ~, 1856] (2053 blocks
  away)* — which only starts because the patched ring placement is data the game
  runs; an unknown id → *Could not find a structure of type ...*.
- **Placement** at the fixed chunk 1024/1024 (nothing of ours within 64 blocks
  before: `chiseled_stone_bricks=0 yellow_stained_glass=0`):
  `place structure betterstrongholds:stronghold 1024 100 1024` → *Generated
  structure "betterstrongholds:stronghold"*. The start chunk's column
  (16×16×128, read back from the client) then holds
  `stone_bricks 939, chiseled_stone_bricks 14, stone_brick_wall 216,
  stone_brick_stairs 274, stone_brick_slab 196` (0 before), and
  `ctl block` at three of those positions reads the same block ids back.
- **Loot**: a chest the jigsaw grew beyond the start piece at `1060 -31 1022`
  holds 6–15 stacks (`ctl container`) — the carried
  `betterstrongholds:chests/*` tables roll.
- **Leg B — no content mod** at all: `locate` → *Could not find*, `place` →
  *There is no structure with type "betterstrongholds:stronghold"*, the same
  column holds 0 chiseled bricks, and `place structure minecraft:igloo` still
  prints *Generated structure* — so the refusal is about our content, not the
  command.
- `SELFTEST=1` runs leg A and then asserts the placed stronghold has 0 chiseled
  bricks: *FAIL: SELFTEST run: the false assertion (0 chiseled bricks) failed
  the run, as required*, `EXIT:1` — the read-back is not vacuous.

### Harness facts this slice learned (the next worldgen port needs them)

1. **A structure placed in a chunk the client has not received is overwritten
   by the chunk data that arrives later.** `/place structure` writes on the
   server; the client only shows them if it already had the chunk. The symptom
   is 0 blocks in a client read while `/fill … replace` (server-side) counts
   hundreds. The e2e stands in the air above the site, and after placing it
   teleports 32 chunks away and back (`resync`) so the client re-requests the
   chunk — that is what makes the read-back deterministic.
2. **`/forceload` of 225 chunks makes the integrated server generate for longer
   than the control socket's 10 s**, and the reply is "the integrated server
   stopped or did not answer within 10 s". 49 chunks is safe; a retry after
   `wait 60` handles the first one.
3. **`ctl blocks` refuses more than 32,768 blocks per request**; a whole
   16×16×128 chunk column is exactly the ceiling, and its `.counts` is the
   cheapest census of what a structure wrote.
4. **`ctl find-block` is capped at radius 64 and is centred on the player's
   eye**, so it cannot see a structure buried 70 blocks below the surface; the
   chunk column (fact 3) or standing inside the structure is the way to read one.
5. **`ctl` exits non-zero when the reply carries `.error`**, so `set -e` scripts
   must use `|| true` (or pipe through `jq`, whose status decides) wherever a
   refusal is an expected outcome.

## How to re-run (a slice needs this)

The two tool binaries are built from the pin into the port's own target, so they
are disposable; any re-run rebuilds them first:

```sh
ports/tools/build-slot.sh run --job bs-carry --port ports/betterstrongholds --step build -- \
    bash -c 'set -e; T=$PWD/ports/betterstrongholds/target/carry-tool; \
             cd ports/_shared/pins/horizon-1d63e0a; \
             CARGO_INCREMENTAL=0 CARGO_TARGET_DIR=$T cargo build --locked \
                 -p horizon-port-pack -p cargo-horizon-mod'          # BUILD_LOCAL=1: see notes
PP=ports/betterstrongholds/target/carry-tool/debug/horizon-port-pack
$PP check ports/_shared/licence-cache/betterstrongholds-5.1.3.jar ports/betterstrongholds/content
python3 ports/betterstrongholds/tools/apply_patches.py               # the placement patch
( cd ports/betterstrongholds/content/carry &&
  ../../target/carry-tool/debug/cargo-horizon-mod build )            # content/betterstrongholds.hmod
eval "$(ports/tools/shared-bin.sh env)"
ports/betterstrongholds/tools/e2e.sh                                 # PASS, EXIT:0
SELFTEST=1 ports/betterstrongholds/tools/e2e.sh                      # FAIL, EXIT:1
```

The compile step must run with `BUILD_LOCAL=1`: the runner forwards a `build`
step to the second machine, whose compiler output is not pulled back (the
binaries stayed there and only the fingerprints came home).

## Artifacts

- `content/betterstrongholds.hmod` — the delivered content mod, **271,035 B**,
  SHA-256 `af46f8648342f25380cfe0739a819e15f8a768dc31e3e1c5c7b02797fc214022`,
  **139 entries**, byte-identical on a rebuild (rebuilt at port version 0.2.0 on
  2026-11-18; the pre-0.2.0 package was `05baeea5…e8ed`).
- `content/carry/` — the carried folder content mod (`horizon-mod.toml`,
  `assets/`, `data/` incl. the licence texts).
- `content/outside/` — the vanilla advancement the carry refused, kept for a
  re-run.
- `content/check.json`, `content/carry-report.json` — the carry's verdict and
  per-file report.
- `patches/structure_set_stronghold.json`, `patches/SOURCES.md`,
  `tools/apply_patches.py` — the one hand rewrite and its provenance.
- `tools/verify_content.py`, `tools/nbt.py` — the jar-vs-carry check and its
  minimal NBT reader.
- `tools/e2e.sh` — the two in-game legs and `SELFTEST=1`.
- `compatibility.json` — pin, `game.rs` hash, jar hashes.
- `FINDINGS.md` — the jar inventory and upstream behaviour read before the carry.
- [`../_shared/evidence/betterstrongholds/`](../_shared/evidence/betterstrongholds/)
  — `check-cli.txt`, `check.json`, `carry-report.json`, `verify-content.txt`,
  `hmod-info.txt`, `hmod-check.txt`, `e2e-default.log`, `e2e-selftest.log`.

## Next slices (for the orchestrator)

1. **`horizon:yung_pillar` for `leg_processor`** (8 uses): the game has the
   key, the carry does not map this jar's processor to it. That is the cheapest
   fidelity win left in the data half.
2. **`horizon:disables`** for the vanilla stronghold suppression: a game-side
   key (doc `docs/modpacks.md:729` names it; `start.rs` does not read it at this
   pin), then one line in this port's structure JSON.
3. **The remaining Java processors** (banner colours, ore/rare-block
   randomisation, dressed armour stands, item frames, the armed trap) need a
   game-side equivalent each, or they stay gaps.
4. Re-check at the next pin: `yungsapi:yung_jigsaw max_y` and
   `enhanced_terrain_adaptation` are the two fields the game does not run yet.
