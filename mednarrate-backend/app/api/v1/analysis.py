import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.middleware.ownership import verify_report_ownership
from app.models.analysis_translation import AnalysisTranslation
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

    from app.models.medication import MedicationSchedule
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

    lang = req.language
    if lang == "en":
        return TranslationOut(
            language="en",
            patient_summary=analysis.patient_summary or "",
            findings_json=[],
        )

    stmt_trans = select(AnalysisTranslation).where(
        AnalysisTranslation.report_analysis_id == analysis.id,
        AnalysisTranslation.language == lang,
    )
    res_trans = await db.execute(stmt_trans)
    translation = res_trans.scalars().first()

    if translation:
        # Cache hit
        if translation.patient_summary.startswith("[Translation") or translation.patient_summary.startswith("This is an automated"):
            await db.delete(translation)
            await db.commit()
            translation = None
        else:
            return TranslationOut(
                language=lang,
                patient_summary=translation.patient_summary,
                findings_json=translation.findings_json,
                ui_labels=getattr(translation, 'ui_labels', {}) or {},
                medications_json=getattr(translation, 'medications_json', []) or [],
            )

    # Cache miss - translate
    LANGUAGE_MAP = {
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
        "bn": "Bengali",
        "mr": "Marathi",
    }
    target_lang_name = LANGUAGE_MAP.get(lang, lang)
    
    prompt = TRANSLATION_PROMPT.format(
        target_language=target_lang_name,
        patient_summary=analysis.patient_summary or "",
        abnormal_findings_json=json.dumps(analysis.abnormal_findings, indent=2),
        medications_json=json.dumps(meds_list, indent=2),
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
        print(f"HTTP STATUS: 200 (LLM Success)")
        print("RESPONSE RECEIVED: YES")
        
        response_text = llm_res.get("content", "")
        provider = llm_res.get("provider", "unknown")
        
        print(f"RESPONSE CONTENT TYPE: application/json")
        print(f"RESPONSE LENGTH: {len(response_text)}")
        
        if provider == "fallback":
            print("ERROR TYPE: ProviderFallback")
            print("ERROR MESSAGE: Primary LLM failed, fell back to local string.")
            print("========== TRANSLATION DEBUG END ==========\n")
            raise HTTPException(
                status_code=503, detail="Translation service is temporarily unavailable."
            )

        # Strip markdown wrappers if LLM returned them
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            parsed = json.loads(response_text)
            print(f"RESPONSE KEYS: {list(parsed.keys())}")
            print("PARSING SUCCESS: YES")
            translated_summary = parsed.get("patient_summary", "[Translation failed]")
            translated_findings = parsed.get("abnormal_findings", [])
            translated_ui_labels = parsed.get("ui_labels", {})
            translated_medications = parsed.get("medications", [])
            print("========== TRANSLATION DEBUG END ==========\n")
        except json.JSONDecodeError as e:
            print("PARSING SUCCESS: NO")
            print("ERROR TYPE: JSONDecodeError")
            print(f"ERROR MESSAGE: {str(e)}")
            print("========== TRANSLATION DEBUG END ==========\n")
            raise HTTPException(
                status_code=502, detail="Translation provider returned invalid JSON."
            )
    except Exception as e:
        print("RESPONSE RECEIVED: NO")
        print(f"ERROR TYPE: {type(e).__name__}")
        print(f"ERROR MESSAGE: {str(e)}")
        print("========== TRANSLATION DEBUG END ==========\n")
        raise

    translation = AnalysisTranslation(
        report_analysis_id=analysis.id,
        language=lang,
        patient_summary=translated_summary,
        findings_json=translated_findings,
        ui_labels=translated_ui_labels,
        medications_json=translated_medications,
    )
    db.add(translation)
    await db.commit()
    await db.refresh(translation)

    return TranslationOut(
        language=lang,
        patient_summary=translation.patient_summary,
        findings_json=translation.findings_json,
        ui_labels=getattr(translation, 'ui_labels', {}) or {},
        medications_json=getattr(translation, 'medications_json', []) or [],
    )
