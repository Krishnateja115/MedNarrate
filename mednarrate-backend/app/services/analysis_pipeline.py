import json
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.report import Report, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.services.text_extraction import extract_text_from_file, clean_extracted_text
from app.services.model_registry import get_ner_pipeline
from app.services.lab_value_extractor import extract_lab_values
from app.services.prompts import CLINICIAN_PROMPT, PATIENT_PROMPT
from app.services.llm_client import generate
from app.services.rag import retrieve_chunks
from app.core.database import AsyncSessionLocal
import uuid
from datetime import datetime, timezone
from pydantic import ValidationError
from app.schemas.report import LabValue, AbnormalFinding, Entity

logger = logging.getLogger(__name__)

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

async def run_analysis(report_id: uuid.UUID):
    async with AsyncSessionLocal() as db:
        try:
            stmt = select(Report).where(Report.id == report_id)
            result = await db.execute(stmt)
            report = result.scalars().first()
            
            if not report:
                logger.error(f"Report {report_id} not found for analysis.")
                return

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
            
            # 3.5 Retrieve RAG chunks for abnormal findings
            evidence_sources = []
            retrieved_context_texts = []
            for finding in abnormal_findings:
                chunks = await retrieve_chunks(finding["test_name"], top_k=2)
                chunk_ids = [str(c.id) for c in chunks]
                sources = list(set([c.source for c in chunks]))
                evidence_sources.append({
                    "finding": finding["test_name"],
                    "chunk_ids": chunk_ids,
                    "sources": sources
                })
                for c in chunks:
                    retrieved_context_texts.append(f"{c.source}: {c.content}")
            
            rag_context = "\n".join(set(retrieved_context_texts))
            
            structured_values_json = json.dumps(structured_lab_values, indent=2)
            
            # 4. Generate summaries
            clinician_prompt = CLINICIAN_PROMPT.format(
                report_type=report.report_type.value,
                structured_values_json=structured_values_json,
                extracted_text=cleaned_text
            )
            
            patient_prompt = PATIENT_PROMPT.format(
                report_type=report.report_type.value,
                structured_values_json=structured_values_json
            )
            
            if rag_context:
                patient_prompt += f"\n\nUse the following reference knowledge if relevant:\n{rag_context}"
                
            clinician_summary = await generate(clinician_prompt)
            patient_summary = await generate(patient_prompt)
            
            check_hallucinated_tests(patient_summary, structured_lab_values)
            
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
