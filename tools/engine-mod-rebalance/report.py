#!/usr/bin/env python
"""Render the engine-mod-rebalance review dashboard.

Computes each shipped mod's RAW declared modifiers and its COMBINED effect on
ship performance (via the x4-analyzer engine sim) and emits a self-contained
HTML dashboard to output/engine-mod-dashboard.html. The two heatmaps share a
row order, so the forward-thrust leak reads as one declared cell lighting up
several downstream cells.

    uv run --project ~/devel/x4-analyzer python tools/engine-mod-rebalance/report.py

The output is a body-only HTML fragment (inline <style>/<script>, no
<head>/<body>) so it renders both as a standalone file and as a published
Artifact.
"""

from __future__ import annotations

import html
import importlib.util
from copy import deepcopy
from pathlib import Path

from lxml import etree

from x4analyzer.gamedata.catalog import GameFiles
from x4analyzer.gamedata.extract import load_textdb
from x4analyzer.gamedata import engines as E

REPO = Path(__file__).resolve().parents[2]
GAME_DIR = Path("/games/SteamLibrary/steamapps/common/X4 Foundations")
DIFF = REPO / "engine-mod-rebalance" / "libraries" / "equipmentmods.xml"
OUT = REPO / "output" / "engine-mod-dashboard.html"

# import the harness module (sibling file) for its diff applier + parser
_spec = importlib.util.spec_from_file_location(
    "engine_eval", Path(__file__).with_name("evaluate.py"))
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)

QN = {1: "Basic", 2: "Enhanced", 3: "Exceptional"}

# (tag, label, higher_is_better) - raw declared-modifier columns
RAW_COLS = [
    ("forwardthrust", "Fwd thrust", True),
    ("boostthrust", "Boost", True),
    ("boostduration", "Boost dur", True),
    ("boostacc", "Boost acc", True),
    ("travelthrust", "Travel", True),
    ("travelchargetime", "Tvl charge", False),
    ("travelattacktime", "Tvl attack", False),
    ("rotationthrust", "Rotation", True),
    ("strafethrust", "Strafe", True),
    ("strafeacc", "Strafe acc", True),
]
# (derived key, label, higher_is_better) - combined ship-performance columns
COMB_COLS = [
    ("forward_speed", "Fwd speed", True),
    ("forward_accel", "Fwd accel", True),
    ("boost_speed", "Boost spd", True),
    ("boost_duration", "Boost dur", True),
    ("boost_accel", "Boost acc", True),
    ("travel_speed", "Travel spd", True),
    ("travel_charge", "Tvl charge", False),
    ("travel_attack", "Tvl attack", False),
    ("turn_rate", "Turn rate", True),
    ("strafe_speed", "Strafe spd", True),
    ("strafe_accel", "Strafe acc", True),
]
# derived stat -> the mod tag that DIRECTLY drives it (anything else = a leak)
OWN_TAG = {
    "forward_speed": "forwardthrust", "forward_accel": "forwardthrust",
    "boost_speed": "boostthrust", "boost_duration": "boostduration",
    "boost_accel": "boostacc", "travel_speed": "travelthrust",
    "travel_charge": "travelchargetime", "travel_attack": "travelattacktime",
    "turn_rate": "rotationthrust", "strafe_speed": "strafethrust",
    "strafe_accel": "strafeacc",
}


# carrier ware -> archetype (everything else is a parked "degenerate" mod)
ARCHETYPE = {
    "mod_engine_forwardthrust_02_mk1": "Interceptor",
    "mod_engine_forwardthrust_02_mk2": "Interceptor",
    "mod_engine_forwardthrust_01_mk3": "Interceptor",
    "mod_engine_strafethrust_02_mk1": "Dogfighter",
    "mod_engine_boostthrust_01_mk2": "Dogfighter",
    "mod_engine_rotationthrust_01_mk3": "Dogfighter",
    "mod_engine_travelstartthrust_01_mk1": "Booster",
    "mod_engine_boostthrust_02_mk2": "Booster",
    "mod_engine_boostthrust_01_mk3": "Booster",
    "mod_engine_travelchargetime_01_mk1": "Voyager",
    "mod_engine_travelthrust_02_mk2": "Voyager",
    "mod_engine_travelthrust_01_mk3": "Voyager",
}
ARCH_ORDER = {"Interceptor": 0, "Dogfighter": 1, "Booster": 2, "Voyager": 3,
              "degenerate": 9}


def role_of(m: dict) -> str:
    return ARCHETYPE.get(m["ware"], "degenerate")


def load_mods() -> list[dict]:
    gf = GameFiles(GAME_DIR)
    tdb = load_textdb(gf)
    names = E._mod_ware_names(gf, tdb)
    base = etree.fromstring(gf.read_bytes("libraries/equipmentmods.xml"),
                            ev._PARSER)
    for ext in gf.extensions:
        p = f"extensions/{ext}/libraries/equipmentmods.xml"
        if p in gf:
            ev.apply_diff(base, etree.fromstring(gf.read_bytes(p), ev._PARSER), ext)
    patched = deepcopy(base)
    errs = ev.apply_diff(patched, etree.parse(str(DIFF), ev._PARSER).getroot(),
                         DIFF.name)
    if errs:
        raise SystemExit("diff errors:\n" + "\n".join(errs))
    ships = E.extract_ships(gf, tdb)
    eng = E.extract_engines(gf, tdb)
    thr = E.extract_thrusters(gf)
    ship = next(s for s in ships if s["macro"] == "ship_arg_s_fighter_01_a_macro")
    engine = E.representative_engine(eng, "s", "allround", 1)
    thruster = thr["s"]
    base_stats = E.derive_stats(ship, engine, thruster)

    mods = [m for m in ev.parse_engine_mods(patched, names)
            if m["ware"].rstrip("0123456789").endswith("_mk")]
    rows = []
    for m in mods:
        raw = E.realized_mults(m, "optimal")
        d = E.modded_stats(ship, engine, thruster, raw)
        comb = {k: (d[k] / base_stats[k] if base_stats[k] else 1.0)
                for k, _, _ in COMB_COLS}
        rows.append({"mod": m, "role": role_of(m), "raw": raw, "comb": comb})
    rows.sort(key=lambda r: (r["mod"]["quality"], ARCH_ORDER[r["role"]],
                             r["mod"]["ware"]))
    return rows


# ------------------------------------------------------------------- render

def cell_class(value: float, higher_better: bool) -> tuple[str, str]:
    """(css class, display) for a value. Blue = improves, red = worsens,
    blank when exactly neutral."""
    if abs(value - 1.0) < 1e-6:
        return "n", ""
    good = (value > 1.0) if higher_better else (value < 1.0)
    if higher_better:
        mag = (value - 1.0) if value > 1 else (1.0 - value)
    else:
        mag = (1.0 - value) if value < 1 else (value - 1.0)
    ramp = "b" if good else "r"
    span = mag / 0.85 if good else mag / 0.30      # buffs reach +85%, maluses -30%
    step = 1 if span < 0.2 else 2 if span < 0.4 else 3 if span < 0.6 else 4 if span < 0.8 else 5
    return f"{ramp}{step}", f"{value:.2f}"


def heatmap(rows: list[dict], cols, kind: str) -> str:
    out = ['<div class="scroll"><table class="hm">']
    out.append("<thead><tr><th class='rowh'></th>")
    for _key, label, hb in cols:
        arrow = "" if hb else " ↓"
        out.append(f"<th><span>{html.escape(label)}{arrow}</span></th>")
    out.append("</tr></thead><tbody>")
    last_q = None
    for r in rows:
        m = r["mod"]
        if m["quality"] != last_q:
            last_q = m["quality"]
            out.append(f"<tr class='grp'><td colspan='{len(cols)+1}'>"
                       f"{QN[last_q]}</td></tr>")
        deg = " deg" if r["role"] == "degenerate" else ""
        out.append(f"<tr class='{deg.strip()}'>")
        out.append(
            f"<td class='rowh'><span class='dot {r['role']}'></span>"
            f"<span class='nm'>{html.escape(m['name'])}</span>"
            f"<span class='rl'>{r['role']}</span></td>")
        for key, label, hb in cols:
            if kind == "raw":
                val = r["raw"].get(key, 1.0)
            else:
                val = r["comb"][key]
            cls, disp = cell_class(val, hb)
            leak = ""
            tip = f"{m['name']} &middot; {label}: &times;{val:.3f}"
            if kind == "comb" and abs(val - 1.0) > 1e-6:
                own = OWN_TAG[key]
                if own not in r["raw"]:
                    leak = " leak"
                    tip += " &mdash; via forward-thrust leak"
                elif disp:
                    tip += " &mdash; direct"
            out.append(f"<td class='c {cls}{leak}' data-tip=\"{tip}\">{disp}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


CSS = """
.emr{--pg:#eef1f0;--sf:#ffffff;--ink:#121820;--sec:#55616d;--mut:#8b95a0;
 --grid:#e2e7ea;--acc:#d6871f;--rowh:#f6f8f8;
 --b1:#dce9fb;--b2:#aecdf3;--b3:#6da7ec;--b4:#2f7fdf;--b5:#16549e;
 --r1:#f6dcdc;--r2:#e9a9a9;--r3:#dd7676;--r4:#cf4f4f;--r5:#b23636;
 color-scheme:light;background:var(--pg);color:var(--ink);
 font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
 line-height:1.5;padding:clamp(16px,4vw,40px);}
@media (prefers-color-scheme:dark){.emr{--pg:#0c0f13;--sf:#151a1f;--ink:#eaeff4;
 --sec:#a7b2bd;--mut:#78838f;--grid:#242b32;--acc:#eba234;--rowh:#1b2127;
 --b1:#1e3350;--b2:#28517f;--b3:#3374c0;--b4:#4f9ae8;--b5:#8cbef2;
 --r1:#4a2626;--r2:#7a3636;--r3:#b04747;--r4:#d76a6a;--r5:#ee9b9b;color-scheme:dark;}}
:root[data-theme="dark"] .emr{--pg:#0c0f13;--sf:#151a1f;--ink:#eaeff4;
 --sec:#a7b2bd;--mut:#78838f;--grid:#242b32;--acc:#eba234;--rowh:#1b2127;
 --b1:#1e3350;--b2:#28517f;--b3:#3374c0;--b4:#4f9ae8;--b5:#8cbef2;
 --r1:#4a2626;--r2:#7a3636;--r3:#b04747;--r4:#d76a6a;--r5:#ee9b9b;color-scheme:dark;}
:root[data-theme="light"] .emr{--pg:#eef1f0;--sf:#ffffff;--ink:#121820;--sec:#55616d;
 --mut:#8b95a0;--grid:#e2e7ea;--acc:#d6871f;--rowh:#f6f8f8;
 --b1:#dce9fb;--b2:#aecdf3;--b3:#6da7ec;--b4:#2f7fdf;--b5:#16549e;
 --r1:#f6dcdc;--r2:#e9a9a9;--r3:#dd7676;--r4:#cf4f4f;--r5:#b23636;color-scheme:light;}
.emr *{box-sizing:border-box;}
.emr .wrap{max-width:1120px;margin:0 auto;}
.emr .eyebrow{font-size:12px;letter-spacing:.18em;text-transform:uppercase;
 color:var(--acc);font-weight:600;margin:0 0 6px;}
.emr h1{font-size:clamp(22px,3.4vw,32px);margin:0 0 8px;letter-spacing:-.01em;
 text-wrap:balance;}
.emr .lede{color:var(--sec);max-width:64ch;margin:0 0 22px;}
.emr h2{font-size:15px;letter-spacing:.02em;margin:30px 0 4px;}
.emr .sub{color:var(--mut);font-size:13px;margin:0 0 12px;}
.emr .legend{display:flex;flex-wrap:wrap;gap:18px 26px;align-items:center;
 background:var(--sf);border:1px solid var(--grid);border-radius:10px;
 padding:12px 16px;margin-bottom:14px;font-size:12.5px;color:var(--sec);}
.emr .scale{display:flex;align-items:center;gap:8px;}
.emr .swatch{display:flex;border-radius:4px;overflow:hidden;
 box-shadow:0 0 0 1px var(--grid) inset;}
.emr .swatch i{width:17px;height:14px;display:block;}
.emr .roles{display:flex;flex-wrap:wrap;gap:12px 16px;}
.emr .rkey{display:flex;align-items:center;gap:6px;}
.emr .dot{width:9px;height:9px;border-radius:50%;flex:none;
 box-shadow:0 0 0 1px rgba(0,0,0,.15) inset;}
.emr .dot.Interceptor{background:#2a78d6;}
.emr .dot.Dogfighter{background:#eb6834;}
.emr .dot.Booster{background:#d6871f;}
.emr .dot.Voyager{background:#4a3aa7;}
.emr .dot.degenerate{background:var(--mut);opacity:.5;}
.emr tr.deg td.rowh .nm{color:var(--mut);font-weight:500;}
.emr .scroll{overflow-x:auto;border:1px solid var(--grid);border-radius:10px;
 background:var(--sf);}
.emr table.hm{border-collapse:separate;border-spacing:2px;width:100%;
 font-variant-numeric:tabular-nums;}
.emr .hm th{font-weight:500;font-size:11px;color:var(--mut);
 text-align:center;vertical-align:bottom;padding:6px 3px;white-space:nowrap;}
.emr .hm th span{display:inline-block;}
.emr .hm th.rowh{position:sticky;left:0;background:var(--sf);z-index:2;}
.emr td.rowh{position:sticky;left:0;background:var(--sf);z-index:1;
 text-align:left;padding:5px 10px 5px 8px;white-space:nowrap;min-width:172px;
 display:flex;align-items:center;gap:8px;}
.emr td.rowh .nm{font-weight:600;font-size:13px;}
.emr td.rowh .rl{color:var(--mut);font-size:10.5px;text-transform:uppercase;
 letter-spacing:.06em;margin-left:auto;}
.emr tr.grp td{position:sticky;left:0;font-size:11px;letter-spacing:.14em;
 text-transform:uppercase;color:var(--sec);font-weight:600;
 padding:14px 8px 4px;background:var(--pg);}
.emr td.c{width:64px;min-width:64px;text-align:center;font-size:12.5px;
 padding:7px 4px;border-radius:4px;color:var(--ink);
 font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;}
.emr td.c.n{color:transparent;}
.emr td.c.n::after{content:"\\00b7";color:var(--grid);}
.emr td.c.leak{outline:1.5px dashed var(--acc);outline-offset:-3px;}
.emr .b1{background:var(--b1);}.emr .b2{background:var(--b2);}
.emr .b3{background:var(--b3);color:#fff;}.emr .b4{background:var(--b4);color:#fff;}
.emr .b5{background:var(--b5);color:#fff;}
.emr .r1{background:var(--r1);}.emr .r2{background:var(--r2);}
.emr .r3{background:var(--r3);color:#fff;}.emr .r4{background:var(--r4);color:#fff;}
.emr .r5{background:var(--r5);color:#fff;}
@media (prefers-color-scheme:dark){.emr .b3,.emr .b4,.emr .b5,
 .emr .r3,.emr .r4,.emr .r5{color:#0c0f13;}}
:root[data-theme="dark"] .emr .b3,:root[data-theme="dark"] .emr .b4,
:root[data-theme="dark"] .emr .b5,:root[data-theme="dark"] .emr .r3,
:root[data-theme="dark"] .emr .r4,:root[data-theme="dark"] .emr .r5{color:#0c0f13;}
:root[data-theme="light"] .emr .b3,:root[data-theme="light"] .emr .b4,
:root[data-theme="light"] .emr .b5,:root[data-theme="light"] .emr .r3,
:root[data-theme="light"] .emr .r4,:root[data-theme="light"] .emr .r5{color:#fff;}
.emr .note{font-size:12.5px;color:var(--mut);margin:8px 2px 0;max-width:70ch;}
.emr .foot{margin-top:30px;padding-top:14px;border-top:1px solid var(--grid);
 font-size:12px;color:var(--mut);}
.emr #tip{position:fixed;z-index:50;pointer-events:none;opacity:0;
 transition:opacity .1s;background:var(--ink);color:var(--pg);
 padding:6px 9px;border-radius:6px;font-size:12px;max-width:260px;
 box-shadow:0 4px 14px rgba(0,0,0,.25);}
"""

JS = """
(function(){var r=document.currentScript.closest('.emr')||document;
var tip=r.querySelector('#tip');
r.addEventListener('mouseover',function(e){var c=e.target.closest('.c[data-tip]');
 if(!c)return;tip.innerHTML=c.getAttribute('data-tip');tip.style.opacity=1;});
r.addEventListener('mousemove',function(e){if(tip.style.opacity=='1'){
 var x=e.clientX+14,y=e.clientY+16;
 if(x+270>innerWidth)x=e.clientX-tip.offsetWidth-14;
 tip.style.left=x+'px';tip.style.top=y+'px';}});
r.addEventListener('mouseout',function(e){if(e.target.closest('.c[data-tip]'))
 tip.style.opacity=0;});})();
"""


def main() -> int:
    rows = load_mods()
    swatch_b = "".join(f"<i class='b{i}'></i>" for i in (1, 2, 3, 4, 5))
    swatch_r = "".join(f"<i class='r{i}'></i>" for i in (5, 4, 3, 2, 1))
    roles = [("Interceptor", "Interceptor (speed)"),
             ("Dogfighter", "Dogfighter (turn + strafe)"),
             ("Booster", "Booster (boost burst)"),
             ("Voyager", "Voyager (travel + spool)"),
             ("degenerate", "degenerate (parked)")]
    rkeys = "".join(
        f"<span class='rkey'><span class='dot {k}'></span>{html.escape(lbl)}</span>"
        for k, lbl in roles)

    parts = [f"<style>{CSS}</style>", "<div class='emr'><div id='tip'></div>",
             "<div class='wrap'>"]
    parts.append("<p class='eyebrow'>Pokey&rsquo;s Engine Mod Rebalance</p>")
    parts.append("<h1>Engine mod archetypes: declared vs. delivered</h1>")
    parts.append(
        "<p class='lede'>Each tier offers four clear archetypes &mdash; "
        "<strong>Interceptor</strong> (speed), <strong>Dogfighter</strong> "
        "(turn + strafe), <strong>Booster</strong> (boost burst) and "
        "<strong>Voyager</strong> (travel + spool) &mdash; one carrier mod "
        "each; every other mod is parked at a token &ldquo;degenerate&rdquo; "
        "value. The top grid is what a mod declares; the bottom is what the "
        "ship actually gains. Cells read blue where performance improves; "
        "dashed cells are <strong>leak</strong> &mdash; a stat moved by "
        "forward thrust, not its own lever (why the Interceptor spreads "
        "across boost and travel). Hover any cell for the exact factor.</p>")

    parts.append("<div class='legend'>")
    parts.append(
        f"<div class='scale'><span>weaker</span>"
        f"<span class='swatch'>{swatch_r}</span>"
        f"<span style='color:var(--mut)'>&times;1.0</span>"
        f"<span class='swatch'>{swatch_b}</span><span>stronger</span></div>")
    parts.append(f"<div class='roles'>{rkeys}</div>")
    parts.append("</div>")

    parts.append("<h2>Raw modifiers &mdash; what the mod declares</h2>")
    parts.append("<p class='sub'>The pinned values from the mod table "
                 "(no RNG). Spool-up columns (&#8595;) improve as the time "
                 "drops, so a low &times; there still reads blue.</p>")
    parts.append(heatmap(rows, RAW_COLS, "raw"))

    parts.append("<h2>Combined effects &mdash; what the ship actually gets</h2>")
    parts.append("<p class='sub'>The same mods run through the movement model. "
                 "The four archetype carriers per tier light up their cluster; "
                 "the degenerate rows barely register. The Interceptors "
                 "(Nudger, Impeller, Slingshot) spread across boost and travel "
                 "via the dashed leak cells.</p>")
    parts.append(heatmap(rows, COMB_COLS, "comb"))

    parts.append(
        "<p class='note'>Speeds and accelerations share a lever "
        "(both = thrust), so forward speed and forward accel always move "
        "together; the model scores on a representative hull, but every "
        "factor here is ship-independent (mass and drag cancel in the "
        "ratio).</p>")
    parts.append(
        "<div class='foot'>Generated by "
        "<code>tools/engine-mod-rebalance/report.py</code> from the shipped "
        "diff and the x4-analyzer engine sim. Values are relative "
        "(mod-vs-mod exact); absolute boost/travel speeds are not to scale. "
        "Not yet in-game verified.</div>")
    parts.append("</div>")     # wrap
    parts.append(f"<script>{JS}</script>")
    parts.append("</div>")     # emr

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {OUT}  ({len(rows)} mods)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
