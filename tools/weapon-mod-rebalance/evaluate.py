#!/usr/bin/env python
"""Evaluation harness for the weapon-mod-rebalance extension.

Run from the repo root with the x4-analyzer environment:

    uv run --project ~/devel/x4-analyzer python tools/weapon-mod-rebalance/evaluate.py

What it does:

1. Loads the vanilla merged libraries/equipmentmods.xml through GameFiles
   (base game + official DLC only) and verifies the base-game weapon
   section against docs/reference/equipmentmods-vanilla-v9.xml. Any
   mismatch aborts with exit code 2 (stop and ask before proceeding).
2. Applies our extension's diff file ITSELF with an lxml XPath patcher
   supporting <replace>/<add>/<remove> sel, including attribute replaces.
   This is deliberate: x4analyzer.gamedata.weapons.extract_weapon_mods
   only collects `ware=`-bearing elements, so it silently ignores
   <replace sel=".../@attr"> patches - parsing the extension file naively
   would miss every attribute change. An unmatched sel is a hard error
   (exit 2), which doubles as the "diff applies cleanly" proof.
3. Re-parses the patched document with the same forced-vs-pool bonus rules
   x4analyzer uses, simulates all weapons x mods at optimal rolls via
   x4analyzer.gamedata.weaponsim, and reports per-mod best-in-cycle-DPS
   win rates, tier inversions, and the max cycle-DPS worth of any
   secondary bundle.
4. Exits nonzero (1) if any acceptance target fails, printing which.

Acceptance targets (docs/weapon-mod-rebalance-design.md), made mechanical:

  T1 dominance    no single mod is best-or-tied WITHIN ITS OWN quality tier
                  on more than 85% of its eligible weapons. Cross-tier
                  dominance by higher tiers is the intended research ladder
                  (Exceptional should be the best you can craft), so this
                  only flags a near-monopoly inside a tier - one mod that
                  leaves no real intra-tier choice (the vanilla-Slasher
                  disease). T2 separately guarantees each mod wins somewhere.
  T2 usefulness   every mod whose PRIMARY stat trades in DPS (damage,
                  cooling, reload, chargetime) is best-or-tied (within
                  0.5%) among the DPS-affecting mods of ITS OWN quality
                  tier on at least one weapon. (Cross-tier "best pick" is
                  meaningless once damage primaries are pinned
                  monotonically per tier; tiers are price/rarity points,
                  so "best pick" = best among what you can afford.) Mods
                  with an orthogonal primary (speed, lifetime, sticktime,
                  surfaceelement, mining, ...) are the best pick for
                  their own stat by definition and exempt.
  T3 bundles      REMOVED. Under the combination design a mod's secondaries
                  ARE its stated identity (Mistral = cooling + reload; the
                  Exceptional capstones are deliberately rich forced sets),
                  so there is no secondary-bundle cap. The scorecard still
                  prints the worst-case bundle worth for information only.
  T4 tier order   no lower-quality mod beats a higher-quality mod of the
                  SAME VARIANT (same primary stat and same set of
                  DPS-carrying guaranteed secondaries, neutral x1.0 slots
                  ignored) by >1% on any weapon, at optimal rolls. Cross-
                  variant comparisons are deliberately unchecked - e.g. a
                  Basic cooling+damage mix "beats" a pure Enhanced cooling
                  mod on a heatless weapon, where both are the wrong tool
                  (the damage mods dominate there anyway).
  T5 no flips     no roll range (primary or bonus) crosses 1.0.

Timelines scenario mods (wares not ending in _mk<n>, e.g.
mod_weapon_damage_fleet_battle_1) are availability-gated, uncraftable and
untouched by this rebalance; they are excluded from the targets but kept
in the informational listing.

Mining weapons/turrets (name or macro containing mining/drill) only count
for mods whose primary or bonuses include the mining stat - nobody
installs combat mods on mining lasers, and as reload-time weapons they
would otherwise distort every combat mod's niche numbers.

Cycle-DPS metric = full-cycle DPS (cyc_dps_*) where the weapon has a heat
or clip cycle, else steady-state DPS (ss_dps_*); both the vs-shield and
vs-hull channels are checked everywhere.
"""

from __future__ import annotations

import argparse
import re
import sys
from copy import deepcopy
from itertools import combinations
from pathlib import Path

from lxml import etree

from x4analyzer.gamedata.catalog import GameFiles
from x4analyzer.gamedata.extract import load_textdb
from x4analyzer.gamedata.weapons import _mod_ware_names, extract_weapons
from x4analyzer.gamedata.weaponsim import (SIM_STATS, guaranteed_stats,
                                           mod_multipliers, optimal_mult,
                                           reload_kind, simulate)

REPO = Path(__file__).resolve().parents[2]
DEFAULT_GAME_DIR = "/games/SteamLibrary/steamapps/common/X4 Foundations"
DEFAULT_DIFF = REPO / "weapon-mod-rebalance" / "libraries" / "equipmentmods.xml"
REFERENCE = REPO / "docs" / "reference" / "equipmentmods-vanilla-v9.xml"

_PARSER = etree.XMLParser(recover=True, huge_tree=True)
_MK_WARE = re.compile(r"_mk\d$")

EPS_TIE = 0.005     # within 0.5% = tied / best pick
EPS_INV = 0.01      # >1% = tier inversion
T1_MAX_TIER_DOMINANCE = 0.85   # within-tier best-or-tied share above this = monopoly


# --------------------------------------------------------------- patching

def apply_diff(root: etree._Element, diff_root: etree._Element,
               label: str) -> list[str]:
    """Apply an X4 <diff> (replace/add/remove, incl. /@attr sels) in place.
    Returns a list of error strings (unmatched sels, malformed ops)."""
    errors: list[str] = []
    for op in diff_root:
        if not isinstance(op.tag, str):
            continue  # comments
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
                    errors.append(f"{label}: <replace> of a node needs exactly"
                                  f" one child element: {sel}")
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
                    if attr in n.attrib:
                        del n.attrib[attr]
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


def parse_weapon_mods(root: etree._Element,
                      names: dict[str, str]) -> list[dict]:
    """Weapon-section mod entries of an (already patched) equipmentmods
    document, using the same forced-vs-pool rule as
    x4analyzer.gamedata.weapons.extract_weapon_mods: a <bonus chance="1.0"
    max="N"> block with <= N children is FORCED, a larger weighted pool is
    optional loot."""
    mods = []
    weapon = root.find("weapon")
    if weapon is None:
        raise SystemExit("patched document has no <weapon> section")
    for el in weapon:
        if not isinstance(el.tag, str):
            continue
        ware = el.get("ware") or ""
        if not ware.startswith("mod_weapon_") or el.get("quality") is None:
            continue
        bonus = el.find("bonus")
        bonuses = []
        chance = _f(bonus, "chance", 0.0) if bonus is not None else 0.0
        bmax = int(_f(bonus, "max", 0) or 0) if bonus is not None else 0
        if bonus is not None:
            for b in bonus:
                if not isinstance(b.tag, str):
                    continue
                bonuses.append({"stat": b.tag,
                                "min": _f(b, "min", 1.0),
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


def canonical(root: etree._Element) -> list[tuple]:
    """Comparable form of a weapon section (for the baseline check)."""
    rows = []
    weapon = root.find("weapon")
    for el in weapon if weapon is not None else []:
        if not isinstance(el.tag, str):
            continue
        bonus = el.find("bonus")
        brows = []
        if bonus is not None:
            brows = [(b.tag, _f(b, "min"), _f(b, "max"), _f(b, "weight", 1.0))
                     for b in bonus if isinstance(b.tag, str)]
            brows = [(bonus.get("chance"), bonus.get("max"))] + brows
        rows.append((el.tag, el.get("ware"), el.get("quality"),
                     _f(el, "min"), _f(el, "max"), tuple(brows)))
    return rows


_MINING_RX = re.compile(r"mining|drill", re.I)


def is_mining_weapon(w: dict) -> bool:
    return bool(_MINING_RX.search(w["name"]) or _MINING_RX.search(w["macro"]))


def serves_mining(mod: dict) -> bool:
    return mod["stat"] == "mining" or any(b["stat"] == "mining"
                                          for b in mod["bonuses"])


def eligible_pair(mod: dict, weapon: dict) -> bool:
    """Mining weapons only count for mods that can roll a mining bonus."""
    return not is_mining_weapon(weapon) or serves_mining(mod)


# ------------------------------------------------------------ simulation

def cycle_dps(weapon: dict, mults: dict[str, float] | None) -> tuple:
    """(vs-shield, vs-hull) full-cycle DPS; steady-state when the weapon
    has no heat/clip cycle. None if the weapon has no sustained DPS."""
    s = simulate(weapon, mults)
    vs = s["cyc_dps_s"] if s["cyc_dps_s"] is not None else s["ss_dps_s"]
    vh = s["cyc_dps_h"] if s["cyc_dps_h"] is not None else s["ss_dps_h"]
    return vs, vh


def bundle_worth(mod: dict, weapon: dict) -> float:
    """Worst-case cycle-DPS worth (fractional gain) of the mod's secondary
    bundle on this weapon: forced bonuses all together, optional pools at
    the DPS-best subset of up to bonus_max picks, all at optimal rolls."""
    rkind = reload_kind(weapon)
    primary = {mod["stat"]: optimal_mult(mod["stat"], mod["min"], mod["max"],
                                         rkind)}
    b_s, b_h = cycle_dps(weapon, primary)
    if not b_s and not b_h:
        return 0.0
    # only bonuses touching simulated stats can move the metric
    simbon = [b for b in mod["bonuses"] if b["stat"] in SIM_STATS]
    if not simbon:
        return 0.0
    if mod["forced"]:
        subsets = [simbon]
    else:
        k = min(mod["bonus_max"], len(simbon))
        subsets = [list(c) for n in range(1, k + 1)
                   for c in combinations(simbon, n)]
    worst = 0.0
    for subset in subsets:
        mults = dict(primary)
        for b in subset:
            m = optimal_mult(b["stat"], b["min"], b["max"], rkind)
            mults[b["stat"]] = mults.get(b["stat"], 1.0) * m
        v_s, v_h = cycle_dps(weapon, mults)
        for v, base in ((v_s, b_s), (v_h, b_h)):
            if v and base:
                worst = max(worst, v / base - 1.0)
    return worst


# ------------------------------------------------------------ evaluation

def evaluate(mods: list[dict], weapons: list[dict]) -> dict:
    """Simulate everything, compute the target numbers. Returns a dict of
    results; see report() for how they are judged."""
    scored = [m for m in mods if _MK_WARE.search(m["ware"])]
    scenario = [m for m in mods if not _MK_WARE.search(m["ware"])]
    sim_mods = [m for m in scored
                if set(guaranteed_stats(m)) & set(SIM_STATS)]

    eligible = []
    for w in weapons:
        vs, vh = cycle_dps(w, None)
        if vs and vs > 0:
            eligible.append(w)

    # guaranteed-effect cycle DPS for every scored mod on every weapon;
    # None = pair not eligible (combat mod on a mining weapon)
    table: dict[str, list[tuple | None]] = {m["ware"]: [] for m in scored}
    for w in eligible:
        for m in scored:
            table[m["ware"]].append(
                cycle_dps(w, mod_multipliers(m, w))
                if eligible_pair(m, w) else None)

    n = len(eligible)
    n_el = {m["ware"]: sum(1 for e in table[m["ware"]] if e is not None)
            for m in scored}
    strict_wins = {m["ware"]: 0 for m in sim_mods}
    best_picks = {m["ware"]: 0 for m in sim_mods}
    tier_best_somewhere = {m["ware"]: False for m in sim_mods}
    tier_best_count = {m["ware"]: 0 for m in sim_mods}  # within-tier best-or-tied
    for i in range(n):
        contestants = [m for m in sim_mods if table[m["ware"]][i] is not None]
        for ch in (0, 1):
            vals = sorted(((table[m["ware"]][i][ch] or 0.0, m["ware"])
                           for m in contestants), reverse=True)
            if not vals:
                continue
            top, ware = vals[0]
            if top <= 0:
                continue
            second = vals[1][0] if len(vals) > 1 else 0.0
            if ch == 0:  # win rates counted on the vs-shield channel
                if top > second * (1 + EPS_TIE):
                    strict_wins[ware] += 1
                for v, wr in vals:
                    if v >= top / (1 + EPS_TIE):
                        best_picks[wr] += 1
        # per-tier best picks (either channel)
        for q in (1, 2, 3):
            tier = [m for m in contestants if m["quality"] == q]
            tb_here: set[str] = set()  # mods best-or-tied within tier q on this weapon
            for ch in (0, 1):
                best = max((table[m["ware"]][i][ch] or 0.0 for m in tier),
                           default=0.0)
                if best <= 0:
                    continue
                for m in tier:
                    if (table[m["ware"]][i][ch] or 0.0) >= best / (1 + EPS_TIE):
                        tier_best_somewhere[m["ware"]] = True
                        tb_here.add(m["ware"])
            for ware in tb_here:
                tier_best_count[ware] += 1

    # T3: worst secondary bundle
    bundles = []
    for m in scored:
        worst, worst_w = 0.0, None
        for w in eligible:
            if not eligible_pair(m, w):
                continue
            v = bundle_worth(m, w)
            if v > worst:
                worst, worst_w = v, w
        bundles.append((worst, m, worst_w))

    # T4: tier inversions between same-VARIANT mods (same primary stat and
    # same DPS-carrying guaranteed-secondary set; neutral 1.0 slots and
    # optional pools do not define a variant). A primary stat pinned to x1.0
    # is a REPURPOSED container (e.g. Kuril = cooling pinned 1.0 + a forced
    # reload child = really a reload mod), so it is dropped from the variant
    # key - otherwise it would false-match the real cooling+reload mods and
    # invert on heat weapons where their cooling helps and its does not.
    def variant(m):
        dps_bonuses = frozenset(
            b["stat"] for b in m["bonuses"]
            if m["forced"] and b["stat"] in SIM_STATS
            and not (b["min"] == 1.0 and b["max"] == 1.0))
        primary = None if (m["min"] == 1.0 and m["max"] == 1.0) else m["stat"]
        return (primary, dps_bonuses)

    inversions = []
    for a in scored:
        for b in scored:
            if variant(a) != variant(b) or a["quality"] >= b["quality"]:
                continue
            worst, worst_w = 0.0, None
            for i, w in enumerate(eligible):
                ea, eb = table[a["ware"]][i], table[b["ware"]][i]
                if ea is None or eb is None:
                    continue
                for ch in (0, 1):
                    va, vb = ea[ch], eb[ch]
                    if va and vb and va / vb - 1 > worst:
                        worst, worst_w = va / vb - 1, w
            if worst > EPS_INV:
                inversions.append((a, b, worst, worst_w))

    # T5: ranges crossing 1.0
    crossings = []
    for m in scored:
        if m["min"] < 1.0 < m["max"]:
            crossings.append((m["ware"], m["stat"], m["min"], m["max"]))
        for b in m["bonuses"]:
            if b["min"] < 1.0 < b["max"]:
                crossings.append((m["ware"], f"bonus {b['stat']}",
                                  b["min"], b["max"]))

    return {"n_weapons": len(weapons), "n_eligible": n, "n_el": n_el,
            "scored": scored, "scenario": scenario, "sim_mods": sim_mods,
            "strict_wins": strict_wins, "best_picks": best_picks,
            "tier_best": tier_best_somewhere, "tier_best_count": tier_best_count,
            "bundles": bundles,
            "inversions": inversions, "crossings": crossings}


def report(r: dict, judge: bool) -> list[str]:
    """Print the scorecard; return the list of failed targets (empty if
    all pass). judge=False prints without judging (vanilla reference)."""
    n = r["n_eligible"]
    print(f"  {r['n_weapons']} weapons/turrets, {n} with sustained DPS; "
          f"{len(r['scored'])} mods scored ({len(r['sim_mods'])} affect the "
          f"firing cycle), {len(r['scenario'])} scenario mods excluded")
    qn = {1: "Basic", 2: "Enhanced", 3: "Exceptional"}
    print(f"  {'mod':<34}{'qual':<12}{'primary':<20}"
          f"{'win%':>6}{'pick%':>7}{'tierdom%':>9}  tier-best")
    for m in sorted(r["sim_mods"], key=lambda m: (m["quality"], m["ware"])):
        ne = max(r["n_el"][m["ware"]], 1)
        w = r["strict_wins"][m["ware"]] / ne * 100
        p = r["best_picks"][m["ware"]] / ne * 100
        td = r["tier_best_count"][m["ware"]] / ne * 100
        tb = "yes" if r["tier_best"][m["ware"]] else "NO"
        print(f"  {m['name'][:22] + ' (' + m['stat'] + ')':<34}"
              f"{qn[m['quality']]:<12}"
              f"{'x' + str(m['min']) + '-' + str(m['max']):<20}"
              f"{w:>5.1f}{p:>7.1f}{td:>8.1f}  {tb}")

    failures = []

    # T1: within-tier dominance. Cross-tier dominance by higher tiers is the
    # INTENDED research ladder (Exceptional should be the best you can craft),
    # so T1 only flags a near-monopoly WITHIN a quality tier - one mod
    # best-or-tied on almost every weapon, leaving no real intra-tier choice
    # (the vanilla-Slasher disease). T2 separately guarantees every mod is the
    # best pick somewhere.
    over = [(m, r["tier_best_count"][m["ware"]] / max(r["n_el"][m["ware"]], 1))
            for m in r["sim_mods"]]
    over = [(m, rate) for m, rate in over if rate > T1_MAX_TIER_DOMINANCE]
    for m, rate in over:
        print(f"  T1 FAIL: {m['name']} ({m['ware']}) best-or-tied within "
              f"quality {m['quality']} on {rate:.0%} of its eligible weapons "
              f"(> {T1_MAX_TIER_DOMINANCE:.0%} = intra-tier monopoly)")
    if over:
        failures.append("T1 within-tier dominance")

    useless = [m for m in r["sim_mods"] if not r["tier_best"][m["ware"]]
               and m["stat"] in SIM_STATS
               and not (m["min"] == 1.0 and m["max"] == 1.0)]
    for m in useless:
        print(f"  T2 FAIL: {m['name']} ({m['ware']}) is never best-or-tied "
              f"within quality {m['quality']} on any weapon")
    if useless:
        failures.append("T2 usefulness")

    # T3 removed: under the combination design a mod's secondaries ARE its
    # identity (Mistral = cooling+reload, the q3 capstones are rich forced
    # sets by design), so there is no cap - the line below is informational.
    worst_b, worst_m, worst_w = max(r["bundles"], key=lambda x: x[0])
    print(f"  max secondary-bundle worth: {worst_b:+.1%} cycle DPS "
          f"({worst_m['name']} [{worst_m['ware']}] on "
          f"{worst_w['name'] if worst_w else '-'}) [informational, uncapped]")

    for a, b, v, w in r["inversions"]:
        print(f"  T4 FAIL: {a['name']} (q{a['quality']}) beats {b['name']} "
              f"(q{b['quality']}) by {v:+.1%} on {w['name']} "
              f"[{a['ware']} > {b['ware']}]")
    if r["inversions"]:
        failures.append("T4 tier inversion")

    for ware, stat, lo, hi in r["crossings"]:
        print(f"  T5 FAIL: {ware} {stat} range x{lo}-{hi} crosses 1.0")
    if r["crossings"]:
        failures.append("T5 range crosses 1.0")

    if judge:
        if failures:
            print(f"  => FAILED: {', '.join(failures)}")
        else:
            print("  => all acceptance targets pass")
    return failures


# ------------------------------------------------------------------ main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game-dir", default=DEFAULT_GAME_DIR, type=Path)
    ap.add_argument("--diff", default=DEFAULT_DIFF, type=Path,
                    help="extension diff to evaluate")
    ap.add_argument("--vanilla-only", action="store_true",
                    help="only print the vanilla scorecard (no judgement)")
    args = ap.parse_args()

    print(f"Indexing game catalogs: {args.game_dir}")
    gf = GameFiles(args.game_dir)   # official DLC only, by design
    tdb = load_textdb(gf)
    names = _mod_ware_names(gf, tdb)
    weapons = extract_weapons(gf, tdb)

    base = etree.fromstring(gf.read_bytes("libraries/equipmentmods.xml"),
                            _PARSER)

    # baseline check: base-game weapon section vs the checked-in reference
    ref = etree.parse(str(REFERENCE), _PARSER).getroot()
    if canonical(base) != canonical(ref):
        got, want = canonical(base), canonical(ref)
        print("BASELINE MISMATCH between the game's equipmentmods.xml and")
        print(f"{REFERENCE} - stop and ask before trusting any numbers.")
        for g in got:
            if g not in want:
                print(f"  game has:      {g[:5]}")
        for w_ in want:
            if w_ not in got:
                print(f"  reference has: {w_[:5]}")
        return 2

    # vanilla merged = base + official DLC diffs, in load order
    merged = base
    for ext in gf.extensions:
        path = f"extensions/{ext}/libraries/equipmentmods.xml"
        if path not in gf:
            continue
        dlc_diff = etree.fromstring(gf.read_bytes(path), _PARSER)
        errs = apply_diff(merged, dlc_diff, ext)
        for e in errs:
            print(f"  warning (DLC diff): {e}")

    print("\n=== VANILLA scorecard (reference, not judged) ===")
    vanilla_mods = parse_weapon_mods(merged, names)
    report(evaluate(vanilla_mods, weapons), judge=False)

    if args.vanilla_only:
        return 0

    # apply OUR diff - unmatched sel = hard error (proves sels match)
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
    print(f"\n=== MODDED scorecard ({args.diff.name}: {n_ops} ops, "
          "all sels matched) ===")
    modded_mods = parse_weapon_mods(patched, names)
    failures = report(evaluate(modded_mods, weapons), judge=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
