#!/usr/bin/env bash
# MedNarrate: apply the dataset feature bundle. Run from the repository root:
#   bash apply_dataset_feature.sh
# Every file it replaces is first copied into _removed_files_backup/<time>/.
set -euo pipefail
cd "$(dirname "$0")"
BUNDLE="dataset-feature.tar.gz"
[ -f "$BUNDLE" ] || { echo "Missing $BUNDLE next to this script."; exit 1; }
BACKUP="_removed_files_backup/$(date +%Y%m%d-%H%M%S)-dataset"
mkdir -p "$BACKUP"
tar -tzf "$BUNDLE" | while IFS= read -r f; do
  if [ -f "$f" ]; then mkdir -p "$BACKUP/$(dirname "$f")"; cp "$f" "$BACKUP/$f"; fi
done
tar -xzf "$BUNDLE"
echo "Applied. Previous versions saved in $BACKUP"
echo
echo "Next:"
echo "  1) cd mednarrate-backend && source .venv/bin/activate && pip install -r requirements.txt   # scikit-learn is new"
echo "     then restart the backend"
echo "  2) cd ..  &&  flutter gen-l10n && flutter pub get && flutter analyze && flutter test"
echo "  3) Admin portal: cd mednarrate-admin && npx tsc --noEmit && npx jest"
echo "  4) To see the badge: Admin > Feature Flags > report_type_check > ON (rollout 100)"
