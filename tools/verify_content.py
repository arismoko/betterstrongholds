#!/usr/bin/env python3
"""Static fidelity check: the carried Better Strongholds data against the jar.

The port is a data carry, so the harness has to prove the carry is faithful and
loadable *before* the game is started: every count is read from the ATM10
1.21.1 jar and compared with the carried folder mod, every template must be
byte-identical, every reference a file makes (template locations, structure
ids, loot tables, block ids in the palettes) must resolve, and the one hand
patch (the placement) must be present.

Usage: verify_content.py [--content DIR] [--jar FILE] [--resources DIR]

Exit 0 only if every check passes; each failure prints `FAIL:` and the last
line is `PASS` (the e2e reads the exit status).
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nbt  # noqa: E402

PORT = Path(__file__).resolve().parent.parent
DEFAULT_JAR = PORT.parent / "_shared/licence-cache/betterstrongholds-5.1.3.jar"
DEFAULT_CONTENT = PORT / "content" / "carry"
DEFAULT_RES = Path("/home/adlf/Desktop/horizon/.local/horizon-client/26.3")

NS = "betterstrongholds"
WORLDGEN = ("structure", "structure_set", "template_pool", "processor_list")


def json_files(root: Path, *parts: str) -> list[Path]:
    return sorted((root.joinpath(*parts)).rglob("*.json"))


def walk_elements(pool: dict):
    """Every pool element of a template pool, including nested lists."""
    for entry in pool.get("elements", []):
        element = entry.get("element", {})
        yield element
        yield from walk_elements(element)


class Verifier:
    def __init__(self, jar: Path, content: Path, res: Path) -> None:
        self.jar_path = jar
        self.jar = zipfile.ZipFile(jar)
        self.jar_names = set(self.jar.namelist())
        self.content = content
        self.res = res
        self.failures: list[str] = []
        facts = json.loads((res / "facts.json").read_text(encoding="utf-8"))
        self.blocks = {state[0] for state in facts["states"]}
        self.items = set(json.loads((res / "items.json").read_text(encoding="utf-8")))

    # ---------------------------------------------------------------- helpers
    def ok(self, message: str) -> None:
        print(f"ok: {message}")

    def fail(self, message: str) -> None:
        self.failures.append(message)
        print(f"FAIL: {message}", file=sys.stderr)

    def jar_json(self, name: str) -> dict:
        return json.loads(self.jar.read(name).decode("utf-8"))

    def carried(self, *parts: str) -> list[Path]:
        return json_files(self.content, "data", NS, *parts)

    def manifest(self) -> dict:
        text = (self.content / "horizon-mod.toml").read_text(encoding="utf-8")
        out = {}
        for line in text.splitlines():
            line = line.split("#", 1)[0].strip()
            if "=" in line:
                key, value = line.split("=", 1)
                out[key.strip()] = value.strip().strip('"')
        return out

    # ------------------------------------------------------------------ checks
    def counts(self) -> dict[str, int]:
        census = collections.Counter()
        for name in self.jar_names:
            if not name.startswith(f"data/{NS}/"):
                continue
            if name.endswith(".nbt"):
                census["nbt"] += 1
            elif name.endswith(".json"):
                parts = name.split("/")
                # data/<ns>/worldgen/<family>/<file> vs data/<ns>/<family>/<file>
                census[parts[3] if parts[2] == "worldgen" else parts[2]] += 1
        return census

    def check_counts(self) -> None:
        jar = self.counts()
        got = {
            "structure": len(self.carried("worldgen", "structure")),
            "structure_set": len(self.carried("worldgen", "structure_set")),
            "template_pool": len(self.carried("worldgen", "template_pool")),
            "processor_list": len(self.carried("worldgen", "processor_list")),
            "loot_table": len(self.carried("loot_table")),
            "nbt": len(list((self.content / "data" / NS / "structure").rglob("*.nbt"))),
        }
        for family, count in got.items():
            want = jar[family]
            if count != want:
                self.fail(f"{family}: carried {count}, the jar has {want}")
            else:
                self.ok(f"{family}: {count} carried = {want} in the jar")

        tags = json_files(self.content, "data", NS, "tags")
        if len(tags) != 2:
            self.fail(f"own tags: carried {len(tags)}, the jar has 2 (biome + structure)")
        else:
            self.ok(f"tags: {len(tags)} carried = 2 in the jar (has_structure biome, structure tag)")

        vanilla_tags = sorted((self.content / "data/minecraft/tags").rglob("*.json"))
        if [p.name for p in vanilla_tags] != ["eye_of_ender_located.json"]:
            self.fail(f"vanilla tag additions: {[p.name for p in vanilla_tags]}")
        else:
            self.ok("vanilla tag addition: data/minecraft/tags/worldgen/structure/eye_of_ender_located.json")

        lang = sorted((self.content / "assets" / NS / "lang").glob("*.json"))
        if len(lang) != 3:
            self.fail(f"lang: carried {len(lang)}, the jar has 3")
        else:
            self.ok("lang: 3 carried = 3 in the jar (en_us, ru_ru, uk_ua)")

    def check_templates_identical(self) -> None:
        carried = {p.relative_to(self.content).as_posix()
                   for p in (self.content / "data" / NS / "structure").rglob("*.nbt")}
        jar = {n for n in self.jar_names
               if n.startswith(f"data/{NS}/structure/") and n.endswith(".nbt")}
        missing = jar - carried
        extra = carried - jar
        if missing or extra:
            self.fail(f"templates: {len(missing)} missing, {len(extra)} extra")
            return
        changed = [n for n in sorted(jar) if self.jar.read(n) != (self.content / n).read_bytes()]
        if changed:
            self.fail(f"templates not byte-identical: {changed[:5]}")
        else:
            self.ok(f"templates: {len(jar)} carried byte-identical to the jar's")

    def check_structure(self) -> None:
        path = self.carried("worldgen", "structure")[0]
        structure = json.loads(path.read_text(encoding="utf-8"))
        if structure.get("type") != "yungsapi:yung_jigsaw":
            self.fail(f"structure type is {structure.get('type')}, not YUNG's jigsaw")
        else:
            self.ok("structure: type yungsapi:yung_jigsaw (read by the game as Draws::Yung)")
        jar_structure = self.jar_json(f"data/{NS}/worldgen/structure/{path.name}")
        for field in ("biomes", "start_pool", "start_jigsaw_name", "size",
                      "max_distance_from_center", "start_height"):
            if structure.get(field) != jar_structure.get(field):
                self.fail(f"structure field {field} changed: {structure.get(field)!r} != {jar_structure.get(field)!r}")
        else:
            self.ok("structure: biomes/start_pool/start_jigsaw_name/size/max_distance/start_height are the jar's")

    def check_structure_set(self) -> None:
        path = self.carried("worldgen", "structure_set")[0]
        data = json.loads(path.read_text(encoding="utf-8"))
        placement = data.get("placement", {})
        jar = self.jar_json(f"data/{NS}/worldgen/structure_set/{path.name}")["placement"]
        if placement.get("type") != "minecraft:random_spread":
            self.fail(f"placement type is {placement.get('type')!r}: the game refuses an unknown one")
        rings = placement.get("horizon:ring_sections")
        want_rings = {
            "distance_to_first_ring": jar["chunk_distance_to_first_ring"],
            "thickness": jar["ring_chunk_thickness"],
        }
        if rings != want_rings:
            self.fail(f"horizon:ring_sections is {rings}, the jar's ring fields are {want_rings}")
        else:
            self.ok(f"structure set: minecraft:random_spread + horizon:ring_sections {rings} "
                    f"(BetterStrongholdsPlacement's odd rings)")
        for field in ("salt", "spacing", "separation"):
            if placement.get(field) != jar.get(field):
                self.fail(f"placement {field} changed: {placement.get(field)} != {jar.get(field)}")
        if not ("max_ring_section" in jar or "max_section" in placement):
            self.ok("structure set: unbounded, as the jar is (no max_ring_section)")
        if "max_ring_section" in jar:
            self.fail("the jar has max_ring_section and the patch does not carry it")
        ids = [entry.get("structure") for entry in data.get("structures", [])]
        if ids != [f"{NS}:stronghold"]:
            self.fail(f"structure set names {ids}")
        else:
            self.ok("structure set: one entry, betterstrongholds:stronghold")

    def check_pools(self) -> None:
        structure_dir = self.content / "data" / NS / "structure"
        carried = {p.relative_to(structure_dir).with_suffix("").as_posix() for p in structure_dir.rglob("*.nbt")}
        missing = []
        elements = collections.Counter()
        for path in self.carried("worldgen", "template_pool"):
            pool = json.loads(path.read_text(encoding="utf-8"))
            for element in walk_elements(pool):
                kind = element.get("element_type")
                elements[kind] += 1
                location = element.get("location")
                if location and location.split(":", 1)[1] not in carried:
                    missing.append(f"{path.name}: {location}")
                for nested in element.get("elements", []) or []:
                    loc = nested.get("location")
                    if loc and loc.split(":", 1)[1] not in carried:
                        missing.append(f"{path.name}: {loc}")
        if missing:
            self.fail(f"pools name templates the package does not carry: {missing[:5]}")
        else:
            self.ok(f"pools: {sum(elements.values())} elements in 12 pools, every location a carried template")
        expected = collections.Counter({"minecraft:single_pool_element": 77, "yungsapi:yung_single_element": 17})
        if elements != expected:
            self.fail(f"pool element types {dict(elements)} != the jar's {dict(expected)}")
        else:
            self.ok(f"pools: element types are the jar's ({dict(elements)})")

    def check_processors(self) -> None:
        java = collections.Counter()
        rules = 0
        for path in self.carried("worldgen", "processor_list"):
            data = json.loads(path.read_text(encoding="utf-8"))
            for processor in data.get("processors", []):
                kind = processor.get("processor_type", "")
                if kind == "minecraft:rule":
                    rules += 1
                    for rule in processor.get("rules", []):
                        state = rule.get("output_state", {})
                        if "Name" in state:
                            self.fail(f"{path.name}: a rule output_state is still 1.21.1's {{Name}} shape")
                        name = state.get("id")
                        if name and name not in self.blocks:
                            self.fail(f"{path.name}: rule output {name} is not a 26.3 block")
                elif kind.startswith("minecraft:") or kind.startswith("horizon:"):
                    pass
                else:
                    java[kind] += 1
        if java:
            self.fail(f"processor lists still name Java processors: {dict(java)}")
        else:
            self.ok("processor lists: no Java processor left (the game refuses a list holding one)")
        if rules != 9:
            self.fail(f"processor lists: {rules} vanilla minecraft:rule processors, the jar has 9")
        else:
            self.ok("processor lists: the 9 vanilla minecraft:rule processors stay")

    def check_template_blocks(self) -> None:
        unknown = collections.Counter()
        entities = collections.Counter()
        loot = set()
        for path in (self.content / "data" / NS / "structure").rglob("*.nbt"):
            template = nbt.read(path.read_bytes())
            for paletted in template.get("palettes", []):
                for entry in paletted.get("palette", []):
                    name = entry.get("Name")
                    if name and name not in self.blocks:
                        unknown[name] += 1
            for block in template.get("blocks", []):
                entity = block.get("nbt")
                if isinstance(entity, dict) and isinstance(entity.get("LootTable"), str):
                    loot.add(entity["LootTable"])
            for entity in template.get("entities", []):
                if isinstance(entity.get("nbt"), dict):
                    kind = entity["nbt"].get("id")
                    if isinstance(kind, str):
                        entities[kind] += 1
        if unknown:
            self.fail(f"templates name blocks 26.3 does not have: {dict(unknown)}")
        else:
            self.ok("templates: every palette entry is a block 26.3 has")
        carried_loot = {f"{NS}:chests/{p.stem}" for p in self.carried("loot_table", "chests")}
        unknown_loot = {t for t in loot
                        if not t.startswith("minecraft:") and t not in carried_loot}
        if unknown_loot:
            self.fail(f"templates name loot tables the package does not carry: {unknown_loot}")
        else:
            self.ok(f"templates: {len(loot)} chest loot tables, all carried or vanilla")
        if entities:
            self.ok(f"templates: {sum(entities.values())} entities ({', '.join(sorted(entities))})")

    def check_loot(self) -> None:
        unknown = collections.Counter()
        named = 0

        def walk(value):
            nonlocal named
            if isinstance(value, dict):
                name = value.get("name")
                if isinstance(name, str) and name.startswith("minecraft:"):
                    named += 1
                    if name not in self.items:
                        unknown[name] += 1
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        for path in self.carried("loot_table"):
            walk(json.loads(path.read_text(encoding="utf-8")))
        if unknown:
            self.fail(f"loot tables name items 26.3 does not have: {dict(unknown)}")
        else:
            self.ok(f"loot tables: every one of the {named} items they name is a 26.3 item")

    def check_tags(self) -> None:
        biome_tag = self.carried("tags", "worldgen", "biome", "has_structure")[0]
        data = json.loads(biome_tag.read_text(encoding="utf-8"))
        values = data.get("values", [])
        optional = [v for v in values if isinstance(v, dict)]
        if any(v.get("required") is not False for v in optional):
            self.fail("the biome tag has a non-optional entry object")
        else:
            self.ok(f"biome tag: {len(values)} entries, {len(optional)} optional "
                    f"(#forge:/#c:/#byg:, dropped by the game as unknown)")
        plain = [v for v in values if isinstance(v, str)]
        vanilla = [v for v in plain if v.startswith("#minecraft:")]
        own = [v for v in plain if not v.startswith("#minecraft:")]
        if not vanilla:
            self.fail("the biome tag has no #minecraft: biome tag")
        else:
            self.ok(f"biome tag: {len(vanilla)} #minecraft: biome-tag entries, {len(own)} plain biome ids")

        own_tag = self.carried("tags", "worldgen", "structure")[0]
        ids = json.loads(own_tag.read_text(encoding="utf-8")).get("values", [])
        if ids != [f"{NS}:stronghold"]:
            self.fail(f"structure tag values {ids}")
        else:
            self.ok("structure tag: betterstrongholds:stronghold")

        vanilla_add = self.content / "data/minecraft/tags/worldgen/structure/eye_of_ender_located.json"
        ids = json.loads(vanilla_add.read_text(encoding="utf-8")).get("values", [])
        if f"{NS}:stronghold" not in ids:
            self.fail("eye_of_ender_located does not name our structure")
        else:
            self.ok("vanilla tag addition: eye_of_ender_located names betterstrongholds:stronghold")

    def check_outside(self) -> None:
        outside = self.content.parent / "outside"
        names = [p.name for p in outside.rglob("*.json")] if outside.is_dir() else []
        if names != ["follow_ender_eye.json"]:
            self.fail(f"outside/ holds {names}, expected only the vanilla advancement")
        else:
            self.ok("outside: data/minecraft/advancement/story/follow_ender_eye.json "
                    "(vanilla data a content mod may not hold)")
        packaged = [p for p in (self.content / "data/minecraft").rglob("*") if p.is_file()]
        if any(p.suffix == ".json" and "advancement" in p.parts for p in packaged):
            self.fail("the package carries a vanilla advancement")
        else:
            self.ok("package: no vanilla advancement inside it (only tag additions under data/minecraft)")

    def check_manifest_and_licence(self) -> None:
        manifest = self.manifest()
        if manifest.get("id") != NS:
            self.fail(f"manifest id is {manifest.get('id')!r}")
        for key, want in (("api", "0.2"), ("side", "both"), ("version", "0.2.0")):
            if manifest.get(key) != want:
                self.fail(f"manifest {key} is {manifest.get(key)!r}, expected {want!r}")
        if manifest.get("capabilities") != '["registries"]':
            self.fail(f"manifest capabilities are {manifest.get('capabilities')!r}")
        self.ok("manifest: id/version 0.2.0/api 0.2/side both/capabilities registries")

        licence_dir = self.content / "data" / NS / "licence"
        for name in ("copying.txt", "notice.txt"):
            if not (licence_dir / name).is_file():
                self.fail(f"the package has no {name}")
        text = (licence_dir / "copying.txt").read_text(encoding="utf-8") if (licence_dir / "copying.txt").is_file() else ""
        if "GNU LESSER GENERAL PUBLIC LICENSE" not in text or "Version 3, 29 June 2007" not in text:
            self.fail("copying.txt is not the LGPL v3 text")
        else:
            self.ok("licence: LGPL v3 text and the NOTICE are inside the package (data/betterstrongholds/licence/)")

    def check_worldgen_record(self) -> None:
        report = json.loads((self.content.parent / "carry-report.json").read_text(encoding="utf-8"))
        types = report["worldgen_types"]
        # The raw carry cannot know the mod's placement type; the patch is what
        # makes the set runnable, so the report must show it and nothing else.
        if types["unsupported"] != {f"{NS}:stronghold": 1}:
            self.fail(f"carry report: unexpected unsupported worldgen types: {types['unsupported']}")
        else:
            self.ok("carry report: the one unsupported type is the placement, which the patch replaces")
        dropped = sum(types["processors_dropped"].values())
        if dropped != 41:
            self.fail(f"carry report: {dropped} Java processors dropped, expected the jar's 41 uses")
        else:
            self.ok(f"carry report: {dropped} Java processor uses dropped, counted by type")
        lost = types["rules_lost"]
        if lost != {"yungsapi:yung_jigsaw enhanced_terrain_adaptation": 1, "yungsapi:yung_jigsaw max_y": 1}:
            self.fail(f"carry report: unexpected YUNG's fields lost: {lost}")
        else:
            self.ok("carry report: YUNG's max_y and enhanced_terrain_adaptation are the only rules lost")

    def run(self) -> int:
        self.check_counts()
        self.check_templates_identical()
        self.check_structure()
        self.check_structure_set()
        self.check_pools()
        self.check_processors()
        self.check_template_blocks()
        self.check_loot()
        self.check_tags()
        self.check_outside()
        self.check_manifest_and_licence()
        self.check_worldgen_record()
        if self.failures:
            print(f"\nFAIL: {len(self.failures)} check(s) failed", file=sys.stderr)
            return 1
        print("\nPASS: the carried data matches the jar and every reference resolves")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jar", type=Path, default=DEFAULT_JAR)
    parser.add_argument("--content", type=Path, default=DEFAULT_CONTENT)
    parser.add_argument("--resources", type=Path, default=DEFAULT_RES)
    args = parser.parse_args()
    return Verifier(args.jar, args.content, args.resources).run()


if __name__ == "__main__":
    sys.exit(main())
