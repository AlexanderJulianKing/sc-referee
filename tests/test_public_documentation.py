from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from typer.testing import CliRunner

from sc_referee.calculation_checks.profiles import default_calculation_check_registry
from sc_referee.cli import app
from sc_referee.scientific_checks.profiles import default_scientific_check_registry

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


def test_public_documentation_completes_the_newcomer_interaction_path(
    project_root: Path,
) -> None:
    agents = (project_root / "AGENTS.md").read_text(encoding="utf-8")
    quickstart = (project_root / "docs" / "QUICKSTART.md").read_text(encoding="utf-8")

    assert "Current accepted public JSON Schemas in `reference/schemas-v0.18.0/`" in agents
    assert "Current accepted public JSON Schemas in `reference/schemas-v0.17.0/`" not in agents
    for command in (
        "sc-referee work-packet",
        "sc-referee submit-proposals",
        "sc-referee questions",
        "sc-referee record-answer",
        "sc-referee record-structured-answer",
        "sc-referee lock-semantics",
        "sc-referee status",
    ):
        assert command in quickstart
    assert (
        "The proposal remains proposed and cannot select an answer for the scientist" in quickstart
    )
    assert "### Worked interpretation example" in quickstart
    assert "zero Findings, one MaterialQuestion, and twenty" in quickstart
    assert "overall coverage is partial" in quickstart
    assert "does not establish that the workflow is correct or publication-ready" in quickstart


def test_task_board_freezes_post_mpp_dependency_and_regression_policy(
    project_root: Path,
) -> None:
    task_board = (project_root / "docs" / "implementation" / "TASK_BOARD.md").read_text(
        encoding="utf-8"
    )
    backlog = (project_root / "docs" / "implementation" / "POST_MPP_PRODUCT_BACKLOG.md").read_text(
        encoding="utf-8"
    )

    assert "POST_MPP_PRODUCT_BACKLOG.md" in task_board
    assert "L01 through L06 are" in task_board
    assert "start with L07 Python and R source adapters" in task_board
    scientific_registry = default_scientific_check_registry()
    calculation_registry = default_calculation_check_registry()
    capability_profiles = json.loads(
        (
            project_root
            / "src"
            / "sc_referee"
            / "resources"
            / "capability-manifests-v1"
            / "profile-manifests.json"
        ).read_text(encoding="utf-8")
    )["records"]
    assert f"{len(scientific_registry.modules)} active question-oriented" in backlog
    assert (
        f"through {sum(len(module.adapters) for module in scientific_registry.modules)} bounded"
        in backlog
    )
    assert f"{len(calculation_registry.modules)} active deterministic calculation-check" in backlog
    assert f"{len(capability_profiles)} published capability profiles" in backlog
    assert len(scientific_registry.method_conflict_bindings) == 1
    for task_id in (f"L{index:02d}" for index in range(1, 18)):
        assert f"**{task_id} " in backlog
    for required_control in (
        "**Positive:**",
        "**Corrected twin:**",
        "**Hard negative:**",
        "**Ambiguous:**",
        "**Unsupported:**",
        "**Counterevidence:**",
        "**Removal and sibling isolation:**",
        "**Mutation:**",
        "**No execution and no late model access:**",
        "**Replay:**",
        "**Independent false-positive control:**",
    ):
        assert required_control in backlog
    assert "- [x] **L02 — One-command corpus regression runner.**" in backlog
    assert "- [x] **L03 — Baseline every current module.**" in backlog
    assert "- [x] **L04 — Publication and input selection ergonomics.**" in backlog
    assert "- [x] **L05 — General static scope joins.**" in backlog
    assert "- [x] **L06 — Natural-language adapter expansion.**" in backlog
    assert "1. L07 through L08" in backlog
    assert "Do not begin detector promotion, MCP transport, or project execution" in backlog


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
