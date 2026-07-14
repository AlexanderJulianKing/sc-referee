"""Shared adapter helpers, so every format emits the SAME canonical Bundle the checks consume.

Centralizes the integer-vs-normalized decision (item 2) so no adapter can diverge on it: a matrix
that isn't raw integers becomes `kind="normalized", counts=None`, and the count-dependent checks
abstain rather than the whole run refusing.
"""
from __future__ import annotations

import re

import numpy as np
import scipy.sparse as sp

from sc_referee.bundle import Measure

# Biological replicate tokens are preferred over technical ones: a `sample_id` is often a 10x
# LIBRARY, not the biological unit. Detecting the library as the replicate would check
# pseudoreplication at the wrong level, so `donor`/`mouse`/… win over `sample`/`replicate`.
BIOLOGICAL_REPLICATE_TOKENS = ("donor", "subject", "patient", "mouse", "animal", "individual")
TECHNICAL_REPLICATE_TOKENS = ("sample", "replicate")
REPLICATE_TOKENS = frozenset(BIOLOGICAL_REPLICATE_TOKENS + TECHNICAL_REPLICATE_TOKENS)


def is_raw_counts(X) -> bool:
    """A matrix is recompute-able RAW COUNTS iff it is non-empty and every value is FINITE,
    NON-NEGATIVE, and INTEGRAL, with at least one positive entry. Whole-valued floats (h5ad stores
    counts as float 3.0) qualify; negatives (log residuals), NaN/inf, or an all-zero library do NOT —
    a count model recomputed on them is invalid, so the matrix is recorded as `normalized` and the
    count-dependent checks abstain."""
    data = X.data if sp.issparse(X) else np.asarray(X)
    if data.size == 0:
        return False                                  # empty / all-zero sparse: nothing to recompute
    if not np.all(np.isfinite(data)):
        return False                                  # NaN/inf -> not raw counts
    if np.any(data < 0):
        return False                                  # a negative "count" is a residual, never a UMI
    if not np.all(np.mod(data, 1) == 0):
        return False                                  # non-integral -> normalized/log/CPM
    return bool(np.any(data > 0))                      # reject a degenerate all-zero matrix


# Back-compat alias: the helper's meaning is now "is a valid raw-count matrix", not merely "integral".
is_integer_valued = is_raw_counts


def id_type(names) -> str:
    if any(re.match(r"^ENSMUSG", n) for n in names):
        return "ensembl_mouse"
    if any(re.match(r"^ENSG", n) for n in names):
        return "ensembl"
    return "symbol"


def detect_replicate_var(columns):
    """The first column naming a BIOLOGICAL replicate unit; only if none exists, a technical one.
    This is a name-hint for the single-file path — the confirmed design is authoritative."""
    for tier in (BIOLOGICAL_REPLICATE_TOKENS, TECHNICAL_REPLICATE_TOKENS):
        for c in columns:
            if any(tok in str(c).lower() for tok in tier):
                return c
    return None


def measure_from_matrix(X, feature_index) -> Measure:
    """`counts` when the matrix is valid raw counts; `normalized` (counts=None) otherwise. A
    normalized matrix is recorded, not refused — the count checks abstain per-check. (item 2)"""
    if is_raw_counts(X):
        counts = X.toarray() if sp.issparse(X) else np.asarray(X)
        return Measure(kind="counts", counts=counts, long=None, feature_index=feature_index)
    return Measure(kind="normalized", counts=None, long=None, feature_index=feature_index)
