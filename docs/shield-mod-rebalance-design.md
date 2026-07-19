# Shield-mod rebalance: design

Third equipment rebalance after weapons and engines, same philosophy applied
to the `<shield>` section of `libraries/equipmentmods.xml`. Built with the
shield model in `~/devel/x4-analyzer` (`x4analyzer.gamedata.shields`).

**Status: Built** (harness-validated, playtested in-game 2026-07).

## The levers

A shield is one `<recharge max rate delay/>` block:

- **capacity** (`max`) — shield HP. The **always-good** stat (the shield
  analog of weapon *damage* / engine *forward speed*): more is never wrong.
- **rechargerate** (`rate`) — HP/s once recharge starts.
- **rechargedelay** (`delay`) — seconds after taking damage before recharge
  begins (**lower is better**).

**The one interaction:** time-to-full ≈ `delay + capacity/rate`, so **capacity
raises the buffer but slows the refill** (bigger pool, same rate). That is a
physical trade-off, not a data malus — capacity mods are still pure upside on
the stat that matters (raw buffer); they just recover slower.

## The archetype model

Only **8 mods** exist (3 Basic, 2 Enhanced, 3 Exceptional), so — unlike
engines — there is no crowding and no "degenerate" parking: every mod is a
real archetype. Carriers are chosen by what the mod **name** evokes
(shield-names → capacity, medical-names → recovery).

| Archetype | Lever | Feel | Basic / Enhanced / Exceptional |
|---|---|---|---|
| **Bastion** | capacity | big buffer / tank | Buckler / Kite / Pavise |
| **Regenerator** | recharge rate | fast refill | Bandage / Cast / Traction |
| **Resilient** | recharge delay | regen sooner | Medic (Basic only) |
| **Bulwark** | balanced | no weakness | Targe (Exceptional only) |

- **Capacity is the tier scalar.** It scales up each tier (Bastion ×1.20 →
  ×1.40 → ×1.60) and rides as a small always-good rider on the higher-tier
  recovery mods (Cast ×1.10, Traction ×1.15) — the "this tier is generally
  better" signal.
- **No RNG** (every range pinned `min = max`), **no maluses** (all buffs; the
  capacity/refill trade-off is physical).
- **The Resilient fold.** Only 2 wares exist at Enhanced, so recharge delay
  has no standalone mod above Basic; it is folded into the Enhanced/Exceptional
  Regenerator (Cast/Traction = rate + delay). Accepted (not filling the gap
  with new wares, which are expensive).

## Acceptance targets (harness)

Enforced by `tools/shield-mod-rebalance/evaluate.py` (applies the diff, exit 0
= pass). Effect vectors are shield-independent (single multipliers).

- **E1** no RNG (every range pinned).
- **E2** no range crosses 1.0.
- **E3** no redundancy: within a tier, no mod is Pareto-dominated by or
  identical to another on capacity / rate / delay — each archetype owns a
  distinct corner.
- **E4** tier order can't invert within a variant (primary + forced-rider
  stat set).

## Hard constraints (shared)

- No per-ship mod compatibility exists in game data; niches are the three
  levers, not compatibility rules.
- Rebalancing retunes existing installs; added riders attach only to newly
  crafted mods (same mechanism as weapons/engines).
