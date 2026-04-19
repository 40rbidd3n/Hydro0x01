# Changelog

All notable changes to HydroponicOne will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- VPD (Vapor Pressure Deficit) calculation and monitoring
- DLI (Daily Light Integral) tracking with PAR sensors
- Master/Slave architecture with LoRa communication
- Hydroponic system type selection (DWC, NFT, Ebb & Flow, etc.)
- AI-powered dashboard assistant
- Camera integration for plant health monitoring

### Changed
- Improved EnvironmentManager with MQTT alert publishing
- Enhanced dosing safety with relay failsafe timeouts

### Fixed
- EC high warning now triggers MQTT alerts (not just logs)

## [1.0.0] - 2026-04-14

### Added
- Initial ESP32 firmware release
- Multi-sensor support (pH, EC, DHT22, DS18B20)
- MQTT telemetry publishing
- Automated pH and nutrient dosing
- Environmental control (fans, lighting)

---

For a complete list of changes, see [GitHub Releases](https://github.com/40rbidd3n/Hydro0x01/releases).
