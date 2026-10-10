# DecoyNet API Reference

## Base URL

```
http://127.0.0.1:8000/api/v1
```

## Common Headers

| Header | Value |
|--------|-------|
| Content-Type | application/json |
| X-Correlation-ID | (optional) Request correlation ID for logging |

## Endpoints

### Health

#### GET /health

Returns application status.

**Response 200**
```json
{
  "status": "ok",
  "app": "DecoyNet",
  "environment": "local"
}
```

#### GET /health/ready

Returns readiness with database connectivity check.

**Response 200**
```json
{
  "status": "ready",
  "database": "ok"
}
```

---

### Events

#### POST /events

Ingest a security event.

**Request Body**
```json
{
  "schema_version": 1,
  "source_event_id": "evt-001",
  "device_id": null,
  "source_ip": "192.168.1.50",
  "destination_ip": "192.168.1.20",
  "transport_protocol": "tcp",
  "destination_port": 80,
  "application_protocol": "http",
  "http_method": "POST",
  "request_path": "/login",
  "event_type": "login_attempt",
  "event_timestamp": "2026-10-09T12:00:00Z",
  "origin": "simulator",
  "metadata": {"username": "admin", "result": "failed"}
}
```

**Response 201**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "duplicate": false,
  "risk_score": 45,
  "severity": "medium",
  "processing_status": "processed",
  "explanation": "Medium risk indicator based on rule evidence. Repeated login attempts from the same observed source in a short window."
}
```

#### GET /events

List events with pagination and filters.

**Query Parameters**
- `limit` (int, 1-200, default 50)
- `offset` (int, >=0, default 0)
- `severity` (enum: info, low, medium, high, critical)
- `event_type` (enum: page_access, login_attempt, sensitive_endpoint_access, ...)
- `device_id` (UUID)
- `source_ip` (string)
- `origin` (enum: simulator, esp32, authorized_test)
- `start_time` (ISO 8601)
- `end_time` (ISO 8601)

**Response 200**
```json
{
  "items": [...],
  "meta": {"limit": 50, "offset": 0, "total": 1}
}
```

#### GET /events/{event_id}

Get a single event by ID.

#### GET /events/{event_id}/analysis

Get detection analysis for an event.

---

### Devices

#### POST /devices

Register a new decoy device.

**Request Body**
```json
{
  "name": "lab-camera-1",
  "device_type": "camera",
  "ip_address": "192.168.1.20",
  "firmware_version": "sim-1.0.0",
  "metadata": {"location": "lab bench", "role": "decoy"}
}
```

**Response 201**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "lab-camera-1",
  "device_type": "camera",
  "ip_address": "192.168.1.20",
  "firmware_version": "sim-1.0.0",
  "registered_at": "2026-10-09T12:00:00Z",
  "last_seen_at": null,
  "status": "registered",
  "metadata": {"location": "lab bench"}
}
```

#### GET /devices

List devices.

#### GET /devices/{device_id}

Get device by ID.

#### PATCH /devices/{device_id}

Update device fields.

#### GET /devices/{device_id}/events

Get events for a specific device.

---

### Dashboard

#### GET /dashboard/summary

Get aggregated dashboard metrics.

**Response 200**
```json
{
  "total_events": 42,
  "unique_events": 38,
  "high_risk_events": 7,
  "registered_devices": 3,
  "recently_seen_devices": 2,
  "severity_counts": {"info": 10, "low": 15, "medium": 10, "high": 5, "critical": 2},
  "origin_counts": {"simulator": 40, "esp32": 2}
}
```

#### GET /dashboard/timeline

Get event timeline (bucketed by hour).

**Query Parameters**
- `hours` (int, 1-168, default 24)

#### GET /dashboard/recent-alerts

Get recent high-risk events.

**Query Parameters**
- `limit` (int, 1-100, default 20)

---

### Discovery

#### POST /discovery/jobs

Start a discovery job (requires `DISCOVERY_ENABLED=true` and authorized CIDR).

**Request Body**
```json
{
  "target_cidr": "192.168.1.0/30"
}
```

**Response 201**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "target_cidr": "192.168.1.0/30",
  "status": "completed",
  "requested_at": "2026-10-09T12:00:00Z",
  "started_at": "2026-10-09T12:00:01Z",
  "completed_at": "2026-10-09T12:00:03Z",
  "error": null,
  "host_count": 2
}
```

#### GET /discovery/jobs/{job_id}

Get discovery job status.

#### GET /discovery/hosts

List discovered hosts.

---

### Demo

#### GET /demo/scenarios

List available demo scenarios.

**Response 200**
```json
["ordinary_page_access", "sensitive_endpoint_access", "repeated_login_attempts", "unusual_endpoint_burst"]
```

#### POST /demo/scenarios/{scenario_name}

Run a demo scenario (requires `DEMO_MODE=true`).

#### POST /demo/reset

Reset demo data (requires `DEMO_MODE=true`).

**Response 200**
```json
{"deleted_events": 5}
```

---

## Error Responses

### 400 Bad Request
```json
{"error": "decoynet_error", "message": "Human-readable error"}
```

### 403 Forbidden
```json
{"error": "discovery_not_allowed", "message": "Discovery is disabled by configuration"}
```
```json
{"error": "demo_mode_disabled", "message": "Demo mode is disabled"}
```

### 404 Not Found
```json
{"error": "not_found", "message": "Event not found"}
```

### 409 Conflict
```json
{"error": "conflict", "message": "A device with this name is already registered"}
```

### 500 Internal Server Error
```json
{"error": "internal_server_error", "message": "Unexpected server error"}
```
## Quick Reference (curl)

### Health and readiness

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/health/ready
```

### Ingest an event

```bash
curl -X POST http://127.0.0.1:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "schema_version": 1,
    "source_event_id": "evt-001",
    "source_ip": "192.168.1.50",
    "destination_ip": "192.168.1.20",
    "transport_protocol": "tcp",
    "destination_port": 80,
    "application_protocol": "http",
    "http_method": "GET",
    "request_path": "/admin/config",
    "event_type": "sensitive_endpoint_access",
    "event_timestamp": "2026-10-09T12:00:00Z",
    "origin": "simulator",
    "metadata": {"username": "admin"}
  }'
```

### List and filter events

```bash
curl "http://127.0.0.1:8000/api/v1/events?severity=medium&limit=10&offset=0"
curl http://127.0.0.1:8000/api/v1/events/{event_id}
curl http://127.0.0.1:8000/api/v1/events/{event_id}/analysis
```

### Register a device

```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "lab-camera-1",
    "device_type": "camera",
    "ip_address": "192.168.1.20",
    "firmware_version": "sim-1.0.0",
    "metadata": {"location": "lab bench", "role": "decoy"}
  }'
```

### Device queries and updates

```bash
curl http://127.0.0.1:8000/api/v1/devices
curl http://127.0.0.1:8000/api/v1/devices/{device_id}
curl -X PATCH http://127.0.0.1:8000/api/v1/devices/{device_id} \
  -H "Content-Type: application/json" \
  -d '{"firmware_version": "sim-1.0.1"}'
curl http://127.0.0.1:8000/api/v1/devices/{device_id}/events
```

### Dashboard

```bash
curl http://127.0.0.1:8000/api/v1/dashboard/summary
curl "http://127.0.0.1:8000/api/v1/dashboard/timeline?hours=24"
curl "http://127.0.0.1:8000/api/v1/dashboard/recent-alerts?limit=20"
```

### Discovery (disabled by default)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/discovery/jobs \
  -H "Content-Type: application/json" \
  -d '{"target_cidr": "192.168.1.0/30"}'
curl http://127.0.0.1:8000/api/v1/discovery/jobs/{job_id}
curl "http://127.0.0.1:8000/api/v1/discovery/hosts?limit=50&offset=0"
```

### Demo mode (requires DEMO_MODE=true)

```bash
curl http://127.0.0.1:8000/api/v1/demo/scenarios
curl -X POST http://127.0.0.1:8000/api/v1/demo/scenarios/sensitive_endpoint_access
curl -X POST http://127.0.0.1:8000/api/v1/demo/reset
```
