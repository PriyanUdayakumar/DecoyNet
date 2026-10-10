from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.discovery import DiscoveryJobStatus, DiscoveryMethod


class DiscoveryJobCreate(BaseModel):
    target_cidr: str = Field(min_length=3, max_length=64, examples=["192.168.1.0/30"])


class DiscoveryJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_cidr: str
    status: DiscoveryJobStatus
    requested_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error: str | None
    host_count: int


class DiscoveredHostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    ip_address: str
    discovered_at: datetime
    method: DiscoveryMethod
    hostname: str | None
    mac_address: str | None
    evidence: str | None
