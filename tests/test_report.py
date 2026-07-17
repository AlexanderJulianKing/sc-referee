"""Frozen presentation contract for the Phase 1 per-claim report ledger."""
from __future__ import annotations

import json
from dataclasses import replace

from rich.console import Console

from fixtures.confounding_alias.make_fixture import build
from sc_referee import statuses as S
from sc_referee.audit import AuditResult, run_audit
from sc_referee.checks.base import Finding
from sc_referee.report import render_tty, to_json, to_md


def test_conditional_major_has_distinct_tty_markdown_and_json_marker():
    from sc_referee.checks.confounding_random_intercept_conditional import (
        ConfoundingRandomInterceptConditionalCheck,
    )
    from tests.test_confounding_random_intercept_conditional import _material_case

    design, bundle = _material_case(ratified=True)
    finding = ConfoundingRandomInterceptConditionalCheck().run(design, bundle)
    result = AuditResult(findings=[finding], analysis_type="condition_contrast_DE",
                         confirmed_by_human=True)
    assert "CONDITIONAL ON YOUR CONFIRMED PREMISE" in _tty(result)
    md = to_md(result)
    assert "**CONDITIONAL ON YOUR CONFIRMED PREMISE**" in md
    assert finding.conditional_on.plain_language_premise in md
    payload = json.loads(to_json(result))["findings"][0]
    assert payload["conditional_on"]["contract_id"] == finding.conditional_on.contract_id


def test_autonomous_finding_omits_conditional_marker_everywhere():
    finding = Finding("autonomous", S.MAJOR, "arithmetic only")
    result = AuditResult(findings=[finding], analysis_type="condition_contrast_DE")
    assert "CONDITIONAL ON" not in _tty(result)
    assert "CONDITIONAL ON" not in to_md(result)
    assert "conditional_on" not in json.loads(to_json(result))["findings"][0]


def _tty(result) -> str:
    console = Console(record=True, width=120, color_system=None)
    render_tty(result, console)
    return console.export_text()


def test_minimal_single_claim_render_fixture_is_frozen():
    result = AuditResult(
        analysis_type="marker_detection",
        findings=[
            Finding("first", S.NEEDS_EVIDENCE, "verdict one", coverage=S.NOT_RUN),
            Finding("second", S.PASS, "verdict two"),
        ],
    )

    assert _tty(result) == (
        "PROPOSED  marker_detection (unconfirmed — nothing can block; run sc-referee confirm)\n"
        "\n"
        "▸ Analysis 1\n"
        "  Analysis — marker_detection.\n"
        "\n"
        " NOT CHECKED  (needs_evidence)  first\n"
        "  verdict one\n"
        "\n"
        " CLEAR  (pass)  second\n"
        "  verdict two\n"
        "\n"
        "worst status: needs_evidence   CI: FAIL\n"
        "coverage: 2 findings · 1 clear · 1 not checked\n"
    )
    assert to_md(result) == (
        "# sc-referee report\n"
        "\n"
        "**Proposed analysis type:** `marker_detection` "
        "(unconfirmed — nothing can block until `sc-referee confirm`)\n"
        "\n"
        "## Analysis 1\n"
        "\n"
        "Analysis — marker_detection.\n"
        "\n"
        "### `not_checked` (`needs_evidence`) — first\n"
        "\n"
        "verdict one\n"
        "\n"
        "\n"
        "### `clear` (`pass`) — second\n"
        "\n"
        "verdict two\n"
        "\n"
        "\n"
        "**Worst status:** `needs_evidence` — CI **fails**\n"
        "\n"
        "**Coverage:** 2 findings · 1 clear · 1 not checked\n"
    )
    assert json.loads(to_json(result)) == {
        "analysis_type": "marker_detection",
        "confirmed_by_human": False,
        "worst_status": "needs_evidence",
        "ci_fails": True,
        "ci_conclusion": "fail",
        "fully_audited": True,
        "analyses": [{
            "claim": None,
            "recognition": "Analysis — marker_detection.",
            "findings": [
                {"check_id": "first", "status": "needs_evidence", "human_state": "not_checked",
                 "applicability": "applies", "judgment": None, "coverage": "not_run",
                 "proof_grade": None, "verdict": "verdict one", "metrics": {}, "citations": [],
                 "fix": None},
                {"check_id": "second", "status": "pass", "human_state": "clear",
                 "applicability": "applies", "judgment": None, "coverage": "complete",
                 "proof_grade": None, "verdict": "verdict two", "metrics": {}, "citations": [],
                 "fix": None},
            ],
            "coverage": {"findings": 2, "human_states": {"clear": 1, "not_checked": 1},
                         "statuses": {"needs_evidence": 1, "pass": 1}},
        }],
        "coverage": {"findings": 2, "human_states": {"clear": 1, "not_checked": 1},
                     "statuses": {"needs_evidence": 1, "pass": 1}},
        # The schema-compatible projection remains byte-identical to the grouped finding records.
        "findings": [
            {"check_id": "first", "status": "needs_evidence", "human_state": "not_checked",
             "applicability": "applies", "judgment": None, "coverage": "not_run",
             "proof_grade": None, "verdict": "verdict one", "metrics": {}, "citations": [],
             "fix": None},
            {"check_id": "second", "status": "pass", "human_state": "clear",
             "applicability": "applies", "judgment": None, "coverage": "complete",
             "proof_grade": None, "verdict": "verdict two", "metrics": {}, "citations": [],
             "fix": None},
        ],
    }


def test_single_bound_claim_is_grouped_recognised_and_verdict_identical(tmp_path):
    build(tmp_path)
    result = run_audit(tmp_path, engine="simple")
    original = [(f.check_id, f.status, f.verdict) for f in result.findings]

    payload = json.loads(to_json(result))

    assert len(payload["analyses"]) == 1
    analysis = payload["analyses"][0]
    assert analysis["claim"]["report_path"] == "results/de.csv"
    assert analysis["recognition"] == (
        "Analysis — condition_contrast_DE  (results/de.csv): stim vs ctrl, per sample."
    )
    assert [(f["check_id"], f["status"], f["verdict"]) for f in analysis["findings"]] == original
    assert [(f["check_id"], f["status"], f["verdict"]) for f in payload["findings"]] == original
    assert [(f["check_id"], f["status"], f["human_state"]) for f in analysis["findings"]] == [
        ("confounding", "blocker", "flagged"),
        ("confounding_strong", "not_audited", "not_checked"),
        ("multiple_testing", "needs_evidence", "not_checked"),
        ("count_model", "needs_evidence", "not_checked"),
        ("effect_size_threshold", "pass", "clear"),
        ("pairing", "needs_evidence", "flagged"),
    ]
    assert analysis["coverage"] == {
        "findings": 6,
        "human_states": {"clear": 1, "flagged": 2, "not_checked": 3},
        "statuses": {"blocker": 1, "needs_evidence": 3, "not_audited": 1, "pass": 1},
    }
    assert payload["coverage"] == analysis["coverage"]

    tty = _tty(result)
    assert "▸ Analysis 1 — results/de.csv" in tty
    assert analysis["recognition"] in tty
    assert tty.rstrip().endswith(
        "coverage: 6 findings · 1 clear · 2 flagged · 3 not checked"
    )

    markdown = to_md(result)
    assert "## Analysis 1 — `results/de.csv`" in markdown
    assert analysis["recognition"] in markdown
    assert markdown.rstrip().endswith(
        "**Coverage:** 6 findings · 1 clear · 2 flagged · 3 not checked"
    )

    # An alternate --design file describes the contrast but does not bind ingest's report table.
    # The recognition line must not turn that external declaration into a false claim identity.
    external_design = tmp_path.parent / "external-design.yaml"
    external_design.write_text((tmp_path / "sc-referee.yaml").read_text())
    external = json.loads(to_json(replace(result, design_path=str(external_design))))["analyses"][0]
    assert external["claim"] is None
    assert external["recognition"] == (
        "Analysis — condition_contrast_DE: stim vs ctrl, per sample."
    )


def test_unresolved_recognition_facts_are_omitted_never_fabricated():
    result = AuditResult(
        analysis_type="marker_detection",
        findings=[Finding("coverage", S.NOT_AUDITED, "not checked")],
    )

    analysis = json.loads(to_json(result))["analyses"][0]

    assert analysis["claim"] is None
    assert analysis["recognition"] == "Analysis — marker_detection."
    assert "None" not in _tty(result)
    assert " vs " not in analysis["recognition"]
    assert " per " not in analysis["recognition"]
    assert "(" not in analysis["recognition"]


def test_explicit_unknown_recognition_values_degrade_to_the_resolved_prefix():
    root = {
        "claim_id": "claim:unknown-details",
        "report_artifact_digest": "sha256:report",
        "report_locator_digest": "sha256:locator",
        "producing_value_digest": "sha256:value",
        "report_path": "UNKNOWN",
        "test": "unresolved",
        "reference": "ctrl",
        "unit_of_test": "UNKNOWN",
    }
    result = AuditResult(
        analysis_type="condition_contrast_DE",
        findings=[Finding("count_model", S.NEEDS_EVIDENCE, "still exact",
                          metrics={"claim_root": root})],
    )

    analysis = json.loads(to_json(result))["analyses"][0]

    assert analysis["recognition"] == "Analysis — condition_contrast_DE."
    assert "ctrl" not in analysis["recognition"]  # never render a half-resolved contrast
    assert "UNKNOWN" not in _tty(result)


def test_grouping_generalizes_to_multiple_exact_claim_roots():
    claim_a = {
        "claim_id": "claim:a",
        "report_artifact_digest": "sha256:a",
        "report_locator_digest": "sha256:la",
        "producing_value_digest": "sha256:va",
        "report_path": "results/a.csv",
        "analysis_type": "condition_contrast_DE",
        "test": "stim",
        "reference": "ctrl",
        "unit_of_test": "cell",
    }
    claim_b = {
        "claim_id": "claim:b",
        "report_artifact_digest": "sha256:b",
        "report_locator_digest": "sha256:lb",
        "producing_value_digest": "sha256:vb",
        "report_path": "results/b.csv",
        "analysis_type": "condition_contrast_DE",
        "test": "treated",
        "reference": "untreated",
        "unit_of_test": "sample",
    }
    findings = [
        Finding("confounding", S.PASS, "verdict a1", metrics={"claim_root": claim_a}),
        Finding("multiple_testing", S.NEEDS_EVIDENCE, "verdict b", metrics={"claim_root": claim_b}),
        Finding("pairing", S.INFORMATIONAL, "verdict a2",
                metrics={"claim_root": {**claim_a, "diagnostic_note": "extra metadata"}}),
    ]
    result = AuditResult(findings=findings, analysis_type="condition_contrast_DE")

    payload = json.loads(to_json(result))

    assert [a["claim"]["claim_id"] for a in payload["analyses"]] == ["claim:a", "claim:b"]
    assert [[f["verdict"] for f in a["findings"]] for a in payload["analyses"]] == [
        ["verdict a1", "verdict a2"],
        ["verdict b"],
    ]
    assert [a["recognition"] for a in payload["analyses"]] == [
        "Analysis — condition_contrast_DE  (results/a.csv): stim vs ctrl, per cell.",
        "Analysis — condition_contrast_DE  (results/b.csv): treated vs untreated, per sample.",
    ]
    assert payload["analyses"][0]["coverage"]["statuses"] == {
        "informational": 1,
        "pass": 1,
    }
    assert payload["analyses"][1]["coverage"]["statuses"] == {"needs_evidence": 1}
    assert payload["coverage"] == {
        "findings": 3,
        "human_states": {"clear": 2, "not_checked": 1},
        "statuses": {"needs_evidence": 1, "informational": 1, "pass": 1},
    }

    tty = _tty(result)
    assert tty.index("▸ Analysis 1 — results/a.csv") < tty.index("▸ Analysis 2 — results/b.csv")
    assert tty.count("verdict a1") == tty.count("verdict a2") == tty.count("verdict b") == 1
