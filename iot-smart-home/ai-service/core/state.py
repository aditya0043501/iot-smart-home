"""
Device state store (Batch 0).

Single source of truth for "what is each device doing right now".

Rule: room-level flags (window_open, hvac_active, ...) are NEVER stored.
They are computed on demand from the latest device readings by
room_flags(). This removes the old failure mode where a room flag and the
device it describes disagreed, so the window_open_ac_on alert never fired.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.clock import Clock, SystemClock

# A thermostat counts as actively conditioning only above this draw.
# Below it the compressor is idle (fan-only or standby). Configurable.
DEFAULT_HVAC_ACTIVE_MIN_W = 50.0


def _truthy(v: Any) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "on", "open", "yes"}
    return bool(v)


class DeviceStateStore:
    def __init__(self, clock: Optional[Clock] = None,
                 hvac_active_min_w: float = DEFAULT_HVAC_ACTIVE_MIN_W):
        self.clock = clock or SystemClock()
        self.hvac_active_min_w = hvac_active_min_w
        self._devices: Dict[str, Dict[str, Any]] = {}

    # ── writes ────────────────────────────────────────────────
    def apply(self, reading: Dict[str, Any]) -> None:
        """Merge one reading into the latest state of its device."""
        dev_id = reading["device_id"]
        current = self._devices.setdefault(dev_id, {})
        current.update({k: v for k, v in reading.items() if v is not None})
        current["_updated_at"] = self.clock.now()

    def apply_many(self, readings: List[Dict[str, Any]]) -> None:
        for r in readings:
            self.apply(r)

    # ── reads ─────────────────────────────────────────────────
    def get(self, device_id: str) -> Optional[Dict[str, Any]]:
        d = self._devices.get(device_id)
        return dict(d) if d else None

    def all(self) -> List[Dict[str, Any]]:
        return [dict(d) for d in self._devices.values()]

    def rooms(self) -> List[str]:
        return sorted({d["room"] for d in self._devices.values() if "room" in d})

    def devices_in_room(self, room: str) -> List[Dict[str, Any]]:
        return [dict(d) for d in self._devices.values() if d.get("room") == room]

    # ── derived predicates (the only place these are defined) ─
    @staticmethod
    def is_window_open(dev: Dict[str, Any]) -> bool:
        return dev.get("device_type") == "window" and _truthy(dev.get("is_open"))

    def is_hvac_active(self, dev: Dict[str, Any]) -> bool:
        if dev.get("device_type") != "thermostat":
            return False
        if not _truthy(dev.get("state")):
            return False
        if str(dev.get("mode", "")).lower() == "off":
            return False
        return float(dev.get("power_watts") or 0.0) >= self.hvac_active_min_w

    def room_flags(self, room: str) -> Dict[str, Any]:
        devs = self.devices_in_room(room)
        open_windows = [d["device_id"] for d in devs if self.is_window_open(d)]
        active_hvac = [d["device_id"] for d in devs if self.is_hvac_active(d)]
        return {
            "room": room,
            "window_open": bool(open_windows),
            "hvac_active": bool(active_hvac),
            "open_windows": open_windows,
            "active_hvac": active_hvac,
        }

    def expert_facts(self) -> List[str]:
        """Ground facts for the expert system, derived from device state."""
        facts = set()
        for room in self.rooms():
            f = self.room_flags(room)
            if f["window_open"]:
                facts.add("WindowOpen")
            if f["hvac_active"]:
                facts.add("ACOn")
        return sorted(facts)
