import pytest
from app.services.lab_value_extractor import extract_lab_values
from unittest.mock import patch, MagicMock

def test_extract_lab_values_basic():
    text = "Hemoglobin: 14.5 g/dL (ref 13.5 - 17.5)\nWhite Blood Cells: 5.2 10^3/µL (reference: 4.5 to 11.0)"
    results = extract_lab_values(text)
    
    assert len(results) == 2
    assert results[0]["test_name"] == "hemoglobin"
    assert results[0]["value"] == 14.5
    assert results[0]["unit"] == "g/dL"
    assert results[0]["flag"] == "normal"
    
    assert results[1]["test_name"] == "wbc_count"
    assert results[1]["value"] == 5.2
    assert results[1]["flag"] == "normal"

def test_extract_lab_values_high_low():
    text = """
    Glucose (Fasting) 115 mg/dL (70 - 99)
    Vitamin D 15 ng/mL (30 - 100)
    """
    results = extract_lab_values(text)
    
    assert len(results) == 2
    assert results[0]["test_name"] == "fasting_glucose"
    assert results[0]["value"] == 115.0
    assert results[0]["flag"] == "high"
    
    assert results[1]["test_name"] == "Vitamin D"
    assert results[1]["value"] == 15.0
    assert results[1]["flag"] == "low"

def test_extract_lab_values_no_reference():
    text = "Cholesterol 220 mg/dL"
    results = extract_lab_values(text)
    
    assert len(results) == 1
    assert results[0]["test_name"] == "cholesterol"
    assert results[0]["value"] == 220.0
    assert results[0]["ref_low"] is None

def test_extract_lab_values_unusual_units():
    text = "HbA1c 6.5 % (4.0 - 5.6)\nTSH 4.2 µIU/mL (0.4 - 4.0)"
    results = extract_lab_values(text)
    
    assert len(results) == 2
    assert results[0]["test_name"] == "HbA1c"
    assert results[0]["unit"] == "%"
    assert results[0]["flag"] == "high"

def test_extract_lab_values_edge_cases():
    text = """
    Test With-Dash 12.3 (10 - 15)
    Empty Ref Test 5.0 ( - )
    Test Without Space:4.5g/L
    """
    results = extract_lab_values(text)
    
    assert results[0]["test_name"] == "Test With-Dash"
    assert results[0]["value"] == 12.3
    
    assert results[1]["test_name"] == "Empty Ref Test"
    assert results[1]["value"] == 5.0
    
    assert results[2]["test_name"] == "Test Without Space"
    assert results[2]["value"] == 4.5
    assert results[2]["unit"] == "g/L"


@pytest.mark.asyncio
@patch("app.services.analysis_pipeline.get_ner_pipeline")
@patch("app.services.analysis_pipeline.generate")
@patch("app.services.analysis_pipeline.extract_text_from_file")
async def test_run_analysis_mocked(mock_extract, mock_generate, mock_ner, db_session):
    db = db_session
    from app.services.analysis_pipeline import run_analysis
    from app.models.report import Report, ProcessingStatus
    from app.models.report_analysis import ReportAnalysis
    
    # Mocks
    mock_extract.return_value = "Glucose 120 mg/dL (70-99)"
    mock_generate.return_value = "Mocked LLM summary"
    mock_ner_pipeline = MagicMock()
    mock_ner_pipeline.return_value = [{"entity": "B-Test", "score": 0.99, "word": "Glucose"}]
    mock_ner.return_value = mock_ner_pipeline
    
    from datetime import date
    # Create a test report in DB manually
    # We need a user first
    from app.models.user import User
    user = User(email="test_analysis@example.com", hashed_password="pw", full_name="User")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    report = Report(
        user_id=user.id,
        title="Test Report",
        report_date=date(2024, 1, 1),
        file_name="test.pdf",
        file_path="dummy/test.pdf",
        file_type="pdf",
        report_type="blood"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    report_id = report.id
        
    # Run analysis
    await run_analysis(report_id, db)
    
    # Assert side effects
    from sqlalchemy.future import select
    stmt = select(Report).where(Report.id == report_id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    assert report.processing_status == ProcessingStatus.completed
    
    stmt = select(ReportAnalysis).where(ReportAnalysis.report_id == report_id)
    result = await db.execute(stmt)
    analysis = result.scalars().first()
    
    assert analysis is not None
    assert len(analysis.structured_lab_values) == 1
    assert analysis.structured_lab_values[0]["test_name"] == "glucose"
    assert analysis.structured_lab_values[0]["flag"] == "high"
    
    assert len(analysis.abnormal_findings) == 1
    assert analysis.clinician_summary == "Mocked LLM summary"
    assert analysis.patient_summary == "Mocked LLM summary"

@pytest.mark.asyncio
@patch("app.services.analysis_pipeline.extract_lab_values")
@patch("app.services.analysis_pipeline.get_ner_pipeline")
@patch("app.services.analysis_pipeline.generate")
@patch("app.services.analysis_pipeline.extract_text_from_file")
async def test_run_analysis_defensive_filtering(mock_extract, mock_generate, mock_ner, mock_extract_lab_values, db_session):
    db = db_session
    from app.services.analysis_pipeline import run_analysis
    from app.models.report import Report
    from app.models.report_analysis import ReportAnalysis
    
    mock_extract.return_value = "dummy text"
    mock_generate.return_value = "Mocked LLM summary"
    mock_ner_pipeline = MagicMock()
    mock_ner_pipeline.return_value = []
    mock_ner.return_value = mock_ner_pipeline
    
    # Return 1 valid lab, 1 missing test_name, 1 with string value instead of float
    mock_extract_lab_values.return_value = [
        {"test_name": "valid", "original_name": "Valid", "value": 10.5, "unit": "g", "original_unit": "g", "flag": "normal"},
        {"original_name": "Missing name", "value": 12.0, "unit": "g", "original_unit": "g", "flag": "normal"}, # invalid
        {"test_name": "invalid_value", "original_name": "Invalid Value", "value": "not_a_float", "unit": "g", "original_unit": "g", "flag": "normal"} # invalid
    ]
    
    from datetime import date
    from app.models.user import User
    
    user = User(email="test_filter@example.com", hashed_password="pw", full_name="User")
    db.add(user)
    await db.commit()
    await db.refresh(user)

    report = Report(
        user_id=user.id, title="Test Filter", report_date=date(2024, 1, 1),
        file_name="test.pdf", file_path="dummy.pdf", file_type="pdf", report_type="blood"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    report_id = report.id
        
    await run_analysis(report_id, db)
    
    from sqlalchemy.future import select
    stmt = select(ReportAnalysis).where(ReportAnalysis.report_id == report_id)
    result = await db.execute(stmt)
    analysis = result.scalars().first()
    
    # Ensure it didn't crash and only 1 valid lab was saved
    assert analysis is not None
    assert len(analysis.structured_lab_values) == 1
    assert analysis.structured_lab_values[0]["test_name"] == "valid"
    assert analysis.structured_lab_values[0]["flag"] == "normal"
    
    assert len(analysis.abnormal_findings) == 0
    assert analysis.clinician_summary == "Mocked LLM summary"
    assert analysis.patient_summary == "Mocked LLM summary"
