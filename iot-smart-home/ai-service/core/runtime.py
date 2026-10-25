"""
Process-wide wiring for the domain core (Batch 0).

One clock, one state store, one guard. Every reading, whether from the
simulator or POSTed by the frontend, goes through ingest(), so the guard
sees the same device state regardless of source.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from config import config
from core.clock import Clock, SimClock
from core.guard import GuardAlert, SafetyGuard
from core.state import DeviceStateStore

clock: Clock = SimClock(speed=config.SIM_SPEED, max_speed=config.SIM_MAX_SPEED)
store = DeviceStateStore(clock=clock)
guard = SafetyGuard(clock=clock)


def ingest(readings: List[Dict], on_alert: Optional[Callable[[GuardAlert], None]] = None) -> List[GuardAlert]:
    """Apply readings to the state store, run the guard, report new alerts."""
    store.apply_many(readings)
    new_alerts = guard.evaluate(store)
    if on_alert:
        for a in new_alerts:
            on_alert(a)
    return new_alerts
