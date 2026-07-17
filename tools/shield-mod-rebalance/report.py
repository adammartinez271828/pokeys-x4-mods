#!/usr/bin/env python
"""Render the shield-mod-rebalance review dashboard (DRAFT).

    uv run --project ~/devel/x4-analyzer python tools/shield-mod-rebalance/report.py

Applies the shield diff and, per mod, shows its effect on capacity / recharge
rate / recharge delay plus the derived REFILL TIME (delay + capacity/rate) -
the composite where capacity trades against recovery. Emits a self-contained
body-only HTML fragment to output/shield-mod-dashboard.html.
"""

from __future__ import annotations

import html
from copy import deepcopy
from pathlib import Path

from lxml import etree

from x4analyzer.gamedata.catalog import GameFiles
from x4analyzer.gamedata.extract import load_textdb
from x4analyzer.gamedata import shields as S

REPO = Path(__file__).resolve().parents[2]
GAME_DIR = Path("/games/SteamLibrary/steamapps/common/X4 Foundations")
DIFF = REPO / "shield-mod-rebalance" / "libraries" / "equipmentmods.xml"
OUT = REPO / "output" / "shield-mod-dashboard.html"
_PARSER = etree.XMLParser(recover=True, huge_tree=True)
QN = {1: "Basic", 2: "Enhanced", 3: "Exceptional"}

ARCHETYPE = {
    "mod_shield_capacity_01_mk1": "Bastion",
    "mod_shield_capacity_01_mk2": "Bastion",
    "mod_shield_capacity_01_mk3": "Bastion",
    "mod_shield_rechargerate_01_mk1": "Regenerator",
    "mod_shield_rechargerate_01_mk2": "Regenerator",
    "mod_shield_rechargerate_01_mk3": "Regenerator",
    "mod_shield_rechargedelay_01_mk1": "Resilient",
    "mod_shield_capacity_02_mk3": "Bulwark",
}
ARCH_ORDER = {"Bastion": 0, "Regenerator": 1, "Resilient": 2, "Bulwark": 3}

# (derived key, label, higher_is_better)
COLS = [
    ("capacity", "Capacity", True),
    ("rechargerate", "Recharge rate", True),
    ("rechargedelay", "Recharge delay", False),
    ("refill_time", "Refill time", False),   # derived composite
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
    sec = root.find("shield")
    for el in sec:
        if not isinstance(el.tag, str) or not (el.get("ware") or "").startswith("mod_shield_"):
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
    names = S._mod_ware_names(gf, tdb)
    base = etree.fromstring(gf.read_bytes("libraries/equipmentmods.xml"), _PARSER)
    for ext in gf.extensions:
        p = f"extensions/{ext}/libraries/equipmentmods.xml"
        if p in gf:
            apply_diff(base, etree.fromstring(gf.read_bytes(p), _PARSER))
    patched = deepcopy(base)
    apply_diff(patched, etree.parse(str(DIFF), _PARSER).getroot())
    rep = S.representative_shield(S.extract_shields(gf), "m")
    b = S.derive_stats(rep)
    rows = []
    for m in parse_mods(patched, names):
        mults = S.realized_mults(m, "optimal")
        d = S.derive_stats(rep, mults)
        rows.append({"mod": m, "role": ARCHETYPE.get(m["ware"], "?"),
                     "mults": mults,
                     "ratio": {k: (d[k] / b[k] if b[k] else 1.0) for k, _, _ in COLS}})
    rows.sort(key=lambda r: (r["mod"]["quality"], ARCH_ORDER.get(r["role"], 9)))
    return rows, rep, b


def cell(value, higher_better):
    if abs(value - 1.0) < 1e-6:
        return "n", ""
    good = (value > 1.0) if higher_better else (value < 1.0)
    mag = abs(value - 1.0)
    span = mag / 0.5
    step = 1 if span < 0.2 else 2 if span < 0.4 else 3 if span < 0.6 else 4 if span < 0.85 else 5
    return f"{'b' if good else 'r'}{step}", f"{value:.2f}"


CSS = """
.smr{--pg:#eef1f0;--sf:#fff;--ink:#121820;--sec:#55616d;--mut:#8b95a0;
 --grid:#e2e7ea;--acc:#3f7f9c;--rowh:#f6f8f8;
 --b1:#dce9fb;--b2:#aecdf3;--b3:#6da7ec;--b4:#2f7fdf;--b5:#16549e;
 --r1:#f6dcdc;--r2:#e9a9a9;--r3:#dd7676;--r4:#cf4f4f;--r5:#b23636;
 color-scheme:light;background:var(--pg);color:var(--ink);
 font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;
 padding:clamp(16px,4vw,40px);}
@media (prefers-color-scheme:dark){.smr{--pg:#0c0f13;--sf:#151a1f;--ink:#eaeff4;
 --sec:#a7b2bd;--mut:#78838f;--grid:#242b32;--acc:#5fb0d0;--rowh:#1b2127;
 --b1:#1e3350;--b2:#28517f;--b3:#3374c0;--b4:#4f9ae8;--b5:#8cbef2;
 --r1:#4a2626;--r2:#7a3636;--r3:#b04747;--r4:#d76a6a;--r5:#ee9b9b;color-scheme:dark;}}
:root[data-theme="dark"] .smr{--pg:#0c0f13;--sf:#151a1f;--ink:#eaeff4;--sec:#a7b2bd;
 --mut:#78838f;--grid:#242b32;--acc:#5fb0d0;--rowh:#1b2127;
 --b1:#1e3350;--b2:#28517f;--b3:#3374c0;--b4:#4f9ae8;--b5:#8cbef2;
 --r1:#4a2626;--r2:#7a3636;--r3:#b04747;--r4:#d76a6a;--r5:#ee9b9b;color-scheme:dark;}
:root[data-theme="light"] .smr{--pg:#eef1f0;--sf:#fff;--ink:#121820;--sec:#55616d;
 --mut:#8b95a0;--grid:#e2e7ea;--acc:#3f7f9c;--rowh:#f6f8f8;
 --b1:#dce9fb;--b2:#aecdf3;--b3:#6da7ec;--b4:#2f7fdf;--b5:#16549e;
 --r1:#f6dcdc;--r2:#e9a9a9;--r3:#dd7676;--r4:#cf4f4f;--r5:#b23636;color-scheme:light;}
.smr *{box-sizing:border-box;}
.smr .wrap{max-width:860px;margin:0 auto;}
.smr .eyebrow{font-size:12px;letter-spacing:.18em;text-transform:uppercase;
 color:var(--acc);font-weight:600;margin:0 0 6px;}
.smr h1{font-size:clamp(22px,3.4vw,30px);margin:0 0 8px;letter-spacing:-.01em;text-wrap:balance;}
.smr .lede{color:var(--sec);max-width:64ch;margin:0 0 20px;}
.smr .lede b{color:var(--ink);}
.smr .legend{display:flex;flex-wrap:wrap;gap:14px 22px;align-items:center;
 background:var(--sf);border:1px solid var(--grid);border-radius:10px;
 padding:12px 16px;margin-bottom:16px;font-size:12.5px;color:var(--sec);}
.smr .scale{display:flex;align-items:center;gap:8px;}
.smr .swatch{display:flex;border-radius:4px;overflow:hidden;box-shadow:0 0 0 1px var(--grid) inset;}
.smr .swatch i{width:17px;height:14px;display:block;}
.smr .roles{display:flex;flex-wrap:wrap;gap:10px 16px;}
.smr .rkey{display:flex;align-items:center;gap:6px;}
.smr .dot{width:9px;height:9px;border-radius:50%;flex:none;box-shadow:0 0 0 1px rgba(0,0,0,.15) inset;}
.smr .dot.Bastion{background:#2f7fdf;}
.smr .dot.Regenerator{background:#1baf7a;}
.smr .dot.Resilient{background:#d6871f;}
.smr .dot.Bulwark{background:#8a72d6;}
.smr .scroll{overflow-x:auto;border:1px solid var(--grid);border-radius:10px;background:var(--sf);}
.smr table{border-collapse:separate;border-spacing:2px;width:100%;font-variant-numeric:tabular-nums;}
.smr th{font-weight:500;font-size:11.5px;color:var(--mut);text-align:center;padding:8px 4px;white-space:nowrap;}
.smr th.rowh{text-align:left;padding-left:12px;}
.smr th.sep{border-left:2px solid var(--grid);}
.smr td.rowh{text-align:left;padding:6px 12px;white-space:nowrap;min-width:170px;
 display:flex;align-items:center;gap:8px;}
.smr td.rowh .nm{font-weight:600;font-size:13px;}
.smr td.rowh .rl{color:var(--mut);font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;margin-left:auto;}
.smr tr.grp td{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--sec);
 font-weight:600;padding:14px 12px 4px;background:var(--pg);}
.smr td.c{width:92px;text-align:center;font-size:12.5px;padding:8px 4px;border-radius:4px;
 color:var(--ink);font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;}
.smr td.c.n{color:var(--grid);}
.smr td.c.sep{border-left:2px solid var(--grid);}
.smr .b1{background:var(--b1);}.smr .b2{background:var(--b2);}
.smr .b3{background:var(--b3);color:#fff;}.smr .b4{background:var(--b4);color:#fff;}.smr .b5{background:var(--b5);color:#fff;}
.smr .r1{background:var(--r1);}.smr .r2{background:var(--r2);}
.smr .r3{background:var(--r3);color:#fff;}.smr .r4{background:var(--r4);color:#fff;}.smr .r5{background:var(--r5);color:#fff;}
@media (prefers-color-scheme:dark){.smr .b3,.smr .b4,.smr .b5,.smr .r3,.smr .r4,.smr .r5{color:#0c0f13;}}
:root[data-theme="dark"] .smr .b3,:root[data-theme="dark"] .smr .b4,:root[data-theme="dark"] .smr .b5,
:root[data-theme="dark"] .smr .r3,:root[data-theme="dark"] .smr .r4,:root[data-theme="dark"] .smr .r5{color:#0c0f13;}
:root[data-theme="light"] .smr .b3,:root[data-theme="light"] .smr .b4,:root[data-theme="light"] .smr .b5,
:root[data-theme="light"] .smr .r3,:root[data-theme="light"] .smr .r4,:root[data-theme="light"] .smr .r5{color:#fff;}
.smr .note{font-size:12.5px;color:var(--mut);margin:10px 2px 0;max-width:72ch;}
.smr .foot{margin-top:26px;padding-top:14px;border-top:1px solid var(--grid);font-size:12px;color:var(--mut);}
.smr #tip{position:fixed;z-index:50;pointer-events:none;opacity:0;transition:opacity .1s;
 background:var(--ink);color:var(--pg);padding:6px 9px;border-radius:6px;font-size:12px;max-width:260px;}
"""

JS = """
(function(){var r=document.currentScript.closest('.smr')||document;var tip=r.querySelector('#tip');
r.addEventListener('mouseover',function(e){var c=e.target.closest('.c[data-tip]');if(!c)return;
 tip.innerHTML=c.getAttribute('data-tip');tip.style.opacity=1;});
r.addEventListener('mousemove',function(e){if(tip.style.opacity=='1'){var x=e.clientX+14,y=e.clientY+16;
 if(x+270>innerWidth)x=e.clientX-tip.offsetWidth-14;tip.style.left=x+'px';tip.style.top=y+'px';}});
r.addEventListener('mouseout',function(e){if(e.target.closest('.c[data-tip]'))tip.style.opacity=0;});})();
"""


def main():
    rows, rep, base = load_rows()
    sb = "".join(f"<i class='b{i}'></i>" for i in (1, 2, 3, 4, 5))
    sr = "".join(f"<i class='r{i}'></i>" for i in (5, 4, 3, 2, 1))
    roles = [("Bastion", "Bastion (capacity)"), ("Regenerator", "Regenerator (recharge rate)"),
             ("Resilient", "Resilient (recharge delay)"), ("Bulwark", "Bulwark (balanced)")]
    rk = "".join(f"<span class='rkey'><span class='dot {k}'></span>{html.escape(l)}</span>" for k, l in roles)

    p = [f"<style>{CSS}</style>", "<div class='smr'><div id='tip'></div><div class='wrap'>"]
    p.append("<p class='eyebrow'>Pokey&rsquo;s Shield Mod Rebalance &middot; draft</p>")
    p.append("<h1>Shield mod archetypes</h1>")
    p.append("<p class='lede'>Three levers, three archetypes: <b>Bastion</b> "
             "(capacity), <b>Regenerator</b> (recharge rate) and <b>Resilient</b> "
             "(recharge delay), plus a balanced <b>Bulwark</b> at the top tier. "
             "<b>Capacity is the always-good stat</b> &mdash; it never hurts, so it "
             "scales up each tier and rides on higher-tier recovery mods. The catch: "
             "capacity raises the buffer but <b>slows the refill</b> (bigger pool, same "
             "rate), so watch the last column. Numbers are for a representative "
             f"M shield ({int(base['capacity'])} HP, {int(base['rechargerate'])} HP/s, "
             f"{base['rechargedelay']:.0f}s delay); blue = better, red = worse.</p>")
    p.append(f"<div class='legend'><div class='scale'><span>worse</span>"
             f"<span class='swatch'>{sr}</span><span style='color:var(--mut)'>&times;1.0</span>"
             f"<span class='swatch'>{sb}</span><span>better</span></div>"
             f"<div class='roles'>{rk}</div></div>")

    p.append("<div class='scroll'><table><thead><tr><th class='rowh'>mod</th>")
    for i, (_k, lbl, hb) in enumerate(COLS):
        sep = " sep" if _k == "refill_time" else ""
        arrow = "" if hb else " ↓"
        p.append(f"<th class='{sep}'>{html.escape(lbl)}{arrow}</th>")
    p.append("</tr></thead><tbody>")
    last = None
    for r in rows:
        m = r["mod"]
        if m["quality"] != last:
            last = m["quality"]
            p.append(f"<tr class='grp'><td colspan='{len(COLS)+1}'>{QN[last]}</td></tr>")
        p.append("<tr>")
        p.append(f"<td class='rowh'><span class='dot {r['role']}'></span>"
                 f"<span class='nm'>{html.escape(m['name'])}</span>"
                 f"<span class='rl'>{r['role']}</span></td>")
        for k, lbl, hb in COLS:
            v = r["ratio"][k]
            cls, disp = cell(v, hb)
            sep = " sep" if k == "refill_time" else ""
            tip = f"{m['name']} &middot; {lbl}: &times;{v:.3f}"
            if k == "refill_time":
                tip += " (delay + capacity/rate)"
            p.append(f"<td class='c {cls}{sep}' data-tip=\"{tip}\">{disp}</td>")
        p.append("</tr>")
    p.append("</tbody></table></div>")
    p.append("<p class='note'>Refill time = delay + capacity/rate (seconds from "
             "shield-down to full). Bastion mods make it <b>longer</b> (red) even as "
             "they add buffer &mdash; the capacity/recovery trade-off. Only 2 wares "
             "exist at Enhanced, so Resilient (delay) is folded into the Enhanced "
             "Regenerator; there is no standalone Resilient above Basic (a gap to "
             "discuss).</p>")
    p.append("<div class='foot'>DRAFT. Generated by tools/shield-mod-rebalance/report.py "
             "from the draft diff and the x4-analyzer shield model. Capacity/rate/delay "
             "ratios are shield-independent; refill time is quoted for the representative "
             "M shield. Not yet in-game verified.</div>")
    p.append("</div>")
    p.append(f"<script>{JS}</script></div>")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(p), encoding="utf-8")
    print(f"wrote {OUT}  ({len(rows)} mods)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
