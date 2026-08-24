from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

from sc_referee.cli import _default_schema_root, app
from sc_referee.records.schema_registry import LocalSchemaRegistry


def _relative_files(root: Path) -> list[Path]:
    return sorted(
        path.relative_to(root)
        for path in root.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") or part == "__pycache__" for part in path.parts)
        and path.suffix != ".pyc"
    )


def test_packaged_schema_release_is_exact_copy(project_root: Path) -> None:
    for version in ("0.19.0", "0.20.0", "0.21.0"):
        public_root = project_root / "reference" / f"schemas-v{version}"
        packaged_root = project_root / "src" / "sc_referee" / "resources" / f"schemas-v{version}"

        assert _relative_files(packaged_root) == _relative_files(public_root)
        for relative_path in _relative_files(public_root):
            assert (packaged_root / relative_path).read_bytes() == (
                public_root / relative_path
            ).read_bytes()


def test_default_schema_root_uses_installed_package_resources(
    monkeypatch: object, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)  # type: ignore[attr-defined]

    root = _default_schema_root()

    assert root == Path(__file__).resolve().parents[1] / "src" / "sc_referee" / "resources" / (
        "schemas-v0.21.0"
    )
    assert LocalSchemaRegistry(root).validate_example_directory() == 81


def test_version_distinguishes_program_schema_and_starter_lineage() -> None:
    result = CliRunner().invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout == ("sc-referee 0.3.0 (schema 0.21.0; starter lineage 0.1.0)\n")


def test_numpy_is_a_direct_python_311_compatible_dependency(project_root: Path) -> None:
    pyproject = tomllib.loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))

    assert "numpy>=1.26,<2.5" in pyproject["project"]["dependencies"]


def test_handoff_manifest_includes_runtime_and_skill_but_not_build_outputs(
    project_root: Path,
) -> None:
    rows = (project_root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    paths = {row.split("  ", maxsplit=1)[1] for row in rows}

    assert ".agents/skills/scientific-audit/SKILL.md" in paths
    assert ".agents/skills/method-contract/SKILL.md" in paths
    assert ".agents/plugins/marketplace.json" in paths
    assert "plugins/sc-referee/.codex-plugin/plugin.json" in paths
    assert "plugins/sc-referee/skills/scientific-audit/SKILL.md" in paths
    assert "plugins/sc-referee/skills/method-contract/SKILL.md" in paths
    assert "docs/QUICKSTART.md" in paths
    assert "docs/AGENTIC_SKILL.md" in paths
    assert "docs/CAPABILITIES.md" in paths
    assert "docs/MIGRATION.md" in paths
    assert "src/sc_referee/agent_protocol.py" in paths
    assert "evaluation/pyproject.toml" in paths
    assert "evaluation/src/sc_referee_evaluation/validation.py" in paths
    assert "evaluation/src/sc_referee_evaluation/stage3.py" in paths
    assert "evaluation/src/sc_referee_evaluation/prospective_selected_result_verifier.py" in paths
    assert "src/sc_referee/records/evaluation_candidate.py" in paths
    assert (
        "src/sc_referee/resources/schemas-v0.19.0/schemas/v0.19.0/audit-bundle.schema.json" in paths
    )
    assert not any(path.startswith(("build/", "dist/")) for path in paths)
