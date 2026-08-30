"""Juvenile lobster shelter trial: two-group comparison over the declared outcome family.

Compares crushed shell substrate against moulded plastic tube shelters on each of the five
pre-declared outcomes with an independent two-sample t-test, then corrects the whole family of
five raw p-values together with pingouin's Holm step-down procedure at a family-wise alpha of
0.05. Every verdict is taken from the adjusted value, never from the raw p-value.
"""

import pandas as pd
from scipy import stats
import pingouin as pg

DATA_FILE = "lobster_shelter_trial.csv"
GROUP_COL = "shelter_type"
GROUP_A = "crushed_shell"
GROUP_B = "plastic_tube"
FAMILY_ALPHA = 0.05

# The five outcomes in the order the experiment declared them in advance.
OUTCOMES = [
    "carapace_increment_mm",
    "mass_gain_g",
    "moult_count",
    "shelter_time_s",
    "haemolymph_protein_g_l",
]


def main():
    df = pd.read_csv(DATA_FILE)

    a = df[df[GROUP_COL] == GROUP_A]
    b = df[df[GROUP_COL] == GROUP_B]
    print(f"n({GROUP_A}) = {len(a)}   n({GROUP_B}) = {len(b)}   total rows = {len(df)}")
    print(f"missing values in outcome columns: {int(df[OUTCOMES].isna().sum().sum())}")
    print()

    means_a = []
    means_b = []
    raw_p = []
    t_stats = []

    for outcome in OUTCOMES:
        x = a[outcome].to_numpy(dtype=float)
        y = b[outcome].to_numpy(dtype=float)
        t, p = stats.ttest_ind(x, y)
        means_a.append(x.mean())
        means_b.append(y.mean())
        t_stats.append(t)
        raw_p.append(p)

    # The complete family of five raw p-values goes to the correction in a single call.
    reject, adj_p = pg.multicomp(raw_p, alpha=FAMILY_ALPHA, method="holm")

    print(
        f"Family-wise correction: pingouin {pg.__version__} multicomp, "
        f"method='holm', alpha={FAMILY_ALPHA}, family size = {len(OUTCOMES)}"
    )
    print()

    header = (
        f"{'outcome':<24}{'mean_' + GROUP_A:>18}{'mean_' + GROUP_B:>18}"
        f"{'t':>9}{'raw_p':>12}{'adj_p':>12}  verdict"
    )
    print(header)
    print("-" * len(header))

    for i, outcome in enumerate(OUTCOMES):
        verdict = "significant" if reject[i] else "not significant"
        print(
            f"{outcome:<24}{means_a[i]:>18.3f}{means_b[i]:>18.3f}"
            f"{t_stats[i]:>9.3f}{raw_p[i]:>12.5f}{adj_p[i]:>12.5f}  {verdict}"
        )


if __name__ == "__main__":
    main()
