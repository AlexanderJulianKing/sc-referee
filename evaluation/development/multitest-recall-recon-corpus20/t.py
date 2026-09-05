"""Traced runner: report the detector line that produced the first reason."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/vnext/src")
sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/work")
os.environ["MT_TRACE"] = "1"

import h  # noqa: E402

spec_path = "/Users/alexanderking/.cache/recon-scratch/work/traced_dataflow_v2.py"
spec_obj = importlib.util.spec_from_file_location("traced_dataflow_v2", spec_path)
assert spec_obj is not None and spec_obj.loader is not None
module = importlib.util.module_from_spec(spec_obj)
sys.modules["traced_dataflow_v2"] = module
spec_obj.loader.exec_module(module)

if __name__ == "__main__":
    case = sys.argv[1]
    source = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    kwargs = h.inputs(case, source)
    result = module.analyze_code_csv_multiple_testing_dataflow(**kwargs)
    print(f"{case} {(source.name if source else 'ORIGINAL'):20s} -> reason={result.reason}")
