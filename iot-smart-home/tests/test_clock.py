"""Injectable clock and sim-speed behaviour (Batch 0). No sleeps (P7)."""
from datetime import datetime, timedelta

import pytest

from core.clock import Clock, FakeClock, SimClock, SystemClock

T0 = datetime(2026, 1, 1, 0, 0, 0)


def test_all_clocks_satisfy_the_port():
    for c in (SystemClock(), FakeClock(), SimClock(base=FakeClock())):
        assert isinstance(c, Clock)


def test_fake_clock_moves_only_when_told():
    c = FakeClock(T0)
    assert c.now() == T0
    c.advance(90)
    assert c.now() == T0 + timedelta(seconds=90)
    assert c.monotonic() == 90
    with pytest.raises(ValueError):
        c.advance(-1)


def test_sim_clock_scales_time():
    base = FakeClock(T0)
    sim = SimClock(speed=600, start=T0, base=base, max_speed=600)
    base.advance(1)
    assert sim.now() == T0 + timedelta(seconds=600)


def test_sim_clock_has_no_drift_at_600x_over_many_uneven_ticks():
    """Old behaviour: sim_t += speed * nominal_interval each tick, so real
    jitter accumulates. New: sim time is anchored, so after N ticks of
    uneven real duration the error is exactly zero."""
    base = FakeClock(T0)
    sim = SimClock(speed=600, start=T0, base=base, max_speed=600)
    naive = T0
    nominal = 5.0
    jitters = [0.003, 0.011, -0.002, 0.017, 0.0, 0.009] * 2000   # 12 000 ticks
    for j in jitters:
        base.advance(nominal + j)
        naive += timedelta(seconds=600 * nominal)        # what drift-prone code does
    real_elapsed = sum(nominal + j for j in jitters)
    expected = T0 + timedelta(seconds=600 * real_elapsed)
    assert abs((sim.now() - expected).total_seconds()) < 1e-3
    # And the naive accumulator really does drift (documents the old bug):
    assert abs((naive - expected).total_seconds()) > 60


def test_sim_speed_is_clamped():
    base = FakeClock(T0)
    assert SimClock(speed=5000, base=base, max_speed=600).speed == 600
    assert SimClock(speed=-3, base=base, max_speed=600).speed == 0


def test_set_speed_does_not_jump_and_reset_is_reproducible():
    base = FakeClock(T0)
    sim = SimClock(speed=10, start=T0, base=base)
    base.advance(6)                       # +60 s sim
    before = sim.now()
    sim.set_speed(100)
    assert sim.now() == before            # no jump on speed change
    base.advance(1)
    assert sim.now() == before + timedelta(seconds=100)
    mono_before = sim.monotonic()
    sim.reset(T0, speed=1)
    assert sim.now() == T0                # scenario restarts at a known time
    assert sim.monotonic() >= mono_before # monotonic never goes backwards
