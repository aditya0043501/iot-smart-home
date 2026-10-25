"""
Clock port (Batch 0).

Every piece of code that needs "now" takes a Clock instead of calling
datetime.now() / time.time() directly. This makes scenarios reproducible
and lets tests advance time without sleeping (principle P7).

Implementations
---------------
SystemClock  - wall clock. Default in production.
FakeClock    - fully manual. Tests call advance()/set(). Never moves on its own.
SimClock     - accelerated simulated time for demos, driven by a base clock.

Why SimClock does not drift
---------------------------
The old approach to "run the sim at 600x" is to add speed*interval to a
simulated timestamp on every tick. Each tick's real duration is not exactly
`interval` (scheduling jitter, work done in the tick), so the error grows
without bound, and at 600x every millisecond of jitter becomes 0.6 s of
simulated time. SimClock instead computes

    sim_now = sim_start + (base.monotonic() - base_t0) * speed

from a single anchor, so the error does not accumulate across ticks.
Speed is clamped to [0, max_speed]; set_speed() and reset() re-anchor so
changing speed mid-run never causes a jump.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Port: anything that can tell the time."""

    def now(self) -> datetime:
        """Current (possibly simulated) local datetime, naive."""
        ...

    def monotonic(self) -> float:
        """Seconds from an arbitrary origin; never goes backwards."""
        ...


class SystemClock:
    """Real wall-clock time."""

    def now(self) -> datetime:
        return datetime.now()

    def monotonic(self) -> float:
        return time.monotonic()


class FakeClock:
    """Manual clock for tests. Time only moves when you move it."""

    def __init__(self, start: datetime | None = None):
        self._now = start or datetime(2026, 1, 1, 12, 0, 0)
        self._mono = 0.0

    def now(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._mono

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("FakeClock cannot go backwards")
        self._now += timedelta(seconds=seconds)
        self._mono += seconds

    def set(self, when: datetime) -> None:
        if when < self._now:
            raise ValueError("FakeClock cannot go backwards")
        self._mono += (when - self._now).total_seconds()
        self._now = when


class SimClock:
    """Accelerated simulated time anchored to a base clock (no drift)."""

    def __init__(
        self,
        speed: float = 1.0,
        start: datetime | None = None,
        base: Clock | None = None,
        max_speed: float = 600.0,
    ):
        self._base = base or SystemClock()
        self.max_speed = float(max_speed)
        self._speed = self.clamp_speed(speed)
        self._anchor_sim = start or self._base.now()
        self._anchor_mono = self._base.monotonic()
        self._mono_offset = 0.0

    def clamp_speed(self, speed: float) -> float:
        return max(0.0, min(float(speed), self.max_speed))

    @property
    def speed(self) -> float:
        return self._speed

    def _elapsed_sim_seconds(self) -> float:
        return (self._base.monotonic() - self._anchor_mono) * self._speed

    def now(self) -> datetime:
        return self._anchor_sim + timedelta(seconds=self._elapsed_sim_seconds())

    def monotonic(self) -> float:
        """Simulated seconds elapsed in total; never decreases, even across reset()."""
        return self._mono_offset + self._elapsed_sim_seconds()

    def _reanchor(self) -> None:
        self._mono_offset = self.monotonic()
        self._anchor_mono = self._base.monotonic()

    def set_speed(self, speed: float) -> None:
        """Change speed without a jump: re-anchor at the current sim time."""
        current = self.now()
        self._reanchor()
        self._anchor_sim = current
        self._speed = self.clamp_speed(speed)

    def reset(self, start: datetime, speed: float | None = None) -> None:
        """Restart simulated time at `start` (for reproducible scenarios)."""
        self._reanchor()
        self._anchor_sim = start
        if speed is not None:
            self._speed = self.clamp_speed(speed)
