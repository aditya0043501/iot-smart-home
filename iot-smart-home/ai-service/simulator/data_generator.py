"""
AETHER AI Service — Realistic Sensor Data Simulator
----------------------------------------------------
Generates time-of-day-aware, noise-added sensor readings for all
8 devices in the store. Used only when real sensor data is absent.
Every reading is tagged is_simulated=1 so the UI can label it.

Design principles:
- Each device has a realistic baseline that varies by hour-of-day
  (e.g. AC works harder in the afternoon, lights off at night).
- Gaussian noise is added to all continuous values.
- Rare anomalies are injected with probability ANOMALY_PROBABILITY
  (e.g. power spike, temperature runaway) to give anomaly detection
  something real to catch.
- The fan_speed_num encodes: off=0, low=1, medium=2, high=3.

Batch 0 changes:
- Time comes from an injectable Clock (core.clock); no direct
  datetime.now()/utcnow()/time.time() calls remain in this module.
- Randomness comes from one RNG. Pass rng=random.Random(seed) (or set
  SIM_SEED) and the same clock to get identical snapshots.
- dev-9 is a window contact sensor (device_type="window", is_open 0/1).
  It is the single source of truth for "window open"; room flags are
  derived from it in core.state.
"""

import math
import random
import time
from datetime import datetime

from config import config
from core.clock import Clock, SystemClock

# Module RNG. Replaced per call when generate_snapshot(rng=...) is given.
_rng: random.Random = random.Random(int(config.SIM_SEED)) if config.SIM_SEED.strip() else random.Random()
_now: datetime = datetime.now()


# ── Device catalogue (mirrors store.js) ───────────────────────
DEVICES = [
    {"id": "dev-1", "name": "Living Room Main Lights",    "room": "Living Room",  "type": "light"},
    {"id": "dev-2", "name": "Master Climate Thermostat",  "room": "Living Room",  "type": "thermostat"},
    {"id": "dev-3", "name": "Front Entrance Smart Lock",  "room": "Living Room",  "type": "lock"},
    {"id": "dev-4", "name": "AeroFlow Ceiling Fan",       "room": "Bedroom",      "type": "fan"},
    {"id": "dev-5", "name": "Bedroom Reading Lamp",       "room": "Bedroom",      "type": "light"},
    {"id": "dev-6", "name": "Smart Kitchen Coffee Maker", "room": "Kitchen",      "type": "appliance"},
    {"id": "dev-7", "name": "Backyard Security Cam HD",   "room": "Living Room",  "type": "camera"},
    {"id": "dev-8", "name": "Smart Convection Oven",      "room": "Kitchen",      "type": "appliance"},
    {"id": "dev-9", "name": "Living Room Window Sensor",  "room": "Living Room",  "type": "window"},
]

# ── Hour-of-day weighting (0–23) ──────────────────────────────
# Returns a 0–1 scale for how "active" the home is.
def _activity_level(hour: int) -> float:
    """Sinusoidal occupancy model: peaks around 8 AM and 7 PM."""
    morning = 0.6 * math.exp(-0.5 * ((hour - 8) / 2.5) ** 2)
    evening = 1.0 * math.exp(-0.5 * ((hour - 19) / 2.0) ** 2)
    return min(1.0, morning + evening)


def _ambient_temp(hour: int) -> float:
    """Chennai-style temperature curve: 26°C at night, 34°C at peak."""
    base = 26.0 + 8.0 * math.sin(math.pi * (hour - 6) / 18) if 6 <= hour <= 24 else 26.0
    return round(base + _rng.gauss(0, 0.4), 1)


def _inject_anomaly(reading: dict, prob: float, hour: int | None = None) -> dict:
    """
    Randomly inject an anomaly into a reading with probability `prob`.
    Types:
      - power_spike: 5-10× normal power draw
      - temp_runaway: temperature 8-15°C above target (thermostat only)
      - motion_at_night: motion detected between 00-05h
    """
    if _rng.random() > prob:
        return reading  # no anomaly

    anomaly_type = _rng.choice(["power_spike", "power_spike", "temp_runaway", "motion_night"])

    if anomaly_type == "power_spike":
        reading["power_watts"] = reading.get("power_watts", 20) * _rng.uniform(5, 10)
        reading["anomaly_score"] = round(_rng.uniform(0.7, 0.98), 3)

    elif anomaly_type == "temp_runaway" and reading["device_type"] == "thermostat":
        reading["temperature"] = round((reading.get("temperature") or 24) + _rng.uniform(8, 15), 1)
        reading["anomaly_score"] = round(_rng.uniform(0.65, 0.92), 3)

    elif anomaly_type == "motion_night":
        # Was datetime.utcnow().hour: UTC vs local mismatch. Use sim clock hour.
        hour = _now.hour if hour is None else hour
        if 0 <= hour <= 5 and reading["device_type"] == "camera":
            reading["motion_detected"] = 1
            reading["anomaly_score"] = round(_rng.uniform(0.75, 0.95), 3)

    return reading


# ── Per-device reading generators ─────────────────────────────

def _gen_light(dev: dict, hour: int, activity: float) -> dict:
    on = activity > 0.15 or (6 <= hour <= 23)
    # Turn off bedroom reading lamp during working hours
    if dev["id"] == "dev-5" and 9 <= hour <= 21:
        on = False
    brightness = round(_rng.gauss(70, 8) * activity, 1) if on else 0.0
    brightness = max(0.0, min(100.0, brightness))
    power = round(brightness * 0.35 + _rng.gauss(0, 1), 1) if on else 0.0
    return {
        "state": int(on),
        "brightness": brightness if on else 0.0,
        "power_watts": max(0.0, power),
    }


def _gen_thermostat(dev: dict, hour: int, activity: float) -> dict:
    ambient = _ambient_temp(hour)
    # Target: cooler at night, comfort during day
    target = 23.0 if 9 <= hour <= 21 else 26.0
    target = round(target + _rng.gauss(0, 0.2), 1)
    # AC power: higher when ambient is far above target
    load = max(0, (ambient - target) * 85 + _rng.gauss(0, 30))
    return {
        "state": 1,
        "temperature": ambient,
        "target_temp": target,
        "humidity": round(_rng.gauss(55, 4), 1),
        "power_watts": round(load, 1),
    }


def _gen_lock(dev: dict, hour: int, activity: float) -> dict:
    # Unlocked briefly in morning and evening
    unlocked = (7 <= hour <= 9) or (17 <= hour <= 19)
    return {
        "state": 1,
        "is_locked": int(not unlocked),
        "battery_pct": round(94 - (_now.timestamp() % 86400) / 86400 * 0.02, 2),
        "power_watts": 0.5,
    }


def _gen_fan(dev: dict, hour: int, activity: float) -> dict:
    # Fan runs medium at night, low in morning, off mid-day
    if 22 <= hour or hour < 6:
        speed_num, speed_name, power = 2, "medium", 48
    elif 6 <= hour < 9:
        speed_num, speed_name, power = 1, "low", 22
    else:
        speed_num, speed_name, power = 0, "off", 0
    return {
        "state": int(speed_num > 0),
        "fan_speed_num": speed_num,
        "power_watts": round(power + _rng.gauss(0, 2), 1),
    }


def _gen_camera(dev: dict, hour: int, activity: float) -> dict:
    motion = int(_rng.random() < 0.04)  # ~4% base motion rate
    return {
        "state": 1,
        "is_recording": 1,
        "motion_detected": motion,
        "power_watts": round(8 + _rng.gauss(0, 0.5), 1),
    }


def _gen_appliance(dev: dict, hour: int, activity: float) -> dict:
    # Coffee maker: active 6-9 AM
    if dev["id"] == "dev-6":
        on = 6 <= hour <= 9
        power = round(_rng.gauss(1200, 50) if on else 2, 1)
    # Oven: active 17-20
    elif dev["id"] == "dev-8":
        on = 17 <= hour <= 20
        power = round(_rng.gauss(2100, 80) if on else 3, 1)
    else:
        on, power = False, 0
    return {
        "state": int(on),
        "power_watts": max(0.0, power),
    }


def _gen_window(dev: dict, hour: int, activity: float) -> dict:
    # Window aired in the morning (07:00-08:59). Contact sensors draw ~0 W.
    is_open = 7 <= hour <= 8
    return {
        "state": 1,
        "is_open": int(is_open),
        "power_watts": 0.0,
    }


_GENERATORS = {
    "light":      _gen_light,
    "thermostat": _gen_thermostat,
    "lock":       _gen_lock,
    "fan":        _gen_fan,
    "camera":     _gen_camera,
    "appliance":  _gen_appliance,
    "window":     _gen_window,
}


def generate_snapshot(clock: Clock | None = None,
                      rng: random.Random | None = None) -> list[dict]:
    """
    Generate one reading for every device.
    Returns a list of row-dicts ready to pass to database.insert_reading().

    clock: time source (default SystemClock). rng: random source
    (default module RNG, seeded by SIM_SEED if set).
    """
    global _rng, _now
    if rng is not None:
        _rng = rng
    _now = (clock or SystemClock()).now()
    hour     = _now.hour
    activity = _activity_level(hour)
    snapshot = []

    for dev in DEVICES:
        gen = _GENERATORS.get(dev["type"])
        if gen is None:
            continue

        fields = gen(dev, hour, activity)
        row = {
            "device_id":    dev["id"],
            "device_name":  dev["name"],
            "device_type":  dev["type"],
            "room":         dev["room"],
            "is_simulated": 1,
            "anomaly_score": 0.0,
            # defaults (overwritten by gen output)
            "state": 0, "power_watts": 0.0,
            "brightness": None, "temperature": None, "target_temp": None,
            "humidity": None, "fan_speed_num": None, "battery_pct": None,
            "is_locked": None, "is_recording": None, "motion_detected": None,
            "is_open": None,
        }
        row.update(fields)

        # Anomaly injection
        row = _inject_anomaly(row, config.ANOMALY_PROBABILITY, hour)
        snapshot.append(row)

    return snapshot
