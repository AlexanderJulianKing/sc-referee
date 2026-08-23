"""Referral waiting times under centralised versus local booking: analysis script.

Design. Twenty-six primary care clinics were assigned to a booking protocol as whole
clinics: 13 centralised, 13 local. Eight consecutive referrals were audited inside each
clinic. The clinic is therefore the independent experimental unit, and the eight audited
referrals are repeated records drawn from within a clinic rather than independent units.

What each file is used for.
  * clinic_summary.csv  -- the inferential comparison. One row per clinic, so the rows are
                           independent of one another. The two-group test is an independent
                           two-sample comparison of the per-clinic mean waiting times, with
                           the sample size reported as the number of clinics in each group.
  * referral_audit.csv  -- descriptive counts only (total referrals audited, referrals per
                           clinic, and the composition of the audited caseload). These
                           referral-level rows never enter the two-group test.

Run: /usr/local/bin/python3 analysis.py
"""

import os

import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(HERE, "referral_audit.csv")
SUMMARY_PATH = os.path.join(HERE, "clinic_summary.csv")

UNIT_COLUMN = "clinic_id"
GROUP_COLUMN = "booking_protocol"
GROUPS = ("centralised", "local")


def load_data():
    """Read both comma-separated files."""
    raw = pd.read_csv(RAW_PATH)
    summary = pd.read_csv(SUMMARY_PATH)
    return raw, summary


def check_consistency(raw, summary):
    """Confirm the summary file really is the aggregate of the raw audit file."""
    recomputed = (
        raw.groupby(UNIT_COLUMN)["waiting_days"]
        .agg(["count", "mean"])
        .rename(columns={"count": "n_recomputed", "mean": "mean_recomputed"})
        .reset_index()
    )
    merged = summary.merge(recomputed, on=UNIT_COLUMN, how="outer", indicator=True)

    unmatched = int((merged["_merge"] != "both").sum())
    count_mismatch = int(
        (merged["n_referrals_audited"] != merged["n_recomputed"]).sum()
    )
    mean_mismatch = int(
        (
            (merged["mean_waiting_days"] - merged["mean_recomputed"]).abs() > 5e-4
        ).sum()
    )

    protocols = raw[[UNIT_COLUMN, GROUP_COLUMN]].drop_duplicates()
    protocol_mismatch = int(
        summary.merge(protocols, on=UNIT_COLUMN, suffixes=("_summary", "_raw"))
        .pipe(lambda d: d[GROUP_COLUMN + "_summary"] != d[GROUP_COLUMN + "_raw"])
        .sum()
    )

    return {
        "clinics_not_in_both_files": unmatched,
        "referral_count_mismatches": count_mismatch,
        "clinic_mean_mismatches": mean_mismatch,
        "protocol_label_mismatches": protocol_mismatch,
    }


def describe_raw(raw):
    """Descriptive counts taken from the raw audit file only."""
    per_clinic = raw.groupby(UNIT_COLUMN).size()
    per_protocol = raw.groupby(GROUP_COLUMN).size()
    return {
        "total_referrals_audited": int(len(raw)),
        "distinct_clinics": int(raw[UNIT_COLUMN].nunique()),
        "distinct_referral_ids": int(raw["referral_id"].nunique()),
        "referrals_per_clinic_min": int(per_clinic.min()),
        "referrals_per_clinic_max": int(per_clinic.max()),
        "referrals_per_clinic_mean": float(per_clinic.mean()),
        "referrals_by_protocol": per_protocol.to_dict(),
        "referrals_by_age_band": raw["patient_age_band"].value_counts().sort_index().to_dict(),
        "referrals_by_specialty": raw["referral_specialty"].value_counts().sort_index().to_dict(),
        "waiting_days_min": int(raw["waiting_days"].min()),
        "waiting_days_max": int(raw["waiting_days"].max()),
    }


def describe_clinics(summary):
    """Per-clinic descriptive statistics from the summary file."""
    out = {}
    for group in GROUPS:
        values = summary.loc[summary[GROUP_COLUMN] == group, "mean_waiting_days"]
        out[group] = {
            "n_clinics": int(values.size),
            "mean_of_clinic_means": float(values.mean()),
            "sd_of_clinic_means": float(values.std(ddof=1)),
            "median_of_clinic_means": float(values.median()),
            "min_of_clinic_means": float(values.min()),
            "max_of_clinic_means": float(values.max()),
        }
    return out


def two_group_test(summary):
    """Independent two-sample comparison of the per-clinic mean waiting times.

    The unit of analysis is the clinic. Welch's t-test is used, which does not assume
    the two groups share a variance. It is reported alongside a Mann-Whitney U test as
    a distribution-free sensitivity check.
    """
    centralised = summary.loc[
        summary[GROUP_COLUMN] == "centralised", "mean_waiting_days"
    ].to_numpy()
    local = summary.loc[summary[GROUP_COLUMN] == "local", "mean_waiting_days"].to_numpy()

    welch = stats.ttest_ind(centralised, local, equal_var=False)
    student = stats.ttest_ind(centralised, local, equal_var=True)
    mwu = stats.mannwhitneyu(centralised, local, alternative="two-sided")

    n_c, n_l = centralised.size, local.size
    var_c = centralised.var(ddof=1)
    var_l = local.var(ddof=1)
    se_diff = (var_c / n_c + var_l / n_l) ** 0.5
    diff = centralised.mean() - local.mean()

    # Welch-Satterthwaite degrees of freedom, computed here because this version of
    # scipy does not expose them on the test result object.
    welch_df = (var_c / n_c + var_l / n_l) ** 2 / (
        (var_c / n_c) ** 2 / (n_c - 1) + (var_l / n_l) ** 2 / (n_l - 1)
    )
    crit = stats.t.ppf(0.975, welch_df)

    pooled_sd = (((n_c - 1) * var_c + (n_l - 1) * var_l) / (n_c + n_l - 2)) ** 0.5

    return {
        "n_clinics_centralised": int(n_c),
        "n_clinics_local": int(n_l),
        "mean_centralised": float(centralised.mean()),
        "mean_local": float(local.mean()),
        "mean_difference_centralised_minus_local": float(diff),
        "se_of_difference": float(se_diff),
        "ci95_low": float(diff - crit * se_diff),
        "ci95_high": float(diff + crit * se_diff),
        "welch_t": float(welch.statistic),
        "welch_df": float(welch_df),
        "welch_p": float(welch.pvalue),
        "student_t": float(student.statistic),
        "student_df": float(n_c + n_l - 2),
        "student_p": float(student.pvalue),
        "cohens_d": float(diff / pooled_sd),
        "mannwhitney_u": float(mwu.statistic),
        "mannwhitney_p": float(mwu.pvalue),
    }


def main():
    raw, summary = load_data()

    print("=" * 72)
    print("FILE CONSISTENCY CHECK")
    print("=" * 72)
    for key, value in check_consistency(raw, summary).items():
        print("  {:<32} {}".format(key, value))
    print()

    print("=" * 72)
    print("DESCRIPTIVE COUNTS -- from referral_audit.csv (raw audit, referral level)")
    print("These counts are descriptive only and do not feed the two-group test.")
    print("=" * 72)
    desc = describe_raw(raw)
    print("  total referrals audited          {}".format(desc["total_referrals_audited"]))
    print("  distinct clinics                 {}".format(desc["distinct_clinics"]))
    print("  distinct referral identifiers    {}".format(desc["distinct_referral_ids"]))
    print(
        "  referrals per clinic             min {}, max {}, mean {:.1f}".format(
            desc["referrals_per_clinic_min"],
            desc["referrals_per_clinic_max"],
            desc["referrals_per_clinic_mean"],
        )
    )
    print("  waiting_days observed range      {} to {} days".format(
        desc["waiting_days_min"], desc["waiting_days_max"]
    ))
    print("  referrals by booking protocol")
    for key, value in sorted(desc["referrals_by_protocol"].items()):
        print("      {:<24} {}".format(key, value))
    print("  referrals by patient age band")
    for key, value in desc["referrals_by_age_band"].items():
        print("      {:<24} {}".format(key, value))
    print("  referrals by referral specialty")
    for key, value in desc["referrals_by_specialty"].items():
        print("      {:<24} {}".format(key, value))
    print()

    print("=" * 72)
    print("PER-CLINIC SUMMARY STATISTICS -- from clinic_summary.csv (one row per clinic)")
    print("=" * 72)
    clinic_stats = describe_clinics(summary)
    for group in GROUPS:
        s = clinic_stats[group]
        print("  {}".format(group))
        print("      clinics (n)                  {}".format(s["n_clinics"]))
        print("      mean of clinic means         {:.3f} days".format(s["mean_of_clinic_means"]))
        print("      sd of clinic means           {:.3f} days".format(s["sd_of_clinic_means"]))
        print("      median of clinic means       {:.3f} days".format(s["median_of_clinic_means"]))
        print(
            "      range of clinic means        {:.3f} to {:.3f} days".format(
                s["min_of_clinic_means"], s["max_of_clinic_means"]
            )
        )
    print()

    print("=" * 72)
    print("TWO-GROUP TEST -- from clinic_summary.csv only")
    print("Unit of analysis: the clinic. n = number of clinics per group.")
    print("=" * 72)
    res = two_group_test(summary)
    print("  n clinics, centralised           {}".format(res["n_clinics_centralised"]))
    print("  n clinics, local                 {}".format(res["n_clinics_local"]))
    print("  mean clinic wait, centralised    {:.3f} days".format(res["mean_centralised"]))
    print("  mean clinic wait, local          {:.3f} days".format(res["mean_local"]))
    print(
        "  difference (centralised - local) {:.3f} days".format(
            res["mean_difference_centralised_minus_local"]
        )
    )
    print("  standard error of difference     {:.3f} days".format(res["se_of_difference"]))
    print(
        "  95% confidence interval          {:.3f} to {:.3f} days".format(
            res["ci95_low"], res["ci95_high"]
        )
    )
    print()
    print("  Primary test: Welch two-sample t-test on per-clinic mean waiting days")
    print(
        "      t = {:.3f}, df = {:.2f}, p = {:.4f}".format(
            res["welch_t"], res["welch_df"], res["welch_p"]
        )
    )
    print("      Cohen's d (pooled)           {:.3f}".format(res["cohens_d"]))
    print()
    print("  Sensitivity checks (same unit of analysis, same 26 clinic rows)")
    print(
        "      Student t-test               t = {:.3f}, df = {:.0f}, p = {:.4f}".format(
            res["student_t"], res["student_df"], res["student_p"]
        )
    )
    print(
        "      Mann-Whitney U               U = {:.1f}, p = {:.4f}".format(
            res["mannwhitney_u"], res["mannwhitney_p"]
        )
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
