# DecoyNet ESP8266 Decoy Camera Firmware

Firmware for a **NodeMCU (ESP-12E)** that impersonates an IP security camera and
reports every access to the DecoyNet backend.

The device is an **event source only**. It serves believable camera pages, and
when a client touches one of them it POSTs a normalized security event to
`POST /api/v1/events`. All risk scoring, rule matching and storage happen in the
backend — the firmware does no scanning, no attack, and no detection of its own.

---

## What it serves

| Method | Path       | Simulated purpose             | Reported `event_type`               |
|--------|------------|-------------------------------|-------------------------------------|
| GET    | `/`        | Camera landing page           | `page_access`                       |
| GET/POST | `/login` | Administration login form     | `page_access` / `login_attempt`     |
| GET    | `/status`  | Device status JSON            | `sensitive_endpoint_access`         |
| GET    | `/config`  | Device configuration JSON     | `sensitive_endpoint_access`         |
| *      | anything   | 404                           | `unusual_endpoint_access`           |

Every event is sent with `origin: "esp32"`, `transport_protocol: "tcp"`,
`application_protocol: "http"`, and a UTC ISO-8601 `event_timestamp`.

**Passwords are never stored or transmitted.** The `/login` handler reads the
submitted form only to decide the `result` (`success` / `failed`); the password
value is discarded immediately. The backend also strips a list of sensitive keys
from `metadata`, but the firmware does not rely on that — it never sends them.

---

## Requirements

### Hardware
- NodeMCU ESP-12E (or any ESP8266 board with an LED on GPIO2)
- Micro-USB cable (data, not charge-only)
- 2.4 GHz Wi-Fi network — **the ESP8266 has no 5 GHz radio**

### Software
- [Arduino IDE](https://www.arduino.cc/en/software) 2.x (or Arduino CLI / PlatformIO)
- **ESP8266 board support**: in *File → Preferences → Additional Boards Manager
  URLs* add
  `http://arduino.esp8266.com/stable/package_esp8266com_index.json`,
  then in *Tools → Board → Boards Manager* install **esp8266**.
- Board libraries used: `ESP8266WiFi`, `ESP8266HTTPClient`, `ESP8266mDNS`,
  `WiFiClient` — all bundled with the ESP8266 core, **no extra installs**.

---

## Wiring

For this project the ESP8266 needs **no external components** — power it over
USB and it works. The on-board LED on GPIO2 doubles as a status indicator. If
you want an external LED, wire it with a series resistor:

```
ESP8266 GPIO2 (D4) ──[ 220Ω ]──►|── ESP8266 GND
                                 LED
```

| Pin     | Purpose                    |
|---------|----------------------------|
| GPIO2/D4 | Status LED (active LOW)   |
| GND     | Ground                     |

> GPIO2 is also a boot-strapping pin. The on-board LED is fine; do not pull
> GPIO2 to GND at boot or the board will enter flash mode.

---

## Configuration

1. Copy the example config:
   ```bash
   # Windows
   copy config.example.h config.h
   # Linux / macOS
   cp config.example.h config.h
   ```
2. Edit `config.h`:

   ```c
   #define WIFI_SSID     "your-2.4ghz-ssid"
   #define WIFI_PASSWORD "your-wifi-password"

   // The LAN IPv4 of the machine running FastAPI — find it with `ipconfig`.
   // NOT 127.0.0.1 (that would be the ESP8266 itself).
   #define BACKEND_HOST  "192.168.1.10"
   #define BACKEND_PORT  8000

   // Optional: link events to a registered device.
   #define DEVICE_ID     ""
   ```

`config.h` is **git-ignored**. Never commit real credentials or lab addresses.

### Point the backend at your LAN

The backend listens on `127.0.0.1` by default, which the ESP8266 cannot reach.
Start it bound to all interfaces:

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On Windows the first run may raise a firewall prompt — allow **private**
networks so the ESP8266 can connect.

---

## Upload

1. Open `DecoyNet_ESP8266.ino` in the Arduino IDE. The IDE will offer to open
   `config.h` in a tab — keep both in the **same folder** (`esp8266_firmware/`).
2. Select **Tools → Board → ESP8266 Boards → NodeMCU 1.0 (ESP-12E Module)**.
3. Select the correct **Port** (e.g. `COM5` on Windows, `/dev/ttyUSB0` on Linux).
4. Set **Upload Speed: 115200** if uploads are unstable.
5. Click **Upload**. If it fails with `espcomm_open failed`, hold the **FLASH**
   button on the board while the `Connecting........` line is shown.

### Serial monitor

Open the Serial Monitor at **115200 baud**. You should see:

```
[     120] BOOT     DecoyNet decoy camera 1.0.0
[     340] WIFI     connecting to SSID 'Priyan'
[    3200] WIFI     connected, IP 192.168.1.55 RSSI -58
[    3600] TIME     synced — UTC 2026-10-09T12:00:00Z
[    3650] HTTP     decoy camera listening on port 80
[    3700] MDNS     http://decoycam.local
```

---

## Testing end to end

Find the device IP from the serial log (or `decoycam.local`), then exercise it.

### 1. Trigger events from your workstation

```bash
# Page access  -> page_access
curl -i http://192.168.1.55/

# Sensitive endpoint -> sensitive_endpoint_access
curl -i http://192.168.1.55/status
curl -i http://192.168.1.55/config

# Login attempt -> login_attempt (result: failed)
curl -i -X POST http://192.168.1.55/login \
     -d "username=admin&password=wrong"

# Unknown path -> unusual_endpoint_access
curl -i http://192.168.1.55/admin/backup.zip
```

Also open `http://192.168.1.55/` in a browser and fill in the login form — the
browser sends a realistic `User-Agent`, which is captured in `metadata`.

### 2. Confirm the backend received them

```bash
curl "http://127.0.0.1:8000/api/v1/events?origin=esp32&limit=5"
```

Each item should show `"origin": "esp32"`, the correct `event_type`, and a
human-readable `explanation`. Filter by type to check specific paths:

```bash
curl "http://127.0.0.1:8000/api/v1/events?origin=esp32&event_type=login_attempt"
```

### 3. Confirm in the dashboard

Open the DecoyNet frontend (**Security Events** page) and filter by
**Origin = ESP32**. Simulator traffic carries the `simulator` badge, so real
device events are easy to tell apart.

### 4. Watch it live

Tail the serial monitor while you `curl` the device — each request logs a
`queued …` line and, moments later, a `delivered esp32-<chip>-<seq>` line.

---

## Optional: link events to a registered device

Register the decoy in the backend, then paste its UUID into `DEVICE_ID`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
        "name": "Lab decoy camera",
        "device_type": "camera",
        "ip_address": "192.168.1.55",
        "firmware_version": "1.0.0",
        "metadata": {"location": "lab bench", "role": "decoy"}
      }'
```

Re-flash or edit `DEVICE_ID` with the returned `id`. Device metadata accepts
only approved keys (`location`, `model`, `role`, `notes`, `lab_label`).

---

## How events are built

Each event carries a unique `source_event_id` of the form
`esp32-<chipId>-<sequence>`. The backend de-duplicates on
`(origin, source_event_id)`, so a retried delivery is recorded once and returned
with `processing_status: "duplicate"` — the firmware treats any 2xx as success,
duplicate or not.

```
schema_version     1
origin             esp32
source_ip          <connecting client>   (from the TCP peer address)
destination_ip     <device LAN IP>
transport_protocol tcp
destination_port   80
application_protocol http
http_method        GET / POST
request_path       /
event_type         page_access | login_attempt | sensitive_endpoint_access |
                   unusual_endpoint_access | heartbeat
event_timestamp    <UTC ISO-8601, e.g. 2026-10-09T12:00:00Z>
metadata           { username?, result?, user_agent?, query?, device_model,
                     firmware_version }
```

### Resilience

- **Offline queue** — if the backend is unreachable, events are buffered in a
  small ring buffer (`EVENT_QUEUE_SIZE`, default 8) and flushed when it returns.
  If the buffer overflows, the *oldest* event is dropped so recent activity
  survives; drops are counted and reported in `/status`.
- **Bounded retries** — a single event is retried up to `MAX_SEND_ATTEMPTS`
  times, spaced by `SEND_RETRY_INTERVAL_MS`, then dropped with a serial log.
- **Wi-Fi recovery** — auto-reconnect plus a periodic link check; NTP is
  re-synced if the clock ever looks wrong.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `Missing config.h` at compile | You did not copy `config.example.h` to `config.h`. |
| `WIFI connect timed out` | Wrong SSID/password, or a 5 GHz-only network. Use 2.4 GHz. |
| Upload hangs at `Connecting...` | Hold the FLASH button during connect; try a data USB cable; lower upload speed. |
| Events never arrive at the backend | `BACKEND_HOST` must be the LAN IP (not `127.0.0.1`) and uvicorn must bind `--host 0.0.0.0`. Check the host firewall. |
| `POST ... -> status 422` in the serial log | Payload failed schema validation — check `config.h` for stray quotes; file an issue with the logged body. |
| Timestamps look wrong | NTP has not synced yet; the device retries automatically. Check the network allows UDP 123 out. |
| LED stays off after boot | Wi-Fi not connected (see above). |

---

## Security notes

- This firmware is for a **trusted lab network only**, matching the backend's
  own posture (unauthenticated, no rate limiting).
- It does not expose a shell, does not scan, and does not attack anything — it
  only records accesses to its own decoy pages.
- The `/login` form is deliberately fake. It accepts any input and reports
  whether the submitted credentials matched a hard-coded dummy pair; it never
  stores or forwards them.
- Keep `config.h` out of version control. If you rotate the lab Wi-Fi password,
  re-flash the updated `config.h`.
