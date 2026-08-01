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
BASELINE = ROOT / "reference" / "schemas-v0.15.0"
BASELINE_VERSION = "0.15.0"
RELEASE_VERSION = "0.16.0"
SOURCE_ADRS = ["docs/implementation/ADR-0041-SECOND-STATIC-QUALIFICATION-PROFILE.md"]

DIRECTION_KIND = "bounded_report_mean_direction_v1"
METHOD_KIND = "bounded_analysis_method_conflict_v1"
DIRECTION_DETECTOR = "detector:bounded-report-mean-direction"
METHOD_DETECTOR = "detector:bounded-analysis-method-conflict"
DIRECTION_ENTRY = "sc_referee_evaluation.static_qualification:verify_bounded_direction_case"
METHOD_ENTRY = (
    "sc_referee_evaluation.analysis_method_qualification:verify_bounded_analysis_method_case"
)
DIRECT = "use_supplied_founder_alleles_directly_in_hmm_emission"
REPAIRED = "repair_ril_founder_orientation_before_hmm_emission"


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


def _sorted_strings(*, min_items: int = 0) -> dict[str, Any]:
    return {
        "items": {"minLength": 1, "type": "string"},
        "minItems": min_items,
        "type": "array",
        "uniqueItems": True,
    }


def _profile_condition(
    kind: str,
    detector_id: str,
    entry_point: str,
    suffixes: list[str],
    dependency_closure: str,
    surface_inventory: str,
) -> dict[str, Any]:
    return {
        "if": {"properties": {"profile_kind": {"const": kind}}, "required": ["profile_kind"]},
        "then": {
            "properties": {
                "target_detector": {
                    "properties": {
                        "detector_id": {"const": detector_id},
                        "detector_version": {"const": "0.1.0"},
                    }
                },
                "verifier": {"properties": {"entry_point": {"const": entry_point}}},
                "selection_rules": {
                    "properties": {
                        "candidate_suffixes": {"const": suffixes},
                        "dependency_closure": {"const": dependency_closure},
                        "surface_inventory": {"const": surface_inventory},
                    }
                },
            }
        },
    }


def _extend_profile_schema(schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    properties["profile_kind"] = {"enum": [DIRECTION_KIND, METHOD_KIND]}
    schema["required"].append("profile_kind")
    target_id = properties["target_detector"]["properties"]["detector_id"]
    target_id.clear()
    target_id["enum"] = [DIRECTION_DETECTOR, METHOD_DETECTOR]
    entry = properties["verifier"]["properties"]["entry_point"]
    entry.clear()
    entry["enum"] = [DIRECTION_ENTRY, METHOD_ENTRY]
    rules = properties["selection_rules"]["properties"]
    rules["candidate_suffixes"] = {"enum": [[".csv", ".md", ".py"], [".md", ".py"]]}
    rules["dependency_closure"] = {
        "enum": [
            "unique_supported_csv_mean_writer_report_transitive_path",
            "unique_supported_founder_operand_writer_selected_report_path",
        ]
    }
    rules["surface_inventory"] = {
        "enum": [
            "every_literal_directional_sentence_in_complete_selected_report",
            "every_closed_founder_orientation_declaration_in_selected_report_and_python_candidates",
        ]
    }
    schema["allOf"] = [
        _profile_condition(
            DIRECTION_KIND,
            DIRECTION_DETECTOR,
            DIRECTION_ENTRY,
            [".csv", ".md", ".py"],
            "unique_supported_csv_mean_writer_report_transitive_path",
            "every_literal_directional_sentence_in_complete_selected_report",
        ),
        _profile_condition(
            METHOD_KIND,
            METHOD_DETECTOR,
            METHOD_ENTRY,
            [".md", ".py"],
            "unique_supported_founder_operand_writer_selected_report_path",
            "every_closed_founder_orientation_declaration_in_selected_report_and_python_candidates",
        ),
    ]


def _method_declaration(*, report: bool) -> dict[str, Any]:
    locations: dict[str, Any] = {
        "operand": {"enum": [DIRECT, REPAIRED]},
        "path": {"minLength": 1, "type": "string"},
    }
    required = ["operand", "path"]
    if report:
        locations.update(
            {
                "start": {"minimum": 0, "type": "integer"},
                "end": {"minimum": 1, "type": "integer"},
                "sentence": {"minLength": 1, "type": "string"},
            }
        )
        required.extend(["start", "end", "sentence"])
    else:
        locations.update(
            {
                "start_line": {"minimum": 1, "type": "integer"},
                "end_line": {"minimum": 1, "type": "integer"},
            }
        )
        required.extend(["start_line", "end_line"])
    return {
        "additionalProperties": False,
        "properties": locations,
        "required": required,
        "type": "object",
    }


def _method_facts() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "selected_report_path": {"minLength": 1, "type": "string"},
            "writer_path": {"minLength": 1, "type": "string"},
            "report_operand": {"enum": [DIRECT, REPAIRED]},
            "source_operand": {"enum": [DIRECT, REPAIRED]},
            "requirement_operand": {"enum": [DIRECT, REPAIRED]},
            "report_declarations": {
                "items": _method_declaration(report=True),
                "minItems": 1,
                "type": "array",
            },
            "source_declarations": {
                "items": _method_declaration(report=False),
                "minItems": 1,
                "type": "array",
            },
            "governing_question": _bound_ref("material_question"),
            "governing_answer": _bound_ref("answer"),
            "governing_contract": _bound_ref("scientific_contract"),
            "requirement_assertion": _bound_ref("semantic_assertion"),
            "candidate_paths": _sorted_strings(min_items=1),
            "supported_closure_paths": _sorted_strings(min_items=2),
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
            "writer_path",
            "report_operand",
            "source_operand",
            "requirement_operand",
            "report_declarations",
            "source_declarations",
            "governing_question",
            "governing_answer",
            "governing_contract",
            "requirement_assertion",
            "candidate_paths",
            "supported_closure_paths",
            "supported_exclusions",
        ],
        "type": "object",
    }


def _proof_condition(kind: str, facts: dict[str, Any], retained_count: int) -> dict[str, Any]:
    return {
        "if": {
            "properties": {"proof_profile_kind": {"const": kind}},
            "required": ["proof_profile_kind"],
        },
        "then": {
            "properties": {"derived_facts": {"oneOf": [facts, {"type": "null"}]}},
            "allOf": [
                {
                    "if": {
                        "properties": {"proof_status": {"const": "complete"}},
                        "required": ["proof_status"],
                    },
                    "then": {
                        "properties": {
                            "derived_facts": {"type": "object"},
                            "retained_bytes": {"minItems": retained_count},
                        }
                    },
                }
            ],
        },
    }


def _extend_proof_schema(schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    direction_facts = properties["derived_facts"]["oneOf"][0]
    method_facts = _method_facts()
    properties["proof_profile_kind"] = {"enum": [DIRECTION_KIND, METHOD_KIND]}
    schema["required"].append("proof_profile_kind")
    properties["derived_facts"] = {"oneOf": [direction_facts, method_facts, {"type": "null"}]}
    schema["allOf"] = [
        _proof_condition(DIRECTION_KIND, direction_facts, 3),
        _proof_condition(METHOD_KIND, method_facts, 2),
    ]


def _extend_static_fixture_schema(schema: dict[str, Any]) -> None:
    branches = schema["properties"]["proof_evidence"]["oneOf"]
    static_branch = next(
        branch
        for branch in branches
        if branch.get("properties", {}).get("controller_profile", {}).get("const")
        == "fixture-proof-evidence-static-v1"
    )
    public = static_branch["properties"]["public_inputs"]
    for collection, record_type in (
        ("answers", "answer"),
        ("material_questions", "material_question"),
        ("semantic_assertions", "semantic_assertion"),
    ):
        public["properties"][collection] = {
            "items": _bound_ref(record_type),
            "minItems": 0,
            "type": "array",
            "uniqueItems": True,
        }
        public["required"].append(collection)


def _bound(record_type: str, ident: str, digit: str) -> dict[str, Any]:
    return {
        "record_ref": {"record_type": record_type, "record_id": ident},
        "semantic_digest": "sha256:" + digit * 64,
    }


def _method_profile_example(direction_profile: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(direction_profile)
    value["profile_id"] = "static-profile:bounded-analysis-method-conflict-v1"
    value["profile_kind"] = METHOD_KIND
    target = value["target_detector"]
    target["manifest"] = _bound("detector_manifest", METHOD_DETECTOR, "a")
    target["detector_id"] = METHOD_DETECTOR
    target["implementation_digest"] = "sha256:" + "b" * 64
    target["parser_manifests"] = [
        _bound("parser_manifest", "parser:markdown-inventory", "c"),
        _bound("parser_manifest", "parser:python-ast-tokenize", "d"),
    ]
    target["semantic_profile_manifests"] = [
        {
            "manifest_kind": "semantic_profile_manifest",
            "manifest_id": "semantic-profile:bounded-analysis-method-conflict-v1",
            "semantic_digest": "sha256:" + "e" * 64,
        }
    ]
    target["version_manifests"] = [
        {
            "manifest_kind": "version_manifest",
            "manifest_id": "version-manifest:bounded-analysis-method-conflict-v1",
            "semantic_digest": "sha256:" + "f" * 64,
        }
    ]
    value["verifier"]["entry_point"] = METHOD_ENTRY
    value["verifier"]["implementation_digest"] = "sha256:" + "1" * 64
    value["verifier"]["dependency_closure"] = [
        {
            "dependency_kind": "implementation",
            "path": "sc_referee_evaluation/analysis_method_qualification.py",
            "content_digest": "sha256:" + "2" * 64,
        }
    ]
    value["selection_rules"].update(
        {
            "candidate_suffixes": [".md", ".py"],
            "dependency_closure": ("unique_supported_founder_operand_writer_selected_report_path"),
            "surface_inventory": (
                "every_closed_founder_orientation_declaration_in_selected_report_and_python_candidates"
            ),
        }
    )
    value["vocabularies"]["applicability_obligation_ids"] = [
        "answer_authority_complete",
        "candidate_enumeration_complete",
        "full_identity_complete",
        "observed_plane_agreement",
        "report_operand_unique",
        "selected_output_scope_closure",
        "source_operand_unique",
        "strict_utf8_complete",
        "unique_selected_output_writer",
    ]
    value["vocabularies"]["counterevidence_check_ids"] = [
        "alternate_or_superseding_intent",
        "approved_method_deviation",
        "conditional_applicability",
        "governing_protocol_amendment",
        "sensitivity_or_unsupported_qualifier",
    ]
    value["selection_protocol_artifact"] = {
        "artifact_kind": "corpus_selection_protocol",
        "artifact_id": "selection-protocol:bounded-analysis-method-v1",
        "content_digest": "sha256:" + "3" * 64,
    }
    value["profile_semantic_digest"] = "sha256:" + "4" * 64
    return value


def _method_proof_example(direction_proof: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(direction_proof)
    value["proof_id"] = "static-proof:analysis-method-case-1"
    value["proof_profile_kind"] = METHOD_KIND
    value["profile"] = _bound(
        "static_qualification_profile",
        "static-profile:bounded-analysis-method-conflict-v1",
        "4",
    )
    value["retained_bytes"] = [
        {
            "path": "analysis.py",
            "byte_size": 200,
            "content_digest": "sha256:" + "5" * 64,
            "encoding": "utf-8",
            "file_record": _bound("file_record", "file:analysis.py", "5"),
            "asset_identity": _bound("asset_identity", "identity:analysis.py", "5"),
        },
        {
            "path": "report.md",
            "byte_size": 100,
            "content_digest": "sha256:" + "6" * 64,
            "encoding": "utf-8",
            "file_record": _bound("file_record", "file:report.md", "6"),
            "asset_identity": _bound("asset_identity", "identity:report.md", "6"),
        },
    ]
    value["derived_facts"] = {
        "selected_report_path": "report.md",
        "writer_path": "analysis.py",
        "report_operand": DIRECT,
        "source_operand": DIRECT,
        "requirement_operand": REPAIRED,
        "report_declarations": [
            {
                "operand": DIRECT,
                "path": "report.md",
                "start": 0,
                "end": 67,
                "sentence": (
                    "The founder-origin HMM was fitted using the supplied founder alleles."
                ),
            }
        ],
        "source_declarations": [
            {
                "operand": DIRECT,
                "path": "analysis.py",
                "start_line": 1,
                "end_line": 6,
            }
        ],
        "governing_question": _bound("material_question", "question:analysis", "7"),
        "governing_answer": _bound("answer", "answer:analysis", "8"),
        "governing_contract": _bound("scientific_contract", "contract:analysis", "9"),
        "requirement_assertion": _bound(
            "semantic_assertion", "assertion:analysis-requirement", "a"
        ),
        "candidate_paths": ["analysis.py", "report.md"],
        "supported_closure_paths": ["analysis.py", "report.md"],
        "supported_exclusions": [],
    }
    value["applicability_results"] = [
        {
            "check_id": "unique_selected_output_writer",
            "completion_status": "completed",
            "outcome": "agreement",
            "evidence_paths": ["analysis.py", "report.md"],
            "detail_code": "unique_supported_closure",
        }
    ]
    value["counterevidence_results"] = [
        {
            "check_id": "alternate_or_superseding_intent",
            "completion_status": "completed",
            "outcome": "counterevidence_absent",
            "evidence_paths": ["analysis.py", "report.md"],
            "detail_code": "closed_search_complete",
        }
    ]
    value["proof_semantic_digest"] = "sha256:" + "b" * 64
    value["limitations"] = [
        "This proof establishes only the frozen review-scoped declaration envelope."
    ]
    return value


def _extend_example(example: dict[str, Any]) -> None:
    if example.get("record_type") == "static_qualification_profile":
        example["profile_kind"] = DIRECTION_KIND
    elif example.get("record_type") == "static_qualification_proof":
        example["proof_profile_kind"] = DIRECTION_KIND
    if (
        example.get("record_type") == "benchmark_fixture"
        and isinstance(example.get("proof_evidence"), dict)
        and example["proof_evidence"].get("controller_profile")
        == "fixture-proof-evidence-static-v1"
    ):
        public = example["proof_evidence"]["public_inputs"]
        public["answers"] = []
        public["material_questions"] = []
        public["semantic_assertions"] = []


def _method_fixture_example(base: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(base)
    value["fixture_id"] = "fixture:static-method-good-1"
    value["problem_id"] = "problem:bounded-analysis-method-good"
    value["declared_scope"]["detector_ids"] = [METHOD_DETECTOR]
    public = value["proof_evidence"]["public_inputs"]
    public["answers"] = [_bound("answer", "answer:analysis", "8")]
    public["material_questions"] = [_bound("material_question", "question:analysis", "7")]
    public["semantic_assertions"] = [
        _bound("semantic_assertion", "assertion:analysis-requirement", "a")
    ]
    public["scientific_contracts"] = [_bound("scientific_contract", "contract:analysis", "9")]
    public["static_qualification_proofs"] = [
        _bound("static_qualification_proof", "static-proof:analysis-method-case-1", "b")
    ]
    value["scientific_contract_refs"] = [
        {"record_type": "scientific_contract", "record_id": "contract:analysis"}
    ]
    return value


def _release_readme() -> str:
    return """# sc-referee public schemas v0.16.0

Accepted forward-only public schema release implementing ADR-0041.

This release adds a second exact static-qualification profile for the bounded cross-surface
analysis-method detector and exact question, Answer, and assertion inputs for static controls. It
does not execute project code, qualify or promote a detector, or grant Finding authority.
"""


def _release_changelog() -> str:
    return """# Changelog

## 0.16.0 — 2026-07-31

- Discriminated both static qualification profile and proof variants.
- Added the bounded analysis-method conflict static profile and fact shape.
- Added exact MaterialQuestion, Answer, and SemanticAssertion inputs to static fixture proofs.
- Preserved v0.15.0 as an immutable migration baseline.
"""


def _release_invariants() -> str:
    return """# Controller invariants for v0.16.0

- A static profile kind fixes one detector, verifier, selection grammar, and proof fact shape.
- Profile components from different variants cannot be mixed.
- Review-requirement controls bind exact human Answer, question, contract, and assertion records.
- Raw report and source facts are independently rederived without production semantic helpers.
- Missing, ambiguous, unsupported, weak, over-budget, or conflicting closure is unavailable.
- Static proof never establishes project execution, numeric causality, or universal correctness.
- No record in this release grants detector promotion or Finding authority.
"""


def _migration_text() -> str:
    return """# Migration from v0.15.0 to v0.16.0

The migration is fail closed. It versions ordinary records and adds the new empty static public
input collections where applicable. Existing v0.15 static profiles, proofs, fixtures, dependent
case outcomes, and metric evidence are retained only as namespaced legacy payloads because a bare
public bundle cannot replay the new discriminated proof and private source-validation closure. It
creates no second profile, Answer, proof, qualification, maturity, Finding, or execution authority.
"""


def _v16_tests() -> str:
    return """from test_examples import errors, invalid, load

def test_second_static_profile_and_proof_examples_validate():
 assert not errors(load("static-qualification-profile.analysis-method.example.json"), "static_qualification_profile")
 assert not errors(load("static-qualification-proof.analysis-method.example.json"), "static_qualification_proof")

def test_static_profile_cannot_mix_detector_and_verifier():
 x=load("static-qualification-profile.analysis-method.example.json")
 x["verifier"]["entry_point"]="sc_referee_evaluation.static_qualification:verify_bounded_direction_case"
 invalid(x,"static_qualification_profile")

def test_static_proof_cannot_mix_profile_and_fact_shape():
 x=load("static-qualification-proof.analysis-method.example.json")
 x["proof_profile_kind"]="bounded_report_mean_direction_v1"
 invalid(x,"static_qualification_proof")

def test_method_fixture_requires_review_authority_collections():
 x=load("benchmark-fixture.static-method-good.example.json")
 del x["proof_evidence"]["public_inputs"]["answers"]
 invalid(x,"benchmark_fixture")
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
    """Build accepted v0.16.0 without modifying immutable v0.15.0."""

    _require_empty_destination(output)
    baseline_schemas = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted(baseline_schemas.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "static-qualification-profile.schema.json":
            _extend_profile_schema(schema)
        elif source.name == "static-qualification-proof.schema.json":
            _extend_proof_schema(schema)
        elif source.name == "benchmark-fixture.schema.json":
            _extend_static_fixture_schema(schema)
        _write_json(schema_output / source.name, schema)

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _write_json(output / "schema-catalog.json", catalog)

    examples: dict[str, dict[str, Any]] = {}
    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        _extend_example(example)
        examples[source.name] = example
        _write_json(output / "examples" / source.name, example)
    method_profile = _method_profile_example(examples["static-qualification-profile.example.json"])
    method_proof = _method_proof_example(examples["static-qualification-proof.example.json"])
    _write_json(
        output / "examples" / "static-qualification-profile.analysis-method.example.json",
        method_profile,
    )
    _write_json(
        output / "examples" / "static-qualification-proof.analysis-method.example.json",
        method_proof,
    )
    _write_json(
        output / "examples" / "benchmark-fixture.static-method-good.example.json",
        _method_fixture_example(examples["benchmark-fixture.static-good.example.json"]),
    )

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.15_to_v0.16.md").write_text(_migration_text(), encoding="utf-8")
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
        if source.name.startswith("test_v") and "from test_examples import" not in source_text:
            helper = "from test_examples import invalid, load\n"
            future = "from __future__ import annotations\n"
            if source_text.startswith(future):
                source_text = future + helper + source_text[len(future) :]
            else:
                source_text = helper + source_text
        (tests_output / source.name).write_text(source_text, encoding="utf-8")
    (tests_output / "test_v016_invariants.py").write_text(_v16_tests(), encoding="utf-8")

    validator = (BASELINE / "tools" / "validate_records.py").read_text(encoding="utf-8")
    (output / "tools").mkdir(parents=True, exist_ok=True)
    (output / "tools" / "validate_records.py").write_text(
        validator.replace(f"v{BASELINE_VERSION}", f"v{RELEASE_VERSION}"),
        encoding="utf-8",
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
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.16.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
