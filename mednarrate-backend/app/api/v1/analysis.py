import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.middleware.ownership import verify_report_ownership
from app.models.analysis_translation import (
    AnalysisTranslation,
    TRANSLATION_SCHEMA_VERSION,
)
from app.models.medication_schedule import MedicationSchedule
from app.models.report import ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.models.user import User
from app.schemas.report import (
    ReportAnalysisOut,
    ReportStatusOut,
    TranslationOut,
    TranslationRequest,
)
from app.services.analysis_pipeline import run_analysis
from app.services.llm_client import generate, generate_with_metadata
from app.services.prompts import TRANSLATION_PROMPT

router = APIRouter()

# Canonical supported language ISO-639-1 code -> English display name
SUPPORTED_TRANSLATION_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
}

# Every ui_labels key that the translation prompt contract promises.
# Backend validates that Gemini populated all of these (non-empty string)
# before storing/returning the translation — so Flutter never sees a
# partially-translated labels dict and is never tempted to fall back to
# hardcoded English for patient-facing text.
REQUIRED_UI_LABEL_KEYS = [
    "section_report_at_a_glance",
    "section_important_results",
    "section_reported_medications",
    "section_what_to_discuss",
    "section_patient_report_info",
    "chip_lab_results",
    "chip_medications",
    "chip_noteworthy",
    "chip_report_type",
    "label_result",
    "label_reported_range",
    "label_status",
    "label_dose",
    "label_frequency",
    "label_timing",
    "label_high",
    "label_low",
    "label_normal",
    "label_critical",
    "label_not_classified",
    "label_not_provided",
    "label_no_lab_results",
    "label_no_medications",
    "label_confirm_followup",
    "label_review_test_parameters",
    "label_confirm_dosage_timing",
    "label_confirm_new_medications",
    "label_generated_by_gemini",
    "label_generated_by_local_fallback",
    "label_generated_by_ollama",
    "label_generated_offline",
    "label_patient_report_heading",
    "label_clinical_report_heading",
    "section_important_findings",
    "section_key_clinical_findings",
    "label_no_key_findings",
    "label_key_finding_expansion_patient",
    "label_key_finding_expansion_clinician",
    "label_source_latest_report",
    "label_report_extracted",
    "label_translate",
    "label_retranslate",
    "label_disclaimer_patient",
    "label_disclaimer_summary",
]


@router.post("/{id}/process", status_code=202)
async def process_report(
    id: str,
    background_tasks: BackgroundTasks,
    force: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await verify_report_ownership(id, str(current_user.id), db)

    if (
        report.processing_status
        in [ProcessingStatus.processing, ProcessingStatus.completed]
        and not force
    ):
        raise HTTPException(
            status_code=409, detail="Report is already processing or completed"
        )

    report.processing_status = ProcessingStatus.processing
    await db.commit()

    background_tasks.add_task(run_analysis, report.id)

    return {"processing_status": "processing"}


@router.get("/{id}/status", response_model=ReportStatusOut)
async def get_report_status(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await verify_report_ownership(id, str(current_user.id), db)

    status_dict = {"processing_status": report.processing_status.value}

    if report.processing_status == ProcessingStatus.failed:
        stmt_analysis = select(ReportAnalysis).where(
            ReportAnalysis.report_id == report.id
        )
        res_analysis = await db.execute(stmt_analysis)
        analysis = res_analysis.scalars().first()
        status_dict["error_reason"] = (
            analysis.error_reason if analysis else "Unknown error"
        )
        status_dict["failure_category"] = (
            getattr(analysis, "failure_category", None) if analysis else None
        )
    else:
        status_dict["error_reason"] = None
        status_dict["failure_category"] = None

    return status_dict


@router.get("/{id}/analysis", response_model=ReportAnalysisOut)
async def get_report_analysis(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await verify_report_ownership(id, str(current_user.id), db)

    stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
    res_analysis = await db.execute(stmt_analysis)
    analysis = res_analysis.scalars().first()

    if not analysis:
        raise HTTPException(
            status_code=404, detail="Analysis not found. Call /process first."
        )

    stmt_meds = select(MedicationSchedule).where(
        MedicationSchedule.report_id == report.id
    )
    res_meds = await db.execute(stmt_meds)
    meds = res_meds.scalars().all()

    meds_list = [
        {
            "id": str(m.id),
            "medication_name": m.medication_name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "times_of_day": m.times_of_day or [],
            "duration_days": m.duration_days,
            "notes": m.notes,
            "provenance": getattr(m, "provenance", "REPORT_EXTRACTED")
            or "REPORT_EXTRACTED",
        }
        for m in meds
    ]

    pref_lang = current_user.preferred_language or "en"
    analysis_out = ReportAnalysisOut.model_validate(analysis)
    analysis_out.medications = meds_list

    if pref_lang != "en":
        stmt_trans = select(AnalysisTranslation).where(
            AnalysisTranslation.report_analysis_id == analysis.id,
            AnalysisTranslation.language == pref_lang,
        )
        res_trans = await db.execute(stmt_trans)
        translation = res_trans.scalars().first()
        if translation:
            analysis_out.translated_patient_summary = translation.patient_summary
            analysis_out.translation_available = True
        else:
            analysis_out.translation_available = False

    return analysis_out


@router.post("/{id}/analysis/translate", response_model=TranslationOut)
async def translate_analysis(
    id: str,
    req: TranslationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await verify_report_ownership(id, str(current_user.id), db)

    stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
    res_analysis = await db.execute(stmt_analysis)
    analysis = res_analysis.scalars().first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    stmt_meds = select(MedicationSchedule).where(MedicationSchedule.report_id == report.id)
    res_meds = await db.execute(stmt_meds)
    meds = res_meds.scalars().all()
    meds_list = [
        {
            "medication_name": m.medication_name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "times_of_day": m.times_of_day or [],
            "instructions": m.notes,
        }
        for m in meds
    ]

    raw_lang = (req.language or "").strip().lower()
    if raw_lang not in SUPPORTED_TRANSLATION_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported language '{req.language}'. "
                f"Supported codes: {sorted(SUPPORTED_TRANSLATION_LANGUAGES.keys())}."
            ),
        )
    lang = raw_lang
    target_lang_name = SUPPORTED_TRANSLATION_LANGUAGES[lang]

    abnormal_findings_source = [
        f for f in (analysis.abnormal_findings or [])
        if not _is_metadata_finding(f)
    ]

    #region debug-point trans-backend-001
    print(f"[TRANSLATION] report_id={report.id} analysis_id={analysis.id} requested_language={lang} target_name={target_lang_name} endpoint=POST /reports/{id}/analysis/translate")
    print(f"[TRANSLATION] abnormal_count={len(abnormal_findings_source)} medication_count={len(meds_list)} source_patient_summary_chars={len(analysis.patient_summary or '')} schema_version_required={TRANSLATION_SCHEMA_VERSION}")
    #endregion

    if lang == "en":
        # English is the baseline/original language — no translation needed.
        return TranslationOut(
            language="en",
            patient_summary=analysis.patient_summary or "",
            findings_json=[],
            medications_json=[],
            doctor_discussion_points=[],
            ui_labels={},
            schema_version=TRANSLATION_SCHEMA_VERSION,
        )

    stmt_trans = select(AnalysisTranslation).where(
        AnalysisTranslation.report_analysis_id == analysis.id,
        AnalysisTranslation.language == lang,
    )
    res_trans = await db.execute(stmt_trans)
    translation = res_trans.scalars().first()

    if translation is not None:
        # region debug-point trans-backend-002
        _f = getattr(translation, "findings_json", []) or []
        _m = getattr(translation, "medications_json", []) or []
        _d = getattr(translation, "doctor_discussion_points", []) or []
        _u = getattr(translation, "ui_labels", {}) or {}
        _sv = getattr(translation, "schema_version", 1)
        print(
            f"[TRANSLATION] cache_hit=true cache_language={translation.language} "
            f"cache_schema_version={_sv} required_schema_version={TRANSLATION_SCHEMA_VERSION} "
            f"findings_count={len(_f)} medications_count={len(_m)} "
            f"discussion_count={len(_d)} ui_labels_count={len(_u)}"
        )
        # endregion
        cache_valid = True
        if _sv < TRANSLATION_SCHEMA_VERSION:
            print("[TRANSLATION] cache_invalidated_reason=old_schema_version")
            cache_valid = False
        elif translation.patient_summary.startswith("[Translation") or translation.patient_summary.startswith("This is an automated"):
            print("[TRANSLATION] cache_invalidated_reason=stale_automated_prefix")
            cache_valid = False
        elif not isinstance(_d, list) or len(_d) == 0:
            print("[TRANSLATION] cache_invalidated_reason=missing_doctor_discussion_points")
            cache_valid = False
        elif not all(k in _u and isinstance(_u.get(k), str) and _u.get(k).strip() for k in REQUIRED_UI_LABEL_KEYS):
            missing = [k for k in REQUIRED_UI_LABEL_KEYS if not (_u.get(k) or "").strip()]
            print(f"[TRANSLATION] cache_invalidated_reason=missing_ui_labels missing_count={len(missing)} sample_missing={missing[:5]}")
            cache_valid = False

        if cache_valid:
            return TranslationOut(
                language=lang,
                patient_summary=translation.patient_summary,
                findings_json=_f,
                medications_json=_m,
                doctor_discussion_points=_d,
                ui_labels={k: str(v) for k, v in _u.items()},
                schema_version=_sv,
                cached=True,
            )
        else:
            await db.delete(translation)
            await db.commit()
            translation = None
    else:
        # region debug-point trans-backend-003
        print(
            f"[TRANSLATION] cache_hit=false target_language_name={target_lang_name} "
            f"provider=gemini_structured_json schema_version={TRANSLATION_SCHEMA_VERSION}"
        )
        # endregion

    # ------------------------------------------------------------------
    # Cache miss — call the LLM translation provider with the structured
    # prompt and validate the response BEFORE we persist anything.
    # ------------------------------------------------------------------
    prompt = TRANSLATION_PROMPT.format(
        target_language=target_lang_name,
        patient_summary=analysis.patient_summary or "",
        abnormal_findings_json=json.dumps(abnormal_findings_source, indent=2, ensure_ascii=False),
        medications_json=json.dumps(meds_list, indent=2, ensure_ascii=False),
    )

    print("\n========== TRANSLATION DEBUG START ==========")
    print(f"REPORT ID: {analysis.report_id}")
    print(f"TARGET LANGUAGE: {target_lang_name}")
    print(f"SOURCE LANGUAGE: en")
    print(f"ENDPOINT: POST /reports/{id}/analysis/translate")
    print(f"HTTP METHOD: POST")
    print("REQUEST SENT: YES")

    try:
        llm_res = await generate_with_metadata(prompt)
        print("HTTP STATUS: 200 (LLM Success)")
        print("RESPONSE RECEIVED: YES")

        response_text = llm_res.get("content", "")
        provider = llm_res.get("provider", "unknown")

        print(f"RESPONSE CONTENT TYPE: application/json")
        print(f"RESPONSE LENGTH: {len(response_text)}")
        print(f"PROVIDER: {provider}")

        if provider == "fallback":
            print("ERROR TYPE: ProviderFallback")
            print("ERROR MESSAGE: Primary LLM failed, fell back to local string.")
            print("========== TRANSLATION DEBUG END ==========\n")
            raise HTTPException(
                status_code=503,
                detail="Translation service is temporarily unavailable.",
            )

        # Robust JSON extraction: strip markdown fences, find outermost {...}
        import re as _re

        raw = response_text.strip()
        fences = _re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
        if fences:
            raw = fences.group(1).strip()
        start = raw.find("{")
        if start == -1:
            print("PARSING SUCCESS: NO")
            print("ERROR TYPE: NoJSON")
            print("ERROR MESSAGE: No JSON object found in response")
            print(f"RAW RESPONSE: {raw[:300]}")
            print("========== TRANSLATION DEBUG END ==========\n")
            raise HTTPException(
                status_code=502,
                detail="Translation provider returned no JSON object.",
            )
        depth = 0
        end = -1
        for i in range(len(raw) - 1, start - 1, -1):
            c = raw[i]
            if c == "}":
                if depth == 0:
                    end = i
                depth += 1
            elif c == "{":
                depth -= 1
                if depth == 0:
                    break
        json_str = raw[start : end + 1] if end != -1 else raw[start:]

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            print("PARSING SUCCESS: NO")
            print("ERROR TYPE: JSONDecodeError")
            print(f"ERROR MESSAGE: {str(e)}")
            print(f"CHAR POSITION: {e.pos}")
            print(f"JSON_STR LENGTH: {len(json_str)}")
            print("========== TRANSLATION DEBUG END ==========\n")
            raise HTTPException(
                status_code=502,
                detail=f"Translation provider returned invalid JSON at pos {e.pos}: {str(e)}",
            )

        print(f"RESPONSE KEYS: {list(parsed.keys())}")
        print("PARSING SUCCESS: YES")

        translated_summary = parsed.get("patient_summary") or ""
        translated_findings = parsed.get("abnormal_findings", parsed.get("findings_json", [])) or []
        translated_medications = parsed.get("medications", parsed.get("medications_json", [])) or []
        translated_discussion = parsed.get("doctor_discussion_points", parsed.get("discussion_points", [])) or []
        translated_ui_labels_raw = parsed.get("ui_labels", {}) or {}
        translated_ui_labels = {
            str(k): "" if v is None else str(v)
            for k, v in translated_ui_labels_raw.items()
        }

        # ---- Completeness validation (refuse to store/serve partial translations) ----
        missing_top_keys = [
            k
            for k in ("patient_summary", "abnormal_findings", "medications", "doctor_discussion_points", "ui_labels")
            if k not in parsed
        ]
        if missing_top_keys:
            print("[TRANSLATION] validation_failed=missing_top_level_keys missing=" + str(missing_top_keys))
            raise HTTPException(
                status_code=502,
                detail=f"Translation provider response missing required keys: {missing_top_keys}",
            )
        if not translated_summary.strip():
            print("[TRANSLATION] validation_failed=empty_patient_summary")
            raise HTTPException(
                status_code=502,
                detail="Translation provider returned empty patient summary.",
            )
        if not isinstance(translated_findings, list):
            print("[TRANSLATION] validation_failed=findings_not_list")
            raise HTTPException(status_code=502, detail="Translation: abnormal_findings must be a list.")
        if not isinstance(translated_medications, list):
            print("[TRANSLATION] validation_failed=meds_not_list")
            raise HTTPException(status_code=502, detail="Translation: medications must be a list.")
        if not isinstance(translated_discussion, list):
            print("[TRANSLATION] validation_failed=discussion_not_list")
            raise HTTPException(status_code=502, detail="Translation: doctor_discussion_points must be a list.")
        if len(translated_discussion) == 0:
            print("[TRANSLATION] validation_failed=empty_doctor_discussion")
            raise HTTPException(
                status_code=502,
                detail="Translation: doctor_discussion_points is empty; at minimum the follow-up bullet is required.",
            )
        if not all(isinstance(s, str) and s.strip() for s in translated_discussion):
            bad = [i for i, s in enumerate(translated_discussion) if not (isinstance(s, str) and s.strip())]
            print(f"[TRANSLATION] validation_failed=discussion_nonstring_or_empty indices={bad}")
            raise HTTPException(
                status_code=502,
                detail="Translation: doctor_discussion_points must be non-empty strings.",
            )

        missing_labels = [
            k
            for k in REQUIRED_UI_LABEL_KEYS
            if not translated_ui_labels.get(k, "").strip()
        ]
        if missing_labels:
            print(f"[TRANSLATION] validation_failed=missing_ui_labels count={len(missing_labels)} sample={missing_labels[:8]}")
            raise HTTPException(
                status_code=502,
                detail=(
                    "Translation provider response missing "
                    f"{len(missing_labels)} required ui_labels: "
                    + ", ".join(missing_labels[:8])
                    + ("…" if len(missing_labels) > 8 else "")
                ),
            )

        # Normalize medications translated_times_of_day into a list.
        # (If Gemini returned a single string despite the prompt asking for an
        # array, coerce it here so the Flutter UI never has to guess.)
        normalized_meds = []
        for med in translated_medications:
            if not isinstance(med, dict):
                continue
            times = med.get("translated_times_of_day")
            if isinstance(times, str) and times.strip():
                times_list = [times.strip()]
            elif isinstance(times, list):
                times_list = [t for t in times if isinstance(t, str) and t.strip()]
            else:
                times_list = []
            normalized_meds.append(
                {
                    "medication_name": med.get("medication_name", ""),
                    "translated_dosage": med.get("translated_dosage", ""),
                    "translated_frequency": med.get("translated_frequency", ""),
                    "translated_times_of_day": times_list,
                    "translated_instructions": med.get("translated_instructions", ""),
                }
            )

        # region debug-point trans-backend-004
        print(
            f"[TRANSLATION] llm_parse_ok=true summary_chars={len(translated_summary)} "
            f"findings_count={len(translated_findings)} medications_count={len(normalized_meds)} "
            f"ui_labels_count={len(translated_ui_labels)} doctor_discussion_count={len(translated_discussion)}"
        )
        # endregion
        print("========== TRANSLATION DEBUG END ==========\n")
    except HTTPException:
        raise
    except Exception as e:
        print("RESPONSE RECEIVED: NO")
        print(f"ERROR TYPE: {type(e).__name__}")
        print(f"ERROR MESSAGE: {str(e)}")
        print("========== TRANSLATION DEBUG END ==========\n")
        raise

    translation = AnalysisTranslation(
        report_analysis_id=analysis.id,
        language=lang,
        schema_version=TRANSLATION_SCHEMA_VERSION,
        patient_summary=translated_summary,
        findings_json=translated_findings,
        medications_json=normalized_meds,
        doctor_discussion_points=translated_discussion,
        ui_labels=translated_ui_labels,
    )
    db.add(translation)
    await db.commit()
    await db.refresh(translation)

    return TranslationOut(
        language=lang,
        patient_summary=translation.patient_summary,
        findings_json=translation.findings_json,
        medications_json=getattr(translation, "medications_json", []) or [],
        doctor_discussion_points=getattr(translation, "doctor_discussion_points", []) or [],
        ui_labels={k: str(v) for k, v in (getattr(translation, "ui_labels", {}) or {}).items()},
        schema_version=getattr(translation, "schema_version", TRANSLATION_SCHEMA_VERSION),
    )


def _is_metadata_finding(finding: dict) -> bool:
    """Returns True if an abnormal finding looks like a metadata parameter
    (age, gender, date, etc.) rather than a lab result. Used so that we
    don't produce doctor-discussion bullets for non-clinical metadata."""
    if not isinstance(finding, dict):
        return False
    name = (
        finding.get("test_name")
        or finding.get("parameter")
        or finding.get("original_name")
        or ""
    )
    n = str(name).strip().lower()
    metadata_tokens = [
        "age",
        "dob",
        "gender",
        "sex",
        "date",
        "report date",
        "collected",
        "received",
        "patient id",
        "patient name",
        "lab no",
        "lab id",
        "laboratory no",
    ]
    return any(tok in n for tok in metadata_tokens)
