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
perfectly balanced design. Both removed. (Reviewed w/ Codex 2026-07-07.)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from enum import Enum

from sc_referee import statuses as S
from sc_referee.checks.base import Finding
from sc_referee.citations import CITATIONS
from sc_referee.design import Design, confidence_high, model_terms

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
# λ is still reported PER TERM as the interpretable bias multiplier (Codex: do not collapse it).
LEAKAGE_MAJOR = 0.10  # retained only for the prose threshold quoted to the user
# The public metric numbers are rounded to this many decimals before serialization. The measured
# values carry float64 last-digit noise that differs across BLAS builds (e.g. 0.0 vs 9.4e-17, or
# 1.0000000000000004 vs 1.0000000000000002 across macOS/Linux); rounding makes the public bytes
# byte-identical across platforms. Decisions still use the RAW values (this only shapes the report).
METRIC_DECIMALS = 6


def _canon(x):
    """Round a reported float to a platform-stable precision; pass through inf / non-floats."""
    if isinstance(x, float) and np.isfinite(x):
        return round(x, METRIC_DECIMALS)
    return x

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
def _dummy_block(samples: pd.DataFrame, cols) -> np.ndarray:
    """Additive, treatment-coded (drop-first) dummies — matching how the model is fit."""
    cols = list(cols)
    if not cols:
        return np.empty((len(samples), 0))
    D = pd.get_dummies(samples[cols].astype(str), columns=cols, drop_first=True)
    return D.to_numpy(dtype=float) if D.shape[1] else np.empty((len(samples), 0))


def _with_intercept(block: np.ndarray, n: int) -> np.ndarray:
    return np.column_stack([np.ones(n), block]) if block.size else np.ones((n, 1))


def _r2(t: np.ndarray, Z: np.ndarray):
    """R² of regressing the target indicator on the nuisance design matrix. None if no variation."""
    tss = float(((t - t.mean()) ** 2).sum())
    if tss <= 0:
        return None
    beta, *_ = np.linalg.lstsq(Z, t, rcond=None)
    rss = float(((t - Z @ beta) ** 2).sum())
    return float(min(max(1.0 - rss / tss, 0.0), 1.0))


def _leakage(samples: pd.DataFrame, t: np.ndarray, w_cols, o_cols) -> dict:
    """The omitted-variable-bias multiplier per omitted nuisance dummy.

    λ_j = coefficient on the target when regressing omitted dummy z_j on [1, included W, t].
    Then  E[β̂_target,unadjusted] = β_target + Σ_j γ_j · λ_j.
    Reported per term (Codex: do not collapse to a scalar as the primary output).
    """
    o_cols = list(o_cols)
    if not o_cols:
        return {}
    n = len(samples)
    X = np.column_stack([_with_intercept(_dummy_block(samples, w_cols), n), t])
    Od = pd.get_dummies(samples[o_cols].astype(str), columns=o_cols, drop_first=True)
    out = {}
    for name in Od.columns:
        z = Od[name].to_numpy(dtype=float)
        beta, *_ = np.linalg.lstsq(X, z, rcond=None)
        out[str(name)] = float(beta[-1])  # coefficient on t
    return out


def _partial_r2(samples: pd.DataFrame, t: np.ndarray, included, omitted) -> float:
    """R² of the target on the OMITTED nuisance block, after residualizing both on the covariates
    the model DOES include. Cardinality-invariant, unlike max|λ|."""
    omitted = list(omitted)
    if not omitted:
        return 0.0
    n = len(samples)
    W = _with_intercept(_dummy_block(samples, included), n)

    def resid(Y):
        beta, *_ = np.linalg.lstsq(W, Y, rcond=None)
        return Y - W @ beta

    t_res = resid(t)
    tss = float((t_res ** 2).sum())
    if tss <= 1e-12:
        return 0.0
    Z = _dummy_block(samples, omitted)
    if Z.size == 0:
        return 0.0
    Z_res = resid(Z)
    beta, *_ = np.linalg.lstsq(Z_res, t_res, rcond=None)
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
    r2 = _r2(t, _with_intercept(_dummy_block(sub, nuis_present), len(sub)))
    aliased = r2 is not None and r2 >= 1.0 - ALIAS_TOL
    vif = float("inf") if aliased else 1.0 / (1.0 - r2)

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
    leakage = _leakage(sub, t, included, omitted)
    max_leak = max((abs(v) for v in leakage.values()), default=0.0)
    omitted_r2 = _partial_r2(sub, t, included, omitted)   # the DECISION statistic

    # target aliased with the nuisance INTERACTION, but additively identified -> report, never block
    interaction_aliased = (not aliased) and not shares_common_support(
        sub, contrast_col, reference, test, nuis_present)

    # Report the RAW measurements, canonicalized to a platform-stable precision (decisions above
    # used the raw values). Byte-for-byte reproducibility across BLAS builds depends on this.
    metrics = dict(nuisance=nuis_present, included=included or [], omitted=omitted,
                   r2=_canon(r2), vif=_canon(vif),
                   leakage={k: _canon(v) for k, v in leakage.items()},
                   max_leakage=_canon(max_leak),
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
    # Estimability of the biological contrast against the declared technical variables is
    # design-matrix algebra, independent of whether the outcome is gene expression or cluster
    # abundance.  Keep outcome-specific model adequacy in its own verifier.
    analysis_types = ("condition_contrast_DE", "differential_abundance")
    audit_dimensions = ("conditioning_set",)
    proof_basis = "design-matrix algebra"
    contract_fields = ("condition", "reference", "test", "batch", "model",
                       "analyst_adjusted_for", "target_coefficient", "subset")
    max_status = S.BLOCKER   # structural, power-independent: an aliased design is not estimable

    def applies_to(self, design: Design, bundle) -> bool:
        return design.analysis_type in self.analysis_types

    def cannot_evaluate(self, design: Design, bundle):
        return None   # needs only .obs; if the design is unrealizable, validate_design_against raises

    def run(self, design: Design, bundle, reported=None) -> Finding:
        return evaluate_confounding(bundle.observations, design)
