"""Private Round-1 projection for the sealed complete-domain held-out ledger.

This module is evaluation-side only.  It does not install qualification authority.  The
projector accepts exactly the frozen v2.0.7 seven-case detector ledger, verifies its self-digest
and closed identities, and derives the ``detector_case_outcome`` inputs consumed by
``compile_qualification_evidence``.  The sealed runs were static audits: project-authored code
was not executed.  ADR-0071 records the maintainer's acceptance of their digest-locked,
lean-consolidated audit closures in place of a separate Stage-3 artifact.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from sc_referee.capability_matrix import default_capability_manifest_root
from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.detectors.method_conflict_grant_pins import (
    ExamAdapterIdentity,
    live_adapter_identity,
)
from sc_referee.qualification_metrics import compile_qualification_evidence
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.scientific_checks.core import MethodConflictBinding
from sc_referee.scientific_checks.profiles import scientific_check_release_registry


class CompleteDomainPromotionError(ValueError):
    """The frozen exam ledger or its deterministic projection is inconsistent."""


DETECTOR_ID = "detector:bounded-analysis-method-conflict"
DETECTOR_VERSION = "0.3.0"
DETECTOR_MANIFEST_DIGEST = "sha256:a8e8bdf16e847745276a3d8da0bc2ba44062e42293e1f3185c9ccf9a19abecbc"
ROUND2_DETECTOR_MANIFEST_DIGEST = (
    "sha256:a5b089be6a18b220f56fd345450912a3aa7ee3e132ff519117b879cee8e72c41"
)
CHECK_ID = "check:complete-domain-exposure-denominator"
CHECK_VERSION = "2.0.7"
BINDING_ID = "method-conflict-binding:complete-domain-exposure-denominator-v1"
BINDING_DIGEST = "sha256:f0b46686e0c5a4ff137cc43b4729fc6194e7aa550565bf4f9fe637f2480262ed"
ROUND2_BINDING_DIGEST = "sha256:0f59ece664acbc541006037fbfc8518c21e8fee9768ed47a651f6532226950f9"
CHECK_MANIFEST_DIGEST = "sha256:c3ef7acd8597c86e8a121ba43e94d4f2a2993c08cd2c14981b85b13c431841a9"
DETECTOR_TUPLE_DIGEST = "sha256:c0d6ec05c8e24e04e4382430e3bfa7fa4086bef016df218f28b907542f2ca3c3"
HELDOUT_LEDGER_DIGEST = "sha256:679cbc06c089ac8bccffbc89619bb4fdb67a722dcae0a47edcce205f87578048"
HELDOUT_OPENING_DIGEST = "sha256:0daf0982bc0e15bb8aada0c6e0be143bea0f439494858f7dc3ffd53f0a3d08ec"
SCIENTIFIC_LABEL_LEDGER_DIGEST = (
    "sha256:913c907ea9f39ecfb1291fb6c183e757180b32b4867f8632a9b91813fca50010"
)
AUTHORING_PROTOCOL_DIGEST = (
    "sha256:6554e88100ee986e8b5f6357ae9fe07d53723654c4aa415df1810ecc56d19c06"
)
ROUND1_QUALIFICATION_ADAPTER_IMPLEMENTATION_DIGEST = (
    "sha256:b6f91c351002d689ef76a66e507f57c66b25bb485d890bc2ac1882b1e61713aa"
)
ROUND2_EXAM_ADAPTER_IDENTITY = (
    ExamAdapterIdentity(
        adapter_id="adapter:complete-domain-exposure-denominator:quantity-consistency-v1",
        adapter_version="2.0.7",
        implementation_digest=(
            "sha256:cb6de94e39efdf726cc516178b77b85443044415b72c8671025ef9c2e6eef05c"
        ),
        manifest_digest=("sha256:231046e541e1e84671b7fe716a2454c67d2d931f1cfe432e7de80512987d3a20"),
        recognition_grammar_digest=(
            "sha256:c757692071a6925a5ca5e409dc0ad79f7421fcdbc93fb15c14efb30050524362"
        ),
    ),
)
QUALIFICATION_ENVELOPE = {
    "issue_classes": ["x-review-scoped-analysis-method-requirement-mismatch"],
    "languages": ["markdown", "python"],
    "packages": [],
    "operation_forms": [
        "closed_method_comparison_algebra_v1",
        "exact_selected_output_writer_scope_v1",
    ],
}
_EXPECTED_CASE_ROLES = {
    "case:0e8a84e424013c876694": "unsupported",
    "case:670f4b5b1a48188a8973": "error_bearing",
    "case:6a3c7be6adbfa11a7168": "renamed_implementation",
    "case:6d9579fa1e8f9f50db4c": "corrected_twin",
    "case:79bba09d589444884c44": "ambiguous",
    "case:87f491b5c0fa3ae7be4a": "valid_alternative",
    "case:cdc9e2ae44b02c1a85d2": "hard_negative",
}
_POSITIVE_ROLES = {"error_bearing", "renamed_implementation"}
_STATIC_VERIFIED_GOOD_ROLES = {"corrected_twin", "valid_alternative"}
_EXPECTED_LABELS = {
    "unsupported": "unsupported_control",
    "error_bearing": "positive_demonstrated",
    "renamed_implementation": "positive_demonstrated",
    "corrected_twin": "verified_good_eligible",
    "ambiguous": "ambiguous_control",
    "valid_alternative": "verified_good_eligible",
    "hard_negative": "verified_good_eligible",
}
_EXPECTED_TOP_LEVEL = {
    "envelope_id": "complete-domain-exposure-denominator-v2.0.7-heldout",
    "check_id": CHECK_ID,
    "check_version": CHECK_VERSION,
    "detector_id": DETECTOR_ID,
    "detector_tuple_digest": DETECTOR_TUPLE_DIGEST,
    "scientific_label_ledger_digest": SCIENTIFIC_LABEL_LEDGER_DIGEST,
    "authoring_protocol_digest": AUTHORING_PROTOCOL_DIGEST,
    "labels_frozen_before_detector_observation": True,
    "deterministic_replay_verified": True,
    "project_code_executed": False,
    "production_finding_count": 0,
}
_SENSITIVITY_BAR = re.compile(
    r"at_least_(?P<numerator>one|two)_of_(?P<denominator>one|two)_positives\Z"
)
_COUNT_WORDS = {"one": 1, "two": 2}


def project_heldout_detector_case_outcomes(path: Path) -> list[dict[str, Any]]:
    """Project the one accepted ledger, refusing byte, identity, or outcome drift."""

    if path.is_symlink() or not path.is_file():
        raise CompleteDomainPromotionError("Held-out detector ledger must be one regular file.")
    payload = path.read_bytes()
    try:
        ledger = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CompleteDomainPromotionError(
            "Held-out detector ledger is not strict UTF-8 JSON."
        ) from error
    if not isinstance(ledger, dict):
        raise CompleteDomainPromotionError("Held-out detector ledger must be one JSON object.")
    supplied_digest = ledger.get("ledger_digest")
    digest_payload = {key: value for key, value in ledger.items() if key != "ledger_digest"}
    computed_digest = semantic_digest(digest_payload)
    if supplied_digest != HELDOUT_LEDGER_DIGEST or computed_digest != HELDOUT_LEDGER_DIGEST:
        raise CompleteDomainPromotionError(
            "Held-out detector ledger digest does not match the seal."
        )
    for key, expected in _EXPECTED_TOP_LEVEL.items():
        if ledger.get(key) != expected:
            raise CompleteDomainPromotionError(f"Held-out detector ledger {key} drifted.")
    entries = ledger.get("entries")
    if not isinstance(entries, list) or len(entries) != len(_EXPECTED_CASE_ROLES):
        raise CompleteDomainPromotionError("Held-out detector ledger must contain seven entries.")
    by_case: dict[str, Mapping[str, Any]] = {}
    for item in entries:
        if not isinstance(item, Mapping):
            raise CompleteDomainPromotionError("Held-out detector ledger entry is malformed.")
        case_id = item.get("case_id")
        if not isinstance(case_id, str) or case_id in by_case:
            raise CompleteDomainPromotionError(
                "Held-out case identities are missing or duplicated."
            )
        by_case[case_id] = item
    if set(by_case) != set(_EXPECTED_CASE_ROLES):
        raise CompleteDomainPromotionError("Held-out case identities do not equal the sealed set.")
    return [
        _project_entry(by_case[case_id], case_id, _EXPECTED_CASE_ROLES[case_id])
        for case_id in sorted(by_case)
    ]


def qualification_profile_descriptor() -> dict[str, Any]:
    """Describe the private lean-consolidated static scope bound by ADR-0071."""

    return {
        "record_type": "static_qualification_profile",
        "record_id": (
            "static-qualification-profile:complete-domain-exposure-denominator-v207-"
            "lean-consolidated"
        ),
        "detector_tuple_digest": DETECTOR_TUPLE_DIGEST,
        "authoring_protocol_digest": AUTHORING_PROTOCOL_DIGEST,
        "scientific_label_ledger_digest": SCIENTIFIC_LABEL_LEDGER_DIGEST,
        "detector_run_ledger_digest": HELDOUT_LEDGER_DIGEST,
        "stage3_comparison_artifact": "absent_maintainer_accepted_lean_substitute_adr_0071",
    }


def numeric_threshold_policy(opening_path: Path) -> dict[str, Any]:
    """Translate the digest-bound pre-label ADR-0070 bar into fixed metric vocabulary."""

    sensitivity_threshold, positive_count = _frozen_sensitivity_requirement(opening_path)

    value: dict[str, Any] = {
        "policy_kind": "pilot_informed_binding_thresholds_v1",
        "policy_id": "threshold-policy:complete-domain-exposure-denominator-v207-heldout",
        "policy_version": "1.0.0",
        "decision_adr_ref": (
            "docs/implementation/ADR-0070-HELDOUT-THRESHOLD-COMPLETE-DOMAIN-ENVELOPE.md"
        ),
        "pilot_evidence_refs": [
            "docs/implementation/ADR-0070-HELDOUT-THRESHOLD-COMPLETE-DOMAIN-ENVELOPE.md",
            (
                "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-"
                "direct-lane-v2/pilot-v206m-lean-pipeline-three-case/detector-run/"
                "DETECTOR_RUN_LEDGER.json"
            ),
        ],
        "frozen_at": "2026-08-08T07:17:48.997584Z",
        "held_out_labels_observed_before_freeze": False,
        "minimum_counts": {
            "workflows": 7,
            "problem_clusters": 7,
            "adjudicated_roots": positive_count,
            "control_cases": 5,
        },
        "require_estimable_intervals": False,
        "metric_requirements": [
            {
                "metric_name": "completed_opportunity_false_positive_rate",
                "statistic": "estimate",
                "operator": "at_most",
                "threshold": 0.0,
            },
            {
                "metric_name": "adjudicated_root_recall",
                "statistic": "estimate",
                "operator": "at_least",
                "threshold": sensitivity_threshold,
            },
        ],
    }
    value["policy_semantic_digest"] = semantic_digest(value)
    return value


def build_round1_records(
    ledger_path: Path, *, recorded_at: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the private metric-set/qualification pair without installing either record."""

    outcomes = project_heldout_detector_case_outcomes(ledger_path)
    policy = numeric_threshold_policy(ledger_path.parent.parent / "HELDOUT_OPENING.json")
    evidence = compile_qualification_evidence(outcomes, QUALIFICATION_ENVELOPE)
    profile = qualification_profile_descriptor()
    scope = {
        "scope_kind": "method_conflict_binding_v1",
        "binding_id": BINDING_ID,
        "production_binding_digest": BINDING_DIGEST,
        "check_id": CHECK_ID,
        "check_version": CHECK_VERSION,
        "check_manifest_digest": CHECK_MANIFEST_DIGEST,
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
        "detector_manifest_digest": DETECTOR_MANIFEST_DIGEST,
        "static_qualification_profile_ref": {
            "record_type": "static_qualification_profile",
            "record_id": profile["record_id"],
        },
        "static_qualification_profile_digest": semantic_digest(profile),
        "qualification_adapter": {
            "adapter_id": "qualification-adapter:heldout-ledger-case-outcome-v1",
            "adapter_version": "1.0.0",
            "implementation_digest": ROUND1_QUALIFICATION_ADAPTER_IMPLEMENTATION_DIGEST,
        },
    }
    metric_set: dict[str, Any] = {
        "schema_version": "0.19.0-round1-private",
        "record_type": "qualification_metric_set",
        **evidence,
        "binding_scope": scope,
        "metric_profile": "root-cause-clustered-metrics-v1",
        "numeric_threshold_policy": policy,
        "promotion_permitted": True,
        "generated_at": recorded_at,
        "non_inferences": [
            "Round 1 installs no production grant and changes no controller authority.",
            "Point estimates from seven cases are not a correctness certificate.",
            "The grant applies only to the exam-time digest pins recorded by ADR-0071.",
        ],
        "provenance": _provenance(recorded_at, "deterministic_heldout_ledger_projection"),
    }
    qualification_id = "qualification:complete-domain-exposure-denominator-v207-round1"
    qualification: dict[str, Any] = {
        "schema_version": "0.19.0-round1-private",
        "record_type": "detector_qualification",
        "qualification_id": qualification_id,
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
        "outcome": "promoted",
        "requested_maturity": "validated",
        "effective_maturity": "validated",
        "binding_scope": scope,
        "numeric_threshold_policy": policy,
        "qualification_proof_families": ["positive_issue", "static_closed_scope"],
        "quantitative_metrics": {
            "metric_profile": "root-cause-clustered-metrics-v1",
            "metric_set_refs": [
                {
                    "record_type": "qualification_metric_set",
                    "record_id": metric_set["metric_set_id"],
                }
            ],
        },
        "review_basis": "agent_panel",
        "agent_adjudication_refs": [
            (
                "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-"
                "direct-lane-v2/heldout-v207-seven-case/review/REVIEW_LEDGER.json"
            ),
            (
                "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-"
                "direct-lane-v2/heldout-v207-seven-case/SCIENTIFIC_LABEL_LEDGER.json"
            ),
        ],
        "software_maintainer_approvals": [
            {
                "actor_kind": "human",
                "actor_id": "person:alex",
                "display_name": "Alex",
                "approved_on": "2026-08-10",
                "decision_ref": (
                    "docs/implementation/ADR-0071-COMPLETE-DOMAIN-ENVELOPE-PROMOTION.md"
                ),
            }
        ],
        "qualification_report_ref": (
            "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-"
            "lane-v2/QUALIFICATION_REPORT.md"
        ),
        "safety_gates": {
            "no_known_high_or_critical_false_accusations": True,
            "conditional_never_promoted": True,
            "verified_good_and_hard_negative_included": True,
            "decisive_counterevidence_included": True,
            "cluster_aware_uncertainty_reported": True,
            "public_development_cases_not_used_for_qualification": True,
            "regression_fixture_for_every_discovered_false_accusation": True,
            "unresolved_disagreement_excluded": True,
            "qualification_report_public": True,
            "proof_families_stratified": True,
        },
        "static_scope_disclosure": {
            "profile_refs": [scope["static_qualification_profile_ref"]],
            "scope_statement": (
                "Seven digest-locked static audit closures; project-authored code was not "
                "executed. ADR-0071 accepts the lean-consolidated evidence because no separate "
                "Stage-3 comparison artifact exists."
            ),
            "stage3_comparison_artifact_exists": False,
            "execution_claimed": False,
            "global_correctness_claimed": False,
        },
        "qualification_basis_disclosure": (
            "One-shot 7/7 held-out exam: zero candidates on five controls and two bounded "
            "candidates on two demonstrated errors. Round 1 records but does not install the grant."
        ),
        "decided_at": recorded_at,
        "provenance": _provenance(recorded_at, "maintainer_promotion_recording"),
    }
    return metric_set, qualification


def build_round2_records(
    ledger_path: Path,
    authoring_protocol_path: Path,
    *,
    recorded_at: str,
    schema_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Re-derive the sealed evidence in public v0.19 shape at ruled current pins."""

    binding, detector_manifest = _round2_live_identity()
    outcomes = deepcopy(project_heldout_detector_case_outcomes(ledger_path))
    for outcome in outcomes:
        outcome["schema_version"] = "0.19.0"
        outcome["detector_manifest_digest"] = binding.detector_manifest_digest
    policy = numeric_threshold_policy(ledger_path.parent.parent / "HELDOUT_OPENING.json")
    evidence = compile_qualification_evidence(outcomes, QUALIFICATION_ENVELOPE)
    profile = qualification_profile_descriptor()
    scope = _round2_scope(binding, profile)
    metric_set: dict[str, Any] = {
        "schema_version": "0.19.0",
        "record_type": "qualification_metric_set",
        **evidence,
        "binding_scope": scope,
        "metric_profile": "root-cause-clustered-metrics-v1",
        "numeric_threshold_policy": policy,
        "promotion_permitted": True,
        "generated_at": recorded_at,
        "non_inferences": [
            "Round 2 installs no production grant and changes no controller authority.",
            "Point estimates from seven cases are not a correctness certificate.",
            "Any future grant applies only to the current digest pins ruled by ADR-0074.",
        ],
        "provenance": _provenance(recorded_at, "deterministic_round2_current_pin_rederivation"),
    }
    qualification: dict[str, Any] = {
        "schema_version": "0.19.0",
        "record_type": "detector_qualification",
        "qualification_id": "qualification:complete-domain-exposure-denominator-v207-round2",
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
        "outcome": "promoted",
        "requested_maturity": "validated",
        "effective_maturity": "validated",
        "binding_scope": scope,
        "numeric_threshold_policy": policy,
        "qualification_proof_families": ["static_closed_scope"],
        "quantitative_metrics": {
            "metric_profile": "root-cause-clustered-metrics-v1",
            "metric_set_refs": [
                {
                    "record_type": "qualification_metric_set",
                    "record_id": metric_set["metric_set_id"],
                }
            ],
        },
        "review_basis": "agent_panel",
        "agent_adjudication_refs": [],
        "evaluation_refs": [
            (
                "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-"
                "direct-lane-v2/heldout-v207-seven-case/review/REVIEW_LEDGER.json"
            ),
            (
                "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-"
                "direct-lane-v2/heldout-v207-seven-case/SCIENTIFIC_LABEL_LEDGER.json"
            ),
        ],
        "author_actor_ids": _round2_author_actor_ids(authoring_protocol_path),
        "human_scientific_approvals": [],
        "software_maintainer_approvals": [
            {
                "actor": {
                    "actor_kind": "human",
                    "actor_id": "person:alex",
                    "display_name": "Alex",
                },
                "approved_on": "2026-08-10",
                "decision_ref": (
                    "docs/implementation/ADR-0071-COMPLETE-DOMAIN-ENVELOPE-PROMOTION.md"
                ),
            }
        ],
        "qualification_report_ref": (
            "evaluation/qualification/complete-domain-exposure-denominator-v1.1.0-direct-"
            "lane-v2/QUALIFICATION_REPORT.md"
        ),
        "safety_gates": _round2_safety_gates(),
        "static_scope_disclosure": {
            "profile_refs": [scope["static_qualification_profile_ref"]],
            "scope_statement": (
                "Seven digest-locked static audit closures; project-authored code was not "
                "executed. ADR-0071 accepts the lean-consolidated evidence without a separate "
                "Stage-3 comparison artifact, and ADR-0074 rules the non-blind seven-case replay "
                "at the current adapter identity into the exact qualification scope."
            ),
            "stage3_comparison_artifact_exists": False,
            "execution_claimed": False,
            "global_correctness_claimed": False,
        },
        "qualification_basis_disclosure": (
            "The same one-shot 7/7 held-out evidence is re-derived in v0.19 shape at the "
            "ADR-0074-ruled current adapter and live binding pins. This record does not install "
            "a grant."
        ),
        "decided_at": recorded_at,
        "provenance": _provenance(recorded_at, "maintainer_round2_rederivation_recording"),
    }
    registry = LocalSchemaRegistry(schema_root)
    registry.validate(metric_set)
    registry.validate(qualification)
    if semantic_digest(detector_manifest) != binding.detector_manifest_digest:
        raise CompleteDomainPromotionError("Live detector manifest changed during re-derivation.")
    return metric_set, qualification


def _round2_live_identity() -> tuple[MethodConflictBinding, dict[str, Any]]:
    bindings = [
        item
        for item in scientific_check_release_registry().method_conflict_bindings
        if item.binding_id == BINDING_ID
    ]
    if len(bindings) != 1:
        raise CompleteDomainPromotionError("Round-2 binding is absent or duplicated.")
    binding = bindings[0]
    if (
        binding.binding_digest != ROUND2_BINDING_DIGEST
        or binding.check_id != CHECK_ID
        or binding.check_version != CHECK_VERSION
        or binding.check_manifest_digest != CHECK_MANIFEST_DIGEST
        or binding.detector_id != DETECTOR_ID
        or binding.detector_version != DETECTOR_VERSION
        or binding.detector_manifest_digest != ROUND2_DETECTOR_MANIFEST_DIGEST
        or live_adapter_identity(binding) != ROUND2_EXAM_ADAPTER_IDENTITY
    ):
        raise CompleteDomainPromotionError("Live Round-2 identity is not the ADR-0074-ruled tuple.")
    collection_path = default_capability_manifest_root() / "detector-manifests.json"
    try:
        collection = json.loads(collection_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CompleteDomainPromotionError(
            "Live detector manifest collection is unreadable."
        ) from error
    records = collection.get("records") if isinstance(collection, Mapping) else None
    matches = (
        [
            dict(item)
            for item in records
            if isinstance(item, Mapping)
            and item.get("detector_id") == DETECTOR_ID
            and item.get("detector_version") == DETECTOR_VERSION
        ]
        if isinstance(records, list)
        else []
    )
    if (
        len(matches) != 1
        or semantic_digest(matches[0]) != ROUND2_DETECTOR_MANIFEST_DIGEST
        or matches[0].get("maturity") != "experimental"
    ):
        raise CompleteDomainPromotionError("Live Round-2 detector manifest is not exact.")
    return binding, matches[0]


def _round2_scope(binding: MethodConflictBinding, profile: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "scope_kind": "method_conflict_binding_v1",
        "binding_id": binding.binding_id,
        "production_binding_digest": binding.binding_digest,
        "check_id": binding.check_id,
        "check_version": binding.check_version,
        "check_manifest_digest": binding.check_manifest_digest,
        "detector_id": binding.detector_id,
        "detector_version": binding.detector_version,
        "detector_manifest_digest": binding.detector_manifest_digest,
        "static_qualification_profile_ref": {
            "record_type": "static_qualification_profile",
            "record_id": profile["record_id"],
        },
        "static_qualification_profile_digest": semantic_digest(profile),
        "qualification_adapter": {
            "adapter_id": "qualification-adapter:heldout-ledger-case-outcome-v1",
            "adapter_version": "2.0.0",
            "implementation_digest": sha256_digest(Path(__file__).read_bytes()),
        },
    }


def _round2_author_actor_ids(path: Path) -> list[str]:
    if path.is_symlink() or not path.is_file():
        raise CompleteDomainPromotionError("Authoring protocol must be one regular file.")
    try:
        protocol = json.loads(path.read_bytes().decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CompleteDomainPromotionError(
            "Authoring protocol is not strict UTF-8 JSON."
        ) from error
    if not isinstance(protocol, Mapping):
        raise CompleteDomainPromotionError("Authoring protocol must be one JSON object.")
    supplied = protocol.get("protocol_digest")
    basis = {key: value for key, value in protocol.items() if key != "protocol_digest"}
    if supplied != AUTHORING_PROTOCOL_DIGEST or semantic_digest(basis) != AUTHORING_PROTOCOL_DIGEST:
        raise CompleteDomainPromotionError("Authoring protocol digest does not match the seal.")
    assignments = protocol.get("author_assignments")
    if not isinstance(assignments, Sequence) or isinstance(assignments, (str, bytes)):
        raise CompleteDomainPromotionError("Authoring protocol assignments are malformed.")
    actors: set[str] = set()
    assigned_cases: set[str] = set()
    for assignment in assignments:
        participant = assignment.get("participant") if isinstance(assignment, Mapping) else None
        actor_id = participant.get("participant_id") if isinstance(participant, Mapping) else None
        case_ids = assignment.get("case_ids") if isinstance(assignment, Mapping) else None
        if (
            not isinstance(actor_id, str)
            or not actor_id.startswith("actor:")
            or not isinstance(case_ids, Sequence)
            or isinstance(case_ids, (str, bytes))
            or not case_ids
            or not all(isinstance(case_id, str) for case_id in case_ids)
            or assigned_cases.intersection(case_ids)
        ):
            raise CompleteDomainPromotionError("Authoring protocol assignment identity is invalid.")
        actors.add(actor_id)
        assigned_cases.update(case_ids)
    if assigned_cases != set(_EXPECTED_CASE_ROLES) or not actors:
        raise CompleteDomainPromotionError("Author assignments do not cover the sealed cases once.")
    return sorted(actors)


def _round2_safety_gates() -> dict[str, bool]:
    return {
        "no_known_high_or_critical_false_accusations": True,
        "conditional_never_promoted": True,
        "verified_good_and_hard_negative_included": True,
        "decisive_counterevidence_included": True,
        "cluster_aware_uncertainty_reported": True,
        "public_development_cases_not_used_for_qualification": True,
        "regression_fixture_for_every_discovered_false_accusation": True,
        "unresolved_disagreement_excluded": True,
        "qualification_report_public": True,
        "proof_families_stratified": True,
    }


def _project_entry(entry: Mapping[str, Any], case_id: str, expected_role: str) -> dict[str, Any]:
    if entry.get("case_role") != expected_role:
        raise CompleteDomainPromotionError(f"Held-out role drifted for {case_id}.")
    positive = expected_role in _POSITIVE_ROLES
    expected_comparison = "true_positive" if positive else "true_negative"
    if (
        entry.get("comparison_outcome") != expected_comparison
        or entry.get("detector_positive") is not positive
        or entry.get("finding_candidate_count") != int(positive)
        or entry.get("frozen_label_status") != _EXPECTED_LABELS[expected_role]
        or entry.get("production_findings") != 0
        or entry.get("project_code_executions") != 0
        or entry.get("replay_equal") is not True
    ):
        raise CompleteDomainPromotionError(f"Held-out outcome is inconsistent for {case_id}.")
    audit_lock_digest = entry.get("audit_lock_digest")
    if not isinstance(audit_lock_digest, str) or not _is_sha256(audit_lock_digest):
        raise CompleteDomainPromotionError(f"Held-out audit lock is malformed for {case_id}.")
    entry_digest = semantic_digest(dict(entry))
    result_id = stable_id("detector-result-projection", HELDOUT_LEDGER_DIGEST, case_id)
    candidate_id = stable_id("detector-evaluation-candidate", HELDOUT_LEDGER_DIGEST, case_id)
    root_id = stable_id("adjudicated-root-cause", SCIENTIFIC_LABEL_LEDGER_DIGEST, case_id)
    candidate_ref = {"record_type": "detector_evaluation_candidate", "record_id": candidate_id}
    root_ref = {"record_type": "adjudicated_root_cause", "record_id": root_id}
    if expected_role == "unsupported":
        state, applicability, coverage = "unsupported_path", "uncertain", "not_covered"
    elif expected_role == "ambiguous":
        state, applicability, coverage = "insufficient_semantics", "uncertain", "not_covered"
    elif positive:
        state, applicability, coverage = "evaluation_finding_candidate", "applicable", "covered"
    else:
        state, applicability, coverage = (
            "no_issue_detected_within_coverage",
            "applicable",
            "covered",
        )
    fixture_kind = (
        "positive_issue_fixture"
        if positive
        else (
            "static_scope_verified_good"
            if expected_role in _STATIC_VERIFIED_GOOD_ROLES
            else "static_scope_hard_negative"
        )
    )
    static_ref = None
    if not positive:
        static_ref = {
            "record_type": "static_qualification_proof",
            "record_id": stable_id(
                "static-qualification-proof-lean-consolidated", audit_lock_digest, case_id
            ),
        }
    result_projection = {
        "record_type": "detector_result",
        "record_id": result_id,
        "state": state,
        "execution_class": "completed",
        "applicability_status": applicability,
        "coverage_status": coverage,
        "evaluation_candidate_refs": [candidate_ref] if positive else [],
        "source_ledger_entry_digest": entry_digest,
    }
    return {
        "schema_version": "0.19.0-round1-private",
        "record_type": "detector_case_outcome",
        "case_outcome_id": stable_id("detector-case-outcome", HELDOUT_LEDGER_DIGEST, case_id),
        "case_id": case_id,
        "problem_id": stable_id("qualification-problem", HELDOUT_LEDGER_DIGEST, case_id),
        "corpus_partition": "held_out",
        "fixture_kind": fixture_kind,
        "qualification_proof_family": "positive_issue" if positive else "static_closed_scope",
        "qualification_proof_status": "complete",
        "static_qualification_proof_ref": static_ref,
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
        "detector_manifest_digest": DETECTOR_MANIFEST_DIGEST,
        "detector_output_observed": True,
        "detector_run_outcome": {
            "execution_status": "completed",
            "applicability_status": applicability,
            "coverage_status": coverage,
        },
        "detector_result_outcomes": [
            {
                "detector_result_ref": {
                    "record_type": "detector_result",
                    "record_id": result_id,
                },
                "detector_result_digest": semantic_digest(result_projection),
                "state": state,
                "execution_class": "completed",
                "applicability_status": applicability,
                "coverage_status": coverage,
                "evaluation_candidate_refs": [candidate_ref] if positive else [],
            }
        ],
        "candidate_refs": [candidate_ref] if positive else [],
        "candidate_outcomes": (
            [
                {
                    "candidate_ref": candidate_ref,
                    "root_cause_ref": root_ref,
                    "status": "bounded_root_match",
                }
            ]
            if positive
            else []
        ),
        "root_cause_refs": [root_ref] if positive else [],
        "root_outcomes": (
            [
                {
                    "root_cause_ref": root_ref,
                    "matched_candidate_refs": [candidate_ref],
                    "status": "boundedly_localized",
                }
            ]
            if positive
            else []
        ),
        "source_audit_lock_digest": audit_lock_digest,
        "scientific_label_freeze_digest": SCIENTIFIC_LABEL_LEDGER_DIGEST,
        "comparison_status": "reconciled",
        "comparison_review_refs": [],
        "exclusion_reasons": [],
        "exact_cross_provider_agreement": False,
        "provider_families": ["Anthropic"],
        "fresh_contexts_verified": True,
        "model_free_reconciliation": True,
        "metric_input_status": "complete",
        "metric_eligible": True,
        "promotion_evidence_eligible": True,
        "provenance": _provenance(
            "2026-08-10T15:22:54Z", "deterministic_heldout_ledger_projection"
        ),
        "reconciled_at": "2026-08-10T15:22:54Z",
    }


def _provenance(created_at: str, method: str) -> dict[str, Any]:
    return {
        "actor": {
            "actor_kind": "controller",
            "actor_id": "software:sc-referee-eval",
            "display_name": "sc-referee evaluation controller",
        },
        "method": method,
        "created_at": created_at,
        "tool": "sc-referee-eval",
        "tool_version": "0.1.0",
    }


def _frozen_sensitivity_requirement(opening_path: Path) -> tuple[float, int]:
    if opening_path.is_symlink() or not opening_path.is_file():
        raise CompleteDomainPromotionError("Held-out opening must be one regular file.")
    try:
        opening = json.loads(opening_path.read_bytes().decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CompleteDomainPromotionError("Held-out opening is not strict UTF-8 JSON.") from error
    if not isinstance(opening, dict):
        raise CompleteDomainPromotionError("Held-out opening must be one JSON object.")
    supplied_digest = opening.get("semantic_digest")
    digest_payload = {key: value for key, value in opening.items() if key != "semantic_digest"}
    if (
        supplied_digest != HELDOUT_OPENING_DIGEST
        or semantic_digest(digest_payload) != HELDOUT_OPENING_DIGEST
    ):
        raise CompleteDomainPromotionError("Held-out opening digest does not match the seal.")
    adr_reference = opening.get("adr_reference")
    sensitivity_bar = (
        adr_reference.get("sensitivity_bar") if isinstance(adr_reference, Mapping) else None
    )
    if not isinstance(sensitivity_bar, str):
        raise CompleteDomainPromotionError("Held-out sensitivity bar is missing.")
    match = _SENSITIVITY_BAR.fullmatch(sensitivity_bar)
    if match is None:
        raise CompleteDomainPromotionError("Held-out sensitivity bar is unsupported.")
    numerator = _COUNT_WORDS[match.group("numerator")]
    denominator = _COUNT_WORDS[match.group("denominator")]
    if numerator > denominator:
        raise CompleteDomainPromotionError("Held-out sensitivity bar is inconsistent.")
    return numerator / denominator, denominator


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 64 and all(char in "0123456789abcdef" for char in suffix)


__all__ = [
    "CompleteDomainPromotionError",
    "build_round1_records",
    "build_round2_records",
    "numeric_threshold_policy",
    "project_heldout_detector_case_outcomes",
    "qualification_profile_descriptor",
]
