"""Full traced run: show every diagnostic line for one source."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/vnext/src")
sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/work")
os.environ["MT_TRACE"] = "1"

import h  # noqa: E402

_s = importlib.util.spec_from_file_location(
    "traced_dataflow_v2", "/Users/alexanderking/.cache/recon-scratch/work/traced_dataflow_v2.py"
)
_m = importlib.util.module_from_spec(_s)
sys.modules["traced_dataflow_v2"] = _m
_s.loader.exec_module(_m)

if __name__ == "__main__":
    case = sys.argv[1]
    source = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = _m.analyze_code_csv_multiple_testing_dataflow(**h.inputs(case, source))
    print(f"=> reason={result.reason}")
