# MedNarrate: translation, voice input, and release audit

**Audit date:** 17 October 2026

**Status:** Findings and implementation plan only. No translation or voice code was changed during this audit.
**Target:** The documented Flutter mobile app, FastAPI API, PostgreSQL database, separate analysis worker, and admin portal.

## 1. Scope and confidence

The audit inventoried and read all 937 Git-tracked and untracked project-owned files present at the time (925 tracked, 12 untracked; about 16 MB). Python, JSON, ARB, and TOML files also received syntax or format checks where applicable. The translation, chat, configuration, tests, deployment, and release paths were then reviewed in detail. Ignored dependencies and generated build output were outside this inventory. Reading all files does not establish that every feature works at runtime.

The existing working tree had 45 modified tracked files and 12 untracked entries before this document was created. Those changes must be reviewed separately; they are not evidence of a deployed fix. No live provider request, app build, test suite, or deployed-environment check was run as part of the read-only audit. The saved backend test log is from 2 October 2026 and records 30 passes and 5 errors; it cannot establish the state of the current tree.

**Diagnosis boundary:** The code contains confirmed failure paths, but the exact cause of the user's current translation failure cannot be identified without one failed request ID and the corresponding API/provider logs. Do not label a guessed provider error as confirmed.

## 2. How translation currently works

1. The patient view language picker in `lib/features/reports/widgets/patient_view_tab.dart` asks `report_detail_controller.dart` to translate a report.
2. `lib/core/services/api_service.dart` posts the language to `/reports/{id}/analysis/translate` and waits up to 240 seconds.
3. `mednarrate-backend/app/api/v1/analysis.py` checks authentication and report ownership, reads or validates a cached translation, collects summaries/findings/medications/parameter names, and selects providers.
4. `mednarrate-backend/app/services/translation_planner.py` splits content into units of at most 700 characters, calls providers sequentially, validates each response, and merges the result. The first unit also asks for 78 translated interface labels.
5. `mednarrate-backend/app/services/translation_validation.py` verifies language script, required labels, field counts, and clinical facts. A translation error becomes HTTP 502 and a generic message in the app.

Supported requested languages are English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, and Marathi. English uses the original analysis rather than a model translation.

## 3. Translation findings and exact repair work

| Priority | Finding and evidence | Consequence | Required repair |
| --- | --- | --- | --- |
| P0 | `DevGeminiProvider._check_production_restriction()` in `mednarrate-backend/app/services/llm_client.py` rejects direct Gemini API use when `ENVIRONMENT=production`. | A production setup relying only on `GEMINI_API_KEY` cannot translate, even if the key is valid. | Confirm the deployed provider order and credentials. Configure and verify a production-supported provider such as the existing Vertex AI route, with a working fallback. Do not assume a local development key will work in production. |
| P0 | The planner's total deadline and Flutter's HTTP timeout are both 240 seconds (`translation_planner.py` and `api_service.dart`). Units are processed sequentially, with up to two attempts per provider. | A long report may reach the phone timeout before the server returns; a reverse proxy might time out sooner. | Set a server deadline below the shortest client/proxy limit and return a useful timeout code. Prefer fewer requests or a queued translation job for long reports. Measure real report latency before selecting limits. |
| P0 | The first model response must contain all 78 required `ui_labels` (`analysis.py` and `translation_validation.py`). A missing or wrong-script value fails validation. | A mostly correct translation can still be rejected, and repeated attempts consume time/quota. | Keep strict medical-data validation, but move fixed interface labels to reviewed app localization resources or translate/cache them separately. Test every required label per language. Do not silently show an incomplete medical translation. |
| P1 | `analysis.py` catches planner failures and returns a generic translation-unavailable message. `app/exceptions.py` returns HTTP 502 with a request ID. | The phone cannot show the actual provider/auth/quota/format cause. | Preserve a safe user message, but log a structured failure category, provider, stage, duration, and request ID without report text. Use the request ID to diagnose a failed attempt. |
| P1 | Development skips final merged-payload validation in `analysis.py`; other environments run it. | A translation that appears acceptable locally can fail in production. | Run the same final validation in tests and staging, and make the development exception explicit or remove it after adjusting fixtures. |
| P1 | `tests/test_translation_pipeline.py` and `test/translation_flow_test.dart` use synthetic or mocked provider responses. Live AI tests are optional in `TESTING.md`. | CI can pass while deployed translation fails. | Add a controlled live-provider smoke test using synthetic reports, plus deterministic tests for missing labels, quota/auth failures, provider fallback, long reports, and every supported language. |

### Diagnostic procedure for one real failure

1. Use a **synthetic** report; do not place patient data in logs or test fixtures.
2. Record the selected language, report size, app error/status, duration, and response `request_id`.
3. Find that ID in API logs. Record the configured provider order and the first failing stage: configuration, upstream HTTP status, response parsing, validation, or timeout. Never print API keys or full report text.
4. Verify credentials, model access, quota, and production environment inside the deployed API container/service, not only in a local `.env` file. The local model name alone is not a confirmed defect.
5. Re-run the same synthetic report after the targeted fix, then test all seven translated languages on a short and a multi-section report. Verify text script, all 78 labels, finding/medication counts, and preservation of medical numbers and units.

**Release acceptance:** A real production-configured API returns complete, clinically checked translations for all supported languages within the measured client/proxy deadline. Cache hits and provider failure messages must also behave correctly.

## 4. Voice-to-text feature

### Current state

There is no speech-recognition or audio-recording dependency in `pubspec.yaml`, no microphone action in either chat composer (`lib/features/reports/widgets/ai_chat_tab.dart` and `lib/features/ai_chat/screens/ai_chat_screen.dart`), no transcription endpoint, and no required Android/iOS speech and microphone permission descriptions. `audioplayers` is for playback, not dictation.

### Recommended scope for the next release

Implement **tap microphone → speak a short message → review/edit the transcript in the chat field → tap Send**. Keep typing available. Do not auto-send dictated text: medical names, doses, and numbers can be misheard.

The quickest path is Flutter's device speech recognition through [`speech_to_text`](https://pub.dev/packages/speech_to_text). It needs **no app API key**. The plugin documents Android `RECORD_AUDIO`, iOS `NSMicrophoneUsageDescription` and `NSSpeechRecognitionUsageDescription`, and an Android recognition-service query for current target SDKs. Initialize recognition once, request permissions when the user taps the mic, show listening/partial/final/error states, stop cleanly on navigation, and place the final words in the existing `TextEditingController`. Use the requested chat language as the preferred locale only when that locale is available on the device. The plugin is designed for commands and short phrases, not continuous, always-on dictation; support varies by device and recognition service.

If consistent cross-device transcription is required, record a bounded clip on the phone and upload it to a new authenticated FastAPI endpoint, for example `POST /api/v1/speech/transcribe`. The **backend** calls the provider, keeps the API key in its secret manager, enforces audio type/size/duration and rate limits, deletes temporary audio, and returns the transcript. OpenAI documents [file transcription](https://developers.openai.com/api/docs/guides/speech-to-text) for recorded clips. [Realtime transcription](https://developers.openai.com/api/docs/guides/realtime-transcription) supports streaming, but a Wispr-like continuous experience also needs streaming transport, interruption handling, latency controls, and substantially more device testing. Do not embed a provider secret in Flutter.

**Recommendation:** Ship only short-message dictation by the deadline if the real Android/iOS and target-language checks pass. Treat continuous dictation as a later feature. If even the short-message checks fail, keep the mic feature out of the release rather than presenting it as reliable.

### Voice acceptance tests

- Permission grant, denial, and later revocation; no app crash or stuck listening indicator.
- Start, partial text, stop, final text, retry, navigation away, incoming call/interruption, and no network or speech service.
- Actual Android and iOS devices; each language promised in the interface; mixed medical terminology, medicine names, quantities, and punctuation.
- User can edit or clear recognized text before sending; voice input never sends a chat message by itself.
- No audio or transcript in ordinary logs; any external processing is accurately described in the privacy policy.

## 5. Other file and release observations

- Four tracked `mednarrate-backend/qwen_capture*.json` files do not parse as standalone JSON. At least some are referenced by development scripts, so they should **not** be deleted solely from this scan. Determine whether they are intended raw captures or malformed fixtures before changing them.
- `.audit_src_tmp.tgz`, `AUDIT_REPORT.md`, and `mednarrate-audit-fixes.patch` were pre-existing untracked audit artifacts. Their role and contents need review before inclusion in a release; this audit did not delete them.
- `git diff --check` found no whitespace errors at audit time. That does not validate builds or behavior.
- `RELEASE_READINESS.md` lists outstanding production inputs: public HTTPS domains, provider credentials, shared storage, worker, database migrations, Android/iOS signing, privacy text, and deployed-environment checks. The permanent mobile identifier is `com.mednarrate.app` in the platform projects.
- `TESTING.md` and `.github/workflows/ci.yml` define an automated release gate, but normal backend tests do not call a real AI provider. The saved October 2 test log's five errors were in deletion/breakglass tests; that historical result must not be presented as a current test run.

## 6. Work order for deployment

1. **First: diagnose and repair translation.** Capture one failed request ID, fix its confirmed provider or validation error, resolve the timeout design, and test all supported languages against production-style configuration.
2. **Second: add the smallest voice feature.** Add the mic composer flow and permissions, then run the voice acceptance tests on real devices. Use a backend speech provider only if device recognition fails the required languages and there is time to secure and test that endpoint.
3. **Third: run the existing release gate from the exact commit intended for deployment.** Resolve any failures in backend tests, PostgreSQL migrations, Flutter analysis/tests, mobile simulator, admin checks, Docker, and secret scans. Review the advisory Python dependency report as well.
4. **Fourth: verify the deployed stack.** Check the API and independent worker, PostgreSQL migrations, file storage, upload/analysis, chat, translation, offline queue/cache, account switching, notifications, admin actions, backup restore, logs, and alerts with synthetic accounts and reports.
5. **Fifth: build and sign final mobile artifacts** with the real HTTPS API URL and `com.mednarrate.app`; test the signed builds on actual Android and iOS devices. Verify the published privacy terms match hosting and AI processing.

**Current go/no-go:** The read-only audit cannot certify a deployment. Translation has confirmed failure paths, voice-to-text is absent, and the required live and signed-build checks remain outstanding. This checklist becomes complete only when each item has a recorded passing result against the exact release build.
