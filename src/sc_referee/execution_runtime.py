from __future__ import annotations

import hashlib
import json
import os
import selectors
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO, Protocol, cast

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.execution_authorization import (
    ClaimBindings,
    _read_canonical_object,
    claim_authorization,
    finalize_claim,
    read_registered_source_lock,
)
from sc_referee.execution_envelope import (
    ExecutionEnvelopeError,
    build_podman_execution_argv,
    capture_stopped_container_outputs,
)
from sc_referee.execution_evidence import publish_linked_execution_evidence
from sc_referee.execution_probe import CommandResult, SubprocessCommandRunner
from sc_referee.execution_resources import (
    AttachedResourceObserver,
    ResourceObservation,
    UnavailableResourceObserver,
    observer_for_attached_command,
    observer_for_capability_attached_command,
)
from sc_referee.execution_snapshot import stage_verified_snapshot
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.storage.atomic import atomic_create_bytes, fsync_directory


@dataclass(frozen=True)
class AttachedProcessResult:
    exit_code: int | None
    timed_out: bool
    stdout_observed_bytes: int
    stderr_observed_bytes: int
    stdout_retained_bytes: int
    stderr_retained_bytes: int
    stdout_truncated: bool
    stderr_truncated: bool
    error: str | None = None
    cpu_time_seconds: float | None = None
    peak_memory_bytes: int | None = None
    process_count_peak: int | None = None
    open_files_peak: int | None = None
    resource_observation_profile: str = "unavailable"
    resource_observation_limitations: tuple[str, ...] = ()


class ExecutionRuntime(Protocol):
    def run(self, argv: tuple[str, ...], *, timeout_seconds: int) -> CommandResult: ...

    def start_attached(
        self,
        argv: tuple[str, ...],
        *,
        timeout_seconds: int,
        stdout_path: Path,
        stderr_path: Path,
        max_log_bytes: int,
    ) -> AttachedProcessResult: ...


class SubprocessExecutionRuntime:
    """Shell-free runtime adapter with bounded retained logs and full pipe draining."""

    def __init__(
        self,
        *,
        observer_factory: Callable[[tuple[str, ...]], AttachedResourceObserver] | None = None,
    ) -> None:
        self._control = SubprocessCommandRunner()
        self._observer_factory = observer_factory or observer_for_attached_command

    def run(self, argv: tuple[str, ...], *, timeout_seconds: int) -> CommandResult:
        return self._control.run(argv, timeout_seconds=timeout_seconds)

    def start_attached(
        self,
        argv: tuple[str, ...],
        *,
        timeout_seconds: int,
        stdout_path: Path,
        stderr_path: Path,
        max_log_bytes: int,
    ) -> AttachedProcessResult:
        if max_log_bytes < 0:
            raise ValueError("retained log limit must be nonnegative")
        if stdout_path.exists() or stdout_path.is_symlink():
            raise FileExistsError(f"stdout log already exists: {stdout_path}")
        if stderr_path.exists() or stderr_path.is_symlink():
            raise FileExistsError(f"stderr log already exists: {stderr_path}")
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_descriptor = os.open(stdout_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        stderr_descriptor = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            try:
                process = subprocess.Popen(
                    argv,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
                )
            except OSError as error:
                return AttachedProcessResult(None, False, 0, 0, 0, 0, False, False, str(error))
            if process.stdout is None or process.stderr is None:
                process.kill()
                process.wait()
                return AttachedProcessResult(
                    None, False, 0, 0, 0, 0, False, False, "runtime pipes unavailable"
                )
            observer: AttachedResourceObserver
            try:
                observer = self._observer_factory(argv)
                observer.start()
            except (OSError, RuntimeError, ValueError) as error:
                observer = UnavailableResourceObserver(
                    f"The attached resource observer could not start: {error}"
                )
                observer.start()
            streams = {
                process.stdout: [stdout_descriptor, 0, 0],
                process.stderr: [stderr_descriptor, 0, 0],
            }
            selector = selectors.DefaultSelector()
            for stream in streams:
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ)
            deadline = time.monotonic() + timeout_seconds
            timed_out = False
            observation = ResourceObservation(None, None, None, None, "unavailable", ())
            try:
                while selector.get_map():
                    if not timed_out and time.monotonic() >= deadline:
                        timed_out = True
                        process.kill()
                    for key, _mask in selector.select(timeout=0.05):
                        stream = cast(BinaryIO, key.fileobj)
                        try:
                            chunk = os.read(stream.fileno(), 64 * 1024)
                        except BlockingIOError:
                            continue
                        if not chunk:
                            selector.unregister(stream)
                            continue
                        descriptor, observed, retained = streams[stream]
                        observed += len(chunk)
                        remaining = max(0, max_log_bytes - retained)
                        if remaining:
                            retained_chunk = chunk[:remaining]
                            view = memoryview(retained_chunk)
                            while view:
                                written = os.write(descriptor, view)
                                view = view[written:]
                            retained += len(retained_chunk)
                        streams[stream] = [descriptor, observed, retained]
                    if process.poll() is not None and not selector.get_map():
                        break
                exit_code = process.wait()
            finally:
                try:
                    observation = observer.finish()
                except (OSError, RuntimeError, ValueError) as error:
                    observation = ResourceObservation(
                        None,
                        None,
                        None,
                        None,
                        "unavailable",
                        (f"The attached resource observer could not finish: {error}",),
                    )
            stdout_observed = streams[process.stdout][1]
            stdout_retained = streams[process.stdout][2]
            stderr_observed = streams[process.stderr][1]
            stderr_retained = streams[process.stderr][2]
            return AttachedProcessResult(
                exit_code=None if timed_out else exit_code,
                timed_out=timed_out,
                stdout_observed_bytes=stdout_observed,
                stderr_observed_bytes=stderr_observed,
                stdout_retained_bytes=stdout_retained,
                stderr_retained_bytes=stderr_retained,
                stdout_truncated=stdout_observed > stdout_retained,
                stderr_truncated=stderr_observed > stderr_retained,
                cpu_time_seconds=observation.cpu_time_seconds,
                peak_memory_bytes=observation.peak_memory_bytes,
                process_count_peak=observation.process_count_peak,
                open_files_peak=observation.open_files_peak,
                resource_observation_profile=observation.profile,
                resource_observation_limitations=observation.limitations,
            )
        finally:
            os.fsync(stdout_descriptor)
            os.fsync(stderr_descriptor)
            os.close(stdout_descriptor)
            os.close(stderr_descriptor)


@dataclass(frozen=True)
class ExecutionAttemptEvidence:
    attempt_root: Path
    evidence_path: Path
    consumption_receipt_path: Path
    consumption_terminal_path: Path
    disposition: str
    exit_code: int | None
    timed_out: bool
    cleanup_observed: bool
    clean_control_eligible: bool
    logs: dict[str, dict[str, object]]
    output_manifest: dict[str, object] | None
    accepted_output_root: Path | None
    limitations: tuple[str, ...]
    semantic_lock_path: Path
    bundle_path: Path
    sqlite_path: Path
    report_path: Path


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("execution timestamp requires a timezone")
    return parsed


def _record_event(events: list[dict[str, object]], event: str, **details: object) -> None:
    events.append({"event": event, **details})


def _exact_image_present(result: CommandResult, reference: str) -> bool:
    if result.exit_code != 0 or result.timed_out:
        return False
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        return False
    digest = reference.rsplit("@", maxsplit=1)[-1]
    repo_digests = value[0].get("RepoDigests")
    return (
        value[0].get("Digest") == digest
        and isinstance(repo_digests, list)
        and reference in repo_digests
    )


def _container_state(result: CommandResult) -> tuple[bool, int | None]:
    if result.exit_code != 0 or result.timed_out:
        return False, None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, None
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        return False, None
    state = value[0].get("State")
    if not isinstance(state, dict) or state.get("Running") is not False:
        return False, None
    exit_code = state.get("ExitCode")
    return True, exit_code if isinstance(exit_code, int) else None


def _log_projection(path: Path, result: AttachedProcessResult, stream: str) -> dict[str, object]:
    payload = path.read_bytes() if path.is_file() else b""
    observed = result.stdout_observed_bytes if stream == "stdout" else result.stderr_observed_bytes
    retained = result.stdout_retained_bytes if stream == "stdout" else result.stderr_retained_bytes
    truncated = result.stdout_truncated if stream == "stdout" else result.stderr_truncated
    return {
        "digest": sha256_digest(payload),
        "observed_bytes": observed,
        "path": path.name,
        "retained_bytes": retained,
        "truncated": truncated,
    }


def _preclaim_capability_check(
    capability: dict[str, object],
    authorization: dict[str, Any],
    executable: Path,
    schema_root: Path,
    started_at: str,
) -> None:
    LocalSchemaRegistry(schema_root).validate(capability)
    if (
        capability.get("project_code_execution_supported") is not True
        or capability.get("rootless_verified") is not True
        or capability.get("capability_evidence_status") != "complete_effective_probe"
    ):
        raise ValueError("bound capability is not eligible for project execution")
    scope = authorization.get("scope")
    if not isinstance(scope, dict) or semantic_digest(capability) != scope.get(
        "capability", {}
    ).get("semantic_digest"):
        raise ValueError("bound capability digest drifted before claim")
    evidence = capability.get("capability_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("bound capability evidence is unavailable")
    backend = evidence.get("backend")
    if not isinstance(backend, dict):
        raise ValueError("bound capability backend identity is unavailable")
    resolved_executable = executable.resolve()
    digest = "sha256:" + hashlib.sha256(resolved_executable.read_bytes()).hexdigest()
    if (
        backend.get("executable_path") != str(resolved_executable)
        or backend.get("executable_digest") != digest
    ):
        raise ValueError("container-runtime executable drifted from the bound capability")
    if _timestamp(started_at) > _timestamp(str(evidence.get("expires_at"))):
        raise ValueError("bound sandbox capability expired before claim")


def _claim_bindings(authorization: dict[str, Any], linked_output_root: Path) -> ClaimBindings:
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
        linked_output_root=linked_output_root,
    )


def execute_registered_podman_attempt(
    registry_root: Path,
    capability: dict[str, object],
    schema_root: Path,
    *,
    executable: Path,
    snapshot_root: Path,
    started_at: str | None = None,
    finished_at: str | None = None,
    runtime: ExecutionRuntime | None = None,
    max_log_bytes: int = 1_048_576,
    clock: Callable[[], datetime] | None = None,
) -> ExecutionAttemptEvidence:
    """Consume and execute one registered envelope; this has no CLI exposure before ADR-0014."""

    active_clock = clock or (lambda: datetime.now(UTC))
    active_started_at = started_at or active_clock().replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    authorization, _payload = _read_canonical_object(
        registry_root / "authorization.json", "authorization"
    )
    linked_output_root = registry_root.parents[1]
    LocalSchemaRegistry(schema_root).validate(authorization)
    if finished_at is not None and _timestamp(finished_at) < _timestamp(active_started_at):
        raise ValueError("execution finish time precedes its start time")
    if max_log_bytes < 0:
        raise ValueError("retained log limit must be nonnegative")
    _preclaim_capability_check(
        capability, authorization, executable, schema_root, active_started_at
    )
    source_lock = read_registered_source_lock(registry_root, authorization)
    execution_snapshot_root = stage_verified_snapshot(
        source_lock,
        authorization,
        snapshot_root,
        linked_output_root / "control" / "execution-snapshot",
        schema_root,
    )
    bindings = _claim_bindings(authorization, linked_output_root)
    receipt = claim_authorization(
        registry_root, bindings, schema_root, claimed_at=active_started_at
    )
    attempt_id = str(receipt["attempt_id"])
    attempt_root = linked_output_root / "attempts" / attempt_id.replace(":", "-")
    attempt_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    stdout_path = attempt_root / "stdout.log"
    stderr_path = attempt_root / "stderr.log"
    controller_events_path = attempt_root / "controller-events.json"
    evidence_path = attempt_root / "attempt-evidence.json"
    output_manifest_path = attempt_root / "output-manifest.json"
    terminal_path = registry_root / "consumption-terminal.json"
    active_runtime = runtime or SubprocessExecutionRuntime(
        observer_factory=lambda argv: observer_for_capability_attached_command(capability, argv)
    )
    events: list[dict[str, object]] = []
    command_results: list[CommandResult] = []
    process_result = AttachedProcessResult(None, False, 0, 0, 0, 0, False, False)
    output_manifest: dict[str, object] | None = None
    accepted_output_root: Path | None = None
    cleanup_observed = False
    container_created = False
    disposition = "controller_failed_unknown"
    limitations = [
        "Output bytes are untrusted evidence and do not establish scientific correctness.",
    ]
    container_name = f"sc-referee-execution-{attempt_id.split(':', maxsplit=1)[-1]}"
    try:
        _record_event(events, "authorization_consumed", attempt_id=attempt_id, at=active_started_at)
        image_reference = str(authorization["image"]["reference"])
        image_result = active_runtime.run(
            (str(executable.resolve()), "image", "inspect", image_reference, "--format", "json"),
            timeout_seconds=30,
        )
        command_results.append(image_result)
        if not _exact_image_present(image_result, image_reference):
            limitations.append("The already-present image identity did not match authorization.")
            disposition = "failed_runtime_start"
        else:
            create_argv = build_podman_execution_argv(
                executable.resolve(), authorization, execution_snapshot_root, container_name
            )
            create_result = active_runtime.run(create_argv, timeout_seconds=30)
            command_results.append(create_result)
            if create_result.exit_code != 0 or create_result.timed_out:
                limitations.append("The OCI runtime did not create the authorized sandbox.")
                disposition = "failed_runtime_start"
            else:
                container_created = True
                _record_event(events, "sandbox_created", at=active_started_at)
                process_result = active_runtime.start_attached(
                    (str(executable.resolve()), "start", "--attach", container_name),
                    timeout_seconds=int(authorization["limits"]["wall_time_seconds"]),
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    max_log_bytes=max_log_bytes,
                )
                if process_result.error is not None:
                    limitations.append(f"Runtime attach failed: {process_result.error}")
                    disposition = "failed_runtime_start"
                if process_result.timed_out:
                    kill_result = active_runtime.run(
                        (str(executable.resolve()), "kill", container_name), timeout_seconds=10
                    )
                    command_results.append(kill_result)
                    limitations.append("The authorized wall-time limit elapsed.")
                    disposition = "timed_out"
                inspect_result = active_runtime.run(
                    (
                        str(executable.resolve()),
                        "container",
                        "inspect",
                        container_name,
                        "--format",
                        "json",
                    ),
                    timeout_seconds=30,
                )
                command_results.append(inspect_result)
                quiescent, observed_exit = _container_state(inspect_result)
                staging_root = attempt_root / "staged-output"
                cp_succeeded = False
                if quiescent and not process_result.timed_out:
                    staging_root.mkdir(mode=0o700)
                    cp_result = active_runtime.run(
                        (
                            str(executable.resolve()),
                            "cp",
                            f"{container_name}:/output/.",
                            str(staging_root),
                        ),
                        timeout_seconds=30,
                    )
                    command_results.append(cp_result)
                    cp_succeeded = cp_result.exit_code == 0 and not cp_result.timed_out
                else:
                    limitations.append("Sandbox quiescence was not established for output capture.")
                rm_result = active_runtime.run(
                    (str(executable.resolve()), "rm", "--force", container_name),
                    timeout_seconds=30,
                )
                command_results.append(rm_result)
                exists_result = active_runtime.run(
                    (str(executable.resolve()), "container", "exists", container_name),
                    timeout_seconds=10,
                )
                command_results.append(exists_result)
                cleanup_observed = rm_result.exit_code == 0 and exists_result.exit_code == 1
                if cleanup_observed:
                    container_created = False
                if not cleanup_observed:
                    limitations.append("Sandbox removal was not established.")
                    disposition = "cleanup_failed"
                elif cp_succeeded:
                    try:
                        accepted_output_root = linked_output_root / "accepted-output"
                        output_manifest = capture_stopped_container_outputs(
                            staging_root,
                            accepted_output_root,
                            allowed_output_paths=tuple(
                                authorization["scope"]["allowed_output_paths"]
                            ),
                            logical_byte_limit=int(authorization["limits"]["writable_bytes"]),
                            project_processes_quiescent=quiescent,
                            cleanup_observed=cleanup_observed,
                        )
                        atomic_create_bytes(
                            output_manifest_path,
                            (canonical_json(output_manifest) + "\n").encode("utf-8"),
                        )
                    except (ExecutionEnvelopeError, FileExistsError, OSError) as error:
                        accepted_output_root = None
                        limitations.append(f"Output capture was rejected: {error}")
                        disposition = "output_rejected"
                if disposition == "controller_failed_unknown":
                    if process_result.timed_out:
                        disposition = "timed_out"
                    elif observed_exit is None:
                        disposition = "controller_failed_unknown"
                    elif observed_exit != 0:
                        limitations.append(f"Project process exited nonzero ({observed_exit}).")
                        disposition = "failed_nonzero_exit"
                    elif output_manifest is None:
                        disposition = "output_rejected"
                    else:
                        disposition = "completed"
    except (OSError, ValueError, KeyError, TypeError) as error:
        limitations.append(f"Controller attempt failed closed: {error}")
        disposition = "controller_failed_unknown"
        if container_created:
            try:
                kill_result = active_runtime.run(
                    (str(executable.resolve()), "kill", container_name), timeout_seconds=10
                )
                command_results.append(kill_result)
                rm_result = active_runtime.run(
                    (str(executable.resolve()), "rm", "--force", container_name),
                    timeout_seconds=30,
                )
                command_results.append(rm_result)
                exists_result = active_runtime.run(
                    (str(executable.resolve()), "container", "exists", container_name),
                    timeout_seconds=10,
                )
                command_results.append(exists_result)
                cleanup_observed = rm_result.exit_code == 0 and exists_result.exit_code == 1
            except (OSError, ValueError) as cleanup_error:
                limitations.append(f"Emergency sandbox cleanup failed: {cleanup_error}")
            if not cleanup_observed:
                disposition = "cleanup_failed"

    if not stdout_path.exists():
        atomic_create_bytes(stdout_path, b"")
    if not stderr_path.exists():
        atomic_create_bytes(stderr_path, b"")
    logs = {
        "stdout": _log_projection(stdout_path, process_result, "stdout"),
        "stderr": _log_projection(stderr_path, process_result, "stderr"),
    }
    if process_result.stdout_truncated or process_result.stderr_truncated:
        limitations.append(
            "At least one retained process log was truncated at the controller limit."
        )
    limitations.extend(process_result.resource_observation_limitations)
    _record_event(
        events,
        "resource_observation",
        profile=process_result.resource_observation_profile,
        limitations=list(process_result.resource_observation_limitations),
    )
    controller_events = {
        "commands": [result.evidence() for result in command_results],
        "events": events,
    }
    atomic_create_bytes(
        controller_events_path,
        (canonical_json(controller_events) + "\n").encode("utf-8"),
    )
    observed_resources = {
        "cpu_time_seconds": process_result.cpu_time_seconds,
        "open_files_peak": process_result.open_files_peak,
        "peak_memory_bytes": process_result.peak_memory_bytes,
        "process_count_peak": process_result.process_count_peak,
        "written_bytes": (
            output_manifest.get("total_logical_bytes") if output_manifest is not None else None
        ),
    }
    unavailable_observations = sorted(
        name for name, value in observed_resources.items() if value is None
    )
    if unavailable_observations:
        limitations.append(
            "Clean-control resource observations are unavailable: "
            + ", ".join(unavailable_observations)
            + "."
        )
    resource_observation_profile_eligible = (
        process_result.resource_observation_profile != "unavailable"
    )
    if not resource_observation_profile_eligible:
        limitations.append("A qualifying attached resource-observation profile is unavailable.")
    resource_limit_violations: list[str] = []
    observed_limit_pairs = (
        ("open_files_peak", "open_files"),
        ("peak_memory_bytes", "memory_bytes"),
        ("process_count_peak", "process_count"),
        ("written_bytes", "writable_bytes"),
    )
    for observed_name, limit_name in observed_limit_pairs:
        observed_value = observed_resources[observed_name]
        allowed_value = authorization["limits"][limit_name]
        if (
            isinstance(observed_value, int)
            and isinstance(allowed_value, int)
            and observed_value > allowed_value
        ):
            resource_limit_violations.append(f"{observed_name} exceeded authorized {limit_name}")
    if resource_limit_violations:
        limitations.append(
            "Observed resource use exceeded the authorization envelope: "
            + ", ".join(resource_limit_violations)
            + "."
        )
    clean_control_eligible = (
        disposition == "completed"
        and cleanup_observed
        and output_manifest is not None
        and not process_result.stdout_truncated
        and not process_result.stderr_truncated
        and not unavailable_observations
        and not resource_limit_violations
        and resource_observation_profile_eligible
    )
    active_finished_at = finished_at or active_clock().replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    if _timestamp(active_finished_at) < _timestamp(active_started_at):
        raise ValueError("execution finish time precedes its start time")
    evidence_record: dict[str, Any] = {
        "attempt_id": attempt_id,
        "authorization_semantic_digest": receipt["authorization_semantic_digest"],
        "cleanup_observed": cleanup_observed,
        "clean_control_eligible": clean_control_eligible,
        "disposition": disposition,
        "finished_at": active_finished_at,
        "logs": logs,
        "observed_exit_code": process_result.exit_code,
        "observed_resources": observed_resources,
        "output_manifest": output_manifest,
        "receipt_digest": receipt["receipt_digest"],
        "started_at": active_started_at,
        "timed_out": process_result.timed_out,
        "limitations": sorted(set(limitations)),
    }
    evidence_payload = (canonical_json(evidence_record) + "\n").encode("utf-8")
    atomic_create_bytes(evidence_path, evidence_payload)
    finalize_claim(
        registry_root,
        attempt_id=attempt_id,
        disposition=disposition,
        finalized_at=active_finished_at,
        evidence_digest=sha256_digest(evidence_payload),
        limitations=tuple(sorted(set(limitations))),
    )
    fsync_directory(attempt_root)
    publication = publish_linked_execution_evidence(
        linked_output_root=linked_output_root,
        registry_root=registry_root,
        capability=capability,
        schema_root=schema_root,
        attempt_root=attempt_root,
        evidence_path=evidence_path,
    )
    return ExecutionAttemptEvidence(
        attempt_root=attempt_root,
        evidence_path=evidence_path,
        consumption_receipt_path=registry_root / "consumption-receipt.json",
        consumption_terminal_path=terminal_path,
        disposition=disposition,
        exit_code=process_result.exit_code,
        timed_out=process_result.timed_out,
        cleanup_observed=cleanup_observed,
        clean_control_eligible=clean_control_eligible,
        logs=logs,
        output_manifest=output_manifest,
        accepted_output_root=accepted_output_root,
        limitations=tuple(sorted(set(limitations))),
        semantic_lock_path=publication.semantic_lock_path,
        bundle_path=publication.bundle_path,
        sqlite_path=publication.sqlite_path,
        report_path=publication.report_path,
    )
