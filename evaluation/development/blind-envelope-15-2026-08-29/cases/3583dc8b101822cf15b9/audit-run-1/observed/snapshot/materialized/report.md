# Metal exposure and biological effect in informal e-waste recycling workers

## The data

`data.csv` holds one row per worker, and nothing else: 96 rows plus a header, no
repeated rows, no summary rows, no blank cells. A single row carries one
worker's trade, his pre-assigned analysis stage, and his six declared outcome
measurements from one blood sample and one spot urine sample taken on the same
morning.

| Column | Meaning | Unit |
| --- | --- | --- |
| `worker_id` | Anonymous survey identifier for the worker | none |
| `trade` | Exposure group: `recycling` (dismantles and burns electronic scrap) or `textile` (control trade, no metal exposure) | none |
| `analysis_stage` | Half of the survey the worker was allocated to: `discovery` or `validation` | none |
| `blood_lead_ug_dl` | Blood lead concentration | micrograms per decilitre |
| `urinary_cadmium_ug_g_cr` | Urinary cadmium, creatinine-corrected | micrograms per gram of creatinine |
| `urinary_nickel_ug_l` | Urinary nickel concentration | micrograms per litre |
| `haemoglobin_g_dl` | Blood haemoglobin concentration | grams per decilitre |
| `serum_alt_u_l` | Serum alanine aminotransferase activity | units per litre |
| `urinary_8ohdg_ng_mg_cr` | Urinary 8-hydroxy-2-deoxyguanosine, creatinine-corrected | nanograms per milligram of creatinine |

The `analysis_stage` column records a split that the study statistician fixed by
random allocation before any sample was analysed, balanced so each half holds 24
recycling and 24 textile workers. It is written into the data file and is not
derived from any measurement. The counts confirm the intended balance: 24
recycling and 24 textile workers in the discovery half, and 24 of each in the
validation half, 96 workers in total.

## Design and declared outcomes

Ninety-six adult male workers from one city took part: 48 who dismantle and burn
electronic scrap and 48 from a nearby textile trade with no metal exposure,
matched on age band and years of work. The survey protocol declared six outcomes
as one family, in this fixed order, before the split was made: blood lead,
urinary cadmium, urinary nickel, haemoglobin, serum ALT, and urinary 8-OHdG.

Family error is controlled by the two-stage design the protocol fixed in
advance. The discovery half screens; the validation half confirms. Every
comparison of the two trades uses a Welch two-sample t-test, which does not
assume the two trades have equal variance.

## Stage 1: discovery

In the discovery half only, all six declared outcomes were compared between the
trades, and those reaching a screening level of 0.05 were carried forward.
Discovery group means, recycling against textile: blood lead 9.66 against 4.54
ug/dL (p = 2.70e-06); urinary cadmium 1.395 against 0.619 ug/g creatinine
(p = 2.96e-06); urinary nickel 6.57 against 3.47 ug/L (p = 0.00025); haemoglobin
13.10 against 14.06 g/dL (p = 0.0062); serum ALT 33.38 against 28.38 U/L
(p = 0.146); urinary 8-OHdG 8.33 against 5.63 ng/mg creatinine (p = 0.0021).

Five outcomes survived screening: blood lead, urinary cadmium, urinary nickel,
haemoglobin, and urinary 8-OHdG. Serum ALT did not reach the screening level and
was not carried forward, so no finding is claimed about it. The discovery half
yields no conclusion of its own; it only decides what gets tested next.

## Stage 2: validation

Five outcomes were carried into validation, so each was judged at
0.05 / 5 = 0.01, a Bonferroni level adjusted for the number actually carried
forward. Dividing the family error rate among exactly those five tests keeps the
family-wise error rate across the confirmed findings at 0.05.

Validation group means, recycling against textile: blood lead 9.75 against 4.73
ug/dL (p = 1.16e-05, confirmed); urinary cadmium 1.367 against 0.583 ug/g
creatinine (p = 2.87e-07, confirmed); urinary nickel 6.38 against 3.65 ug/L
(p = 0.00066, confirmed); urinary 8-OHdG 8.20 against 5.73 ng/mg creatinine
(p = 0.0046, confirmed); haemoglobin 13.38 against 14.03 g/dL (p = 0.064, above
the 0.01 level and therefore not confirmed).

## Conclusion

Resting on the validation stage alone, the survey confirms four findings. Men
who dismantle and burn electronic scrap carry higher body burdens of three
metals than matched textile workers: blood lead is higher by about 5.0 ug/dL,
urinary cadmium by about 0.78 ug/g creatinine, and urinary nickel by about
2.7 ug/L. They also show more oxidative DNA damage, with urinary 8-OHdG higher
by about 2.5 ng/mg creatinine.

Haemoglobin was lower in recycling workers in both halves, but it did not clear
the adjusted validation level, so the survey does not confirm an anaemia effect.
Serum ALT never left the screening stage and is reported as not carried forward,
not as a tested finding.
