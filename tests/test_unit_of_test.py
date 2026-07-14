"""unit_of_test resolution (spine step 3): derive the tested replicate unit from the TYPED sink contract
(SinkUse.accepted_units) rather than a substring name-list. SinkUse is authoritative for Python — it
distinguishes `sc.tl.rank_genes_groups` (a cell-level test) from `sc.pl.rank_genes_groups` (a plot), and
a DESeq2 analysis that merely also plots markers — and only when NO Python sink resolves (R / unparseable
/ bare unimported calls) do we fall back to the coarse token scan (which still covers Seurat FindMarkers).
"""


def test_marker_sink_resolves_to_cell():
    from sc_referee.code_signals import unit_of_test_from_sinks
    src = "import scanpy as sc\nsc.tl.rank_genes_groups(adata, 'leiden')\n"
    assert unit_of_test_from_sinks([src]) == ("cell", True)


def test_count_model_sink_resolves_to_sample():
    from sc_referee.code_signals import unit_of_test_from_sinks
    src = "from pydeseq2.dds import DeseqDataSet\ndds = DeseqDataSet(counts=pb, metadata=m, design='~c')\n"
    assert unit_of_test_from_sinks([src]) == ("sample", True)


def test_ambiguous_test_resolves_but_gives_no_unit():
    # scipy ttest_ind accepts cell OR sample rows — resolved, but the unit is genuinely unsettleable
    from sc_referee.code_signals import unit_of_test_from_sinks
    src = "from scipy.stats import ttest_ind\nttest_ind(a, b)\n"
    assert unit_of_test_from_sinks([src]) == (None, True)


def test_conflicting_marker_and_count_model_is_unresolved_not_guessed():
    # a marker QC step AND a DESeq2 DE — the substring scan wrongly returns "cell" (checks DE_CELL first);
    # honestly we cannot tell which produced the reported table, so the unit is unresolved.
    from sc_referee.code_signals import unit_of_test_from_sinks
    src = ("import scanpy as sc\nfrom pydeseq2.dds import DeseqDataSet\n"
           "sc.tl.rank_genes_groups(adata, 'leiden')\n"
           "dds = DeseqDataSet(counts=pb, metadata=m, design='~c')\n")
    assert unit_of_test_from_sinks([src]) == (None, True)


def test_no_python_sink_resolves_defers_to_the_substring():
    from sc_referee.code_signals import unit_of_test_from_sinks
    # a plot-only call (sc.pl, not sc.tl) and R code resolve NO inferential sink here
    assert unit_of_test_from_sinks(["import scanpy as sc\nsc.pl.umap(adata)\n"]) == (None, False)


def test_resolve_prefers_sinks_over_substring_for_the_conflicting_case():
    # the key improvement: code with both a marker plot-word and DESeq2 no longer routes to "cell"
    from sc_referee.code_signals import resolve_unit_of_test
    cs = {"sources": ["import scanpy as sc\nfrom pydeseq2.dds import DeseqDataSet\n"
                      "sc.tl.rank_genes_groups(adata, 'leiden')\n"
                      "dds = DeseqDataSet(counts=pb, metadata=m, design='~c')\n"],
          "de_calls": ["rank_genes_groups", "deseqdataset"]}
    assert resolve_unit_of_test(cs) is None       # NOT "cell" (what the substring scan would say)


def test_resolve_falls_back_to_substring_for_seurat_r():
    from sc_referee.code_signals import resolve_unit_of_test
    # R source doesn't parse as Python -> no SinkUse -> the FindMarkers token still routes to "cell"
    cs = {"sources": ["markers <- FindMarkers(obj, ident.1 = 'A')\n"], "de_calls": ["findmarkers"]}
    assert resolve_unit_of_test(cs) == "cell"


def test_conflicting_r_scripts_are_unresolved_in_both_filename_orders(tmp_path):
    from sc_referee.code_signals import parse_code_signals, resolve_unit_of_test

    for marker_name, sample_name in (("a_old_markers.R", "z_final_deseq.R"),
                                     ("z_old_markers.R", "a_final_deseq.R")):
        for old in tmp_path.glob("*.R"):
            old.unlink()
        (tmp_path / marker_name).write_text("x <- FindMarkers(obj, ident.1='A')\n")
        (tmp_path / sample_name).write_text("dds <- DESeqDataSetFromMatrix(counts, meta, ~ condition)\n")
        signals = parse_code_signals(tmp_path)
        assert resolve_unit_of_test(signals) is None
