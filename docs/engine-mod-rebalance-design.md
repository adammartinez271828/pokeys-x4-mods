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

## Design direction (proposal)

Mirror the shipped weapon model: **no RNG, a per-tier power ladder, and one
distinct effect-set identity per mod, with niches carved by physics rather
than by (impossible) per-ship gating.** Concretely:

- **Pin every range (min = max).** What you craft is what you get.
- **Basic tier = one honest specialist per movement axis**, no duplicate
  filler. The redundant clean `_01` mods get repurposed — either folded to
  distinct utility identities (boost *duration*, travel *spool-up*, strafe)
  or given an honest cross-axis trade — so no mod Pareto-dominates another.
- **Roles come from the four things forward thrust cannot buy:**
  - **Agility** (`rotationthrust` + `strafethrust`) — turn rate and strafe
    are pure thruster stats; forward thrust cannot touch them. This is the
    cleanest un-substitutable niche (the dogfighter identity).
  - **Boost** as burst-escape (`boostthrust` + `boostduration`) — duration
    especially is forward-thrust-proof.
  - **Travel** spool-up (`travelchargetime` / `travelattacktime`) — getting
    *into* travel fast, which raw travel speed doesn't give.
  - **Raw speed/accel** (`forwardthrust`) — still the king of the straight
    line, but see the open fork.
- **Honest maluses only.** A malus must be charged in a currency the mod's
  buff cannot silently repay. Forward-thrust mods therefore cannot pay in
  boost/travel (the leak refunds it); if they carry a cost it must be in an
  axis forward thrust never feeds — agility.
- **Retune existing wares + add riders** (both verified savegame-safe:
  rebalancing retunes existing installs; newly *added* bonus children only
  attach to freshly crafted mods). Prefer editing values; add a rider only
  to sharpen an identity the vanilla lever set is too thin to express.
- **Tier ladder** mirrors the research ladder (Basic/Enhanced/Exceptional):
  higher tiers widen the specialist peaks, they don't add new axes.

### THE FORK — how to treat forward thrust — DECIDED: (A)

Chosen 2026-07: **(A) give rivals real niches.** Forward thrust stays the
straight-line king; the other mods win by peaking stats it physically can't
reach (turn, strafe, boost duration, travel spool-up), and any forward-thrust
malus is charged in agility (the one currency the leak can't refund).

- **(A) Give rivals real niches** *(chosen)* — keep `forwardthrust` strong as the
  straight-line king, and make the other mods peak stats it physically can't
  reach (turn, strafe, boost duration, travel spool-up) hard enough that
  agility/logistics builds genuinely prefer them. Forward thrust's malus, if
  any, is charged in agility. Preserves the "go-fast" fantasy; risk is
  forward thrust staying a strong default for combat ships that also want
  speed.
- **(B) Nerf the leak** — pin the boost/travel malus on `forwardthrust`
  mods so the leak nets exactly 1.0 (forward becomes a clean forward-only
  lever like the rest). More symmetric, but flattens the fantasy and makes
  forward thrust just one axis among five.

## Balance acceptance targets (harness)

To be enforced by `tools/engine-mod-rebalance/evaluate.py` (applies the diff,
scores mods on a ship sample via the sim; exit 0 = all pass), adapted from
the weapon harness:

- **E1 — no RNG.** Every roll range is pinned (`min = max`).
- **E2 — no range crosses 1.0**, and **no fake malus**: a stat the mod
  labels a malus must have realized net effect ≤ 1.0 *after* the
  forward-thrust leak (kills the Nudger defect).
- **E3 — no redundancy.** Within a quality tier, no mod is Pareto-dominated
  by another (≥ on every derived stat, > on one) and no two mods are
  identical. A non-dominated mod is a best pick for *some* ship weighting,
  so speed+agility **generalists are legitimate** — the Basic tier has more
  mods (15) than independent movement stats (~10), so not every mod can
  solely own one. The per-stat "peaks" list is reported for information.
- **E4 — tier order can't invert:** no lower-quality mod beats a
  higher-quality mod of the same variant on its primary axis.

(The earlier draft split E3/E4 into a strict single-peak rule plus a Pareto
rule; folded into one E3 for the reason above — decided 2026-07.)

## Hard constraints (shared with the weapon mod)

- **No per-ship mod compatibility exists in game data** — the install UI
  buckets by engine-side `modclass` only. Niches must be carved by physics
  (hull mass/drag/inertia, role), not by compatibility rules.
- **Rebalancing retunes existing installs; added riders do not attach** to
  already-crafted mods (verified for weapons 2026-07; same data mechanism).
- **Scenario mods are left untouched** (`*_transport_refugees`,
  `*_escort_scenario` — already fixed-value, availability-gated).

## Open sim TODOs before the harness is trustworthy

- `strafeacc` and `strafethrust` both currently map to strafe thrust in the
  sim (`MOD_STAT_TARGET`) — dedupe or model a separate strafe-accel field so
  Anchor vs. Crab isn't a false domination.
- Surface `boost_accel` and `travel_attack` as derived stats so the minor
  utility mods (Afterburner/`boostacc`, Spur/`travelattacktime`) aren't
  scored as all-1.0 no-ops.
