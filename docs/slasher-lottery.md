# The Slasher lottery — why vanilla weapon mods had no real choices

## What it was

In vanilla X4 v9.0, one Basic-tier weapon mod — **Slasher**
(`mod_weapon_damage_03_mk1`) — is the best full-cycle DPS choice on **210 of
223** weapons and turrets at optimal rolls. It rolls:

- damage **×1.338 – 1.503**
- a forced cooling "malus" **×0.681 – 0.74**
- a forced reload "malus" **×0.682 – 2.0**

Because rerolling a mod is cheap, the realized value of every range is its
**best end**. So Slasher's "reload malus" is, at its max roll, a **×2
fire-rate buff**, and its cooling malus lands at ×0.74. The result is a
single Basic mod that stacks ×1.5 damage with ×2 fire rate — better than
anything the Enhanced or Exceptional tiers can offer. Every other mod is a
strictly worse pick, and the whole weapon-mod system collapses into "grind
Slasher rerolls until you hit the top of each range."

## Why it was bad design

Four separate defects combine to produce the lottery:

1. **Roll ranges cross 1.0.** A "malus" whose range spans 0.68–2.0 is not a
   malus — at the max roll it is a large *buff*. The downside is illusory.
2. **The reroll makes ranges free.** Since you can reroll cheaply, you always
   realize the best end. A wide range is pure upside, not a risk.
3. **Penalties are charged in currencies many weapons don't spend.** The
   cooling malus costs nothing on the ~57 heatless weapons (pure clip guns,
   most L/XL turrets) and little wherever firing time dominates the cycle.
   The "cost" of the buff is waived for most of the roster.
4. **Everything trades in one scalar (DPS), and tier is meaningless.**
   Slasher's ×1.503 is the largest damage multiplier in the game — larger
   than every *Exceptional* damage primary (max ×1.348). A common Basic mod
   beats the rarest tier, so research and rarity buy nothing.

The net effect is an **illusion of choice**: a menu of mods that all resolve
to "use Slasher," no meaningful tiers, and an RNG reroll grind standing in for
a decision.

## How we overcame it

The rebalance attacks each defect directly. (Design rationale:
[`weapon-mod-rebalance-design.md`](weapon-mod-rebalance-design.md); shipped
values: [`weapon-mod-rebalance-v1.md`](weapon-mod-rebalance-v1.md);
before/after: [`weapon-mod-rebalance-power-analysis.md`](weapon-mod-rebalance-power-analysis.md).)

- **Pin every roll (`min = max`).** No RNG, no reroll lottery — the value you
  see is the value you get. Fixes defects 1 and 2 outright.
- **No range crosses 1.0.** A buff stays a buff and a malus stays a malus;
  nothing can be rerolled from one into the other.
- **Pin reloads knowing they're rate-semantic.** Weapons store fire cadence
  as either `<reload rate>` (shots/sec — 86 weapons) or `<reload time>`
  (seconds/shot — 94 weapons), but a reload mod scales the effective fire
  *rate* either way: the engine multiplies a stored `rate` and *divides* a
  stored `time` (validated in-game). So a reload value means the same thing
  across the whole roster — its best roll is always the max — letting us pin
  it as one clean, uniform buff or malus with no ambiguity.
- **Give each mod a distinct effect set (the two-class model).** The Basic
  tier is the seven non-empty combinations of {damage, cooling, reload}, no
  two mods sharing an effect set: a **baseline** (damage, useful everywhere),
  **specialists** that peak in one physical domain, and **generalists** that
  live in the tie band. Niches are carved by weapon *physics* — heat level,
  clip vs. continuous fire, chargetime — since per-weapon compatibility rules
  don't exist in the game data. This replaces "one scalar" with real
  trade-offs.
- **Make tier a genuine power ladder.** Basic / Enhanced / Exceptional map to
  the in-game research ladder (`research_mod_weapon_mk1/2/3`); each tier is
  strictly stronger within a variant, so rarity and research finally buy
  power. Fixes defect 4.
- **Enforce it with a harness.** `tools/weapon-mod-rebalance/evaluate.py`
  applies the diff and scores all weapons against acceptance targets — no mod
  dominates its tier (no new "Slasher"), every DPS mod is best somewhere,
  tiers never invert, and no range crosses 1.0.

The measured result: peak achievable mod power drops (median best-mod cycle
DPS from **+85%** vanilla to **+49%**, and the flat **+201%** burst lottery to
an honest **+51%**), while *which* mod is best now genuinely depends on the
weapon — a choice instead of a reroll.
