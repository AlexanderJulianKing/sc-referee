"""Executed mutation-ladder runner. Rungs are (name, text-substitution list)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import h  # noqa: E402


def apply(src: str, edits) -> str:
    out = src
    for old, new in edits:
        if old not in out:
            raise AssertionError(f"rung edit did not match: {old[:90]!r}")
        out = out.replace(old, new)
    return out


def ladder(case_dir, rungs, spec=None):
    """rungs: list of (label, edits). Each rung is cumulative on the previous."""
    if spec is not None:
        src = (h.CORPUS / "cases" / spec / "analysis.py").read_text()
    else:
        src = (case_dir / "project" / "analysis.py").read_text()
    rows = []
    if spec is not None:
        base = h.analyze_corpus(spec)
    else:
        base = h.analyze_envelope(case_dir)
    rows.append(("rung 0 (verbatim)", h.classify(base)))
    current = src
    for label, edits in rungs:
        current = apply(current, edits)
        b = current.encode("utf-8")
        r = h.analyze_corpus(spec, b) if spec is not None else h.analyze_envelope(case_dir, b)
        rows.append((label, h.classify(r)))
    return rows, current


def show(rows):
    for label, outcome in rows:
        print(f"  {label:<62} {outcome[0]:<9} {outcome[1]}")
