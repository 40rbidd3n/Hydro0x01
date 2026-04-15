# Modular Sensor Architecture

The HydroponicOne firmware uses a memory-safe, hardware-agnostic architecture for environmental sensors. This design ensures that adding new sensors (like the AHT20) does not require changes to the core business logic or the `SensorManager`.

## Core Principles

1. **No Dynamic Memory Allocation**: The system uses only statically allocated memory at compile-time to prevent heap fragmentation, an essential requirement for long-running embedded systems.
2. **Compile-Time Configuration**: Environments defined in `platformio.ini` select exactly which sensor libraries to include via `build_flags`.
3. **Graceful Degradation**: If an I2C or OneWire bus drops, or a sensor becomes unresponsive, the `read()` function will safely return `false`, allowing the system to log the error without crashing.

## The `IEnvSensor` Interface

All environmental sensors implement the `IEnvSensor` interface located at `firmware/include/sensor/IEnvSensor.h`.

```cpp
class IEnvSensor {
public:
    virtual bool begin() = 0;
    virtual bool read(float& temperature, float& humidity, float& pressure) = 0;
    virtual bool hasHumidity() const = 0;
    virtual bool hasPressure() const = 0;
    virtual const char* getName() const = 0;
    virtual ~IEnvSensor() {}
};
```

This ensures that the `SensorManager` only works with an abstract `IEnvSensor*` pointer, decoupling it from `DHT` or `Adafruit_BMP280` specific logic.

## Supported Sensor Configurations

By modifying `platformio.ini`, you can build for the following setups:

- `esp32_bme280`: Uses a single BME280 for Temperature, Humidity, and Pressure.
- `esp32_dht_bmp`: Combines a DHT11/22 with a BMP280 using the **Composite Sensor Pattern**.
- `esp32_dht_only`: Uses only a DHT sensor (Pressure will return NaN).
- `esp32_bmp280_only`: Uses only a BMP280 sensor (Humidity will return NaN).
- `esp32_mock_env`: Hardware-free testing returning generated valid data.

### Composite Sensors

To support multiple discrete sensors (like using a DHT for humidity and a BMP280 for pressure) without writing monolithic hybrid classes, the system uses the `CompositeEnvSensor`. It accepts two `IEnvSensor*` pointers and aggregates their data.

## I2C Multiplexing

If you run multiple I2C devices with the same address (e.g., two BME280s or a BME280 and an I2C OLED display), you can enable the `TCA9548A` multiplexer by adding `-D USE_I2C_MULTIPLEXER` to your build flags.

The `I2CBusManager` transparently handles selecting channels before initializing and reading from devices on the I2C bus.

## How to Add a New Sensor (e.g., AHT20)

To integrate a new sensor:

1. Create `SensorAHT20.h` and `SensorAHT20.cpp` in `firmware/include/sensor/` and `firmware/src/sensor/`.
2. Wrap the entire contents of both files in `#ifdef USE_AHT20`.
3. Implement the `IEnvSensor` interface in `SensorAHT20`.
4. Define a new environment in `platformio.ini`:
   ```ini
   [env:esp32_aht20]
   build_flags = ${env.build_flags} -D USE_AHT20
   lib_deps = ${env.lib_deps} adafruit/Adafruit AHTX0
   ```
5. Add the compile-time instantiation in `SensorManager.cpp`'s `initEnvSensors()` method:
   ```cpp
   #elif defined(USE_AHT20)
       static SensorAHT20 aht;
       envSensor = &aht;
   ```
