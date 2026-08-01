from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.version import SCHEMA_VERSION

EXPECTED_COUNT_PROFILE_ID = "expected_count_background_v1"
EXPECTED_COUNT_PROFILE_VERSION = "1.0.0"
EXPECTED_COUNT_LEDGER_PROFILE = "expected_count_method_ledger_v1"

_REQUIRED_DIMENSIONS = (
    "adjustment_set",
    "control_set",
    "dependence_structure",
    "measurement_model",
    "scale_and_orientation",
    "selection_process",
)
EXPECTED_COUNT_REQUIRED_DIMENSIONS = _REQUIRED_DIMENSIONS
SCIENTIFIC_CONTRACT_DIMENSIONS = (
    "target_population",
    "analysis_population",
    "unit_of_analysis",
    "exposure_or_treatment",
    "outcome",
    "estimand",
    "comparison",
    "time_definition",
    "scale_and_orientation",
    "adjustment_set",
    "denominator_or_universe",
    "control_set",
    "dependence_structure",
    "measurement_model",
    "missingness_and_transport",
    "uncertainty_target",
    "selection_process",
)
_ESTIMATORS = {"negative_binomial_glm", "same_stratum_arithmetic_mean"}
_LIKELIHOODS = {"negative_binomial", "not_applicable"}
_LINKS = {"log", "not_applicable"}
_BACKGROUNDS = {"model_predicted_expected_count", "other_same_stratum_observations"}
_GROUPINGS = {"replicate_intercepts", "replicate_specific_background"}
_COVARIATES = {
    "distance",
    "exposure",
    "gc",
    "mappability",
    "restriction_site_count",
}
_GROUP_SPECIFIC_TERMS = {"distance", "gc"}
_EXCLUSIONS = {
    "case_specific_structural_variant",
    "low_mappability",
    "target_observation",
}
_PROFILE_KEYS = {
    "profile_id",
    "profile_version",
    "estimator_family",
    "likelihood_family",
    "link_function",
    "background_scope",
    "grouping_structure",
    "covariate_terms",
    "group_specific_terms",
    "training_exclusions",
    "target_excluded",
    "analysis_resolution_bp",
}

EXPECTED_COUNT_PROFILE_MANIFEST: dict[str, Any] = {
    "profile_id": EXPECTED_COUNT_PROFILE_ID,
    "profile_version": EXPECTED_COUNT_PROFILE_VERSION,
    "ledger_profile": EXPECTED_COUNT_LEDGER_PROFILE,
    "required_dimensions": list(_REQUIRED_DIMENSIONS),
    "field_dimensions": {
        "analysis_resolution_bp": "scale_and_orientation",
        "background_scope": "control_set",
        "covariate_terms": "adjustment_set",
        "estimator_family": "measurement_model",
        "group_specific_terms": "adjustment_set",
        "grouping_structure": "dependence_structure",
        "likelihood_family": "measurement_model",
        "link_function": "measurement_model",
        "target_excluded": "selection_process",
        "training_exclusions": "selection_process",
    },
    "allowed_values": {
        "background_scope": sorted(_BACKGROUNDS),
        "covariate_terms": sorted(_COVARIATES),
        "estimator_family": sorted(_ESTIMATORS),
        "group_specific_terms": sorted(_GROUP_SPECIFIC_TERMS),
        "grouping_structure": sorted(_GROUPINGS),
        "likelihood_family": sorted(_LIKELIHOODS),
        "link_function": sorted(_LINKS),
        "training_exclusions": sorted(_EXCLUSIONS),
    },
    "materiality_tolerance_supported": False,
    "project_code_execution": False,
}


class MethodContractError(ValueError):
    """Raised when a method profile or its evidence boundary is incomplete."""


def build_expected_count_profile(
    *,
    estimator_family: str,
    likelihood_family: str,
    link_function: str,
    background_scope: str,
    grouping_structure: str,
    covariate_terms: Sequence[str],
    group_specific_terms: Sequence[str],
    training_exclusions: Sequence[str],
    target_excluded: bool,
    analysis_resolution_bp: int,
) -> dict[str, Any]:
    """Build one canonical closed expected/background profile."""

    _require_member(estimator_family, _ESTIMATORS, "estimator_family")
    _require_member(likelihood_family, _LIKELIHOODS, "likelihood_family")
    _require_member(link_function, _LINKS, "link_function")
    _require_member(background_scope, _BACKGROUNDS, "background_scope")
    _require_member(grouping_structure, _GROUPINGS, "grouping_structure")
    covariates = _closed_string_set(covariate_terms, _COVARIATES, "covariate_terms")
    group_terms = _closed_string_set(
        group_specific_terms, _GROUP_SPECIFIC_TERMS, "group_specific_terms"
    )
    exclusions = _closed_string_set(training_exclusions, _EXCLUSIONS, "training_exclusions")
    if type(target_excluded) is not bool:
        raise MethodContractError("target_excluded must be a boolean")
    if type(analysis_resolution_bp) is not int or analysis_resolution_bp <= 0:
        raise MethodContractError("analysis_resolution_bp must be a positive integer")

    if estimator_family == "same_stratum_arithmetic_mean":
        if likelihood_family != "not_applicable" or link_function != "not_applicable":
            raise MethodContractError(
                "same-stratum arithmetic mean requires non-model likelihood and link values"
            )
        if background_scope != "other_same_stratum_observations":
            raise MethodContractError(
                "same-stratum arithmetic mean requires the other-observations background"
            )
    if estimator_family == "negative_binomial_glm":
        if likelihood_family != "negative_binomial" or link_function != "log":
            raise MethodContractError(
                "negative-binomial GLM requires negative_binomial likelihood and log link"
            )
        if background_scope != "model_predicted_expected_count":
            raise MethodContractError(
                "negative-binomial GLM requires model-predicted expected counts"
            )
    if not target_excluded or "target_observation" not in exclusions:
        raise MethodContractError(
            "expected-count profile requires explicit target-observation exclusion"
        )

    return {
        "profile_id": EXPECTED_COUNT_PROFILE_ID,
        "profile_version": EXPECTED_COUNT_PROFILE_VERSION,
        "estimator_family": estimator_family,
        "likelihood_family": likelihood_family,
        "link_function": link_function,
        "background_scope": background_scope,
        "grouping_structure": grouping_structure,
        "covariate_terms": covariates,
        "group_specific_terms": group_terms,
        "training_exclusions": exclusions,
        "target_excluded": target_excluded,
        "analysis_resolution_bp": analysis_resolution_bp,
    }


def validate_expected_count_profile(value: object) -> dict[str, Any]:
    """Validate and canonicalize an already serialized profile."""

    if not isinstance(value, Mapping) or set(value) != _PROFILE_KEYS:
        raise MethodContractError("expected-count profile has unsupported or missing fields")
    if value.get("profile_id") != EXPECTED_COUNT_PROFILE_ID:
        raise MethodContractError("expected-count profile_id is unsupported")
    if value.get("profile_version") != EXPECTED_COUNT_PROFILE_VERSION:
        raise MethodContractError("expected-count profile_version is unsupported")
    return build_expected_count_profile(
        estimator_family=_string(value.get("estimator_family"), "estimator_family"),
        likelihood_family=_string(value.get("likelihood_family"), "likelihood_family"),
        link_function=_string(value.get("link_function"), "link_function"),
        background_scope=_string(value.get("background_scope"), "background_scope"),
        grouping_structure=_string(value.get("grouping_structure"), "grouping_structure"),
        covariate_terms=_string_sequence(value.get("covariate_terms"), "covariate_terms"),
        group_specific_terms=_string_sequence(
            value.get("group_specific_terms"), "group_specific_terms"
        ),
        training_exclusions=_string_sequence(
            value.get("training_exclusions"), "training_exclusions"
        ),
        target_excluded=_boolean(value.get("target_excluded"), "target_excluded"),
        analysis_resolution_bp=_integer(
            value.get("analysis_resolution_bp"), "analysis_resolution_bp"
        ),
    )


def expected_count_dimension_values(profile: object) -> dict[str, Any]:
    """Project a closed profile onto the six accepted ScientificContract dimensions."""

    value = validate_expected_count_profile(profile)
    profile_binding = {
        "profile_id": EXPECTED_COUNT_PROFILE_ID,
        "profile_version": EXPECTED_COUNT_PROFILE_VERSION,
    }
    return {
        "adjustment_set": {
            **profile_binding,
            "covariate_terms": deepcopy(value["covariate_terms"]),
            "group_specific_terms": deepcopy(value["group_specific_terms"]),
        },
        "control_set": {
            **profile_binding,
            "background_scope": value["background_scope"],
        },
        "dependence_structure": {
            **profile_binding,
            "grouping_structure": value["grouping_structure"],
        },
        "measurement_model": {
            **profile_binding,
            "estimator_family": value["estimator_family"],
            "likelihood_family": value["likelihood_family"],
            "link_function": value["link_function"],
        },
        "scale_and_orientation": {
            **profile_binding,
            "analysis_resolution_bp": value["analysis_resolution_bp"],
        },
        "selection_process": {
            **profile_binding,
            "training_exclusions": deepcopy(value["training_exclusions"]),
            "target_excluded": value["target_excluded"],
        },
    }


def expected_count_profile_from_dimensions(values: Mapping[str, object]) -> dict[str, Any]:
    """Reconstruct the closed profile from exactly six dimension values."""

    if set(values) != set(_REQUIRED_DIMENSIONS):
        missing = sorted(set(_REQUIRED_DIMENSIONS) - set(values))
        extra = sorted(set(values) - set(_REQUIRED_DIMENSIONS))
        raise MethodContractError(
            f"expected-count dimensions are incomplete; missing={missing}, extra={extra}"
        )
    normalized: dict[str, Mapping[str, object]] = {}
    for dimension in _REQUIRED_DIMENSIONS:
        raw = values[dimension]
        if not isinstance(raw, Mapping):
            raise MethodContractError(f"{dimension} must be a closed object")
        normalized[dimension] = raw
        if raw.get("profile_id") != EXPECTED_COUNT_PROFILE_ID:
            raise MethodContractError(f"{dimension} has the wrong profile_id")
        if raw.get("profile_version") != EXPECTED_COUNT_PROFILE_VERSION:
            raise MethodContractError(f"{dimension} has the wrong profile_version")
    _require_exact_dimension_keys(
        normalized["adjustment_set"],
        {"profile_id", "profile_version", "covariate_terms", "group_specific_terms"},
        "adjustment_set",
    )
    _require_exact_dimension_keys(
        normalized["control_set"],
        {"profile_id", "profile_version", "background_scope"},
        "control_set",
    )
    _require_exact_dimension_keys(
        normalized["dependence_structure"],
        {"profile_id", "profile_version", "grouping_structure"},
        "dependence_structure",
    )
    _require_exact_dimension_keys(
        normalized["measurement_model"],
        {
            "profile_id",
            "profile_version",
            "estimator_family",
            "likelihood_family",
            "link_function",
        },
        "measurement_model",
    )
    _require_exact_dimension_keys(
        normalized["scale_and_orientation"],
        {"profile_id", "profile_version", "analysis_resolution_bp"},
        "scale_and_orientation",
    )
    _require_exact_dimension_keys(
        normalized["selection_process"],
        {
            "profile_id",
            "profile_version",
            "training_exclusions",
            "target_excluded",
        },
        "selection_process",
    )
    return build_expected_count_profile(
        estimator_family=_string(
            normalized["measurement_model"].get("estimator_family"), "estimator_family"
        ),
        likelihood_family=_string(
            normalized["measurement_model"].get("likelihood_family"), "likelihood_family"
        ),
        link_function=_string(
            normalized["measurement_model"].get("link_function"), "link_function"
        ),
        background_scope=_string(
            normalized["control_set"].get("background_scope"), "background_scope"
        ),
        grouping_structure=_string(
            normalized["dependence_structure"].get("grouping_structure"),
            "grouping_structure",
        ),
        covariate_terms=_string_sequence(
            normalized["adjustment_set"].get("covariate_terms"), "covariate_terms"
        ),
        group_specific_terms=_string_sequence(
            normalized["adjustment_set"].get("group_specific_terms"),
            "group_specific_terms",
        ),
        training_exclusions=_string_sequence(
            normalized["selection_process"].get("training_exclusions"),
            "training_exclusions",
        ),
        target_excluded=_boolean(
            normalized["selection_process"].get("target_excluded"), "target_excluded"
        ),
        analysis_resolution_bp=_integer(
            normalized["scale_and_orientation"].get("analysis_resolution_bp"),
            "analysis_resolution_bp",
        ),
    )


def project_expected_count_ledger(
    *,
    claim_id: str,
    contract: Mapping[str, object],
    assertions: Sequence[Mapping[str, object]],
) -> dict[str, Any]:
    """Recompute a complete intended/reported ledger from named v0.14.0 records."""

    if contract.get("contract_id") is None:
        raise MethodContractError("scientific contract identity is unavailable")
    scope = contract.get("scope")
    if not isinstance(scope, Mapping) or scope.get("level") != "claim":
        raise MethodContractError("expected-count ledger requires one claim-scoped contract")
    subjects = scope.get("subject_refs")
    if not _contains_ref(subjects, "claim", claim_id):
        raise MethodContractError("scientific contract scope does not match the Claim")

    by_id = {
        str(assertion["assertion_id"]): assertion
        for assertion in assertions
        if isinstance(assertion.get("assertion_id"), str)
    }
    dimensions = contract.get("dimensions")
    if not isinstance(dimensions, Mapping):
        raise MethodContractError("scientific contract dimensions are unavailable")
    intended_values: dict[str, object] = {}
    intended_ids: list[str] = []
    source_refs: list[dict[str, Any]] = []
    for dimension in _REQUIRED_DIMENSIONS:
        slot = dimensions.get(dimension)
        if not isinstance(slot, Mapping) or slot.get("state") != "known":
            raise MethodContractError(f"{dimension} is not a known intended-method dimension")
        accepted = slot.get("accepted_assertion_ids")
        if not isinstance(accepted, Sequence) or isinstance(accepted, (str, bytes)):
            raise MethodContractError(f"{dimension} has no accepted assertion identity")
        candidates = [
            by_id[str(assertion_id)]
            for assertion_id in accepted
            if str(assertion_id) in by_id
            and by_id[str(assertion_id)].get("predicate") == f"verified_intended_{dimension}"
        ]
        if len(candidates) != 1:
            raise MethodContractError(
                f"{dimension} does not have one controller-verified intended assertion"
            )
        assertion = candidates[0]
        _verify_intended_assertion(assertion, claim_id)
        intended_values[dimension] = deepcopy(assertion.get("object"))
        intended_ids.append(str(assertion["assertion_id"]))
        source_refs.extend(_source_refs(assertion))

    intended_profile = expected_count_profile_from_dimensions(intended_values)
    reported = [
        assertion
        for assertion in assertions
        if assertion.get("predicate") == "reported_expected_count_background_profile"
        and _ref_equals(assertion.get("subject_ref"), "claim", claim_id)
        and assertion.get("epistemic_status") == "accepted"
    ]
    if len(reported) != 1:
        raise MethodContractError("ledger requires one unambiguous reported expected-count profile")
    reported_assertion = reported[0]
    _verify_reported_assertion(reported_assertion, claim_id)
    reported_profile = validate_expected_count_profile(reported_assertion.get("object"))
    source_refs.extend(_source_refs(reported_assertion))

    ledger: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "projection_profile": EXPECTED_COUNT_LEDGER_PROFILE,
        "method_profile_id": EXPECTED_COUNT_PROFILE_ID,
        "method_profile_version": EXPECTED_COUNT_PROFILE_VERSION,
        "profile_manifest_digest": semantic_digest(EXPECTED_COUNT_PROFILE_MANIFEST),
        "claim_id": claim_id,
        "contract_id": str(contract["contract_id"]),
        "intended_assertion_ids": sorted(intended_ids),
        "reported_assertion_id": str(reported_assertion["assertion_id"]),
        "intended_profile": intended_profile,
        "reported_profile": reported_profile,
        "source_refs": _deduplicate_source_refs(source_refs),
        "completeness": "complete",
    }
    ledger["ledger_digest"] = semantic_digest(ledger)
    return ledger


def profiles_conflict(ledger: Mapping[str, object]) -> bool:
    """Return exact inequality only for one validated complete ledger."""

    if ledger.get("projection_profile") != EXPECTED_COUNT_LEDGER_PROFILE:
        raise MethodContractError("unsupported method-ledger projection profile")
    intended = validate_expected_count_profile(ledger.get("intended_profile"))
    reported = validate_expected_count_profile(ledger.get("reported_profile"))
    return intended != reported


def _verify_intended_assertion(assertion: Mapping[str, object], claim_id: str) -> None:
    if not _ref_equals(assertion.get("subject_ref"), "claim", claim_id):
        raise MethodContractError("intended assertion has the wrong Claim scope")
    actor = _actor_kind(assertion)
    verification = assertion.get("verification")
    if (
        assertion.get("semantic_role") != "intended"
        or assertion.get("assertion_class") != "deterministic_derivation"
        or assertion.get("epistemic_status") != "accepted"
        or assertion.get("authority_scope") != "scientific_intent"
        or assertion.get("independently_checkable") is not True
        or assertion.get("finding_eligibility") != "eligible"
        or actor != "controller"
        or not isinstance(verification, Mapping)
        or verification.get("status") != "verified"
        or verification.get("method") != "deterministic_comparison"
    ):
        raise MethodContractError("intended profile premise is not controller-verified")


def _verify_reported_assertion(assertion: Mapping[str, object], claim_id: str) -> None:
    verification = assertion.get("verification")
    actor = _actor_kind(assertion)
    if (
        not _ref_equals(assertion.get("subject_ref"), "claim", claim_id)
        or assertion.get("semantic_role") != "reported"
        or assertion.get("assertion_class") != "explicit_text_extraction"
        or assertion.get("authority_scope") != "reported_wording"
        or assertion.get("independently_checkable") is not True
        or assertion.get("finding_eligibility") != "eligible"
        or actor not in {"controller", "parser"}
        or not isinstance(verification, Mapping)
        or verification.get("status") != "verified"
        or verification.get("method") not in {"structural_parser", "deterministic_comparison"}
    ):
        raise MethodContractError("reported profile premise is not structurally verified")


def _actor_kind(assertion: Mapping[str, object]) -> object:
    provenance = assertion.get("provenance")
    if not isinstance(provenance, Mapping):
        return None
    actor = provenance.get("actor")
    return actor.get("actor_kind") if isinstance(actor, Mapping) else None


def _source_refs(assertion: Mapping[str, object]) -> list[dict[str, Any]]:
    refs = assertion.get("source_refs")
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
        raise MethodContractError("method assertion source references are unavailable")
    values = [deepcopy(dict(ref)) for ref in refs if isinstance(ref, Mapping)]
    if not values:
        raise MethodContractError("method assertion source references are unavailable")
    return values


def _deduplicate_source_refs(refs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_value = {canonical_json(ref): deepcopy(dict(ref)) for ref in refs}
    return [by_value[key] for key in sorted(by_value)]


def _closed_string_set(values: Sequence[str], allowed: set[str], field: str) -> list[str]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise MethodContractError(f"{field} must be an array of supported strings")
    normalized = list(values)
    if not all(isinstance(value, str) and value in allowed for value in normalized):
        raise MethodContractError(f"{field} contains an unsupported value")
    if len(normalized) != len(set(normalized)):
        raise MethodContractError(f"{field} must not contain duplicates")
    return sorted(normalized)


def _require_member(value: str, allowed: set[str], field: str) -> None:
    if not isinstance(value, str) or value not in allowed:
        raise MethodContractError(f"{field} is unsupported")


def _require_exact_dimension_keys(
    value: Mapping[str, object], expected: set[str], dimension: str
) -> None:
    if set(value) != expected:
        raise MethodContractError(f"{dimension} has unsupported or missing profile fields")


def _string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise MethodContractError(f"{field} must be a string")
    return value


def _string_sequence(value: object, field: str) -> Sequence[str]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or not all(isinstance(item, str) for item in value)
    ):
        raise MethodContractError(f"{field} must be an array of strings")
    return list(value)


def _boolean(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise MethodContractError(f"{field} must be a boolean")
    return value


def _integer(value: object, field: str) -> int:
    if type(value) is not int:
        raise MethodContractError(f"{field} must be an integer")
    return value


def _ref_equals(value: object, record_type: str, record_id: str) -> bool:
    return (
        isinstance(value, Mapping)
        and value.get("record_type") == record_type
        and value.get("record_id") == record_id
    )


def _contains_ref(value: object, record_type: str, record_id: str) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and any(_ref_equals(item, record_type, record_id) for item in value)
    )
