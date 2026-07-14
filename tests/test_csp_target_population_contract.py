from pathlib import Path

from sc_referee.csp_contracts.target_population_estimand_v1 import (
    AUTHORIZED_CONSUMER,
    CONTRACT_TYPE,
    REQUIRED_FIELDS,
    validate_values,
)


def valid_values():
    return {
        "functional": "population_average",
        "reported_scalar_id": "results.csv#IL7R:effect",
        "target_population_id": "registry:california:v4",
        "census_stratum_columns": ("registry.age_band", "registry.sex"),
        "evaluation_stratum_columns": ("donors.age_band", "donors.sex"),
        "stratum_levels": (("18-39", "F"), ("18-39", "M"), ("40-64", "F"), ("40-64", "M")),
        "stratum_ledger_identity": "strata:v1:age-sex:abc123",
        "census_artifact_identity": "artifact:registry-v4:sha256:abc123",
        "census_count_ledger_identity": "counts:v1:sha256:def456",
        "census_total_n": 1000,
        "census_stratum_counts": (300, 200, 325, 175),
        "weight_vector_identity": "weights:v1:sha256:fedcba",
        "weight_vector": ((300, 1000), (200, 1000), (325, 1000), (175, 1000)),
        "support_policy": "require_observed_evaluation_support",
    }


def test_manifest_contract_and_valid_values():
    assert CONTRACT_TYPE == "target_population_estimand/v1"
    assert AUTHORIZED_CONSUMER == "target_population"
    assert tuple(REQUIRED_FIELDS) == tuple(valid_values())
    assert validate_values(valid_values()) == ()


def test_wrong_functional_policy_and_census_are_rejected():
    values = valid_values() | {
        "functional": "sample_average",
        "support_policy": "allow_extrapolation",
        "census_stratum_counts": (300, 200, 325, 174),
    }
    assert validate_values(values) == (
        "functional_is_not_population_average",
        "support_policy_does_not_require_observed_evaluation_support",
        "census_stratum_counts_do_not_sum_to_total_n",
        "weight_vector_does_not_equal_census_counts_over_total_n",
    )


def test_stringified_or_missing_strata_are_rejected():
    values = valid_values() | {"stratum_levels": (("18-39", "F"), "18-39|M")}
    assert "stratum_level_is_not_typed_tuple" in validate_values(values)


def test_manifest_is_premise_only():
    from sc_referee.csp_contracts.target_population_estimand_v1 import MANIFEST
    text = repr(MANIFEST).lower()
    assert "population average" in text
    assert "exact finite census-stratum distribution" in text
    assert "require_observed_evaluation_support" in text
    assert all(x not in text for x in ("formula", "verdict", "biased"))


def test_registered_without_latest_alias():
    import pytest
    from sc_referee.csp_contracts import get_manifest, registered_contract_types

    assert registered_contract_types() == (
        "between_group_adjustment_obligation/v1",
        "target_population_estimand/v1",
        "contamination_basis_obligation/v1",
    )
    assert get_manifest(CONTRACT_TYPE).contract_type == CONTRACT_TYPE
    with pytest.raises(KeyError, match="unknown CSP contract type/version"):
        get_manifest("target_population_estimand/v2")


def test_cstage3_adds_no_check_finding_or_verdict_emitter():
    package = Path("src/sc_referee")
    files = list(package.rglob("*target_population*.py"))
    assert files == [package / "csp_contracts" / "target_population_estimand_v1.py"]
    source = files[0].read_text()
    assert "Finding(" not in source
    assert "checks.base import Finding" not in source
    assert "def run(" not in source
    assert "status=" not in source
