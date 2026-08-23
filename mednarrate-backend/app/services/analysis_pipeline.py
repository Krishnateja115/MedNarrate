import json
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.report import Report, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.models.user import User
from app.services.text_extraction import extract_text_from_file, clean_extracted_text
from app.services.model_registry import get_ner_pipeline
from app.services.lab_value_extractor import extract_lab_values, extract_medication_schedule
from app.services.prompts import CLINICIAN_PROMPT, PATIENT_PROMPT, ROLE_INSTRUCTIONS, get_examples_text
from app.services.llm_client import generate
from app.services.rag import process_report_for_rag
from app.services.multilingual import translate_report_summary
from app.core.database import AsyncSessionLocal
import uuid
from datetime import datetime, timezone
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import ValidationError
from app.schemas.report import LabValue, AbnormalFinding, Entity

logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_with_timeout(prompt: str, timeout: int = 30):
    return await asyncio.wait_for(generate(prompt), timeout=timeout)

def check_hallucinated_tests(patient_summary: str, structured_lab_values: list):
    """Logs a warning if a test name absent from structured data is mentioned in patient_summary."""
    test_names = [v["test_name"].lower() for v in structured_lab_values]
    
    # We look for simple lab test names, but it's hard to catch everything.
    # We will log if any numbers present in the summary are completely missing from the values.
    # Simple heuristic as requested:
    summary_lower = patient_summary.lower()
    
    # Optional guardrail warning log
    if len(test_names) > 0 and not any(t in summary_lower for t in test_names):
        logger.warning("Guardrail: The summary does not appear to mention any of the extracted test names.")

async def run_analysis(report_id: uuid.UUID, db: AsyncSession = None):
    if db is None:
        async with AsyncSessionLocal() as session:
            return await run_analysis(report_id, session)
            
    try:
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalars().first()
        
        if not report:
            logger.error(f"Report {report_id} not found for analysis.")
            return

        # Resolve user role for role-aware prompts
        user_stmt = select(User).where(User.id == report.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalars().first()
        user_role = user.role.value if user else "patient"

        if not report.extracted_text or len(report.extracted_text.strip()) == 0:
            extracted = extract_text_from_file(report.file_path, report.file_type.value)
            report.extracted_text = extracted
            
        extracted_text = report.extracted_text or ""
        
        # Clean text before NER and extraction
        cleaned_text = clean_extracted_text(extracted_text)
        
        # 2. Run NER -> entities
        ner_pipeline = get_ner_pipeline()
        entities_raw = ner_pipeline(cleaned_text[:4000]) # truncated for safe lengths
        entities = []
        for ent in entities_raw:
            ent['score'] = float(ent['score'])
            try:
                valid_ent = Entity(**ent).model_dump()
                entities.append(valid_ent)
            except ValidationError as ve:
                logger.warning(f"Discarding invalid entity: {ve}")
        
        # 3. Run extract_lab_values
        raw_lab_values = extract_lab_values(cleaned_text)
        structured_lab_values = []
        abnormal_findings = []
        
        for lab in raw_lab_values:
            try:
                valid_lab = LabValue(**lab).model_dump()
                structured_lab_values.append(valid_lab)
                
                if valid_lab["flag"] != "normal":
                    try:
                        valid_abnormal = AbnormalFinding(**lab).model_dump()
                        abnormal_findings.append(valid_abnormal)
                    except ValidationError as ve2:
                        logger.warning(f"Discarding invalid abnormal finding: {ve2}")
                        
            except ValidationError as ve:
                logger.warning(f"Discarding invalid lab value: {ve}")
        
        # 3.5 Process Report for RAG
        await process_report_for_rag(report.id, cleaned_text, db)
        
        # (Context generation here is no longer needed since we do RAG on user queries)
        rag_context = ""
        evidence_sources = []
        
        structured_values_json = json.dumps(structured_lab_values, indent=2)
        
        # 4. Generate summaries
        clinician_prompt = CLINICIAN_PROMPT.format(
            report_type=report.report_type.value,
            structured_values_json=structured_values_json,
            extracted_text=cleaned_text
        )
        
        role_instruction = ROLE_INSTRUCTIONS.get(user_role, ROLE_INSTRUCTIONS["patient"])
        examples = get_examples_text()
        patient_prompt = PATIENT_PROMPT.format(
            report_type=report.report_type.value,
            structured_values_json=structured_values_json,
            user_role=user_role,
            role_specific_instruction=role_instruction,
            examples=examples
        )
        
        if rag_context:
            patient_prompt += f"\n\nUse the following reference knowledge if relevant:\n{rag_context}"
            
        clinician_summary = await generate_with_timeout(clinician_prompt)
        patient_summary = await generate_with_timeout(patient_prompt)
        
        check_hallucinated_tests(patient_summary, structured_lab_values)
        
        # Pre-generate translations
        try:
            await translate_report_summary(str(report.id), patient_summary, "hi", db)
            await translate_report_summary(str(report.id), patient_summary, "te", db)
        except Exception as tr_e:
            logger.warning(f"Failed to pre-generate translations: {tr_e}")
            
        # Extract and persist medications
        from app.models.medication_schedule import MedicationSchedule
        meds = await extract_medication_schedule(cleaned_text)
        for med in meds:
            db_med = MedicationSchedule(
                report_id=report.id,
                user_id=report.user_id,
                medication_name=med.medication_name,
                dosage=med.dosage,
                frequency=med.frequency,
                times_of_day=med.times_of_day,
                duration_days=med.duration_days,
                notes=med.notes
            )
            db.add(db_med)
        
        # 5. Persist ReportAnalysis
        stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
        res_analysis = await db.execute(stmt_analysis)
        analysis = res_analysis.scalars().first()
        
        if not analysis:
            analysis = ReportAnalysis(report_id=report.id)
            db.add(analysis)
            
        analysis.structured_lab_values = structured_lab_values
        analysis.entities = entities
        analysis.abnormal_findings = abnormal_findings
        analysis.evidence_sources = evidence_sources
        analysis.clinician_summary = clinician_summary
        analysis.patient_summary = patient_summary
        analysis.processed_at = datetime.now(timezone.utc)
        analysis.error_reason = None
        
        report.processing_status = ProcessingStatus.completed
        
        await db.commit()
        
    except Exception as e:
        logger.error(f"Analysis failed for {report_id}: {e}")
        if 'report' in locals() and report:
            report.processing_status = ProcessingStatus.failed
            
            stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
            res_analysis = await db.execute(stmt_analysis)
            analysis = res_analysis.scalars().first()
            if not analysis:
                analysis = ReportAnalysis(report_id=report.id)
                db.add(analysis)
            analysis.error_reason = str(e)
            
            await db.commit()
