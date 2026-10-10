from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DiscoveryJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class DiscoveryMethod(str, Enum):
    TCP_CONNECT = "tcp_connect"
    MANUAL_OBSERVATION = "manual_observation"


@dataclass(frozen=True)
class DiscoveryTargetValidation:
    allowed: bool
    reason: str
    host_count: int = 0


@dataclass(frozen=True)
class DiscoveredHost:
    ip_address: str
    discovered_at: datetime
    method: DiscoveryMethod
    hostname: str | None = None
    mac_address: str | None = None
    evidence: str | None = None
