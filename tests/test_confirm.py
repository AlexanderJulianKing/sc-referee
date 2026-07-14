"""One-confirm-that-re-derives (spec v2 §10).

`sc-referee confirm <folder>` re-assembles from the (possibly hand-edited) manifest, re-validates the
design against that fresh assembly, records each shard's sha256, and only then flips BOTH
`confirmed_by_human` flags. If a manifest edit made the layout un-assemblable or the design no longer
fit, confirm REFUSES — closing the stale-proposal hazard while keeping a single human gate.
"""
import anndata as ad
import numpy as np
import pandas as pd
import pytest
import yaml
from typer.testing import CliRunner

from sc_referee.cli import app
from sc_referee.manifest import load_manifest

DESIGN_YAML = """analysis_type: condition_contrast_DE
confirmed_by_human: false
design:
  replicate_unit: [mouse_id]
  condition: condition
  batch: []
contrasts:
- name: KO_vs_WT
  reference: WT
  test: KO
  replicate_unit: [mouse_id]
  sample_unit: [mouse_id]
  pairing_unit: []
  model: ~ condition
  target_coefficient: condition[T.KO]
confidence: {replicate_unit: high, condition: high}
unresolved: []
"""


def _shard(path, genes=("g0", "g1", "g2"), seed=0):
    X = np.random.default_rng(seed).poisson(5, size=(3, len(genes))).astype(float)
    ad.AnnData(X=X, obs=pd.DataFrame(index=["a", "b", "c"]),
               var=pd.DataFrame(index=list(genes))).write_h5ad(path)


def _setup(folder, drop_condition=False, gene_mismatch=False):
    mice = [("M1", "WT"), ("M2", "KO")]
    lines = []
    for i, (sid, cond) in enumerate(mice):
        genes = ("g0", "g1", "gX") if (gene_mismatch and i == 1) else ("g0", "g1", "g2")
        _shard(folder / f"{sid}.h5ad", genes=genes, seed=i)
        const = {"sample_id": sid, "mouse_id": sid}
        if not drop_condition:
            const["condition"] = cond
        pairs = ", ".join(f"{k}: {v}" for k, v in const.items())
        lines.append(f"  - {{ path: {sid}.h5ad, constants: {{{pairs}}} }}")
    (folder / "sc-referee.manifest.yaml").write_text(
        "manifest_version: 1\nconfirmed_by_human: false\n"
        "expected: { sample_ids: [M1, M2] }\nshards:\n" + "\n".join(lines) + "\n")
    (folder / "sc-referee.yaml").write_text(DESIGN_YAML)


def _confirmed(path):
    return yaml.safe_load(path.read_text())["confirmed_by_human"]


def test_confirm_flips_both_flags_and_records_hashes(tmp_path):
    _setup(tmp_path)
    result = CliRunner().invoke(app, ["confirm", str(tmp_path)])
    assert result.exit_code == 0
    assert _confirmed(tmp_path / "sc-referee.yaml") is True
    assert _confirmed(tmp_path / "sc-referee.manifest.yaml") is True
    manifest = load_manifest(tmp_path / "sc-referee.manifest.yaml")
    assert all(s.sha256 and len(s.sha256) == 64 for s in manifest.shards)   # content bound


def test_confirm_refuses_when_the_layout_no_longer_assembles(tmp_path):
    _setup(tmp_path, gene_mismatch=True)                    # shards no longer share a gene set
    result = CliRunner().invoke(app, ["confirm", str(tmp_path)])
    assert result.exit_code == 2
    assert _confirmed(tmp_path / "sc-referee.yaml") is False        # nothing confirmed
    assert _confirmed(tmp_path / "sc-referee.manifest.yaml") is False


def test_confirm_refuses_when_the_design_no_longer_fits(tmp_path):
    _setup(tmp_path, drop_condition=True)                   # assembled matrix has no `condition` column
    result = CliRunner().invoke(app, ["confirm", str(tmp_path)])
    assert result.exit_code == 2
    assert _confirmed(tmp_path / "sc-referee.yaml") is False


def test_confirmed_config_semantic_edit_invalidates_authority(tmp_path):
    from sc_referee.config import load_designs
    from sc_referee.design import DesignError

    path = tmp_path / "sc-referee.yaml"
    path.write_text(DESIGN_YAML)
    result = CliRunner().invoke(app, ["confirm", str(path)])
    assert result.exit_code == 0, result.stdout
    raw = yaml.safe_load(path.read_text())
    assert raw["confirmation_digest"].startswith("config:v1:")
    raw["contrasts"][0]["reference"] = "KO"
    path.write_text(yaml.safe_dump(raw, sort_keys=False))
    with pytest.raises(DesignError, match="changed after confirmation"):
        load_designs(path)


def test_config_digest_ignores_formatting_and_key_order(tmp_path):
    from sc_referee.config import load_designs

    path = tmp_path / "sc-referee.yaml"
    path.write_text(DESIGN_YAML)
    result = CliRunner().invoke(app, ["confirm", str(path)])
    assert result.exit_code == 0, result.stdout
    raw = yaml.safe_load(path.read_text())
    path.write_text(yaml.safe_dump(dict(reversed(list(raw.items()))), sort_keys=True))
    assert load_designs(path)[0].confirmed_by_human is True
