from __future__ import annotations

from dataclasses import dataclass

from sc_referee.calculation_checks.core import (
    CalculationCheckContractError,
    CalculationContext,
    FrozenCalculationInput,
)
from sc_referee.core.ids import semantic_digest


@dataclass(frozen=True)
class MaterialCalculationContext(CalculationContext):
    """A forward-only calculation view for explicitly selected material inputs."""

    material_inputs: tuple[FrozenCalculationInput, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        paths = [item.path for item in self.material_inputs]
        if len(paths) != len(set(paths)):
            raise CalculationCheckContractError("material calculation input paths must be unique")
        if self.selected_report.path in paths:
            raise CalculationCheckContractError(
                "selected report must not also be a material calculation input"
            )

    @property
    def context_digest(self) -> str:
        return semantic_digest(
            {
                "base_context_digest": super().context_digest,
                "material_inputs": [
                    {
                        "path": item.path,
                        "artifact_ref": item.artifact_ref.to_dict(),
                        "content_digest": item.content_digest,
                    }
                    for item in self.material_inputs
                ],
            }
        )
