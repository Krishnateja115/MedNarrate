import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.services.prompts import TRANSLATION_PROMPT
import json
import os
import requests

async def main():
    engine = create_async_engine('sqlite+aiosqlite:///mednarrate.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        res = await session.execute(text("SELECT patient_summary, clinician_summary, abnormal_findings, structured_lab_values FROM report_analyses WHERE report_id='1ebb5ebd-2a86-4602-a939-14489e999123'"))
        row = res.fetchone()
        
        if row:
            patient_summary, clinician_summary, abnormal_findings, structured_lab_values = row
            
            try:
                abnormal_findings_source = json.loads(abnormal_findings) if isinstance(abnormal_findings, str) else abnormal_findings
                structured_lab_values_source = json.loads(structured_lab_values) if isinstance(structured_lab_values, str) else structured_lab_values
            except Exception:
                abnormal_findings_source = []
                structured_lab_values_source = []
                
            unique_params = list(
                set(
                    [str(m.get("test_name")) for m in (structured_lab_values_source or []) if m.get("test_name")] +
                    [str(f.get("test_name")) for f in (abnormal_findings_source or []) if f.get("test_name")]
                )
            )

            prompt = TRANSLATION_PROMPT.format(
                target_language='Hindi',
                clinician_summary=clinician_summary or "",
                patient_summary=patient_summary or "",
                abnormal_findings_json=json.dumps(abnormal_findings_source, ensure_ascii=False),
                medications_json="[]",
                unique_parameters_json=json.dumps(unique_params, ensure_ascii=False),
            )
            
            api_key = os.environ.get('GROQ_API_KEY')
            if not api_key:
                from app.core.config import settings
                api_key = settings.GROQ_API_KEY

            payload = {
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1000
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            print("Status:", response.status_code)
            print("Response:", response.text)

asyncio.run(main())
