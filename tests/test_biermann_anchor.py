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
    # These counts come from the pydeseq2 patient-level recompute, whose BLAS-level arithmetic
    # differs across platforms; genes sitting exactly on the significance boundary flip by a handful
    # (e.g. 16,289 on macOS vs 16,288 on Linux). The scientific claim — a ~95% collapse that is
    # responsibly withheld — is invariant, so pin the headline numbers with a tolerance that absorbs
    # boundary flips while still catching real drift.
    assert m["valid_reported_sig"] == pytest.approx(EXPECTED["valid_reported_sig"], abs=5)   # ~16,289
    assert m["survivors"] == pytest.approx(EXPECTED["survivors"], abs=5)                     # ~770
    assert m["survival_rate"] == pytest.approx(EXPECTED["survival_rate"], abs=0.001)         # 95.3% collapse
    assert m["powered"] is EXPECTED["powered"]                           # underpowered
    assert m["powered_fraction"] == pytest.approx(EXPECTED["powered_fraction"], abs=0.005)   # < 0.80 gate
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
