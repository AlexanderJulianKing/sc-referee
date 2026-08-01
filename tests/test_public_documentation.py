from __future__ import annotations

import re
import shutil
from pathlib import Path

from typer.testing import CliRunner

from sc_referee.cli import app

PUBLIC_DOCS = (
    "README.md",
    "docs/README.md",
    "docs/QUICKSTART.md",
    "docs/AGENTIC_SKILL.md",
    "docs/CAPABILITIES.md",
    "docs/MIGRATION.md",
    "ACKNOWLEDGMENTS.md",
)

MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _public_text(project_root: Path) -> str:
    return "\n".join(
        (project_root / relative_path).read_text(encoding="utf-8") for relative_path in PUBLIC_DOCS
    )


def test_public_documentation_links_resolve_inside_the_repository(project_root: Path) -> None:
    for relative_path in PUBLIC_DOCS:
        source = project_root / relative_path
        assert source.is_file()
        for raw_target in MARKDOWN_LINK.findall(source.read_text(encoding="utf-8")):
            target = raw_target.split("#", maxsplit=1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            assert (source.parent / target).resolve().exists(), (
                f"broken documentation link in {relative_path}: {raw_target}"
            )


def test_public_documentation_freezes_version_and_epistemic_boundaries(
    project_root: Path,
) -> None:
    text = _public_text(project_root)

    assert "sc-referee 0.3.0 (schema 0.18.0; starter lineage 0.1.0)" in text
    assert "Production audits do not execute project-authored code." in text
    assert "uninspected" in text
    assert "not no byte access" in text
    assert "Zero Findings means only" in text
    assert "correctness certificate" in text
    assert "1,211" not in text


def test_documented_demo_and_static_audit_sequences_execute(
    project_root: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    demo_output = tmp_path / "demo-audit"
    demo_replay = tmp_path / "demo-replay"

    demo = runner.invoke(
        app,
        [
            "demo",
            str(project_root / "examples" / "walking-skeleton"),
            "--output",
            str(demo_output),
        ],
    )
    assert demo.exit_code == 0, demo.output
    status = runner.invoke(app, ["status", str(demo_output), "--json"])
    assert status.exit_code == 0, status.output
    replay = runner.invoke(
        app,
        [
            "replay",
            str(demo_output / "semantic.lock.json"),
            "--output",
            str(demo_replay),
        ],
    )
    assert replay.exit_code == 0, replay.output

    project = tmp_path / "general-static"
    shutil.copytree(project_root / "examples" / "general-static", project)
    audit_output = tmp_path / "general-audit"
    audit_replay = tmp_path / "general-replay"
    audit = runner.invoke(
        app,
        [
            "audit",
            str(project),
            "--output",
            str(audit_output),
            "--mode",
            "quick",
            "--report",
            "report.md",
            "--material-input",
            "data.csv",
        ],
    )
    assert audit.exit_code == 0, audit.output
    status = runner.invoke(app, ["status", str(audit_output), "--json"])
    assert status.exit_code == 0, status.output
    replay = runner.invoke(
        app,
        [
            "replay",
            str(audit_output / "semantic.lock.json"),
            "--output",
            str(audit_replay),
        ],
    )
    assert replay.exit_code == 0, replay.output
