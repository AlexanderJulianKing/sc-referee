"""Closed, code-owned vocabulary for the recurring dimensions checks audit."""
from __future__ import annotations

AUDIT_DIMENSION_LABELS = {
    "unit_of_independence": "Unit of independence",
    "orientation": "Orientation / sign",
    "inclusion_set": "Inclusion set / denominator",
    "conditioning_set": "Conditioning set",
    "scale": "Scale / transform / normalization",
    "selection": "Selection / circularity",
    "estimand": "Estimand",
    "weighting": "Weighting",
    "calibration": "Calibration",
    "advisory_policy": "Advisory policy",
}

AUDIT_DIMENSIONS = frozenset(AUDIT_DIMENSION_LABELS)
