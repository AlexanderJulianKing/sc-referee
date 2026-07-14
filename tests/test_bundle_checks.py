"""The bundle -> check bridge: run sc-referee's structural checks against a PARSED multi-step bundle,
reusing the SAME decision ladder as the single-contrast audit path.

The headline case is double_dipping. The test that matters most is specificity: in a chain that has
BOTH a legitimate predefined-group DE and a de-novo-cluster-then-marker analysis, the bridge must
flag the double-dip and leave the legit DE completely alone. A bundle is never human-confirmed, so
the strongest it can assert is `needs_evidence` (structure caught) — a blocker still requires the
confirm ratification on the specific contrast.
"""
from pathlib import Path

import pytest


def _write(root: Path, rel: str, text: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _mixed(root, safeguard=False, marker_pvalues=True):
    """A realistic Claude-Science-shaped chain: QC -> legit predefined-group pseudobulk DE ->
    de-novo Leiden clustering -> per-cluster marker DE (the double-dip)."""
    _write(root, "scripts/01_qc.py", "import scanpy as sc\nsc.pp.normalize_total(a)\n")
    _write(root, "scripts/02_condition_de.py",
           "from pydeseq2.dds import DeseqDataSet\n"
           "dds = DeseqDataSet(counts=c, metadata=m, design_factors='genotype')\n")
    _write(root, "scripts/03_cluster.py", "import scanpy as sc\nsc.tl.leiden(adata, key_added='cluster')\n")
    marker = "import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='cluster')\n"
    if safeguard:
        marker += "from countsplit import countsplit\nX1, X2 = countsplit(adata.X)\n"
    _write(root, "scripts/04_cluster_markers.py", marker)
    pv = "at padj < 0.05" if marker_pvalues else "ranked by score"
    _write(root, "docs/report.md",
           "# Findings\nPseudobulk WT vs KO: 830 DE genes at padj < 0.05.\n"
           f"Cluster 7 shows 42 marker genes {pv}, including Adgrl2.\n")


def test_double_dipping_flagged_but_legit_de_untouched(tmp_path):
    from sc_referee.science_bundle import bundle_findings, inventory_bundle
    _mixed(tmp_path)
    findings = bundle_findings(inventory_bundle(tmp_path))
    dd = [f for f in findings if f.check_id == "double_dipping"]
    assert len(dd) == 1
    f = dd[0]
    # F34: prose that merely names a padj threshold is not a finite numeric probability claim.
    assert f.status == "informational"
    assert "cluster" in f.verdict.lower()               # names the de-novo selection
    assert "leiden" in str(f.metrics).lower()           # names the clustering method
    # specificity: the ONLY finding is the double-dip; the pydeseq2 condition-DE is never accused
    assert all(x.check_id == "double_dipping" for x in findings)


def test_safeguard_present_is_review_not_pass(tmp_path):
    """A detected safeguard keyword is REVIEW, not a clean pass — a keyword doesn't prove the
    safeguard is correctly applied (spec rev. 5 §5). This is the liver_fibrosis case."""
    from sc_referee.science_bundle import bundle_findings, inventory_bundle
    _mixed(tmp_path, safeguard=True)
    dd = [f for f in bundle_findings(inventory_bundle(tmp_path)) if f.check_id == "double_dipping"][0]
    # Descriptive-claim routing precedes safeguard review when no numeric probability was reported.
    assert dd.status == "informational"


def test_rankings_without_pvalues_are_informational(tmp_path):
    from sc_referee.science_bundle import bundle_findings, inventory_bundle
    _mixed(tmp_path, marker_pvalues=False)
    dd = [f for f in bundle_findings(inventory_bundle(tmp_path)) if f.check_id == "double_dipping"][0]
    assert dd.status == "informational"                 # descriptive markers, no inference claim


def test_unresolved_grouping_is_needs_evidence_not_silent(tmp_path):
    """adversarial-review finding 3: a data-derived column tested via a DYNAMIC groupby is unresolved to the
    analyzer — it must surface as needs_evidence, never vanish into no-finding (a false-clean)."""
    from sc_referee.science_bundle import bundle_findings, inventory_bundle
    _write(tmp_path, "scripts/03.py",
           "labels = discover(adata.X)\nadata.obs['sub'] = labels\n"
           "col = 'sub'\nsc.tl.rank_genes_groups(adata, groupby=col)\n")
    _write(tmp_path, "docs/report.md", "# M\nSubpop markers at padj < 0.05.\n")
    dd = [f for f in bundle_findings(inventory_bundle(tmp_path)) if f.check_id == "double_dipping"]
    assert dd and dd[0].status == "informational"


def test_predefined_pvalue_claim_does_not_make_descriptive_cluster_inferential(tmp_path):
    """adversarial-review finding 5: a padj claim that belongs to a PREDEFINED test must not make a descriptive
    (no-p-value) cluster test inferential. Attribution is per-claim, not a bundle-wide boolean."""
    from sc_referee.science_bundle import bundle_findings, inventory_bundle
    _write(tmp_path, "scripts/03.py",
           "adata.obs['cluster'] = discover(adata.X)\n"
           "sc.tl.rank_genes_groups(adata, groupby='cluster')\n"       # descriptive, no p-values reported
           "sc.tl.rank_genes_groups(adata, groupby='genotype')\n")     # predefined, p-values reported
    _write(tmp_path, "docs/report.md", "# R\nGenotype comparison found 20 marker genes at padj < 0.05.\n")
    dd = [f for f in bundle_findings(inventory_bundle(tmp_path)) if f.check_id == "double_dipping"]
    assert dd and dd[0].status != "needs_evidence"         # descriptive cluster -> informational, not flagged


def test_predefined_group_de_only_is_not_flagged(tmp_path):
    """A chain with ONLY pseudobulk DE (no de-novo clustering into markers) -> no double_dipping finding."""
    from sc_referee.science_bundle import bundle_findings, inventory_bundle
    _write(tmp_path, "scripts/01_de.py",
           "from pydeseq2.dds import DeseqDataSet\nDeseqDataSet(design_factors='genotype')\n")
    _write(tmp_path, "docs/report.md", "# DE\n830 genes at padj < 0.05.\n")
    findings = bundle_findings(inventory_bundle(tmp_path))
    assert not any(f.check_id == "double_dipping" for f in findings)


def test_custom_named_clustering_into_markers_must_be_caught(tmp_path):
    """The anti-crack guardrail, now GREEN via Layer 2. Clustering done by a bespoke function on the
    data (no leiden/gmm/etc. token anywhere), then markers tested on its output with p-values, is
    STILL a double-dip. A vocabulary-only detector read it clean — the exact failure that must never
    survive. Provenance (taint from `X_pca` -> `discover_subpops(...)` -> obs['subpop'] -> the marker
    test) closes it. See the design notes."""
    from sc_referee.science_bundle import bundle_findings, inventory_bundle
    _write(tmp_path, "scripts/03_group.py",
           '"""Group discovery. Inputs: [\'qc.h5ad\']"""\n'
           "import numpy as np\n"
           "def discover_subpops(embedding):\n"
           "    return (embedding[:, 0] > 0).astype(int)   # bespoke partition of the data\n"
           "labels = discover_subpops(adata.obsm['X_pca'])\n"
           "adata.obs['subpop'] = labels\n")
    _write(tmp_path, "scripts/04_markers.py",
           '"""Markers per subpop. Inputs: [\'clustered.h5ad\']"""\n'
           "import scanpy as sc\n"
           "sc.tl.rank_genes_groups(adata, groupby='subpop', method='wilcoxon')\n")
    _write(tmp_path, "docs/report.md", "# Markers\nSubpop 3 shows 55 marker genes at padj < 0.05.\n")
    findings = bundle_findings(inventory_bundle(tmp_path))
    assert any(f.check_id == "double_dipping" for f in findings)
