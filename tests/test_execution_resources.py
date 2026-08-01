from __future__ import annotations

import sys
from pathlib import Path

from sc_referee.execution_resources import (
    AttachedResourceObserver,
    LinuxCgroupV2ResourceObserver,
    ResourceObservation,
    UnavailableResourceObserver,
    observer_for_capability_attached_command,
    read_linux_cgroup_v2_sample,
)
from sc_referee.execution_runtime import SubprocessExecutionRuntime


def _write_cgroup(cgroup: Path, *, process_ids: tuple[int, ...] = (101, 102)) -> None:
    cgroup.mkdir(parents=True)
    (cgroup / "cpu.stat").write_text(
        "usage_usec 250000\nuser_usec 200000\nsystem_usec 50000\n",
        encoding="utf-8",
    )
    (cgroup / "memory.peak").write_text("33554432\n", encoding="utf-8")
    (cgroup / "pids.peak").write_text("2\n", encoding="utf-8")
    (cgroup / "cgroup.procs").write_text(
        "".join(f"{process_id}\n" for process_id in process_ids), encoding="utf-8"
    )


def _write_descriptors(proc_root: Path, process_id: int, count: int) -> None:
    root = proc_root / str(process_id) / "fd"
    root.mkdir(parents=True)
    for index in range(count):
        (root / str(index)).write_bytes(b"")


def test_cgroup_v2_sample_reads_kernel_peaks_and_per_process_open_file_peak(
    tmp_path: Path,
) -> None:
    cgroup = tmp_path / "cgroup" / "audit.scope"
    proc_root = tmp_path / "proc"
    _write_cgroup(cgroup)
    _write_descriptors(proc_root, 101, 3)
    _write_descriptors(proc_root, 102, 7)

    sample = read_linux_cgroup_v2_sample(cgroup, proc_root)

    assert sample.cpu_nanoseconds == 250_000_000
    assert sample.peak_memory_bytes == 33_554_432
    assert sample.process_count_peak == 2
    assert sample.open_files_peak == 7


def test_cgroup_v2_sample_includes_bounded_descendant_cgroups(tmp_path: Path) -> None:
    cgroup = tmp_path / "cgroup" / "audit.scope"
    proc_root = tmp_path / "proc"
    _write_cgroup(cgroup, process_ids=(101,))
    child = cgroup / "nested.scope"
    child.mkdir()
    (child / "cgroup.procs").write_text("103\n", encoding="utf-8")
    _write_descriptors(proc_root, 101, 3)
    _write_descriptors(proc_root, 103, 9)

    sample = read_linux_cgroup_v2_sample(cgroup, proc_root)

    assert sample.open_files_peak == 9


def test_cgroup_v2_sample_keeps_unavailable_metrics_explicit(tmp_path: Path) -> None:
    cgroup = tmp_path / "cgroup"
    cgroup.mkdir()
    (cgroup / "cpu.stat").write_text("usage_usec invalid\n", encoding="utf-8")
    (cgroup / "cgroup.procs").write_text("", encoding="utf-8")

    sample = read_linux_cgroup_v2_sample(cgroup, tmp_path / "proc")

    assert sample.cpu_nanoseconds is None
    assert sample.peak_memory_bytes is None
    assert sample.process_count_peak is None
    assert sample.open_files_peak == 0


def test_linux_observer_binds_exact_container_pid_and_cgroup(tmp_path: Path) -> None:
    proc_root = tmp_path / "proc"
    cgroup_root = tmp_path / "cgroup"
    cgroup = cgroup_root / "user.slice" / "audit.scope"
    _write_cgroup(cgroup, process_ids=(101,))
    _write_descriptors(proc_root, 101, 5)
    (proc_root / "101" / "cgroup").write_text("0::/user.slice/audit.scope\n", encoding="utf-8")
    lookups: list[tuple[Path, str]] = []

    def lookup(executable: Path, container_name: str) -> int:
        lookups.append((executable, container_name))
        return 101

    observer = LinuxCgroupV2ResourceObserver(
        Path("/auditor/podman"),
        "sc-referee-execution-test",
        proc_root=proc_root,
        cgroup_root=cgroup_root,
        sample_interval_seconds=0.001,
        discovery_attempts=1,
        pid_lookup=lookup,
    )

    observer.start()
    result = observer.finish()

    assert lookups == [(Path("/auditor/podman"), "sc-referee-execution-test")]
    assert result.profile == "linux-cgroup-v2-direct-v1"
    assert result.cpu_time_seconds == 0.25
    assert result.peak_memory_bytes == 33_554_432
    assert result.process_count_peak == 2
    assert result.open_files_peak == 5
    assert "1 ms intervals" in result.limitations[0]


def test_linux_observer_fails_closed_when_pid_cgroup_is_not_local(tmp_path: Path) -> None:
    observer = LinuxCgroupV2ResourceObserver(
        Path("/auditor/podman"),
        "remote-machine-container",
        proc_root=tmp_path / "proc",
        cgroup_root=tmp_path / "cgroup",
        sample_interval_seconds=0.001,
        discovery_attempts=1,
        pid_lookup=lambda _executable, _name: 999,
    )

    observer.start()
    result = observer.finish()

    assert result.cpu_time_seconds is None
    assert result.peak_memory_bytes is None
    assert result.process_count_peak is None
    assert result.open_files_peak is None
    assert any("could not be identified" in value for value in result.limitations)


class _TrackingObserver(AttachedResourceObserver):
    def __init__(self) -> None:
        self.started = False
        self.finished = False

    def start(self) -> None:
        self.started = True

    def finish(self) -> ResourceObservation:
        self.finished = True
        return ResourceObservation(
            cpu_time_seconds=0.125,
            peak_memory_bytes=4_194_304,
            process_count_peak=1,
            open_files_peak=4,
            profile="auditor-test-observer-v1",
            limitations=("Auditor-owned synthetic observation.",),
        )


def test_attached_adapter_drains_logs_while_retaining_observer_result(tmp_path: Path) -> None:
    observer = _TrackingObserver()
    runtime = SubprocessExecutionRuntime(observer_factory=lambda _argv: observer)

    result = runtime.start_attached(
        (sys.executable, "-c", "print('auditor-owned test')"),
        timeout_seconds=5,
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
        max_log_bytes=1024,
    )

    assert observer.started is True
    assert observer.finished is True
    assert result.cpu_time_seconds == 0.125
    assert result.peak_memory_bytes == 4_194_304
    assert result.process_count_peak == 1
    assert result.open_files_peak == 4
    assert result.resource_observation_profile == "auditor-test-observer-v1"
    assert result.resource_observation_limitations == ("Auditor-owned synthetic observation.",)


def test_attached_adapter_finishes_observer_after_wall_timeout(tmp_path: Path) -> None:
    observer = _TrackingObserver()
    runtime = SubprocessExecutionRuntime(observer_factory=lambda _argv: observer)

    result = runtime.start_attached(
        (sys.executable, "-c", "import time; time.sleep(5)"),
        timeout_seconds=1,
        stdout_path=tmp_path / "stdout.log",
        stderr_path=tmp_path / "stderr.log",
        max_log_bytes=64,
    )

    assert result.timed_out is True
    assert observer.started is True
    assert observer.finished is True


def test_unavailable_observer_never_invents_resource_values() -> None:
    observer = UnavailableResourceObserver("No qualifying local observer.")

    observer.start()
    result = observer.finish()

    assert result.profile == "unavailable"
    assert result.cpu_time_seconds is None
    assert result.peak_memory_bytes is None
    assert result.process_count_peak is None
    assert result.open_files_peak is None
    assert result.limitations == ("No qualifying local observer.",)


def test_managed_machine_capability_never_treats_remote_pid_as_local() -> None:
    observer = observer_for_capability_attached_command(
        {"capability_evidence": {"endpoint": {"transport": "podman_managed_machine"}}},
        ("/usr/bin/podman", "start", "--attach", "container-name"),
    )

    observer.start()
    result = observer.finish()

    assert result.profile == "unavailable"
    assert all(
        value is None
        for value in (
            result.cpu_time_seconds,
            result.peak_memory_bytes,
            result.process_count_peak,
            result.open_files_peak,
        )
    )
    assert "managed-machine PIDs" in result.limitations[0]
