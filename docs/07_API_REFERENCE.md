# REST API & MQTT Reference

This document serves as the complete technical specification for the HydroponicOne API. 

---

## 🌐 REST API (Fastify)

### 🏢 Device Management
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/devices` | `GET` | List all registered devices. |
| `/api/devices/:id` | `GET` | Get combined view (status + latest telemetry). |
| `/api/devices/:id/status` | `GET` | Fetch raw health metrics (WiFi, Heap, Uptime). |
| `/api/devices/:id/telemetry` | `GET` | Query historical telemetry from InfluxDB. |

### ⚙️ Configuration
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/config` | `GET` | Fetch global default configuration. |
| `/api/config` | `POST` | Update config (Target one, all, or global). |
| `/api/devices/:id/config` | `GET` | Fetch device-specific configuration override. |

### 🧪 Sensors & Calibration
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/sensors/status` | `GET` | Fetch detailed sensor state (with optional refresh ping). |
| `/api/calibrate/ph` | `POST` | Trigger pH calibration workflow. |
| `/api/calibrate/ec` | `POST` | Trigger EC calibration workflow. |

### 🕹️ System Control
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/control/pump` | `POST` | Manual pump actuation. |
| `/api/control/mode` | `POST` | Switch between `active` and `maintenance` modes. |
| `/api/control/tank` | `POST` | Configure tank geometry or trigger level calibration. |
| `/api/control/env` | `POST` | Toggle Light/Fan (On/Off/Auto). |
| `/api/control/test` | `POST` | Low-level hardware test (Relays/Sensors). |

### 🔄 Maintenance & Alerts
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/ota/deploy` | `POST` | Dispatch OTA firmware update to a device. |
| `/api/diagnostics` | `GET` | List all unresolved system alerts. |
| `/api/diagnostics/:id` | `DELETE` | Resolve/Acknowledge an alert. |

### Control Topics
| Topic | Direction | Purpose |
| :--- | :--- | :--- |
| `status` | Device -> Cloud | Heartbeat (LWT). |
| `cmd/pump` | Cloud -> Device | Manual pump actuation. |
| `cmd/config` | Cloud -> Device | Update runtime settings. |
| `cmd/ota` | Cloud -> Device | OTA trigger. |
| `cmd/tank` | Cloud -> Device | Tank level calibration. |
| `cmd/env` | Cloud -> Device | Actuator control (Light/Fan). |

For full payload examples, refer to the [**MQTT Guide**](./MQTT_GUIDE.md).