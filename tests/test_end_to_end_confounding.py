"""End-to-end: point sc-referee at a folder -> ingest -> confounding -> earned blocker.

This is the D1 deliverable in miniature: the whole propose/confirm/check loop, minus the
LLM proposal (the design is the committed, human-confirmed sc-referee.yaml), producing the
guaranteed, power-independent blocker against a fixture of known structure.
"""
import json

from fixtures.confounding_alias.make_fixture import build
from sc_referee.checks.confounding import ConfoundingCheck
from sc_referee.config import load_designs
from sc_referee.ingest import ingest


def test_confounding_alias_fixture_is_blocker(tmp_path):
    build(tmp_path)

    bundle = ingest(tmp_path)
    designs = load_designs(tmp_path / "sc-referee.yaml")
    finding = ConfoundingCheck().run(designs[0], bundle)

    expected = json.loads((tmp_path / "expected_report.json").read_text())
    assert finding.status == expected["checks"]["confounding"]["status"] == "blocker"

    # the plain-language verdict names the real culprit (condition aliased with the run)
    assert "processing_run" in finding.verdict

    # folder discovery resolved the roles the fixture expects
    for role in expected["provenance_must_include"]:
        assert role in bundle.provenance


def test_ingest_detects_replicate_var(tmp_path):
    build(tmp_path)
    bundle = ingest(tmp_path)
    assert bundle.replicate_var == "donor_id"
