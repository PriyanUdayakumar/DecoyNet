from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorDetail:
    code: str
    message: str


class DecoyNetError(Exception):
    status_code = 400
    code = "decoynet_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(DecoyNetError):
    status_code = 404
    code = "not_found"


class ConflictError(DecoyNetError):
    status_code = 409
    code = "conflict"


class DiscoveryNotAllowedError(DecoyNetError):
    status_code = 403
    code = "discovery_not_allowed"


class InvalidTimeRangeError(DecoyNetError):
    status_code = 422
    code = "invalid_time_range"


class DemoModeDisabledError(DecoyNetError):
    status_code = 403
    code = "demo_mode_disabled"
