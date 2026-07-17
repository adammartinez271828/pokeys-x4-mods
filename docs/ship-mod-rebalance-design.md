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

**Exactly four archetypes at every tier** (no Basic-only utility mods — radar,
capacity and cargo-hide all fold into Tank/Explorer). Carriers are chosen so
each ware's **name** fits the archetype; a mismatched primary stat is pinned
neutral and the bundle rides on the bonus.

| Role | Feel | Basic / Enhanced / Exceptional (ware — name) |
|---|---|---|
| **Racer** | accel + top speed | mass_mk1 (Honeycomb) / **drag_mk2 (Lubricator)** / mass_mk3 (Nanotube) |
| **Tank** | durability + loaded logistics (hull + radar + ALL capacity) | maxhull_mk1 (Buttress) / **regiondamage_mk2 (Mettle)** / **regiondamage_mk3 (Tenacity)** |
| **Ghost** | stealth | radarcloak_mk1/mk2/mk3 (Cloak/Veil/Shroud) |
| **Explorer** | hazard resist + hide cargo | regiondamage_mk1 (Grit) / **mass_mk2 (Composite)** / **hidecargo (Mirage)** |

Ladders: hull ×1.2/1.4/1.6; radar +33/67/100%; capacity +4/6/8 each type;
hazard resist 60/80/100%; cargo-hide 70/85/100%.

The other six Basic wares (drag, radarrange, and all four capacity mods) are
**degenerate** — parked at a token, since their roles fold into Tank/Explorer.

- **maxhull is the always-good stat** (hull analog of damage / forward speed /
  shield capacity): the **tier sweetener** — it rides on *every*
  Enhanced (+10%) and Exceptional (+20%) mod. Tank is built on it.
- **Capacity is a FLAT additive count** (+N consumables; base ~8 on S ships to
  ~20 on L), so the numbers are generous. **Barrage** (Basic Loadout) is the
  one-stop-shop, +4 to *all four* types; **Tank is the loaded-logistics mod**
  carrying all four scaling per tier (Enh +6, Exc +8). **Radar** is generous
  too: +33% / +67% / +100% (Recon → Tank; Shroud gets +33%).
- **Cargo hiding folds into the Explorer line:** Smuggler (Basic Rack, pure
  hide-cargo), Mettle (Enh Explorer), Tenacity (Exc Explorer). Ghost and Tank
  do not hide cargo.
- **Honest / flavour touches.** Ghost keeps a mild *stealth-costs-radar* trade
  at Basic (Exceptional flips to a radar buff). Explorer's vanilla
  *hazard-resist-costs-hull* malus is dropped, and hazard resist scales
  **60% / 80% / 100%** along the Explorer line (Grit / Composite / **Mirage** =
  total immunity). NB: `regiondamage` is a hazard-damage **reduction fraction**
  (higher = better, 1.0 = 100% reduction/immunity, 0 = neutral, negative =
  extra damage) — NOT a damage multiplier; the Tank mods pin it to 0 (neutral).
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
