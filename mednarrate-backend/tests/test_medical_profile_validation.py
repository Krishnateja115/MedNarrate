import pytest
from pydantic import ValidationError
from app.schemas.user import MedicalProfileBase

def test_case_a_valid_full():
    prof = MedicalProfileBase(blood_group="O+", known_allergies="Penicillin", chronic_conditions="Asthma")
    assert prof.blood_group == "O+"
    assert prof.known_allergies == "Penicillin"
    assert prof.chronic_conditions == "Asthma"

def test_case_b_valid_none():
    prof = MedicalProfileBase(blood_group="a+", known_allergies="None", chronic_conditions="None")
    assert prof.blood_group == "A+"
    assert prof.known_allergies == "None"
    assert prof.chronic_conditions == "None"

def test_case_c_valid_multiple():
    prof = MedicalProfileBase(blood_group="AB-", known_allergies="Dust, Pollen", chronic_conditions="Type 2 diabetes")
    assert prof.blood_group == "AB-"

def test_case_d_empty_blood_group():
    prof = MedicalProfileBase(blood_group="", known_allergies="Penicillin", chronic_conditions="Asthma")
    assert prof.blood_group is None

def test_case_e_empty_allergies_and_conditions():
    prof = MedicalProfileBase(blood_group="O+", known_allergies="", chronic_conditions=None)
    assert prof.blood_group == "O+"
    assert prof.known_allergies is None
    assert prof.chronic_conditions is None

def test_case_f_all_empty():
    prof = MedicalProfileBase(blood_group="", known_allergies="", chronic_conditions="")
    assert prof.blood_group is None
    assert prof.known_allergies is None
    assert prof.chronic_conditions is None

# INVALID CASES
def test_case_g_invalid_blood_group_xyz():
    with pytest.raises(ValidationError):
        MedicalProfileBase(blood_group="XYZ")

def test_case_h_invalid_blood_group_digits():
    with pytest.raises(ValidationError):
        MedicalProfileBase(blood_group="12345")

def test_case_i_invalid_blood_group_specials():
    with pytest.raises(ValidationError):
        MedicalProfileBase(blood_group="@#$%")

def test_case_j_invalid_blood_group_abc_plus():
    with pytest.raises(ValidationError):
        MedicalProfileBase(blood_group="ABC+")

def test_case_k_invalid_blood_group_o_plus_plus():
    with pytest.raises(ValidationError):
        MedicalProfileBase(blood_group="O++")

def test_case_l_invalid_allergy_special_chars_only():
    with pytest.raises(ValidationError):
        MedicalProfileBase(known_allergies="@#$%")
    with pytest.raises(ValidationError):
        MedicalProfileBase(chronic_conditions="!!!")
