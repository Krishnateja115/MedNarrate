import pytest

from app.services.lab_value_extractor import extract_lab_values


@pytest.mark.asyncio
async def test_clear_lab_lines_need_no_ai_provider(monkeypatch) -> None:
    async def unavailable_ai(prompt: str) -> str:
        raise AssertionError("Clear lab values should be parsed locally")

    monkeypatch.setattr(
        "app.services.llm_orchestrator.extract_structured_json", unavailable_ai
    )
    text = (
        "CLINICAL LABORATORY REPORT\n"
        "Hemoglobin: 14.2 g/dL (Ref: 13.5 - 17.5)\n"
        "White Blood Cells: 6.5 x10^3/uL (Ref: 4.5 - 11.0)\n"
        "Monocytes: 9 %\n"
    )

    values = await extract_lab_values(text)

    assert [item["test_name"] for item in values] == [
        "Hemoglobin", "WBC", "Monocytes"
    ]
    assert values[0]["flag"] == "normal"
    assert values[1]["value"] == 6.5
    assert values[2]["flag"] == "not_classified"


@pytest.mark.asyncio
async def test_admin_numbers_are_not_lab_results(monkeypatch) -> None:
    async def no_ai(prompt: str) -> str:
        return "[]"

    monkeypatch.setattr("app.services.llm_orchestrator.extract_structured_json", no_ai)
    values = await extract_lab_values(
        "Patient ID: 1234\nInvoice total: 500 mg/dL\nReport Date: 2026-10-11"
    )
    assert values == []
