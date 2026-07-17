#!/usr/bin/env python
"""Evaluation harness for the shield-mod-rebalance extension.

Run from the repo root with the x4-analyzer environment:

    uv run --project ~/devel/x4-analyzer python tools/shield-mod-rebalance/evaluate.py

Mirrors the engine harness, simpler: shields have three levers (capacity,
rechargerate, rechargedelay) and no forward-thrust-style leak, so there are no
maluses and no degenerate "parked" mods - all 8 mods are real archetypes. A
mod's effect vector is just its multipliers (shield-independent), so E3/E4 are
computed directly from them; the capacity/refill trade-off is physical and
reported for information, not a data malus.

Acceptance targets (see docs/shield-mod-rebalance-design.md):

  E1 no RNG       every mod pins min == max on its primary and forced bonuses.
  E2 no crossing  no roll range crosses 1.0.
  E3 no redundancy  within a quality tier, no mod is Pareto-dominated by or
                  identical to another (on capacity / rate / delay-goodness) -
                  each archetype owns a distinct corner.
  E4 tier order   no lower-quality mod beats a higher-quality mod of the same
                  variant (primary stat + forced-rider stat set) on its
                  primary stat.

Scenario/uncraftable shield mods (wares not ending in _mk<n>), if any, are
excluded from the targets.
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
from x4analyzer.gamedata import shields as S

REPO = Path(__file__).resolve().parents[2]
DEFAULT_GAME_DIR = "/games/SteamLibrary/steamapps/common/X4 Foundations"
DEFAULT_DIFF = REPO / "shield-mod-rebalance" / "libraries" / "equipmentmods.xml"
REFERENCE = REPO / "docs" / "reference" / "equipmentmods-vanilla-v9.xml"

_PARSER = etree.XMLParser(recover=True, huge_tree=True)
_MK_WARE = re.compile(r"_mk\d$")
EPS_TIE = 0.005
EPS_INV = 0.01

# derived stat -> higher_is_better. rechargedelay is a time (lower better) but
# realized_mults already yields the raw multiplier; goodness_vector inverts it.
EVAL_STATS = {"capacity": True, "rechargerate": True, "rechargedelay": False}


# --------------------------------------------------------------- patching
# (identical XPath <diff> applier to the weapon/engine harnesses)

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
                for n in nodes:
                    n.set(attr, (op.text or "").strip())
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
                for n in nodes:
                    n.set(a, (op.text or "").strip())
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


def parse_shield_mods(root, names):
    sec = root.find("shield")
    if sec is None:
        raise SystemExit("patched document has no <shield> section")
    mods = []
    for el in sec:
        if not isinstance(el.tag, str):
            continue
        ware = el.get("ware") or ""
        if not ware.startswith("mod_shield_") or el.get("quality") is None:
            continue
        bonus = el.find("bonus")
        bonuses = []
        chance = _f(bonus, "chance", 0.0) if bonus is not None else 0.0
        bmax = int(_f(bonus, "max", 0) or 0) if bonus is not None else 0
        if bonus is not None:
            for b in bonus:
                if isinstance(b.tag, str):
                    bonuses.append({"stat": b.tag, "min": _f(b, "min", 1.0),
                                    "max": _f(b, "max", 1.0)})
        forced = bool(bonuses) and chance >= 1.0 and len(bonuses) <= bmax
        mods.append({"ware": ware, "name": names.get(ware, ware), "stat": el.tag,
                     "quality": int(_f(el, "quality", 1) or 1),
                     "min": _f(el, "min", 1.0), "max": _f(el, "max", 1.0),
                     "forced": forced, "bonuses": bonuses})
    return mods


def canonical_shield(root):
    rows = []
    sec = root.find("shield")
    for el in sec if sec is not None else []:
        if not isinstance(el.tag, str):
            continue
        bonus = el.find("bonus")
        brows = []
        if bonus is not None:
            brows = [(bonus.get("chance"), bonus.get("max"))] + [
                (b.tag, _f(b, "min"), _f(b, "max")) for b in bonus
                if isinstance(b.tag, str)]
        rows.append((el.tag, el.get("ware"), el.get("quality"),
                     _f(el, "min"), _f(el, "max"), tuple(brows)))
    return rows


# ------------------------------------------------------------ evaluation

def goodness_vector(mod):
    """capacity / rate / delay as 'higher = better' multipliers (delay
    inverted). Shield-independent."""
    mults = S.realized_mults(mod, "optimal")
    out = {}
    for k, hb in EVAL_STATS.items():
        m = mults.get(k, 1.0)
        out[k] = m if hb else (1.0 / m if m else 1.0)
    return out


def evaluate(mods):
    scored = [m for m in mods if _MK_WARE.search(m["ware"])]
    scenario = [m for m in mods if not _MK_WARE.search(m["ware"])]
    vecs = {m["ware"]: goodness_vector(m) for m in scored}

    # E1 RNG
    rng = []
    for m in scored:
        if m["min"] != m["max"]:
            rng.append((m["ware"], "primary", m["min"], m["max"]))
        for b in m["bonuses"]:
            if b["min"] != b["max"]:
                rng.append((m["ware"], f"bonus {b['stat']}", b["min"], b["max"]))

    # E2 crossings
    crossings = []
    for m in scored:
        for stat, lo, hi in [(m["stat"], m["min"], m["max"])] + [
                (b["stat"], b["min"], b["max"]) for b in m["bonuses"]]:
            if lo < 1.0 < hi:
                crossings.append((m["ware"], stat, lo, hi))

    # E3 Pareto domination / duplication within a tier
    dominated, duplicates = [], []
    for q in (1, 2, 3):
        tier = [m for m in scored if m["quality"] == q]
        for a in tier:
            for b in tier:
                if a is b:
                    continue
                va, vb = vecs[a["ware"]], vecs[b["ware"]]
                ge = all(va[k] >= vb[k] - 1e-9 for k in EVAL_STATS)
                gt = any(va[k] > vb[k] + 1e-9 for k in EVAL_STATS)
                if ge and gt:
                    dominated.append((b, a))
        for i in range(len(tier)):
            for j in range(i + 1, len(tier)):
                a, b = tier[i], tier[j]
                if all(abs(vecs[a["ware"]][k] - vecs[b["ware"]][k]) < 1e-9
                       for k in EVAL_STATS):
                    duplicates.append((a, b))

    # E4 tier inversion within a variant (primary + forced-rider stat set)
    def variant(m):
        sig = frozenset(b["stat"] for b in m["bonuses"]
                        if m["forced"] and not (b["min"] == 1.0 == b["max"]))
        primary = None if (m["min"] == 1.0 == m["max"]) else m["stat"]
        return (primary, sig)

    inversions = []
    for a in scored:
        for b in scored:
            if variant(a) != variant(b) or a["quality"] >= b["quality"]:
                continue
            va, vb = vecs[a["ware"]][a["stat"]], vecs[b["ware"]][b["stat"]]
            if vb and va / vb - 1 > EPS_INV:
                inversions.append((a, b, va / vb - 1, a["stat"]))

    return {"scored": scored, "scenario": scenario, "vecs": vecs, "rng": rng,
            "crossings": crossings, "dominated": dominated,
            "duplicates": duplicates, "inversions": inversions}


def report(r, judge):
    qn = {1: "Basic", 2: "Enhanced", 3: "Exceptional"}
    print(f"  {len(r['scored'])} mods scored, {len(r['scenario'])} scenario excluded")
    print("  {:<26}{:<12}{}".format("mod", "qual", "capacity / rate / delay"))
    for m in sorted(r["scored"], key=lambda m: (m["quality"], m["stat"], m["ware"])):
        v = r["vecs"][m["ware"]]
        print(f"  {m['name'][:16] + ' (' + m['stat'][:12] + ')':<26}{qn[m['quality']]:<12}"
              f"cap {v['capacity']:.3f}  rate {v['rechargerate']:.3f}  "
              f"delay {v['rechargedelay']:.3f}")

    failures = []
    if r["rng"]:
        failures.append("E1 RNG")
        if judge:
            for ware, what, lo, hi in r["rng"]:
                print(f"  E1 FAIL: {ware} {what} range x{lo}-{hi} is RNG")
    if r["crossings"]:
        failures.append("E2 crossing")
        if judge:
            for ware, stat, lo, hi in r["crossings"]:
                print(f"  E2 FAIL: {ware} {stat} range x{lo}-{hi} crosses 1.0")
    if r["dominated"] or r["duplicates"]:
        failures.append("E3 redundancy")
        if judge:
            for b, a in r["dominated"]:
                print(f"  E3 FAIL: {b['name']} ({b['ware']}) Pareto-dominated by "
                      f"{a['name']} ({a['ware']}) in quality {b['quality']}")
            for a, b in r["duplicates"]:
                print(f"  E3 FAIL: {a['name']} and {b['name']} identical in "
                      f"quality {a['quality']}")
    if r["inversions"]:
        failures.append("E4 tier order")
        if judge:
            for a, b, v, stat in r["inversions"]:
                print(f"  E4 FAIL: {a['name']} (q{a['quality']}) beats {b['name']} "
                      f"(q{b['quality']}) by {v:+.1%} on {stat}")

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
    gf = GameFiles(args.game_dir)
    tdb = load_textdb(gf)
    names = S._mod_ware_names(gf, tdb)

    base = etree.fromstring(gf.read_bytes("libraries/equipmentmods.xml"), _PARSER)
    ref = etree.parse(str(REFERENCE), _PARSER).getroot()
    if canonical_shield(base) != canonical_shield(ref):
        print(f"BASELINE MISMATCH: game <shield> section != {REFERENCE}")
        for g in canonical_shield(base):
            if g not in canonical_shield(ref):
                print(f"  game has:      {g[:4]}")
        for w in canonical_shield(ref):
            if w not in canonical_shield(base):
                print(f"  reference has: {w[:4]}")
        return 2

    merged = base
    for ext in gf.extensions:
        path = f"extensions/{ext}/libraries/equipmentmods.xml"
        if path in gf:
            for e in apply_diff(merged, etree.fromstring(gf.read_bytes(path), _PARSER), ext):
                print(f"  warning (DLC diff): {e}")

    print("\n=== VANILLA scorecard (reference, not judged) ===")
    report(evaluate(parse_shield_mods(merged, names)), judge=False)

    if args.vanilla_only:
        return 0

    patched = deepcopy(merged)
    # STRICT well-formedness check (the game's libxml2 rejects e.g. "--" in a
    # comment and SKIPS the whole file; recover=True would silently tolerate it).
    try:
        etree.parse(str(args.diff), etree.XMLParser(recover=False))
    except etree.XMLSyntaxError as e:
        print(f"\nDIFF NOT WELL-FORMED - the game will skip it: {e}")
        return 2
    our_diff = etree.parse(str(args.diff), _PARSER).getroot()
    n_ops = sum(1 for op in our_diff if isinstance(op.tag, str))
    errs = apply_diff(patched, our_diff, args.diff.name)
    if errs:
        print(f"\nDIFF ERRORS ({args.diff}):")
        for e in errs:
            print(f"  {e}")
        return 2
    print(f"\n=== MODDED scorecard ({args.diff.name}: {n_ops} ops, all sels matched) ===")
    failures = report(evaluate(parse_shield_mods(patched, names)), judge=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
