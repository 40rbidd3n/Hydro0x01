# Firmware Guide

The HydroOne firmware is the heart of your edge device. It is designed to be robust, memory-safe, and highly configurable.

## 🛠️ Environment Setup

We recommend using **VS Code** with the **PlatformIO** extension.

1.  Clone the repository.
2.  Open the `firmware/` folder in VS Code.
3.  PlatformIO will automatically download the required libraries.

## ⚙️ Configuration (`config.h`)

Before flashing, you must configure your credentials and hardware setup in `firmware/include/config.h`.

### 1. Network & MQTT
```cpp
#define WIFI_SSID "Your_SSID"
#define WIFI_PASSWORD "Your_Password"
#define MQTT_BROKER "your-broker.com"
#define MQTT_PORT 1883
```

### 2. Advanced Security (OTA Signing)
For production deployments, we strongly recommend enabling **Strict Security**. This requires all firmware to be cryptographically signed.
- 🔐 [**Security & OTA Guide**](./08_SECURITY_OTA.md) — How to generate keys and sign binaries.

### 3. Sensor Selection & Build Environments
You must build the firmware version that matches your hardware setup. HydroOne uses **PlatformIO environments** to compile only the necessary drivers, saving memory.

In `platformio.ini`, select your Default Environment (`default_envs`) or build a specific one:
- **`esp32_dht_bmp`**: Combines a DHT11/22 and a BMP280.
- **`esp32_bme280`**: Uses a single BME280 for Temp/Hum/Pressure.
- **`esp32_dht_only`**: Uses only a DHT sensor.
- **`esp32_bmp280_only`**: Uses only a BMP280.

**Ultrasonic Sensors** are configured via `config.h`:
- Set `ULTRASONIC_SENSOR_TYPE` to `ULTRASONIC_HC_SR04`, `ULTRASONIC_JSN_SR04T` (Recommended), or `ULTRASONIC_A02YYUW`.

## 🔄 OTA (Over-The-Air) Updates

HydroOne supports secure remote updates. To deploy a new version:
1.  Increase the `VERSION` define in `config.h`.
2.  Build the binary: `pio run`.
3.  Upload the `.bin` file via the HydroOne Dashboard.

## 🧠 Control Logic & Dosing

HydroOne uses a reactive control loop to maintain reservoir parameters.

```mermaid
graph TD
    Start((Loop Start)) --> Read[Read Sensors]
    Read --> CheckMode{Mode == ACTIVE?}
    
    CheckMode -- "NO" --> Sleep[Wait for Interval]
    CheckMode -- "YES" --> EvalPH{pH > Threshold?}
    
    EvalPH -- "YES" --> DosePH[Dose pH Down]
    EvalPH -- "NO" --> EvalEC{EC < Threshold?}
    
    EvalEC -- "YES" --> DoseNut[Dose Nutrient A/B]
    EvalEC -- "NO" --> ResLevel{Level < Critical?}
    
    ResLevel -- "YES" --> Alert[Publish Alert / Stop Pump]
    ResLevel -- "NO" --> Sleep
    
    DosePH --> Cooldown[Wait for Mixing Cooldown]
    DoseNut --> Cooldown
    Cooldown --> Sleep
    Sleep --> Start
```

### Sensor Integration
The firmware uses a hardware-agnostic `SensorManager` that polls data into a `SensorData` struct.

## 🧪 Best Practices
- **Calibrate early**: Use the dashboard's calibration tools for pH and EC before relying on readings.
- **Power Management**: If running on batteries, ensure `USE_DEEP_SLEEP` is correctly configured.

---

### Next Steps:
Configure your Integrations in [**Step 4: Integration Guide**](./04_INTEGRATION_GUIDE.md).
