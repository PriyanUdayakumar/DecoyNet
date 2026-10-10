# DecoyNet Architecture

## Overview

DecoyNet is a modular monolith FastAPI backend designed for IoT decoy event ingestion, threat detection, and dashboard reporting. The architecture enforces strict module boundaries to keep the system testable, maintainable, and ready for future enhancements (e.g., ML-based detection, PostgreSQL migration).

## Module Boundaries

### API Layer (`app/api/`)

- **Responsibility**: HTTP request/response handling only
- **Rules**:
  - Routes must not contain business logic
  - Validate request schemas and return response schemas
  - Delegate all work to services via dependency injection
- **Files**: `v1/health.py`, `v1/events.py`, `v1/devices.py`, `v1/dashboard.py`, `v1/discovery.py`, `v1/demo.py`

### Service Layer (`app/services/`)

- **Responsibility**: Orchestration, transaction boundaries, workflow logic
- **Rules**:
  - Own database commits/rollbacks
  - Use repositories for data access
  - Accept domain objects, return domain/response objects
- **Files**: `event_ingestion_service.py`, `event_query_service.py`, `device_service.py`, `dashboard_service.py`, `discovery_service.py`, `demo_service.py`

### Repository Layer (`app/db/repositories/`)

- **Responsibility**: All SQLAlchemy ORM queries
- **Rules**:
  - Never expose ORM models directly as API responses
  - Never commit; services own transaction boundaries
  - Provide CRUD, filtering, pagination, aggregation
- **Files**: `event_repository.py`, `device_repository.py`, `discovery_repository.py`

### Domain Layer (`app/domain/`)

- **Responsibility**: Framework-free business concepts
- **Rules**:
  - No FastAPI, SQLAlchemy, or Pydantic imports
  - Pure Python dataclasses and enums
  - Defines normalized event, device, detection contexts
- **Files**: `events.py`, `devices.py`, `discovery.py`, `detection.py`

### Detection Layer (`app/detection/`)

- **Responsibility**: Replaceable threat detection engine
- **Rules**:
  - Independent of FastAPI, SQLAlchemy, Pydantic request objects
  - Accept normalized domain events and context
  - Return structured detection results with rule contributions
  - Rules are independently configurable and unit-testable
- **Files**: `interfaces.py`, `rule_engine.py`, `rules.py`, `scoring.py`

### Schemas Layer (`app/schemas/`)

- **Responsibility**: Pydantic request/response models only
- **Rules**:
  - Input validation with detailed error messages
  - Output serialization with `from_attributes=True`
  - Separate request and response models
- **Files**: `events.py`, `devices.py`, `discovery.py`, `dashboard.py`, `common.py`

### Integrations Layer (`app/integrations/`)

- **Responsibility**: External system adapters
- **Rules**:
  - ESP32 adapter is thin; translates external payload to normalized event
  - Simulator generates deterministic demo events through the ingestion service
- **Files**: `esp32/event_adapter.py`, `simulator/event_generator.py`

## Data Flow

### Event Ingestion

1. Client POSTs to `/api/v1/events`
2. API validates `EventIngestRequest` schema
3. Service normalizes, checks idempotency, retrieves context
4. Detection engine analyzes event (returns `DetectionResult`)
5. Service creates event and persists detection result in one transaction
6. Service commits or rolls back; returns stable `EventIngestResponse`

### Detection Context

The event service fetches recent events for the same source IP via the event repository and passes them as a `DetectionContext` to the detection engine. This allows rules like "repeated login attempts" to work without coupling the detection engine to database details.

### Discovery Safety

1. Client requests discovery job
2. Service validates `DISCOVERY_ENABLED` flag
3. Service validates target CIDR against `AUTHORIZED_DISCOVERY_CIDRS` allowlist
4. If validation fails, reject without scanning
5. If allowed, run bounded TCP connect probes with configured timeout
6. Store results and return job status

## Transaction Strategy

- Services own the transaction boundary
- Repositories never commit or roll back
- Repositories flush when they need generated IDs
- Event ingestion uses atomic commit: event + detection result persist together or not at all

## Future Extensibility

- **ML Detection**: Replace `RuleBasedDetectionEngine` with a scikit-learn model implementing the same interface, without changing routes or repositories
- **PostgreSQL Migration**: SQLAlchemy models use standard types compatible with PostgreSQL; Alembic migrations handle schema changes
- **Authentication**: Add middleware and dependency overrides for auth without changing service logic