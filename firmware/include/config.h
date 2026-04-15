/**
 * @file config.h
 * @brief System-wide configuration and constants
 * 
 * Production-grade hydroponic control system configuration.
 * Modify this file to adapt the system to your specific setup.
 */

#ifndef CONFIG_H
#define CONFIG_H

#ifdef MQTT_KEEPALIVE
  #undef MQTT_KEEPALIVE
#endif
#define MQTT_KEEPALIVE 60

#include <Arduino.h>
#include <Preferences.h>


// ============================================================================
// SYSTEM IDENTIFICATION
// ============================================================================
#define SYSTEM_NAME "HydroNode_01"
#ifndef FIRMWARE_VERSION
#define FIRMWARE_VERSION "1.0.0"
#endif
#define HARDWARE_REVISION "ESP-32D"

// ============================================================================
// SYSTEM SECURITY
// ============================================================================
// UNCOMMENT TO LOCK DOWN SYSTEM
#define ENFORCE_STRICT_SECURITY 

#ifdef ENFORCE_STRICT_SECURITY
    #define ALLOW_HTTP_OTA false
    #define REQUIRE_SIGNED_FIRMWARE true
#else
    #define ALLOW_HTTP_OTA true
    #define REQUIRE_SIGNED_FIRMWARE false
#endif

// --- Transport Security Configurations ---
#define MQTT_USE_TLS true               // true: use WiFiClientSecure (8883), false: use WiFiClient (1883)
#define MQTT_ALLOW_INSECURE_TLS false   // true: skip cert validation (setInsecure), false: verify CA
#define MQTT_USE_CA_CERT true           // true: load CA from LittleFS
#define MQTT_CA_FILENAME "/mqtt_ca.pem" // For MQTT Broker (e.g., HiveMQ)
#define OTA_CA_FILENAME "/ota_ca.pem"   // For your OTA Server (e.g., GitHub, AWS)
#define OTA_PUBKEY_FILENAME "/ota_pub.pem" // To sign Firmware

// OTA CA Verification Mode
// ─────────────────────────────────────────────────────────────────────────────
// true  → Full X.509 chain verification. Use with a real CA (Let's Encrypt,
//         AWS, GitHub Releases). The ota_ca.pem must be a proper CA cert.
// false → TLS encryption is used but CA is NOT verified (setInsecure).
//         Safe for local/self-signed servers — firmware integrity is still
//         guaranteed by RSA-SHA256 signature and SHA256 partition check.
//         ⚠ Only use false on a trusted local network.
// ─────────────────────────────────────────────────────────────────────────────
#define OTA_VERIFY_CA false


// ============================================================================
// WIFI CONFIGURATION
// ============================================================================
#define WIFI_SSID "SSID"
#define WIFI_PASSWORD "PASSWORD"
#define WIFI_CONNECT_TIMEOUT 30000  // 30 seconds
#define WIFI_RECONNECT_INTERVAL 60000  // 1 minute

// ============================================================================
// MQTT CONFIGURATION
// ============================================================================
#define MQTT_BROKER "broker.hivemq.com"  // Public broker for testing
#define MQTT_PORT_TLS 8883
#define MQTT_PORT_PLAIN 1883
#define MQTT_USER ""  // Leave empty for public brokers
#define MQTT_PASSWORD ""
#define MQTT_CLIENT_ID SYSTEM_NAME
#define MQTT_KEEPALIVE 60
#define MQTT_QOS 1
#define MQTT_RETAIN true

#if MQTT_USE_TLS
    #define MQTT_PORT MQTT_PORT_TLS
#else
    #define MQTT_PORT MQTT_PORT_PLAIN
#endif

// MQTT Topics (hierarchical structure)
#define MQTT_BASE_TOPIC "HydroOne"
#define MQTT_DEVICE_TOPIC MQTT_BASE_TOPIC "/" SYSTEM_NAME

// Telemetry topics
#define TOPIC_STATUS MQTT_DEVICE_TOPIC "/status"
#define TOPIC_SENSORS MQTT_DEVICE_TOPIC "/sensors"
#define TOPIC_WATER_TEMP MQTT_DEVICE_TOPIC "/sensors/water/temperature"
#define TOPIC_AIR_TEMP MQTT_DEVICE_TOPIC "/sensors/air/temperature"
#define TOPIC_AIR_HUMIDITY MQTT_DEVICE_TOPIC "/sensors/air/humidity"
#define TOPIC_PRESSURE MQTT_DEVICE_TOPIC "/sensors/air/pressure"
#define TOPIC_WATER_LEVEL MQTT_DEVICE_TOPIC "/sensors/water/level"
#define TOPIC_WATER_LEVEL_PERCENT MQTT_DEVICE_TOPIC "/sensors/water/level_percent"
#define TOPIC_WATER_LEVEL_ADC MQTT_DEVICE_TOPIC "/sensors/water/level_adc"
#define TOPIC_WATER_LEVEL_LITRES MQTT_DEVICE_TOPIC "/sensors/water/level_litres"
#define TOPIC_RESERVOIR_DISTANCE MQTT_DEVICE_TOPIC "/sensors/reservoir/distance"
#define TOPIC_PH MQTT_DEVICE_TOPIC "/sensors/water/ph"
#define TOPIC_EC MQTT_DEVICE_TOPIC "/sensors/water/ec"
#define TOPIC_SENSOR_STATUS MQTT_DEVICE_TOPIC "/sensors/status"
#define TOPIC_BATTERY MQTT_DEVICE_TOPIC "/power/battery"

// Control topics (subscribe)
#define TOPIC_CMD_PUMP MQTT_DEVICE_TOPIC "/cmd/pump"
#define TOPIC_CMD_MODE MQTT_DEVICE_TOPIC "/cmd/mode"
#define TOPIC_CMD_CONFIG MQTT_DEVICE_TOPIC "/cmd/config"
#define TOPIC_CMD_OTA MQTT_DEVICE_TOPIC "/cmd/ota"
#define TOPIC_CMD_TANK MQTT_DEVICE_TOPIC "/cmd/tank"
#define TOPIC_CMD_ENV MQTT_DEVICE_TOPIC "/cmd/env"
#define TOPIC_CMD_TEST MQTT_DEVICE_TOPIC "/cmd/test"
#define TOPIC_CMD_SENSORS MQTT_DEVICE_TOPIC "/cmd/sensors"
#define TOPIC_CMD_PH MQTT_DEVICE_TOPIC "/cmd/ph"
#define TOPIC_CMD_EC MQTT_DEVICE_TOPIC "/cmd/ec"

// Diagnostic topics
#define TOPIC_DIAGNOSTICS MQTT_DEVICE_TOPIC "/diagnostics"
#define TOPIC_ERRORS MQTT_DEVICE_TOPIC "/errors"
#define TOPIC_HEARTBEAT MQTT_DEVICE_TOPIC "/heartbeat"

// ============================================================================
// POWER MANAGEMENT
// ============================================================================
#define VOLTAGE_DIVIDER_R1 30000.0 //100000.0
#define VOLTAGE_DIVIDER_R2 7500.0  //20000.0

// ============================================================================
// SENSOR PINS (ESP32 Dev Board)
// ============================================================================
// OneWire sensors
#define PIN_ONEWIRE 4  // DS18B20 water temperature

// I2C sensors (BMP280/BME280) - Standard ESP32 I2C pins
#define PIN_SDA 21
#define PIN_SCL 22

// DHT11/DHT22 (Air temperature and humidity)
#define PIN_DHT 4
#define DHT_TYPE DHT11
//#define DHT_TYPE DHT22 // If using DHT22

// Analog sensors (Must use ADC1 to work alongside WiFi)
#define PIN_WATER_LEVEL 35      // ADC1_CH7 (Input only)
#define PIN_BATTERY_VOLTAGE 34  // ADC1_CH6 (Input only - via voltage divider)

// Digital sensors
#define PIN_HC_SR04_TRIGGER 13
#define PIN_HC_SR04_ECHO 12

// pH and EC sensors
#define PIN_PH_SENSOR 32  // ADC1_CH4
#define PIN_EC_SENSOR 33  // ADC1_CH5

// ============================================================================
// RELAY & SHIFT REGISTER CONFIGURATION
// ============================================================================
// SPI Pins for 74HC595 (Using VSPI defaults for ESP32)
#define PIN_SR_DATA  23  // MOSI (DS)
#define PIN_SR_CLOCK 18  // SCK (SHCP)
#define PIN_SR_LATCH 5   // CS (STCP)
//#define PIN_SR_OE    17  // Output Enable (Active Low) - Optional but recommended for glitch prevention

#define USE_SHIFT_REGISTER true  // Set to false to use direct GPIO control (not recommended for more than 2 relays)
// Logical Relay IDs (Maps to bit positions 0-31)
enum RelayID : uint8_t {
    RELAY_MAIN_PUMP = 0,
    RELAY_PH_UP = 1,
    RELAY_PH_DOWN = 2,
    RELAY_NUTRIENT_A = 3,
    RELAY_NUTRIENT_B = 4,
    RELAY_SEC_PUMP = 5,
    RELAY_LIGHT = 6,
    RELAY_FAN = 7,
    // Add up to 31 for a 4-chained 74HC595 setup
};
constexpr int RELAY_MAX = 31; // set to (max enum value)+1

// Bitmask defining which relays are Active LOW. 
// 1 = Active LOW, 0 = Active HIGH.
// Example: Main pump (0) and Fan (7) are Active Low -> Bits 0 and 7 are 1.
// #define RELAY_ACTIVE_LOW_MASK 0b10000001
#define RELAY_ACTIVE_LOW_MASK 0b10000001

// If not using shift register, define direct GPIO pins for each relay (must be unique and valid GPIOs)
#define MAIN_PUMP_RELAY 26
#define PIN_RELAY_PUMP1 25
#define PIN_RELAY_PUMP2 14
#define PIN_RELAY_PUMP3 27   // Moved from 12 to avoid conflict with Echo
#define PIN_RELAY_PUMP4 2
#define PIN_RELAY_LIGHT 19   // Moved from 13 to avoid conflict with Trigger
#define PIN_RELAY_FAN 15
#define PIN_RELAY_AUX 0    // Moved from 27

// ============================================================================
// SENSOR CONFIGURATION
// ============================================================================
// DS18B20
#define DS18B20_RESOLUTION 12  // 9-12 bits (12 = 0.0625°C resolution)
#define WATER_TEMP_MIN -10.0
#define WATER_TEMP_MAX 50.0

// DHT11/DHT22
#define AIR_TEMP_MIN -20.0
#define AIR_TEMP_MAX 60.0
#define HUMIDITY_MIN 0.0
#define HUMIDITY_MAX 100.0

// BMP280/BME280
#define PRESSURE_MIN 950.0  // hPa
#define PRESSURE_MAX 1050.0

// Ultrasonic Sensor Selection
#define ULTRASONIC_HC_SR04 1
#define ULTRASONIC_JSN_SR04T 2
#define ULTRASONIC_A02YYUW 3

#define ULTRASONIC_SENSOR_TYPE ULTRASONIC_JSN_SR04T // Set to ULTRASONIC_A02YYUW for UART-based sensors

// HC-SR04/JSN-SR04T
#define ULTRASONIC_MAX_DISTANCE 200  // cm
#define ULTRASONIC_TIMEOUT 30000  // microseconds

#if ULTRASONIC_SENSOR_TYPE == ULTRASONIC_JSN_SR04T
    #define ULTRASONIC_TRIGGER_PULSE_US 20
#else
    #define ULTRASONIC_TRIGGER_PULSE_US 10
#endif

// Water level thresholds
#define WATER_LEVEL_EMPTY 100  // ADC value (calibrate)
#define WATER_LEVEL_LOW 500
#define WATER_LEVEL_NORMAL 1500
#define WATER_LEVEL_HIGH 3000
#define WATER_LEVEL_FULL 4000

// pH sensor (calibrate when sensor is installed)
#define PH_MIN 0.0
#define PH_MAX 14.0
#define PH_CALIBRATION_OFFSET 0.0
/** Default linear map pH = PH_DEFAULT_SLOPE * V + PH_DEFAULT_OFFSET (typical analog conditioner ~2.5V @ pH7) */
#define PH_DEFAULT_SLOPE (-6.0f)
#define PH_DEFAULT_OFFSET (22.0f)

// EC sensor (calibrate when sensor is installed)
#define EC_MIN 0.0  // mS/cm
#define EC_MAX 5.0
#define EC_CALIBRATION_FACTOR 1.0
/** Linear temp coefficient for conductivity vs 25 °C (common approximation; adjust per probe datasheet). */
#define EC_TEMP_COEFF 0.019f
#define EC_DEFAULT_DRY_VOLTAGE 0.05f
#define EC_DEFAULT_SCALE 2.0f

// ============================================================================
// TIMING CONFIGURATION
// ============================================================================
#define HEARTBEAT_INTERVAL 60000  // 1 minute
#define ERROR_CHECK_INTERVAL 1000  // 1 second

// ============================================================================
// SAFETY LIMITS
// ============================================================================
#define MAX_CONSECUTIVE_ERRORS 10
#define SENSOR_TIMEOUT_MS 5000
#define MQTT_RECONNECT_ATTEMPTS 3

// ============================================================================
// LOGGING
// ============================================================================
#define LOG_LEVEL_ERROR 0
#define LOG_LEVEL_WARNING 1
#define LOG_LEVEL_INFO 2
#define LOG_LEVEL_DEBUG 3
#define LOG_LEVEL_VERBOSE 4

#ifndef LOG_LEVEL
#define LOG_LEVEL LOG_LEVEL_DEBUG //LOG_LEVEL_DEBUG  // Default log level
#endif

// Log macros
#define LOG_ERROR(msg, ...) if(LOG_LEVEL >= LOG_LEVEL_ERROR) Serial.printf("[ERROR] " msg "\n", ##__VA_ARGS__)
#define LOG_WARN(msg, ...) if(LOG_LEVEL >= LOG_LEVEL_WARNING) Serial.printf("[WARN] " msg "\n", ##__VA_ARGS__)
#define LOG_INFO(msg, ...) if(LOG_LEVEL >= LOG_LEVEL_INFO) Serial.printf("[INFO] " msg "\n", ##__VA_ARGS__)
#define LOG_DEBUG(msg, ...) if(LOG_LEVEL >= LOG_LEVEL_DEBUG) { Serial.printf("[DEBUG] " msg "\n", ##__VA_ARGS__); Serial.flush();}
#define LOG_VERBOSE(msg, ...) if(LOG_LEVEL >= LOG_LEVEL_VERBOSE) Serial.printf("[VERBOSE] " msg "\n", ##__VA_ARGS__)

// ============================================================================
// SYSTEM STATES
// ============================================================================
enum SystemState {
    STATE_INIT,
    STATE_ACTIVE,
    STATE_SLEEP,
    STATE_EMERGENCY,
    STATE_MAINTENANCE,
    STATE_OTA_UPDATE
};

enum PumpState {
    PUMP_OFF,
    PUMP_ON,
    PUMP_COOLDOWN,
    PUMP_ERROR
};

enum ConnectionState {
    CONN_DISCONNECTED,
    CONN_CONNECTING,
    CONN_CONNECTED,
    CONN_ERROR
};

enum TankShape : uint8_t {
    RECTANGULAR = 0,
    CYLINDRICAL = 1
};

/* Default tank configuration */
#define DEFAULT_TANK_TYPE RECTANGULAR
#define DEFAULT_TANK_DIM_A 100.0   // cm (Length or Radius)
#define DEFAULT_TANK_DIM_B 50.0    // cm (Width, unused for cylinder)
#define DEFAULT_TANK_FULL_H 100.0  // cm
#define DEFAULT_TANK_EMPTY_D 120.0 // cm (sensor -> bottom when empty)


// ============================================================================
// DATA STRUCTURES
// ============================================================================
struct SensorData {
    float waterTemp;
    float airTemp;
    float humidity;
    float pressure;
    //uint16_t waterLevel;
    float waterLevel;
    uint16_t waterLevelADC;
    float reservoirDistance;
    float pH;
    float ec;
    float batteryVoltage = 12.01;
    unsigned long timestamp;
    bool valid;
    //float tankVolumeLitres; // New: Current liters
    //float tankFillPercent;  // New: 0 to 100%
    float waterLevelLitres; // New: Current liters
    float waterLevelPercent; //New: 0 to 100%
};

struct SystemStatus {
    SystemState state;
    ConnectionState wifiState;
    ConnectionState mqttState;
    PumpState pumpState;
    uint8_t errorCount;
    unsigned long uptime;
    unsigned long lastSleepTime;
};


struct SystemConfig {
    // Power & Timing Configuration
    // ------------------------------------------------------------
    // These settings control how the system saves power and
    // when it enters deep sleep to protect the battery.
    
    bool deepSleepEnabled = false;      
    // If true → device will enter deep sleep when battery is low/critical
    // Useful for solar-powered autonomous systems
    
    uint32_t sleepDurationSec = 300;    
    // How long the device sleeps before waking up again (seconds)
    // Example: 300s = wake up every 5 minutes
    
    uint32_t activeDurationMs = 60000;  
    // How long the system stays awake after boot (milliseconds)
    // Example: 60000ms = 1 minute active time for sensors + communication
    
    // ------------------------------------------------------------
    // Battery Protection Thresholds (VERY IMPORTANT)
    // ------------------------------------------------------------
    // These values MUST match your battery type.
    
    // For 12V AGM / GEL (lead-acid solar battery):
    // batteryLowThreshold     = 12.1V  → early warning (~40–50% capacity)
    // batteryCriticalThreshold= 11.6V  → emergency shutdown to avoid damage
    //
    // For 12V LiFePO4 (4S battery pack):
    // batteryLowThreshold     = 12.4V  → early warning (~20–30%)
    // batteryCriticalThreshold= 11.6V  → safe cutoff region
    
    float batteryLowThreshold = 12.1;      
    // Warning level: start reducing load / notify user & enter light sleep
    
    float batteryCriticalThreshold = 11.6; 
    // Emergency level: enter deep sleep to protect battery

    uint32_t sensorReadInterval = 5000;
    uint32_t mqttPublishInterval = 10000;

    uint32_t batteryLowCooldown = 600;        // 10 mins
    uint32_t batteryLowMqttInterval = 300000; // 5 mins = 300k ms
    uint32_t solarRecoverySleep = 3600;       // 1 hour
    uint32_t sleepThreshold = 300;            // 5 mins to decide Light vs Deep
    uint32_t envStabilizationSleep = 1800;    // Sleep duration when sensors detect unsafe environment

    // Safety & Environment
    float emergencyShutdownTemp = 45.0;
    float phTargetMin = 5.5;
    float phTargetMax = 6.5;
    float ecTargetMin = 1.2;
    float ecTargetMax = 2.0;

    // Pump control
    uint32_t pumpMinOnTime = 5000;     // Minimum 5 seconds
    uint32_t pumpMaxOnTime = 300000;   // Maximum 5 minutes
    uint32_t pumpCooldownTime = 120000; // 2 minutes between runs

    // ---- Environment Control (optional features) ----
    // Fan: set fanEnabled=false if you have no fan relay connected
    bool fanEnabled = true;
    bool fanAutoMode = true;          // If false, fan is controlled manually via MQTT (overrides temp control)
    float airTempMax = 35.0;           // °C — fan turns ON above this
    float fanHysteresis = 1.0;         // °C — fan turns OFF at (airTempMax - hysteresis)

    // pH Dosing: set dosingEnabled=false if you have no peristaltic dosing pumps
    bool dosingEnabled = false;
    uint32_t dosingPulseMs = 2000;     // How long the dosing relay stays ON per pulse
    uint32_t dosingLockoutMs = 300000; // 5 min lockout between doses to allow mixing

    // Nutrient A/B Dosing: set nutrientDosingEnabled=false if no A/B peristaltic pumps
    bool nutrientDosingEnabled = false;
    uint32_t nutrientDoseDelayMs = 5000; // Delay between A and B pulses (prevent mixing in line)

    // Lighting: set lightingEnabled=false if using sunlight / no grow light relay
    bool lightingEnabled = false;
    //bool lightAutoMode = true;          // If false, lights are controlled manually via MQTT (overrides schedule)
    uint8_t lightOnHour = 6;           // 24h format — lights ON at this hour
    uint8_t lightOffHour = 22;         // 24h format — lights OFF at this hour

    // Tank Geometry
    uint8_t tankType = 0; // RECTANGULAR
    float tankDimA = 100.0;
    float tankDimB = 50.0;
    float tankFullH = 100.0;
    float tankEmptyD = 120.0;

    // Test
    bool testCommandsEnabled = false;

    // Analog pH: pH = phSlope * V + phOffset (V at ADC pin, 0–3.3 V)
    float phSlope = PH_DEFAULT_SLOPE;
    float phOffset = PH_DEFAULT_OFFSET + PH_CALIBRATION_OFFSET;
    // Analog EC: ec = max(0, (V - ecDryVoltage)) * ecScale, then temp-compensated to 25 °C
    float ecDryVoltage = EC_DEFAULT_DRY_VOLTAGE;
    float ecScale = EC_DEFAULT_SCALE * EC_CALIBRATION_FACTOR;

    // Recovery defaults (set by constructor, updated after loadConfiguration)
    uint32_t defaultPumpCooldown;
    uint32_t defaultMqttInterval;
    SystemConfig() {
        defaultPumpCooldown = pumpCooldownTime;
        defaultMqttInterval = mqttPublishInterval;
    }
};

extern SystemConfig sysConfig;
void loadConfiguration();
void saveConfiguration();

#endif // CONFIG_H
