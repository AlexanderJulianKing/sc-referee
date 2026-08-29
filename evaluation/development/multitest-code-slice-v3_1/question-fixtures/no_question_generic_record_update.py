from scipy import stats

p = stats.ttest_ind(a, b).pvalue
result = {"p_value": p}
result.update({"p_used": result["p_value"]})
print(result["p_used"] < 0.05)
