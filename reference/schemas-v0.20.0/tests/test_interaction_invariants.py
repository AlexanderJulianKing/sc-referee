from __future__ import annotations

import json
from pathlib import Path

from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "v0.20.0"
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


def test_interaction_examples_validate() -> None:
    for name in (
        "work-item.ready.example.json",
        "work-item.completed.example.json",
        "answer.candidate-selection.example.json",
        "answer.structured.example.json",
    ):
        value = load(name)
        assert not errors(value, value["record_type"]), name


def test_semantic_work_cannot_request_project_execution() -> None:
    value = load("work-item.ready.example.json")
    value["scheduling"]["execution_privilege"] = "project_code_execution"
    invalid(value, "work_item")


def test_work_packet_cannot_enable_open_ended_issue_discovery() -> None:
    value = load("work-item.ready.example.json")
    value["packet"]["policy"]["open_ended_issue_discovery"] = True
    invalid(value, "work_item")


def test_completed_work_requires_output_and_completion_time() -> None:
    value = load("work-item.completed.example.json")
    value["output_refs"] = []
    value.pop("completed_at")
    invalid(value, "work_item")


def test_awaiting_answer_requires_material_question() -> None:
    value = load("work-item.ready.example.json")
    value["status"] = "awaiting_answer"
    invalid(value, "work_item")


def test_scientist_answer_requires_human_respondent() -> None:
    value = load("answer.candidate-selection.example.json")
    value["respondent"]["actor_kind"] = "model"
    invalid(value, "answer")


def test_candidate_selection_requires_selected_option() -> None:
    value = load("answer.candidate-selection.example.json")
    value.pop("selected_option_id")
    invalid(value, "answer")


def test_available_answer_timestamp_requires_value() -> None:
    value = load("answer.candidate-selection.example.json")
    value.pop("answered_at")
    invalid(value, "answer")


def test_unavailable_answer_timestamp_forbids_invented_value() -> None:
    value = load("answer.structured.example.json")
    value["answered_at"] = "2026-07-28T21:06:00Z"
    invalid(value, "answer")


def test_new_prelock_audit_states_require_snapshot() -> None:
    value = load("audit-run.terminal.example.json")
    value["state"] = "semantics_proposed"
    value.pop("terminal_reason")
    assert not errors(value, "audit_run")
    value.pop("snapshot_ref")
    invalid(value, "audit_run")


def test_bundle_requires_interaction_arrays() -> None:
    value = load("audit-bundle.example.json")
    value.pop("work_items")
    invalid(value, "audit_bundle")
    value = load("audit-bundle.example.json")
    value.pop("answers")
    invalid(value, "audit_bundle")
