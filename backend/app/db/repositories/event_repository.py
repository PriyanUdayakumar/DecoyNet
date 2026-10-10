from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.models.event import EventModel
from app.domain.events import EventHistoryItem, EventOrigin, EventType, Severity
from app.utils.time import utc_now


class EventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, event_id: UUID | str) -> EventModel | None:
        return self.session.get(EventModel, str(event_id))

    def find_duplicate(self, *, origin: EventOrigin, source_event_id: str) -> EventModel | None:
        return self.session.scalar(
            select(EventModel).where(
                EventModel.origin == origin.value,
                EventModel.source_event_id == source_event_id,
            )
        )

    def create(self, **values: object) -> EventModel:
        event = EventModel(**values)
        self.session.add(event)
        self.session.flush()
        return event

    def list(
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
    ) -> tuple[list[EventModel], int]:
        query = self._filtered_query(
            severity=severity,
            event_type=event_type,
            device_id=device_id,
            source_ip=source_ip,
            origin=origin,
            start_time=start_time,
            end_time=end_time,
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            self.session.scalars(
                query.order_by(EventModel.event_timestamp.desc(), EventModel.id.asc())
                .limit(limit)
                .offset(offset)
            )
        )
        return items, total

    def _filtered_query(
        self,
        *,
        severity: Severity | None,
        event_type: EventType | None,
        device_id: UUID | None,
        source_ip: str | None,
        origin: EventOrigin | None,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> Select[tuple[EventModel]]:
        query = select(EventModel)
        if severity:
            query = query.where(EventModel.severity == severity.value)
        if event_type:
            query = query.where(EventModel.event_type == event_type.value)
        if device_id:
            query = query.where(EventModel.device_id == str(device_id))
        if source_ip:
            query = query.where(EventModel.source_ip == source_ip)
        if origin:
            query = query.where(EventModel.origin == origin.value)
        if start_time:
            query = query.where(EventModel.event_timestamp >= start_time)
        if end_time:
            query = query.where(EventModel.event_timestamp <= end_time)
        return query

    def recent_context(
        self,
        *,
        source_ip: str,
        since_seconds: int = 300,
        limit: int = 100,
    ) -> list[EventHistoryItem]:
        since = utc_now() - timedelta(seconds=since_seconds)
        rows = self.session.scalars(
            select(EventModel)
            .where(EventModel.source_ip == source_ip, EventModel.event_timestamp >= since)
            .order_by(EventModel.event_timestamp.desc())
            .limit(limit)
        )
        return [
            EventHistoryItem(
                source_ip=row.source_ip,
                request_path=row.request_path,
                event_type=EventType(row.event_type),
                event_timestamp=row.event_timestamp,
                risk_score=row.risk_score,
            )
            for row in rows
        ]

    def events_for_device(
        self, *, device_id: UUID, limit: int, offset: int
    ) -> tuple[list[EventModel], int]:
        query = select(EventModel).where(EventModel.device_id == str(device_id))
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(
            self.session.scalars(
                query.order_by(EventModel.event_timestamp.desc()).limit(limit).offset(offset)
            )
        )
        return items, total

    def delete_demo_events(self) -> int:
        events = list(
            self.session.scalars(
                select(EventModel).where(EventModel.origin == EventOrigin.SIMULATOR.value)
            )
        )
        count = len(events)
        for event in events:
            self.session.delete(event)
        self.session.flush()
        return count

    def summary_counts(self) -> dict[str, object]:
        total_events = self.session.scalar(select(func.count(EventModel.id))) or 0
        unique_events = (
            self.session.scalar(select(func.count(func.distinct(EventModel.source_event_id)))) or 0
        )
        high_risk_events = (
            self.session.scalar(
                select(func.count(EventModel.id)).where(EventModel.risk_score >= 70)
            )
            or 0
        )
        severity_counts = {
            severity: count
            for severity, count in self.session.execute(
                select(EventModel.severity, func.count(EventModel.id)).group_by(EventModel.severity)
            )
        }
        origin_counts = {
            origin: count
            for origin, count in self.session.execute(
                select(EventModel.origin, func.count(EventModel.id)).group_by(EventModel.origin)
            )
        }
        return {
            "total_events": total_events,
            "unique_events": unique_events,
            "high_risk_events": high_risk_events,
            "severity_counts": severity_counts,
            "origin_counts": origin_counts,
        }

    def recent_alerts(self, *, limit: int) -> list[EventModel]:
        return list(
            self.session.scalars(
                select(EventModel)
                .where(EventModel.risk_score >= 45)
                .order_by(EventModel.event_timestamp.desc())
                .limit(limit)
            )
        )
