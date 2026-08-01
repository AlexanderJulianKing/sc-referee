from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, fields, replace

import pytest

from sc_referee.core.ids import canonical_json, sha256_digest
from sc_referee.scientific_checks import (
    AdapterManifest,
    CanonicalOperand,
    CheckManifest,
    EvidenceSpan,
    FrozenBaseRecord,
    FrozenInspectionContext,
    InspectionDocument,
    InspectionReceipt,
    MethodConflictBinding,
    NormalizedMethodObservation,
    RecordRef,
    RegistryValidationError,
    RequirementCandidate,
    RoleBinding,
    ScientificCheckModule,
    ScientificCheckRegistry,
    ScopeJoinEdge,
)

CHECK_IMPLEMENTATION_DIGEST = sha256_digest("test-check-implementation-v1")
ADAPTER_IMPLEMENTATION_DIGEST = sha256_digest("test-adapter-implementation-v1")
PROHIBITED_INFERENCES = (
    "execution",
    "historical_intent",
    "numerical_causality",
    "scientific_correctness",
)


@dataclass(frozen=True)
class FixedAdapter:
    adapter_id: str
    adapter_version: str
    implementation_digest: str
    recognition_grammar_digest: str
    observation: NormalizedMethodObservation

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        assert context.context_digest
        return self.observation


@dataclass(frozen=True)
class FailingAdapter:
    adapter_id: str
    adapter_version: str
    implementation_digest: str
    recognition_grammar_digest: str

    def inspect(self, context: FrozenInspectionContext) -> NormalizedMethodObservation:
        del context
        raise RuntimeError("localized adapter failure")


def _context() -> FrozenInspectionContext:
    surface_ref = RecordRef("publication_surface", "publication-surface:test")
    artifact_ref = RecordRef("artifact", "artifact:test-report")
    file_ref = RecordRef("file_record", "file:test-analysis")
    parser_ref = RecordRef("parser_result", "parser-result:test-analysis")
    source = b"observed = 'forward'\n"
    parser_payload = canonical_json({"parser_id": "parser:test", "supported": True}).encode()
    return FrozenInspectionContext(
        snapshot_digest=sha256_digest("snapshot"),
        selected_surface_ref=surface_ref,
        selected_artifact_ref=artifact_ref,
        documents=(
            InspectionDocument(
                path="analysis.py",
                file_ref=file_ref,
                content=source,
                content_digest=sha256_digest(source),
                media_type="text/x-python",
                parser_result_ref=parser_ref,
                parser_result_payload=parser_payload,
                parser_result_digest=sha256_digest(parser_payload),
            ),
        ),
        base_records=(
            FrozenBaseRecord.from_record(
                surface_ref, {"publication_surface_id": surface_ref.record_id}
            ),
            FrozenBaseRecord.from_record(artifact_ref, {"artifact_id": artifact_ref.record_id}),
            FrozenBaseRecord.from_record(file_ref, {"file_record_id": file_ref.record_id}),
            FrozenBaseRecord.from_record(parser_ref, {"parser_result_id": parser_ref.record_id}),
        ),
    )


def _adapter_manifest(
    adapter_id: str,
    *,
    evidence_plane: str = "static_source",
) -> AdapterManifest:
    return AdapterManifest(
        adapter_id=adapter_id,
        adapter_version="1.0.0",
        implementation_digest=ADAPTER_IMPLEMENTATION_DIGEST,
        recognition_grammar_digest=sha256_digest(f"recognition:{adapter_id}"),
        parser_id="parser:test",
        parser_version="1.0.0",
        source_language="python",
        evidence_plane=evidence_plane,  # type: ignore[arg-type]
        semantic_roles=("method_input",),
        applicability_profile="exact-data-flow-v1",
        counterevidence_profiles=("finite-sibling-check",),
        known_gaps=("dynamic-dispatch",),
    )


def _check_manifest(check_id: str) -> CheckManifest:
    return CheckManifest(
        check_id=check_id,
        check_version="1.0.0",
        implementation_digest=CHECK_IMPLEMENTATION_DIGEST,
        maturity_tier="question_only",
        dimension="scale_and_orientation",
        comparison_form="value_equals",
        requirement_candidates=(
            RequirementCandidate(
                candidate_id="forward",
                label="Forward orientation",
                operand=CanonicalOperand.scalar("forward"),
                authority_basis="A scientist may select this closed orientation for the review.",
            ),
        ),
        semantic_roles=("method_input",),
        required_record_types=("file_record", "artifact", "publication_surface"),
        permitted_wording="Exact review-scoped compatibility only.",
        prohibited_inferences=PROHIBITED_INFERENCES,
    )


def _observation(
    manifest: CheckManifest,
    adapter_manifest: AdapterManifest,
    *,
    operand: str = "forward",
    target_id: str = "operation:test-method",
    endpoint_id: str = "publication-surface:test",
    relation: str = "declares_selected_report",
) -> NormalizedMethodObservation:
    file_ref = RecordRef("file_record", "file:test-analysis")
    parser_ref = RecordRef("parser_result", "parser-result:test-analysis")
    target_ref = RecordRef("operation", target_id)
    return NormalizedMethodObservation(
        check_id=manifest.check_id,
        check_version=manifest.check_version,
        check_manifest_digest=manifest.manifest_digest,
        check_implementation_digest=manifest.implementation_digest,
        adapter_id=adapter_manifest.adapter_id,
        adapter_version=adapter_manifest.adapter_version,
        adapter_manifest_digest=adapter_manifest.manifest_digest,
        adapter_implementation_digest=adapter_manifest.implementation_digest,
        parser_id=adapter_manifest.parser_id,
        parser_version=adapter_manifest.parser_version,
        applicability="applicable",
        completeness="complete",
        evidence_plane=adapter_manifest.evidence_plane,
        method_target_ref=target_ref,
        role_bindings=(RoleBinding("method_input", "founder_state"),),
        observed_operand=CanonicalOperand.scalar(operand),
        evidence_spans=(
            EvidenceSpan(
                file_ref=file_ref,
                path="analysis.py",
                content_digest=sha256_digest(b"observed = 'forward'\n"),
                start_line=1,
                end_line=1,
                start_column=0,
                end_column=20,
                parser_result_ref=parser_ref,
            ),
        ),
        scope_join_path=(
            ScopeJoinEdge(target_ref, relation, RecordRef("publication_surface", endpoint_id)),
        ),
        receipts=(
            InspectionReceipt(
                receipt_id="finite-sibling-check",
                kind="sibling",
                state="passed",
                evidence_digest=sha256_digest("finite-sibling-check-passed"),
                description="The bounded sibling scan completed without a competing target.",
            ),
        ),
        non_inferences=PROHIBITED_INFERENCES,
        output_ceiling="question_only",
    )


def _module(
    check_id: str,
    *,
    adapter_ids: tuple[str, ...] = ("adapter:test",),
    observations: tuple[NormalizedMethodObservation, ...] | None = None,
) -> ScientificCheckModule:
    manifest = _check_manifest(check_id)
    adapter_manifests = tuple(_adapter_manifest(adapter_id) for adapter_id in adapter_ids)
    selected_observations = observations or tuple(
        _observation(manifest, adapter_manifest) for adapter_manifest in adapter_manifests
    )
    adapters = tuple(
        FixedAdapter(
            adapter_id=adapter_manifest.adapter_id,
            adapter_version=adapter_manifest.adapter_version,
            implementation_digest=adapter_manifest.implementation_digest,
            recognition_grammar_digest=adapter_manifest.recognition_grammar_digest,
            observation=observation,
        )
        for adapter_manifest, observation in zip(
            adapter_manifests, selected_observations, strict=True
        )
    )
    return ScientificCheckModule(
        manifest=manifest,
        declared_manifest_digest=manifest.manifest_digest,
        adapter_manifests=adapter_manifests,
        adapters=adapters,
    )


def _binding(
    module: ScientificCheckModule, *, binding_id: str = "binding:test"
) -> MethodConflictBinding:
    return MethodConflictBinding(
        binding_id=binding_id,
        check_id=module.manifest.check_id,
        check_version=module.manifest.check_version,
        check_manifest_digest=module.manifest.manifest_digest,
        detector_id="detector:bounded-analysis-method-conflict",
        detector_version="0.1.0",
        detector_manifest_digest=sha256_digest("detector-manifest"),
        dimension=module.manifest.dimension,
        comparison_form=module.manifest.comparison_form,
        operand_kind="canonical_scalar",
        required_evidence_planes=("static_source",),
        required_semantic_roles=("method_input",),
        required_assertion_roles=("observed",),
        counterevidence_predicates=(
            "approved_method_deviation",
            "governing_protocol_amendment",
            "method_obligation_applicability",
        ),
    )


def test_registry_order_has_no_semantic_effect() -> None:
    alpha = _module("check:alpha", adapter_ids=("adapter:alpha",))
    beta = _module("check:beta", adapter_ids=("adapter:beta",))

    forward = ScientificCheckRegistry((alpha, beta)).evaluate(_context())
    reverse = ScientificCheckRegistry((beta, alpha)).evaluate(_context())

    assert forward.to_dict() == reverse.to_dict()
    assert [item.check_id for item in forward.modules] == ["check:alpha", "check:beta"]


def test_removing_conformance_module_leaves_other_module_byte_stable() -> None:
    substantive = _module("check:substantive", adapter_ids=("adapter:substantive",))
    conformance = _module("check:conformance", adapter_ids=("adapter:conformance",))

    full = ScientificCheckRegistry((substantive, conformance)).evaluate(_context())
    reduced = ScientificCheckRegistry(
        (substantive,), unavailable_manifests=(conformance.manifest,)
    ).evaluate(_context())

    full_substantive = next(item for item in full.modules if item.check_id == "check:substantive")
    reduced_substantive = next(
        item for item in reduced.modules if item.check_id == "check:substantive"
    )
    assert canonical_json(full_substantive.to_dict()) == canonical_json(
        reduced_substantive.to_dict()
    )
    unavailable = next(item for item in reduced.modules if item.check_id == "check:conformance")
    assert unavailable.state == "not_installed"
    assert unavailable.observations == ()
    assert full.registry_digest != reduced.registry_digest


def test_registry_rejects_duplicate_ids_manifest_drift_and_implementation_drift() -> None:
    module = _module("check:duplicate")
    with pytest.raises(RegistryValidationError, match="duplicate scientific check ID"):
        ScientificCheckRegistry((module, module))

    with pytest.raises(RegistryValidationError, match="manifest digest mismatch"):
        ScientificCheckRegistry(
            (replace(module, declared_manifest_digest=sha256_digest("stale-manifest")),)
        )

    drifted_adapter = replace(
        module.adapters[0], implementation_digest=sha256_digest("different-implementation")
    )
    with pytest.raises(RegistryValidationError, match="adapter implementation digest mismatch"):
        ScientificCheckRegistry((replace(module, adapters=(drifted_adapter,)),))


def test_method_conflict_binding_is_content_addressed_and_order_independent() -> None:
    alpha = _module("check:alpha", adapter_ids=("adapter:alpha",))
    beta = _module("check:beta", adapter_ids=("adapter:beta",))
    alpha_binding = _binding(alpha, binding_id="binding:alpha")
    beta_binding = _binding(beta, binding_id="binding:beta")

    forward = ScientificCheckRegistry(
        (alpha, beta), method_conflict_bindings=(alpha_binding, beta_binding)
    )
    reverse = ScientificCheckRegistry(
        (beta, alpha), method_conflict_bindings=(beta_binding, alpha_binding)
    )

    assert forward.registry_digest == reverse.registry_digest
    assert alpha_binding.binding_digest.startswith("sha256:")


def test_method_conflict_binding_rejects_missing_check_drift_and_duplicates() -> None:
    module = _module("check:bound")
    binding = _binding(module)

    with pytest.raises(RegistryValidationError, match="unavailable check"):
        ScientificCheckRegistry((_module("check:other"),), method_conflict_bindings=(binding,))
    with pytest.raises(RegistryValidationError, match="drifts from check"):
        ScientificCheckRegistry(
            (module,),
            method_conflict_bindings=(
                replace(binding, check_manifest_digest=sha256_digest("drift")),
            ),
        )
    with pytest.raises(RegistryValidationError, match="duplicate method-conflict binding ID"):
        ScientificCheckRegistry((module,), method_conflict_bindings=(binding, binding))


def test_method_conflict_binding_rejects_unavailable_plane_role_and_operand_kind() -> None:
    module = _module("check:bound")
    binding = _binding(module)
    with pytest.raises(RegistryValidationError, match="unavailable evidence plane"):
        ScientificCheckRegistry(
            (module,),
            method_conflict_bindings=(
                replace(
                    binding,
                    required_evidence_planes=("reported_text",),
                    required_assertion_roles=("reported",),
                ),
            ),
        )
    with pytest.raises(RegistryValidationError, match="unavailable semantic role"):
        ScientificCheckRegistry(
            (module,),
            method_conflict_bindings=(replace(binding, required_semantic_roles=("unknown_role",)),),
        )
    with pytest.raises(ValueError, match="value_equals requires a canonical scalar binding"):
        replace(binding, operand_kind="unique_string_array")


def test_adapter_receives_only_the_frozen_base_capability_surface() -> None:
    context = _context()

    assert {field.name for field in fields(context)} == {
        "snapshot_digest",
        "selected_surface_ref",
        "selected_artifact_ref",
        "documents",
        "base_records",
        "shared_derivations",
        "scope_join_graph",
    }
    assert isinstance(context.documents[0].content, bytes)
    assert isinstance(context.base_records[0].canonical_payload, bytes)
    with pytest.raises(FrozenInstanceError):
        context.snapshot_digest = sha256_digest("mutation")  # type: ignore[misc]


def test_one_adapter_failure_is_localized_without_altering_another_module() -> None:
    healthy = _module("check:healthy", adapter_ids=("adapter:healthy",))
    failed_manifest = _check_manifest("check:failed")
    failed_adapter_manifest = _adapter_manifest("adapter:failed")
    failed = ScientificCheckModule(
        manifest=failed_manifest,
        declared_manifest_digest=failed_manifest.manifest_digest,
        adapter_manifests=(failed_adapter_manifest,),
        adapters=(
            FailingAdapter(
                adapter_id=failed_adapter_manifest.adapter_id,
                adapter_version=failed_adapter_manifest.adapter_version,
                implementation_digest=failed_adapter_manifest.implementation_digest,
                recognition_grammar_digest=failed_adapter_manifest.recognition_grammar_digest,
            ),
        ),
    )

    result = ScientificCheckRegistry((failed, healthy)).evaluate(_context())

    assert result.modules[0].state == "unsupported"
    assert result.modules[0].adapter_failures == ("adapter:failed:RuntimeError",)
    assert result.modules[1].state == "applicable"
    assert result.modules[1].adapter_failures == ()


def test_equivalent_multi_adapter_observations_deduplicate_canonically() -> None:
    manifest = _check_manifest("check:equivalent")
    first_manifest = _adapter_manifest("adapter:first")
    second_manifest = _adapter_manifest("adapter:second")
    first = _observation(manifest, first_manifest)
    second = _observation(manifest, second_manifest)
    module = _module(
        manifest.check_id,
        adapter_ids=(first_manifest.adapter_id, second_manifest.adapter_id),
        observations=(first, second),
    )

    evaluation = ScientificCheckRegistry((module,)).evaluate(_context()).modules[0]

    assert evaluation.state == "applicable"
    assert len(evaluation.observations) == 2
    assert len(evaluation.equivalence_groups) == 1
    assert len(evaluation.equivalence_groups[0]) == 2


@pytest.mark.parametrize(
    ("mutation", "value"),
    [
        ("operand", "reverse"),
        ("scope", "publication-surface:other"),
        ("same_plane_target", "operation:competing-target"),
        ("same_target_path", "different-owned-relation"),
    ],
)
def test_cross_adapter_disagreement_fails_closed(mutation: str, value: str) -> None:
    manifest = _check_manifest("check:disagreement")
    first_manifest = _adapter_manifest("adapter:first")
    second_manifest = _adapter_manifest("adapter:second")
    first = _observation(manifest, first_manifest)
    kwargs: dict[str, str] = {}
    if mutation == "operand":
        kwargs["operand"] = value
    elif mutation == "scope":
        kwargs["endpoint_id"] = value
    elif mutation == "same_plane_target":
        kwargs["target_id"] = value
    else:
        kwargs["relation"] = value
    second = _observation(manifest, second_manifest, **kwargs)
    module = _module(
        manifest.check_id,
        adapter_ids=(first_manifest.adapter_id, second_manifest.adapter_id),
        observations=(first, second),
    )

    evaluation = ScientificCheckRegistry((module,)).evaluate(_context()).modules[0]

    assert evaluation.state == "ambiguous"
    assert "disagree" in evaluation.basis


def test_distinct_report_and_source_targets_may_corrobate_one_operand_and_scope() -> None:
    manifest = _check_manifest("check:cross-plane")
    source_manifest = _adapter_manifest("adapter:source", evidence_plane="static_source")
    report_manifest = _adapter_manifest("adapter:report", evidence_plane="reported_text")
    source = _observation(manifest, source_manifest, target_id="operation:test-method")
    report = _observation(manifest, report_manifest, target_id="artifact:test-report")
    module = ScientificCheckModule(
        manifest=manifest,
        declared_manifest_digest=manifest.manifest_digest,
        adapter_manifests=(source_manifest, report_manifest),
        adapters=(
            FixedAdapter(
                source_manifest.adapter_id,
                source_manifest.adapter_version,
                source_manifest.implementation_digest,
                source_manifest.recognition_grammar_digest,
                source,
            ),
            FixedAdapter(
                report_manifest.adapter_id,
                report_manifest.adapter_version,
                report_manifest.implementation_digest,
                report_manifest.recognition_grammar_digest,
                report,
            ),
        ),
    )

    evaluation = ScientificCheckRegistry((module,)).evaluate(_context()).modules[0]

    assert evaluation.state == "applicable"
    assert len(evaluation.equivalence_groups) == 2


@pytest.mark.parametrize(
    ("source_operand", "expected_state"),
    [("forward", "applicable"), ("reverse", "ambiguous")],
)
def test_unscoped_exact_source_operand_corroborates_or_suppresses_report(
    source_operand: str, expected_state: str
) -> None:
    manifest = _check_manifest("check:source-suppressor")
    report_manifest = _adapter_manifest("adapter:report", evidence_plane="reported_text")
    source_manifest = _adapter_manifest("adapter:source", evidence_plane="static_source")
    report = _observation(manifest, report_manifest, operand="forward")
    source_scoped = _observation(manifest, source_manifest, operand=source_operand)
    source = replace(
        source_scoped,
        applicability="unsupported",
        completeness="incomplete",
        scope_join_path=(),
        abstention_reason="Typed source-to-analysis lineage is unavailable.",
    )
    module = ScientificCheckModule(
        manifest=manifest,
        declared_manifest_digest=manifest.manifest_digest,
        adapter_manifests=(report_manifest, source_manifest),
        adapters=(
            FixedAdapter(
                report_manifest.adapter_id,
                report_manifest.adapter_version,
                report_manifest.implementation_digest,
                report_manifest.recognition_grammar_digest,
                report,
            ),
            FixedAdapter(
                source_manifest.adapter_id,
                source_manifest.adapter_version,
                source_manifest.implementation_digest,
                source_manifest.recognition_grammar_digest,
                source,
            ),
        ),
    )

    evaluation = ScientificCheckRegistry((module,)).evaluate(_context()).modules[0]

    assert evaluation.state == expected_state
    if expected_state == "ambiguous":
        assert "unscoped source observation disagrees" in evaluation.basis
