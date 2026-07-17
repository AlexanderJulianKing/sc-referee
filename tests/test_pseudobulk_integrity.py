"""pseudobulk_integrity (spine step 2, increment 1): structural invariants over the pseudobulk the DE
count-model sink consumes. Increment 1 is needs_evidence-only — the blocker-capable invariants each need
machinery SinkUse v1 defers (reaching-scale for the assay contract; a ratified actual_aggregation_key for
the merge), per the Codex design consult. It does the two SOUND things it can: use SinkUse's structural
binding to flag a count model that reads a normalized `.X`, and flag a missing value in the aggregation
key. It must NOT flag a count model reading a RAW LAYER while `.X` is normalized (the false-accuse guard).
"""
import numpy as np
import pandas as pd
from dataclasses import replace

from sc_referee import statuses as S
from sc_referee.bundle import Bundle, Measure
from tests.factories import make_design, paired_crossed_obs, unpaired_crossed_obs


def _bundle(kind, source, obs=None):
    obs = obs if obs is not None else pd.DataFrame(
        {"donor_id": ["D1", "D1", "D2", "D2"], "condition": ["ctrl", "stim", "ctrl", "stim"]},
        index=[f"c{i}" for i in range(4)])
    genes = ["g1", "g2"]
    counts = np.ones((len(obs), 2), dtype="int64") if kind == "counts" else None
    b = Bundle(observations=obs, measure=Measure(kind, counts, None, genes),
               feature_metadata=pd.DataFrame(index=genes), replicate_var="donor_id")
    b.code_signals = {"sources": [source], "de_calls": ["deseqdataset"], "files": ["de.py"]}
    return b


_DDS = "from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(counts={resp}, metadata=m, design='~condition')\n"


def test_countmodel_reading_normalized_dotX_is_needs_evidence():
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    b = _bundle("normalized", _DDS.format(resp="adata.X"))
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"])
    chk = PseudobulkIntegrityCheck()
    assert chk.applies_to(d, b)
    f = chk.run(d, b)
    assert f.status == "needs_evidence" and ".X" in f.verdict
    assert (f.coverage, S.human_state(f)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_countmodel_reading_raw_layer_while_dotX_normalized_does_not_flag():
    # THE false-accuse guard: raw counts in a layer, .X normalized -> the sink got raw counts. Don't flag.
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    b = _bundle("normalized", _DDS.format(resp="adata.layers['counts']"))
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"])
    f = PseudobulkIntegrityCheck().run(d, b)
    assert f.status != "needs_evidence"      # reads a layer, not .X -> no assay smell


def test_countmodel_reading_raw_dotX_passes():
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    b = _bundle("counts", _DDS.format(resp="adata.X"))
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"])
    f = PseudobulkIntegrityCheck().run(d, b)
    assert f.status == "pass"


def test_missing_value_in_aggregation_key_is_needs_evidence():
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    obs = pd.DataFrame({"donor_id": ["D1", "D1", None, "D2"], "condition": ["ctrl", "stim", "ctrl", "stim"]},
                       index=[f"c{i}" for i in range(4)])
    b = _bundle("counts", _DDS.format(resp="pb"), obs=obs)   # local-var response: no assay smell
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"])
    f = PseudobulkIntegrityCheck().run(d, b)
    assert f.status == "needs_evidence" and "missing" in f.verdict.lower()


def test_no_countmodel_sink_does_not_apply():
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    b = _bundle("counts", "from scipy.stats import ttest_ind\nttest_ind(a, b)\n")
    b.code_signals["de_calls"] = ["ttest_ind"]
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"])
    assert not PseudobulkIntegrityCheck().applies_to(d, b)


def test_absent_declared_key_column_is_needs_evidence():
    # a sample_unit naming a column absent from .obs cannot be verified -> don't return a clean pass
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    b = _bundle("counts", _DDS.format(resp="pb"))
    d = make_design(unit_of_test="sample", sample_unit=["absent_key"])
    f = PseudobulkIntegrityCheck().run(d, b)
    assert f.status == "needs_evidence"


def test_unsupported_response_binding_is_needs_evidence():
    # DeseqDataSet(**kwargs): the response is `unsupported`, so its scale can't be checked -> review
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    src = "from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(**kwargs)\n"
    b = _bundle("normalized", src)
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"])
    f = PseudobulkIntegrityCheck().run(d, b)
    assert f.status == "needs_evidence"
    assert (f.coverage, S.human_state(f)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_dotX_wrapped_in_copy_still_flagged():
    # `.X.copy()` is still a read of the normalized main matrix -> the assay smell must not be evaded
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    b = _bundle("normalized", _DDS.format(resp="adata.X.copy()"))
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"])
    f = PseudobulkIntegrityCheck().run(d, b)
    assert f.status == "needs_evidence" and ".X" in f.verdict


# --- the keystone: the aggregation-merge BLOCKER (a ratified aggregation_key that merges the arms) ---

def _dds_bundle(obs):
    genes = ["g1", "g2"]
    b = Bundle(observations=obs, measure=Measure("counts", np.ones((len(obs), 2), dtype="int64"),
                                                 None, genes),
               feature_metadata=pd.DataFrame(index=genes), replicate_var="donor_id")
    b.code_signals = {"sources": [_DDS.format(resp="pb")], "de_calls": ["deseqdataset"], "files": ["de.py"]}
    return b


def test_max_status_is_now_blocker():
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    from sc_referee import statuses as S
    assert PseudobulkIntegrityCheck().max_status == S.BLOCKER


def test_aggregation_key_that_merges_arms_is_a_blocker():
    # aggregation_key=[donor] excludes the contrast, and each donor has BOTH ctrl and stim cells, so every
    # pseudobulk sample mixes the two arms -> the DE contrast is meaningless -> BLOCKER.
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"], aggregation_key=["donor_id"])
    f = PseudobulkIntegrityCheck().run(d, _dds_bundle(paired_crossed_obs()))
    assert f.status == "blocker" and "both" in f.verdict.lower()


def test_aggregation_key_including_the_contrast_does_not_flag():
    # THE must-not-flag: donor x condition -> each output is pure in condition, no arm is merged.
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"],
                    aggregation_key=["donor_id", "condition"])
    f = PseudobulkIntegrityCheck().run(d, _dds_bundle(paired_crossed_obs()))
    assert f.status != "blocker"


def test_between_subject_aggregation_key_does_not_merge():
    # each donor is in only ONE arm (D1-D4 ctrl, D5-D8 stim) -> aggregating by donor never mixes arms.
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"], aggregation_key=["donor_id"])
    f = PseudobulkIntegrityCheck().run(d, _dds_bundle(unpaired_crossed_obs()))
    assert f.status != "blocker"


def test_merge_is_capped_to_needs_evidence_when_not_confirmed():
    # the blocker gate: unconfirmed / low-confidence aggregation_key may not assert a blocker.
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"], aggregation_key=["donor_id"],
                    confirmed=False)
    f = PseudobulkIntegrityCheck().run(d, _dds_bundle(paired_crossed_obs()))
    assert f.status == "needs_evidence"
    assert (f.coverage, S.human_state(f)) == (S.NOT_RUN, S.NOT_CHECKED)


def test_missing_ratified_key_column_does_not_block(monkeypatch=None):
    # FALSE-ACCUSE guard (Codex keystone review #1): a correct donor x arm aggregation whose derived
    # `arm_alias` column is not in .obs must NOT be reduced to donor-only and blocked.
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"],
                    aggregation_key=["donor_id", "arm_alias"])   # arm_alias absent from obs
    f = PseudobulkIntegrityCheck().run(d, _dds_bundle(paired_crossed_obs()))
    assert f.status == "needs_evidence"       # abstain, never block on a reduced key
    assert f.coverage == S.NOT_RUN
    assert S.human_state(f) == "not_checked"


def test_distinct_levels_under_string_coercion_are_not_conflated():
    # FALSE-ACCUSE guard (Codex keystone review #2): int 1 and str "1" are DISTINCT levels; a
    # between-subject design (D1 in level 1, D2 in level "1") must not be read as arm-merging.
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    obs = pd.DataFrame({"donor_id": ["D1", "D1", "D2", "D2"], "condition": [1, 1, "1", "1"]},
                       index=[f"c{i}" for i in range(4)])
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"], aggregation_key=["donor_id"],
                    reference=1, test="1")
    f = PseudobulkIntegrityCheck().run(d, _dds_bundle(obs))
    assert f.status != "blocker"


def test_null_aggregation_key_rows_do_not_form_a_merge_group():
    # pandas groupby drops a null determinant by default. D1 would span both arms only if those null-key
    # rows were retained; the merge rule must preserve the producing aggregation's drop-null semantics.
    from sc_referee.checks.pseudobulk_integrity import PseudobulkIntegrityCheck
    obs = pd.DataFrame({
        "donor_id": ["D1", "D1", "D2", "D3"],
        "condition": ["ctrl", "stim", "ctrl", "stim"],
        "batch": [np.nan, np.nan, "b1", "b1"],
    }, index=[f"c{i}" for i in range(4)])
    d = make_design(unit_of_test="sample", sample_unit=["donor_id"],
                    aggregation_key=["donor_id", "batch"])
    f = PseudobulkIntegrityCheck().run(d, _dds_bundle(obs))
    assert f.status != "blocker"
