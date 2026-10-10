from __future__ import annotations

from ipaddress import IPv4Address

from app.domain.events import ApplicationProtocol, EventOrigin, EventType, TransportProtocol
from app.schemas.events import EventIngestRequest
from app.utils.time import utc_now


class SimulatorEventGenerator:
    def generate(self, scenario_name: str) -> list[EventIngestRequest]:
        now = utc_now()
        base = {
            "schema_version": 1,
            "source_ip": IPv4Address("192.168.1.50"),
            "destination_ip": IPv4Address("192.168.1.20"),
            "transport_protocol": TransportProtocol.TCP,
            "destination_port": 80,
            "application_protocol": ApplicationProtocol.HTTP,
            "event_timestamp": now,
            "origin": EventOrigin.SIMULATOR,
        }
        if scenario_name == "ordinary_page_access":
            return [
                EventIngestRequest(
                    **base,
                    source_event_id="demo-ordinary-page-access-1",
                    http_method="GET",
                    request_path="/",
                    event_type=EventType.PAGE_ACCESS,
                    metadata={"scenario": scenario_name},
                )
            ]
        if scenario_name == "sensitive_endpoint_access":
            return [
                EventIngestRequest(
                    **base,
                    source_event_id="demo-sensitive-endpoint-1",
                    http_method="GET",
                    request_path="/admin/config",
                    event_type=EventType.SENSITIVE_ENDPOINT_ACCESS,
                    metadata={"scenario": scenario_name},
                )
            ]
        if scenario_name == "repeated_login_attempts":
            return [
                EventIngestRequest(
                    **base,
                    source_event_id=f"demo-login-{index}",
                    http_method="POST",
                    request_path="/login",
                    event_type=EventType.LOGIN_ATTEMPT,
                    metadata={"scenario": scenario_name, "username": "admin", "result": "failed"},
                )
                for index in range(1, 5)
            ]
        if scenario_name == "unusual_endpoint_burst":
            paths = ["/.env", "/wp-login.php", "/phpmyadmin", "/cgi-bin/status", "/etc/passwd"]
            return [
                EventIngestRequest(
                    **base,
                    source_event_id=f"demo-unusual-{index}",
                    http_method="GET",
                    request_path=path,
                    event_type=EventType.UNUSUAL_ENDPOINT_ACCESS,
                    metadata={"scenario": scenario_name},
                )
                for index, path in enumerate(paths, start=1)
            ]
        raise ValueError("Unknown demo scenario")


SCENARIO_NAMES = [
    "ordinary_page_access",
    "sensitive_endpoint_access",
    "repeated_login_attempts",
    "unusual_endpoint_burst",
]
