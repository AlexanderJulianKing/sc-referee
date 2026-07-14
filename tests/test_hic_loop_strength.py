"""Hi-C loop-strength contract: specificity before accusation."""
import pytest

from sc_referee import statuses as S
from tests.factories import hic_contact_bundle, make_hic_design


def _alternative_delta(bundle, design, *, include_target=False, ignore_masks=False, pool=False):
    import numpy as np

    bins = bundle.hic.bins.set_index("bin_id")
    target = frozenset((design.hic_target_bin_i, design.hic_target_bin_j))
    rows = []
    for (_, condition), sample in bundle.hic.contacts.groupby(
            ["replicate", "condition"], observed=True, sort=False):
        target_count = None
        background = []
        for row in sample.itertuples(index=False):
            pair = frozenset((row.bin_i, row.bin_j))
            if pair == target:
                target_count = float(row.observed_count)
                if include_target:
                    background.append(float(row.observed_count))
                continue
            if (not ignore_masks
                    and (bool(bins.loc[row.bin_i, "masked"])
                         or bool(bins.loc[row.bin_j, "masked"]))):
                continue
            background.append(float(row.observed_count))
        expected = float(np.mean(background))
        rows.append((condition, target_count, expected, float(np.log2(target_count / expected))))
    means = {}
    for condition in (design.reference, design.test):
        selected = [row for row in rows if row[0] == condition]
        if pool:
            means[condition] = float(np.log2(
                sum(row[1] for row in selected) / sum(row[2] for row in selected)))
        else:
            means[condition] = float(np.mean([row[3] for row in selected]))
    return means[design.test] - means[design.reference]


@pytest.mark.parametrize(
    "seed,n_replicates,effect,distance_bins",
    [(0, 2, 1, 3), (7, 3, 2, 5), (19, 4, -1, 7)],
)
def test_correct_supported_specification_passes(seed, n_replicates, effect, distance_bins):
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    reference = tuple([1] * n_replicates)
    test = tuple([1 + effect] * n_replicates)
    bundle = hic_contact_bundle(
        reference_strengths=reference, test_strengths=test,
        distance_bins=distance_bins, seed=seed)
    design = make_hic_design(hic_target_bin_j=f"b{20 + distance_bins}")
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)

    assert finding.status == S.PASS
    assert abs(finding.metrics["reported_delta"] - finding.metrics["recomputed_delta"]) <= 1e-6
    assert finding.metrics["within_tolerance"] is True


def test_correct_rounded_report_passes_inside_ratified_tolerance():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(report_delta=1.01, seed=3)
    design = make_hic_design(hic_report_delta_tolerance=0.02)
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)

    assert finding.status == S.PASS
    assert finding.metrics["absolute_error"] > 0
    assert finding.metrics["within_tolerance"] is True


def test_unbounded_tolerance_without_rounding_authority_is_not_checked():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(report_delta=-100.0, seed=3)
    design = make_hic_design(
        hic_report_delta_tolerance=1000.0,
        hic_report_delta_tolerance_authority=None,
    )
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_reversing_the_unordered_report_pair_is_still_the_same_target():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(reverse_report_pair=True, seed=5)
    finding = evaluate_hic_loop_strength(make_hic_design(), bundle, bundle.reported_results)

    assert finding.status == S.PASS


@pytest.mark.parametrize(
    "field,value",
    [
        ("hic_contact_scale", "ice_balanced"),
        ("hic_expected_model", "cis_exact_distance_median_v1"),
        ("hic_expected_model", "smoothed_ps_v1"),
        ("hic_expected_model", "cis_exact_distance_mean_target_included_v1"),
        ("hic_mask_policy", "pair_level_blacklist_v1"),
        ("hic_zero_policy", "sparse_nonzero_only"),
        ("hic_pseudocount", 1.0),
        ("hic_target_statistic", "local_donut"),
        ("hic_target_statistic", "central_3x3"),
        ("hic_replicate_functional", "pooled_before_log_v1"),
    ],
)
def test_correct_but_different_estimator_is_not_audited_never_forced_through(field, value):
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(seed=11)
    design = make_hic_design(**{field: value})
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)

    assert finding.status == S.NOT_AUDITED
    assert "not the supported" in finding.verdict.lower()
    assert finding.status != S.BLOCKER


@pytest.mark.parametrize(
    "overrides",
    [
        {"model": "~ condition + batch", "batch": ("batch",)},
        {"pairing_unit": ("subject",)},
        {"subset": {"cell_type": "T"}},
    ],
)
def test_correct_but_different_analysis_structure_is_not_audited(overrides):
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(seed=13)
    finding = evaluate_hic_loop_strength(
        make_hic_design(**overrides), bundle, bundle.reported_results)

    assert finding.status == S.NOT_AUDITED
    assert finding.metrics["unsupported_analysis_structure"]
    assert finding.status != S.BLOCKER


def test_check_is_blocker_entitled_but_still_self_gates():
    from sc_referee.checks.hic_loop_strength import HiCLoopStrengthCheck

    assert HiCLoopStrengthCheck.max_status == S.BLOCKER
    assert not hasattr(HiCLoopStrengthCheck(), "cannot_evaluate")


def test_missing_hic_payload_returns_rich_not_audited_from_run():
    from sc_referee.bundle import HiCBundle, HiCContactData
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = HiCBundle(hic=HiCContactData(contacts=None, bins=None))
    finding = evaluate_hic_loop_strength(make_hic_design(), bundle, None)

    assert finding.status == S.NOT_AUDITED
    assert finding.metrics["recompute_reason"] == "contacts_or_bins_missing"


def test_missing_tolerance_is_unresolved_contract_not_a_magnitude_verdict():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(seed=43)
    finding = evaluate_hic_loop_strength(
        make_hic_design(hic_report_delta_tolerance=None), bundle, bundle.reported_results)

    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"
    assert "hic_report_delta_tolerance" in finding.metrics["unresolved_contract"]


def test_empty_replicate_key_is_unresolved_contract_not_a_recompute_failure():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(seed=45)
    finding = evaluate_hic_loop_strength(
        make_hic_design(replicate_unit=()), bundle, bundle.reported_results)

    assert finding.status == S.NEEDS_EVIDENCE
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"
    assert "replicate_unit" in finding.metrics["unresolved_contract"]


@pytest.mark.parametrize("confirmed,confidence", [(False, True), (True, False)])
def test_diagnostic_agreement_without_entitlement_is_not_checked(confirmed, confidence):
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(seed=47)
    design = make_hic_design(
        confirmed=confirmed, hic_loop_strength_confidence_high=confidence)
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)

    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )
    assert finding.metrics["within_tolerance"] is True


def test_incomplete_contact_universe_is_not_audited_with_metrics():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(seed=53)
    bundle.hic.contacts = bundle.hic.contacts.iloc[1:].copy()
    finding = evaluate_hic_loop_strength(make_hic_design(), bundle, bundle.reported_results)

    assert finding.status == S.NOT_AUDITED
    assert finding.metrics["recompute_reason"] == "dense_zero_inclusive_distance_stratum_incomplete"
    assert finding.metrics["background_pairs"] >= 50


def test_too_few_background_pairs_is_not_audited():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(n_bins=54, masked_indices=(), seed=59)
    design = make_hic_design(hic_background_view_end=540_000)
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)

    assert finding.status == S.NOT_AUDITED
    assert finding.metrics["background_pairs"] < 50


@pytest.mark.parametrize("kind", ["missing", "duplicate", "nonfinite", "wrong_resolution"])
def test_unusable_report_binding_is_not_audited(kind):
    import pandas as pd
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(seed=61)
    if kind == "missing":
        bundle.reported_results = None
    elif kind == "duplicate":
        bundle.reported_results = pd.concat(
            [bundle.reported_results, bundle.reported_results], ignore_index=True)
    elif kind == "nonfinite":
        bundle.reported_results.loc[0, "delta"] = float("nan")
    else:
        bundle.reported_results.loc[0, "resolution_bp"] = 5_000
    finding = evaluate_hic_loop_strength(make_hic_design(), bundle, bundle.reported_results)

    assert finding.status == S.NOT_AUDITED
    assert finding.metrics.get("report_binding_reason")
    assert finding.metrics["recomputed_delta"] == pytest.approx(1.0)


def test_masked_target_is_not_audited():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(seed=67)
    bundle.hic.bins.loc[bundle.hic.bins["bin_id"] == "b20", "masked"] = True
    finding = evaluate_hic_loop_strength(make_hic_design(), bundle, bundle.reported_results)

    assert finding.status == S.NOT_AUDITED
    assert finding.metrics["recompute_reason"] == "target_bin_is_masked"


def test_target_in_expected_background_is_proved_nonconformant():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    design = make_hic_design()
    bundle = hic_contact_bundle(seed=71)
    bundle.reported_results.loc[0, "delta"] = _alternative_delta(
        bundle, design, include_target=True)
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)

    assert finding.status == S.BLOCKER
    assert finding.metrics["absolute_error"] > finding.metrics["report_delta_tolerance"]
    assert "does not conform" in finding.verdict.lower()
    assert "target included" not in finding.verdict.lower()


def test_ignoring_ratified_masks_is_proved_nonconformant_without_cause_claim():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    design = make_hic_design()
    bundle = hic_contact_bundle(seed=73)
    masked_ids = set(bundle.hic.bins.loc[bundle.hic.bins["masked"], "bin_id"])
    touches_mask = bundle.hic.contacts["bin_i"].isin(masked_ids) | bundle.hic.contacts["bin_j"].isin(masked_ids)
    bundle.hic.contacts.loc[touches_mask & (bundle.hic.contacts["condition"] == "stim"),
                            "observed_count"] = 512
    bundle.reported_results.loc[0, "delta"] = _alternative_delta(
        bundle, design, ignore_masks=True)
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)

    assert finding.status == S.BLOCKER
    assert finding.metrics["within_tolerance"] is False
    assert "mask" not in finding.verdict.lower()


def test_pooling_before_log_violates_the_ratified_equal_weight_functional():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    design = make_hic_design()
    bundle = hic_contact_bundle(
        reference_strengths=(0, 2), test_strengths=(1, 1),
        background_counts=(64, 4, 16, 16), seed=79)
    bundle.reported_results.loc[0, "delta"] = _alternative_delta(bundle, design, pool=True)
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)

    assert finding.status == S.BLOCKER
    assert finding.metrics["recomputed_delta"] == pytest.approx(0.0)
    assert finding.metrics["absolute_error"] > finding.metrics["report_delta_tolerance"]


@pytest.mark.parametrize("reported_delta", [-1.0, 2.0, -0.5])
def test_reported_delta_outside_tolerance_is_a_contract_violation(reported_delta):
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(report_delta=reported_delta, seed=83)
    finding = evaluate_hic_loop_strength(make_hic_design(), bundle, bundle.reported_results)

    assert finding.status == S.BLOCKER
    assert finding.judgment == S.VIOLATION
    assert finding.metrics["within_tolerance"] is False
    assert finding.metrics["reported_delta"] == reported_delta


def test_disagreement_without_blocker_entitlement_stays_needs_evidence():
    from sc_referee.checks.hic_loop_strength import evaluate_hic_loop_strength

    bundle = hic_contact_bundle(report_delta=-1.0, seed=89)
    design = make_hic_design(hic_loop_strength_confidence_high=False)
    finding = evaluate_hic_loop_strength(design, bundle, bundle.reported_results)

    assert finding.status == S.NEEDS_EVIDENCE
    assert (finding.coverage, S.human_state(finding)) == (S.NOT_RUN, S.NOT_CHECKED)
    assert finding.metrics["sign_relation"] == "opposite"
