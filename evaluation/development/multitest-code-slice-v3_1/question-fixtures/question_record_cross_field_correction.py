from scipy import stats

FAMILY_SIZE = 5
p = stats.ttest_ind(a, b).pvalue
result = {"p_value": p}
result["p_adjusted"] = min(1.0, result["p_value"] * FAMILY_SIZE)
print(result["p_adjusted"] < 0.05)
