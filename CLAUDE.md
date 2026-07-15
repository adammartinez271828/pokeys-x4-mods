# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Pokey's X4: Foundations game mods — one repo, multiple mods.
Each mod is a top-level directory that IS an X4 extension root (contains
`content.xml` + game-relative files), so it can be symlinked individually
into the game's `extensions/` folder and published to Steam Workshop on its
own. Shared documentation lives in `docs/`; game-file reference copies in
`docs/reference/`. Targets game **v9.0**.

X4 mods are XML diff patches plus optional Lua/MD scripts — nothing
compiles. "Building" = packing cat/dat (the Workshop tool does it);
"testing" = launching the game with the extension enabled, or running the
analysis tooling in the sibling repo `~/devel/x4-analyzer`.

Layout model (based on kuertee's x4-mod-ui-extensions repo, adapted for
multi-mod):

```
pokeys-x4-mods/
  CLAUDE.md  README.md  docs/
  <mod-name>/              # one dir per mod = extension root
    content.xml
    libraries/*.xml        # <diff> patches
    t/0001-l044.xml        # new display strings (diff form)
    preview.jpg            # Workshop preview (>=640x360)
```

## Planned / existing mods

- **weapon-mod-rebalance** — rebalance the `<weapon>` section of
  `libraries/equipmentmods.xml` so equipment mods are meaningful choices.
  Vanilla analysis, design thesis (tier-pinned damage primaries,
  DPS-orthogonal secondaries, no roll ranges crossing 1.0) and balance
  targets: `docs/weapon-mod-rebalance-design.md`. Not scaffolded yet.

## Critical domain knowledge (validated in-game — do not "fix")

- **Reload mods are RATE-semantic on every weapon** (corrected 2026-07,
  in-game: S Plasma Cannon Mk1, `reload time="2.6"`, fired 5 shots in
  10.4 s bare and ~8.7 s under reload ×1.2 — the game DIVIDES a stored
  time by the multiplier). Optimal roll is always the range MAX; a reload
  multiplier can never flip meaning between weapons. The old
  "multiplies the stored field literally" rule (and x4-analyzer's
  `optimal_mult` reload/time branch) is WRONG for `<reload time>`
  weapons. Damage/coolrate/chargetime multipliers behave as expected
  (bigger damage/coolrate = better, smaller chargetime = better).
- **Bonus semantics in equipmentmods.xml:** a `<bonus chance="1.0" max="N">`
  block with ≤ N children is FORCED (all always apply); a larger weighted
  pool is optional loot. Mod qualities 1/2/3 = Basic/Enhanced/Exceptional
  (weapon *names* use Mk for the weapon's own mark — different thing).
- **Adding NEW bonus children to an existing mod ware works in-game**
  (verified 2026-07: `<add sel=".../bonus"><reload .../></add>` plus a
  `bonus/@max` bump on Gregale — the new reload bonus shows up in the
  weapon-mod UI). Ware structure is not fixed; only new *wares* are
  expensive (wares.xml, text pages, drops).
- **Clip weapons** (`<ammunition value reload>`): the clip reload time is
  fixed — reload mods only scale the intra-burst interval; cooling mods do
  nothing when the bullet has no per-shot heat. Explosive weapons (Blast
  Mortar, flak) keep their damage in `<areadamage>`, not `<damage>`.
- **Heat model:** weapons DO cool between shots once `cooldelay` has
  elapsed since the last shot: net heat per shot =
  `heat − coolrate × max(0, interval − cooldelay)` (verified in-game
  2026-07: S Plasma Cannon Mk1 reaches 9800/10000 after 5 bare shots —
  no overheat — but overheats on the 5th shot under a +20% fire-rate mod
  because the shorter gap cools less; both match the formula exactly).
  "No cooling while firing" only holds for fast weapons whose interval ≤
  `cooldelay` (e.g. TER S EM Gun, where the old rule was validated). At
  overheat: offline for `overheatcooldelay`, cools at `coolrate`,
  re-enables at `reenable`. x4-analyzer's weaponsim still uses the old
  no-cooling-while-firing model — slow heat weapons are mis-simulated.
- **Per-weapon mod restriction is NOT possible in game data** — verified:
  equipmentmods.xml has no compatibility hook and the install menu buckets
  by engine-side `modclass` only. Soft-gate via maluses that bind on the
  target archetype, or hard-gate by patching
  `ui/addons/ego_detailmonitor/menu_ship_configuration.lua`.
- Rebalancing equipmentmods.xml DOES retroactively change already-installed
  mod instances (verified in-game 2026-07: a max-roll vanilla Cowboy at
  +100% fire rate read +20% after the rebalance = the new range max).
  BUT newly ADDED bonus children do NOT attach to existing installs
  (verified: an installed Cowboy did not gain the added damage rider) —
  the save stores WHICH bonuses an instance rolled, not their magnitudes;
  values re-derive from the current table, added children only appear on
  newly crafted installs. Mid-range-roll mapping still unknown.

## Machine-specific paths

- Game install (Steam, Linux):
  `/games/SteamLibrary/steamapps/common/X4 Foundations`; extensions live in
  `<game>/extensions/`. Official DLC = `ego_dlc_*`; ~60 third-party mods
  are also installed — watch for conflicts (`pt_ship_mods_no_rng` patches
  equipmentmods.xml too; disable it when testing the rebalance).
- X4 user dir (logs, saves): `~/.config/EgoSoft/X4/` (capital S).
- Sibling analysis repo: `~/devel/x4-analyzer` (uv-managed Python).

## Dev loop

1. Symlink the mod dir into the game:
   `ln -s ~/devel/pokeys-x4-mods/<mod-name> "/games/SteamLibrary/steamapps/common/X4 Foundations/extensions/<folder>"`
   — folder name lowercase, chars `a-z0-9._- `, ≤32; loose XML works, no
   cat packing needed for local play.
2. Enable it in the in-game Extensions menu (restart required).
3. Verify patches applied: launch with `-debug all -logfile debug.log` and
   grep the log (in the X4 user dir) for diff-patch `[=ERROR=]` lines —
   a silent sel mismatch is the most common mod bug.
4. For weapon/equipment changes, cross-check numbers without launching the
   game: the x4-analyzer repo extracts and simulates weapon×mod firing
   cycles (`uv run x4-analyzer gamedata-dashboard`, and
   `x4analyzer.gamedata.weaponsim` / `weapons.extract_weapon_mods` as a
   library). Caveat: its `GameFiles(game_dir)` loads only `ego_dlc_*` by
   default — pass `extensions=[*dlcs, "<folder>"]` explicitly to include a
   mod under test.

## Conventions

- Keep diffs surgical (`<replace sel>` on specific attributes) and note the
  vanilla value in an XML comment beside every change. Real examples:
  `docs/reference/example-diff-pt_ship_mods_no_rng.xml` (attribute
  replaces) and `docs/reference/equipmentmods-timelines-diff.xml`
  (`<add sel>` of new nodes).
- Prefer rebalancing EXISTING wares over adding new ones (new wares need
  wares.xml entries, text pages, and drop/craft integration).
- New display strings: `t/0001-l044.xml` diff under one custom page id per
  mod (pick a high unique id, e.g. 100027xx).
- `content.xml` `version` is ×100 (v1.20 → `version="120"`); bump every
  release. The `id` is replaced with `ws_<workshopid>` on first Workshop
  publish — see `docs/steam-workshop.md` for the whole pipeline.
- `docs/` is never shipped: the Workshop tool packs only game-relevant
  files, but keep it out of any manual zip for Nexus.
- Commit locally without asking; push/publish only when Adam asks.
