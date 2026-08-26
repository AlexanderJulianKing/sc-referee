"""Larvicide regime versus insecticide-treated nets alone, coastal district.

Fifty-two surveyed villages, 26 under each regime, one wet season of trap and
household survey data. Five outcomes were recorded per village and all five are
treated as one outcome family: the raw p-values go into a single call to the
statsmodels multiple-comparison routine with its default correction method and a
family-wide error rate of 5 percent. Only the decisions that routine returns are
used to claim a difference.
"""

import inspect

import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

FAMILY_ALPHA = 0.05

# Declared outcome order. The p-value list handed to the correction routine
# follows this order and nothing is left out of it.
OUTCOMES = [
    ("adult_mosquitoes_per_trap_night", "adults per trap night", 2),
    ("larval_habitat_positive_pct", "habitats positive (%)", 1),
    ("household_biting_rate", "bites per person-night", 2),
    ("fever_cases_per_1000", "fever cases per 1000", 1),
    ("programme_cost_usd_per_capita", "cost per capita (USD)", 2),
]

METHOD_NAMES = {
    "hs": "Holm-Sidak step-down",
    "holm": "Holm step-down",
    "bonferroni": "Bonferroni",
    "fdr_bh": "Benjamini-Hochberg",
}


def fmt_p(p):
    """Small p-values are unreadable in fixed notation, so switch below 1e-4."""
    return f"{p:.2e}" if p < 1e-4 else f"{p:.5f}"


def load():
    data = pd.read_csv("data.csv")
    regimes = set(data["regime"].unique())
    if regimes != {"nets_only", "larvicide"}:
        raise ValueError(f"unexpected regime labels: {sorted(regimes)}")
    return data


def main():
    data = load()
    nets = data[data["regime"] == "nets_only"]
    larvicide = data[data["regime"] == "larvicide"]
    print(f"Villages: nets_only n={len(nets)}, larvicide n={len(larvicide)}")
    print("Test: two-sample Welch t-test on the difference in means, two sided.\n")

    means_nets, means_larv, raw_p = [], [], []
    for column, _label, _dp in OUTCOMES:
        a = nets[column]
        b = larvicide[column]
        result = stats.ttest_ind(a, b, equal_var=False)
        means_nets.append(a.mean())
        means_larv.append(b.mean())
        raw_p.append(result.pvalue)

    # One call, one family, five p-values, correction method left at the default.
    reject, p_adjusted, _alpha_sidak, _alpha_bonf = multipletests(raw_p, alpha=FAMILY_ALPHA)

    applied = inspect.signature(multipletests).parameters["method"].default
    print(f"Correction: statsmodels multipletests, default method '{applied}' "
          f"= {METHOD_NAMES.get(applied, applied)}")
    print(f"Family: the {len(OUTCOMES)} outcomes listed below, corrected in one call, "
          f"family-wide error rate {FAMILY_ALPHA:.0%}.\n")

    header = f"{'outcome':<32}{'nets_only':>11}{'larvicide':>11}{'diff':>10}{'raw p':>12}{'adjusted p':>13}  decision"
    print(header)
    print("-" * len(header))
    for (column, _label, dp), m_nets, m_larv, p_raw, p_adj, rej in zip(
        OUTCOMES, means_nets, means_larv, raw_p, p_adjusted, reject
    ):
        diff = m_nets - m_larv
        decision = "difference" if rej else "no difference"
        print(f"{column:<32}{m_nets:>11.{dp}f}{m_larv:>11.{dp}f}{diff:>10.{dp}f}"
              f"{fmt_p(p_raw):>12}{fmt_p(p_adj):>13}  {decision}")

    print()
    n_rejected = int(sum(reject))
    print(f"{n_rejected} of {len(OUTCOMES)} outcomes differ after correction.")
    for (column, _label, _dp), rej in zip(OUTCOMES, reject):
        if not rej:
            print(f"  {column}: adjusted p above the family-wide level, no claim made.")


if __name__ == "__main__":
    main()
