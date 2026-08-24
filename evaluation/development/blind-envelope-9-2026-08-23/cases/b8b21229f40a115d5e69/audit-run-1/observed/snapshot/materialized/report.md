# Hepatic lead in grey squirrels from inner-city parks and rural woodland

## Background

We compared hepatic lead burdens in grey squirrels taken from two collection settings.
Twenty-six carcasses came to us from routine culls, thirteen from inner-city parks and
thirteen from rural woodland. Each liver was freeze-dried and homogenised, and the
homogenate was digested and read three separate times on the same instrument. That gives
us 78 measurements of hepatic lead concentration in milligrams per kilogram of liver dry
weight.

## The data

All measurements are in `squirrel_liver_lead.csv`: one header line and 78 data rows.

A single row is one instrument reading, that is, one measurement of liver lead
concentration from one analytical run.

The file has four columns.

| Column | Type | What it holds |
| --- | --- | --- |
| `squirrel_tag` | text | The carcass tag code of the animal the reading came from, `SQ-101` through `SQ-126`. |
| `collection_setting` | text | Where the animal was collected: `urban_park` for inner-city parks or `rural_woodland` for rural woodland. |
| `analytical_run` | integer | Which analytical run produced the reading: `1`, `2` or `3`. |
| `lead_mg_per_kg_dw` | decimal number | The measured hepatic lead concentration for that reading, in milligrams of lead per kilogram of liver dry weight, to four decimal places. |

Tags `SQ-101` to `SQ-113` are the urban park animals and `SQ-114` to `SQ-126` the rural
woodland animals, so the two settings contribute 39 rows each.

## Method

All analysis is in `analysis.py`. We compared `lead_mg_per_kg_dw` between the two levels
of `collection_setting` with an independent two-sample t-test with equal variances,
applied to every row of the table, so each measured row entered the comparison as its own
observation. We report the group means and standard deviations, the difference in means
with its 95% confidence interval, and Cohen's d.

## Results

Hepatic lead was measured in 78 observations, 39 from urban park animals and 39 from
rural woodland animals.

| Group | n | Mean (mg/kg dw) | SD | Min | Max |
| --- | --- | --- | --- | --- | --- |
| `urban_park` | 39 | 0.3645 | 0.1253 | 0.1905 | 0.6603 |
| `rural_woodland` | 39 | 0.1255 | 0.0545 | 0.0481 | 0.2145 |

Urban park squirrels carried substantially more hepatic lead than rural woodland
squirrels. The mean difference was 0.2390 mg/kg dry weight (95% CI 0.1954 to 0.2826),
t(76) = 10.92, p = 3.1e-17, Cohen's d = 2.47. Urban park animals averaged 2.9 times the
lead concentration of rural woodland animals.

The separation between the settings is clean. The highest rural woodland reading, 0.2145
mg/kg dry weight, sits below the mean of the urban park group, and the urban park group
reaches 0.6603 mg/kg dry weight at its top end.

## Conclusion

Grey squirrels from inner-city parks carry markedly higher hepatic lead burdens than
those from rural woodland, by a factor of close to three. The difference is large and
statistically unambiguous. The result is consistent with a greater environmental lead
load in the inner-city park habitat, and it supports the use of grey squirrel liver as a
practical sentinel tissue for urban lead exposure.
