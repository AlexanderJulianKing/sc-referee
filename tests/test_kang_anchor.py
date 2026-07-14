"""Item 5: the real-data anchor — does the verdict hold off synthetic data? (Kang 2018, GSE96583.)

Skips unless the raw-counts h5ad is present (it is gitignored; download in bench/kang_anchor.py). The
honest result: a per-cell Wilcoxon of stim vs ctrl claims thousands of genes; sc-referee recomputes
at the DONOR level (8 patients, pydeseq2 NB) and neither rubber-stamps the list (pass) nor
false-accuses the real, strong IFN-β effect (blocker). It lands in the honest middle — the claims
only PARTLY survive — and on the underpowered single-cell-type subset it abstains (needs_evidence).
That is specificity + calibration, measured on real data, not asserted.
"""
from pathlib import Path

import pytest

pytest.importorskip("pydeseq2")
DATA = Path(__file__).resolve().parents[1] / "data" / "kang.h5ad"
pytestmark = [
    pytest.mark.filterwarnings("ignore"),
    pytest.mark.skipif(not DATA.exists(),
                       reason="Kang data not downloaded — see bench/kang_anchor.py for the curl command"),
]


def test_kang_real_data_anchor_neither_rubber_stamps_nor_false_accuses():
    from bench.kang_anchor import run_kang_anchor

    finding, info = run_kang_anchor()                     # all cell types (powered at 8 donors)

    assert info["n_donors"] == 8 and info["paired"] is True
    assert info["per_cell_claimed"] > 4000                # massive pseudoreplication inflation (real data)

    # The honest middle the real (strong, but cell-inflated) IFN-β effect warrants: neither a clean
    # bill of health nor a false accusation of a genuine effect.
    assert finding.status not in ("pass", "blocker")
    assert finding.metrics["survival_rate"] < 0.60        # the claims only PARTLY survive donor-level


def test_kang_underpowered_subset_abstains():
    """CD14+ monocytes alone (fewer cells -> underpowered at 8 donors): honest needs_evidence, not
    a manufactured blocker."""
    from bench.kang_anchor import run_kang_anchor

    finding, info = run_kang_anchor(cell_type="CD14+ Monocytes")
    assert finding.status == "needs_evidence"
    assert finding.metrics["powered"] is False
