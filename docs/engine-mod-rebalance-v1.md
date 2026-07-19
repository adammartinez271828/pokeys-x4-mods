# Engine-mod rebalance v1

The table shipped in `engine-mod-rebalance/libraries/equipmentmods.xml`
(120 ops, `<engine>` section only). Design rationale:
`docs/engine-mod-rebalance-design.md`. Validation:
`uv run --project ~/devel/x4-analyzer python tools/engine-mod-rebalance/evaluate.py`
(exit 0 = E1–E4 pass; the harness applies the diff itself, so a sel typo is a
hard error). Review dashboard:
`tools/engine-mod-rebalance/report.py` → `output/engine-mod-dashboard.html`.

## The system — four archetypes per tier

Instead of a crowded field, each tier offers **four legible archetypes**, one
carrier mod each; every other mod is **parked at a token "degenerate" value**
(the wares can't be removed, so they're made harmless rather than deleted).

| Archetype | Feel | Bundle |
|---|---|---|
| **Interceptor** | straight-line speed | forward thrust (leaks to boost + travel) |
| **Dogfighter** | turn + juke | rotation + strafe |
| **Booster** | burst / escape | boost speed + duration + accel |
| **Voyager** | long-haul cruise | travel speed + fast spool-up |

Carriers are chosen for what the mod **name** evokes (not its vanilla stat);
riders are added to complete each identity:

| Archetype | Basic | Enhanced | Exceptional |
|---|---|---|---|
| Interceptor | **Nudger** | **Impeller** | **Slingshot** |
| Dogfighter | **Sidewinder** | **Antares**\* | **Whirlygig** |
| Booster | **Afterburner** | **Delta** | **Atlas** |
| Voyager | **Overdrive** | **Vinci** | **Vikas** |

\* Enhanced has no rotation/strafe ware, so the boost mod Antares is
repurposed into the agility carrier with rotation + strafe riders.

## Principles

- **No RNG.** Every range pinned (`min = max`); what you craft is what you get.
- **Forward thrust priced modestly.** +X% forward lands on forward, boost,
  travel and boost-accel at once, so the Interceptor is pinned low (Basic
  **+10%**) yet stays competitive — and there is **no super-lever / fake-malus
  problem**, because the design ships no maluses at all.
- **Tiered floor holds the power curve.** Weakest mod pays +5% (Basic), +10%
  (Enhanced); Exceptional is all archetypes (primary ≥ +20%). Carriers scale
  above the floor: ~+10–20% Basic → +20–30% Enhanced → +30–40% Exceptional.
- **Degenerate = intentionally dominated.** The parked mods (incl. the old
  vanilla `_02` "strong" mods that aren't carriers) are exempt from the
  redundancy/ladder checks; the harness only asserts they're actually weak.

## Acceptance targets (all pass)

- **E1** no RNG. **E2** no crossing 1.0 / no fake malus (moot — no maluses).
- **E3** no non-degenerate mod is Pareto-dominated by or identical to another
  in its tier (each archetype owns a distinct corner).
- **E4** no same-variant tier inversion among non-degenerate mods.

## Scorecard (effect vectors are ship-independent)

Bold = archetype carrier; the rest are degenerate (parked at the floor).

| Tier | Archetype / mod | Primary | Delivered peak |
|---|---|---|---|
| Basic | **Nudger** (Interceptor) | fwd ×1.10 | forward (+ boost/travel/accel via leak) |
| Basic | **Sidewinder** (Dogfighter) | strafe ×1.20 | strafe + turn |
| Basic | **Afterburner** (Booster) | boost-accel ×1.20 | boost speed + accel + duration |
| Basic | **Overdrive** (Voyager) | travel-charge ×0.80 | travel speed + spool-up |
| Basic | *11 others* | ×1.05 (times ×0.95) | — parked |
| Enhanced | **Impeller** (Interceptor) | fwd ×1.20 | forward + boost/travel |
| Enhanced | **Antares** (Dogfighter) | +riders | turn + strafe |
| Enhanced | **Delta** (Booster) | boost ×1.30 | boost + duration |
| Enhanced | **Vinci** (Voyager) | travel ×1.30 | travel + spool-up |
| Enhanced | *Propeller, Mira* | ×1.10 | — parked (floor) |
| Exceptional | **Slingshot** (Interceptor) | fwd ×1.30 + riders | speed everywhere |
| Exceptional | **Whirlygig** (Dogfighter) | turn ×1.40 + riders | agility |
| Exceptional | **Atlas** (Booster) | boost ×1.35 + riders | boost sustain |
| Exceptional | **Vikas** (Voyager) | travel ×1.35 + riders | travel + spool |

Scenario mods (`*_transport_refugees`, `*_escort_scenario`) untouched.
**Playtested in-game 2026-07.**
