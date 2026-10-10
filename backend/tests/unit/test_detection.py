from __future__ import annotations

from ipaddress import IPv4Address

from app.core.config import Settings
from app.detection.rule_engine import RuleBasedDetectionEngine
from app.detection.scoring import clamp_score, severity_for_score
from app.domain.detection import DetectionContext
from app.domain.events import (
    ApplicationProtocol,
    EventOrigin,
    EventType,
    NormalizedSecurityEvent,
    TransportProtocol,
)
from app.utils.time import utc_now


def make_event(event_type: EventType, path: str | None) -> NormalizedSecurityEvent:
    now = utc_now()
    return NormalizedSecurityEvent(
        source_event_id="unit-1",
        source_ip=IPv4Address("192.168.1.50"),
        destination_ip=IPv4Address("192.168.1.20"),
        transport_protocol=TransportProtocol.TCP,
        destination_port=80,
        application_protocol=ApplicationProtocol.HTTP,
        event_type=event_type,
        event_timestamp=now,
        received_timestamp=now,
        origin=EventOrigin.SIMULATOR,
        http_method="GET",
        request_path=path,
    )


def test_scoring_boundaries_and_thresholds() -> None:
    assert clamp_score(-10) == 0
    assert clamp_score(120) == 100
    assert severity_for_score(0).value == "info"
    assert severity_for_score(45).value == "medium"
    assert severity_for_score(90).value == "critical"


def test_sensitive_endpoint_rule() -> None:
    engine = RuleBasedDetectionEngine(Settings())
    result = engine.analyze(
        make_event(EventType.SENSITIVE_ENDPOINT_ACCESS, "/admin/config"), DetectionContext()
    )
    assert "sensitive_endpoint_access" in result.rule_ids
    assert result.risk_score >= 35


def test_landing_page_low_score() -> None:
    engine = RuleBasedDetectionEngine(Settings())
    result = engine.analyze(make_event(EventType.PAGE_ACCESS, "/"), DetectionContext())
    assert result.risk_score == 5
    assert result.severity.value == "info"
