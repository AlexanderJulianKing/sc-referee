"""Wrap named dataflow functions to log call/return, then run a case."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import h  # noqa: E402

import sc_referee.scientific_checks.code_csv_multiple_testing_dataflow_v2_1 as M  # noqa: E402

LOG: list[str] = []


def wrap(names, summarize=None):
    for name in names:
        fn = getattr(M, name)
        if getattr(fn, "_wrapped", False):
            continue

        def make(name, fn):
            def inner(*a, **kw):
                out = fn(*a, **kw)
                s = summarize(name, out, a, kw) if summarize else repr(out)[:160]
                LOG.append(f"{name} -> {s}")
                return out

            inner._wrapped = True  # type: ignore[attr-defined]
            return inner

        setattr(M, name, make(name, fn))
