from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import (
    UserCreate, UserLogin, TokenResponse, TokenRefreshRequest,
    PasswordResetRequest, PasswordResetConfirm, EmailVerifyRequest,
    ResendVerificationRequest, UserRead, SignupResponse
)
from app.services.auth_service import auth_service
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user. Sends a 6-digit OTP verification code to their email."""
    return auth_service.register(db, user_in)


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and receive access + refresh tokens. Requires verified email."""
    return auth_service.authenticate(db, credentials)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Refresh an access token using a refresh token."""
    return auth_service.refresh_access_token(db, req.refresh_token)


@router.post("/verify-email")
def verify_email(req: EmailVerifyRequest, db: Session = Depends(get_db)):
    """Verify email address with 6-digit OTP code."""
    return auth_service.verify_otp(db, req.email, req.code)


@router.post("/resend-verification")
def resend_verification(req: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend a new verification OTP code to the user's email."""
    return auth_service.resend_verification(db, req.email)


@router.post("/forgot-password")
def forgot_password(req: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a password reset email."""
    return auth_service.request_password_reset(db, req.email)


@router.post("/reset-password")
def reset_password(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset using token."""
    return auth_service.reset_password(db, req)


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout current user."""
    return {"message": "Logged out successfully"}
