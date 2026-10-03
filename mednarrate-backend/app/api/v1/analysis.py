import hashlib
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.maintenance import check_maintenance
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
from app.services.llm_client import generate_translation
from app.services.translation_validation import parse_translation, validate_translation
from app.exceptions import TranslationServiceError
from app.services.prompts import TRANSLATION_PROMPT

router = APIRouter()
logger = logging.getLogger(__name__)

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
    "label_hospital",
    "label_unspecified",
    "label_date",
    "label_validation",
    "label_status_completed",
    "label_status_processing",
    "label_status_failed",
    "label_status_uploaded",
    "label_validation_passed",
    "label_validation_failed",
    "label_validation_pending",
    "label_why_it_was_flagged",
    "label_parameter",
    "label_unit",
    "label_reference_range",
    "section_diagnoses",
    "section_historical_comparison",
    "section_source_validation",
    "label_no_previous_report",
    "label_source_document",
    "label_report_date",
    "label_rag_search_index",
    "label_medical_validation",
    "label_active_retriever",
    "label_passed_rules",
    "chip_blood",
    "chip_urine",
    "label_uncategorized",
    "label_cat_cbc",
    "label_cat_lipid_panel",
    "label_cat_liver_function",
    "label_cat_kidney_function",
    "label_cat_vitamins_&_minerals",
    "label_search_parameters",
]


@router.post("/{id}/process", status_code=202)
async def process_report(
    id: str,
    background_tasks: BackgroundTasks,
    force: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    maintenance = Depends(check_maintenance("report_analysis")),
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
    maintenance = Depends(check_maintenance("translation")),
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

    source_fingerprint = hashlib.sha256(json.dumps(
        [analysis.patient_summary or "", abnormal_findings_source, meds_list],
        sort_keys=True, ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    if (translation is not None
            and translation.schema_version >= TRANSLATION_SCHEMA_VERSION
            and (translation.ui_labels or {}).get("_source_fingerprint") == source_fingerprint):
        cached_payload = {
            "patient_summary": translation.patient_summary,
            "abnormal_findings": translation.findings_json,
            "medications": translation.medications_json,
            "doctor_discussion_points": translation.doctor_discussion_points,
            "ui_labels": translation.ui_labels,
        }
        try:
            validate_translation(cached_payload, lang, analysis.patient_summary or "",
                                 abnormal_findings_source, meds_list, REQUIRED_UI_LABEL_KEYS)
        except (ValueError, TypeError, KeyError):
            logger.info("Translation cache failed validation language=%s", lang)
        else:
            return TranslationOut(
                language=lang, patient_summary=translation.patient_summary,
                clinician_summary=getattr(translation, "clinician_summary", None),
                findings_json=translation.findings_json,
                medications_json=translation.medications_json,
                doctor_discussion_points=translation.doctor_discussion_points,
                ui_labels=translation.ui_labels,
                schema_version=translation.schema_version, cached=True,
            )

    unique_params = list(set([
        str(m.get("test_name")) for m in (analysis.structured_lab_values or []) if m.get("test_name")
    ] + [
        str(f.get("test_name")) for f in abnormal_findings_source if f.get("test_name")
    ]))

    prompt = TRANSLATION_PROMPT.format(
        target_language=target_lang_name,
        clinical_summary=analysis.clinician_summary or "",
        patient_summary=analysis.patient_summary or "",
        abnormal_findings_json=json.dumps(abnormal_findings_source, ensure_ascii=False),
        medications_json=json.dumps(meds_list, ensure_ascii=False),
        unique_parameters_json=json.dumps(unique_params, ensure_ascii=False),
    )
    logger.info("Translation requested language=%s input_chars=%d", lang, len(prompt))
    llm_res = await generate_translation(prompt)
    if llm_res.get("provider") == "fallback":
        raise TranslationServiceError()
    try:
        parsed = validate_translation(
            parse_translation(llm_res.get("content", "")), lang,
            analysis.patient_summary or "", abnormal_findings_source,
            meds_list, REQUIRED_UI_LABEL_KEYS,
        )
    except (ValueError, TypeError, KeyError) as exc:
        # Do not log the model response or medical data.
        abnormal_len = len(parsed.get("abnormal_findings") or []) if 'parsed' in locals() and isinstance(parsed, dict) else -1
        med_len = len(parsed.get("medications") or []) if 'parsed' in locals() and isinstance(parsed, dict) else -1
        logger.warning(f"Translation validation failed language={lang} error_type={type(exc).__name__} error={str(exc)} src_find_len={len(abnormal_findings_source)} out_find_len={abnormal_len} src_med_len={len(meds_list)} out_med_len={med_len}")
        raise TranslationServiceError(
            "The translation could not be verified. Please try again."
        ) from exc
    translated_summary = parsed["patient_summary"]
    translated_clinical_summary = parsed.get("clinical_summary")
    translated_findings = parsed["abnormal_findings"]
    normalized_meds = parsed["medications"]
    translated_discussion = parsed["doctor_discussion_points"]
    translated_ui_labels = {**parsed["ui_labels"], "_source_fingerprint": source_fingerprint}
    if "translated_parameters" in parsed and isinstance(parsed["translated_parameters"], dict):
        for k, v in parsed["translated_parameters"].items():
            translated_ui_labels[f"param_{k}"] = v

    # Keep the previous row until generation succeeds; replace it atomically.
    if translation is not None:
        await db.delete(translation)
        await db.flush()

    translation = AnalysisTranslation(
        report_analysis_id=analysis.id,
        language=lang,
        schema_version=TRANSLATION_SCHEMA_VERSION,
        patient_summary=translated_summary,
        clinician_summary=translated_clinical_summary,
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
        clinician_summary=translation.clinician_summary,
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
