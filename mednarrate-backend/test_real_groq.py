import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.core.config import settings
from app.models.report_analysis import ReportAnalysis
from app.models.medication_schedule import MedicationSchedule
from app.api.v1.analysis import TRANSLATION_PROMPT
import json
import httpx

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
        
        print("Sending to Groq...")
        
        api_key = settings.GROQ_API_KEY
        payload = {
            "model": settings.GROQ_GPT_TRANSLATION_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            print("Status:", resp.status_code)
            if resp.status_code != 200:
                print("Error:", resp.text)
            else:
                print("Success")

asyncio.run(main())
