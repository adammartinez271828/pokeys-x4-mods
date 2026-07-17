# Releasing a mod (runbook)

Step-by-step for shipping a new version of a mod to Steam Workshop and Nexus.
Background on the tools and first-publish specifics is in
[`steam-workshop.md`](steam-workshop.md); this is the do-it checklist.

Worked example throughout: **weapon-mod-rebalance** (Workshop id
`ws_3765994517`, folder `weapon-mod-rebalance`).

---

## 0. Machine facts (this box)

- **WorkshopTool is a Windows exe** in Steam's "X Tools" package
  (Library → Tools → X Tools → play = opens a prompt in its dir). It runs
  under Proton/Wine.
- Inside that Proton prompt, drive **`S:` maps to
  `/games/SteamLibrary/steamapps`** — so the mod is at
  `S:\common\X4 Foundations\extensions\weapon-mod-rebalance`.
- The game's `extensions/<mod>` is a **symlink** to the repo dir. Wine
  follows it fine, so publishing "through" it writes WorkshopTool's
  `content.xml` edits (id / date / `lastupdate`) **straight back into the
  repo** — convenient, but means you must commit that re-stamp afterward
  (step 5).
- **Always quote paths** in WorkshopTool commands: "X4 Foundations" has a
  space, and an unquoted `-preview`/`-path` silently truncates at it (this
  is the "preview does not exist" trap).

---

## 1. Validate the change

For weapon-mod-rebalance, the balance harness applies the diff itself and
scores every weapon; exit 0 = all targets pass:

```
uv run --project ~/devel/x4-analyzer python tools/weapon-mod-rebalance/evaluate.py
```

If you changed XML by hand, also confirm it's well-formed:

```
python -c "import xml.dom.minidom; xml.dom.minidom.parse('weapon-mod-rebalance/content.xml')"
python -c "import xml.dom.minidom; xml.dom.minidom.parse('weapon-mod-rebalance/libraries/equipmentmods.xml')"
```

## 2. Bump the version

In the mod's `content.xml`, bump `version` (it's ×100: `v1.01` →
`version="101"`). Update `date` if you like. Commit the content change now,
before publishing, so the repo reflects intent even if a publish step fails.

## 3. Publish to Steam Workshop

From the Proton "X Tools" prompt (paths quoted):

```
WorkshopTool update ^
  -path "S:\common\X4 Foundations\extensions\weapon-mod-rebalance" ^
  -buildcat ^
  -changenote "What changed in this version."
```

- `-buildcat` packs a temp cat/dat and deletes it after upload; loose dev
  files never need manual packing.
- This ships the mod files (incl. the updated `content.xml`). The Workshop
  **page description / images** are edited separately on the item's web
  page, not by this command.
- **First publish only** (new mod, not an update): use `publishx4` with a
  `-preview "...\preview.jpg"` instead of `update`; it uploads **private**
  (set visibility on the web page) and rewrites `content.xml`'s `id` to
  `ws_<workshopid>`. See `steam-workshop.md`.

## 4. Update the Nexus file

Nexus is a plain file host: upload a zip whose root is the extension folder,
so it extracts to `extensions/<mod>/`. Zip only the mod dir (it already holds
just the shipping files; `docs/` and `tools/` live outside it):

```
V=$(grep -oP 'version="\K\d+' weapon-mod-rebalance/content.xml)
zip -r "output/weapon-mod-rebalance-v${V}-nexus.zip" weapon-mod-rebalance -x '*.DS_Store'
```

Upload that zip on the mod's Nexus page → **Files** tab as a new file
version, add a changelog line, and set it as the Main File. (Nexus keeps the
same `content.xml` id; no rewriting. Description/images are edited on the web
page and use the same BBCode as Steam.)

## 5. Commit the WorkshopTool re-stamp

A successful Steam publish/update re-writes `content.xml` in place
(`lastupdate`, sometimes `date`) via the symlink. Commit it so the repo
matches what's live:

```
git add weapon-mod-rebalance/content.xml
git commit -m "weapon-mod: record Workshop re-stamp after v<version> update"
git push
```

## 6. Announce (optional)

Cross-link the Steam and Nexus pages in each other's description. For a new
release worth posting, r/X4Foundations is the venue; attach the mod-table
image (`docs/weapon-mod-rebalance-table.png`, rebuild below if values
changed).

---

## Appendix: regenerate the mod-table image

If mod values changed, rebuild the reference table PNG from its HTML:

```
chromium --headless --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=1240,1180 \
  --screenshot="output/weapon-mod-rebalance-table.png" \
  "file://$PWD/docs/weapon-mod-rebalance-table.html"
```

(Update the numbers in `docs/weapon-mod-rebalance-table.html` first; the
values there are hand-authored, not generated.)

## Copy conventions

Drafted copy the user will publish (descriptions, posts, changelogs) must
**not use em-dashes** — use commas, colons, parentheses, or separate
sentences.
