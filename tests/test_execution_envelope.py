from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from sc_referee.core.ids import semantic_digest
from sc_referee.execution_envelope import (
    ExecutionEnvelopeError,
    build_podman_execution_argv,
    capture_stopped_container_outputs,
)


def _authorization(project_root: Path) -> dict[str, object]:
    authorization = json.loads(
        (
            project_root
            / "reference"
            / "schemas-v0.20.0"
            / "examples"
            / "project-execution-authorization.example.json"
        ).read_text(encoding="utf-8")
    )
    authorization["command"]["normalized_digest"] = semantic_digest(
        authorization["command"]["argv"]
    )
    authorization["environment"]["normalized_digest"] = semantic_digest(
        authorization["environment"]["entries"]
    )
    return authorization


def test_launch_argv_is_closed_and_contains_every_authorized_control(
    project_root: Path, tmp_path: Path
) -> None:
    authorization = _authorization(project_root)
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()

    argv = build_podman_execution_argv(
        Path("/usr/bin/podman"), authorization, snapshot, "sc-referee-execution-example"
    )

    joined = " ".join(argv)
    assert argv[:2] == ("/usr/bin/podman", "create")
    for expected in (
        "--pull=never",
        "--read-only",
        "--network=none",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--user=65532:65532",
        "--pids-limit=32",
        "--memory=268435456",
        "--cpus=1",
        "--ulimit=nofile=64:64",
        "destination=/project,ro=true",
        "--workdir=/project",
        "--env=PYTHONHASHSEED=0",
    ):
        assert expected in joined
    assert not any(token in argv for token in ("--privileged", "--device", "--publish"))
    image_index = argv.index(str(authorization["image"]["reference"]))  # type: ignore[index]
    assert argv[image_index + 1 :] == tuple(authorization["command"]["argv"])  # type: ignore[index]


@pytest.mark.parametrize(
    "mutation",
    [
        {"network_policy": "allowed"},
        {"image_reference": "localhost/probe:latest"},
        {"image_digest": "sha256:" + "f" * 64},
        {"command": ["/bin/sh", "-c", "echo unsafe"]},
        {"command": ["bash", "analysis.sh"]},
        {"environment": [{"name": "LD_PRELOAD", "value": "/project/hook.so"}]},
    ],
)
def test_launch_argv_rejects_policy_drift_or_initial_profile_escalation(
    project_root: Path, tmp_path: Path, mutation: dict[str, object]
) -> None:
    authorization = _authorization(project_root)
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    if "network_policy" in mutation:
        authorization["network_policy"] = mutation["network_policy"]
    if "image_reference" in mutation:
        authorization["image"]["reference"] = mutation["image_reference"]  # type: ignore[index]
    if "image_digest" in mutation:
        authorization["image"]["manifest_digest"] = mutation["image_digest"]  # type: ignore[index]
    if "command" in mutation:
        authorization["command"]["argv"] = mutation["command"]  # type: ignore[index]
    if "environment" in mutation:
        authorization["environment"]["entries"] = mutation["environment"]  # type: ignore[index]

    with pytest.raises(ExecutionEnvelopeError):
        build_podman_execution_argv(
            Path("/usr/bin/podman"), authorization, snapshot, "sc-referee-execution-example"
        )


def test_snapshot_mount_must_be_a_real_directory(project_root: Path, tmp_path: Path) -> None:
    authorization = _authorization(project_root)
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)

    with pytest.raises(ExecutionEnvelopeError, match="snapshot"):
        build_podman_execution_argv(
            Path("/usr/bin/podman"), authorization, alias, "sc-referee-execution-example"
        )


def test_output_capture_accepts_only_exact_regular_paths_and_hashes_bytes(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "result.json").write_bytes(b'{"estimate":1.25}\n')
    destination = tmp_path / "accepted"

    manifest = capture_stopped_container_outputs(
        staging,
        destination,
        allowed_output_paths=("result.json",),
        logical_byte_limit=1024,
        project_processes_quiescent=True,
        cleanup_observed=True,
    )

    assert (destination / "result.json").read_bytes() == b'{"estimate":1.25}\n'
    assert manifest["total_logical_bytes"] == 18
    assert manifest["entries"] == [
        {
            "digest": "sha256:e3cba7a46b9d1c79ad6f221f2a850484d1414875b5657264548e98c30ad12b7d",
            "path": "result.json",
            "size_bytes": 18,
        }
    ]


@pytest.mark.parametrize("quiescent,cleanup", [(False, True), (True, False)])
def test_output_capture_requires_quiescence_and_cleanup(
    tmp_path: Path, quiescent: bool, cleanup: bool
) -> None:
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "result.json").write_text("ok", encoding="utf-8")

    with pytest.raises(ExecutionEnvelopeError):
        capture_stopped_container_outputs(
            staging,
            tmp_path / "accepted",
            allowed_output_paths=("result.json",),
            logical_byte_limit=1024,
            project_processes_quiescent=quiescent,
            cleanup_observed=cleanup,
        )


def test_output_capture_rejects_unexpected_symlink_special_escape_and_excess(
    tmp_path: Path,
) -> None:
    scenarios: list[tuple[str, tuple[str, ...], int]] = []

    unexpected = tmp_path / "unexpected"
    unexpected.mkdir()
    (unexpected / "extra.txt").write_text("x", encoding="utf-8")
    scenarios.append(("unexpected", ("result.json",), 1024))

    symlink = tmp_path / "symlink"
    symlink.mkdir()
    (symlink / "result.json").symlink_to("../outside")
    scenarios.append(("symlink", ("result.json",), 1024))

    special = tmp_path / "special"
    special.mkdir()
    os.mkfifo(special / "result.json")
    scenarios.append(("special", ("result.json",), 1024))

    excess = tmp_path / "excess"
    excess.mkdir()
    (excess / "result.json").write_bytes(b"x" * 20)
    scenarios.append(("excess", ("result.json",), 10))

    for directory, allowed, limit in scenarios:
        with pytest.raises(ExecutionEnvelopeError):
            capture_stopped_container_outputs(
                tmp_path / directory,
                tmp_path / f"accepted-{directory}",
                allowed_output_paths=allowed,
                logical_byte_limit=limit,
                project_processes_quiescent=True,
                cleanup_observed=True,
            )

    with pytest.raises(ExecutionEnvelopeError):
        capture_stopped_container_outputs(
            excess,
            tmp_path / "accepted-escape",
            allowed_output_paths=("../result.json",),
            logical_byte_limit=1024,
            project_processes_quiescent=True,
            cleanup_observed=True,
        )


def test_output_capture_never_replaces_existing_destination(
    project_root: Path, tmp_path: Path
) -> None:
    del project_root
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "result.json").write_text("ok", encoding="utf-8")
    destination = tmp_path / "accepted"
    destination.mkdir()

    with pytest.raises(FileExistsError):
        capture_stopped_container_outputs(
            staging,
            destination,
            allowed_output_paths=("result.json",),
            logical_byte_limit=1024,
            project_processes_quiescent=True,
            cleanup_observed=True,
        )
