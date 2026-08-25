__sc_inline_55_12_32_-1_frame = pd.read_csv(DATA_FILE)
frame = __sc_inline_55_12_32_-1_frame
print('Venous leg ulcer dressing comparison')
print('=' * 78)
print(f'Data file: {DATA_FILE.name}')
print(f'Patients: {len(frame)} rows, one row per patient')
print(f'  arms: {GROUP_FOAM} vs {GROUP_ALGINATE}')
print(f'Missing cells in the file: {int(frame.isna().sum().sum())}')
print()
results = {}
for column in DECLARED_OUTCOMES:
    __sc_inline_69_26_38_-1_foam_values = frame.loc[frame[GROUP_COLUMN] == GROUP_FOAM, column].to_numpy()
    __sc_inline_69_26_38_-1_alginate_values = frame.loc[frame[GROUP_COLUMN] == GROUP_ALGINATE, column].to_numpy()
    __sc_inline_69_26_38_-1_test = stats.ttest_ind(__sc_inline_69_26_38_-1_foam_values, __sc_inline_69_26_38_-1_alginate_values)
    results[column] = {'foam_n': int(__sc_inline_69_26_38_-1_foam_values.size), 'foam_mean': float(__sc_inline_69_26_38_-1_foam_values.mean()), 'foam_sd': float(__sc_inline_69_26_38_-1_foam_values.std(ddof=1)), 'alginate_n': int(__sc_inline_69_26_38_-1_alginate_values.size), 'alginate_mean': float(__sc_inline_69_26_38_-1_alginate_values.mean()), 'alginate_sd': float(__sc_inline_69_26_38_-1_alginate_values.std(ddof=1)), 'difference': float(__sc_inline_69_26_38_-1_foam_values.mean() - __sc_inline_69_26_38_-1_alginate_values.mean()), 't_statistic': float(__sc_inline_69_26_38_-1_test.statistic), 'p_value': float(__sc_inline_69_26_38_-1_test.pvalue)}
print('Group summaries (mean and standard deviation)')
print('-' * 78)
header = f"{'Outcome':<40}{'Foam':>18}{'Alginate':>18}"
print(header)
for column in DECLARED_OUTCOMES:
    entry = results[column]
    foam_cell = f"{entry['foam_mean']:.2f} ({entry['foam_sd']:.2f})"
    alginate_cell = f"{entry['alginate_mean']:.2f} ({entry['alginate_sd']:.2f})"
    print(f'{column:<40}{foam_cell:>18}{alginate_cell:>18}')
print()
print(f'Per-outcome tests (independent two-sample t-test, alpha = {ALPHA})')
print('-' * 78)
print(f"{'#':<3}{'Outcome':<40}{'diff':>10}{'t':>9}{'p':>12}  verdict")
for column in DECLARED_OUTCOMES:
    entry = results[column]
    significant_flag = entry['p_value'] < 0.05
    print(f"{column:<40}{entry['difference']:>10.2f}{entry['t_statistic']:>9.3f}{entry['p_value']:>12.4f}  {significant_flag}")
print()
return results