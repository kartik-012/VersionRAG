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
    client.post(f"/api/v1/documents/upload/{proj['id']}", files={"file": ("doc_v15.md", io.BytesIO(v15_content), "text/markdown")}, data={"version_tag": "v15.14.0"}, headers=headers)

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
    assert eval_data["retrieval_precision"] > 0.0
    assert eval_data["versionrag_faithfulness"] > 0.0
    assert len(eval_data["results"]) >= 5


def test_dynamic_custom_document_auto_benchmark(client: TestClient):
    """
    Verifies Solution 4: When a user uploads a completely custom multi-version document
    (unrelated to Node.js assert), EvaluationService automatically synthesizes adversarial
    test questions directly from the uploaded AST diffs and chunks.
    """
    user = {"email": "custom_eval@corp.com", "full_name": "Custom Eval", "password": "Password123!"}
    token = signup_and_login(client, user)
    headers = {"Authorization": f"Bearer {token}"}

    ws = client.post("/api/v1/workspaces", json={"name": "Custom Eval WS"}, headers=headers).json()
    proj = client.post(f"/api/v1/projects/workspace/{ws['id']}", json={"name": "PaymentGateway SDK"}, headers=headers).json()

    v1_doc = (
        b"# PaymentGateway SDK\n"
        b"### chargeCustomer(amount, currency[, idempotencyKey])\n"
        b"Processes a credit card transaction using legacy gateway protocol v1.\n"
    )
    v2_doc = (
        b"# PaymentGateway SDK\n"
        b"### chargeCustomer(amount, currency, idempotencyKey)\n"
        b"Processes a transaction. idempotencyKey is now strictly required and throws TypeError if omitted.\n"
    )

    client.post(
        f"/api/v1/documents/upload/{proj['id']}",
        files={"file": ("payment_sdk.md", io.BytesIO(v1_doc), "text/markdown")},
        data={"title": "PaymentGateway SDK", "version_tag": "v1.0.0"},
        headers=headers,
    )
    client.post(
        f"/api/v1/documents/upload/{proj['id']}",
        files={"file": ("payment_sdk.md", io.BytesIO(v2_doc), "text/markdown")},
        data={"title": "PaymentGateway SDK", "version_tag": "v2.0.0"},
        headers=headers,
    )

    # Verify auto-scenarios preview endpoint generates adversarial scenarios up to 10
    preview_resp = client.get(f"/api/v1/evaluations/auto-scenarios/{proj['id']}", headers=headers)
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["total_generated"] >= 4
    assert any("chargeCustomer" in s["question"] for s in preview_data["scenarios"])

    resp = client.post(
        "/api/v1/evaluations/run",
        json={"project_id": proj["id"], "run_name": "Custom SDK Auto-Benchmark"},
        headers=headers,
    )
    assert resp.status_code == 201
    eval_data = resp.json()
    assert eval_data["status"] == "completed"
    results = eval_data["results"]
    assert len(results) >= 4
    # Verify that questions were dynamically generated about `chargeCustomer` from the uploaded doc
    questions_text = " ".join(r["question"] for r in results)
    assert "chargeCustomer" in questions_text
    assert eval_data["versionrag_accuracy"] >= 0.75


def test_live_llm_provider_and_api_key_switcher(client: TestClient):
    """
    Verifies Part 2 — Item 5:
    - GET /api/v1/health/llm-config returns supported providers (Local, Gemini, OpenAI, Anthropic, Groq).
    - POST /api/v1/health/llm-config dynamically switches active provider, model, and masked API key at runtime.
    """
    init_resp = client.get("/api/v1/health/llm-config")
    assert init_resp.status_code == 200
    init_cfg = init_resp.json()
    provider_ids = [p["id"] for p in init_cfg["supported_providers"]]
    assert "local_deterministic" in provider_ids
    assert "gemini" in provider_ids
    assert "openai" in provider_ids
    assert "anthropic" in provider_ids
    assert "groq" in provider_ids

    # Hot-swap to Gemini with a test API key
    swap_resp = client.post(
        "/api/v1/health/llm-config",
        json={
            "provider": "gemini",
            "model_name": "gemini-1.5-pro",
            "api_key": "AIzaSyTestLiveHotSwapKey9988",
        },
    )
    assert swap_resp.status_code == 200
    swap_cfg = swap_resp.json()
    assert swap_cfg["active_provider"] == "gemini"
    assert swap_cfg["active_model"] == "gemini-1.5-pro"
    assert swap_cfg["has_api_key"] is True
    assert swap_cfg["masked_api_key"] == "AIza...9988"

    # Switch back to local_deterministic so subsequent tests run offline deterministically
    reset_resp = client.post(
        "/api/v1/health/llm-config",
        json={"provider": "local_deterministic"},
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["active_provider"] == "local_deterministic"

