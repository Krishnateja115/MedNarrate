# Audit addendum 6 — Using the MRAD dataset inside the product

Date: 2026-10-18

## Where the dataset was used before this change
MRAD (123,367 usable reports, 110,677 patients; classes Blood / Health / TCGA) was used **only offline** to train the report-type classifier (TF-IDF + logistic regression, patient-level 80/10/10 split, seed 42, header-leakage stripping). The saved artifacts live in `mednarrate-backend/app/ml/artifacts/`. Nothing in the running app used the dataset or the classifier, so it was not visible to a user or an examiner.

## What was added (all optional, nothing existing changed)
1. **Dataset section (read-only).** The Models screen in the app and the Models & XAI page in the admin portal now show the dataset: size, patients, train/validation/test counts, classes, the patient-level split, the leakage safeguard and the scope. The numbers come from the saved `metadata.json` through `/ml/model-performance` (`dataset` block). If the file is missing the section is simply hidden. No file paths are exposed.
2. **Experimental document-type hint.** `GET /api/v1/reports/{id}/document-type` runs the classifier on a finished report's text. The report screen shows a small badge ("Looks like a blood-test report · Model score 87% · Experimental"); tapping it explains what it is.
   - Behind the feature flag `report_type_check`, **off by default**. When off, the endpoint does nothing and the model is not even loaded.
   - Never affects the summary, lab values or chat. Any error, timeout or missing model returns "no hint" and the app shows nothing.
   - Result cached in `ReportAnalysis.model_versions["document_type_check"]` (no migration).
   - Shown only when the report has lab/entity evidence (>= 3 labs or >= 5 entities), confidence >= 0.55 and a margin of >= 0.15 over the runner-up.

## Honest limits (state these when presenting)
- It is an auxiliary research model, not a clinical component, and not part of the safety path.
- The three classes describe where MRAD's records came from (blood tests, general health records, TCGA pathology/cancer-research), not diagnoses.
- Probabilities are poorly calibrated outside the training distribution (nonsense text scored TCGA 99.8%; a real CBC scored Blood 0.60 vs TCGA 0.40). That is why the evidence and margin gates exist.
- No new accuracy figure was measured; the app only displays what is stored in `metrics.json` / `metadata.json`.
- The MRAD source and licence are not recorded in the repository; cite them in the project report.

## Housekeeping fixed on the way
- `scikit-learn==1.9.0` and `joblib` were missing from `requirements.txt` (the artifacts were pickled with 1.9.0); added.
- `.gitignore` ignored every `data/` folder, hiding `mednarrate-backend/data/glossary.json`; now only the root `/data/` and `mednarrate-backend/data/mrad_full/` are ignored.
- Removed a hard-coded `C:/Users/manas/...` path from `app/ml/dataset_loader.py`.

## Verification
- Backend: 616 passed, 3 skipped on SQLite and on PostgreSQL (15 new tests in `tests/test_report_type_check.py`).
- Admin: tsc, eslint clean; 91 Jest tests passed (2 new); `next build` succeeds.
- Flutter: syntax-checked only in the sandbox (no Flutter SDK there). Run `flutter gen-l10n`, `flutter analyze` and `flutter test` locally (new `test/document_type_badge_test.dart`).
- New UI strings in hi, mr, bn, ta, te, kn, ml are machine drafts and need native-speaker review.

## To use
Admin → Feature Flags → create/enable `report_type_check` (rollout 100). Restart the backend after `pip install -r requirements.txt`.
