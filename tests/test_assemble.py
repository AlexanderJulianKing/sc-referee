"""The multi-file assembler — deterministic, verified-not-trusted (spec v2 §6).

Increment 1: row-bind h5ad shards into ONE canonical Bundle, materializing each shard's `constants`
as obs columns (so 'one file per mouse' becomes a real `mouse_id` column — the whole point), prefixing
cell-ids by sample so they stay globally unique, aligning the gene axis (require_identical), and
enforcing the `expected.sample_ids` completeness invariant. The Bundle out is byte-identical in shape
to what every check already consumes.
"""
import anndata as ad
import numpy as np
import pandas as pd
import pytest

from sc_referee.adapters.assemble import assemble
from sc_referee.ingest import IngestError
from sc_referee.manifest import Manifest, Shard


def _shard(path, cells, genes=("g0", "g1", "g2"), seed=0):
    rng = np.random.default_rng(seed)
    X = rng.poisson(5, size=(len(cells), len(genes))).astype(float)
    a = ad.AnnData(X=X, obs=pd.DataFrame(index=list(cells)), var=pd.DataFrame(index=list(genes)))
    a.write_h5ad(path)


def _shard_with_obs(path, obs, genes=("g0", "g1", "g2"), seed=0):
    X = np.random.default_rng(seed).poisson(5, size=(len(obs), len(genes))).astype(float)
    ad.AnnData(X=X, obs=obs, var=pd.DataFrame(index=list(genes))).write_h5ad(path)


def _normalized_shard(path, cells, genes=("p0", "p1", "p2")):
    X = np.log1p(np.random.default_rng(0).poisson(5, size=(len(cells), len(genes))).astype(float))
    ad.AnnData(X=X, obs=pd.DataFrame(index=list(cells)),
               var=pd.DataFrame(index=list(genes))).write_h5ad(path)


def _man(**kw):
    kw.setdefault("expected_sample_ids", ["M1", "M2"])
    shards = [
        Shard(path="M1.h5ad", constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
    ]
    return Manifest(shards=shards, **kw)


def test_assemble_row_binds_and_materializes_constants(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"], seed=1)
    _shard(tmp_path / "M2.h5ad", ["a", "b", "c"], seed=2)     # note: 'a','b' reused across shards

    b = assemble(_man(), tmp_path)

    assert b.measure.kind == "counts"
    assert b.measure.counts.shape == (5, 3)                    # 2 + 3 cells, 3 genes
    assert b.measure.feature_index == ["g0", "g1", "g2"]
    # the file identity is now a real obs column — pseudoreplication becomes visible
    assert list(b.observations["mouse_id"]) == ["M1", "M1", "M2", "M2", "M2"]
    assert list(b.observations["condition"]) == ["WT", "WT", "KO", "KO", "KO"]
    # cell-ids prefixed by sample -> globally unique despite the reused 'a'/'b' barcodes
    assert list(b.observations.index) == ["M1:a", "M1:b", "M2:a", "M2:b", "M2:c"]


def test_assemble_refuses_a_missing_shard_against_expected(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    man = _man(expected_sample_ids=["M1", "M2", "M3"])         # M3 declared but absent
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "expected" in str(e.value).lower()


def test_assemble_refuses_mismatched_gene_sets(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"], genes=("g0", "g1", "g2"))
    _shard(tmp_path / "M2.h5ad", ["a", "b"], genes=("g0", "g1", "gX"))   # gX != g2
    with pytest.raises(IngestError) as e:
        assemble(_man(), tmp_path)
    assert "gene" in str(e.value).lower()


def test_assemble_refuses_a_normalized_shard(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    # a log-normalized second shard (non-integer) must not silently join
    X = np.log1p(np.random.default_rng(0).poisson(5, size=(2, 3)).astype(float))
    ad.AnnData(X=X, obs=pd.DataFrame(index=["a", "b"]),
               var=pd.DataFrame(index=["g0", "g1", "g2"])).write_h5ad(tmp_path / "M2.h5ad")
    with pytest.raises(IngestError) as e:
        assemble(_man(), tmp_path)
    assert "count" in str(e.value).lower()


def test_constants_disagreeing_with_an_embedded_column_refuse(tmp_path):
    # M1's own obs says its cells are a ctrl/stim mix, but the manifest constant claims WT for all.
    _shard_with_obs(tmp_path / "M1.h5ad", pd.DataFrame({"condition": ["ctrl", "stim"]}, index=["a", "b"]))
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    with pytest.raises(IngestError) as e:
        assemble(_man(), tmp_path)
    msg = str(e.value).lower()
    assert "condition" in msg and ("disagree" in msg or "overwrite" in msg or "conflict" in msg)


def test_constants_matching_an_embedded_column_are_allowed(tmp_path):
    # embedded condition already equals the constant -> redundant but harmless, no refuse.
    _shard_with_obs(tmp_path / "M1.h5ad", pd.DataFrame({"condition": ["WT", "WT"]}, index=["a", "b"]))
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    b = assemble(_man(), tmp_path)
    assert list(b.observations["condition"])[:2] == ["WT", "WT"]


def test_non_rna_shard_is_dropped_before_the_count_type_check(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    _normalized_shard(tmp_path / "M1_adt.h5ad", ["a", "b"])   # ADT, non-integer: must be DROPPED
    man = Manifest(shards=[
        Shard(path="M1.h5ad", constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
        Shard(path="M1_adt.h5ad", modality="ADT", constants={"sample_id": "M1"}),
    ], expected_sample_ids=["M1", "M2"])
    b = assemble(man, tmp_path)                               # does NOT refuse on the ADT being normalized
    assert b.measure.counts.shape == (4, 3)                   # only the two RNA shards


def test_all_non_rna_refuses(tmp_path):
    _normalized_shard(tmp_path / "M1_adt.h5ad", ["a", "b"])
    man = Manifest(shards=[Shard(path="M1_adt.h5ad", modality="ADT",
                                 constants={"sample_id": "M1"})], expected_sample_ids=["M1"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "rna" in str(e.value).lower()


def test_declared_transpose_refuses(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    man = Manifest(shards=[
        Shard(path="M1.h5ad", orientation="genes_x_cells",
              constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
    ], expected_sample_ids=["M1", "M2"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "orientation" in str(e.value).lower() or "cells_x_genes" in str(e.value)


def test_shard_path_outside_root_refuses(tmp_path):
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    man = Manifest(shards=[
        Shard(path="../evil.h5ad", constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
    ], expected_sample_ids=["M1", "M2"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "outside" in str(e.value).lower() or "root" in str(e.value).lower() or ".." in str(e.value)


def test_sha256_mismatch_refuses(tmp_path):
    # a shard whose bytes changed since the manifest declared its hash -> refuse (byte-drift guard)
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    man = Manifest(shards=[
        Shard(path="M1.h5ad", sha256="0" * 64,
              constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
    ], expected_sample_ids=["M1", "M2"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "sha256" in str(e.value).lower() or "changed" in str(e.value).lower()


def test_correct_sha256_is_accepted(tmp_path):
    import hashlib

    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    h = hashlib.sha256((tmp_path / "M1.h5ad").read_bytes()).hexdigest()
    man = Manifest(shards=[
        Shard(path="M1.h5ad", sha256=h,
              constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
    ], expected_sample_ids=["M1", "M2"])
    b = assemble(man, tmp_path)                    # matching hash -> no refuse
    assert b.measure.counts.shape == (4, 3)


def test_assemble_csv_shards_with_per_shard_obs(tmp_path):
    # "2 treatments, 2 CSVs": each shard a counts CSV + its own obs carrying donor_id.
    for sid in ("ctrl", "stim"):
        df = pd.DataFrame(np.arange(6).reshape(2, 3) + 1, index=[f"{sid}_a", f"{sid}_b"],
                          columns=["g0", "g1", "g2"])
        df.index.name = "cell_id"
        df.to_csv(tmp_path / f"counts_{sid}.csv")
        pd.DataFrame({"cell_id": [f"{sid}_a", f"{sid}_b"],
                      "donor_id": [f"D_{sid}_1", f"D_{sid}_2"]}).set_index("cell_id").to_csv(tmp_path / f"obs_{sid}.csv")
    man = Manifest(shards=[
        Shard(path="counts_ctrl.csv", format="csv", constants={"sample_id": "ctrl", "condition": "ctrl"},
              obs_path="obs_ctrl.csv"),
        Shard(path="counts_stim.csv", format="csv", constants={"sample_id": "stim", "condition": "stim"},
              obs_path="obs_stim.csv"),
    ], expected_sample_ids=["ctrl", "stim"])
    b = assemble(man, tmp_path)
    assert b.measure.counts.shape == (4, 3)
    assert list(b.observations["condition"]) == ["ctrl", "ctrl", "stim", "stim"]
    assert list(b.observations["donor_id"]) == ["D_ctrl_1", "D_ctrl_2", "D_stim_1", "D_stim_2"]  # per-shard obs joined
    assert list(b.observations.index) == ["ctrl:ctrl_a", "ctrl:ctrl_b", "stim:stim_a", "stim:stim_b"]


def test_assemble_intersect_keeps_only_shared_genes(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"], genes=("g0", "g1", "g2"))
    _shard(tmp_path / "M2.h5ad", ["a", "b"], genes=("g1", "g2", "g3"))   # shares g1, g2
    man = Manifest(shards=[
        Shard(path="M1.h5ad", constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
    ], expected_sample_ids=["M1", "M2"], gene_axis="intersect")
    b = assemble(man, tmp_path)
    assert b.measure.feature_index == ["g1", "g2"]        # intersection, in the first shard's order
    assert b.measure.counts.shape == (4, 2)


def test_assemble_intersect_refuses_when_no_genes_are_shared(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"], genes=("g0", "g1"))
    _shard(tmp_path / "M2.h5ad", ["a", "b"], genes=("gX", "gY"))
    man = Manifest(shards=[
        Shard(path="M1.h5ad", constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
    ], expected_sample_ids=["M1", "M2"], gene_axis="intersect")
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "share no genes" in str(e.value).lower() or "no common" in str(e.value).lower()


def test_duplicate_feature_ids_refuse(tmp_path):
    X = np.random.default_rng(0).poisson(5, size=(2, 3)).astype(float)
    ad.AnnData(X=X, obs=pd.DataFrame(index=["a", "b"]),
               var=pd.DataFrame(index=["g0", "g0", "g2"])).write_h5ad(tmp_path / "M1.h5ad")   # dup g0
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    with pytest.raises(IngestError) as e:
        assemble(_man(), tmp_path)
    assert "duplicate" in str(e.value).lower() and "g0" in str(e.value)


def test_duplicate_sample_ids_refuse(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    _shard(tmp_path / "M2.h5ad", ["c", "d"])                      # disjoint barcodes -> no collision to catch it
    man = Manifest(shards=[
        Shard(path="M1.h5ad", constants={"sample_id": "S", "mouse_id": "S", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "S", "mouse_id": "S", "condition": "KO"}),
    ], expected_sample_ids=["S", "S"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "duplicate sample_id" in str(e.value).lower()


def test_exhaustive_refuses_an_unlisted_matrix(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    _shard(tmp_path / "atlas.h5ad", ["a", "b"])                  # on disk, not in the manifest
    with pytest.raises(IngestError) as e:
        assemble(_man(), tmp_path)
    assert "exhaustive" in str(e.value).lower() and "atlas.h5ad" in str(e.value)


def test_read_anndata_raw_uses_raw_var_names(tmp_path):
    from sc_referee.adapters.anndata_adapter import read_anndata
    raw = ad.AnnData(X=np.random.default_rng(0).poisson(5, size=(2, 4)).astype(float),
                     var=pd.DataFrame(index=["g0", "g1", "g2", "g3"]))
    a = ad.AnnData(X=np.random.default_rng(1).poisson(5, size=(2, 2)).astype(float),
                   obs=pd.DataFrame(index=["a", "b"]), var=pd.DataFrame(index=["g0", "g1"]))
    a.raw = raw
    a.write_h5ad(tmp_path / "x.h5ad")
    with pytest.raises(ValueError, match="multiple differing raw-count matrices"):
        read_anndata(tmp_path / "x.h5ad")
    b = read_anndata(tmp_path / "x.h5ad", layer="raw.X")       # explicit authority keeps raw names
    assert b.measure.feature_index == ["g0", "g1", "g2", "g3"]
    assert b.measure.counts.shape == (2, 4)


def test_read_anndata_honors_declared_layer(tmp_path):
    from sc_referee.adapters.anndata_adapter import read_anndata
    a = ad.AnnData(X=np.log1p(np.random.default_rng(0).poisson(5, size=(2, 3)).astype(float)),  # X normalized
                   obs=pd.DataFrame(index=["a", "b"]), var=pd.DataFrame(index=["g0", "g1", "g2"]))
    a.layers["raw_counts"] = np.random.default_rng(1).poisson(5, size=(2, 3)).astype(float)     # integer layer
    a.write_h5ad(tmp_path / "x.h5ad")
    assert read_anndata(tmp_path / "x.h5ad").measure.kind == "counts"       # unique raw internal candidate
    assert read_anndata(tmp_path / "x.h5ad", layer="layers/raw_counts").measure.kind == "counts"  # honored


def test_csv_shard_obs_joins_on_the_declared_key(tmp_path):
    df = pd.DataFrame(np.arange(4).reshape(2, 2) + 1, index=["a", "b"], columns=["g0", "g1"])
    df.index.name = "cell_id"
    df.to_csv(tmp_path / "counts_s1.csv")
    # obs's FIRST column is junk; the real key is `barcode` -> join must use barcode, not col 0
    pd.DataFrame({"junk": ["z", "y"], "barcode": ["a", "b"], "celltype": ["T", "B"]}).to_csv(
        tmp_path / "obs_s1.csv", index=False)
    man = Manifest(shards=[Shard(path="counts_s1.csv", format="csv", obs_path="obs_s1.csv",
                                 obs_join_on="barcode", constants={"sample_id": "s1", "condition": "WT"})],
                   expected_sample_ids=["s1"])
    b = assemble(man, tmp_path)
    assert list(b.observations["celltype"]) == ["T", "B"]        # aligned via barcode
    assert list(b.observations.index) == ["s1:a", "s1:b"]


def test_h5ad_shard_with_a_per_shard_obs_file_refuses(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    man = Manifest(shards=[
        Shard(path="M1.h5ad", obs_path="stray.csv",
              constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
    ], expected_sample_ids=["M1", "M2"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "per-shard obs" in str(e.value).lower() or "embedded" in str(e.value).lower()


def test_duplicate_shard_paths_refuse(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    man = Manifest(shards=[
        Shard(path="M1.h5ad", constants={"sample_id": "S1", "mouse_id": "S1", "condition": "WT"}),
        Shard(path="M1.h5ad", constants={"sample_id": "S2", "mouse_id": "S2", "condition": "KO"}),  # same file
    ], expected_sample_ids=["S1", "S2"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "duplicate shard path" in str(e.value).lower()


def test_oddly_named_csv_shard_refuses(tmp_path):
    df = pd.DataFrame(np.arange(4).reshape(2, 2) + 1, index=["a", "b"], columns=["g0", "g1"])
    df.index.name = "cell_id"
    df.to_csv(tmp_path / "sample_A.csv")                          # not counts*/matrix* -> undiscoverable
    man = Manifest(shards=[Shard(path="sample_A.csv", format="csv",
                                 constants={"sample_id": "A", "condition": "WT"})],
                   expected_sample_ids=["A"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "counts*" in str(e.value) or "named" in str(e.value).lower()


def test_aliased_shard_paths_refuse(tmp_path):
    _shard(tmp_path / "M1.h5ad", ["a", "b"])
    man = Manifest(shards=[
        Shard(path="M1.h5ad", constants={"sample_id": "S1", "mouse_id": "S1", "condition": "WT"}),
        Shard(path="./M1.h5ad", constants={"sample_id": "S2", "mouse_id": "S2", "condition": "KO"}),  # alias
    ], expected_sample_ids=["S1", "S2"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "duplicate shard path" in str(e.value).lower()


def test_shard_nested_more_than_one_level_refuses(tmp_path):
    (tmp_path / "a" / "b").mkdir(parents=True)
    _shard(tmp_path / "a" / "b" / "M1.h5ad", ["a", "b"])
    _shard(tmp_path / "M2.h5ad", ["a", "b"])
    man = Manifest(shards=[
        Shard(path="a/b/M1.h5ad", constants={"sample_id": "M1", "mouse_id": "M1", "condition": "WT"}),
        Shard(path="M2.h5ad", constants={"sample_id": "M2", "mouse_id": "M2", "condition": "KO"}),
    ], expected_sample_ids=["M1", "M2"])
    with pytest.raises(IngestError) as e:
        assemble(man, tmp_path)
    assert "subdirectory" in str(e.value).lower() or "deep" in str(e.value).lower()
