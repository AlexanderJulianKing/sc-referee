from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from sc_referee.records.root_cause import (
    root_cause_candidate_id,
    root_cause_candidate_payload,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.8.0"
PROPOSAL = ROOT / "schema-proposals" / "root-cause-reconciliation"
BASELINE_VERSION = "0.8.0"
RELEASE_VERSION = "0.9.0"
ADR_PATH = "docs/implementation/ADR-0008-CANONICAL-ROOT-CAUSE-RECONCILIATION.md"
ROOT_CAUSE_ID = "adjudicated-root-cause:case-1"


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
        return (
            value.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}")
            .replace(BASELINE_VERSION, RELEASE_VERSION)
            .replace("__SCHEMA_VERSION__", RELEASE_VERSION)
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


def _candidate_payload(review: dict[str, Any]) -> dict[str, Any]:
    return root_cause_candidate_payload(review)


def _candidate_id(review: dict[str, Any]) -> str:
    return root_cause_candidate_id(review)


def _extend_common(schema: dict[str, Any]) -> None:
    schema["$defs"]["RootCauseCandidateRef"] = {
        "additionalProperties": False,
        "properties": {
            "candidate_root_cause_id": {
                "$ref": (
                    f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                    "common.schema.json#/$defs/Identifier"
                )
            },
            "review_ref": {
                "additionalProperties": False,
                "properties": {
                    "record_id": {
                        "$ref": (
                            f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                            "common.schema.json#/$defs/Identifier"
                        )
                    },
                    "record_type": {"const": "agent_review"},
                },
                "required": ["record_type", "record_id"],
                "type": "object",
            },
        },
        "required": ["review_ref", "candidate_root_cause_id"],
        "type": "object",
    }


def _root_cause_identity_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "candidate_root_cause_id": {
                "$ref": (
                    f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                    "common.schema.json#/$defs/Identifier"
                )
            },
            "equivalence_evidence": {
                "items": {
                    "$ref": (
                        f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                        "common.schema.json#/$defs/EvidenceItem"
                    )
                },
                "minItems": 0,
                "type": "array",
            },
            "identity_profile": {"const": "review-local-root-cause-v1"},
            "reconciled_stage1_candidates": {
                "items": {
                    "$ref": (
                        f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                        "common.schema.json#/$defs/RootCauseCandidateRef"
                    )
                },
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
        },
        "required": [
            "candidate_root_cause_id",
            "identity_profile",
            "reconciled_stage1_candidates",
            "equivalence_evidence",
        ],
        "type": "object",
    }


def _condition(*, stage: str | None = None, verdicts: list[str] | None = None) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    if stage is not None:
        properties["stage"] = {"const": stage}
        required.append("stage")
    if verdicts is not None:
        properties["verdict"] = {"enum": verdicts}
        required.append("verdict")
    return {"properties": properties, "required": required}


def _extend_agent_review(schema: dict[str, Any]) -> None:
    schema.setdefault("$defs", {})["RootCauseIdentity"] = _root_cause_identity_schema()
    schema["properties"]["root_cause_identity"] = {
        "oneOf": [{"$ref": "#/$defs/RootCauseIdentity"}, {"type": "null"}]
    }
    schema["required"].append("root_cause_identity")
    schema["allOf"].extend(
        [
            {
                "if": _condition(verdicts=["demonstrated_issue"]),
                "then": {
                    "properties": {"root_cause_identity": {"$ref": "#/$defs/RootCauseIdentity"}}
                },
            },
            {
                "if": _condition(
                    verdicts=[
                        "no_demonstrated_issue_within_scope",
                        "conditional_or_unknown",
                        "insufficient_evidence",
                        "review_failure",
                    ]
                ),
                "then": {"properties": {"root_cause_identity": {"const": None}}},
            },
            {
                "if": _condition(stage="stage1_blind", verdicts=["demonstrated_issue"]),
                "then": {
                    "properties": {
                        "root_cause_identity": {
                            "properties": {
                                "equivalence_evidence": {"maxItems": 0},
                                "reconciled_stage1_candidates": {"maxItems": 0},
                            }
                        }
                    }
                },
            },
            {
                "if": _condition(
                    stage="stage2_scientific_adjudication",
                    verdicts=["demonstrated_issue"],
                ),
                "then": {
                    "properties": {
                        "root_cause_identity": {
                            "properties": {
                                "equivalence_evidence": {"minItems": 1},
                                "reconciled_stage1_candidates": {"minItems": 2},
                            }
                        }
                    }
                },
            },
        ]
    )


def _extend_benchmark_adjudication(schema: dict[str, Any]) -> None:
    schema["allOf"].pop(1)
    schema["properties"].pop("bounded_root_cause_statement")
    schema["properties"].pop("issue_class")
    schema["properties"]["adjudicated_root_cause_refs"] = {
        "items": {
            "additionalProperties": False,
            "properties": {
                "record_id": {
                    "$ref": (
                        f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                        "common.schema.json#/$defs/Identifier"
                    )
                },
                "record_type": {"const": "adjudicated_root_cause"},
            },
            "required": ["record_type", "record_id"],
            "type": "object",
        },
        "minItems": 0,
        "type": "array",
        "uniqueItems": True,
    }
    schema["properties"]["root_cause_reconciliation_status"] = {
        "enum": ["verified", "not_applicable", "unresolved"]
    }
    schema["required"].extend(["adjudicated_root_cause_refs", "root_cause_reconciliation_status"])
    schema["allOf"].extend(
        [
            {
                "if": {
                    "properties": {"label_status": {"const": "positive_demonstrated"}},
                    "required": ["label_status"],
                },
                "then": {
                    "properties": {
                        "adjudicated_root_cause_refs": {"minItems": 1},
                        "root_cause_reconciliation_status": {"const": "verified"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "label_status": {
                            "enum": ["verified_good_eligible", "hard_negative_eligible"]
                        }
                    },
                    "required": ["label_status"],
                },
                "then": {
                    "properties": {
                        "adjudicated_root_cause_refs": {"maxItems": 0},
                        "root_cause_reconciliation_status": {"const": "not_applicable"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "label_status": {
                            "enum": [
                                "ambiguous_excluded",
                                "insufficient_evidence",
                                "adjudication_failed",
                            ]
                        }
                    },
                    "required": ["label_status"],
                },
                "then": {
                    "properties": {
                        "adjudicated_root_cause_refs": {"maxItems": 0},
                        "root_cause_reconciliation_status": {
                            "enum": ["not_applicable", "unresolved"]
                        },
                    }
                },
            },
        ]
    )


def _extend_benchmark_fixture(schema: dict[str, Any]) -> None:
    schema["properties"]["expected_root_cause_refs"] = {
        "items": {
            "additionalProperties": False,
            "properties": {
                "record_id": {
                    "$ref": (
                        f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                        "common.schema.json#/$defs/Identifier"
                    )
                },
                "record_type": {"const": "adjudicated_root_cause"},
            },
            "required": ["record_type", "record_id"],
            "type": "object",
        },
        "minItems": 0,
        "type": "array",
        "uniqueItems": True,
    }
    schema["required"].append("expected_root_cause_refs")
    positive_rule = next(
        rule
        for rule in schema["allOf"]
        if rule.get("if", {}).get("properties", {}).get("fixture_kind", {}).get("const")
        == "positive_issue_fixture"
    )
    positive_rule["then"]["properties"]["expected_root_cause_refs"] = {"minItems": 1}
    schema["allOf"].append(
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
            "then": {"properties": {"expected_root_cause_refs": {"maxItems": 0}}},
        }
    )


def _extend_bundle(schema: dict[str, Any]) -> None:
    schema["properties"]["adjudicated_root_causes"] = {
        "items": {
            "$ref": (
                f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                "adjudicated-root-cause.schema.json"
            )
        },
        "minItems": 0,
        "type": "array",
    }
    schema["required"].append("adjudicated_root_causes")


def _extend_union(schema: dict[str, Any]) -> None:
    schema["oneOf"].append(
        {
            "$ref": (
                f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                "adjudicated-root-cause.schema.json"
            )
        }
    )


def _extend_catalog(catalog: dict[str, Any]) -> None:
    catalog["schemas"].append(
        {
            "name": "adjudicated_root_cause",
            "file": "adjudicated-root-cause.schema.json",
            "id": (
                f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                "adjudicated-root-cause.schema.json"
            ),
            "kind": "record",
        }
    )


def _candidate_ref(review_id: str, candidate_id: str) -> dict[str, Any]:
    return {
        "review_ref": {"record_type": "agent_review", "record_id": review_id},
        "candidate_root_cause_id": candidate_id,
    }


def _upgrade_example_records(value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            _upgrade_example_records(item)
        return
    if not isinstance(value, dict):
        return
    record_type = value.get("record_type")
    if record_type == "agent_review" and isinstance(value.get("review_id"), str):
        if value.get("verdict") == "demonstrated_issue":
            reconciled: list[dict[str, Any]] = []
            equivalence_evidence: list[dict[str, Any]] = []
            if value.get("stage") == "stage2_scientific_adjudication":
                reconciled = [
                    _candidate_ref("review:stage1:1", "root-cause-candidate:stage1-1"),
                    _candidate_ref("review:stage1:3", "root-cause-candidate:stage1-3"),
                ]
                equivalence_evidence = list(value.get("evidence", []))
            value["root_cause_identity"] = {
                "candidate_root_cause_id": _candidate_id(value),
                "identity_profile": "review-local-root-cause-v1",
                "reconciled_stage1_candidates": reconciled,
                "equivalence_evidence": equivalence_evidence,
            }
        else:
            value["root_cause_identity"] = None
    elif record_type == "benchmark_adjudication" and isinstance(value.get("adjudication_id"), str):
        value.pop("bounded_root_cause_statement", None)
        value.pop("issue_class", None)
        if value.get("label_status") == "positive_demonstrated":
            value["adjudicated_root_cause_refs"] = [
                {"record_type": "adjudicated_root_cause", "record_id": ROOT_CAUSE_ID}
            ]
            value["root_cause_reconciliation_status"] = "verified"
        else:
            value["adjudicated_root_cause_refs"] = []
            value["root_cause_reconciliation_status"] = "not_applicable"
    elif record_type == "benchmark_fixture" and isinstance(value.get("fixture_id"), str):
        value["expected_root_cause_refs"] = (
            [{"record_type": "adjudicated_root_cause", "record_id": ROOT_CAUSE_ID}]
            if value.get("fixture_kind") == "positive_issue_fixture"
            else []
        )
    elif record_type == "audit_bundle" and isinstance(value.get("bundle_id"), str):
        value["adjudicated_root_causes"] = []
    for item in value.values():
        _upgrade_example_records(item)


def _root_cause_example() -> dict[str, Any]:
    evidence = {
        "evidence_id": "evidence:sign",
        "description": "The linked coefficient is negative.",
        "support_role": "supports",
        "observed_value": -0.42,
        "record_refs": [{"record_type": "claim", "record_id": "claim:1"}],
        "source_refs": [],
    }
    return {
        "schema_version": RELEASE_VERSION,
        "record_type": "adjudicated_root_cause",
        "adjudicated_root_cause_id": ROOT_CAUSE_ID,
        "case_id": "case:gene-1",
        "identity_profile": "cross-review-candidate-set-v1",
        "stage1_candidate_refs": [
            _candidate_ref("review:stage1:1", "root-cause-candidate:stage1-1"),
            _candidate_ref("review:stage1:3", "root-cause-candidate:stage1-3"),
        ],
        "stage2_review_refs": [
            {"record_type": "agent_review", "record_id": "review:stage2:1"},
            {"record_type": "agent_review", "record_id": "review:stage2:2"},
        ],
        "statement_source_review_ref": {
            "record_type": "agent_review",
            "record_id": "review:stage2:1",
        },
        "bounded_statement": (
            "The report states a positive coefficient while the linked result is negative under "
            "the established contrast orientation."
        ),
        "issue_class": "claim_result_agreement",
        "evidence": [evidence],
        "affected_record_refs": [{"record_type": "claim", "record_id": "claim:1"}],
        "required_scientific_premises": [
            "The report and result use the same contrast orientation."
        ],
        "stronger_claims_excluded": ["No global workflow correctness claim is established."],
        "material_dissent": False,
        "confidence_used_for_identity": False,
        "adjudicated_at": "2026-07-27T19:00:00Z",
        "provenance": {
            "actor": {
                "actor_kind": "controller",
                "actor_id": "software:sc-referee-eval",
                "display_name": "sc-referee evaluation controller",
            },
            "method": "deterministic_root_cause_reconciliation",
            "created_at": "2026-07-27T19:00:00Z",
            "tool": "sc-referee-eval",
            "tool_version": "0.5.0",
        },
    }


def _release_readme() -> str:
    return """# sc-referee schema package

**Version:** 0.9.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.9.0/`.

Version 0.9.0 implements accepted ADR-0008. Blind Stage-1 AgentReviews receive only review-local
root-cause candidate identities. Fresh Stage-2 reviewers independently reconcile exact frozen
candidate sets. A public AdjudicatedRootCause exists only after cross-provider membership,
evidence, falsification, chronology, and dissent gates pass.

Prose similarity, embeddings, confidence, and majority vote cannot establish root-cause identity.
The canonical identity does not map detector Findings or create qualification metrics. Accepted
v0.8.0 and earlier schema packages remain immutable.
"""


def _release_changelog() -> str:
    return """# Changelog

## 0.9.0

- Accepted ADR-0008 and added review-local root-cause candidate identities.
- Added exact Stage-2 candidate-set reconciliation without Stage-1 answer leakage.
- Added the public AdjudicatedRootCause record and typed adjudication/fixture references.
- Required fail-closed demotion of legacy positives that lack canonical reconciliation evidence.
- Kept detector-to-root-cause comparison and qualification metrics outside this release.

""" + (BASELINE / "CHANGELOG.md").read_text(encoding="utf-8").removeprefix("# Changelog\n")


def _release_invariants() -> str:
    return (
        (BASELINE / "CONTROLLER_INVARIANTS.md").read_text(encoding="utf-8")
        + """

## Canonical root-cause invariants added in 0.9.0

- Stage-1 AgentReviews expose no canonical cross-review root-cause identity or grouping.
- Every demonstrated review-local candidate ID recomputes from exact review content.
- Positive Stage-2 reviews reconcile an exact frozen candidate set with evidence.
- An AdjudicatedRootCause requires identical fresh cross-provider Stage-2 membership, resolved
  evidence, surviving falsification, and no material dissent.
- Prose similarity, embeddings, confidence, and majority vote cannot create identity.
- A positive BenchmarkAdjudication and fixture use typed AdjudicatedRootCause references.
- Canonical scientific identity does not establish detector equivalence or qualification metrics.
"""
    )


def _root_cause_tests() -> str:
    return """from copy import deepcopy

from test_examples import invalid, load


def test_stage1_root_cause_identity_cannot_reconcile_other_reviews():
    review = load("agent-review.example.json")
    review["root_cause_identity"]["reconciled_stage1_candidates"] = [
        {"review_ref": {"record_type": "agent_review", "record_id": "review:other"},
         "candidate_root_cause_id": "root-cause-candidate:other"}
    ]
    invalid(review, "agent_review")


def test_stage2_demonstrated_issue_requires_candidate_set_and_equivalence_evidence():
    review = load("agent-review.stage2.example.json")
    review["root_cause_identity"]["reconciled_stage1_candidates"] = []
    invalid(review, "agent_review")
    review = load("agent-review.stage2.example.json")
    review["root_cause_identity"]["equivalence_evidence"] = []
    invalid(review, "agent_review")


def test_positive_adjudication_requires_typed_verified_root_cause():
    adjudication = load("benchmark-adjudication.example.json")
    adjudication["adjudicated_root_cause_refs"] = []
    invalid(adjudication, "benchmark_adjudication")
    adjudication = load("benchmark-adjudication.example.json")
    adjudication["root_cause_reconciliation_status"] = "unresolved"
    invalid(adjudication, "benchmark_adjudication")


def test_nonpositive_fixture_cannot_claim_a_positive_root_cause():
    fixture = load("benchmark-fixture.example.json")
    fixture["expected_root_cause_refs"] = [
        {"record_type": "adjudicated_root_cause", "record_id": "root-cause:forbidden"}
    ]
    invalid(fixture, "benchmark_fixture")


def test_adjudicated_root_cause_requires_bounded_exclusion():
    root_cause = load("adjudicated-root-cause.example.json")
    root_cause["stronger_claims_excluded"] = []
    invalid(root_cause, "adjudicated_root_cause")


def test_bundle_requires_root_cause_collection():
    bundle = load("audit-bundle.example.json")
    del bundle["adjudicated_root_causes"]
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
    """Build accepted v0.9.0 without modifying immutable v0.8.0."""

    _require_empty_destination(output)
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "common.schema.json":
            _extend_common(schema)
        elif source.name == "agent-review.schema.json":
            _extend_agent_review(schema)
        elif source.name == "benchmark-adjudication.schema.json":
            _extend_benchmark_adjudication(schema)
        elif source.name == "benchmark-fixture.schema.json":
            _extend_benchmark_fixture(schema)
        elif source.name == "audit-bundle.schema.json":
            _extend_bundle(schema)
        elif source.name == "record-union.schema.json":
            _extend_union(schema)
        _write_json(schema_output / source.name, schema)
    root_schema = _replace_version(
        _read_json(PROPOSAL / "schemas" / "adjudicated-root-cause.schema.json")
    )
    _write_json(schema_output / "adjudicated-root-cause.schema.json", root_schema)

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _extend_catalog(catalog)
    _write_json(output / "schema-catalog.json", catalog)

    example_count = 0
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        _upgrade_example_records(example)
        _write_json(output / "examples" / source.name, example)
        example_count += 1
    _write_json(output / "examples" / "adjudicated-root-cause.example.json", _root_cause_example())
    example_count += 1

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.8_to_v0.9.md").write_text(
        """# Migration from v0.8.0 to v0.9.0

Derive review-local candidate IDs only from exact existing demonstrated Stage-1 review content.
Do not infer cross-review equivalence. Demote legacy demonstrated Stage-2 reviews and positive
adjudications to insufficient evidence, preserving prior fields in `x-v0-8-*` extensions. Demote
legacy positive fixtures to ambiguous and preserve prior labels in extensions. Add an empty
AdjudicatedRootCause collection. Do not carry forward a StorageManifest because migrated bytes
require a new manifest.
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
        text = text.replace('len(u["oneOf"])==48', 'len(u["oneOf"])==49')
        (tests_output / source.name).write_text(text, encoding="utf-8")
    (tests_output / "test_root_cause_invariants.py").write_text(
        _root_cause_tests(), encoding="utf-8"
    )
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
        "sc-referee schema package 0.9.0 validation\n\n"
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
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.9.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
