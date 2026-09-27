import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.report_analysis import ReportAnalysis
from app.models.medication_schedule import MedicationSchedule
from app.services.llm_client import llm_client_instance
from app.services.prompts import TRANSLATION_PROMPT
import json

async def test_translation():
    async with AsyncSessionLocal() as session:
        stmt = select(ReportAnalysis).where(ReportAnalysis.report_id == '159351a2adc546cdb7facda28a7810a8')
        res = await session.execute(stmt)
        analysis = res.scalars().first()
        
        stmt_meds = select(MedicationSchedule).where(MedicationSchedule.report_id == analysis.report_id)
        res_meds = await session.execute(stmt_meds)
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
        
        prompt = TRANSLATION_PROMPT.format(
            target_language="Telugu",
            patient_summary=analysis.patient_summary or "",
            abnormal_findings_json=json.dumps(analysis.abnormal_findings, indent=2),
            medications_json=json.dumps(meds_list, indent=2),
        )
        print("PROMPT LENGTH:", len(prompt))
        
        provider = llm_client_instance.get_provider("dev_gemini")
        try:
            res = await provider.generate(prompt)
            content = res.get("content", "")
            print("RESPONSE LENGTH:", len(content))
            
            with open("test_out.json", "w", encoding="utf-8") as f:
                f.write(content)
                
            # Strip markdown
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                parsed = json.loads(content)
                print("JSON PARSED SUCCESS")
            except Exception as e:
                print("JSON PARSE ERROR:", e)
                print("CONTENT:", repr(content[:500]))
                
        except Exception as e:
            print("FAILED:", str(e))

asyncio.run(test_translation())
