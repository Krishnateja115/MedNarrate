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
    #region debug-point trans-backend-001
    print(f"[TRANSLATION] report_id={report.id} analysis_id={analysis.id} requested_language={lang} endpoint=POST /reports/{id}/analysis/translate")
    print(f"[TRANSLATION] abnormal_count={len(analysis.abnormal_findings or [])} medication_count={len(meds_list)} source_patient_summary_chars={len(analysis.patient_summary or '')}")
    #endregion
    if lang == "en":
        return TranslationOut(
            language="en",
            patient_summary=analysis.patient_summary or "",
            findings_json=[],
            medications_json=[],
            ui_labels={},
        )

    stmt_trans = select(AnalysisTranslation).where(
        AnalysisTranslation.report_analysis_id == analysis.id,
        AnalysisTranslation.language == lang,
    )
    res_trans = await db.execute(stmt_trans)
    translation = res_trans.scalars().first()

    if translation:
        # Cache hit
        #region debug-point trans-backend-002
        _f = getattr(translation, 'findings_json', []) or []
        _m = getattr(translation, 'medications_json', []) or []
        _u = getattr(translation, 'ui_labels', {}) or {}
        print(f"[TRANSLATION] cache_hit=true cache_language={translation.language} findings_count={len(_f)} medications_count={len(_m)} ui_labels_count={len(_u)}")
        #endregion
        if translation.patient_summary.startswith("[Translation") or translation.patient_summary.startswith("This is an automated"):
            print("[TRANSLATION] cache_invalidated_reason=stale_automated_prefix")
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
    else:
        #region debug-point trans-backend-003
        print(f"[TRANSLATION] cache_hit=false target_language_name={target_lang_name if False else LANGUAGE_MAP.get(lang, lang)} provider=gemini_json_prompt")
        #endregion

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

        # Robust extraction: strip markdown, then find outermost JSON object
        import re as _re
        raw = response_text.strip()
        # Remove ```json ... ``` or ``` ... ``` wrappers
        m = _re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw)
        if m:
            raw = m.group(1).strip()
        # Find the first '{' and the last '}' that closes it
        start = raw.find('{')
        if start == -1:
            print("PARSING SUCCESS: NO")
            print("ERROR TYPE: NoJSON")
            print("ERROR MESSAGE: No JSON object found in response")
            print(f"RAW RESPONSE: {raw[:300]}")
            print("========== TRANSLATION DEBUG END ==========\n")
            raise HTTPException(status_code=502, detail="Translation provider returned no JSON object.")
        # Walk from end backwards to find closing }
        depth = 0
        end = -1
        for i in range(len(raw) - 1, start - 1, -1):
            if raw[i] == '}':
                if depth == 0:
                    end = i
                depth += 1
            elif raw[i] == '{':
                depth -= 1
                if depth == 0:
                    break
        json_str = raw[start:end + 1] if end != -1 else raw[start:]

        try:
            parsed = json.loads(json_str)
            print(f"RESPONSE KEYS: {list(parsed.keys())}")
            print("PARSING SUCCESS: YES")
            translated_summary = parsed.get("patient_summary", "[Translation failed]")
            translated_findings = parsed.get("abnormal_findings", parsed.get("findings_json", []))
            translated_ui_labels = parsed.get("ui_labels", {})
            translated_medications = parsed.get("medications", parsed.get("medications_json", []))
            translated_discussion = parsed.get("doctor_discussion_points", parsed.get("discussion_points", []))
            #region debug-point trans-backend-004
            print(f"[TRANSLATION] llm_parse_ok=true summary_present={bool(translated_summary and translated_summary != '[Translation failed]')} findings_count={len(translated_findings)} medications_count={len(translated_medications)} ui_labels_count={len(translated_ui_labels)} doctor_discussion_count={len(translated_discussion) if isinstance(translated_discussion, list) else 0}")
            #endregion
            print("========== TRANSLATION DEBUG END ==========\n")
        except json.JSONDecodeError as e:
            print("PARSING SUCCESS: NO")
            print("ERROR TYPE: JSONDecodeError")
            print(f"ERROR MESSAGE: {str(e)}")
            print(f"CHAR POSITION: {e.pos}")
            print(f"JSON_STR LENGTH: {len(json_str)}")
            print("========== TRANSLATION DEBUG END ==========\n")
            raise HTTPException(
                status_code=502, detail=f"Translation provider returned invalid JSON at pos {e.pos}: {str(e)}"
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
