from __future__ import annotations

import socket
from ipaddress import ip_network
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import DiscoveryNotAllowedError, NotFoundError
from app.db.repositories.discovery_repository import DiscoveryRepository
from app.domain.discovery import DiscoveryJobStatus, DiscoveryMethod
from app.schemas.discovery import DiscoveredHostRead, DiscoveryJobRead
from app.utils.time import utc_now


class DiscoveryService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.discovery = DiscoveryRepository(session)

    def start_job(self, *, target_cidr: str) -> DiscoveryJobRead:
        self._validate_target(target_cidr)
        job = self.discovery.create_job(target_cidr=target_cidr)
        job.status = DiscoveryJobStatus.RUNNING.value
        job.started_at = utc_now()
        network = ip_network(target_cidr, strict=False)
        hosts = list(network.hosts())[: self.settings.discovery_max_hosts]
        evidence = "TCP connection accepted on port 80 or 443 during bounded lab discovery."
        for host in hosts:
            if self._tcp_probe(str(host)):
                self.discovery.add_host(
                    job_id=job.id,
                    ip_address=str(host),
                    method=DiscoveryMethod.TCP_CONNECT.value,
                    hostname=None,
                    mac_address=None,
                    evidence=evidence,
                )
        job.host_count = len(job.hosts)
        job.status = DiscoveryJobStatus.COMPLETED.value
        job.completed_at = utc_now()
        self.session.commit()
        return self._job_read(job)

    def get_job(self, job_id: UUID) -> DiscoveryJobRead:
        job = self.discovery.get_job(job_id)
        if job is None:
            raise NotFoundError("Discovery job not found")
        return self._job_read(job)

    def list_hosts(self, *, limit: int, offset: int) -> list[DiscoveredHostRead]:
        return [
            self._host_read(host) for host in self.discovery.list_hosts(limit=limit, offset=offset)
        ]

    def _validate_target(self, target_cidr: str) -> None:
        if not self.settings.discovery_enabled:
            raise DiscoveryNotAllowedError("Discovery is disabled by configuration")
        try:
            target = ip_network(target_cidr, strict=False)
        except ValueError as exc:
            raise DiscoveryNotAllowedError("Invalid discovery target") from exc
        if target.num_addresses > self.settings.discovery_max_hosts + 2:
            raise DiscoveryNotAllowedError("Discovery target exceeds configured host limit")
        allowlist = [
            ip_network(cidr, strict=False) for cidr in self.settings.authorized_discovery_cidrs
        ]
        if not allowlist or not any(target.subnet_of(allowed) for allowed in allowlist):
            raise DiscoveryNotAllowedError("Discovery target is outside authorized CIDR allowlist")

    def _tcp_probe(self, host: str) -> bool:
        for port in (80, 443):
            try:
                with socket.create_connection(
                    (host, port), timeout=self.settings.discovery_timeout_seconds
                ):
                    return True
            except OSError:
                continue
        return False

    def _job_read(self, job) -> DiscoveryJobRead:  # type: ignore[no-untyped-def]
        return DiscoveryJobRead(
            id=UUID(job.id),
            target_cidr=job.target_cidr,
            status=DiscoveryJobStatus(job.status),
            requested_at=job.requested_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error=job.error,
            host_count=job.host_count,
        )

    def _host_read(self, host) -> DiscoveredHostRead:  # type: ignore[no-untyped-def]
        return DiscoveredHostRead(
            id=UUID(host.id),
            job_id=UUID(host.job_id),
            ip_address=host.ip_address,
            discovered_at=host.discovered_at,
            method=DiscoveryMethod(host.method),
            hostname=host.hostname,
            mac_address=host.mac_address,
            evidence=host.evidence,
        )
