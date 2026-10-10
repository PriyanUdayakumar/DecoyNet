from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_settings_dependency
from app.core.config import Settings
from app.schemas.discovery import DiscoveredHostRead, DiscoveryJobCreate, DiscoveryJobRead
from app.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post("/jobs", response_model=DiscoveryJobRead, status_code=201)
def start_discovery_job(
    request: DiscoveryJobCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> DiscoveryJobRead:
    return DiscoveryService(db, settings).start_job(target_cidr=request.target_cidr)


@router.get("/jobs/{job_id}", response_model=DiscoveryJobRead)
def get_discovery_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> DiscoveryJobRead:
    return DiscoveryService(db, settings).get_job(job_id)


@router.get("/hosts", response_model=list[DiscoveredHostRead])
def list_discovered_hosts(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
) -> list[DiscoveredHostRead]:
    return DiscoveryService(db, settings).list_hosts(limit=limit, offset=offset)
