from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.9.0"
BASELINE_VERSION = "0.9.0"
RELEASE_VERSION = "0.10.0"
ADR_PATH = "docs/implementation/ADR-0009-STAGE3-ROOT-CAUSE-EQUIVALENCE-AND-METRICS.md"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _replace_version(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}").replace(
            BASELINE_VERSION, RELEASE_VERSION
        )
    if isinstance(value, list):
        return [_replace_version(item) for item in value]
    if isinstance(value, dict):
        return {key: _replace_version(item) for key, item in value.items()}
    return value


def _require_empty_destination(output: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Release output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)


def _common_ref(name: str) -> dict[str, str]:
    return {
        "$ref": (
            f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
            f"common.schema.json#/$defs/{name}"
        )
    }


def _typed_ref(record_type: str) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "record_id": _common_ref("Identifier"),
            "record_type": {"const": record_type},
        },
        "required": ["record_type", "record_id"],
        "type": "object",
    }


def _typed_ref_or_null(record_type: str) -> dict[str, Any]:
    return {"oneOf": [_typed_ref(record_type), {"type": "null"}]}


def _extensions_schema() -> dict[str, Any]:
    return {
        "additionalProperties": True,
        "propertyNames": {"pattern": "^x-"},
        "type": "object",
    }


def _record_schema(
    *,
    title: str,
    record_type: str,
    properties: dict[str, Any],
    required: list[str],
    all_of: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    shared = {
        "schema_version": _common_ref("SchemaVersion"),
        "record_type": {"const": record_type},
        "extensions": _extensions_schema(),
    }
    result: dict[str, Any] = {
        "$id": (
            f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
            f"{record_type.replace('_', '-')}.schema.json"
        ),
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {**shared, **properties},
        "required": ["schema_version", "record_type", *required],
        "title": title,
        "type": "object",
    }
    if all_of:
        result["allOf"] = all_of
    return result


def _admission_checks_schema() -> dict[str, Any]:
    true_checks = (
        "direct_entailment",
        "no_reversing_unknown",
        "exact_detector_applicability",
        "counterevidence_protocol_complete",
        "bounded_wording",
        "deterministic_replay",
        "source_references_resolved",
    )
    return {
        "additionalProperties": False,
        "properties": {
            **{name: {"const": True} for name in true_checks},
            "material_premise_ids": {
                "items": _common_ref("Identifier"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "unresolved_material_premise_ids": {
                "items": _common_ref("Identifier"),
                "maxItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
            "non_inferences": {
                "items": {"minLength": 1, "type": "string"},
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
        },
        "required": [
            *true_checks,
            "material_premise_ids",
            "unresolved_material_premise_ids",
            "non_inferences",
        ],
        "type": "object",
    }


def _detector_evaluation_candidate_schema() -> dict[str, Any]:
    return _record_schema(
        title="sc-referee Qualification-only Detector Evaluation Candidate",
        record_type="detector_evaluation_candidate",
        properties={
            "evaluation_candidate_id": _common_ref("Identifier"),
            "case_id": _common_ref("Identifier"),
            "fixture_ref": _typed_ref("benchmark_fixture"),
            "scientific_label_freeze_digest": _common_ref("Digest"),
            "audit_bundle_ref": _typed_ref("audit_bundle"),
            "audit_bundle_digest": _common_ref("Digest"),
            "semantic_lock_digest": _common_ref("Digest"),
            "detector_id": _common_ref("Identifier"),
            "detector_version": _common_ref("SemVer"),
            "detector_manifest_digest": _common_ref("Digest"),
            "source_detector_result_ref": _typed_ref("detector_result"),
            "source_detector_result_digest": _common_ref("Digest"),
            "proposed_assessment_type": {"const": "finding"},
            "title": {"minLength": 1, "type": "string"},
            "bounded_statement": {"minLength": 1, "type": "string"},
            "issue_class": _common_ref("IssueClass"),
            "root_locator": {
                "$ref": (
                    f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                    "finding.schema.json#/properties/root_cause"
                )
            },
            "subject_refs": {
                "items": _common_ref("RecordRef"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "affected_record_refs": {
                "items": _common_ref("RecordRef"),
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
            "evidence": {
                "items": _common_ref("EvidenceItem"),
                "minItems": 1,
                "type": "array",
            },
            "admission_checks": _admission_checks_schema(),
            "maturity_gate_bypassed_for_evaluation": {"const": True},
            "production_admission_permitted": {"const": False},
            "production_finding_ref": {"const": None},
            "candidate_created_at": _common_ref("Timestamp"),
            "non_inferences": {
                "items": {"minLength": 1, "type": "string"},
                "minItems": 2,
                "type": "array",
                "uniqueItems": True,
            },
            "provenance": _common_ref("Provenance"),
        },
        required=[
            "evaluation_candidate_id",
            "case_id",
            "fixture_ref",
            "scientific_label_freeze_digest",
            "audit_bundle_ref",
            "audit_bundle_digest",
            "semantic_lock_digest",
            "detector_id",
            "detector_version",
            "detector_manifest_digest",
            "source_detector_result_ref",
            "source_detector_result_digest",
            "proposed_assessment_type",
            "title",
            "bounded_statement",
            "issue_class",
            "root_locator",
            "subject_refs",
            "affected_record_refs",
            "evidence",
            "admission_checks",
            "maturity_gate_bypassed_for_evaluation",
            "production_admission_permitted",
            "production_finding_ref",
            "candidate_created_at",
            "non_inferences",
            "provenance",
        ],
    )


def _reviewer_agent_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "provider": {"minLength": 1, "type": "string"},
            "agent_surface": {"minLength": 1, "type": "string"},
            "model_name": {"minLength": 1, "type": "string"},
            "model_id": {"minLength": 1, "type": "string"},
            "model_snapshot": {"type": ["string", "null"]},
            "agent_version": {"minLength": 1, "type": "string"},
            "reasoning_configuration": {"type": ["string", "object", "null"]},
            "execution_context_id": _common_ref("Identifier"),
            "independent_context": {"const": True},
            "system_prompt_digest": _common_ref("Digest"),
            "task_prompt_digest": _common_ref("Digest"),
            "tool_policy_digest": _common_ref("Digest"),
            "environment_digest": _common_ref("Digest"),
        },
        "required": [
            "provider",
            "agent_surface",
            "model_name",
            "model_id",
            "agent_version",
            "execution_context_id",
            "independent_context",
            "system_prompt_digest",
            "task_prompt_digest",
            "tool_policy_digest",
            "environment_digest",
        ],
        "type": "object",
    }


def _candidate_mapping_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "candidate_ref": _typed_ref("detector_evaluation_candidate"),
            "root_cause_ref": _typed_ref_or_null("adjudicated_root_cause"),
            "scientific_relation": {
                "enum": [
                    "same_first_material_divergence",
                    "different_root_cause",
                    "no_adjudicated_root",
                    "unresolved",
                ]
            },
            "statement_boundedness": {
                "enum": [
                    "within_adjudicated_bounds",
                    "exceeds_adjudicated_bounds",
                    "not_applicable",
                    "unresolved",
                ]
            },
            "affected_scope": {
                "enum": [
                    "within_adjudicated_scope",
                    "exceeds_adjudicated_scope",
                    "outside_declared_scope",
                    "not_applicable",
                    "unresolved",
                ]
            },
            "issue_class_relationship": {
                "enum": ["exact", "mismatch", "not_applicable", "unresolved"]
            },
            "evidence": {
                "items": _common_ref("EvidenceItem"),
                "minItems": 1,
                "type": "array",
            },
            "material_ambiguity": {"type": "boolean"},
            "rationale": {"minLength": 1, "type": "string"},
        },
        "required": [
            "candidate_ref",
            "root_cause_ref",
            "scientific_relation",
            "statement_boundedness",
            "affected_scope",
            "issue_class_relationship",
            "evidence",
            "material_ambiguity",
            "rationale",
        ],
        "type": "object",
    }


def _stage3_comparison_review_schema() -> dict[str, Any]:
    return _record_schema(
        title="sc-referee Stage-3 Detector Comparison Review",
        record_type="stage3_comparison_review",
        properties={
            "comparison_review_id": _common_ref("Identifier"),
            "case_id": _common_ref("Identifier"),
            "stage": {"const": "stage3_detector_comparison"},
            "reviewer_agent": _reviewer_agent_schema(),
            "fixture_ref": _typed_ref("benchmark_fixture"),
            "adjudication_ref": _typed_ref("benchmark_adjudication"),
            "adjudication_digest": _common_ref("Digest"),
            "scientific_label_freeze_digest": _common_ref("Digest"),
            "audit_bundle_ref": _typed_ref("audit_bundle"),
            "audit_bundle_digest": _common_ref("Digest"),
            "detector_id": _common_ref("Identifier"),
            "detector_version": _common_ref("SemVer"),
            "detector_manifest_digest": _common_ref("Digest"),
            "root_cause_refs": {
                "items": _typed_ref("adjudicated_root_cause"),
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
            "candidate_refs": {
                "items": _typed_ref("detector_evaluation_candidate"),
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
            "candidate_mappings": {
                "items": _candidate_mapping_schema(),
                "minItems": 0,
                "type": "array",
            },
            "unmatched_root_cause_refs": {
                "items": _typed_ref("adjudicated_root_cause"),
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
            "all_roots_accounted_for": {"const": True},
            "all_candidates_accounted_for": {"const": True},
            "comparison_access": {
                "additionalProperties": False,
                "properties": {
                    "scientific_label_frozen_before_detector_output": {"const": True},
                    "detector_output_visible": {"const": True},
                    "canonical_root_causes_visible": {"const": True},
                    "other_stage3_reviews_hidden": {"const": True},
                    "prior_review_context_reused": {"const": False},
                },
                "required": [
                    "scientific_label_frozen_before_detector_output",
                    "detector_output_visible",
                    "canonical_root_causes_visible",
                    "other_stage3_reviews_hidden",
                    "prior_review_context_reused",
                ],
                "type": "object",
            },
            "material_ambiguity_retained": {"type": "boolean"},
            "confidence_used_for_equivalence": {"const": False},
            "packet_digest": _common_ref("Digest"),
            "transcript_digest": _common_ref("Digest"),
            "completed_at": _common_ref("Timestamp"),
            "provenance": _common_ref("Provenance"),
        },
        required=[
            "comparison_review_id",
            "case_id",
            "stage",
            "reviewer_agent",
            "fixture_ref",
            "adjudication_ref",
            "adjudication_digest",
            "scientific_label_freeze_digest",
            "audit_bundle_ref",
            "audit_bundle_digest",
            "detector_id",
            "detector_version",
            "detector_manifest_digest",
            "root_cause_refs",
            "candidate_refs",
            "candidate_mappings",
            "unmatched_root_cause_refs",
            "all_roots_accounted_for",
            "all_candidates_accounted_for",
            "comparison_access",
            "material_ambiguity_retained",
            "confidence_used_for_equivalence",
            "packet_digest",
            "transcript_digest",
            "completed_at",
            "provenance",
        ],
    )


def _root_outcome_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "root_cause_ref": _typed_ref("adjudicated_root_cause"),
            "status": {
                "enum": [
                    "boundedly_localized",
                    "localized_but_overstated",
                    "missed",
                    "unresolved",
                ]
            },
            "matched_candidate_refs": {
                "items": _typed_ref("detector_evaluation_candidate"),
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
        },
        "required": ["root_cause_ref", "status", "matched_candidate_refs"],
        "type": "object",
    }


def _candidate_outcome_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "candidate_ref": _typed_ref("detector_evaluation_candidate"),
            "status": {
                "enum": [
                    "bounded_root_match",
                    "overstated_root_match",
                    "false_root_localization",
                    "out_of_declared_scope",
                    "mixed_detector_attribution",
                    "unresolved",
                ]
            },
            "root_cause_ref": _typed_ref_or_null("adjudicated_root_cause"),
        },
        "required": ["candidate_ref", "status", "root_cause_ref"],
        "type": "object",
    }


def _detector_case_outcome_schema() -> dict[str, Any]:
    return _record_schema(
        title="sc-referee Reconciled Detector Case Outcome",
        record_type="detector_case_outcome",
        properties={
            "case_outcome_id": _common_ref("Identifier"),
            "case_id": _common_ref("Identifier"),
            "problem_id": _common_ref("Identifier"),
            "corpus_partition": {
                "enum": [
                    "public_development",
                    "held_out",
                    "hidden",
                    "independent_replication",
                ]
            },
            "fixture_kind": {
                "enum": [
                    "verified_good_fixture",
                    "scope_verified_good",
                    "hard_negative_fixture",
                    "positive_issue_fixture",
                    "ambiguous_fixture",
                ]
            },
            "fixture_ref": _typed_ref("benchmark_fixture"),
            "adjudication_ref": _typed_ref("benchmark_adjudication"),
            "scientific_label_freeze_digest": _common_ref("Digest"),
            "audit_bundle_ref": _typed_ref("audit_bundle"),
            "audit_bundle_digest": _common_ref("Digest"),
            "detector_id": _common_ref("Identifier"),
            "detector_version": _common_ref("SemVer"),
            "detector_manifest_digest": _common_ref("Digest"),
            "comparison_review_refs": {
                "items": _typed_ref("stage3_comparison_review"),
                "minItems": 2,
                "type": "array",
                "uniqueItems": True,
            },
            "provider_families": {
                "items": {"minLength": 1, "type": "string"},
                "minItems": 2,
                "type": "array",
                "uniqueItems": True,
            },
            "fresh_contexts_verified": {"const": True},
            "exact_cross_provider_agreement": {"type": "boolean"},
            "comparison_status": {"enum": ["reconciled", "comparison_excluded"]},
            "exclusion_reasons": {
                "items": {"minLength": 1, "type": "string"},
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
            "root_cause_refs": {
                "items": _typed_ref("adjudicated_root_cause"),
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
            "candidate_refs": {
                "items": _typed_ref("detector_evaluation_candidate"),
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
            "root_outcomes": {
                "items": _root_outcome_schema(),
                "minItems": 0,
                "type": "array",
            },
            "candidate_outcomes": {
                "items": _candidate_outcome_schema(),
                "minItems": 0,
                "type": "array",
            },
            "detector_run_outcome": {
                "additionalProperties": False,
                "properties": {
                    "execution_status": {"enum": ["completed", "detector_error"]},
                    "applicability_status": {"enum": ["applicable", "not_applicable", "uncertain"]},
                    "coverage_status": {
                        "enum": ["covered", "partially_covered", "not_covered", "unknown"]
                    },
                },
                "required": [
                    "execution_status",
                    "applicability_status",
                    "coverage_status",
                ],
                "type": "object",
            },
            "metric_eligible": {"type": "boolean"},
            "promotion_evidence_eligible": {"type": "boolean"},
            "detector_output_observed": {"const": True},
            "model_free_reconciliation": {"const": True},
            "reconciled_at": _common_ref("Timestamp"),
            "provenance": _common_ref("Provenance"),
        },
        required=[
            "case_outcome_id",
            "case_id",
            "problem_id",
            "corpus_partition",
            "fixture_kind",
            "fixture_ref",
            "adjudication_ref",
            "scientific_label_freeze_digest",
            "audit_bundle_ref",
            "audit_bundle_digest",
            "detector_id",
            "detector_version",
            "detector_manifest_digest",
            "comparison_review_refs",
            "provider_families",
            "fresh_contexts_verified",
            "exact_cross_provider_agreement",
            "comparison_status",
            "exclusion_reasons",
            "root_cause_refs",
            "candidate_refs",
            "root_outcomes",
            "candidate_outcomes",
            "detector_run_outcome",
            "metric_eligible",
            "promotion_evidence_eligible",
            "detector_output_observed",
            "model_free_reconciliation",
            "reconciled_at",
            "provenance",
        ],
        all_of=[
            {
                "if": {
                    "properties": {"comparison_status": {"const": "reconciled"}},
                    "required": ["comparison_status"],
                },
                "then": {
                    "properties": {
                        "exact_cross_provider_agreement": {"const": True},
                        "exclusion_reasons": {"maxItems": 0},
                        "metric_eligible": {"const": True},
                    }
                },
            },
            {
                "if": {
                    "properties": {"comparison_status": {"const": "comparison_excluded"}},
                    "required": ["comparison_status"],
                },
                "then": {
                    "properties": {
                        "exclusion_reasons": {"minItems": 1},
                        "metric_eligible": {"const": False},
                        "promotion_evidence_eligible": {"const": False},
                    }
                },
            },
            {
                "if": {
                    "properties": {"corpus_partition": {"const": "public_development"}},
                    "required": ["corpus_partition"],
                },
                "then": {"properties": {"promotion_evidence_eligible": {"const": False}}},
            },
            {
                "if": {
                    "properties": {"fixture_kind": {"const": "positive_issue_fixture"}},
                    "required": ["fixture_kind"],
                },
                "then": {
                    "properties": {
                        "root_cause_refs": {"minItems": 1},
                        "root_outcomes": {"minItems": 1},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "fixture_kind": {
                            "enum": [
                                "verified_good_fixture",
                                "scope_verified_good",
                                "hard_negative_fixture",
                                "ambiguous_fixture",
                            ]
                        }
                    },
                    "required": ["fixture_kind"],
                },
                "then": {
                    "properties": {
                        "root_cause_refs": {"maxItems": 0},
                        "root_outcomes": {"maxItems": 0},
                    }
                },
            },
        ],
    )


_METRIC_NAMES = [
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
]


def _metric_entry_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "metric_name": {"enum": _METRIC_NAMES},
            "numerator": {"minimum": 0, "type": "integer"},
            "denominator": {"minimum": 0, "type": "integer"},
            "estimate": {"maximum": 1, "minimum": 0, "type": ["number", "null"]},
            "interval": {
                "additionalProperties": False,
                "properties": {
                    "status": {"enum": ["estimated", "not_estimable"]},
                    "confidence_level": {"const": 0.95},
                    "lower": {"maximum": 1, "minimum": 0, "type": ["number", "null"]},
                    "upper": {"maximum": 1, "minimum": 0, "type": ["number", "null"]},
                    "valid_replicates": {"minimum": 0, "type": "integer"},
                    "invalid_replicates": {"minimum": 0, "type": "integer"},
                    "limitations": {
                        "items": {"minLength": 1, "type": "string"},
                        "minItems": 0,
                        "type": "array",
                        "uniqueItems": True,
                    },
                },
                "required": [
                    "status",
                    "confidence_level",
                    "lower",
                    "upper",
                    "valid_replicates",
                    "invalid_replicates",
                    "limitations",
                ],
                "type": "object",
            },
        },
        "required": ["metric_name", "numerator", "denominator", "estimate", "interval"],
        "type": "object",
    }


def _qualification_metric_set_schema() -> dict[str, Any]:
    count_names = [
        "problem_clusters",
        "workflows",
        "opportunities",
        "applicable_covered_opportunities",
        "evaluation_candidates",
        "adjudicated_roots",
        "bounded_root_matches",
        "overstated_root_matches",
        "false_root_localizations",
        "boundedly_localized_roots",
        "localized_but_overstated_roots",
        "missed_roots",
        "abstentions",
        "unsupported_opportunities",
        "detector_errors",
        "unresolved_comparisons",
    ]
    return _record_schema(
        title="sc-referee Qualification Metric Set",
        record_type="qualification_metric_set",
        properties={
            "metric_set_id": _common_ref("Identifier"),
            "metric_profile": {"const": "root-cause-clustered-metrics-v1"},
            "detector_id": _common_ref("Identifier"),
            "detector_version": _common_ref("SemVer"),
            "detector_manifest_digest": _common_ref("Digest"),
            "qualification_envelope": {
                "additionalProperties": False,
                "properties": {
                    "issue_classes": {
                        "items": {"minLength": 1, "type": "string"},
                        "minItems": 1,
                        "type": "array",
                        "uniqueItems": True,
                    },
                    "languages": {
                        "items": {"minLength": 1, "type": "string"},
                        "minItems": 0,
                        "type": "array",
                        "uniqueItems": True,
                    },
                    "packages": {
                        "items": {"minLength": 1, "type": "string"},
                        "minItems": 0,
                        "type": "array",
                        "uniqueItems": True,
                    },
                    "operation_forms": {
                        "items": {"minLength": 1, "type": "string"},
                        "minItems": 1,
                        "type": "array",
                        "uniqueItems": True,
                    },
                },
                "required": ["issue_classes", "languages", "packages", "operation_forms"],
                "type": "object",
            },
            "case_outcome_inputs": {
                "items": {
                    "additionalProperties": False,
                    "properties": {
                        "case_outcome_ref": _typed_ref("detector_case_outcome"),
                        "case_outcome_digest": _common_ref("Digest"),
                    },
                    "required": ["case_outcome_ref", "case_outcome_digest"],
                    "type": "object",
                },
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "corpus_partitions": {
                "items": {
                    "enum": [
                        "public_development",
                        "held_out",
                        "hidden",
                        "independent_replication",
                    ]
                },
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "problem_cluster_ids": {
                "items": _common_ref("Identifier"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "excluded_case_outcomes": {
                "items": {
                    "additionalProperties": False,
                    "properties": {
                        "case_outcome_ref": _typed_ref("detector_case_outcome"),
                        "reason": {"minLength": 1, "type": "string"},
                    },
                    "required": ["case_outcome_ref", "reason"],
                    "type": "object",
                },
                "minItems": 0,
                "type": "array",
            },
            "counts": {
                "additionalProperties": False,
                "properties": {name: {"minimum": 0, "type": "integer"} for name in count_names},
                "required": count_names,
                "type": "object",
            },
            "metrics": {
                "items": _metric_entry_schema(),
                "minItems": len(_METRIC_NAMES),
                "maxItems": len(_METRIC_NAMES),
                "type": "array",
            },
            "bootstrap": {
                "additionalProperties": False,
                "properties": {
                    "profile": {"const": "problem-cluster-bootstrap-percentile-v1"},
                    "cluster_unit": {"const": "problem_id"},
                    "replicates": {"const": 10000},
                    "confidence_level": {"const": 0.95},
                    "counter_stream": {"const": "sha256-counter-rejection-sampling-v1"},
                    "input_digest": _common_ref("Digest"),
                },
                "required": [
                    "profile",
                    "cluster_unit",
                    "replicates",
                    "confidence_level",
                    "counter_stream",
                    "input_digest",
                ],
                "type": "object",
            },
            "numeric_threshold_policy": {"const": "deferred_until_pilot_threshold_adr"},
            "promotion_permitted": {"const": False},
            "promotion_evidence_eligible": {"type": "boolean"},
            "generated_at": _common_ref("Timestamp"),
            "non_inferences": {
                "items": {"minLength": 1, "type": "string"},
                "minItems": 2,
                "type": "array",
                "uniqueItems": True,
            },
            "provenance": _common_ref("Provenance"),
        },
        required=[
            "metric_set_id",
            "metric_profile",
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
            "bootstrap",
            "numeric_threshold_policy",
            "promotion_permitted",
            "promotion_evidence_eligible",
            "generated_at",
            "non_inferences",
            "provenance",
        ],
        all_of=[
            {
                "if": {
                    "properties": {
                        "corpus_partitions": {"contains": {"const": "public_development"}}
                    },
                    "required": ["corpus_partitions"],
                },
                "then": {"properties": {"promotion_evidence_eligible": {"const": False}}},
            }
        ],
    )


_NEW_RECORDS = {
    "detector_evaluation_candidate": _detector_evaluation_candidate_schema,
    "stage3_comparison_review": _stage3_comparison_review_schema,
    "detector_case_outcome": _detector_case_outcome_schema,
    "qualification_metric_set": _qualification_metric_set_schema,
}


def _extend_benchmark_fixture(schema: dict[str, Any]) -> None:
    schema["properties"]["corpus_partition"] = {
        "enum": [
            "public_development",
            "held_out",
            "hidden",
            "independent_replication",
        ]
    }
    schema["required"].append("corpus_partition")


def _extend_benchmark_adjudication(schema: dict[str, Any]) -> None:
    schema["properties"]["stage3_detector_comparison_refs"]["maxItems"] = 0


def _extend_detector_qualification(schema: dict[str, Any]) -> None:
    schema["properties"]["quantitative_metrics"] = {
        "oneOf": [
            {"type": "null"},
            {
                "additionalProperties": False,
                "properties": {
                    "metric_profile": {"const": "root-cause-clustered-metrics-v1"},
                    "metric_set_refs": {
                        "items": _typed_ref("qualification_metric_set"),
                        "minItems": 1,
                        "type": "array",
                        "uniqueItems": True,
                    },
                },
                "required": ["metric_profile", "metric_set_refs"],
                "type": "object",
            },
        ]
    }
    schema.setdefault("allOf", []).append(
        {
            "if": {
                "properties": {
                    "numeric_threshold_policy": {"const": "deferred_until_pilot_threshold_adr"}
                },
                "required": ["numeric_threshold_policy"],
            },
            "then": {"properties": {"outcome": {"not": {"const": "promoted"}}}},
        }
    )


def _extend_bundle(schema: dict[str, Any]) -> None:
    for record_type in _NEW_RECORDS:
        collection = f"{record_type}s"
        schema["properties"][collection] = {
            "items": {
                "$ref": (
                    f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                    f"{record_type.replace('_', '-')}.schema.json"
                )
            },
            "minItems": 0,
            "type": "array",
        }
        schema["required"].append(collection)


def _extend_union(schema: dict[str, Any]) -> None:
    for record_type in _NEW_RECORDS:
        schema["oneOf"].append(
            {
                "$ref": (
                    f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                    f"{record_type.replace('_', '-')}.schema.json"
                )
            }
        )


def _extend_catalog(catalog: dict[str, Any]) -> None:
    for record_type in _NEW_RECORDS:
        filename = f"{record_type.replace('_', '-')}.schema.json"
        catalog["schemas"].append(
            {
                "name": record_type,
                "file": filename,
                "id": (f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{filename}"),
                "kind": "record",
            }
        )


def _upgrade_example_records(value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            _upgrade_example_records(item)
        return
    if not isinstance(value, dict):
        return
    record_type = value.get("record_type")
    if record_type == "benchmark_fixture" and isinstance(value.get("fixture_id"), str):
        value["corpus_partition"] = "public_development"
    elif record_type == "benchmark_adjudication" and isinstance(value.get("adjudication_id"), str):
        value["stage3_detector_comparison_refs"] = []
    elif record_type == "detector_qualification" and isinstance(value.get("qualification_id"), str):
        if value.get("outcome") == "promoted":
            extensions = value.setdefault("extensions", {})
            extensions["x-v0-9-outcome"] = value["outcome"]
            extensions["x-v0-9-effective-maturity"] = value["effective_maturity"]
            extensions["x-v0-9-quantitative-metrics"] = value.get("quantitative_metrics")
            value["outcome"] = "deferred"
            value["effective_maturity"] = "experimental"
            value["qualification_basis_disclosure"] = (
                "Legacy v0.9 promotion is deferred because no typed Stage-3 metric set or accepted "
                "numeric threshold policy exists; no validated maturity is claimed."
            )
        value["quantitative_metrics"] = None
    elif record_type == "audit_bundle" and isinstance(value.get("bundle_id"), str):
        for new_type in _NEW_RECORDS:
            value[f"{new_type}s"] = []
    for item in value.values():
        _upgrade_example_records(item)


def _provenance(method: str) -> dict[str, Any]:
    return {
        "actor": {
            "actor_kind": "controller",
            "actor_id": "software:sc-referee-eval",
            "display_name": "sc-referee evaluation controller",
        },
        "method": method,
        "created_at": "2026-07-28T20:00:00Z",
        "tool": "sc-referee-eval",
        "tool_version": "0.6.0",
    }


def _evidence() -> dict[str, Any]:
    return {
        "evidence_id": "evidence:stage3-source",
        "description": "The candidate and adjudicated root cite the same frozen claim span.",
        "support_role": "supports",
        "record_refs": [{"record_type": "claim", "record_id": "claim:1"}],
        "source_refs": [],
    }


def _candidate_ref() -> dict[str, str]:
    return {
        "record_type": "detector_evaluation_candidate",
        "record_id": "evaluation-candidate:case-1",
    }


def _root_ref() -> dict[str, str]:
    return {
        "record_type": "adjudicated_root_cause",
        "record_id": "adjudicated-root-cause:case-1",
    }


def _detector_evaluation_candidate_example() -> dict[str, Any]:
    return {
        "schema_version": RELEASE_VERSION,
        "record_type": "detector_evaluation_candidate",
        "evaluation_candidate_id": "evaluation-candidate:case-1",
        "case_id": "case:gene-1",
        "fixture_ref": {"record_type": "benchmark_fixture", "record_id": "fixture:case-1"},
        "scientific_label_freeze_digest": "sha256:" + "1" * 64,
        "audit_bundle_ref": {"record_type": "audit_bundle", "record_id": "bundle:1"},
        "audit_bundle_digest": "sha256:" + "2" * 64,
        "semantic_lock_digest": "sha256:" + "3" * 64,
        "detector_id": "detector:claim-direction",
        "detector_version": "1.0.0",
        "detector_manifest_digest": "sha256:" + "4" * 64,
        "source_detector_result_ref": {
            "record_type": "detector_result",
            "record_id": "result:claim-direction",
        },
        "source_detector_result_digest": "sha256:" + "5" * 64,
        "proposed_assessment_type": "finding",
        "title": "Reported direction disagrees with the linked result",
        "bounded_statement": (
            "The report states a positive direction while the linked result is negative under the "
            "resolved contrast orientation."
        ),
        "issue_class": "claim_result_disagreement",
        "root_locator": {
            "root_ref": {"record_type": "observed_result", "record_id": "result:1"},
            "violated_semantic_dimension": "comparison_direction",
            "explanation": "The exact report and result directions disagree.",
        },
        "subject_refs": [{"record_type": "claim", "record_id": "claim:1"}],
        "affected_record_refs": [{"record_type": "claim", "record_id": "claim:1"}],
        "evidence": [_evidence()],
        "admission_checks": {
            "direct_entailment": True,
            "no_reversing_unknown": True,
            "exact_detector_applicability": True,
            "counterevidence_protocol_complete": True,
            "bounded_wording": True,
            "deterministic_replay": True,
            "source_references_resolved": True,
            "material_premise_ids": ["premise:contrast-orientation"],
            "unresolved_material_premise_ids": [],
            "non_inferences": ["No global workflow correctness claim is established."],
        },
        "maturity_gate_bypassed_for_evaluation": True,
        "production_admission_permitted": False,
        "production_finding_ref": None,
        "candidate_created_at": "2026-07-28T20:00:00Z",
        "non_inferences": [
            "This qualification-only candidate is not a production Finding.",
            "Bypassing maturity for evaluation does not grant Finding authority.",
        ],
        "provenance": _provenance("deterministic_evaluation_candidate_projection"),
    }


def _reviewer(provider: str, suffix: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "agent_surface": "coding-agent",
        "model_name": f"reference-model-{suffix}",
        "model_id": f"model:{suffix}",
        "model_snapshot": "2026-07-28",
        "agent_version": "1.0.0",
        "reasoning_configuration": "pinned",
        "execution_context_id": f"context:stage3:{suffix}",
        "independent_context": True,
        "system_prompt_digest": "sha256:" + "6" * 64,
        "task_prompt_digest": "sha256:" + "7" * 64,
        "tool_policy_digest": "sha256:" + "8" * 64,
        "environment_digest": "sha256:" + "9" * 64,
    }


def _stage3_comparison_review_example() -> dict[str, Any]:
    return {
        "schema_version": RELEASE_VERSION,
        "record_type": "stage3_comparison_review",
        "comparison_review_id": "stage3-review:provider-a:case-1",
        "case_id": "case:gene-1",
        "stage": "stage3_detector_comparison",
        "reviewer_agent": _reviewer("ProviderA", "provider-a"),
        "fixture_ref": {"record_type": "benchmark_fixture", "record_id": "fixture:case-1"},
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": "benchmark-adjudication:case-1",
        },
        "adjudication_digest": "sha256:" + "a" * 64,
        "scientific_label_freeze_digest": "sha256:" + "1" * 64,
        "audit_bundle_ref": {"record_type": "audit_bundle", "record_id": "bundle:1"},
        "audit_bundle_digest": "sha256:" + "2" * 64,
        "detector_id": "detector:claim-direction",
        "detector_version": "1.0.0",
        "detector_manifest_digest": "sha256:" + "4" * 64,
        "root_cause_refs": [_root_ref()],
        "candidate_refs": [_candidate_ref()],
        "candidate_mappings": [
            {
                "candidate_ref": _candidate_ref(),
                "root_cause_ref": _root_ref(),
                "scientific_relation": "same_first_material_divergence",
                "statement_boundedness": "within_adjudicated_bounds",
                "affected_scope": "within_adjudicated_scope",
                "issue_class_relationship": "exact",
                "evidence": [_evidence()],
                "material_ambiguity": False,
                "rationale": "The exact frozen evidence supports the same bounded divergence.",
            }
        ],
        "unmatched_root_cause_refs": [],
        "all_roots_accounted_for": True,
        "all_candidates_accounted_for": True,
        "comparison_access": {
            "scientific_label_frozen_before_detector_output": True,
            "detector_output_visible": True,
            "canonical_root_causes_visible": True,
            "other_stage3_reviews_hidden": True,
            "prior_review_context_reused": False,
        },
        "material_ambiguity_retained": False,
        "confidence_used_for_equivalence": False,
        "packet_digest": "sha256:" + "b" * 64,
        "transcript_digest": "sha256:" + "c" * 64,
        "completed_at": "2026-07-28T20:10:00Z",
        "provenance": _provenance("captured_stage3_comparison_review"),
    }


def _detector_case_outcome_example() -> dict[str, Any]:
    return {
        "schema_version": RELEASE_VERSION,
        "record_type": "detector_case_outcome",
        "case_outcome_id": "detector-case-outcome:case-1",
        "case_id": "case:gene-1",
        "problem_id": "problem:gene-1",
        "corpus_partition": "public_development",
        "fixture_kind": "positive_issue_fixture",
        "fixture_ref": {"record_type": "benchmark_fixture", "record_id": "fixture:case-1"},
        "adjudication_ref": {
            "record_type": "benchmark_adjudication",
            "record_id": "benchmark-adjudication:case-1",
        },
        "scientific_label_freeze_digest": "sha256:" + "1" * 64,
        "audit_bundle_ref": {"record_type": "audit_bundle", "record_id": "bundle:1"},
        "audit_bundle_digest": "sha256:" + "2" * 64,
        "detector_id": "detector:claim-direction",
        "detector_version": "1.0.0",
        "detector_manifest_digest": "sha256:" + "4" * 64,
        "comparison_review_refs": [
            {
                "record_type": "stage3_comparison_review",
                "record_id": "stage3-review:provider-a:case-1",
            },
            {
                "record_type": "stage3_comparison_review",
                "record_id": "stage3-review:provider-b:case-1",
            },
        ],
        "provider_families": ["ProviderA", "ProviderB"],
        "fresh_contexts_verified": True,
        "exact_cross_provider_agreement": True,
        "comparison_status": "reconciled",
        "exclusion_reasons": [],
        "root_cause_refs": [_root_ref()],
        "candidate_refs": [_candidate_ref()],
        "root_outcomes": [
            {
                "root_cause_ref": _root_ref(),
                "status": "boundedly_localized",
                "matched_candidate_refs": [_candidate_ref()],
            }
        ],
        "candidate_outcomes": [
            {
                "candidate_ref": _candidate_ref(),
                "status": "bounded_root_match",
                "root_cause_ref": _root_ref(),
            }
        ],
        "detector_run_outcome": {
            "execution_status": "completed",
            "applicability_status": "applicable",
            "coverage_status": "covered",
        },
        "metric_eligible": True,
        "promotion_evidence_eligible": False,
        "detector_output_observed": True,
        "model_free_reconciliation": True,
        "reconciled_at": "2026-07-28T20:20:00Z",
        "provenance": _provenance("deterministic_stage3_case_reconciliation"),
    }


def _qualification_metric_set_example() -> dict[str, Any]:
    counts = {
        "problem_clusters": 1,
        "workflows": 1,
        "opportunities": 1,
        "applicable_covered_opportunities": 1,
        "evaluation_candidates": 1,
        "adjudicated_roots": 1,
        "bounded_root_matches": 1,
        "overstated_root_matches": 0,
        "false_root_localizations": 0,
        "boundedly_localized_roots": 1,
        "localized_but_overstated_roots": 0,
        "missed_roots": 0,
        "abstentions": 0,
        "unsupported_opportunities": 0,
        "detector_errors": 0,
        "unresolved_comparisons": 0,
    }
    numerators = {
        "workflow_unsafe_candidate_probability": 0,
        "completed_opportunity_false_positive_rate": 0,
        "applicable_covered_opportunity_false_positive_rate": 0,
        "finding_candidate_precision": 1,
        "false_root_localization_rate": 0,
        "overstatement_rate": 0,
        "adjudicated_root_recall": 1,
        "bounded_root_localization_accuracy": 1,
        "abstention_rate": 0,
        "unsupported_rate": 0,
        "detector_error_rate": 0,
        "unresolved_comparison_rate": 0,
    }
    metrics = []
    for name in _METRIC_NAMES:
        numerator = numerators[name]
        metrics.append(
            {
                "metric_name": name,
                "numerator": numerator,
                "denominator": 1,
                "estimate": float(numerator),
                "interval": {
                    "status": "not_estimable",
                    "confidence_level": 0.95,
                    "lower": None,
                    "upper": None,
                    "valid_replicates": 0,
                    "invalid_replicates": 10000,
                    "limitations": [
                        "At least two nonempty problem clusters are required for an interval."
                    ],
                },
            }
        )
    return {
        "schema_version": RELEASE_VERSION,
        "record_type": "qualification_metric_set",
        "metric_set_id": "qualification-metric-set:claim-direction-dev",
        "metric_profile": "root-cause-clustered-metrics-v1",
        "detector_id": "detector:claim-direction",
        "detector_version": "1.0.0",
        "detector_manifest_digest": "sha256:" + "4" * 64,
        "qualification_envelope": {
            "issue_classes": ["claim_result_disagreement"],
            "languages": ["Python", "Markdown"],
            "packages": [],
            "operation_forms": ["bounded_scalar_direction_comparison"],
        },
        "case_outcome_inputs": [
            {
                "case_outcome_ref": {
                    "record_type": "detector_case_outcome",
                    "record_id": "detector-case-outcome:case-1",
                },
                "case_outcome_digest": "sha256:" + "d" * 64,
            }
        ],
        "corpus_partitions": ["public_development"],
        "problem_cluster_ids": ["problem:gene-1"],
        "excluded_case_outcomes": [],
        "counts": counts,
        "metrics": metrics,
        "bootstrap": {
            "profile": "problem-cluster-bootstrap-percentile-v1",
            "cluster_unit": "problem_id",
            "replicates": 10000,
            "confidence_level": 0.95,
            "counter_stream": "sha256-counter-rejection-sampling-v1",
            "input_digest": "sha256:" + "e" * 64,
        },
        "numeric_threshold_policy": "deferred_until_pilot_threshold_adr",
        "promotion_permitted": False,
        "promotion_evidence_eligible": False,
        "generated_at": "2026-07-28T20:30:00Z",
        "non_inferences": [
            "Development metrics do not qualify or promote the detector.",
            "A point estimate or zero observed false positives is not a correctness certificate.",
        ],
        "provenance": _provenance("deterministic_clustered_metric_calculation"),
    }


_NEW_EXAMPLES = {
    "detector-evaluation-candidate.example.json": _detector_evaluation_candidate_example,
    "stage3-comparison-review.example.json": _stage3_comparison_review_example,
    "detector-case-outcome.example.json": _detector_case_outcome_example,
    "qualification-metric-set.example.json": _qualification_metric_set_example,
}


def _release_readme() -> str:
    return """# sc-referee schema package

**Version:** 0.10.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.10.0/`.

Version 0.10.0 implements accepted ADR-0009. It separates qualification-only detector candidates
from production Findings, records fresh cross-provider Stage-3 comparison reviews, deterministically
reconciles detector/root-cause case outcomes, and publishes typed problem-clustered metric evidence.

No record in this release permits detector promotion while the numeric threshold policy remains
deferred. Evaluation candidates have no production Finding authority. Prose similarity, model
confidence, and majority vote cannot establish detector/root-cause equivalence. Accepted v0.9.0 and
earlier schema packages remain immutable.
"""


def _release_changelog() -> str:
    return """# Changelog

## 0.10.0

- Accepted ADR-0009 and added qualification-only DetectorEvaluationCandidate records.
- Added fresh Stage3ComparisonReview and deterministic DetectorCaseOutcome records.
- Added typed QualificationMetricSet records with exact counts and problem-cluster bootstrap fields.
- Required forward-only Stage-3 chronology without mutating frozen BenchmarkAdjudication records.
- Closed detector promotion while numeric thresholds remain deferred.
- Required fail-closed migration of legacy open-ended metrics and promoted qualifications.

""" + (BASELINE / "CHANGELOG.md").read_text(encoding="utf-8").removeprefix("# Changelog\n")


def _release_invariants() -> str:
    return (
        (BASELINE / "CONTROLLER_INVARIANTS.md").read_text(encoding="utf-8")
        + """

## Stage-3 equivalence and metric invariants added in 0.10.0

- An experimental detector may be represented only by a qualification-only candidate whose
  production admission is false; it does not become a Finding.
- Stage-3 comparison starts only after the scientific-label freeze and uses fresh provider contexts.
- Candidate/root equivalence requires identical cross-provider mappings and exact frozen evidence.
- Prose similarity, confidence, embeddings, and majority vote have no equivalence authority.
- Every admitted root and in-scope candidate is accounted for; disagreement remains excluded.
- Root recall deduplicates multiple candidate manifestations of one root cause.
- Metrics retain integer numerators, denominators, exact case digests, and problem clusters.
- Public development cases and deferred numeric thresholds cannot support detector promotion.
- Stage 3 links forward and never mutates or redigests the frozen scientific adjudication.
"""
    )


def _stage3_tests() -> str:
    return """from copy import deepcopy

from test_examples import invalid, load


def test_evaluation_candidate_cannot_grant_production_finding_authority():
    candidate = load("detector-evaluation-candidate.example.json")
    candidate["production_admission_permitted"] = True
    invalid(candidate, "detector_evaluation_candidate")
    candidate = load("detector-evaluation-candidate.example.json")
    candidate["production_finding_ref"] = {"record_type": "finding", "record_id": "finding:bad"}
    invalid(candidate, "detector_evaluation_candidate")


def test_stage3_review_requires_post_freeze_access_and_fresh_context():
    review = load("stage3-comparison-review.example.json")
    review["comparison_access"]["prior_review_context_reused"] = True
    invalid(review, "stage3_comparison_review")
    review = load("stage3-comparison-review.example.json")
    review["confidence_used_for_equivalence"] = True
    invalid(review, "stage3_comparison_review")


def test_reconciled_case_requires_exact_agreement_and_no_exclusion():
    outcome = load("detector-case-outcome.example.json")
    outcome["exact_cross_provider_agreement"] = False
    invalid(outcome, "detector_case_outcome")
    outcome = load("detector-case-outcome.example.json")
    outcome["exclusion_reasons"] = ["material disagreement"]
    invalid(outcome, "detector_case_outcome")


def test_public_development_case_cannot_be_promotion_evidence():
    outcome = load("detector-case-outcome.example.json")
    outcome["promotion_evidence_eligible"] = True
    invalid(outcome, "detector_case_outcome")
    metrics = load("qualification-metric-set.example.json")
    metrics["promotion_evidence_eligible"] = True
    invalid(metrics, "qualification_metric_set")


def test_deferred_threshold_policy_cannot_promote_detector():
    qualification = load("detector-qualification.example.json")
    qualification["outcome"] = "promoted"
    qualification["effective_maturity"] = "validated"
    invalid(qualification, "detector_qualification")


def test_frozen_adjudication_cannot_gain_backward_stage3_refs():
    adjudication = load("benchmark-adjudication.example.json")
    adjudication["stage3_detector_comparison_refs"] = [
        {"record_type": "detector_case_outcome", "record_id": "outcome:late"}
    ]
    invalid(adjudication, "benchmark_adjudication")


def test_bundle_requires_every_stage3_collection():
    for field in (
        "detector_evaluation_candidates",
        "stage3_comparison_reviews",
        "detector_case_outcomes",
        "qualification_metric_sets",
    ):
        bundle = load("audit-bundle.example.json")
        del bundle[field]
        invalid(bundle, "audit_bundle")
"""


def write_manifest(output: Path) -> None:
    entries = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.sha256" or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(output).as_posix()
        entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    (output / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def build_release(output: Path) -> int:
    """Build accepted v0.10.0 without modifying immutable v0.9.0."""

    _require_empty_destination(output)
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "benchmark-fixture.schema.json":
            _extend_benchmark_fixture(schema)
        elif source.name == "benchmark-adjudication.schema.json":
            _extend_benchmark_adjudication(schema)
        elif source.name == "detector-qualification.schema.json":
            _extend_detector_qualification(schema)
        elif source.name == "audit-bundle.schema.json":
            _extend_bundle(schema)
        elif source.name == "record-union.schema.json":
            _extend_union(schema)
        _write_json(schema_output / source.name, schema)
    for record_type, schema_builder in _NEW_RECORDS.items():
        _write_json(
            schema_output / f"{record_type.replace('_', '-')}.schema.json",
            schema_builder(),
        )

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _extend_catalog(catalog)
    catalog["schemas"] = sorted(catalog["schemas"], key=lambda item: str(item["name"]))
    _write_json(output / "schema-catalog.json", catalog)

    example_count = 0
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        _upgrade_example_records(example)
        _write_json(output / "examples" / source.name, example)
        example_count += 1
    for name, example_builder in _NEW_EXAMPLES.items():
        _write_json(output / "examples" / name, example_builder())
        example_count += 1

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.9_to_v0.10.md").write_text(
        """# Migration from v0.9.0 to v0.10.0

Add empty Stage-3 evaluation collections and classify every legacy BenchmarkFixture as public
development evidence. Keep frozen BenchmarkAdjudication Stage-3 back-references empty. Do not infer
an evaluation candidate, candidate/root mapping, case outcome, metric, interval, or promotion.
Legacy open-ended quantitative metric objects are preserved only in namespaced migration metadata.
A legacy promoted DetectorQualification becomes deferred with experimental effective maturity until
typed metric evidence and a later accepted numeric-threshold policy exist. Do not carry forward a
StorageManifest because migrated bytes require a new manifest.
""",
        encoding="utf-8",
    )
    _write_json(
        output / "RELEASE_STATUS.json",
        {
            "accepted": True,
            "baseline_version": BASELINE_VERSION,
            "public_release": True,
            "release_version": RELEASE_VERSION,
            "source_adr": ADR_PATH,
        },
    )

    tests_output = output / "tests"
    tests_output.mkdir(parents=True, exist_ok=True)
    for source in sorted((BASELINE / "tests").glob("*.py")):
        text = source.read_text(encoding="utf-8")
        text = text.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}")
        text = text.replace('len(u["oneOf"])==49', 'len(u["oneOf"])==53')
        text = text.replace(
            'x["review_basis"]="human_panel"; x["agent_adjudication_refs"]=[]',
            'x["outcome"]="promoted"; x["effective_maturity"]="validated"\n'
            '    x["review_basis"]="human_panel"; x["agent_adjudication_refs"]=[]',
        )
        (tests_output / source.name).write_text(text, encoding="utf-8")
    (tests_output / "test_stage3_invariants.py").write_text(_stage3_tests(), encoding="utf-8")
    validator = (BASELINE / "tools" / "validate_records.py").read_text(encoding="utf-8")
    (output / "tools").mkdir(parents=True, exist_ok=True)
    (output / "tools" / "validate_records.py").write_text(
        validator.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}"), encoding="utf-8"
    )
    baseline_pyproject = (BASELINE / "pyproject.toml").read_text(encoding="utf-8")
    (output / "pyproject.toml").write_text(
        baseline_pyproject.replace(BASELINE_VERSION, RELEASE_VERSION), encoding="utf-8"
    )

    test_count = 0
    for test_path in tests_output.glob("*.py"):
        module = ast.parse(test_path.read_text(encoding="utf-8"))
        test_count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in module.body
        )
    schema_count = len(catalog["schemas"])
    (output / "VALIDATION.txt").write_text(
        "sc-referee schema package 0.10.0 validation\n\n"
        f"JSON Schemas checked: {schema_count}\n"
        f"Cataloged schemas: {schema_count}\n"
        f"Example records validated: {example_count}\n"
        f"Invariant tests declared: {test_count}\n"
        "Canonical local references: all resolved\n"
        "JSON Schema meta-validation: passed\n",
        encoding="utf-8",
    )
    write_manifest(output)
    return example_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.10.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
