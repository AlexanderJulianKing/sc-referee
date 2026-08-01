from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.observed import controller_provenance
from sc_referee.scientific_checks import RecordRef
from sc_referee.version import SCHEMA_VERSION

Applicability = Literal["applicable", "not_applicable", "ambiguous", "unsupported"]
ComparisonOutcome = Literal["conformant", "nonconformant", "unknown", "not_applicable"]
OutputCeiling = Literal["question_only", "disclosure_only", "evaluation_candidate"]
LineageStatus = Literal["complete", "incomplete", "not_applicable"]
OperandKind = Literal[
    "boolean",
    "integer",
    "finite_number",
    "string",
    "boolean_array",
    "integer_array",
    "finite_number_array",
    "string_array",
]
ReceiptKind = Literal["applicability", "ambiguity", "counterevidence", "completeness"]
ReceiptState = Literal["passed", "triggered", "not_applicable", "unsupported"]
NON_INFERENCES = (
    "causality",
    "execution",
    "scientific_correctness",
    "universal_method_adequacy",
)
MAX_OPERANDS = 64
MAX_ARRAY_ITEMS = 10_000


class CalculationCheckContractError(ValueError):
    """Raised when a calculation-check value escapes the accepted closed contract."""


@dataclass(frozen=True)
class CalculationCheckManifest:
    check_id: str
    check_version: str
    implementation_digest: str
    comparison_relation: str
    output_ceiling: OutputCeiling
    permitted_wording: str

    def __post_init__(self) -> None:
        _identifier(self.check_id, "check_id")
        _text(self.check_version, "check_version")
        _digest(self.implementation_digest, "implementation_digest")
        _identifier(self.comparison_relation, "comparison_relation")
        _text(self.permitted_wording, "permitted_wording")

    def to_dict(self) -> dict[str, Any]:
        value = {
            "manifest_kind": "calculation_check_manifest",
            "check_id": self.check_id,
            "check_version": self.check_version,
            "implementation_digest": self.implementation_digest,
        }
        value["manifest_digest"] = semantic_digest(value)
        return value

    @property
    def manifest_digest(self) -> str:
        return str(self.to_dict()["manifest_digest"])


@dataclass(frozen=True)
class CalculationAdapterManifest:
    adapter_id: str
    adapter_version: str
    implementation_digest: str
    recognition_grammar_digest: str

    def __post_init__(self) -> None:
        _identifier(self.adapter_id, "adapter_id")
        _text(self.adapter_version, "adapter_version")
        _digest(self.implementation_digest, "implementation_digest")
        _digest(self.recognition_grammar_digest, "recognition_grammar_digest")

    def to_dict(self) -> dict[str, Any]:
        value = {
            "manifest_kind": "calculation_adapter_manifest",
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "implementation_digest": self.implementation_digest,
        }
        value["manifest_digest"] = semantic_digest(
            {**value, "recognition_grammar_digest": self.recognition_grammar_digest}
        )
        return value

    @property
    def manifest_digest(self) -> str:
        return str(self.to_dict()["manifest_digest"])


@dataclass(frozen=True)
class FrozenCalculationInput:
    path: str
    artifact_ref: RecordRef
    content: bytes
    content_digest: str
    source_ref: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.path or self.path.startswith("/") or ".." in self.path.split("/"):
            raise CalculationCheckContractError(
                "calculation input path must be relative and bounded"
            )
        if sha256_digest(self.content) != self.content_digest:
            raise CalculationCheckContractError("calculation input digest mismatch")
        if self.source_ref.get("content_digest") != self.content_digest:
            raise CalculationCheckContractError("calculation input source digest mismatch")
        if self.source_ref.get("path") != self.path:
            raise CalculationCheckContractError("calculation input source path mismatch")


@dataclass(frozen=True)
class CalculationContext:
    snapshot_digest: str
    selected_surface_ref: RecordRef
    selected_artifact_ref: RecordRef
    selected_report: FrozenCalculationInput
    tabular_inputs: tuple[FrozenCalculationInput, ...]

    def __post_init__(self) -> None:
        _digest(self.snapshot_digest, "snapshot_digest")
        if self.selected_report.artifact_ref != self.selected_artifact_ref:
            raise CalculationCheckContractError("selected report artifact identity mismatch")
        paths = [item.path for item in self.tabular_inputs]
        if len(paths) != len(set(paths)):
            raise CalculationCheckContractError("calculation input paths must be unique")

    @property
    def context_digest(self) -> str:
        return semantic_digest(
            {
                "snapshot_digest": self.snapshot_digest,
                "selected_surface_ref": self.selected_surface_ref.to_dict(),
                "selected_artifact_ref": self.selected_artifact_ref.to_dict(),
                "selected_report_digest": self.selected_report.content_digest,
                "tabular_inputs": [
                    {
                        "path": item.path,
                        "artifact_ref": item.artifact_ref.to_dict(),
                        "content_digest": item.content_digest,
                    }
                    for item in self.tabular_inputs
                ],
            }
        )


@dataclass(frozen=True)
class NamedOperand:
    name: str
    kind: OperandKind
    value: Any

    def __post_init__(self) -> None:
        _identifier(self.name, "operand name")
        _validate_operand(self.kind, self.value)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "kind": self.kind, "value": self.value}


@dataclass(frozen=True)
class ObservationReceipt:
    receipt_kind: ReceiptKind
    predicate: str
    state: ReceiptState
    source_refs: tuple[dict[str, Any], ...]
    detail: str

    def __post_init__(self) -> None:
        _identifier(self.predicate, "receipt predicate")
        _text(self.detail, "receipt detail")

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_kind": self.receipt_kind,
            "predicate": self.predicate,
            "state": self.state,
            "source_refs": list(self.source_refs),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CalculationObservation:
    applicability: Applicability
    comparison_outcome: ComparisonOutcome
    target_ref: RecordRef
    input_refs: tuple[RecordRef, ...]
    source_refs: tuple[dict[str, Any], ...]
    operands: tuple[NamedOperand, ...]
    receipts: tuple[ObservationReceipt, ...]
    lineage_status: LineageStatus
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.input_refs or not self.source_refs or not self.receipts:
            raise CalculationCheckContractError(
                "calculation observations require inputs, sources, and finite receipts"
            )
        if len(self.operands) > MAX_OPERANDS:
            raise CalculationCheckContractError("calculation observation exceeds operand ceiling")
        names = [item.name for item in self.operands]
        if len(names) != len(set(names)):
            raise CalculationCheckContractError("calculation operand names must be unique")
        expected = {
            "applicable": {"conformant", "nonconformant"},
            "not_applicable": {"not_applicable"},
            "ambiguous": {"unknown"},
            "unsupported": {"unknown"},
        }[self.applicability]
        if self.comparison_outcome not in expected:
            raise CalculationCheckContractError("applicability and comparison outcome disagree")
        expected_lineage = {
            "applicable": "complete",
            "not_applicable": "not_applicable",
            "ambiguous": "incomplete",
            "unsupported": "incomplete",
        }[self.applicability]
        if self.lineage_status != expected_lineage:
            raise CalculationCheckContractError("applicability and lineage status disagree")
        if self.applicability == "applicable" and not self.operands:
            raise CalculationCheckContractError("applicable calculation requires typed operands")
        if any(not item for item in self.limitations):
            raise CalculationCheckContractError("calculation limitations must not be empty")

    @property
    def observation_digest(self) -> str:
        return semantic_digest(self._projection())

    def _projection(self) -> dict[str, Any]:
        return {
            "applicability": self.applicability,
            "comparison_outcome": self.comparison_outcome,
            "target_ref": self.target_ref.to_dict(),
            "input_refs": [item.to_dict() for item in self.input_refs],
            "source_refs": list(self.source_refs),
            "operands": [item.to_dict() for item in self.operands],
            "receipts": [item.to_dict() for item in self.receipts],
            "lineage_status": self.lineage_status,
            "limitations": list(self.limitations),
        }


class CalculationAdapter(Protocol):
    manifest: CalculationAdapterManifest

    def inspect(self, context: CalculationContext) -> CalculationObservation | None: ...


@dataclass(frozen=True)
class CalculationCheckModule:
    manifest: CalculationCheckManifest
    adapters: tuple[CalculationAdapter, ...]


@dataclass(frozen=True)
class CalculationModuleEvaluation:
    check_manifest: CalculationCheckManifest
    adapter_manifest: CalculationAdapterManifest | None
    state: Literal["observed", "not_observed", "adapter_failed"]
    observation: CalculationObservation | None
    adapter_failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "check_manifest": self.check_manifest.to_dict(),
            "adapter_manifest": (
                self.adapter_manifest.to_dict() if self.adapter_manifest is not None else None
            ),
            "state": self.state,
            "observation": (
                self.observation._projection() if self.observation is not None else None
            ),
            "adapter_failures": list(self.adapter_failures),
        }
        value["module_evaluation_digest"] = semantic_digest(value)
        return value


@dataclass(frozen=True)
class CalculationRegistryEvaluation:
    profile_id: str
    registry_digest: str
    context_digest: str
    modules: tuple[CalculationModuleEvaluation, ...]

    def to_dict(self) -> dict[str, Any]:
        value = {
            "profile_id": self.profile_id,
            "registry_digest": self.registry_digest,
            "context_digest": self.context_digest,
            "modules": [item.to_dict() for item in self.modules],
        }
        value["registry_evaluation_digest"] = semantic_digest(value)
        return value


@dataclass(frozen=True)
class CalculationCheckRegistry:
    modules: tuple[CalculationCheckModule, ...]
    profile_id: str = "deterministic_calculation_check_v1"

    def __post_init__(self) -> None:
        identities = [item.manifest.check_id for item in self.modules]
        if len(identities) != len(set(identities)):
            raise CalculationCheckContractError("duplicate calculation check ID")
        for module in self.modules:
            if not module.adapters:
                raise CalculationCheckContractError("calculation module requires an adapter")
            adapter_ids = [adapter.manifest.adapter_id for adapter in module.adapters]
            if len(adapter_ids) != len(set(adapter_ids)):
                raise CalculationCheckContractError("duplicate calculation adapter ID")

    @property
    def registry_digest(self) -> str:
        return semantic_digest(
            {
                "profile_id": self.profile_id,
                "modules": [
                    {
                        "check_manifest": module.manifest.to_dict(),
                        "adapter_manifests": [
                            adapter.manifest.to_dict()
                            for adapter in sorted(
                                module.adapters, key=lambda item: item.manifest.adapter_id
                            )
                        ],
                    }
                    for module in sorted(self.modules, key=lambda item: item.manifest.check_id)
                ],
            }
        )

    def evaluate(self, context: CalculationContext) -> CalculationRegistryEvaluation:
        evaluations: list[CalculationModuleEvaluation] = []
        for module in sorted(self.modules, key=lambda item: item.manifest.check_id):
            observations: list[tuple[CalculationAdapterManifest, CalculationObservation]] = []
            failures: list[str] = []
            for adapter in sorted(module.adapters, key=lambda item: item.manifest.adapter_id):
                try:
                    observation = adapter.inspect(context)
                except (CalculationCheckContractError, UnicodeError, ValueError) as error:
                    failures.append(f"{adapter.manifest.adapter_id}:{type(error).__name__}")
                    continue
                if observation is not None:
                    observations.append((adapter.manifest, observation))
            if len(observations) > 1:
                evaluations.append(
                    CalculationModuleEvaluation(
                        module.manifest,
                        None,
                        "adapter_failed",
                        None,
                        tuple([*failures, "multiple_adapters_produced_observations"]),
                    )
                )
            elif observations:
                adapter_manifest, observation = observations[0]
                evaluations.append(
                    CalculationModuleEvaluation(
                        module.manifest,
                        adapter_manifest,
                        "observed",
                        observation,
                        tuple(failures),
                    )
                )
            else:
                evaluations.append(
                    CalculationModuleEvaluation(
                        module.manifest,
                        None,
                        "adapter_failed" if failures else "not_observed",
                        None,
                        tuple(failures),
                    )
                )
        return CalculationRegistryEvaluation(
            self.profile_id,
            self.registry_digest,
            context.context_digest,
            tuple(evaluations),
        )


def public_observation_record(
    module: CalculationModuleEvaluation,
    *,
    run_id: str,
    created_at: str,
) -> dict[str, Any] | None:
    if module.observation is None or module.adapter_manifest is None:
        return None
    observation = module.observation
    record_id = f"calculation-observation:{observation.observation_digest.removeprefix('sha256:')}"
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "deterministic_check_observation",
        "deterministic_check_observation_id": record_id,
        "audit_run_id": run_id,
        "check_manifest": module.check_manifest.to_dict(),
        "adapter_manifest": module.adapter_manifest.to_dict(),
        "applicability": observation.applicability,
        "output_ceiling": module.check_manifest.output_ceiling,
        "target_ref": observation.target_ref.to_dict(),
        "input_refs": [item.to_dict() for item in observation.input_refs],
        "source_refs": list(observation.source_refs),
        "operands": [item.to_dict() for item in observation.operands],
        "comparison": {
            "relation": module.check_manifest.comparison_relation,
            "outcome": observation.comparison_outcome,
        },
        "receipts": [item.to_dict() for item in observation.receipts],
        "lineage_status": observation.lineage_status,
        "limitations": list(observation.limitations),
        "non_inferences": list(NON_INFERENCES),
        "production_finding_permitted": False,
        "observation_digest": observation.observation_digest,
        "provenance": controller_provenance("bounded_deterministic_calculation_v1", created_at),
    }


def _validate_operand(kind: OperandKind, value: Any) -> None:
    if kind == "boolean":
        valid = isinstance(value, bool)
    elif kind == "integer":
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif kind == "finite_number":
        valid = (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )
    elif kind == "string":
        valid = isinstance(value, str)
    else:
        if not isinstance(value, list) or len(value) > MAX_ARRAY_ITEMS:
            valid = False
        elif kind == "boolean_array":
            valid = all(isinstance(item, bool) for item in value)
        elif kind == "integer_array":
            valid = all(isinstance(item, int) and not isinstance(item, bool) for item in value)
        elif kind == "finite_number_array":
            valid = all(
                isinstance(item, (int, float))
                and not isinstance(item, bool)
                and math.isfinite(float(item))
                for item in value
            )
        else:
            valid = all(isinstance(item, str) for item in value)
    if not valid:
        raise CalculationCheckContractError(f"invalid value for operand kind {kind}")
    json.dumps(value, allow_nan=False)


def _identifier(value: str, field: str) -> None:
    _text(value, field)
    if any(character.isspace() for character in value):
        raise CalculationCheckContractError(f"{field} must not contain whitespace")


def _text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise CalculationCheckContractError(f"{field} must not be empty")


def _digest(value: str, field: str) -> None:
    if len(value) != 71 or not value.startswith("sha256:"):
        raise CalculationCheckContractError(f"{field} must be a sha256 digest")
    try:
        int(value.removeprefix("sha256:"), 16)
    except ValueError as error:
        raise CalculationCheckContractError(f"{field} must be hexadecimal") from error
