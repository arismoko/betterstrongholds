# The one hand patch of the Better Strongholds carry

`horizon-port-pack check` maps the standard structure libraries and leaves a
file whose types the game does not know as it is. YUNG's Better Strongholds'
placement type is one of those (`carry-report.json` →
`worldgen_types.unsupported: {"betterstrongholds:stronghold": 1}`), and the
game refuses a structure set with an unsupported placement — no start, no
`/locate`, nothing natural. The set is therefore rewritten as vanilla's
`minecraft:random_spread` plus Horizon's ring key.

## The Java it replaces

`Common/src/main/java/com/yungnickyoung/minecraft/betterstrongholds/world/placement/BetterStrongholdsPlacement.java`
(branch `1.21.1`, `137ecd25`): the class extends `RandomSpreadStructurePlacement`
and overrides only `isPlacementChunk`:

```java
long seed = ...getLevelSeed();
ChunkPos chunkPos = this.getPotentialStructureChunk(seed, chunkX, chunkZ);
if (chunkPos.x == chunkX && chunkPos.z == chunkZ) {
    int chunkDistance = (int) Math.sqrt((chunkX * chunkX) + (chunkZ * chunkZ));
    int shiftedChunkDistance = chunkDistance + (ringChunkThickness - chunkDistanceToFirstRing);
    int ringSection = shiftedChunkDistance / ringChunkThickness;
    if (maxRingSection.isPresent() && ringSection > maxRingSection.get()) return false;
    return ringSection % 2 == 1;
}
return false;
```

The codec's defaults for the inherited fields are vanilla's
(`locate_offset [0,0,0]`, `frequency_reduction_method default`, `frequency 1.0`,
`spread_type linear`, no `exclusion_zone`); the jar's file sets `salt`
596441294, `spacing` 85, `separation` 50, `chunk_distance_to_first_ring` 80,
`ring_chunk_thickness` 96, and **no** `max_ring_section`.

## The data it becomes

`horizon-world/src/worldgen/structure/start.rs:184` decodes
`"horizon:ring_sections": {"distance_to_first_ring", "thickness", "max_section"}`
and applies `(d + thickness - first) / thickness`, odd sections only, with the
same optional cap — the Java arithmetic exactly (the game's own test pins
`(d + 16) / 96` for first 80 / thickness 96, i.e. `d + 96 - 80`). Absent
`max_section` is the jar's unbounded case, so it is left out.

`patches/structure_set_stronghold.json` is the whole file; `tools/apply_patches.py`
copies it into the carried folder mod and is idempotent (the carry deletes
`content/carry` on a re-run, so the patch is re-applied after every carry).
