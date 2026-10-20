#!/bin/bash
# Applies the new start screen. Run from the MedNarrate-main folder: bash apply_splash.sh
set -e
cd "$(dirname "$0")"
BK="_removed_files_backup/splash-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BK"
for f in $(tar tzf splash-2026-10-18.tar.gz); do
  if [ -f "$f" ]; then mkdir -p "$BK/$(dirname "$f")"; cp "$f" "$BK/$f"; fi
done
tar xzf splash-2026-10-18.tar.gz
echo "Applied. Originals backed up in $BK"
