"""Frozen-metric regression for the Biermann published-human-data anchor.

Skips when the capsule is absent (the derived data is not committed by default), so CI stays green
without it; when present, it pins the exact patient-level recompute the demo depends on.
"""
from __future__ import annotations

import pytest

from bench.biermann_anchor import EXPECTED, run_biermann_anchor
from sc_referee.init import propose


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
    assert m["survivors"] == EXPECTED["survivors"]                        # 770
    assert round(m["survival_rate"], 4) == EXPECTED["survival_rate"]      # 0.0473 -> 95.3% collapse
    assert m["powered"] is EXPECTED["powered"]                           # underpowered
    assert round(m["powered_fraction"], 4) == EXPECTED["powered_fraction"]  # 0.3817 < 0.80 gate
    # The dramatic collapse is observed, but the blocker is responsibly withheld.
    assert eu.status == EXPECTED["status"]                               # needs_evidence


def test_biermann_original_r_code_yields_exact_review_readback():
    proposal, source = propose("demos/biermann-pseudoreplication", client=None)

    assert source == "hard_signals"
    assert proposal["design"] == {
        "replicate_unit": ["patient"], "condition": "organ", "batch": [],
    }
    contrast = proposal["contrasts"][0]
    assert (contrast["reference"], contrast["test"]) == ("Peripheral", "Brain")
    assert contrast["analyst_adjusted_for"] == []
    assert proposal["reported_results"]["unit_of_test"] == "cell"
    assert proposal["unresolved"] == []
