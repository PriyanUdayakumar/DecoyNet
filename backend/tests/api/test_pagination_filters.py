from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

BASE_PAYLOAD: dict[str, Any] = {
    "schema_version": 1,
    "source_ip": "192.168.1.50",
    "destination_ip": "192.168.1.20",
    "transport_protocol": "tcp",
    "destination_port": 80,
    "application_protocol": "http",
    "event_timestamp": "2026-10-09T12:00:00Z",
    "origin": "simulator",
}


def make_payload(source_event_id: str, **overrides: Any) -> dict[str, Any]:
    payload = {**BASE_PAYLOAD, "source_event_id": source_event_id, **overrides}
    if "event_type" not in payload:
        payload["event_type"] = "page_access"
        payload["http_method"] = "GET"
        payload["request_path"] = "/"
    return payload


def seed(client: TestClient, payloads: list[dict[str, Any]]) -> None:
    for payload in payloads:
        response = client.post("/api/v1/events", json=payload)
        assert response.status_code == 201, response.text


def test_default_pagination(client: TestClient) -> None:
    seed(client, [make_payload(f"p-{i}") for i in range(5)])
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["limit"] == 50
    assert body["meta"]["offset"] == 0
    assert body["meta"]["total"] == 5
    assert len(body["items"]) == 5


def test_custom_page_size_and_offset(client: TestClient) -> None:
    seed(client, [make_payload(f"p-{i}") for i in range(5)])
    page1 = client.get("/api/v1/events", params={"limit": 2, "offset": 0}).json()
    page2 = client.get("/api/v1/events", params={"limit": 2, "offset": 2}).json()
    ids1 = {item["source_event_id"] for item in page1["items"]}
    ids2 = {item["source_event_id"] for item in page2["items"]}
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    assert not (ids1 & ids2)


def test_offset_beyond_total_returns_empty(client: TestClient) -> None:
    seed(client, [make_payload("p-0")])
    response = client.get("/api/v1/events", params={"offset": 10})
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["meta"]["total"] == 1


def test_invalid_pagination_rejected(client: TestClient) -> None:
    assert client.get("/api/v1/events", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/events", params={"limit": 500}).status_code == 422
    assert client.get("/api/v1/events", params={"offset": -1}).status_code == 422


def test_filter_by_severity(client: TestClient) -> None:
    seed(
        client,
        [
            make_payload("f-low", event_type="page_access", request_path="/"),
            make_payload("f-high", event_type="sensitive_endpoint_access", request_path="/admin"),
        ],
    )
    response = client.get("/api/v1/events", params={"severity": "low"})
    ids = {item["source_event_id"] for item in response.json()["items"]}
    assert ids == {"f-high"}


def test_filter_by_event_type(client: TestClient) -> None:
    seed(
        client,
        [
            make_payload("f-page", event_type="page_access", request_path="/"),
            make_payload(
                "f-login", event_type="login_attempt", http_method="POST", request_path="/login"
            ),
        ],
    )
    response = client.get("/api/v1/events", params={"event_type": "login_attempt"})
    ids = {item["source_event_id"] for item in response.json()["items"]}
    assert ids == {"f-login"}


def test_filter_by_source_ip(client: TestClient) -> None:
    seed(
        client,
        [
            make_payload("f-a", source_ip="10.0.0.1"),
            make_payload("f-b", source_ip="10.0.0.2"),
        ],
    )
    response = client.get("/api/v1/events", params={"source_ip": "10.0.0.1"})
    ids = {item["source_event_id"] for item in response.json()["items"]}
    assert ids == {"f-a"}


def test_filter_by_origin(client: TestClient) -> None:
    seed(
        client,
        [
            make_payload("f-sim", origin="simulator"),
            make_payload("f-esp", origin="esp32"),
        ],
    )
    response = client.get("/api/v1/events", params={"origin": "esp32"})
    ids = {item["source_event_id"] for item in response.json()["items"]}
    assert ids == {"f-esp"}


def test_filter_by_device_id(client: TestClient) -> None:
    device = client.post(
        "/api/v1/devices",
        json={"name": "cam-1", "device_type": "camera"},
    ).json()
    linked = make_payload("f-dev", device_id=device["id"])
    linked["event_type"] = "heartbeat"
    seed(client, [linked, make_payload("f-free")])
    response = client.get("/api/v1/events", params={"device_id": device["id"]})
    ids = {item["source_event_id"] for item in response.json()["items"]}
    assert ids == {"f-dev"}


def test_time_range_filters(client: TestClient) -> None:
    seed(
        client,
        [
            make_payload("t-early", event_timestamp="2026-10-09T10:00:00Z"),
            make_payload("t-inside", event_timestamp="2026-10-09T12:00:00Z"),
            make_payload("t-late", event_timestamp="2026-10-09T14:00:00Z"),
        ],
    )
    response = client.get(
        "/api/v1/events",
        params={"start_time": "2026-10-09T10:00:00Z", "end_time": "2026-10-09T12:00:00Z"},
    )
    ids = {item["source_event_id"] for item in response.json()["items"]}
    assert ids == {"t-early", "t-inside"}


def test_combined_filters(client: TestClient) -> None:
    seed(
        client,
        [
            make_payload("c-match", origin="esp32", event_type="heartbeat"),
            make_payload("c-wrong-origin", event_type="heartbeat"),
            make_payload(
                "c-wrong-type", origin="esp32", event_type="page_access", request_path="/"
            ),
        ],
    )
    response = client.get("/api/v1/events", params={"origin": "esp32", "event_type": "heartbeat"})
    ids = {item["source_event_id"] for item in response.json()["items"]}
    assert ids == {"c-match"}


def test_invalid_time_range_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/events", params={"start_time": "not-a-date"})
    assert response.status_code == 422


def test_deterministic_ordering(client: TestClient) -> None:
    seed(
        client,
        [
            make_payload("o-a", event_timestamp="2026-10-09T12:00:00Z"),
            make_payload("o-b", event_timestamp="2026-10-09T12:00:00Z"),
            make_payload("o-c", event_timestamp="2026-10-09T11:00:00Z"),
        ],
    )
    first = client.get("/api/v1/events").json()
    second = client.get("/api/v1/events").json()
    ids_first = [item["source_event_id"] for item in first["items"]]
    ids_second = [item["source_event_id"] for item in second["items"]]
    assert ids_first == ids_second
    assert ids_first[0] in {"o-a", "o-b"}
    assert ids_first[-1] == "o-c"


def test_time_range_excludes_outside_boundaries(client: TestClient) -> None:
    seed(
        client,
        [
            make_payload("b-before", event_timestamp="2026-10-09T09:59:59Z"),
            make_payload("b-start", event_timestamp="2026-10-09T10:00:00Z"),
            make_payload("b-end", event_timestamp="2026-10-09T12:00:00Z"),
            make_payload("b-after", event_timestamp="2026-10-09T12:00:01Z"),
        ],
    )
    response = client.get(
        "/api/v1/events",
        params={"start_time": "2026-10-09T10:00:00Z", "end_time": "2026-10-09T12:00:00Z"},
    )
    body = response.json()
    assert body["meta"]["total"] == 2
    assert {item["source_event_id"] for item in body["items"]} == {"b-start", "b-end"}


def test_total_reflects_applied_filters(client: TestClient) -> None:
    seed(
        client,
        [
            make_payload("tot-sim", origin="simulator"),
            make_payload("tot-esp1", origin="esp32"),
            make_payload("tot-esp2", origin="esp32"),
        ],
    )
    body = client.get("/api/v1/events", params={"origin": "esp32"}).json()
    assert body["meta"]["total"] == 2
    assert {item["source_event_id"] for item in body["items"]} == {"tot-esp1", "tot-esp2"}


def test_reversed_time_range_rejected(client: TestClient) -> None:
    response = client.get(
        "/api/v1/events",
        params={"start_time": "2026-10-09T12:00:00Z", "end_time": "2026-10-09T10:00:00Z"},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_time_range"


def test_equal_time_range_allowed(client: TestClient) -> None:
    seed(client, [make_payload("eq-1", event_timestamp="2026-10-09T12:00:00Z")])
    response = client.get(
        "/api/v1/events",
        params={"start_time": "2026-10-09T12:00:00Z", "end_time": "2026-10-09T12:00:00Z"},
    )
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1


def test_identical_timestamps_ordered_stably_across_pages(client: TestClient) -> None:
    ids = ["same-a", "same-b", "same-c", "same-d"]
    seed(client, [make_payload(sid, event_timestamp="2026-10-09T12:00:00Z") for sid in ids])
    page1 = client.get("/api/v1/events", params={"limit": 2, "offset": 0}).json()
    page2 = client.get("/api/v1/events", params={"limit": 2, "offset": 2}).json()
    order1 = [item["source_event_id"] for item in page1["items"]]
    order2 = [item["source_event_id"] for item in page2["items"]]
    assert set(order1) | set(order2) == set(ids)
    assert not (set(order1) & set(order2))
    repeat = client.get("/api/v1/events", params={"limit": 4}).json()
    assert [item["source_event_id"] for item in repeat["items"]] == order1 + order2
