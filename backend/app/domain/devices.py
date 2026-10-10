from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from typing import Any
from uuid import UUID


class DeviceStatus(str, Enum):
    REGISTERED = "registered"
    RECENTLY_SEEN = "recently_seen"
    STALE = "stale"
    DISABLED = "disabled"


APPROVED_DEVICE_METADATA_KEYS = {"location", "model", "role", "notes", "lab_label"}


@dataclass(frozen=True)
class DecoyDevice:
    device_id: UUID
    name: str
    device_type: str
    ip_address: IPv4Address | IPv6Address | None
    firmware_version: str | None
    registered_at: datetime
    last_seen_at: datetime | None
    status: DeviceStatus
    metadata: dict[str, Any] = field(default_factory=dict)


def calculate_device_status(
    *,
    last_seen_at: datetime | None,
    disabled: bool,
    now: datetime,
    threshold_seconds: int,
) -> DeviceStatus:
    if disabled:
        return DeviceStatus.DISABLED
    if last_seen_at is None:
        return DeviceStatus.REGISTERED
    if now - last_seen_at <= timedelta(seconds=threshold_seconds):
        return DeviceStatus.RECENTLY_SEEN
    return DeviceStatus.STALE
