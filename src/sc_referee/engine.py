"""The recompute engine + the earned-verdict rule.

This module holds the deterministic heart of the `experimental_unit` check:
  - `Panel`         — every number the verdict needs, folded into one struct (C3)
  - `earned_verdict`— the PINNED decision rule (arithmetic, no LLM)
  - aggregation, the replicate-aware tests (`simple`/`pydeseq2`), MDE + `powered` gate
    (added incrementally; earned_verdict comes first because it is the load-bearing logic)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy import stats
from statsmodels.stats.multitest import multipletests

from sc_referee import statuses as S
from sc_referee.row_ledger import RowLedgerState, RowsExactBasis, Stage

# Survival-rate thresholds for the earned verdict (defaults; tunable).
BLOCKER_AT = 0.10   # survival_rate <= 0.10  -> the claimed discoveries collapse
MAJOR_BELOW = 0.60  # survival_rate <  0.60  -> claims only partly survive

# Selection-FREE reference effects, typed per measure so MDE and ref share a scale (C5).
# NOT the winner's-cursed reported effect sizes (which would make `powered` read True too easily).
REF_LOG2FC = 1.0    # count / DE path:      |log2FC| >= 1
REF_DPROP = 0.10    # EIP / proportion path: |Δ proportion| >= 0.10
POWERED_FRACTION = 0.80  # >= 80% of claimed-sig features must be individually detectable
DEFAULT_POWER = 0.80


@dataclass
class Panel:
    """All inputs to the earned verdict, so `earned_verdict` reads nothing else. (C3)"""
    # ---- gates ----
    comparable: bool
    comparable_reason: str
    valid_reported_sig: int              # THE DENOMINATOR: the claimed discoveries
    covariates_constant: bool
    replicate_recorded: bool             # design.replicate_unit non-empty AND replicate_var present
    n_biological_replicates_per_arm: int
    powered: bool
    survival_rate: float                 # survivors / |valid_reported_sig|
    # ---- evidence / reporting (NOT gates) ----
    survivors: int = 0
    overlap: Optional[float] = None
    effect_corr: Optional[float] = None
    sign_flips: int = 0
    powered_fraction: Optional[float] = None
    ref_effect: Optional[float] = None
    alpha: float = 0.05


def earned_verdict(panel: Panel):
    """The pinned rule. Returns (status, plain-language reason).

    Order matters: every `needs_evidence` gate is checked BEFORE survival, so an
    underpowered or incomparable recompute can never masquerade as a blocker.
    """
    if not panel.comparable:
        return S.NEEDS_EVIDENCE, f"I couldn't fairly compare your results to a recomputation: {panel.comparable_reason}"
    if panel.valid_reported_sig == 0:
        return S.NEEDS_EVIDENCE, ("none of your significant genes could be matched and re-tested in the "
                                  "recomputation, so I couldn't check them")
    if not panel.covariates_constant:
        return S.NEEDS_EVIDENCE, ("a variable changes within a single sample, so I couldn't build one "
                                  "clean row per sample to re-test at the sample level")
    if not panel.replicate_recorded:
        return S.NEEDS_EVIDENCE, ("your data doesn't record what counts as one independent sample (a "
                                  "biological replicate), so I couldn't re-test at the sample level")
    if panel.n_biological_replicates_per_arm < 3:
        return S.NEEDS_EVIDENCE, ("too few independent samples to re-test reliably — I need at least 3 "
                                  "per group")
    if not panel.powered:
        return S.NEEDS_EVIDENCE, ("the sample-level re-test is underpowered — it could miss a real "
                                  "effect, so a disappearance here wouldn't be conclusive; treat these "
                                  "as exploratory")
    if panel.survival_rate <= BLOCKER_AT:
        return S.BLOCKER, ("your significant genes do not survive once the test uses your independent "
                           "samples as the unit instead of individual cells. This is pseudoreplication: "
                           "testing each cell as a replicate makes results look far more significant than "
                           "they are. Re-run the test at the sample level (pseudobulk).")
    if panel.survival_rate < MAJOR_BELOW:
        return S.MAJOR, ("you tested individual cells as the unit; your significant genes only partly "
                         "survive when re-tested at the sample level. Re-run at the sample level "
                         "(pseudobulk) to be safe.")
    return S.PASS, (f"{panel.survivors} of {panel.valid_reported_sig} reported calls survive the "
                    "sample-level sensitivity recomputation. This does not establish that the "
                    "original test used samples as its unit or that its covariance model was valid")


# ---------------------------------------------------------------------------
# Minimum Detectable Effect (MDE) + the `powered` gate (C5)
#
# MDE_i is the smallest effect the replicate-aware test would detect at the given power
# and alpha for feature i. `powered` asks: could the recompute have SEEN a real effect of
# size `ref`? If most claimed-sig features have MDE_i <= ref, a collapse is informative
# (they were detectable and vanished); if not, the recompute is underpowered and a collapse
# is ambiguous -> the earned rule abstains (needs_evidence) rather than blocks.
# ---------------------------------------------------------------------------
def mde_paired(s_diff, n_pairs: int, alpha: float = 0.05, power: float = DEFAULT_POWER) -> float:
    """Two-sided paired t-test MDE:  (t_{1-a/2,df} + t_{power,df}) · s_diff / sqrt(n).

    `s_diff` is the SD of the per-pair differences, on the SAME scale as `ref`
    (log2 for the count/`simple` path, Δproportion for EIP). df = n_pairs - 1.
    """
    if n_pairs < 2:
        return np.inf
    df = n_pairs - 1
    crit = stats.t.ppf(1 - alpha / 2, df) + stats.t.ppf(power, df)
    return float(crit * s_diff / np.sqrt(n_pairs))


def mde_wald(lfc_se, alpha: float = 0.05, power: float = DEFAULT_POWER) -> float:
    """Two-sided NB/DESeq2 Wald MDE in log2FC units:  (z_{1-a/2} + z_{power}) · lfcSE."""
    crit = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return float(crit * lfc_se)


def powered_fraction(mde_values, ref_effect: float) -> float:
    """Fraction of features whose MDE is at or below the reference effect.

    A non-finite MDE means the feature is UNDETECTABLE, not absent — it counts against power.
    Dropping such features from the denominator overstates power and would let an inadequate
    recompute earn a blocker. (Codex review 2026-07-08.)
    """
    mde = np.asarray(mde_values, dtype=float)
    if mde.size == 0:
        return 0.0
    detectable = np.isfinite(mde) & (mde <= ref_effect)
    return float(detectable.sum() / mde.size)


def is_powered(mde_values, ref_effect: float, threshold: float = POWERED_FRACTION) -> bool:
    return powered_fraction(mde_values, ref_effect) >= threshold


# ---------------------------------------------------------------------------
# The recompute: aggregate cells -> pseudobulk samples -> replicate-aware test.
# ---------------------------------------------------------------------------
@dataclass
class RecomputeResult:
    table: pd.DataFrame          # index=feature_id; cols pvalue,padj,effect,se,s_diff,n_used,testable
    mde_kind: str                # "paired" (t-based) | "wald" (z-based, pydeseq2)
    n_replicates_per_arm: int


@dataclass(frozen=True)
class PseudobulkSampleRows:
    rows: pd.DataFrame
    group_positions: tuple[np.ndarray, ...]
    row_ledger_identity: str
    exact: bool = True
    reason: str = "Exact canonical pseudobulk sample rows."
    machine_reason: str = "exact_pseudobulk_rows"
    rows_exact_basis: RowsExactBasis | None = None

    def __post_init__(self):
        if self.rows_exact_basis is None:
            object.__setattr__(self, "rows_exact_basis",
                               RowsExactBasis.HUMAN_DECLARED if self.exact else RowsExactBasis.UNAVAILABLE)


def build_pseudobulk_sample_rows(observations, design, *, recompute_legacy=False):
    """Build deterministic fitted sample rows; the recompute opts into its legacy row contract."""
    from sc_referee.design import apply_subset
    from sc_referee.design_matrix import build_fixed_effect_matrix

    obs = apply_subset(observations, design)
    if recompute_legacy:
        keys = [key for key in design.sample_unit if key in obs.columns]
        identity_keys = list(design.aggregation_key or keys)
    else:
        keys = list(design.aggregation_key or [])
        identity_keys = keys
        if not keys or design.confidence.get("aggregation_key") != "high":
            return PseudobulkSampleRows(
                pd.DataFrame(), (), "", False,
                "The final aggregation key was not ratified at high confidence.",
                "aggregation_key_not_ratified",
            )
        if any(key not in obs.columns for key in keys):
            return PseudobulkSampleRows(
                pd.DataFrame(), (), "", False,
                "A final aggregation-key column is missing.", "missing_aggregation_key",
            )
    contrast_col, _, _ = design.contrast_column_and_levels()
    carry_sources = (
        keys + [contrast_col] + list(design.pairing_unit or []) + list(design.batch)
        + list(design.replicate_unit)
        + ([] if recompute_legacy else list(design.analyst_adjusted_for or []))
    )
    carry = [column for column in dict.fromkeys(carry_sources) if column in obs.columns]
    if any(key not in obs.columns for key in identity_keys):
        return PseudobulkSampleRows(
            pd.DataFrame(columns=carry), (), "", False,
            "A final aggregation-key column is missing.", "missing_aggregation_key",
        )
    invalid_key = obs[identity_keys].isna().to_numpy().any() or any(
        series.map(
            lambda value: isinstance(value, (int, float, complex, np.number))
            and not np.isfinite(value)
        ).any()
        for _, series in obs[identity_keys].items()
    )
    if invalid_key:
        return PseudobulkSampleRows(
            pd.DataFrame(columns=carry), (), "", False,
            "A final aggregation-key value is null or non-finite.",
            "invalid_aggregation_key_value",
        )
    positions = tuple(obs.groupby(keys, sort=False, observed=True).indices.values())
    flattened_positions = np.concatenate(positions) if positions else np.array([], dtype=int)
    exact_partition = (
        len(flattened_positions) == len(obs)
        and np.array_equal(np.sort(flattened_positions), np.arange(len(obs)))
    )
    if not exact_partition:
        return PseudobulkSampleRows(
            pd.DataFrame(), positions, "", False,
            "The fitted groups do not exactly partition the observations.",
            "incomplete_aggregation_partition",
        )
    rows_data = []
    exact = True
    for group_positions in positions:
        group = obs.iloc[group_positions]
        if not recompute_legacy:
            exact &= all(group[column].nunique(dropna=False) == 1 for column in carry if column not in keys)
        first = group.iloc[0]
        rows_data.append({column: first[column] for column in carry})
    rows = pd.DataFrame(rows_data, columns=carry)
    identities = [tuple(row[key] for key in keys) for _, row in rows.iterrows()]
    rows.index = pd.Index(np.asarray(identities, dtype=object), name="sample_identity")
    row_identity = build_fixed_effect_matrix(
        rows, source_columns=(), column_kinds={}, categorical_levels={}, intercept=False
    ).row_identity
    if not exact:
        return PseudobulkSampleRows(
            rows, positions, row_identity.digest, False,
            "A carried fitted column varies within a final sample.",
            "within_sample_column_variation",
        )
    return PseudobulkSampleRows(rows, positions, row_identity.digest)


def apply_row_ledger_evidence(rows, ledger_result, design):
    """Opt-in monotone composition; legacy callers that pass no ledger retain object identity."""
    if ledger_result is None:
        return rows
    attested = (rows.exact and getattr(design, "fitted_design", None) is not None
                and design.fitted_design.rows_exact is True
                and design.confidence.get("fitted_design") == "high")
    certified = (ledger_result.state is RowLedgerState.CERTIFIED_ROWS_RATIFIED
                 and Stage.FIT in ledger_result.certified_stages and ledger_result.artifact is not None)
    if (attested and certified
            and ledger_result.artifact.core_pseudobulk_row_identity == rows.row_ledger_identity):
        from dataclasses import replace
        return replace(rows, row_ledger_identity=ledger_result.artifact.row_ledger_identity,
                       rows_exact_basis=RowsExactBasis.RECONSTRUCTED_CERTIFIED)
    return PseudobulkSampleRows(
        rows.rows, rows.group_positions, rows.row_ledger_identity, False,
        "The supplied row ledger did not certify these fitted rows.", "rows_not_exact",
        RowsExactBasis.UNAVAILABLE,
    )


def _aggregate_positions(counts, positions):
    if sp.issparse(counts):
        # Only the sample×feature result is materialized.  The cell×feature input remains sparse,
        # which is what makes a full public atlas a practical Referee input.
        return [np.asarray(counts[group].sum(axis=0)).ravel() for group in positions]
    return [counts[group].sum(axis=0) for group in positions]


def aggregate_to_pseudobulk(bundle, design):
    """Sum raw counts within each sample_unit -> (pseudobulk DataFrame, sample metadata).

    Aggregation is done BEFORE normalization (count models need summed raw ints). The
    metadata carries the contrast + pairing/batch/replicate factors, one row per sample.
    """
    from sc_referee.design import subset_mask

    obs = bundle.observations
    counts = bundle.measure.counts
    if counts is None:
        raise ValueError("pseudobulk recomputation requires a raw count matrix")
    if not sp.issparse(counts):
        counts = np.asarray(counts)
    mask = subset_mask(obs, design)          # the recompute MUST see the same cells the design does
    if not mask.all():
        obs, counts = obs[mask], counts[mask]
    feats = list(bundle.measure.feature_index)
    sample_rows = build_pseudobulk_sample_rows(bundle.observations, design, recompute_legacy=True)
    pb_rows = _aggregate_positions(counts, sample_rows.group_positions)
    pb = pd.DataFrame(pb_rows, columns=feats)
    meta = sample_rows.rows.reset_index(drop=True)
    return pb, meta


def _bh(pvalues, testable):
    """BH over the TESTABLE family only; non-testable features get padj=1 and are reported
    separately, never counted as 'lost'.

    They must NOT enter the family: BH's n is the number of hypotheses actually tested. Padding
    it with untested features inflates n and drives real discoveries to padj=1 — an
    over-conservative recompute, which manufactures false blockers. (Codex review 2026-07-08;
    this corrects the spec, which said to enter them as p=1.)
    """
    padj = np.ones_like(np.asarray(pvalues, dtype=float))
    testable = np.asarray(testable, dtype=bool)
    if testable.any():
        padj[testable] = multipletests(np.asarray(pvalues, dtype=float)[testable], method="fdr_bh")[1]
    return padj


def simple_recompute(pb: pd.DataFrame, meta: pd.DataFrame, design) -> RecomputeResult:
    """aggregate -> CPM -> log2(CPM+1) -> donor-aware PAIRED t-test -> BH.

    Effects are per-pair mean differences on the log2 scale, so they compare directly to
    ref=|log2FC|>=1. `simple` never blocks (the check caps it to `major`); it is the
    dependency-light engine for CI and fixtures.
    """
    contrast_col, ref, test = design.contrast_column_and_levels()
    feats = list(pb.columns)
    counts = pb.values.astype(float)
    lib = counts.sum(axis=1, keepdims=True)
    lib[lib == 0] = np.nan
    log2cpm = np.log2(counts / lib * 1e6 + 1.0)  # samples × features, log2 scale

    pairing = [p for p in (design.pairing_unit or design.replicate_unit) if p in meta.columns]
    arm = meta[contrast_col].to_numpy()
    diffs = []
    for _, idx in meta.groupby(pairing, sort=False, observed=True).indices.items():
        arms = arm[idx]
        ref_pos, test_pos = idx[arms == ref], idx[arms == test]
        if len(ref_pos) and len(test_pos):
            diffs.append(log2cpm[test_pos].mean(axis=0) - log2cpm[ref_pos].mean(axis=0))

    n = len(diffs)
    if n == 0:
        empty = pd.DataFrame(
            {"pvalue": 1.0, "padj": 1.0, "effect": np.nan, "se": np.nan,
             "s_diff": np.nan, "n_used": 0, "testable": False},
            index=feats,
        )
        return RecomputeResult(table=empty, mde_kind="paired", n_replicates_per_arm=0)

    D = np.vstack(diffs)  # n_pairs × features
    mean_d = D.mean(axis=0)
    sd_d = D.std(axis=0, ddof=1) if n > 1 else np.full(len(feats), np.nan)
    se = sd_d / np.sqrt(n)
    testable = np.isfinite(sd_d) & (sd_d > 0) & (n >= 2)
    pval = np.ones(len(feats))
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(testable, mean_d / se, 0.0)
    pval[testable] = 2 * stats.t.sf(np.abs(t[testable]), df=n - 1)

    table = pd.DataFrame(
        {"pvalue": pval, "padj": _bh(pval, testable), "effect": mean_d,
         "se": se, "s_diff": sd_d, "n_used": n, "testable": testable},
        index=feats,
    )
    return RecomputeResult(table=table, mde_kind="paired", n_replicates_per_arm=n)


# ---------------------------------------------------------------------------
# build_panel — fold the reported claims + the recompute into one Panel (C3).
#
# THE DENOMINATOR is valid_reported_sig: the claimed discoveries that were actually
# testable in the recompute. survival_rate is over THAT set (not all features), so a
# clean analysis where every claim survives reads as ~1.0, not as collapse.
# ---------------------------------------------------------------------------
def _reported_sig_mask(rep: pd.DataFrame, alpha: float):
    if "padj" in rep.columns and rep["padj"].notna().any():
        return rep["padj"] <= alpha
    return rep["pvalue"] <= alpha


def build_panel(reported: pd.DataFrame, res: RecomputeResult, design, bundle, alpha: float = 0.05) -> Panel:
    from sc_referee.checks.confounding import covariates_constant_within_sample_unit

    table = res.table
    rep = (reported.dropna(subset=["feature_id"])
           .drop_duplicates("feature_id").set_index("feature_id"))
    reported_ids = set(rep.index)
    reported_sig = set(rep.index[_reported_sig_mask(rep, alpha).fillna(False)])

    matched = reported_ids & set(table.index)
    id_match_rate = len(matched) / max(len(reported_ids), 1)
    testable_ids = set(table.index[table["testable"].astype(bool)])
    valid_reported = matched & testable_ids
    vrs = sorted(valid_reported & reported_sig)  # the claimed discoveries, testable

    survivors = [f for f in vrs if float(table.loc[f, "padj"]) <= alpha]
    n_survivors = len(survivors)
    survival_rate = (n_survivors / len(vrs)) if vrs else 1.0
    overlap = (n_survivors / len(valid_reported)) if valid_reported else None

    # evidence (never gates): effect correlation + sign flips over the claimed discoveries
    effect_corr, sign_flips = None, 0
    if vrs and "effect" in rep.columns:
        re_eff = rep.loc[vrs, "effect"].to_numpy(dtype=float)
        rc_eff = table.loc[vrs, "effect"].to_numpy(dtype=float)
        ok = np.isfinite(re_eff) & np.isfinite(rc_eff)
        if ok.sum() >= 2 and re_eff[ok].std() > 0 and rc_eff[ok].std() > 0:
            effect_corr = float(np.corrcoef(re_eff[ok], rc_eff[ok])[0, 1])
        sign_flips = int(np.sum(np.sign(re_eff[ok]) * np.sign(rc_eff[ok]) < 0))

    # MDE + powered over the claimed discoveries, on the ref's scale
    ref = REF_DPROP if bundle.measure.kind == "proportions" else REF_LOG2FC
    if vrs:
        if res.mde_kind == "wald":
            mdes = np.array([mde_wald(float(table.loc[f, "se"]), alpha=alpha) for f in vrs])
        else:
            n = res.n_replicates_per_arm
            mdes = np.array([mde_paired(float(table.loc[f, "s_diff"]), n, alpha=alpha) for f in vrs])
        pw_frac = powered_fraction(mdes, ref)
        powered = pw_frac >= POWERED_FRACTION
    else:
        pw_frac, powered = None, False

    # comparability — NOT "same estimator" (the recompute deliberately changes it), but a
    # decent id match and a FULL tested family (non-sig rows present) to rebuild FDR.
    full_family = len(reported_ids) > len(reported_sig)
    reasons = []
    if id_match_rate < 0.70:
        reasons.append(f"only {id_match_rate:.0%} of reported features matched the data")
    if not full_family:
        reasons.append("reported table has significant rows only (can't rebuild the FDR family)")
    # Uncorrected p-values are not an FDR family at all, so a survival comparison against our
    # BH-corrected recompute is apples-to-oranges. Defer to `multiple_testing`, which owns that
    # diagnosis — otherwise we blame an uncorrected gene list on pseudoreplication.
    from sc_referee.checks.multiple_testing import reported_is_uncorrected
    if reported_is_uncorrected(reported):
        reasons.append("reported p-values are uncorrected — not the same FDR family (see multiple_testing)")
    comparable = not reasons

    cov_ok, _ = covariates_constant_within_sample_unit(bundle.observations, design)
    from sc_referee.design import replicate_recorded as _replicate_recorded
    replicate_recorded = _replicate_recorded(design, bundle.observations)   # design is authoritative, not the adapter hint

    return Panel(
        comparable=comparable,
        comparable_reason="; ".join(reasons),
        valid_reported_sig=len(vrs),
        covariates_constant=cov_ok,
        replicate_recorded=replicate_recorded,
        n_biological_replicates_per_arm=res.n_replicates_per_arm,
        powered=powered,
        survival_rate=survival_rate,
        survivors=n_survivors,
        overlap=overlap,
        effect_corr=effect_corr,
        sign_flips=sign_flips,
        powered_fraction=pw_frac,
        ref_effect=ref,
        alpha=alpha,
    )
