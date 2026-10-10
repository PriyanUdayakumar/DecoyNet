from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.events import EventOrigin, EventType, Severity


class DashboardSummary(BaseModel):
    total_events: int
    unique_events: int
    high_risk_events: int
    registered_devices: int
    recently_seen_devices: int
    severity_counts: dict[str, int]
    origin_counts: dict[str, int]


class TimelinePoint(BaseModel):
    bucket_start: datetime
    event_count: int
    high_risk_count: int


class RecentAlert(BaseModel):
    event_id: UUID
    event_timestamp: datetime
    source_ip: str
    event_type: EventType
    origin: EventOrigin
    risk_score: int
    severity: Severity
    explanation: str
