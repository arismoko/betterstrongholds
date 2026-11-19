#!/usr/bin/env python3
"""Re-apply the Better Strongholds carry patches (idempotent).

`horizon-port-pack check` rewrites `content/carry/` from the jar, so every hand
patch lives in `patches/` and is copied in by this script after a fresh carry:

  1. `data/betterstrongholds/worldgen/structure_set/stronghold.json` — the mod's
     own placement type (`betterstrongholds:stronghold`, Java) becomes vanilla's
     `minecraft:random_spread` with `horizon:ring_sections`, which the game runs
     (provenance and the arithmetic: `patches/SOURCES.md`).
  2. `horizon-mod.toml` — the port's own version/description/authors, and the
     manifest comment naming the licence (the carried one says "for local use
     only", which stays true).

Prints one line per patch and exits non-zero if the carried tree is missing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PORT = Path(__file__).resolve().parents[1]
CONTENT = PORT / "content" / "carry"
PATCHES = PORT / "patches"

MANIFEST = """\
# YUNG's Better Strongholds 5.1.3, carried from the ATM10 1.21.1 jar by
# horizon-port-pack at the campaign pin 1d63e0a5 (Minecraft 26.3).
# Licence: LGPL-3.0-only (META-INF/neoforge.mods.toml: license = "LGPLv3");
# the text travels in data/betterstrongholds/licence/ inside this package and
# as LICENSE at the port root. Local use only until publishing is approved.
id = "betterstrongholds"
name = "YUNG's Better Strongholds"
version = "0.2.0"
description = "A complete redesign of Minecraft's strongholds (worldgen data carry)"
authors = ["YUNGNICKYOUNG", "Acarii"]
api = "0.2"
side = "both"
capabilities = ["registries"]
"""


def main() -> int:
    if not (CONTENT / "horizon-mod.toml").is_file():
        print(f"missing carried tree: {CONTENT}", file=sys.stderr)
        return 1

    target = CONTENT / "data/betterstrongholds/worldgen/structure_set/stronghold.json"
    patched = PATCHES / "structure_set_stronghold.json"
    data = json.loads(patched.read_text(encoding="utf-8"))
    placement = data["placement"]
    assert placement["type"] == "minecraft:random_spread", placement["type"]
    assert "horizon:ring_sections" in placement, "the ring key is the point of the patch"
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"patched {target.relative_to(PORT)}: {placement['type']} + horizon:ring_sections")

    (CONTENT / "horizon-mod.toml").write_text(MANIFEST, encoding="utf-8")
    print("rewrote content/carry/horizon-mod.toml (id, 0.2.0, licence comment)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
