# DecoyNet Backend

Modular FastAPI backend for IoT decoy cyber-threat event ingestion, detection, and dashboard visualization.

## Quick Start (Ubuntu)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | local | Environment name |
| `DATABASE_URL` | sqlite:///./decoynet.db | SQLite database path |
| `LOG_LEVEL` | INFO | Logging level |
| `DEMO_MODE` | false | Enable demo scenario generation |
| `DISCOVERY_ENABLED` | false | Enable network discovery |
| `AUTHORIZED_DISCOVERY_CIDRS` | (empty) | Allowlist for discovery targets |
| `DISCOVERY_TIMEOUT_SECONDS` | 1.0 | Per-host probe timeout |
| `SEVERITY_LOW_THRESHOLD` | 20 | Minimum score for LOW severity |
| `SEVERITY_MEDIUM_THRESHOLD` | 45 | Minimum score for MEDIUM severity |
| `SEVERITY_HIGH_THRESHOLD` | 70 | Minimum score for HIGH severity |

## Running Tests

```bash
cd backend
pytest
```

## Running Lint

```bash
cd backend
ruff check .
ruff format --check .
```

## API Documentation

After starting the server, visit:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Demo Mode

To run demo scenarios:

1. Set `DEMO_MODE=true` in `.env`
2. Start the server
3. Run a scenario:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/demo/scenarios/sensitive_endpoint_access
```

Available scenarios:
- `ordinary_page_access`
- `sensitive_endpoint_access`
- `repeated_login_attempts`
- `unusual_endpoint_burst`

Reset demo data:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/demo/reset
```

## Discovery Safety

Network discovery is **disabled by default**. To enable:

1. Set `DISCOVERY_ENABLED=true`
2. Set `AUTHORIZED_DISCOVERY_CIDRS` to comma-separated CIDR ranges (e.g., `192.168.1.0/24`)
3. Restart the server

Discovery requests to targets outside the allowlist are rejected.

## Security Limitations

- This backend runs unauthenticated.
- Intended for a **trusted lab network only**.
- Do not expose to untrusted networks without adding authentication, rate limiting, and request protections.
- Device metadata must use approved keys only (`location`, `model`, `role`, `notes`, `lab_label`).
- Login attempt events are recorded without storing submitted passwords.

## Project Structure

```
backend/
  app/
    api/          # FastAPI routes (thin, delegate to services)
    core/         # Config, logging, exceptions, security helpers
    db/           # SQLAlchemy models, repositories, session
    detection/    # Replaceable detection engine interface and rules
    domain/       # Framework-free domain objects and enums
    schemas/      # Pydantic request/response schemas
    services/     # Business logic, orchestration, transactions
    integrations/ # ESP32 adapter, simulator event generator
    utils/        # Time utilities
  migrations/     # Alembic schema migrations
  tests/          # Unit and API tests
```