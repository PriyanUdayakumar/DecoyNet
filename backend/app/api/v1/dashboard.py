from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.dashboard import DashboardSummary, RecentAlert, TimelinePoint
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    return DashboardService(db).summary()


@router.get("/timeline", response_model=list[TimelinePoint])
def get_timeline(
    hours: int = Query(default=24, ge=1, le=168), db: Session = Depends(get_db)
) -> list[TimelinePoint]:
    return DashboardService(db).timeline(hours=hours)


@router.get("/recent-alerts", response_model=list[RecentAlert])
def get_recent_alerts(
    limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)
) -> list[RecentAlert]:
    return DashboardService(db).recent_alerts(limit=limit)
