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


def test_background_job_5_stage_telemetry_and_index_warmup(client: TestClient):
    """
    Verifies Solution 5:
    - Thread-safe background ingestion worker executes all 5 telemetry stages
      (0.20 -> 0.45 -> 0.70 -> 0.90 -> 1.00).
    - Records stage_history, char_count, chunks_created, hybrid_partition_warmed,
      and AST diff counts in job.execution_meta.
    - Exposes real-time job status via GET /api/v1/jobs/{job_id} and GET /api/v1/jobs/project/{project_id}.
    """
    user = {"email": "telemetry_tester@corp.com", "full_name": "Telemetry Tester", "password": "Password123!"}
    token = signup_and_login(client, user)
    headers = {"Authorization": f"Bearer {token}"}

    ws = client.post("/api/v1/workspaces", json={"name": "Telemetry Workspace"}, headers=headers).json()
    proj = client.post(f"/api/v1/projects/workspace/{ws['id']}", json={"name": "Worker Pipeline"}, headers=headers).json()

    # Upload v1.0.0
    v1_md = (
        b"# Auth Token Service v1.0.0\n\n"
        b"### verifyToken(token, secret)\n"
        b"Verifies JWT signature using `==` comparison.\n"
    )
    resp1 = client.post(
        f"/api/v1/documents/upload/{proj['id']}",
        files={"file": ("auth_v1.md", io.BytesIO(v1_md), "text/markdown")},
        data={"version_tag": "v1.0.0"},
        headers=headers,
    )
    assert resp1.status_code == 201
    doc_id = resp1.json()["document_id"]
    job1_id = resp1.json()["job_id"]

    # Upload v2.0.0 with breaking AST arity & operator shift
    v2_md = (
        b"# Auth Token Service v2.0.0\n\n"
        b"### verifyToken(token, secret, issuer)\n"
        b"Verifies JWT signature using strict `===` comparison and required `issuer` parameter.\n"
    )
    resp2 = client.post(
        f"/api/v1/documents/upload/{proj['id']}",
        files={"file": ("auth_v2.md", io.BytesIO(v2_md), "text/markdown")},
        data={"version_tag": "v2.0.0", "document_id": doc_id},
        headers=headers,
    )
    assert resp2.status_code == 201
    job2_id = resp2.json()["job_id"]

    # Query job2 status
    job2_resp = client.get(f"/api/v1/jobs/{job2_id}", headers=headers)
    assert job2_resp.status_code == 200
    job2 = job2_resp.json()

    assert job2["status"] == "completed"
    assert job2["current_stage"] == "ready"
    assert job2["stage_progress"] == 1.0

    meta = job2["execution_meta"]
    expected_milestones = [
        "0.00:queued",
        "0.20:parsing",
        "0.45:chunking",
        "0.70:generating_embeddings",
        "0.90:detecting_changes",
        "1.00:ready",
    ]
    assert meta["stage_history"] == expected_milestones
    assert meta["char_count"] > 50
    assert meta["chunks_created"] >= 1
    assert meta["hybrid_partition_warmed"] == f"{proj['id']}:v2.0.0"
    assert meta["compared_against_version"] == "v1.0.0"
    assert meta["changes_detected"] >= 1

    # Verify project job listing endpoint
    proj_jobs_resp = client.get(f"/api/v1/jobs/project/{proj['id']}", headers=headers)
    assert proj_jobs_resp.status_code == 200
    proj_jobs = proj_jobs_resp.json()
    job_ids = [j["id"] for j in proj_jobs]
    assert job1_id in job_ids
    assert job2_id in job_ids

