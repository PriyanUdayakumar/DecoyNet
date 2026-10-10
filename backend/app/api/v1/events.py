from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_detection_engine
from app.core.exceptions import InvalidTimeRangeError
from app.detection.interfaces import DetectionEngine
from app.domain.events import EventOrigin, EventType, Severity
from app.schemas.events import (
    EventAnalysisResponse,
    EventIngestRequest,
    EventIngestResponse,
    EventRead,
)
from app.services.event_ingestion_service import EventIngestionService
from app.services.event_query_service import EventQueryService
from app.utils.time import ensure_utc

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventIngestResponse, status_code=201)
def ingest_event(
    payload: EventIngestRequest,
    db: Session = Depends(get_db),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
) -> EventIngestResponse:
    return EventIngestionService(db, detection_engine).ingest(payload)


@router.get("")
def list_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    severity: Severity | None = None,
    event_type: EventType | None = None,
    device_id: UUID | None = None,
    source_ip: str | None = None,
    origin: EventOrigin | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if (
        start_time is not None
        and end_time is not None
        and ensure_utc(start_time) > ensure_utc(end_time)
    ):
        raise InvalidTimeRangeError("start_time must be earlier than or equal to end_time")
    items, total = EventQueryService(db).list_events(
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
    return {"items": items, "meta": {"limit": limit, "offset": offset, "total": total}}


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: UUID, db: Session = Depends(get_db)) -> EventRead:
    return EventQueryService(db).get_event(event_id)


@router.get("/{event_id}/analysis", response_model=EventAnalysisResponse)
def get_event_analysis(event_id: UUID, db: Session = Depends(get_db)) -> EventAnalysisResponse:
    return EventQueryService(db).get_analysis(event_id)
