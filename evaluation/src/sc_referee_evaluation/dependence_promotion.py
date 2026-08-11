"""Private Round-1 projection for the sealed dependence held-out ledger.

This evaluation-side module installs no qualification authority.  It accepts exactly the
digest-bound seven-case dependence exam, verifies the six retained opening/ledger records and
their closed identities, and projects the ``detector_case_outcome`` inputs consumed by
``compile_qualification_evidence``.  The detector audits were static; the separate intake
sandbox executions established fixture ground truth and are not execution evidence for the
recognizer.  ADR-0073 records the maintainer's binding-level promotion decision.
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


class DependencePromotionError(ValueError):
    """The frozen dependence exam or its deterministic projection is inconsistent."""


DETECTOR_ID = "detector:bounded-analysis-method-conflict"
DETECTOR_VERSION = "0.3.0"
DETECTOR_MANIFEST_DIGEST = "sha256:5b74ec663a651bd3e2eb934c25896cfbbe02f6840e2ea898296c0d478aa97e0a"
ROUND2_DETECTOR_MANIFEST_DIGEST = (
    "sha256:05738abe8845442b25b9d03d35b5a5696f169ca46057aabd970561dd5bbf909e"
)
CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
CHECK_VERSION = "1.1.0"
BINDING_ID = (
    "method-conflict-binding:authorized-independent-unit-entry-into-row-independent-procedure-v1"
)
BINDING_DIGEST = "sha256:e212bf6f81ec30490c817cb810ce5214a160a5841b564019b10b8061ddc0cb16"
ROUND2_BINDING_DIGEST = "sha256:4a62385441043681dca65005be3c73a11858449955104dc8efe0582606331787"
CHECK_MANIFEST_DIGEST = "sha256:4f48a3104693cd6cdcf215bd620b59449ee87c3cd969ddbe7285f168e598ab21"
ADAPTER_ID = (
    "adapter:authorized-independent-unit-entry-into-row-independent-procedure:"
    "dependence-semantic-v1"
)
ADAPTER_VERSION = "1.1.0"
ADAPTER_IMPLEMENTATION_DIGEST = (
    "sha256:d5d22803d309ddda51651bcc033cb3e5aa4e093988550fb489b7e9671e289c54"
)
ADAPTER_MANIFEST_DIGEST = "sha256:81df54974a949648f6f86287df725c1a69ce63f41100480d299680f92eee3776"
RECOGNITION_GRAMMAR_DIGEST = (
    "sha256:bb3b283145ec1420491771ca49fbd2214e553602a735af2a6f7027980c8be873"
)
ROUND1_QUALIFICATION_ADAPTER_IMPLEMENTATION_DIGEST = (
    "sha256:4865e8b3e3344dd1d1478a2af78620d76a067d37a9cf34518c19deef6bce29b5"
)
ROUND2_EXAM_ADAPTER_IDENTITY = (
    ExamAdapterIdentity(
        adapter_id=ADAPTER_ID,
        adapter_version=ADAPTER_VERSION,
        implementation_digest=ADAPTER_IMPLEMENTATION_DIGEST,
        manifest_digest=ADAPTER_MANIFEST_DIGEST,
        recognition_grammar_digest=RECOGNITION_GRAMMAR_DIGEST,
    ),
)
DETECTOR_TUPLE_DIGEST = "sha256:252ef70a22da2e2168b26d7477bb0e666f6188d3786f0c41f2034356ab630795"
REGISTRY_CONTENT_DIGEST = "sha256:086db3b7dd0ebbb9e430763efcc6c1e981e22ea3db2b7e6b8200a51d3d38c253"
HELDOUT_OPENING_DIGEST = "sha256:8599661c954459daad710f61462ee3666dab8d9659f94e94714824ee6ad67c61"
AUTHORING_PROTOCOL_DIGEST = (
    "sha256:458c7176308c33de64bde0922823a2c4c7e91a1d1bc90ec86693ace0e86ed596"
)
INTAKE_LEDGER_DIGEST = "sha256:dbab0dd56d330192e7e8ed4d68b6e7612e0fb4a8d4ad50d59b8c5f0d0e4a6b83"
REVIEW_LEDGER_DIGEST = "sha256:6d3fac7bd3791aeffc161e406a6ab7b87e753347a3476a80d2ae2d0fe9d57019"
SCIENTIFIC_LABEL_LEDGER_DIGEST = (
    "sha256:10566c55b4a863ab174a94090a50d542f9f0e8464a979251c74e25efc91df55e"
)
HELDOUT_LEDGER_DIGEST = "sha256:7beb928087f8073f543636e0231e7fc57c1f9a843ea182107bf0b121a2e3d9d5"
ADR_0072_CONTENT_DIGEST = "sha256:011e9738852e73b59afa82a5968760a1e061b05f07abe853113e884cf23a6ee5"
THRESHOLD_FROZEN_AT = "2026-08-10T23:40:00Z"
CASE_RECONCILED_AT = "2026-08-11T00:41:53.935246Z"

QUALIFICATION_ENVELOPE = {
    "issue_classes": [
        "issue-class:repeated-authorized-independent-unit-entry-into-row-independent-procedure"
    ],
    "languages": ["python"],
    "packages": ["numpy==2.2.6", "scipy==1.14.0"],
    "operation_forms": [
        "closed_method_comparison_algebra_v1",
        "digest_bound_csv_unit_key_multiplicity_v1",
        "exact_selected_output_writer_scope_v1",
        "registered_row_independent_scipy_procedure_v1",
    ],
}
_ENVELOPE_ID = "authorized-independent-unit-entry-into-row-independent-procedure-v1.1.0-heldout"
_EXPECTED_CASE_ROLES = {
    "case:6f1702f1e1ff3855d34f": "hard_negative",
    "case:75bb533785f478cbdd8d": "ambiguous",
    "case:8a68d6ae147ce49e2a11": "error_bearing",
    "case:a516621a9cc0c4f6854d": "corrected_twin",
    "case:c37ea6f502dc593de820": "renamed_implementation",
    "case:c41c53bc6fedd68b0ccc": "unsupported",
    "case:e9e6bf9e80c9287dabe5": "valid_alternative",
}
_POSITIVE_ROLES = {"error_bearing", "renamed_implementation"}
_STATIC_VERIFIED_GOOD_ROLES = {"corrected_twin", "valid_alternative"}
_EXPECTED_LABELS = {
    "hard_negative": "verified_good_eligible",
    "ambiguous": "ambiguous_control",
    "error_bearing": "positive_demonstrated",
    "corrected_twin": "verified_good_eligible",
    "renamed_implementation": "positive_demonstrated",
    "unsupported": "unsupported_control",
    "valid_alternative": "verified_good_eligible",
}
_EXPECTED_TOP_LEVEL = {
    "envelope_id": _ENVELOPE_ID,
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
_SENSITIVITY_BAR = re.compile(r"(?P<numerator>one|two)_of_(?P<denominator>one|two)_positives\Z")
_FALSE_ACCUSATION_BAR = re.compile(r"(?P<numerator>zero)_of_(?P<denominator>five)_controls\Z")
_COUNT_WORDS = {"zero": 0, "one": 1, "two": 2, "five": 5}


def project_heldout_detector_case_outcomes(path: Path) -> list[dict[str, Any]]:
    """Project the accepted exam, refusing byte, identity, label, or outcome drift."""

    ledger = _load_semantic_record(path, "ledger_digest", HELDOUT_LEDGER_DIGEST, "detector ledger")
    for key, expected in _EXPECTED_TOP_LEVEL.items():
        if ledger.get(key) != expected:
            raise DependencePromotionError(f"Held-out detector ledger {key} drifted.")
    entries = ledger.get("entries")
    if not isinstance(entries, list) or len(entries) != len(_EXPECTED_CASE_ROLES):
        raise DependencePromotionError("Held-out detector ledger must contain seven entries.")
    by_case: dict[str, Mapping[str, Any]] = {}
    for item in entries:
        if not isinstance(item, Mapping):
            raise DependencePromotionError("Held-out detector ledger entry is malformed.")
        case_id = item.get("case_id")
        if not isinstance(case_id, str) or case_id in by_case:
            raise DependencePromotionError("Held-out case identities are missing or duplicated.")
        by_case[case_id] = item
    if set(by_case) != set(_EXPECTED_CASE_ROLES):
        raise DependencePromotionError("Held-out case identities do not equal the sealed set.")
    _verify_exam_record_chain(path.parent.parent)
    return [
        _project_entry(by_case[case_id], case_id, _EXPECTED_CASE_ROLES[case_id])
        for case_id in sorted(by_case)
    ]


def qualification_profile_descriptor() -> dict[str, Any]:
    """Describe the private lean-consolidated static scope bound by ADR-0073."""

    return {
        "record_type": "static_qualification_profile",
        "record_id": (
            "static-qualification-profile:authorized-independent-unit-entry-v110-lean-consolidated"
        ),
        "detector_tuple_digest": DETECTOR_TUPLE_DIGEST,
        "authoring_protocol_digest": AUTHORING_PROTOCOL_DIGEST,
        "scientific_label_ledger_digest": SCIENTIFIC_LABEL_LEDGER_DIGEST,
        "detector_run_ledger_digest": HELDOUT_LEDGER_DIGEST,
        "stage3_comparison_artifact": "absent_maintainer_accepted_lean_substitute_adr_0073",
    }


def numeric_threshold_policy(opening_path: Path) -> dict[str, Any]:
    """Translate the digest-bound ADR-0072 bars into the resolver vocabulary."""

    sensitivity_threshold, positive_count, false_threshold, control_count = (
        _frozen_threshold_requirements(opening_path)
    )
    value: dict[str, Any] = {
        "policy_kind": "pilot_informed_binding_thresholds_v1",
        "policy_id": "threshold-policy:authorized-independent-unit-entry-v110-heldout",
        "policy_version": "1.0.0",
        "decision_adr_ref": (
            "docs/implementation/ADR-0072-HELDOUT-THRESHOLD-DEPENDENCE-ENVELOPE.md"
        ),
        "pilot_evidence_refs": [
            "docs/implementation/ADR-0072-HELDOUT-THRESHOLD-DEPENDENCE-ENVELOPE.md",
            (
                "evaluation/qualification/authorized-independent-unit-entry-into-row-"
                "independent-procedure-v1.1.0-direct-lane/threshold-rehearsal/detector-run/"
                "DETECTOR_RUN_LEDGER.json"
            ),
        ],
        "frozen_at": THRESHOLD_FROZEN_AT,
        "held_out_labels_observed_before_freeze": False,
        "minimum_counts": {
            "workflows": 7,
            "problem_clusters": 7,
            "adjudicated_roots": positive_count,
            "control_cases": control_count,
        },
        "require_estimable_intervals": False,
        "metric_requirements": [
            {
                "metric_name": "completed_opportunity_false_positive_rate",
                "statistic": "estimate",
                "operator": "at_most",
                "threshold": false_threshold,
            },
            {
                "metric_name": "adjudicated_root_recall",
                "statistic": "estimate",
                "operator": "at_least",
                "threshold": sensitivity_threshold,
            },
        ],
        "absolute_count_requirements": [
            {"count_name": "missed_roots", "operator": "equals", "threshold": 0}
        ],
    }
    value["policy_semantic_digest"] = semantic_digest(value)
    return value


def verify_absolute_missed_root_gate(metric_set: Mapping[str, Any]) -> None:
    """Require the one closed absolute-count gate admitted by this private projector."""

    counts = metric_set.get("counts")
    policy = metric_set.get("numeric_threshold_policy")
    if not isinstance(counts, Mapping) or not isinstance(policy, Mapping):
        raise DependencePromotionError("The absolute missed-root gate inputs are malformed.")
    requirements = policy.get("absolute_count_requirements")
    expected = [{"count_name": "missed_roots", "operator": "equals", "threshold": 0}]
    missed_roots = counts.get("missed_roots")
    if (
        requirements != expected
        or not isinstance(missed_roots, int)
        or isinstance(missed_roots, bool)
        or missed_roots != 0
    ):
        raise DependencePromotionError("The absolute missed-root gate did not pass.")


def build_round1_records(
    ledger_path: Path, *, recorded_at: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the private metric-set/qualification pair without installing authority."""

    outcomes = project_heldout_detector_case_outcomes(ledger_path)
    opening_path = ledger_path.parent.parent / "opening" / "DEPENDENCE_HELDOUT_OPENING.json"
    policy = numeric_threshold_policy(opening_path)
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
            "adapter_id": "qualification-adapter:dependence-heldout-ledger-case-outcome-v1",
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
            "The grant applies only to the exact binding and digest pins recorded by ADR-0073.",
            "Intake sandbox execution is fixture ground truth, not detector execution evidence.",
        ],
        "provenance": _provenance(recorded_at, "deterministic_dependence_ledger_projection"),
    }
    verify_absolute_missed_root_gate(metric_set)
    qualification: dict[str, Any] = {
        "schema_version": "0.19.0-round1-private",
        "record_type": "detector_qualification",
        "qualification_id": "qualification:authorized-independent-unit-entry-v110-round1",
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
                "evaluation/qualification/authorized-independent-unit-entry-into-row-"
                "independent-procedure-v1.1.0-direct-lane/heldout-seven-case/review/"
                "REVIEW_LEDGER.json"
            ),
            (
                "evaluation/qualification/authorized-independent-unit-entry-into-row-"
                "independent-procedure-v1.1.0-direct-lane/heldout-seven-case/"
                "SCIENTIFIC_LABEL_LEDGER.json"
            ),
        ],
        "software_maintainer_approvals": [
            {
                "actor_kind": "human",
                "actor_id": "person:alex",
                "display_name": "Alex",
                "approved_on": "2026-08-10",
                "approval_quote": "go ahead with the qualification report and promotion",
                "decision_ref": "docs/implementation/ADR-0073-DEPENDENCE-ENVELOPE-PROMOTION.md",
            }
        ],
        "qualification_report_ref": (
            "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
            "procedure-v1.1.0-direct-lane/QUALIFICATION_REPORT.md"
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
            "no_missed_roots": True,
        },
        "static_scope_disclosure": {
            "profile_refs": [scope["static_qualification_profile_ref"]],
            "scope_statement": (
                "Seven digest-locked static audit closures under the exact dependence binding; "
                "the recognizer did not execute project-authored code. ADR-0073 accepts the "
                "lean-consolidated evidence because no separate Stage-3 comparison artifact "
                "exists. Intake sandbox executions established fixture ground truth only."
            ),
            "stage3_comparison_artifact_exists": False,
            "execution_claimed": False,
            "global_correctness_claimed": False,
        },
        "qualification_basis_disclosure": (
            "One-shot 7/7 held-out exam at the frozen two-of-two bar: zero candidates on five "
            "controls, two bounded candidates on two demonstrated errors, and zero missed roots. "
            "Round 1 records but does not install the grant."
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
    """Re-derive the sealed dependence evidence in public v0.19 shape at live pins."""

    binding, detector_manifest = _round2_live_identity()
    outcomes = deepcopy(project_heldout_detector_case_outcomes(ledger_path))
    for outcome in outcomes:
        outcome["schema_version"] = "0.19.0"
        outcome["detector_manifest_digest"] = binding.detector_manifest_digest
    opening_path = ledger_path.parent.parent / "opening" / "DEPENDENCE_HELDOUT_OPENING.json"
    policy = _round2_numeric_threshold_policy(opening_path)
    evidence = compile_qualification_evidence(outcomes, QUALIFICATION_ENVELOPE)
    if (
        evidence.get("counts", {}).get("missed_roots") != 0
        or evidence.get("counts", {}).get("adjudicated_roots") != 2
    ):
        raise DependencePromotionError("Round-2 absolute root counts did not replay.")
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
            "Any future grant applies only to this exact current binding and adapter identity.",
            "Intake sandbox execution is fixture ground truth, not detector execution evidence.",
        ],
        "provenance": _provenance(recorded_at, "deterministic_round2_current_pin_rederivation"),
    }
    qualification: dict[str, Any] = {
        "schema_version": "0.19.0",
        "record_type": "detector_qualification",
        "qualification_id": "qualification:authorized-independent-unit-entry-v110-round2",
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
                "evaluation/qualification/authorized-independent-unit-entry-into-row-"
                "independent-procedure-v1.1.0-direct-lane/heldout-seven-case/review/"
                "REVIEW_LEDGER.json"
            ),
            (
                "evaluation/qualification/authorized-independent-unit-entry-into-row-"
                "independent-procedure-v1.1.0-direct-lane/heldout-seven-case/"
                "SCIENTIFIC_LABEL_LEDGER.json"
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
                "decision_ref": "docs/implementation/ADR-0073-DEPENDENCE-ENVELOPE-PROMOTION.md",
            }
        ],
        "qualification_report_ref": (
            "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
            "procedure-v1.1.0-direct-lane/QUALIFICATION_REPORT.md"
        ),
        "safety_gates": _round2_safety_gates(),
        "static_scope_disclosure": {
            "profile_refs": [scope["static_qualification_profile_ref"]],
            "scope_statement": (
                "Seven digest-locked static audit closures under the exact dependence binding; "
                "the recognizer did not execute project-authored code. ADR-0073 accepts the "
                "lean-consolidated evidence without a separate Stage-3 comparison artifact. "
                "Intake sandbox executions established fixture ground truth only."
            ),
            "stage3_comparison_artifact_exists": False,
            "execution_claimed": False,
            "global_correctness_claimed": False,
        },
        "qualification_basis_disclosure": (
            "The same one-shot 7/7 held-out evidence at the frozen two-of-two bar is re-derived "
            "in v0.19 shape at the current live binding pins. It contains two bounded candidates, "
            "five controls without candidates, zero missed roots, and installs no grant."
        ),
        "decided_at": recorded_at,
        "provenance": _provenance(recorded_at, "maintainer_round2_rederivation_recording"),
    }
    registry = LocalSchemaRegistry(schema_root)
    registry.validate(metric_set)
    registry.validate(qualification)
    if semantic_digest(detector_manifest) != binding.detector_manifest_digest:
        raise DependencePromotionError("Live detector manifest changed during re-derivation.")
    return metric_set, qualification


def _round2_numeric_threshold_policy(opening_path: Path) -> dict[str, Any]:
    policy = numeric_threshold_policy(opening_path)
    expected = [{"count_name": "missed_roots", "operator": "equals", "threshold": 0}]
    if policy.pop("absolute_count_requirements", None) != expected:
        raise DependencePromotionError("Private absolute-count policy annotation drifted.")
    policy.pop("policy_semantic_digest")
    policy["policy_semantic_digest"] = semantic_digest(policy)
    return policy


def _round2_live_identity() -> tuple[MethodConflictBinding, dict[str, Any]]:
    bindings = [
        item
        for item in scientific_check_release_registry().method_conflict_bindings
        if item.binding_id == BINDING_ID
    ]
    if len(bindings) != 1:
        raise DependencePromotionError("Round-2 binding is absent or duplicated.")
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
        raise DependencePromotionError("Live Round-2 dependence identity is not exact.")
    collection_path = default_capability_manifest_root() / "detector-manifests.json"
    try:
        collection = json.loads(collection_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DependencePromotionError(
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
        raise DependencePromotionError("Live Round-2 detector manifest is not exact.")
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
            "adapter_id": "qualification-adapter:dependence-heldout-ledger-case-outcome-v1",
            "adapter_version": "2.0.0",
            "implementation_digest": sha256_digest(Path(__file__).read_bytes()),
        },
    }


def _round2_author_actor_ids(path: Path) -> list[str]:
    protocol = _load_semantic_record(
        path, "protocol_digest", AUTHORING_PROTOCOL_DIGEST, "authoring protocol"
    )
    assignments = protocol.get("author_assignments")
    if not isinstance(assignments, Sequence) or isinstance(assignments, (str, bytes)):
        raise DependencePromotionError("Authoring protocol assignments are malformed.")
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
            raise DependencePromotionError("Authoring protocol assignment identity is invalid.")
        actors.add(actor_id)
        assigned_cases.update(case_ids)
    if assigned_cases != set(_EXPECTED_CASE_ROLES) or not actors:
        raise DependencePromotionError("Author assignments do not cover the sealed cases once.")
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
        raise DependencePromotionError(f"Held-out role drifted for {case_id}.")
    positive = expected_role in _POSITIVE_ROLES
    if (
        entry.get("comparison_outcome") != ("true_positive" if positive else "true_negative")
        or entry.get("detector_positive") is not positive
        or entry.get("finding_candidate_count") != int(positive)
        or entry.get("frozen_label_status") != _EXPECTED_LABELS[expected_role]
        or entry.get("production_findings") != 0
        or entry.get("project_code_executions") != 0
        or entry.get("replay_equal") is not True
    ):
        raise DependencePromotionError(f"Held-out outcome is inconsistent for {case_id}.")
    if expected_role == "ambiguous":
        if entry.get("method_contract_applied") is not False:
            raise DependencePromotionError(f"Ambiguous authority state drifted for {case_id}.")
    elif (
        entry.get("method_contract_applied") is not True
        or entry.get("contract_candidate_id") != "one-analyzed-row-per-authorized-independent-unit"
    ):
        raise DependencePromotionError(f"Method-contract binding drifted for {case_id}.")
    audit_lock_digest = entry.get("audit_lock_digest")
    if not _is_sha256(audit_lock_digest):
        raise DependencePromotionError(f"Held-out audit lock is malformed for {case_id}.")
    assert isinstance(audit_lock_digest, str)

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
        "provenance": _provenance(CASE_RECONCILED_AT, "deterministic_dependence_ledger_projection"),
        "reconciled_at": CASE_RECONCILED_AT,
    }


def _verify_exam_record_chain(exam_root: Path) -> None:
    opening = _load_semantic_record(
        exam_root / "opening" / "DEPENDENCE_HELDOUT_OPENING.json",
        "semantic_digest",
        HELDOUT_OPENING_DIGEST,
        "held-out opening",
    )
    authoring = _load_semantic_record(
        exam_root / "authoring" / "AUTHORING_PROTOCOL.json",
        "protocol_digest",
        AUTHORING_PROTOCOL_DIGEST,
        "authoring protocol",
    )
    intake = _load_semantic_record(
        exam_root / "authoring" / "INTAKE_LEDGER.json",
        "ledger_digest",
        INTAKE_LEDGER_DIGEST,
        "intake ledger",
    )
    review = _load_semantic_record(
        exam_root / "review" / "REVIEW_LEDGER.json",
        "ledger_digest",
        REVIEW_LEDGER_DIGEST,
        "review ledger",
    )
    labels = _load_semantic_record(
        exam_root / "SCIENTIFIC_LABEL_LEDGER.json",
        "ledger_digest",
        SCIENTIFIC_LABEL_LEDGER_DIGEST,
        "scientific-label ledger",
    )
    if opening.get("envelope_id") != _ENVELOPE_ID:
        raise DependencePromotionError("Held-out opening envelope drifted.")
    _frozen_threshold_requirements(exam_root / "opening" / "DEPENDENCE_HELDOUT_OPENING.json")
    detector_tuple = authoring.get("detector_tuple")
    expected_adapter = {
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "implementation_digest": ADAPTER_IMPLEMENTATION_DIGEST,
        "manifest_digest": ADAPTER_MANIFEST_DIGEST,
        "recognition_grammar_digest": RECOGNITION_GRAMMAR_DIGEST,
    }
    if (
        authoring.get("envelope_id") != _ENVELOPE_ID
        or authoring.get("detector_tuple_digest") != DETECTOR_TUPLE_DIGEST
        or not isinstance(detector_tuple, Mapping)
        or detector_tuple.get("check_id") != CHECK_ID
        or detector_tuple.get("check_version") != CHECK_VERSION
        or detector_tuple.get("check_manifest_digest") != CHECK_MANIFEST_DIGEST
        or detector_tuple.get("detector_id") != DETECTOR_ID
        or detector_tuple.get("method_conflict_binding_digest") != BINDING_DIGEST
        or detector_tuple.get("registry_content_digest") != REGISTRY_CONTENT_DIGEST
        or detector_tuple.get("production_finding_permitted") is not False
        or detector_tuple.get("adapters") != [expected_adapter]
    ):
        raise DependencePromotionError("Exam-time detector tuple drifted.")
    if (
        intake.get("envelope_id") != _ENVELOPE_ID
        or intake.get("authoring_protocol_digest") != AUTHORING_PROTOCOL_DIGEST
        or intake.get("case_count") != 7
        or len(intake.get("entries", [])) != 7
        or review.get("envelope_id") != _ENVELOPE_ID
        or review.get("unresolved_case_ids") != []
        or review.get("escalation_ran") is not False
        or len(review.get("entries", [])) != 7
        or labels.get("envelope_id") != _ENVELOPE_ID
        or labels.get("authoring_protocol_digest") != AUTHORING_PROTOCOL_DIGEST
        or labels.get("review_ledger_digest") != REVIEW_LEDGER_DIGEST
        or labels.get("detector_output_observed") is not False
        or labels.get("label_count") != 7
        or len(labels.get("entries", [])) != 7
    ):
        raise DependencePromotionError("Exam ledger chain or chronology drifted.")


def _frozen_threshold_requirements(opening_path: Path) -> tuple[float, int, float, int]:
    opening = _load_semantic_record(
        opening_path, "semantic_digest", HELDOUT_OPENING_DIGEST, "held-out opening"
    )
    adr_reference = opening.get("adr_reference")
    if (
        not isinstance(adr_reference, Mapping)
        or adr_reference.get("document")
        != "docs/implementation/ADR-0072-HELDOUT-THRESHOLD-DEPENDENCE-ENVELOPE.md"
        or adr_reference.get("status") != "accepted"
        or adr_reference.get("accepted_on") != "2026-08-10"
        or adr_reference.get("content_digest") != ADR_0072_CONTENT_DIGEST
        or opening.get("threshold_authority") != "accepted_adr_0072"
        or opening.get("qualification_authority") != "none_opening_record_only"
        or opening.get("detector_output_observed") is not False
    ):
        raise DependencePromotionError("Held-out threshold authority drifted.")
    sensitivity = adr_reference.get("sensitivity_bar")
    false_accusation = adr_reference.get("false_accusation_bar")
    sensitivity_match = (
        _SENSITIVITY_BAR.fullmatch(sensitivity) if isinstance(sensitivity, str) else None
    )
    false_match = (
        _FALSE_ACCUSATION_BAR.fullmatch(false_accusation)
        if isinstance(false_accusation, str)
        else None
    )
    if sensitivity_match is None or false_match is None:
        raise DependencePromotionError("Held-out numeric bars are unsupported.")
    sensitivity_numerator = _COUNT_WORDS[sensitivity_match.group("numerator")]
    sensitivity_denominator = _COUNT_WORDS[sensitivity_match.group("denominator")]
    false_numerator = _COUNT_WORDS[false_match.group("numerator")]
    control_count = _COUNT_WORDS[false_match.group("denominator")]
    if sensitivity_numerator > sensitivity_denominator or false_numerator != 0:
        raise DependencePromotionError("Held-out numeric bars are inconsistent.")
    return (
        sensitivity_numerator / sensitivity_denominator,
        sensitivity_denominator,
        false_numerator / control_count,
        control_count,
    )


def _load_semantic_record(
    path: Path, digest_field: str, expected_digest: str, label: str
) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise DependencePromotionError(f"{label.capitalize()} must be one regular file.")
    try:
        value = json.loads(path.read_bytes().decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DependencePromotionError(f"{label.capitalize()} is not strict UTF-8 JSON.") from error
    if not isinstance(value, dict):
        raise DependencePromotionError(f"{label.capitalize()} must be one JSON object.")
    supplied = value.get(digest_field)
    digest_payload = {key: item for key, item in value.items() if key != digest_field}
    if supplied != expected_digest or semantic_digest(digest_payload) != expected_digest:
        raise DependencePromotionError(f"{label.capitalize()} digest does not match the seal.")
    return value


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


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    suffix = value.removeprefix("sha256:")
    return len(suffix) == 64 and all(char in "0123456789abcdef" for char in suffix)
