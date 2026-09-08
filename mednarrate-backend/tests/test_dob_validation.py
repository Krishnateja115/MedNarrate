import pytest
from pydantic import ValidationError
from app.schemas.user import UserUpdate, validate_dob_string

def test_dob_invalid_month():
    with pytest.raises(ValidationError):
        UserUpdate(date_of_birth="2006-13-13")

def test_dob_non_leap_year_february():
    with pytest.raises(ValidationError):
        UserUpdate(date_of_birth="2023-02-29")

def test_dob_leap_year_february():
    user_up = UserUpdate(date_of_birth="2024-02-29")
    assert user_up.date_of_birth == "2024-02-29"

def test_dob_future_date():
    with pytest.raises(ValidationError):
        UserUpdate(date_of_birth="2099-01-01")

def test_dob_valid_past_date():
    user_up = UserUpdate(date_of_birth="2006-05-20")
    assert user_up.date_of_birth == "2006-05-20"
