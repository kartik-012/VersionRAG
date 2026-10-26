from fastapi.testclient import TestClient


def test_security_and_latency_headers_present(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200

    # 1. Latency profiling header
    assert "x-process-time-ms" in resp.headers
    latency = float(resp.headers["x-process-time-ms"])
    assert latency >= 0.0

    # 2. Hardened security headers
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("x-xss-protection") == "1; mode=block"
    assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
