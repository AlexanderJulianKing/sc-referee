from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sc_referee.core.errors import RecordValidationError
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest
from sc_referee.execution_capability import (
    EFFECTIVE_CONTROL_NAMES,
    PROBE_PROFILE,
    ProbeLimits,
    ProbeObservation,
    compile_sandbox_capability,
)
from sc_referee.execution_probe import (
    _EFFECTIVE_PROBE_CODE,
    _WALL_TIME_PROBE_CODE,
    CommandResult,
    _artifact_records,
    _container_argv,
    _effective_controls,
    _endpoint,
    _image_is_exact,
    _json_object,
    _object,
    _selected_info,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry

_ROOT_FILES = frozenset(
    {
        "probe-log.artifact.json",
        "probe-log.asset-identity.json",
        "probe-transcript.json",
        "sandbox-capability.json",
    }
)
_PROBE_INPUT_DIRECTORY = "auditor-probe-input"
_PROBE_INPUT_FILE = "probe-input.txt"
_PROBE_INPUT_BYTES = b"auditor-owned probe input\n"
_MAX_RECORD_BYTES = 1_048_576
_MAX_TRANSCRIPT_BYTES = 32 * 1_048_576
_EXPECTED_COMMAND_COUNT = 11
_BASE_LIMITATIONS = (
    "Only a local Unix-socket Podman service is supported by this initial probe profile.",
    "Host-kernel isolation is shared with the container runtime.",
)


class CapabilityProbePackageError(ValueError):
    """A retained capability-probe package is malformed or internally inconsistent."""


@dataclass(frozen=True)
class VerifiedCapabilityProbeStructure:
    """Read-only structural result with no execution-admission authority.

    A successful result proves only that retained v0.14 bytes are canonical and internally
    consistent with the v0.14 compiler. A fully fabricated package can satisfy these checks.
    Trusted launch origin remains unavailable until ADR-0016 is accepted and implemented.
    """

    package_root: Path
    capability: dict[str, Any]
    log_artifact: dict[str, Any]
    log_asset_identity: dict[str, Any]
    transcript: dict[str, Any]
    transcript_digest: str


def _read_regular_file(directory_fd: int, name: str, *, maximum_bytes: int) -> bytes:
    before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        raise CapabilityProbePackageError(f"package entry is not a regular file: {name}")
    if before.st_nlink != 1:
        raise CapabilityProbePackageError(f"package file has external hard links: {name}")
    if before.st_size > maximum_bytes:
        raise CapabilityProbePackageError(f"package file exceeds its byte limit: {name}")

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    file_fd = os.open(name, flags, dir_fd=directory_fd)
    try:
        opened = os.fstat(file_fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise CapabilityProbePackageError(f"package file changed while opening: {name}")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            chunk = os.read(file_fd, min(remaining, 65_536))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        after = os.fstat(file_fd)
    finally:
        os.close(file_fd)
    if len(payload) > maximum_bytes:
        raise CapabilityProbePackageError(f"package file exceeds its byte limit: {name}")
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
        opened.st_dev,
        opened.st_ino,
        opened.st_size,
        opened.st_mtime_ns,
    ) or len(payload) != opened.st_size:
        raise CapabilityProbePackageError(f"package file changed while reading: {name}")
    return payload


def _read_closed_inventory(root: Path) -> dict[str, bytes]:
    try:
        root_status = root.lstat()
    except OSError as error:
        raise CapabilityProbePackageError(f"capability package is unavailable: {root}") from error
    if not stat.S_ISDIR(root_status.st_mode) or root.is_symlink():
        raise CapabilityProbePackageError("capability package root must be a real directory")

    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    root_fd = os.open(root, directory_flags)
    try:
        opened_root = os.fstat(root_fd)
        if (opened_root.st_dev, opened_root.st_ino) != (
            root_status.st_dev,
            root_status.st_ino,
        ):
            raise CapabilityProbePackageError("capability package changed while opening")
        root_entries = set(os.listdir(root_fd))
        expected_root_entries = _ROOT_FILES | {_PROBE_INPUT_DIRECTORY}
        if root_entries != expected_root_entries:
            raise CapabilityProbePackageError(
                "capability package inventory mismatch: "
                f"expected {sorted(expected_root_entries)!r}, got {sorted(root_entries)!r}"
            )
        payloads = {
            name: _read_regular_file(
                root_fd,
                name,
                maximum_bytes=(
                    _MAX_TRANSCRIPT_BYTES if name == "probe-transcript.json" else _MAX_RECORD_BYTES
                ),
            )
            for name in sorted(_ROOT_FILES)
        }

        input_status = os.stat(_PROBE_INPUT_DIRECTORY, dir_fd=root_fd, follow_symlinks=False)
        if not stat.S_ISDIR(input_status.st_mode):
            raise CapabilityProbePackageError("auditor probe input must be a real directory")
        input_fd = os.open(_PROBE_INPUT_DIRECTORY, directory_flags, dir_fd=root_fd)
        try:
            opened_input = os.fstat(input_fd)
            if (opened_input.st_dev, opened_input.st_ino) != (
                input_status.st_dev,
                input_status.st_ino,
            ):
                raise CapabilityProbePackageError("auditor probe input changed while opening")
            if set(os.listdir(input_fd)) != {_PROBE_INPUT_FILE}:
                raise CapabilityProbePackageError("auditor probe input inventory mismatch")
            payloads[f"{_PROBE_INPUT_DIRECTORY}/{_PROBE_INPUT_FILE}"] = _read_regular_file(
                input_fd, _PROBE_INPUT_FILE, maximum_bytes=1_024
            )
        finally:
            os.close(input_fd)
    finally:
        os.close(root_fd)
    return payloads


def _canonical_object(payload: bytes, *, name: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CapabilityProbePackageError(f"package JSON is invalid: {name}") from error
    if not isinstance(value, dict):
        raise CapabilityProbePackageError(f"package JSON must be an object: {name}")
    if payload != (canonical_json(value) + "\n").encode("utf-8"):
        raise CapabilityProbePackageError(f"package JSON is not canonical: {name}")
    return value


def _command_result(value: object, *, index: int) -> CommandResult:
    if not isinstance(value, dict) or set(value) != {
        "argv",
        "exit_code",
        "stderr",
        "stdout",
        "timed_out",
    }:
        raise CapabilityProbePackageError(f"probe command {index} has an invalid shape")
    argv = value.get("argv")
    exit_code = value.get("exit_code")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
        raise CapabilityProbePackageError(f"probe command {index} has invalid argv")
    if exit_code is not None and (not isinstance(exit_code, int) or isinstance(exit_code, bool)):
        raise CapabilityProbePackageError(f"probe command {index} has invalid exit code")
    if not isinstance(value.get("stdout"), str) or not isinstance(value.get("stderr"), str):
        raise CapabilityProbePackageError(f"probe command {index} has invalid output")
    if not isinstance(value.get("timed_out"), bool):
        raise CapabilityProbePackageError(f"probe command {index} has invalid timeout state")
    return CommandResult(
        argv=tuple(argv),
        exit_code=exit_code,
        stdout=value["stdout"],
        stderr=value["stderr"],
        timed_out=value["timed_out"],
    )


def _container_name(argv: tuple[str, ...], *, index: int) -> str:
    names = [item.removeprefix("--name=") for item in argv if item.startswith("--name=")]
    if len(names) != 1 or not names[0]:
        raise CapabilityProbePackageError(f"probe create command {index} has invalid name")
    return names[0]


def _probe_root(argv: tuple[str, ...], *, index: int) -> Path:
    prefix = "--mount=type=bind,source="
    suffix = ",destination=/project,ro=true"
    mounts = [
        item[len(prefix) : -len(suffix)]
        for item in argv
        if item.startswith(prefix) and item.endswith(suffix)
    ]
    if len(mounts) != 1 or not mounts[0]:
        raise CapabilityProbePackageError(f"probe create command {index} has invalid input mount")
    return Path(mounts[0])


def _require_command(
    result: CommandResult, suffix: tuple[str, ...], *, index: int, executable: str
) -> None:
    if result.argv[0] != executable or result.argv[1:] != suffix:
        raise CapabilityProbePackageError(f"probe command {index} is outside the closed profile")


def _verify_transcript(
    transcript: dict[str, Any], capability: dict[str, Any]
) -> tuple[ProbeObservation, str]:
    if set(transcript) != {
        "commands",
        "image_reference",
        "probe_profile",
        "selected_backend_info",
        "tested_limits",
    }:
        raise CapabilityProbePackageError("probe transcript has an invalid top-level shape")
    if transcript.get("probe_profile") != PROBE_PROFILE:
        raise CapabilityProbePackageError("probe transcript profile is unsupported")
    image_reference = transcript.get("image_reference")
    if not isinstance(image_reference, str):
        raise CapabilityProbePackageError("probe image reference is invalid")
    image_parts = image_reference.rsplit("@sha256:", maxsplit=1)
    if (
        len(image_parts) != 2
        or not image_parts[0]
        or len(image_parts[1]) != 64
        or any(character not in "0123456789abcdef" for character in image_parts[1])
    ):
        raise CapabilityProbePackageError("probe image reference is not digest-pinned")

    raw_commands = transcript.get("commands")
    if not isinstance(raw_commands, list) or len(raw_commands) != _EXPECTED_COMMAND_COUNT:
        raise CapabilityProbePackageError("probe transcript command inventory is incomplete")
    commands = [_command_result(value, index=index) for index, value in enumerate(raw_commands)]
    executable = commands[0].argv[0]
    _require_command(commands[0], ("info", "--format", "json"), index=0, executable=executable)
    _require_command(commands[1], ("version", "--format", "json"), index=1, executable=executable)
    _require_command(
        commands[2],
        ("image", "inspect", image_reference, "--format", "json"),
        index=2,
        executable=executable,
    )
    _require_command(commands[10], ("info", "--format", "json"), index=10, executable=executable)

    tested_limits = transcript.get("tested_limits")
    expected_limit_names = {
        "cpu_quota_millis",
        "memory_bytes",
        "open_files",
        "process_count",
        "wall_time_seconds",
        "writable_bytes",
    }
    if (
        not isinstance(tested_limits, dict)
        or set(tested_limits) != expected_limit_names
        or any(
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
            for value in tested_limits.values()
        )
    ):
        raise CapabilityProbePackageError("probe transcript limits are invalid")
    try:
        limits = ProbeLimits(**tested_limits)
    except TypeError as error:
        raise CapabilityProbePackageError("probe transcript limits are invalid") from error

    main_name = _container_name(commands[3].argv, index=3)
    wall_name = _container_name(commands[6].argv, index=6)
    try:
        expected_main = _container_argv(
            Path(executable),
            name=main_name,
            image_reference=image_reference,
            probe_root=_probe_root(commands[3].argv, index=3),
            limits=limits,
            code=_EFFECTIVE_PROBE_CODE,
        )
        expected_wall = _container_argv(
            Path(executable),
            name=wall_name,
            image_reference=image_reference,
            probe_root=_probe_root(commands[6].argv, index=6),
            limits=limits,
            code=_WALL_TIME_PROBE_CODE,
        )
    except ValueError as error:
        raise CapabilityProbePackageError("probe limits cannot form the closed profile") from error
    if commands[3].argv != expected_main or commands[6].argv != expected_wall:
        raise CapabilityProbePackageError("probe create command is outside the closed profile")
    for index, suffix in (
        (4, ("start", "--attach", main_name)),
        (5, ("rm", "--force", main_name)),
        (7, ("start", "--attach", wall_name)),
        (8, ("kill", wall_name)),
        (9, ("rm", "--force", wall_name)),
    ):
        _require_command(commands[index], suffix, index=index, executable=executable)

    info = _json_object(commands[0])
    post_info = _json_object(commands[10])
    selected_info = _selected_info(info or {})
    if (
        info is None
        or _json_object(commands[1]) is None
        or not _image_is_exact(commands[2], image_reference)
        or not isinstance(transcript.get("selected_backend_info"), dict)
        or semantic_digest(transcript["selected_backend_info"]) != semantic_digest(selected_info)
        or post_info is None
        or _selected_info(post_info) != selected_info
    ):
        raise CapabilityProbePackageError("probe preflight or backend identity is inconsistent")
    if commands[3].exit_code != 0 or commands[3].timed_out:
        raise CapabilityProbePackageError("main probe container was not created")
    if commands[4].exit_code != 0 or commands[4].timed_out or commands[5].exit_code != 0:
        raise CapabilityProbePackageError("main probe execution or cleanup did not succeed")
    if commands[6].exit_code != 0 or commands[6].timed_out:
        raise CapabilityProbePackageError("wall-time probe container was not created")
    if not commands[7].timed_out or commands[9].exit_code != 0:
        raise CapabilityProbePackageError("wall-time probe or cleanup did not succeed")

    controls = _effective_controls(commands[4])
    controls["wall_time_enforced"] = True
    if set(controls) != set(EFFECTIVE_CONTROL_NAMES) or not all(controls.values()):
        raise CapabilityProbePackageError("probe effective controls are incomplete")

    host = _object(info.get("host"))
    security = _object(host.get("security"))
    runtime = _object(host.get("ociRuntime"))
    transport, connection_id, service_id, machine_id, arbitrary_remote = _endpoint(info)
    if security.get("rootless") is not True or arbitrary_remote:
        raise CapabilityProbePackageError(
            "probe backend is not a qualifying local rootless service"
        )

    evidence = capability.get("capability_evidence")
    if not isinstance(evidence, dict):
        raise CapabilityProbePackageError("capability has no complete probe evidence")
    artifact_digest = evidence.get("probe_artifact_digest")
    if not isinstance(artifact_digest, str):
        raise CapabilityProbePackageError("capability probe digest is invalid")
    probe_refs = evidence.get("probe_log_refs")
    if not isinstance(probe_refs, list) or len(probe_refs) != 1:
        raise CapabilityProbePackageError("capability probe log reference is not singular")
    backend = evidence.get("backend")
    if not isinstance(backend, dict):
        raise CapabilityProbePackageError("capability backend evidence is invalid")
    executable_digest = backend.get("executable_digest")
    captured_at = evidence.get("captured_at")
    expires_at = evidence.get("expires_at")
    if (
        not isinstance(executable_digest, str)
        or not isinstance(captured_at, str)
        or not isinstance(expires_at, str)
    ):
        raise CapabilityProbePackageError("capability evidence identity is invalid")

    observation = ProbeObservation(
        backend_kind="podman_rootless",
        backend_name="Podman rootless",
        backend_version=str(_object(info.get("version")).get("Version", "unknown")),
        executable_path=executable,
        executable_digest=executable_digest,
        endpoint_transport=transport,
        connection_id=connection_id,
        service_id=service_id,
        machine_id=machine_id,
        arbitrary_remote=arbitrary_remote,
        normalized_info_digest=semantic_digest(selected_info),
        rootless_reported=True,
        probe_outcome="passed",
        effective_controls=controls,
        tested_limits=limits,
        host_system=str(host.get("os", "unknown")),
        host_release=str(host.get("kernel", "unknown")),
        host_machine=str(host.get("arch", "unknown")),
        oci_runtime_name=str(runtime.get("name", "unknown")),
        oci_runtime_version=str(runtime.get("version", "unknown")),
        probe_log_ref=probe_refs[0],
        probe_artifact_digest=artifact_digest,
        captured_at=captured_at,
        expires_at=expires_at,
        limitations=_BASE_LIMITATIONS,
    )
    return observation, artifact_digest


def verify_capability_probe_package_structure(
    package_root: Path, *, schema_root: Path
) -> VerifiedCapabilityProbeStructure:
    """Verify retained v0.14 probe bytes without granting authority or running commands.

    This function must never be used as proof of controller launch origin. It reads only the
    package and schema roots, validates a closed no-link inventory, requires canonical bytes,
    replays the fixed transcript interpretation, and recomputes all emitted records.
    """

    payloads = _read_closed_inventory(package_root)
    if payloads[f"{_PROBE_INPUT_DIRECTORY}/{_PROBE_INPUT_FILE}"] != _PROBE_INPUT_BYTES:
        raise CapabilityProbePackageError("auditor probe input bytes are not canonical")

    transcript_payload = payloads["probe-transcript.json"]
    transcript = _canonical_object(transcript_payload, name="probe-transcript.json")
    capability = _canonical_object(
        payloads["sandbox-capability.json"], name="sandbox-capability.json"
    )
    artifact = _canonical_object(
        payloads["probe-log.artifact.json"], name="probe-log.artifact.json"
    )
    identity = _canonical_object(
        payloads["probe-log.asset-identity.json"],
        name="probe-log.asset-identity.json",
    )

    registry = LocalSchemaRegistry(schema_root)
    try:
        for record in (capability, artifact, identity):
            registry.validate(record)
    except RecordValidationError as error:
        raise CapabilityProbePackageError(
            "probe package contains an invalid public record"
        ) from error
    if capability.get("project_code_execution_supported") is not True:
        raise CapabilityProbePackageError("probe package is not a qualifying capability package")

    transcript_digest = sha256_digest(transcript_payload)
    observation, recorded_digest = _verify_transcript(transcript, capability)
    if recorded_digest != transcript_digest:
        raise CapabilityProbePackageError("probe transcript digest does not match capability")
    if compile_sandbox_capability(observation) != capability:
        raise CapabilityProbePackageError(
            "capability is not the deterministic transcript projection"
        )

    audit_run_id = artifact.get("audit_run_id")
    captured_at = observation.captured_at
    if not isinstance(audit_run_id, str):
        raise CapabilityProbePackageError("probe artifact audit run is invalid")
    expected_artifact, expected_identity = _artifact_records(
        audit_run_id=audit_run_id,
        captured_at=captured_at,
        transcript_digest=transcript_digest,
    )
    if artifact != expected_artifact or identity != expected_identity:
        raise CapabilityProbePackageError("probe Artifact/AssetIdentity closure is inconsistent")

    return VerifiedCapabilityProbeStructure(
        package_root=package_root,
        capability=capability,
        log_artifact=artifact,
        log_asset_identity=identity,
        transcript=transcript,
        transcript_digest=transcript_digest,
    )
