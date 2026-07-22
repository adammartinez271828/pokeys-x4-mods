# Weapon-mod rebalance — impact of the 2026-07 weapon-sim fixes

Two commits landed in `~/devel/x4-analyzer` that change how the shared
firing-cycle simulator (`gamedata/weaponsim.py`) scores heat and clip
weapons:

- **`441c755`** — mass-driver heat parse (`<heat initial>` fallback) + clip
  weapons report the **sustained** rate, and the clip cycle span is corrected
  to `(clip−1)·interval + reload` (N shots have N−1 gaps).
- **`b038647`** — replaces the continuous net-rate heat model with a
  **discrete, shot-by-shot / activation-by-activation** heat simulation, so a
  big per-shot spike and a beam's onset spike are modelled correctly.

Source of truth for the sim behaviour: `x4-analyzer/docs/weapon-heat-and-rate-bug-2026-07.md`.

**Bottom line: the weapon-mod-rebalance table still passes every acceptance
target unchanged — no re-tune is required.** But the fixes move real DPS
numbers on four weapon families, flip the best-mod pick on 31 of 223 weapons,
and make several design-narrative claims (and the worked numbers) in
`weapon-mod-rebalance-design.md` / `-v1.md` stale. This doc records what moved
so those two can be corrected, and flags one genuinely *new* behaviour worth a
line in the shipped copy.

Method: applied the shipped diff under the pre-fix analyzer (`50ebacb`) and the
post-fix analyzer (HEAD), and diffed full-cycle vs-shield DPS and the
best-among-Basic-DPS-mods pick, per weapon. Scratch tooling was throwaway; the
harness (`tools/weapon-mod-rebalance/evaluate.py`) reproduces the pass/fail.

## The four affected families

| Family | Count | Base DPS shift | What changed |
|---|---|---|---|
| **Mass drivers** (PAR railguns) | 4 | **−56 to −57%** | Were modelled heatless (duty 1.0); now overheat in **2 shots**, duty ~0.23 |
| **Beam guns** (non-turret emitters/streams) | ~12 | **−33 to −47%** | Discrete per-activation heat → lower heat duty; Scalar Aperture now "one full beam, then a short one" |
| **Clip/burst weapons** | 119 | **0 to +30%** (mostly up) | Sustained-rate report + `(clip−1)`-gap cycle → shorter cycle, higher cyc-DPS, lower duty |
| **Slow non-clip heat guns** (Plasma Cannon, Muon Disintegrator) | ~8 | **+5 to +14%** | Discrete heat → whole-number shot counts, cooling worth less at the margin |

Beam **turrets** (13) and mass-driver **turrets** are **unchanged** — they carry
no `<heat value>`, so they were always structural-/duty-limited and the discrete
model is a no-op for them (all still Cowboy/reload, as designed).

## Best-Basic-mod flips: 31 of 223 weapons

Almost all flips are **inside the tie band** (the new top beats the runner-up by
0.06–3.7%), which is exactly the "damage-backed safe pick vs specialist" cluster
the design intends. The flips are a re-sort *within* a near-tie, not a mod
becoming dominant. Direction of travel:

### 1. Mass drivers — a genuinely NEW cooling niche (the one worth shipping copy)

Previously heatless → raw damage/duty won (Stabber). Now they overheat hard (2
shots, ~4 s, then a cooldown), so the nominal best pick flips to **cooling
(Tramontane / Gregale)** — it buys back shots and shortens the offline time.
This is the only *qualitative* change: cooling mods went from doing **nothing**
on Paranid Mass Drivers to being a live contender on them.

```
PAR M/S Mass Driver Mk1/2:  Stabber → Tramontane (S Mk2 → Gregale)
                            base DPS −56%, duty 1.0 → 0.23, 2 shots/cycle
```

The margins over pure damage are tie-band (0.06–0.27%), so this is cooling
*joining the contest*, not routing it — but it is a real behavioural change: the
old heatless model gave cooling zero value here. The design doc frames cooling as
"worthless on the heatless majority … the hottest heat-limited main guns"; mass
drivers are now a second cooling home worth a clause in `-v1.md`'s
Tramontane/Gregale rows.

### 2. Slow heat guns (Plasma Cannon, Muon) — cooling ties/loses to damage-blends

The continuous model over-credited cooling on slow, high-per-shot guns (it let
coolrate push duty up smoothly). The discrete model corrects this: duty drops
(Plasma Cannon 0.45 → 0.33) and a damage-blend generalist edges pure cooling.

```
M/S Plasma Cannon:      Tramontane → Slasher / Gregale   (margins 0.6–1.1%)
TEL Muon Disintegrator: Tramontane → Gregale / Mistral   (margins 0.7–1.5%)
```

These are tie-band swaps, not routs — Tramontane is still best-or-tied here to
within ~1%. But the design-doc line **"Tramontane … the hottest heat-limited
main guns"** using the Plasma Cannon as its mental model is now imprecise:
post-fix, its clean wins are the **mass drivers** and only the *very* hottest
guns (e.g. the 9-shot S Plasma Cannon variant, still Tramontane +3.7%). The
Mistral/cooling-reload synergy pick likewise picks up the small Muon guns.

### 3. Beam guns — reload/cooling gain, damage-triple loses

Beam-gun absolute DPS fell sharply (−33 to −47%) because the discrete
per-activation heat model gives a lower, correctly-heat-limited duty. Relative
mod value shifts toward the rate/heat mods:

```
S/M Beam Emitter:  Slasher → Mistral (cooling+reload) / Cowboy (reload)
Scalar Aperture:   Mistral → Tramontane
```

This *reinforces* the design story — reload raises beam intensity, cooling pays
the heat bill, and the pure-damage-triple Slasher no longer wins where heat is
the true limiter. The **ATF XL Main Battery** headline outlier is unaffected
(base +0.6%, still Tramontane, duty 0.06) — it was already so heat-saturated
that continuous ≈ discrete.

### 4. Clip weapons — reload even more taxed, Piercer edges Stabber

The `(clip−1)`-gap correction shortens the clip cycle, so the fixed reload is a
larger share of it and the intra-burst interval (the only thing reload mods
touch) buys **less**. Pure damage therefore overtakes damage+reload on several
clips:

```
Ion Blaster, Plasma Turret, Needler, Flak, Phoenix Main Battery:
    Stabber/Slasher → Piercer   (reload's clip tax is now steeper)
Bolt Repeater (heat + clip):  Slasher → Mistral
Thermal Disintegrator:        Slasher → Gregale
```

This is consistent with — and strengthens — the shipped claim that "clips only
pay partial value on fire rate." Nothing to fix in intent; the *numbers* behind
it moved.

## Acceptance targets: still green

`uv run --project ~/devel/x4-analyzer python tools/weapon-mod-rebalance/evaluate.py`
→ **exit 0, all targets pass** under the new sim:

- **T1** within-tier dominance — pass (worst still Exterminator/Annihilator ~66–67%).
- **T2** usefulness — pass; every DPS-primary mod is best-or-tied within its tier
  somewhere. Cooling mods keep their niche (Tramontane now *via* mass drivers +
  hottest guns rather than the Plasma Cannon).
- **T4** tier order — no within-variant inversion.
- **T5** — no range crosses 1.0 (min = max everywhere).

The informational **max secondary-bundle** figure moved: **+48.0% (Invader on
TEL M Muon Disintegrator)**, up from the +38.3% (Invader on ATF XL) quoted in
`-v1.md` — the Muon's changed heat behaviour is why the peak relocated. Still
uncapped by design (T3 removed), so this is a doc-number update, not a failure.

## Stale numbers to correct in the shipped docs

None of these change the table; they change the *prose/worked figures* computed
off the old sim:

- **`weapon-mod-rebalance-v1.md`**
  - Tramontane / Gregale rows: cooling now also owns the **Paranid Mass Drivers**
    (new heat mechanic); its Plasma-Cannon win is now a near-tie with the
    damage-blends. Reword "the hottest heat-limited main guns" accordingly.
  - The "Basic DPS bucket" strict-win / best% counts were read off the old sim;
    recomputed under the new sim over the same 211 non-KHA weapons (vs-shield,
    within-Basic-tier): Piercer **53 (15g/38t) 47%**, Cowboy **22 (3g/19t) 12%**,
    Tramontane **8 (8g) 8%**, Mistral **19 (19g) 15%** (up from 9 — beam guns +
    small Muon/Bolt Repeater), Stabber **23 (10g/13t) 26%** (down from 29 —
    clips lost to Piercer), Gregale **7 (7g) 8%** (up from 2 — heat guns),
    Slasher **8 (8g) 11%**, Jumper **2 (2g) 1%**.
  - Harness-scorecard bullet: bundle max is **+48.0% (Invader on Muon
    Disintegrator)**, not +38.3% on ATF XL. The stale "no bundle worth ≥25%"
    line under *Bounded everything* also predates the T3 removal.
- **`weapon-mod-rebalance-design.md`** — same cooling-niche wording; the
  "niches come from weapon physics: heat level" paragraph should note mass
  drivers as a heat family (they read as heatless under the old sim).
- **`tools/weapon-mod-rebalance/tuner.{src.html,html}` + `tuner-data.json`** —
  the tuner carries a **hand-ported JS copy** of `simulate()` that is *also*
  stale: it still uses the continuous net-rate heat model, the old
  `clip·interval + reload` cycle, and does not read `heat_initial`. A
  `dump_data.py` rebuild alone will NOT fix it — the JS `simulate()` must be
  re-ported to the discrete model and `SIM_WEAPON_FIELDS` must add
  `heat_initial`. Larger than a doc edit; tracked as a follow-up, not applied here.

## Recommendation

Ship-as-is: the balance holds and all targets pass. The corrections above are
housekeeping on the narrative + a small win for the cooling mods (a clean new
mass-driver niche) that's worth one line of player-facing copy. Worth an in-game
spot-check on a **Paranid Mass Driver** to confirm cooling now feels meaningful
there (the sim says 2 shots → overheat, cooling buys back shots) and on an
**S/M Beam Emitter** where absolute DPS and the best mod both moved most.
