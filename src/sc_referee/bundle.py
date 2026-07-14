"""The canonical Bundle — what every adapter emits and every check consumes.

The confirmed `design` is NEVER stored on the Bundle; checks receive it separately, so
the Bundle stays a pure description of the analysis-on-disk. (C1)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import numpy as np
import pandas as pd


@dataclass
class Measure:
    # "counts" = raw integer UMIs (recompute-able); "proportions" = EIP path;
    # "normalized" = a non-integer matrix (log/CPM/…) — recorded so count checks abstain, not refuse.
    kind: Literal["counts", "proportions", "normalized"]
    counts: Optional[np.ndarray]  # cells × features RAW ints; None on the EIP + normalized paths
    long: Optional[pd.DataFrame]  # EIP: [cell_id, feature_id, inclusion_counts, exclusion_counts]
    feature_index: list  # feature ids; order == counts columns


@dataclass
class Bundle:
    observations: pd.DataFrame  # index=cell_id, one row/cell, ALL grouping cols
    measure: Measure
    feature_metadata: pd.DataFrame  # index=feature_id; cols: id_type, gene, exon?
    replicate_var: Optional[str] = None  # detected replicate col name, else None (absent)
    reported_results: Optional[pd.DataFrame] = None  # long: [feature_id, pvalue, padj, effect?]
    reported_columns: list = field(default_factory=list)  # the ORIGINAL header, for `init`
    code_signals: dict = field(default_factory=dict)  # {imports, de_calls, cluster_calls, da_calls}
    provenance: dict = field(default_factory=dict)  # {role: {path, reason}}


@dataclass
class HiCContactData:
    """Pre-extracted Hi-C contacts and bin universe; deliberately separate from cell×gene Measure."""

    contacts: Optional[pd.DataFrame]
    bins: Optional[pd.DataFrame]
    contacts_digest: Optional[str] = None
    bins_digest: Optional[str] = None


@dataclass
class HiCBundle:
    """Parallel audit bundle for Hi-C; shares only report/provenance fields with Bundle."""

    hic: HiCContactData
    reported_results: Optional[pd.DataFrame] = None
    reported_columns: list = field(default_factory=list)
    code_signals: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
