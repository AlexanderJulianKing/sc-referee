"""Capture a REAL Claude LAYOUT proposal for a WT/KO multi-file fixture into tests/cassettes/.

Run once (needs ANTHROPIC_API_KEY) to record the exact wire shape the layout proposer must handle; the
recording is replayed by tests/test_layout_cassette.py with NO key and NO network. This is the same
mock-drift antidote as the init cassette: a hand-built fake returns the shapes we imagine, not the
shapes the API sends — a frozen real recording cannot drift.

    set -a; . ./.env; set +a; PYTHONPATH=src python scripts/capture_layout_cassette.py
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import anthropic

from sc_referee.layout_proposer import (DEFAULT_MODEL, LAYOUT_SYSTEM_PROMPT, LAYOUT_TOOL,
                                        layout_tool_schema, scan_shards)

OUT = Path(__file__).resolve().parents[1] / "tests" / "cassettes" / "layout_wt_ko.json"
NAMES = ["WT_1", "WT_2", "KO_1", "KO_2"]   # condition encoded in the FILENAME, not the obs


def _fixture(folder: Path) -> None:
    for name in NAMES:
        X = np.random.default_rng(0).poisson(5, size=(5, 4)).astype(float)
        ad.AnnData(X=X, obs=pd.DataFrame(index=[f"{name}_c{j}" for j in range(5)]),
                   var=pd.DataFrame(index=[f"g{k}" for k in range(4)])).write_h5ad(folder / f"{name}.h5ad")


def main() -> None:
    with tempfile.TemporaryDirectory() as d:
        _fixture(Path(d))
        meta = scan_shards(Path(d))

    msg = anthropic.Anthropic().messages.create(
        model=DEFAULT_MODEL, max_tokens=2000, system=LAYOUT_SYSTEM_PROMPT,
        tools=[{"name": LAYOUT_TOOL,
                "description": "Propose the per-shard layout constants for a human to ratify.",
                "input_schema": layout_tool_schema()}],
        tool_choice={"type": "tool", "name": LAYOUT_TOOL},
        messages=[{"role": "user", "content": json.dumps(meta, indent=2, default=str)}])

    uses = [b for b in msg.content if getattr(b, "type", None) == "tool_use" and b.name == LAYOUT_TOOL]
    if not uses:
        raise SystemExit("the model returned prose, not a propose_layout call — nothing to record")

    cassette = {
        "_note": ("RECORDED real Claude layout proposal for the WT/KO fixture — replayed by "
                  "tests/test_layout_cassette.py. Do not hand-edit; re-capture with "
                  "scripts/capture_layout_cassette.py."),
        "model": msg.model, "stop_reason": msg.stop_reason,
        "tool_name": LAYOUT_TOOL, "input": uses[0].input, "meta": meta,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cassette, indent=2) + "\n")
    proposed = {s["path"]: s.get("constants", {}) for s in uses[0].input.get("shards", [])}
    print(f"wrote {OUT}")
    print(f"proposed constants -> {json.dumps(proposed)}")   # summary only; no secrets


if __name__ == "__main__":
    main()
