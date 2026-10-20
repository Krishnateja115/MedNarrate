# Debug Session: mednarrate-translation-bugs

Status: [OPEN]
Date: 2026-09-27

## Bug Description
MedNarrate translation pipeline: only Telugu partially works. "What to Discuss With Your Doctor" mixes English sentences ("Discuss the LOW MCV level (80)...") with Telugu ones. Same class of bug suspected for all 6 non-English languages (hi, te, ta, kn, ml, mr) across summary, findings, medications, headings, UI labels, and disclaimers.

## Hypotheses
- H1: Flutter generates English discussion sentences locally via templates (e.g. `_generateDoctorDiscussionPoints`) and inserts them alongside translated points.
- H2: Backend translation prompt / schema only translates a subset of patient-facing fields (summary + abnormal_findings) leaving medications, normal findings, discussion points, headings, and UI labels empty → Flutter falls back to English hardcodes.
- H3: Translation cache keyed without language, or stale old-schema records are returned instead of regenerating.
- H4: Medication data (MedicationSchedule) is never joined into the translation request; medication translation fields always empty.
- H5: Language-code mapping broken somewhere between Flutter dropdown → request → backend → Gemini prompt → DB → response.

## Evidence Log
(To be collected)

## Fix Plan
(To be written after evidence)

## Verification Checklist
(en / hi / te / ta / kn / ml / mr) × (summary / findings / normal / abnormal / meds / discussion / headings / labels / disclaimer / retranslate)
