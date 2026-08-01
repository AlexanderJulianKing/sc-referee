from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any

from sc_referee.core.ids import semantic_digest
from sc_referee.execution_capability import ProbeLimits
from sc_referee.storage.atomic import fsync_directory

_TMP_WRITABLE_BYTES = 65_536
_CONTAINER_NAME = re.compile(r"^sc-referee-[a-z0-9][a-z0-9_.-]{0,96}$")
_INITIAL_SAFE_ENVIRONMENT_NAMES = {
    "LANG",
    "LC_ALL",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "PYTHONHASHSEED",
    "TZ",
}
_SHELL_EXECUTABLES = {"ash", "bash", "csh", "dash", "fish", "ksh", "sh", "tcsh", "zsh"}


class ExecutionEnvelopeError(ValueError):
    """Raised before launch/capture when the accepted execution envelope would be broadened."""


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExecutionEnvelopeError(f"authorization {label} is malformed")
    return value


def _positive_integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ExecutionEnvelopeError(f"authorization limit {label} must be a positive integer")
    return value


def _limits(value: object) -> ProbeLimits:
    limits = _object(value, "limits")
    expected = {
        "cpu_quota_millis",
        "memory_bytes",
        "open_files",
        "process_count",
        "wall_time_seconds",
        "writable_bytes",
    }
    if set(limits) != expected:
        raise ExecutionEnvelopeError("authorization limits are not the closed initial profile")
    result = ProbeLimits(
        wall_time_seconds=_positive_integer(limits["wall_time_seconds"], "wall_time_seconds"),
        cpu_quota_millis=_positive_integer(limits["cpu_quota_millis"], "cpu_quota_millis"),
        memory_bytes=_positive_integer(limits["memory_bytes"], "memory_bytes"),
        process_count=_positive_integer(limits["process_count"], "process_count"),
        open_files=_positive_integer(limits["open_files"], "open_files"),
        writable_bytes=_positive_integer(limits["writable_bytes"], "writable_bytes"),
    )
    if result.writable_bytes < 2 * _TMP_WRITABLE_BYTES:
        raise ExecutionEnvelopeError(
            "writable-byte limit must reserve at least 64 KiB each for /tmp and /output"
        )
    return result


def _command(value: object) -> tuple[str, ...]:
    command = _object(value, "command")
    if set(command) != {"argv", "normalized_digest"}:
        raise ExecutionEnvelopeError("authorization command is not closed")
    raw_argv = command.get("argv")
    if (
        not isinstance(raw_argv, list)
        or not raw_argv
        or len(raw_argv) > 128
        or any(not isinstance(item, str) or not item or "\x00" in item for item in raw_argv)
    ):
        raise ExecutionEnvelopeError("authorization argv is malformed")
    argv = tuple(raw_argv)
    if semantic_digest(list(argv)) != command.get("normalized_digest"):
        raise ExecutionEnvelopeError("authorization argv digest does not match")
    executable_name = PurePosixPath(argv[0]).name.lower()
    if executable_name in _SHELL_EXECUTABLES:
        raise ExecutionEnvelopeError("the initial execution profile does not invoke a shell")
    return argv


def _environment(value: object) -> tuple[tuple[str, str], ...]:
    environment = _object(value, "environment")
    if set(environment) != {"entries", "normalized_digest"}:
        raise ExecutionEnvelopeError("authorization environment is not closed")
    raw_entries = environment.get("entries")
    if not isinstance(raw_entries, list):
        raise ExecutionEnvelopeError("authorization environment entries are malformed")
    entries: list[tuple[str, str]] = []
    public_entries: list[dict[str, str]] = []
    for raw_entry in raw_entries:
        entry = _object(raw_entry, "environment entry")
        if set(entry) != {"name", "value"}:
            raise ExecutionEnvelopeError("authorization environment entry is not closed")
        name = entry.get("name")
        value_text = entry.get("value")
        if not isinstance(name, str) or not isinstance(value_text, str) or "\x00" in value_text:
            raise ExecutionEnvelopeError("authorization environment entry is malformed")
        if name not in _INITIAL_SAFE_ENVIRONMENT_NAMES:
            raise ExecutionEnvelopeError(
                f"environment variable {name!r} is outside the initial nonsecret allowlist"
            )
        entries.append((name, value_text))
        public_entries.append({"name": name, "value": value_text})
    if len({name for name, _value in entries}) != len(entries):
        raise ExecutionEnvelopeError("authorization environment names are not unique")
    if entries != sorted(entries):
        raise ExecutionEnvelopeError("authorization environment entries are not normalized")
    if semantic_digest(public_entries) != environment.get("normalized_digest"):
        raise ExecutionEnvelopeError("authorization environment digest does not match")
    return tuple(entries)


def _image(value: object) -> str:
    image = _object(value, "image")
    if set(image) != {"reference", "manifest_digest"}:
        raise ExecutionEnvelopeError("authorization image is not closed")
    reference = image.get("reference")
    digest = image.get("manifest_digest")
    if not isinstance(reference, str) or not isinstance(digest, str):
        raise ExecutionEnvelopeError("authorization image identity is malformed")
    if "@" not in reference or reference.rsplit("@", maxsplit=1)[1] != digest:
        raise ExecutionEnvelopeError("authorization image reference and manifest digest differ")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
        raise ExecutionEnvelopeError("authorization image digest is malformed")
    return reference


def build_podman_execution_argv(
    executable: Path,
    authorization: dict[str, object],
    snapshot_root: Path,
    container_name: str,
) -> tuple[str, ...]:
    """Compile an exact authorization into a shell-free Podman create argv.

    This function is pure with respect to the container runtime: it never invokes the returned
    command and it accepts no repository-defined flags.
    """

    if not executable.is_absolute():
        raise ExecutionEnvelopeError("container-runtime executable path must be absolute")
    if not _CONTAINER_NAME.fullmatch(container_name):
        raise ExecutionEnvelopeError("container name is outside the controller-owned namespace")
    if snapshot_root.is_symlink() or not snapshot_root.is_dir():
        raise ExecutionEnvelopeError("immutable snapshot mount must be a real directory")
    if authorization.get("record_type") != "project_execution_authorization":
        raise ExecutionEnvelopeError("a ProjectExecutionAuthorization record is required")
    if authorization.get("network_policy") != "denied":
        raise ExecutionEnvelopeError("project network policy must remain denied")

    limits = _limits(authorization.get("limits"))
    command = _command(authorization.get("command"))
    environment = _environment(authorization.get("environment"))
    image_reference = _image(authorization.get("image"))
    output_bytes = limits.writable_bytes - _TMP_WRITABLE_BYTES

    runtime_argv = (
        str(executable),
        "create",
        f"--name={container_name}",
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
        f"--tmpfs=/tmp:rw,size={_TMP_WRITABLE_BYTES},nosuid,nodev,noexec",
        f"--tmpfs=/output:rw,size={output_bytes},nosuid,nodev,noexec",
        (f"--mount=type=bind,source={snapshot_root.resolve()},destination=/project,ro=true"),
        "--workdir=/project",
        *(f"--env={name}={value}" for name, value in environment),
        image_reference,
        *command,
    )
    forbidden_runtime_tokens = {
        "--device",
        "--host",
        "--ipc=host",
        "--network=host",
        "--pid=host",
        "--privileged",
        "--publish",
        "--security-opt=label=disable",
        "--uts=host",
    }
    image_index = runtime_argv.index(image_reference)
    if any(token in forbidden_runtime_tokens for token in runtime_argv[:image_index]):
        raise ExecutionEnvelopeError("compiled runtime argv contains a forbidden escalation")
    return runtime_argv


def _normalized_relative_path(value: str) -> PurePosixPath:
    if not value or "\x00" in value or "\\" in value:
        raise ExecutionEnvelopeError("allowed output path is malformed")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ExecutionEnvelopeError(f"allowed output path is unsafe: {value!r}")
    return path


def _inventory_staging(staging_root: Path) -> tuple[list[Path], list[Path]]:
    directories: list[Path] = []
    files: list[Path] = []
    for path in sorted(
        staging_root.rglob("*"), key=lambda item: item.relative_to(staging_root).as_posix()
    ):
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ExecutionEnvelopeError(
                f"output symlink is prohibited: {path.relative_to(staging_root).as_posix()}"
            )
        if stat.S_ISDIR(metadata.st_mode):
            directories.append(path)
        elif stat.S_ISREG(metadata.st_mode):
            files.append(path)
        else:
            raise ExecutionEnvelopeError(
                f"output special file is prohibited: {path.relative_to(staging_root).as_posix()}"
            )
    return directories, files


def _file_digest(path: Path) -> tuple[str, int]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ExecutionEnvelopeError(f"output is not a regular file: {path}")
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
        after = os.fstat(descriptor)
        if (before.st_dev, before.st_ino, before.st_size) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
        ) or size != before.st_size:
            raise ExecutionEnvelopeError(f"output changed during capture: {path}")
        return f"sha256:{digest.hexdigest()}", size
    finally:
        os.close(descriptor)


def _copy_verified_file(source: Path, destination: Path, digest: str, size: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    source_descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        destination_descriptor = os.open(
            destination,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        try:
            copied_digest = hashlib.sha256()
            copied_size = 0
            while True:
                chunk = os.read(source_descriptor, 1024 * 1024)
                if not chunk:
                    break
                view = memoryview(chunk)
                while view:
                    written = os.write(destination_descriptor, view)
                    view = view[written:]
                copied_digest.update(chunk)
                copied_size += len(chunk)
            os.fsync(destination_descriptor)
        finally:
            os.close(destination_descriptor)
    finally:
        os.close(source_descriptor)
    if copied_size != size or f"sha256:{copied_digest.hexdigest()}" != digest:
        raise ExecutionEnvelopeError(f"output changed between validation and copy: {source}")


def capture_stopped_container_outputs(
    staging_root: Path,
    destination_root: Path,
    *,
    allowed_output_paths: tuple[str, ...],
    logical_byte_limit: int,
    project_processes_quiescent: bool,
    cleanup_observed: bool,
) -> dict[str, object]:
    """Validate and copy untrusted output bytes without executing or deserializing them."""

    if not project_processes_quiescent:
        raise ExecutionEnvelopeError("output capture requires an observed quiescent sandbox")
    if not cleanup_observed:
        raise ExecutionEnvelopeError("output capture requires observed sandbox cleanup")
    if staging_root.is_symlink() or not staging_root.is_dir():
        raise ExecutionEnvelopeError("output staging root must be a real directory")
    if destination_root.exists() or destination_root.is_symlink():
        raise FileExistsError(f"accepted output root already exists: {destination_root}")
    if not isinstance(logical_byte_limit, int) or logical_byte_limit < 0:
        raise ExecutionEnvelopeError("logical output byte limit is invalid")

    normalized_allowed = tuple(_normalized_relative_path(value) for value in allowed_output_paths)
    if len(set(normalized_allowed)) != len(normalized_allowed):
        raise ExecutionEnvelopeError("allowed output paths are not unique")
    allowed_names = {path.as_posix() for path in normalized_allowed}
    allowed_directories = {
        parent.as_posix()
        for path in normalized_allowed
        for parent in path.parents
        if parent != PurePosixPath(".")
    }
    directories, files = _inventory_staging(staging_root)
    actual_directories = {path.relative_to(staging_root).as_posix() for path in directories}
    if not actual_directories <= allowed_directories:
        unexpected = sorted(actual_directories - allowed_directories)
        raise ExecutionEnvelopeError(f"unexpected output directories: {unexpected}")

    entries: list[dict[str, object]] = []
    total_size = 0
    for path in files:
        relative = path.relative_to(staging_root).as_posix()
        if relative not in allowed_names:
            raise ExecutionEnvelopeError(f"unexpected output path: {relative}")
        digest, size = _file_digest(path)
        total_size += size
        if total_size > logical_byte_limit:
            raise ExecutionEnvelopeError(
                "accepted output exceeds the authorized logical-byte limit"
            )
        entries.append({"digest": digest, "path": relative, "size_bytes": size})

    destination_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    for entry in entries:
        relative = str(entry["path"])
        size_value = entry["size_bytes"]
        if not isinstance(size_value, int):
            raise AssertionError("internal output inventory size is not an integer")
        _copy_verified_file(
            staging_root / relative,
            destination_root / relative,
            str(entry["digest"]),
            size_value,
        )
    fsync_directory(destination_root)
    return {
        "entries": entries,
        "logical_byte_limit": logical_byte_limit,
        "total_logical_bytes": total_size,
    }
