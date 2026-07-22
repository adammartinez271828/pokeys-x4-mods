# Weapon-mod rebalance: vanilla analysis & design direction

Everything here was produced with the tooling in `~/devel/x4-analyzer`
(v9.0 game files + all official DLC; simulation rules validated in-game).
Rerun anytime: `uv run x4-analyzer gamedata-dashboard` in that repo.

> The vanilla problem numbers below (Slasher on 210/223 weapons, the "13
> exceptions") were measured before the 2026-07 weapon-sim fix (discrete
> heat + sustained clip rate). They still describe the vanilla disease
> faithfully; exact counts would shift a little if re-measured. How the fix
> affects the *shipped* table: `docs/weapon-mod-rebalance-sim-update-2026-07.md`.

## The problem: illusion of choice

**Slasher** (`mod_weapon_damage_03_mk1`, Basic quality: damage ×1.338–1.503
with forced bonuses cooling ×0.681–0.74 and reload ×0.682–2) has the best
full-cycle DPS on **210 of 223** weapons/turrets at optimal rolls.

Three separate defects combine to cause this:

1. **Malus ranges cross 1.0.** Slasher's forced "reload malus" ×0.682–2 is,
   at optimal roll, a ×2 fire-rate BUFF. Rerolling is cheap, so realized
   value = range max.
2. **Maluses are charged in currencies many weapons don't spend.** The
   cooling penalty is free on the 143 heatless weapons (28 clip/heatless
   main guns plus all 115 turrets — every turret in the game, every size,
   is heatless; verified against v9.0 game files) and cheap wherever
   firing time dominates.
3. **All mods trade in one scalar (DPS)**, and Slasher's ×1.503 is the
   game's largest damage multiplier — larger than every Exceptional damage
   primary (max ×1.348). Tier means nothing.

### Where Slasher loses (the 13 exceptions)

All cooldown-dominated weapons, where cooling matters more than fire rate —
winners are Obliterator (forced cooling BUFF) and Slayer (mild malus):
BOR M Ion Pulse Railgun Mk1 (+26% for Obliterator), ATF XL Main Battery
(+17%), M Heavy Distortion Pulsor Mk1 (+13%), TEL S/M Muon Disintegrator
Mk1/Mk2 (+8–10%), SPL S Neutron Gatling Mk2, TER S/M Proton Barrage Mk1/Mk2,
TER M Electromagnetic Cannon Mk1 (≤3%).

Example (BOR M Ion Pulse Railgun: 2000 heat/shot at 2.7/s ⇒ 1.9 s firing,
12.6 s cooling): Slasher's ×2 fire rate compresses the tiny firing window
while its cooling malus stretches the 87% of the cycle that is cooldown.

## Design direction (as shipped in v1)

The early plan below (tier-pinned damage primaries + archetype flavor
sets) was the starting sketch. Building it out revealed that with only
three DPS levers — damage, cooling, reload — the archetype space is far
smaller than it looks: most "flavors" are blends that overlap what they're
built from. The shipped Basic tier (`docs/weapon-mod-rebalance-v1.md`)
therefore reorganized around a **two-class structural model** instead:

- **Basic tier = the seven non-empty COMBINATIONS** of {damage, cooling,
  reload}, one mod each, no two sharing an effect set (+ a chargetime
  specialist and the utility mods). Those seven resolve into two classes —
  a property of the physics, not a tuning choice:
  - **Baseline** — Piercer (damage). Damage is full value on every weapon,
    so it is the universal default and the benchmark, not a niche.
  - **Specialists** — Cowboy (reload), Tramontane (cooling), Mistral
    (cooling+reload). Each PEAKS in one physical domain. Only the
    cooling+reload pair earns a niche as a *pair*, because those two
    effects SYNERGISE (cooling pays the heat bill the fire rate runs up);
    the other combos blend SUBSTITUTES and can't beat a single stat.
  - **Generalists** — Stabber (damage+reload), Gregale (damage+cooling),
    Slasher (triple). Damage-backed safe picks that live in the tie band:
    high best-or-tied coverage, few strict wins. That IS their role.
- **The Basic values are a deliberate equilibrium.** Lowering a generalist
  feeds Piercer (it eats the vacated weapons); raising one mints a rogue
  specialist that kills a real one. Differentiation budget is therefore
  spent at Enhanced/Exceptional, widening the SPECIALIST peaks so identity
  sharpens with rarity — not on splitting the Basic tie band further.
- **No roll ranges crossing 1.0** (every range pinned min = max — no RNG),
  and **no per-weapon gating** (impossible in data — see below); niches
  are carved by weapon physics (heat level — including the Paranid Mass
  Drivers, which the corrected 2026-07 sim treats as overheating charge
  weapons, not heatless; clip vs. continuous fire; chargetime), not by
  compatibility rules.

Original sketch, retained for context: pin the damage primary to tier
(Basic/Enhanced/Exceptional ≈ ×1.17 / ×1.33 / ×1.5) with tight jitter;
differentiate within a tier by DPS-orthogonal or DPS-bounded secondaries;
archetype flavor sets (sniper / brawler / sustain / converter); soft
restriction via maluses charged in the currency an unintended archetype
depends on. The tier-pinned damage ladder and the "no crossings / bounded
secondaries" rules survived into v1; the archetype-flavor and jitter ideas
were dropped for the combination model.

### Balance acceptance targets

Enforced by the harness `tools/weapon-mod-rebalance/evaluate.py` (applies
the diff itself, then scores all 223 weapons via
`x4analyzer.gamedata.weaponsim`; exit 0 = all pass):

- **T1** — no mod is best-or-tied *within its own quality tier* on more
  than 85% of its eligible weapons (intra-tier monopoly). Cross-tier
  dominance by higher tiers is the intended research ladder and is NOT
  flagged; T2 ensures no mod is pointless. (Was a global >30% strict-win
  cap — incompatible with a power ladder, where the top tier should be the
  best you can craft.)
- **T2** — every DPS-primary mod is best-or-tied within its own quality
  tier on ≥1 weapon (repurposed/utility mods with a neutral 1.0 primary
  are exempt — their draw is the utility).
- **T3** — *removed.* A mod's secondaries are part of its stated identity
  (Mistral = cooling+reload; the Exceptional capstones are rich forced
  sets), so there is no secondary-bundle cap. The worst-case bundle worth
  is still reported for information.
- **T4** — no lower-quality mod beats a higher-quality mod of the same
  variant anywhere (tier order can't invert). A primary pinned to 1.0 is a
  repurposed container and dropped from the variant key.
- **T5** — no roll range crosses 1.0.

## Hard constraints discovered

- **No per-weapon mod compatibility exists in game data.**
  `equipmentmods.xml` entries carry only ware/quality/min/max/bonus; the
  install UI (`ui/addons/ego_detailmonitor/menu_ship_configuration.lua`)
  buckets by engine-side `modclass` (weapon/engine/ship/shield/paint) via
  `C.GetAvailableEquipmentMods`. Even Egosoft's Timelines scenario mods are
  gated by AVAILABILITY (uncraftable wares), not compatibility. A hard gate
  would need a Lua UI patch (fragile); soft-gating via maluses is the
  data-native mechanism.
- **Reload is rate-semantic on every weapon** (validated in-game 2026-07,
  correcting an earlier assumption). Weapons store cadence as either
  `<reload rate>` (shots/sec, 86 weapons) or `<reload time>` (seconds/shot,
  94 weapons), but a reload mod scales the effective fire *rate* either way —
  the engine multiplies a stored `rate` and *divides* a stored `time`. So a
  reload multiplier never flips meaning between weapons: its optimal roll is
  always the range MAX. (Damage/coolrate behave as expected; chargetime
  wants the min.)
- Vanilla weapon-mod table: `docs/reference/equipmentmods-vanilla-v9.xml`
  (+ Timelines additions in `equipmentmods-timelines-diff.xml`). Mod ware
  display names (Slasher, Piercer, ...) come from wares.xml `shortname`
  text refs.
- The savegame question is RESOLVED (in-game, 2026-07): a rebalance DOES
  affect existing installs — a vanilla max-roll Cowboy at +100% fire rate
  read +20% (the new range max) after loading with the rebalance active.
  Releases that change ranges therefore retune every ship retroactively;
  verified at the range max, mid-range mapping still unknown.
