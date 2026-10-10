from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.domain.events import ProcessingStatus, Severity
from app.utils.time import utc_now


class EventModel(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("origin", "source_event_id", name="uq_events_origin_source_event_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    source_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    device_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("devices.id"), nullable=True
    )
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    destination_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    transport_protocol: Mapped[str] = mapped_column(String(16), nullable=False)
    destination_port: Mapped[int] = mapped_column(Integer, nullable=False)
    application_protocol: Mapped[str] = mapped_column(String(32), nullable=False)
    http_method: Mapped[str | None] = mapped_column(String(12), nullable=True)
    request_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default=Severity.INFO.value, nullable=False)
    detection_rule_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(String(1000), default="No detection rules triggered.")
    origin: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    score_contributions: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    processing_status: Mapped[str] = mapped_column(
        String(32), default=ProcessingStatus.PROCESSED.value, nullable=False
    )

    device = relationship("DeviceModel", back_populates="events")


Index("ix_events_device_id", EventModel.device_id)
Index("ix_events_source_ip", EventModel.source_ip)
Index("ix_events_timestamp", EventModel.event_timestamp)
Index("ix_events_severity", EventModel.severity)
Index("ix_events_event_type", EventModel.event_type)
Index("ix_events_origin", EventModel.origin)
