#!/usr/bin/env python
"""Render the ship-mod-rebalance (hull mods) review dashboard (DRAFT).

    uv run --project ~/devel/x4-analyzer python tools/ship-mod-rebalance/report.py

One heatmap of every mod's effect across the ~11 ship stats, grouped by tier
and archetype; degenerate mods dimmed. Cells show the raw modifier, coloured
by goodness (blue = better). Body-only HTML fragment -> output/.
"""

from __future__ import annotations

import html
from copy import deepcopy
from pathlib import Path

from lxml import etree

from x4analyzer.gamedata.catalog import GameFiles
from x4analyzer.gamedata.extract import load_textdb
from x4analyzer.gamedata import shipmods as SM

REPO = Path(__file__).resolve().parents[2]
GAME_DIR = Path("/games/SteamLibrary/steamapps/common/X4 Foundations")
DIFF = REPO / "ship-mod-rebalance" / "libraries" / "equipmentmods.xml"
OUT = REPO / "output" / "ship-mod-dashboard.html"
_PARSER = etree.XMLParser(recover=True, huge_tree=True)
QN = {1: "Basic", 2: "Enhanced", 3: "Exceptional"}

ARCHETYPE = {
    # Racer: mass_mk1, drag_mk2, mass_mk3
    "mod_ship_mass_01_mk1": "Racer", "mod_ship_drag_01_mk2": "Racer",
    "mod_ship_mass_01_mk3": "Racer",
    # Tank: maxhull_mk1, regiondamage_mk2, regiondamage_mk3
    "mod_ship_maxhull_01_mk1": "Tank", "mod_ship_regiondamage_01_mk2": "Tank",
    "mod_ship_regiondamage_01_mk3": "Tank",
    # Ghost
    "mod_ship_radarcloak_01_mk1": "Ghost", "mod_ship_radarcloak_01_mk2": "Ghost",
    "mod_ship_radarcloak_01_mk3": "Ghost",
    # Explorer: regiondamage_mk1, mass_mk2, hidecargo
    "mod_ship_regiondamage_01_mk1": "Explorer", "mod_ship_mass_01_mk2": "Explorer",
    "mod_ship_hidecargo_01": "Explorer",
    "mod_ship_radarrange_01_mk1": "Recon",
    "mod_ship_missilecapacity_01_mk1": "Loadout",
    "mod_ship_deployablecapacity_01_mk1": "Smuggler",
}
ARCH_ORDER = {"Racer": 0, "Tank": 1, "Ghost": 2, "Explorer": 3, "Recon": 4,
              "Loadout": 5, "Smuggler": 6, "degenerate": 9}

# (stat, label). direction comes from shipmods (LOWER_BETTER / ADDITIVE).
COLS = [
    ("maxhull", "Hull"), ("mass", "Mass"), ("drag", "Drag"),
    ("radarrange", "Radar"), ("radarcloak", "Cloak"), ("regiondamage", "Hazard"),
    ("countermeasurecapacity", "CM"), ("deployablecapacity", "Deploy"),
    ("missilecapacity", "Missile"), ("unitcapacity", "Unit"),
    ("hidecargochance", "Cargo"),
]


def apply_diff(root, diff_root):
    for op in diff_root:
        if not isinstance(op.tag, str):
            continue
        sel = op.get("sel") or ""
        attr = None
        path = sel
        if "/@" in sel:
            path, attr = sel.rsplit("/@", 1)
        nodes = [n for n in root.xpath(path) if isinstance(n, etree._Element)]
        if not nodes:
            raise SystemExit(f"sel matched nothing: {sel}")
        if op.tag == "replace":
            if attr:
                for n in nodes:
                    n.set(attr, (op.text or "").strip())
            else:
                repl = [c for c in op if isinstance(c.tag, str)][0]
                for n in nodes:
                    n.getparent().replace(n, deepcopy(repl))
        elif op.tag == "add":
            for n in nodes:
                for c in op:
                    if isinstance(c.tag, str):
                        n.append(deepcopy(c))
        elif op.tag == "remove":
            for n in nodes:
                n.getparent().remove(n)


def _f(el, name, default=1.0):
    v = el.get(name)
    try:
        return float(v) if v not in (None, "") else default
    except ValueError:
        return default


def parse_mods(root, names):
    out = []
    for el in root.find("ship"):
        if not isinstance(el.tag, str) or not (el.get("ware") or "").startswith("mod_ship_"):
            continue
        bonus = el.find("bonus")
        bonuses, chance, bmax = [], 0.0, 0
        if bonus is not None:
            chance = _f(bonus, "chance", 0.0)
            bmax = int(_f(bonus, "max", 0))
            bonuses = [{"stat": b.tag, "min": _f(b, "min"), "max": _f(b, "max")}
                       for b in bonus if isinstance(b.tag, str)]
        forced = bool(bonuses) and chance >= 1.0 and len(bonuses) <= bmax
        out.append({"ware": el.get("ware"), "name": names.get(el.get("ware"), el.get("ware")),
                    "stat": el.tag, "quality": int(_f(el, "quality", 1)),
                    "min": _f(el, "min"), "max": _f(el, "max"), "forced": forced,
                    "bonuses": bonuses})
    return out


def load_rows():
    gf = GameFiles(GAME_DIR)
    tdb = load_textdb(gf)
    names = SM._mod_ware_names(gf, tdb)
    base = etree.fromstring(gf.read_bytes("libraries/equipmentmods.xml"), _PARSER)
    for ext in gf.extensions:
        p = f"extensions/{ext}/libraries/equipmentmods.xml"
        if p in gf:
            apply_diff(base, etree.fromstring(gf.read_bytes(p), _PARSER))
    patched = deepcopy(base)
    apply_diff(patched, etree.parse(str(DIFF), _PARSER).getroot())
    rows = []
    for m in parse_mods(patched, names):
        rows.append({"mod": m, "role": ARCHETYPE.get(m["ware"], "degenerate"),
                     "mults": SM.realized_mults(m, "optimal")})
    rows.sort(key=lambda r: (r["mod"]["quality"], ARCH_ORDER[r["role"]], r["mod"]["ware"]))
    return rows


CAP = {"countermeasurecapacity", "deployablecapacity", "missilecapacity",
       "unitcapacity"}


def cell(stat, value):
    """(css class, display) for a raw modifier value, coloured by goodness."""
    neutral = 0.0 if stat in SM.ADDITIVE else 1.0
    if abs(value - neutral) < 1e-9:
        return "n", ""
    good = SM.goodness(stat, value) > SM.goodness(stat, neutral)
    if stat == "radarcloak":
        span, disp = abs(value) / 0.8, f"{value:+.2f}"
    elif stat == "hidecargochance":
        span, disp = abs(value), f"{value:g}"
    elif stat in CAP:                       # flat +N consumables
        span, disp = abs(value) / 8.0, f"+{int(round(value))}"
    else:                                   # multiplier stats
        span, disp = abs(SM.goodness(stat, value) - 1.0) / 0.5, f"{value:.2f}"
    step = 1 if span < 0.2 else 2 if span < 0.4 else 3 if span < 0.6 else 4 if span < 0.85 else 5
    return f"{'b' if good else 'r'}{step}", disp


CSS = """
.hmr{--pg:#eef0ee;--sf:#fff;--ink:#12180f;--sec:#565f4e;--mut:#8b9280;
 --grid:#e3e6df;--acc:#5a7d3a;--rowh:#f6f8f4;
 --b1:#dce9fb;--b2:#aecdf3;--b3:#6da7ec;--b4:#2f7fdf;--b5:#16549e;
 --r1:#f6dcdc;--r2:#e9a9a9;--r3:#dd7676;--r4:#cf4f4f;--r5:#b23636;
 color-scheme:light;background:var(--pg);color:var(--ink);
 font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;
 padding:clamp(16px,4vw,40px);}
@media (prefers-color-scheme:dark){.hmr{--pg:#0c0f0a;--sf:#151a12;--ink:#eaf0e4;
 --sec:#a7b29a;--mut:#78836c;--grid:#242b20;--acc:#8bc35a;--rowh:#1b2116;
 --b1:#1e3350;--b2:#28517f;--b3:#3374c0;--b4:#4f9ae8;--b5:#8cbef2;
 --r1:#4a2626;--r2:#7a3636;--r3:#b04747;--r4:#d76a6a;--r5:#ee9b9b;color-scheme:dark;}}
:root[data-theme="dark"] .hmr{--pg:#0c0f0a;--sf:#151a12;--ink:#eaf0e4;--sec:#a7b29a;
 --mut:#78836c;--grid:#242b20;--acc:#8bc35a;--rowh:#1b2116;
 --b1:#1e3350;--b2:#28517f;--b3:#3374c0;--b4:#4f9ae8;--b5:#8cbef2;
 --r1:#4a2626;--r2:#7a3636;--r3:#b04747;--r4:#d76a6a;--r5:#ee9b9b;color-scheme:dark;}
:root[data-theme="light"] .hmr{--pg:#eef0ee;--sf:#fff;--ink:#12180f;--sec:#565f4e;
 --mut:#8b9280;--grid:#e3e6df;--acc:#5a7d3a;--rowh:#f6f8f4;
 --b1:#dce9fb;--b2:#aecdf3;--b3:#6da7ec;--b4:#2f7fdf;--b5:#16549e;
 --r1:#f6dcdc;--r2:#e9a9a9;--r3:#dd7676;--r4:#cf4f4f;--r5:#b23636;color-scheme:light;}
.hmr *{box-sizing:border-box;}
.hmr .wrap{max-width:1000px;margin:0 auto;}
.hmr .eyebrow{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--acc);font-weight:600;margin:0 0 6px;}
.hmr h1{font-size:clamp(22px,3.4vw,30px);margin:0 0 8px;letter-spacing:-.01em;text-wrap:balance;}
.hmr .lede{color:var(--sec);max-width:66ch;margin:0 0 18px;}
.hmr .lede b{color:var(--ink);}
.hmr .legend{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center;background:var(--sf);
 border:1px solid var(--grid);border-radius:10px;padding:12px 16px;margin-bottom:14px;font-size:12.5px;color:var(--sec);}
.hmr .scale{display:flex;align-items:center;gap:8px;}
.hmr .swatch{display:flex;border-radius:4px;overflow:hidden;box-shadow:0 0 0 1px var(--grid) inset;}
.hmr .swatch i{width:16px;height:14px;display:block;}
.hmr .roles{display:flex;flex-wrap:wrap;gap:9px 14px;}
.hmr .rkey{display:flex;align-items:center;gap:6px;}
.hmr .dot{width:9px;height:9px;border-radius:50%;flex:none;box-shadow:0 0 0 1px rgba(0,0,0,.15) inset;}
.hmr .dot.Racer{background:#eb6834;}.hmr .dot.Tank{background:#2f7fdf;}
.hmr .dot.Ghost{background:#4a3aa7;}.hmr .dot.Explorer{background:#1baf7a;}
.hmr .dot.Recon{background:#d6871f;}.hmr .dot.Loadout{background:#8a72d6;}
.hmr .dot.Smuggler{background:#37a89a;}
.hmr .dot.degenerate{background:var(--mut);opacity:.5;}
.hmr .scroll{overflow-x:auto;border:1px solid var(--grid);border-radius:10px;background:var(--sf);}
.hmr table{border-collapse:separate;border-spacing:2px;width:100%;font-variant-numeric:tabular-nums;}
.hmr th{font-weight:500;font-size:11px;color:var(--mut);text-align:center;padding:7px 3px;white-space:nowrap;}
.hmr th.rowh{text-align:left;padding-left:10px;position:sticky;left:0;background:var(--sf);z-index:2;}
.hmr td.rowh{position:sticky;left:0;background:var(--sf);z-index:1;text-align:left;padding:5px 10px;
 white-space:nowrap;min-width:150px;display:flex;align-items:center;gap:7px;}
.hmr td.rowh .nm{font-weight:600;font-size:12.5px;}
.hmr td.rowh .rl{color:var(--mut);font-size:10px;text-transform:uppercase;letter-spacing:.05em;margin-left:auto;}
.hmr tr.deg td.rowh .nm{color:var(--mut);font-weight:500;}
.hmr tr.grp td{position:sticky;left:0;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
 color:var(--sec);font-weight:600;padding:13px 10px 3px;background:var(--pg);}
.hmr td.c{width:58px;min-width:58px;text-align:center;font-size:12px;padding:6px 3px;border-radius:4px;
 color:var(--ink);font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;}
.hmr td.c.n::after{content:"\\00b7";color:var(--grid);}
.hmr .b1{background:var(--b1);}.hmr .b2{background:var(--b2);}
.hmr .b3{background:var(--b3);color:#fff;}.hmr .b4{background:var(--b4);color:#fff;}.hmr .b5{background:var(--b5);color:#fff;}
.hmr .r1{background:var(--r1);}.hmr .r2{background:var(--r2);}
.hmr .r3{background:var(--r3);color:#fff;}.hmr .r4{background:var(--r4);color:#fff;}.hmr .r5{background:var(--r5);color:#fff;}
@media (prefers-color-scheme:dark){.hmr .b3,.hmr .b4,.hmr .b5,.hmr .r3,.hmr .r4,.hmr .r5{color:#0c0f0a;}}
:root[data-theme="dark"] .hmr .b3,:root[data-theme="dark"] .hmr .b4,:root[data-theme="dark"] .hmr .b5,
:root[data-theme="dark"] .hmr .r3,:root[data-theme="dark"] .hmr .r4,:root[data-theme="dark"] .hmr .r5{color:#0c0f0a;}
:root[data-theme="light"] .hmr .b3,:root[data-theme="light"] .hmr .b4,:root[data-theme="light"] .hmr .b5,
:root[data-theme="light"] .hmr .r3,:root[data-theme="light"] .hmr .r4,:root[data-theme="light"] .hmr .r5{color:#fff;}
.hmr .note{font-size:12.5px;color:var(--mut);margin:10px 2px 0;max-width:74ch;}
.hmr .foot{margin-top:24px;padding-top:14px;border-top:1px solid var(--grid);font-size:12px;color:var(--mut);}
.hmr #tip{position:fixed;z-index:50;pointer-events:none;opacity:0;transition:opacity .1s;
 background:var(--ink);color:var(--pg);padding:6px 9px;border-radius:6px;font-size:12px;max-width:250px;}
"""

JS = """
(function(){var r=document.currentScript.closest('.hmr')||document;var tip=r.querySelector('#tip');
r.addEventListener('mouseover',function(e){var c=e.target.closest('.c[data-tip]');if(!c)return;
 tip.innerHTML=c.getAttribute('data-tip');tip.style.opacity=1;});
r.addEventListener('mousemove',function(e){if(tip.style.opacity=='1'){var x=e.clientX+14,y=e.clientY+16;
 if(x+260>innerWidth)x=e.clientX-tip.offsetWidth-14;tip.style.left=x+'px';tip.style.top=y+'px';}});
r.addEventListener('mouseout',function(e){if(e.target.closest('.c[data-tip]'))tip.style.opacity=0;});})();
"""

LABELS = {
    "maxhull": "hull HP", "mass": "mass (lighter=faster)", "drag": "drag (less=faster)",
    "radarrange": "radar range", "radarcloak": "signature", "regiondamage": "hazard damage taken",
    "countermeasurecapacity": "countermeasure capacity", "deployablecapacity": "deployable capacity",
    "missilecapacity": "missile capacity", "unitcapacity": "unit capacity",
    "hidecargochance": "hide cargo",
}


def main():
    rows = load_rows()
    sb = "".join(f"<i class='b{i}'></i>" for i in (1, 2, 3, 4, 5))
    sr = "".join(f"<i class='r{i}'></i>" for i in (5, 4, 3, 2, 1))
    roles = [("Racer", "Racer (mass+drag)"), ("Tank", "Tank (hull+sensors+loadout)"),
             ("Ghost", "Ghost (stealth)"), ("Explorer", "Explorer (hazard)"),
             ("Recon", "Recon"), ("Loadout", "Loadout"), ("Smuggler", "Smuggler (hide cargo)"),
             ("degenerate", "degenerate")]
    rk = "".join(f"<span class='rkey'><span class='dot {k}'></span>{html.escape(l)}</span>" for k, l in roles)

    p = [f"<style>{CSS}</style>", "<div class='hmr'><div id='tip'></div><div class='wrap'>"]
    p.append("<p class='eyebrow'>Pokey&rsquo;s Hull Mod Rebalance &middot; draft</p>")
    p.append("<h1>Hull mod archetypes</h1>")
    p.append("<p class='lede'>Four archetypes span every tier: <b>Racer</b> "
             "(mass + drag &mdash; accel &amp; top speed), <b>Tank</b> (hull, and it "
             "folds in sensors + loadout above Basic), <b>Ghost</b> (stealth) and "
             "<b>Explorer</b> (hazard resistance). Basic adds two utility picks "
             "(Recon, Loadout) that merge into Tank higher up. <b>Hull is the "
             "always-good stat</b> &mdash; it scales each tier and rides on every "
             "Enhanced/Exceptional mod. Cells show the raw modifier, blue where it "
             "helps; a few Basic mods are parked <b>degenerate</b>. Hover for detail.</p>")
    p.append(f"<div class='legend'><div class='scale'><span>worse</span>"
             f"<span class='swatch'>{sr}</span><span style='color:var(--mut)'>neutral</span>"
             f"<span class='swatch'>{sb}</span><span>better</span></div>"
             f"<div class='roles'>{rk}</div></div>")

    p.append("<div class='scroll'><table><thead><tr><th class='rowh'>mod</th>")
    for _s, lbl in COLS:
        p.append(f"<th>{html.escape(lbl)}</th>")
    p.append("</tr></thead><tbody>")
    last = None
    for r in rows:
        m = r["mod"]
        if m["quality"] != last:
            last = m["quality"]
            p.append(f"<tr class='grp'><td colspan='{len(COLS)+1}'>{QN[last]}</td></tr>")
        deg = " deg" if r["role"] == "degenerate" else ""
        p.append(f"<tr class='{deg.strip()}'>")
        p.append(f"<td class='rowh'><span class='dot {r['role']}'></span>"
                 f"<span class='nm'>{html.escape(m['name'])}</span>"
                 f"<span class='rl'>{r['role']}</span></td>")
        for stat, lbl in COLS:
            neutral = 0.0 if stat in SM.ADDITIVE else 1.0
            v = r["mults"].get(stat, neutral)
            cls, disp = cell(stat, v)
            tip = f"{m['name']} &middot; {html.escape(LABELS[stat])}: {v:g}"
            p.append(f"<td class='c {cls}' data-tip=\"{tip}\">{disp}</td>")
        p.append("</tr>")
    p.append("</tbody></table></div>")
    p.append("<p class='note'>Mass/drag show the raw multiplier (lower = lighter/"
             "sleeker = faster, so they read blue); signature is the additive cloak "
             "(more negative = stealthier); capacities are x multipliers on how many "
             "consumables you carry. The 4 degenerate Basic mods (the redundant drag "
             "ware + deployable/missile/unit capacity) are parked at a token value.</p>")
    p.append("<div class='foot'>DRAFT. Generated by tools/ship-mod-rebalance/report.py. "
             "Effect vectors are ship-independent. Not yet in-game verified.</div>")
    p.append("</div>")
    p.append(f"<script>{JS}</script></div>")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(p), encoding="utf-8")
    print(f"wrote {OUT}  ({len(rows)} mods)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
