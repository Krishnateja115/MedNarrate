from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, desc
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.report import Report, ReportType, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.schemas.report import ReportOut, ReportUpdate, ComparePoint, ComparePreviousResult
from app.services.file_storage import save_upload_file, delete_file
from app.services.prompts import COMPARISON_PROMPT
from app.services.llm_client import generate
from datetime import date
from typing import Optional, List

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

@router.get("/compare", response_model=List[ComparePoint])
async def compare_reports(
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
    stmt = select(Report).where(Report.id == id, Report.user_id == current_user.id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.patch("/{id}", response_model=ReportOut)
async def update_report(
    id: str,
    update_data: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Report).where(Report.id == id, Report.user_id == current_user.id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
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
    stmt = select(Report).where(Report.id == id, Report.user_id == current_user.id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    delete_file(report.file_path)
    
    await db.delete(report)
    await db.commit()

@router.get("/{id}/compare-previous", response_model=ComparePreviousResult)
async def compare_previous(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Report).where(Report.id == id, Report.user_id == current_user.id)
    result = await db.execute(stmt)
    current_report = result.scalars().first()
    if not current_report:
        raise HTTPException(status_code=404, detail="Report not found")
        
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
