#!/usr/bin/env python
"""Vanilla-vs-rebalance review dashboard for weapon-mod-rebalance.

Renders output/weapon-mod-review.html (gitignored) in the style of
x4-analyzer's gamedata dashboard: pick a weapon, see its firing-cycle
stats bare and under every DPS-affecting mod at its OPTIMAL roll - except
here every cell shows the REBALANCED value with the vanilla-mod value
underneath, and every column header shows the old and new roll ranges.
A summary table of all changed wares sits above the per-weapon view.

Run from the repo root:

    uv run --project ~/devel/x4-analyzer python tools/weapon-mod-rebalance/report.py
"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate import (DEFAULT_DIFF, DEFAULT_GAME_DIR, REPO, _PARSER,  # noqa: E402
                      apply_diff, parse_weapon_mods)
from evaluate import eligible_pair, is_mining_weapon  # noqa: E402

from x4analyzer.gamedata.catalog import GameFiles  # noqa: E402
from x4analyzer.gamedata.extract import load_textdb  # noqa: E402
from x4analyzer.gamedata.weapons import _mod_ware_names, extract_weapons  # noqa: E402
from x4analyzer.gamedata.weaponsim import (SIM_STATS, guaranteed_stats,  # noqa: E402
                                           mod_multipliers, reload_kind,
                                           stat_vector)
from x4analyzer.viz.weaponmods import _ROWS_JS, _notes  # noqa: E402

OUT = REPO / "output" / "weapon-mod-review.html"
_SIZE_ORDER = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4, "?": 5}
QNAMES = {1: "Basic", 2: "Enhanced", 3: "Exceptional"}


def _round(v):
    return None if v is None else round(v, 3)


def _rng(e) -> str:
    if e["min"] == e["max"]:
        return f"×{e['min']:g}"
    return f"×{e['min']:g}–{e['max']:g}"


def _bonus_str(m) -> str:
    kind = "forced" if m["forced"] else "pool"
    if not m["bonuses"]:
        return ""
    return f"{kind}: " + "; ".join(
        f"{b['stat']} {_rng(b)}" for b in m["bonuses"])


def _mod_changed(v, m) -> bool:
    if (v["min"], v["max"]) != (m["min"], m["max"]):
        return True
    return [(b["stat"], b["min"], b["max"]) for b in v["bonuses"]] != \
           [(b["stat"], b["min"], b["max"]) for b in m["bonuses"]]


def build() -> str:
    gf = GameFiles(Path(DEFAULT_GAME_DIR))
    tdb = load_textdb(gf)
    names = _mod_ware_names(gf, tdb)
    weapons = extract_weapons(gf, tdb)

    vanilla_doc = etree.fromstring(
        gf.read_bytes("libraries/equipmentmods.xml"), _PARSER)
    for ext in gf.extensions:
        p = f"extensions/{ext}/libraries/equipmentmods.xml"
        if p in gf:
            apply_diff(vanilla_doc,
                       etree.fromstring(gf.read_bytes(p), _PARSER), ext)
    modded_doc = deepcopy(vanilla_doc)
    errs = apply_diff(modded_doc, etree.parse(str(DEFAULT_DIFF),
                                              _PARSER).getroot(), "mod diff")
    if errs:
        raise SystemExit("\n".join(errs))

    vmods = {m["ware"]: m for m in parse_weapon_mods(vanilla_doc, names)}
    mmods = {m["ware"]: m for m in parse_weapon_mods(modded_doc, names)}

    # columns: mods whose guaranteed effects touch the firing cycle in
    # either version (same criterion as the stock dashboard)
    cols = [w for w in vmods
            if set(guaranteed_stats(vmods[w])) & set(SIM_STATS)
            or set(guaranteed_stats(mmods[w])) & set(SIM_STATS)]
    cols.sort(key=lambda w: (mmods[w]["quality"], mmods[w]["stat"], w))

    weapons.sort(key=lambda w: (_SIZE_ORDER.get(w["size"], 9),
                                w["wclass"], w["name"]))
    def _heat_note(w):
        """Reload mods are rate-semantic everywhere (verified in-game), so
        the note worth surfacing per weapon is the between-shot cooling."""
        if not ((w.get("heat") or 0) > 0 and (w.get("overheat") or 0) > 0):
            return None
        if w.get("reload_rate"):
            interval = 1.0 / w["reload_rate"]
        else:
            interval = w.get("reload_time") or 0.0
        interval += w.get("chargetime") or 0.0
        cd = w.get("cooldelay") or 0.0
        if interval > cd:
            return (f"Cools between shots ({interval:g} s interval > "
                    f"{cd:g} s cooldelay), so fire-rate mods also cost "
                    "heat by shrinking the cooling window - the overheat "
                    "numbers include that.")
        return None

    wrows = []
    for w in weapons:
        bare = [_round(x) for x in stat_vector(w)]
        per = {}
        for ware in cols:
            vvec = [_round(x) for x in
                    stat_vector(w, mod_multipliers(vmods[ware], w))]
            mvec = [_round(x) for x in
                    stat_vector(w, mod_multipliers(mmods[ware], w))]
            per[ware] = 0 if vvec == bare and mvec == bare else [vvec, mvec]
        group = (f"{w['size']} "
                 f"{'turrets' if w['wclass'] == 'turret' else 'weapons'}")
        notes = _notes(w)
        rn = _heat_note(w)
        if rn:
            notes.insert(0, rn)
        wrows.append({"id": w["macro"], "n": w["name"], "g": group,
                      "rk": reload_kind(w), "notes": notes,
                      "bare": bare, "mods": per})

    mrows = []
    for ware in cols:
        v, m = vmods[ware], mmods[ware]
        mrows.append({
            "w": ware, "n": m["name"], "q": m["quality"], "s": m["stat"],
            "vr": _rng(v), "mr": _rng(m),
            "vb": _bonus_str(v), "mb": _bonus_str(m),
            "chg": _mod_changed(v, m),
            "forced": ([{"s": b["stat"], "min": b["min"], "max": b["max"]}
                        for b in m["bonuses"]] if m["forced"] else []),
        })

    # niche stats on the rebalanced table (metric: full-cycle DPS vs
    # shields, steady-state fallback), merged into the changed-wares table
    def metric(vec):
        return vec[10] if vec[10] is not None else vec[15]

    strict_gun = {w_: 0 for w_ in cols}
    strict_tur = {w_: 0 for w_ in cols}
    strict_names = {w_: set() for w_ in cols}
    tied = {w_: 0 for w_ in cols}
    gains = {w_: [] for w_ in cols}
    weapon_by_id = {w["macro"]: w for w in weapons}
    for wr in wrows:
        b = metric(wr["bare"])
        if not b:
            continue
        wrec = weapon_by_id[wr["id"]]
        vals = {}
        for ware in cols:
            if not eligible_pair(mmods[ware], wrec):
                continue  # combat mod on a mining weapon: not a real pick
            c = wr["mods"][ware]
            mvec = wr["bare"] if c == 0 else c[1]
            vals[ware] = metric(mvec) or 0.0
            gains[ware].append((vals[ware] / b - 1.0, wr["n"],
                                wrec["wclass"]))
        for q in (1, 2, 3):
            tier = [x for x in vals if mmods[x]["quality"] == q]
            best = max((vals[x] for x in tier), default=0.0)
            if best <= 0:
                continue
            top = [x for x in tier if vals[x] >= best / 1.005]
            for x in top:
                tied[x] += 1
            if len(top) == 1:
                if wrec["wclass"] == "turret":
                    strict_tur[top[0]] += 1
                else:
                    strict_gun[top[0]] += 1
                strict_names[top[0]].add(wr["n"])

    def _targets(entries, strict_set=frozenset()):
        """Top-5 list as lines; +-0.0% entries and duplicate names dropped.
        Entries where the mod is the strict tier winner come first (bold)."""
        seen, out = set(), []
        for g, n, *_ in entries:
            if abs(g) < 0.0005 or n in seen:
                continue
            seen.add(n)
            line = f"{n} ({g:+.1%})"
            out.append(f"<b>{line}</b>" if n in strict_set else line)
            if len(out) == 5:
                break
        return "<br>".join(out)

    # one row per changed ware (orthogonal-primary mods have no niche
    # numbers - their guaranteed effects never move the firing cycle)
    summary = []
    for ware in sorted(vmods, key=lambda w: (vmods[w]["quality"], w)):
        v, m = vmods[ware], mmods[ware]
        if not _mod_changed(v, m):
            continue
        if ware in cols:
            sn = strict_names[ware]
            best_order = sorted(gains[ware],
                                key=lambda e: (e[1] not in sn, -e[0]))
            best_guns = [e for e in best_order if e[2] == "weapon"]
            best_turrets = [e for e in best_order if e[2] == "turret"]
            niche = (f"<td>{strict_gun[ware]}</td><td>{strict_tur[ware]}</td>"
                     f"<td>{tied[ware]}</td>"
                     f"<td>{_targets(best_guns, sn)}</td>"
                     f"<td>{_targets(best_turrets, sn)}</td>")
        else:
            niche = ("<td class='mut'>—</td><td class='mut'>—</td>"
                     "<td class='mut'>—</td><td></td><td></td>")
        summary.append(
            f"<tr><td>{m['name']}<br><span class='mut'>{ware}</span></td>"
            f"<td class='q{m['quality']}'>{QNAMES[m['quality']]}</td>"
            f"<td>{m['stat']} <s class='mut'>{_rng(v)}</s> "
            f"<b>{_rng(m)}</b></td>"
            f"<td><span class='mut'>{_bonus_str(v) or '—'}</span><br>"
            f"<b>{_bonus_str(m) or '—'}</b></td>{niche}</tr>")

    def emb(obj) -> str:
        return json.dumps(obj, separators=(",", ":")).replace("</", "<\\/")

    return _HTML_TEMPLATE.format(
        n_changed=len(summary), n_weapons=len(wrows),
        summary="\n".join(summary),
        weapons=emb(wrows), mods=emb(mrows), rows_js=_ROWS_JS)


_HTML_TEMPLATE = """<!DOCTYPE html><html><head><meta charset='utf-8'>
<title>weapon-mod-rebalance - vanilla vs v1 review</title>
<style>
body{{font-family:sans-serif;background:#1b1b1b;color:#ddd;margin:0;}}
header{{padding:12px 16px 0 16px;}}
h2{{margin:0 0 4px 0;font-size:20px;}} h2 small{{color:#999;font-weight:normal;}}
h3{{font-size:15px;margin:18px 0 4px 0;}}
section{{padding:8px 16px;}}
label{{color:#999;margin-right:10px;user-select:none;}}
select{{background:#2a2a2a;color:#ddd;border:1px solid #555;padding:4px 8px;
  font-size:14px;max-width:460px;}}
.note{{color:#999;font-size:12px;margin:6px 0;}}
.mut{{color:#888;}} s.mut{{color:#777;}}
table{{border-collapse:collapse;font-size:13px;}}
th,td{{border:1px solid #3a3a3a;padding:5px 9px;text-align:right;
  white-space:nowrap;}}
th{{background:#242424;font-weight:normal;}}
#summary td{{text-align:left;vertical-align:top;}}
#stats thead th{{vertical-align:top;text-align:center;cursor:default;}}
#stats thead th .mn{{font-weight:bold;display:block;}}
#stats thead th .rng{{color:#999;font-size:11px;display:block;}}
#stats thead th .old{{color:#777;font-size:11px;display:block;
  text-decoration:line-through;}}
.q1{{color:#8fd18f;}} .q2{{color:#6ab7e8;}} .q3{{color:#d8a35a;}}
#stats tbody th{{text-align:left;}}
#stats td.base{{background:#252525;font-weight:bold;}}
.up{{color:#4ecf71;}} .down{{color:#ff6b6b;}} .same{{color:#999;}}
.delta{{font-size:11px;display:block;}}
.van{{font-size:11px;display:block;color:#777;}}
th.noeff,td.noeff{{color:#666;}} th.noeff .rng,th.noeff .old{{color:#666;}}
.tblwrap{{overflow-x:auto;}}
</style></head><body>
<header><h2>weapon-mod-rebalance <small>vanilla vs v1 - {n_changed} wares
changed, {n_weapons} weapons/turrets simulated at optimal rolls</small></h2>
</header>
<section>
<h3>Changed wares &amp; niche map</h3>
<p class='note'>Struck-through = vanilla, bold = rebalanced. Pools are
optional weighted loot; forced bonuses always apply. Niche columns use
full-cycle DPS vs shields at the fixed roll (steady-state where no
heat/clip cycle): "strict wins" / "best-or-tied" count weapons where the
mod tops its OWN quality tier (>0.5% margin / within 0.5%); best/worst
targets show where installing the mod gains the most vs the bare weapon,
split into ship-mounted main guns and turrets. Bold best targets are
weapons where the mod is the STRICT winner of its tier; those are listed
first. Mining weapons/turrets only count for mods that can roll a mining
bonus. Orthogonal-primary mods (—) never move the firing
cycle.</p>
<div class='tblwrap'><table id='summary'>
<thead><tr><th>Mod</th><th>Quality</th><th>Primary</th><th>Bonuses</th>
<th>Strict wins<br>main guns</th><th>Strict wins<br>turrets</th>
<th>Best or<br>tied</th>
<th>Best main-gun targets</th><th>Best turret targets</th></tr>
</thead><tbody>
{summary}
</tbody></table></div>
<h3>Per-weapon firing cycle</h3>
<p>
<label for='weapon'>Weapon:</label><select id='weapon'></select>
&nbsp;&nbsp;<label>Mod quality:</label>
<label><input type='checkbox' id='q1' checked> Basic</label>
<label><input type='checkbox' id='q2' checked> Enhanced</label>
<label><input type='checkbox' id='q3' checked> Exceptional</label>
&nbsp;&nbsp;<label><input type='checkbox' id='diffonly'> changed cells only</label>
</p>
<div id='notes'></div>
<p class='note'>Each cell: rebalanced value (delta vs bare); the muted
"van" line is what the vanilla mod gave. Mods apply at their OPTIMAL roll
for the selected weapon (reload rate wants max, reload time wants min -
multipliers are literal). Optional pools are NOT in the numbers.</p>
<div class='tblwrap'><table id='stats'></table></div>
</section>
<script>
const WEAPONS = {weapons};
const MODS = {mods};
{rows_js}
const QNAMES = {{1:'Basic', 2:'Enhanced', 3:'Exceptional'}};
const sel = document.getElementById('weapon');
const groups = {{}};
WEAPONS.forEach((w, i) => {{
  if (!groups[w.g]) {{
    groups[w.g] = document.createElement('optgroup');
    groups[w.g].label = w.g;
    sel.appendChild(groups[w.g]);
  }}
  const o = document.createElement('option');
  o.value = i; o.textContent = w.n + '  [' + w.id + ']';
  groups[w.g].appendChild(o);
}});
function fmt(v, dec) {{
  return v.toLocaleString('en-US',
    {{minimumFractionDigits: dec, maximumFractionDigits: dec}});
}}
function visibleMods() {{
  return MODS.filter(m => document.getElementById('q' + m.q).checked);
}}
function render() {{
  const w = WEAPONS[+sel.value];
  const diffonly = document.getElementById('diffonly').checked;
  let mods = visibleMods();
  if (diffonly)
    mods = mods.filter(m => {{
      const c = w.mods[m.w];
      return c !== 0 && JSON.stringify(c[0]) !== JSON.stringify(c[1]);
    }});
  document.getElementById('notes').innerHTML =
    w.notes.map(n => '<p class="note">' + n + '</p>').join('');
  const head = ['<tr><th></th><th><span class="mn">Bare</span></th>'];
  mods.forEach(m => {{
    const noeff = w.mods[m.w] === 0;
    const title = ('vanilla: ' + m.s + ' ' + m.vr
      + (m.vb ? ' | ' + m.vb : '') + '\\nnew: ' + m.s + ' ' + m.mr
      + (m.mb ? ' | ' + m.mb : '') + '\\n' + m.w);
    head.push('<th' + (noeff ? ' class="noeff"' : '') + ' title="'
      + title.replace(/"/g, '&quot;') + '">'
      + '<span class="mn">' + m.n + ' <span class="q' + m.q + '">'
      + QNAMES[m.q] + '</span></span>'
      + '<span class="rng">' + m.s + ' ' + m.mr + '</span>'
      + '<span class="old">' + m.vr + '</span>'
      + (noeff ? '<span class="rng">(no effect)</span>' : '') + '</th>');
  }});
  head.push('</tr>');
  const body = [];
  ROWS.forEach(r => {{
    const [idx, label, dec, dir, suffix] = r;
    const pct = suffix === ' %';
    const scale = pct ? 100 : 1;
    const bare = w.bare[idx];
    const cells = ['<tr><th>' + label + '</th>'];
    cells.push('<td class="base">' + (bare === null ? '\\u2014'
      : fmt(bare * scale, dec) + suffix) + '</td>');
    mods.forEach(m => {{
      const c = w.mods[m.w];
      const vvec = c === 0 ? w.bare : c[0];
      const mvec = c === 0 ? w.bare : c[1];
      const v = mvec[idx], van = vvec[idx];
      const noeff = c === 0;
      if (v === null) {{
        cells.push('<td' + (noeff ? ' class="noeff"' : '')
          + '>\\u2014</td>');
        return;
      }}
      let delta = '';
      if (bare !== null && bare !== 0 && Math.abs(v - bare) > 1e-9) {{
        const p = (v / bare - 1) * 100;
        const cls = dir === 0 ? 'same' : (p * dir > 0 ? 'up' : 'down');
        delta = '<span class="delta ' + cls + '">'
          + (p >= 0 ? '+' : '') + p.toFixed(1) + '%</span>';
      }}
      let vline = '';
      if (van !== null && Math.abs(van - v) > Math.abs(v) * 1e-3 + 1e-9)
        vline = '<span class="van">van ' + fmt(van * scale, dec) + suffix
          + '</span>';
      cells.push('<td' + (noeff ? ' class="noeff"' : '') + '>'
        + fmt(v * scale, dec) + suffix + delta + vline + '</td>');
    }});
    cells.push('</tr>');
    body.push(cells.join(''));
  }});
  document.getElementById('stats').innerHTML =
    '<thead>' + head.join('') + '</thead><tbody>' + body.join('')
    + '</tbody>';
}}
sel.addEventListener('change', render);
['q1', 'q2', 'q3', 'diffonly'].forEach(id =>
  document.getElementById(id).addEventListener('change', render));
if (WEAPONS.length) {{ sel.value = 0; render(); }}
</script></body></html>"""


def main() -> int:
    html = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
