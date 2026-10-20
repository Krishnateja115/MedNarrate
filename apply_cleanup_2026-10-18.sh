#!/usr/bin/env bash
# MedNarrate: apply the 2026-10-18 audit, cleanup and read-aloud bundle.
# Run from the repository root:   bash apply_cleanup_2026-10-18.sh
# Nothing is deleted. Files that are no longer needed are MOVED into
# _removed_files_backup/<time>/ so you can look at them or put them back.
set -euo pipefail
cd "$(dirname "$0")"
BUNDLE="cleanup-2026-10-18.tar.gz"
[ -f "$BUNDLE" ] || { echo "Missing $BUNDLE next to this script."; exit 1; }
BACKUP="_removed_files_backup/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"

echo "1/4  Moving out files that are no longer needed (backup: $BACKUP)"
while IFS= read -r f; do
  if [ -n "$f" ] && [ -e "$f" ]; then
    mkdir -p "$BACKUP/$(dirname "$f")"
    mv "$f" "$BACKUP/$f"
    echo "     removed: $f"
  fi
done <<'LIST'
mednarrate-backend/capture_qwen.py
mednarrate-backend/capture_qwen_local.py
mednarrate-backend/capture_qwen_multi.py
mednarrate-backend/check_data.py
mednarrate-backend/check_db.py
mednarrate-backend/check_db2.py
mednarrate-backend/check_help.py
mednarrate-backend/check_llm.py
mednarrate-backend/check_schema.py
mednarrate-backend/check_sqlite.py
mednarrate-backend/clear_llm.py
mednarrate-backend/create_user.py
mednarrate-backend/debug_groq_200.py
mednarrate-backend/debug_groq_400.py
mednarrate-backend/debug_planner.py
mednarrate-backend/debug_qwen_structure.py
mednarrate-backend/debug_qwen_structure_native.py
mednarrate-backend/download_model.py
mednarrate-backend/fetch_prompt.py
mednarrate-backend/fix_migration.py
mednarrate-backend/get_groq_models.py
mednarrate-backend/groq_resp.txt
mednarrate-backend/health_check.py
mednarrate-backend/health_check_system.py
mednarrate-backend/inspect_report3.py
mednarrate-backend/list_models.py
mednarrate-backend/llm_out_fixed.txt
mednarrate-backend/llm_out_fixed2.txt
mednarrate-backend/llm_out_fixed3.txt
mednarrate-backend/parser_fix.py
mednarrate-backend/parser_fix2.py
mednarrate-backend/patch_dashboard.py
mednarrate-backend/qwen_capture_1.json
mednarrate-backend/qwen_capture_2.json
mednarrate-backend/qwen_capture_3.json
mednarrate-backend/qwen_capture_local.json
mednarrate-backend/qwen_debug.txt
mednarrate-backend/run_final_diagnostic.py
mednarrate-backend/run_forensic.py
mednarrate-backend/run_full_translation_test.py
mednarrate-backend/run_real_diagnostic.py
mednarrate-backend/temp_check.py
mednarrate-backend/temp_del.py
mednarrate-backend/temp_fetch.py
mednarrate-backend/temp_val.py
mednarrate-backend/test_config.py
mednarrate-backend/test_db_id.py
mednarrate-backend/test_e2e.py
mednarrate-backend/test_events.py
mednarrate-backend/test_failover.py
mednarrate-backend/test_failover_mock.py
mednarrate-backend/test_gemini.py
mednarrate-backend/test_gemini_scratch.py
mednarrate-backend/test_groq.py
mednarrate-backend/test_groq2.py
mednarrate-backend/test_groq_actual_report.py
mednarrate-backend/test_groq_actual_report2.py
mednarrate-backend/test_groq_exact.py
mednarrate-backend/test_groq_json.py
mednarrate-backend/test_groq_json_exact.py
mednarrate-backend/test_groq_planner_exact.py
mednarrate-backend/test_groq_resp.py
mednarrate-backend/test_groq_size.py
mednarrate-backend/test_health.py
mednarrate-backend/test_json_format.py
mednarrate-backend/test_len.py
mednarrate-backend/test_llm.py
mednarrate-backend/test_llm_db.py
mednarrate-backend/test_llm_full.py
mednarrate-backend/test_local_qwen.py
mednarrate-backend/test_model_check.py
mednarrate-backend/test_multi_lang.py
mednarrate-backend/test_parse.py
mednarrate-backend/test_parse_regression.py
mednarrate-backend/test_parse_regression2.py
mednarrate-backend/test_prompt.py
mednarrate-backend/test_provider.py
mednarrate-backend/test_real_groq.py
mednarrate-backend/test_real_groq2.py
mednarrate-backend/test_real_groq3.py
mednarrate-backend/test_real_groq4.py
mednarrate-backend/test_real_groq5.py
mednarrate-backend/test_real_prompt_size.py
mednarrate-backend/test_reminders_manual.py
mednarrate-backend/test_run_analysis.py
mednarrate-backend/test_settings.py
mednarrate-backend/test_translate.py
mednarrate-backend/test_translate_api.py
mednarrate-backend/test_translation.py
mednarrate-backend/test_translation_e2e.py
mednarrate-backend/test_translation_fn.py
mednarrate-backend/test_translations.py
mednarrate-backend/test_val_qwen.py
mednarrate-backend/scripts/patch_llm_client.py
mednarrate-backend/scripts/patch_planner.py
mednarrate-backend/scripts/generate_flabs_report.py
mednarrate-backend/scripts/generate_test_reports.py
mednarrate-backend/scripts/run_happy_path.py
mednarrate-backend/scripts/run_evaluation.py
mednarrate-backend/scripts/verify_full_pipeline_on_sample.py
mednarrate-backend/scripts/verify_lab_extraction.py
mednarrate-backend/scripts/verify_lab_extraction_regression.py
mednarrate-backend/scripts/verify_llm_chain.py
mednarrate-backend/scripts/ingest_knowledge.py
mednarrate-backend/scripts/seed_db.py
test_chat_live.py
replace_strings.py
generate_docs.py
generate_inventory.py
lib/core/constants/app_constants.dart
lib/features/reports/repository/report_repository.dart
mednarrate-admin/src/components/ui/breadcrumb.tsx
mednarrate-admin/src/components/ui/command.tsx
mednarrate-admin/src/components/ui/input-group.tsx
mednarrate-backend/:memory:.ses
mednarrate-backend/error.log
mednarrate-backend/disposable.db
mednarrate-audit-fixes.patch
scratch_list.txt
cleanup_scratch_scripts.sh
admin-final.tar.gz
apply_admin_final.sh
admin-polish.tar.gz
apply_admin_polish.sh
LIST

echo "2/4  Moving old reports into docs/archive and one tool into scripts/"
while IFS='|' read -r src dst; do
  if [ -n "$src" ] && [ -e "$src" ]; then
    mkdir -p "$(dirname "$dst")"
    mv "$src" "$dst"
    echo "     $src -> $dst"
  fi
done <<'LIST'
docs/admin/ADMIN_ACCOUNT_SECURITY_AUDIT.md|docs/archive/admin/ADMIN_ACCOUNT_SECURITY_AUDIT.md
docs/admin/ADMIN_CURRENT_STATE_AUDIT.md|docs/archive/admin/ADMIN_CURRENT_STATE_AUDIT.md
docs/admin/ADMIN_DEAD_OR_PLACEHOLDER_FEATURES.md|docs/archive/admin/ADMIN_DEAD_OR_PLACEHOLDER_FEATURES.md
docs/admin/ADMIN_DESKTOP_RELEASE_AUDIT.md|docs/archive/admin/ADMIN_DESKTOP_RELEASE_AUDIT.md
docs/admin/ADMIN_FEATURE_BACKEND_MATRIX.md|docs/archive/admin/ADMIN_FEATURE_BACKEND_MATRIX.md
docs/admin/ADMIN_FEATURE_GAP_MATRIX.md|docs/archive/admin/ADMIN_FEATURE_GAP_MATRIX.md
docs/admin/ADMIN_FINAL_EXISTING_FEATURE_VERIFICATION.md|docs/archive/admin/ADMIN_FINAL_EXISTING_FEATURE_VERIFICATION.md
docs/admin/ADMIN_FINAL_OPERATIONAL_STATUS.md|docs/archive/admin/ADMIN_FINAL_OPERATIONAL_STATUS.md
docs/admin/ADMIN_FINAL_REPAIR_REPORT.md|docs/archive/admin/ADMIN_FINAL_REPAIR_REPORT.md
docs/admin/ADMIN_FULL_FUNCTIONAL_AUDIT.md|docs/archive/admin/ADMIN_FULL_FUNCTIONAL_AUDIT.md
docs/admin/ADMIN_HEALTH_DIAGNOSIS.md|docs/archive/admin/ADMIN_HEALTH_DIAGNOSIS.md
docs/admin/ADMIN_IMMEDIATE_ACTIONS.md|docs/archive/admin/ADMIN_IMMEDIATE_ACTIONS.md
docs/admin/ADMIN_LATEST_API_CONTRACT_AUDIT.md|docs/archive/admin/ADMIN_LATEST_API_CONTRACT_AUDIT.md
docs/admin/ADMIN_LATEST_FILE_AUDIT.md|docs/archive/admin/ADMIN_LATEST_FILE_AUDIT.md
docs/admin/ADMIN_LATEST_GAP_REPORT.md|docs/archive/admin/ADMIN_LATEST_GAP_REPORT.md
docs/admin/ADMIN_LATEST_HEALTH_DIAGNOSIS.md|docs/archive/admin/ADMIN_LATEST_HEALTH_DIAGNOSIS.md
docs/admin/ADMIN_LATEST_STATUS_MATRIX.md|docs/archive/admin/ADMIN_LATEST_STATUS_MATRIX.md
docs/admin/ADMIN_OPERATIONS_GAP_ANALYSIS.md|docs/archive/admin/ADMIN_OPERATIONS_GAP_ANALYSIS.md
docs/admin/ADMIN_REMEDIATION_BASELINE.md|docs/archive/admin/ADMIN_REMEDIATION_BASELINE.md
docs/admin/ADMIN_REPOSITORY_AUDIT.md|docs/archive/admin/ADMIN_REPOSITORY_AUDIT.md
docs/admin/ADMIN_STABILITY_AUDIT.md|docs/archive/admin/ADMIN_STABILITY_AUDIT.md
docs/admin/REPAIR_COMMIT_MANIFEST.md|docs/archive/admin/REPAIR_COMMIT_MANIFEST.md
docs/audit/ADMIN_COMPLETE_FUNCTION_MATRIX.md|docs/archive/audit/ADMIN_COMPLETE_FUNCTION_MATRIX.md
docs/audit/ADMIN_CONFIRMED_BUGS.md|docs/archive/audit/ADMIN_CONFIRMED_BUGS.md
docs/audit/ADMIN_DEAD_FEATURES.md|docs/archive/audit/ADMIN_DEAD_FEATURES.md
docs/audit/ADMIN_FRONTEND_BACKEND_CONTRACTS.md|docs/archive/audit/ADMIN_FRONTEND_BACKEND_CONTRACTS.md
docs/audit/ADMIN_SECURITY_GAPS.md|docs/archive/audit/ADMIN_SECURITY_GAPS.md
docs/audit/ADMIN_TEST_COVERAGE_GAPS.md|docs/archive/audit/ADMIN_TEST_COVERAGE_GAPS.md
docs/audit/FULL_REPOSITORY_FILE_INVENTORY.md|docs/archive/audit/FULL_REPOSITORY_FILE_INVENTORY.md
docs/audit/REPOSITORY_HYGIENE.md|docs/archive/audit/REPOSITORY_HYGIENE.md
docs/audit/REPOSITORY_HYGIENE_FINAL.md|docs/archive/audit/REPOSITORY_HYGIENE_FINAL.md
debug-mednarrate-translation-bugs.md|docs/archive/debug-mednarrate-translation-bugs.md
debug-translation-regression-total-failure.md|docs/archive/debug-translation-regression-total-failure.md
generate_sounds.py|scripts/generate_sounds.py
LIST

echo "3/4  Installing 105 updated files"
tar xzf "$BUNDLE"

echo "4/4  Clearing test leftovers"
find mednarrate-backend/storage -name test_orphan.pdf -delete 2>/dev/null || true
find mednarrate-backend/storage -mindepth 1 -type d -empty -delete 2>/dev/null || true

cat <<'DONE'

Files are in place. Now run these, in this order:

  cd mednarrate-backend && source .venv/bin/activate
  pip install -r requirements.txt            # pins posthog<6 (stops the ChromaDB telemetry errors)
  python scripts/tidy_env.py --dry-run       # optional: shows the .env lines it would tidy
  cd ..

  cd mednarrate-admin && npm install && cd ..   # drops 7 unused packages

  flutter pub get                            # adds flutter_tts and regenerates the l10n files
  flutter analyze
  flutter test

Then restart the backend (Ctrl+C, then: python run_server.py).
DONE
