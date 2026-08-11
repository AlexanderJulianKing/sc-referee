from __future__ import annotations

import argparse
import ast
import hashlib
import shutil
from pathlib import Path
from typing import Any

from scripts.build_method_promotion_schema_candidate import (
    BASELINE,
    BASELINE_VERSION,
    CANDIDATE_VERSION,
    SOURCE_ADR,
    _extend_detector_qualification,
    _extend_metric_set,
    _extend_static_profile,
    _extend_static_proof,
    _read_json,
    _replace_version,
    _transform_example,
    _write_json,
)

RELEASE_VERSION = CANDIDATE_VERSION
SOURCE_ADRS = [SOURCE_ADR]
RELEASE_DATE = "2026-08-11"


def _maintainer_approval_schema() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "actor": {
                "$ref": (
                    f"https://w3id.org/sc-referee/schema/v{RELEASE_VERSION}/"
                    "common.schema.json#/$defs/Actor"
                )
            },
            "approved_on": {
                "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
                "type": "string",
            },
            "decision_ref": {
                "pattern": "^docs/implementation/ADR-[0-9]{4}-[A-Z0-9-]+[.]md$",
                "type": "string",
            },
        },
        "required": ["actor", "approved_on", "decision_ref"],
        "type": "object",
    }


def _move_review_evidence_constraints(schema: dict[str, Any]) -> None:
    """Make path-valued evaluation evidence the required promotion review basis."""

    for branch in schema["allOf"]:
        then_properties = branch.get("then", {}).get("properties", {})
        agent_constraint = then_properties.get("agent_adjudication_refs")
        if not isinstance(agent_constraint, dict) or "minItems" not in agent_constraint:
            continue
        minimum = agent_constraint.pop("minItems")
        if not agent_constraint:
            del then_properties["agent_adjudication_refs"]
        evaluation_constraint = then_properties.setdefault("evaluation_refs", {})
        evaluation_constraint["minItems"] = minimum


def _extend_release_qualification(schema: dict[str, Any]) -> None:
    _extend_detector_qualification(schema)
    _move_review_evidence_constraints(schema)
    schema["properties"]["software_maintainer_approvals"]["items"] = _maintainer_approval_schema()
    object_branch = next(
        branch
        for branch in schema["properties"]["static_scope_disclosure"]["oneOf"]
        if branch.get("type") == "object"
    )
    object_branch["properties"]["stage3_comparison_artifact_exists"] = {"type": "boolean"}
    object_branch["required"].append("stage3_comparison_artifact_exists")


def _transform_release_example(name: str, value: dict[str, Any]) -> None:
    _transform_example(name, value)
    if value.get("record_type") != "detector_qualification":
        return
    approvals = value["software_maintainer_approvals"]
    value["software_maintainer_approvals"] = [
        {
            "actor": approval,
            "approved_on": RELEASE_DATE,
            "decision_ref": SOURCE_ADR,
        }
        for approval in approvals
    ]


def _release_tests() -> str:
    return """from test_examples import errors, invalid, load


def test_maintainer_approval_is_dated_and_decision_bound():
 x=load("detector-qualification.example.json")
 x["software_maintainer_approvals"][0].pop("approved_on")
 invalid(x,"detector_qualification")


def test_flattened_maintainer_actor_is_refused():
 x=load("detector-qualification.example.json")
 x["software_maintainer_approvals"]=[x["software_maintainer_approvals"][0]["actor"]]
 invalid(x,"detector_qualification")


def test_maintainer_decision_ref_is_an_adr_path():
 x=load("detector-qualification.example.json")
 x["software_maintainer_approvals"][0]["decision_ref"]="not-an-adr"
 invalid(x,"detector_qualification")


def test_agent_review_paths_belong_in_evaluation_refs():
 x=load("detector-qualification.example.json")
 x["agent_adjudication_refs"]=[]
 assert not errors(x,"detector_qualification")
 x["evaluation_refs"]=[]
 invalid(x,"detector_qualification")


def test_static_scope_disclosure_states_stage3_artifact_status():
 x=load("detector-qualification.example.json")
 x["qualification_proof_families"]=["static_closed_scope"]
 x["static_scope_disclosure"]={
  "profile_refs":[{"record_type":"static_qualification_profile","record_id":"static-profile:test"}],
  "scope_statement":"One closed static scope.",
  "execution_claimed":False,
  "global_correctness_claimed":False,
  "stage3_comparison_artifact_exists":False,
 }
 assert not errors(x,"detector_qualification")
 x["static_scope_disclosure"].pop("stage3_comparison_artifact_exists")
 invalid(x,"detector_qualification")
"""


def _write_manifest(output: Path) -> None:
    entries: list[str] = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path.name == "MANIFEST.sha256" or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(output).as_posix()
        entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}")
    (output / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def _accepted_readme() -> str:
    return f"""# sc-referee public schemas v{RELEASE_VERSION}

Accepted forward-only public schema release implementing ADR-0061. It represents exact
detector-v0.3 per-binding qualification and promotion evidence, dated maintainer decisions, and
the disclosed presence or absence of a Stage-3 comparison artifact. A conforming record alone
installs no qualification grant and grants no Finding authority.
"""


def _changelog() -> str:
    return f"""# Changelog

## {RELEASE_VERSION} — {RELEASE_DATE}

- Added exact detector-v0.3 binding scopes and pilot-informed numeric threshold policies.
- Added dated, decision-bound `MaintainerApproval` objects.
- Added the closed `stage3_comparison_artifact_exists` disclosure field.
- Assigned path-valued review ledgers to `evaluation_refs`; `agent_adjudication_refs` remains
  reserved for typed adjudication records.
- Preserved v{BASELINE_VERSION} as an immutable migration baseline.
"""


def _controller_invariants() -> str:
    return f"""# Controller invariants for v{RELEASE_VERSION}

- Binding, check, detector, profile, adapter, and threshold-policy identities are exact and
  content-addressed before any promotion can be considered.
- Path-valued evaluation ledgers are carried by `evaluation_refs`; they are never represented as
  invented typed adjudication records.
- Every software-maintainer approval identifies its actor, approval date, and governing ADR.
- Static-scope evidence explicitly discloses whether a Stage-3 comparison artifact exists.
- Schema validity is representation only: an independently installed, matching grant and all
  controller admission gates remain necessary for production Finding authority.
- Migration never invents review, scientific approval, qualification, or Finding authority.
"""


def _migration_notes() -> str:
    return f"""# Migration from v{BASELINE_VERSION} to v{RELEASE_VERSION}

Ordinary public records receive the new schema version and historical qualification records gain
null binding scopes while retaining deferred threshold policy and no promotion authority.

The two Round-1 private method-promotion record pairs require an explicit fail-closed re-stamp:
path-valued review ledgers move from `agent_adjudication_refs` to `evaluation_refs`; author ids are
derived from the digest-frozen authoring protocol; human-scientific approvals remain empty; the
non-schema `positive_issue` label is removed; maintainer actors are nested inside dated,
decision-bound approvals; and the Stage-3 artifact disclosure is retained. Private absolute-count
annotations remain external grant-pin gates rather than becoming self-certified threshold-policy
or safety-gate fields. The migration report records every such projection and creates no grant or
Finding authority.
"""


def _copy_release_tests(output: Path) -> int:
    tests_output = output / "tests"
    tests_output.mkdir(parents=True, exist_ok=True)
    for source in sorted((BASELINE / "tests").glob("*.py")):
        source_text = source.read_text(encoding="utf-8")
        source_text = source_text.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}").replace(
            BASELINE_VERSION, RELEASE_VERSION
        )
        if source.name == "test_examples.py":
            source_text = source_text.replace(
                "test_validated_qualification_needs_agent_adjudication",
                "test_validated_qualification_needs_evaluation_evidence",
            )
            source_text = source_text.replace(
                'x["agent_adjudication_refs"]=[]\n    invalid(x,"detector_qualification")',
                'x["evaluation_refs"]=[]\n    invalid(x,"detector_qualification")',
            )
        (tests_output / source.name).write_text(source_text, encoding="utf-8")
    (tests_output / "test_v019_invariants.py").write_text(_release_tests(), encoding="utf-8")

    test_count = 0
    for test_path in tests_output.glob("*.py"):
        module = ast.parse(test_path.read_text(encoding="utf-8"))
        test_count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in module.body
        )
    return test_count


def build_release(output: Path) -> int:
    """Build accepted v0.19.0 in an isolated destination without publishing it."""

    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Release output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)

    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted((BASELINE / "schemas" / f"v{BASELINE_VERSION}").glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "static-qualification-profile.schema.json":
            _extend_static_profile(schema)
        elif source.name == "static-qualification-proof.schema.json":
            _extend_static_proof(schema)
        elif source.name == "qualification-metric-set.schema.json":
            _extend_metric_set(schema)
        elif source.name == "detector-qualification.schema.json":
            _extend_release_qualification(schema)
        _write_json(schema_output / source.name, schema)

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _write_json(output / "schema-catalog.json", catalog)

    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        _transform_release_example(source.name, example)
        _write_json(output / "examples" / source.name, example)

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_accepted_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_controller_invariants(), encoding="utf-8")
    (output / f"MIGRATION_v{BASELINE_VERSION}_to_v{RELEASE_VERSION}.md").write_text(
        _migration_notes(), encoding="utf-8"
    )
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

    test_count = _copy_release_tests(output)
    validator = (BASELINE / "tools" / "validate_records.py").read_text(encoding="utf-8")
    (output / "tools").mkdir(parents=True, exist_ok=True)
    (output / "tools" / "validate_records.py").write_text(
        validator.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}").replace(
            BASELINE_VERSION, RELEASE_VERSION
        ),
        encoding="utf-8",
    )
    baseline_pyproject = (BASELINE / "pyproject.toml").read_text(encoding="utf-8")
    (output / "pyproject.toml").write_text(
        baseline_pyproject.replace(BASELINE_VERSION, RELEASE_VERSION), encoding="utf-8"
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
    _write_manifest(output)
    return example_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.19.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
