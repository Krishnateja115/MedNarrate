# Debug Session: translation-regression-total-failure

Session ID: translation-regression-total-failure
Status: [OPEN]
Created: 2026-09-27
Symptom:
  PREVIOUS STATE: Telugu translation partially working → some Telugu + some
    mixed-English sentences in patient-facing doctor discussion section.
  CURRENT STATE AFTER e6184f3 + 8490f74 + 59bcad8 commits:
    On clicking Translate → Telugu (or any non-English language), Flutter UI
    shows SnackBar "Translation failed. Please try again." — NO partial
    translated output appears AT ALL. REGRESSION.

Goal: Diagnose the EXACT runtime cause, capture full Python traceback, fix
      minimally without architectural rewrites.

## Falsifiable Hypotheses (H1-H5)

H1: Python NameError or AttributeError or KeyError in translate_analysis
    endpoint validator because `REQUIRED_UI_LABEL_KEYS` /
    `SUPPORTED_TRANSLATION_LANGUAGES` constants import order is wrong or
    reference is wrong in the `lang == "en"` or Gemini path.

H2: Alembic migration `d3f8a1b2c9d4_add_schema_version_and_doctor_discussion`
    was NOT applied to the local dev database. On the cache write,
    `AnalysisTranslation.schema_version` / `doctor_discussion_points` columns
    don't exist → SQLAlchemy ProgrammingError / UndefinedColumn on SQLite or
    PostgreSQL → endpoint 500 → Flutter SnackBar.

H3: The TRANSLATION_PROMPT JSON output template in prompts.py was expanded to
    require `doctor_discussion_points: []` + 44 `ui_labels` keys. Gemini
    returns only the old shape (no new keys, or fewer labels) → validator
    raises HTTPException(502) → Flutter SnackBar. This would manifest as an
    HTTP 502 with message mentioning `doctor_discussion_points` or a
    missing `ui_labels` key.

H4: Pydantic `TranslationOut` schema mismatch. `TranslationOut` now declares
    `doctor_discussion_points: List[str] = []` and `schema_version: int = 1`.
    The actual return dict or AnalysisTranslation object has different field
    names/nullable values causing pydantic ValidationError → 500 → SnackBar.

H5: Language-code whitelist introduced a 400. Previously Telugu `te` might
    have been sent with different casing, or Flutter sends one of the user's
    7 supported codes (en/hi/te/ta/kn/ml/mr) but the backend whitelist is a
    superset (8 including bn=Bengali), which should be fine, but maybe
    `normalize` logic is broken. Result: 400 Bad Request → SnackBar.

## Evidence Log

| Step | Action | Result |
|------|--------|--------|
| 1 | Backend start | PENDING |
| 2 | Reproduce (en→te) | PENDING |
| 3 | Direct HTTP POST check | PENDING |
| 4 | DB migration status check | PENDING |
| 5 | Gemini raw response (keys) | PENDING |

## Instrumentation Points (planned)
Will be added ONLY after H1-H5 falsification attempt via native logs.
