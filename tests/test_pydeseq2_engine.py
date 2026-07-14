"""The pydeseq2 recompute engine (the one that can BLOCK).

Smoke test on the paired count bundle: a strong donor-consistent effect must be recovered
(effect on the log2 scale, padj significant, a positive lfcSE for the Wald MDE)."""
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
