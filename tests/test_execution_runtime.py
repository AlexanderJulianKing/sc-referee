from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from sc_referee.controller import replay
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.execution_authorization import AuthorizationDraft, authorize_execution_draft
from sc_referee.execution_evidence import inspect_linked_execution_v14
from sc_referee.execution_probe import CommandResult
from sc_referee.execution_runtime import (
    AttachedProcessResult,
    SubprocessExecutionRuntime,
    execute_registered_podman_attempt,
)

_ANALYSIS_BYTES = b"print('bounded execution fixture')\n"


class _Terminal:
    def isatty(self) -> bool:
        return True

    def write(self, value: str) -> int:
        return len(value)

    def flush(self) -> None:
        return None

    def readline(self) -> str:
        return "challenge-runtime-0001\n"


class _FakeExecutionRuntime:
    def __init__(
        self,
        *,
        registry_root: Path,
        output_source: Path,
        create_exit: int = 0,
        process_exit: int = 0,
        timed_out: bool = False,
        cleanup_succeeds: bool = True,
        truncate_logs: bool = False,
        raise_on_start: bool = False,
        observe_resources: bool = False,
        exceed_resources: bool = False,
    ) -> None:
        self.registry_root = registry_root
        self.output_source = output_source
        self.create_exit = create_exit
        self.process_exit = process_exit
        self.timed_out = timed_out
        self.cleanup_succeeds = cleanup_succeeds
        self.truncate_logs = truncate_logs
        self.raise_on_start = raise_on_start
        self.observe_resources = observe_resources
        self.exceed_resources = exceed_resources
        self.calls: list[tuple[str, ...]] = []

    def _record(self, argv: tuple[str, ...]) -> None:
        assert (self.registry_root / "consumption-receipt.json").is_file()
        self.calls.append(argv)

    def run(self, argv: tuple[str, ...], *, timeout_seconds: int) -> CommandResult:
        del timeout_seconds
        self._record(argv)
        if argv[1:3] == ("image", "inspect"):
            reference = argv[3]
            digest = reference.rsplit("@", maxsplit=1)[1]
            return CommandResult(
                argv,
                0,
                json.dumps([{"Digest": digest, "RepoDigests": [reference]}]),
                "",
                False,
            )
        if argv[1] == "create":
            return CommandResult(argv, self.create_exit, "container-id\n", "", False)
        if argv[1:3] == ("container", "inspect"):
            return CommandResult(
                argv,
                0,
                json.dumps([{"State": {"Running": False, "ExitCode": self.process_exit}}]),
                "",
                False,
            )
        if argv[1] == "cp":
            destination = Path(argv[-1])
            for source in self.output_source.rglob("*"):
                relative = source.relative_to(self.output_source)
                target = destination / relative
                if source.is_symlink():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(source.readlink())
                elif source.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            return CommandResult(argv, 0, "", "", False)
        if argv[1] == "kill":
            return CommandResult(argv, 0, "", "", False)
        if argv[1:3] == ("rm", "--force"):
            return CommandResult(argv, 0 if self.cleanup_succeeds else 125, "", "", False)
        if argv[1:3] == ("container", "exists"):
            return CommandResult(argv, 1 if self.cleanup_succeeds else 0, "", "", False)
        raise AssertionError(f"unexpected command: {argv}")

    def start_attached(
        self,
        argv: tuple[str, ...],
        *,
        timeout_seconds: int,
        stdout_path: Path,
        stderr_path: Path,
        max_log_bytes: int,
    ) -> AttachedProcessResult:
        del timeout_seconds
        self._record(argv)
        if self.raise_on_start:
            raise OSError("synthetic attach failure")
        stdout = b"x" * (max_log_bytes + 10) if self.truncate_logs else b"workflow stdout\n"
        stderr = b"workflow stderr\n"
        stdout_path.write_bytes(stdout[:max_log_bytes])
        stderr_path.write_bytes(stderr[:max_log_bytes])
        return AttachedProcessResult(
            exit_code=None if self.timed_out else self.process_exit,
            timed_out=self.timed_out,
            stdout_observed_bytes=len(stdout),
            stderr_observed_bytes=len(stderr),
            stdout_retained_bytes=min(len(stdout), max_log_bytes),
            stderr_retained_bytes=min(len(stderr), max_log_bytes),
            stdout_truncated=len(stdout) > max_log_bytes,
            stderr_truncated=len(stderr) > max_log_bytes,
            cpu_time_seconds=0.25 if self.observe_resources else None,
            peak_memory_bytes=(
                536_870_912
                if self.exceed_resources
                else 33_554_432
                if self.observe_resources
                else None
            ),
            process_count_peak=(
                33 if self.exceed_resources else 2 if self.observe_resources else None
            ),
            open_files_peak=(
                65 if self.exceed_resources else 8 if self.observe_resources else None
            ),
            resource_observation_profile=(
                "synthetic-complete-test-v1" if self.observe_resources else "unavailable"
            ),
        )


def _load(project_root: Path, name: str) -> dict[str, object]:
    return json.loads(
        (project_root / "reference" / "schemas-v0.21.0" / "examples" / name).read_text(
            encoding="utf-8"
        )
    )


def _source_lock(project_root: Path, path: Path) -> dict[str, object]:
    snapshot = _load(project_root, "repository-snapshot.example.json")
    snapshot["audit_run_id"] = "audit:source"
    file_record = _load(project_root, "file-record.unreadable.example.json")
    file_record.update(
        {
            "asset_identity_ref": {
                "record_type": "asset_identity",
                "record_id": "asset-identity:analysis.py",
            },
            "audit_run_id": "audit:source",
            "byte_size": len(_ANALYSIS_BYTES),
            "classification": "analysis_source",
            "file_record_id": "file:analysis.py",
            "identity_disposition": "recorded",
            "inspection_disposition": "not_selected",
            "limitations": [],
            "path": "analysis.py",
            "snapshot_ref": {
                "record_type": "repository_snapshot",
                "record_id": snapshot["snapshot_id"],
            },
        }
    )
    identity = _load(project_root, "asset-identity.example.json")
    identity.update(
        {
            "asset_identity_id": "asset-identity:analysis.py",
            "asset_ref": {
                "record_type": "file_record",
                "record_id": "file:analysis.py",
            },
            "audit_run_id": "audit:source",
            "identity_evidence": {
                "kind": "full_digest",
                "digest": "sha256:" + hashlib.sha256(_ANALYSIS_BYTES).hexdigest(),
            },
            "limitations": [],
            "tier": "full_digest",
        }
    )
    item = _load(project_root, "work-item.project-execution.example.json")
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
    environment = packet["launch_envelope"]["environment"]  # type: ignore[index]
    environment["normalized_digest"] = semantic_digest(environment["entries"])  # type: ignore[index]
    packet_without_digest = copy.deepcopy(packet)
    packet_without_digest.pop("packet_digest")
    packet["packet_digest"] = semantic_digest(packet_without_digest)  # type: ignore[index]
    lock: dict[str, object] = {
        "audit_run_id": "audit:source",
        "asset_identities": [identity],
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
    return snapshot


def _materialize_snapshot(tmp_path: Path) -> Path:
    root = tmp_path / "snapshot-materialized"
    root.mkdir()
    (root / "analysis.py").write_bytes(_ANALYSIS_BYTES)
    return root


def _authorized_attempt(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> tuple[object, Path, dict[str, object], Path]:
    executable = tmp_path / "podman"
    executable.write_bytes(b"fake-podman-runtime")
    executable.chmod(0o755)
    executable_digest = "sha256:" + hashlib.sha256(executable.read_bytes()).hexdigest()
    capability = _load(project_root, "sandbox-capability.example.json")
    capability["capability_evidence"]["backend"].update(  # type: ignore[index]
        {
            "executable_path": str(executable.resolve()),
            "executable_digest": executable_digest,
        }
    )
    capability["capability_evidence"]["expires_at"] = "2026-07-29T21:00:00Z"  # type: ignore[index]
    source_lock_path = tmp_path / "source-semantic.lock.json"
    snapshot = _source_lock(project_root, source_lock_path)
    linked = tmp_path / "linked"
    draft = AuthorizationDraft(
        linked_output_root=linked,
        source_semantic_lock_path=source_lock_path,
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
    terminal = _Terminal()
    authorization = authorize_execution_draft(
        draft,
        schema_root,
        terminal_input=terminal,
        terminal_output=terminal,
        confirmed_at="2026-07-29T20:00:00Z",
        nonce_factory=lambda: "nonce-runtime-attempt-0001",
        challenge_factory=lambda: "challenge-runtime-0001",
    )
    return authorization, executable, capability, linked


def _run(
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
    **runtime_options: object,
) -> tuple[object, _FakeExecutionRuntime]:
    authorization, executable, capability, linked = _authorized_attempt(
        project_root, schema_root, tmp_path
    )
    output_source = tmp_path / "runtime-output"
    output_source.mkdir()
    (output_source / "result.json").write_bytes(b'{"estimate":1.25}\n')
    runtime = _FakeExecutionRuntime(
        registry_root=authorization.registry_root,  # type: ignore[attr-defined]
        output_source=output_source,
        **runtime_options,
    )
    evidence = execute_registered_podman_attempt(
        authorization.registry_root,  # type: ignore[attr-defined]
        capability,
        schema_root,
        executable=executable,
        snapshot_root=tmp_path / "snapshot-materialized",
        started_at="2026-07-29T20:01:00Z",
        finished_at="2026-07-29T20:02:00Z",
        runtime=runtime,
        max_log_bytes=64,
    )
    assert linked == authorization.linked_output_root  # type: ignore[attr-defined]
    return evidence, runtime


def test_successful_attempt_claims_before_runtime_and_captures_untrusted_bytes(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, runtime = _run(project_root, schema_root, tmp_path)

    assert evidence.disposition == "completed"  # type: ignore[attr-defined]
    assert evidence.output_manifest["total_logical_bytes"] == 18  # type: ignore[attr-defined]
    assert evidence.clean_control_eligible is False  # type: ignore[attr-defined]
    assert (evidence.accepted_output_root / "result.json").read_bytes() == (  # type: ignore[attr-defined]
        b'{"estimate":1.25}\n'
    )
    assert runtime.calls[0][1:3] == ("image", "inspect")
    assert (
        evidence.attempt_root.parents[1] / "control" / "execution-snapshot" / "analysis.py"
    ).read_bytes() == _ANALYSIS_BYTES  # type: ignore[attr-defined]


def test_complete_resource_observations_make_synthetic_attempt_clean_control_eligible(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(project_root, schema_root, tmp_path, observe_resources=True)

    assert evidence.clean_control_eligible is True  # type: ignore[attr-defined]
    locked = json.loads(evidence.semantic_lock_path.read_text(encoding="utf-8"))  # type: ignore[attr-defined]
    execution = locked["executions"][0]
    assert execution["project_execution"]["observed_resources"] == {
        "cpu_time_seconds": 0.25,
        "open_files_peak": 8,
        "peak_memory_bytes": 33_554_432,
        "process_count_peak": 2,
        "written_bytes": 18,
    }
    assert locked["environments"][0]["identity_status"] == "exact"
    assert not any("unavailable" in value for value in execution["limitations"])


def test_observed_resource_overage_blocks_clean_control(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(
        project_root,
        schema_root,
        tmp_path,
        observe_resources=True,
        exceed_resources=True,
    )

    assert evidence.disposition == "completed"  # type: ignore[attr-defined]
    assert evidence.clean_control_eligible is False  # type: ignore[attr-defined]
    assert any(
        "exceeded the authorization envelope" in value
        for value in evidence.limitations  # type: ignore[attr-defined]
    )


def test_attempt_publishes_replayable_linked_lock_and_nonaccusatory_bundle(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(project_root, schema_root, tmp_path)
    linked_root = evidence.attempt_root.parents[1]  # type: ignore[attr-defined]
    lock_path = linked_root / "semantic.lock.json"
    bundle_path = linked_root / "audit.bundle.json"

    locked = json.loads(lock_path.read_text(encoding="utf-8"))
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert locked["lock_kind"] == "linked_project_execution_v1"
    assert locked["model_calls"] == []
    assert locked["model_access_after_lock"] is False
    assert len(locked["executions"]) == 1
    assert (
        locked["executions"][0]["project_execution"]["work_item_ref"]
        == locked["source_work_item_ref"]
    )
    assert bundle["semantic_lock_digest"] == locked["semantic_lock_digest"]
    assert bundle["findings"] == []
    assert bundle["conditional_concerns"] == []
    assert len(bundle["project_execution_authorizations"]) == 1
    assert len(bundle["executions"]) == 1
    assert bundle["executions"][0]["limitations"]

    replayed = replay(lock_path, tmp_path / "execution-replay", schema_root)
    assert replayed["executions"] == bundle["executions"]
    assert (
        replayed["project_execution_authorizations"] == bundle["project_execution_authorizations"]
    )
    assert replayed["findings"] == []
    assert (tmp_path / "execution-replay" / "accepted-output" / "result.json").read_bytes() == (
        b'{"estimate":1.25}\n'
    )


def test_v14_closure_inspector_is_read_only_and_preserves_explicit_gaps(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, runtime = _run(project_root, schema_root, tmp_path, observe_resources=True)
    calls_before = list(runtime.calls)

    inspection = inspect_linked_execution_v14(evidence.semantic_lock_path, schema_root)  # type: ignore[attr-defined]

    assert (
        inspection.semantic_lock_digest
        == json.loads(
            evidence.semantic_lock_path.read_text(encoding="utf-8")  # type: ignore[attr-defined]
        )["semantic_lock_digest"]
    )
    assert len(inspection.public_record_digests) == 23
    assert {item[0] for item in inspection.source_record_digests} == {
        "repository_snapshot",
        "work_item",
    }
    assert len(inspection.retained_artifact_byte_digests) == 9
    assert len(inspection.coverage_limitations) == 3
    assert any(
        "no public dependency-inventory record" in item for item in inspection.coverage_limitations
    )
    assert any("does not establish" in item for item in inspection.coverage_limitations)
    assert runtime.calls == calls_before


def _rewrite_linked_lock(path: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    lock = json.loads(path.read_text(encoding="utf-8"))
    mutate(lock)
    lock.pop("semantic_lock_digest")
    lock["semantic_lock_digest"] = semantic_digest(lock)
    path.write_text(canonical_json(lock) + "\n", encoding="utf-8")


def _remove_source_lock_artifact(lock: dict[str, Any]) -> None:
    artifact = next(
        item
        for item in lock["artifacts"]
        if item["observed_role"] == "exact registered source semantic lock"
    )
    identity_id = artifact["asset_identity_ref"]["record_id"]
    lock["artifacts"].remove(artifact)
    lock["asset_identities"] = [
        item for item in lock["asset_identities"] if item["asset_identity_id"] != identity_id
    ]


def _substitute_artifact_identity_digest(lock: dict[str, Any]) -> None:
    identity = lock["asset_identities"][0]
    identity["identity_evidence"]["digest"] = "sha256:" + "0" * 64


def _substitute_environment_reference(lock: dict[str, Any]) -> None:
    lock["executions"][0]["environment_ref"]["record_id"] = "environment:substituted"


def _duplicate_artifact(lock: dict[str, Any]) -> None:
    lock["artifacts"].append(copy.deepcopy(lock["artifacts"][0]))


def _drop_output_reference(lock: dict[str, Any]) -> None:
    lock["executions"][0]["output_refs"] = []


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (_remove_source_lock_artifact, "artifact role"),
        (_substitute_artifact_identity_digest, "source reference disagrees"),
        (_substitute_environment_reference, "does not bind its Environment"),
        (_duplicate_artifact, "duplicate Artifact"),
        (_drop_output_reference, "missing or extra roles"),
    ),
)
def test_v14_closure_inspector_rejects_rehashed_dependency_mutation(
    mutate: Callable[[dict[str, Any]], None],
    message: str,
    project_root: Path,
    schema_root: Path,
    tmp_path: Path,
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(project_root, schema_root, tmp_path)
    lock_path = evidence.semantic_lock_path  # type: ignore[attr-defined]
    _rewrite_linked_lock(lock_path, mutate)

    with pytest.raises(ValueError, match=message):
        inspect_linked_execution_v14(lock_path, schema_root)


def test_v14_closure_inspector_rejects_externally_linked_retained_bytes(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(project_root, schema_root, tmp_path)
    retained_output = evidence.attempt_root.parents[1] / "accepted-output" / "result.json"  # type: ignore[attr-defined]
    os.link(retained_output, tmp_path / "external-output-alias.json")

    with pytest.raises(ValueError, match="external hard links"):
        inspect_linked_execution_v14(evidence.semantic_lock_path, schema_root)  # type: ignore[attr-defined]


def test_v14_closure_inspector_rejects_symlinked_retained_ancestor(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(project_root, schema_root, tmp_path)
    linked_root = evidence.attempt_root.parents[1]  # type: ignore[attr-defined]
    accepted_output = linked_root / "accepted-output"
    moved_output = linked_root / "accepted-output-moved"
    accepted_output.rename(moved_output)
    accepted_output.symlink_to(moved_output, target_is_directory=True)

    with pytest.raises(ValueError, match="contains a symlink"):
        inspect_linked_execution_v14(evidence.semantic_lock_path, schema_root)  # type: ignore[attr-defined]


def test_v14_closure_inspector_rejects_reidentified_source_lock_semantic_drift(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(project_root, schema_root, tmp_path)
    linked_root = evidence.attempt_root.parents[1]  # type: ignore[attr-defined]
    lock_path = evidence.semantic_lock_path  # type: ignore[attr-defined]
    source_lock_path = (
        linked_root / "control" / "authorization-registry" / "source-semantic.lock.json"
    )
    source_lock = json.loads(source_lock_path.read_text(encoding="utf-8"))
    source_lock["work_items"][0]["status"] = "blocked"
    source_lock.pop("semantic_lock_digest")
    source_lock["semantic_lock_digest"] = semantic_digest(source_lock)
    source_payload = (canonical_json(source_lock) + "\n").encode()
    source_lock_path.write_bytes(source_payload)

    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    artifact = next(
        item
        for item in lock["artifacts"]
        if item["observed_role"] == "exact registered source semantic lock"
    )
    old_identity_id = artifact["asset_identity_ref"]["record_id"]
    identity = next(
        item for item in lock["asset_identities"] if item["asset_identity_id"] == old_identity_id
    )
    digest = sha256_digest(source_payload)
    identity["identity_evidence"]["digest"] = digest
    identity["asset_identity_id"] = stable_id(
        "asset-identity",
        identity["audit_run_id"],
        "artifact",
        artifact["artifact_id"],
        "full_digest",
        semantic_digest(identity["identity_evidence"]),
    )
    artifact["asset_identity_ref"]["record_id"] = identity["asset_identity_id"]
    artifact["source_refs"][0]["content_digest"] = digest
    lock.pop("semantic_lock_digest")
    lock["semantic_lock_digest"] = semantic_digest(lock)
    lock_path.write_text(canonical_json(lock) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="source semantic-lock digest is inconsistent"):
        inspect_linked_execution_v14(lock_path, schema_root)


@pytest.mark.parametrize("drift", ["changed_bytes", "unexpected_file"])
def test_snapshot_drift_prevents_claim_and_every_runtime_call(
    project_root: Path, schema_root: Path, tmp_path: Path, drift: str
) -> None:
    authorization, executable, capability, _linked = _authorized_attempt(
        project_root, schema_root, tmp_path
    )
    snapshot_root = _materialize_snapshot(tmp_path)
    if drift == "changed_bytes":
        (snapshot_root / "analysis.py").write_bytes(b"changed\n")
    else:
        (snapshot_root / "extra.txt").write_text("extra\n", encoding="utf-8")
    output_source = tmp_path / "runtime-output"
    output_source.mkdir()
    runtime = _FakeExecutionRuntime(
        registry_root=authorization.registry_root,  # type: ignore[attr-defined]
        output_source=output_source,
    )

    with pytest.raises(ValueError, match="snapshot materialization"):
        execute_registered_podman_attempt(
            authorization.registry_root,  # type: ignore[attr-defined]
            capability,
            schema_root,
            executable=executable,
            snapshot_root=snapshot_root,
            started_at="2026-07-29T20:01:00Z",
            finished_at="2026-07-29T20:02:00Z",
            runtime=runtime,
        )

    assert runtime.calls == []
    assert not authorization.consumption_receipt_path.exists()  # type: ignore[attr-defined]


def test_replay_rejects_drifted_linked_artifact_without_runtime(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, runtime = _run(project_root, schema_root, tmp_path)
    before_calls = list(runtime.calls)
    linked_root = evidence.attempt_root.parents[1]  # type: ignore[attr-defined]
    (linked_root / "accepted-output" / "result.json").write_bytes(b"tampered\n")

    with pytest.raises(ValueError, match="drifted"):
        replay(
            linked_root / "semantic.lock.json",
            tmp_path / "tampered-replay",
            schema_root,
        )
    assert runtime.calls == before_calls


def test_runtime_start_failure_still_consumes_authorization(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(project_root, schema_root, tmp_path, create_exit=125)

    assert evidence.disposition == "failed_runtime_start"  # type: ignore[attr-defined]
    assert evidence.consumption_receipt_path.is_file()  # type: ignore[attr-defined]
    assert evidence.consumption_terminal_path.is_file()  # type: ignore[attr-defined]


def test_timeout_kills_and_cleans_but_cannot_be_clean_control(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, runtime = _run(project_root, schema_root, tmp_path, timed_out=True)

    assert evidence.disposition == "timed_out"  # type: ignore[attr-defined]
    assert evidence.clean_control_eligible is False  # type: ignore[attr-defined]
    assert any(call[1] == "kill" for call in runtime.calls)


def test_log_truncation_is_retained_and_blocks_clean_control(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(project_root, schema_root, tmp_path, truncate_logs=True)

    assert evidence.disposition == "completed"  # type: ignore[attr-defined]
    assert evidence.logs["stdout"]["truncated"] is True  # type: ignore[attr-defined]
    assert evidence.clean_control_eligible is False  # type: ignore[attr-defined]


def test_cleanup_failure_is_terminal_and_outputs_are_not_accepted(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, _runtime = _run(project_root, schema_root, tmp_path, cleanup_succeeds=False)

    assert evidence.disposition == "cleanup_failed"  # type: ignore[attr-defined]
    assert evidence.accepted_output_root is None  # type: ignore[attr-defined]


def test_unexpected_post_create_failure_attempts_emergency_cleanup(
    project_root: Path, schema_root: Path, tmp_path: Path
) -> None:
    _materialize_snapshot(tmp_path)
    evidence, runtime = _run(project_root, schema_root, tmp_path, raise_on_start=True)

    assert evidence.disposition == "controller_failed_unknown"  # type: ignore[attr-defined]
    assert evidence.cleanup_observed is True  # type: ignore[attr-defined]
    assert any(call[1] == "kill" for call in runtime.calls)
    assert any(call[1:3] == ("rm", "--force") for call in runtime.calls)


def test_subprocess_adapter_drains_but_bounds_auditor_owned_test_logs(tmp_path: Path) -> None:
    runtime = SubprocessExecutionRuntime()
    stdout = tmp_path / "stdout.log"
    stderr = tmp_path / "stderr.log"

    result = runtime.start_attached(
        (
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('x'*4096); sys.stderr.write('y'*4096)",
        ),
        timeout_seconds=5,
        stdout_path=stdout,
        stderr_path=stderr,
        max_log_bytes=64,
    )

    assert result.exit_code == 0
    assert result.stdout_observed_bytes == 4096
    assert result.stderr_observed_bytes == 4096
    assert result.stdout_truncated is True
    assert result.stderr_truncated is True
    assert stdout.read_bytes() == b"x" * 64
    assert stderr.read_bytes() == b"y" * 64


def test_subprocess_adapter_enforces_wall_timeout_on_auditor_owned_test_code(
    tmp_path: Path,
) -> None:
    result = SubprocessExecutionRuntime().start_attached(
        (sys.executable, "-c", "import time; time.sleep(5)"),
        timeout_seconds=1,
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
        max_log_bytes=64,
    )

    assert result.timed_out is True
    assert result.exit_code is None
