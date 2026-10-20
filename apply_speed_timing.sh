#!/bin/bash
# Applies the speed + timing + phone-support changes. Run from the MedNarrate-main folder:
#   bash apply_speed_timing.sh
set -e
cd "$(dirname "$0")"
BK="_removed_files_backup/speed-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BK"
for f in $(tar tzf speed-timing-2026-10-18.tar.gz); do
  if [ -f "$f" ]; then mkdir -p "$BK/$(dirname "$f")"; cp "$f" "$BK/$f"; fi
done
tar xzf speed-timing-2026-10-18.tar.gz
echo "Applied. Originals backed up in $BK"
