# Weapon-mod rebalance — before/after power analysis

How the rebalanced mods compare to vanilla, measured as **best available mod per weapon** ("whatever was best before" vs "whatever is best now", each at its optimal roll). Two metrics:

- **Sustained (cycle) DPS** — full firing cycle including heat/clip throttling.
- **Burst DPS** — peak `damage × fire-rate` before any heat/clip throttle (rewards damage + reload, ignores cooling).

Scope: 186 obtainable weapons/turrets (6 KHA excluded); mining weapons count only mining mods. Gain % is vs the bare weapon; the ratio is channel-independent for these mods, so the shield channel is used. Vanilla mods are taken at their optimal (best) roll — for most weapons that was Slasher's ×2 reload-reroll lottery.

Beam weapons are modelled as many sub-shots packed into a live window: `dmg_s` is the per-second intensity, the beam is live for `lifetime` of every `reload_time` cycle, so peak/burst = `dmg_s × reload` and sustained = peak × `lifetime/reload_time` × heat duty. Reload packs the sub-shots tighter (raising both burst and sustained); it does not change the on/off cycle. This matches the in-game encyclopedia (ARG M Beam Turret: 168 × 3/7 = 72 MW Weapon Output; S Beam Emitter burst 110→134 under reload ×1.225).

## Sustained (cycle) DPS

The last column compares the two *modded end-states*: the best-modded DPS now ÷ the best-modded DPS before. It is **not** the difference of the two gain-over-bare percentages. `×0.50` means the best mod you can now fit produces half the DPS the best vanilla mod did; `×1.10` means 10% more.

| | Best vanilla mod | Best rebalanced mod | Best-modded DPS, now ÷ before |
|---|---|---|---|
| median gain over bare | +85% | +49% | ×0.80 |
| mean gain over bare | +96% | +50% | ×0.80 |
| max gain over bare | +201% | +75% | |

Of 186 weapons, the best mod is **weaker now on 158 (85%)** and stronger on 24 (13%). The rebalance mostly *lowers* peak mod power — it removes the Slasher reroll lottery — while making the choice meaningful.

### By weapon class (median best-mod gain over bare)

| class | n | best vanilla | best now | now ÷ before |
|---|---|---|---|---|
| heat | 78 | +67% | +53% | ×0.92 |
| clip | 84 | +96% | +47% | ×0.75 |
| heatless | 24 | +201% | +51% | ×0.50 |

### Best rebalanced mod by tier (median gain over bare)

| tier | median | max |
|---|---|---|
| Basic | +16% | +35% |
| Enhanced | +34% | +75% |
| Exceptional | +49% | +69% |

### Biggest sustained-DPS reductions (where vanilla Slasher was most broken)

| weapon | best vanilla | best now (mod) | now ÷ before |
|---|---|---|---|
| ARG M Beam Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |
| ARG M Beam Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |
| TEL M Beam Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |
| TEL M Beam Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |
| XEN M Positron Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |
| TEL M Distortion Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |
| TER M Meson Stream Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |
| TER M Meson Stream Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |
| ARG L Beam Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |
| PAR L Mass Driver Turret Mk1 | +201% (Slasher) | +51% (Annihilator) | ×0.50 |

### Weapons where the best mod is now STRONGER than vanilla

| weapon | best vanilla | best now (mod) | now ÷ before |
|---|---|---|---|
| PAR Odysseus Main Battery | +50% (Obliterator) | +58% (Obliterator) | ×1.06 |
| S Plasma Cannon Mk2 | +51% (Obliterator) | +59% (Obliterator) | ×1.05 |
| M Plasma Cannon Mk1 | +51% (Obliterator) | +59% (Obliterator) | ×1.05 |
| M Plasma Cannon Mk2 | +51% (Obliterator) | +59% (Obliterator) | ×1.05 |
| S Plasma Cannon Mk1 | +52% (Obliterator) | +60% (Obliterator) | ×1.05 |
| TER M Meson Stream Mk1 | +53% (Obliterator) | +60% (Obliterator) | ×1.05 |
| TER M Meson Stream Mk2 | +53% (Obliterator) | +60% (Obliterator) | ×1.05 |
| TER S Meson Stream Mk1 | +53% (Obliterator) | +60% (Obliterator) | ×1.05 |
| TER S Meson Stream Mk2 | +53% (Obliterator) | +60% (Obliterator) | ×1.05 |
| M Heavy Scalar Aperture Emitter Mk1 | +50% (Slayer) | +57% (Obliterator) | ×1.05 |

Peak un-throttled output — `damage × fire-rate` for bullet/clip weapons, and `damage × reload` intensity for beams (reload packs their sub-shots tighter). Damage and reload both raise it on every weapon type; cooling never affects peak. So the burst winners are the damage + reload mods.

| | best vanilla | best rebalanced | best-modded burst, now ÷ before |
|---|---|---|---|
| median gain over bare | +201% | +51% | ×0.50 |
| mean gain over bare | +198% | +51% | ×0.51 |
| max gain over bare | +201% | +51% | |

### Which mod wins burst now (count of weapons where it's the top burst pick)

| mod | tier | weapons |
|---|---|---|
| Annihilator | Exceptional | 185 |
| Obliterator | Exceptional | 1 |

### Burst by weapon class (median best-mod gain over bare)

| class | best vanilla | best now | now ÷ before |
|---|---|---|---|
| heat | +201% | +51% | ×0.50 |
| clip | +201% | +51% | ×0.50 |
| heatless | +201% | +51% | ×0.50 |

## Worked examples

Actual per-weapon numbers (DPS is the shield channel; the multiplier line shows the mod's *forced* rolls at optimal value). These trace the aggregates above to concrete guns.

### The Slasher lottery, dismantled

On continuous-fire turrets Slasher's cooling malus was free, so its reload-reroll ×2 and ×1.5 damage stacked into a flat **+201% burst** with no downside — the single defect the rebalance targets.

**ARG L Beam Turret Mk1** — heatless L turret — the pure Slasher-lottery case (cooling malus costs nothing).

| metric | bare | best vanilla | best rebalanced |
|---|---|---|---|
| sustained DPS | 182 | 547 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 275 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |
| burst DPS | 500 | 1,503 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 756 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |

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
| sustained DPS | 10,774 | 17,985 — **Obliterator** +67%<br><sub>dmg ×1.30, cool ×1.32, stick ×1.30, rot ×1.30</sub> | 18,811 — **Labrador** (Enhanced) +75%<br><sub>cool ×1.90</sub> |
| burst DPS | 194,000 | 583,164 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 293,328 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |

**TER M Meson Stream Mk1** — beam with a heavy heat bill — Obliterator overtakes vanilla by +11%.

| metric | bare | best vanilla | best rebalanced |
|---|---|---|---|
| sustained DPS | 182 | 278 — **Obliterator** +53%<br><sub>dmg ×1.30, cool ×1.32, stick ×1.30, rot ×1.30</sub> | 292 — **Obliterator** (Exceptional) +60%<br><sub>dmg ×1.44, cool ×1.20, stick ×1.40, rot ×1.60</sub> |
| burst DPS | 1,060 | 3,186 — **Slasher** +201%<br><sub>dmg ×1.50, cool ×0.74, reload ×2.00</sub> | 1,603 — **Annihilator** (Exceptional) +51%<br><sub>dmg ×1.44, reload ×1.05, rot ×1.60</sub> |
