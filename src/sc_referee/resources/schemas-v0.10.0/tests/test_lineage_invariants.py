from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "v0.10.0"
EXAMPLES = ROOT / "examples"
CATALOG = json.loads((ROOT / "schema-catalog.json").read_text(encoding="utf-8"))
REGISTRY = Registry()
SCHEMAS = {}
ALIASES = {}
for item in CATALOG["schemas"]:
    schema = json.loads((SCHEMA_DIR / item["file"]).read_text(encoding="utf-8"))
    REGISTRY = REGISTRY.with_resource(schema["$id"], Resource.from_contents(schema))
    SCHEMAS[schema["$id"]] = schema
    ALIASES[item["name"]] = schema["$id"]


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def errors(value: dict, alias: str) -> list:
    schema = SCHEMAS[ALIASES[alias]]
    return list(
        validator_for(schema)(
            schema, registry=REGISTRY, format_checker=FormatChecker()
        ).iter_errors(value)
    )


def invalid(value: dict, alias: str) -> None:
    assert errors(value, alias)


def test_lineage_plane_examples_validate() -> None:
    for name in (
        "data-asset.example.json",
        "variable.example.json",
        "analysis-decision.example.json",
        "selection-envelope.example.json",
        "environment.example.json",
        "execution.auditor-verification.example.json",
        "claim.lineage-mixed.example.json",
        "claim.lineage-complete.example.json",
    ):
        value = load(name)
        assert not errors(value, value["record_type"]), name


def test_complete_aggregate_requires_all_six_complete_grades() -> None:
    value = load("claim.lineage-complete.example.json")
    value["lineage"]["grades"]["execution_origin"] = {
        "status": "missing",
        "record_refs": [],
        "source_refs": [],
        "limitations": ["No project execution was observed."],
    }
    invalid(value, "claim")


def test_all_complete_grades_require_complete_aggregate() -> None:
    value = load("claim.lineage-complete.example.json")
    value["lineage"]["status"] = "partial"
    invalid(value, "claim")


def test_missing_aggregate_forbids_positive_grade() -> None:
    value = load("claim.lineage-mixed.example.json")
    value["lineage"]["status"] = "missing"
    invalid(value, "claim")


def test_unavailable_aggregate_requires_every_grade_unavailable() -> None:
    value = load("claim.lineage-mixed.example.json")
    value["lineage"]["status"] = "unavailable"
    invalid(value, "claim")


def test_noncomplete_grade_requires_a_limitation() -> None:
    value = load("claim.lineage-mixed.example.json")
    value["lineage"]["grades"]["semantic_origin"]["limitations"] = []
    invalid(value, "claim")


def test_unresolved_variable_cannot_claim_semantic_assertion() -> None:
    value = load("variable.example.json")
    value["semantic_assertion_refs"] = [
        {"record_type": "semantic_assertion", "record_id": "assertion:invented"}
    ]
    invalid(value, "variable")


def test_complete_selection_envelope_cannot_hide_a_limitation() -> None:
    value = load("selection-envelope.example.json")
    value["limitations"] = ["An alternative may be missing."]
    invalid(value, "selection_envelope")


def test_auditor_execution_cannot_be_project_execution() -> None:
    value = load("execution.auditor-verification.example.json")
    value["sandbox"]["project_code_executed"] = True
    invalid(value, "execution")
    value = load("execution.auditor-verification.example.json")
    value["sandbox"]["authorization_status"] = "authorized"
    invalid(value, "execution")


def test_project_execution_requires_authority_and_sandbox_capability() -> None:
    value = copy.deepcopy(load("execution.auditor-verification.example.json"))
    value["execution_kind"] = "project_workflow"
    value["actor"] = "project_workflow"
    value["sandbox"]["project_code_executed"] = True
    value["sandbox"]["authorization_status"] = "authorized"
    invalid(value, "execution")
    value["sandbox"]["sandbox_capability_ref"] = {
        "record_type": "sandbox_capability",
        "record_id": "sandbox:rootless-oci",
    }
    assert not errors(value, "execution")


def test_bundle_requires_all_lineage_plane_arrays() -> None:
    for array_name in (
        "data_assets",
        "variables",
        "analysis_decisions",
        "selection_envelopes",
        "executions",
        "environments",
    ):
        value = load("audit-bundle.example.json")
        value.pop(array_name)
        invalid(value, "audit_bundle")


def test_coverage_requires_six_grade_count_dimensions() -> None:
    value = load("coverage-record.example.json")
    value["claim_coverage"]["lineage_grade_counts"].pop("semantic_origin")
    invalid(value, "coverage_record")
