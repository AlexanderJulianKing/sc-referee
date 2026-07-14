"""parse_code_signals must find analysis code wherever it lives in the bundle tree."""

from sc_referee.code_signals import parse_code_signals


def test_parse_code_signals_finds_deeply_nested_script(tmp_path):
    """adversarial-review finding 11: the audit-path scanner only looked one directory deep, so a script under
    scripts/steps/ was invisible -> a false-clean. It must recurse (with sane exclusions)."""
    nested = tmp_path / "scripts" / "steps"
    nested.mkdir(parents=True)
    (nested / "03_cluster_and_markers.py").write_text(
        "import scanpy as sc\nsc.tl.leiden(adata)\nsc.tl.rank_genes_groups(adata, groupby='leiden')\n")
    cs = parse_code_signals(tmp_path)
    assert "leiden" in cs["cluster_calls"]
    assert any("rank_genes_groups" in s for s in cs["sources"])


def test_single_seurat_findmarkers_call_exposes_narrow_design_contract(tmp_path):
    (tmp_path / "analysis.R").write_text("""
library(Seurat)
Idents(seu) <- seu$organ
markers <- FindMarkers(
  seu,
  ident.1 = "Brain",
  ident.2 = "Peripheral",
  test.use = "MAST",
  max.cells.per.ident = min(table(seu$organ))
)
""")

    signals = parse_code_signals(tmp_path)

    assert signals["seurat_findmarkers"] == {
        "ident_1": "Brain",
        "ident_2": "Peripheral",
        "latent_vars": [],
        "identity_column": "organ",
    }


def test_findmarkers_latent_vars_are_parsed_but_ambiguous_multiple_calls_abstain(tmp_path):
    script = tmp_path / "analysis.R"
    script.write_text("""
Idents(seu) <- seu$organ
FindMarkers(seu, ident.1='Brain', ident.2='Peripheral', latent.vars=c('run', 'sex'))
""")
    assert parse_code_signals(tmp_path)["seurat_findmarkers"]["latent_vars"] == ["run", "sex"]

    script.write_text(script.read_text() +
                      "\nFindMarkers(seu, ident.1='A', ident.2='B')\n")
    assert parse_code_signals(tmp_path)["seurat_findmarkers"] is None


def test_parse_code_signals_skips_virtualenv_and_caches(tmp_path):
    """Recursion must not wander into .venv / __pycache__ / node_modules etc."""
    from sc_referee.code_signals import parse_code_signals
    (tmp_path / "01_real.py").write_text("import scanpy as sc\nsc.tl.leiden(adata)\n")
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "junk.py").write_text("import scanpy as sc\nsc.tl.louvain(adata)\n")
    cs = parse_code_signals(tmp_path)
    assert "leiden" in cs["cluster_calls"]
    assert "louvain" not in cs["cluster_calls"]        # .venv content ignored
