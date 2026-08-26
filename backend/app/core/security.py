import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from app.core.config import settings

def get_password_hash(password: str) -> str:
    """Hash a password securely using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """Create a signed JWT with strict type tags and expiration."""
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": expire,
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_access_token(subject: str, email: str) -> str:
    """Generate a standard user access token."""
    return create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        additional_claims={"email": email}
    )

def create_refresh_token(subject: str) -> str:
    """Generate a refresh token."""
    return create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

def create_verification_token(subject: str) -> str:
    """Generate a single-use email verification token."""
    return create_token(
        subject=subject,
        token_type="verify",
        expires_delta=timedelta(hours=settings.VERIFY_TOKEN_EXPIRE_HOURS)
    )

def create_password_reset_token(subject: str) -> str:
    """Generate a password reset token."""
    return create_token(
        subject=subject,
        token_type="reset",
        expires_delta=timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)
    )

def decode_token(token: str, expected_type: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT ensuring the expected token type matches."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except jwt.PyJWTError:
        return None
