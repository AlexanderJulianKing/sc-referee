"""Wire the pseudobulk recompute into the bundle path. When a data file loads as RAW counts and a
condition + donor/replicate resolve, actually recompute the contrast at the DONOR level and report a
needs_evidence DIAGNOSTIC; otherwise say 'recompute available — confirm a design to run it'. Never a
pass or blocker on an unconfirmed bundle. It runs OUR analysis on THEIR data — it never runs their code.
"""
import numpy as np
import pandas as pd
import pytest

anndata = pytest.importorskip("anndata")


def _write_counts_h5ad(path, n_cells=600, n_genes=40, per_arm=4):
    rng = np.random.default_rng(0)
    donors = [f"donor{i}" for i in range(2 * per_arm)]
    arm = {d: ("ctrl" if i < per_arm else "stim") for i, d in enumerate(donors)}
    cell_donor = rng.choice(donors, size=n_cells)
    X = rng.poisson(2.0, size=(n_cells, n_genes)).astype("float32")   # integer-valued -> raw counts
    obs = pd.DataFrame({"donor": cell_donor, "condition": [arm[d] for d in cell_donor]})
    a = anndata.AnnData(X=X, obs=obs)
    a.var_names = [f"g{j}" for j in range(n_genes)]
    a.write_h5ad(path)


def _bundle(tmp_path, de_step=True, report="We found 12 differentially expressed genes at padj < 0.05.\n"):
    (tmp_path / "scripts").mkdir(exist_ok=True)
    if de_step:
        (tmp_path / "scripts" / "02_de.py").write_text(
            "import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='condition', method='wilcoxon')\n")
    else:
        (tmp_path / "scripts" / "01_plot.py").write_text("import matplotlib.pyplot as plt\nplt.plot([1,2])\n")
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "report.md").write_text("# DE\n" + report)


def test_recompute_runs_when_counts_and_roles_resolve(tmp_path):
    from sc_referee.bundle_recompute import bundle_recompute
    from sc_referee.science_bundle import inventory_bundle
    (tmp_path / "data").mkdir()
    _write_counts_h5ad(tmp_path / "data" / "counts.h5ad")
    _bundle(tmp_path)
    f = bundle_recompute(inventory_bundle(tmp_path), tmp_path)
    assert f is not None
    assert f.status == "needs_evidence"                          # never pass/blocker on an unconfirmed bundle
    assert ("donor" in f.verdict.lower() or "pseudobulk" in f.verdict.lower())
    assert "recompute_significant" in f.metrics


def test_recompute_points_to_confirm_when_no_replicate(tmp_path):
    """Counts load but there's no donor column -> can't resolve the design -> honest 'confirm to run'."""
    from sc_referee.bundle_recompute import bundle_recompute
    from sc_referee.science_bundle import inventory_bundle
    (tmp_path / "data").mkdir()
    a = anndata.AnnData(X=np.random.default_rng(1).poisson(2, (120, 20)).astype("float32"),
                        obs=pd.DataFrame({"condition": ["ctrl"] * 60 + ["stim"] * 60}))
    a.write_h5ad(tmp_path / "data" / "counts.h5ad")
    _bundle(tmp_path)
    f = bundle_recompute(inventory_bundle(tmp_path), tmp_path)
    assert f is not None and f.status == "needs_evidence"
    assert "confirm" in f.verdict.lower()


def test_no_de_contrast_returns_none(tmp_path):
    from sc_referee.bundle_recompute import bundle_recompute
    from sc_referee.science_bundle import inventory_bundle
    _bundle(tmp_path, de_step=False, report="A UMAP figure.\n")
    assert bundle_recompute(inventory_bundle(tmp_path), tmp_path) is None
