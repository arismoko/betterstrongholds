# YUNG's Better Strongholds for Sunrise

Strongholds redesigned into sprawling, varied dungeons with libraries, prisons and an end portal room.

A port of [YUNG's Better Strongholds](https://github.com/YUNG-GANG/YUNGs-Better-Strongholds) by YUNGNICKYOUNG and Acarii to [Sunrise](https://playsunrise.net) (Minecraft Java 26.3). It is a content mod: the original's structures, templates, loot tables and strings, upgraded to 26.3, with no code. The 26.3 carry is by AdLf0208 ([AdLf0208/betterstrongholds](https://github.com/AdLf0208/betterstrongholds)); this fork moves it to Sunrise.

## What it adds

- A new stronghold: 97 templates of halls, libraries, prisons, armouries and the portal room, assembled by YUNG's jigsaw rules and buried in the terrain.
- Its placement in rings around the world origin, as the original's; eyes of ender lead to it.
- Ten chest loot tables.
- Vanilla strongholds no longer generate, as in the original.

## Differences from the original

- Many of its Java processors (decoration, cobwebs, torches, spawners) are left out.
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
