"""Speech-in-babble comparison of two cochlear implant sound-processing strategies.

The group comparison is run on the per-recipient summary sheet
(``recipient_mean_scores.csv``), one row per recipient, because the recipient is
the independent experimental unit: each recipient was assigned to exactly one
processing strategy and completed all five sentence lists with it.

The raw scoring sheet (``sentence_list_scores.csv``) is read only to report
descriptive counts and to confirm that the two files agree. No inferential test
is run on the list-level rows, since the five lists within a recipient are
repeated measures on the same unit and are not independent observations.
"""

from pathlib import Path

import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
RAW_PATH = HERE / "sentence_list_scores.csv"
SUMMARY_PATH = HERE / "recipient_mean_scores.csv"

ESTABLISHED = "established"
NOISE_REDUCTION = "noise_reduction"


def describe_raw_scoring_sheet(raw):
    """Descriptive counts from the list-level scoring sheet. No testing here."""
    lists_per_recipient = raw.groupby("recipient_id")["sentence_list"].count()
    return {
        "n_rows": int(len(raw)),
        "n_recipients": int(raw["recipient_id"].nunique()),
        "n_distinct_lists": int(raw["sentence_list"].nunique()),
        "lists_per_recipient_min": int(lists_per_recipient.min()),
        "lists_per_recipient_max": int(lists_per_recipient.max()),
        "n_missing_scores": int(raw["percent_words_correct"].isna().sum()),
        "score_min": float(raw["percent_words_correct"].min()),
        "score_max": float(raw["percent_words_correct"].max()),
    }


def check_files_agree(raw, summary):
    """Confirm the summary sheet matches the raw sheet it was prepared from."""
    recomputed = (
        raw.groupby("recipient_id")["percent_words_correct"].mean().round(2)
    )
    counts = raw.groupby("recipient_id")["percent_words_correct"].count()
    joined = summary.set_index("recipient_id")
    mean_diff = (joined["mean_percent_words_correct"] - recomputed.reindex(joined.index)).abs()
    count_diff = (joined["lists_scored"] - counts.reindex(joined.index)).abs()
    return {
        "max_abs_mean_difference": float(mean_diff.max()),
        "n_recipients_with_count_mismatch": int((count_diff != 0).sum()),
    }


def group_comparison(summary):
    """Independent two-sample t-test on the per-recipient means."""
    established = summary.loc[
        summary["processing_strategy"] == ESTABLISHED, "mean_percent_words_correct"
    ]
    newer = summary.loc[
        summary["processing_strategy"] == NOISE_REDUCTION, "mean_percent_words_correct"
    ]

    t_stat, p_value = stats.ttest_ind(newer, established, equal_var=True)

    n1, n2 = len(newer), len(established)
    m1, m2 = newer.mean(), established.mean()
    s1, s2 = newer.std(ddof=1), established.std(ddof=1)
    df = n1 + n2 - 2
    pooled_sd = (((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / df) ** 0.5
    se_diff = pooled_sd * (1.0 / n1 + 1.0 / n2) ** 0.5
    diff = m1 - m2
    t_crit = stats.t.ppf(0.975, df)

    return {
        "n_established": int(n2),
        "n_noise_reduction": int(n1),
        "mean_established": float(m2),
        "mean_noise_reduction": float(m1),
        "sd_established": float(s2),
        "sd_noise_reduction": float(s1),
        "mean_difference": float(diff),
        "ci_low": float(diff - t_crit * se_diff),
        "ci_high": float(diff + t_crit * se_diff),
        "t_statistic": float(t_stat),
        "df": int(df),
        "p_value": float(p_value),
        "pooled_sd": float(pooled_sd),
        "cohens_d": float(diff / pooled_sd),
    }


def main():
    raw = pd.read_csv(RAW_PATH)
    summary = pd.read_csv(SUMMARY_PATH)

    desc = describe_raw_scoring_sheet(raw)
    agree = check_files_agree(raw, summary)
    result = group_comparison(summary)

    print("=== Raw scoring sheet: sentence_list_scores.csv (descriptive only) ===")
    print(f"list-level rows scored          : {desc['n_rows']}")
    print(f"recipients                      : {desc['n_recipients']}")
    print(f"distinct sentence lists         : {desc['n_distinct_lists']}")
    print(
        "lists per recipient             : "
        f"{desc['lists_per_recipient_min']} to {desc['lists_per_recipient_max']}"
    )
    print(f"missing scores                  : {desc['n_missing_scores']}")
    print(
        "list-level score range (% words): "
        f"{desc['score_min']:.1f} to {desc['score_max']:.1f}"
    )

    print("\n=== Agreement between the two files ===")
    print(
        "max |summary mean - recomputed mean| : "
        f"{agree['max_abs_mean_difference']:.2f}"
    )
    print(
        "recipients whose lists_scored disagrees with the raw row count : "
        f"{agree['n_recipients_with_count_mismatch']}"
    )

    print("\n=== Group comparison: recipient_mean_scores.csv (one row per recipient) ===")
    print(
        "established     : n = "
        f"{result['n_established']}, mean = {result['mean_established']:.2f}%, "
        f"SD = {result['sd_established']:.2f}"
    )
    print(
        "noise_reduction : n = "
        f"{result['n_noise_reduction']}, mean = {result['mean_noise_reduction']:.2f}%, "
        f"SD = {result['sd_noise_reduction']:.2f}"
    )
    print(
        "difference (noise_reduction - established) : "
        f"{result['mean_difference']:.2f} percentage points "
        f"(95% CI {result['ci_low']:.2f} to {result['ci_high']:.2f})"
    )
    print(
        "independent two-sample t-test : "
        f"t({result['df']}) = {result['t_statistic']:.3f}, "
        f"p = {result['p_value']:.3f}"
    )
    print(f"pooled SD = {result['pooled_sd']:.2f}, Cohen's d = {result['cohens_d']:.3f}")


if __name__ == "__main__":
    main()
