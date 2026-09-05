from scipy import stats
import pingouin as pg

p1 = stats.ttest_ind(a1, b1).pvalue
p2 = stats.ttest_ind(a2, b2).pvalue
pg.multicomp([p1])
pg.multicomp([p2])
