from __future__ import annotations

from copy import deepcopy

import pytest

from sc_referee.detectors.bounded_reported_method_contract import (
    BoundedReportedMethodContractConflictDetector,
)
from sc_referee.method_contracts import (
    build_expected_count_profile,
    expected_count_dimension_values,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry


def _profile(estimator: str) -> dict[str, object]:
    if estimator == "negative_binomial_glm":
        return build_expected_count_profile(
            estimator_family=estimator,
            likelihood_family="negative_binomial",
            link_function="log",
            background_scope="model_predicted_expected_count",
            grouping_structure="replicate_intercepts",
            covariate_terms=["distance", "gc", "restriction_site_count"],
            group_specific_terms=["distance", "gc"],
            training_exclusions=[
                "case_specific_structural_variant",
                "low_mappability",
                "target_observation",
            ],
            target_excluded=True,
            analysis_resolution_bp=20_000,
        )
    return build_expected_count_profile(
        estimator_family="same_stratum_arithmetic_mean",
        likelihood_family="not_applicable",
        link_function="not_applicable",
        background_scope="other_same_stratum_observations",
        grouping_structure="replicate_specific_background",
        covariate_terms=["distance", "mappability"],
        group_specific_terms=[],
        training_exclusions=["low_mappability", "target_observation"],
        target_excluded=True,
        analysis_resolution_bp=20_000,
    )


def _source(line: int) -> dict[str, object]:
    return {
        "source_kind": "file_span",
        "locator": f"report.md:{line}",
        "path": "report.md",
        "content_digest": "sha256:" + "a" * 64,
        "start_line": line,
        "end_line": line,
        "quoted_text": "Exact supported expected-count declaration.",
    }


def _case(
    *,
    intended: str = "negative_binomial_glm",
    reported: str = "same_stratum_arithmetic_mean",
    domain: str = "hic_loop_strength",
) -> tuple[dict[str, object], dict[str, object]]:
    values = expected_count_dimension_values(_profile(intended))
    assertions: list[dict[str, object]] = []
    dimensions: dict[str, object] = {}
    for index, (dimension, value) in enumerate(values.items(), start=1):
        assertion_id = f"assertion:intended:{dimension}"
        assertion = {
            "assertion_id": assertion_id,
            "record_type": "semantic_assertion",
            "subject_ref": {"record_type": "claim", "record_id": "claim:method"},
            "predicate": f"verified_intended_{dimension}",
            "object": value,
            "semantic_role": "intended",
            "assertion_class": "deterministic_derivation",
            "epistemic_status": "accepted",
            "authority_scope": "scientific_intent",
            "independently_checkable": True,
            "finding_eligibility": "eligible",
            "verification": {"status": "verified", "method": "deterministic_comparison"},
            "source_refs": [_source(index)],
            "provenance": {"actor": {"actor_kind": "controller"}},
        }
        assertions.append(assertion)
        dimensions[dimension] = {
            "state": "known",
            "assertion_ids": [assertion_id],
            "accepted_assertion_ids": [assertion_id],
        }
    report_assertion = {
        "assertion_id": "assertion:reported:method",
        "record_type": "semantic_assertion",
        "subject_ref": {"record_type": "claim", "record_id": "claim:method"},
        "predicate": "reported_expected_count_background_profile",
        "object": _profile(reported),
        "semantic_role": "reported",
        "assertion_class": "explicit_text_extraction",
        "epistemic_status": "accepted",
        "authority_scope": "reported_wording",
        "independently_checkable": True,
        "finding_eligibility": "eligible",
        "verification": {"status": "verified", "method": "structural_parser"},
        "source_refs": [_source(20)],
        "provenance": {"actor": {"actor_kind": "parser"}},
        "extensions": {},
    }
    assertions.append(report_assertion)
    claim = {
        "record_type": "claim",
        "claim_id": "claim:method",
        "claim_status": "final",
        "claim_kind": "quantitative",
        "scientific_contract_id": "contract:method",
        "source_refs": [_source(1)],
        "extraction": {
            "method": "deterministic",
            "explicit_source_meaning": True,
            "independently_verified": True,
        },
        "extensions": {
            "x-method-profile-id": "expected_count_background_v1",
            "x-portability-domain": domain,
        },
    }
    contract = {
        "record_type": "scientific_contract",
        "contract_id": "contract:method",
        "scope": {
            "level": "claim",
            "subject_refs": [{"record_type": "claim", "record_id": "claim:method"}],
        },
        "dimensions": dimensions,
        "source_refs": [_source(1)],
    }
    locked = {
        "audit_run_id": "audit:method",
        "locked_at": "2026-07-29T14:00:00Z",
        "claims": [claim],
        "scientific_contracts": [contract],
        "semantic_assertions": assertions,
    }
    return locked, claim


def _manifest() -> dict[str, object]:
    detector = BoundedReportedMethodContractConflictDetector
    return {
        "record_type": "detector_manifest",
        "detector_id": detector.detector_id,
        "detector_version": detector.detector_version,
        "maturity": detector.maturity,
        "implementation": {
            "entry_point": detector.entry_point,
            "deterministic": True,
            "implementation_digest": detector.implementation_digest(),
        },
        "counterevidence_protocol": [{"check_id": check_id} for check_id in detector.check_ids],
        "permitted_output_types": ["disclosure"],
    }


def _detector() -> BoundedReportedMethodContractConflictDetector:
    return BoundedReportedMethodContractConflictDetector(_manifest())


def _extra_assertion(predicate: str, value: object = True) -> dict[str, object]:
    return {
        "assertion_id": f"assertion:counter:{predicate}",
        "record_type": "semantic_assertion",
        "subject_ref": {"record_type": "claim", "record_id": "claim:method"},
        "predicate": predicate,
        "object": value,
        "epistemic_status": "accepted",
        "source_refs": [_source(30)],
    }


def test_exact_method_conflict_is_evaluation_only_and_replay_stable(schema_root) -> None:
    locked, claim = _case()
    detector = _detector()

    first = detector.evaluate(locked, claim)
    second = detector.evaluate(deepcopy(locked), deepcopy(claim))

    LocalSchemaRegistry(schema_root).validate(first)
    assert first == second
    assert first["state"] == "evaluation_finding_candidate"
    assert first["detector_maturity"] == "experimental"
    assert first["extensions"]["x-production-finding-permitted"] is False
    assert all(
        check["status"] == "completed" and check["outcome"] == "no_counterevidence"
        for check in first["counterevidence_execution"]
    )
    statement = first["candidate"]["bounded_statement"].lower()
    assert "which code ran" in statement
    assert "universally correct" in statement
    assert "numeric result is wrong" not in statement


def test_matching_method_profiles_are_one_covered_negative(schema_root) -> None:
    locked, claim = _case(reported="negative_binomial_glm")

    result = _detector().evaluate(locked, claim)

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "no_issue_detected_within_coverage"
    assert result["coverage"]["status"] == "covered"
    assert "candidate" not in result


def test_missing_intended_authority_is_insufficient_semantics(schema_root) -> None:
    locked, claim = _case()
    contract = locked["scientific_contracts"][0]
    contract["dimensions"]["measurement_model"] = {
        "state": "unknown",
        "reason": "No authoritative intended measurement model was supplied.",
    }

    result = _detector().evaluate(locked, claim)

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "insufficient_semantics"
    assert "candidate" not in result


def test_non_profile_claim_is_an_unsupported_path(schema_root) -> None:
    locked, claim = _case()
    claim["extensions"].pop("x-method-profile-id")

    result = _detector().evaluate(locked, claim)

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "unsupported_path"
    assert "candidate" not in result


@pytest.mark.parametrize(
    ("case_kind", "expected_state"),
    [
        ("positive", "evaluation_finding_candidate"),
        ("covered_negative", "no_issue_detected_within_coverage"),
        ("ambiguity", "insufficient_semantics"),
        ("hard_negative", "unsupported_path"),
    ],
)
def test_non_hic_copy_number_read_depth_portability_set(
    schema_root, case_kind: str, expected_state: str
) -> None:
    reported = (
        "negative_binomial_glm"
        if case_kind == "covered_negative"
        else "same_stratum_arithmetic_mean"
    )
    locked, claim = _case(
        reported=reported,
        domain="whole_genome_copy_number_read_depth_windows",
    )
    if case_kind == "ambiguity":
        locked["scientific_contracts"][0]["dimensions"]["control_set"] = {
            "state": "unknown",
            "reason": "The governing read-depth background remains unresolved.",
        }
    elif case_kind == "hard_negative":
        claim["extensions"].pop("x-method-profile-id")

    result = _detector().evaluate(locked, claim)

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == expected_state
    assert "candidate" in result if case_kind == "positive" else "candidate" not in result
    assert result["extensions"]["x-production-finding-permitted"] is False


@pytest.mark.parametrize(
    ("mutation", "check_id"),
    [
        ("alternate", "check:alternate-or-superseding-intent"),
        ("conflicting_report", "check:conflicting-reported-method"),
        ("sensitivity_only", "check:sensitivity-only-qualifier"),
        ("amendment", "check:protocol-amendment"),
        ("deviation", "check:approved-deviation"),
        ("conditional", "check:conditional-applicability"),
        ("scope", "check:claim-method-scope"),
        ("unsupported", "check:unsupported-method-construct"),
    ],
)
def test_each_finite_counterevidence_mutation_suppresses_candidate(
    schema_root, mutation: str, check_id: str
) -> None:
    locked, claim = _case()
    assertions = locked["semantic_assertions"]
    if mutation == "alternate":
        alternate = deepcopy(assertions[0])
        alternate["assertion_id"] = "assertion:intended:alternate"
        assertions.append(alternate)
    elif mutation == "conflicting_report":
        conflicting = deepcopy(assertions[-1])
        conflicting["assertion_id"] = "assertion:reported:conflicting"
        conflicting["object"] = _profile("negative_binomial_glm")
        assertions.append(conflicting)
    elif mutation == "sensitivity_only":
        assertions[-1]["extensions"]["x-sensitivity-only"] = True
    elif mutation == "amendment":
        assertions.append(_extra_assertion("governing_protocol_amendment"))
    elif mutation == "deviation":
        assertions.append(_extra_assertion("approved_method_deviation"))
    elif mutation == "conditional":
        assertions.append(
            _extra_assertion("method_obligation_applicability", "condition_not_established")
        )
    elif mutation == "scope":
        locked["scientific_contracts"][0]["scope"]["subject_refs"] = [
            {"record_type": "claim", "record_id": "claim:other"}
        ]
    elif mutation == "unsupported":
        claim["extensions"]["x-unsupported-method-constructs"] = [
            "conditional background selection"
        ]

    result = _detector().evaluate(locked, claim)

    LocalSchemaRegistry(schema_root).validate(result)
    assert result["state"] == "insufficient_semantics"
    assert "candidate" not in result
    check = next(
        item for item in result["counterevidence_execution"] if item["check_id"] == check_id
    )
    assert check["status"] == "completed"
    assert check["outcome"] == "counterevidence_found"
    assert check["evidence_ids"]
