from __future__ import annotations

import hashlib
import hmac
import json
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee_evaluation.prospective_qualification import (
    REQUIRED_CELL_TYPES,
    freeze_prospective_qualification_protocol,
)


class ProspectiveStudyScaffoldError(ValueError):
    """A study-scaffold input or requested write is unsafe or incomplete."""


SCAFFOLD_VERSION = "1.0.0"
_QUALIFICATION_ROLES = {"threshold_pilot", "qualification_heldout"}
_SETUP_KEYS = {
    "study_id",
    "protocol_id",
    "template_digest",
    "authoring_template_digest",
    "detector_lock",
    "participants",
    "block_assignments",
    "stage1_reviewer_ids",
    "stage2_reviewer_ids",
    "case_id_key",
    "assigned_at",
    "protocol_frozen_at",
}


def build_prospective_study_scaffold(
    template: Mapping[str, Any],
    authoring_template: Mapping[str, Any],
    setup: Mapping[str, Any],
) -> dict[str, bytes]:
    """Build a deterministic, role-separated 10 x 2 x 7 study assignment package.

    The returned files contain assignments and authoring instructions only. They contain no case
    material, scientific labels, review decisions, detector observations, metrics, thresholds, or
    promotion authority. The caller remains responsible for access control and every external
    action named by the frozen protocol.
    """

    frozen_template = _validate_template(template)
    frozen_authoring_template = _validate_authoring_template(authoring_template)
    normalized_setup = _validate_setup(setup, frozen_template, frozen_authoring_template)
    participants = deepcopy(normalized_setup["participants"])
    participant_by_id = {
        str(participant["participant_id"]): participant for participant in participants
    }
    relation_catalog, relation_bindings = _relation_catalog(
        frozen_template, frozen_authoring_template
    )
    cell_catalog = {
        str(cell["cell_type"]): deepcopy(cell) for cell in frozen_authoring_template["cell_briefs"]
    }
    case_key = bytes.fromhex(str(normalized_setup["case_id_key"]))
    stage1_ids = [str(value) for value in normalized_setup["stage1_reviewer_ids"]]
    stage2_ids = [str(value) for value in normalized_setup["stage2_reviewer_ids"]]

    assignments: list[dict[str, Any]] = []
    briefs: dict[str, dict[str, Any]] = {}
    for block in normalized_setup["block_assignments"]:
        block_id = str(block["block_id"])
        primary_authors = [str(value) for value in block["primary_author_ids"]]
        renamed_authors = [str(value) for value in block["renamed_author_ids"]]
        for envelope_index, envelope in enumerate(frozen_template["envelopes"]):
            envelope_id = str(envelope["envelope_id"])
            primary_author = primary_authors[envelope_index % len(primary_authors)]
            renamed_author = renamed_authors[envelope_index % len(renamed_authors)]
            family_case_ids = {
                cell_type: _opaque_case_id(
                    case_key,
                    protocol_id=str(normalized_setup["protocol_id"]),
                    block_id=block_id,
                    envelope_id=envelope_id,
                    cell_type=cell_type,
                )
                for cell_type in REQUIRED_CELL_TYPES
            }
            for cell_type in REQUIRED_CELL_TYPES:
                case_id = family_case_ids[cell_type]
                reference_case_id = (
                    family_case_ids["error_bearing"]
                    if cell_type in {"corrected_twin", "renamed_implementation"}
                    else None
                )
                author_id = (
                    renamed_author if cell_type == "renamed_implementation" else primary_author
                )
                brief = _authoring_brief(
                    case_id=case_id,
                    assignment_token=_opaque_assignment_token(case_key, case_id),
                    cell_type=cell_type,
                    reference_case_id=reference_case_id,
                    relation=relation_catalog[envelope_id],
                    cell_brief=cell_catalog[cell_type],
                    neutral_repository_deliverables=frozen_authoring_template[
                        "neutral_repository_deliverables"
                    ],
                    submission_deadline=str(block["submission_deadline"]),
                    submission_channel=str(block["submission_channel"]),
                )
                brief_digest = semantic_digest(brief)
                brief["brief_digest"] = brief_digest
                briefs[case_id] = brief
                assignments.append(
                    {
                        "case_id": case_id,
                        "envelope_id": envelope_id,
                        "block_id": block_id,
                        "cell_type": cell_type,
                        "source_kind": "independent_prospective",
                        "reference_case_id": reference_case_id,
                        "author_id": author_id,
                        "stage1_reviewer_ids": stage1_ids,
                        "stage2_reviewer_ids": stage2_ids,
                        "authoring_brief_digest": brief_digest,
                        "assigned_at": normalized_setup["assigned_at"],
                    }
                )

    blocks = [
        {"block_id": block["block_id"], "evidence_role": block["evidence_role"]}
        for block in normalized_setup["block_assignments"]
    ]
    specification = {
        "protocol_id": normalized_setup["protocol_id"],
        "expected_envelope_count": frozen_template["expected_envelope_count"],
        "detector_lock": deepcopy(normalized_setup["detector_lock"]),
        "participants": participants,
        "envelopes": deepcopy(frozen_template["envelopes"]),
        "blocks": blocks,
        "assignments": assignments,
        "governance": {
            "all_outcomes_retained": True,
            "no_replacement": True,
            "public_benchmark_qualification_excluded": True,
            "development_case_qualification_excluded": True,
            "detector_implementers_label_blind": True,
            "review_detector_output_hidden": True,
            "independent_review_contexts_required": True,
        },
    }
    protocol = freeze_prospective_qualification_protocol(
        specification, frozen_at=str(normalized_setup["protocol_frozen_at"])
    )

    files: dict[str, bytes] = {}
    _put_json(files, "coordinator/protocol-specification.json", specification)
    _put_json(files, "coordinator/protocol.json", protocol)
    _put_json(
        files,
        "coordinator/relation-binding-map.json",
        _self_digest(
            {
                "artifact_kind": "prospective_relation_binding_map",
                "scaffold_version": SCAFFOLD_VERSION,
                "protocol_ref": _protocol_ref(protocol),
                "bindings": relation_bindings,
                "qualification_authority": "none_coordinator_mapping_only",
            },
            "mapping_digest",
        ),
    )
    _put_json(
        files,
        "coordinator/case-register.json",
        _self_digest(
            {
                "artifact_kind": "prospective_case_register",
                "scaffold_version": SCAFFOLD_VERSION,
                "study_id": normalized_setup["study_id"],
                "protocol_ref": {
                    "protocol_id": protocol["protocol_id"],
                    "protocol_digest": protocol["protocol_digest"],
                },
                "assignments": protocol["assignments"],
                "qualification_authority": "none_assignment_register_only",
            },
            "register_digest",
        ),
    )
    for case_id, brief in sorted(briefs.items()):
        _put_json(
            files,
            f"coordinator/authoring-briefs/{case_id.removeprefix('case:')}.json",
            brief,
        )

    author_queues: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    block_by_id = {str(block["block_id"]): block for block in blocks}
    for assignment in protocol["assignments"]:
        key = (str(assignment["block_id"]), str(assignment["author_id"]))
        author_queues[key].append(briefs[str(assignment["case_id"])])
    for (block_id, author_id), queue_briefs in sorted(author_queues.items()):
        evidence_role = str(block_by_id[block_id]["evidence_role"])
        queue = _author_queue(
            protocol=protocol,
            author_id=author_id,
            briefs=queue_briefs,
        )
        location = (
            "releases/pilot/authors"
            if evidence_role == "threshold_pilot"
            else "coordinator/staged-heldout/authors"
        )
        _put_json(files, f"{location}/{_path_token(author_id)}.json", queue)

    for block in blocks:
        block_id = str(block["block_id"])
        evidence_role = str(block["evidence_role"])
        reviewer_case_ids = sorted(
            str(assignment["case_id"])
            for assignment in protocol["assignments"]
            if assignment["block_id"] == block_id
        )
        for stage, reviewer_ids in (("stage1", stage1_ids), ("stage2", stage2_ids)):
            for reviewer_id in reviewer_ids:
                queue = _blind_review_queue(
                    protocol=protocol,
                    block_id=block_id,
                    evidence_role=evidence_role,
                    stage=stage,
                    reviewer_id=reviewer_id,
                    case_ids=reviewer_case_ids,
                )
                if evidence_role == "threshold_pilot" and stage == "stage1":
                    location = "releases/pilot/stage1-reviewers"
                elif evidence_role == "threshold_pilot":
                    location = "coordinator/staged-pilot/stage2-reviewers"
                else:
                    location = f"coordinator/staged-heldout/{stage}-reviewers"
                _put_json(files, f"{location}/{_path_token(reviewer_id)}.json", queue)

    distribution_plan = _distribution_plan(protocol, participant_by_id)
    _put_json(files, "coordinator/distribution-plan.json", distribution_plan)
    package_manifest = _package_manifest(
        files,
        study_id=str(normalized_setup["study_id"]),
        protocol=protocol,
        template_digest=str(frozen_template["template_digest"]),
        authoring_template_digest=str(frozen_authoring_template["template_digest"]),
        case_id_key_digest=sha256_digest(case_key),
    )
    _put_json(files, "PACKAGE_MANIFEST.json", package_manifest)
    return dict(sorted(files.items()))


def write_study_scaffold_once(output_root: Path, files: Mapping[str, bytes]) -> Path:
    """Write one generated package to a new directory without overwriting existing state."""

    destination = output_root.resolve()
    if destination.exists():
        raise ProspectiveStudyScaffoldError(f"Output already exists: {destination}")
    validated: list[tuple[PurePosixPath, bytes]] = []
    for relative, payload in files.items():
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts or not relative_path.parts:
            raise ProspectiveStudyScaffoldError(f"Unsafe generated path: {relative!r}")
        if not isinstance(payload, bytes):
            raise ProspectiveStudyScaffoldError(f"Generated payload is not bytes: {relative!r}")
        validated.append((relative_path, payload))
    destination.mkdir(parents=True)
    for relative_path, payload in validated:
        output_path = destination.joinpath(*relative_path.parts)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(payload)
    return destination


def _validate_template(value: Mapping[str, Any]) -> dict[str, Any]:
    template = deepcopy(dict(value))
    declared_digest = template.pop("template_digest", None)
    if declared_digest != semantic_digest(template):
        raise ProspectiveStudyScaffoldError("Study template digest does not replay.")
    template["template_digest"] = declared_digest
    if (
        template.get("artifact_kind") != "prospective_qualification_study_template"
        or template.get("template_version") != "1.0.0"
        or template.get("qualification_authority") != "none_template_only"
        or template.get("expected_envelope_count") != 10
        or template.get("minimum_frozen_case_count") != 140
        or template.get("required_cell_types") != list(REQUIRED_CELL_TYPES)
        or set(template.get("required_blocks", [])) != _QUALIFICATION_ROLES
    ):
        raise ProspectiveStudyScaffoldError("Unsupported ten-envelope study template.")
    envelopes = template.get("envelopes")
    if not isinstance(envelopes, list) or len(envelopes) != 10:
        raise ProspectiveStudyScaffoldError("The scaffold requires exactly ten envelopes.")
    return template


def _validate_authoring_template(value: Mapping[str, Any]) -> dict[str, Any]:
    template = deepcopy(dict(value))
    declared_digest = template.pop("template_digest", None)
    if declared_digest != semantic_digest(template):
        raise ProspectiveStudyScaffoldError("Authoring template digest does not replay.")
    template["template_digest"] = declared_digest
    if (
        template.get("artifact_kind") != "prospective_qualification_authoring_brief_template"
        or template.get("template_version") != "1.0.0"
        or template.get("qualification_authority") != "none_template_only"
    ):
        raise ProspectiveStudyScaffoldError("Unsupported benchmark-blind authoring template.")
    relations = _object_sequence(template.get("relation_briefs"), "relation_briefs")
    cells = _object_sequence(template.get("cell_briefs"), "cell_briefs")
    if len(relations) != 10 or len({item.get("blind_envelope_id") for item in relations}) != 10:
        raise ProspectiveStudyScaffoldError(
            "The authoring template requires ten unique blind relation briefs."
        )
    if {item.get("cell_type") for item in cells} != set(REQUIRED_CELL_TYPES):
        raise ProspectiveStudyScaffoldError(
            "The authoring template must define every required control cell exactly once."
        )
    return template


def _validate_setup(
    value: Mapping[str, Any],
    template: Mapping[str, Any],
    authoring_template: Mapping[str, Any],
) -> dict[str, Any]:
    setup = deepcopy(dict(value))
    _exact_keys(setup, _SETUP_KEYS, "study setup")
    for key in ("study_id", "protocol_id"):
        _nonempty(setup[key], key)
    if setup["template_digest"] != template["template_digest"]:
        raise ProspectiveStudyScaffoldError("Study setup does not bind the selected template.")
    if setup["authoring_template_digest"] != authoring_template["template_digest"]:
        raise ProspectiveStudyScaffoldError(
            "Study setup does not bind the selected benchmark-blind authoring template."
        )
    key_value = str(setup["case_id_key"])
    if len(key_value) != 64 or any(character not in "0123456789abcdef" for character in key_value):
        raise ProspectiveStudyScaffoldError(
            "case_id_key must be 32 bytes encoded as lowercase hex."
        )
    detector_lock = _mapping(setup["detector_lock"], "detector_lock")
    detector_frozen = _timestamp(str(detector_lock.get("frozen_at")), "detector frozen_at")
    assigned = _timestamp(str(setup["assigned_at"]), "assigned_at")
    protocol_frozen = _timestamp(str(setup["protocol_frozen_at"]), "protocol_frozen_at")
    if not detector_frozen <= assigned <= protocol_frozen:
        raise ProspectiveStudyScaffoldError(
            "Study chronology must be detector freeze <= assignment <= protocol freeze."
        )

    participants = _object_sequence(setup["participants"], "participants")
    participant_by_id: dict[str, dict[str, Any]] = {}
    execution_contexts: set[str] = set()
    for participant in participants:
        participant_id = _nonempty(participant.get("participant_id"), "participant_id")
        context_id = _nonempty(
            participant.get("execution_context_id"), "participant execution_context_id"
        )
        if participant_id in participant_by_id or context_id in execution_contexts:
            raise ProspectiveStudyScaffoldError(
                "Participant and execution-context identities must be globally unique."
            )
        participant_by_id[participant_id] = participant
        execution_contexts.add(context_id)

    stage1 = _participant_ids(setup["stage1_reviewer_ids"], count=4, label="stage1")
    stage2 = _participant_ids(setup["stage2_reviewer_ids"], count=2, label="stage2")
    if set(stage1) & set(stage2):
        raise ProspectiveStudyScaffoldError(
            "Stage-1 and Stage-2 reviewer identities must be fresh."
        )
    _require_role(participant_by_id, stage1, "stage1_reviewer")
    _require_role(participant_by_id, stage2, "stage2_reviewer")
    for reviewer_ids, stage in ((stage1, "Stage-1"), (stage2, "Stage-2")):
        providers = {str(participant_by_id[item].get("provider")) for item in reviewer_ids}
        if len(providers) < 2:
            raise ProspectiveStudyScaffoldError(f"{stage} must span at least two providers.")

    blocks = _object_sequence(setup["block_assignments"], "block_assignments")
    if len(blocks) != 2 or Counter(str(block.get("evidence_role")) for block in blocks) != Counter(
        {"threshold_pilot": 1, "qualification_heldout": 1}
    ):
        raise ProspectiveStudyScaffoldError(
            "The scaffold requires one pilot and one qualification-heldout block."
        )
    block_ids: set[str] = set()
    all_block_authors: list[set[str]] = []
    for block in blocks:
        _exact_keys(
            block,
            {
                "block_id",
                "evidence_role",
                "primary_author_ids",
                "renamed_author_ids",
                "submission_deadline",
                "submission_channel",
            },
            "block assignment",
        )
        block_id = _nonempty(block["block_id"], "block_id")
        if block_id in block_ids:
            raise ProspectiveStudyScaffoldError(f"Duplicate block_id: {block_id}")
        block_ids.add(block_id)
        _timestamp(str(block["submission_deadline"]), "submission_deadline")
        submission_channel = _nonempty(block["submission_channel"], "submission_channel")
        if any(
            marker in submission_channel.lower()
            for marker in ("pilot", "heldout", "held-out", "threshold", "qualification")
        ):
            raise ProspectiveStudyScaffoldError(
                "submission_channel must use a block-neutral opaque name."
            )
        primary = set(_participant_ids(block["primary_author_ids"], label="primary authors"))
        renamed = set(_participant_ids(block["renamed_author_ids"], label="renamed authors"))
        if primary & renamed:
            raise ProspectiveStudyScaffoldError(
                "Renamed implementations require authors outside the primary-author pool."
            )
        authors = primary | renamed
        if any(authors & previous for previous in all_block_authors):
            raise ProspectiveStudyScaffoldError(
                "Pilot and held-out blocks require disjoint author identities."
            )
        all_block_authors.append(authors)
        _require_role(participant_by_id, sorted(authors), "author")
    all_authors = set().union(*all_block_authors)
    if all_authors & (set(stage1) | set(stage2)):
        raise ProspectiveStudyScaffoldError("Authors and reviewers must be disjoint.")
    if not any(participant.get("role") == "detector_implementer" for participant in participants):
        raise ProspectiveStudyScaffoldError("At least one detector implementer must be bound.")
    return setup


def _relation_catalog(
    template: Mapping[str, Any], authoring_template: Mapping[str, Any]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    result: dict[str, dict[str, Any]] = {}
    bindings: list[dict[str, Any]] = []
    for envelope, author_relation in zip(
        template["envelopes"], authoring_template["relation_briefs"], strict=True
    ):
        envelope_id = str(envelope["envelope_id"])
        blind_relation_id = str(author_relation["blind_envelope_id"])
        author_visible = deepcopy(dict(author_relation))
        author_visible.pop("blind_envelope_id")
        result[envelope_id] = author_visible
        bindings.append(
            {
                "envelope_id": envelope_id,
                "check_id": envelope["check_id"],
                "candidate_id": envelope["candidate_id"],
                "binding_digest": envelope["binding_digest"],
                "blind_relation_id": blind_relation_id,
            }
        )
    return result, bindings


def _opaque_case_id(
    key: bytes,
    *,
    protocol_id: str,
    block_id: str,
    envelope_id: str,
    cell_type: str,
) -> str:
    message = "\x00".join((protocol_id, block_id, envelope_id, cell_type)).encode("utf-8")
    return "case:" + hmac.new(key, message, hashlib.sha256).hexdigest()[:20]


def _opaque_assignment_token(key: bytes, case_id: str) -> str:
    message = ("author-assignment\x00" + case_id).encode("utf-8")
    return "assignment:" + hmac.new(key, message, hashlib.sha256).hexdigest()[:24]


def _authoring_brief(
    *,
    case_id: str,
    assignment_token: str,
    cell_type: str,
    reference_case_id: str | None,
    relation: Mapping[str, Any],
    cell_brief: Mapping[str, Any],
    neutral_repository_deliverables: Any,
    submission_deadline: str,
    submission_channel: str,
) -> dict[str, Any]:
    barrier = [
        "Do not inspect public benchmark cases or internal development fixtures.",
        "Do not inspect detector source, recognizers, patterns, prior outputs, or expected behavior.",
        "Do not run sc-referee or ask another actor to predict its response.",
        "Do not communicate case content to reviewers or detector implementers.",
    ]
    if cell_type == "renamed_implementation":
        barrier.append(
            "Do not inspect the referenced error-bearing case or communicate with its author."
        )
    return {
        "artifact_kind": "prospective_case_authoring_brief",
        "scaffold_version": SCAFFOLD_VERSION,
        "opaque_case_id": case_id,
        "block_neutral_assignment_token": assignment_token,
        "one_relation_brief": deepcopy(dict(relation)),
        "one_cell_brief": deepcopy(dict(cell_brief)),
        "paired_case_access": (
            {
                "reference_case_id": reference_case_id,
                "access_rule": "available_after_the_referenced_case_is_frozen",
            }
            if cell_type == "corrected_twin"
            else {"reference_case_id": None, "access_rule": "none"}
        ),
        "neutral_repository_deliverables": deepcopy(neutral_repository_deliverables),
        "submission_deadline": submission_deadline,
        "submission_channel": submission_channel,
        "quality_constraints": [
            "Use a scientifically plausible setting and enough surrounding workflow to test exact scope.",
            "Keep the target relation atomic; do not seed unrelated scientific mistakes.",
            "Do not use benchmark names, repository names, answer values, grading tolerances, or detector phrases.",
            "Do not execute untrusted project-authored code during review or detector evaluation.",
        ],
        "information_barrier": barrier,
        "qualification_authority": "none_authoring_instruction_only",
    }


def _author_queue(
    *,
    protocol: Mapping[str, Any],
    author_id: str,
    briefs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _self_digest(
        {
            "artifact_kind": "prospective_author_queue",
            "scaffold_version": SCAFFOLD_VERSION,
            "protocol_ref": _protocol_ref(protocol),
            "author_id": author_id,
            "briefs": sorted(
                (deepcopy(dict(brief)) for brief in briefs),
                key=lambda brief: str(brief["opaque_case_id"]),
            ),
            "distribution_rule": "deliver_only_to_named_author_in_named_execution_context",
            "qualification_authority": "none_author_queue_only",
        },
        "queue_digest",
    )


def _blind_review_queue(
    *,
    protocol: Mapping[str, Any],
    block_id: str,
    evidence_role: str,
    stage: str,
    reviewer_id: str,
    case_ids: Sequence[str],
) -> dict[str, Any]:
    release_gate = (
        "after_case_material_and_method_contract_are_sealed"
        if stage == "stage1"
        else "after_all_stage1_panel_records_are_sealed"
    )
    return _self_digest(
        {
            "artifact_kind": "prospective_blind_review_queue",
            "scaffold_version": SCAFFOLD_VERSION,
            "protocol_ref": _protocol_ref(protocol),
            "block_id": block_id,
            "evidence_role": evidence_role,
            "review_stage": stage,
            "reviewer_id": reviewer_id,
            "case_ids": list(case_ids),
            "release_gate": release_gate,
            "hidden_from_reviewer": [
                "designed control cell",
                "relation envelope identity",
                "authoring brief",
                "other reviewer submissions",
                "detector output",
            ],
            "qualification_authority": "none_review_queue_only",
        },
        "queue_digest",
    )


def _distribution_plan(
    protocol: Mapping[str, Any], participant_by_id: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    return _self_digest(
        {
            "artifact_kind": "prospective_distribution_plan",
            "scaffold_version": SCAFFOLD_VERSION,
            "protocol_ref": _protocol_ref(protocol),
            "access_boundaries": [
                {
                    "path": "releases/pilot/authors/",
                    "release_when": "protocol_frozen",
                    "recipient_rule": "each file only to its named author and execution context",
                },
                {
                    "path": "releases/pilot/stage1-reviewers/",
                    "release_when": "all pilot case materials and contracts are sealed",
                    "recipient_rule": "each file only to its named Stage-1 reviewer",
                },
                {
                    "path": "coordinator/staged-pilot/stage2-reviewers/",
                    "release_when": "all pilot Stage-1 panel records are sealed",
                    "recipient_rule": "each file only to its named fresh Stage-2 reviewer",
                },
                {
                    "path": "coordinator/staged-heldout/",
                    "release_when": "complete pilot ledger and approved digest-bound threshold decision",
                    "recipient_rule": "release one role-specific file at a time; retain all outcomes",
                },
            ],
            "participant_context_commitments": [
                {
                    "participant_id": participant_id,
                    "role": participant["role"],
                    "provider": participant["provider"],
                    "execution_context_id": participant["execution_context_id"],
                    "identity_evidence_digest": participant["identity_evidence_digest"],
                }
                for participant_id, participant in sorted(participant_by_id.items())
            ],
            "external_enforcement_required": [
                "filesystem or document access control",
                "participant identity authentication",
                "provider and execution-context attestation",
                "case-material and transcript capture",
                "chronological release logging",
                "no-replacement and all-outcome retention",
            ],
            "qualification_authority": "none_distribution_plan_only",
        },
        "plan_digest",
    )


def _package_manifest(
    files: Mapping[str, bytes],
    *,
    study_id: str,
    protocol: Mapping[str, Any],
    template_digest: str,
    authoring_template_digest: str,
    case_id_key_digest: str,
) -> dict[str, Any]:
    paths = [
        {"path": path, "sha256": sha256_digest(payload), "size_bytes": len(payload)}
        for path, payload in sorted(files.items())
    ]
    pilot_count = sum(
        assignment["block_id"]
        == next(
            block["block_id"]
            for block in protocol["blocks"]
            if block["evidence_role"] == "threshold_pilot"
        )
        for assignment in protocol["assignments"]
    )
    heldout_count = len(protocol["assignments"]) - pilot_count
    return _self_digest(
        {
            "artifact_kind": "prospective_study_scaffold_manifest",
            "scaffold_version": SCAFFOLD_VERSION,
            "study_id": study_id,
            "protocol_template_digest": template_digest,
            "authoring_template_digest": authoring_template_digest,
            "protocol_ref": _protocol_ref(protocol),
            "case_id_key_digest": case_id_key_digest,
            "case_counts": {
                "total": len(protocol["assignments"]),
                "threshold_pilot": pilot_count,
                "qualification_heldout": heldout_count,
            },
            "contains_case_material": False,
            "contains_scientific_labels": False,
            "contains_review_decisions": False,
            "contains_detector_observations": False,
            "contains_threshold_decision": False,
            "qualification_authority": "none_scaffold_only",
            "files": paths,
        },
        "manifest_digest",
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


def _put_json(files: dict[str, bytes], path: str, value: Mapping[str, Any]) -> None:
    if path in files:
        raise ProspectiveStudyScaffoldError(f"Duplicate generated path: {path}")
    files[path] = (canonical_json(value) + "\n").encode("utf-8")


def _path_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProspectiveStudyScaffoldError(f"{label} must be an object.")
    return dict(value)


def _object_sequence(value: Any, label: str) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ProspectiveStudyScaffoldError(f"{label} must be an array.")
    result = [_mapping(item, f"{label} item") for item in value]
    if not result:
        raise ProspectiveStudyScaffoldError(f"{label} must not be empty.")
    return result


def _participant_ids(value: Any, *, label: str, count: int | None = None) -> list[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ProspectiveStudyScaffoldError(f"{label} must be an array.")
    result = [_nonempty(item, f"{label} participant") for item in value]
    if not result or len(set(result)) != len(result):
        raise ProspectiveStudyScaffoldError(f"{label} identities must be nonempty and unique.")
    if count is not None and len(result) != count:
        raise ProspectiveStudyScaffoldError(f"{label} requires exactly {count} participants.")
    return result


def _require_role(
    participants: Mapping[str, Mapping[str, Any]], participant_ids: Sequence[str], role: str
) -> None:
    for participant_id in participant_ids:
        participant = participants.get(participant_id)
        if participant is None or participant.get("role") != role:
            raise ProspectiveStudyScaffoldError(
                f"Participant {participant_id!r} is not bound as {role!r}."
            )


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ProspectiveStudyScaffoldError(
            f"{label} keys differ; missing={sorted(expected - actual)}, extra={sorted(actual - expected)}."
        )


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProspectiveStudyScaffoldError(f"{label} must be a nonempty string.")
    return value


def _timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProspectiveStudyScaffoldError(f"{label} must be an ISO-8601 timestamp.") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProspectiveStudyScaffoldError(f"{label} must include a timezone.")
    return parsed


def load_json_object(path: Path) -> dict[str, Any]:
    """Load one JSON object for the standalone scaffold command."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProspectiveStudyScaffoldError(f"Expected a JSON object: {path}")
    return value
