from __future__ import annotations

from dataclasses import dataclass

from app.domain.detection import DetectionContext, ScoreContribution
from app.domain.events import EventType, NormalizedSecurityEvent

SENSITIVE_PATH_PREFIXES = ("/admin", "/config", "/debug", "/shell", "/firmware", "/api/keys")
UNUSUAL_PATHS = ("/wp-login.php", "/.env", "/phpmyadmin", "/cgi-bin", "/etc/passwd")


@dataclass(frozen=True)
class LandingPageAccessRule:
    rule_id: str = "landing_page_access"

    def evaluate(
        self, event: NormalizedSecurityEvent, context: DetectionContext
    ) -> ScoreContribution | None:
        if event.event_type == EventType.PAGE_ACCESS and event.request_path in {"/", "/index.html"}:
            return ScoreContribution(
                self.rule_id, 5, "Ordinary decoy landing page access observed."
            )
        return None


@dataclass(frozen=True)
class SensitiveEndpointRule:
    rule_id: str = "sensitive_endpoint_access"

    def evaluate(
        self, event: NormalizedSecurityEvent, context: DetectionContext
    ) -> ScoreContribution | None:
        path = event.request_path or ""
        if event.event_type == EventType.SENSITIVE_ENDPOINT_ACCESS or path.startswith(
            SENSITIVE_PATH_PREFIXES
        ):
            return ScoreContribution(
                self.rule_id,
                35,
                "Request targeted a sensitive simulated endpoint.",
            )
        return None


@dataclass(frozen=True)
class RepeatedLoginAttemptsRule:
    threshold: int = 3
    rule_id: str = "repeated_login_attempts"

    def evaluate(
        self, event: NormalizedSecurityEvent, context: DetectionContext
    ) -> ScoreContribution | None:
        if event.event_type != EventType.LOGIN_ATTEMPT:
            return None
        previous_attempts = sum(
            1 for item in context.recent_events if item.event_type == EventType.LOGIN_ATTEMPT
        )
        if previous_attempts + 1 >= self.threshold:
            return ScoreContribution(
                self.rule_id,
                30,
                "Repeated login attempts from the same source in a short window.",
            )
        return ScoreContribution(
            self.rule_id, 15, "Login attempt recorded without storing credentials."
        )


@dataclass(frozen=True)
class MultipleUnusualEndpointsRule:
    threshold: int = 3
    rule_id: str = "multiple_unusual_endpoints"

    def evaluate(
        self, event: NormalizedSecurityEvent, context: DetectionContext
    ) -> ScoreContribution | None:
        paths = {item.request_path for item in context.recent_events if item.request_path}
        if event.request_path:
            paths.add(event.request_path)
        unusual_hits = [path for path in paths if path and path.startswith(UNUSUAL_PATHS)]
        if len(unusual_hits) >= self.threshold:
            return ScoreContribution(
                self.rule_id,
                25,
                "Multiple unusual endpoint paths were requested in a short window.",
            )
        return None


@dataclass(frozen=True)
class SuspiciousBurstRule:
    threshold: int = 8
    rule_id: str = "suspicious_burst"

    def evaluate(
        self, event: NormalizedSecurityEvent, context: DetectionContext
    ) -> ScoreContribution | None:
        if len(context.recent_events) + 1 >= self.threshold:
            return ScoreContribution(
                self.rule_id,
                25,
                "Burst of interactions from the same observed source IP.",
            )
        return None


def default_rules() -> list[
    LandingPageAccessRule
    | SensitiveEndpointRule
    | RepeatedLoginAttemptsRule
    | MultipleUnusualEndpointsRule
    | SuspiciousBurstRule
]:
    return [
        LandingPageAccessRule(),
        SensitiveEndpointRule(),
        RepeatedLoginAttemptsRule(),
        MultipleUnusualEndpointsRule(),
        SuspiciousBurstRule(),
    ]
