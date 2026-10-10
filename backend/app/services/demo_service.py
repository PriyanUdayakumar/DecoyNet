from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import DemoModeDisabledError, NotFoundError
from app.db.repositories.event_repository import EventRepository
from app.detection.interfaces import DetectionEngine
from app.integrations.simulator.event_generator import SCENARIO_NAMES, SimulatorEventGenerator
from app.schemas.events import EventIngestResponse
from app.services.event_ingestion_service import EventIngestionService


class DemoService:
    def __init__(
        self, session: Session, detection_engine: DetectionEngine, *, demo_mode: bool
    ) -> None:
        self.session = session
        self.demo_mode = demo_mode
        self.events = EventRepository(session)
        self.generator = SimulatorEventGenerator()
        self.ingestion = EventIngestionService(session, detection_engine)

    def run_scenario(self, scenario_name: str) -> list[EventIngestResponse]:
        if not self.demo_mode:
            raise DemoModeDisabledError("Demo mode is disabled")
        if scenario_name not in SCENARIO_NAMES:
            raise NotFoundError("Demo scenario not found")
        responses = []
        for event in self.generator.generate(scenario_name):
            responses.append(self.ingestion.ingest(event))
        return responses

    def reset(self) -> dict[str, int]:
        if not self.demo_mode:
            raise DemoModeDisabledError("Demo mode is disabled")
        deleted = self.events.delete_demo_events()
        self.session.commit()
        return {"deleted_events": deleted}
