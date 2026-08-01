from __future__ import annotations

import copy
import json
import math
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, stable_id
from sc_referee.method_contracts import (
    EXPECTED_COUNT_PROFILE_ID,
    EXPECTED_COUNT_REQUIRED_DIMENSIONS,
    SCIENTIFIC_CONTRACT_DIMENSIONS,
)
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.scientific_checks.core import (
    FrozenInspectionContext,
    InspectionDocument,
    RecordRef,
)
from sc_referee.version import SCHEMA_VERSION

EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_ID = "expected_count_unresolved_obligation_v1"
EXPECTED_COUNT_UNRESOLVED_DIMENSION_GUIDE = {
    "adjustment_set": "Which covariates or adjustment terms enter the expected-count calculation?",
    "control_set": "Which observations are allowed to define the background?",
    "dependence_structure": "How are replicates or groups handled?",
    "measurement_model": "Which estimator, likelihood, and link define expected counts?",
    "scale_and_orientation": (
        "At what resolution and on which scale or orientation are values computed?"
    ),
    "selection_process": (
        "Which observations are excluded, including whether the focal target is excluded?"
    ),
}

_NUMBER = r"-?(?:0|[1-9][0-9]*)(?:[.][0-9]+)?"
_OUTPUT_NAME = r"[a-z][a-z0-9_]{0,63}"
_TASK_PATH_NAMES = frozenset({"prompt.md", "question.md", "task.md"})
_TASK_REQUEST = re.compile(
    r"(?is)\bReport\s+three\s+quantities\s*:\s*"
    rf"`(?P<case_key>{_OUTPUT_NAME})`\s*\(\s*mean\s+log2\s*"
    r"\(\s*observed\s*/\s*expected\s*\)"
    r"\s+across\s+case\s+replicates\s*\)\s*,\s*"
    rf"`(?P<control_key>{_OUTPUT_NAME})`\s*\(\s*mean\s+log2\s*"
    r"\(\s*observed\s*/\s*expected\s*\)"
    r"\s+across\s+control\s+replicates\s*\)\s*,\s*and\s*"
    rf"`(?P<delta_key>{_OUTPUT_NAME})`\s*\(\s*case\s+minus\s+control\s*\)"
)
_PRIMARY_VALUE = re.compile(rf"(?m)^-\s*`(?P<key>{_OUTPUT_NAME})`\s*:\s*(?P<value>{_NUMBER})\s*$")
_PRIMARY_METHOD_PATTERNS = (
    re.compile(
        r"(?is)\bExpected\s+is\s+the\s+per-replicate\s+arithmetic\s+mean\s+of\s+all\s+"
        r"(?P<count>[1-9][0-9]*)\s+intrachromosomal\s+"
        r"(?P<resolution>[1-9][0-9]*)\s*kb\s+pixels\s+at\s+"
        r"`?dist_bin\s*=\s*(?P<distance>[1-9][0-9]*)`?\s*,\s*"
        r"including\s+the\s+focal\s+pixel\."
    ),
    re.compile(
        r"(?is)\bExpected\s+is\s+the\s+per-replicate\s+arithmetic\s+mean\s+of\s+all\s+"
        r"(?P<count>[1-9][0-9]*)\s+comparison\s+observations\s+in\s+the\s+same\s+"
        r"declared\s+stratum\s*,\s*including\s+the\s+focal\s+observation\."
    ),
)
_SENSITIVITY_PATTERNS = (
    re.compile(
        rf"(?is)\bExcluding\s+only\s+the\s+focal\s+pixel\s+from\s+the\s+expected\s+gives\s+"
        rf"case\s*=\s*(?P<case_value>{_NUMBER})\s*,\s*"
        rf"control\s*=\s*(?P<control_value>{_NUMBER})\s*,\s*"
        rf"and\s+delta\s*=\s*(?P<delta_value>{_NUMBER})\."
    ),
    re.compile(
        rf"(?is)\bExcluding\s+only\s+the\s+focal\s+observation\s+from\s+the\s+expected\s+"
        rf"gives\s+`(?P<case_key>{_OUTPUT_NAME})`\s*=\s*"
        rf"(?P<case_value>{_NUMBER})\s*,\s*"
        rf"`(?P<control_key>{_OUTPUT_NAME})`\s*=\s*"
        rf"(?P<control_value>{_NUMBER})\s*,\s*and\s*"
        rf"`(?P<delta_key>{_OUTPUT_NAME})`\s*=\s*"
        rf"(?P<delta_value>{_NUMBER})\."
    ),
)
_EXPECTED_DEFINITION_TRIGGER = re.compile(r"(?i)\bExpected\s+is\b")

EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE: dict[str, Any] = {
    "profile_id": EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_ID,
    "profile_version": "1.0.0",
    "method_profile_id": EXPECTED_COUNT_PROFILE_ID,
    "task_path_names": sorted(_TASK_PATH_NAMES),
    "required_task_output_roles": ["case", "control", "delta"],
    "unresolved_dimension_guide": EXPECTED_COUNT_UNRESOLVED_DIMENSION_GUIDE,
    "required_evidence": [
        "one exact task-like Markdown request for mean log2(observed/expected)",
        "no complete supported expected-count declaration in inspected Markdown",
        "one enumerated selected-report target-inclusive same-stratum mean declaration",
        "one exact three-value primary result set",
        "one exact three-value target-exclusion sensitivity result set",
        "at least one exact primary-versus-sensitivity value difference",
    ],
    "output_ceiling": "question_only",
    "non_inferences": [
        "No expected-count estimator is nominated as scientifically correct.",
        "No numeric difference is called material, acceptable, or excessive.",
        "No project-authored code is executed.",
        "No Claim, detector candidate, or Finding is emitted by this profile.",
    ],
}
EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_DIGEST = semantic_digest(
    EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE
)


@dataclass(frozen=True)
class ExpectedCountObligationCompilation:
    contract: dict[str, Any]
    question: dict[str, Any]


@dataclass(frozen=True)
class _ExactMatch:
    document: InspectionDocument
    start: int
    end: int

    def source_ref(self) -> dict[str, Any]:
        text = self.document.content.decode("utf-8")
        start_line = text.count("\n", 0, self.start) + 1
        end_line = text.count("\n", 0, self.end) + 1
        start_column = self.start - text.rfind("\n", 0, self.start)
        end_column = self.end - text.rfind("\n", 0, self.end)
        return {
            "source_kind": "file_span",
            "locator": f"{self.document.path}:{start_line}-{end_line}",
            "path": self.document.path,
            "content_digest": self.document.content_digest,
            "start_line": start_line,
            "end_line": end_line,
            "start_column": start_column,
            "end_column": end_column,
            "quoted_text": text[self.start : self.end],
        }


@dataclass(frozen=True)
class _TaskRequestMatch:
    evidence: _ExactMatch
    output_keys: tuple[str, str, str]


def compile_unresolved_expected_count_obligation(
    *,
    context: FrozenInspectionContext,
    run_id: str,
    created_at: str,
) -> ExpectedCountObligationCompilation | None:
    """Compile ADR-0018's exact claimless unresolved expected-count question."""

    markdown_documents = [
        document
        for document in context.documents
        if document.media_type == "text/markdown"
        and document.parser_result_payload is not None
        and document.parser_result_ref is not None
    ]
    if not markdown_documents or not _all_markdown_completely_inspected(
        context, markdown_documents
    ):
        return None
    if any(_supported_expected_count_declarations(document) for document in markdown_documents):
        return None

    report = _selected_report_document(context)
    if report is None:
        return None
    report_text = _strict_text(report)
    if report_text is None:
        return None

    task_matches = _task_request_matches(markdown_documents, report)
    method_matches = [
        match for pattern in _PRIMARY_METHOD_PATTERNS for match in pattern.finditer(report_text)
    ]
    sensitivity_matches = [
        (index, match)
        for index, pattern in enumerate(_SENSITIVITY_PATTERNS)
        for match in pattern.finditer(report_text)
    ]
    if (
        len(task_matches) != 1
        or len(method_matches) != 1
        or len(sensitivity_matches) != 1
        or len(_EXPECTED_DEFINITION_TRIGGER.findall(report_text)) != 1
    ):
        return None

    output_keys = task_matches[0].output_keys
    if len(set(output_keys)) != 3:
        return None
    primary_matches: dict[str, re.Match[str]] = {}
    primary_values: dict[str, float] = {}
    all_primary_matches = list(_PRIMARY_VALUE.finditer(report_text))
    for key in output_keys:
        matches = [match for match in all_primary_matches if match.group("key") == key]
        if len(matches) != 1:
            return None
        value = _finite_float(matches[0].group("value"))
        if value is None:
            return None
        primary_matches[key] = matches[0]
        primary_values[key] = value

    sensitivity_pattern_index, sensitivity_match = sensitivity_matches[0]
    if (
        sensitivity_pattern_index == 1
        and (
            sensitivity_match.group("case_key"),
            sensitivity_match.group("control_key"),
            sensitivity_match.group("delta_key"),
        )
        != output_keys
    ):
        return None
    sensitivity_values = {
        output_keys[0]: _finite_float(sensitivity_match.group("case_value")),
        output_keys[1]: _finite_float(sensitivity_match.group("control_value")),
        output_keys[2]: _finite_float(sensitivity_match.group("delta_value")),
    }
    if any(value is None for value in sensitivity_values.values()):
        return None
    exact_sensitivity_values = {
        key: float(value) for key, value in sensitivity_values.items() if value is not None
    }
    changed_outputs = [
        key
        for key in sorted(primary_values)
        if primary_values[key] != exact_sensitivity_values[key]
    ]
    if not changed_outputs:
        return None

    evidence_matches = [
        task_matches[0].evidence,
        _ExactMatch(report, method_matches[0].start(), method_matches[0].end()),
        *[
            _ExactMatch(report, match.start(), match.end())
            for _, match in sorted(primary_matches.items())
        ],
        _ExactMatch(report, sensitivity_match.start(), sensitivity_match.end()),
    ]
    source_refs_by_value = {
        canonical_json(match.source_ref()): match.source_ref() for match in evidence_matches
    }
    source_refs = [source_refs_by_value[key] for key in sorted(source_refs_by_value)]
    evidence_digest = semantic_digest(
        {
            "source_refs": source_refs,
            "primary_values": primary_values,
            "sensitivity_values": exact_sensitivity_values,
            "changed_outputs": changed_outputs,
        }
    )
    subject_ref = context.selected_surface_ref.to_dict()
    contract_id = stable_id(
        "contract-analysis-expected-count-obligation",
        run_id,
        EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_DIGEST,
        evidence_digest,
    )
    contract = _contract(
        contract_id=contract_id,
        run_id=run_id,
        created_at=created_at,
        subject_ref=subject_ref,
        source_refs=source_refs,
        evidence_digest=evidence_digest,
    )
    question = _question(
        contract_id=contract_id,
        run_id=run_id,
        created_at=created_at,
        subject_ref=subject_ref,
        changed_outputs=changed_outputs,
        source_refs=source_refs,
        evidence_digest=evidence_digest,
    )
    return ExpectedCountObligationCompilation(contract=contract, question=question)


def valid_analysis_expected_count_obligation_question(question: dict[str, Any]) -> bool:
    extensions = question.get("extensions")
    if not isinstance(extensions, dict):
        return False
    evidence_digest = extensions.get("x-unresolved-obligation-evidence-digest")
    changed_outputs = extensions.get("x-demonstrated-sensitive-outputs")
    return (
        question.get("affected_claim_ids") == []
        and extensions.get("x-method-profile-id") == EXPECTED_COUNT_PROFILE_ID
        and extensions.get("x-unresolved-obligation-profile")
        == EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_ID
        and extensions.get("x-unresolved-obligation-profile-digest")
        == EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_DIGEST
        and extensions.get("x-unresolved-dimensions") == list(EXPECTED_COUNT_REQUIRED_DIMENSIONS)
        and extensions.get("x-answer-shape") == "expected_count_background_v1-dimension-values"
        and extensions.get("x-unresolved-dimension-guide")
        == EXPECTED_COUNT_UNRESOLVED_DIMENSION_GUIDE
        and isinstance(extensions.get("x-analysis-subject-ref"), dict)
        and extensions["x-analysis-subject-ref"].get("record_type") == "publication_surface"
        and isinstance(evidence_digest, str)
        and evidence_digest.startswith("sha256:")
        and isinstance(changed_outputs, list)
        and bool(changed_outputs)
        and changed_outputs == sorted(set(changed_outputs))
        and len(changed_outputs) <= 3
        and all(
            isinstance(value, str) and re.fullmatch(_OUTPUT_NAME, value) is not None
            for value in changed_outputs
        )
        and extensions.get("x-output-ceiling") == "question_only"
    )


def _contract(
    *,
    contract_id: str,
    run_id: str,
    created_at: str,
    subject_ref: dict[str, str],
    source_refs: list[dict[str, Any]],
    evidence_digest: str,
) -> dict[str, Any]:
    unknown_reason = (
        "The task requests observed/expected values and the selected report demonstrates that "
        "one background change alters those values, but no supported governing expected-count "
        "profile was established."
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "scientific_contract",
        "contract_id": contract_id,
        "audit_run_id": run_id,
        "title": "Unresolved analysis-scoped expected-count contract",
        "status": "draft",
        "scope": {"level": "analysis", "subject_refs": [subject_ref]},
        "dimensions": {
            dimension: {
                "state": "unknown",
                "reason": unknown_reason,
                "searched_source_refs": copy.deepcopy(source_refs),
            }
            for dimension in SCIENTIFIC_CONTRACT_DIMENSIONS
        },
        "source_refs": copy.deepcopy(source_refs),
        "created_at": created_at,
        "notes": (
            "Question-only ADR-0018 unresolved-obligation profile. Exact sensitivity is "
            "demonstrated, but estimator correctness, materiality, execution, and intent remain "
            "unknown."
        ),
        "extensions": {
            "x-method-profile-id": EXPECTED_COUNT_PROFILE_ID,
            "x-unresolved-obligation-profile": (EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_ID),
            "x-unresolved-obligation-profile-digest": (
                EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_DIGEST
            ),
            "x-unresolved-obligation-evidence-digest": evidence_digest,
            "x-output-ceiling": "question_only",
        },
    }


def _question(
    *,
    contract_id: str,
    run_id: str,
    created_at: str,
    subject_ref: dict[str, str],
    changed_outputs: list[str],
    source_refs: list[dict[str, Any]],
    evidence_digest: str,
) -> dict[str, Any]:
    question_id = stable_id(
        "question-analysis-expected-count-obligation",
        run_id,
        contract_id,
        evidence_digest,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "material_question",
        "question_id": question_id,
        "audit_run_id": run_id,
        "question": "Which expected-count/background profile governs the requested values?",
        "unknown_semantic_dimension": "scientific_contract",
        "why_it_matters": (
            "The report gives exact primary and target-exclusion sensitivity values that differ, "
            "while the governing expected-count recipe remains unresolved. The recipe must name "
            "the background observations, statistical model, replicate or group handling, "
            "covariates, resolution and scale, and exclusions including focal-target handling."
        ),
        "candidate_answers": [
            {
                "answer_id": stable_id("answer-option", question_id, "provide-structured-intent"),
                "label": "Provide expected-count recipe",
                "value": {"action": "provide_structured_intent"},
                "consequence": (
                    "Declare: which observations define the background; which estimator, "
                    "likelihood, and link define expected counts; how replicates or groups are "
                    "handled; which covariates enter; the resolution, scale, and orientation; "
                    "and which observations are excluded, including the focal target. Only these "
                    "review-scoped declarations enter the contract; compatibility with the "
                    "unsupported reported method remains unavailable."
                ),
            },
            {
                "answer_id": stable_id("answer-option", question_id, "retain-unknown"),
                "label": "Retain unresolved",
                "value": {"action": "retain_unknown"},
                "consequence": (
                    "No estimator is nominated and no method-compatibility conclusion is drawn."
                ),
            },
        ],
        "evidence_searched": [
            {
                "source": "completely inspected bounded task and selected-report Markdown",
                "result": (
                    "The task requests mean log2(observed/expected); no complete supported "
                    "expected-count profile was found; the report states one primary background "
                    f"and exact sensitivity values that change {len(changed_outputs)} requested "
                    "output(s)."
                ),
            },
            {
                "source": "exact immutable source spans",
                "result": (
                    f"{len(source_refs)} digest-bound span(s) support the bounded premises. "
                    "They do not establish which method should govern."
                ),
            },
        ],
        "blocked_detector_ids": [],
        "affected_claim_ids": [],
        "linked_conditional_concern_ids": [],
        "priority": "high",
        "status": "open",
        "answer_ids": [],
        "created_at": created_at,
        "provenance": controller_provenance(
            "deterministic_expected_count_unresolved_obligation_v1", created_at
        ),
        "extensions": {
            "x-contract-ref": typed_ref("scientific_contract", contract_id),
            "x-analysis-subject-ref": subject_ref,
            "x-method-profile-id": EXPECTED_COUNT_PROFILE_ID,
            "x-unresolved-dimensions": list(EXPECTED_COUNT_REQUIRED_DIMENSIONS),
            "x-unresolved-dimension-guide": EXPECTED_COUNT_UNRESOLVED_DIMENSION_GUIDE,
            "x-answer-shape": "expected_count_background_v1-dimension-values",
            "x-unresolved-obligation-profile": (EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_ID),
            "x-unresolved-obligation-profile-digest": (
                EXPECTED_COUNT_UNRESOLVED_OBLIGATION_PROFILE_DIGEST
            ),
            "x-unresolved-obligation-evidence-digest": evidence_digest,
            "x-demonstrated-sensitive-outputs": changed_outputs,
            "x-output-ceiling": "question_only",
        },
    }


def _all_markdown_completely_inspected(
    context: FrozenInspectionContext, documents: list[InspectionDocument]
) -> bool:
    represented_parser_refs = {
        document.parser_result_ref
        for document in documents
        if document.parser_result_ref is not None
    }
    all_markdown_parser_refs = {
        record.ref
        for record in context.base_records
        if record.ref.record_type == "parser_result"
        and json.loads(record.canonical_payload).get("parser_id") == "parser:markdown-inventory"
    }
    if represented_parser_refs != all_markdown_parser_refs:
        return False
    for document in documents:
        payload = _parser_payload(document)
        if payload is None:
            return False
        if (
            payload.get("parser_id") != "parser:markdown-inventory"
            or payload.get("parser_version") != "0.2.0"
            or payload.get("state") != "parsed"
            or payload.get("coverage_status") != "covered"
            or _strict_text(document) is None
        ):
            return False
    return True


def _supported_expected_count_declarations(document: InspectionDocument) -> bool:
    payload = _parser_payload(document)
    if payload is None:
        return False
    declarations = payload.get("extensions", {}).get("x-expected-count-method-declarations")
    return isinstance(declarations, list) and bool(declarations)


def _task_request_matches(
    documents: list[InspectionDocument], report: InspectionDocument
) -> list[_TaskRequestMatch]:
    matches: list[_TaskRequestMatch] = []
    for document in documents:
        if (
            document.path == report.path
            or PurePosixPath(document.path).name not in _TASK_PATH_NAMES
        ):
            continue
        text = _strict_text(document)
        if text is None:
            continue
        document_matches = list(_TASK_REQUEST.finditer(text))
        matches.extend(
            _TaskRequestMatch(
                evidence=_ExactMatch(document, match.start(), match.end()),
                output_keys=(
                    match.group("case_key"),
                    match.group("control_key"),
                    match.group("delta_key"),
                ),
            )
            for match in document_matches
        )
    return matches


def _selected_report_document(
    context: FrozenInspectionContext,
) -> InspectionDocument | None:
    artifact = _base_record(context, context.selected_artifact_ref)
    surface = _base_record(context, context.selected_surface_ref)
    if (
        artifact is None
        or artifact.get("kind") != "report"
        or surface is None
        or surface.get("status") != "resolved"
        or surface.get("selection", {}).get("selected_surface_refs")
        != [context.selected_artifact_ref.to_dict()]
    ):
        return None
    path = artifact.get("path")
    identity_ref = artifact.get("asset_identity_ref")
    if not isinstance(path, str) or not isinstance(identity_ref, dict):
        return None
    identity = _base_record(
        context,
        RecordRef(str(identity_ref.get("record_type")), str(identity_ref.get("record_id"))),
    )
    digest = (
        identity.get("identity_evidence", {}).get("digest")
        if isinstance(identity, dict) and identity.get("tier") == "full_digest"
        else None
    )
    matches = [
        document
        for document in context.documents
        if document.path == path
        and document.media_type == "text/markdown"
        and document.content_digest == digest
    ]
    return matches[0] if len(matches) == 1 else None


def _base_record(context: FrozenInspectionContext, ref: RecordRef) -> dict[str, Any] | None:
    matches = [record for record in context.base_records if record.ref == ref]
    if len(matches) != 1:
        return None
    payload = json.loads(matches[0].canonical_payload)
    return payload if isinstance(payload, dict) else None


def _parser_payload(document: InspectionDocument) -> dict[str, Any] | None:
    if document.parser_result_payload is None:
        return None
    payload = json.loads(document.parser_result_payload)
    return payload if isinstance(payload, dict) else None


def _strict_text(document: InspectionDocument) -> str | None:
    try:
        return document.content.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _finite_float(text: str) -> float | None:
    value = float(text)
    return value if math.isfinite(value) else None
