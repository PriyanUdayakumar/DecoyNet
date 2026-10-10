from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import dashboard, demo, devices, discovery, events, health

router = APIRouter()
router.include_router(health.router)
router.include_router(events.router)
router.include_router(devices.router)
router.include_router(dashboard.router)
router.include_router(discovery.router)
router.include_router(demo.router)
