import io
from fastapi.testclient import TestClient
from tests.utils import signup_and_login

def test_version_aware_query_and_citations(client: TestClient):
    # Setup user, workspace, project
    user = {"email": "rag_tester@corp.com", "full_name": "RAG Tester", "password": "Password123!"}
    token = signup_and_login(client, user)
    headers = {"Authorization": f"Bearer {token}"}

    ws = client.post("/api/v1/workspaces", json={"name": "RAG WS"}, headers=headers).json()
    proj = client.post(f"/api/v1/projects/workspace/{ws['id']}", json={"name": "RAG Project"}, headers=headers).json()

    # Upload v14
    v14_content = b"# Module Docs v14\n\n## Functions\n### assert.deepEqual()\nCompares primitives loosely using abstract equality.\n"
    client.post(f"/api/v1/documents/upload/{proj['id']}", files={"file": ("doc_v14.md", io.BytesIO(v14_content), "text/markdown")}, data={"version_tag": "v14.0.0"}, headers=headers)

    # Upload v15
    v15_content = b"# Module Docs v15\n\n## Functions\n### assert.deepEqual()\nCompares prototypes strictly. Throws AssertionError on mismatch.\n"
    client.post(f"/api/v1/documents/upload/{proj['id']}", files={"file": ("doc_v15.md", io.BytesIO(v15_content), "text/markdown")}, data={"version_tag": "v15.0.0"}, headers=headers)

    # Query targeting v15 specifically
    query_payload = {
        "project_id": proj["id"],
        "question": "How does assert.deepEqual() compare objects in v15?",
        "target_version": "v15",
        "scope": "specific"
    }
    resp = client.post("/api/v1/query", json=query_payload, headers=headers)
    assert resp.status_code == 200
    q_data = resp.json()
    assert "strictly" in q_data["answer"] or "prototype" in q_data["answer"].lower()
    assert q_data["target_version"] == "v15"
    assert len(q_data["citations"]) >= 1
    assert "v15" in q_data["citations"][0]["version_tag"]
