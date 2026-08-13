from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.report import Report, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.models.analysis_translation import AnalysisTranslation
from app.schemas.report import ReportAnalysisOut, TranslationRequest, TranslationOut
from app.services.analysis_pipeline import run_analysis
from typing import Dict, Any

router = APIRouter()

@router.post("/{id}/process", status_code=202)
async def process_report(
    id: str,
    background_tasks: BackgroundTasks,
    force: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Report).where(Report.id == id, Report.user_id == current_user.id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if not force and report.processing_status in [ProcessingStatus.processing, ProcessingStatus.completed]:
        raise HTTPException(status_code=409, detail="Report is already processing or completed")
        
    report.processing_status = ProcessingStatus.processing
    await db.commit()
    
    background_tasks.add_task(run_analysis, report.id)
    
    return {"processing_status": "processing"}

@router.get("/{id}/status")
async def get_report_status(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    stmt = select(Report).where(Report.id == id, Report.user_id == current_user.id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
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
    stmt = select(Report).where(Report.id == id, Report.user_id == current_user.id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
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
    stmt = select(Report).where(Report.id == id, Report.user_id == current_user.id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
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
    # Call to translation model (mocked/omitted for brevity, handled by model_registry in real env)
    translated_summary = "[Translated] " + (analysis.patient_summary or "")
    translated_findings = [{"test_name": f["test_name"], "translated_explanation": "[Translated explanation]"} for f in analysis.abnormal_findings]
    
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
