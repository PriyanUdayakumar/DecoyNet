from __future__ import annotations

from app.core.config import Settings
from app.detection.interfaces import DetectionRule
from app.detection.rules import default_rules
from app.detection.scoring import clamp_score, severity_for_score
from app.domain.detection import DetectionContext, DetectionResult
from app.domain.events import NormalizedSecurityEvent, Severity


class RuleBasedDetectionEngine:
    def __init__(self, settings: Settings, rules: list[DetectionRule] | None = None) -> None:
        self.settings = settings
        self.rules = rules or default_rules()

    def analyze(
        self,
        event: NormalizedSecurityEvent,
        context: DetectionContext,
    ) -> DetectionResult:
        contributions = [
            contribution
            for rule in self.rules
            if (contribution := rule.evaluate(event, context)) is not None
        ]
        risk_score = clamp_score(sum(contribution.score for contribution in contributions))
        severity = severity_for_score(
            risk_score,
            low_threshold=self.settings.severity_low_threshold,
            medium_threshold=self.settings.severity_medium_threshold,
            high_threshold=self.settings.severity_high_threshold,
        )
        rule_ids = [contribution.rule_id for contribution in contributions]
        explanation = self._explanation(contributions, severity)
        return DetectionResult(
            risk_score=risk_score,
            severity=severity,
            rule_ids=rule_ids,
            explanation=explanation,
            contributions=contributions,
        )

    def _explanation(self, contributions, severity: Severity) -> str:  # type: ignore[no-untyped-def]
        if not contributions:
            return "No detection rules triggered. Treat this as observed decoy telemetry only."
        reasons = " ".join(contribution.reason for contribution in contributions)
        return f"{severity.value.title()} risk indicator based on rule evidence. {reasons}"
