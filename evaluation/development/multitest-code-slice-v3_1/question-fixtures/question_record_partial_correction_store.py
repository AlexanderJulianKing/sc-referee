from scipy import stats

FAMILY_SIZE = 5
p = stats.ttest_ind(a, b).pvalue
result = {"p_value": p}
result["p_value"] = min(1.0, result["p_value"] * FAMILY_SIZE)
print(result["p_value"] < 0.05)
