from __future__ import annotations

import copy
import json
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, cast
from uuid import uuid4

from sc_referee.agent_protocol import load_audit_status
from sc_referee.controller import (
    _build_contract_questions,
    _derive_general_from_lock,
    _extract_resolved_literal_claims,
    _finalize_bundle,
    _general_coverage_inputs,
    _general_coverage_record,
    _general_disclosures,
    _GeneralCoverageDisposition,
    _resolve_publication_surface,
    _unsupported_source_paths,
)
from sc_referee.core.deadline_ledger import (
    LEDGER_FILENAME,
    DeadlineLedgerError,
    advance_or_exhaust,
    complete_segment,
    current_segment,
    load_deadline_ledger,
    pause_for_scientist,
    resume_after_scientist,
    start_linked_segment,
    write_deadline_ledger,
)
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.core.state import AuditState, transition
from sc_referee.expected_count_obligation import (
    valid_analysis_expected_count_obligation_question,
)
from sc_referee.lineage import bind_bounded_claim_lineage
from sc_referee.method_contracts import (
    EXPECTED_COUNT_PROFILE_ID,
    EXPECTED_COUNT_PROFILE_VERSION,
    EXPECTED_COUNT_REQUIRED_DIMENSIONS,
    MethodContractError,
    expected_count_dimension_values,
    expected_count_profile_from_dimensions,
)
from sc_referee.performance import build_semantic_lock_performance_record
from sc_referee.posthoc_method_ledger import (
    PosthocMethodLedgerError,
    validate_posthoc_requirement,
)
from sc_referee.records.normalization import write_normalized_json
from sc_referee.records.observed import (
    build_audit_run_record,
    build_file_records,
    controller_provenance,
    typed_ref,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.reproduction import build_reproduction_requests
from sc_referee.snapshot.repository import capture_repository
from sc_referee.storage.jsonl import JsonlRecordStore
from sc_referee.storage.layout import AuditLayout
from sc_referee.version import SCHEMA_VERSION, __version__

_SESSION_FILE = "prelock-session.json"
_PARENT_BUNDLE_FILE = "parent-audit.bundle.json"
_PARENT_LOCK_FILE = "parent-semantic.lock.json"
_PACKET_PROFILE = "canonical-json-excluding-packet-digest-v1"
_ANSWER_PROFILE = "canonical-json-excluding-answer-digest-v1"
_PROMPT_TEMPLATE_ID = "prompt:bounded-semantic-resolution-v1"
_PROMPT_TEMPLATE = (
    "Propose only the requested public record types from the exact packet sources and records. "
    "Keep every model-authored SemanticAssertion proposed and Finding-ineligible or pending. "
    "Do not execute project code, search for additional scientific errors, infer missing source "
    "text, establish observed computation, or treat confidence as a material premise."
)


class InteractionProtocolError(ValueError):
    """Raised when a pre-lock command would violate the typed interaction protocol."""


def resume_semantics(
    source_audit: Path,
    repository: Path,
    output: Path,
    schema_root: Path,
    *,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Create a linked, exact-snapshot, append-only pre-lock interaction segment."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"resume output already exists: {output}")
    source_status = load_audit_status(source_audit, schema_root)
    source_layout = AuditLayout(source_audit.resolve())
    parent_bundle = _read_object(source_layout.bundle_path)
    parent_lock = _read_object(source_layout.lock_path)
    if parent_lock.get("lock_kind") != "general_static_v1":
        raise InteractionProtocolError("only a general static audit can start this resume path")
    questions = [
        item for item in parent_bundle.get("material_questions", []) if item.get("status") == "open"
    ]
    if not questions:
        raise InteractionProtocolError("source audit has no open MaterialQuestion")

    timestamp = created_at or _timestamp_now()
    run_id = f"audit:{uuid4().hex}"
    layout = AuditLayout(output)
    layout.create()
    registry = LocalSchemaRegistry(schema_root)
    store = JsonlRecordStore(layout.observed)

    created = build_audit_run_record(
        run_id,
        AuditState.CREATED.value,
        timestamp,
        parent_run_id=source_status.audit_run_id,
    )
    registry.validate(created)
    store.append(created)

    snapshot = capture_repository(
        repository.resolve(), layout.observed / "snapshot", run_id, captured_at=timestamp
    )
    source_snapshot_digest = _source_snapshot_digest(parent_bundle)
    if snapshot.snapshot_record["snapshot_digest"] != source_snapshot_digest:
        raise InteractionProtocolError(
            "repository snapshot differs from the integrity-verified source audit"
        )
    registry.validate(snapshot.snapshot_record)
    write_normalized_json(layout.observed / "snapshot.json", snapshot.snapshot_record)
    public_files = build_file_records(
        snapshot.file_records,
        snapshot.asset_identity_records,
        str(snapshot.snapshot_record["snapshot_id"]),
        timestamp,
    )
    for record in [*snapshot.asset_identity_records, *public_files]:
        registry.validate(record)
        store.append(record)
    for record in [
        *parent_lock.get("cache_entries", []),
        *parent_lock.get("cache_policies", []),
    ]:
        registry.validate(record)
        store.append(record)

    write_normalized_json(layout.observed / _PARENT_BUNDLE_FILE, parent_bundle)
    write_normalized_json(layout.observed / _PARENT_LOCK_FILE, parent_lock)
    deadline_policy = parent_lock.get("deadline_policy")
    if not isinstance(deadline_policy, dict):
        raise InteractionProtocolError("source audit has no deadline policy")
    parent_ledger = load_deadline_ledger(
        source_layout.observed / LEDGER_FILENAME,
        required=False,
    )
    if parent_ledger is None and isinstance(parent_lock.get("deadline_ledger"), dict):
        parent_ledger = copy.deepcopy(parent_lock["deadline_ledger"])
    try:
        ledger = start_linked_segment(
            parent_ledger=parent_ledger,
            audit_run_id=run_id,
            parent_audit_run_id=source_status.audit_run_id,
            mode=str(deadline_policy["mode"]),
            scheduling_cutoff_seconds=float(deadline_policy["scheduling_cutoff_seconds"]),
            hard_seconds=float(deadline_policy["hard_seconds"]),
            started_at=timestamp,
        )
    except (KeyError, TypeError, ValueError, DeadlineLedgerError) as error:
        raise InteractionProtocolError("source deadline policy is invalid") from error
    write_deadline_ledger(layout.observed / LEDGER_FILENAME, ledger)
    session: dict[str, Any] = {
        "session_version": "1.0.0",
        "schema_version": SCHEMA_VERSION,
        "audit_run_id": run_id,
        "parent_audit_run_id": source_status.audit_run_id,
        "parent_semantic_lock_digest": source_status.semantic_lock_digest,
        "parent_bundle_digest": semantic_digest(parent_bundle),
        "source_snapshot_digest": source_snapshot_digest,
        "snapshot_id": snapshot.snapshot_record["snapshot_id"],
        "created_at": timestamp,
        "clock_mode": "injected" if created_at is not None else "wall",
        "deadline_ledger_ref": f"observed/{LEDGER_FILENAME}",
        "prompt_template": {
            "prompt_template_id": _PROMPT_TEMPLATE_ID,
            "normalized_text": _PROMPT_TEMPLATE,
            "prompt_template_digest": sha256_digest(_PROMPT_TEMPLATE),
        },
    }
    session["session_digest"] = semantic_digest(session)
    write_normalized_json(layout.observed / _SESSION_FILE, session)

    current = AuditState.CREATED
    for state in (AuditState.SNAPSHOTTED, AuditState.INVENTORIED, AuditState.PARSED):
        current = transition(current, state)
        _append_run_state(layout, registry, session, current)

    work_store = JsonlRecordStore(layout.derived)
    work_items = [
        _build_work_item(session, parent_bundle, question, timestamp) for question in questions
    ]
    for work_item in work_items:
        registry.validate(work_item)
        work_store.append(work_item)
    return {
        "audit_run_id": run_id,
        "parent_audit_run_id": source_status.audit_run_id,
        "state": current.value,
        "source_snapshot_digest": source_snapshot_digest,
        "work_item_ids": [item["work_item_id"] for item in work_items],
    }


def work_queue(session_root: Path, schema_root: Path) -> dict[str, Any]:
    """Return the latest validated version of every scheduled WorkItem."""

    context = _load_session(session_root, schema_root)
    latest = _latest_records(context["derived_store"], "work_item", "work_item_id")
    return {
        "protocol_version": "0.2.0",
        "audit_run_id": context["session"]["audit_run_id"],
        "state": context["state"].value,
        "work_items": [latest[key] for key in sorted(latest)],
    }


def work_packet(session_root: Path, work_item_id: str, schema_root: Path) -> dict[str, Any]:
    """Return one exact work packet with its normalized prompt template."""

    context = _load_session(session_root, schema_root)
    latest = _latest_records(context["derived_store"], "work_item", "work_item_id")
    try:
        item = latest[work_item_id]
    except KeyError as error:
        raise InteractionProtocolError(f"unknown WorkItem: {work_item_id}") from error
    return {
        "protocol_version": "0.2.0",
        "audit_run_id": context["session"]["audit_run_id"],
        "run_state": context["state"].value,
        "work_item": item,
        "prompt_template": context["session"]["prompt_template"],
    }


def submit_proposal(
    session_root: Path,
    work_item_id: str,
    proposal: dict[str, Any],
    schema_root: Path,
    *,
    submitted_at: str | None = None,
) -> dict[str, Any]:
    """Validate and append one model proposal before semantic lock."""

    context = _load_session(session_root, schema_root, require_unlocked=True)
    if context["state"] not in {AuditState.PARSED, AuditState.SEMANTICS_PROPOSED}:
        raise InteractionProtocolError(
            f"proposal submission is unavailable in state {context['state'].value}"
        )
    latest = _latest_records(context["derived_store"], "work_item", "work_item_id")
    try:
        item = latest[work_item_id]
    except KeyError as error:
        raise InteractionProtocolError(f"unknown WorkItem: {work_item_id}") from error
    if item.get("status") not in {"ready", "in_progress"}:
        raise InteractionProtocolError("WorkItem is not accepting proposals")

    registry: LocalSchemaRegistry = context["registry"]
    registry.validate(proposal)
    _validate_proposal(context, item, proposal)
    existing = _latest_records(context["derived_store"], "semantic_assertion", "assertion_id")
    if proposal["assertion_id"] in existing:
        raise InteractionProtocolError("SemanticAssertion identity was already submitted")
    context["derived_store"].append(proposal)

    timestamp = _interaction_timestamp(context, submitted_at)
    _checkpoint_interaction_deadline(context, timestamp, "model_proposal_submitted")
    submitted = copy.deepcopy(item)
    submitted["status"] = "submitted"
    submitted["started_at"] = timestamp
    submitted["output_refs"] = [typed_ref("semantic_assertion", str(proposal["assertion_id"]))]
    submitted["completion_reason"] = "Bounded proposal submitted for controller adjudication."
    submitted["provenance"] = controller_provenance("deterministic_proposal_submission", timestamp)
    registry.validate(submitted)
    context["derived_store"].append(submitted)
    if context["state"] == AuditState.PARSED:
        _append_run_state(
            context["layout"], registry, context["session"], AuditState.SEMANTICS_PROPOSED
        )
    context["deadline_ledger"] = pause_for_scientist(context["deadline_ledger"], at=timestamp)
    _write_context_deadline(context)
    return proposal


def create_candidate_answer(
    session_root: Path,
    question_id: str,
    selected_option_id: str,
    actor_id: str,
    schema_root: Path,
    *,
    answered_at: str | None = None,
) -> dict[str, Any]:
    """Construct a public candidate-selection Answer from a bounded open question."""

    context = _load_session(session_root, schema_root, require_unlocked=True)
    question = _question(context["parent_bundle"], question_id)
    option = next(
        (
            candidate
            for candidate in question.get("candidate_answers", [])
            if candidate.get("answer_id") == selected_option_id
        ),
        None,
    )
    if option is None:
        raise InteractionProtocolError("selected option does not belong to the MaterialQuestion")
    normalized_actor = actor_id.strip()
    if not normalized_actor:
        raise InteractionProtocolError("actor_id must identify the answering scientist")
    timestamp = _interaction_timestamp(context, answered_at)
    subject_refs, authority_kind = _answer_authority(context["parent_bundle"], question)
    retain_unknown = option.get("value") == {"action": "retain_unknown"}
    answer: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "answer",
        "answer_id": stable_id(
            "answer",
            str(context["session"]["audit_run_id"]),
            question_id,
            selected_option_id,
            normalized_actor,
        ),
        "audit_run_id": context["session"]["audit_run_id"],
        "question_ref": typed_ref("material_question", question_id),
        "source_snapshot_digest": context["session"]["source_snapshot_digest"],
        "answer_kind": "unknown" if retain_unknown else "candidate_selection",
        "answer_value": copy.deepcopy(option["value"]),
        "selected_option_id": selected_option_id,
        "respondent": {"actor_kind": "human", "actor_id": normalized_actor},
        "response_source": "interactive_scientist",
        "authority_scope": {
            "authority_kind": authority_kind,
            "subject_refs": subject_refs,
            "semantic_dimensions": [str(question["unknown_semantic_dimension"])],
        },
        "certainty": {
            "level": "unknown" if retain_unknown else "explicit",
            "basis": (
                "The human respondent explicitly retained this bounded premise as unknown."
                if retain_unknown
                else "The human respondent explicitly selected this bounded answer option."
            ),
        },
        "timestamp_status": "available",
        "answered_at": timestamp,
        "supersedes_answer_refs": [],
        "answer_digest_profile": _ANSWER_PROFILE,
        "created_at": timestamp,
        "provenance": {
            "actor": {"actor_kind": "human", "actor_id": normalized_actor},
            "method": "scientist_answer",
            "created_at": timestamp,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }
    answer["answer_digest"] = semantic_digest(answer)
    context["registry"].validate(answer)
    return answer


def create_structured_answer(
    session_root: Path,
    question_id: str,
    values: dict[str, Any],
    actor_id: str,
    schema_root: Path,
    *,
    answered_at: str | None = None,
) -> dict[str, Any]:
    """Construct a public structured scientist Answer for named contract dimensions."""

    context = _load_session(session_root, schema_root, require_unlocked=True)
    question = _question(context["parent_bundle"], question_id)
    if question.get("unknown_semantic_dimension") != "scientific_contract":
        raise InteractionProtocolError("structured answers are limited to contract questions")
    work_item = _submitted_work_item(context, question_id)
    allowed_dimensions = set(work_item["packet"]["unresolved_dimensions"])
    if not values:
        raise InteractionProtocolError("structured Answer must declare at least one dimension")
    if any(not isinstance(key, str) or key not in allowed_dimensions for key in values):
        raise InteractionProtocolError(
            "structured Answer contains a dimension outside the bounded WorkItem"
        )
    if any(value is None for value in values.values()):
        raise InteractionProtocolError(
            "structured Answer values cannot be null; omit unresolved dimensions"
        )
    _validate_closed_method_answer(question, values)
    normalized_actor = actor_id.strip()
    if not normalized_actor:
        raise InteractionProtocolError("actor_id must identify the answering scientist")
    timestamp = _interaction_timestamp(context, answered_at)
    subject_refs, authority_kind = _answer_authority(context["parent_bundle"], question)
    dimensions = sorted(values)
    answer: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "answer",
        "answer_id": stable_id(
            "answer-structured",
            str(context["session"]["audit_run_id"]),
            question_id,
            semantic_digest(values),
            normalized_actor,
        ),
        "audit_run_id": context["session"]["audit_run_id"],
        "question_ref": typed_ref("material_question", question_id),
        "source_snapshot_digest": context["session"]["source_snapshot_digest"],
        "answer_kind": "structured_value",
        "answer_value": copy.deepcopy(values),
        "respondent": {"actor_kind": "human", "actor_id": normalized_actor},
        "response_source": "provided_answer_file",
        "authority_scope": {
            "authority_kind": authority_kind,
            "subject_refs": subject_refs,
            "semantic_dimensions": dimensions,
        },
        "certainty": {
            "level": "explicit",
            "basis": "The human respondent explicitly supplied these structured intended values.",
        },
        "timestamp_status": "available",
        "answered_at": timestamp,
        "supersedes_answer_refs": [],
        "answer_digest_profile": _ANSWER_PROFILE,
        "created_at": timestamp,
        "provenance": {
            "actor": {"actor_kind": "human", "actor_id": normalized_actor},
            "method": "scientist_answer",
            "created_at": timestamp,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
    }
    answer["answer_digest"] = semantic_digest(answer)
    context["registry"].validate(answer)
    return answer


def record_answer(
    session_root: Path,
    answer: dict[str, Any],
    schema_root: Path,
) -> dict[str, Any]:
    """Validate and append a scientist Answer, preserving proposal conflicts."""

    context = _load_session(session_root, schema_root, require_unlocked=True)
    if context["state"] not in {AuditState.SEMANTICS_PROPOSED, AuditState.AWAITING_ANSWERS}:
        raise InteractionProtocolError("a bounded proposal must be submitted before an Answer")
    context["registry"].validate(answer)
    _validate_answer(context, answer)
    existing = _latest_records(context["derived_store"], "answer", "answer_id")
    if answer["answer_id"] in existing:
        raise InteractionProtocolError("Answer identity was already recorded")

    context["deadline_ledger"] = resume_after_scientist(
        context["deadline_ledger"], at=str(answer["created_at"])
    )
    _write_context_deadline(context)

    if context["state"] == AuditState.SEMANTICS_PROPOSED:
        _append_run_state(
            context["layout"],
            context["registry"],
            context["session"],
            AuditState.AWAITING_ANSWERS,
        )
    context["derived_store"].append(answer)
    question_id = str(answer["question_ref"]["record_id"])
    for item in _latest_records(context["derived_store"], "work_item", "work_item_id").values():
        question_ids = {ref.get("record_id") for ref in item.get("material_question_refs", [])}
        if question_id not in question_ids or item.get("status") != "submitted":
            continue
        completed = copy.deepcopy(item)
        completed["status"] = "completed"
        completed["completed_at"] = str(answer["created_at"])
        completed["completion_reason"] = (
            "A scope-bound scientist Answer resolved the scheduled interaction."
        )
        completed["output_refs"] = [
            *item.get("output_refs", []),
            typed_ref("answer", str(answer["answer_id"])),
        ]
        completed["provenance"] = controller_provenance(
            "deterministic_work_completion", str(answer["created_at"])
        )
        context["registry"].validate(completed)
        context["derived_store"].append(completed)
    _append_run_state(
        context["layout"],
        context["registry"],
        context["session"],
        AuditState.SEMANTICS_RESOLVED,
    )
    return answer


def lock_semantics(
    session_root: Path, schema_root: Path, *, locked_at: str | None = None
) -> dict[str, Any]:
    """Create the semantic lock and complete controller-owned model-free stages."""

    context = _load_session(session_root, schema_root, require_unlocked=True)
    if context["state"] != AuditState.SEMANTICS_RESOLVED:
        raise InteractionProtocolError(
            f"semantic lock requires semantics_resolved, not {context['state'].value}"
        )
    answers = list(_latest_records(context["derived_store"], "answer", "answer_id").values())
    if not answers:
        raise InteractionProtocolError("semantic lock requires at least one validated Answer")
    work_items = list(context["derived_store"].iter_records("work_item"))
    proposals = list(context["derived_store"].iter_records("semantic_assertion"))
    parent_lock = context["parent_lock"]
    prior_assertions = copy.deepcopy(parent_lock.get("semantic_assertions", []))
    timestamp = _interaction_timestamp(context, locked_at)
    _checkpoint_interaction_deadline(context, timestamp, "semantic_lock_reached")
    answer = answers[-1]
    question = _question(context["parent_bundle"], str(answer["question_ref"]["record_id"]))

    run_id = str(context["session"]["audit_run_id"])
    artifacts = copy.deepcopy(parent_lock.get("artifacts", []))
    answered_question = _answered_question(question, answer, run_id, timestamp)
    scientist_assertions: list[dict[str, Any]] = []
    extracted_assertions: list[dict[str, Any]] = []
    if question.get("unknown_semantic_dimension") == "publication_surface":
        selected_path = _selected_artifact_path(artifacts, answer)
        if selected_path is None:
            surface = copy.deepcopy(_source_surface(context["parent_bundle"], question))
            surface["audit_run_id"] = run_id
            surface["created_at"] = timestamp
        else:
            surface, _ = _resolve_publication_surface(
                run_id,
                timestamp,
                artifacts,
                explicit_report=selected_path,
                scientist_answer_id=str(answer["answer_id"]),
            )
            source_surface = _source_surface(context["parent_bundle"], question)
            surface["publication_surface_id"] = source_surface["publication_surface_id"]
        claims, contracts, extracted_assertions = _extract_resolved_literal_claims(
            run_id,
            timestamp,
            copy.deepcopy(parent_lock.get("parser_results", [])),
            artifacts,
            surface,
        )
    elif question.get("unknown_semantic_dimension") == "scientific_contract":
        surfaces = copy.deepcopy(parent_lock.get("publication_surfaces", []))
        if len(surfaces) != 1 or surfaces[0].get("status") != "resolved":
            raise InteractionProtocolError(
                "contract resolution requires one resolved publication surface"
            )
        surface = surfaces[0]
        surface["audit_run_id"] = run_id
        claims = copy.deepcopy(parent_lock.get("claims", []))
        contracts = copy.deepcopy(parent_lock.get("scientific_contracts", []))
        for claim in claims:
            claim["audit_run_id"] = run_id
        for contract in contracts:
            contract["audit_run_id"] = run_id
        if answer.get("answer_kind") != "unknown":
            scientist_assertions = _apply_structured_contract_answer(
                answer,
                question,
                claims,
                contracts,
                run_id,
                timestamp,
                str(context["session"]["source_snapshot_digest"]),
                publication_surfaces=surfaces,
            )
    elif question.get("unknown_semantic_dimension") == "multiplicity_contract":
        surfaces = copy.deepcopy(parent_lock.get("publication_surfaces", []))
        if len(surfaces) != 1 or surfaces[0].get("status") != "resolved":
            raise InteractionProtocolError(
                "multiplicity resolution requires one resolved publication surface"
            )
        surface = surfaces[0]
        surface["audit_run_id"] = run_id
        claims = copy.deepcopy(parent_lock.get("claims", []))
        contracts = copy.deepcopy(parent_lock.get("scientific_contracts", []))
        for claim in claims:
            claim["audit_run_id"] = run_id
        for contract in contracts:
            contract["audit_run_id"] = run_id
        if answer.get("answer_kind") not in {"structured_value", "unknown"}:
            raise InteractionProtocolError(
                "multiplicity resolution requires a structured or unknown Answer"
            )
    else:
        raise InteractionProtocolError("unsupported semantic question at lock boundary")
    observed_results = copy.deepcopy(parent_lock.get("observed_results", []))
    deterministic_check_observations = copy.deepcopy(
        parent_lock.get("deterministic_check_observations", [])
    )
    operations = copy.deepcopy(parent_lock.get("operations", []))
    data_assets = copy.deepcopy(parent_lock.get("data_assets", []))
    variables = copy.deepcopy(parent_lock.get("variables", []))
    analysis_decisions = copy.deepcopy(parent_lock.get("analysis_decisions", []))
    selection_envelopes = copy.deepcopy(parent_lock.get("selection_envelopes", []))
    executions = copy.deepcopy(parent_lock.get("executions", []))
    project_execution_authorizations = copy.deepcopy(
        parent_lock.get("project_execution_authorizations", [])
    )
    environments = copy.deepcopy(parent_lock.get("environments", []))
    claims = bind_bounded_claim_lineage(
        claims,
        observed_results,
        operations,
        data_assets,
        executions,
        artifacts,
    )
    reproduction_requests = build_reproduction_requests(
        claims,
        environments,
        str(context["session"]["source_snapshot_digest"]),
        run_id,
        timestamp,
    )
    questions = [
        answered_question,
        *_build_contract_questions(
            run_id,
            timestamp,
            claims,
            contracts,
            [*prior_assertions, *extracted_assertions, *scientist_assertions],
        ),
    ]
    snapshot_record = _read_object(context["layout"].observed / "snapshot.json")
    snapshot = _snapshot_projection(context, snapshot_record)
    file_records = list(context["observed_store"].iter_records("file_record"))
    unsupported = _unsupported_source_paths(file_records)
    disclosures = _general_disclosures(
        run_id,
        timestamp,
        artifacts,
        file_records,
        operations,
        unsupported,
        [],
    )
    coverage_inputs = _general_coverage_inputs(
        snapshot,
        file_records,
        copy.deepcopy(parent_lock.get("parser_results", [])),
        artifacts,
        surface,
        operations,
        data_assets,
        selection_envelopes,
        unsupported,
        [],
    )
    if contracts and all(contract.get("status") == "resolved" for contract in contracts):
        coverage_inputs["known_gaps"] = [
            gap
            for gap in coverage_inputs["known_gaps"]
            if gap != "No final claim was bound to a complete ScientificContract."
        ]
        coverage_inputs["known_gaps"].append(
            "ScientificContracts reflect scope-bound scientist intent and do not complete observed computational lineage; any partial links retain their missing edges."
        )
    source_asset_identities = [
        item
        for item in parent_lock.get("asset_identities", [])
        if item.get("asset_ref", {}).get("record_type") != "file_record"
    ]
    snapshot_asset_identities = list(context["observed_store"].iter_records("asset_identity"))
    submitted_model_calls = [
        {
            "work_item_id": item["work_item_id"],
            "packet_digest": item["packet"]["packet_digest"],
            "prompt_template_digest": item["packet"]["prompt_template_digest"],
        }
        for item in work_items
        if item.get("status") == "submitted"
    ]
    deadline_segment = current_segment(context["deadline_ledger"])
    performance_record = build_semantic_lock_performance_record(
        audit_run_id=run_id,
        recorded_at=timestamp,
        user_visible_elapsed_seconds=float(deadline_segment["user_visible_elapsed_seconds"]),
        paused_for_scientist_seconds=float(deadline_segment["paused_for_scientist_seconds"]),
        snapshot_record=snapshot_record,
        cache_summary=copy.deepcopy(parent_lock.get("cache_summary", {})),
        deadline_ledger_digest=str(context["deadline_ledger"]["ledger_digest"]),
    )
    context["registry"].validate(performance_record)
    locked: dict[str, Any] = {
        "lock_kind": "general_static_v1",
        "lock_version": "0.2.0",
        "audit_run_id": context["session"]["audit_run_id"],
        "parent_audit_run_id": context["session"]["parent_audit_run_id"],
        "locked_at": timestamp,
        "snapshot_digest": context["session"]["source_snapshot_digest"],
        "model_calls": submitted_model_calls,
        "model_access_after_lock": False,
        "deadline_policy": copy.deepcopy(parent_lock.get("deadline_policy")),
        "deadline_ledger": copy.deepcopy(context["deadline_ledger"]),
        "agent_inputs": copy.deepcopy(answers),
        "repository_snapshot": snapshot_record,
        "file_records": file_records,
        "asset_identities": [*snapshot_asset_identities, *source_asset_identities],
        "parser_results": copy.deepcopy(parent_lock.get("parser_results", [])),
        "operations": operations,
        "artifacts": artifacts,
        "observed_results": observed_results,
        "deterministic_check_observations": deterministic_check_observations,
        "data_assets": data_assets,
        "variables": variables,
        "analysis_decisions": analysis_decisions,
        "selection_envelopes": selection_envelopes,
        "executions": executions,
        "project_execution_authorizations": project_execution_authorizations,
        "environments": environments,
        "scientific_contracts": contracts,
        "semantic_assertions": [
            *prior_assertions,
            *proposals,
            *extracted_assertions,
            *scientist_assertions,
        ],
        "claims": claims,
        "detector_manifests": copy.deepcopy(parent_lock.get("detector_manifests", [])),
        "publication_surfaces": [surface],
        "material_questions": questions,
        "answers": answers,
        "work_items": work_items,
        "disclosures": disclosures,
        "cache_entries": copy.deepcopy(parent_lock.get("cache_entries", [])),
        "cache_policies": copy.deepcopy(parent_lock.get("cache_policies", [])),
        "cache_summary": copy.deepcopy(parent_lock.get("cache_summary", {})),
        "reproduction_requests": reproduction_requests,
        "performance_records": [performance_record],
        "coverage_inputs": coverage_inputs,
        "scientific_check_registry": copy.deepcopy(
            parent_lock.get("scientific_check_registry", {})
        ),
        "calculation_check_registry": copy.deepcopy(
            parent_lock.get("calculation_check_registry", {})
        ),
    }
    locked["semantic_lock_digest"] = semantic_digest(locked)
    write_normalized_json(context["layout"].lock_path, locked)
    _append_run_state(
        context["layout"],
        context["registry"],
        context["session"],
        AuditState.SEMANTICS_LOCKED,
    )
    _append_run_state(
        context["layout"], context["registry"], context["session"], AuditState.DETECTED
    )
    bundle = _derive_general_from_lock(locked, session_root, schema_root, finalize=False)
    _append_run_state(
        context["layout"], context["registry"], context["session"], AuditState.REPORTED
    )
    completion_timestamp = timestamp if locked_at is not None else _timestamp_now()
    final_ledger, exhausted = advance_or_exhaust(
        context["deadline_ledger"],
        at=completion_timestamp,
        event="postlock_stages_completed",
    )
    context["deadline_ledger"] = final_ledger
    if not exhausted:
        context["deadline_ledger"] = complete_segment(
            context["deadline_ledger"],
            at=completion_timestamp,
        )
    _write_context_deadline(context)
    if exhausted:
        disposition = _GeneralCoverageDisposition(
            overall_status="partial_budget_exhausted",
            run_state="partial_deadline",
            termination_reason="hard_deadline",
            pending_work=("Complete the interrupted integrity stage.",),
        )
        coverage = _general_coverage_record(
            locked,
            bundle,
            coverage_disposition=disposition,
        )
        context["registry"].validate(coverage)
        context["derived_store"].append(coverage)
        bundle["coverage_records"] = [coverage]
        _append_run_state(
            context["layout"],
            context["registry"],
            context["session"],
            AuditState.PARTIAL_DEADLINE,
            terminal_reason="User-visible hard deadline reached after semantic lock.",
        )
    else:
        _append_run_state(
            context["layout"], context["registry"], context["session"], AuditState.COMPLETE
        )
    return _finalize_bundle(
        bundle,
        locked,
        context["layout"],
        context["registry"],
        context["derived_store"],
    )


def _answered_question(
    question: dict[str, Any],
    answer: dict[str, Any],
    run_id: str,
    created_at: str,
) -> dict[str, Any]:
    updated = copy.deepcopy(question)
    updated["audit_run_id"] = run_id
    updated["status"] = "deferred" if answer.get("answer_kind") == "unknown" else "answered"
    updated["answer_ids"] = [str(answer["answer_id"])]
    updated["created_at"] = created_at
    return updated


def _apply_structured_contract_answer(
    answer: dict[str, Any],
    question: dict[str, Any],
    claims: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
    run_id: str,
    created_at: str,
    source_snapshot_digest: str,
    publication_surfaces: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if answer.get("answer_kind") != "structured_value" or not isinstance(
        answer.get("answer_value"), dict
    ):
        raise InteractionProtocolError(
            "scientific-contract resolution requires a structured Answer"
        )
    contract_id = question.get("extensions", {}).get("x-contract-ref", {}).get("record_id")
    contract = next((item for item in contracts if item.get("contract_id") == contract_id), None)
    if contract is None:
        raise InteractionProtocolError("structured Answer contract is unavailable")
    scope = contract.get("scope")
    if not isinstance(scope, dict) or len(scope.get("subject_refs", [])) != 1:
        raise InteractionProtocolError("structured Answer contract scope is unavailable")
    subject_ref = copy.deepcopy(scope["subject_refs"][0])
    claim: dict[str, Any] | None = None
    if scope.get("level") == "claim":
        claim_ids = set(question.get("affected_claim_ids", []))
        claim = next((item for item in claims if item.get("claim_id") in claim_ids), None)
        if (
            claim is None
            or subject_ref != typed_ref("claim", str(claim.get("claim_id")))
            or question.get("affected_claim_ids") != [str(claim.get("claim_id"))]
        ):
            raise InteractionProtocolError("structured Answer Claim subject is unavailable")
    elif scope.get("level") == "analysis":
        surfaces = publication_surfaces or []
        if (
            question.get("affected_claim_ids") != []
            or subject_ref.get("record_type") != "publication_surface"
            or question.get("extensions", {}).get("x-analysis-subject-ref") != subject_ref
            or len(
                [
                    item
                    for item in surfaces
                    if item.get("publication_surface_id") == subject_ref.get("record_id")
                    and item.get("status") == "resolved"
                ]
            )
            != 1
        ):
            raise InteractionProtocolError("structured Answer analysis subject is unavailable")
    else:
        raise InteractionProtocolError("structured Answer contract scope is unsupported")
    source_refs = copy.deepcopy(contract.get("source_refs", []))
    if not source_refs:
        raise InteractionProtocolError("structured Answer has no exact contract source")
    actor = copy.deepcopy(answer["respondent"])
    assertions: list[dict[str, Any]] = []
    for dimension, value in sorted(answer["answer_value"].items()):
        assertion_id = stable_id(
            "assertion-scientist-intent", run_id, str(answer["answer_id"]), dimension
        )
        assertion = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "semantic_assertion",
            "assertion_id": assertion_id,
            "audit_run_id": run_id,
            "subject_ref": copy.deepcopy(subject_ref),
            "predicate": f"intended_{dimension}",
            "object": copy.deepcopy(value),
            "semantic_role": "intended",
            "assertion_class": "scientist_declaration",
            "epistemic_status": "accepted",
            "authority_scope": "scientific_intent",
            "independently_checkable": False,
            "finding_eligibility": "ineligible",
            "verification": {
                "status": "verified",
                "method": "scientist_confirmation",
                "validator_id": "controller:answer-authority-scope",
                "verified_at": created_at,
            },
            "certainty": copy.deepcopy(answer["certainty"]),
            "rationale": (
                "The human respondent declared this intended value within the exact Answer "
                "authority scope; it does not establish executed computation."
            ),
            "source_refs": source_refs,
            "provenance": {
                "actor": actor,
                "method": "scientist_answer",
                "created_at": created_at,
                "source_refs": source_refs,
                "tool": "sc-referee",
                "tool_version": __version__,
            },
            "extensions": {
                "x-answer-ref": typed_ref("answer", str(answer["answer_id"])),
                "x-authority-limitation": (
                    "Scientist intent only; observed execution and reported wording are unchanged."
                ),
            },
        }
        contract["dimensions"][dimension] = {
            "state": "known",
            "assertion_ids": [assertion_id],
            "accepted_assertion_ids": [assertion_id],
            "notes": "Resolved only as scientist-declared intent.",
        }
        assertions.append(assertion)
    derived_assertions = [
        *_derive_verified_posthoc_intent_assertions(
            answer=answer,
            question=question,
            claim=claim,
            contract=contract,
            scientist_assertions=assertions,
            run_id=run_id,
            created_at=created_at,
            source_snapshot_digest=source_snapshot_digest,
        ),
        *(
            _derive_verified_expected_count_intent_assertions(
                answer=answer,
                question=question,
                claim=claim,
                contract=contract,
                scientist_assertions=assertions,
                run_id=run_id,
                created_at=created_at,
                source_snapshot_digest=source_snapshot_digest,
            )
            if claim is not None
            else []
        ),
    ]
    for derived in derived_assertions:
        dimension = str(derived["predicate"]).removeprefix("verified_intended_")
        slot = contract["dimensions"][dimension]
        slot["assertion_ids"].append(derived["assertion_id"])
        slot["accepted_assertion_ids"].append(derived["assertion_id"])
        slot["notes"] = (
            "Resolved as scientist-declared intent with a separate closed-profile controller "
            "derivation; neither assertion establishes scientific truth or execution."
        )
    assertions.extend(derived_assertions)
    contract["updated_at"] = created_at
    contract["status"] = (
        "resolved"
        if all(
            contract["dimensions"][dimension].get("state") in {"known", "not_applicable"}
            for dimension in contract["dimensions"]
        )
        else "draft"
    )
    if claim is not None:
        claim.setdefault("extensions", {})["x-scientific-semantics-unresolved"] = (
            contract["status"] != "resolved"
        )
        if derived_assertions:
            claim["extensions"]["x-expected-count-profile-resolved"] = True
        claim.setdefault("extraction", {})["semantic_assertion_ids"] = [
            *claim.get("extraction", {}).get("semantic_assertion_ids", []),
            *(assertion["assertion_id"] for assertion in assertions),
        ]
    return assertions


def _derive_verified_posthoc_intent_assertions(
    *,
    answer: dict[str, Any],
    question: dict[str, Any],
    claim: dict[str, Any] | None,
    contract: dict[str, Any],
    scientist_assertions: list[dict[str, Any]],
    run_id: str,
    created_at: str,
    source_snapshot_digest: str,
) -> list[dict[str, Any]]:
    extensions = question.get("extensions", {})
    forms = extensions.get("x-posthoc-comparison-forms", {})
    report_ids = extensions.get("x-posthoc-reported-assertion-ids", {})
    answer_value = answer.get("answer_value")
    if not isinstance(forms, dict) or not forms or not isinstance(report_ids, dict):
        return []
    if not isinstance(answer_value, dict):
        return []
    digest_input = copy.deepcopy(answer)
    answer_digest = digest_input.pop("answer_digest", None)
    respondent = answer.get("respondent")
    authority = answer.get("authority_scope")
    scope = contract.get("scope")
    scope_level = scope.get("level") if isinstance(scope, dict) else None
    scope_subjects = scope.get("subject_refs") if isinstance(scope, dict) else None
    if not isinstance(scope_subjects, list) or len(scope_subjects) != 1:
        return []
    subject_ref = scope_subjects[0]
    claim_id = str(claim.get("claim_id")) if claim is not None else ""
    common_valid = (
        semantic_digest(digest_input) != answer_digest
        or not isinstance(answer_digest, str)
        or answer.get("audit_run_id") != run_id
        or answer.get("source_snapshot_digest") != source_snapshot_digest
        or not isinstance(respondent, dict)
        or respondent.get("actor_kind") != "human"
        or answer.get("response_source") not in {"interactive_scientist", "provided_answer_file"}
        or not isinstance(authority, dict)
        or authority.get("authority_kind") != "scientific_intent"
        or authority.get("subject_refs") != [subject_ref]
        or authority.get("semantic_dimensions") != sorted(answer_value)
        or answer.get("question_ref")
        != typed_ref("material_question", str(question.get("question_id")))
    )
    claim_scope_valid = (
        scope_level == "claim"
        and claim is not None
        and subject_ref == typed_ref("claim", claim_id)
        and question.get("affected_claim_ids") == [claim_id]
        and claim.get("scientific_contract_id") == contract.get("contract_id")
    )
    analysis_scope_valid = (
        scope_level == "analysis"
        and claim is None
        and isinstance(subject_ref, dict)
        and subject_ref.get("record_type") == "publication_surface"
        and question.get("affected_claim_ids") == []
        and question.get("extensions", {}).get("x-analysis-subject-ref") == subject_ref
        and _valid_analysis_contract_question(question)
    )
    if common_valid or not (claim_scope_valid or analysis_scope_valid):
        return []
    by_predicate = {str(item.get("predicate")): item for item in scientist_assertions}
    source_refs = copy.deepcopy(contract.get("source_refs", []))
    if not source_refs:
        return []
    derived: list[dict[str, Any]] = []
    for dimension, value in sorted(answer_value.items()):
        comparison_form = forms.get(dimension)
        reported_ids = report_ids.get(dimension)
        if not isinstance(comparison_form, str):
            continue
        if (
            not isinstance(reported_ids, list)
            or not reported_ids
            or len(reported_ids) != len(set(map(str, reported_ids)))
            or (claim_scope_valid and len(reported_ids) != 1)
        ):
            continue
        try:
            normalized = validate_posthoc_requirement(dimension, comparison_form, value)
        except PosthocMethodLedgerError:
            continue
        if normalized != value:
            continue
        declaration = by_predicate.get(f"intended_{dimension}")
        if (
            declaration is None
            or declaration.get("object") != value
            or declaration.get("assertion_class") != "scientist_declaration"
            or declaration.get("finding_eligibility") != "ineligible"
            or declaration.get("provenance", {}).get("actor", {}).get("actor_kind") != "human"
            or declaration.get("extensions", {}).get("x-answer-ref")
            != typed_ref("answer", str(answer.get("answer_id")))
        ):
            continue
        assertion_id = stable_id(
            "assertion-verified-posthoc-intent",
            run_id,
            str(answer_digest),
            dimension,
            comparison_form,
            canonical_json(value),
        )
        derived.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "semantic_assertion",
                "assertion_id": assertion_id,
                "audit_run_id": run_id,
                "subject_ref": copy.deepcopy(subject_ref),
                "predicate": f"verified_intended_{dimension}",
                "object": copy.deepcopy(value),
                "semantic_role": "intended",
                "assertion_class": "deterministic_derivation",
                "epistemic_status": "accepted",
                "authority_scope": "scientific_intent",
                "independently_checkable": True,
                "finding_eligibility": ("eligible" if claim_scope_valid else "ineligible"),
                "verification": {
                    "status": "verified",
                    "method": "deterministic_comparison",
                    "validator_id": "controller:posthoc-method-answer-v1",
                    "verified_at": created_at,
                },
                "certainty": copy.deepcopy(answer["certainty"]),
                "rationale": (
                    "The controller verified the human Answer digest, exact review scope, closed "
                    "comparison form, and canonical operand. This establishes only the "
                    "requirement governing this review, not historical intent, execution, or "
                    "scientific correctness."
                ),
                "source_refs": copy.deepcopy(source_refs),
                "provenance": controller_provenance(
                    "deterministic_posthoc_method_answer_derivation_v1", created_at
                ),
                "extensions": {
                    "x-answer-ref": typed_ref("answer", str(answer["answer_id"])),
                    "x-answer-digest": answer_digest,
                    "x-posthoc-comparison-form": comparison_form,
                    "x-reported-assertion-ref": typed_ref(
                        "semantic_assertion", str(reported_ids[0])
                    ),
                    "x-observed-assertion-refs": [
                        typed_ref("semantic_assertion", str(assertion_id))
                        for assertion_id in reported_ids
                    ],
                    "x-original-declaration-ref": typed_ref(
                        "semantic_assertion", str(declaration["assertion_id"])
                    ),
                    "x-authority-limitation": (
                        "Requirement for this review only; no historical intent, execution, or "
                        "general scientific correctness is established."
                    ),
                    **(
                        {
                            "x-scientific-check-id": extensions["x-scientific-check-id"],
                            "x-scientific-check-manifest-digest": extensions[
                                "x-scientific-check-manifest-digest"
                            ],
                            "x-scientific-check-scope-join-digest": extensions[
                                "x-scientific-check-scope-join-digest"
                            ],
                        }
                        if analysis_scope_valid
                        else {}
                    ),
                },
            }
        )
    return derived


def _valid_analysis_check_question(question: dict[str, Any]) -> bool:
    extensions = question.get("extensions")
    if not isinstance(extensions, dict):
        return False
    scope_join = extensions.get("x-scientific-check-scope-join-path")
    scope_digest = extensions.get("x-scientific-check-scope-join-digest")
    observed = extensions.get("x-posthoc-reported-assertion-ids")
    adapter_bindings = extensions.get("x-scientific-check-adapter-bindings")
    return (
        isinstance(extensions.get("x-scientific-check-id"), str)
        and bool(extensions.get("x-scientific-check-id"))
        and isinstance(extensions.get("x-scientific-check-manifest-digest"), str)
        and isinstance(scope_join, list)
        and bool(scope_join)
        and semantic_digest(scope_join) == scope_digest
        and isinstance(observed, dict)
        and bool(observed)
        and isinstance(adapter_bindings, list)
        and bool(adapter_bindings)
    )


def _valid_analysis_contract_question(question: dict[str, Any]) -> bool:
    return _valid_analysis_check_question(
        question
    ) or valid_analysis_expected_count_obligation_question(question)


def _derive_verified_expected_count_intent_assertions(
    *,
    answer: dict[str, Any],
    question: dict[str, Any],
    claim: dict[str, Any],
    contract: dict[str, Any],
    scientist_assertions: list[dict[str, Any]],
    run_id: str,
    created_at: str,
    source_snapshot_digest: str,
) -> list[dict[str, Any]]:
    extensions = question.get("extensions", {})
    if extensions.get("x-method-profile-id") != EXPECTED_COUNT_PROFILE_ID:
        return []
    answer_value = answer.get("answer_value")
    if not isinstance(answer_value, dict):
        return []
    try:
        profile = expected_count_profile_from_dimensions(answer_value)
    except MethodContractError:
        return []
    digest_input = copy.deepcopy(answer)
    answer_digest = digest_input.pop("answer_digest", None)
    respondent = answer.get("respondent")
    authority = answer.get("authority_scope")
    scope = contract.get("scope")
    claim_id = str(claim.get("claim_id"))
    if (
        semantic_digest(digest_input) != answer_digest
        or not isinstance(answer_digest, str)
        or answer.get("audit_run_id") != run_id
        or answer.get("source_snapshot_digest") != source_snapshot_digest
        or not isinstance(respondent, dict)
        or respondent.get("actor_kind") != "human"
        or answer.get("response_source") not in {"interactive_scientist", "provided_answer_file"}
        or not isinstance(authority, dict)
        or authority.get("authority_kind") != "scientific_intent"
        or authority.get("subject_refs") != [typed_ref("claim", claim_id)]
        or authority.get("semantic_dimensions") != sorted(EXPECTED_COUNT_REQUIRED_DIMENSIONS)
        or answer.get("question_ref")
        != typed_ref("material_question", str(question.get("question_id")))
        or question.get("affected_claim_ids") != [claim_id]
        or not isinstance(scope, dict)
        or scope.get("level") != "claim"
        or scope.get("subject_refs") != [typed_ref("claim", claim_id)]
        or claim.get("scientific_contract_id") != contract.get("contract_id")
        or len(extensions.get("x-reported-method-assertion-ids", [])) != 1
    ):
        return []
    by_predicate = {str(item.get("predicate")): item for item in scientist_assertions}
    for dimension in EXPECTED_COUNT_REQUIRED_DIMENSIONS:
        declaration = by_predicate.get(f"intended_{dimension}")
        if (
            declaration is None
            or declaration.get("object") != answer_value[dimension]
            or declaration.get("assertion_class") != "scientist_declaration"
            or declaration.get("finding_eligibility") != "ineligible"
            or declaration.get("provenance", {}).get("actor", {}).get("actor_kind") != "human"
            or declaration.get("extensions", {}).get("x-answer-ref")
            != typed_ref("answer", str(answer.get("answer_id")))
        ):
            return []
    source_refs = copy.deepcopy(contract.get("source_refs", []))
    if not source_refs:
        return []
    values = expected_count_dimension_values(profile)
    derived: list[dict[str, Any]] = []
    for dimension in EXPECTED_COUNT_REQUIRED_DIMENSIONS:
        value = values[dimension]
        assertion_id = stable_id(
            "assertion-verified-scientist-intent",
            run_id,
            str(answer_digest),
            EXPECTED_COUNT_PROFILE_ID,
            EXPECTED_COUNT_PROFILE_VERSION,
            dimension,
            canonical_json(value),
        )
        derived.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "semantic_assertion",
                "assertion_id": assertion_id,
                "audit_run_id": run_id,
                "subject_ref": typed_ref("claim", claim_id),
                "predicate": f"verified_intended_{dimension}",
                "object": copy.deepcopy(value),
                "semantic_role": "intended",
                "assertion_class": "deterministic_derivation",
                "epistemic_status": "accepted",
                "authority_scope": "scientific_intent",
                "independently_checkable": True,
                "finding_eligibility": "eligible",
                "verification": {
                    "status": "verified",
                    "method": "deterministic_comparison",
                    "validator_id": "controller:expected-count-answer-profile-v1",
                    "verified_at": created_at,
                },
                "certainty": copy.deepcopy(answer["certainty"]),
                "rationale": (
                    "The controller verified that the human Answer, Claim scope, contract "
                    "dimensions, and closed expected-count profile agree exactly. This derives "
                    "governing intent only, not scientific truth or execution."
                ),
                "source_refs": copy.deepcopy(source_refs),
                "provenance": controller_provenance(
                    "deterministic_expected_count_answer_derivation_v1", created_at
                ),
                "extensions": {
                    "x-answer-ref": typed_ref("answer", str(answer["answer_id"])),
                    "x-answer-digest": answer_digest,
                    "x-profile-id": EXPECTED_COUNT_PROFILE_ID,
                    "x-profile-version": EXPECTED_COUNT_PROFILE_VERSION,
                    "x-original-declaration-ref": typed_ref(
                        "semantic_assertion",
                        str(by_predicate[f"intended_{dimension}"]["assertion_id"]),
                    ),
                    "x-authority-limitation": (
                        "Verified human intent for this Claim only; no execution or general "
                        "scientific correctness is established."
                    ),
                },
            }
        )
    return derived


def _build_work_item(
    session: dict[str, Any],
    parent_bundle: dict[str, Any],
    question: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    question_id = str(question["question_id"])
    dimension = str(question["unknown_semantic_dimension"])
    if dimension == "publication_surface":
        surface = _source_surface(parent_bundle, question)
        target_refs = [typed_ref("publication_surface", str(surface["publication_surface_id"]))]
        record_refs = [typed_ref("material_question", question_id), *target_refs]
        source_refs = _packet_source_refs(parent_bundle, surface)
        unresolved_dimensions = [dimension]
        materiality = "conclusion_material"
    elif dimension == "scientific_contract":
        contract = _question_contract(parent_bundle, question)
        scope = contract.get("scope", {})
        target_refs = copy.deepcopy(scope.get("subject_refs", []))
        if (
            len(target_refs) != 1
            or scope.get("level") not in {"claim", "analysis"}
            or (
                scope.get("level") == "claim"
                and target_refs
                != [
                    typed_ref("claim", str(claim_id))
                    for claim_id in question.get("affected_claim_ids", [])
                ]
            )
            or (
                scope.get("level") == "analysis"
                and (
                    question.get("affected_claim_ids") != []
                    or target_refs[0].get("record_type") != "publication_surface"
                    or question.get("extensions", {}).get("x-analysis-subject-ref")
                    != target_refs[0]
                    or not _valid_analysis_contract_question(question)
                )
            )
        ):
            raise InteractionProtocolError("contract question has no bounded review subject")
        record_refs = [
            typed_ref("material_question", question_id),
            typed_ref("scientific_contract", str(contract["contract_id"])),
            *target_refs,
        ]
        source_refs = copy.deepcopy(contract["source_refs"])
        unresolved_dimensions = list(
            question.get("extensions", {}).get("x-unresolved-dimensions", [])
        )
        if not unresolved_dimensions:
            raise InteractionProtocolError("contract question has no unresolved dimensions")
        materiality = "claim_material" if scope.get("level") == "claim" else "conclusion_material"
    else:
        raise InteractionProtocolError(f"unsupported material-question dimension: {dimension}")
    packet: dict[str, Any] = {
        "packet_kind": "semantic_or_auditor_work_v1",
        "packet_version": "1.0.0",
        "packet_digest_profile": _PACKET_PROFILE,
        "prompt_template_id": session["prompt_template"]["prompt_template_id"],
        "prompt_template_digest": session["prompt_template"]["prompt_template_digest"],
        "snapshot_digest": session["source_snapshot_digest"],
        "source_refs": source_refs,
        "record_refs": record_refs,
        "unresolved_dimensions": unresolved_dimensions,
        "required_output_record_types": ["semantic_assertion"],
        "limitations": [
            "Proposals may interpret only this exact question, candidate surface, and source set; unresolved alternatives remain explicit."
        ],
        "policy": {
            "open_ended_issue_discovery": False,
            "project_code_execution": False,
            "model_may_establish_material_premise": False,
            "accepted_status_allowed": False,
        },
    }
    packet["packet_digest"] = semantic_digest(packet)
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "work_item",
        "work_item_id": stable_id("work-item", str(session["audit_run_id"]), question_id),
        "audit_run_id": session["audit_run_id"],
        "kind": "semantic_resolution",
        "target_refs": target_refs,
        "dependency_work_item_refs": [],
        "status": "ready",
        "scheduling": {
            "estimated_elapsed_seconds": 45,
            "expected_information_gain": "high",
            "claim_materiality": materiality,
            "downstream_reach": len(question.get("blocked_detector_ids", [])),
            "component_maturity": "experimental",
            "cache_status": "not_cacheable",
            "execution_privilege": "safe_inspection",
        },
        "packet": packet,
        "material_question_refs": [typed_ref("material_question", question_id)],
        "output_refs": [],
        "created_at": created_at,
        "provenance": controller_provenance("deterministic_work_scheduling", created_at),
    }


def _validate_proposal(
    context: dict[str, Any], item: dict[str, Any], proposal: dict[str, Any]
) -> None:
    packet = item.get("packet")
    if not isinstance(packet, dict) or packet.get("packet_kind") != "semantic_or_auditor_work_v1":
        raise InteractionProtocolError("project-execution WorkItems are non-model controller work")
    if proposal.get("record_type") != "semantic_assertion":
        raise InteractionProtocolError("WorkItem accepts only SemanticAssertion proposals")
    if proposal.get("audit_run_id") != context["session"]["audit_run_id"]:
        raise InteractionProtocolError("proposal belongs to a different audit run")
    if proposal.get("epistemic_status") != "proposed":
        raise InteractionProtocolError("model proposals must remain proposed")
    if proposal.get("finding_eligibility") not in {"ineligible", "pending"}:
        raise InteractionProtocolError("model proposals cannot be Finding-eligible")
    if proposal.get("authority_scope") == "executed_computation":
        raise InteractionProtocolError("model proposals cannot establish observed computation")
    actor = proposal.get("provenance", {}).get("actor", {})
    if actor.get("actor_kind") != "model":
        raise InteractionProtocolError("proposal provenance must identify a model actor")
    extensions = proposal.get("extensions", {})
    expected_ref = typed_ref("work_item", str(item["work_item_id"]))
    if extensions.get("x-work-item-ref") != expected_ref:
        raise InteractionProtocolError("proposal WorkItem binding mismatch")
    if extensions.get("x-packet-digest") != item["packet"]["packet_digest"]:
        raise InteractionProtocolError("proposal packet digest mismatch")
    if extensions.get("x-prompt-template-digest") != item["packet"]["prompt_template_digest"]:
        raise InteractionProtocolError("proposal prompt-template digest mismatch")
    allowed_subjects = {
        canonical_json(ref) for ref in [*item["target_refs"], *item["packet"]["record_refs"]]
    }
    if canonical_json(proposal.get("subject_ref")) not in allowed_subjects:
        raise InteractionProtocolError("proposal subject is outside the bounded packet")
    allowed_sources = {canonical_json(ref) for ref in item["packet"]["source_refs"]}
    proposal_sources = proposal.get("source_refs", [])
    if not proposal_sources or any(
        canonical_json(source_ref) not in allowed_sources for source_ref in proposal_sources
    ):
        raise InteractionProtocolError("proposal source is outside the bounded packet")
    provenance_sources = proposal.get("provenance", {}).get("source_refs", [])
    if any(canonical_json(ref) not in allowed_sources for ref in provenance_sources):
        raise InteractionProtocolError("proposal provenance source is outside the bounded packet")
    for source_ref in proposal_sources:
        _verify_snapshot_source(context["layout"], source_ref)


def _validate_closed_method_answer(question: dict[str, Any], values: dict[str, Any]) -> None:
    extensions = question.get("extensions", {})
    posthoc_forms = extensions.get("x-posthoc-comparison-forms", {})
    if isinstance(posthoc_forms, dict):
        for dimension, value in values.items():
            comparison_form = posthoc_forms.get(dimension)
            if not isinstance(comparison_form, str):
                continue
            try:
                normalized = validate_posthoc_requirement(dimension, comparison_form, value)
            except PosthocMethodLedgerError as error:
                raise InteractionProtocolError(
                    f"post-hoc structured Answer is outside the closed profile: {error}"
                ) from error
            if normalized != value:
                raise InteractionProtocolError(
                    "post-hoc structured Answer must use the exact canonical value shown before recording"
                )
    if isinstance(extensions.get("x-scientific-check-id"), str):
        candidates = extensions.get("x-scientific-check-requirement-candidates")
        unresolved = extensions.get("x-unresolved-dimensions")
        if (
            not isinstance(candidates, list)
            or not candidates
            or not isinstance(unresolved, list)
            or len(unresolved) != 1
            or set(values) != {str(unresolved[0])}
        ):
            raise InteractionProtocolError(
                "analysis scientific-check Answer must select one listed dimension operand"
            )
        allowed_values = [
            candidate.get("operand", {}).get("value")
            for candidate in candidates
            if isinstance(candidate, dict) and isinstance(candidate.get("operand"), dict)
        ]
        selected_value = values[str(unresolved[0])]
        if not any(
            canonical_json(selected_value) == canonical_json(value) for value in allowed_values
        ):
            raise InteractionProtocolError(
                "analysis scientific-check Answer is not one exact listed requirement operand"
            )
    if extensions.get("x-method-profile-id") != EXPECTED_COUNT_PROFILE_ID:
        return
    if set(values) != set(EXPECTED_COUNT_REQUIRED_DIMENSIONS):
        raise InteractionProtocolError(
            "expected-count structured Answer must provide exactly the six closed profile dimensions"
        )
    try:
        expected_count_profile_from_dimensions(values)
    except MethodContractError as error:
        raise InteractionProtocolError(
            f"expected-count structured Answer is outside the closed profile: {error}"
        ) from error


def _validate_answer(context: dict[str, Any], answer: dict[str, Any]) -> None:
    digest_input = copy.deepcopy(answer)
    recorded_digest = digest_input.pop("answer_digest", None)
    if semantic_digest(digest_input) != recorded_digest:
        raise InteractionProtocolError("Answer digest mismatch")
    if answer.get("audit_run_id") != context["session"]["audit_run_id"]:
        raise InteractionProtocolError("Answer belongs to a different audit run")
    if answer.get("source_snapshot_digest") != context["session"]["source_snapshot_digest"]:
        raise InteractionProtocolError("Answer snapshot binding mismatch")
    question = _question(
        context["parent_bundle"], str(answer.get("question_ref", {}).get("record_id"))
    )
    if answer.get("answer_kind") in {"candidate_selection", "unknown"}:
        option = next(
            (
                item
                for item in question.get("candidate_answers", [])
                if item.get("answer_id") == answer.get("selected_option_id")
            ),
            None,
        )
        if option is None or canonical_json(option.get("value")) != canonical_json(
            answer.get("answer_value")
        ):
            raise InteractionProtocolError("Answer option and value do not match the question")
        if answer.get("answer_kind") == "unknown" and option.get("value") != {
            "action": "retain_unknown"
        }:
            raise InteractionProtocolError("unknown Answer must select the retain-unknown option")
        if answer.get("answer_kind") == "candidate_selection" and option.get("value") == {
            "action": "retain_unknown"
        }:
            raise InteractionProtocolError("retain-unknown option requires an unknown Answer")
        expected_dimensions = [str(question["unknown_semantic_dimension"])]
    elif answer.get("answer_kind") == "structured_value":
        values = answer.get("answer_value")
        if not isinstance(values, dict) or not values:
            raise InteractionProtocolError("structured Answer value must be a non-empty object")
        work_item = _submitted_work_item(context, str(question["question_id"]))
        allowed_dimensions = set(work_item["packet"]["unresolved_dimensions"])
        if any(key not in allowed_dimensions for key in values):
            raise InteractionProtocolError(
                "structured Answer contains a dimension outside the bounded WorkItem"
            )
        _validate_closed_method_answer(question, values)
        expected_dimensions = sorted(values)
    else:
        raise InteractionProtocolError("unsupported Answer kind for this interaction slice")
    expected_subjects, expected_kind = _answer_authority(context["parent_bundle"], question)
    scope = answer.get("authority_scope", {})
    if (
        scope.get("authority_kind") != expected_kind
        or scope.get("subject_refs") != expected_subjects
        or scope.get("semantic_dimensions") != expected_dimensions
    ):
        raise InteractionProtocolError("Answer authority scope escapes the MaterialQuestion")
    linked = any(
        any(
            ref.get("record_id") == question["question_id"]
            for ref in item.get("material_question_refs", [])
        )
        and item.get("status") == "submitted"
        for item in _latest_records(context["derived_store"], "work_item", "work_item_id").values()
    )
    if not linked:
        raise InteractionProtocolError("Answer has no submitted WorkItem")


def _load_session(
    root: Path, schema_root: Path, *, require_unlocked: bool = False
) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise InteractionProtocolError(f"interaction root is unavailable or unsafe: {root}")
    layout = AuditLayout(root.resolve())
    if require_unlocked and layout.lock_path.exists():
        raise InteractionProtocolError("semantic lock already exists; interaction is closed")
    session = _read_object(layout.observed / _SESSION_FILE)
    digest_input = copy.deepcopy(session)
    session_digest = digest_input.pop("session_digest", None)
    if semantic_digest(digest_input) != session_digest:
        raise InteractionProtocolError("pre-lock session digest mismatch")
    parent_bundle = _read_object(layout.observed / _PARENT_BUNDLE_FILE)
    parent_lock = _read_object(layout.observed / _PARENT_LOCK_FILE)
    if semantic_digest(parent_bundle) != session.get("parent_bundle_digest"):
        raise InteractionProtocolError("imported parent bundle digest mismatch")
    lock_input = copy.deepcopy(parent_lock)
    lock_digest = lock_input.pop("semantic_lock_digest", None)
    if semantic_digest(lock_input) != lock_digest or lock_digest != session.get(
        "parent_semantic_lock_digest"
    ):
        raise InteractionProtocolError("imported parent semantic lock digest mismatch")
    registry = LocalSchemaRegistry(schema_root)
    registry.validate(parent_bundle)
    observed_store = JsonlRecordStore(layout.observed)
    derived_store = JsonlRecordStore(layout.derived)
    deadline_ledger = load_deadline_ledger(layout.observed / LEDGER_FILENAME)
    for record in [*observed_store.iter_records(), *derived_store.iter_records()]:
        registry.validate(record)
    states = [
        AuditState(str(record["state"]))
        for record in observed_store.iter_records("audit_run")
        if record.get("audit_run_id") == session.get("audit_run_id")
    ]
    if not states:
        raise InteractionProtocolError("pre-lock AuditRun state is unavailable")
    return {
        "layout": layout,
        "session": session,
        "parent_bundle": parent_bundle,
        "parent_lock": parent_lock,
        "registry": registry,
        "observed_store": observed_store,
        "derived_store": derived_store,
        "deadline_ledger": deadline_ledger,
        "state": states[-1],
    }


def _append_run_state(
    layout: AuditLayout,
    registry: LocalSchemaRegistry,
    session: dict[str, Any],
    target: AuditState,
    *,
    terminal_reason: str | None = None,
) -> None:
    store = JsonlRecordStore(layout.observed)
    states = [
        AuditState(str(record["state"]))
        for record in store.iter_records("audit_run")
        if record.get("audit_run_id") == session["audit_run_id"]
    ]
    if not states:
        raise InteractionProtocolError("AuditRun has no current state")
    transition(states[-1], target)
    record = build_audit_run_record(
        str(session["audit_run_id"]),
        target.value,
        str(session["created_at"]),
        snapshot_id=str(session["snapshot_id"]),
        parent_run_id=str(session["parent_audit_run_id"]),
        terminal_reason=terminal_reason,
    )
    registry.validate(record)
    store.append(record)


def _checkpoint_interaction_deadline(context: dict[str, Any], at: str, event: str) -> None:
    ledger, exhausted = advance_or_exhaust(
        context["deadline_ledger"],
        at=at,
        event=event,
    )
    context["deadline_ledger"] = ledger
    _write_context_deadline(context)
    if not exhausted:
        return
    _append_run_state(
        context["layout"],
        context["registry"],
        context["session"],
        AuditState.PARTIAL_DEADLINE,
        terminal_reason="User-visible hard deadline reached before semantic lock.",
    )
    raise InteractionProtocolError("user-visible hard deadline exhausted before semantic lock")


def _write_context_deadline(context: dict[str, Any]) -> None:
    write_deadline_ledger(
        context["layout"].observed / LEDGER_FILENAME,
        context["deadline_ledger"],
    )


def _interaction_timestamp(context: dict[str, Any], explicit: str | None) -> str:
    if explicit is not None:
        return explicit
    if context["session"].get("clock_mode") == "injected":
        return str(context["deadline_ledger"]["segments"][-1]["last_accounted_at"])
    return _timestamp_now()


def _latest_records(
    store: JsonlRecordStore, record_type: str, identity_field: str
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in store.iter_records(record_type):
        identity = record.get(identity_field)
        if isinstance(identity, str):
            result[identity] = record
    return result


def _source_snapshot_digest(bundle: dict[str, Any]) -> str:
    snapshots = bundle.get("repository_snapshots", [])
    if not isinstance(snapshots, list) or len(snapshots) != 1:
        raise InteractionProtocolError("source audit must contain exactly one snapshot")
    digest = snapshots[0].get("snapshot_digest")
    if not isinstance(digest, str):
        raise InteractionProtocolError("source snapshot digest is unavailable")
    return digest


def _source_surface(parent_bundle: dict[str, Any], question: dict[str, Any]) -> dict[str, Any]:
    question_id = question.get("question_id")
    matches = [
        surface
        for surface in parent_bundle.get("publication_surfaces", [])
        if surface.get("selection", {}).get("material_question_id") == question_id
    ]
    if len(matches) != 1:
        raise InteractionProtocolError(
            "this slice requires one publication-surface question and subject"
        )
    return cast(dict[str, Any], matches[0])


def _packet_source_refs(
    parent_bundle: dict[str, Any], surface: dict[str, Any]
) -> list[dict[str, Any]]:
    artifact_paths = {
        str(artifact["path"])
        for artifact in parent_bundle.get("artifacts", [])
        if any(
            candidate.get("surface_ref", {}).get("record_id") == artifact.get("artifact_id")
            for candidate in surface.get("candidates", [])
        )
        and isinstance(artifact.get("path"), str)
    }
    by_value: dict[str, dict[str, Any]] = {}
    for parser_result in parent_bundle.get("parser_results", []):
        source_ref = parser_result.get("source_ref")
        if isinstance(source_ref, dict) and source_ref.get("path") in artifact_paths:
            by_value[canonical_json(source_ref)] = copy.deepcopy(source_ref)
    return [by_value[key] for key in sorted(by_value)]


def _question(parent_bundle: dict[str, Any], question_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in parent_bundle.get("material_questions", [])
        if item.get("question_id") == question_id and item.get("status") == "open"
    ]
    if len(matches) != 1:
        raise InteractionProtocolError("Answer question is not uniquely open in the source audit")
    return cast(dict[str, Any], matches[0])


def _question_contract(parent_bundle: dict[str, Any], question: dict[str, Any]) -> dict[str, Any]:
    contract_id = question.get("extensions", {}).get("x-contract-ref", {}).get("record_id")
    matches = [
        contract
        for contract in parent_bundle.get("scientific_contracts", [])
        if contract.get("contract_id") == contract_id
    ]
    if len(matches) != 1:
        raise InteractionProtocolError("contract question has no unique ScientificContract")
    return cast(dict[str, Any], matches[0])


def _submitted_work_item(context: dict[str, Any], question_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in _latest_records(context["derived_store"], "work_item", "work_item_id").values()
        if item.get("status") == "submitted"
        and any(
            ref.get("record_id") == question_id for ref in item.get("material_question_refs", [])
        )
    ]
    if len(matches) != 1:
        raise InteractionProtocolError("question has no unique submitted WorkItem")
    return matches[0]


def _answer_authority(
    parent_bundle: dict[str, Any], question: dict[str, Any]
) -> tuple[list[dict[str, str]], str]:
    if question.get("unknown_semantic_dimension") == "publication_surface":
        surface = _source_surface(parent_bundle, question)
        return (
            [typed_ref("publication_surface", str(surface["publication_surface_id"]))],
            "publication_surface",
        )
    contract = _question_contract(parent_bundle, question)
    scope = contract.get("scope", {})
    subject_refs = copy.deepcopy(scope.get("subject_refs", []))
    if len(subject_refs) != 1 or scope.get("level") not in {"claim", "analysis"}:
        raise InteractionProtocolError("scientific-intent question has no bounded subject")
    if scope.get("level") == "claim":
        expected = [
            typed_ref("claim", str(value)) for value in question.get("affected_claim_ids", [])
        ]
        if subject_refs != expected:
            raise InteractionProtocolError("scientific-intent Claim authority mismatch")
    elif (
        question.get("affected_claim_ids") != []
        or subject_refs[0].get("record_type") != "publication_surface"
        or question.get("extensions", {}).get("x-analysis-subject-ref") != subject_refs[0]
        or not _valid_analysis_contract_question(question)
    ):
        raise InteractionProtocolError("scientific-intent analysis authority mismatch")
    return subject_refs, "scientific_intent"


def _selected_artifact_path(artifacts: list[dict[str, Any]], answer: dict[str, Any]) -> str | None:
    selected_id = answer.get("answer_value")
    artifact = next((item for item in artifacts if item.get("artifact_id") == selected_id), None)
    return str(artifact["path"]) if artifact is not None else None


def _verify_snapshot_source(layout: AuditLayout, source_ref: dict[str, Any]) -> None:
    path_value = source_ref.get("path")
    digest = source_ref.get("content_digest")
    if not isinstance(path_value, str) or not isinstance(digest, str):
        raise InteractionProtocolError("proposal source lacks exact path and content digest")
    relative = PurePosixPath(path_value)
    if relative.is_absolute() or ".." in relative.parts:
        raise InteractionProtocolError("proposal source path is unsafe")
    materialized_root = (layout.observed / "snapshot" / "materialized").resolve()
    path = (materialized_root / relative.as_posix()).resolve()
    try:
        path.relative_to(materialized_root)
    except ValueError as error:
        raise InteractionProtocolError("proposal source escapes the immutable snapshot") from error
    if path.is_symlink() or not path.is_file() or sha256_digest(path.read_bytes()) != digest:
        raise InteractionProtocolError("proposal source does not resolve in the immutable snapshot")
    quoted = source_ref.get("quoted_text")
    start = source_ref.get("start_line")
    end = source_ref.get("end_line")
    if isinstance(quoted, str) and isinstance(start, int) and isinstance(end, int):
        lines = path.read_text(encoding="utf-8").splitlines()
        if start < 1 or end < start or end > len(lines):
            raise InteractionProtocolError("proposal quote span is outside its source")
        if quoted not in "\n".join(lines[start - 1 : end]):
            raise InteractionProtocolError("proposal quoted text was not found at its source span")


def _snapshot_projection(context: dict[str, Any], snapshot_record: dict[str, Any]) -> Any:
    """Rehydrate the bounded SnapshotOutput fields needed by deterministic coverage."""

    from sc_referee.snapshot.repository import AssetIdentityPolicy, SnapshotOutput

    return SnapshotOutput(
        snapshot_record=snapshot_record,
        file_records=[],
        asset_identity_records=[],
        materialized_root=context["layout"].observed / "snapshot" / "materialized",
        identity_policy=AssetIdentityPolicy(),
    )


def _read_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise InteractionProtocolError(f"required interaction file is unavailable: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise InteractionProtocolError(f"required interaction file is not an object: {path.name}")
    return value


def _timestamp_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
