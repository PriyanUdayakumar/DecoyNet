from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.events import EventHistoryItem, Severity


@dataclass(frozen=True)
class ScoreContribution:
    rule_id: str
    score: int
    reason: str


@dataclass(frozen=True)
class DetectionContext:
    recent_events: list[EventHistoryItem] = field(default_factory=list)
    device_known: bool = False


@dataclass(frozen=True)
class DetectionResult:
    risk_score: int
    severity: Severity
    rule_ids: list[str]
    explanation: str
    contributions: list[ScoreContribution]
    metadata: dict[str, Any] = field(default_factory=dict)
