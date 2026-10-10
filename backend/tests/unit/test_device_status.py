from __future__ import annotations

from datetime import timedelta

from app.domain.devices import DeviceStatus, calculate_device_status
from app.utils.time import utc_now


def test_device_status_policy() -> None:
    now = utc_now()
    assert (
        calculate_device_status(last_seen_at=None, disabled=False, now=now, threshold_seconds=300)
        == DeviceStatus.REGISTERED
    )
    assert (
        calculate_device_status(
            last_seen_at=now - timedelta(seconds=20), disabled=False, now=now, threshold_seconds=300
        )
        == DeviceStatus.RECENTLY_SEEN
    )
    assert (
        calculate_device_status(
            last_seen_at=now - timedelta(seconds=600),
            disabled=False,
            now=now,
            threshold_seconds=300,
        )
        == DeviceStatus.STALE
    )
    assert (
        calculate_device_status(last_seen_at=now, disabled=True, now=now, threshold_seconds=300)
        == DeviceStatus.DISABLED
    )
