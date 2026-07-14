from __future__ import annotations

from sc_referee.inference.frontend.python import FrontendResult


def lower_r(unit) -> FrontendResult:
    """R remains an explicit coverage barrier until a real parser is available."""
    return FrontendResult(unit)

