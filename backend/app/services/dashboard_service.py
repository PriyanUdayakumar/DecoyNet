from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.db.repositories.device_repository import DeviceRepository
from app.db.repositories.event_repository import EventRepository
from app.domain.devices import DeviceStatus
from app.schemas.dashboard import DashboardSummary, RecentAlert, TimelinePoint
from app.utils.time import utc_now


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.events = EventRepository(session)
        self.devices = DeviceRepository(session)

    def summary(self) -> DashboardSummary:
        counts = self.events.summary_counts()
        devices = self.devices.list(limit=10_000, offset=0)
        return DashboardSummary(
            total_events=int(counts["total_events"]),
            unique_events=int(counts["unique_events"]),
            high_risk_events=int(counts["high_risk_events"]),
            registered_devices=len(devices),
            recently_seen_devices=sum(
                1 for device in devices if device.status == DeviceStatus.RECENTLY_SEEN.value
            ),
            severity_counts=dict(counts["severity_counts"]),
            origin_counts=dict(counts["origin_counts"]),
        )

    def timeline(self, *, hours: int = 24) -> list[TimelinePoint]:
        now = utc_now()
        points: list[TimelinePoint] = []
        for hour_offset in reversed(range(hours)):
            start = now - timedelta(hours=hour_offset + 1)
            end = now - timedelta(hours=hour_offset)
            events, _ = self.events.list(limit=10_000, offset=0, start_time=start, end_time=end)
            points.append(
                TimelinePoint(
                    bucket_start=start,
                    event_count=len(events),
                    high_risk_count=sum(1 for event in events if event.risk_score >= 70),
                )
            )
        return points

    def recent_alerts(self, *, limit: int) -> list[RecentAlert]:
        return [
            RecentAlert(
                event_id=event.id,
                event_timestamp=event.event_timestamp,
                source_ip=event.source_ip,
                event_type=event.event_type,
                origin=event.origin,
                risk_score=event.risk_score,
                severity=event.severity,
                explanation=event.explanation,
            )
            for event in self.events.recent_alerts(limit=limit)
        ]
