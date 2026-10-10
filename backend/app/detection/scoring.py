from __future__ import annotations

from app.domain.events import Severity


def clamp_score(score: int) -> int:
    return max(0, min(100, score))


def severity_for_score(
    score: int,
    *,
    low_threshold: int = 20,
    medium_threshold: int = 45,
    high_threshold: int = 70,
) -> Severity:
    if score >= 90:
        return Severity.CRITICAL
    if score >= high_threshold:
        return Severity.HIGH
    if score >= medium_threshold:
        return Severity.MEDIUM
    if score >= low_threshold:
        return Severity.LOW
    return Severity.INFO
