from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sc_referee.core.ids import canonical_json, stable_id
from sc_referee.version import SCHEMA_VERSION, __version__

PROBE_PROFILE = "rootless-oci-capability-probe-v1"
BackendKind = Literal["podman_rootless", "docker_rootless"]

EFFECTIVE_CONTROL_NAMES = (
    "capabilities_dropped",
    "cpu_limit_enforced",
    "device_access_restricted",
    "memory_limit_enforced",
    "network_denied",
    "no_new_privileges",
    "open_file_limit_enforced",
    "process_limit_enforced",
    "repository_read_only",
    "separate_writable_root",
    "wall_time_enforced",
    "writable_bytes_enforced",
)


@dataclass(frozen=True)
class ProbeLimits:
    wall_time_seconds: int
    cpu_quota_millis: int
    memory_bytes: int
    process_count: int
    open_files: int
    writable_bytes: int

    def public_record(self) -> dict[str, int]:
        return {
            "cpu_quota_millis": self.cpu_quota_millis,
            "memory_bytes": self.memory_bytes,
            "open_files": self.open_files,
            "process_count": self.process_count,
            "wall_time_seconds": self.wall_time_seconds,
            "writable_bytes": self.writable_bytes,
        }


@dataclass(frozen=True)
class ProbeObservation:
    """Closed observations from a versioned auditor-owned OCI probe.

    This object is deliberately not a public record.  Only the fail-closed compiler below may
    promote its values into a qualifying SandboxCapability.
    """

    backend_kind: BackendKind
    backend_name: str
    backend_version: str
    executable_path: str
    executable_digest: str
    endpoint_transport: str
    connection_id: str
    service_id: str
    machine_id: str | None
    arbitrary_remote: bool
    normalized_info_digest: str
    rootless_reported: bool
    probe_outcome: str
    effective_controls: Mapping[str, bool]
    tested_limits: ProbeLimits
    host_system: str
    host_release: str
    host_machine: str
    oci_runtime_name: str
    oci_runtime_version: str
    probe_log_ref: Mapping[str, str]
    probe_artifact_digest: str
    captured_at: str
    expires_at: str
    limitations: tuple[str, ...]
    machine_identity_stable: bool = True
    evidence_fresh: bool = True


def _timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _digest_is_valid(value: str) -> bool:
    return (
        len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _qualification_failures(observation: ProbeObservation) -> list[str]:
    failures: list[str] = []
    if observation.backend_kind not in {"podman_rootless", "docker_rootless"}:
        failures.append("backend_kind_not_supported")
    if not observation.rootless_reported:
        failures.append("rootless_reported_false")
    if observation.endpoint_transport not in {"local_unix_socket", "podman_managed_machine"}:
        failures.append("endpoint_transport_not_bound")
    if observation.arbitrary_remote:
        failures.append("arbitrary_remote_true")
    if not observation.machine_identity_stable:
        failures.append("machine_identity_stable_false")
    if not observation.evidence_fresh:
        failures.append("evidence_fresh_false")
    if observation.probe_outcome != "passed":
        failures.append("probe_outcome_not_passed")

    actual_controls = set(observation.effective_controls)
    expected_controls = set(EFFECTIVE_CONTROL_NAMES)
    for missing in sorted(expected_controls - actual_controls):
        failures.append(f"{missing}_missing")
    for unexpected in sorted(actual_controls - expected_controls):
        failures.append(f"{unexpected}_unexpected")
    for control in EFFECTIVE_CONTROL_NAMES:
        if observation.effective_controls.get(control) is not True:
            failures.append(f"{control}_false")

    limits = observation.tested_limits.public_record()
    for name, value in limits.items():
        if value <= 0:
            failures.append(f"{name}_not_positive")
    if not _digest_is_valid(observation.executable_digest):
        failures.append("executable_digest_invalid")
    if not _digest_is_valid(observation.normalized_info_digest):
        failures.append("normalized_info_digest_invalid")
    if not _digest_is_valid(observation.probe_artifact_digest):
        failures.append("probe_artifact_digest_invalid")
    if dict(observation.probe_log_ref).get("record_type") != "artifact" or not dict(
        observation.probe_log_ref
    ).get("record_id"):
        failures.append("probe_log_ref_invalid")

    captured = _timestamp(observation.captured_at)
    expires = _timestamp(observation.expires_at)
    if captured is None:
        failures.append("captured_at_invalid")
    if expires is None:
        failures.append("expires_at_invalid")
    if captured is not None and expires is not None and expires <= captured:
        failures.append("evidence_expiry_not_after_capture")
    return sorted(set(failures))


def _public_controls(effective: Mapping[str, bool], *, supported: bool) -> dict[str, bool]:
    if not supported:
        return {
            "capabilities_dropped": False,
            "device_access_restricted": False,
            "network_default_denied": False,
            "no_new_privileges": False,
            "open_file_limits_enforced": False,
            "process_limits_enforced": False,
            "repository_read_only": False,
            "resource_limits_enforced": False,
            "wall_time_enforced": False,
            "writable_bytes_enforced": False,
            "writable_roots_enforced": False,
        }
    return {
        "capabilities_dropped": effective["capabilities_dropped"],
        "device_access_restricted": effective["device_access_restricted"],
        "network_default_denied": effective["network_denied"],
        "no_new_privileges": effective["no_new_privileges"],
        "open_file_limits_enforced": effective["open_file_limit_enforced"],
        "process_limits_enforced": effective["process_limit_enforced"],
        "repository_read_only": effective["repository_read_only"],
        "resource_limits_enforced": (
            effective["cpu_limit_enforced"] and effective["memory_limit_enforced"]
        ),
        "wall_time_enforced": effective["wall_time_enforced"],
        "writable_bytes_enforced": effective["writable_bytes_enforced"],
        "writable_roots_enforced": effective["separate_writable_root"],
    }


def compile_sandbox_capability(observation: ProbeObservation) -> dict[str, object]:
    """Compile probe observations into a schema-valid, fail-closed capability record."""

    failures = _qualification_failures(observation)
    supported = not failures
    capability_id = stable_id(
        "sandbox",
        PROBE_PROFILE,
        observation.backend_kind,
        observation.executable_digest,
        observation.connection_id,
        observation.service_id,
        observation.normalized_info_digest,
        observation.probe_artifact_digest,
        canonical_json(observation.tested_limits.public_record()),
        observation.captured_at,
    )
    limitations = list(observation.limitations)
    limitations.extend(f"Capability probe did not qualify: {failure}." for failure in failures)
    if not limitations:
        limitations.append("Host-kernel isolation is shared with the container runtime.")

    evidence: dict[str, object] | None = None
    if supported:
        evidence = {
            "backend": {
                "backend_kind": observation.backend_kind,
                "executable_path": observation.executable_path,
                "executable_digest": observation.executable_digest,
                "version": observation.backend_version,
            },
            "captured_at": observation.captured_at,
            "effective_controls": dict(observation.effective_controls),
            "endpoint": {
                "arbitrary_remote": False,
                "connection_id": observation.connection_id,
                "machine_id": observation.machine_id,
                "service_id": observation.service_id,
                "transport": observation.endpoint_transport,
            },
            "expires_at": observation.expires_at,
            "host_platform": {
                "machine": observation.host_machine,
                "release": observation.host_release,
                "system": observation.host_system,
            },
            "normalized_info_digest": observation.normalized_info_digest,
            "oci_runtime": {
                "name": observation.oci_runtime_name,
                "version": observation.oci_runtime_version,
            },
            "probe_artifact_digest": observation.probe_artifact_digest,
            "probe_log_refs": [dict(observation.probe_log_ref)],
            "probe_outcome": "passed",
            "probe_profile": PROBE_PROFILE,
            "tested_limits": observation.tested_limits.public_record(),
        }

    return {
        "backend_kind": "rootless_oci",
        "backend_name": observation.backend_name,
        "backend_version": observation.backend_version,
        "capability_evidence": evidence,
        "capability_evidence_status": (
            "complete_effective_probe" if supported else "not_supported"
        ),
        "captured_at": observation.captured_at,
        "controls": _public_controls(observation.effective_controls, supported=supported),
        "limitations": limitations,
        "project_code_execution_supported": supported,
        "provenance": {
            "actor": {
                "actor_id": "software:sc-referee-controller",
                "actor_kind": "controller",
                "display_name": "sc-referee controller",
            },
            "created_at": observation.captured_at,
            "method": "rootless_oci_capability_probe_v1",
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "record_type": "sandbox_capability",
        "rootless_verified": supported,
        "sandbox_capability_id": capability_id,
        "schema_version": SCHEMA_VERSION,
        "unsafe_fallback_available": False,
    }


def compile_unavailable_capability(*, captured_at: str, reason: str) -> dict[str, object]:
    """Represent backend absence without converting it into execution support or a Finding."""

    if not reason.strip():
        raise ValueError("unavailable capability reason must be nonempty")
    return {
        "backend_kind": "no_execution",
        "backend_name": "No qualifying rootless OCI backend",
        "capability_evidence": None,
        "capability_evidence_status": "not_supported",
        "captured_at": captured_at,
        "controls": _public_controls({}, supported=False),
        "limitations": [reason.strip()],
        "project_code_execution_supported": False,
        "provenance": {
            "actor": {
                "actor_id": "software:sc-referee-controller",
                "actor_kind": "controller",
                "display_name": "sc-referee controller",
            },
            "created_at": captured_at,
            "method": "rootless_oci_capability_probe_v1",
            "tool": "sc-referee",
            "tool_version": __version__,
        },
        "record_type": "sandbox_capability",
        "rootless_verified": False,
        "sandbox_capability_id": stable_id(
            "sandbox", PROBE_PROFILE, "unavailable", captured_at, reason.strip()
        ),
        "schema_version": SCHEMA_VERSION,
        "unsafe_fallback_available": False,
    }
