from __future__ import annotations

import hashlib
from collections.abc import Mapping
from fractions import Fraction
from typing import Any

from sc_referee.core.ids import semantic_digest, stable_id


class QualificationMetricInvariantError(ValueError):
    """Closed qualification inputs or their derived evidence are inconsistent."""


METRIC_PROFILE = "root-cause-clustered-metrics-v1"
BOOTSTRAP_PROFILE = "problem-cluster-bootstrap-percentile-v1"
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_DOMAIN = b"sc-referee-bootstrap-v1\0"
METRIC_INPUT_DOMAIN = "sc-referee-qualification-metric-input-v1"

METRIC_NAMES = (
    "workflow_unsafe_candidate_probability",
    "completed_opportunity_false_positive_rate",
    "applicable_covered_opportunity_false_positive_rate",
    "finding_candidate_precision",
    "false_root_localization_rate",
    "overstatement_rate",
    "adjudicated_root_recall",
    "bounded_root_localization_accuracy",
    "abstention_rate",
    "unsupported_rate",
    "detector_error_rate",
    "unresolved_comparison_rate",
)

_UNSAFE_CANDIDATE_STATES = {"overstated_root_match", "false_root_localization"}
_RESOLVED_CANDIDATE_STATES = {
    "bounded_root_match",
    "overstated_root_match",
    "false_root_localization",
}
_RESOLVED_ROOT_STATES = {
    "boundedly_localized",
    "localized_but_overstated",
    "missed",
}
_ABSTENTION_STATES = {"insufficient_semantics", "execution_evidence_unavailable"}
_CONTROL_PROOF_FAMILIES = (
    "clean_execution",
    "documented_external_execution",
    "static_closed_scope",
)
_PROOF_FAMILY_BY_FIXTURE_KIND = {
    "verified_good_fixture": "clean_execution",
    "hard_negative_fixture": "clean_execution",
    "scope_verified_good": "documented_external_execution",
    "static_scope_verified_good": "static_closed_scope",
    "static_scope_hard_negative": "static_closed_scope",
    "positive_issue_fixture": "positive_issue",
    "ambiguous_fixture": "excluded_ambiguous",
}


def compile_qualification_evidence(
    case_outcomes: list[dict[str, Any]], qualification_envelope: Mapping[str, Any]
) -> dict[str, Any]:
    """Recompute every authoritative v0.12 qualification field from case outcomes."""

    outcomes = validate_qualification_case_outcomes(case_outcomes)
    envelope = normalize_qualification_envelope(qualification_envelope)
    first = outcomes[0]
    detector_identity = {
        "detector_id": first["detector_id"],
        "detector_version": first["detector_version"],
        "detector_manifest_digest": first["detector_manifest_digest"],
    }
    corpus_partitions = sorted({str(outcome["corpus_partition"]) for outcome in outcomes})
    problem_ids = sorted({str(outcome["problem_id"]) for outcome in outcomes})
    case_inputs = [
        {
            "case_outcome_ref": _ref("detector_case_outcome", str(outcome["case_outcome_id"])),
            "case_outcome_digest": semantic_digest(outcome),
        }
        for outcome in outcomes
    ]
    input_digest = semantic_digest(
        {
            "domain": METRIC_INPUT_DOMAIN,
            "metric_profile": METRIC_PROFILE,
            "detector_identity": detector_identity,
            "qualification_envelope": envelope,
            "corpus_partitions": corpus_partitions,
            "case_outcome_inputs": case_inputs,
        }
    )
    intervals = _bootstrap_intervals(outcomes, problem_ids, input_digest)
    pairs = _metric_pairs(outcomes)
    metrics = _render_metrics(pairs, intervals)
    control_family_strata = []
    for family in _CONTROL_PROOF_FAMILIES:
        family_outcomes = [
            outcome for outcome in outcomes if outcome["qualification_proof_family"] == family
        ]
        family_metrics: list[dict[str, Any]] = []
        if family_outcomes:
            family_problem_ids = sorted({str(outcome["problem_id"]) for outcome in family_outcomes})
            family_digest = semantic_digest(
                {
                    "domain": "sc-referee-proof-family-stratum-v1",
                    "qualification_input_digest": input_digest,
                    "proof_family": family,
                    "case_outcome_inputs": [
                        {
                            "case_outcome_ref": _ref(
                                "detector_case_outcome", str(outcome["case_outcome_id"])
                            ),
                            "case_outcome_digest": semantic_digest(outcome),
                        }
                        for outcome in family_outcomes
                    ],
                }
            )
            family_metrics = _render_metrics(
                _metric_pairs(family_outcomes),
                _bootstrap_intervals(
                    family_outcomes,
                    family_problem_ids,
                    family_digest,
                ),
            )
        control_family_strata.append(
            {
                "proof_family": family,
                "case_count": len(family_outcomes),
                "metrics": family_metrics,
            }
        )
    excluded = _excluded_case_outcomes(outcomes)
    promotion_evidence_eligible = (
        "public_development" not in corpus_partitions
        and not excluded
        and all(outcome.get("promotion_evidence_eligible") is True for outcome in outcomes)
    )
    return {
        **detector_identity,
        "qualification_envelope": envelope,
        "case_outcome_inputs": case_inputs,
        "corpus_partitions": corpus_partitions,
        "problem_cluster_ids": problem_ids,
        "excluded_case_outcomes": excluded,
        "counts": _public_counts(outcomes),
        "metrics": metrics,
        "control_family_strata": control_family_strata,
        "bootstrap": {
            "profile": BOOTSTRAP_PROFILE,
            "cluster_unit": "problem_id",
            "replicates": BOOTSTRAP_REPLICATES,
            "confidence_level": 0.95,
            "counter_stream": "sha256-counter-rejection-sampling-v1",
            "input_digest": input_digest,
        },
        "promotion_evidence_eligible": promotion_evidence_eligible,
        "metric_set_id": stable_id(
            "qualification-metric-set",
            str(first["detector_id"]),
            str(first["detector_version"]),
            str(first["detector_manifest_digest"]),
            input_digest,
        ),
    }


def verify_qualification_metric_set(
    metric_set: Mapping[str, Any], case_outcomes: list[dict[str, Any]]
) -> None:
    """Fail closed unless every derived public metric field recomputes exactly."""

    envelope = metric_set.get("qualification_envelope")
    if not isinstance(envelope, Mapping):
        raise QualificationMetricInvariantError("Qualification envelope is malformed.")
    expected = compile_qualification_evidence(case_outcomes, envelope)
    derived_fields = (
        "metric_set_id",
        "detector_id",
        "detector_version",
        "detector_manifest_digest",
        "qualification_envelope",
        "case_outcome_inputs",
        "corpus_partitions",
        "problem_cluster_ids",
        "excluded_case_outcomes",
        "counts",
        "metrics",
        "control_family_strata",
        "bootstrap",
        "promotion_evidence_eligible",
    )
    for field in derived_fields:
        if metric_set.get(field) != expected[field]:
            raise QualificationMetricInvariantError(
                f"QualificationMetricSet {field} does not recompute from its exact inputs."
            )
    if metric_set.get("metric_profile") != METRIC_PROFILE:
        raise QualificationMetricInvariantError("Qualification metric profile is not accepted.")
    if metric_set.get("numeric_threshold_policy") != "deferred_until_pilot_threshold_adr":
        raise QualificationMetricInvariantError("Qualification threshold authority is unsupported.")
    if metric_set.get("promotion_permitted") is not False:
        raise QualificationMetricInvariantError("Qualification metrics cannot permit promotion.")


def validate_qualification_case_outcomes(
    values: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not values:
        raise QualificationMetricInvariantError("At least one DetectorCaseOutcome is required.")
    outcomes = sorted(values, key=lambda value: str(value.get("case_outcome_id")))
    identities = {
        (
            str(outcome.get("detector_id")),
            str(outcome.get("detector_version")),
            str(outcome.get("detector_manifest_digest")),
        )
        for outcome in outcomes
    }
    if len(identities) != 1:
        raise QualificationMetricInvariantError("Metric inputs mix detector identities.")
    outcome_ids = [str(outcome.get("case_outcome_id")) for outcome in outcomes]
    case_ids = [str(outcome.get("case_id")) for outcome in outcomes]
    if len(set(outcome_ids)) != len(outcome_ids) or len(set(case_ids)) != len(case_ids):
        raise QualificationMetricInvariantError(
            "Metric inputs must contain one unique outcome per workflow."
        )
    for outcome in outcomes:
        _validate_outcome_projection(outcome)
    return outcomes


def validate_detector_case_outcome_projection(outcome: dict[str, Any]) -> None:
    """Validate one v0.12 case outcome's closed opportunity projection."""

    _validate_outcome_projection(outcome)


def normalize_qualification_envelope(value: Mapping[str, Any]) -> dict[str, list[str]]:
    required = {"issue_classes", "languages", "packages", "operation_forms"}
    if set(value) != required:
        raise QualificationMetricInvariantError("Qualification envelope has unexpected fields.")
    result: dict[str, list[str]] = {}
    for field in sorted(required):
        items = value[field]
        if not isinstance(items, list) or any(
            not isinstance(item, str) or not item for item in items
        ):
            raise QualificationMetricInvariantError(f"Qualification envelope {field} is invalid.")
        normalized = sorted(set(items))
        if len(normalized) != len(items):
            raise QualificationMetricInvariantError(
                f"Qualification envelope {field} has duplicates."
            )
        if field in {"issue_classes", "operation_forms"} and not normalized:
            raise QualificationMetricInvariantError(
                f"Qualification envelope {field} must be nonempty."
            )
        result[field] = normalized
    return result


def bootstrap_problem_sample(
    input_digest: str, problem_ids: list[str], replicate: int
) -> list[str]:
    clusters = sorted(set(problem_ids))
    if not clusters or len(clusters) != len(problem_ids):
        raise QualificationMetricInvariantError(
            "Bootstrap problem IDs must be nonempty and unique."
        )
    return [
        clusters[bootstrap_cluster_index(input_digest, len(clusters), replicate, position)]
        for position in range(len(clusters))
    ]


def bootstrap_cluster_index(
    input_digest: str, cluster_count: int, replicate: int, position: int
) -> int:
    digest_bytes = _raw_sha256_digest(input_digest)
    if cluster_count <= 0:
        raise QualificationMetricInvariantError("Bootstrap cluster_count must be positive.")
    if not 0 <= replicate < 2**64 or not 0 <= position < 2**64:
        raise QualificationMetricInvariantError(
            "Bootstrap counters must fit unsigned 64-bit integers."
        )
    limit = 2**256 - (2**256 % cluster_count)
    retry = 0
    while True:
        value = _counter_value(digest_bytes, replicate, position, retry)
        if value < limit:
            return value % cluster_count
        retry += 1


def _counter_value(digest_bytes: bytes, replicate: int, position: int, retry: int) -> int:
    block = (
        BOOTSTRAP_DOMAIN
        + digest_bytes
        + replicate.to_bytes(8, "big")
        + position.to_bytes(8, "big")
        + retry.to_bytes(8, "big")
    )
    return int.from_bytes(hashlib.sha256(block).digest(), "big")


def _raw_sha256_digest(value: str) -> bytes:
    if not value.startswith("sha256:"):
        raise QualificationMetricInvariantError("Bootstrap input digest must use sha256.")
    try:
        result = bytes.fromhex(value.removeprefix("sha256:"))
    except ValueError as error:
        raise QualificationMetricInvariantError(
            "Bootstrap input digest is not hexadecimal."
        ) from error
    if len(result) != 32:
        raise QualificationMetricInvariantError(
            "Bootstrap input digest must contain exactly 32 bytes."
        )
    return result


def _validate_outcome_projection(outcome: dict[str, Any]) -> None:
    try:
        fixture_kind = str(outcome.get("fixture_kind", ""))
        expected_family = _PROOF_FAMILY_BY_FIXTURE_KIND.get(fixture_kind)
        if expected_family is None or outcome.get("qualification_proof_family") != expected_family:
            raise QualificationMetricInvariantError(
                "Detector case outcome proof family conflicts with its fixture kind."
            )
        static_ref = outcome.get("static_qualification_proof_ref")
        if expected_family == "static_closed_scope":
            if (
                not isinstance(static_ref, Mapping)
                or static_ref.get("record_type") != "static_qualification_proof"
                or not isinstance(static_ref.get("record_id"), str)
            ):
                raise QualificationMetricInvariantError(
                    "A static case outcome lacks its exact static proof reference."
                )
        elif static_ref is not None:
            raise QualificationMetricInvariantError(
                "A non-static case outcome cannot cite a static qualification proof."
            )
        status = outcome.get("metric_input_status")
        projections = outcome.get("detector_result_outcomes")
        if not isinstance(projections, list):
            raise QualificationMetricInvariantError("Detector result projections are unavailable.")
        if status == "legacy_source_projection_unavailable":
            if projections or outcome.get("metric_eligible") is not False:
                raise QualificationMetricInvariantError(
                    "A legacy-incomplete outcome is not fail-closed."
                )
            return
        if status != "complete" or not projections:
            raise QualificationMetricInvariantError(
                "A complete outcome requires exact result projections."
            )
        expected_metric_eligible = outcome.get("comparison_status") == "reconciled"
        if outcome.get("metric_eligible") is not expected_metric_eligible:
            raise QualificationMetricInvariantError(
                "Case metric eligibility conflicts with comparison status."
            )

        projection_ids = [str(item["detector_result_ref"]["record_id"]) for item in projections]
        if projection_ids != sorted(projection_ids) or len(set(projection_ids)) != len(
            projection_ids
        ):
            raise QualificationMetricInvariantError(
                "DetectorResult projections are not unique and ordered."
            )
        projected_candidate_ids: list[str] = []
        for projection in projections:
            refs = projection["evaluation_candidate_refs"]
            ids = [str(ref["record_id"]) for ref in refs]
            if ids != sorted(ids) or len(set(ids)) != len(ids):
                raise QualificationMetricInvariantError(
                    "Projected evaluation-candidate refs are not ordered."
                )
            if projection["state"] == "evaluation_finding_candidate" and not ids:
                raise QualificationMetricInvariantError(
                    "An evaluation_finding_candidate result lacks its evaluation candidate."
                )
            projected_candidate_ids.extend(ids)
        if len(set(projected_candidate_ids)) != len(projected_candidate_ids):
            raise QualificationMetricInvariantError(
                "An evaluation candidate cites multiple result projections."
            )

        candidate_ids = [str(ref["record_id"]) for ref in outcome["candidate_refs"]]
        candidate_outcome_ids = [
            str(item["candidate_ref"]["record_id"]) for item in outcome["candidate_outcomes"]
        ]
        if (
            sorted(projected_candidate_ids) != sorted(candidate_ids)
            or sorted(candidate_outcome_ids) != sorted(candidate_ids)
            or len(set(candidate_outcome_ids)) != len(candidate_outcome_ids)
        ):
            raise QualificationMetricInvariantError(
                "Candidate refs, outcomes, and exact result projections do not agree."
            )
        root_ids = [str(ref["record_id"]) for ref in outcome["root_cause_refs"]]
        root_outcome_ids = [
            str(item["root_cause_ref"]["record_id"]) for item in outcome["root_outcomes"]
        ]
        if sorted(root_ids) != sorted(root_outcome_ids) or len(set(root_outcome_ids)) != len(
            root_outcome_ids
        ):
            raise QualificationMetricInvariantError(
                "Root refs and reconciled root outcomes do not agree."
            )
    except (KeyError, TypeError) as error:
        raise QualificationMetricInvariantError(
            "Detector case outcome projection is malformed."
        ) from error


def _render_metrics(
    pairs: Mapping[str, tuple[int, int]],
    intervals: Mapping[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "metric_name": name,
            "numerator": pairs[name][0],
            "denominator": pairs[name][1],
            "estimate": (
                None if pairs[name][1] == 0 else float(Fraction(pairs[name][0], pairs[name][1]))
            ),
            "interval": intervals[name],
        }
        for name in METRIC_NAMES
    ]


def _eligible(outcome: Mapping[str, Any]) -> bool:
    return (
        outcome.get("metric_input_status") == "complete"
        and outcome.get("comparison_status") == "reconciled"
        and outcome.get("metric_eligible") is True
    )


def _complete(outcome: Mapping[str, Any]) -> bool:
    return outcome.get("metric_input_status") == "complete"


def _candidate_id(value: Mapping[str, Any]) -> str:
    return str(value["candidate_ref"]["record_id"])


def _metric_pairs(outcomes: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    eligible = [outcome for outcome in outcomes if _eligible(outcome)]
    complete = [outcome for outcome in outcomes if _complete(outcome)]
    resolved_candidates = [
        candidate
        for outcome in eligible
        for candidate in outcome["candidate_outcomes"]
        if candidate["status"] in _RESOLVED_CANDIDATE_STATES
    ]
    resolved_roots = [
        root
        for outcome in eligible
        for root in outcome["root_outcomes"]
        if root["status"] in _RESOLVED_ROOT_STATES
    ]

    unsafe_workflows = 0
    completed_opportunities = 0
    unsafe_completed_opportunities = 0
    applicable_covered_opportunities = 0
    unsafe_applicable_covered_opportunities = 0
    for outcome in eligible:
        unsafe_candidate_ids = {
            _candidate_id(candidate)
            for candidate in outcome["candidate_outcomes"]
            if candidate["status"] in _UNSAFE_CANDIDATE_STATES
        }
        if unsafe_candidate_ids:
            unsafe_workflows += 1
        for projection in outcome["detector_result_outcomes"]:
            projected_ids = {
                str(ref["record_id"]) for ref in projection["evaluation_candidate_refs"]
            }
            unsafe = bool(projected_ids & unsafe_candidate_ids)
            if projection["execution_class"] == "completed":
                completed_opportunities += 1
                unsafe_completed_opportunities += int(unsafe)
                if (
                    projection["applicability_status"] == "applicable"
                    and projection["coverage_status"] == "covered"
                ):
                    applicable_covered_opportunities += 1
                    unsafe_applicable_covered_opportunities += int(unsafe)

    diagnostic_opportunities = [
        projection for outcome in complete for projection in outcome["detector_result_outcomes"]
    ]
    bounded_candidates = sum(
        candidate["status"] == "bounded_root_match" for candidate in resolved_candidates
    )
    false_candidates = sum(
        candidate["status"] == "false_root_localization" for candidate in resolved_candidates
    )
    overstated_candidates = sum(
        candidate["status"] == "overstated_root_match" for candidate in resolved_candidates
    )
    bounded_roots = sum(root["status"] == "boundedly_localized" for root in resolved_roots)
    overstated_roots = sum(root["status"] == "localized_but_overstated" for root in resolved_roots)
    return {
        "workflow_unsafe_candidate_probability": (unsafe_workflows, len(eligible)),
        "completed_opportunity_false_positive_rate": (
            unsafe_completed_opportunities,
            completed_opportunities,
        ),
        "applicable_covered_opportunity_false_positive_rate": (
            unsafe_applicable_covered_opportunities,
            applicable_covered_opportunities,
        ),
        "finding_candidate_precision": (bounded_candidates, len(resolved_candidates)),
        "false_root_localization_rate": (false_candidates, len(resolved_candidates)),
        "overstatement_rate": (overstated_candidates, len(resolved_candidates)),
        "adjudicated_root_recall": (
            bounded_roots + overstated_roots,
            len(resolved_roots),
        ),
        "bounded_root_localization_accuracy": (
            bounded_roots,
            bounded_roots + overstated_roots,
        ),
        "abstention_rate": (
            sum(item["state"] in _ABSTENTION_STATES for item in diagnostic_opportunities),
            len(diagnostic_opportunities),
        ),
        "unsupported_rate": (
            sum(item["state"] == "unsupported_path" for item in diagnostic_opportunities),
            len(diagnostic_opportunities),
        ),
        "detector_error_rate": (
            sum(item["execution_class"] == "detector_error" for item in diagnostic_opportunities),
            len(diagnostic_opportunities),
        ),
        "unresolved_comparison_rate": (
            sum(outcome["comparison_status"] == "comparison_excluded" for outcome in complete),
            len(complete),
        ),
    }


def _public_counts(outcomes: list[dict[str, Any]]) -> dict[str, int]:
    eligible = [outcome for outcome in outcomes if _eligible(outcome)]
    complete = [outcome for outcome in outcomes if _complete(outcome)]
    opportunities = [
        projection for outcome in complete for projection in outcome["detector_result_outcomes"]
    ]
    candidates = [
        candidate
        for outcome in eligible
        for candidate in outcome["candidate_outcomes"]
        if candidate["status"] in _RESOLVED_CANDIDATE_STATES
    ]
    roots = [
        root
        for outcome in eligible
        for root in outcome["root_outcomes"]
        if root["status"] in _RESOLVED_ROOT_STATES
    ]
    return {
        "problem_clusters": len({str(outcome["problem_id"]) for outcome in outcomes}),
        "workflows": len(outcomes),
        "opportunities": len(opportunities),
        "applicable_covered_opportunities": sum(
            item["execution_class"] == "completed"
            and item["applicability_status"] == "applicable"
            and item["coverage_status"] == "covered"
            for item in opportunities
        ),
        "evaluation_candidates": len(candidates),
        "adjudicated_roots": len(roots),
        "bounded_root_matches": sum(item["status"] == "bounded_root_match" for item in candidates),
        "overstated_root_matches": sum(
            item["status"] == "overstated_root_match" for item in candidates
        ),
        "false_root_localizations": sum(
            item["status"] == "false_root_localization" for item in candidates
        ),
        "boundedly_localized_roots": sum(item["status"] == "boundedly_localized" for item in roots),
        "localized_but_overstated_roots": sum(
            item["status"] == "localized_but_overstated" for item in roots
        ),
        "missed_roots": sum(item["status"] == "missed" for item in roots),
        "abstentions": sum(item["state"] in _ABSTENTION_STATES for item in opportunities),
        "unsupported_opportunities": sum(
            item["state"] == "unsupported_path" for item in opportunities
        ),
        "detector_errors": sum(
            item["execution_class"] == "detector_error" for item in opportunities
        ),
        "unresolved_comparisons": sum(
            outcome["comparison_status"] == "comparison_excluded" for outcome in complete
        ),
    }


def _excluded_case_outcomes(outcomes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    excluded = []
    for outcome in outcomes:
        reason: str | None = None
        if outcome["metric_input_status"] != "complete":
            reason = "Legacy source DetectorResult projection is unavailable."
        elif outcome["comparison_status"] == "comparison_excluded":
            reason = " | ".join(str(value) for value in outcome["exclusion_reasons"])
        if reason is not None:
            excluded.append(
                {
                    "case_outcome_ref": _ref(
                        "detector_case_outcome", str(outcome["case_outcome_id"])
                    ),
                    "reason": reason,
                }
            )
    return excluded


def _bootstrap_intervals(
    outcomes: list[dict[str, Any]], problem_ids: list[str], input_digest: str
) -> dict[str, dict[str, Any]]:
    pairs_by_problem = {
        problem_id: _metric_pairs(
            [outcome for outcome in outcomes if str(outcome["problem_id"]) == problem_id]
        )
        for problem_id in problem_ids
    }
    estimates: dict[str, list[Fraction]] = {name: [] for name in METRIC_NAMES}
    invalid = {name: 0 for name in METRIC_NAMES}
    for replicate in range(BOOTSTRAP_REPLICATES):
        sampled = bootstrap_problem_sample(input_digest, problem_ids, replicate)
        aggregate = {name: [0, 0] for name in METRIC_NAMES}
        for problem_id in sampled:
            for name, (numerator, denominator) in pairs_by_problem[problem_id].items():
                aggregate[name][0] += numerator
                aggregate[name][1] += denominator
        for name, (numerator, denominator) in aggregate.items():
            if denominator == 0:
                invalid[name] += 1
            else:
                estimates[name].append(Fraction(numerator, denominator))

    result: dict[str, dict[str, Any]] = {}
    cluster_count = len(problem_ids)
    for name in METRIC_NAMES:
        values = sorted(estimates[name])
        limitations = []
        if cluster_count < 2:
            limitations.append(
                "At least two nonempty problem clusters are required for an interval."
            )
        if len(values) < 2:
            limitations.append(
                "At least two valid bootstrap replicates are required for an interval."
            )
        if cluster_count < 20:
            limitations.append(
                "Fewer than twenty problem clusters; percentile intervals may be unstable."
            )
        if cluster_count >= 2 and len(values) >= 2:
            lower_index = (len(values) + 39) // 40 - 1
            upper_index = (39 * len(values) + 39) // 40 - 1
            result[name] = {
                "status": "estimated",
                "confidence_level": 0.95,
                "lower": float(values[lower_index]),
                "upper": float(values[upper_index]),
                "valid_replicates": len(values),
                "invalid_replicates": invalid[name],
                "limitations": limitations,
            }
        else:
            result[name] = {
                "status": "not_estimable",
                "confidence_level": 0.95,
                "lower": None,
                "upper": None,
                "valid_replicates": len(values),
                "invalid_replicates": invalid[name],
                "limitations": limitations,
            }
    return result


def _ref(record_type: str, record_id: str) -> dict[str, str]:
    return {"record_type": record_type, "record_id": record_id}
