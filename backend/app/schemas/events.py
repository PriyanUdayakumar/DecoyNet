from __future__ import annotations

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.events import (
    ApplicationProtocol,
    EventOrigin,
    EventType,
    ProcessingStatus,
    Severity,
    TransportProtocol,
)
from app.utils.time import ensure_utc


class EventIngestRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "schema_version": 1,
                "source_event_id": "sim-login-001",
                "device_id": None,
                "source_ip": "192.168.1.50",
                "destination_ip": "192.168.1.20",
                "transport_protocol": "tcp",
                "destination_port": 80,
                "application_protocol": "http",
                "http_method": "POST",
                "request_path": "/login",
                "event_type": "login_attempt",
                "event_timestamp": "2026-10-09T12:00:00Z",
                "origin": "simulator",
                "metadata": {"username": "admin", "result": "failed"},
            }
        }
    )

    schema_version: int = Field(default=1, ge=1, le=1)
    source_event_id: str = Field(min_length=1, max_length=128)
    device_id: UUID | None = None
    source_ip: IPv4Address | IPv6Address
    destination_ip: IPv4Address | IPv6Address
    transport_protocol: TransportProtocol
    destination_port: int = Field(ge=1, le=65535)
    application_protocol: ApplicationProtocol = ApplicationProtocol.UNKNOWN
    http_method: str | None = Field(default=None, min_length=1, max_length=12)
    request_path: str | None = Field(default=None, max_length=512)
    event_type: EventType
    event_timestamp: datetime
    origin: EventOrigin
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("http_method")
    @classmethod
    def normalize_method(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("request_path")
    @classmethod
    def validate_path(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.startswith("/"):
            raise ValueError("request_path must start with /")
        return value


class EventIngestResponse(BaseModel):
    event_id: UUID
    duplicate: bool
    risk_score: int = Field(ge=0, le=100)
    severity: Severity
    processing_status: ProcessingStatus
    explanation: str


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_event_id: str
    device_id: UUID | None
    source_ip: str
    destination_ip: str
    transport_protocol: TransportProtocol
    destination_port: int
    application_protocol: ApplicationProtocol
    http_method: str | None
    request_path: str | None
    event_type: EventType
    event_timestamp: datetime
    received_timestamp: datetime
    risk_score: int
    severity: Severity
    detection_rule_ids: list[str]
    explanation: str
    origin: EventOrigin
    metadata: dict[str, Any]
    processing_status: ProcessingStatus


class EventAnalysisResponse(BaseModel):
    event_id: UUID
    risk_score: int
    severity: Severity
    detection_rule_ids: list[str]
    explanation: str
    score_contributions: list[dict[str, Any]]
