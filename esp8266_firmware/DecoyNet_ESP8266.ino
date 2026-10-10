// ============================================================================
// DecoyNet ESP8266 Decoy Camera Firmware
// ----------------------------------------------------------------------------
// A NodeMCU (ESP-12E) that pretends to be an IP security camera. It serves
// believable camera-looking HTTP endpoints and, whenever a client touches one
// of them, reports a normalized security event to the DecoyNet FastAPI backend
// (POST /api/v1/events).
//
// This device is an event SOURCE. It performs no scanning, no attacking, and
// no detection — all analysis happens in the backend. It is intended for a
// trusted lab network only.
//
// Board:   NodeMCU 1.0 (ESP-12E Module)
// Libs:    ESP8266 core for Arduino (install via Boards Manager URL
//          http://arduino.esp8266.com/stable/package_esp8266com_index.json)
//
// Before compiling: copy config.example.h to config.h and fill it in.
// See README.md for wiring, upload steps and end-to-end testing.
// ============================================================================

#include <Arduino.h>
#include <ESP8266HTTPClient.h>
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiClient.h>

#if __has_include("config.h")
#include "config.h"
#else
#error "Missing config.h — copy config.example.h to config.h and fill in your values."
#endif

// ---------------------------------------------------------------------------
// Compile-time configuration guards
// ---------------------------------------------------------------------------
#if DEVICE_HTTP_PORT < 1 || DEVICE_HTTP_PORT > 65535
#error "DEVICE_HTTP_PORT must be between 1 and 65535"
#endif
#if EVENT_QUEUE_SIZE < 1
#error "EVENT_QUEUE_SIZE must be at least 1"
#endif

#ifndef BACKEND_PATH
#define BACKEND_PATH "/api/v1/events"
#endif

static const char *kFirmwareVersion = FIRMWARE_VERSION;
static const char *kDeviceId = DEVICE_ID;

// ---------------------------------------------------------------------------
// Event model
// ---------------------------------------------------------------------------
enum EventType : uint8_t {
  EV_PAGE_ACCESS,
  EV_LOGIN_ATTEMPT,
  EV_SENSITIVE_ENDPOINT_ACCESS,
  EV_UNUSUAL_ENDPOINT_ACCESS,
  EV_PORT_PROBE,
  EV_HEARTBEAT,
  EV_OTHER,
};

struct PendingEvent {
  const char *eventType;   // enum string sent to the backend
  char requestPath[64];
  char httpMethod[6];
  uint16_t port;
  char clientIp[16];
  time_t timestamp;
  char sourceEventId[40];
  // Small fixed metadata set — kept as plain fields so the worker never has to
  // touch heap-allocated JSON while a request is live.
  bool hasUsername;
  char username[48];
  char result[12];         // "success" / "failed" / ""
  char userAgent[80];
  char query[48];
};

// ---------------------------------------------------------------------------
// Ring buffer of events waiting to be delivered to the backend.
// A single-producer (HTTP handler) / single-consumer (delivery worker) design:
// the handler appends while the worker drains, so a burst of requests never
// blocks on the network.
// ---------------------------------------------------------------------------
static PendingEvent g_queue[EVENT_QUEUE_SIZE];
static volatile uint16_t g_head = 0;  // next write slot
static volatile uint16_t g_tail = 0;  // next read slot
static volatile uint16_t g_count = 0;
static volatile uint32_t g_droppedEvents = 0;

// ---------------------------------------------------------------------------
// Runtime state
// ---------------------------------------------------------------------------
static WiFiServer g_server(DEVICE_HTTP_PORT);
static uint32_t g_bootMillis = 0;
static uint32_t g_lastHeartbeatMs = 0;
static uint32_t g_lastReconnectAttemptMs = 0;
static uint16_t g_sequence = 0;      // monotonic counter -> unique event ids
static bool g_timeSynced = false;
static uint32_t g_lastWifiCheckMs = 0;

static const uint32_t kWifiCheckIntervalMs = 5000UL;
static const uint32_t kWifiReconnectIntervalMs = 10000UL;

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------
static void logLine(const char *tag, const String &message) {
  Serial.printf("[%8lu] %-8s %s\n", (unsigned long)(millis() - g_bootMillis), tag, message.c_str());
}

static void setLed(bool on) {
#if ENABLE_STATUS_LED
  digitalWrite(STATUS_LED_PIN, on ? LOW : HIGH);  // active LOW on ESP-12E
#endif
}

// ---------------------------------------------------------------------------
// RFC 4180-escaped JSON string writer. Every value that originates from the
// network passes through here, so quotes, backslashes and control characters
// cannot break out of the JSON string and corrupt the payload.
// ---------------------------------------------------------------------------
static void appendJsonString(String &out, const char *value) {
  out += '"';
  if (value != nullptr) {
    for (const char *p = value; *p != '\0'; ++p) {
      unsigned char c = (unsigned char)*p;
      switch (c) {
        case '"': out += F("\\\""); break;
        case '\\': out += F("\\\\"); break;
        case '\b': out += F("\\b"); break;
        case '\f': out += F("\\f"); break;
        case '\n': out += F("\\n"); break;
        case '\r': out += F("\\r"); break;
        case '\t': out += F("\\t"); break;
        default:
          if (c < 0x20) {
            char buf[8];
            snprintf(buf, sizeof(buf), "\\u%04x", c);
            out += buf;
          } else {
            out += (char)c;
          }
      }
    }
  }
  out += '"';
}

// Format a UTC epoch as ISO-8601 with a Z suffix, e.g. 2026-10-09T12:00:00Z.
static String isoUtc(time_t when) {
  struct tm tmUtc;
  gmtime_r(&when, &tmUtc);
  char buf[24];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &tmUtc);
  return String(buf);
}

static void copyTruncated(char *dest, size_t destSize, const char *src) {
  if (destSize == 0) {
    return;
  }
  if (src == nullptr) {
    dest[0] = '\0';
    return;
  }
  strncpy(dest, src, destSize - 1);
  dest[destSize - 1] = '\0';
}

// ---------------------------------------------------------------------------
// URL decoding (application/x-www-form-urlencoded and query strings)
// ---------------------------------------------------------------------------
static void urlDecodeInPlace(char *text) {
  if (text == nullptr) {
    return;
  }
  char *src = text;
  char *dst = text;
  while (*src != '\0') {
    if (*src == '+') {
      *dst++ = ' ';
      ++src;
    } else if (*src == '%' && isxdigit((unsigned char)src[1]) && isxdigit((unsigned char)src[2])) {
      char hex[3] = {src[1], src[2], '\0'};
      *dst++ = (char)strtol(hex, nullptr, 16);
      src += 3;
    } else {
      *dst++ = *src++;
    }
  }
  *dst = '\0';
}

// Extract `key=value` from an application/x-www-form-urlencoded body into out.
static bool extractFormValue(const char *body, const char *key, char *out, size_t outSize) {
  if (body == nullptr || key == nullptr || outSize == 0) {
    return false;
  }
  out[0] = '\0';
  size_t keyLen = strlen(key);
  const char *p = body;
  while (p != nullptr && *p != '\0') {
    const char *pairEnd = strchr(p, '&');
    size_t pairLen = pairEnd ? (size_t)(pairEnd - p) : strlen(p);
    const char *eq = (const char *)memchr(p, '=', pairLen);
    if (eq != nullptr && (size_t)(eq - p) == keyLen && strncmp(p, key, keyLen) == 0) {
      size_t valueLen = pairLen - (size_t)(eq - p) - 1;
      char scratch[128];
      if (valueLen >= sizeof(scratch)) {
        valueLen = sizeof(scratch) - 1;
      }
      memcpy(scratch, eq + 1, valueLen);
      scratch[valueLen] = '\0';
      urlDecodeInPlace(scratch);
      copyTruncated(out, outSize, scratch);
      return true;
    }
    p = pairEnd ? pairEnd + 1 : nullptr;
  }
  return false;
}

// Extract the value of `key` from a query string the same way.
static bool extractQueryValue(const char *query, const char *key, char *out, size_t outSize) {
  return extractFormValue(query, key, out, outSize);
}

// ---------------------------------------------------------------------------
// Event queue
// ---------------------------------------------------------------------------
static bool queueEvent(const PendingEvent &event) {
  if (g_count >= EVENT_QUEUE_SIZE) {
    // Queue full: drop the oldest so the most recent activity is preserved.
    g_tail = (uint16_t)((g_tail + 1) % EVENT_QUEUE_SIZE);
    --g_count;
    ++g_droppedEvents;
  }
  g_queue[g_head] = event;
  g_head = (uint16_t)((g_head + 1) % EVENT_QUEUE_SIZE);
  ++g_count;
  return true;
}

// Build the JSON body for one event. Kept separate so it can be unit-checked by
// eye and so the delivery worker stays readable.
static String buildEventJson(const PendingEvent &event) {
  const IPAddress localIp = WiFi.localIP();
  String destIp = localIp.toString();

  String json;
  json.reserve(512);
  json += F("{\"schema_version\":1,\"source_event_id\":");
  appendJsonString(json, event.sourceEventId);
  json += F(",\"origin\":\"esp32\"");
  if (kDeviceId[0] != '\0') {
    json += F(",\"device_id\":");
    appendJsonString(json, kDeviceId);
  }
  json += F(",\"source_ip\":");
  appendJsonString(json, event.clientIp);
  json += F(",\"destination_ip\":");
  appendJsonString(json, destIp.c_str());
  json += F(",\"transport_protocol\":\"tcp\"");
  json += F(",\"destination_port\":");
  json += String(event.port);
  json += F(",\"application_protocol\":\"http\"");
  json += F(",\"http_method\":");
  appendJsonString(json, event.httpMethod);
  json += F(",\"request_path\":");
  appendJsonString(json, event.requestPath);
  json += F(",\"event_type\":");
  appendJsonString(json, event.eventType);
  json += F(",\"event_timestamp\":");
  appendJsonString(json, isoUtc(event.timestamp).c_str());
  json += F(",\"metadata\":{");
  bool first = true;
  if (event.hasUsername) {
    json += F("\"username\":");
    appendJsonString(json, event.username);
    first = false;
  }
  if (event.result[0] != '\0') {
    if (!first) json += ',';
    json += F("\"result\":");
    appendJsonString(json, event.result);
    first = false;
  }
  if (event.userAgent[0] != '\0') {
    if (!first) json += ',';
    json += F("\"user_agent\":");
    appendJsonString(json, event.userAgent);
    first = false;
  }
  if (event.query[0] != '\0') {
    if (!first) json += ',';
    json += F("\"query\":");
    appendJsonString(json, event.query);
    first = false;
  }
  if (!first) json += ',';
  json += F("\"device_model\":");
  appendJsonString(json, DEVICE_MODEL);
  json += F(",\"firmware_version\":");
  appendJsonString(json, kFirmwareVersion);
  json += F("}}");
  return json;
}

// POST one event to the backend using raw HTTP to ensure correct Content-Type.
// Returns true on any 2xx response (including 201 for new events and duplicate responses).
static bool postEvent(const PendingEvent &event) {
  if (WiFi.status() != WL_CONNECTED) {
    return false;
  }

  String body = buildEventJson(event);
  WiFiClient client;

  if (!client.connect(BACKEND_HOST, BACKEND_PORT)) {
    logLine("HTTP", String("connect failed to ") + BACKEND_HOST);
    return false;
  }

  client.print(F("POST "));
  client.print(BACKEND_PATH);
  client.print(F(" HTTP/1.1\r\n"));
  client.print(F("Host: "));
  client.print(BACKEND_HOST);
  client.print(':');
  client.print(String(BACKEND_PORT));
  client.print(F("\r\n"));
  client.print(F("Content-Type: application/json\r\n"));
  client.print(F("Accept: application/json\r\n"));
  client.print(F("X-Correlation-ID: "));
  client.print(event.sourceEventId);
  client.print(F("\r\n"));
  client.print(F("Content-Length: "));
  client.print(String(body.length()));
  client.print(F("\r\n"));
  client.print(F("Connection: close\r\n"));
  client.print(F("\r\n"));
  client.print(body);

  // Read response status line
  String statusLine = client.readStringUntil('\n');
  int status = 0;
  if (statusLine.startsWith("HTTP/1.")) {
    int sp = statusLine.indexOf(' ');
    if (sp > 0) {
      status = statusLine.substring(sp + 1).toInt();
    }
  }

  // Drain response headers
  while (client.available()) {
    String line = client.readStringUntil('\n');
    if (line.length() <= 1) break;  // End of headers
  }

  // Read response body (if any)
  String responseBody = "";
  while (client.available()) {
    responseBody += (char)client.read();
  }
  client.stop();

  bool ok = status >= 200 && status < 300;
  if (ok) {
    logLine("HTTP", String("POST ") + event.sourceEventId + " -> " + status);
  } else {
    logLine("HTTP", String("POST ") + event.sourceEventId + " -> " + status);
    if (responseBody.length() > 0) {
      // Log first 80 chars of error response (no sensitive data)
      logLine("RESP", responseBody.substring(0, responseBody.length() > 80 ? 80 : responseBody.length()));
    }
  }
  return ok;
}

// Drain the queue with bounded retries. Never runs concurrently with an HTTP
// handler because loop() is the only caller.
static void drainEventQueue() {
  static uint32_t lastAttemptMs = 0;
  if (g_count == 0) {
    return;
  }
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }
  if (millis() - lastAttemptMs < SEND_RETRY_INTERVAL_MS) {
    return;
  }
  lastAttemptMs = millis();

  PendingEvent &event = g_queue[g_tail];
  static uint8_t attempt = 0;

  if (postEvent(event)) {
    logLine("EVENT", String("delivered ") + event.sourceEventId);
    g_tail = (uint16_t)((g_tail + 1) % EVENT_QUEUE_SIZE);
    --g_count;
    attempt = 0;
    setLed(true);
    return;
  }

  ++attempt;
  if (attempt >= MAX_SEND_ATTEMPTS) {
    logLine("EVENT", String("dropping ") + event.sourceEventId + " after " + attempt + " attempts");
    g_tail = (uint16_t)((g_tail + 1) % EVENT_QUEUE_SIZE);
    --g_count;
    ++g_droppedEvents;
    attempt = 0;
  }
}

// ---------------------------------------------------------------------------
// Event construction helpers
// ---------------------------------------------------------------------------
static void makeSourceEventId(char *dest, size_t destSize, const char *prefix) {
  uint32_t chipSuffix = ESP.getChipId();
  uint16_t seq = ++g_sequence;
  snprintf(dest, destSize, "%s-%08x-%05u", prefix, chipSuffix, seq);
}

static void recordEvent(const char *eventType, const char *method, const char *path,
                        const IPAddress &clientIp, const char *username,
                        const char *result, const char *userAgent, const char *query) {
  PendingEvent event;
  memset(&event, 0, sizeof(event));
  event.eventType = eventType;
  event.port = DEVICE_HTTP_PORT;
  event.timestamp = time(nullptr);
  copyTruncated(event.requestPath, sizeof(event.requestPath), path);
  copyTruncated(event.httpMethod, sizeof(event.httpMethod), method);
  copyTruncated(event.clientIp, sizeof(event.clientIp), clientIp.toString().c_str());
  event.hasUsername = (username != nullptr && username[0] != '\0');
  if (event.hasUsername) {
    copyTruncated(event.username, sizeof(event.username), username);
  }
  copyTruncated(event.result, sizeof(event.result), result);
  copyTruncated(event.userAgent, sizeof(event.userAgent), userAgent);
  copyTruncated(event.query, sizeof(event.query), query);
  makeSourceEventId(event.sourceEventId, sizeof(event.sourceEventId), "esp32");
  queueEvent(event);
  logLine("EVENT", String("queued ") + eventType + " " + method + " " + path);
}

// ---------------------------------------------------------------------------
// Minimal HTTP layer
// ---------------------------------------------------------------------------
struct HttpRequest {
  char method[8];
  char rawTarget[192];  // full request target (path + query)
  char path[128];
  char query[96];
  char userAgent[80];
  String body;
};

static void splitTarget(const char *target, char *path, size_t pathSize, char *query,
                        size_t querySize) {
  const char *q = strchr(target, '?');
  if (q == nullptr) {
    copyTruncated(path, pathSize, target);
    query[0] = '\0';
  } else {
    size_t pathLen = (size_t)(q - target);
    if (pathLen >= pathSize) pathLen = pathSize - 1;
    memcpy(path, target, pathLen);
    path[pathLen] = '\0';
    copyTruncated(query, querySize, q + 1);
  }
  if (path[0] == '\0') {
    copyTruncated(path, pathSize, "/");
  }
}

static void sendResponse(WiFiClient &client, int status, const char *statusText,
                         const char *contentType, const String &body) {
  client.print(F("HTTP/1.1 "));
  client.print(status);
  client.print(' ');
  client.print(statusText);
  client.print(F("\r\nContent-Type: "));
  client.print(contentType);
  client.print(F("\r\nContent-Length: "));
  client.print(body.length());
  client.print(F("\r\nConnection: close\r\nServer: "));
  client.print(DEVICE_MODEL);
  client.print(F("\r\n\r\n"));
  client.print(body);
}

static void sendJson(WiFiClient &client, int status, const char *statusText, const String &json) {
  sendResponse(client, status, statusText, "application/json", json);
}

static void sendHtml(WiFiClient &client, int status, const char *statusText, const String &html) {
  sendResponse(client, status, statusText, "text/html; charset=utf-8", html);
}

// Read headers and (optionally) the body. Returns false if the client vanished
// mid-request.
static bool readRequest(WiFiClient &client, HttpRequest &req, uint32_t timeoutMs = 3000,
                        size_t maxBody = 256) {
  unsigned long start = millis();
  String line;

  // Request line
  while (millis() - start < timeoutMs) {
    if (!client.available()) {
      if (!client.connected()) return false;
      delay(1);
      continue;
    }
    line = client.readStringUntil('\n');
    break;
  }
  if (line.length() == 0) {
    return false;
  }
  line.trim();
  int firstSpace = line.indexOf(' ');
  int secondSpace = line.indexOf(' ', firstSpace + 1);
  if (firstSpace < 0 || secondSpace < 0) {
    return false;
  }
  copyTruncated(req.method, sizeof(req.method), line.substring(0, firstSpace).c_str());
  copyTruncated(req.rawTarget, sizeof(req.rawTarget),
                line.substring(firstSpace + 1, secondSpace).c_str());
  splitTarget(req.rawTarget, req.path, sizeof(req.path), req.query, sizeof(req.query));

  // Headers
  int contentLength = 0;
  unsigned long headerStart = millis();
  while (millis() - headerStart < timeoutMs) {
    if (!client.available()) {
      if (!client.connected()) break;
      delay(1);
      continue;
    }
    line = client.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) break;
    int colon = line.indexOf(':');
    if (colon < 0) continue;
    String name = line.substring(0, colon);
    name.toLowerCase();
    String value = line.substring(colon + 1);
    value.trim();
    if (name == "content-length") {
      contentLength = value.toInt();
    } else if (name == "user-agent") {
      copyTruncated(req.userAgent, sizeof(req.userAgent), value.c_str());
    }
  }

  // Body (bounded)
  req.body = "";
  if (contentLength > 0) {
    size_t toRead = (size_t)contentLength;
    if (toRead > maxBody) toRead = maxBody;
    unsigned long bodyStart = millis();
    while (req.body.length() < toRead && millis() - bodyStart < timeoutMs) {
      if (!client.available()) {
        if (!client.connected()) break;
        delay(1);
        continue;
      }
      req.body += (char)client.read();
    }
  }
  return true;
}

static bool isPath(const HttpRequest &req, const char *expected) {
  return strcmp(req.path, expected) == 0;
}

// ---------------------------------------------------------------------------
// Simulated camera pages
// ---------------------------------------------------------------------------
static void serveLoginPage(WiFiClient &client, const HttpRequest &req, const IPAddress &ip) {
  const char *username = nullptr;
  const char *result = nullptr;

  String commonStyle = F("<style>"
                         "body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f4f7f6;color:#333;margin:0;padding:0;display:flex;justify-content:center;align-items:center;height:100vh;}"
                         "main{background:#fff;padding:40px;border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,0.1);width:100%;max-width:320px;text-align:center;}"
                         "h1{margin-top:0;color:#2c3e50;font-size:22px;margin-bottom:20px;}"
                         "input{width:100%;padding:12px;margin-bottom:15px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;font-size:14px;}"
                         "button{width:100%;padding:12px;background:#3498db;color:#fff;border:none;border-radius:4px;font-size:16px;cursor:pointer;font-weight:bold;transition:background 0.3s;}"
                         "button:hover{background:#2980b9;}"
                         ".err{color:#e74c3c;margin-bottom:15px;font-weight:bold;}"
                         ".ok{color:#2ecc71;margin-bottom:15px;font-weight:bold;}"
                         "a{display:block;margin-top:15px;color:#3498db;text-decoration:none;font-size:14px;}"
                         "a:hover{text-decoration:underline;}"
                         "</style>");

  if (strcasecmp(req.method, "POST") == 0) {
    char user[48];
    char pass[48];
    bool hasUser = extractFormValue(req.body.c_str(), "username", user, sizeof(user));
    bool hasPass = extractFormValue(req.body.c_str(), "password", pass, sizeof(pass));
    // Submitted passwords are deliberately never stored or forwarded.
    bool success = hasUser && hasPass && strlen(user) > 0 && strcmp(user, "admin") == 0 &&
                   strcmp(pass, "admin") == 0;
    username = hasUser ? user : "";
    result = success ? "success" : "failed";
    recordEvent("login_attempt", "POST", "/login", ip, username, result, req.userAgent, req.query);
    
    String html = F("<!DOCTYPE html><html><head><title>Sign In Status</title><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
    html += commonStyle;
    html += F("</head><body><main>");
    html += success ? F("<p class=\"ok\">Signed in. Redirecting&hellip;</p>") : F("<p class=\"err\">Invalid credentials.</p><a href=\"/login\">Try Again</a>");
    html += F("</main></body></html>");
    sendHtml(client, 200, "OK", html);
    return;
  }

  if (strcasecmp(req.method, "GET") == 0) {
    // A GET on /login is still worth recording — someone is looking at the page.
    recordEvent("page_access", "GET", "/login", ip, nullptr, nullptr, req.userAgent, req.query);
    String html = F("<!DOCTYPE html><html><head><title>Sign in</title><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
    html += commonStyle;
    html += F("</head><body><main><h1>Camera Administration</h1>");
    html += F("<form method=\"post\" action=\"/login\">");
    html += F("<input name=\"username\" placeholder=\"Username\" required>");
    html += F("<input name=\"password\" type=\"password\" placeholder=\"Password\" required>");
    html += F("<button type=\"submit\">Sign In</button>");
    html += F("</form><a href=\"/\">&larr; Back to Home</a></main></body></html>");
    sendHtml(client, 200, "OK", html);
    return;
  }

  recordEvent("unusual_endpoint_access", req.method, "/login", ip, nullptr, nullptr, req.userAgent,
              req.query);
  sendJson(client, 405, "Method Not Allowed", "{\"error\":\"method_not_allowed\"}");
}

static void serveStatus(WiFiClient &client, const HttpRequest &req, const IPAddress &ip) {
  recordEvent("sensitive_endpoint_access", req.method, "/status", ip, nullptr, nullptr,
              req.userAgent, req.query);
  String html;
  html.reserve(1024);
  html += F("<!DOCTYPE html><html><head><title>Device Status</title><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
  html += F("<style>"
            "body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f4f7f6;color:#333;margin:0;padding:0;}"
            "header{background:#2c3e50;color:#fff;padding:20px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.1);}"
            "h1{margin:0;font-size:24px;}"
            "main{max-width:600px;margin:40px auto;background:#fff;padding:30px;border-radius:8px;box-shadow:0 4px 6px rgba(0,0,0,0.05);}"
            "table{width:100%;border-collapse:collapse;margin-top:20px;}"
            "th,td{padding:12px;border-bottom:1px solid #ddd;text-align:left;}"
            "th{background:#f8f9fa;font-weight:600;}"
            "a{display:inline-block;margin-top:20px;color:#3498db;text-decoration:none;font-weight:bold;}"
            "a:hover{text-decoration:underline;}"
            "</style></head><body>");
  html += F("<header><h1>Device Status</h1></header><main>");
  html += F("<table><tbody>");
  html += F("<tr><th>Device Model</th><td>"); html += DEVICE_MODEL; html += F("</td></tr>");
  html += F("<tr><th>Firmware Version</th><td>"); html += kFirmwareVersion; html += F("</td></tr>");
  html += F("<tr><th>IP Address</th><td>"); html += WiFi.localIP().toString(); html += F("</td></tr>");
  html += F("<tr><th>Uptime (s)</th><td>"); html += String((millis() - g_bootMillis) / 1000UL); html += F("</td></tr>");
  html += F("<tr><th>WiFi RSSI</th><td>"); html += String(WiFi.RSSI()); html += F("</td></tr>");
  html += F("<tr><th>Free Heap</th><td>"); html += String(ESP.getFreeHeap()); html += F("</td></tr>");
  html += F("<tr><th>Events Pending</th><td>"); html += String(g_count); html += F("</td></tr>");
  html += F("<tr><th>Events Dropped</th><td>"); html += String(g_droppedEvents); html += F("</td></tr>");
  html += F("</tbody></table>");
  html += F("<a href=\"/\">&larr; Back to Home</a>");
  html += F("</main></body></html>");
  sendHtml(client, 200, "OK", html);
}

static void serveConfig(WiFiClient &client, const HttpRequest &req, const IPAddress &ip) {
  recordEvent("sensitive_endpoint_access", req.method, "/config", ip, nullptr, nullptr,
              req.userAgent, req.query);
  String html;
  html.reserve(1024);
  html += F("<!DOCTYPE html><html><head><title>Device Configuration</title><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
  html += F("<style>"
            "body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f4f7f6;color:#333;margin:0;padding:0;}"
            "header{background:#2c3e50;color:#fff;padding:20px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.1);}"
            "h1{margin:0;font-size:24px;}"
            "main{max-width:600px;margin:40px auto;background:#fff;padding:30px;border-radius:8px;box-shadow:0 4px 6px rgba(0,0,0,0.05);}"
            "table{width:100%;border-collapse:collapse;margin-top:20px;}"
            "th,td{padding:12px;border-bottom:1px solid #ddd;text-align:left;}"
            "th{background:#f8f9fa;font-weight:600;width:40%;}"
            "a{display:inline-block;margin-top:20px;color:#3498db;text-decoration:none;font-weight:bold;}"
            "a:hover{text-decoration:underline;}"
            "</style></head><body>");
  html += F("<header><h1>Device Configuration</h1></header><main>");
  html += F("<table><tbody>");
  html += F("<tr><th>Device Name</th><td>"); html += DEVICE_NAME; html += F("</td></tr>");
  html += F("<tr><th>Model</th><td>"); html += DEVICE_MODEL; html += F("</td></tr>");
  html += F("<tr><th>Firmware</th><td>"); html += kFirmwareVersion; html += F("</td></tr>");
  html += F("<tr><th>HTTP Port</th><td>"); html += String(DEVICE_HTTP_PORT); html += F("</td></tr>");
  html += F("<tr><th>Reporting Enabled</th><td>True</td></tr>");
  html += F("</tbody></table>");
  html += F("<a href=\"/\">&larr; Back to Home</a>");
  html += F("</main></body></html>");
  sendHtml(client, 200, "OK", html);
}

static void serveRoot(WiFiClient &client, const HttpRequest &req, const IPAddress &ip) {
  recordEvent("page_access", req.method, req.path, ip, nullptr, nullptr, req.userAgent, req.query);
  String html;
  html.reserve(1024);
  html += F("<!DOCTYPE html><html><head><title>");
  html += DEVICE_NAME;
  html += F("</title><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">");
  html += F("<style>"
            "body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f4f7f6;color:#333;margin:0;padding:0;}"
            "header{background:#2c3e50;color:#fff;padding:20px;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,0.1);}"
            "h1{margin:0;font-size:24px;}"
            "main{max-width:600px;margin:40px auto;background:#fff;padding:30px;border-radius:8px;box-shadow:0 4px 6px rgba(0,0,0,0.05);}"
            "ul{list-style:none;padding:0;margin:20px 0 0;}"
            "li{margin-bottom:15px;}"
            "a{display:block;padding:15px;background:#ecf0f1;color:#2980b9;text-decoration:none;border-radius:6px;font-weight:bold;transition:background 0.3s, color 0.3s;}"
            "a:hover{background:#3498db;color:#fff;}"
            "p{color:#7f8c8d;font-size:14px;text-align:center;margin-top:0;}"
            "</style></head><body>");
  html += F("<header><h1>");
  html += DEVICE_NAME;
  html += F("</h1></header><main><p>Firmware Version: ");
  html += kFirmwareVersion;
  html += F("</p><ul><li><a href=\"/status\">Device Status</a></li>");
  html += F("<li><a href=\"/config\">Device Configuration</a></li>");
  html += F("<li><a href=\"/login\">Administration Login</a></li></ul></main></body></html>");
  sendHtml(client, 200, "OK", html);
}

static void handleClient(WiFiClient &client) {
  IPAddress clientIp = client.remoteIP();
  HttpRequest req;
  if (!readRequest(client, req)) {
    client.stop();
    return;
  }

  if (strcasecmp(req.method, "GET") == 0 && (isPath(req, "/") || isPath(req, "/home"))) {
    serveRoot(client, req, clientIp);
  } else if ((strcasecmp(req.method, "GET") == 0 || strcasecmp(req.method, "POST") == 0) &&
             isPath(req, "/login")) {
    serveLoginPage(client, req, clientIp);
  } else if (strcasecmp(req.method, "GET") == 0 && isPath(req, "/status")) {
    serveStatus(client, req, clientIp);
  } else if (strcasecmp(req.method, "GET") == 0 && isPath(req, "/config")) {
    serveConfig(client, req, clientIp);
  } else if (isPath(req, "/favicon.ico")) {
    sendResponse(client, 204, "No Content", "image/x-icon", "");
  } else {
    recordEvent("unusual_endpoint_access", req.method, req.path, clientIp, nullptr, nullptr,
                req.userAgent, req.query);
    String body = F("{\"error\":\"not_found\",\"path\":");
    appendJsonString(body, req.path);
    body += '}';
    sendJson(client, 404, "Not Found", body);
  }

  client.stop();
}

// ---------------------------------------------------------------------------
// Wi-Fi / time / connectivity
// ---------------------------------------------------------------------------
static void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.hostname(DEVICE_MDNS_HOST);
  WiFi.setAutoReconnect(true);
  WiFi.setSleepMode(WIFI_NONE_SLEEP);

  logLine("WIFI", String("connecting to SSID '") + WIFI_SSID + "'");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < WIFI_CONNECT_TIMEOUT_MS) {
    delay(250);
    setLed((millis() / 250) % 2 == 0);
  }

  if (WiFi.status() == WL_CONNECTED) {
    setLed(true);
    logLine("WIFI", String("connected, IP ") + WiFi.localIP().toString() + " RSSI " +
                        String(WiFi.RSSI()));
  } else {
    setLed(false);
    logLine("WIFI", F("connect timed out — will retry in background"));
  }
}

static void syncTime() {
  if (g_timeSynced) {
    return;
  }
  configTime(0, 0, NTP_SERVER_1, NTP_SERVER_2);  // UTC
  uint32_t start = millis();
  while (millis() - start < NTP_SYNC_TIMEOUT_MS) {
    time_t now = time(nullptr);
    if (now > 1600000000) {  // sanity floor: after Sep-2020
      g_timeSynced = true;
      logLine("TIME", String("synced — UTC ") + isoUtc(now));
      return;
    }
    delay(250);
  }
  logLine("TIME", F("NTP sync failed — timestamps will be approximate until it succeeds"));
}

static void maintainWifi() {
  if (millis() - g_lastWifiCheckMs < kWifiCheckIntervalMs) {
    return;
  }
  g_lastWifiCheckMs = millis();

  if (WiFi.status() == WL_CONNECTED) {
    return;
  }
  setLed(false);
  if (millis() - g_lastReconnectAttemptMs < kWifiReconnectIntervalMs) {
    return;
  }
  g_lastReconnectAttemptMs = millis();
  logLine("WIFI", F("link down — reconnecting"));
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

static void maintainTime() {
  if (!g_timeSynced && WiFi.status() == WL_CONNECTED && time(nullptr) > 1600000000) {
    g_timeSynced = true;
  }
  // Re-arm if the clock ever looks wrong again.
  if (g_timeSynced && time(nullptr) < 1600000000) {
    g_timeSynced = false;
  }
}

static void sendHeartbeat() {
  IPAddress self = WiFi.localIP();
  recordEvent("heartbeat", "GET", "/heartbeat", self, nullptr, nullptr, "firmware", "");
}

static void beat() {
  if (HEARTBEAT_INTERVAL_MS == 0UL) {
    return;
  }
  if (millis() - g_lastHeartbeatMs < HEARTBEAT_INTERVAL_MS) {
    return;
  }
  g_lastHeartbeatMs = millis();
  sendHeartbeat();
}

// ---------------------------------------------------------------------------
// Arduino lifecycle
// ---------------------------------------------------------------------------
void setup() {
  g_bootMillis = millis();
  Serial.begin(SERIAL_BAUD);
  delay(200);
  Serial.println();
  logLine("BOOT", String("DecoyNet decoy camera ") + kFirmwareVersion);

#if ENABLE_STATUS_LED
  pinMode(STATUS_LED_PIN, OUTPUT);
  setLed(false);
#endif

  connectWifi();
  if (WiFi.status() == WL_CONNECTED) {
    syncTime();
  }

  g_server.begin();
  g_server.setNoDelay(true);
  logLine("HTTP", String("decoy camera listening on port ") + DEVICE_HTTP_PORT);

#if ENABLE_MDNS
  if (MDNS.begin(DEVICE_MDNS_HOST)) {
    MDNS.addService("http", "tcp", DEVICE_HTTP_PORT);
    logLine("MDNS", String("http://") + DEVICE_MDNS_HOST + ".local");
  } else {
    logLine("MDNS", F("responder failed to start"));
  }
#endif

  sendHeartbeat();
}

void loop() {
  maintainWifi();
  if (WiFi.status() == WL_CONNECTED) {
    maintainTime();
  }

#if ENABLE_MDNS
  MDNS.update();
#endif

  // Accept at most one connection per loop so the delivery worker keeps its
  // turn even under a burst of inbound requests.
  WiFiClient client = g_server.available();
  if (client) {
    handleClient(client);
  }

  drainEventQueue();
  beat();

  delay(1);
}
