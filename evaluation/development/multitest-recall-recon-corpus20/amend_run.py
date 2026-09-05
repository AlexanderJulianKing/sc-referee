"""Run the prototype amended analyzer over the whole open corpus."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/vnext/src")
sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/work")

import h  # noqa: E402

_s = importlib.util.spec_from_file_location(
    "amended_dataflow_v2", "/Users/alexanderking/.cache/recon-scratch/work/amended_dataflow_v2.py"
)
_m = importlib.util.module_from_spec(_s)
sys.modules["amended_dataflow_v2"] = _m
_s.loader.exec_module(_m)

BASE = json.loads(
    (
        Path(
            "/Users/alexanderking/.cache/recon-scratch/vnext/evaluation/development/"
            "multitest-open-corpus-v1/adapter_replay_records.json"
        )
    ).read_text()
)["2.0.0"]["results"]


def outcome(spec: str) -> str:
    result = _m.analyze_code_csv_multiple_testing_dataflow(**h.inputs(spec))
    if result.reason is not None:
        return result.reason
    return "CANDIDATE:" + result.facts.correction_classification


if __name__ == "__main__":
    changed = []
    flips = []
    for spec in sorted(h.LABELS):
        label = h.LABELS[spec]["label"]
        now = outcome(spec)
        before = (
            BASE[spec][1] if BASE[spec][0] == "abstain" else "CANDIDATE:" + BASE[spec][1]
        )
        if now != before:
            changed.append((spec, label, before, now))
        if label == "correct" and now.startswith("CANDIDATE"):
            flips.append(spec)
    for spec, label, before, now in changed:
        print(f"CHANGED {label:8s} {spec}: {before} -> {now}")
    misstep = sum(
        1
        for spec in h.LABELS
        if h.LABELS[spec]["label"] == "misstep" and outcome(spec).startswith("CANDIDATE")
    )
    correct = sum(
        1
        for spec in h.LABELS
        if h.LABELS[spec]["label"] == "correct" and outcome(spec).startswith("CANDIDATE")
    )
    print(f"\nmisstep candidates: {misstep}/25   correct candidates (must be 0): {correct}/25")
    if flips:
        print("FALSE ACCUSATIONS:", flips)
