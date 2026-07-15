# Publishing to Steam Workshop (and elsewhere)

## The official pipeline: Egosoft WorkshopTool

Egosoft ships a command-line uploader in the **"X Tools"** package on Steam
(Library → Tools → X Tools; "playing" it opens a command prompt in the
tool's directory). It is a Windows executable — on this Linux box run it
under Proton/Wine with Steam running, or publish from a Windows machine.
Steam account must not be limited, and the Steam Workshop Legal Agreement
must be accepted once.

First publish:

```
WorkshopTool publishx4 -path "<...>\X4 Foundations\extensions\my_mod" ^
    -preview "<...>\extensions\my_mod\preview.jpg" -buildcat
```

Updates:

```
WorkshopTool update -path "<...>\extensions\my_mod" -buildcat ^
    -changenote "what changed"
```

What the tool does / requires:

- `-buildcat` packs the extension's game-relevant files into
  `ext_01.cat/.dat` automatically (deleted after upload unless
  `-keepcatfiles`). Loose dev files therefore never need manual packing.
- `preview.jpg`/`.png` required: widescreen, ≥ 640×360.
- `content.xml` `id` is REPLACED with `ws_<workshopitemid>` on first
  publish — commit that change back to the repo afterwards, since updates
  and other mods' `<dependency id="ws_...">` refer to it.
- `version` attribute = version × 100 (v2.50 → `version="250"`).
- Folder name: lowercase, `a-z0-9._- `, ≤ 32 chars.
- After the first upload the item is PRIVATE — set visibility on the
  Workshop item page.

## Alternatives

- **Nexus Mods** (common for X4): zip the extension folder (folder itself
  inside the zip, so it extracts to `extensions/my_mod/`). Ship either
  loose files or a self-built cat/dat. Exclude repo-only files (docs/,
  .git). No id rewriting involved.
- Manual install instructions for users: drop the folder into
  `<game>/extensions/` and enable in the Extensions menu.

## Sources

- [Egosoft wiki: Steam Workshop for X Rebirth and X4](https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Steam%20Workshop%20for%20X%20Rebirth%20and%20X4/)
- [Steam guide mirror of the same document](https://steamcommunity.com/sharedfiles/filedetails/?id=245117855)
