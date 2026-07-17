"""Tier 2 — static claim attribution. Backward-link each numeric report claim to the test that
produced it (no execution) and attach that test's provenance verdict to the sentence. The point is
resolution: pin `needs_evidence` onto the exact marker sentence, leave the legit condition-DE sentence
alone, and ABSTAIN when a claim can't be uniquely attributed (Codex: ambiguous producers must not be
force-attributed). We certify METHOD validity of the claim, never that the number reproduces.
"""
from pathlib import Path


def _write(root: Path, rel: str, text: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_marker_claim_flagged_condition_de_claim_untouched(tmp_path):
    from sc_referee.science_bundle import attribute_claims, inventory_bundle
    _write(tmp_path, "scripts/02_condition_de.py",
           "from pydeseq2.dds import DeseqDataSet\nDeseqDataSet(design_factors='genotype')\n")
    _write(tmp_path, "scripts/03_cluster.py", "import scanpy as sc\nsc.tl.leiden(adata, key_added='leiden')\n")
    _write(tmp_path, "scripts/04_markers.py",
           "import scanpy as sc\nsc.tl.rank_genes_groups(adata, groupby='leiden')\n")
    _write(tmp_path, "docs/report.md",
           "# Findings\n"
           "Pseudobulk WT vs KO revealed 830 differentially expressed genes at padj < 0.05.\n"
           "Cluster 7 shows 42 marker genes at padj < 0.05.\n")
    attributed = attribute_claims(inventory_bundle(tmp_path))
    flagged = [a for a in attributed if a.status == "needs_evidence"]
    assert len(flagged) == 1
    assert "42 marker genes" in flagged[0].claim and flagged[0].grouping == "leiden"
    # the legit condition-DE sentence is not a marker claim -> never attributed/flagged
    assert not any("830 differentially expressed" in a.claim for a in attributed)


def test_ambiguous_attribution_abstains(tmp_path):
    """Two data-derived marker tests and a claim that names neither column -> abstain, don't guess."""
    from sc_referee.science_bundle import attribute_claims, inventory_bundle
    _write(tmp_path, "scripts/03_two_clusterings.py",
           "import scanpy as sc\n"
           "sc.tl.leiden(adata, key_added='leiden')\n"
           "labels = kmeans(adata.X)\nadata.obs['gmm'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='leiden')\n"
           "sc.tl.rank_genes_groups(adata, groupby='gmm')\n")
    _write(tmp_path, "docs/report.md", "# Findings\nPopulations show 30 markers at padj < 0.05.\n")
    attributed = attribute_claims(inventory_bundle(tmp_path))
    assert attributed and all(a.status == "unresolved" for a in attributed)


def test_unresolved_competing_test_blocks_the_sole_producer_fallback(tmp_path):
    """Codex finding 8: the 'exactly one marker test' fallback must count ALL marker tests (incl.
    unresolved), or a claim from an unresolved-but-legit test is mis-attributed to the data-derived one."""
    from sc_referee.science_bundle import attribute_claims, inventory_bundle
    _write(tmp_path, "scripts/03.py",
           "adata.obs['cluster'] = discover(adata.X)\n"
           "sc.tl.rank_genes_groups(adata, groupby='cluster')\n"       # data-derived
           "col = 'genotype'\nsc.tl.rank_genes_groups(adata, groupby=col)\n")  # unresolved (dynamic)
    _write(tmp_path, "docs/report.md", "# R\nTreatment comparison found 20 marker genes at padj < 0.05.\n")
    flagged = [a for a in attribute_claims(inventory_bundle(tmp_path)) if a.status == "needs_evidence"]
    assert flagged == []                                    # not force-attributed to 'cluster'


def test_column_name_matches_whole_word_only(tmp_path):
    """Codex finding 8: a grouping named 'g' must not substring-match every sentence with a 'g'."""
    from sc_referee.science_bundle import attribute_claims, inventory_bundle
    _write(tmp_path, "scripts/03.py",
           "adata.obs['g'] = discover(adata.X)\nsc.tl.rank_genes_groups(adata, groupby='g')\n"
           "labels = km(adata.X)\nadata.obs['h'] = labels\nsc.tl.rank_genes_groups(adata, groupby='h')\n")
    _write(tmp_path, "docs/report.md", "# R\nThe genotype groups gave 12 marker genes at padj < 0.05.\n")
    # 'g' appears inside 'genotype'/'groups'/'gave' but is not a whole-word match -> not attributed to g
    flagged = [a for a in attribute_claims(inventory_bundle(tmp_path)) if a.status == "needs_evidence"]
    assert not any(a.grouping == "g" for a in flagged)


def test_repeated_grouping_name_with_mixed_origins_abstains(tmp_path):
    """Codex re-review #5: the same obs column tested by a data-derived AND a predefined invocation is
    ambiguous — a claim naming it must abstain (unresolved), not escalate to needs_evidence."""
    from sc_referee.science_bundle import attribute_claims, inventory_bundle
    _write(tmp_path, "scripts/03.py",
           "adata.obs['g'] = discover(adata.X)\n"
           "sc.tl.rank_genes_groups(adata, groupby='g')\n"           # data-derived
           "adata.obs['g'] = adata.obs['genotype']\n"
           "sc.tl.rank_genes_groups(adata, groupby='g')\n")          # predefined
    _write(tmp_path, "docs/report.md", "# R\nThe g comparison found 20 marker genes at padj < 0.05.\n")
    flagged = [a for a in attribute_claims(inventory_bundle(tmp_path)) if a.status == "needs_evidence"]
    assert flagged == []


def test_claim_naming_its_column_attributes_to_that_test(tmp_path):
    from sc_referee.science_bundle import attribute_claims, inventory_bundle
    _write(tmp_path, "scripts/03.py",
           "import scanpy as sc\n"
           "sc.tl.leiden(adata, key_added='leiden')\n"
           "labels = kmeans(adata.X)\nadata.obs['gmm'] = labels\n"
           "sc.tl.rank_genes_groups(adata, groupby='leiden')\n"
           "sc.tl.rank_genes_groups(adata, groupby='gmm')\n")
    _write(tmp_path, "docs/report.md", "# Findings\nThe gmm clusters yield 12 markers at padj < 0.05.\n")
    flagged = [a for a in attribute_claims(inventory_bundle(tmp_path)) if a.status == "needs_evidence"]
    assert len(flagged) == 1 and flagged[0].grouping == "gmm"
