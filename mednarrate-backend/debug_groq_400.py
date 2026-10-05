import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def main():
    engine = create_async_engine('sqlite+aiosqlite:///mednarrate.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        res = await session.execute(text("SELECT patient_summary, clinician_summary, abnormal_findings, structured_lab_values FROM report_analyses WHERE report_id='1ebb5ebd2a864602a93914489e999123'"))
        row = res.fetchone()
        from app.services.translation_planner import _build_chunks
        from app.services.prompts import TRANSLATION_PROMPT
        import json, os, requests
        patient_summary, clinician_summary, abnormal_findings, structured_lab_values = row
        abnormal_findings_source = json.loads(abnormal_findings) if isinstance(abnormal_findings, str) else []
        structured_lab_values_source = json.loads(structured_lab_values) if isinstance(structured_lab_values, str) else []
        unique_params = []
        chunks = _build_chunks(clinician_summary, patient_summary, abnormal_findings_source, [], unique_params, 1500)
        from app.core.config import settings
        api_key = settings.GROQ_API_KEY
        chunk = chunks[0]
        prompt = TRANSLATION_PROMPT.format(
            target_language='Hindi',
            clinician_summary=chunk["clinician_summary"],
            patient_summary=chunk["patient_summary"],
            abnormal_findings_json=json.dumps(chunk["abnormal_findings"], ensure_ascii=False),
            medications_json="[]",
            unique_parameters_json=json.dumps(chunk["unique_params"], ensure_ascii=False),
        )
        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2, "max_tokens": 3000,
            "response_format": {"type": "json_object"}
        }
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers={"Authorization": f"Bearer {api_key}"})
        print("Status:", resp.status_code)
        print("Resp:", resp.text[:500])

asyncio.run(main())
