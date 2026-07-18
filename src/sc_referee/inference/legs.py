"""Leg 2a orchestration: does a candidate predict the analyst's own residuals?

Leg 1 lives in `materialization.py`. Leg 2b lives in `replay.refit_with_term`. This module is the
middle leg: replay the analyst's model, take its residuals, and ask -- with the same permutation
calibration leg 1 uses -- whether each candidate's unit summary predicts them.

Finds UNUSED variables that predict the leftovers (e.g. a donor covariate like `sex` at 2.1 sd). Blind to a term
collinear-in-the-margin with something already fitted (`rho`, 0.4 sd), because the model already
absorbed it -- which is exactly the case leg 2b exists to catch. So a null here is NOT a clean bill,
and the record says so.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sc_referee.inference.calibration import calibrate

LEG2A_CAVEAT = (
    "A null result here does not certify that the candidate is correctly placed. A term already in "
    "the model, or collinear-in-the-margin with one, is orthogonal to the residuals by construction "
    "and scores null even when its placement changes the effect. Leg 2b (refit with the term) is the "
    "tier that adjudicates that case."
)

RESIDUAL_CONTRACT = "pearson_residual_nb_or_poisson_unit_mean"   # §5.4: pinned


@dataclass(frozen=True)
class Leg2aResult:
    residual_contract: str
    candidates: tuple           # per candidate: name, r, calibration
    caveat: str

    def as_dict(self) -> dict:
        return {
            "leg": "2a",
            "residual_contract": self.residual_contract,
            "candidates": list(self.candidates),
            "caveat": self.caveat,
        }


def leg2a(fit, obs_unit, candidate_unit_summaries: dict, *, n_permutations=10000,
          seed=20260717) -> Leg2aResult:
    """Correlate each candidate's unit summary with the fitted model's unit-mean residuals.

    `fit` is a `replay.Fit` (carries per-observation Pearson residuals). `obs_unit` is the per-obs
    unit label aligned to those residuals. `candidate_unit_summaries` maps candidate name -> its
    per-unit summary indexed by unit label.
    """
    resid = np.asarray(fit.residuals_pearson, dtype=float)
    obs_unit = np.asarray(obs_unit)
    units = list(dict.fromkeys(obs_unit))
    resid_by_unit = np.array([resid[obs_unit == u].mean() for u in units], dtype=float)

    # align every candidate onto the same unit order; the residual vector plays the "exposure" role
    aligned = {}
    for name, summ in candidate_unit_summaries.items():
        vec = np.array([summ.get(u, np.nan) for u in units], dtype=float)
        if np.isfinite(vec).all():
            aligned[name] = vec

    cal = calibrate(aligned, resid_by_unit, n_permutations=n_permutations, seed=seed)
    cands = tuple(
        {"name": name, **cal[name].as_dict()}
        for name in aligned
    )
    return Leg2aResult(residual_contract=RESIDUAL_CONTRACT, candidates=cands, caveat=LEG2A_CAVEAT)
