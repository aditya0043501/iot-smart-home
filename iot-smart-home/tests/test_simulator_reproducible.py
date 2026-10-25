"""Same clock + same seed => identical simulator output (Batch 0)."""
import random
from datetime import datetime

from core.clock import FakeClock
from simulator.data_generator import DEVICES, generate_snapshot


def _snap(seed, when):
    return generate_snapshot(clock=FakeClock(when), rng=random.Random(seed))


def test_same_seed_same_time_gives_identical_snapshot():
    t = datetime(2026, 6, 1, 14, 30)
    assert _snap(42, t) == _snap(42, t)


def test_different_seed_differs():
    t = datetime(2026, 6, 1, 14, 30)
    assert _snap(1, t) != _snap(2, t)


def test_hour_comes_from_clock_not_wall_time():
    night = {r["device_id"]: r for r in _snap(7, datetime(2026, 6, 1, 3, 0))}
    morning = {r["device_id"]: r for r in _snap(7, datetime(2026, 6, 1, 8, 0))}
    assert night["dev-9"]["is_open"] == 0
    assert morning["dev-9"]["is_open"] == 1


def test_every_device_reports_and_window_device_exists():
    snap = _snap(3, datetime(2026, 6, 1, 12, 0))
    assert {r["device_id"] for r in snap} == {d["id"] for d in DEVICES}
    assert any(d["type"] == "window" for d in DEVICES)
