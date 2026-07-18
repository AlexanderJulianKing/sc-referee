"""eQTL donor/genotype support: a certifying check that can never accuse.

It answers one narrow structural question — does this design actually have donor-level support
across genotype classes, so a donor-level genotype coefficient is estimable? It deliberately says
nothing about the reported effect's direction or magnitude, and it is entitled to at most
`not_audited`, so the worst it can do is decline to certify.
"""
from __future__ import annotations

from sc_referee import statuses as S
from sc_referee.checks.eqtl_design_support import EqtlDesignSupportCheck
from tests.factories import eqtl_count_bundle, make_eqtl_design


def test_donor_level_support_across_classes_earns_a_recomputed_pass():
    bundle = eqtl_count_bundle(class_counts=(4, 4, 4), seed=5)
    design = make_eqtl_design()

    check = EqtlDesignSupportCheck()
    assert check.applies_to(design, bundle) is True
    finding = check.run(design, bundle)

    assert finding.status == S.PASS
    assert finding.proof_grade == S.RECOMPUTED
    assert finding.coverage == S.COMPLETE
    assert finding.metrics["n_donors"] == 12
    assert finding.metrics["genotype_class_counts"] == {0: 4, 1: 4, 2: 4}
    # It certifies structure only, and says so rather than implying the effect was validated.
    assert "does not validate the reported effect" in finding.verdict


def test_too_few_donors_per_class_abstains_and_never_accuses():
    """One populated genotype class cannot support a dose coefficient. The honest answer is
    `not_audited` — declining to certify — not an accusation about the analysis."""
    bundle = eqtl_count_bundle(class_counts=(12, 1, 0), seed=5)
    design = make_eqtl_design()

    finding = EqtlDesignSupportCheck().run(design, bundle)

    assert finding.status == S.NOT_AUDITED
    assert finding.coverage == S.NOT_RUN
    assert finding.judgment == S.UNRESOLVED
    assert finding.status not in (S.BLOCKER, S.MAJOR)


def test_entitlement_caps_the_check_below_any_accusation():
    """The structural guarantee, independent of the branch taken: the spine clamps a verifier to
    its declared `max_status`, and this one may never reach `major` or `blocker`."""
    assert EqtlDesignSupportCheck.max_status == S.NOT_AUDITED
    assert EqtlDesignSupportCheck.analysis_types == ("eqtl",)


def test_does_not_apply_to_a_non_eqtl_analysis():
    bundle = eqtl_count_bundle(seed=5)
    assert EqtlDesignSupportCheck().applies_to(
        make_eqtl_design(analysis_type="condition_contrast_DE"), bundle
    ) is False


def test_registered_in_the_default_checklist():
    from sc_referee.registry import build_checks

    ids = {getattr(c, "id", None) for c in build_checks()}
    assert "eqtl_design_support" in ids
