from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunControl:
    """Mutable host/user stop signals checked only at durable stage boundaries."""

    cancellation_requested: bool = False
    host_model_limit_reached: bool = False

    def request_cancellation(self) -> None:
        self.cancellation_requested = True

    def report_host_model_limit(self) -> None:
        self.host_model_limit_reached = True
