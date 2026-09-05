# Gut and serum markers in newly diagnosed coeliac disease

## Design

Sixty adults with newly diagnosed, biopsy-confirmed coeliac disease and sixty healthy
volunteers gave a stool sample and fasting bloods at a single clinic visit. Five
markers were measured: stool Shannon diversity, faecal calprotectin, faecal butyrate,
serum zonulin, and serum 25-OH vitamin D.

The panel is exploratory, so the protocol fixed a discovery/validation split before
any assay was run. Each subject was assigned to a discovery or a validation half, with
the split balanced within diagnosis so that each half holds 30 coeliac and 30 healthy
subjects. That assignment lives in the `cohort` column of `data.csv` and is not touched
by the analysis. The point of the split is that the discovery half is allowed to be
looked at freely, because nothing measured there is reported as a result. The
validation half is only used once, on a short list chosen without reference to it.

## Stage 1: discovery screening

All five markers were tested in the discovery half with Welch's t-test. These p-values
are a filter, not results, and we do not report any of them as evidence for or against
a marker. Four markers screened in at the five-percent level: Shannon diversity
(p = 0.004), faecal calprotectin (p = 1.1e-06), butyrate (p = 1.1e-04), and zonulin
(p = 6.5e-05). Vitamin D did not (p = 0.24) and was dropped.

## Stage 2: validation

The corrected family is therefore four tests, not five. Those four markers were tested
in the validation half and the four p-values corrected together with Holm-Bonferroni
at a family-wide five percent.

| Marker | Healthy | Coeliac | Raw p | Holm p | Verdict |
| --- | --- | --- | --- | --- | --- |
| Faecal calprotectin (ug/g) | 26.6 | 76.7 | 1.2e-06 | 4.9e-06 | finding |
| Zonulin (ng/mL) | 28.0 | 42.1 | 2.0e-04 | 6.1e-04 | finding |
| Butyrate (mmol/kg) | 12.26 | 8.67 | 5.8e-04 | 1.2e-03 | finding |
| Shannon diversity | 3.53 | 3.40 | 0.27 | 0.27 | not significant |

## Findings

Three markers are reported as findings: faecal calprotectin is roughly three times
higher in coeliac subjects, serum zonulin is about 14 ng/mL higher, and faecal butyrate
is about 3.6 mmol/kg lower. Read together they describe an inflamed, more permeable
gut with a depleted butyrate-producing community, which is what the clinical picture
would predict.

Shannon diversity is the instructive case. It screened in easily in the discovery half
and then did not hold up in validation, with a difference of 0.13 units and p = 0.27.
Had we reported the discovery result we would have published a diversity effect that
the second half of our own subjects does not support. Vitamin D was dropped at
screening and so has no result here at all; it was not tested in the validation half,
and nothing in this analysis should be read as evidence that vitamin D status is
unaffected in coeliac disease. All five markers came from a single visit at diagnosis,
before any gluten-free diet, so none of this speaks to what happens on treatment.
