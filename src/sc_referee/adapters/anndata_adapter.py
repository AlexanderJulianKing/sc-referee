"""AnnData (.h5ad) adapter — emits the canonical Bundle from an AnnData file. (C11)

Count models need RAW integers: prefer layers['counts'] -> raw.X -> X. A non-integer matrix is
recorded as normalized (counts=None) rather than refused — the count-dependent checks abstain
per-check (item 2). The integer/id/replicate helpers live in adapters/_common so every format
adapter emits an identical Bundle.
"""
from __future__ import annotations

from pathlib import Path

import anndata as ad
import pandas as pd
import numpy as np
import scipy.sparse as sp

from sc_referee.adapters._common import detect_replicate_var, id_type, is_raw_counts, measure_from_matrix
from sc_referee.bundle import Bundle


def _same_matrix(left, right) -> bool:
    if left.shape != right.shape:
        return False
    if sp.issparse(left) or sp.issparse(right):
        a = left if sp.issparse(left) else sp.csr_matrix(left)
        b = right if sp.issparse(right) else sp.csr_matrix(right)
        return (a != b).nnz == 0
    return np.array_equal(np.asarray(left), np.asarray(right), equal_nan=True)


def _pick_matrix(adata, layer):
    """(matrix, var_names) for the requested layer. Default preference layers['counts'] -> raw.X -> X,
    each paired with ITS OWN feature names — `raw.X` must use `raw.var_names`, not the filtered
    `adata.var_names`, or counts are attributed to the wrong genes."""
    if layer in (None, ""):
        candidates = [(".X", adata.X, adata.var_names)]
        if adata.raw is not None:
            candidates.append((".raw.X", adata.raw.X, adata.raw.var_names))
        candidates.extend((f"layers[{key}]", value, adata.var_names)
                          for key, value in adata.layers.items())
        raw = [candidate for candidate in candidates if is_raw_counts(candidate[1])]
        if len(raw) == 1:
            return raw[0]
        if len(raw) > 1:
            first = raw[0]
            if all(tuple(map(str, item[2])) == tuple(map(str, first[2]))
                   and _same_matrix(item[1], first[1]) for item in raw[1:]):
                return first
            names = ", ".join(item[0] for item in raw)
            raise ValueError(
                f"multiple differing raw-count matrices are plausible ({names}); declare the "
                "intended layer in a confirmed exhaustive manifest")
        if len(candidates) == 1:
            return candidates[0]
        names = ", ".join(item[0] for item in candidates)
        raise ValueError(
            f"multiple internal matrices exist but none is uniquely raw ({names}); declare the "
            "intended layer in a confirmed exhaustive manifest")
    key = str(layer).split("/")[-1]                        # "layers/counts" -> "counts"
    if key == "X":
        return ".X", adata.X, adata.var_names
    if key in ("raw", "raw.X"):
        if adata.raw is None:
            raise ValueError(f"declared count layer {layer!r} but the file has no .raw")
        return ".raw.X", adata.raw.X, adata.raw.var_names
    if key in adata.layers:
        return f"layers[{key}]", adata.layers[key], adata.var_names
    raise ValueError(f"declared count layer {layer!r} not found (layers: {list(adata.layers)})")


def _first_duplicates(names, k=3):
    seen, dups = set(), []
    for n in names:
        if n in seen and n not in dups:
            dups.append(n)
        seen.add(n)
    return dups[:k]


def read_anndata(path, layer=None) -> Bundle:
    adata = ad.read_h5ad(Path(path))
    obs = adata.obs.copy()
    slot, X, var_names = _pick_matrix(adata, layer)

    feat_idx = list(map(str, var_names))
    if len(set(feat_idx)) != len(feat_idx):
        raise ValueError(f"{Path(path).name}: duplicate feature id(s) {_first_duplicates(feat_idx)} — "
                         f"gene columns must be unique, or alignment attributes counts to the wrong gene.")
    feature_metadata = pd.DataFrame(index=feat_idx)
    feature_metadata["id_type"] = id_type(feat_idx)

    bundle = Bundle(
        observations=obs,
        measure=measure_from_matrix(X, feat_idx),
        feature_metadata=feature_metadata,
        replicate_var=detect_replicate_var(list(obs.columns)),
    )
    bundle.matrix_slot = slot
    return bundle
