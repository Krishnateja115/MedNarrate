# MedNarrate clinical evaluation status — prelaunch

MedNarrate's automated tests check selected software behavior. They **do not**
establish clinical accuracy, suitability for diagnosis, or medical-device
compliance. Do not describe the app as clinically validated until the review
below is complete and signed off by qualified reviewers.

## What automated tests currently establish

- Selected emergency and diagnosis/treatment prompts are routed to safety
  responses. This does not prove all dangerous prompts will be detected.
- Known lab examples exercise extraction, flags, provisional comparisons, and
  source-excerpt matching. OCR, units, report layout, and model output can still
  produce wrong or omitted findings.
- Source excerpts are shown only when a test name and measured value occur in
  the same extracted line. They are not page-level citations and do not replace
  visual comparison with the original upload.

## Required review before a public health-app release

1. Define the intended users and claims (report explanation, not diagnosis or
   treatment). Have a medical and regulatory reviewer approve this scope.
2. Assemble a permissioned, de-identified evaluation set covering different
   labs, units, report formats, scans, languages, ages, and normal/abnormal
   findings. Never commit real patient documents to Git.
3. Have qualified reviewers annotate the source truth for each report: test
   name, measured value, unit, report-provided reference range, date, and any
   medication. Record when the source itself is ambiguous.
4. Run the complete upload-to-display workflow. Reviewers compare each
   extracted result, abnormality label, summary, translation, and chat answer
   with the original document. Record both wrong assertions and omissions.
5. Separately test non-medical documents, poor scans, missing ranges, mixed
   units, pediatric reports, and emergency/diagnosis requests. The safe result
   may be an explicit refusal or an unclassified value, not a guess.
6. Define acceptance thresholds **before** reviewing results, based on the
   severity of each error. Any incorrect numeric value, unit, report-specific
   range, or unsafe treatment instruction needs investigation and retesting.
7. Obtain documented sign-off from the reviewers for the exact app/backend
   version and AI-provider configuration intended for release. Re-review after
   material model, prompt, OCR, or reference-range changes.

## Review record template

For each case, record: case ID (not patient identity), document type and
language, source-truth annotation version, app/backend/model versions, finding
or question, expected result, observed result, error severity, reviewer,
resolution, and retest outcome.

**Current status:** Automated checks exist; a representative clinician-reviewed
dataset, agreed acceptance thresholds, and human sign-off are still pending.
