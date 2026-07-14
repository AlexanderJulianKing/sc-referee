"""CSV ingest cell-id integrity — two pre-existing silent-scope holes.

`read_csv` did `obs.reindex(counts_df.index)` with only a "counts cell missing from obs" guard:
  - a DUPLICATE cell_id in the counts matrix silently double-counts that cell (reindex duplicates the
    obs row) — inflating n and biasing every downstream test;
  - obs rows for cells ABSENT from the matrix are silently dropped, so a GLOBAL metadata table over a
    single-sample matrix quietly audits one sample as if it were the whole study.
Both must refuse, not reindex over the problem.
"""
import numpy as np
import pandas as pd
import pytest


def _counts(folder, cells, genes=("g0", "g1", "g2")):
    df = pd.DataFrame(np.arange(len(cells) * len(genes)).reshape(len(cells), len(genes)) + 1,
                      index=list(cells), columns=list(genes))
    df.index.name = "cell_id"
    df.to_csv(folder / "counts.csv")


def _obs(folder, cells):
    n = len(cells)
    pd.DataFrame({"cell_id": list(cells),
                  "donor_id": [f"D{i % 2}" for i in range(n)],
                  "condition": (["a", "b"] * n)[:n]}).set_index("cell_id").to_csv(folder / "obs.csv")


def test_duplicate_cell_ids_in_counts_refuse(tmp_path):
    from sc_referee.adapters.csv_adapter import read_csv

    _counts(tmp_path, ["c0", "c1", "c1", "c2"])           # c1 duplicated
    _obs(tmp_path, ["c0", "c1", "c2"])
    with pytest.raises(ValueError) as e:
        read_csv(tmp_path)
    assert "duplicate" in str(e.value).lower() and "c1" in str(e.value)


def test_obs_with_extra_cells_refuse(tmp_path):
    from sc_referee.adapters.csv_adapter import read_csv

    _counts(tmp_path, ["c0", "c1"])                       # matrix has 2 cells
    _obs(tmp_path, ["c0", "c1", "c2", "c3", "c4", "c5"])  # metadata describes 6 (a global table)
    with pytest.raises(ValueError) as e:
        read_csv(tmp_path)
    msg = str(e.value).lower()
    assert "absent" in msg or "subset" in msg or "not" in msg


def test_exact_match_still_reads(tmp_path):
    from sc_referee.adapters.csv_adapter import read_csv

    _counts(tmp_path, ["c0", "c1", "c2", "c3"])
    _obs(tmp_path, ["c0", "c1", "c2", "c3"])
    b = read_csv(tmp_path)                                # the guards must not over-trigger
    assert b.observations.shape[0] == 4
    assert b.measure.counts.shape == (4, 3)


def test_transposed_genes_by_cells_csv_refuses(tmp_path):
    import pytest

    from sc_referee.adapters.csv_adapter import bundle_from_csv_files
    df = pd.DataFrame(np.arange(6).reshape(3, 2) + 1, index=["ENSG001", "ENSG002", "ENSG003"],
                      columns=["cellA", "cellB"])                      # genes down the rows -> transposed
    df.index.name = "gene"
    df.to_csv(tmp_path / "counts.csv")
    with pytest.raises(ValueError) as e:
        bundle_from_csv_files(tmp_path / "counts.csv")
    m = str(e.value).lower()
    assert "transpose" in m or "gene ids" in m or "cell-id" in m or "cell_id" in m   # genes-row header refused


def test_duplicate_gene_header_refuses_despite_pandas_mangling(tmp_path):
    import pytest

    from sc_referee.adapters.csv_adapter import bundle_from_csv_files
    (tmp_path / "counts.csv").write_text("cell_id,g0,g0,g2\nc0,1,2,3\nc1,4,5,6\n")   # dup g0 header
    with pytest.raises(ValueError) as e:
        bundle_from_csv_files(tmp_path / "counts.csv")
    assert "duplicate gene" in str(e.value).lower()


def test_duplicate_gene_header_with_quotes_refuses(tmp_path):
    import pytest

    from sc_referee.adapters.csv_adapter import bundle_from_csv_files
    (tmp_path / "counts.csv").write_text('cell_id,"g0",g0\nc0,1,2\nc1,3,4\n')   # "g0" and g0 -> dup
    with pytest.raises(ValueError) as e:
        bundle_from_csv_files(tmp_path / "counts.csv")
    assert "duplicate gene" in str(e.value).lower()


def test_numeric_cell_ids_keep_leading_zeros_as_strings(tmp_path):
    from sc_referee.adapters.csv_adapter import bundle_from_csv_files
    (tmp_path / "counts.csv").write_text("cell_id,g0,g1\n001,1,2\n002,3,4\n")
    b = bundle_from_csv_files(tmp_path / "counts.csv")
    assert list(b.observations.index) == ["001", "002"]          # not collapsed to int 1,2
    assert b.measure.counts.tolist() == [[1, 2], [3, 4]]


def test_csv_without_a_cell_id_column_refuses(tmp_path):
    import pytest

    from sc_referee.adapters.csv_adapter import bundle_from_csv_files
    (tmp_path / "counts.csv").write_text("g0,g1,g2\n1,2,3\n4,5,6\n")   # first header is a gene, no cell_id
    with pytest.raises(ValueError) as e:
        bundle_from_csv_files(tmp_path / "counts.csv")
    assert "cell-id" in str(e.value).lower() or "cell_id" in str(e.value).lower()


def test_bom_header_keeps_numeric_ids_as_strings(tmp_path):
    from sc_referee.adapters.csv_adapter import bundle_from_csv_files
    (tmp_path / "counts.csv").write_bytes("﻿cell_id,g0,g1\n001,1,2\n002,3,4\n".encode("utf-8"))
    b = bundle_from_csv_files(tmp_path / "counts.csv")
    assert list(b.observations.index) == ["001", "002"]              # BOM + leading zeros survive


def test_missing_declared_obs_join_key_refuses(tmp_path):
    import pytest

    from sc_referee.adapters.csv_adapter import bundle_from_csv_files
    (tmp_path / "counts.csv").write_text("cell_id,g0,g1\na,1,2\nb,3,4\n")
    (tmp_path / "obs.csv").write_text("cell_id,condition\na,WT\nb,KO\n")
    with pytest.raises(ValueError) as e:
        bundle_from_csv_files(tmp_path / "counts.csv", tmp_path / "obs.csv", obs_join_on="barcode")
    assert "join key" in str(e.value).lower() or "barcode" in str(e.value)


def test_cell_id_header_accepts_spaced_and_hyphenated_labels(tmp_path):
    from sc_referee.adapters.csv_adapter import bundle_from_csv_files
    for hdr in ("Cell ID", "cell-barcode", "barcode_id"):        # all valid cell-id labels -> no refuse
        (tmp_path / "counts.csv").write_text(f"{hdr},g0,g1\nc0,1,2\nc1,3,4\n")
        b = bundle_from_csv_files(tmp_path / "counts.csv")
        assert list(b.observations.index) == ["c0", "c1"], hdr


@pytest.mark.parametrize("payload", [b"", b"\xffcell_id,g0\nc0,1\n"])
def test_empty_or_non_utf8_counts_are_typed_ingest_errors(tmp_path, payload):
    from sc_referee.ingest import IngestError, ingest

    (tmp_path / "counts.csv").write_bytes(payload)
    _obs(tmp_path, ["c0"])
    with pytest.raises(IngestError) as exc:
        ingest(tmp_path)
    assert "counts.csv" in str(exc.value)


def test_nonnumeric_count_cell_is_a_typed_ingest_error(tmp_path):
    from sc_referee.ingest import IngestError, ingest

    (tmp_path / "counts.csv").write_text("cell_id,g0,g1\nc0,1,oops\nc1,2,3\n")
    _obs(tmp_path, ["c0", "c1"])
    with pytest.raises(IngestError) as exc:
        ingest(tmp_path)
    assert "counts.csv" in str(exc.value) and "numeric" in str(exc.value).lower()


def test_duplicate_metadata_header_refuses_before_pandas_mangling(tmp_path):
    from sc_referee.ingest import IngestError, ingest

    _counts(tmp_path, ["c0", "c1"])
    (tmp_path / "obs.csv").write_text(
        "cell_id,condition,condition\nc0,ctrl,stim\nc1,stim,ctrl\n")
    with pytest.raises(IngestError) as exc:
        ingest(tmp_path)
    assert "condition" in str(exc.value) and "duplicate" in str(exc.value).lower()


def test_cli_malformed_counts_exits_2_without_writing_a_report(tmp_path):
    from typer.testing import CliRunner
    from sc_referee.cli import app

    (tmp_path / "counts.csv").write_text("cell_id,g0\nc0,oops\n")
    _obs(tmp_path, ["c0"])
    report = tmp_path / "report.json"
    result = CliRunner().invoke(
        app, ["audit", str(tmp_path), "--engine", "simple", "--json", str(report)])
    assert result.exit_code == 2
    assert "cannot audit" in result.stdout.lower() and "traceback" not in result.stdout.lower()
    assert not report.exists()
