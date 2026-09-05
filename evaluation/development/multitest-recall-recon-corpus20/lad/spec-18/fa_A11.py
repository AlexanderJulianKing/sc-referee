"""Mycorrhizal inoculant in spring wheat: six outcomes, permutation max-T.

Multiplicity is controlled by a label-shuffling procedure rather than a
packaged correction. The reference distribution is the largest absolute
t-statistic seen across the six outcomes within a shuffle, so a single
distribution covers the whole family and the family-wise error rate is held
at the nominal level.
"""

import numpy as np
import pandas as pd

N_SHUFFLES = 5000
SEED = 4711
ALPHA = 0.05

OUTCOMES = [
    "grain_yield_g",
    "thousand_kernel_g",
    "grain_protein_pct",
    "root_colonisation_pct",
    "shoot_p_pct",
    "tiller_count",
]

data = pd.read_csv("data.csv")
values = data[OUTCOMES].to_numpy()
inoculated = (data["inoculant"] == "inoculated").to_numpy()


def welch_t(values, treated):
    """Welch t for every column, treated group minus control group."""
    a = values[treated]
    b = values[~treated]
    na, nb = a.shape[0], b.shape[0]
    va = a.var(axis=0, ddof=1) / na
    vb = b.var(axis=0, ddof=1) / nb
    return (a.mean(axis=0) - b.mean(axis=0)) / np.sqrt(va + vb)


observed = welch_t(values, inoculated)

rng = np.random.default_rng(SEED)
shuffled_max = np.empty(N_SHUFFLES)
labels = inoculated.copy()
for i in range(N_SHUFFLES):
    rng.shuffle(labels)
    shuffled_max[i] = np.max(np.abs(welch_t(values, labels)))

adjusted_p = np.array(
    [np.mean(shuffled_max >= abs(t)) for t in observed]
)

n_none = int((~inoculated).sum())
n_inoc = int(inoculated.sum())

print("Mycorrhizal inoculant trial, one-metre row sections")
print(f"n = {n_none} none, {n_inoc} inoculated")
print(f"label shuffles: {N_SHUFFLES} (seed {SEED})")
print(f"family-wise alpha: {ALPHA}")
print()
print(f"{'outcome':<24}{'none':>10}{'inoculated':>12}{'t':>9}{'p_adj':>10}  verdict")

for i, outcome in enumerate(OUTCOMES):
    mean_none = data.loc[~inoculated, outcome].mean()
    mean_inoc = data.loc[inoculated, outcome].mean()
    verdict = "significant" if adjusted_p[i] < ALPHA else "not significant"
    print(
        f"{outcome:<24}{mean_none:>10.2f}{mean_inoc:>12.2f}"
        f"{observed[i]:>9.2f}{adjusted_p[i]:>10.4f}  {verdict}"
    )

print()
print(
    f"{int((adjusted_p < ALPHA).sum())} of {len(OUTCOMES)} outcomes significant "
    "under the maximum-statistic procedure"
)
print(f"95th percentile of the shuffled maxima: {np.quantile(shuffled_max, 0.95):.2f}")
