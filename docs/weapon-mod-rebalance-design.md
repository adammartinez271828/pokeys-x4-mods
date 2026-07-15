# Weapon-mod rebalance: vanilla analysis & design direction

Everything here was produced with the tooling in `~/devel/x4-analyzer`
(v9.0 game files + all official DLC; simulation rules validated in-game).
Rerun anytime: `uv run x4-analyzer gamedata-dashboard` in that repo.

## The problem: illusion of choice

**Slasher** (`mod_weapon_damage_03_mk1`, Basic quality: damage ×1.338–1.503
with forced bonuses cooling ×0.681–0.74 and reload ×0.682–2) has the best
full-cycle DPS on **210 of 223** weapons/turrets at optimal rolls.

Four separate defects combine to cause this:

1. **Malus ranges cross 1.0.** Slasher's forced "reload malus" ×0.682–2 is,
   at optimal roll, a ×2 fire-rate BUFF. Rerolling is cheap, so realized
   value = range max.
2. **Maluses are charged in currencies many weapons don't spend.** The
   cooling penalty is free on the ~57 heatless weapons (all pure clip
   weapons, most L/XL turrets) and cheap wherever firing time dominates.
3. **All mods trade in one scalar (DPS)**, and Slasher's ×1.503 is the
   game's largest damage multiplier — larger than every Exceptional damage
   primary (max ×1.348). Tier means nothing.
4. **Mods multiply stored fields, not effects.** The same reload ×0.682 is
   a malus on `<reload rate>` weapons and a buff on `<reload time>` ones.

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
  are carved by weapon physics (heat level, clip vs. continuous fire,
  chargetime), not by compatibility rules.

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

- **T1** — no single mod best-in-cycle-DPS on more than ~30% of its
  eligible weapons (within-tier advisory + cross-tier hard).
- **T2** — every DPS-primary mod is best-or-tied within its own quality
  tier on ≥1 weapon.
- **T3** — no secondary bundle worth ≥25% cycle DPS on any weapon (raised
  from 16%: a combo mod's secondaries are part of its identity).
- **T4** — no lower-quality mod beats a higher-quality mod of the same
  variant anywhere (tier order can't invert).
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
- **Mods multiply fields literally** — express intent per storage form
  (`reload rate` vs `reload time` weapons want opposite roll ends).
- Vanilla weapon-mod table: `docs/reference/equipmentmods-vanilla-v9.xml`
  (+ Timelines additions in `equipmentmods-timelines-diff.xml`). Mod ware
  display names (Slasher, Piercer, ...) come from wares.xml `shortname`
  text refs.
- The savegame question is RESOLVED (in-game, 2026-07): a rebalance DOES
  affect existing installs — a vanilla max-roll Cowboy at +100% fire rate
  read +20% (the new range max) after loading with the rebalance active.
  Releases that change ranges therefore retune every ship retroactively;
  verified at the range max, mid-range mapping still unknown.
