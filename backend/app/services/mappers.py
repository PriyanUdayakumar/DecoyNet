from __future__ import annotations

from uuid import UUID

from app.db.models.device import DeviceModel
from app.db.models.event import EventModel
from app.domain.devices import DeviceStatus
from app.domain.events import (
    ApplicationProtocol,
    EventOrigin,
    EventType,
    ProcessingStatus,
    Severity,
    TransportProtocol,
)
from app.schemas.devices import DeviceRead
from app.schemas.events import EventRead


def event_to_read(event: EventModel) -> EventRead:
    return EventRead(
        id=UUID(event.id),
        source_event_id=event.source_event_id,
        device_id=UUID(event.device_id) if event.device_id else None,
        source_ip=event.source_ip,
        destination_ip=event.destination_ip,
        transport_protocol=TransportProtocol(event.transport_protocol),
        destination_port=event.destination_port,
        application_protocol=ApplicationProtocol(event.application_protocol),
        http_method=event.http_method,
        request_path=event.request_path,
        event_type=EventType(event.event_type),
        event_timestamp=event.event_timestamp,
        received_timestamp=event.received_timestamp,
        risk_score=event.risk_score,
        severity=Severity(event.severity),
        detection_rule_ids=event.detection_rule_ids,
        explanation=event.explanation,
        origin=EventOrigin(event.origin),
        metadata=event.metadata_json,
        processing_status=ProcessingStatus(event.processing_status),
    )


def device_to_read(device: DeviceModel) -> DeviceRead:
    return DeviceRead(
        id=UUID(device.id),
        name=device.name,
        device_type=device.device_type,
        ip_address=device.ip_address,
        firmware_version=device.firmware_version,
        registered_at=device.registered_at,
        last_seen_at=device.last_seen_at,
        status=DeviceStatus(device.status),
        metadata=device.metadata_json,
    )
