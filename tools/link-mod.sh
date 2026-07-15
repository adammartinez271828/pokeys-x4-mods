#!/usr/bin/env bash
# Symlink a mod dir from this repo into the X4 extensions folder (dev loop
# step 1 in CLAUDE.md). Usage:
#   tools/link-mod.sh <mod-name> [link-name]     # create/replace the link
#   tools/link-mod.sh -u <mod-name|link-name>    # remove the link
set -euo pipefail

GAME_EXT="/games/SteamLibrary/steamapps/common/X4 Foundations/extensions"
REPO="$(cd "$(dirname "$0")/.." && pwd)"

unlink_mode=0
if [[ "${1:-}" == "-u" ]]; then unlink_mode=1; shift; fi
[[ $# -ge 1 ]] || { echo "usage: $0 [-u] <mod-name> [link-name]" >&2; exit 1; }

mod="$1"
link="${2:-$mod}"

if (( unlink_mode )); then
    target="$GAME_EXT/$link"
    [[ -L "$target" ]] || { echo "not a symlink, refusing: $target" >&2; exit 1; }
    rm -v "$target"
    exit 0
fi

[[ -f "$REPO/$mod/content.xml" ]] || {
    echo "$REPO/$mod is not an extension root (no content.xml)" >&2; exit 1; }
[[ -d "$GAME_EXT" ]] || { echo "game extensions dir not found: $GAME_EXT" >&2; exit 1; }

# Workshop-tool folder rules: lowercase, a-z 0-9 . _ - space, max 32 chars
[[ "$link" =~ ^[a-z0-9._\ -]{1,32}$ ]] || {
    echo "link name '$link' breaks folder rules (lowercase a-z0-9._- space, <=32 chars)" >&2
    exit 1; }

if [[ -e "$GAME_EXT/$link" && ! -L "$GAME_EXT/$link" ]]; then
    echo "$GAME_EXT/$link exists and is not a symlink, refusing to touch it" >&2
    exit 1
fi

ln -sfnv "$REPO/$mod" "$GAME_EXT/$link"

if [[ -d "$GAME_EXT/pt_ship_mods_no_rng" && "$mod" == "weapon-mod-rebalance" ]]; then
    echo "NOTE: pt_ship_mods_no_rng is installed and patches equipmentmods.xml too -"
    echo "      disable it in the Extensions menu while testing this mod."
fi
echo "Now enable '$link' in the in-game Extensions menu (restart required)."
