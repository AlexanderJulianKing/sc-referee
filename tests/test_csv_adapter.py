"""Item 1: ingest a CSV/TSV analysis, not just .h5ad.

Convention (explicit filenames — never guess which CSV is which):
  counts.csv / counts.tsv / matrix.csv   — cells x genes, first column = cell_id, header = gene ids
  obs.csv / metadata.csv / cells.csv      — cell metadata (the design): first column = cell_id + columns
  <reported-DE>.csv                        — detected by header, as before

The count matrix and the cell metadata are separate files because raw formats (CSV, 10x mtx) don't
carry the experimental design the way AnnData's .obs does. Same canonical Bundle out either way, so
every downstream check is format-agnostic. Non-integer values reuse item 2 (kind="normalized").
"""
import numpy as np
import pandas as pd
import pytest


def _write_csv_analysis(folder, integer=True, sep=","):
    ext = "csv" if sep == "," else "tsv"
    rng = np.random.default_rng(1)
    cells = [f"c{i}" for i in range(12)]
    genes = [f"g{j}" for j in range(5)]
    vals = rng.poisson(7, size=(12, 5))
    counts = pd.DataFrame(vals if integer else np.log1p(vals.astype(float)), index=cells, columns=genes)
    counts.index.name = "cell_id"
    counts.to_csv(folder / f"counts.{ext}", sep=sep)
    obs = pd.DataFrame({"cell_id": cells,
                        "donor_id": [f"D{i % 4}" for i in range(12)],
                        "condition": ["ctrl"] * 6 + ["stim"] * 6}).set_index("cell_id")
    obs.to_csv(folder / f"obs.{ext}", sep=sep)


def test_read_csv_builds_the_canonical_bundle(tmp_path):
    from sc_referee.adapters.csv_adapter import read_csv

    _write_csv_analysis(tmp_path)
    b = read_csv(tmp_path)
    assert list(b.observations.columns) == ["donor_id", "condition"]
    assert b.observations.shape[0] == 12
    assert b.measure.kind == "counts"
    assert b.measure.counts.shape == (12, 5)
    assert b.measure.feature_index == ["g0", "g1", "g2", "g3", "g4"]
    assert b.replicate_var == "donor_id"


def test_ingest_routes_to_csv_when_no_h5ad(tmp_path):
    from sc_referee.ingest import ingest

    _write_csv_analysis(tmp_path)
    b = ingest(tmp_path)
    assert b.measure.counts.shape == (12, 5)
    assert b.provenance["data"]["path"].endswith("counts.csv")


def test_tsv_is_accepted(tmp_path):
    from sc_referee.ingest import ingest

    _write_csv_analysis(tmp_path, sep="\t")
    b = ingest(tmp_path)
    assert b.measure.counts.shape == (12, 5)
    assert b.replicate_var == "donor_id"


def test_non_integer_csv_matrix_is_normalized_not_refused(tmp_path):
    """Reuses item 2: a non-integer CSV matrix is flagged normalized, counts held as None."""
    from sc_referee.adapters.csv_adapter import read_csv

    _write_csv_analysis(tmp_path, integer=False)
    b = read_csv(tmp_path)
    assert b.measure.kind == "normalized"
    assert b.measure.counts is None
    assert list(b.observations.columns) == ["donor_id", "condition"]   # .obs still usable


def test_no_supported_matrix_errors_with_the_supported_formats(tmp_path):
    from sc_referee.ingest import ingest

    (tmp_path / "readme.txt").write_text("nothing here")
    with pytest.raises(FileNotFoundError) as e:
        ingest(tmp_path)
    msg = str(e.value)
    assert ".h5ad" in msg and "counts.csv" in msg      # names what it accepts
