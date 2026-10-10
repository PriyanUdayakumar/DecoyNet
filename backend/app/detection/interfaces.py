from __future__ import annotations

from typing import Protocol

from app.domain.detection import DetectionContext, DetectionResult, ScoreContribution
from app.domain.events import NormalizedSecurityEvent


class DetectionRule(Protocol):
    rule_id: str

    def evaluate(
        self,
        event: NormalizedSecurityEvent,
        context: DetectionContext,
    ) -> ScoreContribution | None: ...


class DetectionEngine(Protocol):
    def analyze(
        self,
        event: NormalizedSecurityEvent,
        context: DetectionContext,
    ) -> DetectionResult: ...
