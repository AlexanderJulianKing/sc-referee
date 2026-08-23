"""Analysis for the neonatal tube-weaning feeding protocol comparison.

Study question
--------------
Does the rate of milk transfer during oral feeding (`transfer_rate_ml_per_min`)
differ between the standard and the new tube-weaning feeding protocol?

Design and unit of analysis
---------------------------
The independent experimental unit is the INFANT, not the feeding session.
`feeding_sessions.csv` holds 156 rows: six consecutive feeding sessions for each
of 26 infants (13 per protocol). The six rows belonging to one infant are
repeated measures on the same baby and are therefore NOT independent
observations.

The script consequently runs in two clearly separated stages:

  1. `reduce_sessions_to_infants()` collapses the raw session-level table to one
     row per infant and hands that reduced table back. This is the only place
     where the repeated sessions are aggregated.
  2. `compare_protocols()` performs the two-group comparison on exactly the table
     returned by stage 1, so the sample size entering the test is the number of
     infants (13 vs 13), never the number of sessions.

Run with:  python3 analysis.py
"""

from __future__ import annotations

import os

import pandas as pd
from scipy import stats

RAW_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feeding_sessions.csv")

OUTCOME = "transfer_rate_ml_per_min"
GROUP = "protocol"
UNIT = "infant_id"
GROUP_LEVELS = ("standard", "new")
EXPECTED_SESSIONS_PER_INFANT = 6


def load_raw_sessions(path: str = RAW_CSV) -> pd.DataFrame:
    """Read the raw session-level table. One row = one observed feeding session."""
    raw = pd.read_csv(path)
    required = [
        UNIT,
        GROUP,
        "session_number",
        OUTCOME,
        "pma_weeks",
        "birth_weight_g",
        "volume_taken_ml",
    ]
    missing = [c for c in required if c not in raw.columns]
    if missing:
        raise ValueError("raw file is missing expected columns: %s" % missing)
    return raw


def check_raw_structure(raw: pd.DataFrame) -> None:
    """Confirm the repeated-measures structure the analysis assumes."""
    if raw.isna().any().any():
        raise ValueError("raw table contains missing values; the analysis assumes none")

    sessions_per_infant = raw.groupby(UNIT).size()
    odd = sessions_per_infant[sessions_per_infant != EXPECTED_SESSIONS_PER_INFANT]
    if len(odd) > 0:
        raise ValueError(
            "expected %d sessions per infant, found otherwise for: %s"
            % (EXPECTED_SESSIONS_PER_INFANT, list(odd.index))
        )

    # An infant must sit in exactly one protocol group; protocol is an
    # infant-level trait, not a session-level one.
    protocols_per_infant = raw.groupby(UNIT)[GROUP].nunique()
    if (protocols_per_infant != 1).any():
        raise ValueError("at least one infant appears under more than one protocol")

    levels = set(raw[GROUP].unique())
    if levels != set(GROUP_LEVELS):
        raise ValueError("unexpected protocol levels: %s" % sorted(levels))


def reduce_sessions_to_infants(raw: pd.DataFrame) -> pd.DataFrame:
    """Reduce the raw session table to ONE ROW PER INFANT and return it.

    This is the separate reduction step required by the design. Each infant's six
    repeated feeding sessions are averaged into a single summary value of the
    outcome. Infant-level traits (`protocol`, `birth_weight_g`) are constant
    within an infant and are carried through unchanged.

    Returns
    -------
    pandas.DataFrame
        One row per infant, with columns:
        infant_id, protocol, birth_weight_g, n_sessions,
        mean_transfer_rate_ml_per_min, sd_within_infant_ml_per_min, mean_pma_weeks.
        Nothing downstream of this function ever touches the session-level table.
    """
    grouped = raw.groupby(UNIT, as_index=False)
    reduced = grouped.agg(
        protocol=(GROUP, "first"),
        birth_weight_g=("birth_weight_g", "first"),
        n_sessions=(OUTCOME, "size"),
        mean_transfer_rate_ml_per_min=(OUTCOME, "mean"),
        sd_within_infant_ml_per_min=(OUTCOME, "std"),
        mean_pma_weeks=("pma_weeks", "mean"),
    )

    if reduced[UNIT].duplicated().any():
        raise ValueError("reduction failed: infant_id is not unique after reduction")
    if len(reduced) != raw[UNIT].nunique():
        raise ValueError("reduction failed: row count does not match infant count")

    return reduced


def compare_protocols(infant_level: pd.DataFrame) -> dict:
    """Independent two-sample comparison run on the reduced, one-row-per-infant table.

    The input must be the table returned by `reduce_sessions_to_infants`, so every
    row contributing to the test is one independent infant.
    """
    if infant_level[UNIT].duplicated().any():
        raise ValueError("comparison must be run on a one-row-per-infant table")

    standard = infant_level.loc[
        infant_level[GROUP] == "standard", "mean_transfer_rate_ml_per_min"
    ]
    new = infant_level.loc[infant_level[GROUP] == "new", "mean_transfer_rate_ml_per_min"]

    # Primary test: Welch's independent two-sample t-test (does not assume equal
    # group variances). n is the number of INFANTS in each group.
    welch = stats.ttest_ind(new, standard, equal_var=False)
    # Sensitivity check only: Student's equal-variance version of the same test.
    student = stats.ttest_ind(new, standard, equal_var=True)

    n_std, n_new = int(standard.size), int(new.size)
    mean_std, mean_new = float(standard.mean()), float(new.mean())
    sd_std, sd_new = float(standard.std(ddof=1)), float(new.std(ddof=1))
    diff = mean_new - mean_std

    # 95% confidence interval for the difference in means, Welch form.
    se_diff = (sd_new**2 / n_new + sd_std**2 / n_std) ** 0.5
    df_welch = (sd_new**2 / n_new + sd_std**2 / n_std) ** 2 / (
        (sd_new**2 / n_new) ** 2 / (n_new - 1) + (sd_std**2 / n_std) ** 2 / (n_std - 1)
    )
    tcrit = stats.t.ppf(0.975, df_welch)
    ci_low, ci_high = diff - tcrit * se_diff, diff + tcrit * se_diff

    # Pooled standard deviation and Hedges-corrected standardised effect size.
    pooled_sd = (
        ((n_std - 1) * sd_std**2 + (n_new - 1) * sd_new**2) / (n_std + n_new - 2)
    ) ** 0.5
    cohens_d = diff / pooled_sd
    hedges_g = cohens_d * (1 - 3 / (4 * (n_std + n_new) - 9))

    return {
        "n_infants_standard": n_std,
        "n_infants_new": n_new,
        "mean_standard": mean_std,
        "mean_new": mean_new,
        "sd_standard": sd_std,
        "sd_new": sd_new,
        "mean_difference_new_minus_standard": diff,
        "ci95_low": float(ci_low),
        "ci95_high": float(ci_high),
        "welch_t": float(welch.statistic),
        "welch_df": float(df_welch),
        "welch_p": float(welch.pvalue),
        "student_t": float(student.statistic),
        "student_df": float(n_std + n_new - 2),
        "student_p": float(student.pvalue),
        "pooled_sd": float(pooled_sd),
        "cohens_d": float(cohens_d),
        "hedges_g": float(hedges_g),
    }


def main() -> None:
    raw = load_raw_sessions()
    check_raw_structure(raw)

    print("=" * 72)
    print("RAW SESSION-LEVEL TABLE (not the unit of analysis)")
    print("=" * 72)
    print("rows (feeding sessions):            %d" % len(raw))
    print("distinct infants (independent units): %d" % raw[UNIT].nunique())
    print("sessions per infant:                %d" % EXPECTED_SESSIONS_PER_INFANT)
    print(
        "session-level mean %s by protocol (descriptive only, NOT the test):"
        % OUTCOME
    )
    print(raw.groupby(GROUP)[OUTCOME].agg(["count", "mean", "std"]).to_string())

    # --- reduction step: sessions -> one row per infant -------------------
    infant_level = reduce_sessions_to_infants(raw)

    print()
    print("=" * 72)
    print("REDUCED INFANT-LEVEL TABLE (the unit of analysis)")
    print("=" * 72)
    print("rows (infants): %d" % len(infant_level))
    print(
        infant_level.sort_values([GROUP, UNIT])
        .round(3)
        .to_string(index=False)
    )
    print()
    print("infant-level summary by protocol:")
    print(
        infant_level.groupby(GROUP)["mean_transfer_rate_ml_per_min"]
        .agg(["count", "mean", "std", "min", "max"])
        .round(3)
        .to_string()
    )
    print(
        "mean within-infant SD across sessions: %.3f ml/min"
        % infant_level["sd_within_infant_ml_per_min"].mean()
    )

    # --- comparison, run on exactly the reduced table ---------------------
    res = compare_protocols(infant_level)

    print()
    print("=" * 72)
    print("TWO-GROUP COMPARISON (independent two-sample t-test on infant means)")
    print("=" * 72)
    print(
        "sample size: n = %d infants (standard), n = %d infants (new)"
        % (res["n_infants_standard"], res["n_infants_new"])
    )
    print("  -- sample size is INFANTS, not the 156 feeding sessions --")
    print("mean transfer rate, standard: %.3f ml/min (SD %.3f)" % (res["mean_standard"], res["sd_standard"]))
    print("mean transfer rate, new:      %.3f ml/min (SD %.3f)" % (res["mean_new"], res["sd_new"]))
    print(
        "difference (new - standard):  %.3f ml/min, 95%% CI %.3f to %.3f"
        % (res["mean_difference_new_minus_standard"], res["ci95_low"], res["ci95_high"])
    )
    print(
        "Welch two-sample t-test:      t = %.3f, df = %.2f, p = %.5f"
        % (res["welch_t"], res["welch_df"], res["welch_p"])
    )
    print(
        "Student two-sample t-test:    t = %.3f, df = %.0f, p = %.5f  (sensitivity check)"
        % (res["student_t"], res["student_df"], res["student_p"])
    )
    print(
        "effect size: Cohen's d = %.3f, Hedges' g = %.3f (pooled SD %.3f)"
        % (res["cohens_d"], res["hedges_g"], res["pooled_sd"])
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
