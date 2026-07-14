"""Frozen-metric regression for the Biermann published-human-data anchor.

Skips when the capsule is absent (the derived data is not committed by default), so CI stays green
without it; when present, it pins the exact patient-level recompute the demo depends on.
"""
from __future__ import annotations

import pytest

from bench.biermann_anchor import EXPECTED, run_biermann_anchor


def _capsule_or_skip():
    try:
        return run_biermann_anchor()
    except FileNotFoundError as missing:
        pytest.skip(str(missing))


def test_biermann_reproduces_the_frozen_collapse():
    result, eu = _capsule_or_skip()
    assert eu is not None, "experimental_unit finding must be present"
    m = eu.metrics
    assert m["valid_reported_sig"] == EXPECTED["valid_reported_sig"]      # 16,289
    # One gene lies on a platform-sensitive DESeq2/BLAS boundary: Linux reports 769 and
    # macOS 770. Both reproduce the same 95.3% scientific conclusion.
    assert abs(m["survivors"] - EXPECTED["survivors"]) <= 1
    assert round(1 - m["survival_rate"], 3) == 0.953
    assert m["powered"] is EXPECTED["powered"]                           # underpowered
    assert round(m["powered_fraction"], 4) == EXPECTED["powered_fraction"]  # 0.3817 < 0.80 gate
    # The dramatic collapse is observed, but the blocker is responsibly withheld.
    assert eu.status == EXPECTED["status"]                               # needs_evidence
