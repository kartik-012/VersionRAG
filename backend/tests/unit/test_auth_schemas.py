import pytest
from pydantic import ValidationError
from app.schemas.auth import UserCreate

def test_user_create_validation_success():
    data = {
        "email": "engineer@company.com",
        "full_name": "Senior Engineer",
        "password": "ValidPassword123"
    }
    user = UserCreate(**data)
    assert user.email == "engineer@company.com"

def test_user_create_password_too_short():
    with pytest.raises(ValidationError):
        UserCreate(
            email="engineer@company.com",
            full_name="Senior Engineer",
            password="Short1"  # < 10 chars
        )

def test_user_create_password_missing_uppercase():
    with pytest.raises(ValidationError):
        UserCreate(
            email="engineer@company.com",
            full_name="Senior Engineer",
            password="nouppercase12345"
        )

def test_user_create_password_missing_digit():
    with pytest.raises(ValidationError):
        UserCreate(
            email="engineer@company.com",
            full_name="Senior Engineer",
            password="NoDigitPasswordHere"
        )
