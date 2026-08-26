from fastapi.testclient import TestClient
from tests.utils import signup_and_login

def test_tenant_isolation_between_workspaces(client: TestClient):
    # User A
    user_a = {"email": "user_a@company.com", "full_name": "User A", "password": "Password123!"}
    token_a = signup_and_login(client, user_a)
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    user_b = {"email": "user_b@company.com", "full_name": "User B", "password": "Password123!"}
    token_b = signup_and_login(client, user_b)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates Workspace A
    ws_a = client.post("/api/v1/workspaces", json={"name": "Workspace A"}, headers=headers_a).json()
    ws_a_id = ws_a["id"]

    # User A creates Project A inside Workspace A
    proj_a = client.post(f"/api/v1/projects/workspace/{ws_a_id}", json={"name": "Project A"}, headers=headers_a).json()
    proj_a_id = proj_a["id"]

    # User B tries to access Workspace A -> Security Rule: Returns 404 (does NOT leak workspace existence)
    resp_cross_ws = client.get(f"/api/v1/workspaces/{ws_a_id}", headers=headers_b)
    assert resp_cross_ws.status_code == 404

    # User B tries to access Project A -> Returns 404
    resp_cross_proj = client.get(f"/api/v1/projects/{proj_a_id}", headers=headers_b)
    assert resp_cross_proj.status_code == 404
