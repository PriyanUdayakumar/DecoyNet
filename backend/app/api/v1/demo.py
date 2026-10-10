from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_detection_engine, get_settings_dependency
from app.core.config import Settings
from app.detection.interfaces import DetectionEngine
from app.integrations.simulator.event_generator import SCENARIO_NAMES
from app.schemas.events import EventIngestResponse
from app.services.demo_service import DemoService

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/scenarios", response_model=list[str])
def list_scenarios() -> list[str]:
    return SCENARIO_NAMES


@router.post("/scenarios/{scenario_name}", response_model=list[EventIngestResponse])
def run_scenario(
    scenario_name: str,
    db: Session = Depends(get_db),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    settings: Settings = Depends(get_settings_dependency),
) -> list[EventIngestResponse]:
    return DemoService(db, detection_engine, demo_mode=settings.demo_mode).run_scenario(
        scenario_name
    )


@router.post("/reset")
def reset_demo(
    db: Session = Depends(get_db),
    detection_engine: DetectionEngine = Depends(get_detection_engine),
    settings: Settings = Depends(get_settings_dependency),
) -> dict[str, int]:
    return DemoService(db, detection_engine, demo_mode=settings.demo_mode).reset()
