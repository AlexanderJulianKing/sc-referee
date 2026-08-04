from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee_evaluation.prospective_qualification import (
    REQUIRED_CELL_TYPES,
    ProspectiveQualificationError,
    freeze_prospective_qualification_protocol,
)


class ProspectiveMethodContractInputError(ValueError):
    """Prospective method-contract inputs are inconsistent, incomplete, or unsafe."""


BUILDER_VERSION = "1.0.0"
_QUALIFYING_ROLES = {"threshold_pilot", "qualification_heldout"}
_BRIEF_KEYS = {
    "artifact_kind",
    "scaffold_version",
    "opaque_case_id",
    "block_neutral_assignment_token",
    "one_relation_brief",
    "one_cell_brief",
    "paired_case_access",
    "neutral_repository_deliverables",
    "submission_deadline",
    "submission_channel",
    "quality_constraints",
    "information_barrier",
    "qualification_authority",
    "brief_digest",
}
_MAP_KEYS = {
    "artifact_kind",
    "scaffold_version",
    "protocol_ref",
    "bindings",
    "qualification_authority",
    "mapping_digest",
}
_BINDING_KEYS = {
    "envelope_id",
    "check_id",
    "candidate_id",
    "binding_digest",
    "blind_relation_id",
}


def build_prospective_method_contract_inputs(
    protocol: Mapping[str, Any],
    relation_binding_map: Mapping[str, Any],
    authoring_briefs: Sequence[Mapping[str, Any]],
    *,
    block_id: str,
    scientist_id: str,
    allow_heldout: bool = False,
) -> dict[str, bytes]:
    """Build create-once, evaluation-only method-contract project shells for one block.

    This function parses data artifacts only. It does not execute authored case code, run a
    detector, create a method-contract lock, release author packets, or create qualification
    evidence.
    """

    frozen_protocol = _validate_protocol(protocol)
    selected_block = _select_block(frozen_protocol, block_id)
    evidence_role = str(selected_block["evidence_role"])
    if evidence_role == "qualification_heldout" and not allow_heldout:
        raise ProspectiveMethodContractInputError(
            "Held-out method-contract inputs remain sealed; pass allow_heldout=True only after "
            "the coordinator authorizes held-out preparation."
        )
    scientist = _single_line(scientist_id, "scientist_id")
    assignments = _validate_block_matrix(frozen_protocol, block_id)
    bindings = _validate_relation_binding_map(relation_binding_map, frozen_protocol)
    briefs_by_case = _validate_authoring_briefs(authoring_briefs)
    _validate_assignment_briefs(assignments, briefs_by_case)

    files: dict[str, bytes] = {}
    case_records: list[dict[str, Any]] = []
    relation_briefs: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for assignment in assignments:
        case_id = str(assignment["case_id"])
        envelope_id = str(assignment["envelope_id"])
        brief = briefs_by_case[case_id]
        relation_brief = _mapping(brief["one_relation_brief"], "one_relation_brief")
        relation_briefs[envelope_id].append(relation_brief)

        binding = bindings[envelope_id]
        profile = {
            "profile_id": "scientific_check_requirement_v1",
            "profile_version": "1.0.0",
            "check_id": binding["check_id"],
            "candidate_id": binding["candidate_id"],
        }
        task_bytes = _task_markdown(
            case_id=case_id,
            protocol_id=str(frozen_protocol["protocol_id"]),
            scientist_id=scientist,
            governed_premise=_nonempty(relation_brief.get("governed_premise"), "governed_premise"),
        ).encode("utf-8")
        profile_bytes = (canonical_json(profile) + "\n").encode("utf-8")
        case_token = case_id.removeprefix("case:")
        project_path = f"projects/{case_token}"
        task_path = f"{project_path}/TASK.md"
        profile_path = f"{project_path}/method-contract-profile.json"
        _put(files, task_path, task_bytes)
        _put(files, profile_path, profile_bytes)
        case_records.append(
            {
                "case_id": case_id,
                "envelope_id": envelope_id,
                "authoring_brief_digest": assignment["authoring_brief_digest"],
                "binding_digest": binding["binding_digest"],
                "project_path": project_path,
                "task_path": "TASK.md",
                "task_content_digest": sha256_digest(task_bytes),
                "profile_path": "method-contract-profile.json",
                "profile_semantic_digest": semantic_digest(profile),
            }
        )

    _validate_relation_premise_consistency(relation_briefs)
    manifest = _self_digest(
        {
            "artifact_kind": "prospective_method_contract_input_manifest",
            "builder_version": BUILDER_VERSION,
            "protocol_ref": _protocol_ref(frozen_protocol),
            "block_ref": {
                "block_id": selected_block["block_id"],
                "evidence_role": evidence_role,
            },
            "scientist_id": scientist,
            "profile_family": {
                "profile_id": "scientific_check_requirement_v1",
                "profile_version": "1.0.0",
            },
            "validated_matrix": {
                "relation_count": 10,
                "cell_types_per_relation": len(REQUIRED_CELL_TYPES),
                "case_count": len(case_records),
                "complete": True,
            },
            "projects": sorted(case_records, key=lambda item: str(item["case_id"])),
            "creation_boundary": {
                "write_policy": "new_absent_output_root_only",
                "task_file_policy": "write_once_digest_bound_and_read_only",
                "contains_case_implementation": False,
                "contains_report_material": False,
                "contains_scientific_labels": False,
                "contains_detector_observations": False,
                "contains_method_contract_locks": False,
                "project_authored_code_executed": False,
            },
            "qualification_authority": "none_evaluation_input_only",
        },
        "manifest_digest",
    )
    _put(files, "INPUT_MANIFEST.json", (canonical_json(manifest) + "\n").encode("utf-8"))
    return dict(sorted(files.items()))


def write_prospective_method_contract_inputs_once(
    output_root: Path, files: Mapping[str, bytes]
) -> Path:
    """Write generated shells beneath a new root and make task/profile inputs read-only."""

    destination = output_root.resolve()
    if destination.exists():
        raise ProspectiveMethodContractInputError(f"Output already exists: {destination}")
    validated: list[tuple[PurePosixPath, bytes]] = []
    for relative, payload in files.items():
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts or not relative_path.parts:
            raise ProspectiveMethodContractInputError(f"Unsafe generated path: {relative!r}")
        if not isinstance(payload, bytes):
            raise ProspectiveMethodContractInputError(
                f"Generated payload is not bytes: {relative!r}"
            )
        validated.append((relative_path, payload))

    destination.mkdir(parents=True)
    for checked_path, payload in validated:
        output = destination.joinpath(*checked_path.parts)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        if output.name in {"TASK.md", "method-contract-profile.json"}:
            output.chmod(0o444)
    return destination


def load_json_object(path: Path) -> dict[str, Any]:
    """Load one JSON object without importing or executing project code."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProspectiveMethodContractInputError(f"Expected one JSON object: {path}")
    return value


def load_authoring_briefs(root: Path) -> list[dict[str, Any]]:
    """Load coordinator brief JSON files in deterministic path order."""

    if not root.is_dir():
        raise ProspectiveMethodContractInputError(
            f"Authoring-brief root is not a directory: {root}"
        )
    paths = sorted(path for path in root.iterdir() if path.is_file() and path.suffix == ".json")
    if not paths:
        raise ProspectiveMethodContractInputError(
            f"Authoring-brief root contains no JSON files: {root}"
        )
    return [load_json_object(path) for path in paths]


def _validate_protocol(value: Mapping[str, Any]) -> dict[str, Any]:
    protocol = deepcopy(dict(value))
    expected_digest = protocol.pop("protocol_digest", None)
    if expected_digest != semantic_digest(protocol):
        raise ProspectiveMethodContractInputError("Prospective protocol digest does not replay.")
    protocol["protocol_digest"] = expected_digest
    if (
        protocol.get("artifact_kind") != "prospective_qualification_protocol"
        or protocol.get("protocol_version") != "1.0.0"
        or protocol.get("study_state") != "assignments_frozen_labels_unopened"
        or protocol.get("qualification_authority") != "none_protocol_only"
    ):
        raise ProspectiveMethodContractInputError("Unsupported prospective protocol artifact.")
    try:
        replayed = freeze_prospective_qualification_protocol(
            {
                key: protocol[key]
                for key in (
                    "protocol_id",
                    "expected_envelope_count",
                    "detector_lock",
                    "participants",
                    "envelopes",
                    "blocks",
                    "assignments",
                    "governance",
                )
            },
            frozen_at=str(protocol["frozen_at"]),
        )
    except (KeyError, ProspectiveQualificationError) as error:
        raise ProspectiveMethodContractInputError(
            f"Prospective protocol semantics do not validate: {error}"
        ) from error
    if replayed != protocol:
        raise ProspectiveMethodContractInputError("Prospective protocol semantics do not replay.")
    if protocol["expected_envelope_count"] != 10:
        raise ProspectiveMethodContractInputError("Contract inputs require exactly ten relations.")
    return protocol


def _select_block(protocol: Mapping[str, Any], block_id: str) -> dict[str, Any]:
    identifier = _nonempty(block_id, "block_id")
    matches = [
        _mapping(item, "block")
        for item in _sequence(protocol["blocks"], "blocks")
        if isinstance(item, Mapping) and item.get("block_id") == identifier
    ]
    if len(matches) != 1:
        raise ProspectiveMethodContractInputError(f"Unknown or duplicate block {identifier!r}.")
    if matches[0].get("evidence_role") not in _QUALIFYING_ROLES:
        raise ProspectiveMethodContractInputError(
            "Method-contract input shells are limited to pilot and held-out qualification blocks."
        )
    return matches[0]


def _validate_block_matrix(protocol: Mapping[str, Any], block_id: str) -> list[dict[str, Any]]:
    assignments = [
        _mapping(item, "assignment")
        for item in _sequence(protocol["assignments"], "assignments")
        if isinstance(item, Mapping) and item.get("block_id") == block_id
    ]
    envelopes = {
        str(item["envelope_id"])
        for item in _sequence(protocol["envelopes"], "envelopes")
        if isinstance(item, Mapping)
    }
    counts = Counter(
        (str(item.get("envelope_id")), str(item.get("cell_type"))) for item in assignments
    )
    invalid = [
        f"{envelope_id}/{cell_type}={counts[(envelope_id, cell_type)]}"
        for envelope_id in sorted(envelopes)
        for cell_type in REQUIRED_CELL_TYPES
        if counts[(envelope_id, cell_type)] != 1
    ]
    if len(envelopes) != 10 or len(assignments) != 70 or invalid:
        raise ProspectiveMethodContractInputError(
            "Selected block must contain the complete 10 x 7 assignment matrix; "
            f"case_count={len(assignments)}, invalid={invalid}."
        )
    return sorted(assignments, key=lambda item: str(item["case_id"]))


def _validate_relation_binding_map(
    value: Mapping[str, Any], protocol: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    relation_map = deepcopy(dict(value))
    _exact_keys(relation_map, _MAP_KEYS, "relation-binding map")
    declared_digest = relation_map.pop("mapping_digest")
    if declared_digest != semantic_digest(relation_map):
        raise ProspectiveMethodContractInputError("Relation-binding map digest does not replay.")
    if (
        relation_map.get("artifact_kind") != "prospective_relation_binding_map"
        or relation_map.get("scaffold_version") != "1.0.0"
        or relation_map.get("protocol_ref") != _protocol_ref(protocol)
        or relation_map.get("qualification_authority") != "none_coordinator_mapping_only"
    ):
        raise ProspectiveMethodContractInputError(
            "Relation-binding map is not bound to the selected protocol."
        )
    protocol_by_envelope = {
        str(item["envelope_id"]): _mapping(item, "protocol envelope")
        for item in _sequence(protocol["envelopes"], "envelopes")
        if isinstance(item, Mapping)
    }
    bindings: dict[str, dict[str, Any]] = {}
    blind_ids: set[str] = set()
    for raw in _sequence(relation_map.get("bindings"), "relation bindings"):
        binding = _mapping(raw, "relation binding")
        _exact_keys(binding, _BINDING_KEYS, "relation binding")
        envelope_id = _nonempty(binding["envelope_id"], "binding envelope_id")
        blind_id = _nonempty(binding["blind_relation_id"], "blind_relation_id")
        if envelope_id in bindings or blind_id in blind_ids:
            raise ProspectiveMethodContractInputError("Relation-binding identities must be unique.")
        protocol_binding = protocol_by_envelope.get(envelope_id)
        if protocol_binding is None or any(
            binding[key] != protocol_binding[key]
            for key in ("check_id", "candidate_id", "binding_digest")
        ):
            raise ProspectiveMethodContractInputError(
                f"Relation binding {envelope_id!r} differs from its frozen protocol envelope."
            )
        bindings[envelope_id] = binding
        blind_ids.add(blind_id)
    if set(bindings) != set(protocol_by_envelope) or len(bindings) != 10:
        raise ProspectiveMethodContractInputError(
            "Relation-binding map must cover each of the ten protocol envelopes exactly once."
        )
    return bindings


def _validate_authoring_briefs(
    values: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    if isinstance(values, (str, bytes, bytearray)) or not isinstance(values, Sequence):
        raise ProspectiveMethodContractInputError("authoring_briefs must be an array.")
    result: dict[str, dict[str, Any]] = {}
    for raw in values:
        brief = deepcopy(_mapping(raw, "authoring brief"))
        _exact_keys(brief, _BRIEF_KEYS, "authoring brief")
        declared_digest = brief.pop("brief_digest")
        if declared_digest != semantic_digest(brief):
            raise ProspectiveMethodContractInputError("Authoring brief digest does not replay.")
        brief["brief_digest"] = declared_digest
        case_id = _nonempty(brief["opaque_case_id"], "brief opaque_case_id")
        if case_id in result:
            raise ProspectiveMethodContractInputError(f"Duplicate authoring brief {case_id!r}.")
        if (
            brief.get("artifact_kind") != "prospective_case_authoring_brief"
            or brief.get("scaffold_version") != "1.0.0"
            or brief.get("qualification_authority") != "none_authoring_instruction_only"
        ):
            raise ProspectiveMethodContractInputError("Unsupported authoring brief artifact.")
        result[case_id] = brief
    if not result:
        raise ProspectiveMethodContractInputError("No authoring briefs were supplied.")
    return result


def _validate_assignment_briefs(
    assignments: Sequence[Mapping[str, Any]], briefs: Mapping[str, Mapping[str, Any]]
) -> None:
    for assignment in assignments:
        case_id = str(assignment["case_id"])
        brief = briefs.get(case_id)
        if brief is None:
            raise ProspectiveMethodContractInputError(
                f"Missing coordinator authoring brief for {case_id}."
            )
        if brief["brief_digest"] != assignment["authoring_brief_digest"]:
            raise ProspectiveMethodContractInputError(
                f"Authoring brief {case_id} differs from its frozen assignment digest."
            )
        cell_brief = _mapping(brief["one_cell_brief"], "one_cell_brief")
        if cell_brief.get("cell_type") != assignment["cell_type"]:
            raise ProspectiveMethodContractInputError(
                f"Authoring brief {case_id} does not match its assigned control cell."
            )


def _validate_relation_premise_consistency(
    relation_briefs: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    relation_digests: set[str] = set()
    for envelope_id, briefs in relation_briefs.items():
        digests = {semantic_digest(dict(brief)) for brief in briefs}
        if len(briefs) != len(REQUIRED_CELL_TYPES) or len(digests) != 1:
            raise ProspectiveMethodContractInputError(
                f"Envelope {envelope_id!r} does not carry one consistent premise across seven cells."
            )
        relation_digests.update(digests)
    if len(relation_briefs) != 10 or len(relation_digests) != 10:
        raise ProspectiveMethodContractInputError(
            "The selected block must carry ten distinct governed relation premises."
        )


def _task_markdown(
    *, case_id: str, protocol_id: str, scientist_id: str, governed_premise: str
) -> str:
    return (
        "# Frozen prospective case method premise\n\n"
        f"Opaque case: `{case_id}`  \n"
        f"Frozen protocol: `{protocol_id}`  \n"
        f"Authorizing scientist: `{scientist_id}`\n\n"
        "## Governed premise\n\n"
        "Before any case implementation or report existed, the named scientist authorized this "
        "case-specific method premise for the primary analysis:\n\n"
        f"> {governed_premise}\n\n"
        "## Boundary\n\n"
        "This premise is a human method declaration for this case only. It is not a universal "
        "scientific claim, a scientific label, a detector observation, qualification evidence, "
        "a correctness certificate, or proof that any code ran. No project-authored code was "
        "executed to create this shell.\n\n"
        "Do not modify this file. New scientific intent requires a new absent project shell and "
        "a new method-contract lifecycle. This file is write-once, read-only, and digest-bound "
        "by the coordinator input manifest.\n"
    )


def _protocol_ref(protocol: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "protocol_id": protocol["protocol_id"],
        "protocol_digest": protocol["protocol_digest"],
    }


def _self_digest(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = semantic_digest(result)
    return result


def _put(files: dict[str, bytes], path: str, payload: bytes) -> None:
    if path in files:
        raise ProspectiveMethodContractInputError(f"Duplicate generated path: {path}")
    files[path] = payload


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProspectiveMethodContractInputError(f"{label} must be an object.")
    return dict(value)


def _sequence(value: Any, label: str) -> list[Any]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ProspectiveMethodContractInputError(f"{label} must be an array.")
    return list(value)


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ProspectiveMethodContractInputError(
            f"{label} keys differ; missing={sorted(expected - set(value))}, "
            f"extra={sorted(set(value) - expected)}."
        )


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProspectiveMethodContractInputError(f"{label} must be a nonempty string.")
    return value


def _single_line(value: Any, label: str) -> str:
    result = _nonempty(value, label)
    if any(character in result for character in ("\n", "\r", "\x00")):
        raise ProspectiveMethodContractInputError(f"{label} must be a single line.")
    return result
