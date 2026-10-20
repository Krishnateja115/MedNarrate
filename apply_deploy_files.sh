#!/usr/bin/env bash
# MedNarrate: apply the dataset feature bundle. Run from the repository root:
#   bash apply_deploy_files.sh
# Every file it replaces is first copied into _removed_files_backup/<time>/.
set -euo pipefail
cd "$(dirname "$0")"
BUNDLE="deploy-files.tar.gz"
[ -f "$BUNDLE" ] || { echo "Missing $BUNDLE next to this script."; exit 1; }
BACKUP="_removed_files_backup/$(date +%Y%m%d-%H%M%S)-deploy"
mkdir -p "$BACKUP"
tar -tzf "$BUNDLE" | while IFS= read -r f; do
  if [ -f "$f" ]; then mkdir -p "$BACKUP/$(dirname "$f")"; cp "$f" "$BACKUP/$f"; fi
done
tar -xzf "$BUNDLE"
echo "Applied. Previous versions (if any) saved in $BACKUP"
echo "Next: open DEPLOYMENT_STEPS.md and follow it from Part 1."
