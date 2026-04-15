# HydroponicOne AI Coding Agent Instructions

## Project Overview

**HydroponicOne** is a production-grade IoT hydroponic control platform consisting of:
- **Firmware**: ESP32 nodes running custom C++ with deep-sleep, sensors (DHT11, DS18B20, HC-SR04, etc.), MQTT, and OTA support
- **Backend**: Node.js/TypeScript REST API + MQTT bridge + WebSocket real-time telemetry ingestion
- **Frontend**: (Not yet implemented) React/Vue dashboard
- **Docker**: Local dev environment with Mosquitto MQTT broker

## Architecture at a Glance

```
ESP32 Devices (firmware/) 
    ↓ MQTT (TLS) over broker
Backend (backend/)
    ├─ MQTT Worker: Subscribes nfthydro1337/+/# → parses → writes to InfluxDB + broadcasts via Socket.IO
    ├─ REST API: Device control, config, OTA, telemetry history
    ├─ OTA Service: Signs firmware with RSA-SHA256 + publishes to cmd/ota
    ├─ Database: PostgreSQL (devices, system config, actuation logs)
    └─ Telemetry: InfluxDB time-series measurements
Dashboard (frontend/)
    ↓ Socket.IO (real-time) + REST (historical)
```

## Critical Patterns & Conventions

### 1. MQTT Topic Hierarchy and Naming
- **Base topic** (from env): `MQTT_BASE_TOPIC` (default: `"HydroOne"`)
- **Sensor telemetry topics** (published by device): `{BASE_TOPIC}/{DEVICE_ID}/sensors/{sensor_type}/{sensor_name}` or `{BASE_TOPIC}/{DEVICE_ID}/power/{power_type}`
  - Example: `HydroOne/HydroNode_01/sensors/water/temperature`
  - Example: `HydroOne/HydroNode_01/power/battery`
  - Payloads: Numeric (e.g., `22.5`) or JSON `{"value": 22.5}`
- **Commands published by backend**: `{BASE_TOPIC}/{DEVICE_ID}/cmd/{command}`
  - Examples: `cmd/pump`, `cmd/mode`, `cmd/config`, `cmd/ota`, `cmd/tank`
- **Device lifecycle**: `status` and `heartbeat` topics are NOT stored as telemetry; used for device status updates

**Key implication**: All MQTT topic strings must reference `env.MQTT_BASE_TOPIC` (not hardcoded). Device IDs and sensor tags are extracted via topic parsing (see `mqtt.service.ts` lines 47–87).

### 2. Validation & Security Model
- **Environment variables**: All required env vars validated via Zod at startup in `config/env.ts` → kills process if invalid
- **Request body validation**: All API handlers use Zod schema parsing (e.g., `api.routes.ts` line 15: `z.object({...}).parse(req.body)`)
- **MQTT payload parsing**: Permissive but careful — tries JSON first, falls back to numeric parsing. Sensor values validated with `Number.isFinite()` before writing to InfluxDB (see `mqtt.service.ts` lines 65–72)
- **Never trust device input**: MQTT payloads from sensors are normalized and logged; malformed messages log warnings but don't crash the worker

### 3. Telemetry Data Flow (MQTT → InfluxDB)
1. Device publishes numeric value to `{BASE_TOPIC}/{DEVICE_ID}/sensors/{sensorType}/{sensorName}` → `mqtt.service.ts` receives (line 34)
2. Topic split into parts and device_id extracted (lines 47–55)
3. Payload parsed to number, validated for finiteness (lines 65–72)
4. Sensor tag constructed: `sensor = ${sensorCategory}_${sensorName}` (e.g., `water_temperature`) (line 87)
5. Call `writeTelemetry(deviceId, sensorCategory, sensorName, value)` → writes to **InfluxDB** measurement `hydro_telemetry` with tags `device_id`, `sensor` and float field `value` (see `telemetry.service.ts` lines 28–35)
6. Broadcast to connected WebSocket clients via `broadcastTelemetry()` (line 102, uses `sockets/socket.ts`)
7. Ignore `/status` and `/heartbeat` topics (they don't contain numeric sensor values) (lines 59–62)

**Example InfluxDB structure** (simplified schema):
```
measurement: hydro_telemetry
tags:
  device_id=HydroNode_01
  sensor=water_temperature
fields:
  value=22.4 (float)
```

**Example InfluxDB Flux query**:
```
from(bucket:"hydro_bucket")
  |> range(start: -24h)
  |> filter(fn: (r) => r.device_id == "HydroNode_01" and r.sensor == "water_temperature")
```

### 4. OTA Firmware Signing Workflow
Located in `services/ota.service.ts`.
1. Receive device_id, firmware binary path, version, download URL from REST API (`/ota/deploy`)
2. Load firmware .bin file, compute MD5 hash
3. Load private key from `OTA_PRIVATE_KEY_PATH` (env var)
4. Build payload string: `"{url}|{version}|{md5}"`
5. Sign with RSA-SHA256 using private key (base64 encoded result)
6. Publish JSON to `{BASE_TOPIC}/{device_id}/cmd/ota`:
   ```json
   { "url": "...", "version": "...", "md5": "...", "signature": "..." }
   ```
7. Device firmware verifies signature using public key before flashing

**Security note**: Protect `OTA_PRIVATE_KEY_PATH` in production. Keys stored in `firmware/data/` folder.

### 5. Database Access Pattern
- **ORM**: Prisma 7.x with PostgreSQL adapter (see `prisma/schema.prisma`)
- **Adapter initialization**: Uses `@prisma/adapter-pg` for connection pooling (see `api.routes.ts` lines 14–16):
  ```typescript
  const pool = new pg.Pool({ connectionString: env.DATABASE_URL })
  const adapter = new PrismaPg(pool)
  const prisma = new PrismaClient({ adapter } as any)
  ```
- **Config location**: Database URL moved to `prisma.config.ts` (Prisma 7 requirement; schema.prisma has no `url`)
- **Per-route client**: Single `PrismaClient` instance per route file (reused across requests)
- **Models**:
  - `Device`: device_id (unique), firmware_version, last_seen, status
  - `SystemConfig`: Contains all firmware tunable parameters (pH targets, EC targets, pump timings, tank geometry, sleep settings)
  - `ActuationLog`: Records every pump/control command sent to devices
- **Pattern**: Upsert for config (e.g., `api.routes.ts` line 36: `.upsert({ where: { id: 1 }, create: {...}, update: {...} })`)

### 6. Service Layer Architecture
- **Services are singletons or stateless functions**:
  - `mqtt.service.ts`: Singleton client initialized once, exports `initMqtt()` + `mqttPublish(topic, payload)`
  - `telemetry.service.ts`: Stateless `writeTelemetry()` function writes to InfluxDB
  - `ota.service.ts`: Stateless `deployOta()` function; calls `mqttPublish()` internally
- **No cross-service imports** of internal state — all communication through MQTT or function calls
- **Error logging**: All services log via pino logger from `utils/logger.ts`; errors caught and logged, not thrown unless critical

### 7. Development Workflow

**Setup**:
```powershell
copy .env.example .env          # Fill in broker, Influx, DB credentials
npm install
npx prisma generate            # Generate Prisma client
npx prisma migrate dev --name init  # Create + apply migrations
```

**Run**:
```powershell
npm run dev                     # ts-node-dev with auto-restart
```

**Build**:
```powershell
npm run build                   # tsc compilation to dist/
npm start                       # Run dist/server.js
```

**Key commands**:
- `npx prisma studio`: Browse PostgreSQL via GUI
- `npx prisma migrate dev --name <name>`: Create and apply new schema migration
- `pio run --target upload`: Build and flash ESP32 firmware (from `firmware/` folder, separate project)

### 8. Express & Middleware Stack
- **Security**: Helmet, CORS (origin-restricted), rate-limit (120 req/min)
- **Body parsing**: JSON up to 1MB, URL-encoded
- **Router**: All API endpoints under `/api` prefix mounted in `server.ts` line 34
- **Health endpoint**: `GET /health` returns `{status: "ok"}`
- **Socket.IO**: Initialized on HTTP server in `initSockets()` before server listen (see `server.ts` line 37)

### 9. TypeScript Strictness
- **No `any` types** — use specific types or Zod schemas
- **All function parameters typed** — even `(err) => {...}` must be typed or use type guard
- **Config exports typed objects** — `validateEnv()` returns typed object, not raw env dict
- **Implicit `any` errors**: If editor shows implicit any, fix by:
  - Adding explicit parameter type: `(req: Request, res: Response) => ...`
  - Or using Zod for parse-time validation

## File Navigation Guide

| File | Purpose |
|------|---------|
| `src/server.ts` | Express app, middleware stack, service initialization |
| `src/config/env.ts` | Zod env schema + typed object return |
| `src/services/mqtt.service.ts` | MQTT singleton + telemetry ingestion pipeline + device status handling |
| `src/services/telemetry.service.ts` | InfluxDB write client |
| `src/services/device-status.service.ts` | Device status persistence (PostgreSQL) and retrieval |
| `src/services/influx-query.service.ts` | InfluxDB Flux query helper for telemetry history |
| `src/services/ota.service.ts` | Firmware signing + MQTT publish |
| `src/routes/api.routes.ts` | REST endpoints for device info, telemetry, control, config, OTA |
| `src/sockets/socket.ts` | Socket.IO server + broadcast helper |
| `prisma/schema.prisma` | PostgreSQL schema (Device, SystemConfig, ActuationLog) |
| `package.json` | Dependencies + build/dev scripts |
| `.env.example` | Template for required env variables |

## REST API Endpoints

### Device Information & Telemetry

**GET /api/devices/:deviceId**
- Returns current device status + latest sensor readings
- Response: `{ id, device_id, name, location, status, firmware_version, last_seen, telemetry: {...} }`
- Example: `GET /api/devices/HydroNode_01`

**GET /api/devices/:deviceId/telemetry**
- Query historical telemetry from InfluxDB
- Query params: `range` (default "24h"), `sensor` (optional, filter by sensor name)
- Response: `{ deviceId, range, sensor, count, data: [{ timestamp, sensor, value }, ...] }`
- Example: `GET /api/devices/HydroNode_01/telemetry?range=7d&sensor=water_temperature`

### System Configuration

**GET /api/config**
- Fetch global system configuration (always returns valid config, creates defaults if missing)
- Response: SystemConfig object with all tuning parameters
- Example: `GET /api/config`

**POST /api/config**
- Update system configuration
- Body: `{ deepSleepEnabled?: boolean, ... }`
- Publishes updates to all devices via MQTT
- Example: `POST /api/config` with `{ "deepSleepEnabled": true }`

### Device Control

**POST /api/control/pump**
- Control pump relay
- Body: `{ deviceId: string, action: string, duration?: number }`
- Example: `POST /api/control/pump` with `{ "deviceId": "HydroNode_01", "action": "on", "duration": 30000 }`

**POST /api/control/mode**
- Set device operating mode
- Body: `{ deviceId: string, mode: "maintenance" | "auto" | "manual" }`
- Example: `POST /api/control/mode` with `{ "deviceId": "HydroNode_01", "mode": "auto" }`

**POST /api/control/tank**
- Configure tank geometry
- Body: `{ deviceId: string, tankType?: string, tankDimA?: number, tankDimB?: number }`
- Example: `POST /api/control/tank` with `{ "deviceId": "HydroNode_01", "tankType": "rectangular", "tankDimA": 100, "tankDimB": 50 }`

### OTA Firmware Updates

**POST /api/ota/deploy**
- Deploy firmware update to device
- Body: `{ deviceId: string, firmwarePath: string, version: string, url: string }`
- Signs firmware with RSA-SHA256 and publishes to device
- Example: `POST /api/ota/deploy` with `{ "deviceId": "HydroNode_01", "firmwarePath": "./firmware.bin", "version": "1.1.0", "url": "https://..." }`

## Common Tasks for AI Agents

### Adding a new REST endpoint
1. Add Zod schema for request body in `api.routes.ts`
2. Parse with `z.object({...}).parse(req.body)` 
3. Interact with Prisma or MQTT as needed
4. Return JSON response
5. Always wrap database calls in try-catch for error handling
6. Example: Lines 70–80 (pump control)

### Querying telemetry history
1. Import `queryTelemetry` or `queryLatestTelemetry` from `influx-query.service.ts`
2. Call with `deviceId`, optional `range` (e.g., "24h", "7d"), optional `sensor` filter
3. Returns array of `{ timestamp, sensor, value }` objects
4. Use in GET `/api/devices/:deviceId/telemetry` endpoint
5. See `api.routes.ts` lines 46–66 for implementation

### Storing device status
1. MQTT message arrives on `/status` topic
2. Parse JSON payload containing `{ timestamp, uptime, state, wifi, mqtt, pump, errors, heap, firmware }`
3. Call `updateDeviceStatus(deviceId, statusData)` from `device-status.service.ts`
4. Updates PostgreSQL Device record with latest state + firmware version
5. Broadcast to WebSocket clients for real-time dashboard updates

### Fetching singleton configuration (GET /config pattern)
1. Call `prisma.systemConfig.findFirst()`
2. If result is null, create default with `prisma.systemConfig.create({ data: {} })`
3. Prisma schema defaults (e.g., `@default(false)`, `@default(5.5)`) are automatically applied
4. Always return a valid config object, never null
5. Log when auto-creating default config for debugging
6. See `api.routes.ts` lines 82–96 for implementation

### Adding MQTT command publishing
1. Import `mqttPublish` from `mqtt.service.ts`
2. Call `await mqttPublish(topic, JSON.stringify(payload))`
3. Topic must use `env.MQTT_BASE_TOPIC`; log important events

### Adding a new sensor type to telemetry ingestion
1. Device publishes to `{MQTT_BASE_TOPIC}/{deviceId}/sensors/{category}/{name}` or `.../power/{name}`
2. MQTT service automatically parses topic and extracts sensor tag
3. Payload validated as numeric, then written to InfluxDB with combined sensor tag
4. No code changes needed — it just works with the existing pipeline!
5. See `mqtt.service.ts` lines 87–113 for implementation

### Updating system configuration
1. Modify `prisma/schema.prisma` — add field to `SystemConfig` model with `@default(...)` for sensible defaults
2. Run `npx prisma migrate dev --name add_<field>`
3. In `api.routes.ts` POST `/config`: add field to Zod schema
4. GET `/config` automatically creates config with defaults if missing
4. In `mqtt.service.ts`: extend sensor parsing if config affects telemetry handling
5. GET `/config` automatically creates config with defaults if missing

### Debugging MQTT messages
- All MQTT activity logged via pino at info/error level
- Check terminal output for "Connected to MQTT broker", topic subscriptions, and message parsing errors
- Use external MQTT client (e.g., MQTT Explorer) to inspect raw broker traffic
- Enable log level via `LOG_LEVEL=debug` env var

## Project-Specific Gotchas

1. **MQTT_BASE_TOPIC is configurable** — Never hardcode `"nfthydro1337"`; use `env.MQTT_BASE_TOPIC`
2. **Device IDs are case-sensitive** in MQTT topics and DB uniqueness constraint
3. **Prisma client must be re-instantiated per route file with adapter** (not shared globally) — uses `@prisma/adapter-pg` for connection pooling. Pass `{ adapter }` to PrismaClient constructor. **Prisma 7 requirement**: Database URL must be in `prisma.config.ts`, not in schema.prisma.
4. **Socket.IO broadcasts are fire-and-forget** — no acknowledgment if client disconnects during message
5. **OTA private key is not committed to git** — stored in `firmware/data/` and must be provided at runtime
6. **InfluxDB Flux queries are async** — telemetry history endpoint needs QueryApi implementation
7. **Express error handling is not global** — wrap route handlers in try-catch or use error middleware (TODO: add)

## Validation & Testing Checklist

Before submitting code:
- [ ] All env variables used are defined in `.env.example`
- [ ] Zod schemas validate user inputs and MQTT payloads
- [ ] Error messages logged, not swallowed
- [ ] MQTT topics use `env.MQTT_BASE_TOPIC` (not hardcoded)
- [ ] No implicit `any` types in TypeScript
- [ ] PrismaClient connections properly closed (or use connection pooling)
- [ ] Socket.IO emissions broadcast correct payload shape
- [ ] RSA signatures use correct algorithm (RSA-SHA256 in OTA)

## Future Enhancements & TODOs

- [ ] Implement Flux query in telemetry history endpoint (`GET /api/devices/:deviceId/telemetry`)
- [ ] Add device last_seen automatic update on heartbeat/status messages
- [ ] Add global Express error middleware for consistent error responses
- [ ] Add authentication/authorization (JWT or API keys)
- [ ] Add unit tests for services and route handlers
- [ ] Add e2e tests simulating MQTT device messages
- [ ] Implement analytics/alerting rules based on telemetry thresholds
- [ ] Add metrics endpoint (`/metrics`) for Prometheus scraping
