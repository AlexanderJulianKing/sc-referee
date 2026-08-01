from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sc_referee_evaluation.typed_method_qualification import (
    IndependentQualificationAdapter,
    TypedMethodQualificationError,
)


def registered_qualification_adapter(
    binding: Mapping[str, Any],
) -> IndependentQualificationAdapter:
    """Resolve one explicitly allowlisted adapter; never discover ambient plugins."""

    declared = binding.get("qualification_adapter")
    if not isinstance(declared, Mapping):
        raise TypedMethodQualificationError("qualification adapter binding is absent")
    identity = (
        declared.get("adapter_id"),
        declared.get("adapter_version"),
        declared.get("entry_point"),
    )
    if identity == (
        "qualification-adapter:founder-orientation-python-v1",
        "1.0.0",
        (
            "sc_referee_evaluation.founder_orientation_adapter:"
            "FounderOrientationQualificationAdapter"
        ),
    ):
        from sc_referee_evaluation.founder_orientation_adapter import (
            FounderOrientationQualificationAdapter,
        )

        adapter: IndependentQualificationAdapter = FounderOrientationQualificationAdapter()
        _validate_declared_identity(adapter, declared)
        return adapter
    raise TypedMethodQualificationError("qualification adapter is not in the explicit registry")


def _validate_declared_identity(
    adapter: IndependentQualificationAdapter, declared: Mapping[str, Any]
) -> None:
    closure = declared.get("dependency_closure")
    if (
        declared.get("adapter_id") != adapter.adapter_id
        or declared.get("adapter_version") != adapter.adapter_version
        or declared.get("implementation_digest") != adapter.implementation_digest
        or declared.get("imports_production_semantic_implementation") is not False
        or not isinstance(closure, list)
        or not closure
    ):
        raise TypedMethodQualificationError("qualification adapter identity drifted")
