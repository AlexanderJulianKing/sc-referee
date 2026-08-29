from scipy import stats
from statsmodels.stats.multitest import multipletests

OUTCOMES = ["m1", "m2", "m3", "m4", "m5"]
pvalues = []
for column in OUTCOMES:
    p = stats.ttest_ind(a[column], b[column]).pvalue
    pvalues.append(p)
reject, adjusted, _, _ = multipletests(pvalues)
for p_adjusted in adjusted:
    print(p_adjusted < 0.05)
