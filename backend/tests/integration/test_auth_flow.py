from fastapi.testclient import TestClient
from tests.utils import signup_and_login

def test_full_auth_lifecycle(client: TestClient):
    # 1. Signup (now returns SignupResponse, not User)
    signup_payload = {
        "email": "developer@enterprise.io",
        "full_name": "Senior Architect",
        "password": "Password12345!"
    }
    resp = client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "developer@enterprise.io"
    assert data["requires_verification"] == True

    # 2. Duplicate signup rejection (without leaking user existence)
    resp_dup = client.post("/api/v1/auth/signup", json=signup_payload)
    assert resp_dup.status_code == 400

    # 3. Login before verification should return 403
    login_payload = {
        "email": "developer@enterprise.io",
        "password": "Password12345!"
    }
    resp_unverified = client.post("/api/v1/auth/login", json=login_payload)
    assert resp_unverified.status_code == 403

    # 4. Verify the user manually and login
    from app.models.user import User
    from app.core.database import get_db
    from app.main import app
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    user = db.query(User).filter(User.email == "developer@enterprise.io").first()
    user.is_verified = True
    db.commit()

    resp_login = client.post("/api/v1/auth/login", json=login_payload)
    assert resp_login.status_code == 200
    tokens = resp_login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 5. Protected Route (/auth/me)
    headers = {"Authorization": f"Bearer {access_token}"}
    resp_me = client.get("/api/v1/auth/me", headers=headers)
    assert resp_me.status_code == 200
    assert resp_me.json()["email"] == "developer@enterprise.io"

    # 6. Token Refresh
    resp_ref = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp_ref.status_code == 200
    assert "access_token" in resp_ref.json()

    # 7. Unauthenticated protected request rejection
    resp_unauth = client.get("/api/v1/auth/me")
    assert resp_unauth.status_code == 401
