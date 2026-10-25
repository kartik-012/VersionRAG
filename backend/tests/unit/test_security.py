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


def test_rate_limiter_redis_fallback_and_sliding_window():
    from app.core.rate_limit import RateLimiter

    # Even if an unreachable Redis URL is supplied, RateLimiter falls back to in-memory with zero downtime
    limiter = RateLimiter(redis_url="redis://127.0.0.1:6399/0")
    assert limiter.active_backend == "in_memory_sliding_window"

    key = "login:test@example.com"
    limiter.reset(key)
    assert limiter.is_rate_limited(key, max_attempts=3, window_seconds=60) is False

    limiter.record_attempt(key)
    limiter.record_attempt(key)
    assert limiter.is_rate_limited(key, max_attempts=3, window_seconds=60) is False

    limiter.record_attempt(key)
    assert limiter.is_rate_limited(key, max_attempts=3, window_seconds=60) is True

    limiter.reset(key)
    assert limiter.is_rate_limited(key, max_attempts=3, window_seconds=60) is False


def test_access_token_payload_claims():
    user_id = "user_demo_789"
    email = "demo@versionrag.dev"
    token = create_access_token(subject=user_id, email=email)
    payload = decode_token(token, expected_type="access")

    assert payload is not None
    assert payload.get("sub") == user_id
    assert payload.get("email") == email
    assert payload.get("type") == "access"
    assert "exp" in payload
    assert "iat" in payload

