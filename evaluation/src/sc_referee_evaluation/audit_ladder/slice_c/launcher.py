"""Descriptor-anchored, resource-bounded controller for the isolated worker."""

from __future__ import annotations

import os
import resource
import select
import signal
import stat
import time
from pathlib import Path
from typing import Final

from sc_referee_evaluation.audit_ladder.slice_c.core import (
    RefusalFacetV1,
    SliceCContractError,
    WorkerControllerResultV1,
    sha256,
)
from sc_referee_evaluation.audit_ladder.slice_c.protocol import (
    AdmittedWorkerRequestV1,
    admit_worker_request_v1,
    select_refusal_v1,
    validate_worker_response_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.runtime import (
    _SEALED_ROOT_MODES,
    RuntimeAuthenticationError,
    _open_roots,
    _RootDescriptors,
    _verify_with_open_roots,
    read_runtime_artifacts_v1,
)

_WORKER_SIZE: Final = 47_838
_WORKER_SHA256: Final = "sha256:fcb341d6729712833964012a8fc4d46e28fc296188753fe20dcebcd7c4e94362"
_STDOUT_LIMIT: Final = 8_388_608
_WALL_LIMIT: Final = 90.0
_RSS_LIMIT: Final = 1_073_741_824
_CPU_LIMIT: Final = 60.0
_ENVIRONMENT: Final = {
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin",
    "TZ": "UTC",
    "__CF_USER_TEXT_ENCODING": "0x1F5:0x0:0x0",
}


def _resource_facets_v1(
    *,
    cpu: int | float,
    wall: int | float,
    rss: int,
    stdout: int,
    stderr: int,
    nofile: int,
    fsize: int,
    core: int,
) -> set[RefusalFacetV1]:
    values = (cpu, wall, rss, stdout, stderr, nofile, fsize, core)
    if (
        type(cpu) not in {int, float}
        or type(wall) not in {int, float}
        or any(type(value) is not int for value in values[2:])
        or any(value < 0 for value in values)
    ):
        raise SliceCContractError("resource counter is outside the closed numeric domain")
    observed: set[RefusalFacetV1] = set()
    for condition, facet in (
        (cpu > _CPU_LIMIT, RefusalFacetV1.CPU),
        (wall > _WALL_LIMIT, RefusalFacetV1.WALL),
        (rss > _RSS_LIMIT, RefusalFacetV1.RSS),
        (stdout > _STDOUT_LIMIT, RefusalFacetV1.STDOUT),
        (stderr > 0, RefusalFacetV1.STDERR),
        (nofile > 128, RefusalFacetV1.NOFILE),
        (fsize > 0, RefusalFacetV1.FSIZE),
        (core > 0, RefusalFacetV1.CORE),
    ):
        if condition:
            observed.add(facet)
    return observed


def _process_facets_v1(
    *,
    wrote_request: bool,
    status: int | None,
    stderr_size: int,
) -> set[RefusalFacetV1]:
    if type(wrote_request) is not bool or (status is not None and type(status) is not int):
        raise SliceCContractError("process outcome has the wrong type")
    if type(stderr_size) is not int or stderr_size < 0:
        raise SliceCContractError("stderr size is outside the closed numeric domain")
    observed: set[RefusalFacetV1] = set()
    if (
        not wrote_request
        or status is None
        or not os.WIFEXITED(status)
        or os.WEXITSTATUS(status) != 0
    ):
        observed.add(RefusalFacetV1.PROCESS_STATUS)
    if stderr_size:
        observed.add(RefusalFacetV1.STDERR)
    return observed


def _worker_source() -> str:
    path = Path(__file__).with_name("_worker.py")
    before = os.stat(path, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        raise RuntimeAuthenticationError("isolated worker source is not one regular file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise RuntimeAuthenticationError("isolated worker source descriptor differs")
        chunks: list[bytes] = []
        while True:
            block = os.read(fd, 65_536)
            if not block:
                break
            chunks.append(block)
        after = os.fstat(fd)
        if (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ) != (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        ):
            raise RuntimeAuthenticationError("isolated worker source changed during capture")
    finally:
        os.close(fd)
    raw = b"".join(chunks)
    if len(raw) != _WORKER_SIZE or sha256(raw) != _WORKER_SHA256:
        raise RuntimeAuthenticationError("isolated worker source identity differs")
    return raw.decode("utf-8", "strict")


def _verify_open_runtime(roots: _RootDescriptors) -> tuple[object, dict[str, bytes]]:
    artifacts = read_runtime_artifacts_v1()
    evidence, runtime, cpython = _verify_with_open_roots(
        roots,
        artifacts,
        state="sealed",
        retain_directory_fds=False,
    )
    runtime.close()
    cpython.close()
    return evidence, artifacts


def _close_many(fds: tuple[int, ...]) -> None:
    for fd in fds:
        try:
            os.close(fd)
        except OSError:
            pass


def _child_exec(
    sandbox_fd: int,
    source: str,
    stdin_fd: int,
    stdout_fd: int,
    stderr_fd: int,
    inherited_fds: tuple[int, ...],
) -> None:
    try:
        os.setsid()
        os.fchdir(sandbox_fd)
        os.dup2(stdin_fd, 0)
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        for fd in inherited_fds:
            if fd > 2:
                try:
                    os.close(fd)
                except OSError:
                    pass
        resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
        resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        argv = ["python/bin/python3.11", "-I", "-S", "-B", "-c", source]
        os.execve("python/bin/python3.11", argv, _ENVIRONMENT)
    except BaseException:
        os._exit(127)


def _terminate_process_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _write_request(fd: int, raw: bytes) -> bool:
    offset = 0
    try:
        while offset < len(raw):
            written = os.write(fd, raw[offset : offset + 1_048_576])
            if written <= 0:
                return False
            offset += written
        return True
    except BrokenPipeError:
        return False
    finally:
        os.close(fd)


def _collect_process(
    pid: int,
    stdout_fd: int,
    stderr_fd: int,
    started: float,
) -> tuple[bytes, bytes, int | None, resource.struct_rusage | None, set[RefusalFacetV1]]:
    os.set_blocking(stdout_fd, False)
    os.set_blocking(stderr_fd, False)
    open_fds = {stdout_fd, stderr_fd}
    stdout = bytearray()
    stderr = bytearray()
    status: int | None = None
    usage: resource.struct_rusage | None = None
    observed: set[RefusalFacetV1] = set()
    killed = False
    while open_fds or status is None:
        elapsed = time.monotonic() - started
        if elapsed > _WALL_LIMIT and RefusalFacetV1.WALL not in observed:
            observed.add(RefusalFacetV1.WALL)
            _terminate_process_group(pid)
            killed = True
        ready, _, _ = select.select(list(open_fds), [], [], 0.05)
        for fd in ready:
            try:
                block = os.read(fd, 65_536)
            except BlockingIOError:
                continue
            if not block:
                os.close(fd)
                open_fds.remove(fd)
                continue
            target = stdout if fd == stdout_fd else stderr
            target.extend(block)
            if fd == stdout_fd and len(stdout) > _STDOUT_LIMIT:
                observed.add(RefusalFacetV1.STDOUT)
                _terminate_process_group(pid)
                killed = True
            if fd == stderr_fd and stderr:
                observed.add(RefusalFacetV1.STDERR)
                _terminate_process_group(pid)
                killed = True
        if status is None:
            waited, candidate_status, candidate_usage = os.wait4(pid, os.WNOHANG)
            if waited == pid:
                status = candidate_status
                usage = candidate_usage
        if killed and status is None:
            waited, candidate_status, candidate_usage = os.wait4(pid, 0)
            if waited == pid:
                status = candidate_status
                usage = candidate_usage
    if usage is not None:
        observed.update(
            _resource_facets_v1(
                cpu=usage.ru_utime + usage.ru_stime,
                wall=time.monotonic() - started,
                rss=usage.ru_maxrss,
                stdout=len(stdout),
                stderr=len(stderr),
                nofile=128,
                fsize=0,
                core=0,
            )
        )
    return bytes(stdout), bytes(stderr), status, usage, observed


def run_isolated_worker_v1(
    *,
    registry_raw: bytes,
    request_raw: bytes,
) -> WorkerControllerResultV1:
    """Run one fresh worker after ranks 1-5 and complete runtime authentication."""

    admitted = admit_worker_request_v1(registry_raw, request_raw)
    if type(admitted) is RefusalFacetV1:
        return WorkerControllerResultV1(facts=None, refusal=admitted)
    if type(admitted) is not AdmittedWorkerRequestV1:
        return WorkerControllerResultV1(facts=None, refusal=RefusalFacetV1.REQUEST_PROTOCOL)
    try:
        source = _worker_source()
        roots = _open_roots(_SEALED_ROOT_MODES)
        before_evidence, before_artifacts = _verify_open_runtime(roots)
    except (OSError, RuntimeAuthenticationError, UnicodeError):
        return WorkerControllerResultV1(facts=None, refusal=RefusalFacetV1.POST_RUN_IDENTITY)

    stdin_read, stdin_write = os.pipe()
    stdout_read, stdout_write = os.pipe()
    stderr_read, stderr_write = os.pipe()
    inherited = (
        stdin_read,
        stdin_write,
        stdout_read,
        stdout_write,
        stderr_read,
        stderr_write,
        roots.parent,
        roots.sandbox,
        roots.python,
        roots.venv,
    )
    started = time.monotonic()
    pid = os.fork()
    if pid == 0:
        _child_exec(
            roots.sandbox,
            source,
            stdin_read,
            stdout_write,
            stderr_write,
            inherited,
        )
        os._exit(127)
    _close_many((stdin_read, stdout_write, stderr_write))
    wrote_request = _write_request(stdin_write, request_raw)
    stdout, stderr, status, _usage, observed = _collect_process(
        pid,
        stdout_read,
        stderr_read,
        started,
    )
    observed.update(
        _process_facets_v1(
            wrote_request=wrote_request,
            status=status,
            stderr_size=len(stderr),
        )
    )
    post_identity_ok = False
    try:
        after_evidence, after_artifacts = _verify_open_runtime(roots)
        post_identity_ok = (
            before_evidence == after_evidence
            and before_artifacts == after_artifacts
            and all(
                (os.fstat(fd).st_dev, os.fstat(fd).st_ino) == (identity[0], identity[1])
                for fd, identity in (
                    (roots.parent, (16_777_233, 394_647_424)),
                    (roots.sandbox, (16_777_233, 394_647_433)),
                    (roots.python, (16_777_233, 394_647_434)),
                    (roots.venv, (16_777_233, 394_650_585)),
                )
            )
        )
    except (OSError, RuntimeAuthenticationError):
        post_identity_ok = False
    finally:
        roots.close()
    response = validate_worker_response_v1(
        request_value=admitted.value,
        request_raw=request_raw,
        response_raw=stdout,
        require_world1_success=True,
    )
    if response.refusal in {
        RefusalFacetV1.RESPONSE_FRAME,
        RefusalFacetV1.RESPONSE_PROTOCOL,
    }:
        observed.add(response.refusal)
    if not post_identity_ok:
        observed.add(RefusalFacetV1.POST_RUN_IDENTITY)
    controller = select_refusal_v1(observed)
    if controller is not None:
        return WorkerControllerResultV1(facts=None, refusal=controller)
    # Only an Amendment-5 worker-owned refusal or authenticated success survives.
    return response


__all__ = ["run_isolated_worker_v1"]
