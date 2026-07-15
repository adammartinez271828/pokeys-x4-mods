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

## Agreed design direction

- **Pin the damage primary to quality tier** — e.g. Basic ×1.1667,
  Enhanced ×1.3333, Exceptional ×1.5. Tier = power, strictly monotone;
  restores meaning to the crafting economy. Optional tight jitter (±2–3%)
  keeps rerolling alive without crossing tiers.
- **Differentiate mods WITHIN a tier by secondaries** that are:
  - DPS-orthogonal: projectile speed, range/lifetime, rotation speed,
    heat-window shape (reenable threshold, overheat delay), shield/hull
    bias conversion, travel-drive multiplier; or
  - DPS-bounded: any secondary touching fire rate or cooling must be worth
    **less than one tier step (<~16% cycle DPS)** on every weapon — else it
    recreates dominance (Slasher pinned at ×1.1667 but keeping reload ×2
    would still hit ×2.33 effective on heatless weapons, beating a bare
    Exceptional's ×1.5).
- **No roll ranges crossing 1.0.** Correlate rolls (better primary ⇒ worse
  malus, one roll slides along the tradeoff curve) or fix the malus.
- **Archetype flavor sets** per tier, e.g.: sniper (+projectile speed/
  +range, −rotation), brawler (+rotation, −range), sustain (+heat window,
  −damage bias), converter (shield↔hull swap).
- **Soft restriction instead of hard gating** (hard per-weapon gating is
  impossible in data — see below): charge each variant's malus in the
  currency its unintended archetype depends on.

### Balance acceptance targets

Checked mechanically against all 223 weapons via
`x4analyzer.gamedata.weaponsim`:

- No single mod is best-in-cycle-DPS on more than ~30% of weapons.
- Every mod is the best pick on SOME weapon/use case.
- No secondary bundle worth more than one tier step of cycle DPS.
- Tier inversion impossible (no Basic beats an Exceptional of the same
  variant on any weapon).

An evaluation harness enforcing these against a candidate mod table does
not exist yet; it belongs in x4-analyzer (or a script here that imports it).

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
