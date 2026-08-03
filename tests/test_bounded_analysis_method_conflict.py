from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    load_capability_detector_manifest,
)
from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.detectors.admission import (
    AdmissionContext,
    admit_finding,
    evaluate_non_maturity_finding_admission,
)
from sc_referee.detectors.bounded_analysis_method_conflict import (
    BoundedAnalysisMethodConflictDetector,
)
from sc_referee.detectors.method_conflict_finding import draft_method_conflict_finding
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.scientific_checks.profiles import scientific_check_release_registry

CHECK_ID = "check:founder-orientation-before-hmm-emission"
REQUIRED = "repair_ril_founder_orientation_before_hmm_emission"
OBSERVED = "use_supplied_founder_alleles_directly_in_hmm_emission"


def _source(path: str, line: int) -> dict[str, object]:
    return {
        "source_kind": "file_span",
        "path": path,
        "locator": f"{path}:{line}-{line}",
        "content_digest": "sha256:" + ("a" if path == "analysis.py" else "b") * 64,
        "start_line": line,
        "end_line": line,
        "quoted_text": "bounded method declaration",
    }


def _case(
    *, requirement: str = REQUIRED, observed: str = OBSERVED
) -> tuple[dict[str, object], dict[str, object]]:
    subject = {
        "record_type": "publication_surface",
        "record_id": "publication-surface:analysis",
    }
    file_ref = {"record_type": "file_record", "record_id": "file:analysis"}
    operation_ref = {"record_type": "operation", "record_id": "operation:writer"}
    artifact_ref = {"record_type": "artifact", "record_id": "artifact:report"}
    scope_path = [
        {
            "source_ref": file_ref,
            "relation": "contains_unique_static_selected_output_writer",
            "target_ref": operation_ref,
        },
        {
            "source_ref": operation_ref,
            "relation": "declares_selected_output_artifact",
            "target_ref": artifact_ref,
        },
        {
            "source_ref": artifact_ref,
            "relation": "selected_by_publication_surface",
            "target_ref": subject,
        },
    ]
    scope_digest = semantic_digest(scope_path)
    answer = {
        "answer_id": "answer:analysis",
        "question_ref": {
            "record_type": "material_question",
            "record_id": "question:analysis",
        },
        "answer_value": {"scale_and_orientation": requirement},
        "answer_digest": "sha256:" + "c" * 64,
        "respondent": {"actor_kind": "human", "actor_id": "scientist:test"},
        "authority_scope": {
            "authority_kind": "scientific_intent",
            "subject_refs": [subject],
            "semantic_dimensions": ["scale_and_orientation"],
        },
    }
    requirement_assertion = {
        "assertion_id": "assertion-verified-posthoc-intent:analysis",
        "subject_ref": subject,
        "predicate": "verified_intended_scale_and_orientation",
        "object": requirement,
        "semantic_role": "intended",
        "assertion_class": "deterministic_derivation",
        "epistemic_status": "accepted",
        "authority_scope": "scientific_intent",
        "independently_checkable": True,
        "finding_eligibility": "ineligible",
        "verification": {
            "status": "verified",
            "method": "deterministic_comparison",
        },
        "source_refs": [_source("report.md", 4), _source("analysis.py", 8)],
        "provenance": {"actor": {"actor_kind": "controller"}},
        "extensions": {
            "x-answer-ref": {"record_type": "answer", "record_id": "answer:analysis"},
            "x-answer-digest": answer["answer_digest"],
            "x-scientific-check-id": CHECK_ID,
            "x-scientific-check-manifest-digest": "sha256:" + "d" * 64,
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    static_assertion = {
        "assertion_id": "assertion:analysis-static",
        "subject_ref": file_ref,
        "predicate": "statically_observed_scale_and_orientation",
        "object": observed,
        "semantic_role": "observed",
        "assertion_class": "deterministic_derivation",
        "epistemic_status": "accepted",
        "authority_scope": "none",
        "independently_checkable": True,
        "finding_eligibility": "ineligible",
        "verification": {"status": "verified", "method": "structural_parser"},
        "source_refs": [_source("analysis.py", 8)],
        "provenance": {"actor": {"actor_kind": "controller"}},
        "extensions": {
            "x-scientific-check-id": CHECK_ID,
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    reported_assertion = {
        "assertion_id": "assertion:analysis-report",
        "subject_ref": artifact_ref,
        "predicate": "reported_scale_and_orientation",
        "object": observed,
        "semantic_role": "reported",
        "assertion_class": "explicit_text_extraction",
        "epistemic_status": "accepted",
        "authority_scope": "reported_wording",
        "independently_checkable": True,
        "finding_eligibility": "ineligible",
        "verification": {"status": "verified", "method": "exact_quote_match"},
        "source_refs": [_source("report.md", 4)],
        "provenance": {"actor": {"actor_kind": "parser"}},
        "extensions": {
            "x-scientific-check-id": CHECK_ID,
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    contract = {
        "contract_id": "contract:analysis",
        "scope": {"level": "analysis", "subject_refs": [subject]},
        "dimensions": {
            "scale_and_orientation": {
                "state": "known",
                "assertion_ids": [requirement_assertion["assertion_id"]],
                "accepted_assertion_ids": [requirement_assertion["assertion_id"]],
            }
        },
    }
    question = {
        "record_type": "material_question",
        "question_id": "question:analysis",
        "status": "answered",
        "extensions": {
            "x-analysis-subject-ref": subject,
            "x-contract-ref": {
                "record_type": "scientific_contract",
                "record_id": "contract:analysis",
            },
            "x-output-ceiling": "question_only",
            "x-posthoc-comparison-forms": {"scale_and_orientation": "value_equals"},
            "x-posthoc-reported-assertion-ids": {
                "scale_and_orientation": [
                    static_assertion["assertion_id"],
                    reported_assertion["assertion_id"],
                ]
            },
            "x-scientific-check-id": CHECK_ID,
            "x-scientific-check-scope-join-path": scope_path,
            "x-scientific-check-scope-join-digest": scope_digest,
        },
    }
    locked: dict[str, object] = {
        "audit_run_id": "audit:analysis",
        "locked_at": "2026-07-30T20:00:00Z",
        "scientific_contracts": [contract],
        "semantic_assertions": [
            requirement_assertion,
            static_assertion,
            reported_assertion,
        ],
        "answers": [answer],
        "file_records": [
            {
                "file_record_id": "file:analysis",
                "entry_kind": "regular_file",
                "asset_identity_ref": {
                    "record_type": "asset_identity",
                    "record_id": "identity:source",
                },
            }
        ],
        "operations": [
            {
                "operation_id": "operation:writer",
                "inspection_status": "supported",
                "implementation": {"name": "python.call:<dynamic>.write_text"},
                "output_refs": [artifact_ref],
            }
        ],
        "artifacts": [
            {
                "artifact_id": "artifact:report",
                "kind": "report",
                "producer_operation_refs": [operation_ref],
                "asset_identity_ref": {
                    "record_type": "asset_identity",
                    "record_id": "identity:report",
                },
            }
        ],
        "publication_surfaces": [
            {
                "publication_surface_id": "publication-surface:analysis",
                "status": "resolved",
                "selection": {
                    "kind": "resolved",
                    "selected_surface_refs": [artifact_ref],
                },
            }
        ],
        "asset_identities": [
            {
                "asset_identity_id": "identity:source",
                "asset_ref": file_ref,
                "tier": "full_digest",
            },
            {
                "asset_identity_id": "identity:report",
                "asset_ref": artifact_ref,
                "tier": "full_digest",
            },
        ],
    }
    return locked, question


@pytest.fixture
def detector(schema_root) -> BoundedAnalysisMethodConflictDetector:
    manifest = load_capability_detector_manifest(
        default_capability_manifest_root(),
        schema_root,
        BoundedAnalysisMethodConflictDetector.detector_id,
    )
    manifest["implementation"][  # type: ignore[index]
        "implementation_digest"
    ] = BoundedAnalysisMethodConflictDetector.implementation_digest()
    binding = next(
        item
        for item in scientific_check_release_registry().method_conflict_bindings
        if item.check_id == CHECK_ID
    )
    manifest["extensions"]["x-scientific-check-ids"] = [CHECK_ID]  # type: ignore[index]
    binding = replace(binding, detector_manifest_digest=semantic_digest(manifest))
    return BoundedAnalysisMethodConflictDetector(manifest, (binding,))


def _result(
    detector: BoundedAnalysisMethodConflictDetector,
    locked: dict[str, object],
    question: dict[str, object],
) -> dict[str, object]:
    return detector.evaluate(locked, question)


def test_exact_analysis_method_conflict_is_evaluation_only_and_replay_stable(
    detector, schema_root
) -> None:
    locked, question = _case()

    first = _result(detector, locked, question)
    second = _result(detector, locked, question)

    assert canonical_json(first) == canonical_json(second)
    assert first["state"] == "evaluation_finding_candidate"
    assert first["extensions"]["x-production-finding-permitted"] is False
    assert first["extensions"]["x-review-case-profile"] == (
        "analysis_method_requirement_consistency:1.0.0"
    )
    assert str(first["extensions"]["x-review-case-digest"]).startswith("sha256:")
    assert first["candidate"]["assessment_type"] == "finding"
    assert "does not establish that the source ran" in first["candidate"]["bounded_statement"]
    assert len(first["counterevidence_execution"]) == 10
    assert all(
        item["status"] == "completed" and item["outcome"] == "no_counterevidence"
        for item in first["counterevidence_execution"]
    )
    LocalSchemaRegistry(schema_root).validate(first)


def test_complete_conflict_has_a_schema_valid_draft_but_no_ambient_finding_authority(
    detector, schema_root
) -> None:
    locked, question = _case()
    result = _result(detector, locked, question)
    draft = draft_method_conflict_finding(result, detector.bindings[0])
    promoted_shape = deepcopy(result)
    promoted_shape["state"] = "finding_candidate"
    promoted_shape["detector_maturity"] = "validated"
    context = AdmissionContext(
        finding_draft=draft,
        source_references_resolved=True,
        detector_qualification_applies=False,
        wording_constraints_satisfied=True,
        expected_deterministic_input_digest=str(result["deterministic_input_digest"]),
        required_counterevidence_check_ids=detector.check_ids,
        non_inferences=(
            "No project execution is established.",
            "No numerical causality or universal scientific correctness is established.",
        ),
    )

    assert evaluate_non_maturity_finding_admission(promoted_shape, context) is not None
    assert admit_finding(promoted_shape, context) is None
    qualified_context = replace(context, detector_qualification_applies=True)
    finding = admit_finding(promoted_shape, qualified_context)
    assert finding is not None
    LocalSchemaRegistry(schema_root).validate(finding)


def test_matching_analysis_method_is_one_covered_negative(detector, schema_root) -> None:
    locked, question = _case(requirement=OBSERVED)

    result = _result(detector, locked, question)

    assert result["state"] == "no_issue_detected_within_coverage"
    assert "candidate" not in result
    assert result["coverage"]["status"] == "covered"
    LocalSchemaRegistry(schema_root).validate(result)


def test_report_only_binding_uses_one_plane_and_one_edge_scope(detector, schema_root) -> None:
    manifest = deepcopy(detector.manifest)
    binding = replace(
        detector.bindings[0],
        required_evidence_planes=("reported_text",),
        required_assertion_roles=("reported",),
        detector_manifest_digest=semantic_digest(manifest),
    )
    report_only = BoundedAnalysisMethodConflictDetector(manifest, (binding,))
    locked, question = _case()
    subject = question["extensions"]["x-analysis-subject-ref"]
    artifact_ref = {"record_type": "artifact", "record_id": "artifact:report"}
    scope_path = [
        {
            "source_ref": artifact_ref,
            "relation": "selected_by_publication_surface",
            "target_ref": subject,
        }
    ]
    scope_digest = semantic_digest(scope_path)
    question["extensions"]["x-posthoc-reported-assertion-ids"] = {
        "scale_and_orientation": ["assertion:analysis-report"]
    }
    question["extensions"]["x-scientific-check-scope-join-path"] = scope_path
    question["extensions"]["x-scientific-check-scope-join-digest"] = scope_digest
    for assertion_id in (
        "assertion-verified-posthoc-intent:analysis",
        "assertion:analysis-report",
    ):
        _assertion(locked, assertion_id)["extensions"]["x-scientific-check-scope-join-digest"] = (
            scope_digest
        )

    result = _result(report_only, locked, question)

    assert result["state"] == "evaluation_finding_candidate"
    static_check = next(
        item
        for item in result["counterevidence_execution"]
        if item["check_id"] == "check:static-method-uniqueness"
    )
    assert static_check["outcome"] == "no_counterevidence"
    assert "does not require" in static_check["notes"]
    LocalSchemaRegistry(schema_root).validate(result)


def test_static_only_second_language_binding_uses_selected_source_scope(
    detector, schema_root
) -> None:
    registry = scientific_check_release_registry()
    module = next(
        item
        for item in registry.modules
        if item.manifest.check_id == "check:mvmr-cross-exposure-covariance"
    )
    manifest = deepcopy(detector.manifest)
    manifest["extensions"]["x-scientific-check-ids"] = sorted(  # type: ignore[index]
        [CHECK_ID, module.manifest.check_id]
    )
    founder = replace(detector.bindings[0], detector_manifest_digest=semantic_digest(manifest))
    mvmr = replace(
        founder,
        binding_id="method-conflict-binding:mvmr-cross-exposure-covariance-v1",
        check_id=module.manifest.check_id,
        check_version=module.manifest.check_version,
        check_manifest_digest=module.manifest.manifest_digest,
        dimension=module.manifest.dimension,
        comparison_form=module.manifest.comparison_form,
        operand_kind="canonical_scalar",
        required_evidence_planes=("static_source",),
        required_semantic_roles=module.manifest.semantic_roles,
        required_assertion_roles=("observed",),
    )
    static_only = BoundedAnalysisMethodConflictDetector(manifest, (founder, mvmr))
    locked, question = _case(
        requirement="provided_cross_exposure_covariance",
        observed="zero_cross_exposure_covariance",
    )
    subject = question["extensions"]["x-analysis-subject-ref"]
    artifact_ref = {"record_type": "artifact", "record_id": "artifact:report"}
    scope_path = [
        {
            "source_ref": artifact_ref,
            "relation": "selected_source_artifact_of_publication_surface",
            "target_ref": subject,
        }
    ]
    scope_digest = semantic_digest(scope_path)
    question_extensions = question["extensions"]
    question_extensions["x-scientific-check-id"] = module.manifest.check_id
    question_extensions["x-posthoc-comparison-forms"] = {"measurement_model": "value_equals"}
    question_extensions["x-posthoc-reported-assertion-ids"] = {
        "measurement_model": ["assertion:analysis-static"]
    }
    question_extensions["x-scientific-check-scope-join-path"] = scope_path
    question_extensions["x-scientific-check-scope-join-digest"] = scope_digest
    answer = locked["answers"][0]
    answer["answer_value"] = {"measurement_model": "provided_cross_exposure_covariance"}
    answer["authority_scope"]["semantic_dimensions"] = ["measurement_model"]
    contract = locked["scientific_contracts"][0]
    contract["dimensions"] = {"measurement_model": next(iter(contract["dimensions"].values()))}
    requirement = _assertion(locked, "assertion-verified-posthoc-intent:analysis")
    requirement["predicate"] = "verified_intended_measurement_model"
    requirement["object"] = "provided_cross_exposure_covariance"
    static = _assertion(locked, "assertion:analysis-static")
    static["subject_ref"] = artifact_ref
    static["predicate"] = "statically_observed_measurement_model"
    static["object"] = "zero_cross_exposure_covariance"
    for assertion in (requirement, static):
        assertion["extensions"]["x-scientific-check-id"] = module.manifest.check_id
        assertion["extensions"]["x-scientific-check-scope-join-digest"] = scope_digest

    result = _result(static_only, locked, question)

    assert result["state"] == "evaluation_finding_candidate"
    assert "static-source" in result["candidate"]["bounded_statement"]
    scope_check = next(
        item
        for item in result["counterevidence_execution"]
        if item["check_id"] == "check:selected-output-scope-closure"
    )
    assert scope_check["outcome"] == "no_counterevidence"
    LocalSchemaRegistry(schema_root).validate(result)


def test_non_allowlisted_question_is_an_unsupported_path(detector, schema_root) -> None:
    locked, question = _case()
    question["extensions"]["x-scientific-check-id"] = "check:another-method"

    result = _result(detector, locked, question)

    assert result["state"] == "unsupported_path"
    assert result["applicability"]["status"] == "not_applicable"
    assert "candidate" not in result
    LocalSchemaRegistry(schema_root).validate(result)


def test_missing_scope_identity_suppresses_candidate(detector, schema_root) -> None:
    locked, question = _case()
    locked["asset_identities"][0]["tier"] = "weak_fingerprint"

    result = _result(detector, locked, question)

    assert result["state"] == "insufficient_semantics"
    selected_scope = next(
        item
        for item in result["counterevidence_execution"]
        if item["check_id"] == "check:selected-output-scope-closure"
    )
    assert selected_scope["outcome"] == "counterevidence_found"
    assert "candidate" not in result
    LocalSchemaRegistry(schema_root).validate(result)


@pytest.mark.parametrize(
    ("check_id", "mutation"),
    [
        (
            "check:analysis-requirement-authority",
            lambda locked: locked["answers"][0]["respondent"].update({"actor_kind": "model"}),
        ),
        (
            "check:reported-method-uniqueness",
            lambda locked: _append_assertion_copy(
                locked, "assertion:analysis-report", "assertion:extra-report"
            ),
        ),
        (
            "check:static-method-uniqueness",
            lambda locked: _append_assertion_copy(
                locked, "assertion:analysis-static", "assertion:extra-static"
            ),
        ),
        (
            "check:observed-plane-agreement",
            lambda locked: _assertion(locked, "assertion:analysis-report").update(
                {"object": REQUIRED}
            ),
        ),
        (
            "check:selected-output-scope-closure",
            lambda locked: locked["artifacts"][0].update({"producer_operation_refs": []}),
        ),
        (
            "check:alternate-or-superseding-intent",
            lambda locked: _append_assertion_copy(
                locked,
                "assertion-verified-posthoc-intent:analysis",
                "assertion-verified-posthoc-intent:alternate",
            ),
        ),
        (
            "check:governing-protocol-amendment",
            lambda locked: _append_scoped_signal(
                locked, "assertion:protocol-amendment", "governing_protocol_amendment"
            ),
        ),
        (
            "check:approved-method-deviation",
            lambda locked: _append_scoped_signal(
                locked, "assertion:approved-deviation", "approved_method_deviation"
            ),
        ),
        (
            "check:conditional-applicability",
            lambda locked: _append_scoped_signal(
                locked,
                "assertion:conditional-applicability",
                "method_obligation_applicability",
                object_value="conditional",
            ),
        ),
        (
            "check:sensitivity-or-unsupported-qualifier",
            lambda locked: _assertion(locked, "assertion:analysis-report")["extensions"].update(
                {"x-sensitivity-only": True}
            ),
        ),
    ],
)
def test_each_finite_counterevidence_mutation_suppresses_candidate(
    detector, schema_root, check_id, mutation
) -> None:
    locked, question = _case()
    mutation(locked)

    result = _result(detector, locked, question)

    assert result["state"] == "insufficient_semantics"
    check = next(
        item for item in result["counterevidence_execution"] if item["check_id"] == check_id
    )
    assert check["outcome"] == "counterevidence_found"
    assert "candidate" not in result
    LocalSchemaRegistry(schema_root).validate(result)


def _assertion(locked: dict[str, object], assertion_id: str) -> dict[str, object]:
    return next(
        item for item in locked["semantic_assertions"] if item["assertion_id"] == assertion_id
    )


def _append_assertion_copy(locked: dict[str, object], source_id: str, target_id: str) -> None:
    copied = deepcopy(_assertion(locked, source_id))
    copied["assertion_id"] = target_id
    locked["semantic_assertions"].append(copied)


def _append_scoped_signal(
    locked: dict[str, object],
    assertion_id: str,
    predicate: str,
    *,
    object_value: str = "present",
) -> None:
    requirement = _assertion(locked, "assertion-verified-posthoc-intent:analysis")
    locked["semantic_assertions"].append(
        {
            "assertion_id": assertion_id,
            "subject_ref": deepcopy(requirement["subject_ref"]),
            "predicate": predicate,
            "object": object_value,
            "semantic_role": "intended",
            "epistemic_status": "accepted",
            "source_refs": deepcopy(requirement["source_refs"]),
            "extensions": deepcopy(requirement["extensions"]),
        }
    )
