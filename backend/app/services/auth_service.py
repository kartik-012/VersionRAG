"""
Production authentication service with real OTP email verification.
Handles signup, login, OTP verification, resend, and password reset flows.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.schemas.auth import (
    UserCreate, UserLogin, TokenResponse, UserRead,
    PasswordResetConfirm, SignupResponse
)
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token,
    create_verification_token, create_password_reset_token,
    decode_token
)
from app.core.rate_limit import rate_limiter
from app.core.config import settings
from app.services.email_service import email_service


class AuthService:

    @staticmethod
    def register(db: Session, user_in: UserCreate) -> SignupResponse:
        """
        Register a new user with email verification requirement.
        Generates a 6-digit OTP, stores its hash, and sends it via Gmail SMTP.
        """
        existing = db.query(User).filter(User.email == user_in.email.lower()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to complete registration with the provided details."
            )

        # Generate OTP
        otp_code = email_service.generate_otp(settings.OTP_LENGTH)
        otp_hash = get_password_hash(otp_code)
        otp_expires = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        user = User(
            email=user_in.email.lower(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=True,
            is_verified=False,  # Must verify email before accessing platform
            is_superuser=False,
            verification_code=otp_hash,
            verification_code_expires_at=otp_expires,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Send real verification email via Gmail SMTP
        email_service.send_verification_otp(
            to_email=user.email,
            otp_code=otp_code,
            full_name=user.full_name,
        )

        return SignupResponse(
            message="Account created! Check your email for the 6-digit verification code.",
            requires_verification=True,
            email=user.email,
        )

    @staticmethod
    def authenticate(db: Session, credentials: UserLogin, client_ip: str = "unknown") -> TokenResponse:
        """
        Authenticate with rate limiting.
        Returns requires_verification hint if account is not yet verified.
        """
        rate_key = f"login:{credentials.email.lower()}"
        if rate_limiter.is_rate_limited(rate_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please wait 60 seconds before trying again."
            )

        user = db.query(User).filter(User.email == credentials.email.lower()).first()
        if not user or not verify_password(credentials.password, user.hashed_password):
            rate_limiter.record_attempt(rate_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated."
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="EMAIL_NOT_VERIFIED"
            )

        # Successful login — reset rate limiter
        rate_limiter.reset(rate_key)

        access_token = create_access_token(user.id, user.email)
        refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRead.model_validate(user)
        )

    @staticmethod
    def verify_otp(db: Session, email: str, code: str):
        """
        Verify a user's email using the 6-digit OTP code.
        Validates against the stored hashed OTP and checks expiry.
        """
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address."
            )

        if user.is_verified:
            return {"message": "Email is already verified. You can sign in."}

        if not user.verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No verification code was generated. Please request a new one."
            )

        # Check expiry
        if user.verification_code_expires_at:
            expires_at = user.verification_code_expires_at
            if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code has expired. Please request a new one."
                )

        # Verify OTP against hash
        if not verify_password(code, user.verification_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code. Please check and try again."
            )

        # Mark as verified and clear OTP
        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires_at = None
        db.commit()

        # Send welcome email
        email_service.send_welcome_email(user.email, user.full_name)

        return {"message": "Email successfully verified! You can now sign in."}

    @staticmethod
    def resend_verification(db: Session, email: str):
        """
        Regenerate OTP and resend the verification email.
        Rate-limited to prevent abuse.
        """
        rate_key = f"resend:{email.lower()}"
        if rate_limiter.is_rate_limited(rate_key):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another verification code."
            )

        user = db.query(User).filter(User.email == email.lower()).first()

        if not user:
            # Don't reveal whether email exists
            return {"message": "If that email is registered, a new verification code has been sent."}

        if user.is_verified:
            return {"message": "Email is already verified. You can sign in."}

        # Generate new OTP
        otp_code = email_service.generate_otp(settings.OTP_LENGTH)
        otp_hash = get_password_hash(otp_code)
        otp_expires = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        user.verification_code = otp_hash
        user.verification_code_expires_at = otp_expires
        db.commit()

        rate_limiter.record_attempt(rate_key)

        email_service.send_verification_otp(
            to_email=user.email,
            otp_code=otp_code,
            full_name=user.full_name,
        )

        return {"message": "A new verification code has been sent to your email."}

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> TokenResponse:
        """Issue a new access token using a valid refresh token."""
        payload = decode_token(refresh_token, expected_type="refresh")
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token."
            )
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or deactivated."
            )

        new_access = create_access_token(user.id, user.email)
        new_refresh = create_refresh_token(user.id)
        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRead.model_validate(user)
        )

    @staticmethod
    def request_password_reset(db: Session, email: str):
        """Send password reset token if account exists (non-revealing)."""
        user = db.query(User).filter(User.email == email.lower()).first()
        if user and user.is_active:
            token = create_password_reset_token(user.id)
            email_service.send_password_reset_email(user.email, token)
        return {"message": "If that email is registered, a password reset link has been sent."}

    @staticmethod
    def reset_password(db: Session, reset_data: PasswordResetConfirm):
        """Reset password using single-use reset JWT."""
        payload = decode_token(reset_data.token, expected_type="reset")
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token."
            )
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        user.hashed_password = get_password_hash(reset_data.new_password)
        db.commit()
        return {"message": "Password successfully reset. You may now log in."}

    @staticmethod
    def verify_email(db: Session, token: str):
        """Legacy JWT-based email verification (kept for backward compat)."""
        payload = decode_token(token, expected_type="verify")
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token."
            )
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires_at = None
        db.commit()
        return {"message": "Email successfully verified."}


auth_service = AuthService()
