from external_adjuster import adjust
from scipy import stats

p = stats.ttest_ind(a, b).pvalue
p_adjusted = adjust(p)
print(p_adjusted < 0.05)
