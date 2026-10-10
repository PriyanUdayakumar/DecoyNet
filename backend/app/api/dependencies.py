from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.detection.rule_engine import RuleBasedDetectionEngine


def get_settings_dependency() -> Settings:
    return get_settings()


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_detection_engine(
    settings: Settings = Depends(get_settings_dependency),
) -> RuleBasedDetectionEngine:
    return RuleBasedDetectionEngine(settings)
