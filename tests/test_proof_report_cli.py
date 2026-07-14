"""The optional HTML artifact is additive and never changes audit exit semantics."""
from typer.testing import CliRunner


def test_html_is_written_for_a_blocker_and_preserves_failure_exit(tmp_path):
    from fixtures.confounding_alias.make_fixture import build
    from sc_referee.cli import app

    build(tmp_path)
    destination = tmp_path / "proof.html"
    baseline = CliRunner().invoke(app, ["audit", str(tmp_path)])
    rendered = CliRunner().invoke(
        app, ["audit", str(tmp_path), "--html", str(destination)])

    assert baseline.exit_code == rendered.exit_code == 1
    assert destination.exists()
    html = destination.read_text()
    assert "<!doctype html>" in html.lower()
    assert "Proved violation" in html
    assert "conditioning" in html
    assert "No language model participated" in html


def test_html_is_written_for_a_pass_and_preserves_success_exit(tmp_path):
    from sc_referee.cli import app
    from tests.test_audit import _write_eqtl_audit_fixture

    _write_eqtl_audit_fixture(tmp_path)
    destination = tmp_path / "proof.html"
    baseline = CliRunner().invoke(
        app, ["audit", str(tmp_path), "--engine", "simple"])
    rendered = CliRunner().invoke(
        app, ["audit", str(tmp_path), "--engine", "simple", "--html", str(destination)])

    assert baseline.exit_code == rendered.exit_code == 0
    assert destination.exists()
    html = destination.read_text()
    assert "Proved conformant" in html
    assert "orientation" in html
    assert "sc-referee" in html
