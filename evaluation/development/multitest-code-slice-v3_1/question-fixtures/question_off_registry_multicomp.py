from scipy import stats
import pingouin as pg

OUTCOMES = ["m1", "m2", "m3", "m4", "m5"]
pvalues = []
for column in OUTCOMES:
    p = stats.ttest_ind(a[column], b[column]).pvalue
    pvalues.append(p)
reject, adjusted = pg.multicomp(pvalues)
for p_adjusted in adjusted:
    print(p_adjusted < 0.05)
