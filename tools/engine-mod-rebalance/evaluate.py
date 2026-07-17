#!/usr/bin/env python
"""Evaluation harness for the engine-mod-rebalance extension.

Run from the repo root with the x4-analyzer environment:

    uv run --project ~/devel/x4-analyzer python tools/engine-mod-rebalance/evaluate.py

What it does (mirrors tools/weapon-mod-rebalance/evaluate.py):

1. Loads the vanilla merged libraries/equipmentmods.xml through GameFiles
   (base game + official DLC only) and verifies its <engine> section against
   docs/reference/equipmentmods-vanilla-v9.xml. A mismatch aborts (exit 2).
2. Applies our extension's <diff> ITSELF with an lxml XPath patcher
   (<replace>/<add>/<remove> sel incl. /@attr). An unmatched sel is a hard
   error (exit 2) - that doubles as the "diff applies cleanly" proof.
3. Parses the patched <engine> table and scores every mod with the
   engine-mod movement sim (x4analyzer.gamedata.engines): each mod's effect
   is expressed as a multiplier on a canonical vector of derived ship stats.
   Because every derived-stat multiplier is a product of the mod's own
   multipliers, the ship's mass/drag/inertia CANCEL in the modded/base ratio
   - so the effect vector is ship-independent and one representative ship
   gives exact numbers.
4. Judges the acceptance targets (docs/engine-mod-rebalance-design.md) and
   exits nonzero (1) if any fails.

Acceptance targets, made mechanical:

  E1 no RNG       every scored mod pins min == max on its primary and on
                  every forced bonus (pool entries too where present).
  E2 honest       no roll range crosses 1.0, AND no fake malus: a forced
                  bonus declared as a malus must still leave the mod's NET
                  effect on that stat's derived quantity <= 1.0 after the
                  forward-thrust leak (kills the Nudger defect, where +45%
                  forward refunds a -25% boost/travel malus).
  E3 no redundancy  within a quality tier, no mod is Pareto-dominated by
                  another (>= on every derived stat, > on one) and no two
                  mods are identical. A mod that is not dominated is a best
                  pick for SOME ship weighting, so generalists (speed+agility
                  hybrids) are legitimate; the per-stat "peaks" list is
                  informational only. (Folds the old single-peak + Pareto
                  checks - the Basic tier has more mods than independent
                  stats, so not all can solely own one.)
  E4 tier order   no lower-quality mod beats a higher-quality mod of the same
                  variant (same primary stat + forced-malus/rider signature)
                  on that variant's primary derived stat.

Scenario mods (wares not ending in _mk<n>: *_transport_refugees,
*_escort_scenario) are availability-gated and untouched; excluded from the
targets but kept in the listing.
"""

from __future__ import annotations

import argparse
import re
import sys
from copy import deepcopy
from pathlib import Path

from lxml import etree

from x4analyzer.gamedata.catalog import GameFiles
from x4analyzer.gamedata.extract import load_textdb
from x4analyzer.gamedata import engines as E

REPO = Path(__file__).resolve().parents[2]
DEFAULT_GAME_DIR = "/games/SteamLibrary/steamapps/common/X4 Foundations"
DEFAULT_DIFF = REPO / "engine-mod-rebalance" / "libraries" / "equipmentmods.xml"
REFERENCE = REPO / "docs" / "reference" / "equipmentmods-vanilla-v9.xml"

_PARSER = etree.XMLParser(recover=True, huge_tree=True)
_MK_WARE = re.compile(r"_mk\d$")

EPS_TIE = 0.005     # within 0.5% = tied / same peak
EPS_INV = 0.01      # >1% = tier inversion / fake malus

# Canonical derived stats scored, and whether higher is better. Coupled stats
# that always move together with another (forward_accel~forward_speed,
# turn_accel~turn_rate, roll_rate~turn_rate) and the unmoddable reverse_speed
# are omitted so E3/E4 count each independent lever once.
EVAL_STATS = {
    "forward_speed": True,
    "boost_speed": True,
    "boost_duration": True,
    "boost_accel": True,
    "travel_speed": True,
    "travel_charge": False,   # a time - lower is better
    "travel_attack": False,   # a time - lower is better
    "turn_rate": True,
    "strafe_speed": True,
    "strafe_accel": True,
}

# stat tag -> the derived stat its malus/buff is really felt on (for E2)
STAT_DERIVED = {
    "forwardthrust": "forward_speed",
    "boostthrust": "boost_speed",
    "boostduration": "boost_duration",
    "boostacc": "boost_accel",
    "travelthrust": "travel_speed",
    "travelchargetime": "travel_charge",
    "travelattacktime": "travel_attack",
    "rotationthrust": "turn_rate",
    "strafethrust": "strafe_speed",
    "strafeacc": "strafe_accel",
}


# --------------------------------------------------------------- patching
# (identical XPath <diff> applier to the weapon harness)

def apply_diff(root, diff_root, label):
    errors = []
    for op in diff_root:
        if not isinstance(op.tag, str):
            continue
        sel = op.get("sel") or ""
        tag = op.tag
        attr = None
        path = sel
        if "/@" in sel:
            path, attr = sel.rsplit("/@", 1)
        try:
            nodes = root.xpath(path)
        except etree.XPathError as e:
            errors.append(f"{label}: bad XPath {sel!r}: {e}")
            continue
        nodes = [n for n in nodes if isinstance(n, etree._Element)]
        if not nodes:
            errors.append(f"{label}: <{tag}> sel matched nothing: {sel}")
            continue
        if tag == "replace":
            if attr:
                value = (op.text or "").strip()
                for n in nodes:
                    n.set(attr, value)
            else:
                repl = [c for c in op if isinstance(c.tag, str)]
                if len(repl) != 1:
                    errors.append(f"{label}: <replace> node needs one child: {sel}")
                    continue
                for n in nodes:
                    n.getparent().replace(n, deepcopy(repl[0]))
        elif tag == "add":
            if attr or op.get("type", "").startswith("@"):
                a = attr or op.get("type")[1:]
                value = (op.text or "").strip()
                for n in nodes:
                    n.set(a, value)
            else:
                for n in nodes:
                    for c in op:
                        if isinstance(c.tag, str):
                            n.append(deepcopy(c))
        elif tag == "remove":
            if attr:
                for n in nodes:
                    n.attrib.pop(attr, None)
            else:
                for n in nodes:
                    n.getparent().remove(n)
        else:
            errors.append(f"{label}: unknown diff op <{tag}>")
    return errors


# ------------------------------------------------------- mod-table parse

def _f(el, name, default=None):
    v = el.get(name)
    if v in (None, ""):
        return default
    try:
        return float(v)
    except ValueError:
        return default


def parse_engine_mods(root, names):
    """Engine-section mod entries of an (already patched) equipmentmods
    document; same forced-vs-pool rule as engines.extract_engine_mods."""
    engine = root.find("engine")
    if engine is None:
        raise SystemExit("patched document has no <engine> section")
    mods = []
    for el in engine:
        if not isinstance(el.tag, str):
            continue
        ware = el.get("ware") or ""
        if not ware.startswith("mod_engine_") or el.get("quality") is None:
            continue
        bonus = el.find("bonus")
        bonuses = []
        chance = _f(bonus, "chance", 0.0) if bonus is not None else 0.0
        bmax = int(_f(bonus, "max", 0) or 0) if bonus is not None else 0
        if bonus is not None:
            for b in bonus:
                if not isinstance(b.tag, str):
                    continue
                bonuses.append({"stat": b.tag, "min": _f(b, "min", 1.0),
                                "max": _f(b, "max", 1.0),
                                "weight": _f(b, "weight", 1.0)})
        forced = bool(bonuses) and chance >= 1.0 and len(bonuses) <= bmax
        mods.append({"ware": ware, "name": names.get(ware, ware),
                     "stat": el.tag,
                     "quality": int(_f(el, "quality", 1) or 1),
                     "min": _f(el, "min", 1.0), "max": _f(el, "max", 1.0),
                     "bonus_chance": chance, "bonus_max": bmax,
                     "forced": forced, "bonuses": bonuses})
    return mods


def canonical_engine(root):
    """Comparable form of an <engine> section (for the baseline check)."""
    rows = []
    engine = root.find("engine")
    for el in engine if engine is not None else []:
        if not isinstance(el.tag, str):
            continue
        bonus = el.find("bonus")
        brows = []
        if bonus is not None:
            brows = [(bonus.get("chance"), bonus.get("max"))] + [
                (b.tag, _f(b, "min"), _f(b, "max"), _f(b, "weight", 1.0))
                for b in bonus if isinstance(b.tag, str)]
        rows.append((el.tag, el.get("ware"), el.get("quality"),
                     _f(el, "min"), _f(el, "max"), tuple(brows)))
    return rows


# ------------------------------------------------------------ evaluation

def goodness_vector(mod, ship, engine, thruster, base):
    """modded/base ratio per EVAL stat, converted so higher is always better
    (time stats inverted). Ship-independent; ship just realizes the algebra."""
    mods = E.realized_mults(mod, "optimal")
    d = E.modded_stats(ship, engine, thruster, mods)
    out = {}
    for k, higher_better in EVAL_STATS.items():
        b = base[k] or 1.0
        r = (d[k] or b) / b
        out[k] = r if higher_better else (1.0 / r if r else 1.0)
    return out


def evaluate(mods, ship, engine, thruster):
    base = E.derive_stats(ship, engine, thruster)
    scored = [m for m in mods if _MK_WARE.search(m["ware"])]
    scenario = [m for m in mods if not _MK_WARE.search(m["ware"])]
    vecs = {m["ware"]: goodness_vector(m, ship, engine, thruster, base)
            for m in scored}

    # E1: RNG (any primary or bonus with min != max)
    rng = []
    for m in scored:
        if m["min"] != m["max"]:
            rng.append((m["ware"], "primary", m["min"], m["max"]))
        for b in m["bonuses"]:
            if b["min"] != b["max"]:
                rng.append((m["ware"], f"bonus {b['stat']}", b["min"], b["max"]))

    # E2: crossings + fake maluses
    crossings, fake = [], []
    for m in scored:
        ranges = [(m["stat"], m["min"], m["max"])] + [
            (b["stat"], b["min"], b["max"]) for b in m["bonuses"]]
        for stat, lo, hi in ranges:
            if lo < 1.0 < hi:
                crossings.append((m["ware"], stat, lo, hi))
        # forced malus that the net effect refunds to > 1.0. A malus is a
        # value < 1.0 on a thrust stat, but > 1.0 on a *time* stat (where
        # lower is faster/better), so detect by direction, not raw magnitude.
        if m["forced"]:
            for b in m["bonuses"]:
                is_time = b["stat"] in ("travelattacktime", "travelchargetime")
                worst = max(b["min"], b["max"]) if is_time else min(b["min"], b["max"])
                declared_malus = worst > 1.0 if is_time else worst < 1.0
                dstat = STAT_DERIVED.get(b["stat"])
                if declared_malus and dstat in vecs[m["ware"]]:
                    net = vecs[m["ware"]][dstat]
                    if net > 1.0 + EPS_INV:
                        fake.append((m["ware"], b["stat"], dstat, net))

    # E3: within a quality tier, no mod may be Pareto-dominated by another
    # (>= on every derived stat, > on one) nor be an exact duplicate of
    # another - either way it is a strictly redundant pick. `peaks` (which
    # derived stats each mod uniquely or jointly tops) is kept for the
    # informational specialists report only.
    dominated, duplicates = [], []
    peaks = {}
    for q in (1, 2, 3):
        tier = [m for m in scored if m["quality"] == q]
        if not tier:
            continue
        for k in EVAL_STATS:
            best = max(vecs[m["ware"]][k] for m in tier)
            if best <= 1.0 + EPS_TIE:      # nobody improves this stat: no peak
                continue
            for m in tier:
                if vecs[m["ware"]][k] >= best / (1 + EPS_TIE):
                    peaks.setdefault(m["ware"], set()).add(k)
        for a in tier:
            for b in tier:
                if a is b:
                    continue
                va, vb = vecs[a["ware"]], vecs[b["ware"]]
                ge = all(va[k] >= vb[k] - 1e-9 for k in EVAL_STATS)
                gt = any(va[k] > vb[k] + 1e-9 for k in EVAL_STATS)
                if ge and gt:
                    dominated.append((b, a))   # b dominated by a
        for i in range(len(tier)):
            for j in range(i + 1, len(tier)):
                a, b = tier[i], tier[j]
                if all(abs(vecs[a["ware"]][k] - vecs[b["ware"]][k]) < 1e-9
                       for k in EVAL_STATS):
                    duplicates.append((a, b))

    # E4: tier inversion within a variant (primary + forced signature)
    def variant(m):
        sig = frozenset((b["stat"], round(min(b["min"], b["max"]), 3))
                        for b in m["bonuses"] if m["forced"])
        primary = None if (m["min"] == 1.0 == m["max"]) else m["stat"]
        return (primary, sig)

    inversions = []
    for a in scored:
        for b in scored:
            if variant(a) != variant(b) or a["quality"] >= b["quality"]:
                continue
            dstat = STAT_DERIVED.get(a["stat"])
            if dstat is None:
                continue
            va, vb = vecs[a["ware"]][dstat], vecs[b["ware"]][dstat]
            if vb and va / vb - 1 > EPS_INV:
                inversions.append((a, b, va / vb - 1, dstat))

    return {"scored": scored, "scenario": scenario, "vecs": vecs,
            "peaks": peaks, "rng": rng, "crossings": crossings, "fake": fake,
            "dominated": dominated, "duplicates": duplicates,
            "inversions": inversions}


def report(r, judge):
    qn = {1: "Basic", 2: "Enhanced", 3: "Exceptional"}
    print(f"  {len(r['scored'])} mods scored, {len(r['scenario'])} scenario "
          f"mods excluded")
    hdr = "  {:<30}{:<12}{:<16}peaks".format("mod", "qual", "primary")
    print(hdr)
    for m in sorted(r["scored"], key=lambda m: (m["quality"], m["stat"], m["ware"])):
        pk = ",".join(sorted(k.replace("_", "") for k in r["peaks"].get(m["ware"], ())))
        rng = f"x{m['min']}-{m['max']}" if m["min"] != m["max"] else f"x{m['min']}"
        print(f"  {m['name'][:20] + ' (' + m['stat'][:10] + ')':<30}"
              f"{qn[m['quality']]:<12}{rng:<16}{pk or '(none)'}")

    # Detail lines are only printed when judging our diff; the vanilla
    # reference run (judge=False) would otherwise spew ~90 known RNG lines.
    failures = []
    if r["rng"]:
        failures.append("E1 RNG")
        if judge:
            for ware, what, lo, hi in r["rng"]:
                print(f"  E1 FAIL: {ware} {what} range x{lo}-{hi} is RNG")
    if r["crossings"] or r["fake"]:
        failures.append("E2 honesty")
        if judge:
            for ware, stat, lo, hi in r["crossings"]:
                print(f"  E2 FAIL: {ware} {stat} range x{lo}-{hi} crosses 1.0")
            for ware, stat, dstat, net in r["fake"]:
                print(f"  E2 FAIL: {ware} declares a {stat} malus but net "
                      f"{dstat} = x{net:.3f} > 1.0 (forward-thrust leak refunds it)")
    if r["dominated"] or r["duplicates"]:
        failures.append("E3 redundancy")
        if judge:
            for b, a in r["dominated"]:
                print(f"  E3 FAIL: {b['name']} ({b['ware']}) Pareto-dominated "
                      f"by {a['name']} ({a['ware']}) within quality {b['quality']}")
            for a, b in r["duplicates"]:
                print(f"  E3 FAIL: {a['name']} ({a['ware']}) and {b['name']} "
                      f"({b['ware']}) are identical within quality {a['quality']}")
    if r["inversions"]:
        failures.append("E4 tier order")
        if judge:
            for a, b, v, dstat in r["inversions"]:
                print(f"  E4 FAIL: {a['name']} (q{a['quality']}) beats "
                      f"{b['name']} (q{b['quality']}) by {v:+.1%} on {dstat}")

    if judge:
        print("  => " + ("all acceptance targets pass" if not failures
                         else f"FAILED: {', '.join(failures)}"))
    elif failures:
        print(f"  (vanilla fails, as expected: {', '.join(failures)})")
    return failures


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game-dir", default=DEFAULT_GAME_DIR, type=Path)
    ap.add_argument("--diff", default=DEFAULT_DIFF, type=Path)
    ap.add_argument("--vanilla-only", action="store_true")
    args = ap.parse_args()

    print(f"Indexing game catalogs: {args.game_dir}")
    gf = GameFiles(args.game_dir)   # official DLC only, by design
    tdb = load_textdb(gf)
    names = E._mod_ware_names(gf, tdb)
    ships = E.extract_ships(gf, tdb)
    eng = E.extract_engines(gf, tdb)
    thr = E.extract_thrusters(gf)
    # representative ship+engine+thruster (any works; ratios are ship-independent)
    ship = next(s for s in ships if s["macro"] == "ship_arg_s_fighter_01_a_macro")
    engine = E.representative_engine(eng, "s", "allround", 1)
    thruster = thr["s"]

    base = etree.fromstring(gf.read_bytes("libraries/equipmentmods.xml"), _PARSER)
    ref = etree.parse(str(REFERENCE), _PARSER).getroot()
    if canonical_engine(base) != canonical_engine(ref):
        print("BASELINE MISMATCH: game <engine> section != reference "
              f"{REFERENCE} - stop and ask before trusting numbers.")
        got, want = canonical_engine(base), canonical_engine(ref)
        for g in got:
            if g not in want:
                print(f"  game has:      {g[:4]}")
        for w in want:
            if w not in got:
                print(f"  reference has: {w[:4]}")
        return 2

    merged = base
    for ext in gf.extensions:
        path = f"extensions/{ext}/libraries/equipmentmods.xml"
        if path in gf:
            errs = apply_diff(merged, etree.fromstring(gf.read_bytes(path),
                                                       _PARSER), ext)
            for e in errs:
                print(f"  warning (DLC diff): {e}")

    print("\n=== VANILLA scorecard (reference, not judged) ===")
    report(evaluate(parse_engine_mods(merged, names), ship, engine, thruster),
           judge=False)

    if args.vanilla_only:
        return 0

    patched = deepcopy(merged)
    our_diff = etree.parse(str(args.diff), _PARSER).getroot()
    n_ops = sum(1 for op in our_diff if isinstance(op.tag, str))
    errs = apply_diff(patched, our_diff, args.diff.name)
    if errs:
        print(f"\nDIFF ERRORS ({args.diff}):")
        for e in errs:
            print(f"  {e}")
        return 2
    print(f"\n=== MODDED scorecard ({args.diff.name}: {n_ops} ops, "
          "all sels matched) ===")
    failures = report(evaluate(parse_engine_mods(patched, names),
                               ship, engine, thruster), judge=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
