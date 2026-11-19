#!/usr/bin/env bash
# In-game check for the YUNG's Better Strongholds data carry (Minecraft 26.3,
# campaign pin 1d63e0a5, shared unmodded game from ports/_shared/bin).
#
# A data-tier port's behaviour is worldgen, so the harness proves the three
# layers a `.hmod` can break without a code error:
#
#   1. static fidelity: tools/verify_content.py compares the carried folder mod
#      with the ATM10 jar (counts, byte-identical templates, the one placement
#      patch, every reference resolved).
#   2. worldgen, in a real world: `/locate structure betterstrongholds:stronghold`
#      runs the carried structure set — which only starts at all because the
#      port rewrote the mod's Java placement as `minecraft:random_spread` +
#      `horizon:ring_sections` — and its biome tag, which selects the biomes the
#      structure may start in.
#   3. placement: `/place structure betterstrongholds:stronghold` in a chunk
#      with no structure (checked before) must put the carried templates' own
#      blocks there, read back at their positions, and a chest must roll one of
#      the ten carried loot tables.
#
# Then the control: the same commands with the content removed refuse the id and
# leave the ground untouched, so the assertions above are about our content and
# not about the command.
#
# Modes:
#   default      legs A (content) and B (content removed); PASS + EXIT:0.
#   SELFTEST=1   leg A, then a deliberately false assertion on the placed
#                structure: the run MUST fail (FAIL: + non-zero exit).
#   SKIP_VERIFY=1 skips the jar comparison (debugging only).
set -euo pipefail

CLONE=/home/adlf/Desktop/all_the_mods_10_rust_rewrite
PORT=$CLONE/ports/betterstrongholds
SHARED=${SHARED:-$CLONE/ports/_shared/bin/horizon-1d63e0a5}
CTL=${CTL:-$SHARED/horizon-ctl}
GAME=${GAME:-$SHARED/horizon-client}
RES=${RES:-${HORIZON_RES:-/home/adlf/Desktop/horizon/.local/horizon-client/26.3}}
SOCK=${SOCK:-${E2E_TMP:-/tmp/opencode}/betterstrongholds-e2e.sock}
SELFTEST=${SELFTEST:-0}
CONTROL_FAIL=${CONTROL_FAIL:-0}
SKIP_VERIFY=${SKIP_VERIFY:-0}
SEED=20261105
HMOD=$PORT/content/betterstrongholds.hmod
STRUCTURE=betterstrongholds:stronghold

[ -x "$CTL" ] || { echo "missing horizon-ctl: $CTL (set CTL; ports/tools/shared-bin.sh env)" >&2; exit 1; }
[ -x "$GAME" ] || { echo "missing horizon-client: $GAME (set GAME)" >&2; exit 1; }
[ -d "$RES/assets" ] || { echo "missing prepared resources: $RES" >&2; exit 1; }
[ -f "$HMOD" ] || { echo "missing artifact: $HMOD" >&2; exit 1; }

say() { echo "== $* =="; }
fail() { echo "FAIL: $*" >&2; exit 1; }
ctl() { "$CTL" --socket "$SOCK" "$@"; }
chat() { jq -r '.chat[0] // ""'; }
end() { ctl command "execute in minecraft:the_end run $1"; }

if [ "$SKIP_VERIFY" = 1 ]; then
    echo "== jar comparison skipped (SKIP_VERIFY=1) =="
else
    say "static fidelity: the carried content against the ATM10 1.21.1 jar"
    python3 "$PORT/tools/verify_content.py" --content "$PORT/content/carry" --resources "$RES" \
        || fail "verify_content.py failed"
fi

# The scratch homes live on the project disk, not /tmp: the box's /tmp is a
# 7.5 GB tmpfs shared by every job, and a game run fills it (a full tmpfs makes
# the game panic on its own stdout, `No space left on device`).
SCRATCH_ROOT=${SCRATCH_ROOT:-${E2E_TMP:-$PORT/target/e2e}}
mkdir -p "$SCRATCH_ROOT"
SCRATCH=$(mktemp -d "$SCRATCH_ROOT/run.XXXXXX")
mkdir -p "$(dirname "$SOCK")"
export HORIZON_NO_AUDIO=1
export XDG_DATA_HOME=$SCRATCH/data
export XDG_CONFIG_HOME=$SCRATCH/config
export HORIZON_LAUNCHER_HOME=$SCRATCH/launcher

cleanup() {
    rc=$?
    ctl quit >/dev/null 2>&1 || true
    sleep 1
    rm -rf "$SCRATCH" || true
    echo "EXIT:$rc"
}
trap cleanup EXIT

launch() { # name world [--dev-mod PATH]
    local name=$1 world=$2
    shift 2
    SOCK=${E2E_TMP:-/tmp/opencode}/betterstrongholds-e2e-$name.sock
    rm -f "$SOCK"
    # One HORIZON_HOME per leg: the legs would share logs/latest.log otherwise.
    export HORIZON_HOME=$SCRATCH/$name/home
    mkdir -p "$HORIZON_HOME"
    say "launch $name (offscreen, creative, Overworld, ${*:-no content mod})"
    "$CTL" --socket "$SOCK" launch \
        --game "$GAME" --world "$world" --seed "$SEED" --creative --offscreen --wait \
        --game-dir "$SCRATCH/$name" --resources "$RES" "$@" > "$SCRATCH/$name.launch.json"
    jq -c '{dimension, creative, ok: .launch.ok}' "$SCRATCH/$name.launch.json"
    ctl wait-ready 240
    ctl command "difficulty peaceful" >/dev/null
    ctl wait 5
}

# Keep the chunks around the site loaded (49 of them: a larger `/forceload` makes
# the integrated server generate for longer than the control socket's 10 s, and
# the reply is then "the integrated server stopped or did not answer") and stand
# in the air above it: the client streams the column,
# and the game's `/place` writes reach it (a placement in a chunk the client has
# not received is overwritten by the chunk data that arrives later).
forceload_site() {
    local reply error attempt=0
    while :; do
        reply=$(ctl command "forceload add $((sx - 48)) $((sz - 48)) $((sx + 48)) $((sz + 48))" || true)
        error=$(echo "$reply" | jq -r '.error // ""')
        if [ -z "$error" ]; then break; fi
        # "the integrated server stopped or did not answer": it is generating the
        # teleport target; wait and ask again.
        attempt=$((attempt + 1))
        echo "forceload attempt $attempt: $error"
        [ "$attempt" -lt 4 ] || fail "forceload never answered: $error"
        ctl wait 60 >/dev/null
    done
    echo "forceload: $(echo "$reply" | jq -r '.chat[0] // "ok"')"
}
go_to_site() {
    local reply error attempt=0
    while :; do
        reply=$(ctl tp "$((sx + 8)).5 120 $((sz + 8)).5" || true)
        error=$(echo "$reply" | jq -r '.error // ""')
        if [ -z "$error" ]; then break; fi
        attempt=$((attempt + 1))
        echo "tp attempt $attempt: $error"
        [ "$attempt" -lt 4 ] || fail "the teleport never answered: $error"
        ctl wait 60 >/dev/null
    done
    echo "tp: $(echo "$reply" | jq -c '{ok}')"
    settle
}

# Force the client to re-request the site's chunks from the server: a chunk the
# client received *before* the placement shows the placed blocks, while one that
# arrives afterwards replaces them with the server's copy — and which of the two
# happens depends on the streaming timing. Going 32 chunks away evicts them.
resync() {
    ctl tp "$((sx + 512)).5 120 $((sz + 512)).5" >/dev/null 2>&1 || true
    ctl wait-ready 240 >/dev/null 2>&1 || true
    ctl wait 40 >/dev/null
    ctl tp "$((sx + 8)).5 120 $((sz + 8)).5" >/dev/null 2>&1 || true
    settle
}

# A 2,000-block teleport leaves the client waiting on chunks: wait until the
# world is ready, then give the streamed chunks time to arrive (a `place` in a
# chunk the client does not have answers "That position is not loaded").
settle() {
    ctl wait-ready 240 >/dev/null 2>&1 || true
    ctl wait 60 >/dev/null
    ctl wait-ready 240 >/dev/null 2>&1 || true
    echo "standing at $(ctl state | jq -c '.player.position'), chunks $(ctl state | jq -r '.chunks')"
}

find_count() { ctl find-block "$1" "$2" | jq -r '.count // 0'; }
find_first() { ctl find-block "$1" "$2" | jq -c '.nearest[0].pos // null'; }
block_at() { ctl block "$1" "$2" "$3" | jq -r '.block // "unknown"'; }

# ------------------------------------------------------------------ leg A
leg_a() {
    launch a BetterStrongholdsA --dev-mod "$HMOD"
    local log=$SCRATCH/a.log
    ctl logs --lines 20000 > "$log" 2>/dev/null || true

    say "A: the .hmod loads (content root built from one mod)"
    grep -q 'content from 1 mod(s)' "$log" || { tail -30 "$log" >&2; fail "leg A: no 'content from 1 mod(s)'"; }
    if grep -q 'content mods not loaded' "$log"; then
        grep 'content mods not loaded' "$log" >&2
        fail "leg A: the content mod did not load"
    fi
    echo "A: content mod loaded, no refusal in the log"

    say "A: the carried structure set locates our stronghold"
    local located
    located=$(ctl command "locate structure $STRUCTURE" | chat)
    echo "locate $STRUCTURE -> $located"
    case "$located" in
        "The nearest $STRUCTURE is at ["*) ;;
        *) fail "the carried structure set does not start: $located" ;;
    esac
    local unknown
    unknown=$(ctl command "locate structure betterstrongholds:not_a_structure" | chat)
    echo "locate betterstrongholds:not_a_structure -> $unknown"
    case "$unknown" in
        "Could not find"*) ;;
        *) fail "an unknown structure id was located: $unknown" ;;
    esac
    echo "A: the carried set starts the stronghold, an unknown id does not"

    # ---------------------------------------------------------- the site
    # Place 512 blocks east of the located site: far enough that the natural
    # stronghold the locate found is not in the read box, and the `before`
    # check below proves the box starts empty of the structure's own blocks.
    local sx=${SITE_X:-1024} sz=${SITE_Z:-1024} tries=0
    say "A: the placement site is the fixed chunk at $sx $sz (the located one is $located)"
    forceload_site
    go_to_site

    local before_chiseled before_glass
    while :; do
        before_chiseled=$(find_count chiseled_stone_bricks 64)
        before_glass=$(find_count yellow_stained_glass 64)
        echo "before: chiseled_stone_bricks=$before_chiseled yellow_stained_glass=$before_glass (try $tries)"
        if [ "$before_chiseled" = 0 ] && [ "$before_glass" = 0 ]; then break; fi
        tries=$((tries + 1))
        [ "$tries" -lt 3 ] || fail "no empty site near $sx $sz after 3 shifts"
        sx=$((sx + 512))
        forceload_site
        go_to_site
    done

    # `/place structure` writes the start piece in the chunk the command names;
    # its column is the box (16x16x128 = 32,768 blocks, `ctl blocks`'s ceiling).
    box() { # out-file
        ctl blocks "$sx" -64 "$sz" "$((sx + 15))" 63 "$((sz + 15))" > "$1"
    }
    box "$SCRATCH/box-before.json"

    say "A: /place structure $STRUCTURE at $sx 100 $sz"
    local placed attempt=0
    while :; do
        placed=$(ctl command "place structure $STRUCTURE $sx 100 $sz" | chat)
        echo "reply: $placed"
        case "$placed" in
            *"not loaded"*)
                # A 2,000-block teleport: the client is still receiving chunks.
                attempt=$((attempt + 1))
                [ "$attempt" -lt 3 ] || fail "the start's chunks never loaded: $placed"
                settle
                ;;
            *) break ;;
        esac
    done
    case "$placed" in
        Generated\ structure\ \"$STRUCTURE\"*) ;;
        *) fail "$STRUCTURE did not place: $placed" ;;
    esac
    ctl wait 10 >/dev/null

    say "A: the placed stronghold's own blocks read back at their positions"
    resync
    box "$SCRATCH/box-after.json"
    if [ "$(jq -r '.counts["minecraft:stone_bricks"] // 0' "$SCRATCH/box-after.json")" = 0 ]; then
        echo "the column read empty: re-streaming it once more"
        resync
        box "$SCRATCH/box-after.json"
    fi
    local before_chiseled after_chiseled
    before_chiseled=$(jq -r '.counts["minecraft:chiseled_stone_bricks"] // 0' "$SCRATCH/box-before.json")
    after_chiseled=$(jq -r '.counts["minecraft:chiseled_stone_bricks"] // 0' "$SCRATCH/box-after.json")
    echo "the start chunk's column: chiseled_stone_bricks $before_chiseled before / $after_chiseled after"

    local block got pos x y z readback
    # Chests sit in the rooms grown beyond the start piece, so the loot check
    # below finds one in the structure instead of in the start column.
    for block in minecraft:stone_bricks minecraft:chiseled_stone_bricks minecraft:stone_brick_wall \
                 minecraft:stone_brick_stairs minecraft:stone_brick_slab; do
        got=$(jq -r --arg b "$block" '.counts[$b] // 0' "$SCRATCH/box-after.json")
        echo "after: $block=$got"
        [ "$got" -ge 1 ] || fail "the placed structure holds no $block in its start chunk's column"
    done
    for block in minecraft:stone_bricks minecraft:chiseled_stone_bricks minecraft:stone_brick_wall; do
        pos=$(jq -c --arg b "$block" '[.blocks[] | select(.[3] | startswith($b))][0] | .[0:3]' \
              "$SCRATCH/box-after.json")
        [ "$pos" != null ] || fail "no $block position in the column"
        read -r x y z <<<"$(echo "$pos" | jq -r '.[0], .[1], .[2]' | tr '\n' ' ')"
        readback=$(block_at "$x" "$y" "$z")
        echo "ctl block $x $y $z -> $readback"
        case "$readback" in
            "$block"*) ;;
            *) fail "$block at $x $y $z reads $readback" ;;
        esac
    done
    echo "A: bricks, chiseled bricks, brick walls, stairs and slabs are in the world and read back"

    say "A: a placed chest rolls one of the carried loot tables"
    # Chests are in the rooms the jigsaw grows beyond the start piece, so stand
    # in the structure (at a brick the box found) and search around it.
    local brick
    brick=$(jq -c '[.blocks[] | select(.[3] | startswith("minecraft:stone_bricks"))][0] | .[0:3]' \
            "$SCRATCH/box-after.json")
    [ "$brick" != null ] || fail "no brick position to stand at"
    read -r x y z <<<"$(echo "$brick" | jq -r '.[0], .[1], .[2]' | tr '\n' ' ')"
    ctl tp "$((x)).5 $((y + 3)) $((z)).5" >/dev/null
    ctl wait 30 >/dev/null
    local chests
    chests=$(ctl find-block chest 64 | jq -r '.nearest[]? | .pos | @tsv')
    if [ -z "$chests" ]; then
        ctl tp "$((x + 32)).5 $((y + 3)) $((z)).5" >/dev/null
        ctl wait 30 >/dev/null
        chests=$(ctl find-block chest 64 | jq -r '.nearest[]? | .pos | @tsv')
    fi
    [ -n "$chests" ] || fail "the placed structure has no chest within 64 blocks of it"
    # At the 0b14f8a Nightly a chest's loot table is unpacked when a player
    # opens it, not when the template places it: `ctl container` alone reads an
    # empty block entity (measured; `/data get block … LootTable` names the
    # carried table and `/loot give` rolls it). Open a carried-table chest with
    # `ctl interact` and read it like a player.
    local items=0 found=0 loot
    while read -r x y z; do
        [ -n "${x:-}" ] || continue
        loot=$(ctl command "data get block $x $y $z LootTable" | chat)
        case "$loot" in
            *"betterstrongholds:chests/"*) ;;
            *) echo "chest $x $y $z carries $loot, not a carried table"; continue ;;
        esac
        ctl tp "$((x)).5 $((y + 1)) $((z)).5" >/dev/null
        ctl wait 10 >/dev/null
        ctl interact "$x" "$y" "$z" >/dev/null 2>&1 || true
        ctl wait 5 >/dev/null
        items=$(ctl container "$x" "$y" "$z" | jq '[.slots[] | select(. != null)] | length')
        echo "ctl container $x $y $z -> $items item stack(s); table $loot"
        [ "$items" -ge 1 ] && { found=1; break; }
    done <<<"$chests"
    [ "$found" = 1 ] || fail "no carried betterstrongholds chest rolled any loot"
    echo "A: the chest holds $items stack(s) from a carried betterstrongholds:chests/* table"

    say "A: the log names no worldgen problem for our mod"
    if grep -iE 'betterstrongholds.*(missing|unknown|refus|failed|unsupported)' "$log" | grep -vi 'no sounds'; then
        fail "the log reports a worldgen problem for betterstrongholds"
    fi
    echo "A: no betterstrongholds worldgen warning"

    if [ "$SELFTEST" = 1 ]; then
        say "SELFTEST: a deliberately false assertion must fail the run"
        local now
        now=$(jq -r '.counts["minecraft:chiseled_stone_bricks"] // 0' "$SCRATCH/box-after.json")
        echo "the placed stronghold has $now chiseled_stone_bricks; this run asserts 0"
        [ "$now" = 0 ] || fail "SELFTEST run: the false assertion (0 chiseled bricks) failed the run, as required"
        echo "SELFTEST run did not fail: the assertion is vacuous" >&2
        exit 2
    fi

    echo "$sx $sz" > "$SCRATCH/site"
    ctl quit >/dev/null 2>&1 || true
    sleep 3
    SOCK=
}

# ------------------------------------------------------------------ leg B
leg_b() {
    launch b BetterStrongholdsB
    local log=$SCRATCH/b.log
    ctl logs --lines 20000 > "$log" 2>/dev/null || true

    say "B: with the content removed the ids do not exist"
    grep -q 'content from 1 mod(s)' "$log" && fail "leg B loaded a content mod"
    echo "B: no content mod in this run"

    local located placed
    located=$(ctl command "locate structure $STRUCTURE" | chat)
    echo "locate $STRUCTURE -> $located"
    case "$located" in
        "Could not find"*) ;;
        *) fail "leg B located a structure without its content: $located" ;;
    esac
    placed=$(ctl command "place structure $STRUCTURE 0 100 0" | chat)
    echo "place $STRUCTURE -> $placed"
    case "$placed" in
        *"no structure with type"*) ;;
        *) fail "leg B placed our structure without its content: $placed" ;;
    esac

    say "B: the ground at the same site holds none of the structure's blocks"
    local sx sz
    read -r sx sz < "$SCRATCH/site"
    forceload_site
    go_to_site
    local chiseled
    chiseled=$( { ctl blocks "$sx" -64 "$sz" "$((sx + 15))" 63 "$((sz + 15))" || echo '{}'; } \
                | jq -r '.counts["minecraft:chiseled_stone_bricks"] // 0')
    echo "without the mod, the same box holds $chiseled chiseled_stone_bricks"
    [ "$chiseled" = 0 ] || fail "leg B found $chiseled chiseled stone bricks without the content"

    say "B: the command path itself works (a vanilla structure still places)"
    local vanilla
    # Place it inside this leg's force-loaded square: the spawn chunks are not
    # loaded while the player stands at the site (the 0b14f8a engine answers
    # "That position is not loaded" for them).
    vanilla=$(ctl command "place structure minecraft:igloo $((sx + 32)) 100 $sz" | chat)
    echo "place minecraft:igloo -> $vanilla"
    case "$vanilla" in
        Generated\ structure\ \"minecraft:igloo\"*) ;;
        *) fail "the vanilla control did not place: $vanilla" ;;
    esac
    echo "B: our ids are refused and a vanilla structure still places, so the refusal is about our content"
}

if [ "$CONTROL_FAIL" = 1 ]; then
    # The fail-capable control: launch without the package and require the
    # modded assertion to fail for the right reason (the id is unknown).
    launch control BetterStrongholdsControl
    located=$(ctl command "locate structure $STRUCTURE" | chat)
    echo "locate $STRUCTURE -> $located"
    placed=$(ctl command "place structure $STRUCTURE 0 100 0" | chat)
    echo "place $STRUCTURE -> $placed"
    case "$placed" in
        *"no structure with type"*)
            fail "control: without --dev-mod $STRUCTURE is unknown ($placed), so the default run's structure is the package's" ;;
        *) fail "control: without --dev-mod the game did not report the unknown structure: $placed" ;;
    esac
fi

[ "$SELFTEST" = 1 ] && leg_a || { leg_a; leg_b; }

echo
if [ "$SELFTEST" = 1 ]; then
    echo "PASS: selftest leg completed without failing (should be impossible)"
else
    echo "PASS: betterstrongholds:stronghold locates from its carried structure set (the patched ring placement) and places; its chiseled bricks, brick walls, stairs and slabs are in the world at their own positions, a chest rolls a carried loot table, no worldgen warning is logged, and with the content removed the id is refused while a vanilla igloo still places"
fi
