from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.repositories.event_repository import EventRepository
from app.domain.events import EventOrigin, EventType, Severity
from app.schemas.events import EventAnalysisResponse, EventRead
from app.services.mappers import event_to_read


class EventQueryService:
    def __init__(self, session: Session) -> None:
        self.events = EventRepository(session)

    def list_events(
        self,
        *,
        limit: int,
        offset: int,
        severity: Severity | None = None,
        event_type: EventType | None = None,
        device_id: UUID | None = None,
        source_ip: str | None = None,
        origin: EventOrigin | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[EventRead], int]:
        events, total = self.events.list(
            limit=limit,
            offset=offset,
            severity=severity,
            event_type=event_type,
            device_id=device_id,
            source_ip=source_ip,
            origin=origin,
            start_time=start_time,
            end_time=end_time,
        )
        return [event_to_read(event) for event in events], total

    def get_event(self, event_id: UUID) -> EventRead:
        event = self.events.get(event_id)
        if event is None:
            raise NotFoundError("Event not found")
        return event_to_read(event)

    def get_analysis(self, event_id: UUID) -> EventAnalysisResponse:
        event = self.events.get(event_id)
        if event is None:
            raise NotFoundError("Event not found")
        return EventAnalysisResponse(
            event_id=event_id,
            risk_score=event.risk_score,
            severity=event.severity,
            detection_rule_ids=event.detection_rule_ids,
            explanation=event.explanation,
            score_contributions=event.score_contributions,
        )

    def events_for_device(
        self, *, device_id: UUID, limit: int, offset: int
    ) -> tuple[list[EventRead], int]:
        events, total = self.events.events_for_device(
            device_id=device_id, limit=limit, offset=offset
        )
        return [event_to_read(event) for event in events], total
