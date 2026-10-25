"""
Batch 0 acceptance: window_open_ac_on raises an alert.

Device state is the single source of truth. Room flags are derived from it,
and SG-04 must fire when a window in a room is open while that room's AC is
actively cooling.
"""
from datetime import datetime

from core.clock import FakeClock
from core.guard import SafetyGuard
from core.state import DeviceStateStore

ROOM = "Living Room"


def _window(is_open, room=ROOM, dev="dev-9"):
    return {"device_id": dev, "device_type": "window", "room": room,
            "state": 1, "is_open": int(is_open), "power_watts": 0.0}


def _ac(power, state=1, room=ROOM, dev="dev-2", mode=None):
    r = {"device_id": dev, "device_type": "thermostat", "room": room,
         "state": state, "power_watts": power}
    if mode is not None:
        r["mode"] = mode
    return r


def _setup():
    clock = FakeClock(datetime(2026, 6, 1, 8, 0, 0))
    return clock, DeviceStateStore(clock=clock), SafetyGuard(clock=clock)


def test_window_open_ac_on_raises_alert():
    clock, store, guard = _setup()
    store.apply_many([_window(True), _ac(power=900)])
    alerts = guard.evaluate(store)
    assert len(alerts) == 1
    a = alerts[0]
    assert a.rule_id == "SG-04" and a.name == "window_open_ac_on"
    assert a.room == ROOM
    assert set(a.device_ids) == {"dev-9", "dev-2"}
    assert a.raised_at == clock.now()
    ev = a.to_anomaly_event()
    assert ev["algorithm"] == "SafetyGuard:SG-04" and ev["explanation"]


def test_room_flag_is_derived_from_device_state():
    """The old bug: a stale room flag disagreed with the device. Now there is no
    stored flag, so changing the device changes the flag immediately."""
    _, store, _ = _setup()
    store.apply_many([_window(False), _ac(power=900)])
    assert store.room_flags(ROOM)["window_open"] is False
    store.apply(_window(True))
    assert store.room_flags(ROOM)["window_open"] is True
    store.apply(_window(False))
    assert store.room_flags(ROOM)["window_open"] is False


def test_alert_is_edge_triggered_and_clears():
    _, store, guard = _setup()
    store.apply_many([_window(True), _ac(power=900)])
    assert len(guard.evaluate(store)) == 1
    assert guard.evaluate(store) == []          # still true: no duplicate
    assert len(guard.active()) == 1
    store.apply(_window(False))
    assert guard.evaluate(store) == []
    assert guard.active() == []                 # cleared
    store.apply(_window(True))
    assert len(guard.evaluate(store)) == 1      # re-raised on next opening


def test_no_alert_when_ac_idle_off_or_mode_off():
    for ac in (_ac(power=10), _ac(power=900, state=0), _ac(power=900, mode="off")):
        _, store, guard = _setup()
        store.apply_many([_window(True), ac])
        assert guard.evaluate(store) == [], ac


def test_no_alert_when_window_and_ac_in_different_rooms():
    _, store, guard = _setup()
    store.apply_many([_window(True, room="Bedroom"), _ac(power=900)])
    assert guard.evaluate(store) == []


def test_expert_facts_come_from_device_state():
    from classical.logic.expert_system import ExpertSystem
    _, store, _ = _setup()
    store.apply_many([_window(True), _ac(power=900)])
    facts = store.expert_facts()
    assert facts == ["ACOn", "WindowOpen"]
    es = ExpertSystem()
    res = es.forward_chain(facts)
    assert "EnergyWasteAlert" in str(res)


def test_simulator_window_device_triggers_sg04_at_8am():
    """End to end through the simulator: at 08:00 the window is aired while
    ambient (~28.7 C) is above the 26 C night set point, so the AC is cooling."""
    import random
    from simulator.data_generator import generate_snapshot
    clock = FakeClock(datetime(2026, 6, 1, 8, 0, 0))
    store, guard = DeviceStateStore(clock=clock), SafetyGuard(clock=clock)
    snap = generate_snapshot(clock=clock, rng=random.Random(1))
    store.apply_many(snap)
    rules = [a.rule_id for a in guard.evaluate(store)]
    assert rules == ["SG-04"]
