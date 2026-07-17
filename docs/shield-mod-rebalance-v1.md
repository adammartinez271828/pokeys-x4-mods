# Shield-mod rebalance v1

The table shipped in `shield-mod-rebalance/libraries/equipmentmods.xml`
(33 ops, `<shield>` section only). Design rationale:
`docs/shield-mod-rebalance-design.md`. Validation:
`uv run --project ~/devel/x4-analyzer python tools/shield-mod-rebalance/evaluate.py`
(exit 0 = E1–E4 pass; the harness applies the diff itself, so a sel typo is a
hard error). Review dashboard:
`tools/shield-mod-rebalance/report.py` → `output/shield-mod-dashboard.html`.

**Status: DRAFT** — harness-validated, not yet in-game verified.

## The system — three levers, three archetypes

Shields have three levers (capacity, recharge rate, recharge delay) and only 8
mods, so every mod is a real archetype — no "degenerate" parking. Carriers are
chosen by what the mod **name** evokes (shield-names → capacity, medical-names
→ recovery).

| Archetype | Lever | Feel | Basic / Enhanced / Exceptional |
|---|---|---|---|
| **Bastion** | capacity | big buffer / tank | Buckler / Kite / Pavise |
| **Regenerator** | recharge rate | fast refill | Bandage / Cast / Traction |
| **Resilient** | recharge delay | regen sooner | Medic (Basic only) |
| **Bulwark** | balanced | no weakness | Targe (Exceptional only) |

## Principles

- **Capacity is the always-good stat** (the shield analog of weapon *damage* /
  engine *forward speed*): more is never wrong, so it is the tier scalar — it
  climbs each tier (Bastion ×1.20 → ×1.40 → ×1.60) and rides as a small
  always-good bonus on the higher-tier recovery mods.
- **The trade-off** is physical, not a malus: capacity raises the buffer but
  **slows the refill** (time-to-full ≈ delay + capacity/rate), so Bastion tanks
  harder but recovers slower; Regenerator/Resilient recover faster.
- **No RNG** (every range pinned), **no maluses** (all buffs).
- **Resilient fold**: only 2 Enhanced wares exist, so recharge delay has no
  standalone mod above Basic — it is folded into the Enhanced/Exceptional
  Regenerator (decided: not adding new wares).

## Acceptance targets (all pass)

- **E1** no RNG · **E2** no range crosses 1.0 · **E3** no mod Pareto-dominated
  by or identical to another in its tier · **E4** no same-variant tier
  inversion.

## Scorecard (effect vectors are shield-independent)

Delay shown as its goodness factor (a ×0.80 delay = ×1.25 here). Refill time
is for the representative M shield (5750 HP, 100 HP/s, 12.5 s) — **higher =
slower to refill**, the capacity trade-off.

| Tier | Archetype / mod | Capacity | Rate | Delay | Refill time |
|---|---|---|---|---|---|
| Basic | **Buckler** (Bastion) | ×1.20 | — | — | ×1.16 |
| Basic | **Bandage** (Regenerator) | — | ×1.20 | — | ×0.86 |
| Basic | **Medic** (Resilient) | — | — | ×1.25 | ×0.96 |
| Enhanced | **Kite** (Bastion) | ×1.40 | ×1.10 | — | ×1.22 |
| Enhanced | **Cast** (Regenerator) | ×1.10 | ×1.30 | ×1.18 | ×0.85 |
| Exceptional | **Pavise** (Bastion) | ×1.60 | ×1.15 | — | ×1.32 |
| Exceptional | **Traction** (Regenerator) | ×1.15 | ×1.50 | ×1.67 | ×0.74 |
| Exceptional | **Targe** (Bulwark) | ×1.35 | ×1.25 | ×1.25 | ×1.03 |

Each tier's archetypes are mutually non-dominated: Bastion owns capacity,
Regenerator owns rate (and delay via the fold), Targe is the balanced pick
(refill ≈ ×1.0 — no weakness). **Not yet verified in-game.**
