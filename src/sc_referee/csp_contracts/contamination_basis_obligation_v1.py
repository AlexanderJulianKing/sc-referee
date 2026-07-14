"""Closed dual-premise contract for an exact contamination-basis obligation."""
from __future__ import annotations

from collections.abc import Mapping
import math

from .between_group_adjustment_obligation_v1 import ContractManifest


CONTRACT_TYPE = "contamination_basis_obligation/v1"
MEASUREMENT_FIELDS = (
    "measurement_kind", "axis_identity", "rows_and_aggregation", "transform_kind",
    "transform_detail", "basis_identity", "positive_evidence", "population_state_evidence",
    "source_stratum_applicability", "blindness_attestation", "measurement_scope_authority",
)
CAUSAL_FIELDS = (
    "pre_exposure", "non_descendancy", "outside_estimand_pathway", "required_adjustment",
    "assignment_context", "exact_basis_adequacy", "causal_scope_authority",
)
REQUIRED_FIELDS = MEASUREMENT_FIELDS + CAUSAL_FIELDS
AUTHORIZED_CONSUMER = "contamination_confound"
VALIDATOR_VERSION = "contamination-basis-obligation-v1"
AUTHORITY_ATTESTATION = "I am responsible for this result's scientific interpretation"
CONSEQUENCE = (
    "Confirmation may authorize a conditional contamination_confound finding for this exact scope."
)
PREMISE_TEMPLATE = (
    "The exact basis is accepted as a valid measurement of the scoped pre-exposure nuisance, "
    "and conditioning on that exact basis is required for the scoped estimand."
)

_MEASUREMENT_KINDS = {
    "external_measurement_artifact",
    "orthogonal_origin_artifact",
    "expression_proxy_with_positive_nonexpression",
}
_TRANSFORM_KINDS = {"continuous_identity", "binary_threshold", "frozen_external_basis"}
_FORBIDDEN_EVIDENCE = {
    "ambient_enrichment", "low_observed_expression", "marker_list_omission",
    "algorithm_label", "exposure_separation", "non_containment", "desired_verdict",
}
_FORBIDDEN_CAUSAL_REASONS = {"association", "r_squared", "coefficient_movement", "technical"}
_BLIND_TO = {
    "exposure", "outcomes", "target_results", "coefficient",
    "measurement_exposure_association", "containment", "desired_verdict",
}


def _mapping(value: object, keys: set[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == keys


def _identity(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and ":" in value


def _digest(value: object) -> bool:
    return (
        isinstance(value, str) and value.startswith("sha256:")
        and len(value) == 71 and all(char in "0123456789abcdef" for char in value[7:])
    )


def _evidence(value: object) -> bool:
    return isinstance(value, str) and _identity(value)


def validate_values(values: Mapping[str, object]) -> tuple[str, ...]:
    """Validate closed values; labels, association, and geometry never substitute for evidence."""
    problems: list[str] = []
    if set(values) != set(REQUIRED_FIELDS):
        problems.append("required_fields_incomplete_or_unknown")

    kind = values.get("measurement_kind")
    if kind not in _MEASUREMENT_KINDS:
        problems.append("measurement_kind_invalid")

    axis = values.get("axis_identity")
    axis_keys = {"artifact_id", "run_id", "version", "vector_field", "unit", "scale",
                 "orientation", "value_digest"}
    if (not _mapping(axis, axis_keys)
            or not all(isinstance(axis[key], str) and axis[key].strip()
                       for key in axis_keys - {"value_digest", "vector_field"})
            or not (axis["vector_field"] is None
                    or (isinstance(axis["vector_field"], str)
                        and axis["vector_field"].strip()))
            or not _digest(axis["value_digest"])):
        problems.append("axis_identity_invalid")

    rows = values.get("rows_and_aggregation")
    row_keys = {"input_row_ledger_identity", "output_row_ledger_identity",
                "source_mapping_identity", "aggregation_ledger_identity", "aggregation_rule",
                "exclusions", "missing_rule", "output_vector_digest"}
    if (not _mapping(rows, row_keys)
            or not all(_identity(rows[key]) for key in (
                "input_row_ledger_identity", "output_row_ledger_identity",
                "source_mapping_identity", "aggregation_ledger_identity"))
            or rows["aggregation_rule"] not in {"identity", "per_unit_mean", "frozen_external"}
            or not isinstance(rows["exclusions"], (tuple, list))
            or rows["missing_rule"] != "abstain"
            or not _digest(rows["output_vector_digest"])):
        problems.append("rows_and_aggregation_invalid")

    transform = values.get("transform_kind")
    if transform not in _TRANSFORM_KINDS:
        problems.append("transform_kind_invalid")
    if isinstance(axis, Mapping):
        if transform == "frozen_external_basis" and axis.get("vector_field") is not None:
            problems.append("external_basis_separate_vector_forbidden")
        elif transform != "frozen_external_basis" and not (
            isinstance(axis.get("vector_field"), str) and axis["vector_field"].strip()
        ):
            problems.append("axis_vector_field_missing")
    detail = values.get("transform_detail")
    if transform == "continuous_identity":
        if (not _mapping(detail, {"source_vector_digest", "output_digest"})
                or not _digest(detail["source_vector_digest"])
                or not _digest(detail["output_digest"])):
            problems.append("continuous_transform_detail_invalid")
    elif transform == "binary_threshold":
        keys = {"source_vector_digest", "threshold", "threshold_provenance",
                "comparison", "equality", "missing_rule", "numeric_representation", "output_digest"}
        if (not _mapping(detail, keys)
                or not _digest(detail["source_vector_digest"])
                or not isinstance(detail["threshold"], float)
                or not math.isfinite(detail["threshold"])
                or not _identity(detail["threshold_provenance"])
                or detail["comparison"] != "strict_greater_than"
                or detail["equality"] != "false"
                or detail["missing_rule"] != "abstain"
                or detail["numeric_representation"] != "float64"
                or not _digest(detail["output_digest"])):
            problems.append("binary_transform_detail_invalid")
    elif transform == "frozen_external_basis":
        keys = {"policy_id", "policy_version", "input_identities", "ordered_columns",
                "replay_identity", "source_vector_digest", "output_digest"}
        if (not _mapping(detail, keys) or not _identity(detail["policy_id"])
                or not isinstance(detail["policy_version"], str)
                or not isinstance(detail["input_identities"], (tuple, list))
                or not isinstance(detail["ordered_columns"], (tuple, list))
                or not detail["ordered_columns"]
                or len(set(detail["ordered_columns"])) != len(detail["ordered_columns"])
                or not _identity(detail["replay_identity"])
                or not _digest(detail["source_vector_digest"])
                or not _digest(detail["output_digest"])):
            problems.append("external_basis_transform_detail_invalid")

    basis = values.get("basis_identity")
    if (not _mapping(basis, {"basis_ledger_identity", "ordered_columns", "output_digest"})
            or not _identity(basis["basis_ledger_identity"])
            or not isinstance(basis["ordered_columns"], (tuple, list))
            or not basis["ordered_columns"]
            or len(set(basis["ordered_columns"])) != len(basis["ordered_columns"])
            or not _digest(basis["output_digest"])):
        problems.append("basis_identity_invalid")
    elif isinstance(detail, Mapping) and detail.get("output_digest") != basis["output_digest"]:
        problems.append("basis_output_digest_mismatch")
    if (transform == "frozen_external_basis" and isinstance(detail, Mapping)
            and isinstance(basis, Mapping)
            and tuple(detail.get("ordered_columns", ()))
                != tuple(basis.get("ordered_columns", ()))):
        problems.append("external_basis_column_order_mismatch")

    positive = values.get("positive_evidence")
    positive_ok = (
        _mapping(positive, {"kind", "records"})
        and positive["kind"] not in _FORBIDDEN_EVIDENCE
        and positive["kind"] in {
            "empty_droplet_derived_external_fraction", "orthogonal_origin_validation",
            "positive_negligible_endogenous_expression",
        }
        and isinstance(positive["records"], (tuple, list))
        and bool(positive["records"])
        and all(_evidence(item) for item in positive["records"])
    )
    if not positive_ok:
        problems.append("positive_nonexpression_evidence_missing")
    if (kind == "expression_proxy_with_positive_nonexpression"
            and isinstance(positive, Mapping)
            and positive.get("kind") != "positive_negligible_endogenous_expression"):
        problems.append("expression_proxy_positive_evidence_missing")

    population = values.get("population_state_evidence")
    population_ok = _mapping(population, {"required", "records", "coverage_policy"})
    if not population_ok:
        problems.append("population_state_evidence_invalid")
    elif kind == "expression_proxy_with_positive_nonexpression":
        if (population["required"] is not True or not population["records"]
                or population["coverage_policy"] != "complete_feature_population_state_source"):
            problems.append("population_state_coverage_incomplete")
    elif population != {"required": False, "records": (), "coverage_policy": "not_expression_proxy"}:
        problems.append("population_state_evidence_invalid")

    source = values.get("source_stratum_applicability")
    if (not _mapping(source, {"source_strata", "mapping_identity", "comparability_evidence",
                             "cross_stratum_rule"})
            or not isinstance(source["source_strata"], (tuple, list)) or not source["source_strata"]
            or not _identity(source["mapping_identity"])
            or not source["comparability_evidence"]
            or not all(_evidence(item) for item in source["comparability_evidence"])
            or source["cross_stratum_rule"] not in {"single_source_stratum", "frozen_mapping"}):
        problems.append("source_stratum_applicability_invalid")

    blindness = values.get("blindness_attestation")
    if (not _mapping(blindness, {"blind_to", "evidence_id"})
            or set(blindness["blind_to"]) != _BLIND_TO or not _evidence(blindness["evidence_id"])):
        problems.append("blindness_attestation_incomplete")

    measurement_scope = values.get("measurement_scope_authority")
    measurement_scope_keys = {"scope_id", "authority_id", "assay", "population_state",
                              "source", "analysis_id"}
    if (not _mapping(measurement_scope, measurement_scope_keys)
            or not all(isinstance(measurement_scope[key], str) and measurement_scope[key].strip()
                       for key in measurement_scope_keys)):
        problems.append("measurement_scope_authority_invalid")

    for field in ("pre_exposure", "non_descendancy", "outside_estimand_pathway"):
        answer = values.get(field)
        if (not _mapping(answer, {"confirmed", "evidence_id"})
                or answer["confirmed"] is not True or not _evidence(answer["evidence_id"])):
            problems.append(f"{field}_not_established")

    required = values.get("required_adjustment")
    if (not _mapping(required, {"required", "basis", "evidence_id"})
            or required["required"] is not True
            or required["basis"] in _FORBIDDEN_CAUSAL_REASONS
            or required["basis"] != "prespecified_design_obligation"
            or not _evidence(required["evidence_id"])):
        problems.append("design_based_adjustment_reason_missing")

    assignment = values.get("assignment_context")
    if (not _mapping(assignment, {"kind", "assignment_identity", "compatibility_evidence"})
            or assignment["kind"] not in {"observational", "randomized", "other"}
            or not _identity(assignment["assignment_identity"])
            or not _evidence(assignment["compatibility_evidence"])):
        problems.append("assignment_context_invalid")

    adequacy = values.get("exact_basis_adequacy")
    if (not _mapping(adequacy, {"required_basis_identity", "transform_kind", "evidence_id"})
            or not _identity(adequacy["required_basis_identity"])
            or adequacy["transform_kind"] != transform
            or not _evidence(adequacy["evidence_id"])
            or (isinstance(basis, Mapping)
                and adequacy["required_basis_identity"] != basis.get("basis_ledger_identity"))):
        problems.append("exact_basis_adequacy_invalid")

    causal_scope = values.get("causal_scope_authority")
    causal_keys = {"scope_id", "authority_id", "fitted_result_id", "target_coefficient",
                   "exposure_column", "row_ledger_identity", "estimand_id",
                   "measurement_basis_identity", "fitted_design_identity"}
    if (not _mapping(causal_scope, causal_keys)
            or not all(isinstance(causal_scope[key], str) and causal_scope[key].strip()
                       for key in causal_keys)
            or not all(_identity(causal_scope[key]) for key in (
                "scope_id", "authority_id", "fitted_result_id", "row_ledger_identity",
                "estimand_id", "measurement_basis_identity", "fitted_design_identity"))
            or (isinstance(basis, Mapping)
                and causal_scope["measurement_basis_identity"] != basis.get("basis_ledger_identity"))):
        problems.append("causal_scope_authority_invalid")
    return tuple(dict.fromkeys(problems))


MANIFEST = ContractManifest(
    contract_type=CONTRACT_TYPE,
    required_fields=REQUIRED_FIELDS,
    authorized_consumer=AUTHORIZED_CONSUMER,
    validator_version=VALIDATOR_VERSION,
    authority_attestation=AUTHORITY_ATTESTATION,
    consequence=CONSEQUENCE,
    premise_template=PREMISE_TEMPLATE,
    teach_back_ids={field: f"confirm_{field}" for field in REQUIRED_FIELDS},
    validate_values=validate_values,
    stage="C-Stage-2",
    component_field_groups={
        "measurement_contract_identity": MEASUREMENT_FIELDS,
        "causal_contract_identity": CAUSAL_FIELDS,
    },
)
