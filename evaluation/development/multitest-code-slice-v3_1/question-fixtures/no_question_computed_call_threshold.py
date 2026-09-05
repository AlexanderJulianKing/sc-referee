from scipy import stats


def make_threshold():
    return 0.01


p = stats.ttest_ind(a, b).pvalue
print(p < make_threshold())
