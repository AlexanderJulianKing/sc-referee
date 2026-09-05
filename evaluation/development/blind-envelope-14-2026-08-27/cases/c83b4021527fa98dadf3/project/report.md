# Daily walnuts versus a matched cracker snack: eight-week lipid panel

## Design

A nutrition research unit ran an eight-week parallel-group feeding study in free-living adults
with mildly raised cholesterol. Seventy adults were allocated to one of two daily snacks of
matched energy content: 35 ate a 30 g portion of walnuts each day, and 35 ate a 30 g portion of a
matched savoury cracker snack. Background diet and activity advice was identical in both arms.
Each participant gave one fasting blood sample at the end of week eight, and the same lipid panel
was measured for everyone.

| Group | Daily snack | Participants |
| --- | --- | --- |
| `walnut` | 30 g walnuts | 35 |
| `cracker` | 30 g matched savoury cracker snack | 35 |
| Total | | 70 |

Before recruitment the unit declared a family of five lipid outcomes, in this order: LDL
cholesterol, HDL cholesterol, fasting triglycerides, total cholesterol, and apolipoprotein B.

## Data

The analysis reads a single file, `lipid_panel.csv`. **One row is one participant**: their study
identifier, the snack they were allocated to, and the five declared lipid outcomes measured on
their single end-of-week-eight fasting sample. Each participant appears exactly once. There are
70 data rows plus a header row, and no blank cells.

| Column | Type | Units | What it holds |
| --- | --- | --- | --- |
| `participant_id` | text | none | Study identifier, `NUT-001` to `NUT-070`, unique per row. |
| `snack` | text | none | Allocated snack, exactly two values: `walnut` or `cracker`. |
| `ldl_c_mmol_per_l` | number, 2 dp | mmol/L | Declared outcome 1: fasting LDL cholesterol. |
| `hdl_c_mmol_per_l` | number, 2 dp | mmol/L | Declared outcome 2: fasting HDL cholesterol. |
| `triglycerides_mmol_per_l` | number, 2 dp | mmol/L | Declared outcome 3: fasting triglycerides. |
| `total_c_mmol_per_l` | number, 2 dp | mmol/L | Declared outcome 4: fasting total cholesterol. |
| `apo_b_g_per_l` | number, 2 dp | g/L | Declared outcome 5: fasting apolipoprotein B. |

The five outcome columns appear in the order the unit declared them.

## Statistical method

Each declared outcome was compared between the two snack groups with a two-sided Welch
two-sample t-test, which does not assume the two groups share a variance. For each outcome the
analysis reports the group means, their difference (walnut minus cracker), and the p-value.

Because five outcomes were declared and all five were tested, the family-wise error rate was
controlled with the Sidak correction. The per-comparison threshold is worked out inside
`analysis.py` from the declared family size and the conventional family-wise level of 0.05:

- declared family size: **5** outcomes
- family-wise level: **0.05**
- Sidak per-comparison threshold: `1 - (1 - 0.05) ** (1 / 5)` = **0.010206**

Every one of the five declared outcomes was counted in that family size, and every verdict below
rests on comparing that outcome's p-value against this single threshold of 0.010206. No other
significance threshold is used anywhere in this report.

## Results

Means are group means at week eight. The difference is walnut minus cracker. The verdict is the
comparison of the p-value against the Sidak per-comparison threshold of 0.010206.

| # | Outcome | Units | Walnut mean (n=35) | Cracker mean (n=35) | Difference | p-value | Verdict vs. 0.010206 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | LDL cholesterol | mmol/L | 3.001 | 3.499 | -0.499 | 0.000315 | p < 0.010206, significant |
| 2 | HDL cholesterol | mmol/L | 1.454 | 1.339 | +0.115 | 0.049321 | p > 0.010206, not significant |
| 3 | Fasting triglycerides | mmol/L | 1.345 | 1.366 | -0.022 | 0.837772 | p > 0.010206, not significant |
| 4 | Total cholesterol | mmol/L | 5.055 | 5.458 | -0.403 | 0.007351 | p < 0.010206, significant |
| 5 | Apolipoprotein B | g/L | 0.933 | 1.046 | -0.113 | 0.002336 | p < 0.010206, significant |

Three of the five declared outcomes fall below the Sidak threshold.

### Conclusion for each outcome

1. **LDL cholesterol.** The walnut group averaged 0.499 mmol/L lower than the cracker group.
   p = 0.000315 is below 0.010206, so this difference survives correction for the whole family of
   five.
2. **HDL cholesterol.** The walnut group averaged 0.115 mmol/L higher. p = 0.049321 would clear an
   uncorrected 0.05 cut-off, but it is above the 0.010206 threshold that applies here, so this
   outcome is not significant. It is a marginal result, not a positive one.
3. **Fasting triglycerides.** The two groups were effectively the same, a difference of
   0.022 mmol/L. p = 0.837772 is far above 0.010206, so this outcome is not significant.
4. **Total cholesterol.** The walnut group averaged 0.403 mmol/L lower. p = 0.007351 is below
   0.010206, so this difference survives correction.
5. **Apolipoprotein B.** The walnut group averaged 0.113 g/L lower. p = 0.002336 is below
   0.010206, so this difference survives correction.

## Nutritional interpretation

The pattern across the panel is coherent. Eating 30 g of walnuts a day instead of an
energy-matched cracker snack went with lower LDL cholesterol, lower total cholesterol, and lower
apolipoprotein B at week eight. Those three outcomes measure closely related things:
apolipoprotein B counts the atherogenic particles that carry most of the LDL cholesterol, and
total cholesterol includes LDL, so a real drop in LDL should show up in all three. It does, and
all three clear the corrected threshold. The size of the LDL difference, about half a millimole
per litre, is the kind of change a diet swap of this scale can plausibly produce, and it matches
the fatty-acid difference between the snacks: walnuts supply mostly polyunsaturated fat, including
alpha-linolenic acid, in place of the more saturated fat and refined starch of a cracker.

Two outcomes do not support a claim. Fasting triglycerides were essentially identical in the two
groups, which is unsurprising, since fasting triglycerides respond more to total energy, alcohol,
and carbohydrate load than to swapping one 30 g snack for another of the same energy content. HDL
cholesterol was higher in the walnut group by 0.115 mmol/L, and on its own that comparison would
look positive at a conventional 0.05 cut-off. Under the pre-declared plan it is not: with five
declared outcomes, the per-comparison bar is 0.010206, and 0.049 does not clear it. Treating that
HDL result as a finding would be the multiplicity error the correction exists to prevent. It is
best described as a suggestion worth testing in a study designed and powered for HDL as a primary
outcome.

Two limits are worth stating. This is a single end-of-study measurement with no baseline sample,
so the analysis compares group levels at week eight rather than change from baseline, and it leans
entirely on allocation to make the groups comparable. And an eight-week window shows a lipid
response, not a clinical one; nothing here speaks to cardiovascular events.

## Reproducing

From the project root:

```
python3 analysis.py
```

The script reads `lipid_panel.csv`, prints the Sidak arithmetic and threshold, and prints the
results table with the verdict for each of the five declared outcomes. Every number quoted in this
report comes from that output.
