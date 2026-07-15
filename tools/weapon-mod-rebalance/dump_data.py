#!/usr/bin/env python
"""Dump weapons + weapon-mods to JSON for the interactive slider tool
(tools/weapon-mod-rebalance/tuner.html). Uses the same GameFiles load and
diff application as evaluate.py so the tool is exactly faithful to the
harness. Run with the x4-analyzer env:

    uv run --project ~/devel/x4-analyzer python tools/weapon-mod-rebalance/dump_data.py
"""
import json
import sys
from copy import deepcopy
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as E

SIM_WEAPON_FIELDS = (
    "amount", "barrelamount", "dmg", "dmg_shield", "dmg_hull",
    "area_dmg", "area_dmg_shield", "reload_rate", "reload_time", "chargetime",
    "ammo_clip", "ammo_reload", "heat", "overheat", "coolrate", "cooldelay",
    "overheatcooldelay", "reenable",
)


def main() -> int:
    gf = E.GameFiles(Path(E.DEFAULT_GAME_DIR))
    tdb = E.load_textdb(gf)
    names = E._mod_ware_names(gf, tdb)
    weapons = E.extract_weapons(gf, tdb)

    base = etree.fromstring(gf.read_bytes("libraries/equipmentmods.xml"),
                            E._PARSER)
    merged = base
    for ext in gf.extensions:
        p = f"extensions/{ext}/libraries/equipmentmods.xml"
        if p in gf:
            E.apply_diff(merged,
                         etree.fromstring(gf.read_bytes(p), E._PARSER), ext)
    patched = deepcopy(merged)
    E.apply_diff(patched, etree.parse(str(E.DEFAULT_DIFF), E._PARSER).getroot(),
                 "our")
    mods = E.parse_weapon_mods(patched, names)

    wout = []
    for w in weapons:
        # only weapons with any sustained DPS bare (matches harness eligible)
        vs, vh = E.cycle_dps(w, None)
        if not (vs and vs > 0):
            continue
        s = E.simulate(w)
        if s.get("t_overheat") is not None:
            cat = "heat"
        elif w.get("ammo_clip"):
            cat = "clip"
        else:
            cat = "heatless"
        row = {"name": w["name"], "macro": w.get("macro", ""),
               "mining": E.is_mining_weapon(w), "cat": cat,
               "turret": "turret" in (w.get("name", "") + w.get("macro", "")).lower()}
        for f in SIM_WEAPON_FIELDS:
            v = w.get(f)
            if v is not None:
                row[f] = v
        wout.append(row)

    mout = []
    for m in sorted(mods, key=lambda m: (m["quality"], m["ware"])):
        if not (set(E.guaranteed_stats(m)) & set(E.SIM_STATS)):
            continue  # only DPS-affecting mods drive the niche map
        if not E._MK_WARE.search(m["ware"]):
            continue  # skip scenario wares
        mout.append({
            "ware": m["ware"], "name": m["name"], "quality": m["quality"],
            "stat": m["stat"], "min": m["min"], "max": m["max"],
            "forced": m["forced"], "bonus_max": m["bonus_max"],
            "serves_mining": E.serves_mining(m),
            "bonuses": [{"stat": b["stat"], "min": b["min"], "max": b["max"],
                         "weight": b["weight"]} for b in m["bonuses"]],
        })

    out = {"sim_stats": list(E.SIM_STATS), "weapons": wout, "mods": mout,
           "eps_tie": E.EPS_TIE, "t1_max": E.T1_MAX_WINRATE,
           "t3_max": E.T3_MAX_BUNDLE}
    payload = json.dumps(out, separators=(",", ":"))

    here = E.REPO / "tools" / "weapon-mod-rebalance"
    (here / "tuner-data.json").write_text(payload)

    # build the self-contained tuner.html from the template by inlining data
    template = (here / "tuner.src.html").read_text()
    token = "/*__TUNER_DATA__*/ null"
    if token not in template:
        raise SystemExit(f"template missing data token {token!r}")
    html = template.replace(token, payload, 1)
    (here / "tuner.html").write_text(html)

    print(f"wrote tuner.html ({len(html)//1024} KB, "
          f"{len(wout)} weapons, {len(mout)} mods)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
