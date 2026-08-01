from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.11.0"
BASELINE_VERSION = "0.11.0"
RELEASE_VERSION = "0.12.0"
SOURCE_ADRS = ["docs/implementation/ADR-0012-EVIDENCE-BOUND-FIXTURE-PROOFS.md"]


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


def _public_input(record_type: str) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "record_ref": _typed_ref(record_type),
            "semantic_digest": _common_ref("Digest"),
        },
        "required": ["record_ref", "semantic_digest"],
        "type": "object",
    }


def _public_input_array(
    record_type: str, *, min_items: int = 0, max_items: int | None = None
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "items": _public_input(record_type),
        "minItems": min_items,
        "type": "array",
        "uniqueItems": True,
    }
    if max_items is not None:
        result["maxItems"] = max_items
    return result


def _artifact_input(artifact_kind: str) -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "artifact_id": _common_ref("Identifier"),
            "artifact_kind": {"const": artifact_kind},
            "content_digest": _common_ref("Digest"),
        },
        "required": ["artifact_kind", "artifact_id", "content_digest"],
        "type": "object",
    }


def _artifact_input_array(artifact_kind: str) -> dict[str, Any]:
    return {
        "items": _artifact_input(artifact_kind),
        "minItems": 0,
        "type": "array",
        "uniqueItems": True,
    }


def _proof_evidence_schema() -> dict[str, Any]:
    public_inputs = {
        "additionalProperties": False,
        "properties": {
            "source_snapshots": _public_input_array(
                "repository_snapshot", min_items=1, max_items=1
            ),
            "adjudications": _public_input_array(
                "benchmark_adjudication", min_items=1, max_items=1
            ),
            "agent_reviews": _public_input_array("agent_review"),
            "adjudicated_root_causes": _public_input_array("adjudicated_root_cause"),
            "scientific_contracts": _public_input_array("scientific_contract"),
            "operations": _public_input_array("operation"),
            "environments": _public_input_array("environment"),
            "executions": _public_input_array("execution"),
            "sandbox_capabilities": _public_input_array("sandbox_capability"),
        },
        "required": [
            "source_snapshots",
            "adjudications",
            "agent_reviews",
            "adjudicated_root_causes",
            "scientific_contracts",
            "operations",
            "environments",
            "executions",
            "sandbox_capabilities",
        ],
        "type": "object",
    }
    protocol_artifacts = {
        "additionalProperties": False,
        "properties": {
            "blind_workspace_manifests": _artifact_input_array("blind_workspace_manifest"),
            "review_packets": _artifact_input_array("review_packet"),
            "review_captures": _artifact_input_array("review_capture"),
            "review_transcripts": _artifact_input_array("review_transcript"),
            "stage1_freezes": _artifact_input_array("stage1_freeze"),
        },
        "required": [
            "blind_workspace_manifests",
            "review_packets",
            "review_captures",
            "review_transcripts",
            "stage1_freezes",
        ],
        "type": "object",
    }
    hard_negative = {
        "additionalProperties": False,
        "properties": {
            "suspicious_pattern": {
                "items": _common_ref("EvidenceItem"),
                "minItems": 0,
                "type": "array",
            },
            "decisive_innocent_explanation": {
                "items": _common_ref("EvidenceItem"),
                "minItems": 0,
                "type": "array",
            },
        },
        "required": ["suspicious_pattern", "decisive_innocent_explanation"],
        "type": "object",
    }
    return {
        "additionalProperties": False,
        "properties": {
            "controller_profile": {"const": "fixture-proof-evidence-v1"},
            "source_validation_report_digest": _common_ref("Digest"),
            "chronology_validated": {"const": True},
            "public_inputs": public_inputs,
            "protocol_artifacts": protocol_artifacts,
            "hard_negative_evidence": hard_negative,
        },
        "required": [
            "controller_profile",
            "source_validation_report_digest",
            "chronology_validated",
            "public_inputs",
            "protocol_artifacts",
            "hard_negative_evidence",
        ],
        "type": "object",
    }


def _nested_minimums(
    *, roots: int | None = None, contracts: int | None = None, executions: int | None = None
) -> dict[str, Any]:
    public_properties: dict[str, Any] = {
        "agent_reviews": {"minItems": 6},
    }
    if roots is not None:
        public_properties["adjudicated_root_causes"] = {"minItems": roots}
    if contracts is not None:
        public_properties["scientific_contracts"] = {"minItems": contracts}
    if executions is not None:
        public_properties["environments"] = {"minItems": executions}
        public_properties["executions"] = {"minItems": executions}
        public_properties["sandbox_capabilities"] = {"minItems": executions}
    return {
        "properties": {
            "public_inputs": {"properties": public_properties},
            "protocol_artifacts": {
                "properties": {
                    "blind_workspace_manifests": {"minItems": 1},
                    "review_packets": {"minItems": 6},
                    "review_captures": {"minItems": 6},
                    "review_transcripts": {"minItems": 6},
                    "stage1_freezes": {"minItems": 1, "maxItems": 1},
                }
            },
        }
    }


def _extend_benchmark_fixture(schema: dict[str, Any]) -> None:
    schema["properties"]["qualification_proof_status"] = {
        "enum": [
            "complete",
            "excluded_label",
            "legacy_proof_projection_unavailable",
        ]
    }
    schema["properties"]["proof_evidence"] = {"oneOf": [_proof_evidence_schema(), {"type": "null"}]}
    schema["required"].extend(["qualification_proof_status", "proof_evidence"])
    schema["allOf"].extend(
        [
            {
                "if": {
                    "properties": {"qualification_proof_status": {"const": "complete"}},
                    "required": ["qualification_proof_status"],
                },
                "then": {
                    "properties": {
                        "fixture_kind": {"not": {"const": "ambiguous_fixture"}},
                        "proof_evidence": {"type": "object"},
                    }
                },
            },
            {
                "if": {
                    "properties": {"qualification_proof_status": {"const": "excluded_label"}},
                    "required": ["qualification_proof_status"],
                },
                "then": {
                    "properties": {
                        "fixture_kind": {"const": "ambiguous_fixture"},
                        "proof_evidence": {"type": "null"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "qualification_proof_status": {
                            "const": "legacy_proof_projection_unavailable"
                        }
                    },
                    "required": ["qualification_proof_status"],
                },
                "then": {
                    "properties": {
                        "fixture_kind": {
                            "enum": [
                                "verified_good_fixture",
                                "scope_verified_good",
                                "hard_negative_fixture",
                                "positive_issue_fixture",
                            ]
                        },
                        "proof_evidence": {"type": "null"},
                    }
                },
            },
            {
                "if": {
                    "properties": {"fixture_kind": {"const": "ambiguous_fixture"}},
                    "required": ["fixture_kind"],
                },
                "then": {"properties": {"qualification_proof_status": {"const": "excluded_label"}}},
            },
            {
                "if": {
                    "properties": {
                        "fixture_kind": {"const": "positive_issue_fixture"},
                        "qualification_proof_status": {"const": "complete"},
                    },
                    "required": ["fixture_kind", "qualification_proof_status"],
                },
                "then": {"properties": {"proof_evidence": _nested_minimums(roots=1)}},
            },
            {
                "if": {
                    "properties": {
                        "fixture_kind": {
                            "enum": [
                                "verified_good_fixture",
                                "scope_verified_good",
                                "hard_negative_fixture",
                            ]
                        },
                        "qualification_proof_status": {"const": "complete"},
                    },
                    "required": ["fixture_kind", "qualification_proof_status"],
                },
                "then": {"properties": {"proof_evidence": _nested_minimums(contracts=1)}},
            },
            {
                "if": {
                    "properties": {
                        "fixture_kind": {
                            "enum": ["verified_good_fixture", "hard_negative_fixture"]
                        },
                        "qualification_proof_status": {"const": "complete"},
                    },
                    "required": ["fixture_kind", "qualification_proof_status"],
                },
                "then": {"properties": {"proof_evidence": _nested_minimums(executions=1)}},
            },
            {
                "if": {
                    "properties": {
                        "fixture_kind": {"const": "hard_negative_fixture"},
                        "qualification_proof_status": {"const": "complete"},
                    },
                    "required": ["fixture_kind", "qualification_proof_status"],
                },
                "then": {
                    "properties": {
                        "proof_evidence": {
                            "properties": {
                                "hard_negative_evidence": {
                                    "properties": {
                                        "suspicious_pattern": {"minItems": 1},
                                        "decisive_innocent_explanation": {"minItems": 1},
                                    }
                                }
                            }
                        }
                    }
                },
            },
        ]
    )


def _extend_detector_case_outcome(schema: dict[str, Any]) -> None:
    schema["properties"]["fixture_semantic_digest"] = _common_ref("Digest")
    schema["properties"]["qualification_proof_status"] = {
        "enum": [
            "complete",
            "excluded_label",
            "legacy_proof_projection_unavailable",
        ]
    }
    schema["required"].extend(["fixture_semantic_digest", "qualification_proof_status"])
    for clause in schema["allOf"]:
        condition = clause.get("if", {})
        properties = condition.get("properties", {})
        if (
            properties.get("comparison_status", {}).get("const") == "reconciled"
            and properties.get("metric_input_status", {}).get("const") == "complete"
        ):
            properties["qualification_proof_status"] = {"const": "complete"}
            condition["required"].append("qualification_proof_status")
    schema["allOf"].extend(
        [
            {
                "if": {
                    "properties": {
                        "qualification_proof_status": {
                            "enum": [
                                "excluded_label",
                                "legacy_proof_projection_unavailable",
                            ]
                        }
                    },
                    "required": ["qualification_proof_status"],
                },
                "then": {
                    "properties": {
                        "metric_eligible": {"const": False},
                        "promotion_evidence_eligible": {"const": False},
                    }
                },
            },
            {
                "if": {
                    "properties": {"metric_eligible": {"const": True}},
                    "required": ["metric_eligible"],
                },
                "then": {"properties": {"qualification_proof_status": {"const": "complete"}}},
            },
        ]
    )


def _semantic_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _public_entry(record_type: str, record_id: str, fill: str) -> dict[str, Any]:
    return {
        "record_ref": {"record_type": record_type, "record_id": record_id},
        "semantic_digest": f"sha256:{fill * 64}",
    }


def _artifact_entries(kind: str, prefix: str, count: int, fill: str) -> list[dict[str, Any]]:
    return [
        {
            "artifact_kind": kind,
            "artifact_id": f"{prefix}:{index}",
            "content_digest": f"sha256:{fill * 64}",
        }
        for index in range(1, count + 1)
    ]


def _complete_proof_example() -> dict[str, Any]:
    return {
        "controller_profile": "fixture-proof-evidence-v1",
        "source_validation_report_digest": "sha256:" + "a" * 64,
        "chronology_validated": True,
        "public_inputs": {
            "source_snapshots": [_public_entry("repository_snapshot", "snapshot:1", "1")],
            "adjudications": [
                _public_entry(
                    "benchmark_adjudication", "benchmark-adjudication:verified-good-1", "2"
                )
            ],
            "agent_reviews": [
                _public_entry("agent_review", f"review:verified-good:{index}", "3")
                for index in range(1, 7)
            ],
            "adjudicated_root_causes": [],
            "scientific_contracts": [_public_entry("scientific_contract", "contract:1", "4")],
            "operations": [_public_entry("operation", "operation:1", "5")],
            "environments": [_public_entry("environment", "environment:clean", "e")],
            "executions": [_public_entry("execution", "execution:verified-good", "6")],
            "sandbox_capabilities": [
                _public_entry("sandbox_capability", "sandbox:rootless-podman", "7")
            ],
        },
        "protocol_artifacts": {
            "blind_workspace_manifests": _artifact_entries(
                "blind_workspace_manifest", "workspace-manifest", 1, "8"
            ),
            "review_packets": _artifact_entries("review_packet", "review-packet", 6, "9"),
            "review_captures": _artifact_entries("review_capture", "review-capture", 6, "a"),
            "review_transcripts": _artifact_entries(
                "review_transcript", "review-transcript", 6, "b"
            ),
            "stage1_freezes": _artifact_entries("stage1_freeze", "stage1-freeze", 1, "c"),
        },
        "hard_negative_evidence": {
            "suspicious_pattern": [],
            "decisive_innocent_explanation": [],
        },
    }


def _upgrade_fixture_example(example: dict[str, Any], *, complete: bool) -> None:
    if complete:
        example["qualification_proof_status"] = "complete"
        example["proof_evidence"] = _complete_proof_example()
    elif example.get("fixture_kind") == "ambiguous_fixture":
        example["qualification_proof_status"] = "excluded_label"
        example["proof_evidence"] = None
    else:
        example["qualification_proof_status"] = "legacy_proof_projection_unavailable"
        example["proof_evidence"] = None


def _upgrade_case_outcome_example(
    example: dict[str, Any], *, fixture: dict[str, Any] | None = None, complete: bool
) -> None:
    example["qualification_proof_status"] = (
        "complete" if complete else "legacy_proof_projection_unavailable"
    )
    example["fixture_semantic_digest"] = (
        _semantic_digest(fixture) if fixture is not None else "sha256:" + "d" * 64
    )
    if not complete:
        example["metric_eligible"] = False
        example["promotion_evidence_eligible"] = False


def _upgrade_audit_bundle_example(example: dict[str, Any]) -> None:
    fixtures = {
        str(fixture["fixture_id"]): fixture for fixture in example.get("benchmark_fixtures", [])
    }
    for fixture in fixtures.values():
        _upgrade_fixture_example(fixture, complete=False)
    for outcome in example.get("detector_case_outcomes", []):
        fixture_id = str(outcome.get("fixture_ref", {}).get("record_id", ""))
        _upgrade_case_outcome_example(
            outcome,
            fixture=fixtures.get(fixture_id),
            complete=False,
        )
    if example.get("qualification_metric_sets"):
        extensions = example.setdefault("extensions", {})
        extensions["x-legacy-v0.11-qualification-metric-sets"] = example[
            "qualification_metric_sets"
        ]
        example["qualification_metric_sets"] = []
    example["storage_manifests"] = []


def _release_readme() -> str:
    return f"""# sc-referee public schema package v{RELEASE_VERSION}

This accepted package advances immutable v{BASELINE_VERSION} under ADR-0012. It binds eligible
fixture proof status to exact public inputs and closed private evaluation-artifact identities,
propagates the fixture digest and proof status into detector case outcomes, and excludes legacy
proof projections from authoritative metrics.

Older accepted packages remain immutable migration baselines.
"""


def _release_changelog() -> str:
    return f"""# Changelog

## {RELEASE_VERSION}

- Added closed fixture qualification-proof status and exact proof-evidence projections.
- Bound capture, packet, transcript, blind-workspace, snapshot, and Stage-1-freeze identities.
- Required evidence-backed clean executions and hard-negative explanations for complete controls.
- Added exact fixture digests and copied proof status to detector case outcomes.
- Added fail-closed v{BASELINE_VERSION} migration behavior without inferred proof.
"""


def _release_invariants() -> str:
    return f"""# Controller invariants for schema v{RELEASE_VERSION}

1. A complete eligible fixture resolves every exact public and private proof input.
2. Loose reviews, missing captures, reversed chronology, and post-panel snapshots are ineligible.
3. Clean project execution requires a successful authorized project Execution and qualifying
   rootless OCI SandboxCapability; no subprocess fallback is equivalent.
4. Hard-negative pattern and decisive innocent-explanation evidence resolve independently.
5. Non-complete fixture proof status makes detector case outcomes metric- and promotion-ineligible.
6. Model agreement and confidence never establish a material premise.
"""


def _migration_text() -> str:
    return f"""# Migration from v{BASELINE_VERSION} to v{RELEASE_VERSION}

Migration is fail closed. Existing eligible fixtures receive
`legacy_proof_projection_unavailable` and `proof_evidence: null`; excluded ambiguous fixtures
receive `excluded_label`. No capture, packet, transcript, workspace, chronology, execution,
sandbox, hard-negative explanation, or other proof is inferred. Case outcomes copy the fixture
status and digest, receive a new identity, and become metric- and promotion-ineligible when proof
is unavailable. Legacy QualificationMetricSets are retained only in a namespaced bundle extension,
and StorageManifests are cleared because canonical bytes change.
"""


def _v12_tests() -> str:
    return """from __future__ import annotations
import copy,json
from pathlib import Path
from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry,Resource

ROOT=Path(__file__).resolve().parents[1]; SD=ROOT/"schemas"/"v0.12.0"; EX=ROOT/"examples"
cat=json.loads((ROOT/"schema-catalog.json").read_text()); reg=Registry(); schemas={}; aliases={}
for item in cat["schemas"]:
 d=json.loads((SD/item["file"]).read_text()); validator_for(d).check_schema(d); reg=reg.with_resource(d["$id"],Resource.from_contents(d)); schemas[d["$id"]]=d; aliases[item["name"]]=d["$id"]
def load(name): return json.loads((EX/name).read_text())
def errors(obj,alias):
 s=schemas[aliases[alias]]; return list(validator_for(s)(s,registry=reg,format_checker=FormatChecker()).iter_errors(obj))
def invalid(obj,alias): assert errors(obj,alias)

def test_complete_fixture_requires_exact_proof_projection():
 x=load("benchmark-fixture.example.json"); x["proof_evidence"]=None; invalid(x,"benchmark_fixture")
def test_complete_fixture_requires_capture_and_packet_sets():
 x=load("benchmark-fixture.example.json"); x["proof_evidence"]["protocol_artifacts"]["review_captures"]=[]; invalid(x,"benchmark_fixture")
 x=load("benchmark-fixture.example.json"); x["proof_evidence"]["protocol_artifacts"]["review_packets"]=[]; invalid(x,"benchmark_fixture")
def test_hard_negative_requires_bound_pattern_and_innocent_evidence():
 x=load("benchmark-fixture.example.json"); x["fixture_kind"]="hard_negative_fixture"; x["proof_obligations"]["hard_negative_pattern_documented"]=True; x["proof_obligations"]["decisive_innocent_explanation_documented"]=True; invalid(x,"benchmark_fixture")
def test_legacy_fixture_cannot_retain_complete_proof():
 x=load("benchmark-fixture.example.json"); x["qualification_proof_status"]="legacy_proof_projection_unavailable"; invalid(x,"benchmark_fixture")
 x["proof_evidence"]=None; assert not errors(x,"benchmark_fixture")
def test_noncomplete_case_is_metric_and_promotion_ineligible():
 x=load("detector-case-outcome.example.json"); x["qualification_proof_status"]="legacy_proof_projection_unavailable"; x["metric_eligible"]=False; assert not errors(x,"detector_case_outcome")
 x["metric_eligible"]=True; invalid(x,"detector_case_outcome")
def test_case_requires_fixture_digest():
 x=load("detector-case-outcome.example.json"); x.pop("fixture_semantic_digest"); invalid(x,"detector_case_outcome")
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
    """Build accepted v0.12.0 without modifying immutable v0.11.0."""

    _require_empty_destination(output)
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "benchmark-fixture.schema.json":
            _extend_benchmark_fixture(schema)
        elif source.name == "detector-case-outcome.schema.json":
            _extend_detector_case_outcome(schema)
        _write_json(schema_output / source.name, schema)

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _write_json(output / "schema-catalog.json", catalog)

    example_count = 0
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        if source.name == "benchmark-fixture.example.json":
            _upgrade_fixture_example(example, complete=True)
        elif source.name == "detector-case-outcome.example.json":
            _upgrade_case_outcome_example(example, complete=True)
        elif source.name == "audit-bundle.example.json":
            _upgrade_audit_bundle_example(example)
        _write_json(output / "examples" / source.name, example)
        example_count += 1

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.11_to_v0.12.md").write_text(_migration_text(), encoding="utf-8")
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
        (tests_output / source.name).write_text(source_text, encoding="utf-8")
    (tests_output / "test_v012_invariants.py").write_text(_v12_tests(), encoding="utf-8")

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
        "sc-referee schema package 0.12.0 validation\n\n"
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
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.12.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
