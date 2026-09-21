import os
import io
import json
import uuid
import logging
from datetime import datetime, timezone
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings

from app.models.report import Report, ProcessingStatus
from app.models.report_analysis import ReportAnalysis
from app.models.user import User
from app.services.text_extraction import (
    extract_text_from_file,
    clean_extracted_text,
    extract_text_with_diagnostics,
    resolve_physical_path,
    ExtractionError
)
from app.services.report_date_extractor import extract_report_date
from app.services.model_registry import get_ner_pipeline
from app.services.lab_value_extractor import extract_lab_values, extract_medication_schedule
from app.services.privacy import deidentify_prompt_text
from app.services.prompts import CLINICIAN_PROMPT, PATIENT_PROMPT, ROLE_INSTRUCTIONS, get_examples_text
from app.services.llm_client import generate, LLMConfigurationError, LLMConnectionError
from app.services.rag import process_report_for_rag, retrieve_chunks
from app.services.multilingual import translate_report_summary
from app.services.validation import validate_and_ground_analysis
from app.core.database import AsyncSessionLocal
from pydantic import ValidationError
from app.schemas.report import LabValue, AbnormalFinding, Entity

logger = logging.getLogger(__name__)

async def generate_with_timeout(prompt: str, timeout: int = 60, request_id: str | None = None):
    """Executes single LLM call with request timeout and request correlation tracking."""
    from app.services.llm_orchestrator import generate_primary_reasoning
    return await asyncio.wait_for(
        generate_primary_reasoning(prompt, request_id=request_id),
        timeout=timeout
    )

async def run_analysis(report_id: uuid.UUID, db: AsyncSession = None):
    if db is None:
        async with AsyncSessionLocal() as session:
            return await run_analysis(report_id, session)
            
    req_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    logger.info(f"[STAGE:START] req_id={req_id} Pipeline analysis started for report {report_id}")
    
    try:
        stmt = select(Report).where(Report.id == report_id)
        result = await db.execute(stmt)
        report = result.scalars().first()
        
        if not report:
            logger.error(f"[STAGE:ERROR] req_id={req_id} Report {report_id} not found in database.")
            return

        report.processing_status = ProcessingStatus.processing
        await db.commit()

        # 1. Text Extraction & Diagnostic Handling
        file_type_str = report.file_type.value if hasattr(report.file_type, 'value') else str(report.file_type)
        report_type_str = report.report_type.value if hasattr(report.report_type, 'value') else str(report.report_type)

        logger.info(f"[STAGE:EXTRACTION] req_id={req_id} Processing file: {report.file_path} ({file_type_str})")
        if not report.extracted_text or len(report.extracted_text.strip()) == 0:
            extracted = await asyncio.to_thread(
                extract_text_from_file,
                report.file_path,
                file_type_str
            )
            report.extracted_text = extracted
            
        cleaned_text = clean_extracted_text(report.extracted_text or "")
        logger.info(f"[STAGE:EXTRACTION:SUCCESS] req_id={req_id} Extracted {len(cleaned_text)} characters.")

        # Source-aware Report Date Extraction
        extracted_date = extract_report_date(cleaned_text, report.report_date)
        if extracted_date != report.report_date:
            report.report_date = extracted_date
            await db.commit()

        # 2. Run NER -> entities
        logger.info(f"[STAGE:NLP] req_id={req_id} Running biomedical NER pipeline...")
        entities = []
        try:
            ner_pipeline = await asyncio.wait_for(
                asyncio.to_thread(get_ner_pipeline),
                timeout=30.0
            )
            entities_raw = await asyncio.wait_for(
                asyncio.to_thread(
                    ner_pipeline,
                    cleaned_text[:4000]
                ),
                timeout=30.0
            )
            for ent in entities_raw:
                ent['score'] = float(ent['score'])
                try:
                    valid_ent = Entity(**ent).model_dump()
                    entities.append(valid_ent)
                except ValidationError as ve:
                    logger.warning(f"[STAGE:NLP:WARN] req_id={req_id} Discarding invalid entity (validation error).")
            logger.info(f"[STAGE:NLP:SUCCESS] req_id={req_id} Identified {len(entities)} entities.")
        except asyncio.TimeoutError:
            logger.warning(f"[STAGE:NLP:TIMEOUT] req_id={req_id} NER loading or inference timed out after 30s. Continuing without NER entities.")
        except Exception as ner_e:
            logger.warning(f"[STAGE:NLP:FAIL] req_id={req_id} NER pipeline exception (continuing lab extraction): {ner_e}")

        # 3. Extract Structured Lab Values & Abnormal Findings
        logger.info(f"[STAGE:LAB_EXTRACT] req_id={req_id} Extracting structured lab parameters...")
        raw_lab_values = extract_lab_values(cleaned_text, report_type=report_type_str)
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
                        logger.warning(f"[STAGE:LAB_EXTRACT:WARN] req_id={req_id} Discarding invalid abnormal finding (validation error).")
                    except Exception as ve2:
                        pass
            except Exception as ve:
                logger.warning(f"[STAGE:LAB_EXTRACT:WARN] req_id={req_id} Discarding invalid lab value (validation error).")
                
        logger.info(f"[STAGE:LAB_EXTRACT:SUCCESS] req_id={req_id} Extracted {len(structured_lab_values)} lab values ({len(abnormal_findings)} abnormal).")

        # 4. RAG Processing & Retrieval
        logger.info(f"[STAGE:RAG] req_id={req_id} Processing report chunks for RAG index...")
        rag_retrieved = False
        retrieved_chunks_count = 0
        rag_context = ""
        try:
            await process_report_for_rag(report.id, cleaned_text, db)
            rag_context = await retrieve_chunks(query=cleaned_text[:500], report_id=report.id, db=db, top_k=3)
            if rag_context and rag_context.strip():
                rag_retrieved = True
                retrieved_chunks_count = rag_context.count("[Chunk ")
            logger.info(f"[STAGE:RAG:SUCCESS] req_id={req_id} Report processed for RAG. Retrieved {retrieved_chunks_count} chunks.")
        except Exception as rag_e:
            logger.warning(f"[STAGE:RAG:FAIL] req_id={req_id} RAG indexing/retrieval failed: {rag_e}")

        prompt_has_rag = bool(rag_context and rag_context.strip())

        # 5. User Role & Prompt Preparation with Privacy De-identification
        user_stmt = select(User).where(User.id == report.user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalars().first()
        user_role = (user.role.value if hasattr(user.role, 'value') else str(user.role)) if user else "patient"

        # Apply Privacy boundary to report text before prompt assembly
        deidentified_text = deidentify_prompt_text(cleaned_text)

        structured_values_json = json.dumps(structured_lab_values, indent=2)

        clinician_prompt = CLINICIAN_PROMPT.format(
            report_type=report_type_str,
            structured_values_json=structured_values_json,
            extracted_text=deidentified_text,
            rag_context=rag_context or "None"
        )

        role_instruction = ROLE_INSTRUCTIONS.get(user_role, ROLE_INSTRUCTIONS["patient"])
        examples = get_examples_text()
        patient_prompt = PATIENT_PROMPT.format(
            report_type=report_type_str,
            extracted_text=deidentified_text,
            structured_values_json=structured_values_json,
            user_role=user_role,
            role_specific_instruction=role_instruction,
            rag_context=rag_context or "None",
            examples=examples
        )

        # 6. LLM Generation with Request Correlation
        logger.info(f"[STAGE:LLM] req_id={req_id} Generating summaries via configured LLM provider...")
        from app.services.llm_orchestrator import verify_medical_facts
        clinician_summary = await generate_with_timeout(clinician_prompt, timeout=settings.LLM_TIMEOUT_SECONDS, request_id=req_id)
        patient_summary = await generate_with_timeout(patient_prompt, timeout=settings.LLM_TIMEOUT_SECONDS, request_id=req_id)
        logger.info(f"[STAGE:LLM:SUCCESS] req_id={req_id} Generated clinician and patient summaries.")


        # 7. Medical Validation & Grounding Layer
        logger.info(f"[STAGE:VALIDATION] Validating generated analysis against source document using Medical Verifier...")
        # Old synchronous regex/heuristic validation
        validation_res = validate_and_ground_analysis(
            extracted_text=cleaned_text,
            structured_lab_values=structured_lab_values,
            patient_summary=patient_summary,
            clinician_summary=clinician_summary
        )
        patient_summary = validation_res["patient_summary"]
        clinician_summary = validation_res["clinician_summary"]
        structured_lab_values = validation_res["structured_lab_values"]

        # NEW LLM-based verification using MedGemma (Medical Verifier)
        # We verify the clinician_summary as it is the most critical medical output
        verification_result = await verify_medical_facts(clinician_summary, request_id=req_id)
        if not verification_result["is_valid"]:
            # If the verifier flags dangerous errors, we append the correction warning
            clinician_summary += f"\n\n[WARNING from Medical Verifier]: {verification_result['correction']}"
            patient_summary += "\n\n[Note: This summary has been flagged by the automated verification system and requires doctor review.]"
            logger.warning(f"[STAGE:VALIDATION:FAILED] Medical Verifier flagged output. Correction: {verification_result['correction']}")

        # Pre-generate translations safely
        try:
            await translate_report_summary(str(report.id), patient_summary, "hi", db)
            await translate_report_summary(str(report.id), patient_summary, "te", db)
        except Exception as tr_e:
            logger.warning(f"[STAGE:TRANSLATION:WARN] Pre-generation of translations failed: {tr_e}")

        # Extract and persist medications
        try:
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
        except Exception as med_e:
            logger.warning(f"[STAGE:MEDICATION:WARN] Medication extraction failed: {med_e}")

        # 8. Database Persistence & Final Completion
        stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
        res_analysis = await db.execute(stmt_analysis)
        analysis = res_analysis.scalars().first()

        if not analysis:
            analysis = ReportAnalysis(report_id=report.id)
            db.add(analysis)

        analysis.structured_lab_values = structured_lab_values
        analysis.entities = entities
        analysis.abnormal_findings = abnormal_findings
        analysis.evidence_sources = []
        analysis.clinician_summary = clinician_summary
        analysis.patient_summary = patient_summary
        analysis.processed_at = datetime.now(timezone.utc)
        analysis.error_reason = None

        report.processing_status = ProcessingStatus.completed
        await db.commit()
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(f"[STAGE:COMPLETE] Report {report_id} analysis completed successfully in {duration:.2f}s.")

    except ExtractionError as ee:
        failure_cat = getattr(ee, 'failure_category', 'EXTRACTION_ERROR')
        logger.error(f"[STAGE:FAIL] Extraction failed for report {report_id} [{failure_cat}]: {ee}")
        if 'report' in locals() and report:
            report.processing_status = ProcessingStatus.failed
            
            stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
            res_analysis = await db.execute(stmt_analysis)
            analysis = res_analysis.scalars().first()
            if not analysis:
                analysis = ReportAnalysis(report_id=report.id)
                db.add(analysis)
            analysis.error_reason = str(ee)
            analysis.failure_category = failure_cat
            
            await db.commit()

    except (LLMConfigurationError, LLMConnectionError) as llm_e:
        # LLM not configured or unreachable — store a clean, user-facing message
        # instead of the raw traceback that the generic handler would produce.
        is_config_error = isinstance(llm_e, LLMConfigurationError)
        failure_cat = "LLM_NOT_CONFIGURED" if is_config_error else "LLM_GENERATION_ERROR"
        clean_msg = (
            "AI analysis is unavailable: the AI service is not configured on this server. "
            "Please contact support."
            if is_config_error else
            "AI analysis failed because the AI service could not be reached. Please try again later."
        )
        logger.error(f"[STAGE:FAIL] LLM error for report {report_id} [{failure_cat}]: {llm_e}")

        if 'report' in locals() and report:
            report.processing_status = ProcessingStatus.failed

            stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
            res_analysis = await db.execute(stmt_analysis)
            analysis = res_analysis.scalars().first()
            if not analysis:
                analysis = ReportAnalysis(report_id=report.id)
                db.add(analysis)
            analysis.error_reason = clean_msg
            analysis.failure_category = failure_cat

            await db.commit()

    except Exception as e:
        import traceback
        failure_cat = getattr(e, 'failure_category', 'PIPELINE_ERROR')
        logger.error(f"[STAGE:FAIL] Pipeline failed for report {report_id}: {repr(e)}\n{traceback.format_exc()}")

        if 'report' in locals() and report:
            report.processing_status = ProcessingStatus.failed
            
            stmt_analysis = select(ReportAnalysis).where(ReportAnalysis.report_id == report.id)
            res_analysis = await db.execute(stmt_analysis)
            analysis = res_analysis.scalars().first()
            if not analysis:
                analysis = ReportAnalysis(report_id=report.id)
                db.add(analysis)
            analysis.error_reason = str(e)
            analysis.failure_category = failure_cat
            
            await db.commit()

