#!/usr/bin/env python
"""Before/after power analysis: best vanilla mod vs best rebalanced mod per
weapon, in sustained cycle DPS and in burst DPS (peak dmg x rate). Emits a
markdown report. Reuses evaluate.py's vanilla+modded setup."""
import sys, statistics as st
from copy import deepcopy
from pathlib import Path
from lxml import etree
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent
sys.path.insert(0, str(_HERE))
import evaluate as E

gf = E.GameFiles(Path(E.DEFAULT_GAME_DIR))
tdb = E.load_textdb(gf)
names = E._mod_ware_names(gf, tdb)
weapons = E.extract_weapons(gf, tdb)
base = etree.fromstring(gf.read_bytes("libraries/equipmentmods.xml"), E._PARSER)
merged = base
for ext in gf.extensions:
    p = f"extensions/{ext}/libraries/equipmentmods.xml"
    if p in gf:
        E.apply_diff(merged, etree.fromstring(gf.read_bytes(p), E._PARSER), ext)
vanilla_mods = E.parse_weapon_mods(merged, names)
patched = deepcopy(merged)
E.apply_diff(patched, etree.parse(str(E.DEFAULT_DIFF), E._PARSER).getroot(), "diff")
modded_mods = E.parse_weapon_mods(patched, names)

QN = {1: "Basic", 2: "Enhanced", 3: "Exceptional"}

def cyc(w, mods):  # shield-channel cycle dps (gain% is channel-independent)
    return E.cycle_dps(w, mods)[0]

def burst(w, mults):
    s = E.simulate(w, mults)
    if s.get("rate") and s.get("dmg_s"):
        return s["dmg_s"] * s["rate"]
    return None

def best_over(mods, w, bare, fn):
    best, who = None, None
    for m in mods:
        if not E.eligible_pair(m, w):
            continue
        v = fn(w, E.mod_multipliers(m, w))
        if v and v > 0:
            g = v / bare - 1
            if best is None or g > best:
                best, who = g, m
    return best, who

def wclass(w):
    heat = (w.get("heat") or 0) > 0 and (w.get("overheat") or 0) > 0 and (w.get("coolrate") or 0) > 0
    clip = (w.get("ammo_clip") or 0) > 0
    return "heat" if heat else ("clip" if clip else "heatless")

rows = []
for w in weapons:
    if "KHA" in w["name"].upper() or E.is_mining_weapon(w):
        continue
    bc = cyc(w, None); bb = burst(w, None)
    if not bc or bc <= 0:
        continue
    bef_c, befm_c = best_over(vanilla_mods, w, bc, cyc)
    now_c, nowm_c = best_over(modded_mods, w, bc, cyc)
    # best now per tier (cycle)
    tier_c = {}
    for q in (1, 2, 3):
        g, m = best_over([x for x in modded_mods if x["quality"] == q], w, bc, cyc)
        tier_c[q] = (g, m)
    bef_b = now_b = befm_b = nowm_b = None
    if bb and bb > 0:
        bef_b, befm_b = best_over(vanilla_mods, w, bb, burst)
        now_b, nowm_b = best_over(modded_mods, w, bb, burst)
    rows.append(dict(w=w, cls=wclass(w),
                     bc=bc, bef_c=bef_c, befm_c=befm_c, now_c=now_c, nowm_c=nowm_c,
                     tier_c=tier_c, bb=bb, bef_b=bef_b, befm_b=befm_b,
                     now_b=now_b, nowm_b=nowm_b))

def med(xs): return st.median(xs) if xs else float("nan")
def pct(x): return f"{x*100:+.0f}%" if x is not None else "—"
def mul(x):  # x is a (ratio - 1) value; show the ratio itself as a multiplier
    return f"×{x+1:.2f}" if x is not None else "—"

out = []
W = out.append
W("# Weapon-mod rebalance — before/after power analysis\n")
W("How the rebalanced mods compare to vanilla, measured as **best available "
  "mod per weapon** (\"whatever was best before\" vs \"whatever is best now\", "
  "each at its optimal roll). Two metrics:\n")
W("- **Sustained (cycle) DPS** — full firing cycle including heat/clip throttling.")
W("- **Burst DPS** — peak `damage × fire-rate` before any heat/clip throttle "
  "(rewards damage + reload, ignores cooling).\n")
W(f"Scope: {len(rows)} obtainable weapons/turrets (6 KHA excluded); mining "
  "weapons count only mining mods. Gain % is vs the bare weapon; the ratio is "
  "channel-independent for these mods, so the shield channel is used. Vanilla "
  "mods are taken at their optimal (best) roll — for most weapons that was "
  "Slasher's ×2 reload-reroll lottery.\n")
W("Beam weapons are modelled as many sub-shots packed into a live window: "
  "`dmg_s` is the per-second intensity, the beam is live for `lifetime` of "
  "every `reload_time` cycle, so peak/burst = `dmg_s × reload` and sustained "
  "= peak × `lifetime/reload_time` × heat duty. Reload packs the sub-shots "
  "tighter (raising both burst and sustained); it does not change the on/off "
  "cycle. This matches the in-game encyclopedia (ARG M Beam Turret: 168 × "
  "3/7 = 72 MW Weapon Output; S Beam Emitter burst 110→134 under reload "
  "×1.225).\n")

# ---- overall ----
bef_c = [r["bef_c"] for r in rows if r["bef_c"] is not None]
now_c = [r["now_c"] for r in rows if r["now_c"] is not None]
ratio_c = [ (1+r["now_c"])/(1+r["bef_c"]) - 1 for r in rows
            if r["bef_c"] is not None and r["now_c"] is not None ]
weaker = sum(1 for x in ratio_c if x < -0.005)
strong = sum(1 for x in ratio_c if x > 0.005)
W("## Sustained (cycle) DPS\n")
W("The last column compares the two *modded end-states*: the best-modded DPS "
  "now ÷ the best-modded DPS before. It is **not** the difference of the two "
  "gain-over-bare percentages. `×0.50` means the best mod you can now fit "
  "produces half the DPS the best vanilla mod did; `×1.10` means 10% more.\n")
W("| | Best vanilla mod | Best rebalanced mod | Best-modded DPS, now ÷ before |")
W("|---|---|---|---|")
W(f"| median gain over bare | {pct(med(bef_c))} | {pct(med(now_c))} | {mul(med(ratio_c))} |")
W(f"| mean gain over bare | {pct(st.mean(bef_c))} | {pct(st.mean(now_c))} | {mul(st.mean(ratio_c))} |")
W(f"| max gain over bare | {pct(max(bef_c))} | {pct(max(now_c))} | |\n")
W(f"Of {len(ratio_c)} weapons, the best mod is **weaker now on {weaker} "
  f"({weaker/len(ratio_c)*100:.0f}%)** and stronger on {strong} "
  f"({strong/len(ratio_c)*100:.0f}%). The rebalance mostly *lowers* peak mod "
  "power — it removes the Slasher reroll lottery — while making the choice "
  "meaningful.\n")

# by class
W("### By weapon class (median best-mod gain over bare)\n")
W("| class | n | best vanilla | best now | now ÷ before |")
W("|---|---|---|---|---|")
for c in ("heat", "clip", "heatless"):
    rs = [r for r in rows if r["cls"] == c]
    b = [r["bef_c"] for r in rs if r["bef_c"] is not None]
    n = [r["now_c"] for r in rs if r["now_c"] is not None]
    rr = [ (1+r["now_c"])/(1+r["bef_c"])-1 for r in rs
           if r["bef_c"] is not None and r["now_c"] is not None ]
    W(f"| {c} | {len(rs)} | {pct(med(b))} | {pct(med(n))} | {mul(med(rr))} |")
W("")

# best-now per tier
W("### Best rebalanced mod by tier (median gain over bare)\n")
W("| tier | median | max |")
W("|---|---|---|")
for q in (1, 2, 3):
    g = [r["tier_c"][q][0] for r in rows if r["tier_c"][q][0] is not None]
    W(f"| {QN[q]} | {pct(med(g))} | {pct(max(g))} |")
W("")

# biggest reductions
W("### Biggest sustained-DPS reductions (where vanilla Slasher was most broken)\n")
red = sorted((r for r in rows if r["bef_c"] and r["now_c"] is not None),
             key=lambda r: (1+r["now_c"])/(1+r["bef_c"]))[:10]
W("| weapon | best vanilla | best now (mod) | now ÷ before |")
W("|---|---|---|---|")
for r in red:
    rr = (1+r["now_c"])/(1+r["bef_c"])-1
    W(f"| {r['w']['name']} | {pct(r['bef_c'])} ({r['befm_c']['name']}) | "
      f"{pct(r['now_c'])} ({r['nowm_c']['name']}) | {mul(rr)} |")
W("")
stronger = sorted((r for r in rows if r["bef_c"] is not None and r["now_c"] is not None
                   and (1+r["now_c"])/(1+r["bef_c"])-1 > 0.005),
                  key=lambda r: -((1+r["now_c"])/(1+r["bef_c"])))[:10]
if stronger:
    W("### Weapons where the best mod is now STRONGER than vanilla\n")
    W("| weapon | best vanilla | best now (mod) | now ÷ before |")
    W("|---|---|---|---|")
    for r in stronger:
        rr = (1+r["now_c"])/(1+r["bef_c"])-1
        W(f"| {r['w']['name']} | {pct(r['bef_c'])} ({r['befm_c']['name']}) | "
          f"{pct(r['now_c'])} ({r['nowm_c']['name']}) | {mul(rr)} |")
    W("")

# ---- burst ----
brows = [r for r in rows if r["bef_b"] is not None and r["now_b"] is not None]
bef_b = [r["bef_b"] for r in brows]
now_b = [r["now_b"] for r in brows]
ratio_b = [ (1+r["now_b"])/(1+r["bef_b"])-1 for r in brows ]
W("Peak un-throttled output — `damage × fire-rate` for bullet/clip weapons, "
  "and `damage × reload` intensity for beams (reload packs their sub-shots "
  "tighter). Damage and reload both raise it on every weapon type; cooling "
  "never affects peak. So the burst winners are the damage + reload mods.\n")
W("| | best vanilla | best rebalanced | best-modded burst, now ÷ before |")
W("|---|---|---|---|")
W(f"| median gain over bare | {pct(med(bef_b))} | {pct(med(now_b))} | {mul(med(ratio_b))} |")
W(f"| mean gain over bare | {pct(st.mean(bef_b))} | {pct(st.mean(now_b))} | {mul(st.mean(ratio_b))} |")
W(f"| max gain over bare | {pct(max(bef_b))} | {pct(max(now_b))} | |\n")
# which mod wins burst now
from collections import Counter
cnt = Counter(r["nowm_b"]["name"] for r in brows if r["nowm_b"])
W("### Which mod wins burst now (count of weapons where it's the top burst pick)\n")
W("| mod | tier | weapons |")
W("|---|---|---|")
byware = {m["name"]: m for m in modded_mods}
for nm, c in cnt.most_common():
    W(f"| {nm} | {QN[byware[nm]['quality']]} | {c} |")
W("")
W("### Burst by weapon class (median best-mod gain over bare)\n")
W("| class | best vanilla | best now | now ÷ before |")
W("|---|---|---|---|")
for c in ("heat", "clip", "heatless"):
    rs = [r for r in brows if r["cls"] == c]
    if not rs: continue
    b = [r["bef_b"] for r in rs]; n = [r["now_b"] for r in rs]
    rr = [ (1+r["now_b"])/(1+r["bef_b"])-1 for r in rs ]
    W(f"| {c} | {pct(med(b))} | {pct(med(n))} | {mul(med(rr))} |")
W("")

# ---- detailed worked examples ----
STAT_LABEL = {"damage": "dmg", "cooling": "cool", "reload": "reload",
              "chargetime": "charge", "rotationspeed": "rot",
              "sticktime": "stick", "lifetime": "life", "speed": "speed",
              "surfaceelement": "surf", "mining": "mining",
              "beamlength": "beam"}
def fmt_mults(m, w):
    mm = E.mod_multipliers(m, w)
    parts = [f"{STAT_LABEL.get(k,k)} ×{v:.2f}" for k, v in mm.items()
             if abs(v - 1.0) > 1e-6]
    return ", ".join(parts) if parts else "—"

def find(nm):
    for r in rows:
        if r["w"]["name"] == nm:
            return r
    return None

def example(nm, blurb):
    r = find(nm)
    if not r:
        return
    w = r["w"]
    bare_c = r["bc"]; bare_b = r["bb"]
    bvm, bvw = best_over(vanilla_mods, w, bare_c, cyc)
    nvm, nvw = best_over(modded_mods, w, bare_c, cyc)
    bbm, bbw = (best_over(vanilla_mods, w, bare_b, burst) if bare_b else (None, None))
    nbm, nbw = (best_over(modded_mods, w, bare_b, burst) if bare_b else (None, None))
    W(f"**{nm}** — {blurb}\n")
    W(f"| metric | bare | best vanilla | best rebalanced |")
    W(f"|---|---|---|---|")
    vc = f"**{bvw['name']}** {pct(bvm)}<br><sub>{fmt_mults(bvw, w)}</sub>"
    nc = f"**{nvw['name']}** ({QN[nvw['quality']]}) {pct(nvm)}<br><sub>{fmt_mults(nvw, w)}</sub>"
    W(f"| sustained DPS | {bare_c:,.0f} | {bare_c*(1+bvm):,.0f} — {vc} | {bare_c*(1+nvm):,.0f} — {nc} |")
    if bare_b:
        vb = f"**{bbw['name']}** {pct(bbm)}<br><sub>{fmt_mults(bbw, w)}</sub>"
        nb = f"**{nbw['name']}** ({QN[nbw['quality']]}) {pct(nbm)}<br><sub>{fmt_mults(nbw, w)}</sub>"
        W(f"| burst DPS | {bare_b:,.0f} | {bare_b*(1+bbm):,.0f} — {vb} | {bare_b*(1+nbm):,.0f} — {nb} |")
    W("")

W("## Worked examples\n")
W("Actual per-weapon numbers (DPS is the shield channel; the multiplier "
  "line shows the mod's *forced* rolls at optimal value). These trace the "
  "aggregates above to concrete guns.\n")
W("### The Slasher lottery, dismantled\n")
W("On continuous-fire turrets Slasher's cooling malus was free, so its "
  "reload-reroll ×2 and ×1.5 damage stacked into a flat **+201% burst** with "
  "no downside — the single defect the rebalance targets.\n")
example("ARG L Beam Turret Mk1",
        "heatless L turret — the pure Slasher-lottery case (cooling malus costs nothing).")
example("PAR M Mass Driver Turret Mk1",
        "clip turret — Slasher's cooling malus is free, reload reroll dominates.")
W("### The intended winners: heat-limited guns\n")
W("Weapons whose DPS is gated by heat get *more* from the rebalanced "
  "cooling/damage capstones than they ever did from Slasher — whose cooling "
  "malus actively hurt them. These are the weapons that get **stronger**.\n")
example("S Plasma Cannon Mk1",
        "heat-limited S gun — Obliterator's forced cooling buff beats Slasher's malus.")
example("ATF XL Main Battery",
        "the extreme heat responder — cooling is worth more here than anywhere.")
example("TER M Meson Stream Mk1",
        "beam with a heavy heat bill — Obliterator overtakes vanilla by +11%.")

(_REPO / "docs" / "weapon-mod-rebalance-power-analysis.md").write_text("\n".join(out))
print("wrote docs/weapon-mod-rebalance-power-analysis.md")
print(f"cycle: median before {med(bef_c)*100:+.0f}% now {med(now_c)*100:+.0f}%  weaker {weaker}/{len(ratio_c)}")
print(f"burst: median before {med(bef_b)*100:+.0f}% now {med(now_b)*100:+.0f}%")
