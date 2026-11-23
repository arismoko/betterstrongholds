# YUNG's Better Strongholds for Sunrise

Strongholds redesigned into sprawling, varied dungeons with libraries, prisons and an end portal room.

A port of [YUNG's Better Strongholds](https://github.com/YUNG-GANG/YUNGs-Better-Strongholds) by YUNGNICKYOUNG and Acarii to [Sunrise](https://playsunrise.net) (Minecraft Java 26.3). It is a content mod: the original's structures, templates, loot tables and strings, upgraded to 26.3, with no code. The 26.3 carry is by AdLf0208 ([AdLf0208/betterstrongholds](https://github.com/AdLf0208/betterstrongholds)); this fork moves it to Sunrise.

## What it adds

- A new stronghold: 97 templates of halls, libraries, prisons, armouries and the portal room, assembled by YUNG's jigsaw rules and buried in the terrain.
- Its placement in rings around the world origin, as the original's.
- Ten chest loot tables.
- The original's dressing: banners in three designs, ore veins of coal to diamond in the walls, rare iron, gold, quartz and diamond blocks, stone brick legs down to the ground, and portal frames that hold an eye one time in ten.
- Vanilla strongholds no longer generate, as in the original.

## Differences from the original

- Armour stands and item frames are not dressed, the legs' stair brackets are not placed, and wire is not propped up on loose blocks: those processors are Java code that reaches entities or the world around.
- Eyes of ender still fly towards the vanilla stronghold positions: the game's eye does not read the `eye_of_ender_located` tag, which this mod adds the stronghold to.
- The vanilla "Eye Spy" advancement still counts only vanilla strongholds.

## Building

With the Sunrise mod tool (`cargo sunrise-mod`, from the Sunrise SDK):

```sh
cargo sunrise-mod check
cargo sunrise-mod build    # target/sunrise-mod/betterstrongholds.smod
```

This version is made for the Sunrise Dev build `dev-2026-11-22-7cfdf81`.

## Licence and credits

YUNG's Better Strongholds is by YUNGNICKYOUNG and Acarii (https://github.com/YUNG-GANG/YUNGs-Better-Strongholds). Its structures, templates, loot tables and strings are theirs and are used here under the **GNU LGPL v3.0 only**, the original's licence; `LICENSE` holds the text.

Carried to Minecraft 26.3 by AdLf0208 ([AdLf0208/betterstrongholds](https://github.com/AdLf0208/betterstrongholds)), and ported to Sunrise by arismoko. This port is distributed under the same licence.
