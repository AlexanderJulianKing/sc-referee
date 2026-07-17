"""Manifest loading + the ingest wiring that makes multi-file audits real end-to-end.

`load_manifest` parses `sc-referee.manifest.yaml` into the layout model; `ingest` then routes a folder
that HAS a manifest through the deterministic assembler instead of the single-file path — so
`sc-referee audit` on eight-mice-in-eight-files runs the ordinary checks on one assembled matrix.
"""
import anndata as ad
import numpy as np
import pandas as pd
import pytest

from sc_referee.manifest import draft_manifest, load_manifest, write_manifest


def _shard(path, cells, genes=("g0", "g1", "g2"), seed=0):
    X = np.random.default_rng(seed).poisson(5, size=(len(cells), len(genes))).astype(float)
    ad.AnnData(X=X, obs=pd.DataFrame(index=list(cells)),
               var=pd.DataFrame(index=list(genes))).write_h5ad(path)


MANIFEST_YAML = """
manifest_version: 1
confirmed_by_human: true
exhaustive: true
expected: { sample_ids: [M1, M2] }
excluded: [ { path: atlas.h5ad, reason: reference_atlas } ]
assembly: { gene_axis: require_identical, cell_ids: prefix_by_sample_id }
shards:
  - { path: M1.h5ad, format: h5ad, count_type: raw_counts, modality: RNA,
      constants: {sample_id: M1, mouse_id: M1, condition: WT} }
  - { path: M2.h5ad, constants: {sample_id: M2, mouse_id: M2, condition: KO},
      obs: {path: m2_obs.csv, join_on: cell_id} }
"""


def test_load_manifest_parses_shards_and_assembly(tmp_path):
    (tmp_path / "sc-referee.manifest.yaml").write_text(MANIFEST_YAML)
    m = load_manifest(tmp_path / "sc-referee.manifest.yaml")

    assert m.confirmed_by_human is True
    assert m.expected_sample_ids == ["M1", "M2"]
    assert m.gene_axis == "require_identical" and m.cell_ids == "prefix_by_sample_id"
    assert [s.path for s in m.shards] == ["M1.h5ad", "M2.h5ad"]
    assert m.shards[0].constants["condition"] == "WT"
    assert m.shards[1].obs_path == "m2_obs.csv" and m.shards[1].obs_join_on == "cell_id"
    assert m.excluded == [{"path": "atlas.h5ad", "reason": "reference_atlas"}]


def test_ingest_routes_through_the_manifest_when_present(tmp_path):
    from sc_referee.ingest import ingest

    _shard(tmp_path / "M1.h5ad", ["a", "b"], seed=1)
    _shard(tmp_path / "M2.h5ad", ["a", "b", "c"], seed=2)
    # a second candidate matrix that would trip refuse-on-ambiguity IS suppressed by the manifest
    (tmp_path / "sc-referee.manifest.yaml").write_text(
        "manifest_version: 1\nexpected: { sample_ids: [M1, M2] }\n"
        "shards:\n"
        "  - { path: M1.h5ad, constants: {sample_id: M1, mouse_id: M1, condition: WT} }\n"
        "  - { path: M2.h5ad, constants: {sample_id: M2, mouse_id: M2, condition: KO} }\n")

    b = ingest(tmp_path)

    assert list(b.observations["mouse_id"]) == ["M1", "M1", "M2", "M2", "M2"]   # assembled, not one file
    assert b.measure.counts.shape == (5, 3)
    assert list(b.observations.index) == ["M1:a", "M1:b", "M2:a", "M2:b", "M2:c"]
    assert "manifest" in str(b.provenance.get("data", {})).lower()


def test_end_to_end_eight_files_assemble_and_earn_a_confounding_blocker(tmp_path):
    """The payoff: 8 mice in 8 files, WT all in batch B1 and KO all in B2 (condition perfectly aliased
    with batch). The assembler builds one matrix with mouse_id/condition/batch as real columns, and the
    ordinary confounding check earns its power-independent blocker on the assembled design."""
    from sc_referee.checks.confounding import ConfoundingCheck
    from sc_referee.ingest import ingest
    from tests.factories import make_design

    mice = [("M1", "WT", "B1"), ("M2", "WT", "B1"), ("M3", "WT", "B1"), ("M4", "WT", "B1"),
            ("M5", "KO", "B2"), ("M6", "KO", "B2"), ("M7", "KO", "B2"), ("M8", "KO", "B2")]
    lines = []
    for i, (m, cond, b) in enumerate(mice):
        _shard(tmp_path / f"{m}.h5ad", [f"c{j}" for j in range(3)], seed=i)
        lines.append(f"  - {{ path: {m}.h5ad, constants: {{sample_id: {m}, mouse_id: {m}, "
                     f"condition: {cond}, batch: {b}}} }}")
    (tmp_path / "sc-referee.manifest.yaml").write_text(          # unconfirmed draft; the check runs directly
        "manifest_version: 1\n"
        "expected: { sample_ids: [M1, M2, M3, M4, M5, M6, M7, M8] }\n"
        "shards:\n" + "\n".join(lines) + "\n")

    bundle = ingest(tmp_path)
    assert bundle.measure.counts.shape == (24, 3)                       # 8 mice x 3 cells
    assert sorted(set(bundle.observations["mouse_id"])) == [f"M{i}" for i in range(1, 9)]

    design = make_design(condition="condition", batch=["batch"], reference="WT", test="KO",
                         replicate_unit=["mouse_id"], model="~ condition")
    finding = ConfoundingCheck().run(design, bundle)
    assert finding.status == "blocker"
    assert "batch" in finding.verdict.lower() or "aliased" in finding.verdict.lower()


def test_draft_manifest_enumerates_the_shards(tmp_path):
    _shard(tmp_path / "mouse1.h5ad", ["a", "b"])
    _shard(tmp_path / "mouse2.h5ad", ["a", "b"])
    m = draft_manifest(tmp_path)
    assert [s.path for s in m.shards] == ["mouse1.h5ad", "mouse2.h5ad"]
    assert [s.constants["sample_id"] for s in m.shards] == ["mouse1", "mouse2"]   # sample_id from stem
    assert sorted(m.expected_sample_ids) == ["mouse1", "mouse2"]
    assert m.confirmed_by_human is False                                          # never auto-confirmed


def test_draft_manifest_needs_more_than_one_matrix(tmp_path):
    _shard(tmp_path / "only.h5ad", ["a", "b"])
    with pytest.raises(ValueError):
        draft_manifest(tmp_path)          # single-file folders don't need a manifest


def test_draft_then_write_round_trips_through_load(tmp_path):
    _shard(tmp_path / "mouse1.h5ad", ["a", "b"])
    _shard(tmp_path / "mouse2.h5ad", ["a", "b"])
    write_manifest(draft_manifest(tmp_path), tmp_path / "sc-referee.manifest.yaml")
    loaded = load_manifest(tmp_path / "sc-referee.manifest.yaml")
    assert [s.path for s in loaded.shards] == ["mouse1.h5ad", "mouse2.h5ad"]
    assert loaded.expected_sample_ids == ["mouse1", "mouse2"]
    assert loaded.confirmed_by_human is False


def test_cli_init_on_a_multifile_folder_writes_a_manifest_draft(tmp_path):
    from typer.testing import CliRunner

    from sc_referee.cli import app

    _shard(tmp_path / "mouse1.h5ad", ["a", "b"])
    _shard(tmp_path / "mouse2.h5ad", ["a", "b"])
    result = CliRunner().invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "sc-referee.manifest.yaml").exists()
    # The manifest filename is printed inside a long absolute path that the console hard-wraps
    # mid-token at narrow widths; the wrap point depends on the temp-path length (which differs by
    # OS), so normalize whitespace before the substring check rather than depend on the wrap.
    assert "manifest" in "".join(result.stdout.lower().split())
    assert "mouse1.h5ad" in result.stdout and "mouse2.h5ad" in result.stdout


def test_cli_init_on_a_csv_multifile_folder(tmp_path):
    from typer.testing import CliRunner

    from sc_referee.cli import app
    for sid in ("ctrl", "stim"):
        df = pd.DataFrame(np.arange(6).reshape(2, 3) + 1, index=[f"{sid}_a", f"{sid}_b"],
                          columns=["g0", "g1", "g2"])
        df.index.name = "cell_id"
        df.to_csv(tmp_path / f"counts_{sid}.csv")
    result = CliRunner().invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    m = load_manifest(tmp_path / "sc-referee.manifest.yaml")
    assert sorted(s.format for s in m.shards) == ["csv", "csv"]
    assert sorted(s.path for s in m.shards) == ["counts_ctrl.csv", "counts_stim.csv"]


def test_subset_column_absent_from_data_refuses(tmp_path):
    import pytest

    from sc_referee.design import DesignError, validate_design_against
    from tests.factories import make_design
    obs = pd.DataFrame({"condition": ["ctrl", "stim"]}, index=["a", "b"])   # no `cell_type` column
    d = make_design(condition="condition", reference="ctrl", test="stim", subset={"cell_type": "T"})
    with pytest.raises(DesignError) as e:
        validate_design_against(obs, d)                          # would else audit the FULL data
    assert "subset" in str(e.value).lower() and "cell_type" in str(e.value)


def test_manifest_count_shard_is_not_mis_bound_as_reported(tmp_path):
    from sc_referee.ingest import ingest
    df = pd.DataFrame([[1, 2, 3], [4, 5, 6]], index=["a", "b"], columns=["gene", "pvalue", "padj"])
    df.index.name = "cell_id"
    df.to_csv(tmp_path / "counts_s1.csv")                         # gene columns look like a DE table
    (tmp_path / "sc-referee.manifest.yaml").write_text(
        "manifest_version: 1\nexpected: { sample_ids: [counts_s1] }\n"
        "shards:\n  - { path: counts_s1.csv, format: csv, constants: {sample_id: counts_s1, condition: WT} }\n")
    b = ingest(tmp_path)
    assert b.reported_results is None                            # the count shard was NOT bound as results


def test_nonexhaustive_unconfirmed_manifest_cannot_hide_an_undeclared_matrix(tmp_path):
    from sc_referee.ingest import IngestError, ingest

    _shard(tmp_path / "declared.h5ad", ["g0", "g1"])
    _shard(tmp_path / "real.h5ad", ["g0", "g1"])
    (tmp_path / "sc-referee.manifest.yaml").write_text(
        "manifest_version: 1\nconfirmed_by_human: false\nexhaustive: false\nshards:\n"
        "  - {path: declared.h5ad, constants: {sample_id: decoy}}\n")
    with pytest.raises(IngestError) as exc:
        ingest(tmp_path)
    assert "real.h5ad" in str(exc.value)


def test_case_mismatched_manifest_modality_refuses_instead_of_dropping(tmp_path):
    from sc_referee.ingest import IngestError, ingest

    _shard(tmp_path / "a.h5ad", ["g0", "g1"])
    _shard(tmp_path / "b.h5ad", ["g0", "g1"])
    (tmp_path / "sc-referee.manifest.yaml").write_text(
        "manifest_version: 1\nshards:\n"
        "  - {path: a.h5ad, modality: RNA, constants: {sample_id: a}}\n"
        "  - {path: b.h5ad, modality: rna, constants: {sample_id: b}}\n")
    with pytest.raises(IngestError) as exc:
        ingest(tmp_path)
    assert "rna" in str(exc.value) and "modality" in str(exc.value).lower()


def test_valid_non_rna_shard_is_explicitly_accounted_as_excluded(tmp_path):
    from sc_referee.ingest import ingest

    _shard(tmp_path / "rna.h5ad", ["c0", "c1"])
    _shard(tmp_path / "adt.h5ad", ["a0", "a1"])
    (tmp_path / "sc-referee.manifest.yaml").write_text(
        "manifest_version: 1\nshards:\n"
        "  - {path: rna.h5ad, modality: RNA, constants: {sample_id: rna}}\n"
        "  - {path: adt.h5ad, modality: ADT, constants: {sample_id: adt}}\n")
    bundle = ingest(tmp_path)
    accounting = bundle.provenance["manifest"]["shards"]
    assert {item["path"]: item["disposition"] for item in accounting} == {
        "rna.h5ad": "included_in_rna", "adt.h5ad": "excluded_non_rna",
    }
