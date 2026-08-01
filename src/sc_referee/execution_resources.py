from __future__ import annotations

import os
import subprocess
import sys
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

_OBSERVER_PROFILE = "linux-cgroup-v2-direct-v1"
_UNAVAILABLE_PROFILE = "unavailable"
_DEFAULT_SAMPLE_INTERVAL_SECONDS = 0.05
_DEFAULT_DISCOVERY_ATTEMPTS = 40
_MAX_CGROUP_NODES = 256
_MAX_OBSERVED_PIDS = 4096
_CONTROL_ENVIRONMENT = {"PATH": "/usr/local/bin:/usr/bin:/bin"}


@dataclass(frozen=True)
class ResourceObservation:
    cpu_time_seconds: float | None
    peak_memory_bytes: int | None
    process_count_peak: int | None
    open_files_peak: int | None
    profile: str
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class CgroupV2Sample:
    cpu_nanoseconds: int | None
    peak_memory_bytes: int | None
    process_count_peak: int | None
    open_files_peak: int | None


class AttachedResourceObserver:
    """Bounded observer interface used alongside one attached container client."""

    def start(self) -> None:
        raise NotImplementedError

    def finish(self) -> ResourceObservation:
        raise NotImplementedError


class UnavailableResourceObserver(AttachedResourceObserver):
    def __init__(self, limitation: str) -> None:
        self._limitation = limitation

    def start(self) -> None:
        return None

    def finish(self) -> ResourceObservation:
        return ResourceObservation(
            cpu_time_seconds=None,
            peak_memory_bytes=None,
            process_count_peak=None,
            open_files_peak=None,
            profile=_UNAVAILABLE_PROFILE,
            limitations=(self._limitation,),
        )


def _read_nonnegative_integer(path: Path) -> int | None:
    try:
        value = path.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError, UnicodeError):
        return None
    if not value.isdigit():
        return None
    parsed = int(value)
    return parsed if parsed >= 0 else None


def _read_cpu_nanoseconds(path: Path) -> int | None:
    try:
        rows = path.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError, UnicodeError):
        return None
    values: dict[str, int] = {}
    for row in rows:
        parts = row.split()
        if len(parts) != 2 or not parts[1].isdigit() or parts[0] in values:
            return None
        values[parts[0]] = int(parts[1])
    if "usage_usec" in values:
        return values["usage_usec"] * 1_000
    if "usage_nsec" in values:
        return values["usage_nsec"]
    return None


def _bounded_cgroup_process_ids(cgroup_path: Path) -> tuple[int, ...] | None:
    pending = [cgroup_path]
    seen_nodes = 0
    process_ids: set[int] = set()
    while pending:
        node = pending.pop()
        seen_nodes += 1
        if seen_nodes > _MAX_CGROUP_NODES or node.is_symlink():
            return None
        try:
            rows = (node / "cgroup.procs").read_text(encoding="utf-8").splitlines()
            children = [child for child in node.iterdir() if child.is_dir()]
        except (FileNotFoundError, OSError, UnicodeError):
            return None
        for row in rows:
            if not row.isdigit():
                return None
            process_ids.add(int(row))
            if len(process_ids) > _MAX_OBSERVED_PIDS:
                return None
        pending.extend(children)
    return tuple(sorted(process_ids))


def _open_files_peak(cgroup_path: Path, proc_root: Path) -> int | None:
    process_ids = _bounded_cgroup_process_ids(cgroup_path)
    if process_ids is None:
        return None
    peak = 0
    observed = False
    for process_id in process_ids:
        descriptor_root = proc_root / str(process_id) / "fd"
        try:
            count = sum(1 for _entry in os.scandir(descriptor_root))
        except FileNotFoundError:
            # A process can exit between the cgroup and descriptor reads. A later sample retains
            # the peak already observed for longer-lived processes.
            continue
        except OSError:
            return None
        peak = max(peak, count)
        observed = True
    return peak if observed or not process_ids else None


def read_linux_cgroup_v2_sample(cgroup_path: Path, proc_root: Path) -> CgroupV2Sample:
    """Read one bounded direct cgroup-v2 sample without invoking container code."""

    return CgroupV2Sample(
        cpu_nanoseconds=_read_cpu_nanoseconds(cgroup_path / "cpu.stat"),
        peak_memory_bytes=_read_nonnegative_integer(cgroup_path / "memory.peak"),
        process_count_peak=_read_nonnegative_integer(cgroup_path / "pids.peak"),
        open_files_peak=_open_files_peak(cgroup_path, proc_root),
    )


def _default_pid_lookup(executable: Path, container_name: str) -> int | None:
    try:
        result = subprocess.run(
            (
                str(executable),
                "container",
                "inspect",
                container_name,
                "--format",
                "{{.State.Pid}}",
            ),
            check=False,
            capture_output=True,
            env=_CONTROL_ENVIRONMENT,
            text=True,
            timeout=1,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    if result.returncode != 0 or not value.isdigit() or int(value) <= 0:
        return None
    return int(value)


def _cgroup_path_for_pid(pid: int, proc_root: Path, cgroup_root: Path) -> Path | None:
    try:
        rows = (proc_root / str(pid) / "cgroup").read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError, UnicodeError):
        return None
    unified = [row.removeprefix("0::") for row in rows if row.startswith("0::")]
    if len(unified) != 1:
        return None
    relative = PurePosixPath(unified[0])
    if not relative.is_absolute() or ".." in relative.parts:
        return None
    candidate = cgroup_root.joinpath(*relative.parts[1:])
    if candidate.is_symlink() or not candidate.is_dir():
        return None
    return candidate


class LinuxCgroupV2ResourceObserver(AttachedResourceObserver):
    """Observe one local Linux container cgroup while the attached client drains logs."""

    def __init__(
        self,
        executable: Path,
        container_name: str,
        *,
        proc_root: Path = Path("/proc"),
        cgroup_root: Path = Path("/sys/fs/cgroup"),
        sample_interval_seconds: float = _DEFAULT_SAMPLE_INTERVAL_SECONDS,
        discovery_attempts: int = _DEFAULT_DISCOVERY_ATTEMPTS,
        pid_lookup: Callable[[Path, str], int | None] = _default_pid_lookup,
    ) -> None:
        if sample_interval_seconds <= 0:
            raise ValueError("resource sample interval must be positive")
        if discovery_attempts <= 0:
            raise ValueError("resource discovery attempts must be positive")
        self._executable = executable
        self._container_name = container_name
        self._proc_root = proc_root
        self._cgroup_root = cgroup_root
        self._sample_interval_seconds = sample_interval_seconds
        self._discovery_attempts = discovery_attempts
        self._pid_lookup = pid_lookup
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._cpu_nanoseconds: int | None = None
        self._peak_memory_bytes: int | None = None
        self._process_count_peak: int | None = None
        self._open_files_peak: int | None = None
        self._error: str | None = None

    @staticmethod
    def _maximum(current: int | None, observed: int | None) -> int | None:
        if observed is None:
            return current
        return observed if current is None else max(current, observed)

    def _retain(self, sample: CgroupV2Sample) -> None:
        self._cpu_nanoseconds = self._maximum(self._cpu_nanoseconds, sample.cpu_nanoseconds)
        self._peak_memory_bytes = self._maximum(self._peak_memory_bytes, sample.peak_memory_bytes)
        self._process_count_peak = self._maximum(
            self._process_count_peak, sample.process_count_peak
        )
        self._open_files_peak = self._maximum(self._open_files_peak, sample.open_files_peak)

    def _observe(self) -> None:
        try:
            cgroup_path: Path | None = None
            for _attempt in range(self._discovery_attempts):
                pid = self._pid_lookup(self._executable, self._container_name)
                if pid is not None:
                    cgroup_path = _cgroup_path_for_pid(pid, self._proc_root, self._cgroup_root)
                    if cgroup_path is not None:
                        break
                if self._stop.wait(self._sample_interval_seconds):
                    break
            if cgroup_path is None:
                self._error = "The local Linux container cgroup could not be identified."
                return
            while not self._stop.is_set():
                self._retain(read_linux_cgroup_v2_sample(cgroup_path, self._proc_root))
                self._stop.wait(self._sample_interval_seconds)
            self._retain(read_linux_cgroup_v2_sample(cgroup_path, self._proc_root))
        except (OSError, ValueError) as error:
            self._error = f"The local Linux cgroup observer failed: {error}"

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("resource observer already started")
        self._thread = threading.Thread(
            target=self._observe,
            name="sc-referee-cgroup-observer",
            daemon=True,
        )
        self._thread.start()

    def finish(self) -> ResourceObservation:
        if self._thread is None:
            raise RuntimeError("resource observer was not started")
        self._stop.set()
        self._thread.join(timeout=2)
        limitations = [
            "Open-file use is the maximum per-process descriptor count observed at "
            f"{self._sample_interval_seconds * 1000:g} ms intervals; shorter spikes may not be "
            "observed.",
        ]
        if self._thread.is_alive():
            limitations.append("The resource observer did not terminate within its bounded join.")
            return ResourceObservation(
                None, None, None, None, _UNAVAILABLE_PROFILE, tuple(sorted(limitations))
            )
        if self._error is not None:
            limitations.append(self._error)
        return ResourceObservation(
            cpu_time_seconds=(
                self._cpu_nanoseconds / 1_000_000_000 if self._cpu_nanoseconds is not None else None
            ),
            peak_memory_bytes=self._peak_memory_bytes,
            process_count_peak=self._process_count_peak,
            open_files_peak=self._open_files_peak,
            profile=_OBSERVER_PROFILE,
            limitations=tuple(sorted(limitations)),
        )


def observer_for_attached_command(argv: tuple[str, ...]) -> AttachedResourceObserver:
    if len(argv) != 4 or argv[1:3] != ("start", "--attach"):
        return UnavailableResourceObserver(
            "Direct cgroup observation applies only to the exact Podman attached-start command."
        )
    if not sys.platform.startswith("linux"):
        return UnavailableResourceObserver(
            "Direct container cgroup observation is unavailable outside a local Linux host."
        )
    proc_root = Path("/proc")
    cgroup_root = Path("/sys/fs/cgroup")
    if not proc_root.is_dir() or not (cgroup_root / "cgroup.controllers").is_file():
        return UnavailableResourceObserver(
            "A local Linux cgroup-v2 hierarchy is unavailable for direct observation."
        )
    return LinuxCgroupV2ResourceObserver(Path(argv[0]), argv[3])


def observer_for_capability_attached_command(
    capability: Mapping[str, object], argv: tuple[str, ...]
) -> AttachedResourceObserver:
    evidence = capability.get("capability_evidence")
    endpoint = evidence.get("endpoint") if isinstance(evidence, Mapping) else None
    transport = endpoint.get("transport") if isinstance(endpoint, Mapping) else None
    if transport != "local_unix_socket":
        return UnavailableResourceObserver(
            "Direct cgroup observation requires a capability bound to a local Unix-socket "
            "Podman service; remote and managed-machine PIDs are not treated as local host PIDs."
        )
    return observer_for_attached_command(argv)
