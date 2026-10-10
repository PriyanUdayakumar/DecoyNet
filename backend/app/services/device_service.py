from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import sanitize_metadata
from app.db.repositories.device_repository import DeviceRepository
from app.domain.devices import APPROVED_DEVICE_METADATA_KEYS, calculate_device_status
from app.schemas.devices import DeviceCreate, DeviceRead, DeviceUpdate
from app.services.mappers import device_to_read
from app.utils.time import utc_now


class DeviceService:
    def __init__(self, session: Session, *, last_seen_threshold_seconds: int) -> None:
        self.session = session
        self.devices = DeviceRepository(session)
        self.last_seen_threshold_seconds = last_seen_threshold_seconds

    def register(self, request: DeviceCreate) -> DeviceRead:
        if self.devices.get_by_name(request.name):
            raise ConflictError("A device with this name is already registered")
        try:
            device = self.devices.create(
                name=request.name,
                device_type=request.device_type,
                ip_address=str(request.ip_address) if request.ip_address else None,
                firmware_version=request.firmware_version,
                metadata=self._device_metadata(request.metadata),
            )
            self._refresh_status(device)
            self.session.commit()
        except IntegrityError as exc:
            # Backstop for the unique index ux_devices_name under concurrent registration.
            self.session.rollback()
            raise ConflictError("A device with this name is already registered") from exc
        return device_to_read(device)

    def list_devices(self, *, limit: int, offset: int) -> tuple[list[DeviceRead], int]:
        devices = self.devices.list(limit=limit, offset=offset)
        total = self.devices.count()
        for device in devices:
            self._refresh_status(device)
        self.session.commit()
        return [device_to_read(device) for device in devices], total

    def get_device(self, device_id: UUID) -> DeviceRead:
        device = self.devices.get(device_id)
        if device is None:
            raise NotFoundError("Device not found")
        self._refresh_status(device)
        self.session.commit()
        return device_to_read(device)

    def update_device(self, device_id: UUID, request: DeviceUpdate) -> DeviceRead:
        device = self.devices.get(device_id)
        if device is None:
            raise NotFoundError("Device not found")
        values = request.model_dump(exclude_unset=True)
        if "ip_address" in values and values["ip_address"] is not None:
            values["ip_address"] = str(values["ip_address"])
        if "metadata" in values and values["metadata"] is not None:
            values["metadata_json"] = self._device_metadata(values.pop("metadata"))
        self.devices.update(device, **values)
        self._refresh_status(device)
        self.session.commit()
        return device_to_read(device)

    def _refresh_status(self, device) -> None:  # type: ignore[no-untyped-def]
        device.status = calculate_device_status(
            last_seen_at=device.last_seen_at,
            disabled=device.disabled,
            now=utc_now(),
            threshold_seconds=self.last_seen_threshold_seconds,
        ).value

    def _device_metadata(self, metadata: dict) -> dict:
        sanitized = sanitize_metadata(metadata)
        return {
            key: value for key, value in sanitized.items() if key in APPROVED_DEVICE_METADATA_KEYS
        }
