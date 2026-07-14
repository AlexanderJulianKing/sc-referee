"""Premise manifest for an exact finite target-population estimand."""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from .between_group_adjustment_obligation_v1 import ContractManifest


CONTRACT_TYPE = "target_population_estimand/v1"
REQUIRED_FIELDS = (
    "functional", "reported_scalar_id", "target_population_id",
    "census_stratum_columns", "evaluation_stratum_columns",
    "stratum_levels", "stratum_ledger_identity",
    "census_artifact_identity", "census_count_ledger_identity",
    "census_total_n", "census_stratum_counts",
    "weight_vector_identity", "weight_vector", "support_policy",
)
AUTHORIZED_CONSUMER = "target_population"
VALIDATOR_VERSION = "target-population-estimand-v1"
AUTHORITY_ATTESTATION = "I am responsible for this result's scientific interpretation"
CONSEQUENCE = (
    "Confirmation may allow target_population to use this exact population premise."
)
PREMISE_TEMPLATE = (
    "The reported scalar {reported_scalar_id} targets a population average for "
    "{target_population_id} over its exact finite census-stratum distribution, with "
    "support policy require_observed_evaluation_support."
)

TEACH_BACK_IDS = MappingProxyType({field: f"confirm_{field}" for field in REQUIRED_FIELDS})
TEACH_BACK_IDS = MappingProxyType({
    **dict(TEACH_BACK_IDS),
    "functional": "population_average_exact_census",
    "support_policy": "require_observed_evaluation_support",
})


def _identity(value: object) -> bool:
    return (
        isinstance(value, str) and bool(value.strip())
        and value != "across the population" and (":" in value or "#" in value)
    )


def _columns(value: object) -> bool:
    return (
        isinstance(value, tuple) and bool(value)
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
        and len(set(value)) == len(value)
    )


def _typed_level(level: object, width: int) -> bool:
    return (
        isinstance(level, tuple) and len(level) == width
        and all(item is None or isinstance(item, (str, int, float, bool)) for item in level)
    )


def validate_values(values: Mapping[str, object]) -> tuple[str, ...]:
    """Validate only closed premise values using exact integer-pair arithmetic."""
    problems: list[str] = []
    if values.get("functional") != "population_average":
        problems.append("functional_is_not_population_average")
    if values.get("support_policy") != "require_observed_evaluation_support":
        problems.append("support_policy_does_not_require_observed_evaluation_support")

    for field in (
        "reported_scalar_id", "target_population_id", "stratum_ledger_identity",
        "census_artifact_identity", "census_count_ledger_identity",
        "weight_vector_identity",
    ):
        if not _identity(values.get(field)):
            problems.append(f"{field}_is_not_exact_identity")

    census_columns = values.get("census_stratum_columns")
    evaluation_columns = values.get("evaluation_stratum_columns")
    if not _columns(census_columns):
        problems.append("census_stratum_columns_are_invalid")
    if not _columns(evaluation_columns):
        problems.append("evaluation_stratum_columns_are_invalid")
    if (_columns(census_columns) and _columns(evaluation_columns)
            and len(census_columns) != len(evaluation_columns)):
        problems.append("stratum_column_widths_do_not_match")

    width = len(census_columns) if _columns(census_columns) else 0
    levels = values.get("stratum_levels")
    levels_valid = isinstance(levels, tuple) and bool(levels)
    if not levels_valid:
        problems.append("stratum_levels_are_missing_or_unordered")
        levels = ()
    elif any(not isinstance(level, tuple) for level in levels):
        problems.append("stratum_level_is_not_typed_tuple")
        levels_valid = False
    elif any(not _typed_level(level, width) for level in levels):
        problems.append("stratum_level_width_or_type_is_invalid")
        levels_valid = False
    elif len(set(levels)) != len(levels):
        problems.append("stratum_levels_are_not_unique")
        levels_valid = False

    total = values.get("census_total_n")
    total_valid = isinstance(total, int) and not isinstance(total, bool) and total > 0
    if not total_valid:
        problems.append("census_total_n_is_not_positive_integer")

    counts = values.get("census_stratum_counts")
    counts_valid = (
        isinstance(counts, tuple)
        and all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in counts)
    )
    if not counts_valid:
        problems.append("census_stratum_counts_are_not_nonnegative_integers")
        counts = ()
    if levels_valid and counts_valid and len(counts) != len(levels):
        problems.append("census_stratum_counts_are_not_aligned_with_levels")
    if total_valid and counts_valid and sum(counts) != total:
        problems.append("census_stratum_counts_do_not_sum_to_total_n")

    weights = values.get("weight_vector")
    weights_valid = (
        isinstance(weights, tuple)
        and all(
            isinstance(pair, tuple) and len(pair) == 2
            and all(isinstance(n, int) and not isinstance(n, bool) for n in pair)
            for pair in weights
        )
    )
    if not weights_valid:
        problems.append("weight_vector_is_not_ordered_integer_pairs")
        weights = ()
    if levels_valid and weights_valid and len(weights) != len(levels):
        problems.append("weight_vector_is_not_aligned_with_levels")
    if total_valid and counts_valid and weights_valid:
        if len(weights) != len(counts) or any(
            numerator != count or denominator != total
            for (numerator, denominator), count in zip(weights, counts)
        ):
            problems.append("weight_vector_does_not_equal_census_counts_over_total_n")
    return tuple(problems)


MANIFEST = ContractManifest(
    contract_type=CONTRACT_TYPE,
    required_fields=REQUIRED_FIELDS,
    authorized_consumer=AUTHORIZED_CONSUMER,
    validator_version=VALIDATOR_VERSION,
    authority_attestation=AUTHORITY_ATTESTATION,
    consequence=CONSEQUENCE,
    premise_template=PREMISE_TEMPLATE,
    teach_back_ids=TEACH_BACK_IDS,
    validate_values=validate_values,
    scope_field_bindings={
        "reported_scalar_id": "reported_scalar_id",
        "target_population_id": "target_population_id",
        "census_artifact_identity": "census_artifact_identity",
        "census_count_ledger_identity": "census_count_ledger_identity",
        "stratum_ledger_identity": "stratum_ledger_identity",
        "weight_vector_identity": "weight_vector_identity",
    },
)
