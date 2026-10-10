from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_valid_device(client: TestClient) -> None:
    response = client.post(
        "/api/v1/devices",
        json={"name": "cam-1", "device_type": "camera", "ip_address": "192.168.1.20"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "cam-1"
    assert body["status"] == "registered"


def test_duplicate_name_conflict(client: TestClient) -> None:
    first = client.post("/api/v1/devices", json={"name": "cam-1", "device_type": "camera"})
    assert first.status_code == 201
    second = client.post(
        "/api/v1/devices",
        json={"name": "cam-1", "device_type": "thermostat", "ip_address": "10.0.0.5"},
    )
    assert second.status_code == 409
    assert second.json()["error"] == "conflict"


def test_duplicate_registration_creates_single_record(client: TestClient) -> None:
    client.post("/api/v1/devices", json={"name": "cam-1", "device_type": "camera"})
    client.post("/api/v1/devices", json={"name": "cam-1", "device_type": "thermostat"})
    listed = client.get("/api/v1/devices").json()
    assert listed["meta"]["total"] == 1
    assert listed["items"][0]["device_type"] == "camera"


def test_invalid_device_rejected(client: TestClient) -> None:
    assert client.post("/api/v1/devices", json={"device_type": "camera"}).status_code == 422
    assert (
        client.post(
            "/api/v1/devices",
            json={"name": "cam-2", "device_type": "camera", "ip_address": "not-an-ip"},
        ).status_code
        == 422
    )


def test_update_preserves_unset_fields(client: TestClient) -> None:
    created = client.post(
        "/api/v1/devices",
        json={"name": "cam-1", "device_type": "camera", "firmware_version": "1.0.0"},
    ).json()
    updated = client.patch(f"/api/v1/devices/{created['id']}", json={"firmware_version": "1.0.1"})
    assert updated.status_code == 200
    body = updated.json()
    assert body["firmware_version"] == "1.0.1"
    assert body["device_type"] == "camera"
    assert body["name"] == "cam-1"


def test_device_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/devices/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 404


def test_metadata_secret_sanitized(client: TestClient) -> None:
    response = client.post(
        "/api/v1/devices",
        json={
            "name": "cam-1",
            "device_type": "camera",
            "metadata": {"location": "bench", "password": "secret", "token": "x"},
        },
    )
    assert response.status_code == 201
    assert "password" not in response.json()["metadata"]
    assert "token" not in response.json()["metadata"]


def test_device_total_reflects_true_count_not_page_limit(client: TestClient) -> None:
    for i in range(5):
        client.post(
            "/api/v1/devices",
            json={"name": f"dev-{i}", "device_type": "camera"},
        )
    listed = client.get("/api/v1/devices", params={"limit": 2, "offset": 0}).json()
    assert listed["meta"]["limit"] == 2
    assert listed["meta"]["total"] == 5
    assert len(listed["items"]) == 2


def test_unsupported_metadata_keys_stripped(client: TestClient) -> None:
    response = client.post(
        "/api/v1/devices",
        json={
            "name": "cam-meta",
            "device_type": "camera",
            "metadata": {"location": "bench", "unknown_key": "drop-me", "role": "sensor"},
        },
    )
    assert response.status_code == 201
    meta = response.json()["metadata"]
    assert "location" in meta
    assert "role" in meta
    assert "unknown_key" not in meta
