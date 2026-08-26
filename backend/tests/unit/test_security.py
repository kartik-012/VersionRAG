from datetime import timedelta
from app.core.security import (
    get_password_hash, verify_password,
    create_token, decode_token,
    create_access_token, create_refresh_token
)

def test_password_hashing_and_verification():
    raw = "MySuperSecretPassword123!"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False

def test_token_type_safety():
    access_tok = create_access_token("user_123", "user@example.com")
    refresh_tok = create_refresh_token("user_123")

    # Access token cannot be decoded as refresh
    assert decode_token(access_tok, expected_type="access") is not None
    assert decode_token(access_tok, expected_type="refresh") is None

    # Refresh token cannot be decoded as access
    assert decode_token(refresh_tok, expected_type="refresh") is not None
    assert decode_token(refresh_tok, expected_type="access") is None

def test_expired_token():
    expired_tok = create_token(
        subject="user_123",
        token_type="access",
        expires_delta=timedelta(seconds=-10)
    )
    assert decode_token(expired_tok, expected_type="access") is None
