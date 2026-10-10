from __future__ import annotations

from fastapi.testclient import TestClient

SCENARIOS = [
    "ordinary_page_access",
    "sensitive_endpoint_access",
    "repeated_login_attempts",
    "unusual_endpoint_burst",
]


def test_scenario_list(client: TestClient) -> None:
    response = client.get("/api/v1/demo/scenarios")
    assert response.status_code == 200
    assert response.json() == SCENARIOS


def test_all_scenarios_simulator_origin(client: TestClient) -> None:
    for scenario in SCENARIOS:
        response = client.post(f"/api/v1/demo/scenarios/{scenario}")
        assert response.status_code == 200, scenario
        events = response.json()
        assert len(events) >= 1
        for event in events:
            assert event["duplicate"] is False
            assert 0 <= event["risk_score"] <= 100
            assert event["severity"] in {"info", "low", "medium", "high", "critical"}
            assert event["explanation"]
        listed = client.get("/api/v1/events", params={"origin": "simulator"})
        source_ids = {item["source_event_id"] for item in listed.json()["items"]}
        assert listed.json()["meta"]["total"] >= len(events), scenario
        assert any(sid.startswith("demo-") for sid in source_ids), scenario
        client.post("/api/v1/demo/reset")


def test_login_scenario_excludes_password(client: TestClient) -> None:
    client.post("/api/v1/demo/scenarios/repeated_login_attempts")
    listed = client.get("/api/v1/events", params={"event_type": "login_attempt"})
    for item in listed.json()["items"]:
        for key in ("password", "token", "authorization", "cookie"):
            assert key not in item["metadata"]


def test_repeated_seeding_yields_duplicates(client: TestClient) -> None:
    first = client.post("/api/v1/demo/scenarios/sensitive_endpoint_access").json()
    assert all(event["duplicate"] is False for event in first)
    second = client.post("/api/v1/demo/scenarios/sensitive_endpoint_access").json()
    assert all(event["duplicate"] is True for event in second)
    listed = client.get("/api/v1/events").json()
    assert listed["meta"]["total"] == 1


def test_unknown_scenario_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/demo/scenarios/nonexistent")
    assert response.status_code == 404


def test_simulator_events_not_esp32(client: TestClient) -> None:
    client.post("/api/v1/demo/scenarios/ordinary_page_access")
    esp = client.get("/api/v1/events", params={"origin": "esp32"})
    assert esp.json()["meta"]["total"] == 0


def test_dashboard_reflects_demo_events(client: TestClient) -> None:
    client.post("/api/v1/demo/scenarios/sensitive_endpoint_access")
    summary = client.get("/api/v1/dashboard/summary").json()
    assert summary["total_events"] == 1
    assert summary["origin_counts"] == {"simulator": 1}


def test_each_scenario_persists_expected_attributes(client: TestClient) -> None:
    expected = {
        "ordinary_page_access": (1, "page_access"),
        "sensitive_endpoint_access": (1, "sensitive_endpoint_access"),
        "repeated_login_attempts": (4, "login_attempt"),
        "unusual_endpoint_burst": (5, "unusual_endpoint_access"),
    }
    for scenario_name, (count, primary_type) in expected.items():
        client.post("/api/v1/demo/reset")
        response = client.post(f"/api/v1/demo/scenarios/{scenario_name}")
        assert response.status_code == 200
        events = response.json()
        assert len(events) == count
        assert all(event["duplicate"] is False for event in events)

        listed = client.get(
            "/api/v1/events", params={"origin": "simulator", "event_type": primary_type}
        ).json()
        assert listed["meta"]["total"] == count
        for item in listed["items"]:
            assert item["origin"] == "simulator"
            assert item["risk_score"] >= 0
            assert item["severity"] in {"info", "low", "medium", "high", "critical"}


def test_burst_scenario_increases_risk_over_subsequent_hits(client: TestClient) -> None:
    client.post("/api/v1/demo/reset")
    events = client.post("/api/v1/demo/scenarios/unusual_endpoint_burst").json()
    assert len(events) == 5
    # Later events in burst trigger multiple_unusual_endpoints / suspicious_burst rules
    last_event = events[-1]
    analysis = client.get(f"/api/v1/events/{last_event['event_id']}/analysis").json()
    assert analysis["risk_score"] >= 25
    assert len(analysis["detection_rule_ids"]) >= 1
