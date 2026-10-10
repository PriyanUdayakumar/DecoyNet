from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.discovery import DiscoveryJobStatus, DiscoveryMethod
from app.utils.time import utc_now


class DiscoveryJobModel(Base):
    __tablename__ = "discovery_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    target_cidr: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=DiscoveryJobStatus.PENDING.value)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    host_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    hosts = relationship("DiscoveredHostModel", back_populates="job", cascade="all, delete-orphan")


class DiscoveredHostModel(Base):
    __tablename__ = "discovered_hosts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("discovery_jobs.id"), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    method: Mapped[str] = mapped_column(String(32), default=DiscoveryMethod.TCP_CONNECT.value)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(32), nullable=True)
    evidence: Mapped[str | None] = mapped_column(String(500), nullable=True)

    job = relationship("DiscoveryJobModel", back_populates="hosts")


Index("ix_discovery_jobs_requested_at", DiscoveryJobModel.requested_at)
Index("ix_discovered_hosts_ip_address", DiscoveredHostModel.ip_address)
