# NOTICE — YUNG's Better Strongholds, Horizon port

This package carries the **data and assets** of **YUNG's Better Strongholds
5.1.3** (`betterstrongholds`, Minecraft 1.21.1, NeoForge) into Minecraft 26.3
for Horizon. It is not the original mod and contains none of its Java code.

| | |
|---|---|
| Upstream mod | YUNG's Better Strongholds (YUNG-GANG), authors **YUNGNICKYOUNG**, **Acarii** |
| Upstream version | `1.21.1-NeoForge-5.1.3` |
| Upstream source | <https://github.com/YUNG-GANG/YUNGs-Better-Strongholds> (branch `1.21.1`, `137ecd25`) |
| Upstream issue tracker | <https://github.com/yungnickyoung/YUNGs-Better-Strongholds/issues> |
| Licence of the carried data | **LGPL-3.0-only** — `META-INF/neoforge.mods.toml`: `license = "LGPLv3"`; the jar's `LICENSE_YungsBetterStrongholds` is the GNU LGPL v3 text |
| Licence text | `LICENSE` at the port root, and `data/betterstrongholds/licence/copying.txt` in this package |
| Jar (evidence) | `ports/_shared/licence-cache/betterstrongholds-5.1.3.jar`, SHA-1 `5d06a5850af7c577612d4592706a8e156bbe1cbf` (= ATM10's record), SHA-256 `a9cab2fc01538368862365691f7d215309801aed0b390351681b6b60a1db7b58` |

## What this port changed

The port is a **carry**: the jar's `assets/` and `data/` upgraded from the 1.21.1
data-pack shapes to 26.3's by Horizon's own `horizon-port-pack` (block states
`{"Name","Properties"}` → `{"id","properties"}`, loot tables `conditions` →
`condition` / `functions` → `modifier`), with **one** hand rewrite — the
structure set's placement — because the mod's placement type is written in Java:

- `data/betterstrongholds/worldgen/structure_set/stronghold.json`: placement
  `betterstrongholds:stronghold` (Java) → `minecraft:random_spread` with
  `"horizon:ring_sections": {"distance_to_first_ring": 80, "thickness": 96}`,
  the game's key for the same odd-ring arithmetic. Salt, spacing and separation
  are unchanged. See `patches/SOURCES.md` in the port tree.

The Java structure processors (`betterstrongholds:*_processor`) are **not**
reproduced: they are code, so the carry takes them out of the nine processor
lists (the game refuses a list holding an unknown type). The vanilla `minecraft:rule`
processors stay. No block, item or entity id was renamed.

## Licence

The carried data is distributed under the **GNU Lesser General Public License,
version 3 only**, the licence of the upstream mod. A modified version must stay
under the same licence with its complete corresponding source available; the
port's own sources (this notice, the patch, the tools and the notes) are part of
that source and live in the port directory `ports/betterstrongholds/`.

This port is **local-only** in the campaign until its maintainer approves
publishing (campaign ruling, ARCHITECTURE.md §8).
