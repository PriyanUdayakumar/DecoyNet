from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_and_readiness(client: TestClient) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    readiness = client.get("/api/v1/health/ready")
    assert readiness.status_code == 200
    assert readiness.json()["database"] == "ok"
