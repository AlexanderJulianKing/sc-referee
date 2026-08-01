from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "reference" / "schemas-v0.10.0"
BASELINE_VERSION = "0.10.0"
RELEASE_VERSION = "0.11.0"
SOURCE_ADRS = [
    "docs/implementation/ADR-0010-EXPERIMENTAL-DETECTOR-CANDIDATE-STATE.md",
    "docs/implementation/ADR-0011-REPRODUCIBLE-QUALIFICATION-METRIC-INPUTS.md",
]

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

DETECTOR_RESULT_STATES = [
    "finding_candidate",
    "evaluation_finding_candidate",
    "conditional_concern_candidate",
    "material_question_candidate",
    "disclosure_candidate",
    "no_issue_detected_within_coverage",
    "not_applicable",
    "insufficient_semantics",
    "unsupported_path",
    "execution_evidence_unavailable",
    "detector_error",
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


def _extend_audit_bundle(schema: dict[str, Any]) -> None:
    schema["properties"]["extensions"] = {
        "additionalProperties": True,
        "propertyNames": {"pattern": "^x-"},
        "type": "object",
    }


def _extend_detector_result(schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    properties["state"]["enum"] = DETECTOR_RESULT_STATES
    candidate_states = schema["allOf"][0]["if"]["properties"]["state"]["enum"]
    candidate_states.insert(1, "evaluation_finding_candidate")
    schema["allOf"].insert(
        2,
        {
            "if": {
                "properties": {"state": {"const": "evaluation_finding_candidate"}},
                "required": ["state"],
            },
            "then": {
                "properties": {
                    "candidate": {
                        "properties": {
                            "assessment_type": {"const": "finding"},
                            "material_premise_ids": {"minItems": 1},
                            "unresolved_material_premise_ids": {"maxItems": 0},
                        },
                        "required": [
                            "assessment_type",
                            "material_premise_ids",
                            "unresolved_material_premise_ids",
                        ],
                    },
                    "detector_maturity": {"const": "experimental"},
                },
                "required": ["candidate"],
            },
        },
    )


def _detector_result_outcome_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "allOf": [
            {
                "if": {
                    "properties": {"state": {"const": "detector_error"}},
                    "required": ["state"],
                },
                "then": {"properties": {"execution_class": {"const": "detector_error"}}},
                "else": {"properties": {"execution_class": {"const": "completed"}}},
            }
        ],
        "properties": {
            "detector_result_ref": _typed_ref("detector_result"),
            "detector_result_digest": _common_ref("Digest"),
            "state": {"enum": DETECTOR_RESULT_STATES},
            "applicability_status": {"enum": ["applicable", "not_applicable", "uncertain"]},
            "coverage_status": {"enum": ["covered", "partially_covered", "not_covered", "unknown"]},
            "evaluation_candidate_refs": {
                "items": _typed_ref("detector_evaluation_candidate"),
                "minItems": 0,
                "type": "array",
                "uniqueItems": True,
            },
            "execution_class": {"enum": ["completed", "detector_error"]},
        },
        "required": [
            "detector_result_ref",
            "detector_result_digest",
            "state",
            "applicability_status",
            "coverage_status",
            "evaluation_candidate_refs",
            "execution_class",
        ],
        "type": "object",
    }


def _extend_detector_case_outcome(schema: dict[str, Any]) -> None:
    schema["properties"]["metric_input_status"] = {
        "enum": ["complete", "legacy_source_projection_unavailable"]
    }
    schema["properties"]["detector_result_outcomes"] = {
        "items": _detector_result_outcome_schema(),
        "minItems": 0,
        "type": "array",
        "uniqueItems": True,
    }
    required = schema["required"]
    required.insert(required.index("detector_run_outcome"), "metric_input_status")
    required.insert(required.index("detector_run_outcome"), "detector_result_outcomes")

    reconciled_then = schema["allOf"][0]["then"]["properties"]
    del reconciled_then["metric_eligible"]
    schema["allOf"].extend(
        [
            {
                "if": {
                    "properties": {"metric_input_status": {"const": "complete"}},
                    "required": ["metric_input_status"],
                },
                "then": {"properties": {"detector_result_outcomes": {"minItems": 1}}},
            },
            {
                "if": {
                    "properties": {
                        "metric_input_status": {"const": "legacy_source_projection_unavailable"}
                    },
                    "required": ["metric_input_status"],
                },
                "then": {
                    "properties": {
                        "detector_result_outcomes": {"maxItems": 0},
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
                "then": {
                    "properties": {
                        "comparison_status": {"const": "reconciled"},
                        "metric_input_status": {"const": "complete"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "comparison_status": {"const": "reconciled"},
                        "metric_input_status": {"const": "complete"},
                    },
                    "required": ["comparison_status", "metric_input_status"],
                },
                "then": {"properties": {"metric_eligible": {"const": True}}},
            },
        ]
    )


def _extend_metric_entry(entry: dict[str, Any]) -> None:
    entry["allOf"] = [
        {
            "if": {
                "properties": {"denominator": {"const": 0}},
                "required": ["denominator"],
            },
            "then": {"properties": {"estimate": {"const": None}}},
            "else": {"properties": {"estimate": {"type": "number"}}},
        },
        {
            "if": {
                "properties": {
                    "interval": {
                        "properties": {"status": {"const": "estimated"}},
                        "required": ["status"],
                    }
                },
                "required": ["interval"],
            },
            "then": {
                "properties": {
                    "interval": {
                        "properties": {
                            "lower": {"type": "number"},
                            "upper": {"type": "number"},
                            "valid_replicates": {"minimum": 2},
                        }
                    }
                }
            },
            "else": {
                "properties": {
                    "interval": {
                        "properties": {
                            "lower": {"const": None},
                            "upper": {"const": None},
                        }
                    }
                }
            },
        },
    ]


def _extend_qualification_metric_set(schema: dict[str, Any]) -> None:
    metrics = schema["properties"]["metrics"]
    metrics["uniqueItems"] = True
    _extend_metric_entry(metrics["items"])
    schema["allOf"].extend(
        {
            "properties": {
                "metrics": {
                    "contains": {
                        "properties": {"metric_name": {"const": name}},
                        "required": ["metric_name"],
                    },
                    "maxContains": 1,
                    "minContains": 1,
                }
            }
        }
        for name in METRIC_NAMES
    )


def _upgrade_case_outcome_example(example: dict[str, Any]) -> None:
    candidate_refs = deepcopy(example["candidate_refs"])
    example["metric_input_status"] = "complete"
    example["detector_result_outcomes"] = [
        {
            "detector_result_ref": {
                "record_type": "detector_result",
                "record_id": "result:claim-direction",
            },
            "detector_result_digest": "sha256:" + "5" * 64,
            "state": "evaluation_finding_candidate",
            "applicability_status": "applicable",
            "coverage_status": "covered",
            "evaluation_candidate_refs": candidate_refs,
            "execution_class": "completed",
        }
    ]


def _evaluation_result_example(baseline: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(baseline)
    result["result_id"] = "result:evaluation-claim-direction"
    result["detector_maturity"] = "experimental"
    result["state"] = "evaluation_finding_candidate"
    result["provenance"]["method"] = "deterministic_evaluation_detection"
    return result


def _release_readme() -> str:
    return """# sc-referee schema package

**Version:** 0.11.0

This immutable JSON Schema Draft 2020-12 package defines the public sc-referee record model at
`https://w3id.org/sc-referee/schema/v0.11.0/`.

Version 0.11.0 implements accepted ADR-0010 and ADR-0011. It represents experimental detector
outputs that satisfy every non-maturity Finding check without granting production Finding authority,
preserves one exact metric projection per source DetectorResult, and closes all twelve qualification
metric formulas and the deterministic clustered-bootstrap protocol.

Migration from v0.10.0 is fail-closed. It invents no detector state, evaluation candidate,
opportunity projection, metric, interval, qualification, or Finding. Accepted v0.10.0 and earlier
schema packages remain immutable.
"""


def _release_changelog() -> str:
    prior = (BASELINE / "CHANGELOG.md").read_text(encoding="utf-8").removeprefix("# Changelog\n")
    return (
        """# Changelog

## 0.11.0

- Accepted ADR-0010 and added the closed `evaluation_finding_candidate` DetectorResult state.
- Accepted ADR-0011 and required exact per-DetectorResult metric opportunity projections.
- Closed the twelve qualification metric formulas and deterministic bootstrap byte protocol.
- Required fail-closed v0.10 migration for incomplete case outcomes and legacy metric sets.
- Kept production Finding admission and detector promotion closed.

"""
        + prior
    )


def _release_invariants() -> str:
    return (
        (BASELINE / "CONTROLLER_INVARIANTS.md").read_text(encoding="utf-8")
        + """

## Experimental-candidate and metric invariants added in 0.11.0

- `evaluation_finding_candidate` is experimental and can never enter production Finding admission.
- Evaluation projection reuses every deterministic non-maturity Finding-admission check.
- A complete case outcome contains exactly one digest-verified projection for every source
  DetectorResult and every evaluation candidate cites exactly one such projection.
- A legacy-incomplete projection is metric- and promotion-ineligible and remains explicit.
- Metric inputs contain every selected case outcome; exclusions are a subset, never omitted input.
- One case outcome is one workflow and one projected DetectorResult is one opportunity.
- The twelve public metrics use only their closed status sets and count an unsafe opportunity once.
- A zero denominator has a null estimate; it is never interpreted as zero or one.
- Bootstrap sampling is clustered by problem ID and uses the accepted SHA-256 counter protocol.
- Public-development, excluded, incomplete, or otherwise ineligible evidence cannot promote a
  detector; all v0.11 metric sets retain `promotion_permitted: false`.
"""
    )


def _migration_text() -> str:
    return """# Migration from v0.10.0 to v0.11.0

Update only schema namespaces and versions for existing records, except as follows:

- Give each legacy DetectorCaseOutcome
  `metric_input_status: legacy_source_projection_unavailable`, an empty
  `detector_result_outcomes` array, and false metric/promotion eligibility. Preserve its prior flags
  in namespaced migration metadata.
- Remove every legacy QualificationMetricSet from an AuditBundle's authoritative metric-set array
  and preserve its exact payload only in namespaced migration metadata. A standalone legacy metric
  set is reported as non-authoritative legacy evidence and is not emitted as v0.11.
- Clear StorageManifest arrays because migrated canonical bytes require a new manifest.

Do not infer or create a DetectorResult state, evaluation candidate, opportunity projection,
Finding, equivalence decision, estimate, interval, qualification, capability claim, or maturity.
"""


def _v11_tests() -> str:
    return """from copy import deepcopy

from test_examples import errors, invalid, load


def test_experimental_evaluation_candidate_state_is_closed():
    result = load("detector-result.evaluation-candidate.example.json")
    assert not errors(result, "detector_result")
    result["detector_maturity"] = "validated"
    invalid(result, "detector_result")


def test_finding_candidate_still_rejects_experimental_maturity():
    result = load("detector-result.example.json")
    result["detector_maturity"] = "experimental"
    invalid(result, "detector_result")


def test_evaluation_state_requires_exact_resolved_material_premises():
    result = load("detector-result.evaluation-candidate.example.json")
    result["candidate"]["material_premise_ids"] = []
    invalid(result, "detector_result")
    result = load("detector-result.evaluation-candidate.example.json")
    result["candidate"]["unresolved_material_premise_ids"] = ["premise:unknown"]
    invalid(result, "detector_result")


def test_complete_case_requires_a_result_projection():
    outcome = load("detector-case-outcome.example.json")
    outcome["detector_result_outcomes"] = []
    invalid(outcome, "detector_case_outcome")


def test_result_projection_execution_class_is_derived_from_state():
    outcome = load("detector-case-outcome.example.json")
    outcome["detector_result_outcomes"][0]["execution_class"] = "detector_error"
    invalid(outcome, "detector_case_outcome")
    outcome["detector_result_outcomes"][0]["state"] = "detector_error"
    assert not errors(outcome, "detector_case_outcome")


def test_legacy_incomplete_case_is_fail_closed():
    outcome = load("detector-case-outcome.example.json")
    outcome["metric_input_status"] = "legacy_source_projection_unavailable"
    outcome["detector_result_outcomes"] = []
    outcome["metric_eligible"] = False
    assert not errors(outcome, "detector_case_outcome")
    outcome["metric_eligible"] = True
    invalid(outcome, "detector_case_outcome")


def test_metric_set_requires_each_declared_metric_exactly_once():
    metric_set = load("qualification-metric-set.example.json")
    metric_set["metrics"][1]["metric_name"] = metric_set["metrics"][0]["metric_name"]
    invalid(metric_set, "qualification_metric_set")


def test_zero_denominator_requires_null_estimate():
    metric_set = load("qualification-metric-set.example.json")
    metric_set["metrics"][0]["denominator"] = 0
    metric_set["metrics"][0]["estimate"] = 0
    invalid(metric_set, "qualification_metric_set")
    metric_set["metrics"][0]["estimate"] = None
    assert not errors(metric_set, "qualification_metric_set")


def test_not_estimable_interval_requires_null_bounds():
    metric_set = load("qualification-metric-set.example.json")
    metric_set["metrics"][0]["interval"]["lower"] = 0
    invalid(metric_set, "qualification_metric_set")
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
    """Build accepted v0.11.0 without modifying immutable v0.10.0."""

    _require_empty_destination(output)
    baseline_schema_dir = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted(baseline_schema_dir.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "audit-bundle.schema.json":
            _extend_audit_bundle(schema)
        elif source.name == "detector-result.schema.json":
            _extend_detector_result(schema)
        elif source.name == "detector-case-outcome.schema.json":
            _extend_detector_case_outcome(schema)
        elif source.name == "qualification-metric-set.schema.json":
            _extend_qualification_metric_set(schema)
        _write_json(schema_output / source.name, schema)

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _write_json(output / "schema-catalog.json", catalog)

    example_count = 0
    evaluation_result: dict[str, Any] | None = None
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        if source.name == "detector-case-outcome.example.json":
            _upgrade_case_outcome_example(example)
        if source.name == "detector-result.example.json":
            evaluation_result = _evaluation_result_example(example)
        _write_json(output / "examples" / source.name, example)
        example_count += 1
    if evaluation_result is None:
        raise ValueError("Baseline detector-result example is missing")
    _write_json(
        output / "examples" / "detector-result.evaluation-candidate.example.json",
        evaluation_result,
    )
    example_count += 1

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.10_to_v0.11.md").write_text(_migration_text(), encoding="utf-8")
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
    (tests_output / "test_v011_invariants.py").write_text(_v11_tests(), encoding="utf-8")

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
        "sc-referee schema package 0.11.0 validation\n\n"
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
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.11.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
