#pragma once

// ============================================================================
// DecoyNet ESP8266 firmware configuration (EXAMPLE)
// ----------------------------------------------------------------------------
// Copy this file to `config.h` in the same folder and fill in your own values.
// `config.h` is git-ignored — never commit real Wi-Fi or lab details.
//
//   Windows:  copy config.example.h config.h
//   Linux/macOS:  cp config.example.h config.h
// ============================================================================

// ---------------------------------------------------------------------------
// Wi-Fi (2.4 GHz only — the ESP8266 has no 5 GHz radio)
// ---------------------------------------------------------------------------
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define WIFI_CONNECT_TIMEOUT_MS 20000UL

// ---------------------------------------------------------------------------
// DecoyNet backend
// ---------------------------------------------------------------------------
// BACKEND_HOST must be the LAN IPv4 address of the machine running FastAPI,
// NOT 127.0.0.1 (that would be the ESP8266 itself). Find it with `ipconfig`.
//
// The backend also has to be bound to the LAN, not loopback. Start it with:
//   uvicorn app.main:app --host 0.0.0.0 --port 8000
#define BACKEND_HOST "192.168.1.10"
#define BACKEND_PORT 8000
#define BACKEND_PATH "/api/v1/events"

// ---------------------------------------------------------------------------
// This device's decoy identity
// ---------------------------------------------------------------------------
// Leave DEVICE_ID empty ("") unless you have registered a device via
// POST /api/v1/devices and want this device's events linked to it.
#define DEVICE_ID ""
#define DEVICE_NAME "DecoyCam IPC-100"
#define DEVICE_MODEL "IPC-100"
#define FIRMWARE_VERSION "1.0.0"

// Port the decoy camera listens on for incoming HTTP access.
#define DEVICE_HTTP_PORT 80

// Advertise this hostname over mDNS (e.g. decoycam.local). Set to 0 to disable.
#define ENABLE_MDNS 1
#define DEVICE_MDNS_HOST "decoycam"

// ---------------------------------------------------------------------------
// Time (timestamps are sent to the backend in UTC / ISO-8601)
// ---------------------------------------------------------------------------
#define NTP_SERVER_1 "pool.ntp.org"
#define NTP_SERVER_2 "time.google.com"
#define NTP_SYNC_TIMEOUT_MS 20000UL

// ---------------------------------------------------------------------------
// Event delivery
// ---------------------------------------------------------------------------
// How many events can be buffered while the backend is unreachable.
#define EVENT_QUEUE_SIZE 8
// Per-request timeout when posting an event to the backend.
#define HTTP_TIMEOUT_MS 4000
// Give up on a single event after this many failed delivery attempts.
#define MAX_SEND_ATTEMPTS 5
// Minimum gap between delivery attempts (simple backoff).
#define SEND_RETRY_INTERVAL_MS 2000UL
// Periodic heartbeat events (0 = only one heartbeat at boot).
#define HEARTBEAT_INTERVAL_MS 0UL

// ---------------------------------------------------------------------------
// Diagnostics
// ---------------------------------------------------------------------------
#define SERIAL_BAUD 115200
#define ENABLE_STATUS_LED 1
// NodeMCU ESP-12E on-board LED (active LOW).
#define STATUS_LED_PIN 2
