# Wildfire smoke exposure and firefighter lung function

Thirty-six wildland firefighters were measured in a mobile clinic within 48 hours of
demobilisation from a heavy smoke-exposure deployment, and compared with 36 station-based
firefighters from the same agency who had no deployment that season. Six outcomes were
recorded, and all six are treated as one family: FEV1, FVC, exhaled nitric oxide, CRP,
carboxyhaemoglobin saturation, and a respiratory symptom score.

Each outcome was tested with a Welch two-sample t-test, and the six raw p-values were
corrected together with **multipy** (version 0.16, `multipy.fdr.lsu`), a dedicated
multiple-hypothesis-testing package. `lsu` is the Benjamini-Hochberg one-stage linear
step-up procedure, which controls the **false discovery rate**, here at q = 0.05 across
all six outcomes. That is a different guarantee from a family-wide error rate: it holds
the expected share of false positives among the outcomes we call significant to 5%,
rather than the chance of any false positive at all. The package returns accept/reject
flags, so the adjusted values below were read off the same procedure by finding, for each
outcome, the lowest FDR level at which multipy still rejects it. Significance calls come
only from multipy's flags. The package is pinned in `requirements.txt`.

| Outcome | Station | Wildland | Raw p | Adjusted | multipy decision |
|---|---|---|---|---|---|
| FEV1 (L) | 3.92 | 3.69 | 0.1001 | 0.1146 | not significant |
| FVC (L) | 4.92 | 4.69 | 0.1146 | 0.1146 | not significant |
| FeNO (ppb) | 17.3 | 24.5 | 0.0005 | 0.0009 | significant |
| CRP (mg/L) | 1.55 | 2.33 | 0.0033 | 0.0049 | significant |
| Carboxyhaemoglobin (%) | 1.11 | 2.26 | <0.0001 | <0.0001 | significant |
| Symptom score (0-20) | 3.25 | 6.00 | 0.0001 | 0.0003 | significant |

Four outcomes survive: carboxyhaemoglobin, exhaled nitric oxide, CRP, and the symptom
score. Spirometry does not. FEV1 was 0.23 L lower and FVC 0.23 L lower in the deployed
group, but both sit well above the corrected cutoff, so this study does not demonstrate a
deficit in mechanical lung function at 48 hours after demobilisation.

For exposure policy the surviving four point the same way. Carboxyhaemoglobin roughly
doubled, which is a direct marker of recent combustion-gas uptake and argues for
respiratory protection and rotation limits on active fire lines rather than only at mop-up.
The airway inflammation markers, FeNO and CRP, are raised alongside a symptom score that
also roughly doubled, which is the pattern of an irritant response that has not yet shown
up in spirometry. A sensible reading is that the deployment leaves measurable inflammation
and exposure burden even where forced volumes look intact, so post-deployment monitoring
should not rely on spirometry alone to decide who is affected. Whether any of this persists
is out of reach here, because every measurement was taken within 48 hours of coming off the
line and there is no follow-up visit in this data set.
