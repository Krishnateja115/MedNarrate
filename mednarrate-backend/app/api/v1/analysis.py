from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.report import Report, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.models.analysis_translation import AnalysisTranslation
from app.schemas.report import ReportAnalysisOut, TranslationRequest, TranslationOut, ReportStatusOut
from app.middleware.ownership import verify_report_ownership
from app.services.analysis_pipeline import run_analysis
from app.services.llm_client import generate
from app.services.prompts import TRANSLATION_PROMPT
from typing import Dict, Any
import json
router = APIRouter()

@router.post("/{id}/process", status_code=202)
async def process_report(
    id: str,
    background_tasks: BackgroundTasks,
    force: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await verify_report_ownership(id, str(current_user.id), db)
    
    if report.processing_status in [ProcessingStatus.processing, ProcessingStatus.completed] and not force:
        raise HTTPException(status_code=409, detail="Report is already processing or completed")
        
    report.processing_status = ProcessingStatus.processing
    await db.commit()
    
    background_tasks.add_task(run_analysis, report.id)
    
    return {"processing_status": "processing"}

@router.get("/{id}/status", response_model=ReportStatusOut)
async def get_report_status(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await verify_report_ownership(id, str(current_user.id), db)
    
    status_dict = {"processing_status": report.processing_status.value}
    
    if report.processing_status == ProcessingStatus.failed:
        stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
        res_analysis = await db.execute(stmt_analysis)
        analysis = res_analysis.scalars().first()
        status_dict["error_reason"] = analysis.error_reason if analysis else "Unknown error"
    else:
        status_dict["error_reason"] = None
        
    return status_dict

@router.get("/{id}/analysis", response_model=ReportAnalysisOut)
async def get_report_analysis(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await verify_report_ownership(id, str(current_user.id), db)
        
    stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
    res_analysis = await db.execute(stmt_analysis)
    analysis = res_analysis.scalars().first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found. Call /process first.")
        
    # Check for translation
    pref_lang = current_user.preferred_language or "en"
    analysis_out = ReportAnalysisOut.model_validate(analysis)
    
    if pref_lang != "en":
        stmt_trans = select(AnalysisTranslation).where(
            AnalysisTranslation.report_analysis_id == analysis.id,
            AnalysisTranslation.language == pref_lang
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
    db: AsyncSession = Depends(get_db)
):
    report = await verify_report_ownership(id, str(current_user.id), db)
        
    stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
    res_analysis = await db.execute(stmt_analysis)
    analysis = res_analysis.scalars().first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    lang = req.language
    if lang == "en":
        return TranslationOut(language="en", patient_summary=analysis.patient_summary or "", findings_json=[])
        
    stmt_trans = select(AnalysisTranslation).where(
        AnalysisTranslation.report_analysis_id == analysis.id,
        AnalysisTranslation.language == lang
    )
    res_trans = await db.execute(stmt_trans)
    translation = res_trans.scalars().first()
    
    if translation:
        # Cache hit
        return TranslationOut(
            language=lang,
            patient_summary=translation.patient_summary,
            findings_json=translation.findings_json
        )
        
    # Cache miss - translate
    prompt = TRANSLATION_PROMPT.format(
        target_language=lang,
        patient_summary=analysis.patient_summary or "",
        abnormal_findings_json=json.dumps(analysis.abnormal_findings, indent=2)
    )
    
    response_text = await generate(prompt)
    
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
        translated_summary = parsed.get("patient_summary", "[Translation failed]")
        translated_findings = parsed.get("abnormal_findings", [])
    except json.JSONDecodeError:
        # Fallback if LLM failed to return valid JSON
        translated_summary = "[Translation Parsing Error] " + response_text[:100]
        translated_findings = []
        

    translation = AnalysisTranslation(
        report_analysis_id=analysis.id,
        language=lang,
        patient_summary=translated_summary,
        findings_json=translated_findings
    )
    db.add(translation)
    await db.commit()
    await db.refresh(translation)
    
    return TranslationOut(
        language=lang,
        patient_summary=translation.patient_summary,
        findings_json=translation.findings_json
    )
