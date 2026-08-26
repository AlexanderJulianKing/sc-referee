"""Report the exact source line of the dataflow module that produced the reason."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import h  # noqa: E402
import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_1 as M  # noqa: E402

FILE = M.__file__
SRC = Path(FILE).read_text().splitlines()


def run_traced(fn, *a, **kw):
    """Return (result, [last N executed lines in the dataflow module])."""
    seen: list[int] = []

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != FILE:
            return None
        if event == "line":
            seen.append(frame.f_lineno)
        return tracer

    old = sys.gettrace()
    sys.settrace(tracer)
    try:
        out = fn(*a, **kw)
    finally:
        sys.settrace(old)
    return out, seen


def reason_site(case_dir=None, spec=None, source=None, tail=14):
    if spec is not None:
        out, seen = run_traced(h.analyze_corpus, spec, source)
    else:
        out, seen = run_traced(h.analyze_envelope, case_dir, source)
    lines = []
    for n in seen[-tail:]:
        lines.append(f"{n:>6}: {SRC[n - 1]}")
    return out, lines
