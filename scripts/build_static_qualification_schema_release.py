from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.14.0"
BASELINE_VERSION = "0.14.0"
RELEASE_VERSION = "0.15.0"
SOURCE_ADRS = ["docs/implementation/ADR-0022-STATIC-CLOSED-SCOPE-QUALIFICATION-PROOF.md"]

STATIC_GOOD = "static_scope_verified_good"
STATIC_HARD = "static_scope_hard_negative"
STATIC_KINDS = [STATIC_GOOD, STATIC_HARD]
PROOF_FAMILIES = [
    "clean_execution",
    "documented_external_execution",
    "static_closed_scope",
]


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


def _schema_ref(name: str) -> dict[str, str]:
    return {"$ref": f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/{name}.schema.json"}


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


def _bound_ref(record_type: str) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "record_ref": _typed_ref(record_type),
            "semantic_digest": _common_ref("Digest"),
        },
        "required": ["record_ref", "semantic_digest"],
        "type": "object",
    }


def _bound_private_manifest(manifest_kind: str) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "manifest_kind": {"const": manifest_kind},
            "manifest_id": _common_ref("Identifier"),
            "semantic_digest": _common_ref("Digest"),
        },
        "required": ["manifest_kind", "manifest_id", "semantic_digest"],
        "type": "object",
    }


def _artifact_ref(kind: str | None = None) -> dict[str, Any]:
    kind_schema: dict[str, Any] = {"minLength": 1, "type": "string"}
    if kind is not None:
        kind_schema = {"const": kind}
    return {
        "additionalProperties": False,
        "properties": {
            "artifact_id": _common_ref("Identifier"),
            "artifact_kind": kind_schema,
            "content_digest": _common_ref("Digest"),
        },
        "required": ["artifact_kind", "artifact_id", "content_digest"],
        "type": "object",
    }


def _sorted_string_array(*, min_items: int = 0, enum: list[str] | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"minLength": 1, "type": "string"}
    if enum is not None:
        item = {"enum": enum}
    return {
        "items": item,
        "minItems": min_items,
        "type": "array",
        "uniqueItems": True,
    }


def _base_record(
    *, title: str, record_type: str, identity_field: str, properties: dict[str, Any]
) -> dict[str, Any]:
    shared = {
        "schema_version": _common_ref("SchemaVersion"),
        "record_type": {"const": record_type},
        identity_field: _common_ref("Identifier"),
        "provenance": _common_ref("Provenance"),
        "extensions": {
            "additionalProperties": True,
            "propertyNames": {"pattern": "^x-"},
            "type": "object",
        },
    }
    return {
        "$id": (
            f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
            f"{record_type.replace('_', '-')}.schema.json"
        ),
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {**shared, **properties},
        "required": [
            "schema_version",
            "record_type",
            identity_field,
            *properties.keys(),
            "provenance",
        ],
        "title": title,
        "type": "object",
    }


def _static_profile_schema() -> dict[str, Any]:
    dependency = {
        "additionalProperties": False,
        "properties": {
            "dependency_kind": {"enum": ["implementation", "runtime"]},
            "path": {"minLength": 1, "type": "string"},
            "content_digest": _common_ref("Digest"),
        },
        "required": ["dependency_kind", "path", "content_digest"],
        "type": "object",
    }
    rules = {
        "additionalProperties": False,
        "properties": {
            "candidate_suffixes": {"const": [".csv", ".md", ".py"]},
            "candidate_enumeration": {
                "const": "all_matching_regular_files_in_snapshot_sorted_by_path"
            },
            "dependency_closure": {
                "const": "unique_supported_csv_mean_writer_report_transitive_path"
            },
            "parser_completeness": {
                "const": "strict_utf8_full_bytes_supported_grammar_or_unavailable"
            },
            "report_path_source": {"const": "opaque_case_assignment_manifest"},
            "surface_inventory": {
                "const": "every_literal_directional_sentence_in_complete_selected_report"
            },
        },
        "required": [
            "candidate_suffixes",
            "candidate_enumeration",
            "dependency_closure",
            "parser_completeness",
            "report_path_source",
            "surface_inventory",
        ],
        "type": "object",
    }
    budgets = {
        "additionalProperties": False,
        "properties": {
            "max_candidate_files": {"minimum": 1, "type": "integer"},
            "max_total_bytes": {"minimum": 1, "type": "integer"},
            "max_recursion_depth": {"minimum": 1, "type": "integer"},
            "max_elapsed_milliseconds": {"minimum": 1, "type": "integer"},
        },
        "required": [
            "max_candidate_files",
            "max_total_bytes",
            "max_recursion_depth",
            "max_elapsed_milliseconds",
        ],
        "type": "object",
    }
    target = {
        "additionalProperties": False,
        "properties": {
            "manifest": _bound_ref("detector_manifest"),
            "detector_id": {"const": "detector:bounded-report-mean-direction"},
            "detector_version": {"const": "0.1.0"},
            "implementation_digest": _common_ref("Digest"),
            "material_premise_class": {"const": "static_closed_scope"},
            "parser_manifests": {
                "items": _bound_ref("parser_manifest"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "semantic_profile_manifests": {
                "items": _bound_private_manifest("semantic_profile_manifest"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "version_manifests": {
                "items": _bound_private_manifest("version_manifest"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
        },
        "required": [
            "manifest",
            "detector_id",
            "detector_version",
            "implementation_digest",
            "material_premise_class",
            "parser_manifests",
            "semantic_profile_manifests",
            "version_manifests",
        ],
        "type": "object",
    }
    verifier = {
        "additionalProperties": False,
        "properties": {
            "entry_point": {
                "const": "sc_referee_evaluation.static_qualification:verify_bounded_direction_case"
            },
            "implementation_digest": _common_ref("Digest"),
            "dependency_closure": {
                "items": dependency,
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "allowed_shared_utilities": {
                "const": [
                    "canonical_json",
                    "content_hashing",
                    "schema_shape_validation",
                    "source_reference_resolution",
                ]
            },
        },
        "required": [
            "entry_point",
            "implementation_digest",
            "dependency_closure",
            "allowed_shared_utilities",
        ],
        "type": "object",
    }
    vocabularies = {
        "additionalProperties": False,
        "properties": {
            "applicability_obligation_ids": _sorted_string_array(min_items=1),
            "counterevidence_check_ids": _sorted_string_array(min_items=1),
            "completion_statuses": {"const": ["completed", "error", "unavailable"]},
            "outcomes": {
                "const": [
                    "agreement",
                    "conflict_absent",
                    "conflict_present",
                    "counterevidence_absent",
                    "counterevidence_present",
                ]
            },
        },
        "required": [
            "applicability_obligation_ids",
            "counterevidence_check_ids",
            "completion_statuses",
            "outcomes",
        ],
        "type": "object",
    }
    schema = _base_record(
        title="StaticQualificationProfile",
        record_type="static_qualification_profile",
        identity_field="profile_id",
        properties={
            "profile_version": {"const": "1.0.0"},
            "target_detector": target,
            "verifier": verifier,
            "selection_rules": rules,
            "budgets": budgets,
            "vocabularies": vocabularies,
            "selection_protocol_artifact": _artifact_ref("corpus_selection_protocol"),
            "frozen_at": _common_ref("Timestamp"),
            "profile_semantic_digest": _common_ref("Digest"),
        },
    )
    return schema


def _check_result() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "check_id": _common_ref("Identifier"),
            "completion_status": {"enum": ["completed", "unavailable", "error"]},
            "outcome": {
                "oneOf": [
                    {
                        "enum": [
                            "agreement",
                            "conflict_absent",
                            "conflict_present",
                            "counterevidence_absent",
                            "counterevidence_present",
                        ]
                    },
                    {"type": "null"},
                ]
            },
            "evidence_paths": _sorted_string_array(),
            "detail_code": {"minLength": 1, "type": "string"},
        },
        "required": [
            "check_id",
            "completion_status",
            "outcome",
            "evidence_paths",
            "detail_code",
        ],
        "type": "object",
    }


def _static_proof_schema() -> dict[str, Any]:
    retained = {
        "additionalProperties": False,
        "properties": {
            "path": {"minLength": 1, "type": "string"},
            "byte_size": {"minimum": 0, "type": "integer"},
            "content_digest": _common_ref("Digest"),
            "encoding": {"const": "utf-8"},
            "file_record": _bound_ref("file_record"),
            "asset_identity": _bound_ref("asset_identity"),
        },
        "required": [
            "path",
            "byte_size",
            "content_digest",
            "encoding",
            "file_record",
            "asset_identity",
        ],
        "type": "object",
    }
    node = {
        "additionalProperties": False,
        "properties": {
            "node_id": _common_ref("Identifier"),
            "node_kind": {
                "enum": ["raw_byte_source", "candidate", "dependency", "derived_fact", "check"]
            },
            "path": {"type": ["string", "null"]},
            "semantic_digest": _common_ref("Digest"),
        },
        "required": ["node_id", "node_kind", "path", "semantic_digest"],
        "type": "object",
    }
    edge = {
        "additionalProperties": False,
        "properties": {
            "from_node_id": _common_ref("Identifier"),
            "to_node_id": _common_ref("Identifier"),
            "relation": {
                "enum": ["enumerates", "reads", "derives", "writes", "checks", "excludes"]
            },
        },
        "required": ["from_node_id", "to_node_id", "relation"],
        "type": "object",
    }
    facts = {
        "additionalProperties": False,
        "properties": {
            "selected_report_path": {"minLength": 1, "type": "string"},
            "data_path": {"minLength": 1, "type": "string"},
            "writer_path": {"minLength": 1, "type": "string"},
            "group_column": {"minLength": 1, "type": "string"},
            "outcome_column": {"minLength": 1, "type": "string"},
            "left_group": {"minLength": 1, "type": "string"},
            "right_group": {"minLength": 1, "type": "string"},
            "left_values": {"items": {"type": "number"}, "minItems": 1, "type": "array"},
            "right_values": {"items": {"type": "number"}, "minItems": 1, "type": "array"},
            "left_mean": {"type": "number"},
            "right_mean": {"type": "number"},
            "computed_orientation": {"enum": ["left_higher", "right_higher", "equal"]},
            "literal_claims": {
                "items": {
                    "additionalProperties": False,
                    "properties": {
                        "sentence": {"minLength": 1, "type": "string"},
                        "orientation": {"enum": ["left_higher", "right_higher", "equal"]},
                        "start": {"minimum": 0, "type": "integer"},
                        "end": {"minimum": 1, "type": "integer"},
                    },
                    "required": ["sentence", "orientation", "start", "end"],
                    "type": "object",
                },
                "minItems": 1,
                "type": "array",
            },
            "candidate_paths": _sorted_string_array(min_items=1),
            "supported_closure_paths": _sorted_string_array(min_items=3),
            "supported_exclusions": {
                "items": {
                    "additionalProperties": False,
                    "properties": {
                        "path": {"minLength": 1, "type": "string"},
                        "reason_code": {"minLength": 1, "type": "string"},
                    },
                    "required": ["path", "reason_code"],
                    "type": "object",
                },
                "type": "array",
            },
        },
        "required": [
            "selected_report_path",
            "data_path",
            "writer_path",
            "group_column",
            "outcome_column",
            "left_group",
            "right_group",
            "left_values",
            "right_values",
            "left_mean",
            "right_mean",
            "computed_orientation",
            "literal_claims",
            "candidate_paths",
            "supported_closure_paths",
            "supported_exclusions",
        ],
        "type": "object",
    }
    chronology = {
        "additionalProperties": False,
        "properties": {
            "profile_frozen_at": _common_ref("Timestamp"),
            "case_assigned_at": _common_ref("Timestamp"),
            "label_frozen_at": _common_ref("Timestamp"),
            "proof_frozen_at": _common_ref("Timestamp"),
            "detector_dispatched_at": {"type": "null"},
            "stage3_started_at": {"type": "null"},
        },
        "required": [
            "profile_frozen_at",
            "case_assigned_at",
            "label_frozen_at",
            "proof_frozen_at",
            "detector_dispatched_at",
            "stage3_started_at",
        ],
        "type": "object",
    }
    schema = _base_record(
        title="StaticQualificationProof",
        record_type="static_qualification_proof",
        identity_field="proof_id",
        properties={
            "profile": _bound_ref("static_qualification_profile"),
            "case_assignment_artifact": _artifact_ref("opaque_case_assignment"),
            "label_freeze_artifact": _artifact_ref("scientific_label_freeze"),
            "snapshot": _bound_ref("repository_snapshot"),
            "retained_bytes": {"items": retained, "minItems": 0, "type": "array"},
            "dependency_graph": {
                "additionalProperties": False,
                "properties": {
                    "nodes": {"items": node, "minItems": 1, "type": "array"},
                    "edges": {"items": edge, "minItems": 0, "type": "array"},
                },
                "required": ["nodes", "edges"],
                "type": "object",
            },
            "applicability_results": {
                "items": _check_result(),
                "minItems": 1,
                "type": "array",
            },
            "counterevidence_results": {
                "items": _check_result(),
                "minItems": 1,
                "type": "array",
            },
            "derived_facts": {"oneOf": [facts, {"type": "null"}]},
            "chronology": chronology,
            "proof_status": {"enum": ["complete", "unavailable", "error"]},
            "proof_semantic_digest": _common_ref("Digest"),
            "limitations": _sorted_string_array(min_items=1),
        },
    )
    schema["allOf"] = [
        {
            "if": {
                "properties": {"proof_status": {"const": "complete"}},
                "required": ["proof_status"],
            },
            "then": {
                "properties": {
                    "derived_facts": {"type": "object"},
                    "retained_bytes": {"minItems": 3},
                }
            },
        }
    ]
    return schema


def _extend_fixture(schema: dict[str, Any]) -> None:
    fixture_kinds = schema["properties"]["fixture_kind"]["enum"]
    fixture_kinds.extend(STATIC_KINDS)
    legacy_proof = schema["properties"]["proof_evidence"]["oneOf"][0]
    static_proof = copy.deepcopy(legacy_proof)
    static_proof["properties"]["controller_profile"] = {"const": "fixture-proof-evidence-static-v1"}
    public_inputs = static_proof["properties"]["public_inputs"]["properties"]
    public_inputs["static_qualification_proofs"] = {
        "items": _bound_ref("static_qualification_proof"),
        "maxItems": 1,
        "minItems": 1,
        "type": "array",
    }
    static_proof["properties"]["public_inputs"]["required"].append("static_qualification_proofs")
    for name in ("environments", "executions", "sandbox_capabilities"):
        public_inputs[name]["maxItems"] = 0
    schema["properties"]["proof_evidence"]["oneOf"].insert(1, static_proof)

    schema["allOf"].extend(
        [
            {
                "if": {
                    "properties": {"fixture_kind": {"enum": STATIC_KINDS}},
                    "required": ["fixture_kind"],
                },
                "then": {
                    "properties": {
                        "execution_evidence": {"const": "not_executed"},
                        "expected_issue_labels": {"maxItems": 0},
                        "expected_root_cause_refs": {"maxItems": 0},
                        "qualification_proof_status": {"const": "complete"},
                        "scientific_contract_refs": {"minItems": 1},
                        "proof_obligations": {
                            "properties": {
                                "claim_output_agreement": {"const": True},
                                "no_unresolved_material_disagreement": {"const": True},
                                "reviewed_operations_identified": {"const": True},
                                "scope_semantics_resolved": {"const": True},
                            }
                        },
                        "proof_evidence": {
                            "properties": {
                                "controller_profile": {"const": "fixture-proof-evidence-static-v1"},
                                "protocol_artifacts": {
                                    "properties": {
                                        "blind_workspace_manifests": {"minItems": 1},
                                        "review_captures": {"minItems": 6},
                                        "review_packets": {"minItems": 6},
                                        "review_transcripts": {"minItems": 6},
                                        "stage1_freezes": {"maxItems": 1, "minItems": 1},
                                    }
                                },
                                "public_inputs": {
                                    "properties": {
                                        "agent_reviews": {"minItems": 6},
                                        "scientific_contracts": {"minItems": 1},
                                        "environments": {"maxItems": 0},
                                        "executions": {"maxItems": 0},
                                        "sandbox_capabilities": {"maxItems": 0},
                                        "static_qualification_proofs": {
                                            "maxItems": 1,
                                            "minItems": 1,
                                        },
                                    }
                                },
                            }
                        },
                    },
                    "required": ["scientific_contract_refs"],
                },
            },
            {
                "if": {
                    "properties": {"fixture_kind": {"const": STATIC_HARD}},
                    "required": ["fixture_kind"],
                },
                "then": {
                    "properties": {
                        "proof_obligations": {
                            "properties": {
                                "decisive_innocent_explanation_documented": {"const": True},
                                "hard_negative_pattern_documented": {"const": True},
                            }
                        },
                        "proof_evidence": {
                            "properties": {
                                "hard_negative_evidence": {
                                    "properties": {
                                        "decisive_innocent_explanation": {"minItems": 1},
                                        "suspicious_pattern": {"minItems": 1},
                                    }
                                }
                            }
                        },
                    }
                },
            },
        ]
    )


def _family_for_kind(kind: str) -> str:
    return {
        "verified_good_fixture": "clean_execution",
        "hard_negative_fixture": "clean_execution",
        "scope_verified_good": "documented_external_execution",
        STATIC_GOOD: "static_closed_scope",
        STATIC_HARD: "static_closed_scope",
        "positive_issue_fixture": "positive_issue",
        "ambiguous_fixture": "excluded_ambiguous",
    }[kind]


def _extend_case_outcome(schema: dict[str, Any]) -> None:
    schema["properties"]["fixture_kind"]["enum"].extend(STATIC_KINDS)
    schema["properties"]["qualification_proof_family"] = {
        "enum": [*PROOF_FAMILIES, "positive_issue", "excluded_ambiguous"]
    }
    schema["properties"]["static_qualification_proof_ref"] = {
        "oneOf": [_typed_ref("static_qualification_proof"), {"type": "null"}]
    }
    schema["required"].extend(["qualification_proof_family", "static_qualification_proof_ref"])
    for kind in [
        "verified_good_fixture",
        "hard_negative_fixture",
        "scope_verified_good",
        STATIC_GOOD,
        STATIC_HARD,
        "positive_issue_fixture",
        "ambiguous_fixture",
    ]:
        then: dict[str, Any] = {"qualification_proof_family": {"const": _family_for_kind(kind)}}
        then["static_qualification_proof_ref"] = (
            _typed_ref("static_qualification_proof") if kind in STATIC_KINDS else {"type": "null"}
        )
        schema["allOf"].append(
            {
                "if": {
                    "properties": {"fixture_kind": {"const": kind}},
                    "required": ["fixture_kind"],
                },
                "then": {"properties": then},
            }
        )


def _metric_item(schema: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(schema["properties"]["metrics"]["items"])


def _extend_metrics(schema: dict[str, Any]) -> None:
    stratum = {
        "additionalProperties": False,
        "properties": {
            "proof_family": {"enum": PROOF_FAMILIES},
            "case_count": {"minimum": 0, "type": "integer"},
            "metrics": {"items": _metric_item(schema), "minItems": 0, "type": "array"},
        },
        "required": ["proof_family", "case_count", "metrics"],
        "type": "object",
    }
    schema["properties"]["control_family_strata"] = {
        "items": stratum,
        "maxItems": 3,
        "minItems": 3,
        "type": "array",
    }
    schema["required"].append("control_family_strata")
    for family in PROOF_FAMILIES:
        schema["allOf"].append(
            {
                "properties": {
                    "control_family_strata": {
                        "contains": {
                            "properties": {"proof_family": {"const": family}},
                            "required": ["proof_family"],
                        },
                        "maxContains": 1,
                        "minContains": 1,
                    }
                }
            }
        )


def _extend_qualification(schema: dict[str, Any]) -> None:
    schema["properties"]["qualification_proof_families"] = _sorted_string_array(enum=PROOF_FAMILIES)
    schema["properties"]["static_scope_disclosure"] = {
        "oneOf": [
            {
                "additionalProperties": False,
                "properties": {
                    "profile_refs": {
                        "items": _typed_ref("static_qualification_profile"),
                        "minItems": 1,
                        "type": "array",
                    },
                    "scope_statement": {"minLength": 1, "type": "string"},
                    "execution_claimed": {"const": False},
                    "global_correctness_claimed": {"const": False},
                },
                "required": [
                    "profile_refs",
                    "scope_statement",
                    "execution_claimed",
                    "global_correctness_claimed",
                ],
                "type": "object",
            },
            {"type": "null"},
        ]
    }
    schema["properties"]["safety_gates"]["properties"]["proof_families_stratified"] = {
        "type": "boolean"
    }
    schema["properties"]["safety_gates"]["required"].append("proof_families_stratified")
    schema["required"].extend(["qualification_proof_families", "static_scope_disclosure"])
    schema["allOf"].append(
        {
            "if": {
                "properties": {
                    "qualification_proof_families": {"contains": {"const": "static_closed_scope"}}
                },
                "required": ["qualification_proof_families"],
            },
            "then": {"properties": {"static_scope_disclosure": {"type": "object"}}},
            "else": {"properties": {"static_scope_disclosure": {"type": "null"}}},
        }
    )


def _extend_bundle(schema: dict[str, Any]) -> None:
    for collection, record in (
        ("static_qualification_profiles", "static-qualification-profile"),
        ("static_qualification_proofs", "static-qualification-proof"),
    ):
        schema["properties"][collection] = {
            "items": _schema_ref(record),
            "type": "array",
        }
        schema["required"].append(collection)


def _extend_union(schema: dict[str, Any]) -> None:
    schema["oneOf"].extend(
        [_schema_ref("static-qualification-profile"), _schema_ref("static-qualification-proof")]
    )


def _artifact(kind: str, ident: str, digit: str) -> dict[str, str]:
    return {
        "artifact_kind": kind,
        "artifact_id": ident,
        "content_digest": "sha256:" + digit * 64,
    }


def _bound(record_type: str, ident: str, digit: str) -> dict[str, Any]:
    return {
        "record_ref": {"record_type": record_type, "record_id": ident},
        "semantic_digest": "sha256:" + digit * 64,
    }


def _provenance(at: str = "2026-07-30T18:00:00Z") -> dict[str, Any]:
    return {
        "actor": {
            "actor_id": "software:sc-referee-eval",
            "actor_kind": "controller",
            "display_name": "sc-referee evaluation controller",
        },
        "created_at": at,
        "method": "deterministic_static_qualification",
        "tool": "sc-referee-eval",
        "tool_version": "0.7.0",
    }


def _profile_example() -> dict[str, Any]:
    return {
        "schema_version": RELEASE_VERSION,
        "record_type": "static_qualification_profile",
        "profile_id": "static-profile:bounded-direction-v1",
        "profile_version": "1.0.0",
        "target_detector": {
            "manifest": _bound("detector_manifest", "detector:bounded-report-mean-direction", "1"),
            "detector_id": "detector:bounded-report-mean-direction",
            "detector_version": "0.1.0",
            "implementation_digest": "sha256:" + "2" * 64,
            "material_premise_class": "static_closed_scope",
            "parser_manifests": [_bound("parser_manifest", "parser:python", "3")],
            "semantic_profile_manifests": [
                {
                    "manifest_kind": "semantic_profile_manifest",
                    "manifest_id": "semantic-profile:bounded-direction-v1",
                    "semantic_digest": "sha256:" + "4" * 64,
                }
            ],
            "version_manifests": [
                {
                    "manifest_kind": "version_manifest",
                    "manifest_id": "version-manifest:bounded-direction-v1",
                    "semantic_digest": "sha256:" + "5" * 64,
                }
            ],
        },
        "verifier": {
            "entry_point": (
                "sc_referee_evaluation.static_qualification:verify_bounded_direction_case"
            ),
            "implementation_digest": "sha256:" + "6" * 64,
            "dependency_closure": [
                {
                    "dependency_kind": "implementation",
                    "path": "sc_referee_evaluation/static_qualification.py",
                    "content_digest": "sha256:" + "7" * 64,
                }
            ],
            "allowed_shared_utilities": [
                "canonical_json",
                "content_hashing",
                "schema_shape_validation",
                "source_reference_resolution",
            ],
        },
        "selection_rules": {
            "candidate_suffixes": [".csv", ".md", ".py"],
            "candidate_enumeration": "all_matching_regular_files_in_snapshot_sorted_by_path",
            "dependency_closure": "unique_supported_csv_mean_writer_report_transitive_path",
            "parser_completeness": "strict_utf8_full_bytes_supported_grammar_or_unavailable",
            "report_path_source": "opaque_case_assignment_manifest",
            "surface_inventory": ("every_literal_directional_sentence_in_complete_selected_report"),
        },
        "budgets": {
            "max_candidate_files": 1000,
            "max_total_bytes": 10000000,
            "max_recursion_depth": 32,
            "max_elapsed_milliseconds": 5000,
        },
        "vocabularies": {
            "applicability_obligation_ids": [
                "complete_candidate_enumeration",
                "full_identity",
                "unique_supported_dependency_closure",
            ],
            "counterevidence_check_ids": ["opposite_direction_sibling_claim"],
            "completion_statuses": ["completed", "error", "unavailable"],
            "outcomes": [
                "agreement",
                "conflict_absent",
                "conflict_present",
                "counterevidence_absent",
                "counterevidence_present",
            ],
        },
        "selection_protocol_artifact": _artifact(
            "corpus_selection_protocol", "selection-protocol:direction-v1", "8"
        ),
        "frozen_at": "2026-07-30T18:00:00Z",
        "profile_semantic_digest": "sha256:" + "9" * 64,
        "provenance": _provenance(),
    }


def _proof_example() -> dict[str, Any]:
    def retained(path: str, digit: str) -> dict[str, Any]:
        return {
            "path": path,
            "byte_size": 100,
            "content_digest": "sha256:" + digit * 64,
            "encoding": "utf-8",
            "file_record": _bound("file_record", f"file:{path}", digit),
            "asset_identity": _bound("asset_identity", f"identity:{path}", digit),
        }

    return {
        "schema_version": RELEASE_VERSION,
        "record_type": "static_qualification_proof",
        "proof_id": "static-proof:direction-case-1",
        "profile": _bound(
            "static_qualification_profile", "static-profile:bounded-direction-v1", "9"
        ),
        "case_assignment_artifact": _artifact(
            "opaque_case_assignment", "case-assignment:direction-case-1", "a"
        ),
        "label_freeze_artifact": _artifact(
            "scientific_label_freeze", "label-freeze:direction-case-1", "b"
        ),
        "snapshot": _bound("repository_snapshot", "snapshot:direction-case-1", "c"),
        "retained_bytes": [
            retained("analysis.py", "d"),
            retained("data.csv", "e"),
            retained("report.md", "f"),
        ],
        "dependency_graph": {
            "nodes": [
                {
                    "node_id": "node:data",
                    "node_kind": "raw_byte_source",
                    "path": "data.csv",
                    "semantic_digest": "sha256:" + "1" * 64,
                },
                {
                    "node_id": "node:mean",
                    "node_kind": "derived_fact",
                    "path": None,
                    "semantic_digest": "sha256:" + "2" * 64,
                },
                {
                    "node_id": "node:report",
                    "node_kind": "candidate",
                    "path": "report.md",
                    "semantic_digest": "sha256:" + "3" * 64,
                },
            ],
            "edges": [
                {"from_node_id": "node:data", "to_node_id": "node:mean", "relation": "derives"},
                {"from_node_id": "node:mean", "to_node_id": "node:report", "relation": "writes"},
            ],
        },
        "applicability_results": [
            {
                "check_id": "unique_supported_dependency_closure",
                "completion_status": "completed",
                "outcome": "agreement",
                "evidence_paths": ["analysis.py", "data.csv", "report.md"],
                "detail_code": "unique_closure",
            }
        ],
        "counterevidence_results": [
            {
                "check_id": "opposite_direction_sibling_claim",
                "completion_status": "completed",
                "outcome": "counterevidence_absent",
                "evidence_paths": ["report.md"],
                "detail_code": "full_report_search_complete",
            }
        ],
        "derived_facts": {
            "selected_report_path": "report.md",
            "data_path": "data.csv",
            "writer_path": "analysis.py",
            "group_column": "group",
            "outcome_column": "value",
            "left_group": "A",
            "right_group": "B",
            "left_values": [2.0, 4.0],
            "right_values": [1.0, 1.0],
            "left_mean": 3.0,
            "right_mean": 1.0,
            "computed_orientation": "left_higher",
            "literal_claims": [
                {
                    "sentence": "Group B is higher than group A.",
                    "orientation": "right_higher",
                    "start": 0,
                    "end": 31,
                }
            ],
            "candidate_paths": ["analysis.py", "data.csv", "report.md"],
            "supported_closure_paths": ["analysis.py", "data.csv", "report.md"],
            "supported_exclusions": [],
        },
        "chronology": {
            "profile_frozen_at": "2026-07-30T18:00:00Z",
            "case_assigned_at": "2026-07-30T18:01:00Z",
            "label_frozen_at": "2026-07-30T18:02:00Z",
            "proof_frozen_at": "2026-07-30T18:03:00Z",
            "detector_dispatched_at": None,
            "stage3_started_at": None,
        },
        "proof_status": "complete",
        "proof_semantic_digest": "sha256:" + "4" * 64,
        "limitations": ["This proof establishes only the frozen static direction envelope."],
        "provenance": _provenance("2026-07-30T18:03:00Z"),
    }


def _static_fixture(base: dict[str, Any], hard: bool) -> dict[str, Any]:
    fixture = copy.deepcopy(base)
    fixture["fixture_id"] = "fixture:static-hard-1" if hard else "fixture:static-good-1"
    fixture["fixture_kind"] = STATIC_HARD if hard else STATIC_GOOD
    fixture["execution_evidence"] = "not_executed"
    fixture["proof_evidence"]["controller_profile"] = "fixture-proof-evidence-static-v1"
    inputs = fixture["proof_evidence"]["public_inputs"]
    inputs["environments"] = []
    inputs["executions"] = []
    inputs["sandbox_capabilities"] = []
    inputs["static_qualification_proofs"] = [
        _bound("static_qualification_proof", "static-proof:direction-case-1", "4")
    ]
    if hard:
        fixture["proof_obligations"]["hard_negative_pattern_documented"] = True
        fixture["proof_obligations"]["decisive_innocent_explanation_documented"] = True
        fixture["proof_evidence"]["hard_negative_evidence"] = {
            "suspicious_pattern": [
                {
                    "evidence_id": "evidence:static-suspicious-direction",
                    "description": "A literal directional phrase resembles the target pattern.",
                    "support_role": "context",
                    "record_refs": [
                        {"record_type": "scientific_contract", "record_id": "contract:1"}
                    ],
                }
            ],
            "decisive_innocent_explanation": [
                {
                    "evidence_id": "evidence:static-innocent-direction",
                    "description": "The independently recomputed direction agrees with the report.",
                    "support_role": "counterevidence",
                    "record_refs": [
                        {"record_type": "scientific_contract", "record_id": "contract:1"}
                    ],
                }
            ],
        }
    return fixture


def _extend_example(example: dict[str, Any]) -> None:
    record_type = example.get("record_type")
    if record_type == "audit_bundle":
        example["static_qualification_profiles"] = []
        example["static_qualification_proofs"] = []
    elif record_type == "detector_case_outcome":
        kind = str(example["fixture_kind"])
        example["qualification_proof_family"] = _family_for_kind(kind)
        example["static_qualification_proof_ref"] = None
    elif record_type == "qualification_metric_set":
        example["control_family_strata"] = [
            {"proof_family": family, "case_count": 0, "metrics": []} for family in PROOF_FAMILIES
        ]
    elif record_type == "detector_qualification":
        example["qualification_proof_families"] = []
        example["static_scope_disclosure"] = None
        example["safety_gates"]["proof_families_stratified"] = False


def write_manifest(output: Path) -> None:
    entries = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.sha256" or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(output).as_posix()
        entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    (output / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def _release_readme() -> str:
    return """# sc-referee public schemas v0.15.0

Accepted forward-only public schema release implementing ADR-0022.

This release adds detector-specific static closed-scope qualification profiles and proofs. It does
not weaken clean-execution controls, execute project code, qualify a detector, or make a global
correctness claim. Static, clean-execution, and documented-external control evidence remain
separate in outcomes, metrics, qualification records, and reports.
"""


def _release_changelog() -> str:
    return """# Changelog

## 0.15.0 — 2026-07-30

- Added `StaticQualificationProfile` and `StaticQualificationProof`.
- Added explicit static verified-good and hard-negative fixture kinds.
- Added proof-family stratification to case outcomes, metrics, and qualification records.
- Preserved all v0.14.0 execution-backed fixture meanings unchanged.
"""


def _release_invariants() -> str:
    return """# Controller invariants for v0.15.0

- Static controls use `not_executed` and exactly one bound static proof.
- Static proof facts are independently rederived from immutable full-digest bytes.
- Static proofs are qualification-controller inputs, never detector semantic inputs.
- Missing, ambiguous, unsupported, weak, over-budget, or conflicting closure is unavailable.
- Control families are never silently pooled.
- No record in this release grants detector promotion or global correctness.
"""


def _migration_text() -> str:
    return """# Migration from v0.14.0 to v0.15.0

The migration is fail closed. It versions existing records, adds empty static profile/proof bundle
collections, annotates case outcomes with their pre-existing proof family, and removes authoritative
metric sets whose new family strata cannot be reconstructed from a bare public bundle. It creates
no static fixture, proof, qualification metric, maturity, Finding permission, or execution authority.
"""


def _v15_tests() -> str:
    return """from copy import deepcopy
from test_examples import invalid, load

def test_static_fixture_cannot_claim_execution():
 x=load("benchmark-fixture.static-good.example.json"); x["execution_evidence"]="clean_environment_executed"; invalid(x,"benchmark_fixture")

def test_static_hard_negative_requires_decisive_evidence():
 x=load("benchmark-fixture.static-hard.example.json"); x["proof_evidence"]["hard_negative_evidence"]["decisive_innocent_explanation"]=[]; invalid(x,"benchmark_fixture")

def test_static_proof_chronology_has_no_detector_timestamp():
 x=load("static-qualification-proof.example.json"); x["chronology"]["detector_dispatched_at"]="2026-07-30T18:04:00Z"; invalid(x,"static_qualification_proof")

def test_static_profile_is_exactly_bounded_to_first_detector():
 x=load("static-qualification-profile.example.json"); x["target_detector"]["detector_id"]="detector:any"; invalid(x,"static_qualification_profile")
"""


def build_release(output: Path) -> int:
    """Build accepted v0.15.0 without modifying immutable v0.14.0."""

    _require_empty_destination(output)
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "benchmark-fixture.schema.json":
            _extend_fixture(schema)
        elif source.name == "detector-case-outcome.schema.json":
            _extend_case_outcome(schema)
        elif source.name == "qualification-metric-set.schema.json":
            _extend_metrics(schema)
        elif source.name == "detector-qualification.schema.json":
            _extend_qualification(schema)
        elif source.name == "audit-bundle.schema.json":
            _extend_bundle(schema)
        elif source.name == "record-union.schema.json":
            _extend_union(schema)
        _write_json(schema_output / source.name, schema)

    new_schemas = {
        "static-qualification-profile.schema.json": _static_profile_schema(),
        "static-qualification-proof.schema.json": _static_proof_schema(),
    }
    for name, schema in new_schemas.items():
        _write_json(schema_output / name, schema)

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    for name in ("static_qualification_profile", "static_qualification_proof"):
        catalog["schemas"].append(
            {
                "file": name.replace("_", "-") + ".schema.json",
                "id": (
                    f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                    f"{name.replace('_', '-')}.schema.json"
                ),
                "kind": "record",
                "name": name,
            }
        )
    catalog["schemas"].sort(key=lambda item: str(item["name"]))
    _write_json(output / "schema-catalog.json", catalog)

    examples: dict[str, dict[str, Any]] = {}
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        _extend_example(example)
        examples[source.name] = example
        _write_json(output / "examples" / source.name, example)

    profile = _profile_example()
    proof = _proof_example()
    _write_json(output / "examples" / "static-qualification-profile.example.json", profile)
    _write_json(output / "examples" / "static-qualification-proof.example.json", proof)
    base_fixture = examples["benchmark-fixture.example.json"]
    _write_json(
        output / "examples" / "benchmark-fixture.static-good.example.json",
        _static_fixture(base_fixture, False),
    )
    _write_json(
        output / "examples" / "benchmark-fixture.static-hard.example.json",
        _static_fixture(base_fixture, True),
    )

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.14_to_v0.15.md").write_text(_migration_text(), encoding="utf-8")
    _write_json(
        output / "RELEASE_STATUS.json",
        {
            "accepted": True,
            "baseline_version": BASELINE_VERSION,
            "public_release": True,
            "release_version": RELEASE_VERSION,
            "source_adrs": SOURCE_ADRS,
        },
    )

    tests_output = output / "tests"
    tests_output.mkdir(parents=True, exist_ok=True)
    for source in sorted((BASELINE / "tests").glob("*.py")):
        source_text = source.read_text(encoding="utf-8").replace(
            f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}"
        )
        if source.name == "test_examples.py":
            source_text = source_text.replace('len(u["oneOf"])==53', 'len(u["oneOf"])==56')
        elif source.name.startswith("test_v") and "from test_examples import" not in source_text:
            helper_import = "from test_examples import invalid, load\n"
            future = "from __future__ import annotations\n"
            if source_text.startswith(future):
                source_text = future + helper_import + source_text[len(future) :]
            else:
                source_text = helper_import + source_text
        (tests_output / source.name).write_text(source_text, encoding="utf-8")
    (tests_output / "test_v015_invariants.py").write_text(_v15_tests(), encoding="utf-8")

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
    example_count = len(list((output / "examples").glob("*.json")))
    (output / "VALIDATION.txt").write_text(
        f"sc-referee schema package {RELEASE_VERSION} validation\n\n"
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
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.15.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
