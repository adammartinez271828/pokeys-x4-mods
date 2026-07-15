# X4 extension anatomy

An X4 mod ("extension") is a folder under `<game>/extensions/` whose files
mirror the game's virtual file system. At load, the game merges base cats,
official DLC, then third-party extensions; **later wins**, and loose files
override catalogs. Alphabetical folder order approximates load order unless
`content.xml` dependencies force otherwise (some mods prefix `z_`/`zzz_` to
load late).

## Minimum viable mod

```
my_mod/
  content.xml            # manifest (required)
  libraries/whatever.xml # <diff> patch against the game file of the same path
```

Loose XML files work in-game as-is. For distribution the files are packed
into `ext_01.cat` + `ext_01.dat` (text index + concatenated payloads —
see `x4analyzer/gamedata/catalog.py` for the exact format). `subst_01.cat`
is a variant for FULL-FILE substitution (textures, models); XML patches
belong in `ext_*` cats, substitution cats bypass diffing entirely.

## content.xml

Annotated real-world example (from the Crystal Rarities workshop mod):

```xml
<?xml version="1.0" encoding="utf-8"?>
<content id="ws_2069554360"        <!-- pre-publish: any id; the Workshop
                                        tool replaces it with ws_<itemid> -->
         name="Crystal Rarities"   <!-- Workshop item title -->
         description="[h1]...[/h1]&#13;&#10;..."  <!-- Steam BBCode; &#10; = newline -->
         author="Drewgamer"
         version="300"             <!-- v3.00 x 100 -->
         date="2021-04-12"
         save="0"                  <!-- 0/false: removable from a save;
                                        1: the save will depend on the mod -->
         lastupdate="1618266009">
  <text language="44" name="..." description="..." author="..."/>
  <!-- one <text> per language id; 44 = English, 49 = German, ... -->
  <dependency id="ego_dlc_split" optional="true" name="Split Vendetta"/>
  <!-- workshop deps use id="ws_<itemid>"; hard deps omit optional -->
</content>
```

Folder-name rules (enforced by the Workshop tool): lowercase, characters
`a-z 0-9 . _ - space`, max 32 chars.

## Diff patch syntax

Extension copies of game XML files are patch documents:

```xml
<?xml version="1.0" encoding="utf-8"?>
<diff>
  <!-- replace an attribute (note: vanilla max is 1.2) -->
  <replace sel="/equipmentmods/weapon/damage[@ware='mod_weapon_damage_01_mk1']/@max">1.35</replace>
  <!-- replace a whole node -->
  <replace sel="//ware[@id='foo']/price"><price min="10" average="20" max="30"/></replace>
  <!-- add nodes into a parent -->
  <add sel="/equipmentmods/weapon">
    <damage ware="mod_weapon_damage_new" quality="2" min="1.3" max="1.3"/>
  </add>
  <!-- remove a node -->
  <remove sel="//ware[@id='foo']/restriction"/>
</diff>
```

- `sel` is XPath against the MERGED document (base + earlier extensions).
- A non-matching sel fails silently in-game unless you check the debug log
  (`-debug all -logfile debug.log`, grep for diff/patch errors).
- Real examples in `docs/reference/`:
  - `example-diff-pt_ship_mods_no_rng.xml` — attribute replaces across the
    whole equipmentmods weapon section (a no-RNG mod: sets min = max).
  - `equipmentmods-timelines-diff.xml` — Egosoft's own DLC diff adding new
    mod entries via `<add sel="/equipmentmods/weapon">`.

## Text (localization)

New display strings go in `t/0001-l044.xml` (English; other languages get
their own `-l<id>` files) in diff form:

```xml
<diff>
  <add sel="/language">
    <page id="10002700" title="Pokeys mods">
      <t id="1">My New Mod Name</t>
    </page>
  </add>
</diff>
```

Reference them from game data as `{10002700,1}`. Pick ONE unique high page
id per mod and never collide with the game's pages (weapon names live on
20105, ware names on 20201, etc.).

## Load order & conflicts

- Two mods patching the same node: the later-loaded wins for `replace`;
  `add`s accumulate. `pt_ship_mods_no_rng` (installed locally) patches
  `libraries/equipmentmods.xml` mins — disable it when testing a weapon-mod
  rebalance, or results are the merge of both.
- `content.xml` `<dependency>` entries force load AFTER the dependency.

## Savegames

`save="0"` marks the extension as removable. A *rebalance* of equipment
mods DOES affect mod instances already installed on ships in an existing
save — verified in-game (2026-07, weapon-mod-rebalance): a vanilla
max-roll Cowboy reload mod showing +100% fire rate dropped to +20%, the
new range max, on load. Rolled multipliers are not baked into the save at
their old values. (Verified at the range max; how a mid-range roll maps
into a changed range is still unknown.)
