import pytest
from pydantic import ValidationError
from app.schemas.user import MedicalProfileBase

# VALID TEST CASES
def test_valid_case_1():
    prof = MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="9876543210")
    assert prof.emergency_contact_name == "Mamatha"
    assert prof.emergency_contact_phone == "9876543210"

def test_valid_case_2():
    prof = MedicalProfileBase(emergency_contact_name="Priya Sharma", emergency_contact_phone="9123456789")
    assert prof.emergency_contact_name == "Priya Sharma"

def test_valid_case_3():
    prof = MedicalProfileBase(emergency_contact_name="Ananya Reddy", emergency_contact_phone="8765432109")
    assert prof.emergency_contact_phone == "8765432109"

def test_valid_case_4():
    prof = MedicalProfileBase(emergency_contact_name="Rahul Kumar", emergency_contact_phone="7654321098")
    assert prof.emergency_contact_name == "Rahul Kumar"

# INVALID TEST CASES
def test_invalid_1_eleven_digits():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="88888888888")

def test_invalid_2_starts_with_1():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="1234567890")

def test_invalid_3_starts_with_5():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="5123456789")

def test_invalid_4_nine_digits():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="987654321")

def test_invalid_5_eleven_digits():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="98765432101")

def test_invalid_6_special_char():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="98765@3210")

def test_invalid_7_letters():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="abcdefghij")

def test_invalid_8_plus_91():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="+919876543210")

def test_invalid_9_starts_with_zero():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="0987654321")

def test_invalid_10_empty_name():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="", emergency_contact_phone="9876543210")

def test_invalid_11_empty_phone():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="Mamatha", emergency_contact_phone="")

def test_invalid_12_numeric_name():
    with pytest.raises(ValidationError):
        MedicalProfileBase(emergency_contact_name="12345", emergency_contact_phone="9876543210")
