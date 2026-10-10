from __future__ import annotations

from typing import Any

SENSITIVE_METADATA_KEYS = {
    "authorization",
    "cookie",
    "password",
    "passwd",
    "secret",
    "session",
    "session_token",
    "token",
    "x-api-key",
}
MAX_METADATA_KEYS = 20
MAX_METADATA_VALUE_LENGTH = 300


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    sanitized: dict[str, Any] = {}
    for key, value in metadata.items():
        normalized_key = str(key).strip().lower()[:80]
        if not normalized_key or normalized_key in SENSITIVE_METADATA_KEYS:
            continue
        if len(sanitized) >= MAX_METADATA_KEYS:
            break
        if isinstance(value, str):
            sanitized[normalized_key] = value[:MAX_METADATA_VALUE_LENGTH]
        elif isinstance(value, int | float | bool) or value is None:
            sanitized[normalized_key] = value
        else:
            sanitized[normalized_key] = str(value)[:MAX_METADATA_VALUE_LENGTH]
    return sanitized
