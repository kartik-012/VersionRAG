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


def test_health_ping_liveness_probe(client: TestClient):
    resp = client.get("/api/v1/health/ping")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"status": "ok", "ping": "pong"}
    assert "x-process-time-ms" in resp.headers


def test_health_version_metadata(client: TestClient):
    resp = client.get("/api/v1/health/version")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "1.4.0"
    assert data["service"] == "VersionRAG"
    assert "environment" in data
    assert "database_engine" in data
    assert "x-process-time-ms" in resp.headers
