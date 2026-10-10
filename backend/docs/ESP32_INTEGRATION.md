# ESP32 Integration Guide

## Overview

Future ESP32-S3 decoy nodes will send security events to this backend via HTTP POST. This document specifies the expected payload format and request structure.

## HTTP Request

### Endpoint

```
POST http://<backend-host>:8000/api/v1/events
```

### Headers

| Header | Value |
|--------|-------|
| Content-Type | application/json |
| X-Correlation-ID | (optional) Request correlation ID |

### Payload Schema

```json
{
  "schema_version": 1,
  "source_event_id": "esp32-001-20261009T120000Z",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_ip": "192.168.1.50",
  "destination_ip": "192.168.1.20",
  "transport_protocol": "tcp",
  "destination_port": 80,
  "application_protocol": "http",
  "http_method": "POST",
  "request_path": "/login",
  "event_type": "login_attempt",
  "event_timestamp": "2026-10-09T12:00:00Z",
  "origin": "esp32",
  "metadata": {
    "firmware": "esp32-s3-1.0.0",
    "sensor": "pir-motion",
    "battery_level": 85
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | int | Yes | Currently only `1` |
| `source_event_id` | string | Yes | Unique ID from ESP32; max 128 chars |
| `device_id` | UUID | No | Registered decoy device ID |
| `source_ip` | IPv4/IPv6 | Yes | Client IP that connected to decoy |
| `destination_ip` | IPv4/IPv6 | Yes | Decoy's IP address |
| `transport_protocol` | string | Yes | `tcp`, `udp`, `icmp`, or `other` |
| `destination_port` | int | Yes | Port the client connected to (1-65535) |
| `application_protocol` | string | Yes | `http`, `https`, `ssh`, `telnet`, `mqtt`, or `unknown` |
| `http_method` | string | No | HTTP method if applicable (GET, POST, etc.) |
| `request_path` | string | No | Request path if applicable; must start with `/` |
| `event_type` | string | Yes | `page_access`, `login_attempt`, `sensitive_endpoint_access`, `unusual_endpoint_access`, `port_probe`, `heartbeat`, `other` |
| `event_timestamp` | ISO 8601 | Yes | UTC timestamp of the event |
| `origin` | string | Yes | Must be `esp32` |
| `metadata` | object | No | Structured data; sensitive keys filtered |

### Restrictions

- **No credentials**: Do not send passwords, tokens, or authorization headers in metadata
- **No request bodies**: Do not send full HTTP request bodies; only metadata keys
- **Size limits**: `source_event_id` ≤ 128 chars; `request_path` ≤ 512 chars; metadata keys ≤ 20, values ≤ 300 chars
- **Sensitive keys blocked**: Keys like `password`, `token`, `authorization`, `cookie`, `secret` are sanitized and not stored

## ESP32 Code Example

```cpp
// Pseudo-code for ESP32-S3
#include <HTTPClient.h>

void sendEvent(const char* sourceEventId, const char* jsonPayload) {
  HTTPClient http;
  http.begin("http://192.168.1.10:8000/api/v1/events");
  http.addHeader("Content-Type", "application/json");
  int code = http.POST(jsonPayload);
  http.end();
}
```

## Response

The backend returns:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "duplicate": false,
  "risk_score": 45,
  "severity": "medium",
  "processing_status": "processed",
  "explanation": "Medium risk indicator based on rule evidence..."
}
```

The ESP32 can log or act on the returned `risk_score` and `severity` if needed.

## Idempotency

If the ESP32 retries a failed request, use the same `source_event_id`. The backend detects duplicates and returns the existing event without re-running detection.

## Testing

To test ESP32 integration locally:
1. Start the backend with `DEMO_MODE=false`
2. Send a curl request with `origin: "esp32"`
3. Verify the event is stored with origin `esp32`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "schema_version": 1,
    "source_event_id": "esp32-test-001",
    "source_ip": "192.168.1.50",
    "destination_ip": "192.168.1.20",
    "transport_protocol": "tcp",
    "destination_port": 80,
    "application_protocol": "http",
    "event_type": "heartbeat",
    "event_timestamp": "2026-10-09T12:00:00Z",
    "origin": "esp32"
  }'
```