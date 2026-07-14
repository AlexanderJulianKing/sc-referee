"""The Claude LAYOUT proposer — `init`, one level up.

Claude reads directory metadata only and PROPOSES the per-shard semantic constants (condition/…) for
a human to confirm; sample_id stays deterministic; no key -> a deterministic draft. Tested with a fake
client (no network), the same way the roles proposer is; a real recording (cassette) lands separately.
"""
from types import SimpleNamespace

import anndata as ad
import numpy as np
import pandas as pd

from sc_referee.layout_proposer import propose_manifest, scan_shards


def _shard(path, obs, genes=("g0", "g1", "g2"), seed=0):
    X = np.random.default_rng(seed).poisson(5, size=(len(obs), len(genes))).astype(float)
    ad.AnnData(X=X, obs=obs, var=pd.DataFrame(index=list(genes))).write_h5ad(path)


class _FakeClient:
    """Replays a canned tool_use payload — mirrors the real Anthropic client's shape."""

    def __init__(self, payload):
        self._payload = payload

    @property
    def messages(self):
        def create(**kw):
            block = SimpleNamespace(type="tool_use", name="propose_layout", input=self._payload)
            return SimpleNamespace(content=[block])
        return SimpleNamespace(create=create)


def test_scan_shards_reads_metadata_only(tmp_path):
    _shard(tmp_path / "WT_1.h5ad", pd.DataFrame({"cell_type": ["T", "B"]}, index=["a", "b"]))
    _shard(tmp_path / "KO_1.h5ad", pd.DataFrame({"cell_type": ["T", "B"]}, index=["a", "b"]))
    meta = scan_shards(tmp_path)
    assert [m["sample_id"] for m in meta] == ["KO_1", "WT_1"]          # sorted glob
    assert meta[0]["obs_columns"] == ["cell_type"]
    assert meta[0]["n_cells"] == 2 and meta[0]["n_genes"] == 3
    assert "T" in meta[0]["obs_preview"]["cell_type"]


def test_propose_manifest_fills_condition_via_claude(tmp_path):
    for name in ["WT_1", "WT_2", "KO_1", "KO_2"]:
        _shard(tmp_path / f"{name}.h5ad", pd.DataFrame(index=["a", "b"]))   # condition NOT in obs
    payload = {
        "shards": [
            {"path": "WT_1.h5ad", "constants": {"condition": "WT"}},
            {"path": "WT_2.h5ad", "constants": {"condition": "WT"}},
            {"path": "KO_1.h5ad", "constants": {"condition": "KO"}},
            {"path": "KO_2.h5ad", "constants": {"condition": "KO"}},
        ],
        "excluded": [], "confidence": {"condition": "high"}, "unresolved": ["replicate_unit"],
    }
    m, source = propose_manifest(tmp_path, client=_FakeClient(payload))
    assert source == "claude"
    cond = {s.path: s.constants.get("condition") for s in m.shards}
    assert cond == {"WT_1.h5ad": "WT", "WT_2.h5ad": "WT", "KO_1.h5ad": "KO", "KO_2.h5ad": "KO"}
    assert {s.constants["sample_id"] for s in m.shards} == {"WT_1", "WT_2", "KO_1", "KO_2"}  # deterministic
    assert m.unresolved == ["replicate_unit"] and m.confidence == {"condition": "high"}
    assert m.confirmed_by_human is False                               # never auto-confirmed


def test_propose_manifest_falls_back_to_draft_without_a_client(tmp_path):
    _shard(tmp_path / "m1.h5ad", pd.DataFrame(index=["a", "b"]))
    _shard(tmp_path / "m2.h5ad", pd.DataFrame(index=["a", "b"]))
    m, source = propose_manifest(tmp_path, client=None)               # no client -> deterministic
    assert source == "heuristic_no_llm"
    assert all("condition" not in s.constants for s in m.shards)      # sample_id only, never a guess


def test_propose_manifest_honors_exclusions(tmp_path):
    for name in ["WT_1", "KO_1", "atlas"]:
        _shard(tmp_path / f"{name}.h5ad", pd.DataFrame(index=["a", "b"]))
    payload = {
        "shards": [
            {"path": "WT_1.h5ad", "constants": {"condition": "WT"}},
            {"path": "KO_1.h5ad", "constants": {"condition": "KO"}},
        ],
        "excluded": [{"path": "atlas.h5ad", "reason": "reference_atlas"}],
        "confidence": {}, "unresolved": [],
    }
    m, source = propose_manifest(tmp_path, client=_FakeClient(payload))
    assert [s.path for s in m.shards] == ["KO_1.h5ad", "WT_1.h5ad"]   # atlas dropped; sorted
    assert "atlas" not in m.expected_sample_ids
    assert m.excluded == [{"path": "atlas.h5ad", "reason": "reference_atlas"}]


def test_smart_fallback_detects_condition_in_obs(tmp_path):
    # every shard's obs carries condition + donor_id -> nothing to fill; noted, not nagged
    for name in ("m1", "m2"):
        _shard(tmp_path / f"{name}.h5ad",
               pd.DataFrame({"condition": ["WT", "KO"], "donor_id": ["d1", "d2"]}, index=["a", "b"]))
    m, source = propose_manifest(tmp_path, client=None)
    assert source == "heuristic_no_llm"
    assert m.unresolved == []                                 # condition is embedded, not missing
    assert m.confidence.get("condition") == "in .obs (condition)"
    assert m.confidence.get("replicate_unit") == "in .obs (donor_id)"


def test_smart_fallback_flags_condition_when_absent_from_obs(tmp_path):
    for name in ("m1", "m2"):
        _shard(tmp_path / f"{name}.h5ad", pd.DataFrame(index=["a", "b"]))   # empty obs
    m, source = propose_manifest(tmp_path, client=None)
    assert any("condition" in u.lower() for u in m.unresolved)


def test_proposer_refuses_a_hallucinated_path(tmp_path):
    for n in ("WT_1", "KO_1"):
        _shard(tmp_path / f"{n}.h5ad", pd.DataFrame(index=["a", "b"]))
    payload = {"shards": [{"path": "WT_1.h5ad", "constants": {"condition": "WT"}},
                          {"path": "GHOST.h5ad", "constants": {"condition": "KO"}}],
               "excluded": [], "unresolved": []}
    import pytest
    with pytest.raises(ValueError) as e:
        propose_manifest(tmp_path, client=_FakeClient(payload))
    assert "not found" in str(e.value).lower()


def test_proposer_flags_an_unclassified_shard(tmp_path):
    for n in ("WT_1", "KO_1"):
        _shard(tmp_path / f"{n}.h5ad", pd.DataFrame(index=["a", "b"]))
    payload = {"shards": [{"path": "WT_1.h5ad", "constants": {"condition": "WT"}}],  # KO_1 forgotten
               "excluded": [], "unresolved": []}
    m, _ = propose_manifest(tmp_path, client=_FakeClient(payload))
    assert any("KO_1.h5ad" in u for u in m.unresolved)                # surfaced, not silently blank
    assert [s.path for s in m.shards] == ["KO_1.h5ad", "WT_1.h5ad"]
