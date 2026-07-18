"""Trust-chain integrity (Codex review, Tier 1). The confirm gate must bind the MANIFEST CONTENT
and the per-shard FILES it was confirmed against — not just the counts bytes — or a post-confirm edit
audits a different (possibly inverted) analysis than the human ratified.

- a confirmed manifest's semantic content (paths, constants, assembly, obs joins) is digested;
- each shard's counts AND obs files are hashed;
- at audit, a mismatch REFUSES; an UNCONFIRMED manifest cannot render a blocking verdict.
"""
import anndata as ad
import numpy as np
import pandas as pd
import pytest

from sc_referee.ingest import IngestError, ingest
from sc_referee.manifest import load_manifest

DESIGN = """analysis_type: condition_contrast_DE
confirmed_by_human: false
design: {replicate_unit: [mouse_id], condition: condition, batch: []}
contrasts:
- {name: KO_vs_WT, reference: WT, test: KO, replicate_unit: [mouse_id], sample_unit: [mouse_id],
   pairing_unit: [], model: ~ condition, target_coefficient: 'condition[T.KO]'}
confidence: {replicate_unit: high, condition: high}
unresolved: []
"""


def _shard(path, seed=0):
    X = np.random.default_rng(seed).poisson(5, size=(3, 3)).astype(float)
    ad.AnnData(X=X, obs=pd.DataFrame(index=["a", "b", "c"]),
               var=pd.DataFrame(index=["g0", "g1", "g2"])).write_h5ad(path)


def _setup(folder):
    _shard(folder / "M1.h5ad", 1)
    _shard(folder / "M2.h5ad", 2)
    (folder / "sc-referee.manifest.yaml").write_text(
        "manifest_version: 1\nconfirmed_by_human: false\n"
        "expected: { sample_ids: [M1, M2] }\nshards:\n"
        "  - { path: M1.h5ad, constants: {sample_id: M1, mouse_id: M1, condition: WT} }\n"
        "  - { path: M2.h5ad, constants: {sample_id: M2, mouse_id: M2, condition: KO} }\n")
    (folder / "sc-referee.yaml").write_text(DESIGN)


def _confirm(folder):
    from typer.testing import CliRunner

    from sc_referee.cli import app
    r = CliRunner().invoke(app, ["confirm", str(folder)])
    assert r.exit_code == 0, r.stdout
    return r


def test_confirmed_manifest_assembles_cleanly(tmp_path):
    _setup(tmp_path)
    _confirm(tmp_path)
    b = ingest(tmp_path)                                        # no mutation -> assembles fine
    assert list(b.observations["condition"]) == ["WT", "WT", "WT", "KO", "KO", "KO"]


def test_editing_a_constant_after_confirm_refuses(tmp_path):
    _setup(tmp_path)
    _confirm(tmp_path)
    # invert the labels WITHOUT re-confirming (files unchanged, so byte-hashes still match)
    p = tmp_path / "sc-referee.manifest.yaml"
    p.write_text(p.read_text().replace("condition: WT", "condition: KO_TMP")
                 .replace("condition: KO", "condition: WT").replace("condition: KO_TMP", "condition: KO"))
    with pytest.raises(IngestError) as e:
        ingest(tmp_path)
    assert "confirm" in str(e.value).lower() or "changed" in str(e.value).lower()


def test_editing_a_shard_file_after_confirm_refuses(tmp_path):
    _setup(tmp_path)
    _confirm(tmp_path)
    _shard(tmp_path / "M1.h5ad", seed=99)                      # different bytes, same shape
    with pytest.raises(IngestError) as e:
        ingest(tmp_path)
    assert "changed" in str(e.value).lower() or "sha256" in str(e.value).lower()


def test_corrupt_confirmed_replacement_reports_hash_drift_before_parser_error(tmp_path):
    _setup(tmp_path)
    _confirm(tmp_path)
    (tmp_path / "M1.h5ad").write_bytes(b"not an hdf5 file")
    with pytest.raises(IngestError) as exc:
        ingest(tmp_path)
    message = str(exc.value).lower()
    assert "sha256" in message or "changed since confirmation" in message
    assert "unable to synchronously open" not in message


def test_parser_consumes_verified_snapshot_when_source_path_is_replaced(tmp_path, monkeypatch):
    import sc_referee.adapters.assemble as assembly

    _setup(tmp_path)
    _confirm(tmp_path)
    original = assembly._read_shard
    replaced = False

    def replace_after_snapshot(shard, folder, **kwargs):
        nonlocal replaced
        if not replaced:
            replaced = True
            _shard(tmp_path / "M1.h5ad", seed=99)
        return original(shard, folder, **kwargs)

    monkeypatch.setattr(assembly, "_read_shard", replace_after_snapshot)
    bundle = ingest(tmp_path)
    assert replaced and bundle.measure.counts.shape == (6, 3)


def test_write_manifest_round_trips_all_shard_fields(tmp_path):
    from sc_referee.manifest import Manifest, Shard, write_manifest
    m = Manifest(shards=[Shard(path="c.csv", format="csv", orientation="cells_x_genes",
                               layer="layers/counts", obs_path="o.csv", obs_join_on="cell_id",
                               constants={"sample_id": "s1", "condition": "WT"})],
                 expected_sample_ids=["s1"])
    write_manifest(m, tmp_path / "sc-referee.manifest.yaml")
    loaded = load_manifest(tmp_path / "sc-referee.manifest.yaml")
    s = loaded.shards[0]
    assert (s.format, s.orientation, s.layer, s.obs_path, s.obs_join_on) == (
        "csv", "cells_x_genes", "layers/counts", "o.csv", "cell_id")


def test_audit_gate_requires_the_manifest_to_be_confirmed_too(tmp_path):
    """An UNCONFIRMED manifest must not let a blocker FIRE, even if sc-referee.yaml is confirmed —
    and must not earn certification. Here condition is aliased with batch (a confounding blocker if
    fully confirmed); with the manifest unconfirmed, no blocker may appear but CI fails closed."""
    import yaml as y

    from sc_referee import statuses as S
    from sc_referee.audit import run_audit
    _shard(tmp_path / "M1.h5ad", 1)
    _shard(tmp_path / "M2.h5ad", 2)
    (tmp_path / "sc-referee.manifest.yaml").write_text(
        "manifest_version: 1\nconfirmed_by_human: false\nexpected: { sample_ids: [M1, M2] }\nshards:\n"
        "  - { path: M1.h5ad, constants: {sample_id: M1, mouse_id: M1, condition: WT, batch: B1} }\n"
        "  - { path: M2.h5ad, constants: {sample_id: M2, mouse_id: M2, condition: KO, batch: B2} }\n")
    (tmp_path / "sc-referee.yaml").write_text(DESIGN.replace("batch: []", "batch: [batch]"))
    d = y.safe_load((tmp_path / "sc-referee.yaml").read_text())
    d["confirmed_by_human"] = True                            # confirm ONLY the design
    (tmp_path / "sc-referee.yaml").write_text(y.safe_dump(d))

    result = run_audit(tmp_path, engine="simple")
    assert result.confirmed_by_human is False
    assert result.ci_conclusion() == "neutral"               # unratified authority cannot certify
    assert result.ci_fails() is False                        # ...but absence of proof is not a blocker
    assert all(f.status != S.BLOCKER for f in result.findings)


def test_confirmed_manifest_stripped_of_integrity_fields_refuses(tmp_path):
    _setup(tmp_path)
    _confirm(tmp_path)
    p = tmp_path / "sc-referee.manifest.yaml"                   # strip confirmed_digest, keep confirmed:true
    p.write_text("\n".join(l for l in p.read_text().splitlines()
                           if not l.startswith("confirmed_digest")))
    with pytest.raises(IngestError) as e:
        ingest(tmp_path)
    assert "integrity" in str(e.value).lower() or "missing" in str(e.value).lower()


def test_confirm_refuses_a_manifest_with_unresolved_items(tmp_path):
    from typer.testing import CliRunner

    from sc_referee.cli import app
    _setup(tmp_path)
    p = tmp_path / "sc-referee.manifest.yaml"
    p.write_text(p.read_text() + "unresolved:\n  - 'is the trailing number a replicate or a batch?'\n")
    r = CliRunner().invoke(app, ["confirm", str(tmp_path)])
    assert r.exit_code == 2
    assert "unresolved" in r.stdout.lower()


@pytest.mark.parametrize("payload", [b"\xff", b"- not\n- a\n- mapping\n", b"shards: {bad\n"])
def test_invalid_manifest_bytes_yaml_or_top_level_are_typed(tmp_path, payload):
    (tmp_path / "sc-referee.manifest.yaml").write_bytes(payload)
    with pytest.raises(IngestError) as exc:
        ingest(tmp_path)
    assert "manifest" in str(exc.value).lower()
