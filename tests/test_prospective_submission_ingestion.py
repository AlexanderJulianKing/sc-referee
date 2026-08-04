from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.prospective_submission_ingestion import (
    ProspectiveSubmissionIngestionError,
    build_prospective_submission_seal,
    load_canonical_json_object,
    write_prospective_submission_seal_once,
)

from sc_referee.core.ids import semantic_digest, sha256_digest

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_ID = "context:isolated-author-a"


def test_standalone_submission_sealer_cli_bootstraps_checkout_imports() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "seal_prospective_author_submissions.py"),
            "--help",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "--expected-queue-digest" in completed.stdout
    assert "--author-execution-context-id" in completed.stdout


def _self_digest(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = deepcopy(value)
    result[field] = semantic_digest(result)
    return result


def _brief(case_id: str, token: str, cell_type: str) -> dict[str, Any]:
    return _self_digest(
        {
            "artifact_kind": "prospective_case_authoring_brief",
            "scaffold_version": "1.0.0",
            "opaque_case_id": case_id,
            "block_neutral_assignment_token": token,
            "one_relation_brief": {"governed_premise": "Use the assigned primary method."},
            "one_cell_brief": {"cell_type": cell_type, "author_task": "Author the case."},
            "paired_case_access": {"reference_case_id": None, "access_rule": "none"},
            "neutral_repository_deliverables": ["a small repository"],
            "submission_deadline": "2026-08-05T12:00:00Z",
            "submission_channel": "channel:opaque-a",
            "quality_constraints": ["scientifically plausible"],
            "information_barrier": ["do not inspect detector source"],
            "qualification_authority": "none_authoring_instruction_only",
        },
        "brief_digest",
    )


def _queue() -> dict[str, Any]:
    return _self_digest(
        {
            "artifact_kind": "prospective_author_queue",
            "scaffold_version": "1.0.0",
            "protocol_ref": {
                "protocol_id": "prospective-protocol:test-v1",
                "protocol_digest": sha256_digest("protocol"),
            },
            "author_id": "actor:author-a",
            "briefs": [
                _brief(
                    "case:0123456789abcdefabcd",
                    "assignment:000000000000000000000001",
                    "error_bearing",
                ),
                _brief(
                    "case:fedcba9876543210abcd",
                    "assignment:000000000000000000000002",
                    "corrected_twin",
                ),
            ],
            "distribution_rule": "deliver_only_to_named_author_in_named_execution_context",
            "qualification_authority": "none_author_queue_only",
        },
        "queue_digest",
    )


def _write_case(
    root: Path,
    *,
    case_id: str,
    token: str,
    corrected: bool,
    context_id: str = CONTEXT_ID,
    authored_at: str = "2026-08-05T09:00:00Z",
) -> None:
    case = root / case_id.removeprefix("case:")
    case.mkdir(parents=True)
    payloads = {
        "REPORT.md": b"# Report\n\nPrimary analysis description.\n",
        "analysis.py": b"METHOD = 'declared'\n",
        "DATA_DICTIONARY.md": b"# Data dictionary\n\n`value`: synthetic measurement.\n",
    }
    if corrected:
        payloads["COORDINATOR_CHANGE_NOTE.md"] = b"Only the assigned method relation changed.\n"
    for relative, payload in payloads.items():
        (case / relative).write_bytes(payload)
    submission = {
        "opaque_case_id": case_id,
        "assignment_token": token,
        "execution_context_id": context_id,
        "authored_at": authored_at,
        "selected_report_path": "REPORT.md",
        "source_path": "analysis.py",
        "data_dictionary_path": "DATA_DICTIONARY.md",
    }
    (case / "SUBMISSION.json").write_text(json.dumps(submission, indent=2) + "\n", encoding="utf-8")


def _submission_root(tmp_path: Path) -> Path:
    root = tmp_path / "submissions"
    root.mkdir(parents=True)
    _write_case(
        root,
        case_id="case:0123456789abcdefabcd",
        token="assignment:000000000000000000000001",
        corrected=False,
    )
    _write_case(
        root,
        case_id="case:fedcba9876543210abcd",
        token="assignment:000000000000000000000002",
        corrected=True,
    )
    return root


def _build(tmp_path: Path) -> dict[str, bytes]:
    queue = _queue()
    return build_prospective_submission_seal(
        queue,
        _submission_root(tmp_path),
        expected_queue_digest=queue["queue_digest"],
        author_execution_context_id=CONTEXT_ID,
        sealed_at="2026-08-05T11:00:00Z",
    )


def test_seals_exact_assignment_set_and_hashes_every_accepted_byte(tmp_path: Path) -> None:
    files = _build(tmp_path)
    manifest = json.loads(files["SEAL_MANIFEST.json"])
    declared = manifest.pop("manifest_digest")
    assert semantic_digest(manifest) == declared
    assert manifest["case_count"] == 2
    assert manifest["qualification_authority"] == "none_submission_seal_only"
    assert manifest["epistemic_boundary"] == {
        "ingestion_only": True,
        "project_authored_code_executed": False,
        "scientific_review_performed": False,
        "scientific_labels_created": False,
        "detector_output_created": False,
        "findings_created": False,
        "qualification_decision_created": False,
    }
    assert files == _build(tmp_path / "replay")

    copied = {
        entry["sealed_path"]: (entry["sha256"], entry["size_bytes"])
        for case in manifest["cases"]
        for entry in case["files"]
    }
    for relative, payload in files.items():
        if relative in {"SEAL_MANIFEST.json", "SOURCE_QUEUE.json"}:
            continue
        assert copied[relative] == (sha256_digest(payload), len(payload))
    assert any(path.endswith("/COORDINATOR_CHANGE_NOTE.md") for path in copied)
    source_submission = (
        tmp_path / "submissions" / "0123456789abcdefabcd" / "SUBMISSION.json"
    ).read_bytes()
    assert files["cases/0123456789abcdefabcd/SUBMISSION.json"] == source_submission
    assert source_submission.startswith(b'{\n  "opaque_case_id"')


@pytest.mark.parametrize("mutation", ["missing", "extra", "file_at_root", "replacement"])
def test_rejects_missing_extra_or_replacement_case_directories(
    tmp_path: Path, mutation: str
) -> None:
    root = _submission_root(tmp_path)
    if mutation == "missing":
        (root / "fedcba9876543210abcd").rename(tmp_path / "removed")
    elif mutation == "extra":
        (root / "aaaaaaaaaaaaaaaaaaaa").mkdir()
    elif mutation == "file_at_root":
        (root / "README.md").write_text("extra", encoding="utf-8")
    else:
        (root / "0123456789abcdefabcd").rename(root / "bbbbbbbbbbbbbbbbbbbb")
    queue = _queue()
    with pytest.raises(ProspectiveSubmissionIngestionError, match="case directories"):
        build_prospective_submission_seal(
            queue,
            root,
            expected_queue_digest=queue["queue_digest"],
            author_execution_context_id=CONTEXT_ID,
            sealed_at="2026-08-05T11:00:00Z",
        )


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("opaque_case_id", "case:aaaaaaaaaaaaaaaaaaaa", "case identity"),
        ("assignment_token", "assignment:replacement", "assignment token"),
        ("execution_context_id", "context:replacement", "execution context"),
        ("authored_at", "2026-08-05T13:00:00Z", "authored_at <= sealed_at"),
        ("selected_report_path", "../escape.md", "Unsafe selected path"),
        ("source_path", "other.py", "frozen root path"),
    ],
)
def test_rejects_submission_identity_token_context_and_timestamp_mismatch(
    tmp_path: Path, field: str, value: str, match: str
) -> None:
    root = _submission_root(tmp_path)
    path = root / "0123456789abcdefabcd" / "SUBMISSION.json"
    submission = json.loads(path.read_text(encoding="utf-8"))
    submission[field] = value
    path.write_text(json.dumps(submission, indent=2) + "\n", encoding="utf-8")
    queue = _queue()
    with pytest.raises(ProspectiveSubmissionIngestionError, match=match):
        build_prospective_submission_seal(
            queue,
            root,
            expected_queue_digest=queue["queue_digest"],
            author_execution_context_id=CONTEXT_ID,
            sealed_at="2026-08-05T11:00:00Z",
        )


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("unlisted", "file inventory"),
        ("unsafe", "Unsafe selected path"),
        ("malformed", "Malformed JSON"),
        ("duplicate", "Duplicate JSON key"),
        ("extra_field", "keys differ"),
        ("empty_dir", "directory inventory"),
    ],
)
def test_rejects_unlisted_drifted_unsafe_or_malformed_case_material(
    tmp_path: Path, mutation: str, match: str
) -> None:
    root = _submission_root(tmp_path)
    case = root / "0123456789abcdefabcd"
    path = case / "SUBMISSION.json"
    if mutation == "unlisted":
        (case / "notes.txt").write_text("unlisted", encoding="utf-8")
    elif mutation == "unsafe":
        submission = json.loads(path.read_text(encoding="utf-8"))
        submission["data_dictionary_path"] = "../escape.md"
        path.write_text(json.dumps(submission), encoding="utf-8")
    elif mutation == "malformed":
        path.write_text("{", encoding="utf-8")
    elif mutation == "duplicate":
        original = path.read_text(encoding="utf-8").rstrip()
        path.write_text(
            original[:-1] + ', "opaque_case_id": "case:0123456789abcdefabcd"}',
            encoding="utf-8",
        )
    elif mutation == "extra_field":
        submission = json.loads(path.read_text(encoding="utf-8"))
        submission["unexpected"] = True
        path.write_text(json.dumps(submission), encoding="utf-8")
    else:
        (case / "empty").mkdir()
    queue = _queue()
    with pytest.raises(ProspectiveSubmissionIngestionError, match=match):
        build_prospective_submission_seal(
            queue,
            root,
            expected_queue_digest=queue["queue_digest"],
            author_execution_context_id=CONTEXT_ID,
            sealed_at="2026-08-05T11:00:00Z",
        )


def test_rejects_symlinks_and_wrong_change_note_presence(tmp_path: Path) -> None:
    root = _submission_root(tmp_path)
    case = root / "0123456789abcdefabcd"
    target = case / "target.txt"
    target.write_text("target", encoding="utf-8")
    (case / "linked.txt").symlink_to(target)
    queue = _queue()
    with pytest.raises(ProspectiveSubmissionIngestionError, match="symlink"):
        build_prospective_submission_seal(
            queue,
            root,
            expected_queue_digest=queue["queue_digest"],
            author_execution_context_id=CONTEXT_ID,
            sealed_at="2026-08-05T11:00:00Z",
        )

    root = _submission_root(tmp_path / "wrong-note")
    beta = root / "fedcba9876543210abcd"
    (beta / "COORDINATOR_CHANGE_NOTE.md").unlink()
    with pytest.raises(ProspectiveSubmissionIngestionError, match="file inventory"):
        build_prospective_submission_seal(
            queue,
            root,
            expected_queue_digest=queue["queue_digest"],
            author_execution_context_id=CONTEXT_ID,
            sealed_at="2026-08-05T11:00:00Z",
        )


def test_rejects_queue_digest_drift_and_noncanonical_queue(tmp_path: Path) -> None:
    queue = _queue()
    root = _submission_root(tmp_path)
    with pytest.raises(ProspectiveSubmissionIngestionError, match="expected frozen queue digest"):
        build_prospective_submission_seal(
            queue,
            root,
            expected_queue_digest=sha256_digest("different"),
            author_execution_context_id=CONTEXT_ID,
            sealed_at="2026-08-05T11:00:00Z",
        )

    path = tmp_path / "queue.json"
    path.write_text(json.dumps(queue), encoding="utf-8")
    with pytest.raises(ProspectiveSubmissionIngestionError, match="canonical JSON"):
        load_canonical_json_object(path, label="author queue")


def test_write_is_create_once_and_preserves_validated_bytes(tmp_path: Path) -> None:
    files = _build(tmp_path)
    output = tmp_path / "sealed"
    assert write_prospective_submission_seal_once(output, files) == output.resolve()
    for relative, payload in files.items():
        assert (output / relative).read_bytes() == payload
    with pytest.raises(ProspectiveSubmissionIngestionError, match="already exists"):
        write_prospective_submission_seal_once(output, files)
