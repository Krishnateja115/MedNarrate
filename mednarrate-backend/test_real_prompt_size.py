import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.core.config import settings
from app.models.report_analysis import ReportAnalysis
from app.models.medication_schedule import MedicationSchedule
from app.api.v1.analysis import TRANSLATION_PROMPT
import json
import os

async def main():
    engine = create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as db:
        stmt = select(ReportAnalysis)
        res = await db.execute(stmt)
        analysis = res.scalars().first()
        if not analysis:
            print("No analysis found")
            return
            
        stmt_meds = select(MedicationSchedule).where(MedicationSchedule.report_id == analysis.report_id)
        res_meds = await db.execute(stmt_meds)
        meds = res_meds.scalars().all()

        abnormal_findings_source = analysis.abnormal_findings or []
        meds_list = [
            {
                "id": str(m.id),
                "medication_name": m.medication_name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "times_of_day": m.times_of_day or [],
                "duration_days": m.duration_days,
                "notes": m.notes,
                "provenance": getattr(m, "provenance", "REPORT_EXTRACTED") or "REPORT_EXTRACTED",
            }
            for m in meds
        ]
        unique_params = list(
            set(
                [
                    str(m.get("test_name"))
                    for m in (analysis.structured_lab_values or [])
                    if m.get("test_name")
                ]
                + [
                    str(f.get("test_name"))
                    for f in abnormal_findings_source
                    if f.get("test_name")
                ]
            )
        )

        prompt = TRANSLATION_PROMPT.format(
            target_language="Hindi",
            clinician_summary=analysis.clinician_summary or "",
            patient_summary=analysis.patient_summary or "",
            abnormal_findings_json=json.dumps(abnormal_findings_source, ensure_ascii=False),
            medications_json=json.dumps(meds_list, ensure_ascii=False),
            unique_parameters_json=json.dumps(unique_params, ensure_ascii=False),
        )
        
        print("Prompt character count:", len(prompt))
        print("Prompt estimated tokens (chars/3.5):", len(prompt)//3.5)
        print("Max output tokens:", min(settings.TRANSLATION_MAX_OUTPUT_TOKENS, 4096))
        print("Total estimated tokens:", len(prompt)//3.5 + min(settings.TRANSLATION_MAX_OUTPUT_TOKENS, 4096))

asyncio.run(main())
