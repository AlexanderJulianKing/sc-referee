"""The HTML ledger renderer — a reviewer-facing view over the same AuditResult.

It preserves engine semantics while translating them into actionable browser language, remains
self-contained apart from user-activated citation links, and escapes analysis-supplied text.
"""
from __future__ import annotations

from sc_referee import statuses as S
from sc_referee.audit import AuditResult
from sc_referee.checks.base import Finding
from sc_referee.report import to_html


def test_to_html_translates_engine_states_for_a_reviewer():
    result = AuditResult(
        analysis_type="marker_detection",
        findings=[
            Finding("first", S.NEEDS_EVIDENCE, "verdict one", coverage=S.NOT_RUN),
            Finding("second", S.INFORMATIONAL, "verdict two"),
            Finding("third", S.MAJOR, "verdict three", judgment=S.CONCERN),
        ],
    )
    html = to_html(result)

    # a real page
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "<html" in html and "</html>" in html
    # recognition + the analysis type
    assert "marker_detection" in html
    # Browser language distinguishes evidence needing review from a check that never evaluated.
    assert "NEEDS REVIEW" in html
    assert "CLEAR" in html
    assert "FLAGGED" in html
    # the verdicts
    assert "verdict one" in html and "verdict two" in html and "verdict three" in html
    # the coverage footer
    assert "3 checks" in html and "1 passed" in html and "1 flagged" in html
    assert "1 need review" in html


def test_to_html_escapes_analysis_supplied_text():
    result = AuditResult(
        analysis_type="marker_detection",
        findings=[Finding("x", S.MAJOR, "gene <script>alert(1)</script> & <b>bold</b>")],
    )
    html = to_html(result)
    # the raw markup must not appear as live tags
    assert "<script>alert(1)</script>" not in html
    assert "<b>bold</b>" not in html
    # it must appear escaped instead
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "&amp;" in html


def test_to_html_is_self_contained_no_external_assets():
    result = AuditResult(analysis_type="marker_detection",
                         findings=[Finding("x", S.PASS, "ok")])
    html = to_html(result)
    # no external stylesheet/script/font/image — the page must open offline
    for needle in ("src=", 'link rel="stylesheet"', "@import"):
        assert needle not in html


def test_hero_separates_unresolved_evidence_from_benign_not_checked():
    """The completed report names unresolved evidence without inventing a follow-on form."""
    demand = AuditResult(analysis_type="eqtl", findings=[
        Finding("allele_orientation", S.NEEDS_EVIDENCE, "supply the effect allele", coverage=S.NOT_RUN)])
    dhtml = to_html(demand).lower()
    assert "check needs review" in dhtml
    assert "referee found relevant evidence" in dhtml
    assert "nothing flagged" not in dhtml

    benign = AuditResult(analysis_type="eqtl", findings=[
        Finding("allele_orientation", S.NOT_AUDITED, "couldn't reproduce your estimator")])
    bhtml = to_html(benign).lower()
    assert "nothing flagged" in bhtml
    assert "check needs review" not in bhtml


def test_needs_input_channel_is_visually_tagged():
    """The specific channel demanding input carries its own weight/tag, apart from a benign not-checked."""
    result = AuditResult(analysis_type="eqtl", findings=[
        Finding("allele_orientation", S.NEEDS_EVIDENCE, "supply the effect allele", coverage=S.NOT_RUN)])
    assert "needs-input" in to_html(result)


def test_known_citations_link_to_the_publication():
    result = AuditResult(analysis_type="condition_contrast_DE", findings=[
        Finding("experimental_unit", S.NEEDS_EVIDENCE, "qualified evidence",
                coverage=S.NOT_RUN,
                citations=("Squair et al. 2021, Nat Commun 12:5692",)),
    ])

    rendered = to_html(result)

    assert 'href="https://doi.org/10.1038/s41467-021-25960-2"' in rendered
    assert 'target="_blank"' in rendered
    assert 'rel="noopener noreferrer"' in rendered


def test_conditional_premise_is_an_escaped_distinct_html_panel():
    from sc_referee.checks.base import ConditionalPremise

    marker = ConditionalPremise(
        contract_id="contract-<unsafe>", contract_type="between_group_adjustment_obligation/v1",
        decisive_fields={"between_group_policy": "remove_arbitrary"},
        plain_language_premise="run <script> is exact & bound",
        scope={"group_source_column": "run<unsafe>"},
    )
    result = AuditResult(analysis_type="condition_contrast_DE", findings=[
        Finding("conditional", S.MAJOR, "premise dependent", conditional_on=marker),
    ])
    rendered = to_html(result)
    assert "premise-dependent" in rendered
    assert "CONDITIONAL ON YOUR CONFIRMED PREMISE" in rendered
    assert "<script>" not in rendered
    assert "run &lt;script&gt; is exact &amp; bound" in rendered
    assert "contract-&lt;unsafe&gt;" in rendered
    assert "run&lt;unsafe&gt;" in rendered
