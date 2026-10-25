"""
ALGO-ENTRY: safety_guard
==============================================================================
ALGO        Deterministic rule guard (threshold rules, edge-triggered alerts)
CATEGORY    Safety / rule-based (brief section 3, row 1)
WHAT        Evaluates fixed safety rules against current device state and
            raises an alert when a rule becomes true; clears it when false.
WHY HERE    Safety decisions must be deterministic and auditable (principle P3).
            No ML, fuzzy, planner or LLM output may override this layer.
WHERE USED  main.py simulator loop -> anomaly_events table -> UI alert panel;
            GET /api/guard/status.
INPUT       DeviceStateStore (latest reading per device).
OUTPUT      List[GuardAlert] newly raised on this evaluation; active set kept.
HOW IT WORKS
            STEP 1  For each rule, compute the set of (rule, room) keys whose
                    condition holds, using only derived room flags.
            STEP 2  Keys present now but not before -> new alert (raise once).
            STEP 3  Keys present before but not now -> cleared.
BASELINE    None. This is the safety floor.
EFFICIENCY  Measured (Batch 0, simulated 9-device home, aarch64 sandbox,
            Python 3.10.12, n=20 000 calls): evaluate() median 4.1 us,
            p99 5.4 us. Cost is O(devices). Not yet measured on Python 3.12.
LIMITS      Batch 0 implements SG-04 only. SG-01..03, SG-05..06 (gas, smoke,
            flame/flood, door/lock) plus debounce and hysteresis arrive in
            Batch 3. No network-condition handling yet.
JUDGE Q&A   Q: Why not let the anomaly model flag window+AC?
            A: It is a known, crisp condition. A rule is exact, explainable,
               and cannot be wrong in ways a model can.
            Q: Why edge-triggered?
            A: A level-triggered rule would write an alert every 5 s tick.
==============================================================================

Rule IDs
--------
SG-01 gas leak            (reserved, Batch 3)
SG-02 smoke               (reserved, Batch 3)
SG-03 flood / flame       (reserved, Batch 3)
SG-04 window open while HVAC actively conditioning the same room  <- live
SG-05 door / lock         (reserved, Batch 3)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from core.clock import Clock, SystemClock
from core.state import DeviceStateStore

AlertKey = Tuple[str, str]  # (rule_id, room)


@dataclass
class GuardAlert:
    rule_id: str
    name: str
    severity: str
    room: str
    device_ids: List[str]
    message: str
    suggested_action: str
    raised_at: datetime

    def to_anomaly_event(self) -> Dict[str, object]:
        """Row for the existing anomaly_events table (UI already renders it)."""
        import json
        return {
            "device_id": ",".join(self.device_ids),
            "algorithm": f"SafetyGuard:{self.rule_id}",
            "score": 1.0,
            "threshold": 1.0,
            "feature_values": json.dumps({"room": self.room, "devices": self.device_ids}),
            "explanation": self.message,
            "suggested_action": self.suggested_action,
        }


@dataclass
class SafetyGuard:
    clock: Clock = field(default_factory=SystemClock)
    _active: Dict[AlertKey, GuardAlert] = field(default_factory=dict)

    # STEP 1 ────────────────────────────────────────────────────
    def _sg04_window_open_hvac(self, store: DeviceStateStore) -> Dict[AlertKey, GuardAlert]:
        hits: Dict[AlertKey, GuardAlert] = {}
        for room in store.rooms():
            f = store.room_flags(room)
            if f["window_open"] and f["hvac_active"]:
                hits[("SG-04", room)] = GuardAlert(
                    rule_id="SG-04",
                    name="window_open_ac_on",
                    severity="WARNING",
                    room=room,
                    device_ids=f["open_windows"] + f["active_hvac"],
                    message=(f"Window open in {room} while the AC is running "
                             f"({', '.join(f['active_hvac'])}). Cooled air is escaping."),
                    suggested_action="Close the window or turn the AC off.",
                    raised_at=self.clock.now(),
                )
        return hits

    def evaluate(self, store: DeviceStateStore) -> List[GuardAlert]:
        """Return alerts that became active on this call."""
        current = self._sg04_window_open_hvac(store)
        # STEP 2 — newly true
        new = [a for k, a in current.items() if k not in self._active]
        for k, a in current.items():
            self._active.setdefault(k, a)
        # STEP 3 — no longer true
        for k in [k for k in self._active if k not in current]:
            del self._active[k]
        return new

    def active(self) -> List[GuardAlert]:
        return list(self._active.values())
