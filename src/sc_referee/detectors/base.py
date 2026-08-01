from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class DetectionOutput:
    detector_result: dict[str, Any]
    finding_draft: dict[str, Any] | None
    material_question: dict[str, Any] | None


class Detector(Protocol):
    detector_id: str
    detector_version: str

    def evaluate(self, locked_case: dict[str, Any]) -> DetectionOutput: ...
