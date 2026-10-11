import pytest

from app.services.lab_value_extractor import extract_lab_values
@pytest.mark.parametrize(
    ("report_text", "expected"),
    [
        (
            "LAB REPORT\nHemoglobin 14.2 g/dL (12-16)\n"
            "WBC 5.5 10^3/uL (4-11)\nPlatelets 300 10^3/uL (150-450)",
            {"Hemoglobin": 14.2, "WBC": 5.5, "Platelets": 300.0},
        ),
        (
            "PATHOLOGY RESULTS\nGlucose (Fasting) 105 mg/dL (70-99)\n"
            "TSH 4.5 µIU/mL (0.4-4.0)",
            {"Fasting Glucose": 105.0, "TSH": 4.5},
        ),
        (
            "LAB REPORT\nRBC 4.8 mil/mm3 (4.0-5.5)\n"
            "Cholesterol 210 mg/dL (120-200)",
            {"RBC": 4.8, "Cholesterol": 210.0},
        ),
        (
            "LAB REPORT\nCreatinine 0.9 mg/dL (0.6-1.2)\n"
            "Uric Acid 5.2 mg/dL (3.5-7.2)",
            {"Creatinine": 0.9, "Uric Acid": 5.2},
        ),
    ],
)
async def test_structured_lab_extraction_across_report_formats(report_text, expected):
    """Check real local parsing without fabricated missing files or mocked results."""
    structured_labs = await extract_lab_values(report_text)
    extracted = {lab["test_name"]: lab["value"] for lab in structured_labs}
    assert extracted == expected


@pytest.mark.asyncio
async def test_one_sided_reference_ranges():
    ldl_text = "LDL Cholesterol 165 mg/dL < 100 mg/dL HIGH"
    labs = await extract_lab_values(ldl_text)
    assert len(labs) == 1
    ldl = labs[0]
    assert ldl["value"] == 165.0
    assert ldl["unit"] == "mg/dL"
    assert ldl["ref_high"] == 100.0
    assert ldl.get("ref_low") is None
    assert ldl["flag"] == "high"

    vit_text = "Vitamin D 15 ng/mL < 30 ng/mL LOW"
    labs = await extract_lab_values(vit_text)
    assert len(labs) == 1
    vit = labs[0]
    assert vit["value"] == 15.0
    assert vit["unit"] == "ng/mL"
    assert vit["ref_high"] == 30.0
    assert vit.get("ref_low") is None
    assert vit["flag"] == "low"

    hdl_text = "HDL Cholesterol 65 mg/dL > 40 mg/dL NORMAL"
    labs = await extract_lab_values(hdl_text)
    assert len(labs) == 1
    hdl = labs[0]
    assert hdl["value"] == 65.0
    assert hdl["unit"] == "mg/dL"
    assert hdl["ref_low"] == 40.0
    assert hdl.get("ref_high") is None
    assert hdl["flag"] == "normal"

    ldl_lte = "LDL Cholesterol 165 mg/dL <= 100 mg/dL HIGH"
    labs = await extract_lab_values(ldl_lte)
    assert len(labs) == 1
    assert labs[0]["ref_high"] == 100.0
    assert labs[0]["flag"] == "high"

    hdl_gte = "HDL Cholesterol 65 mg/dL >= 40 mg/dL NORMAL"
    labs = await extract_lab_values(hdl_gte)
    assert len(labs) == 1
    assert labs[0]["ref_low"] == 40.0
    assert labs[0]["flag"] == "normal"

    # Classification must also work when the source has no explicit flag.
    no_flag_high = await extract_lab_values("LDL Cholesterol 165 mg/dL <= 100 mg/dL")
    assert no_flag_high[0]["ref_high"] == 100.0
    assert no_flag_high[0]["flag"] == "high"

    no_flag_normal = await extract_lab_values("HDL Cholesterol 65 mg/dL >= 40 mg/dL")
    assert no_flag_normal[0]["ref_low"] == 40.0
    assert no_flag_normal[0]["flag"] == "normal"
