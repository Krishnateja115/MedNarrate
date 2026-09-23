from app.schemas.report import ReportAnalysisOut
from datetime import datetime
import uuid

# Simulate API Response serialization
model = ReportAnalysisOut(
    id=str(uuid.uuid4()),
    report_id=str(uuid.uuid4()),
    patient_summary="Mock summary",
    clinician_summary="Mock clinical",
    structured_lab_values=[],
    entities=[],
    medications=[],
    abnormal_findings=[],
    evidence_sources=[],
    llm_provider="fallback",
    llm_model="mednarrate-fallback-v1",
    processed_at=datetime.utcnow(),
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    model_versions={}
)
print(model.model_dump_json(indent=2))
