from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import sanitize_metadata
from app.db.repositories.device_repository import DeviceRepository
from app.db.repositories.event_repository import EventRepository
from app.detection.interfaces import DetectionEngine
from app.domain.detection import DetectionContext
from app.domain.events import NormalizedSecurityEvent, ProcessingStatus
from app.schemas.events import EventIngestRequest, EventIngestResponse
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


class EventIngestionService:
    def __init__(self, session: Session, detection_engine: DetectionEngine) -> None:
        self.session = session
        self.events = EventRepository(session)
        self.devices = DeviceRepository(session)
        self.detection_engine = detection_engine

    def ingest(self, request: EventIngestRequest) -> EventIngestResponse:
        duplicate = self.events.find_duplicate(
            origin=request.origin, source_event_id=request.source_event_id
        )
        if duplicate:
            logger.info(
                "duplicate_event origin=%s source_event_id=%s",
                request.origin,
                request.source_event_id,
            )
            return EventIngestResponse(
                event_id=UUID(duplicate.id),
                duplicate=True,
                risk_score=duplicate.risk_score,
                severity=duplicate.severity,
                processing_status=ProcessingStatus.DUPLICATE,
                explanation=duplicate.explanation,
            )

        received_at = utc_now()
        metadata = sanitize_metadata(request.metadata)
        normalized = NormalizedSecurityEvent(
            schema_version=request.schema_version,
            source_event_id=request.source_event_id,
            device_id=request.device_id,
            source_ip=request.source_ip,
            destination_ip=request.destination_ip,
            transport_protocol=request.transport_protocol,
            destination_port=request.destination_port,
            application_protocol=request.application_protocol,
            http_method=request.http_method,
            request_path=request.request_path,
            event_type=request.event_type,
            event_timestamp=request.event_timestamp,
            received_timestamp=received_at,
            origin=request.origin,
            metadata=metadata,
        )
        device_known = False
        if request.device_id:
            device = self.devices.get(request.device_id)
            device_known = device is not None
            if device:
                self.devices.mark_seen(device)
        context = DetectionContext(
            recent_events=self.events.recent_context(source_ip=str(request.source_ip)),
            device_known=device_known,
        )
        detection = self.detection_engine.analyze(normalized, context)
        try:
            event = self.events.create(
                schema_version=request.schema_version,
                source_event_id=request.source_event_id,
                device_id=str(request.device_id) if request.device_id and device_known else None,
                source_ip=str(request.source_ip),
                destination_ip=str(request.destination_ip),
                transport_protocol=request.transport_protocol.value,
                destination_port=request.destination_port,
                application_protocol=request.application_protocol.value,
                http_method=request.http_method,
                request_path=request.request_path,
                event_type=request.event_type.value,
                event_timestamp=request.event_timestamp,
                received_timestamp=received_at,
                risk_score=detection.risk_score,
                severity=detection.severity.value,
                detection_rule_ids=detection.rule_ids,
                explanation=detection.explanation,
                origin=request.origin.value,
                metadata_json=metadata,
                score_contributions=[
                    contribution.__dict__ for contribution in detection.contributions
                ],
                processing_status=ProcessingStatus.PROCESSED.value,
            )
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            duplicate = self.events.find_duplicate(
                origin=request.origin, source_event_id=request.source_event_id
            )
            if duplicate is None:
                raise
            return EventIngestResponse(
                event_id=UUID(duplicate.id),
                duplicate=True,
                risk_score=duplicate.risk_score,
                severity=duplicate.severity,
                processing_status=ProcessingStatus.DUPLICATE,
                explanation=duplicate.explanation,
            )
        logger.info("event_ingested event_id=%s risk_score=%s", event.id, event.risk_score)
        return EventIngestResponse(
            event_id=UUID(event.id),
            duplicate=False,
            risk_score=event.risk_score,
            severity=detection.severity,
            processing_status=ProcessingStatus.PROCESSED,
            explanation=event.explanation,
        )
