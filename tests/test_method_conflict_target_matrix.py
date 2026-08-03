from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from sc_referee.capability_matrix import (
    default_capability_manifest_root,
    load_capability_detector_manifest,
)
from sc_referee.core.ids import semantic_digest
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
from tests.method_conflict_matrix_support import (
    TARGET_RELATIONS,
    TargetRelation,
    add_ambiguous_report_declaration,
    binding_for,
    method_conflict_case,
    selected_report_assertion,
)


@pytest.fixture
def matrix_detector(schema_root) -> BoundedAnalysisMethodConflictDetector:
    manifest = load_capability_detector_manifest(
        default_capability_manifest_root(),
        schema_root,
        BoundedAnalysisMethodConflictDetector.detector_id,
    )
    manifest["implementation"][  # type: ignore[index]
        "implementation_digest"
    ] = BoundedAnalysisMethodConflictDetector.implementation_digest()
    manifest_digest = semantic_digest(manifest)
    bindings = tuple(
        replace(binding, detector_manifest_digest=manifest_digest)
        for binding in scientific_check_release_registry().method_conflict_bindings
    )
    return BoundedAnalysisMethodConflictDetector(manifest, bindings)


def test_target_matrix_has_ten_distinct_generic_relations() -> None:
    assert len(TARGET_RELATIONS) == 10
    assert len({relation.relation_id for relation in TARGET_RELATIONS}) == 10
    assert len({relation.check_id for relation in TARGET_RELATIONS}) == 10


@pytest.mark.parametrize("relation", TARGET_RELATIONS, ids=lambda item: item.relation_id)
def test_each_target_relation_reaches_a_complete_evaluation_candidate(
    relation: TargetRelation,
    matrix_detector: BoundedAnalysisMethodConflictDetector,
    schema_root,
) -> None:
    locked, question = method_conflict_case(
        relation,
        required_candidate_id=relation.required_candidate_id,
        observed_candidate_id=relation.conflicting_candidate_id,
    )

    result = matrix_detector.evaluate(locked, question)

    assert result["state"] == "evaluation_finding_candidate"
    assert result["extensions"]["x-production-finding-permitted"] is False
    assert result["coverage"] == {
        "status": "covered",
        "basis": result["coverage"]["basis"],
        "gaps": [],
    }
    assert all(
        check["status"] == "completed" and check["outcome"] == "no_counterevidence"
        for check in result["counterevidence_execution"]
    )
    binding = binding_for(relation)
    draft = draft_method_conflict_finding(result, binding)
    promotable_shape = deepcopy(result)
    promotable_shape["state"] = "finding_candidate"
    promotable_shape["detector_maturity"] = "validated"
    context = AdmissionContext(
        finding_draft=draft,
        source_references_resolved=True,
        detector_qualification_applies=False,
        wording_constraints_satisfied=True,
        expected_deterministic_input_digest=str(result["deterministic_input_digest"]),
        required_counterevidence_check_ids=matrix_detector.check_ids,
        non_inferences=(
            "No project execution is established.",
            "No numerical causality or universal scientific correctness is established.",
        ),
    )
    assert evaluate_non_maturity_finding_admission(promotable_shape, context) is not None
    assert admit_finding(promotable_shape, context) is None
    LocalSchemaRegistry(schema_root).validate(result)


@pytest.mark.parametrize("relation", TARGET_RELATIONS, ids=lambda item: item.relation_id)
def test_each_target_relation_has_a_corrected_twin_covered_negative(
    relation: TargetRelation,
    matrix_detector: BoundedAnalysisMethodConflictDetector,
    schema_root,
) -> None:
    locked, question = method_conflict_case(
        relation,
        required_candidate_id=relation.required_candidate_id,
        observed_candidate_id=relation.required_candidate_id,
    )

    result = matrix_detector.evaluate(locked, question)

    assert result["state"] == "no_issue_detected_within_coverage"
    assert result["coverage"]["status"] == "covered"
    assert "candidate" not in result
    LocalSchemaRegistry(schema_root).validate(result)


@pytest.mark.parametrize("relation", TARGET_RELATIONS, ids=lambda item: item.relation_id)
def test_each_target_relation_respects_a_pre_authorized_alternative(
    relation: TargetRelation,
    matrix_detector: BoundedAnalysisMethodConflictDetector,
    schema_root,
) -> None:
    locked, question = method_conflict_case(
        relation,
        required_candidate_id=relation.conflicting_candidate_id,
        observed_candidate_id=relation.conflicting_candidate_id,
    )

    result = matrix_detector.evaluate(locked, question)

    assert result["state"] == "no_issue_detected_within_coverage"
    assert "candidate" not in result
    LocalSchemaRegistry(schema_root).validate(result)


@pytest.mark.parametrize("relation", TARGET_RELATIONS, ids=lambda item: item.relation_id)
def test_each_target_relation_abstains_for_a_sensitivity_only_hard_negative(
    relation: TargetRelation,
    matrix_detector: BoundedAnalysisMethodConflictDetector,
    schema_root,
) -> None:
    locked, question = method_conflict_case(
        relation,
        required_candidate_id=relation.required_candidate_id,
        observed_candidate_id=relation.conflicting_candidate_id,
    )
    selected_report_assertion(locked)["extensions"]["x-sensitivity-only"] = True

    result = matrix_detector.evaluate(locked, question)

    assert result["state"] == "insufficient_semantics"
    check = next(
        item
        for item in result["counterevidence_execution"]
        if item["check_id"] == "check:sensitivity-or-unsupported-qualifier"
    )
    assert check["outcome"] == "counterevidence_found"
    assert "candidate" not in result
    LocalSchemaRegistry(schema_root).validate(result)


@pytest.mark.parametrize("relation", TARGET_RELATIONS, ids=lambda item: item.relation_id)
def test_each_target_relation_abstains_for_an_ambiguous_selected_declaration(
    relation: TargetRelation,
    matrix_detector: BoundedAnalysisMethodConflictDetector,
    schema_root,
) -> None:
    locked, question = method_conflict_case(
        relation,
        required_candidate_id=relation.required_candidate_id,
        observed_candidate_id=relation.conflicting_candidate_id,
    )
    add_ambiguous_report_declaration(locked, relation.relation_id)

    result = matrix_detector.evaluate(locked, question)

    assert result["state"] == "insufficient_semantics"
    check = next(
        item
        for item in result["counterevidence_execution"]
        if item["check_id"] == "check:reported-method-uniqueness"
    )
    assert check["outcome"] == "counterevidence_found"
    assert "candidate" not in result
    LocalSchemaRegistry(schema_root).validate(result)


@pytest.mark.parametrize("relation", TARGET_RELATIONS, ids=lambda item: item.relation_id)
def test_each_target_relation_localizes_an_unsupported_profile_without_a_candidate(
    relation: TargetRelation,
    matrix_detector: BoundedAnalysisMethodConflictDetector,
    schema_root,
) -> None:
    locked, question = method_conflict_case(
        relation,
        required_candidate_id=relation.required_candidate_id,
        observed_candidate_id=relation.conflicting_candidate_id,
    )
    question["extensions"]["x-output-ceiling"] = "unsupported_profile"

    result = matrix_detector.evaluate(locked, question)

    assert result["state"] == "unsupported_path"
    assert result["applicability"]["status"] == "not_applicable"
    assert "candidate" not in result
    LocalSchemaRegistry(schema_root).validate(result)


@pytest.mark.parametrize("relation", TARGET_RELATIONS, ids=lambda item: item.relation_id)
def test_target_outcome_survives_identifier_renaming_and_scope_layout_change(
    relation: TargetRelation,
    matrix_detector: BoundedAnalysisMethodConflictDetector,
) -> None:
    chain_case = method_conflict_case(
        relation,
        required_candidate_id=relation.required_candidate_id,
        observed_candidate_id=relation.conflicting_candidate_id,
        namespace="opaque-alpha",
        layout="writer_chain",
    )
    direct_case = method_conflict_case(
        relation,
        required_candidate_id=relation.required_candidate_id,
        observed_candidate_id=relation.conflicting_candidate_id,
        namespace="renamed-zeta",
        layout="direct_artifact",
    )

    chain = matrix_detector.evaluate(*chain_case)
    direct = matrix_detector.evaluate(*direct_case)

    assert chain["state"] == direct["state"] == "evaluation_finding_candidate"
    assert (
        chain["extensions"]["x-review-case-profile"]
        == direct["extensions"]["x-review-case-profile"]
    )
    assert [item["outcome"] for item in chain["counterevidence_execution"]] == [
        item["outcome"] for item in direct["counterevidence_execution"]
    ]
