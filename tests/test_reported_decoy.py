"""Reported-results decoy — a pre-existing silent hole.

`_discover_reported` bound the FIRST CSV whose header looked like DE output. A folder with
`old_results.csv` beside `paper_results.csv` (or a stale rerun) could silently audit the wrong table
and PASS against a decoy. With more than one candidate, bind NONE and record why — the reported-table
checks then abstain honestly, rather than auditing a guess.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml


ORACLES = Path(__file__).parent / "frozen_oracles" / "pipeline_claim_init_oracles.json"


def _analysis(folder):
    cells = [f"c{i}" for i in range(6)]
    df = pd.DataFrame(np.arange(18).reshape(6, 3) + 1, index=cells, columns=["g0", "g1", "g2"])
    df.index.name = "cell_id"
    df.to_csv(folder / "counts.csv")
    pd.DataFrame({"cell_id": cells, "donor_id": ["D0", "D1"] * 3,
                  "condition": ["a", "b"] * 3}).set_index("cell_id").to_csv(folder / "obs.csv")


def _de(folder, name):
    pd.DataFrame({"gene": ["g0", "g1", "g2"], "p_value": [0.01, 0.2, 0.3],
                  "padj": [0.02, 0.3, 0.4], "log2FoldChange": [1.5, 0.1, 0.2]}).to_csv(folder / name, index=False)


def _confirmed_config(folder, reported_path):
    config = {
        "analysis_type": "condition_contrast_DE",
        "confirmed_by_human": True,
        "design": {"condition": "condition", "replicate_unit": ["donor_id"], "batch": []},
        "contrasts": [{
            "name": "b_vs_a", "reference": "a", "test": "b",
            "sample_unit": ["donor_id", "condition"],
        }],
        "reported_results": {"path": reported_path, "unit_of_test": "cell"},
        "confidence": {"condition": "high", "replicate_unit": "high"},
    }
    (folder / "sc-referee.yaml").write_text(yaml.safe_dump(config, sort_keys=False))


def _reported_public_output(bundle):
    frame = bundle.reported_results
    return {
        "reported_results": None if frame is None else {
            column: [None if pd.isna(value) else value for value in frame[column].tolist()]
            for column in frame.columns
        },
        "reported_columns": list(bundle.reported_columns),
        "reported_provenance": bundle.provenance.get("reported"),
    }


def test_single_reported_table_is_still_bound(tmp_path):
    from sc_referee.ingest import ingest

    _analysis(tmp_path)
    _de(tmp_path, "results.csv")
    b = ingest(tmp_path)
    assert b.reported_results is not None
    assert b.provenance["reported"]["path"].endswith("results.csv")

    frozen = json.loads(ORACLES.read_text())["single_table_auto_detect_legacy"]
    assert _reported_public_output(b) == frozen


def test_two_reported_tables_bind_none_not_the_first(tmp_path):
    from sc_referee.ingest import ingest

    _analysis(tmp_path)
    _de(tmp_path, "old_results.csv")
    _de(tmp_path, "paper_results.csv")
    b = ingest(tmp_path)
    assert b.reported_results is None                         # did NOT silently bind a decoy
    note = str(b.provenance.get("reported", {})).lower()
    assert "ambiguous" in note and "old_results.csv" in note and "paper_results.csv" in note


def test_two_reported_tables_bind_the_confirmed_declared_claim(tmp_path):
    """A confirmed claim binding is authoritative; discovery ambiguity must not erase it."""
    from sc_referee.ingest import ingest

    _analysis(tmp_path)
    _de(tmp_path, "de_claim.csv")
    _de(tmp_path, "splicing_summary.csv")
    _confirmed_config(tmp_path, "de_claim.csv")

    bundle = ingest(tmp_path)

    assert bundle.reported_results is not None
    assert bundle.provenance["reported"] == {
        "path": "de_claim.csv",
        "reason": "confirmed sc-referee.yaml declared this reported claim",
    }
    assert list(bundle.reported_results["feature_id"]) == ["g0", "g1", "g2"]

    frozen = json.loads(ORACLES.read_text())["two_tables_confirmed_declared_claim"]
    assert _reported_public_output(bundle) == frozen


@pytest.mark.parametrize("declared,contents,problem", [
    ("missing.csv", None, "does not exist"),
    ("notes.csv", "topic,value\nsplicing,summary\n", "not a reported-DE table"),
])
def test_invalid_confirmed_claim_path_is_a_design_error_not_a_finding(
        tmp_path, declared, contents, problem):
    from sc_referee.design import DesignError
    from sc_referee.ingest import ingest

    _analysis(tmp_path)
    _de(tmp_path, "auto_detectable.csv")
    if contents is not None:
        (tmp_path / declared).write_text(contents)
    _confirmed_config(tmp_path, declared)

    with pytest.raises(DesignError, match=problem):
        ingest(tmp_path)


def test_unconfirmed_claim_declaration_cannot_override_discovery_ambiguity(tmp_path):
    """A model-written proposal is not claim authority until the person confirms it."""
    from sc_referee.ingest import ingest

    _analysis(tmp_path)
    _de(tmp_path, "de_claim.csv")
    _de(tmp_path, "other_claim.csv")
    _confirmed_config(tmp_path, "de_claim.csv")
    config = yaml.safe_load((tmp_path / "sc-referee.yaml").read_text())
    config["confirmed_by_human"] = False
    (tmp_path / "sc-referee.yaml").write_text(yaml.safe_dump(config, sort_keys=False))

    bundle = ingest(tmp_path)
    assert bundle.reported_results is None
    assert "ambiguous" in bundle.provenance["reported"]["reason"].lower()


def test_reported_tsv_is_parsed_with_tabs(tmp_path):
    import anndata as ad

    from sc_referee.ingest import ingest
    ad.AnnData(X=np.arange(6).reshape(2, 3).astype(float),
               obs=pd.DataFrame({"condition": ["a", "b"]}, index=["c0", "c1"]),
               var=pd.DataFrame(index=["g0", "g1", "g2"])).write_h5ad(tmp_path / "data.h5ad")
    (tmp_path / "results.tsv").write_text("gene\tpvalue\tpadj\ng0\t0.01\t0.02\ng1\t0.2\t0.3\n")
    b = ingest(tmp_path)
    assert b.reported_results is not None                         # bound (was missed as comma-CSV)
    assert list(b.reported_results["feature_id"]) == ["g0", "g1"]


def test_deep_confirmed_report_binds_even_when_discovery_finds_zero(tmp_path):
    from sc_referee.ingest import ingest

    _analysis(tmp_path)
    deep = tmp_path / "results" / "final"
    deep.mkdir(parents=True)
    _de(deep, "de.csv")
    _confirmed_config(tmp_path, "results/final/de.csv")
    bundle = ingest(tmp_path)
    assert bundle.provenance["reported"]["path"] == "results/final/de.csv"
    assert bundle.reported_columns == ["gene", "p_value", "padj", "log2FoldChange"]


@pytest.mark.parametrize("confirmed", [False, True])
def test_duplicate_report_header_refuses_before_synonym_binding(tmp_path, confirmed):
    from sc_referee.design import DesignError
    from sc_referee.ingest import IngestError, ingest

    _analysis(tmp_path)
    (tmp_path / "results.csv").write_text(
        "gene,pvalue,padj,padj\ng0,0.01,0.02,0.9\n")
    if confirmed:
        _confirmed_config(tmp_path, "results.csv")
    expected = DesignError if confirmed else IngestError
    with pytest.raises(expected) as exc:
        ingest(tmp_path)
    assert "duplicate" in str(exc.value).lower() and "padj" in str(exc.value)
