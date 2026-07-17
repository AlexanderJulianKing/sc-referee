"""Permutation calibration for the confounder-candidate diagnostic.

Why this exists
---------------
A per-test null of 1/sqrt(n-1) prices ONE correlation. Across a candidate set, several causally-null
quantities will clear 3-4 sd by chance, and the tool's entire value is not crying wolf. So every
association statistic in the diagnostic is calibrated two ways against the SAME candidate set:

* per-candidate permutation p: how often a random reassignment of the exposure to units produces an
  association at least as extreme for THIS candidate.
* scan-wide (family-wise) p: how often the MAXIMUM association across ALL candidates, under a random
  reassignment, is at least as extreme as this candidate's observed value. This is the max-T /
  Westfall-Young construction and it controls the family-wise false-positive rate over the whole scan.

The exposure is permuted at the unit level (the level at which it varies), holding every candidate's
unit summary fixed. That tests exactly the claim the leg makes: "this summary tracks the exposure
more than a chance reassignment of the exposure to units would."

Determinism: seeded. The seed is part of the protocol identity so a rerun reproduces the p-values.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

DEFAULT_PERMUTATIONS = 10000
DEFAULT_SEED = 20260717


@dataclass(frozen=True)
class Calibration:
    """The calibrated verdict for one candidate's association. Descriptive; no threshold applied."""

    statistic: float | None          # observed correlation
    n_units: int
    null_sd_per_test: float | None    # 1/sqrt(n-1), shown for orientation
    permutation_p: float | None       # per-candidate
    scanwide_p: float | None          # family-wise over the whole candidate set
    n_permutations: int
    seed: int

    def as_dict(self) -> dict:
        return {
            "statistic": None if self.statistic is None else round(self.statistic, 6),
            "n_units": self.n_units,
            "null_sd_per_test": None if self.null_sd_per_test is None else round(self.null_sd_per_test, 4),
            "permutation_p": None if self.permutation_p is None else round(self.permutation_p, 5),
            "scanwide_p": None if self.scanwide_p is None else round(self.scanwide_p, 5),
            "n_permutations": self.n_permutations,
            "seed": self.seed,
            "note": "permutation_p is per-candidate; scanwide_p controls the family-wise "
                    "false-positive rate over the whole candidate set. Descriptive: no threshold "
                    "is applied.",
        }


def _corr(x: np.ndarray, y: np.ndarray) -> float | None:
    sx, sy = x.std(), y.std()
    if sx == 0 or sy == 0:
        return None
    return float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))


def calibrate(summaries: dict, exposure: np.ndarray, *,
              n_permutations: int = DEFAULT_PERMUTATIONS, seed: int = DEFAULT_SEED) -> dict:
    """Calibrate every candidate's association against a shared permutation null.

    `summaries` maps candidate id -> its unit-summary vector (aligned to `exposure`, one value per
    unit). Returns candidate id -> Calibration. Candidates with a constant summary (undefined
    correlation) get a Calibration with statistic=None and no p-values -- they are still emitted, per
    the no-filter rule, just not calibratable.

    The permutation null and the scan-wide maximum are computed ONCE over all calibratable
    candidates, so both p-values price the same family.
    """
    exposure = np.asarray(exposure, dtype=float)
    n = len(exposure)
    n_units = n

    obs: dict[str, float] = {}
    vecs: dict[str, np.ndarray] = {}
    for cid, vec in summaries.items():
        v = np.asarray(vec, dtype=float)
        if len(v) != n:
            continue
        r = _corr(v, exposure)
        if r is None:
            continue
        obs[cid] = r
        vecs[cid] = v

    null_sd = None if n_units < 4 else 1.0 / math.sqrt(n_units - 1)

    if not obs or n_units < 4:
        out = {}
        for cid, vec in summaries.items():
            r = obs.get(cid)
            out[cid] = Calibration(r, n_units, null_sd, None, None, n_permutations, seed)
        return out

    rng = np.random.default_rng(seed)
    ids = list(obs)
    V = np.vstack([vecs[c] for c in ids])                  # (k, n)
    Vc = V - V.mean(axis=1, keepdims=True)
    Vnorm = np.sqrt((Vc ** 2).sum(axis=1))                 # (k,)

    # per-candidate and family-wise exceedance counts
    ge_self = np.zeros(len(ids))
    ge_max = np.zeros(len(ids))
    abs_obs = np.array([abs(obs[c]) for c in ids])
    for _ in range(n_permutations):
        gp = exposure[rng.permutation(n)]
        gc = gp - gp.mean()
        gnorm = math.sqrt((gc ** 2).sum())
        if gnorm == 0:
            continue
        r_perm = np.abs(Vc @ gc) / (Vnorm * gnorm)         # (k,) abs correlations this permutation
        ge_self += (r_perm >= abs_obs)
        ge_max += (r_perm.max() >= abs_obs)

    out = {}
    for cid, vec in summaries.items():
        if cid not in obs:
            out[cid] = Calibration(obs.get(cid), n_units, null_sd, None, None, n_permutations, seed)
            continue
        j = ids.index(cid)
        out[cid] = Calibration(
            statistic=obs[cid], n_units=n_units, null_sd_per_test=null_sd,
            permutation_p=(1 + ge_self[j]) / (n_permutations + 1),
            scanwide_p=(1 + ge_max[j]) / (n_permutations + 1),
            n_permutations=n_permutations, seed=seed,
        )
    return out
