from __future__ import annotations

import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(),
                    reason="git worktree unavailable")
def test_demo_whitelists_do_not_reinclude_machine_or_secret_files():
    ignored = (
        "demos/biermann-pseudoreplication/.DS_Store",
        "demos/biermann-pseudoreplication/.Rhistory",
        "demos/biermann-pseudoreplication/__pycache__/analysis.pyc",
        "demos/multi-claim-pipeline/.env",
        "demos/multi-claim-pipeline/.env.local",
    )
    for path in ignored:
        result = subprocess.run(["git", "check-ignore", "--no-index", "-q", path], cwd=ROOT)
        assert result.returncode == 0, path

    allowed = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "demos/multi-claim-pipeline/README.md"],
        cwd=ROOT,
    )
    assert allowed.returncode == 1


def test_data_fetch_dependency_is_declared():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    data = project["project"]["optional-dependencies"]["data"]
    assert any(requirement.startswith("synapseclient") for requirement in data)

