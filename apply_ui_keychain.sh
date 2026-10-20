#!/usr/bin/env bash
# Applies the dashboard buttons, keychain-prompt fix and Upload / Original report polish.
# Run from the repository root:  bash apply_ui_keychain.sh
set -euo pipefail
cd "$(dirname "$0")"
[ -f ui-keychain-2026-10-18.tar.gz ] || { echo "Missing ui-keychain-2026-10-18.tar.gz next to this script."; exit 1; }
BACKUP="_removed_files_backup/ui-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
for f in $(tar tzf ui-keychain-2026-10-18.tar.gz); do
  if [ -f "$f" ]; then mkdir -p "$BACKUP/$(dirname "$f")"; cp "$f" "$BACKUP/$f"; fi
done
tar xzf ui-keychain-2026-10-18.tar.gz
echo "Installed. Previous copies of the files are in $BACKUP"
echo "Now run:  flutter analyze && flutter test && flutter run -d macos"
