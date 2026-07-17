"""The pydeseq2 recompute engine (the one that can BLOCK).

Smoke test on the paired count bundle: a strong donor-consistent effect must be recovered
(effect on the log2 scale, padj significant, a positive lfcSE for the Wald MDE)."""
import numpy as np
import pandas as pd
import pytest

from sc_referee.engine import aggregate_to_pseudobulk
from tests.factories import make_design, paired_count_bundle

pytest.importorskip("pydeseq2")


# pydeseq2's parametric dispersion fit needs many genes; on a 32-gene toy it falls back to
# mean-based (harmless). Real/benchmark data (thousands of genes) does not trigger this.
@pytest.mark.filterwarnings("ignore:The dispersion trend curve fitting did not converge")
def test_pydeseq2_recompute_recovers_donor_level_effect():
    from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

    bundle = paired_count_bundle(n_donors=8, seed=3)
    design = make_design(sample_unit=("donor_id", "condition"), pairing_unit=("donor_id",))
    pb, meta = aggregate_to_pseudobulk(bundle, design)

    res = pydeseq2_recompute(pb, meta, design)
    assert res.mde_kind == "wald"
    assert res.n_replicates_per_arm == 8

    up = res.table.loc["G_up"]
    assert up.effect > 1.0 and up.padj < 0.05 and up.se > 0 and bool(up.testable)
    assert res.table.loc["G_null"].padj > 0.05


@pytest.mark.parametrize("pb,reason", [
    (pd.DataFrame([[0, 0], [0, 0], [0, 0], [0, 0]], columns=["z1", "z2"]),
     "all_features_zero"),
    (pd.DataFrame(index=range(4)), "no_features"),
])
def test_degenerate_feature_matrices_return_typed_non_certifying_results(pb, reason):
    from sc_referee.engines.pydeseq2_engine import (
        NonCertifyingPydeseq2Result,
        pydeseq2_recompute,
    )

    meta = pd.DataFrame({"condition": ["ctrl", "ctrl", "stim", "stim"]})
    res = pydeseq2_recompute(pb, meta, make_design())
    assert isinstance(res, NonCertifyingPydeseq2Result)
    assert res.certifying is False
    assert res.unavailable_reason == reason
    assert list(res.table.index) == list(pb.columns)
    assert not res.table["testable"].any()


def test_zero_contrast_rows_return_non_certifying_result():
    from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

    pb = pd.DataFrame([[1], [2]], columns=["g"])
    meta = pd.DataFrame({"condition": ["other", "other"]})
    res = pydeseq2_recompute(pb, meta, make_design())
    assert res.unavailable_reason == "no_contrast_rows"
    assert res.n_replicates_per_arm == 0
    assert not res.table["testable"].any()


def test_single_worker_is_default_and_explicit_parallelism_preserves_alignment(monkeypatch):
    import pydeseq2.dds
    import pydeseq2.ds
    from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

    seen = []

    class FakeDDS:
        def __init__(self, *, counts, metadata, design, quiet, n_cpus):
            seen.append(("dds", n_cpus, tuple(counts.columns)))

        def deseq2(self):
            pass

    class FakeStats:
        def __init__(self, dds, contrast, quiet, n_cpus):
            seen.append(("stats", n_cpus, tuple(contrast)))
            self.results_df = pd.DataFrame({
                "pvalue": [0.01], "padj": [0.02], "log2FoldChange": [1.5], "lfcSE": [0.2],
            }, index=["signal"])

        def summary(self):
            pass

    monkeypatch.setattr(pydeseq2.dds, "DeseqDataSet", FakeDDS)
    monkeypatch.setattr(pydeseq2.ds, "DeseqStats", FakeStats)
    pb = pd.DataFrame([[3, 0], [4, 0], [8, 0], [9, 0]], columns=["signal", "zero"])
    meta = pd.DataFrame({"condition": ["ctrl", "ctrl", "stim", "stim"]})

    single = pydeseq2_recompute(pb, meta, make_design())
    parallel = pydeseq2_recompute(pb, meta, make_design(), n_workers=2)

    assert [item[1] for item in seen] == [1, 1, 2, 2]
    pd.testing.assert_frame_equal(single.table, parallel.table)
    assert list(single.table.index) == ["signal", "zero"]
    assert bool(single.table.loc["signal", "testable"])
    assert not bool(single.table.loc["zero", "testable"])


@pytest.mark.parametrize("workers", [0, -1, 33, True])
def test_worker_setting_is_bounded(workers):
    from sc_referee.engines.pydeseq2_engine import pydeseq2_recompute

    with pytest.raises(ValueError, match="n_workers"):
        pydeseq2_recompute(pd.DataFrame([[1]], columns=["g"]),
                           pd.DataFrame({"condition": ["ctrl"]}), make_design(),
                           n_workers=workers)
