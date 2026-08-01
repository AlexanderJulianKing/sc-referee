from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Literal

from .errors import DeadlineExceededError

AuditMode = Literal["quick", "standard", "publication"]

_MODE_LIMITS: dict[AuditMode, tuple[float, float]] = {
    "quick": (120.0, 300.0),
    "standard": (480.0, 600.0),
    "publication": (1500.0, 1800.0),
}


@dataclass
class AuditDeadline:
    hard_seconds: float
    now: Callable[[], float] = monotonic
    scheduling_cutoff_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.hard_seconds <= 0:
            raise ValueError("hard_seconds must be positive")
        if self.scheduling_cutoff_seconds is None:
            self.scheduling_cutoff_seconds = self.hard_seconds
        if self.scheduling_cutoff_seconds <= 0:
            raise ValueError("scheduling_cutoff_seconds must be positive")
        if self.scheduling_cutoff_seconds > self.hard_seconds:
            raise ValueError("scheduling_cutoff_seconds cannot exceed hard_seconds")
        self._started = self.now()
        self._paused_at: float | None = None
        self._paused_total = 0.0
        self._last_elapsed = 0.0

    @classmethod
    def for_mode(
        cls,
        mode: AuditMode,
        *,
        now: Callable[[], float] = monotonic,
    ) -> AuditDeadline:
        scheduling_cutoff, hard_deadline = _MODE_LIMITS[mode]
        return cls(
            hard_deadline,
            now=now,
            scheduling_cutoff_seconds=scheduling_cutoff,
        )

    def pause_for_scientist(self) -> None:
        if self._paused_at is None:
            self._paused_at = self.now()

    def resume_after_scientist(self) -> None:
        if self._paused_at is not None:
            self._paused_total += self.now() - self._paused_at
            self._paused_at = None

    @property
    def elapsed(self) -> float:
        current = self._paused_at if self._paused_at is not None else self.now()
        self._last_elapsed = max(0.0, current - self._started - self._paused_total)
        return self._last_elapsed

    @property
    def observed_elapsed(self) -> float:
        """Return the most recently checked elapsed value without sampling the clock again."""

        return self._last_elapsed

    @property
    def paused_for_scientist(self) -> float:
        current_pause = 0.0
        if self._paused_at is not None:
            current_pause = max(0.0, self.now() - self._paused_at)
        return max(0.0, self._paused_total + current_pause)

    @property
    def remaining(self) -> float:
        return max(0.0, self.hard_seconds - self.elapsed)

    @property
    def expired(self) -> bool:
        return self.remaining <= 0.0

    @property
    def scheduling_cutoff_reached(self) -> bool:
        cutoff = self.scheduling_cutoff_seconds
        if cutoff is None:
            raise RuntimeError("AuditDeadline was not initialized")
        return self.elapsed >= cutoff

    @property
    def optional_scheduling_open(self) -> bool:
        return not self.scheduling_cutoff_reached and not self.expired

    def check(self) -> None:
        if self.expired:
            raise DeadlineExceededError("Audit hard deadline exhausted")
