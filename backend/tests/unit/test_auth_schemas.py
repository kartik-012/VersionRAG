import pytest
from pydantic import ValidationError
from app.schemas.auth import UserCreate
from app.schemas.document import sanitize_version_tag, DocumentVersionBase

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


def test_document_version_tag_sanitization():
    """Validates sanitize_version_tag prefixing, trimming, and default fallbacks."""
    assert sanitize_version_tag("15.14.0") == "v15.14.0"
    assert sanitize_version_tag("v16.0.0") == "v16.0.0"
    assert sanitize_version_tag("   2.4.1   ") == "v2.4.1"
    assert sanitize_version_tag("") == "v1.0.0"


def test_document_version_base_validation():
    """Validates DocumentVersionBase automatic version_tag sanitation."""
    ver = DocumentVersionBase(version_tag="18.2.0")
    assert ver.version_tag == "v18.2.0"

    ver2 = DocumentVersionBase(version_tag="  v20.0.1  ")
    assert ver2.version_tag == "v20.0.1"

