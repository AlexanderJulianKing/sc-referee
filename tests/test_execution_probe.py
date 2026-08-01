from __future__ import annotations

import json
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from sc_referee.cli import app
from sc_referee.core.ids import canonical_json, semantic_digest, sha256_digest, stable_id
from sc_referee.execution_capability import ProbeLimits
from sc_referee.execution_probe import CommandResult, _artifact_records, probe_podman_backend
from sc_referee.execution_probe_package import (
    CapabilityProbePackageError,
    verify_capability_probe_package_structure,
)
from sc_referee.records.schema_registry import LocalSchemaRegistry


class _FakePodmanRunner:
    def __init__(self, *, rootless: bool = True, network_denied: bool = True) -> None:
        self.rootless = rootless
        self.network_denied = network_denied
        self.calls: list[tuple[str, ...]] = []
        self.info_calls = 0

    def run(self, argv: tuple[str, ...], *, timeout_seconds: int) -> CommandResult:
        self.calls.append(argv)
        if argv[1:4] == ("info", "--format", "json"):
            self.info_calls += 1
            payload = {
                "host": {
                    "arch": "amd64",
                    "kernel": "6.12.0",
                    "os": "linux",
                    "ociRuntime": {"name": "crun", "version": "1.17"},
                    "remoteSocket": {"path": "unix:///run/user/1000/podman/podman.sock"},
                    "security": {"rootless": self.rootless},
                },
                "version": {"Version": "5.0.0"},
            }
            return CommandResult(argv, 0, json.dumps(payload), "", False)
        if argv[1:4] == ("version", "--format", "json"):
            return CommandResult(argv, 0, '{"Client":{"Version":"5.0.0"}}', "", False)
        if argv[1:3] == ("image", "inspect"):
            digest = "a" * 64
            return CommandResult(
                argv,
                0,
                json.dumps([{"Digest": f"sha256:{digest}", "RepoDigests": [argv[3]]}]),
                "",
                False,
            )
        if argv[1] == "create":
            return CommandResult(argv, 0, "container-id\n", "", False)
        if argv[1:3] == ("start", "--attach") and "-wall-" in argv[-1]:
            return CommandResult(argv, None, "", "", True)
        if argv[1:3] == ("start", "--attach"):
            controls = {
                "capabilities_dropped": True,
                "cpu_limit_enforced": True,
                "device_access_restricted": True,
                "memory_limit_enforced": True,
                "network_denied": self.network_denied,
                "no_new_privileges": True,
                "open_file_limit_enforced": True,
                "process_limit_enforced": True,
                "repository_read_only": True,
                "separate_writable_root": True,
                "writable_bytes_enforced": True,
            }
            return CommandResult(argv, 0, json.dumps(controls), "", False)
        if argv[1] in {"kill", "rm"}:
            return CommandResult(argv, 0, "", "", False)
        raise AssertionError(f"unexpected command: {argv}")


def _request(tmp_path: Path) -> dict[str, object]:
    executable = tmp_path / "podman"
    executable.write_bytes(b"fake-podman-binary")
    executable.chmod(0o755)
    return {
        "executable": executable,
        "image_reference": "localhost/sc-referee-probe@sha256:" + "a" * 64,
        "audit_run_id": "audit:probe-test",
        "output": tmp_path / "probe-output",
        "captured_at": "2026-07-29T18:00:00Z",
        "expires_at": "2026-07-29T19:00:00Z",
        "limits": ProbeLimits(
            wall_time_seconds=2,
            cpu_quota_millis=500,
            memory_bytes=67_108_864,
            process_count=16,
            open_files=32,
            writable_bytes=1_048_576,
        ),
    }


def test_podman_probe_uses_closed_control_argv_and_writes_valid_evidence(
    schema_root: Path, tmp_path: Path
) -> None:
    runner = _FakePodmanRunner()
    package = probe_podman_backend(**_request(tmp_path), runner=runner, schema_root=schema_root)

    LocalSchemaRegistry(schema_root).validate(package.capability)
    LocalSchemaRegistry(schema_root).validate(package.log_artifact)
    assert package.capability["project_code_execution_supported"] is True
    create = next(call for call in runner.calls if call[1] == "create")
    joined = " ".join(create)
    for expected in (
        "--pull=never",
        "--read-only",
        "--network=none",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=16",
        "--memory=67108864",
        "--cpus=0.5",
        "--ulimit=nofile=32:32",
        "destination=/project,ro=true",
        "--workdir=/project",
    ):
        assert expected in joined
    assert not any(token in create for token in ("--privileged", "--device", "--publish"))
    assert (package.output_root / "sandbox-capability.json").is_file()
    assert (package.output_root / "probe-log.artifact.json").is_file()
    assert (package.output_root / "probe-transcript.json").is_file()


def test_probe_package_structure_recomputes_closure_without_running_commands(
    schema_root: Path, tmp_path: Path
) -> None:
    runner = _FakePodmanRunner()
    package = probe_podman_backend(**_request(tmp_path), runner=runner, schema_root=schema_root)
    calls_before_verification = list(runner.calls)

    verified = verify_capability_probe_package_structure(
        package.output_root, schema_root=schema_root
    )

    assert verified.capability == package.capability
    assert verified.log_artifact == package.log_artifact
    assert verified.log_asset_identity == package.log_asset_identity
    assert semantic_digest(verified.transcript) == semantic_digest(package.transcript)
    assert (
        verified.transcript_digest
        == package.capability["capability_evidence"]["probe_artifact_digest"]
    )
    assert runner.calls == calls_before_verification


def _mutate_transcript(value: dict[str, Any]) -> None:
    value["selected_backend_info"]["arch"] = "arm64"


def _mutate_capability(value: dict[str, Any]) -> None:
    value["capability_evidence"]["probe_artifact_digest"] = "sha256:" + "b" * 64


def _mutate_artifact(value: dict[str, Any]) -> None:
    value["audit_run_id"] = "audit:substituted"


def _mutate_identity(value: dict[str, Any]) -> None:
    value["identity_evidence"]["digest"] = "sha256:" + "b" * 64


@pytest.mark.parametrize(
    ("filename", "mutate"),
    (
        ("probe-transcript.json", _mutate_transcript),
        ("sandbox-capability.json", _mutate_capability),
        ("probe-log.artifact.json", _mutate_artifact),
        ("probe-log.asset-identity.json", _mutate_identity),
    ),
)
def test_probe_package_structure_rejects_canonical_component_mutation(
    filename: str,
    mutate: Callable[[dict[str, Any]], None],
    schema_root: Path,
    tmp_path: Path,
) -> None:
    package = probe_podman_backend(
        **_request(tmp_path), runner=_FakePodmanRunner(), schema_root=schema_root
    )
    path = package.output_root / filename
    value = json.loads(path.read_text(encoding="utf-8"))
    mutate(value)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")

    with pytest.raises(CapabilityProbePackageError):
        verify_capability_probe_package_structure(package.output_root, schema_root=schema_root)


def test_probe_package_structure_rejects_noncanonical_json(
    schema_root: Path, tmp_path: Path
) -> None:
    package = probe_podman_backend(
        **_request(tmp_path), runner=_FakePodmanRunner(), schema_root=schema_root
    )
    capability_path = package.output_root / "sandbox-capability.json"
    value = json.loads(capability_path.read_text(encoding="utf-8"))
    capability_path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(CapabilityProbePackageError, match="not canonical"):
        verify_capability_probe_package_structure(package.output_root, schema_root=schema_root)


def test_probe_package_structure_rejects_open_inventory(schema_root: Path, tmp_path: Path) -> None:
    package = probe_podman_backend(
        **_request(tmp_path), runner=_FakePodmanRunner(), schema_root=schema_root
    )
    (package.output_root / "unbound.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(CapabilityProbePackageError, match="inventory mismatch"):
        verify_capability_probe_package_structure(package.output_root, schema_root=schema_root)


def test_probe_package_structure_rejects_multiply_linked_file(
    schema_root: Path, tmp_path: Path
) -> None:
    package = probe_podman_backend(
        **_request(tmp_path), runner=_FakePodmanRunner(), schema_root=schema_root
    )
    artifact = package.output_root / "probe-log.artifact.json"
    external_alias = tmp_path / "external-artifact-alias.json"
    os.link(artifact, external_alias)

    with pytest.raises(CapabilityProbePackageError, match="external hard links"):
        verify_capability_probe_package_structure(package.output_root, schema_root=schema_root)


def test_probe_package_structure_rejects_changed_or_linked_probe_input(
    schema_root: Path, tmp_path: Path
) -> None:
    package = probe_podman_backend(
        **_request(tmp_path), runner=_FakePodmanRunner(), schema_root=schema_root
    )
    probe_input = package.output_root / "auditor-probe-input" / "probe-input.txt"
    probe_input.write_bytes(b"changed\n")
    with pytest.raises(CapabilityProbePackageError, match="input bytes"):
        verify_capability_probe_package_structure(package.output_root, schema_root=schema_root)

    probe_input.unlink()
    probe_input.symlink_to(package.output_root / "probe-transcript.json")
    with pytest.raises(CapabilityProbePackageError, match="regular file"):
        verify_capability_probe_package_structure(package.output_root, schema_root=schema_root)


def test_copied_probe_package_is_only_structurally_verifiable(
    schema_root: Path, tmp_path: Path
) -> None:
    package = probe_podman_backend(
        **_request(tmp_path), runner=_FakePodmanRunner(), schema_root=schema_root
    )
    copied = tmp_path / "copied-probe-output"
    shutil.copytree(package.output_root, copied)

    verified = verify_capability_probe_package_structure(copied, schema_root=schema_root)

    assert verified.capability == package.capability
    # This result intentionally has no launch-admission method or authority flag. The separate
    # execute-authorized guard test proves that standalone/copyable evidence cannot reach runtime.
    assert not hasattr(verified, "authorize_execution")


def test_probe_package_structure_rejects_digest_rebound_command_drift(
    schema_root: Path, tmp_path: Path
) -> None:
    package = probe_podman_backend(
        **_request(tmp_path), runner=_FakePodmanRunner(), schema_root=schema_root
    )
    transcript_path = package.output_root / "probe-transcript.json"
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    create_argv = transcript["commands"][3]["argv"]
    create_argv[create_argv.index("--network=none")] = "--network=host"
    transcript_payload = (canonical_json(transcript) + "\n").encode()
    transcript_path.write_bytes(transcript_payload)
    transcript_digest = sha256_digest(transcript_payload)

    capability_path = package.output_root / "sandbox-capability.json"
    capability = json.loads(capability_path.read_text(encoding="utf-8"))
    evidence = capability["capability_evidence"]
    old_artifact_id = evidence["probe_log_refs"][0]["record_id"]
    evidence["probe_artifact_digest"] = transcript_digest
    limits = canonical_json(evidence["tested_limits"])
    capability["sandbox_capability_id"] = stable_id(
        "sandbox",
        evidence["probe_profile"],
        evidence["backend"]["backend_kind"],
        evidence["backend"]["executable_digest"],
        evidence["endpoint"]["connection_id"],
        evidence["endpoint"]["service_id"],
        evidence["normalized_info_digest"],
        transcript_digest,
        limits,
        evidence["captured_at"],
    )

    artifact_path = package.output_root / "probe-log.artifact.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    new_artifact, new_identity = _artifact_records(
        audit_run_id=artifact["audit_run_id"],
        captured_at=evidence["captured_at"],
        transcript_digest=transcript_digest,
    )
    assert new_artifact["artifact_id"] != old_artifact_id
    evidence["probe_log_refs"] = [
        {"record_type": "artifact", "record_id": new_artifact["artifact_id"]}
    ]
    capability_path.write_text(canonical_json(capability) + "\n", encoding="utf-8")
    artifact_path.write_text(canonical_json(new_artifact) + "\n", encoding="utf-8")
    (package.output_root / "probe-log.asset-identity.json").write_text(
        canonical_json(new_identity) + "\n", encoding="utf-8"
    )

    with pytest.raises(CapabilityProbePackageError, match="closed profile"):
        verify_capability_probe_package_structure(package.output_root, schema_root=schema_root)


def test_rootful_backend_never_runs_probe_container(schema_root: Path, tmp_path: Path) -> None:
    runner = _FakePodmanRunner(rootless=False)
    package = probe_podman_backend(**_request(tmp_path), runner=runner, schema_root=schema_root)

    assert package.capability["project_code_execution_supported"] is False
    assert package.capability["capability_evidence"] is None
    assert not any(call[1] == "create" for call in runner.calls)


def test_failed_effective_network_probe_fails_closed(schema_root: Path, tmp_path: Path) -> None:
    runner = _FakePodmanRunner(network_denied=False)
    package = probe_podman_backend(**_request(tmp_path), runner=runner, schema_root=schema_root)

    assert package.capability["project_code_execution_supported"] is False
    assert package.capability["capability_evidence"] is None


def test_probe_output_is_create_only(schema_root: Path, tmp_path: Path) -> None:
    request = _request(tmp_path)
    probe_podman_backend(**request, runner=_FakePodmanRunner(), schema_root=schema_root)

    try:
        probe_podman_backend(**request, runner=_FakePodmanRunner(), schema_root=schema_root)
    except FileExistsError:
        pass
    else:
        raise AssertionError("probe output was overwritten")


def test_cli_records_absent_backend_without_running_project_code(
    monkeypatch: object, tmp_path: Path
) -> None:
    monkeypatch.setattr("sc_referee.cli.shutil.which", lambda _name: None)  # type: ignore[attr-defined]
    output = tmp_path / "unavailable"

    result = CliRunner().invoke(
        app,
        ["probe-execution-capability", "--output", str(output)],
    )

    assert result.exit_code == 0
    record = json.loads((output / "sandbox-capability.json").read_text(encoding="utf-8"))
    assert record["project_code_execution_supported"] is False
    assert record["backend_kind"] == "no_execution"
