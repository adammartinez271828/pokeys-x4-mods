# Pokey's X4 mods

Mods for X4: Foundations (v9.0), one directory per mod — each directory is
a complete X4 extension that can be symlinked into the game's `extensions/`
folder for development and published to Steam Workshop / Nexus on its own.

| Mod | Status | What it does |
|---|---|---|
| weapon-mod-rebalance | v1 built, awaiting in-game verification | Rebalances weapon equipment mods into meaningful choices ([design](docs/weapon-mod-rebalance-design.md), [shipped table](docs/weapon-mod-rebalance-v1.md)) |

## Docs

- [X4 extension anatomy: content.xml, diff patches, load order](docs/x4-mod-structure.md)
- [Publishing to Steam Workshop](docs/steam-workshop.md)
- [Weapon-mod rebalance: analysis & design](docs/weapon-mod-rebalance-design.md)
- `docs/reference/` — vanilla `equipmentmods.xml` (v9.0) and real diff-patch examples

Per-mod tooling lives under `tools/<mod-name>/`;
`tools/weapon-mod-rebalance/evaluate.py` is the balance acceptance harness
(run: `uv run --project ~/devel/x4-analyzer python tools/weapon-mod-rebalance/evaluate.py`;
exit 0 = all targets pass) and `report.py` beside it renders the
vanilla-vs-rebalance review dashboard into `output/`.
Analysis/validation tooling lives in the sibling repo
[`x4-analyzer`](../x4-analyzer) (weapon×mod firing-cycle simulator and
comparison dashboard built from the game files).
