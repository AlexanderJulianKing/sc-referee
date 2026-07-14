"""The earned-verdict rule (PINNED) — what makes a blocker *deserved*.

A blocker requires the recompute to be adequately powered, so "underpowered" is never
mistaken for "refuted". These constructed panels pin each branch and boundary of the rule.
"""
from sc_referee import statuses as S
from sc_referee.engine import Panel, earned_verdict


def base_panel(**kw):
    d = dict(
        comparable=True,
        comparable_reason="",
        valid_reported_sig=100,
        covariates_constant=True,
        replicate_recorded=True,
        n_biological_replicates_per_arm=8,
        powered=True,
        survival_rate=1.0,
    )
    d.update(kw)
    return Panel(**d)


def test_not_comparable_needs_evidence():
    status, msg = earned_verdict(base_panel(comparable=False, comparable_reason="id match too low"))
    assert status == S.NEEDS_EVIDENCE
    assert "id match too low" in msg


def test_no_valid_reported_sig_needs_evidence():
    status, _ = earned_verdict(base_panel(valid_reported_sig=0))
    assert status == S.NEEDS_EVIDENCE


def test_covariate_varies_needs_evidence():
    status, _ = earned_verdict(base_panel(covariates_constant=False))
    assert status == S.NEEDS_EVIDENCE


def test_replicate_not_recorded_needs_evidence():
    status, _ = earned_verdict(base_panel(replicate_recorded=False))
    assert status == S.NEEDS_EVIDENCE


def test_too_few_replicates_needs_evidence():
    status, _ = earned_verdict(base_panel(n_biological_replicates_per_arm=2))
    assert status == S.NEEDS_EVIDENCE


def test_underpowered_beats_collapse():
    """The load-bearing property: total collapse but underpowered -> needs_evidence, NOT blocker."""
    status, _ = earned_verdict(base_panel(powered=False, survival_rate=0.0))
    assert status == S.NEEDS_EVIDENCE


def test_powered_collapse_is_blocker():
    status, msg = earned_verdict(base_panel(survival_rate=0.02))
    assert status == S.BLOCKER
    assert "do not survive" in msg


def test_partial_survival_is_major():
    status, _ = earned_verdict(base_panel(survival_rate=0.40))
    assert status == S.MAJOR


def test_boundary_survival_at_010_is_blocker():
    status, _ = earned_verdict(base_panel(survival_rate=0.10))
    assert status == S.BLOCKER  # rule is survival_rate <= 0.10


def test_boundary_survival_at_060_is_pass():
    status, _ = earned_verdict(base_panel(survival_rate=0.60))
    assert status == S.PASS  # rule is survival_rate < 0.60 for major


def test_high_survival_is_pass():
    status, _ = earned_verdict(base_panel(survival_rate=0.95))
    assert status == S.PASS
