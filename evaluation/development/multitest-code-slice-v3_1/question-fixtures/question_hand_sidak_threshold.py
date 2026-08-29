from scipy import stats

ALPHA = 0.05
FAMILY_SIZE = 5
p = stats.ttest_ind(a, b).pvalue
threshold = 1 - (1 - ALPHA) ** (1 / FAMILY_SIZE)
print(p < threshold)
