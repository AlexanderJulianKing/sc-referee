from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sc_referee.cli import app
from sc_referee.core.ids import canonical_json, semantic_digest
from sc_referee.execution_authorization import (
    authorize_execution_draft,
    prepare_authorization_draft,
)
from sc_referee.execution_request import (
    ExecutionRequestDraft,
    ExecutionRequestError,
    create_execution_request,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry


class _Terminal:
    def isatty(self) -> bool:
        return True

    def write(self, value: str) -> int:
        return len(value)

    def flush(self) -> None:
        return None

    def readline(self) -> str:
        return "challenge-request-admission-0001\n"


def _load(project_root: Path, name: str) -> dict[str, object]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.18.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _source_audit(project_root: Path, root: Path) -> tuple[Path, dict[str, object]]:
    root.mkdir()
    snapshot = _load(project_root, "repository-snapshot.example.json")
    snapshot["audit_run_id"] = "audit:static-source"
    file_record = _load(project_root, "file-record.unreadable.example.json")
    file_record.update(
        {
            "audit_run_id": "audit:static-source",
            "classification": "analysis_source",
            "file_record_id": "file:analysis.py",
            "path": "analysis.py",
            "snapshot_ref": {
                "record_type": "repository_snapshot",
                "record_id": snapshot["snapshot_id"],
            },
        }
    )
    lock: dict[str, object] = {
        "audit_run_id": "audit:static-source",
        "file_records": [file_record],
        "lock_kind": "general_static_v1",
        "lock_version": "0.2.0",
        "locked_at": "2026-07-29T18:00:00Z",
        "model_access_after_lock": False,
        "repository_snapshot": snapshot,
        "work_items": [],
    }
    lock["semantic_lock_digest"] = semantic_digest(lock)
    path = root / "semantic.lock.json"
    path.write_text(canonical_json(lock) + "\n", encoding="utf-8")
    return path, snapshot


def _draft(snapshot: dict[str, object]) -> ExecutionRequestDraft:
    snapshot_ref = {
        "record_type": "repository_snapshot",
        "record_id": snapshot["snapshot_id"],
    }
    environment_entries = ({"name": "PYTHONHASHSEED", "value": "0"},)
    return ExecutionRequestDraft(
        purpose="Run the exact bounded analysis entry point for reproduction evidence.",
        target_refs=({"record_type": "file_record", "record_id": "file:analysis.py"},),
        declared_input_refs=(snapshot_ref,),
        allowed_output_paths=("result.json",),
        image={
            "reference": "localhost/sc-referee-python@sha256:" + "3" * 64,
            "manifest_digest": "sha256:" + "3" * 64,
        },
        argv=("python", "/project/analysis.py", "--output", "/output/result.json"),
        environment_entries=environment_entries,
        limits={
            "cpu_quota_millis": 1000,
            "memory_bytes": 268_435_456,
            "open_files": 64,
            "process_count": 32,
            "wall_time_seconds": 60,
            "writable_bytes": 1_048_576,
        },
        unresolved_launch_fields=(),
    )


def test_request_creates_non_authorizing_child_lock_and_preserves_parent(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    source_lock, snapshot = _source_audit(project_root, tmp_path / "source")
    before = source_lock.read_bytes()

    result = create_execution_request(
        source_lock.parent,
        tmp_path / "request",
        _draft(snapshot),
        schema_root,
        created_at="2026-07-29T19:00:00Z",
    )

    assert source_lock.read_bytes() == before
    locked = json.loads(result.semantic_lock_path.read_text(encoding="utf-8"))
    item = locked["work_items"][0]
    LocalSchemaRegistry(schema_root).validate(item)
    assert locked["parent_semantic_lock_digest"] == json.loads(before)["semantic_lock_digest"]
    assert locked["model_calls"] == []
    assert locked["model_access_after_lock"] is False
    assert locked["project_execution_authorizations"] == []
    assert locked["executions"] == []
    assert locked["file_records"] == json.loads(before)["file_records"]
    assert locked["asset_identities"] == []
    assert item["kind"] == "project_execution"
    assert item["status"] == "awaiting_authorization"
    assert item["packet"]["policy"]["launch_authorized"] is False
    digest_input = copy.deepcopy(locked)
    digest_input.pop("semantic_lock_digest")
    assert locked["semantic_lock_digest"] == semantic_digest(digest_input)


def test_request_rejects_missing_target_without_creating_output(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _source_lock, snapshot = _source_audit(project_root, tmp_path / "source")
    draft = _draft(snapshot)
    draft = ExecutionRequestDraft(
        **{
            **draft.__dict__,
            "target_refs": ({"record_type": "file_record", "record_id": "file:not-in-lock"},),
        }
    )

    with pytest.raises(ExecutionRequestError, match="target"):
        create_execution_request(
            tmp_path / "source",
            tmp_path / "request",
            draft,
            schema_root,
            created_at="2026-07-29T19:00:00Z",
        )
    assert not (tmp_path / "request").exists()


def test_request_preserves_explicit_unresolved_launch_field(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _source_lock, snapshot = _source_audit(project_root, tmp_path / "source")
    draft = _draft(snapshot)
    draft = ExecutionRequestDraft(
        **{
            **draft.__dict__,
            "argv": None,
            "unresolved_launch_fields": ("argv",),
        }
    )
    result = create_execution_request(
        tmp_path / "source",
        tmp_path / "request",
        draft,
        schema_root,
        created_at="2026-07-29T19:00:00Z",
    )
    locked = json.loads(result.semantic_lock_path.read_text(encoding="utf-8"))
    launch = locked["work_items"][0]["packet"]["launch_envelope"]
    assert launch["argv"] is None
    assert launch["unresolved_fields"] == ["argv"]


@pytest.mark.parametrize("path", ["../escape.json", "/absolute.json", "*.json"])
def test_request_rejects_broadenable_output_path(
    project_root: Path, schema_root: Path, tmp_path: Path, path: str
) -> None:
    _source_lock, snapshot = _source_audit(project_root, tmp_path / "source")
    draft = _draft(snapshot)
    draft = ExecutionRequestDraft(**{**draft.__dict__, "allowed_output_paths": (path,)})
    with pytest.raises(ExecutionRequestError):
        create_execution_request(
            tmp_path / "source",
            tmp_path / "request",
            draft,
            schema_root,
            created_at="2026-07-29T19:00:00Z",
        )
    assert not (tmp_path / "request").exists()


def test_request_execution_cli_creates_locked_request_only(
    project_root: Path, tmp_path: Path
) -> None:
    _source_lock, snapshot = _source_audit(project_root, tmp_path / "source")
    draft = _draft(snapshot)
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "allowed_output_paths": list(draft.allowed_output_paths),
                "argv": list(draft.argv or ()),
                "declared_input_refs": list(draft.declared_input_refs),
                "environment_entries": list(draft.environment_entries or ()),
                "image": draft.image,
                "limits": draft.limits,
                "purpose": draft.purpose,
                "target_refs": list(draft.target_refs),
                "unresolved_launch_fields": list(draft.unresolved_launch_fields),
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "request-output"

    result = CliRunner().invoke(
        app,
        [
            "request-execution",
            str(tmp_path / "source"),
            "--request",
            str(request_path),
            "--output",
            str(output),
            "--created-at",
            "2026-07-29T19:00:00Z",
        ],
    )

    assert result.exit_code == 0, result.output
    status = json.loads((output / "REQUEST_STATUS.json").read_text(encoding="utf-8"))
    assert status["execution_authorized"] is False
    assert status["execution_launched"] is False
    assert "awaiting direct authorization" in result.output


def test_authorize_execution_cli_refuses_noninteractive_confirmation(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _source_lock, snapshot = _source_audit(project_root, tmp_path / "source")
    request = create_execution_request(
        tmp_path / "source",
        tmp_path / "request",
        _draft(snapshot),
        schema_root,
        created_at="2026-07-29T19:00:00Z",
    )
    capability = _load(project_root, "sandbox-capability.example.json")
    capability_path = tmp_path / "capability.json"
    capability_path.write_text(canonical_json(capability) + "\n", encoding="utf-8")
    launch_path = tmp_path / "launch.json"
    launch_path.write_text(
        json.dumps(
            {
                "argv": [
                    "python",
                    "/project/analysis.py",
                    "--output",
                    "/output/result.json",
                ],
                "environment_entries": [{"name": "PYTHONHASHSEED", "value": "0"}],
                "image_reference": "localhost/sc-referee-python@sha256:" + "3" * 64,
                "limits": {
                    "cpu_quota_millis": 1000,
                    "memory_bytes": 268_435_456,
                    "open_files": 64,
                    "process_count": 32,
                    "wall_time_seconds": 60,
                    "writable_bytes": 1_048_576,
                },
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "authorize-execution",
            str(request.output_root),
            "--work-item-id",
            request.work_item_id,
            "--capability",
            str(capability_path),
            "--launch",
            str(launch_path),
            "--output",
            str(tmp_path / "linked"),
            "--linked-audit-run-id",
            "audit:linked-reproduction",
            "--expires-at",
            "2026-07-29T20:05:00Z",
            "--actor-id",
            "local-user:declared",
            "--actor-display-name",
            "Declared local user",
        ],
    )

    assert result.exit_code == 2
    assert "interactive" in result.output
    assert not (tmp_path / "linked").exists()


def test_created_request_is_admitted_by_direct_authorization_path(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _source_lock, snapshot = _source_audit(project_root, tmp_path / "source")
    request = create_execution_request(
        tmp_path / "source",
        tmp_path / "request",
        _draft(snapshot),
        schema_root,
        created_at="2026-07-29T19:00:00Z",
    )
    capability = _load(project_root, "sandbox-capability.example.json")
    capability_path = tmp_path / "capability.json"
    capability_path.write_text(canonical_json(capability) + "\n", encoding="utf-8")
    draft = prepare_authorization_draft(
        request.output_root,
        request.work_item_id,
        capability_path,
        {
            "argv": ["python", "/project/analysis.py", "--output", "/output/result.json"],
            "environment_entries": [{"name": "PYTHONHASHSEED", "value": "0"}],
            "image_reference": "localhost/sc-referee-python@sha256:" + "3" * 64,
            "limits": {
                "cpu_quota_millis": 1000,
                "memory_bytes": 268_435_456,
                "open_files": 64,
                "process_count": 32,
                "wall_time_seconds": 60,
                "writable_bytes": 1_048_576,
            },
        },
        tmp_path / "linked",
        "audit:linked-reproduction",
        expires_at="2026-07-29T20:05:00Z",
        actor_id="local-user:declared",
        actor_display_name="Declared local user",
    )

    result = authorize_execution_draft(
        draft,
        schema_root,
        terminal_input=_Terminal(),
        terminal_output=_Terminal(),
        confirmed_at="2026-07-29T20:00:00Z",
        nonce_factory=lambda: "nonce-request-admission-0001",
        challenge_factory=lambda: "challenge-request-admission-0001",
    )

    assert result.authorization["scope"]["source_audit_run_ref"]["record_id"] == (
        request.audit_run_id
    )
    assert (
        result.authorization["scope"]["snapshot"]["record_ref"]["record_id"]
        == (snapshot["snapshot_id"])
    )


def test_execute_authorized_cli_rejects_standalone_capability_before_runtime(
    project_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    linked = tmp_path / "linked"
    (linked / "control" / "authorization-registry").mkdir(parents=True)
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    executable = tmp_path / "podman"
    executable.write_bytes(b"test-owned-placeholder")
    capability = _load(project_root, "sandbox-capability.example.json")
    capability_path = tmp_path / "capability.json"
    capability_path.write_text(canonical_json(capability) + "\n", encoding="utf-8")
    observed: dict[str, object] = {}

    def fake_execute(*_args: object, **_options: object) -> object:
        observed["called"] = True
        raise AssertionError("disabled CLI reached the executor")

    monkeypatch.setattr(
        "sc_referee.execution_runtime.execute_registered_podman_attempt", fake_execute
    )
    result = CliRunner().invoke(
        app,
        [
            "execute-authorized",
            str(linked),
            "--capability",
            str(capability_path),
            "--snapshot-root",
            str(snapshot),
            "--podman-executable",
            str(executable),
        ],
    )

    assert result.exit_code == 2
    assert observed == {}
    normalized_output = " ".join(result.output.split())
    assert "disabled by ADR-0017" in normalized_output
    assert "cannot establish a launch premise" in normalized_output


def test_post_mpp_execution_commands_are_hidden_from_product_help() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "audit" in result.output
    assert "replay" in result.output
    for command in (
        "probe-execution-capability",
        "request-execution",
        "authorize-execution",
        "execute-authorized",
    ):
        assert command not in result.output
