from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response
import csv
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, desc
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.report import Report, ReportType, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.middleware.ownership import verify_report_ownership
from app.schemas.report import ReportOut, ReportUpdate, ComparePoint, ComparePreviousResult
from app.services.file_storage import save_upload_file, delete_file
from app.services.prompts import COMPARISON_PROMPT
from app.services.llm_client import generate
from datetime import date
from typing import Optional, List
from app.schemas.report import ReportOut, ReportUpdate, ComparePoint, ComparePreviousResult, TranslationRequest, TranslationOut, ReportComparisonResult, ParameterComparison, LabValuePoint
from app.services.multilingual import translate_report_summary, LANGUAGE_MAP
from app.services.lab_value_normalizer import normalize_parameter_name
from app.services.prompts import TREND_NARRATIVE_PROMPT

router = APIRouter()

@router.post("/upload", response_model=ReportOut, status_code=201)
async def upload_report(
    title: str = Form(...),
    report_date: date = Form(...),
    report_type: ReportType = Form(...),
    hospital: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validation and saving happens in the service
    file_path = await save_upload_file(current_user.id, file)
    
    file_type_str = file.filename.split(".")[-1].lower()
    file_type = "pdf" if file_type_str == "pdf" else "image"
    
    new_report = Report(
        user_id=current_user.id,
        title=title,
        hospital=hospital,
        report_date=report_date,
        file_name=file.filename,
        file_path=file_path,
        file_type=file_type,
        report_type=report_type,
        processing_status=ProcessingStatus.uploaded
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    return new_report

@router.get("", response_model=List[ReportOut])
async def list_reports(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    report_type: Optional[ReportType] = Query(None),
    is_favourite: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Report).where(Report.user_id == current_user.id)
    
    if report_type:
        stmt = stmt.where(Report.report_type == report_type)
    if is_favourite is not None:
        stmt = stmt.where(Report.is_favourite == is_favourite)
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Report.title.ilike(search_term),
                Report.hospital.ilike(search_term)
            )
        )
        
    stmt = stmt.order_by(desc(Report.uploaded_at)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    reports = result.scalars().all()
    return reports

@router.get("/trend", response_model=List[ComparePoint])
async def get_test_trend(
    test_name: str,
    limit: int = Query(10, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # query structured_lab_values across the current user's completed ReportAnalysis rows
    stmt = select(Report, ReportAnalysis).join(ReportAnalysis, Report.id == ReportAnalysis.report_id)\
        .where(Report.user_id == current_user.id, Report.processing_status == ProcessingStatus.completed)\
        .order_by(Report.report_date.asc())
        
    result = await db.execute(stmt)
    rows = result.all()
    
    points = []
    for report, analysis in rows:
        for val in analysis.structured_lab_values:
            if val["test_name"].lower() == test_name.lower():
                points.append(ComparePoint(
                    report_id=report.id,
                    report_date=report.report_date,
                    value=val["value"],
                    unit=val["unit"],
                    flag=val["flag"]
                ))
                break
                
    return points[-limit:]

@router.get("/{id}", response_model=ReportOut)
async def get_report(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await verify_report_ownership(id, str(current_user.id), db)
    return report

@router.patch("/{id}", response_model=ReportOut)
async def update_report(
    id: str,
    update_data: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await verify_report_ownership(id, str(current_user.id), db)
        
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(report, field, value)
        
    await db.commit()
    await db.refresh(report)
    return report

@router.delete("/{id}", status_code=204)
async def delete_report(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await verify_report_ownership(id, str(current_user.id), db)
        
    await delete_file(report.file_path)
    
    await db.delete(report)
    await db.commit()

@router.get("/{id}/compare-previous", response_model=ComparePreviousResult)
async def compare_previous(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_report = await verify_report_ownership(id, str(current_user.id), db)
        
    stmt_prev = select(Report)\
        .where(Report.user_id == current_user.id, Report.report_type == current_report.report_type, Report.report_date < current_report.report_date, Report.processing_status == ProcessingStatus.completed)\
        .order_by(Report.report_date.desc()).limit(1)
    result_prev = await db.execute(stmt_prev)
    prev_report = result_prev.scalars().first()
    
    if not prev_report:
        return ComparePreviousResult(comparable=False, reason="no_previous_report")
        
    stmt_curr_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == current_report.id)
    curr_analysis = (await db.execute(stmt_curr_analysis)).scalars().first()
    
    stmt_prev_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == prev_report.id)
    prev_analysis = (await db.execute(stmt_prev_analysis)).scalars().first()
    
    if not curr_analysis or not prev_analysis:
        return ComparePreviousResult(comparable=False, reason="missing_analysis")
        
    prev_vals = {v["test_name"].lower(): v for v in prev_analysis.structured_lab_values}
    curr_vals = {v["test_name"].lower(): v for v in curr_analysis.structured_lab_values}
    
    diffed_findings = []
    for t_name, curr_v in curr_vals.items():
        if t_name in prev_vals:
            prev_v = prev_vals[t_name]
            # Simple diff
            diff = curr_v["value"] - prev_v["value"]
            status = "stable"
            if abs(diff) > 0.01:
                # Basic rule: closer to ref_low / ref_high midpoint is improved, else worsened (simplified)
                status = "changed"
            diffed_findings.append({
                "test_name": curr_v["test_name"],
                "previous_value": prev_v["value"],
                "current_value": curr_v["value"],
                "unit": curr_v["unit"],
                "status": status
            })
        else:
            diffed_findings.append({
                "test_name": curr_v["test_name"],
                "current_value": curr_v["value"],
                "unit": curr_v["unit"],
                "status": "new"
            })
            
    import json
    prompt = COMPARISON_PROMPT.format(diffed_findings_json=json.dumps(diffed_findings, indent=2))
    summary = await generate(prompt)
    
    return ComparePreviousResult(
        comparable=True,
        previous_report_id=prev_report.id,
        compared_findings=diffed_findings,
        narrative_summary=summary
    )

@router.post("/{report_id}/translate", response_model=TranslationOut)
async def translate_report(
    report_id: str,
    req: TranslationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if req.language not in LANGUAGE_MAP:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported language. Supported: {', '.join(LANGUAGE_MAP.keys())}"
        )
        
    report = await verify_report_ownership(report_id, str(current_user.id), db)
        
    stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report_id)
    analysis = (await db.execute(stmt_analysis)).scalars().first()
    if not analysis or not analysis.patient_summary:
        raise HTTPException(status_code=400, detail="No patient summary available to translate")
        
    from app.models.report_translation import ReportTranslation
    # Check cache first to set the 'cached' boolean correctly
    stmt_cache = select(ReportTranslation).where(
        ReportTranslation.report_id == report_id,
        ReportTranslation.language_code == req.language
    )
    cached_translation = (await db.execute(stmt_cache)).scalars().first()
    
    if cached_translation:
        return TranslationOut(
            language=req.language,
            translated_summary=cached_translation.translated_text,
            cached=True
        )
        
    translated_text = await translate_report_summary(report_id, analysis.patient_summary, req.language, db)
    
    return TranslationOut(
        language=req.language,
        translated_summary=translated_text,
        cached=False
    )

@router.get("/compare", response_model=ReportComparisonResult)
async def compare_reports_multiple(
    report_ids: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ids = [r_id.strip() for r_id in report_ids.split(",") if r_id.strip()]
    if len(ids) < 2 or len(ids) > 5:
        raise HTTPException(status_code=400, detail="Must provide between 2 and 5 report IDs")
        
    # Verify ownership and fetch reports
    stmt = select(Report).where(Report.id.in_(ids), Report.user_id == current_user.id).order_by(Report.report_date)
    reports = (await db.execute(stmt)).scalars().all()
    
    if len(reports) != len(ids):
        raise HTTPException(status_code=404, detail="One or more reports not found or unauthorized")
        
    reports_sorted = sorted(reports, key=lambda r: r.report_date)
    
    # Fetch analyses
    stmt_analyses = select(ReportAnalysis).where(ReportAnalysis.report_id.in_([r.id for r in reports_sorted]))
    analyses = (await db.execute(stmt_analyses)).scalars().all()
    analysis_by_report_id = {str(a.report_id): a for a in analyses}
    
    # Build comparison object
    param_map = {}
    
    for report in reports_sorted:
        analysis = analysis_by_report_id.get(str(report.id))
        if not analysis:
            continue
            
        for lab in analysis.structured_lab_values:
            norm_name = normalize_parameter_name(lab['test_name'])
            
            if norm_name not in param_map:
                param_map[norm_name] = {
                    "parameter": norm_name,
                    "unit": lab['unit'],
                    "reference_range": f"{lab.get('ref_low', '')}-{lab.get('ref_high', '')}",
                    "values": []
                }
                
            # Check if this report already has a value for this param
            existing = [v for v in param_map[norm_name]["values"] if v["report_id"] == str(report.id)]
            if not existing:
                param_map[norm_name]["values"].append({
                    "report_id": str(report.id),
                    "date": report.report_date.isoformat(),
                    "value": lab['value'],
                    "status": lab['flag']
                })
                
    # Filter to parameters present in at least 2 reports and compute trends
    comparisons = []
    diffed_findings = []
    
    for param_name, data in param_map.items():
        if len(data["values"]) >= 2:
            values = data["values"]
            # Sort by date
            values.sort(key=lambda x: x["date"])
            
            # Compute changes
            for i in range(1, len(values)):
                values[i]["change_from_previous"] = round(values[i]["value"] - values[i-1]["value"], 2)
                
            first_val = values[0]["value"]
            last_val = values[-1]["value"]
            first_status = values[0]["status"]
            last_status = values[-1]["status"]
            
            trend = "stable"
            
            # Simple trend logic
            pct_change = abs((last_val - first_val) / first_val) if first_val else 0
            if pct_change <= 0.05:
                trend = "stable"
            else:
                # Normalizing?
                if first_status != "normal" and last_status == "normal":
                    trend = "improving"
                elif first_status == "normal" and last_status != "normal":
                    trend = "worsening"
                else:
                    trend = "stable"
                    
            lab_value_points = [LabValuePoint(**v) for v in values]
            
            diffed_findings.append({
                "parameter": param_name,
                "first_value": first_val,
                "last_value": last_val,
                "first_status": first_status,
                "last_status": last_status,
                "trend": trend
            })
            
            comparisons.append(ParameterComparison(
                parameter=param_name,
                unit=data["unit"],
                reference_range=data["reference_range"],
                values=lab_value_points,
                trend=trend
            ))
            
    import json
    diffed_json = json.dumps(diffed_findings, indent=2)
    prompt = TREND_NARRATIVE_PROMPT.format(diffed_findings_json=diffed_json)
    
    ai_summary = "Not enough data to compare."
    if diffed_findings:
        try:
            ai_summary = await generate(prompt)
        except Exception as e:
            ai_summary = "Comparison summary temporarily unavailable."
            
    return ReportComparisonResult(
        report_ids=[str(r.id) for r in reports_sorted],
        comparisons=comparisons,
        ai_summary=ai_summary
    )

@router.get("/{id}/export/csv")
async def export_report_csv(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = await verify_report_ownership(id, str(current_user.id), db)
    
    stmt = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
    analysis = (await db.execute(stmt)).scalars().first()
    
    if not analysis or not analysis.structured_lab_values:
        raise HTTPException(status_code=404, detail="No structured lab data available for this report")
        
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Test Name", "Value", "Unit", "Reference Low", "Reference High", "Status Flag"])
    
    for val in analysis.structured_lab_values:
        writer.writerow([
            val.get("test_name", ""),
            val.get("value", ""),
            val.get("unit", ""),
            val.get("ref_low", ""),
            val.get("ref_high", ""),
            val.get("flag", "")
        ])
        
    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=report_{id}_export.csv"
    return response
