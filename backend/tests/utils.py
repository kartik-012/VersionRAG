from app.models.user import User
from app.core.database import get_db
from app.main import app

def signup_and_login(client, user_data: dict) -> str:
    """
    Helper: Signup a user, auto-verify them in-DB, then login to get access token.
    This bypasses OTP email verification for test suite execution.
    """
    client.post("/api/v1/auth/signup", json=user_data)
    # Directly verify user in test database
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    user = db.query(User).filter(User.email == user_data["email"].lower()).first()
    if user:
        user.is_verified = True
        db.commit()
    
    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]}
    )
    return login_resp.json()["access_token"]
