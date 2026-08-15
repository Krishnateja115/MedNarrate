from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime
from app.models.report import FileType, ReportType, ProcessingStatus

class ReportStatusOut(BaseModel):
    processing_status: str
    error_reason: Optional[str] = None

class ReportOut(BaseModel):
    """
    Field names map to the existing Flutter ReportModel verbatim.
    Mapping:
    - id -> id
    - title -> title
    - hospital -> hospital
    - report_date -> reportDate
    - file_name -> fileName
    - file_path -> filePath
    - file_type -> fileType
    - report_type -> reportType
    - extracted_text -> extractedText
    - processing_status -> processingStatus
    - is_favourite -> isFavourite
    - uploaded_at -> uploadedAt
    """
    id: UUID
    title: str
    hospital: Optional[str] = None
    reportDate: date = Field(..., alias="report_date")
    fileName: str = Field(..., alias="file_name")
    filePath: str = Field(..., alias="file_path")
    fileType: FileType = Field(..., alias="file_type")
    reportType: ReportType = Field(..., alias="report_type")
    extractedText: Optional[str] = Field(None, alias="extracted_text")
    processingStatus: ProcessingStatus = Field(..., alias="processing_status")
    isFavourite: bool = Field(..., alias="is_favourite")
    uploadedAt: datetime = Field(..., alias="uploaded_at")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    hospital: Optional[str] = None
    is_favourite: Optional[bool] = None

class LabValue(BaseModel):
    test_name: str = Field(..., min_length=1)
    original_name: str = Field(..., min_length=1)
    value: float
    unit: str
    original_unit: str
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    flag: str = Field(default="normal", pattern="^(normal|low|high)$")

class Entity(BaseModel):
    entity_group: Optional[str] = None
    entity: Optional[str] = None
    score: float
    word: str
    start: Optional[int] = None
    end: Optional[int] = None

class AbnormalFinding(BaseModel):
    test_name: str
    original_name: str
    value: float
    unit: str
    flag: str
    explanation: Optional[str] = None

class ReportAnalysisOut(BaseModel):
    id: UUID
    report_id: UUID
    structured_lab_values: List[LabValue]
    entities: List[Entity]
    abnormal_findings: List[AbnormalFinding]
    evidence_sources: List[Dict[str, Any]] = []
    clinician_summary: Optional[str] = None
    patient_summary: Optional[str] = None
    translated_patient_summary: Optional[str] = None
    translation_available: bool = False
    error_reason: Optional[str] = None
    model_versions: Dict[str, Any]
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TranslationRequest(BaseModel):
    language: str

class TranslationOut(BaseModel):
    language: str
    translated_summary: str
    cached: bool

class ComparePoint(BaseModel):
    report_id: UUID
    report_date: date
    value: float
    unit: str
    flag: str

class ComparePreviousResult(BaseModel):
    comparable: bool
    reason: Optional[str] = None
    previous_report_id: Optional[UUID] = None
    compared_findings: List[Dict[str, Any]] = []
    narrative_summary: Optional[str] = None

class LabValuePoint(BaseModel):
    report_id: str
    date: str
    value: float
    status: str
    change_from_previous: Optional[float] = None

class ParameterComparison(BaseModel):
    parameter: str
    unit: str
    reference_range: str
    values: List[LabValuePoint]
    trend: str
    ai_summary: Optional[str] = None

class ReportComparisonResult(BaseModel):
    report_ids: List[str]
    comparisons: List[ParameterComparison]
    ai_summary: Optional[str] = None
