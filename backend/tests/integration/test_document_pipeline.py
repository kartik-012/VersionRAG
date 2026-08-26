import io
from fastapi.testclient import TestClient
from tests.utils import signup_and_login

def test_document_upload_and_ingestion(client: TestClient):
    # Setup user, workspace, project
    user = {"email": "doc_tester@corp.com", "full_name": "Doc Tester", "password": "Password123!"}
    token = signup_and_login(client, user)
    headers = {"Authorization": f"Bearer {token}"}

    ws = client.post("/api/v1/workspaces", json={"name": "Engineering Docs"}, headers=headers).json()
    proj = client.post(f"/api/v1/projects/workspace/{ws['id']}", json={"name": "API Service"}, headers=headers).json()

    # Upload document
    doc_content = b"# Payment API Specification v15\n\n## Overview\nThis is version 15 of Payment API.\n\n## Endpoints\n### POST /charge\nCharges a credit card.\n"
    files = {"file": ("payment_api_v15.md", io.BytesIO(doc_content), "text/markdown")}
    data = {"version_tag": "v15.0.0"}

    resp = client.post(f"/api/v1/documents/upload/{proj['id']}", files=files, data=data, headers=headers)
    assert resp.status_code == 201
    upload_res = resp.json()
    assert "document_id" in upload_res
    assert "job_id" in upload_res

    # Check document listing
    doc_list = client.get(f"/api/v1/documents/project/{proj['id']}", headers=headers).json()
    assert len(doc_list) >= 1
    assert doc_list[0]["id"] == upload_res["document_id"]
