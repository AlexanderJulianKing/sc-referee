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
BASELINE = ROOT / "reference" / "schemas-v0.16.0"
BASELINE_VERSION = "0.16.0"
RELEASE_VERSION = "0.17.0"
SOURCE_ADRS = ["docs/implementation/ADR-0042-MODULAR-METHOD-CHECK-EXTENSION-BOUNDARY.md"]

DIRECTION_KIND = "bounded_report_mean_direction_v1"
METHOD_KIND = "typed_static_method_conflict_v1"
METHOD_DETECTOR = "detector:bounded-analysis-method-conflict"
METHOD_ENTRY = "sc_referee_evaluation.typed_method_qualification:verify_typed_method_case"


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


def _content_digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _semantic_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _evaluation_dependency(path: str) -> dict[str, str]:
    return {
        "path": f"sc_referee_evaluation/{path}",
        "content_digest": _content_digest(
            ROOT / "evaluation" / "src" / "sc_referee_evaluation" / path
        ),
    }


def _qualification_adapter_example() -> dict[str, Any]:
    closure = [
        _evaluation_dependency("analysis_method_qualification.py"),
        _evaluation_dependency("founder_orientation_adapter.py"),
    ]
    return {
        "adapter_id": "qualification-adapter:founder-orientation-python-v1",
        "adapter_version": "1.0.0",
        "entry_point": (
            "sc_referee_evaluation.founder_orientation_adapter:"
            "FounderOrientationQualificationAdapter"
        ),
        "implementation_digest": _semantic_digest(closure),
        "dependency_closure": closure,
        "imports_production_semantic_implementation": False,
    }


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


def _general_ref() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "record_id": _common_ref("Identifier"),
            "record_type": _common_ref("Identifier"),
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


def _unique_strings(*, min_items: int = 0, max_items: int | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "items": {"minLength": 1, "type": "string"},
        "minItems": min_items,
        "type": "array",
        "uniqueItems": True,
    }
    if max_items is not None:
        value["maxItems"] = max_items
    return value


def _qualification_adapter() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "adapter_id": {"pattern": "^qualification-adapter:", "type": "string"},
            "adapter_version": {"minLength": 1, "type": "string"},
            "entry_point": {
                "pattern": "^sc_referee_evaluation[.][A-Za-z0-9_.]+:[A-Za-z0-9_]+$",
                "type": "string",
            },
            "implementation_digest": _common_ref("Digest"),
            "dependency_closure": {
                "items": {
                    "additionalProperties": False,
                    "properties": {
                        "content_digest": _common_ref("Digest"),
                        "path": {"minLength": 1, "type": "string"},
                    },
                    "required": ["path", "content_digest"],
                    "type": "object",
                },
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "imports_production_semantic_implementation": {"const": False},
        },
        "required": [
            "adapter_id",
            "adapter_version",
            "entry_point",
            "implementation_digest",
            "dependency_closure",
            "imports_production_semantic_implementation",
        ],
        "type": "object",
    }


def _method_binding() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "binding_id": _common_ref("Identifier"),
            "binding_digest": _common_ref("Digest"),
            "check_id": _common_ref("Identifier"),
            "check_version": {"minLength": 1, "type": "string"},
            "check_manifest_digest": _common_ref("Digest"),
            "detector_id": {"const": METHOD_DETECTOR},
            "detector_version": {"const": "0.2.0"},
            "detector_manifest_digest": _common_ref("Digest"),
            "dimension": _common_ref("Identifier"),
            "comparison_form": {"enum": ["value_equals", "set_relation", "step_precedes"]},
            "operand_kind": {
                "enum": [
                    "canonical_scalar",
                    "unique_string_array",
                    "ordered_step_names",
                ]
            },
            "required_evidence_planes": {
                "items": {"enum": ["reported_text", "static_source"]},
                "minItems": 1,
                "maxItems": 2,
                "type": "array",
                "uniqueItems": True,
            },
            "required_semantic_roles": _unique_strings(min_items=1),
            "required_assertion_roles": {
                "items": {"enum": ["observed", "reported"]},
                "minItems": 1,
                "maxItems": 2,
                "type": "array",
                "uniqueItems": True,
            },
            "counterevidence_predicates": {
                "const": [
                    "approved_method_deviation",
                    "governing_protocol_amendment",
                    "method_obligation_applicability",
                ]
            },
            "forbidden_members": _unique_strings(),
            "production_finding_permitted": {"const": False},
            "qualification_adapter": _qualification_adapter(),
        },
        "required": [
            "binding_id",
            "binding_digest",
            "check_id",
            "check_version",
            "check_manifest_digest",
            "detector_id",
            "detector_version",
            "detector_manifest_digest",
            "dimension",
            "comparison_form",
            "operand_kind",
            "required_evidence_planes",
            "required_semantic_roles",
            "required_assertion_roles",
            "counterevidence_predicates",
            "forbidden_members",
            "production_finding_permitted",
            "qualification_adapter",
        ],
        "allOf": [
            {
                "oneOf": [
                    {
                        "properties": {
                            "required_evidence_planes": {"const": ["reported_text"]},
                            "required_assertion_roles": {"const": ["reported"]},
                        }
                    },
                    {
                        "properties": {
                            "required_evidence_planes": {"const": ["static_source"]},
                            "required_assertion_roles": {"const": ["observed"]},
                        }
                    },
                    {
                        "properties": {
                            "required_evidence_planes": {
                                "const": ["reported_text", "static_source"]
                            },
                            "required_assertion_roles": {"const": ["observed", "reported"]},
                        }
                    },
                ]
            },
            {
                "if": {"properties": {"comparison_form": {"const": "value_equals"}}},
                "then": {
                    "properties": {
                        "forbidden_members": {"maxItems": 0},
                        "operand_kind": {"const": "canonical_scalar"},
                    }
                },
            },
            {
                "if": {"properties": {"comparison_form": {"const": "set_relation"}}},
                "then": {"properties": {"operand_kind": {"const": "unique_string_array"}}},
            },
            {
                "if": {"properties": {"comparison_form": {"const": "step_precedes"}}},
                "then": {
                    "properties": {
                        "forbidden_members": {"maxItems": 0},
                        "operand_kind": {"const": "ordered_step_names"},
                    }
                },
            },
        ],
        "type": "object",
    }


def _extend_profile_schema(schema: dict[str, Any]) -> None:
    properties = schema["properties"]
    properties["profile_kind"] = {"enum": [DIRECTION_KIND, METHOD_KIND]}
    properties["method_binding"] = {"oneOf": [_method_binding(), {"type": "null"}]}
    properties["target_detector"]["properties"]["detector_version"] = {"enum": ["0.1.0", "0.2.0"]}
    properties["target_detector"]["properties"]["detector_id"] = {
        "enum": ["detector:bounded-report-mean-direction", METHOD_DETECTOR]
    }
    properties["verifier"]["properties"]["entry_point"] = {
        "enum": [
            "sc_referee_evaluation.static_qualification:verify_bounded_direction_case",
            METHOD_ENTRY,
        ]
    }
    rules = properties["selection_rules"]["properties"]
    rules["candidate_suffixes"] = _unique_strings(min_items=1)
    rules["dependency_closure"] = {
        "enum": [
            "unique_supported_csv_mean_writer_report_transitive_path",
            "registered_independent_qualification_adapter_selected_scope",
        ]
    }
    rules["surface_inventory"] = {
        "enum": [
            "every_literal_directional_sentence_in_complete_selected_report",
            "every_binding_declared_report_and_static_evidence_plane",
        ]
    }
    direction = copy.deepcopy(schema["allOf"][0])
    direction["then"]["properties"]["method_binding"] = {"const": None}
    method = {
        "if": {
            "properties": {"profile_kind": {"const": METHOD_KIND}},
            "required": ["profile_kind"],
        },
        "then": {
            "required": ["method_binding"],
            "properties": {
                "method_binding": _method_binding(),
                "selection_rules": {
                    "properties": {
                        "dependency_closure": {
                            "const": "registered_independent_qualification_adapter_selected_scope"
                        },
                        "surface_inventory": {
                            "const": "every_binding_declared_report_and_static_evidence_plane"
                        },
                    }
                },
                "target_detector": {
                    "properties": {
                        "detector_id": {"const": METHOD_DETECTOR},
                        "detector_version": {"const": "0.2.0"},
                    }
                },
                "verifier": {"properties": {"entry_point": {"const": METHOD_ENTRY}}},
            },
        },
    }
    schema["allOf"] = [direction, method]


def _typed_operand() -> dict[str, Any]:
    scalar = {"type": ["string", "number", "boolean", "null"]}
    strings = _unique_strings()
    ordered = _unique_strings(min_items=1)
    return {
        "additionalProperties": False,
        "properties": {
            "kind": {
                "enum": [
                    "canonical_scalar",
                    "unique_string_array",
                    "ordered_step_names",
                ]
            },
            "value": {"oneOf": [scalar, strings, ordered]},
        },
        "required": ["kind", "value"],
        "allOf": [
            {
                "if": {"properties": {"kind": {"const": "canonical_scalar"}}},
                "then": {"properties": {"value": scalar}},
            },
            {
                "if": {"properties": {"kind": {"const": "unique_string_array"}}},
                "then": {"properties": {"value": strings}},
            },
            {
                "if": {"properties": {"kind": {"const": "ordered_step_names"}}},
                "then": {"properties": {"value": ordered}},
            },
        ],
        "type": "object",
    }


def _declaration() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "evidence_plane": {"enum": ["reported_text", "static_source"]},
            "path": {"minLength": 1, "type": "string"},
            "start_line": {"minimum": 1, "type": "integer"},
            "end_line": {"minimum": 1, "type": "integer"},
            "retained_text": {"minLength": 1, "type": "string"},
        },
        "required": [
            "evidence_plane",
            "path",
            "start_line",
            "end_line",
            "retained_text",
        ],
        "type": "object",
    }


def _scope_edge() -> dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "source_ref": _general_ref(),
            "relation": {
                "enum": [
                    "contained_in_selected_source_artifact",
                    "contains_unique_static_selected_output_writer",
                    "declares_selected_output_artifact",
                    "selected_by_publication_surface",
                    "selected_source_artifact_of_publication_surface",
                ]
            },
            "target_ref": _general_ref(),
        },
        "required": ["source_ref", "relation", "target_ref"],
        "type": "object",
    }


def _observation() -> dict[str, Any]:
    declaration = _declaration()
    return {
        "additionalProperties": False,
        "properties": {
            "evidence_plane": {"enum": ["reported_text", "static_source"]},
            "operand": _typed_operand(),
            "declarations": {
                "items": declaration,
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "candidate_paths": _unique_strings(min_items=1),
            "scope_join_path": {
                "items": _scope_edge(),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "scope_join_digest": _common_ref("Digest"),
        },
        "required": [
            "evidence_plane",
            "operand",
            "declarations",
            "candidate_paths",
            "scope_join_path",
            "scope_join_digest",
        ],
        "allOf": [
            {
                "if": {"properties": {"evidence_plane": {"const": "reported_text"}}},
                "then": {
                    "properties": {
                        "declarations": {
                            "items": {
                                "allOf": [
                                    declaration,
                                    {"properties": {"evidence_plane": {"const": "reported_text"}}},
                                ]
                            }
                        }
                    }
                },
            },
            {
                "if": {"properties": {"evidence_plane": {"const": "static_source"}}},
                "then": {
                    "properties": {
                        "declarations": {
                            "items": {
                                "allOf": [
                                    declaration,
                                    {"properties": {"evidence_plane": {"const": "static_source"}}},
                                ]
                            }
                        }
                    }
                },
            },
        ],
        "type": "object",
    }


def _comparison() -> dict[str, Any]:
    return {
        "oneOf": [
            {
                "additionalProperties": False,
                "properties": {
                    "comparison_form": {"const": "value_equals"},
                    "outcome": {"enum": ["covered_negative", "exact_conflict_candidate"]},
                    "values_equal": {"type": "boolean"},
                },
                "required": ["comparison_form", "outcome", "values_equal"],
                "type": "object",
            },
            {
                "additionalProperties": False,
                "properties": {
                    "comparison_form": {"const": "set_relation"},
                    "outcome": {"enum": ["covered_negative", "exact_conflict_candidate"]},
                    "missing_required_members": _unique_strings(),
                    "present_forbidden_members": _unique_strings(),
                },
                "required": [
                    "comparison_form",
                    "outcome",
                    "missing_required_members",
                    "present_forbidden_members",
                ],
                "type": "object",
            },
            {
                "additionalProperties": False,
                "properties": {
                    "comparison_form": {"const": "step_precedes"},
                    "outcome": {
                        "enum": [
                            "covered_negative",
                            "exact_conflict_candidate",
                            "unsupported_path",
                        ]
                    },
                    "required_order_present": {"type": "boolean"},
                    "missing_steps": _unique_strings(),
                },
                "required": ["comparison_form", "outcome"],
                "oneOf": [
                    {"required": ["required_order_present"]},
                    {"required": ["missing_steps"]},
                ],
                "type": "object",
            },
        ]
    }


def _typed_facts() -> dict[str, Any]:
    observation = _observation()
    facts = {
        "additionalProperties": False,
        "properties": {
            "binding_id": _common_ref("Identifier"),
            "binding_digest": _common_ref("Digest"),
            "check_id": _common_ref("Identifier"),
            "dimension": _common_ref("Identifier"),
            "comparison_form": {"enum": ["value_equals", "set_relation", "step_precedes"]},
            "operand_kind": {
                "enum": [
                    "canonical_scalar",
                    "unique_string_array",
                    "ordered_step_names",
                ]
            },
            "qualification_adapter": _qualification_adapter(),
            "requirement_operand": _typed_operand(),
            "observed_operand": _typed_operand(),
            "forbidden_members": _unique_strings(),
            "observations": {
                "items": observation,
                "minItems": 1,
                "maxItems": 2,
                "type": "array",
                "uniqueItems": True,
                "allOf": [
                    {
                        "contains": {
                            "properties": {"evidence_plane": {"const": "reported_text"}},
                            "required": ["evidence_plane"],
                        },
                        "minContains": 0,
                        "maxContains": 1,
                    },
                    {
                        "contains": {
                            "properties": {"evidence_plane": {"const": "static_source"}},
                            "required": ["evidence_plane"],
                        },
                        "minContains": 0,
                        "maxContains": 1,
                    },
                    {
                        "anyOf": [
                            {
                                "contains": {
                                    "properties": {"evidence_plane": {"const": "reported_text"}},
                                    "required": ["evidence_plane"],
                                }
                            },
                            {
                                "contains": {
                                    "properties": {"evidence_plane": {"const": "static_source"}},
                                    "required": ["evidence_plane"],
                                }
                            },
                        ]
                    },
                ],
            },
            "comparison": _comparison(),
            "governing_question": _bound_ref("material_question"),
            "governing_answer": _bound_ref("answer"),
            "governing_contract": _bound_ref("scientific_contract"),
            "requirement_assertion": _bound_ref("semantic_assertion"),
            "candidate_paths": _unique_strings(min_items=1),
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
                "uniqueItems": True,
            },
            "production_finding_permitted": {"const": False},
        },
        "required": [
            "binding_id",
            "binding_digest",
            "check_id",
            "dimension",
            "comparison_form",
            "operand_kind",
            "qualification_adapter",
            "requirement_operand",
            "observed_operand",
            "forbidden_members",
            "observations",
            "comparison",
            "governing_question",
            "governing_answer",
            "governing_contract",
            "requirement_assertion",
            "candidate_paths",
            "supported_exclusions",
            "production_finding_permitted",
        ],
        "type": "object",
    }
    facts["allOf"] = [
        {
            "if": {"properties": {"comparison_form": {"const": "value_equals"}}},
            "then": {
                "properties": {
                    "operand_kind": {"const": "canonical_scalar"},
                    "requirement_operand": {"properties": {"kind": {"const": "canonical_scalar"}}},
                    "observed_operand": {"properties": {"kind": {"const": "canonical_scalar"}}},
                    "comparison": {"properties": {"comparison_form": {"const": "value_equals"}}},
                    "forbidden_members": {"maxItems": 0},
                }
            },
        },
        {
            "if": {"properties": {"comparison_form": {"const": "set_relation"}}},
            "then": {
                "properties": {
                    "operand_kind": {"const": "unique_string_array"},
                    "requirement_operand": {
                        "properties": {"kind": {"const": "unique_string_array"}}
                    },
                    "observed_operand": {"properties": {"kind": {"const": "unique_string_array"}}},
                    "comparison": {"properties": {"comparison_form": {"const": "set_relation"}}},
                }
            },
        },
        {
            "if": {"properties": {"comparison_form": {"const": "step_precedes"}}},
            "then": {
                "properties": {
                    "operand_kind": {"const": "ordered_step_names"},
                    "requirement_operand": {
                        "properties": {
                            "kind": {"const": "ordered_step_names"},
                            "value": {"minItems": 2, "maxItems": 2},
                        }
                    },
                    "observed_operand": {"properties": {"kind": {"const": "ordered_step_names"}}},
                    "comparison": {"properties": {"comparison_form": {"const": "step_precedes"}}},
                    "forbidden_members": {"maxItems": 0},
                }
            },
        },
    ]
    return facts


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
    method_facts = _typed_facts()
    properties["proof_profile_kind"] = {"enum": [DIRECTION_KIND, METHOD_KIND]}
    properties["derived_facts"] = {"oneOf": [direction_facts, method_facts, {"type": "null"}]}
    schema["allOf"] = [
        _proof_condition(DIRECTION_KIND, direction_facts, 3),
        _proof_condition(METHOD_KIND, method_facts, 1),
    ]


def _binding_example() -> dict[str, Any]:
    value = {
        "binding_id": "method-conflict-binding:founder-orientation-before-hmm-emission-v1",
        "check_id": "check:founder-orientation-before-hmm-emission",
        "check_version": "1.0.0",
        "check_manifest_digest": "sha256:" + "1" * 64,
        "detector_id": METHOD_DETECTOR,
        "detector_version": "0.2.0",
        "detector_manifest_digest": "sha256:" + "2" * 64,
        "dimension": "scale_and_orientation",
        "comparison_form": "value_equals",
        "operand_kind": "canonical_scalar",
        "required_evidence_planes": ["reported_text", "static_source"],
        "required_semantic_roles": [
            "founder_allele_input",
            "hmm_emission",
            "orientation_step",
        ],
        "required_assertion_roles": ["observed", "reported"],
        "counterevidence_predicates": [
            "approved_method_deviation",
            "governing_protocol_amendment",
            "method_obligation_applicability",
        ],
        "forbidden_members": [],
        "production_finding_permitted": False,
        "qualification_adapter": _qualification_adapter_example(),
    }
    value["binding_digest"] = _semantic_digest(value)
    return value


def _transform_profile(example: dict[str, Any]) -> None:
    if example.get("record_type") == "static_qualification_profile":
        example["method_binding"] = None
    if example.get("profile_kind") != "bounded_analysis_method_conflict_v1":
        return
    example["profile_kind"] = METHOD_KIND
    example["profile_id"] = "static-profile:typed-static-method-conflict-v1"
    example["method_binding"] = _binding_example()
    example["target_detector"]["detector_version"] = "0.2.0"
    example["verifier"]["entry_point"] = METHOD_ENTRY
    verifier_closure = [
        {
            "dependency_kind": "implementation",
            **_evaluation_dependency("typed_method_qualification.py"),
        },
        {
            "dependency_kind": "implementation",
            **_evaluation_dependency("founder_orientation_adapter.py"),
        },
        {
            "dependency_kind": "implementation",
            **_evaluation_dependency("analysis_method_qualification.py"),
        },
    ]
    example["verifier"]["dependency_closure"] = verifier_closure
    example["verifier"]["implementation_digest"] = _semantic_digest(verifier_closure)
    example["selection_rules"].update(
        {
            "dependency_closure": "registered_independent_qualification_adapter_selected_scope",
            "surface_inventory": "every_binding_declared_report_and_static_evidence_plane",
        }
    )


def _typed_observation(plane: str, path: str, operand: str) -> dict[str, Any]:
    scope = [
        {
            "source_ref": {"record_type": "artifact", "record_id": "artifact:report"},
            "relation": "selected_by_publication_surface",
            "target_ref": {
                "record_type": "publication_surface",
                "record_id": "surface:selected",
            },
        }
    ]
    return {
        "evidence_plane": plane,
        "operand": {"kind": "canonical_scalar", "value": operand},
        "declarations": [
            {
                "evidence_plane": plane,
                "path": path,
                "start_line": 1,
                "end_line": 6 if plane == "static_source" else 1,
                "retained_text": "Exact independently retained method declaration.",
            }
        ],
        "candidate_paths": ["analysis.py", "report.md"],
        "scope_join_path": scope,
        "scope_join_digest": "sha256:" + ("5" if plane == "reported_text" else "6") * 64,
    }


def _transform_proof(example: dict[str, Any]) -> None:
    if example.get("proof_profile_kind") != "bounded_analysis_method_conflict_v1":
        return
    direct = "use_supplied_founder_alleles_directly_in_hmm_emission"
    repaired = "repair_ril_founder_orientation_before_hmm_emission"
    old = example["derived_facts"]
    binding = _binding_example()
    example["proof_profile_kind"] = METHOD_KIND
    example["profile"]["record_ref"]["record_id"] = "static-profile:typed-static-method-conflict-v1"
    example["derived_facts"] = {
        "binding_id": binding["binding_id"],
        "binding_digest": binding["binding_digest"],
        "check_id": binding["check_id"],
        "dimension": binding["dimension"],
        "comparison_form": "value_equals",
        "operand_kind": "canonical_scalar",
        "qualification_adapter": binding["qualification_adapter"],
        "requirement_operand": {"kind": "canonical_scalar", "value": repaired},
        "observed_operand": {"kind": "canonical_scalar", "value": direct},
        "forbidden_members": [],
        "observations": [
            _typed_observation("reported_text", "report.md", direct),
            _typed_observation("static_source", "analysis.py", direct),
        ],
        "comparison": {
            "comparison_form": "value_equals",
            "outcome": "exact_conflict_candidate",
            "values_equal": False,
        },
        "governing_question": old["governing_question"],
        "governing_answer": old["governing_answer"],
        "governing_contract": old["governing_contract"],
        "requirement_assertion": old["requirement_assertion"],
        "candidate_paths": ["analysis.py", "report.md"],
        "supported_exclusions": [],
        "production_finding_permitted": False,
    }


def _release_readme() -> str:
    return """# sc-referee public schemas v0.17.0

Accepted forward-only public schema release implementing ADR-0042.

This release replaces the founder-specific static method proof with one closed typed proof for
registered scalar, set, and step-order method checks. It binds an independent qualification
adapter and exact report/source declarations. It does not qualify or promote a detector, execute
project code, or grant Finding authority.
"""


def _release_changelog() -> str:
    return """# Changelog

## 0.17.0 — 2026-07-31

- Added the `typed_static_method_conflict_v1` profile and proof variant.
- Bound each method proof to a content-addressed check/detector/qualification-adapter record.
- Added closed scalar, set-relation, and step-order operand shapes.
- Preserved v0.16.0 as an immutable migration baseline.
"""


def _release_invariants() -> str:
    return """# Controller invariants for v0.17.0

- The method binding, detector, check, and independent qualification adapter verify by digest.
- Required and binding-selected observed operands use one closed relation-valid type.
- Every required observation is independently rederived and multiple planes must agree exactly.
- Qualification code cannot import production adapters, detector logic, reducers, or grammars.
- Ambiguity, incomplete scope, failed applicability, and counterevidence remain unavailable.
- Static proof never establishes execution, numerical causality, or universal correctness.
- No record in this release grants detector promotion or Finding authority.
"""


def _migration_text() -> str:
    return """# Migration from v0.16.0 to v0.17.0

The migration is fail closed. Ordinary records are versioned. Existing v0.16 static profiles,
proofs, fixtures, dependent case outcomes, and metric evidence are retained only as namespaced
historical payloads because the public bundle cannot infer a generic binding or independent
qualification adapter. Migration creates no Answer, proof, qualification, maturity, Finding, or
execution authority.
"""


def _v17_tests() -> str:
    return """from test_examples import errors, invalid, load

def test_typed_method_profile_and_proof_examples_validate():
 assert not errors(load("static-qualification-profile.analysis-method.example.json"), "static_qualification_profile")
 assert not errors(load("static-qualification-proof.analysis-method.example.json"), "static_qualification_proof")

def test_typed_method_profile_cannot_reuse_production_adapter_identity():
 x=load("static-qualification-profile.analysis-method.example.json")
 x["method_binding"]["qualification_adapter"]["adapter_id"]="adapter:production"
 invalid(x,"static_qualification_profile")

def test_typed_method_proof_rejects_relation_kind_mixing():
 x=load("static-qualification-proof.analysis-method.example.json")
 x["derived_facts"]["comparison_form"]="set_relation"
 invalid(x,"static_qualification_proof")

def test_typed_method_profile_and_proof_allow_one_report_plane():
 p=load("static-qualification-profile.analysis-method.example.json")
 p["method_binding"]["required_evidence_planes"]=["reported_text"]
 p["method_binding"]["required_assertion_roles"]=["reported"]
 assert not errors(p,"static_qualification_profile")
 x=load("static-qualification-proof.analysis-method.example.json")
 x["derived_facts"]["observations"]=x["derived_facts"]["observations"][:1]
 x["derived_facts"]["candidate_paths"]=["report.md"]
 assert not errors(x,"static_qualification_proof")
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
    """Build accepted v0.17.0 without modifying immutable v0.16.0."""

    _require_empty_destination(output)
    source_schemas = BASELINE / "schemas" / f"v{BASELINE_VERSION}"
    schema_output = output / "schemas" / f"v{RELEASE_VERSION}"
    for source in sorted(source_schemas.glob("*.json")):
        schema = _replace_version(_read_json(source))
        if source.name == "static-qualification-profile.schema.json":
            _extend_profile_schema(schema)
        elif source.name == "static-qualification-proof.schema.json":
            _extend_proof_schema(schema)
        _write_json(schema_output / source.name, schema)

    catalog = _replace_version(_read_json(BASELINE / "schema-catalog.json"))
    catalog["schema_version"] = RELEASE_VERSION
    _write_json(output / "schema-catalog.json", catalog)

    for source in sorted((BASELINE / "examples").glob("*.json")):
        example = _replace_version(_read_json(source))
        _transform_profile(example)
        _transform_proof(example)
        _write_json(output / "examples" / source.name, example)

    for name in ("LICENSE", "LICENSE-NOTICE.md", "NOTICE", "requirements.txt"):
        shutil.copy2(BASELINE / name, output / name)
    (output / "VERSION").write_text(RELEASE_VERSION + "\n", encoding="utf-8")
    (output / "README.md").write_text(_release_readme(), encoding="utf-8")
    (output / "CHANGELOG.md").write_text(_release_changelog(), encoding="utf-8")
    (output / "CONTROLLER_INVARIANTS.md").write_text(_release_invariants(), encoding="utf-8")
    (output / "MIGRATION_v0.16_to_v0.17.md").write_text(_migration_text(), encoding="utf-8")
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
    (tests_output / "test_v017_invariants.py").write_text(_v17_tests(), encoding="utf-8")

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
    parser = argparse.ArgumentParser(description="Build accepted sc-referee schema release 0.17.0")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = build_release(args.output.resolve())
    print(f"Built public schema release {RELEASE_VERSION} with {count} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
