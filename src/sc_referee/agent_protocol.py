from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from sc_referee.core.ids import semantic_digest
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.reporting.html import render_report_bytes
from sc_referee.reporting.policy import validate_report_contract
from sc_referee.storage.integrity import verify_sqlite_index, verify_storage_manifest
from sc_referee.storage.layout import AuditLayout


class AssessmentCounts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    findings: int
    conditional_concerns: int
    material_questions: int
    disclosures: int


class AgentDeadlinePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["quick", "standard", "publication"]
    scheduling_cutoff_seconds: float
    hard_seconds: float
    scientist_wait_pauses_elapsed_time: bool


class AgentAuditStatus(BaseModel):
    """Small typed, read-only status payload for an agent integration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_version: Literal["0.1.0"] = "0.1.0"
    audit_run_id: str
    run_state: str
    terminal: bool
    integrity: Literal["verified"] = "verified"
    overall_status: str
    publication_surface_status: str
    semantic_lock_digest: str
    assessment_counts: AssessmentCounts
    open_question_ids: list[str]
    known_gap_count: int
    model_calls_recorded: int | None
    model_access_after_lock: bool | None
    deadline_policy: AgentDeadlinePolicy | None
    bundle_path: str
    report_path: str


class AgentQuestionOption(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    answer_id: str
    label: str
    value: Any
    consequence: str


class AgentRequirementCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str
    label: str
    operand: dict[str, Any]
    authority_basis: str


class AgentObservedOperand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dimension: str
    assertion_id: str
    subject_ref: dict[str, str]
    predicate: str
    value: Any
    authority_scope: str
    finding_eligibility: str
    source_refs: list[dict[str, Any]]


class AgentQuestionScope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    level: str
    subject_refs: list[dict[str, str]]


class AgentMaterialQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: str
    question: str
    unknown_semantic_dimension: str
    why_it_matters: str
    priority: str
    candidate_answers: list[AgentQuestionOption]
    affected_claim_ids: list[str]
    review_scope: AgentQuestionScope | None = None
    comparison_forms: dict[str, str] = Field(default_factory=dict)
    requirement_candidates: list[AgentRequirementCandidate] = Field(default_factory=list)
    observed_operands: list[AgentObservedOperand] = Field(default_factory=list)
    output_ceiling: str | None = None
    authority_limitation: str | None = None


class AgentQuestionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    protocol_version: Literal["0.1.0"] = "0.1.0"
    audit_run_id: str
    semantic_lock_digest: str
    integrity: Literal["verified"] = "verified"
    questions: list[AgentMaterialQuestion]


def load_audit_status(audit_root: Path, schema_root: Path) -> AgentAuditStatus:
    """Validate a completed audit and return a bounded machine-readable status."""

    layout = AuditLayout(audit_root.resolve())
    if audit_root.is_symlink() or not audit_root.is_dir():
        raise ValueError(f"audit root is unavailable or unsafe: {audit_root}")
    bundle = _read_object(layout.bundle_path)
    locked = _read_object(layout.lock_path)
    if layout.report_path.is_symlink() or not layout.report_path.is_file():
        raise ValueError("audit report is unavailable or unsafe")

    registry = LocalSchemaRegistry(schema_root)
    registry.validate(bundle)
    validate_report_contract(bundle)
    if layout.report_path.read_bytes() != render_report_bytes(bundle):
        raise ValueError("audit report bytes do not match the deterministic bundle rendering")
    if bundle.get("audit_run_id") != locked.get("audit_run_id"):
        raise ValueError("bundle and semantic lock belong to different audit runs")
    lock_digest = locked.get("semantic_lock_digest")
    if not isinstance(lock_digest, str):
        raise ValueError("semantic lock digest is missing")
    digest_input = dict(locked)
    digest_input.pop("semantic_lock_digest", None)
    if semantic_digest(digest_input) != lock_digest:
        raise ValueError("semantic lock digest mismatch")
    if bundle.get("semantic_lock_digest") != lock_digest:
        raise ValueError("bundle does not bind the semantic lock digest")

    manifests = bundle.get("storage_manifests")
    if not isinstance(manifests, list) or len(manifests) != 1:
        raise ValueError("exactly one storage manifest is required")
    verify_storage_manifest(layout, manifests[0])
    verify_sqlite_index(layout.sqlite_path, _bundle_records(bundle))

    audit_runs = bundle.get("audit_runs")
    coverage_records = bundle.get("coverage_records")
    if (
        not isinstance(audit_runs, list)
        or not isinstance(coverage_records, list)
        or len(coverage_records) != 1
    ):
        raise ValueError("audit status records are incomplete")
    coverage = coverage_records[0]
    run_state = (
        audit_runs[-1].get("state")
        if audit_runs
        else coverage.get("extensions", {}).get("x-run-state")
    )
    if not isinstance(run_state, str):
        raise ValueError("terminal audit state is missing")
    terminal_states = {
        "complete",
        "partial_deadline",
        "partial_host_limit",
        "cancelled",
        "failed_controller",
    }
    surface_records = bundle.get("publication_surfaces", [])
    surface_status = (
        str(surface_records[0].get("status"))
        if isinstance(surface_records, list) and surface_records
        else "not_recorded"
    )
    model_calls = locked.get("model_calls")
    recorded_count = len(model_calls) if isinstance(model_calls, list) else None
    access_after_lock = locked.get("model_access_after_lock")
    deadline_policy = locked.get("deadline_policy")
    counts = coverage.get("assessment_counts")
    if not isinstance(counts, dict):
        raise ValueError("assessment counts are missing")
    questions = bundle.get("material_questions", [])
    known_gaps = coverage.get("known_gaps", [])
    return AgentAuditStatus(
        audit_run_id=str(bundle["audit_run_id"]),
        run_state=run_state,
        terminal=run_state in terminal_states,
        overall_status=str(coverage["overall_status"]),
        publication_surface_status=surface_status,
        semantic_lock_digest=lock_digest,
        assessment_counts=AssessmentCounts.model_validate(counts),
        open_question_ids=[
            str(question["question_id"])
            for question in questions
            if question.get("status") == "open"
        ],
        known_gap_count=len(known_gaps),
        model_calls_recorded=recorded_count,
        model_access_after_lock=(
            access_after_lock if isinstance(access_after_lock, bool) else None
        ),
        deadline_policy=(
            AgentDeadlinePolicy.model_validate(deadline_policy)
            if isinstance(deadline_policy, dict)
            else None
        ),
        bundle_path=str(layout.bundle_path),
        report_path=str(layout.report_path),
    )


def load_open_questions(audit_root: Path, schema_root: Path) -> AgentQuestionBatch:
    """Return an integrity-verified, bounded projection of open MaterialQuestions."""

    status = load_audit_status(audit_root, schema_root)
    bundle = _read_object(AuditLayout(audit_root.resolve()).bundle_path)
    questions = [
        _agent_material_question(bundle, question)
        for question in bundle.get("material_questions", [])
        if question.get("status") == "open"
    ]
    return AgentQuestionBatch(
        audit_run_id=status.audit_run_id,
        semantic_lock_digest=status.semantic_lock_digest,
        questions=questions,
    )


def _agent_material_question(
    bundle: dict[str, Any], question: dict[str, Any]
) -> AgentMaterialQuestion:
    extensions = question.get("extensions")
    extension_values = extensions if isinstance(extensions, dict) else {}
    contract_ref = extension_values.get("x-contract-ref")
    contract_id = contract_ref.get("record_id") if isinstance(contract_ref, dict) else None
    contracts = [
        item
        for item in bundle.get("scientific_contracts", [])
        if item.get("contract_id") == contract_id
    ]
    scope_value = contracts[0].get("scope") if len(contracts) == 1 else None
    review_scope = (
        AgentQuestionScope.model_validate(scope_value) if isinstance(scope_value, dict) else None
    )
    reported = extension_values.get("x-posthoc-reported-assertion-ids")
    dimensions_by_assertion: dict[str, str] = {}
    if isinstance(reported, dict):
        for dimension, assertion_ids in reported.items():
            if isinstance(dimension, str) and isinstance(assertion_ids, list):
                for assertion_id in assertion_ids:
                    if isinstance(assertion_id, str):
                        dimensions_by_assertion[assertion_id] = dimension
    observed_operands = [
        AgentObservedOperand(
            dimension=dimensions_by_assertion[str(assertion["assertion_id"])],
            assertion_id=str(assertion["assertion_id"]),
            subject_ref=dict(assertion["subject_ref"]),
            predicate=str(assertion["predicate"]),
            value=assertion.get("object"),
            authority_scope=str(assertion["authority_scope"]),
            finding_eligibility=str(assertion["finding_eligibility"]),
            source_refs=[dict(item) for item in assertion.get("source_refs", [])],
        )
        for assertion in bundle.get("semantic_assertions", [])
        if assertion.get("assertion_id") in dimensions_by_assertion
    ]
    candidate_values = extension_values.get("x-scientific-check-requirement-candidates")
    comparison_values = extension_values.get("x-posthoc-comparison-forms")
    authority_limitations = [
        assertion.get("extensions", {}).get("x-authority-limitation")
        for assertion in bundle.get("semantic_assertions", [])
        if assertion.get("assertion_id") in dimensions_by_assertion
    ]
    limitations = [item for item in authority_limitations if isinstance(item, str) and item]
    return AgentMaterialQuestion(
        question_id=str(question["question_id"]),
        question=str(question["question"]),
        unknown_semantic_dimension=str(question["unknown_semantic_dimension"]),
        why_it_matters=str(question["why_it_matters"]),
        priority=str(question["priority"]),
        candidate_answers=[
            AgentQuestionOption.model_validate(option)
            for option in question.get("candidate_answers", [])
        ],
        affected_claim_ids=[str(value) for value in question.get("affected_claim_ids", [])],
        review_scope=review_scope,
        comparison_forms=(
            {str(key): str(value) for key, value in comparison_values.items()}
            if isinstance(comparison_values, dict)
            else {}
        ),
        requirement_candidates=(
            [AgentRequirementCandidate.model_validate(item) for item in candidate_values]
            if isinstance(candidate_values, list)
            else []
        ),
        observed_operands=observed_operands,
        output_ceiling=(
            str(extension_values["x-output-ceiling"])
            if isinstance(extension_values.get("x-output-ceiling"), str)
            else None
        ),
        authority_limitation=limitations[0] if len(set(limitations)) == 1 else None,
    )


def _read_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required audit file is unavailable or unsafe: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"required audit file is not a JSON object: {path.name}")
    return value


def _bundle_records(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for value in bundle.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("record_type"), str):
                records.append(item)
    return records
