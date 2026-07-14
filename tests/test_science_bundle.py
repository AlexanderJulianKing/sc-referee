"""Ingest a Claude Science export bundle — a MULTI-STEP package (numbered scripts + data + a report
with claims) — into a structured inventory, parsing (never executing) the code. This is the front door
for auditing the real thing scientists produce: not a clean single result, a chain of steps.
"""
import shutil


def _make_bundle(root):
    (root / "scripts").mkdir(parents=True)
    (root / "data").mkdir()
    (root / "docs").mkdir()
    (root / "scripts" / "01_cluster.py").write_text(
        '"""Fig 1 clustering. Inputs: [\'counts.h5ad\']"""\n'
        "import scanpy as sc\nsc.tl.leiden(a)\nsc.tl.rank_genes_groups(a)\n")
    (root / "scripts" / "02_de.py").write_text(
        '"""Fig 2 DE. Inputs: [\'counts.h5ad\']\nReconstructed from artifact lineage (version abc12345-de00)."""\n'
        "import pydeseq2\nfrom pydeseq2.dds import DeseqDataSet\n")
    (root / "data" / "counts.h5ad").write_bytes(b"\x00\x01")
    (root / "docs" / "report.md").write_text(
        "# Findings\n\nWe report **42 significant genes** at padj < 0.05.\n"
        "The SS-A exon shows 94% median PSI in neurons vs 1% elsewhere.\n"
        "The pipeline is well designed.\n")   # <- no number -> not a claim
    (root / "requirements.txt").write_text("pandas\nnumpy\n")


def test_inventory_folder_parses_steps_data_and_claims(tmp_path):
    from sc_referee.science_bundle import inventory_bundle
    _make_bundle(tmp_path)
    inv = inventory_bundle(tmp_path)

    assert [s.name for s in inv.steps] == ["01_cluster.py", "02_de.py"]      # ordered by prefix
    assert inv.steps[0].order == 1 and inv.steps[1].order == 2
    assert inv.steps[0].declared_inputs == ["counts.h5ad"]
    assert "leiden" in inv.steps[0].calls["cluster"]
    assert "rank_genes_groups" in inv.steps[0].calls["de_cell"]
    assert "pydeseq2" in inv.steps[1].calls["de_sample"]
    assert inv.steps[1].lineage == "abc12345-de00"                           # traced to the conversation
    assert any(d.name.endswith("counts.h5ad") for d in inv.data)
    assert inv.requirements == ["requirements.txt"]

    claims = inv.reports[0].claims
    assert any("42" in c and "gene" in c.lower() for c in claims)            # the DE claim
    assert any("94%" in c for c in claims)                                   # the PSI claim
    assert not any("well designed" in c for c in claims)                     # prose, no number -> not a claim


def test_analysis_calls_union_flags_cluster_then_de(tmp_path):
    from sc_referee.science_bundle import inventory_bundle
    _make_bundle(tmp_path)
    calls = inventory_bundle(tmp_path).analysis_calls
    assert "leiden" in calls["cluster"] and "rank_genes_groups" in calls["de_cell"]   # double-dipping shape


def test_inventory_reads_a_zip_without_extracting(tmp_path):
    from sc_referee.science_bundle import inventory_bundle
    _make_bundle(tmp_path / "b")
    shutil.make_archive(str(tmp_path / "bundle"), "zip", tmp_path / "b")
    inv = inventory_bundle(tmp_path / "bundle.zip")
    assert len(inv.steps) == 2 and len(inv.data) >= 1
    assert inv.steps[1].lineage == "abc12345-de00"


def _claims_of(tmp_path, md: str):
    from sc_referee.science_bundle import inventory_bundle
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "r.md").write_text(md)
    return inventory_bundle(tmp_path).reports[0].claims


def test_claim_extraction_strips_markdown_and_keeps_full_sentence(tmp_path):
    claims = _claims_of(tmp_path, "# Results\n\nCluster 7 shows **42 marker genes** at padj < 0.05.\n")
    assert "Cluster 7 shows 42 marker genes at padj < 0.05." in claims
    assert not any("*" in c or "`" in c for c in claims)


def test_claim_extraction_does_not_split_on_decimals(tmp_path):
    claims = _claims_of(tmp_path, "We found 830 genes at padj < 0.05 overall.\n")
    assert len(claims) == 1 and "0.05 overall" in claims[0]


def test_claim_extraction_splits_two_sentences(tmp_path):
    claims = _claims_of(tmp_path,
                        "Cluster 3 had 58 markers at padj < 0.05. Cluster 8 had 71 markers at padj < 0.05.\n")
    assert len(claims) == 2
    assert all(c.endswith(".") and "**" not in c for c in claims)


def test_claim_extraction_excludes_nonquantitative_prose_and_ids(tmp_path):
    """A tighter filter: a number must sit in a quantitative context (%, p-value, or N <count-noun>),
    so gene IDs and bare prose are not claims."""
    claims = _claims_of(tmp_path,
                        "# ADGRL2 (ENSG00000117114, chr1)\n\n"
                        "The gene ADGRL2 is located on chromosome 1.\n"
                        "The pipeline is well designed.\n")
    assert claims == []


def test_claim_extraction_q_value_and_adjusted_p(tmp_path):
    claims = _claims_of(tmp_path, "Cluster markers had q < 0.05.\nMarkers passed adjusted P of 0.01.\n")
    assert len(claims) == 2


def test_claim_extraction_normalizes_unicode_operator(tmp_path):
    claims = _claims_of(tmp_path, "Markers reached adjusted P ≤ 0.05 across clusters.\n")
    assert len(claims) == 1


def test_claim_extraction_unicode_le_operator(tmp_path):
    """adversarial re-review #3: 'q ≤ 0.05' normalizes to 'q <= 0.05' — the operator regex must accept <="""
    claims = _claims_of(tmp_path, "Cluster markers had q ≤ 0.05.\n")
    assert len(claims) == 1


def test_claim_extraction_skips_fenced_code(tmp_path):
    claims = _claims_of(tmp_path,
                        "Intro text with no numbers.\n```\nprint('42 marker genes at padj < 0.05')\n```\nEnd.\n")
    assert claims == []


def test_negated_pvalue_sentence_is_not_a_marker_claim():
    from sc_referee.science_bundle import _is_marker_pvalue_claim
    assert _is_marker_pvalue_claim("We did not report cluster marker p-values here.") is False
    assert _is_marker_pvalue_claim("Cluster 7 had 42 markers at padj < 0.05.") is True


def test_coverage_verdict_auditable_when_a_de_step_exists(tmp_path):
    from sc_referee.science_bundle import coverage_verdict, inventory_bundle
    _make_bundle(tmp_path)                                 # has cluster + cell DE + sample DE
    cov = coverage_verdict(inventory_bundle(tmp_path))
    assert cov.status == "auditable"
    assert "02_de.py" in cov.auditable_steps               # the pydeseq2 step a check can evaluate
    assert any("double_dipping" in n for n in cov.notes)   # cluster + cell-level DE in one pipeline


def test_coverage_verdict_not_audited_when_no_recognized_analysis(tmp_path):
    """A splicing/PSI pipeline uses none of sc-referee's checks -> honest not_audited, never a rubber-stamp."""
    from sc_referee.science_bundle import coverage_verdict, inventory_bundle
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "01_psi.py").write_text("import pandas as pd\npsi = df.mean()\n")
    (tmp_path / "report.md").write_text("# PSI\nSS-A shows 94% median PSI in neurons.\n")
    cov = coverage_verdict(inventory_bundle(tmp_path))
    assert cov.status == "not_audited"
    assert cov.auditable_steps == []
    assert "not looked at" in cov.reason.lower() or "not audited" in cov.reason.lower()
