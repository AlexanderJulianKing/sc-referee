"""Refuse-on-ambiguity: the flagship pre-existing silent-scope hole.

Today `ingest` takes `h5ads[0]` (the lexicographically-first *.h5ad). A folder with a reference
`atlas.h5ad` beside the experiment's `results.h5ad` silently audits the ATLAS; `ctrl.h5ad` +
`stim.h5ad` silently audits one arm. When >1 candidate matrix exists and no manifest declares how they
assemble, the honest move is to REFUSE, not to guess one — a partial/wrong-scope audit dressed as a
whole-analysis verdict is exactly what the tool must never do.
"""
import anndata as ad
import numpy as np
import pandas as pd
import pytest


def _write_h5ad(path, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.poisson(5, size=(6, 4)).astype(float)
    obs = pd.DataFrame({"donor_id": [f"D{i % 3}" for i in range(6)],
                        "condition": ["a"] * 3 + ["b"] * 3},
                       index=[f"c{i}" for i in range(6)])
    var = pd.DataFrame(index=[f"g{j}" for j in range(4)])
    ad.AnnData(X=X, obs=obs, var=var).write_h5ad(path)


def test_multiple_h5ads_refuse_rather_than_audit_the_first(tmp_path):
    from sc_referee.ingest import IngestError, ingest

    _write_h5ad(tmp_path / "atlas.h5ad", 1)
    _write_h5ad(tmp_path / "results.h5ad", 2)
    with pytest.raises(IngestError) as e:
        ingest(tmp_path)
    msg = str(e.value)
    assert "atlas.h5ad" in msg and "results.h5ad" in msg      # names the candidates
    assert "manifest" in msg.lower() or "init" in msg.lower()  # tells the human what to do


def test_single_h5ad_still_ingests(tmp_path):
    from sc_referee.ingest import ingest

    _write_h5ad(tmp_path / "only.h5ad")
    b = ingest(tmp_path)
    assert b.measure.counts.shape == (6, 4)                    # the guard must not over-trigger


def test_two_named_count_matrices_refuse(tmp_path):
    from sc_referee.ingest import IngestError, ingest

    cells = [f"c{i}" for i in range(6)]
    df = pd.DataFrame(np.arange(24).reshape(6, 4), index=cells, columns=[f"g{j}" for j in range(4)])
    df.index.name = "cell_id"
    df.to_csv(tmp_path / "counts.csv")
    df.to_csv(tmp_path / "matrix.csv")                          # a second candidate -> ambiguous
    pd.DataFrame({"cell_id": cells, "donor_id": ["D0"] * 6,
                 "condition": ["a"] * 3 + ["b"] * 3}).set_index("cell_id").to_csv(tmp_path / "obs.csv")
    with pytest.raises(IngestError):
        ingest(tmp_path)


def test_cli_audit_refuses_ambiguous_folder_with_exit_2(tmp_path):
    from typer.testing import CliRunner

    from sc_referee.cli import app

    _write_h5ad(tmp_path / "atlas.h5ad", 1)
    _write_h5ad(tmp_path / "results.h5ad", 2)
    result = CliRunner().invoke(app, ["audit", str(tmp_path), "--engine", "simple"])
    assert result.exit_code == 2                                # a clean refuse, not a traceback
    assert "candidate data matrices" in result.stdout.lower()


def test_subdir_csv_matrix_triggers_refuse_on_ambiguity(tmp_path):
    from sc_referee.ingest import IngestError, ingest
    (tmp_path / "counts.csv").write_text("cell_id,g0,g1\nc0,1,2\nc1,3,4\n")
    (tmp_path / "obs.csv").write_text("cell_id,condition\nc0,WT\nc1,KO\n")
    (tmp_path / "stim").mkdir()
    (tmp_path / "stim" / "counts.csv").write_text("cell_id,g0,g1\nd0,1,2\n")   # a second, subdir matrix
    with pytest.raises(IngestError) as e:
        ingest(tmp_path)
    assert "candidate data matrices" in str(e.value).lower() and "stim/counts.csv" in str(e.value)


def test_competing_supported_metadata_tables_refuse_and_name_both(tmp_path):
    from sc_referee.ingest import IngestError, ingest

    (tmp_path / "counts.csv").write_text("cell_id,g0\nc0,1\nc1,2\n")
    (tmp_path / "obs.csv").write_text("cell_id,condition\nc0,ctrl\nc1,stim\n")
    (tmp_path / "metadata.csv").write_text("cell_id,condition\nc0,stim\nc1,ctrl\n")
    with pytest.raises(IngestError) as exc:
        ingest(tmp_path)
    msg = str(exc.value)
    assert "obs.csv" in msg and "metadata.csv" in msg


def test_differing_raw_anndata_candidates_refuse_and_name_internal_slots(tmp_path):
    from sc_referee.ingest import IngestError, ingest

    path = tmp_path / "data.h5ad"
    _write_h5ad(path)
    obj = ad.read_h5ad(path)
    obj.layers["counts"] = obj.X + 1
    obj.write_h5ad(path)
    with pytest.raises(IngestError) as exc:
        ingest(tmp_path)
    msg = str(exc.value)
    assert ".X" in msg and "layers[counts]" in msg


def test_unique_raw_x_is_not_suppressed_by_misleading_counts_layer(tmp_path):
    from sc_referee.ingest import ingest

    path = tmp_path / "data.h5ad"
    _write_h5ad(path)
    obj = ad.read_h5ad(path)
    obj.layers["counts"] = np.log1p(obj.X)
    obj.write_h5ad(path)
    bundle = ingest(tmp_path)
    assert bundle.measure.kind == "counts"
    assert bundle.provenance["data"]["matrix_slot"] == ".X"
