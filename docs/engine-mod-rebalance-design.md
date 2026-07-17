# Engine-mod rebalance: vanilla analysis & design direction

Companion to `docs/weapon-mod-rebalance-design.md`, same philosophy applied
to the `<engine>` section of `libraries/equipmentmods.xml`. Everything here
is produced with the new engine-mod sim in `~/devel/x4-analyzer`
(`x4analyzer.gamedata.engines`: extraction + the X4 movement model,
cross-checked against the v9 game files). Rerun the analysis scripts in
`tools/engine-mod-rebalance/`.

**Status: DRAFT for review.** The model below is a proposal; the one open
fork (how to treat the forward-thrust super-lever) is called out explicitly
and not yet decided.

## The movement model (what a mod actually changes)

A ship's motion comes from three components — the **engine** (`thrust
forward/reverse`, `boost`, `travel`), a size-matched **thruster** (`thrust
strafe/pitch/yaw/roll`), and the ship's **`<physics>`** (mass, inertia,
per-axis drag). Two documented formulas, applied per axis:

    max speed(axis) = thrust(axis) / drag(axis)
    acceleration    = thrust        / mass     (linear)
    angular accel   = thrust        / inertia  (rotational)

`boost/@thrust` and `travel/@thrust` are **multipliers of forward thrust**,
so boost and travel top speed are `forward_speed × the boost/travel
multiplier`. Absolute boost/travel m/s from this model read low versus the
in-game encyclopedia (omitted global constants), but a mod scales the same
base quantity for every mod, so **the constant cancels in mod-vs-mod
comparison** — rankings and best-at-a-stat verdicts are exact; treat the
absolute m/s as relative.

Each engine-mod stat tag multiplies one base quantity:

| tag | multiplies | moves these derived stats |
|---|---|---|
| `forwardthrust` | engine forward thrust | forward speed, forward accel, **boost speed, travel speed** |
| `boostthrust` | boost multiplier | boost speed |
| `boostduration` | boost duration | boost duration |
| `boostacc` | boost acceleration | boost ramp-up |
| `travelthrust` | travel multiplier | travel speed |
| `travelchargetime` | travel charge (↓) | travel spool-up |
| `travelattacktime` | travel attack (↓) | travel spool-up |
| `rotationthrust` | pitch/yaw/roll thrust | turn rate + turn accel |
| `strafethrust` | strafe thrust | strafe speed + accel |
| `strafeacc` | strafe thrust (best-effort) | strafe (see note) |

## The problem

Vanilla ships 27 engine mods (three quality tiers; two scenario mods,
`*_transport_refugees` / `*_escort_scenario`, are already pinned and left
alone). Three defects, the first two shared with weapons, the third unique
to engines:

### 1. RNG everywhere — illusion of choice

Every one of the 27 mods has `min ≠ max`, so every craft is a lottery and
rerolling is mandatory. Same defect the weapon mod removed by pinning.

### 2. Clean vs. dirty duplicates — the Basic tier is half redundant

Each thrust stat ships **twice**: a weak clean `_01` (≈ +5–20 %, no malus)
and a strong "penalty" `_02` (+35–45 % with a 0.7–0.9 malus). Scored on the
sim, the `_02` mods are the true specialists — each is the sole peak of its
axis at +45 %:

| axis | peak mod (`_02`) | clean duplicate (`_01`) |
|---|---|---|
| forward | Nudger +45 % | Pusher +10 % |
| boost | Minuteman +45 % | Juno +20 % |
| travel | Reaver +45 % | Aestus +20 % |
| turn | Twister +45 % | Spinner +20 % |
| strafe | Sidewinder +45 % | Crab +20 % |

The clean `_01` mods are just weaker copies with no compensating identity —
pure filler. (Pareto check: within Basic, the only non-artefact dominations
are the `_01` mods being strictly beaten once you account for their axis.)

### 3. The forward-thrust super-lever — and its fake malus

Forward thrust feeds forward speed, accel, boost speed **and** travel speed
(boost/travel are multipliers *of* forward thrust). So `forwardthrust`
mods move four stats while every rival moves one — and their maluses are
fake:

> **Nudger** (`forwardthrust_02`): +45 % forward, −25 % boost, −25 % travel.
> Because forward thrust drives boost and travel, the net is boost `1.45 ×
> 0.75 = ` **+9 %** and travel **+9 %**. Its "penalty" is a small *gain*.
> Realized: **+45 % / +45 % / +9 % / +9 %** (fwd speed / accel / boost /
> travel) — it beats the clean Pusher (+10 % to all) almost everywhere and
> pays nothing for it.

This is the engine analogue of the weapon mod's Slasher: a headline buff
whose stated cost is refunded by the physics. Unlike Slasher the maluses
never cross 1.0 (they stay < 1.0 literally), but the leak makes them
inert.

## Design direction — the ARCHETYPE model

Decided 2026-07. The earlier draft made all 15 Basic mods mutually
non-dominated; in play that is still *too many options*. Instead each tier
offers **four legible archetypes**, one carrier mod each, and every other mod
is **parked at a token "degenerate" value** — present (the wares can't be
removed from the game) but plainly not the pick. The result is a handful of
real choices per tier.

**The four archetypes** (the natural clusters of the movement levers):

| Archetype | Feel | Stat bundle |
|---|---|---|
| **Interceptor** | straight-line speed | forward thrust (leaks to boost + travel) |
| **Dogfighter** | turn + juke | rotation + strafe |
| **Booster** | burst / escape | boost speed + duration + accel |
| **Voyager** | long-haul cruise | travel speed + fast spool-up |

**Carriers per tier** (chosen for what the mod's *name* evokes in English, not
its vanilla stat — riders are added to fill out the identity):

| Archetype | Basic | Enhanced | Exceptional |
|---|---|---|---|
| Interceptor | Nudger | Impeller | Slingshot |
| Dogfighter | Sidewinder | Antares\* | Whirlygig |
| Booster | Afterburner | Delta | Atlas |
| Voyager | Overdrive | Vinci | Vikas |

\* Enhanced has no rotation/strafe *ware*, so the boost mod Antares is
repurposed into the agility carrier via rotation + strafe riders.

**Key rules:**

- **Forward thrust is a broad lever, priced modestly.** Because +X% forward
  lands on forward, boost, travel *and* boost-accel at once, the Interceptor
  is pinned low (Basic **+10%**) — that +10% is worth as much as a
  specialist's bigger single-axis number. This also defuses the vanilla
  super-lever/fake-malus problem: there are no maluses at all now
  (archetypes are pure upside), so nothing to secretly refund.
- **No RNG** (every range pinned `min = max`).
- **Tiered floor keeps the power curve monotonic.** The weakest mod pays
  **+5%** at Basic, **+10%** at Enhanced; Exceptional is all archetypes
  (primary **≥ +20%**). Carriers scale above their tier's floor
  (~+10–20% Basic, +20–30% Enhanced, +30–40% Exceptional).
- **Retune existing wares + add riders** (both savegame-safe). Carriers whose
  vanilla ware lacks the needed lever get forced riders added (e.g. Afterburner
  gains boost-speed + duration); the old `_02` "strong" mods that aren't
  carriers are neutralised to the floor.

## Balance acceptance targets (harness)

Enforced by `tools/engine-mod-rebalance/evaluate.py` (applies the diff, scores
via the sim; exit 0 = all pass). A mod is **degenerate** when no derived stat
moves past its tier's cap (`VESTIGIAL_CAP` = +7.5% / +15% / +25%, tracking the
rising floor); degenerate mods are *meant* to be dominated and are exempt from
E3/E4.

- **E1 — no RNG.** Every range pinned (`min = max`).
- **E2 — no range crosses 1.0**, and no fake malus (net effect of a declared
  malus stays ≤ 1.0 after the forward-thrust leak). Moot now — the design
  ships no maluses.
- **E3 — no redundancy among archetypes.** Within a tier, no *non-degenerate*
  mod is Pareto-dominated by or identical to another; each archetype owns a
  distinct corner. The per-stat "peaks" list is informational.
- **E4 — tier order can't invert:** among non-degenerate mods, no lower tier
  beats a higher tier of the same variant (primary + forced-rider stat set)
  on its primary stat.

## Hard constraints (shared with the weapon mod)

- **No per-ship mod compatibility exists in game data** — the install UI
  buckets by engine-side `modclass` only. Niches must be carved by physics
  (hull mass/drag/inertia, role), not by compatibility rules.
- **Rebalancing retunes existing installs; added riders do not attach** to
  already-crafted mods (verified for weapons 2026-07; same data mechanism).
- **Scenario mods are left untouched** (`*_transport_refugees`,
  `*_escort_scenario` — already fixed-value, availability-gated).

## Sim fixes applied (were open TODOs)

- `strafeacc` now scales only strafe *acceleration* (a derived post-multiplier),
  distinct from `strafethrust` which scales strafe thrust (speed + accel).
- `boost_accel` and `travel_attack` are scored as derived stats, so the
  boost-accel / spool-up levers register.

Still open: the design is **not yet verified in-game** — absolute boost/travel
speeds read low vs the encyclopedia (the mod-vs-mod ratios are exact), and no
play-test has confirmed the archetypes feel distinct on real hulls.
