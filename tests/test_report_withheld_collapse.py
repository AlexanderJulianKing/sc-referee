"""Presentation of the underpower-after-collapse case.

When experimental_unit OBSERVES a blocker-sized collapse but WITHHOLDS the hard block because the
corrected sample-level analysis is underpowered (the Biermann-2022 shape), the report must lead with
the observed discrepancy and state the qualification SEPARATELY — instead of leading with the caveat
and burying the collapse. This is presentation only: the machine-readable status stays needs_evidence
and no threshold changes.
"""
from __future__ import annotations

import json
from io import StringIO

from rich.console import Console

from sc_referee import statuses as S
from sc_referee.audit import AuditResult
from sc_referee.checks.base import Finding
from sc_referee.report import _withheld_collapse, render_tty, to_html, to_json, to_md

# The audited Biermann et al. 2022 metrics (patient-level PyDESeq2 recompute of a cell-as-replicate DE).
_BIERMANN = dict(valid_reported_sig=16289, survivors=770, survival_rate=0.0473, powered=False,
                 comparable=True, covariates_constant=True, replicate_recorded=True,
                 n_replicates_per_arm=16, effect_corr=0.419, sign_flips=2342)


def _finding(verdict="the sample-level re-test is underpowered — treat these as exploratory", **over):
    return Finding("experimental_unit", S.NEEDS_EVIDENCE, verdict,
                   metrics=dict(_BIERMANN, **over), coverage=S.NOT_RUN)


def _result(f):
    return AuditResult(findings=[f], analysis_type="condition_contrast_DE", confirmed_by_human=True)


def test_helper_returns_the_three_separated_pieces():
    d = _withheld_collapse(_finding())
    assert d["headline"] == ("Critical discrepancy: 95.3% of reported discoveries lost "
                             "significance when recomputed at the sample level.")
    assert d["counts"] == ("16,289 discoveries were reported as significant; "
                            "770 remained significant at the sample level.")
    assert "Why this is not definitive" in d["qualification"] and "limited" in d["qualification"]


def test_markdown_leads_with_strength_before_qualification():
    md = to_md(_result(_finding()))
    assert "Critical discrepancy: 95.3%" in md
    assert "16,289 discoveries were reported as significant" in md
    assert md.index("Critical discrepancy") < md.index("Why this is not definitive")


def test_html_shows_strength_and_qualification_as_separate_elements():
    h = to_html(_result(_finding()))
    assert 'class="disc-headline"' in h and "Critical discrepancy: 95.3%" in h
    assert 'class="disc-counts"' in h and "16,289 discoveries were reported as significant" in h
    assert 'class="disc-qual"' in h and "Why this is not definitive" in h
    assert "95.3% lost significance after correcting the experimental unit" in h
    assert h.index("95.3% lost significance") < h.index("Critical discrepancy: 95.3%")


def test_tty_shows_the_headline():
    console = Console(file=StringIO(), width=120, force_terminal=False)
    render_tty(_result(_finding()), console=console)
    out = console.file.getvalue()
    assert "Critical discrepancy: 95.3%" in out and "16,289 discoveries" in out


def test_machine_status_and_metrics_are_unchanged():
    fj = json.loads(to_json(_result(_finding())))["findings"][0]
    assert fj["status"] == S.NEEDS_EVIDENCE                 # adjudication untouched
    assert fj["metrics"]["survival_rate"] == 0.0473         # the observed collapse persists in the data
    assert fj["metrics"]["powered"] is False


def test_few_replicates_needs_evidence_is_not_reframed():
    md = to_md(_result(_finding(verdict="too few independent samples to re-test reliably",
                                n_replicates_per_arm=2)))
    assert "Critical discrepancy" not in md
    assert "too few independent samples" in md              # the original caveat still leads


def test_major_sized_partial_collapse_is_not_reframed():
    # survival 0.3 is above BLOCKER_AT (0.10): partly survives, not a blocker-sized collapse.
    assert _withheld_collapse(_finding(survival_rate=0.3)) is None


def test_powered_finding_is_not_reframed():
    # if the recompute WAS powered it would be a real blocker, not this withheld-presentation case.
    assert _withheld_collapse(_finding(powered=True)) is None
