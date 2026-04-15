# Troubleshooting

Use this guide to resolve common issues with HydroponicOne.

## 📡 Connectivity Issues

### MQTT "Connection Refused"
- **Check Broker Health**: Ensure your broker (e.g., HiveMQ, Mosquitto) is online.
- **Port Settings**: Confirm you are using 1883 (Non-TLS) or 8883 (TLS).
- **Credentials**: Double-check `MQTT_USER` and `MQTT_PASS` in `config.h`.

### Device is "Offline" in Dashboard
- **Heartbeat**: check if the blue LED (if configured) is blinking.
- **WiFi Strength**: ESP32s can have poor range. Distance from router should be minimized.
- **Deep Sleep**: If `USE_DEEP_SLEEP` is on, the device only appears online during its wake cycle.

## 🧪 Sensor Issues

### Readings are `NaN` or `0.0`
- **I2C Bus Error**: Check SCL/SDA wiring. Ensure pull-up resistors (4.7kΩ) are present if the module doesn't have them.
- **Conflict**: Verify no other sensor is sharing the same GPIO (except I2C/OneWire buses).
- **Sensor Type**: Ensure `ULTRASONIC_SENSOR_TYPE` or `DHT_TYPE` matches your actual hardware.

### Ultrasonic Values are Jumpy
- **JSN-SR04T Blind Spot**: This sensor cannot read closer than 20-25cm. Ensure it is mounted high enough.
- **Reflections**: Ensure no pump tubes or cables are in the sensor's field of view.

### pH/EC Values drifting
- **Ground Loops**: Ensure your reservoir is properly grounded or use an isolated power supply for the probes.
- **Calibration**: Re-run the [Calibration Guide](./05_CALIBRATION_GUIDE.md).

## 💻 Dashboard/Backend Issues

### No Data in Charts
- **InfluxDB Token**: Verify your `INFLUX_TOKEN` in `backend/.env`.
- **Bucket Names**: Ensure the bucket exists in your InfluxDB instance.

### Commands Not Working
- **Topic Prefix**: ensure your `MQTT_BASE_TOPIC` matches between firmware and backend.

---

### Still stuck?
Open an issue on GitHub or join our community Discord!
