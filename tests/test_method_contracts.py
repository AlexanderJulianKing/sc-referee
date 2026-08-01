from __future__ import annotations

from copy import deepcopy

import pytest

from sc_referee.core.ids import semantic_digest
from sc_referee.method_contracts import (
    EXPECTED_COUNT_PROFILE_ID,
    EXPECTED_COUNT_PROFILE_MANIFEST,
    EXPECTED_COUNT_PROFILE_VERSION,
    MethodContractError,
    build_expected_count_profile,
    expected_count_dimension_values,
    project_expected_count_ledger,
)


def _profile(*, estimator: str = "negative_binomial_glm") -> dict[str, object]:
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


def _source_ref(line: int) -> dict[str, object]:
    return {
        "source_kind": "file_span",
        "locator": f"report.md:{line}",
        "path": "report.md",
        "content_digest": "sha256:" + "a" * 64,
        "start_line": line,
        "end_line": line,
        "quoted_text": "Exact supported expected-count declaration.",
    }


def _records() -> tuple[dict[str, object], list[dict[str, object]], dict[str, object]]:
    profile = _profile()
    values = expected_count_dimension_values(profile)
    assertion_ids: list[str] = []
    assertions: list[dict[str, object]] = []
    dimensions: dict[str, object] = {}
    for index, (dimension, value) in enumerate(sorted(values.items()), start=1):
        assertion_id = f"assertion:intended:{dimension}"
        assertion_ids.append(assertion_id)
        assertions.append(
            {
                "assertion_id": assertion_id,
                "record_type": "semantic_assertion",
                "subject_ref": {"record_type": "claim", "record_id": "claim:target"},
                "predicate": f"verified_intended_{dimension}",
                "object": value,
                "semantic_role": "intended",
                "assertion_class": "deterministic_derivation",
                "epistemic_status": "accepted",
                "authority_scope": "scientific_intent",
                "independently_checkable": True,
                "finding_eligibility": "eligible",
                "verification": {
                    "status": "verified",
                    "method": "deterministic_comparison",
                },
                "source_refs": [_source_ref(index)],
                "provenance": {
                    "actor": {"actor_kind": "controller", "actor_id": "controller:test"}
                },
            }
        )
        dimensions[dimension] = {
            "state": "known",
            "assertion_ids": [assertion_id],
            "accepted_assertion_ids": [assertion_id],
        }
    contract = {
        "record_type": "scientific_contract",
        "contract_id": "contract:target",
        "status": "draft",
        "scope": {
            "level": "claim",
            "subject_refs": [{"record_type": "claim", "record_id": "claim:target"}],
        },
        "dimensions": dimensions,
    }
    reported = {
        "assertion_id": "assertion:reported:method",
        "record_type": "semantic_assertion",
        "subject_ref": {"record_type": "claim", "record_id": "claim:target"},
        "predicate": "reported_expected_count_background_profile",
        "object": _profile(estimator="same_stratum_arithmetic_mean"),
        "semantic_role": "reported",
        "assertion_class": "explicit_text_extraction",
        "epistemic_status": "accepted",
        "authority_scope": "reported_wording",
        "independently_checkable": True,
        "finding_eligibility": "eligible",
        "verification": {"status": "verified", "method": "structural_parser"},
        "source_refs": [_source_ref(20)],
        "provenance": {"actor": {"actor_kind": "parser", "actor_id": "parser:test"}},
    }
    return contract, assertions, reported


def test_closed_expected_count_profile_is_canonical_and_dimension_mapped() -> None:
    first = _profile()
    second = _profile()

    assert first == second
    assert first["profile_id"] == EXPECTED_COUNT_PROFILE_ID
    assert first["profile_version"] == EXPECTED_COUNT_PROFILE_VERSION
    assert first["covariate_terms"] == ["distance", "gc", "restriction_site_count"]
    assert first["training_exclusions"] == [
        "case_specific_structural_variant",
        "low_mappability",
        "target_observation",
    ]
    assert set(expected_count_dimension_values(first)) == {
        "adjustment_set",
        "control_set",
        "dependence_structure",
        "measurement_model",
        "scale_and_orientation",
        "selection_process",
    }
    assert semantic_digest(EXPECTED_COUNT_PROFILE_MANIFEST).startswith("sha256:")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"estimator_family": "invented"}, "estimator_family"),
        ({"analysis_resolution_bp": True}, "analysis_resolution_bp"),
        ({"covariate_terms": ["gc", "gc"]}, "covariate_terms"),
        (
            {
                "estimator_family": "same_stratum_arithmetic_mean",
                "likelihood_family": "negative_binomial",
            },
            "same-stratum",
        ),
    ],
)
def test_closed_expected_count_profile_rejects_unsupported_values(
    mutation: dict[str, object], message: str
) -> None:
    kwargs = dict(_profile())
    kwargs.pop("profile_id")
    kwargs.pop("profile_version")
    kwargs.update(mutation)

    with pytest.raises(MethodContractError, match=message):
        build_expected_count_profile(**kwargs)  # type: ignore[arg-type]


def test_ledger_projection_is_replayable_and_keeps_authority_planes_separate() -> None:
    contract, assertions, reported = _records()

    first = project_expected_count_ledger(
        claim_id="claim:target",
        contract=contract,
        assertions=[*assertions, reported],
    )
    second = project_expected_count_ledger(
        claim_id="claim:target",
        contract=deepcopy(contract),
        assertions=deepcopy([*assertions, reported]),
    )

    assert first == second
    assert first["projection_profile"] == "expected_count_method_ledger_v1"
    assert first["profile_manifest_digest"] == semantic_digest(EXPECTED_COUNT_PROFILE_MANIFEST)
    assert first["completeness"] == "complete"
    assert first["intended_profile"]["estimator_family"] == "negative_binomial_glm"
    assert first["reported_profile"]["estimator_family"] == ("same_stratum_arithmetic_mean")
    digest_input = dict(first)
    digest = digest_input.pop("ledger_digest")
    assert digest == semantic_digest(digest_input)


def test_model_or_quote_only_assertion_cannot_enter_material_ledger() -> None:
    contract, assertions, reported = _records()
    intended_id = contract["dimensions"]["measurement_model"]["accepted_assertion_ids"][0]  # type: ignore[index]
    intended = next(item for item in assertions if item["assertion_id"] == intended_id)
    intended["provenance"] = {"actor": {"actor_kind": "model", "actor_id": "model:test"}}
    intended["assertion_class"] = "explicit_text_extraction"
    intended["verification"] = {"status": "verified", "method": "exact_quote_match"}

    with pytest.raises(MethodContractError, match="controller-verified"):
        project_expected_count_ledger(
            claim_id="claim:target",
            contract=contract,
            assertions=[*assertions, reported],
        )


def test_partial_or_conflicting_profile_fails_closed() -> None:
    contract, assertions, reported = _records()
    contract["dimensions"]["adjustment_set"] = {  # type: ignore[index]
        "state": "unknown",
        "reason": "No governing adjustment set was supplied.",
    }

    with pytest.raises(MethodContractError, match="adjustment_set"):
        project_expected_count_ledger(
            claim_id="claim:target",
            contract=contract,
            assertions=[*assertions, reported],
        )
