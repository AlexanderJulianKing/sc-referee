from __future__ import annotations

import json
import stat
import unicodedata
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest


class ProspectiveSubmissionIngestionError(ValueError):
    """A prospective author submission is incomplete, changed, or unsafe to seal."""


SEAL_VERSION = "1.0.0"
MAX_CASES = 140
MAX_FILES_PER_CASE = 5
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_JSON_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
MAX_RELATIVE_PATH_BYTES = 512

_QUEUE_KEYS = {
    "artifact_kind",
    "scaffold_version",
    "protocol_ref",
    "author_id",
    "briefs",
    "distribution_rule",
    "qualification_authority",
    "queue_digest",
}
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
_SUBMISSION_KEYS = {
    "opaque_case_id",
    "assignment_token",
    "execution_context_id",
    "authored_at",
    "selected_report_path",
    "source_path",
    "data_dictionary_path",
}
_SELECTED_PATH_FIELDS = {
    "selected_report_path": "REPORT.md",
    "source_path": "analysis.py",
    "data_dictionary_path": "DATA_DICTIONARY.md",
}
_CHANGE_NOTE_PATH = "COORDINATOR_CHANGE_NOTE.md"
_SUPPORTED_CELL_TYPES = {
    "error_bearing",
    "corrected_twin",
    "valid_alternative",
    "hard_negative",
    "ambiguous",
    "unsupported",
    "renamed_implementation",
}


def build_prospective_submission_seal(
    author_queue: Mapping[str, Any],
    submission_root: Path,
    *,
    expected_queue_digest: str,
    author_execution_context_id: str,
    sealed_at: str,
) -> dict[str, bytes]:
    """Validate and snapshot one complete author queue without executing submitted code.

    This boundary checks assignment identity, chronology, paths, and bytes only. It does not assess
    the scientific meaning of a case, decide its intended cell, run a detector, create a Finding,
    or make a qualification decision.
    """

    queue, briefs = _validate_queue(author_queue, expected_queue_digest)
    context_id = _single_line(author_execution_context_id, "author_execution_context_id")
    sealed_timestamp = _timestamp(sealed_at, "sealed_at")
    root = _validate_submission_root(submission_root)
    expected_case_ids = set(briefs)
    expected_directories = {case_id.removeprefix("case:") for case_id in expected_case_ids}
    actual_entries = list(root.iterdir())
    actual_directories = {entry.name for entry in actual_entries}
    if (
        actual_directories != expected_directories
        or len(actual_directories) != len(actual_entries)
        or any(entry.is_symlink() or not entry.is_dir() for entry in actual_entries)
    ):
        raise ProspectiveSubmissionIngestionError(
            "Submission root case directories differ from the frozen queue; "
            f"missing={sorted(expected_directories - actual_directories)}, "
            f"extra={sorted(actual_directories - expected_directories)}."
        )

    queue_bytes = (canonical_json(queue) + "\n").encode("utf-8")
    output_files: dict[str, bytes] = {"SOURCE_QUEUE.json": queue_bytes}
    total_bytes = len(queue_bytes)
    case_records: list[dict[str, Any]] = []
    for case_id in sorted(expected_case_ids):
        brief = briefs[case_id]
        case_token = case_id.removeprefix("case:")
        case_root = root / case_token
        submission_path = case_root / "SUBMISSION.json"
        submission_bytes = _read_regular_bytes(
            submission_path, label=f"{case_id} SUBMISSION.json", limit=MAX_JSON_BYTES
        )
        submission = _parse_json_object(submission_bytes, label=f"{case_id} SUBMISSION.json")
        selected_paths = _validate_submission(
            submission,
            brief=brief,
            author_execution_context_id=context_id,
            sealed_at=sealed_timestamp,
        )
        actual_files, nested_directories = _inventory_case_tree(case_root)
        expected_files = selected_paths | {"SUBMISSION.json"}
        if actual_files != expected_files:
            raise ProspectiveSubmissionIngestionError(
                f"{case_id} file inventory differs from the frozen delivery protocol; "
                f"unlisted={sorted(actual_files - expected_files)}, "
                f"missing={sorted(expected_files - actual_files)}."
            )
        if nested_directories:
            raise ProspectiveSubmissionIngestionError(
                f"{case_id} directory inventory must not contain nested directories."
            )

        sealed_root = f"cases/{case_token}"
        file_records: list[dict[str, Any]] = []
        all_case_payloads: dict[str, bytes] = {"SUBMISSION.json": submission_bytes}
        for relative in sorted(selected_paths):
            payload = _read_regular_bytes(
                case_root / relative,
                label=f"{case_id} selected file {relative!r}",
                limit=MAX_FILE_BYTES,
            )
            all_case_payloads[relative] = payload

        for relative, payload in sorted(all_case_payloads.items()):
            sealed_path = f"{sealed_root}/{relative}"
            _put(output_files, sealed_path, payload)
            total_bytes += len(payload)
            if total_bytes > MAX_TOTAL_BYTES:
                raise ProspectiveSubmissionIngestionError(
                    f"Accepted bytes exceed the {MAX_TOTAL_BYTES}-byte ingestion bound."
                )
            file_records.append(
                {
                    "source_path": relative,
                    "sealed_path": sealed_path,
                    "sha256": sha256_digest(payload),
                    "size_bytes": len(payload),
                }
            )
        case_records.append(
            {
                "opaque_case_id": case_id,
                "assignment_token": submission["assignment_token"],
                "execution_context_id": submission["execution_context_id"],
                "authored_at": submission["authored_at"],
                "files": file_records,
            }
        )

    manifest = _self_digest(
        {
            "artifact_kind": "prospective_author_submission_seal",
            "seal_version": SEAL_VERSION,
            "protocol_ref": deepcopy(queue["protocol_ref"]),
            "source_queue": {
                "queue_digest": queue["queue_digest"],
                "sealed_path": "SOURCE_QUEUE.json",
                "sha256": sha256_digest(queue_bytes),
                "size_bytes": len(queue_bytes),
            },
            "author_id": queue["author_id"],
            "author_execution_context_id": context_id,
            "sealed_at": sealed_at,
            "case_count": len(case_records),
            "cases": case_records,
            "limits": {
                "maximum_cases": MAX_CASES,
                "maximum_files_per_case": MAX_FILES_PER_CASE,
                "maximum_file_bytes": MAX_FILE_BYTES,
                "maximum_total_bytes": MAX_TOTAL_BYTES,
            },
            "epistemic_boundary": {
                "ingestion_only": True,
                "project_authored_code_executed": False,
                "scientific_review_performed": False,
                "scientific_labels_created": False,
                "detector_output_created": False,
                "findings_created": False,
                "qualification_decision_created": False,
            },
            "qualification_authority": "none_submission_seal_only",
        },
        "manifest_digest",
    )
    _put(
        output_files,
        "SEAL_MANIFEST.json",
        (canonical_json(manifest) + "\n").encode("utf-8"),
    )
    return dict(sorted(output_files.items()))


def write_prospective_submission_seal_once(output_root: Path, files: Mapping[str, bytes]) -> Path:
    """Write a validated seal beneath one absent destination without overwriting bytes."""

    if output_root.is_symlink() or output_root.exists():
        raise ProspectiveSubmissionIngestionError(f"Output already exists: {output_root}")
    destination = output_root.resolve()
    checked: list[tuple[PurePosixPath, bytes]] = []
    for relative, payload in files.items():
        path = _safe_relative_path(relative)
        if not isinstance(payload, bytes):
            raise ProspectiveSubmissionIngestionError(
                f"Generated payload is not bytes: {relative!r}."
            )
        checked.append((path, payload))
    destination.mkdir(parents=True)
    for checked_path, payload in checked:
        target = destination.joinpath(*checked_path.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        target.chmod(0o444)
    return destination


def load_canonical_json_object(path: Path, *, label: str) -> dict[str, Any]:
    """Load one bounded canonical JSON object from a non-symlink regular file."""

    payload = _read_regular_bytes(path, label=label, limit=MAX_JSON_BYTES)
    value = _parse_json_object(payload, label=label)
    if payload != (canonical_json(value) + "\n").encode("utf-8"):
        raise ProspectiveSubmissionIngestionError(f"{label} must be canonical JSON plus newline.")
    return value


def _parse_json_object(payload: bytes, *, label: str) -> dict[str, Any]:
    """Parse strict JSON while preserving the caller's original bytes for sealing."""

    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProspectiveSubmissionIngestionError(f"Malformed JSON in {label}.") from error
    if not isinstance(value, dict):
        raise ProspectiveSubmissionIngestionError(f"{label} must contain one JSON object.")
    return value


def _validate_queue(
    value: Mapping[str, Any], expected_queue_digest: str
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    queue = deepcopy(dict(value))
    _exact_keys(queue, _QUEUE_KEYS, "author queue")
    declared = _single_line(queue.pop("queue_digest"), "queue_digest")
    if declared != semantic_digest(queue):
        raise ProspectiveSubmissionIngestionError("Author queue digest does not replay.")
    if declared != _single_line(expected_queue_digest, "expected_queue_digest"):
        raise ProspectiveSubmissionIngestionError(
            "Author queue differs from the expected frozen queue digest."
        )
    queue["queue_digest"] = declared
    if (
        queue.get("artifact_kind") != "prospective_author_queue"
        or queue.get("scaffold_version") != "1.0.0"
        or queue.get("distribution_rule")
        != "deliver_only_to_named_author_in_named_execution_context"
        or queue.get("qualification_authority") != "none_author_queue_only"
    ):
        raise ProspectiveSubmissionIngestionError("Unsupported prospective author queue.")
    _single_line(queue.get("author_id"), "queue author_id")
    protocol_ref = _mapping(queue.get("protocol_ref"), "protocol_ref")
    _exact_keys(protocol_ref, {"protocol_id", "protocol_digest"}, "protocol_ref")
    _single_line(protocol_ref.get("protocol_id"), "protocol_id")
    _digest(protocol_ref.get("protocol_digest"), "protocol_digest")

    raw_briefs = _sequence(queue.get("briefs"), "queue briefs")
    if not 1 <= len(raw_briefs) <= MAX_CASES:
        raise ProspectiveSubmissionIngestionError(
            f"Author queue must contain between 1 and {MAX_CASES} briefs."
        )
    briefs: dict[str, dict[str, Any]] = {}
    tokens: set[str] = set()
    portable_ids: set[str] = set()
    for raw in raw_briefs:
        brief = _mapping(raw, "authoring brief")
        _exact_keys(brief, _BRIEF_KEYS, "authoring brief")
        brief_digest = _single_line(brief.pop("brief_digest"), "brief_digest")
        if brief_digest != semantic_digest(brief):
            raise ProspectiveSubmissionIngestionError("Authoring brief digest does not replay.")
        brief["brief_digest"] = brief_digest
        if (
            brief.get("artifact_kind") != "prospective_case_authoring_brief"
            or brief.get("scaffold_version") != "1.0.0"
            or brief.get("qualification_authority") != "none_authoring_instruction_only"
        ):
            raise ProspectiveSubmissionIngestionError("Unsupported prospective authoring brief.")
        case_id = _safe_case_id(brief.get("opaque_case_id"))
        portable_id = unicodedata.normalize("NFC", case_id).casefold()
        token = _single_line(
            brief.get("block_neutral_assignment_token"), "block_neutral_assignment_token"
        )
        if case_id in briefs or portable_id in portable_ids or token in tokens:
            raise ProspectiveSubmissionIngestionError(
                "Author queue case identities and assignment tokens must be unique."
            )
        cell_brief = _mapping(brief.get("one_cell_brief"), "one_cell_brief")
        if cell_brief.get("cell_type") not in _SUPPORTED_CELL_TYPES:
            raise ProspectiveSubmissionIngestionError("Unsupported authoring cell type.")
        _timestamp(
            _single_line(brief.get("submission_deadline"), "submission_deadline"),
            "submission_deadline",
        )
        briefs[case_id] = brief
        tokens.add(token)
        portable_ids.add(portable_id)
    return queue, briefs


def _validate_submission(
    value: Mapping[str, Any],
    *,
    brief: Mapping[str, Any],
    author_execution_context_id: str,
    sealed_at: datetime,
) -> set[str]:
    submission = deepcopy(dict(value))
    _exact_keys(submission, _SUBMISSION_KEYS, "SUBMISSION.json")
    if submission.get("opaque_case_id") != brief["opaque_case_id"]:
        raise ProspectiveSubmissionIngestionError("SUBMISSION.json case identity differs.")
    if submission.get("assignment_token") != brief["block_neutral_assignment_token"]:
        raise ProspectiveSubmissionIngestionError("SUBMISSION.json assignment token differs.")
    if submission.get("execution_context_id") != author_execution_context_id:
        raise ProspectiveSubmissionIngestionError(
            "SUBMISSION.json differs from the supplied author execution context."
        )
    authored = _timestamp(_single_line(submission.get("authored_at"), "authored_at"), "authored_at")
    deadline = _timestamp(str(brief["submission_deadline"]), "submission_deadline")
    if authored > sealed_at:
        raise ProspectiveSubmissionIngestionError(
            "Submission timestamps must satisfy authored_at <= sealed_at."
        )
    if sealed_at > deadline:
        raise ProspectiveSubmissionIngestionError(
            "Coordinator seal timestamp is later than the frozen submission deadline."
        )

    selected_paths: set[str] = set()
    for field, required_path in _SELECTED_PATH_FIELDS.items():
        selected = _safe_relative_path(_single_line(submission.get(field), field)).as_posix()
        if selected != required_path:
            raise ProspectiveSubmissionIngestionError(
                f"{field} must be the frozen root path {required_path!r}."
            )
        selected_paths.add(selected)
    cell_type = _mapping(brief["one_cell_brief"], "one_cell_brief")["cell_type"]
    if cell_type == "corrected_twin":
        selected_paths.add(_CHANGE_NOTE_PATH)
    return selected_paths


def _validate_submission_root(path: Path) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise ProspectiveSubmissionIngestionError(
            "Submission root must be one existing non-symlink directory."
        )
    return path.resolve()


def _inventory_case_tree(root: Path) -> tuple[set[str], set[str]]:
    files: set[str] = set()
    directories: set[str] = set()
    pending = [root]
    while pending:
        directory = pending.pop()
        for entry in directory.iterdir():
            relative = entry.relative_to(root).as_posix()
            mode = entry.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ProspectiveSubmissionIngestionError(
                    f"Case tree contains a symlink: {relative!r}."
                )
            if stat.S_ISDIR(mode):
                _safe_relative_path(relative)
                directories.add(relative)
                pending.append(entry)
            elif stat.S_ISREG(mode):
                _safe_relative_path(relative)
                files.add(relative)
            else:
                raise ProspectiveSubmissionIngestionError(
                    f"Case tree contains a non-regular entry: {relative!r}."
                )
    return files, directories


def _read_regular_bytes(path: Path, *, label: str, limit: int) -> bytes:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError as error:
        raise ProspectiveSubmissionIngestionError(f"Missing required file: {label}.") from error
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise ProspectiveSubmissionIngestionError(f"{label} must be a non-symlink regular file.")
    size = path.stat(follow_symlinks=False).st_size
    if size > limit:
        raise ProspectiveSubmissionIngestionError(f"{label} exceeds the {limit}-byte bound.")
    payload = path.read_bytes()
    if len(payload) != size:
        raise ProspectiveSubmissionIngestionError(f"{label} changed while it was read.")
    return payload


def _safe_case_id(value: Any) -> str:
    case_id = _single_line(value, "opaque_case_id")
    suffix = case_id.removeprefix("case:")
    if (
        not case_id.startswith("case:")
        or len(suffix) != 20
        or any(character not in "0123456789abcdef" for character in suffix)
    ):
        raise ProspectiveSubmissionIngestionError("opaque_case_id has an unsupported form.")
    return case_id


def _safe_relative_path(value: str) -> PurePosixPath:
    if "\\" in value or len(value.encode("utf-8")) > MAX_RELATIVE_PATH_BYTES:
        raise ProspectiveSubmissionIngestionError(f"Unsafe selected path: {value!r}.")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
        or unicodedata.normalize("NFC", value) != value
    ):
        raise ProspectiveSubmissionIngestionError(f"Unsafe selected path: {value!r}.")
    return path


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProspectiveSubmissionIngestionError(f"Duplicate JSON key: {key!r}.")
        result[key] = value
    return result


def _self_digest(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = semantic_digest(result)
    return result


def _put(files: dict[str, bytes], relative: str, payload: bytes) -> None:
    _safe_relative_path(relative)
    if relative in files:
        raise ProspectiveSubmissionIngestionError(f"Duplicate sealed path: {relative!r}.")
    files[relative] = payload


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ProspectiveSubmissionIngestionError(
            f"{label} keys differ; missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}."
        )


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProspectiveSubmissionIngestionError(f"{label} must be an object.")
    return dict(value)


def _sequence(value: Any, label: str) -> list[Any]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise ProspectiveSubmissionIngestionError(f"{label} must be an array.")
    return list(value)


def _single_line(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
        raise ProspectiveSubmissionIngestionError(f"{label} must be a nonempty single-line string.")
    return value


def _digest(value: Any, label: str) -> str:
    digest = _single_line(value, label)
    if len(digest) != 71 or not digest.startswith("sha256:"):
        raise ProspectiveSubmissionIngestionError(f"{label} must be a sha256 digest.")
    hexadecimal = digest.removeprefix("sha256:")
    if any(character not in "0123456789abcdef" for character in hexadecimal):
        raise ProspectiveSubmissionIngestionError(f"{label} must be a sha256 digest.")
    return digest


def _timestamp(value: str, label: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ProspectiveSubmissionIngestionError(
            f"{label} must be an ISO-8601 timestamp."
        ) from error
    if result.tzinfo is None or result.utcoffset() is None:
        raise ProspectiveSubmissionIngestionError(f"{label} must include a timezone.")
    return result
