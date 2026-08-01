from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.posthoc_method_ledger import posthoc_form_allowed
from sc_referee.scientific_checks.core import (
    CheckManifest,
    FrozenInspectionContext,
    MethodConflictBinding,
    NormalizedMethodObservation,
    ScientificCheckModule,
)

ReductionState = Literal[
    "applicable", "not_applicable", "ambiguous", "unsupported", "not_installed"
]
SCIENTIFIC_CHECK_REDUCER_IMPLEMENTATION_DIGEST = sha256_digest(Path(__file__).read_bytes())


class RegistryValidationError(ValueError):
    """Raised when a registry or module cannot satisfy the accepted extension contract."""


@dataclass(frozen=True)
class ModuleEvaluation:
    check_id: str
    check_version: str
    manifest_digest: str
    state: ReductionState
    basis: str
    observations: tuple[NormalizedMethodObservation, ...]
    equivalence_groups: tuple[tuple[str, ...], ...]
    adapter_failures: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "check_id": self.check_id,
            "check_version": self.check_version,
            "manifest_digest": self.manifest_digest,
            "state": self.state,
            "basis": self.basis,
            "observations": [item.to_dict() for item in self.observations],
            "equivalence_groups": [list(item) for item in self.equivalence_groups],
            "adapter_failures": list(self.adapter_failures),
        }
        value["module_evaluation_digest"] = semantic_digest(value)
        return value


@dataclass(frozen=True)
class RegistryEvaluation:
    profile_id: str
    registry_digest: str
    context_digest: str
    modules: tuple[ModuleEvaluation, ...]

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "profile_id": self.profile_id,
            "registry_digest": self.registry_digest,
            "context_digest": self.context_digest,
            "modules": [item.to_dict() for item in self.modules],
        }
        value["registry_evaluation_digest"] = semantic_digest(value)
        return value


@dataclass(frozen=True)
class ScientificCheckRegistry:
    modules: tuple[ScientificCheckModule, ...]
    unavailable_manifests: tuple[CheckManifest, ...] = ()
    method_conflict_bindings: tuple[MethodConflictBinding, ...] = ()
    profile_id: str = "scientific_check_registry_v1"

    def __post_init__(self) -> None:
        if not self.modules:
            raise RegistryValidationError("scientific-check registry must not be empty")
        identities = [
            *(module.manifest.check_id for module in self.modules),
            *(manifest.check_id for manifest in self.unavailable_manifests),
        ]
        if len(identities) != len(set(identities)):
            raise RegistryValidationError("duplicate scientific check ID")
        for module in self.modules:
            _validate_module(module)
        _validate_method_conflict_bindings(self.modules, self.method_conflict_bindings)

    @property
    def canonical_modules(self) -> tuple[ScientificCheckModule, ...]:
        return tuple(sorted(self.modules, key=lambda item: item.manifest.check_id))

    @property
    def registry_digest(self) -> str:
        return semantic_digest(
            {
                "profile_id": self.profile_id,
                "modules": [
                    {
                        "check_id": module.manifest.check_id,
                        "check_version": module.manifest.check_version,
                        "manifest_digest": module.declared_manifest_digest,
                        "adapters": [
                            {
                                "adapter_id": manifest.adapter_id,
                                "adapter_version": manifest.adapter_version,
                                "manifest_digest": manifest.manifest_digest,
                            }
                            for manifest in sorted(
                                module.adapter_manifests, key=lambda item: item.adapter_id
                            )
                        ],
                    }
                    for module in self.canonical_modules
                ],
                "unavailable_modules": [
                    {
                        "check_id": manifest.check_id,
                        "check_version": manifest.check_version,
                        "manifest_digest": manifest.manifest_digest,
                    }
                    for manifest in sorted(
                        self.unavailable_manifests, key=lambda item: item.check_id
                    )
                ],
                "method_conflict_bindings": [
                    binding.to_dict()
                    for binding in sorted(
                        self.method_conflict_bindings, key=lambda item: item.binding_id
                    )
                ],
            }
        )

    def evaluate(self, context: FrozenInspectionContext) -> RegistryEvaluation:
        evaluations = [_evaluate_module(module, context) for module in self.canonical_modules]
        evaluations.extend(
            ModuleEvaluation(
                check_id=manifest.check_id,
                check_version=manifest.check_version,
                manifest_digest=manifest.manifest_digest,
                state="not_installed",
                basis="This known scientific check is explicitly unavailable in the active registry.",
                observations=(),
                equivalence_groups=(),
                adapter_failures=(),
            )
            for manifest in self.unavailable_manifests
        )
        evaluations.sort(key=lambda item: item.check_id)
        return RegistryEvaluation(
            profile_id=self.profile_id,
            registry_digest=self.registry_digest,
            context_digest=context.context_digest,
            modules=tuple(evaluations),
        )


def _validate_module(module: ScientificCheckModule) -> None:
    manifest = module.manifest
    if module.declared_manifest_digest != manifest.manifest_digest:
        raise RegistryValidationError(f"manifest digest mismatch for check {manifest.check_id}")
    if not posthoc_form_allowed(manifest.dimension, manifest.comparison_form):
        raise RegistryValidationError(f"unsupported comparison form for check {manifest.check_id}")
    adapter_manifests = {item.adapter_id: item for item in module.adapter_manifests}
    adapters = {item.adapter_id: item for item in module.adapters}
    if len(adapter_manifests) != len(module.adapter_manifests):
        raise RegistryValidationError(f"duplicate adapter ID in check {manifest.check_id}")
    if len(adapters) != len(module.adapters):
        raise RegistryValidationError(
            f"duplicate adapter implementation in check {manifest.check_id}"
        )
    if not adapters or set(adapters) != set(adapter_manifests):
        raise RegistryValidationError(
            f"adapter manifest and implementation set mismatch for check {manifest.check_id}"
        )
    for adapter_id, adapter in adapters.items():
        adapter_manifest = adapter_manifests[adapter_id]
        if adapter.adapter_version != adapter_manifest.adapter_version:
            raise RegistryValidationError(f"adapter version mismatch for {adapter_id}")
        if adapter.implementation_digest != adapter_manifest.implementation_digest:
            raise RegistryValidationError(
                f"adapter implementation digest mismatch for {adapter_id}"
            )
        if adapter.recognition_grammar_digest != adapter_manifest.recognition_grammar_digest:
            raise RegistryValidationError(
                f"adapter recognition grammar digest mismatch for {adapter_id}"
            )
        if not set(adapter_manifest.semantic_roles).issubset(manifest.semantic_roles):
            raise RegistryValidationError(f"adapter {adapter_id} declares unknown semantic roles")


def _validate_method_conflict_bindings(
    modules: tuple[ScientificCheckModule, ...],
    bindings: tuple[MethodConflictBinding, ...],
) -> None:
    if len({item.binding_id for item in bindings}) != len(bindings):
        raise RegistryValidationError("duplicate method-conflict binding ID")
    if len({item.check_id for item in bindings}) != len(bindings):
        raise RegistryValidationError("one scientific check has multiple method-conflict bindings")
    modules_by_id = {module.manifest.check_id: module for module in modules}
    for binding in bindings:
        module = modules_by_id.get(binding.check_id)
        if module is None:
            raise RegistryValidationError(
                f"method-conflict binding references unavailable check {binding.check_id}"
            )
        manifest = module.manifest
        if (
            binding.check_version != manifest.check_version
            or binding.check_manifest_digest != manifest.manifest_digest
            or binding.dimension != manifest.dimension
            or binding.comparison_form != manifest.comparison_form
        ):
            raise RegistryValidationError(
                f"method-conflict binding drifts from check {binding.check_id}"
            )
        candidate_kinds = {item.operand.kind for item in manifest.requirement_candidates}
        if candidate_kinds != {binding.operand_kind}:
            raise RegistryValidationError(
                f"method-conflict operand kind drifts from check {binding.check_id}"
            )
        adapter_planes = {item.evidence_plane for item in module.adapter_manifests}
        if not set(binding.required_evidence_planes).issubset(adapter_planes):
            raise RegistryValidationError(
                f"method-conflict binding requests an unavailable evidence plane for {binding.check_id}"
            )
        if not set(binding.required_semantic_roles).issubset(manifest.semantic_roles):
            raise RegistryValidationError(
                f"method-conflict binding requests an unavailable semantic role for {binding.check_id}"
            )


def _evaluate_module(
    module: ScientificCheckModule, context: FrozenInspectionContext
) -> ModuleEvaluation:
    manifest = module.manifest
    observations: list[NormalizedMethodObservation] = []
    failures: list[str] = []
    for adapter in sorted(module.adapters, key=lambda item: item.adapter_id):
        try:
            observation = adapter.inspect(context)
            _validate_observation(module, observation)
            observations.append(observation)
        except Exception as error:  # adapter failures are a localized unsupported boundary
            failures.append(f"{adapter.adapter_id}:{type(error).__name__}")

    canonical = _canonical_observations(observations)
    equivalence_groups = _equivalence_groups(canonical)
    applicable = [item for item in canonical if item.applicability == "applicable"]
    explicit_ambiguous = [item for item in canonical if item.applicability == "ambiguous"]
    explicit_unsupported = [item for item in canonical if item.applicability == "unsupported"]
    explicit_not_applicable = [item for item in canonical if item.applicability == "not_applicable"]

    state: ReductionState
    basis: str
    if explicit_ambiguous:
        state = "ambiguous"
        basis = "At least one adapter reported an unresolved bounded ambiguity."
    elif applicable and _applicable_disagree(applicable):
        state = "ambiguous"
        basis = "Applicable adapters disagree on operand or analysis-scope join."
    elif applicable and _unscoped_observation_disagrees(applicable, explicit_unsupported):
        state = "ambiguous"
        basis = (
            "An exact but unscoped source observation disagrees with the analysis-scoped operand."
        )
    elif applicable:
        state = "applicable"
        basis = "One unambiguous normalized operand is supported by completed finite checks."
    elif failures or explicit_unsupported:
        state = "unsupported"
        basis = (
            "No applicable operand was produced and at least one adapter boundary is unsupported."
        )
    elif explicit_not_applicable:
        state = "not_applicable"
        basis = "Every completed adapter determined that its exact representation does not apply."
    else:
        state = "unsupported"
        basis = "No adapter produced a valid normalized observation."

    return ModuleEvaluation(
        check_id=manifest.check_id,
        check_version=manifest.check_version,
        manifest_digest=module.declared_manifest_digest,
        state=state,
        basis=basis,
        observations=canonical,
        equivalence_groups=equivalence_groups,
        adapter_failures=tuple(sorted(failures)),
    )


def _validate_observation(
    module: ScientificCheckModule, observation: NormalizedMethodObservation
) -> None:
    manifest = module.manifest
    adapter_manifests = {item.adapter_id: item for item in module.adapter_manifests}
    adapter_manifest = adapter_manifests.get(observation.adapter_id)
    if adapter_manifest is None:
        raise RegistryValidationError("adapter emitted an undeclared identity")
    expected = (
        observation.check_id == manifest.check_id
        and observation.check_version == manifest.check_version
        and observation.check_manifest_digest == module.declared_manifest_digest
        and observation.check_implementation_digest == manifest.implementation_digest
        and observation.adapter_version == adapter_manifest.adapter_version
        and observation.adapter_manifest_digest == adapter_manifest.manifest_digest
        and observation.adapter_implementation_digest == adapter_manifest.implementation_digest
        and observation.parser_id == adapter_manifest.parser_id
        and observation.parser_version == adapter_manifest.parser_version
        and observation.evidence_plane == adapter_manifest.evidence_plane
        and observation.output_ceiling == manifest.maturity_tier
    )
    if not expected:
        raise RegistryValidationError("normalized observation identity or authority mismatch")
    if not set(binding.role for binding in observation.role_bindings).issubset(
        adapter_manifest.semantic_roles
    ):
        raise RegistryValidationError("normalized observation contains an undeclared semantic role")
    if observation.applicability == "applicable" and {
        binding.role for binding in observation.role_bindings
    } != set(adapter_manifest.semantic_roles):
        raise RegistryValidationError("applicable observation does not bind every declared role")
    if observation.observed_operand is not None:
        allowed_kind = {
            "value_equals": "canonical_scalar",
            "set_relation": "unique_string_array",
            "step_precedes": "ordered_step_names",
        }[manifest.comparison_form]
        if observation.observed_operand.kind != allowed_kind:
            raise RegistryValidationError("normalized operand does not match comparison form")
    required_receipts = set(adapter_manifest.counterevidence_profiles)
    if (
        observation.applicability == "applicable"
        and {item.receipt_id for item in observation.receipts} != required_receipts
    ):
        raise RegistryValidationError("applicable observation has an incomplete receipt set")
    if not set(manifest.prohibited_inferences).issubset(observation.non_inferences):
        raise RegistryValidationError("normalized observation omits prohibited inferences")


def _canonical_observations(
    observations: list[NormalizedMethodObservation],
) -> tuple[NormalizedMethodObservation, ...]:
    by_value = {canonical_json(item.to_dict()): item for item in observations}
    return tuple(by_value[key] for key in sorted(by_value))


def _equivalence_groups(
    observations: tuple[NormalizedMethodObservation, ...],
) -> tuple[tuple[str, ...], ...]:
    groups: dict[str, list[str]] = {}
    for observation in observations:
        groups.setdefault(observation.equivalence_key, []).append(observation.observation_digest)
    return tuple(tuple(sorted(groups[key])) for key in sorted(groups))


def _applicable_disagree(observations: list[NormalizedMethodObservation]) -> bool:
    operands = {
        canonical_json(item.observed_operand.to_dict())
        for item in observations
        if item.observed_operand is not None
    }
    scope_endpoints = {
        canonical_json(item.scope_join_path[-1].target_ref.to_dict())
        for item in observations
        if item.scope_join_path
    }
    paths_by_target_plane: dict[tuple[str, str], set[str]] = {}
    targets_by_plane: dict[str, set[str]] = {}
    for item in observations:
        target = (
            canonical_json(item.method_target_ref.to_dict())
            if item.method_target_ref is not None
            else "null"
        )
        path = canonical_json([edge.to_dict() for edge in item.scope_join_path])
        paths_by_target_plane.setdefault((target, item.evidence_plane), set()).add(path)
        targets_by_plane.setdefault(item.evidence_plane, set()).add(target)
    return (
        len(operands) != 1
        or len(scope_endpoints) != 1
        or any(len(paths) != 1 for paths in paths_by_target_plane.values())
        or any(len(targets) != 1 for targets in targets_by_plane.values())
    )


def _unscoped_observation_disagrees(
    applicable: list[NormalizedMethodObservation],
    unsupported: list[NormalizedMethodObservation],
) -> bool:
    scoped_operands = {
        canonical_json(item.observed_operand.to_dict())
        for item in applicable
        if item.observed_operand is not None
    }
    incomplete_operands = {
        canonical_json(item.observed_operand.to_dict())
        for item in unsupported
        if item.observed_operand is not None
    }
    return bool(incomplete_operands) and incomplete_operands != scoped_operands
