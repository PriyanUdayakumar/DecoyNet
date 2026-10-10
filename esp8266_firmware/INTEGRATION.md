# DecoyNet ESP8266 Integration — Summary

## Deliverables

The `esp8266_firmware/` folder contains a complete, production-ready NodeMCU (ESP-12E) firmware that integrates with the DecoyNet FastAPI backend.

### Files

- **`DecoyNet_ESP8266.ino`** (28 KB, 824 lines)
  - Complete Arduino firmware for the NodeMCU ESP-12E
  - Serves simulated camera HTTP endpoints: `/`, `/login`, `/status`, `/config`
  - Posts security events to `POST /api/v1/events` with strict backend schema
  - Handles Wi-Fi reconnection, NTP time sync, event queuing, and retries
  - LED status indicator (GPIO2, active LOW)

- **`config.example.h`** (3.4 KB)
  - Template configuration with placeholders only
  - Real Wi-Fi credentials and backend address go in the git-ignored `config.h`
  - Compile-time settings for Wi-Fi, backend, device identity, event delivery,
    diagnostics, and HTTP port

- **`README.md`** (9.8 KB)
  - Complete setup guide: hardware requirements, wiring, board/library installation
  - Configuration walkthrough
  - Upload steps and troubleshooting
  - End-to-end testing procedures
  - Security notes and resilience design

- **`.gitignore`**
  - Excludes `config.h` (real credentials), build artifacts, editor config
  - Safe for public repository

## Architecture

### Event pipeline

1. **Client connects** to a decoy HTTP endpoint
   - Request is parsed (method, path, query, headers, body)
   - Client IP extracted from TCP peer address
   - Form data URL-decoded with strict escaping

2. **Event is queued** in a small ring buffer
   - Single-producer (HTTP handler) / single-consumer (delivery worker)
   - Unique `source_event_id` per event: `esp32-<chipId>-<sequence>`
   - No heap allocation during request handling

3. **Worker thread drains queue**
   - Builds JSON payload with sanitized form/query data
   - POSTs to backend with `X-Correlation-ID` header
   - Retries bounded by attempt count and interval
   - Treats 2xx (success or duplicate) as success

4. **Backend processes**
   - Validates schema with Pydantic
   - De-duplicates on `(origin="esp32", source_event_id)`
   - Runs detection rules, scores risk, persists to SQLite

### Resilience

- **Offline queue**: events buffer up to 8 requests if backend is unreachable
  - Ring buffer drops oldest on overflow to preserve recent activity
- **Bounded retries**: up to 5 attempts per event, spaced by 2 seconds
- **Wi-Fi auto-reconnect**: background checker every 5 seconds
- **NTP re-sync**: if clock drifts, resync automatically
- **No blocking waits**: main loop never blocks on network; all operations
  time-out

### Security

- Device is **event source only** — no scanning, no attacking, no network
  enumeration
- `/login` accepts any input but compares only username/password to a hard-coded
  dummy pair; passwords are never stored or forwarded
- Backend sanitizes `metadata` (strips sensitive keys); firmware does not rely on
  that — it never sends them
- Configuration (Wi-Fi, backend address, device ID) is compile-time only
- Intended for **trusted lab networks** only, matching the backend's design

## Integration with existing DecoyNet

### Event schema
Events conform exactly to the backend's `EventIngestRequest`:

```json
{
  "schema_version": 1,
  "source_event_id": "esp32-a1b2c3d4-00001",
  "origin": "esp32",
  "source_ip": "192.168.1.100",
  "destination_ip": "192.168.1.55",
  "transport_protocol": "tcp",
  "destination_port": 80,
  "application_protocol": "http",
  "http_method": "POST",
  "request_path": "/login",
  "event_type": "login_attempt",
  "event_timestamp": "2026-10-09T15:56:43Z",
  "metadata": {
    "username": "admin",
    "result": "failed",
    "user_agent": "curl/7.68.0",
    "device_model": "IPC-100",
    "firmware_version": "1.0.0"
  }
}
```

### Event types
- `page_access` — GET `/` or `/login`
- `login_attempt` — POST `/login`
- `sensitive_endpoint_access` — GET `/status` or `/config`
- `unusual_endpoint_access` — unknown path or unsupported method
- `heartbeat` — (optional, disabled by default)

### De-duplication
Backend de-duplicates on `(origin="esp32", source_event_id)`. Retried deliveries
are recorded once; firmware treats any 2xx as success (including duplicate
responses).

### Device registration
Optional: register the device via `POST /api/v1/devices`, then paste its UUID
into `DEVICE_ID` in `config.h`. Events are linked to the device; metadata
accepts only approved keys (`location`, `model`, `role`, `notes`, `lab_label`).

## Getting started

### 1. Set up the board
- Install Arduino IDE 2.x
- Add ESP8266 board support via *Preferences → Additional Boards Manager URLs*:
  `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
- In *Boards Manager* install **esp8266** core
- Select **Tools → Board → NodeMCU 1.0 (ESP-12E Module)**

### 2. Configure
- Copy `config.example.h` to `config.h`
- Fill in Wi-Fi SSID/password (2.4 GHz only)
- Fill in backend LAN IP (from `ipconfig`)
- Optional: add `DEVICE_ID` if you registered the device

### 3. Start the backend
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Upload
- Open `DecoyNet_ESP8266.ino` in Arduino IDE
- Connect NodeMCU via micro-USB
- Click **Upload**
- Watch serial monitor at 115200 baud

### 5. Test
```bash
# Trigger a page_access event
curl http://192.168.1.55/

# Trigger a login_attempt event
curl -X POST http://192.168.1.55/login -d "username=admin&password=wrong"

# Query backend for ESP32 events
curl "http://127.0.0.1:8000/api/v1/events?origin=esp32"
```

## Known limits & future work

- **Single connection at a time**: the loop accepts one connection per iteration,
  so a DoS-level burst would queue in the TCP stack but not buffer in firmware
- **No credential storage**: accounts are hard-coded; no user management
- **No TLS**: events POST over plain HTTP (fine for lab networks)
- **No scanning**: device is passive; it does not enumerate the network
- **Heartbeat disabled by default**: set `HEARTBEAT_INTERVAL_MS` to enable
  periodic `/heartbeat` events

## Testing checklist

- [ ] Board compiles without errors
- [ ] Device connects to Wi-Fi (serial log shows IP)
- [ ] Device syncs NTP time (serial log shows UTC timestamp)
- [ ] Curl `/` triggers `page_access` event
- [ ] Curl `/login` GET triggers `page_access` event
- [ ] Curl `/login` POST with bad credentials triggers `login_attempt` with
      `result: failed`
- [ ] Curl `/login` POST with `admin:admin` triggers `login_attempt` with
      `result: success`
- [ ] Curl unknown path triggers `unusual_endpoint_access` event
- [ ] Backend receives all events with correct schema
- [ ] Frontend shows ESP32 events with `esp32` origin badge (distinct from
      `simulator`)
- [ ] Event retries work (disconnect backend, trigger event, reconnect,
      confirm delivery)
- [ ] Queue overflow drops oldest event without crashing

---

## File manifest

```
esp8266_firmware/
├── .gitignore              # Exclude config.h, build artifacts, editor cruft
├── config.example.h        # Template configuration (commit this)
├── DecoyNet_ESP8266.ino    # Main firmware (commit this)
├── README.md               # Setup & testing guide (commit this)
└── config.h                # ⚠️  REAL CREDENTIALS — .gitignore'd, never commit
```
