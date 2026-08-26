from __future__ import annotations

import importlib.util
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

if __name__ == "__main__":
    spec = sys.argv[1]
    source = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = _m.analyze_code_csv_multiple_testing_dataflow(**h.inputs(spec, source))
    label = result.reason or ("CANDIDATE:" + result.facts.correction_classification)
    print(f"{spec} {(source.name if source else 'ORIGINAL'):16s} -> {label}")
