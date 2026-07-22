# Weapon-mod rebalance v1

The table shipped in `weapon-mod-rebalance/libraries/equipmentmods.xml`
(192 ops: attribute replaces, added bonus blocks, and pool-pruning removes,
weapon section only). Design rationale: `docs/weapon-mod-rebalance-design.md`.
Validation:
`uv run --project ~/devel/x4-analyzer python tools/weapon-mod-rebalance/evaluate.py`
(exit 0 = all acceptance targets pass; the harness applies the diff
itself, so a sel typo is a hard error, not a silent no-op). Interactive
prototyping: the slider tool `tools/weapon-mod-rebalance/tuner.html`
(rebuild with `dump_data.py`) recomputes the within-tier win/tie split
live as you drag mod values.

**All three tiers are now designed** (Basic, Enhanced, Exceptional) on one
model: a per-tier power ladder that mirrors the in-game research ladder,
with each mod inside a tier a distinct effect-set identity.

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
  heatless majority, decisive on cooldown-dominated guns — including the
  Paranid Mass Drivers, which the corrected 2026-07 sim models as
  overheating charge weapons rather than heatless), *clip vs. continuous*
  fire (clips only pay partial value on fire rate — the clip reload is
  fixed, and the corrected sim makes that tax steeper still), and the
  *chargetime* lever nobody but Jumper touches.

- **Bounded everything**: no roll range crosses 1.0, and tier order can
  never invert within a variant. Secondary bundles are deliberately
  uncapped (a combo mod's secondaries *are* its identity — the old ≥25%
  T3 cap was removed); the biggest measured is a utility capstone's DPS
  side (max +48.0%, Invader on the TEL M Muon Disintegrator), not a DPS
  mod's.

## Basic DPS bucket

Values below are the shipped equilibrium. **Strict wins** = weapons where
the mod beats every other Basic DPS mod by >0.5% (the within-tier split,
over the 211 obtainable non-KHA weapons; ties counted separately). `g`/`t`
= wins on main guns / turrets. **best%** = share of a mod's eligible
weapons where it is best-or-tied — the generalist signature is *high
best%, low strict wins*.

Counts here reflect the corrected 2026-07 weapon sim (discrete heat +
sustained clip rate); see `docs/weapon-mod-rebalance-sim-update-2026-07.md`
for what moved and why. The `tools/weapon-mod-rebalance/tuner.html` slider
tool still carries the *old* continuous-heat physics in its ported JS and
is pending a re-port — trust these numbers, not the tuner, until then.

| Mod | Class | Vanilla | New (fixed) | Strict | best% | Role |
|---|---|---|---|---|---|---|
| Piercer (damage_01_mk1) | **baseline** | dmg 1.05–1.2 | dmg ×1.15 | 53 (15g/38t) | 47% | **Universal default & benchmark.** Full value everywhere; contests the clip weapons and warm guns at once — the gravity well the generalists orbit. Picked up more clip turrets outright once the sim fix steepened reload's clip tax. |
| Cowboy (reload_01_mk1) | specialist | **reload 0.682–2** | rel ×1.225 | 22 (3g/19t) | 12% | **Reload.** Owns continuous heatless turrets cleanly; full value on clips, taxed on heat guns. Headline sits above a damage single's because reload is situational where damage is universal. |
| Tramontane (cooling_01_mk1) | specialist | cool 1.048–1.216 | cool ×1.4 | 8 (8g) | 8% | **Cooling.** Pure coolrate: worthless on the heatless majority and on turrets, decisive on the hottest heat-limited guns — and now a live contender on the **Paranid Mass Drivers** (a heat weapon under the corrected sim; cooling did nothing there before). On the Plasma Cannon it is now a tie-band pick, not a clean win. Narrow, high ceiling. |
| Mistral (cooling_03_mk1) | specialist | cool 1.356–1.525, dmg 0.677–0.757, **reload 0.682–2** | cool ×1.32, rel ×1.125 *(dmg child pinned 1.0)* | 19 (19g) | 15% | **Cooling+reload — the one synergistic pair.** Coolrate pays the heat bill the fire rate runs up, so rate converts to DPS: the pick for hot rapid-fire guns where Cowboy overheats and Tramontane leaves rate on the table. Its footprint doubled under the corrected sim (the beam guns and the small Muon/Bolt Repeater guns are now heat-limited). No raw damage. |
| Stabber (damage_02_mk1) | generalist | dmg 1.35–1.45, cooling 0.684–0.736 | dmg ×1.10, rel ×1.10 *(cool child pinned 1.0)* | 23 (10g/13t) | 26% | **Damage+reload.** Damage backbone with a fire-rate lean; contests the clip weapons against Piercer. Reload's steeper clip tax under the corrected sim tipped several clips (Ion Blaster, Plasma/Flak/Needler turrets) to Piercer, trimming its coverage. Can't out-damage Piercer nor out-rate Cowboy — a damage-backed safe pick. |
| Gregale (cooling_02_mk1) | generalist | cool 1.38–1.49, dmg 0.7–0.75 | cool ×1.2, dmg ×1.08 | 7 (7g) | 8% | **Damage+cooling.** Damage backbone with a cooling lean for warm main guns; can't out-cool Tramontane nor out-damage Piercer, so it sits in the tie band as a safe pick for heat guns. Gained ground under the corrected sim, where damage-backed cooling now edges pure cooling on several warm guns (Plasma Cannon, small Muon). |
| Slasher (damage_03_mk1) | generalist | dmg 1.338–1.503, cooling 0.681–0.74, **reload 0.682–2** | dmg ×1.115, cool ×1.07, rel ×1.045 | 8 (8g) | 11% | **Damage+cooling+reload — the pure all-rounder.** Lowest peak of any Basic mod, near-Piercer damage keeping it alive across the tie band. Under the corrected sim it cedes some heat guns to Gregale/Mistral and some clips to Piercer, so its best% eased from ~18% to 11%. Vanilla Slasher was the ×2-reroll lottery that dominated 210/223 weapons. |
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
| Digger (mining_01_mk1) | mining 5.25–6 | mining ×3.5 (no rider) | **Mining yield.** Lowered well below Excavator's ×6.74 so the Exceptional mining mod is a real upgrade. Deliberately no damage rider: a combat bonus on a mining mod re-opens the combat-cheat door. Mining weapons are excluded from all combat-mod evaluations. |

## Enhanced (q2) & Exceptional (q3)

The upper tiers echo the Basic combat identities one tier up on a **power
ladder that mirrors the in-game research ladder** — Basic / Advanced /
Exceptional Weapon Mods (`research_mod_weapon_mk1/2/3`) unlock each whole
tier, which is *why* Exceptional earns the top band. Targets: damage-
equivalent **~24–36% (Enhanced)**, **~36–48% (Exceptional)** on-niche, with
outsize responders (ATF XL Main Battery under cooling; beam turrets under
reload) exceeding the band by design. Same rules as Basic (no RNG, no 1.0
crossings, distinct effect set per mod within a tier).

Vanilla ships more wares than there are distinct niches, so surplus wares
are **repurposed** — native primary pinned to ×1.0, the effect set rebuilt
from bonus children (the sim and the game both read the forced children;
the UI still lists the old primary stat, a harmless container label). Pool
bonuses are **pruned to forced** (`<remove>` of unwanted children) where an
identity needs a guaranteed secondary. Only 11 q2 wares surface in the
install menu (5 damage, 5 cooling, Infiltrator/surface); the **three
sticktime wares are left untouched** (they never appear — inventory / stat
applicability, not a research gate). `mod_weapon_damage_fleet_battle_1`
(Timelines, `noplayerblueprint`) and the engine/ship/shield sections are
untouched.

### Enhanced combat (band ~24–36% on niche)

| Mod (ware) | Identity (Basic echo) | New (fixed) | tier-dom% | Niche |
|---|---|---|---|---|
| Assassin (damage_01_mk2) | **baseline** {d} (Piercer) | dmg ×1.26 | 13% | Universal benchmark; DPS pool entries neutralised so it never rolls a random rate buff. |
| Exterminator (damage_02_mk2) | {d,r} (Stabber) | dmg ×1.24, rel ×1.15 | 71% | Damage + fire rate: the broad Enhanced default, wins the clip/rate majority. |
| Executioner (damage_04_mk2) | {d,c} (Gregale) | dmg ×1.26, cool ×1.2 | 20% | Damage + heat headroom for warm main guns (native forced cooling malus → buff). |
| Slayer (damage_05_mk2) | {d,c,r} triple (Slasher) | dmg ×1.20, cool ×1.18, rel ×1.10 | 6% | The all-rounder: a bit of everything, broad tie coverage, lowest peak. |
| Butcher (damage_03_mk2) | {d,ch} (Jumper) | dmg ×1.26, charge ×0.70 | 4% | Charge-weapon specialist (Ray Ion Projector, Erlking, …). |
| Labrador (cooling_01_mk2) | {c} (Tramontane) | cool ×1.9 | 5% | Pure coolrate: the hottest heat-limited guns (+86% on ATF XL). |
| Benguela (cooling_05_mk2) | {c,r} (Mistral) | cool ×1.7, rel ×1.22 | 4% | Cooling+reload synergy: hot rapid-fire guns (native forced damage pinned 1.0). |

### Enhanced utility (+16% damage rider; repurposed cooling wares)

| Mod (ware) | Identity (Basic echo) | New (fixed) | Niche |
|---|---|---|---|
| Okhotsk (cooling_04_mk2) | speed (Dispatcher) | speed ×1.5, dmg ×1.16 *(cool pinned 1.0)* | Projectile velocity. |
| Humboldt (cooling_02_mk2) | lifetime (Endurance) | lifetime ×1.5, dmg ×1.16 *(cool pinned 1.0)* | Reach (+50% range). |
| Kuril (cooling_03_mk2) | rotationspeed (Gimbal) | rot ×1.6, dmg ×1.16 *(cool pinned 1.0)* | Turret tracking (a pure-reload mod has no niche once Exterminator exists). |
| Infiltrator (surfaceelement_01_mk2) | surface (Intruder) | surf ×1.4, dmg ×1.16, +rot/life | Anti-subsystem. |

### Exceptional (band ~36–48%; rich, distinct capstones)

| Mod (ware) | Identity | New (fixed) | tier-dom% | Niche |
|---|---|---|---|---|
| Obliterator (damage_01_mk3) | **damage / brawler** {d,c,stick,rot} | dmg ×1.44, cool ×1.2, stick ×1.4, rot ×1.6 | 34% | Top damage + heat headroom + sticky/tracking; wins heat guns. Cooling trimmed 1.25→1.2 to keep heat-gun gains nearer the band ceiling. |
| Annihilator (damage_02_mk3) | **damage + rate** {d,r,rot} | dmg ×1.44, rel ×1.05, rot ×1.6 | 69% | Aggressive DPS; the broad Exceptional default (rate weapons). No cooling → distinct from Obliterator. |
| Invader (surfaceelement_01_mk3) | surface capstone | surf ×1.5, dmg ×1.24, cool ×1.2, life ×1.4, rot ×1.6 | — | Anti-subsystem heavy. |
| Expediter (speed_01_mk3) | sniper capstone | speed ×1.5, dmg ×1.24, life ×1.5, rot ×1.6 | — | Long-range velocity + tracking. |
| Excavator (mining_01_mk3) | mining capstone | mining ×6.74, rot ×2.0, rel ×1.3, beam ×1.2 *(no damage rider)* | — | Mining yield; non-damage riders only (faster cycles, aims the turret, +20% beam reach) — never a combat cheat. |

## Harness scorecard (all targets pass)

Metric: full-cycle DPS (steady-state where no heat/clip cycle exists),
vs-shield and vs-hull channels, 217 DPS-capable of 223 weapons/turrets;
mining weapons only count for mods that can roll a mining bonus.

- **T1 within-tier dominance** — no mod is best-or-tied *within its own
  quality tier* on >85% of its eligible weapons: pass (worst is
  Exterminator/Annihilator ~70%). This replaces the old global >30% cap,
  which is mathematically incompatible with a research-gated power ladder:
  the top-tier mods *should* be the best you can craft, so cross-tier
  dominance is intended; the guard is only against an intra-tier monopoly
  (the vanilla-Slasher disease — 97% within its tier). T2 separately
  ensures no mod is pointless.
- **T2 usefulness** — every DPS-primary mod is best-or-tied within its
  own quality tier on ≥1 weapon: pass. Repurposed wares (primary pinned
  1.0) and orthogonal-primary utility mods are exempt (their draw is the
  utility, not DPS).
- **T3 bundles** — **removed.** Under the combination design a mod's
  secondaries *are* its identity (Mistral = cooling+reload; the Exceptional
  capstones are deliberately rich forced sets), so there is no cap. The
  scorecard still prints the worst-case bundle worth for information (max
  +48.0%, Invader on TEL M Muon Disintegrator under the corrected sim).
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
