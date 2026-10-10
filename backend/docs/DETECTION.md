# Detection Engine

## Overview

The detection engine is a replaceable component that analyzes normalized security events and returns structured detection results. It is designed to be independent of FastAPI, SQLAlchemy, and Pydantic request objects, making it testable in isolation and extensible for future ML-based detection.

## Interface

The detection engine accepts:
- A normalized `NormalizedSecurityEvent` domain object
- A `DetectionContext` containing recent event history for context

It returns a `DetectionResult` containing:
- `risk_score`: Integer 0-100
- `severity`: One of info, low, medium, high, critical
- `rule_ids`: List of triggered rule identifiers
- `explanation`: Human-readable summary
- `contributions`: Per-rule score contributions

## Default Rules

### landing_page_access

**Trigger**: Ordinary decoy landing page access (`/` or `/index.html`)
**Score**: +5
**Severity**: info

This rule identifies benign traffic to the decoy's landing page.

### sensitive_endpoint_access

**Trigger**: Request to sensitive paths (`/admin`, `/config`, `/debug`, `/shell`, `/firmware`, `/api/keys`) or explicit sensitive endpoint access event type.
**Score**: +35
**Severity**: medium to high

This rule flags attempts to access administrative or configuration endpoints.

### repeated_login_attempts

**Trigger**: Multiple login attempts (≥3) from the same source IP within the context window.
**Score**: +30 (or +15 for first attempt)
**Severity**: medium to high

This rule identifies brute-force or credential-guessing behavior.

### multiple_unusual_endpoints

**Trigger**: Access to ≥3 unusual paths (`/.env`, `/wp-login.php`, `/phpmyadmin`, `/cgi-bin`, `/etc/passwd`) within the context window.
**Score**: +25
**Severity**: medium

This rule detects reconnaissance behavior targeting common vulnerabilities.

### suspicious_burst

**Trigger**: ≥8 events from the same source IP within the context window.
**Score**: +25
**Severity**: medium to high

This rule identifies high-volume automated scanning or attack scripts.

## Severity Thresholds

Configurable thresholds (default values):
- INFO: score < 20
- LOW: 20 ≤ score < 45
- MEDIUM: 45 ≤ score < 70
- HIGH: 70 ≤ score < 90
- CRITICAL: score ≥ 90

Thresholds are configured via:
- `SEVERITY_LOW_THRESHOLD` (default 20)
- `SEVERITY_MEDIUM_THRESHOLD` (default 45)
- `SEVERITY_HIGH_THRESHOLD` (default 70)

## Context Window

The detection engine receives recent event history for the source IP from the event repository. The context window is determined by the event query in the ingestion service (currently 300 seconds / 5 minutes).

## Scoring Strategy

- Scores are deterministic: identical events produce identical scores
- Scores are clamped to [0, 100]
- Multiple rules can contribute, summing to the final score
- The engine does not inflate scores from repeated processing of the same event

## Limitations

- Scores are indicators for investigation, not proof of malicious intent
- The system does not confirm attacks; it surfaces suspicious activity
- No ML model is trained in this phase; the interface supports future ML integration
- Rules are static; tuning requires configuration changes

## Future Extensibility

To add an ML-based detector:
1. Implement a class with the same `analyze(event, context) -> DetectionResult` interface
2. Replace `RuleBasedDetectionEngine` in the dependency injection
3. No changes to routes, services, or repositories required