#!/usr/bin/env bash
# Sync canonical Foxhole styles from gavmor/foxhole-styles into this skill.
#
# The Foxhole design system (fonts, plate baker, print CSS patterns) lives
# in foxhole-styles as the single source of truth. This script vendors the
# pieces the skill needs; the vendored copies ARE committed so the skill
# works standalone. Re-run after any visual change upstream.
#
#   bin/sync-styles.sh
set -euo pipefail

REPO="https://github.com/gavmor/foxhole-styles.git"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/foxhole-styles"
HERE="$(cd "$(dirname "$0")/.." && pwd)"

if [ -d "$CACHE/.git" ]; then
  git -C "$CACHE" pull --ff-only -q
else
  git clone -q "$REPO" "$CACHE"
fi

cp "$CACHE/plate/make_plate.py"      "$HERE/bin/make_plate.py"
cp "$CACHE/print/foxhole-print.css"  "$HERE/references/foxhole-print.css"
mkdir -p "$HERE/fonts"
cp "$CACHE/fonts/"*.ttf              "$HERE/fonts/"

echo "synced from $(git -C "$CACHE" rev-parse --short HEAD)"
