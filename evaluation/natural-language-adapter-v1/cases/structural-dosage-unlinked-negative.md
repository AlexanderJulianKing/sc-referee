# Locus Q calibrated segment-B analysis

## Breakpoint QC and dosage calibration

Reliability required at least 30 molecules, mean MAPQ at least 55, alignment entropy no more than 0.15, pair balance at least 0.65, and local complexity no more than 0.25. This retained 476 of 780 breakpoint-panel samples. Copy-index rounding produced 284, 170, and 22 samples with 0, 1, and 2 segment-B copies. All 476 calls agreed with the independent depth-log2 classification; the 192 nonzero calls define the requested carrier count.

The outer orientation and nested segment were deliberately calibrated separately. An interval-1 ExtraTrees classifier predicted outer copy count with 100.00% 10-fold accuracy. An interval-2 standardized multinomial logistic classifier predicted segment-B copy count with 99.37% accuracy. In contrast, using the outer interval for segment B achieved only 63.66%, confirming that the nested signal is not interchangeable with the broader orientation.

## Clinical association

The full 1,900-sample cohort was merged without missing strata to the released sampling design. Weights were inverse sample fractions for the complete clinic × recruitment stream × ancestry × age band × case strata and normalized to mean one. The weighted binomial-logit model included segment-B dosage and outer-orientation dosage simultaneously, plus continuous age, sex, three ancestry PCs, clinic stratum, and ancestry group. Recruitment stream and age band were design variables only. The segment-B coefficient was -0.325223 (robust SE 0.100281, 95% CI -0.521774 to -0.128673); this is the reported source-population log odds ratio. The estimate stayed negative without the categorical ancestry term (-0.314450) and with exposures only (-0.226491). The same unweighted adjusted model (-0.128837) differed materially, as expected under the strong outcome-dependent sampling fractions, so it was not used.
