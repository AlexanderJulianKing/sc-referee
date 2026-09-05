from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import scripts.verify_handoff as verify_handoff
from scripts.verify_handoff import (
    V014_TO_V015_TARGET_SCHEMA_ROOT,
    V015_TO_V016_TARGET_SCHEMA_ROOT,
    V016_TO_V017_TARGET_SCHEMA_ROOT,
    V017_TO_V018_TARGET_SCHEMA_ROOT,
    V018_TO_V019_TARGET_SCHEMA_ROOT,
)


def test_handoff_migration_targets_preserve_each_public_schema_boundary() -> None:
    assert V014_TO_V015_TARGET_SCHEMA_ROOT == "reference/schemas-v0.15.0"
    assert V015_TO_V016_TARGET_SCHEMA_ROOT == "reference/schemas-v0.16.0"
    assert V016_TO_V017_TARGET_SCHEMA_ROOT == "reference/schemas-v0.17.0"
    assert V017_TO_V018_TARGET_SCHEMA_ROOT == "reference/schemas-v0.18.0"
    assert V018_TO_V019_TARGET_SCHEMA_ROOT == "reference/schemas-v0.19.0"


def test_evaluation_wheel_smoke_installs_production_dependency_first(
    monkeypatch: Any, tmp_path: Path
) -> None:
    calls: list[tuple[list[str], Path, bool]] = []

    def capture(command: list[str], *, cwd: Path, check: bool) -> None:
        calls.append((command, cwd, check))

    monkeypatch.setattr(verify_handoff.subprocess, "run", capture)
    core_wheel = tmp_path / "sc_referee-0.4.0-py3-none-any.whl"
    evaluation_wheel = tmp_path / "sc_referee_evaluation-0.1.0.dev0-py3-none-any.whl"
    install_root = tmp_path / "install"

    verify_handoff._install_evaluation_smoke_wheels(
        core_wheel,
        evaluation_wheel,
        install_root,
    )

    assert [Path(command[-1]) for command, _, _ in calls] == [
        core_wheel,
        evaluation_wheel,
    ]
    assert all(command[:4] == [sys.executable, "-m", "pip", "install"] for command, _, _ in calls)
    assert all(
        command[4:7] == ["--no-deps", "--target", str(install_root)] for command, _, _ in calls
    )
    assert all(cwd == verify_handoff.ROOT and check for _, cwd, check in calls)
