"""Replay executor and one-term refit (legs 2a, 2b).

What this is, and what it deliberately is not
---------------------------------------------
Legs 2a and 2b need to re-run the analyst's own model. This module fits a model from an EXPLICIT
`ModelSpec` -- family, offset, additive-reference term, linear-predictor terms -- and abstains loudly
on anything the spec cannot express. It does NOT parse arbitrary analyst code and it does NOT execute
the analyst's script. Reconstructing the structure from code is the IR/must-slicer's job; this module
is the arithmetic once the structure is known.

Two operations:

* `replay(spec, data)` -> a `Fit`. Re-fits the analyst's declared structure. Faithful replay is the
  precondition for everything downstream: if the refit does not reproduce the analyst's reported
  number, nothing else is claimed. This is REPLAY -- re-running a structure the analyst authored.

* `refit_with_term(spec, data, term)` -> a `Fit`. Adds exactly ONE human-declared term at a declared
  basis, refits, and reports the effect shift and an identification check. The term and its basis
  come from the scientist (via the CSP, upstream). The engine never chooses the term or the basis.
  This is leg 2b, and it stays a calculator: every degree of freedom it adds was named by a human.

Scope of v0: negative-binomial or Poisson likelihood with mean

    mu_i = ref_i + exposure_i * exp(linear_predictor_i)

where ref_i is an optional additive reference (contamination) term and exposure_i an optional
multiplicative offset. This is exactly the GB-P07 structure. Anything else raises Abstain.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

REPLAY_VERSION = "replay.v0"


class Abstain(Exception):
    """Raised whenever the model structure or the added term is outside v0's expressible class."""


@dataclass(frozen=True)
class ModelSpec:
    """The analyst's declared model structure. Reconstructed upstream; this module only fits it.

    response, exposure_offset, additive_reference are column names in `data`.
    predictors is the linear-predictor design: an ordered list of column names (an intercept is
    always included). target_term is the predictor whose coefficient is the reported effect.
    family is "nb" or "poisson".
    """

    response: str
    predictors: tuple            # column names entering the linear predictor (besides intercept)
    target_term: str             # which predictor's coefficient is the reported effect
    family: str = "nb"
    exposure_offset: str | None = None       # multiplicative exposure column, or None (=> 1)
    additive_reference: str | None = None     # additive contamination column, or None (=> 0)


@dataclass(frozen=True)
class AddedTerm:
    """One human-declared term for leg 2b. The engine never fills this in on its own."""

    name: str                     # column in `data` carrying the term's values
    basis: str                    # human's declared basis label, e.g. "centered_continuous"
    declared_by: str = "human"    # provenance; must not be "engine"


@dataclass(frozen=True)
class Fit:
    spec_family: str
    target_term: str
    coefficients: dict
    target_effect: float
    n_obs: int
    converged: bool
    loglik: float
    dispersion: float | None
    design_rank: int
    design_condition: float
    residuals_pearson: tuple = field(default=())

    def as_dict(self) -> dict:
        return {
            "family": self.spec_family, "target_term": self.target_term,
            "target_effect": round(self.target_effect, 6),
            "coefficients": {k: round(v, 6) for k, v in self.coefficients.items()},
            "n_obs": self.n_obs, "converged": self.converged,
            "loglik": round(self.loglik, 4),
            "dispersion": None if self.dispersion is None else round(self.dispersion, 6),
            "design_rank": self.design_rank,
            "design_condition": round(self.design_condition, 2),
        }


def _vector(data, name: str, n: int, label: str) -> np.ndarray:
    if name not in data:
        raise Abstain(f"{label} column {name!r} is not present")
    try:
        vector = np.asarray(data[name], dtype=float)
    except (TypeError, ValueError) as exc:
        raise Abstain(f"{label} {name!r} is not numeric") from exc
    if vector.ndim != 1:
        raise Abstain(f"{label} {name!r} must be one-dimensional")
    if len(vector) != n:
        raise Abstain(f"{label} {name!r} length does not match response length")
    if not np.all(np.isfinite(vector)):
        if label == "exposure offset":
            raise Abstain("exposure offset must contain only positive finite values")
        raise Abstain(f"{label} {name!r} must contain only finite values")
    return vector


def _design(data, spec: ModelSpec, n: int, extra_cols=()):
    cols = [("intercept", np.ones(n))]
    for p in spec.predictors:
        cols.append((p, _vector(data, p, n, "predictor")))
    for name, vec in extra_cols:
        try:
            extra = np.asarray(vec, dtype=float)
        except (TypeError, ValueError) as exc:
            raise Abstain(f"added term {name!r} is not numeric") from exc
        if extra.ndim != 1 or len(extra) != n:
            raise Abstain(f"added term {name!r} length does not match response length")
        if not np.all(np.isfinite(extra)):
            raise Abstain(f"added term {name!r} must contain only finite values")
        cols.append((name, extra))
    names = [c[0] for c in cols]
    X = np.column_stack([c[1] for c in cols])
    return names, X


def _fit(data, spec: ModelSpec, extra_cols=(), *, require_identified: bool = True) -> Fit:
    if spec.family == "limma_voom":
        return _fit_limma_voom(data, spec, extra_cols)
    if spec.family not in ("nb", "poisson"):
        raise Abstain(f"family {spec.family!r} outside v0 (nb|poisson|limma_voom)")
    if spec.response not in data:
        raise Abstain(f"response column {spec.response!r} is not present")
    try:
        y = np.asarray(data[spec.response], dtype=float)
    except (TypeError, ValueError) as exc:
        raise Abstain("response is not numeric") from exc
    if y.ndim != 1 or len(y) == 0:
        raise Abstain("response must be a non-empty one-dimensional vector")
    if not np.all(np.isfinite(y)):
        raise Abstain("response must contain only finite values")
    if np.any(y < 0) or np.any(y != np.floor(y)):
        raise Abstain("response is not nonnegative integer counts")
    n = len(y)
    ref = (_vector(data, spec.additive_reference, n, "additive reference")
           if spec.additive_reference else np.zeros(n))
    if np.any(ref < 0):
        raise Abstain("additive reference must be nonnegative")
    expo = (_vector(data, spec.exposure_offset, n, "exposure offset")
            if spec.exposure_offset else np.ones(n))
    if np.any(expo <= 0):
        raise Abstain("exposure offset must contain only positive finite values")
    names, X = _design(data, spec, n, extra_cols)
    if spec.target_term not in names:
        raise Abstain(f"target_term {spec.target_term!r} not in design")
    ti = names.index(spec.target_term)

    rank = int(np.linalg.matrix_rank(X))
    sv = np.linalg.svd(X, compute_uv=False)
    cond = float(sv[0] / sv[-1]) if sv[-1] > 0 else float("inf")

    k = X.shape[1]
    if require_identified and rank < k:
        raise Abstain("target coefficient is not identified by a full-rank design")

    def mu_of(beta):
        return ref + expo * np.exp(np.clip(X @ beta, -30, 30))

    if spec.family == "poisson":
        def nll(p):
            mu = np.clip(mu_of(p), 1e-9, None)
            return -np.sum(y * np.log(mu) - mu - gammaln(y + 1))
        x0 = np.zeros(k); x0[0] = math.log(max(y.mean(), 1e-3))
        res = minimize(nll, x0, method="Nelder-Mead",
                       options=dict(xatol=1e-8, fatol=1e-8, maxiter=40000))
    else:
        def nll(p):
            mu = np.clip(mu_of(p[:-1]), 1e-9, None); th = math.exp(p[-1])
            return -np.sum(gammaln(y + th) - gammaln(th) - gammaln(y + 1)
                           + th * np.log(th / (th + mu)) + y * np.log(mu / (th + mu)))
        x0 = np.zeros(k + 1); x0[0] = math.log(max(y.mean(), 1e-3)); x0[-1] = 0.0
        res = minimize(nll, x0, method="Nelder-Mead",
                       options=dict(xatol=1e-8, fatol=1e-8, maxiter=60000))

    # Nelder-Mead is stable on the small released fixtures but can stop at its iteration cap even
    # from a useful point.  A distinct deterministic optimizer gets one chance to establish actual
    # convergence; neither partial result is accepted merely because its coefficients look finite.
    if not bool(res.success) and np.all(np.isfinite(res.x)):
        res = minimize(
            nll,
            res.x,
            method="Powell",
            options=dict(xtol=1e-8, ftol=1e-8, maxiter=40000),
        )

    if not bool(res.success):
        message = getattr(res, "message", "unknown optimizer failure")
        raise Abstain(f"optimizer did not converge: {message}")
    beta = res.x if spec.family == "poisson" else res.x[:-1]
    theta = None if spec.family == "poisson" else math.exp(res.x[-1])
    if not np.all(np.isfinite(beta)) or not math.isfinite(float(res.fun)):
        raise Abstain("optimizer returned non-finite coefficients or objective")
    if theta is not None and (not math.isfinite(theta) or theta <= 0):
        raise Abstain("optimizer returned an invalid dispersion")

    mu = mu_of(beta)
    var = mu if theta is None else mu + mu ** 2 / theta
    resid = (y - mu) / np.sqrt(np.clip(var, 1e-12, None))
    if (not np.all(np.isfinite(mu)) or np.any(mu <= 0)
            or not np.all(np.isfinite(var)) or np.any(var <= 0)
            or not np.all(np.isfinite(resid))):
        raise Abstain("fit returned non-finite means, variances, or residuals")
    return Fit(
        spec_family=spec.family, target_term=spec.target_term,
        coefficients={names[i]: float(beta[i]) for i in range(k)},
        target_effect=float(beta[ti]), n_obs=n, converged=bool(res.success),
        loglik=float(-res.fun), dispersion=theta, design_rank=rank, design_condition=cond,
        residuals_pearson=tuple(float(r) for r in resid),
    )


def _fit_limma_voom(data, spec: ModelSpec, extra_cols=()) -> Fit:
    """limma-voom: a weighted linear model on log2-CPM (Law et al. 2014, Genome Biology).

    Formulas verified against the voom paper:
      * logCPM      y_gi = log2( (count_gi + 0.5) / (libsize_i + 1) * 1e6 )
      * trend       LOWESS of sqrt(residual sd_g) vs mean log-count, across genes
      * weights     w_gi = lo(fitted log-count_gi)^-4   (inverse predicted variance)
    The empirical-Bayes moderation (eBayes) does not change the coefficient, so it is not needed for
    the effect estimate or the residuals -- only for limma's moderated p-value. This replay is a
    PROXY (the exact eBayes-moderated pipeline is not reproduced); the faithfulness gate decides
    whether it reproduces the reported log2 fold change.

    Needs the full count matrix (units x genes) to fit the trend: pass it as data["__all_counts__"].
    Without it, falls back to unweighted OLS on log-CPM when a library-size offset is available; with
    neither, abstains.
    """
    from statsmodels.nonparametric.smoothers_lowess import lowess

    if spec.response not in data:
        raise Abstain(f"response column {spec.response!r} is not present")
    counts = np.asarray(data[spec.response], dtype=float)
    if counts.ndim != 1 or len(counts) == 0:
        raise Abstain("limma-voom response must be a non-empty one-dimensional vector")
    if not np.all(np.isfinite(counts)) or np.any(counts < 0):
        raise Abstain("limma-voom response is not nonnegative counts")
    n = len(counts)
    names, X = _design(data, spec, n, extra_cols)
    if spec.target_term not in names:
        raise Abstain(f"target_term {spec.target_term!r} not in design")
    ti = names.index(spec.target_term)
    rank = int(np.linalg.matrix_rank(X))
    sv = np.linalg.svd(X, compute_uv=False)
    cond = float(sv[0] / sv[-1]) if sv[-1] > 0 else float("inf")
    if rank < X.shape[1]:
        raise Abstain("target coefficient is not identified by a full-rank design")

    all_counts = data.get("__all_counts__")
    if all_counts is not None:
        M = np.asarray(all_counts, dtype=float)              # units x genes
        if M.ndim != 2 or M.shape[0] != n:
            raise Abstain("__all_counts__ rows do not match the response length")
        if not np.all(np.isfinite(M)) or np.any(M < 0):
            raise Abstain("__all_counts__ must contain finite nonnegative counts")
        lib = M.sum(axis=1)
    elif spec.exposure_offset and spec.exposure_offset in data:
        M, lib = None, _vector(data, spec.exposure_offset, n, "exposure offset")
    else:
        raise Abstain("limma-voom needs the full count matrix (__all_counts__) for the "
                      "mean-variance trend, or a library-size offset for the OLS fallback")
    if not np.all(np.isfinite(lib)) or np.any(lib <= 0):
        raise Abstain("limma-voom library sizes must be positive finite values")
    lib = np.clip(lib, 1.0, None)

    def logcpm(c):
        return np.log2((c + 0.5) / (lib + 1.0) * 1e6)

    def wls(y, w):
        Xw = X * np.sqrt(w)[:, None]
        beta, *_ = np.linalg.lstsq(Xw, y * np.sqrt(w), rcond=None)
        return beta

    weights = np.ones(n)
    if M is not None and M.shape[1] >= 5:
        # mean-variance trend across genes: initial OLS per gene on logCPM
        Yall = np.log2((M + 0.5) / (lib[:, None] + 1.0) * 1e6)   # units x genes
        beta_all, *_ = np.linalg.lstsq(X, Yall, rcond=None)      # k x genes
        resid_all = Yall - X @ beta_all
        dof = max(n - X.shape[1], 1)
        sd_g = np.sqrt((resid_all ** 2).sum(axis=0) / dof)       # genes
        mean_logcpm = Yall.mean(axis=0)                          # genes
        R_tilde = np.exp(np.log(lib + 1.0).mean())               # geometric mean of lib+1
        x_g = mean_logcpm + np.log2(R_tilde) - np.log2(1e6)      # mean log-count
        keep = sd_g > 0
        if keep.sum() >= 5:
            fit = lowess(np.sqrt(sd_g[keep]), x_g[keep], frac=0.5, return_sorted=True)
            xs, ys = fit[:, 0], fit[:, 1]
            # per-observation fitted log-count for the target gene, then predicted sqrt-sd
            beta0 = wls(logcpm(counts), np.ones(n))
            fitted_logcpm = X @ beta0
            lam = fitted_logcpm + np.log2(lib + 1.0) - np.log2(1e6)
            pred = np.interp(lam, xs, ys, left=ys[0], right=ys[-1])
            weights = np.clip(pred, 1e-6, None) ** -4

    y = logcpm(counts)
    beta = wls(y, weights)
    resid = (y - X @ beta) * np.sqrt(weights)                    # weighted residuals
    if not np.all(np.isfinite(beta)) or not np.all(np.isfinite(resid)):
        raise Abstain("limma-voom fit returned non-finite coefficients or residuals")
    return Fit(
        spec_family=spec.family, target_term=spec.target_term,
        coefficients={names[i]: float(beta[i]) for i in range(X.shape[1])},
        target_effect=float(beta[ti]), n_obs=n, converged=True,
        loglik=float("nan"), dispersion=None, design_rank=rank, design_condition=cond,
        residuals_pearson=tuple(float(r) for r in resid),
    )


def replay(spec: ModelSpec, data: dict, *, reported_effect: float | None = None,
           tol: float = 0.02) -> Fit:
    """Re-fit the analyst's declared structure. Faithful replay is the precondition for legs 2a/2b.

    If `reported_effect` is given, the replay must reproduce it within `tol` or Abstain -- an
    unfaithful replay must not be used to compute residuals or contrasts.
    """
    if not math.isfinite(float(tol)) or tol < 0:
        raise Abstain("replay tolerance must be a finite nonnegative number")
    if reported_effect is not None and not math.isfinite(float(reported_effect)):
        raise Abstain("reported effect must be finite")
    fit = _fit(data, spec)
    if reported_effect is not None and abs(fit.target_effect - reported_effect) > tol:
        raise Abstain(
            f"replay did not reproduce the reported effect: got {fit.target_effect:.4f}, "
            f"reported {reported_effect:.4f}, tol {tol}")
    return fit


def refit_with_term(spec: ModelSpec, data: dict, term: AddedTerm) -> dict:
    """Leg 2b: add ONE human-declared term, refit, report the shift and an identification check.

    Returns a contrast dict. Never chooses the term or basis -- those are in `term`, declared by the
    human. Abstains when the added term is not separately identified (§5.5): point movement under a
    rank-deficient or ill-conditioned augmented design is noise, not evidence.
    """
    if term.declared_by == "engine":
        raise Abstain("leg 2b will not run an engine-chosen term; the human must declare it")
    if term.name not in data:
        raise Abstain(f"declared term column {term.name!r} not present in bound data")

    base = _fit(data, spec)
    added_vec = np.asarray(data[term.name], dtype=float)
    aug = _fit(
        data,
        spec,
        extra_cols=((f"{term.name}[{term.basis}]", added_vec),),
        require_identified=False,
    )

    # identification: did adding the term actually increase the design rank, and is it conditioned?
    identified = aug.design_rank > base.design_rank
    well_conditioned = aug.design_condition < 1e6
    if not identified or not well_conditioned:
        return {
            "leg": "2b",
            "term": {"name": term.name, "basis": term.basis, "declared_by": term.declared_by},
            "identified": bool(identified),
            "design_condition": round(aug.design_condition, 2),
            "abstained": ("added term is not separately identified: it lies in the span of the "
                          "existing design (rank did not increase) or the augmented design is "
                          "ill-conditioned. Point movement here is not evidence."),
        }

    return {
        "leg": "2b",
        "term": {"name": term.name, "basis": term.basis, "declared_by": term.declared_by},
        "identified": True,
        "target_effect_without_term": round(base.target_effect, 6),
        "target_effect_with_term": round(aug.target_effect, 6),
        "shift": round(aug.target_effect - base.target_effect, 6),
        "added_term_coefficient": round(
            aug.coefficients[f"{term.name}[{term.basis}]"], 6),
        "design_rank_base": base.design_rank,
        "design_rank_augmented": aug.design_rank,
        "design_condition": round(aug.design_condition, 2),
        "note": "The scientist declared this term and basis; the engine only refit. The shift is a "
                "sensitivity, not a claim the augmented model is correct. Whether the term is a "
                "technical confounder to keep or a mediator to drop is the scientist's decision.",
    }
