"""Digest-bound asymmetric answers for multiple-testing correction-scope questions.

The input is an external, noninteractive human attestation.  An incomplete-scope answer is
reported only as author-attributed conditional evidence.  A complete-scope answer is only a
pointer into the unchanged structural proof; the claimed factor is never a resolved value.
"""

from __future__ import annotations

import ast
import copy
import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.records.observed import controller_provenance, typed_ref
from sc_referee.scientific_checks.multiple_testing_scope_questions_v1 import (
    QUESTION_PURPOSE,
    GuidedCoverageProof,
    SourceSpan,
    existing_complete_coverage_recheck,
)
from sc_referee.version import SCHEMA_VERSION, __version__

ATTESTATION_PROFILE = "multiple_testing_correction_scope_attestations_v1"
ATTESTATION_PROFILE_VERSION = "1.0.0"
ANSWER_DIGEST_PROFILE = "canonical-json-excluding-answer-digest-v1"
CERTAINTY_BASIS = "The named human supplied this answer for the bound question."
MAX_ATTESTATION_BYTES = 1 << 20

INCOMPLETE_OPTION = "correction-scope-incomplete"
COMPLETE_OPTION = "correction-scope-complete"
UNKNOWN_OPTION = "correction-scope-unknown"
_OPTIONS = frozenset({INCOMPLETE_OPTION, COMPLETE_OPTION, UNKNOWN_OPTION})
_FACTOR_KINDS = frozenset(
    {
        "literal_multiplier",
        "resolved_constant_integer",
        "contract_family_size",
        "correction_input_count",
        "threshold_divisor",
    }
)
CLOSED_ATTESTATION_ERROR_CATEGORIES = frozenset(
    {
        "attestations-file-unavailable",
        "attestations-file-path-unsafe",
        "attestations-file-outside-size-bound",
        "attestations-json-invalid",
        "attestations-schema-invalid",
        "attestations-question-not-open",
        "attestations-answer-cardinality-invalid",
        "attestations-snapshot-binding-mismatch",
        "attestations-analysis-binding-mismatch",
        "attestations-evidence-binding-mismatch",
        "attestations-authority-binding-mismatch",
        "attestations-supersession-invalid",
        "attestations-claimed-correction-invalid",
    }
)


class MultipleTestingAttestationError(ValueError):
    """A deterministic, closed attestation preflight refusal."""

    def __init__(
        self,
        category: str,
        *,
        pointer: str = "",
        input_digest: str | None = None,
    ) -> None:
        if category not in CLOSED_ATTESTATION_ERROR_CATEGORIES:
            raise ValueError("unknown multiple-testing attestation error category")
        self.category = category
        self.pointer = pointer
        self.input_digest = input_digest
        suffix = f" at {pointer}" if pointer else ""
        digest = f" ({input_digest})" if input_digest is not None else ""
        super().__init__(f"{category}{suffix}{digest}")


@dataclass(frozen=True)
class LoadedAttestation:
    value: dict[str, Any]
    raw_bytes: bytes
    raw_digest: str
    semantic_digest: str


@dataclass(frozen=True)
class AttestationApplication:
    question: dict[str, Any]
    concern: dict[str, Any] | None
    answer: dict[str, Any]
    disclosure: dict[str, Any] | None
    guided_proof: GuidedCoverageProof | None
    lock_receipt: dict[str, Any]


def load_attestation_file(path: Path, *, project_root: Path) -> LoadedAttestation:
    """Read one external regular file once without following a symlink."""

    raw_path = str(path)
    if not path.is_absolute() or os.path.normpath(raw_path) != raw_path:
        raise MultipleTestingAttestationError("attestations-file-path-unsafe")
    try:
        before = os.lstat(path)
    except OSError as error:
        raise MultipleTestingAttestationError("attestations-file-unavailable") from error
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise MultipleTestingAttestationError("attestations-file-path-unsafe")
    if before.st_size > MAX_ATTESTATION_BYTES:
        raise MultipleTestingAttestationError("attestations-file-outside-size-bound")
    try:
        parent = path.parent.resolve(strict=True)
        project = project_root.resolve(strict=True)
    except OSError as error:
        raise MultipleTestingAttestationError("attestations-file-path-unsafe") from error
    if parent == project or project in parent.parents:
        raise MultipleTestingAttestationError("attestations-file-path-unsafe")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise MultipleTestingAttestationError("attestations-file-unavailable") from error
    try:
        after = os.fstat(descriptor)
        if not stat.S_ISREG(after.st_mode) or (before.st_dev, before.st_ino) != (
            after.st_dev,
            after.st_ino,
        ):
            raise MultipleTestingAttestationError("attestations-file-path-unsafe")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65_536, MAX_ATTESTATION_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_ATTESTATION_BYTES:
                raise MultipleTestingAttestationError("attestations-file-outside-size-bound")
        final = os.fstat(descriptor)
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
            final.st_dev,
            final.st_ino,
            final.st_size,
            final.st_mtime_ns,
        ) or total != final.st_size:
            raise MultipleTestingAttestationError("attestations-file-path-unsafe")
    finally:
        os.close(descriptor)
    return parse_attestation_bytes(b"".join(chunks))


def parse_attestation_bytes(payload: bytes) -> LoadedAttestation:
    raw_digest = sha256_digest(payload)
    if len(payload) > MAX_ATTESTATION_BYTES:
        raise MultipleTestingAttestationError(
            "attestations-file-outside-size-bound", input_digest=raw_digest
        )
    try:
        text = payload.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise MultipleTestingAttestationError(
            "attestations-json-invalid", input_digest=raw_digest
        ) from error
    if not isinstance(value, dict):
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid", pointer="/", input_digest=raw_digest
        )
    _validate_envelope_shape(value, raw_digest)
    return LoadedAttestation(
        cast(dict[str, Any], value), payload, raw_digest, semantic_digest(value)
    )


def apply_attestation(
    loaded: LoadedAttestation,
    *,
    question: dict[str, Any],
    initial_concern: dict[str, Any],
    analysis_content: bytes,
    outcome_columns: tuple[str, ...],
    created_at: str,
) -> AttestationApplication:
    """Validate all bindings, then apply exactly one asymmetric answer."""

    entry = cast(dict[str, Any], loaded.value["answers"][0])
    extensions = question.get("extensions")
    if (
        question.get("status") != "open"
        or not isinstance(extensions, dict)
        or extensions.get("x-question-purpose") != QUESTION_PURPOSE
        or entry.get("question_id") != question.get("question_id")
    ):
        raise _binding_error(loaded, "attestations-question-not-open", "/answers/0/question_id")
    bindings = (
        (
            "source_snapshot_digest",
            "x-source-snapshot-digest",
            "attestations-snapshot-binding-mismatch",
        ),
        (
            "analysis_content_digest",
            "x-analysis-content-digest",
            "attestations-analysis-binding-mismatch",
        ),
        (
            "question_evidence_digest",
            "x-question-evidence-digest",
            "attestations-evidence-binding-mismatch",
        ),
        (
            "authority_binding_digest",
            "x-authority-binding-digest",
            "attestations-authority-binding-mismatch",
        ),
    )
    for input_key, extension_key, category in bindings:
        if entry.get(input_key) != extensions.get(extension_key):
            raise _binding_error(loaded, category, f"/answers/0/{input_key}")
    if entry["analysis_content_digest"] != sha256_digest(analysis_content):
        raise _binding_error(
            loaded, "attestations-analysis-binding-mismatch", "/answers/0/analysis_content_digest"
        )

    count = int(extensions["x-authorized-count"])
    claimed = entry["claimed_correction"]
    if entry["answer"] == COMPLETE_OPTION:
        _validate_claimed_correction(
            claimed,
            analysis_content=analysis_content,
            analysis_digest=str(entry["analysis_content_digest"]),
            authorized_count=count,
            loaded=loaded,
        )
    answer = _build_answer(
        entry,
        question=question,
        source_snapshot_digest=str(entry["source_snapshot_digest"]),
        loaded=loaded,
        created_at=created_at,
    )
    option = str(entry["answer"])
    updated_question = copy.deepcopy(question)
    updated_question["answer_ids"] = [answer["answer_id"]]
    guided: GuidedCoverageProof | None = None
    disclosure: dict[str, Any] | None = None
    concern: dict[str, Any] | None
    if option == INCOMPLETE_OPTION:
        updated_question["status"] = "answered"
        concern = _author_attested_concern(
            initial_concern,
            question=updated_question,
            answer=answer,
            created_at=created_at,
        )
        updated_question["linked_conditional_concern_ids"] = [concern["concern_id"]]
    elif option == UNKNOWN_OPTION:
        updated_question["status"] = "open"
        concern = copy.deepcopy(initial_concern)
    else:
        assert isinstance(claimed, dict)
        span = _source_span(cast(dict[str, Any], claimed["source_span"]))
        guided = existing_complete_coverage_recheck(
            analysis_content,
            source_span=span,
            authorized_count=count,
            outcome_columns=outcome_columns,
        )
        if guided.status == "complete":
            updated_question["status"] = "answered"
            updated_question["linked_conditional_concern_ids"] = []
            concern = None
        else:
            updated_question["status"] = "open"
            concern = _conflicted_concern(
                initial_concern,
                question=updated_question,
                answer=answer,
                proof=guided,
                created_at=created_at,
            )
            updated_question["linked_conditional_concern_ids"] = [concern["concern_id"]]
            disclosure = _unverified_disclosure(
                updated_question,
                answer=answer,
                proof=guided,
                created_at=created_at,
            )
    lock_receipt: dict[str, Any] = {
        "profile": ATTESTATION_PROFILE,
        "profile_version": ATTESTATION_PROFILE_VERSION,
        "raw_input_digest": loaded.raw_digest,
        "semantic_input_digest": loaded.semantic_digest,
        "question_id": question["question_id"],
        "answer_id": answer["answer_id"],
        "answer_digest": answer["answer_digest"],
        "route": option,
        "guided_proof": (
            {
                "status": guided.status,
                "corrected_positions": list(guided.corrected_positions),
                "proof_root_span": guided.proof_root_span.to_dict(),
                "proof_digest": guided.proof_digest,
                "failure_code": guided.failure_code,
                "answer_removal_equivalent": True,
            }
            if guided is not None
            else None
        ),
        "source_classification_changed": False,
    }
    lock_receipt["receipt_digest"] = semantic_digest(lock_receipt)
    return AttestationApplication(
        updated_question,
        concern,
        answer,
        disclosure,
        guided,
        lock_receipt,
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _validate_envelope_shape(value: dict[str, Any], digest: str) -> None:
    if set(value) != {"profile", "profile_version", "answers"}:
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid", pointer="/", input_digest=digest
        )
    if (
        value.get("profile") != ATTESTATION_PROFILE
        or value.get("profile_version") != ATTESTATION_PROFILE_VERSION
        or not isinstance(value.get("answers"), list)
    ):
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid", pointer="/", input_digest=digest
        )
    answers = cast(list[Any], value["answers"])
    if len(answers) != 1:
        raise MultipleTestingAttestationError(
            "attestations-answer-cardinality-invalid", pointer="/answers", input_digest=digest
        )
    _validate_entry_shape(answers[0], digest)


def _validate_entry_shape(value: Any, digest: str) -> None:
    required = {
        "question_id",
        "source_snapshot_digest",
        "analysis_content_digest",
        "question_evidence_digest",
        "authority_binding_digest",
        "answer",
        "respondent",
        "certainty",
        "timestamp_status",
        "supersedes_answer_digest",
        "claimed_correction",
    }
    if (
        not isinstance(value, dict)
        or set(value) - (required | {"answered_at"})
        or not required.issubset(value)
    ):
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid", pointer="/answers/0", input_digest=digest
        )
    if value["supersedes_answer_digest"] is not None:
        raise MultipleTestingAttestationError(
            "attestations-supersession-invalid",
            pointer="/answers/0/supersedes_answer_digest",
            input_digest=digest,
        )
    if value["answer"] not in _OPTIONS:
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid", pointer="/answers/0/answer", input_digest=digest
        )
    for key in (
        "question_id",
        "source_snapshot_digest",
        "analysis_content_digest",
        "question_evidence_digest",
        "authority_binding_digest",
    ):
        if not isinstance(value[key], str):
            raise MultipleTestingAttestationError(
                "attestations-schema-invalid", pointer=f"/answers/0/{key}", input_digest=digest
            )
        if key != "question_id" and not _is_sha256_digest(value[key]):
            raise MultipleTestingAttestationError(
                "attestations-schema-invalid", pointer=f"/answers/0/{key}", input_digest=digest
            )
    respondent = value["respondent"]
    if (
        not isinstance(respondent, dict)
        or set(respondent) - {"actor_kind", "actor_id", "display_name"}
        or set(respondent) < {"actor_kind", "actor_id"}
        or respondent.get("actor_kind") != "human"
        or not isinstance(respondent.get("actor_id"), str)
        or not respondent["actor_id"]
        or (
            "display_name" in respondent
            and (not isinstance(respondent["display_name"], str) or not respondent["display_name"])
        )
    ):
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid", pointer="/answers/0/respondent", input_digest=digest
        )
    if value.get("certainty") != {"level": "explicit", "basis": CERTAINTY_BASIS}:
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid", pointer="/answers/0/certainty", input_digest=digest
        )
    timestamp = value.get("timestamp_status")
    if timestamp not in {"available", "unavailable"}:
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid",
            pointer="/answers/0/timestamp_status",
            input_digest=digest,
        )
    if (timestamp == "available") != ("answered_at" in value):
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid", pointer="/answers/0/answered_at", input_digest=digest
        )
    if "answered_at" in value:
        answered_at = value["answered_at"]
        try:
            parsed = (
                datetime.fromisoformat(answered_at.replace("Z", "+00:00"))
                if isinstance(answered_at, str)
                else None
            )
        except ValueError:
            parsed = None
        if parsed is None or parsed.tzinfo is None:
            raise MultipleTestingAttestationError(
                "attestations-schema-invalid",
                pointer="/answers/0/answered_at",
                input_digest=digest,
            )
    complete = value["answer"] == COMPLETE_OPTION
    if complete != isinstance(value["claimed_correction"], dict):
        raise MultipleTestingAttestationError(
            "attestations-schema-invalid",
            pointer="/answers/0/claimed_correction",
            input_digest=digest,
        )


def _validate_claimed_correction(
    value: Any,
    *,
    analysis_content: bytes,
    analysis_digest: str,
    authorized_count: int,
    loaded: LoadedAttestation,
) -> None:
    required = {"path", "analysis_content_digest", "source_span", "factor"}
    if not isinstance(value, dict) or set(value) != required:
        raise _claim_error(loaded, "/answers/0/claimed_correction")
    if (
        value.get("path") != "analysis.py"
        or value.get("analysis_content_digest") != analysis_digest
        or not _is_sha256_digest(value.get("analysis_content_digest"))
    ):
        raise _claim_error(loaded, "/answers/0/claimed_correction/path")
    factor = value.get("factor")
    if not isinstance(factor, dict) or set(factor) != {"kind", "value", "source_span"}:
        raise _claim_error(loaded, "/answers/0/claimed_correction/factor")
    if (
        factor.get("kind") not in _FACTOR_KINDS
        or not isinstance(factor.get("value"), int)
        or isinstance(factor.get("value"), bool)
        or not 1 <= factor["value"] <= authorized_count
    ):
        raise _claim_error(loaded, "/answers/0/claimed_correction/factor")
    correction_span = _source_span_or_error(value.get("source_span"), loaded)
    factor_span = _source_span_or_error(factor.get("source_span"), loaded)
    try:
        text = analysis_content.decode("utf-8", errors="strict")
        tree = ast.parse(text, filename="analysis.py", mode="exec", type_comments=True)
    except (UnicodeError, SyntaxError) as error:
        raise _claim_error(loaded, "/answers/0/claimed_correction/source_span") from error
    positioned = [node for node in ast.walk(tree) if hasattr(node, "lineno")]
    correction_nodes = [node for node in positioned if _ast_span(node, text) == correction_span]
    factor_nodes = [node for node in positioned if _ast_span(node, text) == factor_span]
    if (
        len(correction_nodes) != 1
        or not isinstance(correction_nodes[0], ast.expr)
        or len(factor_nodes) != 1
        or not isinstance(factor_nodes[0], ast.expr)
    ):
        raise _claim_error(loaded, "/answers/0/claimed_correction/source_span")
    if factor["kind"] == "contract_family_size" and factor["value"] != authorized_count:
        raise _claim_error(loaded, "/answers/0/claimed_correction/factor/value")
    if not _factor_pointer_matches(
        factor_nodes[0],
        kind=str(factor["kind"]),
        value=int(factor["value"]),
        correction_node=correction_nodes[0],
        tree=tree,
    ):
        raise _claim_error(loaded, "/answers/0/claimed_correction/factor/source_span")


def _factor_pointer_matches(
    node: ast.expr,
    *,
    kind: str,
    value: int,
    correction_node: ast.expr,
    tree: ast.Module,
) -> bool:
    if kind == "correction_input_count":
        if node is not correction_node or not isinstance(node, ast.Call):
            return False
        terminal = _callee_terminal(node.func)
        return terminal in {
            "multipletests",
            "fdrcorrection",
            "false_discovery_control",
            "benjamini_hochberg",
            "multicomp",
            "fdr_correction",
            "p_adjust",
            "padjust",
            "bonferroni",
            "holm",
            "sidak",
        }
    resolved = _static_factor_value(node, tree)
    if resolved != value:
        return False
    if kind == "literal_multiplier":
        return isinstance(node, ast.Constant)
    if kind == "resolved_constant_integer":
        return isinstance(node, ast.Name)
    if kind == "contract_family_size":
        return isinstance(node, (ast.Name, ast.Call))
    if kind == "threshold_divisor":
        return isinstance(node, (ast.Constant, ast.Name, ast.Call))
    return False


def _static_factor_value(node: ast.expr, tree: ast.Module) -> int | None:
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value > 0
    ):
        return node.value
    if isinstance(node, ast.Name):
        bindings = [
            statement.value
            for statement in ast.walk(tree)
            if isinstance(statement, (ast.Assign, ast.AnnAssign))
            and statement.value is not None
            and any(
                isinstance(target, ast.Name) and target.id == node.id
                for target in (
                    statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                )
            )
        ]
        if len(bindings) == 1:
            return _static_factor_value(bindings[0], tree)
        return None
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "len"
        and len(node.args) == 1
        and not node.keywords
    ):
        sequence = node.args[0]
        if isinstance(sequence, ast.Name):
            assignments = [
                statement.value
                for statement in ast.walk(tree)
                if isinstance(statement, (ast.Assign, ast.AnnAssign))
                and statement.value is not None
                and any(
                    isinstance(target, ast.Name) and target.id == sequence.id
                    for target in (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                )
            ]
            if len(assignments) == 1:
                sequence = assignments[0]
        if isinstance(sequence, (ast.List, ast.Tuple, ast.Set)):
            return len(sequence.elts)
    return None


def _callee_terminal(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id.lower()
    if isinstance(node, ast.Attribute):
        return node.attr.lower()
    return None


def _is_sha256_digest(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _build_answer(
    entry: dict[str, Any],
    *,
    question: dict[str, Any],
    source_snapshot_digest: str,
    loaded: LoadedAttestation,
    created_at: str,
) -> dict[str, Any]:
    option_id = str(entry["answer"])
    option = next(item for item in question["candidate_answers"] if item["answer_id"] == option_id)
    claimed_digest = (
        semantic_digest(entry["claimed_correction"])
        if entry["claimed_correction"] is not None
        else None
    )
    identity = {
        "question_id": question["question_id"],
        "selected_option_id": option_id,
        "answer_value": option["value"],
        "respondent_actor_id": entry["respondent"]["actor_id"],
        "timestamp_status": entry["timestamp_status"],
        "answered_at": entry.get("answered_at"),
        "claimed_correction_digest": claimed_digest,
        "source_snapshot_digest": source_snapshot_digest,
        "analysis_content_digest": entry["analysis_content_digest"],
        "question_evidence_digest": entry["question_evidence_digest"],
        "authority_binding_digest": entry["authority_binding_digest"],
    }
    answer_id = f"answer:multiple-testing-correction-scope:{semantic_digest(identity)[7:31]}"
    answer: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "answer",
        "answer_id": answer_id,
        "audit_run_id": question["audit_run_id"],
        "question_ref": typed_ref("material_question", str(question["question_id"])),
        "source_snapshot_digest": source_snapshot_digest,
        "answer_kind": "unknown" if option_id == UNKNOWN_OPTION else "candidate_selection",
        "answer_value": copy.deepcopy(option["value"]),
        "selected_option_id": option_id,
        "respondent": copy.deepcopy(entry["respondent"]),
        "response_source": "provided_answer_file",
        "authority_scope": {
            "authority_kind": "reported_intent",
            "subject_refs": [
                typed_ref("material_question", str(question["question_id"])),
                copy.deepcopy(question["extensions"]["x-analysis-subject-ref"]),
            ],
            "semantic_dimensions": [QUESTION_PURPOSE],
        },
        "certainty": copy.deepcopy(entry["certainty"]),
        "timestamp_status": entry["timestamp_status"],
        "supersedes_answer_refs": [],
        "answer_digest_profile": ANSWER_DIGEST_PROFILE,
        "created_at": created_at,
        "provenance": {
            "actor": copy.deepcopy(entry["respondent"]),
            "method": "scientist_answer",
            "created_at": created_at,
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "extensions": {
            "x-attestation-profile": ATTESTATION_PROFILE,
            "x-attestation-profile-version": ATTESTATION_PROFILE_VERSION,
            "x-attestation-raw-input-digest": loaded.raw_digest,
            "x-attestation-semantic-input-digest": loaded.semantic_digest,
            "x-question-evidence-digest": entry["question_evidence_digest"],
            "x-analysis-content-digest": entry["analysis_content_digest"],
            "x-authority-binding-digest": entry["authority_binding_digest"],
            "x-claimed-correction-digest": claimed_digest,
        },
    }
    if entry["timestamp_status"] == "available":
        answer["answered_at"] = entry["answered_at"]
    answer["answer_digest"] = semantic_digest(answer)
    return answer


def _author_attested_concern(
    base: dict[str, Any],
    *,
    question: dict[str, Any],
    answer: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    count = int(question["extensions"]["x-authorized-count"])
    value = copy.deepcopy(base)
    value["concern_id"] = (
        "conditional-concern:multiple-testing-correction-scope-author-attested:"
        f"{semantic_digest({'question': question['question_id'], 'answer': answer['answer_digest']})[7:31]}"
    )
    value["title"] = (
        f"Author attests that the located correction does not cover all {count} declared outcomes."
    )
    statement = (
        "If the bound author attestation accurately describes this source snapshot, the "
        "declared family has incomplete multiple-testing correction."
    )
    value["conditional_statement"] = statement
    value["condition"] = {
        "premise_id": f"premise:author-attestation:{answer['answer_id'].rsplit(':', 1)[-1]}",
        "premise_state": "unknown",
        "if_true": statement,
    }
    value["next_evidence_needed"] = [
        "Inspect a corrected source revision or independently prove the correction-position flow before admitting any tool Finding."
    ]
    value["created_at"] = created_at
    value["provenance"] = controller_provenance("author_attestation_projection", created_at)
    value["extensions"] = {
        "x-report-label": "Author attestation — not a tool Finding",
        "x-basis": "author_attestation",
        "x-attestation-class": "admission-against-interest",
        "x-author-attested-misstep": True,
        "x-answer-digest": answer["answer_digest"],
        "x-analysis-content-digest": answer["extensions"]["x-analysis-content-digest"],
        "x-question-evidence-digest": answer["extensions"]["x-question-evidence-digest"],
        "x-authority-binding-digest": answer["extensions"]["x-authority-binding-digest"],
    }
    return value


def _conflicted_concern(
    base: dict[str, Any],
    *,
    question: dict[str, Any],
    answer: dict[str, Any],
    proof: GuidedCoverageProof,
    created_at: str,
) -> dict[str, Any]:
    value = copy.deepcopy(base)
    suffix = semantic_digest(
        {
            "question": question["question_id"],
            "answer": answer["answer_digest"],
            "proof": proof.proof_digest,
        }
    )[7:31]
    value["concern_id"] = (
        f"conditional-concern:multiple-testing-correction-scope-conflicted:{suffix}"
    )
    value["condition"]["premise_state"] = "conflicted"
    value["created_at"] = created_at
    value["provenance"] = controller_provenance(
        "answer_guided_multiple_testing_scope_recheck_v1", created_at
    )
    value["extensions"] = {
        "x-question-purpose": QUESTION_PURPOSE,
        "x-assessment-separation": "conditional-concern-not-finding",
        "x-author-attests-complete": True,
        "x-answer-digest": answer["answer_digest"],
        "x-recheck-digest": proof.proof_digest,
    }
    return value


def _unverified_disclosure(
    question: dict[str, Any],
    *,
    answer: dict[str, Any],
    proof: GuidedCoverageProof,
    created_at: str,
) -> dict[str, Any]:
    count = int(question["extensions"]["x-authorized-count"])
    span = cast(dict[str, int], question["extensions"]["x-source-span"])
    location = f"analysis.py:{span['start_line']}:{span['start_column']}"
    suffix = semantic_digest(
        {
            "question": question["question_id"],
            "answer": answer["answer_digest"],
            "proof": proof.proof_digest,
        }
    )[7:31]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "disclosure",
        "disclosure_id": f"disclosure:multiple-testing-correction-scope-unverified:{suffix}",
        "audit_run_id": question["audit_run_id"],
        "disclosure_kind": "detector_gap",
        "title": "Author attests complete correction; structural coverage remains unverified",
        "description": (
            f"The author attests that the correction at {location} covers all {count} declared "
            "outcomes, but the bounded structural recheck did not prove complete coverage."
        ),
        "importance": "important",
        "non_accusatory": True,
        "affected_refs": [
            typed_ref("material_question", str(question["question_id"])),
            typed_ref("answer", str(answer["answer_id"])),
            copy.deepcopy(question["extensions"]["x-analysis-subject-ref"]),
            typed_ref("detector_result", str(question["extensions"]["x-detector-result-id"])),
        ],
        "source_refs": [],
        "coverage_status": "unknown",
        "interpretive_consequence": (
            "Complete-family correction remains unverified; no Finding or clearance follows "
            "from the attestation."
        ),
        "next_step": (
            "Make the claimed correction and every corrected conclusion structurally "
            "inspectable, or leave the question open."
        ),
        "created_at": created_at,
        "provenance": controller_provenance(
            "answer_guided_multiple_testing_scope_recheck_v1", created_at
        ),
        "extensions": {
            "x-question-purpose": QUESTION_PURPOSE,
            "x-recheck-failure-code": proof.failure_code,
            "x-recheck-digest": proof.proof_digest,
            "x-answer-digest": answer["answer_digest"],
            "x-author-attests-complete": True,
            "x-analysis-content-digest": answer["extensions"]["x-analysis-content-digest"],
            "x-question-evidence-digest": answer["extensions"]["x-question-evidence-digest"],
            "x-authority-binding-digest": answer["extensions"]["x-authority-binding-digest"],
        },
    }


def _source_span(value: dict[str, Any]) -> SourceSpan:
    return SourceSpan(
        int(value["start_line"]),
        int(value["start_column"]),
        int(value["end_line"]),
        int(value["end_column"]),
    )


def _source_span_or_error(value: Any, loaded: LoadedAttestation) -> SourceSpan:
    if not isinstance(value, dict) or set(value) != {
        "start_line",
        "start_column",
        "end_line",
        "end_column",
    }:
        raise _claim_error(loaded, "/answers/0/claimed_correction/source_span")
    if any(not isinstance(item, int) or isinstance(item, bool) for item in value.values()):
        raise _claim_error(loaded, "/answers/0/claimed_correction/source_span")
    try:
        return _source_span(value)
    except ValueError as error:
        raise _claim_error(loaded, "/answers/0/claimed_correction/source_span") from error


def _ast_span(node: ast.AST, text: str) -> SourceSpan:
    lines = text.splitlines()
    positioned = cast(Any, node)
    start_line = int(positioned.lineno)
    end_line = int(positioned.end_lineno)
    start_prefix = lines[start_line - 1].encode("utf-8")[: int(positioned.col_offset)]
    end_prefix = lines[end_line - 1].encode("utf-8")[: int(positioned.end_col_offset)]
    return SourceSpan(
        start_line,
        len(start_prefix.decode("utf-8", errors="strict")) + 1,
        end_line,
        len(end_prefix.decode("utf-8", errors="strict")) + 1,
    )


def _binding_error(
    loaded: LoadedAttestation, category: str, pointer: str
) -> MultipleTestingAttestationError:
    return MultipleTestingAttestationError(
        category, pointer=pointer, input_digest=loaded.raw_digest
    )


def _claim_error(loaded: LoadedAttestation, pointer: str) -> MultipleTestingAttestationError:
    return _binding_error(loaded, "attestations-claimed-correction-invalid", pointer)


__all__ = [
    "ANSWER_DIGEST_PROFILE",
    "ATTESTATION_PROFILE",
    "ATTESTATION_PROFILE_VERSION",
    "COMPLETE_OPTION",
    "INCOMPLETE_OPTION",
    "UNKNOWN_OPTION",
    "AttestationApplication",
    "LoadedAttestation",
    "MultipleTestingAttestationError",
    "apply_attestation",
    "load_attestation_file",
    "parse_attestation_bytes",
]
