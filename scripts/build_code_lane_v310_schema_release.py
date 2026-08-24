from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from sc_referee.core.ids import canonical_json

ROOT = Path(__file__).resolve().parents[1]
BASELINE_VERSION = "0.20.0"
RELEASE_VERSION = "0.21.0"
RELEASE_DATE = "2026-08-23"
BASELINE = ROOT / f"reference/schemas-v{BASELINE_VERSION}"
PROPOSAL_ROOT = (
    ROOT / "evaluation/qualification/authorized-independent-unit-entry-into-row-independent-"
    "procedure-v3.1.0-code-csv-lane/envelope-9-promotion-v021"
)
SOURCE_ADR = "docs/implementation/ADR-0076-CONTRACT-BOUND-REPORT-CSV-PSEUDOREPLICATION-FINDING.md"
OLD_DETECTOR = "detector:bounded-analysis-method-conflict"
OLD_DETECTOR_VERSION = "0.3.0"
CODE_DETECTOR = "detector:bounded-code-csv-dependence-conflict"
HISTORICAL_CODE_DETECTOR_VERSION = "2.1.0"
CODE_DETECTOR_VERSION = "3.1.0"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected one JSON object: {path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def _replace_version(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _replace_version(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_version(item) for item in value]
    if isinstance(value, str):
        return value.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}").replace(
            BASELINE_VERSION, RELEASE_VERSION
        )
    return value


def _identity_pair_constraints() -> list[dict[str, Any]]:
    return [
        {
            "if": {
                "properties": {"detector_id": {"const": OLD_DETECTOR}},
                "required": ["detector_id"],
            },
            "then": {"properties": {"detector_version": {"const": OLD_DETECTOR_VERSION}}},
        },
        {
            "if": {
                "properties": {"detector_id": {"const": CODE_DETECTOR}},
                "required": ["detector_id"],
            },
            "then": {
                "properties": {
                    "detector_version": {
                        "enum": [HISTORICAL_CODE_DETECTOR_VERSION, CODE_DETECTOR_VERSION]
                    }
                }
            },
        },
    ]


def _extend_detector_identity_pairs(value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            _extend_detector_identity_pairs(item)
        return
    if not isinstance(value, dict):
        return
    properties = value.get("properties")
    if isinstance(properties, dict) and {
        "detector_id",
        "detector_version",
    } <= set(properties):
        detector_id = properties["detector_id"]
        detector_version = properties["detector_version"]
        if detector_id == {"enum": [OLD_DETECTOR, CODE_DETECTOR]} and detector_version == {
            "enum": [OLD_DETECTOR_VERSION, HISTORICAL_CODE_DETECTOR_VERSION]
        }:
            properties["detector_version"] = {
                "enum": [
                    OLD_DETECTOR_VERSION,
                    HISTORICAL_CODE_DETECTOR_VERSION,
                    CODE_DETECTOR_VERSION,
                ]
            }
        if properties["detector_id"] == {"enum": [OLD_DETECTOR, CODE_DETECTOR]} and properties[
            "detector_version"
        ] == {
            "enum": [
                OLD_DETECTOR_VERSION,
                HISTORICAL_CODE_DETECTOR_VERSION,
                CODE_DETECTOR_VERSION,
            ]
        }:
            value["allOf"] = _identity_pair_constraints()
    for item in value.values():
        _extend_detector_identity_pairs(item)


def _extend_reportless_finding_materiality(schema: dict[str, Any]) -> None:
    definition = schema["$defs"]["PublicationMaterialityAssessment"]
    if len(definition["oneOf"]) != 3:
        raise ValueError("the v0.20 reportless materiality branch drifted")


def _code_examples() -> tuple[dict[str, Any], dict[str, Any]]:
    qualification = _load(PROPOSAL_ROOT / "DETECTOR_QUALIFICATION.json")
    metric_set = _load(PROPOSAL_ROOT / "QUALIFICATION_METRIC_SET.json")
    qualification = _replace_version(qualification)
    metric_set = _replace_version(metric_set)
    approvals = qualification.get("software_maintainer_approvals")
    if not isinstance(approvals, list) or len(approvals) != 1:
        raise ValueError("code-lane qualification must have one maintainer approval")
    approvals[0]["decision_ref"] = SOURCE_ADR
    return qualification, metric_set


def _release_tests() -> str:
    return f'''from copy import deepcopy

from test_examples import errors, invalid, load


def test_code_csv_qualification_identity_is_accepted():
 qualification=load("detector-qualification.code-csv-dependence.example.json")
 metric=load("qualification-metric-set.code-csv-dependence.example.json")
 assert qualification["detector_id"]=="{CODE_DETECTOR}"
 assert qualification["detector_version"]=="{CODE_DETECTOR_VERSION}"
 assert metric["binding_scope"]==qualification["binding_scope"]
 assert not errors(qualification,"detector_qualification")
 assert not errors(metric,"qualification_metric_set")


def test_detector_identity_versions_cannot_cross():
 for name,record_type in (
  ("detector-qualification.code-csv-dependence.example.json","detector_qualification"),
  ("qualification-metric-set.code-csv-dependence.example.json","qualification_metric_set"),
 ):
  value=load(name)
  for target in (value,value["binding_scope"]):
   wrong=deepcopy(value)
   selected=wrong if target is value else wrong["binding_scope"]
   selected["detector_version"]="9.9.9"
   invalid(wrong,record_type)


def test_old_generic_identity_remains_accepted():
 qualification=load("detector-qualification.code-csv-dependence.example.json")
 metric=load("qualification-metric-set.code-csv-dependence.example.json")
 for value in (qualification,metric):
  value["detector_id"]="{OLD_DETECTOR}"
  value["detector_version"]="{OLD_DETECTOR_VERSION}"
  value["binding_scope"]["detector_id"]="{OLD_DETECTOR}"
  value["binding_scope"]["detector_version"]="{OLD_DETECTOR_VERSION}"
 assert qualification["detector_id"]=="{OLD_DETECTOR}"
 assert qualification["detector_version"]=="{OLD_DETECTOR_VERSION}"
 assert not errors(qualification,"detector_qualification")
 assert not errors(metric,"qualification_metric_set")


def test_historical_code_identity_remains_accepted():
 qualification=load("detector-qualification.code-csv-dependence.example.json")
 metric=load("qualification-metric-set.code-csv-dependence.example.json")
 for value in (qualification,metric):
  value["detector_version"]="{HISTORICAL_CODE_DETECTOR_VERSION}"
  value["binding_scope"]["detector_version"]="{HISTORICAL_CODE_DETECTOR_VERSION}"
 assert not errors(qualification,"detector_qualification")
 assert not errors(metric,"qualification_metric_set")


def test_reportless_finding_materiality_is_accepted_without_claiming_selection():
 finding=load("finding.example.json")
 finding["publication_materiality"]={{
  "state":"unassessed",
  "reason":"no_selected_publication_surface",
  "rationale":"The reportless lane establishes no selected publication surface.",
  "candidate_publication_surface_ids":[],
 }}
 assert not errors(finding,"finding")
'''


def _write_manifest(output: Path) -> None:
    rows = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.sha256" or "__pycache__" in path.parts:
            continue
        rows.append(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
            f"{path.relative_to(output).as_posix()}"
        )
    (output / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")


def build_release(output: Path) -> int:
    """Build accepted v0.21.0 without modifying the immutable v0.20.0 baseline."""

    if output.exists() and any(output.iterdir()):
        raise ValueError(f"release output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    schema_dir = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted((BASELINE / "schemas" / f"v{BASELINE_VERSION}").glob("*.json")):
        schema = _replace_version(_load(source))
        if source.name == "common.schema.json":
            _extend_reportless_finding_materiality(schema)
        if source.name in {
            "detector-qualification.schema.json",
            "qualification-metric-set.schema.json",
        }:
            _extend_detector_identity_pairs(schema)
        _write_json(schema_dir / source.name, schema)

    catalog = _replace_version(_load(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _write_json(output / "schema-catalog.json", catalog)

    for source in sorted((BASELINE / "examples").glob("*.json")):
        _write_json(output / "examples" / source.name, _replace_version(_load(source)))
    qualification, metric_set = _code_examples()
    _write_json(
        output / "examples/detector-qualification.code-csv-dependence.example.json",
        qualification,
    )
    _write_json(
        output / "examples/qualification-metric-set.code-csv-dependence.example.json",
        metric_set,
    )

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        f"# sc-referee public schemas v{RELEASE_VERSION}\n\n"
        "Accepted forward-only schema release implementing the ADR-0076 code-lane amendment. "
        "It preserves the generic and code-lane 2.1.0 identities and adds the exact code-CSV "
        "dependence detector 3.1.0 identity for binding-scoped qualification records. "
        "Schema validity alone grants no Finding authority.\n",
        encoding="utf-8",
    )
    (output / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## {RELEASE_VERSION} — {RELEASE_DATE}\n\n"
        "- Added detector:bounded-code-csv-dependence-conflict 3.1.0 to "
        "binding-scoped DetectorQualification and QualificationMetricSet records.\n"
        "- Preserved detector:bounded-code-csv-dependence-conflict 2.1.0 and "
        "detector:bounded-analysis-method-conflict 0.3.0 while rejecting cross-paired "
        "detector IDs and versions.\n"
        f"- Preserved v{BASELINE_VERSION} byte-for-byte as the immutable migration baseline.\n",
        encoding="utf-8",
    )
    (output / "CONTROLLER_INVARIANTS.md").write_text(
        f"# Controller invariants for v{RELEASE_VERSION}\n\n"
        "- Code-lane and generic method-conflict detector IDs are paired only with their exact "
        "2.1.0/3.1.0 and 0.3.0 versions.\n"
        "- Binding, check, detector, adapter, Finding profile, qualification, metric, threshold, "
        "and installed pin identities must all match before Finding admission.\n"
        "- Schema representation alone installs no grant and grants no Finding authority.\n"
        "- Migration never invents review, scientific approval, qualification, or Finding authority.\n",
        encoding="utf-8",
    )
    (output / f"MIGRATION_v{BASELINE_VERSION}_to_v{RELEASE_VERSION}.md").write_text(
        f"# Migration from v{BASELINE_VERSION} to v{RELEASE_VERSION}\n\n"
        "Ordinary public records receive the new schema version with no semantic projection. "
        "Existing installed generic method-conflict qualification and metric records may be "
        "restamped only when every non-version byte and external grant identity remains fixed. "
        "Immutable v0.19.0 method-contract parent locks remain byte-identical and are validated "
        "against the co-installed v0.19.0 schema package before a v0.21.0 child audit is derived. "
        "The code-CSV dependence qualification is newly representable only under its exact "
        "detector 3.1.0 identity; the historical 2.1.0 identity remains representable and "
        "cross-paired detector versions are refused.\n",
        encoding="utf-8",
    )
    _write_json(
        output / "RELEASE_STATUS.json",
        {
            "accepted": True,
            "baseline_version": BASELINE_VERSION,
            "public_release": True,
            "release_version": RELEASE_VERSION,
            "source_adrs": [SOURCE_ADR],
        },
    )

    tests = output / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    for source in sorted((BASELINE / "tests").glob("*.py")):
        if source.name == "test_v020_invariants.py":
            continue
        text = source.read_text(encoding="utf-8")
        text = text.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}").replace(
            BASELINE_VERSION, RELEASE_VERSION
        )
        (tests / source.name).write_text(text, encoding="utf-8")
    (tests / "test_v021_invariants.py").write_text(_release_tests(), encoding="utf-8")

    validator = (BASELINE / "tools/validate_records.py").read_text(encoding="utf-8")
    (output / "tools").mkdir(parents=True, exist_ok=True)
    (output / "tools/validate_records.py").write_text(
        validator.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}").replace(
            BASELINE_VERSION, RELEASE_VERSION
        ),
        encoding="utf-8",
    )
    (output / "pyproject.toml").write_text(
        (BASELINE / "pyproject.toml")
        .read_text(encoding="utf-8")
        .replace(BASELINE_VERSION, RELEASE_VERSION),
        encoding="utf-8",
    )

    schema_count = len(catalog["schemas"])
    example_count = len(list((output / "examples").glob("*.json")))
    test_count = 0
    for path in tests.glob("*.py"):
        module = ast.parse(path.read_text(encoding="utf-8"))
        test_count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in module.body
        )
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
    _write_manifest(output)
    return example_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.21.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
