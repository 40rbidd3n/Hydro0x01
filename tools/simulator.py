#!/usr/bin/env python3
"""
HydroOne ESP32 Node Simulator
tools/simulator.py

Publishes fake sensor telemetry on the exact MQTT topic schema used by
HydroOne firmware.  Listens for cmd/ topics and reacts like real hardware.
Run this instead of a physical ESP32 to develop/demo the full stack.

Usage:
    python simulator.py                          # default broker: localhost:1883
    python simulator.py --broker 192.168.1.10   # remote broker
    python simulator.py --broker test.mosquitto.org --port 1883
    python simulator.py --no-mqtt               # offline mode, no broker needed

Controls (keyboard):
    1  pH crash        4  pump on (manual)
    2  EC depletion    5  pump off (manual)
    3  temp spike      6  low water event
    r  reset all faults
    q  quit

Requires:
    pip install paho-mqtt rich
"""

import argparse
import json
import math
import random
import sys
import time
import threading
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# ── Config ────────────────────────────────────────────────────────────────────

BASE_TOPIC   = "HydroOne"
DEVICE_NAME  = "HydroNode_01"
INTERVAL     = 2.0          # seconds between publishes (matches firmware default)
TANK_MAX_L   = 20.0         # reservoir size in litres
TANK_HEIGHT  = 30.0         # cm from sensor to bottom when full

# ── Realistic sensor physics ──────────────────────────────────────────────────

def noise(t, seed, scale=1.0):
    """Layered sine noise — not random, deterministic + repeatable."""
    return (
        math.sin(t * 7.31  + seed)       * 0.60 +
        math.sin(t * 13.71 + seed * 2.3) * 0.30 +
        math.sin(t * 3.17  + seed * 0.9) * 0.10
    ) * scale

class SystemState:
    def __init__(self):
        self.t          = 0.0        # sim time in seconds
        self.start      = time.time()

        # faults injected by keypress
        self.faults     = {}         # key → (magnitude, injected_at)

        # actuator state (updated by cmd/ subscriptions)
        self.pump_on    = False
        self.light_on   = True
        self.fan_on     = False
        self.mode       = "active"

        # persisted log lines
        self.log        = []
        self.mqtt_out   = []

    def elapsed(self):
        return time.time() - self.start

    def inject(self, key, mag):
        self.faults[key] = (mag, self.t)

    def reset(self):
        self.faults = {}

    def _fault(self, key):
        """Return decayed fault value for a given sensor key."""
        if key not in self.faults:
            return 0.0
        mag, t0 = self.faults[key]
        dt = self.t - t0
        decay = math.exp(-dt / 120.0)   # ~2 min half-life
        if decay < 0.01:
            del self.faults[key]
            return 0.0
        return mag * decay

    # ── Sensor values ─────────────────────────────────────────────────────────

    def water_temp(self):
        base = 21.0 + math.sin(self.t * 0.00073) * 2.5
        v = base + noise(self.t * 0.001, 11) * 0.4 + self._fault("temp") * 6.0
        return round(v, 2)

    def air_temp(self):
        base = 24.0 + math.sin(self.t * 0.00073 + 0.8) * 3.0
        v = base + noise(self.t * 0.001, 22) * 0.6
        if self.light_on:
            v += 2.5
        return round(v, 2)

    def air_humidity(self):
        base = 62.0 + math.sin(self.t * 0.00053 + 1.2) * 9.0
        v = base + noise(self.t * 0.001, 33) * 1.8 + self._fault("humidity") * 18.0
        return round(max(10.0, min(99.0, v)), 1)

    def air_pressure(self):
        return round(1013.25 + noise(self.t * 0.0002, 44) * 2.1, 2)

    def ph(self):
        # Slow natural drift downward + pH crash fault
        drift = -(self.t / 86400.0) * 0.08
        base  = 6.1 + drift + noise(self.t * 0.0008, 55) * 0.07
        v = base + self._fault("ph") * (-1.4)
        return round(max(3.5, min(10.0, v)), 2)

    def ec(self):
        # Depletes as plants absorb nutrients
        depletion = max(0.0, 1.0 - (self.t / 604800.0))   # over 7 days
        base = 1.45 * depletion + 0.15
        v = base + noise(self.t * 0.0009, 66) * 0.04 + self._fault("ec") * (-0.6)
        return round(max(0.0, v), 2)

    def level_percent(self):
        # Slowly evaporates, pump refills when on
        base = max(5.0, 78.0 - (self.t / 3600.0) * 1.2)
        if self.pump_on:
            base = min(100.0, base + 0.5)
        v = base + noise(self.t * 0.0005, 77) * 0.8 + self._fault("level") * (-45.0)
        return round(max(0.0, min(100.0, v)), 1)

    def reservoir_distance(self):
        pct = self.level_percent()
        filled_cm = (pct / 100.0) * TANK_HEIGHT
        distance_cm = TANK_HEIGHT - filled_cm
        return round(distance_cm + noise(self.t * 0.001, 88) * 0.3, 1)

    def level_litres(self):
        return round((self.level_percent() / 100.0) * TANK_MAX_L, 2)

    def all_sensors(self):
        return {
            "water_temp":   self.water_temp(),
            "air_temp":     self.air_temp(),
            "humidity":     self.air_humidity(),
            "pressure":     self.air_pressure(),
            "ph":           self.ph(),
            "ec":           self.ec(),
            "distance":     self.reservoir_distance(),
            "level_pct":    self.level_percent(),
            "level_litres": self.level_litres(),
        }

    def status_payload(self):
        return {
            "rssi":      random.randint(-75, -45),
            "heap_free": random.randint(120000, 180000),
            "uptime_s":  int(self.elapsed()),
            "pump":      "ON" if self.pump_on  else "OFF",
            "light":     "ON" if self.light_on else "OFF",
            "fan":       "ON" if self.fan_on   else "OFF",
            "mode":      self.mode,
            "faults":    list(self.faults.keys()),
        }


# ── MQTT helper ───────────────────────────────────────────────────────────────

def full_topic(suffix):
    return f"{BASE_TOPIC}/{DEVICE_NAME}/{suffix}"


def make_client(state):
    if not MQTT_AVAILABLE:
        return None

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f"HydroOne-Sim-{random.randint(1000,9999)}")

    def on_connect(c, userdata, flags, rc, props=None):
        if rc == 0:
            state.log.append(("[green]MQTT connected[/green]", datetime.now()))
            c.subscribe(full_topic("cmd/#"))
        else:
            state.log.append((f"[red]MQTT error rc={rc}[/red]", datetime.now()))

    def on_message(c, userdata, msg):
        topic = msg.topic.split("/")[-1]   # last segment after cmd/
        try:
            payload = json.loads(msg.payload)
        except Exception:
            payload = msg.payload.decode()

        ts = datetime.now()
        state.log.append((f"[cyan]← CMD {topic}[/cyan] {json.dumps(payload)}", ts))

        # Simulate actuator reactions
        if topic == "pump":
            action = payload.get("action", "")
            state.pump_on = (action == "on")
            state.mqtt_out.append(
                (full_topic("status"),
                 json.dumps({"pump": "ON" if state.pump_on else "OFF"}))
            )
        elif topic == "env":
            action = payload.get("action", "")
            if "light_on"  in action: state.light_on = True
            if "light_off" in action: state.light_on = False
            if "fan_on"    in action: state.fan_on   = True
            if "fan_off"   in action: state.fan_on   = False

    client.on_connect = on_connect
    client.on_message = on_message
    return client


# ── Rich TUI ──────────────────────────────────────────────────────────────────

SAFE = {
    "ph":          (5.5, 7.5),
    "ec":          (0.5, 3.5),
    "water_temp":  (15,  28),
    "air_temp":    (15,  35),
    "humidity":    (30,  95),
    "level_pct":   (10,  100),
}

def status_color(key, val):
    if key not in SAFE:
        return "white"
    lo, hi = SAFE[key]
    if val < lo or val > hi:
        return "red"
    margin = (hi - lo) * 0.12
    if val < lo + margin or val > hi - margin:
        return "yellow"
    return "green"


def build_sensor_table(s):
    sensors = s.all_sensors()
    t = Table(box=box.SIMPLE_HEAD, show_header=True, header_style="bold dim",
              expand=True, min_width=38)
    t.add_column("Sensor",  style="dim", width=18)
    t.add_column("Value",   justify="right", width=10)
    t.add_column("Unit",    width=7)
    t.add_column("Status",  width=6)

    rows = [
        ("Water pH",       "ph",         sensors["ph"],         "",        SAFE["ph"]),
        ("Water EC",       "ec",         sensors["ec"],         "mS/cm",   SAFE["ec"]),
        ("Water Temp",     "water_temp", sensors["water_temp"], "°C",      SAFE["water_temp"]),
        ("Air Temp",       "air_temp",   sensors["air_temp"],   "°C",      SAFE["air_temp"]),
        ("Humidity",       "humidity",   sensors["humidity"],   "%",       SAFE["humidity"]),
        ("Air Pressure",   None,         sensors["pressure"],   "hPa",     None),
        ("Tank Level",     "level_pct",  sensors["level_pct"],  "%",       SAFE["level_pct"]),
        ("Tank Litres",    None,         sensors["level_litres"],"L",      None),
        ("US Distance",    None,         sensors["distance"],   "cm",      None),
    ]

    for label, key, val, unit, bounds in rows:
        col = status_color(key, val) if key else "white"
        dot = "●" if col != "white" else "·"
        t.add_row(
            label,
            f"[bold {col}]{val}[/]",
            f"[dim]{unit}[/]",
            f"[{col}]{dot}[/]",
        )
    return t


def build_actuator_panel(s):
    st = s.status_payload()
    lines = []
    lines.append(f"  Pump   [{'green' if st['pump']=='ON' else 'dim'}]{'■' if st['pump']=='ON' else '□'} {st['pump']}[/]")
    lines.append(f"  Light  [{'yellow' if st['light']=='ON' else 'dim'}]{'■' if st['light']=='ON' else '□'} {st['light']}[/]")
    lines.append(f"  Fan    [{'cyan' if st['fan']=='ON' else 'dim'}]{'■' if st['fan']=='ON' else '□'} {st['fan']}[/]")
    lines.append(f"  Mode   [blue]{st['mode']}[/]")
    if st["faults"]:
        lines.append(f"  Faults [red]{', '.join(st['faults'])}[/]")
    else:
        lines.append("  Faults [green]none[/]")
    lines.append(f"  Uptime {st['uptime_s']}s")
    lines.append(f"  RSSI   {st['rssi']} dBm")
    return "\n".join(lines)


def build_log_panel(s, n=10):
    entries = s.log[-n:]
    lines = []
    for msg, ts in entries:
        lines.append(f"[dim]{ts.strftime('%H:%M:%S')}[/] {msg}")
    return "\n".join(lines) if lines else "[dim]no messages yet[/]"


def build_mqtt_panel(s, n=8):
    out = []
    # most recent published topics
    recent = s.mqtt_out[-n:]
    for topic, payload in recent:
        short = topic.split("/", 2)[-1]   # strip base+device prefix
        plen = min(len(payload), 46)
        out.append(f"[dim]→[/] [cyan]{short}[/] [dim]{payload[:plen]}{'…' if len(payload)>46 else ''}[/]")
    if not out:
        out.append("[dim]no publishes yet[/]")
    return "\n".join(out)


def render(s, connected, broker):
    layout = Layout()
    layout.split_column(
        Layout(name="header",  size=3),
        Layout(name="main",    ratio=1),
        Layout(name="keys",    size=3),
    )
    layout["main"].split_row(
        Layout(name="left",  ratio=2),
        Layout(name="right", ratio=3),
    )
    layout["left"].split_column(
        Layout(name="sensors",   ratio=3),
        Layout(name="actuators", ratio=2),
    )
    layout["right"].split_column(
        Layout(name="mqtt",  ratio=2),
        Layout(name="log",   ratio=3),
    )

    # Header
    conn_str = f"[green]● {broker}[/]" if connected else "[red]● offline[/]"
    t_str    = datetime.now().strftime("%H:%M:%S")
    layout["header"].update(Panel(
        f"  [bold]HydroOne[/] [dim]ESP32 Simulator[/]   {conn_str}   [dim]{t_str}[/]   "
        f"[dim]t+{int(s.elapsed())}s[/]",
        style="on default", box=box.HORIZONTALS
    ))

    layout["sensors"].update(Panel(
        build_sensor_table(s),
        title="[bold]sensors[/]", border_style="dim", box=box.ROUNDED
    ))
    layout["actuators"].update(Panel(
        build_actuator_panel(s),
        title="[bold]actuators[/]", border_style="dim", box=box.ROUNDED
    ))
    layout["mqtt"].update(Panel(
        build_mqtt_panel(s),
        title="[bold]published[/]", border_style="dim", box=box.ROUNDED
    ))
    layout["log"].update(Panel(
        build_log_panel(s),
        title="[bold]event log[/]", border_style="dim", box=box.ROUNDED
    ))
    layout["keys"].update(Panel(
        "  [bold]1[/] pH crash  [bold]2[/] EC depletion  [bold]3[/] temp spike  "
        "[bold]4[/] pump on  [bold]5[/] pump off  [bold]6[/] low water  "
        "[bold]r[/] reset  [bold]q[/] quit",
        style="dim", box=box.HORIZONTALS
    ))
    return layout


# ── Main loop ─────────────────────────────────────────────────────────────────

def publish_loop(state, client, no_mqtt, broker):
    connected = False

    if not no_mqtt and client:
        try:
            host, port = broker.split(":") if ":" in broker else (broker, "1883")
            client.connect(host, int(port), keepalive=60)
            client.loop_start()
            connected = True
        except Exception as e:
            state.log.append((f"[red]broker unreachable: {e}[/red]", datetime.now()))

    return connected


def main():
    parser = argparse.ArgumentParser(description="HydroOne ESP32 node simulator")
    parser.add_argument("--broker",   default="localhost:1883", help="MQTT broker host[:port]")
    parser.add_argument("--no-mqtt",  action="store_true",      help="run without MQTT (offline demo)")
    parser.add_argument("--speed",    type=float, default=1.0,  help="sim speed multiplier")
    args = parser.parse_args()

    state  = SystemState()
    client = None if (args.no_mqtt or not MQTT_AVAILABLE) else make_client(state)
    connected = publish_loop(state, client, args.no_mqtt, args.broker)

    console = Console()
    next_publish = time.time()

    # Key input thread (non-blocking)
    import termios, tty, select

    def getch_noblock():
        """Return pressed key or None without blocking."""
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            r, _, _ = select.select([sys.stdin], [], [], 0)
            if r:
                return sys.stdin.read(1)
        except Exception:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return None

    FAULT_MAP = {
        "1": ("ph",      -1.0,  "pH crash injected"),
        "2": ("ec",      -0.8,  "EC depletion injected"),
        "3": ("temp",    +1.0,  "Temp spike injected"),
        "4": None,
        "5": None,
        "6": ("level",   -1.0,  "Low water injected"),
    }

    with Live(render(state, connected, args.broker),
              console=console, refresh_per_second=4, screen=True) as live:
        while True:
            now = time.time()

            # Advance sim time
            state.t += args.speed * (now - (now - 0.01))  # tiny increment each frame
            state.t += args.speed * 0.25   # ~1 sim-second per 0.25 real-sec at 4fps

            # Publish every INTERVAL seconds
            if now >= next_publish:
                next_publish = now + INTERVAL
                sensors = state.all_sensors()
                ts_iso  = datetime.utcnow().isoformat() + "Z"

                publishes = [
                    ("sensors/water/temperature", sensors["water_temp"]),
                    ("sensors/air/temperature",   sensors["air_temp"]),
                    ("sensors/air/humidity",      sensors["humidity"]),
                    ("sensors/air/pressure",      sensors["pressure"]),
                    ("sensors/water/ph",          sensors["ph"]),
                    ("sensors/water/ec",          sensors["ec"]),
                    ("sensors/reservoir/distance",sensors["distance"]),
                    ("sensors/water/level_percent",sensors["level_pct"]),
                    ("sensors/water/level_litres", sensors["level_litres"]),
                    ("status",                    json.dumps(state.status_payload())),
                    ("heartbeat",                 ts_iso),
                ]

                for suffix, payload in publishes:
                    topic = full_topic(suffix)
                    msg   = str(payload) if not isinstance(payload, str) else payload
                    if client and connected:
                        client.publish(topic, msg, qos=1)
                    state.mqtt_out.append((topic, msg))

                # Keep mqtt_out buffer small
                if len(state.mqtt_out) > 60:
                    state.mqtt_out = state.mqtt_out[-60:]

            # Keyboard
            key = getch_noblock()
            if key:
                if key == "q":
                    break
                elif key == "r":
                    state.reset()
                    state.log.append(("[dim]faults cleared[/dim]", datetime.now()))
                elif key == "4":
                    state.pump_on = True
                    state.log.append(("[green]pump ON (manual)[/green]", datetime.now()))
                    if client and connected:
                        client.publish(full_topic("status"),
                                       json.dumps({"pump": "ON"}), qos=1)
                elif key == "5":
                    state.pump_on = False
                    state.log.append(("[dim]pump OFF (manual)[/dim]", datetime.now()))
                elif key in FAULT_MAP and FAULT_MAP[key]:
                    fkey, mag, label = FAULT_MAP[key]
                    state.inject(fkey, mag)
                    state.log.append((f"[red]FAULT: {label}[/red]", datetime.now()))

                if len(state.log) > 80:
                    state.log = state.log[-80:]

            live.update(render(state, connected, args.broker))
            time.sleep(0.25)

    if client:
        client.loop_stop()
        client.disconnect()

    console.print("\n[dim]Simulator stopped.[/dim]")


if __name__ == "__main__":
    main()
