"""The report header must not claim a design is 'human-ratified' before it has been confirmed.

The audit runs (and downgrades earned blockers to needs_evidence) whether or not the design is
confirmed. The header printed `CONFIRMED … (human-ratified)` unconditionally — contradicting the
body, which correctly says 'not human-confirmed'. The header must reflect the real confirm state.
"""
from rich.console import Console

from sc_referee import statuses as S
from sc_referee.audit import AuditResult
from sc_referee.checks.base import Finding
from sc_referee.report import render_tty, to_md

_F = [Finding("confounding", S.NEEDS_EVIDENCE, "aliasing detected, but not human-confirmed")]


def _tty(confirmed):
    con = Console(record=True, width=100)
    render_tty(AuditResult(findings=_F, analysis_type="condition_contrast_DE",
                           confirmed_by_human=confirmed), con)
    return con.export_text()


def test_unconfirmed_header_does_not_claim_human_ratified():
    out = _tty(confirmed=False)
    assert "human-ratified" not in out
    assert "confirm" in out.lower()                 # tells the user what to do


def test_confirmed_header_says_human_ratified():
    assert "human-ratified" in _tty(confirmed=True)


def test_markdown_header_reflects_confirm_state():
    unconfirmed = to_md(AuditResult(findings=_F, analysis_type="condition_contrast_DE",
                                    confirmed_by_human=False))
    confirmed = to_md(AuditResult(findings=_F, analysis_type="condition_contrast_DE",
                                  confirmed_by_human=True))
    assert "human-ratified" not in unconfirmed
    assert "human-ratified" in confirmed
