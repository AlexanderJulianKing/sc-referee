from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.execution_capability import (
    EFFECTIVE_CONTROL_NAMES,
    ProbeLimits,
    ProbeObservation,
    compile_sandbox_capability,
    compile_unavailable_capability,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry
from sc_referee.storage.atomic import atomic_create_bytes, fsync_directory
from sc_referee.version import SCHEMA_VERSION, __version__

_MAX_COMMAND_OUTPUT_BYTES = 1_048_576
_PROBE_TMP_BYTES = 65_536

# This payload is owned and versioned by sc-referee. It observes only its container envelope and
# auditor-created probe inputs; it never imports or executes a file from an audited project.
_EFFECTIVE_PROBE_CODE = r"""
import json, os, resource, socket
from pathlib import Path

def first(paths):
    for path in paths:
        try:
            return Path(path).read_text(encoding="utf-8").strip()
        except OSError:
            pass
    return ""

def denied_write(path):
    try:
        Path(path).write_bytes(b"x")
    except OSError:
        return True
    return False

memory_limit = int(os.environ["SC_REFEREE_MEMORY_BYTES"])
cpu_millis = int(os.environ["SC_REFEREE_CPU_MILLIS"])
process_limit = int(os.environ["SC_REFEREE_PROCESS_COUNT"])
open_file_limit = int(os.environ["SC_REFEREE_OPEN_FILES"])
output_limit = int(os.environ["SC_REFEREE_OUTPUT_BYTES"])
status = Path("/proc/self/status").read_text(encoding="utf-8")
status_values = dict(
    line.split(":", 1) for line in status.splitlines() if ":" in line
)
memory_value = first(("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"))
pids_value = first(("/sys/fs/cgroup/pids.max", "/sys/fs/cgroup/pids/pids.max"))
cpu_value = first(("/sys/fs/cgroup/cpu.max", "/sys/fs/cgroup/cpu/cpu.cfs_quota_us"))
memory_ok = memory_value.isdigit() and int(memory_value) <= memory_limit
pids_ok = pids_value.isdigit() and int(pids_value) <= process_limit
cpu_ok = False
if " " in cpu_value:
    quota, period = cpu_value.split()[:2]
    cpu_ok = quota.isdigit() and period.isdigit() and int(quota) * 1000 <= cpu_millis * int(period)
elif cpu_value.isdigit():
    period = first(("/sys/fs/cgroup/cpu/cpu.cfs_period_us",))
    cpu_ok = period.isdigit() and int(cpu_value) * 1000 <= cpu_millis * int(period)
network_denied = False
try:
    connection = socket.create_connection(("1.1.1.1", 53), timeout=0.25)
    connection.close()
except OSError:
    network_denied = True
try:
    Path("/output/probe-ok.txt").write_text("ok", encoding="utf-8")
    writable_ok = True
except OSError:
    writable_ok = False
output_ok = False
try:
    with Path("/output/probe-fill.bin").open("wb", buffering=0) as handle:
        block = b"0" * 65536
        written = 0
        while written <= output_limit:
            handle.write(block)
            written += len(block)
except OSError:
    output_ok = written >= output_limit
allowed_devices = {"core", "fd", "full", "mqueue", "null", "ptmx", "pts", "random", "shm", "stderr", "stdin", "stdout", "tty", "urandom", "zero"}
device_ok = set(os.listdir("/dev")) <= allowed_devices
controls = {
    "capabilities_dropped": int(status_values.get("CapEff", "1").strip(), 16) == 0,
    "cpu_limit_enforced": cpu_ok,
    "device_access_restricted": device_ok,
    "memory_limit_enforced": memory_ok,
    "network_denied": network_denied,
    "no_new_privileges": status_values.get("NoNewPrivs", "0").strip() == "1",
    "open_file_limit_enforced": resource.getrlimit(resource.RLIMIT_NOFILE)[0] <= open_file_limit,
    "process_limit_enforced": pids_ok,
    "repository_read_only": denied_write("/project/probe-input.txt"),
    "separate_writable_root": writable_ok,
    "writable_bytes_enforced": output_ok,
}
print(json.dumps(controls, sort_keys=True, separators=(",", ":")))
""".strip()

_WALL_TIME_PROBE_CODE = "import time; time.sleep(3600)"


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool

    def evidence(self) -> dict[str, object]:
        return {
            "argv": list(self.argv),
            "exit_code": self.exit_code,
            "stderr": self.stderr,
            "stdout": self.stdout,
            "timed_out": self.timed_out,
        }


class CommandRunner(Protocol):
    def run(self, argv: tuple[str, ...], *, timeout_seconds: int) -> CommandResult: ...


class SubprocessCommandRunner:
    """Run controller-selected argv without a shell or inherited stdin."""

    def run(self, argv: tuple[str, ...], *, timeout_seconds: int) -> CommandResult:
        try:
            completed = subprocess.run(
                argv,
                check=False,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=timeout_seconds,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin"},
            )
        except subprocess.TimeoutExpired as error:
            return CommandResult(
                argv=argv,
                exit_code=None,
                stdout=_bounded_text(error.stdout),
                stderr=_bounded_text(error.stderr),
                timed_out=True,
            )
        return CommandResult(
            argv=argv,
            exit_code=completed.returncode,
            stdout=_bounded_text(completed.stdout),
            stderr=_bounded_text(completed.stderr),
            timed_out=False,
        )


@dataclass(frozen=True)
class CapabilityProbePackage:
    output_root: Path
    capability: dict[str, Any]
    log_artifact: dict[str, Any]
    log_asset_identity: dict[str, Any]
    transcript: dict[str, Any]


def write_unavailable_capability(
    output: Path, *, captured_at: str, reason: str, schema_root: Path
) -> dict[str, Any]:
    """Publish a bounded static-only capability result without probe or execution claims."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"capability probe output already exists: {output}")
    record = compile_unavailable_capability(captured_at=captured_at, reason=reason)
    LocalSchemaRegistry(schema_root).validate(record)
    output.mkdir(parents=True, exist_ok=False)
    atomic_create_bytes(
        output / "sandbox-capability.json", (canonical_json(record) + "\n").encode()
    )
    fsync_directory(output)
    return record


def _bounded_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    payload = value.encode("utf-8", errors="replace") if isinstance(value, str) else value
    return payload[:_MAX_COMMAND_OUTPUT_BYTES].decode("utf-8", errors="replace")


def _json_object(result: CommandResult) -> dict[str, Any] | None:
    if result.exit_code != 0 or result.timed_out:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _object(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _image_is_exact(result: CommandResult, reference: str) -> bool:
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


def _endpoint(info: dict[str, Any]) -> tuple[str, str, str, str | None, bool]:
    host = info.get("host")
    if not isinstance(host, dict):
        return "unbound_remote", "connection:unknown", "service:unknown", None, True
    remote_socket = host.get("remoteSocket")
    socket_path = remote_socket.get("path") if isinstance(remote_socket, dict) else None
    if not isinstance(socket_path, str):
        return "unbound_remote", "connection:unknown", "service:unknown", None, True
    if socket_path.startswith("unix://") or socket_path.startswith("/"):
        identity = sha256_digest(socket_path)
        return (
            "local_unix_socket",
            stable_id("connection", identity),
            stable_id("service", identity),
            None,
            False,
        )
    return (
        "unbound_remote",
        stable_id("connection", socket_path),
        stable_id("service", socket_path),
        None,
        True,
    )


def _selected_info(info: dict[str, Any]) -> dict[str, Any]:
    host = _object(info.get("host"))
    security = _object(host.get("security"))
    runtime = _object(host.get("ociRuntime"))
    endpoint = _endpoint(info)
    return {
        "arch": host.get("arch"),
        "endpoint": endpoint,
        "kernel": host.get("kernel"),
        "oci_runtime": {"name": runtime.get("name"), "version": runtime.get("version")},
        "os": host.get("os"),
        "rootless": security.get("rootless") is True,
        "version": info.get("version"),
    }


def _effective_controls(result: CommandResult) -> dict[str, bool]:
    value = _json_object(result)
    controls = {name: False for name in EFFECTIVE_CONTROL_NAMES}
    if value is None:
        return controls
    for name in EFFECTIVE_CONTROL_NAMES:
        if name == "wall_time_enforced":
            continue
        controls[name] = value.get(name) is True
    return controls


def _container_argv(
    executable: Path,
    *,
    name: str,
    image_reference: str,
    probe_root: Path,
    limits: ProbeLimits,
    code: str,
) -> tuple[str, ...]:
    output_bytes = limits.writable_bytes - _PROBE_TMP_BYTES
    if output_bytes < _PROBE_TMP_BYTES:
        raise ValueError(
            "writable-byte limit must reserve at least 64 KiB each for /tmp and /output"
        )
    return (
        str(executable),
        "create",
        f"--name={name}",
        "--pull=never",
        "--read-only",
        "--network=none",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--user=65532:65532",
        f"--pids-limit={limits.process_count}",
        f"--memory={limits.memory_bytes}",
        f"--cpus={limits.cpu_quota_millis / 1000:g}",
        f"--ulimit=nofile={limits.open_files}:{limits.open_files}",
        f"--tmpfs=/tmp:rw,size={_PROBE_TMP_BYTES},nosuid,nodev,noexec",
        f"--tmpfs=/output:rw,size={output_bytes},nosuid,nodev,noexec",
        f"--mount=type=bind,source={probe_root},destination=/project,ro=true",
        "--workdir=/project",
        f"--env=SC_REFEREE_MEMORY_BYTES={limits.memory_bytes}",
        f"--env=SC_REFEREE_CPU_MILLIS={limits.cpu_quota_millis}",
        f"--env=SC_REFEREE_PROCESS_COUNT={limits.process_count}",
        f"--env=SC_REFEREE_OPEN_FILES={limits.open_files}",
        f"--env=SC_REFEREE_OUTPUT_BYTES={output_bytes}",
        image_reference,
        "python3",
        "-c",
        code,
    )


def _run_container_probe(
    runner: CommandRunner,
    executable: Path,
    create_argv: tuple[str, ...],
    name: str,
    *,
    timeout_seconds: int,
    expect_timeout: bool,
) -> tuple[CommandResult, bool, list[CommandResult]]:
    transcript: list[CommandResult] = []
    created = runner.run(create_argv, timeout_seconds=30)
    transcript.append(created)
    if created.exit_code != 0 or created.timed_out:
        return created, False, transcript
    started = runner.run(
        (str(executable), "start", "--attach", name), timeout_seconds=timeout_seconds
    )
    transcript.append(started)
    if started.timed_out:
        killed = runner.run((str(executable), "kill", name), timeout_seconds=10)
        transcript.append(killed)
    removed = runner.run((str(executable), "rm", "--force", name), timeout_seconds=30)
    transcript.append(removed)
    expected_state = (
        started.timed_out if expect_timeout else (started.exit_code == 0 and not started.timed_out)
    )
    return started, expected_state and removed.exit_code == 0, transcript


def _artifact_records(
    *, audit_run_id: str, captured_at: str, transcript_digest: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    artifact_id = stable_id("artifact", "capability-probe-log", transcript_digest)
    identity_id = stable_id("asset-identity", artifact_id, transcript_digest)
    provenance = {
        "actor": {
            "actor_id": "software:sc-referee-controller",
            "actor_kind": "controller",
            "display_name": "sc-referee controller",
        },
        "created_at": captured_at,
        "method": "rootless_oci_capability_probe_v1",
        "tool": "sc-referee",
        "tool_version": __version__,
    }
    artifact = {
        "artifact_id": artifact_id,
        "asset_identity_ref": {"record_type": "asset_identity", "record_id": identity_id},
        "audit_run_id": audit_run_id,
        "consumer_operation_refs": [],
        "kind": "log",
        "limitations": ["The probe log describes auditor-owned capability verification only."],
        "observed_role": "rootless OCI capability probe transcript",
        "producer_operation_refs": [],
        "provenance": provenance,
        "record_type": "artifact",
        "schema_version": SCHEMA_VERSION,
        "source_refs": [
            {
                "locator": "internal:rootless-oci-capability-probe-v1",
                "source_kind": "runtime_command",
            }
        ],
    }
    identity = {
        "asset_identity_id": identity_id,
        "asset_ref": {"record_type": "artifact", "record_id": artifact_id},
        "audit_run_id": audit_run_id,
        "created_at": captured_at,
        "identity_evidence": {"kind": "full_digest", "digest": transcript_digest},
        "limitations": ["Identity covers the canonical retained capability-probe transcript."],
        "provenance": provenance,
        "record_type": "asset_identity",
        "schema_version": SCHEMA_VERSION,
        "tier": "full_digest",
    }
    return artifact, identity


def probe_podman_backend(
    executable: Path,
    image_reference: str,
    audit_run_id: str,
    output: Path,
    captured_at: str,
    expires_at: str,
    limits: ProbeLimits,
    schema_root: Path,
    *,
    runner: CommandRunner | None = None,
) -> CapabilityProbePackage:
    """Probe a local rootless Podman service with auditor-owned code and publish evidence."""

    if output.exists() or output.is_symlink():
        raise FileExistsError(f"capability probe output already exists: {output}")
    if not executable.is_file():
        raise ValueError(f"Podman executable is unavailable: {executable}")
    resolved_executable = executable.resolve()
    expected_image_digest = image_reference.rsplit("@", maxsplit=1)
    if len(expected_image_digest) != 2 or not expected_image_digest[1].startswith("sha256:"):
        raise ValueError("capability probe image must be digest-pinned")
    if len(expected_image_digest[1]) != 71:
        raise ValueError("capability probe image digest is malformed")
    output.mkdir(parents=True, exist_ok=False)
    probe_root = output / "auditor-probe-input"
    probe_root.mkdir()
    atomic_create_bytes(probe_root / "probe-input.txt", b"auditor-owned probe input\n")

    active_runner = runner or SubprocessCommandRunner()
    results: list[CommandResult] = []
    info_result = active_runner.run(
        (str(resolved_executable), "info", "--format", "json"), timeout_seconds=30
    )
    results.append(info_result)
    version_result = active_runner.run(
        (str(resolved_executable), "version", "--format", "json"), timeout_seconds=30
    )
    results.append(version_result)
    image_result = active_runner.run(
        (str(resolved_executable), "image", "inspect", image_reference, "--format", "json"),
        timeout_seconds=30,
    )
    results.append(image_result)

    info = _json_object(info_result) or {}
    selected_info = _selected_info(info)
    host = _object(info.get("host"))
    security = _object(host.get("security"))
    runtime = _object(host.get("ociRuntime"))
    transport, connection_id, service_id, machine_id, arbitrary_remote = _endpoint(info)
    rootless = security.get("rootless") is True
    image_exact = _image_is_exact(image_result, image_reference)
    version_ok = _json_object(version_result) is not None
    controls = {name: False for name in EFFECTIVE_CONTROL_NAMES}
    cleanup_ok = False
    identity_stable = False
    limitations = [
        "Only a local Unix-socket Podman service is supported by this initial probe profile.",
        "Host-kernel isolation is shared with the container runtime.",
    ]

    preflight_ok = rootless and not arbitrary_remote and image_exact and version_ok
    if preflight_ok:
        suffix = stable_id(
            "probe", audit_run_id, captured_at, image_reference, semantic_digest(selected_info)
        ).split(":", maxsplit=1)[1]
        main_name = f"sc-referee-probe-main-{suffix}"
        main_argv = _container_argv(
            resolved_executable,
            name=main_name,
            image_reference=image_reference,
            probe_root=probe_root.resolve(),
            limits=limits,
            code=_EFFECTIVE_PROBE_CODE,
        )
        main_result, cleanup_ok, main_transcript = _run_container_probe(
            active_runner,
            resolved_executable,
            main_argv,
            main_name,
            timeout_seconds=max(10, limits.wall_time_seconds),
            expect_timeout=False,
        )
        results.extend(main_transcript)
        controls.update(_effective_controls(main_result))

        wall_name = f"sc-referee-probe-wall-{suffix}"
        wall_argv = _container_argv(
            resolved_executable,
            name=wall_name,
            image_reference=image_reference,
            probe_root=probe_root.resolve(),
            limits=limits,
            code=_WALL_TIME_PROBE_CODE,
        )
        _wall_result, wall_ok, wall_transcript = _run_container_probe(
            active_runner,
            resolved_executable,
            wall_argv,
            wall_name,
            timeout_seconds=limits.wall_time_seconds,
            expect_timeout=True,
        )
        results.extend(wall_transcript)
        controls["wall_time_enforced"] = wall_ok

        post_info_result = active_runner.run(
            (str(resolved_executable), "info", "--format", "json"), timeout_seconds=30
        )
        results.append(post_info_result)
        post_info = _json_object(post_info_result)
        identity_stable = post_info is not None and _selected_info(post_info) == selected_info
    if not rootless:
        limitations.append("Podman service did not report rootless operation.")
    if arbitrary_remote:
        limitations.append("Podman endpoint is remote or is not a bound local Unix socket.")
    if not image_exact:
        limitations.append("Pinned probe image was absent or its inspected digest did not match.")
    if not version_ok:
        limitations.append("Podman version evidence was unavailable.")
    if preflight_ok and not cleanup_ok:
        limitations.append("Probe-container cleanup was not observed.")

    transcript: dict[str, Any] = {
        "commands": [result.evidence() for result in results],
        "image_reference": image_reference,
        "probe_profile": "rootless-oci-capability-probe-v1",
        "selected_backend_info": selected_info,
        "tested_limits": limits.public_record(),
    }
    transcript_payload = (canonical_json(transcript) + "\n").encode("utf-8")
    transcript_digest = sha256_digest(transcript_payload)
    log_artifact, log_identity = _artifact_records(
        audit_run_id=audit_run_id,
        captured_at=captured_at,
        transcript_digest=transcript_digest,
    )
    executable_digest = "sha256:" + hashlib.sha256(resolved_executable.read_bytes()).hexdigest()
    observation = ProbeObservation(
        backend_kind="podman_rootless",
        backend_name="Podman rootless",
        backend_version=str(_object(info.get("version")).get("Version", "unknown")),
        executable_path=str(resolved_executable),
        executable_digest=executable_digest,
        endpoint_transport=transport,
        connection_id=connection_id,
        service_id=service_id,
        machine_id=machine_id,
        arbitrary_remote=arbitrary_remote,
        normalized_info_digest=semantic_digest(selected_info),
        rootless_reported=rootless,
        probe_outcome=(
            "passed"
            if preflight_ok and cleanup_ok and identity_stable and all(controls.values())
            else "failed"
        ),
        effective_controls=controls,
        tested_limits=limits,
        host_system=str(host.get("os", "unknown")),
        host_release=str(host.get("kernel", "unknown")),
        host_machine=str(host.get("arch", "unknown")),
        oci_runtime_name=str(runtime.get("name", "unknown")),
        oci_runtime_version=str(runtime.get("version", "unknown")),
        probe_log_ref={
            "record_type": "artifact",
            "record_id": log_artifact["artifact_id"],
        },
        probe_artifact_digest=transcript_digest,
        captured_at=captured_at,
        expires_at=expires_at,
        limitations=tuple(limitations),
        machine_identity_stable=identity_stable,
        evidence_fresh=True,
    )
    capability = compile_sandbox_capability(observation)
    registry = LocalSchemaRegistry(schema_root)
    registry.validate(log_artifact)
    registry.validate(log_identity)
    registry.validate(capability)
    atomic_create_bytes(output / "probe-transcript.json", transcript_payload)
    atomic_create_bytes(
        output / "probe-log.artifact.json", (canonical_json(log_artifact) + "\n").encode()
    )
    atomic_create_bytes(
        output / "probe-log.asset-identity.json",
        (canonical_json(log_identity) + "\n").encode(),
    )
    atomic_create_bytes(
        output / "sandbox-capability.json", (canonical_json(capability) + "\n").encode()
    )
    fsync_directory(output)
    return CapabilityProbePackage(output, capability, log_artifact, log_identity, transcript)
