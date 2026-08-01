from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, stable_id
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.version import SCHEMA_VERSION

SCOPE_SELECTION_PROFILE = "bounded-review-scope-selection-v1"
MAX_SCOPE_SELECTION_CANDIDATES = 64
SCOPE_SELECTION_DIMENSIONS = {
    "analysis_source": "analysis_source_selection",
    "material_input": "material_input_selection",
    "analysis_output": "analysis_output_selection",
}


@dataclass(frozen=True)
class ScopeSelectionBuild:
    questions: tuple[dict[str, Any], ...]
    projection: dict[str, Any]


def build_scope_selection_contracts(
    *,
    run_id: str,
    created_at: str,
    repository_snapshot: dict[str, Any],
    file_records: list[dict[str, Any]],
    asset_identities: list[dict[str, Any]],
    parser_results: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    explicit_material_inputs: tuple[str, ...] = (),
) -> ScopeSelectionBuild:
    """Build finite scope questions without inferring scientific or execution authority."""

    snapshot_id = str(repository_snapshot["snapshot_id"])
    snapshot_digest = str(repository_snapshot["snapshot_digest"])
    identities = {
        str(item["asset_identity_id"]): item
        for item in asset_identities
        if isinstance(item.get("asset_identity_id"), str)
    }
    regular_paths = {
        str(item["path"]): item
        for item in file_records
        if item.get("entry_kind") == "regular_file" and _safe_path(item.get("path"))
    }
    parsed_paths = {
        str(source_ref["path"]): str(source_ref["content_digest"])
        for item in parser_results
        if item.get("state") in {"parsed", "partially_parsed"}
        and isinstance((source_ref := item.get("source_ref")), dict)
        and _safe_path(source_ref.get("path"))
        and isinstance(source_ref.get("content_digest"), str)
    }

    explicit_inputs = {_normalized_path(value) for value in explicit_material_inputs}
    source_candidates = _source_candidates(file_records, identities, regular_paths, parsed_paths)
    artifact_input_candidates = _artifact_candidates(
        artifacts,
        identities,
        regular_paths,
        kinds={"data_file", "table"},
        observed_roles={"input_file", "material_input", "tabular_input"},
        explicitly_selected_paths=explicit_inputs,
    )
    artifact_input_paths = {str(item["path"]) for item in artifact_input_candidates}
    input_candidates = _deduplicate_candidates(
        [
            *artifact_input_candidates,
            *(
                item
                for item in _explicit_file_candidates(
                    file_records,
                    identities,
                    explicitly_selected_paths=explicit_inputs,
                )
                if item["path"] not in artifact_input_paths
            ),
        ]
    )
    output_candidates = _artifact_candidates(
        artifacts,
        identities,
        regular_paths,
        kinds={"result_file", "table"},
        observed_roles={"output_file", "analysis_output", "tabular_output"},
    )
    by_kind = {
        "analysis_source": source_candidates,
        "material_input": input_candidates,
        "analysis_output": output_candidates,
    }
    questions: list[dict[str, Any]] = []
    selections: dict[str, Any] = {}
    for kind, candidates in by_kind.items():
        explicit = (
            [item for item in candidates if item["path"] in explicit_inputs]
            if kind == "material_input" and explicit_inputs
            else []
        )
        entry = _initial_projection_entry(kind, candidates, explicit)
        if not explicit and 2 <= len(candidates) <= MAX_SCOPE_SELECTION_CANDIDATES:
            question = _scope_question(
                run_id=run_id,
                created_at=created_at,
                snapshot_id=snapshot_id,
                snapshot_digest=snapshot_digest,
                kind=kind,
                candidates=candidates,
            )
            questions.append(question)
            entry["question_ref"] = typed_ref("material_question", str(question["question_id"]))
        selections[kind] = entry
    projection = {
        "profile": SCOPE_SELECTION_PROFILE,
        "source_snapshot_digest": snapshot_digest,
        "snapshot_ref": typed_ref("repository_snapshot", snapshot_id),
        "selections": selections,
        "authority_limitation": (
            "Selections define review scope only; they do not establish execution, lineage, "
            "scientific intent, materiality, or correctness."
        ),
    }
    projection["projection_digest"] = semantic_digest(projection)
    return ScopeSelectionBuild(tuple(questions), projection)


def validate_scope_selection_question(
    parent_bundle: dict[str, Any],
    question: dict[str, Any],
    snapshot_digest: str,
) -> dict[str, Any]:
    """Return a validated closed selection contract or raise ValueError."""

    extensions = question.get("extensions")
    if not isinstance(extensions, dict) or extensions.get("x-selection-profile") != (
        SCOPE_SELECTION_PROFILE
    ):
        raise ValueError("question is not a bounded review-scope selection")
    kind = extensions.get("x-selection-kind")
    if kind not in SCOPE_SELECTION_DIMENSIONS:
        raise ValueError("scope-selection kind is unsupported")
    if question.get("unknown_semantic_dimension") != SCOPE_SELECTION_DIMENSIONS[kind]:
        raise ValueError("scope-selection dimension does not match its kind")
    if extensions.get("x-source-snapshot-digest") != snapshot_digest:
        raise ValueError("scope-selection question has a stale snapshot binding")
    snapshot = parent_bundle.get("repository_snapshots")
    if not isinstance(snapshot, list) or len(snapshot) != 1:
        raise ValueError("scope-selection question has no unique RepositorySnapshot")
    expected_snapshot_ref = typed_ref("repository_snapshot", str(snapshot[0].get("snapshot_id")))
    if extensions.get("x-snapshot-ref") != expected_snapshot_ref:
        raise ValueError("scope-selection question snapshot reference is invalid")
    bindings = extensions.get("x-candidate-bindings")
    if not isinstance(bindings, list) or len(bindings) < 2:
        raise ValueError("scope-selection question has no ambiguous candidate set")
    if len(bindings) > MAX_SCOPE_SELECTION_CANDIDATES:
        raise ValueError("scope-selection candidate set exceeds the bounded limit")

    records = _record_index(parent_bundle)
    identity_index = {
        str(item.get("asset_identity_id")): item
        for item in parent_bundle.get("asset_identities", [])
        if isinstance(item, dict) and isinstance(item.get("asset_identity_id"), str)
    }
    normalized: list[dict[str, Any]] = []
    seen_refs: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ValueError("scope-selection candidate binding is malformed")
        record_ref = binding.get("record_ref")
        identity_ref = binding.get("asset_identity_ref")
        path = binding.get("path")
        digest = binding.get("content_digest")
        source_ref = binding.get("source_ref")
        if (
            not isinstance(record_ref, dict)
            or not isinstance(identity_ref, dict)
            or not _safe_path(path)
            or not isinstance(digest, str)
            or not isinstance(source_ref, dict)
        ):
            raise ValueError("scope-selection candidate binding is incomplete or unsafe")
        assert isinstance(path, str)
        key = canonical_json(record_ref)
        if key in seen_refs:
            raise ValueError("scope-selection candidate identity is duplicated")
        seen_refs.add(key)
        record = records.get(key)
        identity = identity_index.get(str(identity_ref.get("record_id")))
        if record is None or identity is None:
            raise ValueError("scope-selection candidate record or identity is missing")
        if (
            identity_ref.get("record_type") != "asset_identity"
            or identity.get("tier") != "full_digest"
            or identity.get("asset_ref") != record_ref
            or identity.get("identity_evidence") != {"kind": "full_digest", "digest": digest}
            or record.get("asset_identity_ref") != identity_ref
            or record.get("path") != path
            or source_ref != _candidate_source_ref(path, digest)
        ):
            raise ValueError("scope-selection candidate identity binding is inconsistent")
        if record_ref.get("record_type") == "file_record" and record.get("entry_kind") != (
            "regular_file"
        ):
            raise ValueError("scope-selection source candidate is not a regular file")
        normalized.append(copy.deepcopy(binding))
    if normalized != sorted(normalized, key=lambda item: (item["path"], canonical_json(item))):
        raise ValueError("scope-selection candidates are not canonical")
    _validate_candidate_answers(question, kind, normalized)
    return {
        "kind": kind,
        "dimension": SCOPE_SELECTION_DIMENSIONS[kind],
        "snapshot_ref": expected_snapshot_ref,
        "candidate_bindings": normalized,
        "max_selections": int(extensions.get("x-max-selections", 0)),
    }


def selected_bindings_from_answer(
    contract: dict[str, Any], answer: dict[str, Any]
) -> tuple[str, list[dict[str, Any]]]:
    """Validate and project one Answer against an already validated selection contract."""

    bindings = contract["candidate_bindings"]
    by_ref = {canonical_json(item["record_ref"]): item for item in bindings}
    if answer.get("answer_kind") == "unknown":
        return "unknown", []
    value = answer.get("answer_value")
    if not isinstance(value, dict) or value.get("selection_kind") != contract["kind"]:
        raise ValueError("scope-selection Answer has the wrong selection kind")
    selected = value.get("selected_candidate_refs")
    if not isinstance(selected, list):
        raise ValueError("scope-selection Answer has no selected candidate references")
    selected_keys = [canonical_json(item) for item in selected]
    if len(set(selected_keys)) != len(selected_keys):
        raise ValueError("scope-selection Answer references are not unique")
    candidate_order = {
        canonical_json(item["record_ref"]): index for index, item in enumerate(bindings)
    }
    if any(key not in candidate_order for key in selected_keys) or selected_keys != sorted(
        selected_keys, key=lambda key: candidate_order[key]
    ):
        raise ValueError("scope-selection Answer references are not in canonical candidate order")
    if len(selected) > contract["max_selections"]:
        raise ValueError("scope-selection Answer exceeds its bounded selection limit")
    resolved: list[dict[str, Any]] = []
    for record_ref in selected:
        binding = by_ref.get(canonical_json(record_ref))
        if binding is None:
            raise ValueError("scope-selection Answer contains an unlisted candidate")
        resolved.append(copy.deepcopy(binding))
    return ("selected" if resolved else "selected_none"), resolved


def update_scope_selection_projection(
    prior: dict[str, Any],
    *,
    contract: dict[str, Any],
    answer: dict[str, Any],
    snapshot_digest: str,
) -> dict[str, Any]:
    """Update one internal lock projection while preserving all other selection dimensions."""

    projection = copy.deepcopy(prior)
    digest_input = copy.deepcopy(projection)
    recorded_digest = digest_input.pop("projection_digest", None)
    if semantic_digest(digest_input) != recorded_digest:
        raise ValueError("scope-selection projection digest mismatch")
    if (
        projection.get("profile") != SCOPE_SELECTION_PROFILE
        or projection.get("source_snapshot_digest") != snapshot_digest
        or projection.get("snapshot_ref") != contract["snapshot_ref"]
    ):
        raise ValueError("scope-selection projection is stale or incompatible")
    status, selected = selected_bindings_from_answer(contract, answer)
    entry = copy.deepcopy(projection["selections"][contract["kind"]])
    entry.update(
        {
            "status": status,
            "selected_record_refs": [item["record_ref"] for item in selected],
            "selected_identity_refs": [item["asset_identity_ref"] for item in selected],
            "selected_paths": [item["path"] for item in selected],
            "answer_ref": typed_ref("answer", str(answer["answer_id"])),
            "question_ref": copy.deepcopy(answer["question_ref"]),
            "selection_authority": "interactive_scientist",
        }
    )
    projection["selections"][contract["kind"]] = entry
    projection.pop("projection_digest", None)
    projection["projection_digest"] = semantic_digest(projection)
    return projection


def refresh_scope_selection_projection(
    prior: dict[str, Any],
    current: dict[str, Any],
    *,
    snapshot_digest: str,
) -> dict[str, Any]:
    """Rebind preserved selections to current records for the same immutable snapshot."""

    _validate_projection(prior, snapshot_digest)
    _validate_projection(current, snapshot_digest)
    if prior.get("snapshot_ref") != current.get("snapshot_ref"):
        raise ValueError("scope-selection projection snapshot reference changed")

    refreshed = copy.deepcopy(current)
    current_selections = refreshed.get("selections")
    prior_selections = prior.get("selections")
    if not isinstance(current_selections, dict) or not isinstance(prior_selections, dict):
        raise ValueError("scope-selection projection has no complete selections map")
    if set(current_selections) != set(SCOPE_SELECTION_DIMENSIONS) or set(prior_selections) != set(
        SCOPE_SELECTION_DIMENSIONS
    ):
        raise ValueError("scope-selection projection dimensions are incomplete")

    resolved_statuses = {
        "selected",
        "selected_none",
        "unknown",
        "selected_explicit_invocation",
    }
    for kind in SCOPE_SELECTION_DIMENSIONS:
        prior_entry = prior_selections[kind]
        current_entry = current_selections[kind]
        if not isinstance(prior_entry, dict) or not isinstance(current_entry, dict):
            raise ValueError("scope-selection projection entry is malformed")
        status = prior_entry.get("status")
        if status not in resolved_statuses:
            continue

        candidate_refs = current_entry.get("candidate_record_refs")
        candidate_identities = current_entry.get("candidate_identity_refs")
        candidate_paths = current_entry.get("candidate_paths")
        if not (
            isinstance(candidate_refs, list)
            and isinstance(candidate_identities, list)
            and isinstance(candidate_paths, list)
            and len(candidate_refs) == len(candidate_identities) == len(candidate_paths)
        ):
            raise ValueError("current scope-selection candidates are malformed")
        current_by_ref = {
            canonical_json(record_ref): (record_ref, identity_ref, path)
            for record_ref, identity_ref, path in zip(
                candidate_refs, candidate_identities, candidate_paths, strict=True
            )
        }
        selected_refs = prior_entry.get("selected_record_refs")
        if not isinstance(selected_refs, list):
            raise ValueError("preserved scope selection has no selected record references")
        rebound = [current_by_ref.get(canonical_json(record_ref)) for record_ref in selected_refs]
        if any(item is None for item in rebound):
            raise ValueError("preserved scope selection is absent from the identical snapshot")

        resolved_entry = copy.deepcopy(current_entry)
        resolved_entry.update(
            {
                "status": status,
                "selected_record_refs": [copy.deepcopy(item[0]) for item in rebound if item],
                "selected_identity_refs": [copy.deepcopy(item[1]) for item in rebound if item],
                "selected_paths": [str(item[2]) for item in rebound if item],
                "selection_authority": prior_entry.get("selection_authority", "none"),
            }
        )
        for field in ("answer_ref", "question_ref"):
            if field in prior_entry:
                resolved_entry[field] = copy.deepcopy(prior_entry[field])
            elif field in resolved_entry:
                del resolved_entry[field]
        current_selections[kind] = resolved_entry

    refreshed.pop("projection_digest", None)
    refreshed["projection_digest"] = semantic_digest(refreshed)
    return refreshed


def is_scope_selection_question(question: dict[str, Any]) -> bool:
    extensions = question.get("extensions")
    return isinstance(extensions, dict) and extensions.get("x-selection-profile") == (
        SCOPE_SELECTION_PROFILE
    )


def _validate_projection(projection: dict[str, Any], snapshot_digest: str) -> None:
    digest_input = copy.deepcopy(projection)
    recorded_digest = digest_input.pop("projection_digest", None)
    if semantic_digest(digest_input) != recorded_digest:
        raise ValueError("scope-selection projection digest mismatch")
    if (
        projection.get("profile") != SCOPE_SELECTION_PROFILE
        or projection.get("source_snapshot_digest") != snapshot_digest
    ):
        raise ValueError("scope-selection projection is stale or incompatible")


def _source_candidates(
    file_records: list[dict[str, Any]],
    identities: dict[str, dict[str, Any]],
    regular_paths: dict[str, dict[str, Any]],
    parsed_paths: dict[str, str],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for record in file_records:
        path = record.get("path")
        if (
            record.get("classification") != "analysis_source"
            or record.get("entry_kind") != "regular_file"
            or not _safe_path(path)
            or path not in regular_paths
            or path not in parsed_paths
        ):
            continue
        binding = _binding(record, "file_record", identities)
        if binding is not None and binding["content_digest"] == parsed_paths[path]:
            candidates.append(binding)
    return _deduplicate_candidates(candidates)


def _artifact_candidates(
    artifacts: list[dict[str, Any]],
    identities: dict[str, dict[str, Any]],
    regular_paths: dict[str, dict[str, Any]],
    *,
    kinds: set[str],
    observed_roles: set[str],
    explicitly_selected_paths: set[str] | None = None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for record in artifacts:
        path = record.get("path")
        if (
            record.get("kind") not in kinds
            or (
                record.get("observed_role") not in observed_roles
                and path not in (explicitly_selected_paths or set())
            )
            or not _safe_path(path)
            or path not in regular_paths
        ):
            continue
        binding = _binding(record, "artifact", identities)
        if binding is not None:
            candidates.append(binding)
    return _deduplicate_candidates(candidates)


def _explicit_file_candidates(
    file_records: list[dict[str, Any]],
    identities: dict[str, dict[str, Any]],
    *,
    explicitly_selected_paths: set[str],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for record in file_records:
        if (
            record.get("entry_kind") != "regular_file"
            or record.get("path") not in explicitly_selected_paths
        ):
            continue
        binding = _binding(record, "file_record", identities)
        if binding is not None:
            candidates.append(binding)
    return _deduplicate_candidates(candidates)


def _binding(
    record: dict[str, Any],
    record_type: str,
    identities: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    identity_ref = record.get("asset_identity_ref")
    if not isinstance(identity_ref, dict) or identity_ref.get("record_type") != "asset_identity":
        return None
    identity = identities.get(str(identity_ref.get("record_id")))
    identifier_key = "file_record_id" if record_type == "file_record" else "artifact_id"
    record_id = record.get(identifier_key)
    path = record.get("path")
    if not isinstance(record_id, str) or not _safe_path(path) or identity is None:
        return None
    record_ref = typed_ref(record_type, record_id)
    evidence = identity.get("identity_evidence")
    if (
        identity.get("tier") != "full_digest"
        or identity.get("asset_ref") != record_ref
        or not isinstance(evidence, dict)
        or evidence.get("kind") != "full_digest"
        or not isinstance(evidence.get("digest"), str)
    ):
        return None
    digest = str(evidence["digest"])
    return {
        "record_ref": record_ref,
        "asset_identity_ref": copy.deepcopy(identity_ref),
        "path": str(path),
        "content_digest": digest,
        "source_ref": _candidate_source_ref(str(path), digest),
    }


def _deduplicate_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    ambiguous_paths: set[str] = set()
    for candidate in sorted(candidates, key=lambda item: (item["path"], canonical_json(item))):
        path = str(candidate["path"])
        existing = by_path.get(path)
        if existing is None:
            by_path[path] = candidate
        elif canonical_json(existing["record_ref"]) != canonical_json(candidate["record_ref"]):
            ambiguous_paths.add(path)
    return [by_path[path] for path in sorted(by_path) if path not in ambiguous_paths]


def _initial_projection_entry(
    kind: str,
    candidates: list[dict[str, Any]],
    explicit: list[dict[str, Any]],
) -> dict[str, Any]:
    if explicit:
        status = "selected_explicit_invocation"
    elif not candidates:
        status = "unavailable"
    elif len(candidates) == 1:
        status = "unique_candidate_unselected"
    elif len(candidates) > MAX_SCOPE_SELECTION_CANDIDATES:
        status = "selection_over_budget"
    else:
        status = "unresolved"
    selected = explicit
    return {
        "status": status,
        "candidate_record_refs": [item["record_ref"] for item in candidates],
        "candidate_identity_refs": [item["asset_identity_ref"] for item in candidates],
        "candidate_paths": [item["path"] for item in candidates],
        "selected_record_refs": [item["record_ref"] for item in selected],
        "selected_identity_refs": [item["asset_identity_ref"] for item in selected],
        "selected_paths": [item["path"] for item in selected],
        "selection_authority": "explicit_invocation" if explicit else "none",
        "selection_kind": kind,
    }


def _scope_question(
    *,
    run_id: str,
    created_at: str,
    snapshot_id: str,
    snapshot_digest: str,
    kind: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    dimension = SCOPE_SELECTION_DIMENSIONS[kind]
    question_id = stable_id(
        "question-review-scope",
        run_id,
        kind,
        *(canonical_json(item["record_ref"]) for item in candidates),
    )
    labels = {
        "analysis_source": "analysis source file",
        "material_input": "material input artifact",
        "analysis_output": "analysis output artifact",
    }
    prompts = {
        "analysis_source": (
            "Which inventoried analysis source file or files should be in scope for this audit?"
        ),
        "material_input": (
            "Which inventoried data artifact or artifacts are material inputs to the analysis "
            "being audited?"
        ),
        "analysis_output": (
            "Which snapshotted result artifact or artifacts are outputs of the analysis being "
            "audited?"
        ),
    }
    options = [
        {
            "answer_id": stable_id(
                "answer-option", question_id, canonical_json(item["record_ref"])
            ),
            "label": item["path"],
            "value": {
                "selection_kind": kind,
                "selected_candidate_refs": [item["record_ref"]],
            },
            "consequence": (
                f"This exact {labels[kind]} identity becomes selected review scope; this does "
                "not establish execution, lineage, or scientific correctness."
            ),
        }
        for item in candidates
    ]
    options.extend(
        [
            {
                "answer_id": stable_id("answer-option", question_id, "select-none"),
                "label": "None of these candidates",
                "value": {"selection_kind": kind, "selected_candidate_refs": []},
                "consequence": (
                    "No listed identity is selected for this review-scope dimension; this does "
                    "not establish that no such source or artifact exists."
                ),
            },
            {
                "answer_id": stable_id("answer-option", question_id, "retain-unknown"),
                "label": "Retain as unknown",
                "value": {"action": "retain_unknown"},
                "consequence": "The competing candidates remain unresolved.",
            },
        ]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "material_question",
        "question_id": question_id,
        "audit_run_id": run_id,
        "question": prompts[kind],
        "unknown_semantic_dimension": dimension,
        "why_it_matters": (
            "The selected immutable identities bound downstream static scope joins. Scientist "
            "selection defines review scope only."
        ),
        "candidate_answers": options,
        "evidence_searched": [
            {
                "source": "immutable repository inventory and typed static artifacts",
                "result": (
                    f"{len(candidates)} fully identified {labels[kind]} candidates remained; "
                    "the controller cannot choose their review materiality."
                ),
            }
        ],
        "blocked_detector_ids": [],
        "affected_claim_ids": [],
        "linked_conditional_concern_ids": [],
        "priority": "medium",
        "status": "open",
        "answer_ids": [],
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_review_scope_question_generation", created_at
        ),
        "extensions": {
            "x-selection-profile": SCOPE_SELECTION_PROFILE,
            "x-selection-kind": kind,
            "x-source-snapshot-digest": snapshot_digest,
            "x-snapshot-ref": typed_ref("repository_snapshot", snapshot_id),
            "x-candidate-bindings": copy.deepcopy(candidates),
            "x-min-selections": 0,
            "x-max-selections": 8 if kind == "material_input" else len(candidates),
            "x-multiple-selection-command": "record-scope-answer",
            "x-authority-limitation": (
                "A scientist Answer establishes review scope only, not execution, lineage, "
                "scientific intent, materiality outside this audit, or correctness."
            ),
        },
    }


def _validate_candidate_answers(
    question: dict[str, Any], kind: str, bindings: list[dict[str, Any]]
) -> None:
    expected_values = [
        {
            "selection_kind": kind,
            "selected_candidate_refs": [item["record_ref"]],
        }
        for item in bindings
    ]
    expected_values.extend(
        [
            {"selection_kind": kind, "selected_candidate_refs": []},
            {"action": "retain_unknown"},
        ]
    )
    actual = question.get("candidate_answers")
    if not isinstance(actual, list) or [item.get("value") for item in actual] != expected_values:
        raise ValueError("scope-selection answer options do not match the candidate bindings")


def _record_index(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for key, record_type, identifier in (
        ("file_records", "file_record", "file_record_id"),
        ("artifacts", "artifact", "artifact_id"),
    ):
        for item in bundle.get(key, []):
            if isinstance(item, dict) and isinstance(item.get(identifier), str):
                index[canonical_json(typed_ref(record_type, str(item[identifier])))] = item
    return index


def _candidate_source_ref(path: str, digest: str) -> dict[str, Any]:
    return {
        "source_kind": "artifact",
        "locator": path,
        "path": path,
        "content_digest": digest,
    }


def _normalized_path(value: str) -> str:
    candidate = PurePosixPath(value)
    return candidate.as_posix()


def _safe_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    candidate = PurePosixPath(value)
    return not candidate.is_absolute() and ".." not in candidate.parts
