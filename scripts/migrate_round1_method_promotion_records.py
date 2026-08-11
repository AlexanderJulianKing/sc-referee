from __future__ import annotations

import argparse
import copy
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee.records.normalization import write_normalized_json_once
from sc_referee.records.schema_registry import LocalSchemaRegistry

SOURCE_VERSION = "0.19.0-round1-private"
TARGET_VERSION = "0.19.0"
_STANDARD_SAFETY_GATES = {
    "cluster_aware_uncertainty_reported",
    "conditional_never_promoted",
    "decisive_counterevidence_included",
    "no_known_high_or_critical_false_accusations",
    "proof_families_stratified",
    "public_development_cases_not_used_for_qualification",
    "qualification_report_public",
    "regression_fixture_for_every_discovered_false_accusation",
    "unresolved_disagreement_excluded",
    "verified_good_and_hard_negative_included",
}


class MethodPromotionMigrationError(ValueError):
    """Raised when a private Round-1 pair cannot be re-stamped without invention."""


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MethodPromotionMigrationError(f"Expected one JSON object in {path}")
    return value


def _replay_self_digest(record: Mapping[str, Any], field: str, label: str) -> None:
    basis = dict(record)
    supplied = basis.pop(field, None)
    if not isinstance(supplied, str) or supplied != semantic_digest(basis):
        raise MethodPromotionMigrationError(f"{label} does not replay its {field}")


def _author_ids(protocol: Mapping[str, Any]) -> list[str]:
    _replay_self_digest(protocol, "protocol_digest", "Authoring protocol")
    assignments = protocol.get("author_assignments")
    if not isinstance(assignments, Sequence) or isinstance(assignments, (str, bytes)):
        raise MethodPromotionMigrationError("Authoring protocol has no closed author assignments")
    result: set[str] = set()
    for assignment in assignments:
        participant = assignment.get("participant") if isinstance(assignment, Mapping) else None
        participant_id = (
            participant.get("participant_id") if isinstance(participant, Mapping) else None
        )
        if not isinstance(participant_id, str) or not participant_id.startswith("actor:"):
            raise MethodPromotionMigrationError("Author assignment has no participant identity")
        result.add(participant_id)
    if not result:
        raise MethodPromotionMigrationError("Authoring protocol contains no authors")
    return sorted(result)


def _replay_policy(policy: Mapping[str, Any], label: str) -> None:
    _replay_self_digest(policy, "policy_semantic_digest", label)


def _normalize_policy(policy: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
    _replay_policy(policy, "Round-1 threshold policy")
    normalized = copy.deepcopy(dict(policy))
    absolute = normalized.pop("absolute_count_requirements", None)
    if absolute is not None and absolute != [
        {"count_name": "missed_roots", "operator": "equals", "threshold": 0}
    ]:
        raise MethodPromotionMigrationError("Unknown private absolute-count policy extension")
    normalized.pop("policy_semantic_digest")
    normalized["policy_semantic_digest"] = semantic_digest(normalized)
    return normalized, absolute is not None


def _normalize_approval(value: Any) -> tuple[dict[str, Any], bool]:
    if not isinstance(value, Mapping):
        raise MethodPromotionMigrationError("Maintainer approval must be an object")
    required = {"actor_kind", "actor_id", "display_name", "approved_on", "decision_ref"}
    optional = {"approval_quote"}
    if not required.issubset(value) or not set(value).issubset(required | optional):
        raise MethodPromotionMigrationError("Private maintainer approval has an unknown shape")
    actor = {key: value[key] for key in ("actor_kind", "actor_id", "display_name")}
    return (
        {
            "actor": actor,
            "approved_on": value["approved_on"],
            "decision_ref": value["decision_ref"],
        },
        "approval_quote" in value,
    )


def migrate_round1_method_promotion_records(
    qualification_path: Path,
    metric_set_path: Path,
    authoring_protocol_path: Path,
    target_schema_root: Path,
    output: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Re-stamp one frozen private pair into accepted v0.19 representation only."""

    if output.exists() and any(output.iterdir()):
        raise MethodPromotionMigrationError(f"Migration output must be absent or empty: {output}")
    qualification = _read_object(qualification_path)
    metric_set = _read_object(metric_set_path)
    protocol = _read_object(authoring_protocol_path)
    if (
        qualification.get("schema_version") != SOURCE_VERSION
        or qualification.get("record_type") != "detector_qualification"
        or metric_set.get("schema_version") != SOURCE_VERSION
        or metric_set.get("record_type") != "qualification_metric_set"
    ):
        raise MethodPromotionMigrationError("Inputs must be the exact private Round-1 record pair")
    if qualification.get("numeric_threshold_policy") != metric_set.get("numeric_threshold_policy"):
        raise MethodPromotionMigrationError("Qualification and metric-set policies differ")
    if qualification.get("qualification_proof_families") != [
        "positive_issue",
        "static_closed_scope",
    ]:
        raise MethodPromotionMigrationError("Unknown private qualification proof families")

    ledger_paths = qualification.get("agent_adjudication_refs")
    if (
        not isinstance(ledger_paths, list)
        or not ledger_paths
        or not all(isinstance(item, str) and item for item in ledger_paths)
        or qualification.get("evaluation_refs") is not None
        or qualification.get("author_actor_ids") is not None
        or qualification.get("human_scientific_approvals") is not None
    ):
        raise MethodPromotionMigrationError("Private review-reference projection is not exact")

    safety_gates = qualification.get("safety_gates")
    if not isinstance(safety_gates, Mapping):
        raise MethodPromotionMigrationError("Private safety gates are malformed")
    extra_safety = set(safety_gates) - _STANDARD_SAFETY_GATES
    if extra_safety not in (set(), {"no_missed_roots"}) or (
        "no_missed_roots" in extra_safety and safety_gates.get("no_missed_roots") is not True
    ):
        raise MethodPromotionMigrationError("Unknown private safety-gate extension")

    raw_approvals = qualification.get("software_maintainer_approvals")
    if not isinstance(raw_approvals, list) or not raw_approvals:
        raise MethodPromotionMigrationError("Private record has no maintainer approval")
    approval_pairs = [_normalize_approval(item) for item in raw_approvals]
    policy, absolute_policy_removed = _normalize_policy(qualification["numeric_threshold_policy"])

    migrated_qualification = copy.deepcopy(qualification)
    migrated_metric_set = copy.deepcopy(metric_set)
    for record in (migrated_qualification, migrated_metric_set):
        record["schema_version"] = TARGET_VERSION
        record["numeric_threshold_policy"] = copy.deepcopy(policy)
    migrated_qualification["agent_adjudication_refs"] = []
    migrated_qualification["evaluation_refs"] = list(ledger_paths)
    migrated_qualification["author_actor_ids"] = _author_ids(protocol)
    migrated_qualification["human_scientific_approvals"] = []
    migrated_qualification["qualification_proof_families"] = ["static_closed_scope"]
    migrated_qualification["software_maintainer_approvals"] = [
        approval for approval, _quote_removed in approval_pairs
    ]
    migrated_qualification["safety_gates"] = {
        key: value for key, value in safety_gates.items() if key in _STANDARD_SAFETY_GATES
    }

    registry = LocalSchemaRegistry(target_schema_root)
    registry.validate(migrated_metric_set)
    registry.validate(migrated_qualification)

    output.mkdir(parents=True, exist_ok=True)
    write_normalized_json_once(output / "QUALIFICATION_METRIC_SET.json", migrated_metric_set)
    write_normalized_json_once(output / "DETECTOR_QUALIFICATION.json", migrated_qualification)
    write_normalized_json_once(
        output / "MIGRATION_REPORT.json",
        {
            "source_schema_version": SOURCE_VERSION,
            "target_schema_version": TARGET_VERSION,
            "agent_adjudication_record_invented": False,
            "evaluation_paths_moved": True,
            "author_ids_derived_from_replayed_protocol": True,
            "human_scientific_approval_invented": False,
            "maintainer_approval_quote_omitted": any(
                quote_removed for _approval, quote_removed in approval_pairs
            ),
            "private_absolute_policy_annotation_omitted": absolute_policy_removed,
            "private_safety_annotation_omitted": "no_missed_roots" in extra_safety,
            "qualification_grant_installed": False,
            "finding_authority_created": False,
            "execution_launched": False,
            "validation": "passed",
        },
    )
    return migrated_metric_set, migrated_qualification


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-stamp private Round-1 method-promotion records for schema v0.19.0"
    )
    parser.add_argument("qualification", type=Path)
    parser.add_argument("metric_set", type=Path)
    parser.add_argument("authoring_protocol", type=Path)
    parser.add_argument("--target-schema-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    migrate_round1_method_promotion_records(
        args.qualification.resolve(),
        args.metric_set.resolve(),
        args.authoring_protocol.resolve(),
        args.target_schema_root.resolve(),
        args.output.resolve(),
    )
    print(f"Re-stamped private Round-1 records as schema {TARGET_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
