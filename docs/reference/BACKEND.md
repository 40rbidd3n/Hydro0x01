# Backend Architecture (Fastify)

The backend is built with Fastify, utilizing full TypeScript strictures and Zod type-provisioning.

### Plugins
- `mqtt.plugin.ts`: Manages single global MQTT connection wrapping Mosquitto/HiveMQ.
- `socket.plugin.ts`: Wrapper for `socket.io` enabling broadcast endpoints.
- `prisma.plugin.ts`: Global PrismaClient instance for PostgreSQL connections (configs, logs).
- `influx.plugin.ts`: Global InfluxDB WriteApi instance for telemetry ingest.

`services/socket.ts` connects to Fastify. Upon receiving `telemetry:update` payloads, it pushes directly into the Zustand store. React components passively listen to these hook changes and re-render efficiently.

```mermaid
graph TD
    subgraph "Data Stream"
        Socket["socket.service.ts"]
        API["api.service.ts"]
    end

    subgraph "Central State (Zustand)"
        Store["useHydroStore.ts"]
        T_State["Telemetry State"]
        C_State["Config State"]
        Store --- T_State
        Store --- C_State
    end

    subgraph "React Components (UI)"
        Dash["Dashboard.tsx"]
        Sensors["SensorCard.tsx"]
        Controls["ControlPanel.tsx"]
    end

    %% Flow
    Socket -- "telemetry:update" --> Store
    API -- "fetch/update" --> Store
    
    Store -- "selector" --> Sensors
    Sensors -- "render" --> Dash
    Controls -- "trigger" --> API
```

### Modules Layout
- `telemetry/`: Subscribes to MQTT telemetry topics, validates schema using Zod, writes to Influx, and pushes updates via Socket.IO.
- `config/`: CRUD interface for `SystemConfig` managed via Prisma.
- `system/`: Command endpoints to activate Relays, Pumps, or Dosing logic. Triggers MQTT payload dispatch and inserts `ActuationLog` via Prisma.

### Models
- **SystemConfig**: Stores device settings (target pH, dosing thresholds, MQTT credentials).
- **SystemAlert**: Tracks diagnostic issues and health status across devices.
- **ActuationLog**: Records every time a relay or pump is triggered (manual or automated).

```mermaid
erDiagram
    SystemConfig {
        string device_id PK
        string name
        float batteryLowThreshold
        int sensorReadInterval
    }
    SystemAlert {
        int id PK
        string status
        string message
        datetime created_at
    }
    ActuationLog {
        int id PK
        string action
        int duration
        string result
        datetime timestamp
    }
    
    SystemConfig ||--o{ SystemAlert : "monitors"
    SystemConfig ||--o{ ActuationLog : "controls"
```

```mermaid
graph TD
    subgraph "Fastify Registry"
        App["app.ts (Root)"]
        PluginRegistry["Plugins / Hooks"]
    end

    subgraph "Core Plugins"
        PrismaPlg["prisma.plugin"]
        MqttPlg["mqtt.plugin"]
        SocketPlg["socket.plugin"]
        InfluxPlg["influx.plugin"]
    end

    subgraph "Functional Modules"
        TeleMod["Telemetry Module"]
        ConfMod["Config Module"]
        SysMod["System Module"]
    end

    %% Dependency Flow
    App -- "registers" --> PluginRegistry
    PluginRegistry -- "injects" --> PrismaPlg
    PluginRegistry -- "injects" --> MqttPlg
    
    MqttPlg -- "pub/sub" --> TeleMod
    TeleMod -- "broadcast" --> SocketPlg
    TeleMod -- "persist" --> InfluxPlg

    ConfMod -- "query" --> PrismaPlg
    SysMod -- "command" --> MqttPlg
    SysMod -- "audit" --> PrismaPlg
```

### Environment Requirements
Refer to `.env.example`. Requires MQTT broker access, PostgreSQL DB, and InfluxDB token.
