# Hull-mod rebalance: design (DRAFT)

Fourth equipment rebalance (after weapons, engines, shields), applied to the
`<ship>` section of `libraries/equipmentmods.xml`. Built with
`x4analyzer.gamedata.shipmods`. **Not yet in-game verified.**

## The problem

The `<ship>` section is the most heterogeneous: ~11 stat families (durability,
mobility, sensors, stealth, loadout, hazard resist, cargo) across 18 mods — 10
crowded into Basic, only 4 each at Enhanced/Exceptional. Everything rolls RNG.

## The archetype model

**Four archetypes span all three tiers**, mapped to wares (repurposing where a
ware's stat doesn't match its archetype, using its existing bonus pool):

| Archetype | Feel | Levers | Basic / Enhanced / Exceptional |
|---|---|---|---|
| **Racer** | accel + top speed | mass + drag | mass_mk1 / mass_mk2 / mass_mk3 |
| **Tank** | durability + support | maxhull + radar + loadout | maxhull_mk1 / drag_mk2\* / hidecargo\* |
| **Ghost** | stealth | radarcloak | radarcloak_mk1/mk2/mk3 |
| **Explorer** | hazard resistance | regiondamage | regiondamage_mk1/mk2/mk3 |

\* The Enhanced `drag` ware and Exceptional `hidecargo` ware are repurposed as
Tank — their vanilla pools already carry the maxhull/radar/capacity riders.

- **maxhull is the always-good stat** (the hull analog of weapon damage /
  engine forward speed / shield capacity): more HP never hurts, so it is the
  **tier sweetener** — it scales up each tier and rides on *every*
  Enhanced/Exceptional mod (+10% Enh, +20% Exc). Tank is built on it.
- **Basic-only utility → folds into Tank.** Basic also offers **Recon**
  (radarrange) and **Loadout** (countermeasure capacity); above Basic these
  fold into Tank, which becomes a hull + sensors + loadout "support/command"
  mod.
- **Two honest touches.** Ghost keeps a mild *stealth-costs-radar* trade at
  Basic (Exceptional flips to a radar buff, as vanilla). Explorer's vanilla
  *hazard-resist-costs-hull* malus is dropped (it fought the always-good stat).
- **Degenerate (Basic only, parked at a token):** the redundant `drag` ware
  and the deployable/missile/unit capacity mods. (Countermeasure is the kept
  Loadout; the others are the niche the user chose to park.)
- **No RNG** (every range pinned).

## Acceptance targets (harness, all pass)

`tools/ship-mod-rebalance/evaluate.py` (exit 0 = pass). Effect vectors are
ship-independent; the parked mods are named explicitly (`DEGENERATE`) since the
stats sit on very different scales.

- **E1** no RNG · **E2** no multiplier range crosses 1.0 (radarcloak additive,
  exempt) · **E3** no non-degenerate mod Pareto-dominated by/identical to
  another in its tier · **E4** no same-variant tier inversion.

## Open questions for review

- Degenerate capacity mods are the *sole* provider of their niche (missile/
  unit capacity), so parking them means those builds lose their mod — is the
  token value right, or keep one or two meaningful?
- Tank's higher-tier carriers (drag ware, hidecargo ware) have names that don't
  evoke "tank" — cosmetic only (numbers-only mod), but worth noting.
