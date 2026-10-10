from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def make_payload(source_event_id: str, origin: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source_event_id": source_event_id,
        "source_ip": "192.168.1.50",
        "destination_ip": "192.168.1.20",
        "transport_protocol": "tcp",
        "destination_port": 80,
        "application_protocol": "http",
        "http_method": "GET",
        "request_path": "/",
        "event_type": "page_access",
        "event_timestamp": "2026-10-09T12:00:00Z",
        "origin": origin,
    }


def seed_real_records(client: TestClient) -> None:
    for event_id, origin in [
        ("esp-1", "esp32"),
        ("esp-2", "esp32"),
        ("auth-1", "authorized_test"),
    ]:
        response = client.post("/api/v1/events", json=make_payload(event_id, origin))
        assert response.status_code == 201, response.text


def test_reset_preserves_non_demo_records(client: TestClient) -> None:
    seed_real_records(client)
    client.post("/api/v1/demo/scenarios/ordinary_page_access")

    summary_before = client.get("/api/v1/dashboard/summary").json()
    assert summary_before["total_events"] == 4

    reset = client.post("/api/v1/demo/reset")
    assert reset.status_code == 200
    assert reset.json()["deleted_events"] == 1

    summary_after = client.get("/api/v1/dashboard/summary").json()
    assert summary_after["total_events"] == 3
    assert summary_after["origin_counts"] == {"esp32": 2, "authorized_test": 1}


def test_reset_is_repeatable(client: TestClient) -> None:
    client.post("/api/v1/demo/scenarios/ordinary_page_access")
    assert client.post("/api/v1/demo/reset").json()["deleted_events"] == 1
    assert client.post("/api/v1/demo/reset").json()["deleted_events"] == 0
    assert client.post("/api/v1/demo/reset").json()["deleted_events"] == 0


def test_reset_empty_dataset(client: TestClient) -> None:
    reset = client.post("/api/v1/demo/reset")
    assert reset.status_code == 200
    assert reset.json()["deleted_events"] == 0


def test_demo_mode_disabled_blocks_scenario_and_reset() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.api.dependencies import get_db, get_settings_dependency
    from app.core.config import Settings
    from app.db.base import Base
    from app.main import app

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_settings() -> Settings:
        return Settings(demo_mode=False)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings_dependency] = override_settings
    try:
        with TestClient(app) as test_client:
            scenario = test_client.post("/api/v1/demo/scenarios/ordinary_page_access")
            assert scenario.status_code == 403
            assert scenario.json()["error"] == "demo_mode_disabled"
            reset = test_client.post("/api/v1/demo/reset")
            assert reset.status_code == 403
            assert reset.json()["error"] == "demo_mode_disabled"
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_reset_preserves_device_inventory(client: TestClient) -> None:
    client.post("/api/v1/devices", json={"name": "real-sensor", "device_type": "sensor"})
    client.post("/api/v1/demo/scenarios/sensitive_endpoint_access")
    devices_before = client.get("/api/v1/devices").json()["meta"]["total"]
    assert devices_before == 1

    client.post("/api/v1/demo/reset")
    devices_after = client.get("/api/v1/devices").json()["meta"]["total"]
    assert devices_after == 1
    assert client.get("/api/v1/devices").json()["items"][0]["name"] == "real-sensor"


def test_reset_preserves_authorized_test_records_and_counts(client: TestClient) -> None:
    # Seed authorized_test and esp32 records
    client.post("/api/v1/events", json=make_payload("at-1", "authorized_test"))
    client.post("/api/v1/events", json=make_payload("at-2", "authorized_test"))
    client.post("/api/v1/events", json=make_payload("esp-keep", "esp32"))
    client.post("/api/v1/demo/scenarios/repeated_login_attempts")

    summary_before = client.get("/api/v1/dashboard/summary").json()
    assert summary_before["total_events"] == 7  # 2 + 1 + 4
    assert summary_before["origin_counts"]["authorized_test"] == 2
    assert summary_before["origin_counts"]["esp32"] == 1
    assert summary_before["origin_counts"]["simulator"] == 4

    reset_res = client.post("/api/v1/demo/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["deleted_events"] == 4

    summary_after = client.get("/api/v1/dashboard/summary").json()
    assert summary_after["total_events"] == 3
    assert summary_after["origin_counts"] == {"authorized_test": 2, "esp32": 1}
    assert "simulator" not in summary_after["origin_counts"]
