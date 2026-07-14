from __future__ import annotations

from dataclasses import dataclass

from sc_referee.inference.frontend.common import SourceUnit


@dataclass(frozen=True)
class FrontendResult:
    unit: SourceUnit


def lower_python(unit: SourceUnit) -> FrontendResult:
    return FrontendResult(unit)

