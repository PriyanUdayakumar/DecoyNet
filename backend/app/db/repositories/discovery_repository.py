from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.discovery import DiscoveredHostModel, DiscoveryJobModel


class DiscoveryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_job(self, *, target_cidr: str) -> DiscoveryJobModel:
        job = DiscoveryJobModel(target_cidr=target_cidr)
        self.session.add(job)
        self.session.flush()
        return job

    def get_job(self, job_id: UUID | str) -> DiscoveryJobModel | None:
        return self.session.get(DiscoveryJobModel, str(job_id))

    def list_hosts(self, *, limit: int, offset: int) -> list[DiscoveredHostModel]:
        return list(
            self.session.scalars(
                select(DiscoveredHostModel)
                .order_by(DiscoveredHostModel.discovered_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )

    def add_host(
        self,
        *,
        job_id: UUID | str,
        ip_address: str,
        method: str,
        hostname: str | None,
        mac_address: str | None,
        evidence: str | None,
    ) -> DiscoveredHostModel:
        host = DiscoveredHostModel(
            job_id=str(job_id),
            ip_address=ip_address,
            method=method,
            hostname=hostname,
            mac_address=mac_address,
            evidence=evidence,
        )
        self.session.add(host)
        self.session.flush()
        return host
