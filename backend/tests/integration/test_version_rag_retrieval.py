import io
import json
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


def test_sse_streaming_query_stages_and_tokens(client: TestClient):
    """
    Verifies Solution 6:
    - POST /api/v1/query/stream returns text/event-stream.
    - Emits 4 ordered reasoning stage events (stage 1 -> 2 -> 3 -> 4).
    - Emits token delta events whose concatenation matches the final grounded answer.
    - Emits final 'done' event with persisted QueryResponse and version-pure citations.
    """
    user = {"email": "sse_tester@corp.com", "full_name": "SSE Tester", "password": "Password123!"}
    token = signup_and_login(client, user)
    headers = {"Authorization": f"Bearer {token}"}

    ws = client.post("/api/v1/workspaces", json={"name": "SSE WS"}, headers=headers).json()
    proj = client.post(f"/api/v1/projects/workspace/{ws['id']}", json={"name": "SSE Project"}, headers=headers).json()

    v15_content = (
        b"# Crypto Engine v15.0.0\n\n"
        b"### verifySignature(payload, publicKey, strictPadding)\n"
        b"Verifies RSA-PSS signatures with mandatory strictPadding in v15.0.0.\n"
    )
    client.post(
        f"/api/v1/documents/upload/{proj['id']}",
        files={"file": ("crypto_v15.md", io.BytesIO(v15_content), "text/markdown")},
        data={"version_tag": "v15.0.0"},
        headers=headers,
    )

    stream_payload = {
        "project_id": proj["id"],
        "question": "How does verifySignature handle strictPadding in v15.0.0?",
        "target_version": "v15.0.0",
        "scope": "specific",
    }

    with client.stream("POST", "/api/v1/query/stream", json=stream_payload, headers=headers) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        raw_body = "".join(resp.iter_text())

    events = []
    for block in raw_body.split("\n\n"):
        line = block.strip()
        if line.startswith("data:"):
            events.append(json.loads(line.replace("data:", "", 1).strip()))

    stage_events = [e for e in events if e.get("type") == "stage"]
    token_events = [e for e in events if e.get("type") == "token"]
    done_events = [e for e in events if e.get("type") == "done"]

    assert [s["stage"] for s in stage_events] == [1, 2, 3, 4]
    assert len(token_events) >= 3
    assert len(done_events) == 1

    reconstructed_answer = "".join(t["delta"] for t in token_events)
    final_response = done_events[0]["response"]
    assert reconstructed_answer == final_response["answer"]
    assert "strictPadding" in final_response["answer"]
    assert len(final_response["citations"]) >= 1
    assert final_response["citations"][0]["version_tag"] == "v15.0.0"

