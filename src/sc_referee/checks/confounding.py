"""The `confounding` check — the guaranteed, power-INDEPENDENT blocker.

Exact design-matrix algebra on a sample-level factor table. Never a power question, never
an LLM opinion. It answers two distinct questions and reports both as numbers:

  1. ESTIMABILITY (blocker).  Is the target coefficient identified at all? Judged by the RANK
     of the ADDITIVE design matrix the analyst actually fits — equivalently R²(target ~ nuisance) == 1.
     If so, no model — not a better one, not an LLM's — can separate them. Re-run the experiment.

  2. DEGREE + BIAS (major/pass).  Partial confounding is a continuum, and whether it hurts you
     depends on whether you ADJUSTED for the nuisance:
        · nuisance in the model  -> the estimate is unbiased; you merely pay variance inflation (VIF).
        · nuisance omitted       -> omitted-variable bias: the target coefficient absorbs
                                    λ × (nuisance effect), where λ is the OVB multiplier.

Why NOT joint-stratum co-occurrence (the previous implementation)? Because it stratifies by the
SATURATED (interaction) combination of nuisance columns, while real models are ADDITIVE. With ≥2
nuisance columns those diverge: condition = XOR(run, sex) makes every joint (run,sex) stratum pure,
yet `~ run + sex + condition` is full rank and condition is orthogonal to both main effects
(R²=0, VIF=1). The old rule emitted a FALSE BLOCKER there — the worst error this tool can make.
Likewise the old `min_cell == 1` clause conflated *small* with *confounded*, false-flagging a
perfectly balanced design. Both removed. (Reviewed adversarially 2026-07-07.)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from enum import Enum

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.design import Design, confidence_high, model_terms
from sc_referee.design_matrix import DesignMatrixError, build_fixed_effect_matrix

CHECK_ID = "confounding"

# R² at (or numerically indistinguishable from) 1 means the target is aliased: not estimable.
# This is the ONLY threshold that is mathematics rather than policy.
ALIAS_TOL = 1e-8

# --- the two policy cuts. Both are choices, not laws. The measured numbers (r2, vif,
# leakage) are ALWAYS reported in `metrics` and named in the verdict, whatever the cut does,
# so a reader can disagree with the threshold without being denied the evidence. ---

# The OMITTED block explains ≥ this share of the target's residual variance ⇒ materially biasing.
# We decide on PARTIAL R², not on max|λ|: λ_j is per-dummy and shrinks mechanically as the nuisance
# gains levels (λ_j ≈ 2/n_levels for condition-pure levels). A 40-run batch perfectly aliased with
# condition yields max|λ| = 0.053 — under the old 0.10 cut — while R² = 1.0. Partial R² is
# cardinality-invariant. For a balanced binary nuisance, λ = corr, so R² = 0.01 reproduces the old
# λ ≥ 0.10 behaviour exactly. (Opus review 2026-07-08.)
OMITTED_R2_MAJOR = 0.01
# Float64 least-squares decisions use an error envelope of 64 machine epsilons and a
# 64x safety margin.  4096 * eps = 9.094947017729282e-13: narrow enough that 0.009
# and 0.011 remain distinct, while covering the observed 1e-15..1e-14 categorical error.
PARTIAL_R2_NUMERIC_POLICY_VERSION = "partial-r2-decision-v2"
PARTIAL_R2_LSTSQ_ERROR_ENVELOPE = 64 * np.finfo(np.float64).eps
PARTIAL_R2_CUT_EPSILON = 64 * PARTIAL_R2_LSTSQ_ERROR_ENVELOPE
# λ is still reported PER TERM as the interpretable bias multiplier (adversarial review: do not collapse it).
LEAKAGE_MAJOR = 0.10  # retained only for the prose threshold quoted to the user

# VIF ≥ this ⇒ near-collinear. If the nuisance IS adjusted for, this is an EFFICIENCY cost
# (SE inflated ×sqrt(VIF)), not a confound — so it is `informational` and never fails CI.
# 10 is the classical convention (SE inflated ×3.2).
VIF_ADVISORY = 10.0


class PartialR2Decision(str, Enum):
    MATERIAL = "material"
    IMMATERIAL = "immaterial"
    INDETERMINATE_NEAR_CUT = "indeterminate_near_cut"


def decide_partial_r2(value: float, cut: float = OMITTED_R2_MAJOR) -> PartialR2Decision:
    if abs(float(value) - float(cut)) <= PARTIAL_R2_CUT_EPSILON:
        return PartialR2Decision.INDETERMINATE_NEAR_CUT
    return (PartialR2Decision.MATERIAL if value >= cut
            else PartialR2Decision.IMMATERIAL)


def nuisance_columns(design: Design) -> list:
    """`nuisance = (every model term except the target) ∪ declared batch`.

    `replicate_unit` (donor) is deliberately NOT unioned in unconditionally — that would
    false-flag every valid *unpaired* design. Donor enters only when it is a model term,
    where an unpaired design genuinely is rank-deficient and SHOULD block.
    """
    contrast_col, _, _ = design.contrast_column_and_levels()
    nuis = (model_terms(design.model) - {design.target_term}) | set(design.batch)
    nuis.discard(contrast_col)
    return sorted(nuis)


def _subset(observations: pd.DataFrame, design: Design) -> pd.DataFrame:
    obs = observations
    if design.subset:
        for col, val in design.subset.items():
            if col in obs.columns:
                obs = obs[obs[col] == val]
    return obs


def _decategorize(df: pd.DataFrame) -> pd.DataFrame:
    """Cast Categorical columns (as AnnData .obs round-trips them) to object, so set logic
    never sees phantom zero-count levels."""
    for c in df.columns:
        if isinstance(df[c].dtype, pd.CategoricalDtype):
            df[c] = df[c].astype(object)
    return df


def build_sample_factor_table(observations: pd.DataFrame, design: Design) -> pd.DataFrame:
    """One row per pseudobulk sample (grouped by sample_unit), carrying the contrast +
    nuisance factors — built BEFORE aggregating anything away."""
    obs = _subset(observations, design)
    contrast_col, _, _ = design.contrast_column_and_levels()
    carry = [c for c in dict.fromkeys([contrast_col, *nuisance_columns(design)]) if c in obs.columns]
    keys = [c for c in design.sample_unit if c in obs.columns]
    if not keys:
        return _decategorize(obs[carry].reset_index(drop=True))
    carry_non_key = [c for c in carry if c not in keys]
    grouped = obs.groupby(keys, sort=False, observed=True)[carry_non_key].first().reset_index()
    return _decategorize(grouped)


def covariates_constant_within_sample_unit(observations: pd.DataFrame, design: Design):
    """Every nuisance covariate must be constant within a sample_unit group, else the
    pseudobulk sample is ill-defined. Returns (ok, offending_col)."""
    obs = _subset(observations, design)
    keys = [c for c in design.sample_unit if c in obs.columns]
    if not keys:
        return True, None
    cols = [c for c in nuisance_columns(design) if c in obs.columns and c not in keys]
    for col in cols:
        if (obs.groupby(keys, sort=False, observed=True)[col].nunique() > 1).any():
            return False, col
    return True, None


# --------------------------------------------------------------------------- #
# design-matrix algebra
# --------------------------------------------------------------------------- #
# Equilibrate the least-squares solve only when column L2 norms differ by more than this ratio.
# Below it, scales are comparable and `lstsq` is already reliable, so we solve RAW — keeping results
# byte-identical to the established (frozen) outputs. Categorical dummy/intercept norm ratios are
# tiny (≈√n); the exact affine aliases equilibration recovers arise only at ratios ≥ ~1e9 (F1).
_EQUILIBRATION_TRIGGER = 1e6

# KNOWN NUMERICAL BOUNDARIES (documented; below any realistic single-cell covariate). A near-alias
# hidden in a sub-2^-44 coefficient direction of a comparably-scaled column can be missed by the raw
# solve (F1), and denormal covariate magnitudes (|x| < ~1e-308) are not conditioned (F2). Both need
# covariate values no real dataset produces; genuine large-scale and small-scale (down to ~1e-20)
# aliases DO block. Closing these fully requires always-equilibrated fits with an abstain-on-unresolved
# -near-dependence policy — deferred as out of scope for the continuous-covariate false-blocker fix.


def _column_l2_norms(A: np.ndarray) -> np.ndarray:
    """Per-column Euclidean norms, overflow-safe for extreme magnitudes; a zero column -> 1.0 so
    equilibration leaves it untouched."""
    A = np.asarray(A, dtype=float)
    scale = np.abs(A).max(axis=0)
    scale = np.where(np.isfinite(scale) & (scale > 0), scale, 1.0)
    norms = scale * np.sqrt(((A / scale) ** 2).sum(axis=0))
    return np.where(np.isfinite(norms) & (norms > 0), norms, 1.0)


def _equilibrated_lstsq(A: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Least-squares coefficients for A x ≈ b, solved on UNIT-NORM-EQUILIBRATED columns and returned
    in ORIGINAL coordinates. Column equilibration is exact — it changes neither the fitted values nor
    R² — but prevents predictors of wildly different scale from making `lstsq` discard a real
    direction (F1). The response b is never scaled."""
    A = np.asarray(A, dtype=float)
    b = np.asarray(b, dtype=float)
    if A.shape[1] == 0:
        return np.zeros((0,) if b.ndim == 1 else (0, b.shape[1]))
    norms = _column_l2_norms(A)
    if norms.max() <= _EQUILIBRATION_TRIGGER * norms.min():
        beta, *_ = np.linalg.lstsq(A, b, rcond=None)     # comparable scales: raw, byte-stable solve
        return beta
    beta_scaled, *_ = np.linalg.lstsq(A / norms, b, rcond=None)
    return beta_scaled / norms[:, None] if beta_scaled.ndim == 2 else beta_scaled / norms


def _design_block(samples: pd.DataFrame, cols, continuous=()) -> tuple[np.ndarray, tuple[str, ...]]:
    """The additive design sub-matrix for `cols` (no intercept) + its canonical column ids, built by
    the CANONICAL `build_fixed_effect_matrix`: a covariate the ratified `column_kinds` declares
    CONTINUOUS enters as its numeric column (then mean-centered here for conditioning); every other
    covariate is treatment-coded (drop-first) dummies dropping the SAME reference level pandas would
    (sorted-first), preserving the established categorical encoding and reported leakage. Delegating
    construction gives ONE validation boundary — boolean, missing, non-finite, or non-numeric
    declared-continuous inputs raise DesignMatrixError (the caller abstains, F2/F4) — and
    collision-proof unique column ids (F3). One-hot-coding a continuous covariate would manufacture a
    spurious perfect alias, a false BLOCKER (F8)."""
    cols = list(cols)
    n = len(samples)
    if not cols:
        return np.empty((n, 0)), ()
    continuous = set(continuous)
    frame, kinds, levels = {}, {}, {}
    for col in cols:
        key = str(col)
        if col in continuous:
            series = samples[col]
            if pd.api.types.is_integer_dtype(series.dtype):
                raw = series.to_numpy()
                if not np.array_equal(raw, raw.astype("float64").astype(raw.dtype)):
                    # >2^53 integers collapse on the float64 cast and can manufacture a false alias;
                    # abstain rather than test estimability on corrupted values (F6).
                    raise DesignMatrixError(
                        f"integer continuous source {key!r} is not exactly representable in float64")
            frame[key] = series                             # raw — the builder validates it
            kinds[key] = "continuous"
        else:
            values = samples[col].astype(str)
            frame[key] = values
            kinds[key] = "categorical"
            levels[key] = tuple(sorted(set(values)))        # drop-first reference = pandas' sorted-first
    rows = pd.DataFrame(frame, index=samples.index)
    built = build_fixed_effect_matrix(
        rows, source_columns=tuple(str(c) for c in cols),
        column_kinds=kinds, categorical_levels=levels, intercept=False,
    )
    matrix = np.array(built.matrix, dtype=float)            # writable copy
    for cid, idxs in built.source_slices.items():
        if kinds.get(cid) == "continuous":
            for j in idxs:
                matrix[:, j] = matrix[:, j] - matrix[:, j].mean()
    if not np.isfinite(matrix).all():                       # e.g. ~1e308 values overflow on centering
        raise DesignMatrixError("non-finite continuous design column after centering")
    # Preserve the ESTABLISHED per-term ids (pandas `{col}_{level}` / `{col}`) so the reported leakage
    # dict — a frozen public contract — is byte-identical to the previous encoder; the builder's own
    # `{col}[level=..]` ids collide-check construction only.
    legacy_ids: list[str] = []
    for col in cols:
        key = str(col)
        if col in continuous:
            legacy_ids.append(key)
        else:
            legacy_ids.extend(f"{key}_{level}" for level in levels[key][1:])
    return matrix, tuple(legacy_ids)


def _dummy_block(samples: pd.DataFrame, cols, continuous=()) -> np.ndarray:
    """Back-compat accessor for the encoded design matrix alone (used by sibling-check tests)."""
    return _design_block(samples, cols, continuous)[0]


def _with_intercept(block: np.ndarray, n: int) -> np.ndarray:
    return np.column_stack([np.ones(n), block]) if block.size else np.ones((n, 1))


def _r2(t: np.ndarray, Z: np.ndarray):
    """R² of regressing the target indicator on the nuisance design matrix. None if no variation."""
    tss = float(((t - t.mean()) ** 2).sum())
    if tss <= 0:
        return None
    beta = _equilibrated_lstsq(Z, t)
    rss = float(((t - Z @ beta) ** 2).sum())
    return float(min(max(1.0 - rss / tss, 0.0), 1.0))


def _leakage(samples: pd.DataFrame, t: np.ndarray, w_cols, o_cols, continuous=()) -> dict:
    """The omitted-variable-bias multiplier per omitted encoded term (dummy or continuous).

    λ_j = coefficient on the target when regressing omitted term z_j on [1, included W, t].
    Then  E[β̂_target,unadjusted] = β_target + Σ_j γ_j · λ_j.
    Reported per term (adversarial review: do not collapse to a scalar as the primary output).
    """
    o_cols = list(o_cols)
    if not o_cols:
        return {}
    n = len(samples)
    W, _ = _design_block(samples, w_cols, continuous)
    X = np.column_stack([_with_intercept(W, n), t])
    Od, ids = _design_block(samples, o_cols, continuous)
    out = {}
    for j, name in enumerate(ids):                          # positional access — collision-proof (F3)
        key = str(name)
        while key in out:                                   # disambiguate a pathological id collision
            key += "#"                                      # so no λ is silently dropped
        out[key] = float(_equilibrated_lstsq(X, Od[:, j])[-1])   # coefficient on t, back-transformed
    return out


def _partial_r2(samples: pd.DataFrame, t: np.ndarray, included, omitted, continuous=()) -> float:
    """R² of the target on the OMITTED nuisance block, after residualizing both on the covariates
    the model DOES include. Cardinality-invariant, unlike max|λ|."""
    omitted = list(omitted)
    if not omitted:
        return 0.0
    n = len(samples)
    Wblk, _ = _design_block(samples, included, continuous)
    W = _with_intercept(Wblk, n)

    def resid(Y):
        return Y - W @ _equilibrated_lstsq(W, Y)

    t_res = resid(t)
    tss = float((t_res ** 2).sum())
    if tss <= 1e-12:
        return 0.0
    Z, _ = _design_block(samples, omitted, continuous)
    if Z.size == 0:
        return 0.0
    Z_res = resid(Z)
    beta = _equilibrated_lstsq(Z_res, t_res)
    rss = float(((t_res - Z_res @ beta) ** 2).sum())
    return float(min(max(1.0 - rss / tss, 0.0), 1.0))


def shares_common_support(samples, contrast_col, reference, test, nuisance) -> bool:
    """Do reference and test co-occur within at least one JOINT nuisance stratum?

    Retained as a *diagnostic* only: its failure means the target is aliased with the
    nuisance INTERACTION. That does not imply the additive model fails to identify it.
    """
    nuis = [c for c in nuisance if c in samples.columns and c != contrast_col]
    if not nuis:
        present = set(samples[contrast_col])
        return reference in present and test in present
    for _, grp in samples.groupby(nuis, sort=False, observed=True):
        levels = set(grp[contrast_col])
        if reference in levels and test in levels:
            return True
    return False


def _f(status, verdict, *, coverage=S.COMPLETE, judgment=None, **metrics) -> Finding:
    if judgment is None:
        judgment = {S.BLOCKER: S.VIOLATION, S.MAJOR: S.CONCERN, S.PASS: S.CONFORMANT}.get(status)
    return Finding(CHECK_ID, status, verdict, metrics=metrics, citations=CITATIONS[CHECK_ID],
                   coverage=coverage, judgment=judgment)


def _cols(names) -> str:
    """Column names as plain English — 'a', 'a and b', 'a, b, and c' — never a ['list'] literal.
    The reader may be auditing agentically-generated code and not recognize their own variables."""
    names = [str(n) for n in names]
    if not names:
        return "a technical variable"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def evaluate_confounding(observations: pd.DataFrame, design: Design) -> Finding:
    declaration = design.fitted_design
    # Covariates the fitted design declares CONTINUOUS enter the design matrix as their numeric
    # column, not n-1 dummies (F8). Trust `column_kinds` ONLY when the declaration is itself ratified
    # (high confidence): an unratified type claim must not change a structural verdict — neither
    # suppress nor manufacture a blocker (F3). Unratified/absent -> categorical encoding as before.
    continuous = frozenset(
        col for col, kind in (getattr(declaration, "column_kinds", None) or {}).items()
        if kind == "continuous"
    ) if confidence_high(design, "fitted_design") else frozenset()
    upstream = [] if declaration is None else [
        batch for batch in design.batch
        if batch in declaration.batch_modeling
        and declaration.batch_modeling[batch].modeled_as == "upstream_handled"
        and declaration.batch_modeling[batch].field_confidence.get("modeled_as") == "high"
    ]
    if upstream:
        return _f(
            S.NOT_AUDITED,
            "batch corrected upstream — a design-matrix check cannot verify it",
            coverage=S.NOT_RUN,
            machine_reason="upstream_handling_not_independently_certified",
            upstream_handled_batches=upstream,
        )
    blocking_allowed = design.confirmed_by_human and confidence_high(design, "condition")
    contrast_col, reference, test = design.contrast_column_and_levels()

    ok, offending = covariates_constant_within_sample_unit(observations, design)
    if not ok:
        return _f(S.NEEDS_EVIDENCE,
                  f"a variable ({offending}) changes within a single sample, so I can't build one clean "
                  f"row per sample to test — I didn't check confounding. Make {offending} constant "
                  f"within each sample (or drop it from the design) and re-run.",
                  coverage=S.NOT_RUN)

    samples = build_sample_factor_table(observations, design)
    present = set(samples[contrast_col].unique()) if contrast_col in samples.columns else set()
    nuisance = nuisance_columns(design)

    # A declared level that is absent is a CONFIG error, not a scientific one. It is raised by
    # `validate_design_against` at audit time. If we somehow reach here, abstain — and never
    # fabricate `r2`/`vif`, in the one module that promises the numbers are always MEASURED.
    # (Opus review 2026-07-08.)
    if reference not in present or test not in present:
        return _f(S.NEEDS_EVIDENCE,
                  f"the declared contrast levels are not both present ({reference!r} vs {test!r}) — "
                  f"this is a configuration error, not a finding about the science",
                  coverage=S.NOT_RUN, nuisance=nuisance)

    sub = samples[samples[contrast_col].isin([reference, test])].reset_index(drop=True)
    t = (sub[contrast_col] == test).to_numpy(dtype=float)
    if t.min() == t.max():
        return _f(S.NEEDS_EVIDENCE,
                  "the target has no variation after subsetting (only one level present) — "
                  "a configuration error, not a finding about the science",
                  coverage=S.NOT_RUN, nuisance=nuisance)

    nuis_present = [c for c in nuisance if c in sub.columns]
    # A ratified fitted design must declare the kind of every fitted-model nuisance term; if it is
    # confirmed high-confidence yet omits one, the design matrix cannot be built soundly — abstain
    # rather than default it to categorical and manufacture a false blocker (missing_column_kind).
    if declaration is not None and confidence_high(design, "fitted_design"):
        undeclared = [c for c in nuis_present
                      if c in model_terms(design.model) and c not in declaration.column_kinds]
        if undeclared:
            return _f(S.NEEDS_EVIDENCE,
                      f"your confirmed fitted design does not declare whether {_cols(undeclared)} "
                      f"is continuous or categorical, so I can't build the design matrix to test "
                      f"estimability — declare the missing column kind(s) and re-run.",
                      coverage=S.NOT_RUN, nuisance=nuis_present)
        # A ratified categorical level ledger is a contract. If the data show a level it does not list,
        # or list a level the data never show (checked against the FULL sample table), that is a
        # configuration inconsistency — abstain rather than silently re-derive the ledger from observed
        # values and risk a false blocker (F4). The design-matrix ENCODING still uses sorted observed
        # levels, so reported leakage stays byte-stable.
        for col in nuis_present:
            ledger = declaration.categorical_levels.get(col)
            if ledger is None:
                continue
            try:
                if len({str(level) for level in ledger}) != len(ledger):
                    # Type-distinct ratified levels that collide under the sorted-string encoding
                    # (e.g. 1 and "1") cannot be represented distinctly by the algebra below, which
                    # would silently merge them and miss a real alias — abstain instead.
                    raise DesignMatrixError("ratified categorical levels collide under string encoding")
                # Typed canonical validation through the same builder: rejects a present-but-unlisted or
                # globally-unused level, missing values, and type-distinct observations that string
                # normalization would conflate (e.g. None→"None", int 1 vs level "1"). The matrix is
                # discarded — the algebra below keeps the sorted-observed encoding for byte-stable metrics.
                build_fixed_effect_matrix(
                    pd.DataFrame({str(col): samples[col]}),
                    source_columns=(str(col),), column_kinds={str(col): "categorical"},
                    categorical_levels={str(col): tuple(ledger)}, intercept=False,
                )
            except DesignMatrixError:
                return _f(S.NEEDS_EVIDENCE,
                          f"the observed levels of {col} do not match your confirmed design's declared "
                          f"levels for it (or contain missing values), so I can't build the design "
                          f"matrix to test estimability — reconcile the levels and re-run.",
                          coverage=S.NOT_RUN, nuisance=nuis_present)

    # Which nuisance did the ANALYST actually adjust for? This is their confirmed fitted-design
    # capture, not the referee's recompute formula. A missing or field-specifically unratified set
    # cannot support an omitted-variable accusation (G4/G5).
    adjusted_labels_valid = (design.analyst_adjusted_for is not None
                             and all(item in observations.columns
                                     for item in design.analyst_adjusted_for))
    adjusted_ratified = (adjusted_labels_valid
                         and confidence_high(design, "analyst_adjusted_for"))
    if adjusted_ratified:
        included = sorted(
            (set(design.analyst_adjusted_for) - {design.target_term}) & set(sub.columns)
        )
        omitted = sorted((set(design.batch) & set(sub.columns)) - set(included))
    else:
        included = None
        omitted = []

    try:
        r2 = _r2(t, _with_intercept(_design_block(sub, nuis_present, continuous)[0], len(sub)))
        leakage = _leakage(sub, t, included, omitted, continuous)
        omitted_r2 = _partial_r2(sub, t, included, omitted, continuous)   # the DECISION statistic
    except DesignMatrixError as exc:
        # A declared-continuous covariate that is non-numeric / non-finite / boolean (or otherwise not
        # a valid fitted-design source) cannot form a design matrix. Abstain as a configuration error —
        # never a dummy-coded false blocker, never an SVD crash (F2/F4).
        return _f(S.NEEDS_EVIDENCE,
                  f"I can't build the design matrix to test estimability ({exc}); check that the "
                  f"declared-continuous covariates are finite numeric values, then re-run.",
                  coverage=S.NOT_RUN, nuisance=nuis_present)
    aliased = r2 is not None and r2 >= 1.0 - ALIAS_TOL
    vif = float("inf") if aliased else 1.0 / (1.0 - r2)
    max_leak = max((abs(v) for v in leakage.values()), default=0.0)

    # target aliased with the nuisance INTERACTION, but additively identified -> report, never block
    interaction_aliased = (not aliased) and not shares_common_support(
        sub, contrast_col, reference, test, nuis_present)

    metrics = dict(nuisance=nuis_present, included=included or [], omitted=omitted,
                   r2=r2, vif=vif, leakage=leakage, max_leakage=max_leak,
                   omitted_partial_r2=round(omitted_r2, 6),
                   interaction_aliased=interaction_aliased)
    if not adjusted_ratified:
        metrics["analyst_model_captured"] = False

    if aliased:
        if not blocking_allowed:
            return _f(S.NEEDS_EVIDENCE,
                      f"the condition ({contrast_col}) looks perfectly entangled with a technical "
                      f"variable ({_cols(nuis_present)}) — but you haven't confirmed the design yet, so "
                      f"I won't hard-block on it. Confirm the design (sc-referee confirm) to make this a "
                      f"blocking verdict.", coverage=S.NOT_RUN,
                      **metrics)
        return _f(S.BLOCKER,
                  f"the condition you're comparing ({contrast_col}) is perfectly entangled with a "
                  f"technical variable ({_cols(nuis_present)}): every {contrast_col} group falls in a "
                  f"different {_cols(nuis_present)}. Because they line up exactly (R²=1.00), no "
                  f"statistical model can separate the biological effect from the batch effect — this "
                  f"comparison isn't estimable as the data were collected. It would need to be re-run "
                  f"with each {contrast_col} spread across more than one {_cols(nuis_present)}.",
                  **metrics)

    if not blocking_allowed:
        return _f(S.NEEDS_EVIDENCE,
                  f"I measured how tangled the condition ({contrast_col}) is with the technical "
                  f"variables, but you haven't confirmed the design yet, so I can't render a firm "
                  f"verdict. Confirm the design (sc-referee confirm) and re-run.",
                  coverage=S.NOT_RUN, **metrics)

    if included is None:
        # Uncaptured/unratified analyst model: we cannot judge omission. This is a COVERAGE gap, not a
        # concern — NEEDS_EVIDENCE with coverage=NOT_RUN so it renders as "needs your input" (not
        # FLAGGED). INFORMATIONAL would render FLAGGED and false-flag a clean analysis (specificity bug).
        return _f(
            S.NEEDS_EVIDENCE,
            f"I measured how tangled the condition ({contrast_col}) is with the technical variables, "
            f"but I couldn't read which covariates your analysis's model actually adjusted for, so I "
            f"can't yet tell whether a confounder was left out. Tell me your model's covariates "
            f"(sc-referee confirm) and I'll check it.",
            coverage=S.NOT_RUN,
            **metrics,
        )

    partial_r2_decision = decide_partial_r2(omitted_r2)

    if omitted and partial_r2_decision is PartialR2Decision.INDETERMINATE_NEAR_CUT:
        return _f(
            S.NOT_AUDITED,
            "the exposure-batch partial R-squared is at the materiality threshold within "
            "float64 least-squares numerical error, so the omission decision was not audited",
            coverage=S.NOT_RUN,
            machine_reason="partial_r2_indeterminate_near_cut",
            partial_r2_decision=partial_r2_decision.value,
            partial_r2_numeric_policy=PARTIAL_R2_NUMERIC_POLICY_VERSION,
            partial_r2_cut_epsilon=PARTIAL_R2_CUT_EPSILON,
            **metrics,
        )

    if omitted and partial_r2_decision is PartialR2Decision.MATERIAL:
        worst = max(leakage, key=lambda k: abs(leakage[k])) if leakage else None
        lam = f" (worst term λ={leakage[worst]:.2f} on {worst})" if worst else ""
        # Don't editorialise the price of the fix — ×1.15 is cheap, ×3.24 is not.
        pricey = (f" (though the design is also near-collinear, VIF={vif:.1f} — separable, "
                  f"but expensively)") if vif >= VIF_ADVISORY else ""
        return _f(S.MAJOR,
                  f"the condition you're comparing ({contrast_col}) is partly confounded with a "
                  f"technical variable ({_cols(omitted)}) that your model leaves out: {_cols(omitted)} "
                  f"explains {omitted_r2:.0%} of the {contrast_col} differences your model doesn't "
                  f"already account for{lam}. This one is fixable — unlike a full entanglement, the "
                  f"two can still be separated: add {omitted[0]} to your model. The cost is a "
                  f"×{np.sqrt(vif):.2f} widening of the error bars{pricey}.",
                  **metrics)

    # Below the flagging cut we still SAY what we measured — the threshold decides the status,
    # never whether the reader gets the evidence.
    weak = ""
    if omitted:
        weak = (f" · {omitted[0]} is left out of your model, but it's only weakly tied to "
                f"{contrast_col} (partial R²={omitted_r2:.3f}, below the {OMITTED_R2_MAJOR:.2f} "
                f"threshold where we'd flag it — a policy cut we chose, not a hard law)")
    interaction = ""
    if interaction_aliased:
        interaction = (f" · heads-up: {contrast_col} is entangled with the combination of "
                       f"{_cols(nuis_present)} (their interaction), which your model doesn't include — "
                       f"we're reporting it, not blocking on it")

    if vif >= VIF_ADVISORY:
        # Only an ADJUSTED nuisance makes collinearity a mere efficiency cost. If a nuisance is
        # omitted we must not say "not a confound" — we reach here only because its partial R² is
        # negligible, so say exactly that instead. (Opus review 2026-07-08.)
        gloss = ("That's an efficiency cost, not a confound — reported, never blocking."
                 if not omitted else
                 "Adjusting is expensive here, but the left-out term is barely tied to the condition.")
        status = S.PASS if not omitted else S.INFORMATIONAL
        return _f(status,
                  f"the condition you're comparing ({contrast_col}) can be estimated, but it's nearly "
                  f"redundant with the technical variable {_cols(nuis_present)} (R²={r2:.2f}, "
                  f"VIF={vif:.1f}): correcting for it widens the error bars ×{np.sqrt(vif):.1f}. "
                  f"{gloss}{weak}{interaction}",
                  **metrics)

    if omitted:
        return _f(
            S.PASS,
            f"the measured conditional exposure–batch association is below the frozen "
            f"{OMITTED_R2_MAJOR:.2f} policy threshold (partial R²={omitted_r2:.3f}); the condition "
            f"coefficient is estimable in this additive design (R²={r2:.2f}, VIF={vif:.1f}). "
            f"This check did not measure batch effects on outcomes or rule out omitted-variable "
            f"bias.{interaction}",
            **metrics,
        )
    return _f(S.PASS,
              f"the condition you're comparing ({contrast_col}) is cleanly estimable against the "
              f"technical variables (R²={r2:.2f}; correcting for them costs only ×{np.sqrt(vif):.2f} "
              f"on the error bars){interaction}",
              **metrics)


class ConfoundingCheck:
    """Registry-facing wrapper. Reads only `bundle.observations`."""

    id = CHECK_ID
    analysis_types = ("condition_contrast_DE",)
    audit_dimensions = ("conditioning_set",)
    proof_basis = "design-matrix algebra"
    contract_fields = ("condition", "reference", "test", "batch", "model",
                       "analyst_adjusted_for", "target_coefficient", "subset", "fitted_design")
    max_status = S.BLOCKER   # structural, power-independent: an aliased design is not estimable

    def applies_to(self, design: Design, bundle) -> bool:
        return design.analysis_type in self.analysis_types

    def cannot_evaluate(self, design: Design, bundle):
        return None   # needs only .obs; if the design is unrealizable, validate_design_against raises

    def run(self, design: Design, bundle, reported=None) -> Finding:
        return evaluate_confounding(bundle.observations, design)
