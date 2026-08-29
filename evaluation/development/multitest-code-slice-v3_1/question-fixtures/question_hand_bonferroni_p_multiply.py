from scipy import stats

FAMILY_SIZE = 5
p = stats.ttest_ind(a, b).pvalue
p_adjusted = min(1.0, p * FAMILY_SIZE)
print(p_adjusted < 0.05)
