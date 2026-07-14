"""pairing (spine step 4, increment 1): pair-matching structure over obs. adversarial boundary consult ruled
none of the arithmetic patterns is a sound BLOCKER with current inputs, so this increment is diagnostic:

  - OMITTED PAIRING (needs_evidence): the model is unpaired (pairing_unit empty) but the data is
    paired-capable — the replicate key spans both contrast arms. The genuinely new catch; nothing else
    sees it (confounding stays silent because an unpaired model is full-rank).
  - PARTIAL MATCHING (informational): a paired design where some replicate levels appear in only one arm
    — a reported fact, not a defect (a paired method just drops them).
  - genuinely UNPAIRED data (pass) and a well-formed PAIRED design (pass) are not flagged.

Zero complete pairs in a PAIRED model is deliberately NOT re-handled here — confounding already blocks on
the rank deficiency (adversarial review: it "belongs to the existing confounding check").
"""
import numpy as np
import pandas as pd
from dataclasses import replace

from sc_referee import statuses as S
from sc_referee.bundle import Bundle, Measure
from tests.factories import make_design, paired_crossed_obs, unpaired_crossed_obs


def _bundle(obs):
    genes = ["g1", "g2"]
    return Bundle(observations=obs, measure=Measure("counts", np.ones((len(obs), 2), dtype="int64"),
                                                    None, genes),
                  feature_metadata=pd.DataFrame(index=genes), replicate_var="donor_id")


def _unpaired_design():
    return make_design(unit_of_test="sample", pairing_unit=[])


def _paired_design():
    return make_design(unit_of_test="sample", pairing_unit=["donor_id"])


def test_design_factory_preserves_an_explicit_unpaired_declaration():
    assert make_design(pairing_unit=[]).pairing_unit == []


def test_missing_pairing_and_replicate_key_is_not_checked():
    from sc_referee.checks.pairing import PairingCheck

    design = make_design(replicate_unit=(), pairing_unit=None)
    finding = PairingCheck().run(design, _bundle(unpaired_crossed_obs()))
    assert (finding.status, finding.coverage, S.human_state(finding)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_omitted_pairing_on_paired_capable_data_is_needs_evidence():
    from sc_referee.checks.pairing import PairingCheck
    # unpaired model, but each donor has both ctrl and stim (paired-capable)
    f = PairingCheck().run(_unpaired_design(), _bundle(paired_crossed_obs()))
    assert f.status == "needs_evidence" and "paired" in f.verdict.lower()
    assert (f.judgment, f.coverage, S.human_state(f)) == (S.CONCERN, S.COMPLETE, S.FLAGGED)


def test_genuinely_unpaired_data_is_not_flagged():
    from sc_referee.checks.pairing import PairingCheck
    # unpaired model, donors are distinct per arm (D1-D4 ctrl, D5-D8 stim) -> no pairing to omit
    f = PairingCheck().run(_unpaired_design(), _bundle(unpaired_crossed_obs()))
    assert f.status == "pass"


def test_clean_muscat_benchmark_is_declared_unpaired_and_passes_pairing():
    from bench.analyses import bench_design, bundle_from
    from bench.muscat_sim import simulate
    from sc_referee.checks.pairing import PairingCheck

    design = bench_design()
    bundle = bundle_from(simulate(n_donors=2, n_genes=5, cells_per_donor=2, seed=0))

    assert design.pairing_unit == []
    finding = PairingCheck().run(design, bundle)
    assert finding.status == "pass"
    assert finding.metrics["complete_pairs"] == 0


def test_distinct_levels_that_stringify_identically_do_not_fabricate_pairs():
    from sc_referee.checks.pairing import PairingCheck

    obs = pd.DataFrame({
        "donor_id": ["D1", "D2", "D3", "D4"],
        "condition": pd.Series([1, 1, "1", "1"], dtype=object),
    })
    design = replace(_unpaired_design(), reference=1, test="1")

    finding = PairingCheck().run(design, _bundle(obs))

    assert finding.status == "pass"
    assert finding.metrics["complete_pairs"] == 0
    assert finding.metrics["unmatched_levels"] == 4


def test_unpaired_composite_candidate_key_missing_a_column_abstains_explicitly():
    from sc_referee import statuses as S
    from sc_referee.checks.pairing import PairingCheck

    obs = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D2"],
        "condition": ["ctrl", "stim", "ctrl", "stim"],
    })
    design = replace(_unpaired_design(), replicate_unit=["donor_id", "visit_id"])

    finding = PairingCheck().run(design, _bundle(obs))

    assert finding.status == "needs_evidence"
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"
    assert finding.metrics["pairing_key"] == ["donor_id", "visit_id"]
    assert finding.metrics["missing_fields"] == ["visit_id"]
    assert finding.metrics["coverage_reason"] == "missing_pairing_key_columns"
    assert "couldn't check the pairing" in finding.verdict.lower()
    assert "complete_pairs" not in finding.metrics


def test_paired_composite_key_missing_a_column_abstains_explicitly():
    from sc_referee import statuses as S
    from sc_referee.checks.pairing import PairingCheck

    obs = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D2"],
        "condition": ["ctrl", "stim", "ctrl", "stim"],
    })
    design = make_design(
        unit_of_test="sample", pairing_unit=["donor_id", "visit_id"])

    finding = PairingCheck().run(design, _bundle(obs))

    assert finding.status == "needs_evidence"
    assert finding.coverage == S.NOT_RUN
    assert S.human_state(finding) == "not_checked"
    assert finding.metrics["pairing_key"] == ["donor_id", "visit_id"]
    assert finding.metrics["missing_fields"] == ["visit_id"]
    assert "complete_pairs" not in finding.metrics


def test_degenerate_contrast_level_does_not_duplicate_rows_into_both_arms():
    from sc_referee.checks.pairing import PairingCheck

    obs = pd.DataFrame({"donor_id": ["D1", "D2"], "condition": ["ctrl", "ctrl"]})
    design = replace(_unpaired_design(), reference="ctrl", test="ctrl")

    finding = PairingCheck().run(design, _bundle(obs))

    assert finding.status == "pass"
    assert finding.metrics["complete_pairs"] == 0


def test_well_formed_paired_design_passes():
    from sc_referee.checks.pairing import PairingCheck
    f = PairingCheck().run(_paired_design(), _bundle(paired_crossed_obs()))
    assert f.status == "pass"


def test_partial_pairs_are_informational_not_a_defect():
    from sc_referee.checks.pairing import PairingCheck
    obs = paired_crossed_obs()
    # drop D4's stim rows -> D4 appears in only one arm (an incomplete pair, legitimately dropped)
    obs = obs[~((obs["donor_id"] == "D4") & (obs["condition"] == "stim"))]
    f = PairingCheck().run(_paired_design(), _bundle(obs))
    assert f.status == "informational" and "one arm" in f.verdict.lower()
    assert (f.coverage, f.judgment, S.human_state(f)) == (S.COMPLETE, None, S.CLEAR)


# --- the duplicated-pairing BLOCKER: aggregation yields >1 sample per (pair, arm) -> matching ambiguous ---

def _dup_obs():
    # D1 has control in TWO batches -> aggregating by donor x condition x batch gives (D1, ctrl) TWO
    # pseudobulk samples; the donor<->donor pairing across conditions is then ambiguous.
    return pd.DataFrame({
        "donor_id":  ["D1", "D1", "D1", "D2", "D2", "D2"],
        "condition": ["ctrl", "ctrl", "stim", "ctrl", "ctrl", "stim"],
        "batch":     ["b1", "b2", "b1", "b1", "b2", "b1"],
    }, index=[f"c{i}" for i in range(6)])


def test_max_status_is_now_blocker():
    from sc_referee.checks.pairing import PairingCheck
    from sc_referee import statuses as S
    assert PairingCheck().max_status == S.BLOCKER


def test_within_pair_estimand_alone_never_authorizes_duplicate_blocker():
    from sc_referee.checks.pairing import PairingCheck
    d = make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                    aggregation_key=["donor_id", "condition", "batch"], pairing_estimand="within_pair")
    f = PairingCheck().run(d, _bundle(_dup_obs()))
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_explicit_one_to_one_mechanics_retains_duplicate_blocker():
    from sc_referee.checks.pairing import PairingCheck
    d = make_design(
        unit_of_test="sample", pairing_unit=["donor_id"],
        aggregation_key=["donor_id", "condition", "batch"],
        pairing_estimand="within_pair", pairing_mechanics="one_to_one",
    )
    f = PairingCheck().run(d, _bundle(_dup_obs()))
    assert f.status == S.BLOCKER
    assert f.judgment == S.VIOLATION


def test_repeated_measures_within_pair_abstains_on_duplicate_visits():
    from sc_referee.checks.pairing import PairingCheck
    d = make_design(
        unit_of_test="sample", pairing_unit=["donor_id"],
        aggregation_key=["donor_id", "condition", "batch"],
        pairing_estimand="within_pair", pairing_mechanics="repeated_measures",
    )
    f = PairingCheck().run(d, _bundle(_dup_obs()))
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )
    assert "repeated" in f.verdict.lower()


def test_duplicated_without_within_pair_estimand_is_needs_evidence():
    # FALSE-ACCUSE guard (adversarial pairing review #2): a mixed/repeated-measures model handles multiplicity;
    # column names alone don't prove a one-to-one estimand, so without `within_pair` it may NOT block.
    from sc_referee.checks.pairing import PairingCheck
    d = make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                    aggregation_key=["donor_id", "condition", "batch"])   # no pairing_estimand
    f = PairingCheck().run(d, _bundle(_dup_obs()))
    assert f.status == "needs_evidence"
    assert (f.coverage, S.human_state(f)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_duplicates_only_on_an_unmatched_level_do_not_block():
    # FALSE-ACCUSE guard (adversarial pairing review #1): D4 has two control samples and NO stim, so a paired
    # analysis drops it entirely — its duplicates must not fire.
    from sc_referee.checks.pairing import PairingCheck
    obs = pd.DataFrame({
        "donor_id":  ["D1", "D1", "D2", "D2", "D3", "D3", "D4", "D4"],
        "condition": ["ctrl", "stim", "ctrl", "stim", "ctrl", "stim", "ctrl", "ctrl"],
        "batch":     ["b1", "b1", "b1", "b1", "b1", "b1", "b1", "b2"],
    }, index=[f"c{i}" for i in range(8)])
    d = make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                    aggregation_key=["donor_id", "condition", "batch"], pairing_estimand="within_pair")
    f = PairingCheck().run(d, _bundle(obs))
    assert f.status != "blocker"


def test_nan_in_aggregation_key_does_not_fabricate_a_duplicate():
    # FALSE-ACCUSE guard (adversarial pairing review #3): a NaN batch is dropped by real groupby, leaving one
    # control sample -> no ambiguous duplicate.
    from sc_referee.checks.pairing import PairingCheck
    obs = pd.DataFrame({"donor_id": ["D1", "D1", "D1"], "condition": ["ctrl", "ctrl", "stim"],
                        "batch": ["b1", np.nan, "b1"]}, index=["c0", "c1", "c2"])
    d = make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                    aggregation_key=["donor_id", "condition", "batch"], pairing_estimand="within_pair")
    f = PairingCheck().run(d, _bundle(obs))
    assert f.status != "blocker"


def test_one_sample_per_pair_arm_is_not_a_duplicated_blocker():
    # aggregation_key = donor x condition -> exactly one sample per (donor, arm) -> clean 1:1 pairing
    from sc_referee.checks.pairing import PairingCheck
    d = make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                    aggregation_key=["donor_id", "condition"], pairing_estimand="within_pair")
    f = PairingCheck().run(d, _bundle(paired_crossed_obs()))
    assert f.status != "blocker"


def test_two_stage_collapse_uses_the_final_key_not_the_intermediate(monkeypatch=None):
    # FALSE-ACCUSE guard (adversarial pairing review, final): lanes summed before the sink are technical
    # replicates. `aggregation_key` is the FINAL post-collapse key, so the human ratifies [donor,
    # condition] (not the intermediate [donor, condition, lane]) -> exactly one sample per arm -> no block.
    from sc_referee.checks.pairing import PairingCheck
    obs = pd.DataFrame({
        "donor_id":  ["D1", "D1", "D1", "D1", "D2", "D2", "D2", "D2"],
        "condition": ["ctrl", "ctrl", "stim", "stim", "ctrl", "ctrl", "stim", "stim"],
        "lane":      ["L1", "L2", "L1", "L2", "L1", "L2", "L1", "L2"],
    }, index=[f"c{i}" for i in range(8)])
    d = make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                    aggregation_key=["donor_id", "condition"], pairing_estimand="within_pair")
    f = PairingCheck().run(d, _bundle(obs))
    assert f.status != "blocker"


def test_duplicated_pairing_capped_when_not_confirmed():
    from sc_referee.checks.pairing import PairingCheck
    d = make_design(unit_of_test="sample", pairing_unit=["donor_id"],
                    aggregation_key=["donor_id", "condition", "batch"], pairing_estimand="within_pair",
                    pairing_mechanics="one_to_one",
                    confirmed=False)
    f = PairingCheck().run(d, _bundle(_dup_obs()))
    assert f.status != "blocker"
    assert (f.status, f.coverage, S.human_state(f)) == (
        S.NEEDS_EVIDENCE, S.NOT_RUN, S.NOT_CHECKED
    )


def test_no_aggregation_key_falls_back_to_diagnostic_pairing():
    # without a ratified aggregation_key the duplicated blocker cannot run; existing behavior stands
    from sc_referee.checks.pairing import PairingCheck
    d = _paired_design()   # no aggregation_key
    f = PairingCheck().run(d, _bundle(paired_crossed_obs()))
    assert f.status == "pass"
