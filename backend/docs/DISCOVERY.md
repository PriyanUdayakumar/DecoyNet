# Network Discovery

## Overview

Network discovery allows authorized network scanning to identify live hosts on configured CIDR ranges. Discovery is **disabled by default** and requires explicit configuration to enable.

## Safety Model

Discovery is designed with multiple safety guards:

1. **Disabled by default**: Discovery is off until `DISCOVERY_ENABLED=true` is set
2. **Allowlist enforcement**: Targets must be within `AUTHORIZED_DISCOVERY_CIDRS`
3. **Bounded scope**: Maximum hosts per job limited by `DISCOVERY_MAX_HOSTS` (default 64)
4. **Timeout enforcement**: Per-host probe timeout via `DISCOVERY_TIMEOUT_SECONDS` (default 1.0s)
5. **Concurrency limits**: Controlled via `DISCOVERY_CONCURRENCY_LIMIT` (default 16)
6. **No stealth**: Standard TCP connect probes only; no stealth scanning
7. **No exploits**: No credential attacks, OS fingerprinting, or exploit checks

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCOVERY_ENABLED` | false | Enable discovery |
| `AUTHORIZED_DISCOVERY_CIDRS` | (none) | Comma-separated CIDR allowlist |
| `DISCOVERY_MAX_HOSTS` | 64 | Maximum hosts per job |
| `DISCOVERY_TIMEOUT_SECONDS` | 1.0 | Per-host probe timeout |
| `DISCOVERY_CONCURRENCY_LIMIT` | 16 | Concurrent probe limit |

### Example Configuration

```bash
# In .env
DISCOVERY_ENABLED=true
AUTHORIZED_DISCOVERY_CIDRS=192.168.1.0/24,192.168.2.0/24
```

## Usage

### Start a discovery job

```bash
curl -X POST http://127.0.0.1:8000/api/v1/discovery/jobs \
  -H "Content-Type: application/json" \
  -d '{"target_cidr": "192.168.1.0/30"}'
```

### Get job status

```bash
curl http://127.0.0.1:8000/api/v1/discovery/jobs/{job_id}
```

### List discovered hosts

```bash
curl http://127.0.0.1:8000/api/v1/discovery/hosts
```

## Response: Job

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

## Rejection Scenarios

| Condition | HTTP Status | Error Code |
|-----------|-------------|------------|
| Discovery disabled | 403 | discovery_not_allowed |
| Target outside allowlist | 403 | discovery_not_allowed |
| Target exceeds max hosts | 403 | discovery_not_allowed |
| Invalid CIDR format | 403 | discovery_not_allowed |

## Evidence and Limitations

- Discovery uses TCP connect probes on ports 80 and 443
- Results are evidence of responsiveness, not definitive host identification
- No MAC addresses, hostnames, or OS fingerprints are collected
- The system does not claim complete network inventory
- Partial results are reported; scan timeouts do not fail the entire job

## Ethical Use

Network discovery must only be used on networks you own or have explicit authorization to scan. Unauthorized network scanning may be illegal. This tool is intended for:
- Authorized lab environments
- Your own network inventory
- Penetration testing with written authorization

Do not use discovery to scan networks without explicit permission.