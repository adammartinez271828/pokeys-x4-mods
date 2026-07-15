# Weapon-mod rebalance v1 — Basic-tier testbed

The table shipped in `weapon-mod-rebalance/libraries/equipmentmods.xml`
(158 attribute replaces + 9 added bonus blocks, weapon section only).
Design rationale: `docs/weapon-mod-rebalance-design.md`. Validation:
`uv run --project ~/devel/x4-analyzer python tools/weapon-mod-rebalance/evaluate.py`
(exit 0 = all acceptance targets pass; the harness applies the diff
itself, so a sel typo is a hard error, not a silent no-op). Browsable
review dashboard: `tools/weapon-mod-rebalance/report.py` →
`output/weapon-mod-review.html`.

The **Basic tier is the finished testbed** for the design language below;
Enhanced/Exceptional carry interim values until they get the same
treatment one tier up.

## The system

- **No roll RNG.** Every range is pinned (min = max): what you craft is
  what you get, rerolling is pointless. The only randomness left is
  engine-side *selection* of optional pool bonuses on some
  Enhanced/Exceptional mods — game data cannot remove that.
- **Two buckets per tier.** The *DPS bucket* trades purely in cycle DPS:
  each mod is worth ~+16.67% (one Basic tier step) at the center of its
  niche and falls off outside it. The *utility bucket* tweaks a
  less-tangible weapon attribute and carries a flat **+10% damage rider**
  so picking utility costs ~6% DPS instead of all of it (ladder reserved
  for later tiers: +20% Enhanced, +30% Exceptional).
- **Niches come from weapon physics**, exploiting how mods multiply the
  stored field literally:
  - *Heat level*: cooling is worth nothing on the 137 heatless weapons
    and up to +50% on cooldown-dominated guns. The cooling-heavy mods are
    calibrated so their crossover points are staggered along the heat
    axis (touchpoint: S Bolt Repeater Mk1, the median heat weapon at
    38.4% cooldown).
  - *Reload storage form*: `reload rate` weapons want reload multipliers
    >1, `reload time` weapons want <1. Every reload-carrying mod picks a
    side, which fences the rate family and the time family apart.
  - *Clip weapons* only get partial value from fire rate (the clip
    reload is fixed), and *charge weapons* have a chargetime lever nobody
    else touches — those make two more niches.
- **Bounded everything**: no roll range crosses 1.0, no secondary bundle
  is worth ≥16% cycle DPS on any weapon (measured max +14.3%, Excavator's
  pool on the BOR M Ion Pulse Railgun), and tier order can never invert
  within a variant.

## Basic DPS bucket

All eight are ~+16.67% full-cycle DPS at their niche center. "Strict
wins" = weapons where the mod beats every other Basic DPS mod by >0.5%
(192 non-mining weapons with sustained DPS; ties excluded).

| Mod | Vanilla | New (fixed) | Wins | Niche |
|---|---|---|---|---|
| Piercer (damage_01_mk1) | dmg 1.05–1.2 | dmg ×1.1667 | 61 | **The generalist.** Full value on every weapon; the default on non-clip rate weapons, flak and cool-running guns. |
| Stabber (damage_02_mk1) | dmg 1.35–1.45, cooling 0.684–0.736 | dmg ×1.128, cool ×1.2 | 9 | **Lukewarm rate weapons** (~26–47% cooldown): overtakes Piercer once heat starts to matter. |
| Slasher (damage_03_mk1) | dmg 1.338–1.503, cooling 0.681–0.74, **reload 0.682–2** | dmg ×1.155, cool ×1.1, rel ×0.95 | 48 | **Reload-time weapons** (beams, mass drivers, launchers). These store reload as *seconds between shots*, and mods multiply the stored number: time ×0.95 = shorter interval = **+5.3% fire rate**. On rate-storing weapons the same ×0.95 cuts the rate by 5% — the gate. Vanilla Slasher was the ×2-reroll lottery that dominated 210/223 weapons. |
| Gregale (cooling_02_mk1) | cool 1.38–1.49, dmg 0.7–0.75 | cool ×1.55, dmg ×1.055, rel ×0.95 *(added child)* | 18 | **Warm time weapons**: takes the baton from Slasher around ~46% cooldown. The added time-flavored reload keeps its damage kicker off the rate family's turf. |
| Mistral (cooling_03_mk1) | cool 1.356–1.525, dmg 0.677–0.757, **reload 0.682–2** | cool ×1.45, dmg ×1.05, rel ×1.05 | 7 | **Warm rate weapons**: Stabber's successor from ~47% cooldown; its reload buff is a malus on time weapons, fencing it off Gregale. |
| Tramontane (cooling_01_mk1) | cool 1.048–1.216 | cool ×1.83 | 5 | **The hottest guns** (Ion Pulse Railgun +50%, Distortion Pulsor, Neutron Gatling, Muons): pure coolrate, worthless on heatless weapons. |
| Cowboy (reload_01_mk1) | **reload 0.682–2** | rel ×1.2, dmg ×1.05 *(added rider)* | 14 | **Clip/burst weapons** (Ion Blasters, gatlings): fire rate compresses the burst; the tempered rider tips it past Piercer exactly where reload pays most. −16.7% on reload-time weapons — wrong tool there by design. |
| Jumper (chargetime_01_mk1) | charge 0.8–0.95 | charge ×0.58, dmg ×1.1 *(added rider)* | 5 | **The charge cannons** (KHA Ravager/Obliterator, Ray Ion Projector, Erlking, XEN Omega): charge time is up to half the volley interval there and nothing else can buy it. Utility-grade +10% anywhere else. |

## Basic utility bucket

Orthogonal primaries — no weapon has them as its *strongest* DPS pick,
by design. Each carries the flat **+10% damage rider** (added forced
block) so the utility costs ~6% DPS vs the bucket above, not all of it.
Primaries pinned at (or retuned from) their vanilla best roll.

| Mod | Vanilla | New (fixed) | Niche |
|---|---|---|---|
| Dispatcher (speed_01_mk1) | speed 1.05–1.1 | speed ×1.25, lifetime ×0.84, dmg ×1.1 | **Velocity.** Projectiles arrive 25% faster (easier leads, better vs fast/evasive targets) at nearly unchanged range (1.25 × 0.84 = +5%). |
| Endurance (lifetime_01_mk1) | lifetime 1.05–1.2 | lifetime ×1.1, speed ×1.1, dmg ×1.1 | **Reach.** +21% projectile range (1.1 × 1.1) with the flight character unchanged — standoff work. |
| Lens (beamlength_01_mk1) | beam 1.05–1.1 | beam ×1.21, dmg ×1.1 | **Beam reach.** The beam-weapon counterpart of Endurance: +21% beam length. |
| Gimbal (rotationspeed_01_mk1) | rot 1.05–1.2 | rot ×1.2, dmg ×1.1 | **Turret tracking.** Faster slew for turrets chasing small, fast targets. |
| Gum (sticktime_01_mk1) | stick 1.05–1.2 | stick ×1.2, dmg ×1.1 | **Sticky weapons.** Longer stick time for the leech/disruptor projectile family. |
| Intruder (surfaceelement_01_mk1) | surf 1.2–1.35 | surf ×1.35, dmg ×1.1 | **Destroying surface elements** — turrets, shield generators, engines on stations and capital ships. |
| Digger (mining_01_mk1) | mining 5.25–6 | mining ×6 (no rider) | **Mining yield.** Deliberately no damage rider: a combat bonus on a mining mod re-opens the combat-cheat door. Mining weapons are excluded from all combat-mod evaluations. |

## Enhanced / Exceptional (interim)

Not yet given the testbed treatment. Current placeholder state, kept
consistent with the Basic tier (no RNG, no crossings, tier order intact):

- Damage mods pinned to tier: Assassin/Exterminator/Butcher/Slayer
  ×1.3333, Executioner ×1.36 (+cooling ×0.92 malus), Slayer keeps its
  time-flavored reload ×0.9; Obliterator/Annihilator ×1.5.
- The five Enhanced cooling mods are floored at ×1.9 (just above Basic
  Tramontane's ×1.83) to preserve tier order until properly staggered.
- Optional loot pools pinned and bounded: reload ×1.12, chargetime ×0.9,
  Annihilator's cooling ×1.15 / reload ×1.1, Expediter's damage ×1.1,
  Excavator's combat loot ×1.06/×1.1/×1.05.
- Invader keeps surface ×1.45 with a real but bounded cooling ×1.15 perk.
- Known follow-ups for that pass: stagger the cooling family crossings
  one tier up, +20%/+30% utility riders, and give Expediter a
  speed-primary identity above Basic Dispatcher's ×1.25.

Untouched: `mod_weapon_damage_fleet_battle_1` (Timelines scenario ware,
already fixed-value in vanilla) and the engine/ship/shield sections.

## Harness scorecard (all targets pass)

Metric: full-cycle DPS (steady-state where no heat/clip cycle exists),
vs-shield and vs-hull channels, 217 DPS-capable of 223 weapons/turrets;
mining weapons only count for mods that can roll a mining bonus.

- **T1 dominance** — nothing is strictly best globally on >30% of its
  eligible weapons: pass (the two Exceptional damage mods tie at ×1.5 on
  top; every Basic winner sits under them). Vanilla baseline: Slasher
  strictly best on 91.7% (the "210 of 223" from the design doc).
- **T2 usefulness** — every DPS-primary mod is best-or-tied within its
  own quality tier on ≥1 weapon: pass (see the wins column above;
  orthogonal-primary mods are best picks for their stat by definition).
- **T3 bundles** — no secondary bundle (forced, or worst-case optional
  selection) worth ≥16% cycle DPS on any weapon: pass, max +14.3%
  (Excavator pool on BOR M Ion Pulse Railgun). Vanilla max: +169.6%.
- **T4 tier order** — no lower-quality mod beats a higher-quality mod of
  the same *variant* (same primary + same DPS-carrying guaranteed
  secondaries) by >1% anywhere: pass. Cross-variant comparisons are
  deliberately unchecked — a Basic cooling mix "beats" a pure Enhanced
  cooling mod on a heatless weapon, where both are the wrong tool.
- **T5** — no roll range crosses 1.0: pass (trivial with min = max).

## Verified in-game (so far)

- All sels apply cleanly (no diff-patch errors in debug.log).
- A rebalance retroactively re-maps installed mod instances: a vanilla
  max-roll Cowboy at +100% fire rate read +20% (the new fixed value) on
  load. Releases that change values retune every ship.
- Added bonus children show up in the weapon-mod UI (Gregale's reload).
  Still to confirm: an installed Gregale applies BOTH bonuses (forced
  semantics with the bumped `bonus/@max`) — one check covers all nine
  added blocks.
