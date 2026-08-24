from __future__ import annotations

import copy
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest

from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.execution_authorization import (
    AuthorizationDraft,
    AuthorizationError,
    ClaimBindings,
    InteractiveAuthorizationResult,
    authorize_execution_draft,
    claim_authorization,
    finalize_claim,
    recover_orphaned_claim,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry


class _Terminal:
    def __init__(self, response: str, *, attached: bool = True) -> None:
        self.response = response
        self.attached = attached
        self.displayed = ""

    def isatty(self) -> bool:
        return self.attached

    def write(self, value: str) -> int:
        self.displayed += value
        return len(value)

    def flush(self) -> None:
        return None

    def readline(self) -> str:
        return self.response


def _example(project_root: Path, name: str) -> dict[str, object]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.21.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _write_source_lock(
    project_root: Path, path: Path
) -> tuple[dict[str, object], dict[str, object]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = _example(project_root, "repository-snapshot.example.json")
    snapshot["audit_run_id"] = "audit:source"
    file_record = _example(project_root, "file-record.unreadable.example.json")
    file_record.update(
        {
            "audit_run_id": "audit:source",
            "classification": "analysis_source",
            "file_record_id": "file:analysis.py",
            "path": "analysis.py",
            "snapshot_ref": {
                "record_type": "repository_snapshot",
                "record_id": snapshot["snapshot_id"],
            },
        }
    )
    item = _example(project_root, "work-item.project-execution.example.json")
    item["audit_run_id"] = "audit:source"
    item["target_refs"] = [{"record_type": "file_record", "record_id": "file:analysis.py"}]
    packet = item["packet"]
    packet["source_snapshot"] = {  # type: ignore[index]
        "record_ref": {
            "record_type": "repository_snapshot",
            "record_id": snapshot["snapshot_id"],
        },
        "semantic_digest": semantic_digest(snapshot),
    }
    packet["target_refs"] = copy.deepcopy(item["target_refs"])  # type: ignore[index]
    packet["declared_input_refs"] = [  # type: ignore[index]
        {"record_type": "repository_snapshot", "record_id": snapshot["snapshot_id"]}
    ]
    proposed_environment = packet["launch_envelope"]["environment"]  # type: ignore[index]
    proposed_environment["normalized_digest"] = semantic_digest(  # type: ignore[index]
        proposed_environment["entries"]  # type: ignore[index]
    )
    packet_without_digest = copy.deepcopy(packet)
    packet_without_digest.pop("packet_digest")
    packet["packet_digest"] = semantic_digest(packet_without_digest)  # type: ignore[index]
    lock: dict[str, object] = {
        "audit_run_id": "audit:source",
        "file_records": [file_record],
        "lock_kind": "general_static_v1",
        "lock_version": "0.2.0",
        "locked_at": "2026-07-29T19:59:00Z",
        "model_access_after_lock": False,
        "repository_snapshot": snapshot,
        "work_items": [item],
    }
    lock["semantic_lock_digest"] = semantic_digest(lock)
    path.write_text(canonical_json(lock) + "\n", encoding="utf-8")
    return snapshot, item


def _draft(project_root: Path, output: Path) -> AuthorizationDraft:
    capability = _example(project_root, "sandbox-capability.example.json")
    snapshot, _item = _write_source_lock(project_root, output.parent / "source-semantic.lock.json")
    return AuthorizationDraft(
        linked_output_root=output,
        source_semantic_lock_path=output.parent / "source-semantic.lock.json",
        linked_audit_run_id="audit:linked-reproduction",
        work_item_id="work-item:execute-example",
        capability_record=capability,
        image_reference="localhost/sc-referee-python@sha256:" + "3" * 64,
        argv=("python", "/project/analysis.py", "--output", "/output/result.json"),
        declared_input_refs=(
            {"record_type": "repository_snapshot", "record_id": snapshot["snapshot_id"]},
        ),
        allowed_output_paths=("result.json",),
        environment=(("PYTHONHASHSEED", "0"),),
        wall_time_seconds=60,
        cpu_quota_millis=1000,
        memory_bytes=268_435_456,
        process_count=32,
        open_files=64,
        writable_bytes=1_048_576,
        expires_at="2026-07-29T20:05:00Z",
        actor_id="local-user:declared",
        actor_display_name="Declared local user",
    )


def _authorize(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> InteractiveAuthorizationResult:
    challenge = "challenge-fresh-0001"
    terminal = _Terminal(challenge + "\n")
    return authorize_execution_draft(
        _draft(project_root, tmp_path / "linked"),
        schema_root,
        terminal_input=terminal,
        terminal_output=terminal,
        confirmed_at="2026-07-29T20:00:00Z",
        nonce_factory=lambda: "nonce-fresh-authorization-0001",
        challenge_factory=lambda: challenge,
    )


def _bindings(result: InteractiveAuthorizationResult) -> ClaimBindings:
    authorization = result.authorization
    scope = authorization["scope"]
    return ClaimBindings(
        source_semantic_lock_digest=scope["source_semantic_lock_digest"],
        linked_audit_run_id=scope["linked_audit_run_ref"]["record_id"],
        work_item_id=scope["work_item_ref"]["record_id"],
        work_item_semantic_digest=scope["work_item_semantic_digest"],
        snapshot_semantic_digest=scope["snapshot"]["semantic_digest"],
        capability_semantic_digest=scope["capability"]["semantic_digest"],
        image_manifest_digest=authorization["image"]["manifest_digest"],
        command_digest=authorization["command"]["normalized_digest"],
        environment_digest=authorization["environment"]["normalized_digest"],
        allowed_output_paths=tuple(scope["allowed_output_paths"]),
        linked_output_root=result.linked_output_root,
    )


def test_interactive_authorization_constructs_valid_record_and_private_registry(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    challenge = "challenge-fresh-0001"
    terminal = _Terminal(challenge + "\n")

    result = authorize_execution_draft(
        _draft(project_root, tmp_path / "linked"),
        schema_root,
        terminal_input=terminal,
        terminal_output=terminal,
        confirmed_at="2026-07-29T20:00:00Z",
        nonce_factory=lambda: "nonce-fresh-authorization-0001",
        challenge_factory=lambda: challenge,
    )

    LocalSchemaRegistry(schema_root).validate(result.authorization)
    assert challenge in terminal.displayed
    assert result.authorization["scope"]["source_semantic_lock_digest"] in terminal.displayed
    assert result.authorization["scope"]["work_item_binding_status"] == (
        "complete_project_execution_work_item"
    )
    assert result.authorization["scope"]["work_item_semantic_digest"] in terminal.displayed
    assert result.authorization_path.is_file()
    assert result.registry_entry_path.is_file()
    assert result.source_semantic_lock_path.is_file()
    assert (
        result.source_semantic_lock_path.read_bytes()
        == (tmp_path / "source-semantic.lock.json").read_bytes()
    )
    assert not result.consumption_receipt_path.exists()


@pytest.mark.parametrize("input_attached,output_attached", [(False, True), (True, False)])
def test_authorization_rejects_noninteractive_or_piped_terminal(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    input_attached: bool,
    output_attached: bool,
) -> None:
    with pytest.raises(AuthorizationError, match="interactive"):
        authorize_execution_draft(
            _draft(project_root, tmp_path / "linked"),
            schema_root,
            terminal_input=_Terminal("challenge-fresh-0001\n", attached=input_attached),
            terminal_output=_Terminal("", attached=output_attached),
            confirmed_at="2026-07-29T20:00:00Z",
            nonce_factory=lambda: "nonce-fresh-authorization-0001",
            challenge_factory=lambda: "challenge-fresh-0001",
        )
    assert not (tmp_path / "linked").exists()


def test_wrong_or_stale_challenge_creates_no_launchable_registry_entry(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    with pytest.raises(AuthorizationError, match="challenge"):
        authorize_execution_draft(
            _draft(project_root, tmp_path / "linked"),
            schema_root,
            terminal_input=_Terminal("challenge-from-an-earlier-request\n"),
            terminal_output=_Terminal(""),
            confirmed_at="2026-07-29T20:00:00Z",
            nonce_factory=lambda: "nonce-fresh-authorization-0001",
            challenge_factory=lambda: "challenge-fresh-0001",
        )
    assert not (tmp_path / "linked" / "control" / "authorization-registry" / "entry.json").exists()


def test_atomic_claim_is_single_use_even_under_concurrency(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    result = _authorize(project_root, schema_root, tmp_path)
    bindings = _bindings(result)

    def claim() -> str:
        try:
            receipt = claim_authorization(
                result.registry_root,
                bindings,
                schema_root,
                claimed_at="2026-07-29T20:01:00Z",
            )
            return str(receipt["attempt_id"])
        except FileExistsError:
            return "already-consumed"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _index: claim(), range(2)))

    assert outcomes.count("already-consumed") == 1
    assert len({outcome for outcome in outcomes if outcome != "already-consumed"}) == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_semantic_lock_digest", "sha256:" + "0" * 64),
        ("linked_audit_run_id", "audit:drift"),
        ("work_item_id", "work-item:drift"),
        ("work_item_semantic_digest", "sha256:" + "0" * 64),
        ("snapshot_semantic_digest", "sha256:" + "0" * 64),
        ("capability_semantic_digest", "sha256:" + "0" * 64),
        ("image_manifest_digest", "sha256:" + "0" * 64),
        ("command_digest", "sha256:" + "0" * 64),
        ("environment_digest", "sha256:" + "0" * 64),
        ("allowed_output_paths", ("other.json",)),
    ],
)
def test_binding_drift_prevents_claim_without_consuming(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    result = _authorize(project_root, schema_root, tmp_path)
    values = _bindings(result).__dict__ | {field: value}

    with pytest.raises(AuthorizationError, match="binding"):
        claim_authorization(
            result.registry_root,
            ClaimBindings(**values),
            schema_root,
            claimed_at="2026-07-29T20:01:00Z",
        )
    assert not result.consumption_receipt_path.exists()


def test_expired_authorization_does_not_create_receipt(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    result = _authorize(project_root, schema_root, tmp_path)

    with pytest.raises(AuthorizationError, match="expired"):
        claim_authorization(
            result.registry_root,
            _bindings(result),
            schema_root,
            claimed_at="2026-07-29T20:06:00Z",
        )
    assert not result.consumption_receipt_path.exists()


def test_mutated_public_authorization_and_copied_registry_cannot_launch(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    result = _authorize(project_root, schema_root, tmp_path)
    authorization = json.loads(result.authorization_path.read_text(encoding="utf-8"))
    authorization["limits"]["wall_time_seconds"] = 61
    result.authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
    with pytest.raises(AuthorizationError, match="authorization bytes"):
        claim_authorization(
            result.registry_root,
            _bindings(result),
            schema_root,
            claimed_at="2026-07-29T20:01:00Z",
        )

    second = _authorize(project_root, schema_root, tmp_path / "second")
    copied = tmp_path / "copied-registry"
    shutil.copytree(second.registry_root, copied)
    copied_bindings = copy.copy(_bindings(second))
    object.__setattr__(copied_bindings, "linked_output_root", copied.parents[1])
    with pytest.raises(AuthorizationError, match="registry identity"):
        claim_authorization(
            copied,
            copied_bindings,
            schema_root,
            claimed_at="2026-07-29T20:01:00Z",
        )


def test_authorization_preserves_source_lock_bytes(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    draft = _draft(project_root, tmp_path / "linked")
    before = draft.source_semantic_lock_path.read_bytes()
    challenge = "challenge-source-lock-0001"
    authorize_execution_draft(
        draft,
        schema_root,
        terminal_input=_Terminal(challenge + "\n"),
        terminal_output=_Terminal(""),
        confirmed_at="2026-07-29T20:00:00Z",
        nonce_factory=lambda: "nonce-source-lock-0001",
        challenge_factory=lambda: challenge,
    )
    assert draft.source_semantic_lock_path.read_bytes() == before


def test_registered_source_lock_drift_prevents_claim_without_consuming(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    result = _authorize(project_root, schema_root, tmp_path)
    registered = json.loads(result.source_semantic_lock_path.read_text(encoding="utf-8"))
    registered["model_access_after_lock"] = True
    result.source_semantic_lock_path.write_text(canonical_json(registered) + "\n", encoding="utf-8")

    with pytest.raises(AuthorizationError, match="source semantic lock drifted"):
        claim_authorization(
            result.registry_root,
            _bindings(result),
            schema_root,
            claimed_at="2026-07-29T20:01:00Z",
        )
    assert not result.consumption_receipt_path.exists()


@pytest.mark.parametrize(
    "case",
    [
        "absent_work_item",
        "cross_run",
        "non_project",
        "non_awaiting",
        "wrong_privilege",
        "wrong_packet_kind",
        "packet_digest_mismatch",
        "lock_digest_mismatch",
        "snapshot_digest_mismatch",
        "missing_target",
    ],
)
def test_work_item_admission_rejects_before_challenge_or_registry_write(
    project_root: Path, schema_root: Path, tmp_path: Path, case: str
) -> None:
    draft = _draft(project_root, tmp_path / "linked")
    lock = json.loads(draft.source_semantic_lock_path.read_text(encoding="utf-8"))
    item = lock["work_items"][0]
    if case == "absent_work_item":
        lock["work_items"] = []
    elif case == "cross_run":
        item["audit_run_id"] = "audit:other"
    elif case == "non_project":
        item["kind"] = "semantic_resolution"
    elif case == "non_awaiting":
        item["status"] = "ready"
    elif case == "wrong_privilege":
        item["scheduling"]["execution_privilege"] = "safe_inspection"
    elif case == "wrong_packet_kind":
        item["packet"]["packet_kind"] = "semantic_or_auditor_work_v1"
    elif case == "packet_digest_mismatch":
        item["packet"]["packet_digest"] = "sha256:" + "0" * 64
    elif case == "lock_digest_mismatch":
        lock["semantic_lock_digest"] = "sha256:" + "0" * 64
    elif case == "snapshot_digest_mismatch":
        item["packet"]["source_snapshot"]["semantic_digest"] = "sha256:" + "0" * 64
        packet = copy.deepcopy(item["packet"])
        packet.pop("packet_digest")
        item["packet"]["packet_digest"] = semantic_digest(packet)
    elif case == "missing_target":
        lock["file_records"] = []
    if case != "lock_digest_mismatch":
        lock.pop("semantic_lock_digest", None)
        lock["semantic_lock_digest"] = semantic_digest(lock)
    draft.source_semantic_lock_path.write_text(canonical_json(lock) + "\n", encoding="utf-8")
    terminal = _Terminal("challenge-work-item-0001\n")

    with pytest.raises(AuthorizationError):
        authorize_execution_draft(
            draft,
            schema_root,
            terminal_input=terminal,
            terminal_output=terminal,
            confirmed_at="2026-07-29T20:00:00Z",
            nonce_factory=lambda: "nonce-work-item-0001",
            challenge_factory=lambda: "challenge-work-item-0001",
        )
    assert terminal.displayed == ""
    assert not draft.linked_output_root.exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("argv", ("python", "/project/other.py")),
        (
            "declared_input_refs",
            ({"record_type": "repository_snapshot", "record_id": "snapshot:other"},),
        ),
        ("allowed_output_paths", ("other.json",)),
        ("environment", (("OMP_NUM_THREADS", "2"), ("PYTHONHASHSEED", "0"))),
        ("wall_time_seconds", 61),
    ],
)
def test_authorization_cannot_broaden_locked_work_item_scope(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    draft = replace(_draft(project_root, tmp_path / "linked"), **{field: value})
    terminal = _Terminal("challenge-no-broadening-0001\n")
    with pytest.raises(AuthorizationError, match="WorkItem"):
        authorize_execution_draft(
            draft,
            schema_root,
            terminal_input=terminal,
            terminal_output=terminal,
            confirmed_at="2026-07-29T20:00:00Z",
            nonce_factory=lambda: "nonce-no-broadening-0001",
            challenge_factory=lambda: "challenge-no-broadening-0001",
        )
    assert terminal.displayed == ""
    assert not draft.linked_output_root.exists()


def test_authorization_may_narrow_locked_environment_and_limits(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    draft = replace(
        _draft(project_root, tmp_path / "linked"),
        environment=(),
        wall_time_seconds=30,
        memory_bytes=134_217_728,
    )
    challenge = "challenge-narrowing-0001"
    result = authorize_execution_draft(
        draft,
        schema_root,
        terminal_input=_Terminal(challenge + "\n"),
        terminal_output=_Terminal(""),
        confirmed_at="2026-07-29T20:00:00Z",
        nonce_factory=lambda: "nonce-narrowing-0001",
        challenge_factory=lambda: challenge,
    )
    assert result.authorization["environment"]["entries"] == []
    assert result.authorization["limits"]["wall_time_seconds"] == 30


def test_crash_recovery_preserves_receipt_and_records_unknown_once(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    result = _authorize(project_root, schema_root, tmp_path)
    receipt = claim_authorization(
        result.registry_root,
        _bindings(result),
        schema_root,
        claimed_at="2026-07-29T20:01:00Z",
    )
    before = result.consumption_receipt_path.read_bytes()

    terminal = recover_orphaned_claim(
        result.registry_root,
        recovered_at="2026-07-29T20:02:00Z",
        reason="controller_restarted_before_terminal_capture",
    )

    assert terminal["attempt_id"] == receipt["attempt_id"]
    assert terminal["disposition"] == "failed_unknown_after_controller_recovery"
    assert result.consumption_receipt_path.read_bytes() == before
    with pytest.raises(FileExistsError):
        recover_orphaned_claim(
            result.registry_root,
            recovered_at="2026-07-29T20:03:00Z",
            reason="second_recovery",
        )


@pytest.mark.parametrize(
    "disposition",
    [
        "completed",
        "failed_runtime_start",
        "failed_nonzero_exit",
        "timed_out",
        "cancelled",
        "output_rejected",
        "cleanup_failed",
        "controller_failed_unknown",
    ],
)
def test_terminal_dispositions_preserve_and_never_reopen_consumption(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    disposition: str,
) -> None:
    result = _authorize(project_root, schema_root, tmp_path)
    receipt = claim_authorization(
        result.registry_root,
        _bindings(result),
        schema_root,
        claimed_at="2026-07-29T20:01:00Z",
    )
    before = result.consumption_receipt_path.read_bytes()

    terminal = finalize_claim(
        result.registry_root,
        attempt_id=receipt["attempt_id"],
        disposition=disposition,
        finalized_at="2026-07-29T20:02:00Z",
        evidence_digest="sha256:" + "d" * 64,
        limitations=("Synthetic registry test; no project process was launched.",),
    )

    assert terminal["disposition"] == disposition
    assert result.consumption_receipt_path.read_bytes() == before
    with pytest.raises(FileExistsError):
        finalize_claim(
            result.registry_root,
            attempt_id=receipt["attempt_id"],
            disposition=disposition,
            finalized_at="2026-07-29T20:03:00Z",
            evidence_digest=None,
            limitations=("Second terminal write is prohibited.",),
        )
