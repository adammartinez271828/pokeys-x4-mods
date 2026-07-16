# Weapon-mod rebalance — before/after power analysis

How the rebalanced mods compare to vanilla, measured as **best available mod per weapon** ("whatever was best before" vs "whatever is best now", each at its optimal roll). Two metrics:

- **Sustained (cycle) DPS** — full firing cycle including heat/clip throttling.
- **Burst DPS** — peak `damage × fire-rate` before any heat/clip throttle (rewards damage + reload, ignores cooling).

Scope: 186 obtainable weapons/turrets (6 KHA excluded); mining weapons count only mining mods. Gain % is vs the bare weapon; the ratio is channel-independent for these mods, so the shield channel is used. Vanilla mods are taken at their optimal (best) roll — for most weapons that was Slasher's ×2 reload-reroll lottery.

## Sustained (cycle) DPS

| | Best vanilla mod | Best rebalanced mod | Change (now vs before) |
|---|---|---|---|
| median gain over bare | +85% | +49% | -20% |
| mean gain over bare | +97% | +50% | -20% |
| max gain over bare | +201% | +86% | |

Of 186 weapons, the best mod is **weaker now on 159 (85%)** and stronger on 23 (12%). The rebalance mostly *lowers* peak mod power — it removes the Slasher reroll lottery — while making the choice meaningful.

### By weapon class (median best-mod gain over bare)

| class | n | best vanilla | best now | now vs before |
|---|---|---|---|---|
| heat | 78 | +68% | +53% | -8% |
| clip | 84 | +96% | +47% | -25% |
| heatless | 24 | +201% | +51% | -50% |

### Best rebalanced mod by tier (median gain over bare)

| tier | median | max |
|---|---|---|
| Basic | +16% | +38% |
| Enhanced | +34% | +86% |
| Exceptional | +49% | +72% |

### Biggest sustained-DPS reductions (where vanilla Slasher was most broken)

| weapon | best vanilla | best now (mod) | now vs before |
|---|---|---|---|
| Astrid M Turret | +201% (Slasher) | +51% (Annihilator) | -50% |
| XEN M Positron Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | -50% |
| TEL M Distortion Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | -50% |
| ARG L Beam Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | -50% |
| ARG M Beam Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | -50% |
| ARG M Beam Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | -50% |
| PAR L Mass Driver Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | -50% |
| PAR M Mass Driver Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | -50% |
| PAR M Mass Driver Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | -50% |
| TEL L Beam Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | -50% |

### Weapons where the best mod is now STRONGER than vanilla

| weapon | best vanilla | best now (mod) | now vs before |
|---|---|---|---|
| TER M Meson Stream Mk2 | +47% (Obliterator) | +63% (Obliterator) | +11% |
| TER M Meson Stream Mk1 | +47% (Obliterator) | +63% (Obliterator) | +11% |
| ATF XL Main Battery | +71% (Obliterator) | +86% (Labrador) | +9% |
| TER S Meson Stream Mk1 | +35% (Annihilator) | +44% (Obliterator) | +7% |
| TER S Meson Stream Mk2 | +35% (Annihilator) | +44% (Obliterator) | +7% |
| PAR Odysseus Main Battery | +50% (Obliterator) | +58% (Obliterator) | +6% |
| S Plasma Cannon Mk2 | +51% (Obliterator) | +59% (Obliterator) | +5% |
| M Plasma Cannon Mk1 | +51% (Obliterator) | +59% (Obliterator) | +5% |
| M Plasma Cannon Mk2 | +51% (Obliterator) | +59% (Obliterator) | +5% |
| S Plasma Cannon Mk1 | +52% (Obliterator) | +60% (Obliterator) | +5% |

## Burst DPS

Peak `damage × fire-rate`, no throttle. Cooling does nothing here, so the winners are damage + reload mods.

| | best vanilla | best rebalanced | change |
|---|---|---|---|
| median gain over bare | +201% | +51% | -50% |
| mean gain over bare | +198% | +51% | -49% |
| max gain over bare | +201% | +51% | |

### Which mod wins burst now (count of weapons where it's the top burst pick)

| mod | tier | weapons |
|---|---|---|
| Annihilator | Exceptional | 185 |
| Obliterator | Exceptional | 1 |

### Burst by weapon class (median best-mod gain over bare)

| class | best vanilla | best now | now vs before |
|---|---|---|---|
| heat | +201% | +51% | -50% |
| clip | +201% | +51% | -50% |
| heatless | +201% | +51% | -50% |

## Worked examples

Actual per-weapon numbers (DPS is the shield channel; the multiplier line shows the mod's *forced* rolls at optimal value). These trace the aggregates above to concrete guns.

### The Slasher lottery, dismantled

On continuous-fire turrets Slasher's cooling malus was free, so its reload-reroll ×2 and ×1.5 damage stacked into a flat **+201% burst** with no downside — the single defect the rebalance targets.

**ARG L Beam Turret Mk1** — heatless L turret — the pure Slasher-lottery case (cooling malus costs nothing).

| metric | bare | best vanilla | best rebalanced |
|---|---|---|---|
| sustained DPS | 45 | 137 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 69 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |
| burst DPS | 45 | 137 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 69 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |

**PAR M Mass Driver Turret Mk1** — clip turret — Slasher's cooling malus is free, reload reroll dominates.

| metric | bare | best vanilla | best rebalanced |
|---|---|---|---|
| sustained DPS | 69 | 207 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 104 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |
| burst DPS | 69 | 207 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 104 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |

### The intended winners: heat-limited guns

Weapons whose DPS is gated by heat get *more* from the rebalanced cooling/damage capstones than they ever did from Slasher — whose cooling malus actively hurt them. These are the weapons that get **stronger**.

**S Plasma Cannon Mk1** — heat-limited S gun — Obliterator's forced cooling buff beats Slasher's malus.

| metric | bare | best vanilla | best rebalanced |
|---|---|---|---|
| sustained DPS | 151 | 230 — **Obliterator** +52%<br><sub>dmg ×1.30, cool ×1.32, stick ×1.30, rot ×1.30</sub> | 241 — **Obliterator** (Exceptional) +60%<br><sub>dmg ×1.44, cool ×1.20, stick ×1.40, rot ×1.60</sub> |
| burst DPS | 277 | 832 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 419 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |

**ATF XL Main Battery** — the extreme heat responder — cooling is worth more here than anywhere.

| metric | bare | best vanilla | best rebalanced |
|---|---|---|---|
| sustained DPS | 11,840 | 20,197 — **Obliterator** +71%<br><sub>dmg ×1.30, cool ×1.32, stick ×1.30, rot ×1.30</sub> | 22,069 — **Labrador** (Enhanced) +86%<br><sub>cool ×1.90</sub> |
| burst DPS | 26,575 | 79,885 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 40,182 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |

**TER M Meson Stream Mk1** — beam with a heavy heat bill — Obliterator overtakes vanilla by +11%.

| metric | bare | best vanilla | best rebalanced |
|---|---|---|---|
| sustained DPS | 188 | 276 — **Obliterator** +47%<br><sub>dmg ×1.30, cool ×1.32, stick ×1.30, rot ×1.30</sub> | 305 — **Obliterator** (Exceptional) +63%<br><sub>dmg ×1.44, cool ×1.20, stick ×1.40, rot ×1.60</sub> |
| burst DPS | 212 | 637 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 321 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |
