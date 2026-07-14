from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from sc_referee.inference.ir.nodes import SourceSpan


@dataclass(frozen=True)
class Diagnostic:
    kind: str
    message: str
    span: SourceSpan | None = None
    details: Mapping[str, object] = field(default_factory=dict)

