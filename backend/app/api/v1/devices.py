from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_settings_dependency
from app.core.config import Settings
from app.schemas.devices import DeviceCreate, DeviceRead, DeviceUpdate
from app.services.device_service import DeviceService
from app.services.event_query_service import EventQueryService

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("", response_model=DeviceRead, status_code=201)
def create_device(
    request: DeviceCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> DeviceRead:
    return DeviceService(
        db, last_seen_threshold_seconds=settings.device_last_seen_threshold_seconds
    ).register(request)


@router.get("")
def list_devices(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> dict[str, object]:
    items, total = DeviceService(
        db, last_seen_threshold_seconds=settings.device_last_seen_threshold_seconds
    ).list_devices(limit=limit, offset=offset)
    return {"items": items, "meta": {"limit": limit, "offset": offset, "total": total}}


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(
    device_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> DeviceRead:
    return DeviceService(
        db, last_seen_threshold_seconds=settings.device_last_seen_threshold_seconds
    ).get_device(device_id)


@router.patch("/{device_id}", response_model=DeviceRead)
def update_device(
    device_id: UUID,
    request: DeviceUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> DeviceRead:
    return DeviceService(
        db, last_seen_threshold_seconds=settings.device_last_seen_threshold_seconds
    ).update_device(device_id, request)


@router.get("/{device_id}/events")
def get_device_events(
    device_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    items, total = EventQueryService(db).events_for_device(
        device_id=device_id, limit=limit, offset=offset
    )
    return {"items": items, "meta": {"limit": limit, "offset": offset, "total": total}}
