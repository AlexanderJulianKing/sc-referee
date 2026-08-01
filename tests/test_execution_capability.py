from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from sc_referee.execution_capability import (
    EFFECTIVE_CONTROL_NAMES,
    ProbeLimits,
    ProbeObservation,
    compile_sandbox_capability,
    compile_unavailable_capability,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry


def _passing_observation() -> ProbeObservation:
    return ProbeObservation(
        backend_kind="podman_rootless",
        backend_name="Podman rootless",
        backend_version="5.0.0",
        executable_path="/usr/bin/podman",
        executable_digest="sha256:" + "1" * 64,
        endpoint_transport="local_unix_socket",
        connection_id="connection:local-podman",
        service_id="service:local-podman",
        machine_id=None,
        arbitrary_remote=False,
        normalized_info_digest="sha256:" + "2" * 64,
        rootless_reported=True,
        probe_outcome="passed",
        effective_controls={name: True for name in EFFECTIVE_CONTROL_NAMES},
        tested_limits=ProbeLimits(
            wall_time_seconds=2,
            cpu_quota_millis=500,
            memory_bytes=67_108_864,
            process_count=16,
            open_files=32,
            writable_bytes=1_048_576,
        ),
        host_system="Linux",
        host_release="6.12.0",
        host_machine="x86_64",
        oci_runtime_name="crun",
        oci_runtime_version="1.17",
        probe_log_ref={"record_type": "artifact", "record_id": "artifact:probe-log"},
        probe_artifact_digest="sha256:" + "3" * 64,
        captured_at="2026-07-29T18:00:00Z",
        expires_at="2026-07-29T19:00:00Z",
        limitations=("Host-kernel isolation is shared with the container runtime.",),
    )


def test_complete_probe_compiles_schema_valid_qualifying_capability(schema_root: Path) -> None:
    record = compile_sandbox_capability(_passing_observation())

    LocalSchemaRegistry(schema_root).validate(record)
    assert record["project_code_execution_supported"] is True
    assert record["rootless_verified"] is True
    assert record["capability_evidence_status"] == "complete_effective_probe"
    assert record["unsafe_fallback_available"] is False
    assert all(record["controls"].values())


@pytest.mark.parametrize("control", EFFECTIVE_CONTROL_NAMES)
def test_each_missing_effective_control_fails_closed(schema_root: Path, control: str) -> None:
    observation = _passing_observation()
    controls = dict(observation.effective_controls)
    controls[control] = False

    record = compile_sandbox_capability(replace(observation, effective_controls=controls))

    LocalSchemaRegistry(schema_root).validate(record)
    assert record["project_code_execution_supported"] is False
    assert record["rootless_verified"] is False
    assert record["capability_evidence_status"] == "not_supported"
    assert record["capability_evidence"] is None
    assert any(control in limitation for limitation in record["limitations"])


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ({"rootless_reported": False}, "rootless"),
        ({"arbitrary_remote": True}, "arbitrary_remote"),
        ({"endpoint_transport": "unbound_remote"}, "endpoint_transport"),
        ({"probe_outcome": "failed"}, "probe_outcome"),
        ({"machine_identity_stable": False}, "machine_identity_stable"),
        ({"evidence_fresh": False}, "evidence_fresh"),
    ],
)
def test_nonqualifying_identity_or_probe_state_fails_closed(
    schema_root: Path, mutation: dict[str, object], reason: str
) -> None:
    record = compile_sandbox_capability(replace(_passing_observation(), **mutation))

    LocalSchemaRegistry(schema_root).validate(record)
    assert record["project_code_execution_supported"] is False
    assert record["capability_evidence"] is None
    assert any(reason in limitation for limitation in record["limitations"])


def test_docker_is_not_inferred_rootless_from_a_version_or_successful_probe(
    schema_root: Path,
) -> None:
    observation = replace(
        _passing_observation(),
        backend_kind="docker_rootless",
        backend_name="Docker",
        rootless_reported=False,
    )

    record = compile_sandbox_capability(observation)

    LocalSchemaRegistry(schema_root).validate(record)
    assert record["project_code_execution_supported"] is False
    assert "rootless_reported" in " ".join(record["limitations"])


def test_absent_backend_is_a_schema_valid_unavailable_capability(schema_root: Path) -> None:
    record = compile_unavailable_capability(
        captured_at="2026-07-29T18:00:00Z",
        reason="No supported rootless OCI backend executable was found.",
    )

    LocalSchemaRegistry(schema_root).validate(record)
    assert record["backend_kind"] == "no_execution"
    assert record["project_code_execution_supported"] is False
    assert record["capability_evidence_status"] == "not_supported"
