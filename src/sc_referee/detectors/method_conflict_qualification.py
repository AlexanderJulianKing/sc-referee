from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from math import isfinite
from typing import Any, Literal, cast

from sc_referee.core.ids import semantic_digest, stable_id
from sc_referee.scientific_checks.core import MethodConflictBinding


@dataclass(frozen=True)
class MethodConflictQualificationGrant:
    """One exact, replayable binding-level authority result.

    Constructing this value is intentionally possible only through the fail-closed resolver below.
    The package currently installs no instances and the production controller does not discover
    project-supplied qualification records.
    """

    qualification_id: str
    qualification_digest: str
    metric_set_id: str
    metric_set_digest: str
    threshold_policy_digest: str
    binding_id: str
    binding_digest: str
    detector_id: str
    detector_version: str
    detector_manifest_digest: str
    maturity: Literal["validated", "publication_grade"]


def resolve_method_conflict_qualification(
    *,
    binding: MethodConflictBinding,
    detector_manifest: Mapping[str, Any],
    qualification: Mapping[str, Any],
    metric_set: Mapping[str, Any],
) -> MethodConflictQualificationGrant | None:
    """Resolve one exact binding grant without trusting a boolean promotion flag alone."""

    detector_identity = (
        binding.detector_id,
        binding.detector_version,
        binding.detector_manifest_digest,
    )
    if detector_identity != (
        detector_manifest.get("detector_id"),
        detector_manifest.get("detector_version"),
        semantic_digest(detector_manifest),
    ):
        return None
    if detector_manifest.get("maturity") != "experimental":
        # The frozen candidate manifest is the qualified object. A separately published promoted
        # manifest is downstream of, not an input to, this decision.
        return None

    if qualification.get("record_type") != "detector_qualification":
        return None
    maturity = qualification.get("effective_maturity")
    if (
        qualification.get("outcome") != "promoted"
        or maturity not in {"validated", "publication_grade"}
        or qualification.get("requested_maturity") != maturity
        or (qualification.get("detector_id"), qualification.get("detector_version"))
        != detector_identity[:2]
        or not _complete_safety_gates(qualification.get("safety_gates"))
        or qualification.get("review_basis") not in {"agent_panel", "mixed_panel"}
        or not _nonempty_sequence(qualification.get("agent_adjudication_refs"))
        or not _nonempty_sequence(qualification.get("software_maintainer_approvals"))
        or not isinstance(qualification.get("qualification_report_ref"), str)
        or not qualification.get("qualification_report_ref")
        or "static_closed_scope"
        not in _string_set(qualification.get("qualification_proof_families"))
        or not isinstance(qualification.get("static_scope_disclosure"), Mapping)
    ):
        return None

    qualification_scope = qualification.get("binding_scope")
    if not _scope_matches_binding(qualification_scope, binding, detector_identity):
        return None
    threshold_policy = qualification.get("numeric_threshold_policy")
    if not _valid_threshold_policy(threshold_policy):
        return None
    threshold_mapping = cast(Mapping[str, Any], threshold_policy)

    metrics = qualification.get("quantitative_metrics")
    metric_refs = metrics.get("metric_set_refs") if isinstance(metrics, Mapping) else None
    if (
        not isinstance(metric_refs, Sequence)
        or isinstance(metric_refs, (str, bytes))
        or len(metric_refs) != 1
        or not isinstance(metric_refs[0], Mapping)
        or metric_refs[0].get("record_type") != "qualification_metric_set"
        or metric_refs[0].get("record_id") != metric_set.get("metric_set_id")
    ):
        return None

    if (
        metric_set.get("record_type") != "qualification_metric_set"
        or (
            metric_set.get("detector_id"),
            metric_set.get("detector_version"),
            metric_set.get("detector_manifest_digest"),
        )
        != detector_identity
        or metric_set.get("binding_scope") != qualification_scope
        or metric_set.get("numeric_threshold_policy") != threshold_policy
        or metric_set.get("promotion_evidence_eligible") is not True
        or metric_set.get("promotion_permitted") is not True
        or "public_development" in _string_set(metric_set.get("corpus_partitions"))
        or bool(metric_set.get("excluded_case_outcomes"))
        or not _thresholds_pass(metric_set, threshold_mapping)
    ):
        return None

    qualification_id = qualification.get("qualification_id")
    metric_set_id = metric_set.get("metric_set_id")
    policy_digest = threshold_mapping.get("policy_semantic_digest")
    if not all(
        isinstance(value, str) and value
        for value in (qualification_id, metric_set_id, policy_digest)
    ):
        return None
    return MethodConflictQualificationGrant(
        qualification_id=cast(str, qualification_id),
        qualification_digest=semantic_digest(qualification),
        metric_set_id=cast(str, metric_set_id),
        metric_set_digest=semantic_digest(metric_set),
        threshold_policy_digest=cast(str, policy_digest),
        binding_id=binding.binding_id,
        binding_digest=binding.binding_digest,
        detector_id=binding.detector_id,
        detector_version=binding.detector_version,
        detector_manifest_digest=binding.detector_manifest_digest,
        maturity=cast(Literal["validated", "publication_grade"], maturity),
    )


def project_qualified_method_conflict_candidate(
    result: Mapping[str, Any],
    binding: MethodConflictBinding,
    grant: MethodConflictQualificationGrant,
    *,
    work_packet: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Project a candidate only when replay inputs prove the result's exact binding."""

    extensions = result.get("extensions")
    if (
        result.get("record_type") != "detector_result"
        or result.get("state") != "evaluation_finding_candidate"
        or result.get("detector_maturity") != "experimental"
        or result.get("detector_id") != binding.detector_id
        or result.get("detector_version") != binding.detector_version
        or result.get("detector_manifest_digest") != binding.detector_manifest_digest
        or grant.binding_id != binding.binding_id
        or grant.binding_digest != binding.binding_digest
        or (
            grant.detector_id,
            grant.detector_version,
            grant.detector_manifest_digest,
        )
        != (
            binding.detector_id,
            binding.detector_version,
            binding.detector_manifest_digest,
        )
        or not isinstance(extensions, Mapping)
        or not isinstance(extensions.get("x-review-case-digest"), str)
        or not isinstance(result.get("candidate"), Mapping)
        or result["candidate"].get("assessment_type") != "finding"
        or not _work_packet_matches_binding(result, work_packet, binding)
    ):
        return None
    promoted = deepcopy(dict(result))
    promoted["state"] = "finding_candidate"
    promoted["detector_maturity"] = grant.maturity
    promoted_extensions = promoted["extensions"]
    assert isinstance(promoted_extensions, dict)
    promoted_extensions.update(
        {
            "x-evaluation-only": False,
            "x-production-finding-permitted": True,
            "x-method-conflict-binding-id": grant.binding_id,
            "x-method-conflict-binding-digest": grant.binding_digest,
            "x-detector-qualification-id": grant.qualification_id,
            "x-detector-qualification-digest": grant.qualification_digest,
            "x-qualification-metric-set-id": grant.metric_set_id,
            "x-qualification-metric-set-digest": grant.metric_set_digest,
            "x-threshold-policy-digest": grant.threshold_policy_digest,
        }
    )
    return promoted


def _work_packet_matches_binding(
    result: Mapping[str, Any],
    work_packet: Mapping[str, Any],
    binding: MethodConflictBinding,
) -> bool:
    """Bind a v0.3 result to the exact question-selected registry binding by replay identity."""

    question = work_packet.get("target_question")
    question_extensions = question.get("extensions") if isinstance(question, Mapping) else None
    question_id = question.get("question_id") if isinstance(question, Mapping) else None
    input_digest = semantic_digest(work_packet)
    return (
        work_packet.get("profile") == "bounded_analysis_method_conflict_work_packet_v1"
        and work_packet.get("audit_run_id") == result.get("audit_run_id")
        and work_packet.get("detector_id") == binding.detector_id
        and work_packet.get("detector_version") == binding.detector_version
        and work_packet.get("detector_manifest_digest") == binding.detector_manifest_digest
        and isinstance(question, Mapping)
        and question.get("record_type") == "material_question"
        and question.get("status") == "answered"
        and isinstance(question_id, str)
        and bool(question_id)
        and isinstance(question_extensions, Mapping)
        and question_extensions.get("x-scientific-check-id") == binding.check_id
        and result.get("deterministic_input_digest") == input_digest
        and result.get("result_id")
        == stable_id(
            "detector-result",
            binding.detector_id,
            binding.detector_version,
            question_id,
            input_digest,
        )
    )


def _scope_matches_binding(
    value: object,
    binding: MethodConflictBinding,
    detector_identity: tuple[str, str, str],
) -> bool:
    if not isinstance(value, Mapping):
        return False
    expected = {
        "scope_kind": "method_conflict_binding_v1",
        "binding_id": binding.binding_id,
        "production_binding_digest": binding.binding_digest,
        "check_id": binding.check_id,
        "check_version": binding.check_version,
        "check_manifest_digest": binding.check_manifest_digest,
        "detector_id": detector_identity[0],
        "detector_version": detector_identity[1],
        "detector_manifest_digest": detector_identity[2],
    }
    if any(value.get(key) != expected_value for key, expected_value in expected.items()):
        return False
    profile_ref = value.get("static_qualification_profile_ref")
    adapter = value.get("qualification_adapter")
    return (
        isinstance(profile_ref, Mapping)
        and profile_ref.get("record_type") == "static_qualification_profile"
        and isinstance(profile_ref.get("record_id"), str)
        and isinstance(value.get("static_qualification_profile_digest"), str)
        and isinstance(adapter, Mapping)
        and isinstance(adapter.get("adapter_id"), str)
        and isinstance(adapter.get("adapter_version"), str)
        and isinstance(adapter.get("implementation_digest"), str)
    )


def _valid_threshold_policy(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    supplied = value.get("policy_semantic_digest")
    if not isinstance(supplied, str):
        return False
    payload = {
        key: deepcopy(item) for key, item in value.items() if key != "policy_semantic_digest"
    }
    return (
        value.get("policy_kind") == "pilot_informed_binding_thresholds_v1"
        and value.get("held_out_labels_observed_before_freeze") is False
        and isinstance(value.get("policy_id"), str)
        and bool(value.get("policy_id"))
        and isinstance(value.get("policy_version"), str)
        and bool(value.get("policy_version"))
        and isinstance(value.get("decision_adr_ref"), str)
        and str(value.get("decision_adr_ref")).startswith("docs/implementation/ADR-")
        and isinstance(value.get("frozen_at"), str)
        and bool(value.get("frozen_at"))
        and _nonempty_string_sequence(value.get("pilot_evidence_refs"))
        and _nonempty_sequence(value.get("metric_requirements"))
        and supplied == semantic_digest(payload)
    )


def _thresholds_pass(metric_set: Mapping[str, Any], policy: Mapping[str, Any]) -> bool:
    counts = metric_set.get("counts")
    minimum = policy.get("minimum_counts")
    if not isinstance(counts, Mapping) or not isinstance(minimum, Mapping):
        return False
    control_strata = metric_set.get("control_family_strata")
    if not isinstance(control_strata, Sequence) or isinstance(control_strata, (str, bytes)):
        return False
    control_cases = sum(
        int(item.get("case_count", 0))
        for item in control_strata
        if isinstance(item, Mapping)
        and item.get("proof_family")
        in {"clean_execution", "documented_external_execution", "static_closed_scope"}
        and isinstance(item.get("case_count"), int)
    )
    count_values = {
        "workflows": counts.get("workflows"),
        "problem_clusters": counts.get("problem_clusters"),
        "adjudicated_roots": counts.get("adjudicated_roots"),
        "control_cases": control_cases,
    }
    if any(
        not isinstance(count_values[key], int)
        or isinstance(count_values[key], bool)
        or not isinstance(minimum.get(key), int)
        or isinstance(minimum.get(key), bool)
        or cast(int, minimum[key]) < 1
        or cast(int, count_values[key]) < cast(int, minimum[key])
        for key in count_values
    ):
        return False

    metrics = metric_set.get("metrics")
    if not isinstance(metrics, Sequence) or isinstance(metrics, (str, bytes)):
        return False
    by_name = {str(item.get("metric_name")): item for item in metrics if isinstance(item, Mapping)}
    require_intervals = policy.get("require_estimable_intervals") is True
    requirements = policy.get("metric_requirements")
    if not isinstance(requirements, Sequence) or isinstance(requirements, (str, bytes)):
        return False
    for requirement in requirements:
        if not isinstance(requirement, Mapping):
            return False
        metric = by_name.get(str(requirement.get("metric_name")))
        if metric is None:
            return False
        interval = metric.get("interval")
        if require_intervals and (
            not isinstance(interval, Mapping) or interval.get("status") != "estimated"
        ):
            return False
        statistic = requirement.get("statistic")
        if statistic == "estimate":
            observed = metric.get("estimate")
        elif statistic == "interval_lower":
            observed = interval.get("lower") if isinstance(interval, Mapping) else None
        elif statistic == "interval_upper":
            observed = interval.get("upper") if isinstance(interval, Mapping) else None
        else:
            return False
        threshold = requirement.get("threshold")
        if not isinstance(observed, (int, float)) or isinstance(observed, bool):
            return False
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
            return False
        if (
            not isfinite(float(observed))
            or not isfinite(float(threshold))
            or not 0 <= float(observed) <= 1
            or not 0 <= float(threshold) <= 1
        ):
            return False
        operator = requirement.get("operator")
        if (operator == "at_most" and observed > threshold) or (
            operator == "at_least" and observed < threshold
        ):
            return False
        if operator not in {"at_most", "at_least"}:
            return False
    return True


def _complete_safety_gates(value: object) -> bool:
    required = {
        "no_known_high_or_critical_false_accusations",
        "conditional_never_promoted",
        "verified_good_and_hard_negative_included",
        "decisive_counterevidence_included",
        "cluster_aware_uncertainty_reported",
        "public_development_cases_not_used_for_qualification",
        "regression_fixture_for_every_discovered_false_accusation",
        "unresolved_disagreement_excluded",
        "qualification_report_public",
        "proof_families_stratified",
    }
    return isinstance(value, Mapping) and all(value.get(key) is True for key in required)


def _nonempty_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and bool(value)


def _nonempty_string_sequence(value: object) -> bool:
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and bool(value)
        and all(isinstance(item, str) and item for item in value)
    )


def _string_set(value: object) -> set[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return set()
    return {item for item in value if isinstance(item, str)}
