from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.18.0"
BASELINE_VERSION = "0.18.0"
CANDIDATE_VERSION = "0.19.0"
METHOD_DETECTOR = "detector:bounded-analysis-method-conflict"
METHOD_V1 = "typed_static_method_conflict_v1"
METHOD_V2 = "typed_static_method_conflict_v2"
SOURCE_ADR = "docs/implementation/ADR-0061-PER-BINDING-METHOD-CONFLICT-PROMOTION-PATH.md"

METRIC_NAMES = [
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


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected one JSON object in {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _semantic_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _replace_version(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(f"v{BASELINE_VERSION}", f"v{CANDIDATE_VERSION}").replace(
            BASELINE_VERSION, CANDIDATE_VERSION
        )
    if isinstance(value, list):
        return [_replace_version(item) for item in value]
    if isinstance(value, dict):
        return {key: _replace_version(item) for key, item in value.items()}
    return value


def _require_empty_destination(output: Path) -> None:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Candidate output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)


def _common_ref(name: str) -> dict[str, str]:
    return {
        "$ref": (
            f"https://w3id.org/sc-referee/schema/v{CANDIDATE_VERSION}/"
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


def _qualification_adapter_identity() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "adapter_id": {"pattern": "^qualification-adapter:", "type": "string"},
            "adapter_version": {"minLength": 1, "type": "string"},
            "implementation_digest": _common_ref("Digest"),
        },
        "required": ["adapter_id", "adapter_version", "implementation_digest"],
        "type": "object",
    }


def _binding_scope() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "scope_kind": {"const": "method_conflict_binding_v1"},
            "binding_id": _common_ref("Identifier"),
            "production_binding_digest": _common_ref("Digest"),
            "check_id": _common_ref("Identifier"),
            "check_version": {"minLength": 1, "type": "string"},
            "check_manifest_digest": _common_ref("Digest"),
            "detector_id": {"const": METHOD_DETECTOR},
            "detector_version": {"const": "0.3.0"},
            "detector_manifest_digest": _common_ref("Digest"),
            "static_qualification_profile_ref": _typed_ref("static_qualification_profile"),
            "static_qualification_profile_digest": _common_ref("Digest"),
            "qualification_adapter": _qualification_adapter_identity(),
        },
        "required": [
            "scope_kind",
            "binding_id",
            "production_binding_digest",
            "check_id",
            "check_version",
            "check_manifest_digest",
            "detector_id",
            "detector_version",
            "detector_manifest_digest",
            "static_qualification_profile_ref",
            "static_qualification_profile_digest",
            "qualification_adapter",
        ],
        "type": "object",
    }


def _threshold_policy() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "policy_kind": {"const": "pilot_informed_binding_thresholds_v1"},
            "policy_id": _common_ref("Identifier"),
            "policy_version": _common_ref("SemVer"),
            "policy_semantic_digest": _common_ref("Digest"),
            "decision_adr_ref": {
                "pattern": "^docs/implementation/ADR-[0-9]{4}-[A-Z0-9-]+[.]md$",
                "type": "string",
            },
            "pilot_evidence_refs": {
                "items": {"minLength": 1, "type": "string"},
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "frozen_at": _common_ref("Timestamp"),
            "held_out_labels_observed_before_freeze": {"const": False},
            "minimum_counts": {
                "additionalProperties": False,
                "properties": {
                    "workflows": {"minimum": 1, "type": "integer"},
                    "problem_clusters": {"minimum": 2, "type": "integer"},
                    "adjudicated_roots": {"minimum": 1, "type": "integer"},
                    "control_cases": {"minimum": 1, "type": "integer"},
                },
                "required": [
                    "workflows",
                    "problem_clusters",
                    "adjudicated_roots",
                    "control_cases",
                ],
                "type": "object",
            },
            "require_estimable_intervals": {"type": "boolean"},
            "metric_requirements": {
                "items": {
                    "additionalProperties": False,
                    "properties": {
                        "metric_name": {"enum": METRIC_NAMES},
                        "statistic": {"enum": ["estimate", "interval_lower", "interval_upper"]},
                        "operator": {"enum": ["at_most", "at_least"]},
                        "threshold": {"minimum": 0, "maximum": 1, "type": "number"},
                    },
                    "required": ["metric_name", "statistic", "operator", "threshold"],
                    "type": "object",
                },
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
        },
        "required": [
            "policy_kind",
            "policy_id",
            "policy_version",
            "policy_semantic_digest",
            "decision_adr_ref",
            "pilot_evidence_refs",
            "frozen_at",
            "held_out_labels_observed_before_freeze",
            "minimum_counts",
            "require_estimable_intervals",
            "metric_requirements",
        ],
        "type": "object",
    }


def _threshold_policy_choice() -> dict[str, Any]:
    return {
        "oneOf": [
            {"const": "deferred_until_pilot_threshold_adr"},
            _threshold_policy(),
        ]
    }


def _v03_method_binding(v02_binding: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(v02_binding)
    value["properties"]["detector_version"] = {"const": "0.3.0"}
    value["properties"]["production_binding_digest"] = _common_ref("Digest")
    value["required"].append("production_binding_digest")
    return value


def _extend_static_profile(schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    kinds = properties["profile_kind"]["enum"]
    kinds.append(METHOD_V2)
    versions = properties["target_detector"]["properties"]["detector_version"]["enum"]
    versions.append("0.3.0")
    v02_binding = properties["method_binding"]["oneOf"][0]
    v03_binding = _v03_method_binding(v02_binding)
    properties["method_binding"]["oneOf"].insert(1, copy.deepcopy(v03_binding))
    v1_branch = next(
        branch
        for branch in schema["allOf"]
        if branch.get("if", {}).get("properties", {}).get("profile_kind", {}).get("const")
        == METHOD_V1
    )
    v2_branch = copy.deepcopy(v1_branch)
    v2_branch["if"]["properties"]["profile_kind"]["const"] = METHOD_V2
    v2_branch["then"]["properties"]["method_binding"] = v03_binding
    v2_branch["then"]["properties"]["target_detector"]["properties"]["detector_version"] = {
        "const": "0.3.0"
    }
    schema["allOf"].append(v2_branch)


def _extend_static_proof(schema: dict[str, Any]) -> None:
    schema["properties"]["proof_profile_kind"]["enum"].append(METHOD_V2)
    v1_branch = next(
        branch
        for branch in schema["allOf"]
        if branch.get("if", {}).get("properties", {}).get("proof_profile_kind", {}).get("const")
        == METHOD_V1
    )
    v2_branch = copy.deepcopy(v1_branch)
    v2_branch["if"]["properties"]["proof_profile_kind"]["const"] = METHOD_V2
    schema["allOf"].append(v2_branch)


def _extend_metric_set(schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    properties["binding_scope"] = {"oneOf": [_binding_scope(), {"type": "null"}]}
    properties["numeric_threshold_policy"] = _threshold_policy_choice()
    properties["promotion_permitted"] = {"type": "boolean"}
    schema["required"].append("binding_scope")
    schema["allOf"].append(
        {
            "if": {
                "properties": {"promotion_permitted": {"const": True}},
                "required": ["promotion_permitted"],
            },
            "then": {
                "properties": {
                    "detector_id": {"const": METHOD_DETECTOR},
                    "detector_version": {"const": "0.3.0"},
                    "binding_scope": _binding_scope(),
                    "numeric_threshold_policy": _threshold_policy(),
                    "promotion_evidence_eligible": {"const": True},
                    "corpus_partitions": {"not": {"contains": {"const": "public_development"}}},
                    "excluded_case_outcomes": {"maxItems": 0},
                }
            },
        }
    )


def _extend_detector_qualification(schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    properties["binding_scope"] = {"oneOf": [_binding_scope(), {"type": "null"}]}
    properties["numeric_threshold_policy"] = _threshold_policy_choice()
    schema["required"].append("binding_scope")
    schema["allOf"].append(
        {
            "if": {
                "properties": {"outcome": {"const": "promoted"}},
                "required": ["outcome"],
            },
            "then": {
                "required": ["quantitative_metrics"],
                "properties": {
                    "detector_id": {"const": METHOD_DETECTOR},
                    "detector_version": {"const": "0.3.0"},
                    "binding_scope": _binding_scope(),
                    "numeric_threshold_policy": _threshold_policy(),
                    "qualification_proof_families": {"contains": {"const": "static_closed_scope"}},
                    "quantitative_metrics": {
                        "properties": {"metric_set_refs": {"minItems": 1, "maxItems": 1}},
                        "required": ["metric_profile", "metric_set_refs"],
                        "type": "object",
                    },
                    "static_scope_disclosure": {"type": "object"},
                },
            },
        }
    )


def _transform_example(name: str, value: dict[str, Any]) -> None:
    record_type = value.get("record_type")
    if record_type in {"qualification_metric_set", "detector_qualification"}:
        value["binding_scope"] = None
    if name == "static-qualification-profile.analysis-method.example.json":
        value["profile_kind"] = METHOD_V2
        value["profile_id"] = "static-profile:typed-static-method-conflict-v2"
        value["target_detector"]["detector_version"] = "0.3.0"
        binding = value["method_binding"]
        binding["detector_version"] = "0.3.0"
        binding["production_binding_digest"] = "sha256:" + "7" * 64
        digest_basis = {key: item for key, item in binding.items() if key != "binding_digest"}
        binding["binding_digest"] = _semantic_digest(digest_basis)
        value["profile_semantic_digest"] = "sha256:" + "8" * 64
    if name == "static-qualification-proof.analysis-method.example.json":
        value["proof_profile_kind"] = METHOD_V2
        value["profile"]["record_ref"]["record_id"] = (
            "static-profile:typed-static-method-conflict-v2"
        )


def build_candidate(output: Path) -> int:
    """Build the nonpublic v0.19 promotion representation without modifying v0.18."""

    _require_empty_destination(output)
    schema_output = output / "schemas" / f"v{CANDIDATE_VERSION}"
    for source in sorted((BASELINE / "schemas" / f"v{BASELINE_VERSION}").glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "static-qualification-profile.schema.json":
            _extend_static_profile(schema)
        elif source.name == "static-qualification-proof.schema.json":
            _extend_static_proof(schema)
        elif source.name == "qualification-metric-set.schema.json":
            _extend_metric_set(schema)
        elif source.name == "detector-qualification.schema.json":
            _extend_detector_qualification(schema)
        _write_json(schema_output / source.name, schema)

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = CANDIDATE_VERSION
    _write_json(output / "schema-catalog.json", catalog)

    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        _transform_example(source.name, example)
        _write_json(output / "examples" / source.name, example)

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(CANDIDATE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        "# sc-referee schema candidate v0.19.0\n\n"
        "Nonpublic review candidate for exact detector-v0.3 per-binding qualification and "
        "promotion records. It installs no qualification grant and grants no Finding authority.\n",
        encoding="utf-8",
    )
    (output / "MIGRATION_v0.18_to_v0.19.md").write_text(
        "# Candidate migration from v0.18.0 to v0.19.0\n\n"
        "Migration adds null binding scopes to historical qualification records and preserves the "
        "deferred threshold policy. It creates no threshold, qualification, maturity, or Finding "
        "authority. Storage manifests are cleared after canonical bytes change.\n",
        encoding="utf-8",
    )
    _write_json(
        output / "PROPOSAL_STATUS.json",
        {
            "accepted": False,
            "baseline_version": BASELINE_VERSION,
            "candidate_version": CANDIDATE_VERSION,
            "public_release": False,
            "source_adr": SOURCE_ADR,
            "warning": (
                "Representation candidate only. Pilot-informed thresholds, independent held-out "
                "qualification, maintainer promotion, and an accepted public schema are absent."
            ),
        },
    )
    return len(list((output / "examples").glob("*.json")))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build nonpublic method-promotion schema candidate"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_candidate(args.output.resolve())
    print(f"Built schema candidate {CANDIDATE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
