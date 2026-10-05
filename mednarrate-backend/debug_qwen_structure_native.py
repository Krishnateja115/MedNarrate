import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.services.translation_planner import _build_chunks
from app.services.prompts import TRANSLATION_PROMPT
from app.services.llm_client import generate_translation_with_provider
import json

async def main():
    engine = create_async_engine('sqlite+aiosqlite:///mednarrate.db')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        res = await session.execute(text("SELECT patient_summary, clinician_summary, abnormal_findings, structured_lab_values FROM report_analyses WHERE report_id='1ebb5ebd2a864602a93914489e999123'"))
        row = res.fetchone()
        
        patient_summary, clinician_summary, abnormal_findings, structured_lab_values = row
        abnormal_findings_source = json.loads(abnormal_findings) if isinstance(abnormal_findings, str) else []
        
        chunks = _build_chunks(clinician_summary, patient_summary, abnormal_findings_source, [], [], 1500)
        chunk = chunks[0]
        
        prompt = TRANSLATION_PROMPT.format(
            target_language='Hindi',
            clinician_summary=chunk["clinician_summary"],
            patient_summary=chunk["patient_summary"],
            abnormal_findings_json="[]",
            medications_json="[]",
            unique_parameters_json="[]",
        )
        
        print("Sending request to Groq Qwen using native backend function...")
        try:
            # This calls GroqProvider("qwen").generate() which does the exact backend logic
            result = await generate_translation_with_provider(prompt, "groq_qwen")
            content = result["content"]
            
            with open("qwen_debug.txt", "w", encoding="utf-8") as f:
                f.write("\n--- RAW CONTENT STRUCTURE (First 200 chars) ---\n")
                f.write(content[:200])
                f.write("\n--- END RAW CONTENT ---\n\n")
                
                try:
                    parsed_content = json.loads(content)
                    f.write("JSON Parsing: SUCCESS\n")
                    f.write("\nTop-level keys in parsed JSON:\n")
                    for k in parsed_content.keys():
                        v = parsed_content[k]
                        v_type = type(v).__name__
                        if v_type == 'list':
                            f.write(f"  - {k}: list (length {len(v)})\n")
                        elif v_type == 'dict':
                            f.write(f"  - {k}: dict (keys: {len(v.keys())})\n")
                        elif v_type == 'str':
                            f.write(f"  - {k}: str (length {len(v)})\n")
                            if not v.strip():
                                f.write(f"      WARNING: {k} is empty string\n")
                        else:
                            f.write(f"  - {k}: {v_type}\n")
                except Exception as e:
                    f.write(f"JSON Parsing: FAILED - {e}\n")
            print("Successfully wrote to qwen_debug.txt")
        except Exception as e:
            print(f"Failed with exception: {e}")

asyncio.run(main())
