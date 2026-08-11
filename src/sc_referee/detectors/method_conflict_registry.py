from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    load_capability_detector_manifest,
)
from sc_referee.core.ids import semantic_digest
from sc_referee.detectors.bounded_analysis_method_conflict import (
    BoundedAnalysisMethodConflictDetector,
)
from sc_referee.scientific_checks.core import (
    EvidencePlane,
    MethodConflictBinding,
    OperandKind,
)
from sc_referee.scientific_checks.registry import ScientificCheckRegistry


class MethodConflictRegistryError(ValueError):
    """Raised when a locked or packaged detector binding is incomplete or drifted."""


@dataclass(frozen=True)
class MethodConflictEvaluation:
    """One detector result with the exact binding and work packet that produced it."""

    result: dict[str, Any]
    binding: MethodConflictBinding
    work_packet: dict[str, Any]


def validate_registered_method_conflict_manifests(
    registry: ScientificCheckRegistry,
    schema_root: Path,
) -> tuple[dict[str, Any], ...]:
    """Load and validate every explicit detector family used by the scientific registry."""

    bindings_by_detector = _group_bindings(registry.method_conflict_bindings)
    manifests: list[dict[str, Any]] = []
    for detector_id in sorted(bindings_by_detector):
        if detector_id != BoundedAnalysisMethodConflictDetector.detector_id:
            raise MethodConflictRegistryError(
                f"registered method-conflict detector family is not installed: {detector_id}"
            )
        manifest = load_capability_detector_manifest(
            default_capability_manifest_root(), schema_root, detector_id
        )
        _validate_manifest_binding(manifest, bindings_by_detector[detector_id])
        BoundedAnalysisMethodConflictDetector(manifest, bindings_by_detector[detector_id])
        manifests.append(manifest)
    return tuple(manifests)


def evaluate_registered_method_conflicts(
    locked_case: Mapping[str, Any],
) -> list[MethodConflictEvaluation]:
    """Dispatch all locked method-conflict bindings without detector-specific controller code."""

    bindings = locked_method_conflict_bindings(locked_case)
    bindings_by_detector = _group_bindings(bindings)
    manifests = _mapping_list(locked_case.get("detector_manifests"))
    evaluations: list[MethodConflictEvaluation] = []
    for detector_id in sorted(bindings_by_detector):
        if detector_id != BoundedAnalysisMethodConflictDetector.detector_id:
            raise MethodConflictRegistryError(
                f"locked method-conflict detector family is not installed: {detector_id}"
            )
        matches = [item for item in manifests if item.get("detector_id") == detector_id]
        if len(matches) != 1:
            raise MethodConflictRegistryError(
                f"locked method-conflict detector manifest count is not one: {detector_id}"
            )
        detector_bindings = bindings_by_detector[detector_id]
        _validate_manifest_binding(matches[0], detector_bindings)
        detector = BoundedAnalysisMethodConflictDetector(matches[0], detector_bindings)
        check_ids = set(detector.supported_check_ids)
        targets = sorted(
            (
                question
                for question in _mapping_list(locked_case.get("material_questions"))
                if question.get("status") == "answered"
                and question.get("extensions", {}).get("x-scientific-check-id") in check_ids
            ),
            key=lambda question: str(question.get("question_id")),
        )
        for question in targets:
            extensions = question.get("extensions")
            check_id = (
                str(extensions.get("x-scientific-check-id", ""))
                if isinstance(extensions, Mapping)
                else ""
            )
            binding = detector.bindings_by_check.get(check_id)
            if binding is None:
                raise MethodConflictRegistryError(
                    f"locked method-conflict target has no exact binding: {check_id}"
                )
            # The detector's work-packet constructor is deterministic and is the
            # same path used internally by evaluate(). Keeping the detector file
            # byte-identical preserves its installed implementation digest.
            packet = detector._work_packet(locked_case, question)
            result = detector.evaluate(locked_case, question)
            if result.get("deterministic_input_digest") != semantic_digest(packet):
                raise MethodConflictRegistryError(
                    "method-conflict detector result drifted from its exposed work packet"
                )
            evaluations.append(
                MethodConflictEvaluation(
                    result=deepcopy(result),
                    binding=binding,
                    work_packet=deepcopy(packet),
                )
            )
    return evaluations


def locked_method_conflict_bindings(
    locked_case: Mapping[str, Any],
) -> tuple[MethodConflictBinding, ...]:
    lock = locked_case.get("scientific_check_registry")
    if not isinstance(lock, Mapping):
        return ()
    raw = lock.get("method_conflict_bindings")
    if raw is None:
        return ()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise MethodConflictRegistryError("locked method-conflict binding list is malformed")
    bindings = tuple(_binding_from_dict(item) for item in raw if isinstance(item, Mapping))
    if len(bindings) != len(raw):
        raise MethodConflictRegistryError("locked method-conflict binding is malformed")
    enabled = lock.get("enabled_modules")
    if not isinstance(enabled, Sequence) or isinstance(enabled, (str, bytes)):
        raise MethodConflictRegistryError("locked scientific-check module list is malformed")
    manifest_digests = {
        str(item.get("manifest", {}).get("check_id")): str(item.get("manifest_digest"))
        for item in enabled
        if isinstance(item, Mapping) and isinstance(item.get("manifest"), Mapping)
    }
    for binding in bindings:
        if manifest_digests.get(binding.check_id) != binding.check_manifest_digest:
            raise MethodConflictRegistryError(
                f"locked method-conflict check manifest drifted: {binding.check_id}"
            )
    return tuple(sorted(bindings, key=lambda item: item.binding_id))


def _validate_manifest_binding(
    manifest: Mapping[str, Any], bindings: tuple[MethodConflictBinding, ...]
) -> None:
    manifest_digest = semantic_digest(manifest)
    detector_id = str(manifest.get("detector_id", ""))
    detector_version = str(manifest.get("detector_version", ""))
    for binding in bindings:
        if (
            binding.detector_id != detector_id
            or binding.detector_version != detector_version
            or binding.detector_manifest_digest != manifest_digest
        ):
            raise MethodConflictRegistryError(
                f"method-conflict binding drifts from detector manifest: {binding.binding_id}"
            )


def _group_bindings(
    bindings: Sequence[MethodConflictBinding],
) -> dict[str, tuple[MethodConflictBinding, ...]]:
    grouped: dict[str, list[MethodConflictBinding]] = {}
    for binding in bindings:
        grouped.setdefault(binding.detector_id, []).append(binding)
    return {
        detector_id: tuple(sorted(values, key=lambda item: item.binding_id))
        for detector_id, values in grouped.items()
    }


def _binding_from_dict(value: Mapping[str, Any]) -> MethodConflictBinding:
    try:
        return MethodConflictBinding(
            binding_id=str(value["binding_id"]),
            check_id=str(value["check_id"]),
            check_version=str(value["check_version"]),
            check_manifest_digest=str(value["check_manifest_digest"]),
            detector_id=str(value["detector_id"]),
            detector_version=str(value["detector_version"]),
            detector_manifest_digest=str(value["detector_manifest_digest"]),
            dimension=str(value["dimension"]),
            comparison_form=str(value["comparison_form"]),
            operand_kind=cast(OperandKind, value["operand_kind"]),
            required_evidence_planes=tuple(
                cast(Sequence[EvidencePlane], value["required_evidence_planes"])
            ),
            required_semantic_roles=_string_tuple(value["required_semantic_roles"]),
            required_assertion_roles=_string_tuple(value["required_assertion_roles"]),
            counterevidence_predicates=_string_tuple(value["counterevidence_predicates"]),
            forbidden_members=_string_tuple(value["forbidden_members"]),
            production_finding_permitted=value["production_finding_permitted"] is True,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise MethodConflictRegistryError("locked method-conflict binding is invalid") from error


def _string_tuple(value: object) -> tuple[str, ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not all(isinstance(item, str) for item in value)
    ):
        raise MethodConflictRegistryError("locked binding string collection is malformed")
    return tuple(value)


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]
