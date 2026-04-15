# HydroOne Tools

## simulator.py

A CLI simulator that publishes fake ESP32 telemetry on the exact MQTT topic
schema used by HydroOne firmware. Use this to develop and demo the full stack
without physical hardware.

### Install

```bash
# Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r tools/requirements.txt
```

### MQTT Broker (Mosquitto)

The simulator needs a running MQTT broker. Install and start Mosquitto:

**macOS:**
```bash
brew install mosquitto

# Start the broker (use the full path — brew may not symlink it)
/usr/local/Cellar/mosquitto/2.1.2/sbin/mosquitto
```

> Note: on Apple Silicon Macs the path may be `/opt/homebrew/sbin/mosquitto`.
> Run `find /usr/local /opt/homebrew -name mosquitto -type f 2>/dev/null` if
> neither works.

**Linux:**
```bash
sudo apt install mosquitto
mosquitto
```

### Usage

```bash
# Offline demo — no broker needed
python tools/simulator.py --no-mqtt

# Against a local Mosquitto broker
python tools/simulator.py --broker localhost:1883

# Against the public test broker
python tools/simulator.py --broker test.mosquitto.org:1883
```

### Verify it's working

In a second terminal, subscribe to all HydroOne topics:

```bash
mosquitto_sub -h localhost -t "HydroOne/#" -v
```

You should see all 9 sensor topics streaming every 2 seconds.

### Keyboard controls

| Key | Action           |
|-----|------------------|
| `1` | Inject pH crash  |
| `2` | Inject EC depletion |
| `3` | Inject temp spike |
| `4` | Pump on          |
| `5` | Pump off         |
| `6` | Low water event  |
| `r` | Reset all faults |
| `q` | Quit             |
