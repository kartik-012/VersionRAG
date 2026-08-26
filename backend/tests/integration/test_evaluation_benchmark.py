import io
from fastapi.testclient import TestClient
from tests.utils import signup_and_login

def test_evaluation_benchmark_execution(client: TestClient):
    # Setup user, workspace, project
    user = {"email": "eval_tester@corp.com", "full_name": "Eval Tester", "password": "Password123!"}
    token = signup_and_login(client, user)
    headers = {"Authorization": f"Bearer {token}"}

    ws = client.post("/api/v1/workspaces", json={"name": "Eval WS"}, headers=headers).json()
    proj = client.post(f"/api/v1/projects/workspace/{ws['id']}", json={"name": "Eval Project"}, headers=headers).json()

    # Upload document versions
    v14_content = b"# Module Docs v14\n## Functions\n### assert.deepEqual()\nCompares primitives loosely.\n"
    v15_content = b"# Module Docs v15\n## Functions\n### assert.deepEqual()\nCompares prototypes strictly.\n### assert.partialDeepStrictEqual()\nRelease candidate.\n"
    client.post(f"/api/v1/documents/upload/{proj['id']}", files={"file": ("doc_v14.md", io.BytesIO(v14_content), "text/markdown")}, data={"version_tag": "v14.0.0"}, headers=headers)
    client.post(f"/api/v1/documents/upload/{proj['id']}", files={"file": ("doc_v15.md", io.BytesIO(v15_content), "text/markdown")}, data={"version_tag": "v15.0.0"}, headers=headers)

    # Run Benchmark
    req = {
        "project_id": proj["id"],
        "dataset_name": "Standard-VersionRAG-Eval-v1",
        "run_name": "Integration Test Benchmark"
    }
    resp = client.post("/api/v1/evaluations/run", json=req, headers=headers)
    assert resp.status_code == 201
    eval_data = resp.json()
    assert eval_data["status"] == "completed"
    assert eval_data["versionrag_accuracy"] >= 0.70
    assert len(eval_data["results"]) >= 5
