from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def make_payload(source_event_id: str, origin: str = "simulator") -> dict[str, Any]:
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
        "origin": origin,
        "metadata": {"username": "admin", "password": "hunter2"},
    }


def test_ingest_valid_event(client: TestClient) -> None:
    response = client.post("/api/v1/events", json=make_payload("i-1"))
    assert response.status_code == 201
    body = response.json()
    assert body["duplicate"] is False
    assert 0 <= body["risk_score"] <= 100
    assert body["explanation"]


def test_server_calculates_score_ignoring_client_claims(client: TestClient) -> None:
    payload = make_payload("i-score")
    payload["metadata"]["risk_score"] = 0
    payload["metadata"]["severity"] = "info"
    first = client.post("/api/v1/events", json=payload).json()
    detail = client.get(f"/api/v1/events/{first['event_id']}").json()
    assert detail["risk_score"] >= 35
    assert detail["severity"] != "info"


def test_repeated_submission_same_source_event_id(client: TestClient) -> None:
    first = client.post("/api/v1/events", json=make_payload("i-dup")).json()
    for _ in range(3):
        retry = client.post("/api/v1/events", json=make_payload("i-dup")).json()
        assert retry["duplicate"] is True
        assert retry["event_id"] == first["event_id"]
        assert retry["risk_score"] == first["risk_score"]
    assert client.get("/api/v1/events").json()["meta"]["total"] == 1


def test_same_source_id_different_origins_both_stored(client: TestClient) -> None:
    a = client.post("/api/v1/events", json=make_payload("i-shared", origin="simulator"))
    b = client.post("/api/v1/events", json=make_payload("i-shared", origin="esp32"))
    assert a.status_code == 201
    assert b.status_code == 201
    assert a.json()["duplicate"] is False
    assert b.json()["duplicate"] is False
    assert client.get("/api/v1/events").json()["meta"]["total"] == 2


def test_invalid_payloads_rejected(client: TestClient) -> None:
    cases: list[dict[str, Any]] = [
        {"source_ip": "not-an-ip"},
        {"destination_port": 0},
        {"destination_port": 99999},
        {"schema_version": 2},
        {"origin": "hacker"},
        {"event_timestamp": "yesterday"},
        {"request_path": "no-leading-slash"},
    ]
    for index, override in enumerate(cases):
        payload = make_payload(f"i-invalid-{index}")
        payload.update(override)
        response = client.post("/api/v1/events", json=payload)
        assert response.status_code == 422, f"{override} -> {response.status_code}"


def test_passwords_never_stored(client: TestClient) -> None:
    response = client.post("/api/v1/events", json=make_payload("i-secret"))
    assert response.status_code == 201
    detail = client.get(f"/api/v1/events/{response.json()['event_id']}").json()
    assert "password" not in detail["metadata"]
    serialized = str(detail)
    assert "hunter2" not in serialized


def test_unknown_device_id_not_linked(client: TestClient) -> None:
    payload = make_payload("i-ghost")
    payload["device_id"] = "00000000-0000-0000-0000-000000000099"
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 201
    detail = client.get(f"/api/v1/events/{response.json()['event_id']}").json()
    assert detail["device_id"] is None
