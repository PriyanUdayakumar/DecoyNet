from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from ipaddress import IPv4Address, IPv6Address
from typing import Any
from uuid import UUID


class TransportProtocol(str, Enum):
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    OTHER = "other"


class ApplicationProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SSH = "ssh"
    TELNET = "telnet"
    MQTT = "mqtt"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    PAGE_ACCESS = "page_access"
    LOGIN_ATTEMPT = "login_attempt"
    SENSITIVE_ENDPOINT_ACCESS = "sensitive_endpoint_access"
    UNUSUAL_ENDPOINT_ACCESS = "unusual_endpoint_access"
    PORT_PROBE = "port_probe"
    HEARTBEAT = "heartbeat"
    OTHER = "other"


class EventOrigin(str, Enum):
    SIMULATOR = "simulator"
    ESP32 = "esp32"
    AUTHORIZED_TEST = "authorized_test"


class ProcessingStatus(str, Enum):
    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class NormalizedSecurityEvent:
    source_event_id: str
    source_ip: IPv4Address | IPv6Address
    destination_ip: IPv4Address | IPv6Address
    transport_protocol: TransportProtocol
    destination_port: int
    application_protocol: ApplicationProtocol
    event_type: EventType
    event_timestamp: datetime
    received_timestamp: datetime
    origin: EventOrigin
    schema_version: int = 1
    device_id: UUID | None = None
    http_method: str | None = None
    request_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EventHistoryItem:
    source_ip: str
    request_path: str | None
    event_type: EventType
    event_timestamp: datetime
    risk_score: int
