from scipy import stats

p = stats.ttest_ind(a, b).pvalue
print(p < 0.01)
