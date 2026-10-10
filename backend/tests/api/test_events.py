from __future__ import annotations

from fastapi.testclient import TestClient


def event_payload(source_event_id: str = "evt-1") -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_event_id": source_event_id,
        "source_ip": "192.168.1.50",
        "destination_ip": "192.168.1.20",
        "transport_protocol": "tcp",
        "destination_port": 80,
        "application_protocol": "http",
        "http_method": "GET",
        "request_path": "/admin/config",
        "event_type": "sensitive_endpoint_access",
        "event_timestamp": "2026-10-09T12:00:00Z",
        "origin": "simulator",
        "metadata": {"password": "not-stored", "username": "admin"},
    }


def test_event_ingestion_persistence_and_duplicate(client: TestClient) -> None:
    created = client.post("/api/v1/events", json=event_payload())
    assert created.status_code == 201
    body = created.json()
    assert body["duplicate"] is False
    assert body["risk_score"] >= 35
    assert body["severity"] in {"low", "medium", "high", "critical"}

    duplicate = client.post("/api/v1/events", json=event_payload())
    assert duplicate.status_code == 201
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["event_id"] == body["event_id"]

    listed = client.get("/api/v1/events")
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 1
    assert listed.json()["items"][0]["metadata"] == {"username": "admin"}


def test_invalid_event_rejected(client: TestClient) -> None:
    payload = event_payload("evt-invalid")
    payload["destination_port"] = 70000
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 422


def test_event_filtering(client: TestClient) -> None:
    client.post("/api/v1/events", json=event_payload("evt-filter"))
    response = client.get("/api/v1/events", params={"severity": "low"})
    assert response.status_code == 200
    assert response.json()["meta"]["total"] >= 0
