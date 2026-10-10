from __future__ import annotations

from fastapi.testclient import TestClient


def test_device_registration_update_and_events(client: TestClient) -> None:
    created = client.post(
        "/api/v1/devices",
        json={
            "name": "lab-camera",
            "device_type": "camera",
            "ip_address": "192.168.1.20",
            "firmware_version": "sim-1.0.0",
            "metadata": {"location": "bench", "password": "drop-me"},
        },
    )
    assert created.status_code == 201
    device = created.json()
    assert device["metadata"] == {"location": "bench"}
    assert device["status"] == "registered"

    updated = client.patch(f"/api/v1/devices/{device['id']}", json={"disabled": True})
    assert updated.status_code == 200
    assert updated.json()["status"] == "disabled"

    events = client.get(f"/api/v1/devices/{device['id']}/events")
    assert events.status_code == 200


def test_dashboard_and_demo_reset_isolation(client: TestClient) -> None:
    scenario = client.post("/api/v1/demo/scenarios/sensitive_endpoint_access")
    assert scenario.status_code == 200
    assert scenario.json()[0]["duplicate"] is False

    summary = client.get("/api/v1/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["total_events"] == 1

    reset = client.post("/api/v1/demo/reset")
    assert reset.status_code == 200
    assert reset.json()["deleted_events"] == 1


def test_discovery_disabled_by_default(client: TestClient) -> None:
    response = client.post("/api/v1/discovery/jobs", json={"target_cidr": "192.168.1.0/30"})
    assert response.status_code == 403
    assert response.json()["error"] == "discovery_not_allowed"
