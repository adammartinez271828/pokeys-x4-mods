# Weapon-mod rebalance v1 — Basic-tier testbed

The table shipped in `weapon-mod-rebalance/libraries/equipmentmods.xml`
(166 ops: attribute replaces + added bonus blocks, weapon section only).
Design rationale: `docs/weapon-mod-rebalance-design.md`. Validation:
`uv run --project ~/devel/x4-analyzer python tools/weapon-mod-rebalance/evaluate.py`
(exit 0 = all acceptance targets pass; the harness applies the diff
itself, so a sel typo is a hard error, not a silent no-op). Interactive
prototyping: the slider tool `tools/weapon-mod-rebalance/tuner.html`
(rebuild with `dump_data.py`) recomputes the within-tier win/tie split
live as you drag mod values.

The **Basic tier is the finished testbed** for the design language below;
Enhanced/Exceptional carry interim values until they get the same
treatment one tier up.

## The system

The Basic tier is the seven non-empty **combinations** of the three DPS
stats — damage, cooling, reload — one mod each, no two sharing an effect
set, plus a chargetime specialist (Jumper) and the utility mods. With only
three levers, those seven combinations don't produce seven distinct
positions; they collapse into **two structural classes**. This is a
property of the physics, not a tuning choice.

- **No roll RNG.** Every range is pinned (min = max): what you craft is
  what you get, rerolling is pointless. The only randomness left is
  engine-side *selection* of optional pool bonuses on some
  Enhanced/Exceptional mods — game data cannot remove that.

- **Baseline — Piercer (damage).** Damage is full value on *every* weapon
  (a heavy shot on a heat gun even runs cooler per point of DPS), so
  Piercer is the universal default and the benchmark the rest are measured
  against, not a niche pick. Its universality is a gravity well: it
  contests the clip weapons and the warm guns everywhere at once.

- **Specialists — Cowboy (reload), Tramontane (cooling), Mistral
  (cooling+reload).** Each PEAKS in one physical domain and does little
  outside it — a high ceiling on a narrow set:
  - *Reload* (Cowboy) is full value on heatless and clip weapons but taxed
    on heat guns (faster firing just adds heat); it owns continuous
    heatless turrets cleanly.
  - *Cooling* (Tramontane) is huge on the hottest heat-limited main guns
    and literally nothing on the heatless majority or on turrets (turrets
    have no heat mechanic).
  - *cooling+reload* (Mistral) is the **one pair that earns a niche**,
    because its two effects SYNERGISE: the coolrate pays the heat bill the
    extra fire rate runs up, so the rate converts to real DPS on hot
    rapid-fire guns — a peak neither single stat reaches.

- **Generalists — Stabber (damage+reload), Gregale (damage+cooling),
  Slasher (damage+cooling+reload).** Each blends damage with a stat that
  is a SUBSTITUTE for damage, not a synergy, so it can never out-damage
  Piercer nor out-focus the matching specialist. They live in the tie band
  as damage-backed **safe picks**: broad best-or-tied coverage, few strict
  wins (Slasher, the triple, has the lowest peak and the widest tie
  coverage — the archetypal all-rounder). The values are a deliberate
  equilibrium — push a generalist down and Piercer eats its weapons, push
  it up and it mints a rogue specialist that kills a real one.

- **Niches come from weapon physics**, exploiting how mods multiply the
  stored field literally: *heat level* (cooling is worthless on the
  heatless majority, decisive on cooldown-dominated guns), *clip vs.
  continuous* fire (clips only pay partial value on fire rate — the clip
  reload is fixed), and the *chargetime* lever nobody but Jumper touches.

- **Bounded everything**: no roll range crosses 1.0, no secondary bundle
  is worth ≥25% cycle DPS on any weapon (measured max +14.4%, Annihilator
  on the ATF XL Main Battery — a combo mod's secondaries are part of its
  identity, so the cap sits near the strongest single-stat headline, not
  the old 16%), and tier order can never invert within a variant.

## Basic DPS bucket

Values below are the shipped equilibrium. **Strict wins** = weapons where
the mod beats every other Basic DPS mod by >0.5% (the tuner's within-tier
split, over the 211 obtainable non-KHA weapons; ties counted separately).
`g`/`t` = wins on main guns / turrets. **best%** = share of a mod's
eligible weapons where it is best-or-tied — the generalist signature is
*high best%, low strict wins*.

| Mod | Class | Vanilla | New (fixed) | Strict | best% | Role |
|---|---|---|---|---|---|---|
| Piercer (damage_01_mk1) | **baseline** | dmg 1.05–1.2 | dmg ×1.15 | 37 (13g/24t) | 45% | **Universal default & benchmark.** Full value everywhere; contests the clip weapons and warm guns at once — the gravity well the generalists orbit. |
| Cowboy (reload_01_mk1) | specialist | **reload 0.682–2** | rel ×1.225 | 21 (2g/19t) | 13% | **Reload.** Owns continuous heatless turrets cleanly; full value on clips, taxed on heat guns. Headline sits above a damage single's because reload is situational where damage is universal. |
| Tramontane (cooling_01_mk1) | specialist | cool 1.048–1.216 | cool ×1.4 | 10 (10g) | 8% | **Cooling.** The hottest heat-limited main guns; pure coolrate, worthless on the heatless majority and on turrets. Narrow, high ceiling. |
| Mistral (cooling_03_mk1) | specialist | cool 1.356–1.525, dmg 0.677–0.757, **reload 0.682–2** | cool ×1.32, rel ×1.125 *(dmg child pinned 1.0)* | 9 (9g) | 12% | **Cooling+reload — the one synergistic pair.** Coolrate pays the heat bill the fire rate runs up, so rate converts to DPS: the pick for hot rapid-fire guns where Cowboy overheats and Tramontane leaves rate on the table. No raw damage. |
| Stabber (damage_02_mk1) | generalist | dmg 1.35–1.45, cooling 0.684–0.736 | dmg ×1.10, rel ×1.10 *(cool child pinned 1.0)* | 29 (11g/18t) | 38% | **Damage+reload.** Damage backbone with a fire-rate lean; contests the clip weapons against Piercer (they see-saw — winner-take-most on clips). Can't out-damage Piercer nor out-rate Cowboy — a damage-backed safe pick. |
| Gregale (cooling_02_mk1) | generalist | cool 1.38–1.49, dmg 0.7–0.75 | cool ×1.2, dmg ×1.08 | 2 (2g) | 4% | **Damage+cooling.** Damage backbone with a cooling lean for warm main guns; can't out-cool Tramontane nor out-damage Piercer, so it sits in the tie band as a safe pick for heat guns. |
| Slasher (damage_03_mk1) | generalist | dmg 1.338–1.503, cooling 0.681–0.74, **reload 0.682–2** | dmg ×1.115, cool ×1.07, rel ×1.045 | 7 (5g heat/2g heatless) | 18% | **Damage+cooling+reload — the pure all-rounder.** Lowest peak of any Basic mod, but the widest tie coverage (26 ties): a bit of everything, near-Piercer damage keeping it alive everywhere. Vanilla Slasher was the ×2-reroll lottery that dominated 210/223 weapons. |
| Jumper (chargetime_01_mk1) | specialist | charge 0.8–0.95 | charge ×0.75, dmg ×1.08 *(added rider)* | 2 (2g) | 1% | **Chargetime** (its own axis, outside the three-stat matrix). The charge family (Ray Ion Projector, Erlking, ...): charge time is a big slice of the volley interval there and nothing else can buy it. Utility-grade +8% anywhere else. |

## Basic utility bucket

Orthogonal primaries — no weapon has them as its *strongest* DPS pick,
by design (best% ~0 for all of them). Each carries a flat **+8% damage
rider** (added forced block) so the utility effect is the reason you take
the mod — it costs only ~6% DPS vs the Piercer baseline (+15%), not all
of it. Primaries pinned at (or retuned from) their vanilla best roll.

| Mod | Vanilla | New (fixed) | Niche |
|---|---|---|---|
| Dispatcher (speed_01_mk1) | speed 1.05–1.1 | speed ×1.25, lifetime ×0.84, dmg ×1.08 | **Velocity.** Projectiles arrive 25% faster (easier leads, better vs fast/evasive targets) at nearly unchanged range (1.25 × 0.84 = +5%). |
| Endurance (lifetime_01_mk1) | lifetime 1.05–1.2 | lifetime ×1.1, speed ×1.1, dmg ×1.08 | **Reach.** +21% projectile range (1.1 × 1.1) with the flight character unchanged — standoff work. |
| Lens (beamlength_01_mk1) | beam 1.05–1.1 | beam ×1.21, dmg ×1.08 | **Beam reach.** The beam-weapon counterpart of Endurance: +21% beam length. |
| Gimbal (rotationspeed_01_mk1) | rot 1.05–1.2 | rot ×1.2, dmg ×1.08 | **Turret tracking.** Faster slew for turrets chasing small, fast targets. |
| Gum (sticktime_01_mk1) | stick 1.05–1.2 | stick ×1.2, dmg ×1.08 | **Sticky weapons.** Longer stick time for the leech/disruptor projectile family. |
| Intruder (surfaceelement_01_mk1) | surf 1.2–1.35 | surf ×1.35, dmg ×1.08 | **Destroying surface elements** — turrets, shield generators, engines on stations and capital ships. |
| Digger (mining_01_mk1) | mining 5.25–6 | mining ×6 (no rider) | **Mining yield.** Deliberately no damage rider: a combat bonus on a mining mod re-opens the combat-cheat door. Mining weapons are excluded from all combat-mod evaluations. |

## Enhanced / Exceptional (interim)

Not yet given the testbed treatment. Current placeholder state, kept
consistent with the Basic tier (no RNG, no crossings, tier order intact):

- Damage mods pinned to tier: Assassin/Exterminator/Butcher/Slayer
  ×1.3333, Executioner ×1.36 (+cooling ×0.92 malus), Slayer keeps its
  time-flavored reload ×0.9; Obliterator/Annihilator ×1.5.
- The five Enhanced cooling mods are floored at ×1.9 (well above Basic
  Tramontane's ×1.4) to preserve tier order until properly staggered.
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
  selection) worth ≥25% cycle DPS on any weapon: pass, max +14.4%
  (Annihilator on ATF XL Main Battery). The cap was raised from 16% to
  25% because a combo mod's secondaries are part of its identity, not a
  free rider — the ceiling sits near the strongest single-stat headline.
  Vanilla max: +169.6%.
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
- Added bonus children show up in the weapon-mod UI (verified 2026-07 on
  an added reload child + `bonus/@max` bump — the reworked table now ships
  that exact shape on Stabber). Still to confirm: an install applies BOTH
  bonuses (forced semantics with the bumped `bonus/@max`) — one check
  covers all the added blocks.
