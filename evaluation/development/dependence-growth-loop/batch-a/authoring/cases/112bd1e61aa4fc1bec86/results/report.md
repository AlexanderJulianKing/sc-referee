# Oviposition substrate choice in individually assayed Drosophila suzukii females

## Design

Mated Drosophila suzukii females were each tested once, alone, in a dedicated
two-choice arena holding one intact ripening raspberry and one wounded overripe
raspberry. The recorded outcome is the substrate that received the female's
first egg during a 24 h observation window.

Each female appears in exactly one row and each arena is used by exactly one
female, so the analysed rows are independent replicates: no female is measured
twice and nothing is pooled across repeated observations of the same individual.

Design check: 20 rows, 20 distinct female_id values, 20 distinct arena_id values.

## Sample description

| quantity | value |
| --- | --- |
| females assayed | 20 |
| rearing cohorts | A (10), B (10) |
| age at assay (days) | 4-7 |
| mean wing length (mm) | 2.38 |
| mean eggs laid in 24 h | 40.5 |
| median eggs laid in 24 h | 40.5 |
| mean latency to first egg (min) | 24.9 |

## Analysis

The pre-specified question is whether the first egg lands on the ripening
substrate more often than chance would give. Because each row carries one
female's single binary outcome, the rows are independent Bernoulli trials and an
exact two-sided binomial test against p = 0.5 applies to the raw row counts
without any correction for within-individual dependence.

## Result

First egg on the ripening substrate: 16 of 20 females (proportion 0.800).
Exact two-sided binomial test against p = 0.5: p = 0.011818.

[selected-result] 16 of 20 individually assayed females (proportion 0.800) placed their first egg on the ripening substrate rather than the overripe substrate; an exact two-sided binomial test against p = 0.5 gives p = 0.011818, so the preference for ripening fruit is significant at the 5 percent level.

## Cohort consistency check

The same exact test applied separately within each rearing cohort is reported
for description only; the primary claim rests on the pooled test above.

| cohort | ripening | tested | proportion | exact two-sided p |
| --- | --- | --- | --- | --- |
| A | 9 | 10 | 0.900 | 0.021484 |
| B | 7 | 10 | 0.700 | 0.343750 |

Both cohorts lean the same way. Cohort B on its own does not reach the 5 percent
level, which is unsurprising at this per-cohort sample size.

## Limitations

The outcome is the placement of the first egg in a two-item arena over a single
24 h window, so it speaks to relative acceptance of the two offered substrates,
not to how a female would spread eggs across a whole fruit patch. The result
describes laboratory-reared females in the age range assayed here.
