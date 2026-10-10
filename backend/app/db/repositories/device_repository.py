from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.device import DeviceModel
from app.domain.devices import DeviceStatus
from app.utils.time import utc_now


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        name: str,
        device_type: str,
        ip_address: str | None,
        firmware_version: str | None,
        metadata: dict,
    ) -> DeviceModel:
        device = DeviceModel(
            name=name,
            device_type=device_type,
            ip_address=ip_address,
            firmware_version=firmware_version,
            metadata_json=metadata,
            status=DeviceStatus.REGISTERED.value,
        )
        self.session.add(device)
        self.session.flush()
        return device

    def get(self, device_id: UUID | str) -> DeviceModel | None:
        return self.session.get(DeviceModel, str(device_id))

    def get_by_name(self, name: str) -> DeviceModel | None:
        # "name" is the device identifier for uniqueness; backing unique index ux_devices_name.
        return self.session.scalar(select(DeviceModel).where(DeviceModel.name == name))

    def list(self, *, limit: int, offset: int) -> list[DeviceModel]:
        return list(
            self.session.scalars(
                select(DeviceModel)
                .order_by(DeviceModel.registered_at.desc(), DeviceModel.id.asc())
                .limit(limit)
                .offset(offset)
            )
        )

    def update(self, device: DeviceModel, **values: object) -> DeviceModel:
        for key, value in values.items():
            if value is not None:
                setattr(device, key, value)
        self.session.flush()
        return device

    def mark_seen(self, device: DeviceModel) -> DeviceModel:
        device.last_seen_at = utc_now()
        self.session.flush()
        return device

    def count(self) -> int:
        return self.session.scalar(select(func.count(DeviceModel.id))) or 0
