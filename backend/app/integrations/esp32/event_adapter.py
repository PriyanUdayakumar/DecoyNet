from __future__ import annotations

from app.schemas.events import EventIngestRequest


def adapt_esp32_payload(payload: dict) -> EventIngestRequest:
    return EventIngestRequest.model_validate(payload)
