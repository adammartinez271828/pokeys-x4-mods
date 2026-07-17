# Hull-mod rebalance: design (DRAFT)

Fourth equipment rebalance (after weapons, engines, shields), applied to the
`<ship>` section of `libraries/equipmentmods.xml`. Built with
`x4analyzer.gamedata.shipmods`. **Not yet in-game verified.**

## The problem

The `<ship>` section is the most heterogeneous: ~11 stat families (durability,
mobility, sensors, stealth, loadout, hazard resist, cargo) across 18 mods — 10
crowded into Basic, only 4 each at Enhanced/Exceptional. Everything rolls RNG.

## The archetype model

**Four archetypes span all three tiers**, plus three Basic-only utility picks
that fold into Tank above Basic. Wares are repurposed where a ware's stat
doesn't match its archetype, using its existing bonus pool.

| Role | Feel | Levers | Basic / Enhanced / Exceptional |
|---|---|---|---|
| **Racer** | accel + top speed | mass + drag | mass_mk1 / mass_mk2 / mass_mk3 |
| **Tank** | durability + loaded logistics | maxhull + radar + ALL capacity | maxhull_mk1 / drag_mk2\* / hidecargo\* |
| **Ghost** | stealth (+ hide cargo) | radarcloak | radarcloak_mk1/mk2/mk3 |
| **Explorer** | hazard resistance | regiondamage | regiondamage_mk1/mk2/mk3 |
| **Recon** | sensors (folds → Tank) | radarrange | radarrange_mk1 |
| **Loadout** | countermeasures (folds → Tank) | countermeasurecap | countermeasure_mk1 |
| **Smuggler** | hide cargo | hidecargo + deployable | deployable_mk1 |

\* The Enhanced `drag` ware and Exceptional `hidecargo` ware are repurposed as
Tank — their vanilla pools already carry the maxhull/radar/capacity riders.

- **maxhull is the always-good stat** (hull analog of damage / forward speed /
  shield capacity): the **tier sweetener** — it rides on *every*
  Enhanced (+10%) and Exceptional (+20%) mod. Tank is built on it.
- **Capacity is a FLAT additive count** (+N consumables; base ~8 on S ships to
  ~20 on L), so the numbers are generous. **Tank is the loaded-logistics mod**:
  it folds in Recon + Loadout and carries *all four* capacity types, scaling
  per tier (Enh +6 each, Exc +8 each).
- **Cargo hiding** lives on the Smuggler (Basic), Shroud (Exc Ghost) and Mirage
  (Exc Tank).
- **Honest / flavour touches.** Ghost keeps a mild *stealth-costs-radar* trade
  at Basic (Exceptional flips to a radar buff). Explorer's vanilla
  *hazard-resist-costs-hull* malus is dropped; at Exceptional (**Tenacity**) it
  is *total* hazard immunity (regiondamage → 0).
- **Degenerate (Basic only, parked):** the redundant `drag` ware + the
  missile/unit capacity mods (folded into Tank above Basic anyway).
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
