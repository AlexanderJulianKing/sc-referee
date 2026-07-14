"""The layout proposer, tested against a RECORDED real Claude response.

The fake-client tests (test_layout_proposer.py) return the shape we imagined; this replays a FROZEN
real recording (tests/cassettes/layout_wt_ko.json, captured by scripts/capture_layout_cassette.py)
with no key and no network, so the wire shape under test is the one the API actually sends — it cannot
drift. The WT/KO fixture encodes condition in the FILENAME (no obs columns), which is exactly the case
a deterministic draft cannot solve and Claude must propose.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import anndata as ad
import numpy as np
import pandas as pd

import jsonschema

from sc_referee.layout_proposer import (_manifest_from_payload, layout_tool_schema,
                                        propose_manifest)

CASSETTE = Path(__file__).parent / "cassettes" / "layout_wt_ko.json"
NAMES = ["WT_1", "WT_2", "KO_1", "KO_2"]


def _load():
    return json.loads(CASSETTE.read_text())


def test_recorded_response_matches_the_layout_schema():
    """The real payload validates against the tool schema — proof the shape we handle is the shape sent."""
    payload = _load()["input"]
    jsonschema.validate(payload, layout_tool_schema())
    for shard in payload["shards"]:
        assert "path" in shard and "constants" in shard
        assert "condition" in shard["constants"]        # condition was recoverable from the filename


def test_recorded_response_maps_files_to_conditions():
    cas = _load()
    manifest = _manifest_from_payload(cas["input"], cas["meta"])
    cond = {s.path: s.constants.get("condition") for s in manifest.shards}
    assert cond == {"WT_1.h5ad": "WT", "WT_2.h5ad": "WT", "KO_1.h5ad": "KO", "KO_2.h5ad": "KO"}
    assert {s.constants["sample_id"] for s in manifest.shards} == {"WT_1", "WT_2", "KO_1", "KO_2"}
    assert manifest.confirmed_by_human is False


def test_recorded_response_round_trips_through_propose_manifest(tmp_path):
    """End-to-end replay: rebuild the same fixture, replay the recorded tool_use, get a Manifest."""
    for name in NAMES:
        X = np.random.default_rng(0).poisson(5, size=(5, 4)).astype(float)
        ad.AnnData(X=X, obs=pd.DataFrame(index=[f"{name}_c{j}" for j in range(5)]),
                   var=pd.DataFrame(index=[f"g{k}" for k in range(4)])).write_h5ad(tmp_path / f"{name}.h5ad")

    payload = _load()["input"]

    class _Replay:
        @property
        def messages(self):
            def create(**kw):
                block = SimpleNamespace(type="tool_use", name="propose_layout", input=payload)
                return SimpleNamespace(content=[block])
            return SimpleNamespace(create=create)

    manifest, source = propose_manifest(tmp_path, client=_Replay())
    assert source == "claude"
    assert {s.path: s.constants.get("condition") for s in manifest.shards} == {
        "WT_1.h5ad": "WT", "WT_2.h5ad": "WT", "KO_1.h5ad": "KO", "KO_2.h5ad": "KO"}
    assert manifest.unresolved                          # the model flagged batch / replicate-unit ambiguity
