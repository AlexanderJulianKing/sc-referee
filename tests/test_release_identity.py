from __future__ import annotations

import json
import subprocess
import tomllib
from pathlib import Path

import yaml

from sc_referee.version import __version__
from scripts.build_manifest import (
    INTENTIONALLY_GENERATED_ARTIFACTS,
    MANIFEST_RELATIVE_PATH,
    build_manifest_rows,
    manifest_inventory,
)


def test_public_release_version_is_coordinated(project_root: Path) -> None:
    package = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    evaluation = tomllib.loads(
        (project_root / "evaluation" / "pyproject.toml").read_text(encoding="utf-8")
    )
    handoff = json.loads((project_root / "HANDOFF_MANIFEST.json").read_text(encoding="utf-8"))

    assert __version__ == "0.3.0"
    assert package["project"]["version"] == __version__
    assert evaluation["project"]["dependencies"] == [f"sc-referee=={__version__}"]
    assert handoff["program_version"] == __version__


def test_public_release_identity_credits_human_and_ai_roles_exactly(
    project_root: Path,
) -> None:
    package = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    citation = yaml.safe_load((project_root / "CITATION.cff").read_text(encoding="utf-8"))
    acknowledgments = (project_root / "ACKNOWLEDGMENTS.md").read_text(encoding="utf-8")

    assert package["project"]["authors"] == [{"name": "Alexander King"}]
    assert package["project"]["maintainers"] == [{"name": "Alexander King"}]
    assert citation["version"] == "0.3.0"
    assert citation["authors"] == [{"family-names": "King", "given-names": "Alexander"}]
    assert citation["repository-code"] == "https://github.com/AlexanderJulianKing/sc-referee"
    assert "sole human author" in acknowledgments
    assert "OpenAI Codex" in acknowledgments
    assert "Anthropic Claude" in acknowledgments
    assert "not represented as people, copyright holders" in acknowledgments


def test_release_identity_files_are_in_the_handoff_manifest(project_root: Path) -> None:
    rows = (project_root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    paths = {row.split("  ", maxsplit=1)[1] for row in rows}

    assert "CITATION.cff" in paths
    assert "ACKNOWLEDGMENTS.md" in paths
    assert "docs/implementation/EXPERIMENT-0033-PUBLIC-RELEASE-IDENTITY.md" in paths


def test_manifest_builder_inventory_equals_git_tree_listing(project_root: Path) -> None:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "ls-tree",
            "-r",
            "--full-tree",
            "--name-only",
            "-z",
            "HEAD",
        ],
        check=True,
        capture_output=True,
    )
    tracked = {
        item.decode("utf-8", errors="strict") for item in completed.stdout.split(b"\0") if item
    }
    expected = tuple(
        sorted((tracked - {MANIFEST_RELATIVE_PATH}) | set(INTENTIONALLY_GENERATED_ARTIFACTS))
    )

    assert manifest_inventory(project_root) == expected
    assert (project_root / MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8") == (
        "\n".join(build_manifest_rows(project_root)) + "\n"
    )
