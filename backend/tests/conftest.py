import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import sys
import os

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, get_db
from app.core.rate_limit import rate_limiter
from app.main import app

# Create in-memory SQLite database for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def clean_rate_limits():
    """Reset rate limiter state before and after every test."""
    rate_limiter.clear_all()
    yield
    rate_limiter.clear_all()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database schema for each test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def signup_and_login(client, user_data: dict) -> str:
    """
    Helper: Signup a user, auto-verify them in-DB, then login to get access token.
    This bypasses OTP email verification for test convenience.
    """
    from app.models.user import User as UserModel
    # Signup
    client.post("/api/v1/auth/signup", json=user_data)
    # Directly verify the user in the test database
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    user = db.query(UserModel).filter(UserModel.email == user_data["email"].lower()).first()
    if user:
        user.is_verified = True
        db.commit()
    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]}
    )
    return login_resp.json()["access_token"]
