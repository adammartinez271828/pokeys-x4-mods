# Engine-mod rebalance v1

The table shipped in `engine-mod-rebalance/libraries/equipmentmods.xml`
(122 ops: attribute pins, two child-swaps on the forward specialists, all in
the `<engine>` section). Design rationale:
`docs/engine-mod-rebalance-design.md`. Validation:
`uv run --project ~/devel/x4-analyzer python tools/engine-mod-rebalance/evaluate.py`
(exit 0 = all acceptance targets pass; the harness applies the diff itself,
so a sel typo is a hard error, not a silent no-op).

**All three tiers designed** (Basic / Enhanced / Exceptional) on one model: a
per-tier power ladder mirroring the research ladder, each mod a distinct
movement identity, built on fork A (forward thrust stays the straight-line
king; rivals win on stats it physically cannot buy).

## The system

X4 motion comes from engine forward/boost/travel thrust, a thruster's
strafe/rotation thrust, and the ship's mass/drag/inertia. `max speed =
thrust/drag`, `accel = thrust/mass`. The one structural fact that shapes
everything: **forward thrust also drives boost and travel speed** (both are
multipliers of it), so a forward-thrust mod moves four stats at once while
every other lever moves one.

- **No roll RNG.** Every range is pinned (`min = max`): what you craft is
  what you get. The only randomness left is engine-side *selection* of the
  optional pool bonuses on the Enhanced clean mods, which game data cannot
  remove (their values are pinned regardless).

- **Forward = the generalist.** `Pusher` (+20%) / `Propeller` (+30%) /
  `Slingshot` (+40%) raise forward, boost and travel together: the universal
  "faster everywhere" pick and the benchmark the specialists must beat on
  their own axis.

- **Specialists out-peak the leak and pay honestly.** Each `_02` buffs its
  axis to +45% (Enhanced +55%), above the forward generalist's leak, and pays
  a **real** malus in a stat its own buff cannot silently refund:
  - `Minuteman`/`Delta` (boost) pay in travel; `Reaver`/`Vinci` (travel) pay
    in boost; `Twister` (turn) pays in strafe; `Sidewinder` (strafe) pays in
    turn; `Nudger`/`Impeller` (forward) pay in **turn** (the one currency the
    forward leak cannot repay). Vanilla charged the forward mods in
    boost/travel, which the leak refunded to a net *gain* - the central bug
    this fixes.

- **Clean mods are the safe band.** Each `_01` (`Juno`, `Aestus`, `Spinner`,
  `Crab`, +25%) sits just above the generalist's leak, so it is never a
  strictly worse pick: it wins the very stat its `_02` sibling sacrificed
  (boost without losing travel, turn without losing strafe...). They peak no
  single stat but are Pareto-efficient generalists - the tie band.

- **Utility mods own the un-leakable niches.** `Creatine` (boost duration),
  `Afterburner` (boost-accel), `Anchor` (strafe-accel), `Spur` (travel
  attack), `Overdrive` (travel charge): stats forward thrust never touches.

- **Exceptional = pure-upside capstones.** `Slingshot` (speed), `Whirlygig`
  (agility), `Atlas` (boost+duration), `Vikas` (travel+spool): rich forced
  buff sets, no maluses, each owning a niche the others cannot (so even the
  Slingshot speed monster dominates none of them).

## Acceptance targets (all pass)

Enforced by `tools/engine-mod-rebalance/evaluate.py`:

- **E1** no RNG (every range pinned).
- **E2** no range crosses 1.0, and no fake malus (a declared malus must stay
  a net loss after the forward-thrust leak).
- **E3** no redundancy: within a tier no mod is Pareto-dominated by, or
  identical to, another (generalists in the tie band are legitimate).
- **E4** tier order never inverts within a variant.

## Scorecard (representative; effect vectors are ship-independent)

| tier | mod | primary | peaks (informational) |
|---|---|---|---|
| Basic | Pusher | forward x1.20 | (generalist) |
| Basic | Nudger | forward x1.35, turn -15% | forward speed |
| Basic | Juno | boost x1.25 | (clean) |
| Basic | Minuteman | boost x1.45, travel -15% | boost speed |
| Basic | Aestus | travel x1.25 | (clean) |
| Basic | Reaver | travel x1.45, boost -15% | travel speed |
| Basic | Spinner | turn x1.25 | (clean) |
| Basic | Twister | turn x1.45, strafe -15% | turn rate |
| Basic | Crab | strafe x1.25 | (clean) |
| Basic | Sidewinder | strafe x1.45, turn -15% | strafe speed + accel |
| Basic | Creatine | boost duration x1.30 | boost duration |
| Basic | Afterburner | boost-accel x1.45 | boost accel |
| Basic | Anchor | strafe-accel x1.30 | (clean) |
| Basic | Spur | travel attack x0.75 | travel spool |
| Basic | Overdrive | travel charge x0.75 | travel spool |
| Enhanced | Propeller | forward x1.30 | (generalist) |
| Enhanced | Impeller | forward x1.45, turn -15% | forward speed |
| Enhanced | Antares | boost x1.35 | (clean) |
| Enhanced | Delta | boost x1.55, travel -15% | boost speed |
| Enhanced | Mira | travel x1.35 | (clean) |
| Enhanced | Vinci | travel x1.55, boost -15% | travel speed |
| Exceptional | Slingshot | forward x1.40 + boost/travel/turn/strafe | speed capstone |
| Exceptional | Whirlygig | turn x1.50 + forward/strafe | agility capstone |
| Exceptional | Atlas | boost x1.30 + forward/duration/accel/strafe | boost capstone |
| Exceptional | Vikas | travel x1.40 + forward/spool/turn/strafe | travel capstone |

Scenario mods (`*_transport_refugees`, `*_escort_scenario`) are
availability-gated and untouched.
