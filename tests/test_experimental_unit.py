"""build_panel + the experimental_unit check.

The panel math is tested directly on constructed recompute/reported pairs (exact control
over survival/powered/comparability); the check wiring is tested end-to-end on a paired
count bundle to prove a VALID analysis is not false-accused.
"""
import numpy as np
import pandas as pd

from sc_referee import statuses as S
from sc_referee.bundle import Bundle, Measure
from sc_referee.checks.experimental_unit import ExperimentalUnitCheck, evaluate_experimental_unit
from sc_referee.design import ReportInferenceContract
from sc_referee.engine import RecomputeResult, build_panel, earned_verdict
from tests.factories import make_design, paired_count_bundle


def _panel_bundle(n_donors=8):
    rows = [(f"D{d}", c) for d in range(n_donors) for c in ("ctrl", "stim")]
    obs = pd.DataFrame(rows, columns=["donor_id", "condition"],
                       index=[f"s{i}" for i in range(len(rows))])
    counts = np.ones((len(rows), 2), dtype="int64")
    return Bundle(observations=obs, measure=Measure("counts", counts, None, ["a", "b"]),
                  feature_metadata=pd.DataFrame(index=["a", "b"]), replicate_var="donor_id")


def _res(feats, padj_rc, effect_rc, s_diff=0.3, n=8, testable=None):
    testable = [True] * len(feats) if testable is None else testable
    table = pd.DataFrame(
        {"pvalue": padj_rc, "padj": padj_rc, "effect": effect_rc, "se": [0.1] * len(feats),
         "s_diff": [s_diff] * len(feats), "n_used": n, "testable": testable},
        index=feats,
    )
    return RecomputeResult(table=table, mde_kind="paired", n_replicates_per_arm=n)


def _reported(feats, n_sig):
    return pd.DataFrame({
        "feature_id": feats,
        "pvalue": [1e-4] * n_sig + [0.5] * (len(feats) - n_sig),
        "padj": [1e-3] * n_sig + [0.5] * (len(feats) - n_sig),
        "effect": [2.0] * n_sig + [0.1] * (len(feats) - n_sig),
    })


DESIGN = make_design(sample_unit=("donor_id", "condition"))


def _inference_contract(dependence_semantics):
    return ReportInferenceContract(
        producer_binding="exact", response_scale="raw_counts", method_family="gaussian",
        dependence_semantics=dependence_semantics,
    )


def test_build_panel_collapse_is_earned_blocker():
    feats = [f"g{i}" for i in range(20)]
    reported = _reported(feats, n_sig=10)
    # only g0 survives among the 10 claimed discoveries; the rest collapse
    padj_rc = [1e-3] + [1.0] * 9 + [1.0] * 10
    res = _res(feats, padj_rc, [1.9] * 10 + [0.1] * 10, s_diff=0.3, n=8)
    panel = build_panel(reported, res, DESIGN, _panel_bundle(), alpha=0.05)

    assert panel.valid_reported_sig == 10
    assert panel.survivors == 1
    assert abs(panel.survival_rate - 0.1) < 1e-9
    assert panel.powered is True and panel.comparable is True
    assert earned_verdict(panel)[0] == S.BLOCKER


def test_build_panel_clean_analysis_passes():
    feats = [f"g{i}" for i in range(20)]
    reported = _reported(feats, n_sig=10)
    res = _res(feats, [1e-3] * 10 + [1.0] * 10, [1.9] * 10 + [0.1] * 10, s_diff=0.3, n=8)
    panel = build_panel(reported, res, DESIGN, _panel_bundle(), alpha=0.05)

    assert panel.survival_rate == 1.0
    status, voice = earned_verdict(panel)
    assert status == S.PASS
    assert "survive" in voice.lower()
    assert "already works" not in voice.lower()


def test_build_panel_significant_only_table_is_not_comparable():
    feats = [f"g{i}" for i in range(10)]
    reported = _reported(feats, n_sig=10)  # ALL rows significant -> can't rebuild FDR family
    res = _res(feats, [1.0] * 10, [1.9] * 10, s_diff=0.3, n=8)
    panel = build_panel(reported, res, DESIGN, _panel_bundle(), alpha=0.05)

    assert panel.comparable is False
    assert earned_verdict(panel)[0] == S.NEEDS_EVIDENCE


def test_build_panel_underpowered_collapse_abstains():
    """Total collapse but a huge per-pair SD (underpowered) -> needs_evidence, not blocker."""
    feats = [f"g{i}" for i in range(20)]
    reported = _reported(feats, n_sig=10)
    res = _res(feats, [1.0] * 20, [1.9] * 10 + [0.1] * 10, s_diff=5.0, n=4)  # huge SD -> MDE >> ref
    panel = build_panel(reported, res, DESIGN, _panel_bundle(), alpha=0.05)

    assert panel.powered is False
    assert earned_verdict(panel)[0] == S.NEEDS_EVIDENCE


def test_dependence_aware_cell_level_model_abstains_even_when_sensitivity_collapses():
    feats = [f"g{i}" for i in range(20)]
    reported = _reported(feats, n_sig=10)
    collapse = _res(feats, [1e-3] + [1.0] * 19, [1.9] * 10 + [0.1] * 10, s_diff=0.3, n=8)
    design = make_design(
        sample_unit=("donor_id", "condition"),
        report_inference_contract=_inference_contract("mixed_model"),
    )
    finding = evaluate_experimental_unit(
        design, _panel_bundle(), reported, engine="simple", recompute=collapse,
    )
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )
    assert "mixed_model" in finding.verdict


def test_bound_iid_cell_producer_retains_adverse_result():
    feats = [f"g{i}" for i in range(20)]
    reported = _reported(feats, n_sig=10)
    collapse = _res(feats, [1e-3] + [1.0] * 19, [1.9] * 10 + [0.1] * 10, s_diff=0.3, n=8)
    design = make_design(
        sample_unit=("donor_id", "condition"),
        report_inference_contract=_inference_contract("iid_rows"),
    )
    finding = evaluate_experimental_unit(
        design, _panel_bundle(), reported, engine="pydeseq2", recompute=collapse,
    )
    assert finding.status == S.BLOCKER
    assert finding.judgment == S.VIOLATION


def test_experimental_unit_valid_analysis_not_false_accused():
    bundle = paired_count_bundle(n_donors=8)
    genes = list(bundle.measure.feature_index)
    reported = pd.DataFrame({
        "feature_id": genes,
        "pvalue": [1e-8 if g == "G_up" else 0.5 for g in genes],
        "padj": [1e-6 if g == "G_up" else 0.6 for g in genes],
        "effect": [2.0 if g == "G_up" else 0.0 for g in genes],
    })
    design = make_design(sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",))
    finding = evaluate_experimental_unit(design, bundle, reported, engine="simple")
    # G_up is a real donor-level effect -> the claim survives -> never a blocker/major
    assert finding.status in (S.PASS, S.NEEDS_EVIDENCE)
    if finding.status == S.NEEDS_EVIDENCE:
        assert (finding.coverage, S.human_state(finding)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_uncorrected_p_values_are_not_blamed_on_pseudoreplication():
    """The misdiagnosis fix. A per-cell analysis that ALSO forgot BH must not be told its
    claims 'do not survive replicate-aware inference' — its p-values were never an FDR family.
    `multiple_testing` owns that diagnosis; experimental_unit must abstain."""
    feats = [f"g{i}" for i in range(20)]
    reported = _reported(feats, n_sig=10)
    reported["padj"] = reported["pvalue"]              # never corrected
    res = _res(feats, [1.0] * 20, [1.9] * 10 + [0.1] * 10, s_diff=0.3, n=8)

    panel = build_panel(reported, res, DESIGN, _panel_bundle(), alpha=0.05)
    assert panel.comparable is False
    status, reason = earned_verdict(panel)
    assert status == S.NEEDS_EVIDENCE
    assert "uncorrected" in reason.lower()


def test_experimental_unit_no_reported_is_needs_evidence():
    bundle = paired_count_bundle(n_donors=4)
    design = make_design(sample_unit=("donor_id", "condition"))
    finding = evaluate_experimental_unit(design, bundle, None, engine="simple")
    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"


def test_applies_to_requires_a_recorded_replicate():
    """Fires iff the CONFIRMED design names a replicate present in .obs. The design is authoritative,
    not the adapter's name-detection (`bundle.replicate_var`), so a named-and-present replicate runs
    even when the adapter missed it. (Coupling fix, 2026-07-08.)"""
    bundle = paired_count_bundle(n_donors=4)
    check = ExperimentalUnitCheck(engine="simple")
    assert check.applies_to(make_design(), bundle) is True             # design names donor_id, it is in .obs
    bundle.replicate_var = None                                        # adapter hint gone...
    assert check.applies_to(make_design(), bundle) is True             # ...but the design still names it -> runs
    assert check.applies_to(make_design(replicate_unit=()), bundle) is False            # no replicate named
    assert check.applies_to(make_design(replicate_unit=("missing",)), bundle) is False  # named but absent


def test_applies_to_requires_a_cell_level_reported_analysis():
    """C7: unit_of_test gates the check. A already-sample-level report has no
    pseudoreplication to correct, so the check does not fire at all."""
    bundle = paired_count_bundle(n_donors=4)
    check = ExperimentalUnitCheck(engine="simple")
    assert check.applies_to(make_design(unit_of_test="cell"), bundle) is True
    assert check.applies_to(make_design(unit_of_test="sample"), bundle) is False


def test_contrast_varying_within_the_sample_unit_abstains():
    """sample_unit=[donor] on a PAIRED design merges ctrl+stim into one pseudobulk sample and
    labels it arbitrarily. Abstain rather than recompute nonsense. (adversarial review 2026-07-08.)"""
    bundle = paired_count_bundle(n_donors=4)          # each donor has BOTH conditions
    design = make_design(sample_unit=("donor_id",))   # ...but we aggregate by donor only
    genes = list(bundle.measure.feature_index)
    reported = pd.DataFrame({"feature_id": genes, "pvalue": [1e-6] * len(genes),
                             "padj": [1e-4] * len(genes), "effect": [2.0] * len(genes)})
    f = evaluate_experimental_unit(design, bundle, reported, engine="simple")
    assert f.status == S.NEEDS_EVIDENCE
    assert f.coverage == S.NOT_RUN
    assert S.human_state(f) == "not_checked"
    assert "varies within the sample unit" in f.verdict


def test_covariate_varying_within_sample_unit_is_not_checked_for_this_recompute():
    bundle = paired_count_bundle(n_donors=4)
    bundle.observations["batch"] = ["a", "b"] * (len(bundle.observations) // 2)
    design = make_design(
        sample_unit=("donor_id", "condition"),
        batch=("batch",),
        model="~ batch + condition",
    )
    finding = evaluate_experimental_unit(design, bundle, _reported(
        list(bundle.measure.feature_index), n_sig=1), engine="simple")

    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"
