from __future__ import annotations

from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.devices import DeviceStatus


class DeviceCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Lab ESP32 camera decoy",
                "device_type": "camera",
                "ip_address": "192.168.1.20",
                "firmware_version": "sim-1.0.0",
                "metadata": {"location": "lab bench", "role": "decoy"},
            }
        }
    )

    name: str = Field(min_length=1, max_length=120)
    device_type: str = Field(min_length=1, max_length=80)
    ip_address: IPv4Address | IPv6Address | None = None
    firmware_version: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    device_type: str | None = Field(default=None, min_length=1, max_length=80)
    ip_address: IPv4Address | IPv6Address | None = None
    firmware_version: str | None = Field(default=None, max_length=80)
    disabled: bool | None = None
    metadata: dict[str, Any] | None = None


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    device_type: str
    ip_address: str | None
    firmware_version: str | None
    registered_at: datetime
    last_seen_at: datetime | None
    status: DeviceStatus
    metadata: dict[str, Any]
