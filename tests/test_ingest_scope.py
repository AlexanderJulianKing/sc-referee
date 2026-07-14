"""Fast-follow #53: data-gen / test scaffolding .py files must not be ingested as analysis sources.
An unrelated script that also writes the reported paths (or uses a dynamic path) otherwise fails the
producer scoper closed and silently degrades real catches to NOT CHECKED."""


def test_parse_code_signals_excludes_scaffolding(tmp_path):
    from sc_referee.code_signals import parse_code_signals
    (tmp_path / "analysis.py").write_text(
        "import scanpy as sc\nsc.tl.rank_genes_groups(adata, 'ct')\n")
    (tmp_path / "make_data.py").write_text(
        "import pandas as pd\npd.DataFrame().to_csv('results/de.csv')\n")
    (tmp_path / "conftest.py").write_text("import pytest\n")
    (tmp_path / "test_analysis.py").write_text("def test_x(): pass\n")

    cs = parse_code_signals(tmp_path)
    assert "analysis.py" in cs["files"]
    assert "make_data.py" not in cs["files"]
    assert "conftest.py" not in cs["files"]
    assert "test_analysis.py" not in cs["files"]
    assert not any("make_data" in s or "def test_x" in s for s in cs["sources"] if s)
