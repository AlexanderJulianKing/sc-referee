"""Apply exact single-construct text edits to a rung source; report reason + emitting line."""
from __future__ import annotations

import importlib.util
import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/vnext/src")
sys.path.insert(0, "/Users/alexanderking/.cache/recon-scratch/work")
os.environ["MT_TRACE"] = "1"

import h  # noqa: E402

_spec_obj = importlib.util.spec_from_file_location(
    "traced_dataflow_v2", "/Users/alexanderking/.cache/recon-scratch/work/traced_dataflow_v2.py"
)
assert _spec_obj is not None and _spec_obj.loader is not None
_traced = importlib.util.module_from_spec(_spec_obj)
sys.modules["traced_dataflow_v2"] = _traced
_spec_obj.loader.exec_module(_traced)


def report(spec: str, path: Path) -> str:
    plain = h.reason(spec, path)
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        _traced.analyze_code_csv_multiple_testing_dataflow(**h.inputs(spec, path))
    trace = [
        line.strip()
        for line in buffer.getvalue().splitlines()
        if "[trace]" in line and f"] {plain} @" in line
    ]
    site = trace[-1].split("@")[-1].strip() if trace else "-"
    return f"{spec} {path.name:16s} -> {plain:44s} ({site})"


if __name__ == "__main__":
    spec, base, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if out != base:
        text = base.read_text()
        for edit in sys.argv[4:]:
            old, new = edit.split("===>", 1)
            if old not in text:
                raise SystemExit(f"MISS: {old!r} not present in {base}")
            text = text.replace(old, new)
        out.write_text(text)
    print(report(spec, out))
